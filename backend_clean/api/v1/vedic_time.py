"""
Vedic Time API Router

API endpoints for Vedic time calculations and planetary routes

Source:
- backend/server.py lines 577-774 (vedic time endpoints)

Date created: 2025-10-14
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from datetime import datetime

from models.user import User
from models.credit import CREDIT_COSTS
from api.v1.dependencies import (
    get_current_user,
    get_user_repository,
    get_credit_service
)
from database.repositories.user_repository import UserRepository
from services.credit_service import CreditService

# Import calculation functions from old backend
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

try:
    from vedic_time_calculations import (
        get_vedic_day_schedule,
        get_monthly_planetary_route,
        get_quarterly_planetary_route
    )
    print("✅ Successfully imported vedic time calculation modules")
except ImportError as e:
    print(f"⚠️  Warning: Could not import vedic time modules: {e}")
    get_vedic_day_schedule = None
    get_monthly_planetary_route = None
    get_quarterly_planetary_route = None


router = APIRouter(prefix="/vedic-time", tags=["Vedic Time"])


@router.get(
    "/daily-schedule",
    summary="Get Vedic daily schedule"
)
async def vedic_daily_schedule(
    city: Optional[str] = Query(None, description="City name"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
    credit_service: CreditService = Depends(get_credit_service)
) -> Dict[str, Any]:
    """
    Get Vedic daily schedule - costs 1 credit

    Source: backend/server.py lines 577-616

    **Requires:** Authentication

    **Query parameters:**
    - city: City name (optional, uses user profile if not provided)
    - date: Date in YYYY-MM-DD format (optional, uses today if not provided)

    **Returns:**
    - Vedic daily schedule with auspicious/inauspicious periods

    **Errors:**
    - 404: User not found
    - 422: City not specified
    - 402: Insufficient credits
    - 500: Calculation module not available
    """
    if get_vedic_day_schedule is None:
        raise HTTPException(
            status_code=500,
            detail='Vedic time calculation module not available'
        )

    user_id = current_user.id

    # Get city from request or user profile
    if not city:
        user_dict = await user_repo.find_by_id(user_id)
        if user_dict:
            city = user_dict.get('city')

    if not city:
        raise HTTPException(
            status_code=422,
            detail="Город не указан. Укажите город в запросе или обновите профиль пользователя."
        )

    # Parse date
    if date:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    else:
        date_obj = datetime.now()

    # Deduct credits
    try:
        await credit_service.deduct_credits(
            user_id=user_id,
            cost=CREDIT_COSTS['vedic_daily'],
            description='Ведическое время на день',
            category='vedic',
            details={
                'calculation_type': 'vedic_daily',
                'city': city,
                'date': date or date_obj.strftime("%Y-%m-%d")
            }
        )
    except HTTPException:
        raise

    # Calculate schedule
    schedule = get_vedic_day_schedule(city=city, date=date_obj)

    if 'error' in schedule:
        # Refund credits on error
        await credit_service.add_credits(
            user_id=user_id,
            amount=CREDIT_COSTS['vedic_daily'],
            description='Возврат за ошибку ведического времени',
            category='refund'
        )
        raise HTTPException(status_code=400, detail=schedule['error'])

    return schedule


@router.get(
    "/planetary-route",
    summary="Get daily planetary route"
)
async def planetary_route_daily(
    city: Optional[str] = Query(None, description="City name"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
    credit_service: CreditService = Depends(get_credit_service)
) -> Dict[str, Any]:
    """
    Get daily planetary route - costs 1 credit

    Source: backend/server.py lines 618-675

    **Requires:** Authentication

    **Query parameters:**
    - city: City name (optional, uses user profile if not provided)
    - date: Date in YYYY-MM-DD format (optional, uses today if not provided)

    **Returns:**
    - Daily planetary route with hourly breakdown

    **Errors:**
    - 404: User not found
    - 422: City or birth date not specified
    - 402: Insufficient credits
    - 500: Calculation module not available
    """
    if get_vedic_day_schedule is None:
        raise HTTPException(
            status_code=500,
            detail='Vedic time calculation module not available'
        )

    user_id = current_user.id

    # Get user data
    user_dict = await user_repo.find_by_id(user_id)
    if not user_dict:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    # Get city
    if not city:
        city = user_dict.get('city')

    if not city:
        raise HTTPException(
            status_code=422,
            detail="Город не указан. Укажите город в запросе или обновите профиль пользователя."
        )

    # Get birth date
    birth_date = user_dict.get('birth_date')
    if not birth_date:
        raise HTTPException(
            status_code=422,
            detail="Дата рождения не указана в профиле"
        )

    # Parse date
    if date:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    else:
        date_obj = datetime.now()

    # Deduct credits
    await credit_service.deduct_credits(
        user_id=user_id,
        cost=CREDIT_COSTS.get('planetary_daily', 1),
        description='Планетарный маршрут на день',
        category='vedic',
        details={
            'calculation_type': 'planetary_daily',
            'city': city,
            'date': date or date_obj.strftime("%Y-%m-%d")
        }
    )

    # Calculate schedule
    schedule = get_vedic_day_schedule(city=city, date=date_obj, birth_date=birth_date)

    if 'error' in schedule:
        # Refund credits on error
        await credit_service.add_credits(
            user_id=user_id,
            amount=CREDIT_COSTS.get('planetary_daily', 1),
            description='Возврат за ошибку планетарного маршрута',
            category='refund'
        )
        raise HTTPException(status_code=400, detail=schedule['error'])

    # Build route from schedule (Source: backend/server.py lines 658-675)
    rec = schedule.get('recommendations', {})
    route = {
        'date': date_obj.strftime('%Y-%m-%d'),
        'city': city,
        'personal_birth_date': birth_date,
        'daily_ruling_planet': schedule.get('weekday', {}).get('ruling_planet', ''),
        'best_activity_hours': rec.get('best_hours', []),
        'avoid_periods': {
            'rahu_kaal': schedule.get('inauspicious_periods', {}).get('rahu_kaal', {}),
            'gulika_kaal': schedule.get('inauspicious_periods', {}).get('gulika_kaal', {}),
            'yamaghanta': schedule.get('inauspicious_periods', {}).get('yamaghanta', {})
        },
        'favorable_period': schedule.get('auspicious_periods', {}).get('abhijit_muhurta', {}),
        'hourly_guide': schedule.get('planetary_hours', [])[:8],
        'daily_recommendations': rec
    }

    return route


@router.get(
    "/planetary-route/monthly",
    summary="Get monthly planetary route"
)
async def planetary_route_monthly_endpoint(
    city: Optional[str] = Query(None, description="City name"),
    month: Optional[int] = Query(None, description="Month (1-12)"),
    year: Optional[int] = Query(None, description="Year"),
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
    credit_service: CreditService = Depends(get_credit_service)
) -> Dict[str, Any]:
    """
    Get monthly planetary route - costs 5 credits

    Source: backend/server.py lines 677-716

    **Requires:** Authentication

    **Query parameters:**
    - city: City name (optional, uses user profile if not provided)
    - month: Month (1-12, optional, uses current month if not provided)
    - year: Year (optional, uses current year if not provided)

    **Returns:**
    - Monthly planetary route calendar

    **Errors:**
    - 404: User not found
    - 422: City or birth date not specified
    - 402: Insufficient credits
    - 500: Calculation module not available
    """
    if get_planetary_route_monthly is None:
        raise HTTPException(
            status_code=500,
            detail='Planetary route calculation module not available'
        )

    user_id = current_user.id

    # Get user data
    user_dict = await user_repo.find_by_id(user_id)
    if not user_dict:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    # Get city
    if not city:
        city = user_dict.get('city')

    if not city:
        raise HTTPException(
            status_code=422,
            detail="Город не указан"
        )

    # Get birth date
    birth_date = user_dict.get('birth_date')
    if not birth_date:
        raise HTTPException(
            status_code=422,
            detail="Дата рождения не указана в профиле"
        )

    # Default to current month/year
    if not month:
        month = datetime.now().month
    if not year:
        year = datetime.now().year

    # Create start_date from month and year
    start_date = datetime(year=year, month=month, day=1)

    # Deduct credits
    await credit_service.deduct_credits(
        user_id=user_id,
        cost=CREDIT_COSTS.get('planetary_monthly', 5),
        description='Планетарный маршрут на месяц',
        category='vedic',
        details={
            'calculation_type': 'planetary_monthly',
            'city': city,
            'month': month,
            'year': year
        }
    )

    # Calculate route
    try:
        route = get_monthly_planetary_route(
            city=city,
            start_date=start_date,
            birth_date=birth_date
        )
        return route
    except Exception as e:
        # Refund credits on error
        await credit_service.add_credits(
            user_id=user_id,
            amount=CREDIT_COSTS.get('planetary_monthly', 5),
            description='Возврат за ошибку месячного планетарного маршрута',
            category='refund'
        )
        raise HTTPException(status_code=400, detail=f'Ошибка расчета месячного маршрута: {str(e)}')


@router.get(
    "/planetary-route/quarterly",
    summary="Get quarterly planetary route"
)
async def planetary_route_quarterly_endpoint(
    city: Optional[str] = Query(None, description="City name"),
    quarter: Optional[int] = Query(None, description="Quarter (1-4)"),
    year: Optional[int] = Query(None, description="Year"),
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
    credit_service: CreditService = Depends(get_credit_service)
) -> Dict[str, Any]:
    """
    Get quarterly planetary route - costs 15 credits

    Source: backend/server.py lines 718-774

    **Requires:** Authentication

    **Query parameters:**
    - city: City name (optional, uses user profile if not provided)
    - quarter: Quarter 1-4 (optional, uses current quarter if not provided)
    - year: Year (optional, uses current year if not provided)

    **Returns:**
    - Quarterly planetary route calendar

    **Errors:**
    - 404: User not found
    - 422: City or birth date not specified
    - 402: Insufficient credits
    - 500: Calculation module not available
    """
    if get_planetary_route_quarterly is None:
        raise HTTPException(
            status_code=500,
            detail='Planetary route calculation module not available'
        )

    user_id = current_user.id

    # Get user data
    user_dict = await user_repo.find_by_id(user_id)
    if not user_dict:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    # Get city
    if not city:
        city = user_dict.get('city')

    if not city:
        raise HTTPException(
            status_code=422,
            detail="Город не указан"
        )

    # Get birth date
    birth_date = user_dict.get('birth_date')
    if not birth_date:
        raise HTTPException(
            status_code=422,
            detail="Дата рождения не указана в профиле"
        )

    # Default to current quarter/year
    if not quarter:
        quarter = (datetime.now().month - 1) // 3 + 1
    if not year:
        year = datetime.now().year

    # Create start_date from quarter and year
    # Quarter 1 = Jan-Mar, Quarter 2 = Apr-Jun, Quarter 3 = Jul-Sep, Quarter 4 = Oct-Dec
    start_month = (quarter - 1) * 3 + 1
    start_date = datetime(year=year, month=start_month, day=1)

    # Deduct credits
    await credit_service.deduct_credits(
        user_id=user_id,
        cost=CREDIT_COSTS.get('planetary_quarterly', 10),
        description='Планетарный маршрут на квартал',
        category='vedic',
        details={
            'calculation_type': 'planetary_quarterly',
            'city': city,
            'quarter': quarter,
            'year': year
        }
    )

    # Calculate route
    try:
        route = get_quarterly_planetary_route(
            city=city,
            start_date=start_date,
            birth_date=birth_date
        )
        return route
    except Exception as e:
        # Refund credits on error
        await credit_service.add_credits(
            user_id=user_id,
            amount=CREDIT_COSTS.get('planetary_quarterly', 10),
            description='Возврат за ошибку квартального планетарного маршрута',
            category='refund'
        )
        raise HTTPException(status_code=400, detail=f'Ошибка расчета квартального маршрута: {str(e)}')


__all__ = ['router']
