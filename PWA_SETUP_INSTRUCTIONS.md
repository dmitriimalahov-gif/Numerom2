# Инструкция по запуску PWA с Push-уведомлениями

## Что уже сделано ✅

1. **Frontend:**
   - ✅ manifest.json создан
   - ✅ Service Worker настроен (service-worker.js)
   - ✅ Service Worker зарегистрирован в React (index.js)
   - ✅ Утилиты для работы с push (serviceWorkerRegistration.js)
   - ✅ UI компонент для настроек (PushNotificationSettings.jsx)

2. **Backend:**
   - ✅ Модуль push_notifications.py создан
   - ✅ API endpoints добавлены в server.py
   - ✅ Зависимости добавлены в requirements.txt
   - ✅ Скрипт генерации VAPID ключей готов

## Что нужно сделать для запуска:

### Шаг 1: Установить зависимости

```bash
cd backend
pip install -r requirements.txt
```

### Шаг 2: Сгенерировать VAPID ключи

```bash
cd backend
python generate_vapid_keys.py
```

Скрипт создаст файл `.env.vapid` с ключами. Скопируйте их в ваш `.env` файл:

```env
VAPID_PUBLIC_KEY=<ваш_публичный_ключ>
VAPID_PRIVATE_KEY=<ваш_приватный_ключ>
```

### Шаг 3: Создать иконки PWA

Следуйте инструкциям в файле:
`frontend/public/PWA_ICONS_INSTRUCTIONS.md`

Минимально необходимо:
- `icon-192x192.png`
- `icon-512x512.png`

Поместите их в `/frontend/public/`

### Шаг 4: Интегрировать компонент в уроки

Добавьте `PushNotificationSettings` в FirstLesson.jsx и CustomLessonViewer.jsx:

```jsx
import PushNotificationSettings from './PushNotificationSettings';

// В компоненте, в разделе с челленджем:
<PushNotificationSettings
  lessonId={lessonData.id}
  onSubscribed={() => {
    // Опционально: обработать успешную подписку
  }}
/>
```

### Шаг 5: Перезапустить сервисы

```bash
# Backend
cd backend
python server.py

# Frontend
cd frontend
npm start
```

## Тестирование:

1. Откройте приложение в браузере
2. Перейдите в раздел с челленджем
3. Нажмите "Включить напоминания"
4. Разрешите уведомления в браузере
5. Получите тестовое уведомление

## Настройка scheduled tasks (ежедневные напоминания):

### Вариант 1: Использовать APScheduler (рекомендуется)

Добавить в `requirements.txt`:
```
apscheduler==3.10.4
```

Добавить в `server.py`:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

scheduler = AsyncIOScheduler()

async def send_daily_challenge_reminders():
    """Отправить ежедневные напоминания всем активным пользователям"""
    try:
        # Получаем все активные подписки
        subscriptions = await db.push_subscriptions.find({
            "challenge_started": True,
            "enabled": True
        }).to_list(length=None)

        for subscription in subscriptions:
            user_id = subscription['user_id']

            # Получаем прогресс челленджа
            user_progress = await db.challenge_progress.find_one({
                "user_id": user_id,
                "lesson_id": subscription['lesson_id']
            })

            if not user_progress:
                continue

            current_day = user_progress.get('current_day', 1)

            # Отправляем напоминание
            await push_manager.send_challenge_reminder(
                user_id=user_id,
                day_number=current_day
            )

        logger.info(f"Sent {len(subscriptions)} daily reminders")
    except Exception as e:
        logger.error(f"Error sending daily reminders: {e}")

# В on_startup добавить:
scheduler.add_job(
    send_daily_challenge_reminders,
    'cron',
    hour=10,  # Отправлять в 10:00
    minute=0,
    timezone=pytz.UTC
)
scheduler.start()
```

### Вариант 2: Использовать внешний cron

Создать endpoint:
```python
@app.post("/api/admin/send-challenge-reminders")
async def trigger_challenge_reminders(
    current_user: dict = Depends(get_current_user)
):
    """Админ endpoint для запуска отправки напоминаний (для cron)"""
    await send_daily_challenge_reminders()
    return {"success": True}
```

Добавить в crontab:
```bash
0 10 * * * curl -X POST http://localhost:8000/api/admin/send-challenge-reminders
```

## Важные замечания:

1. **HTTPS обязателен** для production (Service Workers требуют https)
2. **Localhost работает** без https для разработки
3. **iOS Safari** требует "Add to Home Screen" для полноценной работы PWA
4. **Иконки** должны быть квадратными PNG
5. **VAPID ключи** держите в секрете, не коммитьте в git

## Troubleshooting:

### Уведомления не приходят:
- Проверьте, что VAPID ключи добавлены в .env
- Убедитесь, что браузер разрешил уведомления
- Проверьте консоль браузера на ошибки
- Убедитесь, что Service Worker зарегистрирован (DevTools → Application → Service Workers)

### Service Worker не регистрируется:
- Проверьте, что используете localhost или https
- Очистите кэш браузера
- Проверьте путь к service-worker.js

### Ошибка при подписке:
- Проверьте, что VAPID ключи сгенерированы и добавлены в .env
- Проверьте, что бэкенд возвращает публичный ключ на /api/push/vapid-public-key
- Убедитесь, что MongoDB доступна

## Полезные ссылки:

- [PWA Builder](https://www.pwabuilder.com/)
- [Web Push Protocol](https://web.dev/push-notifications/)
- [Service Workers API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
