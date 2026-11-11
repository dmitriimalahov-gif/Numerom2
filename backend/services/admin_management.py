"""Admin account policy and atomic, auditable account changes."""
import re
import uuid
import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from pymongo import ReturnDocument
from services.credit_history import admin_credit_transaction, flush_pending_credit_transactions


logger = logging.getLogger(__name__)
HISTORY_LIMIT = 100
MAX_CREDITS = 1_000_000
USER_FIELDS = ('id', 'email', 'full_name', 'name', 'is_admin', 'is_super_admin',
               'is_disabled', 'credits_remaining', 'level', 'created_at')
USER_PROJECTION = {'_id': 0, **{field: 1 for field in USER_FIELDS}}
HISTORY_VALUE_FIELDS = ('is_admin', 'is_disabled', 'credits_remaining', 'level')


def safe_user(user):
    result = {field: user.get(field) for field in USER_FIELDS}
    for field in ('is_admin', 'is_super_admin', 'is_disabled'):
        result[field] = bool(user.get(field, False))
    result['credits_remaining'] = user.get('credits_remaining', 0)
    result['level'] = user.get('level', 1)
    return result


def safe_history(entries):
    result = []
    for entry in entries[-HISTORY_LIMIT:]:
        if not isinstance(entry, dict):
            continue
        item = {field: entry.get(field) for field in (
            'id', 'action', 'actor_id', 'reason', 'created_at',
        )}
        for state in ('before', 'after'):
            values = entry.get(state)
            item[state] = {key: values[key] for key in HISTORY_VALUE_FIELDS if key in values} \
                if isinstance(values, dict) else {}
        result.append(item)
    return result


def snapshot_filter(document, fields):
    """Match absent fields explicitly so legacy records can still be updated."""
    return {field: document[field] if field in document else {'$exists': False}
            for field in fields}


def audit_entry(actor, action, before, after, reason):
    return {'id': str(uuid.uuid4()), 'actor_id': actor['id'], 'action': action,
            'before': dict(before), 'after': dict(after), 'reason': reason,
            'created_at': datetime.now(timezone.utc)}


class AdminManagementService:
    def __init__(self, db):
        self.db = db
        self.users = db.users

    async def authorize(self, user_id):
        if not user_id:
            raise HTTPException(status_code=401, detail='Authentication required')
        actor = await self.users.find_one({'id': user_id}, {
            '_id': 0, 'id': 1, 'is_admin': 1, 'is_super_admin': 1, 'is_disabled': 1,
        })
        if not actor or actor.get('is_disabled') or not (
                actor.get('is_admin') or actor.get('is_super_admin')):
            raise HTTPException(status_code=403, detail='Administrator access required')
        return actor

    async def overview(self):
        return {
            'users_total': await self.users.count_documents({}),
            'users_disabled': await self.users.count_documents({'is_disabled': True}),
            'admins_total': await self.users.count_documents({
                '$or': [{'is_admin': True}, {'is_super_admin': True}],
            }),
            'lessons_total': await self.db.lessons_v2.count_documents({}),
            'consultations_total': await self.db.personal_consultations.count_documents({}),
        }

    async def list_users(self, q, page, page_size):
        term = q.strip()
        query = {'$or': [
            {field: {'$regex': re.escape(term), '$options': 'i'}}
            for field in ('email', 'full_name', 'name', 'id')
        ]} if term else {}
        total = await self.users.count_documents(query)
        rows = await self.users.find(query, USER_PROJECTION).sort([
            ('created_at', -1), ('id', 1),
        ]).skip((page - 1) * page_size).limit(page_size).to_list(length=page_size)
        return {'users': [safe_user(row) for row in rows], 'total': total,
                'page': page, 'page_size': page_size}

    async def user_detail(self, user_id):
        user = await self.users.find_one({'id': user_id}, {
            **USER_PROJECTION, 'admin_history': {'$slice': -HISTORY_LIMIT},
        })
        if not user:
            raise HTTPException(status_code=404, detail='User not found')
        return {'user': safe_user(user), 'admin_history': safe_history(user.get('admin_history') or [])}

    async def _target(self, user_id):
        user = await self.users.find_one({'id': user_id}, {**USER_PROJECTION, 'auth_version': 1})
        if not user:
            raise HTTPException(status_code=404, detail='User not found')
        return user

    @staticmethod
    def _check_target(actor, target, access=False):
        if access and (actor['id'] == target['id'] or target.get('is_super_admin')):
            raise HTTPException(status_code=403, detail='This account access is protected')
        if not actor.get('is_super_admin') and (
                target.get('is_super_admin') or
                (target.get('is_admin') and target['id'] != actor['id'])):
            raise HTTPException(status_code=403, detail='A super administrator is required for this account')

    async def _mutate(self, query, update, event):
        # Mongo applies the matched document's change and audit entry as one write.
        update.setdefault('$push', {})['admin_history'] = {'$each': [event], '$slice': -HISTORY_LIMIT}
        update.setdefault('$set', {})['updated_at'] = event['created_at']
        user = await self.users.find_one_and_update(
            query, update, projection=USER_PROJECTION, return_document=ReturnDocument.AFTER,
        )
        if user is None:
            raise HTTPException(status_code=409, detail='Account changed; reload it before trying again')
        if event['action'] == 'credits':
            try:
                await flush_pending_credit_transactions(self.db, user['id'])
            except Exception:
                logger.warning('Credit history delivery deferred; committed entry retained for retry')
        return {'user': safe_user(user)}

    async def change_access(self, actor, user_id, data):
        target = await self._target(user_id)
        self._check_target(actor, target, access=True)
        requested = data.model_dump(exclude_unset=True, exclude={'reason'})
        if 'is_admin' in requested and not actor.get('is_super_admin'):
            raise HTTPException(status_code=403, detail='Only a super administrator can change roles')
        changes = {key: value for key, value in requested.items()
                   if value != bool(target.get(key, False))}
        if not changes:
            raise HTTPException(status_code=400, detail='No access changes provided')
        event = audit_entry(actor, 'access',
                            {key: bool(target.get(key, False)) for key in changes},
                            changes, data.reason)
        query = {'id': user_id, **snapshot_filter(target, (
            'is_admin', 'is_super_admin', 'is_disabled', 'auth_version',
        ))}
        return await self._mutate(query, {'$set': changes, '$inc': {'auth_version': 1}}, event)

    async def change_credits(self, actor, user_id, data):
        target = await self._target(user_id)
        self._check_target(actor, target)
        balance = target.get('credits_remaining', 0)
        if balance != data.expected_balance:
            raise HTTPException(status_code=409, detail='Balance changed; reload it before trying again')
        new_balance = balance + data.amount
        if not 0 <= new_balance <= MAX_CREDITS:
            raise HTTPException(status_code=400, detail=f'Balance must be between 0 and {MAX_CREDITS}')
        event = audit_entry(actor, 'credits', {'credits_remaining': balance},
                            {'credits_remaining': new_balance}, data.reason)
        query = {'id': user_id, **snapshot_filter(target, (
            'credits_remaining', 'is_admin', 'is_super_admin', 'is_disabled', 'auth_version',
        ))}
        return await self._mutate(query, {
            '$inc': {'credits_remaining': data.amount},
            '$push': {'pending_credit_transactions': {'$each': [admin_credit_transaction(user_id, event)]}},
        }, event)
