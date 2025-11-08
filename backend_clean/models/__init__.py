"""
Models module

Pydantic models for all application domains

Source code transferred from:
- backend/models.py (512 lines split into 9 files)

Date created: 2025-10-09
"""

# User models
from .user import (
    UserCreate,
    UserProfileUpdate,
    UserResponse,
    User,
    LoginRequest,
    TokenResponse,
    create_user_response,
)

# Credit models
from .credit import (
    CreditTransaction,
    CREDIT_COSTS,
)

# Payment models
from .payment import (
    PaymentTransaction,
    PaymentRequest,
)

# Numerology models
from .numerology import (
    FreeCalculationRequest,
    CompatibilityRequest,
    GroupCompatibilityPerson,
    GroupCompatibilityRequest,
    PersonalNumbersResponse,
    PersonalNumbersResult,
    PythagoreanSquareResult,
    EnhancedPythagoreanSquare,
    VedicNumerologyResult,
    NumerologyCalculation,
    PlanetaryEnergyData,
    WeeklyEnergyForecast,
    VedicTimeRequest,
    PlanetaryDaySchedule,
)

# Lesson models
from .lesson import (
    VideoLesson,
    UserProgress,
    UserLevel,
    QuizQuestion,
    LessonQuiz,
    QuizResult,
    RandomizedQuiz,
    LessonContent,
    EnhancedLessonContent,
    MaterialUpload,
    LessonMaterialResponse,
)

# Consultation models
from .consultation import (
    PersonalConsultation,
    SubtitleFile,
    ConsultationPurchase,
)

# Admin models
from .admin import (
    AdminUser,
    SuperAdminAction,
    StatusCheckCreate,
    StatusCheck,
)

__all__ = [
    # User
    'UserCreate',
    'UserProfileUpdate',
    'UserResponse',
    'User',
    'LoginRequest',
    'TokenResponse',
    'create_user_response',

    # Credit
    'CreditTransaction',
    'CREDIT_COSTS',

    # Payment
    'PaymentTransaction',
    'PaymentRequest',

    # Numerology
    'FreeCalculationRequest',
    'CompatibilityRequest',
    'GroupCompatibilityPerson',
    'GroupCompatibilityRequest',
    'PersonalNumbersResponse',
    'PersonalNumbersResult',
    'PythagoreanSquareResult',
    'EnhancedPythagoreanSquare',
    'VedicNumerologyResult',
    'NumerologyCalculation',
    'PlanetaryEnergyData',
    'WeeklyEnergyForecast',
    'VedicTimeRequest',
    'PlanetaryDaySchedule',

    # Lesson
    'VideoLesson',
    'UserProgress',
    'UserLevel',
    'QuizQuestion',
    'LessonQuiz',
    'QuizResult',
    'RandomizedQuiz',
    'LessonContent',
    'EnhancedLessonContent',
    'MaterialUpload',
    'LessonMaterialResponse',

    # Consultation
    'PersonalConsultation',
    'SubtitleFile',
    'ConsultationPurchase',

    # Admin
    'AdminUser',
    'SuperAdminAction',
    'StatusCheckCreate',
    'StatusCheck',
]
