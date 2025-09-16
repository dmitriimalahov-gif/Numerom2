from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# User Models
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    birth_date: str  # DD.MM.YYYY format
    city: Optional[str] = "Москва"  # Город по умолчанию
    phone_number: Optional[str] = None  # Номер телефона с кодом страны

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None  # +37369183398 format
    city: Optional[str] = None
    car_number: Optional[str] = None  # До 13 символов, любая раскладка
    street: Optional[str] = None
    house_number: Optional[str] = None
    apartment_number: Optional[str] = None
    postal_code: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    birth_date: str
    city: str = "Москва"
    phone_number: Optional[str] = None
    car_number: Optional[str] = None
    street: Optional[str] = None
    house_number: Optional[str] = None
    apartment_number: Optional[str] = None
    postal_code: Optional[str] = None
    is_premium: bool = False
    is_super_admin: bool = False  # Суперадминистратор
    is_admin: bool = False  # Обычный администратор
    subscription_type: Optional[str] = None
    credits_remaining: int = 0
    created_at: datetime

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    password_hash: str
    full_name: str
    birth_date: str  # DD.MM.YYYY format
    city: str = "Москва"  # Город пользователя для временных расчетов
    phone_number: Optional[str] = None  # Номер телефона с кодом страны (+37369183398)
    car_number: Optional[str] = None  # Номер автомобиля (до 13 символов)
    street: Optional[str] = None  # Улица проживания
    house_number: Optional[str] = None  # Номер дома
    apartment_number: Optional[str] = None  # Номер квартиры
    postal_code: Optional[str] = None  # Почтовый индекс
    is_premium: bool = False
    is_super_admin: bool = False  # Суперадминистратор
    is_admin: bool = False  # Обычный администратор
    subscription_type: Optional[str] = None  # "monthly", "annual", None
    subscription_expires_at: Optional[datetime] = None
    credits_remaining: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Payment Models
class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    package_type: str  # "one_time", "monthly", "annual"
    amount: float
    currency: str = "eur"
    session_id: str
    payment_status: str = "pending"  # pending, paid, failed, expired
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PaymentRequest(BaseModel):
    package_type: str  # "one_time", "monthly", "annual"
    origin_url: str

# Numerology request models
class CompatibilityRequest(BaseModel):
    person1_birth_date: str  # DD.MM.YYYY
    person2_birth_date: str  # DD.MM.YYYY
    person1_name: Optional[str] = "Человек 1"
    person2_name: Optional[str] = "Человек 2"

class GroupCompatibilityPerson(BaseModel):
    name: str
    birth_date: str  # DD.MM.YYYY

class GroupCompatibilityRequest(BaseModel):
    main_person_birth_date: str  # DD.MM.YYYY основного пользователя
    main_person_name: str = "Вы"
    people: List[GroupCompatibilityPerson]  # До 5 человек

class FreeCalculationRequest(BaseModel):
    birth_date: str

# Numerology Models
class PersonalNumbersResponse(BaseModel):
    soul_number: int  # ЧД - число души
    mind_number: int  # ЧУ - число ума
    destiny_number: int  # ЧС - число судьбы
    helping_mind_number: int  # ЧУ* - помогающее число ума
    wisdom_number: int  # ЧМ - число мудрости  
    ruling_number: int  # ПЧ - правящее число
    planetary_strength: Dict[str, int]  # Сила планет
    birth_weekday: str  # День недели рождения
class NumerologyCalculation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    birth_date: str
    calculation_type: str  # "personal_numbers", "pythagorean_square", "compatibility", etc.
    results: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PersonalNumbersResult(BaseModel):
    life_path: int
    destiny: int
    soul: int
    ruling_number: int
    problem_number: int
    life_path_code: str
    planetary_strength: Dict[str, int]
    individual_year: int
    individual_month: int
    individual_day: int

class PythagoreanSquareResult(BaseModel):
    square: List[List[str]]
    horizontal_sums: List[int]
    vertical_sums: List[int]
    diagonal_sums: List[int]
    additional_numbers: List[int]
    planet_positions: Dict[str, List[int]]

class QuizResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    quiz_type: str
    answers: List[Dict[str, Any]]
    score: int
    recommendations: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Learning Management System Models
class VideoLesson(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    video_url: Optional[str] = None  # YouTube or external video URL
    video_file_id: Optional[str] = None  # ID загруженного видео файла (как в консультациях)
    pdf_file_id: Optional[str] = None  # ID загруженного PDF файла (как в консультациях)
    subtitles_file_id: Optional[str] = None  # ID файла субтитров (как в консультациях)
    duration_minutes: Optional[int] = None  
    level: int = 1  # 1-10 levels
    order: int = 1  # order within level
    prerequisites: List[str] = []  # lesson IDs required before this one
    points_for_lesson: int = 0  # Points required to access this lesson (0 = free)
    quiz_questions: List[Dict[str, Any]] = []  # Автоматически сгенерированные вопросы Quiz
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class UserProgress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    lesson_id: str
    completed: bool = False
    completion_date: Optional[datetime] = None
    watch_time_minutes: int = 0
    quiz_score: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserLevel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    current_level: int = 1
    experience_points: int = 0
    lessons_completed: int = 0
    last_activity: datetime = Field(default_factory=datetime.utcnow)

# Personal Consultation Models
class PersonalConsultation(BaseModel):
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

# Subtitle Model
class SubtitleFile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    consultation_id: str
    language: str = 'ru'  # ru, en, etc.
    file_path: str
    original_filename: str
    content_type: str  # text/vtt, application/x-subrip
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ConsultationPurchase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    consultation_id: str
    purchased_at: datetime = Field(default_factory=datetime.utcnow)
    credits_spent: int

# Credit Transaction History
class CreditTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    transaction_type: str  # 'debit' или 'credit'
    amount: int  # количество баллов (положительное для пополнения, отрицательное для списания)
    description: str  # описание за что списано/начислено
    category: str  # категория: 'numerology', 'vedic', 'learning', 'quiz', 'materials', 'purchase', etc.
    details: Optional[dict] = None  # дополнительные детали транзакции
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Credit costs configuration
CREDIT_COSTS = {
    'name_numerology': 1,           # Нумерология имени
    'personal_numbers': 1,          # Персональные числа
    'pythagorean_square': 1,        # Квадрат Пифагора
    'vedic_daily': 1,              # Ведическое время на день
    'planetary_daily': 1,           # Планетарный маршрут на день
    'planetary_monthly': 5,         # Планетарный маршрут на месяц
    'planetary_quarterly': 10,      # Планетарный маршрут на квартал
    'compatibility_pair': 1,        # Совместимость пары
    'group_compatibility': 5,       # Групповая совместимость (5 человек)
    'personality_test': 1,          # Тест личности
    'lesson_viewing': 10,           # Просмотр урока
    'quiz_completion': 1,           # Прохождение Quiz
    'material_viewing': 1,          # Просмотр материалов
}

# Enhanced Quiz Models
class QuizQuestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    options: List[Dict[str, Any]]
    category: str  # "personality", "numerology", "vedic", etc.
    difficulty: int = 1  # 1-5
    is_active: bool = True

class RandomizedQuiz(BaseModel):
    questions: List[QuizQuestion]
    session_id: str
    user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Chart/Graph Data Models
class PlanetaryEnergyData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    date: datetime
    surya: int  # Sun
    chandra: int  # Moon  
    mangal: int  # Mars
    budha: int  # Mercury
    guru: int  # Jupiter
    shukra: int  # Venus
    shani: int  # Saturn
    rahu: int  # Rahu
    ketu: int  # Ketu
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WeeklyEnergyForecast(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    week_start: datetime
    daily_energies: List[Dict[str, Any]]  # 7 days of energy data
    dominant_planet: str
    recommendations: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Admin Models
class AdminUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    role: str = "admin"  # admin, super_admin
    permissions: List[str] = ["video_management", "user_management", "content_management"]
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Enhanced Vedic Numerology Results
class VedicNumerologyResult(BaseModel):
    # Core numbers with Vedic terminology
    janma_ank: int  # Life Path (Birth Number)
    nama_ank: int   # Name Number
    bhagya_ank: int # Destiny Number
    atma_ank: int   # Soul Number
    shakti_ank: int # Power Number
    
    # Planetary influences (Vedic names)
    graha_shakti: Dict[str, int]  # Planetary strength
    
    # Vedic periods
    mahadasha: str  # Major period
    antardasha: str # Minor period
    
    # Yantra (Square) analysis
    yantra_matrix: List[List[str]]
    yantra_sums: Dict[str, List[int]]
    
    # Recommendations in Sanskrit/Vedic context
    upayas: List[str]  # Remedies
    mantras: List[str] # Chants
    gemstones: List[str] # Ratnas
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Status Check Models (for legacy endpoints)
class StatusCheckCreate(BaseModel):
    status: str
    message: Optional[str] = None

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str
    message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# New Models for Enhanced Features

# Vedic Time Calculations
class VedicTimeRequest(BaseModel):
    city: str
    date: Optional[str] = None  # YYYY-MM-DD format, если не указана - сегодня

class CityChangeRequest(BaseModel):
    city: str

class PDFReportRequest(BaseModel):
    include_vedic: bool = True
    include_charts: bool = True
    include_compatibility: bool = False
    partner_birth_date: Optional[str] = None

# Enhanced Pythagorean Square
class EnhancedPythagoreanSquare(BaseModel):
    # Полная матрица с планетарными энергиями
    square: List[List[str]]  # 3x3 matrix with numbers
    planet_positions: Dict[str, Dict[str, Any]]  # планета -> {цифры, сила, описание}
    
    # Все виды чисел
    life_path: int      # Число жизненного пути  
    destiny: int        # Число судьбы
    soul: int          # Число души
    mind: int          # Число ума (ЧУ)
    personality: int   # Число личности (ЧМ)
    power: int         # Число силы (ПЧ)
    
    # Энергетический анализ
    energy_totals: Dict[str, int]  # общее количество каждой цифры
    energy_strength: Dict[str, str]  # сила каждой планеты (слабая/средняя/сильная)
    
    # Линии и суммы
    horizontal_sums: List[int]  # материальная сфера
    vertical_sums: List[int]    # духовная сфера  
    diagonal_sums: List[int]    # баланс
    
    # Рекомендации для каждой планеты
    recommendations: Dict[str, List[str]]

# Planetary Daily Schedule  
class PlanetaryDaySchedule(BaseModel):
    date: str
    city: str
    timezone: str
    
    # Временные периоды
    sunrise: str
    sunset: str
    rahu_kaal: Dict[str, str]      # start, end, duration
    gulika_kaal: Dict[str, str]    # start, end, duration  
    yamaghanta: Dict[str, str]     # start, end, duration
    abhijit_muhurta: Dict[str, str]  # start, end, duration
    
    # Планетарные часы дня (12 часов)
    planetary_hours: List[Dict[str, Any]]
    
    # Персональные рекомендации
    daily_recommendations: Dict[str, Any]
    ruling_planet: str
    favorable_hours: List[str]

# Quiz After Lessons
class LessonQuiz(BaseModel):
    lesson_id: str
    questions: List[QuizQuestion]
    passing_score: int = 70

class LessonContent(BaseModel):
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

# Subscription Credits Update
class SubscriptionCredits(BaseModel):
    one_time: int = 1      # Разовый платеж - 1 расчет  
    monthly: int = 50      # Месячная подписка - 50 расчетов
    annual: int = 1000     # Годовая подписка - безлимитно (1000 = практически безлимит)

# Learning Materials and Admin Models
class MaterialUpload(BaseModel):
    lesson_id: str
    title: str
    description: str
    material_type: str  # "pdf", "video", "text"
    file_name: Optional[str] = None
    file_data: Optional[str] = None  # base64 encoded для PDF

class LessonMaterialResponse(BaseModel):
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

class EnhancedLessonContent(BaseModel):
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

class SuperAdminAction(BaseModel):
    action_type: str  # "create_lesson", "upload_material", "create_quiz"
    target_id: str
    details: Dict[str, Any]
    performed_by: str  # email суперадминистратора
    performed_at: datetime = Field(default_factory=datetime.utcnow)

# HTML Export Models
class HTMLReportRequest(BaseModel):
    # Новая система выбора расчётов
    selected_calculations: List[str] = []  # IDs расчётов для включения
    
    # Устаревшие поля (для совместимости)
    include_vedic: bool = True
    include_charts: bool = True
    include_compatibility: bool = False
    partner_birth_date: Optional[str] = None
    theme: str = "default"  # "default", "dark", "print"