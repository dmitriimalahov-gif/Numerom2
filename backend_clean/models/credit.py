"""
Credit модели (система баллов)

Исходный код перенесён из:
- backend/models.py (строки 224-249)

Дата переноса: 2025-10-09
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


# ===========================================
# Credit Transaction Model
# ===========================================

class CreditTransaction(BaseModel):
    """
    Модель транзакции баллов

    Используется для истории начисления и списания кредитов
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    transaction_type: str  # 'debit' или 'credit'
    amount: int  # количество баллов (положительное для пополнения, отрицательное для списания)
    description: str  # описание за что списано/начислено
    category: str  # категория: 'numerology', 'vedic', 'learning', 'quiz', 'materials', 'purchase', etc.
    details: Optional[dict] = None  # дополнительные детали транзакции
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ===========================================
# Credit Costs Configuration
# ===========================================

CREDIT_COSTS = {
    # Нумерология
    'name_numerology': 1,           # Нумерология имени
    'personal_numbers': 1,          # Персональные числа
    'pythagorean_square': 1,        # Квадрат Пифагора
    'compatibility_pair': 1,        # Совместимость пары
    'group_compatibility': 5,       # Групповая совместимость (5 человек)

    # Ведическая нумерология
    'vedic_daily': 1,              # Ведическое время на день
    'planetary_daily': 1,           # Планетарный маршрут на день
    'planetary_monthly': 5,         # Планетарный маршрут на месяц
    'planetary_quarterly': 10,      # Планетарный маршрут на квартал

    # Обучение
    'lesson_viewing': 10,           # Просмотр урока
    'quiz_completion': 1,           # Прохождение Quiz
    'material_viewing': 1,          # Просмотр материалов

    # Тесты
    'personality_test': 1,          # Тест личности
}


__all__ = [
    'CreditTransaction',
    'CREDIT_COSTS',
]
