# 🗺️ Карта рефакторинга Numerom Backend

**Дата начала:** 2025-10-09
**Цель:** Рефакторинг монолитного server.py (4806 строк) в модульную Clean Architecture
**Статус:** 🚧 В процессе

---

## 📊 Общая статистика

| Метрика | Старый backend | Новый backend | Прогресс |
|---------|----------------|---------------|----------|
| Всего строк | 4,806 | 0 | 0% |
| Файлов | 9 | 0 | 0% |
| Эндпоинтов | 122 | 0 | 0% |
| DB операций | ~280 | 0 | 0% |

---

## 🎯 План рефакторинга (25 этапов)

### Фаза 1: Инфраструктура (Этапы 1-5)
- [ ] Этап 1: Создать структуру папок
- [ ] Этап 2: Настроить конфигурацию (config.py)
- [ ] Этап 3: Вынести security логику (core/security.py)
- [ ] Этап 4: Создать database connection (database/connection.py)
- [ ] Этап 5: Создать базовый репозиторий (database/repositories/base.py)

### Фаза 2: Модели и схемы (Этапы 6-7)
- [ ] Этап 6: Разбить models.py на домены
- [ ] Этап 7: Создать Pydantic схемы для валидации

### Фаза 3: Репозитории (Этапы 8-15)
- [ ] Этап 8: UserRepository
- [ ] Этап 9: CreditRepository
- [ ] Этап 10: PaymentRepository
- [ ] Этап 11: NumerologyRepository
- [ ] Этап 12: LessonRepository
- [ ] Этап 13: ConsultationRepository
- [ ] Этап 14: MaterialRepository
- [ ] Этап 15: FileRepository

### Фаза 4: Сервисы (Этапы 16-22)
- [ ] Этап 16: AuthService
- [ ] Этап 17: CreditService
- [ ] Этап 18: PaymentService
- [ ] Этап 19: NumerologyService
- [ ] Этап 20: LessonService
- [ ] Этап 21: ConsultationService
- [ ] Этап 22: AdminService

### Фаза 5: API Роутеры (Этапы 23-25)
- [ ] Этап 23: Создать роутеры для всех доменов
- [ ] Этап 24: Создать main.py и подключить роутеры
- [ ] Этап 25: Тестирование и валидация

---

## 📝 Детальная карта рефакторинга server.py

### Легенда
- ✅ Завершено
- 🚧 В процессе
- ⏳ Запланировано
- ❌ Отменено

---

## Этап 1: Создание структуры папок ⏳

**Статус:** Запланировано
**Дата:** 2025-10-09

### Создаваемые папки:
```
backend_clean/
├── core/                   # Ядро приложения
├── database/              # Слой работы с БД
│   └── repositories/      # Паттерн Repository
├── models/                # Pydantic модели
├── services/              # Бизнес-логика
├── api/                   # API эндпоинты
│   └── v1/               # Версия API
├── utils/                 # Утилиты
├── tests/                 # Тесты
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── docs/                  # Документация
```

**Зависимости:** Нет
**Время:** 10 минут

---

## Этап 2: Конфигурация (core/config.py) ⏳

**Статус:** Запланировано

### Исходный код (backend/server.py)

| Строки | Что переносим | Куда |
|--------|---------------|------|
| 50-56 | Загрузка .env и MongoDB connection | `core/config.py` |
| 63-72 | Stripe configuration и payment packages | `core/config.py` |
| 74-79 | Subscription credits | `core/config.py` |
| 86-95 | Upload paths | `core/config.py` |

### Новый файл: `core/config.py`

**Содержимое:**
```python
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    # MongoDB
    MONGO_URL: str
    MONGODB_DATABASE: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Stripe
    STRIPE_PUBLIC_KEY: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # App
    APP_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    # Super Admin
    SUPER_ADMIN_EMAIL: str
    SUPER_ADMIN_PASSWORD: str

    # Upload paths
    UPLOAD_ROOT: Path = Path("uploads")

    class Config:
        env_file = ".env"

settings = Settings()

# Payment packages
PAYMENT_PACKAGES = {
    'one_time': 0.99,
    'monthly': 9.99,
    'annual': 66.6,
    'master_consultation': 666.0
}

# Subscription credits
SUBSCRIPTION_CREDITS = {
    'one_time': 10,
    'monthly': 150,
    'annual': 1000,
    'master_consultation': 10000
}
```

**Изменения в старом коде:** Удалить строки 50-95

---

## Этап 3: Security (core/security.py) ⏳

**Статус:** Запланировано

### Исходный код (backend/auth.py)

| Строки | Что переносим | Куда |
|--------|---------------|------|
| 1-32 | Все импорты и функции для JWT/паролей | `core/security.py` |
| 34-50 | get_current_user | `core/security.py` |
| 53-76 | get_current_user_full | `core/security.py` |

### Новый файл: `core/security.py`

**Статус:** ⏳ Создать

---

## Этап 4: Database Connection (database/connection.py) ⏳

**Статус:** Запланировано

### Исходный код (backend/server.py)

| Строки | Что переносим | Куда |
|--------|---------------|------|
| 54-56 | MongoDB client и db | `database/connection.py` |
| 114-116 | Shutdown handler | `database/connection.py` |

### Новый файл: `database/connection.py`

**Содержимое:**
```python
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from core.config import settings

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db = None

    async def connect(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URL)
        self.db = self.client[settings.MONGODB_DATABASE]
        print("✅ Connected to MongoDB")

    async def disconnect(self):
        if self.client:
            self.client.close()
            print("✅ Disconnected from MongoDB")

db_instance = Database()

async def get_db():
    return db_instance.db
```

---

## Этап 5: Base Repository (database/repositories/base.py) ⏳

**Статус:** Запланировано

### Концепция

Создать базовый класс для всех репозиториев с общими CRUD операциями.

### Новый файл: `database/repositories/base.py`

**Содержимое:**
```python
from typing import List, Dict, Any, Optional
from abc import ABC

class BaseRepository(ABC):
    collection_name: str = None

    def __init__(self, db):
        self.db = db
        if not self.collection_name:
            raise ValueError("collection_name must be set")
        self.collection = db[self.collection_name]

    async def find_one(self, query: Dict) -> Optional[Dict]:
        return await self.collection.find_one(query)

    async def find_many(self, query: Dict, limit: int = 100) -> List[Dict]:
        return await self.collection.find(query).limit(limit).to_list(limit)

    async def create(self, data: Dict) -> Dict:
        result = await self.collection.insert_one(data)
        return await self.find_one({'_id': result.inserted_id})

    async def update(self, query: Dict, update_data: Dict) -> bool:
        result = await self.collection.update_one(query, {'$set': update_data})
        return result.modified_count > 0

    async def delete(self, query: Dict) -> bool:
        result = await self.collection.delete_one(query)
        return result.deleted_count > 0

    async def count(self, query: Dict) -> int:
        return await self.collection.count_documents(query)
```

**Зависимости:** Этап 4 (Database Connection)

---

## Этап 6: Разбить models.py ⏳

**Статус:** Запланировано

### Исходный код (backend/models.py - 512 строк)

| Строки | Модель | Новый файл |
|--------|--------|------------|
| 7-73 | User, UserCreate, UserResponse, LoginRequest, TokenResponse | `models/user.py` |
| 76-92 | PaymentTransaction, PaymentRequest | `models/payment.py` |
| 94-141 | NumerologyCalculation, PersonalNumbers, etc. | `models/numerology.py` |
| 150-176 | VideoLesson, UserProgress, UserLevel | `models/lesson.py` |
| 196-226 | PersonalConsultation, ConsultationPurchase | `models/consultation.py` |
| 229-254 | CreditTransaction, CREDIT_COSTS | `models/credit.py` |
| 256-270 | QuizQuestion, QuizResult | `models/quiz.py` |
| 297-302 | AdminUser | `models/admin.py` |

**Задачи:**
1. Создать 8 файлов в `models/`
2. Перенести соответствующие модели
3. Обновить импорты в `models/__init__.py`

---

## Этап 8: UserRepository ⏳

**Статус:** Запланировано

### Исходный код (backend/server.py)

**Операции с users коллекцией:**

| Строки | Операция | Метод в UserRepository |
|--------|----------|------------------------|
| 138 | `db.users.find_one({'id': user_id})` | `find_by_id(user_id)` |
| 146 | `db.users.update_one({'id': user_id}, {'$inc': {...}})` | `increment_credits(user_id, amount)` |
| 177 | `db.users.find_one({'email': email})` | `find_by_email(email)` |
| 203 | `db.users.insert_one(user.dict())` | `create(user_data)` |
| 217 | `db.users.update_one({'email': email}, ...)` | `update_last_login(email)` |
| 299, 308, 343, 348 | `db.users.update_one({'id': user_id}, {'$inc': ...})` | `increment_credits(user_id, amount)` |
| 1650 | `db.users.find({}).to_list(length=None)` | `find_all()` |
| 1686 | `db.users.update_one({'id': user_id}, ...)` | `update(user_id, data)` |
| 1725 | `db.users.delete_one({'id': user_id})` | `delete(user_id)` |

### Новый файл: `database/repositories/user_repository.py`

**Методы:**
```python
class UserRepository(BaseRepository):
    collection_name = 'users'

    async def find_by_id(self, user_id: str) -> Optional[Dict]
    async def find_by_email(self, email: str) -> Optional[Dict]
    async def exists_by_email(self, email: str) -> bool
    async def create(self, user_data: Dict) -> Dict
    async def update(self, user_id: str, data: Dict) -> bool
    async def delete(self, user_id: str) -> bool
    async def increment_credits(self, user_id: str, amount: int) -> bool
    async def update_last_login(self, email: str) -> bool
    async def find_all(self) -> List[Dict]
    async def update_subscription(self, user_id: str, subscription_data: Dict) -> bool
```

**Затронутые строки в server.py:** 138, 146, 177, 203, 217, 299, 308, 343, 348, 402, 429, 567, 606, 665, 706, 742, 767, 1631, 1650, 1686, 1713, 1725, 2107, 2683, 2778, 2783, 2897, 2902, 2942, 2949, 2961, 2975

---

## Этап 9: CreditRepository ⏳

**Статус:** Запланировано

### Исходный код (backend/server.py)

| Строки | Операция | Метод в CreditRepository |
|--------|----------|--------------------------|
| 134 | `db.credit_transactions.insert_one(...)` | `create_transaction(data)` |
| 158-160 | `db.credit_transactions.find(...).sort(...).skip(...).limit(...)` | `find_by_user(user_id, limit, offset)` |
| 171 | `db.credit_transactions.count_documents(...)` | `count_by_user(user_id)` |

### Новый файл: `database/repositories/credit_repository.py`

**Методы:**
```python
class CreditRepository(BaseRepository):
    collection_name = 'credit_transactions'

    async def create_transaction(self, data: Dict) -> Dict
    async def find_by_user(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict]
    async def count_by_user(self, user_id: str) -> int
```

**Затронутые строки:** 134, 158-171

---

## Этап 16: AuthService ⏳

**Статус:** Запланировано

### Исходный код (backend/server.py)

**Эндпоинты для рефакторинга:**

| Строки | Эндпоинт | Метод сервиса |
|--------|----------|---------------|
| 175-206 | POST `/auth/register` | `register_user(user_data)` |
| 208-233 | POST `/auth/login` | `login(credentials)` |

### Новый файл: `services/auth_service.py`

**Содержимое:**
```python
from database.repositories.user_repository import UserRepository
from core.security import get_password_hash, verify_password, create_access_token
from models.user import UserCreate, LoginRequest, TokenResponse

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register_user(self, user_data: UserCreate) -> TokenResponse:
        # Логика регистрации (строки 175-206)
        pass

    async def login(self, credentials: LoginRequest) -> TokenResponse:
        # Логика входа (строки 208-233)
        pass
```

**Затронутые строки:** 175-233

---

## Этап 23: API Роутеры ⏳

**Статус:** Запланировано

### План создания роутеров

| Файл роутера | Эндпоинты | Строки в server.py |
|--------------|-----------|-------------------|
| `api/v1/auth.py` | 3 эндпоинта | 175-233 |
| `api/v1/credits.py` | 2 эндпоинта | 152-172 |
| `api/v1/payments.py` | 5 эндпоинтов | 235-370 |
| `api/v1/users.py` | 8 эндпоинтов | 2942-2976 |
| `api/v1/numerology.py` | 15 эндпоинтов | 390-2900 |
| `api/v1/lessons.py` | 25 эндпоинтов | 820-2050 |
| `api/v1/consultations.py` | 15 эндпоинтов | 2070-2680 |
| `api/v1/materials.py` | 12 эндпоинтов | 1440-1850 |
| `api/v1/files.py` | 20 эндпоинтов | 1870-4250 |
| `api/v1/admin.py` | 14 эндпоинтов | 1390-1780 |

---

## 📈 Трекинг прогресса

### Метрики завершения

```
Фаза 1 (Инфраструктура):  0/5   (0%)
Фаза 2 (Модели):          0/2   (0%)
Фаза 3 (Репозитории):     0/8   (0%)
Фаза 4 (Сервисы):         0/7   (0%)
Фаза 5 (Роутеры):         0/3   (0%)

Общий прогресс:           0/25  (0%)
```

---

## 🔄 История изменений

### 2025-10-09
- ✅ Создана структура папок backend_clean
- ✅ Создан REFACTORING_MAP.md
- 🚧 Начата фаза 1 (Инфраструктура)

---

## 📚 Справочная информация

### Количество операций по коллекциям

| Коллекция | Операций | Приоритет |
|-----------|----------|-----------|
| users | 48 | Высокий |
| credit_transactions | 5 | Высокий |
| payment_transactions | 8 | Высокий |
| video_lessons | 12 | Средний |
| uploaded_files | 18 | Средний |
| personal_consultations | 10 | Средний |
| consultation_purchases | 6 | Средний |
| numerology_calculations | 5 | Низкий |
| materials | 12 | Низкий |
| Остальные | ~150 | Низкий |

**Всего операций:** ~280

---

## ⚠️ Важные замечания

1. **Не удаляем старый backend** - работаем параллельно
2. **Каждый этап тестируем** перед переходом к следующему
3. **Документируем все изменения** в этом файле
4. **Используем Git** для отслеживания изменений
5. **Backward compatibility** - API должен остаться совместимым

---

## 🎯 Следующий шаг

**Этап 2:** Создать `core/config.py` и вынести конфигурацию
