import copy
import sys
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from domain.full_report import build_full_report
from domain.full_report_profile import snapshot_profile
from domain.report_positions import position_targets
from domain.consultation import section_parts
from services.report_insights import _sentence, _accept_part, compose, generation_parts, _resume_positions
from services.report_files import write_json
from services.position_readings import parts, validate, unique, retry_part, collect
from test_report_insights import result_for


class PositionReadings(unittest.TestCase):
    def test_ordinary_russian_words_are_not_calculated_numbers(self):
        for text in ('Важное легче отделять от второстепенного, когда понятно назначение работы.',
                     'Одни и те же действия могут давать разный результат в зависимости от обстановки.',
                     'Если замечаете склонность бросать начатое при первых признаках скуки, это повод уточнить интерес.'):
            self.assertEqual(_sentence(text),text)
        for text in ('Второй этап вашей жизни определяет успех.', 'Число души два определяет способности.'):
            with self.assertRaises(ValueError): _sentence(text)

    def setUp(self):
        self.report = build_full_report('10.01.1982', '2026-11-08', snapshot_profile({'name': 'Dmitrii', 'surname': 'Malahov'}))
        self.targets = position_targets(self.report)
        self.by_ref = {item['ref']: item for item in self.targets}

    def test_same_digit_keeps_different_personal_name_and_calendar_contexts(self):
        soul, mind = self.by_ref['personal:0'], self.by_ref['personal:1']
        self.assertEqual(soul['value'], mind['value'])
        self.assertNotEqual(soul['context']['definition'], mind['context']['definition'])
        self.assertIn('personal:1', soul['same_value_positions'])
        names = [t for t in self.targets if t['section_id'] == 'profile-name']
        self.assertTrue(names)
        self.assertTrue(all(t['context']['area'] == 'name' for t in names))
        self.assertIn('самовыражение', names[0]['context']['action_scope'])
        self.assertFalse(any(t['section_id'] == 'cycles' for t in self.targets))
        self.assertEqual(len([t for t in self.targets if t['section_id'] == 'profile-abracadabra']), 45)

    def test_counts_never_become_planet_digits_and_no_missing_name_is_invented(self):
        for target in self.targets:
            if target['section_id'] == 'square':
                self.assertEqual(target['context']['value_kind'], 'count')
                self.assertFalse(any(ref.startswith('personal:') for ref in target['same_value_positions']))
        basic = position_targets(build_full_report('10.01.1982', '2026-11-08'))
        self.assertFalse(any(t['context']['area'] == 'name' for t in basic))

    def test_calendar_horizons_and_period_boundaries_are_frozen(self):
        for index, horizon, boundary in [(0, 'year', '2026'), (1, 'month', '11.2026'), (2, 'day', '08.11.2026')]:
            context = self.by_ref[f'individual:{index}']['context']
            self.assertEqual((context['horizon'], context['boundary']), (horizon, boundary))
        for p in self.report['raw']['cycles']['periods']:
            entries = [self.by_ref[f'cycle-period-{p["index"]}:{i}'] for i in range(4)]
            self.assertEqual(len({e['context']['definition'] for e in entries}), 4)
            for entry in entries:
                self.assertIn(f'{p["startAge"]}–{p["endAge"]}', entry['context']['boundary'])
                self.assertIn(str(p['years'][0]['year']), entry['context']['boundary'])

    def test_every_position_is_covered_once_in_bounded_model_batches(self):
        batches = parts(self.report)
        refs = [t['ref'] for batch in batches for t in batch['targets']]
        self.assertEqual(refs, list(self.by_ref))
        self.assertTrue(all(len(b['targets']) <= 4 for b in batches))
        for batch in batches:
            self.assertLess(len(str(batch['material'])), 20000)

    def test_missing_duplicate_foreign_and_wrong_horizon_cannot_be_published(self):
        target = self.by_ref['individual:2']
        entry = {'ref': target['ref'], 'insight': 'В разговоре можно заметить, насколько ясно вы выражаете своё намерение.',
            'attention': 'Спешка иногда мешает услышать, что собеседник действительно хотел сказать.',
            'practice': 'В выбранный день перескажите услышанное и вечером отметьте, стало ли меньше недоразумений.'}
        self.assertEqual(validate([target], [entry], _sentence)[0], entry)
        for invalid in ([], [entry, entry], [{**entry, 'ref': 'personal:0'}],
                        [{**entry, 'practice': 'Посвятите всю жизнь поиску подходящего занятия и сохраняйте верность своему пути.'}],
                        [{**entry, 'insight': 'Число души два означает отсутствие лидерских способностей.'}]):
            with self.assertRaises(ValueError): validate([target], invalid, _sentence)

    def test_copied_sentence_is_rejected_even_with_different_opening(self):
        shared = 'Перед ответом уточните смысл вопроса и перескажите услышанное своими словами.'
        first = {'ref': 'personal:0', 'insight': 'Здесь важна самостоятельность. ' + shared,
            'attention': 'Поспешность иногда усложняет согласование ожиданий.', 'practice': 'Запишите намерение и проверьте результат на опыте.'}
        second = {'ref': 'profile-name:0', 'insight': 'Выражение мысли требует ясности. ' + shared,
            'attention': 'Собеседник может по-своему воспринимать сказанное.', 'practice': 'Спросите, насколько понятным оказалось ваше объяснение.'}
        with self.assertRaisesRegex(ValueError, 'Repeated position'): unique([first, second])

    def test_report_audio_uses_each_contextual_reading_without_arithmetic(self):
        # Base fixture has all teaching chapters; keep this test on that report.
        source = build_full_report('10.01.1982', '2026-11-08')
        result = result_for(source)
        first, second = result['positions'][:2]
        first['insight'] = 'Самостоятельное желание легче заметить, когда вы отделяете свой интерес от чужих ожиданий.'
        second['insight'] = 'При выборе решения полезна ясная собственная позиция, которую можно проверить доводами.'
        before = copy.deepcopy(source)
        output = compose(source, result, 'qwen3.5:9b')
        section = next(s for s in output['sections'] if s['id'] == 'personal')
        speech = '\n'.join(section_parts(section))
        for entry in (first, second): self.assertEqual(speech.count(entry['insight']), 1)
        self.assertLess(speech.index('Число души —'), speech.index('Число души: 1'))
        self.assertNotIn('10 + 1', speech)
        self.assertNotIn('День рождения: 10;', speech)
        self.assertEqual(source, before)
        self.assertEqual(section['values'], before['sections'][0]['values'])
        self.assertEqual(section['steps'], before['sections'][0]['steps'])

    def test_cross_batch_duplicates_are_rejected_before_checkpoint(self):
        batch = next(p for p in generation_parts(self.report) if p['kind'] == 'positions')
        entries = result_for(build_full_report('10.01.1982', '2026-11-08'))['positions'][:4]
        previous = {'sections': [], 'positions': [{**entries[0], 'ref': 'earlier:0'}]}
        with self.assertRaisesRegex(ValueError, 'Repeated position'):
            _accept_part(self.report, batch, {'positions': entries}, previous)

    def test_retry_keeps_valid_positions_and_repairs_only_bad_one(self):
        source = build_full_report('10.01.1982', '2026-11-08')
        batch = parts(source)[0]
        entries = result_for(source)['positions'][:4]
        changed = copy.deepcopy(entries)
        changed[1]['insight'] = 'Число судьбы девять определяет ваши способности.'
        accepted = {}
        with self.assertRaises(ValueError):
            collect(batch, batch, {'positions': changed}, accepted, [], _sentence)
        self.assertEqual(len(accepted), 3)
        pending = retry_part(batch, accepted)
        self.assertEqual([t['ref'] for t in pending['targets']], [entries[1]['ref']])
        self.assertEqual(pending['response_schema']['properties']['positions']['minItems'], 1)
        complete = collect(batch, pending, {'positions': [entries[1]]}, accepted, [], _sentence)
        self.assertEqual(complete['positions'], entries)
        with self.assertRaises(ValueError):
            collect(batch, pending, {'positions': [entries[0]]}, accepted, [], _sentence)

    def test_partial_restart_revalidates_each_position_and_rejects_wrong_identity(self):
        source = build_full_report('10.01.1982', '2026-11-08')
        batch = parts(source)[0]; entries = result_for(source)['positions'][:4]
        broken = copy.deepcopy(entries)
        broken[1]['insight'] = 'Число судьбы два определяет ваши способности.'
        identity = {'key':'test', 'contract_hash':'current'}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'partial.json'
            write_json(path,{**identity,'part':1,'positions':broken})
            accepted = _resume_positions([path],identity,batch,0,{'positions':[]})
            self.assertEqual(set(accepted), {entries[i]['ref'] for i in (0,2,3)})
            self.assertEqual(len(retry_part(batch,accepted)['targets']),1)
            self.assertEqual(_resume_positions([path],{**identity,'contract_hash':'foreign'},batch,0,{}),{})
            self.assertEqual(_resume_positions([path],identity,batch,1,{}),{})

    def test_long_prose_is_shortened_only_at_complete_sentence_boundary(self):
        source=build_full_report('10.01.1982','2026-11-08')
        target=parts(source)[0]['targets'][0]
        entry=result_for(source)['positions'][0]
        first='Спокойное обсуждение помогает отличать собственный интерес от ожиданий окружающих.'
        long=' '.join([first]*6)
        result=validate([target],[{**entry,'attention':long}],_sentence)[0]
        self.assertTrue(result['attention'].endswith('.'))
        self.assertLessEqual(len(result['attention']),320)
        self.assertTrue(long.startswith(result['attention']))
        # Never conceal a forbidden claim by trimming the tail before checking.
        with self.assertRaises(ValueError):
            validate([target],[{**entry,'attention':long+' Число души два гарантирует успех.'}],_sentence)


if __name__ == '__main__': unittest.main()
