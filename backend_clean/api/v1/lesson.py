"""
Lesson API Router

API endpoints for learning management system (LMS)

Source:
- backend/server.py lines 848-1014 (learning endpoints)

Date created: 2025-10-09
"""

from fastapi import APIRouter, Depends
from typing import Optional

from models.user import User
from services.lesson_service import LessonService
from api.v1.dependencies import get_current_user


router = APIRouter(prefix="/learning", tags=["Learning"])


# Dependency will be added later
async def get_lesson_service() -> LessonService:
    """Temporary placeholder - will be implemented in dependencies.py"""
    from database.connection import get_database
    from database.repositories.lesson_repository import LessonRepository
    from database.repositories.user_repository import UserRepository
    from database.repositories.credit_repository import CreditRepository
    from services.credit_service import CreditService

    db = await get_database()
    lesson_repo = LessonRepository(db)
    user_repo = UserRepository(db)
    credit_repo = CreditRepository(db)
    credit_service = CreditService(user_repo, credit_repo)

    return LessonService(lesson_repo, credit_service)


# ===========================================
# Get Lessons
# ===========================================

@router.get(
    "/dashboard",
    summary="Get all lessons with user progress"
)
async def get_learning_dashboard(
    current_user: User = Depends(get_current_user),
    lesson_service: LessonService = Depends(get_lesson_service)
):
    """
    Get all active lessons with user progress

    Source: backend/server.py lines 848-890

    **Requires authorization:** Bearer token in Authorization header

    **Returns:**
    - lessons: List of all active lessons with user progress
      - Each lesson includes:
        - Lesson data (id, title, description, video_url, etc.)
        - user_progress: {completed, watch_time_minutes, quiz_score}
    - user_level: User's current level info
      - current_level: 1-10
      - experience_points: Total XP
      - lessons_completed: Number of completed lessons

    **Logic:**
    - Lessons are sorted by level and order
    - Progress shows completion status and quiz scores
    - Level increases every 3 completed lessons
    """
    return await lesson_service.get_all_lessons(current_user.id)


@router.get(
    "/lessons",
    summary="Get all lessons (public)"
)
async def get_lessons_public(
    lesson_service: LessonService = Depends(get_lesson_service)
):
    """
    Get all active lessons without progress (public access)

    Source: backend/server.py lines 908-919

    **No authorization required**

    **Returns:**
    - List of all active lessons
    - Sorted by level and order
    - No user progress data

    **Use case:**
    - Public lesson catalog
    - Preview for non-registered users
    """
    return await lesson_service.get_lessons_public()


# ===========================================
# Start Lesson
# ===========================================

@router.post(
    "/lesson/{lesson_id}/start",
    summary="Start a lesson - costs 10 credits (one-time)"
)
async def start_lesson(
    lesson_id: str,
    current_user: User = Depends(get_current_user),
    lesson_service: LessonService = Depends(get_lesson_service)
):
    """
    Start a lesson - deduct 10 credits (one-time payment)

    Source: backend/server.py lines 969-1011

    **Requires authorization:** Bearer token in Authorization header

    **Path parameters:**
    - lesson_id: ID of the lesson to start

    **Cost:** 10 credits (charged only once per lesson)

    **Returns:**
    - lesson_started: True
    - points_deducted: Number of credits deducted (0 if already started)
    - message: Status message

    **Logic:**
    - Checks if lesson was already started
    - If already started, returns success without charging
    - If new, deducts 10 credits and creates initial progress
    - Creates user_progress record with completed=False

    **Errors:**
    - 404: Lesson not found
    - 402: Insufficient credits
    """
    return await lesson_service.start_lesson(
        user_id=current_user.id,
        lesson_id=lesson_id
    )


# ===========================================
# Complete Lesson
# ===========================================

@router.post(
    "/lesson/{lesson_id}/complete",
    summary="Mark lesson as completed"
)
async def complete_lesson(
    lesson_id: str,
    watch_time: int,
    quiz_score: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    lesson_service: LessonService = Depends(get_lesson_service)
):
    """
    Mark lesson as completed

    Source: backend/server.py lines 921-934

    **Requires authorization:** Bearer token in Authorization header

    **Path parameters:**
    - lesson_id: ID of the lesson

    **Query parameters:**
    - watch_time: Watch time in minutes
    - quiz_score: Quiz score 0-100 (optional)

    **Returns:**
    - lesson_completed: True
    - new_level: User's new level (1-10)
    - total_completed: Total number of completed lessons

    **Logic:**
    - Updates user_progress with completion data
    - Calculates new level: (completed // 3) + 1, max 10
    - Adds 10 experience points
    - Updates user_level table

    **Errors:**
    - 404: Lesson not found
    """
    return await lesson_service.complete_lesson(
        user_id=current_user.id,
        lesson_id=lesson_id,
        watch_time=watch_time,
        quiz_score=quiz_score
    )


# ===========================================
# Quiz
# ===========================================

@router.get(
    "/lesson/{lesson_id}/quiz",
    summary="Get quiz for lesson"
)
async def get_lesson_quiz(
    lesson_id: str,
    current_user: User = Depends(get_current_user),
    lesson_service: LessonService = Depends(get_lesson_service)
):
    """
    Get 5 random quiz questions for lesson

    Source: backend/server.py lines 936-967

    **Requires authorization:** Bearer token in Authorization header

    **Path parameters:**
    - lesson_id: ID of the lesson

    **Returns:**
    - lesson_id: Lesson ID
    - lesson_title: Lesson title
    - quiz: Quiz object
      - title: Quiz title
      - description: Quiz description
      - questions: List of 5 random questions
        - Each question has shuffled options

    **Logic:**
    - Selects 5 random questions from quiz pool
    - Shuffles answer options in each question
    - If less than 5 questions available, returns all

    **Errors:**
    - 404: Lesson not found
    """
    return await lesson_service.get_lesson_quiz(lesson_id)


# ===========================================
# Statistics
# ===========================================

@router.get(
    "/stats",
    summary="Get learning statistics"
)
async def get_learning_stats(
    current_user: User = Depends(get_current_user),
    lesson_service: LessonService = Depends(get_lesson_service)
):
    """
    Get user's learning statistics

    **Requires authorization:** Bearer token in Authorization header

    **Returns:**
    - level: Current level (1-10)
    - experience_points: Total XP earned
    - lessons_completed: Number of completed lessons
    - total_lessons: Total active lessons available
    - completion_rate: Percentage of completed lessons
    - average_quiz_score: Average quiz score
    """
    return await lesson_service.get_user_stats(current_user.id)


# ===========================================
# Additional Files (PDFs and Videos)
# ===========================================

# Create a separate router for /lessons prefix
from fastapi import APIRouter as FastAPIRouter

lessons_files_router = FastAPIRouter(prefix="/lessons", tags=["Lessons"])


@lessons_files_router.get(
    "/{lesson_id}/additional-pdfs",
    summary="Get additional PDF files for lesson"
)
async def get_lesson_additional_pdfs(lesson_id: str):
    """
    Get all additional PDF files for a lesson

    Source: backend/server.py lines 3824-3852

    **Path parameters:**
    - lesson_id: Lesson ID

    **Returns:**
    - lesson_id: Lesson ID
    - additional_pdfs: List of PDF files
      - file_id: File ID
      - filename: Original filename
      - title: PDF title
      - pdf_url: URL to download PDF
      - uploaded_at: Upload timestamp
    - count: Number of PDFs

    **Logic:**
    - Searches uploaded_files collection for consultation_pdf type
    - Returns list of PDFs linked to this lesson
    """
    from database.connection import get_database

    try:
        db = await get_database()

        # Find all PDF files linked to this lesson
        pdf_cursor = db.uploaded_files.find({
            'lesson_id': lesson_id,
            'file_type': 'consultation_pdf'
        })

        pdfs = []
        async for pdf_record in pdf_cursor:
            pdfs.append({
                'file_id': pdf_record['id'],
                'filename': pdf_record['original_filename'],
                'title': pdf_record.get('pdf_title', pdf_record['original_filename']),
                'pdf_url': f'/api/consultations/pdf/{pdf_record["id"]}',
                'uploaded_at': pdf_record.get('uploaded_at')
            })

        return {
            'lesson_id': lesson_id,
            'additional_pdfs': pdfs,
            'count': len(pdfs)
        }

    except Exception as e:
        import logging
        logging.error(f"Error getting lesson additional PDFs: {str(e)}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Error getting PDFs: {str(e)}")


@lessons_files_router.get(
    "/{lesson_id}/additional-videos",
    summary="Get additional video files for lesson"
)
async def get_lesson_additional_videos(lesson_id: str):
    """
    Get all additional video files for a lesson

    Source: backend/server.py lines 3910-3938

    **Path parameters:**
    - lesson_id: Lesson ID

    **Returns:**
    - lesson_id: Lesson ID
    - additional_videos: List of video files
      - file_id: File ID
      - filename: Original filename
      - title: Video title
      - video_url: URL to stream video
      - uploaded_at: Upload timestamp
    - count: Number of videos

    **Logic:**
    - Searches uploaded_files collection for consultation_video type
    - Returns list of videos linked to this lesson
    """
    from database.connection import get_database

    try:
        db = await get_database()

        # Find all video files linked to this lesson
        video_cursor = db.uploaded_files.find({
            'lesson_id': lesson_id,
            'file_type': 'consultation_video'
        })

        videos = []
        async for video_record in video_cursor:
            videos.append({
                'file_id': video_record['id'],
                'filename': video_record['original_filename'],
                'title': video_record.get('video_title', video_record['original_filename']),
                'video_url': f'/api/consultations/video/{video_record["id"]}',
                'uploaded_at': video_record.get('uploaded_at')
            })

        return {
            'lesson_id': lesson_id,
            'additional_videos': videos,
            'count': len(videos)
        }

    except Exception as e:
        import logging
        logging.error(f"Error getting lesson additional videos: {str(e)}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Error getting videos: {str(e)}")


__all__ = ['router', 'lessons_files_router']
