"""Authorized student reads and server-owned learning outcomes.

Credit rewards and their delivery outbox share a conditional user-document
mutation. A durable per-lesson reward marker makes retries safe without Mongo
multi-document transactions (the application also runs on standalone Mongo).
"""
import hashlib
import logging
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from services.credit_history import flush_pending_credit_transactions

logger = logging.getLogger(__name__)
Identifier = Annotated[str, Field(strict=True, pattern=r'^[A-Za-z0-9_-]{1,128}$')]


class QuizSubmission(BaseModel):
    model_config = ConfigDict(extra='forbid')
    lesson_id: Identifier
    quiz_id: Identifier
    answers: dict[Identifier, Annotated[StrictStr, Field(max_length=4000)]] = Field(max_length=100)
    submission_id: UUID

    @field_validator('submission_id')
    @classmethod
    def version_four(cls, value):
        if value.version != 4:
            raise ValueError('submission_id must be UUIDv4')
        return value


class ExerciseSubmission(BaseModel):
    model_config = ConfigDict(extra='forbid')
    lesson_id: Identifier
    exercise_id: Identifier
    response_text: Annotated[StrictStr, Field(min_length=1, max_length=10000)]
    attachment_ids: list[Annotated[StrictStr, Field(pattern=r'^[a-f0-9]{64}$')]] = Field(default_factory=list, max_length=3)

    @field_validator('attachment_ids')
    @classmethod
    def unique_attachments(cls, values):
        if len(set(values)) != len(values):
            raise ValueError('duplicate attachment')
        return values

    @field_validator('response_text')
    @classmethod
    def nonempty(cls, value):
        if not value.strip():
            raise ValueError('response_text must not be blank')
        return value.strip()


class TheoryRead(BaseModel):
    model_config = ConfigDict(extra='forbid')


async def _student(db, user_id):
    user = await db.users.find_one({'id': user_id})
    if not user or user.get('is_disabled'):
        raise HTTPException(401, 'Требуется вход в действующий аккаунт')
    return user


def _level(value):
    return value if type(value) is int and value >= 1 else 1


def _accessible(user, lesson):
    return bool(user.get('is_admin') or user.get('is_super_admin') or
                _level(lesson.get('level')) <= _level(user.get('level')))


async def require_student_lesson(db, user_id, lesson_id):
    """Shared authorization boundary for student content and scoped media."""
    user = await _student(db, user_id)
    lesson = await db.lessons_v2.find_one({'id': lesson_id, 'is_active': True})
    if not lesson:
        raise HTTPException(404, 'Урок не найден')
    if not _accessible(user, lesson):
        raise HTTPException(403, 'Урок пока недоступен на вашем уровне')
    return user, lesson


LESSON_FIELDS = {'id', 'title', 'description', 'module', 'level', 'order', 'points_required',
                 'is_active', 'theory', 'content', 'exercises', 'challenge', 'quiz', 'files',
                 'analytics_enabled', 'created_at', 'updated_at', 'video_platform', 'bunny_video_id', 'video_url'}
PRIVATE_CONTENT_FIELDS = {'_id', 'correct_answer', 'explanation', 'created_by', 'updated_by',
                          'file_path', 'stored_name', 'path', 'answer', 'answers'}
PROGRESS_FIELDS = {'id', 'user_id', 'lesson_id', 'is_completed', 'completion_percentage',
                   'theory_read', 'exercises_completed', 'challenge_started',
                   'challenge_completed', 'quiz_passed', 'started_at', 'last_activity_at',
                   'completed_at', 'last_accessed'}


def _clean_content(value):
    if isinstance(value, dict):
        return {key: _clean_content(item) for key, item in value.items() if key not in PRIVATE_CONTENT_FIELDS}
    if isinstance(value, list):
        return [_clean_content(item) for item in value]
    return value


def _safe_lesson(lesson):
    return _clean_content({key: value for key, value in lesson.items() if key in LESSON_FIELDS})


def _safe_progress(user_id, lesson_id, progress=None):
    result = {'user_id': user_id, 'lesson_id': lesson_id, 'is_completed': False,
              'completion_percentage': 0, 'theory_read': False, 'exercises_completed': 0,
              'challenge_started': False, 'challenge_completed': False, 'quiz_passed': False}
    result.update({key: value for key, value in (progress or {}).items() if key in PROGRESS_FIELDS})
    return result


def _key(*parts):
    return hashlib.sha256('\0'.join(parts).encode()).hexdigest()


class StudentLearningService:
    def __init__(self, db):
        self.db = db

    async def lessons(self, user_id):
        user = await _student(self.db, user_id)
        lessons = await self.db.lessons_v2.find({'is_active': True}).sort('order', 1).to_list(1000)
        lessons = [lesson for lesson in lessons if _accessible(user, lesson)]
        rows = await self.db.lesson_progress.find({'user_id': user_id,
            'lesson_id': {'$in': [lesson['id'] for lesson in lessons]}}).to_list(1000)
        progress = {row['lesson_id']: row for row in rows}
        return {'user_level': _level(user.get('level')), 'lessons': [
            {**_safe_lesson(lesson), 'progress_data': _safe_progress(user_id, lesson['id'], progress.get(lesson['id']))}
            for lesson in lessons]}

    async def lesson(self, user_id, lesson_id):
        _, lesson = await require_student_lesson(self.db, user_id, lesson_id)
        return {'lesson': _safe_lesson(lesson), 'progress': await self.progress(user_id, lesson_id)}

    async def progress(self, user_id, lesson_id):
        await require_student_lesson(self.db, user_id, lesson_id)
        progress = await self.db.lesson_progress.find_one({'user_id': user_id, 'lesson_id': lesson_id})
        return _safe_progress(user_id, lesson_id, progress)

    async def _configured_points(self, key):
        config = await self.db.learning_points_config.find_one({'is_active': True}) or {}
        points = config.get(key, 10)
        if type(points) is not int or not 0 <= points <= 1000:
            raise HTTPException(503, 'Настройки баллов временно недоступны')
        return points

    async def _award_once(self, user_id, scope, source_id, points, category, lesson_id):
        marker = _key(scope)
        field = 'learning_awards.' + marker
        event = {'id': 'learning-' + _key(user_id, scope), 'user_id': user_id,
                 'transaction_type': 'credit', 'amount': points, 'category': category,
                 'description': {'quiz': 'Прохождение теста', 'exercise': 'Выполнение упражнения',
                                 'lesson': 'Завершение урока'}[category],
                 'details': {'lesson_id': lesson_id}, 'created_at': datetime.utcnow()}
        update = {'$set': {field: {'source_id': source_id, 'points': points}},
                  '$inc': {'credits_remaining': points}}
        if points:
            update['$push'] = {'pending_credit_transactions': event}
        changed = await self.db.users.find_one_and_update(
            {'id': user_id, 'is_disabled': {'$ne': True}, field: {'$exists': False},
             'credits_remaining': {'$type': 'number', '$gte': 0, '$lte': 1000000 - points}},
            update, return_document=ReturnDocument.AFTER)
        user = changed or await _student(self.db, user_id)
        winner = user.get('learning_awards', {}).get(marker)
        if winner is None:
            raise HTTPException(409, 'Баланс не позволяет начислить награду. Обратитесь к администратору.')
        try:
            await flush_pending_credit_transactions(self.db, user_id)
        except Exception:
            # The committed reward remains deliverable from the same user document.
            logger.warning('Learning credit history delivery deferred')
        return winner['points'] if winner['source_id'] == source_id else 0

    @staticmethod
    def _grade(lesson, request):
        quiz = lesson.get('quiz') or {}
        if request.quiz_id != (quiz.get('id') or lesson['id']):
            raise HTTPException(404, 'Тест не найден')
        questions = quiz.get('questions') or []
        threshold = quiz.get('passing_score', 70)
        if (not isinstance(questions, list) or not 1 <= len(questions) <= 100 or
                type(threshold) is not int or not 0 <= threshold <= 100):
            raise HTTPException(409, 'Тест пока не готов к проверке')
        question_ids, earned, total = set(), 0, 0
        for question in questions:
            question_id = question.get('id')
            correct = question.get('correct_answer')
            kind = question.get('type', 'multiple_choice')
            weight = question.get('points', 1)
            if (not isinstance(question_id, str) or not question_id or question_id in question_ids or
                    not isinstance(correct, str) or not correct.strip() or
                    kind not in ('multiple_choice', 'true_false', 'text') or
                    type(weight) is not int or not 1 <= weight <= 100):
                raise HTTPException(409, 'Тест пока не готов к проверке')
            question_ids.add(question_id)
            submitted = request.answers.get(question_id)
            if kind in ('multiple_choice', 'true_false'):
                options = question.get('options')
                if (not isinstance(options, list) or len(options) < 2 or
                        any(not isinstance(option, str) for option in options) or correct not in options):
                    raise HTTPException(409, 'Тест пока не готов к проверке')
                if submitted is not None and submitted not in options:
                    raise HTTPException(422, 'Выберите один из вариантов ответа')
                matches = submitted == correct
            else:
                matches = submitted is not None and submitted.strip().casefold() == correct.strip().casefold()
            total += weight
            if matches:
                earned += weight
        if set(request.answers) - question_ids:
            raise HTTPException(422, 'В ответах указан неизвестный вопрос')
        score = round(100 * earned / total, 2)
        return score, score >= threshold

    async def submit_quiz(self, user_id, request: QuizSubmission):
        _, lesson = await require_student_lesson(self.db, user_id, request.lesson_id)
        submission = str(request.submission_id)
        identifier = 'quiz-' + _key(user_id, submission)
        identity = {'lesson_id': request.lesson_id, 'quiz_id': request.quiz_id,
                    'answers': request.answers, 'submission_id': submission}
        attempt = await self.db.quiz_attempts.find_one({'_id': identifier})
        if not attempt:
            score, passed = self._grade(lesson, request)
            initial = {'id': identifier, 'user_id': user_id, **identity,
                       'score': score, 'passed': passed, 'attempted_at': datetime.utcnow(),
                       'graded_by_server': True,
                       'reward_points': await self._configured_points('quiz_points_per_attempt') if passed else 0}
            try:
                await self.db.quiz_attempts.update_one({'_id': identifier}, {'$setOnInsert': initial}, upsert=True)
            except DuplicateKeyError:
                pass  # Concurrent first submission inserted the same unique operation.
            attempt = await self.db.quiz_attempts.find_one({'_id': identifier})
        if any(attempt.get(key) != value for key, value in identity.items()):
            raise HTTPException(409, 'Этот номер отправки уже использован для другого ответа')
        points = 0
        if attempt['passed']:
            points = await self._award_once(user_id, 'quiz:' + request.lesson_id + ':' + request.quiz_id,
                identifier, attempt['reward_points'], 'quiz', request.lesson_id)
        await self.db.quiz_attempts.update_one({'_id': identifier}, {'$set': {'points_earned': points}})
        await self.sync_progress(user_id, request.lesson_id)
        return {'attempt_id': attempt['id'], 'submission_id': submission,
                'score': attempt['score'], 'passed': attempt['passed'], 'points_earned': points}

    async def quiz_attempts(self, user_id, lesson_id):
        await require_student_lesson(self.db, user_id, lesson_id)
        attempts = await self.db.quiz_attempts.find({'user_id': user_id, 'lesson_id': lesson_id,
            'graded_by_server': True}).sort('attempted_at', -1).to_list(100)
        fields = {'id', 'user_id', 'lesson_id', 'quiz_id', 'score', 'passed', 'answers',
                  'attempted_at', 'points_earned', 'submission_id'}
        return {'attempts': [{**{key: value for key, value in attempt.items() if key in fields},
                              'attempt_id': attempt['id']} for attempt in attempts]}

    async def submit_exercise(self, user_id, request: ExerciseSubmission):
        _, lesson = await require_student_lesson(self.db, user_id, request.lesson_id)
        if request.exercise_id not in {exercise.get('id') for exercise in lesson.get('exercises', [])}:
            raise HTTPException(404, 'Упражнение не найдено')
        query = {'user_id': user_id, 'lesson_id': request.lesson_id, 'exercise_id': request.exercise_id}
        existing = await self.db.exercise_responses.find_one(query)
        identifier = existing['_id'] if existing else 'exercise-' + _key(user_id, request.lesson_id, request.exercise_id)
        if existing is None:
            try:
                await self.db.exercise_responses.update_one({'_id': identifier}, {'$setOnInsert': {
                    **query, 'id': str(identifier), 'attachment_draft_only': True}}, upsert=True)
            except DuplicateKeyError:
                pass
            existing = await self.db.exercise_responses.find_one({'_id': identifier})
        attachment_ids = request.attachment_ids if 'attachment_ids' in request.model_fields_set else existing.get('attachment_ids', [])
        available = {item['id'] for item in (existing or {}).get('attachment_files', [])}
        if not set(attachment_ids) <= available:
            raise HTTPException(422, 'Вложение недоступно. Обновите список файлов и повторите отправку.')
        data = {'response_text': request.response_text, 'submitted_at': datetime.utcnow(),
                'attachment_ids': attachment_ids,
                'reviewed': False, 'admin_comment': None, 'reviewed_at': None, 'reviewed_by': None}
        points = await self._configured_points('exercise_points_per_submission')
        if existing and existing.get('attachment_draft_only'):
            # Uploading a file creates only a private staging record, never a completed answer.
            data.update({'submitted_by_server': True, 'reward_points': points, 'attachment_draft_only': False})
        if attachment_ids:
            # Removal and submission contend on this same document. A disappearing file
            # cannot be referenced by a confirmed answer; a submitted file cannot be removed.
            changed = await self.db.exercise_responses.update_one(
                {'_id': identifier, 'attachment_files.id': {'$all': attachment_ids}}, {'$set': data})
            if not changed.matched_count:
                raise HTTPException(409, 'Список вложений изменился. Обновите ответ и повторите отправку.')
        else:
            await self.db.exercise_responses.update_one({'_id': identifier}, {'$set': data})
        response = await self.db.exercise_responses.find_one({'_id': identifier})
        if response.get('submitted_by_server'):
            await self._award_once(user_id, 'exercise:' + request.lesson_id + ':' + request.exercise_id,
                response['id'], response['reward_points'], 'exercise', request.lesson_id)
        await self.sync_progress(user_id, request.lesson_id)
        return {'message': 'Ответ сохранён', 'response_id': response['id']}

    async def exercise_responses(self, user_id, lesson_id):
        _, lesson = await require_student_lesson(self.db, user_id, lesson_id)
        valid_ids = [exercise.get('id') for exercise in lesson.get('exercises', [])]
        rows = await self.db.exercise_responses.find({'user_id': user_id, 'lesson_id': lesson_id,
            'exercise_id': {'$in': valid_ids}}).to_list(1000)
        fields = {'id', 'lesson_id', 'exercise_id', 'response_text', 'submitted_at',
                  'reviewed', 'admin_comment', 'reviewed_at', 'attachment_ids'}
        rows = [row for row in rows if not row.get('attachment_draft_only')]
        return {'exercise_responses': {row['exercise_id']: {key: value for key, value in row.items()
                                       if key in fields} for row in rows}}

    async def files(self, user_id, lesson_id):
        await require_student_lesson(self.db, user_id, lesson_id)
        fields = {'id', 'lesson_id', 'original_name', 'original_filename', 'filename',
                  'mime_type', 'file_type', 'file_size', 'description', 'section', 'lesson_section'}
        rows = await self.db.files.find({'lesson_id': lesson_id, 'is_active': {'$ne': False}}).to_list(1000)
        files = [{key: value for key, value in row.items() if key in fields} for row in rows]
        return {'files': files, 'total': len(files)}

    async def mark_theory(self, user_id, lesson_id):
        await require_student_lesson(self.db, user_id, lesson_id)
        await self._save_progress(user_id, lesson_id, {'theory_read': True})
        return await self.sync_progress(user_id, lesson_id)

    async def _save_progress(self, user_id, lesson_id, values):
        existing = await self.db.lesson_progress.find_one({'user_id': user_id, 'lesson_id': lesson_id})
        identifier = existing['_id'] if existing else 'progress-' + _key(user_id, lesson_id)
        initial = {'id': str(identifier), 'user_id': user_id, 'lesson_id': lesson_id,
                   'started_at': datetime.utcnow()}
        try:
            await self.db.lesson_progress.update_one({'_id': identifier}, {
                '$setOnInsert': initial, '$set': {'last_activity_at': datetime.utcnow()},
                '$max': values}, upsert=True)
        except DuplicateKeyError:
            await self.db.lesson_progress.update_one({'_id': identifier}, {'$max': values})

    async def sync_progress(self, user_id, lesson_id):
        _, lesson = await require_student_lesson(self.db, user_id, lesson_id)
        existing = await self.db.lesson_progress.find_one({'user_id': user_id, 'lesson_id': lesson_id}) or {}
        theory_read = bool(existing.get('theory_read'))
        exercises = {exercise.get('id') for exercise in lesson.get('exercises', []) if exercise.get('id')}
        completed = await self.db.exercise_responses.distinct('exercise_id', {
            'user_id': user_id, 'lesson_id': lesson_id, 'exercise_id': {'$in': list(exercises)}})
        quiz = lesson.get('quiz') or {}
        quiz_passed = bool(quiz and await self.db.quiz_attempts.find_one({
            'user_id': user_id, 'lesson_id': lesson_id, 'quiz_id': quiz.get('id') or lesson_id,
            'passed': True, 'graded_by_server': True}))
        challenge = lesson.get('challenge') or {}
        challenge_progress = await self.db.challenge_progress.find_one({'user_id': user_id,
            'lesson_id': lesson_id, 'challenge_id': challenge.get('id')}) if challenge else None
        user = await _student(self.db, user_id)
        journal = user.get('challenge_journals', {}).get(_key(lesson_id, str(challenge.get('id')))) if challenge else None
        challenge_completed = bool(journal.get('ever_completed') if journal else challenge_progress and challenge_progress.get('is_completed'))
        challenge_progress = journal or challenge_progress
        total = 1 + len(exercises) + bool(quiz) + bool(challenge)
        count = int(theory_read) + len(completed) + int(quiz_passed) + int(challenge_completed)
        percentage = int(100 * count / total)
        values = {'theory_read': theory_read, 'exercises_completed': len(completed),
                  'quiz_passed': quiz_passed, 'challenge_started': bool(challenge_progress),
                  'challenge_completed': challenge_completed, 'completion_percentage': percentage,
                  'is_completed': percentage == 100}
        if percentage == 100:
            if not existing.get('is_completed') or existing.get('completion_awarded_by_server'):
                await self._award_once(user_id, 'lesson:' + lesson_id, 'lesson:' + lesson_id,
                                       50, 'lesson', lesson_id)
                values['completion_awarded_by_server'] = True
            values['completed_at'] = existing.get('completed_at') or datetime.utcnow()
        await self._save_progress(user_id, lesson_id, values)
        return await self.progress(user_id, lesson_id)
