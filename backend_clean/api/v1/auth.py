"""
Authentication API Router

API эндпоинты для аутентификации и регистрации

Источник:
- backend/server.py строки 175-224 (register, login endpoints)

Дата создания: 2025-10-09
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional

from models.user import UserCreate, TokenResponse, LoginRequest, User, create_user_response
from services.auth_service import AuthService
from api.v1.dependencies import get_auth_service, get_current_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


# ===========================================
# Регистрация
# ===========================================

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Зарегистрировать нового пользователя"
)
async def register(
    user_data: UserCreate,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """
    Зарегистрировать нового пользователя

    Источник: backend/server.py строки 176-206

    **Требуемые поля:**
    - email: Email пользователя
    - password: Пароль (будет захеширован)
    - full_name: Полное имя
    - birth_date: Дата рождения в формате DD.MM.YYYY
    - city: Город (опционально, по умолчанию "Москва")
    - phone_number: Номер телефона (опционально)

    **Возвращает:**
    - access_token: JWT токен для авторизации
    - user: Данные зарегистрированного пользователя (без пароля)

    **Ошибки:**
    - 400: Пользователь с таким email уже существует
    """
    return await auth_service.register_user(user_data, request)


# ===========================================
# Вход
# ===========================================

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Войти в систему"
)
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """
    Войти в систему

    Источник: backend/server.py строки 208-224

    **Требуемые поля:**
    - email: Email пользователя
    - password: Пароль

    **Возвращает:**
    - access_token: JWT токен для авторизации
    - user: Данные пользователя (без пароля)

    **Ошибки:**
    - 401: Неверный email или пароль

    **Дополнительная логика:**
    - Проверяет срок действия подписки и обнуляет её при истечении
    - Обновляет время последнего входа
    """
    return await auth_service.login(login_data)


# ===========================================
# Получение информации о текущем пользователе
# ===========================================

@router.get(
    "/me",
    response_model=User,
    summary="Получить информацию о текущем пользователе"
)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Получить информацию о текущем авторизованном пользователе

    Источник: backend/server.py строки 227-232

    **Требует авторизации:** Bearer token в заголовке Authorization

    **Возвращает:**
    - Полную информацию о пользователе (включая баллы, подписку и т.д.)

    **Ошибки:**
    - 401: Невалидный или отсутствующий токен
    - 404: Пользователь не найден (токен валиден, но пользователь удалён)

    **Дополнительная логика:**
    - Проверяет срок действия подписки
    """
    return current_user


__all__ = ['router']
