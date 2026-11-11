import asyncio
import os
import sys
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from auth import get_current_user
from domain.relationships import RelationshipRequest, build_relationships
from numerology import calculate_compatibility, calculate_group_compatibility
from routers.relationships import create_relationships_router
from services.relationships import Relationships
from public_gateway import create_public_gateway


def payload(**changes):
    return dict(kind='pair', request_id=str(uuid.uuid4()), expected_cost=1,
                main={'name': 'Анна', 'birth_date': '10.01.1982'},
                people=[{'name': 'Иван', 'birth_date': '22.11.1990'}], **changes)


class DomainTests(unittest.TestCase):
    def test_pair_and_group_preserve_existing_formula(self):
        data=RelationshipRequest.model_validate(payload())
        result=build_relationships(data)
        legacy=calculate_compatibility(data.main.birth_date,data.people[0].birth_date)
        self.assertEqual(result['legacy'],legacy)
        self.assertEqual(result['connections'][0]['score'],legacy['compatibility_score'])
        raw=payload();raw.update(kind='group',expected_cost=5)
        raw['people'].append({'name':'Ольга','birth_date':'01.01.2000'})
        data=RelationshipRequest.model_validate(raw);result=build_relationships(data)
        legacy=calculate_group_compatibility(data.main.birth_date,[p.model_dump() for p in data.people])
        self.assertEqual(result['legacy'],legacy)
        self.assertEqual(result['average'],legacy['average_compatibility'])
        self.assertTrue(result['main']['steps'])

    def test_validation_rejects_invalid_dates_prices_and_scope(self):
        for date in ['31.02.2000','01.01.2100','1.1.2000','01.01.1899']:
            raw=payload();raw['main']['birth_date']=date
            with self.assertRaises(ValidationError):RelationshipRequest.model_validate(raw)
        for update in [{'expected_cost':True},{'expected_cost':-1},{'expected_cost':'1'},
                       {'people':[]},{'people':[{'name':'x','birth_date':'01.01.2000'}]*6},
                       {'request_id':'bad'},{'user_id':'other'}]:
            raw=payload();raw.update(update)
            with self.assertRaises(ValidationError):RelationshipRequest.model_validate(raw)
        raw=payload();raw['people']*=2
        with self.assertRaises(ValidationError):RelationshipRequest.model_validate(raw)


class GatewayTests(unittest.IsolatedAsyncioTestCase):
    async def test_json_calculation_is_forwarded_and_invalid_input_is_blocked(self):
        seen=[]
        async def upstream(request):
            seen.append(request)
            return httpx.Response(200,json={'ok':True})
        app=create_public_gateway(['https://example.org'],transport=httpx.MockTransport(upstream))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test',headers={'Origin':'https://example.org','Authorization':'Bearer test'}) as client:
            response=await client.post('/api/numerology/relationships',json=payload())
            self.assertEqual(response.status_code,200)
            self.assertEqual(len(seen),1)
            invalid=payload();invalid['expected_cost']=True
            self.assertEqual((await client.post('/api/numerology/relationships',json=invalid)).status_code,422)
            self.assertEqual(len(seen),1)


@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'),'isolated Mongo required')
class ServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mongo=AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL'])
        self.db=self.mongo['numerom_test_relationships_'+uuid.uuid4().hex]
        await self.db.users.insert_many([{'id':'student','credits_remaining':20},{'id':'other','credits_remaining':20}])
        self.service=Relationships(self.db)
        self.data=RelationshipRequest.model_validate(payload())

    async def asyncTearDown(self):
        await self.mongo.drop_database(self.db.name);self.mongo.close()

    async def test_parallel_retry_commits_one_debit_and_result(self):
        results=await asyncio.gather(*(self.service.calculate('student',self.data) for _ in range(15)))
        self.assertEqual(len({r['id'] for r in results}),1)
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],19)
        self.assertEqual(await self.db.numerology_calculations.count_documents({}),1)
        self.assertEqual(await self.db.credit_transactions.count_documents({}),1)
        self.assertEqual((await self.service.history('student'))['calculations'][0]['id'],results[0]['id'])
        self.assertEqual((await self.service.history('other'))['calculations'],[])

    async def test_changed_retry_is_rejected_and_completed_retry_ignores_new_price(self):
        first=await self.service.calculate('student',self.data)
        altered=self.data.model_copy(deep=True);altered.people[0].name='Другое имя'
        with self.assertRaises(HTTPException) as error:await self.service.calculate('student',altered)
        self.assertEqual(error.exception.status_code,409)
        await self.db.credits_deduction_config.insert_one({'is_active':True,'compatibility_pair':7})
        self.assertEqual(await self.service.calculate('student',self.data),first)
        newer=self.data.model_copy(update={'request_id':uuid.uuid4()})
        with self.assertRaises(HTTPException) as error:await self.service.calculate('student',newer)
        self.assertEqual(error.exception.status_code,409)
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],19)

    async def test_balance_and_disabled_account_do_not_commit(self):
        await self.db.users.update_one({'id':'student'},{'$set':{'credits_remaining':0}})
        with self.assertRaises(HTTPException) as error:await self.service.calculate('student',self.data)
        self.assertEqual(error.exception.status_code,402)
        self.assertEqual(await self.db.numerology_calculations.count_documents({}),0)
        await self.db.users.update_one({'id':'student'},{'$set':{'is_disabled':True}})
        with self.assertRaises(HTTPException) as error:await self.service.history('student')
        self.assertEqual(error.exception.status_code,401)

    async def test_outbox_survives_delivery_failure_and_reads_are_free(self):
        failing=SimpleNamespace(users=self.db.users,credits_deduction_config=self.db.credits_deduction_config,
            numerology_calculations=SimpleNamespace(update_one=AsyncMock(side_effect=RuntimeError()),
                find=self.db.numerology_calculations.find,find_one=self.db.numerology_calculations.find_one),
            credit_transactions=SimpleNamespace(update_one=AsyncMock(side_effect=RuntimeError())))
        service=Relationships(failing)
        result=await service.calculate('student',self.data)
        self.assertEqual((await service.history('student'))['calculations'][0],result)
        await self.service.calculate('student',self.data)
        self.assertEqual(await self.db.numerology_calculations.count_documents({}),1)
        self.assertEqual(await self.db.credit_transactions.count_documents({}),1)
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],19)

    async def test_free_group_and_same_request_id_in_another_account(self):
        await self.db.credits_deduction_config.insert_one({'is_active':True,'group_compatibility':0})
        group=self.data.model_copy(update={'kind':'group','expected_cost':0})
        one=await self.service.calculate('student',group);two=await self.service.calculate('other',group)
        self.assertNotEqual(one['id'],two['id'])
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],20)
        self.assertEqual(await self.db.credit_transactions.count_documents({}),0)

    async def test_http_auth_validation_and_history_contract(self):
        app=FastAPI();app.include_router(create_relationships_router(self.db))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
            self.assertEqual((await client.get('/api/numerology/relationships/history')).status_code,401)
            app.dependency_overrides[get_current_user]=lambda:{'user_id':'student'}
            self.assertEqual((await client.get('/api/numerology/relationships/catalog')).json(),{'pair':1,'group':5})
            bad=payload();bad['main']['birth_date']='31.02.2000'
            self.assertEqual((await client.post('/api/numerology/relationships',json=bad)).status_code,422)
            response=await client.post('/api/numerology/relationships',json=self.data.model_dump(mode='json'))
            self.assertEqual(response.status_code,200)
            self.assertNotIn('request_hash',response.json())
            self.assertNotIn('_id',response.json())
            self.assertEqual(len((await client.get('/api/numerology/relationships/history')).json()['calculations']),1)

    async def test_legacy_website_response_and_invalid_date_before_debit(self):
        data={'person1_name':'Анна','person1_birth_date':'10.01.1982','person2_name':'Иван','person2_birth_date':'22.11.1990','request_id':str(uuid.uuid4()),'expected_cost':1}
        result=await self.service.legacy('student','pair',data)
        self.assertEqual(result,calculate_compatibility('10.01.1982','22.11.1990'))
        self.assertEqual(await self.service.legacy('student','pair',data),result)
        data['person2_birth_date']='31.02.2000'
        with self.assertRaises(HTTPException) as error:await self.service.legacy('student','pair',data)
        self.assertEqual(error.exception.status_code,422)
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],19)
