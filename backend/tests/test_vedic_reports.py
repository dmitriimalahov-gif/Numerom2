import asyncio,json,os,sys,unittest,uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi import FastAPI,HTTPException
from pydantic import ValidationError
from motor.motor_asyncio import AsyncIOMotorClient
import httpx
from auth import get_current_user
from domain import vedic_report as domain
from services.vedic_calculations import VedicCalculations
from routers.vedic_calculations import create_vedic_calculations_router

def payload(kind='daily',**changes):return {'kind':kind,'date':'2026-10-18','city':'Кишинёв','birth_date':'10.01.1982','request_id':str(uuid.uuid4()),'expected_cost':1,**changes}
def data(kind='daily',**changes):return domain.VedicRequest.model_validate(payload(kind,**changes))
class DomainTests(unittest.TestCase):
 def setUp(self):self.coordinates=patch.dict(domain.legacy._city_cache,{'Кишинёв':(47.0105,28.8638,'Europe/Chisinau')});self.coordinates.start()
 def tearDown(self):self.coordinates.stop()
 def test_every_period_contains_exact_dates_real_values_and_one_narration(self):
  for kind,count in domain.KINDS.items():
   report=domain.build_vedic_report(data(kind));self.assertEqual(len(report['days']),count)
   self.assertEqual(report['narration_id'],'vedic-'+kind)
   self.assertEqual(len(report['days'][0]['hours']),24 if count==1 else 0)
   for d in report['days']:
    self.assertEqual(len(d['energies']),0 if kind=='schedule' else 9)
    self.assertEqual(len(d['periods']),4)
    if kind!='schedule':self.assertAlmostEqual(d['average'],sum(i['value'] for i in d['energies'])/9,places=2)
   self.assertNotIn('energy_level',json.dumps(report))
   self.assertLess(len(json.dumps(report))*5,4*1024*1024)
 def test_existing_daily_formula_and_hours_are_preserved(self):
  d=data();report=domain.build_vedic_report(d)
  energies=domain.calculate_enhanced_daily_planetary_energy(destiny_number=domain.calculate_bhagya_ank(10,1,1982),date=datetime(2026,10,18),birth_date=d.birth_date,city=d.city,**domain.user_context(d.birth_date),modifiers_config={})
  self.assertEqual({e['key']:e['value'] for e in report['days'][0]['energies']},energies)
  schedule=domain.legacy.get_vedic_day_schedule(d.city,datetime(2026,10,18))
  self.assertEqual(report['days'][0]['hours'][0]['start'],schedule['planetary_hours'][0]['start_time'])
 def test_routes_use_and_report_real_wisdom_never_doubled_destiny(self):
  profile={'name':'Dmitrii','surname':'Malahov','full_name':'Дмитрий Малахов'}
  report=domain.build_vedic_report(data(),profile=profile)
  self.assertEqual(report['wisdom'],{'value':5,'destiny':4,'full_name_number':1,'calculation':'4 + 1 = 5'})
  self.assertIn('Число мудрости 5 = судьба 4 + полное число имени 1',report['wisdom_note'])
  context=domain.user_context('10.01.1982',profile)
  self.assertEqual(context['user_numbers']['wisdom_number'],5)
  self.assertEqual(context['name_numbers'],{'first_name_number':1,'last_name_number':9,'total_name_number':1,'full_name_number':1})
  energies=domain.calculate_enhanced_daily_planetary_energy(destiny_number=4,date=datetime(2026,10,18),birth_date='10.01.1982',city='Кишинёв',**context,modifiers_config={})
  self.assertEqual({e['key']:e['value'] for e in report['days'][0]['energies']},energies)
  # Without a Latin name (or for someone else's birth date) the wisdom is left out, not replaced by 4 × 2.
  for missing,reason in [({'name':'Дмитрий','surname':'Малахов'},'латиницей'),(None,'не совпадает')]:
   self.assertNotIn('wisdom_number',domain.user_context('10.01.1982',missing)['user_numbers'])
   report=domain.build_vedic_report(data(),profile=missing)
   self.assertIsNone(report['wisdom']);self.assertIn(reason,report['wisdom_note'])
  self.assertNotIn('wisdom',domain.build_vedic_report(data('schedule',birth_date='')))
 def test_unknown_polar_and_incomplete_routes_fail_instead_of_fallback(self):
  for coords in [(0,0,'UTC'),(89,0,'UTC')]:
   with patch.object(domain.legacy,'get_city_coordinates',return_value=coords),self.assertRaises(HTTPException) as error:domain.build_vedic_report(data())
   self.assertEqual(error.exception.status_code,422)
  with patch.object(domain.legacy,'get_weekly_planetary_route',return_value={'daily_schedule':[]}),self.assertRaises(HTTPException):domain.build_vedic_report(data('weekly'))
  with patch.object(domain,'calculate_enhanced_daily_planetary_energy',return_value={'surya':50}),self.assertRaises(HTTPException):domain.build_vedic_report(data())
 def test_strict_input_and_boundary_dates(self):
  for change in [{'date':'2026-02-30'},{'city':'123'},{'city':'a\nb'},{'birth_date':''},{'birth_date':'31.02.2000'},{'expected_cost':True},{'request_id':str(uuid.uuid1())},{'user_id':'other'},{'date':'2099-12-31','kind':'weekly'}]:
   item=payload();item.update(change)
   with self.assertRaises(ValidationError):domain.VedicRequest.model_validate(item)
  self.assertEqual(data('schedule',birth_date='').birth_date,'')

@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'),'isolated Mongo required')
class ServiceTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  self.client=AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL']);self.db=self.client['numerom_test_vedic_'+uuid.uuid4().hex]
  await self.db.users.insert_many([{'id':'student','credits_remaining':10},{'id':'other','credits_remaining':10}])
  await self.db.credits_deduction_config.insert_one({'is_active':True,**{p:1 for p in domain.PRICES.values()}})
  self.service=VedicCalculations(self.db);self.data=data()
 async def asyncTearDown(self):await self.client.drop_database(self.db.name);self.client.close()
 async def test_async_build_replay_concurrency_and_owner_history(self):
  def fake(d,**kwargs):return {'legacy':{},'version':1,'kind':d.kind,'profile':kwargs['profile']}
  with patch('services.vedic_calculations.build_vedic_report',side_effect=fake) as build:
   rows=await asyncio.gather(*(self.service.calculate('student',self.data) for _ in range(6)))
   self.assertTrue(all(r==rows[0] for r in rows));self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],9)
   await self.db.credits_deduction_config.update_one({'is_active':True},{'$set':{'planetary_daily':2}})
   build.reset_mock();self.assertEqual(await self.service.calculate('student',self.data),rows[0]);build.assert_not_called()
  self.assertEqual((await self.service.history('other'))['calculations'],[])
  self.assertEqual(len((await self.service.history('student'))['calculations']),1)
  self.assertEqual(await self.db.credit_transactions.count_documents({}),1)
 async def test_profile_name_applies_only_to_the_owners_birth_date(self):
  await self.db.users.update_one({'id':'student'},{'$set':{'birth_date':'10.01.1982','name':'Dmitrii','surname':'Malahov','full_name':'Дмитрий Малахов'}})
  def fake(d,**kwargs):return {'legacy':{},'version':1,'kind':d.kind,'profile':kwargs['profile']}
  with patch('services.vedic_calculations.build_vedic_report',side_effect=fake):
   own=await self.service.calculate('student',self.data)
   other=await self.service.calculate('student',data(birth_date='11.02.1990'))
  self.assertEqual(own['results']['profile'],{'name':'Dmitrii','surname':'Malahov','full_name':'Дмитрий Малахов'})
  self.assertIsNone(other['results']['profile'])
 async def test_failed_build_never_debits_or_saves(self):
  with patch('services.vedic_calculations.build_vedic_report',side_effect=HTTPException(422,'Unknown place')):
   with self.assertRaises(HTTPException):await self.service.calculate('student',self.data)
  self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],10)
  self.assertEqual(await self.db.numerology_calculations.count_documents({}),0)
 async def test_auth_validation_and_get_are_read_only(self):
  app=FastAPI();app.include_router(create_vedic_calculations_router(self.db))
  async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
   self.assertEqual((await client.get('/api/numerology/vedic/catalog')).status_code,401)
   app.dependency_overrides[get_current_user]=lambda:{'user_id':'student'}
   self.assertEqual((await client.get('/api/numerology/vedic/catalog')).status_code,200)
   self.assertEqual((await client.get('/api/numerology/vedic/history')).status_code,200)
   invalid=payload();invalid['date']='2026-02-30'
   self.assertEqual((await client.post('/api/numerology/vedic',json=invalid)).status_code,422)
  self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],10)
