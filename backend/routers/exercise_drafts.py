from typing import Annotated
from fastapi import APIRouter, Depends, Path
from auth import get_current_user
from services.exercise_drafts import ExerciseDrafts, DraftWrite

Identifier = Annotated[str, Path(pattern=r'^[A-Za-z0-9_-]{1,128}$')]


def create_exercise_drafts_router(db):
    router = APIRouter(prefix='/api/student/exercise-drafts', tags=['exercise-drafts'])
    service = ExerciseDrafts(db)

    @router.get('/{lesson_id}/{exercise_id}')
    async def read(lesson_id: Identifier, exercise_id: Identifier, user=Depends(get_current_user)):
        return await service.read(user['user_id'], lesson_id, exercise_id)

    @router.post('/{lesson_id}/{exercise_id}')
    async def save(lesson_id: Identifier, exercise_id: Identifier, body: DraftWrite, user=Depends(get_current_user)):
        return await service.save(user['user_id'], lesson_id, exercise_id, body)

    return router
