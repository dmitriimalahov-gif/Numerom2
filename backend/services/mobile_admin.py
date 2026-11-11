"""Bounded administrative edits with account authorization and revision receipts."""
import hashlib,json,re,uuid
from datetime import datetime
from typing import Annotated,Literal
from fastapi import HTTPException
from pydantic import BaseModel,ConfigDict,Field,StrictBool,StrictInt,StrictFloat,StrictStr,field_validator,model_validator
from pymongo.errors import DuplicateKeyError
from services.admin_management import AdminManagementService
from services.student_learning import Identifier
from services.mobile_admin_settings import settings_spec, validate_settings
from services.mobile_admin_learning import paging, learning_page, joined_fields, learning_analytics, legacy_reward, deliver_review_award
from services.mobile_admin_import import lesson_preview

Text=Annotated[StrictStr,Field(max_length=10000)]
class Model(BaseModel):model_config=ConfigDict(extra='forbid')
class Change(Model):
    request_id:uuid.UUID
    revision:StrictInt=Field(ge=0)
    reason:StrictStr=Field(min_length=1,max_length=500)
    @field_validator('reason')
    @classmethod
    def reason_required(cls,v):
        if not v.strip():raise ValueError('Укажите причину изменения')
        return v.strip()
class Theory(Model):
    id:Identifier|None=None
    order:StrictInt=Field(default=0,ge=0,le=100000)
    title:StrictStr=Field(max_length=300)
    content:Text
class Exercise(Model):
    id:Identifier
    title:StrictStr=Field(min_length=1,max_length=300)
    description:Text=''
    instructions:Text=''
    type:Literal['text','multiple_choice','calculation','reflection']='text'
    expected_outcome:Text=''
    correct_answer:Text|None=None
    order:StrictInt=Field(default=0,ge=0,le=100000)
    options:list[Annotated[StrictStr,Field(max_length=4000)]]=Field(default_factory=list,max_length=20)
class QuizQuestion(Model):
    id:Identifier
    question:Annotated[StrictStr,Field(min_length=1,max_length=10000)]
    type:Literal['text','multiple_choice','true_false']='multiple_choice'
    options:list[Annotated[StrictStr,Field(min_length=1,max_length=4000)]]=Field(default_factory=list,max_length=20)
    correct_answer:Annotated[StrictStr,Field(min_length=1,max_length=4000)]
    explanation:Text=''
    points:StrictInt=Field(default=1,ge=1,le=100)
    order:StrictInt=Field(default=0,ge=0,le=100000)
    @model_validator(mode='after')
    def coherent_answer(self):
        if not self.question.strip() or not self.correct_answer.strip():raise ValueError('Вопрос и правильный ответ обязательны')
        if self.type!='text':
            if len(self.options)<2 or len(set(self.options))!=len(self.options) or any(not v.strip() for v in self.options):raise ValueError('Добавьте разные непустые варианты ответа')
            if self.correct_answer not in self.options:raise ValueError('Правильный ответ должен совпадать с вариантом')
            if self.type=='true_false' and len(self.options)!=2:raise ValueError('Для верно/неверно нужны два варианта')
        return self
class QuizChange(Model):
    id:Identifier
    title:Annotated[StrictStr,Field(min_length=1,max_length=300)]
    description:Text=''
    passing_score:StrictInt=Field(default=70,ge=0,le=100)
    questions:list[QuizQuestion]=Field(min_length=1,max_length=100)
    @model_validator(mode='after')
    def unique_questions(self):
        if len({q.id for q in self.questions})!=len(self.questions):raise ValueError('Идентификаторы вопросов должны отличаться')
        return self
class ChallengeDay(Model):
    day:StrictInt=Field(ge=1,le=90)
    title:Annotated[StrictStr,Field(min_length=1,max_length=300)]
    description:Text=''
    tasks:list[Annotated[StrictStr,Field(min_length=1,max_length=4000)]]=Field(default_factory=list,max_length=30)
class ChallengeChange(Model):
    id:Identifier
    title:Annotated[StrictStr,Field(min_length=1,max_length=300)]
    description:Text=''
    duration_days:StrictInt=Field(ge=1,le=90)
    daily_tasks:list[ChallengeDay]=Field(min_length=1,max_length=90)
    @model_validator(mode='after')
    def complete_days(self):
        if len(self.daily_tasks)!=self.duration_days or {d.day for d in self.daily_tasks}!=set(range(1,self.duration_days+1)):raise ValueError('Добавьте каждый день дневника по порядку без повторений')
        return self
class LessonChange(Change):
    title:StrictStr=Field(min_length=1,max_length=300)
    description:Text=''
    level:StrictInt=Field(ge=1,le=100)
    order:StrictInt=Field(ge=0,le=100000)
    is_active:StrictBool
    theory:list[Theory]|None=Field(default=None,max_length=100)
    exercises:list[Exercise]|None=Field(default=None,max_length=100)
    video_url:StrictStr|None=Field(default=None,max_length=2048)
    @field_validator('video_url')
    @classmethod
    def lesson_video(cls,v):
        if v:
            from urllib.parse import urlsplit
            p=urlsplit(v)
            if p.scheme!='https' or not p.hostname or p.username or p.password or p.hostname in ('localhost','127.0.0.1','::1'):raise ValueError('Укажите HTTPS ссылку на видео')
        return v
    quiz:QuizChange|None=None
    challenge:ChallengeChange|None=None
class ConsultationChange(Change):
    title:StrictStr=Field(min_length=1,max_length=300)
    description:Text=''
    assigned_user_id:Identifier
    cost_credits:StrictInt=Field(ge=0,le=1000000)
    is_active:StrictBool
    video_url:StrictStr=Field(default='',max_length=2048)
    pdf_file_id:Identifier|None=None
    @field_validator('video_url')
    @classmethod
    def safe_url(cls,v):
        from urllib.parse import urlsplit
        p=urlsplit(v)
        if v and (p.scheme!='https' or not p.hostname or p.username or p.password or p.hostname in ('localhost','127.0.0.1','::1')):raise ValueError('Укажите HTTPS ссылку на видео')
        return v
class ReviewChange(Change):
    admin_comment:Text
    expected_answer:StrictStr=Field(min_length=1,max_length=64)
    admin_score:StrictInt|None=Field(default=None,ge=0,le=100)
    points_earned:StrictInt|None=Field(default=None,ge=0,le=100)
class SettingsChange(Change):
    values:dict[str,StrictInt|StrictFloat|StrictBool]=Field(min_length=1,max_length=100)
class ImportPreview(Model):
    text:StrictStr=Field(min_length=1,max_length=200000)
class LessonImport(Change,ImportPreview):
    fingerprint:StrictStr=Field(pattern=r'^[a-f0-9]{64}$')
class ArchiveChange(Change):pass
class LegacyReview(Model):
    points_earned:StrictInt=Field(default=0,ge=0,le=100)
    admin_comment:Text=''
    review_start_time:StrictStr|None=Field(default=None,max_length=80)
    request_id:uuid.UUID|None=None
class LevelChange(Model):
    level:StrictInt=Field(ge=1,le=100)
    expected_level:StrictInt=Field(ge=1,le=100)
    reason:StrictStr=Field(min_length=1,max_length=500)

def answer_tag(row):
    return hashlib.sha256(json.dumps({k:row.get(k) for k in ('response_text','submitted_at','attachment_ids')},sort_keys=True,default=str).encode()).hexdigest()

class MobileAdmin:
    def __init__(self,db):self.db=db;self.accounts=AdminManagementService(db)
    async def authorize(self,uid):return await self.accounts.authorize(uid)
    @staticmethod
    def public(row,fields):
        return {'revision':row.get('mobile_revision',0),**{k:row.get(k) for k in fields}}
    async def mutate(self,collection,identity,body,patch,actor,create=False,guard=None):
        request=str(body.request_id);fingerprint=hashlib.sha256(json.dumps(body.model_dump(mode='json'),sort_keys=True).encode()).hexdigest()
        old=await collection.find_one({'id':identity})
        if old and old.get('mobile_request')==request:
            if old.get('mobile_fingerprint')!=fingerprint:raise HTTPException(409,'Этот запрос уже использован для других данных')
            return old
        if not old and not create:raise HTTPException(404,'Запись не найдена')
        if (old or {}).get('mobile_revision',0)!=body.revision:raise HTTPException(409,'Запись изменилась. Обновите её перед сохранением.')
        event={'actor_id':actor['id'],'reason':body.reason,'at':datetime.utcnow(),'fields':sorted(patch)}
        changes={**patch,'updated_at':datetime.utcnow(),'updated_by':actor['id'],'mobile_revision':body.revision+1,'mobile_request':request,'mobile_fingerprint':fingerprint}
        if not old:
            row={'_id':'mobile-'+identity,'id':identity,'created_at':datetime.utcnow(),**changes,'mobile_audit':[event]}
            try:await collection.insert_one(row)
            except DuplicateKeyError:raise HTTPException(409,'Запись уже создана. Обновите список.')
            return row
        query={'_id':old['_id'],'mobile_revision':old.get('mobile_revision') if 'mobile_revision' in old else {'$exists':False}}
        query.update(guard or {})
        result=await collection.update_one(query,{'$set':changes,'$push':{'mobile_audit':{'$each':[event],'$slice':-100}}})
        if not result.matched_count:raise HTTPException(409,'Запись изменилась. Обновите её перед сохранением.')
        return {**old,**changes}
    async def content_list(self,uid,kind,page=1,page_size=25,q='',archived='all'):
        await self.authorize(uid);paging(page,page_size,q)
        if archived not in ('all','active','archived'):raise HTTPException(422,'Неизвестный фильтр архива')
        query={}
        if archived!='all':query['is_archived']=True if archived=='archived' else {'$ne':True}
        if q.strip():query['$or']=[{k:{'$regex':re.escape(q.strip()),'$options':'i'}} for k in ('id','title','description')]
        collection=self.db.lessons_v2 if kind=='lessons' else self.db.personal_consultations
        fields=['id','title','description','level','order','is_active','is_archived','theory','exercises','quiz','challenge','video_url','video_platform'] if kind=='lessons' else ['id','title','description','assigned_user_id','cost_credits','is_active','is_archived','video_url','video_file_id','pdf_file_id']
        total=await collection.count_documents(query)
        rows=await collection.find(query,{**{f:1 for f in fields},'mobile_revision':1}).sort([('order',1),('created_at',-1),('id',1)]).skip((page-1)*page_size).limit(page_size).to_list(page_size)
        return {kind:[{**self.public(r,fields),'is_archived':bool(r.get('is_archived'))} for r in rows], 'total':total,'page':page,'page_size':page_size,'has_more':page*page_size<total}
    async def lessons(self,uid,**query):return await self.content_list(uid,'lessons',**query)
    async def lesson(self,uid,lid,body):
        actor=await self.authorize(uid)
        patch=body.model_dump(exclude={'request_id','revision','reason'},exclude_none=True)
        existing=await self.db.lessons_v2.find_one({'id':lid}) or {}
        if existing.get('is_archived'):raise HTTPException(409,'Урок в архиве; его история сохранена')
        if 'video_url' in patch:patch['video_platform']='external' if patch['video_url'] else existing.get('video_platform')
        for section in ('theory','exercises'):
            if section in patch:
                prior={r.get('id'):r for r in existing.get(section,[]) if isinstance(r,dict) and r.get('id')}
                patch[section]=[{**prior.get(r.get('id'),{}),**r,'id':r.get('id') or str(uuid.uuid4())} for r in patch[section]]
                if len({r['id'] for r in patch[section]})!=len(patch[section]):raise HTTPException(422,'Идентификаторы разделов должны отличаться')
        if 'exercises' in patch and len({e['id'] for e in patch['exercises']})!=len(patch['exercises']):raise HTTPException(422,'Идентификаторы упражнений должны отличаться')
        for section,children,key in (('quiz','questions','id'),('challenge','daily_tasks','day')):
            if section in patch:
                old=existing.get(section) or {}
                if old.get('id')!=patch[section]['id']:old={}
                prior={r[key]:r for r in old.get(children,[]) if isinstance(r,dict) and key in r}
                patch[section]={**old,**patch[section],children:[{**prior.get(r[key],{}),**r} for r in patch[section][children]]}
        row=await self.mutate(self.db.lessons_v2,lid,body,patch,actor,create=True,guard={'is_archived':{'$ne':True}})
        return {'id':row['id'],'revision':row['mobile_revision']}
    async def consultations(self,uid,**query):return await self.content_list(uid,'consultations',**query)
    async def consultation(self,uid,cid,body):
        actor=await self.authorize(uid)
        existing=await self.db.personal_consultations.find_one({'id':cid}) or {}
        if existing.get('is_archived'):raise HTTPException(409,'Консультация в архиве; её история сохранена')
        if not await self.db.users.find_one({'id':body.assigned_user_id}):raise HTTPException(404,'Ученик не найден')
        patch=body.model_dump(exclude={'request_id','revision','reason'},exclude_unset=True)
        if body.video_url:patch['video_file_id']=None
        if body.pdf_file_id is not None and not await self.db.files.find_one({'id':body.pdf_file_id,'consultation_id':cid,'private_consultation':True,'mime_type':'application/pdf'}):raise HTTPException(422,'PDF должен быть загружен к этой консультации')
        row=await self.mutate(self.db.personal_consultations,cid,body,patch,actor,create=True,guard={'is_archived':{'$ne':True}})
        return {'id':row['id'],'revision':row['mobile_revision']}
    async def archive(self,uid,kind,identity,body):
        actor=await self.authorize(uid)
        collection=self.db.lessons_v2 if kind=='lessons' else self.db.personal_consultations
        row=await self.mutate(collection,identity,body,{'is_archived':True,'is_active':False,'archived_at':datetime.utcnow()},actor)
        return {'id':row['id'],'revision':row['mobile_revision'],'is_archived':True}
    async def preview_import(self,uid,body):
        await self.authorize(uid);return lesson_preview(body.text)
    async def import_lesson(self,uid,body):
        actor=await self.authorize(uid);preview=lesson_preview(body.text)
        if body.fingerprint!=preview['fingerprint']:raise HTTPException(409,'Предпросмотр изменился. Проверьте текст перед импортом.')
        if body.revision!=0:raise HTTPException(422,'Импорт создаёт новый черновик')
        identity='import-'+hashlib.sha256((uid+'\0'+str(body.request_id)).encode()).hexdigest()[:32]
        row=await self.mutate(self.db.lessons_v2,identity,body,{**preview['lesson'],'module':'Импортированные материалы','is_archived':False,'import_fingerprint':preview['fingerprint']},actor,create=True)
        return {'id':row['id'],'revision':row['mobile_revision']}
    async def responses(self,uid,**query):
        await self.authorize(uid);result=await learning_page(self.db,'responses',**query)
        fields=['id','user_id','lesson_id','exercise_id','response_text','reviewed','admin_comment','admin_score','points_earned','attachment_ids','submitted_at','reviewed_at']
        rows=result.pop('rows')
        return {**result,'responses':[{**self.public(r,fields),**joined_fields(r),
            'attachments':[{k:a.get(k) for k in ('id','name','mime','size')} for a in r.get('attachment_files',[]) if isinstance(a,dict) and a.get('id') in (r.get('attachment_ids') or [])],
            'expected_answer':answer_tag(r)} for r in rows]}
    async def challenge_notes(self,uid,**query):
        await self.authorize(uid);result=await learning_page(self.db,'notes',**query)
        return {**{k:v for k,v in result.items() if k!='rows'},'notes':result['rows']}
    async def analytics(self,uid):
        await self.authorize(uid);return await learning_analytics(self.db)
    async def review(self,uid,rid,body):
        actor=await self.authorize(uid);row=await self.db.exercise_responses.find_one({'id':rid,'attachment_draft_only':{'$ne':True}})
        if not row:raise HTTPException(404,'Ответ не найден')
        if answer_tag(row)!=body.expected_answer:raise HTTPException(409,'Ученик изменил ответ. Прочитайте новую версию.')
        guard={k:row[k] if k in row else {'$exists':False} for k in ('response_text','submitted_at','attachment_ids')}
        guard['attachment_draft_only']={'$ne':True}
        patch={'reviewed':True,'admin_comment':body.admin_comment,'reviewed_by':uid,'reviewed_at':datetime.utcnow()}
        if body.admin_score is not None:patch['admin_score']=body.admin_score
        if body.points_earned is not None:
            patch.update(points_earned=body.points_earned,
                review_legacy_watermark=legacy_reward(row.get('review_legacy_watermark',row.get('points_earned'))),
                review_award_target=max(body.points_earned,legacy_reward(row.get('review_award_target'))))
        saved=await self.mutate(self.db.exercise_responses,rid,body,patch,actor,guard=guard)
        reward={'points_awarded':0,'award_total':legacy_reward(saved.get('review_legacy_watermark',saved.get('points_earned'))),'award_pending':False}
        if 'review_award_target' in saved:
            try:reward=await deliver_review_award(self.db,saved)
            except Exception:reward['award_pending']=True
        return {'id':saved['id'],'revision':saved['mobile_revision'],**reward}
    async def legacy_review(self,uid,rid,body):
        await self.authorize(uid)
        row=await self.db.exercise_responses.find_one({'id':rid,'attachment_draft_only':{'$ne':True}})
        if not row:raise HTTPException(404,'Ответ не найден')
        # Same service and user-document watermark as the mobile endpoint. A
        # legacy request cannot bypass answer/revision guards or duplicate pay.
        revision=row.get('mobile_revision',0)
        if body.request_id and str(body.request_id)==row.get('mobile_request'):revision=max(0,revision-1)
        request=ReviewChange(request_id=body.request_id or uuid.uuid4(),revision=revision,
            reason='Проверка упражнения в веб-кабинете',admin_comment=body.admin_comment,expected_answer=answer_tag(row),points_earned=body.points_earned)
        result=await self.review(uid,rid,request)
        return {'message':'Ответ проверен','points_earned':body.points_earned,'admin_comment':body.admin_comment,**result}
    def settings(self,kind):
        collection,defaults,fields=settings_spec(kind)
        return getattr(self.db,collection),defaults,fields
    async def read_settings(self,uid,kind):
        await self.authorize(uid);collection,defaults,fields=self.settings(kind)
        row=await collection.find_one({'is_active':True}) or {}
        return {'revision':row.get('mobile_revision',0),'values':{k:row.get(k,v) for k,v in defaults.items()},'fields':fields}
    async def write_settings(self,uid,kind,body):
        actor=await self.authorize(uid);collection,defaults,fields=self.settings(kind)
        if set(body.values)-set(defaults):raise HTTPException(422,'Неизвестная настройка')
        old=await collection.find_one({'is_active':True})
        merged={k:(old or {}).get(k,v) for k,v in defaults.items()};merged.update(body.values)
        validate_settings(kind,merged)
        identity=old['id'] if old else 'mobile-'+kind+'-config'
        await self.mutate(collection,identity,body,{**merged,'is_active':True},actor,create=True)
        return await self.read_settings(uid,kind)
    async def level(self,uid,target,body):
        actor=await self.authorize(uid);user=await self.accounts._target(target);self.accounts._check_target(actor,user)
        if not body.reason.strip():raise HTTPException(422,'Укажите причину')
        event={'id':str(uuid.uuid4()),'actor_id':uid,'action':'learning_level','reason':body.reason.strip(),'before':{'level':body.expected_level},'after':{'level':body.level},'created_at':datetime.utcnow()}
        result=await self.db.users.update_one({'id':target,'level':body.expected_level},{'$set':{'level':body.level},'$push':{'admin_history':{'$each':[event],'$slice':-100}}})
        if not result.matched_count:raise HTTPException(409,'Уровень изменился. Обновите пользователя.')
        return {'level':body.level}
