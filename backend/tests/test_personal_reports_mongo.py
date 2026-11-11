"""Real Mongo reads from a disposable test database, including undelivered results."""
import copy
import os
import sys
import unittest
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from auth import get_current_user
from routers.personal_reports import create_personal_reports_router
from services.personal_numbers import personal_numbers_result


@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'), 'isolated Mongo required')
class LatestReportMongo(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client = AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL'])
        self.db = self.client['numerom_test_personal_reports_' + uuid.uuid4().hex]
        self.user = {'id': 'u', 'credits_remaining': 7, 'name': 'Anna', 'surname': 'Li', 'birth_date': '10.01.1982'}
        await self.db.users.insert_one(copy.deepcopy(self.user))
        app = FastAPI()
        app.include_router(create_personal_reports_router(self.db))
        app.dependency_overrides[get_current_user] = lambda: {'user_id': 'u'}
        self.http = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://isolated-test')

    async def asyncTearDown(self):
        await self.http.aclose()
        await self.client.drop_database(self.db.name)
        self.client.close()

    async def latest(self):
        return await self.http.get('/api/numerology/personal-numbers/latest')

    async def test_paid_result_can_be_read_repeatedly_free_after_balance_reaches_zero(self):
        result = await personal_numbers_result(self.db, 'u', None, 7)
        before = await self.db.users.find_one({'id': 'u'})
        self.assertEqual(before['credits_remaining'], 0)
        for _ in range(3):
            response = await self.latest()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['calculation']['results'], result)
            self.assertEqual(set(response.json()['calculation']), {'id', 'birth_date', 'created_at', 'results'})
        self.assertEqual(await self.db.users.find_one({'id': 'u'}), before)
        self.assertEqual(await self.db.numerology_calculations.count_documents({}), 1)
        self.assertEqual(await self.db.credit_transactions.count_documents({}), 1)

    async def test_outbox_delivery_outage_remains_readable_without_archive_writes(self):
        failing = SimpleNamespace(users=self.db.users, credit_transactions=self.db.credit_transactions,
            numerology_calculations=SimpleNamespace(update_one=AsyncMock(side_effect=RuntimeError('synthetic delivery outage'))))
        result = await personal_numbers_result(failing, 'u', None, 7)
        before = await self.db.users.find_one({'id': 'u'})
        self.assertEqual(len(before['pending_calculations']), 1)
        response = await self.latest()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['calculation']['results'], result)
        self.assertEqual(await self.db.users.find_one({'id': 'u'}), before)
        self.assertEqual(await self.db.numerology_calculations.count_documents({}), 0)
        self.assertEqual(await self.db.credit_transactions.count_documents({}), 1)

    async def test_query_uses_current_owner_type_and_latest_creation_time(self):
        now = datetime.utcnow()
        common = {'birth_date': '10.01.1982', 'results': {'soul_number': 1}, 'calculation_type': 'personal_numbers'}
        await self.db.numerology_calculations.insert_many([
            {**common, 'id': 'older', 'user_id': 'u', 'created_at': now - timedelta(days=1)},
            {**common, 'id': 'mine', 'user_id': 'u', 'created_at': now},
            {**common, 'id': 'other-owner', 'user_id': 'other', 'created_at': now + timedelta(days=1)},
            {**common, 'id': 'other-type', 'user_id': 'u', 'created_at': now + timedelta(days=2), 'calculation_type': 'compatibility'},
        ])
        before = await self.db.users.find_one({'id': 'u'})
        response = await self.latest()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['calculation']['id'], 'mine')
        self.assertEqual(await self.db.users.find_one({'id': 'u'}), before)
        self.assertEqual(await self.db.credit_transactions.count_documents({}), 0)
        await self.db.users.update_one({'id': 'u'}, {'$set': {'is_disabled': True}})
        self.assertEqual((await self.latest()).status_code, 401)


if __name__ == '__main__':
    unittest.main()
