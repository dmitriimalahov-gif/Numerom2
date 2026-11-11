from fastapi import APIRouter,Depends,Request
import json
from pydantic import BaseModel,ConfigDict,Field,StrictStr,field_validator
from auth import get_current_user
from services.passkeys import Passkeys
class Empty(BaseModel):
    model_config=ConfigDict(extra='forbid')
class RegisterBegin(Empty):
    password:StrictStr=Field(min_length=1,max_length=200)
class Finish(Empty):
    challenge_id:StrictStr=Field(pattern=r'^[A-Za-z0-9_-]{43}$')
    credential:dict
    @field_validator('credential')
    @classmethod
    def bounded_proof(cls,value):
        if len(json.dumps(value))>100000:raise ValueError('Credential is too large')
        return value
class RegisterFinish(Finish):
    label:StrictStr=Field(min_length=1,max_length=80)
class Remove(Empty):
    id:StrictStr=Field(pattern=r'^[A-Za-z0-9_-]{1,2048}$')
def create_passkeys_router(db,**options):
    router=APIRouter(prefix='/api',tags=['passkeys']);service=Passkeys(db,**options)
    @router.post('/auth/passkeys/options')
    async def options(request:Request,body:Empty):return await service.begin(request.headers.get('origin'))
    @router.post('/auth/passkeys/verify')
    async def verify(request:Request,body:Finish):return await service.finish(request.headers.get('origin'),body.challenge_id,body.credential)
    @router.get('/user/passkeys')
    async def keys(user=Depends(get_current_user)):return await service.list(user['user_id'])
    @router.post('/user/passkeys/options')
    async def register_options(request:Request,body:RegisterBegin,user=Depends(get_current_user)):
        return await service.begin(request.headers.get('origin'),user['user_id'],body.password)
    @router.post('/user/passkeys/verify')
    async def register_verify(request:Request,body:RegisterFinish,user=Depends(get_current_user)):
        return await service.finish(request.headers.get('origin'),body.challenge_id,body.credential,user['user_id'],body.label)
    @router.post('/user/passkeys/remove')
    async def remove(body:Remove,user=Depends(get_current_user)):return await service.remove(user['user_id'],body.id)
    return router
