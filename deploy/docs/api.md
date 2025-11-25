# API Документация

## Обзор

NUMEROM API предоставляет RESTful интерфейс для всех функций платформы. API построен на FastAPI с автоматической документацией через OpenAPI/Swagger.

## Базовая информация

- **Base URL:** `https://api.numerom.com` (или `http://localhost:8000` для разработки)
- **Формат данных:** JSON
- **Аутентификация:** Bearer Token (JWT)
- **Кодировка:** UTF-8

## Аутентификация

### Заголовки запросов
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Получение токена
```http
POST /api/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid4-string",
    "email": "user@example.com",
    "full_name": "Имя Фамилия",
    "credits_remaining": 150
  }
}
```

## Коды ответов

| Код | Описание |
|-----|----------|
| 200 | OK - Запрос выполнен успешно |
| 201 | Created - Ресурс создан |
| 400 | Bad Request - Некорректный запрос |
| 401 | Unauthorized - Требуется аутентификация |
| 402 | Payment Required - Недостаточно кредитов |
| 403 | Forbidden - Недостаточно прав |
| 404 | Not Found - Ресурс не найден |
| 422 | Unprocessable Entity - Ошибка валидации |
| 500 | Internal Server Error - Внутренняя ошибка сервера |

## Группы эндпоинтов

### 1. Аутентификация

#### POST /api/register
Регистрация нового пользователя.

**Запрос:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "Анна Смирнова",
  "birth_date": "15.08.1985",
  "city": "Москва"
}
```

**Ответ:** Аналогичен `/api/login`

#### POST /api/login
Вход в систему.

#### GET /api/profile
Получение профиля текущего пользователя.

**Заголовки:** `Authorization: Bearer <token>`

**Ответ:**
```json
{
  "id": "uuid4-string",
  "email": "user@example.com",
  "full_name": "Анна Смирнова",
  "birth_date": "15.08.1985",
  "city": "Москва",
  "phone_number": "+37369183398",
  "is_premium": true,
  "credits_remaining": 125,
  "subscription_type": "monthly",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### PUT /api/profile
Обновление профиля пользователя.

**Запрос:**
```json
{
  "full_name": "Анна Петрова",
  "phone_number": "+37369183398",
  "city": "Кишинев",
  "car_number": "ABC123",
  "street": "ул. Пушкина",
  "house_number": "10",
  "apartment_number": "5"
}
```

### 2. Нумерологические расчеты

#### POST /api/numerology/personal-numbers
Расчет персональных чисел.

**Стоимость:** 1 кредит

**Запрос:**
```json
{
  "birth_date": "15.08.1985"
}
```

**Ответ:**
```json
{
  "soul_number": 6,
  "mind_number": 8,
  "destiny_number": 1,
  "ruling_number": 1,
  "planetary_strength": {
    "Солнце": 1,
    "Луна": 9,
    "Марс": 8,
    "Меркурий": 3,
    "Юпитер": 9,
    "Венера": 8,
    "Сатурн": 2
  },
  "birth_weekday": "четверг",
  "calculation_details": {
    "calculation_number": 1983982,
    "start_planet_index": 3
  }
}
```

#### POST /api/numerology/pythagorean-square
Построение квадрата Пифагора.

**Стоимость:** 1 кредит

**Запрос:**
```json
{
  "birth_date": "15.08.1985"
}
```

**Ответ:**
```json
{
  "square": [
    ["111", "", "33"],
    ["", "555", ""],
    ["7", "888", "9"]
  ],
  "horizontal_sums": [6, 3, 4],
  "vertical_sums": [4, 6, 3],
  "diagonal_sums": [7, 6],
  "additional_numbers": [37, 1, 35, 8]
}
```

#### POST /api/numerology/name-number
Нумерология имени.

**Стоимость:** 1 кредит

**Запрос:**
```json
{
  "name": "Анна Смирнова"
}
```

**Ответ:**
```json
{
  "full_name": "Анна Смирнова",
  "first_name": "Анна",
  "last_name": "Смирнова",
  "first_name_number": 4,
  "last_name_number": 7,
  "total_name_number": 2,
  "first_name_interpretation": "Стабильность, практичность, трудолюбие",
  "last_name_interpretation": "Духовность, анализ, мудрость",
  "total_interpretation": "Сотрудничество, дипломатия, чувствительность"
}
```

#### POST /api/numerology/compatibility
Анализ совместимости двух людей.

**Стоимость:** 1 кредит

**Запрос:**
```json
{
  "person1_birth_date": "15.08.1985",
  "person2_birth_date": "22.03.1990",
  "person1_name": "Анна",
  "person2_name": "Михаил"
}
```

**Ответ:**
```json
{
  "person1_life_path": 5,
  "person2_life_path": 7,
  "compatibility_score": 8,
  "description": "Совместимость 8/10",
  "detailed_analysis": {
    "strengths": ["Взаимное уважение", "Дополняющие качества"],
    "challenges": ["Разные подходы к жизни"],
    "recommendations": ["Больше общения", "Принятие различий"]
  }
}
```

#### POST /api/numerology/group-compatibility
Групповая совместимость (до 5 человек).

**Стоимость:** 5 кредитов

**Запрос:**
```json
{
  "main_person_birth_date": "15.08.1985",
  "main_person_name": "Анна",
  "people": [
    {"name": "Михаил", "birth_date": "22.03.1990"},
    {"name": "Елена", "birth_date": "10.12.1988"},
    {"name": "Сергей", "birth_date": "05.07.1987"}
  ]
}
```

### 3. Ведическая нумерология

#### POST /api/vedic/comprehensive-analysis
Полный ведический анализ.

**Стоимость:** 2 кредита

**Запрос:**
```json
{
  "birth_date": "15.08.1985",
  "name": "Анна Смирнова"
}
```

**Ответ:**
```json
{
  "janma_ank": 1,
  "nama_ank": 2,
  "bhagya_ank": 1,
  "atma_ank": 6,
  "shakti_ank": 3,
  "graha_shakti": {
    "graha_1_सूर्य (Surya)": 2,
    "graha_5_बुध (Budha)": 2,
    "graha_8_शनि (Shani)": 2,
    "graha_9_मंगल (Mangal)": 1
  },
  "mahadasha": "सूर्य (Surya)",
  "antardasha": "चन्द्र (Chandra)",
  "yantra_matrix": [
    ["11", "", ""],
    ["", "55", ""],
    ["", "88", "9"]
  ],
  "upayas": [
    "सूर्य नमस्कार का अभ्यास करें (Practice Surya Namaskara)",
    "रविवार को लाल वस्त्र धारण करें (Wear red clothes on Sunday)"
  ],
  "mantras": ["ॐ ह्राम ह्रीम ह्राम सः सूर्याय नमः"],
  "gemstones": ["माणिक्य (Ruby)", "गार्नेट (Garnet)"]
}
```

#### POST /api/vedic/weekly-energy
Планетарные энергии на неделю.

**Стоимость:** 3 кредита

**Запрос:**
```json
{
  "birth_date": "15.08.1985"
}
```

**Ответ:**
```json
[
  {
    "date": "2024-01-15",
    "day_name": "Monday",
    "surya": 75,
    "chandra": 85,
    "mangal": 60,
    "budha": 70,
    "guru": 80,
    "shukra": 65,
    "shani": 55,
    "rahu": 45,
    "ketu": 40
  }
]
```

### 4. Временные расчеты

#### POST /api/vedic-time/daily-schedule
Ведическое расписание дня.

**Стоимость:** 1 кредит

**Запрос:**
```json
{
  "city": "Кишинев",
  "date": "2024-01-15"
}
```

**Ответ:**
```json
{
  "date": "2024-01-15",
  "city": "Кишинев",
  "timezone": "Europe/Chisinau",
  "sun_times": {
    "sunrise": "07:45",
    "sunset": "17:30",
    "day_length": 9.75
  },
  "rahu_kaal": {
    "start": "09:15",
    "end": "10:45",
    "duration": "1:30"
  },
  "gulika_kaal": {
    "start": "15:30",
    "end": "17:00",
    "duration": "1:30"
  },
  "abhijit_muhurta": {
    "start": "12:13",
    "end": "13:01",
    "duration": "0:48"
  },
  "planetary_hours": [
    {
      "hour": 1,
      "start_time": "07:45",
      "end_time": "08:44",
      "planet": "Chandra",
      "planet_ru": "Луна",
      "favorable": true
    }
  ]
}
```

#### POST /api/vedic-time/monthly-route
Планетарный маршрут на месяц.

**Стоимость:** 5 кредитов

**Запрос:**
```json
{
  "birth_date": "15.08.1985",
  "city": "Кишинев",
  "month": 1,
  "year": 2024
}
```

#### POST /api/vedic-time/quarterly-route
Планетарный маршрут на квартал.

**Стоимость:** 10 кредитов

### 5. Система обучения (LMS)

#### GET /api/lessons
Получение списка доступных уроков.

**Ответ:**
```json
{
  "lessons": [
    {
      "id": "lesson_numerom_intro",
      "title": "Введение в NumerOM",
      "module": "Модуль 1: Основы",
      "points_required": 10,
      "user_has_access": true,
      "completion_status": "not_started",
      "duration_minutes": 45
    }
  ],
  "user_level": {
    "current_level": 1,
    "experience_points": 150,
    "lessons_completed": 2
  }
}
```

#### GET /api/lessons/{lesson_id}
Получение содержания урока.

**Стоимость:** 10 кредитов (при первом доступе)

#### POST /api/lessons/{lesson_id}/quiz
Отправка ответов квиза.

**Стоимость:** 1 кредит

**Запрос:**
```json
{
  "answers": ["a", "b", "c", "a", "b"],
  "time_spent_minutes": 5
}
```

**Ответ:**
```json
{
  "score": 80,
  "passed": true,
  "correct_answers": 4,
  "total_questions": 5,
  "experience_gained": 50,
  "lesson_completed": true
}
```

### 6. Платежи

#### POST /api/payments/create-checkout-session
Создание сессии оплаты Stripe.

**Запрос:**
```json
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

#### GET /api/payments/status/{transaction_id}
Проверка статуса платежа.

#### GET /api/payments/history
История платежей пользователя.

### 7. Кредиты

#### GET /api/credits/balance
Баланс кредитов пользователя.

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

#### GET /api/credits/transactions
История транзакций кредитов.

**Параметры:** `limit`, `offset`

### 8. Отчеты

#### POST /api/reports/html
Создание HTML отчета.

**Запрос:**
```json
{
  "selected_calculations": ["calc_id_1", "calc_id_2"],
  "include_vedic": true,
  "include_charts": true,
  "theme": "default"
}
```

**Ответ:**
```json
{
  "report_url": "/api/reports/download/report_uuid.html",
  "report_id": "report_uuid"
}
```

### 9. Квизы

#### GET /api/quiz/questions
Получение вопросов для теста самопознания.

**Параметры:** `count` (по умолчанию 10)

**Стоимость:** 1 кредит

**Ответ:**
```json
{
  "questions": [
    {
      "id": "vedic_1",
      "question": "Какой цвет лучше всего отражает вашу внутреннюю энергию?",
      "options": [
        {"text": "Огненно-красный", "value": 1},
        {"text": "Лунно-серебристый", "value": 2}
      ],
      "category": "vedic_colors"
    }
  ],
  "session_id": "quiz_session_uuid"
}
```

#### POST /api/quiz/submit
Отправка ответов теста.

**Запрос:**
```json
{
  "session_id": "quiz_session_uuid",
  "answers": [1, 2, 3, 1, 2, 3, 1, 2, 3, 1]
}
```

**Ответ:**
```json
{
  "score": 75,
  "dominant_numbers": [1, 3, 6],
  "personality_type": "Лидер-творец",
  "recommendations": [
    "Развивайте лидерские качества",
    "Используйте творческий потенциал",
    "Заботьтесь о гармонии в отношениях"
  ],
  "detailed_analysis": {
    "strengths": ["Уверенность", "Креативность"],
    "areas_for_growth": ["Терпение", "Дипломатия"]
  }
}
```

## Административные эндпоинты

### Управление пользователями

#### GET /api/admin/users
Список пользователей (только для админов).

**Параметры:** `page`, `limit`, `search`, `filter_by`

#### POST /api/admin/users/{user_id}/credits
Управление кредитами пользователя.

#### GET /api/admin/users/{user_id}/details
Детальная информация о пользователе.

### Управление контентом (суперадмины)

#### GET /api/admin/lessons
Список уроков для администрирования.

#### POST /api/admin/lessons
Создание нового урока.

#### PUT /api/admin/lessons/{lesson_id}
Редактирование урока.

#### POST /api/admin/consultations
Создание персональной консультации.

### Аналитика

#### GET /api/admin/analytics/overview
Общая аналитика системы.

#### GET /api/admin/analytics/payments
Аналитика платежей.

#### GET /api/admin/analytics/usage
Аналитика использования функций.

## Обработка ошибок

### Формат ошибок
```json
{
  "detail": "Описание ошибки",
  "error_code": "INSUFFICIENT_CREDITS",
  "error_data": {
    "required_credits": 5,
    "current_balance": 2
  }
}
```

### Типичные ошибки

#### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

#### 402 Payment Required
```json
{
  "detail": "Недостаточно кредитов для выполнения операции",
  "error_code": "INSUFFICIENT_CREDITS",
  "error_data": {
    "required_credits": 5,
    "current_balance": 2,
    "suggested_package": "monthly"
  }
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "birth_date"],
      "msg": "Invalid date format. Use DD.MM.YYYY",
      "type": "value_error"
    }
  ]
}
```

## Rate Limiting

### Лимиты по эндпоинтам
- **Регистрация/вход:** 5 запросов в минуту
- **Расчеты:** 10 запросов в минуту
- **Платежи:** 3 запроса в минуту
- **Общие запросы:** 100 запросов в минуту

### Заголовки лимитов
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642680000
```

## Webhook Endpoints

### Stripe Webhooks
```http
POST /api/payments/stripe-webhook
Content-Type: application/json
Stripe-Signature: t=1234567890,v1=...

{
  "type": "checkout.session.completed",
  "data": {
    "object": {
      "id": "cs_test_xxx",
      "metadata": {
        "user_id": "uuid4",
        "package_type": "monthly"
      }
    }
  }
}
```

## SDK и библиотеки

### JavaScript/TypeScript
```javascript
// Пример использования с axios
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://api.numerom.com',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

// Расчет персональных чисел
const calculatePersonalNumbers = async (birthDate) => {
  try {
    const response = await api.post('/api/numerology/personal-numbers', {
      birth_date: birthDate
    });
    return response.data;
  } catch (error) {
    if (error.response?.status === 402) {
      // Недостаточно кредитов
      throw new Error('Недостаточно кредитов');
    }
    throw error;
  }
};
```

### Python
```python
import requests

class NumeromAPI:
    def __init__(self, token, base_url="https://api.numerom.com"):
        self.token = token
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })
    
    def calculate_personal_numbers(self, birth_date):
        response = self.session.post(
            f'{self.base_url}/api/numerology/personal-numbers',
            json={'birth_date': birth_date}
        )
        response.raise_for_status()
        return response.json()
```

## OpenAPI/Swagger документация

Автоматически сгенерированная документация доступна по адресам:
- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`
- **OpenAPI JSON:** `/openapi.json`

## Версионирование API

### Текущая версия
- **Версия:** v1
- **Поддержка:** Активная
- **Изменения:** Обратно совместимые

### Планируемые версии
- **v2:** Улучшенная структура ответов
- **v3:** GraphQL поддержка

## Тестирование API

### Демо данные
Для тестирования доступны демо эндпоинты с префиксом `/demo`:
```http
POST /demo/api/numerology/personal-numbers
# Не требует аутентификации и кредитов
```

### Тестовая среда
- **URL:** `https://test-api.numerom.com`
- **Токены:** Тестовые токены с полным доступом
- **Данные:** Сбрасываются каждые 24 часа


