"""Regression checks for Whisper's numeric spelling of Russian dates; no synthesis."""
import importlib.util
from pathlib import Path
import re
import unittest
from num2words import num2words

spec=importlib.util.spec_from_file_location('worker',Path(__file__).with_name('generate-project-voices.py'))
worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)

class Voice:
    @staticmethod
    def words(text):
        text=re.sub(r'\d+',lambda match:num2words(int(match[0]),lang='ru'),text)
        return re.sub(r'[^а-яё ]',' ',text.lower().replace('ё','е')).split()

class Numbers(unittest.TestCase):
    def words(self,text):return worker.comparison_words(text,Voice)
    def test_date_case_and_ordinal_are_same_value(self):
        self.assertEqual(self.words('Десятое января тысяча девятьсот восемьдесят второго года'),self.words('10 января 1982 года'))
    def test_gender_and_case_keep_the_number(self):
        self.assertEqual(self.words('Одна четвёрка, две единицы, сумма равна двадцати двум'),self.words('1 четвёрка, 2 единицы, сумма равна 22'))
    def test_long_numbers_are_never_left_as_digits_for_tts(self):
        product=worker.spoken('1001 умножить на 1982 равно 1983982.')
        self.assertNotRegex(product,r'\d')
        self.assertIn('равно один, девять, восемь, три, девять, восемь, два.',product)
        # However Whisper writes the spoken digits, both sides normalise to the same words.
        for heard in ('1001 умножить на 1982 равно 1, 9, 8, 3, 9, 8, 2.','1001 умножить на 1982 равно 1983982.'):
            self.assertEqual(self.words(heard),self.words(product))
        self.assertEqual(worker.spoken('Телефон 37360123456, код 0123'),'Телефон три, семь, три, шесть, ноль, один, два, три, четыре, пять, шесть, код сто двадцать три')
        self.assertEqual(worker.spoken('Код 012345.'),'Код ноль, один, два, три, четыре, пять.')
        # Whisper prints the product as digits; both sides normalise to the same words.
        self.assertEqual(self.words('1001 умножить на 1982 равно 1983982.'),self.words(product))
        self.assertNotEqual(self.words('равно 1982.'),self.words(product))
    def test_lone_latin_letters_are_named_and_words_stay(self):
        self.assertEqual(worker.spoken('Ряд 1, позиция 2: M ; далее 4.'),'Ряд один, позиция два: эм ; далее четыре.')
        self.assertEqual(worker.spoken('NumerOM и ERP'),'NumerOM и ERP')
        # Whisper may print the letter in Latin; both sides become the same word.
        self.assertEqual(self.words('позиция 2: M'),self.words('позиция два: эм'))
        self.assertNotEqual(self.words('позиция 2: M'),self.words('позиция два: эн'))
        # Heard with the Cyrillic letter (as Whisper prints «эм»), and prepositions unchanged.
        self.assertEqual(self.words('Ряд 1, позиция 2, М далее 4.'),self.words(worker.spoken('Ряд 1, позиция 2: M ; далее 4.')))
        self.assertEqual(self.words('в доме с садом'),self.words('в доме с садом'))
        self.assertNotEqual(self.words('позиция 2, Н'),self.words('позиция два: эм'))
    def test_course_formula_has_spoken_operators_and_named_variables(self):
        speech=worker.spoken('ЧП 1 равно |А − В|; ЧП 2 равно |А − С|. ДДММ × год.')
        self.assertIn('число проблемы один равно модуль разности а и вэ',speech)
        self.assertIn('число проблемы два равно модуль разности а и эс',speech)
        self.assertIn('день и месяц без разделителей умножить на год',speech)
        self.assertNotRegex(speech,r'[|×−]|ЧП|ДДММ')
        self.assertEqual(worker.spoken('А вы в доме с садом.'),'А вы в доме с садом.')
    def test_challenge_formula_keeps_subtraction_and_each_index(self):
        speech=worker.spoken('ЧП 3 равно |ЧП 1 − ЧП 2|. Разность −7. А, В, С.')
        self.assertIn('модуль разности число проблемы один и число проблемы два',speech)
        self.assertIn('минус семь',speech)
        self.assertIn('а, вэ, эс',speech)
        self.assertNotEqual(speech,worker.spoken('ЧП 3 равно |ЧП 2 − ЧП 1|.'))
    def test_wrong_date_and_omitted_number_still_fail(self):
        self.assertNotEqual(self.words('Десятое января тысяча девятьсот восемьдесят второго года'),self.words('11 января 1982 года'))
        self.assertNotEqual(self.words('Пять двоек'),self.words('Двойки'))
    def test_whisper_singular_variant_does_not_hide_missing_numbers(self):
        expected='пять:тридцать–шесть:тридцать восемь. Действие, решительность и личные границы.'
        self.assertEqual(self.words(expected),self.words('5, 30, 6, 38. Действия, решительность и личные границы.'))
        self.assertNotEqual(self.words(expected),self.words('5, 30, 6, 39. Действия, решительность и личные границы.'))
        self.assertNotEqual(self.words(expected),self.words('5, 30, 6, 38. Решительность и личные границы.'))

if __name__=='__main__':unittest.main()
