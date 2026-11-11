"""Read-only teaching views and durable review rewards on standalone Mongo."""
import math
import re
from datetime import datetime
from fastapi import HTTPException
from services.student_learning import _key
from services.credit_history import flush_pending_credit_transactions
from services.challenge_diary import history_entry


def paging(page, page_size, q=''):
    if type(page) is not int or not 1 <= page <= 10000 or type(page_size) is not int or not 1 <= page_size <= 100:
        raise HTTPException(422, 'Недопустимая страница')
    if not isinstance(q,str) or len(q)>100: raise HTTPException(422,'Слишком длинный поиск')


def identity_match(lesson_id=None,user_id=None):
    result={}
    for key,value in (('lesson_id',lesson_id),('user_id',user_id)):
        if value:
            if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',value): raise HTTPException(422,'Недопустимый идентификатор')
            result[key]=value
    return result


def challenge_pipeline(filters=None):
    filters=filters or {}
    # Pending records and committed credits share the same user write. Reading
    # this outbox includes a saved note even when archival delivery was delayed.
    return [{'$match':filters},{'$unionWith':{'coll':'users','pipeline':[
        {'$match':{'id':filters['user_id']} if filters.get('user_id') else {}},
        {'$project':{'pending_challenge_progress':1}},
        {'$unwind':'$pending_challenge_progress'},
        {'$replaceRoot':{'newRoot':'$pending_challenge_progress.record'}},
        {'$match':filters}]}},
        {'$sort':{'revision':-1,'last_updated':-1}},
        {'$group':{'_id':{'user':'$user_id','id':'$id'},'row':{'$first':'$$ROOT'}}},
        {'$replaceRoot':{'newRoot':'$row'}}]


def joins():
    return [
        {'$lookup':{'from':'users','let':{'uid':'$user_id'},'pipeline':[
            {'$match':{'$expr':{'$eq':['$id','$$uid']}}},
            {'$project':{'_id':0,'id':1,'name':1,'surname':1,'full_name':1,'email':1}}], 'as':'student'}},
        {'$lookup':{'from':'lessons_v2','let':{'lid':'$lesson_id'},'pipeline':[
            {'$match':{'$expr':{'$eq':['$id','$$lid']}}},
            {'$project':{'_id':0,'id':1,'title':1,'exercises.id':1,'exercises.title':1}}], 'as':'lesson'}}]


def joined_fields(row):
    student=next(iter(row.get('student') or []),{});lesson=next(iter(row.get('lesson') or []),{})
    name=student.get('full_name') or ' '.join(str(student.get(k) or '') for k in ('name','surname')).strip()
    exercise=next((e for e in lesson.get('exercises',[]) if e.get('id')==row.get('exercise_id')), {})
    return {'student_name':name or student.get('email') or row.get('user_id'), 'student_email':student.get('email'),
            'lesson_title':lesson.get('title') or row.get('lesson_id'), 'exercise_title':exercise.get('title') or row.get('exercise_id')}


async def learning_page(db,kind,page=1,page_size=25,q='',lesson_id=None,user_id=None,reviewed='all'):
    paging(page,page_size,q);filters=identity_match(lesson_id,user_id)
    if kind=='responses':
        if reviewed not in ('all','pending','reviewed'):raise HTTPException(422,'Неизвестный фильтр проверки')
        filters['attachment_draft_only']={'$ne':True}
        if reviewed!='all':filters['reviewed']=True if reviewed=='reviewed' else {'$ne':True}
        collection=db.exercise_responses;pipeline=[{'$match':filters}]
    else:
        collection=db.challenge_progress;pipeline=challenge_pipeline(filters)
    pipeline+=joins()
    if q.strip():
        fields=('id','response_text','student.full_name','student.name','student.surname','student.email','lesson.title','daily_notes.note')
        pipeline.append({'$match':{'$or':[{f:{'$regex':re.escape(q.strip()),'$options':'i'}} for f in fields]}})
    selected=['id','user_id','lesson_id','student','lesson','exercise_id','response_text','reviewed','admin_comment','admin_score','points_earned',
              'submitted_at','reviewed_at','attachment_ids','attachment_files','mobile_revision'] if kind=='responses' else [
              'id','user_id','lesson_id','student','lesson','challenge_id','attempt_number','is_completed','completed_days','daily_notes','started_at','last_updated','revision']
    pipeline += [{'$sort':{'reviewed':1,'submitted_at':-1,'last_updated':-1,'id':1}},
                 {'$facet':{'total':[{'$count':'value'}], 'rows':[{'$skip':(page-1)*page_size},{'$limit':page_size},{'$project':{'_id':0,**{f:1 for f in selected}}}]}}]
    result=(await collection.aggregate(pipeline).to_list(1))[0]
    total=next(iter(result['total']),{}).get('value',0)
    if kind!='responses':
        result['rows']=[{**{k:r.get(k) for k in ('id','user_id','lesson_id','challenge_id','attempt_number','is_completed','completed_days','started_at','last_updated')},
                         **joined_fields(r),'daily_notes':history_entry(r)['daily_notes']} for r in result['rows']]
    return {'rows':result['rows'],'total':total,'page':page,'page_size':page_size,'has_more':page*page_size<total}


async def learning_analytics(db):
    lesson_rows=await db.lessons_v2.find({}, {'_id':0,'id':1,'title':1,'is_active':1}).sort('order',1).limit(1000).to_list(1000)
    progress=await db.lesson_progress.aggregate([{'$group':{'_id':'$lesson_id','students':{'$addToSet':'$user_id'},
        'completed_students':{'$sum':{'$cond':['$is_completed',1,0]}},'average_completion':{'$avg':'$completion_percentage'}}}]).to_list(None)
    responses=await db.exercise_responses.aggregate([{'$match':{'attachment_draft_only':{'$ne':True}}},
        {'$group':{'_id':'$lesson_id','responses':{'$sum':1},'pending_reviews':{'$sum':{'$cond':['$reviewed',0,1]}}}}]).to_list(None)
    quizzes=await db.quiz_attempts.aggregate([{'$group':{'_id':'$lesson_id','quiz_attempts':{'$sum':1},'average_quiz_score':{'$avg':'$score'}}}]).to_list(None)
    challenges=await db.challenge_progress.aggregate(challenge_pipeline()+[{'$group':{'_id':'$lesson_id',
        'challenge_attempts':{'$sum':1},'completed_challenges':{'$sum':{'$cond':['$is_completed',1,0]}}}}]).to_list(None)
    maps=[{r['_id']:r for r in rows} for rows in (progress,responses,quizzes,challenges)]
    lessons=[]
    for lesson in lesson_rows:
        item={'id':lesson['id'],'title':lesson.get('title'),'is_active':bool(lesson.get('is_active')),
              **dict.fromkeys(('students','completed_students','responses','pending_reviews','quiz_attempts','challenge_attempts','completed_challenges'),0)}
        for rows in maps:
            record=rows.get(lesson['id'],{})
            item.update({k:(len(v) if k=='students' else round(v,2) if isinstance(v,float) else v) for k,v in record.items() if k!='_id'})
        lessons.append(item)
    summary={'students':await db.users.count_documents({'is_admin':{'$ne':True},'is_super_admin':{'$ne':True}}),
             'active_lessons':await db.lessons_v2.count_documents({'is_active':True})}
    for rows,keys in ((responses,('responses','pending_reviews')),(quizzes,('quiz_attempts',)),(challenges,('challenge_attempts','completed_challenges'))):
        summary.update({key:sum(row.get(key,0) for row in rows) for key in keys})
    return {'summary':summary,'lessons':lessons,'lessons_truncated':await db.lessons_v2.count_documents({})>len(lessons)}


def legacy_reward(value):
    return value if type(value) in (int,float) and math.isfinite(value) and 0<=value<=1000000 else 0


async def deliver_review_award(db, response):
    """Award only a new high-water mark; durable intent survives delivery failure.

    Review score may go down. Earned/spent credits never go down here. Baseline
    legacy reward is frozen before the first mobile/bridged review.
    """
    uid=response['user_id'];rid=response['id'];key=_key(rid);field='review_awards.'+key
    target=max(legacy_reward(response.get('review_award_target')),legacy_reward(response.get('review_legacy_watermark')))
    legacy=legacy_reward(response.get('review_legacy_watermark'))
    for _ in range(5):
        user=await db.users.find_one({'id':uid},{'id':1,'credits_remaining':1,'is_disabled':1,field:1})
        if not user:raise HTTPException(409,'Аккаунт ученика недоступен; награда ожидает начисления')
        current=(user.get('review_awards') or {}).get(key)
        previous=max(legacy,legacy_reward((current or {}).get('max_points')))
        difference=max(0,target-previous)
        if current and difference==0:
            await flush_pending_credit_transactions(db,uid)
            return {'points_awarded':0,'award_total':previous,'award_pending':False}
        marker={'response_id':rid,'max_points':max(target,previous),'legacy_points':legacy,'updated_at':datetime.utcnow()}
        update={'$set':{field:marker}}
        query={'id':uid,field+'.max_points':current['max_points']} if current else {'id':uid,field:{'$exists':False}}
        if difference:
            query.update({'is_disabled':{'$ne':True},'credits_remaining':{'$type':'number','$gte':0,'$lte':1000000-difference}})
            event={'id':'review-'+_key(uid,rid,str(marker['max_points'])),'user_id':uid,'transaction_type':'credit','amount':difference,
                   'category':'exercise_review','description':'Баллы за проверку упражнения', 'created_at':datetime.utcnow(),
                   'details':{'lesson_id':response.get('lesson_id'),'response_id':rid,'previous_awarded':previous,'awarded_total':marker['max_points']}}
            update['$inc']={'credits_remaining':difference};update['$push']={'pending_credit_transactions':event}
        result=await db.users.update_one(query,update)
        if result.matched_count:
            try:await flush_pending_credit_transactions(db,uid)
            except Exception:pass # credit and durable history outbox are already committed
            return {'points_awarded':difference,'award_total':marker['max_points'],'award_pending':False}
    raise HTTPException(409,'Баланс не позволяет начислить награду сейчас; проверка сохранена')
