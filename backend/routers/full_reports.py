from fastapi import APIRouter, Depends

from auth import get_current_user
from domain.full_report_purchase import FullReportCheckout, FullReportPreview, FullReportProfileExtension
from services.full_reports import FullReports
from services.narration import NarrationService
from services.student_learning import TheoryRead


def create_full_reports_router(db, service=None, narration=None, video=None):
    router = APIRouter(prefix='/api/full-reports', tags=['full-reports'])
    reports = service or FullReports(db)
    voice = narration or NarrationService(db)
    from services.report_video import ReportVideo
    movies = video or ReportVideo(db, reports=reports)

    @router.get('/catalog')
    async def catalog(user=Depends(get_current_user)):
        return await reports.catalog(user['user_id'])

    @router.post('/preview')
    async def preview(body: FullReportPreview, user=Depends(get_current_user)):
        return await reports.preview(user['user_id'], body)

    @router.post('/checkout')
    async def checkout(body: FullReportCheckout, user=Depends(get_current_user)):
        return await reports.create(user['user_id'], body)

    @router.get('/history')
    async def history(user=Depends(get_current_user)):
        return await reports.history(user['user_id'])

    @router.delete('/{order_id}')
    async def delete(order_id: str, user=Depends(get_current_user)):
        return await reports.delete(user['user_id'], order_id)

    @router.get('/{order_id}')
    async def status(order_id: str, user=Depends(get_current_user)):
        return await reports.status(user['user_id'], order_id)

    @router.post('/{order_id}/extend-profile')
    async def extend_profile(order_id: str, body: FullReportProfileExtension, user=Depends(get_current_user)):
        return await reports.extend_profile(user['user_id'], order_id, body)

    @router.get('/{order_id}/revisions/{revision}')
    async def revision(order_id: str, revision: int, user=Depends(get_current_user)):
        return await reports.revision(user['user_id'], order_id, revision)

    @router.post('/{order_id}/cancel')
    async def cancel(order_id: str, body: TheoryRead, user=Depends(get_current_user)):
        return await reports.cancel(user['user_id'], order_id)

    @router.get('/{order_id}/narration')
    async def clips(order_id: str, user=Depends(get_current_user)):
        return await voice.catalog(user['user_id'], 'full-report', order_id)

    @router.post('/{order_id}/narration/{clip_id}/access')
    async def access(order_id: str, clip_id: str, body: TheoryRead, user=Depends(get_current_user)):
        return await voice.access(user['user_id'], 'full-report', order_id, clip_id)

    @router.get('/{order_id}/video')
    async def movie(order_id: str, user=Depends(get_current_user)):
        return await movies.status(user['user_id'], order_id)

    @router.post('/{order_id}/video')
    async def movie_retry(order_id: str, body: TheoryRead, user=Depends(get_current_user)):
        return await movies.status(user['user_id'], order_id, retry=True)

    return router
