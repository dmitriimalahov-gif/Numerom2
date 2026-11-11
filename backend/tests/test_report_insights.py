"""No network or model inference: grounded prose and private artifact contracts."""
import copy
import hashlib
import json
import os
import stat
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from domain.full_report import build_full_report
from services.report_files import MAX_JSON_BYTES, digest, enqueue, folder, read_json, write_json
from services.report_insights import ATTEMPTS, CHECKPOINT_VERSION, ReportInsights, VERSION, compose, evidence, generation_parts, material, schema, validate


def report():
    return build_full_report('10.01.1982', '2026-10-23')


def positions_for(source):
    from domain.report_positions import position_targets
    # Deliberately distinct fixture prose; these tests exercise transport and
    # checkpoint integrity. Actual Russian consultation quality has separate cases.
    result = []
    for target in position_targets(source):
        item = {'ref': target['ref']}
        for field in ('insight', 'attention', 'practice'):
            token = hashlib.sha512((target['ref'] + field).encode()).hexdigest().translate(str.maketrans('0123456789abcdef', 'абвгдежзиклмнопр'))
            item[field] = ' '.join(token[i:i+12] for i in range(0, 120, 12)) + '.'
        horizon = target['context']['horizon']
        item['practice'] += {'year': ' План на год.', 'month': ' План на месяц.', 'day': ' Сегодня вечером.'}.get(horizon, '')
        result.append(item)
    return result


def result_for(source):
    references = list(evidence(source))
    result = {'overview': 'Соотнесите самостоятельность с готовностью услышать обратную связь. Наблюдайте, какие действия помогают воплотить замысел.',
        'strengths': [
            {'text': 'Самостоятельность может поддержать ясное намерение, если вы проверяете свои предположения.', 'sources': ['personal:0']},
            {'text': 'Внимание к собеседнику помогает уточнить собственное решение в спокойном разговоре.', 'sources': ['personal:1']},
            {'text': 'Масштабный замысел полезно соединять с небольшими проверяемыми действиями.', 'sources': ['personal:5']},
            {'text': 'Тяга к порядку может помочь доводить начатое до ясного результата.', 'sources': ['personal:2']},
            {'text': 'Готовность вести за собой полезна, когда вы заранее договариваетесь о ролях.', 'sources': ['personal:3']}],
        'attention': [
            {'text': 'Заметьте, когда настойчивость мешает услышать чужое мнение, и спокойно уточните разногласие.', 'sources': ['personal:0']},
            {'text': 'Обратите внимание, достаточно ли сведений для выбранного решения, и отметьте пробелы.', 'sources': ['personal:1']},
            {'text': 'Соотнесите объём замысла с доступными силами и определите посильное действие.', 'sources': ['personal:5']},
            {'text': 'Отмечайте, когда стремление к порядку превращается в лишнюю строгость к себе.', 'sources': ['personal:2']},
            {'text': 'Замечайте, оставляете ли вы другим место для собственного решения.', 'sources': ['personal:3']}],
        'practices': [
            {'text': 'Запишите намерение и наблюдаемый результат, затем сопоставьте их без оценок.', 'sources': ['personal:0']},
            {'text': 'Обсудите открытый вопрос с собеседником и перескажите услышанное своими словами.', 'sources': ['personal:1']},
            {'text': 'Выберите небольшую часть замысла и заранее определите признак её завершения.', 'sources': ['personal:5']}],
        'sections': [], 'positions': positions_for(source)}
    tags = ['спокойствие', 'терпение', 'порядок', 'внимание', 'согласованность', 'ясность', 'доверие', 'открытость',
            'последовательность', 'участие', 'собранность', 'любознательность', 'бережность', 'чуткость', 'интерес',
            'искренность', 'осознанность', 'аккуратность', 'понимание', 'уверенность']
    for section, tag in zip(source['sections'], tags):
        result['sections'].append({'id': section['id'],
            'insight': f'Проверьте, как выбранный подход помогает сохранять {tag} в повседневных делах.',
            'practice': f'Запишите наблюдение о том, что помогло сохранить {tag}, и обсудите его с близким человеком.',
            'sources': [next(ref for ref in references if ref.startswith(section['id'] + ':'))]})
    return result


class InterpretationContract(unittest.TestCase):
    def setUp(self):
        self.report = report()
        self.result = result_for(self.report)

    def test_math_raw_methods_steps_values_and_charts_are_immutable(self):
        before = copy.deepcopy(self.report)
        result_before = copy.deepcopy(self.result)
        composed = compose(self.report, self.result, 'qwen3.5:9b')
        self.assertEqual(self.report, before)
        self.assertEqual(self.result, result_before)
        self.assertEqual(composed['raw'], before['raw'])
        self.assertEqual(composed['excluded'], before['excluded'])
        self.assertEqual(len(composed['sections']), len(before['sections']) + 1)
        for old, new in zip(before['sections'], composed['sections'][1:]):
            for key in ['id', 'title', 'values', 'steps', 'method', 'chart']:
                self.assertEqual(old.get(key), new.get(key), (old['id'], key))
            self.assertIn('Основание в расчёте:', new['paragraphs'][1])
        self.assertEqual(composed['interpretation']['version'], VERSION)
        self.assertEqual(len(composed['narration']), 18)
        self.assertTrue(all(item['id'].startswith('full-report-') for item in composed['narration']))

    def test_source_names_and_values_are_attached_by_server(self):
        composed = compose(self.report, self.result, 'qwen3.5:9b')
        self.assertIn('Число жизненного пути: 22', composed['sections'][0]['values'][2]['meaning'])
        self.assertIn('Личные числа и их сочетание', composed['sections'][0]['values'][2]['meaning'])
        self.assertIn('Число души: 1', composed['sections'][1]['paragraphs'][1])

    def test_unknown_duplicate_and_foreign_section_references_are_rejected(self):
        for refs in [['missing:1'], ['personal:0', 'personal:0'], ['square:0'], ['personal:0', 'square:0'], [None], []]:
            changed = copy.deepcopy(self.result)
            changed['sections'][0]['sources'] = refs
            with self.subTest(refs=refs), self.assertRaises(ValueError):
                validate(self.report, changed)

    def test_synthesis_basis_names_each_section_once(self):
        self.result['strengths'][0]['sources'] = ['personal:0', 'personal:1', 'square:0']
        basis = compose(self.report, self.result, 'qwen3.5:9b')['highlights'][0]['items'][0]['basis']
        self.assertEqual(basis.count('Личные числа и их сочетание'), 1)
        self.assertIn('Число души: 1, Число ума: 1; ', basis)

    def test_potentials_and_attention_are_spoken_after_explaining_calculations(self):
        composed = compose(self.report, self.result, 'qwen3.5:9b')
        potentials, attention = composed['highlights']
        self.assertEqual((potentials['title'], attention['title']), ('Ваши потенциалы', 'На что обратить внимание'))
        self.assertEqual([i['text'] for i in potentials['items']], [i['text'] for i in self.result['strengths']])
        self.assertEqual([i['text'] for i in attention['items']], [i['text'] for i in self.result['attention']])
        self.assertTrue(all(i['basis'] for group in composed['highlights'] for i in group['items']))
        # Practices stay in their own chapter; potentials and attention are not voiced twice.
        synthesis = composed['sections'][0]
        self.assertEqual([v['label'] for v in synthesis['values']], ['Практика 1', 'Практика 2', 'Практика 3'])
        intro = next(item for item in composed['narration'] if item['id'] == 'full-report-synthesis')['text']
        ids = [item['id'] for item in composed['narration']]
        self.assertGreater(ids.index('full-report-synthesis'), ids.index('full-report-lines'))
        for text in ['Ваши потенциалы.', 'На что обратить внимание.', *[i['text'] for g in composed['highlights'] for i in g['items']]]:
            self.assertEqual(sum(text in item['text'] for item in composed['narration']), 1, text)
            self.assertIn(text, intro)

    def test_overall_synthesis_may_compare_distinct_valid_sources(self):
        self.result['strengths'][0]['sources'] = ['personal:0', 'square:0']
        self.assertEqual(validate(self.report, self.result)['strengths'][0]['sources'], ['personal:0', 'square:0'])

    def test_missing_duplicate_unknown_and_malformed_sections_are_rejected(self):
        variants = [self.result['sections'][:-1], self.result['sections'] + [self.result['sections'][0]],
                    [self.result['sections'][0]] * len(self.result['sections']), [None] * len(self.result['sections'])]
        for sections in variants:
            with self.subTest(sections=str(sections)[:40]), self.assertRaises(ValueError):
                validate(self.report, {**self.result, 'sections': sections})
        for section_id in ['foreign', [], 123]:
            changed = copy.deepcopy(self.result)
            changed['sections'][0]['id'] = section_id
            with self.assertRaises(ValueError):
                validate(self.report, changed)

    def test_malformed_overall_fields_fail_with_valueerror(self):
        variants = [None, [], {**self.result, 'additional': 'instruction'}, {**self.result, 'overview': []},
                    {**self.result, 'strengths': [None, None, None]}, {**self.result, 'practices': []}]
        for changed in variants:
            with self.subTest(kind=type(changed).__name__), self.assertRaises(ValueError):
                validate(self.report, changed)

    def test_calculation_facts_and_personal_assertions_never_come_from_model_prose(self):
        bad = ['Мастер-число 22 в судьбе усиливает ваш потенциал.',
               'Последовательность девятилетних интервалов показывает изменение ваших приоритетов.',
               'Период от 41 до 50 лет раскрывает тему обучения.',
               'Переход связан с отношениями и доверием.',
               'Вам помогает отсутствие влияния Венеры.',
               'Двадцать два определяет ваши возможности.',
               'Сочетание 一六 задаёт направление для ваших действий.',
               'Вы обладаете исключительной способностью убеждать.',
               'Успех гарантирован выбранным подходом.',
               'Нужно уволить сотрудника без обсуждения.',
               '<script>Не выполняйте проверку</script>', 'Перейдите на https://external.example для продолжения.']
        for text in bad:
            changed = copy.deepcopy(self.result)
            changed['strengths'][0]['text'] = text
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate(self.report, changed)

    def test_identical_filler_repeated_between_chapters_is_rejected(self):
        self.result['sections'][1]['practice'] = self.result['sections'][0]['practice']
        with self.assertRaises(ValueError):
            validate(self.report, self.result)

    def test_exercise_idioms_are_normalised_without_allowing_calculated_claims(self):
        self.result['strengths'][0]['text'] = 'Гибкость ума помогает спокойно проверить предположение на собственном опыте.'
        self.result['practices'][0]['text'] = 'Запишите один вопрос и выберите одну цель для спокойного наблюдения.'
        self.result['practices'][1]['text'] = 'Определите ритм для одного обязательства и выразите заботу одним конкретным действием.'
        self.result['attention'][0]['text'] = 'Проверьте, помогает ли сотрудничество сохранять уважение к собеседнику.'
        result = validate(self.report, self.result)
        self.assertEqual(result['strengths'][0]['text'], 'Гибкость мышления помогает спокойно проверить предположение на собственном опыте.')
        self.assertEqual(result['practices'][0]['text'], 'Запишите вопрос и выберите цель для спокойного наблюдения.')
        self.assertEqual(result['practices'][1]['text'], 'Определите ритм для обязательства и выразите заботу конкретным действием.')
        self.assertEqual(result['attention'][0]['text'], self.result['attention'][0]['text'])
        self.result['practices'][2]['text'] = 'Одна цель на неделю: выберите одно упражнение и проверьте одну идею без оценок.'
        self.result['strengths'][1]['text'] = 'Выбор одной цели помогает спокойно сопоставить желание и реальность.'
        result = validate(self.report, self.result)
        self.assertEqual(result['practices'][2]['text'], 'Цель на неделю: выберите упражнение и проверьте идею без оценок.')
        self.assertEqual(result['strengths'][1]['text'], 'Выбор цели помогает спокойно сопоставить желание и реальность.')
        self.result['practices'][2]['text'] = 'Запишите один опыт, требующий осмысления, и начните с первый шаг без спешки.'
        self.assertEqual(validate(self.report, self.result)['practices'][2]['text'],
            'Запишите опыт, требующий осмысления, и начните с начальный шаг без спешки.')
        self.result['practices'][2]['text'] = 'Выберите один из дней недели и одну из привычек, затем проверьте их на опыте.'
        self.assertEqual(validate(self.report, self.result)['practices'][2]['text'],
            'Выберите любой из дней недели и любую из привычек, затем проверьте их на опыте.')
        for text in ('Выберите один из периодов и проверьте его на опыте.',
                     'Забота глубже, когда в ней есть место обоим, а не только одному.',
                     'Ваше число один помогает спокойно проверять решения.'):
            changed = copy.deepcopy(self.result)
            changed['practices'][2]['text'] = text
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate(self.report, changed)
        self.result['strengths'][0]['text'] = 'Гибкость ума связана с числом судьбы двадцать два.'
        with self.assertRaises(ValueError):
            validate(self.report, self.result)

    def test_only_specific_everyday_temporal_expressions_are_normalised(self):
        cases = [
            ('В периоде перемен полезно спокойно уточнять ожидания в разговоре.',
             'Во время перемен полезно спокойно уточнять ожидания в разговоре.'),
            ('В периоды нагрузки проверяйте, помогает ли отдых сохранять внимание.',
             'При нагрузке проверяйте, помогает ли отдых сохранять внимание.'),
            ('Выделите период отдыха и отметьте, что помогает восстановить внимание.',
             'Выделите время для отдыха и отметьте, что помогает восстановить внимание.'),
            ('Составьте цикл наблюдения и отмечайте, что помогает сосредоточиться.',
             'Составьте порядок наблюдения и отмечайте, что помогает сосредоточиться.'),
            ('Обсудите цикл обратной связи с собеседником и запишите открытые вопросы.',
             'Обсудите обмен обратной связью с собеседником и запишите открытые вопросы.'),
            ('Переход от размышления к действию полезно проверить на небольшом замысле.',
             'Движение от размышления к действию полезно проверить на небольшом замысле.')]
        for text, expected in cases:
            with self.subTest(text=text):
                changed = copy.deepcopy(self.result)
                changed['sections'][8]['insight'] = text
                self.assertEqual(validate(self.report, changed)['sections'][8]['insight'], expected)

    def test_temporal_normalisation_does_not_hide_calculated_or_personal_claims(self):
        cases = ['В этом периоде вас ожидает раскрытие важных талантов.',
                 'В периоде перемен вас ждёт раскрытие важных талантов.',
                 'В периоде перемен вас ждёт успех, поэтому полезно подготовиться.',
                 'В периоде перемен раскрываются ваши особенные таланты.',
                 'В текущем цикле усиливается влияние отношений.',
                 'Переход связан с отношениями и доверием.',
                 'Рассчитанный цикл наблюдения определяет ваш характер.',
                 'Ваш нумерологический цикл обратной связи связан с самостоятельностью.',
                 'В периоде перемен число судьбы раскрывает ваши способности.',
                 'В периоде перемен вам исполнится 35 лет.',
                 'В периоде перемен вы обладаете исключительной способностью убеждать.',
                 'Переход от размышления к действию гарантирует успех.']
        for text in cases:
            with self.subTest(text=text), self.assertRaises(ValueError):
                changed = copy.deepcopy(self.result)
                changed['sections'][8]['insight'] = text
                validate(self.report, changed)

    def test_source_report_rejects_duplicate_or_already_interpreted_sections(self):
        changed = copy.deepcopy(self.report)
        changed['sections'][1]['id'] = changed['sections'][0]['id']
        with self.assertRaises(ValueError):
            evidence(changed)
        with self.assertRaises(ValueError):
            evidence(compose(self.report, self.result, 'qwen3.5:9b'))

    def test_schema_contains_only_actual_evidence_ids(self):
        contract = schema(self.report)
        actual = contract['$defs']['evidenceReference']['enum']
        self.assertEqual(actual, list(evidence(self.report)))
        for field in ('strengths', 'attention', 'practices', 'sections'):
            pointer = contract['properties'][field]['items']['properties']['sources']['items']
            self.assertEqual(pointer, {'$ref': '#/$defs/evidenceReference'})
        self.assertEqual(json.dumps(contract).count('"enum": ["personal:0"'), 1)
        self.assertFalse(contract['additionalProperties'])

    def test_synthesis_schema_constrains_sources_to_one_shared_actual_ref_enum(self):
        for with_profile in (False, True):
            source = copy.deepcopy(self.report)
            if with_profile:
                source['profile_snapshot'] = {'version': 1}
            with self.subTest(with_profile=with_profile):
                part = generation_parts(source)[0]
                contract = part['response_schema']
                self.assertEqual(contract['$defs']['evidenceReference']['enum'], list(evidence(source)))
                self.assertEqual(json.dumps(contract).count('"enum": ["personal:0"'), 1)
                for key in ('strengths', 'attention', 'practices'):
                    sources = contract['properties'][key]['items']['properties']['sources']
                    self.assertEqual(sources['items'], {'$ref': '#/$defs/evidenceReference'})
                    self.assertTrue(sources['uniqueItems'])
                self.assertNotIn('m0', contract['$defs']['evidenceReference']['enum'])

    def test_chapter_schema_admits_only_each_sections_own_refs(self):
        refs = list(evidence(self.report))
        covered = []
        for part in (p for p in generation_parts(self.report) if p['kind'] == 'chapters'):
            rule = part['response_schema']['properties']['sections']
            alternatives = rule['items']['anyOf']
            ids = [s['id'] for s in part['report']['sections']]
            self.assertEqual(rule['minItems'], len(ids))
            self.assertEqual([a['properties']['id']['enum'] for a in alternatives], [[i] for i in ids])
            for section_id, alternative in zip(ids, alternatives):
                own = alternative['properties']['sources']['items']['enum']
                self.assertTrue(own)
                self.assertTrue(all(ref.startswith(section_id + ':') for ref in own))
                self.assertEqual(alternative['properties']['insight']['maxLength'], 220)
                self.assertEqual(alternative['properties']['practice']['maxLength'], 180)
                self.assertFalse(alternative['additionalProperties'])
                covered += own
        self.assertEqual(covered, refs)

    def test_prompt_dictionary_is_lossless_for_every_result_and_full_long_meanings(self):
        source = copy.deepcopy(self.report)
        long_meaning = '  Полная трактовка без сокращений.\n' * 60
        source['sections'][0]['values'][0]['meaning'] = long_meaning
        source['sections'][1]['values'][0]['meaning'] = long_meaning
        before = copy.deepcopy(source)
        packed = json.loads(json.dumps(material(source), ensure_ascii=False))
        self.assertEqual(source, before)
        self.assertEqual(packed['birth_date'], source['birth_date'])
        self.assertEqual(packed['as_of_date'], source['as_of_date'])
        self.assertEqual(len(packed['sections']), len(source['sections']))
        actual_refs = []
        for original, compact in zip(source['sections'], packed['sections']):
            self.assertEqual(compact['id'], original['id'])
            self.assertEqual(compact['title'], original['title'])
            self.assertEqual(compact['knowledge'], original['paragraphs'])
            self.assertEqual(len(compact['values']), len(original['values']))
            for index, (value, entry) in enumerate(zip(original['values'], compact['values'])):
                self.assertEqual(entry['ref'], f'{original["id"]}:{index}')
                self.assertEqual(entry['label'], value['label'])
                self.assertEqual(entry['value'], value['value'])
                self.assertEqual(packed['meanings'][entry['meaning_ref']], value.get('meaning', ''))
                actual_refs.append(entry['ref'])
        self.assertEqual(actual_refs, list(evidence(source)))
        self.assertEqual(list(packed['meanings'].values()).count(long_meaning), 1)
        self.assertEqual(packed['sections'][0]['values'][0]['meaning_ref'],
                         packed['sections'][1]['values'][0]['meaning_ref'])
        self.assertEqual(material(source), material(source))

    def test_prompt_dictionary_reduces_real_material_without_losing_refs(self):
        packed = material(self.report)
        expanded = {'birth_date': packed['birth_date'], 'as_of_date': packed['as_of_date'],
            'sections': [{**s, 'values': [{**{k: v for k, v in entry.items() if k != 'meaning_ref'},
                'meaning': packed['meanings'][entry['meaning_ref']]} for entry in s['values']]}
                for s in packed['sections']]}
        compact_size = len(json.dumps(packed, ensure_ascii=False, separators=(',', ':')))
        expanded_size = len(json.dumps(expanded, ensure_ascii=False, separators=(',', ':')))
        # Four life periods (the author's table) repeat fewer meanings than the old nine, so ~17% is saved.
        self.assertLess(compact_size, expanded_size * 0.85)
        self.assertEqual(sum(len(s['values']) for s in packed['sections']), len(evidence(self.report)))


class InterpretationCache(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.report = report()
        self.key = digest(VERSION, self.report)
        self.service = ReportInsights(self.root)

    def test_digest_is_order_independent_but_version_and_values_change_identity(self):
        self.assertEqual(digest('v', {'a': 1, 'b': 2}), digest('v', {'b': 2, 'a': 1}))
        self.assertNotEqual(self.key, digest('numerom-insights-v1', self.report))
        changed = copy.deepcopy(self.report)
        changed['raw']['personal']['soul'] = 9
        self.assertNotEqual(self.key, digest(VERSION, changed))

    def test_enrich_coalesces_job_and_validated_cache_is_reused(self):
        original, status = self.service.enrich(self.report)
        self.assertIs(original, self.report)
        self.assertEqual(status, 'preparing')
        target = folder(self.root, self.key)
        job = read_json(target / 'job.json')
        self.service.enrich(self.report)
        self.assertEqual(read_json(target / 'job.json'), job)
        write_json(target / 'ready.json', {'key': self.key, 'provider': 'ollama', 'model': 'qwen3.5:9b', 'result': result_for(self.report)})
        with patch('services.report_insights.enqueue', side_effect=AssertionError('cache must not enqueue')):
            output, status = self.service.enrich(self.report)
        self.assertEqual(status, 'ready')
        self.assertEqual(output['raw'], self.report['raw'])

    def test_corrupt_mismatched_and_unvalidated_cache_cannot_be_ready(self):
        target = folder(self.root, self.key)
        for content in [[], {'key': 'b' * 64}, {'key': self.key, 'model': 'qwen3.5:9b', 'result': result_for(self.report)},
                        {'key': self.key, 'provider': 'ollama', 'model': 'qwen3.5:9b', 'result': {'wrong': 'shape'}}]:
            write_json(target / 'ready.json', content)
            self.assertEqual(self.service.enrich(self.report)[1], 'preparing')

    def test_enrich_preserves_backoff_and_explicit_retry_clears_failure(self):
        self.service.enrich(self.report)
        target = folder(self.root, self.key)
        failure = {'attempts': 3, 'retry_at': 9999999999, 'error': 'invalid model prose'}
        write_json(target / 'failed.json', failure)
        self.assertEqual(self.service.enrich(self.report)[1], 'preparing')
        self.assertEqual(read_json(target / 'failed.json'), failure)
        self.assertEqual(self.service.retry(self.report)[1], 'preparing')
        self.assertFalse((target / 'failed.json').exists())


class PrivateArtifacts(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_bounded_queue_is_atomic_and_same_key_can_retry_at_capacity(self):
        keys = [digest('queue', i) for i in range(12)]
        def add(key):
            try:
                enqueue(self.root, key, {'key': key}, limit=3)
                return key
            except RuntimeError:
                return None
        with ThreadPoolExecutor(max_workers=12) as pool:
            accepted = [key for key in pool.map(add, keys) if key]
        self.assertEqual(len(accepted), 3)
        self.assertEqual(len(list(self.root.glob('*/job.json'))), 3)
        self.assertEqual(enqueue(self.root, accepted[0], {'key': accepted[0]}, limit=3).name, accepted[0])

    def test_atomic_private_writes_repair_corruption_and_reject_oversized_json(self):
        key = digest('queue', 'x')
        target = folder(self.root, key)
        target.mkdir()
        (target / 'job.json').write_text('{broken')
        enqueue(self.root, key, {'key': key}, limit=1)
        self.assertEqual(read_json(target / 'job.json'), {'key': key})
        self.assertEqual(stat.S_IMODE((target / 'job.json').stat().st_mode), 0o600)
        with self.assertRaises(ValueError):
            write_json(target / 'ready.json', {'large': 'x' * MAX_JSON_BYTES})
        self.assertFalse((target / 'ready.json').exists())
        self.assertEqual(list(target.glob('.writing-*')), [])

    def test_reads_ignore_arrays_nonfinite_missing_and_symlink_files(self):
        target = self.root / 'data.json'
        for data in ['[]', 'null', '{"value":NaN}', '{broken']:
            target.write_text(data)
            self.assertIsNone(read_json(target))
        target.unlink()
        other = self.root / 'actual.json'
        other.write_text('{"private":true}')
        target.symlink_to(other)
        self.assertIsNone(read_json(target))
        self.assertIsNone(read_json(self.root / 'missing.json'))
        self.assertIsNone(read_json(self.root))
        fifo = self.root / 'fifo'
        os.mkfifo(fifo)
        self.assertIsNone(read_json(fifo))

    def test_paths_reject_traversal_and_symlink_artifact_directory(self):
        for key in ['../outside', 'A' * 64, 'f' * 63]:
            with self.assertRaises(ValueError):
                folder(self.root, key)
        actual = self.root / 'actual'
        actual.mkdir()
        (self.root / ('a' * 64)).symlink_to(actual)
        with self.assertRaises(ValueError):
            folder(self.root, 'a' * 64)


class LocalGeneration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.service_count = 0

    def new_service(self):
        self.service_count += 1
        return ReportInsights(self.root / str(self.service_count))

    def inference_client(self, source, corrupt=None):
        full = result_for(source)
        seen = []
        async def post(url, **kwargs):
            request = kwargs['json']
            body = json.loads(request['messages'][1]['content'])
            seen.append(request)
            if 'overview' in body['response_schema']['properties']:
                fragment = {k: v for k, v in full.items() if k not in ('sections', 'positions')}
            elif 'positions' in body['response_schema']['properties']:
                refs = {p['ref'] for p in body['material']['positions']}
                fragment = {'positions': [p for p in full['positions'] if p['ref'] in refs]}
            else:
                ids = {s['id'] for s in body['material']['sections']}
                fragment = {'sections': [s for s in full['sections'] if s['id'] in ids]}
            payload = {'done': True, 'done_reason': 'stop', 'prompt_eval_count': 1234, 'eval_count': 567,
                'message': {'content': json.dumps(fragment, ensure_ascii=False)}}
            if corrupt:
                payload = corrupt(len(seen), payload)
            return httpx.Response(200, json=payload, request=httpx.Request('POST', url))
        return SimpleNamespace(post=AsyncMock(side_effect=post)), seen

    async def test_inference_stays_local_and_new_invocations_have_auditable_fresh_seeds(self):
        source = report()
        client, seen = self.inference_client(source)
        context = AsyncMock()
        context.__aenter__.return_value = client
        with patch('services.report_insights.httpx.AsyncClient', return_value=context) as constructor, \
                patch('services.report_insights.secrets.randbits', side_effect=[1234, 5678]) as seed:
            first = await self.new_service().generate(source)
            second = await self.new_service().generate(source)
        self.assertFalse(constructor.call_args.kwargs['trust_env'])
        self.assertEqual(first['key'], second['key'])
        self.assertEqual(first['prompt_eval_count'], 1234 * len(generation_parts(source)))
        self.assertEqual(first['eval_count'], 567 * len(generation_parts(source)))
        self.assertEqual(first['done_reason'], 'stop')
        self.assertEqual(first['result'], result_for(source))
        self.assertEqual(len(first['calls']), len(generation_parts(source)))
        requests = client.post.call_args_list
        self.assertEqual(len(requests), 2 * len(generation_parts(source)))
        self.assertEqual(requests[0].args[0], 'http://127.0.0.1:11434/api/chat')
        self.assertEqual(first['base_seed'], 1234)
        self.assertEqual(second['base_seed'], 5678)
        self.assertEqual(seed.call_count, 2)
        self.assertEqual([r['options']['seed'] for r in seen[:len(generation_parts(source))]], list(range(1234, 1234 + len(generation_parts(source)))))
        self.assertEqual([r['options']['seed'] for r in seen[len(generation_parts(source)): ]], list(range(5678, 5678 + len(generation_parts(source)))))
        self.assertEqual([c['seed'] for c in first['calls']], list(range(1234, 1234 + len(generation_parts(source)))))
        self.assertIn('НИГДЕ В ТЕКСТЕ', requests[0].kwargs['json']['messages'][0]['content'])
        self.assertFalse(requests[0].kwargs['json']['stream'])
        self.assertEqual(requests[0].kwargs['json']['keep_alive'], 0)
        self.assertEqual(requests[0].kwargs['json']['options']['num_ctx'], 16384)
        self.assertEqual(json.loads(requests[0].kwargs['json']['messages'][1]['content'])['material'], material(source))
        self.assertEqual(seen[0]['format'], json.loads(seen[0]['messages'][1]['content'])['response_schema'])
        self.assertEqual(seen[0]['format']['$defs']['evidenceReference']['enum'], list(evidence(source)))

    async def test_bounded_parts_preserve_every_calculation_and_reassemble_full_report(self):
        source = report()
        before = copy.deepcopy(source)
        client, requests = self.inference_client(source)
        context = AsyncMock()
        context.__aenter__.return_value = client
        with patch('services.report_insights.httpx.AsyncClient', return_value=context):
            generated = await self.new_service().generate(source)
        self.assertEqual(source, before)
        self.assertEqual(len(requests), len(generation_parts(source)))
        supplied, identifiers = {}, []
        for request in requests[1:4]:
            self.assertLessEqual(request['options']['num_predict'], 2500)
            body = json.loads(request['messages'][1]['content'])
            self.assertEqual(request['format'], body['response_schema'])
            self.assertLessEqual(len(body['material']['sections']), 5)
            self.assertNotIn('$defs', body['response_schema'])
            self.assertEqual(body['response_schema']['required'], ['sections'])
            for section in body['material']['sections']:
                identifiers.append(section['id'])
                for value in section['values']:
                    supplied[value['ref']] = {'label': value['label'], 'value': value['value'],
                        'meaning': value['meaning']}
        expected = {ref: {key: value.get(key, '') for key in ('label', 'value', 'meaning')}
            for ref, value in evidence(source).items()}
        self.assertEqual(supplied, expected)
        self.assertEqual(identifiers, [s['id'] for s in source['sections']])
        composed = compose(source, generated['result'], generated['model'])
        self.assertEqual(composed['raw'], source['raw'])
        self.assertEqual(len(composed['sections']), 16)
        self.assertEqual(len(composed['narration']), 18)

    async def test_invalid_part_is_repaired_with_original_evidence_and_changed_seed(self):
        source = report()
        def truncated(index, payload):
            return {**payload, 'done_reason': 'length'} if index == 2 else payload
        def foreign(index, payload):
            if index == 2:
                fragment = json.loads(payload['message']['content'])
                fragment['sections'][0]['sources'] = ['square:0']
                payload['message']['content'] = json.dumps(fragment)
            return payload
        for corrupt in (truncated, foreign):
            client, requests = self.inference_client(source, corrupt)
            context = AsyncMock()
            context.__aenter__.return_value = client
            with self.subTest(case=corrupt.__name__), patch('services.report_insights.httpx.AsyncClient', return_value=context):
                generated = await self.new_service().generate(source)
            self.assertEqual(len(requests), len(generation_parts(source)) + 1)
            initial, repaired = [json.loads(r['messages'][1]['content']) for r in requests[1:3]]
            self.assertEqual(initial['material'], repaired['material'])
            self.assertEqual(initial['response_schema'], repaired['response_schema'])
            self.assertNotIn('repair', initial)
            self.assertTrue(repaired['repair']['validation_error'])
            self.assertNotEqual(requests[1]['options']['seed'], requests[2]['options']['seed'])
            self.assertEqual(generated['result'], result_for(source))
            self.assertFalse(generated['calls'][1]['accepted'])
            self.assertTrue(generated['calls'][2]['accepted'])
            self.assertEqual(generated['calls'][2]['attempt'], 2)
            self.assertEqual(generated['eval_count'], 567 * (len(generation_parts(source)) + 1))

    async def test_synthesis_reference_failure_is_precise_and_repaired_without_remapping(self):
        source = report()
        for refs, reason in ((['m0'], 'Unknown calculation reference'),
                             (['personal:999'], 'Unknown calculation reference'),
                             (['personal:0', 'personal:0'], 'Repeated calculation reference')):
            def invalid_ref(index, payload):
                if index == 1:
                    fragment = json.loads(payload['message']['content'])
                    fragment['strengths'][1]['sources'] = refs
                    payload['message']['content'] = json.dumps(fragment)
                return payload
            client, requests = self.inference_client(source, invalid_ref)
            context = AsyncMock()
            context.__aenter__.return_value = client
            with self.subTest(refs=refs), patch('services.report_insights.httpx.AsyncClient', return_value=context):
                generated = await self.new_service().generate(source)
            self.assertEqual(len(requests), len(generation_parts(source)) + 1)
            initial, repaired = [json.loads(r['messages'][1]['content']) for r in requests[:2]]
            self.assertEqual(initial['material'], repaired['material'])
            self.assertEqual(requests[0]['format'], requests[1]['format'])
            self.assertIn('strengths[1].sources: ' + reason, repaired['repair']['validation_error'])
            self.assertEqual(generated['result'], result_for(source))
            self.assertFalse(generated['calls'][0]['accepted'])
            self.assertTrue(generated['calls'][1]['accepted'])

    async def test_synthesis_invalid_ref_is_rejected_even_if_structured_model_ignores_schema(self):
        source = report()
        def unknown_ref(index, payload):
            fragment = json.loads(payload['message']['content'])
            fragment['practices'][2]['sources'] = ['m0']
            payload['message']['content'] = json.dumps(fragment)
            return payload
        client, requests = self.inference_client(source, unknown_ref)
        context = AsyncMock()
        context.__aenter__.return_value = client
        with patch('services.report_insights.httpx.AsyncClient', return_value=context), \
                self.assertRaisesRegex(ValueError, rf'part 1 failed after {ATTEMPTS} attempts: practices\[2\].sources: Unknown calculation reference'):
            await self.new_service().generate(source)
        self.assertEqual(len(requests), ATTEMPTS)

    async def test_late_failure_resumes_only_after_revalidating_accepted_private_parts(self):
        source = report()
        service = self.new_service()
        def late_failure(index, payload):
            if 3 <= index < 3 + ATTEMPTS:
                fragment = json.loads(payload['message']['content'])
                fragment['sections'][0]['insight'] = 'В этом периоде вас ожидает раскрытие важных талантов.'
                payload['message']['content'] = json.dumps(fragment)
            return payload
        client, requests = self.inference_client(source, late_failure)
        context = AsyncMock()
        context.__aenter__.return_value = client
        with patch('services.report_insights.httpx.AsyncClient', return_value=context), \
                self.assertRaisesRegex(ValueError, f'part 3 failed after {ATTEMPTS} attempts'):
            await service.generate(source)
        target = folder(service.root, digest(VERSION, source))
        checkpoint = read_json(target / 'checkpoint.json')
        self.assertEqual(checkpoint['version'], CHECKPOINT_VERSION)
        self.assertEqual(len(checkpoint['parts']), 2)
        self.assertEqual(stat.S_IMODE((target / 'checkpoint.json').stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o700)
        self.assertFalse((target / 'ready.json').exists())
        rejection = read_json(target / 'rejected-latest.json')
        self.assertEqual((rejection['part'], rejection['attempt']), (3, ATTEMPTS))
        self.assertIn('В этом периоде', json.loads(rejection['content'])['sections'][0]['insight'])
        self.assertEqual(stat.S_IMODE((target / 'rejected-latest.json').stat().st_mode), 0o600)

        resumed_client, resumed_requests = self.inference_client(source)
        context.__aenter__.return_value = resumed_client
        with patch('services.report_insights.httpx.AsyncClient', return_value=context):
            generated = await service.generate(source)
        self.assertEqual(len(resumed_requests), len(generation_parts(source)) - 2)
        self.assertEqual(generated['result'], result_for(source))
        self.assertEqual([call.get('cached', False) for call in generated['calls']], [True, True] + [False] * (len(generation_parts(source)) - 2))
        self.assertEqual(generated['eval_count'], 567 * (len(generation_parts(source)) - 2))
        self.assertEqual(len(read_json(target / 'checkpoint.json')['parts']), len(generation_parts(source)))
        self.assertTrue(all('В этом периоде вас ожидает' not in request['messages'][1]['content']
                            for request in requests + resumed_requests))

    async def test_calculated_word_repair_covers_all_bad_fields_and_survives_job_restart(self):
        source = report()
        service = self.new_service()
        invalid_insight = 'Последовательность девятилетних интервалов показывает изменение ваших приоритетов.'
        invalid_practice = 'Запишите периоды перемен и свяжите наблюдения с повседневными привычками.'
        def numerical_words(index, payload):
            if 3 <= index < 3 + ATTEMPTS:
                fragment = json.loads(payload['message']['content'])
                item = next(item for item in fragment['sections'] if item['id'] == 'cycles')
                item['insight'], item['practice'] = invalid_insight, invalid_practice
                payload['message']['content'] = json.dumps(fragment, ensure_ascii=False)
            return payload
        client, requests = self.inference_client(source, numerical_words)
        context = AsyncMock()
        context.__aenter__.return_value = client
        with patch('services.report_insights.httpx.AsyncClient', return_value=context), \
                self.assertRaisesRegex(ValueError, 'cycles.insight:.*девятилетних'):
            await service.generate(source)
        target = folder(service.root, digest(VERSION, source))
        checkpoint = read_json(target / 'checkpoint.json')
        self.assertEqual(len(checkpoint['parts']), 2)
        repair_before_restart = json.loads(requests[3]['messages'][1]['content'])['repair']
        by_field = {item['field']: item for item in repair_before_restart['invalid_prose']}
        self.assertEqual(by_field['cycles.insight']['forbidden_terms'], ['девятилетних'])
        self.assertEqual(by_field['cycles.practice']['forbidden_terms'], ['периоды'])
        self.assertIn('Числовые прилагательные тоже запрещены', repair_before_restart['instruction'])
        self.assertIn('Не пересказывай title, label, value или knowledge', repair_before_restart['instruction'])

        resumed_client, resumed_requests = self.inference_client(source)
        context.__aenter__.return_value = resumed_client
        with patch('services.report_insights.httpx.AsyncClient', return_value=context):
            generated = await service.generate(source)
        self.assertEqual(len(resumed_requests), len(generation_parts(source)) - 2)
        self.assertEqual(generated['result'], result_for(source))
        # The first request after restart receives recomputed diagnostics, not
        # another uncorrected attempt, and accepted parts keep their identity.
        resumed_body = json.loads(resumed_requests[0]['messages'][1]['content'])
        self.assertEqual(resumed_body['repair'], repair_before_restart)
        self.assertEqual(resumed_body['material'], json.loads(requests[2]['messages'][1]['content'])['material'])
        self.assertEqual(checkpoint['contract_hash'], read_json(target / 'checkpoint.json')['contract_hash'])
        self.assertEqual(checkpoint['parts'], read_json(target / 'checkpoint.json')['parts'][:2])
        for request in requests + resumed_requests:
            self.assertNotIn(invalid_insight, request['messages'][1]['content'])
            self.assertNotIn(invalid_practice, request['messages'][1]['content'])

    async def test_saved_repair_is_revalidated_and_not_trusted_from_another_contract(self):
        source = report()
        service = self.new_service()
        def invalid(index, payload):
            fragment = json.loads(payload['message']['content'])
            fragment['strengths'][0]['text'] = 'Последовательность девятилетних интервалов определяет характер.'
            payload['message']['content'] = json.dumps(fragment, ensure_ascii=False)
            return payload
        client, requests = self.inference_client(source, invalid)
        context = AsyncMock()
        context.__aenter__.return_value = client
        with patch('services.report_insights.httpx.AsyncClient', return_value=context), self.assertRaises(ValueError):
            await service.generate(source)
        target = folder(service.root, digest(VERSION, source)) / 'rejected-latest.json'
        original = read_json(target)
        for mismatch in (False, True):
            modified = {**original, 'validation_error': 'UNTRUSTED_ERROR_INSTRUCTION'}
            if mismatch:
                modified['contract_hash'] = 'a' * 64
            write_json(target, modified)
            checkpoint = target.parent / 'checkpoint.json'
            checkpoint.unlink(missing_ok=True)
            client, requests = self.inference_client(source)
            context.__aenter__.return_value = client
            with self.subTest(mismatch=mismatch), patch('services.report_insights.httpx.AsyncClient', return_value=context):
                generated = await service.generate(source)
            body = json.loads(requests[0]['messages'][1]['content'])
            self.assertEqual('repair' in body, not mismatch)
            self.assertNotIn('UNTRUSTED_ERROR_INSTRUCTION', requests[0]['messages'][1]['content'])
            self.assertEqual(generated['result'], result_for(source))

    async def test_checkpoint_invalid_fragment_discards_only_it_and_following_parts(self):
        source = report()
        service = self.new_service()
        client, requests = self.inference_client(source)
        context = AsyncMock()
        context.__aenter__.return_value = client
        with patch('services.report_insights.httpx.AsyncClient', return_value=context):
            await service.generate(source)
        target = folder(service.root, digest(VERSION, source)) / 'checkpoint.json'
        valid = read_json(target)
        for corruption in ('foreign_ref', 'number_claim', 'cross_part_repetition'):
            saved = copy.deepcopy(valid)
            item = saved['parts'][2]['fragment']['sections'][0]
            if corruption == 'foreign_ref':
                item['sources'] = ['personal:0']
            elif corruption == 'number_claim':
                item['insight'] = 'Число судьбы 22 определяет ваши способности.'
            else:
                item['practice'] = saved['parts'][1]['fragment']['sections'][0]['practice']
            write_json(target, saved)
            client, requests = self.inference_client(source)
            context.__aenter__.return_value = client
            with self.subTest(corruption=corruption), patch('services.report_insights.httpx.AsyncClient', return_value=context):
                generated = await service.generate(source)
            self.assertEqual(len(requests), len(generation_parts(source)) - 2)
            self.assertEqual(generated['result'], result_for(source))
            self.assertEqual(sum(call.get('cached', False) for call in generated['calls']), 2)

    async def test_checkpoint_identity_and_model_mismatch_cannot_reuse_prose(self):
        source = report()
        service = self.new_service()
        client, requests = self.inference_client(source)
        context = AsyncMock()
        context.__aenter__.return_value = client
        with patch('services.report_insights.httpx.AsyncClient', return_value=context):
            await service.generate(source)
        target = folder(service.root, digest(VERSION, source)) / 'checkpoint.json'
        valid = read_json(target)
        for field, value in (('version', 'old-version'), ('key', 'a' * 64),
                             ('contract_hash', 'b' * 64), ('model', 'another-model')):
            write_json(target, {**valid, field: value})
            client, requests = self.inference_client(source)
            context.__aenter__.return_value = client
            with self.subTest(field=field), patch('services.report_insights.httpx.AsyncClient', return_value=context):
                generated = await service.generate(source)
            self.assertEqual(len(requests), len(generation_parts(source)))
            self.assertFalse(any(call.get('cached', False) for call in generated['calls']))
            self.assertEqual(generated['result'], result_for(source))

    async def test_complete_checkpoint_can_be_verified_without_another_model_request(self):
        source = report()
        service = self.new_service()
        client, requests = self.inference_client(source)
        context = AsyncMock()
        context.__aenter__.return_value = client
        with patch('services.report_insights.httpx.AsyncClient', return_value=context):
            first = await service.generate(source)
        client.post.side_effect = AssertionError('validated checkpoint must not request inference')
        with patch('services.report_insights.httpx.AsyncClient', return_value=context):
            resumed = await service.generate(source)
        self.assertEqual(resumed['result'], first['result'])
        self.assertEqual(resumed['eval_count'], 0)
        self.assertTrue(all(call['cached'] for call in resumed['calls']))
        self.assertEqual(len(requests), len(generation_parts(source)))

    async def test_rejected_response_is_bounded_and_never_copied_into_next_prompt(self):
        source = report()
        service = self.new_service()
        secret_marker = 'REJECTED_FRAGMENT_DO_NOT_REPLAY'
        oversized = secret_marker + 'х' * 15000
        client, requests = self.inference_client(source, lambda index, payload: {
            **payload, 'message': {'content': oversized}})
        context = AsyncMock()
        context.__aenter__.return_value = client
        with patch('services.report_insights.httpx.AsyncClient', return_value=context), self.assertRaises(ValueError):
            await service.generate(source)
        path = folder(service.root, digest(VERSION, source)) / 'rejected-latest.json'
        rejection = read_json(path)
        self.assertEqual(len(rejection['content']), 14000)
        self.assertTrue(rejection['truncated'])
        self.assertLess(path.stat().st_size, MAX_JSON_BYTES)
        self.assertEqual(rejection['attempt'], ATTEMPTS)
        self.assertTrue(all(secret_marker not in request['messages'][1]['content'] for request in requests))

    async def test_symlink_or_corrupt_checkpoint_is_not_trusted(self):
        source = report()
        for corrupt in ('json', 'symlink'):
            service = self.new_service()
            target = folder(service.root, digest(VERSION, source))
            target.mkdir(parents=True)
            checkpoint = target / 'checkpoint.json'
            outside = self.root / 'outside-checkpoint.json'
            outside.write_text('{"untrusted": true}')
            if corrupt == 'symlink':
                checkpoint.symlink_to(outside)
            else:
                checkpoint.write_text('broken json')
            client, requests = self.inference_client(source)
            context = AsyncMock()
            context.__aenter__.return_value = client
            with self.subTest(corrupt=corrupt), patch('services.report_insights.httpx.AsyncClient', return_value=context):
                generated = await service.generate(source)
            self.assertEqual(generated['result'], result_for(source))
            self.assertEqual(len(requests), len(generation_parts(source)))
            self.assertFalse(checkpoint.is_symlink())
            self.assertEqual(outside.read_text(), '{"untrusted": true}')

    async def test_two_invalid_attempts_stop_without_partial_success(self):
        source = report()
        def always_foreign(index, payload):
            if 2 <= index < 2 + ATTEMPTS:
                fragment = json.loads(payload['message']['content'])
                fragment['sections'][0]['sources'] = ['square:0']
                payload['message']['content'] = json.dumps(fragment)
            return payload
        client, requests = self.inference_client(source, always_foreign)
        context = AsyncMock()
        context.__aenter__.return_value = client
        with patch('services.report_insights.httpx.AsyncClient', return_value=context), self.assertRaisesRegex(ValueError, f'after {ATTEMPTS} attempts'):
            await self.new_service().generate(source)
        self.assertEqual(len(requests), 1 + ATTEMPTS)

    async def test_cross_part_repetition_gets_bounded_repair_without_losing_previous_parts(self):
        source = report()
        def repeated(index, payload):
            if index == 3:
                fragment = json.loads(payload['message']['content'])
                fragment['sections'][0]['practice'] = result_for(source)['sections'][0]['practice']
                payload['message']['content'] = json.dumps(fragment)
            return payload
        client, requests = self.inference_client(source, repeated)
        context = AsyncMock()
        context.__aenter__.return_value = client
        with patch('services.report_insights.httpx.AsyncClient', return_value=context):
            generated = await self.new_service().generate(source)
        self.assertEqual(generated['result'], result_for(source))
        self.assertEqual(len(requests), len(generation_parts(source)) + 1)
        repair = json.loads(requests[3]['messages'][1]['content'])['repair']
        self.assertIn('Repeated interpretation passage', repair['validation_error'])

    async def test_math_and_foreign_references_are_never_relaxed_on_repair(self):
        source = report()
        for invalid in ('Мастер-число 22 означает неизбежный успех.', 'Вы обладаете выдающейся способностью убеждать.'):
            def unsafe(index, payload):
                fragment = json.loads(payload['message']['content'])
                fragment['strengths'][0]['text'] = invalid
                payload['message']['content'] = json.dumps(fragment)
                return payload
            client, requests = self.inference_client(source, unsafe)
            context = AsyncMock()
            context.__aenter__.return_value = client
            with self.subTest(invalid=invalid), patch('services.report_insights.httpx.AsyncClient', return_value=context), self.assertRaisesRegex(ValueError, f'after {ATTEMPTS} attempts'):
                await self.new_service().generate(source)
            self.assertEqual(len(requests), ATTEMPTS)

    async def test_incomplete_or_malformed_model_response_is_never_accepted(self):
        source = report()
        variants = [[], {'done': False}, {'done': True, 'done_reason': 'length'}, {'done': True, 'message': []},
                    {'done': True, 'message': {'content': 'not JSON'}}, {'done': True, 'message': {'content': '[]'}}]
        for payload in variants:
            client = SimpleNamespace(post=AsyncMock(return_value=httpx.Response(200, json=payload, request=httpx.Request('POST', 'http://localhost'))))
            context = AsyncMock()
            context.__aenter__.return_value = client
            with self.subTest(payload=payload), patch('services.report_insights.httpx.AsyncClient', return_value=context), self.assertRaises(ValueError):
                await self.new_service().generate(source)
            self.assertEqual(client.post.call_count, ATTEMPTS)


if __name__ == '__main__':
    unittest.main()
