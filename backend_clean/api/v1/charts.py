"""
Charts API Router

API endpoints for charts and visualizations

Source:
- backend/server.py lines 783-795 (planetary energy charts)

Date created: 2025-10-14
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List

from models.user import User
from api.v1.dependencies import get_current_user, get_user_repository
from database.repositories.user_repository import UserRepository

# Import calculation functions from old backend
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

try:
    from vedic_numerology import generate_weekly_planetary_energy
    print("✅ Successfully imported charts calculation modules")
except ImportError as e:
    print(f"⚠️  Warning: Could not import charts modules: {e}")
    generate_weekly_planetary_energy = None


router = APIRouter(prefix="/charts", tags=["Charts"])


@router.get(
    "/planetary-energy/{days}",
    summary="Get planetary energy chart data"
)
async def get_planetary_energy(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
) -> Dict[str, Any]:
    """
    Get planetary energy chart data for specified number of days

    Source: backend/server.py lines 783-795

    **Requires:** Authentication

    **Path parameters:**
    - days: Number of days to generate chart data for (default: 7)

    **Returns:**
    - chart_data: List of daily planetary energy values
    - period: Period description
    - user_birth_date: User's birth date

    **Errors:**
    - 404: User not found
    - 500: Calculation module not available
    """
    if generate_weekly_planetary_energy is None:
        raise HTTPException(
            status_code=500,
            detail='Chart generation module not available'
        )

    # Get user birth date
    user_dict = await user_repo.find_by_id(current_user.id)
    if not user_dict:
        raise HTTPException(status_code=404, detail='User not found')

    birth_date = user_dict.get('birth_date')
    if not birth_date:
        raise HTTPException(
            status_code=400,
            detail='Birth date not set in user profile'
        )

    # Generate chart data
    if days <= 7:
        chart_data = generate_weekly_planetary_energy(birth_date)
    else:
        # Generate multiple weeks if needed
        chart_data = generate_weekly_planetary_energy(birth_date)
        for _ in range(1, (days // 7) + 1):
            chart_data.extend(generate_weekly_planetary_energy(birth_date))

    return {
        'chart_data': chart_data[:days],
        'period': f'{days} days',
        'user_birth_date': birth_date
    }


__all__ = ['router']
