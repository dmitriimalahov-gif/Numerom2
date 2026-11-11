"""Idempotent personal reports using the same committed receipt as other tools."""
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel,ConfigDict,Field,StrictStr,field_validator
from fastapi import HTTPException
from services.paid_calculations import PaidCalculations
from services.student_learning import _student
from domain.personal_report import build_personal_report,full_name_number_for_report
from numerology import calculate_personal_numbers,reduce_to_single_digit

class PersonalRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    kind:Literal['personal']='personal'
    request_id:UUID
    expected_cost:int=Field(strict=True,ge=0,le=1000000)
    birth_date:StrictStr=Field(pattern=r'^\d{2}\.\d{2}\.\d{4}$')
    @field_validator('request_id')
    @classmethod
    def v4(cls,v):
        if v.version!=4:raise ValueError('request_id must be UUIDv4')
        return v
    @field_validator('birth_date')
    @classmethod
    def date(cls,v):
        d=datetime.strptime(v,'%d.%m.%Y')
        if d.year<1900 or d>datetime.utcnow():raise ValueError('Укажите существующую дату рождения')
        return v

def prepare_personal(data,user):
    result=calculate_personal_numbers(data.birth_date)
    name=full_name_number_for_report(user.get('name'),user.get('surname'))
    result['full_name_number']=name
    result['wisdom_number']=reduce_to_single_digit(result['destiny_number']+name) if name is not None else None
    result['report']=build_personal_report(data.birth_date,result,name=user.get('name'),surname=user.get('surname'),profile_birth_date=user.get('birth_date'))
    return {**result,'version':1,'legacy':result}

class PersonalCalculations:
    def __init__(self,db):self.db=db
    def service(self,user=None):
        return PaidCalculations(self.db,namespace='personal_requests',report_key='personal_detail',prices={'personal':'personal_numbers'},
            build=lambda data:prepare_personal(data,user),metadata=lambda data:('personal_numbers','Расчёт персональных чисел',data.birth_date),key_prefix='personal:')
    async def catalog(self,uid):return await self.service().catalog(uid)
    async def calculate(self,uid,data):return await self.service(await _student(self.db,uid)).calculate(uid,data)
