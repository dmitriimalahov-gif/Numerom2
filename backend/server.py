from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, status, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse, StreamingResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pytz
import os
import uuid
import io
import shutil
import requests
import logging
import tempfile
import re
import mimetypes

from dotenv import load_dotenv

# Local imports
from models import (
    User, UserCreate, UserResponse, TokenResponse, LoginRequest,
    PaymentTransaction, PaymentRequest,
    NumerologyCalculation, CompatibilityRequest,
    StatusCheck, StatusCheckCreate,
    VideoLesson, AdminUser, QuizResult,
    VedicTimeRequest, PDFReportRequest, HTMLReportRequest,
    UserProfileUpdate, GroupCompatibilityRequest, GroupCompatibilityPerson,
    PersonalConsultation, ConsultationPurchase, CreditTransaction, CREDIT_COSTS,
    PlanetaryAdviceResponse, LearningPointsConfig, LearningPointsConfigUpdate,
    NumerologyCreditsConfig, NumerologyCreditsConfigUpdate,
    CreditsDeductionConfig, CreditsDeductionConfigUpdate,
    PlanetaryEnergyModifiersConfig, PlanetaryEnergyModifiersConfigUpdate,
    MonthlyRouteConfig, MonthlyRouteConfigUpdate
)
# Import V2 learning system models and functions
from models_v2 import (
    LessonV2, TheoryBlock, Exercise, Challenge, ChallengeDay, Quiz, QuizQuestion,
    LessonFile, ExerciseResult, LessonAnalytics, LessonProgress, ChallengeProgress,
    QuizAttempt, StudentAnalytics
)
from auth import (
    get_current_user, create_access_token, get_password_hash, verify_password,
    create_user_response, ensure_super_admin_exists
)
from push_notifications import PushNotificationManager, push_manager
from numerology import (
    calculate_personal_numbers,
    calculate_compatibility,
    parse_birth_date,
    create_pythagorean_square,
    reduce_to_single_digit,
    reduce_to_single_digit_always,
    reduce_for_ruling_number
)
from vedic_numerology import (
    calculate_comprehensive_vedic_numerology,
    generate_weekly_planetary_energy
)
from vedic_time_calculations import get_vedic_day_schedule, get_monthly_planetary_route, get_quarterly_planetary_route, calculate_planetary_hours, calculate_night_planetary_hours, is_favorable_time, get_sunrise_sunset
from html_generator import create_numerology_report_html
from pdf_generator import create_numerology_report_pdf, create_compatibility_pdf
from planetary_advice import init_planetary_advice_collection, get_personalized_planetary_advice
import stripe

# Helpers: calculate full name number (только латиница)
def _letters_to_number_sum(text: str) -> int:
    if not text:
        return 0
    norm = [ch for ch in (text or '').upper() if 'A' <= ch <= 'Z']
    total = 0
    for ch in norm:
        total += ord(ch) - ord('A') + 1  # A=1 ... Z=26
    return total

def calculate_full_name_number(name: str = '', surname: str = '') -> int:
    """
    Число имени: используем ТОЛЬКО латиницу из поля name и фамилии.
    Полное число имени = reduce( sum(буквы имени+фамилии) ).
    """
    base_sum = _letters_to_number_sum((name or '') + (surname or ''))
    x = abs(int(base_sum))
    while x > 9:
        x = sum(int(d) for d in str(x))
    return x

# Load env
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Mongo
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('MONGODB_DATABASE')]

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Payments
STRIPE_API_KEY = os.environ.get('STRIPE_SECRET_KEY')
stripe.api_key = STRIPE_API_KEY
PAYMENT_DEMO_MODE = not STRIPE_API_KEY or STRIPE_API_KEY == 'sk_test_dummy_key_for_testing'

PAYMENT_PACKAGES = {
    'one_time': 0.99,    # 0,99€ = 10 баллов + месяц доступа
    'monthly': 9.99,     # 9,99€ = 150 баллов + месяц доступа  
    'annual': 66.6,      # 66,6€ = 500 баллов + год доступа
    'master_consultation': 666.0  # 666€ = 10000 баллов + персональная консультация от мастера
}

SUBSCRIPTION_CREDITS = {
    'one_time': 10,      # 10 баллов за 0,99€
    'monthly': 150,      # 150 баллов за 9,99€
    'annual': 1000,      # 1000 баллов за 66,6€ (было 500)
    'master_consultation': 10000  # 10000 баллов за 666€ + персональная консультация
}

# FastAPI app
app = FastAPI()
api_router = APIRouter(prefix='/api')

# Mount static files directory
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Global scoring configuration cache
_scoring_config_cache = None
_scoring_config_cache_time = None
SCORING_CONFIG_CACHE_TTL = 300  # 5 минут

def get_scoring_config_sync() -> Dict[str, int]:
    """Получить конфигурацию системы оценки (синхронная версия с кэшированием)"""
    global _scoring_config_cache, _scoring_config_cache_time
    
    # Проверяем кэш
    if _scoring_config_cache and _scoring_config_cache_time:
        if (datetime.utcnow() - _scoring_config_cache_time).total_seconds() < SCORING_CONFIG_CACHE_TTL:
            return _scoring_config_cache
    
    # Пытаемся загрузить из базы данных
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Если event loop уже запущен, используем дефолтные значения
            # (обновление произойдёт при следующем вызове)
            pass
        else:
            config = loop.run_until_complete(db.scoring_config.find_one({'is_active': True}))
            if config:
                config.pop('_id', None)
                _scoring_config_cache = config
                _scoring_config_cache_time = datetime.utcnow()
                return config
    except Exception as e:
        print(f"⚠️ Ошибка загрузки конфигурации из БД: {e}")
    
    # Если не удалось загрузить из БД, возвращаем значения по умолчанию
    default_config = {
        'base_score': 20,
        'personal_energy_high': 10,
        'personal_energy_low': -10,
        'personal_energy_zero': -15,
        'soul_resonance': 1,
        'soul_friendship': 5,
        'soul_hostility': -10,
        'mind_resonance': 1,
        'mind_friendship': 6,
        'mind_hostility': -20,
        'destiny_resonance': 1,
        'destiny_hostility': -30,
        'planet_strength_high': 12,
        'planet_strength_medium': 1,
        'planet_strength_low': -10,
        'birthday_bonus': 15,
        'rahu_kaal_penalty': -5,
        'favorable_period_bonus': 5,
        'planet_friendship': 8,
        'planet_hostility': -8,
        'name_resonance': 5,
        'name_conflict': -5,
        'global_harmony_bonus': 10,
        'global_harmony_penalty': -10,
        'day_number_bonus': 5
    }
    
    _scoring_config_cache = default_config
    _scoring_config_cache_time = datetime.utcnow()
    
    return default_config

async def load_scoring_config():
    """Загрузить конфигурацию из базы данных при старте приложения"""
    global _scoring_config_cache, _scoring_config_cache_time
    
    config = await db.scoring_config.find_one({'is_active': True})
    
    if not config:
        # Создаём конфигурацию по умолчанию
        from models import ScoringSystemConfig
        default_config = ScoringSystemConfig()
        await db.scoring_config.insert_one(default_config.dict())
        config = default_config.dict()
    
    # Кэшируем конфигурацию
    _scoring_config_cache = {k: v for k, v in config.items() if isinstance(v, int)}
    _scoring_config_cache_time = datetime.utcnow()
    
    print(f"✅ Конфигурация системы оценки загружена (версия {config.get('version', 1)})")

# Upload paths
UPLOAD_ROOT = Path('uploads')
MATERIALS_DIR = UPLOAD_ROOT / 'materials'
CONSULTATIONS_DIR = UPLOAD_ROOT / 'consultations'
CONSULTATIONS_VIDEO_DIR = CONSULTATIONS_DIR / 'videos'
CONSULTATIONS_PDF_DIR = CONSULTATIONS_DIR / 'pdfs'
CONSULTATIONS_SUBTITLES_DIR = CONSULTATIONS_DIR / 'subtitles'
LESSONS_DIR = UPLOAD_ROOT / 'lessons'
LESSONS_VIDEO_DIR = LESSONS_DIR / 'videos'
LESSONS_PDF_DIR = LESSONS_DIR / 'pdfs'
LESSONS_WORD_DIR = LESSONS_DIR / 'word'
LESSONS_RESOURCES_DIR = LESSONS_DIR / 'resources'
TMP_DIR = UPLOAD_ROOT / 'tmp'

@app.on_event('startup')
async def on_startup():
    global push_manager
    try:
        await ensure_super_admin_exists(db)
        await init_planetary_advice_collection(db)
        MATERIALS_DIR.mkdir(parents=True, exist_ok=True)
        CONSULTATIONS_DIR.mkdir(parents=True, exist_ok=True)
        CONSULTATIONS_VIDEO_DIR.mkdir(parents=True, exist_ok=True)
        CONSULTATIONS_PDF_DIR.mkdir(parents=True, exist_ok=True)
        CONSULTATIONS_SUBTITLES_DIR.mkdir(parents=True, exist_ok=True)
        LESSONS_DIR.mkdir(parents=True, exist_ok=True)
        LESSONS_VIDEO_DIR.mkdir(parents=True, exist_ok=True)
        LESSONS_PDF_DIR.mkdir(parents=True, exist_ok=True)
        LESSONS_WORD_DIR.mkdir(parents=True, exist_ok=True)
        LESSONS_RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
        TMP_DIR.mkdir(parents=True, exist_ok=True)

        # Инициализируем менеджер push уведомлений
        import push_notifications
        push_notifications.push_manager = PushNotificationManager(db)
        push_manager = push_notifications.push_manager
        logger.info('Push notification manager initialized')

        logger.info('Startup tasks completed')
    except Exception as e:
        logger.error(f'Startup error: {e}')

@app.on_event('shutdown')
async def on_shutdown():
    client.close()

# Helper function for credit transactions
async def record_credit_transaction(user_id: str, amount: int, description: str, category: str, details: dict = None):
    """Записать транзакцию баллов в историю"""
    # НЕ записываем транзакции с нулевой суммой - это ошибка логики
    if amount == 0:
        print(f"⚠️  Попытка записать транзакцию с нулевой суммой: {description}")
        return
        
    transaction = CreditTransaction(
        user_id=user_id,
        transaction_type='debit' if amount < 0 else 'credit',
        amount=amount,
        description=description,
        category=category,
        details=details or {}
    )
    await db.credit_transactions.insert_one(transaction.dict())

async def get_credits_deduction_config() -> dict:
    """Получить конфигурацию списания баллов"""
    try:
        config = await db.credits_deduction_config.find_one({'is_active': True})
        if config:
            config.pop('_id', None)
            return config
    except Exception as e:
        logger.error(f"Error getting credits deduction config: {e}")
    
    # Возвращаем значения по умолчанию
    default_config = CreditsDeductionConfig()
    return default_config.dict()

async def deduct_credits(user_id: str, cost: int, description: str, category: str, details: dict = None):
    """Списать баллы и записать транзакцию"""
    user = await db.users.find_one({'id': user_id})
    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    if user.get('credits_remaining', 0) < cost:
        raise HTTPException(status_code=402, detail='Недостаточно баллов для операции. Пополните баланс.')
    
    # Списываем баллы
    await db.users.update_one({'id': user_id}, {'$inc': {'credits_remaining': -cost}})
    
    # Записываем транзакцию
    await record_credit_transaction(user_id, -cost, description, category, details)

async def get_learning_points_config() -> dict:
    """Получить конфигурацию начисления баллов за обучение"""
    try:
        config = await db.learning_points_config.find_one({'is_active': True})
        if config:
            config.pop('_id', None)
            return config
    except Exception as e:
        logger.error(f"Error getting learning points config: {e}")
    
    # Возвращаем значения по умолчанию
    default_config = LearningPointsConfig()
    return default_config.dict()

async def award_credits_for_learning(user_id: str, amount: int, description: str, category: str, details: dict = None):
    """Начислить кредиты за обучение и записать транзакцию"""
    if amount <= 0:
        return  # Не начисляем нулевые или отрицательные баллы
    
    user = await db.users.find_one({'id': user_id})
    if not user:
        logger.warning(f"Попытка начислить кредиты несуществующему пользователю: {user_id}")
        return
    
    # Начисляем кредиты
    await db.users.update_one({'id': user_id}, {'$inc': {'credits_remaining': amount}})
    
    # Записываем транзакцию
    await record_credit_transaction(user_id, amount, description, category, details)
    
    logger.info(f"Начислено {amount} кредитов пользователю {user_id} за {description}")

# ----------------- CREDIT HISTORY -----------------
@api_router.get('/credits/costs')
async def get_credit_costs():
    """Получить актуальные стоимости всех операций из конфигурации"""
    try:
        # Получаем конфигурацию из БД
        config = await get_credits_deduction_config()
        
        # Возвращаем стоимости с fallback на дефолтные значения
        return {
            # Нумерология
            'personal_numbers': config.get('personal_numbers', CREDIT_COSTS.get('personal_numbers', 1)),
            'pythagorean_square': config.get('pythagorean_square', CREDIT_COSTS.get('pythagorean_square', 1)),
            'compatibility_pair': config.get('compatibility_pair', CREDIT_COSTS.get('compatibility_pair', 1)),
            'group_compatibility': config.get('group_compatibility', CREDIT_COSTS.get('group_compatibility', 5)),
            'name_numerology': config.get('name_numerology', CREDIT_COSTS.get('name_numerology', 1)),
            'address_numerology': config.get('address_numerology', CREDIT_COSTS.get('address_numerology', 1)),
            'car_numerology': config.get('car_numerology', CREDIT_COSTS.get('car_numerology', 1)),
            
            # Ведическое время
            'vedic_daily': config.get('vedic_daily', CREDIT_COSTS.get('vedic_daily', 1)),
            'vedic_weekly': config.get('vedic_weekly', CREDIT_COSTS.get('vedic_weekly', 2)),
            'vedic_monthly': config.get('vedic_monthly', CREDIT_COSTS.get('vedic_monthly', 5)),
            'vedic_quarterly': config.get('vedic_quarterly', CREDIT_COSTS.get('vedic_quarterly', 10)),
            
            # Планетарный маршрут
            'planetary_daily': config.get('planetary_daily', CREDIT_COSTS.get('planetary_daily', 1)),
            'planetary_weekly': config.get('planetary_weekly', CREDIT_COSTS.get('planetary_weekly', 2)),
            'planetary_monthly': config.get('planetary_monthly', CREDIT_COSTS.get('planetary_monthly', 5)),
            'planetary_quarterly': config.get('planetary_quarterly', CREDIT_COSTS.get('planetary_quarterly', 10)),
            
            # Отчеты
            'comprehensive_report': config.get('comprehensive_report', CREDIT_COSTS.get('comprehensive_report', 10)),
            'pdf_report': config.get('pdf_report', CREDIT_COSTS.get('pdf_report', 5)),
            'html_report': config.get('html_report', CREDIT_COSTS.get('html_report', 3)),
            
            # Прочее
            'personality_test': config.get('personality_test', CREDIT_COSTS.get('personality_test', 1)),
        }
    except Exception as e:
        logger.error(f"Error getting credit costs: {e}")
        # В случае ошибки возвращаем дефолтные значения
        return CREDIT_COSTS

@api_router.get('/user/credit-history')
async def get_credit_history(limit: int = 50, offset: int = 0, current_user: dict = Depends(get_current_user)):
    """Получить историю транзакций баллов пользователя"""
    user_id = current_user['user_id']
    
    # Получаем транзакции с пагинацией
    transactions = await db.credit_transactions.find(
        {'user_id': user_id}
    ).sort('created_at', -1).skip(offset).limit(limit).to_list(limit)
    
    # Очищаем от MongoDB _id
    result = []
    for transaction in transactions:
        transaction_dict = dict(transaction)
        transaction_dict.pop('_id', None)
        result.append(transaction_dict)
    
    return {
        'transactions': result,
        'total': await db.credit_transactions.count_documents({'user_id': user_id})
    }

@api_router.get('/user/points-breakdown')
async def get_points_breakdown(current_user: dict = Depends(get_current_user)):
    """Получить разбивку баллов по категориям"""
    user_id = current_user['user_id']
    
    # Получаем все транзакции пользователя
    transactions = await db.credit_transactions.find(
        {'user_id': user_id, 'transaction_type': 'credit'}
    ).to_list(length=None)
    
    # Инициализируем счетчики
    earned_points = 0  # Заработанные баллы (обучение, активность)
    purchased_points = 0  # Купленные баллы (подписка, покупка)
    admin_points = 0  # Баллы, добавленные администратором
    exercise_review_points = 0  # Баллы за проверку упражнений
    
    # Категории для заработанных баллов
    earned_categories = ['learning', 'exercise', 'quiz', 'challenge', 'lesson']
    
    # Категории для купленных баллов
    purchased_categories = ['purchase', 'subscription']
    
    # Обрабатываем транзакции
    for transaction in transactions:
        amount = transaction.get('amount', 0)
        category = transaction.get('category', '')
        details = transaction.get('details', {})
        
        if category in earned_categories:
            # Проверяем, не является ли это проверкой упражнения
            if category == 'exercise' and (details.get('reviewed_by') or details.get('admin_review')):
                exercise_review_points += amount
            else:
                earned_points += amount
        elif category in purchased_categories:
            purchased_points += amount
        elif category == 'admin' or details.get('added_by_admin'):
            admin_points += amount
        elif category == 'exercise_review' or details.get('exercise_review'):
            exercise_review_points += amount
        elif category == 'report':
            # Отчёты считаются заработанными (пользователь потратил баллы на получение отчёта)
            # Но это списание, поэтому не добавляем в earned_points
            # Можно добавить отдельную категорию для отчётов, если нужно
            pass
    
    # Получаем текущий баланс
    user = await db.users.find_one({'id': user_id})
    total_balance = user.get('credits_remaining', 0) if user else 0
    
    return {
        'earned_points': earned_points,
        'purchased_points': purchased_points,
        'admin_points': admin_points,
        'exercise_review_points': exercise_review_points,
        'total_balance': total_balance,
        'total_earned': earned_points + exercise_review_points  # Все заработанные включая проверку
    }

# ----------------- AUTH -----------------
@api_router.post('/auth/register', response_model=TokenResponse)
async def register(user_data: UserCreate, request: Request):
    existing = await db.users.find_one({'email': user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail='User already exists')
    
    # Определяем город по IP если не указан
    city = user_data.city
    if not city or city == "Москва":
        client_ip = request.client.host
        # Проверяем заголовки на случай прокси
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            client_ip = forwarded_for.split(',')[0].strip()
        
        detected_city = get_city_from_ip(client_ip)
        if detected_city != "Москва":
            city = detected_city
    
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        name=user_data.name or (user_data.full_name.split()[0] if user_data.full_name else None),
        surname=user_data.surname or (user_data.full_name.split()[1] if user_data.full_name and len(user_data.full_name.split()) > 1 else None),
        birth_date=user_data.birth_date,
        city=city or 'Москва',
        phone_number=user_data.phone_number,
        credits_remaining=100
    )
    await db.users.insert_one(user.dict())

    # Записываем начисление бонусных кредитов при регистрации
    credit_transaction = CreditTransaction(
        user_id=user.id,
        transaction_type='credit',
        amount=100,
        description='Приветственный бонус при регистрации',
        category='purchase',
        details={'reason': 'registration_bonus'}
    )
    await db.credit_transactions.insert_one(credit_transaction.dict())

    # Вычисляем роль из флагов (для новых пользователей всегда 'user')
    role = 'admin' if (user.is_super_admin or user.is_admin) else 'user'

    token = create_access_token({'sub': user.id, 'role': role})
    return TokenResponse(access_token=token, user=create_user_response(user))

@api_router.post('/auth/login', response_model=TokenResponse)
async def login(login_data: LoginRequest):
    print(f"=== ПОПЫТКА ВХОДА ===")
    print(f"Email: {login_data.email}")
    print(f"Пароль (первые 3 символа): {login_data.password[:3]}...")

    user_dict = await db.users.find_one({'email': login_data.email})
    print(f"Найден пользователь в БД: {user_dict is not None}")

    if not user_dict:
        print(f"ОШИБКА: Пользователь с email {login_data.email} не найден в БД")
        raise HTTPException(status_code=401, detail='Invalid credentials')

    user = User(**user_dict)
    print(f"User ID: {user.id}")
    print(f"User password_hash (первые 10 символов): {user.password_hash[:10]}...")

    password_valid = verify_password(login_data.password, user.password_hash)
    print(f"Проверка пароля: {password_valid}")

    if not password_valid:
        print(f"ОШИБКА: Неверный пароль для пользователя {login_data.email}")
        raise HTTPException(status_code=401, detail='Invalid credentials')

    # expire subscription if needed
    if user.subscription_expires_at and user.subscription_expires_at < datetime.utcnow():
        await db.users.update_one(
            {'id': user.id},
            {'$set': {'is_premium': False, 'subscription_type': None, 'subscription_expires_at': None}}
        )
        user.is_premium = False
        user.subscription_type = None

    # Вычисляем роль из флагов
    role = 'admin' if (user.is_super_admin or user.is_admin) else 'user'

    token = create_access_token({'sub': user.id, 'role': role})
    print(f"✅ УСПЕШНЫЙ ВХОД для {login_data.email}, роль: {role}")
    return TokenResponse(access_token=token, user=create_user_response(user))

# ----------------- PAYMENTS -----------------
@api_router.post('/payments/checkout/session')
async def create_checkout_session(payment_request: PaymentRequest, request: Request, current_user: dict = Depends(get_current_user)):
    if payment_request.package_type not in PAYMENT_PACKAGES:
        raise HTTPException(status_code=400, detail='Invalid package type')
    amount = PAYMENT_PACKAGES[payment_request.package_type]

    if PAYMENT_DEMO_MODE:
        session_id = f"cs_demo_{uuid.uuid4().hex[:16]}"
        transaction = PaymentTransaction(
            package_type=payment_request.package_type,
            amount=amount,
            currency='eur',
            session_id=session_id,
            payment_status='pending',
            metadata={'origin_url': payment_request.origin_url, 'demo': True},
            user_id=current_user['user_id']
        )
        await db.payment_transactions.insert_one(transaction.dict())
        url = f"{payment_request.origin_url}/payment-success?session_id={session_id}&demo=true"
        return {'url': url, 'session_id': session_id}

    try:
        success_url = f"{payment_request.origin_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{payment_request.origin_url}/payment-cancelled"
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': f'Numerom Package: {payment_request.package_type}',
                    },
                    'unit_amount': int(amount * 100),  # Stripe expects amounts in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={'package_type': payment_request.package_type, 'origin_url': payment_request.origin_url, 'user_id': current_user['user_id']}
        )
        
        transaction = PaymentTransaction(
            package_type=payment_request.package_type,
            amount=amount,
            currency='eur',
            session_id=session.id,
            payment_status='pending',
            metadata={'origin_url': payment_request.origin_url},
            user_id=current_user['user_id']
        )
        await db.payment_transactions.insert_one(transaction.dict())
        return {'url': session.url, 'session_id': session.id}
    except Exception as e:
        logger.error(f'Stripe error: {e}')
        raise HTTPException(status_code=500, detail=f'Failed to create checkout session: {e}')

@api_router.get('/payments/checkout/status/{session_id}')
async def get_payment_status(session_id: str):
    tx = await db.payment_transactions.find_one({'session_id': session_id})
    if not tx:
        raise HTTPException(status_code=404, detail='Transaction not found')

    # Demo mode: auto pay and grant credits
    if PAYMENT_DEMO_MODE or tx.get('metadata', {}).get('demo'):
        package = tx['package_type']
        user_id = tx.get('user_id')
        # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Проверяем что баллы еще не были начислены
        if user_id and tx.get('payment_status') != 'paid':
            # Добавляем баллы согласно пакету
            credits_to_add = SUBSCRIPTION_CREDITS.get(package, 0)
            await db.users.update_one({'id': user_id}, {'$inc': {'credits_remaining': credits_to_add}})
            
            # Записываем транзакцию в историю
            if credits_to_add > 0:
                package_names = {
                    'one_time': 'Разовая покупка',
                    'monthly': 'Месячная подписка',
                    'annual': 'Годовая подписка',
                    'master_consultation': 'Мастер консультация'
                }
                await record_credit_transaction(
                    user_id=user_id,
                    amount=credits_to_add,
                    description=f"Покупка: {package_names.get(package, package)} ({credits_to_add} баллов)",
                    category='purchase' if package == 'one_time' else 'subscription',
                    details={
                        'package_type': package,
                        'package_name': package_names.get(package, package),
                        'amount_paid': tx.get('amount', 0),
                        'currency': tx.get('currency', 'eur'),
                        'session_id': session_id,
                        'payment_method': 'demo' if PAYMENT_DEMO_MODE else 'stripe'
                    }
                )
            
            # Обновляем подписку если это не разовая покупка
            if package == 'monthly':
                await db.users.update_one({'id': user_id}, {'$set': {
                    'subscription_type': 'monthly',
                    'subscription_expires_at': datetime.utcnow() + timedelta(days=30)
                }})
            elif package == 'annual':
                await db.users.update_one({'id': user_id}, {'$set': {
                    'subscription_type': 'annual',
                    'subscription_expires_at': datetime.utcnow() + timedelta(days=365)
                }})
            elif package == 'master_consultation':
                # Для мастер консультации создаем персональную консультацию
                master_consultation = {
                    'id': str(uuid.uuid4()),
                    'title': 'Персональная консультация от мастера',
                    'description': 'Эксклюзивная персональная консультация от ведущего мастера нумерологии',
                    'assigned_user_id': user_id,
                    'cost_credits': 0,  # Уже оплачено
                    'is_active': True,
                    'video_url': 'https://example.com/master-consultation-video',  # Будет заменено на реальное видео
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                await db.personal_consultations.insert_one(master_consultation)
                
        await db.payment_transactions.update_one({'session_id': session_id}, {'$set': {'payment_status': 'paid', 'updated_at': datetime.utcnow()}})
        return {'status': 'complete', 'payment_status': 'paid', 'amount_total': int(tx['amount'] * 100), 'currency': 'eur', 'user_id': user_id}

    # Real stripe mode
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid' and tx['payment_status'] != 'paid':
            package = tx['package_type']
            user_id = tx.get('user_id')
            if user_id:
                # Добавляем баллы согласно пакету (используем $inc чтобы добавить к существующему балансу)
                credits_to_add = SUBSCRIPTION_CREDITS.get(package, 0)
                await db.users.update_one({'id': user_id}, {'$inc': {'credits_remaining': credits_to_add}})
                
                # Записываем транзакцию в историю
                if credits_to_add > 0:
                    package_names = {
                        'one_time': 'Разовая покупка',
                        'monthly': 'Месячная подписка',
                        'annual': 'Годовая подписка',
                        'master_consultation': 'Мастер консультация'
                    }
                    await record_credit_transaction(
                        user_id=user_id,
                        amount=credits_to_add,
                        description=f"Покупка: {package_names.get(package, package)} ({credits_to_add} баллов)",
                        category='purchase' if package == 'one_time' else 'subscription',
                        details={
                            'package_type': package,
                            'package_name': package_names.get(package, package),
                            'amount_paid': tx.get('amount', 0),
                            'currency': tx.get('currency', 'eur'),
                            'session_id': session_id,
                            'payment_method': 'stripe'
                        }
                    )
                
                # Обновляем подписку если это не разовая покупка
                if package == 'monthly':
                    await db.users.update_one({'id': user_id}, {'$set': {
                        'subscription_type': 'monthly',
                        'subscription_expires_at': datetime.utcnow() + timedelta(days=30)
                    }})
                elif package == 'annual':
                    await db.users.update_one({'id': user_id}, {'$set': {
                        'subscription_type': 'annual',
                        'subscription_expires_at': datetime.utcnow() + timedelta(days=365)
                    }})
                elif package == 'master_consultation':
                    # Для мастер консультации создаем персональную консультацию
                    master_consultation = {
                        'id': str(uuid.uuid4()),
                        'title': 'Персональная консультация от мастера',
                        'description': 'Эксклюзивная персональная консультация от ведущего мастера нумерологии',
                        'assigned_user_id': user_id,
                        'cost_credits': 0,  # Уже оплачено
                        'is_active': True,
                        'video_url': 'https://example.com/master-consultation-video',  # Будет заменено на реальное видео
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                    await db.personal_consultations.insert_one(master_consultation)
            await db.payment_transactions.update_one({'session_id': session_id}, {'$set': {'payment_status': checkout_status.payment_status, 'updated_at': datetime.utcnow()}})
        return {
            'status': checkout_status.status,
            'payment_status': checkout_status.payment_status,
            'amount_total': checkout_status.amount_total,
            'currency': checkout_status.currency
        }
    except Exception as e:
        logger.error(f'Stripe status check error: {e}')
        raise HTTPException(status_code=500, detail=f'Failed to check payment status: {e}')

@api_router.post('/webhook/stripe')
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(body, signature, webhook_secret)
        logger.info(f'Received Stripe webhook event: {event["type"]}')
        return {'received': True}
    except stripe.error.SignatureVerificationError as e:
        logger.error(f'Webhook signature verification failed: {e}')
        raise HTTPException(status_code=400, detail=f'Webhook signature verification failed: {e}')
    except Exception as e:
        logger.error(f'Webhook error: {e}')
        raise HTTPException(status_code=400, detail=f'Webhook error: {e}')

# ----------------- NUMEROLOGY -----------------
@api_router.post('/numerology/personal-numbers')
async def personal_numbers(birth_date: str = None, current_user: dict = Depends(get_current_user)):
    """Расчёт персональных чисел - 1 балл"""
    user_id = current_user['user_id']
    
    # Get user data for birth_date if not provided
    if not birth_date:
        user_dict = await db.users.find_one({'id': user_id})
        if not user_dict:
            raise HTTPException(status_code=404, detail='Пользователь не найден')
        user = User(**user_dict)
        birth_date = user.birth_date
    
    # Получаем стоимость из конфигурации
    config = await get_credits_deduction_config()
    cost = config.get('personal_numbers', CREDIT_COSTS.get('personal_numbers', 1))
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        cost, 
        'Расчёт персональных чисел', 
        'numerology',
        {'calculation_type': 'personal_numbers', 'birth_date': birth_date}
    )
    
    results = calculate_personal_numbers(birth_date)
    # augment with full_name_number from user profile (compute and persist if absent)
    user_doc = await db.users.find_one({'id': user_id})
    # Для числа имени используем ТОЛЬКО латинское имя + фамилию
    name_val = (user_doc or {}).get('name', '')  # ожидаем латиницу
    surname_val = (user_doc or {}).get('surname', '')
    fn_number = (user_doc or {}).get('full_name_number')
    if fn_number is None:
        fn_number = calculate_full_name_number(name_val, surname_val)
        await db.users.update_one({'id': user_id}, {'$set': {'full_name_number': fn_number}})
    results['full_name_number'] = fn_number
    calc = NumerologyCalculation(user_id=user_id, birth_date=birth_date, calculation_type='personal_numbers', results=results)
    await db.numerology_calculations.insert_one(calc.dict())
    return results

@api_router.get('/numerology/planetary-advice/{planet_number}', response_model=PlanetaryAdviceResponse)
async def planetary_advice_endpoint(
    planet_number: int,
    score: int = Query(..., ge=0, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Получение рекомендаций по усилению энергии планеты из базы данных"""
    if planet_number < 1 or planet_number > 9:
        raise HTTPException(status_code=422, detail='Номер планеты должен быть в диапазоне от 1 до 9')

    advice_doc = await db.planetary_advice.find_one({
        'planet_number': planet_number,
        'min_percent': {'$lte': score},
        'max_percent': {'$gte': score}
    })

    if not advice_doc:
        advice_doc = await db.planetary_advice.find_one(
            {'planet_number': planet_number},
            sort=[('min_percent', 1)]
        )

    advice_text = advice_doc.get('advice') if advice_doc else None

    return PlanetaryAdviceResponse(
        planet_number=planet_number,
        score=score,
        advice=advice_text or 'Совет пока не сформирован. Обратитесь к мастеру или попробуйте позже.',
        min_percent=advice_doc.get('min_percent') if advice_doc else None,
        max_percent=advice_doc.get('max_percent') if advice_doc else None
    )
@api_router.post('/numerology/pythagorean-square')
async def pythagorean_square(birth_date: str = None, current_user: dict = Depends(get_current_user)):
    """Расчёт квадрата Пифагора - 1 балл"""
    user_id = current_user['user_id']
    
    # Get user data for birth_date if not provided
    if not birth_date:
        user_dict = await db.users.find_one({'id': user_id})
        if not user_dict:
            raise HTTPException(status_code=404, detail='Пользователь не найден')
        user = User(**user_dict)
        birth_date = user.birth_date
    
    # Получаем стоимость из конфигурации
    config = await get_credits_deduction_config()
    cost = config.get('pythagorean_square', CREDIT_COSTS.get('pythagorean_square', 1))
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        cost, 
        'Расчёт квадрата Пифагора', 
        'numerology',
        {'calculation_type': 'pythagorean_square', 'birth_date': birth_date}
    )
    
    d, m, y = parse_birth_date(birth_date)
    results = create_pythagorean_square(d, m, y)
    
    # Добавляем личные числа (все сводим к однозначному, кроме правящего)
    soul_number = reduce_to_single_digit_always(d)
    mind_number = reduce_to_single_digit_always(m)
    destiny_number = reduce_to_single_digit_always(d + m + y)
    helping_mind_number = reduce_to_single_digit_always(m + y)
    wisdom_number = reduce_to_single_digit_always(d + m)
    # Правящее число = сумма всех цифр даты рождения (день + месяц + год) (может быть 11, 22)
    from numerology import calculate_ruling_number
    ruling_number = calculate_ruling_number(d, m, y)
    
    # Добавляем личные циклы (текущие) - все сводим к однозначному
    from datetime import datetime
    now = datetime.now()
    current_day = now.day
    current_month = now.month
    current_year = now.year
    current_hour = now.hour
    
    personal_year = reduce_to_single_digit_always(d + m + current_year)
    personal_month = reduce_to_single_digit_always(personal_year + current_month)
    personal_day = reduce_to_single_digit_always(personal_month + current_day)
    personal_hour = reduce_to_single_digit_always(personal_day + current_hour)
    challenge_number = abs(soul_number - destiny_number) if soul_number and destiny_number else 0
    
    results['soul_number'] = soul_number
    results['mind_number'] = mind_number
    results['destiny_number'] = destiny_number
    results['helping_mind_number'] = helping_mind_number
    results['wisdom_number'] = wisdom_number
    results['ruling_number'] = ruling_number
    results['personal_year'] = personal_year
    results['personal_month'] = personal_month
    results['personal_day'] = personal_day
    results['personal_hour'] = personal_hour
    results['challenge_number'] = challenge_number
    
    calc = NumerologyCalculation(user_id=user_id, birth_date=birth_date, calculation_type='pythagorean_square', results=results)
    await db.numerology_calculations.insert_one(calc.dict())
    return results

@api_router.post('/numerology/compatibility')
async def compatibility_endpoint(request_data: CompatibilityRequest, current_user: dict = Depends(get_current_user)):
    """Расчёт совместимости пары - 1 балл"""
    user_id = current_user['user_id']
    
    # Получаем стоимость из конфигурации
    config = await get_credits_deduction_config()
    cost = config.get('compatibility_pair', CREDIT_COSTS.get('compatibility_pair', 1))
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        cost, 
        'Расчёт совместимости пары', 
        'numerology',
        {
            'calculation_type': 'compatibility', 
            'person1_birth_date': request_data.person1_birth_date,
            'person2_birth_date': request_data.person2_birth_date
        }
    )
    
    results = calculate_compatibility(request_data.person1_birth_date, request_data.person2_birth_date)
    calc = NumerologyCalculation(user_id=user_id, birth_date=f"{request_data.person1_birth_date},{request_data.person2_birth_date}", calculation_type='compatibility', results=results)
    await db.numerology_calculations.insert_one(calc.dict())
    return results

@api_router.post('/numerology/name-numerology')
async def name_numerology(name_data: dict, current_user: dict = Depends(get_current_user)):
    """Нумерология имени - 1 балл"""
    user_id = current_user['user_id']
    
    name = name_data.get('name', '')
    surname = name_data.get('surname', '')
    full_name = f"{name} {surname}".strip()
    
    if not name:
        raise HTTPException(status_code=400, detail='Имя обязательно для расчёта')
    
    # Получаем стоимость из конфигурации
    config = await get_credits_deduction_config()
    cost = config.get('name_numerology', CREDIT_COSTS.get('name_numerology', 1))
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        cost, 
        'Нумерология имени', 
        'numerology',
        {'calculation_type': 'name_numerology', 'name': name, 'surname': surname}
    )
    
    # Рассчитываем нумерологию имени
    from numerology import calculate_name_numerology
    results = calculate_name_numerology(full_name)
    
    # Сохраняем в БД
    calc = NumerologyCalculation(
        user_id=user_id, 
        birth_date='', 
        calculation_type='name_numerology', 
        results={**results, 'name': name, 'surname': surname}
    )
    await db.numerology_calculations.insert_one(calc.dict())
    
    return results

@api_router.post('/numerology/group-compatibility')
async def group_compatibility_numerology(group_data: GroupCompatibilityRequest, current_user: dict = Depends(get_current_user)):
    """Групповая совместимость (5 человек) - 5 баллов"""
    user_id = current_user['user_id']
    
    if len(group_data.people) > 5:
        raise HTTPException(status_code=400, detail='Максимум 5 человек для группового анализа')
    
    # Получаем стоимость из конфигурации
    config = await get_credits_deduction_config()
    cost = config.get('group_compatibility', CREDIT_COSTS.get('group_compatibility', 5))
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        cost, 
        f'Групповая совместимость ({len(group_data.people)} чел.)', 
        'numerology',
        {'calculation_type': 'group_compatibility', 'people_count': len(group_data.people)}
    )
    
    # Рассчитываем групповую совместимость
    try:
        from numerology import calculate_group_compatibility
        # Конвертируем данные людей в нужный формат
        people_data = [{"name": person.name, "birth_date": person.birth_date} for person in group_data.people]
        results = calculate_group_compatibility(group_data.main_person_birth_date, people_data)
        
        # Сохраняем в БД
        calc = NumerologyCalculation(
            user_id=user_id, 
            birth_date=group_data.main_person_birth_date, 
            calculation_type='group_compatibility', 
            results={**results, 'main_person_birth_date': group_data.main_person_birth_date, 'people': people_data}
        )
        await db.numerology_calculations.insert_one(calc.dict())
        
        return results
    except Exception as e:
        # Возвращаем баллы при ошибке
        config = await get_credits_deduction_config()
        cost = config.get('group_compatibility', CREDIT_COSTS.get('group_compatibility', 5))
        await record_credit_transaction(user_id, cost, 'Возврат за ошибку группового анализа', 'refund')
        await db.users.update_one({'id': user_id}, {'$inc': {'credits_remaining': cost}})
        raise HTTPException(status_code=400, detail=f'Ошибка расчета: {str(e)}')

@api_router.post('/numerology/address-numerology')
async def address_numerology(address_data: dict, current_user: dict = Depends(get_current_user)):
    """Нумерология адреса - 1 балл"""
    user_id = current_user['user_id']
    
    street = address_data.get('street', '')
    house_number = address_data.get('house_number', '')
    apartment_number = address_data.get('apartment_number', '')
    postal_code = address_data.get('postal_code', '')
    
    if not house_number:
        raise HTTPException(status_code=400, detail='Номер дома обязателен для расчёта')
    
    # Получаем стоимость из конфигурации
    config = await get_credits_deduction_config()
    cost = config.get('address_numerology', CREDIT_COSTS.get('address_numerology', 1))
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        cost, 
        'Нумерология адреса', 
        'numerology',
        {'calculation_type': 'address_numerology', 'street': street, 'house_number': house_number, 'apartment_number': apartment_number}
    )
    
    # Рассчитываем нумерологию адреса
    from numerology import calculate_address_numerology
    results = calculate_address_numerology(street, house_number, apartment_number, postal_code)
    
    # Сохраняем в БД
    calc = NumerologyCalculation(
        user_id=user_id, 
        birth_date='', 
        calculation_type='address_numerology', 
        results={**results, 'street': street, 'house_number': house_number, 'apartment_number': apartment_number, 'postal_code': postal_code}
    )
    await db.numerology_calculations.insert_one(calc.dict())
    
    return results

@api_router.post('/numerology/car-numerology')
async def car_numerology(car_data: dict, current_user: dict = Depends(get_current_user)):
    """Нумерология автомобиля - 1 балл"""
    user_id = current_user['user_id']
    
    car_number = car_data.get('car_number', '')
    
    if not car_number:
        raise HTTPException(status_code=400, detail='Номер автомобиля обязателен для расчёта')
    
    # Получаем стоимость из конфигурации
    config = await get_credits_deduction_config()
    cost = config.get('car_numerology', CREDIT_COSTS.get('car_numerology', 1))
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        cost, 
        'Нумерология автомобиля', 
        'numerology',
        {'calculation_type': 'car_numerology', 'car_number': car_number}
    )
    
    # Рассчитываем нумерологию автомобиля
    from numerology import calculate_car_number_numerology
    results = calculate_car_number_numerology(car_number)
    
    # Сохраняем в БД
    calc = NumerologyCalculation(
        user_id=user_id, 
        birth_date='', 
        calculation_type='car_numerology', 
        results=results
    )
    await db.numerology_calculations.insert_one(calc.dict())
    
    return results

@api_router.post('/vedic-time/planetary-route/save')
async def save_planetary_route(route_data: dict, current_user: dict = Depends(get_current_user)):
    """Сохранение планетарного маршрута в БД"""
    user_id = current_user['user_id']
    
    # Сохраняем планетарный маршрут
    calc = NumerologyCalculation(
        user_id=user_id, 
        birth_date=route_data.get('date', ''), 
        calculation_type='planetary_route', 
        results=route_data
    )
    await db.numerology_calculations.insert_one(calc.dict())
    
    return {'status': 'saved', 'message': 'Планетарный маршрут сохранён'}

@api_router.get('/numerology/saved-calculations')
async def get_saved_calculations(
    calculation_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Получение сохранённых расчётов пользователя"""
    user_id = current_user['user_id']
    
    query = {'user_id': user_id}
    if calculation_type:
        query['calculation_type'] = calculation_type
    
    # Получаем последние расчёты каждого типа
    calculations = await db.numerology_calculations.find(query).sort('created_at', -1).to_list(length=100)
    
    # Группируем по типу и берём последний для каждого типа
    grouped = {}
    for calc in calculations:
        calc_type = calc.get('calculation_type')
        if calc_type not in grouped:
            grouped[calc_type] = {
                'id': calc.get('id'),
                'calculation_type': calc_type,
                'results': calc.get('results', {}),
                'created_at': calc.get('created_at').isoformat() if calc.get('created_at') else None
            }
    
    return grouped

@api_router.get('/quiz/personality-test')
async def personality_test(test_data: dict, current_user: dict = Depends(get_current_user)):
    """Тест личности - 1 балл"""
    user_id = current_user['user_id']
    
    # Получаем стоимость из конфигурации
    config = await get_credits_deduction_config()
    cost = config.get('personality_test', CREDIT_COSTS.get('personality_test', 1))
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        cost, 
        'Тест личности', 
        'quiz',
        {'calculation_type': 'personality_test'}
    )
    
    # Здесь должна быть логика обработки теста личности
    # Пока возвращаем заглушку
    results = {
        'personality_type': 'Analytical',
        'score': 85,
        'description': 'Вы аналитический тип личности'
    }
    
    return results

@api_router.get('/vedic-time/daily-schedule')
async def vedic_daily_schedule(vedic_request: VedicTimeRequest = Depends(), current_user: dict = Depends(get_current_user)):
    """Ведическое дневное расписание - 1 балл"""
    user_id = current_user['user_id']
    
    # Получаем город из запроса или профиля пользователя
    city = vedic_request.city
    if not city:
        user_dict = await db.users.find_one({'id': user_id})
        if user_dict:
            city = user_dict.get('city')
        
    if not city:
        raise HTTPException(status_code=422, detail="Город не указан. Укажите город в запросе или обновите профиль пользователя.")
    
    # Получаем стоимость из конфигурации
    config = await get_credits_deduction_config()
    cost = config.get('vedic_daily', CREDIT_COSTS.get('vedic_daily', 1))
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        cost, 
        'Ведическое время на день', 
        'vedic',
        {'calculation_type': 'vedic_daily', 'city': city, 'date': vedic_request.date}
    )
    
    # Parse date string to datetime object
    if vedic_request.date:
        try:
            date_obj = datetime.strptime(vedic_request.date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        # Используем UTC время с timezone для корректной конвертации в локальное время города
        date_obj = datetime.now(pytz.UTC)

    schedule = get_vedic_day_schedule(city=city, date=date_obj)
    if 'error' in schedule:
        # Возвращаем балл при ошибке
        config = await get_credits_deduction_config()
        cost = config.get('vedic_daily', CREDIT_COSTS.get('vedic_daily', 1))
        await record_credit_transaction(user_id, cost, 'Возврат за ошибку ведического времени', 'refund')
        await db.users.update_one({'id': user_id}, {'$inc': {'credits_remaining': cost}})
        raise HTTPException(status_code=400, detail=schedule['error'])
    
    # Add planetary energy calculation for the day
    try:
        user_dict = await db.users.find_one({'id': user_id})
        if user_dict and user_dict.get('birth_date'):
            user = User(**user_dict)
            
            # Prepare user data for enhanced calculation
            user_numbers = None
            pythagorean_square_data = None
            fractal_behavior = None
            problem_numbers = None
            name_numbers = None
            weekday_energy = None
            janma_ank_value = None
            
            try:
                day, month, year = parse_birth_date(user.birth_date)
                
                # Get personal numbers
                personal_numbers = calculate_personal_numbers(user.birth_date)
                user_numbers = {
                    'soul_number': personal_numbers.get('soul_number'),
                    'mind_number': personal_numbers.get('mind_number'),
                    'destiny_number': personal_numbers.get('destiny_number'),
                    'wisdom_number': personal_numbers.get('wisdom_number'),
                    'ruling_number': personal_numbers.get('ruling_number'),
                    'personal_day': personal_numbers.get('personal_day')
                }
                
                # Calculate Pythagorean Square
                pythagorean_square_data = create_pythagorean_square(day, month, year)
                
                # Calculate Janma Ank
                from vedic_numerology import calculate_janma_ank, calculate_bhagya_ank, calculate_enhanced_daily_planetary_energy
                janma_ank_value = calculate_janma_ank(day, month, year)
                total_before_reduction = day + month + year
                if total_before_reduction == 22:
                    janma_ank_value = 22
                
                destiny_number = calculate_bhagya_ank(day, month, year)
                
                # Calculate fractal behavior
                day_reduced = reduce_to_single_digit(day)
                month_reduced = reduce_to_single_digit(month)
                year_reduced = reduce_to_single_digit(year)
                year_sum = reduce_to_single_digit(day + month + year)
                fractal_behavior = [day_reduced, month_reduced, year_reduced, year_sum]
                
                # Calculate problem numbers
                soul_num = user_numbers.get('soul_number', 1)
                mind_num = user_numbers.get('mind_number', 1)
                destiny_num = user_numbers.get('destiny_number', 1)
                problem1 = reduce_to_single_digit(abs(soul_num - mind_num))
                problem2 = reduce_to_single_digit(abs(soul_num - year_reduced))
                problem3 = reduce_to_single_digit(abs(problem1 - problem2))
                problem4 = reduce_to_single_digit(abs(mind_num - year_reduced))
                problem_numbers = [problem1, problem2, problem3, problem4]
                
                # Get name numbers if available
                if hasattr(user, 'full_name') and user.full_name:
                    from numerology import calculate_name_numerology
                    try:
                        name_data = calculate_name_numerology(user.full_name)
                        name_numbers = {
                            'first_name_number': name_data.get('first_name_number'),
                            'last_name_number': name_data.get('last_name_number'),
                            'total_name_number': name_data.get('total_name_number'),
                            'full_name_number': name_data.get('total_name_number')
                        }
                    except:
                        pass
                
                # Calculate weekday energy
                try:
                    from numerology import calculate_planetary_strength
                    planetary_strength_data = calculate_planetary_strength(day, month, year)
                    strength_dict = planetary_strength_data.get('strength', {})
                    planet_name_to_key = {
                        'Солнце': 'surya', 'Луна': 'chandra', 'Марс': 'mangal',
                        'Меркурий': 'budha', 'Юпитер': 'guru', 'Венера': 'shukra', 'Сатурн': 'shani'
                    }
                    weekday_energy = {}
                    for planet_name, energy_value in strength_dict.items():
                        planet_key = planet_name_to_key.get(planet_name)
                        if planet_key:
                            weekday_energy[planet_key] = float(energy_value)
                except:
                    pass
                
                # Get modifiers config
                modifiers_config = await get_planetary_energy_modifiers_config()
                
                # Calculate planetary energy for the day
                planetary_energies = calculate_enhanced_daily_planetary_energy(
                    destiny_number=destiny_number,
                    date=date_obj,
                    birth_date=user.birth_date,
                    user_numbers=user_numbers,
                    pythagorean_square=pythagorean_square_data,
                    fractal_behavior=fractal_behavior,
                    problem_numbers=problem_numbers,
                    name_numbers=name_numbers,
                    weekday_energy=weekday_energy,
                    janma_ank=janma_ank_value,
                    city=city,
                    modifiers_config=modifiers_config
                )
                
                # Add planetary energies to schedule
                schedule['planetary_energies'] = planetary_energies
                schedule['total_energy'] = sum(planetary_energies.values())
                
            except Exception as e:
                print(f"Error calculating planetary energy for daily schedule: {e}")
    except Exception as e:
        print(f"Error adding planetary energy to daily schedule: {e}")
    
    return schedule

async def get_scoring_config_cached():
    """Получить конфигурацию системы баллов (с кешированием)"""
    config = await db.scoring_config.find_one({'is_active': True})
    
    if not config:
        # Создаём дефолтную конфигурацию
        from models import ScoringConfig
        default_config = ScoringConfig()
        await db.scoring_config.insert_one(default_config.dict())
        return default_config.dict()
    
    return config

async def get_user_numerology_data(user_id: str) -> Dict[str, Any]:
    """Получить нумерологические данные пользователя"""
    user = await db.users.find_one({'id': user_id})
    if not user:
        return {}
    
    birth_date = user.get('birth_date', '')
    if not birth_date:
        return {}
    
    # Вычисляем персональные числа
    try:
        numbers = calculate_personal_numbers(birth_date)
        return {
            'soul_number': numbers.get('soul_number', 0),
            'destiny_number': numbers.get('destiny_number', 0),
            'mind_number': numbers.get('mind_number', 0),
            'birth_date': birth_date,
            'planet_counts': numbers.get('planetary_strength', {}).get('strength', {})
        }
    except Exception as e:
        logger.error(f"Error calculating numerology data: {e}")
        return {}

async def calculate_hourly_planetary_energy(hours: List[Dict[str, Any]], user_data: Dict[str, Any], db) -> List[Dict[str, Any]]:
    """Вычислить почасовую энергию планет с детальными советами"""
    if not hours:
        return []
    
    result = []
    for hour in hours:
        planet = hour.get('planet', '')
        result.append({
            **hour,
            'energy_level': 50,  # Базовая энергия
            'advice': f'Период планеты {planet}'
        })
    return result

def find_best_hours_for_activities(hours: List[Dict[str, Any]], user_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Найти лучшие часы для разных активностей"""
    return {
        'work': hours[:3] if len(hours) >= 3 else hours,
        'communication': hours[3:6] if len(hours) >= 6 else [],
        'rest': hours[6:9] if len(hours) >= 9 else [],
        'creativity': hours[9:12] if len(hours) >= 12 else []
    }

def analyze_day_compatibility(date_obj: datetime, user_data: Dict[str, Any], schedule: Dict[str, Any], scoring_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Анализирует совместимость дня с личными числами пользователя
    Возвращает оценку дня, сильные/слабые стороны и рекомендации
    
    Args:
        date_obj: Дата для анализа
        user_data: Данные пользователя
        schedule: Расписание дня
        scoring_config: Конфигурация системы баллов (опционально)
    """
    # Если конфигурация не передана, используем дефолтные значения
    if not scoring_config:
        scoring_config = {
            'base_score': 20,
            'personal_energy_high': 10,
            'personal_energy_low': -10,
            'personal_energy_zero': -15,
            'soul_resonance': 1,
            'soul_friendship': 5,
            'soul_hostility': -10,
            'mind_resonance': 1,
            'mind_friendship': 6,
            'mind_hostility': -20,
            'destiny_resonance': 1,
            'destiny_hostility': -30,
            'planet_strength_high': 12,
            'planet_strength_medium': 1,
            'planet_strength_low': -10,
            'birthday_bonus': 15,
            'planet_friendship': 8,
            'planet_hostility': -8,
            'name_resonance': 5,
            'name_conflict': -5,
            'rahu_kaal_penalty': -5,
            'favorable_period_bonus': 5,
            'global_harmony_bonus': 10,
            'global_harmony_penalty': -10,
            'day_number_bonus': 5
        }
    # Дружественность планет (ведическая нумерология)
    planet_relationships = {
        'Surya': {'friends': ['Chandra', 'Mangal', 'Guru'], 'enemies': ['Shukra', 'Shani'], 'neutral': ['Budh']},
        'Chandra': {'friends': ['Surya', 'Budh'], 'enemies': [], 'neutral': ['Mangal', 'Guru', 'Shukra', 'Shani']},
        'Mangal': {'friends': ['Surya', 'Chandra', 'Guru'], 'enemies': ['Budh'], 'neutral': ['Shukra', 'Shani']},
        'Budh': {'friends': ['Surya', 'Shukra'], 'enemies': ['Chandra'], 'neutral': ['Mangal', 'Guru', 'Shani']},
        'Guru': {'friends': ['Surya', 'Chandra', 'Mangal'], 'enemies': ['Budh', 'Shukra'], 'neutral': ['Shani']},
        'Shukra': {'friends': ['Budh', 'Shani'], 'enemies': ['Surya', 'Chandra'], 'neutral': ['Mangal', 'Guru']},
        'Shani': {'friends': ['Budh', 'Shukra', 'Rahu'], 'enemies': ['Surya', 'Chandra', 'Mangal'], 'neutral': ['Guru']},
        'Rahu': {'friends': ['Budh', 'Shukra', 'Shani'], 'enemies': ['Surya', 'Chandra', 'Mangal'], 'neutral': ['Guru']},
        'Ketu': {'friends': ['Mangal', 'Guru'], 'enemies': ['Surya', 'Chandra', 'Budh'], 'neutral': ['Shukra', 'Shani']}
    }
    
    # Получаем правящую планету дня
    ruling_planet = schedule.get('weekday', {}).get('ruling_planet', 'Surya')
    
    # Получаем личные числа пользователя
    soul_number = user_data.get('soul_number', 1)
    mind_number = user_data.get('mind_number', 1)
    destiny_number = user_data.get('destiny_number', 1)
    ruling_number = user_data.get('ruling_number', 1)
    
    # Получаем силу планет из квадрата Пифагора
    pythagorean_square = user_data.get('pythagorean_square', {})
    planet_counts = pythagorean_square.get('planet_counts', {})
    
    # Получаем день недели рождения пользователя
    birth_date_str = user_data.get('birth_date', '')
    is_birth_weekday = False
    personal_weekday_energy = {}  # Личная энергия по дням недели (DDMM × YYYY)
    
    if birth_date_str:
        try:
            birth_date = datetime.strptime(birth_date_str, '%d.%m.%Y')
            is_birth_weekday = birth_date.weekday() == date_obj.weekday()
            
            # Рассчитываем личную энергию по дням недели (DDMM × YYYY)
            from numerology import calculate_planetary_strength
            day = birth_date.day
            month = birth_date.month
            year = birth_date.year
            
            planetary_strength_data = calculate_planetary_strength(day, month, year)
            personal_weekday_energy = planetary_strength_data.get('strength', {})
            
            # Конвертируем русские названия в ведические
            russian_to_vedic = {
                'Солнце': 'Surya',
                'Луна': 'Chandra',
                'Марс': 'Mangal',
                'Меркурий': 'Budh',
                'Юпитер': 'Guru',
                'Венера': 'Shukra',
                'Сатурн': 'Shani'
            }
            personal_weekday_energy = {
                russian_to_vedic.get(k, k): v 
                for k, v in personal_weekday_energy.items()
            }
        except Exception as e:
            print(f"⚠️ Ошибка расчёта личной энергии: {e}")
            pass
    
    # Получаем день правящей планеты
    is_planet_day = schedule.get('weekday', {}).get('ruling_planet') == ruling_planet
    
    # Получаем конфигурацию системы оценки
    config = get_scoring_config_sync()
    
    # Утилита для безопасного извлечения числовых значений из конфигурации
    def score_value(key: str, default: int) -> int:
        value = config.get(key, default)
        if isinstance(value, (int, float)):
            return int(value)
        try:
            return int(str(value))
        except Exception:
            return default
    
    # 1. БАЗОВЫЙ СЧЁТ - из конфигурации
    base_score = score_value('base_score', 20)
    compatibility_score = base_score
    
    # Списки для позитивных аспектов и вызовов
    positive_aspects = []
    challenges = []
    
    # Маппинг планет на числа
    planet_to_number = {
        'Surya': 1, 'Chandra': 2, 'Guru': 3, 'Rahu': 4,
        'Budh': 5, 'Shukra': 6, 'Ketu': 7, 'Shani': 8, 'Mangal': 9
    }
    number_to_planet = {v: k for k, v in planet_to_number.items()}
    
    ruling_planet_number = planet_to_number.get(ruling_planet, 1)
    
    # 🔥 КРИТИЧЕСКАЯ ПРОВЕРКА: Личная энергия по дням недели (DDMM × YYYY)
    # Если энергия планеты дня = 0, это СЛОЖНЫЙ день!
    planet_weekday_energy = personal_weekday_energy.get(ruling_planet, -1)
    
    if planet_weekday_energy == 0:
        # Это КРИТИЧЕСКИ СЛОЖНЫЙ день - энергия планеты отсутствует!
        zero_penalty = score_value('personal_energy_zero', -15)
        compatibility_score += zero_penalty
        challenges.append({
            'type': 'zero_weekday_energy',
            'icon': '🚨',
            'title': 'КРИТИЧЕСКИЙ ДЕНЬ: НУЛЕВАЯ ЭНЕРГИЯ!',
            'short_text': f"У вас НУЛЕВАЯ личная энергия {ruling_planet} в этот день недели! Это один из самых сложных дней для вас.",
            'detailed_info': f"По расчёту DDMM × YYYY ваша личная энергия планеты {ruling_planet} в этот день недели равна 0. Это означает полное отсутствие резонанса с энергией дня. Ваши действия будут требовать в несколько раз больше усилий, а результаты могут быть минимальными.",
            'advice': [
                "⚠️ ИЗБЕГАЙТЕ важных начинаний и решений в этот день!",
                "Это день для отдыха, восстановления и рефлексии",
                "Не планируйте встречи, переговоры или подписание документов",
                "Используйте день для внутренней работы и медитации",
                f"Работайте с энергией {ruling_planet} через мантры для компенсации",
                "Носите камни и цвета, усиливающие энергию этой планеты",
                "Проводите больше времени в уединении и покое"
            ],
            'planet_info': f"Ваша личная энергия {ruling_planet} = 0 (расчёт по дате рождения)",
            'solution': f"Перенесите все важные дела на дни с высокой энергией других планет. Сегодня - день минимальной активности и максимальной осторожности.",
            'score_impact': zero_penalty
        })
        print(f"🚨 КРИТИЧЕСКИЙ ДЕНЬ: Энергия {ruling_planet} = 0 для пользователя!")
    elif planet_weekday_energy > 0 and planet_weekday_energy <= 3:
        # Низкая энергия - день сложный, но не критический
        low_penalty = score_value('personal_energy_low', -10)
        compatibility_score += low_penalty
        challenges.append({
            'type': 'low_weekday_energy',
            'icon': '⚡',
            'title': 'Низкая личная энергия дня',
            'short_text': f"Ваша личная энергия {ruling_planet} сегодня низкая ({planet_weekday_energy}/9). День потребует дополнительных усилий.",
            'detailed_info': f"По расчёту личной энергии (DDMM × YYYY) ваша энергия планеты {ruling_planet} в этот день недели составляет всего {planet_weekday_energy} из 9. Это означает, что вам потребуется больше усилий для достижения результатов.",
            'advice': [
                "Планируйте меньше дел, чем обычно",
                "Делайте больше перерывов для восстановления",
                "Избегайте энергозатратных задач",
                f"Используйте мантры {ruling_planet} для поддержки энергии",
                "Отдавайте предпочтение рутинным делам"
            ],
            'planet_info': f"Личная энергия {ruling_planet} = {planet_weekday_energy}/9",
            'solution': "Работайте в планетарные часы других, более сильных для вас планет",
            'score_impact': low_penalty
        })
    elif planet_weekday_energy >= 7:
        # Высокая энергия - день благоприятный!
        high_bonus = score_value('personal_energy_high', 10)
        compatibility_score += high_bonus
        positive_aspects.append({
            'type': 'high_weekday_energy',
            'icon': '⚡',
            'title': 'ВЫСОКАЯ личная энергия дня!',
            'short_text': f"Ваша личная энергия {ruling_planet} сегодня на пике ({planet_weekday_energy}/9)! Это ВАШЕ время!",
            'detailed_info': f"По расчёту личной энергии (DDMM × YYYY) ваша энергия планеты {ruling_planet} в этот день недели составляет {planet_weekday_energy} из 9. Это один из самых благоприятных дней для вас!",
            'advice': [
                "Планируйте самые важные дела на этот день!",
                "Начинайте новые проекты и инициативы",
                "Проводите важные встречи и переговоры",
                "Принимайте стратегические решения",
                f"Энергия {ruling_planet} полностью поддерживает вас"
            ],
            'planet_info': f"Личная энергия {ruling_planet} = {planet_weekday_energy}/9 - МАКСИМУМ!",
            'score_impact': high_bonus
        })
    
    # 2. РЕЗОНАНС ЧИСЛА ДУШИ (+1/+5/-10)
    soul_planet = number_to_planet.get(soul_number)
    if soul_number == ruling_planet_number:
        delta = score_value('soul_resonance', 1)
        compatibility_score += delta
        positive_aspects.append({
            'type': 'soul_resonance',
            'icon': '🌟',
            'title': 'ИДЕАЛЬНЫЙ РЕЗОНАНС ДУШИ!',
            'short_text': f"Ваше число души ({soul_number}) полностью резонирует с {ruling_planet}. Это ВАШЕ время максимальной силы!",
            'detailed_info': f"Число души {soul_number} соответствует планете {soul_planet}, которая сегодня управляет днём. Это означает полное совпадение ваших внутренних желаний с энергией дня.",
            'advice': [
                "Сегодня - идеальный день для самовыражения и реализации своих истинных желаний",
                "Действуйте смело и уверенно - энергия дня полностью поддерживает вас",
                "Это время максимальной силы для начинаний, связанных с вашей истинной природой",
                f"Медитируйте на энергию {ruling_planet} для усиления эффекта"
            ],
            'planet_info': f"{ruling_planet} управляет вашей душой и днём одновременно, создавая мощный резонанс",
            'score_impact': delta
        })
    elif soul_planet and ruling_planet in planet_relationships.get(soul_planet, {}).get('friends', []):
        delta = score_value('soul_friendship', 5)
        compatibility_score += delta
        positive_aspects.append({
            'type': 'soul_harmony',
            'icon': '✨',
            'title': 'Гармония числа души',
            'short_text': f"Ваше число души ({soul_number}) гармонирует с энергией {ruling_planet}. Хороший день для самовыражения.",
            'detailed_info': f"Ваша планета души {soul_planet} дружественна к {ruling_planet}. Это создаёт благоприятную атмосферу для реализации ваших желаний.",
            'advice': [
                "Используйте день для творчества и самовыражения",
                "Ваши истинные желания найдут поддержку",
                f"Планеты {soul_planet} и {ruling_planet} работают в гармонии"
            ],
            'planet_info': f"{soul_planet} (ваша душа) дружит с {ruling_planet} (планета дня)",
            'score_impact': delta
        })
    elif soul_planet and ruling_planet in planet_relationships.get(soul_planet, {}).get('enemies', []):
        delta = score_value('soul_hostility', -10)
        compatibility_score += delta
        challenges.append({
            'type': 'soul_conflict',
            'icon': '⚠️',
            'title': 'КОНФЛИКТ ДУШИ!',
            'short_text': f"Число души ({soul_number}) конфликтует с {ruling_planet}. День может быть эмоционально сложным.",
            'detailed_info': f"Ваша планета души {soul_planet} враждебна к {ruling_planet}. Это создаёт внутренний конфликт между вашими истинными желаниями и энергией дня.",
            'advice': [
                "Избегайте важных эмоциональных решений",
                "Не форсируйте события, действуйте осторожно",
                "Уделите время самоанализу и медитации",
                f"Работайте с энергией {soul_planet} для гармонизации",
                "Отложите важные начинания на более благоприятный день"
            ],
            'planet_info': f"Враждебные отношения: {soul_planet} (душа) ⚔ {ruling_planet} (день)",
            'solution': f"Используйте планетарные часы {soul_planet} для важных дел",
            'score_impact': delta
        })
    
    # 3. РЕЗОНАНС ЧИСЛА УМА (+1/+6/-20)
    mind_planet = number_to_planet.get(mind_number)
    if mind_number == ruling_planet_number:
        delta = score_value('mind_resonance', 1)
        compatibility_score += delta
        positive_aspects.append({
            'type': 'mind_resonance',
            'icon': '🧠',
            'title': 'РЕЗОНАНС УМА!',
            'short_text': f"Ваше число ума ({mind_number}) резонирует с {ruling_planet}. Ваш ум работает на пике! Идеальное время для интеллектуальной работы и принятия решений.",
            'detailed_info': f"Число ума {mind_number} управляется планетой {mind_planet}, которая сегодня правит днём. Ваше мышление, логика и способность принимать решения находятся на максимуме.",
            'advice': [
                "Идеальный день для важных решений и стратегического планирования",
                "Ваш интеллект работает на пике - используйте это для сложных задач",
                "Отличное время для обучения, анализа и работы с информацией",
                "Доверяйте своей интуиции и логике - они в полной гармонии"
            ],
            'planet_info': f"{ruling_planet} усиливает ваши ментальные способности в {(12/80)*100:.0f}% от максимума"
        })
    elif mind_planet and ruling_planet in planet_relationships.get(mind_planet, {}).get('friends', []):
        delta = score_value('mind_friendship', 6)
        compatibility_score += delta
        positive_aspects.append({
            'type': 'mind_harmony',
            'icon': '💭',
            'title': 'Гармония ума',
            'short_text': f"Число ума ({mind_number}) в гармонии с {ruling_planet}. Хороший день для планирования и анализа.",
            'detailed_info': f"Планета вашего ума {mind_planet} дружественна к {ruling_planet}. Ваше мышление поддерживается энергией дня.",
            'advice': [
                "Хороший день для планирования и организации",
                "Ваши мысли ясны и структурированы",
                f"Используйте гармонию {mind_planet} и {ruling_planet} для продуктивной работы"
            ],
            'planet_info': f"{mind_planet} (ваш ум) дружит с {ruling_planet} (планета дня)"
        })
    elif mind_planet and ruling_planet in planet_relationships.get(mind_planet, {}).get('enemies', []):
        delta = score_value('mind_hostility', -20)
        compatibility_score += delta
        challenges.append({
            'type': 'mind_conflict',
            'icon': '🧠',
            'title': 'КОНФЛИКТ УМА!',
            'short_text': f"Число ума ({mind_number}) конфликтует с {ruling_planet}. Будьте осторожны в принятии решений.",
            'detailed_info': f"Планета вашего ума {mind_planet} враждебна к {ruling_planet}. Это создаёт ментальное напряжение, затрудняет принятие решений и может вызывать сомнения.",
            'advice': [
                "НЕ принимайте важных решений сегодня - отложите их на более благоприятный день",
                "Перепроверяйте всю информацию дважды, не доверяйте первому впечатлению",
                "Избегайте споров и конфликтов - ваша логика может подвести",
                "Используйте письменные заметки для важных мыслей",
                f"Медитируйте на планету {mind_planet} для успокоения ума",
                "Отдыхайте больше, не перегружайте мозг"
            ],
            'planet_info': f"ВРАЖДЕБНОСТЬ: {mind_planet} (ваш ум) ⚔️ {ruling_planet} (день) = -5 баллов",
            'solution': f"Перенесите важные решения на день {mind_planet} или используйте её планетарные часы"
        })
    
    # 4. РЕЗОНАНС ЧИСЛА СУДЬБЫ (+1/-30)
    destiny_planet = number_to_planet.get(destiny_number)
    if destiny_number == ruling_planet_number:
        delta = score_value('destiny_resonance', 1)
        compatibility_score += delta
        positive_aspects.append({
            'type': 'destiny_resonance',
            'icon': '🎯',
            'title': 'РЕЗОНАНС СУДЬБЫ!',
            'short_text': f"Число судьбы ({destiny_number}) совпадает с {ruling_planet}. Ваш жизненный путь поддерживается энергией дня!",
            'detailed_info': f"Число судьбы {destiny_number} управляется планетой {destiny_planet}. Когда эта планета правит днём, ваш жизненный путь получает мощную поддержку от Вселенной.",
            'advice': [
                "Идеальный день для движения к вашим долгосрочным целям",
                "События дня будут способствовать вашему предназначению",
                "Обращайте внимание на знаки и синхронности",
                "Это время, когда судьба работает в вашу пользу"
            ],
            'planet_info': f"{ruling_planet} направляет вас по пути вашего предназначения"
        })
    elif destiny_planet and ruling_planet in planet_relationships.get(destiny_planet, {}).get('enemies', []):
        delta = score_value('destiny_hostility', -30)
        compatibility_score += delta
        challenges.append({
            'type': 'destiny_conflict',
            'icon': '🎯',
            'title': 'КОНФЛИКТ СУДЬБЫ!',
            'short_text': f"Число судьбы ({destiny_number}) конфликтует с {ruling_planet}. Препятствия на пути к целям.",
            'detailed_info': f"Планета вашей судьбы {destiny_planet} враждебна к {ruling_planet}. Это создаёт препятствия на пути к вашим долгосрочным целям.",
            'advice': [
                "Не форсируйте движение к долгосрочным целям",
                "Сосредоточьтесь на текущих задачах",
                "Отложите важные стратегические решения",
                f"Работайте с энергией {destiny_planet} для гармонизации"
            ],
            'planet_info': f"Враждебные отношения: {destiny_planet} (судьба) ⚔ {ruling_planet} (день)",
            'solution': f"Используйте планетарные часы {destiny_planet} для важных дел"
        })
    
    # 5. ЕДИНСТВО ДУШИ И УМА (+10)
    if soul_number == mind_number and soul_number == ruling_planet_number:
        compatibility_score += 10
        positive_aspects.append({
            'type': 'unity',
            'icon': '💫',
            'title': 'ЕДИНСТВО ДУШИ И УМА!',
            'short_text': f"Ваша душа и ум в полной гармонии с {ruling_planet}. Ваши желания и мысли совпадают, что даёт огромную силу для реализации!",
            'detailed_info': f"Редкое состояние полного единства: ваше число души ({soul_number}) и число ума ({mind_number}) совпадают и резонируют с планетой дня {ruling_planet}. Это создаёт мощнейший синергетический эффект.",
            'advice': [
                "МАКСИМАЛЬНАЯ СИЛА! Используйте этот день для самых важных целей",
                "Ваши желания и мысли едины - это даёт невероятную силу проявления",
                "Всё, что вы задумаете сегодня, имеет высокий шанс реализации",
                "Это ваш день абсолютной силы - действуйте смело!",
                "Медитируйте на единство души, ума и энергии дня"
            ],
            'planet_info': f"Тройной резонанс: Душа + Ум + {ruling_planet} = Максимальная сила!"
        })
    
    # 6. СИЛА ПЛАНЕТЫ В КАРТЕ (+12/+1/-10)
    planet_count = planet_counts.get(ruling_planet, 0)
    if planet_count >= 4:
        delta = score_value('planet_strength_high', 12)
        compatibility_score += delta
        positive_aspects.append({
            'type': 'planet_strength_high',
            'icon': '⚖️',
            'title': 'МОЩНАЯ ЭНЕРГИЯ ПЛАНЕТЫ!',
            'short_text': f"У вас очень сильная энергия {ruling_planet} ({planet_count} цифр в карте). Этот день усиливает ваши естественные способности вдвойне!",
            'detailed_info': f"В вашем квадрате Пифагора {planet_count} цифр, связанных с {ruling_planet}. Это означает, что энергия этой планеты является вашей естественной силой. Когда она правит днём, происходит двойное усиление.",
            'advice': [
                f"Ваша природная сила {ruling_planet} сегодня на максимуме!",
                "Используйте день для дел, требующих ваших сильных качеств",
                f"С {planet_count} цифрами в карте, вы - мастер энергии {ruling_planet}",
                "Это ваш день абсолютного преимущества",
                "Помогайте другим, делясь своей силой"
            ],
            'planet_info': f"Сила {ruling_planet} в вашей карте: {planet_count}/9 = {(planet_count/9)*100:.0f}% мощности"
        })
    elif planet_count >= 2:
        delta = score_value('planet_strength_medium', 1)
        compatibility_score += delta
        positive_aspects.append({
            'type': 'planet_strength_balanced',
            'icon': '⚡',
            'title': 'Сбалансированная энергия',
            'short_text': f"У вас сбалансированная энергия {ruling_planet} ({planet_count} цифры). Этот день усиливает ваши естественные способности.",
            'detailed_info': f"В вашей карте {planet_count} цифры {ruling_planet}. Это гармоничное количество, дающее стабильную силу без перегрузки.",
            'advice': [
                "Хороший день для использования качеств этой планеты",
                f"Ваша энергия {ruling_planet} сбалансирована и эффективна",
                "Действуйте уверенно в своих сильных областях"
            ],
            'planet_info': f"Баланс {ruling_planet}: {planet_count}/9 = оптимальная сила"
        })
    elif planet_count == 1:
        delta = score_value('planet_strength_low', -10)
        compatibility_score += delta
        challenges.append({
            'type': 'planet_weakness',
            'icon': '📉',
            'title': 'Слабая энергия планеты',
            'short_text': f"Энергия {ruling_planet} слабая в вашей карте ({planet_count} цифра). Используйте этот день для развития этого качества.",
            'detailed_info': f"В вашем квадрате Пифагора только {planet_count} цифра {ruling_planet}. Это означает, что качества этой планеты не являются вашей сильной стороной.",
            'advice': [
                f"Изучите качества планеты {ruling_planet} и работайте над их развитием",
                "Не беритесь за дела, требующие качеств этой планеты",
                "Обратитесь за помощью к людям, у которых эта планета сильна",
                f"Носите камни и цвета {ruling_planet} для усиления энергии",
                "Это день для обучения, а не для демонстрации мастерства"
            ],
            'planet_info': f"Слабость {ruling_planet}: {planet_count}/9 = {(planet_count/9)*100:.0f}% силы",
            'solution': f"Развивайте качества {ruling_planet} постепенно, день за днём"
        })
    else:
        compatibility_score -= 10
        challenges.append({
            'type': 'planet_absence',
            'icon': '❌',
            'title': 'ОТСУТСТВИЕ ЭНЕРГИИ ПЛАНЕТЫ!',
            'short_text': f"Энергия {ruling_planet} отсутствует в вашей карте. Это возможность познакомиться с этой энергией и развить её.",
            'detailed_info': f"В вашем квадрате Пифагора НЕТ цифр {ruling_planet}. Это означает полное отсутствие этой энергии в вашей натальной карте. День будет особенно сложным.",
            'advice': [
                f"ИЗБЕГАЙТЕ важных дел, связанных с качествами {ruling_planet}",
                "Это день для наблюдения и обучения, а не для действий",
                "Попросите помощи у людей с сильной энергией этой планеты",
                f"Изучите, какие качества даёт {ruling_planet}, и начните их развивать",
                "Будьте терпеливы к себе - это ваша зона роста",
                f"Носите талисманы {ruling_planet} для защиты и поддержки"
            ],
            'planet_info': f"ОТСУТСТВИЕ {ruling_planet}: 0/9 = критический недостаток (-10 баллов)",
            'solution': f"Работайте с мантрами {ruling_planet} ежедневно для постепенного развития этой энергии"
        })
    
    # 7. ДЕНЬ НЕДЕЛИ РОЖДЕНИЯ (+20)
    if is_birth_weekday:
        compatibility_score += 20
        positive_aspects.append({
            'type': 'birth_weekday',
            'icon': '👑',
            'title': 'ДЕНЬ ВАШЕГО РОЖДЕНИЯ!',
            'short_text': f"Сегодня день недели, в который вы родились! Все планетарные часы сегодня особенно сильны для вас. Это ваш личный день силы!",
            'detailed_info': f"Вы родились в {schedule.get('weekday', {}).get('name_ru', 'этот день')}, управляемый {ruling_planet}. Когда день недели вашего рождения повторяется, вы получаете мощную поддержку от своей натальной энергии.",
            'advice': [
                "ЭТО ВАШ ДЕНЬ! Максимальная сила и удача на вашей стороне",
                "Все планетарные часы сегодня работают в вашу пользу",
                "Идеальный день для самых важных начинаний и решений",
                "Ваша натальная энергия усиливает всё, что вы делаете",
                "Празднуйте этот день как мини-день рождения каждую неделю",
                "Загадайте желание - оно имеет высокий шанс исполниться"
            ],
            'planet_info': f"Натальная планета {ruling_planet} даёт вам +20 баллов силы!"
        })
    
    # 8. ДЕНЬ ПЛАНЕТЫ (+10/-20)
    if is_planet_day:
        # Проверяем, дружественна ли планета дня пользователю
        user_main_planet = number_to_planet.get(soul_number)
        if user_main_planet and ruling_planet in planet_relationships.get(user_main_planet, {}).get('friends', []):
            compatibility_score += 10
            positive_aspects.append({
                'type': 'planet_day_friendly',
                'icon': '📅',
                'title': 'ДЕНЬ ДРУЖЕСТВЕННОЙ ПЛАНЕТЫ!',
                'short_text': f"Сегодня день {ruling_planet}, дружественной вашей душе!",
                'detailed_info': f"Планета дня {ruling_planet} дружественна к вашей планете души {user_main_planet}. Это создаёт благоприятную атмосферу для всех ваших дел.",
                'advice': [
                    f"Энергии {user_main_planet} и {ruling_planet} работают в синергии",
                    "Отличный день для социальных контактов и сотрудничества",
                    "Ваши естественные качества поддерживаются днём",
                    "Действуйте смело - планеты на вашей стороне"
                ],
                'planet_info': f"Дружба планет: {user_main_planet} ❤️ {ruling_planet}"
            })
        elif user_main_planet and ruling_planet in planet_relationships.get(user_main_planet, {}).get('enemies', []):
            compatibility_score -= 20
            challenges.append({
                'type': 'enemy_planet_day',
                'icon': '⚔️',
                'title': 'ДЕНЬ ВРАЖДЕБНОЙ ПЛАНЕТЫ!',
                'short_text': f"Сегодня день {ruling_planet}, враждебной вашей душе. Будьте осторожны.",
                'detailed_info': f"Планета дня {ruling_planet} является врагом вашей планеты души {user_main_planet}. Это создаёт максимальное напряжение и конфликт энергий. Один из самых сложных дней для вас.",
                'advice': [
                    "ИЗБЕГАЙТЕ важных начинаний, подписания договоров, крупных покупок",
                    "Не вступайте в конфликты - они будут особенно разрушительными",
                    "Отложите важные встречи и переговоры на другой день",
                    "Больше отдыхайте, не перегружайте себя",
                    f"Медитируйте на свою планету {user_main_planet} для защиты",
                    "Носите защитные амулеты и камни вашей планеты",
                    "Это день для завершения старых дел, а не начала новых"
                ],
                'planet_info': f"ВРАЖДЕБНОСТЬ: {user_main_planet} (душа) ⚔️ {ruling_planet} (день) = -20 баллов!",
                'solution': f"Дождитесь дня {user_main_planet} или её друзей для важных дел"
            })
        else:
            compatibility_score += 10
            positive_aspects.append({
                'type': 'planet_day_neutral',
                'icon': '📅',
                'title': 'ДЕНЬ ПЛАНЕТЫ',
                'short_text': f"Сегодня день {ruling_planet}!",
                'detailed_info': f"Планета {ruling_planet} правит этим днём, создавая особую энергетическую атмосферу.",
                'advice': [
                    f"Изучите качества {ruling_planet} и используйте их",
                    "Нейтральная энергия даёт свободу действий",
                    "Хороший день для баланса и гармонии"
                ],
                'planet_info': f"Планета дня: {ruling_planet}"
            })
    
    # 9. ЛИЧНЫЙ ДЕНЬ (+8)
    personal_year = user_data.get('personal_year', 1)
    personal_month = user_data.get('personal_month', 1)
    personal_day = user_data.get('personal_day', 1)
    
    if personal_day == ruling_planet_number:
        compatibility_score += 8
        positive_aspects.append({
            'type': 'personal_day',
            'icon': '🌱',
            'title': 'РЕЗОНАНС ЛИЧНОГО ДНЯ!',
            'short_text': f"Ваш личный день ({personal_day}) резонирует с {ruling_planet}. Энергия дня поддерживает ваш текущий цикл!",
            'detailed_info': f"Ваш личный день в нумерологическом цикле - {personal_day}, что соответствует планете {number_to_planet.get(personal_day)}. Совпадение с планетой дня {ruling_planet} создаёт поддерживающий резонанс.",
            'advice': [
                "Ваш личный цикл синхронизирован с энергией дня",
                "Отличное время для движения вперёд по вашим планам",
                "События дня будут способствовать вашему развитию",
                f"Личный год: {personal_year}, месяц: {personal_month}, день: {personal_day}"
            ],
            'planet_info': f"Синхронизация: Личный день {personal_day} = {ruling_planet}"
        })
    
    # 10. ГЛОБАЛЬНАЯ ГАРМОНИЯ (+5/-15)
    user_planets = [k for k, v in planet_counts.items() if v > 0]
    friendly_count = 0
    enemy_count = 0
    friendly_planets = []
    enemy_planets = []
    
    for user_planet in user_planets:
        if user_planet in planet_relationships:
            if ruling_planet in planet_relationships[user_planet].get('friends', []):
                friendly_count += planet_counts[user_planet]
                friendly_planets.append(f"{user_planet} ({planet_counts[user_planet]})")
            elif ruling_planet in planet_relationships[user_planet].get('enemies', []):
                enemy_count += planet_counts[user_planet]
                enemy_planets.append(f"{user_planet} ({planet_counts[user_planet]})")
    
    if friendly_count > enemy_count * 2:
        compatibility_score += 5
        positive_aspects.append({
            'type': 'global_harmony',
            'icon': '🤝',
            'title': 'ГЛОБАЛЬНАЯ ГАРМОНИЯ!',
            'short_text': f"Планеты в вашей карте дружественны к {ruling_planet}. Общая гармония поддерживает вас!",
            'detailed_info': f"В вашей карте {friendly_count} дружественных цифр против {enemy_count} враждебных к {ruling_planet}. Это создаёт общую поддерживающую атмосферу.",
            'advice': [
                "Общий баланс планет в вашу пользу",
                f"Дружественные планеты: {', '.join(friendly_planets)}",
                "Используйте эту гармонию для важных дел",
                "День благоприятствует вашей натуре"
            ],
            'planet_info': f"Баланс: {friendly_count} дружественных vs {enemy_count} враждебных"
        })
    elif enemy_count > friendly_count * 2:
        compatibility_score -= 15
        challenges.append({
            'type': 'global_disharmony',
            'icon': '⚔️',
            'title': 'ГЛОБАЛЬНАЯ ДИСГАРМОНИЯ!',
            'short_text': f"Многие планеты в вашей карте конфликтуют с {ruling_planet}. Будьте терпеливы и гибки.",
            'detailed_info': f"В вашей карте {enemy_count} враждебных цифр против {friendly_count} дружественных к {ruling_planet}. Это создаёт общую неблагоприятную атмосферу.",
            'advice': [
                "Минимизируйте активность - это день для отдыха и восстановления",
                "Не начинайте новых проектов и не принимайте важных решений",
                "Будьте терпеливы к себе и окружающим",
                f"Враждебные планеты: {', '.join(enemy_planets)}",
                "Работайте с защитными практиками и медитациями",
                "Это временное состояние - завтра будет лучше"
            ],
            'planet_info': f"Дисбаланс: {enemy_count} враждебных vs {friendly_count} дружественных = -15 баллов",
            'solution': f"Используйте планетарные часы дружественных планет для важных дел"
        })
    
    # 11. РЕЗОНАНС С ПРАВЯЩИМ ЧИСЛОМ (+5/-5)
    if ruling_number == ruling_planet_number:
        compatibility_score += 5
        positive_aspects.append({
            'type': 'ruling_number',
            'icon': '✨',
            'title': 'РЕЗОНАНС ПРАВЯЩЕГО ЧИСЛА!',
            'short_text': f"Ваше правящее число ({ruling_number}) совпадает с планетой дня!",
            'detailed_info': f"Правящее число {ruling_number} - это сумма всех цифр вашей даты рождения. Оно представляет вашу жизненную миссию и предназначение. Совпадение с планетой дня {ruling_planet} усиливает вашу связь с предназначением.",
            'advice': [
                "День поддерживает вашу жизненную миссию",
                "Действуйте в соответствии со своим предназначением",
                "Это время для реализации вашего потенциала",
                f"Правящее число {ruling_number} = {ruling_planet}"
            ],
            'planet_info': f"Ваша миссия ({ruling_number}) резонирует с днём ({ruling_planet})"
        })
    elif ruling_number:
        ruling_num_planet = number_to_planet.get(ruling_number)
        if ruling_num_planet and ruling_planet in planet_relationships.get(ruling_num_planet, {}).get('enemies', []):
            compatibility_score -= 5
            challenges.append({
                'type': 'ruling_conflict',
                'icon': '👑',
                'title': 'Конфликт правящего числа',
                'short_text': f"Ваше правящее число ({ruling_number}) конфликтует с планетой дня.",
                'detailed_info': f"Правящее число {ruling_number} (планета {ruling_num_planet}) враждебно к {ruling_planet}. Это создаёт конфликт между вашей жизненной миссией и энергией дня.",
                'advice': [
                    "Не форсируйте движение к долгосрочным целям сегодня",
                    "Сосредоточьтесь на текущих, рутинных делах",
                    "Избегайте стратегических решений",
                    f"Работайте с энергией {ruling_num_planet} для баланса",
                    "Это день для тактики, а не стратегии"
                ],
                'planet_info': f"Конфликт миссии: {ruling_num_planet} ({ruling_number}) ⚔️ {ruling_planet}",
                'solution': f"Планируйте важные шаги на дни {ruling_num_planet}"
            })
    
    # 12. РЕЗОНАНС ЛИЧНОГО ЧИСЛА ДНЯ (+2/-4)
    day_number = date_obj.day % 9 if date_obj.day % 9 != 0 else 9
    if day_number == ruling_planet_number:
        compatibility_score += 2
        positive_aspects.append({
            'type': 'day_number',
            'icon': '📆',
            'title': 'Резонанс числа дня',
            'short_text': f"Число дня ({day_number}) резонирует с планетой дня!",
            'detailed_info': f"Сегодня {date_obj.day} число месяца, что даёт нумерологическое число {day_number}. Это число соответствует планете {number_to_planet.get(day_number)}, которая совпадает с правящей планетой дня.",
            'advice': [
                "Число календарного дня поддерживает энергию",
                "Хороший день для начинаний",
                f"Дата {date_obj.day} = число {day_number} = {ruling_planet}"
            ],
            'planet_info': f"Календарное число {day_number} = {ruling_planet}"
        })
    elif number_to_planet.get(day_number) and ruling_planet in planet_relationships.get(number_to_planet.get(day_number), {}).get('enemies', []):
        compatibility_score -= 4
        challenges.append({
            'type': 'day_number_conflict',
            'icon': '📆',
            'title': 'Конфликт числа дня',
            'short_text': f"Число дня ({day_number}) конфликтует с планетой дня.",
            'detailed_info': f"Календарное число дня {date_obj.day} даёт нумерологическое число {day_number} (планета {number_to_planet.get(day_number)}), которое враждебно к {ruling_planet}.",
            'advice': [
                "Календарная дата не в вашу пользу сегодня",
                "Избегайте подписания документов с сегодняшней датой",
                "Если возможно, перенесите важные дела на другое число месяца",
                "Это временное влияние - завтра число изменится"
            ],
            'planet_info': f"Конфликт даты: {day_number} ({number_to_planet.get(day_number)}) ⚔️ {ruling_planet}",
            'solution': "Дождитесь более благоприятного числа месяца"
        })
    
    # 13. РЕЗОНАНС ЧИСЛА ИМЕНИ (+5/-5)
    name_number = user_data.get('name_number', 0)
    if name_number:
        name_planet = number_to_planet.get(name_number)
        if name_number == ruling_planet_number:
            compatibility_score += 5
            positive_aspects.append({
                'type': 'name_number',
                'icon': '📝',
                'title': 'РЕЗОНАНС ИМЕНИ!',
                'short_text': f"Ваше имя ({name_number}) резонирует с планетой дня!",
                'detailed_info': f"Нумерологическое число вашего имени - {name_number}, что соответствует планете {name_planet}. Когда эта планета правит днём, ваше имя и личность получают дополнительную силу.",
                'advice': [
                    "Ваше имя резонирует с энергией дня",
                    "Отличный день для самопрезентации и общения",
                    "Ваша личность сияет особенно ярко",
                    f"Имя {name_number} = {ruling_planet}"
                ],
                'planet_info': f"Ваше имя ({name_number}) = {ruling_planet} (планета дня)"
            })
        elif name_planet and ruling_planet in planet_relationships.get(name_planet, {}).get('enemies', []):
            compatibility_score -= 5
            challenges.append({
                'type': 'name_conflict',
                'icon': '📝',
                'title': 'Конфликт имени',
                'short_text': f"Ваше имя ({name_number}) конфликтует с планетой дня.",
                'detailed_info': f"Нумерологическое число вашего имени {name_number} (планета {name_planet}) враждебно к {ruling_planet}. Ваша личность и самопрезентация могут встретить сопротивление.",
                'advice': [
                    "Избегайте важных презентаций и самопрезентации",
                    "Не лучший день для первых встреч и знакомств",
                    "Ваше имя может не резонировать с окружающими сегодня",
                    "Работайте за кулисами, избегайте публичности",
                    f"Медитируйте на энергию {name_planet} для защиты"
                ],
                'planet_info': f"Конфликт имени: {name_planet} ({name_number}) ⚔️ {ruling_planet}",
                'solution': f"Используйте дни {name_planet} для важных встреч и презентаций"
            })
    
    # Проверяем Rahu Kaal
    rahu_kaal = schedule.get('inauspicious_periods', {}).get('rahu_kaal', {})
    if rahu_kaal:
        challenges.append({
            'type': 'rahu_kaal',
            'icon': '⚠️',
            'title': 'RAHU KAAL - НЕБЛАГОПРИЯТНОЕ ВРЕМЯ!',
            'short_text': f"Сегодня Rahu Kaal с {rahu_kaal.get('start', '')} до {rahu_kaal.get('end', '')}. Избегайте важных начинаний в это время.",
            'detailed_info': f"Rahu Kaal - это период дня, управляемый теневой планетой Rahu. Это самое неблагоприятное время для любых начинаний. Сегодня он длится с {rahu_kaal.get('start', '')} до {rahu_kaal.get('end', '')}.",
            'advice': [
                "НЕ НАЧИНАЙТЕ ничего нового в это время!",
                "Не подписывайте документы, не заключайте сделки",
                "Не отправляйтесь в путешествия",
                "Не проводите важные встречи и переговоры",
                "Используйте это время для рутинных дел и отдыха",
                "После окончания Rahu Kaal энергия дня нормализуется",
                "Планируйте важные дела ДО или ПОСЛЕ этого периода"
            ],
            'planet_info': f"Rahu Kaal: {rahu_kaal.get('start', '')} - {rahu_kaal.get('end', '')} = критический период",
            'solution': "Перенесите все важные дела на время после окончания Rahu Kaal"
        })
    
    # Ограничиваем score в пределах 0-100
    compatibility_score = max(0, min(100, compatibility_score))
    
    # Определяем общую оценку и цвет
    if compatibility_score >= 80:
        overall_rating = "Отличный день"
        color_class = "green"
        influence_dynamic = "Благоприятное"
    elif compatibility_score >= 65:
        overall_rating = "Хороший день"
        color_class = "green"
        influence_dynamic = "Поддерживающее"
    elif compatibility_score >= 50:
        overall_rating = "Нейтральный день"
        color_class = "blue"
        influence_dynamic = "Сбалансированное"
    elif compatibility_score >= 35:
        overall_rating = "Развивающий день"
        color_class = "orange"
        influence_dynamic = "Вызов"
    else:
        overall_rating = "Сложный день"
        color_class = "orange"
        influence_dynamic = "Испытание"
    
    # Генерируем детальное описание с учётом всех факторов
    overall_description = f"Сегодня {schedule.get('weekday', {}).get('name_ru', 'день')}, управляемый планетой {ruling_planet}. "
    
    # Анализ взаимодействия планет
    user_main_planet = number_to_planet.get(soul_number)
    
    # Проверяем реальные отношения между планетами
    if user_main_planet:
        user_planet_data = planet_relationships.get(user_main_planet, {})
        
        if ruling_planet in user_planet_data.get('friends', []):
            planet_relation = "дружественна"
            overall_description += f"Планета дня {ruling_planet} дружественна к вашей планете души {user_main_planet}. "
        elif ruling_planet in user_planet_data.get('enemies', []):
            planet_relation = "враждебна"
            overall_description += f"Планета дня {ruling_planet} враждебна к вашей планете души {user_main_planet}. "
        else:
            planet_relation = "нейтральна"
            overall_description += f"Планета дня {ruling_planet} нейтральна к вашей планете души {user_main_planet}. "
    else:
        planet_relation = "нейтральна"
    
    # Добавляем информацию о силе планеты в карте (ТОЛЬКО если она есть в карте)
    if planet_count >= 4:
        overall_description += f"У вас очень сильная энергия {ruling_planet} ({planet_count} {'цифр' if planet_count >= 5 else 'цифры'}), что даёт вам преимущество. "
    elif planet_count >= 2:
        overall_description += f"У вас сбалансированная энергия {ruling_planet} ({planet_count} цифры). "
    elif planet_count == 1:
        overall_description += f"Энергия {ruling_planet} слабая в вашей карте ({planet_count} цифра), будьте осторожны. "
    elif planet_count == 0:
        overall_description += f"Энергия {ruling_planet} отсутствует в вашей карте - это ваша зона роста. "
    
    # Добавляем рекомендации по времени
    if compatibility_score >= 70:
        overall_description += f"Энергии дня прекрасно резонируют с вашими личными числами (баллы: {compatibility_score}/100). Это благоприятное время для важных дел, начинаний, подписания договоров и принятия решений. "
        
        # Находим лучшие часы
        best_hours = []
        if user_main_planet:
            best_hours.append(f"часы {user_main_planet}")
        if soul_number != mind_number:
            mind_planet = number_to_planet.get(mind_number)
            if mind_planet:
                best_hours.append(f"часы {mind_planet}")
        
        if best_hours:
            overall_description += f"Особенно благоприятны: {', '.join(best_hours)}. "
            
    elif compatibility_score >= 50:
        overall_description += f"Энергии дня находятся в балансе с вашими личными числами (баллы: {compatibility_score}/100). Действуйте обдуманно и используйте свои сильные стороны. "
        
        # Рекомендации по времени
        if user_main_planet:
            overall_description += f"Планируйте важные дела на часы {user_main_planet} для максимальной эффективности. "
            
    else:
        overall_description += f"Энергии дня создают напряжение (баллы: {compatibility_score}/100). Это время для осторожности, завершения старых дел и развития новых качеств. "
        
        # Предупреждения
        if planet_count == 0:
            overall_description += f"ИЗБЕГАЙТЕ важных начинаний - у вас нет энергии {ruling_planet}. "
        
        if planet_relation == "враждебна":
            overall_description += f"Планета дня враждебна вашей душе - минимизируйте риски. "
        
        # Рекомендации по безопасному времени
        safe_hours = []
        for p, count in planet_counts.items():
            if count > 0 and p in planet_relationships.get(ruling_planet, {}).get('friends', []):
                safe_hours.append(p)
        
        if safe_hours:
            overall_description += f"Безопасные часы для дел: {', '.join(safe_hours[:3])}. "
        elif user_main_planet:
            overall_description += f"Используйте часы {user_main_planet} для защиты. "
    
    # Добавляем информацию о Rahu Kaal
    if rahu_kaal:
        overall_description += f"⚠️ ВНИМАНИЕ: Rahu Kaal с {rahu_kaal.get('start', '')} до {rahu_kaal.get('end', '')} - избегайте любых начинаний в это время!"
    
    # Если нет позитивных аспектов, добавляем общие
    if not positive_aspects:
        positive_aspects.append("Каждый день - это возможность для роста и развития.")
        positive_aspects.append("Используйте энергию дня для познания нового.")
    
    # Если нет вызовов, добавляем общие
    if not challenges:
        challenges.append("Будьте внимательны к деталям и не спешите с решениями.")
    
    # Создаём конкретный план действий на день
    action_plan = {
        'morning': [],
        'afternoon': [],
        'evening': [],
        'avoid': [],
        'best_hours': [],
        'protective_practices': []
    }
    
    # Утро
    if compatibility_score >= 70:
        action_plan['morning'].append("Начните день с планирования важных дел")
        action_plan['morning'].append(f"Медитация на энергию {ruling_planet} для усиления резонанса")
        action_plan['morning'].append("Идеальное время для начала новых проектов")
    elif compatibility_score >= 50:
        action_plan['morning'].append("Начните с рутинных дел для разогрева")
        action_plan['morning'].append("Оцените свои ресурсы перед важными решениями")
    else:
        action_plan['morning'].append("Начните день с защитных практик")
        action_plan['morning'].append(f"Медитация на {user_main_planet} для защиты от негативных влияний")
        action_plan['morning'].append("Избегайте важных решений до обеда")
    
    # День
    if compatibility_score >= 70:
        action_plan['afternoon'].append("Проводите важные встречи и переговоры")
        action_plan['afternoon'].append("Подписывайте договоры и соглашения")
        action_plan['afternoon'].append("Принимайте стратегические решения")
    elif compatibility_score >= 50:
        action_plan['afternoon'].append("Работайте над текущими проектами")
        action_plan['afternoon'].append("Консультируйтесь перед важными решениями")
    else:
        action_plan['afternoon'].append("Занимайтесь рутинными делами")
        action_plan['afternoon'].append("Избегайте конфликтов и споров")
        action_plan['afternoon'].append("Отложите важные решения на другой день")
    
    # Вечер
    if compatibility_score >= 70:
        action_plan['evening'].append("Подведите итоги успешного дня")
        action_plan['evening'].append("Планируйте следующие шаги")
        action_plan['evening'].append(f"Благодарственная медитация {ruling_planet}")
    elif compatibility_score >= 50:
        action_plan['evening'].append("Проанализируйте результаты дня")
        action_plan['evening'].append("Завершите начатые дела")
    else:
        action_plan['evening'].append("Отдохните и восстановите силы")
        action_plan['evening'].append("Защитные практики перед сном")
        action_plan['evening'].append("Не принимайте решений в усталом состоянии")
    
    # Что избегать
    if planet_count == 0:
        action_plan['avoid'].append(f"Дела, требующие качеств {ruling_planet}")
    if planet_relation == "враждебна":
        action_plan['avoid'].append("Конфликты и противостояния")
        action_plan['avoid'].append("Рискованные начинания")
    if enemy_count > friendly_count:
        action_plan['avoid'].append("Важные финансовые решения")
        action_plan['avoid'].append("Начало долгосрочных проектов")
    if rahu_kaal:
        action_plan['avoid'].append(f"Любые начинания с {rahu_kaal.get('start', '')} до {rahu_kaal.get('end', '')}")
    
    # Лучшие часы
    if user_main_planet:
        action_plan['best_hours'].append(f"Часы {user_main_planet} - ваша максимальная сила")
    if soul_number != mind_number:
        mind_planet = number_to_planet.get(mind_number)
        if mind_planet:
            action_plan['best_hours'].append(f"Часы {mind_planet} - для интеллектуальной работы")
    if destiny_number and destiny_number != soul_number:
        destiny_planet = number_to_planet.get(destiny_number)
        if destiny_planet:
            action_plan['best_hours'].append(f"Часы {destiny_planet} - для движения к целям")
    
    # Защитные практики
    if compatibility_score < 50:
        action_plan['protective_practices'].append(f"Мантра {user_main_planet} - 108 раз утром")
        action_plan['protective_practices'].append(f"Носите камни/цвета {user_main_planet}")
        action_plan['protective_practices'].append("Избегайте негативных людей и ситуаций")
        if planet_count == 0:
            action_plan['protective_practices'].append(f"Изучайте качества {ruling_planet} для будущего развития")
    
    return {
        'overall_score': compatibility_score,
        'overall_rating': overall_rating,
        'overall_description': overall_description,
        'positive_aspects': positive_aspects,
        'challenges': challenges,
        'color_class': color_class,
        'influence': {
            'dynamic': influence_dynamic
        },
        'all_planet_counts': planet_counts,
        'rahu_kaal_info': rahu_kaal,
        'global_harmony': {
            'friendly_count': friendly_count,
            'enemy_count': enemy_count
        },
        'action_plan': action_plan
    }

@api_router.get('/vedic-time/planetary-route')
async def planetary_route(vedic_request: VedicTimeRequest = Depends(), current_user: dict = Depends(get_current_user)):
    """Детальный планетарный маршрут на день с полным анализом - 1 балл"""
    user_id = current_user['user_id']
    
    # Получаем данные пользователя для города и даты рождения
    user_dict = await db.users.find_one({'id': user_id})
    if not user_dict:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    user = User(**user_dict)
    
    # Получаем стоимость из конфигурации
    config = await get_credits_deduction_config()
    cost = config.get('planetary_daily', CREDIT_COSTS.get('planetary_daily', 1))
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        cost, 
        'Планетарный маршрут на день', 
        'vedic',
        {'calculation_type': 'planetary_daily', 'date': vedic_request.date}
    )
    
    # Parse date string to datetime object
    if vedic_request.date:
        try:
            date_obj = datetime.strptime(vedic_request.date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        # Используем UTC время с timezone для корректной конвертации в локальное время города
        date_obj = datetime.now(pytz.UTC)

    city = vedic_request.city or user.city
    if not city:
        raise HTTPException(status_code=422, detail="Город не указан. Укажите город в запросе или обновите профиль пользователя.")
        
    schedule = get_vedic_day_schedule(city=city, date=date_obj)
    if 'error' in schedule:
        # Возвращаем балл при ошибке
        config = await get_credits_deduction_config()
        cost = config.get('planetary_daily', CREDIT_COSTS.get('planetary_daily', 1))
        await record_credit_transaction(user_id, cost, 'Возврат за ошибку планетарного маршрута', 'refund')
        await db.users.update_one({'id': user_id}, {'$inc': {'credits_remaining': cost}})
        raise HTTPException(status_code=400, detail=schedule['error'])
        
    # Получаем нумерологические данные пользователя
    user_data = await get_user_numerology_data(user_id)
    
    # Анализируем день с учётом личных чисел
    day_analysis = analyze_day_compatibility(date_obj, user_data, schedule)
    
    # Получаем почасовую энергию планет с детальными советами (дневные часы)
    day_hours_energy = await calculate_hourly_planetary_energy(schedule.get('planetary_hours', []), user_data, db)
    
    # Получаем ночные часы с детальными советами
    night_hours = schedule.get('night_hours', [])
    night_hours_energy = await calculate_hourly_planetary_energy(night_hours, user_data, db) if night_hours else []
    
    # Объединяем дневные и ночные часы в полный 24-часовой гид
    full_24h_guide = day_hours_energy + night_hours_energy
    
    # Находим лучшие часы для разных активностей
    best_hours = find_best_hours_for_activities(full_24h_guide, user_data)
    
    # Calculate planetary energies for the day
    planetary_energies = {}
    total_energy = 0
    try:
        # Prepare user data for enhanced calculation
        user_numbers = None
        pythagorean_square_data = None
        fractal_behavior = None
        problem_numbers = None
        name_numbers = None
        weekday_energy = None
        janma_ank_value = None
        
        if user.birth_date:
            try:
                day, month, year = parse_birth_date(user.birth_date)
                
                # Get personal numbers
                personal_numbers = calculate_personal_numbers(user.birth_date)
                user_numbers = {
                    'soul_number': personal_numbers.get('soul_number'),
                    'mind_number': personal_numbers.get('mind_number'),
                    'destiny_number': personal_numbers.get('destiny_number'),
                    'wisdom_number': personal_numbers.get('wisdom_number'),
                    'ruling_number': personal_numbers.get('ruling_number'),
                    'personal_day': personal_numbers.get('personal_day')
                }
                
                # Calculate Pythagorean Square
                pythagorean_square_data = create_pythagorean_square(day, month, year)
                
                # Calculate Janma Ank
                from vedic_numerology import calculate_janma_ank, calculate_bhagya_ank, calculate_enhanced_daily_planetary_energy
                janma_ank_value = calculate_janma_ank(day, month, year)
                total_before_reduction = day + month + year
                if total_before_reduction == 22:
                    janma_ank_value = 22
                
                destiny_number = calculate_bhagya_ank(day, month, year)
                
                # Calculate fractal behavior
                day_reduced = reduce_to_single_digit(day)
                month_reduced = reduce_to_single_digit(month)
                year_reduced = reduce_to_single_digit(year)
                year_sum = reduce_to_single_digit(day + month + year)
                fractal_behavior = [day_reduced, month_reduced, year_reduced, year_sum]
                
                # Calculate problem numbers
                soul_num = user_numbers.get('soul_number', 1)
                mind_num = user_numbers.get('mind_number', 1)
                destiny_num = user_numbers.get('destiny_number', 1)
                problem1 = reduce_to_single_digit(abs(soul_num - mind_num))
                problem2 = reduce_to_single_digit(abs(soul_num - year_reduced))
                problem3 = reduce_to_single_digit(abs(problem1 - problem2))
                problem4 = reduce_to_single_digit(abs(mind_num - year_reduced))
                problem_numbers = [problem1, problem2, problem3, problem4]
                
                # Get name numbers if available
                if hasattr(user, 'full_name') and user.full_name:
                    from numerology import calculate_name_numerology
                    try:
                        name_data = calculate_name_numerology(user.full_name)
                        name_numbers = {
                            'first_name_number': name_data.get('first_name_number'),
                            'last_name_number': name_data.get('last_name_number'),
                            'total_name_number': name_data.get('total_name_number'),
                            'full_name_number': name_data.get('total_name_number')
                        }
                    except:
                        pass
                
                # Calculate weekday energy
                try:
                    from numerology import calculate_planetary_strength
                    planetary_strength_data = calculate_planetary_strength(day, month, year)
                    strength_dict = planetary_strength_data.get('strength', {})
                    planet_name_to_key = {
                        'Солнце': 'surya', 'Луна': 'chandra', 'Марс': 'mangal',
                        'Меркурий': 'budha', 'Юпитер': 'guru', 'Венера': 'shukra', 'Сатурн': 'shani'
                    }
                    weekday_energy = {}
                    for planet_name, energy_value in strength_dict.items():
                        planet_key = planet_name_to_key.get(planet_name)
                        if planet_key:
                            weekday_energy[planet_key] = float(energy_value)
                except:
                    pass
                
                # Get modifiers config
                modifiers_config = await get_planetary_energy_modifiers_config()
                
                # Calculate planetary energy for the day
                planetary_energies = calculate_enhanced_daily_planetary_energy(
                    destiny_number=destiny_number,
                    date=date_obj,
                    birth_date=user.birth_date,
                    user_numbers=user_numbers,
                    pythagorean_square=pythagorean_square_data,
                    fractal_behavior=fractal_behavior,
                    problem_numbers=problem_numbers,
                    name_numbers=name_numbers,
                    weekday_energy=weekday_energy,
                    janma_ank=janma_ank_value,
                    city=city,
                    modifiers_config=modifiers_config
                )
                
                total_energy = sum(planetary_energies.values())
            except Exception as e:
                print(f"Error calculating planetary energy for daily route: {e}")
    except Exception as e:
        print(f"Error adding planetary energy to daily route: {e}")
    
    # Build detailed route from schedule
    rec = schedule.get('recommendations', {})
    route = {
        'date': date_obj.strftime('%Y-%m-%d'),
        'city': city,
        'personal_birth_date': user.birth_date,
        'daily_ruling_planet': schedule.get('weekday', {}).get('ruling_planet', ''),
        
        # Нумерологический анализ дня
        'day_analysis': day_analysis,
        
        # НОВОЕ: Добавляем schedule для фронтенда
        'schedule': schedule,
        
        # Планетарные энергии дня
        'planetary_energies': planetary_energies,
        'total_energy': total_energy,
        
        # Полный 24-часовой гид с детальными советами
        'hourly_guide_24h': full_24h_guide,
        
        # Обратная совместимость со старым фронтендом
        'hourly_energy': full_24h_guide,  # Для графика
        'hourly_guide': schedule.get('planetary_hours', []),  # Для почасового плана (только дневные часы)
        
        # Лучшие часы для конкретных активностей
        'best_hours_by_activity': best_hours,
        
        # Периоды, которых стоит избегать
        'avoid_periods': {
            'rahu_kaal': schedule.get('inauspicious_periods', {}).get('rahu_kaal', {}),
            'gulika_kaal': schedule.get('inauspicious_periods', {}).get('gulika_kaal', {}),
            'yamaghanta': schedule.get('inauspicious_periods', {}).get('yamaghanta', {})
        },
        
        # Благоприятный период
        'favorable_period': schedule.get('auspicious_periods', {}).get('abhijit_muhurta', {}),
        
        # Общие рекомендации
        'daily_recommendations': rec,
        
        # Совместимость с личными числами
        'personal_compatibility': {
            'soul_number': user_data.get('soul_number'),
            'destiny_number': user_data.get('destiny_number'),
            'mind_number': user_data.get('mind_number'),
            'compatibility_score': day_analysis.get('overall_score', 0)
        }
    }
    
    # Сохраняем планетарный маршрут в БД
    try:
        calc = NumerologyCalculation(
            user_id=user_id, 
            birth_date=vedic_request.date, 
            calculation_type='planetary_route_daily', 
            results=route
        )
        await db.numerology_calculations.insert_one(calc.dict())
    except Exception as e:
        print(f"Ошибка сохранения планетарного маршрута: {e}")
    
    return route
@api_router.get('/vedic-time/planetary-route/weekly')
async def weekly_planetary_route(vedic_request: VedicTimeRequest = Depends(), current_user: dict = Depends(get_current_user)):
    """Планетарный маршрут на неделю - 10 баллов"""
    user_id = current_user['user_id']
    
    # Получаем данные пользователя
    user_dict = await db.users.find_one({'id': user_id})
    if not user_dict:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    user = User(**user_dict)
    
    # Получаем стоимость из единой конфигурации
    config = await get_credits_deduction_config()
    cost = config.get('planetary_weekly', CREDIT_COSTS.get('planetary_weekly', 10))
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id,
        cost,
        'Планетарный маршрут на неделю',
        'vedic',
        {'calculation_type': 'planetary_weekly', 'date': vedic_request.date}
    )
    
    try:
        
        # Парсим дату
        date_obj = datetime.strptime(vedic_request.date, '%Y-%m-%d')
        
        # Импортируем функцию
        from vedic_time_calculations import get_weekly_planetary_route
        
        # Prepare user data for enhanced calculation
        user_numbers = None
        pythagorean_square_data = None
        fractal_behavior = None
        problem_numbers = None
        name_numbers = None
        weekday_energy = None
        janma_ank_value = None
        
        city = vedic_request.city or user.city
        if not city:
            raise HTTPException(status_code=422, detail="Город не указан. Укажите город в запросе или обновите профиль пользователя.")
        
        # Initialize variables with default values
        user_numbers = None
        pythagorean_square_data = None
        fractal_behavior = None
        problem_numbers = None
        name_numbers = None
        weekday_energy = None
        janma_ank_value = None
        
        if user.birth_date:
            try:
                day, month, year = parse_birth_date(user.birth_date)
                
                # Get personal numbers
                personal_numbers = calculate_personal_numbers(user.birth_date)
                user_numbers = {
                    'soul_number': personal_numbers.get('soul_number'),
                    'mind_number': personal_numbers.get('mind_number'),
                    'destiny_number': personal_numbers.get('destiny_number'),
                    'wisdom_number': personal_numbers.get('wisdom_number'),
                    'ruling_number': personal_numbers.get('ruling_number'),
                    'personal_day': personal_numbers.get('personal_day')
                }
                
                # Calculate Pythagorean Square
                pythagorean_square_data = create_pythagorean_square(day, month, year)
                
                # Calculate Janma Ank
                from vedic_numerology import calculate_janma_ank
                janma_ank_value = calculate_janma_ank(day, month, year)
                total_before_reduction = day + month + year
                if total_before_reduction == 22:
                    janma_ank_value = 22
                
                # Calculate fractal behavior
                day_reduced = reduce_to_single_digit(day)
                month_reduced = reduce_to_single_digit(month)
                year_reduced = reduce_to_single_digit(year)
                year_sum = reduce_to_single_digit(day + month + year)
                fractal_behavior = [day_reduced, month_reduced, year_reduced, year_sum]
                
                # Calculate problem numbers
                soul_num = user_numbers.get('soul_number', 1)
                mind_num = user_numbers.get('mind_number', 1)
                destiny_num = user_numbers.get('destiny_number', 1)
                problem1 = reduce_to_single_digit(abs(soul_num - mind_num))
                problem2 = reduce_to_single_digit(abs(soul_num - year_reduced))
                problem3 = reduce_to_single_digit(abs(problem1 - problem2))
                problem4 = reduce_to_single_digit(abs(mind_num - year_reduced))
                problem_numbers = [problem1, problem2, problem3, problem4]
                
                # Get name numbers if available
                if hasattr(user, 'full_name') and user.full_name:
                    from numerology import calculate_name_numerology
                    try:
                        name_data = calculate_name_numerology(user.full_name)
                        name_numbers = {
                            'first_name_number': name_data.get('first_name_number'),
                            'last_name_number': name_data.get('last_name_number'),
                            'total_name_number': name_data.get('total_name_number'),
                            'full_name_number': name_data.get('total_name_number')
                        }
                    except:
                        pass
                
                # Calculate weekday energy
                try:
                    from numerology import calculate_planetary_strength
                    planetary_strength_data = calculate_planetary_strength(day, month, year)
                    strength_dict = planetary_strength_data.get('strength', {})
                    planet_name_to_key = {
                        'Солнце': 'surya', 'Луна': 'chandra', 'Марс': 'mangal',
                        'Меркурий': 'budha', 'Юпитер': 'guru', 'Венера': 'shukra', 'Сатурн': 'shani'
                    }
                    weekday_energy = {}
                    for planet_name, energy_value in strength_dict.items():
                        planet_key = planet_name_to_key.get(planet_name)
                        if planet_key:
                            weekday_energy[planet_key] = float(energy_value)
                except:
                    pass
            except Exception as e:
                print(f"Error preparing enhanced calculation data: {e}")
        
        # Get modifiers config
        modifiers_config = await get_planetary_energy_modifiers_config()
        
        # Получаем недельный маршрут
        weekly_route = get_weekly_planetary_route(
            city=city,
            start_date=date_obj,
            birth_date=user.birth_date,
            user_numbers=user_numbers,
            pythagorean_square=pythagorean_square_data,
            fractal_behavior=fractal_behavior,
            problem_numbers=problem_numbers,
            name_numbers=name_numbers,
            weekday_energy=weekday_energy,
            janma_ank=janma_ank_value,
            modifiers_config=modifiers_config
        )
        
        # Получаем нумерологические данные пользователя
        from numerology import reduce_to_single_digit_always, reduce_for_ruling_number
        
        # Рассчитываем личные числа
        from numerology import calculate_ruling_number
        if user.birth_date:
            d, m, y = parse_birth_date(user.birth_date)
        else:
            d, m, y = 1, 1, 2000  # Default values
        soul_number = reduce_to_single_digit_always(d)
        mind_number = reduce_to_single_digit_always(m)
        destiny_number = reduce_to_single_digit_always(d + m + y)
        ruling_number = calculate_ruling_number(d, m, y)
        
        # Добавляем персонализированный анализ для каждого дня
        user_data = {
            'soul_number': soul_number,
            'mind_number': mind_number,
            'destiny_number': destiny_number,
            'ruling_number': ruling_number,
            'pythagorean_square': user_dict.get('pythagorean_square', {}),
            'birth_date': user.birth_date,
            'full_name': user_dict.get('full_name', ''),
            'address': user_dict.get('address', ''),
            'car_number': user_dict.get('car_number', '')
        }
        
        # Анализируем каждый день недели
        for day in weekly_route['daily_schedule']:
            day_date = datetime.strptime(day['date'], '%Y-%m-%d')
            
            # Получаем полное расписание дня для анализа
            from vedic_time_calculations import get_vedic_day_schedule
            day_schedule = get_vedic_day_schedule(city=vedic_request.city, date=day_date)
            
            # Анализируем совместимость дня
            day_analysis = analyze_day_compatibility(day_date, user_data, day_schedule)
            
            # Добавляем полный анализ к дню
            day['compatibility_score'] = day_analysis.get('overall_score', 50)  # Используем overall_score
            day['positive_aspects'] = day_analysis.get('positive_aspects', [])[:3]  # Топ 3
            day['challenges'] = day_analysis.get('challenges', [])[:3]  # Топ 3
            day['key_advice'] = day_analysis.get('overall_description', '')[:200] + '...' if len(day_analysis.get('overall_description', '')) > 200 else day_analysis.get('overall_description', '')
            day['influence'] = day_analysis.get('influence', {})
            day['color_class'] = day_analysis.get('color_class', 'blue')
            
            # Добавляем информацию о личной энергии планеты дня (DDMM × YYYY)
            from numerology import calculate_planetary_strength
            ruling_planet = day.get('ruling_planet', 'Surya')
            
            try:
                birth_date_obj = datetime.strptime(user.birth_date, '%d.%m.%Y')
                planetary_strength_data = calculate_planetary_strength(
                    birth_date_obj.day, 
                    birth_date_obj.month, 
                    birth_date_obj.year
                )
                
                # Конвертируем русские названия в ведические
                russian_to_vedic = {
                    'Солнце': 'Surya',
                    'Луна': 'Chandra',
                    'Марс': 'Mangal',
                    'Меркурий': 'Budh',
                    'Юпитер': 'Guru',
                    'Венера': 'Shukra',
                    'Сатурн': 'Shani'
                }
                
                personal_weekday_energy = {
                    russian_to_vedic.get(k, k): v 
                    for k, v in planetary_strength_data.get('strength', {}).items()
                }
                
                # Добавляем энергию планеты дня
                day['personal_planet_energy'] = personal_weekday_energy.get(ruling_planet, -1)
                day['all_weekday_energies'] = personal_weekday_energy
                
            except Exception as e:
                print(f"⚠️ Ошибка расчёта энергии для дня {day['date']}: {e}")
                day['personal_planet_energy'] = -1
                day['all_weekday_energies'] = {}
            
            # Добавляем информацию о пользователе для отображения
            day['user_soul_number'] = soul_number
            day['user_mind_number'] = mind_number
            day['user_destiny_number'] = destiny_number
        
        return weekly_route
        
    except Exception as e:
        # Логируем ошибку для отладки
        import traceback
        print(f"❌ ОШИБКА в weekly_planetary_route: {str(e)}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        
        # Возвращаем баллы в случае ошибки
        config = await get_credits_deduction_config()
        cost = config.get('planetary_weekly', CREDIT_COSTS.get('planetary_weekly', 10))
        await record_credit_transaction(user_id, cost, 'Возврат за ошибку недельного маршрута', 'refund')
        await db.users.update_one({'id': user_id}, {'$inc': {'credits_remaining': cost}})
        raise HTTPException(status_code=400, detail=f'Ошибка расчета недельного маршрута: {str(e)}')

@api_router.get('/vedic-time/planetary-route/monthly')
async def monthly_planetary_route(vedic_request: VedicTimeRequest = Depends(), current_user: dict = Depends(get_current_user)):
    """Планетарный маршрут на месяц - 30 баллов"""
    user_id = current_user['user_id']
    
    # Получаем данные пользователя
    user_dict = await db.users.find_one({'id': user_id})
    if not user_dict:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    user = User(**user_dict)
    
    # Получаем стоимость из единой конфигурации
    config = await get_credits_deduction_config()
    cost = config.get('planetary_monthly', CREDIT_COSTS.get('planetary_monthly', 30))
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        cost, 
        'Планетарный маршрут на месяц', 
        'vedic',
        {'calculation_type': 'planetary_monthly', 'date': vedic_request.date}
    )
    
    if vedic_request.date:
        try:
            date_obj = datetime.strptime(vedic_request.date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        # Используем UTC время с timezone для корректной конвертации в локальное время города
        date_obj = datetime.now(pytz.UTC)

    city = vedic_request.city or user.city
    if not city:
        raise HTTPException(status_code=422, detail="Город не указан. Укажите город в запросе или обновите профиль пользователя.")
    
    try:
        # Prepare user data for enhanced calculation
        user_numbers = None
        pythagorean_square_data = None
        fractal_behavior = None
        problem_numbers = None
        name_numbers = None
        weekday_energy = None
        janma_ank_value = None
        
        if user.birth_date:
            try:
                day, month, year = parse_birth_date(user.birth_date)
                
                # Get personal numbers
                personal_numbers = calculate_personal_numbers(user.birth_date)
                user_numbers = {
                    'soul_number': personal_numbers.get('soul_number'),
                    'mind_number': personal_numbers.get('mind_number'),
                    'destiny_number': personal_numbers.get('destiny_number'),
                    'wisdom_number': personal_numbers.get('wisdom_number'),
                    'ruling_number': personal_numbers.get('ruling_number'),
                    'personal_day': personal_numbers.get('personal_day')
                }
                
                # Calculate Pythagorean Square
                pythagorean_square_data = create_pythagorean_square(day, month, year)
                
                # Calculate Janma Ank
                from vedic_numerology import calculate_janma_ank
                janma_ank_value = calculate_janma_ank(day, month, year)
                total_before_reduction = day + month + year
                if total_before_reduction == 22:
                    janma_ank_value = 22
                
                # Calculate fractal behavior
                day_reduced = reduce_to_single_digit(day)
                month_reduced = reduce_to_single_digit(month)
                year_reduced = reduce_to_single_digit(year)
                year_sum = reduce_to_single_digit(day + month + year)
                fractal_behavior = [day_reduced, month_reduced, year_reduced, year_sum]
                
                # Calculate problem numbers
                soul_num = user_numbers.get('soul_number', 1)
                mind_num = user_numbers.get('mind_number', 1)
                destiny_num = user_numbers.get('destiny_number', 1)
                problem1 = reduce_to_single_digit(abs(soul_num - mind_num))
                problem2 = reduce_to_single_digit(abs(soul_num - year_reduced))
                problem3 = reduce_to_single_digit(abs(problem1 - problem2))
                problem4 = reduce_to_single_digit(abs(mind_num - year_reduced))
                problem_numbers = [problem1, problem2, problem3, problem4]
                
                # Get name numbers if available
                if hasattr(user, 'full_name') and user.full_name:
                    from numerology import calculate_name_numerology
                    try:
                        name_data = calculate_name_numerology(user.full_name)
                        name_numbers = {
                            'first_name_number': name_data.get('first_name_number'),
                            'last_name_number': name_data.get('last_name_number'),
                            'total_name_number': name_data.get('total_name_number'),
                            'full_name_number': name_data.get('total_name_number')
                        }
                    except:
                        pass
                
                # Calculate weekday energy
                try:
                    from numerology import calculate_planetary_strength
                    planetary_strength_data = calculate_planetary_strength(day, month, year)
                    strength_dict = planetary_strength_data.get('strength', {})
                    planet_name_to_key = {
                        'Солнце': 'surya', 'Луна': 'chandra', 'Марс': 'mangal',
                        'Меркурий': 'budha', 'Юпитер': 'guru', 'Венера': 'shukra', 'Сатурн': 'shani'
                    }
                    weekday_energy = {}
                    for planet_name, energy_value in strength_dict.items():
                        planet_key = planet_name_to_key.get(planet_name)
                        if planet_key:
                            weekday_energy[planet_key] = float(energy_value)
                except:
                    pass
            except Exception as e:
                print(f"Error preparing enhanced calculation data: {e}")
        
        # Get modifiers config
        modifiers_config = await get_planetary_energy_modifiers_config()
        
        monthly_route = get_monthly_planetary_route(
            city=city, start_date=date_obj, birth_date=user.birth_date,
            user_numbers=user_numbers, pythagorean_square=pythagorean_square_data,
            fractal_behavior=fractal_behavior, problem_numbers=problem_numbers,
            name_numbers=name_numbers, weekday_energy=weekday_energy,
            janma_ank=janma_ank_value, modifiers_config=modifiers_config
        )
        return monthly_route
    except Exception as e:
        # Возвращаем баллы при ошибке
        config = await get_credits_deduction_config()
        cost = config.get('planetary_monthly', CREDIT_COSTS.get('planetary_monthly', 30))
        await record_credit_transaction(user_id, cost, 'Возврат за ошибку месячного маршрута', 'refund')
        await db.users.update_one({'id': user_id}, {'$inc': {'credits_remaining': cost}})
        raise HTTPException(status_code=400, detail=f'Ошибка расчета месячного маршрута: {str(e)}')
@api_router.get('/vedic-time/planetary-route/quarterly') 
async def quarterly_planetary_route(vedic_request: VedicTimeRequest = Depends(), current_user: dict = Depends(get_current_user)):
    """Планетарный маршрут на квартал - 100 баллов"""
    user_id = current_user['user_id']
    
    # Получаем данные пользователя
    user_dict = await db.users.find_one({'id': user_id})
    if not user_dict:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    user = User(**user_dict)
    
    # Получаем стоимость из единой конфигурации
    config = await get_credits_deduction_config()
    cost = config.get('planetary_quarterly', CREDIT_COSTS.get('planetary_quarterly', 100))
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        cost, 
        'Планетарный маршрут на квартал', 
        'vedic',
        {'calculation_type': 'planetary_quarterly', 'date': vedic_request.date}
    )
    
    if vedic_request.date:
        try:
            date_obj = datetime.strptime(vedic_request.date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        # Используем UTC время с timezone для корректной конвертации в локальное время города
        date_obj = datetime.now(pytz.UTC)

    city = vedic_request.city or user.city
    if not city:
        raise HTTPException(status_code=422, detail="Город не указан. Укажите город в запросе или обновите профиль пользователя.")
    
    try:
        # Prepare user data for enhanced calculation (same as monthly)
        user_numbers = None
        pythagorean_square_data = None
        fractal_behavior = None
        problem_numbers = None
        name_numbers = None
        weekday_energy = None
        janma_ank_value = None
        
        if user.birth_date:
            try:
                day, month, year = parse_birth_date(user.birth_date)
                
                # Get personal numbers
                personal_numbers = calculate_personal_numbers(user.birth_date)
                user_numbers = {
                    'soul_number': personal_numbers.get('soul_number'),
                    'mind_number': personal_numbers.get('mind_number'),
                    'destiny_number': personal_numbers.get('destiny_number'),
                    'wisdom_number': personal_numbers.get('wisdom_number'),
                    'ruling_number': personal_numbers.get('ruling_number'),
                    'personal_day': personal_numbers.get('personal_day')
                }
                
                # Calculate Pythagorean Square
                pythagorean_square_data = create_pythagorean_square(day, month, year)
                
                # Calculate Janma Ank
                from vedic_numerology import calculate_janma_ank
                janma_ank_value = calculate_janma_ank(day, month, year)
                total_before_reduction = day + month + year
                if total_before_reduction == 22:
                    janma_ank_value = 22
                
                # Calculate fractal behavior
                day_reduced = reduce_to_single_digit(day)
                month_reduced = reduce_to_single_digit(month)
                year_reduced = reduce_to_single_digit(year)
                year_sum = reduce_to_single_digit(day + month + year)
                fractal_behavior = [day_reduced, month_reduced, year_reduced, year_sum]
                
                # Calculate problem numbers
                soul_num = user_numbers.get('soul_number', 1)
                mind_num = user_numbers.get('mind_number', 1)
                destiny_num = user_numbers.get('destiny_number', 1)
                problem1 = reduce_to_single_digit(abs(soul_num - mind_num))
                problem2 = reduce_to_single_digit(abs(soul_num - year_reduced))
                problem3 = reduce_to_single_digit(abs(problem1 - problem2))
                problem4 = reduce_to_single_digit(abs(mind_num - year_reduced))
                problem_numbers = [problem1, problem2, problem3, problem4]
                
                # Get name numbers if available
                if hasattr(user, 'full_name') and user.full_name:
                    from numerology import calculate_name_numerology
                    try:
                        name_data = calculate_name_numerology(user.full_name)
                        name_numbers = {
                            'first_name_number': name_data.get('first_name_number'),
                            'last_name_number': name_data.get('last_name_number'),
                            'total_name_number': name_data.get('total_name_number'),
                            'full_name_number': name_data.get('total_name_number')
                        }
                    except:
                        pass
                
                # Calculate weekday energy
                try:
                    from numerology import calculate_planetary_strength
                    planetary_strength_data = calculate_planetary_strength(day, month, year)
                    strength_dict = planetary_strength_data.get('strength', {})
                    planet_name_to_key = {
                        'Солнце': 'surya', 'Луна': 'chandra', 'Марс': 'mangal',
                        'Меркурий': 'budha', 'Юпитер': 'guru', 'Венера': 'shukra', 'Сатурн': 'shani'
                    }
                    weekday_energy = {}
                    for planet_name, energy_value in strength_dict.items():
                        planet_key = planet_name_to_key.get(planet_name)
                        if planet_key:
                            weekday_energy[planet_key] = float(energy_value)
                except:
                    pass
            except Exception as e:
                print(f"Error preparing enhanced calculation data: {e}")
        
        # Get modifiers config
        modifiers_config = await get_planetary_energy_modifiers_config()
        
        quarterly_route = get_quarterly_planetary_route(
            city=city, start_date=date_obj, birth_date=user.birth_date,
            user_numbers=user_numbers, pythagorean_square=pythagorean_square_data,
            fractal_behavior=fractal_behavior, problem_numbers=problem_numbers,
            name_numbers=name_numbers, weekday_energy=weekday_energy,
            janma_ank=janma_ank_value, modifiers_config=modifiers_config
        )
        return quarterly_route
    except Exception as e:
        # Возвращаем баллы при ошибке
        config = await get_credits_deduction_config()
        cost = config.get('planetary_quarterly', CREDIT_COSTS.get('planetary_quarterly', 100))
        await record_credit_transaction(user_id, cost, 'Возврат за ошибку квартального маршрута', 'refund')
        await db.users.update_one({'id': user_id}, {'$inc': {'credits_remaining': cost}})
        raise HTTPException(status_code=400, detail=f'Ошибка расчета квартального маршрута: {str(e)}')

@api_router.get('/vedic-time/planetary-advice/{planet}')
async def get_planetary_hour_advice(
    planet: str,
    is_night: bool = Query(False, description="Ночной час или дневной"),
    current_user: dict = Depends(get_current_user)
):
    """
    Получить персонализированные советы для планетарного часа
    Бесплатно - не списываются баллы
    """
    user_id = current_user['user_id']
    
    # Получаем данные пользователя
    user_dict = await db.users.find_one({'id': user_id})
    if not user_dict:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    user = User(**user_dict)
    
    # Подготавливаем данные пользователя для персонализации
    user_data = {
        "birth_date": user.birth_date,
        "soul_number": None,
        "destiny_number": None,
        "mind_number": None,
        "ruling_number": None,
        "planet_counts": {}
    }
    
    # Если есть дата рождения, вычисляем числа
    if user.birth_date:
        try:
            # Парсим дату в разных форматах
            birth_date_str = str(user.birth_date)
            
            # Пробуем разные форматы
            if '.' in birth_date_str:
                # Формат DD.MM.YYYY
                parts = birth_date_str.split('.')
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                birth_date_obj = datetime(year, month, day)
            elif '-' in birth_date_str and len(birth_date_str) == 10:
                # Формат YYYY-MM-DD
                birth_date_obj = datetime.fromisoformat(birth_date_str)
                day, month, year = birth_date_obj.day, birth_date_obj.month, birth_date_obj.year
            else:
                # Пробуем ISO формат
                birth_date_obj = datetime.fromisoformat(birth_date_str)
                day, month, year = birth_date_obj.day, birth_date_obj.month, birth_date_obj.year
            
            print(f"📅 Дата рождения пользователя: {day}.{month}.{year}")
            
            # Вычисляем основные числа (с учетом мастер-чисел)
            def reduce_to_single_digit(num, keep_master=True):
                """Редуцирует число до однозначного, сохраняя мастер-числа 11, 22, 33"""
                if keep_master and num in [11, 22, 33]:
                    return num
                while num > 9:
                    num = sum(int(d) for d in str(num))
                    if keep_master and num in [11, 22, 33]:
                        return num
                return num
            
            def reduce_to_single_digit_always(num):
                """Редуцирует число до однозначного всегда, без мастер-чисел (для числа судьбы)"""
                while num > 9:
                    num = sum(int(d) for d in str(num))
                return num
            
            def reduce_for_ruling_number(num):
                """Редуцирует число для правящего числа - сохраняет только 11 и 22"""
                if num in [11, 22]:
                    return num
                while num > 9:
                    num = sum(int(d) for d in str(num))
                    if num in [11, 22]:
                        return num
                return num
            
            # Число души (день рождения)
            user_data["soul_number"] = reduce_to_single_digit(day)
            
            # Число судьбы (сумма всех цифр даты) - всегда сводится к одной цифре, без мастер-чисел
            full_date_sum = day + month + year
            user_data["destiny_number"] = reduce_to_single_digit_always(full_date_sum)
            
            # Число ума (месяц)
            user_data["mind_number"] = reduce_to_single_digit(month)
            
            # Правящее число (сумма всех цифр даты рождения) - может быть 11 или 22
            from numerology import calculate_ruling_number
            user_data["ruling_number"] = calculate_ruling_number(day, month, year)
            
            print(f"🔢 Число души: {user_data['soul_number']}")
            print(f"🔢 Число судьбы: {user_data['destiny_number']}")
            print(f"🔢 Число ума: {user_data['mind_number']}")
            print(f"🔢 Правящее число: {user_data['ruling_number']}")
            
            # Создаем квадрат Пифагора для подсчета силы планет (метод Александрова)
            birth_date_str = birth_date_obj.strftime("%d%m%Y")
            
            # Получаем цифры даты рождения (без нулей)
            birth_digits = [int(d) for d in birth_date_str if d != '0']
            
            # Вычисляем рабочие числа
            # 1-е рабочее число: сумма всех цифр даты рождения
            first_working = sum(birth_digits)
            
            # 2-е рабочее число: сумма цифр 1-го рабочего числа
            second_working = sum(int(d) for d in str(first_working))
            
            # 3-е рабочее число: 1-е рабочее - (2 × первая цифра даты)
            first_digit = int(birth_date_str[0])
            third_working = first_working - (2 * first_digit)
            
            # 4-е рабочее число: сумма цифр 3-го рабочего числа
            fourth_working = sum(int(d) for d in str(abs(third_working)))
            
            print(f"🔢 Рабочие числа: 1-е={first_working}, 2-е={second_working}, 3-е={third_working}, 4-е={fourth_working}")
            
            # Объединяем все цифры: дата рождения + рабочие числа
            all_digits = (
                birth_digits +
                [int(d) for d in str(first_working)] +
                [int(d) for d in str(second_working)] +
                [int(d) for d in str(abs(third_working))] +
                [int(d) for d in str(fourth_working)]
            )
            
            print(f"📊 Все цифры для анализа: {all_digits}")
            
            # Подсчитываем количество каждой цифры (1-9)
            digit_counts = {}
            for i in range(1, 10):
                digit_counts[str(i)] = all_digits.count(i)
            
            # Маппинг цифр на планеты
            planet_digit_map = {
                "Surya": "1",
                "Chandra": "2",
                "Guru": "3",
                "Rahu": "4",
                "Budh": "5",
                "Shukra": "6",
                "Ketu": "7",
                "Shani": "8",
                "Mangal": "9"
            }
            
            for planet_name, digit in planet_digit_map.items():
                user_data["planet_counts"][planet_name] = digit_counts.get(digit, 0)
            
            print(f"🌍 Сила планет: {user_data['planet_counts']}")
            print(f"🌟 Запрашиваемая планета: {planet}, сила: {user_data['planet_counts'].get(planet, 0)}")
            
            # Сохраняем дату рождения в user_data для дальнейшего анализа
            user_data["birth_date"] = birth_date_obj
        except Exception as e:
            print(f"❌ Ошибка при вычислении чисел: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🚀 Вызываем get_personalized_planetary_advice для {planet}")
    print(f"   user_data: {user_data}")
    
    # Получаем персонализированные советы
    advice = await get_personalized_planetary_advice(db, planet, user_data, is_night)
    
    if not advice:
        raise HTTPException(status_code=404, detail=f'Советы для планеты {planet} не найдены')
    
    return advice

# ----------------- CHARTS -----------------
@api_router.get('/charts/planetary-energy/{days}')
async def get_planetary_energy(days: int = 7, current_user: dict = Depends(get_current_user)):
    """Динамика энергии планет - списание баллов в зависимости от периода"""
    user_id = current_user['user_id']
    user_dict = await db.users.find_one({'id': user_id})
    if not user_dict:
        raise HTTPException(status_code=404, detail='User not found')
    user = User(**user_dict)
    
    # Определяем период и стоимость
    if days <= 7:
        period = 'weekly'
        cost_key = 'planetary_energy_weekly'
        description = 'Динамика энергии планет на неделю'
    elif days <= 30:
        period = 'monthly'
        cost_key = 'planetary_energy_monthly'
        description = 'Динамика энергии планет на месяц'
    else:
        period = 'quarterly'
        cost_key = 'planetary_energy_quarterly'
        description = 'Динамика энергии планет на квартал'
    
    # Получаем стоимость из единой конфигурации
    config = await get_credits_deduction_config()
    cost = config.get(cost_key, CREDIT_COSTS.get(cost_key, 10))
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id,
        cost,
        description,
        'numerology',
        {
            'calculation_type': 'planetary_energy',
            'period': period,
            'days': days,
            'cost_key': cost_key
        }
    )
    
    try:
        # Get user's personal numbers for enhanced calculation
        user_numbers = None
        pythagorean_square_data = None
        fractal_behavior = None
        problem_numbers = None
        name_numbers = None
        weekday_energy = None
        
        if user.birth_date:
            try:
                day, month, year = parse_birth_date(user.birth_date)
                
                # Get personal numbers
                personal_numbers = calculate_personal_numbers(user.birth_date)
                user_numbers = {
                    'soul_number': personal_numbers.get('soul_number'),
                    'mind_number': personal_numbers.get('mind_number'),
                    'destiny_number': personal_numbers.get('destiny_number'),
                    'wisdom_number': personal_numbers.get('wisdom_number'),
                    'ruling_number': personal_numbers.get('ruling_number'),
                    'personal_day': personal_numbers.get('personal_day')
                }
                
                # Calculate Pythagorean Square
                pythagorean_square_data = create_pythagorean_square(day, month, year)
                
                # Calculate Janma Ank (Life Path/Birth Number) - can be master number 22
                from vedic_numerology import calculate_janma_ank
                janma_ank_value = calculate_janma_ank(day, month, year)
                # Note: calculate_janma_ank uses reduce_to_single_digit which preserves 11, 22, 33
                # But we need to check if the sum before reduction was 22
                total_before_reduction = day + month + year
                if total_before_reduction == 22 or (total_before_reduction > 9 and reduce_to_single_digit(total_before_reduction) == 4 and total_before_reduction % 11 == 0):
                    # Check if it's actually 22 (master number)
                    if total_before_reduction == 22:
                        janma_ank_value = 22
                
                # Calculate fractal behavior (4 numbers: day, month, year reduced, sum)
                day_reduced = reduce_to_single_digit(day)
                month_reduced = reduce_to_single_digit(month)
                year_reduced = reduce_to_single_digit(year)
                year_sum = reduce_to_single_digit(day + month + year)
                fractal_behavior = [day_reduced, month_reduced, year_reduced, year_sum]
                
                # Calculate problem numbers (simplified - can be enhanced)
                # Problem numbers are calculated from personal numbers
                soul_num = user_numbers.get('soul_number', 1)
                mind_num = user_numbers.get('mind_number', 1)
                destiny_num = user_numbers.get('destiny_number', 1)
                year_num = year_reduced
                
                # Problem numbers calculation (simplified)
                problem1 = reduce_to_single_digit(abs(soul_num - mind_num))
                problem2 = reduce_to_single_digit(abs(soul_num - year_num))
                problem3 = reduce_to_single_digit(abs(problem1 - problem2))
                problem4 = reduce_to_single_digit(abs(mind_num - year_num))
                problem_numbers = [problem1, problem2, problem3, problem4]
                
                # Get name numbers if available
                if hasattr(user, 'full_name') and user.full_name:
                    # Calculate name numbers (name and surname separately)
                    from numerology import calculate_name_numerology
                    try:
                        name_data = calculate_name_numerology(user.full_name)
                        name_numbers = {
                            'first_name_number': name_data.get('first_name_number'),
                            'last_name_number': name_data.get('last_name_number'),
                            'total_name_number': name_data.get('total_name_number'),
                            'full_name_number': name_data.get('total_name_number')  # Alias
                        }
                    except:
                        # Fallback to simple calculation
                        try:
                            from numerology import calculate_full_name_number
                            name_num = calculate_full_name_number(user.full_name)
                            name_numbers = {'name_number': name_num, 'full_name_number': name_num}
                        except:
                            pass
                
                # Calculate weekday energy (personal energy by day of week)
                # This uses calculate_planetary_strength which calculates DDMM × YYYY
                try:
                    from numerology import calculate_planetary_strength
                    planetary_strength_data = calculate_planetary_strength(day, month, year)
                    strength_dict = planetary_strength_data.get('strength', {})
                    weekday_map = planetary_strength_data.get('weekday_map', {})
                    
                    # Map planet names to energy keys
                    planet_name_to_key = {
                        'Солнце': 'surya',
                        'Луна': 'chandra',
                        'Марс': 'mangal',
                        'Меркурий': 'budha',
                        'Юпитер': 'guru',
                        'Венера': 'shukra',
                        'Сатурн': 'shani'
                    }
                    
                    weekday_energy = {}
                    for planet_name, energy_value in strength_dict.items():
                        planet_key = planet_name_to_key.get(planet_name)
                        if planet_key:
                            weekday_energy[planet_key] = float(energy_value)
                except Exception as e:
                    print(f"Error calculating weekday energy: {e}")
                    weekday_energy = None
                
            except Exception as e:
                print(f"Error preparing enhanced calculation data: {e}")
                pass
        
        user_city = getattr(user, 'city', 'Москва') or 'Москва'
        # Get modifiers config
        modifiers_config = await get_planetary_energy_modifiers_config()
        
        # Start from today
        base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        chart_data = []
        
        # Generate data for the requested number of days
        weeks_needed = (days // 7) + (1 if days % 7 > 0 else 0)
        
        for week_idx in range(weeks_needed):
            # Calculate start date for this week
            week_start_date = base_date + timedelta(days=week_idx * 7)
            
            # Generate weekly data starting from this week's start date
            week_data = generate_weekly_planetary_energy(
                user.birth_date, user_numbers, user_city,
                pythagorean_square=pythagorean_square_data,
                fractal_behavior=fractal_behavior,
                problem_numbers=problem_numbers,
                name_numbers=name_numbers,
                weekday_energy=weekday_energy,
                janma_ank=janma_ank_value if 'janma_ank_value' in locals() else None,
                modifiers_config=modifiers_config,
                start_date=week_start_date
            )
            
            chart_data.extend(week_data)
            
            # Stop if we have enough days
            if len(chart_data) >= days:
                break
        
        # Trim to exact number of days requested
        chart_data = chart_data[:days]
        
        # Apply anti-cyclicity to the entire period (for month and quarter)
        if days > 7:
            from vedic_numerology import apply_anti_cyclicity_to_period
            chart_data = apply_anti_cyclicity_to_period(chart_data, modifiers_config)
        
        return {'chart_data': chart_data, 'period': f'{days} days', 'user_birth_date': user.birth_date}
    except Exception as e:
        # Возвращаем баллы при ошибке
        config = await get_credits_deduction_config()
        cost = config.get(cost_key, CREDIT_COSTS.get(cost_key, 10))
        await record_credit_transaction(user_id, cost, f'Возврат за ошибку {description}', 'refund')
        await db.users.update_one({'id': user_id}, {'$inc': {'credits_remaining': cost}})
        raise HTTPException(status_code=400, detail=f'Ошибка расчета динамики энергии планет: {str(e)}')

# ----------------- QUIZ -----------------
@api_router.get('/quiz/randomized-questions')
async def quiz_questions():
    from quiz_data import NUMEROLOGY_QUIZ
    import random
    questions = NUMEROLOGY_QUIZ['questions']
    random.shuffle(questions)
    return {
        'session_id': str(uuid.uuid4()),
        'title': NUMEROLOGY_QUIZ['title'],
        'description': NUMEROLOGY_QUIZ['description'],
        'questions': questions[:10]
    }

@api_router.post('/quiz/submit')
async def submit_quiz(answers: List[Dict[str, Any]], current_user: dict = Depends(get_current_user)):
    """Прохождение Quiz - 1 балл"""
    user_id = current_user['user_id']
    
    # Получаем стоимость из конфигурации
    config = await get_credits_deduction_config()
    cost = config.get('quiz_completion', CREDIT_COSTS.get('quiz_completion', 1))
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        cost, 
        'Прохождение викторины', 
        'quiz',
        {'quiz_type': 'numerology_assessment'}
    )
    
    from quiz_data import calculate_quiz_results
    results = calculate_quiz_results(answers)
    qr = QuizResult(user_id=user_id, quiz_type='numerology_assessment', answers=answers, score=results['total_score'], recommendations=results['recommendations'])
    await db.quiz_results.insert_one(qr.dict())
    return results

# ==================== НОВАЯ СИСТЕМА ОБУЧЕНИЯ V2 ====================

@app.post("/api/admin/lessons-v2/upload-from-file")
async def upload_lesson_from_file_v2(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Загрузить урок V2 из текстового файла с 5 разделами (дублированный эндпоинт)"""
    try:
        # Получаем полные данные пользователя из базы данных
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        # Читаем файл
        content = await file.read()
        text_content = content.decode('utf-8')

        # Парсим урок из файла
        lesson_data = parse_lesson_from_text_v2(text_content)

        # Сохраняем в базу данных
        lesson_dict = lesson_data.dict()
        lesson_dict['created_by'] = user.get('id', 'admin_system')
        lesson_dict['updated_by'] = user.get('id', 'admin_system')

        result = await db.lessons_v2.insert_one(lesson_dict)
        
        return {
            "message": "Урок V2 успешно загружен",
            "lesson_id": lesson_data.id,
            "sections": {
                "theory_blocks": len(lesson_data.theory),
                "exercises": len(lesson_data.exercises),
                "has_challenge": lesson_data.challenge is not None,
                "has_quiz": lesson_data.quiz is not None,
                "analytics_enabled": lesson_data.analytics_enabled
            }
        }
        
    except Exception as e:
        logger.error(f"Error uploading lesson V2: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading lesson: {str(e)}")

def parse_lesson_from_text_v2(text_content: str) -> 'LessonV2':
    """Парсить урок V2 из текстового файла"""
    from models import LessonV2, TheoryBlock, Exercise, Challenge, ChallengeDay, Quiz, QuizQuestion

    lines = text_content.split('\n')
    lesson_data = {
        'title': '',
        'description': '',
        'module': 'Основы нумерологии',
        'level': 1,
        'order': 0,
        'theory': [],
        'exercises': [],
        'challenge': None,
        'quiz': None
    }

    current_section = None
    current_block = None
    block_order = 0
    exercise_order = 0

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Заголовок урока
        if line.startswith('УРОК') and ('ЦИФРА' in line or 'ЧИСЛО' in line):
            # Парсим заголовок урока
            lesson_data['title'] = line
            i += 1
            continue

        # Разделы
        if '───────────────────────────────────────────────' in line:
            i += 1
            if i < len(lines):
                section_title = lines[i].strip().upper()
                if 'ВВЕДЕНИЕ' in section_title:
                    current_section = 'introduction'
                elif 'КЛЮЧЕВЫЕ КОНЦЕПЦИИ' in section_title:
                    current_section = 'key_concepts'
                elif 'ПРАКТИЧЕСКОЕ ПРИМЕНЕНИЕ' in section_title:
                    current_section = 'practical'
                elif 'УПРАЖНЕНИЯ' in section_title or 'ПРАКТИЧЕСКИЕ ЗАДАНИЯ' in section_title:
                    current_section = 'exercises'
                elif 'ЧЕЛЛЕНДЖ' in section_title or 'ВЫЗОВ' in section_title:
                    current_section = 'challenge'
                elif 'ТЕСТ' in section_title or 'ВОПРОСЫ' in section_title:
                    current_section = 'quiz'
            i += 1
            continue

        # Разделы, начинающиеся с "РАЗДЕЛ"
        elif line.startswith('РАЗДЕЛ'):
            section_title = line.strip().upper()
            if 'ЧЕЛЛЕНДЖ' in section_title or 'ВЫЗОВ' in section_title:
                current_section = 'challenge'
            elif 'ТЕСТ' in section_title or 'ВОПРОСЫ' in section_title:
                current_section = 'quiz'
            elif 'УПРАЖНЕНИЯ' in section_title or 'ПРАКТИЧЕСКИЕ ЗАДАНИЯ' in section_title:
                current_section = 'exercises'
            i += 1
            continue

        # Обрабатываем контент по разделам
        if current_section == 'introduction' and line:
            if not lesson_data['description']:
                lesson_data['description'] = line
            else:
                lesson_data['description'] += ' ' + line
        elif current_section in ['key_concepts', 'practical'] and line:
            # Создаем или добавляем к блоку теории
            if not current_block or current_block.get('title') != section_title:
                current_block = {
                    'title': section_title if 'section_title' in locals() else current_section.replace('_', ' ').title(),
                    'content': line,
                    'order': block_order
                }
                lesson_data['theory'].append(current_block)
                block_order += 1
            else:
                current_block['content'] += '\n' + line

        elif current_section == 'exercises' and line.startswith('УПРАЖНЕНИЕ') or line.startswith('ЗАДАНИЕ'):
            # Создаем упражнение
            exercise = {
                'title': line,
                'description': '',
                'type': 'reflection',
                'instructions': '',
                'expected_outcome': '',
                'order': exercise_order
            }

            # Читаем описание упражнения
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('УПРАЖНЕНИЕ') and not lines[i].strip().startswith('───────────────────────────────────────────────'):
                if lines[i].strip():
                    exercise['instructions'] += lines[i].strip() + '\n'
                i += 1

            lesson_data['exercises'].append(exercise)
            exercise_order += 1
            continue

        elif current_section == 'challenge' and line:
            # Обрабатываем челлендж
            if not lesson_data['challenge']:
                lesson_data['challenge'] = {
                    'title': '7-дневный челлендж',
                    'description': '',
                    'duration_days': 7,
                    'daily_tasks': []
                }

            # Ищем заголовки дней
            if any(day in line.upper() for day in ['ПОНЕДЕЛЬНИК', 'ВТОРНИК', 'СРЕДА', 'ЧЕТВЕРГ', 'ПЯТНИЦА', 'СУББОТА', 'ВОСКРЕСЕНЬЕ']):
                # Это новый день челленджа
                day_name = line.upper()
                day_number = len(lesson_data['challenge']['daily_tasks']) + 1

                # Читаем задачи для этого дня
                tasks = []
                i += 1
                while i < len(lines) and not any(d in lines[i].upper() for d in ['ПОНЕДЕЛЬНИК', 'ВТОРНИК', 'СРЕДА', 'ЧЕТВЕРГ', 'ПЯТНИЦА', 'СУББОТА', 'ВОСКРЕСЕНЬЕ']) and not '───────────────────────────────────────────────' in lines[i]:
                    if lines[i].strip() and lines[i].strip()[0].isdigit():
                        tasks.append(lines[i].strip())
                    i += 1

                lesson_data['challenge']['daily_tasks'].append({
                    'day': day_number,
                    'title': day_name,
                    'description': f'Задачи для {day_name.lower()}:',
                    'tasks': tasks
                })
                continue

            elif not lesson_data['challenge']['description']:
                lesson_data['challenge']['description'] += line + '\n'

        elif current_section == 'quiz' and line:
            # Обрабатываем тест
            if not lesson_data['quiz']:
                lesson_data['quiz'] = {
                    'title': 'Тест по материалу урока',
                    'description': 'Проверьте свои знания',
                    'questions': [],
                    'passing_score': 70
                }

            # Ищем вопросы (начинаются с цифры и точки)
            if line.strip() and line.strip()[0].isdigit() and line.strip().split('.')[0].isdigit():
                question_text = line.strip().split('.', 1)[1].strip() if '.' in line else line.strip()

                # Читаем варианты ответов
                options = []
                i += 1
                while i < len(lines) and not (lines[i].strip() and lines[i].strip()[0].isdigit() and '───' not in lines[i]):
                    option_line = lines[i].strip()
                    if option_line.startswith(('A.', 'B.', 'C.', 'D.', 'E.')):
                        option_text = option_line[2:].strip()
                        options.append(option_text)
                    i += 1

                if question_text and options:
                    lesson_data['quiz']['questions'].append({
                        'question': question_text,
                        'type': 'multiple_choice',
                        'options': options,
                        'correct_answer': options[0] if options else '',  # Пока первый вариант
                        'explanation': 'Правильный ответ',
                        'points': 1
                    })
                continue

        i += 1

    # Создаем объекты моделей
    theory_blocks = [
        TheoryBlock(
            title=block['title'],
            content=block['content'],
            order=block['order']
        ) for block in lesson_data['theory']
    ]

    exercises = [
        Exercise(
            title=ex['title'],
            description=ex['instructions'][:200] + '...' if len(ex['instructions']) > 200 else ex['instructions'],
            type='reflection',
            instructions=ex['instructions'],
            expected_outcome='Осознание и применение полученных знаний',
            order=ex['order']
        ) for ex in lesson_data['exercises']
    ]

    # Создаем челлендж, если есть данные
    challenge_obj = None
    if lesson_data['challenge'] and lesson_data['challenge']['daily_tasks']:
        daily_tasks = [
            ChallengeDay(
                day=task['day'],
                title=task['title'],
                description=task['description'],
                tasks=task['tasks']
            ) for task in lesson_data['challenge']['daily_tasks']
        ]
        challenge_obj = Challenge(
            title=lesson_data['challenge']['title'],
            description=lesson_data['challenge']['description'],
            duration_days=lesson_data['challenge']['duration_days'],
            daily_tasks=daily_tasks
        )

    # Создаем тест, если есть данные
    quiz_obj = None
    if lesson_data['quiz'] and lesson_data['quiz']['questions']:
        questions = [
            QuizQuestion(
                question=q['question'],
                type=q['type'],
                options=q['options'],
                correct_answer=q['correct_answer'],
                explanation=q['explanation'],
                points=q['points']
            ) for q in lesson_data['quiz']['questions']
        ]
        quiz_obj = Quiz(
            title=lesson_data['quiz']['title'],
            description=lesson_data['quiz']['description'],
            questions=questions,
            passing_score=lesson_data['quiz']['passing_score']
        )

    # Создаем урок V2
    lesson = LessonV2(
        title=lesson_data['title'],
        description=lesson_data['description'],
        module=lesson_data['module'],
        level=lesson_data['level'],
        order=lesson_data['order'],
        theory=theory_blocks,
        exercises=exercises,
        challenge=challenge_obj,
        quiz=quiz_obj,
        created_by="admin_system",
        updated_by="admin_system"
    )

    return lesson

# ==================== ADMIN API ====================

@app.get("/api/admin/users")
async def get_all_users(current_user: dict = Depends(get_current_user)):
    """Получить всех пользователей для админа"""
    try:
        # Получаем полные данные пользователя из базы данных
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        # Получаем всех пользователей
        users = await db.users.find({}).to_list(1000)

        users_list = []
        for user_doc in users:
            user_dict = dict(user_doc)
            user_dict.pop('_id', None)
            user_dict.pop('password_hash', None)  # Не показываем хэш пароля
            users_list.append(user_dict)

        return {"users": users_list}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting users: {str(e)}")

@app.patch("/api/admin/users/{target_user_id}/credits")
async def update_user_credits(
    target_user_id: str,
    request_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Обновить кредиты пользователя (администратор)"""
    try:
        # Проверка прав администратора
        admin_user_id = current_user.get("user_id")
        if not admin_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        admin_user = await db.users.find_one({"id": admin_user_id})
        if not admin_user:
            raise HTTPException(status_code=404, detail="Admin user not found")

        if not admin_user.get('is_super_admin', False) and not admin_user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        # Получаем целевого пользователя
        target_user = await db.users.find_one({"id": target_user_id})
        if not target_user:
            raise HTTPException(status_code=404, detail="Target user not found")

        # Получаем новое значение кредитов
        new_credits = request_data.get("credits_remaining")
        if new_credits is None:
            raise HTTPException(status_code=400, detail="credits_remaining is required")

        new_credits = int(new_credits)
        old_credits = target_user.get("credits_remaining", 0)
        credits_difference = new_credits - old_credits

        # Обновляем кредиты
        await db.users.update_one(
            {"id": target_user_id},
            {"$set": {"credits_remaining": new_credits}}
        )

        # Записываем транзакцию в историю
        if credits_difference != 0:
            await record_credit_transaction(
                user_id=target_user_id,
                amount=credits_difference,
                description=f"Изменение баланса администратором {admin_user.get('email', admin_user_id)}",
                category='admin',
                details={
                    'added_by_admin': True,
                    'admin_user_id': admin_user_id,
                    'admin_email': admin_user.get('email', ''),
                    'old_credits': old_credits,
                    'new_credits': new_credits,
                    'difference': credits_difference
                }
            )

        return {
            "message": "Кредиты успешно обновлены",
            "old_credits": old_credits,
            "new_credits": new_credits,
            "difference": credits_difference
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user credits: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error updating user credits: {str(e)}")

# ==================== API УРОКОВ V2 ====================

@app.get("/api/admin/lessons-v2/{lesson_id}")
async def get_lesson_v2_admin(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Получить урок V2 по ID"""
    try:
        # Получаем полные данные пользователя из базы данных
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        lesson = await db.lessons_v2.find_one({"id": lesson_id})
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        lesson_dict = dict(lesson)
        lesson_dict.pop('_id', None)

        return {"lesson": lesson_dict}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lesson V2: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting lesson: {str(e)}")

# REMOVED: First upload_lesson_file_v2 function (conflicts with the second one)
# Function body removed - conflicts with duplicate function below
        # Получаем полные данные пользователя из базы данных
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        # Проверяем существование урока
        lesson = await db.lessons_v2.find_one({"id": lesson_id})
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        # Сохраняем файл
        file_content = await file.read()
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"

        # Определяем тип файла
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension in ['mp4', 'avi', 'mov', 'mp3', 'wav']:
            file_type = 'media'
            detailed_type = 'video' if file_extension in ['mp4', 'avi', 'mov'] else 'audio'
        elif file_extension in ['pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx']:
            file_type = 'document'
            if file_extension == 'pdf':
                detailed_type = 'pdf'
            elif file_extension in ['doc', 'docx']:
                detailed_type = 'word'
            elif file_extension == 'txt':
                detailed_type = 'txt'
            elif file_extension in ['xls', 'xlsx']:
                detailed_type = 'excel'
            else:
                detailed_type = 'other'
        else:
            file_type = 'other'
            detailed_type = 'other'

        # Сохраняем файл на диск
        import os
        upload_dir = f"uploads/lessons_v2/{lesson_id}"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, filename)
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Создаем запись о файле
        from models import LessonFile
        lesson_file = LessonFile(
            filename=filename,
            original_filename=file.filename,
            file_type=detailed_type,  # Сохраняем детальный тип для урока
            file_size=len(file_content),
            lesson_section=section
        )

        # Добавляем файл к уроку
        await db.lessons_v2.update_one(
            {"id": lesson_id},
            {"$push": {"files": lesson_file.dict()}}
        )

        # Также сохраняем в коллекцию files для статистики
        file_record = {
            "id": lesson_file.id,
            "lesson_id": lesson_id,
            "filename": filename,
            "original_name": file.filename,
            "stored_name": filename,
            "file_type": file_type,  # Сохраняем общий тип (media/document) для статистики
            "detailed_type": detailed_type,  # Детальный тип для совместимости
            "section": section,
            "file_size": len(file_content),
            "mime_type": file.content_type,
            "extension": file_extension,
            "uploaded_by": user_id,
            "uploaded_at": datetime.utcnow()
        }

        await db.files.insert_one(file_record)
        
        return {
            "message": "Файл успешно загружен",
            "file_id": lesson_file.id,
            "filename": filename,
            "file_type": file_type
        }
        
    except Exception as e:
        logger.error(f"Error uploading file to lesson V2: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

# ==================== API ДЛЯ СТУДЕНТОВ V2 ====================

@app.get("/api/learning-v2/lessons")
async def get_all_lessons_v2_student(current_user: dict = Depends(get_current_user)):
    """Получить все доступные уроки V2 для студентов"""
    try:
        logger.info(f"get_all_lessons_v2_student called, current_user: {current_user}")
        user_id = current_user.get('user_id') or current_user.get('id')
        if not user_id:
            logger.error(f"Invalid current_user object: {current_user}")
            raise HTTPException(status_code=401, detail="Invalid token")

        # Проверяем уровень пользователя
        user = await db.users.find_one({'id': user_id})
        user_level = user.get('level', 1) if user else 1

        # Получаем активные уроки до текущего уровня пользователя
        # Временно убираем фильтр по уровню, чтобы показывать все активные уроки
        # TODO: Восстановить фильтр по уровню после настройки системы уровней
        lessons = await db.lessons_v2.find({
            "is_active": True
        }).sort("order", 1).to_list(1000)

        lessons_list = []
        for lesson in lessons:
            lesson_dict = dict(lesson)
            lesson_dict.pop('_id', None)
            # Убираем чувствительную информацию
            lesson_dict.pop('created_by', None)
            lesson_dict.pop('updated_by', None)
            lessons_list.append(lesson_dict)
        
        logger.info(f"Returning {len(lessons_list)} lessons for user {user_id} (level {user_level})")
        return {
            "lessons": lessons_list,
            "user_level": user_level
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lessons V2 for student: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting lessons: {str(e)}")

@app.get("/api/learning-v2/lessons/{lesson_id}")
async def get_lesson_v2_student(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Получить урок V2 для студента"""
    try:
        user_id = current_user['user_id']

        lesson = await db.lessons_v2.find_one({"id": lesson_id, "is_active": True})
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        lesson_dict = dict(lesson)
        lesson_dict.pop('_id', None)
        lesson_dict.pop('created_by', None)
        lesson_dict.pop('updated_by', None)

        # Получаем прогресс пользователя по уроку
        progress = await db.lesson_progress_v2.find_one({
            "lesson_id": lesson_id,
            "user_id": user_id
        })
        
        return {
            "lesson": lesson_dict,
            "progress": progress or {}
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lesson V2 for student: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting lesson: {str(e)}")

# ==================== ADMIN: GET LESSONS ====================

@app.get("/api/admin/lessons")
async def get_all_lessons_admin(current_user: dict = Depends(get_current_user)):
    """Получить список всех уроков для админа из единой коллекции"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Получить все уроки из единой коллекции MongoDB
        all_lessons = await db.lessons.find({}).sort("order", 1).to_list(1000)

        lessons_list = []
        for lesson in all_lessons:
            lessons_list.append({
                "id": lesson["id"],
                "title": lesson.get("title", "Без названия"),
                "module": lesson.get("module", "numerology"),
                "points_required": lesson.get("points_required", 0),
                "is_active": lesson.get("is_active", True)
            })

        logger.info(f"Returning {len(lessons_list)} lessons from unified collection")
        return {"lessons": lessons_list}
    except Exception as e:
        logger.error(f"Error getting all lessons: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting all lessons: {str(e)}")

@app.get("/api/admin/lessons/{lesson_id}")
async def get_lesson_admin(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Получить урок со всеми кастомными изменениями для редактирования"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Получить урок из единой коллекции
        lesson = await db.lessons.find_one({"id": lesson_id})

        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        # Преобразуем в словарь и удаляем MongoDB ObjectId
        lesson_dict = dict(lesson)
        lesson_dict.pop('_id', None)

        logger.info(f"Loaded lesson {lesson_id} from unified collection")
        return {"lesson": lesson_dict}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lesson for admin: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting lesson for admin: {str(e)}")

async def create_lesson(
    lesson_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Создать новый урок"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Проверяем обязательные поля
        if not lesson_data.get("id") or not lesson_data.get("title"):
            raise HTTPException(status_code=400, detail="Missing required fields: id and title")

        # Проверяем, не существует ли урок с таким ID
        existing_lesson = await db.lessons.find_one({"id": lesson_data["id"]})
        if existing_lesson:
            raise HTTPException(status_code=400, detail=f"Lesson with id {lesson_data['id']} already exists")

        # Создаем новый урок
        new_lesson = {
            "id": lesson_data["id"],
            "title": lesson_data["title"],
            "module": lesson_data.get("module", "numerology"),
            "description": lesson_data.get("description", ""),
            "points_required": lesson_data.get("points_required", 0),
            "is_active": lesson_data.get("is_active", True),
            "content": lesson_data.get("content", {}),
            "exercises": lesson_data.get("exercises", []),
            "quiz": lesson_data.get("quiz"),
            "challenges": lesson_data.get("challenges", []),
            "additional_pdfs": lesson_data.get("additional_pdfs", []),
            "additional_resources": lesson_data.get("additional_resources", []),
            "video_file_id": lesson_data.get("video_file_id"),
            "video_filename": lesson_data.get("video_filename"),
            "pdf_file_id": lesson_data.get("pdf_file_id"),
            "pdf_filename": lesson_data.get("pdf_filename"),
            "word_file_id": lesson_data.get("word_file_id"),
            "word_filename": lesson_data.get("word_filename"),
            "level": lesson_data.get("level", 1),
            "order": lesson_data.get("order", 0),
            "created_at": lesson_data.get("created_at"),
            "created_by": admin_user["id"]
        }

        # Сохраняем в единой коллекции MongoDB
        print(f"DEBUG: Saving lesson data to unified collection: additional_resources={len(new_lesson.get('additional_resources', []))}, additional_pdfs={len(new_lesson.get('additional_pdfs', []))}")
        result = await db.lessons.insert_one(new_lesson)
        print(f"DEBUG: Created new lesson {lesson_data['id']} in unified collection")
        print(f"DEBUG: Saved lesson keys: {list(new_lesson.keys())}")

        # Проверим, что сохранилось
        saved_lesson = await db.lessons.find_one({"id": lesson_data["id"]})
        if saved_lesson:
            print(f"DEBUG: Verified saved lesson has additional_resources: {len(saved_lesson.get('additional_resources', []))}")
            print(f"DEBUG: Verified saved lesson has additional_pdfs: {len(saved_lesson.get('additional_pdfs', []))}")

        return {
            "message": "Lesson created successfully",
            "lesson_id": lesson_data["id"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating lesson: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating lesson: {str(e)}")

@app.put("/api/admin/lessons/{lesson_id}")
async def update_lesson(
    lesson_id: str,
    lesson_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Обновить существующий урок в единой коллекции"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Проверяем, существует ли урок в единой коллекции
        existing_lesson = await db.lessons.find_one({"id": lesson_id})

        if not existing_lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        # Подготавливаем данные для обновления
        update_data = {
            "updated_at": datetime.utcnow().isoformat(),
            "updated_by": admin_user["id"]
        }

        # Обновляем поля, которые переданы в lesson_data
        updateable_fields = [
            "title", "module", "description", "points_required", "is_active",
            "content", "exercises", "quiz", "challenges", "level", "order",
            "additional_pdfs", "additional_resources",
            "video_file_id", "video_filename", "pdf_file_id", "pdf_filename",
            "word_file_id", "word_filename", "word_url"
        ]

        for field in updateable_fields:
            if field in lesson_data:
                update_data[field] = lesson_data[field]

        await db.lessons.update_one(
            {"id": lesson_id},
            {"$set": update_data}
        )

        logger.info(f"Updated lesson {lesson_id} in unified collection")
        return {
            "message": "Lesson updated successfully",
            "lesson_id": lesson_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating lesson: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating lesson: {str(e)}")

@app.delete("/api/admin/lessons/{lesson_id}")
async def delete_lesson(
    lesson_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Удалить урок из единой коллекции"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Нельзя удалить первый урок
        if lesson_id == "lesson_numerom_intro":
            raise HTTPException(status_code=403, detail="Cannot delete the first lesson")

        # Проверяем, существует ли урок
        existing_lesson = await db.lessons.find_one({"id": lesson_id})
        if not existing_lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        # Удаляем из единой коллекции
        result = await db.lessons.delete_one({"id": lesson_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Lesson not found")

        # Также удаляем все связанные данные
        await db.lesson_content.delete_many({"lesson_id": lesson_id})
        await db.lesson_exercises.delete_many({"lesson_id": lesson_id})
        await db.lesson_quiz_questions.delete_many({"lesson_id": lesson_id})
        await db.lesson_challenge_days.delete_many({"lesson_id": lesson_id})
        await db.lessons.delete_many({"id": lesson_id})

        logger.info(f"Deleted lesson {lesson_id} by admin {admin_user['id']}")
        
        return {
            "message": "Lesson deleted successfully",
            "lesson_id": lesson_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting lesson: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting lesson: {str(e)}")

@app.get("/api/admin/lesson-content/{lesson_id}")
# ==================== THEORY SECTIONS MANAGEMENT ====================

@app.get("/api/admin/theory-sections")
async def get_theory_sections(current_user: dict = Depends(get_current_user)):
    """Получение списка кастомных разделов теории"""
    try:
        # Проверяем права администратора
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Получаем кастомные разделы теории из базы
        theory_sections = await db.lesson_theory_sections.find({}).to_list(None)
        
        # Преобразуем ObjectId в строку
        for section in theory_sections:
            section['id'] = str(section['_id'])
            del section['_id']
        
        return {
            "theory_sections": theory_sections,
            "count": len(theory_sections)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting theory sections: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting theory sections: {str(e)}")

@app.post("/api/admin/add-theory-section")
async def add_theory_section(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Добавление нового раздела теории"""
    try:
        # Проверяем права администратора
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        title = request.get('title', '').strip()
        content = request.get('content', '').strip()
        lesson_id = request.get('lesson_id', 'lesson_numerom_intro')
        
        if not title or not content:
            raise HTTPException(status_code=400, detail="Название и содержание обязательны")
        
        # Создаем новый раздел теории
        section_data = {
            'title': title,
            'content': content,
            'lesson_id': lesson_id,
            'created_by': current_user['user_id'],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Сохраняем в базе данных
        result = await db.lesson_theory_sections.insert_one(section_data)
        section_id = str(result.inserted_id)
        
        return {
            "success": True,
            "section_id": section_id,
            "message": "Раздел теории успешно создан"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding theory section: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding theory section: {str(e)}")

@app.post("/api/admin/update-theory-section")
async def update_theory_section(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Обновление раздела теории"""
    try:
        # Проверяем права администратора
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        section_id = request.get('section_id', '').strip()
        title = request.get('title', '').strip()
        content = request.get('content', '').strip()
        
        if not section_id or not title or not content:
            raise HTTPException(status_code=400, detail="ID раздела, название и содержание обязательны")
        
        # Проверяем существование раздела
        try:
            from bson import ObjectId
            section_object_id = ObjectId(section_id)
        except:
            raise HTTPException(status_code=400, detail="Неверный ID раздела")
        
        existing_section = await db.lesson_theory_sections.find_one({"_id": section_object_id})
        if not existing_section:
            raise HTTPException(status_code=404, detail="Раздел не найден")
        
        # Обновляем раздел
        update_data = {
            'title': title,
            'content': content,
            'updated_at': datetime.now().isoformat(),
            'updated_by': current_user['user_id']
        }
        
        await db.lesson_theory_sections.update_one(
            {"_id": section_object_id},
            {"$set": update_data}
        )
        
        return {
            "success": True,
            "message": "Раздел теории успешно обновлен"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating theory section: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating theory section: {str(e)}")

@app.delete("/api/admin/delete-theory-section/{section_id}")
async def delete_theory_section(
    section_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Удаление раздела теории"""
    try:
        # Проверяем права администратора
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Проверяем валидность ID
        try:
            from bson import ObjectId
            section_object_id = ObjectId(section_id)
        except:
            raise HTTPException(status_code=400, detail="Неверный ID раздела")
        
        # Проверяем существование раздела
        existing_section = await db.lesson_theory_sections.find_one({"_id": section_object_id})
        if not existing_section:
            raise HTTPException(status_code=404, detail="Раздел не найден")
        
        # Удаляем раздел
        await db.lesson_theory_sections.delete_one({"_id": section_object_id})
        
        return {
            "success": True,
            "message": "Раздел теории успешно удален"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting theory section: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting theory section: {str(e)}")

# ==================== END THEORY SECTIONS ====================

# ==================== PUSH NOTIFICATIONS ====================

@app.post("/api/push/subscribe")
async def subscribe_to_push(
    subscription_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Подписка пользователя на push уведомления"""
    try:
        result = await push_manager.save_subscription(
            user_id=current_user['id'],
            subscription_data=subscription_data,
            notification_time=subscription_data.get('notificationTime', '10:00'),
            timezone=subscription_data.get('timezone', 'Europe/Moscow')
        )

        return {
            "success": True,
            "message": "Подписка на уведомления успешно создана"
        }
    except Exception as e:
        logger.error(f"Error subscribing to push: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/push/vapid-public-key")
async def get_vapid_public_key():
    """Получить публичный VAPID ключ для фронтенда"""
    return {
        "publicKey": push_manager.vapid_public_key
    }


@app.get("/api/push/subscriptions")
async def get_user_push_subscriptions(
    current_user: dict = Depends(get_current_user)
):
    """Получить все подписки пользователя"""
    try:
        subscriptions = await push_manager.get_user_subscriptions(current_user['id'])
        return {
            "subscriptions": subscriptions
        }
    except Exception as e:
        logger.error(f"Error getting subscriptions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/push/unsubscribe")
async def unsubscribe_from_push(
    endpoint: str,
    current_user: dict = Depends(get_current_user)
):
    """Отписаться от push уведомлений"""
    try:
        success = await push_manager.remove_subscription(
            user_id=current_user['id'],
            endpoint=endpoint
        )

        if success:
            return {
                "success": True,
                "message": "Подписка успешно удалена"
            }
        else:
            raise HTTPException(status_code=404, detail="Подписка не найдена")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/push/update-settings")
async def update_push_settings(
    settings: dict,
    current_user: dict = Depends(get_current_user)
):
    """Обновить настройки push уведомлений"""
    try:
        endpoint = settings.get('endpoint')
        if not endpoint:
            raise HTTPException(status_code=400, detail="Endpoint required")

        update_data = {}
        if 'notificationTime' in settings:
            update_data['notification_time'] = settings['notificationTime']
        if 'timezone' in settings:
            update_data['timezone'] = settings['timezone']
        if 'enabled' in settings:
            update_data['enabled'] = settings['enabled']

        success = await push_manager.update_subscription_settings(
            user_id=current_user['id'],
            endpoint=endpoint,
            **update_data
        )

        if success:
            return {
                "success": True,
                "message": "Настройки успешно обновлены"
            }
        else:
            raise HTTPException(status_code=404, detail="Подписка не найдена")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/push/start-challenge-notifications")
async def start_challenge_notifications(
    lesson_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Начать отправку уведомлений для челленджа"""
    try:
        success = await push_manager.start_challenge_notifications(
            user_id=current_user['id'],
            lesson_id=lesson_id
        )

        return {
            "success": True,
            "message": "Уведомления для челленджа активированы"
        }
    except Exception as e:
        logger.error(f"Error starting challenge notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/push/stop-challenge-notifications")
async def stop_challenge_notifications(
    current_user: dict = Depends(get_current_user)
):
    """Остановить отправку уведомлений для челленджа"""
    try:
        success = await push_manager.stop_challenge_notifications(current_user['id'])

        return {
            "success": True,
            "message": "Уведомления для челленджа отключены"
        }
    except Exception as e:
        logger.error(f"Error stopping challenge notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/push/send-test")
async def send_test_notification(
    current_user: dict = Depends(get_current_user)
):
    """Отправить тестовое уведомление"""
    try:
        subscriptions = await push_manager.get_user_subscriptions(current_user['id'])

        if not subscriptions:
            raise HTTPException(status_code=404, detail="Нет активных подписок")

        sent_count = 0
        for subscription in subscriptions:
            success = push_manager.send_notification(
                subscription_info=subscription,
                title="Тестовое уведомление NumerOM",
                body="Push-уведомления работают! 🎉",
                url="/"
            )
            if success:
                sent_count += 1
        
        return {
            "success": True,
            "message": f"Отправлено {sent_count} уведомлений"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== END PUSH NOTIFICATIONS ====================

# Include router and middleware at the end to ensure all endpoints are registered
app.include_router(api_router)

# Bunny.net Stream integration
try:
    from bunny_endpoints import bunny_router
    from bunny_manual_link import manual_link_router
    app.include_router(bunny_router)
    app.include_router(manual_link_router)
    logger.info("Bunny.net Stream endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"Bunny.net endpoints not loaded: {e}. Install httpx to enable Bunny.net integration.")
except Exception as e:
    logger.error(f"Error loading Bunny.net endpoints: {e}")

raw_origins = os.environ.get('CORS_ORIGINS', '')
allowed_origins = [origin.strip() for origin in raw_origins.split(',') if origin.strip()]
if not allowed_origins:
    allowed_origins = ["http://localhost:3000"]
origin_regex = os.environ.get('CORS_ORIGIN_REGEX') or None
compiled_origin_regex = re.compile(origin_regex) if origin_regex else None
print(f"[CORS] allow_origins={allowed_origins}, regex={origin_regex}")

@app.middleware("http")
async def custom_cors_handler(request, call_next):
    origin = request.headers.get("origin")
    access_control_request_method = request.headers.get("access-control-request-method")
    access_control_request_headers = request.headers.get("access-control-request-headers")

    if request.method == "OPTIONS":
        print(f"[CORS middleware] OPTIONS origin={origin} method={access_control_request_method} headers={access_control_request_headers}")

    is_allowed_origin = False
    if origin:
        if origin in allowed_origins:
            is_allowed_origin = True
        elif compiled_origin_regex and compiled_origin_regex.match(origin):
            is_allowed_origin = True

    if request.method == "OPTIONS" and origin:
        print(f"[CORS middleware] OPTIONS is_allowed_origin={is_allowed_origin} for {origin}")
        if not is_allowed_origin:
            return Response("Disallowed CORS origin", status_code=400)

        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": access_control_request_method or "GET,POST,PUT,DELETE,OPTIONS,PATCH",
            "Access-Control-Allow-Headers": access_control_request_headers or "Authorization,Content-Type",
            "Access-Control-Max-Age": "600",
            "Vary": "Origin",
        }
        return Response(status_code=200, headers=headers)
    
    # Обрабатываем обычные запросы - добавляем CORS заголовки к ответу
    response = await call_next(request)
    
    # Добавляем CORS заголовки к ответу, если origin разрешен
    if origin and is_allowed_origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers.setdefault("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS,PATCH")
        response.headers.setdefault("Access-Control-Allow-Headers", "Authorization,Content-Type")
        vary_header = response.headers.get("Vary")
        if vary_header:
            if "Origin" not in vary_header:
                response.headers["Vary"] = f"{vary_header}, Origin"
        else:
            response.headers["Vary"] = "Origin"
    elif not origin:
        # Если нет origin (например, запрос из того же домена), разрешаем
        response.headers["Access-Control-Allow-Origin"] = "*"
    
    return response

# ===== LEARNING SYSTEM V2 ENDPOINTS =====
# Интеграция системы обучения V2 в основной проект

# Простая аутентификация для тестирования системы обучения V2
@app.post("/api/auth/login-v2")
async def login_v2(request_data: dict):
    """Простая аутентификация для системы обучения V2"""
    email = request_data.get("email", "")
    password = request_data.get("password", "")

    # Для тестирования принимаем любые credentials
    # В реальной системе здесь должна быть проверка с основной БД
    if email and password:
        # Создаем тестовый токен
        test_token = create_access_token({"sub": email, "user_id": "test_user_v2", "is_admin": True})

        return {
            "access_token": test_token,
            "token_type": "bearer",
            "user": {
                "id": "test_user_v2",
                "email": email,
                "name": "Test User V2",
                "is_admin": True,
                "is_super_admin": True
            }
        }

    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/user/profile-v2")
async def get_user_profile_v2(current_user: dict = Depends(get_current_user)):
    """Получить профиль пользователя для системы обучения V2"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Получаем реальные данные пользователя из базы данных
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Удаляем MongoDB _id перед возвратом
        user_dict = dict(user)
        user_dict.pop("_id", None)
        
        # Возвращаем все поля пользователя, включая личные данные
        return {
            "id": user_dict.get("id", ""),
            "email": user_dict.get("email", ""),
            "name": user_dict.get("name", user_dict.get("full_name", "Пользователь")),
            "full_name": user_dict.get("full_name", ""),
            "surname": user_dict.get("surname", ""),
            "full_name_number": user_dict.get("full_name_number", None),
            "birth_date": user_dict.get("birth_date", ""),
            "phone_number": user_dict.get("phone_number", ""),
            "city": user_dict.get("city", ""),
            "car_number": user_dict.get("car_number", ""),
            "street": user_dict.get("street", ""),
            "house_number": user_dict.get("house_number", ""),
            "apartment_number": user_dict.get("apartment_number", ""),
            "postal_code": user_dict.get("postal_code", ""),
            "is_admin": user_dict.get("is_admin", False),
            "is_super_admin": user_dict.get("is_super_admin", False),
            "credits_remaining": user_dict.get("credits_remaining", 0),
            "level": user_dict.get("level", 1)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile V2: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting user profile: {str(e)}")


@app.patch("/api/user/profile-v2")
async def update_user_profile_v2(request_data: dict, current_user: dict = Depends(get_current_user)):
    """Обновить профиль пользователя для системы обучения V2"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        allowed_fields = [
            "full_name",
            "name",
            "surname",
            "birth_date",
            "city",
            "phone_number",
            "car_number",
            "street",
            "house_number",
            "apartment_number",
            "postal_code"
        ]

        update_payload = {}
        for field in allowed_fields:
            if field in request_data:
                value = request_data.get(field)
                if isinstance(value, str):
                    value = value.strip()
                update_payload[field] = value

        if not update_payload:
            raise HTTPException(status_code=400, detail="No valid fields provided for update")

        update_payload["updated_at"] = datetime.utcnow()

        await db.users.update_one({"id": user_id}, {"$set": update_payload})
        # Пересчитываем число имени ТОЛЬКО по name+surname (латиница)
        if any(f in request_data for f in ["name", "surname"]):
            fresh = await db.users.find_one({"id": user_id})
            if fresh:
                name_val = fresh.get("name", "")
                surname_val = fresh.get("surname", "")
                fn_number = calculate_full_name_number(name_val, surname_val)
                await db.users.update_one({"id": user_id}, {"$set": {"full_name_number": fn_number}})

        updated_user = await db.users.find_one({"id": user_id})
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found after update")

        updated_user.pop("_id", None)
        return updated_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile V2: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating user profile: {str(e)}")

# Этот эндпоинт уже определен выше (строка 2790), удаляем дубликат

@app.get("/api/learning-v2/lessons/{lesson_id}")
async def get_lesson_v2_student(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Получить урок V2 для студента"""
    try:
        user_id = current_user['user_id']

        lesson = await db.lessons_v2.find_one({"id": lesson_id, "is_active": True})
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        lesson_dict = dict(lesson)
        lesson_dict.pop('_id', None)
        lesson_dict.pop('created_by', None)
        lesson_dict.pop('updated_by', None)

        return {
            "lesson": lesson_dict,
            "progress": {}  # Пока без прогресса
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lesson V2 for student: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting lesson: {str(e)}")

@app.get("/api/admin/lessons-v2")
async def get_all_lessons_v2_admin(current_user: dict = Depends(get_current_user)):
    """Получить все уроки V2 для админа"""
    try:
        # Получаем полные данные пользователя из базы данных
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        logger.info("Access granted, querying lessons...")
        lessons = await db.lessons_v2.find({}).sort("order", 1).to_list(1000)
        logger.info(f"Found {len(lessons)} lessons")

        lessons_list = []
        for lesson in lessons:
            lesson_dict = dict(lesson)
            lesson_dict.pop('_id', None)
            lessons_list.append(lesson_dict)

        logger.info("Successfully processed lessons")
        return {"lessons": lessons_list}

    except Exception as e:
        import traceback
        logger.error(f"Error getting lessons V2: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting lessons: {str(e)}")

@app.put("/api/admin/lessons-v2/{lesson_id}")
async def update_lesson_v2(
    lesson_id: str,
    lesson_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Обновить урок V2 (полное обновление всех разделов)"""
    try:
        # Получаем полные данные пользователя из базы данных
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        # Подготовим данные для обновления
        update_data = {
            "title": lesson_data.get("title"),
            "description": lesson_data.get("description"),
            "level": lesson_data.get("level", 1),
            "order": lesson_data.get("order", 0),
            "points_required": lesson_data.get("points_required", 0),
            "is_active": lesson_data.get("is_active", True),
            "analytics_enabled": lesson_data.get("analytics_enabled", True),
            "updated_by": current_user.get('user_id', current_user.get('id', 'admin_system')),
            "updated_at": datetime.utcnow()
        }

        # Если указан модуль, обновим его тоже
        if "module" in lesson_data:
            update_data["module"] = lesson_data["module"]

        # Обновляем теорию если передана
        if "theory" in lesson_data:
            update_data["theory"] = lesson_data["theory"]

        # Обновляем упражнения если переданы
        if "exercises" in lesson_data:
            update_data["exercises"] = lesson_data["exercises"]

        # Обновляем челлендж если передан
        if "challenge" in lesson_data:
            update_data["challenge"] = lesson_data["challenge"]

        # Обновляем тест если передан
        if "quiz" in lesson_data:
            update_data["quiz"] = lesson_data["quiz"]

        # Обновляем файлы если переданы
        if "files" in lesson_data:
            update_data["files"] = lesson_data["files"]

        # Обновляем урок в базе данных
        result = await db.lessons_v2.update_one(
            {"id": lesson_id},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Lesson not found")

        logger.info(f"Lesson {lesson_id} updated successfully with all sections")
        return {"message": "Урок успешно обновлен", "lesson_id": lesson_id}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error updating lesson V2 {lesson_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error updating lesson: {str(e)}")

@app.delete("/api/admin/lessons-v2/{lesson_id}")
async def delete_lesson_v2(
    lesson_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Удалить урок V2 с каскадным удалением всех связанных данных"""
    try:
        # Получаем полные данные пользователя из базы данных
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        # Проверяем существование урока
        lesson = await db.lessons_v2.find_one({"id": lesson_id})
        if not lesson:
            raise HTTPException(status_code=404, detail="Урок не найден")

        # Каскадное удаление связанных данных
        # 1. Удаляем прогресс студентов по этому уроку (если есть коллекция)
        if "lesson_progress" in await db.list_collection_names():
            progress_result = await db.lesson_progress.delete_many({"lesson_id": lesson_id})
            logger.info(f"Deleted {progress_result.deleted_count} progress records for lesson {lesson_id}")

        # 2. Удаляем ответы студентов на упражнения (если есть коллекция)
        if "exercise_responses" in await db.list_collection_names():
            responses_result = await db.exercise_responses.delete_many({"lesson_id": lesson_id})
            logger.info(f"Deleted {responses_result.deleted_count} exercise responses for lesson {lesson_id}")

        # 3. Удаляем результаты тестов (если есть коллекция)
        if "quiz_results" in await db.list_collection_names():
            quiz_result = await db.quiz_results.delete_many({"lesson_id": lesson_id})
            logger.info(f"Deleted {quiz_result.deleted_count} quiz results for lesson {lesson_id}")

        # 4. Удаляем прогресс челленджей (если есть коллекция)
        if "challenge_progress" in await db.list_collection_names():
            challenge_result = await db.challenge_progress.delete_many({"lesson_id": lesson_id})
            logger.info(f"Deleted {challenge_result.deleted_count} challenge progress records for lesson {lesson_id}")

        # 5. Удаляем сам урок
        delete_result = await db.lessons_v2.delete_one({"id": lesson_id})

        if delete_result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Не удалось удалить урок")

        logger.info(f"Lesson {lesson_id} and all related data deleted successfully by {current_user.get('user_id')}")
        
        return {
            "message": "Урок и все связанные данные успешно удалены",
            "lesson_id": lesson_id,
            "deleted_by": current_user.get('user_id', current_user.get('id', 'admin'))
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error deleting lesson V2 {lesson_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении урока: {str(e)}")

@app.post("/api/admin/lessons-v2/upload-from-file")
async def upload_lesson_from_file_v2(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Загрузить урок V2 из текстового файла"""
    try:
        # Получаем полные данные пользователя из базы данных
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

            content = await file.read()
        text_content = content.decode('utf-8')

        # Парсим урок из текста
        lesson_obj = parse_lesson_from_text_v2(text_content)

        # Сохраняем в базу данных
        lesson_dict = lesson_obj.dict()
        lesson_dict['created_by'] = user.get('id', 'admin_system')
        lesson_dict['updated_by'] = user.get('id', 'admin_system')

        result = await db.lessons_v2.insert_one(lesson_dict)
        
        return {
            "message": "Урок V2 успешно загружен",
            "lesson_id": lesson_obj.id,
            "sections": {
                "theory_blocks": len(lesson_obj.theory),
                "exercises": len(lesson_obj.exercises),
                "has_challenge": lesson_obj.challenge is not None,
                "has_quiz": lesson_obj.quiz is not None,
                "analytics_enabled": lesson_obj.analytics_enabled
            }
        }

    except Exception as e:
        import traceback
        logger.error(f"Error uploading lesson V2: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error uploading lesson: {str(e)}")

@app.post("/api/admin/lessons-v2/{lesson_id}/upload-file")
async def upload_lesson_file_v2(
    lesson_id: str,
    file: UploadFile = File(...),
    section: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Загрузить файл к уроку V2 (дублированный эндпоинт - удалить)"""
    try:
        # Получаем полные данные пользователя из базы данных
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        # Проверяем существование урока
        lesson = await db.lessons_v2.find_one({"id": lesson_id})
        if not lesson:
            raise HTTPException(status_code=404, detail="Урок не найден")

        # Создаем директорию для загрузок если её нет
        upload_dir = Path("uploads/learning_v2")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Обрабатываем имя файла с правильной кодировкой
        original_name = file.filename
        if isinstance(original_name, bytes):
            original_name = original_name.decode("utf-8", errors="ignore")
        if not original_name:
            original_name = "uploaded_file"

        # Генерируем уникальное имя файла
        file_extension = Path(original_name).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Сохраняем файл
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Определяем тип файла
        content_type = file.content_type or mimetypes.guess_type(original_name)[0] or "application/octet-stream"
        is_media = content_type.startswith(('video/', 'audio/', 'image/'))
        file_type = "media" if is_media else "document"

        # Создаем запись о файле
        file_record = {
            "id": str(uuid.uuid4()),
            "lesson_id": lesson_id,
            "section": section,
            "original_name": original_name,
            "stored_name": unique_filename,
            "file_path": str(file_path),
            "file_type": file_type,
            "mime_type": content_type,
            "file_size": file_path.stat().st_size,
            "extension": file_extension.lstrip('.'),
            "uploaded_by": current_user.get('user_id', current_user.get('id', 'admin')),
            "uploaded_at": datetime.utcnow()
        }

        # Сохраняем в базу данных
        try:
            result = await db.files.insert_one(file_record)
            logger.info(f"File record saved successfully, inserted_id: {result.inserted_id}")
        except Exception as db_error:
            logger.error(f"Database error saving file: {db_error}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")

        logger.info(f"File {file.filename} uploaded successfully, file_id: {file_record['id']}")
        
        return {
            "message": "Файл успешно загружен",
            "file_id": file_record["id"],
            "file_info": {
                "original_name": file.filename,
                "file_type": file_type,
                "section": section,
                "file_size": file_path.stat().st_size
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error uploading file to lesson V2: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

# ==================== ФУНКЦИИ ДЛЯ РАСЧЕТА ЭФФЕКТИВНОСТИ АКТИВНОСТИ ====================

def get_user_ruling_planet(birth_date: str) -> str:
    """
    Определяет правящую планету пользователя по дате рождения
    Правящая планета определяется по дню недели рождения
    """
    try:
        day, month, year = parse_birth_date(birth_date)
        birth_date_obj = datetime(year, month, day)
        weekday = birth_date_obj.weekday()  # 0=Monday, 6=Sunday
        
        # Планеты в порядке по дням недели
        planets_order = ['Chandra', 'Mangal', 'Budh', 'Guru', 'Shukra', 'Shani', 'Surya']
        return planets_order[weekday]
    except Exception as e:
        logger.error(f"Error calculating ruling planet: {e}")
        return 'Surya'  # По умолчанию Солнце


def detect_lesson_planet(lesson_title: str, lesson_content: str = "") -> str:
    """
    Определяет планетарную связь урока по названию и содержимому
    Ищет ключевые слова, связанные с планетами
    """
    text = (lesson_title + " " + lesson_content).lower()
    
    # Ключевые слова для каждой планеты
    planet_keywords = {
        'Surya': ['сурья', 'surya', 'солнце', 'sun', 'солнечн', 'лидер', 'творчеств', 'эго'],
        'Chandra': ['чандра', 'chandra', 'луна', 'moon', 'лунн', 'эмоц', 'интуиц', 'чувств'],
        'Mangal': ['мангал', 'mangal', 'марс', 'mars', 'марсиан', 'энерг', 'активн', 'действ'],
        'Budh': ['будх', 'budh', 'меркурий', 'mercury', 'обучен', 'коммуникац', 'интеллект'],
        'Guru': ['гуру', 'guru', 'юпитер', 'jupiter', 'мудрост', 'расширен', 'философ'],
        'Shukra': ['шукра', 'shukra', 'венера', 'venus', 'красот', 'любов', 'гармони'],
        'Shani': ['шани', 'shani', 'сатурн', 'saturn', 'дисциплин', 'ответственн', 'ограничен']
    }
    
    # Подсчитываем совпадения для каждой планеты
    planet_scores = {}
    for planet, keywords in planet_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            planet_scores[planet] = score
    
    # Возвращаем планету с наибольшим количеством совпадений
    if planet_scores:
        return max(planet_scores.items(), key=lambda x: x[1])[0]
    
    return None  # Не удалось определить планету


def get_planetary_hour_for_datetime(activity_datetime: datetime, city: str = "Москва") -> Dict[str, Any]:
    """
    Определяет планетарный час для конкретного времени
    Возвращает информацию о текущем планетарном часе
    """
    try:
        # Получаем время восхода и заката для даты активности
        activity_date = activity_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        sunrise, sunset = get_sunrise_sunset(city, activity_date)
        
        # Определяем, день это или ночь
        if sunrise <= activity_datetime < sunset:
            # Дневной час
            weekday = activity_datetime.weekday()
            planetary_hours = calculate_planetary_hours(sunrise, sunset, weekday)
            
            # Находим текущий планетарный час
            for hour_data in planetary_hours:
                hour_start = datetime.fromisoformat(hour_data["start_time"].replace('Z', '+00:00'))
                hour_end = datetime.fromisoformat(hour_data["end_time"].replace('Z', '+00:00'))
                
                # Убираем timezone для сравнения
                if isinstance(hour_start, datetime) and hour_start.tzinfo:
                    hour_start = hour_start.replace(tzinfo=None)
                if isinstance(hour_end, datetime) and hour_end.tzinfo:
                    hour_end = hour_end.replace(tzinfo=None)
                if isinstance(activity_datetime, datetime) and activity_datetime.tzinfo:
                    activity_datetime_naive = activity_datetime.replace(tzinfo=None)
                else:
                    activity_datetime_naive = activity_datetime
                
                if hour_start <= activity_datetime_naive < hour_end:
                    return {
                        "planet": hour_data["planet"],
                        "hour_number": hour_data["hour"],
                        "period": "day",
                        "is_favorable": hour_data.get("is_favorable", False)
                    }
        else:
            # Ночной час
            weekday = activity_datetime.weekday()
            # Получаем следующий восход для расчета ночных часов
            next_sunrise = sunrise + timedelta(days=1)
            planetary_hours = calculate_night_planetary_hours(sunset, next_sunrise, weekday)
            
            # Находим текущий планетарный час
            for hour_data in planetary_hours:
                hour_start = datetime.fromisoformat(hour_data["start_time"].replace('Z', '+00:00'))
                hour_end = datetime.fromisoformat(hour_data["end_time"].replace('Z', '+00:00'))
                
                # Убираем timezone для сравнения
                if isinstance(hour_start, datetime) and hour_start.tzinfo:
                    hour_start = hour_start.replace(tzinfo=None)
                if isinstance(hour_end, datetime) and hour_end.tzinfo:
                    hour_end = hour_end.replace(tzinfo=None)
                if isinstance(activity_datetime, datetime) and activity_datetime.tzinfo:
                    activity_datetime_naive = activity_datetime.replace(tzinfo=None)
                else:
                    activity_datetime_naive = activity_datetime
                
                if hour_start <= activity_datetime_naive < hour_end:
                    return {
                        "planet": hour_data["planet"],
                        "hour_number": hour_data["hour"],
                        "period": "night",
                        "is_favorable": hour_data.get("is_favorable", False)
                    }
    except Exception as e:
        logger.error(f"Error calculating planetary hour: {e}")
    
    # Fallback: определяем планету по дню недели
    weekday = activity_datetime.weekday()
    planets_order = ['Chandra', 'Mangal', 'Budh', 'Guru', 'Shukra', 'Shani', 'Surya']
    return {
        "planet": planets_order[weekday],
        "hour_number": 1,
        "period": "day",
        "is_favorable": False
    }


def calculate_activity_efficiency(
    user_ruling_planet: str,
    lesson_planet: str,
    activity_datetime: datetime,
    is_challenge_completed: bool = False,
    challenge_completion_percentage: float = 0.0,
    user_city: str = "Москва"
) -> float:
    """
    Рассчитывает эффективность активности на основе планетарных соответствий
    Улучшенная версия с учетом точных планетарных часов
    
    Параметры:
    - user_ruling_planet: правящая планета пользователя
    - lesson_planet: планета урока
    - activity_datetime: дата и время активности
    - is_challenge_completed: завершен ли челлендж полностью
    - challenge_completion_percentage: процент выполнения челленджа
    - user_city: город пользователя для расчета восхода/заката
    
    Возвращает эффективность от 0 до 100%
    """
    efficiency = 50.0  # Базовая эффективность
    
    # Получаем информацию о планетарном часе
    planetary_hour_info = get_planetary_hour_for_datetime(activity_datetime, user_city)
    current_hour_planet = planetary_hour_info.get("planet")
    
    # 1. Соответствие планет урока и пользователя
    if lesson_planet and user_ruling_planet:
        if lesson_planet == user_ruling_planet:
            efficiency += 25.0  # Изучение урока своей планеты
        else:
            # Проверяем дружественность планет
            planet_relationships = {
                'Surya': {'friends': ['Chandra', 'Mangal', 'Guru'], 'enemies': ['Shukra', 'Shani']},
                'Chandra': {'friends': ['Surya', 'Budh'], 'enemies': []},
                'Mangal': {'friends': ['Surya', 'Chandra', 'Guru'], 'enemies': ['Budh']},
                'Budh': {'friends': ['Surya', 'Shukra'], 'enemies': ['Chandra']},
                'Guru': {'friends': ['Surya', 'Chandra', 'Mangal'], 'enemies': ['Budh', 'Shukra']},
                'Shukra': {'friends': ['Budh', 'Shani'], 'enemies': ['Surya', 'Chandra']},
                'Shani': {'friends': ['Budh', 'Shukra'], 'enemies': ['Surya', 'Chandra', 'Mangal']}
            }
            
            user_relations = planet_relationships.get(user_ruling_planet, {})
            if lesson_planet in user_relations.get('friends', []):
                efficiency += 12.0  # Дружественная планета
            elif lesson_planet in user_relations.get('enemies', []):
                efficiency -= 8.0  # Враждебная планета
    
    # 2. Благоприятный день недели
    weekday = activity_datetime.weekday()  # 0=Monday, 6=Sunday
    planets_order = ['Chandra', 'Mangal', 'Budh', 'Guru', 'Shukra', 'Shani', 'Surya']
    day_planet = planets_order[weekday]
    
    # Идеальное совпадение: день планеты урока + час планеты урока = 100%
    if lesson_planet and day_planet == lesson_planet and current_hour_planet == lesson_planet:
        efficiency = 100.0  # Максимальная эффективность!
        return round(efficiency, 1)
    
    # День планеты урока
    if lesson_planet and day_planet == lesson_planet:
        efficiency += 20.0  # Изучение урока в день его планеты (например, Сурья в воскресенье)
    
    # День правящей планеты пользователя
    if day_planet == user_ruling_planet:
        efficiency += 10.0  # День правящей планеты пользователя
    
    # 3. Планетарный час - КРИТИЧЕСКИ ВАЖНО!
    if lesson_planet and current_hour_planet:
        # Идеальное совпадение: час планеты урока
        if current_hour_planet == lesson_planet:
            efficiency += 30.0  # Очень большой бонус за совпадение часа!
        
        # Час правящей планеты пользователя
        if current_hour_planet == user_ruling_planet:
            efficiency += 15.0
        
        # Дружественность планетарного часа
        if lesson_planet and user_ruling_planet:
            planet_relationships = {
                'Surya': {'friends': ['Chandra', 'Mangal', 'Guru'], 'enemies': ['Shukra', 'Shani']},
                'Chandra': {'friends': ['Surya', 'Budh'], 'enemies': []},
                'Mangal': {'friends': ['Surya', 'Chandra', 'Guru'], 'enemies': ['Budh']},
                'Budh': {'friends': ['Surya', 'Shukra'], 'enemies': ['Chandra']},
                'Guru': {'friends': ['Surya', 'Chandra', 'Mangal'], 'enemies': ['Budh', 'Shukra']},
                'Shukra': {'friends': ['Budh', 'Shani'], 'enemies': ['Surya', 'Chandra']},
                'Shani': {'friends': ['Budh', 'Shukra'], 'enemies': ['Surya', 'Chandra', 'Mangal']}
            }
            
            # Проверяем дружественность часа к планете урока
            hour_relations = planet_relationships.get(current_hour_planet, {})
            if lesson_planet in hour_relations.get('friends', []):
                efficiency += 10.0  # Час дружественен планете урока
            elif lesson_planet in hour_relations.get('enemies', []):
                efficiency -= 5.0  # Час враждебен планете урока
            
            # Проверяем дружественность часа к правящей планете пользователя
            if current_hour_planet in hour_relations.get('friends', []):
                efficiency += 5.0
            elif current_hour_planet in hour_relations.get('enemies', []):
                efficiency -= 3.0
    
    # 4. Выполнение челленджа
    if is_challenge_completed:
        efficiency = 100.0  # 100% эффективность при полном выполнении челленджа
    elif challenge_completion_percentage > 0:
        # Частичное выполнение челленджа добавляет бонус
        challenge_bonus = challenge_completion_percentage * 0.3  # До 30% бонуса
        efficiency = min(100.0, efficiency + challenge_bonus)
    
    # Ограничиваем эффективность от 0 до 100%
    efficiency = max(0.0, min(100.0, efficiency))
    
    return round(efficiency, 1)


@app.get("/api/student/dashboard-stats")
async def get_student_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Получить расширенную статистику дашборда студента (V2)"""
    try:
        logger.info(f"get_student_dashboard_stats called, current_user: {current_user}")
        user_id = current_user.get('user_id', current_user.get('id'))
        if not user_id:
            logger.error(f"Invalid current_user object: {current_user}")
            raise HTTPException(status_code=401, detail="Invalid token")

        # Получаем данные пользователя для расчета эффективности
        user = await db.users.find_one({"id": user_id})
        user_birth_date = user.get('birth_date') if user else None
        user_city = user.get('city', 'Москва') if user else 'Москва'
        user_ruling_planet = None
        if user_birth_date:
            try:
                user_ruling_planet = get_user_ruling_planet(user_birth_date)
                logger.info(f"User ruling planet: {user_ruling_planet}")
            except Exception as e:
                logger.error(f"Error calculating user ruling planet: {e}")

        collection_names = await db.list_collection_names()

        # ----- Уроки и прогресс -----
        lessons_cursor = db.lessons_v2.find({"is_active": True})
        lessons = await lessons_cursor.to_list(length=None)
        total_lessons = len(lessons)

        lesson_progress_list = []
        if "lesson_progress" in collection_names:
            progress_cursor = db.lesson_progress.find({"user_id": user_id})
            lesson_progress_list = await progress_cursor.to_list(length=None)

        completed_lessons = len([p for p in lesson_progress_list if p.get("is_completed")])
        in_progress_lessons = len([
            p for p in lesson_progress_list
            if not p.get("is_completed") and p.get("completion_percentage", 0) > 0
        ])

        # ----- Упражнения -----
        total_exercises_completed = 0
        recent_exercises = 0
        exercise_points = 0
        exercise_review_points = 0  # Баллы за проверенные упражнения
        exercise_review_time = 0  # Время проверки упражнений администратором
        
        if "exercise_responses" in collection_names:
            exercise_cursor = db.exercise_responses.find({"user_id": user_id})
            exercise_responses = await exercise_cursor.to_list(length=None)
            total_exercises_completed = len(exercise_responses)
            
            # Баллы за проверенные упражнения (назначенные администратором)
            exercise_review_points = sum(resp.get("points_earned", 0) for resp in exercise_responses if resp.get("reviewed", False))
            exercise_review_time = sum(resp.get("review_time_minutes", 0) for resp in exercise_responses if resp.get("review_time_minutes"))
            
            # Если нет баллов за проверку, используем базовые баллы
            if exercise_review_points == 0:
                exercise_points = total_exercises_completed * 10  # 10 баллов за упражнение
            else:
                exercise_points = exercise_review_points

            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent_exercises = sum(
                1 for resp in exercise_responses
                if resp.get("submitted_at") and resp["submitted_at"] >= seven_days_ago
            )
        
        # Также проверяем time_activity для баллов за упражнения
        if "time_activity" in collection_names:
            exercise_review_activity = await db.time_activity.find({
                "user_id": user_id,
                "activity_type": "exercise_review"
            }).to_list(length=None)
            
            if exercise_review_activity:
                exercise_review_points = max(exercise_review_points, sum(a.get("total_points", 0) for a in exercise_review_activity))
                exercise_review_time = max(exercise_review_time, sum(a.get("review_time_minutes", 0) for a in exercise_review_activity))
                exercise_points = exercise_review_points if exercise_review_points > 0 else exercise_points

        # ----- Тесты (детальная аналитика) -----
        total_quiz_attempts = 0
        total_quiz_points = 0
        recent_quizzes = 0
        quiz_details = []
        quiz_attempts_by_lesson = {}
        max_quiz_score = 0
        avg_quiz_score = 0
        
        if "quiz_attempts" in collection_names:
            quiz_cursor = db.quiz_attempts.find({"user_id": user_id})
            quiz_attempts = await quiz_cursor.to_list(length=None)
            total_quiz_attempts = len(quiz_attempts)
            
            # Получаем информацию об уроках для тестов
            lessons_dict = {l["id"]: l for l in lessons}

            for attempt in quiz_attempts:
                points = attempt.get("points_earned") or 0
                score = attempt.get("score", 0)
                lesson_id = attempt.get("lesson_id")
                passed = attempt.get("passed", False)
                
                # Если баллы не указаны, но тест пройден - начисляем 10 баллов
                if points == 0 and passed:
                    points = 10
                
                total_quiz_points += points
                max_quiz_score = max(max_quiz_score, score)
                
                # Группируем попытки по урокам
                if lesson_id not in quiz_attempts_by_lesson:
                    quiz_attempts_by_lesson[lesson_id] = []
                
                quiz_attempts_by_lesson[lesson_id].append({
                    "attempt_id": attempt.get("id"),
                    "score": score,
                    "points_earned": points,
                    "passed": attempt.get("passed", False),
                    "attempted_at": attempt.get("attempted_at").isoformat() if attempt.get("attempted_at") else None,
                    "time_spent_minutes": attempt.get("time_spent_minutes", 0)
                })

                attempted_at = attempt.get("attempted_at")
                if attempted_at and attempted_at >= datetime.utcnow() - timedelta(days=7):
                    recent_quizzes += 1
            
            # Вычисляем средний балл
            if total_quiz_attempts > 0:
                avg_quiz_score = sum(attempt.get("score", 0) for attempt in quiz_attempts) / total_quiz_attempts
            
            # Формируем детали по каждому уроку с тестами
            for lesson_id, attempts in quiz_attempts_by_lesson.items():
                lesson = lessons_dict.get(lesson_id)
                if not lesson:
                    continue
                
                quiz = lesson.get("quiz")
                max_possible_score = 100  # По умолчанию
                if quiz and quiz.get("questions"):
                    # Максимальный балл = сумма всех баллов за вопросы
                    max_possible_score = sum(q.get("points", 10) for q in quiz.get("questions", []))
                
                best_attempt = max(attempts, key=lambda x: x.get("score", 0))
                passed_count = sum(1 for a in attempts if a.get("passed", False))
                
                quiz_details.append({
                    "lesson_id": lesson_id,
                    "lesson_title": lesson.get("title", "Урок"),
                    "total_attempts": len(attempts),
                    "passed_attempts": passed_count,
                    "pass_percentage": round((passed_count / len(attempts)) * 100, 1) if attempts else 0,
                    "best_score": best_attempt.get("score", 0),
                    "best_score_percentage": round((best_attempt.get("score", 0) / max_possible_score) * 100, 1) if max_possible_score > 0 else 0,
                    "avg_score": round(sum(a.get("score", 0) for a in attempts) / len(attempts), 1) if attempts else 0,
                    "avg_score_percentage": round((sum(a.get("score", 0) for a in attempts) / len(attempts) / max_possible_score) * 100, 1) if attempts and max_possible_score > 0 else 0,
                    "max_possible_score": max_possible_score,
                    "total_points_earned": sum(a.get("points_earned", 0) for a in attempts),
                    "total_time_minutes": sum(a.get("time_spent_minutes", 0) for a in attempts),
                    "attempts": attempts
                })

        # ----- Челленджи (детальная аналитика) -----
        total_challenge_attempts = 0
        total_challenge_points = 0
        recent_challenges = 0
        total_challenge_days_completed = 0
        total_challenge_time_minutes = 0
        challenge_details = []
        challenge_problem_days = []
        
        if "challenge_progress" in collection_names:
            challenge_cursor = db.challenge_progress.find({"user_id": user_id})
            challenge_attempts = await challenge_cursor.to_list(length=None)
            total_challenge_attempts = len(challenge_attempts)

            # Получаем информацию об уроках для челленджей
            lessons_dict = {l["id"]: l for l in lessons}

            for attempt in challenge_attempts:
                points = attempt.get("points_earned") or 0
                completed_days = attempt.get("completed_days") or []
                current_day = attempt.get("current_day", 0)
                daily_notes = attempt.get("daily_notes", [])
                
                if points == 0:
                    points = len(completed_days) * 15  # 15 баллов за каждый завершенный день
                
                total_challenge_points += points
                total_challenge_days_completed += len(completed_days)
                
                # Время на челлендж (из time_activity для этого урока)
                challenge_time = 0
                if "time_activity" in collection_names:
                    challenge_time_records = await db.time_activity.find({
                        "user_id": user_id,
                        "lesson_id": attempt.get("lesson_id")
                    }).to_list(length=None)
                    challenge_time = sum(r.get("total_minutes", 0) for r in challenge_time_records)
                
                total_challenge_time_minutes += challenge_time
                
                # Определяем дни с проблемами (дни без заметок или пропущенные дни)
                lesson = lessons_dict.get(attempt.get("lesson_id"))
                challenge = None
                if lesson and lesson.get("challenge"):
                    challenge = lesson["challenge"]
                    total_days = challenge.get("total_days", 0)
                    
                    # Дни с проблемами: пропущенные дни между завершенными
                    if completed_days and total_days > 0:
                        for day in range(1, min(current_day + 1, total_days + 1)):
                            if day not in completed_days:
                                # Проверяем есть ли заметка для этого дня
                                has_note = any(note.get("day") == day for note in daily_notes)
                                if not has_note:
                                    challenge_problem_days.append({
                                        "lesson_id": attempt.get("lesson_id"),
                                        "lesson_title": lesson.get("title", "Урок"),
                                        "challenge_id": attempt.get("challenge_id"),
                                        "day": day,
                                        "reason": "Пропущенный день"
                                    })
                
                # Детали по каждому челленджу
                challenge_details.append({
                    "lesson_id": attempt.get("lesson_id"),
                    "lesson_title": lessons_dict.get(attempt.get("lesson_id"), {}).get("title", "Урок"),
                    "challenge_id": attempt.get("challenge_id"),
                    "current_day": current_day,
                    "completed_days": len(completed_days),
                    "total_days": challenge.get("total_days", 0) if challenge else 0,
                    "completion_percentage": round((len(completed_days) / challenge.get("total_days", 1)) * 100, 1) if challenge and challenge.get("total_days") else 0,
                    "is_completed": attempt.get("is_completed", False),
                    "points_earned": points,
                    "time_minutes": challenge_time,
                    "started_at": attempt.get("started_at").isoformat() if attempt.get("started_at") else None,
                    "completed_at": attempt.get("completed_at").isoformat() if attempt.get("completed_at") else None
                })

                last_updated = attempt.get("last_updated")
                if last_updated and last_updated >= datetime.utcnow() - timedelta(days=7):
                    recent_challenges += 1

        # ----- Время обучения -----
        time_minutes = 0
        time_points = 0
        if "time_activity" in collection_names:
            time_records = await db.time_activity.find({"user_id": user_id}).to_list(length=None)
            for record in time_records:
                if record.get("activity_type") == "file_view":
                    continue  # учитываем отдельно ниже
                time_minutes += record.get("total_minutes", 0)
                time_points += record.get("total_points", 0)

        # ----- Видео -----
        video_minutes = 0
        video_points = 0
        if "video_watch_time" in collection_names:
            video_records = await db.video_watch_time.find({"user_id": user_id}).to_list(length=None)
            video_minutes = sum(record.get("total_minutes", 0) for record in video_records)
            video_points = sum(record.get("total_points", 0) for record in video_records)

        # ----- Файлы -----
        file_view_points = 0
        file_views = 0
        file_downloads = 0
        if "time_activity" in collection_names:
            file_view_records = await db.time_activity.find({
                "user_id": user_id,
                "activity_type": "file_view"
            }).to_list(length=None)
            file_view_points = sum(record.get("total_points", 0) for record in file_view_records)
            file_views = sum(record.get("view_count", 0) for record in file_view_records)

        if "file_analytics" in collection_names:
            file_views = max(
                file_views,
                await db.file_analytics.count_documents({"user_id": user_id, "action": "view"})
            )
            file_downloads = await db.file_analytics.count_documents({"user_id": user_id, "action": "download"})

        # ----- Общие баллы и уровни -----
        total_points = (
            total_challenge_points +
            total_quiz_points +
            time_points +
            video_points +
            file_view_points +
            exercise_points
        )

        level = 1
        level_name = "Новичок"
        next_level_points = 100

        if total_points >= 1000:
            level = 5
            level_name = "Мастер"
            next_level_points = 2000
        elif total_points >= 500:
            level = 4
            level_name = "Эксперт"
            next_level_points = 1000
        elif total_points >= 250:
            level = 3
            level_name = "Продвинутый"
            next_level_points = 500
        elif total_points >= 100:
            level = 2
            level_name = "Ученик"
            next_level_points = 250

        # Прогресс к следующему уровню
        previous_level_thresholds = {1: 0, 2: 100, 3: 250, 4: 500, 5: 1000}
        current_level_threshold = previous_level_thresholds[level]
        progress_to_next_level = 0
        if level < 5:
            progress_to_next_level = ((total_points - current_level_threshold) / (next_level_points - current_level_threshold)) * 100
        else:
            progress_to_next_level = 100

        # ----- Активность по дням (7 дней) с детализацией и эффективностью -----
        # Создаем словарь уроков для быстрого доступа
        lessons_dict = {l["id"]: l for l in lessons}
        
        activity_chart = []
        for i in range(7):
            day = datetime.utcnow() - timedelta(days=6 - i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            day_activity = 0
            theory_activity = 0  # Активность теории (просмотр теории)
            lesson_presence = 0  # Активность присутствия в уроке (time_activity без file_view)
            video_activity = 0  # Активность просмотра видео
            pdf_activity = 0  # Активность просмотра PDF файлов
            study_time_minutes = 0  # Время обучения в минутах
            file_views_count = 0  # Количество просмотров файлов
            
            # Эффективность активности за день (средняя по всем активностям)
            day_efficiencies = []

            if "exercise_responses" in collection_names:
                exercise_count = await db.exercise_responses.count_documents({
                    "user_id": user_id,
                    "submitted_at": {"$gte": day_start, "$lt": day_end}
                })
                day_activity += exercise_count
                
                # Получаем упражнения для расчета эффективности
                exercise_records = await db.exercise_responses.find({
                    "user_id": user_id,
                    "submitted_at": {"$gte": day_start, "$lt": day_end}
                }).to_list(length=None)
                
                for ex in exercise_records:
                    lesson_id = ex.get("lesson_id")
                    lesson = lessons_dict.get(lesson_id) if lesson_id else None
                    lesson_planet = None
                    if lesson:
                        lesson_planet = detect_lesson_planet(lesson.get("title", ""), "")
                    
                    if user_ruling_planet and lesson_planet:
                        efficiency = calculate_activity_efficiency(
                            user_ruling_planet,
                            lesson_planet,
                            ex.get("submitted_at", day_start),
                            False,
                            0.0,
                            user_city
                        )
                        day_efficiencies.append(efficiency)

            if "quiz_attempts" in collection_names:
                quiz_count = await db.quiz_attempts.count_documents({
                    "user_id": user_id,
                    "attempted_at": {"$gte": day_start, "$lt": day_end}
                })
                day_activity += quiz_count
                
                # Получаем тесты для расчета эффективности
                quiz_records = await db.quiz_attempts.find({
                    "user_id": user_id,
                    "attempted_at": {"$gte": day_start, "$lt": day_end}
                }).to_list(length=None)
                
                for quiz in quiz_records:
                    lesson_id = quiz.get("lesson_id")
                    lesson = lessons_dict.get(lesson_id) if lesson_id else None
                    lesson_planet = None
                    if lesson:
                        lesson_planet = detect_lesson_planet(lesson.get("title", ""), "")
                    
                    if user_ruling_planet and lesson_planet:
                        efficiency = calculate_activity_efficiency(
                            user_ruling_planet,
                            lesson_planet,
                            quiz.get("attempted_at", day_start),
                            False,
                            0.0,
                            user_city
                        )
                        day_efficiencies.append(efficiency)

            if "challenge_progress" in collection_names:
                challenge_count = await db.challenge_progress.count_documents({
                    "user_id": user_id,
                    "last_updated": {"$gte": day_start, "$lt": day_end}
                })
                day_activity += challenge_count
                
                # Получаем челленджи для расчета эффективности
                challenge_records = await db.challenge_progress.find({
                    "user_id": user_id,
                    "last_updated": {"$gte": day_start, "$lt": day_end}
                }).to_list(length=None)
                
                for challenge in challenge_records:
                    lesson_id = challenge.get("lesson_id")
                    lesson = lessons_dict.get(lesson_id) if lesson_id else None
                    lesson_planet = None
                    if lesson:
                        lesson_planet = detect_lesson_planet(lesson.get("title", ""), "")
                    
                    is_completed = challenge.get("is_completed", False)
                    completed_days = challenge.get("completed_days", [])
                    total_days = 0
                    if lesson and lesson.get("challenge"):
                        total_days = lesson["challenge"].get("total_days", 0)
                    completion_percentage = (len(completed_days) / total_days * 100) if total_days > 0 else 0
                    
                    if user_ruling_planet and lesson_planet:
                        efficiency = calculate_activity_efficiency(
                            user_ruling_planet,
                            lesson_planet,
                            challenge.get("last_updated", day_start),
                            is_completed,
                            completion_percentage,
                            user_city
                        )
                        day_efficiencies.append(efficiency)

            # УНИФИЦИРОВАННЫЙ ИСТОЧНИК ДАННЫХ: time_activity - основная коллекция для всех типов активности
            # Все данные активности должны браться из time_activity с правильными типами:
            # - "lesson_view" - присутствие в уроке
            # - "theory" или "theory_view" - просмотр теории
            # - "video_watch" - просмотр видео (время в минутах)
            # - "file_view" - просмотр файлов (PDF и другие)
            # - "exercise" - выполнение упражнений
            # - "challenge" - выполнение челленджей
            # - "quiz" - прохождение тестов
            
            if "time_activity" in collection_names:
                # Получаем все записи активности за день из time_activity
                all_activity_records_cursor = db.time_activity.find({
                    "user_id": user_id,
                    "$or": [
                        {"last_activity_at": {"$gte": day_start, "$lt": day_end}},
                        {"created_at": {"$gte": day_start, "$lt": day_end}}
                    ]
                })
                all_activity_records = []
                async for r in all_activity_records_cursor:
                    r_dict = dict(r)
                    r_dict.pop("_id", None)  # Удаляем ObjectId
                    all_activity_records.append(r_dict)
                
                # Группируем по типам активности
                for record in all_activity_records:
                    activity_type = record.get("activity_type", "")
                    lesson_id = record.get("lesson_id")
                    lesson = lessons_dict.get(lesson_id) if lesson_id else None
                    lesson_planet = None
                    if lesson:
                        lesson_planet = detect_lesson_planet(lesson.get("title", ""), "")
                    
                    # Присутствие в уроке (lesson_view, но не file_view)
                    if activity_type == "lesson_view":
                        lesson_presence += 1
                        # Суммируем время обучения из lesson_view
                        study_time_minutes += record.get("total_minutes", 0)
                    
                    # Активность теории
                    if activity_type in ["theory", "theory_view"]:
                        theory_activity += 1
                        # Суммируем время обучения из теории
                        study_time_minutes += record.get("total_minutes", 0)
                    
                    # Активность просмотра видео (суммируем минуты)
                    if activity_type == "video_watch":
                        video_activity += record.get("total_minutes", 0)
                        # Суммируем время обучения из видео
                        study_time_minutes += record.get("total_minutes", 0)
                    
                    # Активность просмотра PDF (file_view с типом pdf)
                    if activity_type == "file_view":
                        file_views_count += 1  # Считаем все просмотры файлов
                        file_type = record.get("file_type", "")
                        if file_type in ["pdf", "application/pdf"]:
                            pdf_activity += 1
                    
                    # Рассчитываем эффективность для всех типов активности
                    if user_ruling_planet and lesson_planet:
                        efficiency = calculate_activity_efficiency(
                            user_ruling_planet,
                            lesson_planet,
                            record.get("created_at") or record.get("last_activity_at") or day_start,
                            False,
                            0.0,
                            user_city
                        )
                        day_efficiencies.append(efficiency)
            
            # ДОПОЛНИТЕЛЬНЫЕ ИСТОЧНИКИ (для обратной совместимости и детализации):
            # video_watch_time - для детального времени просмотра видео (если нет в time_activity)
            if "video_watch_time" in collection_names and video_activity == 0:
                video_records_cursor = db.video_watch_time.find({
                    "user_id": user_id,
                    "$or": [
                        {"last_updated": {"$gte": day_start, "$lt": day_end}},
                        {"created_at": {"$gte": day_start, "$lt": day_end}}
                    ]
                })
                video_records = []
                async for r in video_records_cursor:
                    r_dict = dict(r)
                    r_dict.pop("_id", None)
                    video_records.append(r_dict)
                video_activity = sum(r.get("total_minutes", 0) for r in video_records)
                
                # Рассчитываем эффективность для просмотра видео
                for record in video_records:
                    lesson_id = record.get("lesson_id")
                    lesson = lessons_dict.get(lesson_id) if lesson_id else None
                    lesson_planet = None
                    if lesson:
                        lesson_planet = detect_lesson_planet(lesson.get("title", ""), "")
                    
                    if user_ruling_planet and lesson_planet:
                        efficiency = calculate_activity_efficiency(
                            user_ruling_planet,
                            lesson_planet,
                            record.get("created_at", day_start),
                            False,
                            0.0,
                            user_city
                        )
                        day_efficiencies.append(efficiency)
            
            # file_analytics - для просмотров файлов (если нет в time_activity или для дополнения)
            if "file_analytics" in collection_names:
                file_views_cursor = db.file_analytics.find({
                    "user_id": user_id,
                    "created_at": {"$gte": day_start, "$lt": day_end},
                    "action": "view"
                })
                file_views = []
                async for fv in file_views_cursor:
                    fv_dict = dict(fv)
                    fv_dict.pop("_id", None)
                    file_views.append(fv_dict)
                
                # Добавляем к общему количеству просмотров файлов
                file_views_count += len(file_views)
                
                # Получаем информацию о файлах, чтобы определить PDF
                file_ids = [fv.get("file_id") for fv in file_views if fv.get("file_id")]
                if file_ids:
                    pdf_files_cursor = db.files.find({
                        "id": {"$in": file_ids},
                        "mime_type": {"$in": ["application/pdf", "pdf"]}
                    })
                    pdf_files = []
                    async for f in pdf_files_cursor:
                        pdf_file = dict(f)
                        pdf_file.pop("_id", None)
                        pdf_files.append(pdf_file)
                    pdf_file_ids = {f.get("id") for f in pdf_files}
                    # Добавляем к активности PDF (если еще не было в time_activity)
                    if pdf_activity == 0:
                        pdf_activity = len([fv for fv in file_views if fv.get("file_id") in pdf_file_ids])
            
            # lesson_progress - для активности теории (если нет в time_activity)
            if "lesson_progress" in collection_names and theory_activity == 0:
                theory_records_cursor = db.lesson_progress.find({
                    "user_id": user_id,
                    "last_accessed": {"$gte": day_start, "$lt": day_end}
                })
                theory_records = []
                async for r in theory_records_cursor:
                    r_dict = dict(r)
                    r_dict.pop("_id", None)
                    theory_records.append(r_dict)
                theory_activity = len(theory_records)
                
                # Рассчитываем эффективность для теории
                for record in theory_records:
                    lesson_id = record.get("lesson_id")
                    lesson = lessons_dict.get(lesson_id) if lesson_id else None
                    lesson_planet = None
                    if lesson:
                        lesson_planet = detect_lesson_planet(lesson.get("title", ""), "")
                    
                    if user_ruling_planet and lesson_planet:
                        efficiency = calculate_activity_efficiency(
                            user_ruling_planet,
                            lesson_planet,
                            record.get("last_accessed", day_start),
                            False,
                            0.0,
                            user_city
                        )
                        day_efficiencies.append(efficiency)

            # Рассчитываем среднюю эффективность за день
            avg_efficiency = 0.0
            if day_efficiencies:
                avg_efficiency = sum(day_efficiencies) / len(day_efficiencies)
            elif day_activity > 0:
                # Если есть активность, но не удалось рассчитать эффективность, используем базовую
                avg_efficiency = 50.0

            activity_chart.append({
                "day_name": day.strftime('%a')[:2],
                "date": day.strftime('%d.%m'),
                "activity": day_activity,
                "theory_activity": theory_activity,
                "lesson_presence": lesson_presence,
                "video_activity": video_activity,
                "pdf_activity": pdf_activity,
                "study_time_minutes": study_time_minutes,
                "file_views": file_views_count,
                "efficiency": round(avg_efficiency, 1)  # Эффективность активности в процентах
            })

        recent_activity_7days = sum(item["activity"] for item in activity_chart)

        # ----- Достижения -----
        achievements = []

        if completed_lessons >= 1:
            achievements.append({
                'id': 'first_lesson',
                'title': 'Первый шаг',
                'description': 'Завершен первый урок',
                'icon': '🎯',
                'earned': True
            })

        if total_exercises_completed >= 1:
            achievements.append({
                'id': 'first_exercise',
                'title': 'Практик',
                'description': 'Выполнено первое упражнение',
                'icon': '📝',
                'earned': True
            })

        if total_quiz_attempts >= 1:
            achievements.append({
                'id': 'first_quiz',
                'title': 'Тестировщик',
                'description': 'Пройден первый тест',
                'icon': '🎯',
                'earned': True
            })

        if total_challenge_attempts >= 1:
            achievements.append({
                'id': 'first_challenge',
                'title': 'Принял вызов',
                'description': 'Начат первый челлендж',
                'icon': '⚡',
                'earned': True
            })

        if total_points >= 100:
            achievements.append({
                'id': 'hundred_points',
                'title': 'Сотня',
                'description': 'Заработано 100 баллов',
                'icon': '💯',
                'earned': True
            })

        # ----- Топ уроков (по прогрессу) -----
        top_lessons = []
        if lesson_progress_list:
            for progress in lesson_progress_list:
                lesson = next((l for l in lessons if l["id"] == progress["lesson_id"]), None)
                if lesson:
                    top_lessons.append({
                        "lesson_id": lesson["id"],
                        "lesson_title": lesson.get("title", "Урок"),
                        "completion": progress.get("completion_percentage", 0)
                    })
            top_lessons = sorted(top_lessons, key=lambda x: x["completion"], reverse=True)[:5]

        return {
            "stats": {
                "level": level,
                "level_name": level_name,
                "total_points": total_points,
                "progress_to_next_level": max(0, min(100, round(progress_to_next_level))),
                "next_level_points": next_level_points,
                # Совместимость со старым фронтендом
                "completed_lessons": completed_lessons,
                "total_lessons": total_lessons,
                "total_challenge_attempts": total_challenge_attempts,
                "total_challenge_points": total_challenge_points,
                "total_quiz_attempts": total_quiz_attempts,
                "total_quiz_points": total_quiz_points,
                "total_exercises_completed": total_exercises_completed,
                "lessons": {
                    "total": total_lessons,
                    "completed": completed_lessons,
                    "completion_percentage": round((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0,
                    "in_progress": in_progress_lessons
                },
                "activity": {
                    "total_exercises": total_exercises_completed,
                    "total_quizzes": total_quiz_attempts,
                    "total_challenges": total_challenge_attempts,
                    "recent_exercises": recent_exercises,
                    "recent_quizzes": recent_quizzes,
                    "recent_challenges": recent_challenges
                },
                "points_breakdown": {
                    "challenges": total_challenge_points,
                    "quizzes": total_quiz_points,
                    "time": time_points,
                    "videos": video_points,
                    "files": file_view_points,
                    "exercises": exercise_points,
                    "exercise_review": exercise_review_points,
                    "time_minutes": time_minutes,
                    "video_minutes": video_minutes,
                    "exercise_review_time_minutes": exercise_review_time
                },
                "challenge_analytics": {
                    "total_days_completed": total_challenge_days_completed,
                    "total_time_minutes": total_challenge_time_minutes,
                    "total_time_hours": round(total_challenge_time_minutes / 60, 1),
                    "problem_days": challenge_problem_days,
                    "details": challenge_details
                },
                "quiz_analytics": {
                    "total_attempts": total_quiz_attempts,
                    "max_score": max_quiz_score,
                    "avg_score": round(avg_quiz_score, 1),
                    "avg_score_percentage": round(avg_quiz_score, 1),
                    "details": quiz_details
                },
                "time_stats": {
                    "study_minutes": time_minutes,
                    "video_minutes": video_minutes
                },
                "files": {
                    "views": file_views,
                    "downloads": file_downloads
                },
                "activity_chart": activity_chart,
                "recent_activity_7days": recent_activity_7days,
                "active_students": 1,
                "top_lessons": top_lessons,
                "achievements": achievements,
                "recent_achievements": achievements[:3]
            }
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Error getting dashboard stats: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting dashboard stats: {str(e)}")

@app.get("/api/student/analytics/{section}")
async def get_detailed_analytics(
    section: str, 
    period: str = 'week',
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format (for calendar)"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format (for calendar)"),
    current_user: dict = Depends(get_current_user)
):
    """Получить детальную аналитику по конкретному разделу (lessons, challenges, quizzes, exercises)"""
    try:
        logger.info(f"get_detailed_analytics called for section: {section}, period: {period}, start_date: {start_date}, end_date: {end_date}")
        user_id = current_user.get('user_id', current_user.get('id'))
        logger.info(f"User ID: {user_id}")
        if not user_id:
            logger.error("No user_id found in current_user")
            raise HTTPException(status_code=401, detail="Invalid token")

        # Получаем данные пользователя для расчета эффективности
        user = await db.users.find_one({"id": user_id})
        user_birth_date = user.get('birth_date') if user else None
        user_city = user.get('city', 'Москва') if user else 'Москва'
        user_ruling_planet = None
        if user_birth_date:
            try:
                user_ruling_planet = get_user_ruling_planet(user_birth_date)
                logger.info(f"User ruling planet: {user_ruling_planet}")
            except Exception as e:
                logger.error(f"Error calculating user ruling planet: {e}")

        collection_names = await db.list_collection_names()
        logger.info(f"Available collections: {collection_names}")
        
        if section == 'lessons':
            # Детальная аналитика по урокам
            lessons_cursor = db.lessons_v2.find({"is_active": True})
            lessons = await lessons_cursor.to_list(length=None)
            
            lesson_progress_list = []
            if "lesson_progress" in collection_names:
                progress_cursor = db.lesson_progress.find({"user_id": user_id})
                lesson_progress_list = await progress_cursor.to_list(length=None)
            
            # Детали по каждому уроку
            lesson_details = []
            for lesson in lessons:
                progress = next((p for p in lesson_progress_list if p.get("lesson_id") == lesson["id"]), None)
                
                # Время изучения урока
                lesson_time = 0
                if "time_activity" in collection_names:
                    time_records = await db.time_activity.find({
                        "user_id": user_id,
                        "lesson_id": lesson["id"]
                    }).to_list(length=None)
                    lesson_time = sum(r.get("total_minutes", 0) for r in time_records)
                
                # Видео время
                video_time = 0
                if "video_watch_time" in collection_names:
                    video_records = await db.video_watch_time.find({
                        "user_id": user_id,
                        "lesson_id": lesson["id"]
                    }).to_list(length=None)
                    video_time = sum(r.get("total_minutes", 0) for r in video_records)
                
                # Файлы
                file_views = 0
                file_downloads = 0
                if "time_activity" in collection_names:
                    file_records = await db.time_activity.find({
                        "user_id": user_id,
                        "lesson_id": lesson["id"],
                        "activity_type": "file_view"
                    }).to_list(length=None)
                    file_views = sum(r.get("view_count", 0) for r in file_records)
                
                if "file_analytics" in collection_names:
                    file_views = max(file_views, await db.file_analytics.count_documents({
                        "user_id": user_id,
                        "lesson_id": lesson["id"],
                        "action": "view"
                    }))
                    file_downloads = await db.file_analytics.count_documents({
                        "user_id": user_id,
                        "lesson_id": lesson["id"],
                        "action": "download"
                    })
                
                lesson_details.append({
                    "lesson_id": lesson["id"],
                    "lesson_title": lesson.get("title", "Урок"),
                    "completion_percentage": progress.get("completion_percentage", 0) if progress else 0,
                    "is_completed": progress.get("is_completed", False) if progress else False,
                    "time_minutes": lesson_time,
                    "video_minutes": video_time,
                    "file_views": file_views,
                    "file_downloads": file_downloads,
                    "started_at": progress.get("started_at").isoformat() if progress and progress.get("started_at") else None,
                    "completed_at": progress.get("completed_at").isoformat() if progress and progress.get("completed_at") else None
                })
            
            # Получаем activity_chart для графика активности с эффективностью
            lessons_dict = {l["id"]: l for l in lessons}
            activity_chart = []
            
            # Определяем диапазон дат в зависимости от периода и переданных дат
            if start_date and end_date:
                # Используем переданные даты из календаря
                try:
                    # Парсим даты как naive datetime (без timezone) - это локальная дата от пользователя
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                    # Устанавливаем время для правильной фильтрации (используем UTC для совместимости с БД)
                    start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
                    logger.info(f"Parsed dates for activity_chart: start_dt={start_dt}, end_dt={end_dt}, start_date={start_date}, end_date={end_date}, period={period}")
                except Exception as e:
                    logger.error(f"Error parsing dates: {e}, start_date={start_date}, end_date={end_date}")
                    # Если не удалось распарсить, используем период
                    start_dt = None
                    end_dt = None
            else:
                start_dt = None
                end_dt = None
            
            # Функция-помощник для сбора данных активности за период (час или день)
            async def collect_activity_data(period_start, period_end, is_hour=False):
                """Собирает данные активности за указанный период (час или день)"""
                period_activity = 0
                period_theory_activity = 0
                period_lesson_presence = 0
                period_video_activity = 0
                period_pdf_activity = 0
                period_study_time_minutes = 0
                period_file_views_count = 0
                period_efficiencies = []
                
                # Упражнения
                if "exercise_responses" in collection_names:
                    exercise_count = await db.exercise_responses.count_documents({
                        "user_id": user_id,
                        "submitted_at": {"$gte": period_start, "$lt": period_end}
                    })
                    period_activity += exercise_count
                    
                    exercise_records = await db.exercise_responses.find({
                        "user_id": user_id,
                        "submitted_at": {"$gte": period_start, "$lt": period_end}
                    }).to_list(length=None)
                    
                    for ex in exercise_records:
                        lesson_id = ex.get("lesson_id")
                        lesson = lessons_dict.get(lesson_id) if lesson_id else None
                        lesson_planet = detect_lesson_planet(lesson.get("title", ""), "") if lesson else None
                        if user_ruling_planet and lesson_planet:
                            efficiency = calculate_activity_efficiency(
                                user_ruling_planet, lesson_planet, ex.get("submitted_at", period_start),
                                False, 0.0, user_city
                            )
                            period_efficiencies.append(efficiency)
                
                # Тесты
                if "quiz_attempts" in collection_names:
                    quiz_count = await db.quiz_attempts.count_documents({
                        "user_id": user_id,
                        "attempted_at": {"$gte": period_start, "$lt": period_end}
                    })
                    period_activity += quiz_count
                    
                    quiz_records = await db.quiz_attempts.find({
                        "user_id": user_id,
                        "attempted_at": {"$gte": period_start, "$lt": period_end}
                    }).to_list(length=None)
                    
                    for quiz in quiz_records:
                        lesson_id = quiz.get("lesson_id")
                        lesson = lessons_dict.get(lesson_id) if lesson_id else None
                        lesson_planet = detect_lesson_planet(lesson.get("title", ""), "") if lesson else None
                        if user_ruling_planet and lesson_planet:
                            efficiency = calculate_activity_efficiency(
                                user_ruling_planet, lesson_planet, quiz.get("attempted_at", period_start),
                                False, 0.0, user_city
                            )
                            period_efficiencies.append(efficiency)
                
                # Челленджи
                if "challenge_progress" in collection_names:
                    challenge_count = await db.challenge_progress.count_documents({
                        "user_id": user_id,
                        "last_updated": {"$gte": period_start, "$lt": period_end}
                    })
                    period_activity += challenge_count
                    
                    challenge_records = await db.challenge_progress.find({
                        "user_id": user_id,
                        "last_updated": {"$gte": period_start, "$lt": period_end}
                    }).to_list(length=None)
                    
                    for challenge in challenge_records:
                        lesson_id = challenge.get("lesson_id")
                        lesson = lessons_dict.get(lesson_id) if lesson_id else None
                        lesson_planet = detect_lesson_planet(lesson.get("title", ""), "") if lesson else None
                        is_completed = challenge.get("is_completed", False)
                        completed_days = challenge.get("completed_days", [])
                        total_days = lesson["challenge"].get("total_days", 0) if lesson and lesson.get("challenge") else 0
                        completion_percentage = (len(completed_days) / total_days * 100) if total_days > 0 else 0
                        if user_ruling_planet and lesson_planet:
                            efficiency = calculate_activity_efficiency(
                                user_ruling_planet, lesson_planet, challenge.get("last_updated", period_start),
                                is_completed, completion_percentage, user_city
                            )
                            period_efficiencies.append(efficiency)
                
                # Присутствие в уроке
                if "time_activity" in collection_names:
                    presence_records = await db.time_activity.find({
                        "user_id": user_id,
                        "$or": [
                            {"created_at": {"$gte": period_start, "$lt": period_end}},
                            {"last_activity_at": {"$gte": period_start, "$lt": period_end}}
                        ],
                        "activity_type": {"$ne": "file_view"}
                    }).to_list(length=None)
                    period_lesson_presence = len(presence_records)
                    period_study_time_minutes = sum(r.get("total_minutes", 0) for r in presence_records)
                    
                    for record in presence_records:
                        lesson_id = record.get("lesson_id")
                        lesson = lessons_dict.get(lesson_id) if lesson_id else None
                        lesson_planet = detect_lesson_planet(lesson.get("title", ""), "") if lesson else None
                        if user_ruling_planet and lesson_planet:
                            efficiency = calculate_activity_efficiency(
                                user_ruling_planet, lesson_planet, record.get("created_at") or record.get("last_activity_at") or period_start,
                                False, 0.0, user_city
                            )
                            period_efficiencies.append(efficiency)
                
                # Видео
                if "time_activity" in collection_names:
                    video_records = await db.time_activity.find({
                        "user_id": user_id,
                        "$or": [
                            {"created_at": {"$gte": period_start, "$lt": period_end}},
                            {"last_activity_at": {"$gte": period_start, "$lt": period_end}}
                        ],
                        "activity_type": "video_watch"
                    }).to_list(length=None)
                    period_video_activity = sum(r.get("total_minutes", 0) for r in video_records)
                    
                    for record in video_records:
                        lesson_id = record.get("lesson_id")
                        lesson = lessons_dict.get(lesson_id) if lesson_id else None
                        lesson_planet = detect_lesson_planet(lesson.get("title", ""), "") if lesson else None
                        if user_ruling_planet and lesson_planet:
                            efficiency = calculate_activity_efficiency(
                                user_ruling_planet, lesson_planet, record.get("created_at") or record.get("last_activity_at") or period_start,
                                False, 0.0, user_city
                            )
                            period_efficiencies.append(efficiency)
                
                # PDF файлы
                if "time_activity" in collection_names:
                    pdf_records = await db.time_activity.find({
                        "user_id": user_id,
                        "$or": [
                            {"created_at": {"$gte": period_start, "$lt": period_end}},
                            {"last_activity_at": {"$gte": period_start, "$lt": period_end}}
                        ],
                        "activity_type": "file_view",
                        "file_type": {"$in": ["pdf", "application/pdf"]}
                    }).to_list(length=None)
                    period_pdf_activity = len(pdf_records)
                    
                    for record in pdf_records:
                        lesson_id = record.get("lesson_id")
                        lesson = lessons_dict.get(lesson_id) if lesson_id else None
                        lesson_planet = detect_lesson_planet(lesson.get("title", ""), "") if lesson else None
                        if user_ruling_planet and lesson_planet:
                            efficiency = calculate_activity_efficiency(
                                user_ruling_planet, lesson_planet, record.get("created_at") or record.get("last_activity_at") or period_start,
                                False, 0.0, user_city
                            )
                            period_efficiencies.append(efficiency)
                
                # Просмотр файлов
                if "file_analytics" in collection_names:
                    period_file_views_count = await db.file_analytics.count_documents({
                        "user_id": user_id,
                        "action": "view",
                        "created_at": {"$gte": period_start, "$lt": period_end}
                    })
                
                # Теория
                if "time_activity" in collection_names:
                    theory_records = await db.time_activity.find({
                        "user_id": user_id,
                        "$or": [
                            {"created_at": {"$gte": period_start, "$lt": period_end}},
                            {"last_activity_at": {"$gte": period_start, "$lt": period_end}}
                        ],
                        "activity_type": {"$in": ["theory", "theory_view"]}
                    }).to_list(length=None)
                    period_theory_activity = len(theory_records)
                    
                    for record in theory_records:
                        lesson_id = record.get("lesson_id")
                        lesson = lessons_dict.get(lesson_id) if lesson_id else None
                        lesson_planet = detect_lesson_planet(lesson.get("title", ""), "") if lesson else None
                        if user_ruling_planet and lesson_planet:
                            efficiency = calculate_activity_efficiency(
                                user_ruling_planet, lesson_planet, record.get("created_at") or record.get("last_activity_at") or period_start,
                                False, 0.0, user_city
                            )
                            period_efficiencies.append(efficiency)
                
                avg_efficiency = sum(period_efficiencies) / len(period_efficiencies) if period_efficiencies else (50.0 if period_activity > 0 else 0.0)

                return {
                    "activity": period_activity,
                    "theory_activity": period_theory_activity,
                    "lesson_presence": period_lesson_presence,
                    "video_activity": period_video_activity,
                    "pdf_activity": period_pdf_activity,
                    "study_time_minutes": period_study_time_minutes,
                    "file_views": period_file_views_count,
                    "efficiency": round(avg_efficiency, 1)
                }
            
            # Если период "day", возвращаем данные за один день с детализацией по часам
            if period == 'day':
                logger.info(f"Processing period 'day' for activity_chart")
                # Используем переданную дату или сегодня (как в других timeline эндпоинтах)
                if start_dt and end_dt:
                    # Если переданы обе даты, используем end_dt как базовую дату (выбранную пользователем)
                    # и устанавливаем start_dt на начало того же дня
                    target_day = end_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                elif start_dt:
                    # Если передана только start_dt, используем её
                    target_day = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                elif end_dt:
                    # Если передана только end_dt, используем её
                    target_day = end_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                else:
                    # Если дата не передана, используем сегодня в UTC
                    target_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                
                logger.info(f"Target day for 'day' period: {target_day}, start_dt: {start_dt}, end_dt: {end_dt}")
                
                # Генерируем данные по часам (24 часа) - от 00:00 до 23:59 выбранного дня
                for hour in range(24):
                    hour_start = target_day + timedelta(hours=hour)
                    hour_end = hour_start + timedelta(hours=1)
                    
                    # Собираем данные за этот час
                    hour_data = await collect_activity_data(hour_start, hour_end, is_hour=True)
                    
                    activity_chart.append({
                        "day_name": hour_start.strftime('%H:%M'),
                        "date": hour_start.strftime('%d.%m %H:%M'),
                        "hour": hour,
                        "activity": hour_data["activity"],
                        "theory_activity": hour_data["theory_activity"],
                        "lesson_presence": hour_data["lesson_presence"],
                        "video_activity": hour_data["video_activity"],
                        "pdf_activity": hour_data["pdf_activity"],
                        "study_time_minutes": hour_data["study_time_minutes"],
                        "file_views": hour_data["file_views"],
                        "efficiency": hour_data["efficiency"]
                    })
                
                logger.info(f"Generated {len(activity_chart)} hour entries for 'day' period, first date: {activity_chart[0]['date'] if activity_chart else 'none'}, last date: {activity_chart[-1]['date'] if activity_chart else 'none'}")
            else:
                # Для других периодов (week, month, quarter) используем дни
                # Определяем количество дней и начальную дату
                if period == 'week':
                    days_count = 7
                    if start_dt:
                        first_day = start_dt
                    else:
                        first_day = datetime.utcnow() - timedelta(days=6)
                elif period == 'month':
                    days_count = 30
                    if start_dt:
                        first_day = start_dt
                    else:
                        first_day = datetime.utcnow() - timedelta(days=29)
                elif period == 'quarter':
                    days_count = 90
                    if start_dt:
                        first_day = start_dt
                    else:
                        first_day = datetime.utcnow() - timedelta(days=89)
                else:
                    days_count = 7
                    if start_dt:
                        first_day = start_dt
                    else:
                        first_day = datetime.utcnow() - timedelta(days=6)
                
                # Если указаны даты, используем их диапазон
                if start_dt and end_dt:
                    current_day = start_dt
                    while current_day <= end_dt:
                        day_start = current_day.replace(hour=0, minute=0, second=0, microsecond=0)
                        day_end = day_start + timedelta(days=1)
                        if day_end > end_dt:
                            day_end = end_dt
                        
                        # Собираем данные за этот день
                        day_data = await collect_activity_data(day_start, day_end, is_hour=False)
                        
                        activity_chart.append({
                            "day_name": day_start.strftime('%a')[:2],
                            "date": day_start.strftime('%d.%m'),
                            "activity": day_data["activity"],
                            "theory_activity": day_data["theory_activity"],
                            "lesson_presence": day_data["lesson_presence"],
                            "video_activity": day_data["video_activity"],
                            "pdf_activity": day_data["pdf_activity"],
                            "study_time_minutes": day_data["study_time_minutes"],
                            "file_views": day_data["file_views"],
                            "efficiency": day_data["efficiency"]
                        })
                        
                        current_day += timedelta(days=1)
                else:
                    # Используем стандартную логику для периода
                    for i in range(days_count):
                        day = first_day + timedelta(days=i)
                        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
                        day_end = day_start + timedelta(days=1)
                        
                        # Собираем данные за этот день
                        day_data = await collect_activity_data(day_start, day_end, is_hour=False)
                        
                        activity_chart.append({
                            "day_name": day.strftime('%a')[:2],
                            "date": day.strftime('%d.%m'),
                            "activity": day_data["activity"],
                            "theory_activity": day_data["theory_activity"],
                            "lesson_presence": day_data["lesson_presence"],
                            "video_activity": day_data["video_activity"],
                            "pdf_activity": day_data["pdf_activity"],
                            "study_time_minutes": day_data["study_time_minutes"],
                            "file_views": day_data["file_views"],
                            "efficiency": day_data["efficiency"]
                        })
            
            logger.info(f"Returning {len(lesson_details)} lesson details")
            return {
                "analytics": lesson_details,
                "activity_chart": activity_chart
            }
        
        elif section == 'video-timeline':
            # Детальная аналитика просмотра видео с временными метками и эффективностью
            # period: week, month, quarter
            # Также поддерживаем start_date и end_date для календаря
            timeline_start_date = None
            timeline_end_date = datetime.utcnow()
            
            # Если указаны даты в параметрах запроса, используем их
            if start_date and end_date:
                try:
                    timeline_start_date = datetime.strptime(start_date, '%Y-%m-%d')
                    timeline_end_date = datetime.strptime(end_date, '%Y-%m-%d')
                    # Добавляем время конца дня
                    timeline_end_date = timeline_end_date.replace(hour=23, minute=59, second=59)
                except Exception as e:
                    logger.error(f"Error parsing dates: {e}")
                    timeline_start_date = None
            
            # Если даты не указаны, используем period
            if timeline_start_date is None:
                if period == 'day':
                    # Один день (24 часа) - сегодня
                    timeline_start_date = timeline_end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    timeline_end_date = timeline_end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                elif period == 'week':
                    timeline_start_date = timeline_end_date - timedelta(days=7)
                elif period == 'month':
                    timeline_start_date = timeline_end_date - timedelta(days=30)
                elif period == 'quarter':
                    timeline_start_date = timeline_end_date - timedelta(days=90)
                else:
                    timeline_start_date = timeline_end_date - timedelta(days=7)
            
            start_date = timeline_start_date
            end_date = timeline_end_date
            
            # УНИФИЦИРОВАННЫЙ ИСТОЧНИК: time_activity - основная коллекция для всех типов активности
            # Получаем данные о просмотре видео с временными метками
            video_timeline = []
            lessons_cursor = db.lessons_v2.find({"is_active": True})
            lessons = await lessons_cursor.to_list(length=None)
            lessons_dict = {l["id"]: l for l in lessons}
            
            # Используем time_activity как основной источник (activity_type = "video_watch")
            video_records = []
            if "time_activity" in collection_names:
                video_records_cursor = db.time_activity.find({
            "user_id": user_id,
                    "$or": [
                        {"last_activity_at": {"$gte": start_date, "$lte": end_date}},
                        {"created_at": {"$gte": start_date, "$lte": end_date}}
                    ],
                    "activity_type": "video_watch"
                })
                async for r in video_records_cursor:
                    r_dict = dict(r)
                    r_dict.pop("_id", None)
                    video_records.append(r_dict)
            
            # Дополнительный источник: video_watch_time (для обратной совместимости)
            if "video_watch_time" in collection_names and len(video_records) == 0:
                video_watch_records = await db.video_watch_time.find({
                    "user_id": user_id,
                    "$or": [
                        {"last_updated": {"$gte": start_date, "$lte": end_date}},
                        {"created_at": {"$gte": start_date, "$lte": end_date}}
                    ]
                }).sort("created_at", 1).to_list(length=None)
                video_records.extend(video_watch_records)
            
            if video_records:
                # Группируем по часам для детализации
                timeline_data = {}
                for record in video_records:
                    # Используем created_at или last_activity_at из time_activity, или created_at/last_updated из video_watch_time
                    created_at = record.get("created_at") or record.get("last_activity_at") or record.get("last_updated")
                    if created_at:
                        if isinstance(created_at, str):
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        hour_key = created_at.replace(minute=0, second=0, microsecond=0)
                        
                        if hour_key not in timeline_data:
                            timeline_data[hour_key] = {
                                "timestamp": hour_key.isoformat(),
                                "date": hour_key.strftime('%d.%m'),
                                "time": hour_key.strftime('%H:00'),
                                "video_minutes": 0,
                                "is_watching": False,
                                "efficiency": 0.0,
                                "efficiency_count": 0,
                                "planetary_hour": None,
                                "day_planet": None,
                                "lesson_planet": None
                            }
                        
                        lesson_id = record.get("lesson_id")
                        lesson = lessons_dict.get(lesson_id) if lesson_id else None
                        lesson_planet = detect_lesson_planet(lesson.get("title", ""), "") if lesson else None
                        
                        # Получаем информацию о планетарном часе
                        planetary_hour_info = get_planetary_hour_for_datetime(created_at, user_city)
                        current_hour_planet = planetary_hour_info.get("planet")
                        weekday = created_at.weekday()
                        planets_order = ['Chandra', 'Mangal', 'Budh', 'Guru', 'Shukra', 'Shani', 'Surya']
                        day_planet = planets_order[weekday]
                        
                        efficiency = 50.0
                        if user_ruling_planet and lesson_planet:
                            efficiency = calculate_activity_efficiency(
                                user_ruling_planet,
                                lesson_planet,
                                created_at,
                                False,
                                0.0,
                                user_city
                            )
                        
                        # Для time_activity используем total_minutes, для video_watch_time тоже total_minutes
                        video_minutes = record.get("total_minutes", 0)
                        timeline_data[hour_key]["video_minutes"] += video_minutes
                        timeline_data[hour_key]["is_watching"] = True
                        timeline_data[hour_key]["efficiency"] += efficiency
                        timeline_data[hour_key]["efficiency_count"] += 1
                        timeline_data[hour_key]["planetary_hour"] = current_hour_planet
                        timeline_data[hour_key]["day_planet"] = day_planet
                        if lesson_planet:
                            timeline_data[hour_key]["lesson_planet"] = lesson_planet
                
                # Заполняем все часы в периоде (даже без просмотра)
                current = start_date.replace(minute=0, second=0, microsecond=0)
                while current <= end_date:
                    hour_key = current
                    if hour_key not in timeline_data:
                        timeline_data[hour_key] = {
                            "timestamp": hour_key.isoformat(),
                            "date": hour_key.strftime('%d.%m'),
                            "time": hour_key.strftime('%H:00'),
                            "video_minutes": 0,
                            "is_watching": False,
                            "efficiency": 0.0,
                            "efficiency_count": 0
                        }
                    current += timedelta(hours=1)
                
                # Рассчитываем среднюю эффективность для каждого часа
                for hour_key in timeline_data:
                    if timeline_data[hour_key].get("efficiency_count", 0) > 0:
                        timeline_data[hour_key]["efficiency"] = round(
                            timeline_data[hour_key]["efficiency"] / timeline_data[hour_key]["efficiency_count"], 
                            1
                        )
                    if "efficiency_count" in timeline_data[hour_key]:
                        del timeline_data[hour_key]["efficiency_count"]
                
                # Сортируем по времени
                video_timeline = sorted(timeline_data.values(), key=lambda x: x["timestamp"])
            
            return {"timeline": video_timeline, "period": period}
        
        elif section == 'theory-timeline':
            # Детальная аналитика изучения теории с временными метками и эффективностью
            # period: week, month, quarter, day
            # Также поддерживаем start_date и end_date для календаря
            timeline_start_date = None
            timeline_end_date = datetime.utcnow()
            
            # Если указаны даты в параметрах запроса, используем их
            if start_date and end_date:
                try:
                    timeline_start_date = datetime.strptime(start_date, '%Y-%m-%d')
                    timeline_end_date = datetime.strptime(end_date, '%Y-%m-%d')
                    # Добавляем время конца дня
                    timeline_end_date = timeline_end_date.replace(hour=23, minute=59, second=59)
                except Exception as e:
                    logger.error(f"Error parsing dates: {e}")
                    timeline_start_date = None
            
            # Если даты не указаны, используем period
            if timeline_start_date is None:
                if period == 'day':
                    # Один день (24 часа) - сегодня
                    timeline_start_date = timeline_end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    timeline_end_date = timeline_end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                elif period == 'week':
                    timeline_start_date = timeline_end_date - timedelta(days=7)
                elif period == 'month':
                    timeline_start_date = timeline_end_date - timedelta(days=30)
                elif period == 'quarter':
                    timeline_start_date = timeline_end_date - timedelta(days=90)
                else:
                    timeline_start_date = timeline_end_date - timedelta(days=7)
            
            start_date = timeline_start_date
            end_date = timeline_end_date
            
            # УНИФИЦИРОВАННЫЙ ИСТОЧНИК: time_activity - основная коллекция для всех типов активности
            # Получаем данные о просмотре теории с временными метками
            theory_timeline = []
            lessons_cursor = db.lessons_v2.find({"is_active": True})
            lessons = await lessons_cursor.to_list(length=None)
            lessons_dict = {l["id"]: l for l in lessons}
            
            # Используем time_activity как основной источник (activity_type = "theory" или "theory_view")
            theory_records = []
            if "time_activity" in collection_names:
                theory_records_cursor = db.time_activity.find({
                    "user_id": user_id,
                    "$or": [
                        {"last_activity_at": {"$gte": start_date, "$lte": end_date}},
                        {"created_at": {"$gte": start_date, "$lte": end_date}}
                    ],
                    "activity_type": {"$in": ["theory", "theory_view"]}
                })
                async for r in theory_records_cursor:
                    r_dict = dict(r)
                    r_dict.pop("_id", None)
                    theory_records.append(r_dict)
            
            # Дополнительный источник: lesson_progress (для обратной совместимости)
            if "lesson_progress" in collection_names and len(theory_records) == 0:
                lesson_progress_records = await db.lesson_progress.find({
                    "user_id": user_id,
                    "last_accessed": {"$gte": start_date, "$lte": end_date}
                }).sort("last_accessed", 1).to_list(length=None)
                # Преобразуем lesson_progress в формат, совместимый с time_activity
                for lp_record in lesson_progress_records:
                    theory_records.append({
                        "last_accessed": lp_record.get("last_accessed"),
                        "lesson_id": lp_record.get("lesson_id"),
                        "user_id": lp_record.get("user_id"),
                        "activity_type": "theory_view"
                    })
            
            if theory_records:
                # Группируем по часам для детализации
                timeline_data = {}
                for record in theory_records:
                    # Используем last_accessed из lesson_progress или created_at/last_activity_at из time_activity
                    last_accessed = record.get("last_accessed") or record.get("created_at") or record.get("last_activity_at")
                    if last_accessed:
                        if isinstance(last_accessed, str):
                            last_accessed = datetime.fromisoformat(last_accessed.replace('Z', '+00:00'))
                        hour_key = last_accessed.replace(minute=0, second=0, microsecond=0)
                        
                        lesson_id = record.get("lesson_id")
                        lesson = lessons_dict.get(lesson_id) if lesson_id else None
                        lesson_planet = detect_lesson_planet(lesson.get("title", ""), "") if lesson else None
                        
                        efficiency = 50.0
                        if user_ruling_planet and lesson_planet:
                            efficiency = calculate_activity_efficiency(
                                user_ruling_planet,
                                lesson_planet,
                                last_accessed,
                                False,
                                0.0,
                                user_city
                            )
                        
                        if hour_key not in timeline_data:
                            timeline_data[hour_key] = {
                                "timestamp": hour_key.isoformat(),
                                "date": hour_key.strftime('%d.%m'),
                                "time": hour_key.strftime('%H:00'),
                                "theory_sessions": 0,
                                "is_watching": False,  # Добавляем поле is_watching
                                "efficiency": 0.0,
                                "efficiency_count": 0
                            }
                        
                        timeline_data[hour_key]["theory_sessions"] += 1
                        timeline_data[hour_key]["is_watching"] = True  # Устанавливаем is_watching в True при наличии активности
                        timeline_data[hour_key]["efficiency"] += efficiency
                        timeline_data[hour_key]["efficiency_count"] += 1
                
                # Заполняем все часы в периоде (даже без активности)
                current = start_date.replace(minute=0, second=0, microsecond=0)
                while current <= end_date:
                    hour_key = current
                    if hour_key not in timeline_data:
                        timeline_data[hour_key] = {
                            "timestamp": hour_key.isoformat(),
                            "date": hour_key.strftime('%d.%m'),
                            "time": hour_key.strftime('%H:00'),
                            "theory_sessions": 0,
                            "is_watching": False,  # Добавляем поле is_watching
                            "efficiency": 0.0,
                            "efficiency_count": 0
                        }
                    current += timedelta(hours=1)
                
                # Рассчитываем среднюю эффективность для каждого часа
                for hour_key in timeline_data:
                    if timeline_data[hour_key]["efficiency_count"] > 0:
                        timeline_data[hour_key]["efficiency"] = round(
                            timeline_data[hour_key]["efficiency"] / timeline_data[hour_key]["efficiency_count"], 
                            1
                        )
                    del timeline_data[hour_key]["efficiency_count"]
                
                # Сортируем по времени
                theory_timeline = sorted(timeline_data.values(), key=lambda x: x["timestamp"])
            
            return {"timeline": theory_timeline, "period": period}
        
        elif section == 'challenge-timeline':
            # Детальная аналитика выполнения челленджей с временными метками и эффективностью
            # period: week, month, quarter, day
            # Также поддерживаем start_date и end_date для календаря
            timeline_start_date = None
            timeline_end_date = datetime.utcnow()
            
            # Если указаны даты в параметрах запроса, используем их
            if start_date and end_date:
                try:
                    timeline_start_date = datetime.strptime(start_date, '%Y-%m-%d')
                    timeline_end_date = datetime.strptime(end_date, '%Y-%m-%d')
                    # Добавляем время конца дня
                    timeline_end_date = timeline_end_date.replace(hour=23, minute=59, second=59)
                except Exception as e:
                    logger.error(f"Error parsing dates: {e}")
                    timeline_start_date = None
            
            # Если даты не указаны, используем period
            if timeline_start_date is None:
                if period == 'day':
                    # Один день (24 часа) - сегодня
                    timeline_start_date = timeline_end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    timeline_end_date = timeline_end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                elif period == 'week':
                    timeline_start_date = timeline_end_date - timedelta(days=7)
                elif period == 'month':
                    timeline_start_date = timeline_end_date - timedelta(days=30)
                elif period == 'quarter':
                    timeline_start_date = timeline_end_date - timedelta(days=90)
                else:
                    timeline_start_date = timeline_end_date - timedelta(days=7)
            
            start_date = timeline_start_date
            end_date = timeline_end_date
            
            # УНИФИЦИРОВАННЫЙ ИСТОЧНИК: time_activity - основная коллекция для всех типов активности
            # Получаем данные о челленджах с временными метками
            challenge_timeline = []
            lessons_cursor = db.lessons_v2.find({"is_active": True})
            lessons = await lessons_cursor.to_list(length=None)
            lessons_dict = {l["id"]: l for l in lessons}
            
            challenge_records = []
            # Используем time_activity как основной источник (activity_type = "challenge")
            if "time_activity" in collection_names:
                challenge_records_cursor = db.time_activity.find({
            "user_id": user_id,
                    "$or": [
                        {"last_activity_at": {"$gte": start_date, "$lte": end_date}},
                        {"created_at": {"$gte": start_date, "$lte": end_date}}
                    ],
                    "activity_type": "challenge"
                })
                async for r in challenge_records_cursor:
                    r_dict = dict(r)
                    r_dict.pop("_id", None)
                    challenge_records.append(r_dict)
            
            # Дополнительный источник: challenge_progress (для обратной совместимости)
            if "challenge_progress" in collection_names:
                challenge_progress_records = await db.challenge_progress.find({
                    "user_id": user_id,
                    "last_updated": {"$gte": start_date, "$lte": end_date}
                }).sort("last_updated", 1).to_list(length=None)
                # Преобразуем challenge_progress в формат, совместимый с time_activity
                for cp_record in challenge_progress_records:
                    challenge_records.append({
                        "last_updated": cp_record.get("last_updated"),
                        "lesson_id": cp_record.get("lesson_id"),
                        "user_id": cp_record.get("user_id"),
                        "is_completed": cp_record.get("is_completed", False),
                        "completed_days": cp_record.get("completed_days", []),
                        "activity_type": "challenge"
                    })
            
            logger.info(f"Challenge timeline: found {len(challenge_records)} records for period {period}, start_date={start_date}, end_date={end_date}")
            
            # Инициализируем timeline_data для заполнения всех часов
            timeline_data = {}
            
            if challenge_records:
                # Группируем по часам для детализации
                for record in challenge_records:
                    # Используем last_updated из challenge_progress или created_at/last_activity_at из time_activity
                    last_updated = record.get("last_updated") or record.get("created_at") or record.get("last_activity_at")
                    if last_updated:
                        if isinstance(last_updated, str):
                            # Преобразуем строку в datetime, убирая timezone info для совместимости
                            last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                            # Преобразуем в naive datetime (без timezone) для совместимости с БД
                            if last_updated.tzinfo:
                                last_updated = last_updated.replace(tzinfo=None)
                        hour_key = last_updated.replace(minute=0, second=0, microsecond=0)
                        
                        lesson_id = record.get("lesson_id")
                        lesson = lessons_dict.get(lesson_id) if lesson_id else None
                        lesson_planet = detect_lesson_planet(lesson.get("title", ""), "") if lesson else None
                        
                        is_completed = record.get("is_completed", False)
                        completed_days = record.get("completed_days", [])
                        total_days = lesson["challenge"].get("total_days", 0) if lesson and lesson.get("challenge") else 0
                        completion_percentage = (len(completed_days) / total_days * 100) if total_days > 0 else 0
                        
                        efficiency = 50.0
                        if user_ruling_planet and lesson_planet:
                            efficiency = calculate_activity_efficiency(
                                user_ruling_planet,
                                lesson_planet,
                                last_updated,
                                is_completed,
                                completion_percentage,
                                user_city
                            )
                        
                        if hour_key not in timeline_data:
                            timeline_data[hour_key] = {
                                "timestamp": hour_key.isoformat(),
                                "date": hour_key.strftime('%d.%m'),
                                "time": hour_key.strftime('%H:00'),
                                "challenge_updates": 0,
                                "completed_challenges": 0,
                                "efficiency": 0.0,
                                "efficiency_count": 0
                            }
                        
                        timeline_data[hour_key]["challenge_updates"] += 1
                        if is_completed:
                            timeline_data[hour_key]["completed_challenges"] += 1
                        timeline_data[hour_key]["efficiency"] += efficiency
                        timeline_data[hour_key]["efficiency_count"] += 1
            
            # Заполняем все часы в периоде (даже без активности)
            current = start_date.replace(minute=0, second=0, microsecond=0)
            while current <= end_date:
                hour_key = current
                if hour_key not in timeline_data:
                    timeline_data[hour_key] = {
                        "timestamp": hour_key.isoformat(),
                        "date": hour_key.strftime('%d.%m'),
                        "time": hour_key.strftime('%H:00'),
                        "challenge_updates": 0,
                        "completed_challenges": 0,
                        "efficiency": 0.0,
                        "efficiency_count": 0
                    }
                current += timedelta(hours=1)
                
                # Рассчитываем среднюю эффективность для каждого часа
                for hour_key in timeline_data:
                    if "efficiency_count" in timeline_data[hour_key] and timeline_data[hour_key]["efficiency_count"] > 0:
                        timeline_data[hour_key]["efficiency"] = round(
                            timeline_data[hour_key]["efficiency"] / timeline_data[hour_key]["efficiency_count"], 
                            1
                        )
                    if "efficiency_count" in timeline_data[hour_key]:
                        del timeline_data[hour_key]["efficiency_count"]
                
                # Сортируем по времени
                challenge_timeline = sorted(timeline_data.values(), key=lambda x: x["timestamp"])
            
            return {"timeline": challenge_timeline, "period": period}
        
        elif section == 'quiz-timeline':
            # Детальная аналитика прохождения тестов с временными метками и эффективностью
            # period: week, month, quarter, day
            # Также поддерживаем start_date и end_date для календаря
            timeline_start_date = None
            timeline_end_date = datetime.utcnow()
            
            # Если указаны даты в параметрах запроса, используем их
            if start_date and end_date:
                try:
                    timeline_start_date = datetime.strptime(start_date, '%Y-%m-%d')
                    timeline_end_date = datetime.strptime(end_date, '%Y-%m-%d')
                    # Добавляем время конца дня
                    timeline_end_date = timeline_end_date.replace(hour=23, minute=59, second=59)
                except Exception as e:
                    logger.error(f"Error parsing dates: {e}")
                    timeline_start_date = None
            
            # Если даты не указаны, используем period
            if timeline_start_date is None:
                if period == 'day':
                    # Один день (24 часа) - сегодня
                    timeline_start_date = timeline_end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    timeline_end_date = timeline_end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                elif period == 'week':
                    timeline_start_date = timeline_end_date - timedelta(days=7)
                elif period == 'month':
                    timeline_start_date = timeline_end_date - timedelta(days=30)
                elif period == 'quarter':
                    timeline_start_date = timeline_end_date - timedelta(days=90)
                else:
                    timeline_start_date = timeline_end_date - timedelta(days=7)
            
            start_date = timeline_start_date
            end_date = timeline_end_date
            
            # УНИФИЦИРОВАННЫЙ ИСТОЧНИК: time_activity - основная коллекция для всех типов активности
            # Получаем данные о тестах с временными метками
            quiz_timeline = []
            lessons_cursor = db.lessons_v2.find({"is_active": True})
            lessons = await lessons_cursor.to_list(length=None)
            lessons_dict = {l["id"]: l for l in lessons}
            
            quiz_records = []
            # Используем time_activity как основной источник (activity_type = "quiz")
            if "time_activity" in collection_names:
                quiz_records_cursor = db.time_activity.find({
            "user_id": user_id,
                    "$or": [
                        {"last_activity_at": {"$gte": start_date, "$lte": end_date}},
                        {"created_at": {"$gte": start_date, "$lte": end_date}}
                    ],
                    "activity_type": "quiz"
                })
                async for r in quiz_records_cursor:
                    r_dict = dict(r)
                    r_dict.pop("_id", None)
                    quiz_records.append(r_dict)
            
            # Дополнительный источник: quiz_attempts (для обратной совместимости)
            if "quiz_attempts" in collection_names:
                quiz_attempts_records = await db.quiz_attempts.find({
                    "user_id": user_id,
                    "attempted_at": {"$gte": start_date, "$lte": end_date}
                }).sort("attempted_at", 1).to_list(length=None)
                # Преобразуем quiz_attempts в формат, совместимый с time_activity
                for qa_record in quiz_attempts_records:
                    quiz_records.append({
                        "attempted_at": qa_record.get("attempted_at"),
                        "lesson_id": qa_record.get("lesson_id"),
                        "user_id": qa_record.get("user_id"),
                        "passed": qa_record.get("passed", False),
                        "score": qa_record.get("score", 0),
                        "activity_type": "quiz"
                    })
            
            logger.info(f"Quiz timeline: found {len(quiz_records)} records for period {period}, start_date={start_date}, end_date={end_date}")
            
            # Инициализируем timeline_data для заполнения всех часов
            timeline_data = {}
            
            if quiz_records:
                # Группируем по часам для детализации
                for record in quiz_records:
                    # Используем attempted_at из quiz_attempts или created_at/last_activity_at из time_activity
                    attempted_at = record.get("attempted_at") or record.get("created_at") or record.get("last_activity_at")
                    if attempted_at:
                        if isinstance(attempted_at, str):
                            # Преобразуем строку в datetime, убирая timezone info для совместимости
                            attempted_at = datetime.fromisoformat(attempted_at.replace('Z', '+00:00'))
                            # Преобразуем в naive datetime (без timezone) для совместимости с БД
                            if attempted_at.tzinfo:
                                attempted_at = attempted_at.replace(tzinfo=None)
                        hour_key = attempted_at.replace(minute=0, second=0, microsecond=0)
                        
                        lesson_id = record.get("lesson_id")
                        lesson = lessons_dict.get(lesson_id) if lesson_id else None
                        lesson_planet = detect_lesson_planet(lesson.get("title", ""), "") if lesson else None
                        
                        efficiency = 50.0
                        if user_ruling_planet and lesson_planet:
                            efficiency = calculate_activity_efficiency(
                                user_ruling_planet,
                                lesson_planet,
                                attempted_at,
                                False,
                                0.0,
                                user_city
                            )
                        
                        # Учитываем результат теста в эффективности
                        is_passed = record.get("passed", False) or record.get("is_passed", False)
                        score = record.get("score", 0)
                        max_score = record.get("max_possible_score", 100)
                        score_percentage = (score / max_score * 100) if max_score > 0 else 0
                        
                        # Если тест пройден успешно, увеличиваем эффективность
                        if is_passed:
                            efficiency = min(100.0, efficiency + (score_percentage * 0.2))
                        
                        if hour_key not in timeline_data:
                            timeline_data[hour_key] = {
                                "timestamp": hour_key.isoformat(),
                                "date": hour_key.strftime('%d.%m'),
                                "time": hour_key.strftime('%H:00'),
                                "quiz_attempts": 0,
                                "passed_quizzes": 0,
                                "avg_score": 0.0,
                                "total_score": 0.0,
                                "score_count": 0,
                                "efficiency": 0.0,
                                "efficiency_count": 0
                            }
                        
                        timeline_data[hour_key]["quiz_attempts"] += 1
                        if is_passed:
                            timeline_data[hour_key]["passed_quizzes"] += 1
                        timeline_data[hour_key]["total_score"] += score_percentage
                        timeline_data[hour_key]["score_count"] += 1
                        timeline_data[hour_key]["efficiency"] += efficiency
                        timeline_data[hour_key]["efficiency_count"] += 1
            
            # Заполняем все часы в периоде (даже без активности)
            current = start_date.replace(minute=0, second=0, microsecond=0)
            while current <= end_date:
                hour_key = current
                if hour_key not in timeline_data:
                    timeline_data[hour_key] = {
                        "timestamp": hour_key.isoformat(),
                        "date": hour_key.strftime('%d.%m'),
                        "time": hour_key.strftime('%H:00'),
                        "quiz_attempts": 0,
                        "passed_quizzes": 0,
                        "avg_score": 0.0,
                        "total_score": 0.0,
                        "score_count": 0,
                        "efficiency": 0.0,
                        "efficiency_count": 0
                    }
                current += timedelta(hours=1)
                
                # Рассчитываем средние значения для каждого часа
                for hour_key in timeline_data:
                    if "score_count" in timeline_data[hour_key] and timeline_data[hour_key]["score_count"] > 0:
                        timeline_data[hour_key]["avg_score"] = round(
                            timeline_data[hour_key]["total_score"] / timeline_data[hour_key]["score_count"], 
                            1
                        )
                    if "efficiency_count" in timeline_data[hour_key] and timeline_data[hour_key]["efficiency_count"] > 0:
                        timeline_data[hour_key]["efficiency"] = round(
                            timeline_data[hour_key]["efficiency"] / timeline_data[hour_key]["efficiency_count"], 
                            1
                        )
                    if "total_score" in timeline_data[hour_key]:
                        del timeline_data[hour_key]["total_score"]
                    if "score_count" in timeline_data[hour_key]:
                        del timeline_data[hour_key]["score_count"]
                    if "efficiency_count" in timeline_data[hour_key]:
                        del timeline_data[hour_key]["efficiency_count"]
                
                # Сортируем по времени
                quiz_timeline = sorted(timeline_data.values(), key=lambda x: x["timestamp"])
            
            return {"timeline": quiz_timeline, "period": period}
        
        elif section == 'challenges':
            # Детальная аналитика по челленджам
            challenge_details = []
            if "challenge_progress" in collection_names:
                challenge_cursor = db.challenge_progress.find({"user_id": user_id})
                challenge_attempts = await challenge_cursor.to_list(length=None)
                
                lessons_cursor = db.lessons_v2.find({"is_active": True})
                lessons = await lessons_cursor.to_list(length=None)
                lessons_dict = {l["id"]: l for l in lessons}
                
                for attempt in challenge_attempts:
                    lesson = lessons_dict.get(attempt.get("lesson_id"))
                    challenge = lesson.get("challenge") if lesson else None
                    
                    # Время на челлендж
                    challenge_time = 0
                    if "time_activity" in collection_names:
                        time_records = await db.time_activity.find({
            "user_id": user_id,
                            "lesson_id": attempt.get("lesson_id")
                        }).to_list(length=None)
                        challenge_time = sum(r.get("total_minutes", 0) for r in time_records)
                    
                    challenge_details.append({
                        "lesson_id": attempt.get("lesson_id"),
                        "lesson_title": lesson.get("title", "Урок") if lesson else "Урок",
                        "challenge_id": attempt.get("challenge_id"),
                        "current_day": attempt.get("current_day", 0),
                        "completed_days": attempt.get("completed_days", []),
                        "total_days": challenge.get("total_days", 0) if challenge else 0,
                        "completion_percentage": round((len(attempt.get("completed_days", [])) / challenge.get("total_days", 1)) * 100, 1) if challenge and challenge.get("total_days") else 0,
                        "is_completed": attempt.get("is_completed", False),
                        "points_earned": attempt.get("points_earned", 0),
                        "time_minutes": challenge_time,
                        "daily_notes": attempt.get("daily_notes", []),
                        "started_at": attempt.get("started_at").isoformat() if attempt.get("started_at") else None,
                        "completed_at": attempt.get("completed_at").isoformat() if attempt.get("completed_at") else None,
                        "last_updated": attempt.get("last_updated").isoformat() if attempt.get("last_updated") else None
                    })
            
            logger.info(f"Returning {len(challenge_details)} challenge details")
            return {"analytics": challenge_details}
        
        elif section == 'quizzes':
            # Детальная аналитика по тестам
            quiz_details = []
            if "quiz_attempts" in collection_names:
                quiz_cursor = db.quiz_attempts.find({"user_id": user_id})
                quiz_attempts = await quiz_cursor.to_list(length=None)
                
                lessons_cursor = db.lessons_v2.find({"is_active": True})
                lessons = await lessons_cursor.to_list(length=None)
                lessons_dict = {l["id"]: l for l in lessons}
                
                # Группируем по урокам
                attempts_by_lesson = {}
                for attempt in quiz_attempts:
                    lesson_id = attempt.get("lesson_id")
                    if lesson_id not in attempts_by_lesson:
                        attempts_by_lesson[lesson_id] = []
                    attempts_by_lesson[lesson_id].append(attempt)
                
                for lesson_id, attempts in attempts_by_lesson.items():
                    lesson = lessons_dict.get(lesson_id)
                    quiz = lesson.get("quiz") if lesson else None
                    max_possible_score = sum(q.get("points", 10) for q in quiz.get("questions", [])) if quiz and quiz.get("questions") else 100
                    
                    quiz_details.append({
                        "lesson_id": lesson_id,
                        "lesson_title": lesson.get("title", "Урок") if lesson else "Урок",
                        "total_attempts": len(attempts),
                        "passed_attempts": sum(1 for a in attempts if a.get("passed", False)),
                        "best_score": max(a.get("score", 0) for a in attempts),
                        "avg_score": round(sum(a.get("score", 0) for a in attempts) / len(attempts), 1) if attempts else 0,
                        "max_possible_score": max_possible_score,
                        "total_points_earned": sum(a.get("points_earned", 0) for a in attempts),
                        "total_time_minutes": sum(a.get("time_spent_minutes", 0) for a in attempts),
                        "attempts": [
                            {
                                "attempt_id": a.get("id"),
                                "score": a.get("score", 0),
                                "score_percentage": round((a.get("score", 0) / max_possible_score) * 100, 1) if max_possible_score > 0 else 0,
                                "passed": a.get("passed", False),
                                "points_earned": a.get("points_earned", 0),
                                "attempted_at": a.get("attempted_at").isoformat() if a.get("attempted_at") else None,
                                "time_spent_minutes": a.get("time_spent_minutes", 0)
                            }
                            for a in attempts
                        ]
                    })
            
            logger.info(f"Returning {len(quiz_details)} quiz details")
            return {"analytics": quiz_details}
        
        elif section == 'exercises':
            # Детальная аналитика по упражнениям
            exercise_details = []
            if "exercise_responses" in collection_names:
                exercise_cursor = db.exercise_responses.find({"user_id": user_id})
                exercise_responses = await exercise_cursor.to_list(length=None)
                
                lessons_cursor = db.lessons_v2.find({"is_active": True})
                lessons = await lessons_cursor.to_list(length=None)
                lessons_dict = {l["id"]: l for l in lessons}
                
                # Группируем по урокам
                responses_by_lesson = {}
                for response in exercise_responses:
                    lesson_id = response.get("lesson_id")
                    if lesson_id not in responses_by_lesson:
                        responses_by_lesson[lesson_id] = []
                    responses_by_lesson[lesson_id].append(response)
                
                for lesson_id, responses in responses_by_lesson.items():
                    lesson = lessons_dict.get(lesson_id)
                    
                    exercise_details.append({
            "lesson_id": lesson_id,
                        "lesson_title": lesson.get("title", "Урок") if lesson else "Урок",
                        "total_exercises": len(responses),
                        "reviewed_exercises": sum(1 for r in responses if r.get("reviewed", False)),
                        "total_points_earned": sum(r.get("points_earned", 0) for r in responses),
                        "total_review_time_minutes": sum(r.get("review_time_minutes", 0) for r in responses),
                        "exercises": [
                            {
                                "exercise_id": r.get("exercise_id"),
                                "response_text": r.get("response_text", ""),
                                "points_earned": r.get("points_earned", 0),
                                "reviewed": r.get("reviewed", False),
                                "admin_comment": r.get("admin_comment", ""),
                                "submitted_at": r.get("submitted_at").isoformat() if r.get("submitted_at") else None,
                                "reviewed_at": r.get("reviewed_at").isoformat() if r.get("reviewed_at") else None,
                                "review_time_minutes": r.get("review_time_minutes", 0)
                            }
                            for r in responses
                        ]
                    })
            
            logger.info(f"Returning {len(exercise_details)} exercise details")
            return {"analytics": exercise_details}
        
        elif section == 'exercise-timeline':
            # Детальная аналитика выполнения упражнений с временными метками и эффективностью
            # period: week, month, quarter, day
            # Также поддерживаем start_date и end_date для календаря
            timeline_start_date = None
            timeline_end_date = datetime.utcnow()
            
            # Если указаны даты в параметрах запроса, используем их
            if start_date and end_date:
                try:
                    timeline_start_date = datetime.strptime(start_date, '%Y-%m-%d')
                    timeline_end_date = datetime.strptime(end_date, '%Y-%m-%d')
                    # Добавляем время конца дня
                    timeline_end_date = timeline_end_date.replace(hour=23, minute=59, second=59)
                except Exception as e:
                    logger.error(f"Error parsing dates: {e}")
                    timeline_start_date = None
            
            # Если даты не указаны, используем period
            if timeline_start_date is None:
                if period == 'day':
                    # Один день (24 часа) - сегодня
                    timeline_start_date = timeline_end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    timeline_end_date = timeline_end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                elif period == 'week':
                    timeline_start_date = timeline_end_date - timedelta(days=7)
                elif period == 'month':
                    timeline_start_date = timeline_end_date - timedelta(days=30)
                elif period == 'quarter':
                    timeline_start_date = timeline_end_date - timedelta(days=90)
                else:
                    timeline_start_date = timeline_end_date - timedelta(days=7)
            
            start_date = timeline_start_date
            end_date = timeline_end_date
            
            # УНИФИЦИРОВАННЫЙ ИСТОЧНИК: time_activity - основная коллекция для всех типов активности
            # Получаем данные об упражнениях с временными метками
            exercise_timeline = []
            lessons_cursor = db.lessons_v2.find({"is_active": True})
            lessons = await lessons_cursor.to_list(length=None)
            lessons_dict = {l["id"]: l for l in lessons}
            
            exercise_records = []
            # Используем time_activity как основной источник (activity_type = "exercise")
            if "time_activity" in collection_names:
                exercise_records_cursor = db.time_activity.find({
            "user_id": user_id,
                    "$or": [
                        {"last_activity_at": {"$gte": start_date, "$lte": end_date}},
                        {"created_at": {"$gte": start_date, "$lte": end_date}}
                    ],
                    "activity_type": "exercise"
                })
                async for r in exercise_records_cursor:
                    r_dict = dict(r)
                    r_dict.pop("_id", None)
                    exercise_records.append(r_dict)
            
            # Дополнительный источник: exercise_responses (для обратной совместимости)
            if "exercise_responses" in collection_names:
                exercise_responses_records = await db.exercise_responses.find({
                    "user_id": user_id,
                    "submitted_at": {"$gte": start_date, "$lte": end_date}
                }).sort("submitted_at", 1).to_list(length=None)
                # Преобразуем exercise_responses в формат, совместимый с time_activity
                for er_record in exercise_responses_records:
                    exercise_records.append({
                        "submitted_at": er_record.get("submitted_at"),
                        "lesson_id": er_record.get("lesson_id"),
                        "user_id": er_record.get("user_id"),
                        "exercise_id": er_record.get("exercise_id"),
                        "reviewed": er_record.get("reviewed", False),
                        "points_earned": er_record.get("points_earned", 0),
                        "activity_type": "exercise"
                    })
            
            logger.info(f"Exercise timeline: found {len(exercise_records)} records for period {period}, start_date={start_date}, end_date={end_date}")
            
            # Инициализируем timeline_data для заполнения всех часов
            timeline_data = {}
            
            if exercise_records:
                # Группируем по часам для детализации
                for record in exercise_records:
                    # Используем submitted_at из exercise_responses или created_at/last_activity_at из time_activity
                    submitted_at = record.get("submitted_at") or record.get("created_at") or record.get("last_activity_at")
                    if submitted_at:
                        if isinstance(submitted_at, str):
                            # Преобразуем строку в datetime, убирая timezone info для совместимости
                            submitted_at = datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
                            # Преобразуем в naive datetime (без timezone) для совместимости с БД
                            if submitted_at.tzinfo:
                                submitted_at = submitted_at.replace(tzinfo=None)
                        hour_key = submitted_at.replace(minute=0, second=0, microsecond=0)
                        
                        lesson_id = record.get("lesson_id")
                        lesson = lessons_dict.get(lesson_id) if lesson_id else None
                        lesson_planet = detect_lesson_planet(lesson.get("title", ""), "") if lesson else None
                        
                        efficiency = 50.0
                        if user_ruling_planet and lesson_planet:
                            efficiency = calculate_activity_efficiency(
                                user_ruling_planet,
                                lesson_planet,
                                submitted_at,
                                False,
                                0.0,
                                user_city
                            )
                        
                        # Учитываем, что упражнение проверено
                        is_reviewed = record.get("reviewed", False)
                        points_earned = record.get("points_earned", 0) or record.get("total_points", 0)
                        if is_reviewed and points_earned > 0:
                            efficiency = min(100.0, efficiency + (points_earned * 0.5))
                        
                        if hour_key not in timeline_data:
                            timeline_data[hour_key] = {
                                "timestamp": hour_key.isoformat(),
                                "date": hour_key.strftime('%d.%m'),
                                "time": hour_key.strftime('%H:00'),
                                "exercise_submissions": 0,
                                "reviewed_exercises": 0,
                                "total_points": 0,
                                "efficiency": 0.0,
                                "efficiency_count": 0
                            }
                        
                        timeline_data[hour_key]["exercise_submissions"] += 1
                        if is_reviewed:
                            timeline_data[hour_key]["reviewed_exercises"] += 1
                        timeline_data[hour_key]["total_points"] += points_earned
                        timeline_data[hour_key]["efficiency"] += efficiency
                        timeline_data[hour_key]["efficiency_count"] += 1
            
            # Заполняем все часы в периоде (даже без активности)
            current = start_date.replace(minute=0, second=0, microsecond=0)
            while current <= end_date:
                hour_key = current
                if hour_key not in timeline_data:
                    timeline_data[hour_key] = {
                        "timestamp": hour_key.isoformat(),
                        "date": hour_key.strftime('%d.%m'),
                        "time": hour_key.strftime('%H:00'),
                        "exercise_submissions": 0,
                        "reviewed_exercises": 0,
                        "total_points": 0,
                        "efficiency": 0.0,
                        "efficiency_count": 0
                    }
                current += timedelta(hours=1)
            
            # Рассчитываем среднюю эффективность для каждого часа
            for hour_key in timeline_data:
                if "efficiency_count" in timeline_data[hour_key] and timeline_data[hour_key]["efficiency_count"] > 0:
                    timeline_data[hour_key]["efficiency"] = round(
                        timeline_data[hour_key]["efficiency"] / timeline_data[hour_key]["efficiency_count"], 
                        1
                    )
                if "efficiency_count" in timeline_data[hour_key]:
                    del timeline_data[hour_key]["efficiency_count"]
            
            # Сортируем по времени
            exercise_timeline = sorted(timeline_data.values(), key=lambda x: x["timestamp"])
            
            return {"timeline": exercise_timeline, "period": period}
        
        else:
            raise HTTPException(status_code=400, detail="Invalid section. Must be: lessons, challenges, quizzes, exercises, or exercise-timeline")
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error getting detailed analytics for {section}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting analytics: {str(e)}")

@app.get("/api/user/consultations")
async def get_user_consultations(current_user: dict = Depends(get_current_user)):
    """Получить список консультаций для текущего пользователя"""
    try:
        user_id = current_user.get('user_id', current_user.get('id'))
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        collection_names = await db.list_collection_names()
        
        consultations = []
        if "personal_consultations" in collection_names:
            # Получаем консультации, назначенные пользователю
            consultations_cursor = db.personal_consultations.find({
                "assigned_user_id": user_id
            })
            consultations_list = await consultations_cursor.to_list(length=None)
            
            # Получаем информацию о покупках
            purchases = {}
            if "consultation_purchases" in collection_names:
                purchases_cursor = db.consultation_purchases.find({
                    "user_id": user_id
                })
                purchases_list = await purchases_cursor.to_list(length=None)
                purchases = {p.get("consultation_id"): p for p in purchases_list}
            
            for consultation in consultations_list:
                consultation_dict = dict(consultation)
                consultation_dict.pop('_id', None)
                
                # Проверяем, куплена ли консультация
                purchase = purchases.get(consultation.get("id"))
                consultation_dict["is_purchased"] = purchase is not None
                consultation_dict["purchased_at"] = purchase.get("purchased_at").isoformat() if purchase and purchase.get("purchased_at") else None
                
                consultations.append(consultation_dict)
        
        return consultations
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error getting user consultations: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Возвращаем пустой список вместо ошибки, чтобы не ломать фронтенд
        return []

@app.post("/api/user/consultations/{consultation_id}/purchase")
async def purchase_consultation(consultation_id: str, current_user: dict = Depends(get_current_user)):
    """Купить консультацию за баллы"""
    try:
        user_id = current_user.get('user_id', current_user.get('id'))
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Получаем информацию о пользователе
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Получаем информацию о консультации
        consultation = await db.personal_consultations.find_one({"id": consultation_id})
        if not consultation:
            raise HTTPException(status_code=404, detail="Consultation not found")

        cost_credits = consultation.get("cost_credits", 0)
        user_credits = user.get("credits_remaining", 0)

        if user_credits < cost_credits:
            raise HTTPException(status_code=402, detail="Insufficient credits")

        # Проверяем, не куплена ли уже консультация
        existing_purchase = await db.consultation_purchases.find_one({
            "user_id": user_id,
            "consultation_id": consultation_id
        })
        if existing_purchase:
            raise HTTPException(status_code=400, detail="Consultation already purchased")

        # Списываем баллы
        await db.users.update_one(
            {"id": user_id},
            {"$inc": {"credits_remaining": -cost_credits}}
        )

        # Создаем запись о покупке
        purchase_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "consultation_id": consultation_id,
            "purchased_at": datetime.utcnow(),
            "cost_credits": cost_credits
        }
        await db.consultation_purchases.insert_one(purchase_data)

        # Записываем транзакцию
        await db.credit_transactions.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "amount": -cost_credits,
            "transaction_type": "consultation_purchase",
            "description": f"Покупка консультации: {consultation.get('title', 'Консультация')}",
            "created_at": datetime.utcnow()
        })

        return {"message": "Consultation purchased successfully", "purchase": purchase_data}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error purchasing consultation: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error purchasing consultation: {str(e)}")

# ==================== ADMIN CONSULTATIONS API ====================

@app.get("/api/admin/consultations")
async def get_all_consultations(current_user: dict = Depends(get_current_user)):
    """Получить все консультации для админа"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        collection_names = await db.list_collection_names()
        consultations = []
        
        if "personal_consultations" in collection_names:
            consultations_cursor = db.personal_consultations.find({})
            consultations_list = await consultations_cursor.to_list(length=None)
            
            for consultation in consultations_list:
                consultation_dict = dict(consultation)
                consultation_dict.pop('_id', None)
                consultations.append(consultation_dict)
        
        return consultations

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error getting consultations: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting consultations: {str(e)}")

@app.post("/api/admin/consultations")
async def create_consultation(consultation_data: dict, current_user: dict = Depends(get_current_user)):
    """Создать новую консультацию"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        consultation = {
            "id": str(uuid.uuid4()),
            "title": consultation_data.get("title", ""),
            "description": consultation_data.get("description", ""),
            "video_url": consultation_data.get("video_url"),
            "video_file_id": consultation_data.get("video_file_id"),
            "pdf_file_id": consultation_data.get("pdf_file_id"),
            "subtitles_file_id": consultation_data.get("subtitles_file_id"),
            "assigned_user_id": consultation_data.get("assigned_user_id", ""),
            "cost_credits": consultation_data.get("cost_credits", 6667),
            "is_active": consultation_data.get("is_active", True),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        await db.personal_consultations.insert_one(consultation)
        consultation.pop('_id', None)
        
        return consultation

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error creating consultation: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error creating consultation: {str(e)}")

@app.put("/api/admin/consultations/{consultation_id}")
async def update_consultation(consultation_id: str, consultation_data: dict, current_user: dict = Depends(get_current_user)):
    """Обновить консультацию"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        # Проверяем существование консультации
        existing = await db.personal_consultations.find_one({"id": consultation_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Consultation not found")

        # Обновляем данные
        update_data = {
            "$set": {
                "title": consultation_data.get("title", existing.get("title")),
                "description": consultation_data.get("description", existing.get("description")),
                "video_url": consultation_data.get("video_url", existing.get("video_url")),
                "video_file_id": consultation_data.get("video_file_id", existing.get("video_file_id")),
                "pdf_file_id": consultation_data.get("pdf_file_id", existing.get("pdf_file_id")),
                "subtitles_file_id": consultation_data.get("subtitles_file_id", existing.get("subtitles_file_id")),
                "assigned_user_id": consultation_data.get("assigned_user_id", existing.get("assigned_user_id")),
                "cost_credits": consultation_data.get("cost_credits", existing.get("cost_credits", 6667)),
                "is_active": consultation_data.get("is_active", existing.get("is_active", True)),
                "updated_at": datetime.utcnow()
            }
        }

        await db.personal_consultations.update_one({"id": consultation_id}, update_data)
        
        updated = await db.personal_consultations.find_one({"id": consultation_id})
        updated.pop('_id', None)
        
        return updated

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error updating consultation: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error updating consultation: {str(e)}")

@app.delete("/api/admin/consultations/{consultation_id}")
async def delete_consultation(consultation_id: str, current_user: dict = Depends(get_current_user)):
    """Удалить консультацию"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        result = await db.personal_consultations.delete_one({"id": consultation_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Consultation not found")

        return {"message": "Consultation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error deleting consultation: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error deleting consultation: {str(e)}")

@app.post("/api/admin/consultations/upload-video")
async def upload_consultation_video(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Загрузить видео для консультации"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        # Сохраняем файл
        upload_dir = Path("uploads/consultations")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Сохраняем информацию о файле в базу
        file_record = {
            "id": str(uuid.uuid4()),
            "original_name": file.filename,
            "stored_name": unique_filename,
            "file_path": str(file_path),
            "file_type": "video",
            "mime_type": file.content_type,
            "file_size": file_path.stat().st_size,
            "uploaded_by": user_id,
            "uploaded_at": datetime.utcnow()
        }

        await db.files.insert_one(file_record)
        
        return {
            "file_id": file_record["id"],
            "filename": file.filename,
            "file_path": str(file_path),
            "file_size": file_record["file_size"]
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error uploading video: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error uploading video: {str(e)}")

@app.post("/api/admin/consultations/upload-pdf")
async def upload_consultation_pdf(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Загрузить PDF для консультации"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        # Сохраняем файл
        upload_dir = Path("uploads/consultations")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Сохраняем информацию о файле в базу
        file_record = {
            "id": str(uuid.uuid4()),
            "original_name": file.filename,
            "stored_name": unique_filename,
            "file_path": str(file_path),
            "file_type": "pdf",
            "mime_type": file.content_type,
            "file_size": file_path.stat().st_size,
            "uploaded_by": user_id,
            "uploaded_at": datetime.utcnow()
        }

        await db.files.insert_one(file_record)
        
        return {
            "file_id": file_record["id"],
            "filename": file.filename,
            "file_path": str(file_path),
            "file_size": file_record["file_size"]
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error uploading PDF: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error uploading PDF: {str(e)}")

@app.post("/api/admin/consultations/upload-subtitles")
async def upload_consultation_subtitles(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Загрузить субтитры для консультации"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        # Сохраняем файл
        upload_dir = Path("uploads/consultations/subtitles")
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Сохраняем информацию о файле в базу
        file_record = {
            "id": str(uuid.uuid4()),
            "original_name": file.filename,
            "stored_name": unique_filename,
            "file_path": str(file_path),
            "file_type": "subtitles",
            "mime_type": file.content_type,
            "file_size": file_path.stat().st_size,
            "uploaded_by": user_id,
            "uploaded_at": datetime.utcnow()
        }

        await db.files.insert_one(file_record)
        
        return {
            "file_id": file_record["id"],
            "filename": file.filename,
            "file_path": str(file_path),
            "file_size": file_record["file_size"]
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error uploading subtitles: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error uploading subtitles: {str(e)}")

@app.get("/api/student/lesson-progress/{lesson_id}")
async def get_lesson_progress(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Получить прогресс урока для студента"""
    try:
        user_id = current_user.get('user_id', current_user.get('id'))

        # Получаем урок
        lesson = await db.lessons_v2.find_one({"id": lesson_id})
        if not lesson:
            raise HTTPException(status_code=404, detail="Урок не найден")

        now = datetime.utcnow()
        
        # ЗАПИСЫВАЕМ В time_activity с типом "lesson_view" при открытии урока
        # Проверяем, есть ли уже запись за сегодня
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        existing_activity = await db.time_activity.find_one({
            "user_id": user_id,
            "lesson_id": lesson_id,
            "activity_type": "lesson_view",
            "created_at": {"$gte": today_start}
        })
        
        if not existing_activity:
            # Создаем новую запись в time_activity для отслеживания присутствия в уроке
            activity_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "lesson_id": lesson_id,
                "activity_type": "lesson_view",
                "total_minutes": 0,  # Время будет обновляться через save_time_activity
                "total_points": 0,
                "created_at": now,
                "last_activity_at": now
            }
            await db.time_activity.insert_one(activity_data)

        # Получаем прогресс урока
        progress = await db.lesson_progress.find_one({"user_id": user_id, "lesson_id": lesson_id})
        if not progress:
            # Создаем начальный прогресс
            progress = {
                "user_id": user_id,
                "lesson_id": lesson_id,
                "is_completed": False,
                "completion_percentage": 0,
                "theory_read": False,
                "exercises_completed": 0,
                "challenge_started": False,
                "challenge_completed": False,
                "quiz_passed": False,
                "started_at": now,
                "last_activity_at": now,
                "last_accessed": now  # Добавляем last_accessed для отслеживания просмотра теории
            }
            # Сохраняем прогресс в базу
            await db.lesson_progress.insert_one(progress)
            
            # ЗАПИСЫВАЕМ В time_activity с типом "theory_view" при первом открытии урока
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            existing_theory_activity = await db.time_activity.find_one({
                "user_id": user_id,
                "lesson_id": lesson_id,
                "activity_type": {"$in": ["theory", "theory_view"]},
                "created_at": {"$gte": today_start}
            })
            
            if not existing_theory_activity:
                # Создаем новую запись в time_activity для отслеживания просмотра теории
                theory_activity_data = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "lesson_id": lesson_id,
                    "activity_type": "theory_view",
                    "total_minutes": 0,
                    "total_points": 0,
                    "created_at": now,
                    "last_activity_at": now
                }
                await db.time_activity.insert_one(theory_activity_data)
        else:
            progress = dict(progress)
            progress.pop('_id', None)
            # Обновляем last_accessed при каждом открытии урока
            await db.lesson_progress.update_one(
                {"user_id": user_id, "lesson_id": lesson_id},
                {"$set": {"last_accessed": now, "last_activity_at": now}}
            )
            progress["last_accessed"] = now
            
            # ЗАПИСЫВАЕМ В time_activity с типом "theory_view" при открытии урока (для отслеживания просмотра теории)
            # Проверяем, есть ли уже запись за сегодня
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            existing_theory_activity = await db.time_activity.find_one({
                "user_id": user_id,
                "lesson_id": lesson_id,
                "activity_type": {"$in": ["theory", "theory_view"]},
                "created_at": {"$gte": today_start}
            })
            
            if not existing_theory_activity:
                # Создаем новую запись в time_activity для отслеживания просмотра теории
                theory_activity_data = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "lesson_id": lesson_id,
                    "activity_type": "theory_view",
                    "total_minutes": 0,
                    "total_points": 0,
                    "created_at": now,
                    "last_activity_at": now
                }
                await db.time_activity.insert_one(theory_activity_data)

        return progress

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error getting lesson progress: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting lesson progress: {str(e)}")

@app.post("/api/student/exercise-response")
async def save_exercise_response(request_data: dict, current_user: dict = Depends(get_current_user)):
    """Сохранить ответ на упражнение"""
    try:
        user_id = current_user.get('user_id', current_user.get('id'))

        exercise_response_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "lesson_id": request_data["lesson_id"],
            "exercise_id": request_data["exercise_id"],
            "response_text": request_data["response_text"],
            "submitted_at": datetime.utcnow(),
            "reviewed": False
        }

        # Сохраняем или обновляем ответ
        existing_response = await db.exercise_responses.find_one({
            "user_id": user_id,
            "lesson_id": request_data["lesson_id"],
            "exercise_id": request_data["exercise_id"]
        })

        if existing_response:
            # Обновляем существующий
            await db.exercise_responses.update_one(
                {"_id": existing_response["_id"]},
                {"$set": {
                    "response_text": request_data["response_text"],
                    "submitted_at": datetime.utcnow(),
                    "reviewed": False,
                    "admin_comment": None,
                    "reviewed_at": None,
                    "reviewed_by": None
                }}
            )
            exercise_response_data["id"] = existing_response["id"]
        else:
            # Создаем новый
            result = await db.exercise_responses.insert_one(exercise_response_data)
            
            # Начисляем кредиты за выполнение упражнения (только для новых ответов)
            points_config = await get_learning_points_config()
            exercise_points = points_config.get('exercise_points_per_submission', 10)
            
            await award_credits_for_learning(
                user_id=user_id,
                amount=exercise_points,
                description=f"Выполнение упражнения урока {request_data['lesson_id']}",
                category='exercise',
                details={
                    'lesson_id': request_data['lesson_id'],
                    'exercise_id': request_data['exercise_id'],
                    'points': exercise_points
                }
            )
            
            # ЗАПИСЫВАЕМ В time_activity с типом "exercise" для унифицированной аналитики
            now = datetime.utcnow()
            existing_activity = await db.time_activity.find_one({
                "user_id": user_id,
                "lesson_id": request_data["lesson_id"],
                "activity_type": "exercise"
            })
            
            if existing_activity:
                # Обновляем существующую запись
                await db.time_activity.update_one(
                    {"_id": existing_activity["_id"]},
                    {"$set": {"last_activity_at": now}}
                )
            else:
                # Создаем новую запись в time_activity
                activity_data = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "lesson_id": request_data["lesson_id"],
                    "activity_type": "exercise",
                    "total_minutes": 0,
                    "total_points": exercise_points,
                    "created_at": now,
                    "last_activity_at": now
                }
                await db.time_activity.insert_one(activity_data)

        # Обновляем прогресс урока
        await update_lesson_progress(user_id, request_data["lesson_id"])
        
        return {
            "message": "Ответ сохранен успешно",
            "response_id": exercise_response_data["id"]
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Error saving exercise response: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error saving exercise response: {str(e)}")

@app.get("/api/student/exercise-responses/{lesson_id}")
async def get_exercise_responses(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Получить все ответы на упражнения урока"""
    try:
        user_id = current_user.get('user_id', current_user.get('id'))

        responses = await db.exercise_responses.find({
            "user_id": user_id,
            "lesson_id": lesson_id
        }).to_list(length=None)

        # Группируем по exercise_id
        exercise_responses = {}
        for response in responses:
            response_dict = dict(response)
            response_dict.pop('_id', None)
            exercise_responses[response["exercise_id"]] = response_dict
        
        return {
            "exercise_responses": exercise_responses
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Error getting exercise responses: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting exercise responses: {str(e)}")

@app.post("/api/student/challenge-progress")
async def save_challenge_progress(request_data: dict, current_user: dict = Depends(get_current_user)):
    """Сохранить прогресс челленджа (заметки, завершение дня, начисление баллов)"""
    try:
        user_id = current_user.get('user_id', current_user.get('id'))
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        lesson_id = request_data.get("lesson_id")
        challenge_id = request_data.get("challenge_id")
        day = int(request_data.get("day", 0))
        note_text = request_data.get("note", "")
        mark_completed = bool(request_data.get("completed", False))

        if not lesson_id or not challenge_id or day <= 0:
            raise HTTPException(status_code=400, detail="Invalid challenge progress payload")

        # Получаем урок, чтобы взять параметры челленджа
        lesson = await db.lessons_v2.find_one({"id": lesson_id})
        challenge = lesson.get("challenge", {}) if lesson else {}
        total_days = challenge.get("duration_days", 7)
        
        # Получаем настройки начисления баллов из конфигурации
        points_config = await get_learning_points_config()
        points_per_day = challenge.get("points_per_day") or points_config.get('challenge_points_per_day', 10)
        bonus_points = challenge.get("bonus_points") or points_config.get('challenge_bonus_points', 50)

        # Получаем существующий прогресс (активную попытку)
        existing_progress = await db.challenge_progress.find_one({
            "user_id": user_id,
            "lesson_id": lesson_id,
            "challenge_id": challenge_id,
            "is_completed": False
        })

        now = datetime.utcnow()

        if existing_progress:
            daily_notes = existing_progress.get("daily_notes", [])
            completed_days = existing_progress.get("completed_days", [])

            # Обновляем или добавляем заметку
            note_found = False
            for note_item in daily_notes:
                if int(note_item.get("day", 0)) == day:
                    note_item["day"] = day
                    note_item["note"] = note_text
                    note_item["updated_at"] = now
                    note_item["completed_at"] = now
                    note_found = True
                    break

            if not note_found:
                daily_notes.append({
                    "day": day,
                    "note": note_text,
                    "updated_at": now,
                    "completed_at": now
                })

            # Обновляем список завершенных дней
            day_was_newly_completed = False
            if mark_completed and day not in completed_days:
                completed_days.append(day)
                day_was_newly_completed = True

            # Пересчитываем показатели
            completed_days = sorted(set(completed_days))
            completed_count = len(completed_days)
            is_completed = completed_count >= total_days
            was_already_completed = existing_progress.get("is_completed", False)
            current_day = min(total_days, max(completed_days) + 1) if completed_days else max(existing_progress.get("current_day", 1), 1)

            points_earned = completed_count * points_per_day
            if is_completed:
                points_earned += bonus_points

            update_data = {
                "current_day": current_day,
                "completed_days": completed_days,
                "daily_notes": daily_notes,
                "is_completed": is_completed,
                "points_earned": points_earned,
                "total_points": points_earned,
                "last_updated": now
            }

            if is_completed and not existing_progress.get("completed_at"):
                update_data["completed_at"] = now
            
            # Начисляем кредиты за завершение дня (только если день был только что завершен)
            if day_was_newly_completed:
                await award_credits_for_learning(
                    user_id=user_id,
                    amount=points_per_day,
                    description=f"Завершение дня {day} челленджа урока {lesson_id}",
                    category='challenge',
                    details={
                        'lesson_id': lesson_id,
                        'challenge_id': challenge_id,
                        'day': day,
                        'points_per_day': points_per_day
                    }
                )
            
            # Начисляем бонусные кредиты при завершении всего челленджа (только один раз)
            if is_completed and not was_already_completed:
                await award_credits_for_learning(
                    user_id=user_id,
                    amount=bonus_points,
                    description=f"Завершение челленджа урока {lesson_id}",
                    category='challenge',
                    details={
                        'lesson_id': lesson_id,
                        'challenge_id': challenge_id,
                        'total_days': total_days,
                        'completed_days': completed_count
                    }
                )

            await db.challenge_progress.update_one(
                {"_id": existing_progress["_id"]},
                {"$set": update_data}
            )
            
            # ЗАПИСЫВАЕМ В time_activity с типом "challenge" для унифицированной аналитики
            existing_activity = await db.time_activity.find_one({
                "user_id": user_id,
                "lesson_id": lesson_id,
                "activity_type": "challenge"
            })
            
            if existing_activity:
                # Обновляем существующую запись
                await db.time_activity.update_one(
                    {"_id": existing_activity["_id"]},
                    {"$set": {"last_activity_at": now}}
                )
            else:
                # Создаем новую запись в time_activity
                activity_data = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "lesson_id": lesson_id,
                    "activity_type": "challenge",
                    "total_minutes": 0,
                    "total_points": 0,
                    "created_at": now,
                    "last_activity_at": now
                }
                await db.time_activity.insert_one(activity_data)
        else:
            # Подсчитываем, сколько попыток уже было
            total_attempts = await db.challenge_progress.count_documents({
                "user_id": user_id,
                "lesson_id": lesson_id,
                "challenge_id": challenge_id
            })

            completed_days = [day] if mark_completed else []
            completed_count = len(completed_days)
            is_completed = completed_count >= total_days

            points_earned = completed_count * points_per_day
            if is_completed:
                points_earned += bonus_points

            progress_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "lesson_id": lesson_id,
                "challenge_id": challenge_id,
                "current_day": max(1, day if not mark_completed else min(total_days, day + 1)),
                "completed_days": completed_days,
                "daily_notes": [{
                    "day": day,
                    "note": note_text,
                    "updated_at": now,
                    "completed_at": now
                }] if note_text else [],
                "is_completed": is_completed,
                "points_earned": points_earned,
                "total_points": points_earned,
                "attempt_number": total_attempts + 1,
                "started_at": now,
                "last_updated": now
            }

            if is_completed:
                progress_data["completed_at"] = now

            await db.challenge_progress.insert_one(progress_data)
            
            # ЗАПИСЫВАЕМ В time_activity с типом "challenge" для унифицированной аналитики
            existing_activity = await db.time_activity.find_one({
                "user_id": user_id,
                "lesson_id": lesson_id,
                "activity_type": "challenge"
            })
            
            if not existing_activity:
                # Создаем новую запись в time_activity
                activity_data = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "lesson_id": lesson_id,
                    "activity_type": "challenge",
                    "total_minutes": 0,
                    "total_points": 0,
                    "created_at": now,
                    "last_activity_at": now
                }
                await db.time_activity.insert_one(activity_data)
            
            # Начисляем кредиты за завершение дня (если день был завершен)
            if mark_completed:
                await award_credits_for_learning(
                    user_id=user_id,
                    amount=points_per_day,
                    description=f"Завершение дня {day} челленджа урока {lesson_id}",
                    category='challenge',
                    details={
                        'lesson_id': lesson_id,
                        'challenge_id': challenge_id,
                        'day': day,
                        'points_per_day': points_per_day
                    }
                )
            
            # Начисляем бонусные кредиты при завершении всего челленджа
            if is_completed:
                await award_credits_for_learning(
                    user_id=user_id,
                    amount=bonus_points,
                    description=f"Завершение челленджа урока {lesson_id}",
                    category='challenge',
                    details={
                        'lesson_id': lesson_id,
                        'challenge_id': challenge_id,
                        'total_days': total_days,
                        'completed_days': completed_count
                    }
                )

        # Обновляем прогресс урока
        await update_lesson_progress(user_id, lesson_id)

        return {"message": "Прогресс челленджа сохранен"}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error saving challenge progress: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error saving challenge progress: {str(e)}")

@app.get("/api/student/challenge-progress/{lesson_id}/{challenge_id}")
async def get_challenge_progress(lesson_id: str, challenge_id: str, current_user: dict = Depends(get_current_user)):
    """Получить прогресс челленджа"""
    try:
        user_id = current_user.get('user_id', current_user.get('id'))

        progress = await db.challenge_progress.find_one({
            "user_id": user_id,
            "lesson_id": lesson_id,
            "challenge_id": challenge_id
        })

        if progress:
            progress_dict = dict(progress)
            progress_dict.pop('_id', None)
            return progress_dict
        else:
            # Возвращаем пустой прогресс
            return {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "lesson_id": lesson_id,
                "challenge_id": challenge_id,
                "current_day": 1,
                "completed_days": [],
                "daily_notes": [],
                "is_completed": False,
                "points_earned": 0,
                "total_points": 0
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Error getting challenge progress: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting challenge progress: {str(e)}")

@app.get("/api/student/challenge-history/{lesson_id}/{challenge_id}")
async def get_challenge_history(lesson_id: str, challenge_id: str, current_user: dict = Depends(get_current_user)):
    """Получить историю всех попыток челленджа"""
    try:
        user_id = current_user.get('user_id', current_user.get('id'))

        attempts = await db.challenge_progress.find({
            "user_id": user_id,
            "lesson_id": lesson_id,
            "challenge_id": challenge_id
        }).sort("started_at", -1).to_list(length=None)

        attempts_list = []
        for attempt in attempts:
            attempt_dict = dict(attempt)
            attempt_dict.pop('_id', None)
            attempts_list.append(attempt_dict)

        return {"attempts": attempts_list}
        
    except Exception as e:
        import traceback
        logger.error(f"Error getting challenge history: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting challenge history: {str(e)}")

@app.get("/api/student/quiz-attempts/{lesson_id}")
async def get_quiz_attempts(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Получить все попытки прохождения теста урока"""
    try:
        user_id = current_user.get('user_id', current_user.get('id'))

        attempts = await db.quiz_attempts.find({
            "user_id": user_id,
            "lesson_id": lesson_id
        }).sort("attempted_at", -1).to_list(length=None)

        attempts_list = []
        for attempt in attempts:
            attempt_dict = dict(attempt)
            attempt_dict.pop('_id', None)
            attempts_list.append(attempt_dict)

        return {"attempts": attempts_list}
        
    except Exception as e:
        import traceback
        logger.error(f"Error getting quiz attempts: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting quiz attempts: {str(e)}")

@app.post("/api/student/quiz-attempt")
async def save_quiz_attempt(request_data: dict, current_user: dict = Depends(get_current_user)):
    """Сохранить попытку прохождения теста"""
    try:
        user_id = current_user.get('user_id', current_user.get('id'))
        lesson_id = request_data["lesson_id"]
        passed = request_data.get("passed", False)
        
        # Получаем настройки начисления баллов из конфигурации
        points_config = await get_learning_points_config()
        quiz_points = points_config.get('quiz_points_per_attempt', 10)
        
        # Начисляем баллы за прохождение теста
        points_earned = quiz_points if passed else 0
        if request_data.get("points_earned") is not None:
            # Если баллы переданы явно, используем их
            points_earned = request_data.get("points_earned", 0)

        attempt_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "lesson_id": lesson_id,
            "quiz_id": request_data.get("quiz_id", lesson_id),
            "score": request_data["score"],
            "passed": passed,
            "answers": request_data["answers"],
            "attempted_at": datetime.utcnow(),
            "points_earned": points_earned
        }

        result = await db.quiz_attempts.insert_one(attempt_data)

        # Начисляем кредиты за прохождение теста (только если тест пройден)
        if passed and points_earned > 0:
            await award_credits_for_learning(
                user_id=user_id,
                amount=points_earned,
                description=f"Прохождение теста урока {lesson_id}",
                category='quiz',
                details={
                    'lesson_id': lesson_id,
                    'quiz_id': request_data.get("quiz_id", lesson_id),
                    'score': request_data["score"],
                    'passed': passed,
                    'points_earned': points_earned
                }
            )

        # ЗАПИСЫВАЕМ В time_activity с типом "quiz" для унифицированной аналитики
        now = datetime.utcnow()
        existing_activity = await db.time_activity.find_one({
            "user_id": user_id,
            "lesson_id": lesson_id,
            "activity_type": "quiz"
        })
        
        if existing_activity:
            # Обновляем существующую запись
            await db.time_activity.update_one(
                {"_id": existing_activity["_id"]},
                {
                    "$inc": {"total_points": points_earned},
                    "$set": {"last_activity_at": now}
                }
            )
        else:
            # Создаем новую запись в time_activity
            activity_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "lesson_id": lesson_id,
                "activity_type": "quiz",
                "total_minutes": 0,
                "total_points": points_earned,
                "created_at": now,
                "last_activity_at": now
            }
            await db.time_activity.insert_one(activity_data)

        # Обновляем прогресс урока
        await update_lesson_progress(user_id, lesson_id)
        
        return {
            "message": "Результат теста сохранен",
            "attempt_id": attempt_data["id"],
            "points_earned": points_earned
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Error saving quiz attempt: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error saving quiz attempt: {str(e)}")

@app.get("/api/student/time-activity/{lesson_id}")
async def get_time_activity(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Получить статистику времени активности для урока"""
    try:
        user_id = current_user.get('user_id', current_user.get('id'))

        time_doc = await db.time_activity.find_one({
            "user_id": user_id,
            "lesson_id": lesson_id
        })

        if time_doc:
            time_dict = dict(time_doc)
            time_dict.pop('_id', None)
            return time_dict
        else:
            return {
                "user_id": user_id,
            "lesson_id": lesson_id,
                "total_minutes": 0,
                "total_points": 0
            }

    except Exception as e:
        import traceback
        logger.error(f"Error getting time activity: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting time activity: {str(e)}")

@app.post("/api/student/time-activity")
async def save_time_activity(request_data: dict, current_user: dict = Depends(get_current_user)):
    """Сохранить время активности"""
    try:
        user_id = current_user.get('user_id', current_user.get('id'))
        lesson_id = request_data.get("lesson_id")
        activity_type = request_data.get("activity_type", "lesson_view")  # Тип активности: lesson_view, theory_view, theory
        new_minutes = request_data.get("minutes_spent", 0)
        
        # Получаем настройки начисления баллов из конфигурации
        points_config = await get_learning_points_config()
        time_points_per_minute = points_config.get('time_points_per_minute', 1)
        new_points = new_minutes * time_points_per_minute
        
        now = datetime.utcnow()

        # Ищем существующий документ с таким же типом активности
        existing_doc = await db.time_activity.find_one({
            "user_id": user_id,
            "lesson_id": lesson_id,
            "activity_type": activity_type
        })

        if existing_doc:
            # Обновляем существующий
            old_total_points = existing_doc.get("total_points", 0)
            total_minutes = existing_doc.get("total_minutes", 0) + new_minutes
            total_points = existing_doc.get("total_points", 0) + new_points
            
            # Вычисляем разницу в баллах для начисления
            points_difference = total_points - old_total_points

            await db.time_activity.update_one(
                {"_id": existing_doc["_id"]},
                {"$set": {
                    "total_minutes": total_minutes,
                    "total_points": total_points,
                    "last_activity_at": now
                }}
            )
            
            # Начисляем баллы через award_credits_for_learning (только разницу)
            if points_difference > 0:
                activity_description = {
                    "lesson_view": "Время на уроке",
                    "theory_view": "Просмотр теории",
                    "theory": "Изучение теории"
                }.get(activity_type, "Время активности")
                
                await award_credits_for_learning(
                    user_id=user_id,
                    amount=points_difference,
                    description=f"{activity_description} (урок {lesson_id})",
                    category='learning',
                    details={
                        'lesson_id': lesson_id,
                        'activity_type': activity_type,
                        'minutes_spent': new_minutes,
                        'points_per_minute': time_points_per_minute,
                        'total_points': points_difference
                    }
                )
        else:
            # Создаем новый
            time_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
            "lesson_id": lesson_id,
                "total_minutes": new_minutes,
                "total_points": new_points,
                "activity_type": activity_type,  # Тип активности
                "created_at": now,
                "last_activity_at": now
            }
            result = await db.time_activity.insert_one(time_data)
            
            # Начисляем баллы через award_credits_for_learning
            if new_points > 0:
                activity_description = {
                    "lesson_view": "Время на уроке",
                    "theory_view": "Просмотр теории",
                    "theory": "Изучение теории"
                }.get(activity_type, "Время активности")
                
                await award_credits_for_learning(
                    user_id=user_id,
                    amount=new_points,
                    description=f"{activity_description} (урок {lesson_id})",
                    category='learning',
                    details={
                        'lesson_id': lesson_id,
                        'activity_type': activity_type,
                        'minutes_spent': new_minutes,
                        'points_per_minute': time_points_per_minute,
                        'total_points': new_points
                    }
                )

        return {"message": "Время активности сохранено"}
        
    except Exception as e:
        import traceback
        logger.error(f"Error saving time activity: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error saving time activity: {str(e)}")

@app.get("/api/student/lesson-files/{lesson_id}")
async def get_lesson_files(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Получить файлы урока"""
    try:
        files = await db.files.find({"lesson_id": lesson_id}).to_list(length=None)

        files_list = []
        for file in files:
            file_dict = dict(file)
            file_dict.pop('_id', None)
            files_list.append(file_dict)

        return {
            "files": files_list,
            "total": len(files_list)
        }

    except Exception as e:
        import traceback
        logger.error(f"Error getting lesson files: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting lesson files: {str(e)}")

async def award_points_for_file_view(user_id: str, file_id: str, lesson_id: str):
    """Начислить баллы за просмотр файла и записать в time_activity"""
    try:
        # Получаем информацию о файле
        file_info = await db.files.find_one({"id": file_id})
        if not file_info:
            logger.warning(f"File not found for file_id: {file_id}")
            return

        # Получаем настройки начисления баллов из конфигурации
        points_config = await get_learning_points_config()
        
        # Определяем количество баллов в зависимости от типа файла
        points = 0
        file_type = file_info.get("file_type", "")
        mime_type = file_info.get("mime_type", "")
        
        # Проверяем тип файла - если это PDF по mime_type, тоже начисляем баллы
        is_pdf = False
        if mime_type in ["application/pdf", "pdf"] or file_type == "pdf" or file_type == "document":
            is_pdf = True
            points = points_config.get('pdf_points_per_view', 5)  # Баллы за просмотр PDF
            logger.info(f"PDF file detected: file_id={file_id}, mime_type={mime_type}, file_type={file_type}, points={points}")
        elif file_type == "media":
            points = points_config.get('media_points_per_view', 10)  # Баллы за просмотр медиафайла
            logger.info(f"Media file detected: file_id={file_id}, mime_type={mime_type}, file_type={file_type}, points={points}")
        else:
            # Если тип не определен, но это PDF по расширению или mime_type, начисляем баллы
            if mime_type and "pdf" in mime_type.lower():
                is_pdf = True
                points = points_config.get('pdf_points_per_view', 5)
                logger.info(f"PDF detected by mime_type: file_id={file_id}, mime_type={mime_type}, points={points}")
            else:
                logger.warning(f"Unknown file type: file_id={file_id}, file_type={file_type}, mime_type={mime_type}, points=0")

        now = datetime.utcnow()
        
        # ЗАПИСЫВАЕМ В time_activity с типом "file_view" для унифицированной аналитики
        existing_doc = await db.time_activity.find_one({
            "user_id": user_id,
            "lesson_id": lesson_id,
            "activity_type": "file_view",
            "file_id": file_id
        })

        if not existing_doc:
            # Создаем новую запись в time_activity
            activity_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "lesson_id": lesson_id,
                "activity_type": "file_view",
                "file_id": file_id,
                "file_type": "pdf" if is_pdf else mime_type or file_type,  # Сохраняем тип файла для фильтрации PDF
                "total_minutes": 0,
                "total_points": points,
                "created_at": now,
                "last_activity_at": now
            }
            await db.time_activity.insert_one(activity_data)
            
            # Начисляем баллы через award_credits_for_learning (только один раз за файл)
            if points > 0:
                file_name = file_info.get("original_name", file_id)
                logger.info(f"Awarding {points} points for file view: user_id={user_id}, file_id={file_id}, file_name={file_name}")
                await award_credits_for_learning(
                    user_id=user_id,
                    amount=points,
                    description=f"Просмотр файла: {file_name} (урок {lesson_id})",
                    category='learning',
                    details={
                        'lesson_id': lesson_id,
                        'file_id': file_id,
                        'file_name': file_name,
                        'file_type': file_type,
                        'mime_type': mime_type,
                        'points': points
                    }
                )
            else:
                logger.warning(f"No points to award for file view: file_id={file_id}, file_type={file_type}, mime_type={mime_type}")
        else:
            # Обновляем время последней активности (баллы начисляются только один раз за файл)
            logger.info(f"File already viewed, updating last_activity_at: file_id={file_id}, user_id={user_id}")
            await db.time_activity.update_one(
                {"_id": existing_doc["_id"]},
                {"$set": {"last_activity_at": now}}
            )
        
    except Exception as e:
        logger.error(f"Error awarding points for file view: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

@app.post("/api/student/file-analytics")
async def save_file_analytics(request_data: dict, current_user: dict = Depends(get_current_user)):
    """Сохранить аналитику просмотров/скачиваний файлов"""
    try:
        user_id = current_user.get('user_id', current_user.get('id'))

        analytics_data = {
            "id": str(uuid.uuid4()),
            "file_id": request_data["file_id"],
            "user_id": user_id,
            "lesson_id": request_data["lesson_id"],
            "action": request_data["action"],  # 'view' или 'download'
            "created_at": datetime.utcnow()
        }

        result = await db.file_analytics.insert_one(analytics_data)

        # Начисляем баллы за просмотр файла (если это просмотр, а не скачивание)
        if request_data["action"] == "view":
            await award_points_for_file_view(user_id, request_data["file_id"], request_data["lesson_id"])

        return {"message": "Аналитика сохранена"}
        
    except Exception as e:
        import traceback
        logger.error(f"Error saving file analytics: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error saving file analytics: {str(e)}")

@app.post("/api/student/video-watch-time")
async def save_video_watch_time(request_data: dict, current_user: dict = Depends(get_current_user)):
    """Сохранить время просмотра видео"""
    try:
        user_id = current_user.get('user_id', current_user.get('id'))
        lesson_id = request_data.get("lesson_id")
        file_id = request_data.get("file_id")

        # Получаем существующий документ
        existing_doc = await db.video_watch_time.find_one({
            "file_id": file_id,
            "user_id": user_id
        })

        new_minutes = request_data.get("minutes_watched", 0)
        
        # Получаем настройки начисления баллов из конфигурации
        points_config = await get_learning_points_config()
        video_points_per_minute = points_config.get('video_points_per_minute', 1)
        new_points = new_minutes * video_points_per_minute
        
        logger.info(f"Video watch time: user_id={user_id}, file_id={file_id}, lesson_id={lesson_id}, new_minutes={new_minutes}, new_points={new_points}, points_per_minute={video_points_per_minute}")
        
        now = datetime.utcnow()

        if existing_doc:
            # Обновляем существующий
            old_total_points = existing_doc.get("total_points", 0)
            total_minutes = existing_doc.get("total_minutes", 0) + new_minutes
            total_points = existing_doc.get("total_points", 0) + new_points
            
            # Вычисляем разницу в баллах для начисления
            points_difference = total_points - old_total_points
            
            await db.video_watch_time.update_one(
                {"_id": existing_doc["_id"]},
                {"$set": {
                    "total_minutes": total_minutes,
                    "total_points": total_points,
                    "last_updated": now
                }}
            )
            
            # Начисляем баллы через award_credits_for_learning (только разницу)
            if points_difference > 0:
                logger.info(f"Awarding {points_difference} points for video watch (existing doc): user_id={user_id}, file_id={file_id}, old_points={old_total_points}, new_points={total_points}")
                await award_credits_for_learning(
                    user_id=user_id,
                    amount=points_difference,
                    description=f"Просмотр видео (файл {file_id}, урок {lesson_id})",
                    category='learning',
                    details={
                        'lesson_id': lesson_id,
                        'file_id': file_id,
                        'minutes_watched': new_minutes,
                        'points_per_minute': video_points_per_minute,
                        'total_points': points_difference
                    }
                )
            else:
                logger.warning(f"No points difference for video watch: user_id={user_id}, file_id={file_id}, old_points={old_total_points}, new_points={total_points}, points_difference={points_difference}")
        else:
            # Создаем новый
            video_data = {
                "id": str(uuid.uuid4()),
                "file_id": file_id,
                "user_id": user_id,
            "lesson_id": lesson_id,
                "total_minutes": new_minutes,
                "total_points": new_points,
                "created_at": now,
                "last_updated": now
            }
            result = await db.video_watch_time.insert_one(video_data)
            
            # Начисляем баллы через award_credits_for_learning
            if new_points > 0:
                logger.info(f"Awarding {new_points} points for video watch (new doc): user_id={user_id}, file_id={file_id}, minutes={new_minutes}")
                await award_credits_for_learning(
                    user_id=user_id,
                    amount=new_points,
                    description=f"Просмотр видео (файл {file_id}, урок {lesson_id})",
                    category='learning',
                    details={
                        'lesson_id': lesson_id,
                        'file_id': file_id,
                        'minutes_watched': new_minutes,
                        'points_per_minute': video_points_per_minute,
                        'total_points': new_points
                    }
                )
            else:
                logger.warning(f"No points to award for video watch: user_id={user_id}, file_id={file_id}, new_minutes={new_minutes}, new_points={new_points}")

        # ЗАПИСЫВАЕМ В time_activity с типом "video_watch" для унифицированной аналитики
        if lesson_id and new_minutes > 0:
            # Ищем существующую запись в time_activity для этого урока и файла
            existing_activity = await db.time_activity.find_one({
                "user_id": user_id,
                "lesson_id": lesson_id,
                "activity_type": "video_watch",
                "file_id": file_id
            })
            
            if existing_activity:
                # Обновляем существующую запись
                await db.time_activity.update_one(
                    {"_id": existing_activity["_id"]},
                    {
                        "$inc": {
                            "total_minutes": new_minutes,
                            "total_points": new_points
                        },
                        "$set": {
                            "last_activity_at": now
                        }
                    }
                )
            else:
                # Создаем новую запись в time_activity
                activity_data = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "lesson_id": lesson_id,
                    "file_id": file_id,
                    "activity_type": "video_watch",
                    "total_minutes": new_minutes,
                    "total_points": new_points,
                    "created_at": now,
                    "last_activity_at": now
                }
                await db.time_activity.insert_one(activity_data)

        return {"message": "Время просмотра видео сохранено"}
        
    except Exception as e:
        import traceback
        logger.error(f"Error saving video watch time: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error saving video watch time: {str(e)}")

@app.get("/api/student/my-files-stats/{lesson_id}")
async def get_student_files_stats(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Получить статистику файлов студента для урока"""
    try:
        user_id = current_user.get('user_id', current_user.get('id'))

        # Получаем все файлы урока
        files = await db.files.find({"lesson_id": lesson_id}).to_list(length=None)

        # Получаем аналитику для каждого файла
        files_stats = []
        total_views = 0
        total_downloads = 0
        total_video_points = 0
        total_video_minutes = 0

        for file in files:
            # Получаем аналитику для этого файла
            views_count = await db.file_analytics.count_documents({
                "file_id": file["id"],
                "user_id": user_id,
                "action": "view"
            })

            downloads_count = await db.file_analytics.count_documents({
                "file_id": file["id"],
                "user_id": user_id,
                "action": "download"
            })

            # Получаем время просмотра видео
            video_watch = await db.video_watch_time.find_one({
                "file_id": file["id"],
                "user_id": user_id
            })

            file_stat = {
                "file_id": file["id"],
                "file_name": file["original_name"],
                "views": views_count,
                "downloads": downloads_count,
                "video_stats": {
                    "minutes_watched": video_watch.get("total_minutes", 0),
                    "points_earned": video_watch.get("total_points", 0)
                } if video_watch else None
            }

            files_stats.append(file_stat)
            total_views += views_count
            total_downloads += downloads_count

            if video_watch:
                total_video_minutes += video_watch.get("total_minutes", 0)
                total_video_points += video_watch.get("total_points", 0)

        return {
            "files": files_stats,
            "summary": {
                "total_files": len(files),
                "total_views": total_views,
                "total_downloads": total_downloads,
                "total_video_minutes": total_video_minutes,
                "total_video_points": total_video_points
            }
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Error getting student files stats: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting student files stats: {str(e)}")

@app.get("/api/admin/files")
async def get_admin_files_stats(lesson_id: str = Query(None), section: str = Query(None), current_user: dict = Depends(get_current_user)):
    """Получить статистику файлов для админа"""
    try:
        # Получаем полные данные пользователя из базы данных
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        query = {}
        if lesson_id:
            query["lesson_id"] = lesson_id
        if section:
            query["section"] = section

        files = await db.files.find(query).sort("uploaded_at", -1).to_list(length=None)

        files_list = []
        for file in files:
            file_dict = dict(file)
            file_dict.pop('_id', None)

            # Получаем статистику просмотров и скачиваний
            views_count = await db.file_analytics.count_documents({
                "file_id": file["id"],
                "action": "view"
            })

            downloads_count = await db.file_analytics.count_documents({
                "file_id": file["id"],
                "action": "download"
            })

            file_dict["views"] = views_count
            file_dict["downloads"] = downloads_count
            files_list.append(file_dict)

        return {
            "files": files_list,
            "total": len(files_list)
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error getting admin files stats: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting admin files stats: {str(e)}")

@app.post("/api/admin/review-response/{response_id}")
async def review_exercise_response(response_id: str, request_data: dict, current_user: dict = Depends(get_current_user)):
    """Проверить и прокомментировать ответ на упражнение, назначить баллы"""
    try:
        # Получаем полные данные пользователя из базы данных
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        # Находим ответ на упражнение
        response_doc = await db.exercise_responses.find_one({"id": response_id})
        if not response_doc:
            raise HTTPException(status_code=404, detail="Ответ не найден")

        student_user_id = response_doc.get("user_id")
        lesson_id = response_doc.get("lesson_id")
        exercise_id = response_doc.get("exercise_id")
        points_earned = request_data.get("points_earned", 0)
        admin_comment = request_data.get("admin_comment", "")
        review_start_time = request_data.get("review_start_time")  # Время начала проверки (ISO string)
        
        # Вычисляем время проверки
        review_time_minutes = 0
        if review_start_time:
            try:
                start_time = datetime.fromisoformat(review_start_time.replace('Z', '+00:00'))
                if start_time.tzinfo:
                    start_time = start_time.replace(tzinfo=None) - (start_time.utcoffset() or timedelta(0))
                review_time_minutes = max(0, (datetime.utcnow() - start_time).total_seconds() / 60)
            except:
                pass

        # Обновляем ответ
        update_data = {
            "reviewed": True,
            "admin_comment": admin_comment,
            "reviewed_at": datetime.utcnow(),
            "reviewed_by": user_id,
            "points_earned": points_earned,
            "review_time_minutes": round(review_time_minutes, 2)
        }
        
        await db.exercise_responses.update_one(
            {"id": response_id},
            {"$set": update_data}
        )

        # Сохраняем баллы в единую базу данных time_activity
        # Проверяем, были ли уже начислены баллы за это упражнение
        old_points_earned = response_doc.get("points_earned", 0)
        points_difference = points_earned - old_points_earned
        
        if points_earned > 0:
            # Ищем существующую запись или создаем новую
            time_activity = await db.time_activity.find_one({
                "user_id": student_user_id,
                "lesson_id": lesson_id,
                "activity_type": "exercise_review"
            })
            
            if time_activity:
                # Обновляем существующую запись
                await db.time_activity.update_one(
                    {"_id": time_activity["_id"]},
                    {
                        "$inc": {
                            "total_points": points_difference,  # Начисляем только разницу
                            "review_count": 1 if old_points_earned == 0 else 0,  # Увеличиваем счетчик только при первой проверке
                            "review_time_minutes": review_time_minutes
                        },
                        "$set": {
                            "last_updated": datetime.utcnow()
                        }
                    }
                )
            else:
                # Создаем новую запись
                await db.time_activity.insert_one({
                    "id": str(uuid.uuid4()),
                    "user_id": student_user_id,
                    "lesson_id": lesson_id,
                    "activity_type": "exercise_review",
                    "total_points": points_earned,
                    "total_minutes": 0,
                    "review_count": 1,
                    "review_time_minutes": review_time_minutes,
                    "created_at": datetime.utcnow(),
                    "last_updated": datetime.utcnow()
                })
        
        # Начисляем баллы через award_credits_for_learning (только разницу, если баллы изменились)
        if points_difference > 0:
            # Получаем информацию об упражнении для описания
            lesson = await db.lessons_v2.find_one({"id": lesson_id})
            lesson_title = lesson.get("title", "Урок") if lesson else "Урок"
            
            await award_credits_for_learning(
                user_id=student_user_id,
                amount=points_difference,
                description=f"Проверка упражнения урока '{lesson_title}' (упражнение {exercise_id})",
                category='exercise_review',
                details={
                    'lesson_id': lesson_id,
                    'exercise_id': exercise_id,
                    'response_id': response_id,
                    'points_earned': points_earned,
                    'old_points': old_points_earned,
                    'points_difference': points_difference,
                    'reviewed_by': user_id,
                    'admin_email': user.get('email', ''),
                    'admin_review': True,
                    'review_time_minutes': review_time_minutes,
                    'admin_comment': admin_comment
                }
            )

        return {
            "message": "Ответ проверен и прокомментирован",
            "points_earned": points_earned,
            "review_time_minutes": round(review_time_minutes, 2)
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error reviewing response: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error reviewing response: {str(e)}")


def _ensure_admin_user(current_user: dict):
    """Получить объект пользователя и проверить права администратора"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = current_user.get("user_id") or current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_id


def _to_iso(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value


@app.get("/api/admin/analytics/lesson/{lesson_id}")
async def get_lesson_analytics(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Получить подробную аналитику по уроку"""
    try:
        user_id = _ensure_admin_user(current_user)
        user = await db.users.find_one({"id": user_id})
        if not user or (not user.get("is_super_admin", False) and not user.get("is_admin", False)):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        lesson = await db.lessons_v2.find_one({"id": lesson_id})
        if not lesson:
            raise HTTPException(status_code=404, detail="Урок не найден")

        exercise_responses = await db.exercise_responses.find({"lesson_id": lesson_id}).to_list(length=None)
        lesson_progress_list = await db.lesson_progress.find({"lesson_id": lesson_id}).to_list(length=None)
        quiz_attempts = await db.quiz_attempts.find({"lesson_id": lesson_id}).to_list(length=None)
        challenge_progress_list = await db.challenge_progress.find({"lesson_id": lesson_id}).to_list(length=None)
        
        # Аналитика по времени
        time_activity_list = await db.time_activity.find({"lesson_id": lesson_id}).to_list(length=None) if "time_activity" in await db.list_collection_names() else []
        
        # Время на чтение урока (теория)
        theory_time_minutes = sum(
            t.get("total_minutes", 0) for t in time_activity_list 
            if t.get("activity_type") in ["lesson_view", "theory_read", None]  # None для старых записей
        )
        
        # Время на выполнение заданий (упражнения)
        exercise_time_minutes = sum(
            t.get("total_minutes", 0) for t in time_activity_list 
            if t.get("activity_type") == "exercise"
        )
        
        # Время проверки упражнений администратором
        review_time_minutes = sum(
            t.get("review_time_minutes", 0) for t in time_activity_list 
            if t.get("activity_type") == "exercise_review"
        )
        
        # Среднее время на урок
        avg_lesson_time = 0
        if lesson_progress_list:
            avg_lesson_time = sum(p.get("time_spent_minutes", 0) for p in lesson_progress_list) / len(lesson_progress_list)

        total_students = len({progress.get("user_id") for progress in lesson_progress_list})
        completed_students = len([p for p in lesson_progress_list if p.get("is_completed")])
        avg_completion = (
            sum(p.get("completion_percentage", 0) for p in lesson_progress_list) / len(lesson_progress_list)
            if lesson_progress_list else 0
        )

        total_exercise_responses = len(exercise_responses)
        reviewed_responses = len([resp for resp in exercise_responses if resp.get("reviewed")])

        total_quiz_attempts = len(quiz_attempts)
        passed_quizzes = len([attempt for attempt in quiz_attempts if attempt.get("passed")])
        avg_quiz_score = (
            sum(attempt.get("score", 0) for attempt in quiz_attempts) / total_quiz_attempts
            if total_quiz_attempts else 0
        )
        total_quiz_points = sum(attempt.get("points_earned", 0) for attempt in quiz_attempts)
        avg_quiz_points = total_quiz_points / total_quiz_attempts if total_quiz_attempts else 0

        unique_challenge_users = len({cp.get("user_id") for cp in challenge_progress_list})
        total_challenge_attempts = len(challenge_progress_list)
        completed_challenges = len([cp for cp in challenge_progress_list if cp.get("is_completed")])
        total_challenge_notes = sum(len(cp.get("daily_notes", [])) for cp in challenge_progress_list)
        total_points_earned = sum(cp.get("points_earned", 0) for cp in challenge_progress_list)
        avg_points_per_attempt = total_points_earned / total_challenge_attempts if total_challenge_attempts else 0

        # Топ студентов по тестам
        user_quiz_points = {}
        for attempt in quiz_attempts:
            uid = attempt.get("user_id")
            if not uid:
                continue
            if uid not in user_quiz_points:
                user_quiz_points[uid] = {"total_points": 0, "attempts": 0, "passed": 0, "best_score": 0}
            
            # Начисляем баллы: 10 за прохождение теста, если не указано явно
            points = attempt.get("points_earned") or 0
            if points == 0 and attempt.get("passed", False):
                points = 10
            
            user_quiz_points[uid]["total_points"] += points
            user_quiz_points[uid]["attempts"] += 1
            if attempt.get("passed"):
                user_quiz_points[uid]["passed"] += 1
            user_quiz_points[uid]["best_score"] = max(
                user_quiz_points[uid]["best_score"], attempt.get("score", 0)
            )

        # Топ студентов по челленджам
        user_challenge_points = {}
        for cp in challenge_progress_list:
            uid = cp.get("user_id")
            if not uid:
                continue
            if uid not in user_challenge_points:
                user_challenge_points[uid] = {"total_points": 0, "attempts": 0, "completed": 0}
            user_challenge_points[uid]["total_points"] += cp.get("points_earned", 0)
            user_challenge_points[uid]["attempts"] += 1
            if cp.get("is_completed"):
                user_challenge_points[uid]["completed"] += 1

        # Получаем имена пользователей для лидербордов
        all_user_ids = set(user_quiz_points.keys()) | set(user_challenge_points.keys())
        users = await db.users.find({"id": {"$in": list(all_user_ids)}}).to_list(length=None) if all_user_ids else []
        users_map = {u.get("id"): u.get("full_name") or u.get("name") or u.get("email") or u.get("id") for u in users}

        progress_timeline = {}
        for progress in lesson_progress_list:
            started_at = progress.get("started_at")
            if isinstance(started_at, datetime):
                key = started_at.strftime("%Y-%m-%d")
                if key not in progress_timeline:
                    progress_timeline[key] = {"started": 0, "completed": 0}
                progress_timeline[key]["started"] += 1
                if progress.get("is_completed"):
                    progress_timeline[key]["completed"] += 1

        return {
            "lesson_id": lesson_id,
            "lesson_title": lesson.get("title"),
            "statistics": {
                "total_students": total_students,
                "completed_students": completed_students,
                "avg_completion_percentage": round(avg_completion, 2),
                "total_exercise_responses": total_exercise_responses,
                "reviewed_responses": reviewed_responses,
                "pending_review": total_exercise_responses - reviewed_responses,
                "total_quiz_attempts": total_quiz_attempts,
                "passed_quizzes": passed_quizzes,
                "avg_quiz_score": round(avg_quiz_score, 2),
                "total_quiz_points": total_quiz_points,
                "avg_quiz_points": round(avg_quiz_points, 2),
                "unique_challenge_users": unique_challenge_users,
                "total_challenge_attempts": total_challenge_attempts,
                "completed_challenges": completed_challenges,
                "total_challenge_notes": total_challenge_notes,
                "total_points_earned": total_points_earned,
                "avg_points_per_attempt": round(avg_points_per_attempt, 2),
                "time_analytics": {
                    "theory_time_minutes": round(theory_time_minutes, 1),
                    "theory_time_hours": round(theory_time_minutes / 60, 1),
                    "exercise_time_minutes": round(exercise_time_minutes, 1),
                    "exercise_time_hours": round(exercise_time_minutes / 60, 1),
                    "review_time_minutes": round(review_time_minutes, 1),
                    "review_time_hours": round(review_time_minutes / 60, 1),
                    "avg_lesson_time_minutes": round(avg_lesson_time, 1),
                    "avg_lesson_time_hours": round(avg_lesson_time / 60, 1)
                }
            },
            "quiz_leaderboard": sorted(
                ({"user_id": uid, "user_name": users_map.get(uid, uid), **data} for uid, data in user_quiz_points.items()),
                key=lambda item: item["total_points"],
                reverse=True
            )[:10],
            "challenge_leaderboard": sorted(
                ({"user_id": uid, "user_name": users_map.get(uid, uid), **data} for uid, data in user_challenge_points.items()),
                key=lambda item: item["total_points"],
                reverse=True
            )[:10],
            "progress_timeline": sorted(progress_timeline.items()),
            "students_data": [
                {
                    "user_id": progress.get("user_id"),
                    "completion_percentage": progress.get("completion_percentage", 0),
                    "exercises_completed": progress.get("exercises_completed", 0),
                    "quiz_passed": progress.get("quiz_passed", False),
                    "challenge_completed": progress.get("challenge_completed", False),
                    "last_activity_at": _to_iso(progress.get("last_activity_at"))
                }
                for progress in lesson_progress_list
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error getting lesson analytics: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting lesson analytics: {str(e)}")


@app.get("/api/admin/analytics/student-responses/{lesson_id}")
async def get_student_responses_for_lesson(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Получить ответы студентов на упражнения урока"""
    try:
        user_id = _ensure_admin_user(current_user)
        user = await db.users.find_one({"id": user_id})
        if not user or (not user.get("is_super_admin", False) and not user.get("is_admin", False)):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        lesson = await db.lessons_v2.find_one({"id": lesson_id})
        if not lesson:
            raise HTTPException(status_code=404, detail="Урок не найден")

        responses = await db.exercise_responses.find({"lesson_id": lesson_id}).sort("submitted_at", -1).to_list(length=None)
        user_ids = [resp.get("user_id") for resp in responses if resp.get("user_id")]
        users = await db.users.find({"id": {"$in": user_ids}}).to_list(length=None) if user_ids else []
        users_map = {u.get("id"): u.get("full_name") or u.get("email") or u.get("id") for u in users}

        exercises_map = {ex.get("id"): ex for ex in lesson.get("exercises", [])}

        formatted = []
        for resp in responses:
            exercise = exercises_map.get(resp.get("exercise_id"), {})
            formatted.append({
                "id": resp.get("id"),
                "user_id": resp.get("user_id"),
                "user_name": users_map.get(resp.get("user_id"), resp.get("user_id")),
                "exercise_id": resp.get("exercise_id"),
                "exercise_title": exercise.get("title") or exercise.get("name") or "Неизвестное упражнение",
                "response_text": resp.get("response_text"),
                "submitted_at": _to_iso(resp.get("submitted_at")),
                "reviewed": resp.get("reviewed", False),
                "admin_comment": resp.get("admin_comment"),
                "reviewed_at": _to_iso(resp.get("reviewed_at")),
                "reviewed_by": resp.get("reviewed_by"),
                "points_earned": resp.get("points_earned", 0),
                "review_time_minutes": resp.get("review_time_minutes", 0)
            })

        return {
            "lesson_id": lesson_id,
            "lesson_title": lesson.get("title"),
            "total_responses": len(formatted),
            "responses": formatted
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error getting student responses: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting student responses: {str(e)}")


@app.get("/api/admin/analytics/challenge-notes/{lesson_id}")
async def get_challenge_notes_for_lesson(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Получить заметки студентов по челленджу урока"""
    try:
        user_id = _ensure_admin_user(current_user)
        admin_user = await db.users.find_one({"id": user_id})
        if not admin_user or (not admin_user.get("is_super_admin", False) and not admin_user.get("is_admin", False)):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        lesson = await db.lessons_v2.find_one({"id": lesson_id})
        if not lesson:
            raise HTTPException(status_code=404, detail="Урок не найден")

        challenge_progresses = await db.challenge_progress.find({"lesson_id": lesson_id}).sort("started_at", -1).to_list(length=None)
        user_ids = [progress.get("user_id") for progress in challenge_progresses if progress.get("user_id")]
        users = await db.users.find({"id": {"$in": user_ids}}).to_list(length=None) if user_ids else []
        users_map = {u.get("id"): u.get("full_name") or u.get("email") or u.get("id") for u in users}

        notes = []
        for progress in challenge_progresses:
            for note_item in progress.get("daily_notes", []):
                note_text = note_item.get("note")
                if not note_text:
                    continue
                notes.append({
                    "user_id": progress.get("user_id"),
                    "user_name": users_map.get(progress.get("user_id"), progress.get("user_id")),
                    "day": note_item.get("day"),
                    "note": note_text,
                    "updated_at": _to_iso(note_item.get("updated_at") or note_item.get("completed_at")),
                    "completed_at": _to_iso(note_item.get("completed_at") or note_item.get("updated_at")),
                    "is_challenge_completed": progress.get("is_completed", False)
                })

        return {
            "lesson_id": lesson_id,
            "lesson_title": lesson.get("title"),
            "total_notes": len(notes),
            "notes": notes
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error getting challenge notes: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting challenge notes: {str(e)}")


@app.get("/api/admin/lesson-files-analytics/{lesson_id}")
async def get_lesson_files_analytics(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Получить аналитику по файлам урока"""
    try:
        user_id = _ensure_admin_user(current_user)
        user = await db.users.find_one({"id": user_id})
        if not user or (not user.get("is_super_admin", False) and not user.get("is_admin", False)):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        files = await db.files.find({"lesson_id": lesson_id}).to_list(length=None)
        result = []

        for file_doc in files:
            file_id = file_doc.get("id")
            analytics = await db.file_analytics.find({"file_id": file_id}).to_list(length=None)
            total_views = sum(1 for entry in analytics if entry.get("action") == "view")
            total_downloads = sum(1 for entry in analytics if entry.get("action") == "download")
            unique_users = len({entry.get("user_id") for entry in analytics})

            video_stats = None
            if file_doc.get("mime_type", "").startswith("video/"):
                video_records = await db.video_watch_time.find({"file_id": file_id}).to_list(length=None)
                video_stats = {
                    "total_watch_minutes": sum(rec.get("total_minutes", 0) for rec in video_records),
                    "total_points_earned": sum(rec.get("total_points", 0) for rec in video_records),
                    "unique_watchers": len(video_records)
                }

            result.append({
                "file_id": file_id,
                "file_name": file_doc.get("original_name"),
                "file_type": file_doc.get("file_type"),
                "section": file_doc.get("section"),
                "mime_type": file_doc.get("mime_type"),
                "total_views": total_views,
                "total_downloads": total_downloads,
                "unique_users": unique_users,
                "video_stats": video_stats
            })

        return {
            "lesson_id": lesson_id,
            "total_files": len(result),
            "files": result
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error getting lesson files analytics: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting lesson files analytics: {str(e)}")

@app.get("/api/admin/analytics/overview")
async def get_admin_analytics_overview(current_user: dict = Depends(get_current_user)):
    """Получить общую аналитику для админа"""
    try:
        # Получаем полные данные пользователя из базы данных
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        # Получаем общую статистику
        total_students = await db.users.count_documents({})  # Пока все пользователи
        total_lessons = await db.lessons_v2.count_documents({"is_active": True})

        # Подсчитываем баллы
        points_stats = {
            "total": 0,
            "challenges": 0,
            "quizzes": 0,
            "time": 0,
            "videos": 0,
            "files": 0
        }

        # Баллы за челленджи
        if "challenge_progress" in await db.list_collection_names():
            challenge_cursor = db.challenge_progress.find({})
            challenge_docs = await challenge_cursor.to_list(length=None)
            points_stats["challenges"] = sum(doc.get("points_earned", 0) for doc in challenge_docs)

        # Баллы за тесты
        if "quiz_attempts" in await db.list_collection_names():
            quiz_cursor = db.quiz_attempts.find({})
            quiz_docs = await quiz_cursor.to_list(length=None)
            points_stats["quizzes"] = sum(doc.get("points_earned", 0) for doc in quiz_docs)

        # Баллы за время
        if "time_activity" in await db.list_collection_names():
            time_cursor = db.time_activity.find({})
            time_docs = await time_cursor.to_list(length=None)
            points_stats["time"] = sum(doc.get("total_points", 0) for doc in time_docs)

        # Баллы за видео
        if "video_watch_time" in await db.list_collection_names():
            video_cursor = db.video_watch_time.find({})
            video_docs = await video_cursor.to_list(length=None)
            points_stats["videos"] = sum(doc.get("total_points", 0) for doc in video_docs)

        # Баллы за просмотр файлов
        if "time_activity" in await db.list_collection_names():
            file_view_cursor = db.time_activity.find({"activity_type": "file_view"})
            file_view_docs = await file_view_cursor.to_list(length=None)
            points_stats["files"] = sum(doc.get("total_points", 0) for doc in file_view_docs)

        points_stats["total"] = points_stats["challenges"] + points_stats["quizzes"] + points_stats["time"] + points_stats["videos"] + points_stats["files"]

        # Непроверенные ответы на упражнения
        pending_reviews = 0
        pending_reviews_details = []

        if "exercise_responses" in await db.list_collection_names():
            pending_cursor = db.exercise_responses.find({"reviewed": False})
            pending_docs = await pending_cursor.to_list(length=None)
            pending_reviews = len(pending_docs)

            # Детали непроверенных ответов (первые 10)
            for doc in pending_docs[:10]:
                lesson = await db.lessons_v2.find_one({"id": doc["lesson_id"]})
                user_info = await db.users.find_one({"id": doc["user_id"]}) or {"name": "Неизвестный пользователь"}

                pending_reviews_details.append({
                    "response_id": doc["id"],
                    "user_name": user_info.get("name", "Неизвестный"),
                    "lesson_title": lesson.get("title", "Неизвестный урок") if lesson else "Неизвестный урок",
                    "exercise_title": "Упражнение",  # Пока без названия
                    "response_text": doc.get("response_text", "")[:200] + "..." if len(doc.get("response_text", "")) > 200 else doc.get("response_text", ""),
                    "submitted_at": doc.get("submitted_at")
                })

        # Активность за последние 7 дней
        recent_activity_7days = 0
        active_students = 0
        top_lessons = []

        if "lesson_progress" in await db.list_collection_names():
            seven_days_ago = datetime.utcnow() - timedelta(days=7)

            recent_progress_cursor = db.lesson_progress.find({
                "last_activity_at": {"$gte": seven_days_ago}
            })
            recent_progress = await recent_progress_cursor.to_list(length=None)
            recent_activity_7days = len(recent_progress)
            active_students = len({item.get("user_id") for item in recent_progress if item.get("user_id")})

            pipeline = [
                {
                    "$group": {
                        "_id": "$lesson_id",
                        "students_count": {"$sum": 1},
                        "avg_completion": {"$avg": "$completion_percentage"}
                    }
                },
                {"$sort": {"students_count": -1}},
                {"$limit": 5}
            ]
            top_lessons_raw = await db.lesson_progress.aggregate(pipeline).to_list(length=5)

            lesson_ids = [doc["_id"] for doc in top_lessons_raw if doc.get("_id")]
            lessons_info = []
            if lesson_ids:
                lessons_info = await db.lessons_v2.find({"id": {"$in": lesson_ids}}).to_list(length=None)
            lessons_map = {lesson.get("id"): lesson.get("title", "Неизвестный урок") for lesson in lessons_info}

            top_lessons = [
                {
                    "lesson_id": item.get("_id"),
                    "lesson_title": lessons_map.get(item.get("_id"), "Неизвестный урок"),
                    "students_count": item.get("students_count", 0),
                    "avg_completion": round(item.get("avg_completion", 0), 2)
                }
                for item in top_lessons_raw
            ]
        
        return {
            "total_students": total_students,
            "total_lessons": total_lessons,
            "points": points_stats,
            "pending_reviews": pending_reviews,
            "pending_reviews_details": pending_reviews_details,
            "recent_activity_7days": recent_activity_7days,
            "active_students": active_students,
            "top_lessons": top_lessons
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error getting admin analytics overview: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting admin analytics overview: {str(e)}")

# Вспомогательные функции для обновления прогресса
async def update_lesson_progress(user_id: str, lesson_id: str):
    """Обновить прогресс урока на основе выполненных заданий"""
    try:
        # Получаем урок
        lesson = await db.lessons_v2.find_one({"id": lesson_id})
        if not lesson:
            return

        # Получаем существующий прогресс
        existing_progress = await db.lesson_progress.find_one({"user_id": user_id, "lesson_id": lesson_id})

        # Подсчитываем прогресс
        theory_read = True  # Пока считаем, что теория прочитана

        # Подсчитываем выполненные упражнения
        exercises_count = len(lesson.get("exercises", []))
        completed_exercises = 0

        if "exercise_responses" in await db.list_collection_names():
            completed_exercises = await db.exercise_responses.count_documents({
                "user_id": user_id,
                "lesson_id": lesson_id
            })

        # Проверяем челлендж
        challenge_started = False
        challenge_completed = False

        if lesson.get("challenge") and "challenge_progress" in await db.list_collection_names():
            challenge_progress_doc = await db.challenge_progress.find_one({
                "user_id": user_id,
            "lesson_id": lesson_id,
                "challenge_id": lesson["challenge"]["id"]
            })

            if challenge_progress_doc:
                challenge_started = True
                challenge_completed = challenge_progress_doc.get("is_completed", False)

        # Проверяем тест
        quiz_passed = False

        if lesson.get("quiz") and "quiz_attempts" in await db.list_collection_names():
            quiz_attempt = await db.quiz_attempts.find_one({
                "user_id": user_id,
            "lesson_id": lesson_id,
                "passed": True
            }, sort=[("attempted_at", -1)])

            quiz_passed = quiz_attempt is not None

        # Рассчитываем процент завершения
        total_tasks = 1 + exercises_count + (1 if lesson.get("challenge") else 0) + (1 if lesson.get("quiz") else 0)  # теория + упражнения + челлендж + тест
        completed_tasks = (1 if theory_read else 0) + completed_exercises + (1 if challenge_completed else 0) + (1 if quiz_passed else 0)
        completion_percentage = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

        is_completed = completion_percentage >= 100

        progress_data = {
            "user_id": user_id,
            "lesson_id": lesson_id,
            "is_completed": is_completed,
            "completion_percentage": completion_percentage,
            "theory_read": theory_read,
            "exercises_completed": completed_exercises,
            "challenge_started": challenge_started,
            "challenge_completed": challenge_completed,
            "quiz_passed": quiz_passed,
            "last_activity_at": datetime.utcnow()
        }

        # Проверяем, был ли урок только что завершен (для начисления бонусных кредитов)
        was_already_completed = existing_progress.get("is_completed", False) if existing_progress else False
        lesson_just_completed = is_completed and not was_already_completed

        if existing_progress:
            # Обновляем существующий прогресс
            await db.lesson_progress.update_one(
                {"_id": existing_progress["_id"]},
                {"$set": progress_data}
            )

            # Если урок завершен и не был завершен ранее
            if is_completed and not existing_progress.get("is_completed"):
                progress_data["completed_at"] = datetime.utcnow()
                await db.lesson_progress.update_one(
                    {"_id": existing_progress["_id"]},
                    {"$set": {"completed_at": datetime.utcnow()}}
                )
        else:
            # Создаем новый прогресс
            progress_data["id"] = str(uuid.uuid4())
            progress_data["started_at"] = datetime.utcnow()

            if is_completed:
                progress_data["completed_at"] = datetime.utcnow()

            result = await db.lesson_progress.insert_one(progress_data)
        
        # Начисляем бонусные кредиты при завершении урока (только один раз)
        if lesson_just_completed:
            await award_credits_for_learning(
                user_id=user_id,
                amount=50,  # 50 бонусных баллов за завершение урока
                description=f"Завершение урока {lesson_id}",
                category='lesson',
                details={
                    'lesson_id': lesson_id,
                    'completion_percentage': completion_percentage,
                    'theory_read': theory_read,
                    'exercises_completed': completed_exercises,
                    'quiz_passed': quiz_passed,
                    'challenge_completed': challenge_completed
                }
            )

    except Exception as e:
        import traceback
        logger.error(f"Error updating lesson progress: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")

# ==================== FILE OPERATIONS ====================

@app.get("/api/download-file/{file_id}")
async def download_file(file_id: str, current_user: dict = Depends(get_current_user)):
    """Скачать файл по ID"""
    try:
        # Проверяем пользователя
        user_id = current_user.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Получаем информацию о файле
        file_info = await db.files.find_one({"id": file_id})
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")

        # Проверяем существование файла на диске
        # Сначала ищем в папке урока, затем в корне папки learning_v2
        lesson_id = file_info.get('lesson_id')
        if lesson_id:
            file_path = Path(f"uploads/learning_v2/{lesson_id}/{file_info['stored_name']}")
            if not file_path.exists():
                # Если не найден в папке урока, ищем в корне
                file_path = Path(f"uploads/learning_v2/{file_info['stored_name']}")
                if not file_path.exists():
                    raise HTTPException(status_code=404, detail="File not found on disk")
        else:
            file_path = Path(f"uploads/learning_v2/{file_info['stored_name']}")
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found on disk")

        # Определяем правильный MIME type
        mime_type = file_info.get('mime_type', 'application/octet-stream')
        if not mime_type or mime_type == 'application/octet-stream':
            # Если MIME type не определен, пытаемся определить по расширению
            mime_type = mimetypes.guess_type(file_info['original_name'])[0] or 'application/octet-stream'

        # Возвращаем файл для скачивания/просмотра
        return FileResponse(
            path=file_path,
            media_type=mime_type,
            filename=file_info['original_name']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@app.delete("/api/admin/files/{file_id}")
async def delete_file_admin(file_id: str, current_user: dict = Depends(get_current_user)):
    """Удалить файл (только для админов)"""
    try:
        # Получаем полные данные пользователя из базы данных
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        # Получаем информацию о файле
        file_info = await db.files.find_one({"id": file_id})
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")

        # Удаляем файл с диска
        file_path = Path(f"uploads/learning_v2/{file_info['stored_name']}")
        if file_path.exists():
            file_path.unlink()

        # Удаляем запись из базы данных
        await db.files.delete_one({"id": file_id})

        # Удаляем файл из массива файлов урока
        await db.lessons_v2.update_one(
            {"id": file_info["lesson_id"]},
            {"$pull": {"files": {"id": file_id}}}
        )

        return {"message": "Файл успешно удален"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

# ==================== LEARNING POINTS CONFIGURATION ====================

@app.get("/api/admin/learning-points-config")
async def get_learning_points_config_endpoint(current_user: dict = Depends(get_current_user)):
    """Получить конфигурацию начисления баллов за обучение"""
    try:
        user_id = current_user.get('user_id') or current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({'id': user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        config = await get_learning_points_config()
        return {"config": config}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting learning points config: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting learning points config: {str(e)}")

@app.put("/api/admin/learning-points-config")
async def update_learning_points_config(
    config_update: LearningPointsConfigUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Обновить конфигурацию начисления баллов за обучение"""
    try:
        user_id = current_user.get('user_id') or current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({'id': user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        # Получаем текущую активную конфигурацию
        existing_config = await db.learning_points_config.find_one({'is_active': True})
        
        # Подготавливаем данные для обновления
        update_data = config_update.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.utcnow()
        update_data['updated_by'] = user.get('email', user_id)
        
        if existing_config:
            # Обновляем существующую конфигурацию
            await db.learning_points_config.update_one(
                {'_id': existing_config['_id']},
                {'$set': update_data}
            )
            config_id = existing_config.get('id')
        else:
            # Создаем новую конфигурацию
            new_config = LearningPointsConfig(**update_data)
            result = await db.learning_points_config.insert_one(new_config.dict())
            config_id = new_config.id

        # Получаем обновленную конфигурацию
        updated_config = await get_learning_points_config()
        
        logger.info(f"Learning points config updated by {user.get('email', user_id)}")

        return {
            "message": "Конфигурация начисления баллов успешно обновлена",
            "config": updated_config
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating learning points config: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error updating learning points config: {str(e)}")

# ==================== NUMEROLOGY CREDITS CONFIGURATION ====================

async def get_numerology_credits_config() -> dict:
    """Получить конфигурацию стоимости услуг нумерологии"""
    try:
        config = await db.numerology_credits_config.find_one({'is_active': True})
        if config:
            config.pop('_id', None)
            return config
    except Exception as e:
        logger.error(f"Error getting numerology credits config: {e}")
    
    # Возвращаем значения по умолчанию
    default_config = NumerologyCreditsConfig()
    return default_config.dict()

@app.get("/api/admin/numerology-credits-config")
async def get_numerology_credits_config_endpoint(current_user: dict = Depends(get_current_user)):
    """Получить конфигурацию стоимости услуг нумерологии"""
    try:
        user_id = current_user.get('user_id') or current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({'id': user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        config = await get_numerology_credits_config()
        return {"config": config}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting numerology credits config: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting numerology credits config: {str(e)}")

@app.put("/api/admin/numerology-credits-config")
async def update_numerology_credits_config(
    config_update: NumerologyCreditsConfigUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Обновить конфигурацию стоимости услуг нумерологии"""
    try:
        user_id = current_user.get('user_id') or current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({'id': user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        # Получаем текущую активную конфигурацию
        existing_config = await db.numerology_credits_config.find_one({'is_active': True})
        
        # Подготавливаем данные для обновления
        update_data = config_update.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.utcnow()
        update_data['updated_by'] = user.get('email', user_id)
        
        if existing_config:
            # Обновляем существующую конфигурацию
            await db.numerology_credits_config.update_one(
                {'_id': existing_config['_id']},
                {'$set': update_data}
            )
            config_id = existing_config.get('id')
        else:
            # Создаем новую конфигурацию
            new_config = NumerologyCreditsConfig(**update_data)
            result = await db.numerology_credits_config.insert_one(new_config.dict())
            config_id = new_config.id

        # Получаем обновленную конфигурацию
        updated_config = await get_numerology_credits_config()
        
        logger.info(f"Numerology credits config updated by {user.get('email', user_id)}")

        return {
            "message": "Конфигурация стоимости услуг нумерологии успешно обновлена",
            "config": updated_config
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating numerology credits config: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error updating numerology credits config: {str(e)}")

# ==================== CREDITS DEDUCTION CONFIGURATION (ЕДИНАЯ СИСТЕМА) ====================

@app.get("/api/admin/credits-deduction-config")
async def get_credits_deduction_config_endpoint(current_user: dict = Depends(get_current_user)):
    """Получить единую конфигурацию всех списаний баллов"""
    try:
        user_id = current_user.get('user_id') or current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({'id': user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        config = await get_credits_deduction_config()
        return {"config": config}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting credits deduction config: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting credits deduction config: {str(e)}")

@app.put("/api/admin/credits-deduction-config")
async def update_credits_deduction_config(
    config_update: CreditsDeductionConfigUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Обновить единую конфигурацию всех списаний баллов"""
    try:
        user_id = current_user.get('user_id') or current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({'id': user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        # Получаем текущую активную конфигурацию
        existing_config = await db.credits_deduction_config.find_one({'is_active': True})
        
        # Подготавливаем данные для обновления
        update_data = config_update.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.utcnow()
        update_data['updated_by'] = user.get('email', user_id)
        
        if existing_config:
            # Обновляем существующую конфигурацию
            await db.credits_deduction_config.update_one(
                {'_id': existing_config['_id']},
                {'$set': update_data}
            )
            config_id = existing_config.get('id')
        else:
            # Создаем новую конфигурацию
            new_config = CreditsDeductionConfig(**update_data)
            result = await db.credits_deduction_config.insert_one(new_config.dict())
            config_id = new_config.id

        # Получаем обновленную конфигурацию
        updated_config = await get_credits_deduction_config()
        
        logger.info(f"Credits deduction config updated by {user.get('email', user_id)}")
        
        return {
            "message": "Конфигурация списания баллов успешно обновлена",
            "config": updated_config
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating credits deduction config: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error updating credits deduction config: {str(e)}")

# ==================== PLANETARY ENERGY MODIFIERS CONFIGURATION ====================

async def get_planetary_energy_modifiers_config() -> dict:
    """Получить конфигурацию модификаторов энергии планет"""
    try:
        config = await db.planetary_energy_modifiers_config.find_one({'is_active': True})
        if config:
            config.pop('_id', None)
            return config
    except Exception as e:
        logger.error(f"Error getting planetary energy modifiers config: {e}")
    
    # Возвращаем значения по умолчанию
    default_config = PlanetaryEnergyModifiersConfig()
    return default_config.dict()

@app.get("/api/admin/planetary-energy-modifiers-config")
async def get_planetary_energy_modifiers_config_endpoint(current_user: dict = Depends(get_current_user)):
    """Получить конфигурацию модификаторов энергии планет"""
    try:
        user_id = current_user.get('user_id') or current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({'id': user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        config = await get_planetary_energy_modifiers_config()
        return {"config": config}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting planetary energy modifiers config: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting planetary energy modifiers config: {str(e)}")

@app.put("/api/admin/planetary-energy-modifiers-config")
async def update_planetary_energy_modifiers_config(
    config_update: PlanetaryEnergyModifiersConfigUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Обновить конфигурацию модификаторов энергии планет"""
    try:
        user_id = current_user.get('user_id') or current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({'id': user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        # Получаем текущую активную конфигурацию
        existing_config = await db.planetary_energy_modifiers_config.find_one({'is_active': True})
        
        # Подготавливаем данные для обновления
        update_data = config_update.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.utcnow()
        update_data['updated_by'] = user.get('email', user_id)
        
        if existing_config:
            # Обновляем существующую конфигурацию
            await db.planetary_energy_modifiers_config.update_one(
                {'_id': existing_config['_id']},
                {'$set': update_data}
            )
            config_id = existing_config.get('id')
        else:
            # Создаем новую конфигурацию
            new_config = PlanetaryEnergyModifiersConfig(**update_data)
            result = await db.planetary_energy_modifiers_config.insert_one(new_config.dict())
            config_id = new_config.id

        # Получаем обновленную конфигурацию
        updated_config = await get_planetary_energy_modifiers_config()
        
        logger.info(f"Planetary energy modifiers config updated by {user.get('email', user_id)}")
        
        return {
            "message": "Конфигурация модификаторов энергии планет успешно обновлена",
            "config": updated_config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating planetary energy modifiers config: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error updating planetary energy modifiers config: {str(e)}")

# ==================== MONTHLY ROUTE CONFIG ENDPOINTS ====================

async def get_monthly_route_config() -> dict:
    """Получить конфигурацию месячного маршрута"""
    try:
        config = await db.monthly_route_config.find_one({'is_active': True})
        if config:
            config.pop('_id', None)
            return config
    except Exception as e:
        logger.error(f"Error getting monthly route config: {e}")
    
    # Возвращаем значения по умолчанию
    from models import MonthlyRouteConfig
    default_config = MonthlyRouteConfig()
    return default_config.dict()

@app.get("/api/admin/monthly-route-config")
async def get_monthly_route_config_endpoint(current_user: dict = Depends(get_current_user)):
    """Получить конфигурацию месячного маршрута"""
    try:
        user_id = current_user.get('user_id') or current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({'id': user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        config = await get_monthly_route_config()
        return {"config": config}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting monthly route config: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting monthly route config: {str(e)}")

@app.put("/api/admin/monthly-route-config")
async def update_monthly_route_config(
    config_update: MonthlyRouteConfigUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Обновить конфигурацию месячного маршрута"""
    try:
        user_id = current_user.get('user_id') or current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({'id': user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка прав администратора
        if not user.get('is_super_admin', False) and not user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        # Получаем текущую активную конфигурацию
        existing_config = await db.monthly_route_config.find_one({'is_active': True})
        
        # Подготавливаем данные для обновления
        update_data = config_update.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.utcnow()
        update_data['updated_by'] = user.get('email', user_id)
        
        if existing_config:
            # Обновляем существующую конфигурацию
            await db.monthly_route_config.update_one(
                {'_id': existing_config['_id']},
                {'$set': update_data}
            )
            config_id = existing_config.get('id')
        else:
            # Создаем новую конфигурацию
            from models import MonthlyRouteConfig
            new_config = MonthlyRouteConfig(**update_data)
            result = await db.monthly_route_config.insert_one(new_config.dict())
            config_id = new_config.id

        # Получаем обновленную конфигурацию
        updated_config = await get_monthly_route_config()
        
        logger.info(f"Monthly route config updated by {user.get('email', user_id)}")
        
        return {
            "message": "Конфигурация месячного маршрута успешно обновлена",
            "config": updated_config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating monthly route config: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error updating monthly route config: {str(e)}")

# ==================== REPORTS ENDPOINTS ====================

@app.post("/api/reports/html/numerology")
async def generate_numerology_html_report(
    html_request: HTMLReportRequest,
    current_user: dict = Depends(get_current_user)
):
    """Генерация HTML отчёта по нумерологии"""
    try:
        user_id = current_user.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({'id': user_id})
        if not user:
            raise HTTPException(status_code=404, detail='Пользователь не найден')

        # Получаем стоимость из конфигурации
        config = await get_credits_deduction_config()
        cost = config.get('html_report_numerology', 3)

        # Списываем баллы (включая premium пользователей)
        await deduct_credits(
            user_id,
            cost,
            'Генерация HTML отчёта по нумерологии',
            'report',
            {'report_type': 'html', 'report_category': 'numerology'}
        )

        # Подготавливаем данные пользователя
        user_data = {
            'full_name': user.get('full_name', ''),
            'email': user.get('email', ''),
            'birth_date': user.get('birth_date', ''),
            'city': user.get('city', ''),
            'phone_number': user.get('phone_number', ''),
            'car_number': user.get('car_number', ''),
            'street': user.get('street', ''),
            'house_number': user.get('house_number', ''),
            'apartment_number': user.get('apartment_number', ''),
            'postal_code': user.get('postal_code', '')
        }

        # Вычисляем данные
        calculations = calculate_personal_numbers(user.get('birth_date', ''))
        
        pythagorean_data = None
        try:
            d, m, y = parse_birth_date(user.get('birth_date', ''))
            pythagorean_data = create_pythagorean_square(d, m, y)
        except Exception:
            pass

        # Выбранные расчёты
        selected_calculations = html_request.selected_calculations
        if not selected_calculations:
            selected_calculations = []
            if html_request.include_vedic:
                selected_calculations.append('vedic_times')
            if html_request.include_charts:
                selected_calculations.extend(['personal_numbers', 'pythagorean_square'])
            if html_request.include_compatibility:
                selected_calculations.append('compatibility')

        if not selected_calculations:
            selected_calculations = ['personal_numbers', 'pythagorean_square']

        # Ведические данные
        vedic_data = None
        vedic_times = None
        if 'vedic_times' in selected_calculations and user.get('city'):
            try:
                vedic_times = get_vedic_day_schedule(city=user.get('city'), date=datetime.utcnow())
            except Exception:
                pass

        # Планетарный маршрут
        planetary_route = None
        if 'planetary_route' in selected_calculations and user.get('city'):
            try:
                planetary_route = {
                    'date': datetime.utcnow().strftime('%Y-%m-%d'),
                    'city': user.get('city'),
                    'daily_route': []
                }
            except Exception:
                pass

        # Данные для графиков
        charts_data = None
        if any(calc in selected_calculations for calc in ['personal_numbers', 'pythagorean_square']):
            try:
                user_numbers = None
                if user.get('birth_date'):
                    try:
                        personal_numbers = calculate_personal_numbers(user.get('birth_date', ''))
                        user_numbers = {
                            'soul_number': personal_numbers.get('soul_number'),
                            'mind_number': personal_numbers.get('mind_number'),
                            'destiny_number': personal_numbers.get('destiny_number'),
                            'personal_day': personal_numbers.get('personal_day')
                        }
                    except:
                        pass
                user_city = user.get('city', 'Москва') or 'Москва'
                
                # Prepare enhanced calculation data
                pythagorean_square_data = pythagorean_data
                fractal_behavior = None
                problem_numbers = None
                name_numbers = None
                weekday_energy = None
                
                if user.get('birth_date'):
                    try:
                        d, m, y = parse_birth_date(user.get('birth_date', ''))
                        
                        # Calculate fractal behavior
                        day_reduced = reduce_to_single_digit(d)
                        month_reduced = reduce_to_single_digit(m)
                        year_reduced = reduce_to_single_digit(y)
                        year_sum = reduce_to_single_digit(d + m + y)
                        fractal_behavior = [day_reduced, month_reduced, year_reduced, year_sum]
                        
                        # Calculate problem numbers
                        soul_num = user_numbers.get('soul_number', 1) if user_numbers else 1
                        mind_num = user_numbers.get('mind_number', 1) if user_numbers else 1
                        destiny_num = user_numbers.get('destiny_number', 1) if user_numbers else 1
                        problem1 = reduce_to_single_digit(abs(soul_num - mind_num))
                        problem2 = reduce_to_single_digit(abs(soul_num - year_reduced))
                        problem3 = reduce_to_single_digit(abs(problem1 - problem2))
                        problem4 = reduce_to_single_digit(abs(mind_num - year_reduced))
                        problem_numbers = [problem1, problem2, problem3, problem4]
                        
                        # Get name numbers if available
                        if user.get('full_name'):
                            # Calculate name numbers (name and surname separately)
                            from numerology import calculate_name_numerology
                            try:
                                name_data = calculate_name_numerology(user.get('full_name', ''))
                                name_numbers = {
                                    'first_name_number': name_data.get('first_name_number'),
                                    'last_name_number': name_data.get('last_name_number'),
                                    'total_name_number': name_data.get('total_name_number'),
                                    'full_name_number': name_data.get('total_name_number')  # Alias
                                }
                            except:
                                # Fallback to simple calculation
                                try:
                                    from numerology import calculate_full_name_number
                                    name_num = calculate_full_name_number(user.get('full_name', ''))
                                    name_numbers = {'name_number': name_num, 'full_name_number': name_num}
                                except:
                                    pass
                        
                        # Calculate weekday energy (personal energy by day of week)
                        try:
                            from numerology import calculate_planetary_strength
                            planetary_strength_data = calculate_planetary_strength(d, m, y)
                            strength_dict = planetary_strength_data.get('strength', {})
                            
                            # Map planet names to energy keys
                            planet_name_to_key = {
                                'Солнце': 'surya',
                                'Луна': 'chandra',
                                'Марс': 'mangal',
                                'Меркурий': 'budha',
                                'Юпитер': 'guru',
                                'Венера': 'shukra',
                                'Сатурн': 'shani'
                            }
                            
                            weekday_energy = {}
                            for planet_name, energy_value in strength_dict.items():
                                planet_key = planet_name_to_key.get(planet_name)
                                if planet_key:
                                    weekday_energy[planet_key] = float(energy_value)
                        except:
                            weekday_energy = None
                        
                        # Calculate Janma Ank
                        try:
                            from vedic_numerology import calculate_janma_ank
                            janma_ank_value = calculate_janma_ank(d, m, y)
                            total_before_reduction = d + m + y
                            if total_before_reduction == 22:
                                janma_ank_value = 22
                        except:
                            janma_ank_value = None
                    except:
                        pass
                
                charts_data = {
                    'planetary_energy': generate_weekly_planetary_energy(
                        user.get('birth_date', ''), user_numbers, user_city,
                        pythagorean_square=pythagorean_square_data,
                        fractal_behavior=fractal_behavior,
                        problem_numbers=problem_numbers,
                        name_numbers=name_numbers,
                        weekday_energy=weekday_energy,
                        janma_ank=janma_ank_value if 'janma_ank_value' in locals() else None,
                        modifiers_config=await get_planetary_energy_modifiers_config()
                    )
                }
            except Exception:
                pass

        # Загружаем сохранённые расчёты
        saved_calculations_query = {'user_id': user_id}
        saved_calculations_list = await db.numerology_calculations.find(saved_calculations_query).sort('created_at', -1).to_list(length=100)
        
        # Группируем по типу и берём последний для каждого типа
        saved_calculations = {}
        for calc in saved_calculations_list:
            calc_type = calc.get('calculation_type')
            if calc_type not in saved_calculations:
                saved_calculations[calc_type] = calc.get('results', {})
        
        # Объединяем все данные
        all_data = {
            'personal_numbers': calculations,
            'pythagorean_square': pythagorean_data,
            'vedic_times': vedic_times,
            'planetary_route': saved_calculations.get('planetary_route_daily') or planetary_route,
            'charts': charts_data,
            'compatibility': saved_calculations.get('compatibility'),
            'group_compatibility': saved_calculations.get('group_compatibility'),
            'name_numerology': saved_calculations.get('name_numerology'),
            'address_numerology': saved_calculations.get('address_numerology'),
            'car_numerology': saved_calculations.get('car_numerology')
        }

        # Генерируем HTML отчёт
        html_str = create_numerology_report_html(
            user_data=user_data,
            all_data=all_data,
            vedic_data=vedic_data,
            charts_data=charts_data,
            theme=html_request.theme,
            selected_calculations=selected_calculations
        )

        if not html_str or len(html_str) < 100:
            raise HTTPException(
                status_code=500,
                detail='Ошибка генерации HTML: пустой результат'
            )

        return Response(content=html_str, media_type='text/html; charset=utf-8')

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"HTML generation error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f'Ошибка генерации HTML отчёта: {str(e)}'
        )

@app.post("/api/reports/pdf/numerology")
async def generate_numerology_pdf_report(
    pdf_request: PDFReportRequest,
    current_user: dict = Depends(get_current_user)
):
    """Генерация PDF отчёта по нумерологии"""
    try:
        user_id = current_user.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({'id': user_id})
        if not user:
            raise HTTPException(status_code=404, detail='Пользователь не найден')

        # Получаем стоимость из конфигурации
        config = await get_credits_deduction_config()
        cost = config.get('pdf_report_numerology', 5)

        # Списываем баллы (включая premium пользователей)
        await deduct_credits(
            user_id,
            cost,
            'Генерация PDF отчёта по нумерологии',
            'report',
            {'report_type': 'pdf', 'report_category': 'numerology'}
        )

        # Подготавливаем данные пользователя
        user_data = {
            'full_name': user.get('full_name', ''),
            'email': user.get('email', ''),
            'birth_date': user.get('birth_date', ''),
            'city': user.get('city', '')
        }

        # Вычисляем данные
        calculations = calculate_personal_numbers(user.get('birth_date', ''))

        pythagorean_data = None
        try:
            d, m, y = parse_birth_date(user.get('birth_date', ''))
            pythagorean_data = create_pythagorean_square(d, m, y)
        except Exception:
            pass

        # Ведические данные
        vedic_data = None
        if pdf_request.include_vedic:
            try:
                vedic_data = calculate_comprehensive_vedic_numerology(
                    user.get('birth_date', ''),
                    user.get('full_name', '')
                )
            except Exception:
                pass

        # Данные для графиков
        charts_data = None
        if pdf_request.include_charts:
            try:
                user_numbers = None
                if user.get('birth_date'):
                    try:
                        personal_numbers = calculate_personal_numbers(user.get('birth_date', ''))
                        user_numbers = {
                            'soul_number': personal_numbers.get('soul_number'),
                            'mind_number': personal_numbers.get('mind_number'),
                            'destiny_number': personal_numbers.get('destiny_number'),
                            'personal_day': personal_numbers.get('personal_day')
                        }
                    except:
                        pass
                # Prepare enhanced calculation data
                pythagorean_square_data = pythagorean_data
                fractal_behavior = None
                problem_numbers = None
                name_numbers = None
                weekday_energy = None
                
                if user.get('birth_date'):
                    try:
                        d, m, y = parse_birth_date(user.get('birth_date', ''))
                        
                        # Calculate fractal behavior
                        day_reduced = reduce_to_single_digit(d)
                        month_reduced = reduce_to_single_digit(m)
                        year_reduced = reduce_to_single_digit(y)
                        year_sum = reduce_to_single_digit(d + m + y)
                        fractal_behavior = [day_reduced, month_reduced, year_reduced, year_sum]
                        
                        # Calculate problem numbers
                        soul_num = user_numbers.get('soul_number', 1) if user_numbers else 1
                        mind_num = user_numbers.get('mind_number', 1) if user_numbers else 1
                        destiny_num = user_numbers.get('destiny_number', 1) if user_numbers else 1
                        problem1 = reduce_to_single_digit(abs(soul_num - mind_num))
                        problem2 = reduce_to_single_digit(abs(soul_num - year_reduced))
                        problem3 = reduce_to_single_digit(abs(problem1 - problem2))
                        problem4 = reduce_to_single_digit(abs(mind_num - year_reduced))
                        problem_numbers = [problem1, problem2, problem3, problem4]
                        
                        # Get name numbers if available
                        if user.get('full_name'):
                            # Calculate name numbers (name and surname separately)
                            from numerology import calculate_name_numerology
                            try:
                                name_data = calculate_name_numerology(user.get('full_name', ''))
                                name_numbers = {
                                    'first_name_number': name_data.get('first_name_number'),
                                    'last_name_number': name_data.get('last_name_number'),
                                    'total_name_number': name_data.get('total_name_number'),
                                    'full_name_number': name_data.get('total_name_number')  # Alias
                                }
                            except:
                                # Fallback to simple calculation
                                try:
                                    from numerology import calculate_full_name_number
                                    name_num = calculate_full_name_number(user.get('full_name', ''))
                                    name_numbers = {'name_number': name_num, 'full_name_number': name_num}
                                except:
                                    pass
                        
                        # Calculate weekday energy (personal energy by day of week)
                        try:
                            from numerology import calculate_planetary_strength
                            planetary_strength_data = calculate_planetary_strength(d, m, y)
                            strength_dict = planetary_strength_data.get('strength', {})
                            
                            # Map planet names to energy keys
                            planet_name_to_key = {
                                'Солнце': 'surya',
                                'Луна': 'chandra',
                                'Марс': 'mangal',
                                'Меркурий': 'budha',
                                'Юпитер': 'guru',
                                'Венера': 'shukra',
                                'Сатурн': 'shani'
                            }
                            
                            weekday_energy = {}
                            for planet_name, energy_value in strength_dict.items():
                                planet_key = planet_name_to_key.get(planet_name)
                                if planet_key:
                                    weekday_energy[planet_key] = float(energy_value)
                        except:
                            weekday_energy = None
                    except:
                        pass
                
                charts_data = {
                    'planetary_energy': generate_weekly_planetary_energy(
                        user.get('birth_date', ''), user_numbers, user.get('city', 'Москва') or 'Москва',
                        pythagorean_square=pythagorean_square_data,
                        fractal_behavior=fractal_behavior,
                        problem_numbers=problem_numbers,
                        name_numbers=name_numbers,
                        weekday_energy=weekday_energy,
                        modifiers_config=await get_planetary_energy_modifiers_config()
                    )
                }
            except Exception:
                pass

        # Загружаем сохранённые расчёты (как в HTML отчёте)
        saved_calculations_query = {'user_id': user_id}
        saved_calculations_list = await db.numerology_calculations.find(saved_calculations_query).sort('created_at', -1).to_list(length=100)
        
        # Группируем по типу и берём последний для каждого типа
        saved_calculations = {}
        for calc in saved_calculations_list:
            calc_type = calc.get('calculation_type')
            if calc_type not in saved_calculations:
                saved_calculations[calc_type] = calc.get('results', {})
        
        # Получаем планетарный маршрут
        planetary_route = None
        if user.get('city'):
            try:
                from vedic_time_calculations import get_daily_planetary_route
                planetary_route = get_daily_planetary_route(
                    city=user.get('city'),
                    date=datetime.utcnow(),
                    birth_date=user.get('birth_date', '')
                )
            except:
                pass
        
        # Объединяем все данные для PDF (как в HTML отчете)
        all_data = {
            'personal_numbers': calculations,
            'pythagorean_square': pythagorean_data,
            'vedic_times': None,
            'planetary_route': saved_calculations.get('planetary_route_daily') or planetary_route,
            'charts': charts_data,
            'compatibility': saved_calculations.get('compatibility'),
            'group_compatibility': saved_calculations.get('group_compatibility'),
            'name_numerology': saved_calculations.get('name_numerology'),
            'address_numerology': saved_calculations.get('address_numerology'),
            'car_numerology': saved_calculations.get('car_numerology')
        }
        
        # Генерируем PDF отчёт
        pdf_bytes = create_numerology_report_pdf(
            user_data=user_data,
            all_data=all_data,
            vedic_data=vedic_data,
            charts_data=charts_data,
            selected_calculations=None  # Включаем все доступные
        )

        if not pdf_bytes:
            raise HTTPException(
                status_code=500,
                detail='Ошибка генерации PDF: пустой результат'
            )

        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="numerology_report_{user_id}.pdf"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF generation error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f'Ошибка генерации PDF отчёта: {str(e)}'
        )

@app.post("/api/reports/html/compatibility")
async def generate_compatibility_html_report(
    compatibility_request: CompatibilityRequest,
    current_user: dict = Depends(get_current_user)
):
    """Генерация HTML отчёта по совместимости"""
    try:
        user_id = current_user.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({'id': user_id})
        if not user:
            raise HTTPException(status_code=404, detail='Пользователь не найден')

        # Получаем стоимость из конфигурации
        config = await get_credits_deduction_config()
        cost = config.get('html_report_compatibility', 3)

        # Списываем баллы (включая premium пользователей)
        await deduct_credits(
            user_id,
            cost,
            'Генерация HTML отчёта по совместимости',
            'report',
            {'report_type': 'html', 'report_category': 'compatibility'}
        )

        # Вычисляем совместимость
        compatibility_result = calculate_compatibility(
            compatibility_request.person1_birth_date,
            compatibility_request.person2_birth_date
        )

        # Подготавливаем данные пользователей
        user1_data = {
            'name': compatibility_request.person1_name or 'Человек 1',
            'birth_date': compatibility_request.person1_birth_date
        }
        user2_data = {
            'name': compatibility_request.person2_name or 'Человек 2',
            'birth_date': compatibility_request.person2_birth_date
        }

        # Генерируем HTML отчёт
        from html_generator import create_compatibility_html
        html_str = create_compatibility_html(user1_data, user2_data, compatibility_result)

        if not html_str or len(html_str) < 100:
            raise HTTPException(
                status_code=500,
                detail='Ошибка генерации HTML: пустой результат'
            )

        return Response(content=html_str, media_type='text/html; charset=utf-8')

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"HTML compatibility report generation error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f'Ошибка генерации HTML отчёта по совместимости: {str(e)}'
        )

@app.post("/api/reports/pdf/compatibility")
async def generate_compatibility_pdf_report(
    compatibility_request: CompatibilityRequest,
    current_user: dict = Depends(get_current_user)
):
    """Генерация PDF отчёта по совместимости"""
    try:
        user_id = current_user.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({'id': user_id})
        if not user:
            raise HTTPException(status_code=404, detail='Пользователь не найден')

        # Получаем стоимость из конфигурации
        config = await get_credits_deduction_config()
        cost = config.get('pdf_report_compatibility', 5)

        # Списываем баллы (включая premium пользователей)
        await deduct_credits(
            user_id,
            cost,
            'Генерация PDF отчёта по совместимости',
            'report',
            {'report_type': 'pdf', 'report_category': 'compatibility'}
        )

        # Вычисляем совместимость
        compatibility_result = calculate_compatibility(
            compatibility_request.person1_birth_date,
            compatibility_request.person2_birth_date
        )

        # Подготавливаем данные пользователей
        user1_data = {
            'name': compatibility_request.person1_name or 'Человек 1',
            'birth_date': compatibility_request.person1_birth_date
        }
        user2_data = {
            'name': compatibility_request.person2_name or 'Человек 2',
            'birth_date': compatibility_request.person2_birth_date
        }

        # Генерируем PDF отчёт
        pdf_bytes = create_compatibility_pdf(user1_data, user2_data, compatibility_result)

        if not pdf_bytes:
            raise HTTPException(
                status_code=500,
                detail='Ошибка генерации PDF: пустой результат'
            )

        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="compatibility_report_{user_id}.pdf"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF compatibility report generation error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f'Ошибка генерации PDF отчёта по совместимости: {str(e)}'
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)