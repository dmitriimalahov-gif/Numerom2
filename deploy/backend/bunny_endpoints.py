"""
Bunny.net Stream Endpoints
Endpoints для работы с видео через Bunny.net
"""
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from video_platforms.bunny_stream import get_bunny_service, BunnyStreamService

logger = logging.getLogger(__name__)

# Создаем роутер
bunny_router = APIRouter(prefix="/api", tags=["Bunny Video"])


# Временная директория для загрузки файлов
# Используем относительный путь для совместимости с Docker и локальной разработкой
UPLOAD_ROOT = Path(__file__).parent / "uploads"
TMP_DIR = UPLOAD_ROOT / "tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)


# ==================== АДМИНСКИЕ ENDPOINTS ====================

@bunny_router.post('/admin/lessons/{lesson_id}/upload-video-bunny')
async def upload_video_to_bunny(
    lesson_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(lambda: None),  # Placeholder, заменить на get_current_user
    bunny_service: BunnyStreamService = Depends(get_bunny_service)
):
    """
    Загружает видео на Bunny.net Stream для урока

    Args:
        lesson_id: ID урока
        file: Видео файл
        current_user: Текущий пользователь (требуется админ)
        bunny_service: Сервис Bunny.net

    Returns:
        {
            'success': True,
            'video_id': 'abc123',
            'status': 'processing',
            'message': '...'
        }
    """
    try:
        # TODO: Раскомментировать после интеграции auth
        # from server import check_admin_rights
        # admin_user = await check_admin_rights(current_user, require_super_admin=False)

        # Валидация типа файла
        allowed_types = ['video/mp4', 'video/avi', 'video/mov', 'video/webm', 'video/quicktime']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f'Неподдерживаемый формат видео: {file.content_type}. Разрешены: MP4, AVI, MOV, WEBM'
            )

        # Валидация размера (500MB)
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)

        if file_size_mb > 500:
            raise HTTPException(
                status_code=400,
                detail=f'Размер файла ({file_size_mb:.1f}MB) превышает максимум 500MB'
            )

        logger.info(f"Uploading video to Bunny for lesson {lesson_id}: {file.filename} ({file_size_mb:.1f}MB)")

        # Сохраняем временно на диск
        temp_filename = f"{uuid.uuid4()}_{file.filename}"
        temp_path = TMP_DIR / temp_filename

        with open(temp_path, 'wb') as buffer:
            buffer.write(content)

        # Получаем информацию о уроке из БД
        from server import db
        lesson = await db.custom_lessons.find_one({'id': lesson_id})
        if not lesson:
            lesson = await db.lessons.find_one({'id': lesson_id})

        # Если урок не найден - используем ID для названия
        if lesson:
            video_title = f"{lesson.get('title', lesson_id)} - Видео урока"
        else:
            logger.warning(f"Lesson {lesson_id} not found in DB, using ID as title")
            video_title = f"Урок {lesson_id} - Видео"

        try:
            # Загружаем на Bunny
            upload_result = await bunny_service.upload_video(
                file_path=str(temp_path),
                title=video_title
            )

            # Удаляем временный файл
            temp_path.unlink()

            # Сохраняем информацию в БД
            update_data = {
                'video_platform': 'bunny',
                'video_id': upload_result['video_id'],
                'video_library_id': upload_result['library_id'],
                'video_thumbnail': upload_result['thumbnail_url'],
                'video_iframe_url': upload_result['iframe_url'],
                'video_status': 'processing',
                'video_uploaded_at': datetime.utcnow(),
                'video_filename': file.filename,
                'video_size_mb': file_size_mb
            }

            # Обновляем урок в БД
            result = await db.custom_lessons.update_one(
                {'id': lesson_id},
                {'$set': update_data}
            )

            if result.matched_count == 0:
                # Пробуем обновить в коллекции lessons
                result2 = await db.lessons.update_one(
                    {'id': lesson_id},
                    {'$set': update_data}
                )

                # Если урок не найден нигде - создаем запись в custom_lessons
                if result2.matched_count == 0:
                    logger.warning(f"Lesson {lesson_id} not found, creating new record in custom_lessons")
                    await db.custom_lessons.insert_one({
                        'id': lesson_id,
                        'title': video_title,
                        'is_active': True,
                        'created_at': datetime.utcnow(),
                        **update_data
                    })

            logger.info(f"Video uploaded to Bunny successfully: {upload_result['video_id']}")

            return {
                'success': True,
                'video_id': upload_result['video_id'],
                'thumbnail_url': upload_result['thumbnail_url'],
                'status': 'processing',
                'message': 'Видео успешно загружено на Bunny.net. Обработка займет несколько минут.'
            }

        except Exception as e:
            # Удаляем временный файл в случае ошибки
            if temp_path.exists():
                temp_path.unlink()
            raise

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading to Bunny: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки: {str(e)}")


@bunny_router.delete('/admin/lessons/{lesson_id}/video-bunny')
async def delete_lesson_video_from_bunny(
    lesson_id: str,
    current_user: dict = Depends(lambda: None),  # Placeholder
    bunny_service: BunnyStreamService = Depends(get_bunny_service)
):
    """
    Удаляет видео урока с Bunny.net

    Args:
        lesson_id: ID урока
        current_user: Текущий пользователь (требуется админ)
        bunny_service: Сервис Bunny.net

    Returns:
        {'success': True, 'message': '...'}
    """
    try:
        # TODO: Раскомментировать после интеграции auth
        # from server import check_admin_rights
        # admin_user = await check_admin_rights(current_user, require_super_admin=False)

        from server import db

        # Получаем информацию о видео из БД
        lesson = await db.custom_lessons.find_one({'id': lesson_id})
        if not lesson:
            lesson = await db.lessons.find_one({'id': lesson_id})

        if not lesson:
            raise HTTPException(status_code=404, detail="Урок не найден")

        video_id = lesson.get('video_id')
        if not video_id or lesson.get('video_platform') != 'bunny':
            raise HTTPException(status_code=404, detail="Видео не найдено на Bunny платформе")

        # Удаляем с Bunny
        deleted = await bunny_service.delete_video(video_id)

        if deleted:
            # Удаляем информацию из БД
            await db.custom_lessons.update_one(
                {'id': lesson_id},
                {'$unset': {
                    'video_platform': '',
                    'video_id': '',
                    'video_library_id': '',
                    'video_thumbnail': '',
                    'video_iframe_url': '',
                    'video_status': '',
                    'video_uploaded_at': '',
                    'video_filename': '',
                    'video_size_mb': ''
                }}
            )

            await db.lessons.update_one(
                {'id': lesson_id},
                {'$unset': {
                    'video_platform': '',
                    'video_id': '',
                    'video_library_id': '',
                    'video_thumbnail': '',
                    'video_iframe_url': '',
                    'video_status': '',
                    'video_uploaded_at': '',
                    'video_filename': '',
                    'video_size_mb': ''
                }}
            )

            logger.info(f"Video deleted from Bunny: {video_id}")

            return {
                'success': True,
                'message': 'Видео успешно удалено с Bunny.net и из урока'
            }
        else:
            raise HTTPException(status_code=500, detail="Не удалось удалить видео с Bunny.net")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting video from Bunny: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка удаления: {str(e)}")


# ==================== ПОЛЬЗОВАТЕЛЬСКИЕ ENDPOINTS ====================

@bunny_router.get('/lessons/{lesson_id}/video-url')
async def get_lesson_video_url(
    lesson_id: str,
    request: Request,
    current_user: dict = Depends(lambda: None),  # Placeholder
    bunny_service: BunnyStreamService = Depends(get_bunny_service)
):
    """
    Генерирует защищенный URL для просмотра видео урока

    Требует авторизации. Возвращает signed URL который:
    - Работает только 2 часа
    - Привязан к IP пользователя
    - Нельзя передать другому пользователю

    Args:
        lesson_id: ID урока
        request: HTTP Request (для получения IP)
        current_user: Текущий пользователь
        bunny_service: Сервис Bunny.net

    Returns:
        {
            'success': True,
            'video_url': 'https://...',
            'expires_in': '2 hours',
            'thumbnail': '...'
        }
    """
    try:
        # TODO: Раскомментировать после интеграции auth
        # if not current_user:
        #     raise HTTPException(status_code=401, detail="Требуется авторизация")

        from server import db

        # Получаем урок
        lesson = await db.custom_lessons.find_one({'id': lesson_id})
        if not lesson:
            lesson = await db.lessons.find_one({'id': lesson_id})

        if not lesson:
            raise HTTPException(status_code=404, detail="Урок не найден")

        # Проверяем наличие видео
        if lesson.get('video_platform') != 'bunny':
            raise HTTPException(
                status_code=400,
                detail="Видео не размещено на Bunny платформе"
            )

        video_id = lesson.get('video_id')
        if not video_id:
            raise HTTPException(status_code=404, detail="Видео не загружено для этого урока")

        # Проверяем статус обработки
        video_status = lesson.get('video_status', 'unknown')
        if video_status == 'processing':
            return {
                'success': False,
                'status': 'processing',
                'message': 'Видео еще обрабатывается. Попробуйте через несколько минут.',
                'thumbnail': lesson.get('video_thumbnail')
            }

        # TODO: Проверить доступ пользователя к уроку (оплачен ли урок, есть ли подписка и т.д.)
        # user_has_access = await check_lesson_access(current_user['user_id'], lesson_id)
        # if not user_has_access:
        #     raise HTTPException(status_code=403, detail="У вас нет доступа к этому уроку")

        # Получаем IP пользователя
        user_ip = request.client.host

        # Генерируем signed URL
        signed_url = bunny_service.generate_signed_url(
            video_id=video_id,
            expires_in_hours=2,  # Ссылка живет 2 часа
            user_ip=user_ip  # Привязываем к IP
        )

        logger.info(f"Generated signed URL for lesson {lesson_id}, user IP: {user_ip}")

        return {
            'success': True,
            'video_url': signed_url,
            'expires_in': '2 hours',
            'thumbnail': lesson.get('video_thumbnail'),
            'video_id': video_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating video URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации URL: {str(e)}")


@bunny_router.get('/admin/lessons/{lesson_id}/video-info')
async def get_lesson_video_info(
    lesson_id: str,
    current_user: dict = Depends(lambda: None),  # Placeholder
    bunny_service: BunnyStreamService = Depends(get_bunny_service)
):
    """
    Получает информацию о видео урока с Bunny.net

    Args:
        lesson_id: ID урока
        current_user: Текущий пользователь (требуется админ)
        bunny_service: Сервис Bunny.net

    Returns:
        Информация о видео с Bunny.net
    """
    try:
        # TODO: Раскомментировать после интеграции auth
        # from server import check_admin_rights
        # admin_user = await check_admin_rights(current_user, require_super_admin=False)

        from server import db

        lesson = await db.custom_lessons.find_one({'id': lesson_id})
        if not lesson:
            lesson = await db.lessons.find_one({'id': lesson_id})

        if not lesson:
            raise HTTPException(status_code=404, detail="Урок не найден")

        video_id = lesson.get('video_id')
        if not video_id or lesson.get('video_platform') != 'bunny':
            raise HTTPException(status_code=404, detail="Видео не найдено на Bunny платформе")

        # Получаем информацию с Bunny
        video_info = await bunny_service.get_video_info(video_id)

        # Обновляем статус в БД если изменился
        if video_info.get('status') == 4:  # 4 = готов
            await db.custom_lessons.update_one(
                {'id': lesson_id},
                {'$set': {'video_status': 'ready'}}
            )
            await db.lessons.update_one(
                {'id': lesson_id},
                {'$set': {'video_status': 'ready'}}
            )

        return {
            'success': True,
            'video_info': video_info,
            'lesson_data': {
                'video_filename': lesson.get('video_filename'),
                'video_uploaded_at': lesson.get('video_uploaded_at'),
                'video_size_mb': lesson.get('video_size_mb')
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения информации: {str(e)}")
