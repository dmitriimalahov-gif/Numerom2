"""Stripe Checkout, verified fulfillment and single-document credit commits."""
import asyncio
import hashlib
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

import stripe
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from domain.payments import PACKAGES, packages
from services.student_learning import _student
from services.credit_history import flush_pending_credit_transactions

log=logging.getLogger(__name__)
EVENTS={'checkout.session.completed','checkout.session.async_payment_succeeded',
        'checkout.session.async_payment_failed','checkout.session.expired'}

def unpaid_state(order,session,event_type=None):
    if session.get('status')=='expired':return 'expired'
    if event_type=='checkout.session.async_payment_failed' or order.get('state')=='failed':return 'failed'
    return 'processing' if session.get('status')=='complete' else 'pending'

def return_url(value, *, local=False):
    p=urlsplit(value)
    secure=p.scheme=='https' or (local and p.scheme=='http' and p.hostname in ('localhost','127.0.0.1'))
    if not secure or not p.hostname or p.username or p.password or p.query or p.fragment:
        raise ValueError('Payment return URL must be configured on the server')
    return value.rstrip('/')+'/'

class PaymentConfig:
    def __init__(self, env=None):
        env=os.environ if env is None else env
        self.key=env.get('STRIPE_SECRET_KEY','')
        self.webhook_secret=env.get('STRIPE_WEBHOOK_SECRET','')
        self.mode=env.get('STRIPE_MODE','test')
        self.live=self.mode=='live'
        expiry=env.get('STRIPE_SANDBOX_EXPIRES_AT','')
        try:self.sandbox_expires=datetime.fromisoformat(expiry).replace(tzinfo=timezone.utc).timestamp() if expiry else None
        except ValueError:self.sandbox_expires=0
        key_mode='live' if re.match(r'^[sr]k_live_',self.key) else 'test' if re.match(r'^(?:[sr]k|rkcs)_test_',self.key) else None
        self.returns={}
        for client,name in [('mobile','STRIPE_MOBILE_RETURN_URL'),('web','STRIPE_WEB_RETURN_URL')]:
            try:self.returns[client]=return_url(env.get(name,''),local=not self.live)
            except ValueError:pass
        self._enabled=(key_mode==self.mode and self.webhook_secret.startswith('whsec_')
                      and bool(self.returns) and (not self.live or env.get('STRIPE_LIVE_ENABLED')=='1'))

    @property
    def enabled(self):
        return bool(self._enabled and (self.live or self.sandbox_expires is None or time.time()<self.sandbox_expires))

class StripeProvider:
    def __init__(self, config):
        self.config=config
        self.client=stripe.StripeClient(config.key, max_network_retries=1,
            http_client=stripe.HTTPXClient(timeout=10)) if config.key else None
    async def create(self, params, key):
        return (await self.client.v1.checkout.sessions.create_async(params,options={'idempotency_key':key})).to_dict()
    async def retrieve(self, session_id):
        return (await self.client.v1.checkout.sessions.retrieve_async(session_id)).to_dict()
    async def expire(self, session_id):
        return (await self.client.v1.checkout.sessions.expire_async(session_id)).to_dict()
    def event(self, raw, signature):
        return stripe.Webhook.construct_event(raw,signature,self.config.webhook_secret,tolerance=300).to_dict()

class Payments:
    def __init__(self, db, config=None, provider=None):
        self.db=db;self.config=config or PaymentConfig();self.provider=provider or StripeProvider(self.config)

    async def catalog(self, user_id):
        user=await _student(self.db,user_id)
        return {'packages':packages(),'enabled':bool(self.config.enabled),'mode':self.config.mode,
            'clients':list(self.config.returns),'balance':user.get('credits_remaining',0),
            'test_balance':user.get('test_credits_remaining',0),
            'message':None if self.config.enabled else 'Оплата временно недоступна. Подключение Stripe ещё настраивается.'}

    def available(self):
        if not self.config.enabled:raise HTTPException(503,'Оплата временно недоступна. Баллы не списаны.')

    async def create(self,user_id,request):
        self.available();await _student(self.db,user_id)
        if request.client not in self.config.returns:raise HTTPException(503,'Возврат после оплаты ещё настраивается.')
        order_id=hashlib.sha256((user_id+':'+str(request.request_id)).encode()).hexdigest()
        now=datetime.utcnow()
        order={'_id':order_id,'user_id':user_id,'package_type':request.package_type,
            **PACKAGES[request.package_type],'currency':'eur','client':request.client,
            'return_url':self.config.returns[request.client],'livemode':self.config.live,
            'state':'creating','created_at':now,'expires_at':int(time.time())+2700}
        try:await self.db.payment_orders.insert_one(order)
        except DuplicateKeyError:
            order=await self.db.payment_orders.find_one({'_id':order_id})
        if any(order[k]!=v for k,v in [('package_type',request.package_type),('client',request.client),('livemode',self.config.live)]):
            raise HTTPException(409,'Эта попытка уже относится к другому пакету. Обновите страницу.')
        if order.get('session_id'):return self.checkout_response(await self.reconcile(order))
        if now-order['created_at']>timedelta(hours=23):raise HTTPException(409,'Попытка устарела. Начните новую оплату.')
        metadata={'integration':'numerom-credits-v1','order_id':order_id,'user_id':user_id,
                  'package_type':order['package_type']}
        params={'mode':'payment','client_reference_id':order_id,'metadata':metadata,
            'payment_intent_data':{'metadata':metadata},
            'success_url':order['return_url']+'?session_id={CHECKOUT_SESSION_ID}',
            'cancel_url':order['return_url']+'?cancelled=1&order_id='+order_id,
            'expires_at':order['expires_at'],
            'integration_identifier':'numerom_credits_qvhjtxpr',
            'line_items':[{'price_data':{'currency':order['currency'],'unit_amount':order['amount_total'],
                'product_data':{'name':'NumerOM · '+order['title'],'description':str(order['credits'])+' баллов. Разовая оплата.'}},'quantity':1}]}
        try:session=await self.provider.create(params,'numerom-checkout-'+order_id)
        except Exception:
            log.warning('Stripe checkout unavailable; order retained for idempotent retry')
            raise HTTPException(502,'Не удалось открыть Stripe. Повторите эту же попытку.')
        url=session.get('url','');p=urlsplit(url)
        if (not re.fullmatch(r'cs_(?:test_|live_)?[A-Za-z0-9]+',session.get('id','')) or
            p.scheme!='https' or p.hostname!='checkout.stripe.com' or p.username or p.password):
            raise HTTPException(502,'Stripe вернул некорректную ссылку. Повторите позже.')
        # A paid webhook may arrive before this write: never reset a fulfilled order.
        await self.db.payment_orders.update_one({'_id':order_id},{'$set':{'session_id':session['id'],'checkout_url':url}})
        await self.db.payment_orders.update_one({'_id':order_id,'state':'creating'},{'$set':{'state':'pending'}})
        order=await self.db.payment_orders.find_one({'_id':order_id})
        return self.checkout_response(order)

    def checkout_response(self,order):
        return {'order_id':order['_id'],'session_id':order['session_id'],'url':order['checkout_url'],
                'mode':'live' if order['livemode'] else 'test','state':order['state']}

    async def fulfill(self, session):
        metadata=session.get('metadata') or {}
        if metadata.get('integration')!='numerom-credits-v1':return None
        order_id=metadata.get('order_id','')
        if not re.fullmatch('[a-f0-9]{64}',order_id):raise HTTPException(400,'Некорректный заказ')
        order=await self.db.payment_orders.find_one({'_id':order_id})
        if not order:raise HTTPException(503,'Заказ пока недоступен')
        if (session.get('mode')!='payment' or session.get('client_reference_id')!=order_id or
            session.get('livemode') is not order['livemode'] or order['livemode']!=self.config.live or
            metadata.get('user_id')!=order['user_id'] or metadata.get('package_type')!=order['package_type'] or
            session.get('amount_total')!=order['amount_total'] or session.get('currency')!=order['currency'] or
            (order.get('session_id') and order['session_id']!=session.get('id'))):
            raise HTTPException(400,'Параметры платежа не совпали с заказом')
        if session.get('payment_status')!='paid':return order
        now=datetime.utcnow();live=order['livemode'];uid=order['user_id'];field='credits_remaining' if live else 'test_credits_remaining'
        marker='fulfilled_payments.'+order_id
        transaction={'id':'stripe-'+order_id,'user_id':uid,'transaction_type':'credit','amount':order['credits'],
            'category':'purchase','description':'Пополнение Stripe · '+order['title'],
            'details':{'amount_paid':order['amount_total']/100,'currency':order['currency'],'package_type':order['package_type']},'created_at':now}
        updates={field:{'$add':[{'$ifNull':['$'+field,0]},order['credits']]},marker:{'$literal':{'credits':order['credits'],'at':now,'livemode':live}}}
        if live:
            updates['pending_credit_transactions']={'$concatArrays':[{'$ifNull':['$pending_credit_transactions',[]]},{'$literal':[transaction]}]}
            if order['access_days']:
                current={'$cond':[{'$eq':[{'$type':'$subscription_expires_at'},'date']},'$subscription_expires_at',now]}
                updates.update(is_premium=True,subscription_type='annual' if order['access_days']==365 else 'monthly',
                    subscription_expires_at={'$add':[{'$max':[now,current]},order['access_days']*86400000]})
        result=await self.db.users.update_one({'id':uid,marker:{'$exists':False}},[{'$set':updates}])
        if not result.matched_count and not await self.db.users.find_one({'id':uid,marker:{'$exists':True}},{'_id':1}):
            raise HTTPException(503,'Не удалось зачислить баллы. Подтверждение будет повторено.')
        if live and order.get('consultation'):
            await self.db.personal_consultations.update_one({'_id':'stripe-'+order_id},{'$setOnInsert':{
                'id':'stripe-'+order_id,'assigned_user_id':uid,'title':'Персональная консультация мастера',
                'description':'Оплачено. Материалы появятся после подготовки мастером.','cost_credits':0,
                'is_active':True,'created_at':now,'updated_at':now}},upsert=True)
        if live:
            try:await flush_pending_credit_transactions(self.db,uid)
            except Exception:log.warning('Payment history delivery deferred; credits already committed')
        else:
            await self.db.payment_test_ledger.update_one({'_id':order_id},{'$setOnInsert':transaction},upsert=True)
        await self.db.payment_orders.update_one({'_id':order_id},{'$set':{'state':'paid','session_id':session['id'],'updated_at':now}})
        return await self.db.payment_orders.find_one({'_id':order_id})

    async def reconcile(self,order):
        if not order.get('session_id'):return order
        if order['livemode']!=self.config.live:return order
        if order['state']=='paid':return order
        if (not self.config.live and order['state']=='expired'
                and order.get('expiration_reason')=='test_session_unavailable'):return order
        self.available()
        try:session=await self.provider.retrieve(order['session_id'])
        except stripe.InvalidRequestError as error:
            # A replaced temporary sandbox cannot retrieve its old Checkout IDs.
            # Release only overdue TEST attempts; network errors and LIVE payments
            # still require authoritative reconciliation and must remain pending.
            expires=order.get('expires_at')
            if (not self.config.live and order['livemode'] is False and error.code=='resource_missing'
                    and isinstance(expires,(int,float)) and expires<=time.time()):
                await self.db.payment_orders.update_one(
                    {'_id':order['_id'],'livemode':False,'state':{'$ne':'paid'}},
                    {'$set':{'state':'expired','expiration_reason':'test_session_unavailable','updated_at':datetime.utcnow()}})
                return await self.db.payment_orders.find_one({'_id':order['_id']})
            raise HTTPException(502,'Пока не удалось проверить Stripe. Проверьте снова позже.')
        except Exception:raise HTTPException(502,'Пока не удалось проверить Stripe. Проверьте снова позже.')
        result=await self.fulfill(session)
        if not result:raise HTTPException(502,'Платёж не принадлежит NumerOM')
        if result['state']!='paid':
            state=unpaid_state(result,session)
            await self.db.payment_orders.update_one({'_id':order['_id'],'state':{'$ne':'paid'}},{'$set':{'state':state}})
            result=await self.db.payment_orders.find_one({'_id':order['_id']})
        return result

    async def status(self,user_id,session_id):
        await _student(self.db,user_id)
        order=await self.db.payment_orders.find_one({'user_id':user_id,'session_id':session_id})
        if not order:raise HTTPException(404,'Платёж не найден в вашем аккаунте')
        return self.public_order(await self.reconcile(order))

    async def cancel(self,user_id,session_id):
        await _student(self.db,user_id);self.available()
        order=await self.db.payment_orders.find_one({'user_id':user_id,'session_id':session_id})
        if not order:raise HTTPException(404,'Платёж не найден в вашем аккаунте')
        if order['livemode']!=self.config.live:raise HTTPException(409,'Режим оплаты изменился')
        try:await self.provider.expire(session_id)
        except Exception:pass  # The session may already be paid; reconcile authoritative state.
        return self.public_order(await self.reconcile(order))

    def public_order(self,order):
        return {'order_id':order['_id'],'session_id':order.get('session_id'),'status':order['state'],
                'payment_status':'paid' if order['state']=='paid' else 'unpaid','title':order['title'],
                'credits':order['credits'],'amount_total':order['amount_total'],'currency':order['currency'],
                'mode':'live' if order['livemode'] else 'test','created_at':order['created_at'].isoformat()+'Z'}

    async def history(self,user_id):
        await _student(self.db,user_id)
        orders=await self.db.payment_orders.find({'user_id':user_id}).sort('created_at',-1).limit(30).to_list(30)
        return {'orders':[self.public_order(order) for order in orders]}

    async def webhook(self,raw,signature):
        if not self.config.webhook_secret:raise HTTPException(503,'Webhook не настроен')
        try:event=self.provider.event(raw,signature)
        except (ValueError,stripe.SignatureVerificationError):raise HTTPException(400,'Неверная подпись Stripe')
        if event.get('type') not in EVENTS:return {'received':True}
        session=event['data']['object']
        integration=(session.get('metadata') or {}).get('integration')
        if integration not in ('numerom-credits-v1','numerom-full-report-v1'):return {'received':True}
        # Retrieve current state: an old failed/expired delivery cannot undo a paid order.
        try:current=await self.provider.retrieve(session['id'])
        except Exception:raise HTTPException(503,'Повторите доставку уведомления')
        if (current.get('metadata') or {}).get('integration')!=integration:
            raise HTTPException(400,'Параметры уведомления Stripe изменились')
        if integration=='numerom-full-report-v1':
            from services.full_reports import FullReports
            reports=FullReports(self.db,self.config,self.provider)
            await reports.materialize(await reports.accept_current(current,event['type']))
            return {'received':True}
        order=await self.fulfill(current)
        if order and order['state']!='paid':
            state=unpaid_state(order,current,event['type'])
            await self.db.payment_orders.update_one({'_id':order['_id'],'state':{'$ne':'paid'}},{'$set':{'state':state,'session_id':current['id']}})
        return {'received':True}
