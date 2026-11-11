"""Prepare personal-number results before committing their price and durable record."""
from datetime import datetime
from fastapi import HTTPException
from domain.personal_report import build_personal_report, full_name_number_for_report
from models import NumerologyCalculation
from numerology import calculate_personal_numbers, reduce_to_single_digit
from services.credit_debit import debit_credits


async def personal_numbers_result(db, user_id, birth_date, cost):
    user = await db.users.find_one({'id': user_id})
    if not user or user.get('is_disabled'):
        raise HTTPException(401, 'Требуется вход в действующий аккаунт')
    birth_date = birth_date or user.get('birth_date')
    try:
        date_value = datetime.strptime(birth_date, '%d.%m.%Y')
        if date_value.strftime('%d.%m.%Y') != birth_date or date_value > datetime.utcnow():
            raise ValueError('Invalid birth date')
        results = calculate_personal_numbers(birth_date)
    except (ValueError, TypeError):
        raise HTTPException(422, 'Укажите корректную дату рождения в формате ДД.ММ.ГГГГ')
    full_name_number = full_name_number_for_report(user.get('name'), user.get('surname'))
    if user.get('full_name_number') != full_name_number:
        # This optional profile cache must not introduce a failure after payment.
        await db.users.update_one({'id': user_id}, {'$set': {'full_name_number': full_name_number}})
    results['full_name_number'] = full_name_number
    results['wisdom_number'] = (reduce_to_single_digit(results['destiny_number'] + full_name_number)
                                if full_name_number is not None else None)
    results['report'] = build_personal_report(birth_date, results,
        name=user.get('name'), surname=user.get('surname'), profile_birth_date=user.get('birth_date'))
    calculation = NumerologyCalculation(user_id=user_id, birth_date=birth_date,
        calculation_type='personal_numbers', results=results).model_dump()
    await debit_credits(db, user_id, cost, 'Расчёт персональных чисел', 'numerology',
        {'calculation_type': 'personal_numbers', 'birth_date': birth_date}, calculation=calculation)
    # Delivery failures after the atomic commit are handled inside debit_credits.
    return results
