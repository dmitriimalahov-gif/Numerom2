# NumerOM - Платформа нумерологии

Полнофункциональная платформа для изучения и практики нумерологии с системой обучения, консультациями и расчетами.

## 🚀 Быстрый старт (Docker Compose)

### Предварительные требования
- Docker и Docker Compose
- Git

### 1. Клонирование репозитория
```bash
git clone https://github.com/dmitriimalahov-gif/Numerom2.git
cd Numerom2
```

### 2. Настройка переменных окружения

#### Backend (.env)
Создайте файл `backend/.env`:
```env
MONGO_URL=mongodb://mongodb:27017
MONGODB_DATABASE=numerom
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://yourdomain.com

# JWT секретный ключ (сгенерируйте безопасный ключ)
JWT_SECRET_KEY=your-secret-jwt-key-here

# Stripe (опционально, для платежей)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLIC_KEY=pk_live_...

# VAPID ключи (опционально, для push-уведомлений)
# Будут автоматически сгенерированы при первом запуске если не указаны
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
```

#### Frontend (.env)
Создайте файл `frontend/.env`:
```env
REACT_APP_BACKEND_URL=http://localhost:8000
GENERATE_SOURCEMAP=false
PORT=3000
```

### 3. Запуск проекта
```bash
docker-compose up --build -d
```

Проект будет автоматически:
- ✅ Запустит MongoDB в Docker контейнере
- ✅ Создаст суперадминистратора при первом запуске
- ✅ Создаст все уроки из папки `файлы для запуска`
- ✅ Загрузит медиафайлы (PDF, Word) для уроков

### 4. Доступ к приложению

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Документация**: http://localhost:8000/docs

### 5. Данные для входа (суперадминистратор)

Учётные данные суперадминистратора задаются переменными окружения (`SUPER_ADMIN_EMAIL`, `SUPER_ADMIN_PASSWORD`) при первом запуске и **не хранятся в репозитории**. Явные пароли по умолчанию отсутствуют.

## 📋 Структура проекта

```
Numerom/
├── backend/              # FastAPI backend (routers/services/domain)
│   ├── server.py        # Точка входа приложения
│   ├── routers/         # HTTP-маршруты
│   ├── services/        # Бизнес-логика
│   ├── domain/          # Доменные модели
│   └── tests/           # unittest-тесты
├── frontend/            # React frontend (CRA/craco)
├── mobile/              # Expo / React Native приложение
├── packages/            # Общие пакеты: api-client, brand, knowledge, number-knowledge
├── scripts/             # Служебные скрипты (озвучка, экспорт)
├── docker-compose.yml   # Docker Compose конфигурация
├── файлы для запуска/   # Материалы курса (автоматически загружаются)
└── docs/                # Документация
```

## 🔧 Управление контейнерами

### Просмотр логов
```bash
# Все сервисы
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# Только frontend
docker-compose logs -f frontend
```

### Остановка
```bash
docker-compose down
```

### Перезапуск
```bash
docker-compose restart
```

### Пересборка после изменений
```bash
docker-compose up --build -d
```

## 🌐 Деплой на продакшн сервер

### 1. Подготовка сервера
```bash
# Установка Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose-plugin
```

### 2. Клонирование на сервер
```bash
git clone https://github.com/dmitriimalahov-gif/Numerom2.git
cd Numerom2
```

### 3. Настройка переменных окружения
Создайте `.env` файлы для backend и frontend (см. раздел "Настройка переменных окружения")

**Важно для продакшна:**
- Измените `CORS_ORIGINS` на ваш домен
- Измените `REACT_APP_BACKEND_URL` на URL вашего backend
- Используйте безопасные `JWT_SECRET_KEY`
- Настройте SSL/TLS (рекомендуется использовать nginx как reverse proxy)

### 4. Обновление docker-compose.yml для продакшна

Измените порты в `docker-compose.yml` если нужно:
```yaml
backend:
  ports:
    - "8000:8000"  # Внешний:Внутренний

frontend:
  ports:
    - "3000:80"
```

### 5. Запуск
```bash
docker-compose up --build -d
```

### 6. Проверка работы
```bash
# Проверить статус контейнеров
docker-compose ps

# Проверить логи
docker-compose logs -f
```

## 🔄 Обновление проекта на сервере

```bash
# 1. Перейти в директорию проекта
cd Numerom2

# 2. Получить последние изменения
git pull origin main

# 3. Пересобрать и перезапустить
docker-compose down
docker-compose up --build -d

# 4. Проверить логи
docker-compose logs -f
```

## 📝 Особенности

### Автоматическая инициализация уроков
При первом запуске backend автоматически:
- Создает суперадминистратора
- Парсит материалы из папки `файлы для запуска`
- Создает все уроки (вводное, 1-9, 0)
- Загружает медиафайлы (PDF, Word)

При последующих запусках уроки не создаются повторно (проверка существования).

### Порты по умолчанию
- **Backend**: 8000
- **Frontend**: 3000
- **MongoDB**: 27017 (локально; внутри Docker-сети обращение через `mongodb:27017`)

## 🐛 Решение проблем

### Backend не запускается
```bash
# Проверить логи
docker-compose logs backend

# Проверить переменные окружения
docker-compose exec backend env | grep MONGO
```

### Frontend не подключается к backend
Проверьте `REACT_APP_BACKEND_URL` в `frontend/.env` - должен указывать на правильный URL backend.

### Уроки не создаются
Убедитесь что папка `файлы для запуска` существует и смонтирована в контейнер:
```bash
docker-compose exec backend ls -la /app/lesson_files
```

## 📚 Дополнительная документация

- [API Документация](docs/api.md)
- [Архитектура](docs/architecture.md)
- [Система обучения](docs/lms.md)

## 📄 Лицензия

Проект NumerOM — частная разработка владельца. Исходный код и материалы не распространяются публично без явного разрешения.

**Озвучка и лицензия модели.** Записи чисел 1–9 и личные записи озвучиваются локальным движком OmniVoice, веса которого распространяются по лицензии **CC-BY-NC (некоммерческое использование)**. Такие записи предназначены только для личного некоммерческого использования и существующей публикации внутри проекта. Для коммерческого выпуска необходимо сначала разрешить лицензионный вопрос (коммерческие веса или замена движка); до этого записи **не включаются в коммерческую мобильную поставку**.
