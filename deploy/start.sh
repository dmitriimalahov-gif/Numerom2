#!/bin/bash

# NumerOM - Быстрый запуск
echo "🚀 Запуск NumerOM..."

# Проверка наличия .env файла
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Файл backend/.env не найден. Копирую из примера..."
    cp backend/.env.example backend/.env
    echo "✅ Скопирован backend/.env.example -> backend/.env"
    echo "📝 Отредактируйте backend/.env перед запуском!"
fi

# Запуск сервисов
echo "🐳 Запуск Docker контейнеров..."
docker-compose -f docker-compose.prod.yml up -d

# Ожидание запуска
echo "⏳ Ожидание запуска сервисов..."
sleep 10

# Проверка работы
echo "🔍 Проверка работы сервисов..."

# Backend
if curl -s http://localhost:8001/docs > /dev/null; then
    echo "✅ Backend: http://localhost:8001"
else
    echo "❌ Backend не отвечает"
fi

# Frontend
if curl -s http://localhost:5128 > /dev/null; then
    echo "✅ Frontend: http://localhost:5128"
else
    echo "❌ Frontend не отвечает"
fi

echo ""
echo "🎉 NumerOM запущен!"
echo ""
echo "📖 Документация: README.md"
echo "🔧 Управление: docker-compose logs -f"
echo "🛑 Остановка: docker-compose down"
