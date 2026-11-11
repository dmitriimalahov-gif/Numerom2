"""Administrative consultation previews are authenticated and directory confined."""
import mimetypes
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
from auth import get_current_user
from services.admin_management import AdminManagementService
from services.media_response import media_file_response

def create_admin_media_router(db, root='uploads/consultations'):
    router = APIRouter(prefix='/api/admin/consultations', tags=['admin-media'])
    directory = Path(root).resolve()
    service = AdminManagementService(db)

    @router.api_route('/files/{file_id}', methods=['GET', 'HEAD'])
    async def consultation_file(file_id: str, request: Request, current_user: dict = Depends(get_current_user)):
        await service.authorize(current_user['user_id'])
        item = await db.files.find_one({'id': file_id})
        if not item or item.get('lesson_id'):
            raise HTTPException(404, 'Файл консультации не найден')
        stored = item.get('stored_name', '')
        if not stored or Path(stored).name != stored or '\\' in stored or '\x00' in stored:
            raise HTTPException(404, 'Файл консультации недоступен')
        file = (directory / stored).resolve()
        if not file.is_relative_to(directory) or not file.is_file():
            raise HTTPException(404, 'Файл консультации недоступен')
        name = Path(str(item.get('original_name') or stored)).name.replace('\r','').replace('\n','')
        mime = mimetypes.guess_type(name)[0] or 'application/octet-stream'
        safe = mime == 'application/pdf' or mime.startswith(('video/','audio/'))
        return await media_file_response(request, file, name,
                                         mime if safe else 'application/octet-stream',
                                         'inline' if safe else 'attachment')
    return router
