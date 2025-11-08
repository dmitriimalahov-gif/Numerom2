"""
User Profile API Router

API endpoints for user profile management

Source:
- backend/server.py lines 2958-2994 (user profile endpoints)

Date created: 2025-10-09
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Any

from models.user import User, UserResponse, UserProfileUpdate, create_user_response
from api.v1.dependencies import get_current_user, get_user_repository
from database.repositories.user_repository import UserRepository
from database.connection import get_database
from datetime import datetime


router = APIRouter(prefix="/user", tags=["User Profile"])


# ===========================================
# Get Profile
# ===========================================

@router.get(
    "/profile",
    response_model=UserResponse,
    summary="Get user profile"
)
async def get_profile(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Get current user profile

    Source: backend/server.py lines 2958-2963

    **Requires authorization:** Bearer token in Authorization header

    **Returns:**
    - Full user profile (without password_hash)
    - Includes credits, subscription info, etc.

    **Errors:**
    - 401: Invalid or missing token
    - 404: User not found
    """
    return create_user_response(current_user)


# ===========================================
# Update Profile
# ===========================================

@router.patch(
    "/profile",
    response_model=UserResponse,
    summary="Update user profile"
)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
) -> UserResponse:
    """
    Update user profile

    Source: backend/server.py lines 2965-2986

    **Requires authorization:** Bearer token in Authorization header

    **Body parameters (all optional):**
    - full_name: Full name
    - birth_date: Birth date (DD.MM.YYYY)
    - city: City
    - phone_number: Phone number

    **Returns:**
    - Updated user profile

    **Logic:**
    - Only updates provided fields (exclude_unset)
    - Automatically sets updated_at timestamp
    - Returns fresh user data after update

    **Errors:**
    - 401: Invalid or missing token
    - 404: User not found
    """
    # Prepare update data (only non-None fields)
    update_data = {}
    for field, value in profile_data.dict(exclude_unset=True).items():
        if value is not None:
            update_data[field] = value

    if update_data:
        update_data['updated_at'] = datetime.utcnow()
        success = await user_repo.update_user(current_user.id, update_data)

        if not success:
            raise HTTPException(status_code=404, detail='User not found')

    # Return updated profile
    updated_user = await user_repo.find_by_id(current_user.id)
    if not updated_user:
        raise HTTPException(status_code=404, detail='User not found')

    return create_user_response(User(**updated_user))


# ===========================================
# Change City
# ===========================================

@router.post(
    "/change-city",
    summary="Change user city"
)
async def change_city(
    city_request: Dict[str, str],
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Change user city

    Source: backend/server.py lines 2988-2994

    **Requires authorization:** Bearer token in Authorization header

    **Body parameters:**
    - city: New city name

    **Returns:**
    - message: Success message
    - city: New city value

    **Errors:**
    - 400: City not provided
    - 401: Invalid or missing token
    """
    city = city_request.get('city')
    if not city:
        raise HTTPException(status_code=400, detail='city required')

    await user_repo.update_user(
        current_user.id,
        {'city': city, 'updated_at': datetime.utcnow()}
    )

    return {
        'message': f'Город изменен на {city}',
        'city': city
    }


# ===========================================
# User Consultations
# ===========================================

@router.get(
    "/consultations",
    summary="Get user consultations"
)
async def get_user_consultations(
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get consultations assigned to current user

    Source: backend/server.py lines 2404-2424

    **Requires authorization:** Bearer token in Authorization header

    **Returns:**
    - List of consultations with purchase status

    **Errors:**
    - 401: Invalid or missing token
    """
    user_id = current_user.id
    db = await get_database()

    # Get consultations assigned to user
    consultations = await db.personal_consultations.find({
        'assigned_user_id': user_id,
        'is_active': True
    }).to_list(100)

    # Get user purchases
    purchases = await db.consultation_purchases.find({
        'user_id': user_id
    }).to_list(100)
    purchased_consultation_ids = {
        purchase['consultation_id'] for purchase in purchases
    }

    # Prepare response
    result = []
    for consultation in consultations:
        consultation_dict = dict(consultation)
        consultation_dict.pop('_id', None)
        consultation_dict['is_purchased'] = (
            consultation['id'] in purchased_consultation_ids
        )
        result.append(consultation_dict)

    return result


__all__ = ['router']
