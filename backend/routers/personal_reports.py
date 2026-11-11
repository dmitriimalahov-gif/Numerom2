"""Read the current user's latest durable personal result without spending credits."""
from copy import deepcopy
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
from domain.personal_report import build_personal_report
from domain.personal_scheme import build_personal_scheme


def _created_at(record):
    value = record.get('created_at')
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if not isinstance(value, datetime):
        raise ValueError('Saved personal calculation has no valid creation time')
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def present(record):
    result = deepcopy(record['results'])
    if not isinstance(result, dict):
        raise ValueError('Saved personal calculation has invalid results')
    # The durable paid receipt embeds the original report twice for replay.
    # History exposes the original report once, keeping 100 entries bounded.
    result.pop('personal_detail', None)
    if not isinstance(result.get('report'), dict):
        result['report'] = build_personal_report(record['birth_date'], result, legacy=True)
    elif result['report'].get('version') == 1 and 'scheme' not in result['report']:
        # Enrich only this response copy, using the report's own saved date.
        result['report']['scheme'] = build_personal_scheme(result['report'].get('birth_date'), legacy=True)
    return {'id':record['id'],'birth_date':record['birth_date'],'created_at':record['created_at'],'results':result}

def create_personal_reports_router(db):
    router = APIRouter(prefix='/api/numerology/personal-numbers', tags=['personal-reports'])

    @router.get('/latest')
    async def latest(current_user: dict = Depends(get_current_user)):
        user_id = current_user['user_id']
        user = await db.users.find_one({'id': user_id},
            {'_id': 0, 'id': 1, 'is_disabled': 1, 'pending_calculations': 1})
        if not user or user.get('is_disabled'):
            raise HTTPException(401, 'Требуется вход в действующий аккаунт')
        saved = await db.numerology_calculations.find_one(
            {'user_id': user_id, 'calculation_type': 'personal_numbers'},
            {'_id': 0, 'id': 1, 'birth_date': 1, 'created_at': 1, 'results': 1},
            sort=[('created_at', -1), ('id', -1)])
        # Payment commits the result in this user's outbox before archive delivery.
        # Reading must neither retry delivery nor modify balance/history/profile.
        candidates = [saved] if saved else []
        candidates.extend(record for record in user.get('pending_calculations', [])
                          if record.get('user_id') == user_id and record.get('calculation_type') == 'personal_numbers')
        if not candidates:
            return {'calculation': None}
        record = max(candidates, key=lambda item: (_created_at(item), item['id']))
        return {'calculation':present(record)}

    @router.get('/history')
    async def history(current_user:dict=Depends(get_current_user)):
        uid=current_user['user_id']
        user=await db.users.find_one({'id':uid})
        if not user or user.get('is_disabled'):raise HTTPException(401,'Требуется вход')
        pending=[r for r in user.get('pending_calculations',[]) if r.get('user_id')==uid and r.get('calculation_type')=='personal_numbers']
        rows=await db.numerology_calculations.find({'user_id':uid,'calculation_type':'personal_numbers'}).sort([('created_at',-1),('id',-1)]).limit(100).to_list(100)
        records={r['id']:r for r in rows+pending}
        records=sorted(records.values(),key=lambda r:(_created_at(r),r['id']),reverse=True)[:100]
        return {'calculations':[{**present(r),'request_id':r.get('request_id'),'cost':r.get('cost')} for r in records]}

    return router
