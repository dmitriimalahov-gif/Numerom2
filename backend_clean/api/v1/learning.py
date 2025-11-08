"""
Learning API Router

API endpoints for learning system (lessons, progress, levels)

Source:
- backend/server.py lines 831-1020 (learning endpoints)

Date created: 2025-10-14
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
from datetime import datetime
import random

from models.user import User
from models.credit import CREDIT_COSTS
from api.v1.dependencies import (
    get_current_user,
    get_credit_service
)
from services.credit_service import CreditService
from database.connection import get_database

# Import quiz data from old backend
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

try:
    from quiz_data import NUMEROLOGY_QUIZ
    print("✅ Successfully imported learning/quiz data modules")
except ImportError as e:
    print(f"⚠️  Warning: Could not import quiz modules: {e}")
    NUMEROLOGY_QUIZ = None


router = APIRouter(prefix="/learning", tags=["Learning"])


@router.get(
    "/all-lessons",
    summary="Get all available lessons"
)
async def get_all_student_lessons(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get all available lessons for student (video_lessons + custom_lessons)

    Source: backend/server.py lines 833-895

    **Requires:** Authentication

    **Returns:**
    - user_level: User's current level data
    - available_lessons: List of all active lessons
    - total_levels: Total number of levels (10)

    **Errors:**
    - 500: Error loading lessons
    """
    try:
        user_id = current_user.id
        db = await get_database()

        # Get or create user level
        level = await db.user_levels.find_one({'user_id': user_id})
        if not level:
            from models.lesson import UserLevel
            level = UserLevel(user_id=user_id).dict()
            await db.user_levels.insert_one(level)
            level.pop('_id', None)
        else:
            level = dict(level)
            level.pop('_id', None)

        # Get video lessons
        video_lessons = await db.video_lessons.find(
            {'is_active': True}
        ).sort('level', 1).sort('order', 1).to_list(100)

        # Get custom lessons
        custom_lessons = await db.custom_lessons.find(
            {'is_active': True}
        ).to_list(100)

        # Combine lessons
        all_lessons = []

        # Add video lessons
        for lesson in video_lessons:
            lesson_dict = dict(lesson)
            lesson_dict.pop('_id', None)
            lesson_dict['source'] = 'video_lessons'
            all_lessons.append(lesson_dict)

        # Add custom lessons
        for lesson in custom_lessons:
            lesson_dict = dict(lesson)
            lesson_dict.pop('_id', None)
            lesson_dict['source'] = 'custom_lessons'
            # Set defaults for compatibility
            lesson_dict['level'] = lesson_dict.get('level', 1)
            lesson_dict['order'] = lesson_dict.get('order', 999)
            lesson_dict['duration_minutes'] = lesson_dict.get('duration_minutes', 30)
            lesson_dict['video_url'] = lesson_dict.get('video_url', '')
            lesson_dict['video_file_id'] = lesson_dict.get('video_file_id', '')
            lesson_dict['pdf_file_id'] = lesson_dict.get('pdf_file_id', '')
            all_lessons.append(lesson_dict)

        # Sort: intro lesson first, then by level and order
        all_lessons.sort(key=lambda x: (
            0 if x.get('id') == 'lesson_numerom_intro' else 1,
            x.get('level', 1),
            x.get('order', 999)
        ))

        return {
            'user_level': level,
            'available_lessons': all_lessons,
            'total_levels': 10
        }

    except Exception as e:
        import logging
        logging.error(f"Error getting all student lessons: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка загрузки уроков: {str(e)}"
        )


@router.get(
    "/levels",
    summary="Get learning levels"
)
async def get_learning_levels(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get user's learning level and available lessons

    Source: backend/server.py lines 897-919

    **Requires:** Authentication

    **Returns:**
    - user_level: User's current level
    - available_lessons: List of video lessons
    - total_levels: Total number of levels

    **Errors:**
    - 500: Error loading levels
    """
    user_id = current_user.id
    db = await get_database()

    # Get or create user level
    level = await db.user_levels.find_one({'user_id': user_id})
    if not level:
        from models.lesson import UserLevel
        level = UserLevel(user_id=user_id).dict()
        await db.user_levels.insert_one(level)
        level.pop('_id', None)
    else:
        level = dict(level)
        level.pop('_id', None)

    # Get video lessons
    lessons = await db.video_lessons.find(
        {'is_active': True}
    ).sort('level', 1).sort('order', 1).to_list(100)

    # Clean lessons
    clean_lessons = []
    for lesson in lessons:
        lesson_dict = dict(lesson)
        lesson_dict.pop('_id', None)
        clean_lessons.append(lesson_dict)

    return {
        'user_level': level,
        'available_lessons': clean_lessons,
        'total_levels': 10
    }


@router.post(
    "/lesson/{lesson_id}/start",
    summary="Start a lesson"
)
async def start_lesson(
    lesson_id: str,
    current_user: User = Depends(get_current_user),
    credit_service: CreditService = Depends(get_credit_service)
) -> Dict[str, Any]:
    """
    Start a lesson - costs 10 credits (one-time charge)

    Source: backend/server.py lines 969-1020

    **Requires:** Authentication

    **Path parameters:**
    - lesson_id: Lesson ID

    **Returns:**
    - lesson_started: True if lesson started successfully
    - credits_deducted: Whether credits were deducted

    **Errors:**
    - 404: Lesson not found
    - 402: Insufficient credits
    """
    user_id = current_user.id
    db = await get_database()

    # Check if lesson exists
    lesson = await db.video_lessons.find_one({'id': lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail='Урок не найден')

    # Check if user already started this lesson
    existing_progress = await db.user_progress.find_one({
        'user_id': user_id,
        'lesson_id': lesson_id
    })

    credits_deducted = False

    # Only deduct credits if starting for the first time
    if not existing_progress:
        await credit_service.deduct_credits(
            user_id=user_id,
            cost=CREDIT_COSTS.get('lesson_start', 10),
            description=f'Начало урока: {lesson.get("title", "Урок")}',
            category='learning',
            details={'lesson_id': lesson_id}
        )
        credits_deducted = True

        # Create initial progress record
        progress_data = {
            'user_id': user_id,
            'lesson_id': lesson_id,
            'started': True,
            'start_date': datetime.utcnow(),
            'completed': False,
            'watch_time_minutes': 0
        }
        await db.user_progress.insert_one(progress_data)

    return {
        'lesson_started': True,
        'credits_deducted': credits_deducted,
        'lesson_title': lesson.get('title', 'Урок')
    }


@router.post(
    "/complete-lesson/{lesson_id}",
    summary="Complete a lesson"
)
async def complete_lesson(
    lesson_id: str,
    watch_time: int,
    quiz_score: Optional[int] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Mark a lesson as completed

    Source: backend/server.py lines 921-934

    **Requires:** Authentication

    **Path parameters:**
    - lesson_id: Lesson ID

    **Query parameters:**
    - watch_time: Watch time in minutes
    - quiz_score: Quiz score (optional)

    **Returns:**
    - lesson_completed: True
    - new_level: User's new level
    - total_completed: Total lessons completed

    **Errors:**
    - 404: Lesson not found
    """
    user_id = current_user.id
    db = await get_database()

    # Check if lesson exists
    lesson = await db.video_lessons.find_one({'id': lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail='Lesson not found')

    # Update progress
    progress_data = {
        'user_id': user_id,
        'lesson_id': lesson_id,
        'completed': True,
        'completion_date': datetime.utcnow(),
        'watch_time_minutes': watch_time,
        'quiz_score': quiz_score
    }

    await db.user_progress.update_one(
        {'user_id': user_id, 'lesson_id': lesson_id},
        {'$set': progress_data},
        upsert=True
    )

    # Calculate new level
    completed = await db.user_progress.count_documents({
        'user_id': user_id,
        'completed': True
    })

    new_level = min(10, (completed // 3) + 1)

    # Update user level
    await db.user_levels.update_one(
        {'user_id': user_id},
        {
            '$set': {
                'current_level': new_level,
                'lessons_completed': completed,
                'last_activity': datetime.utcnow()
            },
            '$inc': {'experience_points': 10}
        },
        upsert=True
    )

    return {
        'lesson_completed': True,
        'new_level': new_level,
        'total_completed': completed
    }


@router.get(
    "/lesson/{lesson_id}/quiz",
    summary="Get lesson quiz"
)
async def get_lesson_quiz(
    lesson_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get 5 random quiz questions for a lesson

    Source: backend/server.py lines 936-967

    **Requires:** Authentication

    **Path parameters:**
    - lesson_id: Lesson ID

    **Returns:**
    - lesson_id: Lesson ID
    - lesson_title: Lesson title
    - quiz: Quiz data with questions

    **Errors:**
    - 404: Lesson not found
    - 500: Quiz data not available
    """
    db = await get_database()

    # Check if lesson exists
    lesson = await db.video_lessons.find_one({'id': lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail='Урок не найден')

    if NUMEROLOGY_QUIZ is None:
        raise HTTPException(
            status_code=500,
            detail='Quiz data not available'
        )

    # Get all questions and select random 5
    all_questions = NUMEROLOGY_QUIZ['questions']
    if len(all_questions) <= 5:
        selected_questions = all_questions
    else:
        selected_questions = random.sample(all_questions, 5)

    # Shuffle answer options in each question
    for question in selected_questions:
        random.shuffle(question['options'])

    return {
        'lesson_id': lesson_id,
        'lesson_title': lesson.get('title', 'Урок'),
        'quiz': {
            'title': 'Викторина по уроку',
            'description': f'Ответьте на 5 вопросов по материалу урока "{lesson.get("title", "")}"',
            'questions': selected_questions
        }
    }


__all__ = ['router']
