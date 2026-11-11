"""Optional tests against a disposable MongoDB, never the application database."""
import asyncio
import ast
import os
import sys
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException, FastAPI, APIRouter, Depends
import httpx
from services.credit_debit import debit_credits, flush_pending_calculations
from services.credit_history import flush_pending_credit_transactions
from services.personal_numbers import personal_numbers_result

@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'), 'isolated Mongo required')
class DebitConcurrency(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client = AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL'])
        self.db = self.client['numerom_test_debit_' + uuid.uuid4().hex]
        await self.db.users.insert_one({'id': 'u', 'credits_remaining': 3})
    async def asyncTearDown(self):
        await self.client.drop_database(self.db.name)
        self.client.close()
    async def test_parallel_calculations_cannot_overspend_and_history_matches_balance(self):
        results = await asyncio.gather(*(debit_credits(self.db, 'u', 1, 'Calculation', 'numerology') for _ in range(10)), return_exceptions=True)
        self.assertEqual(sum(result is None for result in results), 3)
        self.assertEqual([error.status_code for error in results if isinstance(error, HTTPException)], [402] * 7)
        self.assertEqual((await self.db.users.find_one({'id': 'u'}))['credits_remaining'], 0)
        history = await self.db.credit_transactions.find({'user_id': 'u'}).to_list(100)
        self.assertEqual(len(history), 3)
        self.assertEqual(sum(item['amount'] for item in history), -3)

    async def test_result_survives_delivery_failure_and_concurrent_retry_deduplicates(self):
        await self.db.users.update_one({'id': 'u'}, {'$set': {
            'birth_date': '02.03.1990', 'name': 'Anna', 'surname': 'Li'}})
        failing_db = SimpleNamespace(users=self.db.users,
            numerology_calculations=SimpleNamespace(update_one=AsyncMock(side_effect=RuntimeError('synthetic archive outage'))))
        # Execute the actual route, without application startup or a live listener.
        source = ast.parse((Path(__file__).resolve().parents[1] / 'server.py').read_text())
        route = next(node for node in source.body if isinstance(node, ast.AsyncFunctionDef) and node.name == 'personal_numbers')
        app, router = FastAPI(), APIRouter(prefix='/api')
        async def identity():
            return {'user_id': 'u'}
        exec(compile(ast.Module(body=[route], type_ignores=[]), 'actual-personal-route', 'exec'), {
            'api_router': router, 'db': failing_db, 'Depends': Depends, 'get_current_user': identity,
            'get_credits_deduction_config': AsyncMock(return_value={'personal_numbers': 1}),
            'CREDIT_COSTS': {'personal_numbers': 1}})
        app.include_router(router)
        with patch('services.credit_debit.flush_pending_credit_transactions', new=AsyncMock(side_effect=RuntimeError('synthetic history outage'))):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://isolated-test') as client:
                response = await client.post('/api/numerology/personal-numbers?birth_date=02.03.1990')
            self.assertEqual(response.status_code, 200, response.text)
            result = response.json()
        user = await self.db.users.find_one({'id': 'u'})
        self.assertEqual(user['credits_remaining'], 2)
        self.assertEqual(len(user['pending_calculations']), 1)
        self.assertEqual(len(user['pending_credit_transactions']), 1)
        self.assertEqual(user['pending_calculations'][0]['results'], result)
        self.assertEqual(await self.db.numerology_calculations.count_documents({}), 0)

        # Crash after archive insertion but before outbox acknowledgment.
        cleanup_failure_db = SimpleNamespace(
            users=SimpleNamespace(find_one=self.db.users.find_one,
                                  update_one=AsyncMock(side_effect=RuntimeError('synthetic acknowledgment outage'))),
            numerology_calculations=self.db.numerology_calculations)
        with self.assertRaises(RuntimeError):
            await flush_pending_calculations(cleanup_failure_db, 'u')
        self.assertEqual(await self.db.numerology_calculations.count_documents({}), 1)
        await asyncio.gather(*[flush_pending_calculations(self.db, 'u') for _ in range(8)])
        await asyncio.gather(*[flush_pending_credit_transactions(self.db, 'u') for _ in range(8)])
        saved = await self.db.numerology_calculations.find_one({'user_id': 'u'})
        self.assertEqual(saved['results'], result)
        self.assertEqual(await self.db.numerology_calculations.count_documents({}), 1)
        self.assertEqual(await self.db.credit_transactions.count_documents({}), 1)
        user = await self.db.users.find_one({'id': 'u'})
        self.assertEqual(user['credits_remaining'], 2)
        self.assertEqual(user['pending_calculations'], [])
        self.assertEqual(user['pending_credit_transactions'], [])

    async def test_insufficient_credit_cannot_commit_a_calculation_record(self):
        await self.db.users.update_one({'id': 'u'}, {'$set': {'full_name_number': 5}})
        with self.assertRaises(HTTPException) as error:
            await personal_numbers_result(self.db, 'u', '02.03.1990', 4)
        self.assertEqual(error.exception.status_code, 402)
        user = await self.db.users.find_one({'id': 'u'})
        self.assertEqual(user['credits_remaining'], 3)
        self.assertNotIn('pending_calculations', user)
        self.assertEqual(await self.db.numerology_calculations.count_documents({}), 0)

    async def test_free_calculation_is_archived_without_credit_transaction(self):
        await self.db.users.update_one({'id': 'u'}, {'$set': {'full_name_number': 5}})
        result = await personal_numbers_result(self.db, 'u', '02.03.1990', 0)
        self.assertEqual((await self.db.users.find_one({'id': 'u'}))['credits_remaining'], 3)
        self.assertEqual((await self.db.numerology_calculations.find_one({'user_id': 'u'}))['results'], result)
        self.assertEqual(await self.db.credit_transactions.count_documents({}), 0)
