"""
Authentication Service

Бизнес-логика для аутентификации и регистрации пользователей

Исходный код перенесён из:
- backend/server.py (строки 175-224)
- backend/auth.py (строка 99-146 - ensure_super_admin_exists)

Дата создания: 2025-10-09
"""

from fastapi import HTTPException, Request
from datetime import datetime
from typing import Optional

from database.repositories.user_repository import UserRepository
from models.user import User, UserCreate, TokenResponse, LoginRequest, create_user_response
from core.security import get_password_hash, verify_password, create_access_token
from core.config import settings


class AuthService:
    """
    Сервис для аутентификации пользователей

    Обрабатывает регистрацию, вход, и создание суперадминистратора
    """

    def __init__(self, user_repo: UserRepository):
        """
        Инициализация AuthService

        Args:
            user_repo: UserRepository instance
        """
        self.user_repo = user_repo

    # ===========================================
    # Регистрация
    # ===========================================

    async def register_user(
        self,
        user_data: UserCreate,
        request: Optional[Request] = None
    ) -> TokenResponse:
        """
        Зарегистрировать нового пользователя

        Источник: backend/server.py строки 176-205

        Args:
            user_data: Данные для регистрации
            request: FastAPI Request (для определения города по IP)

        Returns:
            TokenResponse с access_token и данными пользователя

        Raises:
            HTTPException: 400 если пользователь уже существует
        """
        # Проверяем существование пользователя
        existing = await self.user_repo.find_by_email(user_data.email)
        if existing:
            raise HTTPException(
                status_code=400,
                detail='User already exists'
            )

        # Определяем город
        city = user_data.city or "Москва"

        # TODO: Определение города по IP (требует дополнительной логики)
        # if request:
        #     city = await self._detect_city_from_ip(request)

        # Создаём пользователя
        user = User(
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            birth_date=user_data.birth_date,
            city=city,
            phone_number=user_data.phone_number,
            credits_remaining=1  # Стартовый балл для нового пользователя
        )

        # Сохраняем в БД
        await self.user_repo.create_user(user.dict())

        # Создаём JWT токен
        token = create_access_token({'sub': user.id})

        return TokenResponse(
            access_token=token,
            user=create_user_response(user)
        )

    # ===========================================
    # Вход
    # ===========================================

    async def login(self, login_data: LoginRequest) -> TokenResponse:
        """
        Войти в систему

        Источник: backend/server.py строки 208-224

        Args:
            login_data: Email и пароль

        Returns:
            TokenResponse с access_token и данными пользователя

        Raises:
            HTTPException: 401 если неверные credentials
        """
        # Ищем пользователя
        user_dict = await self.user_repo.find_by_email(login_data.email)
        if not user_dict:
            raise HTTPException(
                status_code=401,
                detail='Invalid credentials'
            )

        user = User(**user_dict)

        # Проверяем пароль
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=401,
                detail='Invalid credentials'
            )

        # Проверяем не истекла ли подписка
        await self._check_subscription_expiry(user)

        # Обновляем время последнего входа
        await self.user_repo.update_last_login(user.email)

        # Создаём JWT токен
        token = create_access_token({'sub': user.id})

        return TokenResponse(
            access_token=token,
            user=create_user_response(user)
        )

    # ===========================================
    # Получение информации о пользователе
    # ===========================================

    async def get_current_user_info(self, user_id: str) -> User:
        """
        Получить полную информацию о пользователе

        Args:
            user_id: ID пользователя из JWT

        Returns:
            User модель

        Raises:
            HTTPException: 404 если пользователь не найден
        """
        user_dict = await self.user_repo.find_by_id(user_id)
        if not user_dict:
            raise HTTPException(
                status_code=404,
                detail='User not found'
            )

        user = User(**user_dict)

        # Проверяем подписку
        await self._check_subscription_expiry(user)

        return user

    # ===========================================
    # Создание суперадминистратора
    # ===========================================

    async def ensure_super_admin_exists(self) -> None:
        """
        Создать суперадминистратора при первом запуске

        Источник: backend/auth.py строки 99-146

        Проверяет существование суперадмина из настроек.
        Если не существует - создаёт, если существует - обновляет пароль.
        """
        SUPER_ADMIN_EMAIL = settings.SUPER_ADMIN_EMAIL
        SUPER_ADMIN_PASSWORD = settings.SUPER_ADMIN_PASSWORD

        # Проверяем существование
        existing_admin = await self.user_repo.find_by_email(SUPER_ADMIN_EMAIL)

        if not existing_admin:
            # Создаём суперадминистратора
            super_admin = User(
                email=SUPER_ADMIN_EMAIL,
                password_hash=get_password_hash(SUPER_ADMIN_PASSWORD),
                full_name="Дмитрий Малахов (Суперадминистратор)",
                birth_date="01.01.1980",
                city="Москва",
                is_premium=True,
                is_super_admin=True,
                credits_remaining=1000000  # Безлимитные кредиты
            )

            await self.user_repo.create_user(super_admin.dict())
            print(f"✅ Создан суперадминистратор: {SUPER_ADMIN_EMAIL}")

        else:
            # Обновляем существующего до суперадмина
            await self.user_repo.update_user(
                existing_admin['id'],
                {
                    'is_super_admin': True,
                    'is_premium': True,
                    'credits_remaining': 1000000,
                    'password_hash': get_password_hash(SUPER_ADMIN_PASSWORD),
                }
            )

            # TODO: Создать запись в admin_users коллекции
            # Это будет реализовано в AdminService

            print(f"✅ Обновлён статус суперадминистратора: {SUPER_ADMIN_EMAIL}")

    # ===========================================
    # Вспомогательные методы
    # ===========================================

    async def _check_subscription_expiry(self, user: User) -> None:
        """
        Проверить и обнулить подписку если истекла

        Источник: backend/server.py строки 216-222

        Args:
            user: User модель (будет изменена in-place)
        """
        if user.subscription_expires_at and user.subscription_expires_at < datetime.utcnow():
            # Обнуляем подписку в БД
            await self.user_repo.update_subscription(
                user.id,
                {
                    'is_premium': False,
                    'subscription_type': None,
                    'subscription_expires_at': None
                }
            )

            # Обновляем локальную модель
            user.is_premium = False
            user.subscription_type = None
            user.subscription_expires_at = None

    async def _detect_city_from_ip(self, request: Request) -> str:
        """
        Определить город по IP адресу

        Источник: backend/server.py строки 182-192

        TODO: Реализовать определение города
        Требует:
        - geopy или другая библиотека для геолокации
        - Обработку прокси (X-Forwarded-For)

        Args:
            request: FastAPI Request

        Returns:
            Название города
        """
        # client_ip = request.client.host
        # forwarded_for = request.headers.get('X-Forwarded-For')
        # if forwarded_for:
        #     client_ip = forwarded_for.split(',')[0].strip()
        #
        # detected_city = get_city_from_ip(client_ip)
        # return detected_city or "Москва"

        return "Москва"  # Временная заглушка


__all__ = ['AuthService']
