"""Assigned consultations, atomic purchases and short-lived material access."""
import hashlib
import hmac
import logging
import math
import mimetypes
import os
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.parse import urlsplit
from fastapi import HTTPException
from jose import jwt,JWTError
from pydantic import BaseModel,ConfigDict,Field
from auth import signing_key
from services.student_learning import _student
from services.credit_history import flush_pending_credit_transactions

log=logging.getLogger(__name__)
class ConsultationPurchase(BaseModel):
    model_config=ConfigDict(extra='forbid')
    expected_cost:float=Field(strict=True,ge=0,le=1000000,allow_inf_nan=False)

def cost(item):
    value=item.get('cost_credits')
    return value if type(value) in (int,float) and math.isfinite(value) and 0<=value<=1000000 else None

def marker(consultation_id):
    return hashlib.sha256(consultation_id.encode()).hexdigest()

def media_key():
    return hmac.new(signing_key().encode(),b'numerom:consultation-media:v1',hashlib.sha256).hexdigest()

class Consultations:
    def __init__(self,db,root='uploads/consultations',public_url=None,private_root=None):
        self.db=db;self.root=Path(root).resolve();self.public_url=public_url
        self.private_root=Path(private_root or Path(__file__).resolve().parents[1]/'private/consultation-materials').resolve()

    async def assigned(self,uid,cid):
        user=await _student(self.db,uid)
        item=await self.db.personal_consultations.find_one({'id':cid,'assigned_user_id':uid,'is_active':{'$ne':False}})
        if not item:raise HTTPException(404,'Консультация не найдена')
        return user,item

    async def unlocked(self,user,item):
        return (cost(item)==0 or marker(item['id']) in user.get('consultation_access',{}) or
                await self.db.consultation_purchases.find_one({'user_id':user['id'],'consultation_id':item['id']}) is not None)

    async def card(self,user,item):
        return {'id':item['id'],'title':str(item.get('title') or 'Персональная консультация'),
            'description':str(item.get('description') or ''),'cost_credits':cost(item),
            'is_purchased':bool(await self.unlocked(user,item)),
            'has_video':bool(item.get('video_file_id') or item.get('video_url')),'has_pdf':bool(item.get('pdf_file_id'))}

    async def listing(self,uid):
        user=await _student(self.db,uid)
        await self.deliver(user)
        rows=await self.db.personal_consultations.find({'assigned_user_id':uid,'is_active':{'$ne':False}}).sort('created_at',-1).limit(100).to_list(100)
        return {'consultations':[await self.card(user,item) for item in rows]}

    async def purchase(self,uid,cid,expected):
        user,item=await self.assigned(uid,cid)
        if await self.unlocked(user,item):
            await self.deliver(user)
            return await self.card(user,item)
        price=cost(item)
        if price is None:raise HTTPException(503,'Стоимость консультации уточняется')
        if expected!=price:raise HTTPException(409,'Стоимость изменилась. Обновите список и подтвердите новую цену.')
        key=marker(cid);field='consultation_access.'+key;now=datetime.utcnow()
        purchase_id='consultation-'+hashlib.sha256((uid+':'+cid).encode()).hexdigest()
        entry={'id':purchase_id,'user_id':uid,'transaction_type':'debit','amount':-price,'category':'consultation',
            'description':'Консультация: '+str(item.get('title') or 'Персональная консультация'),
            'details':{'consultation_id':cid},'created_at':now}
        committed={'id':purchase_id,'consultation_id':cid,'cost_credits':price,'purchased_at':now}
        result=await self.db.users.update_one({'id':uid,'is_disabled':{'$ne':True},field:{'$exists':False},'credits_remaining':{'$gte':price}},
            {'$inc':{'credits_remaining':-price},'$set':{field:committed},'$push':{'pending_credit_transactions':entry}})
        user=await _student(self.db,uid)
        receipt=user.get('consultation_access',{}).get(key)
        if not result.matched_count and not receipt:raise HTTPException(402,'Недостаточно баллов. Пополните баланс.')
        await self.deliver(user)
        return await self.card(user,item)

    async def deliver(self,user):
        try:
            for receipt in user.get('consultation_access',{}).values():
                await self.db.consultation_purchases.update_one({'_id':receipt['id']},{'$setOnInsert':{**receipt,'user_id':user['id']}},upsert=True)
            await flush_pending_credit_transactions(self.db,user['id'])
        except Exception:log.warning('Consultation history deferred; purchase remains committed in user document')

    async def material(self,uid,cid,kind):
        user,item=await self.assigned(uid,cid)
        if not await self.unlocked(user,item):raise HTTPException(403,'Сначала откройте доступ к консультации')
        if kind not in ('video','pdf'):raise HTTPException(404,'Материал не найден')
        fid=item.get(kind+'_file_id')
        if not fid:
            url=item.get('video_url') if kind=='video' else None
            parsed=urlsplit(url or '')
            if parsed.scheme=='https' and parsed.hostname and parsed.hostname not in ('localhost','127.0.0.1','::1') and not parsed.username and not parsed.password:
                return user,{'external':url},None
            raise HTTPException(404,'Мастер ещё не добавил этот материал')
        record=await self.db.files.find_one({'id':fid})
        if not record or record.get('lesson_id'):raise HTTPException(404,'Материал недоступен')
        if record.get('private_consultation') is True and record.get('consultation_id')!=cid:raise HTTPException(404,'Материал недоступен')
        return user,record,self.file_path(record)

    def file_path(self,record):
        stored=record.get('stored_name','')
        if not stored or Path(stored).name!=stored or '\\' in stored or '\x00' in stored:raise HTTPException(404,'Материал недоступен')
        root=self.private_root if record.get('private_consultation') is True else self.root
        path=(root/stored).resolve()
        if not path.is_relative_to(root) or not path.is_file():raise HTTPException(404,'Файл материала недоступен')
        if path.stat().st_size>512*1024*1024:raise HTTPException(413,'Материал слишком большой для просмотра')
        return path

    async def admin_material(self,uid,cid,fid):
        from services.admin_management import AdminManagementService
        user=await AdminManagementService(self.db).authorize(uid)
        if not await self.db.personal_consultations.find_one({'id':cid}):raise HTTPException(404,'Консультация не найдена')
        record=await self.db.files.find_one({'id':fid,'consultation_id':cid,'private_consultation':True,'mime_type':'application/pdf'})
        if not record:raise HTTPException(404,'PDF не найден')
        return user,record,self.file_path(record)

    async def admin_access(self,uid,cid,fid):
        user,record,_=await self.admin_material(uid,cid,fid)
        return self.signed_access(user,cid,'pdf',record,admin_preview=True)

    async def access(self,uid,cid,kind):
        user,record,path=await self.material(uid,cid,kind)
        if 'external' in record:return {'url':record['external'],'expires_in':None,'external':True}
        return self.signed_access(user,cid,kind,record)

    def signed_access(self,user,cid,kind,record,admin_preview=False):
        public=(self.public_url or os.environ.get('PUBLIC_API_URL','')).rstrip('/');p=urlsplit(public)
        if p.scheme!='https' or not p.hostname or p.username or p.password or p.path or p.query or p.fragment:raise HTTPException(503,'Просмотр материалов ещё настраивается')
        token=jwt.encode({'sub':user['id'],'consultation':cid,'kind':kind,'file':record['id'],'auth_version':user.get('auth_version',0),'admin_preview':admin_preview,
            'aud':'numerom-consultation-media','exp':datetime.now(timezone.utc)+timedelta(minutes=5)},media_key(),algorithm='HS256')
        return {'url':public+'/api/student/consultation-media/'+token,'expires_in':300,'external':False}

    async def resolve(self,token):
        try:
            c=jwt.decode(token,media_key(),algorithms=['HS256'],audience='numerom-consultation-media',options={'require_exp':True,'require_sub':True})
            if not all(isinstance(c.get(k),str) and c[k] for k in ('sub','consultation','kind','file')):raise ValueError()
        except (JWTError,ValueError):raise HTTPException(401,'Ссылка истекла. Откройте материал ещё раз.')
        if c.get('admin_preview') is True:user,record,path=await self.admin_material(c['sub'],c['consultation'],c['file'])
        else:user,record,path=await self.material(c['sub'],c['consultation'],c['kind'])
        if record.get('id')!=c['file'] or c.get('auth_version')!=user.get('auth_version',0):raise HTTPException(401,'Ссылка больше не действует')
        name=Path(str(record.get('original_name') or path.name)).name.replace('\r','').replace('\n','')
        mime=mimetypes.guess_type(name)[0] or 'application/octet-stream';safe=mime=='application/pdf' or mime.startswith(('video/','audio/'))
        return path,name,mime if safe else 'application/octet-stream','inline' if safe else 'attachment'
