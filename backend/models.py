from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# User Models
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    name: Optional[str] = None  # Имя
    surname: Optional[str] = None  # Фамилия
    birth_date: str  # DD.MM.YYYY format
    city: Optional[str] = "Москва"  # Город по умолчанию
    phone_number: Optional[str] = None  # Номер телефона с кодом страны

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    name: Optional[str] = None  # Имя
    surname: Optional[str] = None  # Фамилия
    phone_number: Optional[str] = None  # +37369183398 format
    city: Optional[str] = None
    car_number: Optional[str] = None  # До 13 символов, любая раскладка
    street: Optional[str] = None
    house_number: Optional[str] = None
    apartment_number: Optional[str] = None
    postal_code: Optional[str] = None
    birth_date: Optional[str] = None

    @field_validator('birth_date')
    @classmethod
    def validate_birth_date(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError('Дата рождения не может быть пустой')
        try:
            datetime.strptime(value, '%d.%m.%Y')
        except ValueError as exc:
            raise ValueError('Дата рождения должна быть в формате ДД.ММ.ГГГГ') from exc
        return value

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    name: Optional[str] = None  # Имя
    surname: Optional[str] = None  # Фамилия
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
    name: Optional[str] = None  # Имя
    surname: Optional[str] = None  # Фамилия
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

class PlanetaryAdviceResponse(BaseModel):
    planet_number: int
    score: int
    advice: str
    min_percent: Optional[int] = None
    max_percent: Optional[int] = None

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
    'planetary_weekly': 10,         # Планетарный маршрут на неделю
    'planetary_monthly': 30,        # Планетарный маршрут на месяц
    'planetary_quarterly': 100,     # Планетарный маршрут на квартал
    'planetary_energy_weekly': 10,  # Динамика энергии планет на неделю
    'planetary_energy_monthly': 30, # Динамика энергии планет на месяц
    'planetary_energy_quarterly': 100, # Динамика энергии планет на квартал
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
    city: Optional[str] = None
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

# ===== НОВАЯ СИСТЕМА ОБУЧЕНИЯ V2 =====

class TheoryBlock(BaseModel):
    """Блок теоретического материала"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    order: int = 0

class Exercise(BaseModel):
    """Интерактивное упражнение"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    type: str = "text"  # text, multiple_choice, calculation, reflection
    instructions: str
    expected_outcome: str
    options: Optional[List[str]] = None  # Для multiple_choice
    correct_answer: Optional[str] = None  # Для проверки
    order: int = 0

class ChallengeDay(BaseModel):
    """День челленджа"""
    day: int
    title: str
    description: str
    tasks: List[str]
    completed: bool = False

class Challenge(BaseModel):
    """Челлендж на несколько дней"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    duration_days: int
    daily_tasks: List[ChallengeDay] = []
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class QuizQuestion(BaseModel):
    """Вопрос теста"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    type: str = "multiple_choice"  # multiple_choice, text, true_false
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    points: int = 1

class Quiz(BaseModel):
    """Тест на знания"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    questions: List[QuizQuestion] = []
    passing_score: int = 70  # Процент для прохождения
    time_limit_minutes: Optional[int] = None

class ExerciseResult(BaseModel):
    """Результат выполнения упражнения"""
    exercise_id: str
    user_id: str
    answer: str
    is_correct: Optional[bool] = None
    feedback: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class LessonAnalytics(BaseModel):
    """Аналитика прохождения урока"""
    lesson_id: str
    user_id: str
    theory_read_time: int = 0  # Время чтения теории в минутах
    exercises_completed: int = 0
    exercises_correct: int = 0
    quiz_score: Optional[int] = None
    challenge_progress: int = 0  # Процент выполнения челленджа
    total_time_spent: int = 0  # Общее время в минутах
    recommendations: List[str] = []  # Персональные рекомендации
    strengths: List[str] = []  # Сильные стороны
    areas_for_improvement: List[str] = []  # Зоны роста
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class LessonFile(BaseModel):
    """Файл урока (PDF, Word, TXT, Excel, Video)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_filename: str
    file_type: str  # pdf, word, txt, excel, video
    file_size: int
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    lesson_section: str  # theory, exercises, challenge, quiz, analytics

class LessonV2(BaseModel):
    """Новая модель урока с 5 разделами"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    module: str
    level: int = 1
    order: int = 0
    points_required: int = 0
    is_active: bool = True

    # 1. ТЕОРИЯ - структурированная теория
    theory: List[TheoryBlock] = []

    # 2. УПРАЖНЕНИЯ - интерактивные задания
    exercises: List[Exercise] = []

    # 3. ЧЕЛЛЕНДЖ - ежедневные задания
    challenge: Optional[Challenge] = None

    # 4. ТЕСТ - проверка знаний
    quiz: Optional[Quiz] = None

    # 5. АНАЛИТИКА - результаты и рекомендации (вычисляется динамически)
    analytics_enabled: bool = True

    # Файлы
    files: List[LessonFile] = []

    # Мета-информация
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    updated_by: str

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

# Scoring System Configuration Models
class ScoringSystemConfig(BaseModel):
    """Конфигурация системы оценки дня"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Базовый счёт
    base_score: int = 20
    
    # Личная энергия планеты дня
    personal_energy_high: int = 10      # >= 7
    personal_energy_low: int = -10      # 1-3
    personal_energy_zero: int = -15     # 0
    
    # Резонанс числа души
    soul_resonance: int = 1             # Точное совпадение
    soul_friendship: int = 5            # Дружественные планеты
    soul_hostility: int = -10           # Враждебные планеты
    
    # Резонанс числа ума
    mind_resonance: int = 1             # Точное совпадение
    mind_friendship: int = 6            # Дружественные планеты
    mind_hostility: int = -20           # Враждебные планеты
    
    # Резонанс числа судьбы
    destiny_resonance: int = 1          # Точное совпадение
    destiny_hostility: int = -30        # Враждебные планеты
    
    # Сила планеты в квадрате Пифагора
    planet_strength_high: int = 12      # >= 4 цифр
    planet_strength_medium: int = 1     # 2-3 цифры
    planet_strength_low: int = -10      # 0 цифр
    
    # Особые дни и периоды
    birthday_bonus: int = 15            # День рождения
    rahu_kaal_penalty: int = -5         # Rahu Kaal
    favorable_period_bonus: int = 5     # Abhijit Muhurta
    
    # Дружественность планет
    planet_friendship_bonus: int = 8    # Дружественные планеты
    planet_hostility_penalty: int = -8  # Враждебные планеты
    
    # Нумерология имени/адреса/машины
    name_address_bonus: int = 5         # Совпадение
    name_address_penalty: int = -5      # Конфликт
    
    # Глобальная гармония
    global_harmony_bonus: int = 10      # Больше дружественных
    global_harmony_penalty: int = -10   # Больше враждебных
    
    # Число дня
    day_number_bonus: int = 5           # Совпадение с личными числами
    
    # Метаданные
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None    # email администратора
    is_active: bool = True              # Активная конфигурация
    version: int = 1                    # Версия конфигурации

class ScoringSystemConfigUpdate(BaseModel):
    """Обновление конфигурации системы оценки"""
    base_score: Optional[int] = None
    personal_energy_high: Optional[int] = None
    personal_energy_low: Optional[int] = None
    personal_energy_zero: Optional[int] = None
    soul_resonance: Optional[int] = None
    soul_friendship: Optional[int] = None
    soul_hostility: Optional[int] = None
    mind_resonance: Optional[int] = None
    mind_friendship: Optional[int] = None
    mind_hostility: Optional[int] = None
    destiny_resonance: Optional[int] = None
    destiny_hostility: Optional[int] = None
    planet_strength_high: Optional[int] = None
    planet_strength_medium: Optional[int] = None
    planet_strength_low: Optional[int] = None
    birthday_bonus: Optional[int] = None
    rahu_kaal_penalty: Optional[int] = None
    favorable_period_bonus: Optional[int] = None
    planet_friendship_bonus: Optional[int] = None
    planet_hostility_penalty: Optional[int] = None
    name_address_bonus: Optional[int] = None
    name_address_penalty: Optional[int] = None
    global_harmony_bonus: Optional[int] = None
    global_harmony_penalty: Optional[int] = None
    day_number_bonus: Optional[int] = None

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

# Scoring Configuration Models
class ScoringConfig(BaseModel):
    """Конфигурация системы баллов для оценки дня"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Базовые настройки
    base_score: int = 20
    
    # Личная энергия планеты дня (DDMM × YYYY)
    personal_energy_high: int = 10      # >= 7
    personal_energy_low: int = -10      # 1-3
    personal_energy_zero: int = -15     # = 0
    
    # Резонанс числа души
    soul_resonance: int = 1             # Полное совпадение
    soul_friendship: int = 5            # Дружественные планеты
    soul_hostility: int = -10           # Враждебные планеты
    
    # Резонанс числа ума
    mind_resonance: int = 1             # Полное совпадение
    mind_friendship: int = 6            # Дружественные планеты
    mind_hostility: int = -20           # Враждебные планеты
    
    # Резонанс числа судьбы
    destiny_resonance: int = 1          # Полное совпадение
    destiny_hostility: int = -30        # Враждебные планеты
    
    # Сила планеты в квадрате Пифагора
    planet_strength_high: int = 12      # >= 4 цифры
    planet_strength_medium: int = 1     # 2-3 цифры
    planet_strength_low: int = -10      # 0 цифр
    
    # Специальные бонусы
    birthday_bonus: int = 15            # День рождения (день недели)
    planet_friendship: int = 8          # Дружественность планет
    planet_hostility: int = -8          # Враждебность планет
    
    # Нумерология имени/адреса/машины
    name_resonance: int = 5             # Совпадение с планетой дня
    name_conflict: int = -5             # Конфликт с планетой дня
    
    # Ведические периоды
    rahu_kaal_penalty: int = -5         # Период Раху Каал
    favorable_period_bonus: int = 5     # Благоприятный период
    
    # Глобальная гармония
    global_harmony_bonus: int = 10      # Больше дружественных планет
    global_harmony_penalty: int = -10   # Больше враждебных планет
    
    # Число дня
    day_number_bonus: int = 5           # Совпадение числа дня
    
    # Метаданные
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    version: str = "1.0"
    description: str = "Финальная система оценки дня"

class ScoringConfigUpdate(BaseModel):
    """Модель для обновления конфигурации баллов"""
    base_score: Optional[int] = None
    personal_energy_high: Optional[int] = None
    personal_energy_low: Optional[int] = None
    personal_energy_zero: Optional[int] = None
    soul_resonance: Optional[int] = None
    soul_friendship: Optional[int] = None
    soul_hostility: Optional[int] = None
    mind_resonance: Optional[int] = None
    mind_friendship: Optional[int] = None
    mind_hostility: Optional[int] = None
    destiny_resonance: Optional[int] = None
    destiny_hostility: Optional[int] = None
    planet_strength_high: Optional[int] = None
    planet_strength_medium: Optional[int] = None
    planet_strength_low: Optional[int] = None
    birthday_bonus: Optional[int] = None
    planet_friendship: Optional[int] = None
    planet_hostility: Optional[int] = None
    name_resonance: Optional[int] = None

# Learning Points Configuration Models
class LearningPointsConfig(BaseModel):
    """Конфигурация начисления баллов за обучение"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Баллы за просмотр видео (за минуту)
    video_points_per_minute: int = 1  # 1 балл за минуту просмотра видео
    
    # Баллы за просмотр PDF файлов
    pdf_points_per_view: int = 5  # 5 баллов за просмотр PDF документа
    media_points_per_view: int = 10  # 10 баллов за просмотр медиафайла
    
    # Баллы за время нахождения на сайте (за минуту)
    time_points_per_minute: int = 1  # 1 балл за минуту на сайте
    
    # Баллы за прохождение челленджа
    challenge_points_per_day: int = 10  # 10 баллов за каждый день челленджа
    challenge_bonus_points: int = 50  # 50 бонусных баллов за завершение всего челленджа
    
    # Баллы за прохождение теста
    quiz_points_per_attempt: int = 10  # 10 баллов за прохождение теста
    
    # Баллы за выполнение упражнения
    exercise_points_per_submission: int = 10  # 10 баллов за отправку упражнения
    
    # Метаданные
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None  # email администратора
    is_active: bool = True  # Активная конфигурация
    version: int = 1  # Версия конфигурации

class LearningPointsConfigUpdate(BaseModel):
    """Модель для обновления конфигурации начисления баллов за обучение"""
    video_points_per_minute: Optional[int] = None
    pdf_points_per_view: Optional[int] = None
    media_points_per_view: Optional[int] = None
    time_points_per_minute: Optional[int] = None
    challenge_points_per_day: Optional[int] = None
    challenge_bonus_points: Optional[int] = None
    quiz_points_per_attempt: Optional[int] = None
    exercise_points_per_submission: Optional[int] = None

class NumerologyCreditsConfig(BaseModel):
    """Конфигурация стоимости услуг нумерологии"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Планетарные маршруты
    planetary_weekly: int = 10  # Планетарный маршрут на неделю
    planetary_monthly: int = 30  # Планетарный маршрут на месяц
    planetary_quarterly: int = 100  # Планетарный маршрут на квартал
    
    # Динамика энергии планет
    planetary_energy_weekly: int = 10  # Динамика энергии планет на неделю
    planetary_energy_monthly: int = 30  # Динамика энергии планет на месяц
    planetary_energy_quarterly: int = 100  # Динамика энергии планет на квартал
    
    # Метаданные
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None  # email администратора
    is_active: bool = True  # Активная конфигурация
    version: int = 1  # Версия конфигурации

class NumerologyCreditsConfigUpdate(BaseModel):
    """Модель для обновления конфигурации стоимости услуг нумерологии"""
    planetary_weekly: Optional[int] = None
    planetary_monthly: Optional[int] = None
    planetary_quarterly: Optional[int] = None
    planetary_energy_weekly: Optional[int] = None
    planetary_energy_monthly: Optional[int] = None
    planetary_energy_quarterly: Optional[int] = None

class CreditsDeductionConfig(BaseModel):
    """Единая конфигурация всех списаний баллов"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # === НУМЕРОЛОГИЯ ===
    name_numerology: int = 1                    # Нумерология имени
    personal_numbers: int = 1                   # Расчёт персональных чисел
    pythagorean_square: int = 1                 # Квадрат Пифагора
    compatibility_pair: int = 1                 # Совместимость пары
    group_compatibility: int = 5                # Групповая совместимость (5 человек)
    
    # === ВЕДИЧЕСКОЕ ВРЕМЯ ===
    vedic_daily: int = 1                        # Ведическое время на день
    planetary_daily: int = 1                    # Планетарный маршрут на день
    planetary_weekly: int = 10                  # Планетарный маршрут на неделю
    planetary_monthly: int = 30                 # Планетарный маршрут на месяц
    planetary_quarterly: int = 100              # Планетарный маршрут на квартал
    
    # === ДИНАМИКА ЭНЕРГИИ ПЛАНЕТ ===
    planetary_energy_weekly: int = 10           # Динамика энергии планет на неделю
    planetary_energy_monthly: int = 30          # Динамика энергии планет на месяц
    planetary_energy_quarterly: int = 100       # Динамика энергии планет на квартал
    
    # === ТЕСТЫ/КВИЗЫ ===
    personality_test: int = 1                   # Тест личности
    quiz_completion: int = 1                    # Прохождение Quiz
    
    # === ОБУЧЕНИЕ ===
    lesson_viewing: int = 10                    # Просмотр урока
    material_viewing: int = 1                   # Просмотр материалов
    
    # === ОТЧЁТЫ ===
    pdf_report_numerology: int = 5              # Генерация PDF отчёта по нумерологии
    html_report_numerology: int = 3             # Генерация HTML отчёта по нумерологии
    pdf_report_compatibility: int = 5           # Генерация PDF отчёта по совместимости
    html_report_compatibility: int = 3          # Генерация HTML отчёта по совместимости
    
    # Метаданные
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None  # email администратора
    is_active: bool = True  # Активная конфигурация
    version: int = 1  # Версия конфигурации

class CreditsDeductionConfigUpdate(BaseModel):
    """Модель для обновления конфигурации списания баллов"""
    # Нумерология
    name_numerology: Optional[int] = None
    personal_numbers: Optional[int] = None
    pythagorean_square: Optional[int] = None
    compatibility_pair: Optional[int] = None
    group_compatibility: Optional[int] = None
    
    # Ведическое время
    vedic_daily: Optional[int] = None
    planetary_daily: Optional[int] = None
    planetary_weekly: Optional[int] = None
    planetary_monthly: Optional[int] = None
    planetary_quarterly: Optional[int] = None
    
    # Динамика энергии планет
    planetary_energy_weekly: Optional[int] = None
    planetary_energy_monthly: Optional[int] = None
    planetary_energy_quarterly: Optional[int] = None
    
    # Тесты/Квизы
    personality_test: Optional[int] = None
    quiz_completion: Optional[int] = None
    
    # Обучение
    lesson_viewing: Optional[int] = None
    material_viewing: Optional[int] = None
    
    # Отчёты
    pdf_report_numerology: Optional[int] = None
    html_report_numerology: Optional[int] = None
    pdf_report_compatibility: Optional[int] = None
    html_report_compatibility: Optional[int] = None

class PlanetaryEnergyModifiersConfig(BaseModel):
    """Конфигурация модификаторов для расчёта энергии планет"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # === БАЗОВЫЕ МОДИФИКАТОРЫ ===
    # Дружественность/враждебность планет
    friend_planet_bonus: float = 0.10  # +10% для дружественных планет
    enemy_planet_penalty: float = 0.10  # -10% для вражеских планет
    
    # Фрактал поведения
    fractal_present_bonus: float = 0.10  # +10% если планета присутствует во фрактале
    fractal_absent_penalty: float = 0.10  # -10% если планета отсутствует во фрактале
    
    # Числа проблем
    problem_number_penalty: float = 0.10  # -10% если планета в числах проблем
    
    # === ИНДИВИДУАЛЬНЫЕ ЧИСЛА ===
    individual_year_bonus: float = 0.06  # +6% за число индивидуального года
    individual_month_bonus: float = 0.05  # +5% за число индивидуального месяца
    individual_day_bonus: float = 0.07  # +7% за число индивидуального дня
    
    # === КВАДРАТ ПИФАГОРА ===
    pythagorean_digit_bonus: float = 0.03  # +3% за каждую цифру в квадрате
    
    # === ПЕРСОНАЛЬНЫЕ ЧИСЛА ===
    soul_number_bonus: float = 0.08  # +8% за число души
    mind_number_bonus: float = 0.06  # +6% за число ума
    destiny_number_bonus: float = 0.05  # +5% за число судьбы
    wisdom_number_bonus: float = 0.04  # +4% за число мудрости
    ruling_number_bonus: float = 0.07  # +7% за правящее число
    
    # === ГОРИЗОНТАЛИ, ВЕРТИКАЛИ, ДИАГОНАЛИ ===
    line_sum_bonus: float = 2.0  # +2 за каждую сумму в линии
    
    # === ИМЯ И ФАМИЛИЯ ===
    name_number_bonus: float = 0.04  # +4% за число имени
    surname_number_bonus: float = 0.04  # +4% за число фамилии
    total_name_bonus: float = 0.05  # +5% за полное число имени
    
    # === ИНДИКАТОРЫ ДНЯ НЕДЕЛИ ===
    weekday_multiplier: float = 3.0  # Множитель для индикаторов дня недели
    
    # === СОВПАДЕНИЯ ===
    personal_day_match_bonus: float = 0.60  # +60% если день совпадает с личным днём
    personal_month_match_bonus: float = 0.50  # +50% если месяц совпадает с днём
    current_day_match_bonus: float = 0.40  # +40% если число совпадает с текущим днём
    
    # === ВРАЖДЕБНОСТЬ/ДРУЖЕСТВЕННОСТЬ ПРИ НЕСОВПАДЕНИИ ===
    enemy_mismatch_penalty: float = 0.30  # -30% для вражеских планет при несовпадении
    friend_mismatch_bonus: float = 0.15  # +15% для дружественных планет при несовпадении
    neutral_mismatch_penalty: float = 0.10  # -10% для нейтральных планет при несовпадении
    
    # === ЧИСЛА ПРОБЛЕМ ===
    problem_number_match_penalty: float = 0.80  # -80% если число проблемы совпадает с важным числом
    
    # === JANMA ANK = 22 (МАСТЕР ЧИСЛО) ===
    janma_ank_22_bonus: float = 0.25  # +25% для Rahu при Janma Ank = 22
    janma_ank_22_match_bonus: float = 0.30  # +30% дополнительно если совпадает с днём
    
    # === ЦИКЛИЧНОСТЬ ===
    cyclicity_bonus: float = 0.20  # +20% для повторяющихся чисел
    cyclicity_penalty: float = 0.05  # -5% для неповторяющихся планет при цикличности
    
    # === НОРМАЛИЗАЦИЯ ===
    normalization_min: int = 10  # Минимальное значение после нормализации (не 0)
    normalization_max: int = 90  # Максимальное значение после нормализации (не 100)
    energy_cap_multiplier: float = 3.0  # Максимальная энергия = destiny_number * multiplier
    energy_floor_multiplier: float = 0.1  # Минимальная энергия = destiny_number * multiplier
    
    # === АНТИЦИКЛИЧНОСТЬ ===
    anti_cyclicity_enabled: bool = True  # Включить функцию убирания цикличности
    anti_cyclicity_threshold: float = 5.0  # Порог стандартного отклонения для обнаружения цикличности
    anti_cyclicity_variation: float = 3.0  # Величина вариации для разбалансировки (в единицах энергии)
    
    # === ПОРОГ БЛАГОПРИЯТНЫХ/НЕБЛАГОПРИЯТНЫХ ДНЕЙ ===
    favorable_day_threshold: float = 60.0  # Порог средней энергии планет для определения благоприятных дней (в процентах) - устаревший параметр
    favorable_day_score_threshold: float = 50.0  # Порог баллов для определения благоприятных дней (0-100, где 50 - нейтральный день)
    
    # Метаданные
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None  # email администратора
    is_active: bool = True  # Активная конфигурация
    version: int = 1  # Версия конфигурации

class MonthlyRouteConfig(BaseModel):
    """Конфигурация настроек для расчёта месячного планетарного маршрута"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # === ПОРОГИ ДЛЯ КЛАССИФИКАЦИИ ДНЕЙ ===
    favorable_day_threshold: float = 60.0  # Порог для благоприятных дней (avg_energy >= threshold)
    best_day_threshold: float = 70.0  # Порог для лучших дней (avg_energy >= threshold)
    challenging_day_threshold: float = 40.0  # Порог для сложных дней (avg_energy < threshold)
    
    # === ПОРОГИ ДЛЯ НЕДЕЛЬНОГО АНАЛИЗА ===
    high_energy_week_threshold: float = 70.0  # Высокая энергия недели (avg_energy >= threshold)
    low_energy_week_threshold: float = 40.0  # Низкая энергия недели (avg_energy < threshold)
    favorable_week_threshold: float = 60.0  # Благоприятная неделя (avg_energy >= threshold)
    challenging_week_threshold: float = 40.0  # Сложная неделя (avg_energy < threshold)
    many_favorable_days_threshold: int = 5  # Много благоприятных дней (>= threshold)
    several_challenging_days_threshold: int = 3  # Несколько сложных дней (>= threshold)
    
    # === ПОРОГИ ДЛЯ СФЕР ЖИЗНИ ===
    sphere_excellent_threshold: float = 70.0  # Отлично (energy >= threshold)
    sphere_good_threshold: float = 55.0  # Хорошо (energy >= threshold)
    sphere_satisfactory_threshold: float = 40.0  # Удовлетворительно (energy >= threshold)
    sphere_attention_threshold: float = 40.0  # Требует внимания (energy < threshold)
    sphere_best_days_threshold: float = 70.0  # Лучшие дни сферы (energy >= threshold)
    sphere_challenging_days_threshold: float = 40.0  # Сложные дни сферы (energy < threshold)
    
    # === ПОРОГИ ДЛЯ ТРЕНДОВ ===
    optimal_start_energy_threshold: float = 65.0  # Оптимальный период для начинаний (energy >= threshold)
    optimal_start_min_days: int = 3  # Минимум дней подряд для оптимального периода
    completion_energy_min: float = 40.0  # Минимум энергии для периода завершения
    completion_energy_max: float = 55.0  # Максимум энергии для периода завершения
    completion_min_days: int = 2  # Минимум дней подряд для периода завершения
    trend_rising_threshold: float = 5.0  # Рост энергии (second_avg > first_avg + threshold)
    trend_declining_threshold: float = 5.0  # Снижение энергии (second_avg < first_avg - threshold)
    
    # === ПОРОГИ ДЛЯ ТРАНЗИТОВ ===
    transit_peak_threshold: float = 85.0  # Пик энергии планеты (energy >= threshold)
    transit_low_threshold: float = 15.0  # Низкая энергия планеты (energy <= threshold)
    max_transits_per_month: int = 20  # Максимальное количество транзитов в месяц
    
    # === ПОРОГИ ДЛЯ МЕСЯЧНОГО АНАЛИЗА ===
    month_high_energy_threshold: float = 65.0  # Высокая энергия месяца (avg_month_energy >= threshold)
    month_low_energy_threshold: float = 45.0  # Низкая энергия месяца (avg_month_energy < threshold)
    
    # Метаданные
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None  # email администратора
    is_active: bool = True  # Активная конфигурация
    version: int = 1  # Версия конфигурации

class MonthlyRouteConfigUpdate(BaseModel):
    """Модель для обновления конфигурации месячного маршрута"""
    # Пороги для классификации дней
    favorable_day_threshold: Optional[float] = None
    best_day_threshold: Optional[float] = None
    challenging_day_threshold: Optional[float] = None
    
    # Пороги для недельного анализа
    high_energy_week_threshold: Optional[float] = None
    low_energy_week_threshold: Optional[float] = None
    favorable_week_threshold: Optional[float] = None
    challenging_week_threshold: Optional[float] = None
    many_favorable_days_threshold: Optional[int] = None
    several_challenging_days_threshold: Optional[int] = None
    
    # Пороги для сфер жизни
    sphere_excellent_threshold: Optional[float] = None
    sphere_good_threshold: Optional[float] = None
    sphere_satisfactory_threshold: Optional[float] = None
    sphere_attention_threshold: Optional[float] = None
    sphere_best_days_threshold: Optional[float] = None
    sphere_challenging_days_threshold: Optional[float] = None
    
    # Пороги для трендов
    optimal_start_energy_threshold: Optional[float] = None
    optimal_start_min_days: Optional[int] = None
    completion_energy_min: Optional[float] = None
    completion_energy_max: Optional[float] = None
    completion_min_days: Optional[int] = None
    trend_rising_threshold: Optional[float] = None
    trend_declining_threshold: Optional[float] = None
    
    # Пороги для транзитов
    transit_peak_threshold: Optional[float] = None
    transit_low_threshold: Optional[float] = None
    max_transits_per_month: Optional[int] = None
    
    # Пороги для месячного анализа
    month_high_energy_threshold: Optional[float] = None
    month_low_energy_threshold: Optional[float] = None

class PlanetaryEnergyModifiersConfigUpdate(BaseModel):
    """Модель для обновления конфигурации модификаторов энергии планет"""
    # Базовые модификаторы
    friend_planet_bonus: Optional[float] = None
    enemy_planet_penalty: Optional[float] = None
    fractal_present_bonus: Optional[float] = None
    fractal_absent_penalty: Optional[float] = None
    problem_number_penalty: Optional[float] = None
    
    # Индивидуальные числа
    individual_year_bonus: Optional[float] = None
    individual_month_bonus: Optional[float] = None
    individual_day_bonus: Optional[float] = None
    
    # Квадрат Пифагора
    pythagorean_digit_bonus: Optional[float] = None
    
    # Персональные числа
    soul_number_bonus: Optional[float] = None
    mind_number_bonus: Optional[float] = None
    destiny_number_bonus: Optional[float] = None
    wisdom_number_bonus: Optional[float] = None
    ruling_number_bonus: Optional[float] = None
    
    # Горизонтали, вертикали, диагонали
    line_sum_bonus: Optional[float] = None
    
    # Имя и фамилия
    name_number_bonus: Optional[float] = None
    surname_number_bonus: Optional[float] = None
    total_name_bonus: Optional[float] = None
    
    # Индикаторы дня недели
    weekday_multiplier: Optional[float] = None
    
    # Совпадения
    personal_day_match_bonus: Optional[float] = None
    personal_month_match_bonus: Optional[float] = None
    current_day_match_bonus: Optional[float] = None
    
    # Враждебность/дружественность при несовпадении
    enemy_mismatch_penalty: Optional[float] = None
    friend_mismatch_bonus: Optional[float] = None
    neutral_mismatch_penalty: Optional[float] = None
    
    # Числа проблем
    problem_number_match_penalty: Optional[float] = None
    
    # Janma Ank = 22
    janma_ank_22_bonus: Optional[float] = None
    janma_ank_22_match_bonus: Optional[float] = None
    
    # Цикличность
    cyclicity_bonus: Optional[float] = None
    cyclicity_penalty: Optional[float] = None
    
    # Нормализация
    normalization_min: Optional[int] = None
    normalization_max: Optional[int] = None
    energy_cap_multiplier: Optional[float] = None
    energy_floor_multiplier: Optional[float] = None
    
    # Антицикличность
    anti_cyclicity_enabled: Optional[bool] = None
    anti_cyclicity_threshold: Optional[float] = None
    anti_cyclicity_variation: Optional[float] = None
    
    # Порог благоприятных/неблагоприятных дней
    favorable_day_threshold: Optional[float] = None  # Порог средней энергии планет для определения благоприятных дней (в процентах) - устаревший параметр
    favorable_day_score_threshold: Optional[float] = None  # Порог баллов для определения благоприятных дней (0-100)

# ===== МОДЕЛИ ДЛЯ ХРАНЕНИЯ ОТВЕТОВ СТУДЕНТОВ =====

class ExerciseResponse(BaseModel):
    """Ответ студента на упражнение"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    lesson_id: str
    exercise_id: str
    response_text: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed: bool = False
    admin_comment: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None

class QuizAttempt(BaseModel):
    """Попытка прохождения теста"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    lesson_id: str
    quiz_id: str
    answers: List[Dict[str, Any]]  # [{question_id, selected_answer, is_correct}]
    score: int  # Набранные баллы
    max_score: int  # Максимальные баллы
    percentage: float  # Процент правильных ответов
    passed: bool  # Прошел ли тест
    started_at: datetime
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    time_spent_minutes: Optional[int] = None

class ChallengeProgress(BaseModel):
    """Прогресс прохождения челленджа"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    lesson_id: str
    challenge_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_days: List[int] = []  # Список завершенных дней [1, 2, 3]
    daily_notes: Dict[int, str] = {}  # {day: note}
    is_completed: bool = False
    completed_at: Optional[datetime] = None

class LessonProgress(BaseModel):
    """Общий прогресс по уроку"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    lesson_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Прогресс по разделам
    theory_completed: bool = False
    exercises_completed: int = 0  # Количество завершенных упражнений
    challenge_completed: bool = False
    quiz_completed: bool = False
    quiz_passed: bool = False

    # Общий прогресс
    completion_percentage: float = 0.0
    is_completed: bool = False

    # Метаданные
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)
    time_spent_minutes: int = 0

class StudentAnalytics(BaseModel):
    """Аналитика по студенту для урока"""
    user_id: str
    lesson_id: str

    # Статистика
    total_exercises: int
    completed_exercises: int
    quiz_attempts: int
    best_quiz_score: Optional[float] = None
    challenge_progress: Optional[int] = None  # Количество завершенных дней

    # Временные метрики
    time_spent_minutes: int
    first_access: datetime
    last_access: datetime

    # Активность
    is_active: bool
    completion_rate: float  # Процент завершения урока



    description: Optional[str] = None
    name_conflict: Optional[int] = None
    rahu_kaal_penalty: Optional[int] = None
    favorable_period_bonus: Optional[int] = None
    global_harmony_bonus: Optional[int] = None
    global_harmony_penalty: Optional[int] = None
    day_number_bonus: Optional[int] = None
    description: Optional[str] = None