"""Atomic balance debit with an outbox committed in the same user document."""
import logging
import uuid
from datetime import datetime
from fastapi import HTTPException
from services.credit_history import flush_pending_credit_transactions

logger = logging.getLogger(__name__)

async def flush_pending_calculations(db, user_id):
    """Deliver committed results by unique ID, retaining any unacknowledged entry."""
    user = await db.users.find_one({'id': user_id}, {'_id': 0, 'pending_calculations': 1})
    for calculation in (user or {}).get('pending_calculations', []):
        await db.numerology_calculations.update_one(
            {'_id': calculation['id']}, {'$setOnInsert': calculation}, upsert=True)
        await db.users.update_one({'id': user_id}, {
            '$pull': {'pending_calculations': {'id': calculation['id']}}})


async def debit_credits(db, user_id, cost, description, category, details=None, *, calculation=None):
    if type(cost) is not int or cost < 0:
        raise HTTPException(503, 'Стоимость операции временно недоступна')
    if cost == 0 and calculation is None:
        return
    if calculation is not None and (not isinstance(calculation, dict) or
            not isinstance(calculation.get('id'), str) or not calculation['id'] or
            calculation.get('user_id') != user_id):
        raise ValueError('The prepared calculation must belong to the debited user')
    transaction = {
        'id': str(uuid.uuid4()), 'user_id': user_id,
        'transaction_type': 'debit', 'amount': -cost,
        'description': description, 'category': category,
        'details': details or {}, 'created_at': datetime.utcnow(),
    }
    pending = {}
    if cost:
        pending['pending_credit_transactions'] = transaction
    if calculation is not None:
        pending['pending_calculations'] = calculation
    result = await db.users.update_one(
        {'id': user_id, 'is_disabled': {'$ne': True}, 'credits_remaining': {'$gte': cost}},
        {'$inc': {'credits_remaining': -cost}, '$push': pending},
    )
    if not result.matched_count:
        raise HTTPException(402, 'Недостаточно баллов для операции. Пополните баланс.')
    try:
        await flush_pending_credit_transactions(db, user_id)
    except Exception:
        # A history outage must not turn a committed debit into a retry/double charge.
        logger.warning('Credit history delivery deferred; committed debit remains in outbox')
    if calculation is not None:
        try:
            await flush_pending_calculations(db, user_id)
        except Exception:
            logger.warning('Calculation delivery deferred; prepared result remains in outbox')
