import asyncio
from fastapi import HTTPException
from models import PlanetaryEnergyModifiersConfig
from domain.vedic_report import build_vedic_report,PRICES,TITLES
from services.paid_calculations import PaidCalculations
from services.student_learning import _student
from services.vedic_location import resolve_location

async def active_modifiers(db):
    """The author's active planetary modifiers over the model defaults, as every route tool uses them."""
    config=await db.planetary_energy_modifiers_config.find_one({'is_active':True})
    return {**PlanetaryEnergyModifiersConfig().model_dump(),**(config or {})}

def frozen_modifiers(modifiers):
    """Only the numeric settings, for a purchased report's snapshot: no ids, dates or the editor's address."""
    return {key:modifiers[key] for key in PlanetaryEnergyModifiersConfig.model_fields if key not in ('id','created_at','updated_at','updated_by','is_active')}

class VedicCalculations:
    def __init__(self,db):self.db=db
    def service(self,user=None):
        async def build(data):
            modifiers=await active_modifiers(self.db)
            # The profile name (wisdom and name numbers) belongs only to the owner's own birth date.
            own=bool(user) and bool(data.birth_date) and user.get('birth_date')==data.birth_date
            profile={key:user.get(key) for key in ('name','surname','full_name')} if own else None
            return await asyncio.to_thread(build_vedic_report,data,profile=profile,modifiers=modifiers)
        return PaidCalculations(self.db,namespace='vedic_requests',key_prefix='vedic:',report_key='vedic_report',prices=PRICES,build=build,
                                metadata=lambda data:(PRICES[data.kind],TITLES[data.kind],data.birth_date))
    async def catalog(self,uid):return await self.service().catalog(uid)
    async def location(self,uid,data):
        await _student(self.db,uid)
        try:return await asyncio.wait_for(asyncio.to_thread(resolve_location,data),timeout=10)
        except asyncio.TimeoutError:
            raise HTTPException(503,'Определение города заняло слишком много времени. Введите город вручную.') from None
    async def calculate(self,uid,data):return await self.service(await _student(self.db,uid)).calculate(uid,data)
    async def history(self,uid):
        result=await self.service().history(uid)
        # Five complete 90-day reports remain below the public gateway response cap.
        return {'calculations':result['calculations'][:5]}
