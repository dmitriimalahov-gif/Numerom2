"""Disposable browser QA: isolated Mongo container 27039 only, no production env."""
import os
from contextlib import asynccontextmanager

if os.environ.get('NUMEROM_RELATIONSHIPS_QA') != '1':
    raise RuntimeError('Enable only for isolated browser QA')
os.environ['SECRET_KEY'] = 'isolated-relationships-preview-signing-key-only'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from auth import get_password_hash
from models import User
from routers.accounts import create_accounts_router
from routers.relationships import create_relationships_router

mongo = AsyncIOMotorClient('mongodb://127.0.0.1:27039', serverSelectionTimeoutMS=4000)
db = mongo['numerom_relationships_browser_qa']

@asynccontextmanager
async def lifespan(app):
    user = User(id='relationships-qa',email='relationships@example.invalid',
                password_hash=get_password_hash('preview-only'),full_name='Анна',
                name='Анна',birth_date='10.01.1982',credits_remaining=20)
    await db.users.update_one({'id':user.id},{'$setOnInsert':user.model_dump()},upsert=True)
    yield
    mongo.close()

app=FastAPI(lifespan=lifespan)
app.state.auth_db=db
app.add_middleware(CORSMiddleware,allow_origins=['http://127.0.0.1:5132'],allow_methods=['GET','POST','PATCH'],allow_headers=['Authorization','Content-Type'])
app.include_router(create_accounts_router(db))
app.include_router(create_relationships_router(db))
