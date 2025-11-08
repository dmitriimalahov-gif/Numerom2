"""
Базовый репозиторий для всех коллекций MongoDB

Реализует паттерн Repository для абстракции работы с базой данных

Дата создания: 2025-10-09
"""

from typing import List, Dict, Any, Optional, TypeVar, Generic
from abc import ABC
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Базовый класс репозитория для MongoDB коллекций

    Предоставляет общие CRUD операции для всех коллекций.
    Дочерние классы должны определить collection_name.

    Attributes:
        collection_name: Имя коллекции в MongoDB
        db: Database instance
        collection: Collection instance
    """

    collection_name: str = None

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Инициализация репозитория

        Args:
            db: AsyncIOMotorDatabase instance

        Raises:
            ValueError: Если collection_name не установлен
        """
        if not self.collection_name:
            raise ValueError(
                f"{self.__class__.__name__} must define collection_name"
            )

        self.db = db
        self.collection: AsyncIOMotorCollection = db[self.collection_name]

    # ===========================================
    # READ операции
    # ===========================================

    async def find_one(
        self,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Найти один документ

        Args:
            query: MongoDB query (например, {"id": "123"})
            projection: Поля для возврата (опционально)

        Returns:
            Документ или None если не найден
        """
        return await self.collection.find_one(query, projection)

    async def find_many(
        self,
        query: Dict[str, Any],
        limit: int = 100,
        skip: int = 0,
        sort: Optional[List[tuple]] = None,
        projection: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Найти несколько документов

        Args:
            query: MongoDB query
            limit: Максимальное количество документов
            skip: Количество документов для пропуска (пагинация)
            sort: Список кортежей для сортировки [("field", 1/-1)]
            projection: Поля для возврата

        Returns:
            Список документов
        """
        cursor = self.collection.find(query, projection)

        if sort:
            cursor = cursor.sort(sort)

        if skip > 0:
            cursor = cursor.skip(skip)

        if limit > 0:
            cursor = cursor.limit(limit)

        return await cursor.to_list(length=limit if limit > 0 else None)

    async def find_all(
        self,
        projection: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Найти все документы в коллекции

        Args:
            projection: Поля для возврата

        Returns:
            Список всех документов
        """
        return await self.collection.find({}, projection).to_list(length=None)

    async def exists(self, query: Dict[str, Any]) -> bool:
        """
        Проверить существование документа

        Args:
            query: MongoDB query

        Returns:
            True если документ существует, False иначе
        """
        doc = await self.collection.find_one(query, {"_id": 1})
        return doc is not None

    async def count(self, query: Dict[str, Any] = None) -> int:
        """
        Подсчитать количество документов

        Args:
            query: MongoDB query (если None - считает все)

        Returns:
            Количество документов
        """
        if query is None:
            query = {}
        return await self.collection.count_documents(query)

    # ===========================================
    # CREATE операции
    # ===========================================

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создать новый документ

        Args:
            data: Данные для вставки

        Returns:
            Созданный документ (с _id)
        """
        result = await self.collection.insert_one(data)

        # Вернуть созданный документ
        return await self.find_one({'_id': result.inserted_id})

    async def create_many(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Создать несколько документов

        Args:
            documents: Список документов для вставки

        Returns:
            Список созданных документов
        """
        if not documents:
            return []

        result = await self.collection.insert_many(documents)

        # Вернуть созданные документы
        return await self.find_many(
            {'_id': {'$in': result.inserted_ids}}
        )

    # ===========================================
    # UPDATE операции
    # ===========================================

    async def update(
        self,
        query: Dict[str, Any],
        update_data: Dict[str, Any],
        upsert: bool = False
    ) -> bool:
        """
        Обновить один документ

        Args:
            query: MongoDB query для поиска документа
            update_data: Данные для обновления
            upsert: Создать документ если не существует

        Returns:
            True если документ был обновлён, False иначе
        """
        result = await self.collection.update_one(
            query,
            {'$set': update_data},
            upsert=upsert
        )
        return result.modified_count > 0 or (upsert and result.upserted_id is not None)

    async def update_many(
        self,
        query: Dict[str, Any],
        update_data: Dict[str, Any]
    ) -> int:
        """
        Обновить несколько документов

        Args:
            query: MongoDB query
            update_data: Данные для обновления

        Returns:
            Количество обновлённых документов
        """
        result = await self.collection.update_many(
            query,
            {'$set': update_data}
        )
        return result.modified_count

    async def increment(
        self,
        query: Dict[str, Any],
        field: str,
        amount: int = 1
    ) -> bool:
        """
        Инкрементировать числовое поле

        Args:
            query: MongoDB query
            field: Имя поля для инкремента
            amount: Значение для добавления (может быть отрицательным)

        Returns:
            True если успешно, False иначе
        """
        result = await self.collection.update_one(
            query,
            {'$inc': {field: amount}}
        )
        return result.modified_count > 0

    # ===========================================
    # DELETE операции
    # ===========================================

    async def delete(self, query: Dict[str, Any]) -> bool:
        """
        Удалить один документ

        Args:
            query: MongoDB query

        Returns:
            True если документ был удалён, False иначе
        """
        result = await self.collection.delete_one(query)
        return result.deleted_count > 0

    async def delete_many(self, query: Dict[str, Any]) -> int:
        """
        Удалить несколько документов

        Args:
            query: MongoDB query

        Returns:
            Количество удалённых документов
        """
        result = await self.collection.delete_many(query)
        return result.deleted_count

    # ===========================================
    # Утилиты
    # ===========================================

    async def aggregate(
        self,
        pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Выполнить aggregation pipeline

        Args:
            pipeline: MongoDB aggregation pipeline

        Returns:
            Результаты агрегации
        """
        cursor = self.collection.aggregate(pipeline)
        return await cursor.to_list(length=None)

    def _remove_mongo_id(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Удалить MongoDB _id из документа

        Args:
            doc: Документ

        Returns:
            Документ без _id
        """
        if doc and '_id' in doc:
            doc = dict(doc)
            del doc['_id']
        return doc

    def _remove_mongo_ids(
        self,
        docs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Удалить MongoDB _id из списка документов

        Args:
            docs: Список документов

        Returns:
            Список документов без _id
        """
        return [self._remove_mongo_id(doc) for doc in docs]


__all__ = ['BaseRepository']
