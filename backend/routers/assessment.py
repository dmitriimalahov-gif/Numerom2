from fastapi import APIRouter, Depends
from auth import get_current_user
from domain.assessment import AssessmentRequest
from services.assessment import Assessment


def create_assessment_router(db):
    router = APIRouter(prefix='/api/numerology/assessment', tags=['assessment'])
    service = Assessment(db)

    @router.get('/catalog')
    async def catalog(user=Depends(get_current_user)):
        return await service.catalog(user['user_id'])

    @router.get('/history')
    async def history(user=Depends(get_current_user)):
        return await service.history(user['user_id'])

    @router.post('')
    async def calculate(body: AssessmentRequest, user=Depends(get_current_user)):
        return await service.calculate(user['user_id'], body)

    return router
