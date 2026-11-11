"""Deliver committed admin credit entries to the existing user-visible history."""


def admin_credit_transaction(user_id, event):
    before = event['before']['credits_remaining']
    after = event['after']['credits_remaining']
    amount = after - before
    return {
        'id': event['id'], 'user_id': user_id,
        'transaction_type': 'credit' if amount > 0 else 'debit',
        'amount': amount, 'category': 'admin',
        'description': 'Корректировка баланса администратором',
        'details': {'added_by_admin': True, 'old_credits': before, 'new_credits': after},
        'created_at': event['created_at'],
    }


async def flush_pending_credit_transactions(db, user_id):
    user = await db.users.find_one({'id': user_id}, {'_id': 0, 'pending_credit_transactions': 1})
    for transaction in (user or {}).get('pending_credit_transactions', []):
        # Mongo's unique _id makes retries and simultaneous readers idempotent.
        await db.credit_transactions.update_one(
            {'_id': transaction['id']}, {'$setOnInsert': transaction}, upsert=True,
        )
        # A failed delivery or cleanup leaves the committed entry available to retry.
        await db.users.update_one(
            {'id': user_id}, {'$pull': {'pending_credit_transactions': {'id': transaction['id']}}},
        )
