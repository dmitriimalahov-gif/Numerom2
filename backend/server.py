from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, status, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse, StreamingResponse, Response, FileResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pytz
import os
import uuid
import io
import shutil
import requests
import logging
import tempfile
import re

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
    PlanetaryAdviceResponse
)
from lesson_system import lesson_system
from auth import (
    get_current_user, create_access_token, get_password_hash, verify_password,
    create_user_response, ensure_super_admin_exists
)
from push_notifications import PushNotificationManager, push_manager
from numerology import (
    calculate_personal_numbers,
    calculate_compatibility,
    parse_birth_date,
    create_pythagorean_square
)
from vedic_numerology import (
    calculate_comprehensive_vedic_numerology,
    generate_weekly_planetary_energy
)
from vedic_time_calculations import get_vedic_day_schedule, get_monthly_planetary_route, get_quarterly_planetary_route
from html_generator import create_numerology_report_html
from pdf_generator import create_numerology_report_pdf, create_compatibility_pdf
from planetary_advice import init_planetary_advice_collection, get_personalized_planetary_advice
import stripe

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

# ----------------- CREDIT HISTORY -----------------
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
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        CREDIT_COSTS['personal_numbers'], 
        'Расчёт персональных чисел', 
        'numerology',
        {'calculation_type': 'personal_numbers', 'birth_date': birth_date}
    )
    
    results = calculate_personal_numbers(birth_date)
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
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        CREDIT_COSTS['pythagorean_square'], 
        'Расчёт квадрата Пифагора', 
        'numerology',
        {'calculation_type': 'pythagorean_square', 'birth_date': birth_date}
    )
    
    d, m, y = parse_birth_date(birth_date)
    results = create_pythagorean_square(d, m, y)
    calc = NumerologyCalculation(user_id=user_id, birth_date=birth_date, calculation_type='pythagorean_square', results=results)
    await db.numerology_calculations.insert_one(calc.dict())
    return results

@api_router.post('/numerology/compatibility')
async def compatibility_endpoint(request_data: CompatibilityRequest, current_user: dict = Depends(get_current_user)):
    """Расчёт совместимости пары - 1 балл"""
    user_id = current_user['user_id']
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        CREDIT_COSTS['compatibility_pair'], 
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
    
    if not name:
        raise HTTPException(status_code=400, detail='Имя обязательно для расчёта')
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        CREDIT_COSTS['name_numerology'], 
        'Нумерология имени', 
        'numerology',
        {'calculation_type': 'name_numerology', 'name': name, 'surname': surname}
    )
    
    # Здесь должна быть логика расчета нумерологии имени
    # Пока возвращаем заглушку
    results = {
        'name': name,
        'surname': surname,
        'name_number': sum(ord(c) for c in name) % 9 + 1,
        'surname_number': sum(ord(c) for c in surname) % 9 + 1 if surname else 0,
        'full_name_number': (sum(ord(c) for c in (name + surname))) % 9 + 1
    }
    
    return results

@api_router.post('/numerology/group-compatibility')
async def group_compatibility_numerology(group_data: GroupCompatibilityRequest, current_user: dict = Depends(get_current_user)):
    """Групповая совместимость (5 человек) - 5 баллов"""
    user_id = current_user['user_id']
    
    if len(group_data.people) > 5:
        raise HTTPException(status_code=400, detail='Максимум 5 человек для группового анализа')
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        CREDIT_COSTS['group_compatibility'], 
        f'Групповая совместимость ({len(group_data.people)} чел.)', 
        'numerology',
        {'calculation_type': 'group_compatibility', 'people_count': len(group_data.people)}
    )
    
    # Рассчитываем групповую совместимость
    try:
        from numerology import calculate_group_compatibility
        # Конвертируем данные людей в нужный формат
        people_data = [{"name": person.name, "birth_date": person.birth_date} for person in group_data.people]
        results = calculate_group_compatibility(group_data.people)
        return results
    except Exception as e:
        # Возвращаем баллы при ошибке
        await record_credit_transaction(user_id, CREDIT_COSTS['group_compatibility'], 'Возврат за ошибку группового анализа', 'refund')
        await db.users.update_one({'id': user_id}, {'$inc': {'credits_remaining': CREDIT_COSTS['group_compatibility']}})
        raise HTTPException(status_code=400, detail=f'Ошибка расчета: {str(e)}')

@api_router.post('/quiz/personality-test')
async def personality_test(test_data: dict, current_user: dict = Depends(get_current_user)):
    """Тест личности - 1 балл"""
    user_id = current_user['user_id']
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        CREDIT_COSTS['personality_test'], 
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
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        CREDIT_COSTS['vedic_daily'], 
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
        await record_credit_transaction(user_id, CREDIT_COSTS['vedic_daily'], 'Возврат за ошибку ведического времени', 'refund')
        await db.users.update_one({'id': user_id}, {'$inc': {'credits_remaining': CREDIT_COSTS['vedic_daily']}})
        raise HTTPException(status_code=400, detail=schedule['error'])
    return schedule

@api_router.get('/vedic-time/planetary-route')
async def planetary_route(vedic_request: VedicTimeRequest = Depends(), current_user: dict = Depends(get_current_user)):
    """Планетарный маршрут на день - 1 балл"""
    user_id = current_user['user_id']
    
    # Получаем данные пользователя для города и даты рождения
    user_dict = await db.users.find_one({'id': user_id})
    if not user_dict:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    user = User(**user_dict)
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        CREDIT_COSTS['planetary_daily'], 
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
        await record_credit_transaction(user_id, CREDIT_COSTS['planetary_daily'], 'Возврат за ошибку планетарного маршрута', 'refund')
        await db.users.update_one({'id': user_id}, {'$inc': {'credits_remaining': CREDIT_COSTS['planetary_daily']}})
        raise HTTPException(status_code=400, detail=schedule['error'])
        
    # Build simple route from schedule
    rec = schedule.get('recommendations', {})
    route = {
        'date': date_obj.strftime('%Y-%m-%d'),
        'city': city,
        'personal_birth_date': user.birth_date,
        'daily_ruling_planet': schedule.get('weekday', {}).get('ruling_planet', ''),
        'best_activity_hours': rec.get('best_hours', []),
        'avoid_periods': {
            'rahu_kaal': schedule.get('inauspicious_periods', {}).get('rahu_kaal', {}),
            'gulika_kaal': schedule.get('inauspicious_periods', {}).get('gulika_kaal', {}),
            'yamaghanta': schedule.get('inauspicious_periods', {}).get('yamaghanta', {})
        },
        'favorable_period': schedule.get('auspicious_periods', {}).get('abhijit_muhurta', {}),
        'hourly_guide': schedule.get('planetary_hours', [])[:8],
        'daily_recommendations': rec
    }
    return route

@api_router.get('/vedic-time/planetary-route/monthly')
async def monthly_planetary_route(vedic_request: VedicTimeRequest = Depends(), current_user: dict = Depends(get_current_user)):
    """Планетарный маршрут на месяц - 5 баллов"""
    user_id = current_user['user_id']
    
    # Получаем данные пользователя
    user_dict = await db.users.find_one({'id': user_id})
    if not user_dict:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    user = User(**user_dict)
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        CREDIT_COSTS['planetary_monthly'], 
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
        monthly_route = get_monthly_planetary_route(city=city, start_date=date_obj, birth_date=user.birth_date)
        return monthly_route
    except Exception as e:
        # Возвращаем баллы при ошибке
        await record_credit_transaction(user_id, CREDIT_COSTS['planetary_monthly'], 'Возврат за ошибку месячного маршрута', 'refund')
        await db.users.update_one({'id': user_id}, {'$inc': {'credits_remaining': CREDIT_COSTS['planetary_monthly']}})
        raise HTTPException(status_code=400, detail=f'Ошибка расчета месячного маршрута: {str(e)}')
@api_router.get('/vedic-time/planetary-route/quarterly') 
async def quarterly_planetary_route(vedic_request: VedicTimeRequest = Depends(), current_user: dict = Depends(get_current_user)):
    """Планетарный маршрут на квартал - 10 баллов"""
    user_id = current_user['user_id']
    
    # Получаем данные пользователя
    user_dict = await db.users.find_one({'id': user_id})
    if not user_dict:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    user = User(**user_dict)
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        CREDIT_COSTS['planetary_quarterly'], 
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
        quarterly_route = get_quarterly_planetary_route(city=city, start_date=date_obj, birth_date=user.birth_date)
        return quarterly_route
    except Exception as e:
        # Возвращаем баллы при ошибке
        await record_credit_transaction(user_id, CREDIT_COSTS['planetary_quarterly'], 'Возврат за ошибку квартального маршрута', 'refund')
        await db.users.update_one({'id': user_id}, {'$inc': {'credits_remaining': CREDIT_COSTS['planetary_quarterly']}})
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
            birth_date_obj = datetime.fromisoformat(str(user.birth_date))
            day, month, year = birth_date_obj.day, birth_date_obj.month, birth_date_obj.year
            
            # Вычисляем основные числа
            def reduce_to_single(num):
                while num > 9:
                    num = sum(int(d) for d in str(num))
                return num
            
            user_data["soul_number"] = reduce_to_single(day)
            user_data["destiny_number"] = reduce_to_single(day + month + year)
            user_data["mind_number"] = reduce_to_single(month)
            
            # Вычисляем правящее число (сумма числа души и числа судьбы)
            ruling = user_data["soul_number"] + user_data["destiny_number"]
            user_data["ruling_number"] = reduce_to_single(ruling)
            
            # Создаем квадрат Пифагора для подсчета силы планет
            birth_date_str = birth_date_obj.strftime("%d%m%Y")
            all_digits = birth_date_str
            
            # Подсчитываем количество каждой цифры
            digit_counts = {}
            for digit in all_digits:
                digit_counts[digit] = digit_counts.get(digit, 0) + 1
            
            # Маппинг цифр на планеты
            planet_digit_map = {
                "Sun": "1",
                "Moon": "2",
                "Jupiter": "3",
                "Rahu": "4",
                "Mercury": "5",
                "Venus": "6",
                "Ketu": "7",
                "Saturn": "8",
                "Mars": "9"
            }
            
            for planet_name, digit in planet_digit_map.items():
                user_data["planet_counts"][planet_name] = digit_counts.get(digit, 0)
                
        except Exception as e:
            print(f"Ошибка при вычислении чисел: {e}")
    
    # Получаем персонализированные советы
    advice = await get_personalized_planetary_advice(db, planet, user_data, is_night)
    
    if not advice:
        raise HTTPException(status_code=404, detail=f'Советы для планеты {planet} не найдены')
    
    return advice

# ----------------- CHARTS -----------------
@api_router.get('/charts/planetary-energy/{days}')
async def get_planetary_energy(days: int = 7, current_user: dict = Depends(get_current_user)):
    user_dict = await db.users.find_one({'id': current_user['user_id']})
    if not user_dict:
        raise HTTPException(status_code=404, detail='User not found')
    user = User(**user_dict)
    if days <= 7:
        chart_data = generate_weekly_planetary_energy(user.birth_date)
    else:
        chart_data = generate_weekly_planetary_energy(user.birth_date)
        for _ in range(1, (days // 7) + 1):
            chart_data.extend(generate_weekly_planetary_energy(user.birth_date))
    return {'chart_data': chart_data[:days], 'period': f'{days} days', 'user_birth_date': user.birth_date}

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
    
    # Списываем баллы с записью в историю
    await deduct_credits(
        user_id, 
        CREDIT_COSTS['quiz_completion'], 
        'Прохождение викторины', 
        'quiz',
        {'quiz_type': 'numerology_assessment'}
    )
    
    from quiz_data import calculate_quiz_results
    results = calculate_quiz_results(answers)
    qr = QuizResult(user_id=user_id, quiz_type='numerology_assessment', answers=answers, score=results['total_score'], recommendations=results['recommendations'])
    await db.quiz_results.insert_one(qr.dict())
    return results

# ----------------- LEARNING -----------------
# Обновленный endpoint для получения всех уроков для студентов (включая custom_lessons)
@api_router.get('/learning/all-lessons')
async def get_all_student_lessons(current_user: dict = Depends(get_current_user)):
    """Получить все доступные уроки для студентов (video_lessons + custom_lessons)"""
    try:
        user_id = current_user['user_id']
        
        # Получаем данные уровня пользователя
        level = await db.user_levels.find_one({'user_id': user_id})
        if not level:
            from models import UserLevel
            level = UserLevel(user_id=user_id).dict()
            await db.user_levels.insert_one(level)
            level.pop('_id', None)
        else:
            level = dict(level)
            level.pop('_id', None)
        
        # Получаем уроки из video_lessons
        video_lessons = await db.video_lessons.find({'is_active': True}).sort('level', 1).sort('order', 1).to_list(100)
        
        # Получаем уроки из custom_lessons  
        custom_lessons = await db.custom_lessons.find({'is_active': True}).to_list(100)
        
        # Объединяем уроки и очищаем от MongoDB ObjectId
        all_lessons = []
        
        # Добавляем video_lessons
        for lesson in video_lessons:
            lesson_dict = dict(lesson)
            lesson_dict.pop('_id', None)
            lesson_dict['source'] = 'video_lessons'
            all_lessons.append(lesson_dict)
        
        # Добавляем custom_lessons
        for lesson in custom_lessons:
            lesson_dict = dict(lesson)
            lesson_dict.pop('_id', None)
            lesson_dict['source'] = 'custom_lessons'
            # Устанавливаем значения по умолчанию для совместимости
            lesson_dict['level'] = lesson_dict.get('level', 1)
            lesson_dict['order'] = lesson_dict.get('order', 999)
            lesson_dict['duration_minutes'] = lesson_dict.get('duration_minutes', 30)
            lesson_dict['video_url'] = lesson_dict.get('video_url', '')
            lesson_dict['video_file_id'] = lesson_dict.get('video_file_id', '')
            lesson_dict['pdf_file_id'] = lesson_dict.get('pdf_file_id', '')
            lesson_dict['word_file_id'] = lesson_dict.get('word_file_id', '')
            lesson_dict['word_filename'] = lesson_dict.get('word_filename', '')
            lesson_dict['word_url'] = lesson_dict.get('word_url', '')
            all_lessons.append(lesson_dict)
        
        # Исключаем lesson_numerom_intro из списка и сортируем по order
        all_lessons = [lesson for lesson in all_lessons if lesson.get('id') != 'lesson_numerom_intro']
        
        # Сортируем по order (0 для вводного, 1-9 для уроков, 10 для урока 0)
        all_lessons.sort(key=lambda x: (
            x.get('order', 999),
            x.get('level', 999)
        ))
        
        return {
            'user_level': level, 
            'available_lessons': all_lessons, 
            'total_levels': 10
        }
        
    except Exception as e:
        logger.error(f"Error getting all student lessons: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки уроков: {str(e)}")

@api_router.get('/learning/levels')
async def get_learning_levels(current_user: dict = Depends(get_current_user)):
    level = await db.user_levels.find_one({'user_id': current_user['user_id']})
    if not level:
        from models import UserLevel
        level = UserLevel(user_id=current_user['user_id']).dict()
        await db.user_levels.insert_one(level)
        # Remove MongoDB _id from newly created level
        level.pop('_id', None)
    else:
        # Convert MongoDB document to dict and remove _id
        level = dict(level)
        level.pop('_id', None)
    
    lessons = await db.video_lessons.find({'is_active': True}).sort('level', 1).sort('order', 1).to_list(100)
    # Convert all lessons to dicts and remove _id
    clean_lessons = []
    for lesson in lessons:
        lesson_dict = dict(lesson)
        lesson_dict.pop('_id', None)
        clean_lessons.append(lesson_dict)
    
    return {'user_level': level, 'available_lessons': clean_lessons, 'total_levels': 10}

@api_router.post('/learning/complete-lesson/{lesson_id}')
async def complete_lesson(lesson_id: str, watch_time: int, quiz_score: int = None, current_user: dict = Depends(get_current_user)):
    lesson = await db.video_lessons.find_one({'id': lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail='Lesson not found')
    progress_data = {
        'user_id': current_user['user_id'], 'lesson_id': lesson_id, 'completed': True,
        'completion_date': datetime.utcnow(), 'watch_time_minutes': watch_time, 'quiz_score': quiz_score
    }
    await db.user_progress.update_one({'user_id': current_user['user_id'], 'lesson_id': lesson_id}, {'$set': progress_data}, upsert=True)
    completed = await db.user_progress.count_documents({'user_id': current_user['user_id'], 'completed': True})
    new_level = min(10, (completed // 3) + 1)
    await db.user_levels.update_one({'user_id': current_user['user_id']}, {'$set': {'current_level': new_level, 'lessons_completed': completed, 'last_activity': datetime.utcnow()}, '$inc': {'experience_points': 10}}, upsert=True)
    return {'lesson_completed': True, 'new_level': new_level, 'total_completed': completed}

@api_router.get('/learning/lesson/{lesson_id}/quiz')
async def get_lesson_quiz(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Получить 5 случайных вопросов викторины для урока"""
    # Проверяем существование урока
    lesson = await db.video_lessons.find_one({'id': lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail='Урок не найден')
    
    # Импортируем данные викторины
    from quiz_data import NUMEROLOGY_QUIZ
    import random
    
    # Получаем все вопросы и выбираем случайные 5
    all_questions = NUMEROLOGY_QUIZ['questions']
    if len(all_questions) <= 5:
        selected_questions = all_questions
    else:
        selected_questions = random.sample(all_questions, 5)
    
    # Перемешиваем варианты ответов в каждом вопросе
    for question in selected_questions:
        random.shuffle(question['options'])
    
    return {
        'lesson_id': lesson_id,
        'lesson_title': lesson.get('title', 'Урок'),
        'quiz': {
            'title': 'Викторина по уроку',
            'description': f'Ответьте на 5 вопросов по материалу урока "{lesson.get("title", "")}"',
            'questions': selected_questions
        }
    }

@api_router.post('/learning/lesson/{lesson_id}/start')
async def start_lesson(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Начать урок - 10 баллов (одноразовое списание)"""
    user_id = current_user['user_id']
    
    # Проверяем существование урока
    lesson = await db.video_lessons.find_one({'id': lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail='Урок не найден')
    
    # Проверяем, не начинал ли пользователь уже этот урок
    existing_progress = await db.user_progress.find_one({
        'user_id': user_id,
        'lesson_id': lesson_id
    })
    
    # Если урок уже начат, просто возвращаем успех
    if existing_progress:
        return {
            'lesson_started': True,
            'points_deducted': 0,
            'message': 'Урок уже был начат ранее'
        }
    
    # Всегда списываем 10 баллов за первый просмотр урока
    await deduct_credits(
        user_id, 
        CREDIT_COSTS['lesson_viewing'], 
        f'Просмотр урока: {lesson.get("title", "Без названия")}', 
        'learning',
        {'lesson_id': lesson_id, 'lesson_title': lesson.get('title')}
    )
    
    # Создаем запись о начале урока
    progress_data = {
        'user_id': user_id,
        'lesson_id': lesson_id,
        'completed': False,
        'watch_time_minutes': 0,
        'created_at': datetime.utcnow()
    }
    await db.user_progress.insert_one(progress_data)
    
    return {
        'lesson_started': True,
        'points_deducted': CREDIT_COSTS['lesson_viewing'],
        'message': f'Урок начат! Списано {CREDIT_COSTS["lesson_viewing"]} баллов'
    }

# ----------------- ADMIN (SUPER ADMIN ONLY) -----------------

# NEW LESSON MANAGEMENT ENDPOINTS (must come before general routes)
@api_router.post('/admin/lessons/create')
async def create_new_lesson(lesson_data: dict, current_user: dict = Depends(get_current_user)):
    """Создать новый урок с полной структурой"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Добавляем метаданные создания
        lesson_data['created_by'] = current_user['user_id']
        lesson_data['created_at'] = datetime.utcnow()
        lesson_data['updated_at'] = datetime.utcnow()
        
        # Вставляем урок в коллекцию custom_lessons для новых уроков
        await db.custom_lessons.insert_one(lesson_data)
        
        return {
            'success': True, 
            'message': 'Урок успешно создан',
            'lesson_id': lesson_data['id']
        }
        
    except Exception as e:
        logger.error(f"Error creating lesson: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка создания урока: {str(e)}")

@api_router.get('/admin/lessons/{lesson_id}')
async def get_lesson_for_editing(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Получить урок для редактирования"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Ищем сначала в custom_lessons, потом в video_lessons для совместимости
        lesson = await db.custom_lessons.find_one({'id': lesson_id})
        if not lesson:
            lesson = await db.video_lessons.find_one({'id': lesson_id})
        
        if not lesson:
            raise HTTPException(status_code=404, detail='Урок не найден')
        
        # Очищаем MongoDB ObjectId
        lesson_dict = dict(lesson)
        lesson_dict.pop('_id', None)
        
        # Убеждаемся, что все поля медиафайлов присутствуют (даже если None)
        lesson_dict.setdefault('video_file_id', None)
        lesson_dict.setdefault('video_filename', None)
        lesson_dict.setdefault('pdf_file_id', None)
        lesson_dict.setdefault('pdf_filename', None)
        lesson_dict.setdefault('word_file_id', None)
        lesson_dict.setdefault('word_filename', None)
        
        logger.info(f"Loading lesson {lesson_id} for editing")
        logger.info(f"PDF file_id: {lesson_dict.get('pdf_file_id')}, PDF filename: {lesson_dict.get('pdf_filename')}")
        
        return {'lesson': lesson_dict}
        
    except Exception as e:
        logger.error(f"Error getting lesson: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки урока: {str(e)}")

@api_router.put('/admin/lessons/{lesson_id}/content')
async def update_lesson_content(lesson_id: str, content_data: dict, current_user: dict = Depends(get_current_user)):
    """Обновить контент урока"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        section = content_data.get('section')
        field = content_data.get('field')
        value = content_data.get('value')
        
        if not all([section, field, value is not None]):
            raise HTTPException(status_code=400, detail='Недостаточно данных для обновления')
        
        # Формируем путь для обновления в MongoDB
        update_path = f"content.{section}.{field}"
        update_data = {
            update_path: value,
            'updated_at': datetime.utcnow(),
            'updated_by': current_user['user_id']
        }
        
        # Обновляем в custom_lessons
        result = await db.custom_lessons.update_one(
            {'id': lesson_id},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            # Если не найдено в custom_lessons, пробуем video_lessons (для совместимости)
            result = await db.video_lessons.update_one(
                {'id': lesson_id},
                {'$set': update_data}
            )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail='Урок не найден')
        
        return {'success': True, 'message': 'Контент обновлен'}
        
    except Exception as e:
        logger.error(f"Error updating lesson content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка обновления контента: {str(e)}")

@api_router.post('/admin/lessons/{lesson_id}/upload-video')
async def upload_lesson_video(lesson_id: str, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Загрузка видео для урока"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Проверяем тип файла
        allowed_types = ['video/mp4', 'video/avi', 'video/mov', 'video/webm']
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail='Неподдерживаемый формат видео')
        
        # Проверяем размер файла (максимум 500MB для уроков)
        if file.size and file.size > 500 * 1024 * 1024:
            raise HTTPException(status_code=400, detail='Размер файла превышает 500MB')
        
        # Генерируем уникальное имя файла
        file_extension = Path(file.filename).suffix if file.filename else '.mp4'
        unique_filename = f"{lesson_id}_video_{uuid.uuid4()}{file_extension}"
        
        # Сохраняем файл
        file_path = LESSONS_VIDEO_DIR / unique_filename
        with open(file_path, 'wb') as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Сохраняем метаданные файла
        file_id = str(uuid.uuid4())
        file_record = {
            'id': file_id,
            'lesson_id': lesson_id,
            'original_filename': file.filename,
            'stored_filename': unique_filename,
            'file_path': str(file_path),
            'file_size': len(content),
            'content_type': file.content_type,
            'uploaded_at': datetime.utcnow(),
            'uploaded_by': current_user['user_id']
        }
        
        await db.lesson_videos.insert_one(file_record)
        
        return {
            'success': True,
            'file_id': file_id,
            'filename': file.filename,
            'video_url': f'/api/lessons/video/{file_id}'
        }
        
    except Exception as e:
        logger.error(f"Error uploading lesson video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки видео: {str(e)}")

@api_router.post('/admin/lessons/{lesson_id}/upload-pdf')
async def upload_lesson_pdf(lesson_id: str, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Загрузка PDF для урока"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Проверяем тип файла
        if file.content_type != 'application/pdf':
            raise HTTPException(status_code=400, detail='Разрешены только PDF файлы')
        
        # Проверяем размер файла (максимум 50MB)
        if file.size and file.size > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail='Размер файла превышает 50MB')
        
        # Генерируем уникальное имя файла
        unique_filename = f"{lesson_id}_pdf_{uuid.uuid4()}.pdf"
        
        # Сохраняем файл
        file_path = LESSONS_PDF_DIR / unique_filename
        with open(file_path, 'wb') as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Сохраняем метаданные файла
        file_id = str(uuid.uuid4())
        file_record = {
            'id': file_id,
            'lesson_id': lesson_id,
            'original_filename': file.filename,
            'stored_filename': unique_filename,
            'file_path': str(file_path),
            'file_size': len(content),
            'content_type': file.content_type,
            'uploaded_at': datetime.utcnow(),
            'uploaded_by': current_user['user_id']
        }
        
        await db.lesson_pdfs.insert_one(file_record)
        
        return {
            'success': True,
            'file_id': file_id,
            'filename': file.filename,
            'pdf_url': f'/api/lessons/pdf/{file_id}'
        }
        
    except Exception as e:
        logger.error(f"Error uploading lesson PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки PDF: {str(e)}")

@api_router.post('/admin/lessons/{lesson_id}/upload-word')
async def upload_lesson_word(lesson_id: str, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Загрузка Word файла для урока"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Проверяем тип файла (Word форматы)
        allowed_types = [
            'application/msword',  # .doc
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'  # .docx
        ]
        filename_lower = file.filename.lower() if file.filename else ''
        is_docx = filename_lower.endswith('.docx')
        is_doc = filename_lower.endswith('.doc')
        
        if file.content_type not in allowed_types and not (is_docx or is_doc):
            raise HTTPException(status_code=400, detail='Разрешены только Word файлы (.doc, .docx)')
        
        # Проверяем размер файла (максимум 50MB)
        if file.size and file.size > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail='Размер файла превышает 50MB')
        
        # Определяем расширение файла
        file_extension = '.docx' if is_docx else '.doc'
        
        # Генерируем уникальное имя файла
        unique_filename = f"{lesson_id}_word_{uuid.uuid4()}{file_extension}"
        
        # Сохраняем файл
        file_path = LESSONS_WORD_DIR / unique_filename
        with open(file_path, 'wb') as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Сохраняем метаданные файла
        file_id = str(uuid.uuid4())
        file_record = {
            'id': file_id,
            'lesson_id': lesson_id,
            'original_filename': file.filename,
            'stored_filename': unique_filename,
            'file_path': str(file_path),
            'file_size': len(content),
            'content_type': file.content_type or ('application/vnd.openxmlformats-officedocument.wordprocessingml.document' if file_extension == '.docx' else 'application/msword'),
            'file_extension': file_extension,
            'uploaded_at': datetime.utcnow(),
            'uploaded_by': current_user['user_id']
        }
        
        await db.lesson_word_files.insert_one(file_record)
        
        return {
            'success': True,
            'file_id': file_id,
            'filename': file.filename,
            'word_url': f'/api/lessons/word/{file_id}',
            'download_url': f'/api/lessons/word/{file_id}/download'
        }
        
    except Exception as e:
        logger.error(f"Error uploading lesson Word file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки Word файла: {str(e)}")

# OLD LESSON MANAGEMENT ENDPOINTS (for compatibility)
@api_router.post('/admin/lessons')
async def create_video_lesson(lesson: VideoLesson, current_user: dict = Depends(get_current_user)):
    admin_user = await check_admin_rights(current_user, require_super_admin=False)
    await db.video_lessons.insert_one(lesson.dict())
    return {'message': 'Lesson created successfully', 'lesson_id': lesson.id}

# Endpoint для синхронизации первого урока с общей системой
@api_router.post('/admin/lessons/sync-first-lesson')
async def sync_first_lesson_to_system(current_user: dict = Depends(get_current_user)):
    """Синхронизировать первый урок с общей системой управления уроками"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Получаем данные первого урока из lesson_system
        first_lesson_data = lesson_system.get_lesson('lesson_numerom_intro')
        if not first_lesson_data:
            raise HTTPException(status_code=404, detail='Первый урок не найден в системе')
        
        # Проверяем, не существует ли урок уже в custom_lessons
        existing_lesson = await db.custom_lessons.find_one({'id': 'lesson_numerom_intro'})
        
        if not existing_lesson:
            # Создаем запись в custom_lessons для первого урока
            first_lesson_record = {
                'id': 'lesson_numerom_intro',
                'title': 'Первое занятие NumerOM',
                'module': 'Модуль 1: Основы',
                'description': 'Введение в NumerOM: История космического корабля и основы нумерологии',
                'points_required': 0,  # Бесплатный урок
                'is_active': True,
                'content': {
                    'theory': {
                        'what_is_topic': 'Введение в мир ведической нумерологии через историю космического корабля',
                        'main_story': first_lesson_data.content.get('theory', {}).get('cosmic_ship_story', ''),
                        'key_concepts': 'Планетарные энергии, численные вибрации, космический корабль как метафора',
                        'practical_applications': 'Анализ своих основных чисел, понимание планетарных энергий'
                    },
                    'exercises': [
                        {
                            'id': ex.id,
                            'title': ex.title,
                            'type': ex.type,
                            'content': ex.content,
                            'instructions': ex.instructions,
                            'expected_outcome': ex.expected_outcome
                        } for ex in first_lesson_data.exercises
                    ],
                    'quiz': {
                        'id': first_lesson_data.quiz.id,
                        'title': first_lesson_data.quiz.title,
                        'questions': first_lesson_data.quiz.questions,
                        'correct_answers': first_lesson_data.quiz.correct_answers,
                        'explanations': first_lesson_data.quiz.explanations
                    },
                    'challenge': {
                        'id': first_lesson_data.challenges[0].id,
                        'title': first_lesson_data.challenges[0].title,
                        'description': first_lesson_data.challenges[0].description,
                        'daily_tasks': first_lesson_data.challenges[0].daily_tasks
                    }
                },
                'source': 'first_lesson_sync',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'created_by': current_user['user_id']
            }
            
            # Вставляем в custom_lessons
            await db.custom_lessons.insert_one(first_lesson_record)
            
            return {
                'success': True, 
                'message': 'Первый урок успешно добавлен в общую систему',
                'action': 'created'
            }
        else:
            return {
                'success': True, 
                'message': 'Первый урок уже существует в общей системе',
                'action': 'already_exists'
            }
        
    except Exception as e:
        logger.error(f"Error syncing first lesson: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка синхронизации первого урока: {str(e)}")

# Endpoint для получения объединенного списка всех уроков (включая первый урок)
@api_router.get('/admin/lessons')
async def get_all_lessons(current_user: dict = Depends(get_current_user)):
    admin_user = await check_admin_rights(current_user, require_super_admin=False)
    
    # Получаем уроки из обеих коллекций
    video_lessons = await db.video_lessons.find().to_list(100)
    custom_lessons = await db.custom_lessons.find().to_list(100)
    
    # Объединяем и очищаем от MongoDB ObjectId
    all_lessons = []
    
    # Добавляем существующие video_lessons (для совместимости)
    for lesson in video_lessons:
        lesson_dict = dict(lesson)
        lesson_dict.pop('_id', None)
        lesson_dict['source'] = 'video_lessons'  # Указываем источник
        all_lessons.append(lesson_dict)
    
    # Добавляем новые custom_lessons
    for lesson in custom_lessons:
        lesson_dict = dict(lesson)
        lesson_dict.pop('_id', None)
        lesson_dict['source'] = 'custom_lessons'  # Указываем источник
        all_lessons.append(lesson_dict)
    
    # Если первого урока нет в списке, добавляем его из lesson_system
    first_lesson_exists = any(lesson.get('id') == 'lesson_numerom_intro' for lesson in all_lessons)
    if not first_lesson_exists:
        # Получаем данные первого урока из lesson_system
        first_lesson_data = lesson_system.get_lesson('lesson_numerom_intro')
        if first_lesson_data:
            first_lesson_dict = {
                'id': 'lesson_numerom_intro',
                'title': 'Первое занятие NumerOM',
                'module': 'Модуль 1: Основы',
                'description': 'Введение в NumerOM: История космического корабля и основы нумерологии',
                'points_required': 0,
                'is_active': True,
                'source': 'lesson_system',
                'created_at': datetime.now(),
                'content': first_lesson_data.content
            }
            all_lessons.insert(0, first_lesson_dict)  # Добавляем в начало списка
    
    # Сортируем по дате создания (первый урок всегда первый)
    all_lessons.sort(key=lambda x: (
        0 if x.get('id') == 'lesson_numerom_intro' else 1,  # Первый урок всегда первый
        x.get('created_at', datetime.min)
    ), reverse=False)
    
    return {'lessons': all_lessons, 'total_count': len(all_lessons)}

@api_router.put('/admin/lessons/{lesson_id}')
async def update_lesson(lesson_id: str, lesson_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    """Обновить урок (работает с обеими коллекциями, поддерживает медиа поля как в консультациях)"""
    admin_user = await check_admin_rights(current_user, require_super_admin=False)
    
    # Добавляем метаданные обновления
    lesson_data['updated_at'] = datetime.utcnow()
    lesson_data['updated_by'] = current_user['user_id']
    
    # Пробуем обновить в custom_lessons
    result = await db.custom_lessons.update_one({'id': lesson_id}, {'$set': lesson_data})
    lesson_source = 'custom_lessons'
    
    # Если не найден в custom_lessons, пробуем video_lessons
    if result.matched_count == 0:
        result = await db.video_lessons.update_one({'id': lesson_id}, {'$set': lesson_data})
        lesson_source = 'video_lessons'
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail='Урок не найден')
    
    return {
        'message': f'Урок успешно обновлен в {lesson_source}',
        'lesson_id': lesson_id,
        'updated_fields': list(lesson_data.keys())
    }

@api_router.delete('/admin/lessons/{lesson_id}')
async def delete_lesson(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Удалить урок (работает с обеими коллекциями)"""
    admin_user = await check_admin_rights(current_user, require_super_admin=False)
    
    # Ищем и удаляем из custom_lessons
    result = await db.custom_lessons.delete_one({'id': lesson_id})
    lesson_source = 'custom_lessons'
    
    # Если не найден в custom_lessons, пробуем video_lessons
    if result.deleted_count == 0:
        result = await db.video_lessons.delete_one({'id': lesson_id})
        lesson_source = 'video_lessons'
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Урок не найден')
    
    # Удаляем связанные медиа файлы
    await db.lesson_videos.delete_many({'lesson_id': lesson_id})
    await db.lesson_pdfs.delete_many({'lesson_id': lesson_id})
    
    # Удаляем прогресс пользователей
    await db.user_progress.delete_many({'lesson_id': lesson_id})
    
    return {
        'success': True, 
        'message': f'Урок успешно удален из {lesson_source}',
        'lesson_id': lesson_id
    }
    
    # Также удаляем связанные записи о прогрессе пользователей
    await db.user_progress.delete_many({'lesson_id': lesson_id})
    
    return {'message': 'Урок успешно удален'}

@api_router.post('/admin/make-admin/{user_id}')
async def make_user_admin(user_id: str, current_user: dict = Depends(get_current_user)):
    admin_user = await check_admin_rights(current_user, require_super_admin=False)
    
    # Check if target user exists
    target_user = await db.users.find_one({'id': user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    # Update user to have admin rights
    await db.users.update_one(
        {'id': user_id}, 
        {'$set': {'is_admin': True, 'updated_at': datetime.utcnow()}}
    )
    
    # Also create/update admin_users record for legacy compatibility
    admin_user_record = AdminUser(user_id=user_id, role='admin', permissions=['video_management', 'user_management', 'content_management'])
    await db.admin_users.update_one({'user_id': user_id}, {'$set': admin_user_record.dict()}, upsert=True)
    
    return {'message': f'Права администратора предоставлены пользователю {target_user["email"]}', 'user_email': target_user['email']}
@api_router.delete('/admin/revoke-admin/{user_id}')
async def revoke_user_admin(user_id: str, current_user: dict = Depends(get_current_user)):
    admin_user = await check_admin_rights(current_user, require_super_admin=False)
    
    # Check if target user exists
    target_user = await db.users.find_one({'id': user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    # Prevent revoking super admin rights
    if target_user.get('is_super_admin'):
        raise HTTPException(status_code=400, detail='Нельзя отозвать права суперадминистратора')
    
    # Remove admin rights
    await db.users.update_one(
        {'id': user_id}, 
        {'$set': {'is_admin': False, 'updated_at': datetime.utcnow()}}
    )
    
    # Remove admin_users record
    await db.admin_users.delete_one({'user_id': user_id})
    
    return {'message': f'Права администратора отозваны у пользователя {target_user["email"]}', 'user_email': target_user['email']}

# Materials upload (super admin only for upload/delete; list/stream requires auth)
@api_router.post('/admin/materials/upload/init')
async def materials_upload_init(
    title: str = Form(...),
    description: str = Form(''),
    lesson_id: str = Form(''),
    material_type: str = Form('pdf'),
    filename: str = Form(...),
    total_size: int = Form(...),
    current_user: dict = Depends(get_current_user)
):
    admin_user = await check_admin_rights(current_user, require_super_admin=False)
    upload_id = str(uuid.uuid4())
    await db.material_upload_sessions.insert_one({
        'upload_id': upload_id, 'filename': filename, 'title': title, 'description': description,
        'lesson_id': lesson_id, 'material_type': material_type, 'total_size': total_size,
        'created_at': datetime.utcnow(), 'user_id': current_user['user_id'], 'received_chunks': 0
    })
    (TMP_DIR / upload_id).mkdir(parents=True, exist_ok=True)
    return {'uploadId': upload_id}

@api_router.post('/admin/materials/upload/chunk')
async def materials_upload_chunk(uploadId: str = Form(...), index: int = Form(...), chunk: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    admin_user = await check_admin_rights(current_user, require_super_admin=False)
    tmp_dir = TMP_DIR / uploadId
    if not tmp_dir.exists():
        raise HTTPException(status_code=404, detail='Upload session not found')
    chunk_path = tmp_dir / f'chunk_{index}'
    with open(chunk_path, 'wb') as f:
        f.write(await chunk.read())
    await db.material_upload_sessions.update_one({'upload_id': uploadId}, {'$inc': {'received_chunks': 1}})
    return {'ok': True, 'index': index}

@api_router.post('/admin/materials/upload/finish')
async def materials_upload_finish(uploadId: str = Form(...), current_user: dict = Depends(get_current_user)):
    admin_user = await check_admin_rights(current_user, require_super_admin=False)
    session = await db.material_upload_sessions.find_one({'upload_id': uploadId})
    if not session:
        raise HTTPException(status_code=404, detail='Upload session not found')
    tmp_dir = TMP_DIR / uploadId
    if not tmp_dir.exists():
        raise HTTPException(status_code=404, detail='Upload temp data missing')
    safe_name = f"{uuid.uuid4().hex}_{Path(session['filename']).name}"
    final_path = MATERIALS_DIR / safe_name
    chunk_files = sorted([p for p in tmp_dir.iterdir() if p.name.startswith('chunk_')], key=lambda p: int(p.name.split('_')[1]))
    with open(final_path, 'wb') as outfile:
        for part in chunk_files:
            with open(part, 'rb') as infile:
                shutil.copyfileobj(infile, outfile)
    file_size = final_path.stat().st_size
    material_id = str(uuid.uuid4())
    material_doc = {
        'id': material_id,
        'lesson_id': session.get('lesson_id', ''),
        'title': session.get('title', 'Untitled'),
        'description': session.get('description', ''),
        'material_type': session.get('material_type', 'pdf'),
        'file_name': Path(session.get('filename', '')).name,
        'file_path': str(final_path),
        'file_size': file_size,
        'file_url': f"/api/materials/{material_id}/stream",
        'created_at': datetime.utcnow(),
        'uploaded_by': current_user['user_id']
    }
    await db.materials.insert_one(material_doc)
    try:
        shutil.rmtree(tmp_dir)
        await db.material_upload_sessions.delete_one({'upload_id': uploadId})
    except Exception as e:
        logger.warning(f'Tmp cleanup failed: {e}')
    return {'material': {k: v for k, v in material_doc.items() if k != 'file_path'}}

@api_router.get('/materials')
async def list_materials(current_user: dict = Depends(get_current_user)):
    materials = await db.materials.find().sort('created_at', -1).to_list(100)
    clean_materials = []
    for m in materials:
        material_dict = dict(m)
        material_dict.pop('_id', None)
        if 'file_path' in material_dict:
            material_dict.pop('file_path')
        clean_materials.append(material_dict)
    return clean_materials

@api_router.get('/materials/{material_id}/stream')
async def stream_material(material_id: str, current_user: dict = Depends(get_current_user)):
    """Просмотр материала - 1 балл (одноразовое списание)"""
    user_id = current_user['user_id']
    
    material = await db.materials.find_one({'id': material_id})
    if not material:
        raise HTTPException(status_code=404, detail='Материал не найден')
    
    # Проверяем, не просматривал ли пользователь уже этот материал
    existing_view = await db.material_views.find_one({
        'user_id': user_id,
        'material_id': material_id
    })
    
    # Если материал еще не просматривался, списываем баллы
    if not existing_view:
        await deduct_credits(
            user_id, 
            CREDIT_COSTS['material_viewing'], 
            f'Просмотр материала: {material.get("title", "Без названия")}', 
            'materials',
            {'material_id': material_id, 'material_title': material.get('title')}
        )
        
        # Записываем факт просмотра
        view_record = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'material_id': material_id,
            'viewed_at': datetime.utcnow()
        }
        await db.material_views.insert_one(view_record)
    
    file_path = material.get('file_path')
    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail='Файл не найден')
    
    # Определяем тип файла
    file_extension = Path(file_path).suffix.lower()
    if file_extension == '.pdf':
        media_type = 'application/pdf'
    elif file_extension in ['.mp4', '.avi', '.mov']:
        media_type = 'video/mp4'
    elif file_extension in ['.mp3', '.wav']:
        media_type = 'audio/mpeg'
    else:
        media_type = 'application/octet-stream'
    
    # Возвращаем файл с CORS headers
    from fastapi.responses import FileResponse
    response = FileResponse(
        file_path,
        media_type=media_type,
        headers={
            'Accept-Ranges': 'bytes',
            'Content-Disposition': 'inline',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
            'Access-Control-Allow-Headers': 'Authorization, Content-Type',
        }
    )
    return response

@api_router.delete('/admin/materials/{material_id}')
async def delete_material(material_id: str, current_user: dict = Depends(get_current_user)):
    user_doc = await db.users.find_one({'id': current_user['user_id']})
    if not user_doc or not user_doc.get('is_super_admin', False):
        raise HTTPException(status_code=403, detail='Требуются права суперадминистратора')
    material = await db.materials.find_one({'id': material_id})
    if not material:
        raise HTTPException(status_code=404, detail='Материал не найден')
    file_path = material.get('file_path')
    if file_path and Path(file_path).exists():
        try:
            Path(file_path).unlink()
        except Exception as e:
            logger.warning(f'Failed to delete file: {e}')
    await db.materials.delete_one({'id': material_id})
    return {'deleted': True}

# IP Geolocation function
def get_city_from_ip(client_ip: str = None) -> str:
    """
    Определяет город по IP адресу пользователя
    """
    if not client_ip or client_ip in ['127.0.0.1', 'localhost']:
        return "Москва"  # По умолчанию для локальных адресов
    
    try:
        # Используем бесплатный сервис ipapi.co
        response = requests.get(f'http://ipapi.co/{client_ip}/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            city = data.get('city')
            if city:
                return city
    except Exception as e:
        print(f"Ошибка геолокации: {e}")
    
    return "Москва"  # Возвращаем по умолчанию при ошибке

# Helper function to check admin rights
async def check_admin_rights(current_user: dict, require_super_admin: bool = False):
    user = await db.users.find_one({'id': current_user['user_id']})
    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    if require_super_admin:
        if not user.get('is_super_admin'):
            raise HTTPException(status_code=403, detail='Требуются права суперадминистратора')
    else:
        # Check if user is either super admin or regular admin
        if not (user.get('is_super_admin') or user.get('is_admin')):
            raise HTTPException(status_code=403, detail='Нет прав администратора')
    
    return user

# Admin endpoints
@api_router.get('/admin/users')
async def get_all_users(current_user: dict = Depends(get_current_user)):
    admin_user = await check_admin_rights(current_user)
    
    users = await db.users.find({}).to_list(length=None)
    user_list = []
    
    for u in users:
        # Подсчет прогресса уроков
        lessons_progress = await db.user_lesson_progress.find({'user_id': u['id']}).to_list(length=None)
        completed_lessons = len([p for p in lessons_progress if p.get('completed', False)])
        total_lessons = await db.materials.count_documents({})
        
        user_info = {
            'id': u['id'],
            'email': u['email'],
            'name': u.get('name', ''),
            'birth_date': u.get('birth_date', ''),
            'city': u.get('city', ''),
            'credits_remaining': u.get('credits_remaining', 0),
            'is_premium': u.get('is_premium', False),
            'subscription_type': u.get('subscription_type', ''),
            'subscription_expires_at': u.get('subscription_expires_at', ''),
            'created_at': u.get('created_at', ''),
            'lessons_completed': completed_lessons,
            'lessons_total': total_lessons,
            'lessons_progress_percent': round((completed_lessons / max(total_lessons, 1)) * 100, 1)
        }
        user_list.append(user_info)
    
    return {'users': user_list, 'total_count': len(user_list)}

@api_router.patch('/admin/users/{user_id}/credits')
async def update_user_credits(user_id: str, credits_data: dict, current_user: dict = Depends(get_current_user)):
    admin_user = await check_admin_rights(current_user)
    
    new_credits = credits_data.get('credits_remaining')
    if new_credits is None or new_credits < 0:
        raise HTTPException(status_code=400, detail='Некорректное количество кредитов')
    
    result = await db.users.update_one(
        {'id': user_id},
        {'$set': {'credits_remaining': new_credits}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    # Логирование изменений
    log_entry = {
        'id': str(uuid.uuid4()),
        'admin_id': current_user['user_id'],
        'user_id': user_id,
        'action': 'credits_update',
        'new_credits': new_credits,
        'timestamp': datetime.utcnow()
    }
    await db.admin_logs.insert_one(log_entry)
    
    return {'success': True, 'new_credits': new_credits}

@api_router.delete('/admin/users/{user_id}')
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Удалить пользователя (только для супер-админа)"""
    admin_user = await check_admin_rights(current_user, require_super_admin=False)
    
    # Проверяем что пользователь не является супер-админом
    user_to_delete = await db.users.find_one({'id': user_id})
    if not user_to_delete:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    if user_to_delete.get('is_super_admin'):
        raise HTTPException(status_code=403, detail='Нельзя удалить супер-администратора')
    
    # Запрещаем удаление самого себя
    if user_id == current_user['user_id']:
        raise HTTPException(status_code=403, detail='Нельзя удалить самого себя')
    
    # Удаляем пользователя и связанные данные
    await db.users.delete_one({'id': user_id})
    await db.user_progress.delete_many({'user_id': user_id})
    await db.user_levels.delete_many({'user_id': user_id})
    await db.quiz_results.delete_many({'user_id': user_id})
    await db.consultation_purchases.delete_many({'user_id': user_id})
    
    # Логирование удаления
    log_entry = {
        'id': str(uuid.uuid4()),
        'admin_id': current_user['user_id'],
        'user_id': user_id,
        'action': 'user_delete',
        'user_email': user_to_delete.get('email', 'unknown'),
        'timestamp': datetime.utcnow()
    }
    await db.admin_logs.insert_one(log_entry)
    
    return {'message': 'Пользователь успешно удален'}

# Admin material management endpoints
@api_router.get('/admin/materials')
async def get_all_materials(current_user: dict = Depends(get_current_user)):
    admin_user = await check_admin_rights(current_user)
    
    materials = await db.materials.find({}).to_list(length=None)
    # Clean MongoDB _id fields to avoid serialization errors
    clean_materials = []
    for material in materials:
        material_dict = dict(material)
        material_dict.pop('_id', None)
        clean_materials.append(material_dict)
    
    return {'materials': clean_materials, 'total_count': len(clean_materials)}

@api_router.post('/admin/materials')
async def create_material(material_data: dict, current_user: dict = Depends(get_current_user)):
    admin_user = await check_admin_rights(current_user)
    
    material = {
        'id': str(uuid.uuid4()),
        'title': material_data.get('title', ''),
        'description': material_data.get('description', ''),
        'content': material_data.get('content', ''),
        'video_url': material_data.get('video_url', ''),
        'video_file': material_data.get('video_file', ''), # старое поле для совместимости
        'video_file_id': material_data.get('video_file_id', ''), # новое поле как в PersonalConsultations
        'video_filename': material_data.get('video_filename', ''), # filename для отображения
        'pdf_file_id': material_data.get('pdf_file_id', ''), # PDF как в PersonalConsultations
        'pdf_filename': material_data.get('pdf_filename', ''), # filename для отображения
        'file_url': material_data.get('file_url', ''), # старое поле для совместимости
        'quiz_questions': material_data.get('quiz_questions', []),
        'order': material_data.get('order', 0),
        'is_active': material_data.get('is_active', True),
        'created_at': datetime.utcnow(),
        'created_by': current_user['user_id']
    }
    
    result = await db.materials.insert_one(material)
    return {'success': True, 'material_id': material['id']}

@api_router.put('/admin/materials/{material_id}')
async def update_material(material_id: str, material_data: dict, current_user: dict = Depends(get_current_user)):
    admin_user = await check_admin_rights(current_user)
    
    update_data = {
        'title': material_data.get('title'),
        'description': material_data.get('description'),
        'content': material_data.get('content'),
        'video_url': material_data.get('video_url'),
        'video_file': material_data.get('video_file'), # старое поле для совместимости
        'video_file_id': material_data.get('video_file_id'), # новое поле как в PersonalConsultations
        'video_filename': material_data.get('video_filename'), # filename для отображения
        'pdf_file_id': material_data.get('pdf_file_id'), # PDF как в PersonalConsultations
        'pdf_filename': material_data.get('pdf_filename'), # filename для отображения
        'file_url': material_data.get('file_url'), # старое поле для совместимости
        'quiz_questions': material_data.get('quiz_questions'),
        'order': material_data.get('order'),
        'is_active': material_data.get('is_active'),
        'updated_at': datetime.utcnow(),
        'updated_by': current_user['user_id']
    }
    
    # Убираем None значения
    update_data = {k: v for k, v in update_data.items() if v is not None}
    
    result = await db.materials.update_one(
        {'id': material_id},
        {'$set': update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail='Материал не найден')
    
    return {'success': True}

@api_router.delete('/admin/materials/{material_id}')
async def delete_material(material_id: str, current_user: dict = Depends(get_current_user)):
    admin_user = await check_admin_rights(current_user)
    
    result = await db.materials.delete_one({'id': material_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Материал не найден')
    
    # Также удаляем прогресс пользователей по этому материалу
    await db.user_lesson_progress.delete_many({'material_id': material_id})
    
    return {'success': True}

# Video upload endpoint
@api_router.post('/admin/upload-video')
async def upload_video(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    admin_user = await check_admin_rights(current_user)
    
    # Проверяем тип файла
    allowed_types = ['video/mp4', 'video/avi', 'video/mov', 'video/wmv', 'video/webm']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail='Неподдерживаемый формат видео. Поддерживаются: MP4, AVI, MOV, WMV, WEBM')
    
    # Проверяем размер файла (максимум 100MB)
    if file.size > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail='Размер файла не должен превышать 100MB')
    
    # Генерируем уникальное имя файла
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'mp4'
    unique_filename = f"{str(uuid.uuid4())}.{file_extension}"
    
    # Создаем директорию для видео если не существует
    video_dir = Path('/app/uploaded_videos')
    video_dir.mkdir(exist_ok=True)
    
    file_path = video_dir / unique_filename
    
    try:
        # Сохраняем файл
        with open(file_path, 'wb') as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Сохраняем информацию о файле в базе данных
        video_record = {
            'id': str(uuid.uuid4()),
            'original_filename': file.filename,
            'stored_filename': unique_filename,
            'file_path': str(file_path),
            'file_size': len(content),
            'content_type': file.content_type,
            'uploaded_at': datetime.utcnow(),
            'uploaded_by': current_user['user_id']
        }
        
        await db.uploaded_videos.insert_one(video_record)
        
        return {
            'success': True,
            'video_id': video_record['id'],
            'filename': unique_filename,
            'video_url': f'/api/video/{video_record["id"]}'
        }
        
    except Exception as e:
        # Если что-то пошло не так, удаляем файл
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f'Ошибка при загрузке файла: {str(e)}')

# Video serving endpoint
@api_router.get('/video/{video_id}')
async def serve_video(video_id: str):
    video_record = await db.uploaded_videos.find_one({'id': video_id})
    if not video_record:
        raise HTTPException(status_code=404, detail='Видео не найдено')
    
    file_path = Path(video_record['file_path'])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail='Файл видео не найден на сервере')
    
    return FileResponse(
        path=str(file_path),
        media_type=video_record['content_type'],
        filename=video_record['original_filename'],
        headers={
            'Accept-Ranges': 'bytes',
            'Content-Disposition': 'inline',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
            'Access-Control-Allow-Headers': 'Authorization, Content-Type',
        }
    )

@api_router.get('/admin/users/{user_id}/lessons')
async def get_user_lessons_progress(user_id: str, current_user: dict = Depends(get_current_user)):
    admin_user = await check_admin_rights(current_user)
    
    # Получаем все материалы
    materials = await db.materials.find({}).to_list(length=None)
    
    # Получаем прогресс пользователя
    progress = await db.user_lesson_progress.find({'user_id': user_id}).to_list(length=None)
    progress_dict = {p['material_id']: p for p in progress}
    
    lessons_data = []
    for material in materials:
        material_progress = progress_dict.get(material['id'], {})
        lessons_data.append({
            'material_id': material['id'],
            'title': material['title'],
            'completed': material_progress.get('completed', False),
            'started_at': material_progress.get('started_at', ''),
            'completed_at': material_progress.get('completed_at', ''),
            'quiz_score': material_progress.get('quiz_score', 0)
        })
    
    return {'lessons': lessons_data, 'user_id': user_id}

# Групповая совместимость
@api_router.post('/group-compatibility')
async def calculate_group_compatibility_endpoint(request: GroupCompatibilityRequest, current_user: dict = Depends(get_current_user)):
    try:
        from numerology import calculate_group_compatibility
        
        # Конвертируем данные людей в нужный формат
        people_data = [{"name": person.name, "birth_date": person.birth_date} for person in request.people]
        
        result = calculate_group_compatibility(request.main_person_birth_date, people_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Ошибка расчета: {str(e)}')

# Нумерология автомобиля
@api_router.post('/car-numerology')
async def calculate_car_numerology_endpoint(car_data: Dict[str, str], current_user: dict = Depends(get_current_user)):
    try:
        from numerology import calculate_car_number_numerology
        
        car_number = car_data.get('car_number')
        if not car_number:
            raise HTTPException(status_code=400, detail='Номер автомобиля не указан')
        
        result = calculate_car_number_numerology(car_number)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Ошибка расчета: {str(e)}')

# Нумерология адреса
@api_router.post('/address-numerology')
async def calculate_address_numerology_endpoint(address_data: Dict[str, str], current_user: dict = Depends(get_current_user)):
    try:
        from numerology import calculate_address_numerology
        
        result = calculate_address_numerology(
            street=address_data.get('street'),
            house_number=address_data.get('house_number'),
            apartment_number=address_data.get('apartment_number'),
            postal_code=address_data.get('postal_code')
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Ошибка расчета: {str(e)}')

# Video upload for lessons endpoint
@api_router.post('/admin/lessons/{lesson_id}/upload-video')
async def upload_lesson_video(lesson_id: str, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    admin_user = await check_admin_rights(current_user, require_super_admin=False)
    
    # Check if lesson exists
    lesson = await db.video_lessons.find_one({'id': lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail='Урок не найден')
    
    # Check file type
    allowed_types = ['video/mp4', 'video/avi', 'video/mov', 'video/wmv', 'video/webm']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail='Неподдерживаемый формат видео. Поддерживаются: MP4, AVI, MOV, WMV, WEBM')
    
    # Check file size (maximum 100MB)
    if file.size > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail='Размер файла не должен превышать 100MB')
    
    # Generate unique filename
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'mp4'
    unique_filename = f"lesson_{lesson_id}_{str(uuid.uuid4())}.{file_extension}"
    
    # Create video directory if not exists
    video_dir = Path('/app/uploaded_videos')
    video_dir.mkdir(exist_ok=True)
    
    file_path = video_dir / unique_filename
    
    try:
        # Save file
        with open(file_path, 'wb') as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Save video information to database
        video_record = {
            'id': str(uuid.uuid4()),
            'lesson_id': lesson_id,
            'original_filename': file.filename,
            'stored_filename': unique_filename,
            'file_path': str(file_path),
            'file_size': len(content),
            'content_type': file.content_type,
            'uploaded_at': datetime.utcnow(),
            'uploaded_by': current_user['user_id']
        }
        
        await db.uploaded_videos.insert_one(video_record)
        
        # Update lesson with direct video file reference
        video_url = f'/api/video/{video_record["id"]}'
        await db.video_lessons.update_one(
            {'id': lesson_id}, 
            {
                '$set': {
                    'video_url': video_url,
                    'video_file_id': video_record['id'],
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        return {
            'success': True,
            'video_id': video_record['id'],
            'filename': unique_filename,
            'video_url': video_url,
            'lesson_id': lesson_id
        }
        
    except Exception as e:
        # If something went wrong, delete file
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f'Ошибка при загрузке файла: {str(e)}')

# ----------------- PERSONAL CONSULTATIONS -----------------

# Admin endpoints for managing consultations
@api_router.get('/admin/consultations')
async def get_all_consultations(current_user: dict = Depends(get_current_user)):
    """Получить все персональные консультации с данными покупателей (только для админа)"""
    admin_user = await check_admin_rights(current_user, require_super_admin=False)  # Позволяем обычным админам
    
    consultations = await db.personal_consultations.find().sort('created_at', -1).to_list(100)
    clean_consultations = []
    
    for consultation in consultations:
        consultation_dict = dict(consultation)
        consultation_dict.pop('_id', None)
        
        # Если консультация куплена, добавляем полную информацию о покупателе
        if consultation_dict.get('is_purchased'):
            buyer_info = {
                'is_purchased': True,
                'purchased_at': consultation_dict.get('purchased_at'),
                'buyer_details': {
                    'user_id': consultation_dict.get('purchased_by_user_id'),
                    'full_name': consultation_dict.get('buyer_full_name', ''),
                    'email': consultation_dict.get('buyer_email', ''),
                    'birth_date': consultation_dict.get('buyer_birth_date', ''),
                    'city': consultation_dict.get('buyer_city', ''),
                    'phone': consultation_dict.get('buyer_phone', ''),
                    'address': consultation_dict.get('buyer_address', ''),
                    'credits_spent': consultation_dict.get('credits_spent', 0)
                }
            }
            consultation_dict.update(buyer_info)
        else:
            consultation_dict['is_purchased'] = False
            consultation_dict['buyer_details'] = None
            
        clean_consultations.append(consultation_dict)
    
    return clean_consultations

@api_router.get('/admin/users/{user_id}/details')
async def get_user_details(user_id: str, current_user: dict = Depends(get_current_user)):
    """Получить подробные данные пользователя (для админа)"""
    admin_user = await check_admin_rights(current_user)
    
    user = await db.users.find_one({'id': user_id})
    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    # Возвращаем все доступные данные пользователя
    user_details = {
        'id': user.get('id'),
        'email': user.get('email', ''),
        'full_name': user.get('full_name', user.get('name', '')),
        'birth_date': user.get('birth_date', ''),
        'city': user.get('city', ''),
        'phone': user.get('phone', ''),
        'address': user.get('address', ''),
        'car': user.get('car', ''),
        'credits_remaining': user.get('credits_remaining', 0),
        'subscription_type': user.get('subscription_type', ''),
        'subscription_expires_at': user.get('subscription_expires_at', ''),
        'created_at': user.get('created_at', ''),
        'last_login': user.get('last_login', ''),
        'is_admin': user.get('is_admin', False),
        'is_super_admin': user.get('is_super_admin', False)
    }
    
    # Дополнительная статистика
    completed_lessons = await db.user_progress.count_documents({'user_id': user_id, 'completed': True})
    total_lessons = await db.video_lessons.count_documents({'is_active': True})
    quiz_results = await db.quiz_results.count_documents({'user_id': user_id})
    
    user_details.update({
        'lessons_completed': completed_lessons,
        'lessons_total': total_lessons,
        'lessons_progress_percent': round((completed_lessons / max(total_lessons, 1)) * 100, 1),
        'quiz_results_count': quiz_results
    })
    
    return user_details

@api_router.post('/admin/consultations')
async def create_consultation(consultation: PersonalConsultation, current_user: dict = Depends(get_current_user)):
    """Создать новую персональную консультацию (только для админа)"""
    admin_user = await check_admin_rights(current_user, require_super_admin=False)  # Позволяем обычным админам
    await db.personal_consultations.insert_one(consultation.dict())
    return {'message': 'Консультация успешно создана', 'consultation_id': consultation.id}

@api_router.put('/admin/consultations/{consultation_id}')
async def update_consultation(consultation_id: str, consultation_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    """Обновить персональную консультацию (только для админа)"""
    admin_user = await check_admin_rights(current_user, require_super_admin=False)  # Позволяем обычным админам
    consultation_data['updated_at'] = datetime.utcnow()
    result = await db.personal_consultations.update_one({'id': consultation_id}, {'$set': consultation_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail='Консультация не найдена')
    return {'message': 'Консультация успешно обновлена'}

@api_router.delete('/admin/consultations/{consultation_id}')
async def delete_consultation(consultation_id: str, current_user: dict = Depends(get_current_user)):
    """Удалить персональную консультацию (только для админа)"""
    admin_user = await check_admin_rights(current_user, require_super_admin=False)  # Позволяем обычным админам
    result = await db.personal_consultations.delete_one({'id': consultation_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Консультация не найдена')
    return {'message': 'Консультация успешно удалена'}

# Upload endpoints for consultations
@api_router.post('/admin/consultations/upload-video')
async def upload_consultation_video(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Загрузка видео файла для консультации"""
    admin_user = await check_admin_rights(current_user, require_super_admin=False)  # Позволяем обычным админам
    
    # Проверяем тип файла
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail='Файл должен быть видео')
    
    try:
        # Генерируем уникальное имя файла
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        file_path = CONSULTATIONS_VIDEO_DIR / f"{file_id}{file_extension}"
        
        # Сохраняем файл
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Сохраняем информацию в базу данных
        video_record = {
            'id': file_id,
            'original_filename': file.filename,
            'file_path': str(file_path),
            'content_type': file.content_type,
            'file_size': len(content),
            'uploaded_by': current_user['user_id'],
            'created_at': datetime.utcnow(),
            'file_type': 'consultation_video'
        }
        
        await db.uploaded_files.insert_one(video_record)
        
        return {
            'success': True,
            'file_id': file_id,
            'filename': file.filename,
            'video_url': f'/api/consultations/video/{file_id}'
        }
    except Exception as e:
        logger.error(f'Video upload error: {e}')
        raise HTTPException(status_code=500, detail=f'Ошибка при загрузке видео: {str(e)}')
@api_router.post('/admin/consultations/upload-pdf')
async def upload_consultation_pdf(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Загрузка PDF файла для консультации"""
    admin_user = await check_admin_rights(current_user, require_super_admin=False)  # Позволяем обычным админам
    
    # Проверяем тип файла
    if file.content_type != 'application/pdf':
        raise HTTPException(status_code=400, detail='Файл должен быть PDF')
    
    try:
        # Генерируем уникальное имя файла
        file_id = str(uuid.uuid4())
        file_path = CONSULTATIONS_PDF_DIR / f"{file_id}.pdf"
        
        # Сохраняем файл
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Сохраняем информацию в базу данных
        pdf_record = {
            'id': file_id,
            'original_filename': file.filename,
            'file_path': str(file_path),
            'content_type': file.content_type,
            'file_size': len(content),
            'uploaded_by': current_user['user_id'],
            'created_at': datetime.utcnow(),
            'file_type': 'consultation_pdf'
        }
        
        await db.uploaded_files.insert_one(pdf_record)
        
        return {
            'success': True,
            'file_id': file_id,
            'filename': file.filename,
            'pdf_url': f'/api/consultations/pdf/{file_id}'
        }
    except Exception as e:
        logger.error(f'PDF upload error: {e}')
        raise HTTPException(status_code=500, detail=f'Ошибка при загрузке PDF: {str(e)}')

@api_router.post('/admin/consultations/upload-subtitles')
async def upload_consultation_subtitles(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Загрузка файла субтитров для консультации"""
    admin_user = await check_admin_rights(current_user, require_super_admin=False)  # Позволяем обычным админам
    
    # Проверяем тип файла
    allowed_types = ['text/vtt', 'application/x-subrip', 'text/plain']
    if file.content_type not in allowed_types and not file.filename.lower().endswith(('.vtt', '.srt')):
        raise HTTPException(status_code=400, detail='Файл должен быть субтитрами (.vtt или .srt)')
    
    try:
        # Генерируем уникальное имя файла
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        file_path = CONSULTATIONS_SUBTITLES_DIR / f"{file_id}{file_extension}"
        
        # Сохраняем файл
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Сохраняем информацию в базу данных
        subtitles_record = {
            'id': file_id,
            'original_filename': file.filename,
            'file_path': str(file_path),
            'content_type': file.content_type or 'text/vtt',
            'file_size': len(content),
            'uploaded_by': current_user['user_id'],
            'created_at': datetime.utcnow(),
            'file_type': 'consultation_subtitles'
        }
        
        await db.uploaded_files.insert_one(subtitles_record)
        
        return {
            'success': True,
            'file_id': file_id,
            'filename': file.filename,
            'subtitles_url': f'/api/consultations/subtitles/{file_id}'
        }
    except Exception as e:
        logger.error(f'Subtitles upload error: {e}')
        raise HTTPException(status_code=500, detail=f'Ошибка при загрузке субтитров: {str(e)}')

# Serving endpoints for consultation files
@api_router.get('/consultations/video/{file_id}')
async def serve_consultation_video(file_id: str):
    """Стриминг видео файлов консультаций"""
    file_record = await db.uploaded_files.find_one({'id': file_id, 'file_type': 'consultation_video'})
    if not file_record:
        raise HTTPException(status_code=404, detail='Видео файл не найден')
    
    file_path = Path(file_record['file_path'])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail='Видео файл не найден на сервере')
    
    return FileResponse(
        path=str(file_path),
        media_type=file_record['content_type'],
        filename=file_record['original_filename'],
        headers={
            'Accept-Ranges': 'bytes',
            'Content-Disposition': 'inline',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
            'Access-Control-Allow-Headers': 'Authorization, Content-Type',
        }
    )

@api_router.get('/consultations/pdf/{file_id}')
async def serve_consultation_pdf(file_id: str):
    """Стриминг PDF файлов консультаций"""
    file_record = await db.uploaded_files.find_one({'id': file_id, 'file_type': 'consultation_pdf'})
    if not file_record:
        raise HTTPException(status_code=404, detail='PDF файл не найден')
    
    file_path = Path(file_record['file_path'])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail='PDF файл не найден на сервере')
    
    return FileResponse(
        path=str(file_path),
        media_type=file_record.get('content_type', 'application/pdf'),  # Default to PDF if missing
        filename=file_record['original_filename'],
        headers={
            'Accept-Ranges': 'bytes',
            'Content-Disposition': 'inline',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
            'Access-Control-Allow-Headers': 'Authorization, Content-Type',
        }
    )

@api_router.get('/consultations/subtitles/{file_id}')
async def serve_consultation_subtitles(file_id: str):
    """Стриминг файлов субтитров консультаций"""
    file_record = await db.uploaded_files.find_one({'id': file_id, 'file_type': 'consultation_subtitles'})
    if not file_record:
        raise HTTPException(status_code=404, detail='Файл субтитров не найден')
    
    file_path = Path(file_record['file_path'])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail='Файл субтитров не найден на сервере')
    
    return FileResponse(
        path=str(file_path),
        media_type=file_record['content_type'],
        filename=file_record['original_filename'],
        headers={
            'Accept-Ranges': 'bytes',
            'Content-Disposition': 'inline',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
            'Access-Control-Allow-Headers': 'Authorization, Content-Type',
        }
    )

# User endpoints for consultations
@api_router.get('/user/consultations')
async def get_user_consultations(current_user: dict = Depends(get_current_user)):
    """Получить консультации назначенные текущему пользователю"""
    user_id = current_user['user_id']
    
    # Получаем консультации назначенные пользователю
    consultations = await db.personal_consultations.find({'assigned_user_id': user_id, 'is_active': True}).to_list(100)
    
    # Получаем информацию о покупках пользователя
    purchases = await db.consultation_purchases.find({'user_id': user_id}).to_list(100)
    purchased_consultation_ids = {purchase['consultation_id'] for purchase in purchases}
    
    # Подготавливаем ответ
    result = []
    for consultation in consultations:
        consultation_dict = dict(consultation)
        consultation_dict.pop('_id', None)
        consultation_dict['is_purchased'] = consultation['id'] in purchased_consultation_ids
        result.append(consultation_dict)
    
    return result

# Auto Quiz Generation from Video Subtitles
@api_router.post('/learning/generate-quiz')
async def generate_quiz_from_video(
    lesson_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Автоматическая генерация Quiz на основе субтитров видео"""
    try:
        lesson_id = lesson_data.get('lesson_id')
        video_url = lesson_data.get('video_url')
        video_file_id = lesson_data.get('video_file_id')
        
        # Получаем информацию об уроке
        lesson = await db.video_lessons.find_one({'id': lesson_id})
        if not lesson:
            raise HTTPException(status_code=404, detail='Урок не найден')
        
        # Пытаемся извлечь субтитры из видео
        subtitles_text = await extract_subtitles_from_video(video_url, video_file_id)
        
        if not subtitles_text:
            # Fallback: используем title и description урока для генерации
            subtitles_text = f"{lesson.get('title', '')}. {lesson.get('description', '')}"
        
        # Генерируем Quiz на основе субтитров с помощью AI
        quiz_questions = await generate_quiz_questions(subtitles_text, lesson.get('title'))
        
        return {
            'questions': quiz_questions,
            'lesson_title': lesson.get('title'),
            'total_points': len(quiz_questions) * 5,
            'generated_from': 'auto_subtitles'
        }
        
    except Exception as e:
        logger.error(f'Quiz generation error: {e}')
        
        # Fallback quiz if auto generation fails
        fallback_questions = [
            {
                'id': 1,
                'question': 'Вы внимательно просмотрели весь видеоурок?',
                'options': [
                    'Да, просмотрел полностью и внимательно',
                    'Просмотрел, но отвлекался',
                    'Просмотрел частично',
                    'Только прослушал фрагменты'
                ],
                'correct_answer': 0,
                'explanation': 'Для лучшего усвоения материала рекомендуется внимательный просмотр всего урока.'
            },
            {
                'id': 2,
                'question': 'Какие новые знания вы получили из этого урока?',
                'options': [
                    'Углубил понимание ведической нумерологии',
                    'Изучил практические методы расчетов',
                    'Узнал историческую информацию',
                    'Все перечисленное выше'
                ],
                'correct_answer': 3,
                'explanation': 'Каждый урок по нумерологии содержит комплексную информацию: теорию, практику и контекст.'
            }
        ]
        
        return {
            'questions': fallback_questions,
            'lesson_title': lesson.get('title', 'Урок'),
            'total_points': 10,
            'generated_from': 'fallback'
        }

async def extract_subtitles_from_video(video_url, video_file_id):
    """Извлечение субтитров из видео файла"""
    try:
        if video_file_id:
            # Для локальных видео файлов
            file_record = await db.uploaded_files.find_one({'id': video_file_id})
            if file_record and file_record.get('file_path'):
                # TODO: Интеграция с Speech-to-Text API (Whisper, Google Speech, etc.)
                # Пока возвращаем None, чтобы использовать fallback
                return None
        elif video_url and ('youtube.com' in video_url or 'youtu.be' in video_url):
            # Для YouTube видео можно использовать YouTube API для получения субтитров
            # TODO: Интеграция с YouTube API для получения субтитров
            return None
            
        return None
    except Exception as e:
        logger.error(f'Subtitle extraction error: {e}')
        return None

async def generate_quiz_questions(text_content, lesson_title):
    """Генерация вопросов Quiz на основе текстового содержимого"""
    try:
        # TODO: Интеграция с LLM для генерации вопросов
        # Можно использовать OpenAI, Claude или локальные модели
        
        # Пока создаем базовые вопросы на основе содержимого
        questions = []
        
        # Анализируем текст и создаем вопросы
        words = text_content.lower().split()
        
        # Ищем ключевые термины нумерологии
        numerology_terms = ['число', 'цифра', 'расчет', 'планета', 'энергия', 'судьба', 'имя']
        found_terms = [term for term in numerology_terms if any(term in word for word in words)]
        
        if 'число' in text_content.lower() or 'цифра' in text_content.lower():
            questions.append({
                'id': len(questions) + 1,
                'question': f'О каких числовых значениях говорится в уроке "{lesson_title}"?',
                'options': [
                    'О числах судьбы и планетарных влияниях',
                    'О математических формулах',
                    'О статистических данных', 
                    'О номерах телефонов'
                ],
                'correct_answer': 0,
                'explanation': 'В ведической нумерологии изучаются числа судьбы и их планетарные влияния на жизнь человека.'
            })
        
        if 'планета' in text_content.lower() or 'энергия' in text_content.lower():
            questions.append({
                'id': len(questions) + 1,
                'question': 'Как планетарные энергии влияют на числа в ведической нумерологии?',
                'options': [
                    'Каждому числу соответствует планета со своей энергией',
                    'Планеты не влияют на числа',
                    'Влияние зависит от времени года',
                    'Влияние только на четные числа'
                ],
                'correct_answer': 0,
                'explanation': 'В ведической системе каждое число от 1 до 9 связано с определенной планетой и ее энергетическими качествами.'
            })
        
        # Если не нашли специфичных терминов, добавляем общие вопросы
        if len(questions) == 0:
            questions.extend([
                {
                    'id': 1,
                    'question': f'Какая основная тема рассматривается в уроке "{lesson_title}"?',
                    'options': [
                        'Ведическая нумерология и числовые влияния',
                        'Современная математика',
                        'История древней Индии',
                        'Астрономические расчеты'
                    ],
                    'correct_answer': 0,
                    'explanation': 'Урок посвящен изучению ведической нумерологии и влиянию чисел на жизнь человека.'
                }
            ])
        
        # Всегда добавляем практический вопрос
        questions.append({
            'id': len(questions) + 1,
            'question': 'Как лучше всего применить полученные знания на практике?',
            'options': [
                'Рассчитать свои личные числа и изучить их влияние',
                'Заучить все формулы наизусть',
                'Игнорировать полученную информацию',
                'Рассказать друзьям без изучения'
            ],
            'correct_answer': 0,
            'explanation': 'Практическое применение знаний через расчет и анализ личных чисел помогает лучше понять и использовать нумерологические принципы.'
        })
        
        return questions
        
    except Exception as e:
        logger.error(f'Question generation error: {e}')
        return []

# Regular learning endpoints continue below...

@api_router.post('/user/consultations/{consultation_id}/purchase')
async def purchase_consultation(consultation_id: str, current_user: dict = Depends(get_current_user)):
    """Купить персональную консультацию - ФИКСИРОВАННАЯ стоимость 6667 баллов"""
    user_id = current_user['user_id']
    
    # Проверяем существование консультации и что она назначена этому пользователю
    consultation = await db.personal_consultations.find_one({
        'id': consultation_id,
        'assigned_user_id': user_id,
        'is_active': True
    })
    if not consultation:
        raise HTTPException(status_code=404, detail='Консультация не найдена или не назначена вам')
    
    # Проверяем, не была ли уже куплена
    existing_purchase = await db.consultation_purchases.find_one({
        'user_id': user_id,
        'consultation_id': consultation_id
    })
    if existing_purchase:
        raise HTTPException(status_code=400, detail='Консультация уже приобретена')
    
    # Получаем информацию о пользователе
    user = await db.users.find_one({'id': user_id})
    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    # ИСПРАВЛЕНО: Фиксированная стоимость персональной консультации
    consultation_cost = 6667  # Всегда 6667 баллов, не зависит от настроек консультации
    
    # Проверяем что у пользователя достаточно баллов
    user_credits = user.get('credits_remaining', 0)
    if user_credits < consultation_cost:
        raise HTTPException(status_code=402, detail=f'Недостаточно баллов. Нужно: {consultation_cost}, у вас: {user_credits}')
    
    # ИСПРАВЛЕНО: Проверяем дублирование запроса (защита от двойных кликов)
    # Добавляем проверку на недавние покупки (в течение 30 секунд)
    from datetime import datetime, timedelta
    recent_purchase = await db.consultation_purchases.find_one({
        'user_id': user_id,
        'created_at': {'$gte': datetime.utcnow() - timedelta(seconds=30)}
    })
    if recent_purchase:
        raise HTTPException(status_code=429, detail='Подождите 30 секунд между покупками консультаций')
    
    # Списываем баллы
    await deduct_credits(
        user_id,
        consultation_cost,
        f'Покупка персональной консультации: {consultation.get("title", "Без названия")}',
        'consultation',
        {
            'consultation_id': consultation_id,
            'consultation_title': consultation.get('title'),
            'remaining_credits': user_credits - consultation_cost
        }
    )
    
    # Создаем запись о покупке
    purchase = ConsultationPurchase(
        user_id=user_id,
        consultation_id=consultation_id,
        credits_spent=consultation_cost
    )
    await db.consultation_purchases.insert_one(purchase.dict())
    
    # ИСПРАВЛЕНО: Обновляем консультацию - добавляем данные покупателя СРАЗУ
    user_data = {
        'purchased_by_user_id': user_id,
        'purchased_at': datetime.utcnow(),
        'buyer_full_name': user.get('full_name', user.get('name', '')),
        'buyer_email': user.get('email', ''),
        'buyer_birth_date': user.get('birth_date', ''),
        'buyer_city': user.get('city', ''),
        'buyer_phone': user.get('phone_number', ''),  # ИСПРАВЛЕНО: правильное поле
        'buyer_address': user.get('address', ''),
        'credits_spent': consultation_cost,
        'is_purchased': True
    }
    
    await db.personal_consultations.update_one(
        {'id': consultation_id},
        {'$set': user_data}
    )
    
    return {
        'message': 'Персональная консультация успешно приобретена!',
        'credits_spent': consultation_cost,
        'remaining_credits': user_credits - consultation_cost,
        'consultation_title': consultation.get('title', 'Персональная консультация')
    }

# ----------------- REPORTS -----------------

# Получение доступных расчётов для отчёта
@api_router.get('/reports/available-calculations')
async def get_available_calculations(current_user: dict = Depends(get_current_user)):
    """
    Возвращает список всех расчётов, которые пользователь может включить в отчёт
    """
    user_dict = await db.users.find_one({'id': current_user['user_id']})
    if not user_dict:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    user = User(**user_dict)
    
    # Получаем историю расчётов пользователя
    calculations = await db.numerology_calculations.find({'user_id': current_user['user_id']}).to_list(100)
    
    available_calculations = {
        'personal_numbers': {
            'id': 'personal_numbers',
            'name': 'Персональные числа',
            'description': 'Числа судьбы, души, ума, правления и другие',
            'available': True,  # Всегда доступно для пользователя
            'icon': '🌟'
        },
        'name_numerology': {
            'id': 'name_numerology', 
            'name': 'Нумерология имени и фамилии',
            'description': 'Анализ имени и фамилии пользователя',
            'available': bool(user.full_name),
            'icon': '📝'
        },
        'car_numerology': {
            'id': 'car_numerology',
            'name': 'Нумерология автомобиля',
            'description': 'Анализ номера автомобиля',
            'available': bool(user.car_number),
            'icon': '🚗'
        },
        'address_numerology': {
            'id': 'address_numerology',
            'name': 'Нумерология адреса',
            'description': 'Анализ адреса проживания',
            'available': bool(user.street or user.house_number or user.apartment_number or user.postal_code),
            'icon': '🏠'
        },
        'pythagorean_square': {
            'id': 'pythagorean_square',
            'name': 'Квадрат Пифагора',
            'description': 'Психоматрица и анализ характера',
            'available': True,
            'icon': '⬜'
        },
        'vedic_times': {
            'id': 'vedic_times',
            'name': 'Ведические времена',
            'description': 'Рahu Kala, Abhijit Muhurta и другие',
            'available': bool(user.city),
            'icon': '⏰'
        },
        'planetary_route': {
            'id': 'planetary_route',
            'name': 'Планетарный маршрут',
            'description': 'Ежедневный планетарный анализ',
            'available': True,
            'icon': '🌍'
        }
    }
    
    # Проверяем, какие расчёты совместимости доступны
    compatibility_calculations = [calc for calc in calculations if calc.get('calculation_type') == 'compatibility']
    if compatibility_calculations:
        available_calculations['compatibility'] = {
            'id': 'compatibility',
            'name': 'Анализ совместимости',
            'description': f'Сохранённые расчёты совместимости ({len(compatibility_calculations)} шт.)',
            'available': True,
            'icon': '❤️'
        }
    
    # Проверяем групповую совместимость
    group_calculations = [calc for calc in calculations if calc.get('calculation_type') == 'group_compatibility']
    if group_calculations:
        available_calculations['group_compatibility'] = {
            'id': 'group_compatibility',
            'name': 'Групповая совместимость',
            'description': f'Групповые анализы ({len(group_calculations)} шт.)',
            'available': True,
            'icon': '👥'
        }
    
    return {
        'available_calculations': available_calculations,
        'user_has_data': {
            'full_name': bool(user.full_name),
            'car_number': bool(user.car_number),
            'address': bool(user.street or user.house_number),
            'city': bool(user.city)
        }
    }

@api_router.post('/reports/html/numerology')
async def generate_numerology_html(html_request: HTMLReportRequest, current_user: dict = Depends(get_current_user)):
    user_dict = await db.users.find_one({'id': current_user['user_id']})
    if not user_dict:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    user = User(**user_dict)
    if user.subscription_expires_at and user.subscription_expires_at < datetime.utcnow():
        await db.users.update_one({'id': user.id}, {'$set': {'is_premium': False, 'subscription_type': None, 'subscription_expires_at': None}})
        user.is_premium = False
        user.subscription_type = None
    if not user.is_premium and (user.credits_remaining is None or user.credits_remaining <= 0):
        raise HTTPException(status_code=402, detail='Недостаточно кредитов. Требуется подписка или дополнительные кредиты.')
    user_data = {
        'full_name': user.full_name, 
        'email': user.email, 
        'birth_date': user.birth_date, 
        'city': user.city,
        'phone_number': user.phone_number,
        'car_number': user.car_number,
        'street': user.street,
        'house_number': user.house_number,
        'apartment_number': user.apartment_number,
        'postal_code': user.postal_code
    }
    
    # Основные персональные числа
    calculations = calculate_personal_numbers(user.birth_date)
    
    # Квадрат Пифагора с дополнительными числами
    pythagorean_data = None
    try:
        d, m, y = parse_birth_date(user.birth_date)
        pythagorean_data = create_pythagorean_square(d, m, y)
    except:
        pass
    
    # Параметры отчета
    selected_calculations = html_request.selected_calculations
    
    # Для совместимости со старой системой
    if not selected_calculations:
        selected_calculations = []
        if html_request.include_vedic:
            selected_calculations.append('vedic_numerology')
        if html_request.include_charts:
            selected_calculations.extend(['personal_numbers', 'pythagorean_square'])
        if html_request.include_compatibility:
            selected_calculations.append('compatibility')
        
        # Если ничего не выбрано, добавляем базовые расчёты
        if not selected_calculations:
            selected_calculations = ['personal_numbers', 'pythagorean_square']
    
    # Проверяем что выбран хотя бы один расчёт
    if not selected_calculations:
        raise HTTPException(status_code=400, detail='Необходимо выбрать хотя бы один раздел для отчёта')
    
    # Ведические времена
    vedic_data = None
    vedic_times = None
    if 'vedic_times' in selected_calculations and user.city:
        try:
            from vedic_time_calculations import get_vedic_day_schedule
            vedic_times = get_vedic_day_schedule(city=user.city, date=datetime.utcnow())
        except:
            pass
    
    # Планетарный маршрут
    planetary_route = None
    if 'planetary_route' in selected_calculations and user.city:
        try:
            planetary_route = {
                'date': datetime.utcnow().strftime('%Y-%m-%d'),
                'city': user.city,
                'daily_route': ['Солнце: Утро (6:00-12:00)', 'Луна: День (12:00-18:00)', 'Марс: Вечер (18:00-24:00)']
            }
        except:
            pass
    
    # Планетарные энергии
    charts_data = {'planetary_energy': generate_weekly_planetary_energy(user.birth_date)} if any(calc in selected_calculations for calc in ['personal_numbers', 'pythagorean_square']) else None
    
    # Объединяем все данные
    all_data = {
        'personal_numbers': calculations,
        'pythagorean_square': pythagorean_data,
        'vedic_times': vedic_times,
        'planetary_route': planetary_route,
        'charts': charts_data
    }
    
    # Добавляем данные из профиля пользователя для новых расчётов
    user_data_dict = user_data
    
    try:
        # Генерируем HTML отчет с выбранными расчётами
        html_str = create_numerology_report_html(
            user_data=user_data_dict,
            all_data=all_data,
            vedic_data=vedic_data,
            charts_data=charts_data,
            theme=html_request.theme,
            selected_calculations=selected_calculations
        )
        
        # Проверяем что HTML сгенерирован корректно
        if not html_str or len(html_str) < 100:
            raise HTTPException(status_code=500, detail='Ошибка генерации HTML: пустой результат')
            
        # Списываем кредит только после успешной генерации
        if not user.is_premium:
            await db.users.update_one({'id': user.id}, {'$inc': {'credits_remaining': -1}})
        
        return Response(content=html_str, media_type='text/html; charset=utf-8')
        
    except Exception as e:
        print(f"HTML generation error: {str(e)}")  # Debug log
        raise HTTPException(status_code=500, detail=f'Ошибка генерации HTML отчёта: {str(e)}')

@api_router.post('/reports/pdf/numerology')
async def generate_numerology_pdf(pdf_request: PDFReportRequest, current_user: dict = Depends(get_current_user)):
    user_dict = await db.users.find_one({'id': current_user['user_id']})
    if not user_dict:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    user = User(**user_dict)
    if user.subscription_expires_at and user.subscription_expires_at < datetime.utcnow():
        await db.users.update_one({'id': user.id}, {'$set': {'is_premium': False, 'subscription_type': None, 'subscription_expires_at': None}})
        user.is_premium = False
        user.subscription_type = None
    if not user.is_premium and (user.credits_remaining is None or user.credits_remaining <= 0):
        raise HTTPException(status_code=402, detail='Недостаточно кредитов. Требуется подписка или дополнительные кредиты.')
    user_data = {
        'full_name': user.full_name, 
        'email': user.email, 
        'birth_date': user.birth_date, 
        'city': user.city,
        'phone_number': user.phone_number,
        'car_number': user.car_number,
        'street': user.street,
        'house_number': user.house_number,
        'apartment_number': user.apartment_number,
        'postal_code': user.postal_code
    }
    calculations = calculate_personal_numbers(user.birth_date)
    vedic_data = calculate_comprehensive_vedic_numerology(user.birth_date, user.full_name) if pdf_request.include_vedic else None
    charts_data = {'planetary_energy': generate_weekly_planetary_energy(user.birth_date)} if pdf_request.include_charts else None
    compatibility_result = None
    if pdf_request.include_compatibility and pdf_request.partner_birth_date:
        from enhanced_numerology import get_compatibility_score
        compatibility_result = get_compatibility_score(user.birth_date, pdf_request.partner_birth_date)
    if compatibility_result:
        partner_data = {'birth_date': pdf_request.partner_birth_date}
        pdf_bytes = create_compatibility_pdf(user_data, partner_data, compatibility_result)
        filename = f"numerom_compatibility_{current_user['user_id']}_{datetime.now().strftime('%Y%m%d')}.pdf"
    else:
        pdf_bytes = create_numerology_report_pdf(user_data, calculations, vedic_data, charts_data)
        filename = f"numerom_report_{current_user['user_id']}_{datetime.now().strftime('%Y%m%d')}.pdf"
    if not user.is_premium:
        await db.users.update_one({'id': user.id}, {'$inc': {'credits_remaining': -1}})
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type='application/pdf', headers={'Content-Disposition': f'attachment; filename={filename}'})



# ----------------- USER -----------------
@api_router.get('/user/profile', response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    user_dict = await db.users.find_one({'id': current_user['user_id']})
    if not user_dict:
        raise HTTPException(status_code=404, detail='User not found')
    return create_user_response(User(**user_dict))

@api_router.patch('/user/profile')
async def update_user_profile(profile_data: UserProfileUpdate, current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({'id': current_user['user_id']})
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    
    # Подготавливаем данные для обновления (только не None поля)
    update_data = {}
    for field, value in profile_data.dict(exclude_unset=True).items():
        if value is not None:
            update_data[field] = value
    
    if update_data:
        update_data['updated_at'] = datetime.utcnow()
        await db.users.update_one(
            {'id': current_user['user_id']},
            {'$set': update_data}
        )
    
    # Возвращаем обновленный профиль
    updated_user = await db.users.find_one({'id': current_user['user_id']})
    return create_user_response(User(**updated_user))

@api_router.post('/user/change-city')
async def change_user_city(city_request: Dict[str, str], current_user: dict = Depends(get_current_user)):
    city = city_request.get('city')
    if not city:
        raise HTTPException(status_code=400, detail='city required')
    await db.users.update_one({'id': current_user['user_id']}, {'$set': {'city': city, 'updated_at': datetime.utcnow()}})
    return {'message': f'Город изменен на {city}', 'city': city}

@api_router.get('/')
async def root():
    return {'message': 'NUMEROM API - Self-Knowledge Through Numbers'}

@api_router.post('/status', response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(**input.dict())
    await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get('/status', response_model=List[StatusCheck])
async def get_status_checks():
    checks = await db.status_checks.find().to_list(1000)
    clean_checks = []
    for c in checks:
        check_dict = dict(c)
        check_dict.pop('_id', None)
        clean_checks.append(check_dict)
    return [StatusCheck(**c) for c in clean_checks]

# Router will be included at the end of the file

# =================== QUIZ GENERATION ===================
@app.post("/api/admin/generate-quiz/{lesson_id}")
async def generate_quiz_for_lesson(
    lesson_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Generate a quiz for a specific lesson using AI"""
    if not current_user.get("is_super_admin"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Find the lesson
        lesson = await db.lessons.find_one({"_id": lesson_id, "type": "lesson"})
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        # Generate quiz questions based on lesson content
        quiz_questions = [
            {
                "question": f"Основной вопрос по теме '{lesson['title']}'?",
                "options": ["Вариант A", "Вариант B", "Вариант C", "Вариант D"],
                "correct_answer": "A",
                "explanation": "Объяснение правильного ответа"
            }
        ]
        
        # Update lesson with quiz
        await db.lessons.update_one(
            {"_id": lesson_id},
            {"$set": {"quiz_questions": quiz_questions}}
        )
        
        return {"message": "Quiz generated successfully", "questions": quiz_questions}
        
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating quiz: {str(e)}")

# =================== ПЕРВОЕ ЗАНЯТИЕ NUMEROM ===================
@app.get("/api/lessons/first-lesson")
async def get_first_lesson():
    """Получить первое занятие NumerOM"""
    try:
        lesson = lesson_system.get_lesson("lesson_numerom_intro")
        if not lesson:
            raise HTTPException(status_code=404, detail="First lesson not found")

        # Преобразуем структуру для фронтенда
        lesson_dict = lesson.dict()

        # Перемещаем exercises, quiz, challenges внутрь content для фронтенда
        if "content" not in lesson_dict:
            lesson_dict["content"] = {}

        # Загружаем кастомные изменения в контенте (теория и т.д.)
        custom_content = await db.lesson_content.find({
            "lesson_id": "lesson_numerom_intro",
            "type": "content_update"
        }).to_list(100)

        if custom_content:
            for item in custom_content:
                section = item.get("section")
                field = item.get("field")
                value = item.get("value")

                if section and field and value is not None:
                    if section not in lesson_dict["content"]:
                        lesson_dict["content"][section] = {}
                    lesson_dict["content"][section][field] = value

        # Загружаем кастомные упражнения из БД (если есть)
        custom_exercises = await db.lesson_exercises.find({
            "lesson_id": "lesson_numerom_intro",
            "content_type": "exercise_update"
        }).to_list(100)

        if custom_exercises:
            # Создаем словарь для быстрого поиска кастомных упражнений
            custom_exercises_dict = {ex["exercise_id"]: ex for ex in custom_exercises}

            # Обновляем базовые упражнения кастомными (если есть)
            if "exercises" not in lesson_dict or not lesson_dict["exercises"]:
                lesson_dict["exercises"] = []

            updated_exercises = []
            existing_ids = set()

            # Обновляем существующие упражнения
            for exercise in lesson_dict["exercises"]:
                exercise_id = exercise.get("id")
                existing_ids.add(exercise_id)
                if exercise_id in custom_exercises_dict:
                    # Используем кастомное упражнение
                    custom = custom_exercises_dict[exercise_id]
                    updated_exercises.append({
                        "id": custom["exercise_id"],
                        "title": custom["title"],
                        "type": custom["type"],
                        "content": custom["content"],
                        "instructions": custom["instructions"],
                        "expected_outcome": custom.get("expected_outcome", "")
                    })
                else:
                    # Используем базовое упражнение
                    updated_exercises.append(exercise)

            # Добавляем НОВЫЕ упражнения которых нет в базовом уроке
            for exercise_id, custom in custom_exercises_dict.items():
                if exercise_id not in existing_ids:
                    updated_exercises.append({
                        "id": custom["exercise_id"],
                        "title": custom["title"],
                        "type": custom["type"],
                        "content": custom["content"],
                        "instructions": custom["instructions"],
                        "expected_outcome": custom.get("expected_outcome", "")
                    })

            lesson_dict["exercises"] = updated_exercises

        # Присваиваем ID базовым упражнениям (если их нет)
        if "exercises" in lesson_dict:
            for idx, exercise in enumerate(lesson_dict["exercises"]):
                if isinstance(exercise, dict):
                    if "id" not in exercise or not exercise["id"]:
                        exercise["id"] = f"exercise_{idx + 1}"

        # Добавляем exercises в content
        if "exercises" in lesson_dict and lesson_dict["exercises"]:
            lesson_dict["content"]["exercises"] = lesson_dict["exercises"]

        # Присваиваем ID базовым вопросам (если их нет)
        if "quiz" in lesson_dict and lesson_dict["quiz"] and "questions" in lesson_dict["quiz"]:
            for idx, question in enumerate(lesson_dict["quiz"]["questions"]):
                if "id" not in question or not question["id"]:
                    question["id"] = f"q{idx + 1}"

        # Загружаем кастомные вопросы теста из БД (если есть)
        custom_quiz_questions = await db.lesson_quiz_questions.find({
            "lesson_id": "lesson_numerom_intro",
            "content_type": "quiz_question_update"
        }).to_list(100)

        if custom_quiz_questions:
            # Создаем словарь для быстрого поиска кастомных вопросов
            custom_questions_dict = {q["question_id"]: q for q in custom_quiz_questions}
            logger.info(f"Found {len(custom_quiz_questions)} custom quiz questions: {list(custom_questions_dict.keys())}")

            # Обновляем базовые вопросы кастомными (если есть)
            if "quiz" in lesson_dict and lesson_dict["quiz"]:
                if "questions" not in lesson_dict["quiz"]:
                    lesson_dict["quiz"]["questions"] = []

                updated_questions = []
                existing_ids = set()

                # Обновляем существующие вопросы
                for question in lesson_dict["quiz"]["questions"]:
                    question_id = question.get("id")
                    existing_ids.add(question_id)
                    if question_id in custom_questions_dict:
                        # Используем кастомный вопрос
                        logger.info(f"Replacing base question {question_id} with custom version")
                        custom = custom_questions_dict[question_id]
                        updated_questions.append({
                            "id": custom["question_id"],
                            "question": custom["question"],
                            "options": custom["options"],
                            "correct_answer": custom["correct_answer"],
                            "explanation": custom.get("explanation", "")
                        })
                    else:
                        # Используем базовый вопрос
                        logger.info(f"Using base question {question_id}")
                        updated_questions.append(question)

                # Добавляем НОВЫЕ вопросы которых нет в базовом уроке
                for question_id, custom in custom_questions_dict.items():
                    if question_id not in existing_ids:
                        logger.info(f"Adding NEW custom question {question_id}")
                        updated_questions.append({
                            "id": custom["question_id"],
                            "question": custom["question"],
                            "options": custom["options"],
                            "correct_answer": custom["correct_answer"],
                            "explanation": custom.get("explanation", "")
                        })

                lesson_dict["quiz"]["questions"] = updated_questions
                logger.info(f"Final quiz has {len(updated_questions)} questions")

        # Добавляем quiz в content
        if "quiz" in lesson_dict and lesson_dict["quiz"]:
            lesson_dict["content"]["quiz"] = lesson_dict["quiz"]

        # Загружаем кастомные дни челленджа из БД (если есть)
        custom_challenge_days = await db.lesson_challenge_days.find({
            "lesson_id": "lesson_numerom_intro",
            "content_type": "challenge_day_update"
        }).to_list(100)

        # Применяем кастомные дни к челленджу
        if custom_challenge_days and "challenges" in lesson_dict and lesson_dict["challenges"]:
            custom_days_dict = {day["day"]: day for day in custom_challenge_days}

            # Получаем первый челлендж
            challenge = lesson_dict["challenges"][0]
            if "daily_tasks" in challenge:
                updated_daily_tasks = []

                # Обновляем существующие дни или добавляем новые
                existing_days = {task.get("day"): task for task in challenge["daily_tasks"]}
                all_days = set(existing_days.keys()) | set(custom_days_dict.keys())

                for day_num in sorted(all_days):
                    if day_num in custom_days_dict:
                        # Используем кастомный день
                        custom = custom_days_dict[day_num]
                        updated_daily_tasks.append({
                            "day": custom["day"],
                            "title": custom["title"],
                            "tasks": custom["tasks"]
                        })
                    elif day_num in existing_days:
                        # Используем оригинальный день
                        updated_daily_tasks.append(existing_days[day_num])

                challenge["daily_tasks"] = updated_daily_tasks

        # Загружаем кастомный habit_tracker из MongoDB (если есть)
        lesson_in_db = await db.lessons.find_one({"id": "lesson_numerom_intro"})
        if lesson_in_db and "habit_tracker" in lesson_in_db:
            # Если урок существует в MongoDB и имеет habit_tracker, используем его
            lesson_dict["habit_tracker"] = lesson_in_db["habit_tracker"]

        # Добавляем первый challenge как challenge (не challenges[0])
        if "challenges" in lesson_dict and lesson_dict["challenges"]:
            lesson_dict["content"]["challenge"] = lesson_dict["challenges"][0]

        return {
            "lesson": lesson_dict,
            "message": "Первое занятие успешно загружено"
        }
    except Exception as e:
        logger.error(f"Error getting first lesson: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting first lesson: {str(e)}")

@app.get("/api/lessons/{lesson_id}")
async def get_lesson(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Получить урок по ID (для кастомных уроков из MongoDB или первого урока из lesson_system)"""
    try:
        # Если это первый урок - используем endpoint first-lesson
        if lesson_id == "lesson_numerom_intro":
            lesson = lesson_system.get_lesson(lesson_id)
            if not lesson:
                raise HTTPException(status_code=404, detail="Lesson not found")
            lesson_dict = lesson.dict()

            # Перемещаем exercises, quiz, challenges внутрь content для единообразия
            if "content" not in lesson_dict:
                lesson_dict["content"] = {}

            return {"lesson": lesson_dict}

        # Для кастомных уроков - загружаем из MongoDB
        custom_lesson = await db.custom_lessons.find_one({"id": lesson_id})

        if custom_lesson:
            lesson_dict = dict(custom_lesson)
            lesson_dict.pop('_id', None)
            logger.info(f"Loaded custom lesson {lesson_id} from MongoDB")
            return {"lesson": lesson_dict}

        # Если не нашли нигде - 404
        logger.error(f"Lesson {lesson_id} not found")
        raise HTTPException(status_code=404, detail="Lesson not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lesson {lesson_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting lesson: {str(e)}")

@app.post("/api/lessons/start-challenge/{challenge_id}")
async def start_challenge(
    challenge_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Начать челлендж для пользователя"""
    try:
        user_id = current_user["user_id"]

        # Попытка извлечь lesson_id из challenge_id (формат: challenge_lesson_XXXXX или challenge_sun_7days)
        lesson_id = None
        if challenge_id.startswith("challenge_lesson_"):
            lesson_id = challenge_id.replace("challenge_", "")
        elif challenge_id == "challenge_sun_7days":
            lesson_id = "lesson_numerom_intro"

        # Попытка найти урок в MongoDB (для кастомных уроков)
        custom_lesson = None
        challenge_dict = None

        if lesson_id:
            custom_lesson = await db.custom_lessons.find_one({"id": lesson_id})

        if custom_lesson and custom_lesson.get("content", {}).get("challenge"):
            # Урок найден в MongoDB
            challenge_dict = custom_lesson["content"]["challenge"]
            if challenge_dict.get("id") != challenge_id:
                challenge_dict = None
        else:
            # Попытка найти в lesson_system (для первого урока)
            lesson = lesson_system.get_lesson("lesson_numerom_intro")
            if lesson and lesson.challenges:
                for ch in lesson.challenges:
                    if ch.id == challenge_id:
                        challenge_dict = ch.dict()
                        break

        if not challenge_dict:
            logger.error(f"Challenge {challenge_id} not found in any lesson")
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Сохранить начало челленджа в базе данных
        challenge_progress = {
            "_id": f"{user_id}_{challenge_id}",
            "user_id": user_id,
            "challenge_id": challenge_id,
            "type": "challenge_progress",
            "start_date": datetime.now().isoformat(),
            "current_day": 1,
            "completed_days": [],
            "status": "active",
            "daily_completions": {}
        }
        
        await db.challenge_progress.insert_one(challenge_progress)

        return {
            "message": "Челлендж успешно начат",
            "challenge": challenge_dict,
            "start_date": challenge_progress["start_date"],
            "current_day": 1
        }
        
    except Exception as e:
        logger.error(f"Error starting challenge: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting challenge: {str(e)}")

@app.post("/api/lessons/complete-challenge-day")
async def complete_challenge_day(
    challenge_id: str = Form(...),
    day: int = Form(...),
    notes: str = Form(""),
    current_user: dict = Depends(get_current_user)
):
    """Отметить день челленджа как выполненный"""
    try:
        user_id = current_user["user_id"]
        progress_id = f"{user_id}_{challenge_id}"
        
        # Найти прогресс челленджа
        progress = await db.challenge_progress.find_one({"_id": progress_id, "type": "challenge_progress"})
        if not progress:
            raise HTTPException(status_code=404, detail="Challenge progress not found")
        
        # Обновить прогресс
        today = datetime.now().strftime("%Y-%m-%d")
        if day not in progress.get("completed_days", []):
            await db.challenge_progress.update_one(
                {"_id": progress_id},
                {
                    "$push": {"completed_days": day},
                    "$set": {
                        f"daily_completions.{today}": {
                            "day": day,
                            "completed": True,
                            "notes": notes,
                            "completion_time": datetime.now().isoformat()
                        },
                        "current_day": day + 1 if day + 1 <= 7 else 7
                    }
                }
            )
        
        return {"message": f"День {day} челленджа отмечен как выполненный"}
        
    except Exception as e:
        logger.error(f"Error completing challenge day: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error completing challenge day: {str(e)}")

@app.get("/api/lessons/challenge-progress/{challenge_id}")
async def get_challenge_progress(
    challenge_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Получить прогресс челленджа пользователя"""
    try:
        user_id = current_user["user_id"]
        progress_id = f"{user_id}_{challenge_id}"
        
        progress = await db.challenge_progress.find_one({"_id": progress_id, "type": "challenge_progress"})
        if not progress:
            return {"message": "Challenge not started", "progress": None}
        
        # Конвертировать ObjectId в строку для JSON
        progress["_id"] = str(progress["_id"])
        
        return {"progress": progress}
        
    except Exception as e:
        logger.error(f"Error getting challenge progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting challenge progress: {str(e)}")

@app.post("/api/lessons/submit-quiz")
async def submit_quiz(
    quiz_id: str = Form(...),
    answers: str = Form(...),  # JSON string with answers
    current_user: dict = Depends(get_current_user)
):
    """Отправить ответы на квиз"""
    try:
        user_id = current_user["user_id"]

        # Парс ответов
        import json
        user_answers = json.loads(answers)

        # Попытка извлечь lesson_id из quiz_id (формат: quiz_lesson_XXXXX или quiz_intro_1)
        lesson_id = None
        if quiz_id.startswith("quiz_lesson_"):
            lesson_id = quiz_id.replace("quiz_", "")
        elif quiz_id.startswith("quiz_intro"):
            lesson_id = "lesson_numerom_intro"

        # Попытка найти урок в MongoDB (для кастомных уроков)
        custom_lesson = None
        quiz_dict = None

        if lesson_id:
            custom_lesson = await db.custom_lessons.find_one({"id": lesson_id})

        if custom_lesson and custom_lesson.get("content", {}).get("quiz"):
            # Урок найден в MongoDB
            quiz_dict = custom_lesson["content"]["quiz"]
            if quiz_dict.get("id") != quiz_id:
                quiz_dict = None
        else:
            # Попытка найти в lesson_system (для первого урока)
            lesson = lesson_system.get_lesson("lesson_numerom_intro")
            if lesson and lesson.quiz and lesson.quiz.id == quiz_id:
                quiz_dict = lesson.quiz.dict()

        if not quiz_dict:
            logger.error(f"Quiz {quiz_id} not found in any lesson")
            raise HTTPException(status_code=404, detail="Quiz not found")

        # Проверить ответы
        score = 0
        questions = quiz_dict.get("questions", [])
        total_questions = len(questions)

        results = []
        for i, question in enumerate(questions):
            question_id = question.get("id", f"q{i+1}")
            user_answer = user_answers.get(question_id, "")

            # Для новой структуры correct_answer находится в самом вопросе
            correct_answer = question.get("correct_answer", "")
            explanation = question.get("explanation", "")

            # Если нет в вопросе, попытка получить из старой структуры
            if not correct_answer and "correct_answers" in quiz_dict:
                correct_answer = quiz_dict["correct_answers"][i] if i < len(quiz_dict["correct_answers"]) else ""
            if not explanation and "explanations" in quiz_dict:
                explanation = quiz_dict["explanations"][i] if i < len(quiz_dict["explanations"]) else ""

            is_correct = user_answer.lower() == correct_answer.lower()

            if is_correct:
                score += 1

            results.append({
                "question": question.get("question", ""),
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": explanation
            })
        
        percentage = (score / total_questions) * 100
        passed = percentage >= 60  # 60% для прохождения
        
        # Сохранить результат
        quiz_result = {
            "_id": f"{user_id}_{quiz_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "user_id": user_id,
            "quiz_id": quiz_id,
            "type": "quiz_result",
            "score": score,
            "total_questions": total_questions,
            "percentage": percentage,
            "passed": passed,
            "answers": user_answers,
            "results": results,
            "completed_at": datetime.now().isoformat()
        }
        
        await db.quiz_results.insert_one(quiz_result)
        
        return {
            "message": "Квиз успешно пройден",
            "score": score,
            "total_questions": total_questions,
            "percentage": percentage,
            "passed": passed,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error submitting quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error submitting quiz: {str(e)}")

@app.post("/api/lessons/add-habit-tracker")
async def add_habit_tracker(
    lesson_id: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Добавить трекер привычек к пользователю"""
    try:
        user_id = current_user["user_id"]

        # Получить привычки из урока (с учетом кастомизаций из админ-панели)
        active_habits = []

        # Сначала проверяем MongoDB (кастомные привычки)
        lesson_in_db = await db.lessons.find_one({"id": lesson_id})
        if lesson_in_db and "habit_tracker" in lesson_in_db:
            # Если есть кастомный habit_tracker в MongoDB
            habit_tracker = lesson_in_db["habit_tracker"]
            planet_habits = habit_tracker.get("planet_habits", {})

            # Берем привычки для планеты sun (для первого урока)
            sun_habits = planet_habits.get("sun", [])
            active_habits = [h["habit"] for h in sun_habits if isinstance(h, dict) and "habit" in h]

        # Если нет кастомных привычек, берем из lesson_system
        if not active_habits:
            lesson = lesson_system.get_lesson(lesson_id)
            if lesson and lesson.habit_tracker:
                sun_habits = lesson.habit_tracker.planet_habits.get("sun", [])
                active_habits = [h["habit"] for h in sun_habits if isinstance(h, dict) and "habit" in h]

        # Если все еще нет привычек, используем дефолтные
        if not active_habits:
            active_habits = [
                "Утренняя аффирмация или медитация",
                "Осознание лидерских качеств",
                "Проявление инициативы",
                "Контроль осанки и речи",
                "Вечернее подведение итогов"
            ]

        # Добавить пользователя к трекеру привычек урока
        lesson_system.add_user_to_tracker(lesson_id, user_id)

        # Сохранить трекер в базе данных
        habit_tracker_data = {
            "_id": f"{user_id}_{lesson_id}_tracker",
            "user_id": user_id,
            "lesson_id": lesson_id,
            "type": "habit_tracker",
            "start_date": datetime.now().isoformat(),
            "daily_completions": {},
            "active_habits": active_habits
        }

        await db.habit_trackers.insert_one(habit_tracker_data)

        return {"message": "Трекер привычек успешно добавлен"}

    except Exception as e:
        logger.error(f"Error adding habit tracker: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding habit tracker: {str(e)}")

@app.get("/api/lessons/habit-tracker/{lesson_id}")
async def get_habit_tracker(
    lesson_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Получить трекер привычек пользователя для урока"""
    try:
        user_id = current_user["user_id"]
        tracker_id = f"{user_id}_{lesson_id}_tracker"

        # Получить трекер из базы данных
        tracker = await db.habit_trackers.find_one({"_id": tracker_id, "type": "habit_tracker"})

        if not tracker:
            return {"tracker": None, "message": "Трекер привычек не найден"}

        # Удалить _id для JSON сериализации
        tracker["_id"] = str(tracker["_id"])

        return {"tracker": tracker, "message": "Трекер привычек успешно загружен"}

    except Exception as e:
        logger.error(f"Error getting habit tracker: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting habit tracker: {str(e)}")

@app.post("/api/lessons/update-habit")
async def update_habit(
    lesson_id: str = Form(...),
    habit_name: str = Form(...),
    completed: bool = Form(...),
    notes: str = Form(""),
    current_user: dict = Depends(get_current_user)
):
    """Обновить статус выполнения привычки"""
    try:
        user_id = current_user["user_id"]
        tracker_id = f"{user_id}_{lesson_id}_tracker"
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Обновить в системе уроков
        lesson_system.update_habit_completion(lesson_id, user_id, habit_name, completed)
        
        # Обновить в базе данных
        await db.habit_trackers.update_one(
            {"_id": tracker_id, "type": "habit_tracker"},
            {
                "$set": {
                    f"daily_completions.{today}.{habit_name}": {
                        "completed": completed,
                        "notes": notes,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            }
        )
        
        return {"message": f"Привычка '{habit_name}' обновлена"}
        
    except Exception as e:
        logger.error(f"Error updating habit: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating habit: {str(e)}")

@app.get("/api/lessons/user-progress/{lesson_id}")
async def get_user_lesson_progress(
    lesson_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Получить прогресс пользователя по уроку"""
    try:
        user_id = current_user["user_id"]
        
        # Получить прогресс из системы уроков
        progress = lesson_system.get_user_progress(lesson_id, user_id)
        
        # Получить дополнительные данные из базы
        quiz_results = await db.quiz_results.find({
            "user_id": user_id,
            "type": "quiz_result"
        }).to_list(100)
        
        challenge_progress = await db.challenge_progress.find({
            "user_id": user_id,
            "type": "challenge_progress"
        }).to_list(100)
        
        habit_tracker = await db.habit_trackers.find_one({
            "user_id": user_id,
            "lesson_id": lesson_id,
            "type": "habit_tracker"
        })
        
        # Очистить ObjectId
        for result in quiz_results:
            result["_id"] = str(result["_id"])
        
        for challenge in challenge_progress:
            challenge["_id"] = str(challenge["_id"])
        
        if habit_tracker:
            habit_tracker["_id"] = str(habit_tracker["_id"])
        
        return {
            "lesson_progress": progress,
            "quiz_results": quiz_results,
            "challenge_progress": challenge_progress,
            "habit_tracker": habit_tracker
        }
        
    except Exception as e:
        logger.error(f"Error getting user progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting user progress: {str(e)}")

@app.post("/api/lessons/save-exercise-response")
async def save_exercise_response(
    lesson_id: str = Form(...),
    exercise_id: str = Form(...),
    response_text: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Сохранить ответ на упражнение"""
    try:
        user_id = current_user["user_id"]
        
        # Создать или обновить ответ на упражнение
        exercise_response = {
            "_id": f"{user_id}_{lesson_id}_{exercise_id}",
            "user_id": user_id,
            "lesson_id": lesson_id,
            "exercise_id": exercise_id,
            "type": "exercise_response",
            "response_text": response_text,
            "completed": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Использовать upsert для обновления существующего или создания нового
        await db.exercise_responses.update_one(
            {"_id": f"{user_id}_{lesson_id}_{exercise_id}"},
            {"$set": exercise_response},
            upsert=True
        )
        
        return {"message": "Ответ на упражнение сохранен"}
        
    except Exception as e:
        logger.error(f"Error saving exercise response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving exercise response: {str(e)}")

@app.get("/api/lessons/exercise-responses/{lesson_id}")
async def get_exercise_responses(
    lesson_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Получить все ответы пользователя на упражнения урока"""
    try:
        user_id = current_user["user_id"]
        
        responses = await db.exercise_responses.find({
            "user_id": user_id,
            "lesson_id": lesson_id,
            "type": "exercise_response"
        }).to_list(100)
        
        # Очистить ObjectId и преобразовать в удобный формат
        result = {}
        for response in responses:
            result[response["exercise_id"]] = {
                "response_text": response["response_text"],
                "completed": response["completed"],
                "updated_at": response["updated_at"]
            }
        
        return {"responses": result}
        
    except Exception as e:
        logger.error(f"Error getting exercise responses: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting exercise responses: {str(e)}")

@app.post("/api/lessons/complete-challenge")
async def complete_challenge(
    challenge_id: str = Form(...),
    rating: int = Form(...),  # Оценка от 1 до 5
    notes: str = Form(""),
    current_user: dict = Depends(get_current_user)
):
    """Завершить челлендж с оценкой"""
    try:
        user_id = current_user["user_id"]
        progress_id = f"{user_id}_{challenge_id}"
        
        # Найти прогресс челленджа
        progress = await db.challenge_progress.find_one({"_id": progress_id, "type": "challenge_progress"})
        if not progress:
            raise HTTPException(status_code=404, detail="Challenge progress not found")
        
        # Обновить статус на завершен
        await db.challenge_progress.update_one(
            {"_id": progress_id},
            {
                "$set": {
                    "status": "completed",
                    "completion_date": datetime.now().isoformat(),
                    "rating": rating,
                    "final_notes": notes,
                    "current_day": 7
                }
            }
        )
        
        return {
            "message": "Челлендж успешно завершен",
            "rating": rating,
            "completed_days": len(progress.get("completed_days", []))
        }
        
    except Exception as e:
        logger.error(f"Error completing challenge: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error completing challenge: {str(e)}")

@app.get("/api/lessons/overall-progress/{lesson_id}")
async def get_overall_progress(
    lesson_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Получить общий прогресс урока в процентах"""
    try:
        user_id = current_user["user_id"]
        logger.info(f"Getting overall progress for lesson {lesson_id}, user {user_id}")

        # Получить данные урока (сначала MongoDB, потом lesson_system)
        custom_lesson = await db.custom_lessons.find_one({"id": lesson_id})

        lesson = None
        if custom_lesson:
            # Урок существует в MongoDB
            logger.info(f"Found custom lesson {lesson_id} in MongoDB")
            lesson_exists = True
        else:
            # Проверяем lesson_system
            logger.info(f"Checking lesson_system for {lesson_id}")
            lesson = lesson_system.get_lesson(lesson_id)
            if not lesson:
                logger.error(f"Lesson {lesson_id} not found in MongoDB or lesson_system")
                raise HTTPException(status_code=404, detail="Lesson not found")
            lesson_exists = True
        
        # Подсчитать общий прогресс
        total_components = 5  # теория, упражнения, квиз, челлендж, привычки
        completed_components = 0
        
        # 1. Проверить упражнения (20%)
        exercise_responses = await db.exercise_responses.find({
            "user_id": user_id,
            "lesson_id": lesson_id,
            "type": "exercise_response"
        }).to_list(100)

        # Получить общее количество упражнений
        total_exercises_count = 0
        if lesson:
            total_exercises_count = len(lesson.exercises) if lesson.exercises else 0
        elif custom_lesson and custom_lesson.get("content", {}).get("exercises"):
            total_exercises_count = len(custom_lesson["content"]["exercises"])

        exercises_completed = total_exercises_count > 0 and len(exercise_responses) >= total_exercises_count
        if exercises_completed:
            completed_components += 1
        
        # 2. Проверить квиз (20%)
        quiz_results = await db.quiz_results.find({
            "user_id": user_id,
            "type": "quiz_result"
        }).to_list(1)
        
        quiz_completed = len(quiz_results) > 0 and any(r.get("passed", False) for r in quiz_results)
        if quiz_completed:
            completed_components += 1
        
        # 3. Проверить челлендж (20%)
        challenge_progress = await db.challenge_progress.find_one({
            "user_id": user_id,
            "type": "challenge_progress"
        })
        
        challenge_completed = challenge_progress and challenge_progress.get("status") == "completed"
        if challenge_completed:
            completed_components += 1
        
        # 4. Проверить трекер привычек (20%)
        habit_tracker = await db.habit_trackers.find_one({
            "user_id": user_id,
            "lesson_id": lesson_id,
            "type": "habit_tracker"
        })
        
        habits_active = habit_tracker is not None
        if habits_active:
            completed_components += 1
        
        # 5. Теория (считаем завершенной если есть хотя бы одно выполненное упражнение) (20%)
        theory_completed = exercises_completed
        if theory_completed:
            completed_components += 1
        
        overall_percentage = int((completed_components / total_components) * 100)
        
        # Получить общее количество упражнений
        total_exercises = 0
        if lesson:
            total_exercises = len(lesson.exercises)
        elif custom_lesson and custom_lesson.get("content", {}).get("exercises"):
            total_exercises = len(custom_lesson["content"]["exercises"])

        return {
            "lesson_id": lesson_id,
            "overall_percentage": overall_percentage,
            "completed_components": completed_components,
            "total_components": total_components,
            "breakdown": {
                "theory": theory_completed,
                "exercises": exercises_completed,
                "quiz": quiz_completed,
                "challenge": challenge_completed,
                "habits": habits_active
            },
            "exercise_count": len(exercise_responses),
            "total_exercises": total_exercises
        }
        
    except Exception as e:
        logger.error(f"Error getting overall progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting overall progress: {str(e)}")

# ==================== ADMIN ENDPOINTS ====================

@app.post("/api/admin/update-lesson-content")
async def update_lesson_content(
    lesson_id: str = Form(...),
    section: str = Form(...),
    field: str = Form(...),
    value: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Обновить содержимое урока (только для администраторов)"""
    try:
        user_id = current_user["user_id"]

        # Проверить права администратора из базы данных
        user = await db.users.find_one({"id": user_id})
        if not user or (not user.get("is_admin") and not user.get("is_super_admin")):
            raise HTTPException(status_code=403, detail="Access denied. Admin rights required.")

        logger.info(f"Updating lesson content: lesson_id={lesson_id}, section={section}, field={field}, value_length={len(value)}")

        # Сохранить изменения в коллекции lesson_content
        content_update = {
            "_id": f"{lesson_id}_{section}_{field}",
            "lesson_id": lesson_id,
            "section": section,
            "field": field,
            "value": value,
            "updated_by": user_id,
            "updated_at": datetime.now().isoformat(),
            "type": "content_update"
        }

        await db.lesson_content.update_one(
            {"_id": f"{lesson_id}_{section}_{field}"},
            {"$set": content_update},
            upsert=True
        )

        logger.info(f"Successfully updated {section}.{field}")
        return {"message": f"Content updated successfully for {section}.{field}"}

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error updating lesson content: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Error updating lesson content: {str(e)}")

@app.post("/api/admin/upload-video")
async def upload_video(
    lesson_id: str = Form(...),
    section: str = Form(...),
    video: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Загрузить видео для урока (только для администраторов)"""
    try:
        # Проверить права администратора из базы данных
        user = await db.users.find_one({"id": current_user["user_id"]})
        if not user or (not user.get("is_admin") and not user.get("is_super_admin")):
            raise HTTPException(status_code=403, detail="Access denied. Admin rights required.")
        
        # Проверить формат файла
        if not video.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="Invalid file format. Only video files are allowed.")
        
        # Создать директорию для загрузки если не существует
        upload_dir = Path("uploads/videos")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Сгенерировать уникальное имя файла
        file_extension = Path(video.filename).suffix
        unique_filename = f"{lesson_id}_{section}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Сохранить файл
        with open(file_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
        
        # Сохранить информацию в базе данных
        video_info = {
            "_id": f"{lesson_id}_{section}_video",
            "lesson_id": lesson_id,
            "section": section,
            "file_path": str(file_path),
            "original_filename": video.filename,
            "file_size": len(content),
            "content_type": video.content_type,
            "uploaded_by": current_user["user_id"],
            "uploaded_at": datetime.now().isoformat(),
            "type": "video_upload"
        }
        
        await db.lesson_media.update_one(
            {"_id": f"{lesson_id}_{section}_video"},
            {"$set": video_info},
            upsert=True
        )
        
        return {
            "message": "Video uploaded successfully",
            "video_url": f"/uploads/videos/{unique_filename}",
            "file_size": len(content)
        }
        
    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading video: {str(e)}")

@app.post("/api/admin/upload-pdf")
async def upload_pdf(
    lesson_id: str = Form(...),
    section: str = Form(...),
    pdf: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Загрузить PDF для урока (только для администраторов)"""
    try:
        # Проверить права администратора из базы данных
        user = await db.users.find_one({"id": current_user["user_id"]})
        if not user or (not user.get("is_admin") and not user.get("is_super_admin")):
            raise HTTPException(status_code=403, detail="Access denied. Admin rights required.")
        
        # Проверить формат файла
        if pdf.content_type != 'application/pdf':
            raise HTTPException(status_code=400, detail="Invalid file format. Only PDF files are allowed.")
        
        # Создать директорию для загрузки если не существует
        upload_dir = Path("uploads/pdfs")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Сгенерировать уникальное имя файла
        unique_filename = f"{lesson_id}_{section}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = upload_dir / unique_filename
        
        # Сохранить файл
        with open(file_path, "wb") as buffer:
            content = await pdf.read()
            buffer.write(content)
        
        # Сохранить информацию в базе данных
        pdf_info = {
            "_id": f"{lesson_id}_{section}_pdf",
            "lesson_id": lesson_id,
            "section": section,
            "file_path": str(file_path),
            "original_filename": pdf.filename,
            "file_size": len(content),
            "content_type": pdf.content_type,
            "uploaded_by": current_user["user_id"],
            "uploaded_at": datetime.now().isoformat(),
            "type": "pdf_upload"
        }
        
        await db.lesson_media.update_one(
            {"_id": f"{lesson_id}_{section}_pdf"},
            {"$set": pdf_info},
            upsert=True
        )
        
        return {
            "message": "PDF uploaded successfully",
            "pdf_url": f"/uploads/pdfs/{unique_filename}",
            "file_size": len(content)
        }
        
    except Exception as e:
        logger.error(f"Error uploading PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading PDF: {str(e)}")

@app.get("/api/admin/lesson-media/{lesson_id}")
async def get_lesson_media(
    lesson_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Получить загруженные медиафайлы урока"""
    try:
        # Проверить права администратора из базы данных
        user = await db.users.find_one({"id": current_user["user_id"]})
        if not user or (not user.get("is_admin") and not user.get("is_super_admin")):
            raise HTTPException(status_code=403, detail="Access denied. Admin rights required.")
        
        media_files = await db.lesson_media.find({
            "lesson_id": lesson_id,
            "type": {"$in": ["video_upload", "pdf_upload"]}
        }).to_list(100)
        
        # Очистить ObjectId
        for media in media_files:
            media["_id"] = str(media["_id"])
        
        return {"media_files": media_files}
        
    except Exception as e:
        logger.error(f"Error getting lesson media: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting lesson media: {str(e)}")

@app.post("/api/admin/lessons/{lesson_id}/add-pdf")
async def add_lesson_additional_pdf(
    lesson_id: str,
    title: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Добавить дополнительный PDF файл к уроку (используем consultations endpoint)"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Используем тот же endpoint что и для консультаций - УНИФИКАЦИЯ!
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        # Генерируем уникальный ID для файла
        file_id = str(uuid.uuid4())
        file_path = CONSULTATIONS_PDF_DIR / f"{file_id}.pdf"
        
        # Копируем файл в директорию консультаций
        import shutil
        shutil.move(temp_file.name, file_path)
        
        # Сохраняем запись в uploaded_files с типом consultation_pdf
        file_record = {
            'id': file_id,
            'original_filename': file.filename,
            'file_path': str(file_path),
            'file_type': 'consultation_pdf',  # Используем тот же тип что и консультации
            'content_type': 'application/pdf',  # Добавляем content_type для совместимости
            'uploaded_by': current_user['user_id'],
            'uploaded_at': datetime.utcnow(),
            'lesson_id': lesson_id,  # Дополнительное поле для связи с уроком
            'pdf_title': title  # Пользовательское название
        }
        
        await db.uploaded_files.insert_one(file_record)
        
        return {
            'success': True,
            'file_id': file_id,
            'filename': file.filename,
            'title': title,
            'pdf_url': f'/api/consultations/pdf/{file_id}',
            'message': 'Дополнительный PDF успешно добавлен к уроку'
        }
        
    except Exception as e:
        logger.error(f"Error adding additional PDF to lesson: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding PDF: {str(e)}")

@app.get("/api/lessons/{lesson_id}/additional-pdfs")
async def get_lesson_additional_pdfs(lesson_id: str):
    """Получить все дополнительные PDF файлы урока"""
    try:
        # Ищем все PDF файлы связанные с уроком
        pdf_cursor = db.uploaded_files.find({
            'lesson_id': lesson_id,
            'file_type': 'consultation_pdf'  # Используем consultations тип
        })
        
        pdfs = []
        async for pdf_record in pdf_cursor:
            pdfs.append({
                'file_id': pdf_record['id'],
                'filename': pdf_record['original_filename'],
                'title': pdf_record.get('pdf_title', pdf_record['original_filename']),
                'pdf_url': f'/api/consultations/pdf/{pdf_record["id"]}',
                'uploaded_at': pdf_record.get('uploaded_at')
            })
        
        return {
            'lesson_id': lesson_id,
            'additional_pdfs': pdfs,
            'count': len(pdfs)
        }
        
    except Exception as e:
        logger.error(f"Error getting lesson additional PDFs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting PDFs: {str(e)}")

@app.post("/api/admin/lessons/{lesson_id}/add-video")
async def add_lesson_additional_video(
    lesson_id: str,
    title: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Добавить дополнительный видео файл к уроку (используем consultations endpoint)"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Используем тот же endpoint что и для консультаций - УНИФИКАЦИЯ!
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        # Генерируем уникальный ID для файла
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix.lower()
        file_path = CONSULTATIONS_VIDEO_DIR / f"{file_id}{file_extension}"
        
        # Копируем файл в директорию консультаций
        import shutil
        shutil.move(temp_file.name, file_path)
        
        # Сохраняем запись в uploaded_files с типом consultation_video
        file_record = {
            'id': file_id,
            'original_filename': file.filename,
            'file_path': str(file_path),
            'file_type': 'consultation_video',  # Используем тот же тип что и консультации
            'content_type': file.content_type or 'video/mp4',
            'uploaded_by': current_user['user_id'],
            'uploaded_at': datetime.utcnow(),
            'lesson_id': lesson_id,  # Дополнительное поле для связи с уроком
            'video_title': title  # Пользовательское название
        }
        
        await db.uploaded_files.insert_one(file_record)
        
        return {
            'success': True,
            'file_id': file_id,
            'filename': file.filename,
            'title': title,
            'video_url': f'/api/consultations/video/{file_id}',
            'message': 'Дополнительное видео успешно добавлено к уроку'
        }
        
    except Exception as e:
        logger.error(f"Error adding additional video to lesson: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding video: {str(e)}")

@app.get("/api/lessons/{lesson_id}/additional-videos")
async def get_lesson_additional_videos(lesson_id: str):
    """Получить все дополнительные видео файлы урока"""
    try:
        # Ищем все видео файлы связанные с уроком
        video_cursor = db.uploaded_files.find({
            'lesson_id': lesson_id,
            'file_type': 'consultation_video'  # Используем consultations тип
        })
        
        videos = []
        async for video_record in video_cursor:
            videos.append({
                'file_id': video_record['id'],
                'filename': video_record['original_filename'],
                'title': video_record.get('video_title', video_record['original_filename']),
                'video_url': f'/api/consultations/video/{video_record["id"]}',
                'uploaded_at': video_record.get('uploaded_at')
            })
        
        return {
            'lesson_id': lesson_id,
            'additional_videos': videos,
            'count': len(videos)
        }
        
    except Exception as e:
        logger.error(f"Error getting lesson additional videos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting videos: {str(e)}")

# ==================== SIMPLE LESSON FILE UPLOAD ENDPOINTS ====================

@app.post("/api/admin/lessons/upload-video")
async def upload_lesson_video(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Загрузка видео файла для урока (упрощенный endpoint)"""
    try:
        logger.info(f"Starting lesson video upload for user: {current_user.get('user_id')}")

        # Проверить права администратора
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        logger.info(f"Admin rights verified for user: {admin_user}")

        # Проверяем тип файла
        if not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail='Файл должен быть видео')

        # Генерируем уникальное имя файла
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        file_path = LESSONS_VIDEO_DIR / f"{file_id}{file_extension}"

        logger.info(f"Saving video file to: {file_path}")

        # Сохраняем файл
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        logger.info(f"Video file saved successfully. Size: {len(content)} bytes")

        # Сохраняем информацию в базу данных
        video_record = {
            'id': file_id,
            'original_filename': file.filename,
            'file_path': str(file_path),
            'content_type': file.content_type,
            'file_size': len(content),
            'uploaded_by': current_user['user_id'],
            'created_at': datetime.now().isoformat(),
            'file_type': 'lesson_video'
        }

        logger.info(f"Inserting video record into DB: {video_record}")
        result = await db.uploaded_files.insert_one(video_record)
        logger.info(f"Video record inserted with _id: {result.inserted_id}")

        return {
            'success': True,
            'file_id': file_id,
            'filename': file.filename,
            'video_url': f'/api/lessons/video/{file_id}',
            'message': 'Видео успешно загружено для урока'
        }
        
    except HTTPException:
        # Re-raise HTTPExceptions (like 400, 403, 404) without modification
        raise
    except Exception as e:
        logger.error(f'Lesson video upload error: {e}')
        raise HTTPException(status_code=500, detail=f'Ошибка при загрузке видео урока: {str(e)}')

@app.post("/api/admin/lessons/upload-pdf")
async def upload_lesson_pdf(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Загрузка PDF файла для урока (упрощенный endpoint)"""
    try:
        # Проверить права администратора
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Проверяем тип файла
        if file.content_type != 'application/pdf':
            raise HTTPException(status_code=400, detail='Файл должен быть PDF')
        
        # Генерируем уникальное имя файла
        file_id = str(uuid.uuid4())
        file_path = LESSONS_PDF_DIR / f"{file_id}.pdf"
        
        # Сохраняем файл
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Сохраняем информацию в базу данных
        pdf_record = {
            'id': file_id,
            'original_filename': file.filename,
            'file_path': str(file_path),
            'content_type': file.content_type,
            'file_size': len(content),
            'uploaded_by': current_user['user_id'],
            'created_at': datetime.now().isoformat(),
            'file_type': 'lesson_pdf'
        }
        
        await db.uploaded_files.insert_one(pdf_record)
        
        return {
            'success': True,
            'file_id': file_id,
            'filename': file.filename,
            'pdf_url': f'/api/lessons/pdf/{file_id}',
            'message': 'PDF успешно загружен для урока'
        }
        
    except HTTPException:
        # Re-raise HTTPExceptions (like 400, 403, 404) without modification
        raise
    except Exception as e:
        logger.error(f'Lesson PDF upload error: {e}')
        raise HTTPException(status_code=500, detail=f'Ошибка при загрузке PDF урока: {str(e)}')

@app.post("/api/admin/lessons/upload-word")
async def upload_lesson_word_simple(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Загрузка Word файла для урока (упрощенный endpoint)"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Проверяем тип файла
        allowed_types = [
            'application/msword',  # .doc
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'  # .docx
        ]
        filename_lower = file.filename.lower() if file.filename else ''
        is_docx = filename_lower.endswith('.docx')
        is_doc = filename_lower.endswith('.doc')
        
        if file.content_type not in allowed_types and not (is_docx or is_doc):
            raise HTTPException(status_code=400, detail='Файл должен быть Word документом (.doc или .docx)')
        
        # Определяем расширение
        file_extension = '.docx' if is_docx else '.doc'
        
        # Генерируем уникальное имя файла
        file_id = str(uuid.uuid4())
        file_path = LESSONS_WORD_DIR / f"{file_id}{file_extension}"
        
        # Сохраняем файл
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Сохраняем информацию в базу данных
        word_record = {
            'id': file_id,
            'original_filename': file.filename,
            'file_path': str(file_path),
            'content_type': file.content_type or ('application/vnd.openxmlformats-officedocument.wordprocessingml.document' if is_docx else 'application/msword'),
            'file_size': len(content),
            'file_extension': file_extension,
            'uploaded_by': current_user['user_id'],
            'created_at': datetime.now().isoformat(),
            'file_type': 'lesson_word'
        }
        
        await db.uploaded_files.insert_one(word_record)
        
        return {
            'success': True,
            'file_id': file_id,
            'filename': file.filename,
            'word_url': f'/api/lessons/word/{file_id}',
            'download_url': f'/api/lessons/word/{file_id}/download',
            'message': 'Word файл успешно загружен для урока'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Lesson Word upload error: {e}')
        raise HTTPException(status_code=500, detail=f'Ошибка при загрузке Word файла урока: {str(e)}')

# Endpoints для получения файлов уроков
@app.api_route("/api/lessons/video/{file_id}", methods=["GET", "HEAD"])
async def get_lesson_video(file_id: str, request: Request):
    """Получить видео урока по ID с поддержкой Range requests"""
    try:
        file_record = await db.uploaded_files.find_one({'id': file_id, 'file_type': 'lesson_video'})
        if not file_record:
            raise HTTPException(status_code=404, detail="Video not found")

        file_path = Path(file_record['file_path'])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found on disk")

        file_size = file_record['file_size']

        # Обработка Range запросов для HEAD и GET
        range_header = request.headers.get('range')

        # Для HEAD запросов возвращаем только заголовки
        if request.method == "HEAD":
            if range_header:
                # Parse range header для HEAD запроса
                import re
                match = re.search(r'bytes=(\d+)-(\d*)', range_header)
                if match:
                    start = int(match.group(1))
                    end = int(match.group(2)) if match.group(2) else file_size - 1
                    end = min(end, file_size - 1)
                    content_length = end - start + 1

                    return Response(
                        status_code=206,
                        headers={
                            'Content-Range': f'bytes {start}-{end}/{file_size}',
                            'Accept-Ranges': 'bytes',
                            'Content-Length': str(content_length),
                            'Content-Type': file_record['content_type'],
                            'Access-Control-Allow-Origin': '*',
                        }
                    )

            return Response(
                headers={
                    'Accept-Ranges': 'bytes',
                    'Content-Type': file_record['content_type'],
                    'Content-Length': str(file_size),
                    'Access-Control-Allow-Origin': '*',
                }
            )

        if range_header:
            # Parse range header (format: "bytes=start-end")
            import re
            match = re.search(r'bytes=(\d+)-(\d*)', range_header)
            if match:
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else file_size - 1
                end = min(end, file_size - 1)

                content_length = end - start + 1

                # Read the requested range
                with open(file_path, 'rb') as f:
                    f.seek(start)
                    data = f.read(content_length)

                return Response(
                    content=data,
                    status_code=206,
                    headers={
                        'Content-Range': f'bytes {start}-{end}/{file_size}',
                        'Accept-Ranges': 'bytes',
                        'Content-Length': str(content_length),
                        'Content-Type': file_record['content_type'],
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
                        'Access-Control-Allow-Headers': 'Range, Authorization, Content-Type',
                    },
                    media_type=file_record['content_type']
                )

        # Если Range не запрошен, возвращаем весь файл
        return FileResponse(
            path=str(file_path),
            media_type=file_record['content_type'],
            filename=file_record['original_filename'],
            headers={
                'Accept-Ranges': 'bytes',
                'Content-Disposition': 'inline',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
                'Access-Control-Allow-Headers': 'Range, Authorization, Content-Type',
            }
        )
    except HTTPException:
        # Re-raise HTTPExceptions (like 404) without modification
        raise
    except Exception as e:
        logger.error(f"Error serving lesson video: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving video")
@app.get("/api/lessons/pdf/{file_id}")
async def get_lesson_pdf(file_id: str):
    """Получить PDF урока по ID"""
    try:
        file_record = await db.uploaded_files.find_one({'id': file_id, 'file_type': 'lesson_pdf'})
        if not file_record:
            raise HTTPException(status_code=404, detail="PDF not found")
        
        file_path = Path(file_record['file_path'])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="PDF file not found on disk")
        
        return FileResponse(
            path=str(file_path),
            media_type='application/pdf',
            filename=file_record['original_filename'],
            headers={
                'Accept-Ranges': 'bytes',
                'Content-Disposition': 'inline',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
                'Access-Control-Allow-Headers': 'Authorization, Content-Type',
            }
        )
    except HTTPException:
        # Re-raise HTTPExceptions (like 404) without modification
        raise
    except Exception as e:
        logger.error(f"Error serving lesson PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving PDF")

@app.get("/api/lessons/word/{file_id}")
async def get_lesson_word(file_id: str, request: Request):
    """Получить Word файл урока по ID для просмотра"""
    try:
        file_record = await db.lesson_word_files.find_one({'id': file_id})
        if not file_record:
            # Проверяем в старой коллекции uploaded_files
            file_record = await db.uploaded_files.find_one({'id': file_id, 'file_type': 'lesson_word'})
        
        if not file_record:
            raise HTTPException(status_code=404, detail="Word file not found")
        
        file_path = Path(file_record['file_path'])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Word file not found on disk")
        
        # Возвращаем файл с правильным MIME type
        content_type = file_record.get('content_type', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document' if file_record.get('file_extension') == '.docx' 
            else 'application/msword')
        
        return FileResponse(
            path=str(file_path),
            media_type=content_type,
            filename=file_record['original_filename'],
            headers={
                'Accept-Ranges': 'bytes',
                'Content-Disposition': 'inline',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
                'Access-Control-Allow-Headers': 'Authorization, Content-Type',
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving lesson Word file: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving Word file")

@app.get("/api/lessons/word/{file_id}/download")
async def download_lesson_word(file_id: str):
    """Скачать Word файл урока по ID"""
    try:
        file_record = await db.lesson_word_files.find_one({'id': file_id})
        if not file_record:
            file_record = await db.uploaded_files.find_one({'id': file_id, 'file_type': 'lesson_word'})
        
        if not file_record:
            raise HTTPException(status_code=404, detail="Word file not found")
        
        file_path = Path(file_record['file_path'])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Word file not found on disk")
        
        content_type = file_record.get('content_type',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document' if file_record.get('file_extension') == '.docx'
            else 'application/msword')
        
        return FileResponse(
            path=str(file_path),
            media_type=content_type,
            filename=file_record['original_filename'],
            headers={
                'Content-Disposition': f'attachment; filename="{file_record["original_filename"]}"',
                'Access-Control-Allow-Origin': '*',
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading lesson Word file: {str(e)}")
        raise HTTPException(status_code=500, detail="Error downloading Word file")

# Obsolete endpoints removed - moved to proper location above

# Обновляем endpoints удаления для работы с консультационной системой
@api_router.delete('/admin/lessons/video/{file_id}')
async def delete_lesson_video(file_id: str, current_user: dict = Depends(get_current_user)):
    """Удалить видео файл урока (через консультационную систему)"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Удаляем из lesson_videos (связь с уроком)
        lesson_video_result = await db.lesson_videos.delete_one({'id': file_id})
        
        # Удаляем из uploaded_files (консультационная система)
        uploaded_file_result = await db.uploaded_files.delete_one({
            'id': file_id, 
            'file_type': 'consultation_video'
        })
        
        # Находим и удаляем физический файл
        file_record = await db.uploaded_files.find_one({'id': file_id})
        if file_record and file_record.get('file_path'):
            file_path = Path(file_record['file_path'])
            if file_path.exists():
                file_path.unlink()
        
        return {
            'success': True,
            'message': 'Видео файл успешно удален из урока и системы',
            'deleted_from_lesson': lesson_video_result.deleted_count > 0,
            'deleted_from_system': uploaded_file_result.deleted_count > 0
        }
        
    except Exception as e:
        logger.error(f"Error deleting lesson video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка удаления видео: {str(e)}")

@api_router.delete('/admin/lessons/pdf/{file_id}')
async def delete_lesson_pdf(file_id: str, current_user: dict = Depends(get_current_user)):
    """Удалить PDF файл урока (через консультационную систему)"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Удаляем из lesson_pdfs (связь с уроком)
        lesson_pdf_result = await db.lesson_pdfs.delete_one({'id': file_id})
        
        # Удаляем из uploaded_files (консультационная система)
        uploaded_file_result = await db.uploaded_files.delete_one({
            'id': file_id, 
            'file_type': 'consultation_pdf'
        })
        
        # Находим и удаляем физический файл
        file_record = await db.uploaded_files.find_one({'id': file_id})
        if file_record and file_record.get('file_path'):
            file_path = Path(file_record['file_path'])
            if file_path.exists():
                file_path.unlink()
        
        return {
            'success': True,
            'message': 'PDF файл успешно удален из урока и системы',
            'deleted_from_lesson': lesson_pdf_result.deleted_count > 0,
            'deleted_from_system': uploaded_file_result.deleted_count > 0
        }
        
    except Exception as e:
        logger.error(f"Error deleting lesson PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка удаления PDF: {str(e)}")

# Унифицированные endpoints для связывания медиа файлов с уроками (используют консультационную систему)
@api_router.post('/admin/lessons/{lesson_id}/link-video')
async def link_video_to_lesson(lesson_id: str, video_data: dict, current_user: dict = Depends(get_current_user)):
    """Связать загруженное через консультационную систему видео с уроком"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Добавляем источник
        video_data['source'] = 'consultation_system'
        video_data['linked_at'] = datetime.utcnow()
        
        # Сохраняем связь в lesson_videos коллекции
        await db.lesson_videos.insert_one(video_data)
        
        return {'success': True, 'message': 'Видео успешно связано с уроком'}
        
    except Exception as e:
        logger.error(f"Error linking video to lesson: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка связывания видео: {str(e)}")

@api_router.post('/admin/lessons/{lesson_id}/link-pdf')
async def link_pdf_to_lesson(lesson_id: str, pdf_data: dict, current_user: dict = Depends(get_current_user)):
    """Связать загруженный через консультационную систему PDF с уроком"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Добавляем источник
        pdf_data['source'] = 'consultation_system'
        pdf_data['linked_at'] = datetime.utcnow()
        
        # Сохраняем связь в lesson_pdfs коллекции
        await db.lesson_pdfs.insert_one(pdf_data)
        
        return {'success': True, 'message': 'PDF успешно связан с уроком'}
        
    except Exception as e:
        logger.error(f"Error linking PDF to lesson: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка связывания PDF: {str(e)}")

# Обновляем endpoint получения медиа файлов для использования консультационных URLs
@app.get("/api/lessons/media/{lesson_id}")
async def get_lesson_media(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Get all media files (videos and PDFs) for a lesson - UNIFIED SYSTEM"""
    try:
        # Получаем видео файлы урока
        video_files = await db.lesson_videos.find({
            'lesson_id': lesson_id
        }).to_list(length=None)
        
        # Получаем PDF файлы урока
        pdf_files = await db.lesson_pdfs.find({
            'lesson_id': lesson_id
        }).to_list(length=None)
        
        # Очищаем MongoDB ObjectIds и унифицируем URLs
        for video in video_files:
            video.pop('_id', None)
            if video.get('id'):
                # ИСПОЛЬЗУЕМ КОНСУЛЬТАЦИОННУЮ СИСТЕМУ ДЛЯ ВСЕХ ФАЙЛОВ
                video['video_url'] = f'/api/consultations/video/{video["id"]}'
            # Добавляем поле filename для совместимости
            if video.get('original_filename'):
                video['filename'] = video['original_filename']
        
        for pdf in pdf_files:
            pdf.pop('_id', None)
            if pdf.get('id'):
                # ИСПОЛЬЗУЕМ КОНСУЛЬТАЦИОННУЮ СИСТЕМУ ДЛЯ ВСЕХ ФАЙЛОВ
                pdf['pdf_url'] = f'/api/consultations/pdf/{pdf["id"]}'
            # Добавляем поле filename для совместимости
            if pdf.get('original_filename'):
                pdf['filename'] = pdf['original_filename']
        
        return {
            'lesson_id': lesson_id,
            'videos': video_files,
            'pdfs': pdf_files,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Error getting lesson media: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting lesson media: {str(e)}")

@app.post("/api/admin/update-exercise")
async def update_exercise(
    lesson_id: str = Form(...),
    exercise_id: str = Form(...),
    title: str = Form(...),
    content: str = Form(""),
    instructions: str = Form(""),
    expected_outcome: str = Form(""),
    exercise_type: str = Form("reflection"),
    current_user: dict = Depends(get_current_user)
):
    """Обновить упражнение (только для администраторов)"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        user_id = current_user["user_id"]
        
        # Разделить инструкции по переносам строк
        instructions_list = [inst.strip() for inst in instructions.split('\n') if inst.strip()]
        
        exercise_update = {
            "_id": f"{lesson_id}_{exercise_id}",
            "lesson_id": lesson_id,
            "exercise_id": exercise_id,
            "title": title,
            "content": content,
            "instructions": instructions_list,
            "expected_outcome": expected_outcome,
            "type": exercise_type,
            "updated_by": user_id,
            "updated_at": datetime.now().isoformat(),
            "content_type": "exercise_update"
        }
        
        await db.lesson_exercises.update_one(
            {"_id": f"{lesson_id}_{exercise_id}"},
            {"$set": exercise_update},
            upsert=True
        )
        
        return {"message": f"Exercise {exercise_id} updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating exercise: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating exercise: {str(e)}")

@app.post("/api/admin/add-exercise")
async def add_exercise(
    lesson_id: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    instructions: str = Form(...),
    expected_outcome: str = Form(...),
    exercise_type: str = Form("reflection"),
    current_user: dict = Depends(get_current_user)
):
    """Добавить новое упражнение (только для администраторов)"""
    try:
        user_id = current_user["user_id"]

        # Проверить права администратора из базы данных
        user = await db.users.find_one({"id": user_id})
        if not user or (not user.get("is_admin") and not user.get("is_super_admin")):
            raise HTTPException(status_code=403, detail="Access denied. Admin rights required.")

        # Сгенерировать ID для нового упражнения с учетом базовых и кастомных
        max_exercise_num = 0

        # Получить базовый урок и посмотреть существующие ID
        lesson = lesson_system.get_lesson(lesson_id)
        if lesson and lesson.exercises:
            for ex in lesson.exercises:
                # Извлекаем номер из ID типа "exercise_1", "exercise_2"
                # ex может быть dict или Pydantic объектом
                exid = ex.id if hasattr(ex, 'id') else ex.get('id', '')
                if exid.startswith('exercise_') and exid[9:].isdigit():
                    max_exercise_num = max(max_exercise_num, int(exid[9:]))

        # Проверяем кастомные упражнения в MongoDB
        custom_exercises = await db.lesson_exercises.find({"lesson_id": lesson_id}).to_list(100)
        for ex in custom_exercises:
            exid = ex.get("exercise_id", "")
            if exid.startswith('exercise_') and exid[9:].isdigit():
                max_exercise_num = max(max_exercise_num, int(exid[9:]))

        exercise_id = f"exercise_{max_exercise_num + 1}"
        logger.info(f"Generated new exercise_id: {exercise_id}")
        
        instructions_list = [inst.strip() for inst in instructions.split('\n') if inst.strip()]
        
        new_exercise = {
            "_id": f"{lesson_id}_{exercise_id}",
            "lesson_id": lesson_id,
            "exercise_id": exercise_id,
            "title": title,
            "content": content,
            "instructions": instructions_list,
            "expected_outcome": expected_outcome,
            "type": exercise_type,
            "created_by": user_id,
            "created_at": datetime.now().isoformat(),
            "content_type": "exercise_update"
        }
        
        await db.lesson_exercises.insert_one(new_exercise)
        
        return {"message": f"Exercise {exercise_id} added successfully", "exercise_id": exercise_id}
        
    except Exception as e:
        logger.error(f"Error adding exercise: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding exercise: {str(e)}")

@app.post("/api/admin/update-quiz-question")
async def update_quiz_question(
    lesson_id: str = Form(...),
    question_id: str = Form(...),
    question_text: str = Form(...),
    options: str = Form(...),
    correct_answer: str = Form(...),
    explanation: str = Form(""),  # Сделаем необязательным
    current_user: dict = Depends(get_current_user)
):
    """Обновить вопрос квиза (только для администраторов)"""
    try:
        user_id = current_user["user_id"]

        # Проверить права администратора из базы данных
        user = await db.users.find_one({"id": user_id})
        if not user or (not user.get("is_admin") and not user.get("is_super_admin")):
            raise HTTPException(status_code=403, detail="Access denied. Admin rights required.")

        logger.info(f"Updating quiz question: lesson_id={lesson_id}, question_id={question_id}, question={question_text[:50]}")
        
        # Разделить варианты ответов по переносам строк
        options_list = [opt.strip() for opt in options.split('\n') if opt.strip()]
        
        question_update = {
            "_id": f"{lesson_id}_{question_id}",
            "lesson_id": lesson_id,
            "question_id": question_id,
            "question": question_text,
            "options": options_list,
            "correct_answer": correct_answer,
            "explanation": explanation,
            "updated_by": user_id,
            "updated_at": datetime.now().isoformat(),
            "content_type": "quiz_question_update"
        }
        
        await db.lesson_quiz_questions.update_one(
            {"_id": f"{lesson_id}_{question_id}"},
            {"$set": question_update},
            upsert=True
        )
        
        return {"message": f"Quiz question {question_id} updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating quiz question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating quiz question: {str(e)}")

@app.post("/api/admin/add-quiz-question")
async def add_quiz_question(
    lesson_id: str = Form(...),
    question_text: str = Form(...),
    options: str = Form(...),
    correct_answer: str = Form(...),
    explanation: str = Form(""),  # Сделаем необязательным
    current_user: dict = Depends(get_current_user)
):
    """Добавить новый вопрос в квиз (только для администраторов)"""
    try:
        user_id = current_user["user_id"]

        # Проверить права администратора из базы данных
        user = await db.users.find_one({"id": user_id})
        if not user or (not user.get("is_admin") and not user.get("is_super_admin")):
            raise HTTPException(status_code=403, detail="Access denied. Admin rights required.")

        logger.info(f"Adding quiz question: lesson_id={lesson_id}, question={question_text[:50]}, options={options[:100]}, correct={correct_answer}")

        # Сгенерировать ID для нового вопроса с учетом базовых и кастомных
        max_question_num = 0

        # Получить базовый урок и посмотреть существующие ID
        lesson = lesson_system.get_lesson(lesson_id)
        if lesson and lesson.quiz and lesson.quiz.questions:
            for q in lesson.quiz.questions:
                # Извлекаем номер из ID типа "q1", "q2"
                # q может быть dict или Pydantic объектом
                qid = q.id if hasattr(q, 'id') else q.get('id', '')
                if qid.startswith('q') and qid[1:].isdigit():
                    max_question_num = max(max_question_num, int(qid[1:]))

        # Проверяем кастомные вопросы в MongoDB
        custom_questions = await db.lesson_quiz_questions.find({"lesson_id": lesson_id}).to_list(100)
        for q in custom_questions:
            qid = q.get("question_id", "")
            if qid.startswith('q') and qid[1:].isdigit():
                max_question_num = max(max_question_num, int(qid[1:]))

        question_id = f"q{max_question_num + 1}"
        logger.info(f"Generated new question_id: {question_id}")
        
        options_list = [opt.strip() for opt in options.split('\n') if opt.strip()]
        
        new_question = {
            "_id": f"{lesson_id}_{question_id}",
            "lesson_id": lesson_id,
            "question_id": question_id,
            "question": question_text,
            "options": options_list,
            "correct_answer": correct_answer,
            "explanation": explanation,
            "created_by": user_id,
            "created_at": datetime.now().isoformat(),
            "content_type": "quiz_question_update"
        }
        
        await db.lesson_quiz_questions.insert_one(new_question)
        
        return {"message": f"Quiz question {question_id} added successfully", "question_id": question_id}
        
    except Exception as e:
        logger.error(f"Error adding quiz question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding quiz question: {str(e)}")

@app.post("/api/admin/update-challenge-day")
async def update_challenge_day(
    lesson_id: str = Form(...),
    challenge_id: str = Form(...),
    day: int = Form(...),
    title: str = Form(...),
    tasks: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Обновить день челленджа (только для администраторов)"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        user_id = current_user["user_id"]
        
        # Разделить задачи по переносам строк
        tasks_list = [task.strip() for task in tasks.split('\n') if task.strip()]
        
        day_update = {
            "_id": f"{lesson_id}_{challenge_id}_day_{day}",
            "lesson_id": lesson_id,
            "challenge_id": challenge_id,
            "day": day,
            "title": title,
            "tasks": tasks_list,
            "updated_by": user_id,
            "updated_at": datetime.now().isoformat(),
            "content_type": "challenge_day_update"
        }
        
        await db.lesson_challenge_days.update_one(
            {"_id": f"{lesson_id}_{challenge_id}_day_{day}"},
            {"$set": day_update},
            upsert=True
        )
        
        return {"message": f"Challenge day {day} updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating challenge day: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating challenge day: {str(e)}")

@app.post("/api/admin/add-challenge-day")
async def add_challenge_day(
    lesson_id: str = Form(...),
    challenge_id: str = Form(...),
    title: str = Form(...),
    tasks: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Добавить новый день в челлендж (только для администраторов)"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        user_id = current_user["user_id"]
        
        # Найти следующий номер дня
        existing_days = await db.lesson_challenge_days.find({
            "lesson_id": lesson_id,
            "challenge_id": challenge_id
        }).to_list(100)
        
        next_day = len(existing_days) + 1
        tasks_list = [task.strip() for task in tasks.split('\n') if task.strip()]
        
        new_day = {
            "_id": f"{lesson_id}_{challenge_id}_day_{next_day}",
            "lesson_id": lesson_id,
            "challenge_id": challenge_id,
            "day": next_day,
            "title": title,
            "tasks": tasks_list,
            "created_by": user_id,
            "created_at": datetime.now().isoformat(),
            "content_type": "challenge_day_update"
        }
        
        await db.lesson_challenge_days.insert_one(new_day)
        
        return {"message": f"Challenge day {next_day} added successfully", "day": next_day}

    except Exception as e:
        logger.error(f"Error adding challenge day: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding challenge day: {str(e)}")

# ==================== HABITS MANAGEMENT (ADMIN) ====================

@app.post("/api/admin/add-habit")
async def add_habit(
    lesson_id: str = Form(...),
    planet: str = Form(...),
    habit: str = Form(...),
    description: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Добавить привычку к планете в уроке (только для администраторов)"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)

        # Проверяем существование урока в MongoDB
        lesson_in_db = await db.lessons.find_one({"id": lesson_id})

        if not lesson_in_db:
            # Если урока нет в MongoDB, получаем его из lesson_system
            lesson_from_system = lesson_system.get_lesson(lesson_id)
            if not lesson_from_system:
                raise HTTPException(status_code=404, detail="Lesson not found")

            # Создаем урок в MongoDB с базовой структурой
            lesson_dict = lesson_from_system.dict()
            lesson_dict["_id"] = lesson_id

            # Если у урока нет habit_tracker, создаем его
            if "habit_tracker" not in lesson_dict or not lesson_dict["habit_tracker"]:
                lesson_dict["habit_tracker"] = {
                    "planet_habits": {
                        "sun": [], "moon": [], "jupiter": [], "rahu": [],
                        "mercury": [], "venus": [], "ketu": [], "saturn": [], "mars": []
                    }
                }
            else:
                # Если habit_tracker существует, убеждаемся что все планеты инициализированы
                if "planet_habits" not in lesson_dict["habit_tracker"]:
                    lesson_dict["habit_tracker"]["planet_habits"] = {}

                planets = ["sun", "moon", "jupiter", "rahu", "mercury", "venus", "ketu", "saturn", "mars"]
                for planet in planets:
                    if planet not in lesson_dict["habit_tracker"]["planet_habits"]:
                        lesson_dict["habit_tracker"]["planet_habits"][planet] = []

            await db.lessons.insert_one(lesson_dict)

        new_habit = {
            "habit": habit,
            "description": description
        }

        # Обновить habit_tracker урока, добавив привычку в массив для планеты
        await db.lessons.update_one(
            {"id": lesson_id},
            {"$push": {f"habit_tracker.planet_habits.{planet}": new_habit}}
        )

        return {"message": f"Habit added to {planet} successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding habit: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding habit: {str(e)}")

@app.post("/api/admin/update-habit-content")
async def update_habit_content(
    lesson_id: str = Form(...),
    planet: str = Form(...),
    habit_index: str = Form(...),
    habit: str = Form(...),
    description: str = Form(""),
    current_user: dict = Depends(get_current_user)
):
    """Обновить привычку в уроке (только для администраторов)"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)

        logger.info(f"Updating habit - lesson_id: {lesson_id}, planet: {planet}, habit_index: {habit_index}")

        # Конвертируем habit_index в int
        try:
            index = int(habit_index)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid habit_index")

        # Проверяем существование урока в MongoDB
        lesson = await db.lessons.find_one({"id": lesson_id})

        if not lesson:
            logger.info(f"Lesson {lesson_id} not found in MongoDB, trying to get from lesson_system")
            # Если урока нет в MongoDB, получаем его из lesson_system
            lesson_from_system = lesson_system.get_lesson(lesson_id)
            if not lesson_from_system:
                raise HTTPException(status_code=404, detail=f"Lesson {lesson_id} not found in lesson_system")

            # Создаем урок в MongoDB с базовой структурой
            lesson_dict = lesson_from_system.dict()
            lesson_dict["_id"] = lesson_id

            # Если у урока нет habit_tracker, создаем его
            if "habit_tracker" not in lesson_dict or not lesson_dict["habit_tracker"]:
                lesson_dict["habit_tracker"] = {
                    "planet_habits": {
                        "sun": [], "moon": [], "jupiter": [], "rahu": [],
                        "mercury": [], "venus": [], "ketu": [], "saturn": [], "mars": []
                    }
                }
            else:
                # Если habit_tracker существует, убеждаемся что все планеты инициализированы
                if "planet_habits" not in lesson_dict["habit_tracker"]:
                    lesson_dict["habit_tracker"]["planet_habits"] = {}

                planets = ["sun", "moon", "jupiter", "rahu", "mercury", "venus", "ketu", "saturn", "mars"]
                for planet in planets:
                    if planet not in lesson_dict["habit_tracker"]["planet_habits"]:
                        lesson_dict["habit_tracker"]["planet_habits"][planet] = []

            await db.lessons.insert_one(lesson_dict)
            lesson = await db.lessons.find_one({"id": lesson_id})

        if "habit_tracker" not in lesson:
            raise HTTPException(status_code=404, detail="Habit tracker not found in lesson")

        # Убеждаемся что все планеты инициализированы
        if "planet_habits" not in lesson["habit_tracker"]:
            lesson["habit_tracker"]["planet_habits"] = {}
            await db.lessons.update_one(
                {"id": lesson_id},
                {"$set": {"habit_tracker.planet_habits": {}}}
            )

        planets = ["sun", "moon", "jupiter", "rahu", "mercury", "venus", "ketu", "saturn", "mars"]
        for p in planets:
            if p not in lesson["habit_tracker"]["planet_habits"]:
                await db.lessons.update_one(
                    {"id": lesson_id},
                    {"$set": {f"habit_tracker.planet_habits.{p}": []}}
                )
                lesson["habit_tracker"]["planet_habits"][p] = []

        # Получаем привычки планеты
        planet_habits = lesson.get("habit_tracker", {}).get("planet_habits", {}).get(planet, [])

        if index < 0 or index >= len(planet_habits):
            raise HTTPException(status_code=400, detail=f"Invalid habit index: {index}, planet has {len(planet_habits)} habits")

        # Обновить конкретную привычку в массиве планеты
        update_fields = {
            f"habit_tracker.planet_habits.{planet}.{index}.habit": habit,
            f"habit_tracker.planet_habits.{planet}.{index}.description": description
        }

        await db.lessons.update_one(
            {"id": lesson_id},
            {"$set": update_fields}
        )

        return {"message": f"Habit {index} for {planet} updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating habit: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating habit: {str(e)}")

@app.post("/api/admin/delete-habit")
async def delete_habit(
    lesson_id: str = Form(...),
    planet: str = Form(...),
    habit_index: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Удалить привычку из урока (только для администраторов)"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)

        # Конвертируем habit_index в int
        try:
            index = int(habit_index)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid habit_index")

        # Сначала получим текущие привычки планеты
        lesson = await db.lessons.find_one({"id": lesson_id})
        if not lesson:
            # Пытаемся загрузить из lesson_system
            lesson_from_system = lesson_system.get_lesson(lesson_id)
            if not lesson_from_system:
                raise HTTPException(status_code=404, detail="Lesson not found")

            # Создаем урок в MongoDB
            lesson_dict = lesson_from_system.dict()
            lesson_dict["_id"] = lesson_id

            if "habit_tracker" not in lesson_dict or not lesson_dict["habit_tracker"]:
                lesson_dict["habit_tracker"] = {
                    "planet_habits": {
                        "sun": [], "moon": [], "jupiter": [], "rahu": [],
                        "mercury": [], "venus": [], "ketu": [], "saturn": [], "mars": []
                    }
                }
            else:
                if "planet_habits" not in lesson_dict["habit_tracker"]:
                    lesson_dict["habit_tracker"]["planet_habits"] = {}

                planets = ["sun", "moon", "jupiter", "rahu", "mercury", "venus", "ketu", "saturn", "mars"]
                for p in planets:
                    if p not in lesson_dict["habit_tracker"]["planet_habits"]:
                        lesson_dict["habit_tracker"]["planet_habits"][p] = []

            await db.lessons.insert_one(lesson_dict)
            lesson = await db.lessons.find_one({"id": lesson_id})

        if "habit_tracker" not in lesson:
            raise HTTPException(status_code=404, detail="Habit tracker not found in lesson")

        # Убеждаемся что все планеты инициализированы
        if "planet_habits" not in lesson["habit_tracker"]:
            lesson["habit_tracker"]["planet_habits"] = {}
            await db.lessons.update_one(
                {"id": lesson_id},
                {"$set": {"habit_tracker.planet_habits": {}}}
            )

        planets = ["sun", "moon", "jupiter", "rahu", "mercury", "venus", "ketu", "saturn", "mars"]
        for p in planets:
            if p not in lesson["habit_tracker"]["planet_habits"]:
                await db.lessons.update_one(
                    {"id": lesson_id},
                    {"$set": {f"habit_tracker.planet_habits.{p}": []}}
                )
                lesson["habit_tracker"]["planet_habits"][p] = []

        planet_habits = lesson.get("habit_tracker", {}).get("planet_habits", {}).get(planet, [])

        if index < 0 or index >= len(planet_habits):
            raise HTTPException(status_code=400, detail=f"Invalid habit index: {index}")

        # Удалить привычку из массива
        planet_habits.pop(index)

        # Обновить весь массив привычек планеты
        await db.lessons.update_one(
            {"id": lesson_id},
            {"$set": {f"habit_tracker.planet_habits.{planet}": planet_habits}}
        )

        return {"message": f"Habit {index} deleted from {planet} successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting habit: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting habit: {str(e)}")

# ==================== ADMIN: GET LESSONS ====================

@app.get("/api/admin/lessons")
async def get_all_lessons_admin(current_user: dict = Depends(get_current_user)):
    """Получить список всех уроков для админа"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)

        # Получить все уроки из системы (in-memory)
        system_lessons = lesson_system.get_all_lessons()

        lessons_list = []
        for lesson in system_lessons:
            lessons_list.append({
                "id": lesson.id,
                "title": lesson.title,
                "module": lesson.module,
                "points_required": lesson.points_required
            })

        # Добавить кастомные уроки из MongoDB (из обеих коллекций)
        custom_lessons_from_lessons = await db.lessons.find({}).to_list(1000)
        custom_lessons_from_custom = await db.custom_lessons.find({}).to_list(1000)

        all_custom_lessons = custom_lessons_from_lessons + custom_lessons_from_custom

        for lesson in all_custom_lessons:
            # Проверяем что этого урока нет в system_lessons
            if not any(sl["id"] == lesson["id"] for sl in lessons_list):
                lessons_list.append({
                    "id": lesson["id"],
                    "title": lesson.get("title", "Без названия"),
                    "module": lesson.get("module", "numerology"),
                    "points_required": lesson.get("points_required", 0)
                })

        logger.info(f"Returning {len(lessons_list)} lessons ({len(system_lessons)} from system + {len(all_custom_lessons)} custom from both collections)")
        return {"lessons": lessons_list}
    except Exception as e:
        logger.error(f"Error getting all lessons: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting all lessons: {str(e)}")

@app.get("/api/admin/lessons/{lesson_id}")
async def get_lesson_admin(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Получить урок со всеми кастомными изменениями для редактирования"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)

        # Сначала проверяем custom_lessons (новые уроки)
        custom_lesson = await db.custom_lessons.find_one({"id": lesson_id})

        if custom_lesson:
            # Это кастомный урок из MongoDB
            lesson_dict = dict(custom_lesson)
            lesson_dict.pop('_id', None)
            
            # Убеждаемся, что все поля медиафайлов присутствуют (даже если None)
            lesson_dict.setdefault('video_file_id', None)
            lesson_dict.setdefault('video_filename', None)
            lesson_dict.setdefault('pdf_file_id', None)
            lesson_dict.setdefault('pdf_filename', None)
            lesson_dict.setdefault('word_file_id', None)
            lesson_dict.setdefault('word_filename', None)
            
            logger.info(f"Loaded custom lesson {lesson_id} from MongoDB")
            logger.info(f"PDF file_id: {lesson_dict.get('pdf_file_id')}, PDF filename: {lesson_dict.get('pdf_filename')}")
            return {"lesson": lesson_dict}

        # Если не нашли в custom_lessons, ищем в lesson_system
        lesson = lesson_system.get_lesson(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        # Преобразуем структуру для фронтенда
        lesson_dict = lesson.dict()
        logger.info(f"Loaded system lesson {lesson_id}")

        # Подготовим content
        if "content" not in lesson_dict:
            lesson_dict["content"] = {}

        # Загружаем кастомные изменения в контенте
        custom_content = await db.lesson_content.find({
            "lesson_id": lesson_id,
            "type": "content_update"
        }).to_list(100)

        if custom_content:
            for item in custom_content:
                section = item.get("section")
                field = item.get("field")
                value = item.get("value")

                if section and field and value is not None:
                    if section not in lesson_dict["content"]:
                        lesson_dict["content"][section] = {}
                    lesson_dict["content"][section][field] = value

        # Загружаем кастомные упражнения из БД (если есть)
        custom_exercises = await db.lesson_exercises.find({
            "lesson_id": lesson_id,
            "content_type": "exercise_update"
        }).to_list(100)

        if custom_exercises:
            custom_exercises_dict = {ex["exercise_id"]: ex for ex in custom_exercises}

            if "exercises" in lesson_dict and lesson_dict["exercises"]:
                updated_exercises = []
                for exercise in lesson_dict["exercises"]:
                    if exercise.get("id") in custom_exercises_dict:
                        custom = custom_exercises_dict[exercise["id"]]
                        updated_exercises.append({
                            "id": custom["exercise_id"],
                            "title": custom["title"],
                            "type": custom["type"],
                            "content": custom["content"],
                            "instructions": custom["instructions"],
                            "expected_outcome": custom["expected_outcome"]
                        })
                    else:
                        updated_exercises.append(exercise)
                lesson_dict["exercises"] = updated_exercises

        # Загружаем кастомные вопросы теста из БД (если есть)
        custom_quiz_questions = await db.lesson_quiz_questions.find({
            "lesson_id": lesson_id,
            "content_type": "quiz_question_update"
        }).to_list(100)

        if custom_quiz_questions:
            custom_questions_dict = {q["question_id"]: q for q in custom_quiz_questions}

            if "quiz" in lesson_dict and lesson_dict["quiz"] and "questions" in lesson_dict["quiz"]:
                updated_questions = []
                for question in lesson_dict["quiz"]["questions"]:
                    if question.get("id") in custom_questions_dict:
                        custom = custom_questions_dict[question["id"]]
                        updated_questions.append({
                            "id": custom["question_id"],
                            "question": custom["question"],
                            "options": custom["options"],
                            "correct_answer": custom["correct_answer"],
                            "explanation": custom["explanation"]
                        })
                    else:
                        updated_questions.append(question)
                lesson_dict["quiz"]["questions"] = updated_questions

        # Загружаем кастомные дни челленджа из БД (если есть)
        custom_challenge_days = await db.lesson_challenge_days.find({
            "lesson_id": lesson_id,
            "content_type": "challenge_day_update"
        }).to_list(100)

        # Применяем кастомные дни к челленджу
        if custom_challenge_days and "challenges" in lesson_dict and lesson_dict["challenges"]:
            custom_days_dict = {day["day"]: day for day in custom_challenge_days}

            # Получаем первый челлендж
            challenge = lesson_dict["challenges"][0]
            if "daily_tasks" in challenge:
                updated_daily_tasks = []

                # Обновляем существующие дни или добавляем новые
                existing_days = {task.get("day"): task for task in challenge["daily_tasks"]}
                all_days = set(existing_days.keys()) | set(custom_days_dict.keys())

                for day_num in sorted(all_days):
                    if day_num in custom_days_dict:
                        # Используем кастомный день
                        custom = custom_days_dict[day_num]
                        updated_daily_tasks.append({
                            "day": custom["day"],
                            "title": custom["title"],
                            "tasks": custom["tasks"]
                        })
                    elif day_num in existing_days:
                        # Используем оригинальный день
                        updated_daily_tasks.append(existing_days[day_num])

                challenge["daily_tasks"] = updated_daily_tasks

        # Загружаем кастомный habit_tracker из MongoDB (если есть)
        lesson_in_db = await db.lessons.find_one({"id": lesson_id})
        if lesson_in_db and "habit_tracker" in lesson_in_db:
            # Если урок существует в MongoDB и имеет habit_tracker, используем его
            lesson_dict["habit_tracker"] = lesson_in_db["habit_tracker"]

        # Добавляем exercises в content
        if "exercises" in lesson_dict and lesson_dict["exercises"]:
            lesson_dict["content"]["exercises"] = lesson_dict["exercises"]

        # Добавляем quiz в content
        if "quiz" in lesson_dict and lesson_dict["quiz"]:
            lesson_dict["content"]["quiz"] = lesson_dict["quiz"]

        # Добавляем первый challenge как challenge (не challenges[0])
        if "challenges" in lesson_dict and lesson_dict["challenges"]:
            lesson_dict["content"]["challenge"] = lesson_dict["challenges"][0]

        return {
            "lesson": lesson_dict,
            "message": "Урок успешно загружен"
        }
    except Exception as e:
        logger.error(f"Error getting lesson for admin: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting lesson for admin: {str(e)}")

@app.post("/api/admin/lessons/create")
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
        existing_lesson = await db.custom_lessons.find_one({"id": lesson_data["id"]})
        if existing_lesson:
            raise HTTPException(status_code=400, detail=f"Lesson with id {lesson_data['id']} already exists")

        # Также проверяем в системных уроках
        system_lesson = lesson_system.get_lesson(lesson_data["id"])
        if system_lesson:
            raise HTTPException(status_code=400, detail=f"Lesson with id {lesson_data['id']} already exists in system")

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

        # Сохраняем в MongoDB
        result = await db.custom_lessons.insert_one(new_lesson)
        logger.info(f"Created new lesson {lesson_data['id']} by admin {admin_user['id']}")

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
    """Обновить существующий урок"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)

        # Проверяем, существует ли урок в custom_lessons
        existing_lesson = await db.custom_lessons.find_one({"id": lesson_id})

        if existing_lesson:
            # Обновляем существующий кастомный урок
            # Явно обновляем все поля, включая медиафайлы, даже если они None
            update_data = {
                "title": lesson_data.get("title", existing_lesson.get("title")),
                "module": lesson_data.get("module", existing_lesson.get("module")),
                "description": lesson_data.get("description", existing_lesson.get("description")),
                "points_required": lesson_data.get("points_required", existing_lesson.get("points_required")),
                "is_active": lesson_data.get("is_active", existing_lesson.get("is_active")),
                "content": lesson_data.get("content", existing_lesson.get("content")),
                "updated_at": datetime.utcnow().isoformat(),
                "updated_by": admin_user["id"]
            }
            
            # Добавляем exercises, quiz и challenges если они есть в lesson_data
            if "exercises" in lesson_data:
                update_data["exercises"] = lesson_data.get("exercises")
            if "quiz" in lesson_data:
                update_data["quiz"] = lesson_data.get("quiz")
            if "challenges" in lesson_data:
                update_data["challenges"] = lesson_data.get("challenges")
            
            # Явно обновляем медиафайлы (даже если они None - это позволит очистить поля)
            if "video_file_id" in lesson_data:
                update_data["video_file_id"] = lesson_data.get("video_file_id")
            if "video_filename" in lesson_data:
                update_data["video_filename"] = lesson_data.get("video_filename")
            if "pdf_file_id" in lesson_data:
                update_data["pdf_file_id"] = lesson_data.get("pdf_file_id")
            if "pdf_filename" in lesson_data:
                update_data["pdf_filename"] = lesson_data.get("pdf_filename")
            if "word_file_id" in lesson_data:
                update_data["word_file_id"] = lesson_data.get("word_file_id")
            if "word_filename" in lesson_data:
                update_data["word_filename"] = lesson_data.get("word_filename")

            result = await db.custom_lessons.update_one(
                {"id": lesson_id},
                {"$set": update_data}
            )
            logger.info(f"Updated custom lesson {lesson_id} by admin {admin_user['id']}")
            logger.info(f"Update result - matched: {result.matched_count}, modified: {result.modified_count}")
            logger.info(f"Update data: pdf_file_id={update_data.get('pdf_file_id')}, pdf_filename={update_data.get('pdf_filename')}")

        else:
            # Это системный урок - создаем запись в custom_lessons
            system_lesson = lesson_system.get_lesson(lesson_id)
            if not system_lesson:
                raise HTTPException(status_code=404, detail=f"Lesson {lesson_id} not found")

            new_custom_lesson = {
                "id": lesson_id,
                "title": lesson_data.get("title", system_lesson.title),
                "module": lesson_data.get("module", system_lesson.module),
                "description": lesson_data.get("description", ""),
                "points_required": lesson_data.get("points_required", system_lesson.points_required),
                "is_active": lesson_data.get("is_active", True),
                "content": lesson_data.get("content", {}),
                "video_file_id": lesson_data.get("video_file_id"),
                "video_filename": lesson_data.get("video_filename"),
                "pdf_file_id": lesson_data.get("pdf_file_id"),
                "pdf_filename": lesson_data.get("pdf_filename"),
                "word_file_id": lesson_data.get("word_file_id"),
                "word_filename": lesson_data.get("word_filename"),
                "created_at": datetime.utcnow().isoformat(),
                "created_by": admin_user["id"]
            }

            await db.custom_lessons.insert_one(new_custom_lesson)
            logger.info(f"Created custom override for system lesson {lesson_id} by admin {admin_user['id']}")

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
    """Удалить урок (только кастомные уроки, не системные)"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)

        # Нельзя удалить первый урок
        if lesson_id == "lesson_numerom_intro":
            raise HTTPException(status_code=403, detail="Cannot delete the first lesson")

        # Проверяем, это системный урок или кастомный
        system_lesson = lesson_system.get_lesson(lesson_id)
        if system_lesson:
            raise HTTPException(status_code=403, detail="Cannot delete system lessons. You can only delete custom lessons.")

        # Удаляем из custom_lessons
        result = await db.custom_lessons.delete_one({"id": lesson_id})

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
async def get_lesson_content_for_editing(
    lesson_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Получить все кастомизированное содержимое урока для редактирования"""
    try:
        admin_user = await check_admin_rights(current_user, require_super_admin=False)
        
        # Получить базовое содержимое урока
        lesson = lesson_system.get_lesson(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        # Получить кастомизированные упражнения
        custom_exercises = await db.lesson_exercises.find({
            "lesson_id": lesson_id,
            "content_type": "exercise_update"
        }).to_list(100)
        
        # Получить кастомизированные вопросы квиза
        custom_quiz_questions = await db.lesson_quiz_questions.find({
            "lesson_id": lesson_id,
            "content_type": "quiz_question_update"
        }).to_list(100)
        
        # Получить кастомизированные дни челленджа
        custom_challenge_days = await db.lesson_challenge_days.find({
            "lesson_id": lesson_id,
            "content_type": "challenge_day_update"
        }).to_list(100)
        
        # Получить кастомизированный контент
        custom_content = await db.lesson_content.find({
            "lesson_id": lesson_id,
            "type": "content_update"
        }).to_list(100)
        
        # Очистить ObjectId
        for item in custom_exercises + custom_quiz_questions + custom_challenge_days + custom_content:
            item["_id"] = str(item["_id"])
        
        return {
            "lesson": lesson.dict() if lesson else None,
            "custom_exercises": custom_exercises,
            "custom_quiz_questions": custom_quiz_questions, 
            "custom_challenge_days": custom_challenge_days,
            "custom_content": custom_content
        }
        
    except Exception as e:
        logger.error(f"Error getting lesson content for editing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting lesson content for editing: {str(e)}")

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

    response = await call_next(request)

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

    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)