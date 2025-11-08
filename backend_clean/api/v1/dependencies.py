"""
API Dependencies

Dependency injection для FastAPI роутеров

Источник:
- backend/auth.py строки 19-40 (get_current_user)
- backend/server.py строки 107-112 (database setup)

Дата создания: 2025-10-09
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from jose import JWTError

from core.security import decode_access_token
from database.connection import get_database
from database.repositories.user_repository import UserRepository
from database.repositories.credit_repository import CreditRepository
from database.repositories.payment_repository import PaymentRepository
from services.auth_service import AuthService
from services.credit_service import CreditService
from services.payment_service import PaymentService
from models.user import User


# ===========================================
# Security
# ===========================================

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Получить текущего авторизованного пользователя

    Источник: backend/auth.py строки 19-40

    Args:
        credentials: JWT токен из HTTP Bearer header

    Returns:
        User модель

    Raises:
        HTTPException: 401 если токен невалиден или пользователь не найден
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Получаем пользователя из БД
    db = await get_database()
    user_repo = UserRepository(db)
    user_dict = await user_repo.find_by_id(user_id)

    if user_dict is None:
        raise credentials_exception

    return User(**user_dict)


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Проверить что пользователь является администратором

    Источник: backend/auth.py строки 43-53

    Args:
        current_user: Текущий пользователь

    Returns:
        User модель

    Raises:
        HTTPException: 403 если пользователь не админ
    """
    if not current_user.is_admin and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_current_super_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Проверить что пользователь является суперадминистратором

    Источник: backend/auth.py строки 56-66

    Args:
        current_user: Текущий пользователь

    Returns:
        User модель

    Raises:
        HTTPException: 403 если пользователь не суперадмин
    """
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user


# ===========================================
# Repository Dependencies
# ===========================================

async def get_user_repository() -> UserRepository:
    """
    Получить UserRepository instance

    Returns:
        UserRepository
    """
    db = await get_database()
    return UserRepository(db)


async def get_credit_repository() -> CreditRepository:
    """
    Получить CreditRepository instance

    Returns:
        CreditRepository
    """
    db = await get_database()
    return CreditRepository(db)


async def get_payment_repository() -> PaymentRepository:
    """
    Получить PaymentRepository instance

    Returns:
        PaymentRepository
    """
    db = await get_database()
    return PaymentRepository(db)


# ===========================================
# Service Dependencies
# ===========================================

async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> AuthService:
    """
    Получить AuthService instance

    Args:
        user_repo: UserRepository (dependency injection)

    Returns:
        AuthService
    """
    return AuthService(user_repo)


async def get_credit_service(
    user_repo: UserRepository = Depends(get_user_repository),
    credit_repo: CreditRepository = Depends(get_credit_repository)
) -> CreditService:
    """
    Получить CreditService instance

    Args:
        user_repo: UserRepository (dependency injection)
        credit_repo: CreditRepository (dependency injection)

    Returns:
        CreditService
    """
    return CreditService(user_repo, credit_repo)


async def get_payment_service(
    user_repo: UserRepository = Depends(get_user_repository),
    payment_repo: PaymentRepository = Depends(get_payment_repository)
) -> PaymentService:
    """
    Получить PaymentService instance

    Args:
        user_repo: UserRepository (dependency injection)
        payment_repo: PaymentRepository (dependency injection)

    Returns:
        PaymentService
    """
    return PaymentService(user_repo, payment_repo)


__all__ = [
    'get_current_user',
    'get_current_admin_user',
    'get_current_super_admin',
    'get_user_repository',
    'get_credit_repository',
    'get_payment_repository',
    'get_auth_service',
    'get_credit_service',
    'get_payment_service',
]
