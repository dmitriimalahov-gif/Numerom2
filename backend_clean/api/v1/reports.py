"""
Reports API Router

API endpoints for generating numerology reports

Source:
- backend/server.py lines 2696-2837 (reports endpoints)

Date created: 2025-10-14
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from typing import Dict, Any
from datetime import datetime

from models.user import User
from models.reports import HTMLReportRequest, PDFReportRequest
from api.v1.dependencies import get_current_user
from database.connection import get_database

# Import report generators from old backend
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

try:
    from html_generator import create_numerology_report_html
    from pdf_generator import create_numerology_report_pdf
    from numerology import calculate_personal_numbers, create_pythagorean_square, parse_birth_date
    from vedic_numerology import generate_weekly_planetary_energy
    from vedic_time_calculations import get_vedic_day_schedule
    print("✅ Successfully imported report generation modules")
except ImportError as e:
    print(f"⚠️  Warning: Could not import report modules: {e}")
    create_numerology_report_html = None
    create_numerology_report_pdf = None
    calculate_personal_numbers = None
    create_pythagorean_square = None
    parse_birth_date = None
    generate_weekly_planetary_energy = None
    get_vedic_day_schedule = None


router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "/available-calculations",
    summary="Get available calculations for report"
)
async def get_available_calculations(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get list of all calculations user can include in a report

    Source: backend/server.py lines 2696-2774

    **Requires:** Authentication

    **Returns:**
    - Dictionary of available calculation types with their status

    **Errors:**
    - 404: User not found
    """
    db = await get_database()

    # Get user's calculation history
    calculations = await db.numerology_calculations.find({
        'user_id': current_user.id
    }).to_list(100)

    available_calculations = {
        'personal_numbers': {
            'id': 'personal_numbers',
            'name': 'Персональные числа',
            'description': 'Числа судьбы, души, ума, правления и другие',
            'available': True,  # Always available for user
            'icon': '🌟'
        },
        'name_numerology': {
            'id': 'name_numerology',
            'name': 'Нумерология имени и фамилии',
            'description': 'Анализ имени и фамилии пользователя',
            'available': bool(current_user.full_name),
            'icon': '📝'
        },
        'car_numerology': {
            'id': 'car_numerology',
            'name': 'Нумерология автомобильного номера',
            'description': 'Анализ номера автомобиля',
            'available': bool(current_user.car_number),
            'icon': '🚗'
        },
        'address_numerology': {
            'id': 'address_numerology',
            'name': 'Нумерология адреса',
            'description': 'Анализ адреса проживания',
            'available': bool(
                current_user.street or
                current_user.house_number or
                current_user.apartment_number
            ),
            'icon': '🏠'
        },
        'pythagorean_square': {
            'id': 'pythagorean_square',
            'name': 'Квадрат Пифагора',
            'description': 'Психоматрица по дате рождения',
            'available': True,
            'icon': '⬜'
        },
        'compatibility': {
            'id': 'compatibility',
            'name': 'Совместимость',
            'description': 'Анализ совместимости с партнёром',
            'available': any(
                calc.get('calculation_type') == 'compatibility'
                for calc in calculations
            ),
            'icon': '💑'
        },
        'vedic_numerology': {
            'id': 'vedic_numerology',
            'name': 'Ведическая нумерология',
            'description': 'Джанма анк, Бхагья анк, Атма анк и другие',
            'available': True,
            'icon': '🕉️'
        },
        'enhanced_pythagorean': {
            'id': 'enhanced_pythagorean',
            'name': 'Расширенный квадрат Пифагора',
            'description': 'Детальный анализ психоматрицы',
            'available': True,
            'icon': '🔢'
        }
    }

    return {
        'available_calculations': available_calculations,
        'user_has_data': {
            'full_name': bool(current_user.full_name),
            'car_number': bool(current_user.car_number),
            'address': bool(
                current_user.street or
                current_user.house_number
            ),
            'city': bool(current_user.city)
        }
    }


@router.post(
    "/html/numerology",
    summary="Generate HTML numerology report"
)
async def generate_numerology_html(
    html_request: HTMLReportRequest,
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    Generate HTML numerology report

    Source: backend/server.py lines 2794-2911

    **Requires:** Authentication, Premium or credits

    **Body:**
    - selected_calculations: List of calculation IDs to include
    - theme: "default", "dark", or "print"

    **Returns:**
    - HTML document

    **Errors:**
    - 402: Insufficient credits
    - 404: User not found
    - 500: Report generation error
    """
    if create_numerology_report_html is None:
        raise HTTPException(
            status_code=500,
            detail='Report generation module not available'
        )

    db = await get_database()

    # Check user and credits
    user_dict = await db.users.find_one({'id': current_user.id})
    if not user_dict:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    user = User(**user_dict)

    # Check subscription expiration
    if user.subscription_expires_at and user.subscription_expires_at < datetime.utcnow():
        await db.users.update_one(
            {'id': user.id},
            {'$set': {
                'is_premium': False,
                'subscription_type': None,
                'subscription_expires_at': None
            }}
        )
        user.is_premium = False
        user.subscription_type = None

    # Check credits
    if not user.is_premium and (user.credits_remaining is None or user.credits_remaining <= 0):
        raise HTTPException(
            status_code=402,
            detail='Недостаточно кредитов. Требуется подписка или дополнительные кредиты.'
        )

    # Prepare user data
    user_data = {
        'full_name': user.full_name,
        'email': user.email,
        'birth_date': user.birth_date,
        'city': user.city,
        'phone_number': user.phone_number,
        'car_number': user.car_number,
        'street': user.street,
        'house_number': user.house_number,
        'apartment_number': user.apartment_number,
        'postal_code': user.postal_code
    }

    # Calculate personal numbers
    calculations = calculate_personal_numbers(user.birth_date)

    # Pythagorean square
    pythagorean_data = None
    try:
        d, m, y = parse_birth_date(user.birth_date)
        pythagorean_data = create_pythagorean_square(d, m, y)
    except Exception:
        pass

    # Selected calculations
    selected_calculations = html_request.selected_calculations

    # For compatibility with old system
    if not selected_calculations:
        selected_calculations = []
        if html_request.include_vedic:
            selected_calculations.append('vedic_numerology')
        if html_request.include_charts:
            selected_calculations.extend(['personal_numbers', 'pythagorean_square'])
        if html_request.include_compatibility:
            selected_calculations.append('compatibility')

        # If nothing selected, add basic calculations
        if not selected_calculations:
            selected_calculations = ['personal_numbers', 'pythagorean_square']

    # Check at least one calculation is selected
    if not selected_calculations:
        raise HTTPException(
            status_code=400,
            detail='Необходимо выбрать хотя бы один раздел для отчёта'
        )

    # Vedic times
    vedic_data = None
    vedic_times = None
    if 'vedic_times' in selected_calculations and user.city:
        try:
            vedic_times = get_vedic_day_schedule(city=user.city, date=datetime.utcnow())
        except Exception:
            pass

    # Planetary route
    planetary_route = None
    if 'planetary_route' in selected_calculations and user.city:
        try:
            planetary_route = {
                'date': datetime.utcnow().strftime('%Y-%m-%d'),
                'city': user.city,
                'daily_route': [
                    'Солнце: Утро (6:00-12:00)',
                    'Луна: День (12:00-18:00)',
                    'Марс: Вечер (18:00-24:00)'
                ]
            }
        except Exception:
            pass

    # Planetary energies
    charts_data = None
    if any(calc in selected_calculations for calc in ['personal_numbers', 'pythagorean_square']):
        try:
            charts_data = {'planetary_energy': generate_weekly_planetary_energy(user.birth_date)}
        except Exception:
            pass

    # Combine all data
    all_data = {
        'personal_numbers': calculations,
        'pythagorean_square': pythagorean_data,
        'vedic_times': vedic_times,
        'planetary_route': planetary_route,
        'charts': charts_data
    }

    try:
        # Generate HTML report
        html_str = create_numerology_report_html(
            user_data=user_data,
            all_data=all_data,
            vedic_data=vedic_data,
            charts_data=charts_data,
            theme=html_request.theme,
            selected_calculations=selected_calculations
        )

        # Check HTML generated correctly
        if not html_str or len(html_str) < 100:
            raise HTTPException(
                status_code=500,
                detail='Ошибка генерации HTML: пустой результат'
            )

        # Deduct credit only after successful generation
        if not user.is_premium:
            await db.users.update_one(
                {'id': user.id},
                {'$inc': {'credits_remaining': -1}}
            )

        return Response(content=html_str, media_type='text/html; charset=utf-8')

    except Exception as e:
        import logging
        logging.error(f"HTML generation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f'Ошибка генерации HTML отчёта: {str(e)}'
        )


@router.post(
    "/pdf/numerology",
    summary="Generate PDF numerology report"
)
async def generate_numerology_pdf(
    pdf_request: PDFReportRequest,
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    Generate PDF numerology report

    Source: backend/server.py lines 2913-3020

    **Requires:** Authentication, Premium or credits

    **Body:**
    - selected_calculations: List of calculation IDs to include
    - include_vedic: Include vedic numerology
    - include_charts: Include charts

    **Returns:**
    - PDF document

    **Errors:**
    - 402: Insufficient credits
    - 404: User not found
    - 500: Report generation error
    """
    if create_numerology_report_pdf is None:
        raise HTTPException(
            status_code=500,
            detail='PDF generation module not available'
        )

    db = await get_database()

    # Get user
    user_dict = await db.users.find_one({'id': current_user.id})
    if not user_dict:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    user = User(**user_dict)

    # Check subscription
    if user.subscription_expires_at and user.subscription_expires_at < datetime.utcnow():
        await db.users.update_one(
            {'id': user.id},
            {'$set': {
                'is_premium': False,
                'subscription_type': None,
                'subscription_expires_at': None
            }}
        )
        user.is_premium = False

    # Check credits
    if not user.is_premium and (user.credits_remaining is None or user.credits_remaining <= 0):
        raise HTTPException(
            status_code=402,
            detail='Недостаточно кредитов для генерации PDF отчёта'
        )

    # Prepare user data
    user_data = {
        'full_name': user.full_name,
        'email': user.email,
        'birth_date': user.birth_date,
        'city': user.city
    }

    # Calculate data
    calculations = calculate_personal_numbers(user.birth_date)

    pythagorean_data = None
    try:
        d, m, y = parse_birth_date(user.birth_date)
        pythagorean_data = create_pythagorean_square(d, m, y)
    except Exception:
        pass

    # Vedic data
    vedic_data = None
    if pdf_request.include_vedic:
        try:
            from vedic_numerology import calculate_comprehensive_vedic_numerology
            vedic_data = calculate_comprehensive_vedic_numerology(
                user.birth_date,
                user.full_name or ''
            )
        except Exception:
            pass

    # Charts data
    charts_data = None
    if pdf_request.include_charts:
        try:
            charts_data = {
                'planetary_energy': generate_weekly_planetary_energy(user.birth_date)
            }
        except Exception:
            pass

    try:
        # Generate PDF
        pdf_bytes = create_numerology_report_pdf(
            user_data,
            calculations,
            vedic_data,
            charts_data
        )

        if not pdf_bytes:
            raise HTTPException(
                status_code=500,
                detail='Ошибка генерации PDF: пустой результат'
            )

        # Deduct credit
        if not user.is_premium:
            await db.users.update_one(
                {'id': user.id},
                {'$inc': {'credits_remaining': -1}}
            )

        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="numerology_report_{user.id}.pdf"'
            }
        )

    except Exception as e:
        import logging
        logging.error(f"PDF generation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f'Ошибка генерации PDF отчёта: {str(e)}'
        )


__all__ = ['router']
