from fastapi import APIRouter, Depends
from auth import get_current_user
from domain.number_tools import ToolRequest
from services.number_tools import NumberTools


def create_number_tools_router(db):
    router = APIRouter(prefix='/api/numerology/tools', tags=['number-tools'])
    service = NumberTools(db)

    @router.get('/catalog')
    async def catalog(user=Depends(get_current_user)):
        return await service.catalog(user['user_id'])

    @router.get('/history')
    async def history(user=Depends(get_current_user)):
        return await service.history(user['user_id'])

    @router.post('')
    async def calculate(data: ToolRequest, user=Depends(get_current_user)):
        return await service.calculate(user['user_id'], data)

    return router
