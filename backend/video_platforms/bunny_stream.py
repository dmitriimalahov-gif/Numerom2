"""
Bunny.net Stream Integration
Документация: https://docs.bunny.net/reference/video-api
"""
import hashlib
import time
import os
from typing import Optional, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

try:
    import httpx
except ImportError:
    logger.warning("httpx not installed. Install with: pip install httpx")
    httpx = None


class BunnyStreamService:
    """Сервис для работы с Bunny.net Stream API"""

    def __init__(self, library_id: str, api_key: str):
        """
        Инициализация сервиса

        Args:
            library_id: ID библиотеки в Bunny Stream
            api_key: API ключ из панели Bunny
        """
        self.library_id = library_id
        self.api_key = api_key
        self.base_url = f"https://video.bunnycdn.com/library/{library_id}"
        self.cdn_hostname = f"vz-{library_id[:8]}.b-cdn.net"

    def generate_signed_url(
        self,
        video_id: str,
        expires_in_hours: int = 2,
        user_ip: Optional[str] = None
    ) -> str:
        """
        Генерирует защищенный URL для видео

        Args:
            video_id: ID видео в Bunny
            expires_in_hours: Время жизни ссылки (по умолчанию 2 часа)
            user_ip: IP пользователя (опционально, для дополнительной защиты)

        Returns:
            Защищенный URL для iframe плеера
        """
        # Время истечения (Unix timestamp)
        expires = int(time.time()) + (expires_in_hours * 3600)

        # Базовый URL без подписи
        base_url = f"https://iframe.mediadelivery.net/embed/{self.library_id}/{video_id}"

        # Генерируем токен
        # Формат: library_id + video_id + expires + security_key
        token_string = f"{self.library_id}{video_id}{expires}{self.api_key}"

        # Опционально добавляем IP для привязки к пользователю
        if user_ip:
            token_string += user_ip

        # SHA256 хеш
        token = hashlib.sha256(token_string.encode()).hexdigest()

        # Итоговый URL
        signed_url = f"{base_url}?token={token}&expires={expires}"

        if user_ip:
            signed_url += f"&ip={user_ip}"

        return signed_url

    async def upload_video(
        self,
        file_path: str,
        title: str,
        collection_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Загружает видео на Bunny Stream

        Args:
            file_path: Путь к видео файлу
            title: Название видео
            collection_id: ID коллекции (опционально)

        Returns:
            Dict с информацией о загруженном видео:
            {
                'video_id': 'abc123',
                'status': 'processing',
                'thumbnail_url': '...',
                'iframe_url': '...'
            }
        """
        if httpx is None:
            raise Exception("httpx library is required. Install with: pip install httpx")

        async with httpx.AsyncClient(timeout=300.0) as client:
            # 1. Создаем видео (получаем video_id)
            logger.info(f"Creating video in Bunny: {title}")

            create_payload = {"title": title}
            if collection_id:
                create_payload["collectionId"] = collection_id

            create_response = await client.post(
                f"{self.base_url}/videos",
                headers={"AccessKey": self.api_key},
                json=create_payload
            )

            if create_response.status_code != 200:
                logger.error(f"Failed to create video: {create_response.text}")
                raise Exception(f"Failed to create video: {create_response.text}")

            video_data = create_response.json()
            video_id = video_data['guid']

            logger.info(f"Video created with ID: {video_id}")

            # 2. Загружаем файл
            logger.info(f"Uploading video file: {file_path}")

            file_size = Path(file_path).stat().st_size
            logger.info(f"File size: {file_size / (1024*1024):.2f} MB")

            with open(file_path, 'rb') as f:
                upload_response = await client.put(
                    f"{self.base_url}/videos/{video_id}",
                    headers={
                        "AccessKey": self.api_key,
                        "Content-Type": "application/octet-stream"
                    },
                    content=f.read()
                )

            if upload_response.status_code not in [200, 201]:
                logger.error(f"Failed to upload video: {upload_response.text}")
                # Удаляем созданное видео, если загрузка не удалась
                await self.delete_video(video_id)
                raise Exception(f"Failed to upload video: {upload_response.text}")

            logger.info(f"Video uploaded successfully: {video_id}")

            # 3. Возвращаем информацию
            return {
                'video_id': video_id,
                'status': 'processing',
                'thumbnail_url': f"https://{self.cdn_hostname}/{video_id}/thumbnail.jpg",
                'iframe_url': f"https://iframe.mediadelivery.net/embed/{self.library_id}/{video_id}",
                'library_id': self.library_id
            }

    async def delete_video(self, video_id: str) -> bool:
        """
        Удаляет видео с Bunny Stream

        Args:
            video_id: ID видео

        Returns:
            True если успешно удалено
        """
        if httpx is None:
            raise Exception("httpx library is required")

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/videos/{video_id}",
                headers={"AccessKey": self.api_key}
            )

            success = response.status_code == 200
            if success:
                logger.info(f"Video deleted: {video_id}")
            else:
                logger.error(f"Failed to delete video {video_id}: {response.text}")

            return success

    async def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """
        Получает информацию о видео

        Args:
            video_id: ID видео

        Returns:
            Dict с информацией о видео
        """
        if httpx is None:
            raise Exception("httpx library is required")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/videos/{video_id}",
                headers={"AccessKey": self.api_key}
            )

            if response.status_code != 200:
                logger.error(f"Failed to get video info: {response.text}")
                raise Exception(f"Failed to get video info: {response.text}")

            return response.json()

    async def update_video(
        self,
        video_id: str,
        title: Optional[str] = None,
        collection_id: Optional[str] = None
    ) -> bool:
        """
        Обновляет метаданные видео

        Args:
            video_id: ID видео
            title: Новое название (опционально)
            collection_id: Новая коллекция (опционально)

        Returns:
            True если успешно обновлено
        """
        if httpx is None:
            raise Exception("httpx library is required")

        update_data = {}
        if title:
            update_data['title'] = title
        if collection_id:
            update_data['collectionId'] = collection_id

        if not update_data:
            return True

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/videos/{video_id}",
                headers={"AccessKey": self.api_key},
                json=update_data
            )

            success = response.status_code == 200
            if success:
                logger.info(f"Video updated: {video_id}")
            else:
                logger.error(f"Failed to update video: {response.text}")

            return success


def get_bunny_service() -> BunnyStreamService:
    """
    Создает и возвращает экземпляр BunnyStreamService
    Использует переменные окружения для конфигурации

    Returns:
        BunnyStreamService instance

    Raises:
        Exception: Если не заданы необходимые переменные окружения
    """
    library_id = os.getenv('BUNNY_LIBRARY_ID')
    api_key = os.getenv('BUNNY_API_KEY')

    if not library_id or not api_key:
        raise Exception(
            "BUNNY_LIBRARY_ID and BUNNY_API_KEY must be set in environment variables. "
            "Get them from https://dash.bunny.net/stream"
        )

    return BunnyStreamService(library_id, api_key)


# Функция для проверки доступности сервиса
async def check_bunny_service() -> bool:
    """
    Проверяет доступность Bunny.net API

    Returns:
        True если сервис доступен и настроен
    """
    try:
        service = get_bunny_service()
        if httpx is None:
            logger.error("httpx not installed")
            return False

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{service.base_url}/videos",
                headers={"AccessKey": service.api_key},
                params={"page": 1, "itemsPerPage": 1}
            )
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Bunny service check failed: {e}")
        return False
