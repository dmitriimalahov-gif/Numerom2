import asyncio
import hashlib
import os
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlsplit, parse_qs
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fastapi import FastAPI
from fastapi.testclient import TestClient
from auth import get_password_hash, ensure_super_admin_exists
from routers.accounts import create_accounts_router
from recovery_support import Collection, Mailbox

class RecoveryContracts(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {'JWT_SECRET_KEY':'synthetic-recovery-test-secret-32-characters-only'}, clear=False); self.environment.start()
        self.db = SimpleNamespace(users=Collection([{'id':'u1','email':'anna@example.invalid','full_name':'Anna','birth_date':'02.03.1990','password_hash':get_password_hash('old-password-only'),'credits_remaining':12}]), recovery_limits=Collection(), admin_users=Collection())
        self.mail = Mailbox(); self.now = datetime(2026,10,15,12)
        self.app = FastAPI(); self.app.state.auth_db = self.db
        self.app.include_router(create_accounts_router(self.db))
        # Import inside test setup so a missing feature is reported as the intended red.
        from routers.recovery import create_recovery_router
        self.app.include_router(create_recovery_router(self.db, mailer=self.mail, reset_url='https://numerom.example/reset-password', clock=lambda:self.now))
        self.client = TestClient(self.app)
    def tearDown(self): self.client.close(); self.environment.stop()
    def request_link(self, email='anna@example.invalid'):
        return self.client.post('/api/auth/forgot-password',json={'email':email})
    def token(self): return parse_qs(urlsplit(self.mail.messages[0]['url']).fragment)['token'][0]
    def login(self, password): return self.client.post('/api/auth/login',json={'email':'anna@example.invalid','password':password})
    def test_unknown_and_known_email_have_identical_public_response(self):
        known=self.request_link(); self.now+=timedelta(seconds=11)
        unknown=self.request_link('nobody@example.invalid')
        self.assertEqual(known.status_code,202); self.assertEqual(unknown.json(),known.json())
        self.assertNotIn('token',known.text); self.assertEqual(len(self.mail.messages),1)
    def test_only_hash_is_stored_and_link_uses_configured_origin(self):
        self.request_link('ANNA@example.invalid'); token=self.token()
        record=self.db.users.documents[0]
        self.assertNotIn(token,str(record)); self.assertEqual(record['password_reset_hash'],hashlib.sha256(token.encode()).hexdigest())
        self.assertEqual(record['password_reset_expires_at'],self.now+timedelta(minutes=30))
        self.assertTrue(self.mail.messages[0]['url'].startswith('https://numerom.example/reset-password#token='))
    def test_valid_reset_changes_password_revokes_sessions_and_is_single_use(self):
        old=self.login('old-password-only').json()['access_token']; self.request_link(); token=self.token()
        reset=self.client.post('/api/auth/reset-password',json={'token':token,'password':'a-long-new-password'})
        self.assertEqual(reset.status_code,200); self.assertNotIn('access_token',reset.json())
        self.assertEqual(self.login('old-password-only').status_code,401)
        fresh=self.login('a-long-new-password'); self.assertEqual(fresh.status_code,200)
        self.assertEqual(self.client.get('/api/user/profile-v2',headers={'Authorization':'Bearer '+old}).status_code,401)
        self.assertEqual(self.client.get('/api/user/profile-v2',headers={'Authorization':'Bearer '+fresh.json()['access_token']}).status_code,200)
        self.now+=timedelta(seconds=2)
        self.assertEqual(self.client.post('/api/auth/reset-password',json={'token':token,'password':'another-long-password'}).status_code,400)
        self.assertNotIn('password_reset_hash',self.db.users.documents[0])
        self.assertTrue(any(m.get('changed') for m in self.mail.messages))
    def test_expired_and_invalid_token_do_not_change_password(self):
        self.request_link(); token=self.token(); before=self.db.users.documents[0]['password_hash']; self.now+=timedelta(minutes=31)
        for value in [token,'x'*43]:
            self.now+=timedelta(seconds=2)
            self.assertEqual(self.client.post('/api/auth/reset-password',json={'token':value,'password':'valid-long-password'}).status_code,400)
        self.assertEqual(self.db.users.documents[0]['password_hash'],before)
    def test_weak_or_bcrypt_truncating_password_rejected_without_consuming_link(self):
        self.request_link(); token=self.token()
        for value in ['short','я'*37]:
            self.assertEqual(self.client.post('/api/auth/reset-password',json={'token':token,'password':value}).status_code,422)
        self.assertEqual(self.client.post('/api/auth/reset-password',json={'token':token,'password':'valid-long-password'}).status_code,200)
    def test_repeated_requests_are_throttled_without_account_disclosure(self):
        first=self.request_link(); second=self.request_link()
        self.assertEqual(first.json(),second.json()); self.assertEqual(len(self.mail.messages),1)
    def test_disabled_account_cannot_login_or_use_old_session(self):
        token=self.login('old-password-only').json()['access_token']; self.db.users.documents[0]['is_disabled']=True
        self.assertEqual(self.login('old-password-only').status_code,401)
        self.assertEqual(self.client.get('/api/user/profile-v2',headers={'Authorization':'Bearer '+token}).status_code,401)
    def test_missing_mail_configuration_reports_service_unavailable(self):
        self.mail.configured=False
        self.assertEqual(self.request_link().status_code,503); self.assertEqual(self.mail.messages,[])
    def test_mail_failure_removes_pending_token_and_does_not_echo_internal_error(self):
        self.mail.fail=True; response=self.request_link()
        self.assertEqual(response.status_code,202); self.assertNotIn('synthetic',response.text)
        self.assertNotIn('password_reset_hash',self.db.users.documents[0])
    def test_inflight_request_cannot_restore_token_after_password_version_changes(self):
        original=self.db.users.update_one
        async def change_password_before_save(query, update, **kwargs):
            if 'password_reset_hash' in update.get('$set', {}):
                self.db.users.documents[0]['auth_version']=1
            return await original(query, update, **kwargs)
        self.db.users.update_one=change_password_before_save
        self.assertEqual(self.request_link().status_code,202)
        self.assertEqual(self.mail.messages,[])
        self.assertNotIn('password_reset_hash',self.db.users.documents[0])
    def test_bootstrap_never_resets_existing_admin_password(self):
        self.db.users.documents[0]['is_super_admin']=True
        before=self.db.users.documents[0]['password_hash']
        with patch.dict(os.environ,{'SUPER_ADMIN_EMAIL':'anna@example.invalid','SUPER_ADMIN_PASSWORD':'new-bootstrap-password'}):
            asyncio.run(ensure_super_admin_exists(self.db))
        self.assertEqual(self.db.users.documents[0]['password_hash'],before)
    def test_no_hardcoded_admin_is_created_when_bootstrap_not_configured(self):
        before=len(self.db.users.documents)
        with patch.dict(os.environ,{'SUPER_ADMIN_EMAIL':'','SUPER_ADMIN_PASSWORD':''}): asyncio.run(ensure_super_admin_exists(self.db))
        self.assertEqual(len(self.db.users.documents),before)

if __name__=='__main__': unittest.main()
