"""Disposable UI fixture. No MongoDB, no real accounts, no payments.
Run from backend: .venv/bin/uvicorn tests.preview_app:app --host 127.0.0.1 --port 8013
Credentials are synthetic and only valid in this in-memory fixture.
"""
import copy
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from auth import get_current_user, get_password_hash
from routers.accounts import create_accounts_router
from numerology import calculate_personal_numbers

class Users:
    def __init__(self):
        self.document = {'id':'preview-user','email':'preview@example.invalid',
            'password_hash':get_password_hash('preview-only'),'full_name':'Тестовый профиль',
            'name':'Анна','surname':'','birth_date':'02.03.1990','city':'Тестовый город','credits_remaining':12,'level':1}
    async def find_one(self, query):
        return copy.deepcopy(self.document) if all(self.document.get(k)==v for k,v in query.items()) else None
    async def update_one(self, query, update):
        if await self.find_one(query): self.document.update(update['$set'])

class Repository:
    users = Users()
repository = Repository()
app = FastAPI(title='NumerOM isolated UI fixture')
app.state.auth_db = repository
app.add_middleware(CORSMiddleware, allow_origins=['http://127.0.0.1:5131'], allow_methods=['GET','POST','PATCH'], allow_headers=['Authorization','Content-Type'])
app.include_router(create_accounts_router(repository))

@app.get('/api/numerology/costs')
async def costs(user=Depends(get_current_user)):
    return {'personal_numbers':1}

@app.post('/api/numerology/personal-numbers')
async def numbers(birth_date:str, user=Depends(get_current_user)):
    result=calculate_personal_numbers(birth_date)
    repository.users.document['credits_remaining']-=1
    return dict(result, full_name_number=0)

lesson={'id':'preview-lesson','title':'Знакомство с числами','description':'Тестовый материал для проверки мобильного интерфейса.','level':1,'theory':[{'title':'Первый шаг','content':'Этот текст загружен через API из изолированной проверки. Учебные данные и реальные аккаунты не используются.'}]}
@app.get('/api/learning-v2/lessons')
async def lessons(user=Depends(get_current_user)):
    return {'lessons':[lesson], 'user_level':1}
@app.get('/api/learning-v2/lessons/{lesson_id}')
async def detail(lesson_id:str,user=Depends(get_current_user)):
    return {'lesson':lesson,'progress':{}}
