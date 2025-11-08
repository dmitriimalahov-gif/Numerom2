"""
Lesson Service

Бизнес-логика для системы обучения (LMS)

Исходный код перенесён из:
- backend/server.py строки 848-1014 (learning endpoints)
- backend/server.py строки 2088-2439 (admin lesson management)

Дата создания: 2025-10-09
"""

from fastapi import HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
import random
import sys
import os

# Импортируем quiz данные из старого backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

try:
    from quiz_data import NUMEROLOGY_QUIZ
except ImportError:
    NUMEROLOGY_QUIZ = {'questions': []}

from database.repositories.lesson_repository import LessonRepository
from services.credit_service import CreditService
from models.lesson import VideoLesson, UserProgress
from models.credit import CREDIT_COSTS


class LessonService:
    """
    Сервис для управления уроками и прогрессом обучения

    Обрабатывает просмотр уроков, прогресс, квизы и уровни пользователей
    """

    def __init__(
        self,
        lesson_repo: LessonRepository,
        credit_service: CreditService
    ):
        """
        Инициализация LessonService

        Args:
            lesson_repo: LessonRepository instance
            credit_service: CreditService instance
        """
        self.lesson_repo = lesson_repo
        self.credit_service = credit_service

    # ===========================================
    # Получение уроков
    # ===========================================

    async def get_all_lessons(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Получить все активные уроки с прогрессом

        Источник: backend/server.py строки 848-890

        Args:
            user_id: ID пользователя

        Returns:
            Dict с уроками и прогрессом
        """
        # Получаем все активные уроки
        lessons = await self.lesson_repo.find_active_lessons()

        # Получаем прогресс пользователя
        progress_list = await self.lesson_repo.get_all_user_progress(user_id)
        progress_map = {p['lesson_id']: p for p in progress_list}

        # Обогащаем уроки информацией о прогрессе
        enriched_lessons = []
        for lesson in lessons:
            lesson_id = lesson['id']
            lesson_data = dict(lesson)
            lesson_data.pop('_id', None)

            # Добавляем прогресс
            if lesson_id in progress_map:
                progress = progress_map[lesson_id]
                lesson_data['user_progress'] = {
                    'completed': progress.get('completed', False),
                    'watch_time_minutes': progress.get('watch_time_minutes', 0),
                    'quiz_score': progress.get('quiz_score')
                }
            else:
                lesson_data['user_progress'] = {
                    'completed': False,
                    'watch_time_minutes': 0,
                    'quiz_score': None
                }

            enriched_lessons.append(lesson_data)

        # Получаем уровень пользователя
        user_level = await self.lesson_repo.get_user_level(user_id)
        if not user_level:
            user_level = {
                'current_level': 1,
                'experience_points': 0,
                'lessons_completed': 0
            }

        return {
            'lessons': enriched_lessons,
            'user_level': user_level
        }

    async def get_lessons_public(self) -> List[Dict[str, Any]]:
        """
        Получить все активные уроки (без прогресса, публичный доступ)

        Источник: backend/server.py строки 908-919

        Returns:
            Список уроков
        """
        lessons = await self.lesson_repo.find_active_lessons()

        # Очищаем от _id
        clean_lessons = []
        for lesson in lessons:
            lesson_data = dict(lesson)
            lesson_data.pop('_id', None)
            clean_lessons.append(lesson_data)

        return clean_lessons

    # ===========================================
    # Начало и завершение урока
    # ===========================================

    async def start_lesson(
        self,
        user_id: str,
        lesson_id: str
    ) -> Dict[str, Any]:
        """
        Начать урок - списать 10 баллов (одноразово)

        Источник: backend/server.py строки 969-1011

        Args:
            user_id: ID пользователя
            lesson_id: ID урока

        Returns:
            Dict с результатом

        Raises:
            HTTPException: 404 если урок не найден
            HTTPException: 402 если недостаточно баллов
        """
        # Проверяем существование урока
        lesson = await self.lesson_repo.find_lesson_by_id(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail='Урок не найден')

        # Проверяем, не начинал ли пользователь уже этот урок
        existing_progress = await self.lesson_repo.get_user_progress(user_id, lesson_id)

        # Если урок уже начат, просто возвращаем успех
        if existing_progress:
            return {
                'lesson_started': True,
                'points_deducted': 0,
                'message': 'Урок уже был начат ранее'
            }

        # Списываем 10 баллов за первый просмотр
        await self.credit_service.deduct_credits(
            user_id=user_id,
            cost=CREDIT_COSTS['lesson_viewing'],
            description=f'Просмотр урока: {lesson.get("title", "Без названия")}',
            category='learning',
            details={'lesson_id': lesson_id, 'lesson_title': lesson.get('title')}
        )

        # Создаём начальный прогресс
        progress_data = {
            'user_id': user_id,
            'lesson_id': lesson_id,
            'completed': False,
            'watch_time_minutes': 0,
            'created_at': datetime.utcnow()
        }
        await self.lesson_repo.create_or_update_progress(user_id, lesson_id, progress_data)

        return {
            'lesson_started': True,
            'points_deducted': CREDIT_COSTS['lesson_viewing'],
            'message': 'Урок успешно начат'
        }

    async def complete_lesson(
        self,
        user_id: str,
        lesson_id: str,
        watch_time: int,
        quiz_score: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Завершить урок

        Источник: backend/server.py строки 921-934

        Args:
            user_id: ID пользователя
            lesson_id: ID урока
            watch_time: Время просмотра в минутах
            quiz_score: Оценка за квиз (опционально)

        Returns:
            Dict с результатом и новым уровнем

        Raises:
            HTTPException: 404 если урок не найден
        """
        # Проверяем существование урока
        lesson = await self.lesson_repo.find_lesson_by_id(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail='Lesson not found')

        # Обновляем прогресс
        progress_data = {
            'user_id': user_id,
            'lesson_id': lesson_id,
            'completed': True,
            'completion_date': datetime.utcnow(),
            'watch_time_minutes': watch_time,
            'quiz_score': quiz_score
        }
        await self.lesson_repo.create_or_update_progress(user_id, lesson_id, progress_data)

        # Подсчитываем завершённые уроки
        completed = await self.lesson_repo.count_completed_lessons(user_id)

        # Вычисляем новый уровень (каждые 3 урока = +1 уровень, макс 10)
        new_level = min(10, (completed // 3) + 1)

        # Обновляем уровень пользователя
        level_data = {
            'current_level': new_level,
            'lessons_completed': completed,
            'last_activity': datetime.utcnow()
        }
        await self.lesson_repo.create_or_update_level(user_id, level_data)

        # Добавляем 10 очков опыта
        await self.lesson_repo.increment_experience(user_id, 10)

        return {
            'lesson_completed': True,
            'new_level': new_level,
            'total_completed': completed
        }

    # ===========================================
    # Квизы
    # ===========================================

    async def get_lesson_quiz(
        self,
        lesson_id: str
    ) -> Dict[str, Any]:
        """
        Получить 5 случайных вопросов викторины для урока

        Источник: backend/server.py строки 936-967

        Args:
            lesson_id: ID урока

        Returns:
            Dict с вопросами квиза

        Raises:
            HTTPException: 404 если урок не найден
        """
        # Проверяем существование урока
        lesson = await self.lesson_repo.find_lesson_by_id(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail='Урок не найден')

        # Получаем все вопросы
        all_questions = NUMEROLOGY_QUIZ.get('questions', [])

        # Выбираем случайные 5 вопросов
        if len(all_questions) <= 5:
            selected_questions = all_questions
        else:
            selected_questions = random.sample(all_questions, 5)

        # Перемешиваем варианты ответов в каждом вопросе
        for question in selected_questions:
            if 'options' in question:
                random.shuffle(question['options'])

        return {
            'lesson_id': lesson_id,
            'lesson_title': lesson.get('title', 'Урок'),
            'quiz': {
                'title': 'Викторина по уроку',
                'description': f'Ответьте на 5 вопросов по материалу урока "{lesson.get("title", "")}"',
                'questions': selected_questions
            }
        }

    # ===========================================
    # CRUD операции (для админов)
    # ===========================================

    async def create_lesson(
        self,
        lesson_data: Dict[str, Any]
    ) -> str:
        """
        Создать новый урок

        Args:
            lesson_data: Данные урока

        Returns:
            ID созданного урока
        """
        lesson = VideoLesson(**lesson_data)
        return await self.lesson_repo.create_lesson(lesson.dict())

    async def update_lesson(
        self,
        lesson_id: str,
        lesson_data: Dict[str, Any]
    ) -> bool:
        """
        Обновить урок

        Args:
            lesson_id: ID урока
            lesson_data: Новые данные

        Returns:
            True если обновлено

        Raises:
            HTTPException: 404 если урок не найден
        """
        lesson = await self.lesson_repo.find_lesson_by_id(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail='Урок не найден')

        return await self.lesson_repo.update_lesson(lesson_id, lesson_data)

    async def delete_lesson(
        self,
        lesson_id: str
    ) -> bool:
        """
        Удалить урок

        Args:
            lesson_id: ID урока

        Returns:
            True если удалено

        Raises:
            HTTPException: 404 если урок не найден
        """
        lesson = await self.lesson_repo.find_lesson_by_id(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail='Урок не найден')

        return await self.lesson_repo.delete_lesson(lesson_id)

    async def get_all_lessons_admin(self) -> List[Dict[str, Any]]:
        """
        Получить все уроки (включая неактивные) для админов

        Returns:
            Список всех уроков
        """
        lessons = await self.lesson_repo.find_all_lessons()

        # Очищаем от _id
        clean_lessons = []
        for lesson in lessons:
            lesson_data = dict(lesson)
            lesson_data.pop('_id', None)
            clean_lessons.append(lesson_data)

        return clean_lessons

    # ===========================================
    # Статистика
    # ===========================================

    async def get_user_stats(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Получить статистику обучения пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Dict со статистикой
        """
        # Статистика завершения
        completion_stats = await self.lesson_repo.get_completion_stats(user_id)

        # Уровень пользователя
        user_level = await self.lesson_repo.get_user_level(user_id)
        if not user_level:
            user_level = {
                'current_level': 1,
                'experience_points': 0,
                'lessons_completed': 0
            }

        # Общее количество активных уроков
        total_lessons = await self.lesson_repo.count_active_lessons()

        return {
            'level': user_level.get('current_level', 1),
            'experience_points': user_level.get('experience_points', 0),
            'lessons_completed': user_level.get('lessons_completed', 0),
            'total_lessons': total_lessons,
            'completion_rate': completion_stats.get('completion_rate', 0),
            'average_quiz_score': completion_stats.get('average_quiz_score', 0)
        }


__all__ = ['LessonService']
