"""Versioned challenge journal, atomic user credits, retryable archive delivery."""
import hashlib
import json
import logging
from datetime import datetime
from uuid import UUID, uuid5, NAMESPACE_URL
import uuid
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from pymongo.errors import DuplicateKeyError
from services.student_learning import Identifier, require_student_lesson, _key, StudentLearningService
from services.credit_history import flush_pending_credit_transactions
from domain.narration import plain

log=logging.getLogger(__name__)


class DiaryWrite(BaseModel):
    model_config=ConfigDict(extra='forbid')
    request_id: UUID
    attempt_id: UUID
    revision: int=Field(strict=True,ge=0)
    day: int=Field(strict=True,ge=1,le=90)
    note: str=Field(max_length=4000)
    completed: StrictBool=False


class DiaryRestart(BaseModel):
    model_config=ConfigDict(extra='forbid')
    request_id: UUID
    attempt_id: UUID
    revision: int=Field(strict=True,ge=0)


class LegacyDiaryWrite(BaseModel):
    model_config=ConfigDict(extra='forbid')
    lesson_id: Identifier
    challenge_id: Identifier
    day: int=Field(strict=True,ge=1,le=90)
    note: str=Field(default='',max_length=4000)
    completed: StrictBool=False


def challenge_data(lesson,challenge_id):
    ch=lesson.get('challenge') or (lesson.get('content') or {}).get('challenge') or {}
    if ch.get('id')!=challenge_id:raise HTTPException(404,'Челлендж не найден')
    days=ch.get('daily_tasks');duration=ch.get('duration_days')
    if type(duration) is not int or not 1<=duration<=90 or not isinstance(days,list) or len(days)!=duration:
        raise HTTPException(409,'Преподаватель ещё готовит задания по дням')
    numbers=[d.get('day') for d in days if isinstance(d,dict)]
    if len(numbers)!=duration or any(type(n) is not int for n in numbers) or sorted(numbers)!=list(range(1,duration+1)):
        raise HTTPException(409,'Порядок дней пока не настроен')
    return ch


def public_progress(state):
    fields=('id','attempt_id','attempt_number','revision','last_request_id','current_day','completed_days','is_completed',
            'points_earned','total_points','points_per_day','bonus_points','started_at','last_updated','completed_at')
    result={key:state[key] for key in fields if key in state}
    result['daily_notes']=[{'day':int(day),'note':entry['note'],'updated_at':entry['updated_at']}
                           for day,entry in sorted(state.get('notes',{}).items(),key=lambda pair:int(pair[0]))]
    return result


def history_entry(row):
    allowed={'id','attempt_id','attempt_number','completed_days','daily_notes','points_earned','is_completed','started_at','last_updated','revision'}
    result={key:value for key,value in row.items() if key in allowed}
    notes=result.get('daily_notes') or []
    if isinstance(notes,dict):
        notes=[{'day':int(day),**(value if isinstance(value,dict) else {'note':str(value)})}
               for day,value in notes.items() if str(day).isdigit()]
    result['daily_notes']=sorted(
        ({'day':item['day'],'note':str(item.get('note','')),'updated_at':item.get('updated_at')}
         for item in notes if isinstance(item,dict) and type(item.get('day')) is int and 1<=item['day']<=90),
        key=lambda item:item['day'])
    return result


class ChallengeDiary:
    def __init__(self,db):self.db=db

    async def snapshot(self,uid,lesson_id,challenge_id):
        user,lesson=await require_student_lesson(self.db,uid,lesson_id)
        ch=challenge_data(lesson,challenge_id);key=_key(lesson_id,challenge_id)
        stored=user.get('challenge_journals',{}).get(key)
        if stored:return user,lesson,ch,key,stored,True
        config=await self.db.learning_points_config.find_one({'is_active':True}) or {}
        def points(field,default):
            value=ch.get(field)
            if value is None:value=config.get('challenge_'+field,default)
            if type(value) is not int or not 0<=value<=1000:raise HTTPException(503,'Настройки наград временно недоступны')
            return value
        legacy=await self.db.challenge_progress.find_one({'user_id':uid,'lesson_id':lesson_id,'challenge_id':challenge_id},sort=[('started_at',-1)]) or {}
        totals=await self.db.challenge_progress.aggregate([
            {'$match':{'user_id':uid,'lesson_id':lesson_id,'challenge_id':challenge_id}},
            {'$group':{'_id':None,'points':{'$sum':'$points_earned'}}}]).to_list(1)
        valid=set(range(1,ch['duration_days']+1))
        completed=sorted({d for d in legacy.get('completed_days',[]) if type(d) is int and d in valid})
        # A completed legacy attempt must never earn its original rewards again.
        if legacy.get('is_completed'):completed=sorted(valid)
        old_notes=legacy.get('daily_notes') or []
        if isinstance(old_notes,dict):old_notes=[{'day':int(d),'note':n} for d,n in old_notes.items() if str(d).isdigit()]
        notes={str(n['day']):{'note':str(n.get('note','')),'updated_at':n.get('updated_at') or legacy.get('last_updated') or legacy.get('started_at')}
               for n in old_notes if isinstance(n,dict) and n.get('day') in valid}
        attempt=str(uuid5(NAMESPACE_URL,f'numerom:{uid}:{key}:{legacy.get("id","first")}'))
        state={'id':legacy.get('id') or 'challenge-'+_key(uid,attempt),'archive_id':legacy.get('_id'),'attempt_id':attempt,'attempt_number':legacy.get('attempt_number',1),
               'revision':0,'notes':notes,'completed_days':completed,'is_completed':len(completed)==len(valid),
               'ever_completed':bool(legacy.get('is_completed')),'current_day':next((d for d in sorted(valid) if d not in completed),len(valid)),
               'points_earned':legacy.get('points_earned',0),'total_points':totals[0]['points'] if totals else 0,
               'points_per_day':points('points_per_day',10),'bonus_points':points('bonus_points',50),
               'started_at':legacy.get('started_at'),'last_updated':legacy.get('last_updated'),'requests':{}}
        return user,lesson,ch,key,state,False

    async def legacy_read(self,uid,lesson_id,challenge_id):
        result=await self.read(uid,lesson_id,challenge_id)
        return {**result['progress'],'total_attempts':result['progress']['attempt_number']}

    async def legacy_save(self,uid,data):
        state=(await self.snapshot(uid,data.lesson_id,data.challenge_id))[4]
        request=DiaryWrite(request_id=uuid.uuid4(),attempt_id=state['attempt_id'],revision=state['revision'],
                           day=data.day,note=data.note,completed=data.completed)
        return await self.save(uid,data.lesson_id,data.challenge_id,request)

    async def read(self,uid,lesson_id,challenge_id):
        user,lesson,ch,key,state,stored=await self.snapshot(uid,lesson_id,challenge_id)
        rows=await self.db.challenge_progress.find({'user_id':uid,'lesson_id':lesson_id,'challenge_id':challenge_id}).sort('started_at',-1).limit(30).to_list(30)
        pending=[e['record'] for e in user.get('pending_challenge_progress',[]) if e['record'].get('lesson_id')==lesson_id and e['record'].get('challenge_id')==challenge_id]
        history={row['id']:row for row in rows if row.get('id')}
        for row in pending:
            old=history.get(row['id'])
            if not old or old.get('revision',-1)<=row['revision']:history[row['id']]=row
        if stored:history[state['id']]=public_progress(state)
        # Only own note/date/award fields; never _id or request fingerprints.
        return {'challenge':{'id':ch['id'],'title':plain(ch.get('title')),'description':plain(ch.get('description')),
                'duration_days':ch['duration_days'],'days':[{'day':day['day'],'title':plain(day.get('title')),'description':plain(day.get('description')),
                    'tasks':[plain(t) for t in day.get('tasks',[]) if isinstance(t,str)],'narration_id':f'challenge-{index}'} for index,day in enumerate(ch['daily_tasks'])]},
                'progress':public_progress(state),
                'history':[history_entry(row) for row in history.values() if row['id']!=state['id']][:30]}

    async def deliver(self,uid):
        user=await self.db.users.find_one({'id':uid})
        for event in (user or {}).get('pending_challenge_progress',[]):
            record=event['record'];identity=event.get('archive_id') or record['id']
            try:
                await self.db.challenge_progress.update_one({'_id':identity,'$or':[{'revision':{'$lte':record['revision']}},{'revision':{'$exists':False}}]}, {'$set':record},upsert=True)
            except DuplicateKeyError:
                pass # A later revision already won delivery.
            await self.db.users.update_one({'id':uid},{'$pull':{'pending_challenge_progress':{'delivery_id':event['delivery_id']}}})
        await flush_pending_credit_transactions(self.db,uid)

    async def save(self,uid,lesson_id,challenge_id,data,*,restart=False):
        user,lesson,ch,key,old,stored=await self.snapshot(uid,lesson_id,challenge_id)
        body=data.model_dump(mode='json');request=str(data.request_id)
        fingerprint=hashlib.sha256(json.dumps([body,restart],sort_keys=True).encode()).hexdigest()
        marker=old.get('requests',{}).get(request)
        if marker:
            if marker!=fingerprint:raise HTTPException(409,'Эта отправка уже относится к другой записи')
            return await self.finish(uid,lesson_id,challenge_id)
        if str(data.attempt_id)!=old['attempt_id'] or data.revision!=old['revision']:
            raise HTTPException(409,'Дневник обновлён на другом экране. Обновите сохранённые записи; ваш текст остаётся в поле.')
        if len(user.get('pending_challenge_progress',[]))>=32:raise HTTPException(503,'Архив синхронизируется. Попробуйте сохранить позже.')
        state={**old,'notes':dict(old['notes']),'completed_days':list(old['completed_days']),'requests':dict(old.get('requests',{}))}
        now=datetime.utcnow();now=now.replace(microsecond=now.microsecond//1000*1000)
        award=0;description='Практика по дням'
        if restart:
            if not state['is_completed']:raise HTTPException(409,'Сначала завершите текущую практику')
            state.update(id='challenge-'+_key(uid,lesson_id,challenge_id,request),attempt_id=request,attempt_number=state['attempt_number']+1,
                         notes={},completed_days=[],is_completed=False,ever_completed=True,current_day=1,points_earned=0,
                         started_at=now,requests={})
            state.pop('completed_at',None)
            state.pop('archive_id',None)
        else:
            if data.day not in {day['day'] for day in ch['daily_tasks']}:raise HTTPException(422,'Такого дня нет в задании')
            if data.completed and not data.note.strip():raise HTTPException(422,'Добавьте наблюдение о выполненном задании')
            state['notes'][str(data.day)]={'note':data.note.strip(),'updated_at':now}
            if data.completed and data.day not in state['completed_days']:
                state['completed_days']=sorted(state['completed_days']+[data.day]);award=state['points_per_day']
            complete=len(state['completed_days'])==ch['duration_days']
            if complete and not state['is_completed']:award+=state['bonus_points'];state['completed_at']=now
            state['is_completed']=complete;state['ever_completed']=state.get('ever_completed',False) or complete
            state['current_day']=next((d for d in range(1,ch['duration_days']+1) if d not in state['completed_days']),ch['duration_days'])
            state['points_earned']+=award
            state['total_points']+=award
            description=f'Практика: день {data.day}' + (' и завершение челленджа' if complete and not old['is_completed'] else '')
        state['revision']=old['revision']+1;state['started_at']=state.get('started_at') or now;state['last_updated']=now
        state['requests'][request]=fingerprint;state['last_request_id']=request
        state['requests']=dict(list(state['requests'].items())[-128:])
        record={**public_progress(state),'user_id':uid,'lesson_id':lesson_id,'challenge_id':challenge_id,'journal_version':1}
        event={'delivery_id':_key(uid,lesson_id,challenge_id,request),'record':record,'archive_id':state.get('archive_id')}
        pending={'pending_challenge_progress':event}
        if award:pending['pending_credit_transactions']={'id':'challenge-'+_key(uid,lesson_id,challenge_id,request),'user_id':uid,'transaction_type':'credit','amount':award,'category':'challenge',
            'description':description,'created_at':now,'details':{'lesson_id':lesson_id,'challenge_id':challenge_id,'attempt_id':state['attempt_id'],'day':data.day}}
        field='challenge_journals.'+key
        query={'id':uid,'is_disabled':{'$ne':True},'credits_remaining':{'$type':'number','$gte':0,'$lte':1000000-award}}
        query.update({field+'.revision':old['revision'],field+'.attempt_id':old['attempt_id']} if stored else {field:{'$exists':False}})
        changed=await self.db.users.update_one(query,{'$set':{field:state},'$inc':{'credits_remaining':award},'$push':pending})
        if not changed.matched_count:
            # Retry only resolves a matching request; it never overwrites a newer note.
            fresh=(await self.snapshot(uid,lesson_id,challenge_id))[4]
            if fresh.get('requests',{}).get(request)==fingerprint:return await self.finish(uid,lesson_id,challenge_id)
            raise HTTPException(409,'Запись изменилась или баланс недоступен. Обновите дневник и повторите сохранение.')
        return await self.finish(uid,lesson_id,challenge_id)

    async def finish(self,uid,lesson_id,challenge_id):
        try:await self.deliver(uid)
        except Exception:log.warning('Challenge archive delivery deferred; committed journal retained')
        result=await self.read(uid,lesson_id,challenge_id)
        try:await StudentLearningService(self.db).sync_progress(uid,lesson_id)
        except Exception:result['progress_sync_pending']=True
        return result
