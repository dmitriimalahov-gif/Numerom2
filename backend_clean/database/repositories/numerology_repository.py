"""
Numerology Repository

Репозиторий для работы с нумерологическими расчётами

Источник:
- backend/server.py строки 394-565 (numerology endpoints используют прямые DB запросы)

Коллекции:
- numerology_calculations: хранение расчётов
- planetary_energy_data: данные планетарных энергий
- weekly_energy_forecasts: недельные прогнозы

Дата создания: 2025-10-09
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from database.repositories.base import BaseRepository


class NumerologyRepository(BaseRepository):
    """
    Репозиторий для нумерологических расчётов

    Источник: backend/server.py строки 394-565
    """

    collection_name = 'numerology_calculations'

    # ===========================================
    # Базовые операции с расчётами
    # ===========================================

    async def save_calculation(
        self,
        calculation: Dict[str, Any]
    ) -> str:
        """
        Сохранить нумерологический расчёт

        Args:
            calculation: Данные расчёта

        Returns:
            ID созданного расчёта
        """
        result = await self.create(calculation)
        return result

    async def find_by_user(
        self,
        user_id: str,
        calculation_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Получить расчёты пользователя

        Args:
            user_id: ID пользователя
            calculation_type: Тип расчёта (опционально)
            limit: Максимальное количество

        Returns:
            Список расчётов
        """
        query = {'user_id': user_id}
        if calculation_type:
            query['calculation_type'] = calculation_type

        return await self.find_many(
            query=query,
            limit=limit,
            sort=[('created_at', -1)]
        )

    async def find_by_birth_date(
        self,
        birth_date: str,
        calculation_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Найти расчёт по дате рождения и типу

        Args:
            birth_date: Дата рождения (DD.MM.YYYY)
            calculation_type: Тип расчёта

        Returns:
            Расчёт или None
        """
        return await self.find_one({
            'birth_date': birth_date,
            'calculation_type': calculation_type
        })

    # ===========================================
    # Planetary Energy Data
    # ===========================================

    async def save_planetary_energy(
        self,
        energy_data: Dict[str, Any]
    ) -> str:
        """
        Сохранить данные планетарных энергий

        Args:
            energy_data: Данные энергий

        Returns:
            ID созданной записи
        """
        return await self.collection.database['planetary_energy_data'].insert_one(
            energy_data
        ).inserted_id

    async def get_planetary_energy(
        self,
        user_id: str,
        date: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Получить планетарные энергии на дату

        Args:
            user_id: ID пользователя
            date: Дата

        Returns:
            Данные энергий или None
        """
        # Ищем энергии на конкретную дату
        result = await self.collection.database['planetary_energy_data'].find_one({
            'user_id': user_id,
            'date': {
                '$gte': datetime(date.year, date.month, date.day),
                '$lt': datetime(date.year, date.month, date.day + 1)
            }
        })
        return result

    async def get_energy_history(
        self,
        user_id: str,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Получить историю энергий пользователя

        Args:
            user_id: ID пользователя
            limit: Количество дней

        Returns:
            История энергий
        """
        cursor = self.collection.database['planetary_energy_data'].find(
            {'user_id': user_id}
        ).sort('date', -1).limit(limit)

        return await cursor.to_list(limit)

    # ===========================================
    # Weekly Energy Forecasts
    # ===========================================

    async def save_weekly_forecast(
        self,
        forecast: Dict[str, Any]
    ) -> str:
        """
        Сохранить недельный прогноз

        Args:
            forecast: Данные прогноза

        Returns:
            ID созданного прогноза
        """
        return await self.collection.database['weekly_energy_forecasts'].insert_one(
            forecast
        ).inserted_id

    async def get_weekly_forecast(
        self,
        user_id: str,
        week_start: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Получить недельный прогноз

        Args:
            user_id: ID пользователя
            week_start: Начало недели

        Returns:
            Прогноз или None
        """
        result = await self.collection.database['weekly_energy_forecasts'].find_one({
            'user_id': user_id,
            'week_start': week_start
        })
        return result

    async def get_recent_forecasts(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Получить последние прогнозы пользователя

        Args:
            user_id: ID пользователя
            limit: Количество прогнозов

        Returns:
            Список прогнозов
        """
        cursor = self.collection.database['weekly_energy_forecasts'].find(
            {'user_id': user_id}
        ).sort('week_start', -1).limit(limit)

        return await cursor.to_list(limit)

    # ===========================================
    # Statistics
    # ===========================================

    async def count_calculations_by_type(
        self,
        user_id: str
    ) -> Dict[str, int]:
        """
        Подсчитать количество расчётов по типам

        Args:
            user_id: ID пользователя

        Returns:
            Dict с количеством по типам
        """
        pipeline = [
            {'$match': {'user_id': user_id}},
            {'$group': {
                '_id': '$calculation_type',
                'count': {'$sum': 1}
            }}
        ]

        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(None)

        return {item['_id']: item['count'] for item in results}

    async def get_total_calculations(
        self,
        user_id: Optional[str] = None
    ) -> int:
        """
        Получить общее количество расчётов

        Args:
            user_id: ID пользователя (опционально, если None - все пользователи)

        Returns:
            Количество расчётов
        """
        query = {'user_id': user_id} if user_id else {}
        return await self.count(query)


__all__ = ['NumerologyRepository']
