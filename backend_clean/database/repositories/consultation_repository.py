"""
Consultation Repository

Репозиторий для работы с персональными консультациями

Источник:
- backend/server.py строки 343, 383, 2088-2681 (consultation endpoints используют прямые DB запросы)

Коллекции:
- personal_consultations: персональные консультации
- consultation_purchases: покупки консультаций

Дата создания: 2025-10-09
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from database.repositories.base import BaseRepository


class ConsultationRepository(BaseRepository):
    """
    Репозиторий для персональных консультаций

    Источник: backend/server.py строки 343, 383, 2088-2681
    """

    collection_name = 'personal_consultations'

    # ===========================================
    # Consultations - CRUD
    # ===========================================

    async def create_consultation(
        self,
        consultation: Dict[str, Any]
    ) -> str:
        """
        Создать консультацию

        Источник: backend/server.py строки 343, 383, 2166

        Args:
            consultation: Данные консультации

        Returns:
            ID созданной консультации
        """
        return await self.create(consultation)

    async def find_all_consultations(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Получить все консультации

        Источник: backend/server.py строка 2088

        Args:
            limit: Максимальное количество

        Returns:
            Список консультаций (сортировка по дате DESC)
        """
        return await self.find_many(
            query={},
            sort=[('created_at', -1)],
            limit=limit
        )

    async def find_by_user(
        self,
        user_id: str,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Получить консультации пользователя

        Источник: backend/server.py строка 2410

        Args:
            user_id: ID пользователя
            active_only: Только активные консультации

        Returns:
            Список консультаций пользователя
        """
        query = {'assigned_user_id': user_id}
        if active_only:
            query['is_active'] = True

        return await self.find_many(query=query, limit=100)

    async def find_consultation_by_id(
        self,
        consultation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Найти консультацию по ID

        Источник: backend/server.py строка 2607

        Args:
            consultation_id: ID консультации

        Returns:
            Консультация или None
        """
        return await self.find_one({'id': consultation_id})

    async def find_by_id_and_user(
        self,
        consultation_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Найти консультацию по ID и пользователю

        Источник: backend/server.py строка 2607

        Args:
            consultation_id: ID консультации
            user_id: ID пользователя

        Returns:
            Консультация или None
        """
        return await self.find_one({
            'id': consultation_id,
            'assigned_user_id': user_id,
            'is_active': True
        })

    async def update_consultation(
        self,
        consultation_id: str,
        consultation_data: Dict[str, Any]
    ) -> bool:
        """
        Обновить консультацию

        Источник: backend/server.py строки 2174, 2681

        Args:
            consultation_id: ID консультации
            consultation_data: Новые данные

        Returns:
            True если обновлено, False иначе
        """
        # Добавляем updated_at
        consultation_data['updated_at'] = datetime.utcnow()
        return await self.update({'id': consultation_id}, consultation_data)

    async def delete_consultation(
        self,
        consultation_id: str
    ) -> bool:
        """
        Удалить консультацию

        Источник: backend/server.py строка 2183

        Args:
            consultation_id: ID консультации

        Returns:
            True если удалено, False иначе
        """
        return await self.delete({'id': consultation_id})

    # ===========================================
    # Consultation Purchases
    # ===========================================

    async def record_purchase(
        self,
        purchase: Dict[str, Any]
    ) -> str:
        """
        Записать покупку консультации

        Args:
            purchase: Данные покупки

        Returns:
            ID записи о покупке
        """
        collection = self.collection.database['consultation_purchases']
        result = await collection.insert_one(purchase)
        return str(result.inserted_id)

    async def get_user_purchases(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Получить покупки пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Список покупок
        """
        collection = self.collection.database['consultation_purchases']
        cursor = collection.find({'user_id': user_id}).sort('purchased_at', -1)
        return await cursor.to_list(None)

    async def check_if_purchased(
        self,
        user_id: str,
        consultation_id: str
    ) -> bool:
        """
        Проверить была ли куплена консультация

        Args:
            user_id: ID пользователя
            consultation_id: ID консультации

        Returns:
            True если куплена, False иначе
        """
        collection = self.collection.database['consultation_purchases']
        result = await collection.find_one({
            'user_id': user_id,
            'consultation_id': consultation_id
        })
        return result is not None

    # ===========================================
    # Statistics
    # ===========================================

    async def count_active_consultations(self) -> int:
        """
        Подсчитать активные консультации

        Returns:
            Количество активных консультаций
        """
        return await self.count({'is_active': True})

    async def count_user_consultations(
        self,
        user_id: str
    ) -> int:
        """
        Подсчитать консультации пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Количество консультаций
        """
        return await self.count({
            'assigned_user_id': user_id,
            'is_active': True
        })

    async def get_total_purchases_count(self) -> int:
        """
        Получить общее количество покупок

        Returns:
            Количество покупок
        """
        collection = self.collection.database['consultation_purchases']
        return await collection.count_documents({})

    async def get_consultation_revenue(self) -> Dict[str, Any]:
        """
        Получить статистику по доходам от консультаций

        Returns:
            Dict с общей суммой и количеством
        """
        collection = self.collection.database['consultation_purchases']

        pipeline = [
            {'$group': {
                '_id': None,
                'total_credits': {'$sum': '$credits_spent'},
                'total_purchases': {'$sum': 1}
            }}
        ]

        cursor = collection.aggregate(pipeline)
        results = await cursor.to_list(1)

        if results:
            return {
                'total_credits_spent': results[0]['total_credits'],
                'total_purchases': results[0]['total_purchases']
            }
        return {
            'total_credits_spent': 0,
            'total_purchases': 0
        }


__all__ = ['ConsultationRepository']
