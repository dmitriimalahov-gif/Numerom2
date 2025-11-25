# Платежная система

## Обзор

NUMEROM использует интеграцию со Stripe для обработки платежей в евро с системой кредитов и подписок. Поддерживается как разовые платежи, так и рекуррентные подписки.

## Архитектура платежей

### Компоненты системы
1. **Stripe Checkout** - безопасная обработка платежей
2. **Система кредитов** - внутренняя валюта платформы
3. **Подписки** - автоматическое продление доступа
4. **Транзакции** - отслеживание всех операций

### Схема платежного процесса
```
Пользователь → Frontend → Backend → Stripe → Webhook → Зачисление кредитов
```

## Тарифные планы

### Стоимость и содержание пакетов
```python
PAYMENT_PACKAGES = {
    'one_time': 0.99,         # 0,99€ = 10 баллов + месяц доступа
    'monthly': 9.99,          # 9,99€ = 150 баллов + месяц доступа  
    'annual': 66.6,           # 66,6€ = 1000 баллов + год доступа
    'master_consultation': 666.0  # 666€ = 10000 баллов + персональная консультация
}

SUBSCRIPTION_CREDITS = {
    'one_time': 10,           # 10 баллов за 0,99€
    'monthly': 150,           # 150 баллов за 9,99€
    'annual': 1000,           # 1000 баллов за 66,6€
    'master_consultation': 10000  # 10000 баллов + консультация за 666€
}
```

### Детальное описание тарифов

#### 1. Стартовый пакет (0.99€)
- **Кредиты:** 10
- **Длительность:** 1 месяц доступа
- **Возможности:**
  - Базовые нумерологические расчеты
  - Квадрат Пифагора  
  - HTML отчеты
  - Ограниченный доступ к урокам

#### 2. Базовый пакет (9.99€) 
- **Кредиты:** 150
- **Длительность:** 1 месяц доступа
- **Возможности:**
  - Все функции Стартового
  - Ведические расчеты
  - Временные расчеты
  - Планетарные графики
  - Совместимость
  - Полный доступ к урокам

#### 3. Профессиональный (66.6€)
- **Кредиты:** 1000 
- **Длительность:** 1 год доступа
- **Возможности:**
  - Все функции Базового
  - Приоритетная поддержка
  - Эксклюзивные материалы
  - Групповая совместимость
  - Практически безлимитное использование

#### 4. Мастер консультация (666€)
- **Кредиты:** 10000
- **Длительность:** Без ограничений
- **Возможности:**
  - Все функции Профессионального
  - Персональная консультация от мастера
  - Индивидуальные рекомендации
  - VIP поддержка

## Система кредитов

### Стоимость операций
```python
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
```

### Модель транзакций кредитов
```python
class CreditTransaction(BaseModel):
    id: str                         # Уникальный идентификатор
    user_id: str                    # ID пользователя
    transaction_type: str           # 'debit' или 'credit'
    amount: int                     # Количество баллов (+ или -)
    description: str                # Описание операции
    category: str                   # Категория: 'numerology', 'vedic', 'learning', etc.
    details: Optional[dict] = None  # Дополнительные детали
    created_at: datetime            # Время транзакции
```

### Примеры транзакций
```python
# Покупка кредитов
{
    "transaction_type": "credit",
    "amount": 150,
    "description": "Покупка Базового пакета",
    "category": "purchase",
    "details": {"package": "monthly", "stripe_session": "cs_xxx"}
}

# Использование кредитов
{
    "transaction_type": "debit", 
    "amount": -1,
    "description": "Расчет персональных чисел",
    "category": "numerology",
    "details": {"calculation_type": "personal_numbers", "birth_date": "15.08.1985"}
}
```

## Интеграция со Stripe

### Настройка Stripe
```python
# Конфигурация
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
PAYMENT_DEMO_MODE = not STRIPE_API_KEY or STRIPE_API_KEY == 'sk_test_dummy_key_for_testing'

# Использование Emergent Integrations
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionRequest
)
```

### Модель платежной транзакции
```python
class PaymentTransaction(BaseModel):
    id: str                         # Уникальный идентификатор
    user_id: Optional[str] = None   # ID пользователя (может быть неавторизован)
    user_email: Optional[str] = None # Email для неавторизованных
    package_type: str               # "one_time", "monthly", "annual", "master_consultation"
    amount: float                   # Сумма в евро
    currency: str = "eur"           # Валюта
    session_id: str                 # Stripe session ID
    payment_status: str = "pending" # pending, paid, failed, expired
    metadata: Optional[Dict[str, Any]] = None  # Дополнительные данные
    created_at: datetime            # Время создания
    updated_at: datetime            # Время обновления
```

## API Endpoints

### 1. Создание сессии оплаты
```http
POST /api/payments/create-checkout-session
Authorization: Bearer <token> (optional)
Content-Type: application/json

{
  "package_type": "monthly",
  "origin_url": "https://numerom.com"
}
```

**Ответ:**
```json
{
  "success": true,
  "checkout_url": "https://checkout.stripe.com/pay/cs_test_xxx",
  "session_id": "cs_test_xxx",
  "transaction_id": "uuid4-string"
}
```

### 2. Проверка статуса платежа
```http
GET /api/payments/status/{transaction_id}
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "transaction_id": "uuid4-string",
  "payment_status": "paid",
  "package_type": "monthly", 
  "amount": 9.99,
  "credits_added": 150,
  "subscription_until": "2024-02-15T10:30:00Z"
}
```

### 3. История платежей пользователя
```http
GET /api/payments/history
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "transactions": [
    {
      "id": "uuid4-string",
      "package_type": "monthly",
      "amount": 9.99,
      "payment_status": "paid",
      "credits_received": 150,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_spent": 19.98,
  "total_credits_purchased": 300
}
```

### 4. Получение информации о кредитах
```http
GET /api/credits/balance
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "current_balance": 45,
  "total_earned": 160,
  "total_spent": 115,
  "last_transaction": {
    "type": "debit",
    "amount": -1,
    "description": "Расчет совместимости",
    "date": "2024-01-15T14:22:00Z"
  }
}
```

### 5. История транзакций кредитов
```http
GET /api/credits/transactions?limit=20&offset=0
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "transactions": [
    {
      "id": "uuid4-string",
      "transaction_type": "debit",
      "amount": -1,
      "description": "Расчет персональных чисел",
      "category": "numerology",
      "created_at": "2024-01-15T14:22:00Z"
    },
    {
      "id": "uuid4-string",
      "transaction_type": "credit", 
      "amount": 150,
      "description": "Покупка Базового пакета",
      "category": "purchase",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 25,
  "has_more": true
}
```

## Обработка платежей

### Создание Stripe сессии
```python
async def create_checkout_session(package_type: str, user_id: str = None, origin_url: str = ""):
    """Создает сессию Stripe Checkout"""
    
    # Проверяем валидность пакета
    if package_type not in PAYMENT_PACKAGES:
        raise HTTPException(400, f"Неизвестный тип пакета: {package_type}")
    
    amount = PAYMENT_PACKAGES[package_type]
    credits = SUBSCRIPTION_CREDITS[package_type]
    
    # Создаем транзакцию в БД
    transaction = PaymentTransaction(
        user_id=user_id,
        package_type=package_type,
        amount=amount,
        session_id="",  # Будет обновлен после создания сессии
        payment_status="pending"
    )
    
    # Создаем Stripe сессию
    stripe_checkout = StripeCheckout(STRIPE_API_KEY)
    
    checkout_request = CheckoutSessionRequest(
        success_url=f"{origin_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{origin_url}/payment-cancelled",
        line_items=[{
            "price_data": {
                "currency": "eur",
                "product_data": {
                    "name": get_package_name(package_type),
                    "description": f"{credits} кредитов NUMEROM"
                },
                "unit_amount": int(amount * 100)  # Stripe принимает центы
            },
            "quantity": 1
        }],
        metadata={
            "transaction_id": transaction.id,
            "user_id": user_id or "",
            "package_type": package_type,
            "credits": str(credits)
        }
    )
    
    session = stripe_checkout.create_checkout_session(checkout_request)
    
    # Обновляем транзакцию с session_id
    transaction.session_id = session.id
    await db.payment_transactions.insert_one(transaction.dict())
    
    return {
        "success": True,
        "checkout_url": session.url,
        "session_id": session.id,
        "transaction_id": transaction.id
    }
```

### Webhook обработка
```python
@app.post("/api/payments/stripe-webhook")
async def handle_stripe_webhook(request: Request):
    """Обрабатывает вебхуки от Stripe"""
    
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")
    
    # Обрабатываем успешную оплату
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        await process_successful_payment(session)
    
    return {"status": "success"}

async def process_successful_payment(session):
    """Обрабатывает успешную оплату"""
    
    metadata = session.get('metadata', {})
    transaction_id = metadata.get('transaction_id')
    user_id = metadata.get('user_id')
    package_type = metadata.get('package_type')
    credits = int(metadata.get('credits', 0))
    
    # Обновляем статус транзакции
    await db.payment_transactions.update_one(
        {"id": transaction_id},
        {"$set": {
            "payment_status": "paid",
            "updated_at": datetime.utcnow()
        }}
    )
    
    if user_id:
        # Начисляем кредиты пользователю
        await add_credits_to_user(user_id, credits, package_type)
        
        # Обновляем подписку
        await update_user_subscription(user_id, package_type)

async def add_credits_to_user(user_id: str, credits: int, package_type: str):
    """Начисляет кредиты пользователю"""
    
    # Обновляем баланс пользователя
    await db.users.update_one(
        {"id": user_id},
        {"$inc": {"credits_remaining": credits}}
    )
    
    # Записываем транзакцию кредитов
    credit_transaction = CreditTransaction(
        user_id=user_id,
        transaction_type="credit",
        amount=credits,
        description=f"Покупка пакета {get_package_name(package_type)}",
        category="purchase",
        details={"package_type": package_type}
    )
    
    await db.credit_transactions.insert_one(credit_transaction.dict())

async def update_user_subscription(user_id: str, package_type: str):
    """Обновляет подписку пользователя"""
    
    now = datetime.utcnow()
    
    if package_type == "monthly":
        expires_at = now + timedelta(days=30)
        subscription_type = "monthly"
    elif package_type == "annual":
        expires_at = now + timedelta(days=365)
        subscription_type = "annual"
    elif package_type == "master_consultation":
        expires_at = None  # Без ограничений
        subscription_type = "lifetime"
    else:  # one_time
        expires_at = now + timedelta(days=30)
        subscription_type = None
    
    update_data = {
        "is_premium": True,
        "subscription_type": subscription_type,
        "updated_at": now
    }
    
    if expires_at:
        update_data["subscription_expires_at"] = expires_at
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": update_data}
    )
```

## Списание кредитов

### Функция списания
```python
async def deduct_credits(user_id: str, amount: int, description: str, 
                        category: str, details: dict = None) -> bool:
    """
    Списывает кредиты у пользователя
    
    Returns:
        bool: True если списание успешно, False если недостаточно кредитов
    """
    
    # Получаем текущий баланс
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(404, "Пользователь не найден")
    
    current_balance = user.get("credits_remaining", 0)
    
    # Проверяем достаточность кредитов
    if current_balance < amount:
        return False
    
    # Списываем кредиты
    await db.users.update_one(
        {"id": user_id},
        {"$inc": {"credits_remaining": -amount}}
    )
    
    # Записываем транзакцию
    transaction = CreditTransaction(
        user_id=user_id,
        transaction_type="debit",
        amount=-amount,
        description=description,
        category=category,
        details=details
    )
    
    await db.credit_transactions.insert_one(transaction.dict())
    
    return True

# Использование при расчетах
@app.post("/api/numerology/personal-numbers")
async def calculate_personal_numbers_endpoint(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    cost = CREDIT_COSTS['personal_numbers']
    
    # Списываем кредиты
    success = await deduct_credits(
        user_id=current_user["user_id"],
        amount=cost,
        description="Расчет персональных чисел",
        category="numerology",
        details={"birth_date": request["birth_date"]}
    )
    
    if not success:
        raise HTTPException(402, "Недостаточно кредитов")
    
    # Выполняем расчет
    result = calculate_personal_numbers(request["birth_date"])
    return result
```

## Демо режим

### Конфигурация демо режима
```python
PAYMENT_DEMO_MODE = not STRIPE_API_KEY or STRIPE_API_KEY == 'sk_test_dummy_key_for_testing'

if PAYMENT_DEMO_MODE:
    # В демо режиме используются тестовые данные
    # Платежи обрабатываются мгновенно без реального списания
    pass
```

### Обработка в демо режиме
```python
async def create_demo_payment(package_type: str, user_id: str = None):
    """Создает демо платеж без реальных денег"""
    
    credits = SUBSCRIPTION_CREDITS[package_type]
    
    # Создаем успешную транзакцию
    transaction = PaymentTransaction(
        user_id=user_id,
        package_type=package_type,
        amount=PAYMENT_PACKAGES[package_type],
        session_id=f"demo_{uuid.uuid4()}",
        payment_status="paid"
    )
    
    await db.payment_transactions.insert_one(transaction.dict())
    
    if user_id:
        await add_credits_to_user(user_id, credits, package_type)
        await update_user_subscription(user_id, package_type)
    
    return {
        "success": True,
        "demo_mode": True,
        "credits_added": credits
    }
```

## Аналитика платежей

### Метрики для администраторов
```python
@app.get("/api/admin/payments/analytics")
async def get_payment_analytics(current_user: dict = Depends(get_current_user)):
    # Проверка прав суперадминистратора
    
    # Общая статистика
    total_transactions = await db.payment_transactions.count_documents({"payment_status": "paid"})
    total_revenue = await db.payment_transactions.aggregate([
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    
    # По пакетам
    package_stats = await db.payment_transactions.aggregate([
        {"$match": {"payment_status": "paid"}},
        {"$group": {
            "_id": "$package_type",
            "count": {"$sum": 1},
            "revenue": {"$sum": "$amount"}
        }}
    ]).to_list(None)
    
    # Конверсия
    pending_count = await db.payment_transactions.count_documents({"payment_status": "pending"})
    conversion_rate = (total_transactions / (total_transactions + pending_count)) * 100 if total_transactions + pending_count > 0 else 0
    
    return {
        "total_transactions": total_transactions,
        "total_revenue": total_revenue[0]["total"] if total_revenue else 0,
        "conversion_rate": round(conversion_rate, 2),
        "package_breakdown": package_stats,
        "average_transaction": round(total_revenue[0]["total"] / total_transactions, 2) if total_transactions > 0 else 0
    }
```

## Безопасность

### Валидация платежей
1. **Webhook подписи** - проверка подлинности запросов от Stripe
2. **Идемпотентность** - защита от повторной обработки платежей
3. **Таймауты** - автоматическое истечение незавершенных сессий
4. **Логирование** - запись всех платежных операций

### Защита от мошенничества
1. **Rate limiting** - ограничение количества попыток оплаты
2. **IP filtering** - блокировка подозрительных IP
3. **Суммовые лимиты** - ограничения на крупные платежи
4. **Мониторинг паттернов** - обнаружение аномальной активности

## Возвраты и отмены

### Политика возвратов
```python
async def process_refund(transaction_id: str, reason: str, admin_user_id: str):
    """Обрабатывает возврат средств"""
    
    transaction = await db.payment_transactions.find_one({"id": transaction_id})
    if not transaction or transaction["payment_status"] != "paid":
        raise HTTPException(400, "Транзакция не найдена или не оплачена")
    
    # Возврат через Stripe
    refund = stripe.Refund.create(
        payment_intent=transaction["session_id"],
        reason=reason
    )
    
    # Обновляем статус
    await db.payment_transactions.update_one(
        {"id": transaction_id},
        {"$set": {
            "payment_status": "refunded",
            "refund_reason": reason,
            "refunded_by": admin_user_id,
            "refunded_at": datetime.utcnow()
        }}
    )
    
    # Списываем кредиты у пользователя (если есть)
    if transaction["user_id"]:
        credits_to_deduct = SUBSCRIPTION_CREDITS[transaction["package_type"]]
        await deduct_credits(
            user_id=transaction["user_id"],
            amount=credits_to_deduct,
            description=f"Возврат платежа {transaction_id}",
            category="refund"
        )
```

## Планируемые улучшения

### Дополнительные способы оплаты
1. **PayPal** - альтернативный провайдер
2. **Apple Pay / Google Pay** - мобильные платежи
3. **Криптовалюты** - Bitcoin, Ethereum
4. **Банковские переводы** - для корпоративных клиентов

### Функции лояльности
1. **Бонусные кредиты** - за активность и рефералы
2. **Скидки** - для долгосрочных пользователей
3. **Промокоды** - маркетинговые акции
4. **Cashback** - возврат части платежа кредитами


