from fastapi import APIRouter,Depends,HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from auth import get_current_user
from domain.vedic_report import VedicRequest
from domain.vedic_location import LocationInput
from services.vedic_calculations import VedicCalculations

class _VedicRoute(APIRoute):
    def get_route_handler(self):
        original=super().get_route_handler()
        async def validated(request):
            try:return await original(request)
            except RequestValidationError:
                # Do not echo coordinates. Non-JSON NaN/Infinity inputs must also
                # return 422 rather than break JSON error serialization.
                raise HTTPException(422,'Проверьте параметры расчёта или координаты места.') from None
        return validated

def create_vedic_calculations_router(db):
    service=VedicCalculations(db);router=APIRouter(prefix='/api/numerology/vedic',tags=['vedic-calculations'],route_class=_VedicRoute)
    @router.get('/catalog')
    async def catalog(user=Depends(get_current_user)):return await service.catalog(user['user_id'])
    @router.get('/history')
    async def history(user=Depends(get_current_user)):return await service.history(user['user_id'])
    @router.post('/location')
    async def location(data:LocationInput,user=Depends(get_current_user)):
        return JSONResponse(await service.location(user['user_id'],data),headers={'Cache-Control':'no-store'})
    @router.post('')
    async def calculate(data:VedicRequest,user=Depends(get_current_user)):return await service.calculate(user['user_id'],data)
    return router
