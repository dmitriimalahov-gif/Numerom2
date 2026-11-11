"""HTTP contracts against a small isolated repository; no production database."""
import copy
import os
from unittest.mock import patch
import io
import sys
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from datetime import datetime, timedelta
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import FastAPI
from fastapi.testclient import TestClient
from auth import get_current_user, get_password_hash
from routers.accounts import create_accounts_router

class Users:
    def __init__(self, data): self.data = data
    async def find_one(self, query):
        return copy.deepcopy(self.data) if self.data and all(self.data.get(k) == v for k, v in query.items()) else None
    async def update_one(self, query, update):
        if await self.find_one(query): self.data.update(update['$set'])

class AccountContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.password_hash = get_password_hash('test-password-only')
    def setUp(self):
        self.key = patch.dict(os.environ, {"JWT_SECRET_KEY":"synthetic-account-tests-secret-more-than32"}); self.key.start()
        self.addCleanup(self.key.stop)
        self.db = type('Repository', (), {})()
        self.db.users = Users({'id':'u1','email':'test@example.invalid','password_hash':self.password_hash,'full_name':'Anna','name':'Anna','surname':'Li','birth_date':'02.03.1990','credits_remaining':12,'is_admin':False,'is_super_admin':False,'private_secret':'hidden'})
        self.app = FastAPI()
        self.app.include_router(create_accounts_router(self.db))
        self.app.dependency_overrides[get_current_user] = lambda: {'user_id':'u1','role':'user'}
        self.client = TestClient(self.app)
    def test_login_returns_token_and_never_echoes_password_or_logs_fragments(self):
        output = io.StringIO()
        with redirect_stdout(output): response = self.client.post('/api/auth/login', json={'email':'test@example.invalid','password':'test-password-only'})
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json()['access_token'])
        self.assertNotIn('password_hash',response.json()['user'])
        self.assertEqual(output.getvalue(),'')
    def test_login_level_matches_current_profile_without_refresh(self):
        self.db.users.data['level'] = 7
        response = self.client.post('/api/auth/login', json={
            'email':'test@example.invalid', 'password':'test-password-only', 'level':999})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user'].get('level'), 7)
        self.assertEqual(response.json()['user']['level'], self.client.get('/api/user/profile-v2').json()['level'])
        self.assertEqual(self.db.users.data['level'], 7)
        self.assertNotIn('private_secret', response.json()['user'])
    def test_login_missing_stored_level_defaults_to_first_level(self):
        self.assertNotIn('level', self.db.users.data)
        response = self.client.post('/api/auth/login', json={
            'email':'test@example.invalid', 'password':'test-password-only'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user'].get('level'), 1)
    def test_bad_password_and_unknown_user_have_same_status(self):
        for email in ['test@example.invalid','missing@example.invalid']:
            response=self.client.post('/api/auth/login',json={'email':email,'password':'wrong'})
            self.assertEqual(response.status_code,401)
            self.assertEqual(response.json()['detail'],'Invalid credentials')
    def test_expired_subscription_is_disabled_on_login(self):
        self.db.users.data.update(is_premium=True,subscription_type='monthly',subscription_expires_at=datetime.utcnow()-timedelta(days=1))
        response=self.client.post('/api/auth/login',json={'email':'test@example.invalid','password':'test-password-only'})
        self.assertEqual(response.status_code,200)
        self.assertFalse(response.json()['user']['is_premium'])
        self.assertIsNone(self.db.users.data['subscription_expires_at'])
    def test_profile_returns_current_balance_without_private_data(self):
        response=self.client.get('/api/user/profile-v2')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['credits_remaining'],12)
        self.assertNotIn('password_hash',response.json())
        self.assertNotIn('private_secret',response.json())
    def test_missing_user_is_404(self):
        self.db.users.data=None
        self.assertEqual(self.client.get('/api/user/profile-v2').status_code,404)
    def test_update_trims_recalculates_name_and_does_not_escalate_or_leak(self):
        response=self.client.patch('/api/user/profile-v2',json={'name':'  Bob  ','surname':'Li','credits_remaining':99999,'is_admin':True})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['name'],'Bob')
        self.assertEqual(response.json()['full_name_number'],4)  # B+O+B+L+I=40
        self.assertEqual(self.db.users.data['credits_remaining'],12)
        self.assertFalse(self.db.users.data['is_admin'])
        self.assertNotIn('password_hash',response.json())
        self.assertNotIn('private_secret',response.json())
    def test_invalid_birth_date_is_rejected_without_mutation(self):
        response=self.client.patch('/api/user/profile-v2',json={'birth_date':'31.02.2000'})
        self.assertEqual(response.status_code,422)
        self.assertEqual(self.db.users.data['birth_date'],'02.03.1990')
    def test_only_forbidden_fields_cannot_update_account(self):
        self.assertEqual(self.client.patch('/api/user/profile-v2',json={'is_admin':True}).status_code,400)
    def test_anonymous_profile_is_401(self):
        self.app.dependency_overrides.clear()
        self.assertEqual(self.client.get('/api/user/profile-v2').status_code,401)

if __name__=='__main__': unittest.main()
