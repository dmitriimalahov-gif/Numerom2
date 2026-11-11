from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
from models import User, UserResponse

# Security configuration
# Поддерживаем оба варианта для совместимости
def signing_key():
    key = os.environ.get("SECRET_KEY") or os.environ.get("JWT_SECRET_KEY") or ""
    if len(key) < 32 or key in {"your-secret-key-change-in-production", "your-super-secret-jwt-key-change-this-in-production"}:
        raise HTTPException(status_code=503, detail="Вход временно недоступен: требуется настройка сервера")
    return key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 часа

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)  # Отключаем автоматическую ошибку для более гибкой обработки

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # Используем настройку из константы
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, signing_key(), algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    failure = HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate":"Bearer"})
    if not credentials or not credentials.credentials: raise failure
    key = signing_key()
    try:
        payload = jwt.decode(credentials.credentials, key, algorithms=[ALGORITHM])
    except JWTError:
        raise failure
    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id: raise failure
    db = getattr(request.app.state, 'auth_db', None)
    if db is None: raise HTTPException(503, "Account service unavailable")
    user = await db.users.find_one({'id':user_id})
    if not user or user.get('is_disabled') or payload.get('auth_version',0) != user.get('auth_version',0):
        raise failure
    role = 'admin' if user.get('is_admin') or user.get('is_super_admin') else 'user'
    return {'user_id':user_id,'role':role}


async def get_current_user_full(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security), db=None):
    current = await get_current_user(request, credentials)
    repository = db if db is not None else request.app.state.auth_db
    document = await repository.users.find_one({'id':current['user_id']})
    return User(**document)


def create_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        name=user.name,
        surname=user.surname,
        birth_date=user.birth_date,
        city=user.city,
        birth_city=user.birth_city,
        birth_city_id=user.birth_city_id,
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
        level=user.level,
        created_at=user.created_at
    )

async def ensure_super_admin_exists(db):
    """Opt-in initial bootstrap only. Never overwrite a person's existing password."""
    email = os.environ.get('SUPER_ADMIN_EMAIL','').strip()
    password = os.environ.get('SUPER_ADMIN_PASSWORD','')
    if not email or not password: return
    # Existing accounts are never promoted or reset implicitly on process restart.
    if await db.users.find_one({'email':email}): return
    if len(password) < 12 or len(password.encode('utf-8')) > 72 or password == 'change-this-secure-password':
        raise RuntimeError('Configure a strong initial administrator password')
    user = User(email=email,password_hash=get_password_hash(password),full_name='Администратор NumerOM',
                birth_date='01.01.1980',is_super_admin=True,is_admin=True)
    await db.users.update_one({'email':email}, {'$setOnInsert':user.model_dump()}, upsert=True)


def require_super_admin(current_user: dict, db):
    """Декоратор для проверки прав суперадминистратора"""
    async def check_super_admin():
        user_data = await db.users.find_one({"id": current_user["user_id"]})
        if not user_data or not user_data.get("is_super_admin", False):
            raise HTTPException(
                status_code=403, 
                detail="Доступ запрещен. Требуются права суперадминистратора."
            )
        return User(**user_data)
    return check_super_admin
