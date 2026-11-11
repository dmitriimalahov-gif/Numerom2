from typing import Annotated
from fastapi import APIRouter,Depends,Path,Query
from auth import get_current_user
from services.admin_materials import AdminMaterials,MaterialUpload,MaterialChange
from services.admin_consultation_materials import AdminConsultationMaterials,ConsultationMaterialUpload
from services.mobile_admin import MobileAdmin,LessonChange,ConsultationChange,ReviewChange,SettingsChange,LevelChange,ImportPreview,LessonImport,ArchiveChange
Id=Annotated[str,Path(pattern=r'^[A-Za-z0-9_-]{1,128}$')]
def create_mobile_admin_router(db,materials_root=None,consultation_materials_root=None):
    router=APIRouter(prefix='/api/admin/mobile',tags=['mobile-admin']);service=MobileAdmin(db);materials=AdminMaterials(db,materials_root) if materials_root else AdminMaterials(db)
    consultation_materials=AdminConsultationMaterials(db,consultation_materials_root) if consultation_materials_root else AdminConsultationMaterials(db)
    @router.post('/lessons/import/preview')
    async def preview_import(body:ImportPreview,user=Depends(get_current_user)):return await service.preview_import(user['user_id'],body)
    @router.post('/lessons/import')
    async def import_lesson(body:LessonImport,user=Depends(get_current_user)):return await service.import_lesson(user['user_id'],body)
    @router.get('/lessons')
    async def lessons(page:int=Query(1,ge=1,le=10000),page_size:int=Query(25,ge=1,le=100),q:str=Query('',max_length=100),archived:str=Query('all',pattern='^(all|active|archived)$'),user=Depends(get_current_user)):
        return await service.lessons(user['user_id'],page=page,page_size=page_size,q=q,archived=archived)
    @router.post('/lessons/{identity}/archive')
    async def archive_lesson(identity:Id,body:ArchiveChange,user=Depends(get_current_user)):return await service.archive(user['user_id'],'lessons',identity,body)
    @router.post('/lessons/{identity}')
    async def lesson(identity:Id,body:LessonChange,user=Depends(get_current_user)):return await service.lesson(user['user_id'],identity,body)
    @router.get('/consultations')
    async def consultations(page:int=Query(1,ge=1,le=10000),page_size:int=Query(25,ge=1,le=100),q:str=Query('',max_length=100),archived:str=Query('all',pattern='^(all|active|archived)$'),user=Depends(get_current_user)):
        return await service.consultations(user['user_id'],page=page,page_size=page_size,q=q,archived=archived)
    @router.post('/consultations/{identity}/archive')
    async def archive_consultation(identity:Id,body:ArchiveChange,user=Depends(get_current_user)):return await service.archive(user['user_id'],'consultations',identity,body)
    @router.post('/consultations/{identity}')
    async def consultation(identity:Id,body:ConsultationChange,user=Depends(get_current_user)):return await service.consultation(user['user_id'],identity,body)
    @router.get('/responses')
    async def responses(page:int=Query(1,ge=1,le=10000),page_size:int=Query(25,ge=1,le=100),q:str=Query('',max_length=100),reviewed:str=Query('all',pattern='^(all|pending|reviewed)$'),lesson_id:str=Query('',max_length=128),user_id:str=Query('',max_length=128),user=Depends(get_current_user)):
        return await service.responses(user['user_id'],page=page,page_size=page_size,q=q,reviewed=reviewed,lesson_id=lesson_id,user_id=user_id)
    @router.get('/analytics')
    async def analytics(user=Depends(get_current_user)):return await service.analytics(user['user_id'])
    @router.get('/challenge-notes')
    async def challenge_notes(page:int=Query(1,ge=1,le=10000),page_size:int=Query(25,ge=1,le=100),q:str=Query('',max_length=100),lesson_id:str=Query('',max_length=128),user_id:str=Query('',max_length=128),user=Depends(get_current_user)):
        return await service.challenge_notes(user['user_id'],page=page,page_size=page_size,q=q,lesson_id=lesson_id,user_id=user_id)
    @router.post('/responses/{identity}')
    async def review(identity:Id,body:ReviewChange,user=Depends(get_current_user)):return await service.review(user['user_id'],identity,body)
    @router.get('/settings/{kind}')
    async def settings(kind:Id,user=Depends(get_current_user)):return await service.read_settings(user['user_id'],kind)
    @router.post('/settings/{kind}')
    async def save_settings(kind:Id,body:SettingsChange,user=Depends(get_current_user)):return await service.write_settings(user['user_id'],kind,body)
    @router.post('/users/{identity}/level')
    async def level(identity:Id,body:LevelChange,user=Depends(get_current_user)):return await service.level(user['user_id'],identity,body)
    @router.get('/lessons/{identity}/materials')
    async def material_list(identity:Id,user=Depends(get_current_user)):return await materials.list(user['user_id'],identity)
    @router.post('/lessons/{identity}/materials')
    async def material_upload(identity:Id,body:MaterialUpload,user=Depends(get_current_user)):return await materials.upload(user['user_id'],identity,body)
    @router.post('/lessons/{identity}/materials/{file_id}')
    async def material_change(identity:Id,file_id:Id,body:MaterialChange,user=Depends(get_current_user)):return await materials.change(user['user_id'],identity,file_id,body)
    @router.get('/lessons/{identity}/materials/{file_id}/access')
    async def material_access(identity:Id,file_id:Id,user=Depends(get_current_user)):return await materials.access(user['user_id'],identity,file_id)
    @router.get('/consultations/{identity}/materials')
    async def consultation_material_list(identity:Id,user=Depends(get_current_user)):return await consultation_materials.list(user['user_id'],identity)
    @router.post('/consultations/{identity}/materials')
    async def consultation_material_upload(identity:Id,body:ConsultationMaterialUpload,user=Depends(get_current_user)):return await consultation_materials.upload(user['user_id'],identity,body)
    @router.get('/consultations/{identity}/materials/{file_id}/access')
    async def consultation_material_access(identity:Id,file_id:Id,user=Depends(get_current_user)):return await consultation_materials.access(user['user_id'],identity,file_id)
    return router
