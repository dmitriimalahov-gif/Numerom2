"""New course content, private keys, grading and insert-only data preservation."""
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from domain.course_curriculum import load_packages, validate_package, install_packages, import_plan
from domain.narration import lesson_clips
from services.challenge_diary import challenge_data
from services.student_learning import _safe_lesson, StudentLearningService, QuizSubmission


class CurriculumContent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packages = load_packages()

    def test_all_lessons_grade_and_have_valid_seven_day_diaries(self):
        self.assertEqual([p['number'] for p in self.packages], ['intro', 4, 5, 6, 7, 8, 9, 0])
        for package in self.packages:
            with self.subTest(number=package['number']):
                lesson = package['lesson']
                questions = lesson['quiz']['questions']
                request = QuizSubmission(lesson_id=lesson['id'], quiz_id=lesson['quiz']['id'],
                    answers={q['id']: q['correct_answer'] for q in questions}, submission_id=uuid.uuid4())
                self.assertEqual(StudentLearningService._grade(lesson, request), (100, True))
                request.answers = {q['id']: next(o for o in q['options'] if o != q['correct_answer']) for q in questions}
                self.assertEqual(StudentLearningService._grade(lesson, request), (0, False))
                self.assertEqual(len(challenge_data(lesson, lesson['challenge']['id'])['daily_tasks']), 7)

    def test_answer_keys_and_explanations_never_enter_student_payload_or_audio(self):
        for package in self.packages:
            lesson = deepcopy(package['lesson'])
            lesson['quiz']['questions'][0]['explanation'] = 'PRIVATE-KEY-EXPLANATION'
            lesson['quiz']['questions'][0]['correct_answer'] = 'PRIVATE-KEY-ANSWER'
            public = json.dumps(_safe_lesson(lesson), ensure_ascii=False)
            clips = lesson_clips(lesson)
            spoken = json.dumps(clips, ensure_ascii=False)
            for secret in ('correct_answer', 'PRIVATE-KEY-EXPLANATION', 'PRIVATE-KEY-ANSWER'):
                self.assertNotIn(secret, public)
                self.assertNotIn(secret, spoken)
            expected = 2 + len(lesson['theory']) + len(lesson['exercises']) + len(lesson['quiz']['questions']) + 7
            self.assertEqual(len(clips), expected)
            self.assertEqual(len({c['id'] for c in clips}), len(clips))
            self.assertTrue(all(1 <= len(c['text']) <= 20000 for c in clips))

    def test_invalid_sources_options_and_day_order_block_import(self):
        for mutation in ('source', 'quiz', 'day'):
            p = deepcopy(self.packages[0])
            if mutation == 'source':
                p['sources'][0]['sha256'] = '0' * 64
            elif mutation == 'quiz':
                p['lesson']['quiz']['questions'][0]['correct_answer'] = 'Not an option'
            else:
                p['lesson']['challenge']['daily_tasks'][1]['day'] = 1
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_package(p)


@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'), 'requires isolated test Mongo')
class CurriculumInstall(unittest.TestCase):
    def setUp(self):
        from pymongo import MongoClient
        self.client = MongoClient(os.environ['NUMEROM_TEST_MONGO_URL'], serverSelectionTimeoutMS=5000)
        self.db = self.client['numerom_test_curriculum_' + uuid.uuid4().hex]
        self.db.lessons_v2.create_index('id', unique=True)
        self.packages = load_packages()
        self.db.lessons_v2.insert_one({'id': 'existing', 'title': 'Teacher content', 'is_active': False})
        self.db.lesson_progress.insert_one({'user_id': 'student', 'lesson_id': 'existing', 'completion_percentage': 73})
        self.original_lesson = self.db.lessons_v2.find_one({'id': 'existing'})
        self.original_progress = list(self.db.lesson_progress.find({}))

    def tearDown(self):
        self.client.drop_database(self.db.name)
        self.client.close()

    def test_repeated_import_preserves_existing_lessons_and_progress(self):
        first = install_packages(self.db.lessons_v2, self.packages)
        self.assertEqual(sum(r['action'] == 'insert' for r in first), 8)
        second = install_packages(self.db.lessons_v2, self.packages)
        self.assertTrue(all(r['action'] == 'unchanged' for r in second))
        self.assertEqual(self.db.lessons_v2.count_documents({}), 9)
        self.assertEqual(self.db.lessons_v2.find_one({'id': 'existing'}), self.original_lesson)
        self.assertEqual(list(self.db.lesson_progress.find({})), self.original_progress)

    def test_teacher_edit_or_partial_collision_blocks_all_new_writes(self):
        package = self.packages[0]
        self.db.lessons_v2.insert_one({'id': package['lesson']['id'], 'title': 'Edited by teacher'})
        before = list(self.db.lessons_v2.find({}))
        self.assertTrue(any(row['action'] == 'conflict' for row in import_plan(self.db.lessons_v2, self.packages)))
        with self.assertRaises(ValueError):
            install_packages(self.db.lessons_v2, self.packages)
        self.assertEqual(before, list(self.db.lessons_v2.find({})))

    def test_interrupted_import_can_resume_without_duplicate_lessons(self):
        install_packages(self.db.lessons_v2, self.packages[:3])
        result = install_packages(self.db.lessons_v2, self.packages)
        self.assertEqual(sum(r['action'] == 'insert' for r in result), 5)
        self.assertEqual(self.db.lessons_v2.count_documents({}), 9)

    def test_missing_unique_index_blocks_writes(self):
        self.db.lessons_v2.drop_index('id_1')
        with self.assertRaises(ValueError):
            install_packages(self.db.lessons_v2, self.packages)
        self.assertEqual(self.db.lessons_v2.count_documents({}), 1)


if __name__ == '__main__':
    unittest.main()
