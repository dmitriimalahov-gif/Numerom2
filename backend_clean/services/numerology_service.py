"""
Numerology Service

Бизнес-логика для нумерологических расчётов

Исходный код перенесён из:
- backend/server.py строки 413-565 (numerology endpoints)
- backend/numerology.py (функции расчётов)
- backend/vedic_numerology.py (ведическая нумерология)
- backend/enhanced_numerology.py (расширенная нумерология)

Дата создания: 2025-10-09
"""

from fastapi import HTTPException
from typing import Dict, Any, Optional
from datetime import datetime
import sys
import os

# Импортируем функции расчётов из старого backend
# TODO: В будущем эти функции нужно перенести в отдельный модуль utils/calculations
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

try:
    from numerology import (
        calculate_personal_numbers,
        create_pythagorean_square,
        parse_birth_date,
        calculate_compatibility,
        calculate_group_compatibility
    )
    from vedic_numerology import calculate_comprehensive_vedic_numerology
    from enhanced_numerology import (
        create_enhanced_pythagorean_square,
        get_personal_numbers as calculate_enhanced_personal_numbers
    )

    print("✅ Successfully imported numerology calculation modules")
except ImportError as e:
    # Fallback если модули не найдены
    print(f"⚠️  Warning: Could not import numerology modules: {e}")
    calculate_personal_numbers = None
    create_pythagorean_square = None
    parse_birth_date = None
    calculate_compatibility = None
    calculate_group_compatibility = None
    calculate_comprehensive_vedic_numerology = None
    create_enhanced_pythagorean_square = None
    calculate_enhanced_personal_numbers = None

from database.repositories.user_repository import UserRepository
from database.repositories.numerology_repository import NumerologyRepository
from database.repositories.credit_repository import CreditRepository
from services.credit_service import CreditService
from models.numerology import NumerologyCalculation
from models.credit import CREDIT_COSTS


class NumerologyService:
    """
    Сервис для нумерологических расчётов

    Обрабатывает все виды нумерологических расчётов с списанием баллов
    """

    def __init__(
        self,
        user_repo: UserRepository,
        numerology_repo: NumerologyRepository,
        credit_service: CreditService
    ):
        """
        Инициализация NumerologyService

        Args:
            user_repo: UserRepository instance
            numerology_repo: NumerologyRepository instance
            credit_service: CreditService instance
        """
        self.user_repo = user_repo
        self.numerology_repo = numerology_repo
        self.credit_service = credit_service

    # ===========================================
    # Персональные числа
    # ===========================================

    async def calculate_personal_numbers(
        self,
        user_id: str,
        birth_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Расчёт персональных чисел

        Источник: backend/server.py строки 413-438

        Args:
            user_id: ID пользователя
            birth_date: Дата рождения (DD.MM.YYYY), если None - берётся из профиля

        Returns:
            Dict с персональными числами

        Raises:
            HTTPException: 404 если пользователь не найден
            HTTPException: 402 если недостаточно баллов
        """
        # Получаем дату рождения если не указана
        if not birth_date:
            user = await self.user_repo.find_by_id(user_id)
            if not user:
                raise HTTPException(status_code=404, detail='Пользователь не найден')
            birth_date = user.get('birth_date')

        # Списываем баллы
        await self.credit_service.deduct_credits(
            user_id=user_id,
            cost=CREDIT_COSTS['personal_numbers'],
            description='Расчёт персональных чисел',
            category='numerology',
            details={'calculation_type': 'personal_numbers', 'birth_date': birth_date}
        )

        # Выполняем расчёт
        if calculate_personal_numbers is None:
            raise HTTPException(status_code=500, detail='Calculation module not available')

        results = calculate_personal_numbers(birth_date)

        # Сохраняем результат
        calc = NumerologyCalculation(
            user_id=user_id,
            birth_date=birth_date,
            calculation_type='personal_numbers',
            results=results
        )
        await self.numerology_repo.save_calculation(calc.dict())

        return results

    # ===========================================
    # Квадрат Пифагора
    # ===========================================

    async def calculate_pythagorean_square(
        self,
        user_id: str,
        birth_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Расчёт квадрата Пифагора

        Источник: backend/server.py строки 440-466

        Args:
            user_id: ID пользователя
            birth_date: Дата рождения (DD.MM.YYYY), если None - берётся из профиля

        Returns:
            Dict с квадратом Пифагора

        Raises:
            HTTPException: 404 если пользователь не найден
            HTTPException: 402 если недостаточно баллов
        """
        # Получаем дату рождения если не указана
        if not birth_date:
            user = await self.user_repo.find_by_id(user_id)
            if not user:
                raise HTTPException(status_code=404, detail='Пользователь не найден')
            birth_date = user.get('birth_date')

        # Списываем баллы
        await self.credit_service.deduct_credits(
            user_id=user_id,
            cost=CREDIT_COSTS['pythagorean_square'],
            description='Расчёт квадрата Пифагора',
            category='numerology',
            details={'calculation_type': 'pythagorean_square', 'birth_date': birth_date}
        )

        # Выполняем расчёт
        if parse_birth_date is None or create_pythagorean_square is None:
            raise HTTPException(status_code=500, detail='Calculation module not available')

        d, m, y = parse_birth_date(birth_date)
        results = create_pythagorean_square(d, m, y)

        # Сохраняем результат
        calc = NumerologyCalculation(
            user_id=user_id,
            birth_date=birth_date,
            calculation_type='pythagorean_square',
            results=results
        )
        await self.numerology_repo.save_calculation(calc.dict())

        return results

    # ===========================================
    # Совместимость
    # ===========================================

    async def calculate_compatibility(
        self,
        user_id: str,
        person1_birth_date: str,
        person2_birth_date: str,
        person1_name: str = "Человек 1",
        person2_name: str = "Человек 2"
    ) -> Dict[str, Any]:
        """
        Расчёт совместимости пары

        Источник: backend/server.py строки 468-492

        Args:
            user_id: ID пользователя
            person1_birth_date: Дата рождения первого человека
            person2_birth_date: Дата рождения второго человека
            person1_name: Имя первого человека
            person2_name: Имя второго человека

        Returns:
            Dict с результатами совместимости

        Raises:
            HTTPException: 402 если недостаточно баллов
        """
        # Списываем баллы
        await self.credit_service.deduct_credits(
            user_id=user_id,
            cost=CREDIT_COSTS['compatibility'],
            description='Расчёт совместимости пары',
            category='numerology',
            details={
                'calculation_type': 'compatibility',
                'person1_birth_date': person1_birth_date,
                'person2_birth_date': person2_birth_date
            }
        )

        # Выполняем расчёт
        if calculate_compatibility is None:
            raise HTTPException(status_code=500, detail='Calculation module not available')

        results = calculate_compatibility(
            person1_birth_date,
            person2_birth_date,
            person1_name,
            person2_name
        )

        # Сохраняем результат
        calc = NumerologyCalculation(
            user_id=user_id,
            birth_date=f"{person1_birth_date}+{person2_birth_date}",
            calculation_type='compatibility',
            results=results
        )
        await self.numerology_repo.save_calculation(calc.dict())

        return results

    # ===========================================
    # Групповая совместимость
    # ===========================================

    async def calculate_group_compatibility(
        self,
        user_id: str,
        main_person_birth_date: str,
        main_person_name: str,
        people: list
    ) -> Dict[str, Any]:
        """
        Расчёт групповой совместимости

        Источник: backend/server.py строки 494-524

        Args:
            user_id: ID пользователя
            main_person_birth_date: Дата рождения главного человека
            main_person_name: Имя главного человека
            people: Список людей для сравнения (до 5 человек)

        Returns:
            Dict с результатами групповой совместимости

        Raises:
            HTTPException: 400 если слишком много людей
            HTTPException: 402 если недостаточно баллов
        """
        if len(people) > 5:
            raise HTTPException(
                status_code=400,
                detail='Максимум 5 человек для групповой совместимости'
            )

        # Списываем баллы
        await self.credit_service.deduct_credits(
            user_id=user_id,
            cost=CREDIT_COSTS['group_compatibility'],
            description='Расчёт групповой совместимости',
            category='numerology',
            details={
                'calculation_type': 'group_compatibility',
                'main_person': main_person_birth_date,
                'people_count': len(people)
            }
        )

        # Выполняем расчёт
        if calculate_group_compatibility is None:
            raise HTTPException(status_code=500, detail='Calculation module not available')

        results = calculate_group_compatibility(
            main_person_birth_date,
            main_person_name,
            people
        )

        # Сохраняем результат
        calc = NumerologyCalculation(
            user_id=user_id,
            birth_date=main_person_birth_date,
            calculation_type='group_compatibility',
            results=results
        )
        await self.numerology_repo.save_calculation(calc.dict())

        return results

    # ===========================================
    # Бесплатный расчёт
    # ===========================================

    async def free_calculation(
        self,
        birth_date: str
    ) -> Dict[str, Any]:
        """
        Бесплатный расчёт (без авторизации)

        Источник: backend/server.py строки 526-540

        Args:
            birth_date: Дата рождения (DD.MM.YYYY)

        Returns:
            Dict с базовыми персональными числами
        """
        if calculate_personal_numbers is None:
            raise HTTPException(status_code=500, detail='Calculation module not available')

        results = calculate_personal_numbers(birth_date)

        # Сохраняем анонимный расчёт (без user_id)
        calc = NumerologyCalculation(
            user_id=None,
            birth_date=birth_date,
            calculation_type='free_calculation',
            results=results
        )
        await self.numerology_repo.save_calculation(calc.dict())

        return results

    # ===========================================
    # История расчётов
    # ===========================================

    async def get_user_calculations(
        self,
        user_id: str,
        calculation_type: Optional[str] = None,
        limit: int = 50
    ) -> list:
        """
        Получить историю расчётов пользователя

        Args:
            user_id: ID пользователя
            calculation_type: Фильтр по типу (опционально)
            limit: Максимальное количество

        Returns:
            Список расчётов
        """
        return await self.numerology_repo.find_by_user(
            user_id=user_id,
            calculation_type=calculation_type,
            limit=limit
        )

    async def get_calculation_stats(
        self,
        user_id: str
    ) -> Dict[str, int]:
        """
        Получить статистику расчётов пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Dict с количеством по типам
        """
        return await self.numerology_repo.count_calculations_by_type(user_id)


__all__ = ['NumerologyService']
