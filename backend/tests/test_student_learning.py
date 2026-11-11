"""Student learning contracts using disposable Mongo, never the application DB."""
import asyncio
import ast
import os
import sys
import unittest
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import HTTPException, FastAPI, Depends
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from services.student_learning import StudentLearningService, QuizSubmission, ExerciseSubmission, TheoryRead


@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'), 'requires isolated test Mongo')
class StudentLearningContracts(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client = AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL'], serverSelectionTimeoutMS=5000)
        self.db = self.client['numerom_test_' + uuid.uuid4().hex]
        await self.db.users.insert_one({'id': 'student', 'level': 1, 'credits_remaining': 10})
        await self.db.lessons_v2.insert_many([
            {'id': 'lesson', 'is_active': True, 'level': 1, 'title': 'Numerology',
             'theory': [{'id': 't1', 'title': 'Read', 'content': 'Theory'}],
             'exercises': [{'id': 'e1', 'title': 'Reflect', 'correct_answer': 'private-exercise-answer'}],
             'quiz': {'id': 'q1', 'passing_score': 70, 'questions': [
                 {'id': 'a', 'question': 'First?', 'type': 'multiple_choice', 'options': ['one', 'two'],
                  'correct_answer': 'two', 'points': 1, 'explanation': 'private-explanation'},
                 {'id': 'b', 'question': 'Second?', 'type': 'text', 'correct_answer': 'seven', 'points': 1},
             ]}},
            {'id': 'locked', 'is_active': True, 'level': 2, 'title': 'Locked'},
            {'id': 'draft', 'is_active': False, 'level': 1, 'title': 'Draft'},
        ])
        self.service = StudentLearningService(self.db)

    async def asyncTearDown(self):
        await self.client.drop_database(self.db.name)
        self.client.close()

    def quiz(self, answers=None, submission_id=None):
        return QuizSubmission(lesson_id='lesson', quiz_id='q1',
                              answers=answers or {'a': 'two', 'b': 'seven'},
                              submission_id=submission_id or str(uuid.uuid4()))

    async def test_lesson_reads_hide_answer_keys_and_enforce_active_level_access(self):
        result = await self.service.lessons('student')
        self.assertEqual([lesson['id'] for lesson in result['lessons']], ['lesson'])
        for forbidden in ('correct_answer', 'private-explanation', 'private-exercise-answer'):
            self.assertNotIn(forbidden, str(result))
        detail = await self.service.lesson('student', 'lesson')
        self.assertFalse(detail['progress']['theory_read'])
        self.assertNotIn("'_id':", repr(detail))
        for lesson_id, status in [('locked', 403), ('draft', 404)]:
            with self.assertRaises(HTTPException) as raised:
                await self.service.lesson('student', lesson_id)
            self.assertEqual(raised.exception.status_code, status)

    async def test_quiz_grades_answers_and_rejects_client_results(self):
        with self.assertRaises(ValidationError):
            QuizSubmission(**self.quiz().model_dump(), passed=True, points_earned=9999)
        failed = await self.service.submit_quiz('student', self.quiz({'a': 'one', 'b': 'wrong'}))
        self.assertEqual((failed['score'], failed['passed'], failed['points_earned']), (0, False, 0))
        passed = await self.service.submit_quiz('student', self.quiz())
        self.assertEqual((passed['score'], passed['passed'], passed['points_earned']), (100, True, 10))
        self.assertEqual((await self.db.users.find_one({'id': 'student'}))['credits_remaining'], 20)
        progress = await self.service.progress('student', 'lesson')
        self.assertTrue(progress['quiz_passed'])
        self.assertFalse(progress['theory_read'])

    async def test_simultaneous_submissions_and_retries_award_once(self):
        request = self.quiz()
        first = await asyncio.gather(*[self.service.submit_quiz('student', request) for _ in range(8)])
        self.assertEqual(len({row['attempt_id'] for row in first}), 1)
        self.assertEqual({row['points_earned'] for row in first}, {10})
        other = await asyncio.gather(*[self.service.submit_quiz('student', self.quiz()) for _ in range(8)])
        self.assertTrue(all(row['points_earned'] == 0 for row in other))
        self.assertEqual((await self.db.users.find_one({'id': 'student'}))['credits_remaining'], 20)
        self.assertEqual(await self.db.credit_transactions.count_documents({'user_id': 'student'}), 1)
        with self.assertRaises(HTTPException) as raised:
            await self.service.submit_quiz('student', self.quiz({'a': 'one'}, str(request.submission_id)))
        self.assertEqual(raised.exception.status_code, 409)
        history = await self.service.quiz_attempts('student', 'lesson')
        self.assertIn('answers', history['attempts'][0])
        self.assertNotIn("'_id':", repr(history))

    async def test_exercise_requires_membership_awards_once_and_theory_is_explicit(self):
        with self.assertRaises(HTTPException) as raised:
            await self.service.submit_exercise('student', ExerciseSubmission(
                lesson_id='lesson', exercise_id='fake', response_text='response'))
        self.assertEqual(raised.exception.status_code, 404)
        request = ExerciseSubmission(lesson_id='lesson', exercise_id='e1', response_text='response')
        await asyncio.gather(*[self.service.submit_exercise('student', request) for _ in range(8)])
        self.assertEqual((await self.db.users.find_one({'id': 'student'}))['credits_remaining'], 20)
        self.assertFalse((await self.service.progress('student', 'lesson'))['theory_read'])
        await self.service.submit_quiz('student', self.quiz())
        await asyncio.gather(*[self.service.mark_theory('student', 'lesson') for _ in range(8)])
        progress = await self.service.progress('student', 'lesson')
        self.assertTrue(progress['is_completed'])
        self.assertEqual(progress['completion_percentage'], 100)
        self.assertEqual((await self.db.users.find_one({'id': 'student'}))['credits_remaining'], 80)
        self.assertEqual(await self.db.credit_transactions.count_documents({'category': 'lesson'}), 1)

    async def test_unknown_answers_disabled_users_and_file_metadata_are_protected(self):
        with self.assertRaises(HTTPException) as raised:
            await self.service.submit_quiz('student', self.quiz({'unknown': 'two'}))
        self.assertEqual(raised.exception.status_code, 422)
        await self.db.files.insert_one({'id': 'file', 'lesson_id': 'lesson', 'original_name': 'read.pdf',
                                        'file_path': '/secret/path', 'stored_name': 'private.pdf'})
        files = await self.service.files('student', 'lesson')
        self.assertEqual(files['files'][0]['original_name'], 'read.pdf')
        self.assertNotIn('secret', str(files))
        self.assertNotIn('stored_name', str(files))
        await self.db.users.update_one({'id': 'student'}, {'$set': {'is_disabled': True}})
        with self.assertRaises(HTTPException) as raised:
            await self.service.submit_quiz('student', self.quiz())
        self.assertEqual(raised.exception.status_code, 401)

    async def test_failed_ledger_delivery_retries_without_crediting_again(self):
        request = self.quiz()
        with patch('services.student_learning.flush_pending_credit_transactions',
                   new=AsyncMock(side_effect=OSError('synthetic delivery failure'))):
            first = await self.service.submit_quiz('student', request)
        self.assertEqual(await self.db.credit_transactions.count_documents({}), 0)
        user = await self.db.users.find_one({'id': 'student'})
        self.assertEqual(user['credits_remaining'], 20)
        self.assertEqual(len(user['pending_credit_transactions']), 1)
        second = await self.service.submit_quiz('student', request)
        self.assertEqual(first, second)
        self.assertEqual(await self.db.credit_transactions.count_documents({}), 1)
        user = await self.db.users.find_one({'id': 'student'})
        self.assertEqual(user['credits_remaining'], 20)
        self.assertEqual(user['pending_credit_transactions'], [])

    async def test_legacy_completed_lesson_does_not_receive_completion_bonus_again(self):
        await self.db.lessons_v2.update_one({'id': 'lesson'}, {'$set': {'exercises': [], 'quiz': None}})
        await self.db.lesson_progress.insert_one({'user_id': 'student', 'lesson_id': 'lesson',
            'theory_read': True, 'is_completed': True, 'completion_percentage': 100})
        for _ in range(2):
            await self.service.mark_theory('student', 'lesson')
        self.assertEqual((await self.db.users.find_one({'id': 'student'}))['credits_remaining'], 10)

    async def test_real_server_route_wiring_validates_requests_and_serializes_reads(self):
        async def identity():
            return {'user_id': 'student'}
        app = FastAPI()
        source = ast.parse((Path(__file__).resolve().parents[1] / 'server.py').read_text())
        names = {'get_all_lessons_v2_student', 'get_lesson_v2_student', 'get_lesson_progress',
                 'mark_lesson_theory_read', 'save_exercise_response', 'get_exercise_responses',
                 'get_quiz_attempts', 'save_quiz_attempt', 'get_lesson_files'}
        selected = [node for node in source.body if isinstance(node, ast.AsyncFunctionDef) and node.name in names]
        self.assertEqual(len(selected), len(names) + 1)  # Both pre-existing detail registrations.
        exec(compile(ast.Module(body=selected, type_ignores=[]), 'actual-student-handlers', 'exec'), {
            'app': app, 'db': self.db, 'Depends': Depends, 'get_current_user': identity,
            'StudentLearningService': StudentLearningService, 'QuizSubmission': QuizSubmission,
            'ExerciseSubmission': ExerciseSubmission, 'TheoryRead': TheoryRead})
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            for path in ('/api/learning-v2/lessons', '/api/learning-v2/lessons/lesson',
                         '/api/student/lesson-progress/lesson', '/api/student/lesson-files/lesson',
                         '/api/student/exercise-responses/lesson', '/api/student/quiz-attempts/lesson'):
                response = await client.get(path)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertNotIn('correct_answer', response.text)
            request = self.quiz().model_dump(mode='json')
            self.assertEqual((await client.post('/api/student/quiz-attempt', json={**request, 'passed': True})).status_code, 422)
            result = await client.post('/api/student/quiz-attempt', json=request)
            self.assertEqual(result.status_code, 200, result.text)
            self.assertTrue(result.json()['passed'])
            self.assertEqual((await client.post('/api/student/lesson-progress/lesson/theory', json={})).status_code, 200)
