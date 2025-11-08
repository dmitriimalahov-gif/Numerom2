"""
Payment API Router

API эндпоинты для обработки платежей через Stripe

Источник:
- backend/server.py строки 234-283 (create_checkout_session)
- backend/server.py строки 285-375 (get_payment_status)
- backend/server.py строки 377-392 (stripe_webhook)

Дата создания: 2025-10-09
"""

from fastapi import APIRouter, Depends, Request
from typing import Dict, Any
from pydantic import BaseModel

from models.user import User
from services.payment_service import PaymentService
from api.v1.dependencies import get_payment_service, get_current_user


router = APIRouter(prefix="/payments", tags=["Payments"])


# ===========================================
# Request/Response Models
# ===========================================

class PaymentRequest(BaseModel):
    """Request модель для создания платежа"""
    package_type: str
    origin_url: str


# ===========================================
# Создание Checkout Session
# ===========================================

@router.post(
    "/checkout",
    response_model=Dict[str, str],
    summary="Создать Stripe Checkout Session"
)
async def create_checkout_session(
    payment_request: PaymentRequest,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
) -> Dict[str, str]:
    """
    Создать Stripe Checkout Session для оплаты пакета

    Источник: backend/server.py строки 234-283

    **Требует авторизации:** Bearer token в заголовке Authorization

    **Body параметры:**
    - package_type: Тип пакета (one_time, monthly, annual, master_consultation)
    - origin_url: URL для редиректа после оплаты

    **Возвращает:**
    - url: URL для перехода на Stripe Checkout
    - session_id: ID сессии для проверки статуса

    **Пакеты и цены:**
    - one_time: 9.99 EUR - Разовая покупка 10 баллов
    - monthly: 29.99 EUR - Месячная подписка (50 баллов)
    - annual: 299.99 EUR - Годовая подписка (600 баллов)
    - master_consultation: 199.99 EUR - Персональная консультация

    **Demo mode:**
    - Если PAYMENT_DEMO_MODE=True, создаётся тестовая сессия без реального Stripe
    - Редирект на {origin_url}/payment-success?session_id={id}&demo=true

    **Ошибки:**
    - 400: Неверный package_type
    - 500: Ошибка создания Stripe сессии
    """
    return await payment_service.create_checkout_session(
        user_id=current_user.id,
        package_type=payment_request.package_type,
        origin_url=payment_request.origin_url
    )


# ===========================================
# Проверка статуса платежа
# ===========================================

@router.get(
    "/checkout/status/{session_id}",
    response_model=Dict[str, Any],
    summary="Проверить статус платежа"
)
async def get_payment_status(
    session_id: str,
    payment_service: PaymentService = Depends(get_payment_service)
) -> Dict[str, Any]:
    """
    Проверить статус Stripe платежа и обработать успешную оплату

    Источник: backend/server.py строки 285-375

    **Path параметры:**
    - session_id: Stripe Checkout Session ID

    **Возвращает:**
    - status: Статус сессии (complete, open, expired)
    - payment_status: Статус платежа (paid, unpaid, no_payment_required)
    - amount_total: Сумма в центах
    - currency: Валюта (eur)

    **Логика обработки:**
    1. Проверяет существование транзакции в БД
    2. В demo mode - сразу помечает как paid и начисляет баллы
    3. В real mode - получает статус из Stripe API
    4. При первой успешной оплате (paid):
       - Начисляет баллы согласно пакету
       - Обновляет подписку (monthly/annual)
       - Создаёт консультацию (master_consultation)
       - Помечает транзакцию как paid в БД

    **КРИТИЧЕСКОЕ:**
    - Проверяет что баллы начислены только 1 раз (payment_status != 'paid')

    **Ошибки:**
    - 404: Транзакция не найдена
    - 500: Ошибка Stripe API
    """
    return await payment_service.get_payment_status(session_id)


# ===========================================
# Stripe Webhook
# ===========================================

@router.post(
    "/webhook/stripe",
    response_model=Dict[str, bool],
    summary="Обработать Stripe webhook"
)
async def stripe_webhook(
    request: Request,
    payment_service: PaymentService = Depends(get_payment_service)
) -> Dict[str, bool]:
    """
    Обработать Stripe webhook события

    Источник: backend/server.py строки 377-392

    **Headers:**
    - Stripe-Signature: Подпись для верификации

    **События:**
    - checkout.session.completed: Сессия завершена
    - payment_intent.succeeded: Платёж успешен
    - payment_intent.payment_failed: Платёж не прошёл

    **Security:**
    - Проверяет подпись через STRIPE_WEBHOOK_SECRET
    - Отклоняет запросы с неверной подписью

    **Возвращает:**
    - received: True

    **Ошибки:**
    - 400: Неверная подпись или ошибка обработки
    """
    body = await request.body()
    signature = request.headers.get('Stripe-Signature')

    return await payment_service.handle_stripe_webhook(body, signature)


__all__ = ['router']
