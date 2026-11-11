from fastapi import APIRouter,Depends,Request
from auth import get_current_user
from services.consultations import Consultations,ConsultationPurchase
from services.media_response import media_file_response

def create_consultations_router(db,service=None):
    router=APIRouter(prefix='/api/student',tags=['consultations']);service=service or Consultations(db)
    @router.get('/consultations')
    async def listing(user=Depends(get_current_user)):
        return await service.listing(user['user_id'])
    @router.post('/consultations/{consultation_id}/purchase')
    async def purchase(consultation_id:str,body:ConsultationPurchase,user=Depends(get_current_user)):
        return await service.purchase(user['user_id'],consultation_id,body.expected_cost)
    @router.get('/consultations/{consultation_id}/{kind}/access')
    async def access(consultation_id:str,kind:str,user=Depends(get_current_user)):
        return await service.access(user['user_id'],consultation_id,kind)
    @router.api_route('/consultation-media/{token}',methods=['GET','HEAD'])
    async def media(token:str,request:Request):
        return await media_file_response(request,*(await service.resolve(token)))
    return router
