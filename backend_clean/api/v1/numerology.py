"""
Numerology API Router

API endpoints for numerology calculations

Source:
- backend/server.py lines 413-540 (numerology endpoints)

Date created: 2025-10-09
"""

from fastapi import APIRouter, Depends
from typing import Optional

from models.user import User
from models.numerology import (
    FreeCalculationRequest,
    CompatibilityRequest,
    GroupCompatibilityRequest
)
from services.numerology_service import NumerologyService
from api.v1.dependencies import get_current_user


router = APIRouter(prefix="/numerology", tags=["Numerology"])


# Dependency will be added later
async def get_numerology_service() -> NumerologyService:
    """Temporary placeholder - will be implemented in dependencies.py"""
    from database.connection import get_database
    from database.repositories.user_repository import UserRepository
    from database.repositories.numerology_repository import NumerologyRepository
    from database.repositories.credit_repository import CreditRepository
    from services.credit_service import CreditService

    db = await get_database()
    user_repo = UserRepository(db)
    numerology_repo = NumerologyRepository(db)
    credit_repo = CreditRepository(db)
    credit_service = CreditService(user_repo, credit_repo)

    return NumerologyService(user_repo, numerology_repo, credit_service)


# ===========================================
# Personal Numbers
# ===========================================

@router.post(
    "/personal-numbers",
    summary="Calculate personal numbers - costs 1 credit"
)
async def calculate_personal_numbers(
    birth_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    numerology_service: NumerologyService = Depends(get_numerology_service)
):
    """
    Calculate personal numbers

    Source: backend/server.py lines 413-438

    **Requires authorization:** Bearer token in Authorization header

    **Query parameters:**
    - birth_date: Birth date in DD.MM.YYYY format (optional, uses profile if not provided)

    **Cost:** 1 credit

    **Returns:**
    - soul_number: Soul number
    - mind_number: Mind number
    - destiny_number: Destiny number
    - helping_mind_number: Helping mind number
    - wisdom_number: Wisdom number
    - ruling_number: Ruling number
    - planetary_strength: Planetary strength map
    - birth_weekday: Birth weekday

    **Errors:**
    - 404: User not found
    - 402: Insufficient credits
    """
    return await numerology_service.calculate_personal_numbers(
        user_id=current_user.id,
        birth_date=birth_date
    )


# ===========================================
# Pythagorean Square
# ===========================================

@router.post(
    "/pythagorean-square",
    summary="Calculate Pythagorean square - costs 1 credit"
)
async def calculate_pythagorean_square(
    birth_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    numerology_service: NumerologyService = Depends(get_numerology_service)
):
    """
    Calculate Pythagorean square

    Source: backend/server.py lines 440-466

    **Requires authorization:** Bearer token in Authorization header

    **Query parameters:**
    - birth_date: Birth date in DD.MM.YYYY format (optional, uses profile if not provided)

    **Cost:** 1 credit

    **Returns:**
    - square: 3x3 matrix with numbers
    - horizontal_sums: Horizontal line sums
    - vertical_sums: Vertical line sums
    - diagonal_sums: Diagonal line sums
    - additional_numbers: Additional numbers
    - planet_positions: Planetary positions

    **Errors:**
    - 404: User not found
    - 402: Insufficient credits
    """
    return await numerology_service.calculate_pythagorean_square(
        user_id=current_user.id,
        birth_date=birth_date
    )


# ===========================================
# Compatibility
# ===========================================

@router.post(
    "/compatibility",
    summary="Calculate compatibility between two people - costs 1 credit"
)
async def calculate_compatibility(
    request_data: CompatibilityRequest,
    current_user: User = Depends(get_current_user),
    numerology_service: NumerologyService = Depends(get_numerology_service)
):
    """
    Calculate compatibility between two people

    Source: backend/server.py lines 468-492

    **Requires authorization:** Bearer token in Authorization header

    **Body parameters:**
    - person1_birth_date: First person birth date (DD.MM.YYYY)
    - person2_birth_date: Second person birth date (DD.MM.YYYY)
    - person1_name: First person name (optional, default "Person 1")
    - person2_name: Second person name (optional, default "Person 2")

    **Cost:** 1 credit

    **Returns:**
    - Compatibility analysis between two people
    - Compatibility scores
    - Recommendations

    **Errors:**
    - 402: Insufficient credits
    """
    return await numerology_service.calculate_compatibility(
        user_id=current_user.id,
        person1_birth_date=request_data.person1_birth_date,
        person2_birth_date=request_data.person2_birth_date,
        person1_name=request_data.person1_name,
        person2_name=request_data.person2_name
    )


# ===========================================
# Group Compatibility
# ===========================================

@router.post(
    "/group-compatibility",
    summary="Calculate group compatibility - costs 1 credit"
)
async def calculate_group_compatibility(
    request_data: GroupCompatibilityRequest,
    current_user: User = Depends(get_current_user),
    numerology_service: NumerologyService = Depends(get_numerology_service)
):
    """
    Calculate group compatibility (up to 5 people)

    Source: backend/server.py lines 494-524

    **Requires authorization:** Bearer token in Authorization header

    **Body parameters:**
    - main_person_birth_date: Main person birth date (DD.MM.YYYY)
    - main_person_name: Main person name (default "You")
    - people: List of people to compare (max 5)
      - name: Person name
      - birth_date: Person birth date (DD.MM.YYYY)

    **Cost:** 1 credit

    **Returns:**
    - Group compatibility analysis
    - Individual compatibility with each person
    - Overall group dynamics

    **Errors:**
    - 400: Too many people (max 5)
    - 402: Insufficient credits
    """
    return await numerology_service.calculate_group_compatibility(
        user_id=current_user.id,
        main_person_birth_date=request_data.main_person_birth_date,
        main_person_name=request_data.main_person_name,
        people=[p.dict() for p in request_data.people]
    )


# ===========================================
# Free Calculation (No Auth)
# ===========================================

@router.post(
    "/free-calculation",
    summary="Free calculation without authorization"
)
async def free_calculation(
    request_data: FreeCalculationRequest,
    numerology_service: NumerologyService = Depends(get_numerology_service)
):
    """
    Free calculation without authorization

    Source: backend/server.py lines 526-540

    **No authorization required**

    **Body parameters:**
    - birth_date: Birth date in DD.MM.YYYY format

    **Cost:** Free (no credits required)

    **Returns:**
    - Basic personal numbers
    - Limited information compared to paid calculation

    **Use case:**
    - Demo for non-registered users
    - Lead generation
    """
    return await numerology_service.free_calculation(
        birth_date=request_data.birth_date
    )


# ===========================================
# History
# ===========================================

@router.get(
    "/history",
    summary="Get calculation history"
)
async def get_calculation_history(
    calculation_type: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    numerology_service: NumerologyService = Depends(get_numerology_service)
):
    """
    Get user's calculation history

    **Requires authorization:** Bearer token in Authorization header

    **Query parameters:**
    - calculation_type: Filter by type (optional)
      - personal_numbers
      - pythagorean_square
      - compatibility
      - group_compatibility
    - limit: Maximum number of results (default 50)

    **Returns:**
    - List of calculations sorted by date (newest first)
    """
    return await numerology_service.get_user_calculations(
        user_id=current_user.id,
        calculation_type=calculation_type,
        limit=limit
    )


# ===========================================
# Statistics
# ===========================================

@router.get(
    "/stats",
    summary="Get calculation statistics"
)
async def get_calculation_stats(
    current_user: User = Depends(get_current_user),
    numerology_service: NumerologyService = Depends(get_numerology_service)
):
    """
    Get user's calculation statistics

    **Requires authorization:** Bearer token in Authorization header

    **Returns:**
    - Count by calculation type
    - Total calculations
    """
    return await numerology_service.get_calculation_stats(
        user_id=current_user.id
    )


__all__ = ['router']
