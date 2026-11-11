import asyncio,os,sys,uuid,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException,FastAPI
from httpx import AsyncClient,ASGITransport
from auth import get_current_user
from services.personal_calculations import PersonalCalculations,PersonalRequest
from routers.personal_reports import create_personal_reports_router
@unittest.skipUnless(os.getenv('NUMEROM_TEST_MONGO_URL'),'isolated Mongo only')
class PersonalPaidTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  self.client=AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL']);self.db=self.client['numerom_test_personal_paid_'+uuid.uuid4().hex]
  await self.db.users.insert_many([{'id':'u','name':'Anna','surname':'Li','birth_date':'10.01.1982','credits_remaining':10},{'id':'other','credits_remaining':20}]);self.s=PersonalCalculations(self.db)
 async def asyncTearDown(self):await self.client.drop_database(self.db.name);self.client.close()
 def request(self,**data):return PersonalRequest(**{'request_id':uuid.uuid4(),'kind':'personal','expected_cost':1,'birth_date':'10.01.1982',**data})
 async def test_concurrent_retry_commits_one_debit_and_same_personal_scheme(self):
  request=self.request();rows=await asyncio.gather(*(self.s.calculate('u',request) for _ in range(12)))
  self.assertEqual(len({r['id'] for r in rows}),1);self.assertEqual(rows[0]['results']['full_name_number'],6)
  self.assertEqual((await self.db.users.find_one({'id':'u'}))['credits_remaining'],9)
  self.assertEqual(await self.db.numerology_calculations.count_documents({}),1)
  self.assertEqual(await self.db.credit_transactions.count_documents({}),1)
 async def test_retry_uses_paid_snapshot_after_name_and_price_change(self):
  req=self.request();first=await self.s.calculate('u',req)
  self.assertEqual(first['results']['report']['profile_parts'],{'name':'Anna','surname':'Li'})
  await self.db.users.update_one({'id':'u'},{'$set':{'name':'Eve','surname':'Hill'}})
  await self.db.credits_deduction_config.insert_one({'is_active':True,'personal_numbers':7})
  self.assertEqual(await self.s.calculate('u',req),first)
  with self.assertRaises(HTTPException):await self.s.calculate('u',req.model_copy(update={'birth_date':'11.01.1982'}))
 async def test_free_history_is_owner_scoped_including_legacy_records(self):
  receipt=await self.s.calculate('u',self.request())
  await self.db.numerology_calculations.insert_one({'id':'legacy','user_id':'u','calculation_type':'personal_numbers','birth_date':'10.01.1982','created_at':'2026-10-17T00:00:00Z','results':receipt['results']['legacy']})
  app=FastAPI();app.include_router(create_personal_reports_router(self.db));app.dependency_overrides[get_current_user]=lambda:{'user_id':'u'}
  async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
   r=await client.get('/api/numerology/personal-numbers/history');self.assertEqual(r.status_code,200);self.assertEqual(len(r.json()['calculations']),2)
   self.assertTrue(all('personal_detail' not in row['results'] for row in r.json()['calculations']))
   app.dependency_overrides[get_current_user]=lambda:{'user_id':'other'}
   self.assertEqual((await client.get('/api/numerology/personal-numbers/history')).json()['calculations'],[])
  self.assertEqual((await self.db.users.find_one({'id':'u'}))['credits_remaining'],9)
