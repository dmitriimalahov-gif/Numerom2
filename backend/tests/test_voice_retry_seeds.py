"""No model inference: worker retries keep verified chunks and get fresh entropy."""
from contextlib import nullcontext
import builtins
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))


class VoiceRetrySeedTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        with patch.dict(sys.modules, {'num2words': SimpleNamespace(num2words=lambda n, **kw: str(n))}), patch.dict(os.environ):
            spec = importlib.util.spec_from_file_location('numerom_voice_retry_seed_tests', ROOT / 'scripts/generate-project-voices.py')
            self.worker = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.worker)
        # The fake samples cannot go through FFmpeg; tempo has its own test below.
        tempo = patch.dict(self.worker.voice_tempo.TEMPO, clear=True); tempo.start(); self.addCleanup(tempo.stop)
        self.key = 'a' * 64
        self.queue = self.root / 'backend/private/narration'
        self.cache = self.queue / 'clips' / self.key
        self.cache.mkdir(parents=True)
        (self.queue / 'jobs').mkdir()
        (self.queue / 'jobs' / (self.key + '.json')).write_text(json.dumps({
            'hash': self.key, 'id': 'full-report-seed-test', 'section': 'full-report',
            'text': 'Тестовая запись.'}), encoding='utf-8')
        self.helper = self.root / 'helper'
        (self.helper / 'voice').mkdir(parents=True)
        (self.helper / 'voice/helper_male_ref.wav').write_bytes(b'synthetic Helper reference')
        (self.helper / 'voice/helper_male_ref.txt').write_text('Фраза Helper.', encoding='utf-8')
        (self.helper / 'voice/dmitrii_ref.wav').write_bytes(b'synthetic Dmitrii reference')
        (self.helper / 'voice/dmitrii_ref.txt').write_text('Фраза Дмитрия.', encoding='utf-8')

    def queue_voice(self, value):
        path = self.queue / 'jobs' / (self.key + '.json')
        job = json.loads(path.read_text())
        job['voice'] = value
        path.write_text(json.dumps(job), encoding='utf-8')

    def read(self, name):
        return json.loads((self.cache / name).read_text())

    def run_worker(self, texts, heard, base_seed, retry=False, cue_end=None, automatic=False, reuse=False, low_memory=False, headroom=True):
        """Exercise actual worker.main with fake samples, TTS, ASR and encoder."""
        class Samples:
            def __init__(self, size=10): self.size = size
            def __len__(self): return self.size
            def astype(self, dtype): return self
        events = SimpleNamespace(seeds=[], texts=[], reads=[], prompts=[], references=[], temperatures=[], processing=[], asr_loads=0)
        transcripts = iter(heard)
        def seed(value):
            events.seeds.append(value)
        def generate(**kwargs):
            # The seed must be on disk before synthesis, including a crash here.
            saved = self.read('generation.json')
            self.assertEqual(saved['attempts'][-1]['seed'], events.seeds[-1])
            self.assertEqual(saved['attempts'][-1]['status'], 'synthesizing')
            events.texts.append(kwargs['text'])
            events.references.append((Path(kwargs['ref_audio']).name, kwargs.get('ref_text')))
            events.temperatures.append(kwargs['temperature'])
            return [SimpleNamespace(audio=Samples())]
        def transcribe(*args, **kwargs):
            if whisper.model is None:
                events.asr_loads += 1
                whisper.model = object(); whisper.model_path = 'resolved-offline-whisper'
            self.assertEqual(kwargs['path_or_hf_repo'], 'resolved-offline-whisper')
            events.prompts.append(kwargs['initial_prompt'])
            result = next(transcripts)
            if isinstance(result, Exception): raise result
            # cue_end: Whisper's end of the only phrase, possibly after the audio ends.
            return {'text': result, 'segments': [] if cue_end is None else [{'start': 0, 'end': cue_end, 'text': result}]}
        def read_audio(path, **kwargs):
            events.reads.append(Path(path))
            return Samples(), 10
        voice = SimpleNamespace(
            load_model=Mock(return_value=SimpleNamespace(sample_rate=10, generate=generate)),
            mx=SimpleNamespace(set_cache_limit=Mock(), random=SimpleNamespace(seed=seed), clear_cache=Mock()),
            np=SimpleNamespace(concatenate=lambda arrays: Samples(sum(len(a) for a in arrays)), asarray=lambda array: array,
                float32='float32', zeros=lambda size, **kwargs: Samples(size)),
            polish=lambda audio, sr: events.processing.append('polish') or audio, to16k=lambda audio, sr: audio,
            highpass=lambda audio, sr: events.processing.append('highpass') or audio,
            gate=lambda audio, sr: events.processing.append('gate') or audio,
            soft_edges=lambda audio, sr: events.processing.append('soft_edges') or audio,
            loudness=lambda audio: events.processing.append('loudness') or audio,
            words=lambda text: re.findall(r'[а-яё0-9]+', text.lower()), WHISPER='synthetic-whisper',
            mlx_whisper=SimpleNamespace(transcribe=transcribe),
            sf=SimpleNamespace(write=lambda path, *args: Path(path).write_bytes(b'synthetic PCM'), read=read_audio))
        whisper = SimpleNamespace(model=None, model_path=None)
        def encode(command, **kwargs):
            self.assertEqual(command[0], '/usr/bin/afconvert')
            Path(command[-1]).write_bytes(b'synthetic AAC')
        handles, original_open = [], Path.open
        def tracked_open(path, *args, **kwargs):
            stream = original_open(path, *args, **kwargs)
            if path.name == 'worker.lock': handles.append(stream)
            return stream
        argv = ['generate-project-voices.py', '--limit', '1'] + (['--retry-failed'] if retry else []) + (['--auto-retry'] if automatic else [])
        argv += (['--reuse-models'] if reuse else []) + (['--low-memory'] if low_memory else [])
        try:
            with patch.object(self.worker, 'ROOT', self.root), patch.object(self.worker, 'HELPER', self.helper), \
                    patch.object(self.worker, 'local_whisper_model', return_value='resolved-offline-whisper'), \
                    patch.object(self.worker, 'model_memory_available', **({'side_effect':headroom} if isinstance(headroom,list) else {'return_value':headroom})), \
                    patch.object(sys, 'argv', argv), patch.object(Path, 'open', tracked_open), \
                    patch.object(self.worker, 'report_generation_slot', side_effect=nullcontext), \
                    patch.object(self.worker, 'segments', return_value=texts), \
                    patch.object(self.worker.secrets, 'randbits', return_value=base_seed) as entropy, \
                    patch.object(self.worker.importlib.util, 'spec_from_file_location', return_value=SimpleNamespace(loader=SimpleNamespace(exec_module=lambda module: None))), \
                    patch.object(self.worker.importlib.util, 'module_from_spec', return_value=voice), \
                    patch.object(self.worker.importlib, 'import_module', return_value=SimpleNamespace(ModelHolder=whisper)), \
                    patch.object(self.worker.subprocess, 'run', side_effect=encode), patch.object(builtins, 'print'):
                self.worker.main()
            events.entropy_calls = entropy.call_count
            events.tts_loads = voice.load_model.call_count
            self.assertIsNone(whisper.model)
            return events
        finally:
            for stream in handles: stream.close()

    def test_tempo_metadata_uses_actual_output_samples_and_bounds_last_cue(self):
        # atempo does not produce exactly input_samples / tempo. Keeping that
        # estimate made valid long recordings fail the video fragment gate.
        self.queue_voice('dmitrii')
        texts = ['Первая готовая фраза.', 'Вторая готовая фраза.']
        with patch.dict(self.worker.voice_tempo.TEMPO, {'dmitrii': 1.2}), \
                patch.object(self.worker.voice_tempo, 'stretch', side_effect=lambda audio, *args: type(audio)(7)):
            self.run_worker(texts, texts, 100, cue_end=1)
        ready = self.read('ready.json')
        self.assertEqual(ready['seconds'], 1.8)  # 7 + 4 gap + 7 samples at 10 Hz
        self.assertEqual([s['seconds'] for s in ready['segments']], [.7, .7])
        self.assertEqual([s['cues'][0]['end'] for s in ready['segments']], [.7, .7])
        raw = json.loads(next(self.cache.glob('0-*.json')).read_text())
        self.assertEqual(raw['seconds'], 1)
        self.assertEqual(raw['cues'][0]['end'], 1)

    def test_reuse_models_loads_each_model_once_for_all_verified_fragments(self):
        texts = ['Первая готовая фраза.', 'Вторая готовая фраза.', 'Третья готовая фраза.']
        events = self.run_worker(texts, texts, 100, reuse=True)
        self.assertEqual((events.tts_loads, events.asr_loads), (1, 1))
        self.assertEqual(len(events.prompts), 3)
        self.assertTrue((self.cache/'ready.json').exists())

    def test_reuse_models_falls_back_to_low_memory_when_headroom_is_missing(self):
        texts = ['Первая готовая фраза.', 'Вторая готовая фраза.']
        events = self.run_worker(texts, texts, 100, reuse=True, headroom=False)
        self.assertEqual((events.tts_loads, events.asr_loads), (2, 2))
        self.assertTrue((self.cache/'ready.json').exists())

    def test_low_memory_mode_still_unloads_both_models_per_fragment(self):
        texts = ['Первая готовая фраза.', 'Вторая готовая фраза.']
        events = self.run_worker(texts, texts, 100, low_memory=True)
        self.assertEqual((events.tts_loads, events.asr_loads), (2, 2))

    def test_memory_pressure_during_chapter_releases_models_and_continues(self):
        texts = ['Первая готовая фраза.', 'Вторая готовая фраза.', 'Третья готовая фраза.']
        events = self.run_worker(texts, texts, 100, reuse=True, headroom=[True,True,False])
        self.assertEqual((events.tts_loads, events.asr_loads), (3, 3))
        self.assertEqual(self.read('generation.json')['performance']['mode'], 'low-fallback')
        self.assertTrue((self.cache/'ready.json').exists())

    def test_memory_reuse_is_disabled_if_telemetry_is_missing_or_memory_low(self):
        for total,pressure,expected in [(36*1024**3, 'System-wide memory free percentage: 55%', True),
                                       (36*1024**3, 'System-wide memory free percentage: 15%', False),
                                       (16*1024**3, 'System-wide memory free percentage: 90%', False),
                                       (36*1024**3, 'unknown', False)]:
            with self.subTest(total=total,pressure=pressure), patch.object(self.worker.sys,'platform','darwin'), \
                    patch.object(self.worker.subprocess,'run',side_effect=[SimpleNamespace(stdout=str(total)), SimpleNamespace(stdout=pressure)]):
                self.assertEqual(self.worker.model_memory_available(),expected)
        with patch.object(self.worker.sys,'platform','darwin'), patch.object(self.worker.subprocess,'run',side_effect=OSError()):
            self.assertFalse(self.worker.model_memory_available())

    def test_finish_nearest_report_before_spreading_work_across_every_report(self):
        jobs=[{'id':'full-report-cycle-a','hash':'a'*64,'text':'а'*100,'section':'full-report'},
              {'id':'full-report-cycle-z','hash':'b'*64,'text':'б'*20,'section':'full-report'},
              {'id':'number-1','hash':'c'*64,'text':'в'*10,'section':'numbers'}]
        movies=self.queue.parent/'report-video';movies.mkdir()
        for key,items in [('long',[jobs[0]]),('near',[jobs[1]])]:
            target=movies/key;target.mkdir()
            (target/'job.json').write_text(json.dumps({'report':{'narration':items}}))
        self.assertEqual([x['hash'] for x in self.worker.ordered_jobs(self.queue,jobs)],['b'*64,'a'*64,'c'*64])
        # A newly bought report's overview is still delivered promptly.
        intro={'id':'full-report-summary','hash':'d'*64,'text':'Обзор','section':'full-report'}
        self.assertEqual(self.worker.ordered_jobs(self.queue,[*jobs,intro])[0],intro)

    def test_report_priority_counts_missing_audio_even_when_its_ready_marker_exists(self):
        jobs=[{'id':'full-report-cycle-z','hash':'a'*64,'text':'а'*20,'section':'full-report'},
              {'id':'full-report-cycle-a','hash':'b'*64,'text':'б'*50,'section':'full-report'}]
        hidden={'hash':'e'*64,'text':'д'*500}
        cache=self.queue/'clips'/hidden['hash'];cache.mkdir()
        (cache/'ready.json').write_text(json.dumps({'hash':hidden['hash']}))
        movies=self.queue.parent/'report-video';movies.mkdir()
        for key,items in [('missing',[jobs[0],hidden]),('near',[jobs[1]])]:
            target=movies/key;target.mkdir()
            (target/'job.json').write_text(json.dumps({'report':{'narration':items}}))
        self.assertEqual(self.worker.ordered_jobs(self.queue,jobs)[0]['hash'],'b'*64)

    def test_manual_retry_uses_new_cycle_and_reuses_verified_segment(self):
        texts = ['Первая фраза готова.', 'Действие, решительность и личные границы.']
        first = self.run_worker(texts, [texts[0]] + ['Совсем другое.'] * 3, 1000)
        self.assertEqual(first.seeds, [1000, 1013, 1114, 1215])
        self.assertEqual(self.read('generation.json')['cycle'], 1)
        self.assertEqual(self.read('generation.json')['status'], 'failed')
        self.assertFalse((self.cache / 'ready.json').exists())
        verified = next(self.cache.glob('0-*.json'))
        prior_bytes = verified.read_bytes()
        prior_audio = verified.with_suffix('.wav').read_bytes()
        # This is the state transition used by the authorized report retry:
        # remove only the failure marker; never erase successful chunk files.
        (self.cache / 'failed.json').unlink()
        second = self.run_worker(texts, [texts[1]], 5000)
        self.assertEqual(second.seeds, [5013])
        self.assertEqual(second.texts, [texts[1]])
        self.assertEqual(second.reads, [verified.with_suffix('.wav')])
        self.assertEqual(verified.read_bytes(), prior_bytes)
        self.assertEqual(verified.with_suffix('.wav').read_bytes(), prior_audio)
        current = self.read('generation.json')
        self.assertEqual((current['cycle'], current['base_seed'], current['status']), (2, 5000, 'ready'))
        self.assertEqual(current['history'][0]['base_seed'], 1000)
        self.assertEqual(current['reused_segments'][0]['generation']['cycle'], 1)
        self.assertEqual(self.read('ready.json')['segments'][1]['generation'],
            {'cycle': 2, 'base_seed': 5000, 'seed': 5013, 'attempt': 1})
        self.assertEqual(stat.S_IMODE((self.cache / 'generation.json').stat().st_mode), 0o600)
        # A third scan leaves a validated complete clip and its diagnostics alone.
        prior_generation = (self.cache / 'generation.json').read_bytes()
        third = self.run_worker(texts, [], 9000, retry=True)
        self.assertEqual(third.seeds, [])
        self.assertEqual(third.entropy_calls, 0)
        self.assertEqual((self.cache / 'generation.json').read_bytes(), prior_generation)

    def test_best_failed_attempt_seed_is_preserved_in_review_sidecar(self):
        text = 'Действие, решительность и личные границы.'
        self.run_worker([text], ['Действие, решительности и личные границы.', 'Совсем другое.', 'Нет.'], 70)
        diagnostic = self.read('review-1.json')
        self.assertEqual(diagnostic['generation'], {'cycle': 1, 'base_seed': 70, 'seed': 70, 'attempt': 1})
        self.assertAlmostEqual(diagnostic['difference'], .2)
        current = self.read('generation.json')
        self.assertEqual([attempt['seed'] for attempt in current['attempts']], [70, 171, 272])
        self.assertFalse((self.cache / 'ready.json').exists())
        self.assertIn('20.0%', self.read('failed.json')['error'])

    def test_failed_worker_waits_then_retries_without_losing_cached_segment(self):
        texts=['Готовая часть.', 'Действие, решительность и личные границы.']
        self.run_worker(texts,[texts[0]]+['Совсем другое.']*3,100,automatic=True)
        self.assertTrue((self.cache/'failed.json').exists())
        self.assertEqual(self.read('automatic-retry.json')['used'],0)
        waiting=self.run_worker(texts,[],200,automatic=True)
        self.assertEqual(waiting.texts,[])
        after=self.read('automatic-retry.json')['after']
        with patch.object(self.worker.time,'time',return_value=after+1):
            resumed=self.run_worker(texts,[texts[1]],300,automatic=True)
        self.assertEqual(resumed.texts,[texts[1]])
        self.assertEqual(len(resumed.reads),1)
        self.assertTrue((self.cache/'ready.json').exists())
        self.assertFalse((self.cache/'failed.json').exists())
        self.assertFalse((self.cache/'automatic-retry.json').exists())

    def test_automatic_retry_survives_restart_and_continues_with_backoff(self):
        with patch.object(self.worker.time,'time',return_value=1000):
            self.worker.schedule_automatic_retry(self.cache)
        self.assertFalse(self.worker.automatic_retry_due(self.cache,1299))
        self.assertTrue(self.worker.automatic_retry_due(self.cache,1300))
        delays=[]
        for cycle in range(8):
            now=self.read('automatic-retry.json')['after']
            with patch.object(self.worker.time,'time',return_value=now):
                self.worker.reserve_automatic_retry(self.cache)
                self.worker.schedule_automatic_retry(self.cache)
            delays.append(self.read('automatic-retry.json')['after']-now)
        self.assertEqual(self.read('automatic-retry.json')['used'],8)
        self.assertEqual(delays,sorted(delays))
        self.assertLessEqual(max(delays),6*3600)
        after=self.read('automatic-retry.json')['after']
        self.assertFalse(self.worker.automatic_retry_due(self.cache,after-1))
        self.assertTrue(self.worker.automatic_retry_due(self.cache,after))
        self.assertEqual(stat.S_IMODE((self.cache/'automatic-retry.json').stat().st_mode),0o600)
    def test_old_unrequested_failure_is_not_automatically_retried(self):
        (self.cache/'failed.json').write_text('{}')
        self.assertFalse(self.worker.automatic_retry_due(self.cache,100000))

    def test_missing_library_audio_is_reassembled_from_verified_chunks(self):
        path=self.queue/'jobs'/(self.key+'.json');job=json.loads(path.read_text())
        job['id']='number-1';path.write_text(json.dumps(job))
        texts=['Тестовая запись.']
        self.run_worker(texts,texts,100)
        (self.cache/'audio.m4a').unlink()
        resumed=self.run_worker(texts,[],200)
        self.assertFalse(resumed.texts)
        self.assertEqual(len(resumed.reads),1)
        self.assertTrue((self.cache/'audio.m4a').is_file())

    def test_seed_collision_is_changed_and_history_is_bounded(self):
        with patch.object(self.worker.secrets, 'randbits', return_value=2**32-1):
            first = self.worker.begin_generation_cycle(self.cache)
            second = self.worker.begin_generation_cycle(self.cache)
        self.assertNotEqual(first['base_seed'], second['base_seed'])
        self.assertEqual(second['base_seed'], 0)
        # Saved base seed and indices reproduce every individual attempt.
        self.assertEqual(self.worker.generation_seed(first, 1, 2), 214)
        with patch.object(self.worker.secrets, 'randbits', side_effect=range(30)):
            for _ in range(30): self.worker.begin_generation_cycle(self.cache)
        current = self.read('generation.json')
        self.assertEqual(current['cycle'], 32)
        self.assertEqual(len(current['history']), 8)
        self.assertEqual(current['history'][0]['cycle'], 24)

    def test_legacy_verified_chunk_without_seed_metadata_is_reused(self):
        text = 'Тестовая фраза.'
        self.run_worker([text], [text], 100)
        verified = next(self.cache.glob('0-*.json'))
        check = json.loads(verified.read_text()); del check['generation']
        verified.write_text(json.dumps(check), encoding='utf-8')
        for name in ('ready.json', 'audio.m4a', 'generation.json'):
            (self.cache / name).unlink()
        events = self.run_worker([text], [], 200)
        self.assertEqual(events.seeds, [])
        self.assertEqual(events.reads, [verified.with_suffix('.wav')])
        self.assertEqual(self.read('ready.json')['segments'], [check])
        self.assertIsNone(self.read('generation.json')['reused_segments'][0]['generation'])

    def test_asr_exception_keeps_attempt_seed_without_publishing_audio(self):
        self.run_worker(['Тестовая фраза.'], [RuntimeError('synthetic ASR failure')], 333)
        current = self.read('generation.json')
        self.assertEqual(current['status'], 'failed')
        self.assertEqual(current['attempts'], [{'segment': 1, 'attempt': 1, 'seed': 333, 'status': 'synthesizing'}])
        self.assertFalse((self.cache / 'ready.json').exists())
        self.assertFalse((self.cache / 'working.json').exists())

    def test_whisper_model_is_resolved_offline_before_synthesis(self):
        snapshot = self.root / 'whisper-snapshot'
        snapshot.mkdir()
        (snapshot / 'config.json').write_text('{}')
        (snapshot / 'weights.safetensors').write_bytes(b'synthetic weights')
        download = Mock(return_value=str(snapshot))
        with patch.dict(sys.modules, {'huggingface_hub': SimpleNamespace(snapshot_download=download)}):
            resolved = self.worker.local_whisper_model('synthetic-whisper')
        self.assertEqual(resolved, str(snapshot))
        download.assert_called_once_with(repo_id='synthetic-whisper', local_files_only=True)
        (snapshot / 'weights.safetensors').unlink()
        with patch.dict(sys.modules, {'huggingface_hub': SimpleNamespace(snapshot_download=download)}):
            with self.assertRaises(FileNotFoundError):
                self.worker.local_whisper_model('synthetic-whisper')

    def test_new_job_uses_dmitrii_voice(self):
        events = self.run_worker(['Тестовая фраза.'], ['Тестовая фраза.'], 10)
        self.assertEqual(events.references, [('dmitrii_ref.wav', 'Фраза Дмитрия.')])
        # The settings chosen for this voice in helper-voice: --clean --temperature 0.75.
        self.assertEqual(events.temperatures, [.75])
        self.assertEqual(events.processing, ['highpass', 'gate', 'soft_edges', 'loudness'])
        self.assertEqual(self.read('ready.json')['profile'], 'numerom-dmitrii-v2-clean')

    def test_job_queued_before_switch_keeps_helper_voice_and_its_chunks(self):
        self.queue_voice('helper-male')
        text = 'Тестовая фраза.'
        # A chunk verified before the switch keys on the legacy profile and Helper reference.
        reference = hashlib.sha256(b'synthetic Helper reference').hexdigest()
        chunk = hashlib.sha256(json.dumps([text, 'numerom-helper-male-project-v1', self.worker.MODEL, reference]).encode()).hexdigest()[:16]
        (self.cache / f'0-{chunk}.wav').write_bytes(b'synthetic PCM')
        (self.cache / f'0-{chunk}.json').write_text(json.dumps({'text': text, 'difference': 0}), encoding='utf-8')
        events = self.run_worker([text], [], 20)
        self.assertEqual(events.seeds, [])
        self.assertEqual(events.reads, [self.cache / f'0-{chunk}.wav'])
        self.assertEqual(self.read('ready.json')['profile'], 'numerom-helper-male-project-v1')
        (self.cache / 'ready.json').unlink()
        (self.cache / f'0-{chunk}.wav').unlink()
        events = self.run_worker([text], [text], 30)
        self.assertEqual(events.references, [('helper_male_ref.wav', 'Фраза Helper.')])
        self.assertEqual((events.temperatures, events.processing), ([.65], ['polish']))

    def test_list_that_loses_an_item_is_read_sentence_by_sentence(self):
        text = 'Ряд один, позиция один: буква. Ряд один, позиция два: буква. Ряд один, позиция три: буква.'
        lost = 'Ряд один, позиция один: буква. Ряд один, позиция три: буква.'
        pieces = ['Ряд один, позиция один: буква.', 'Ряд один, позиция два: буква.', 'Ряд один, позиция три: буква.']
        events = self.run_worker([text], [lost] * 3 + pieces, 50)
        self.assertEqual(events.texts, [text] * 3 + pieces)
        # Sentence seeds never repeat the three whole-segment seeds.
        self.assertEqual(len(set(events.seeds)), 6)
        ready = self.read('ready.json')
        self.assertEqual(ready['segments'][0]['difference'], 0)
        self.assertEqual(ready['segments'][0]['generation']['attempt'], 'sentences')
        self.assertFalse((self.cache / 'failed.json').exists())

    def test_sentence_split_keeps_every_word_once(self):
        text = ('Каждый ряд — суммы. Ряд один, позиция один: дэ ; далее четыре. Ряд один, позиция два: эм ; далее четыре. '
                'Ряд один, позиция три: и ; далее девять. Итог.')
        pieces = self.worker.sentences(text)
        self.assertEqual(' '.join(pieces), text)
        self.assertEqual(pieces[1], 'Ряд один, позиция один: дэ ; далее четыре.')
        self.assertEqual(pieces[-1], 'Ряд один, позиция три: и ; далее девять. Итог.')

    def test_sentence_cues_stay_inside_their_own_sentence(self):
        text = 'Ряд один, позиция один: буква. Ряд один, позиция два: буква. Ряд один, позиция три: буква.'
        lost = 'Ряд один, позиция один: буква. Ряд один, позиция три: буква.'
        pieces = ['Ряд один, позиция один: буква.', 'Ряд один, позиция два: буква.', 'Ряд один, позиция три: буква.']
        # Each sentence lasts 1 s; Whisper reports 1.6 s, which would overlap the next sentence.
        self.run_worker([text], [lost] * 3 + pieces, 70, cue_end=1.6)
        segment = self.read('ready.json')['segments'][0]
        cues = segment['cues']
        self.assertEqual(len(cues), 3)
        for previous, cue in zip(cues, cues[1:]):
            self.assertLessEqual(previous['end'], cue['start'])
        self.assertLessEqual(cues[-1]['end'], segment['seconds'])

    def test_sentence_fallback_that_still_loses_an_item_fails(self):
        text = 'Ряд один, позиция один: буква. Ряд один, позиция два: буква.'
        lost = 'Ряд один, позиция один: буква.'
        self.run_worker([text], [lost] * 3 + [lost, 'Ряд один.'] * 3, 60)
        self.assertFalse((self.cache / 'ready.json').exists())
        self.assertIn('Segment 1', self.read('failed.json')['error'])

    def test_unknown_voice_is_not_synthesized(self):
        self.queue_voice('somebody-else')
        events = self.run_worker(['Тестовая фраза.'], [], 40)
        self.assertEqual(events.seeds, [])
        self.assertFalse((self.cache / 'ready.json').exists())
        self.assertFalse((self.cache / 'failed.json').exists())

    def test_selected_conversation_voice_uses_embedding_and_no_denoising(self):
        self.queue_voice('dmitrii-conversation-v1')
        path=self.queue/'jobs'/(self.key+'.json');job=json.loads(path.read_text())
        job['pronunciation']=self.worker.russian_pronunciation.VERSION;path.write_text(json.dumps(job))
        ref = self.helper / 'voice/dmitrii_ref.wav'
        with patch.object(self.worker,'reference',return_value=(ref,None,'selected-reference',
                'dmitrii-speaker-identity-e8bbe873-tempo120-v1',.85,None)), \
                patch.object(self.worker.russian_pronunciation,'apply_adapter') as adapter, \
                patch.object(self.worker.russian_pronunciation,'prepare',return_value='Жива́я консульта́ция.') as prepare:
            events = self.run_worker(['Живая консультация.'], ['Живая консультация.'], 41)
        adapter.assert_called_once();prepare.assert_called_once_with('Живая консультация.')
        self.assertEqual(events.texts,['Жива́я консульта́ция.'])
        self.assertEqual(events.references, [('dmitrii_ref.wav',None)])
        self.assertEqual(events.temperatures,[.85])
        self.assertEqual(events.processing,['loudness'])
        self.assertEqual(self.read('ready.json')['profile'],'dmitrii-speaker-identity-e8bbe873-tempo120-v1')

    def test_obsolete_pronunciation_job_is_preserved_without_generating(self):
        self.queue_voice('dmitrii-conversation-v1')
        path=self.queue/'jobs'/(self.key+'.json');before=path.read_bytes()
        events=self.run_worker(['Живая консультация.'],[],41)
        self.assertEqual(events.seeds,[])
        self.assertEqual(path.read_bytes(),before)
        self.assertFalse((self.cache/'ready.json').exists())

    def test_spoken_route_is_a_list_and_preserves_master_number(self):
        self.assertEqual(self.worker.spoken('Вертикаль 4–5–6. Число 22.'),'Вертикаль 4, 5, 6. Число 22.')

    def test_all_paid_chapters_precede_bulk_library_refresh(self):
        jobs=[{'id':'soul','section':'numbers'},{'id':'theory-0','section':'theory'},
              {'id':'full-report-profile-phone','section':'full-report'},
              {'id':'full-report-summary','section':'full-report'},
              {'id':'full-report-vedic-yantra','section':'full-report'}]
        self.assertEqual([j['id'] for j in sorted(jobs,key=self.worker.job_priority)][:3],
            ['full-report-summary','full-report-profile-phone','full-report-vedic-yantra'])

    def test_lexicon_is_only_terms_and_does_not_weaken_numeric_gate(self):
        for term in ('Джанма-анк', 'Атма-анк', 'Бхагья-анк', 'Нама-анк', 'Шакти-анк'):
            self.assertEqual(self.worker.LEXICON.count(term), 1)
        self.assertFalse(re.search(r'\d', self.worker.LEXICON))
        text = 'Итог расчёта 8.'
        events = self.run_worker([text], ['Итог расчёта 9.'] * 3, 400)
        self.assertEqual(len(events.seeds), 3)
        self.assertTrue(all(prompt == self.worker.LEXICON for prompt in events.prompts))
        self.assertTrue(all(text not in prompt for prompt in events.prompts))
        self.assertFalse((self.cache / 'ready.json').exists())
        self.assertIn('33.3%', self.read('failed.json')['error'])



class VoiceTempoTests(unittest.TestCase):
    def test_dmitrii_recordings_are_faster_with_matching_cues(self):
        import voice_tempo
        self.assertEqual(voice_tempo.TEMPO['dmitrii'], 1.2)
        self.assertEqual(voice_tempo.TEMPO['dmitrii-conversation-v1'], 1.2)
        check = {'seconds': 6.0, 'cues': [{'start': 1.2, 'end': 2.4, 'text': 'слово'}], 'text': 'Фраза.'}
        faster = voice_tempo.faster(check, 1.2)
        self.assertAlmostEqual(faster['seconds'], 5.0)
        self.assertEqual((faster['cues'][0]['start'], faster['cues'][0]['end']), (1.0, 2.0))
        self.assertIs(voice_tempo.faster(check, 1), check)

    def test_stretch_keeps_pitch_and_shortens_audio(self):
        try:
            import numpy, soundfile, voice_tempo
        except ImportError:
            self.skipTest('soundfile lives in the voice environment')
        if not voice_tempo.ffmpeg()[0].is_file():
            self.skipTest('Remotion FFmpeg is not installed')
        sr = 24000
        tone = numpy.sin(2 * numpy.pi * 220 * numpy.arange(sr * 2) / sr).astype(numpy.float32) * .3
        fast = voice_tempo.stretch(tone, sr, 1.2, soundfile)
        self.assertAlmostEqual(len(fast) / sr, 2 / 1.2, delta=.05)
        spectrum = numpy.abs(numpy.fft.rfft(fast[sr // 4: sr // 4 + sr // 2]))
        self.assertAlmostEqual(numpy.argmax(spectrum) * 2, 220, delta=6)


if __name__ == '__main__':
    unittest.main()
