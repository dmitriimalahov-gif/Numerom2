"""
Consultation Models

Модели для персональных консультаций

Исходный код перенесён из:
- backend/models.py строки 122-152 (PersonalConsultation, SubtitleFile, ConsultationPurchase)

Дата создания: 2025-10-09
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


# ===========================================
# Consultation Models
# ===========================================

class PersonalConsultation(BaseModel):
    """
    Персональная консультация

    Источник: backend/models.py строки 123-135
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    video_url: Optional[str] = None  # YouTube or external video URL
    video_file_id: Optional[str] = None  # ID загруженного видео файла
    pdf_file_id: Optional[str] = None  # ID загруженного PDF файла
    subtitles_file_id: Optional[str] = None  # ID файла субтитров (.vtt, .srt)
    assigned_user_id: str  # User ID this consultation is assigned to
    cost_credits: int = 6667  # Cost in credits (updated from 10000)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SubtitleFile(BaseModel):
    """
    Файл субтитров для консультации

    Источник: backend/models.py строки 138-145
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    consultation_id: str
    language: str = 'ru'  # ru, en, etc.
    file_path: str
    original_filename: str
    content_type: str  # text/vtt, application/x-subrip
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConsultationPurchase(BaseModel):
    """
    Покупка консультации пользователем

    Источник: backend/models.py строки 147-152
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    consultation_id: str
    purchased_at: datetime = Field(default_factory=datetime.utcnow)
    credits_spent: int


__all__ = [
    'PersonalConsultation',
    'SubtitleFile',
    'ConsultationPurchase',
]
