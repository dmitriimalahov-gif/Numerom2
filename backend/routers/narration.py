from fastapi import APIRouter,Depends,Request
from auth import get_current_user
from services.narration import NarrationService
from services.media_response import media_file_response
from services.student_learning import TheoryRead

def create_narration_router(db):
    router=APIRouter(prefix='/api',tags=['narration']);service=NarrationService(db)
    @router.get('/public/narration/project')
    async def public_project():
        return service.public_catalog()
    @router.get('/narration/project')
    async def project(user=Depends(get_current_user)):
        return await service.catalog(user['user_id'],'project','project')
    @router.post('/narration/project/{clip_id}/access')
    async def project_access(clip_id:str,body:TheoryRead,user=Depends(get_current_user)):
        return await service.access(user['user_id'],'project','project',clip_id)
    @router.get('/narration/lesson/{lesson_id}')
    async def lesson(lesson_id:str,user=Depends(get_current_user)):
        return await service.catalog(user['user_id'],'lesson',lesson_id)
    @router.post('/narration/lesson/{lesson_id}/{clip_id}/access')
    async def lesson_access(lesson_id:str,clip_id:str,body:TheoryRead,user=Depends(get_current_user)):
        return await service.access(user['user_id'],'lesson',lesson_id,clip_id)
    @router.api_route('/student/narration-media/{token}',methods=['GET','HEAD'])
    async def media(token:str,request:Request):
        path=await service.resolve(token)
        return await media_file_response(request,path,'numerom-audio.m4a','audio/mp4','inline')
    @router.api_route('/student/report-video/{token}',methods=['GET','HEAD'])
    async def report_video(token:str,request:Request):
        from services.report_video import ReportVideo
        path,disposition=await ReportVideo(db).resolve(token)
        return await media_file_response(request,path,'NumerOM-video-report.mp4','video/mp4',disposition)
    return router
