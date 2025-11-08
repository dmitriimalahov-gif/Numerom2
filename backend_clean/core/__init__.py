"""
Core модуль приложения

Содержит базовую функциональность:
- config.py: Конфигурация и настройки
- security.py: Аутентификация и безопасность
- exceptions.py: Кастомные исключения
"""

from .config import settings, PAYMENT_PACKAGES, SUBSCRIPTION_CREDITS
from .security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    get_current_user,
    get_current_user_id,
    require_super_admin,
    require_admin,
    security,
)

__all__ = [
    # Config
    'settings',
    'PAYMENT_PACKAGES',
    'SUBSCRIPTION_CREDITS',

    # Security - Password
    'verify_password',
    'get_password_hash',

    # Security - JWT
    'create_access_token',
    'decode_access_token',

    # Security - Dependencies
    'get_current_user',
    'get_current_user_id',
    'require_super_admin',
    'require_admin',
    'security',
]
