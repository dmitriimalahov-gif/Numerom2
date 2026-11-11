import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import HTTPException
from services.credit_debit import debit_credits

class DebitTests(unittest.IsolatedAsyncioTestCase):
    async def test_balance_predicate_and_history_are_committed_together(self):
        users = SimpleNamespace(update_one=AsyncMock(return_value=SimpleNamespace(matched_count=1)))
        db = SimpleNamespace(users=users)
        with patch('services.credit_debit.flush_pending_credit_transactions', new=AsyncMock(side_effect=RuntimeError('storage down'))):
            await debit_credits(db, 'u', 2, 'Calculation', 'numerology')
        query, change = users.update_one.call_args.args
        self.assertEqual(query['credits_remaining'], {'$gte': 2})
        self.assertEqual(change['$inc'], {'credits_remaining': -2})
        self.assertEqual(change['$push']['pending_credit_transactions']['amount'], -2)
    async def test_failed_debit_never_writes_a_history_entry(self):
        db = SimpleNamespace(users=SimpleNamespace(update_one=AsyncMock(return_value=SimpleNamespace(matched_count=0))))
        with patch('services.credit_debit.flush_pending_credit_transactions', new=AsyncMock()) as flush:
            with self.assertRaises(HTTPException) as error:
                await debit_credits(db, 'u', 2, 'Calculation', 'numerology')
            self.assertEqual(error.exception.status_code, 402)
            flush.assert_not_awaited()
    async def test_invalid_cost_never_touches_database(self):
        for cost in (-1, True, 1.5, '1'):
            with self.assertRaises(HTTPException):
                await debit_credits(None, 'u', cost, 'Calculation', 'numerology')
    async def test_calculation_and_ledger_outboxes_share_the_debit_mutation(self):
        users = SimpleNamespace(update_one=AsyncMock(return_value=SimpleNamespace(matched_count=1)))
        db = SimpleNamespace(users=users)
        calculation = {'id': 'calc-id', 'user_id': 'u', 'results': {'soul_number': 2}}
        with patch('services.credit_debit.flush_pending_credit_transactions', new=AsyncMock()), \
                patch('services.credit_debit.flush_pending_calculations', new=AsyncMock()):
            await debit_credits(db, 'u', 2, 'Calculation', 'numerology', calculation=calculation)
        change = users.update_one.call_args.args[1]
        self.assertEqual(change['$push']['pending_calculations'], calculation)
        self.assertEqual(change['$push']['pending_credit_transactions']['amount'], -2)
        self.assertEqual(change['$inc']['credits_remaining'], -2)
