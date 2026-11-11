"""Execute the real legacy handlers in isolation, without importing server startup."""
import ast
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from fastapi.testclient import TestClient
from auth import create_access_token, get_current_user, get_password_hash
from models import LoginRequest, TokenResponse
from routers.admin_management import create_admin_management_router
from tests.test_admin_management import Collection


class LegacyCollection(Collection):
    async def update_one(self, query, update):
        result = await self.find_one_and_update(query, update)
        return SimpleNamespace(matched_count=int(result is not None))


def install_legacy_routes(app, db):
    """AST extraction preserves handler code/decorators but excludes global DB setup."""
    source = ast.parse((Path(__file__).resolve().parents[1] / 'server.py').read_text())
    selected = []
    for node in source.body:
        if isinstance(node, (ast.AsyncFunctionDef, ast.ClassDef)) and node.name in {
                'login_v2', 'get_all_users', 'update_user_credits', 'LegacyCreditChange',
                'get_credit_history', 'get_points_breakdown'}:
            selected.append(node)
        elif isinstance(node, ast.ImportFrom) and node.module in {
                'pydantic', 'routers.admin_management', 'services.admin_management'}:
            selected.append(node)
    async def record_transaction(**kwargs):
        pass
    api_router = APIRouter(prefix='/api')
    namespace = {
        'app': app, 'db': db, 'Depends': Depends, 'HTTPException': HTTPException,
        'api_router': api_router, 'Query': Query,
        'get_current_user': get_current_user, 'create_access_token': create_access_token,
        'LoginRequest': LoginRequest, 'TokenResponse': TokenResponse,
        'record_credit_transaction': record_transaction,
        'logger': SimpleNamespace(error=lambda *args: None),
    }
    exec(compile(ast.Module(body=selected, type_ignores=[]), 'server-legacy-routes', 'exec'), namespace)
    app.include_router(api_router)


class LegacyAdminSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password_hash = get_password_hash('correct-existing-password')

    def setUp(self):
        env = patch.dict(os.environ, {'SECRET_KEY': 'synthetic-legacy-route-contract-signing-key-only'})
        env.start()
        self.addCleanup(env.stop)
        self.db = SimpleNamespace(
            users=LegacyCollection([
                {'id': 'owner-id', 'email': 'owner@example.invalid', 'full_name': 'Owner',
                 'birth_date': '01.01.1980', 'is_super_admin': True,
                 'password_hash': self.password_hash, 'credits_remaining': 7},
                {'id': 'admin-id', 'email': 'admin@example.invalid', 'full_name': 'Admin',
                 'birth_date': '01.01.1980', 'is_admin': True,
                 'password_hash': self.password_hash, 'credits_remaining': 7},
                {'id': 'student-id', 'email': 'student@example.invalid', 'full_name': 'Student',
                 'birth_date': '01.01.1980', 'password_hash': self.password_hash,
                 'credits_remaining': 12},
            ]), lessons_v2=Collection(), personal_consultations=Collection(), credit_transactions=Collection(),
        )
        self.app = FastAPI()
        self.app.state.auth_db = self.db
        self.app.include_router(create_admin_management_router(self.db))
        install_legacy_routes(self.app, self.db)
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)
        self.admin_headers = self.headers('admin-id')

    def headers(self, user_id):
        return {'Authorization': 'Bearer ' + create_access_token({'sub': user_id})}

    def test_legacy_login_cannot_mint_victim_session_without_password(self):
        for identifier in ('owner-id', 'owner@example.invalid'):
            with self.subTest(identifier=identifier):
                result = self.client.post('/api/auth/login-v2', json={
                    'email': identifier, 'password': 'attacker-guess',
                })
                self.assertEqual(result.status_code, 401)
                self.assertNotIn('access_token', result.json())

    def test_legacy_login_uses_actual_account_password_and_current_access(self):
        result = self.client.post('/api/auth/login-v2', json={
            'email': 'owner@example.invalid', 'password': 'correct-existing-password',
        })
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['user']['id'], 'owner-id')
        self.assertNotIn('password_hash', result.text)
        protected = self.client.get('/api/admin/manage/overview', headers={
            'Authorization': 'Bearer ' + result.json()['access_token'],
        })
        self.assertEqual(protected.status_code, 200)
        self.db.users.documents[0]['is_disabled'] = True
        self.assertEqual(self.client.post('/api/auth/login-v2', json={
            'email': 'owner@example.invalid', 'password': 'correct-existing-password',
        }).status_code, 401)

    def test_legacy_credit_route_cannot_bypass_protected_targets_or_integer_bounds(self):
        protected = self.client.patch('/api/admin/users/owner-id/credits', headers=self.admin_headers,
                                      json={'credits_remaining': 20})
        self.assertEqual(protected.status_code, 403)
        for value in (-1, 1000001, True, 2.5, '20'):
            with self.subTest(value=value):
                result = self.client.patch('/api/admin/users/student-id/credits', headers=self.admin_headers,
                                           json={'credits_remaining': value})
                self.assertEqual(result.status_code, 422)
        detail = self.client.get('/api/admin/manage/users/student-id', headers=self.admin_headers).json()
        self.assertEqual(detail['user']['credits_remaining'], 12)

    def test_legacy_credit_change_keeps_response_shape_and_adds_safe_audit(self):
        result = self.client.patch('/api/admin/users/student-id/credits', headers=self.admin_headers,
                                   json={'credits_remaining': 20})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json(), {
            'message': 'Кредиты успешно обновлены', 'old_credits': 12,
            'new_credits': 20, 'difference': 8,
        })
        detail = self.client.get('/api/admin/manage/users/student-id', headers=self.admin_headers).json()
        self.assertEqual(len(detail['admin_history']), 1)
        self.assertEqual(detail['admin_history'][0]['before'], {'credits_remaining': 12})
        self.assertEqual(detail['admin_history'][0]['after'], {'credits_remaining': 20})
        self.assertTrue(detail['admin_history'][0]['reason'])

    def test_legacy_credit_route_conflicts_with_stale_balance_and_intervening_spend(self):
        stale = self.client.patch('/api/admin/users/student-id/credits', headers=self.admin_headers,
                                  json={'credits_remaining': 20, 'expected_balance': 10, 'reason': 'Correction'})
        self.assertEqual(stale.status_code, 409)
        self.db.users.before_mutation = lambda rows: rows[2].update(credits_remaining=9)
        raced = self.client.patch('/api/admin/users/student-id/credits', headers=self.admin_headers,
                                  json={'credits_remaining': 20})
        self.assertEqual(raced.status_code, 409)
        detail = self.client.get('/api/admin/manage/users/student-id', headers=self.admin_headers).json()
        self.assertEqual(detail['user']['credits_remaining'], 9)
        self.assertEqual(detail['admin_history'], [])

    def test_both_admin_routes_make_adjustments_visible_in_user_credit_history(self):
        legacy = self.client.patch('/api/admin/users/student-id/credits', headers=self.admin_headers,
                                   json={'credits_remaining': 20, 'reason': 'Internal support note'})
        self.assertEqual(legacy.status_code, 200)
        debit = self.client.patch('/api/admin/manage/users/student-id/credits', headers=self.admin_headers,
                                  json={'amount': -3, 'expected_balance': 20, 'reason': 'Internal reversal note'})
        self.assertEqual(debit.status_code, 200)
        user_headers = self.headers('student-id')
        history = self.client.get('/api/user/credit-history', headers=user_headers).json()
        self.assertEqual(history['total'], 2)
        self.assertEqual([item['amount'] for item in history['transactions']], [-3, 8])
        self.assertEqual([item['transaction_type'] for item in history['transactions']], ['debit', 'credit'])
        self.assertNotIn('Internal support note', str(history))
        self.assertNotIn('Internal reversal note', str(history))
        breakdown = self.client.get('/api/user/points-breakdown', headers=user_headers).json()
        self.assertEqual((breakdown['admin_points'], breakdown['total_balance']), (8, 17))

    def test_failed_history_delivery_retries_without_losing_or_duplicating_credit_change(self):
        for failed_stage in ('insert', 'cleanup'):
            with self.subTest(failed_stage=failed_stage):
                self.setUp()
                if failed_stage == 'insert':
                    original = self.db.credit_transactions.update_one
                    async def fail_once(*args, **kwargs):
                        self.db.credit_transactions.update_one = original
                        raise RuntimeError('Synthetic history insertion failure')
                    self.db.credit_transactions.update_one = fail_once
                else:
                    original = self.db.users.update_one
                    async def fail_once(*args, **kwargs):
                        self.db.users.update_one = original
                        raise RuntimeError('Synthetic cleanup failure after history insertion')
                    self.db.users.update_one = fail_once
                changed = self.client.patch('/api/admin/manage/users/student-id/credits', headers=self.admin_headers,
                                            json={'amount': 8, 'expected_balance': 12, 'reason': 'Support adjustment'})
                self.assertEqual(changed.status_code, 200)
                self.assertEqual(changed.json()['user']['credits_remaining'], 20)
                user_headers = self.headers('student-id')
                for _ in range(2):
                    history = self.client.get('/api/user/credit-history', headers=user_headers).json()
                    self.assertEqual(history['total'], 1)
                    self.assertEqual(history['transactions'][0]['amount'], 8)
                breakdown = self.client.get('/api/user/points-breakdown', headers=user_headers).json()
                self.assertEqual((breakdown['admin_points'], breakdown['total_balance']), (8, 20))

    def test_points_breakdown_also_retries_pending_history_delivery(self):
        original = self.db.credit_transactions.update_one
        async def fail_once(*args, **kwargs):
            self.db.credit_transactions.update_one = original
            raise RuntimeError('Synthetic history insertion failure')
        self.db.credit_transactions.update_one = fail_once
        self.client.patch('/api/admin/users/student-id/credits', headers=self.admin_headers,
                          json={'credits_remaining': 20})
        user_headers = self.headers('student-id')
        breakdown = self.client.get('/api/user/points-breakdown', headers=user_headers).json()
        self.assertEqual((breakdown['admin_points'], breakdown['total_balance']), (8, 20))
        self.assertEqual(self.client.get('/api/user/credit-history', headers=user_headers).json()['total'], 1)

    def test_pending_history_survives_bounded_admin_audit_rollover(self):
        original = self.db.credit_transactions.update_one
        async def fail_once(*args, **kwargs):
            self.db.credit_transactions.update_one = original
            raise RuntimeError('Synthetic history insertion failure')
        self.db.credit_transactions.update_one = fail_once
        self.client.patch('/api/admin/users/student-id/credits', headers=self.admin_headers,
                          json={'credits_remaining': 20})
        for index in range(100):
            result = self.client.patch('/api/admin/manage/users/student-id/access', headers=self.admin_headers,
                                       json={'is_disabled': index % 2 == 0, 'reason': 'Access review'})
            self.assertEqual(result.status_code, 200)
        detail = self.client.get('/api/admin/manage/users/student-id', headers=self.admin_headers).json()
        self.assertEqual(len(detail['admin_history']), 100)
        self.assertTrue(all(event['action'] == 'access' for event in detail['admin_history']))
        user_headers = {'Authorization': 'Bearer ' + create_access_token({'sub': 'student-id', 'auth_version': 100})}
        history = self.client.get('/api/user/credit-history', headers=user_headers).json()
        self.assertEqual(history['total'], 1)
        self.assertEqual(history['transactions'][0]['amount'], 8)
