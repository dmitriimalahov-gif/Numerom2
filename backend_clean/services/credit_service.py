"""
Credit Service

Бизнес-логика для управления баллами пользователей

Исходный код перенесён из:
- backend/server.py строки 120-150 (record_credit_transaction, deduct_credits)
- backend/server.py строки 152-172 (get_credit_history)

Дата создания: 2025-10-09
"""

from fastapi import HTTPException
from typing import Dict, Any, List, Optional

from database.repositories.user_repository import UserRepository
from database.repositories.credit_repository import CreditRepository
from models.credit import CreditTransaction, CREDIT_COSTS


class CreditService:
    """
    Сервис для управления баллами пользователей

    Обрабатывает начисление, списание и историю транзакций баллов
    """

    def __init__(
        self,
        user_repo: UserRepository,
        credit_repo: CreditRepository
    ):
        """
        Инициализация CreditService

        Args:
            user_repo: UserRepository instance
            credit_repo: CreditRepository instance
        """
        self.user_repo = user_repo
        self.credit_repo = credit_repo

    # ===========================================
    # Запись транзакций
    # ===========================================

    async def record_transaction(
        self,
        user_id: str,
        amount: int,
        description: str,
        category: str,
        details: Optional[Dict[str, Any]] = None
    ) -> CreditTransaction:
        """
        Записать транзакцию баллов (начисление или списание)

        Источник: backend/server.py строки 120-134

        Args:
            user_id: ID пользователя
            amount: Количество баллов (положительное - начисление, отрицательное - списание)
            description: Описание транзакции
            category: Категория (personal_numbers, lesson_viewing, etc.)
            details: Дополнительные данные (опционально)

        Returns:
            Созданная CreditTransaction
        """
        transaction = CreditTransaction(
            user_id=user_id,
            transaction_type='debit' if amount < 0 else 'credit',
            amount=amount,
            description=description,
            category=category,
            details=details or {}
        )

        await self.credit_repo.create_transaction(transaction.dict())
        return transaction

    # ===========================================
    # Списание баллов
    # ===========================================

    async def deduct_credits(
        self,
        user_id: str,
        cost: int,
        description: str,
        category: str,
        details: Optional[Dict[str, Any]] = None
    ) -> CreditTransaction:
        """
        Списать баллы у пользователя с проверкой баланса

        Источник: backend/server.py строки 136-149

        Args:
            user_id: ID пользователя
            cost: Стоимость операции (положительное число)
            description: Описание операции
            category: Категория (из CREDIT_COSTS)
            details: Дополнительные данные

        Returns:
            Созданная CreditTransaction

        Raises:
            HTTPException: 404 если пользователь не найден
            HTTPException: 402 если недостаточно баллов
        """
        # Проверяем существование пользователя
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail='Пользователь не найден'
            )

        # Проверяем баланс
        credits_remaining = user.get('credits_remaining', 0)
        if credits_remaining < cost:
            raise HTTPException(
                status_code=402,
                detail='Недостаточно баллов для операции. Пополните баланс.'
            )

        # Списываем баллы
        await self.user_repo.increment_credits(user_id, -cost)

        # Записываем транзакцию (отрицательное значение)
        return await self.record_transaction(
            user_id=user_id,
            amount=-cost,
            description=description,
            category=category,
            details=details
        )

    # ===========================================
    # Начисление баллов
    # ===========================================

    async def add_credits(
        self,
        user_id: str,
        amount: int,
        description: str,
        category: str = 'manual_credit',
        details: Optional[Dict[str, Any]] = None
    ) -> CreditTransaction:
        """
        Начислить баллы пользователю

        Args:
            user_id: ID пользователя
            amount: Количество баллов для начисления
            description: Описание начисления
            category: Категория
            details: Дополнительные данные

        Returns:
            Созданная CreditTransaction

        Raises:
            HTTPException: 404 если пользователь не найден
        """
        # Проверяем существование пользователя
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail='Пользователь не найден'
            )

        # Начисляем баллы
        await self.user_repo.increment_credits(user_id, amount)

        # Записываем транзакцию
        return await self.record_transaction(
            user_id=user_id,
            amount=amount,
            description=description,
            category=category,
            details=details
        )

    # ===========================================
    # История транзакций
    # ===========================================

    async def get_user_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Получить историю транзакций баллов пользователя

        Источник: backend/server.py строки 152-172

        Args:
            user_id: ID пользователя
            limit: Максимальное количество транзакций
            offset: Смещение для пагинации

        Returns:
            Dict с transactions и total
        """
        return await self.credit_repo.get_user_history(user_id, limit, offset)

    # ===========================================
    # Проверка стоимости операций
    # ===========================================

    def get_operation_cost(self, category: str) -> int:
        """
        Получить стоимость операции по категории

        Args:
            category: Категория операции

        Returns:
            Стоимость в баллах

        Raises:
            HTTPException: 400 если категория не найдена
        """
        if category not in CREDIT_COSTS:
            raise HTTPException(
                status_code=400,
                detail=f'Неизвестная категория: {category}'
            )
        return CREDIT_COSTS[category]

    async def can_afford_operation(
        self,
        user_id: str,
        category: str
    ) -> bool:
        """
        Проверить может ли пользователь позволить себе операцию

        Args:
            user_id: ID пользователя
            category: Категория операции

        Returns:
            True если достаточно баллов, False иначе
        """
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            return False

        cost = self.get_operation_cost(category)
        return user.get('credits_remaining', 0) >= cost

    # ===========================================
    # Аналитика
    # ===========================================

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Получить статистику по баллам пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Dict с total_earned, total_spent, spending_by_category
        """
        total_earned = await self.credit_repo.get_total_credits_earned(user_id)
        total_spent = await self.credit_repo.get_total_credits_spent(user_id)
        spending_by_category = await self.credit_repo.get_spending_by_category(user_id)

        # Получаем текущий баланс
        user = await self.user_repo.find_by_id(user_id)
        current_balance = user.get('credits_remaining', 0) if user else 0

        return {
            'current_balance': current_balance,
            'total_earned': total_earned,
            'total_spent': total_spent,
            'spending_by_category': spending_by_category
        }


__all__ = ['CreditService']
