"""
User Repository

Репозиторий для работы с коллекцией users

Операции перенесены из backend/server.py:
- Строка 138: find_by_id
- Строка 146: increment_credits
- Строка 177: find_by_email
- Строка 203: create
- Строка 217: update_last_login
- Строка 299, 308, 343, 348: increment_credits (покупки)
- Строка 1650: find_all
- Строка 1686: update
- Строка 1725: delete
- И другие (~35 использований)

Дата создания: 2025-10-09
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from .base import BaseRepository
from models.user import User, UserResponse, create_user_response


class UserRepository(BaseRepository):
    """
    Репозиторий для работы с пользователями

    Коллекция: users
    """

    collection_name = 'users'

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)

    # ===========================================
    # READ операции
    # ===========================================

    async def find_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Найти пользователя по ID

        Источник: backend/server.py строки 138, 402, 429, и т.д. (~15 раз)

        Args:
            user_id: ID пользователя (UUID string)

        Returns:
            User документ или None
        """
        return await self.find_one({'id': user_id})

    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Найти пользователя по email

        Источник: backend/server.py строки 177, 209

        Args:
            email: Email пользователя

        Returns:
            User документ или None
        """
        return await self.find_one({'email': email})

    async def exists_by_email(self, email: str) -> bool:
        """
        Проверить существование пользователя по email

        Используется при регистрации

        Args:
            email: Email для проверки

        Returns:
            True если пользователь существует
        """
        return await self.exists({'email': email})

    async def find_all_users(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Получить всех пользователей (для админки)

        Источник: backend/server.py строка 1650

        Args:
            skip: Пропустить N пользователей (пагинация)
            limit: Максимальное количество

        Returns:
            Список пользователей
        """
        return await self.find_many({}, limit=limit, skip=skip)

    # ===========================================
    # CREATE операции
    # ===========================================

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создать нового пользователя

        Источник: backend/server.py строка 203

        Args:
            user_data: Данные пользователя (из User модели)

        Returns:
            Созданный пользователь
        """
        return await self.create(user_data)

    # ===========================================
    # UPDATE операции
    # ===========================================

    async def update_user(
        self,
        user_id: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """
        Обновить данные пользователя

        Источник: backend/server.py строки 217, 1686, 2961, 2975

        Args:
            user_id: ID пользователя
            update_data: Данные для обновления

        Returns:
            True если успешно обновлено
        """
        # Добавляем updated_at автоматически
        update_data['updated_at'] = datetime.utcnow()
        return await self.update({'id': user_id}, update_data)

    async def update_last_login(self, email: str) -> bool:
        """
        Обновить время последнего входа

        Источник: backend/server.py строка 217

        Args:
            email: Email пользователя

        Returns:
            True если успешно
        """
        return await self.update(
            {'email': email},
            {
                'updated_at': datetime.utcnow(),
                'last_login': datetime.utcnow()
            }
        )

    async def increment_credits(
        self,
        user_id: str,
        amount: int
    ) -> bool:
        """
        Инкрементировать (увеличить/уменьшить) баллы пользователя

        Источник: backend/server.py строки 146, 299, 308, 343, 348, 742, 761, и т.д.

        Args:
            user_id: ID пользователя
            amount: Количество баллов (может быть отрицательным для списания)

        Returns:
            True если успешно
        """
        return await self.increment(
            {'id': user_id},
            'credits_remaining',
            amount
        )

    async def update_subscription(
        self,
        user_id: str,
        subscription_data: Dict[str, Any]
    ) -> bool:
        """
        Обновить подписку пользователя

        Используется при покупке подписки

        Источник: backend/server.py строки 303, 308, 343, 348

        Args:
            user_id: ID пользователя
            subscription_data: Данные подписки
                - subscription_type: "monthly" | "annual"
                - subscription_expires_at: datetime
                - is_premium: bool

        Returns:
            True если успешно
        """
        subscription_data['updated_at'] = datetime.utcnow()
        return await self.update({'id': user_id}, subscription_data)

    async def set_admin_status(
        self,
        user_id: str,
        is_admin: bool = False,
        is_super_admin: bool = False
    ) -> bool:
        """
        Установить админский статус пользователю

        Источник: backend/server.py строки 1408, 1433

        Args:
            user_id: ID пользователя
            is_admin: Флаг обычного админа
            is_super_admin: Флаг суперадмина

        Returns:
            True если успешно
        """
        return await self.update(
            {'id': user_id},
            {
                'is_admin': is_admin,
                'is_super_admin': is_super_admin,
                'updated_at': datetime.utcnow()
            }
        )

    async def update_city(self, user_id: str, city: str) -> bool:
        """
        Обновить город пользователя

        Источник: backend/server.py строка 2975

        Args:
            user_id: ID пользователя
            city: Название города

        Returns:
            True если успешно
        """
        return await self.update(
            {'id': user_id},
            {
                'city': city,
                'updated_at': datetime.utcnow()
            }
        )

    async def check_and_expire_subscription(self, user_id: str) -> bool:
        """
        Проверить и обнулить подписку если истекла

        Источник: backend/server.py строки 2783, 2902

        Args:
            user_id: ID пользователя

        Returns:
            True если подписка была обнулена, False если всё ок
        """
        user = await self.find_by_id(user_id)
        if not user:
            return False

        # Проверяем истекла ли подписка
        subscription_expires = user.get('subscription_expires_at')
        if subscription_expires and datetime.utcnow() > subscription_expires:
            # Обнуляем подписку
            await self.update(
                {'id': user_id},
                {
                    'is_premium': False,
                    'subscription_type': None,
                    'subscription_expires_at': None,
                    'updated_at': datetime.utcnow()
                }
            )
            return True

        return False

    # ===========================================
    # DELETE операции
    # ===========================================

    async def delete_user(self, user_id: str) -> bool:
        """
        Удалить пользователя

        Источник: backend/server.py строка 1725

        ВНИМАНИЕ: Это также должно удалить связанные данные:
        - user_progress
        - user_levels
        - quiz_results
        - consultation_purchases
        (см. строки 1726-1729 в server.py)

        Args:
            user_id: ID пользователя

        Returns:
            True если успешно удалён
        """
        return await self.delete({'id': user_id})

    # ===========================================
    # Специальные запросы
    # ===========================================

    async def count_users(self) -> int:
        """
        Подсчитать общее количество пользователей

        Returns:
            Количество пользователей
        """
        return await self.count({})

    async def get_users_with_credits(
        self,
        min_credits: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Получить пользователей с определённым количеством баллов

        Args:
            min_credits: Минимальное количество баллов

        Returns:
            Список пользователей
        """
        return await self.find_many(
            {'credits_remaining': {'$gte': min_credits}}
        )

    async def get_premium_users(self) -> List[Dict[str, Any]]:
        """
        Получить всех premium пользователей

        Returns:
            Список premium пользователей
        """
        return await self.find_many({'is_premium': True})

    async def get_admins(self) -> List[Dict[str, Any]]:
        """
        Получить всех администраторов

        Returns:
            Список администраторов (обычных и супер)
        """
        return await self.find_many({
            '$or': [
                {'is_admin': True},
                {'is_super_admin': True}
            ]
        })


__all__ = ['UserRepository']
