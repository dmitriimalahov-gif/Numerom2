"""
Подключение к базе данных MongoDB

Исходный код перенесён из:
- backend/server.py (строки 54-56, 114-116)

Дата переноса: 2025-10-09
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import logging

from core.config import settings

logger = logging.getLogger(__name__)


class Database:
    """
    Singleton класс для управления подключением к MongoDB

    Использует Motor (async драйвер для MongoDB)
    Источник: backend/server.py строки 54-56
    """

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        """
        Подключиться к MongoDB

        Создаёт AsyncIOMotorClient и получает database instance
        Источник: backend/server.py строки 54-56
        """
        try:
            # Создаём MongoDB клиент
            self.client = AsyncIOMotorClient(settings.MONGO_URL)

            # Получаем database instance
            self.db = self.client[settings.MONGODB_DATABASE]

            # Проверяем подключение
            await self.client.admin.command('ping')

            logger.info(
                f"✅ Connected to MongoDB: {settings.MONGODB_DATABASE}"
            )

        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self) -> None:
        """
        Отключиться от MongoDB

        Источник: backend/server.py строки 114-116
        """
        if self.client:
            self.client.close()
            logger.info("✅ Disconnected from MongoDB")

    async def ping(self) -> bool:
        """
        Проверить подключение к MongoDB

        Returns:
            True если подключение активно, False иначе
        """
        try:
            if self.client:
                await self.client.admin.command('ping')
                return True
        except Exception as e:
            logger.error(f"MongoDB ping failed: {e}")

        return False

    def get_database(self) -> AsyncIOMotorDatabase:
        """
        Получить database instance

        Returns:
            AsyncIOMotorDatabase instance

        Raises:
            RuntimeError: Если подключение не установлено
        """
        if self.db is None:
            raise RuntimeError(
                "Database connection not established. "
                "Call await database.connect() first."
            )
        return self.db

    def get_collection(self, name: str):
        """
        Получить коллекцию по имени

        Args:
            name: Имя коллекции

        Returns:
            AsyncIOMotorCollection

        Raises:
            RuntimeError: Если подключение не установлено
        """
        db = self.get_database()
        return db[name]


# ===========================================
# Singleton instance
# ===========================================

database = Database()


# ===========================================
# FastAPI Dependency
# ===========================================

async def get_db() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency для получения database instance

    Usage:
        @router.get("/users")
        async def get_users(db = Depends(get_db)):
            users = await db.users.find().to_list(100)
            return users
    """
    return database.get_database()


async def get_database() -> AsyncIOMotorDatabase:
    """
    Получить database instance (alias для get_db)

    Returns:
        AsyncIOMotorDatabase instance
    """
    return database.get_database()


# ===========================================
# Lifecycle функции для FastAPI
# ===========================================

async def connect_to_database() -> None:
    """
    Подключиться к MongoDB при старте приложения

    Используется в FastAPI startup event:
        @app.on_event("startup")
        async def startup():
            await connect_to_database()
    """
    await database.connect()


async def disconnect_from_database() -> None:
    """
    Отключиться от MongoDB при остановке приложения

    Используется в FastAPI shutdown event:
        @app.on_event("shutdown")
        async def shutdown():
            await disconnect_from_database()
    """
    await database.disconnect()


# ===========================================
# Экспорт
# ===========================================

__all__ = [
    'database',
    'get_db',
    'get_database',
    'connect_to_database',
    'disconnect_from_database',
    'Database',
]
