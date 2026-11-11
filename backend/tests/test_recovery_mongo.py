"""Run against a disposable Mongo only: NUMEROM_TEST_MONGO_URL=mongodb://127.0.0.1:27028.
Every test creates/drops its own numerom_test_* database; never uses the configured app DB.
"""
import asyncio
import hashlib
import os
import sys
import unittest
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from auth import get_password_hash
from services.recovery import RecoveryService
from services.admin_management import AdminManagementService
from services.credit_history import admin_credit_transaction, flush_pending_credit_transactions
from routers.admin_management import CreditChange
from recovery_support import Mailbox

@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'),'optional isolated Mongo integration')
class MongoAtomicity(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client=AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL'],serverSelectionTimeoutMS=5000)
        self.db=self.client['numerom_test_'+uuid.uuid4().hex]
        self.now=datetime.utcnow(); self.token='synthetic-token-with-at-least-32-characters'
        await self.db.users.insert_one({'id':'u1','email':'anna@example.invalid','password_hash':get_password_hash('old-long-password'),'credits_remaining':10,'password_reset_hash':hashlib.sha256(self.token.encode()).hexdigest(),'password_reset_expires_at':self.now+timedelta(minutes=30)})
        self.service=RecoveryService(self.db,Mailbox(),'https://numerom.example/reset-password',lambda:self.now)
    async def asyncTearDown(self):
        await self.client.drop_database(self.db.name); self.client.close()
    async def test_only_one_concurrent_reset_consumes_token(self):
        results=await asyncio.gather(self.service.reset(self.token,'first-new-password','one'),self.service.reset(self.token,'second-new-password','two'),return_exceptions=True)
        self.assertEqual(sum(isinstance(r,str) for r in results),1)
        self.assertEqual([r.status_code for r in results if isinstance(r,HTTPException)],[400])
        record=await self.db.users.find_one({'id':'u1'});self.assertEqual(record['auth_version'],1);self.assertNotIn('password_reset_hash',record)
    async def test_shared_rate_limit_allows_only_one_email_request(self):
        results=await asyncio.gather(*(self.service.reserve_request('anna@example.invalid',str(i)) for i in range(8)))
        self.assertEqual(sum(results),1)
    async def test_competing_admin_balance_updates_have_one_winner_and_one_audit(self):
        manager=AdminManagementService(self.db);actor={'id':'admin','is_super_admin':True}
        results=await asyncio.gather(*(manager.change_credits(actor,'u1',CreditChange(amount=5,expected_balance=10,reason='Synthetic test')) for _ in range(2)),return_exceptions=True)
        self.assertEqual(sum(isinstance(r,dict) for r in results),1)
        self.assertEqual([r.status_code for r in results if isinstance(r,HTTPException)],[409])
        record=await self.db.users.find_one({'id':'u1'});self.assertEqual(record['credits_remaining'],15);self.assertEqual(len(record['admin_history']),1)

    async def test_concurrent_credit_outbox_drains_create_one_ledger_entry(self):
        event = {
            'id': str(uuid.uuid4()), 'actor_id': 'admin', 'action': 'credits',
            'before': {'credits_remaining': 10}, 'after': {'credits_remaining': 15},
            'reason': 'Private administrative test reason', 'created_at': self.now,
        }
        transaction = admin_credit_transaction('u1', event)
        await self.db.users.update_one({'id': 'u1'}, {
            '$set': {'credits_remaining': 15},
            '$push': {'pending_credit_transactions': transaction},
        })

        # Every worker reads the same committed item before any worker can drain it.
        # All reads/writes still reach this test's real, disposable Mongo database.
        workers = 8
        readers_ready = asyncio.Event()
        readers = 0
        async def read_same_snapshot(query, projection=None):
            nonlocal readers
            snapshot = await self.db.users.find_one(query, projection)
            readers += 1
            if readers == workers:
                readers_ready.set()
            await asyncio.wait_for(readers_ready.wait(), timeout=5)
            return snapshot
        synchronized_db = SimpleNamespace(
            users=SimpleNamespace(find_one=read_same_snapshot, update_one=self.db.users.update_one),
            credit_transactions=self.db.credit_transactions,
        )
        results = await asyncio.gather(*(
            flush_pending_credit_transactions(synchronized_db, 'u1') for _ in range(workers)
        ), return_exceptions=True)
        self.assertEqual(results, [None] * workers)
        ledger = await self.db.credit_transactions.find({'user_id': 'u1'}).to_list(length=None)
        self.assertEqual(len(ledger), 1)
        self.assertEqual(ledger[0]['_id'], event['id'])
        self.assertEqual((ledger[0]['amount'], ledger[0]['transaction_type'], ledger[0]['category']),
                         (5, 'credit', 'admin'))
        self.assertEqual(ledger[0]['details'], {'added_by_admin': True, 'old_credits': 10, 'new_credits': 15})
        self.assertNotIn('Private administrative test reason', str(ledger))
        record = await self.db.users.find_one({'id': 'u1'})
        self.assertEqual((record['credits_remaining'], record['pending_credit_transactions']), (15, []))

        # Simulate a process that wrote the ledger and died before clearing its item.
        await self.db.users.update_one({'id': 'u1'}, {'$push': {'pending_credit_transactions': transaction}})
        await asyncio.gather(*(flush_pending_credit_transactions(self.db, 'u1') for _ in range(workers)))
        self.assertEqual(await self.db.credit_transactions.count_documents({'user_id': 'u1'}), 1)
        self.assertEqual((await self.db.users.find_one({'id': 'u1'}))['pending_credit_transactions'], [])
