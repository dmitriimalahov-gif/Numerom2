"""
Quiz API Router

API endpoints for numerology quiz/assessment

Source:
- backend/server.py lines 797-829 (quiz endpoints)

Date created: 2025-10-14
"""

from fastapi import APIRouter, Depends
from typing import List, Dict, Any
import uuid
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
    from quiz_data import NUMEROLOGY_QUIZ, calculate_quiz_results
    print("✅ Successfully imported quiz data modules")
except ImportError as e:
    print(f"⚠️  Warning: Could not import quiz modules: {e}")
    NUMEROLOGY_QUIZ = None
    calculate_quiz_results = None


router = APIRouter(prefix="/quiz", tags=["Quiz"])


@router.get(
    "/randomized-questions",
    summary="Get randomized quiz questions"
)
async def get_quiz_questions() -> Dict[str, Any]:
    """
    Get randomized quiz questions (no authentication required)

    Source: backend/server.py lines 798-809

    **Returns:**
    - session_id: Unique session ID
    - title: Quiz title
    - description: Quiz description
    - questions: List of 10 randomized questions

    **Errors:**
    - 500: Quiz data not available
    """
    if NUMEROLOGY_QUIZ is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail='Quiz data not available'
        )

    questions = NUMEROLOGY_QUIZ['questions'].copy()
    random.shuffle(questions)

    return {
        'session_id': str(uuid.uuid4()),
        'title': NUMEROLOGY_QUIZ['title'],
        'description': NUMEROLOGY_QUIZ['description'],
        'questions': questions[:10]
    }


@router.post(
    "/submit",
    summary="Submit quiz answers"
)
async def submit_quiz(
    answers: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    credit_service: CreditService = Depends(get_credit_service)
) -> Dict[str, Any]:
    """
    Submit quiz answers and get results - costs 1 credit

    Source: backend/server.py lines 811-829

    **Requires:** Authentication

    **Body:**
    - answers: List of answer dictionaries

    **Returns:**
    - Quiz results with score and recommendations

    **Errors:**
    - 402: Insufficient credits
    - 500: Quiz calculation module not available
    """
    if calculate_quiz_results is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail='Quiz calculation module not available'
        )

    user_id = current_user.id

    # Deduct credits
    await credit_service.deduct_credits(
        user_id=user_id,
        cost=CREDIT_COSTS.get('quiz_completion', 1),
        description='Прохождение викторины',
        category='quiz',
        details={'quiz_type': 'numerology_assessment'}
    )

    # Calculate results
    results = calculate_quiz_results(answers)

    # Save quiz result to database
    from models.quiz import QuizResult
    quiz_result = QuizResult(
        user_id=user_id,
        quiz_type='numerology_assessment',
        answers=answers,
        score=results.get('total_score', 0),
        recommendations=results.get('recommendations', [])
    )

    db = await get_database()
    await db.quiz_results.insert_one(quiz_result.dict())

    return results


__all__ = ['router']
