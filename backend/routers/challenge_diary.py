from fastapi import APIRouter,Depends
from auth import get_current_user
from services.challenge_diary import ChallengeDiary,DiaryWrite,DiaryRestart


def create_challenge_diary_router(db):
    router=APIRouter(prefix='/api/student/diary',tags=['challenge-diary']);service=ChallengeDiary(db)
    @router.get('/{lesson_id}/{challenge_id}')
    async def read(lesson_id:str,challenge_id:str,user=Depends(get_current_user)):
        return await service.read(user['user_id'],lesson_id,challenge_id)
    @router.post('/{lesson_id}/{challenge_id}')
    async def save(lesson_id:str,challenge_id:str,data:DiaryWrite,user=Depends(get_current_user)):
        return await service.save(user['user_id'],lesson_id,challenge_id,data)
    @router.post('/{lesson_id}/{challenge_id}/restart')
    async def restart(lesson_id:str,challenge_id:str,data:DiaryRestart,user=Depends(get_current_user)):
        return await service.save(user['user_id'],lesson_id,challenge_id,data,restart=True)
    return router
