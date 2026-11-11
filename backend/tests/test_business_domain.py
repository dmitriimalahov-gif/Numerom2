"""Synthetic import and evidence-only business report acceptance tests."""
from copy import deepcopy
import csv
from datetime import date, datetime
from io import BytesIO, StringIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openpyxl import Workbook
from pydantic import ValidationError
from domain.business import (EmployeeInput, GroupInput, MAX_FILE_BYTES, analyze_group,
                             employee_identity, parse_employee_file)


def employee(**changes):
    return {'name': 'Анна', 'surname': 'Тестовая', 'birth_date': '02.03.1990',
            'department': '', 'role': '', 'skills': [], 'experience': '',
            'interests': [], 'hours_per_week': None, **changes}


def group(**changes):
    return {'name': 'Запуск', 'task': 'Подготовить запуск продукта', 'required_skills': [],
            'target_hours': None, 'member_ids': [], **changes}


def csv_bytes(rows, headers=('Имя', 'Фамилия', 'Дата рождения'), delimiter=';'):
    out = StringIO(newline='')
    writer = csv.writer(out, delimiter=delimiter)
    writer.writerow(headers)
    writer.writerows(rows)
    return out.getvalue().encode('utf-8-sig')


def xlsx_bytes(rows, headers=('Имя', 'Фамилия', 'Дата рождения'), configure=None):
    book = Workbook()
    book.active.append(list(headers))
    for row in rows:
        book.active.append(row)
    if configure:
        configure(book)
    out = BytesIO()
    book.save(out)
    book.close()
    return out.getvalue()


def alter_archive(content, replacements=None, additional=None):
    replacements = replacements or {}
    out = BytesIO()
    with ZipFile(BytesIO(content)) as source, ZipFile(out, 'w', ZIP_DEFLATED) as target:
        for item in source.infolist():
            data = source.read(item.filename)
            transform = replacements.get(item.filename)
            target.writestr(item.filename, transform(data) if callable(transform) else transform or data)
        for name, data in (additional or {}).items():
            target.writestr(name, data)
    return out.getvalue()


class EmployeeValidationTests(unittest.TestCase):
    def test_models_normalize_dates_and_retain_unknowns(self):
        result = EmployeeInput.model_validate(employee(name='  Jean-Luc  ', surname='O’Neil', birth_date='1990-03-02', skills=[' SQL ', 'sql', 'Тестирование'], interests=['Планирование']))
        self.assertEqual(result.name, 'Jean-Luc')
        self.assertEqual(result.birth_date, '02.03.1990')
        self.assertEqual(result.skills, ['SQL', 'Тестирование'])
        self.assertIsNone(result.hours_per_week)
        self.assertIsNone(EmployeeInput(name='А', surname='Б').birth_date)

    def test_invalid_fields_and_coercion_are_rejected(self):
        bad = [{'name': ''}, {'name': 123}, {'name': 'a' * 81}, {'name': 'А\x00Б'},
               {'surname': 'a' * 81}, {'department': 'x' * 121}, {'role': 'x' * 121},
               {'skills': 'SQL'}, {'skills': ['x'] * 31}, {'skills': ['']}, {'skills': [1]},
               {'skills': ['x' * 81]}, {'interests': ['x'] * 21}, {'experience': 'x' * 2001},
               {'birth_date': '31.02.1990'}, {'birth_date': '1899-01-01'}, {'birth_date': '2999-01-01'},
               {'birth_date': 33000}, {'hours_per_week': True}, {'hours_per_week': '40'},
               {'hours_per_week': -1}, {'hours_per_week': 169}, {'hours_per_week': float('inf')},
               {'hours_per_week': float('nan')}, {'hours_per_week': 10 ** 1000}, {'gender': 'female'}]
        for change in bad:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                EmployeeInput.model_validate(employee(**change))

    def test_groups_validate_unique_ids_and_bounds(self):
        self.assertEqual(GroupInput.model_validate(group(required_skills=[' SQL ', 'sql'])).required_skills, ['SQL'])
        for change in [{'name': ''}, {'task': ''}, {'member_ids': ['a', 'a']},
                       {'member_ids': [str(i) for i in range(21)]}, {'target_hours': True},
                       {'target_hours': '30'}, {'target_hours': -1}, {'target_hours': 3361},
                       {'required_skills': ['x'] * 31}, {'extra': 'forbidden'}]:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                GroupInput.model_validate(group(**change))

    def test_identity_normalizes_unicode_case_whitespace_and_date(self):
        first = EmployeeInput.model_validate(employee(name='  ANNA  Maria ', surname='Ｔｅｓｔ', birth_date='1990-03-02')).model_dump()
        second = EmployeeInput.model_validate(employee(name='anna maria', surname='test')).model_dump()
        self.assertEqual(employee_identity(first), employee_identity(second))


class EmployeeImportTests(unittest.TestCase):
    def test_250_rows_accepted_without_truncation_and_251_rejected(self):
        rows = [[f'Имя{i}', f'Фамилия{i}', '1990-01-01'] for i in range(251)]
        for extension, generate in [('csv', csv_bytes), ('xlsx', xlsx_bytes)]:
            good = parse_employee_file('team.' + extension, generate(rows[:250]))
            self.assertTrue(good['valid'], good['issues'])
            self.assertEqual((good['row_count'], len(good['employees'])), (250, 250))
            bad = parse_employee_file('team.' + extension, generate(rows))
            self.assertFalse(bad['valid'])
            self.assertEqual(bad['row_count'], 251)
            self.assertTrue(any('250' in item['message'] for item in bad['issues']))

    def test_optional_evidence_and_aliases(self):
        headers = ['first_name', 'last_name', 'birth_date', 'Отдел', 'Должность', 'Навыки', 'Опыт', 'Интересы', 'Часов в неделю']
        result = parse_employee_file('staff.CSV', csv_bytes([[' Анна ', 'Тестовая', '02.03.1990', 'ИТ', 'Инженер', 'SQL; Python; sql', 'Два проекта', 'Обучение;Процессы', '20,5']], headers))
        self.assertTrue(result['valid'], result['issues'])
        self.assertEqual(result['employees'][0], employee(department='ИТ', role='Инженер', skills=['SQL', 'Python'], experience='Два проекта', interests=['Обучение', 'Процессы'], hours_per_week=20.5))

    def test_comma_and_tab_csv_preserve_quoted_multiline_experience(self):
        for delimiter in (',', '\t'):
            result = parse_employee_file('team.csv', csv_bytes([['А', 'Б', 'Первый проект\nВторой проект']], ('name', 'surname', 'experience'), delimiter))
            self.assertTrue(result['valid'], result['issues'])
            self.assertEqual(result['employees'][0]['experience'], 'Первый проект\nВторой проект')

    def test_blank_cell_and_missing_name_errors_are_actionable_russian(self):
        result = parse_employee_file('team.csv', csv_bytes([['', 'Б', ''], ['В', '', '']]))
        self.assertFalse(result['valid'])
        self.assertTrue(all('символ' in issue['message'] for issue in result['issues']), result['issues'])

    def test_internal_employee_row_map_tracks_blank_rows(self):
        result = parse_employee_file('team.csv', csv_bytes([[], ['А', 'Б', ''], [], ['В', 'Г', '']]))
        self.assertEqual(result['_employee_rows'], [3, 5])

    def test_typed_excel_dates_and_blank_optional_values(self):
        result = parse_employee_file('team.xlsx', xlsx_bytes([['А', 'Б', datetime(1990, 3, 2)], ['В', 'Г', None]]))
        self.assertTrue(result['valid'], result['issues'])
        self.assertEqual([e['birth_date'] for e in result['employees']], ['02.03.1990', None])

    def test_original_row_numbers_and_no_silent_bad_rows(self):
        result = parse_employee_file('team.csv', csv_bytes([['А', 'Б', '1990-01-01'], [], ['В', 'Г', '31.02.2000'], ['', 'Д', '']]))
        self.assertFalse(result['valid'])
        self.assertEqual(result['row_count'], 3)
        self.assertEqual({item['row'] for item in result['issues']}, {4, 5})
        self.assertEqual(len(result['employees']), 1)

    def test_exact_duplicates_rejected_names_only_warned(self):
        duplicate = parse_employee_file('team.csv', csv_bytes([['А', 'Б', '1990-01-01'], [' а ', 'б', '01.01.1990']]))
        self.assertFalse(duplicate['valid'])
        self.assertEqual(duplicate['issues'][0]['row'], 3)
        same_name = parse_employee_file('team.csv', csv_bytes([['А', 'Б', '1990-01-01'], ['А', 'Б', '1991-01-01'], ['А', 'Б', '']]))
        self.assertTrue(same_name['valid'])
        self.assertEqual([w['row'] for w in same_name['warnings']], [3, 4])

    def test_headers_are_required_unambiguous_and_known(self):
        for headers in [('Имя', 'Отдел'), ('Имя', 'name', 'Фамилия'), ('Имя', 'Фамилия', 'Зарплата')]:
            result = parse_employee_file('team.csv', csv_bytes([['А', 'Б', 'В']], headers))
            self.assertFalse(result['valid'])
            self.assertTrue(any(item['row'] == 1 for item in result['issues']))

    def test_csv_formula_injection_and_excel_formulas_rejected(self):
        for formula in ['=1+1', '+SUM(1,2)', '@SUM(A1:A2)', '-2+3', ' \t=HYPERLINK("https://example.invalid")']:
            result = parse_employee_file('team.csv', csv_bytes([['А', formula, '']]))
            self.assertFalse(result['valid'])
            self.assertEqual(result['issues'][0]['row'], 2)
        result = parse_employee_file('team.xlsx', xlsx_bytes([['А', 'Б', '=TODAY()']]))
        self.assertFalse(result['valid'])
        self.assertTrue(any('формул' in item['message'].lower() for item in result['issues']))

    def test_extra_cells_and_nontext_identity_rejected(self):
        for rows in [[['А', 'Б', '', 'лишнее']], [[123, 'Б', None]]]:
            result = parse_employee_file('team.xlsx', xlsx_bytes(rows))
            self.assertFalse(result['valid'])

    def test_legacy_macro_invalid_encoding_and_empty_files_rejected(self):
        for filename, content in [('team.xls', b'old'), ('team.xlsm', b'macro'), ('team.zip', b'zip'),
                                  ('team.csv', b'\xff\xff'), ('team.csv', b''), ('team.xlsx', b'bad')]:
            result = parse_employee_file(filename, content)
            self.assertFalse(result['valid'])
            self.assertEqual(result['employees'], [])
        self.assertIn('XLSX', parse_employee_file('team.xls', b'old')['issues'][0]['message'])

    def test_file_size_archive_ratio_xml_entities_and_external_links_rejected_before_load(self):
        base = xlsx_bytes([['А', 'Б', None]])
        dangerous = [b'X' * (MAX_FILE_BYTES + 1),
                     alter_archive(base, additional={'xl/payload.xml': b'x' * 2_000_000}),
                     alter_archive(base, additional={'xl/evil.xml': b'<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><x>&e;</x>'}),
                     alter_archive(base, additional={'xl/_rels/evil.rels': b'<Relationships><Relationship TargetMode="External" Target="https://example.invalid" /></Relationships>'}),
                     alter_archive(base, additional={'xl/vbaProject.bin': b'macro'})]
        with patch('domain.business.load_workbook') as loader:
            for content in dangerous:
                result = parse_employee_file('team.xlsx', content)
                self.assertFalse(result['valid'], result)
            loader.assert_not_called()

    def test_dimensions_and_multiple_sheets_rejected_without_unbounded_iteration(self):
        content = xlsx_bytes([['А', 'Б', None]])
        altered = alter_archive(content, {'xl/worksheets/sheet1.xml': lambda value: value.replace(b'ref="A1:C2"', b'ref="A1:XFD1048576"')})
        with patch('domain.business.load_workbook') as loader:
            result = parse_employee_file('team.xlsx', altered)
            self.assertFalse(result['valid'])
            loader.assert_not_called()
        multiple = xlsx_bytes([['А', 'Б', None]], configure=lambda workbook: workbook.create_sheet('Extra'))
        self.assertFalse(parse_employee_file('team.xlsx', multiple)['valid'])

    def test_hidden_formula_ignored_dimension_cannot_bypass_preflight(self):
        content = xlsx_bytes([['А', 'Б', None]], configure=lambda workbook: setattr(workbook.active['Z900'], 'value', '=1+1'))
        content = alter_archive(content, {'xl/worksheets/sheet1.xml': lambda value: value.replace(b'ref="A1:Z900"', b'ref="A1:C2"')})
        self.assertFalse(parse_employee_file('team.xlsx', content)['valid'])

    def test_renamed_xml_part_cannot_bypass_preflight(self):
        base = xlsx_bytes([['А', 'Б', None]])
        for disguised_type in (False, True):
            out = BytesIO()
            with ZipFile(BytesIO(base)) as source, ZipFile(out, 'w', ZIP_DEFLATED) as target:
                for item in source.infolist():
                    name, data = item.filename, source.read(item.filename)
                    if name == 'xl/worksheets/sheet1.xml':
                        name = 'xl/worksheets/sheet1.bin'
                    elif name == 'xl/_rels/workbook.xml.rels':
                        data = data.replace(b'sheet1.xml', b'sheet1.bin')
                        if disguised_type:
                            data = data.replace(b'/worksheet"', b'/image"')
                    target.writestr(name, data)
            with self.subTest(disguised_type=disguised_type), patch('domain.business.load_workbook') as loader:
                result = parse_employee_file('team.xlsx', out.getvalue())
                self.assertFalse(result['valid'])
                loader.assert_not_called()

    def test_mass_invalid_cells_produce_bounded_errors_and_explicit_total(self):
        headers = ['Имя', 'Фамилия'] + [''] * 30
        rows = [[f'Имя{i}', f'Фамилия{i}'] + ['лишнее'] * 30 for i in range(250)]
        result = parse_employee_file('team.csv', csv_bytes(rows, headers))
        self.assertFalse(result['valid'])
        self.assertLessEqual(len(result['issues']), 1001)
        self.assertIn('7500', result['issues'][-1]['message'])
        self.assertEqual(result['row_count'], 250)

    def test_renamed_xml_worksheet_preserves_coordinate_preflight(self):
        base = xlsx_bytes([['А', 'Б', None]])

        def renamed(transform=lambda data: data):
            out = BytesIO()
            with ZipFile(BytesIO(base)) as source, ZipFile(out, 'w', ZIP_DEFLATED) as target:
                for item in source.infolist():
                    name, data = item.filename, source.read(item.filename)
                    if name == 'xl/worksheets/sheet1.xml':
                        name, data = 'xl/hidden.xml', transform(data)
                    else:
                        data = data.replace(b'/xl/worksheets/sheet1.xml', b'/xl/hidden.xml')
                    target.writestr(name, data)
            return out.getvalue()

        valid = parse_employee_file('team.xlsx', renamed())
        self.assertTrue(valid['valid'], valid['issues'])
        for label, transform in [
            ('dimension', lambda data: data.replace(b'ref="A1:C2"', b'ref="A1:XFD1048576"')),
            ('row', lambda data: data.replace(b'<row r="2"', b'<row r="1002"')),
            ('cell', lambda data: data.replace(b'<c r="A2"', b'<c r="AG2"')),
        ]:
            with self.subTest(label=label), patch('domain.business.load_workbook') as loader:
                result = parse_employee_file('team.xlsx', renamed(transform))
                self.assertFalse(result['valid'])
                loader.assert_not_called()


class BusinessReportTests(unittest.TestCase):
    def setUp(self):
        self.people = [{'id': 'a', **employee(skills=[' SQL ', 'Python'], hours_per_week=20)},
                       {'id': 'b', **employee(name='Борис', surname='Примеров', skills=['Продажи'], hours_per_week=10)}]
        self.task = group(member_ids=['b', 'a'], required_skills=['sql', 'Продажи', 'Дизайн'], target_hours=40)

    def test_exact_skill_coverage_is_not_a_rank_and_preserves_manual_group_order(self):
        report = analyze_group(self.people, self.task)
        self.assertEqual(report['coverage'], [{'skill': 'sql', 'employee_ids': ['a']}, {'skill': 'Продажи', 'employee_ids': ['b']}, {'skill': 'Дизайн', 'employee_ids': []}])
        self.assertEqual(report['missing_skills'], ['Дизайн'])
        self.assertEqual(report['available_hours'], 30)
        self.assertEqual([m['id'] for m in report['members']], ['b', 'a'])
        self.assertEqual(report['member_count'], 2)
        self.assertNotIn('score', report)
        self.assertTrue(report['next_steps'])

    def test_names_birth_dates_role_and_experience_do_not_influence_coverage(self):
        original = analyze_group(self.people, self.task)
        changed = deepcopy(self.people)
        for person in changed:
            person.update(name='Другое имя', surname='Другая фамилия', birth_date='01.01.2000', role='Директор', experience='Любой текст', interests=['Дизайн'])
        changed_report = analyze_group(changed, self.task)
        for key in ('coverage', 'missing_skills', 'available_hours', 'missing_hours_data', 'next_steps'):
            self.assertEqual(original[key], changed_report[key], key)

    def test_unknown_hours_stay_unknown_and_missing_skills_are_not_fabricated(self):
        self.people[0]['hours_per_week'] = None
        self.people[0]['skills'] = []
        result = analyze_group(self.people, self.task)
        self.assertIsNone(result['available_hours'])
        self.assertEqual(result['missing_hours_data'], ['a'])
        self.assertEqual(result['missing_skills'], ['sql', 'Дизайн'])

    def test_no_substring_matching_and_no_unselected_employees(self):
        self.people[0]['skills'] = ['PostgreSQL']
        result = analyze_group(self.people, group(member_ids=['a'], required_skills=['SQL', 'Продажи']))
        self.assertEqual(result['missing_skills'], ['SQL', 'Продажи'])

    def test_empty_group_has_zero_members_and_incomplete_task_evidence(self):
        result = analyze_group(self.people, group(required_skills=['SQL']))
        self.assertEqual(result['members'], [])
        self.assertEqual(result['available_hours'], 0)
        self.assertEqual(result['missing_skills'], ['SQL'])

    def test_unknown_and_duplicate_member_ids_cannot_silently_disappear(self):
        for ids in [['not-owned'], ['a', 'a']]:
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                analyze_group(self.people, group(member_ids=ids))


if __name__ == '__main__':
    unittest.main()
