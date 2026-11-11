import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import russian_pronunciation as p

class RussianPronunciation(unittest.TestCase):
    def test_audio_revision_is_separate_from_text_and_voice(self):
        from domain.narration import clip
        from unittest.mock import patch
        current=clip('number-1','numbers','Число','Ваше число один.')
        with patch('domain.narration.PRONUNCIATION','previous'):
            previous=clip('number-1','numbers','Число','Ваше число один.')
        self.assertNotEqual(current['hash'],previous['hash'])
        self.assertEqual(current['text'],previous['text'])
        self.assertEqual(current['voice'],previous['voice'])

    def test_previous_selected_voice_cache_can_remain_playable(self):
        from domain.narration import clip,PROFILE,STYLE,VOICE_IDENTITY
        import hashlib
        text='Короткий текст.'
        old=clip('intro','intro','Приветствие',text,previous_pronunciation=True)
        expected=hashlib.sha256(('\0'.join([PROFILE,STYLE,VOICE_IDENTITY,text,text])).encode()).hexdigest()
        self.assertEqual(old['hash'],expected)
        self.assertNotIn('pronunciation',old)

    def test_context_not_a_global_word_replacement(self):
        model=Mock();model.process_all.return_value='эти ч+исла зависят от числ+а д+уши.'
        result=p.prepare('Эти числа зависят от числа души.',model)
        self.assertEqual(result,'Эти чи́сла зависят от числа́ ду́ши.')
        self.assertEqual(p.canonical(result),p.canonical('Эти числа зависят от числа души.'))

    def test_preserves_punctuation_digits_and_author_stress(self):
        text='Число души — 1. Автор: Дми́трий!'
        result=p.merge_marks(text,'числ+о д+уши 1 +автор дмитр+ий')
        self.assertEqual(result,'Число́ ду́ши — 1. А́втор: Дми́трий!')

    def test_yo_restoration_and_case(self):
        self.assertEqual(p.merge_marks('Все расчеты — в отчете.', 'все расчёты в отчёте'),
                         'Все расчёты — в отчёте.')

    def test_drops_and_substitutions_fail_closed(self):
        for wrong in ['души','число ума','число души снова','ч+исл+о души','́число души']:
            with self.subTest(wrong=wrong),self.assertRaises(ValueError):p.merge_marks('число души',wrong)

    def test_greeting_regression_words(self):
        text='Нумером. Двигайтесь в своём ритме. Свои личные числа: что за ними стоит. Имени и даже адреса.'
        model=Mock();model.process_all.return_value=text.lower()
        output=p.prepare(text,model)
        for marked in ('Нумеро́м','Дви́гайтесь','ри́тме','чи́сла','стои́т','а́дреса'):
            self.assertIn(marked,output)
        self.assertEqual(p.canonical(text),p.canonical(output))

    @unittest.skipUnless((p.RESOURCE/'accentuator/nn/nn_accent/model.onnx').is_file(),
                         'Local pronunciation models required')
    def test_real_unknown_word_uses_required_onnx_inputs(self):
        # This exercises CharTokenizer -> ONNX, bypassed for dictionary words.
        self.assertEqual(p.canonical(p.prepare('Чандры')), 'чандры')

    @unittest.skipUnless((p.RESOURCE/'accentuator/nn/nn_accent/model.onnx').is_file(),
                         'Local pronunciation models required')
    def test_real_formula_separator_does_not_join_words(self):
        text='Вариант два. А плюс В−С.'
        self.assertEqual(p.canonical(p.prepare(text)), p.canonical(text))

    @unittest.skipUnless(importlib.util.find_spec('num2words'),'Voice runtime dependency')
    def test_word_check_does_not_split_accented_words(self):
        spec=importlib.util.spec_from_file_location('voice_worker',ROOT/'scripts/generate-project-voices.py')
        worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
        mock=Mock();mock.words=lambda s:__import__('re').findall('[а-яё]+',s.lower())
        self.assertEqual(worker.comparison_words('Квадрат Пифаго́ра. Дви́гайтесь.',mock),worker.comparison_words('Квадрат Пифагора. Двигайтесь.',mock))

if __name__=='__main__':unittest.main()
