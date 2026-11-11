"""Disposable admin/recovery browser fixture, in memory; never sends email.

Start with a synthetic JWT_SECRET_KEY and backend on 8013, frontend on 5132.
The seeded accounts and password exist only in this process.
"""
from datetime import datetime
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth import get_password_hash
from routers.accounts import create_accounts_router
from routers.admin_management import create_admin_management_router
from routers.recovery import create_recovery_router
from tests.test_admin_management import Collection
from tests.recovery_support import Collection as Limits, Mailbox

seed = [
    {'id':'preview-owner','email':'owner@example.invalid','full_name':'Администратор · тест',
     'name':'Администратор','birth_date':'02.03.1990','is_super_admin':True,'is_admin':True,
     'credits_remaining':100,'created_at':datetime(2026,10,1)},
    {'id':'preview-anna','email':'anna@example.invalid','full_name':'Анна · тест',
     'name':'Анна','birth_date':'12.05.1992','credits_remaining':12,'created_at':datetime(2026,10,2)},
    {'id':'preview-oleg','email':'oleg@example.invalid','full_name':'Олег · тест',
     'name':'Олег','birth_date':'02.03.1988','credits_remaining':0,'created_at':datetime(2026,10,3)},
]
for user in seed: user['password_hash'] = get_password_hash('preview-only-password')
repository = SimpleNamespace(users=Collection(seed), recovery_limits=Limits(),
    lessons_v2=Collection(), personal_consultations=Collection(), credit_transactions=Collection())
mailbox=Mailbox(); mailbox.configured=False
app=FastAPI(title='NumerOM disposable admin preview')
app.state.auth_db=repository
app.add_middleware(CORSMiddleware,allow_origins=['http://127.0.0.1:5132'],allow_methods=['GET','POST','PATCH'],allow_headers=['Authorization','Content-Type'])
app.include_router(create_accounts_router(repository))
app.include_router(create_admin_management_router(repository))
app.include_router(create_recovery_router(repository,mailer=mailbox,reset_url='http://127.0.0.1:5132/reset-password'))
