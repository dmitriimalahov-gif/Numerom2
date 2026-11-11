from fastapi import APIRouter, Depends
from auth import get_current_user
from domain.relationships import RelationshipRequest
from services.relationships import Relationships


def create_relationships_router(db):
    router = APIRouter(prefix='/api/numerology/relationships', tags=['relationships'])
    service = Relationships(db)

    @router.get('/catalog')
    async def catalog(user=Depends(get_current_user)):
        return await service.catalog(user['user_id'])

    @router.get('/history')
    async def history(user=Depends(get_current_user)):
        return await service.history(user['user_id'])

    @router.post('')
    async def calculate(data: RelationshipRequest, user=Depends(get_current_user)):
        return await service.calculate(user['user_id'], data)

    return router
