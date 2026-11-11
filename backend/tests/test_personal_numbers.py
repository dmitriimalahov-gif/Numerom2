"""Fault tests for the prepared personal-numbers result and debit boundary."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.personal_numbers import personal_numbers_result
from fastapi import HTTPException
from numerology import calculate_personal_numbers


class PersonalNumbersFaults(unittest.IsolatedAsyncioTestCase):
    def database(self):
        return SimpleNamespace(users=SimpleNamespace(
            find_one=AsyncMock(return_value={'id': 'u', 'birth_date': '02.03.1990', 'name': 'Anna', 'surname': 'Li'}),
            update_one=AsyncMock(return_value=SimpleNamespace(matched_count=1))))

    async def test_user_read_failure_does_not_charge(self):
        db = self.database()
        db.users.find_one.side_effect = RuntimeError('synthetic read failure')
        with patch('services.personal_numbers.debit_credits', new=AsyncMock()) as debit:
            with self.assertRaises(RuntimeError):
                await personal_numbers_result(db, 'u', '02.03.1990', 1)
            debit.assert_not_awaited()

    async def test_name_cache_failure_does_not_charge(self):
        db = self.database()
        db.users.update_one.side_effect = RuntimeError('synthetic cache failure')
        with patch('services.personal_numbers.debit_credits', new=AsyncMock()) as debit:
            with self.assertRaises(RuntimeError):
                await personal_numbers_result(db, 'u', '02.03.1990', 1)
            debit.assert_not_awaited()

    async def test_full_result_is_prepared_and_attached_to_debit(self):
        db = self.database()
        with patch('services.personal_numbers.debit_credits', new=AsyncMock()) as debit:
            result = await personal_numbers_result(db, 'u', '02.03.1990', 1)
        record = debit.call_args.kwargs['calculation']
        self.assertEqual(record['results'], result)
        self.assertEqual(record['user_id'], 'u')
        self.assertEqual(record['calculation_type'], 'personal_numbers')
        self.assertIsInstance(result['full_name_number'], int)
        self.assertEqual(db.users.find_one.await_count, 1)

    async def test_known_date_uses_fresh_name_for_wisdom_and_keeps_other_numbers(self):
        db = self.database()
        db.users.find_one.return_value.update(birth_date='10.01.1982', full_name_number=9)
        with patch('services.personal_numbers.debit_credits', new=AsyncMock()) as debit:
            result = await personal_numbers_result(db, 'u', None, 7)
        self.assertEqual(result['full_name_number'], 6)  # A+N+N+A+L+I = 51 -> 6.
        self.assertEqual(result['wisdom_number'], 1)
        self.assertEqual(result['destiny_number'], 4)
        self.assertEqual(result['ruling_number'], 22)
        self.assertNotEqual(result['wisdom_number'], 8)
        original = calculate_personal_numbers('10.01.1982')
        for key in ['soul_number', 'mind_number', 'destiny_number', 'helping_mind_number', 'ruling_number']:
            self.assertEqual(result[key], original[key])
        self.assertEqual(debit.call_args.args[2], 7)
        self.assertEqual(debit.await_count, 1)
        self.assertEqual(debit.call_args.kwargs['calculation']['results']['report'], result['report'])
        db.users.update_one.assert_awaited_once_with({'id': 'u'}, {'$set': {'full_name_number': 6}})

    async def test_missing_or_unsupported_complete_name_never_uses_cache_or_fake_zero(self):
        for name, surname in [('', ''), ('Anna', ''), ('Анна', 'Ли'), ('Annа', 'Li'), ('Éva', 'Li'), ('Anna1', 'Li')]:
            with self.subTest(name=name, surname=surname):
                db = self.database()
                db.users.find_one.return_value.update(name=name, surname=surname, full_name_number=5)
                with patch('services.personal_numbers.debit_credits', new=AsyncMock()):
                    result = await personal_numbers_result(db, 'u', '10.01.1982', 1)
                self.assertIsNone(result['full_name_number'])
                self.assertIsNone(result['wisdom_number'])
                entries = {entry['key']: entry for entry in result['report']['numbers']}
                self.assertIsNone(entries['full_name_number']['value'])
                self.assertIsNone(entries['wisdom_number']['interpretation'])
                self.assertTrue(entries['full_name_number']['note'])

    async def test_report_failure_happens_before_debit(self):
        db = self.database()
        with patch('services.personal_numbers.build_personal_report', side_effect=RuntimeError('synthetic report failure')), \
                patch('services.personal_numbers.debit_credits', new=AsyncMock()) as debit:
            with self.assertRaises(RuntimeError):
                await personal_numbers_result(db, 'u', '10.01.1982', 1)
            debit.assert_not_awaited()

    async def test_name_reduces_master_sum_but_wisdom_preserves_master(self):
        for name, surname, name_number, wisdom in [('A', 'J', 2, 6), ('A', 'F', 7, 11),
                                                  ("Anne-Marie", "O’Neil", 9, 4)]:
            db = self.database()
            db.users.find_one.return_value.update(name=name, surname=surname)
            with patch('services.personal_numbers.debit_credits', new=AsyncMock()):
                result = await personal_numbers_result(db, 'u', '10.01.1982', 1)
            self.assertEqual(result['full_name_number'], name_number)
            self.assertEqual(result['wisdom_number'], wisdom)
            entry = next(item for item in result['report']['numbers'] if item['key'] == 'wisdom_number')
            self.assertIn(str(wisdom), entry['steps'][-1])

    async def test_invalid_date_and_inactive_account_do_not_charge(self):
        for user, date in [(None, '10.01.1982'), ({'id': 'u', 'is_disabled': True}, '10.01.1982'),
                           ({'id': 'u'}, '31.02.1982'), ({'id': 'u'}, '01.01.2999')]:
            db = self.database()
            db.users.find_one.return_value = user
            with patch('services.personal_numbers.debit_credits', new=AsyncMock()) as debit:
                with self.assertRaises(HTTPException):
                    await personal_numbers_result(db, 'u', date, 1)
                debit.assert_not_awaited()
