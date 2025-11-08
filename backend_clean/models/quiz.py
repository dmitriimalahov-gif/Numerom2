"""
Quiz Models

Pydantic models for quiz/assessment functionality

Source:
- backend/models.py (QuizResult)

Date created: 2025-10-14
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class QuizResult(BaseModel):
    """
    Quiz Result model

    Stores user's quiz/assessment results
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    quiz_type: str  # e.g., 'numerology_assessment'
    answers: List[Dict[str, Any]]
    score: int
    recommendations: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "787a67ea-b697-470d-9b06-b1eda5ad489b",
                "quiz_type": "numerology_assessment",
                "answers": [
                    {"question_id": 1, "answer": "A"},
                    {"question_id": 2, "answer": "B"}
                ],
                "score": 85,
                "recommendations": [
                    "Развивайте интуицию",
                    "Больше времени проводите в размышлениях"
                ],
                "created_at": "2025-10-14T12:00:00Z"
            }
        }


__all__ = ['QuizResult']
