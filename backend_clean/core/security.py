"""
Модуль безопасности и аутентификации

Исходный код перенесён из:
- backend/auth.py (строки 1-158)

Дата переноса: 2025-10-09
"""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from .config import settings


# ===========================================
# Password hashing context
# Источник: backend/auth.py строки 15-16
# ===========================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


# ===========================================
# Password функции
# Источник: backend/auth.py строки 18-22
# ===========================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверить пароль против хэша

    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хэш пароля из БД

    Returns:
        True если пароль совпадает, False иначе
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Захэшировать пароль

    Args:
        password: Пароль в открытом виде

    Returns:
        Хэш пароля (bcrypt)
    """
    return pwd_context.hash(password)


# ===========================================
# JWT Token функции
# Источник: backend/auth.py строки 24-32
# ===========================================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Создать JWT access token

    Args:
        data: Данные для кодирования в токен (обычно {"sub": user_id})
        expires_delta: Время жизни токена (опционально)

    Returns:
        JWT токен (строка)
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Используем настройку из config
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Декодировать JWT токен

    Args:
        token: JWT токен

    Returns:
        Payload токена или None если токен невалиден
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


# ===========================================
# FastAPI Dependencies для аутентификации
# Источник: backend/auth.py строки 34-76
# ===========================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, str]:
    """
    Dependency для получения текущего пользователя из JWT токена

    Args:
        credentials: HTTP Bearer токен

    Returns:
        Dict с user_id: {"user_id": "uuid"}

    Raises:
        HTTPException: 401 если токен невалиден
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Return user_id for further processing
    return {"user_id": user_id}


async def get_current_user_id(
    current_user: Dict[str, str] = Depends(get_current_user)
) -> str:
    """
    Dependency для получения только ID пользователя

    Args:
        current_user: Результат get_current_user

    Returns:
        user_id (строка)
    """
    return current_user["user_id"]


# ===========================================
# Проверка прав доступа
# Источник: backend/auth.py строки 148-158
# ===========================================

async def require_super_admin(
    current_user: Dict[str, str] = Depends(get_current_user),
    db = None  # Будет инжектиться через Depends(get_db)
) -> Dict[str, Any]:
    """
    Dependency для проверки прав суперадминистратора

    ПРИМЕЧАНИЕ: Эта функция требует доступа к БД.
    В новой архитектуре она будет перенесена в api/deps.py
    и использовать UserRepository вместо прямого доступа к db.

    Args:
        current_user: Текущий пользователь из JWT
        db: Database instance

    Returns:
        User данные

    Raises:
        HTTPException: 403 если не суперадминистратор
        HTTPException: 404 если пользователь не найден
    """
    if db is None:
        raise HTTPException(
            status_code=500,
            detail="Database dependency not provided"
        )

    user_data = await db.users.find_one({"id": current_user["user_id"]})

    if not user_data:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if not user_data.get("is_super_admin", False):
        raise HTTPException(
            status_code=403,
            detail="Доступ запрещен. Требуются права суперадминистратора."
        )

    return user_data


async def require_admin(
    current_user: Dict[str, str] = Depends(get_current_user),
    db = None
) -> Dict[str, Any]:
    """
    Dependency для проверки прав администратора (обычного или супер)

    Args:
        current_user: Текущий пользователь из JWT
        db: Database instance

    Returns:
        User данные

    Raises:
        HTTPException: 403 если не администратор
        HTTPException: 404 если пользователь не найден
    """
    if db is None:
        raise HTTPException(
            status_code=500,
            detail="Database dependency not provided"
        )

    user_data = await db.users.find_one({"id": current_user["user_id"]})

    if not user_data:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    is_admin = user_data.get("is_admin", False)
    is_super_admin = user_data.get("is_super_admin", False)

    if not (is_admin or is_super_admin):
        raise HTTPException(
            status_code=403,
            detail="Доступ запрещен. Требуются права администратора."
        )

    return user_data


# ===========================================
# Утилиты для работы с пользователями
# (Будут перенесены в services/auth_service.py)
# ===========================================

# NOTE: create_user_response перенесена в models/user.py
# NOTE: ensure_super_admin_exists будет перенесена в services/admin_service.py


# ===========================================
# Экспорт
# ===========================================

__all__ = [
    # Password
    'verify_password',
    'get_password_hash',

    # JWT
    'create_access_token',
    'decode_access_token',

    # Dependencies
    'get_current_user',
    'get_current_user_id',
    'require_super_admin',
    'require_admin',

    # FastAPI Security
    'security',
]
