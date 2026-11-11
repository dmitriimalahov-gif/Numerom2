import asyncio
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from auth import get_current_user
from domain.number_tools import ToolRequest, build_tools, THEMES
from numerology import calculate_name_numerology, calculate_address_numerology, calculate_car_number_numerology
from public_gateway import create_public_gateway
from routers.number_tools import create_number_tools_router
from services.number_tools import NumberTools


def payload(kind='name', inputs=None, **changes):
    return {'kind':kind,'inputs':inputs or {'name':'Анна','surname':'Иванова'},'expected_cost':1,'request_id':str(uuid.uuid4()),**changes}


class DomainTests(unittest.TestCase):
    def test_existing_formula_and_every_arithmetic_step(self):
        examples=[('name',{'name':'Анна','surname':'Иванова'},calculate_name_numerology('Анна Иванова')),
                  ('name',{'name':'Ё'},calculate_name_numerology('Ё')),
                  ('name',{'name':'А'*11},calculate_name_numerology('А'*11)),
                  ('name',{'name':"Jean-Luc",'surname':"O’Neil"},calculate_name_numerology('Jean-Luc O’Neil')),
                  ('car',{'car_number':'ABC 123'},calculate_car_number_numerology('ABC 123')),
                  ('address',{'street':'Пушкина','house_number':'14А','apartment_number':'22','postal_code':'2009'},calculate_address_numerology('Пушкина','14А','22','2009'))]
        for kind,inputs,legacy in examples:
            result=build_tools(ToolRequest.model_validate(payload(kind,inputs)))
            self.assertEqual(result['legacy'],legacy)
            for part in result['items']:
                self.assertEqual(part['total'],sum(t['value'] for t in part['tokens']))
                for step in part['steps']:
                    left,right=step.split(' = ')
                    self.assertEqual(sum(map(int,left.split(' + '))),int(right))
                self.assertEqual(part['narration_id'],f'tool-{kind}-{part["number"]}')
        report=build_tools(ToolRequest.model_validate(payload('address',{'house_number':'14А','postal_code':'2009'})))
        self.assertEqual([part['number'] for part in report['items']],[5,11])

    def test_invalid_input_never_reaches_a_calculation(self):
        for kind,inputs in [('name',{'name':'123'}),('name',{'name':'Ștefan'}),('name',{'name':'А','surname':'---'}),
          ('name',{'name':'А','role':'admin'}),('name',{'name':True}),('name',{'name':'а'*121}),
          ('car',{'car_number':'000'}),('car',{'car_number':'X'*14}),('car',{'car_number':'²'}),
          ('address',{'house_number':'А'}),('address',{'house_number':'1','apartment_number':'000'}),
          ('address',{'house_number':'1','postal_code':'²'})]:
            with self.subTest(kind=kind,inputs=inputs),self.assertRaises(ValidationError):ToolRequest.model_validate(payload(kind,inputs))
        for change in [{'expected_cost':True},{'expected_cost':'1'},{'expected_cost':-1},{'request_id':'fake'},{'user_id':'other'}]:
            with self.assertRaises(ValidationError):ToolRequest.model_validate(payload(**change))

    def test_each_result_has_matching_contextual_narration(self):
        root=Path(__file__).resolve().parents[2]
        spec=importlib.util.spec_from_file_location('tool_narration',root/'scripts/prepare-tool-narration.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        source=json.loads((root/'packages/project-knowledge/ru.json').read_text())['items']
        rows={r['id']:r for r in source}
        self.assertEqual(len(rows),len(source))
        for row in module.entries():self.assertEqual(rows[row['id']],row)
        for kind in ['name','address','car']:
            for value in THEMES:self.assertIn(f'tool-{kind}-{value}',rows)
            self.assertIn(f'tool-method-{kind}',rows)


class GatewayTests(unittest.IsolatedAsyncioTestCase):
    async def test_only_valid_calculation_is_forwarded(self):
        seen=[]
        async def upstream(request):seen.append(request);return httpx.Response(200,json={'ok':True})
        app=create_public_gateway(['https://example.org'],transport=httpx.MockTransport(upstream))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test',headers={'Origin':'https://example.org','Authorization':'Bearer test'}) as client:
            self.assertEqual((await client.post('/api/numerology/tools',json=payload())).status_code,200)
            self.assertEqual((await client.post('/api/numerology/tools',json=payload('car',{'car_number':'000'}))).status_code,422)
            self.assertEqual(len(seen),1)


@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'),'isolated Mongo required')
class ServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mongo=AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL'])
        self.db=self.mongo['numerom_test_tools_'+uuid.uuid4().hex]
        await self.db.users.insert_many([{'id':'student','credits_remaining':20},{'id':'other','credits_remaining':20}])
        self.service=NumberTools(self.db);self.data=ToolRequest.model_validate(payload())
    async def asyncTearDown(self):
        await self.mongo.drop_database(self.db.name);self.mongo.close()

    async def test_parallel_retries_commit_once_and_history_is_private_free(self):
        rows=await asyncio.gather(*(self.service.calculate('student',self.data) for _ in range(15)))
        self.assertEqual(len({r['id'] for r in rows}),1)
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],19)
        self.assertEqual(await self.db.numerology_calculations.count_documents({}),1)
        self.assertEqual(await self.db.credit_transactions.count_documents({}),1)
        self.assertEqual((await self.service.history('student'))['calculations'],[rows[0]])
        self.assertEqual((await self.service.history('other'))['calculations'],[])
        self.assertEqual(await self.service.catalog('student'),{'name':1,'address':1,'car':1})

    async def test_distinct_concurrent_requests_cannot_overdraw(self):
        await self.db.users.update_one({'id':'student'},{'$set':{'credits_remaining':3}})
        rows=await asyncio.gather(*(self.service.calculate('student',ToolRequest.model_validate(payload())) for _ in range(10)),return_exceptions=True)
        self.assertEqual(sum(isinstance(r,dict) for r in rows),3)
        self.assertTrue(all(isinstance(r,dict) or isinstance(r,HTTPException) and r.status_code==402 for r in rows))
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],0)
        self.assertEqual(await self.db.numerology_calculations.count_documents({}),3)

    async def test_price_change_and_changed_retry(self):
        first=await self.service.calculate('student',self.data)
        await self.db.credits_deduction_config.insert_one({'is_active':True,'name_numerology':2})
        self.assertEqual(await self.service.calculate('student',self.data),first)
        for data in [self.data.model_copy(update={'request_id':uuid.uuid4()}),self.data.model_copy(update={'inputs':{'name':'Иван'}})]:
            with self.assertRaises(HTTPException) as e:await self.service.calculate('student',data)
            self.assertEqual(e.exception.status_code,409)
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],19)

    async def test_outbox_keeps_a_result_during_delivery_failure(self):
        broken=SimpleNamespace(users=self.db.users,credits_deduction_config=self.db.credits_deduction_config,
          numerology_calculations=SimpleNamespace(update_one=AsyncMock(side_effect=RuntimeError()),find=self.db.numerology_calculations.find,find_one=self.db.numerology_calculations.find_one),
          credit_transactions=SimpleNamespace(update_one=AsyncMock(side_effect=RuntimeError())))
        service=NumberTools(broken);first=await service.calculate('student',self.data)
        self.assertEqual((await service.history('student'))['calculations'],[first])
        self.assertEqual(await self.service.calculate('student',self.data),first)
        self.assertEqual(await self.db.numerology_calculations.count_documents({}),1)
        self.assertEqual(await self.db.credit_transactions.count_documents({}),1)

    async def test_http_auth_and_legacy_validation_before_spending(self):
        app=FastAPI();app.include_router(create_number_tools_router(self.db))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
            self.assertEqual((await client.get('/api/numerology/tools/history')).status_code,401)
            app.dependency_overrides[get_current_user]=lambda:{'user_id':'student'}
            self.assertEqual((await client.post('/api/numerology/tools',json=payload('car',{'car_number':'000'}))).status_code,422)
            response=await client.post('/api/numerology/tools',json=self.data.model_dump(mode='json'))
            self.assertEqual(response.status_code,200)
        with self.assertRaises(HTTPException) as e:await self.service.legacy('student','name',{'name':'123'})
        self.assertEqual(e.exception.status_code,422)
        raw={'car_number':'ABC123','request_id':str(uuid.uuid4()),'expected_cost':1}
        one=await self.service.legacy('student','car',raw)
        self.assertEqual(one,calculate_car_number_numerology('ABC123'))
        self.assertEqual(await self.service.legacy('student','car',raw),one)
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],18)

    async def test_free_calculation_and_disabled_account(self):
        await self.db.credits_deduction_config.insert_one({'is_active':True,'name_numerology':0})
        data=self.data.model_copy(update={'expected_cost':0})
        self.assertEqual((await self.service.calculate('student',data))['cost'],0)
        self.assertEqual(await self.db.credit_transactions.count_documents({}),0)
        await self.db.users.update_one({'id':'student'},{'$set':{'is_disabled':True}})
        with self.assertRaises(HTTPException) as e:await self.service.history('student')
        self.assertEqual(e.exception.status_code,401)
