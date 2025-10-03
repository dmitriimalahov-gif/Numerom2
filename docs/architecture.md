# Архитектура системы NUMEROM

## Общая архитектура

NUMEROM построен по архитектуре **клиент-сервер** с разделением на frontend и backend компоненты.

```
┌─────────────────┐    HTTP/REST    ┌─────────────────┐    MongoDB    ┌─────────────┐
│   React Client  │ ◄─────────────► │   FastAPI       │ ◄───────────► │   Database  │
│   (Frontend)    │                 │   (Backend)     │               │             │
└─────────────────┘                 └─────────────────┘               └─────────────┘
                                            │                                 
                                            ▼                                 
                                    ┌─────────────────┐                      
                                    │   File Storage  │                      
                                    │   (Videos/PDFs) │                      
                                    └─────────────────┘                      
```

## Backend Architecture

### Основные компоненты

#### 1. **server.py** - Главный сервер
```python
# Основные зависимости
- FastAPI - веб-фреймворк
- MongoDB - база данных  
- JWT - аутентификация
- Stripe - платежи
- Emergent Integrations - дополнительные сервисы
```

**Ключевые функции:**
- REST API endpoints
- Аутентификация и авторизация
- Загрузка и обработка файлов
- Интеграция с платежными системами
- Система кредитов и подписок

#### 2. **models.py** - Модели данных
Все Pydantic модели для валидации и сериализации данных:

```python
# Основные модели
- User, UserCreate, UserResponse      # Пользователи
- PaymentTransaction, PaymentRequest  # Платежи
- VideoLesson, PersonalConsultation  # Обучение
- NumerologyCalculation              # Расчеты
- QuizResult, UserProgress           # Прогресс обучения
```

#### 3. **Модули расчетов**

##### numerology.py - Классическая нумерология
```python
# Основные функции:
- calculate_personal_numbers()    # Персональные числа
- create_pythagorean_square()    # Квадрат Пифагора  
- calculate_compatibility()      # Совместимость
- calculate_name_numerology()    # Нумерология имени
```

##### vedic_numerology.py - Ведическая система
```python
# Ведические расчеты:
- calculate_janma_ank()          # Число рождения
- calculate_bhagya_ank()         # Число судьбы
- create_vedic_yantra()          # Ведическая янтра
- get_vedic_upayas()             # Средства гармонизации
```

##### vedic_time_calculations.py - Временные расчеты
```python
# Временные функции:
- get_vedic_day_schedule()       # Расписание дня
- calculate_rahu_kaal()          # Раху кала
- get_planetary_hours()          # Планетарные часы
- get_muhurtas()                 # Благоприятные периоды
```

#### 4. **Системы управления**

##### auth.py - Аутентификация
```python
# Безопасность:
- JWT токены с 24-часовым сроком
- Хеширование паролей (bcrypt)
- Роли: пользователь, админ, суперадмин
- Middleware для проверки токенов
```

##### lesson_system.py - Система обучения
```python
# LMS компоненты:
- Lesson, Quiz, Challenge         # Основные сущности
- HabitTracker                   # Трекер привычек
- Exercise                       # Упражнения
- Прогресс пользователей
```

##### materials_manager.py - Управление контентом
```python
# Файловая система:
- Загрузка PDF и видеофайлов
- Система хранения в /app/uploads/
- Связывание файлов с уроками
- Контроль доступа к материалам
```

## Frontend Architecture

### Компонентная структура

```
src/
├── components/
│   ├── ui/                    # Базовые UI компоненты (Radix UI)
│   ├── AuthContext.jsx       # Контекст аутентификации
│   ├── MainDashboard.jsx     # Главная панель
│   ├── UserDashboard.jsx     # Пользовательская панель
│   ├── AdminPanel.jsx        # Административная панель
│   ├── NumerologyCalculator.jsx  # Калькулятор нумерологии
│   └── [специализированные компоненты]
├── hooks/
│   └── use-toast.js          # Хук для уведомлений
├── lib/
│   └── utils.js              # Утилиты
└── App.js                    # Главный компонент
```

### Ключевые компоненты

#### 1. **AuthContext** - Управление состоянием пользователя
```jsx
// Предоставляет:
- user: объект текущего пользователя
- login/logout функции
- Проверка токенов
- Автоматическое обновление состояния
```

#### 2. **MainDashboard** - Лендинг и навигация
```jsx
// Функции:
- Лендинг для неавторизованных пользователей
- Презентация функций системы
- Тарифные планы
- Переход к регистрации/входу
```

#### 3. **UserDashboard** - Пользовательский интерфейс
```jsx
// Основные секции:
- Нумерологические расчеты
- Ведические временные расчеты
- Система обучения
- Управление профилем и кредитами
```

#### 4. **AdminPanel** - Административная панель
```jsx
// Управление:
- Пользователями и их правами
- Обучающим контентом
- Системными настройками
- Аналитикой и отчетами
```

## База данных (MongoDB)

### Основные коллекции

#### users - Пользователи системы
```javascript
{
  id: String,
  email: String,
  password_hash: String,
  full_name: String,
  birth_date: String,        // DD.MM.YYYY
  city: String,
  phone_number: String,
  is_premium: Boolean,
  is_super_admin: Boolean,
  credits_remaining: Number,
  subscription_type: String, // "monthly", "annual", null
  created_at: DateTime
}
```

#### numerology_calculations - Результаты расчетов
```javascript
{
  id: String,
  user_id: String,
  calculation_type: String,  // "personal_numbers", "vedic", "compatibility"
  results: Object,          // JSON с результатами
  birth_date: String,
  created_at: DateTime
}
```

#### video_lessons - Обучающие уроки
```javascript
{
  id: String,
  title: String,
  description: String,
  video_url: String,
  pdf_file_id: String,
  level: Number,            // 1-10
  order: Number,
  points_for_lesson: Number, // Стоимость в кредитах
  quiz_questions: Array,
  is_active: Boolean
}
```

#### payment_transactions - Платежные транзакции
```javascript
{
  id: String,
  user_id: String,
  package_type: String,     // "one_time", "monthly", "annual"
  amount: Number,
  currency: String,         // "eur"
  payment_status: String,   // "pending", "paid", "failed"
  session_id: String,       // Stripe session ID
  created_at: DateTime
}
```

#### credit_transactions - История кредитов
```javascript
{
  id: String,
  user_id: String,
  transaction_type: String, // "credit", "debit"
  amount: Number,
  description: String,
  category: String,         // "numerology", "vedic", "learning"
  created_at: DateTime
}
```

## Система безопасности

### Аутентификация
1. **JWT токены** - срок действия 24 часа
2. **Хеширование паролей** - bcrypt с солью
3. **CORS** - настроенный для frontend домена
4. **Rate limiting** - защита от спама запросов

### Авторизация
```python
# Роли в системе:
- Пользователь: основные расчеты и обучение
- Админ: управление пользователями
- Суперадмин: полный доступ к системе

# Проверка прав:
@app.get("/admin/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    # Проверка роли суперадмина
```

## Файловая система

### Структура хранения
```
/app/uploads/
├── consultations/
│   ├── videos/           # Видео консультации
│   ├── pdfs/            # PDF материалы консультаций
│   └── subtitles/       # Субтитры к видео
├── lessons/
│   ├── videos/          # Обучающие видео
│   └── pdfs/            # Методические материалы
├── materials/           # Дополнительные материалы
└── tmp/                # Временные файлы
```

### Управление файлами
1. **Загрузка**: Multipart form data через FastAPI
2. **Хранение**: Локальная файловая система
3. **Доступ**: Контролируемый через API эндпоинты
4. **Безопасность**: Проверка типов файлов и размера

## Интеграции

### Stripe (Платежи)
```python
# Настройка:
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
PAYMENT_PACKAGES = {
    'one_time': 0.99,    # €
    'monthly': 9.99,     # €
    'annual': 66.6,      # €
}
```

### Геокодирование (Временные расчеты)
```python
# Библиотеки:
- geopy.geocoders.Nominatim  # Координаты городов
- timezonefinder             # Часовые пояса
- pytz                       # Работа с временными зонами
```

## Производительность

### Кеширование
1. **Координаты городов** - кеш в памяти
2. **Результаты расчетов** - сохранение в MongoDB
3. **Статические файлы** - обслуживание через FastAPI

### Оптимизация
1. **Async/await** - асинхронная обработка запросов
2. **Пагинация** - для больших списков данных
3. **Ленивая загрузка** - для тяжелых расчетов
4. **Компрессия** - для передачи больших файлов

## Мониторинг и логирование

### Логирование
```python
import logging
logging.basicConfig(level=logging.INFO)

# Логируются:
- Успешные операции
- Ошибки и исключения
- Платежные транзакции
- Доступ к административным функциям
```

### Метрики
- Количество пользователей
- Использование кредитов
- Популярность функций
- Конверсия платежей


