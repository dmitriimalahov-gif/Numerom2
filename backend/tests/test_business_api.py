"""Business API invariants on a real, explicitly isolated disposable MongoDB."""
import asyncio
import base64
import os
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import httpx
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from auth import create_access_token
from routers.business import create_business_router
from services.business import (
    ActivateRequest, BusinessService, EmployeeWrite, GroupWrite, ImportRequest,
    MAX_BASE64_LENGTH, PreviewRequest, RevisionRequest,
)


def employee(number=1, **changes):
    return {'name': 'Иван', 'surname': f'Тестовый {number}', 'birth_date': '10.01.1982',
            'department': 'Операции', 'role': 'Специалист', 'skills': ['Excel'],
            'experience': 'Практическая работа с таблицами', 'interests': ['Отчёты'],
            'hours_per_week': 20, **changes}


def group(members, **changes):
    return {'name': 'Сводный отчёт', 'task': 'Подготовить отчёт',
            'required_skills': ['Excel', 'SQL'], 'target_hours': 30,
            'member_ids': members, **changes}


class BusinessContractTests(unittest.TestCase):
    def test_request_models_reject_injected_owner_coercion_and_limits(self):
        for payload in ({'expected_revision': True}, {'expected_revision': -1},
                        {'expected_revision': '0'}, {'expected_revision': 0, 'user_id': 'victim'}):
            with self.assertRaises(ValidationError):
                RevisionRequest.model_validate(payload)
        with self.assertRaises(ValidationError):
            ActivateRequest(company_name='   ')
        for name in ('Company\x00', '\x00', 'Company\u202e', 'Company\nName'):
            with self.assertRaises(ValidationError):
                ActivateRequest(company_name=name)
        self.assertEqual(ActivateRequest(company_name='  Тестовая   компания ').company_name, 'Тестовая компания')
        with self.assertRaises(ValidationError):
            ImportRequest(request_id='small', expected_revision=0, employees=[employee()])
        with self.assertRaises(ValidationError):
            ImportRequest(request_id=str(uuid4()), expected_revision=0, employees=[employee(i) for i in range(251)])
        with self.assertRaises(ValidationError):
            PreviewRequest(filename='x.csv', content_base64='A' * (MAX_BASE64_LENGTH + 1))


@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'), 'isolated Mongo required')
class BusinessApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.env = patch.dict(os.environ, {'SECRET_KEY': 'business-test-signing-key-isolated-20261018'})
        self.env.start()
        self.mongo = AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL'])
        self.db = self.mongo['numerom_test_business_' + uuid4().hex]
        await self.db.users.insert_many([
            {'id': 'owner', 'credits_remaining': 17},
            {'id': 'other', 'credits_remaining': 11, 'is_admin': True},
        ])
        self.app = FastAPI()
        self.app.state.auth_db = self.db
        self.app.include_router(create_business_router(self.db))
        self.http = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url='http://isolated-test')
        self.service = BusinessService(self.db)

    async def asyncTearDown(self):
        await self.http.aclose()
        await self.mongo.drop_database(self.db.name)
        self.mongo.close()
        self.env.stop()

    def headers(self, owner='owner', **claims):
        return {'Authorization': 'Bearer ' + create_access_token({'sub': owner, **claims})}

    async def call(self, method, route='', *, owner='owner', body=None):
        return await self.http.request(method, '/api/business' + route, headers=self.headers(owner), json=body)

    async def activate(self, owner='owner'):
        response = await self.call('POST', '/activate', owner=owner, body={'company_name': 'Тестовая компания'})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()['workspace']

    async def import_rows(self, rows, revision=0, request_id=None):
        body = {'request_id': request_id or str(uuid4()), 'expected_revision': revision, 'employees': rows}
        return await self.call('POST', '/import', body=body)

    async def seeded(self, count=2):
        await self.activate()
        response = await self.import_rows([employee(index) for index in range(count)])
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()['workspace']

    async def test_all_routes_use_live_authenticated_user_and_entitlement(self):
        anonymous = await self.http.get('/api/business')
        self.assertEqual(anonymous.status_code, 401)
        self.assertIsNone((await self.call('GET')).json()['workspace'])
        for method, path, payload in [
            ('GET', '/template', None), ('GET', '/groups/x/report', None),
            ('POST', '/import/preview', {'filename': 'x.csv', 'content_base64': 'eA=='}),
            ('POST', '/import', {'request_id': str(uuid4()), 'expected_revision': 0, 'employees': [employee()]}),
            ('POST', '/groups', {'expected_revision': 0, 'group': group([])}),
            ('PATCH', '/employees/x', {'expected_revision': 0, 'employee': employee()}),
            ('POST', '/employees/x/remove', {'expected_revision': 0}),
            ('POST', '/groups/x/remove', {'expected_revision': 0}),
        ]:
            response = await self.call(method, path, body=payload)
            self.assertEqual(response.status_code, 403, (path, response.text))
        self.assertEqual((await self.call('GET', owner='deleted')).status_code, 401)
        await self.db.users.update_one({'id': 'owner'}, {'$set': {'is_disabled': True}})
        self.assertEqual((await self.call('POST', '/activate', body={'company_name': 'X'})).status_code, 401)

    async def test_pilot_activation_idempotent_concurrent_and_never_spends_credits(self):
        before = await self.db.users.find_one({'id': 'owner'})
        responses = await asyncio.gather(*(self.activate() for _ in range(8)))
        self.assertEqual(len({row['id'] for row in responses}), 1)
        self.assertEqual(await self.db.business_workspaces.count_documents({}), 1)
        again = await self.call('POST', '/activate', body={'company_name': 'Переименование не разрешено активацией'})
        self.assertEqual(again.json()['workspace']['company_name'], 'Тестовая компания')
        self.assertEqual(again.json()['package']['price'], 0)
        self.assertEqual(again.json()['package']['mode'], 'pilot')
        self.assertEqual(await self.db.users.find_one({'id': 'owner'}), before)
        self.assertEqual(await self.db.credit_transactions.count_documents({}), 0)
        self.assertEqual(await self.db.payment_transactions.count_documents({}), 0)
        self.assertNotIn('_id', again.json()['workspace'])
        self.assertNotIn('import_history', again.json()['workspace'])

    async def test_invalid_company_cannot_create_unreadable_workspace(self):
        response = await self.call('POST', '/activate', body={'company_name': 'Company\x00'})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(await self.db.business_workspaces.count_documents({}), 0)
        workspace = await self.activate()
        self.assertEqual(workspace['company_name'], 'Тестовая компания')

    async def test_preview_and_template_never_write_source_bytes(self):
        await self.activate()
        before = await self.db.business_workspaces.find_one({'_id': 'owner'})
        template = (await self.call('GET', '/template')).json()
        response = await self.call('POST', '/import/preview', body={
            'filename': template['filename'],
            'content_base64': base64.b64encode(template['content'].encode()).decode(),
        })
        self.assertEqual(response.status_code, 200, response.text)
        preview = response.json()
        self.assertTrue(preview['valid'], preview)
        self.assertEqual(len(preview['employees']), 1)
        self.assertEqual(await self.db.business_workspaces.find_one({'_id': 'owner'}), before)
        self.assertEqual(set(await self.db.list_collection_names()), {'users', 'business_workspaces'})

    async def test_preview_rejects_bad_base64_and_decoded_oversize(self):
        await self.activate()
        bad = await self.call('POST', '/import/preview', body={'filename': 'x.csv', 'content_base64': '!!!!'})
        self.assertEqual(bad.status_code, 422)
        big = await self.call('POST', '/import/preview', body={'filename': 'x.csv', 'content_base64': base64.b64encode(b'x' * (5 * 1024 * 1024 + 1)).decode()})
        self.assertEqual(big.status_code, 413)
        row = (await self.call('GET')).json()['workspace']
        self.assertEqual(row['revision'], 0)

    async def test_preview_existing_duplicate_uses_original_row_and_does_not_write(self):
        await self.seeded(1)
        content = 'Имя;Фамилия;Дата рождения\r\n\r\nИван;Тестовый 0;10.01.1982\r\nИван;Тестовый 0;02.01.1982\r\n'
        preview = await self.call('POST', '/import/preview', body={
            'filename': 'people.csv', 'content_base64': base64.b64encode(content.encode()).decode(),
        })
        self.assertEqual(preview.status_code, 200)
        result = preview.json()
        self.assertFalse(result['valid'], result)
        self.assertTrue(any(issue['row'] == 3 and 'уже есть' in issue['message'] for issue in result['issues']), result)
        self.assertTrue(any(warning['row'] == 4 for warning in result['warnings']), result)
        self.assertNotIn('_employee_rows', result)
        row = (await self.call('GET')).json()['workspace']
        self.assertEqual(row['revision'], 1)
        self.assertEqual(len(row['employees']), 1)

    async def test_import_exactly_250_and_rejects_251_without_partial_write(self):
        await self.activate()
        excessive = await self.import_rows([employee(i) for i in range(251)])
        self.assertEqual(excessive.status_code, 422)
        self.assertEqual((await self.call('GET')).json()['workspace']['employees'], [])
        response = await self.import_rows([employee(i) for i in range(250)])
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()['workspace']['employees']), 250)
        after = await self.import_rows([employee(300)], revision=1)
        self.assertEqual(after.status_code, 422)
        self.assertEqual((await self.call('GET')).json()['workspace']['revision'], 1)

    async def test_same_import_retry_concurrently_is_exactly_once_and_conflicts_changed_body(self):
        await self.activate()
        request_id = str(uuid4())
        responses = await asyncio.gather(*(self.import_rows([employee()], request_id=request_id) for _ in range(8)))
        self.assertEqual({item.status_code for item in responses}, {200})
        self.assertEqual({item.json()['workspace']['revision'] for item in responses}, {1})
        self.assertEqual(len((await self.call('GET')).json()['workspace']['employees']), 1)
        conflict = await self.import_rows([employee(99)], request_id=request_id)
        self.assertEqual(conflict.status_code, 409)
        await self.import_rows([employee(2)], revision=1)
        retried = await self.import_rows([employee()], request_id=request_id)
        self.assertEqual(retried.status_code, 200)
        self.assertEqual(retried.json()['workspace']['revision'], 2)
        self.assertEqual(len(retried.json()['workspace']['employees']), 2)

    async def test_competing_imports_use_atomic_revision_and_preserve_winner(self):
        await self.activate()
        results = await asyncio.gather(*(self.import_rows([employee(i)]) for i in range(8)))
        self.assertEqual(sum(item.status_code == 200 for item in results), 1)
        self.assertEqual(sum(item.status_code == 409 for item in results), 7)
        row = (await self.call('GET')).json()['workspace']
        self.assertEqual(row['revision'], 1)
        self.assertEqual(len(row['employees']), 1)

    async def test_duplicate_import_rejects_entire_batch_including_normalized_identity(self):
        await self.seeded(count=1)
        response = await self.import_rows([employee(8), employee(0, name='  иВАН  ', surname='ТЕСТОВЫЙ  0')], revision=1)
        self.assertEqual(response.status_code, 422)
        row = (await self.call('GET')).json()['workspace']
        self.assertEqual(len(row['employees']), 1)
        self.assertEqual(row['revision'], 1)
        response = await self.import_rows([employee(8), employee(8)], revision=1)
        self.assertEqual(response.status_code, 422)

    async def test_owner_boundary_blocks_employee_group_and_report_access_even_for_admin(self):
        row = await self.seeded()
        member = row['employees'][0]['id']
        saved = await self.call('POST', '/groups', body={'expected_revision': 1, 'group': group([member])})
        group_id = saved.json()['workspace']['groups'][0]['id']
        await self.activate('other')
        other = (await self.call('GET', owner='other')).json()['workspace']
        self.assertEqual(other['employees'], [])
        for method, path, body in [
            ('PATCH', f'/employees/{member}', {'expected_revision': 0, 'employee': employee(8)}),
            ('POST', f'/employees/{member}/remove', {'expected_revision': 0}),
            ('POST', '/groups', {'expected_revision': 0, 'id': group_id, 'group': group([])}),
            ('POST', f'/groups/{group_id}/remove', {'expected_revision': 0}),
            ('GET', f'/groups/{group_id}/report', None),
        ]:
            result = await self.call(method, path, body=body, owner='other')
            self.assertEqual(result.status_code, 404, result.text)
        injected = await self.call('POST', '/groups', owner='other', body={'expected_revision': 0, 'group': group([member])})
        self.assertEqual(injected.status_code, 422)
        self.assertEqual((await self.call('GET')).json()['workspace']['revision'], 2)

    async def test_employee_edit_conflict_duplicate_and_atomic_membership_removal(self):
        row = await self.seeded()
        first, second = [item['id'] for item in row['employees']]
        result = await self.call('POST', '/groups', body={'expected_revision': 1, 'group': group([first, second])})
        self.assertEqual(result.status_code, 200)
        conflict = await self.call('PATCH', f'/employees/{first}', body={'expected_revision': 1, 'employee': employee(5)})
        self.assertEqual(conflict.status_code, 409)
        duplicate = await self.call('PATCH', f'/employees/{first}', body={'expected_revision': 2, 'employee': employee(1)})
        self.assertEqual(duplicate.status_code, 422)
        edited = await self.call('PATCH', f'/employees/{first}', body={'expected_revision': 2, 'employee': employee(5, skills=['SQL'])})
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(edited.json()['workspace']['employees'][0]['id'], first)
        removed = await self.call('POST', f'/employees/{first}/remove', body={'expected_revision': 3})
        self.assertEqual(removed.status_code, 200)
        workspace = removed.json()['workspace']
        self.assertEqual([item['id'] for item in workspace['employees']], [second])
        self.assertEqual(workspace['groups'][0]['member_ids'], [second])
        self.assertEqual(workspace['revision'], 4)

    async def test_group_edit_remove_and_capacity_limits(self):
        row = await self.seeded(21)
        members = [item['id'] for item in row['employees']]
        too_many = await self.call('POST', '/groups', body={'expected_revision': 1, 'group': group(members)})
        self.assertEqual(too_many.status_code, 422)
        repeated = await self.call('POST', '/groups', body={'expected_revision': 1, 'group': group([members[0], members[0]])})
        self.assertEqual(repeated.status_code, 422)
        saved = await self.call('POST', '/groups', body={'expected_revision': 1, 'group': group(members[:20])})
        self.assertEqual(saved.status_code, 200)
        group_id = saved.json()['workspace']['groups'][0]['id']
        edited = await self.call('POST', '/groups', body={'expected_revision': 2, 'id': group_id, 'group': group([], name='Новая задача')})
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(edited.json()['workspace']['groups'][0]['name'], 'Новая задача')
        removed = await self.call('POST', f'/groups/{group_id}/remove', body={'expected_revision': 3})
        self.assertEqual(removed.json()['workspace']['groups'], [])
        await self.db.business_workspaces.update_one({'_id': 'owner'}, {'$set': {'groups': [{**group([]), 'id': str(uuid4())} for _ in range(50)]}})
        limit = await self.call('POST', '/groups', body={'expected_revision': 4, 'group': group([])})
        self.assertEqual(limit.status_code, 422)

    async def test_report_uses_only_declared_skills_and_hours_not_name_or_date(self):
        row = await self.seeded(1)
        member = row['employees'][0]['id']
        saved = await self.call('POST', '/groups', body={'expected_revision': 1, 'group': group([member])})
        group_id = saved.json()['workspace']['groups'][0]['id']
        original = (await self.call('GET', f'/groups/{group_id}/report')).json()['report']
        changed = await self.call('PATCH', f'/employees/{member}', body={'expected_revision': 2, 'employee': employee(0, name='Анна', surname='Иная', birth_date='02.03.2001')})
        self.assertEqual(changed.status_code, 200)
        updated = (await self.call('GET', f'/groups/{group_id}/report')).json()['report']
        for field in ('coverage', 'missing_skills', 'available_hours', 'target_hours', 'missing_hours_data', 'next_steps'):
            self.assertEqual(updated[field], original[field], field)
        self.assertEqual(original['missing_skills'], ['SQL'])
        self.assertEqual(original['available_hours'], 20)
        self.assertNotIn('score', original)

    async def test_import_receipts_remain_bounded_and_hidden(self):
        await self.activate()
        first_id = str(uuid4())
        for index in range(66):
            response = await self.import_rows([employee(index)], revision=index, request_id=first_id if index == 0 else None)
            self.assertEqual(response.status_code, 200, response.text)
        saved = await self.db.business_workspaces.find_one({'_id': 'owner'})
        self.assertEqual(len(saved['import_history']), 64)
        replay = await self.import_rows([employee(0)], request_id=first_id)
        self.assertEqual(replay.status_code, 409)
        self.assertEqual(len((await self.call('GET')).json()['workspace']['employees']), 66)


if __name__ == '__main__':
    unittest.main()
