"""
Lesson Models

Модели для системы обучения (LMS)

Исходный код перенесён из:
- backend/models.py строки 86-121 (VideoLesson, UserProgress, UserLevel)
- backend/models.py строки 333-360 (LessonQuiz, LessonContent)
- backend/models.py строки 389-419 (EnhancedLessonContent)

Дата создания: 2025-10-09
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


# ===========================================
# Video Lesson Models
# ===========================================

class VideoLesson(BaseModel):
    """
    Модель видео урока

    Источник: backend/models.py строки 86-102
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    video_url: Optional[str] = None  # YouTube or external video URL
    video_file_id: Optional[str] = None  # ID загруженного видео файла
    pdf_file_id: Optional[str] = None  # ID загруженного PDF файла
    subtitles_file_id: Optional[str] = None  # ID файла субтитров
    duration_minutes: Optional[int] = None
    level: int = 1  # 1-10 levels
    order: int = 1  # order within level
    prerequisites: List[str] = []  # lesson IDs required before this one
    points_for_lesson: int = 0  # Points required to access this lesson (0 = free)
    quiz_questions: List[Dict[str, Any]] = []  # Автоматически сгенерированные вопросы Quiz
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ===========================================
# User Progress Models
# ===========================================

class UserProgress(BaseModel):
    """
    Прогресс пользователя по уроку

    Источник: backend/models.py строки 104-112
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    lesson_id: str
    completed: bool = False
    completion_date: Optional[datetime] = None
    watch_time_minutes: int = 0
    quiz_score: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserLevel(BaseModel):
    """
    Уровень пользователя в системе обучения

    Источник: backend/models.py строки 114-120
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    current_level: int = 1
    experience_points: int = 0
    lessons_completed: int = 0
    last_activity: datetime = Field(default_factory=datetime.utcnow)


# ===========================================
# Quiz Models
# ===========================================

class QuizQuestion(BaseModel):
    """
    Вопрос квиза

    Источник: backend/models.py строки 183-189
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    options: List[Dict[str, Any]]
    category: str  # "personality", "numerology", "vedic", etc.
    difficulty: int = 1  # 1-5
    is_active: bool = True


class LessonQuiz(BaseModel):
    """
    Квиз после урока

    Источник: backend/models.py строки 333-336
    """
    lesson_id: str
    questions: List[QuizQuestion]
    passing_score: int = 70


class QuizResult(BaseModel):
    """
    Результат прохождения квиза

    Источник: backend/models.py строки 150-153 (из старого models.py)
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    quiz_type: str
    answers: List[Dict[str, Any]]
    score: int
    recommendations: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RandomizedQuiz(BaseModel):
    """
    Рандомизированный квиз

    Источник: backend/models.py строки 191-195
    """
    questions: List[QuizQuestion]
    session_id: str
    user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ===========================================
# Enhanced Lesson Content
# ===========================================

class LessonContent(BaseModel):
    """
    Контент урока

    Источник: backend/models.py строки 338-360
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    module_name: str
    lesson_number: int
    title: str

    # Из методологии
    content_description: str
    learning_objectives: List[str]
    assignments: List[str]
    social_mechanics: List[str]
    additional_materials: List[str]
    expected_results: List[str]

    # Практическая информация
    duration_minutes: int = 45
    difficulty_level: int = 1  # 1-5
    prerequisites: List[str] = []

    # Связанный квиз
    quiz: Optional[LessonQuiz] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)


class EnhancedLessonContent(BaseModel):
    """
    Расширенный контент урока с материалами

    Источник: backend/models.py строки 389-419
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    module_name: str
    lesson_number: int
    title: str

    # Из методологии
    content_description: str
    learning_objectives: List[str]
    assignments: List[str]
    social_mechanics: List[str]
    additional_materials: List[str]
    expected_results: List[str]

    # Практическая информация
    duration_minutes: int = 45
    difficulty_level: int = 1  # 1-5
    prerequisites: List[str] = []

    # Связанные материалы
    materials: List[str] = []  # IDs материалов
    video_url: Optional[str] = None

    # Связанный квиз
    quiz: Optional[LessonQuiz] = None

    # Метаинформация
    is_active: bool = True
    created_by: str  # ID суперадминистратора
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ===========================================
# Learning Materials
# ===========================================

class MaterialUpload(BaseModel):
    """
    Загрузка учебного материала

    Источник: backend/models.py строки 369-375
    """
    lesson_id: str
    title: str
    description: str
    material_type: str  # "pdf", "video", "text"
    file_name: Optional[str] = None
    file_data: Optional[str] = None  # base64 encoded для PDF


class LessonMaterialResponse(BaseModel):
    """
    Ответ с информацией о материале

    Источник: backend/models.py строки 377-387
    """
    id: str
    lesson_id: str
    title: str
    description: str
    material_type: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_url: Optional[str] = None  # URL для доступа к файлу
    created_at: datetime
    uploaded_by: str  # ID суперадминистратора


__all__ = [
    # Video lessons
    'VideoLesson',

    # Progress tracking
    'UserProgress',
    'UserLevel',

    # Quiz models
    'QuizQuestion',
    'LessonQuiz',
    'QuizResult',
    'RandomizedQuiz',

    # Lesson content
    'LessonContent',
    'EnhancedLessonContent',

    # Materials
    'MaterialUpload',
    'LessonMaterialResponse',
]
