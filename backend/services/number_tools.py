"""Paid name/address/vehicle calculations, with legacy website response adapters."""
import uuid
from fastapi import HTTPException
from pydantic import ValidationError
from domain.number_tools import ToolRequest, build_tools, TITLES, FIELDS
from services.paid_calculations import PaidCalculations


class NumberTools(PaidCalculations):
    def __init__(self, db):
        super().__init__(db, namespace='tool_requests', key_prefix='tools:', report_key='tool_report',
            prices={kind: kind + '_numerology' for kind in TITLES}, build=build_tools,
            metadata=lambda data: (data.kind + '_numerology', TITLES[data.kind], ''))

    async def legacy(self, uid, kind, raw):
        price = raw.get('expected_cost')
        if price is None:
            price = (await self.catalog(uid))[kind]
        if price is None:
            raise HTTPException(503, 'Стоимость расчёта временно недоступна')
        try:
            data = ToolRequest.model_validate({'kind': kind, 'request_id': raw.get('request_id') or str(uuid.uuid4()),
                'expected_cost': price, 'inputs': {key: raw[key] for key in FIELDS[kind] if raw.get(key) is not None}})
        except ValidationError as error:
            raise HTTPException(422, str(error.errors()[0]['msg']).removeprefix('Value error, '))
        return (await self.calculate(uid, data))['results']['legacy']
