"""
Payment модели (платежи через Stripe)

Исходный код перенесён из:
- backend/models.py (строки 71-86)

Дата переноса: 2025-10-09
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


# ===========================================
# Payment Transaction Model
# ===========================================

class PaymentTransaction(BaseModel):
    """
    Модель платежной транзакции

    Хранит информацию о платежах через Stripe
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    package_type: str  # "one_time", "monthly", "annual", "master_consultation"
    amount: float
    currency: str = "eur"
    session_id: str  # Stripe Checkout Session ID
    payment_status: str = "pending"  # pending, paid, failed, expired
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ===========================================
# Payment Request Model
# ===========================================

class PaymentRequest(BaseModel):
    """
    Модель запроса на создание платежа

    Используется для создания Stripe Checkout Session
    """
    package_type: str  # "one_time", "monthly", "annual", "master_consultation"
    origin_url: str  # URL для редиректа после оплаты


__all__ = [
    'PaymentTransaction',
    'PaymentRequest',
]
