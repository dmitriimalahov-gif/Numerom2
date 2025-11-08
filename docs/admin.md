# Административные функции

## Обзор

Административная панель NUMEROM предоставляет мощные инструменты для управления пользователями, контентом, аналитикой и системными настройками. Доступ ограничен ролями суперадминистратора и администратора.

## Система ролей

### Роли в системе
```python
# Иерархия ролей:
1. Пользователь (is_premium: false)     # Базовый доступ
2. Премиум пользователь (is_premium: true)  # Расширенный доступ
3. Администратор (is_admin: true)       # Управление пользователями
4. Суперадминистратор (is_super_admin: true)  # Полный доступ
```

### Права доступа

#### Суперадминистратор
- ✅ Все функции администратора
- ✅ Управление обучающим контентом
- ✅ Загрузка и редактирование уроков
- ✅ Создание и управление квизами
- ✅ Управление персональными консультациями
- ✅ Системные настройки
- ✅ Создание других администраторов

#### Администратор  
- ✅ Просмотр списка пользователей
- ✅ Управление кредитами пользователей
- ✅ Базовая аналитика
- ❌ Управление контентом
- ❌ Системные настройки

## Главный интерфейс (AdminPanel.jsx)

### Структура панели администратора
```jsx
<Tabs defaultValue="users">
  <TabsList>
    <TabsTrigger value="users">Пользователи</TabsTrigger>
    <TabsTrigger value="analytics">Аналитика</TabsTrigger>
    <TabsTrigger value="lessons">Уроки</TabsTrigger>      {/* Только суперадмин */}
    <TabsTrigger value="materials">Материалы</TabsTrigger>  {/* Только суперадмин */}
    <TabsTrigger value="consultations">Консультации</TabsTrigger> {/* Только суперадмин */}
    <TabsTrigger value="settings">Настройки</TabsTrigger>   {/* Только суперадмин */}
  </TabsList>
</Tabs>
```

## Управление пользователями

### API для работы с пользователями

#### Получение списка пользователей
```http
GET /api/admin/users?page=1&limit=20&search=&filter_by=all
Authorization: Bearer <admin_token>
```

**Параметры запроса:**
- `page` - номер страницы (по умолчанию 1)
- `limit` - количество записей на странице (по умолчанию 20)
- `search` - поиск по email или имени
- `filter_by` - фильтр: "all", "premium", "active", "inactive"

**Ответ:**
```json
{
  "users": [
    {
      "id": "uuid4-string",
      "email": "user@example.com",
      "full_name": "Анна Смирнова",
      "birth_date": "15.08.1985",
      "city": "Москва",
      "is_premium": true,
      "is_admin": false,
      "is_super_admin": false,
      "credits_remaining": 125,
      "subscription_type": "monthly",
      "subscription_expires_at": "2024-02-15T10:30:00Z",
      "created_at": "2024-01-15T10:30:00Z",
      "last_login": "2024-01-20T14:22:00Z",
      "total_calculations": 45,
      "total_spent_credits": 75
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 12,
    "total_users": 245,
    "has_next": true,
    "has_previous": false
  },
  "statistics": {
    "total_users": 245,
    "premium_users": 89,
    "active_this_month": 156,
    "total_credits_in_system": 15420
  }
}
```

#### Управление кредитами пользователя
```http
POST /api/admin/users/{user_id}/credits
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "operation": "add",        // "add" или "subtract"
  "amount": 50,
  "reason": "Бонус за активность",
  "category": "admin_bonus"
}
```

**Ответ:**
```json
{
  "success": true,
  "user_id": "uuid4-string",
  "previous_balance": 25,
  "new_balance": 75,
  "transaction_id": "uuid4-string"
}
```

#### Изменение роли пользователя
```http
POST /api/admin/users/{user_id}/role
Authorization: Bearer <super_admin_token>
Content-Type: application/json

{
  "is_admin": true,
  "is_super_admin": false,
  "reason": "Назначение модератором"
}
```

#### Просмотр детальной информации о пользователе
```http
GET /api/admin/users/{user_id}/details
Authorization: Bearer <admin_token>
```

**Ответ:**
```json
{
  "user": {
    "id": "uuid4-string",
    "email": "user@example.com",
    "full_name": "Анна Смирнова",
    "birth_date": "15.08.1985",
    "registration_ip": "192.168.1.1",
    "last_activity": "2024-01-20T14:22:00Z",
    "subscription_history": [
      {
        "package_type": "monthly",
        "purchased_at": "2024-01-15T10:30:00Z",
        "amount": 9.99,
        "credits_received": 150
      }
    ]
  },
  "usage_statistics": {
    "total_calculations": 45,
    "calculations_by_type": {
      "personal_numbers": 15,
      "vedic_numerology": 12,
      "compatibility": 8,
      "time_calculations": 10
    },
    "lessons_viewed": 8,
    "quizzes_completed": 5,
    "last_calculation": "2024-01-20T14:22:00Z"
  },
  "credit_transactions": [
    {
      "id": "uuid4-string",
      "transaction_type": "debit",
      "amount": -1,
      "description": "Расчет совместимости",
      "category": "numerology",
      "created_at": "2024-01-20T14:22:00Z"
    }
  ]
}
```

## Управление обучающим контентом

### Система управления уроками

#### Получение списка уроков
```http
GET /api/admin/lessons
Authorization: Bearer <super_admin_token>
```

**Ответ:**
```json
{
  "lessons": [
    {
      "id": "lesson_numerom_intro",
      "title": "Введение в NumerOM",
      "module": "Модуль 1: Основы",
      "points_required": 10,
      "is_active": true,
      "students_enrolled": 156,
      "completion_rate": 78.5,
      "average_quiz_score": 85.2,
      "has_video": true,
      "has_pdf": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Создание нового урока
```http
POST /api/admin/lessons
Authorization: Bearer <super_admin_token>
Content-Type: multipart/form-data

{
  "title": "Новый урок по нумерологии",
  "module": "Модуль 2: Продвинутый уровень",
  "description": "Подробное изучение ведических принципов",
  "points_required": 15,
  "video_file": <video_file>,
  "pdf_file": <pdf_file>,
  "content": {
    "theory": {
      "introduction": "Введение в урок...",
      "main_concepts": "Основные концепции..."
    },
    "practical_tips": {
      "exercises": "Практические упражнения..."
    }
  }
}
```

#### Редактирование урока
```http
PUT /api/admin/lessons/{lesson_id}
Authorization: Bearer <super_admin_token>
Content-Type: application/json

{
  "title": "Обновленное название урока",
  "content": {
    "theory": {
      "updated_section": "Новая информация..."
    }
  },
  "exercises": [
    {
      "id": "new_exercise_1",
      "title": "Новое упражнение",
      "type": "reflection",
      "content": "Описание упражнения...",
      "instructions": ["Шаг 1", "Шаг 2", "Шаг 3"]
    }
  ]
}
```

### Управление квизами

#### Создание квиза для урока
```http
POST /api/admin/lessons/{lesson_id}/quiz
Authorization: Bearer <super_admin_token>
Content-Type: application/json

{
  "title": "Квиз по основам нумерологии",
  "questions": [
    {
      "question": "Что такое число души?",
      "options": [
        "a) Число из дня рождения",
        "b) Число из месяца рождения",
        "c) Число из года рождения",
        "d) Сумма всех цифр даты"
      ],
      "correct_answer": "a",
      "explanation": "Число души рассчитывается из дня рождения человека"
    }
  ],
  "passing_score": 70
}
```

### Управление персональными консультациями

#### Создание новой консультации
```http
POST /api/admin/consultations
Authorization: Bearer <super_admin_token>
Content-Type: multipart/form-data

{
  "title": "Персональная консультация: Планетарные энергии",
  "description": "Индивидуальный разбор планетарного влияния",
  "assigned_user_id": "uuid4-string",
  "cost_credits": 6667,
  "video_file": <video_file>,
  "pdf_file": <pdf_file>,
  "subtitles_file": <subtitles_file>
}
```

#### Просмотр консультаций
```http
GET /api/admin/consultations?user_id=&status=all
Authorization: Bearer <super_admin_token>
```

**Ответ:**
```json
{
  "consultations": [
    {
      "id": "uuid4-string",
      "title": "Персональная консультация: Планетарные энергии",
      "assigned_user_email": "user@example.com",
      "assigned_user_name": "Анна Смирнова",
      "cost_credits": 6667,
      "is_purchased": true,
      "purchased_at": "2024-01-18T15:30:00Z",
      "has_video": true,
      "has_pdf": true,
      "has_subtitles": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## Аналитика и отчеты

### Общая аналитика системы
```http
GET /api/admin/analytics/overview
Authorization: Bearer <admin_token>
```

**Ответ:**
```json
{
  "users": {
    "total_users": 245,
    "new_users_this_month": 23,
    "active_users_last_30_days": 156,
    "premium_users": 89,
    "conversion_rate": 36.3
  },
  "revenue": {
    "total_revenue": 2458.67,
    "revenue_this_month": 456.78,
    "average_revenue_per_user": 10.03,
    "most_popular_package": "monthly"
  },
  "usage": {
    "total_calculations": 12450,
    "calculations_this_month": 1234,
    "most_popular_calculation": "personal_numbers",
    "average_calculations_per_user": 50.8
  },
  "content": {
    "total_lessons": 15,
    "lessons_completed": 1456,
    "average_completion_rate": 73.2,
    "most_popular_lesson": "lesson_numerom_intro"
  }
}
```

### Аналитика платежей
```http
GET /api/admin/analytics/payments?period=30days
Authorization: Bearer <admin_token>
```

**Ответ:**
```json
{
  "period": "30days",
  "total_transactions": 67,
  "successful_transactions": 62,
  "failed_transactions": 5,
  "conversion_rate": 92.5,
  "revenue_by_package": {
    "one_time": {"count": 15, "revenue": 14.85},
    "monthly": {"count": 35, "revenue": 349.65},
    "annual": {"count": 12, "revenue": 799.2}
  },
  "daily_revenue": [
    {"date": "2024-01-01", "revenue": 29.97, "transactions": 3},
    {"date": "2024-01-02", "revenue": 66.6, "transactions": 2}
  ]
}
```

### Аналитика использования функций
```http
GET /api/admin/analytics/usage?period=7days
Authorization: Bearer <admin_token>
```

**Ответ:**
```json
{
  "period": "7days",
  "calculations_by_type": {
    "personal_numbers": 234,
    "vedic_numerology": 187,
    "compatibility": 156,
    "time_calculations": 123,
    "pythagorean_square": 98
  },
  "peak_usage_hours": [
    {"hour": 14, "calculations": 45},
    {"hour": 20, "calculations": 42},
    {"hour": 10, "calculations": 38}
  ],
  "user_retention": {
    "day_1": 89.5,
    "day_7": 67.2,
    "day_30": 34.8
  }
}
```

## Система логирования

### Логирование административных действий
```python
class AdminAction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_user_id: str              # ID администратора
    admin_email: str                # Email для удобства
    action_type: str                # Тип действия
    target_type: str                # Тип целевого объекта
    target_id: str                  # ID целевого объекта
    description: str                # Описание действия
    details: Dict[str, Any] = {}    # Дополнительные детали
    ip_address: str                 # IP адрес
    user_agent: str                 # Браузер/клиент
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Примеры действий:
action_types = [
    "user_credits_modified",        # Изменение кредитов пользователя
    "user_role_changed",           # Изменение роли пользователя
    "lesson_created",              # Создание урока
    "lesson_modified",             # Изменение урока
    "consultation_created",        # Создание консультации
    "system_settings_changed"     # Изменение системных настроек
]
```

### API для просмотра логов
```http
GET /api/admin/logs?page=1&limit=50&action_type=&admin_id=&date_from=&date_to=
Authorization: Bearer <super_admin_token>
```

**Ответ:**
```json
{
  "logs": [
    {
      "id": "uuid4-string",
      "admin_email": "admin@numerom.com",
      "action_type": "user_credits_modified",
      "target_type": "user",
      "target_id": "user-uuid",
      "description": "Добавлено 50 кредитов пользователю user@example.com",
      "details": {
        "previous_balance": 25,
        "new_balance": 75,
        "reason": "Бонус за активность"
      },
      "ip_address": "192.168.1.100",
      "created_at": "2024-01-20T14:22:00Z"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 23,
    "total_logs": 1150
  }
}
```

## Системные настройки

### Управление настройками (только суперадмин)
```http
GET /api/admin/settings
Authorization: Bearer <super_admin_token>
```

**Ответ:**
```json
{
  "credit_costs": {
    "personal_numbers": 1,
    "vedic_numerology": 1,
    "compatibility": 1,
    "time_calculations": 1,
    "lesson_viewing": 10
  },
  "payment_packages": {
    "one_time": {"price": 0.99, "credits": 10},
    "monthly": {"price": 9.99, "credits": 150},
    "annual": {"price": 66.6, "credits": 1000}
  },
  "system_limits": {
    "max_file_size_mb": 100,
    "max_video_duration_minutes": 120,
    "max_lessons_per_module": 20
  },
  "features": {
    "registration_enabled": true,
    "payments_enabled": true,
    "demo_mode": false,
    "maintenance_mode": false
  }
}
```

### Обновление настроек
```http
PUT /api/admin/settings
Authorization: Bearer <super_admin_token>
Content-Type: application/json

{
  "credit_costs": {
    "personal_numbers": 2,  // Увеличена стоимость
    "lesson_viewing": 8     // Снижена стоимость урока
  },
  "features": {
    "maintenance_mode": true  // Включен режим обслуживания
  }
}
```

## Управление файлами

### Загрузка файлов для уроков
```http
POST /api/admin/upload/lesson-video
Authorization: Bearer <super_admin_token>
Content-Type: multipart/form-data

{
  "lesson_id": "lesson_id",
  "video_file": <video_file>,
  "title": "Основы нумерологии - Часть 1"
}
```

### Управление дополнительными материалами
```http
POST /api/admin/materials/upload
Authorization: Bearer <super_admin_token>
Content-Type: multipart/form-data

{
  "lesson_id": "lesson_id",
  "title": "Дополнительные упражнения",
  "description": "PDF с практическими заданиями",
  "material_type": "pdf",
  "file": <pdf_file>
}
```

### Просмотр статистики файлов
```http
GET /api/admin/files/statistics
Authorization: Bearer <super_admin_token>
```

**Ответ:**
```json
{
  "total_files": 127,
  "total_size_gb": 15.7,
  "files_by_type": {
    "video": {"count": 45, "size_gb": 12.3},
    "pdf": {"count": 67, "size_gb": 2.8},
    "subtitles": {"count": 15, "size_gb": 0.6}
  },
  "largest_files": [
    {
      "filename": "advanced_lesson_video.mp4",
      "size_mb": 456.7,
      "lesson_title": "Продвинутая ведическая нумерология"
    }
  ]
}
```

## Безопасность и аудит

### Двухфакторная аутентификация для админов
```http
POST /api/admin/enable-2fa
Authorization: Bearer <admin_token>
```

### Сессии администраторов
```http
GET /api/admin/active-sessions
Authorization: Bearer <super_admin_token>
```

**Ответ:**
```json
{
  "active_sessions": [
    {
      "admin_email": "admin@numerom.com",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "login_time": "2024-01-20T09:00:00Z",
      "last_activity": "2024-01-20T14:22:00Z",
      "session_id": "sess_uuid"
    }
  ]
}
```

### Принудительный выход администратора
```http
POST /api/admin/revoke-session
Authorization: Bearer <super_admin_token>
Content-Type: application/json

{
  "session_id": "sess_uuid",
  "reason": "Подозрительная активность"
}
```

## Резервное копирование и восстановление

### Создание резервной копии данных
```http
POST /api/admin/backup/create
Authorization: Bearer <super_admin_token>
Content-Type: application/json

{
  "backup_type": "full",  // "full", "users_only", "content_only"
  "include_files": true,
  "compress": true
}
```

### Список резервных копий
```http
GET /api/admin/backups
Authorization: Bearer <super_admin_token>
```

**Ответ:**
```json
{
  "backups": [
    {
      "id": "backup_uuid",
      "backup_type": "full",
      "file_size_gb": 18.5,
      "created_at": "2024-01-20T02:00:00Z",
      "status": "completed",
      "download_url": "/api/admin/backups/download/backup_uuid"
    }
  ]
}
```

## Мониторинг производительности

### Системные метрики
```http
GET /api/admin/system/metrics
Authorization: Bearer <super_admin_token>
```

**Ответ:**
```json
{
  "server": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 34.5,
    "uptime_hours": 168
  },
  "database": {
    "total_documents": 15420,
    "database_size_gb": 2.3,
    "query_performance_ms": 12.5,
    "connections": 15
  },
  "application": {
    "active_users": 67,
    "requests_per_minute": 145,
    "error_rate": 0.2,
    "average_response_time_ms": 250
  }
}
```

## Уведомления и алерты

### Настройка уведомлений
```http
POST /api/admin/notifications/settings
Authorization: Bearer <super_admin_token>
Content-Type: application/json

{
  "email_notifications": {
    "new_user_registration": true,
    "payment_failures": true,
    "system_errors": true,
    "daily_reports": true
  },
  "alert_thresholds": {
    "high_cpu_usage": 80,
    "low_disk_space_gb": 5,
    "error_rate_percent": 5
  }
}
```

### Просмотр уведомлений
```http
GET /api/admin/notifications?unread_only=true
Authorization: Bearer <admin_token>
```

## Автоматизация задач

### Планировщик задач
```python
# Автоматические задачи:
scheduled_tasks = [
    "daily_backup",              # Ежедневное резервное копирование
    "weekly_analytics_report",   # Еженедельный отчет аналитики  
    "monthly_user_cleanup",      # Очистка неактивных пользователей
    "subscription_renewal",      # Обработка продления подписок
    "credit_expiration_check"   # Проверка истечения кредитов
]
```

### Ручной запуск задач
```http
POST /api/admin/tasks/run
Authorization: Bearer <super_admin_token>
Content-Type: application/json

{
  "task_name": "weekly_analytics_report",
  "parameters": {
    "email_recipients": ["admin@numerom.com"],
    "include_detailed_breakdown": true
  }
}
```

## Интеграции и экспорт данных

### Экспорт пользователей
```http
GET /api/admin/export/users?format=csv&filters=premium_only
Authorization: Bearer <admin_token>
```

### Экспорт аналитики
```http
GET /api/admin/export/analytics?period=monthly&format=excel
Authorization: Bearer <admin_token>
```

## Планируемые улучшения

### Дополнительные функции
1. **Машинное обучение** - прогнозирование поведения пользователей
2. **A/B тестирование** - оптимизация интерфейса и контента
3. **Чат-поддержка** - интегрированная система помощи
4. **API для партнеров** - расширение экосистемы

### Улучшения безопасности
1. **SSO интеграция** - единый вход для корпоративных клиентов
2. **RBAC система** - более гранулярные права доступа
3. **Аудит логи** - детальное отслеживание всех действий
4. **Compliance** - соответствие GDPR и другим регуляциям


