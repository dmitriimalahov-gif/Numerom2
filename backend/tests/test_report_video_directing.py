"""Pure cue direction; no server, database, model or audio generation."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from domain.report_video import cue_segments, FPS


class CueDirectionTests(unittest.TestCase):
    def section(self):
        return {'values': [{'key': 'soul', 'label': 'Число души', 'value': 1},
            {'key': 'mind', 'label': 'Число ума', 'value': 1},
            {'key': 'destiny', 'label': 'Число судьбы', 'value': 4},
            {'key': 'helping_mind', 'label': 'Помогающее число ума', 'value': 11}]}

    def meta(self, text, seconds=12, **extra):
        return {'segments': [{'seconds': seconds, 'cues': [{'start': 0, 'end': seconds, 'text': text, **extra}]}]}

    def test_multiple_named_results_in_one_phrase_get_ordered_independent_focus(self):
        item = cue_segments(self.meta('Число души — один. Число ума — один. Число судьбы — четыре.'), self.section())[0]
        self.assertEqual([c['focusIndex'] for c in item['focusCues']], [0, 1, 2])
        self.assertEqual(item['timingSource'], 'asr')
        self.assertTrue(all(c['timingSource'] == 'estimated' for c in item['focusCues']))
        for a, b in zip(item['focusCues'], item['focusCues'][1:]):
            self.assertEqual(a['fromFrame'] + a['durationInFrames'], b['fromFrame'])
        self.assertEqual(item['focusCues'][-1]['fromFrame'] + item['focusCues'][-1]['durationInFrames'], 12 * FPS)

    def test_longest_label_wins_over_nested_mind_label(self):
        item = cue_segments(self.meta('Помогающее число ума — одиннадцать.'), self.section())[0]
        self.assertEqual([c['focusIndex'] for c in item['focusCues']], [3])

    def test_shorthand_requires_the_saved_value_and_never_matches_unrelated_numbers(self):
        item = cue_segments(self.meta('Душа один, ум один, судьба четыре, помогающий ум одиннадцать.'), self.section())[0]
        self.assertEqual([c['focusIndex'] for c in item['focusCues']], [0, 1, 2, 3])
        other = cue_segments(self.meta('Год одиннадцать, месяц четыре. Душа девять.'), self.section())[0]
        self.assertNotIn('focusCues', other)

    def test_summary_clears_unrelated_focus_but_can_direct_multiple_mentions(self):
        meta = {'segments': [{'seconds': 6, 'cues': [
            {'start': 0, 'end': 2, 'text': 'Число души — один.'},
            {'start': 2, 'end': 4, 'text': 'Фрактал: один, один, два, четыре.'},
            {'start': 4, 'end': 6, 'text': 'Число ума и число судьбы.'}]}]}
        items = cue_segments(meta, self.section(), summary=True)
        self.assertNotIn('focusIndex', items[1]); self.assertNotIn('focusCues', items[1])
        self.assertEqual([c['focusIndex'] for c in items[2]['focusCues']], [1, 2])

    def test_optional_asr_word_timestamps_take_precedence_over_character_estimate(self):
        timed = [{'word': w, 'start': a, 'end': b} for w, a, b in [
            ('Теперь', 0, 1), ('число', 4, 4.4), ('души', 4.4, 5), ('один', 5, 5.5)]]
        item = cue_segments(self.meta('Теперь число души один', seconds=6, words=timed), self.section())[0]
        self.assertEqual(item['focusCues'][0]['fromFrame'], 4 * FPS)
        self.assertEqual(item['focusCues'][0]['timingSource'], 'asr-word')

    def test_old_recordings_explicitly_mark_estimated_captions_and_stay_in_duration(self):
        item = cue_segments({'segments': [{'seconds': 4, 'text': 'Число души — один.'}]}, self.section())[0]
        self.assertEqual(item['timingSource'], 'estimated')
        self.assertEqual(item['durationInFrames'], 4 * FPS)

    def test_task_short_label_does_not_require_speaking_entire_age_range(self):
        section = {'values': [{'key': 'problem1', 'label': 'Задача 1 · границы 32 и 41 лет', 'value': 0}]}
        item = cue_segments(self.meta('Задача один: ноль.'), section)[0]
        self.assertEqual(item['focusCues'][0]['focusIndex'], 0)

    def test_fractal_repeated_digits_are_separate_saved_positions(self):
        section = {'id': 'fractal', 'values': [{'label': label, 'value': digit} for label, digit in
            [('Начало', 1), ('Осмысление', 1), ('Опыт', 2), ('Соединение', 4)]]}
        item = cue_segments(self.meta('Фрактал: один, один, два, четыре.'), section)[0]
        self.assertEqual([c['focusIndex'] for c in item['focusCues']], [0, 1, 2, 3])
        wrong = cue_segments(self.meta('Фрактал: один, один, два, девять.'), section)[0]
        self.assertNotIn('focusCues', wrong)

    def test_narrated_square_order_follows_saved_labels_not_numeric_sort(self):
        section = {'id': 'square', 'values': [{'label': str(d) + ' · Планета', 'value': 0} for d in [1, 4, 7, 2, 5, 8, 3, 6, 9]]}
        item = cue_segments(self.meta('Расположение ячеек: один, четыре, семь, два, пять, восемь, три, шесть, девять.'), section)[0]
        self.assertEqual([c['focusIndex'] for c in item['focusCues']], list(range(9)))

    def test_out_of_bounds_words_and_overlapping_cues_are_rejected(self):
        with self.assertRaises(ValueError):
            cue_segments(self.meta('Число души', seconds=2, words=[
                {'word': 'Число', 'start': 0, 'end': 1}, {'word': 'души', 'start': 1, 'end': 3}]), self.section())
        with self.assertRaises(ValueError):
            cue_segments({'segments': [{'seconds': 2, 'cues': [
                {'start': 0, 'end': 1.5, 'text': 'Начало'}, {'start': 1, 'end': 2, 'text': 'Далее'}]}]}, {})


if __name__ == '__main__': unittest.main()
