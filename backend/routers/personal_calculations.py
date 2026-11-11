from fastapi import APIRouter,Depends
from auth import get_current_user
from services.personal_calculations import PersonalCalculations,PersonalRequest
def create_personal_calculations_router(db):
    service=PersonalCalculations(db);router=APIRouter(prefix='/api/numerology/personal',tags=['personal-calculations'])
    @router.get('/catalog')
    async def catalog(user=Depends(get_current_user)):return await service.catalog(user['user_id'])
    @router.post('')
    async def calculate(body:PersonalRequest,user=Depends(get_current_user)):return await service.calculate(user['user_id'],body)
    return router
