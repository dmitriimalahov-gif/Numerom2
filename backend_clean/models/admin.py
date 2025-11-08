"""
Admin Models

Модели для административных операций

Исходный код перенесён из:
- backend/models.py строки 222-228 (AdminUser)
- backend/models.py строки 421-426 (SuperAdminAction)
- backend/models.py строки 257-266 (StatusCheck)

Дата создания: 2025-10-09
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


# ===========================================
# Admin User Models
# ===========================================

class AdminUser(BaseModel):
    """
    Пользователь-администратор

    Источник: backend/models.py строки 223-228
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    role: str = "admin"  # admin, super_admin
    permissions: List[str] = ["video_management", "user_management", "content_management"]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SuperAdminAction(BaseModel):
    """
    Логирование действий суперадминистратора

    Источник: backend/models.py строки 421-426
    """
    action_type: str  # "create_lesson", "upload_material", "create_quiz"
    target_id: str
    details: Dict[str, Any]
    performed_by: str  # email суперадминистратора
    performed_at: datetime = Field(default_factory=datetime.utcnow)


# ===========================================
# Status Check Models
# ===========================================

class StatusCheckCreate(BaseModel):
    """
    Создание статусной проверки

    Источник: backend/models.py строки 258-260
    """
    status: str
    message: Optional[str] = None


class StatusCheck(BaseModel):
    """
    Статусная проверка системы

    Источник: backend/models.py строки 262-266
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str
    message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


__all__ = [
    'AdminUser',
    'SuperAdminAction',
    'StatusCheckCreate',
    'StatusCheck',
]
