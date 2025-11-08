"""
API v1 Router

Combines all API routers for version 1

Date created: 2025-10-09
"""

from .auth import router as auth_router
from .credit import router as credit_router
from .payment import router as payment_router
from .numerology import router as numerology_router
from .lesson import router as lesson_router
from .consultation import router as consultation_router
from .user import router as user_router
from .admin import router as admin_router
from .charts import router as charts_router
from .vedic_time import router as vedic_time_router
from .quiz import router as quiz_router
from .learning import router as learning_router
from .reports import router as reports_router

__all__ = [
    'auth_router',
    'credit_router',
    'payment_router',
    'numerology_router',
    'lesson_router',
    'consultation_router',
    'user_router',
    'admin_router',
    'charts_router',
    'vedic_time_router',
    'quiz_router',
    'learning_router',
    'reports_router',
]
