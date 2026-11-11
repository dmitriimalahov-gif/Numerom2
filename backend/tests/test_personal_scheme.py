"""Square accuracy, saved-date provenance, and read-only report enrichment."""
import copy
import sys
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import FastAPI
from fastapi.testclient import TestClient
from auth import get_current_user
from domain.personal_report import build_personal_report
from domain.personal_scheme import build_personal_scheme
from numerology import create_pythagorean_square
from routers.personal_reports import create_personal_reports_router
from services.personal_numbers import personal_numbers_result


class PersonalScheme(unittest.TestCase):
    def test_known_date_has_exact_cells_additional_numbers_and_all_line_sums(self):
        scheme = build_personal_scheme('10.01.1982')
        self.assertEqual(scheme['version'], 1)
        self.assertEqual(scheme['birth_date'], '10.01.1982')
        self.assertEqual(scheme['additional_numbers'], [22, 4, 20, 2])
        self.assertEqual([cell['digit'] for cell in scheme['cells']], [1, 4, 7, 2, 5, 8, 3, 6, 9])
        self.assertEqual([cell['digits'] for cell in scheme['cells']],
                         ['111', '4', '', '22222', '', '8', '', '', '9'])
        self.assertEqual([cell['count'] for cell in scheme['cells']], [3, 1, 0, 5, 0, 1, 0, 0, 1])
        self.assertEqual([(line['key'], line['digits'], line['value']) for line in scheme['lines']], [
            ('row-0', [1, 4, 7], 4), ('row-1', [2, 5, 8], 6), ('row-2', [3, 6, 9], 1),
            ('col-0', [1, 2, 3], 8), ('col-1', [4, 5, 6], 1), ('col-2', [7, 8, 9], 2),
            ('diag-0', [1, 5, 9], 4), ('diag-1', [3, 5, 7], 0),
        ])
        for item in scheme['cells'] + scheme['lines']:
            self.assertTrue(item['title'])
            self.assertIn('символике NumerOM', item['meaning'])

    def test_single_digit_day_keeps_existing_leading_zero_method(self):
        scheme = build_personal_scheme('02.03.1990')
        self.assertEqual(scheme['additional_numbers'], [24, 6, 24, 6])
        self.assertEqual([cell['count'] for cell in scheme['cells']], [1, 2, 0, 3, 0, 0, 1, 2, 2])
        self.assertEqual([line['value'] for line in scheme['lines']], [3, 3, 5, 5, 4, 2, 3, 1])
        self.assertIn('для 01–09 это 0', scheme['method'])

    def test_scheme_matches_authoritative_square_and_each_line_matches_its_cells(self):
        for date in ['10.01.1982', '02.03.1990', '29.02.2000', '31.12.1999', '01.01.0001']:
            with self.subTest(date=date):
                day, month, year = map(int, date.split('.'))
                expected = create_pythagorean_square(day, month, year)
                scheme = build_personal_scheme(date)
                self.assertEqual(scheme['additional_numbers'], expected['additional_numbers'])
                self.assertEqual([cell['digits'] for cell in scheme['cells']],
                                 [value for row in expected['square'] for value in row])
                counts = {cell['digit']: cell['count'] for cell in scheme['cells']}
                for cell in scheme['cells']:
                    self.assertEqual(cell['digits'], str(cell['digit']) * cell['count'])
                for line in scheme['lines']:
                    self.assertEqual(line['value'], sum(counts[digit] for digit in line['digits']))

    def test_invalid_or_noncanonical_dates_produce_no_scheme_or_calculation(self):
        invalid = [None, '', 10011982, {}, '1.1.1982', '10.1.1982', '1982-01-10',
                   '31.02.1982', '29.02.1900', '00.01.1982', '10.13.1982', '01.01.0000',
                   '10.01.1982 ', '１０.０１.１９８２', '10.01.1982\n']
        with patch('domain.personal_scheme.create_pythagorean_square') as calculate:
            for date in invalid:
                with self.subTest(date=date):
                    self.assertIsNone(build_personal_scheme(date))
            calculate.assert_not_called()

    def test_report_uses_its_date_and_does_not_change_stored_values(self):
        results = {'soul_number': 8, 'destiny_number': 7, 'wisdom_number': 33}
        before = copy.deepcopy(results)
        report = build_personal_report('10.01.1982', results,
                                       profile_birth_date='02.03.1990', legacy=True)
        self.assertEqual(results, before)
        self.assertEqual(report['scheme']['birth_date'], report['birth_date'])
        self.assertEqual(report['scheme']['additional_numbers'], [22, 4, 20, 2])
        self.assertIn('сохранённой дате рождения текущим методом', report['scheme']['note'])
        self.assertEqual(next(item['value'] for item in report['numbers'] if item['key'] == 'soul_number'), 8)
        self.assertIsNone(build_personal_report('invalid', results, legacy=True)['scheme'])


class PreparedScheme(unittest.IsolatedAsyncioTestCase):
    async def test_requested_date_scheme_is_attached_before_atomic_debit(self):
        db = SimpleNamespace(users=SimpleNamespace(
            find_one=AsyncMock(return_value={'id': 'u', 'birth_date': '02.03.1990', 'name': 'Anna', 'surname': 'Li'}),
            update_one=AsyncMock()))

        async def inspect_debit(*args, **kwargs):
            record = kwargs['calculation']
            self.assertEqual(record['birth_date'], '10.01.1982')
            self.assertEqual(record['results']['report']['scheme']['birth_date'], record['birth_date'])
            self.assertEqual(record['results']['report']['scheme']['additional_numbers'], [22, 4, 20, 2])

        with patch('services.personal_numbers.debit_credits', new=AsyncMock(side_effect=inspect_debit)) as debit:
            result = await personal_numbers_result(db, 'u', '10.01.1982', 7)
        self.assertEqual(debit.await_count, 1)
        self.assertEqual(debit.call_args.kwargs['calculation']['results']['report']['scheme'], result['report']['scheme'])

    async def test_scheme_calculation_failure_never_reaches_debit(self):
        db = SimpleNamespace(users=SimpleNamespace(
            find_one=AsyncMock(return_value={'id': 'u', 'birth_date': '10.01.1982'}),
            update_one=AsyncMock()))
        with patch('domain.personal_scheme.create_pythagorean_square', side_effect=RuntimeError('synthetic square failure')), \
                patch('services.personal_numbers.debit_credits', new=AsyncMock()) as debit:
            with self.assertRaises(RuntimeError):
                await personal_numbers_result(db, 'u', None, 7)
            debit.assert_not_awaited()


class LatestScheme(unittest.TestCase):
    def setUp(self):
        self.user = {'id': 'u', 'birth_date': '02.03.1990', 'pending_calculations': [], 'credits_remaining': 0}
        self.records = []

        async def read_record(query, projection=None, sort=None):
            matches = [record for record in self.records
                       if all(record.get(key) == value for key, value in query.items())]
            return max(matches, key=lambda record: (record['created_at'], record['id'])) if matches else None

        self.db = SimpleNamespace(
            users=SimpleNamespace(find_one=AsyncMock(return_value=self.user), update_one=AsyncMock()),
            numerology_calculations=SimpleNamespace(find_one=AsyncMock(side_effect=read_record), update_one=AsyncMock()),
            credit_transactions=SimpleNamespace(insert_one=AsyncMock()))
        app = FastAPI()
        app.include_router(create_personal_reports_router(self.db))
        app.dependency_overrides[get_current_user] = lambda: {'user_id': 'u'}
        self.client = TestClient(app)

    def record(self, identifier='saved', owner='u', day=15):
        return {'id': identifier, 'user_id': owner, 'calculation_type': 'personal_numbers',
                'birth_date': '10.01.1982', 'created_at': datetime(2026, 10, day),
                'results': {'soul_number': 8, 'wisdom_number': 33, 'report': {
                    'version': 1, 'birth_date': '10.01.1982', 'profile_name': 'Historic Name',
                    'numbers': [{'key': 'soul_number', 'value': 8, 'note': 'Historic explanation'}],
                    'planets': {'items': [{'name': 'Солнце', 'value': 9}]}, 'extra': ['preserve'],
                }}}

    def latest(self):
        response = self.client.get('/api/numerology/personal-numbers/latest')
        self.assertEqual(response.status_code, 200)
        self.db.users.update_one.assert_not_awaited()
        self.db.numerology_calculations.update_one.assert_not_awaited()
        self.db.credit_transactions.insert_one.assert_not_awaited()
        return response.json()['calculation']

    def test_old_report_adds_only_scheme_on_response_copy(self):
        record = self.record()
        self.records = [record]
        before = copy.deepcopy(record)
        user_before = copy.deepcopy(self.user)
        for _ in range(2):
            result = self.latest()['results']
            scheme = result['report'].pop('scheme')
            self.assertEqual(result, before['results'])
            self.assertEqual(scheme['birth_date'], '10.01.1982')
            self.assertIn('сохранённой дате рождения текущим методом', scheme['note'])
        self.assertEqual(record, before)
        self.assertEqual(self.user, user_before)

    def test_report_date_is_authoritative_even_if_profile_or_record_date_differs(self):
        record = self.record()
        record['birth_date'] = '02.03.1990'
        self.records = [record]
        scheme = self.latest()['results']['report']['scheme']
        self.assertEqual(scheme['birth_date'], record['results']['report']['birth_date'])
        self.assertEqual(scheme['additional_numbers'], [22, 4, 20, 2])

    def test_missing_or_invalid_report_date_has_null_scheme_without_profile_fallback(self):
        for date in [None, '31.02.1982', '1.1.1982']:
            record = self.record()
            if date is None:
                record['results']['report'].pop('birth_date')
            else:
                record['results']['report']['birth_date'] = date
            self.records = [record]
            self.assertIsNone(self.latest()['results']['report']['scheme'])
            self.assertNotIn('scheme', record['results']['report'])

    def test_existing_scheme_including_null_is_preserved(self):
        for scheme in [None, {'version': 1, 'birth_date': '10.01.1982', 'note': 'Saved scheme'}]:
            record = self.record()
            record['results']['report']['scheme'] = scheme
            self.records = [record]
            self.assertEqual(self.latest()['results'], record['results'])

    def test_unknown_report_version_is_not_reinterpreted(self):
        record = self.record()
        record['results']['report']['version'] = 2
        self.records = [record]
        self.assertEqual(self.latest()['results'], record['results'])

    def test_archive_and_pending_enrichment_keep_owner_and_calculation_type_boundaries(self):
        own = self.record('own')
        foreign = self.record('foreign', owner='other', day=18)
        wrong_type = self.record('wrong-type', day=19)
        wrong_type['calculation_type'] = 'compatibility'
        self.records = [own, foreign, wrong_type]
        self.assertEqual(self.latest()['id'], 'own')
        query = self.db.numerology_calculations.find_one.call_args.args[0]
        self.assertEqual(query, {'user_id': 'u', 'calculation_type': 'personal_numbers'})
        pending = self.record('pending', day=16)
        self.user['pending_calculations'] = [pending, foreign, wrong_type]
        before = copy.deepcopy(self.user)
        response = self.latest()
        self.assertEqual(response['id'], 'pending')
        self.assertEqual(response['results']['report']['scheme']['birth_date'], '10.01.1982')
        self.assertEqual(self.user, before)
        self.assertTrue(all('scheme' not in record['results']['report'] for record in self.records))


if __name__ == '__main__':
    unittest.main()
