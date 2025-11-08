"""
Credit Repository

Репозиторий для работы с коллекцией credit_transactions

Операции перенесены из backend/server.py:
- Строка 134: create_transaction
- Строки 158-160: find_by_user (с пагинацией)
- Строка 171: count_by_user

Дата создания: 2025-10-09
"""

from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from .base import BaseRepository


class CreditRepository(BaseRepository):
    """
    Репозиторий для работы с транзакциями баллов

    Коллекция: credit_transactions
    """

    collection_name = 'credit_transactions'

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)

    # ===========================================
    # CREATE операции
    # ===========================================

    async def create_transaction(
        self,
        transaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Создать новую транзакцию баллов

        Источник: backend/server.py строка 134

        Args:
            transaction_data: Данные транзакции (из CreditTransaction модели)

        Returns:
            Созданная транзакция
        """
        return await self.create(transaction_data)

    # ===========================================
    # READ операции
    # ===========================================

    async def find_by_user(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Получить транзакции пользователя с пагинацией

        Источник: backend/server.py строки 158-160

        Args:
            user_id: ID пользователя
            limit: Максимальное количество транзакций
            offset: Пропустить N транзакций (для пагинации)

        Returns:
            Список транзакций (отсортированные по created_at DESC)
        """
        return await self.find_many(
            query={'user_id': user_id},
            limit=limit,
            skip=offset,
            sort=[('created_at', -1)]  # Сначала новые
        )

    async def count_by_user(self, user_id: str) -> int:
        """
        Подсчитать количество транзакций пользователя

        Источник: backend/server.py строка 171

        Args:
            user_id: ID пользователя

        Returns:
            Количество транзакций
        """
        return await self.count({'user_id': user_id})

    async def get_user_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Получить историю транзакций пользователя с мета-данными

        Комбинированная функция для API endpoint

        Источник: backend/server.py строки 152-172

        Args:
            user_id: ID пользователя
            limit: Максимальное количество
            offset: Смещение для пагинации

        Returns:
            Dict с transactions и total
        """
        transactions = await self.find_by_user(user_id, limit, offset)
        total = await self.count_by_user(user_id)

        # Очищаем от MongoDB _id
        clean_transactions = self._remove_mongo_ids(transactions)

        return {
            'transactions': clean_transactions,
            'total': total,
            'limit': limit,
            'offset': offset
        }

    # ===========================================
    # Аналитика
    # ===========================================

    async def get_total_credits_earned(self, user_id: str) -> int:
        """
        Посчитать общее количество заработанных баллов

        Args:
            user_id: ID пользователя

        Returns:
            Сумма всех начислений (amount > 0)
        """
        pipeline = [
            {'$match': {
                'user_id': user_id,
                'transaction_type': 'credit',
                'amount': {'$gt': 0}
            }},
            {'$group': {
                '_id': None,
                'total': {'$sum': '$amount'}
            }}
        ]

        result = await self.aggregate(pipeline)
        return result[0]['total'] if result else 0

    async def get_total_credits_spent(self, user_id: str) -> int:
        """
        Посчитать общее количество потраченных баллов

        Args:
            user_id: ID пользователя

        Returns:
            Сумма всех списаний (amount < 0)
        """
        pipeline = [
            {'$match': {
                'user_id': user_id,
                'transaction_type': 'debit',
                'amount': {'$lt': 0}
            }},
            {'$group': {
                '_id': None,
                'total': {'$sum': '$amount'}
            }}
        ]

        result = await self.aggregate(pipeline)
        return abs(result[0]['total']) if result else 0

    async def get_spending_by_category(
        self,
        user_id: str
    ) -> Dict[str, int]:
        """
        Получить расходы по категориям

        Args:
            user_id: ID пользователя

        Returns:
            Dict: category -> total_spent
        """
        pipeline = [
            {'$match': {
                'user_id': user_id,
                'transaction_type': 'debit'
            }},
            {'$group': {
                '_id': '$category',
                'total': {'$sum': {'$abs': '$amount'}}
            }}
        ]

        result = await self.aggregate(pipeline)

        return {
            item['_id']: item['total']
            for item in result
        }


__all__ = ['CreditRepository']
