"""Server-owned prices in minor currency units; no recurring charges."""
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator

PACKAGES = {
    'one_time': {'title':'Стартовый пакет','amount_total':99,'credits':10,'access_days':30},
    'monthly': {'title':'Месяц практики','amount_total':999,'credits':150,'access_days':30},
    'annual': {'title':'Год практики','amount_total':6660,'credits':1000,'access_days':365},
    'master_consultation': {'title':'Консультация мастера','amount_total':66600,'credits':10000,'access_days':0,'consultation':True},
}

class CheckoutRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    package_type: Literal['one_time','monthly','annual','master_consultation']
    request_id: UUID
    client: Literal['mobile','web'] = 'mobile'

    @field_validator('request_id')
    @classmethod
    def uuid4(cls, value):
        if value.version != 4: raise ValueError('UUIDv4 required')
        return value

def packages():
    return [{'id':key, 'consultation':False, **value, 'currency':'eur', 'recurring':False} for key,value in PACKAGES.items()]
