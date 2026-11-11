"""Administrative account operations, using the active application's database."""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, field_validator

from auth import get_current_user
from services.admin_management import AdminManagementService, MAX_CREDITS


class AdminChange(BaseModel):
    model_config = ConfigDict(extra='forbid')
    reason: str = Field(min_length=1, max_length=500)

    @field_validator('reason')
    @classmethod
    def require_reason(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('A reason is required')
        return value


class AccessChange(AdminChange):
    is_admin: StrictBool | None = None
    is_disabled: StrictBool | None = None

    @field_validator('is_admin', 'is_disabled', mode='before')
    @classmethod
    def reject_explicit_null(cls, value):
        if value is None:
            raise ValueError('Access flags cannot be null')
        return value


class CreditChange(AdminChange):
    amount: StrictInt = Field(ge=-MAX_CREDITS, le=MAX_CREDITS)
    expected_balance: StrictInt = Field(ge=0, le=MAX_CREDITS)

    @field_validator('amount')
    @classmethod
    def require_nonzero_delta(cls, value):
        if value == 0:
            raise ValueError('Credit adjustment cannot be zero')
        return value


def create_admin_management_router(db):
    router = APIRouter(prefix='/api/admin/manage', tags=['admin-management'])
    service = AdminManagementService(db)

    async def current_admin(current_user: dict = Depends(get_current_user)):
        return await service.authorize(current_user.get('user_id'))

    @router.get('/overview')
    async def overview(actor: dict = Depends(current_admin)):
        return await service.overview()

    @router.get('/users')
    async def list_users(q: str = Query('', max_length=200),
                         page: int = Query(1, ge=1, le=100000),
                         page_size: int = Query(20, ge=1, le=100),
                         actor: dict = Depends(current_admin)):
        return await service.list_users(q, page, page_size)

    @router.get('/users/{user_id}')
    async def user_detail(user_id: str, actor: dict = Depends(current_admin)):
        return await service.user_detail(user_id)

    @router.patch('/users/{user_id}/access')
    async def change_access(user_id: str, data: AccessChange,
                            actor: dict = Depends(current_admin)):
        return await service.change_access(actor, user_id, data)

    @router.patch('/users/{user_id}/credits')
    async def change_credits(user_id: str, data: CreditChange,
                             actor: dict = Depends(current_admin)):
        return await service.change_credits(actor, user_id, data)

    return router
