"""Disposable-account live TEST-mode checkout drill; never enables real charging."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from dotenv import load_dotenv
load_dotenv(ROOT/'backend/.env')
from motor.motor_asyncio import AsyncIOMotorClient
import httpx
from auth import get_password_hash
from models import User
from services.payments import PaymentConfig,StripeProvider

STATE=ROOT/'backend/private/runtime/full-report-qa.json'
OUTPUT=ROOT/'artifacts/full-report-live-check.json'

async def main(action):
    config=PaymentConfig()
    if config.mode!='test':raise RuntimeError('Only existing Stripe TEST mode may be verified')
    mongo=AsyncIOMotorClient(os.environ['MONGO_URL'],serverSelectionTimeoutMS=5000)
    db=mongo[os.environ['MONGODB_DATABASE']]
    provider=StripeProvider(config)
    async with httpx.AsyncClient(timeout=30,headers={'Origin':'https://dmitriimalahov-gif.github.io'}) as client:
        if action=='prepare':
            if STATE.exists():raise RuntimeError('Finish or clean up the previous QA account first')
            if not config.enabled:raise RuntimeError('Configured Stripe sandbox is unavailable')
            uid='qa-full-report-'+uuid.uuid4().hex
            email=uid+'@example.invalid'
            password='Numerom-QA-666-Temporary!'
            user=User(id=uid,email=email,password_hash=get_password_hash(password),full_name='Проверка полного отчёта',name='Проверка',surname='Отчёта',birth_date='10.01.1982',credits_remaining=13)
            await db.users.insert_one(user.model_dump())
            state={'id':uid,'email':email,'password':password,'request_id':str(uuid.uuid4()),'base':os.environ['PUBLIC_API_URL'].rstrip('/')}
            STATE.write_text(json.dumps(state));STATE.chmod(0o600)
            login=await client.post(state['base']+'/api/auth/login',json={'email':email,'password':password});login.raise_for_status()
            state['token']=login.json()['access_token'];STATE.write_text(json.dumps(state))
            headers={'Authorization':'Bearer '+state['token']}
            catalog=await client.get(state['base']+'/api/full-reports/catalog',headers=headers);catalog.raise_for_status()
            result=await client.post(state['base']+'/api/full-reports/checkout',headers=headers,json={'birth_date':'10.01.1982','client':'mobile','request_id':state['request_id']});result.raise_for_status()
            state['order']=result.json();STATE.write_text(json.dumps(state))
            session=await provider.retrieve(state['order']['session_id'])
            assert session['amount_total']==666 and session['currency']=='eur' and session['livemode'] is False
            assert not (await db.full_report_orders.find_one({'_id':state['order']['order_id']})).get('report')
            print(json.dumps({'prepared':True,'mode':'test','amount_total':session['amount_total'],'currency':session['currency'],'email':email,'checkout_url':state['order']['url']},ensure_ascii=False))
        else:
            state=json.loads(STATE.read_text())
            if not state['id'].startswith('qa-full-report-'):raise RuntimeError('Not a disposable QA identity')
            if action=='verify':
                result=await client.get(state['base']+'/api/full-reports/'+state['order']['order_id'],headers={'Authorization':'Bearer '+state['token']});result.raise_for_status()
                order=result.json()
                session=await provider.retrieve(state['order']['session_id'])
                user=await db.users.find_one({'id':state['id']})
                result={'stripe_status':session['payment_status'],'mode':'test','amount_total':session['amount_total'],'currency':session['currency'],'report_status':order.get('report_status'),'sections':len(order.get('report',{}).get('sections',[])),'credits_unchanged':user['credits_remaining']==13}
                OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
            elif action=='cleanup':
                if state.get('order',{}).get('session_id'):
                    session=await provider.retrieve(state['order']['session_id'])
                    if session['status']=='open':await provider.expire(session['id'])
                await db.full_report_orders.delete_many({'user_id':state['id'],'livemode':False})
                await db.users.delete_one({'id':state['id']})
                STATE.unlink()
                print('Disposable QA account and test order removed; any unpaid Checkout expired.')
    mongo.close()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','verify','cleanup'])
    asyncio.run(main(p.parse_args().action))
