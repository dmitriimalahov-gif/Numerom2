"""Admin HTTP contracts with an isolated Mongo-style adapter, never live data."""
import copy
import os
import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import FastAPI
from fastapi.testclient import TestClient
from auth import create_access_token, get_current_user
from routers.admin_management import create_admin_management_router


def matches(document, query):
    for key, condition in query.items():
        if key == '$or':
            if not any(matches(document, item) for item in condition):
                return False
        elif isinstance(condition, dict):
            value = document.get(key)
            if '$ne' in condition and value == condition['$ne']:
                return False
            if '$exists' in condition and (key in document) != condition['$exists']:
                return False
            if '$regex' in condition and not re.search(
                    condition['$regex'], str(value or ''),
                    re.IGNORECASE if 'i' in condition.get('$options', '') else 0):
                return False
        elif document.get(key) != condition:
            return False
    return True


def project(document, projection=None):
    if document is None:
        return None
    if projection is None:
        return copy.deepcopy(document)
    result = {}
    for key, value in projection.items():
        if not value or key not in document:
            continue
        result[key] = copy.deepcopy(document[key])
        if isinstance(value, dict) and '$slice' in value:
            result[key] = result[key][value['$slice']:]
    return result


class Cursor:
    def __init__(self, documents):
        self.documents = documents

    def sort(self, key, direction=None):
        keys = key if isinstance(key, list) else [(key, direction)]
        for field, order in reversed(keys):
            self.documents.sort(key=lambda item: str(item.get(field) or ''), reverse=order < 0)
        return self

    def skip(self, amount):
        self.documents = self.documents[amount:]
        return self

    def limit(self, amount):
        self.documents = self.documents[:amount]
        return self

    async def to_list(self, length):
        return copy.deepcopy(self.documents[:length])


class Collection:
    def __init__(self, documents=()):
        self.documents = copy.deepcopy(list(documents))
        self.before_mutation = None

    async def find_one(self, query, projection=None):
        return project(next((row for row in self.documents if matches(row, query)), None), projection)

    def find(self, query, projection=None):
        return Cursor([project(row, projection) for row in self.documents if matches(row, query)])

    async def count_documents(self, query):
        return sum(matches(row, query) for row in self.documents)

    async def find_one_and_update(self, query, update, projection=None, return_document=None):
        if self.before_mutation:
            action, self.before_mutation = self.before_mutation, None
            action(self.documents)
        for row in self.documents:
            if not matches(row, query):
                continue
            updated = copy.deepcopy(row)
            updated.update(copy.deepcopy(update.get('$set', {})))
            for key, delta in update.get('$inc', {}).items():
                updated[key] = updated.get(key, 0) + delta
            for key, instruction in update.get('$push', {}).items():
                updated.setdefault(key, []).extend(copy.deepcopy(instruction['$each']))
                if '$slice' in instruction:
                    updated[key] = updated[key][instruction['$slice']:]
            for key, condition in update.get('$pull', {}).items():
                updated[key] = [item for item in updated.get(key, []) if not matches(item, condition)]
            row.clear()
            row.update(updated)
            return project(row, projection)
        return None

    async def update_one(self, query, update, upsert=False):
        result = await self.find_one_and_update(query, update)
        if result is not None:
            return SimpleNamespace(matched_count=1)
        if upsert:
            self.documents.append({**copy.deepcopy(query), **copy.deepcopy(update.get('$setOnInsert', {}))})
        return SimpleNamespace(matched_count=0)


class AdminManagementContracts(unittest.TestCase):
    def setUp(self):
        self.db = SimpleNamespace(
            users=Collection([
                {'id': 'owner', 'email': 'owner@example.invalid', 'is_super_admin': True},
                {'id': 'admin', 'email': 'admin@example.invalid', 'is_admin': True},
                {'id': 'u1', 'email': 'anna@example.invalid', 'full_name': 'Anna Stone',
                 'name': 'Anna', 'credits_remaining': 12, 'level': 1, 'created_at': '2026-10-01',
                 'password_hash': 'never-echo-this', 'password_reset_hash': 'also-secret',
                 'private_secret': 'hidden'},
                {'id': 'u2', 'email': 'bo@example.invalid', 'full_name': 'Bo Stone',
                 'is_disabled': True, 'credits_remaining': 0},
            ]),
            lessons_v2=Collection([{'id': 'lesson1'}, {'id': 'lesson2'}]),
            personal_consultations=Collection([{'id': 'consultation1'}]),
            credit_transactions=Collection(),
        )
        self.app = FastAPI()
        self.app.include_router(create_admin_management_router(self.db))
        self.as_user('admin')
        self.client = TestClient(self.app)

    def as_user(self, user_id, role='admin'):
        self.app.dependency_overrides[get_current_user] = lambda: {'user_id': user_id, 'role': role}

    def test_overview_counts_current_collections_and_requires_current_admin(self):
        response = self.client.get('/api/admin/manage/overview')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'users_total': 4, 'users_disabled': 1, 'admins_total': 2,
            'lessons_total': 2, 'consultations_total': 1,
        })
        self.as_user('u1', role='admin')
        self.assertEqual(self.client.get('/api/admin/manage/overview').status_code, 403)
        self.app.dependency_overrides.clear()
        self.assertEqual(self.client.get('/api/admin/manage/overview').status_code, 401)

    def test_user_search_is_literal_paginated_and_returns_only_known_fields(self):
        response = self.client.get('/api/admin/manage/users?q=STONE&page_size=1&page=1')
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual((result['total'], result['page'], result['page_size']), (2, 1, 1))
        self.assertEqual(result['users'][0], {
            'id': 'u1', 'email': 'anna@example.invalid', 'full_name': 'Anna Stone',
            'name': 'Anna', 'credits_remaining': 12, 'level': 1, 'created_at': '2026-10-01',
            'is_admin': False, 'is_super_admin': False, 'is_disabled': False,
        })
        second = self.client.get('/api/admin/manage/users?q=STONE&page_size=1&page=2').json()
        self.assertEqual([user['id'] for user in second['users']], ['u2'])
        self.assertEqual(self.client.get('/api/admin/manage/users?q=.*').json()['total'], 0)
        for query in ('page=0', 'page_size=101', 'page_size=0'):
            self.assertEqual(self.client.get('/api/admin/manage/users?' + query).status_code, 422)

    def test_detail_returns_bounded_safe_history_and_rejects_disabled_actor(self):
        self.db.users.documents[2]['admin_history'] = [
            {'id': str(index), 'actor_id': 'owner', 'action': 'credits',
             'reason': 'Correction', 'created_at': '2026-10-01',
             'before': {'credits_remaining': 10, 'password_hash': 'never-echo-this'},
             'after': {'credits_remaining': 12, 'reset_token_hash': 'also-secret'},
             'private_secret': 'hidden'} for index in range(105)
        ]
        response = self.client.get('/api/admin/manage/users/u1')
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['user']['id'], 'u1')
        self.assertEqual(len(result['admin_history']), 100)
        self.assertEqual(result['admin_history'][0], {
            'id': '5', 'actor_id': 'owner', 'action': 'credits',
            'reason': 'Correction', 'created_at': '2026-10-01',
            'before': {'credits_remaining': 10}, 'after': {'credits_remaining': 12},
        })
        self.assertNotIn('never-echo-this', response.text)
        self.assertNotIn('also-secret', response.text)
        self.assertNotIn('hidden', response.text)
        self.assertEqual(self.client.get('/api/admin/manage/users/missing').status_code, 404)
        self.db.users.documents[1]['is_disabled'] = True
        self.assertEqual(self.client.get('/api/admin/manage/users/u1').status_code, 403)
        self.assertEqual(self.client.get('/api/admin/manage/users').status_code, 403)

    def test_access_changes_are_audited_and_require_current_authority(self):
        response = self.client.patch('/api/admin/manage/users/u1/access', json={
            'is_disabled': True, 'reason': '  Requested suspension  ',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['user']['is_disabled'])
        detail = self.client.get('/api/admin/manage/users/u1').json()
        self.assertEqual(len(detail['admin_history']), 1)
        event = detail['admin_history'][0]
        self.assertEqual(event['action'], 'access')
        self.assertEqual(event['actor_id'], 'admin')
        self.assertEqual(event['reason'], 'Requested suspension')
        self.assertEqual(event['before'], {'is_disabled': False})
        self.assertEqual(event['after'], {'is_disabled': True})
        self.assertTrue(event['id'])
        self.assertTrue(event['created_at'])
        promotion = {'is_admin': True, 'reason': 'New content manager'}
        self.assertEqual(self.client.patch('/api/admin/manage/users/u1/access', json=promotion).status_code, 403)
        self.as_user('owner', role='user')
        promoted = self.client.patch('/api/admin/manage/users/u1/access', json=promotion)
        self.assertEqual(promoted.status_code, 200)
        self.assertTrue(promoted.json()['user']['is_admin'])
        self.as_user('admin')
        self.assertEqual(self.client.patch('/api/admin/manage/users/u1/access', json={
            'is_disabled': False, 'reason': 'Unblock',
        }).status_code, 403)

    def test_access_protects_self_superadmin_and_invalid_or_empty_updates(self):
        for actor, target in [('admin', 'admin'), ('admin', 'owner'), ('owner', 'owner')]:
            self.as_user(actor)
            response = self.client.patch(f'/api/admin/manage/users/{target}/access', json={
                'is_disabled': True, 'reason': 'Block',
            })
            self.assertEqual(response.status_code, 403)
        self.as_user('owner')
        for payload in ({'reason': 'Empty'}, {'is_disabled': False, 'reason': 'Already enabled'}):
            self.assertEqual(self.client.patch('/api/admin/manage/users/u1/access', json=payload).status_code, 400)
        for payload in (
            {'is_disabled': True, 'reason': '   '},
            {'is_disabled': 'false', 'reason': 'Invalid flag'},
            {'is_admin': None, 'reason': 'Invalid null'},
            {'is_super_admin': True, 'reason': 'Escalation'},
        ):
            self.assertEqual(self.client.patch('/api/admin/manage/users/u1/access', json=payload).status_code, 422)
        self.assertEqual(self.client.get('/api/admin/manage/users/u1').json()['admin_history'], [])

    def test_access_rejects_target_promoted_while_request_is_in_progress(self):
        def promote_concurrently(documents):
            documents[2]['is_admin'] = True
        self.db.users.before_mutation = promote_concurrently
        response = self.client.patch('/api/admin/manage/users/u1/access', json={
            'is_disabled': True, 'reason': 'Suspend',
        })
        self.assertEqual(response.status_code, 409)
        detail = self.client.get('/api/admin/manage/users/u1').json()
        self.assertTrue(detail['user']['is_admin'])
        self.assertFalse(detail['user']['is_disabled'])
        self.assertEqual(detail['admin_history'], [])

    def test_credit_delta_is_audited_and_stale_resubmission_cannot_apply_twice(self):
        payload = {'amount': 8, 'expected_balance': 12, 'reason': '  Support adjustment  '}
        response = self.client.patch('/api/admin/manage/users/u1/credits', json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['credits_remaining'], 20)
        self.assertEqual(self.client.patch('/api/admin/manage/users/u1/credits', json=payload).status_code, 409)
        detail = self.client.get('/api/admin/manage/users/u1').json()
        self.assertEqual(detail['user']['credits_remaining'], 20)
        self.assertEqual(len(detail['admin_history']), 1)
        event = detail['admin_history'][0]
        self.assertEqual(event['action'], 'credits')
        self.assertEqual(event['actor_id'], 'admin')
        self.assertEqual(event['reason'], 'Support adjustment')
        self.assertEqual(event['before'], {'credits_remaining': 12})
        self.assertEqual(event['after'], {'credits_remaining': 20})
        debited = self.client.patch('/api/admin/manage/users/u1/credits', json={
            'amount': -20, 'expected_balance': 20, 'reason': 'Refund correction',
        })
        self.assertEqual(debited.status_code, 200)
        self.assertEqual(debited.json()['user']['credits_remaining'], 0)

    def test_credit_amounts_cannot_escape_valid_integer_balance_range(self):
        valid = {'amount': 1, 'expected_balance': 12, 'reason': 'Adjustment'}
        for invalid in (
            {'amount': 0}, {'amount': True}, {'amount': 1.5}, {'amount': '1'},
            {'amount': 1000001}, {'amount': -1000001},
            {'expected_balance': -1}, {'expected_balance': True},
            {'expected_balance': 1000001}, {'reason': '   '}, {'reason': 'x' * 501},
            {'credits_remaining': 999999},
        ):
            with self.subTest(invalid=invalid):
                response = self.client.patch('/api/admin/manage/users/u1/credits', json={**valid, **invalid})
                self.assertEqual(response.status_code, 422)
        for amount in (-13, 999989):
            response = self.client.patch('/api/admin/manage/users/u1/credits', json={**valid, 'amount': amount})
            self.assertEqual(response.status_code, 400)
        detail = self.client.get('/api/admin/manage/users/u1').json()
        self.assertEqual(detail['user']['credits_remaining'], 12)
        self.assertEqual(detail['admin_history'], [])

    def test_credit_adjustment_conflicts_with_intervening_spend_or_role_change(self):
        for changed_fields in ({'credits_remaining': 9}, {'is_admin': True}):
            with self.subTest(changed_fields=changed_fields):
                self.setUp()
                def change_concurrently(documents):
                    documents[2].update(changed_fields)
                self.db.users.before_mutation = change_concurrently
                response = self.client.patch('/api/admin/manage/users/u1/credits', json={
                    'amount': 8, 'expected_balance': 12, 'reason': 'Support adjustment',
                })
                self.assertEqual(response.status_code, 409)
                detail = self.client.get('/api/admin/manage/users/u1').json()
                self.assertEqual(detail['user']['credits_remaining'], changed_fields.get('credits_remaining', 12))
                self.assertEqual(detail['admin_history'], [])

    def test_credits_protect_other_administrators_and_allow_legacy_zero_balance(self):
        payload = {'amount': 1, 'expected_balance': 0, 'reason': 'Adjustment'}
        self.db.users.documents.append({'id': 'other-admin', 'is_admin': True})
        for target in ('owner', 'other-admin'):
            self.assertEqual(self.client.patch(f'/api/admin/manage/users/{target}/credits', json=payload).status_code, 403)
        own = self.client.patch('/api/admin/manage/users/admin/credits', json=payload)
        self.assertEqual(own.status_code, 200)
        self.assertEqual(own.json()['user']['credits_remaining'], 1)
        self.as_user('owner')
        self.assertEqual(self.client.patch('/api/admin/manage/users/other-admin/credits', json=payload).status_code, 200)
        self.assertEqual(self.client.patch('/api/admin/manage/users/owner/credits', json=payload).status_code, 200)
        self.assertEqual(self.client.patch('/api/admin/manage/users/missing/credits', json=payload).status_code, 404)

    def test_audit_retains_only_last_hundred_changes_after_update(self):
        self.db.users.documents[2]['admin_history'] = [
            {'id': str(index), 'actor_id': 'owner', 'action': 'credits',
             'before': {}, 'after': {}, 'reason': 'Old adjustment',
             'created_at': '2026-10-01'} for index in range(100)
        ]
        self.client.patch('/api/admin/manage/users/u1/credits', json={
            'amount': 1, 'expected_balance': 12, 'reason': 'Most recent adjustment',
        })
        history = self.client.get('/api/admin/manage/users/u1').json()['admin_history']
        self.assertEqual(len(history), 100)
        self.assertEqual(history[0]['id'], '1')
        self.assertEqual(history[-1]['reason'], 'Most recent adjustment')

    def test_every_mutation_rechecks_actor_against_database(self):
        self.db.users.documents[1]['is_admin'] = False
        for endpoint, payload in (
            ('access', {'is_disabled': True, 'reason': 'Suspend'}),
            ('credits', {'amount': 1, 'expected_balance': 12, 'reason': 'Adjustment'}),
        ):
            self.assertEqual(self.client.patch(f'/api/admin/manage/users/u1/{endpoint}', json=payload).status_code, 403)
        self.as_user('owner')
        detail = self.client.get('/api/admin/manage/users/u1').json()
        self.assertEqual(detail['user']['credits_remaining'], 12)
        self.assertFalse(detail['user']['is_disabled'])
        self.assertEqual(detail['admin_history'], [])

    def test_access_revokes_old_sessions_and_credits_preserve_current_session(self):
        self.app.dependency_overrides.clear()
        self.app.state.auth_db = self.db
        with patch.dict(os.environ, {'SECRET_KEY': 'test-only-admin-contract-signing-key-32-plus'}):
            def headers(user_id, version):
                token = create_access_token({'sub': user_id, 'auth_version': version})
                return {'Authorization': 'Bearer ' + token}
            owner_headers = headers('owner', 0)
            old_headers = headers('u1', 0)
            self.assertEqual(self.client.get('/api/admin/manage/overview', headers=old_headers).status_code, 403)
            promoted = self.client.patch('/api/admin/manage/users/u1/access', headers=owner_headers, json={
                'is_admin': True, 'reason': 'New administrator',
            })
            self.assertEqual(promoted.status_code, 200)
            self.assertEqual(self.client.get('/api/admin/manage/overview', headers=old_headers).status_code, 401)
            current_headers = headers('u1', 1)
            self.assertEqual(self.client.get('/api/admin/manage/overview', headers=current_headers).status_code, 200)
            self.client.patch('/api/admin/manage/users/u1/credits', headers=owner_headers, json={
                'amount': 1, 'expected_balance': 12, 'reason': 'Adjustment',
            })
            self.assertEqual(self.client.get('/api/admin/manage/overview', headers=current_headers).status_code, 200)
            for disabled in (True, False):
                changed = self.client.patch('/api/admin/manage/users/u1/access', headers=owner_headers, json={
                    'is_disabled': disabled, 'reason': 'Access review',
                })
                self.assertEqual(changed.status_code, 200)
                self.assertEqual(self.client.get('/api/admin/manage/overview', headers=current_headers).status_code, 401)
            self.assertEqual(self.client.get('/api/admin/manage/overview', headers=headers('u1', 3)).status_code, 200)


if __name__ == '__main__':
    unittest.main()
