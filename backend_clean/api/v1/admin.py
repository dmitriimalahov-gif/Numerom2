"""
Admin API Router

API endpoints for admin operations

Source:
- backend/server.py lines 1021-2183 (admin endpoints)

Date created: 2025-10-09
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

from models.user import User
from models.lesson import VideoLesson
from models.consultation import PersonalConsultation
from services.lesson_service import LessonService
from services.consultation_service import ConsultationService
from api.v1.dependencies import get_current_admin_user, get_user_repository, get_current_super_admin
from database.repositories.user_repository import UserRepository
from database.connection import get_database


router = APIRouter(prefix="/admin", tags=["Admin"])


# Temporary dependencies - will be moved to dependencies.py
async def get_lesson_service_admin() -> LessonService:
    from database.connection import get_database
    from database.repositories.lesson_repository import LessonRepository
    from database.repositories.credit_repository import CreditRepository
    from services.credit_service import CreditService

    db = await get_database()
    lesson_repo = LessonRepository(db)
    user_repo = UserRepository(db)
    credit_repo = CreditRepository(db)
    credit_service = CreditService(user_repo, credit_repo)

    return LessonService(lesson_repo, credit_service)


async def get_consultation_service_admin() -> ConsultationService:
    from database.connection import get_database
    from database.repositories.consultation_repository import ConsultationRepository
    from database.repositories.credit_repository import CreditRepository
    from services.credit_service import CreditService

    db = await get_database()
    consultation_repo = ConsultationRepository(db)
    user_repo = UserRepository(db)
    credit_repo = CreditRepository(db)
    credit_service = CreditService(user_repo, credit_repo)

    return ConsultationService(consultation_repo, credit_service)


# ===========================================
# Lesson Management
# ===========================================

@router.get(
    "/lessons",
    summary="Get all lessons (admin)"
)
async def get_all_lessons_admin(
    current_admin: User = Depends(get_current_admin_user),
    lesson_service: LessonService = Depends(get_lesson_service_admin)
):
    """
    Get all lessons including inactive (admin only)

    Source: backend/server.py lines 1302-1313

    **Requires:** Admin or Super Admin role

    **Returns:**
    - List of all lessons (active and inactive)

    **Errors:**
    - 403: Not admin
    """
    return await lesson_service.get_all_lessons_admin()


@router.post(
    "/lessons",
    summary="Create new lesson"
)
async def create_lesson(
    lesson_data: Dict[str, Any],
    current_admin: User = Depends(get_current_admin_user),
    lesson_service: LessonService = Depends(get_lesson_service_admin)
):
    """
    Create new lesson

    Source: backend/server.py lines 1215-1220

    **Requires:** Admin or Super Admin role

    **Body:** VideoLesson model data

    **Returns:**
    - Lesson ID

    **Errors:**
    - 403: Not admin
    """
    lesson_id = await lesson_service.create_lesson(lesson_data)
    return {'lesson_id': lesson_id, 'message': 'Lesson created successfully'}


@router.put(
    "/lessons/{lesson_id}",
    summary="Update lesson"
)
async def update_lesson(
    lesson_id: str,
    lesson_data: Dict[str, Any],
    current_admin: User = Depends(get_current_admin_user),
    lesson_service: LessonService = Depends(get_lesson_service_admin)
):
    """
    Update lesson

    Source: backend/server.py lines 1354-1379

    **Requires:** Admin or Super Admin role

    **Path parameters:**
    - lesson_id: Lesson ID

    **Body:** Partial lesson data to update

    **Returns:**
    - Success message

    **Errors:**
    - 403: Not admin
    - 404: Lesson not found
    """
    success = await lesson_service.update_lesson(lesson_id, lesson_data)
    if not success:
        raise HTTPException(status_code=404, detail='Lesson not found')

    return {'message': 'Lesson updated successfully'}


@router.delete(
    "/lessons/{lesson_id}",
    summary="Delete lesson"
)
async def delete_lesson(
    lesson_id: str,
    current_admin: User = Depends(get_current_admin_user),
    lesson_service: LessonService = Depends(get_lesson_service_admin)
):
    """
    Delete lesson

    Source: backend/server.py lines 1381-1396

    **Requires:** Admin or Super Admin role

    **Path parameters:**
    - lesson_id: Lesson ID

    **Returns:**
    - Success message

    **Errors:**
    - 403: Not admin
    - 404: Lesson not found
    """
    success = await lesson_service.delete_lesson(lesson_id)
    if not success:
        raise HTTPException(status_code=404, detail='Lesson not found')

    return {'message': 'Lesson deleted successfully'}


@router.post(
    "/lessons/sync-first-lesson",
    summary="Sync first lesson from lesson system"
)
async def sync_first_lesson_to_system(
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Synchronize first lesson with general lesson management system

    Source: backend/server.py lines 1222-1299

    **Requires:** Admin or Super Admin role

    **Returns:**
    - Success message with action taken (created or already_exists)

    **Errors:**
    - 403: Not admin
    - 404: First lesson not found in system
    - 500: Sync error
    """
    # Import lesson_system from old backend
    import sys
    import os
    from datetime import datetime

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

    try:
        from lesson_system import lesson_system
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f'Could not import lesson_system: {str(e)}'
        )

    try:
        # Get first lesson data from lesson_system
        first_lesson_data = lesson_system.get_lesson('lesson_numerom_intro')
        if not first_lesson_data:
            raise HTTPException(
                status_code=404,
                detail='Первый урок не найден в системе'
            )

        db = await get_database()

        # Check if lesson already exists in custom_lessons
        existing_lesson = await db.custom_lessons.find_one({'id': 'lesson_numerom_intro'})

        if not existing_lesson:
            # Create record in custom_lessons for first lesson
            first_lesson_record = {
                'id': 'lesson_numerom_intro',
                'title': 'Первое занятие NumerOM',
                'module': 'Модуль 1: Основы',
                'description': 'Введение в NumerOM: История космического корабля и основы нумерологии',
                'points_required': 0,  # Free lesson
                'is_active': True,
                'content': {
                    'theory': {
                        'what_is_topic': 'Введение в мир ведической нумерологии через историю космического корабля',
                        'main_story': first_lesson_data.content.get('theory', {}).get('cosmic_ship_story', ''),
                        'key_concepts': 'Планетарные энергии, численные вибрации, космический корабль как метафора',
                        'practical_applications': 'Анализ своих основных чисел, понимание планетарных энергий'
                    },
                    'exercises': [
                        {
                            'id': ex.id,
                            'title': ex.title,
                            'type': ex.type,
                            'content': ex.content,
                            'instructions': ex.instructions,
                            'expected_outcome': ex.expected_outcome
                        } for ex in first_lesson_data.exercises
                    ],
                    'quiz': {
                        'id': first_lesson_data.quiz.id,
                        'title': first_lesson_data.quiz.title,
                        'questions': first_lesson_data.quiz.questions,
                        'correct_answers': first_lesson_data.quiz.correct_answers,
                        'explanations': first_lesson_data.quiz.explanations
                    },
                    'challenge': {
                        'id': first_lesson_data.challenges[0].id,
                        'title': first_lesson_data.challenges[0].title,
                        'description': first_lesson_data.challenges[0].description,
                        'daily_tasks': first_lesson_data.challenges[0].daily_tasks
                    }
                },
                'source': 'first_lesson_sync',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'created_by': current_admin.id
            }

            # Insert into custom_lessons
            await db.custom_lessons.insert_one(first_lesson_record)

            return {
                'success': True,
                'message': 'Первый урок успешно добавлен в общую систему',
                'action': 'created'
            }
        else:
            return {
                'success': True,
                'message': 'Первый урок уже существует в общей системе',
                'action': 'already_exists'
            }

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Error syncing first lesson: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f'Ошибка синхронизации первого урока: {str(e)}'
        )


# ===========================================
# Consultation Management
# ===========================================

@router.get(
    "/consultations",
    summary="Get all consultations (admin)"
)
async def get_all_consultations_admin(
    current_admin: User = Depends(get_current_admin_user),
    consultation_service: ConsultationService = Depends(get_consultation_service_admin)
):
    """
    Get all consultations (admin only)

    Source: backend/server.py lines 2088-2099

    **Requires:** Admin or Super Admin role

    **Returns:**
    - List of all consultations

    **Errors:**
    - 403: Not admin
    """
    return await consultation_service.get_all_consultations()


@router.post(
    "/consultations",
    summary="Create consultation"
)
async def create_consultation(
    consultation_data: Dict[str, Any],
    current_admin: User = Depends(get_current_admin_user),
    consultation_service: ConsultationService = Depends(get_consultation_service_admin)
):
    """
    Create new consultation

    Source: backend/server.py lines 2158-2168

    **Requires:** Admin or Super Admin role

    **Body:** PersonalConsultation model data

    **Returns:**
    - Consultation ID

    **Errors:**
    - 403: Not admin
    """
    consultation_id = await consultation_service.create_consultation(consultation_data)
    return {'consultation_id': consultation_id, 'message': 'Consultation created successfully'}


@router.put(
    "/consultations/{consultation_id}",
    summary="Update consultation"
)
async def update_consultation(
    consultation_id: str,
    consultation_data: Dict[str, Any],
    current_admin: User = Depends(get_current_admin_user),
    consultation_service: ConsultationService = Depends(get_consultation_service_admin)
):
    """
    Update consultation

    Source: backend/server.py lines 2170-2176

    **Requires:** Admin or Super Admin role

    **Path parameters:**
    - consultation_id: Consultation ID

    **Body:** Partial consultation data

    **Returns:**
    - Success message

    **Errors:**
    - 403: Not admin
    - 404: Consultation not found
    """
    success = await consultation_service.update_consultation(consultation_id, consultation_data)
    if not success:
        raise HTTPException(status_code=404, detail='Consultation not found')

    return {'message': 'Consultation updated successfully'}


@router.delete(
    "/consultations/{consultation_id}",
    summary="Delete consultation"
)
async def delete_consultation(
    consultation_id: str,
    current_admin: User = Depends(get_current_admin_user),
    consultation_service: ConsultationService = Depends(get_consultation_service_admin)
):
    """
    Delete consultation

    Source: backend/server.py lines 2179-2183

    **Requires:** Admin or Super Admin role

    **Path parameters:**
    - consultation_id: Consultation ID

    **Returns:**
    - Success message

    **Errors:**
    - 403: Not admin
    - 404: Consultation not found
    """
    success = await consultation_service.delete_consultation(consultation_id)
    if not success:
        raise HTTPException(status_code=404, detail='Consultation not found')

    return {'message': 'Consultation deleted successfully'}


# ===========================================
# User Management
# ===========================================

@router.get(
    "/users",
    summary="Get all users (admin)"
)
async def get_all_users(
    limit: int = 100,
    offset: int = 0,
    current_admin: User = Depends(get_current_admin_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Get all users (admin only)

    Source: backend/server.py lines 1664-1694

    **Requires:** Admin or Super Admin role

    **Query parameters:**
    - limit: Max results (default 100)
    - offset: Skip N users (default 0)

    **Returns:**
    - List of users
    - Total count

    **Errors:**
    - 403: Not admin
    """
    users = await user_repo.find_all_users(limit=limit, skip=offset)
    total = await user_repo.count_users()

    # Remove sensitive data
    clean_users = []
    for user in users:
        user_dict = dict(user)
        user_dict.pop('_id', None)
        user_dict.pop('password_hash', None)
        clean_users.append(user_dict)

    return {
        'users': clean_users,
        'total': total,
        'limit': limit,
        'offset': offset
    }


@router.patch(
    "/users/{user_id}/credits",
    summary="Adjust user credits (admin)"
)
async def adjust_user_credits(
    user_id: str,
    credits_data: Dict[str, int],
    current_admin: User = Depends(get_current_admin_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Adjust user credits (admin only)

    Source: backend/server.py lines 1696-1723

    **Requires:** Admin or Super Admin role

    **Path parameters:**
    - user_id: User ID

    **Body:**
    - credits_delta: Amount to add (positive) or subtract (negative)

    **Returns:**
    - New credit balance

    **Errors:**
    - 403: Not admin
    - 404: User not found
    """
    credits_delta = credits_data.get('credits_delta', 0)

    user = await user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    success = await user_repo.increment_credits(user_id, credits_delta)
    if not success:
        raise HTTPException(status_code=500, detail='Failed to update credits')

    # Get updated user
    updated_user = await user_repo.find_by_id(user_id)

    return {
        'message': 'Credits adjusted successfully',
        'new_balance': updated_user.get('credits_remaining', 0)
    }


@router.post(
    "/make-admin/{user_id}",
    summary="Grant admin role"
)
async def make_admin(
    user_id: str,
    current_admin: User = Depends(get_current_admin_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Grant admin role to user

    Source: backend/server.py lines 1416-1435

    **Requires:** Admin or Super Admin role

    **Path parameters:**
    - user_id: User ID

    **Returns:**
    - Success message

    **Errors:**
    - 403: Not admin
    - 404: User not found
    """
    user = await user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    await user_repo.update_user(user_id, {'is_admin': True})

    return {'message': 'User granted admin role successfully'}


@router.delete(
    "/revoke-admin/{user_id}",
    summary="Revoke admin role"
)
async def revoke_admin(
    user_id: str,
    current_admin: User = Depends(get_current_admin_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Revoke admin role from user

    Source: backend/server.py lines 1437-1460

    **Requires:** Admin or Super Admin role

    **Path parameters:**
    - user_id: User ID

    **Returns:**
    - Success message

    **Errors:**
    - 403: Not admin
    - 404: User not found
    """
    user = await user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    await user_repo.update_user(user_id, {'is_admin': False})

    return {'message': 'Admin role revoked successfully'}


# ===========================================
# Lesson Content Management
# ===========================================

@router.get(
    "/lesson-content/{lesson_id}",
    summary="Get lesson content for editing"
)
async def get_lesson_content_for_editing(
    lesson_id: str,
    current_admin: User = Depends(get_current_super_admin)
):
    """
    Get all customized lesson content for editing

    Source: backend/server.py lines 4598-4650

    **Requires:** Super Admin role

    **Path parameters:**
    - lesson_id: Lesson ID

    **Returns:**
    - Lesson content with custom exercises, quiz questions, and challenge days

    **Errors:**
    - 403: Not super admin
    - 404: Lesson not found
    """
    db = await get_database()

    # Get basic lesson - check both video_lessons and custom_lessons
    lesson = await db.video_lessons.find_one({'id': lesson_id})
    if not lesson:
        lesson = await db.custom_lessons.find_one({'id': lesson_id})

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    lesson_dict = dict(lesson)
    lesson_dict.pop('_id', None)

    # Get custom exercises
    custom_exercises = await db.lesson_exercises.find({
        "lesson_id": lesson_id,
        "content_type": "exercise_update"
    }).to_list(100)

    # Clean exercises
    for ex in custom_exercises:
        ex.pop('_id', None)

    # Get custom quiz questions
    custom_quiz_questions = await db.lesson_quiz_questions.find({
        "lesson_id": lesson_id,
        "content_type": "quiz_question_update"
    }).to_list(100)

    # Clean quiz questions
    for q in custom_quiz_questions:
        q.pop('_id', None)

    # Get custom challenge days
    custom_challenge_days = await db.lesson_challenge_days.find({
        "lesson_id": lesson_id,
        "content_type": "challenge_day_update"
    }).to_list(100)

    # Clean challenge days
    for day in custom_challenge_days:
        day.pop('_id', None)

    return {
        'lesson': lesson_dict,
        'custom_exercises': custom_exercises,
        'custom_quiz_questions': custom_quiz_questions,
        'custom_challenge_days': custom_challenge_days
    }


# ===========================================
# Theory Sections Management
# ===========================================

@router.get(
    "/theory-sections",
    summary="Get custom theory sections"
)
async def get_theory_sections(
    current_admin: User = Depends(get_current_super_admin)
):
    """
    Get list of custom theory sections

    Source: backend/server.py lines 4654-4678

    **Requires:** Super Admin role

    **Returns:**
    - theory_sections: List of custom theory sections
    - count: Number of sections

    **Errors:**
    - 403: Not super admin
    - 500: Database error
    """
    from datetime import datetime

    try:
        db = await get_database()

        # Get custom theory sections from database
        theory_sections = await db.lesson_theory_sections.find({}).to_list(None)

        # Convert ObjectId to string
        for section in theory_sections:
            section['id'] = str(section['_id'])
            del section['_id']

        return {
            "theory_sections": theory_sections,
            "count": len(theory_sections)
        }

    except Exception as e:
        import logging
        logging.error(f"Error getting theory sections: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting theory sections: {str(e)}"
        )


__all__ = ['router']
