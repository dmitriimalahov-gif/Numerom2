"""The greeting video follows measured speech, including short opening sentences."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('author_voice', ROOT/'scripts/render-author-conversation.py')
author = importlib.util.module_from_spec(spec); spec.loader.exec_module(author)


class GreetingTiming(unittest.TestCase):
    def test_brand_spelling_and_short_greeting_are_aligned(self):
        words = [{'word': word, 'start': start, 'end': end} for word, start, end in
            [('Здравствуйте!', .1, .8), ('Я', 1.1, 1.3), ('Дмитрий,', 1.3, 1.8),
             ('автор', 1.9, 2.2), ('NumerOM.', 2.2, 2.8)]]
        result = author.sentence_timings('Здравствуйте! Я Дмитрий, автор Нумером.',
            {'segments': [{'words': words}]}, 3)
        self.assertEqual([(c['start'], c['end']) for c in result], [(.1, .8), (1.1, 2.8)])

    def test_missing_sentence_cannot_get_fabricated_timing(self):
        with self.assertRaises(ValueError):
            author.sentence_timings('Здравствуйте! Введите свою дату рождения.',
                {'segments': [{'words': [{'word': 'Здравствуйте!', 'start': 0, 'end': 1}]}]}, 2)

    def test_product_normalization_does_not_hide_wrong_words(self):
        self.assertEqual(author.words('NumerOM, Нумер ОМ, Нумером'), ['нумером']*3)
        self.assertNotEqual(author.words('Нумером'), author.words('Номером'))


if __name__ == '__main__': unittest.main()
