from typing import Annotated, Literal
from fastapi import APIRouter, Depends, Path, Query
from auth import get_current_user
from services.admin_reports import AdminReports, ReportRetry


def create_admin_reports_router(db, service=None):
    router = APIRouter(prefix='/api/admin/mobile/reports', tags=['mobile-admin-reports'])
    service = service or AdminReports(db)

    @router.get('')
    async def reports(q: str = Query('', max_length=120), state: Literal['all','paid','pending','expired'] = 'all',
                      page: int = Query(1, ge=1, le=10000), page_size: int = Query(10, ge=1, le=20), user=Depends(get_current_user)):
        return await service.list(user['user_id'], q, state, page, page_size)

    @router.post('/{order_id}/retry')
    async def retry(order_id: Annotated[str, Path(pattern=r'^[a-f0-9]{64}$')], body: ReportRetry, user=Depends(get_current_user)):
        return await service.retry(user['user_id'], order_id, body)

    return router
