"""
Payment Repository

Репозиторий для работы с коллекцией payment_transactions

Операции перенесены из backend/server.py:
- Строка 244: create_transaction
- Строка 279: create_transaction
- Строка 287: find_by_session_id
- Строка 327: update_status
- Строка 366: update_status

Дата создания: 2025-10-09
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from .base import BaseRepository


class PaymentRepository(BaseRepository):
    """
    Репозиторий для работы с платежными транзакциями

    Коллекция: payment_transactions
    """

    collection_name = 'payment_transactions'

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
        Создать новую платёжную транзакцию

        Источник: backend/server.py строки 244, 279

        Args:
            transaction_data: Данные транзакции (из PaymentTransaction модели)

        Returns:
            Созданная транзакция
        """
        return await self.create(transaction_data)

    # ===========================================
    # READ операции
    # ===========================================

    async def find_by_session_id(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Найти транзакцию по Stripe Session ID

        Источник: backend/server.py строка 287

        Args:
            session_id: Stripe Checkout Session ID

        Returns:
            Транзакция или None
        """
        return await self.find_one({'session_id': session_id})

    async def find_by_user(
        self,
        user_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Получить транзакции пользователя

        Args:
            user_id: ID пользователя
            limit: Максимальное количество
            skip: Пропустить N транзакций

        Returns:
            Список транзакций
        """
        return await self.find_many(
            query={'user_id': user_id},
            limit=limit,
            skip=skip,
            sort=[('created_at', -1)]
        )

    async def find_by_email(
        self,
        user_email: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Получить транзакции по email

        Используется когда пользователь не залогинен

        Args:
            user_email: Email пользователя
            limit: Максимальное количество

        Returns:
            Список транзакций
        """
        return await self.find_many(
            query={'user_email': user_email},
            limit=limit,
            sort=[('created_at', -1)]
        )

    # ===========================================
    # UPDATE операции
    # ===========================================

    async def update_status(
        self,
        session_id: str,
        status: str
    ) -> bool:
        """
        Обновить статус платёжной транзакции

        Источник: backend/server.py строки 327, 366

        Args:
            session_id: Stripe Session ID
            status: Новый статус ("paid", "failed", "expired")

        Returns:
            True если успешно обновлено
        """
        return await self.update(
            {'session_id': session_id},
            {
                'payment_status': status,
                'updated_at': datetime.utcnow()
            }
        )

    async def mark_as_paid(self, session_id: str) -> bool:
        """
        Пометить транзакцию как оплаченную

        Args:
            session_id: Stripe Session ID

        Returns:
            True если успешно
        """
        return await self.update_status(session_id, 'paid')

    async def mark_as_failed(self, session_id: str) -> bool:
        """
        Пометить транзакцию как неудавшуюся

        Args:
            session_id: Stripe Session ID

        Returns:
            True если успешно
        """
        return await self.update_status(session_id, 'failed')

    async def mark_as_expired(self, session_id: str) -> bool:
        """
        Пометить транзакцию как истекшую

        Args:
            session_id: Stripe Session ID

        Returns:
            True если успешно
        """
        return await self.update_status(session_id, 'expired')

    # ===========================================
    # Статистика
    # ===========================================

    async def get_successful_payments(
        self,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получить успешные платежи

        Args:
            user_id: ID пользователя (опционально, если None - все платежи)

        Returns:
            Список успешных транзакций
        """
        query = {'payment_status': 'paid'}
        if user_id:
            query['user_id'] = user_id

        return await self.find_many(query, limit=0)  # Все записи

    async def get_total_revenue(self) -> float:
        """
        Посчитать общую выручку (все успешные платежи)

        Returns:
            Сумма в евро
        """
        pipeline = [
            {'$match': {'payment_status': 'paid'}},
            {'$group': {
                '_id': None,
                'total': {'$sum': '$amount'}
            }}
        ]

        result = await self.aggregate(pipeline)
        return result[0]['total'] if result else 0.0

    async def get_revenue_by_package(self) -> Dict[str, float]:
        """
        Получить выручку по типам пакетов

        Returns:
            Dict: package_type -> total_amount
        """
        pipeline = [
            {'$match': {'payment_status': 'paid'}},
            {'$group': {
                '_id': '$package_type',
                'total': {'$sum': '$amount'},
                'count': {'$sum': 1}
            }}
        ]

        result = await self.aggregate(pipeline)

        return {
            item['_id']: {
                'total': item['total'],
                'count': item['count']
            }
            for item in result
        }

    async def count_payments_by_status(self) -> Dict[str, int]:
        """
        Подсчитать платежи по статусам

        Returns:
            Dict: status -> count
        """
        pipeline = [
            {'$group': {
                '_id': '$payment_status',
                'count': {'$sum': 1}
            }}
        ]

        result = await self.aggregate(pipeline)

        return {
            item['_id']: item['count']
            for item in result
        }


__all__ = ['PaymentRepository']
