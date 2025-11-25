"""
Модуль для работы с Web Push уведомлениями
"""

import json
import os
from typing import Dict, Optional, List
from datetime import datetime
from pywebpush import webpush, WebPushException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field
from bson import ObjectId


class PushSubscription(BaseModel):
    """Модель подписки на push уведомления"""
    user_id: str
    endpoint: str
    keys: Dict[str, str]  # p256dh и auth ключи
    created_at: datetime = Field(default_factory=datetime.utcnow)
    lesson_id: Optional[str] = None  # ID урока для челленджа
    challenge_started: bool = False
    notification_time: str = "10:00"  # Время уведомлений в формате HH:MM
    timezone: str = "Europe/Moscow"
    enabled: bool = True

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PushNotificationManager:
    """Менеджер для управления push уведомлениями"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.subscriptions_collection = db.push_subscriptions

        # VAPID ключи (нужно сгенерировать)
        self.vapid_private_key = os.getenv(
            "VAPID_PRIVATE_KEY",
            ""  # Будет сгенерировано автоматически
        )
        self.vapid_public_key = os.getenv(
            "VAPID_PUBLIC_KEY",
            ""  # Будет сгенерировано автоматически
        )
        self.vapid_claims = {
            "sub": "mailto:support@numerom.com"
        }

    async def save_subscription(
        self,
        user_id: str,
        subscription_data: Dict,
        lesson_id: Optional[str] = None,
        notification_time: str = "10:00",
        timezone: str = "Europe/Moscow"
    ) -> Dict:
        """Сохранить подписку пользователя"""

        subscription = {
            "user_id": user_id,
            "endpoint": subscription_data["endpoint"],
            "keys": subscription_data["keys"],
            "lesson_id": lesson_id,
            "notification_time": notification_time,
            "timezone": timezone,
            "challenge_started": False,
            "enabled": True,
            "created_at": datetime.utcnow()
        }

        # Проверяем, существует ли подписка
        existing = await self.subscriptions_collection.find_one({
            "user_id": user_id,
            "endpoint": subscription_data["endpoint"]
        })

        if existing:
            # Обновляем существующую
            await self.subscriptions_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": subscription}
            )
            subscription["_id"] = existing["_id"]
        else:
            # Создаём новую
            result = await self.subscriptions_collection.insert_one(subscription)
            subscription["_id"] = result.inserted_id

        return subscription

    async def get_user_subscriptions(self, user_id: str) -> List[Dict]:
        """Получить все подписки пользователя"""
        cursor = self.subscriptions_collection.find({"user_id": user_id, "enabled": True})
        return await cursor.to_list(length=100)

    async def remove_subscription(self, user_id: str, endpoint: str) -> bool:
        """Удалить подписку"""
        result = await self.subscriptions_collection.delete_one({
            "user_id": user_id,
            "endpoint": endpoint
        })
        return result.deleted_count > 0

    async def update_subscription_settings(
        self,
        user_id: str,
        endpoint: str,
        **settings
    ) -> bool:
        """Обновить настройки подписки"""
        result = await self.subscriptions_collection.update_one(
            {"user_id": user_id, "endpoint": endpoint},
            {"$set": settings}
        )
        return result.modified_count > 0

    async def start_challenge_notifications(
        self,
        user_id: str,
        lesson_id: str
    ) -> bool:
        """Запустить уведомления для челленджа"""
        result = await self.subscriptions_collection.update_many(
            {"user_id": user_id},
            {"$set": {
                "challenge_started": True,
                "lesson_id": lesson_id,
                "challenge_start_date": datetime.utcnow()
            }}
        )
        return result.modified_count > 0

    async def stop_challenge_notifications(self, user_id: str) -> bool:
        """Остановить уведомления для челленджа"""
        result = await self.subscriptions_collection.update_many(
            {"user_id": user_id},
            {"$set": {
                "challenge_started": False,
                "lesson_id": None
            }}
        )
        return result.modified_count > 0

    def send_notification(
        self,
        subscription_info: Dict,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        icon: str = "/icon-192x192.png",
        badge: str = "/icon-192x192.png",
        url: str = "/"
    ) -> bool:
        """Отправить push уведомление"""

        try:
            # Формируем данные уведомления
            notification_data = {
                "title": title,
                "body": body,
                "icon": icon,
                "badge": badge,
                "url": url,
                "tag": "numerom-challenge",
                "requireInteraction": False
            }

            if data:
                notification_data.update(data)

            # Отправляем через Web Push
            webpush(
                subscription_info={
                    "endpoint": subscription_info["endpoint"],
                    "keys": subscription_info["keys"]
                },
                data=json.dumps(notification_data),
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims
            )

            return True

        except WebPushException as e:
            print(f"Web Push Error: {e}")
            # Если подписка невалидна (410 Gone), удаляем её
            if e.response and e.response.status_code == 410:
                # Подписка устарела, нужно удалить
                pass
            return False
        except Exception as e:
            print(f"Error sending notification: {e}")
            return False

    async def send_challenge_reminder(
        self,
        user_id: str,
        day_number: int,
        lesson_title: str = "Челлендж NumerOM"
    ) -> int:
        """Отправить напоминание о дне челленджа всем подпискам пользователя"""

        subscriptions = await self.get_user_subscriptions(user_id)
        sent_count = 0

        for subscription in subscriptions:
            if not subscription.get("challenge_started"):
                continue

            success = self.send_notification(
                subscription_info=subscription,
                title=f"День {day_number} - {lesson_title}",
                body=f"Пора выполнить задания дня {day_number}! 🌟",
                data={
                    "lessonId": subscription.get("lesson_id"),
                    "challengeDay": day_number
                },
                url=f"/?lesson={subscription.get('lesson_id')}&tab=challenge&day={day_number}"
            )

            if success:
                sent_count += 1

        return sent_count

    def generate_vapid_keys(self):
        """Генерация VAPID ключей (выполнить один раз)"""
        from py_vapid import Vapid

        vapid = Vapid()
        vapid.generate_keys()

        return {
            "public_key": vapid.public_key.export_public().decode('utf-8'),
            "private_key": vapid.private_key.export().decode('utf-8')
        }


# Глобальный экземпляр менеджера (инициализируется в server.py)
push_manager: Optional[PushNotificationManager] = None


def get_push_manager() -> PushNotificationManager:
    """Получить экземпляр менеджера push уведомлений"""
    if push_manager is None:
        raise RuntimeError("Push notification manager not initialized")
    return push_manager
