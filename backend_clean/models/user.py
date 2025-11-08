"""
User модели

Исходный код перенесён из:
- backend/models.py (строки 7-73)

Дата переноса: 2025-10-09
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


# ===========================================
# User Creation & Update
# ===========================================

class UserCreate(BaseModel):
    """
    Модель для создания нового пользователя

    Используется при регистрации
    """
    email: str
    password: str
    full_name: str
    birth_date: str  # DD.MM.YYYY format
    city: Optional[str] = "Москва"  # Город по умолчанию
    phone_number: Optional[str] = None  # Номер телефона с кодом страны


class UserProfileUpdate(BaseModel):
    """
    Модель для обновления профиля пользователя

    Все поля опциональные - можно обновлять по отдельности
    """
    full_name: Optional[str] = None
    phone_number: Optional[str] = None  # +37369183398 format
    city: Optional[str] = None
    car_number: Optional[str] = None  # До 13 символов, любая раскладка
    street: Optional[str] = None
    house_number: Optional[str] = None
    apartment_number: Optional[str] = None
    postal_code: Optional[str] = None


# ===========================================
# User Response (API Response)
# ===========================================

class UserResponse(BaseModel):
    """
    Модель для возврата данных пользователя через API

    Не включает чувствительные данные (password_hash)
    """
    id: str
    email: str
    full_name: str
    birth_date: str
    city: str = "Москва"
    phone_number: Optional[str] = None
    car_number: Optional[str] = None
    street: Optional[str] = None
    house_number: Optional[str] = None
    apartment_number: Optional[str] = None
    postal_code: Optional[str] = None
    is_premium: bool = False
    is_super_admin: bool = False  # Суперадминистратор
    is_admin: bool = False  # Обычный администратор
    subscription_type: Optional[str] = None
    credits_remaining: int = 0
    created_at: datetime


# ===========================================
# User Database Model
# ===========================================

class User(BaseModel):
    """
    Полная модель пользователя для базы данных

    Включает все поля включая password_hash
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    password_hash: str
    full_name: str
    birth_date: str  # DD.MM.YYYY format
    city: str = "Москва"  # Город пользователя для временных расчетов
    phone_number: Optional[str] = None  # Номер телефона с кодом страны (+37369183398)
    car_number: Optional[str] = None  # Номер автомобиля (до 13 символов)
    street: Optional[str] = None  # Улица проживания
    house_number: Optional[str] = None  # Номер дома
    apartment_number: Optional[str] = None  # Номер квартиры
    postal_code: Optional[str] = None  # Почтовый индекс
    is_premium: bool = False
    is_super_admin: bool = False  # Суперадминистратор
    is_admin: bool = False  # Обычный администратор
    subscription_type: Optional[str] = None  # "monthly", "annual", None
    subscription_expires_at: Optional[datetime] = None
    credits_remaining: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ===========================================
# Authentication Models
# ===========================================

class LoginRequest(BaseModel):
    """Модель для входа пользователя"""
    email: str
    password: str


class TokenResponse(BaseModel):
    """
    Модель ответа после успешной аутентификации

    Возвращает JWT токен и данные пользователя
    """
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ===========================================
# Utility Functions
# ===========================================

def create_user_response(user: User) -> UserResponse:
    """
    Создать UserResponse из User модели

    Убирает чувствительные данные (password_hash) перед возвратом

    Args:
        user: User модель из БД

    Returns:
        UserResponse для API
    """
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        birth_date=user.birth_date,
        city=user.city,
        phone_number=user.phone_number,
        car_number=user.car_number,
        street=user.street,
        house_number=user.house_number,
        apartment_number=user.apartment_number,
        postal_code=user.postal_code,
        is_premium=user.is_premium,
        is_super_admin=user.is_super_admin,
        is_admin=user.is_admin,
        subscription_type=user.subscription_type,
        credits_remaining=user.credits_remaining,
        created_at=user.created_at
    )


__all__ = [
    # Creation & Update
    'UserCreate',
    'UserProfileUpdate',

    # Response
    'UserResponse',

    # Database Model
    'User',

    # Authentication
    'LoginRequest',
    'TokenResponse',

    # Utilities
    'create_user_response',
]
