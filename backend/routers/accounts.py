"""Account HTTP boundary. Constructed with the active application's repository."""
from fastapi import APIRouter, Depends
from auth import get_current_user
from models import LoginRequest, TokenResponse, UserProfileUpdate
from services.accounts import AccountService


def create_accounts_router(db):
    router = APIRouter(prefix='/api', tags=['accounts'])
    service = AccountService(db)

    @router.post('/auth/login', response_model=TokenResponse)
    async def login(data: LoginRequest):
        return await service.login(data)

    @router.get('/user/profile-v2')
    async def profile(current_user: dict = Depends(get_current_user)):
        return await service.profile(current_user.get('user_id'))

    @router.patch('/user/profile-v2')
    async def update_profile(data: UserProfileUpdate, current_user: dict = Depends(get_current_user)):
        return await service.update_profile(current_user.get('user_id'), data)

    return router
