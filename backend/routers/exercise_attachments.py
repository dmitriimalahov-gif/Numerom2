from typing import Annotated
from fastapi import APIRouter, Depends, Path, Request
from auth import get_current_user
from services.exercise_attachments import AttachmentUpload, ExerciseAttachments
from services.media_response import media_file_response
from services.student_learning import TheoryRead

Identifier = Annotated[str, Path(pattern=r'^[A-Za-z0-9_-]{1,128}$')]
FileID = Annotated[str, Path(pattern=r'^[a-f0-9]{64}$')]


def create_exercise_attachments_router(db, **options):
    router = APIRouter(prefix='/api/student', tags=['exercise-attachments'])
    service = ExerciseAttachments(db, **options)

    @router.get('/exercise-attachments/{lesson}/{exercise}')
    async def files(lesson: Identifier, exercise: Identifier, user=Depends(get_current_user)):
        return await service.list(user['user_id'], lesson, exercise)

    @router.post('/exercise-attachments/{lesson}/{exercise}')
    async def upload(lesson: Identifier, exercise: Identifier, body: AttachmentUpload, user=Depends(get_current_user)):
        return await service.upload(user['user_id'], lesson, exercise, body)

    @router.post('/exercise-attachments/{lesson}/{exercise}/{file_id}/remove')
    async def remove(lesson: Identifier, exercise: Identifier, file_id: FileID, body: TheoryRead, user=Depends(get_current_user)):
        return await service.remove(user['user_id'], lesson, exercise, file_id)

    @router.get('/exercise-attachment-access/{file_id}')
    async def access(file_id: FileID, user=Depends(get_current_user)):
        return await service.access(user['user_id'], file_id)

    @router.api_route('/exercise-attachment-media/{token}', methods=['GET', 'HEAD'])
    async def media(token: str, request: Request):
        path, item = await service.resolve(token)
        return await media_file_response(request, path, item['name'], item['mime'], 'attachment')

    return router
