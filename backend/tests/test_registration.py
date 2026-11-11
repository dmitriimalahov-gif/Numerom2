"""Execute the real registration handler without touching application accounts."""
import ast
from datetime import datetime
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from fastapi import FastAPI,APIRouter,HTTPException,Request
from models import User,UserCreate,TokenResponse,CreditTransaction
from auth import create_user_response

class RegistrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_mobile_signup_without_city_creates_account_and_bonus(self):
        source=ast.parse((Path(__file__).resolve().parents[1]/'server.py').read_text())
        node=next(n for n in source.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='register')
        users=SimpleNamespace(find_one=AsyncMock(return_value=None),insert_one=AsyncMock())
        history=SimpleNamespace(insert_one=AsyncMock())
        app=FastAPI();router=APIRouter(prefix='/api')
        scope={'api_router':router,'UserCreate':UserCreate,'TokenResponse':TokenResponse,'Request':Request,
            'User':User,'CreditTransaction':CreditTransaction,'db':SimpleNamespace(users=users,credit_transactions=history),
            'HTTPException':HTTPException,'get_password_hash':lambda p:'fixture-password-hash',
            'create_access_token':lambda claims:'fixture-session-token','create_user_response':create_user_response}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-registration-handler','exec'),scope)
        app.include_router(router)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app,raise_app_exceptions=False),base_url='http://test') as client:
            r=await client.post('/api/auth/register',json={'email':'registration@example.invalid','password':'test-password-123','full_name':'Test Student','birth_date':'02.03.1990'})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()['user']['credits_remaining'],10)
        self.assertEqual(r.json()['access_token'],'fixture-session-token')
        users.insert_one.assert_awaited_once();history.insert_one.assert_awaited_once()
        self.assertEqual(users.insert_one.call_args.args[0]['credits_remaining'],10)
        self.assertEqual(history.insert_one.call_args.args[0]['amount'],10)
        self.assertNotIn('password_hash',r.json()['user'])
