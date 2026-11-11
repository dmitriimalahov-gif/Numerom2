from fastapi import APIRouter, Depends, Request, HTTPException
from auth import get_current_user
from domain.payments import CheckoutRequest
from services.payments import Payments
from services.student_learning import TheoryRead

def create_payments_router(db,service=None):
    router=APIRouter(prefix='/api',tags=['payments']);payments=service or Payments(db)
    @router.get('/payments/packages')
    async def catalog(user=Depends(get_current_user)):
        return await payments.catalog(user['user_id'])
    @router.post('/payments/checkout/session')
    async def checkout(body:CheckoutRequest,user=Depends(get_current_user)):
        return await payments.create(user['user_id'],body)
    @router.get('/payments/checkout/status/{session_id}')
    async def status(session_id:str,user=Depends(get_current_user)):
        return await payments.status(user['user_id'],session_id)
    @router.get('/payments/history')
    async def history(user=Depends(get_current_user)):
        return await payments.history(user['user_id'])
    @router.post('/payments/checkout/{session_id}/cancel')
    async def cancel(session_id:str,body:TheoryRead,user=Depends(get_current_user)):
        return await payments.cancel(user['user_id'],session_id)
    @router.post('/webhook/stripe')
    async def webhook(request:Request):
        body=bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body)>256*1024:raise HTTPException(413,'Слишком большой запрос')
        signatures=request.headers.getlist('stripe-signature')
        if len(signatures)!=1:raise HTTPException(400,'Отсутствует подпись Stripe')
        return await payments.webhook(bytes(body),signatures[0])
    return router
