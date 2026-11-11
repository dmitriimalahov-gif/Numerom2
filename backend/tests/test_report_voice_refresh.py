"""A voice refresh queues only validated speech and never repeats a payment or email."""
import copy
import importlib.util
from pathlib import Path
import sys
from unittest import TestCase
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('voice_refresh', ROOT/'scripts/prepare-report-voice-refresh.py')
refresh = importlib.util.module_from_spec(spec); spec.loader.exec_module(refresh)


class VoiceRefresh(TestCase):
    def test_pending_interpretation_only_queues_once_and_keeps_snapshot(self):
        report = {'birth_date': '10.01.1982', 'raw': {'soul': 1}, 'narration': [{'voice': 'legacy'}]}
        original = copy.deepcopy(report)
        insights, voice, video = Mock(), Mock(), Mock()
        insights.enrich.return_value = (report, 'preparing')
        result = refresh.prepare([report, report], insights, voice, video)
        self.assertEqual(result, {'snapshots': 1, 'analysis_preparing': 1})
        insights.enrich.assert_called_once_with(report)
        voice.enqueue.assert_not_called(); video.enqueue.assert_not_called()
        self.assertEqual(report, original)

    def test_ready_current_voice_enqueues_downstream_without_mutation(self):
        original = {'raw': {'soul': 1}}
        current = {'raw': {'soul': 1}, 'narration': [{'id': 'full-report-personal', 'voice': refresh.VOICE}]}
        insights, voice, video = Mock(), Mock(), Mock()
        insights.enrich.return_value = (current, 'ready')
        voice.state.return_value = {'status': 'preparing'}
        video.state.return_value = {'status': 'waiting_audio'}
        result = refresh.prepare([original], insights, voice, video)
        voice.enqueue.assert_called_once_with(current['narration'][0], 'full-report', 'paid-report')
        video.enqueue.assert_called_once_with(current)
        self.assertEqual(result['audio_preparing'], 1)
        self.assertEqual(original, {'raw': {'soul': 1}})

    def test_legacy_voice_cannot_be_accepted_as_a_completed_replacement(self):
        insights, voice, video = Mock(), Mock(), Mock()
        insights.enrich.return_value = ({'narration': [{'voice': 'dmitrii'}]}, 'ready')
        with self.assertRaises(ValueError): refresh.prepare([{'raw': {}}], insights, voice, video)
        voice.enqueue.assert_not_called(); video.enqueue.assert_not_called()
