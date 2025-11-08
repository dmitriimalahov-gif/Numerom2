"""
Payment Service

Бизнес-логика для обработки платежей через Stripe

Исходный код перенесён из:
- backend/server.py строки 234-283 (create_checkout_session)
- backend/server.py строки 285-375 (get_payment_status, процессинг оплаты)
- backend/server.py строки 377-392 (stripe_webhook)

Дата создания: 2025-10-09
"""

import stripe
import uuid
from fastapi import HTTPException
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

from database.repositories.user_repository import UserRepository
from database.repositories.payment_repository import PaymentRepository
from models.payment import PaymentTransaction
from core.config import settings

logger = logging.getLogger(__name__)

# Stripe configuration
stripe.api_key = settings.STRIPE_SECRET_KEY

# Subscription credits mapping
SUBSCRIPTION_CREDITS = {
    'one_time': 10,
    'monthly': 50,
    'annual': 600,
    'master_consultation': 0  # No credits, just consultation access
}

# Pricing in EUR
SUBSCRIPTION_PRICES = {
    'one_time': 9.99,
    'monthly': 29.99,
    'annual': 299.99,
    'master_consultation': 199.99
}


class PaymentService:
    """
    Сервис для обработки платежей и подписок

    Обрабатывает создание Stripe сессий, проверку статуса платежей,
    начисление баллов и обновление подписок
    """

    def __init__(
        self,
        user_repo: UserRepository,
        payment_repo: PaymentRepository
    ):
        """
        Инициализация PaymentService

        Args:
            user_repo: UserRepository instance
            payment_repo: PaymentRepository instance
        """
        self.user_repo = user_repo
        self.payment_repo = payment_repo

    # ===========================================
    # Создание Checkout Session
    # ===========================================

    async def create_checkout_session(
        self,
        user_id: str,
        package_type: str,
        origin_url: str
    ) -> Dict[str, str]:
        """
        Создать Stripe Checkout Session

        Источник: backend/server.py строки 234-283

        Args:
            user_id: ID пользователя
            package_type: Тип пакета (one_time, monthly, annual, master_consultation)
            origin_url: URL для редиректа

        Returns:
            Dict с url и session_id

        Raises:
            HTTPException: 400 если неверный package_type
            HTTPException: 500 если ошибка Stripe
        """
        # Проверяем package_type
        if package_type not in SUBSCRIPTION_PRICES:
            raise HTTPException(
                status_code=400,
                detail=f'Invalid package type: {package_type}'
            )

        amount = SUBSCRIPTION_PRICES[package_type]

        # Demo mode
        if settings.PAYMENT_DEMO_MODE:
            session_id = f'demo_{uuid.uuid4().hex[:24]}'

            transaction = PaymentTransaction(
                package_type=package_type,
                amount=amount,
                currency='eur',
                session_id=session_id,
                payment_status='pending',
                metadata={'origin_url': origin_url, 'demo': True},
                user_id=user_id
            )
            await self.payment_repo.create_transaction(transaction.dict())

            url = f"{origin_url}/payment-success?session_id={session_id}&demo=true"
            return {'url': url, 'session_id': session_id}

        # Real Stripe mode
        try:
            success_url = f"{origin_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = f"{origin_url}/payment-cancelled"

            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': f'Numerom Package: {package_type}',
                        },
                        'unit_amount': int(amount * 100),  # Stripe expects cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'package_type': package_type,
                    'origin_url': origin_url,
                    'user_id': user_id
                }
            )

            transaction = PaymentTransaction(
                package_type=package_type,
                amount=amount,
                currency='eur',
                session_id=session.id,
                payment_status='pending',
                metadata={'origin_url': origin_url},
                user_id=user_id
            )
            await self.payment_repo.create_transaction(transaction.dict())

            return {'url': session.url, 'session_id': session.id}

        except Exception as e:
            logger.error(f'Stripe error: {e}')
            raise HTTPException(
                status_code=500,
                detail=f'Failed to create checkout session: {e}'
            )

    # ===========================================
    # Проверка статуса платежа
    # ===========================================

    async def get_payment_status(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Проверить статус платежа и обработать успешную оплату

        Источник: backend/server.py строки 285-375

        Args:
            session_id: Stripe Session ID

        Returns:
            Dict со статусом платежа

        Raises:
            HTTPException: 404 если транзакция не найдена
            HTTPException: 500 если ошибка Stripe
        """
        # Получаем транзакцию
        tx = await self.payment_repo.find_by_session_id(session_id)
        if not tx:
            raise HTTPException(
                status_code=404,
                detail='Transaction not found'
            )

        # Demo mode
        if settings.PAYMENT_DEMO_MODE or tx.get('metadata', {}).get('demo'):
            package = tx['package_type']
            user_id = tx.get('user_id')

            # КРИТИЧЕСКОЕ: Проверяем что баллы еще не начислены
            if user_id and tx.get('payment_status') != 'paid':
                await self._process_successful_payment(user_id, package)
                await self.payment_repo.mark_as_paid(session_id)

            return {
                'status': 'complete',
                'payment_status': 'paid',
                'amount_total': int(tx['amount'] * 100),
                'currency': 'eur',
                'user_id': user_id
            }

        # Real Stripe mode
        try:
            session = stripe.checkout.Session.retrieve(session_id)

            if session.payment_status == 'paid' and tx['payment_status'] != 'paid':
                package = tx['package_type']
                user_id = tx.get('user_id')

                if user_id:
                    await self._process_successful_payment(user_id, package)

                await self.payment_repo.update_status(
                    session_id,
                    session.payment_status
                )

            return {
                'status': session.status,
                'payment_status': session.payment_status,
                'amount_total': session.amount_total,
                'currency': session.currency
            }

        except Exception as e:
            logger.error(f'Stripe status check error: {e}')
            raise HTTPException(
                status_code=500,
                detail=f'Failed to check payment status: {e}'
            )

    # ===========================================
    # Обработка успешного платежа
    # ===========================================

    async def _process_successful_payment(
        self,
        user_id: str,
        package_type: str
    ) -> None:
        """
        Обработать успешный платеж - начислить баллы и обновить подписку

        Источник: backend/server.py строки 297-325, 337-365

        Args:
            user_id: ID пользователя
            package_type: Тип пакета
        """
        # Начисляем баллы
        credits_to_add = SUBSCRIPTION_CREDITS.get(package_type, 0)
        if credits_to_add > 0:
            await self.user_repo.increment_credits(user_id, credits_to_add)

        # Обновляем подписку
        if package_type == 'monthly':
            await self.user_repo.update_subscription(
                user_id,
                {
                    'is_premium': True,
                    'subscription_type': 'monthly',
                    'subscription_expires_at': datetime.utcnow() + timedelta(days=30)
                }
            )

        elif package_type == 'annual':
            await self.user_repo.update_subscription(
                user_id,
                {
                    'is_premium': True,
                    'subscription_type': 'annual',
                    'subscription_expires_at': datetime.utcnow() + timedelta(days=365)
                }
            )

        elif package_type == 'master_consultation':
            # TODO: Создать персональную консультацию
            # Это будет реализовано в ConsultationService
            pass

    # ===========================================
    # Stripe Webhook
    # ===========================================

    async def handle_stripe_webhook(
        self,
        body: bytes,
        signature: str
    ) -> Dict[str, bool]:
        """
        Обработать Stripe webhook

        Источник: backend/server.py строки 377-392

        Args:
            body: Request body
            signature: Stripe-Signature header

        Returns:
            Dict с received: True

        Raises:
            HTTPException: 400 если signature verification failed
        """
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(
                body, signature, webhook_secret
            )
            logger.info(f'Received Stripe webhook event: {event["type"]}')

            # TODO: Обработка различных типов событий
            # - checkout.session.completed
            # - payment_intent.succeeded
            # - payment_intent.payment_failed

            return {'received': True}

        except stripe.error.SignatureVerificationError as e:
            logger.error(f'Webhook signature verification failed: {e}')
            raise HTTPException(
                status_code=400,
                detail=f'Webhook signature verification failed: {e}'
            )
        except Exception as e:
            logger.error(f'Webhook error: {e}')
            raise HTTPException(
                status_code=400,
                detail=f'Webhook error: {e}'
            )

    # ===========================================
    # История платежей
    # ===========================================

    async def get_user_payments(
        self,
        user_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> Dict[str, Any]:
        """
        Получить историю платежей пользователя

        Args:
            user_id: ID пользователя
            limit: Максимальное количество
            skip: Пропустить N записей

        Returns:
            Dict с payments и total
        """
        payments = await self.payment_repo.find_by_user(user_id, limit, skip)
        total = await self.payment_repo.count({'user_id': user_id})

        # Очищаем от MongoDB _id
        clean_payments = [
            {k: v for k, v in payment.items() if k != '_id'}
            for payment in payments
        ]

        return {
            'payments': clean_payments,
            'total': total,
            'limit': limit,
            'skip': skip
        }


__all__ = ['PaymentService', 'SUBSCRIPTION_CREDITS', 'SUBSCRIPTION_PRICES']
