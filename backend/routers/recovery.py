import os
import re
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from auth import get_current_user
from services.mail import SMTPMailer
from services.recovery import RecoveryService, GENERIC_MESSAGE

class RecoveryRequest(BaseModel):
    email: str = Field(min_length=3,max_length=254)
    @field_validator('email')
    @classmethod
    def email_address(cls, value):
        value=value.strip()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value): raise ValueError('Введите адрес электронной почты')
        return value
class ResetRequest(BaseModel):
    token: str = Field(min_length=32,max_length=128,pattern=r'^[A-Za-z0-9_-]+$')
    password: str = Field(min_length=12,max_length=72)
    @field_validator('password')
    @classmethod
    def password_size(cls, value):
        if len(value.encode('utf-8'))>72: raise ValueError('Пароль слишком длинный: максимум 72 байта UTF-8')
        return value

def create_recovery_router(db, *, mailer=None, reset_url=None, clock=datetime.utcnow):
    router=APIRouter(prefix='/api',tags=['password recovery'])
    service=RecoveryService(db,mailer or SMTPMailer(),reset_url if reset_url is not None else os.environ.get('PASSWORD_RESET_URL',''),clock)
    @router.post('/auth/forgot-password',status_code=202)
    async def forgot(data:RecoveryRequest, request:Request, tasks:BackgroundTasks):
        if await service.reserve_request(data.email,request.client.host if request.client else 'unknown'):
            tasks.add_task(service.deliver,data.email)
        return {'message':GENERIC_MESSAGE}
    @router.post('/auth/reset-password')
    async def reset(data:ResetRequest,request:Request,tasks:BackgroundTasks):
        email=await service.reset(data.token,data.password,request.client.host if request.client else 'unknown')
        tasks.add_task(service.notify_changed,email)
        return {'message':'Пароль изменён. Войдите с новым паролем.'}
    @router.get('/admin/manage/recovery-status')
    async def status(current_user=Depends(get_current_user)):
        actor=await db.users.find_one({'id':current_user['user_id']})
        if not actor or actor.get('is_disabled') or not (actor.get('is_admin') or actor.get('is_super_admin')): raise HTTPException(403,'Недостаточно прав')
        return {'configured':service.configured}
    return router
