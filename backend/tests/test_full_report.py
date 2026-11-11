"""The paid report freezes existing arithmetic, text, date and narration together."""
import copy
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from domain.full_report import build_full_report, full_report_clips, _speech_date
from numerology import calculate_planetary_strength, create_pythagorean_square
from vedic_numerology import create_vedic_yantra


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = json.loads((ROOT / 'docs/artifacts/full-report-fixture.json').read_text())


class FullReportArithmetic(unittest.TestCase):
    def test_matches_reference_javascript_all_four_calculations_for_six_dates(self):
        self.assertEqual(FIXTURE['source'], 'packages/numerology-core/comprehensive.js')
        for case in FIXTURE['cases']:
            with self.subTest(birth=case['birth_date']):
                report = build_full_report(case['birth_date'], case['as_of_date'])
                for kind in ('fractal', 'tasks', 'individual', 'cycles'):
                    self.assertEqual(report['raw'][kind], case['expected'][kind], kind)

    def test_1982_master_numbers_and_method_distinctions_are_preserved(self):
        report = build_full_report('10.01.1982', '2026-10-22')
        self.assertEqual(report['raw']['personal'], {
            'soul': 1, 'mind': 1, 'destiny': 4, 'helping_mind': 11,
            'ruling': 22, 'life_path': 22, 'problem': 8,
        })
        self.assertEqual(report['raw']['vedic']['numbers'], {'janma': 4, 'atma': 1, 'bhagya': 4})
        report = build_full_report('29.11.1999', '2026-10-22')
        self.assertEqual(report['raw']['personal']['soul'], 11)
        self.assertEqual(report['raw']['personal']['mind'], 11)
        self.assertEqual(report['raw']['fractal']['digit1'], 2)
        self.assertEqual(report['raw']['fractal']['digit2'], 2)
        self.assertEqual(report['raw']['vedic']['numbers']['atma'], 2)

    def test_square_cells_and_eight_lines_match_authoritative_arithmetic(self):
        for date in ['10.01.1982', '02.03.1990', '29.02.2000']:
            with self.subTest(birth=date):
                report = build_full_report(date, '2026-10-22')
                raw = report['raw']['scheme']
                sections = {s['id']: s for s in report['sections']}
                expected = create_pythagorean_square(*map(int, date.split('.')))
                self.assertEqual(raw['additional_numbers'], expected['additional_numbers'])
                self.assertEqual([cell['digits'] for cell in raw['cells']], [x for row in expected['square'] for x in row])
                self.assertEqual([cell['count'] for cell in raw['cells']], [v['value'] for v in sections['square']['values']])
                counts = {cell['digit']: cell['count'] for cell in raw['cells']}
                self.assertEqual(len(sections['lines']['values']), 8)
                for line in raw['lines']:
                    self.assertEqual(line['value'], sum(counts[d] for d in line['digits']))
                self.assertEqual(sections['square']['chart']['type'], 'matrix')
                self.assertEqual(len(sections['square']['chart']['items']), 9)
        self.assertEqual(build_full_report('02.03.1990', '2026-10-22')['raw']['scheme']['additional_numbers'], [24, 6, 24, 6])

    def test_seven_planet_chart_is_actual_digits_including_zero_and_wraparound(self):
        for date, target in [('10.01.1982', '2026-10-22'), ('01.01.2000', '2026-10-22'), ('31.12.9999', '9999-12-31')]:
            report = build_full_report(date, target)
            expected = calculate_planetary_strength(*map(int, date.split('.')))
            self.assertEqual(report['raw']['planets'], expected)
            section = next(s for s in report['sections'] if s['id'] == 'planets')
            self.assertEqual({v['label']: v['value'] for v in section['values']}, expected['strength'])
            self.assertEqual(len(section['chart']['items']), 7)

    def test_vedic_lines_count_planets_and_stay_separate_from_the_square(self):
        report = build_full_report('10.01.1982', '2026-10-22')
        sections = {s['id']: s for s in report['sections']}
        expected = create_vedic_yantra(10, 1, 1982)
        self.assertEqual(report['raw']['vedic']['yantra'], expected)
        self.assertEqual([v['value'] for v in sections['vedic-yantra']['values']], [3, 0, 0, 1, 0, 1, 0, 0, 1])
        # 1-4-7: 3+0+0, 2-5-8: 1+0+1, 3-6-9: 0+0+1, 1-2-3: 3+1+0, 4-5-6: 0, 7-8-9: 0+1+1, 1-5-9: 3+0+1, 3-5-7: 0.
        self.assertEqual([v['value'] for v in sections['vedic-lines']['values']], [3, 2, 1, 4, 0, 2, 4, 0])
        self.assertEqual(sections['vedic-lines']['steps'][1], 'Горизонталь 2-5-8: 1 + 0 + 1 = 2')
        # «88» is two planets: the line counts, it never adds the digit itself.
        eights = create_vedic_yantra(8, 8, 1980)['yantra_sums']
        self.assertEqual(eights['horizontal'][1], 3)
        self.assertNotEqual(sections['vedic-lines']['values'], sections['lines']['values'])

    def test_zero_tasks_are_explained_and_never_filtered_out(self):
        report = build_full_report('01.01.2000', '2026-10-22')
        section = next(s for s in report['sections'] if s['id'] == 'tasks')
        self.assertEqual(section['values'][0]['value'], 0)
        self.assertIn('совпали', section['values'][0]['meaning'])
        self.assertEqual(section['chart']['items'][0]['value'], 0)

    def test_complete_100_year_data_and_period_boundaries(self):
        for case in FIXTURE['cases']:
            report = build_full_report(case['birth_date'], case['as_of_date'])
            cycles = report['raw']['cycles']
            self.assertEqual([y['age'] for y in cycles['years']], list(range(1, 101)))
            section = next(s for s in report['sections'] if s['id'] == 'cycles')
            self.assertEqual(len(section['values']), 100)
            self.assertEqual(len(section['chart']['items']), 100)
            # The author's table: four nine-year periods from 27 − destiny, «23–32, 32–41, …».
            self.assertEqual(len(cycles['periods']), 4)
            self.assertEqual(cycles['periods'][0]['startAge'], 27 - report['raw']['personal']['destiny'])
            for period in cycles['periods']:
                self.assertEqual(period['endAge'], period['startAge'] + 9)
            for first, second in zip(cycles['periods'], cycles['periods'][1:]):
                self.assertEqual(first['endAge'], second['startAge'])
            for period in cycles['periods']:
                section = next(s for s in report['sections'] if s['id'] == f'cycle-period-{period["index"]}')
                self.assertEqual([v['value'] for v in section['values']], period['periodNumbers'])


class FullReportSnapshot(unittest.TestCase):
    def test_dates_are_strict_existing_and_target_is_mandatory(self):
        invalid = [None, {}, 19820110, '', '1.1.1982', '1982-01-10', '10.01.1982\n',
                   '31.02.1982', '29.02.1900', '０１.０１.１９８２', '00.01.1982', '01.01.0000']
        for date in invalid:
            with self.subTest(birth=date), self.assertRaises((ValueError, TypeError)):
                build_full_report(date, '2026-10-22')
        for target in [None, '', {}, '2026-02-30', '2026-1-1', '2026-10-22Z']:
            with self.subTest(target=target), self.assertRaises((ValueError, TypeError)):
                build_full_report('10.01.1982', target)
        with self.assertRaises(TypeError):
            build_full_report('10.01.1982')
        with self.assertRaises(ValueError):
            build_full_report('23.10.2026', '2026-10-22')

    def test_explicit_date_is_canonical_and_does_not_depend_on_clock(self):
        iso = build_full_report('10.01.1982', '2026-10-22')
        self.assertEqual(iso, build_full_report('10.01.1982', '22.10.2026'))
        later = build_full_report('10.01.1982', '2027-11-23')
        for key in ['personal', 'scheme', 'planets', 'fractal', 'tasks', 'cycles', 'vedic']:
            self.assertEqual(iso['raw'][key], later['raw'][key])
        self.assertNotEqual(iso['raw']['individual'], later['raw']['individual'])
        self.assertEqual(iso['raw']['individual']['currentDate'], {'day': 22, 'month': 10, 'year': 2026})

    def test_new_calls_are_deeply_detached_and_serializable(self):
        first = build_full_report('10.01.1982', '2026-10-22')
        expected = copy.deepcopy(first)
        first['sections'][0]['values'][0]['meaning'] = 'changed'
        first['raw']['cycles']['years'][0]['chlg'] = 999
        first['narration'][0]['text'] = 'changed'
        actual = build_full_report('10.01.1982', '2026-10-22')
        self.assertEqual(actual, expected)
        self.assertEqual(json.loads(json.dumps(actual, allow_nan=False)), actual)

    def test_has_substantive_explanations_and_no_placeholder_profile_values(self):
        report = build_full_report('10.01.1982', '2026-10-22')
        self.assertNotIn('wisdom', report['raw']['personal'])
        self.assertNotIn('full_name', report['raw']['personal'])
        self.assertTrue(any('мудрости' in item['title'] for item in report['excluded']))
        self.assertTrue(any('место' in item['reason'] for item in report['excluded']))
        self.assertTrue(any('других участников' in item['reason'] for item in report['excluded']))
        for section in report['sections']:
            self.assertTrue(section['paragraphs'])
            self.assertTrue(section['steps'])
            for value in section['values']:
                self.assertIsInstance(value['value'], int)
                self.assertTrue(value['meaning'])
        overview = next(s for s in report['sections'] if s['id'] == 'personal')
        self.assertEqual(len(overview['values']), 7)
        self.assertTrue(all(len(value['meaning']) > 150 for value in overview['values']))
        # A date-only arithmetic report makes no medical or employment judgments.
        self.assertNotIn('здоровье', json.dumps(report, ensure_ascii=False))
        self.assertNotIn('подходит для работы', json.dumps(report, ensure_ascii=False))

    def test_fixture_report_matches_current_snapshot(self):
        self.assertEqual(FIXTURE['report'], build_full_report('10.01.1982', '2026-10-22'))


class FullReportNarration(unittest.TestCase):
    def test_text_only_insight_is_spoken_without_null_or_invented_number(self):
        report = build_full_report('10.01.1982', '2026-10-22')
        report['sections'] = [{'id': 'synthesis', 'title': 'Практики', 'paragraphs': [],
            'method': '', 'steps': [], 'values': [{'label': 'Точка внимания', 'value': None,
                'meaning': 'Проверьте намерение на небольшом действии.'}]}]
        audio = next(item for item in full_report_clips(report) if item['id'] == 'full-report-synthesis')
        self.assertIn('Точка внимания. Проверьте намерение', ' '.join(audio['text'].split()))
        self.assertNotIn('None', audio['text'])
        self.assertNotIn('Точка внимания: 0', audio['text'])

    def test_every_section_has_bounded_personalized_audio_with_stable_ids(self):
        report = build_full_report('10.01.1982', '2026-10-22')
        clips = report['narration']
        self.assertEqual(len({c['id'] for c in clips}), len(clips))
        self.assertEqual(clips[0]['id'], 'full-report-summary')
        self.assertEqual(clips[-1]['id'], 'full-report-excluded')
        self.assertTrue(all(c['id'].startswith('full-report-') for c in clips))
        self.assertTrue(all(c['section'] == 'full-report' for c in clips))
        self.assertTrue(all(0 < len(c['text']) <= 20000 for c in clips))
        self.assertTrue(all(re.fullmatch('[0-9a-f]{64}', c['hash']) for c in clips))
        for section in report['sections']:
            audio = next(c for c in clips if c['id'] == 'full-report-' + section['id'])
            self.assertEqual(section['title'], audio['title'])
            if section['id'] != 'cycles':
                for value in section['values']:
                    self.assertIn(str(value['value']), audio['text'])
        self.assertEqual(full_report_clips(report), clips)

    def test_audio_fingerprint_changes_with_actual_date_and_result(self):
        first = build_full_report('10.01.1982', '2026-10-22')
        second = build_full_report('02.03.1990', '2026-10-22')
        for key in ['summary', 'personal', 'square', 'lines', 'planets', 'fractal', 'tasks']:
            one = next(c for c in first['narration'] if c['id'] == 'full-report-' + key)
            two = next(c for c in second['narration'] if c['id'] == 'full-report-' + key)
            self.assertNotEqual(one['hash'], two['hash'])
        # Numeric zero has a spoken sentence and mathematical symbols are expanded.
        clip_square = next(c for c in first['narration'] if c['id'] == 'full-report-square')
        self.assertIn('Количество в вашем расчёте: 0.', clip_square['text'])
        self.assertNotIn('Как получены результаты.', clip_square['text'])
        self.assertNotIn('×', clip_square['text'])

    def test_spoken_dates_have_russian_months_and_ordinal_years(self):
        dates = {
            '10.01.1982': 'десятое января тысяча девятьсот восемьдесят второго года',
            '2026-10-22': 'двадцать второе октября две тысячи двадцать шестого года',
            '23.11.2000': 'двадцать третье ноября двухтысячного года',
            '29.02.2000': 'двадцать девятое февраля двухтысячного года',
            '01.01.1900': 'первое января тысяча девятисотого года',
            '31.12.1999': 'тридцать первое декабря тысяча девятьсот девяносто девятого года',
        }
        for value, expected in dates.items():
            self.assertEqual(_speech_date(value), expected)
        report = build_full_report('10.01.1982', '2026-10-22')
        audio = report['narration'][0]['text']
        self.assertNotIn('10.01.1982', audio)
        self.assertNotIn('2026-10-22', audio)
        self.assertIn(dates['10.01.1982'], audio)
        self.assertIn(dates['2026-10-22'], audio)

    def test_summary_states_shared_themes_once_and_preserves_their_positions(self):
        cases = [
            ('10.01.1982', 'Числа души и ума совпали: 1.', 'инициатива, самовыражение и самостоятельность'),
            ('01.01.2006', 'Числа души, ума и судьбы совпали: 1.', 'инициатива, самовыражение и самостоятельность'),
            ('02.03.1995', 'Числа души и судьбы совпали: 2.', 'чуткость, забота и взаимодействие'),
            ('02.03.1996', 'Числа ума и судьбы совпали: 3.', 'обучение, кругозор и обмен знаниями'),
            ('11.11.1982', 'Числа души и ума совпали: 11.', 'интуиция, вдохновение и чувствительность'),
        ]
        for birth, positions, theme in cases:
            with self.subTest(birth=birth):
                report = build_full_report(birth, '2026-10-22')
                summary = ' '.join(report['summary'])
                self.assertIn(positions, summary)
                self.assertEqual(summary.count(theme), 1)
                self.assertNotIn(theme, report['narration'][0]['text'])  # Explain terms in their chapters first.
        distinct = build_full_report('02.03.1990', '2026-10-22')['summary'][0]
        for part in ['Число души — 2:', 'Число ума — 3:', 'Число судьбы — 6:']:
            self.assertIn(part, distinct)
        self.assertNotIn('совпали', distinct)

    def test_fractal_is_spoken_digit_by_digit_but_visual_code_is_unchanged(self):
        for case in FIXTURE['cases']:
            with self.subTest(birth=case['birth_date']):
                report = build_full_report(case['birth_date'], case['as_of_date'])
                code = report['raw']['fractal']['fractal']
                words = ('ноль', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять')
                spoken = ', '.join(words[int(d)] for d in code)
                self.assertIn('Фрактал: ' + code, ' '.join(report['summary']))
                visual = next(s for s in report['sections'] if s['id'] == 'fractal')
                self.assertEqual(visual['title'], 'Фрактал поведения · ' + code)
                for key, prefix in [('fractal', 'Фрактал поведения · ')]:
                    audio = next(c for c in report['narration'] if c['id'] == 'full-report-' + key)
                    self.assertIn(prefix + spoken, audio['text'])
                    self.assertNotIn(prefix + code, audio['text'])

    def test_square_position_codes_are_spoken_separately_without_changing_real_numbers(self):
        report = build_full_report('10.01.1982', '2026-10-22')
        clips = {c['id']: c for c in report['narration']}
        for key in ['full-report-square', 'full-report-vedic-yantra']:
            self.assertIn('один, четыре, семь', clips[key]['text'])
            self.assertIn('два, пять, восемь', clips[key]['text'])
            self.assertIn('три, шесть, девять', clips[key]['text'])
        self.assertIn('Горизонталь один, четыре, семь', clips['full-report-lines']['text'])
        # DDMM is an integer in a multiplication, and 22 is a master number.
        self.assertNotIn('1001 умножить на 1982 равно 1983982', clips['full-report-planets']['text'])
        self.assertIn('Правящее число: 22.', clips['full-report-personal']['text'])


if __name__ == '__main__':
    unittest.main()
