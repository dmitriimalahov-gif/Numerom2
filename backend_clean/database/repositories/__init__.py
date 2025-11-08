"""
Repository module

Implementation of Repository pattern for MongoDB collections.

Contains:
- base.py: Base repository with all CRUD operations
- user_repository.py: Repository for users collection
- credit_repository.py: Repository for credit_transactions
- payment_repository.py: Repository for payment_transactions
- numerology_repository.py: Repository for numerology_calculations
- lesson_repository.py: Repository for video_lessons, user_progress, user_level
- consultation_repository.py: Repository for personal_consultations
"""

from .base import BaseRepository
from .user_repository import UserRepository
from .credit_repository import CreditRepository
from .payment_repository import PaymentRepository
from .numerology_repository import NumerologyRepository
from .lesson_repository import LessonRepository
from .consultation_repository import ConsultationRepository

__all__ = [
    'BaseRepository',
    'UserRepository',
    'CreditRepository',
    'PaymentRepository',
    'NumerologyRepository',
    'LessonRepository',
    'ConsultationRepository',
]
