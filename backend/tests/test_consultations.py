import asyncio,json,os,sys,tempfile,unittest,uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi import HTTPException,FastAPI
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from services.consultations import Consultations,ConsultationPurchase
from routers.consultations import create_consultations_router
from auth import get_current_user
from public_gateway import _route,_valid_body

class ContractTests(unittest.TestCase):
    def test_gateway_and_purchase_contract(self):
        self.assertEqual(_route('GET','/api/student/consultations'),'read')
        self.assertEqual(_route('POST','/api/student/consultations/abc/purchase'),'write')
        self.assertEqual(_route('HEAD','/api/student/consultation-media/abc'),'media')
        self.assertIsNone(_route('GET','/api/student/consultations/abc/private/access'))
        self.assertTrue(_valid_body('/api/student/consultations/abc/purchase',{'expected_cost':10}))
        for body in [{'expected_cost':-1},{'expected_cost':True},{'expected_cost':10,'user_id':'other'},{'expected_cost':'10'},{'expected_cost':float('nan')}]:
            self.assertFalse(_valid_body('/api/student/consultations/abc/purchase',body))

@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'),'isolated Mongo required')
class ConsultationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.secret=patch.dict(os.environ,{'SECRET_KEY':'consultation-test-signing-key-32-characters'});self.secret.start()
        self.mongo=AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL']);self.db=self.mongo['numerom_test_consultations_'+uuid.uuid4().hex]
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        await self.db.users.insert_many([{'id':'student','credits_remaining':20},{'id':'other','credits_remaining':20}])
        await self.db.personal_consultations.insert_one({'id':'c1','assigned_user_id':'student','title':'Разбор','cost_credits':10,'is_active':True,'pdf_file_id':'f1'})
        await self.db.files.insert_one({'id':'f1','stored_name':'guide.pdf','original_name':'Разбор.pdf'})
        (self.root/'guide.pdf').write_bytes(b'%PDF-1.4\nQA material')
        self.service=Consultations(self.db,self.root,'https://example.org')
    async def asyncTearDown(self):
        await self.mongo.drop_database(self.db.name);self.mongo.close();self.temp.cleanup();self.secret.stop()
    async def test_listing_hides_files_and_other_users(self):
        own=(await self.service.listing('student'))['consultations'];self.assertEqual(len(own),1);self.assertNotIn('pdf_file_id',own[0]);self.assertNotIn('video_url',own[0]);self.assertFalse(own[0]['is_purchased'])
        self.assertEqual((await self.service.listing('other'))['consultations'],[])
        for user in ['student','other']:
            with self.assertRaises(HTTPException):await self.service.access(user,'c1','pdf')
        with self.assertRaises(HTTPException):await self.service.purchase('other','c1',10)
    async def test_concurrent_purchase_debits_once_and_repairs_history(self):
        receipts=await asyncio.gather(*(self.service.purchase('student','c1',10) for _ in range(20)))
        self.assertTrue(all(r['is_purchased'] for r in receipts));self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],10)
        self.assertEqual(await self.db.consultation_purchases.count_documents({}),1);self.assertEqual(await self.db.credit_transactions.count_documents({}),1)
    async def test_insufficient_or_changed_price_cannot_debit(self):
        with self.assertRaises(HTTPException) as e:await self.service.purchase('student','c1',1)
        self.assertEqual(e.exception.status_code,409)
        await self.db.users.update_one({'id':'student'},{'$set':{'credits_remaining':5}})
        with self.assertRaises(HTTPException) as e:await self.service.purchase('student','c1',10)
        self.assertEqual(e.exception.status_code,402)
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],5)
    async def test_free_and_legacy_paid_consultations_do_not_charge(self):
        await self.db.consultation_purchases.insert_one({'user_id':'student','consultation_id':'c1'})
        self.assertTrue((await self.service.purchase('student','c1',10))['is_purchased'])
        await self.db.personal_consultations.update_one({'id':'c1'},{'$set':{'cost_credits':0}})
        self.assertTrue((await self.service.purchase('student','c1',0))['is_purchased'])
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],20)
    async def test_delivery_failure_keeps_access_and_retry_repairs_without_charge(self):
        failing=SimpleNamespace(users=self.db.users,personal_consultations=self.db.personal_consultations,consultation_purchases=SimpleNamespace(find_one=self.db.consultation_purchases.find_one,update_one=AsyncMock(side_effect=RuntimeError())),credit_transactions=self.db.credit_transactions)
        service=Consultations(failing,self.root,'https://example.org')
        self.assertTrue((await service.purchase('student','c1',10))['is_purchased'])
        await self.service.listing('student')
        self.assertEqual(await self.db.consultation_purchases.count_documents({}),1)
        self.assertEqual(await self.db.credit_transactions.count_documents({}),1)
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],10)
    async def test_material_token_rechecks_assignment_block_and_password_version(self):
        await self.service.purchase('student','c1',10);access=await self.service.access('student','c1','pdf');token=access['url'].rsplit('/',1)[1]
        self.assertEqual((await self.service.resolve(token))[0],(self.root/'guide.pdf').resolve())
        await self.db.users.update_one({'id':'student'},{'$set':{'auth_version':1}})
        with self.assertRaises(HTTPException):await self.service.resolve(token)
        await self.db.users.update_one({'id':'student'},{'$set':{'auth_version':0,'is_disabled':True}})
        with self.assertRaises(HTTPException):await self.service.resolve(token)
        await self.db.users.update_one({'id':'student'},{'$set':{'is_disabled':False}})
        await self.db.personal_consultations.update_one({'id':'c1'},{'$set':{'assigned_user_id':'other'}})
        with self.assertRaises(HTTPException):await self.service.resolve(token)
    async def test_path_traversal_and_inactive_consultation_are_unavailable(self):
        await self.service.purchase('student','c1',10)
        await self.db.files.update_one({'id':'f1'},{'$set':{'stored_name':'../outside.pdf'}})
        with self.assertRaises(HTTPException):await self.service.access('student','c1','pdf')
        await self.db.personal_consultations.update_one({'id':'c1'},{'$set':{'is_active':False}})
        self.assertEqual((await self.service.listing('student'))['consultations'],[])
    async def test_router_requires_auth_and_serves_private_range(self):
        app=FastAPI();app.include_router(create_consultations_router(self.db,self.service))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='https://example.org') as client:
            self.assertEqual((await client.get('/api/student/consultations')).status_code,401)
            app.dependency_overrides[get_current_user]=lambda:{'user_id':'student'}
            r=await client.post('/api/student/consultations/c1/purchase',json={'expected_cost':10});self.assertEqual(r.status_code,200)
            url=(await client.get('/api/student/consultations/c1/pdf/access')).json()['url']
            r=await client.get(url,headers={'Range':'bytes=0-3'});self.assertEqual(r.status_code,206);self.assertEqual(r.content,b'%PDF');self.assertIn('no-store',r.headers['cache-control'])
