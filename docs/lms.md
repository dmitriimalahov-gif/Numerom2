# Система обучения (LMS)

## Обзор

Learning Management System (LMS) в NUMEROM предоставляет комплексную образовательную платформу с интерактивными уроками, квизами, челленджами и системой отслеживания прогресса.

## Архитектура системы

### Backend компоненты

#### lesson_system.py - Ядро системы обучения
```python
# Основные классы:
- Lesson          # Урок с видео, PDF, упражнениями
- Quiz            # Квиз с вопросами и ответами
- Challenge       # Многодневный вызов
- HabitTracker    # Трекер привычек
- Exercise        # Интерактивное упражнение
```

#### materials_manager.py - Управление контентом
```python
# Функции:
- Загрузка PDF и видеофайлов
- Связывание материалов с уроками
- Контроль доступа к файлам
- Управление метаданными
```

### Frontend компоненты

#### LearningSystem.jsx - Главный интерфейс обучения
#### CustomLessonViewer.jsx - Просмотр уроков
#### EnhancedVideoViewer.jsx - Видеоплеер с функциями
#### Quiz.jsx - Интерактивные квизы

## Модель урока (Lesson)

### Структура урока
```python
class Lesson(BaseModel):
    id: str                           # Уникальный идентификатор
    title: str                        # Название урока
    module: str                       # Модуль (например, "Модуль 1: Основы")
    content: Dict[str, Any]           # Теоретическое содержание
    video_path: Optional[str]         # Путь к видеофайлу
    pdf_path: Optional[str]           # Основной PDF материал
    additional_pdfs: List[Dict]       # Дополнительные PDF файлы
    exercises: List[Exercise]         # Практические упражнения
    quiz: Optional[Quiz]              # Квиз для проверки знаний
    challenges: List[Challenge]       # Связанные челленджи
    habit_tracker: Optional[HabitTracker]  # Трекер привычек
    points_required: int = 0          # Стоимость доступа в кредитах
```

### Содержание урока (content)
```python
content = {
    "theory": {
        "what_is_numerology": "Описание нумерологии...",
        "cosmic_ship_story": "История космического корабля...",
        "planets_and_numbers": "Соответствие планет и чисел...",
        "three_states": "Три состояния энергии..."
    },
    "practical_tips": {
        "basic_calculations": "Основные расчеты...",
        "how_to_use": "Как использовать нумерологию..."
    }
}
```

## Первый урок - "История космического корабля"

### Концепция
Метафора космического корабля для объяснения планетарных энергий:

```python
# Роли планет в космическом корабле:
СОЛНЦЕ (1) - создание идеи корабля, лидерство, вдохновение команды
ЛУНА (2) - обустройство уюта, взаимоотношения в команде
ЮПИТЕР (3) - технологии, образование, банковская система
РАХУ (4) - переворот системы, искусственный интеллект, инновации
МЕРКУРИЙ (5) - расширение, покорение галактик, коммуникации
ВЕНЕРА (6) - красота, комфорт, развлечения, эстетика
КЕТУ (7) - легкость, чудеса, духовность, отрешенность
САТУРН (8) - порядок, контроль, регламенты, дисциплина
МАРС (9) - спорт, справедливость, военные действия, управление
АНУГРАХА (0) - потенциал развития или разрушения
```

### Упражнения в первом уроке

#### 1. "История космического корабля"
```python
Exercise(
    id="ex_cosmic_ship",
    title="История космического корабля",
    type="reflection",
    content="Представьте космический корабль...",
    instructions=[
        "Прочитайте описание каждой планеты",
        "Определите резонирующие планеты", 
        "Запишите свои ощущения",
        "Подумайте о проявлениях в жизни"
    ],
    expected_outcome="Понимание планетарных энергий и их влияния"
)
```

#### 2. "Базовый анализ даты рождения"
```python
Exercise(
    id="ex_birth_date_analysis", 
    title="Базовый анализ даты рождения",
    type="calculation",
    content="Научитесь рассчитывать основные числа...",
    instructions=[
        "Запишите свою дату рождения",
        "Рассчитайте число души",
        "Рассчитайте число судьбы",
        "Найдите соответствие с планетами"
    ]
)
```

## Система квизов (Quiz)

### Структура квиза
```python
class Quiz(BaseModel):
    id: str                           # Идентификатор квиза
    title: str                        # Название
    questions: List[Dict[str, Any]]   # Список вопросов
    correct_answers: List[str]        # Правильные ответы
    explanations: List[str]           # Объяснения к ответам
```

### Пример квиза
```python
intro_quiz = Quiz(
    id="quiz_intro_1",
    title="Введение в нумерологию",
    questions=[
        {
            "question": "Что изучает нумерология?",
            "options": [
                "a) Энергетическое влияние чисел",
                "b) Магию камней",
                "c) Гадание по картам", 
                "d) Астрологию"
            ]
        },
        {
            "question": "Какая планета соответствует числу 1?",
            "options": [
                "a) Луна",
                "b) Солнце",
                "c) Марс",
                "d) Юпитер"
            ]
        }
    ],
    correct_answers=["a", "b"],
    explanations=[
        "Нумерология изучает энергетическое влияние чисел на жизнь",
        "Число 1 соответствует Солнцу - энергии лидерства"
    ]
)
```

## Система челленджей (Challenge)

### Структура челленджа
```python
class Challenge(BaseModel):
    id: str                           # Идентификатор
    title: str                        # Название челленджа
    description: str                  # Описание цели
    duration_days: int                # Продолжительность в днях
    daily_tasks: List[Dict[str, Any]] # Задания по дням
    completion_tracking: Dict[str, bool] = {}  # Отслеживание выполнения
```

### Пример: "Челлендж энергии Солнца" (7 дней)

#### День 1: Осознание своей силы
```python
{
    "day": 1,
    "title": "Осознание своей силы",
    "tasks": [
        "Напишите список своих сильных сторон и достижений",
        "Осознайте, в чём ваша главная сила",
        "Проговаривайте аффирмацию: 'Я – источник силы и света'"
    ]
}
```

#### День 4: Управление энергией  
```python
{
    "day": 4,
    "title": "Управление энергией",
    "tasks": [
        "Проведите 10-15 минут на солнце утром",
        "Визуализируйте реализацию своих целей",
        "Впитывайте солнечную энергию осознанно"
    ]
}
```

## Трекер привычек (HabitTracker)

### Структура трекера
```python
class HabitTracker(BaseModel):
    id: str                           # Идентификатор
    user_id: str                      # ID пользователя
    planet_habits: Dict[str, List[Dict]] # Привычки по планетам
    daily_completions: Dict[str, Dict[str, bool]] # Ежедневное выполнение
```

### Привычки для энергии Солнца
```python
sun_habits = [
    {
        "habit": "Утренняя аффирмация или медитация",
        "description": "Ежедневная практика укрепления уверенности"
    },
    {
        "habit": "Осознание лидерских качеств", 
        "description": "Анализ проявления лидерства в течение дня"
    },
    {
        "habit": "Проявление инициативы",
        "description": "Активные действия и принятие ответственности"
    },
    {
        "habit": "Вечернее подведение итогов",
        "description": "Рефлексия достижений дня"
    }
]
```

## Прогресс пользователя

### UserProgress модель
```python
class UserProgress(BaseModel):
    id: str                           # Идентификатор записи
    user_id: str                      # ID пользователя
    lesson_id: str                    # ID урока
    completed: bool = False           # Завершен ли урок
    completion_date: Optional[datetime] = None
    watch_time_minutes: int = 0       # Время просмотра видео
    quiz_score: Optional[int] = None  # Оценка за квиз
    created_at: datetime
```

### UserLevel модель
```python
class UserLevel(BaseModel):
    id: str                           # Идентификатор
    user_id: str                      # ID пользователя  
    current_level: int = 1            # Текущий уровень (1-10)
    experience_points: int = 0        # Очки опыта
    lessons_completed: int = 0        # Количество завершенных уроков
    last_activity: datetime           # Последняя активность
```

## API Endpoints

### 1. Получение доступных уроков
```http
GET /api/lessons
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "lessons": [
    {
      "id": "lesson_numerom_intro",
      "title": "Введение в NumerOM",
      "module": "Модуль 1: Основы",
      "points_required": 5,
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

### 2. Получение содержания урока
```http
GET /api/lessons/{lesson_id}
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "lesson": {
    "id": "lesson_numerom_intro",
    "title": "Введение в NumerOM",
    "content": {
      "theory": { ... },
      "practical_tips": { ... }
    },
    "video_url": "/api/lessons/video/lesson_numerom_intro",
    "exercises": [ ... ],
    "quiz": { ... },
    "challenges": [ ... ]
  },
  "user_progress": {
    "completed": false,
    "watch_time_minutes": 15,
    "quiz_score": null
  }
}
```

### 3. Отправка ответов квиза
```http
POST /api/lessons/{lesson_id}/quiz
Authorization: Bearer <token>
Content-Type: application/json

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
  "explanations": [
    "Правильно! Нумерология изучает влияние чисел...",
    "Верно! Число 1 соответствует Солнцу..."
  ],
  "experience_gained": 50,
  "lesson_completed": true
}
```

### 4. Обновление прогресса челленджа
```http
POST /api/challenges/{challenge_id}/progress
Authorization: Bearer <token>
Content-Type: application/json

{
  "day": 1,
  "completed_tasks": [
    "Написал список сильных сторон",
    "Определил главную силу",
    "Проговорил аффирмацию"
  ]
}
```

### 5. Обновление трекера привычек
```http
POST /api/habit-tracker/{tracker_id}/update
Authorization: Bearer <token>
Content-Type: application/json

{
  "date": "2024-01-15",
  "habits": {
    "Утренняя аффирмация или медитация": true,
    "Осознание лидерских качеств": true,
    "Проявление инициативы": false,
    "Вечернее подведение итогов": true
  }
}
```

## Стоимость в кредитах

| Операция | Стоимость |
|----------|-----------|
| Доступ к уроку | 10 кредитов |
| Прохождение квиза | 1 кредит |
| Участие в челлендже | 5 кредитов |
| Доступ к материалам | 1 кредит |

## Система геймификации

### Опыт и уровни
```python
# Опыт за активности:
lesson_completion = 100      # За завершение урока
quiz_passed = 50            # За успешное прохождение квиза
challenge_day = 20          # За день в челлендже
habit_completed = 10        # За выполнение привычки
exercise_done = 30          # За выполнение упражнения

# Уровни:
level_thresholds = {
    1: 0,      # Новичок
    2: 200,    # Ученик
    3: 500,    # Практик
    4: 1000,   # Исследователь
    5: 2000,   # Знаток
    6: 3500,   # Эксперт
    7: 5500,   # Мастер
    8: 8000,   # Гуру
    9: 12000,  # Учитель
    10: 18000  # Мудрец
}
```

### Достижения (будущие)
```python
achievements = [
    "Первые шаги",          # Завершил первый урок
    "Знаток теории",        # Прошел 5 квизов
    "Борец с привычками",   # 7 дней трекера подряд
    "Исследователь чисел",  # Завершил модуль 1
    "Мастер расчетов",      # Выполнил все упражнения
]
```

## Административные функции

### Создание уроков (Суперадмин)
```http
POST /api/admin/lessons
Authorization: Bearer <token>
Content-Type: multipart/form-data

{
  "title": "Новый урок",
  "module": "Модуль 2",
  "content": { ... },
  "video_file": <file>,
  "pdf_file": <file>,
  "points_required": 10
}
```

### Редактирование контента
```http
PUT /api/admin/lessons/{lesson_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Обновленное название",
  "content": { ... },
  "exercises": [ ... ],
  "quiz": { ... }
}
```

### Просмотр статистики
```http
GET /api/admin/lessons/statistics
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "total_lessons": 15,
  "total_students": 245,
  "completion_rate": 67.5,
  "popular_lessons": [
    {
      "lesson_id": "lesson_numerom_intro",
      "title": "Введение в NumerOM",
      "completions": 180,
      "average_score": 85.2
    }
  ],
  "user_engagement": {
    "daily_active_users": 45,
    "weekly_active_users": 123,
    "average_session_time": 25.5
  }
}
```

## Файловая система

### Структура хранения
```
/app/uploads/lessons/
├── videos/
│   ├── lesson_numerom_intro.mp4
│   └── lesson_advanced_calculations.mp4
├── pdfs/
│   ├── intro_theory.pdf
│   ├── calculations_guide.pdf
│   └── additional_materials/
│       ├── cosmic_ship_story.pdf
│       └── planet_energies.pdf
└── subtitles/
    ├── lesson_numerom_intro.vtt
    └── lesson_advanced_calculations.vtt
```

### Безопасность доступа
```python
# Проверка доступа к уроку
async def check_lesson_access(user_id: str, lesson_id: str):
    user = await db.users.find_one({"id": user_id})
    lesson = await db.lessons.find_one({"id": lesson_id})
    
    # Проверка кредитов
    if user["credits_remaining"] < lesson["points_required"]:
        raise HTTPException(403, "Недостаточно кредитов")
    
    # Проверка пререквизитов
    for prereq_id in lesson.get("prerequisites", []):
        progress = await db.user_progress.find_one({
            "user_id": user_id,
            "lesson_id": prereq_id,
            "completed": True
        })
        if not progress:
            raise HTTPException(403, "Не завершены предыдущие уроки")
    
    return True
```

## Интеграция с остальной системой

### Связь с нумерологическими расчетами
```python
# Упражнения могут включать реальные расчеты
exercise_data = {
    "birth_date": user.birth_date,
    "calculation_type": "personal_numbers",
    "results": calculate_personal_numbers(user.birth_date)
}
```

### Связь с челленджами
```python
# Челленджи используют планетарные соответствия
user_ruling_planet = get_ruling_planet(user.birth_date)
recommended_challenges = get_challenges_for_planet(user_ruling_planet)
```

### Связь с трекером привычек
```python
# Привычки персонализируются под слабые планеты пользователя
weak_planets = analyze_planetary_weakness(user.birth_date)
custom_habits = generate_habits_for_planets(weak_planets)
```

## Будущие улучшения

### Планируемые функции
1. **Видеоконференции** - живые уроки с преподавателем
2. **Форум сообщества** - обсуждения и взаимопомощь
3. **Персональные планы обучения** - на основе нумерологического профиля
4. **Сертификация** - выдача сертификатов по завершению курсов

### Интеграции
1. **Zoom/Meet** - для онлайн-уроков
2. **YouTube** - для хостинга видео
3. **Календарь** - напоминания о челленджах
4. **Telegram бот** - уведомления и поддержка

### Аналитика
1. **Тепловые карты** - где пользователи останавливают видео
2. **A/B тесты** - оптимизация контента
3. **Предиктивная аналитика** - прогноз завершения курсов
4. **Персонализация** - рекомендации контента

