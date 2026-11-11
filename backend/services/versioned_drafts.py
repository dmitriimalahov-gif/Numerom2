"""Optimistic draft storage shared by exercises, quiz work, and diary notes."""
from datetime import datetime
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError


def public(row=None):
    row=row or {}
    return {key:row.get(key,default) for key,default in
            [('revision',0),('text',None),('request_id',None),('updated_at',None)]}


async def write_versioned(collection,identity,request,metadata):
    request_id = str(request.request_id)
    old = await collection.find_one({'_id': identity})
    if old and old.get('request_id') == request_id:
        if old['revision'] != request.revision + 1 or old['text'] != request.text:
            raise HTTPException(409, 'Этот запрос уже использован для другого черновика')
        return public(old)
    if (old or {}).get('revision', 0) != request.revision:
        raise HTTPException(409, 'Черновик изменён на другом устройстве. Ваш текст остаётся в поле.')
    row = {**metadata,
           'revision': request.revision + 1, 'text': request.text,
           'request_id': request_id, 'updated_at': datetime.utcnow()}
    try:
        changed = await collection.update_one(
            {'_id': identity, 'revision': request.revision} if old else {'_id': identity, 'revision': {'$exists': False}},
            {'$set': row}, upsert=not old)
        success = changed.matched_count or changed.upserted_id is not None
    except DuplicateKeyError:
        success = False
    if success:
        return public(row)
    latest = await collection.find_one({'_id': identity})
    if latest and latest.get('request_id') == request_id and latest['text'] == request.text and latest['revision'] == request.revision + 1:
        return public(latest)
    raise HTTPException(409, 'Черновик изменён на другом устройстве. Ваш текст остаётся в поле.')
