import asyncio
import copy
import hashlib
import hmac
import json
import os
import sys
import time
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
import stripe
from fastapi import FastAPI,HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from auth import get_current_user
from domain.payments import CheckoutRequest,PACKAGES,packages
from services.payments import PaymentConfig,Payments
from services.credit_history import flush_pending_credit_transactions
from routers.payments import create_payments_router
from public_gateway import create_public_gateway,_route,_valid_body

def config(live=False):
    return PaymentConfig({'STRIPE_SECRET_KEY':'sk_'+('live' if live else 'test')+'_fake',
        'STRIPE_WEBHOOK_SECRET':'whsec_test_fixture','STRIPE_MODE':'live' if live else 'test',
        'STRIPE_LIVE_ENABLED':'1' if live else '0','STRIPE_MOBILE_RETURN_URL':'https://example.org/app/payment-result/'})

class FakeStripe:
    def __init__(self,live):self.sessions={};self.keys={};self.calls=[];self.live=live
    async def create(self,params,key):
        self.calls.append((copy.deepcopy(params),key))
        if key not in self.keys:
            sid='cs_test_'+uuid.uuid4().hex
            self.keys[key]=sid
            self.sessions[sid]={'id':sid,'url':'https://checkout.stripe.com/c/pay/'+sid,
                'payment_status':'unpaid','status':'open','livemode':self.live,
                **{k:params[k] for k in ['mode','metadata','client_reference_id']},
                'currency':'eur','amount_total':params['line_items'][0]['price_data']['unit_amount']}
        return copy.deepcopy(self.sessions[self.keys[key]])
    async def retrieve(self,sid):return copy.deepcopy(self.sessions[sid])
    async def expire(self,sid):
        if self.sessions[sid]['status']!='open':raise RuntimeError('Session is no longer open')
        self.sessions[sid]['status']='expired'
        return copy.deepcopy(self.sessions[sid])
    def event(self,raw,signature):return stripe.Webhook.construct_event(raw,signature,'whsec_test_fixture').to_dict()

class ContractTests(unittest.TestCase):
    def test_catalog_declares_all_client_required_fields(self):
        for item in packages():
            self.assertIsInstance(item['consultation'],bool)
            self.assertIsInstance(item['access_days'],int)
            self.assertIs(item['recurring'],False)
    def test_unconfigured_and_live_without_explicit_switch_are_disabled(self):
        self.assertFalse(PaymentConfig({}).enabled)
        self.assertFalse(PaymentConfig({'STRIPE_SECRET_KEY':'sk_live_fake','STRIPE_MODE':'live',
            'STRIPE_WEBHOOK_SECRET':'whsec_x','STRIPE_MOBILE_RETURN_URL':'https://example.org/return'}).enabled)
        self.assertTrue(config().enabled)
    def test_return_url_does_not_come_from_request(self):
        with self.assertRaises(ValueError):CheckoutRequest(package_type='one_time',request_id=uuid.uuid4(),origin_url='https://evil.test')
        self.assertFalse(PaymentConfig({'STRIPE_SECRET_KEY':'sk_test_fake','STRIPE_WEBHOOK_SECRET':'whsec_x',
            'STRIPE_MOBILE_RETURN_URL':'javascript:alert(1)'}).enabled)
    def test_expired_temporary_sandbox_cannot_offer_new_checkout(self):
        c=PaymentConfig({'STRIPE_SECRET_KEY':'rkcs_test_fake','STRIPE_WEBHOOK_SECRET':'whsec_fixture',
            'STRIPE_MOBILE_RETURN_URL':'https://example.org/return','STRIPE_SANDBOX_EXPIRES_AT':'2000-01-01'})
        self.assertFalse(c.enabled)
    def test_gateway_uses_bounded_contracts(self):
        self.assertEqual(_route('POST','/api/webhook/stripe'),'stripe_webhook')
        self.assertEqual(_route('GET','/api/payments/checkout/status/cs_test_123'),'read')
        self.assertIsNone(_route('POST','/api/payments/checkout/status/cs_test_123'))
        body={'package_type':'one_time','request_id':str(uuid.uuid4()),'client':'mobile'}
        self.assertTrue(_valid_body('/api/payments/checkout/session',body))
        self.assertFalse(_valid_body('/api/payments/checkout/session',{**body,'credits':1000000}))

class GatewayTests(unittest.IsolatedAsyncioTestCase):
    async def test_signed_bytes_forward_unchanged_without_bearer(self):
        raw=b'{ "id": "evt_test", "data" : {"object": {}} }\n'
        async def upstream(request):
            self.assertEqual(await request.aread(),raw)
            self.assertEqual(request.headers['stripe-signature'],'t=1,v1=abc')
            self.assertNotIn('authorization',request.headers)
            return httpx.Response(200,json={'received':True})
        app=create_public_gateway(['https://example.org'],transport=httpx.MockTransport(upstream))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='https://gateway') as client:
            r=await client.post('/api/webhook/stripe',content=raw,headers={'stripe-signature':'t=1,v1=abc','content-type':'application/json'})
            self.assertEqual(r.status_code,200)
            self.assertEqual((await client.post('/api/webhook/stripe',content=raw)).status_code,400)
            self.assertEqual((await client.get('/api/payments/packages')).status_code,401)

@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'),'isolated Mongo required')
class PaymentConcurrency(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mongo=AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL'])
        self.db=self.mongo['numerom_test_payments_'+uuid.uuid4().hex]
        await self.db.users.insert_one({'id':'student','credits_remaining':7})
        self.provider=FakeStripe(True);self.service=Payments(self.db,config(True),self.provider)
    async def asyncTearDown(self):
        await self.mongo.drop_database(self.db.name);self.mongo.close()
    async def checkout(self,package='one_time'):
        return await self.service.create('student',CheckoutRequest(package_type=package,request_id=uuid.uuid4()))
    def pay(self,response):
        session=self.provider.sessions[response['session_id']]
        session.update(payment_status='paid',status='complete')
        return session
    async def test_parallel_create_reuses_one_order_and_identical_stripe_parameters(self):
        request=CheckoutRequest(package_type='one_time',request_id=uuid.uuid4())
        responses=await asyncio.gather(*(self.service.create('student',request) for _ in range(12)))
        self.assertEqual(len({r['session_id'] for r in responses}),1)
        self.assertEqual(await self.db.payment_orders.count_documents({}),1)
        self.assertTrue(all(call==self.provider.calls[0] for call in self.provider.calls))
        self.assertNotIn('payment_method_types',self.provider.calls[0][0])
        self.assertGreater(self.provider.calls[0][0]['expires_at'],time.time()+1800)
    async def test_concurrent_duplicate_fulfillment_and_status_grant_once(self):
        response=await self.checkout();paid=self.pay(response)
        await asyncio.gather(*(self.service.fulfill(copy.deepcopy(paid)) for _ in range(20)))
        user=await self.db.users.find_one({'id':'student'})
        self.assertEqual(user['credits_remaining'],17)
        self.assertEqual(len(user['fulfilled_payments']),1)
        self.assertEqual(await self.db.credit_transactions.count_documents({}),1)
        self.assertAlmostEqual((user['subscription_expires_at']-user['fulfilled_payments'][response['order_id']]['at']).total_seconds(),30*86400,delta=.1)
    async def test_failure_after_credit_commit_is_repaired_without_second_grant(self):
        response=await self.checkout();paid=self.pay(response)
        failing=SimpleNamespace(users=self.db.users,credit_transactions=self.db.credit_transactions,
            payment_orders=SimpleNamespace(find_one=self.db.payment_orders.find_one,
                update_one=AsyncMock(side_effect=RuntimeError('synthetic write outage'))))
        with self.assertRaises(RuntimeError):await Payments(failing,config(True),self.provider).fulfill(paid)
        await self.service.fulfill(paid)
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],17)
        self.assertEqual(await self.db.credit_transactions.count_documents({}),1)
    async def test_history_failure_leaves_recoverable_outbox(self):
        response=await self.checkout()
        with patch('services.payments.flush_pending_credit_transactions',new=AsyncMock(side_effect=RuntimeError('history outage'))):
            await self.service.fulfill(self.pay(response))
        user=await self.db.users.find_one({'id':'student'});self.assertEqual(user['credits_remaining'],17)
        self.assertEqual(len(user['pending_credit_transactions']),1)
        await flush_pending_credit_transactions(self.db,'student')
        self.assertEqual(await self.db.credit_transactions.count_documents({}),1)
    async def test_unpaid_or_mismatched_amount_cannot_grant(self):
        response=await self.checkout();session=self.provider.sessions[response['session_id']]
        await self.service.fulfill(session)
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],7)
        session=self.pay(response);session['amount_total']=1
        with self.assertRaises(HTTPException):await self.service.fulfill(session)
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],7)
    async def test_owner_currency_mode_and_session_are_verified(self):
        response=await self.checkout();paid=self.pay(response)
        for change in [{'livemode':False},{'currency':'usd'},{'id':'cs_test_foreign'},{'metadata':{**paid['metadata'],'user_id':'other'}}]:
            with self.assertRaises(HTTPException):await self.service.fulfill({**paid,**change})
        await self.db.users.insert_one({'id':'other'})
        with self.assertRaises(HTTPException) as e:await self.service.status('other',response['session_id'])
        self.assertEqual(e.exception.status_code,404)
    async def test_test_money_does_not_change_real_balance_or_access(self):
        self.provider.live=False;self.service=Payments(self.db,config(),self.provider)
        response=await self.checkout('master_consultation');await self.service.fulfill(self.pay(response))
        user=await self.db.users.find_one({'id':'student'})
        self.assertEqual(user['credits_remaining'],7);self.assertEqual(user['test_credits_remaining'],10000)
        self.assertNotIn('is_premium',user)
        self.assertEqual(await self.db.personal_consultations.count_documents({}),0)
        self.assertEqual(await self.db.credit_transactions.count_documents({}),0)
    async def test_cancel_expires_only_owned_open_session_and_does_not_hide_paid_session(self):
        response=await self.checkout()
        await self.db.users.insert_one({'id':'other'})
        with self.assertRaises(HTTPException) as e:await self.service.cancel('other',response['session_id'])
        self.assertEqual(e.exception.status_code,404)
        self.assertEqual((await self.service.cancel('student',response['session_id']))['status'],'expired')
        second=await self.checkout();self.pay(second)
        self.assertEqual((await self.service.cancel('student',second['session_id']))['status'],'paid')
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],17)
    async def test_retry_does_not_reopen_an_expired_checkout(self):
        request=CheckoutRequest(package_type='one_time',request_id=uuid.uuid4())
        response=await self.service.create('student',request)
        await self.provider.expire(response['session_id'])
        retried=await self.service.create('student',request)
        self.assertEqual(retried['state'],'expired')
        self.assertEqual(retried['session_id'],response['session_id'])
    async def test_replaced_sandbox_releases_missing_expired_test_checkout(self):
        self.provider.live=False;self.service=Payments(self.db,config(),self.provider)
        request=CheckoutRequest(package_type='one_time',request_id=uuid.uuid4())
        response=await self.service.create('student',request)
        await self.db.payment_orders.update_one({'_id':response['order_id']},{'$set':{'expires_at':int(time.time())-60}})
        missing=stripe.InvalidRequestError('No such checkout session','id',code='resource_missing')
        with patch.object(self.provider,'retrieve',new=AsyncMock(side_effect=missing)) as retrieve:
            self.assertEqual((await self.service.create('student',request))['state'],'expired')
            self.assertEqual((await self.service.status('student',response['session_id']))['status'],'expired')
            retrieve.assert_awaited_once()
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],7)
        self.assertEqual(await self.db.payment_test_ledger.count_documents({}),0)
    async def test_missing_session_cannot_expire_live_active_or_uncertain_payment(self):
        missing=stripe.InvalidRequestError('No such checkout session','id',code='resource_missing')
        for live,remaining,error in [(True,-60,missing),(False,60,missing),(False,-60,RuntimeError('network outage'))]:
            self.provider.live=live;self.service=Payments(self.db,config(live),self.provider)
            response=await self.checkout()
            await self.db.payment_orders.update_one({'_id':response['order_id']},{'$set':{'expires_at':int(time.time())+remaining}})
            with patch.object(self.provider,'retrieve',new=AsyncMock(side_effect=error)), self.assertRaises(HTTPException) as raised:
                await self.service.status('student',response['session_id'])
            self.assertEqual(raised.exception.status_code,502)
            self.assertEqual((await self.db.payment_orders.find_one({'_id':response['order_id']}))['state'],'pending')
    async def test_missing_test_session_never_overwrites_concurrent_paid_state(self):
        self.provider.live=False;self.service=Payments(self.db,config(),self.provider)
        response=await self.checkout()
        await self.db.payment_orders.update_one({'_id':response['order_id']},{'$set':{'expires_at':int(time.time())-60}})
        async def race(_):
            await self.service.fulfill(self.pay(response))
            raise stripe.InvalidRequestError('No such checkout session','id',code='resource_missing')
        with patch.object(self.provider,'retrieve',new=AsyncMock(side_effect=race)):
            self.assertEqual((await self.service.status('student',response['session_id']))['status'],'paid')
    async def test_master_consultation_is_created_once_without_placeholder_video(self):
        response=await self.checkout('master_consultation');paid=self.pay(response)
        await asyncio.gather(*(self.service.fulfill(paid) for _ in range(5)))
        self.assertEqual(await self.db.personal_consultations.count_documents({}),1)
        self.assertNotIn('video_url',await self.db.personal_consultations.find_one({}))
    async def test_signed_webhook_and_old_failure_event_are_idempotent(self):
        response=await self.checkout();paid=self.pay(response)
        for kind in ['checkout.session.completed','checkout.session.async_payment_succeeded','checkout.session.async_payment_failed']:
            raw=json.dumps({'type':kind,'data':{'object':paid}}).encode();timestamp=int(time.time())
            signature=hmac.new(b'whsec_test_fixture',str(timestamp).encode()+b'.'+raw,hashlib.sha256).hexdigest()
            await self.service.webhook(raw,f't={timestamp},v1={signature}')
        self.assertEqual((await self.service.status('student',response['session_id']))['status'],'paid')
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],17)
        with self.assertRaises(HTTPException):await self.service.webhook(raw,'invalid')
    async def test_failed_async_payment_stays_failed_after_status_or_late_completed_event(self):
        response=await self.checkout();session=self.provider.sessions[response['session_id']];session['status']='complete'
        for kind in ['checkout.session.async_payment_failed','checkout.session.completed']:
            raw=json.dumps({'type':kind,'data':{'object':session}}).encode();timestamp=int(time.time())
            signature=hmac.new(b'whsec_test_fixture',str(timestamp).encode()+b'.'+raw,hashlib.sha256).hexdigest()
            await self.service.webhook(raw,f't={timestamp},v1={signature}')
            self.assertEqual((await self.service.status('student',session['id']))['status'],'failed')
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],7)
    async def test_real_router_requires_auth_and_rejects_client_price(self):
        app=FastAPI();app.include_router(create_payments_router(self.db,self.service))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
            self.assertEqual((await client.get('/api/payments/history')).status_code,401)
            app.dependency_overrides[get_current_user]=lambda:{'user_id':'student'}
            r=await client.post('/api/payments/checkout/session',json={'package_type':'one_time','request_id':str(uuid.uuid4()),'amount':1})
            self.assertEqual(r.status_code,422)
            self.assertEqual(await self.db.payment_orders.count_documents({}),0)
