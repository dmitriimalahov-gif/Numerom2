"""
Credit API Router

API эндпоинты для работы с баллами пользователей

Источник:
- backend/server.py строки 152-172 (get_credit_history)

Дата создания: 2025-10-09
"""

from fastapi import APIRouter, Depends, Query
from typing import Dict, Any

from models.user import User
from services.credit_service import CreditService
from api.v1.dependencies import get_credit_service, get_current_user


router = APIRouter(prefix="/user", tags=["Credits"])


# ===========================================
# История транзакций баллов
# ===========================================

@router.get(
    "/credit-history",
    response_model=Dict[str, Any],
    summary="Получить историю транзакций баллов пользователя"
)
async def get_credit_history(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    credit_service: CreditService = Depends(get_credit_service)
) -> Dict[str, Any]:
    """
    Получить историю транзакций баллов пользователя

    Источник: backend/server.py строки 152-172

    **Требует авторизации:** Bearer token в заголовке Authorization

    **Query параметры:**
    - limit: Максимальное количество транзакций (1-100, по умолчанию 50)
    - offset: Смещение для пагинации (по умолчанию 0)

    **Возвращает:**
    - transactions: Список транзакций (отсортированные по дате DESC)
    - total: Общее количество транзакций
    - limit: Текущий limit
    - offset: Текущий offset

    **Формат транзакции:**
    - id: Уникальный ID транзакции
    - user_id: ID пользователя
    - transaction_type: Тип (credit - начисление, debit - списание)
    - amount: Количество баллов (положительное или отрицательное)
    - description: Описание операции
    - category: Категория (numerology, lesson_viewing, etc.)
    - details: Дополнительные данные
    - created_at: Дата создания
    """
    return await credit_service.get_user_history(
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )


# ===========================================
# Статистика по баллам
# ===========================================

@router.get(
    "/credit-stats",
    response_model=Dict[str, Any],
    summary="Получить статистику по баллам пользователя"
)
async def get_credit_stats(
    current_user: User = Depends(get_current_user),
    credit_service: CreditService = Depends(get_credit_service)
) -> Dict[str, Any]:
    """
    Получить статистику по баллам пользователя

    **Требует авторизации:** Bearer token в заголовке Authorization

    **Возвращает:**
    - current_balance: Текущий баланс баллов
    - total_earned: Всего заработано баллов
    - total_spent: Всего потрачено баллов
    - spending_by_category: Расходы по категориям

    **Пример ответа:**
    ```json
    {
      "current_balance": 45,
      "total_earned": 60,
      "total_spent": 15,
      "spending_by_category": {
        "numerology": 5,
        "lesson_viewing": 10
      }
    }
    ```
    """
    return await credit_service.get_user_stats(current_user.id)


__all__ = ['router']
