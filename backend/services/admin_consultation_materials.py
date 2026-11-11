"""Draft PDFs scoped to one consultation; publishing is a separate versioned edit."""
import hashlib,json
from pathlib import Path
from datetime import datetime
from fastapi import HTTPException
from pydantic import Field,StrictStr
from pymongo.errors import DuplicateKeyError
from services.exercise_attachments import AttachmentUpload,validate_file
from services.admin_materials import store_file
from services.mobile_admin import MobileAdmin
from services.consultations import Consultations
ROOT=Path(__file__).resolve().parents[1]/'private/consultation-materials'
class ConsultationMaterialUpload(AttachmentUpload):
    reason:StrictStr=Field(min_length=1,max_length=500)
class AdminConsultationMaterials:
    def __init__(self,db,root=ROOT):self.db=db;self.root=Path(root).resolve();self.admin=MobileAdmin(db)
    async def scope(self,uid,cid):
        await self.admin.authorize(uid)
        row=await self.db.personal_consultations.find_one({'id':cid})
        if not row:raise HTTPException(404,'Консультация не найдена')
        return row
    @staticmethod
    def public(row):return {'id':row['id'],'name':row['original_name'],'mime':row['mime_type'],'size':row['file_size']}
    async def list(self,uid,cid):
        consultation=await self.scope(uid,cid)
        rows=await self.db.files.find({'consultation_id':cid,'private_consultation':True}).sort('uploaded_at',-1).limit(1000).to_list(1000)
        return {'files':[self.public(row) for row in rows],'selected_file_id':consultation.get('pdf_file_id')}
    async def upload(self,uid,cid,request):
        await self.scope(uid,cid)
        if not request.reason.strip():raise HTTPException(422,'Укажите причину загрузки')
        data,mime,name=validate_file(request)
        if mime!='application/pdf':raise HTTPException(422,'К консультации можно прикрепить PDF размером до 5 МБ')
        identity=hashlib.sha256(f'consultation:{uid}:{cid}:{request.request_id}'.encode()).hexdigest()
        digest=hashlib.sha256(data).hexdigest();fingerprint=hashlib.sha256(json.dumps([digest,name,request.reason],ensure_ascii=False).encode()).hexdigest()
        previous=await self.db.files.find_one({'_id':identity})
        if previous:
            if previous.get('upload_fingerprint')!=fingerprint:raise HTTPException(409,'Запрос уже использован для другого PDF')
            return {'file':self.public(previous)}
        stored=identity+'-'+digest+'.pdf';path=store_file(self.root,stored,data,digest)
        row={'_id':identity,'id':identity,'consultation_id':cid,'original_name':name,'stored_name':stored,'private_consultation':True,'mime_type':mime,'file_size':len(data),
             'file_type':'document','upload_fingerprint':fingerprint,'uploaded_by':uid,'uploaded_at':datetime.utcnow(),'upload_reason':request.reason.strip()}
        try:await self.db.files.insert_one(row)
        except DuplicateKeyError:
            previous=await self.db.files.find_one({'_id':identity})
            if previous.get('upload_fingerprint')!=fingerprint:
                if previous.get('stored_name')!=stored:path.unlink(missing_ok=True)
                raise HTTPException(409,'Запрос уже использован для другого PDF')
            row=previous
        return {'file':self.public(row)}
    async def access(self,uid,cid,fid):
        await self.scope(uid,cid)
        return await Consultations(self.db,private_root=self.root).admin_access(uid,cid,fid)
