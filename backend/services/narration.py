"""Local narration catalog, bounded queue, and revocable lesson-scoped playback."""
import hashlib
import hmac
import fcntl
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlsplit
from fastapi import HTTPException
from jose import jwt, JWTError
from auth import signing_key
from domain.narration import clip, lesson_clips
from domain.report_audio import ready_audio
from domain.media_retry import scheduled
from services.report_files import read_json, write_json
from services.student_learning import _student, require_student_lesson

DEFAULT_ROOT=Path(__file__).resolve().parents[1]/'private/narration'
PROJECT_SOURCE=Path(__file__).resolve().parents[2]/'packages/project-knowledge/ru.json'
QUEUE_LIMIT=2048

def narration_key():
    return hmac.new(signing_key().encode(),b'numerom:narration:v1',hashlib.sha256).hexdigest()

class NarrationService:
    def __init__(self,db,root=DEFAULT_ROOT,project_source=PROJECT_SOURCE,public_url=None):
        self.db=db;self.root=Path(root).resolve();self.project_source=Path(project_source);self.public_url=public_url

    async def source(self,user_id,scope,source_id):
        if scope=='full-report':
            from services.full_reports import FullReports
            return await FullReports(self.db).narration_source(user_id,source_id)
        if scope=='lesson':
            user,lesson=await require_student_lesson(self.db,user_id,source_id)
            return user,[self.prefer_current(self.prefer_current(new,previous),old) for new,previous,old in
                         zip(lesson_clips(lesson),lesson_clips(lesson,previous_pronunciation=True),lesson_clips(lesson,consultation=False))]
        if scope=='project' and source_id=='project':
            user=await _student(self.db,user_id)
            return user,self.project_items()
        raise HTTPException(404,'Раздел озвучки не найден')

    def project_items(self):
        """Shared guide narration: the same text for every visitor, no personal data."""
        entries=json.loads(self.project_source.read_text())['items']
        return [self.prefer_current(self.prefer_current(clip(e['id'],e.get('section','guide'),e['title'],e['text']),
                    clip(e['id'],e.get('section','guide'),e['title'],e['text'],previous_pronunciation=True)),
                    clip(e['id'],e.get('section','guide'),e['title'],e['text'],consultation=False)) for e in entries]

    def prefer_current(self, current, previous):
        """Keep playback available while the authorized batch records the new voice.

        Both candidates are derived from today's visible source, so hidden/edited
        content can never be restored by this fallback. A guest still cannot queue.
        Paid reports are frozen and deliberately do not use this transition.
        """
        if self.state(current)['status'] != 'ready' and self.state(previous)['status'] == 'ready':
            return {**previous, 'replacement_pending': True}
        return current

    def public_catalog(self):
        """Guide narration for guests: verified recordings only; a guest never queues synthesis."""
        result=[]
        for item in self.project_items():
            state=self.state(item)
            if state['status']=='ready':state=self.media_link(state,{'sub':'guest','scope':'public-project','source':'project',
                'clip':item['id'],'hash':item['hash']})
            result.append({**item,**state})
        return {'items':result}

    def folder(self,key):
        if not re.fullmatch('[a-f0-9]{64}',key):raise HTTPException(404,'Запись не найдена')
        folder=self.root/'clips'/key
        if folder.resolve()!=folder or not folder.resolve().is_relative_to(self.root):raise HTTPException(404,'Запись недоступна')
        return folder

    def state(self,item):
        folder=self.folder(item['hash']);ready=folder/'ready.json';audio=folder/'audio.m4a'
        retry=read_json(folder/'automatic-retry.json')
        recovering=(folder/'failed.json').exists() and scheduled(retry,'after')
        pending={'status':'preparing','seconds':0,'automatic_retry':True,
            'retry_at':retry['after']} if recovering else None
        if item.get('id','').startswith('full-report-'):
            meta=ready_audio(folder,item['hash'])
            if meta:return {'status':'ready','seconds':meta['seconds']}
            if recovering:return pending
            if ready.exists() or (folder/'failed.json').exists():return {'status':'review','seconds':0}
            return {'status':'preparing' if (self.root/'jobs'/(item['hash']+'.json')).exists() else 'missing','seconds':0}
        meta=ready_audio(folder,item['hash'])
        if meta:return {'status':'ready','seconds':meta['seconds']}
        if recovering:return pending
        if (folder/'failed.json').exists():return {'status':'review','seconds':0}
        return {'status':'preparing' if (self.root/'jobs'/(item['hash']+'.json')).exists() else 'missing','seconds':0}

    async def catalog(self,user_id,scope,source_id):
        user,items=await self.source(user_id,scope,source_id)
        result=[]
        for item in items:
            state=self.state(item)
            if state['status']=='ready':state=self.playback(user_id,user,scope,source_id,item,state)
            result.append({**item,**state})
        return {'items':result}

    async def selected(self,user_id,scope,source_id,clip_id):
        user,items=await self.source(user_id,scope,source_id)
        item=next((i for i in items if i['id']==clip_id),None)
        if item is None:raise HTTPException(404,'Фрагмент озвучки не найден')
        return user,item

    async def access(self,user_id,scope,source_id,clip_id):
        user,item=await self.selected(user_id,scope,source_id,clip_id)
        state=self.state(item)
        if state['status']!='ready':
            if state['status']=='review':return {**state,'message':'Запись проходит проверку произношения.'}
            self.enqueue(item,scope,source_id)
            return {'status':'preparing','message':'Запись готовится. Можно продолжить чтение и проверить позже.'}
        return self.playback(user_id,user,scope,source_id,item,state)

    def enqueue(self,item,scope,source_id):
        """Queue already-authorized source text without re-entering source resolution."""
        if self.state(item)['status'] in ('ready','review'):return
        jobs=self.root/'jobs';jobs.mkdir(parents=True,exist_ok=True,mode=0o700)
        if not 1<=len(item['text'])<=20000:raise HTTPException(413,'Материал нужно разделить на небольшие части')
        destination=jobs/(item['hash']+'.json')
        descriptor=os.open(jobs/'.queue.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        with os.fdopen(descriptor,'r+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            saved=read_json(destination)
            if saved and saved.get('hash')==item['hash'] and saved.get('text')==item['text']:return
            pending=0
            for path in jobs.glob('*.json'):
                if path==destination:continue
                queued=read_json(path) or {};cache=self.root/'clips'/path.stem
                complete=ready_audio(cache,path.stem) if str(queued.get('id','')).startswith('full-report-') else (cache/'ready.json').is_file()
                pending+=not bool(complete)
                if pending>=QUEUE_LIMIT:raise HTTPException(503,'Очередь озвучки заполнена. Попробуйте позже.')
            write_json(destination,{**item,'scope':scope,'lesson_title':source_id})

    def retry_report(self,items,order_id):
        """Only call with the current validated snapshot of an owned paid order."""
        if any(not item.get('id','').startswith('full-report-') for item in items):
            raise ValueError('Only paid-report narration can be retried here')
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        descriptor=os.open(self.root/'report-retry.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        blocked=0
        with os.fdopen(descriptor,'r+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            for item in items:
                if self.state(item)['status']=='review':
                    target=self.folder(item['hash']);saved=read_json(target/'retry.json') or {};now=time.time()
                    history=saved.get('attempts',[])
                    attempts=[value for value in history if isinstance(value,(int,float)) and now-3600<value<=now] if isinstance(history,list) else []
                    if len(attempts)>=3 or attempts and now-max(attempts)<60:
                        blocked+=1;continue
                    write_json(target/'retry.json',{'attempts':[*attempts,now]})
                    (target/'failed.json').unlink(missing_ok=True)
                    (target/'ready.json').unlink(missing_ok=True)
                self.enqueue(item,'full-report',order_id)
        return blocked

    def playback(self,user_id,user,scope,source_id,item,state):
        return self.media_link(state,{'sub':user_id,'scope':scope,'source':source_id,'clip':item['id'],'hash':item['hash'],
            'auth_version':user.get('auth_version',0)})

    def media_link(self,state,claims):
        public=(self.public_url or os.environ.get('PUBLIC_API_URL','')).rstrip('/')
        parsed=urlsplit(public)
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
            raise HTTPException(503,'Адрес озвучки ещё настраивается')
        token=jwt.encode({**claims,'aud':'numerom-narration','exp':int(time.time())+1800},narration_key(),algorithm='HS256')
        return {**state,'url':public+'/api/student/narration-media/'+token,'expires_in':1800}

    async def resolve(self,token):
        try:
            claims=jwt.decode(token,narration_key(),algorithms=['HS256'],audience='numerom-narration',options={'require_exp':True,'require_sub':True})
            if not all(isinstance(claims.get(k),str) for k in ['sub','scope','source','clip','hash']):raise ValueError()
        except (JWTError,ValueError):raise HTTPException(401,'Ссылка истекла. Нажмите «Слушать» ещё раз.')
        if claims['scope']=='public-project':
            # A guest link opens only shared guide narration, never a lesson or report.
            if claims['sub']!='guest' or claims['source']!='project':raise HTTPException(401,'Ссылка истекла. Нажмите «Слушать» ещё раз.')
            item=next((i for i in self.project_items() if i['id']==claims['clip']),None)
            if item is None:raise HTTPException(404,'Запись не найдена')
            if claims['hash']!=item['hash']:raise HTTPException(401,'Запись обновлена. Откройте её ещё раз.')
        else:
            user,item=await self.selected(claims['sub'],claims['scope'],claims['source'],claims['clip'])
            if claims.get('auth_version')!=user.get('auth_version',0) or claims['hash']!=item['hash']:
                raise HTTPException(401,'Запись обновлена. Откройте её ещё раз.')
        if self.state(item)['status']!='ready':raise HTTPException(404,'Запись пока недоступна')
        return self.folder(item['hash'])/'audio.m4a'
