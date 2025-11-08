"""
Consultation Service

Бизнес-логика для управления персональными консультациями

Исходный код перенесён из:
- backend/server.py строки 2088-2183 (admin consultation management)
- backend/server.py строки 2404-2424 (user consultation access)
- backend/server.py строки 2597-2690 (consultation purchase)

Дата создания: 2025-10-09
"""

from fastapi import HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from database.repositories.consultation_repository import ConsultationRepository
from services.credit_service import CreditService
from models.consultation import PersonalConsultation, ConsultationPurchase


class ConsultationService:
    """
    Сервис для управления персональными консультациями

    Обрабатывает создание, обновление, покупку и доступ к консультациям
    """

    def __init__(
        self,
        consultation_repo: ConsultationRepository,
        credit_service: CreditService
    ):
        """
        Инициализация ConsultationService

        Args:
            consultation_repo: ConsultationRepository instance
            credit_service: CreditService instance
        """
        self.consultation_repo = consultation_repo
        self.credit_service = credit_service

    # ===========================================
    # Получение консультаций (User)
    # ===========================================

    async def get_user_consultations(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Получить консультации назначенные пользователю

        Источник: backend/server.py строки 2404-2424

        Args:
            user_id: ID пользователя

        Returns:
            Список консультаций с флагом is_purchased
        """
        # Получаем консультации назначенные пользователю
        consultations = await self.consultation_repo.find_by_user(
            user_id=user_id,
            active_only=True
        )

        # Получаем информацию о покупках пользователя
        purchases = await self.consultation_repo.get_user_purchases(user_id)
        purchased_consultation_ids = {purchase['consultation_id'] for purchase in purchases}

        # Подготавливаем ответ
        result = []
        for consultation in consultations:
            consultation_dict = dict(consultation)
            consultation_dict.pop('_id', None)
            consultation_dict['is_purchased'] = consultation['id'] in purchased_consultation_ids
            result.append(consultation_dict)

        return result

    # ===========================================
    # Покупка консультации
    # ===========================================

    async def purchase_consultation(
        self,
        user_id: str,
        consultation_id: str
    ) -> Dict[str, Any]:
        """
        Купить консультацию за баллы

        Источник: backend/server.py строки 2597-2644

        Args:
            user_id: ID пользователя
            consultation_id: ID консультации

        Returns:
            Dict с результатом покупки

        Raises:
            HTTPException: 404 если консультация не найдена
            HTTPException: 400 если консультация уже куплена
            HTTPException: 402 если недостаточно баллов
        """
        # Проверяем существование консультации
        consultation = await self.consultation_repo.find_by_id_and_user(
            consultation_id=consultation_id,
            user_id=user_id
        )

        if not consultation:
            raise HTTPException(
                status_code=404,
                detail='Консультация не найдена или не назначена вам'
            )

        # Проверяем, не куплена ли уже
        already_purchased = await self.consultation_repo.check_if_purchased(
            user_id=user_id,
            consultation_id=consultation_id
        )

        if already_purchased:
            raise HTTPException(
                status_code=400,
                detail='Вы уже приобрели эту консультацию'
            )

        # Стоимость консультации
        cost = consultation.get('cost_credits', 6667)

        # Списываем баллы
        await self.credit_service.deduct_credits(
            user_id=user_id,
            cost=cost,
            description=f'Покупка консультации: {consultation.get("title", "Без названия")}',
            category='consultation',
            details={
                'consultation_id': consultation_id,
                'consultation_title': consultation.get('title')
            }
        )

        # Записываем покупку
        purchase = ConsultationPurchase(
            user_id=user_id,
            consultation_id=consultation_id,
            credits_spent=cost
        )
        await self.consultation_repo.record_purchase(purchase.dict())

        return {
            'success': True,
            'consultation_id': consultation_id,
            'credits_spent': cost,
            'message': 'Консультация успешно приобретена'
        }

    # ===========================================
    # CRUD операции (Admin)
    # ===========================================

    async def get_all_consultations(self) -> List[Dict[str, Any]]:
        """
        Получить все консультации (для админов)

        Источник: backend/server.py строки 2088-2099

        Returns:
            Список всех консультаций
        """
        consultations = await self.consultation_repo.find_all_consultations()

        # Очищаем от _id
        result = []
        for consultation in consultations:
            consultation_dict = dict(consultation)
            consultation_dict.pop('_id', None)
            result.append(consultation_dict)

        return result

    async def create_consultation(
        self,
        consultation_data: Dict[str, Any]
    ) -> str:
        """
        Создать консультацию (для админов)

        Источник: backend/server.py строки 2158-2168

        Args:
            consultation_data: Данные консультации

        Returns:
            ID созданной консультации
        """
        consultation = PersonalConsultation(**consultation_data)
        return await self.consultation_repo.create_consultation(consultation.dict())

    async def update_consultation(
        self,
        consultation_id: str,
        consultation_data: Dict[str, Any]
    ) -> bool:
        """
        Обновить консультацию (для админов)

        Источник: backend/server.py строки 2170-2176

        Args:
            consultation_id: ID консультации
            consultation_data: Новые данные

        Returns:
            True если обновлено

        Raises:
            HTTPException: 404 если консультация не найдена
        """
        consultation = await self.consultation_repo.find_consultation_by_id(consultation_id)
        if not consultation:
            raise HTTPException(status_code=404, detail='Консультация не найдена')

        return await self.consultation_repo.update_consultation(
            consultation_id,
            consultation_data
        )

    async def delete_consultation(
        self,
        consultation_id: str
    ) -> bool:
        """
        Удалить консультацию (для админов)

        Источник: backend/server.py строки 2179-2183

        Args:
            consultation_id: ID консультации

        Returns:
            True если удалено

        Raises:
            HTTPException: 404 если консультация не найдена
        """
        consultation = await self.consultation_repo.find_consultation_by_id(consultation_id)
        if not consultation:
            raise HTTPException(status_code=404, detail='Консультация не найдена')

        return await self.consultation_repo.delete_consultation(consultation_id)

    # ===========================================
    # Создание консультации при покупке пакета
    # ===========================================

    async def create_master_consultation_for_user(
        self,
        user_id: str
    ) -> str:
        """
        Создать персональную консультацию от мастера для пользователя

        Используется при покупке пакета 'master_consultation'

        Источник: backend/server.py строки 312-325, 352-365

        Args:
            user_id: ID пользователя

        Returns:
            ID созданной консультации
        """
        master_consultation = PersonalConsultation(
            title='Персональная консультация от мастера',
            description='Эксклюзивная персональная консультация от ведущего мастера нумерологии',
            assigned_user_id=user_id,
            cost_credits=0,  # Уже оплачено
            is_active=True,
            video_url='https://example.com/master-consultation-video',  # Будет заменено на реальное видео
        )

        return await self.consultation_repo.create_consultation(master_consultation.dict())

    # ===========================================
    # Статистика
    # ===========================================

    async def get_consultation_stats(self) -> Dict[str, Any]:
        """
        Получить статистику по консультациям

        Returns:
            Dict со статистикой
        """
        total_active = await self.consultation_repo.count_active_consultations()
        revenue = await self.consultation_repo.get_consultation_revenue()

        return {
            'total_active_consultations': total_active,
            'total_purchases': revenue.get('total_purchases', 0),
            'total_credits_spent': revenue.get('total_credits_spent', 0)
        }

    async def get_user_consultation_stats(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Получить статистику консультаций пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Dict со статистикой
        """
        total_assigned = await self.consultation_repo.count_user_consultations(user_id)
        purchases = await self.consultation_repo.get_user_purchases(user_id)

        total_spent = sum(p.get('credits_spent', 0) for p in purchases)

        return {
            'total_assigned': total_assigned,
            'total_purchased': len(purchases),
            'total_credits_spent': total_spent
        }


__all__ = ['ConsultationService']
