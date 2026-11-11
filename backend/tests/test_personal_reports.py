"""Explanations, historical provenance, and the authenticated free latest-result boundary."""
import copy
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import FastAPI
from fastapi.testclient import TestClient
from auth import get_current_user
from domain.personal_report import build_personal_report
from numerology import calculate_personal_numbers, reduce_to_single_digit
from routers.personal_reports import create_personal_reports_router


def prepared_result(date='10.01.1982', name_number=6):
    result = calculate_personal_numbers(date)
    result['full_name_number'] = name_number
    result['wisdom_number'] = reduce_to_single_digit(result['destiny_number'] + name_number)
    return result


class ReportExplanations(unittest.TestCase):
    def report(self, date='10.01.1982'):
        return build_personal_report(date, prepared_result(date), name='Anna', surname='Li', profile_birth_date=date)

    def test_complete_report_has_real_methods_and_planet_digits(self):
        report = self.report()
        self.assertEqual(report['version'], 1)
        self.assertEqual(report['birth_weekday'], 'воскресенье')
        self.assertEqual(report['profile_name'], 'Anna Li')
        self.assertEqual([item['key'] for item in report['numbers']],
                         ['soul_number', 'mind_number', 'destiny_number', 'helping_mind_number', 'wisdom_number', 'ruling_number', 'full_name_number'])
        entries = {item['key']: item for item in report['numbers']}
        for item in entries.values():
            self.assertTrue(item['title'])
            self.assertTrue(item['meaning'])
            self.assertTrue(item['method'])
            self.assertTrue(item['steps'])
            self.assertIn('NumerOM', item['interpretation'])
        self.assertIn('10 + 1 + 1982 = 1993', entries['destiny_number']['steps'])
        self.assertIn('1 + 9 + 9 + 3 = 22', entries['destiny_number']['steps'])
        self.assertIn('2 + 2 = 4', entries['destiny_number']['steps'])
        self.assertIn('Месяц рождения: 1', entries['mind_number']['steps'])
        self.assertIn('4 + 6 = 10', entries['wisdom_number']['steps'])
        self.assertIn('1 + 0 = 1', entries['wisdom_number']['steps'])
        self.assertIn('A=1', ' '.join(entries['full_name_number']['steps']))
        self.assertIn('5 + 1 = 6', entries['full_name_number']['steps'])
        self.assertEqual(report['planets']['calculation_number'], 1983982)
        self.assertEqual(report['planets']['formula'], '1001 × 1982 = 1983982')
        self.assertEqual([item['value'] for item in report['planets']['items']], [1, 9, 8, 3, 9, 8, 2])
        self.assertTrue(all(0 <= item['value'] <= 9 for item in report['planets']['items']))
        self.assertIn('не проценты', report['planets']['note'])

    def test_master_rules_match_each_existing_number(self):
        for date in ['22.11.1982', '29.11.1991', '11.11.2011', '31.12.1999', '01.01.0001',
                     '28.02.1983', '29.12.1986']:
            with self.subTest(date=date):
                result = prepared_result(date)
                report = self.report(date)
                entries = {item['key']: item for item in report['numbers']}
                for key in ['soul_number', 'mind_number', 'destiny_number', 'helping_mind_number', 'wisdom_number', 'ruling_number', 'full_name_number']:
                    self.assertEqual(entries[key]['value'], result[key])
                    self.assertTrue(entries[key]['steps'])
                    self.assertTrue(entries[key]['steps'][-1].startswith(f"Итог: {entries[key]['value']}"))
                self.assertLessEqual(entries['destiny_number']['value'], 9)
                self.assertNotEqual(entries['ruling_number']['value'], 33)
        master = {item['key']: item for item in self.report('22.11.1982')['numbers']}
        self.assertEqual(master['soul_number']['value'], 22)
        self.assertEqual(master['mind_number']['value'], 11)
        self.assertEqual(master['helping_mind_number']['value'], 33)
        self.assertIn('33', master['helping_mind_number']['steps'][-1])
        self.assertNotIn('3 + 3 = 6', master['helping_mind_number']['steps'])
        ruling_33 = next(item for item in self.report('28.02.1983')['numbers'] if item['key'] == 'ruling_number')
        self.assertIn('3 + 3 = 6', ruling_33['steps'])
        ruling_chain = next(item for item in self.report('29.12.1986')['numbers'] if item['key'] == 'ruling_number')
        self.assertIn('3 + 8 = 11', ruling_chain['steps'])
        self.assertEqual(ruling_chain['value'], 11)

    def test_a_different_requested_date_keeps_name_provenance_explicit(self):
        report = build_personal_report('10.01.1982', prepared_result(),
                                      name='Anna', surname='Li', profile_birth_date='02.03.1990')
        notes = [item['note'] or '' for item in report['numbers'] if item['key'] in {'full_name_number', 'wisdom_number'}]
        self.assertTrue(all('профил' in note and 'отличается' in note for note in notes))

    def test_legacy_explains_saved_values_without_new_profile_or_false_formula(self):
        result = calculate_personal_numbers('10.01.1982')
        result.update(full_name_number=0, soul_number=8)
        before = copy.deepcopy(result)
        report = build_personal_report('10.01.1982', result, legacy=True)
        entries = {item['key']: item for item in report['numbers']}
        self.assertEqual(result, before)
        self.assertIsNone(report['profile_name'])
        self.assertEqual(entries['wisdom_number']['value'], 8)
        self.assertEqual(entries['full_name_number']['value'], 0)
        self.assertTrue(entries['wisdom_number']['note'])
        self.assertTrue(entries['full_name_number']['note'])
        self.assertIsNone(entries['wisdom_number']['interpretation'])
        self.assertEqual(entries['soul_number']['steps'], [])
        self.assertIn('не совпадает', entries['soul_number']['note'])
        self.assertIn('2 + 2 = 4', entries['destiny_number']['steps'])

    def test_legacy_does_not_invent_planet_strengths_when_absent(self):
        report = build_personal_report('10.01.1982', {'destiny_number': 4}, legacy=True)
        self.assertEqual(report['planets']['items'], [])
        self.assertIn('не сохранены', report['planets']['note'])


class LatestPersonalReports(unittest.TestCase):
    def setUp(self):
        self.user = {'id': 'u', 'credits_remaining': 0, 'name': 'CURRENT', 'surname': 'PROFILE',
                     'birth_date': '01.01.2000', 'password_hash': 'private', 'pending_calculations': []}
        self.documents = []
        self.queries = []

        async def read_user(query, projection=None):
            return copy.deepcopy(self.user) if self.user and self.user['id'] == query.get('id') else None

        async def read_calculation(query, projection=None, sort=None):
            self.queries.append((query, projection, sort))
            matches = [doc for doc in self.documents if all(doc.get(key) == value for key, value in query.items())]
            return copy.deepcopy(max(matches, key=lambda doc: doc['created_at'])) if matches else None

        self.db = SimpleNamespace(
            users=SimpleNamespace(find_one=AsyncMock(side_effect=read_user), update_one=AsyncMock()),
            numerology_calculations=SimpleNamespace(find_one=AsyncMock(side_effect=read_calculation), update_one=AsyncMock()),
            credit_transactions=SimpleNamespace(insert_one=AsyncMock()))
        app = FastAPI()
        app.include_router(create_personal_reports_router(self.db))
        app.dependency_overrides[get_current_user] = lambda: {'user_id': 'u'}
        self.app = app
        self.client = TestClient(app, raise_server_exceptions=False)

    def record(self, identifier, user_id='u', when=datetime(2026, 10, 15), calculation_type='personal_numbers'):
        return {'id': identifier, '_id': 'internal-id', 'user_id': user_id, 'private_secret': 'hidden',
                'birth_date': '10.01.1982', 'created_at': when, 'calculation_type': calculation_type,
                'results': calculate_personal_numbers('10.01.1982')}

    def get(self):
        return self.client.get('/api/numerology/personal-numbers/latest')

    def assert_read_only(self):
        self.db.users.update_one.assert_not_awaited()
        self.db.numerology_calculations.update_one.assert_not_awaited()
        self.db.credit_transactions.insert_one.assert_not_awaited()

    def test_empty_history_returns_null_with_no_charge_or_writes(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'calculation': None})
        self.assert_read_only()

    def test_latest_is_scoped_and_sorted_and_excludes_private_fields(self):
        self.documents = [self.record('mine-old'), self.record('mine-new', when=datetime(2026, 10, 16)),
                          self.record('other-new', user_id='other', when=datetime(2026, 10, 17)),
                          self.record('wrong-type', when=datetime(2026, 10, 18), calculation_type='compatibility')]
        response = self.get()
        self.assertEqual(response.status_code, 200)
        calculation = response.json()['calculation']
        self.assertEqual(calculation['id'], 'mine-new')
        self.assertEqual(set(calculation), {'id', 'birth_date', 'created_at', 'results'})
        query, projection, sort = self.queries[0]
        self.assertEqual(query, {'user_id': 'u', 'calculation_type': 'personal_numbers'})
        self.assertEqual(sort[0], ('created_at', -1))
        self.assertIsNone(calculation['results']['report']['profile_name'])
        self.assert_read_only()

    def test_new_pending_result_is_visible_without_delivery_or_debit(self):
        self.documents = [self.record('archived')]
        pending = self.record('pending', when=datetime(2026, 10, 16, tzinfo=timezone.utc))
        pending['results'] = prepared_result()
        pending['results']['report'] = build_personal_report('10.01.1982', pending['results'], name='Anna', surname='Li')
        self.user['pending_calculations'] = [pending,
            self.record('foreign-pending', user_id='other', when=datetime(2026, 10, 19)),
            self.record('wrong-type', when=datetime(2026, 10, 20), calculation_type='compatibility')]
        before = copy.deepcopy(self.user)
        response = self.get()
        self.assertEqual(response.status_code, 200)
        saved = response.json()['calculation']
        self.assertEqual(saved['id'], 'pending')
        self.assertEqual(saved['results']['report'], pending['results']['report'])
        self.assertEqual(self.user, before)
        self.assert_read_only()

    def test_archive_can_be_newer_than_pending_and_duplicate_read_stays_free(self):
        self.documents = [self.record('latest', when=datetime(2026, 10, 16))]
        self.user['pending_calculations'] = [self.record('older')]
        for _ in range(2):
            self.assertEqual(self.get().json()['calculation']['id'], 'latest')
        self.assert_read_only()

    def test_disabled_or_deleted_user_is_denied_before_history_lookup(self):
        for user in [{'id': 'u', 'is_disabled': True}, None]:
            self.user = user
            self.assertEqual(self.get().status_code, 401)
        self.db.numerology_calculations.find_one.assert_not_awaited()
        self.assert_read_only()

    def test_anonymous_request_is_denied(self):
        self.app.dependency_overrides.clear()
        self.assertEqual(self.get().status_code, 401)
        self.db.users.find_one.assert_not_awaited()

    def test_storage_outage_is_not_silently_reported_as_empty(self):
        self.db.numerology_calculations.find_one.side_effect = RuntimeError('synthetic archive outage')
        self.assertEqual(self.get().status_code, 500)
        self.assert_read_only()

    def test_corrupt_record_is_not_silently_reported_as_empty(self):
        self.documents = [self.record('broken')]
        self.documents[0]['results'] = None
        self.assertEqual(self.get().status_code, 500)
        self.assert_read_only()


if __name__ == '__main__':
    unittest.main()
