"""
Lesson Repository

Репозиторий для работы с уроками и прогрессом обучения

Источник:
- backend/server.py строки 851-2439 (lesson endpoints используют прямые DB запросы)

Коллекции:
- video_lessons: видео уроки
- user_progress: прогресс пользователей
- user_level: уровни пользователей

Дата создания: 2025-10-09
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from database.repositories.base import BaseRepository


class LessonRepository(BaseRepository):
    """
    Репозиторий для видео уроков

    Источник: backend/server.py строки 851-2439
    """

    collection_name = 'video_lessons'

    # ===========================================
    # Lessons - CRUD
    # ===========================================

    async def find_active_lessons(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Получить все активные уроки

        Источник: backend/server.py строки 851, 911

        Args:
            limit: Максимальное количество

        Returns:
            Список активных уроков (сортировка: level, order)
        """
        return await self.find_many(
            query={'is_active': True},
            sort=[('level', 1), ('order', 1)],
            limit=limit
        )

    async def find_lesson_by_id(
        self,
        lesson_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Найти урок по ID

        Источник: backend/server.py строки 923, 940, 975, 1054, 2009

        Args:
            lesson_id: ID урока

        Returns:
            Урок или None
        """
        return await self.find_one({'id': lesson_id})

    async def create_lesson(
        self,
        lesson: Dict[str, Any]
    ) -> str:
        """
        Создать урок

        Источник: backend/server.py строка 1218

        Args:
            lesson: Данные урока

        Returns:
            ID созданного урока
        """
        return await self.create(lesson)

    async def update_lesson(
        self,
        lesson_id: str,
        lesson_data: Dict[str, Any]
    ) -> bool:
        """
        Обновить урок

        Источник: backend/server.py строки 1098, 1369, 2055

        Args:
            lesson_id: ID урока
            lesson_data: Новые данные

        Returns:
            True если обновлено, False иначе
        """
        # Добавляем updated_at
        lesson_data['updated_at'] = datetime.utcnow()
        return await self.update({'id': lesson_id}, lesson_data)

    async def delete_lesson(
        self,
        lesson_id: str
    ) -> bool:
        """
        Удалить урок

        Источник: backend/server.py строка 1392

        Args:
            lesson_id: ID урока

        Returns:
            True если удалено, False иначе
        """
        return await self.delete({'id': lesson_id})

    async def count_active_lessons(self) -> int:
        """
        Подсчитать количество активных уроков

        Источник: backend/server.py строка 2150

        Returns:
            Количество активных уроков
        """
        return await self.count({'is_active': True})

    async def find_all_lessons(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Получить все уроки (включая неактивные)

        Источник: backend/server.py строка 1307

        Args:
            limit: Максимальное количество

        Returns:
            Список всех уроков
        """
        return await self.find_many(query={}, limit=limit)

    # ===========================================
    # User Progress
    # ===========================================

    async def get_user_progress(
        self,
        user_id: str,
        lesson_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Получить прогресс пользователя

        Args:
            user_id: ID пользователя
            lesson_id: ID урока (опционально)

        Returns:
            Прогресс или None
        """
        query = {'user_id': user_id}
        if lesson_id:
            query['lesson_id'] = lesson_id

        collection = self.collection.database['user_progress']
        return await collection.find_one(query)

    async def get_all_user_progress(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Получить весь прогресс пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Список прогресса по всем урокам
        """
        collection = self.collection.database['user_progress']
        cursor = collection.find({'user_id': user_id})
        return await cursor.to_list(None)

    async def create_or_update_progress(
        self,
        user_id: str,
        lesson_id: str,
        progress_data: Dict[str, Any]
    ) -> bool:
        """
        Создать или обновить прогресс

        Args:
            user_id: ID пользователя
            lesson_id: ID урока
            progress_data: Данные прогресса

        Returns:
            True если создано/обновлено
        """
        collection = self.collection.database['user_progress']

        # Обновить или создать
        result = await collection.update_one(
            {'user_id': user_id, 'lesson_id': lesson_id},
            {'$set': progress_data},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None

    async def mark_lesson_completed(
        self,
        user_id: str,
        lesson_id: str,
        quiz_score: Optional[int] = None
    ) -> bool:
        """
        Отметить урок как завершённый

        Args:
            user_id: ID пользователя
            lesson_id: ID урока
            quiz_score: Оценка за квиз (опционально)

        Returns:
            True если обновлено
        """
        collection = self.collection.database['user_progress']

        update_data = {
            'completed': True,
            'completion_date': datetime.utcnow()
        }
        if quiz_score is not None:
            update_data['quiz_score'] = quiz_score

        result = await collection.update_one(
            {'user_id': user_id, 'lesson_id': lesson_id},
            {'$set': update_data},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None

    async def count_completed_lessons(
        self,
        user_id: str
    ) -> int:
        """
        Подсчитать завершённые уроки

        Args:
            user_id: ID пользователя

        Returns:
            Количество завершённых уроков
        """
        collection = self.collection.database['user_progress']
        return await collection.count_documents({
            'user_id': user_id,
            'completed': True
        })

    # ===========================================
    # User Level
    # ===========================================

    async def get_user_level(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Получить уровень пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Данные уровня или None
        """
        collection = self.collection.database['user_level']
        return await collection.find_one({'user_id': user_id})

    async def create_or_update_level(
        self,
        user_id: str,
        level_data: Dict[str, Any]
    ) -> bool:
        """
        Создать или обновить уровень

        Args:
            user_id: ID пользователя
            level_data: Данные уровня

        Returns:
            True если создано/обновлено
        """
        collection = self.collection.database['user_level']

        level_data['last_activity'] = datetime.utcnow()

        result = await collection.update_one(
            {'user_id': user_id},
            {'$set': level_data},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None

    async def increment_experience(
        self,
        user_id: str,
        points: int
    ) -> bool:
        """
        Увеличить опыт пользователя

        Args:
            user_id: ID пользователя
            points: Количество очков опыта

        Returns:
            True если обновлено
        """
        collection = self.collection.database['user_level']

        result = await collection.update_one(
            {'user_id': user_id},
            {
                '$inc': {'experience_points': points},
                '$set': {'last_activity': datetime.utcnow()}
            },
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None

    # ===========================================
    # Statistics
    # ===========================================

    async def get_lessons_by_level(
        self,
        level: int
    ) -> List[Dict[str, Any]]:
        """
        Получить уроки определённого уровня

        Args:
            level: Уровень (1-10)

        Returns:
            Список уроков
        """
        return await self.find_many(
            query={'level': level, 'is_active': True},
            sort=[('order', 1)]
        )

    async def get_completion_stats(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Получить статистику завершения уроков

        Args:
            user_id: ID пользователя

        Returns:
            Dict со статистикой
        """
        collection = self.collection.database['user_progress']

        total_started = await collection.count_documents({'user_id': user_id})
        total_completed = await collection.count_documents({
            'user_id': user_id,
            'completed': True
        })

        # Средняя оценка за квизы
        pipeline = [
            {'$match': {'user_id': user_id, 'quiz_score': {'$exists': True}}},
            {'$group': {
                '_id': None,
                'avg_score': {'$avg': '$quiz_score'}
            }}
        ]
        cursor = collection.aggregate(pipeline)
        results = await cursor.to_list(1)
        avg_score = results[0]['avg_score'] if results else 0

        return {
            'total_started': total_started,
            'total_completed': total_completed,
            'completion_rate': (total_completed / total_started * 100) if total_started > 0 else 0,
            'average_quiz_score': round(avg_score, 2)
        }


__all__ = ['LessonRepository']
