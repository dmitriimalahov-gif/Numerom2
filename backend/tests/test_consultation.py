"""The listener learns a term before hearing interpretations or advice."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from domain.consultation import explanation, VOICE
from domain.full_report import build_full_report, full_report_clips
from domain.narration import clip, lesson_clips
from services.narration import NarrationService

ROOT = Path(__file__).resolve().parents[2]


class ConsultationContract(unittest.TestCase):
    def setUp(self):
        self.report = build_full_report('10.01.1982', '2026-11-07')
        self.audio = {c['id']: c['text'] for c in self.report['narration']}

    def test_concepts_before_values_and_coincidence_before_advice(self):
        text = self.audio['full-report-personal']
        self.assertLess(text.index('Число души — это про'), text.index('Число души: 1.'))
        self.assertLess(text.index('Число ума — это про'), text.index('Число ума: 1.'))
        self.assertLess(text.index('Число ума: 1.'), text.index('Когда числа души и ума совпадают'))
        self.assertLess(text.index('Когда числа души и ума совпадают'), text.index('Сила этого числа'))
        self.assertNotIn('День рождения: 10;', text)
        self.assertNotIn('Месяц рождения: 1;', text)
        self.assertNotIn('10 плюс 1 равно 11', text)
        self.assertEqual(text.count('Единица напоминает о ценности собственного голоса.'), 1)

    def test_distinct_values_do_not_get_coincidence_story(self):
        report = build_full_report('02.03.1990', '2026-11-07')
        text = next(c['text'] for c in report['narration'] if c['id'] == 'full-report-personal')
        self.assertNotIn('Когда числа души и ума совпадают', text)
        self.assertIn('Число души: 2.', text)
        self.assertIn('Число ума: 3.', text)

    def test_cells_and_all_routes_explained_without_reinterpreting_counts(self):
        square = self.audio['full-report-square']
        for digit in range(1, 10): self.assertIn(f'Ячейка {digit} — про', square)
        self.assertIn('Количество в вашем расчёте: 0.', square)
        self.assertEqual(square.count('Ноль означает'), 1)
        lines = self.audio['full-report-lines']
        for kind, route in [('Горизонталь','один, четыре, семь'),('Горизонталь','два, пять, восемь'),
                            ('Горизонталь','три, шесть, девять'),('Вертикаль','один, два, три'),
                            ('Вертикаль','четыре, пять, шесть'),('Вертикаль','семь, восемь, девять'),
                            ('Диагональ','один, пять, девять'),('Диагональ','три, пять, семь')]:
            self.assertLess(lines.index(kind+' '+route+' — про'), lines.index(kind+' '+route+'. Количество'))

    def test_every_calculation_guide_has_known_plain_explanation(self):
        entries = json.loads((ROOT/'packages/project-knowledge/ru.json').read_text())['items']
        for entry in entries:
            if entry['section'] == 'guide': continue
            with self.subTest(id=entry['id']):
                self.assertTrue(explanation(entry['id']))
                spoken = clip(entry['id'],entry['section'],entry['title'],entry['text'])
                self.assertTrue(spoken['text'].startswith(explanation(entry['id'])))
                self.assertEqual(spoken['voice'],VOICE)

    def test_renderer_never_changes_frozen_calculations(self):
        before = copy.deepcopy(self.report)
        self.assertEqual(full_report_clips(self.report),self.report['narration'])
        self.assertEqual(before,self.report)

    def test_voice_and_style_have_new_cache_identity(self):
        args = ('mind','numbers','Число ума','Текст для проверки.')
        new,old = clip(*args),clip(*args,consultation=False)
        self.assertNotEqual(new['hash'],old['hash'])
        self.assertNotIn('voice',old)
        self.assertEqual(new['voice'],VOICE)

    def test_questions_remain_exact_visible_questions(self):
        lesson = {'title':'Число ума', 'content':{'quiz':{'questions':[{
            'question':'Что означает число ума?', 'options':['А','Б'],
            'correct_answer':0,'explanation':'Секретный ответ'}]}}}
        new = next(c for c in lesson_clips(lesson) if c['section']=='quiz')
        old = next(c for c in lesson_clips(lesson,consultation=False) if c['section']=='quiz')
        self.assertEqual(new['text'],old['text'])
        self.assertNotIn('про способ думать',new['text'])
        self.assertNotIn('Секретный',new['text'])

    def test_theory_defines_terms_at_first_mention_even_with_generic_heading(self):
        item=clip('theory-0','theory','Основное',
            'Рассмотрим число ума. Затем вертикаль 4–5–6. Снова обсудим число ума.')
        text=item['text']
        self.assertEqual(text.count('Число ума — это про'),1)
        self.assertLess(text.index('Число ума — это про'),text.index('Рассмотрим число ума'))
        self.assertLess(text.index('Вертикаль 4–5–6 — про'),text.index('Затем вертикаль'))

    def test_existing_playback_remains_until_verified_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = NarrationService(None,root=tmp)
            args = ('mind','numbers','Число ума','Текст для проверки.')
            new,old = clip(*args),clip(*args,consultation=False)
            def ready(item):
                path=Path(tmp)/'clips'/item['hash'];path.mkdir(parents=True)
                audio=path/'audio.m4a';audio.write_bytes(b'audio')
                digest=hashlib.sha256(b'audio').hexdigest()
                (path/'ready.json').write_text(json.dumps({'hash':item['hash'],'bytes':5,'seconds':1,'sha256':digest}))
            ready(old)
            self.assertEqual(service.prefer_current(new,old)['hash'],old['hash'])
            self.assertTrue(service.prefer_current(new,old)['replacement_pending'])
            changed=clip(*args[:-1],'Новый видимый текст.',consultation=False)
            self.assertEqual(service.prefer_current(new,changed)['hash'],new['hash'])
            ready(new)
            self.assertEqual(service.prefer_current(new,old)['hash'],new['hash'])


if __name__ == '__main__': unittest.main()
