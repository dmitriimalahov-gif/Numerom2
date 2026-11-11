"""Private course materials managed through explicit admin authorization."""
import hashlib,json,re,os,tempfile
from pathlib import Path
from datetime import datetime
from typing import Literal
from fastapi import HTTPException
from pydantic import Field,StrictStr,StrictBool
from pymongo.errors import DuplicateKeyError
from services.exercise_attachments import AttachmentUpload,validate_file
from services.mobile_admin import Change,MobileAdmin
from services.student_media import StudentMediaService
ROOT=Path(__file__).resolve().parents[1]/'private/lesson-materials'
Section=Literal['theory','exercises','quiz','challenge','analytics']
def store_file(root,stored,data,digest):
    root.mkdir(parents=True,exist_ok=True);path=root/stored
    if path.is_symlink() or path.resolve().parent!=root:raise HTTPException(404,'Файл недоступен')
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=root,prefix='.upload-',delete=False) as stream:
            temporary=Path(stream.name);stream.write(data);stream.flush();os.fsync(stream.fileno())
        try:os.link(temporary,path)
        except FileExistsError:
            if path.is_symlink() or path.stat().st_size!=len(data) or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
                raise HTTPException(409,'Сохранённый файл повреждён. Загрузите материал заново.')
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)
    return path
class MaterialUpload(AttachmentUpload):
    section:Section='theory'
    reason:StrictStr=Field(min_length=1,max_length=500)
class MaterialChange(Change):
    name:StrictStr=Field(min_length=1,max_length=180)
    section:Section
    is_active:StrictBool
class AdminMaterials:
    def __init__(self,db,root=ROOT):self.db=db;self.root=Path(root).resolve();self.admin=MobileAdmin(db)
    async def scope(self,uid,lesson):
        actor=await self.admin.authorize(uid)
        if not await self.db.lessons_v2.find_one({'id':lesson}):raise HTTPException(404,'Урок не найден')
        return actor
    @staticmethod
    def public(row):
        return {'id':row['id'],'name':row.get('original_name') or row.get('filename') or 'Материал','mime':row.get('mime_type'),'size':row.get('file_size'),
                'section':row.get('section') or 'theory','is_active':row.get('is_active') is not False,'revision':row.get('mobile_revision',0)}
    async def list(self,uid,lesson):
        await self.scope(uid,lesson);rows=await self.db.files.find({'lesson_id':lesson}).sort('uploaded_at',-1).limit(1000).to_list(1000)
        return {'files':[self.public(row) for row in rows]}
    async def upload(self,uid,lesson,request):
        await self.scope(uid,lesson)
        if not request.reason.strip():raise HTTPException(422,'Укажите причину загрузки')
        data,mime,name=validate_file(request)
        identity=hashlib.sha256(f'{uid}:{lesson}:{request.request_id}'.encode()).hexdigest()
        digest=hashlib.sha256(data).hexdigest();fingerprint=hashlib.sha256(json.dumps([digest,name,request.section,request.reason],ensure_ascii=False).encode()).hexdigest()
        previous=await self.db.files.find_one({'_id':identity})
        if previous:
            if previous.get('upload_fingerprint')!=fingerprint:raise HTTPException(409,'Запрос уже использован для другого материала')
            return {'file':self.public(previous)}
        stored=identity+'-'+digest+Path(name).suffix
        # Publish a complete inode only. Another worker must never observe a partial write.
        path=store_file(self.root,stored,data,digest)
        row={'_id':identity,'id':identity,'lesson_id':lesson,'original_name':name,'stored_name':stored,'private_material':True,'mime_type':mime,'file_size':len(data),
             'file_type':'document' if mime=='application/pdf' else 'media','section':request.section,'is_active':False,'mobile_revision':0,'upload_fingerprint':fingerprint,
             'uploaded_by':uid,'uploaded_at':datetime.utcnow(),'mobile_audit':[{'actor_id':uid,'reason':request.reason.strip(),'fields':['upload'],'at':datetime.utcnow()}]}
        try:await self.db.files.insert_one(row)
        except DuplicateKeyError:
            previous=await self.db.files.find_one({'_id':identity})
            if previous.get('upload_fingerprint')!=fingerprint:
                if previous.get('stored_name')!=stored:path.unlink(missing_ok=True)
                raise HTTPException(409,'Запрос уже использован для другого материала')
            row=previous
        return {'file':self.public(row)}
    async def change(self,uid,lesson,identity,body):
        actor=await self.scope(uid,lesson);row=await self.db.files.find_one({'id':identity,'lesson_id':lesson})
        if not row:raise HTTPException(404,'Материал не найден')
        extension=Path(str(row.get('original_name') or row.get('filename') or '')).suffix
        name=Path(body.name.replace('\\','/')).stem
        name=re.sub(r'[\x00-\x1f\x7f]','',name).strip()[:150]
        if not name:raise HTTPException(422,'Введите название материала')
        updated=await self.admin.mutate(self.db.files,identity,body,{'original_name':name+extension,'section':body.section,'is_active':body.is_active},actor,guard={'lesson_id':lesson})
        return {'file':self.public(updated)}
    async def access(self,uid,lesson,identity):
        await self.scope(uid,lesson)
        return await StudentMediaService(self.db,'uploads/learning_v2',private_root=self.root).access(uid,lesson,identity)
