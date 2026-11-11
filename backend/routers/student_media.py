from fastapi import APIRouter, Depends, Request
from auth import get_current_user
from services.media_response import media_file_response
from services.student_media import StudentMediaService

def create_student_media_router(db, root='uploads/learning_v2'):
    router = APIRouter(prefix='/api/student', tags=['student-media'])
    service = StudentMediaService(db, root)

    @router.get('/lesson-video/{lesson_id}/access')
    async def video(lesson_id: str, current_user: dict = Depends(get_current_user)):
        return await service.video(current_user['user_id'], lesson_id)

    @router.get('/lesson-files/{lesson_id}/{file_id}/access')
    async def access(lesson_id: str, file_id: str, current_user: dict = Depends(get_current_user)):
        return await service.access(current_user['user_id'], lesson_id, file_id)

    @router.api_route('/media/{token}', methods=['GET','HEAD'])
    async def media(token: str, request: Request):
        path, name, kind, disposition = await service.resolve(token)
        return await media_file_response(request, path, name, kind, disposition)

    return router
