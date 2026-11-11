"""Real eight-lesson student flows in a disposable Mongo database.

Only NUMEROM_TEST_MONGO_URL is used. Every run creates a random test database,
never imports the application server, and drops only its own database afterward.
Open exercise answers are submissions for review, not automatically graded work.
"""
import os
from pathlib import Path
import sys
import unittest
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from motor.motor_asyncio import AsyncIOMotorClient

from domain.course_curriculum import load_packages, planned_document
from services.challenge_diary import ChallengeDiary, DiaryWrite
from services.student_learning import (
    ExerciseSubmission,
    QuizSubmission,
    StudentLearningService,
)


@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'), 'requires isolated test Mongo')
class CourseLearningFlow(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.packages = load_packages()

    async def asyncSetUp(self):
        self.client = AsyncIOMotorClient(
            os.environ['NUMEROM_TEST_MONGO_URL'], serverSelectionTimeoutMS=5000,
        )
        self.db = self.client['numerom_test_course_flow_' + uuid.uuid4().hex]
        self.addAsyncCleanup(self.cleanup_database)
        self.student_id = 'ordinary-course-student'
        self.initial_balance = 10
        await self.db.users.insert_one({
            'id': self.student_id,
            'level': 1,
            'is_admin': False,
            'is_super_admin': False,
            'credits_remaining': self.initial_balance,
        })
        await self.db.lessons_v2.create_index('id', unique=True)
        await self.db.lessons_v2.insert_many([
            planned_document(package) for package in self.packages
        ])
        self.learning = StudentLearningService(self.db)
        self.diary = ChallengeDiary(self.db)

    async def cleanup_database(self):
        try:
            await self.client.drop_database(self.db.name)
        finally:
            self.client.close()

    async def balance(self):
        user = await self.db.users.find_one({'id': self.student_id})
        return user['credits_remaining']

    def quiz_request(self, lesson):
        return QuizSubmission(
            lesson_id=lesson['id'],
            quiz_id=lesson['quiz']['id'],
            answers={
                question['id']: question['correct_answer']
                for question in lesson['quiz']['questions']
            },
            submission_id=uuid.uuid4(),
        )

    async def test_ordinary_student_completes_all_eight_lessons_and_retries_do_not_pay_again(self):
        self.assertEqual(len(self.packages), 8)
        listing = await self.learning.lessons(self.student_id)
        self.assertEqual(listing['user_level'], 1)
        self.assertEqual(
            [lesson['id'] for lesson in listing['lessons']],
            [package['lesson']['id'] for package in self.packages],
        )
        self.assertNotIn('correct_answer', repr(listing))

        for completed_lessons, package in enumerate(self.packages, 1):
            lesson = package['lesson']
            lesson_id = lesson['id']
            challenge_id = lesson['challenge']['id']
            with self.subTest(lesson=lesson_id):
                detail = await self.learning.lesson(self.student_id, lesson_id)
                self.assertEqual(detail['progress']['completion_percentage'], 0)
                self.assertFalse(detail['progress']['is_completed'])
                self.assertNotIn('correct_answer', repr(detail))
                starting_balance = await self.balance()

                theory = await self.learning.mark_theory(self.student_id, lesson_id)
                self.assertTrue(theory['theory_read'])
                self.assertFalse(theory['is_completed'])
                self.assertEqual(await self.balance(), starting_balance)

                self.assertEqual(len(lesson['exercises']), 4)
                for exercise in lesson['exercises']:
                    # The real service accepts a nonempty response for teacher
                    # review; it does not claim this generic answer is correct.
                    exercise_request = ExerciseSubmission(
                        lesson_id=lesson_id,
                        exercise_id=exercise['id'],
                        response_text=(
                            'Учебная запись: я описал пример, отделил наблюдение '
                            'от предположения и записал небольшой следующий шаг.'
                        ),
                    )
                    saved = await self.learning.submit_exercise(
                        self.student_id, exercise_request,
                    )
                    self.assertTrue(saved['response_id'])
                responses = (await self.learning.exercise_responses(
                    self.student_id, lesson_id,
                ))['exercise_responses']
                self.assertEqual(set(responses), {e['id'] for e in lesson['exercises']})
                self.assertTrue(all(not row['reviewed'] for row in responses.values()))
                self.assertEqual(await self.balance(), starting_balance + 40)

                quiz_request = self.quiz_request(lesson)
                quiz = await self.learning.submit_quiz(self.student_id, quiz_request)
                self.assertEqual((quiz['score'], quiz['passed'], quiz['points_earned']),
                                 (100, True, 10))
                pre_challenge = await self.learning.progress(self.student_id, lesson_id)
                self.assertEqual(pre_challenge['exercises_completed'], 4)
                self.assertTrue(pre_challenge['quiz_passed'])
                self.assertFalse(pre_challenge['challenge_completed'])
                self.assertFalse(pre_challenge['is_completed'])
                self.assertLess(pre_challenge['completion_percentage'], 100)

                diary = await self.diary.read(self.student_id, lesson_id, challenge_id)
                progress = diary['progress']
                self.assertEqual([day['day'] for day in diary['challenge']['days']],
                                 list(range(1, 8)))
                self.assertEqual(progress['revision'], 0)
                self.assertEqual(progress['completed_days'], [])
                # attempt_id belongs to the real diary snapshot, not a test stub.
                uuid.UUID(progress['attempt_id'])
                attempt_id = progress['attempt_id']

                for day in range(1, 8):
                    last_day_request = DiaryWrite(
                        request_id=uuid.uuid4(),
                        attempt_id=progress['attempt_id'],
                        revision=progress['revision'],
                        day=day,
                        note=f'День {day}: выполнил небольшой шаг и сохранил наблюдение.',
                        completed=True,
                    )
                    saved = await self.diary.save(
                        self.student_id, lesson_id, challenge_id, last_day_request,
                    )
                    self.assertNotIn('progress_sync_pending', saved)
                    progress = saved['progress']
                    self.assertEqual(progress['attempt_id'], attempt_id)
                    self.assertEqual(progress['revision'], day)
                    self.assertEqual(progress['completed_days'], list(range(1, day + 1)))
                    self.assertEqual(len(progress['daily_notes']), day)
                    if day < 7:
                        self.assertFalse(progress['is_completed'])
                        partial = await self.learning.progress(self.student_id, lesson_id)
                        self.assertFalse(partial['is_completed'])
                        self.assertLess(partial['completion_percentage'], 100)

                self.assertTrue(progress['is_completed'])
                self.assertEqual(progress['points_earned'], 120)  # seven days + bonus
                self.assertEqual(progress['total_points'], 120)
                completed = await self.learning.progress(self.student_id, lesson_id)
                self.assertTrue(completed['theory_read'])
                self.assertEqual(completed['exercises_completed'], 4)
                self.assertTrue(completed['quiz_passed'])
                self.assertTrue(completed['challenge_completed'])
                self.assertTrue(completed['is_completed'])
                self.assertEqual(completed['completion_percentage'], 100)
                self.assertEqual(await self.balance(), starting_balance + 220)

                ledger_query = {
                    'user_id': self.student_id,
                    'details.lesson_id': lesson_id,
                }
                ledger = await self.db.credit_transactions.find(ledger_query).to_list(20)
                self.assertEqual(len(ledger), 13)
                self.assertEqual(sum(row['amount'] for row in ledger), 220)
                self.assertEqual(sum(row['category'] == 'lesson' for row in ledger), 1)
                completed_balance = await self.balance()

                # A transport retry returns the original quiz result, but must
                # not credit it again. A new passing attempt earns zero.
                replayed_quiz = await self.learning.submit_quiz(self.student_id, quiz_request)
                self.assertEqual(replayed_quiz['attempt_id'], quiz['attempt_id'])
                new_quiz = await self.learning.submit_quiz(
                    self.student_id, self.quiz_request(lesson),
                )
                self.assertTrue(new_quiz['passed'])
                self.assertEqual(new_quiz['points_earned'], 0)
                await self.learning.mark_theory(self.student_id, lesson_id)
                await self.learning.submit_exercise(self.student_id, exercise_request)

                replayed = await self.diary.save(
                    self.student_id, lesson_id, challenge_id, last_day_request,
                )
                self.assertEqual(replayed['progress']['revision'], progress['revision'])
                # A fresh, current-revision save of the same completed day is
                # also a normal mobile edit and must not pay the day/bonus again.
                current = (await self.diary.read(
                    self.student_id, lesson_id, challenge_id,
                ))['progress']
                edited = await self.diary.save(
                    self.student_id, lesson_id, challenge_id,
                    DiaryWrite(
                        request_id=uuid.uuid4(), attempt_id=current['attempt_id'],
                        revision=current['revision'], day=7,
                        note='День 7: уточнил итог, завершение не изменилось.',
                        completed=True,
                    ),
                )
                self.assertEqual(edited['progress']['points_earned'], 120)
                self.assertEqual(await self.balance(), completed_balance)
                self.assertEqual(await self.db.credit_transactions.count_documents(ledger_query), 13)
                self.assertEqual((await self.learning.progress(
                    self.student_id, lesson_id,
                ))['completion_percentage'], 100)
                self.assertEqual(await self.balance(), self.initial_balance + 220 * completed_lessons)

        final = await self.learning.lessons(self.student_id)
        self.assertTrue(all(row['progress_data']['is_completed'] for row in final['lessons']))
        self.assertTrue(all(row['progress_data']['completion_percentage'] == 100
                            for row in final['lessons']))
        self.assertEqual(await self.db.exercise_responses.count_documents({'user_id': self.student_id}), 32)
        self.assertEqual(await self.db.challenge_progress.count_documents({'user_id': self.student_id}), 8)
        self.assertEqual(await self.db.credit_transactions.count_documents({'user_id': self.student_id}), 104)
        self.assertEqual(await self.balance(), self.initial_balance + 1760)


if __name__ == '__main__':
    unittest.main()
