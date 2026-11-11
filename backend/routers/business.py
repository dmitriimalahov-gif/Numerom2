"""Authenticated routes for each owner's independent Business 250 package."""
from typing import Annotated

from fastapi import APIRouter, Depends, Path

from auth import get_current_user
from services.business import (
    ActivateRequest, BusinessService, EmployeeWrite, GroupWrite, ImportRequest,
    PreviewRequest, RevisionRequest,
)

Identifier = Annotated[str, Path(pattern=r'^[A-Za-z0-9_-]{1,128}$')]


def create_business_router(db):
    router = APIRouter(prefix='/api/business', tags=['business'])
    service = BusinessService(db)

    @router.get('')
    async def read(user=Depends(get_current_user)):
        return await service.read(user['user_id'])

    @router.post('/activate')
    async def activate(body: ActivateRequest, user=Depends(get_current_user)):
        return await service.activate(user['user_id'], body)

    @router.post('/import/preview')
    async def preview(body: PreviewRequest, user=Depends(get_current_user)):
        return await service.preview(user['user_id'], body)

    @router.post('/import')
    async def import_employees(body: ImportRequest, user=Depends(get_current_user)):
        return await service.import_employees(user['user_id'], body)

    @router.patch('/employees/{employee_id}')
    async def edit_employee(employee_id: Identifier, body: EmployeeWrite, user=Depends(get_current_user)):
        return await service.edit_employee(user['user_id'], employee_id, body)

    @router.post('/employees/{employee_id}/remove')
    async def remove_employee(employee_id: Identifier, body: RevisionRequest, user=Depends(get_current_user)):
        return await service.remove_employee(user['user_id'], employee_id, body)

    @router.post('/groups')
    async def save_group(body: GroupWrite, user=Depends(get_current_user)):
        return await service.save_group(user['user_id'], body)

    @router.post('/groups/{group_id}/remove')
    async def remove_group(group_id: Identifier, body: RevisionRequest, user=Depends(get_current_user)):
        return await service.remove_group(user['user_id'], group_id, body)

    @router.get('/groups/{group_id}/report')
    async def report(group_id: Identifier, user=Depends(get_current_user)):
        return await service.report(user['user_id'], group_id)

    @router.get('/template')
    async def template(user=Depends(get_current_user)):
        return await service.template(user['user_id'])

    return router
