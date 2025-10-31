"""
Endpoint для ручной привязки video_id из Bunny.net к уроку
Используется когда видео загружено напрямую через панель Bunny.net
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

manual_link_router = APIRouter(prefix="/api/admin", tags=["Bunny Manual Link"])


class ManualVideoLink(BaseModel):
    """Модель для ручной привязки видео"""
    video_id: str
    lesson_id: str
    video_title: str = None


@manual_link_router.post('/lessons/link-bunny-video')
async def link_existing_bunny_video(
    data: ManualVideoLink,
    current_user: dict = Depends(lambda: None)  # Placeholder для auth
):
    """
    Привязать существующее видео из Bunny.net к уроку

    Используется когда:
    1. Видео загружено напрямую через https://dash.bunny.net/stream
    2. Нужно привязать его к уроку в вашей системе

    Args:
        data: {
            "video_id": "abc-123-def",  // ID из Bunny.net
            "lesson_id": "lesson_intro",
            "video_title": "Название видео"  // опционально
        }

    Returns:
        {
            "success": true,
            "message": "Видео успешно привязано к уроку"
        }
    """
    try:
        # TODO: Раскомментировать после интеграции auth
        # from server import check_admin_rights
        # admin_user = await check_admin_rights(current_user, require_super_admin=False)

        from server import db
        from video_platforms.bunny_stream import get_bunny_service

        # Проверяем существует ли видео на Bunny
        bunny_service = get_bunny_service()
        try:
            video_info = await bunny_service.get_video_info(data.video_id)
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Видео с ID {data.video_id} не найдено на Bunny.net: {str(e)}"
            )

        # Проверяем статус видео
        status = video_info.get('status', 0)
        video_status = 'processing' if status == 3 else 'ready' if status == 4 else 'unknown'

        # Извлекаем информацию о видео
        video_title = data.video_title or video_info.get('title', f'Видео урока {data.lesson_id}')

        # Подготавливаем данные для обновления
        update_data = {
            'video_platform': 'bunny',
            'video_id': data.video_id,
            'video_library_id': bunny_service.library_id,
            'video_thumbnail': f"https://{bunny_service.cdn_hostname}/{data.video_id}/thumbnail.jpg",
            'video_iframe_url': f"https://iframe.mediadelivery.net/embed/{bunny_service.library_id}/{data.video_id}",
            'video_status': video_status,
            'video_uploaded_at': datetime.utcnow(),
            'video_filename': video_title,
            'video_size_mb': video_info.get('storageSize', 0) / (1024 * 1024) if video_info.get('storageSize') else 0,
            'video_duration_seconds': video_info.get('length', 0),
            'video_width': video_info.get('width', 0),
            'video_height': video_info.get('height', 0)
        }

        # Обновляем урок
        result = await db.custom_lessons.update_one(
            {'id': data.lesson_id},
            {'$set': update_data}
        )

        if result.matched_count == 0:
            # Пробуем в lessons
            result2 = await db.lessons.update_one(
                {'id': data.lesson_id},
                {'$set': update_data}
            )

            if result2.matched_count == 0:
                # Создаем новую запись
                logger.warning(f"Lesson {data.lesson_id} not found, creating new record")
                await db.custom_lessons.insert_one({
                    'id': data.lesson_id,
                    'title': video_title,
                    'is_active': True,
                    'created_at': datetime.utcnow(),
                    **update_data
                })

        logger.info(f"Video {data.video_id} linked to lesson {data.lesson_id}")

        return {
            'success': True,
            'message': f'Видео успешно привязано к уроку {data.lesson_id}',
            'video_info': {
                'video_id': data.video_id,
                'status': video_status,
                'resolution': f"{video_info.get('width')}x{video_info.get('height')}",
                'duration': f"{video_info.get('length', 0)} секунд",
                'thumbnail': update_data['video_thumbnail']
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking Bunny video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка привязки видео: {str(e)}")


@manual_link_router.get('/lessons/{lesson_id}/bunny-video-id')
async def get_lesson_bunny_video_id(
    lesson_id: str,
    current_user: dict = Depends(lambda: None)
):
    """
    Получить video_id привязанный к уроку

    Полезно для проверки какое видео привязано к уроку
    """
    try:
        from server import db

        lesson = await db.custom_lessons.find_one({'id': lesson_id})
        if not lesson:
            lesson = await db.lessons.find_one({'id': lesson_id})

        if not lesson:
            raise HTTPException(status_code=404, detail="Урок не найден")

        video_id = lesson.get('video_id')
        video_platform = lesson.get('video_platform')

        if not video_id or video_platform != 'bunny':
            return {
                'success': False,
                'message': 'Видео не привязано к этому уроку или не на Bunny платформе'
            }

        return {
            'success': True,
            'lesson_id': lesson_id,
            'video_id': video_id,
            'video_status': lesson.get('video_status'),
            'video_thumbnail': lesson.get('video_thumbnail'),
            'video_resolution': f"{lesson.get('video_width')}x{lesson.get('video_height')}",
            'bunny_dashboard_url': f"https://dash.bunny.net/stream/{lesson.get('video_library_id')}/video/{video_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video ID: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


__all__ = ['manual_link_router']
