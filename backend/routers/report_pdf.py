from fastapi import APIRouter, Depends, Request
from auth import get_current_user
from services.media_response import media_file_response
from services.report_pdf import ReportPdf, ReportPdfRequest


def create_report_pdf_router(db, service=None):
    router = APIRouter(prefix='/api', tags=['report-pdf'])
    service = service or ReportPdf(db)

    @router.post('/report-pdf')
    async def create(body: ReportPdfRequest, user=Depends(get_current_user)):
        return await service.create(user['user_id'], body)

    # The trailing file name only names the download; the token alone decides access.
    @router.api_route('/student/report-pdf/{token}', methods=['GET', 'HEAD'])
    @router.api_route('/student/report-pdf/{token}/{file}', methods=['GET', 'HEAD'])
    async def download(token: str, request: Request, file: str = ''):
        path, name = await service.resolve(token)
        return await media_file_response(request, path, name, 'application/pdf', 'inline')

    return router
