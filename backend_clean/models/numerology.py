"""
Numerology Models

Модели для нумерологических расчётов

Исходный код перенесён из:
- backend/models.py строки 93-149 (Request/Response модели)
- backend/models.py строки 231-256 (VedicNumerologyResult)
- backend/models.py строки 284-308 (EnhancedPythagoreanSquare)

Дата создания: 2025-10-09
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


# ===========================================
# Request Models
# ===========================================

class FreeCalculationRequest(BaseModel):
    """
    Запрос для бесплатного расчёта

    Источник: backend/models.py строка 109-110
    """
    birth_date: str  # DD.MM.YYYY


class CompatibilityRequest(BaseModel):
    """
    Запрос для расчёта совместимости пары

    Источник: backend/models.py строки 94-98
    """
    person1_birth_date: str  # DD.MM.YYYY
    person2_birth_date: str  # DD.MM.YYYY
    person1_name: Optional[str] = "Человек 1"
    person2_name: Optional[str] = "Человек 2"


class GroupCompatibilityPerson(BaseModel):
    """
    Человек для групповой совместимости

    Источник: backend/models.py строки 100-102
    """
    name: str
    birth_date: str  # DD.MM.YYYY


class GroupCompatibilityRequest(BaseModel):
    """
    Запрос для расчёта групповой совместимости

    Источник: backend/models.py строки 104-107
    """
    main_person_birth_date: str  # DD.MM.YYYY основного пользователя
    main_person_name: str = "Вы"
    people: List[GroupCompatibilityPerson]  # До 5 человек


# ===========================================
# Response Models - Personal Numbers
# ===========================================

class PersonalNumbersResponse(BaseModel):
    """
    Ответ с персональными числами

    Источник: backend/models.py строки 113-121
    """
    soul_number: int  # ЧД - число души
    mind_number: int  # ЧУ - число ума
    destiny_number: int  # ЧС - число судьбы
    helping_mind_number: int  # ЧУ* - помогающее число ума
    wisdom_number: int  # ЧМ - число мудрости
    ruling_number: int  # ПЧ - правящее число
    planetary_strength: Dict[str, int]  # Сила планет
    birth_weekday: str  # День недели рождения


class PersonalNumbersResult(BaseModel):
    """
    Детальный результат персональных чисел

    Источник: backend/models.py строки 130-140
    """
    life_path: int
    destiny: int
    soul: int
    ruling_number: int
    problem_number: int
    life_path_code: str
    planetary_strength: Dict[str, int]
    individual_year: int
    individual_month: int
    individual_day: int


# ===========================================
# Response Models - Pythagorean Square
# ===========================================

class PythagoreanSquareResult(BaseModel):
    """
    Результат расчёта квадрата Пифагора

    Источник: backend/models.py строки 142-148
    """
    square: List[List[str]]
    horizontal_sums: List[int]
    vertical_sums: List[int]
    diagonal_sums: List[int]
    additional_numbers: List[int]
    planet_positions: Dict[str, List[int]]


class EnhancedPythagoreanSquare(BaseModel):
    """
    Расширенный квадрат Пифагора с планетарными энергиями

    Источник: backend/models.py строки 285-308
    """
    # Полная матрица с планетарными энергиями
    square: List[List[str]]  # 3x3 matrix with numbers
    planet_positions: Dict[str, Dict[str, Any]]  # планета -> {цифры, сила, описание}

    # Все виды чисел
    life_path: int  # Число жизненного пути
    destiny: int  # Число судьбы
    soul: int  # Число души
    mind: int  # Число ума (ЧУ)
    personality: int  # Число личности (ЧМ)
    power: int  # Число силы (ПЧ)

    # Энергетический анализ
    energy_totals: Dict[str, int]  # общее количество каждой цифры
    energy_strength: Dict[str, str]  # сила каждой планеты (слабая/средняя/сильная)

    # Линии и суммы
    horizontal_sums: List[int]  # материальная сфера
    vertical_sums: List[int]  # духовная сфера
    diagonal_sums: List[int]  # баланс

    # Рекомендации для каждой планеты
    recommendations: Dict[str, List[str]]


# ===========================================
# Vedic Numerology Models
# ===========================================

class VedicNumerologyResult(BaseModel):
    """
    Результат ведической нумерологии

    Источник: backend/models.py строки 231-255
    """
    # Core numbers with Vedic terminology
    janma_ank: int  # Life Path (Birth Number)
    nama_ank: int  # Name Number
    bhagya_ank: int  # Destiny Number
    atma_ank: int  # Soul Number
    shakti_ank: int  # Power Number

    # Planetary influences (Vedic names)
    graha_shakti: Dict[str, int]  # Planetary strength

    # Vedic periods
    mahadasha: str  # Major period
    antardasha: str  # Minor period

    # Yantra (Square) analysis
    yantra_matrix: List[List[str]]
    yantra_sums: Dict[str, List[int]]

    # Recommendations in Sanskrit/Vedic context
    upayas: List[str]  # Remedies
    mantras: List[str]  # Chants
    gemstones: List[str]  # Ratnas

    created_at: datetime = Field(default_factory=datetime.utcnow)


# ===========================================
# Calculation Storage
# ===========================================

class NumerologyCalculation(BaseModel):
    """
    Сохранённый расчёт нумерологии

    Источник: backend/models.py строки 123-128

    Используется для хранения всех видов расчётов в БД
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    birth_date: str
    calculation_type: str  # "personal_numbers", "pythagorean_square", "compatibility", etc.
    results: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ===========================================
# Planetary Energy Models
# ===========================================

class PlanetaryEnergyData(BaseModel):
    """
    Данные планетарных энергий

    Источник: backend/models.py строки 198-211
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    date: datetime
    surya: int  # Sun
    chandra: int  # Moon
    mangal: int  # Mars
    budha: int  # Mercury
    guru: int  # Jupiter
    shukra: int  # Venus
    shani: int  # Saturn
    rahu: int  # Rahu
    ketu: int  # Ketu
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WeeklyEnergyForecast(BaseModel):
    """
    Недельный энергетический прогноз

    Источник: backend/models.py строки 213-220
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    week_start: datetime
    daily_energies: List[Dict[str, Any]]  # 7 days of energy data
    dominant_planet: str
    recommendations: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ===========================================
# Vedic Time Models
# ===========================================

class VedicTimeRequest(BaseModel):
    """
    Запрос для ведического времени

    Источник: backend/models.py строки 271-273
    """
    city: Optional[str] = None
    date: Optional[str] = None  # YYYY-MM-DD format, если не указана - сегодня


class PlanetaryDaySchedule(BaseModel):
    """
    Планетарный расписание на день

    Источник: backend/models.py строки 311-330
    """
    date: str
    city: str
    timezone: str

    # Временные периоды
    sunrise: str
    sunset: str
    rahu_kaal: Dict[str, str]  # start, end, duration
    gulika_kaal: Dict[str, str]  # start, end, duration
    yamaghanta: Dict[str, str]  # start, end, duration
    abhijit_muhurta: Dict[str, str]  # start, end, duration

    # Планетарные часы дня (12 часов)
    planetary_hours: List[Dict[str, Any]]

    # Персональные рекомендации
    daily_recommendations: Dict[str, Any]
    ruling_planet: str
    favorable_hours: List[str]


__all__ = [
    # Request models
    'FreeCalculationRequest',
    'CompatibilityRequest',
    'GroupCompatibilityPerson',
    'GroupCompatibilityRequest',
    'VedicTimeRequest',

    # Response models - Personal Numbers
    'PersonalNumbersResponse',
    'PersonalNumbersResult',

    # Response models - Pythagorean Square
    'PythagoreanSquareResult',
    'EnhancedPythagoreanSquare',

    # Vedic models
    'VedicNumerologyResult',

    # Storage
    'NumerologyCalculation',

    # Planetary
    'PlanetaryEnergyData',
    'WeeklyEnergyForecast',
    'PlanetaryDaySchedule',
]
