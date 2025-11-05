#!/bin/bash

echo "🚀 Starting NumerOM Backend..."

# Проверка наличия VAPID ключей (без set -e чтобы не падать на ошибках генерации)
if [ -z "$VAPID_PUBLIC_KEY" ] || [ -z "$VAPID_PRIVATE_KEY" ]; then
    echo "⚠️  VAPID keys not found in environment"

    # Проверяем, есть ли файл с ключами
    if [ ! -f "/app/.env.vapid" ]; then
        echo "🔑 Trying to generate VAPID keys..."

        # Пытаемся сгенерировать, но не падаем если не получится
        set +e  # Временно отключаем exit on error
        python generate_vapid_keys.py
        VAPID_EXIT_CODE=$?
        set -e  # Включаем обратно

        # Даем время на запись файла
        sleep 1

        if [ -f "/app/.env.vapid" ]; then
            echo "✅ VAPID keys generated successfully"
            echo "📝 Loading keys from .env.vapid"
            export $(cat /app/.env.vapid | xargs)
        else
            echo "⚠️  Failed to generate VAPID keys - continuing without push notifications"
            echo "💡 Push notifications will be disabled. To enable them, add VAPID keys to .env"
        fi
    else
        echo "📂 Loading existing VAPID keys from .env.vapid"
        export $(cat /app/.env.vapid | xargs)
    fi
else
    echo "✅ VAPID keys found in environment"
fi

# Включаем exit on error для остальной части скрипта
set -e

# Создаём необходимые директории
echo "📁 Creating upload directories..."
mkdir -p /app/uploads/materials
mkdir -p /app/uploads/consultations/videos
mkdir -p /app/uploads/consultations/pdfs
mkdir -p /app/uploads/consultations/subtitles
mkdir -p /app/uploads/lessons/videos
mkdir -p /app/uploads/lessons/pdfs
mkdir -p /app/uploads/tmp

echo "🔌 Waiting for MongoDB to be ready..."
python << END
import time
import os
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def wait_for_mongo():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://mongodb:27017')
    max_retries = 30
    retry_interval = 1

    for i in range(max_retries):
        try:
            client = AsyncIOMotorClient(mongo_url)
            await client.admin.command('ping')
            print(f"✅ MongoDB is ready!")
            client.close()
            return True
        except Exception as e:
            if i < max_retries - 1:
                print(f"⏳ Waiting for MongoDB... ({i+1}/{max_retries})")
                await asyncio.sleep(retry_interval)
            else:
                print(f"❌ Failed to connect to MongoDB: {e}")
                return False
    return False

if __name__ == "__main__":
    result = asyncio.run(wait_for_mongo())
    exit(0 if result else 1)
END

if [ $? -ne 0 ]; then
    echo "❌ MongoDB connection failed"
    exit 1
fi

echo "✨ Starting Uvicorn server..."
# Запускаем uvicorn в фоне
uvicorn server:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

# Ждем, пока backend запустится
echo "⏳ Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  Backend startup timeout (this is OK, continuing anyway)"
    fi
    sleep 1
done

# Инициализация уроков (если файлы доступны)
if [ -d "/app/lesson_files" ] && [ "$(ls -A /app/lesson_files 2>/dev/null)" ]; then
    echo "📚 Инициализация уроков..."
    python init_lessons.py || echo "⚠️  Предупреждение: Не удалось инициализировать уроки (это нормально если уроки уже созданы)"
else
    echo "ℹ️  Файлы уроков не найдены, пропускаем инициализацию"
fi

# Ожидаем завершения uvicorn процесса
wait $UVICORN_PID
