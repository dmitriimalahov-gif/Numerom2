#!/bin/bash

# Скрипт для создания бэкапа проекта
# Использование: ./create_backup.sh "описание изменений"

BACKUP_DATE=$(date +"%Y-%m-%d_%H-%M-%S")
DESCRIPTION=${1:-"manual_backup"}
BACKUP_NAME="backup_${BACKUP_DATE}_${DESCRIPTION}"

echo "🔄 Создание бэкапа..."

# Коммитим все изменения
git add -A
if git diff --cached --quiet; then
    echo "ℹ️  Нет изменений для коммита"
else
    git commit -m "backup: ${BACKUP_NAME}"
    echo "✅ Изменения закоммичены"
fi

# Создаём тег
git tag -a "${BACKUP_NAME}" -m "Бэкап: ${DESCRIPTION}"
echo "✅ Создан тег: ${BACKUP_NAME}"

# Показываем последние 5 бэкапов
echo ""
echo "📋 Последние бэкапы:"
git tag | grep backup | tail -5

echo ""
echo "📌 Для возврата к этому состоянию используйте:"
echo "   git checkout ${BACKUP_NAME}"
echo ""
echo "📌 Для возврата к предыдущему бэкапу:"
echo "   git tag | grep backup | tail -2 | head -1 | xargs git checkout"

