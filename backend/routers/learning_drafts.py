from typing import Annotated
from uuid import UUID
from fastapi import APIRouter,Depends,Path
from auth import get_current_user
from services.learning_drafts import LearningDrafts,QuizDraftWrite,DiaryDraftWrite
Identifier=Annotated[str,Path(pattern=r'^[A-Za-z0-9_-]{1,128}$')]
Day=Annotated[int,Path(ge=1,le=90)]


def create_learning_drafts_router(db):
    router=APIRouter(prefix='/api/student',tags=['learning-drafts']);service=LearningDrafts(db)
    @router.get('/quiz-drafts/{lesson_id}/{quiz_id}')
    async def quiz_read(lesson_id:Identifier,quiz_id:Identifier,user=Depends(get_current_user)):
        return await service.quiz(user['user_id'],lesson_id,quiz_id)
    @router.post('/quiz-drafts/{lesson_id}/{quiz_id}')
    async def quiz_save(lesson_id:Identifier,quiz_id:Identifier,body:QuizDraftWrite,user=Depends(get_current_user)):
        return await service.quiz(user['user_id'],lesson_id,quiz_id,body)
    @router.get('/diary-drafts/{lesson_id}/{challenge_id}/{attempt_id}/{day}')
    async def diary_read(lesson_id:Identifier,challenge_id:Identifier,attempt_id:UUID,day:Day,user=Depends(get_current_user)):
        return await service.diary(user['user_id'],lesson_id,challenge_id,attempt_id,day)
    @router.post('/diary-drafts/{lesson_id}/{challenge_id}/{attempt_id}/{day}')
    async def diary_save(lesson_id:Identifier,challenge_id:Identifier,attempt_id:UUID,day:Day,body:DiaryDraftWrite,user=Depends(get_current_user)):
        return await service.diary(user['user_id'],lesson_id,challenge_id,attempt_id,day,body)
    return router
