"""
Consultation API Router

API endpoints for personal consultations

Source:
- backend/server.py lines 2404-2424 (user consultation access)
- backend/server.py lines 2597-2644 (consultation purchase)

Date created: 2025-10-09
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from models.user import User
from services.consultation_service import ConsultationService
from api.v1.dependencies import get_current_user


router = APIRouter(prefix="/consultations", tags=["Consultations"])


# Dependency will be added later
async def get_consultation_service() -> ConsultationService:
    """Temporary placeholder - will be implemented in dependencies.py"""
    from database.connection import get_database
    from database.repositories.consultation_repository import ConsultationRepository
    from database.repositories.user_repository import UserRepository
    from database.repositories.credit_repository import CreditRepository
    from services.credit_service import CreditService

    db = await get_database()
    consultation_repo = ConsultationRepository(db)
    user_repo = UserRepository(db)
    credit_repo = CreditRepository(db)
    credit_service = CreditService(user_repo, credit_repo)

    return ConsultationService(consultation_repo, credit_service)


# ===========================================
# Get User Consultations
# ===========================================

@router.get(
    "/my",
    summary="Get consultations assigned to current user"
)
async def get_my_consultations(
    current_user: User = Depends(get_current_user),
    consultation_service: ConsultationService = Depends(get_consultation_service)
):
    """
    Get consultations assigned to current user

    Source: backend/server.py lines 2404-2424

    **Requires authorization:** Bearer token in Authorization header

    **Returns:**
    - List of consultations assigned to user
    - Each consultation includes:
      - id: Consultation ID
      - title: Consultation title
      - description: Description
      - video_url: Video URL (if available)
      - video_file_id: Video file ID (if uploaded)
      - pdf_file_id: PDF file ID (if available)
      - subtitles_file_id: Subtitles file ID (if available)
      - cost_credits: Cost in credits
      - is_active: Active status
      - is_purchased: Whether user has purchased this consultation

    **Logic:**
    - Shows only active consultations
    - Includes purchase status for each consultation
    - User can see which consultations they have access to
    """
    return await consultation_service.get_user_consultations(current_user.id)


# ===========================================
# Purchase Consultation
# ===========================================

@router.post(
    "/{consultation_id}/purchase",
    summary="Purchase consultation with credits"
)
async def purchase_consultation(
    consultation_id: str,
    current_user: User = Depends(get_current_user),
    consultation_service: ConsultationService = Depends(get_consultation_service)
) -> Dict[str, Any]:
    """
    Purchase consultation with credits

    Source: backend/server.py lines 2597-2644

    **Requires authorization:** Bearer token in Authorization header

    **Path parameters:**
    - consultation_id: ID of consultation to purchase

    **Cost:** Default 6667 credits (can vary by consultation)

    **Returns:**
    - success: True
    - consultation_id: ID of purchased consultation
    - credits_spent: Number of credits deducted
    - message: Success message

    **Logic:**
    - Checks if consultation exists and is assigned to user
    - Checks if already purchased (prevents double purchase)
    - Deducts credits from user balance
    - Records purchase in consultation_purchases collection
    - After purchase, user can access consultation materials

    **Errors:**
    - 404: Consultation not found or not assigned to user
    - 400: Consultation already purchased
    - 402: Insufficient credits
    """
    return await consultation_service.purchase_consultation(
        user_id=current_user.id,
        consultation_id=consultation_id
    )


# ===========================================
# Statistics
# ===========================================

@router.get(
    "/stats",
    summary="Get consultation statistics"
)
async def get_consultation_stats(
    current_user: User = Depends(get_current_user),
    consultation_service: ConsultationService = Depends(get_consultation_service)
):
    """
    Get user's consultation statistics

    **Requires authorization:** Bearer token in Authorization header

    **Returns:**
    - total_assigned: Number of consultations assigned to user
    - total_purchased: Number of consultations purchased
    - total_credits_spent: Total credits spent on consultations
    """
    return await consultation_service.get_user_consultation_stats(current_user.id)


__all__ = ['router']
