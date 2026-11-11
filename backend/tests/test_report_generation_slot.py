"""Real process locks and fake voice integration; no models or private artifacts."""
from contextlib import contextmanager
import builtins
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import weakref


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from report_generation_slot import report_generation_slot


class SlotTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.lock = self.root / 'runtime/report-generation.lock'

    def child(self):
        code = ('import sys; sys.path.insert(0, sys.argv[1]); '
                'from report_generation_slot import report_generation_slot\n'
                'with report_generation_slot(sys.argv[2]):\n'
                ' print("acquired", flush=True)\n'
                ' sys.stdin.readline()\n')
        process = subprocess.Popen([sys.executable, '-c', code, str(ROOT / 'scripts'), str(self.lock)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        def close():
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()
        self.addCleanup(close)
        return process

    def acquired(self, process):
        self.assertTrue(select.select([process.stdout], [], [], 5)[0], 'Child did not acquire the slot')
        self.assertEqual(process.stdout.readline().strip(), 'acquired')

    def test_separate_process_waits_for_current_job_to_finish(self):
        with report_generation_slot(self.lock):
            child = self.child()
            self.assertEqual(select.select([child.stdout], [], [], .2)[0], [])
            self.assertIsNone(child.poll())
        self.acquired(child)
        child.stdin.write('done\n'); child.stdin.flush()
        self.assertEqual(child.wait(timeout=5), 0)

    def test_process_exit_releases_the_slot_even_without_python_cleanup(self):
        child = self.child(); self.acquired(child)
        child.send_signal(signal.SIGKILL); child.wait(timeout=5)
        descriptor = os.open(self.lock, os.O_RDWR)
        try:
            # Nonblocking proves availability without risking a hung test.
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)

    def test_exception_closes_noninheritable_descriptor_and_preserves_lock_inode(self):
        with self.assertRaisesRegex(RuntimeError, 'synthetic'):
            with report_generation_slot(self.lock) as descriptor:
                self.assertFalse(os.get_inheritable(descriptor))
                self.assertEqual(stat.S_IMODE(os.fstat(descriptor).st_mode), 0o600)
                inode = os.fstat(descriptor).st_ino
                raise RuntimeError('synthetic failure')
        with self.assertRaises(OSError):
            os.fstat(descriptor)
        with report_generation_slot(self.lock) as next_descriptor:
            self.assertEqual(os.fstat(next_descriptor).st_ino, inode)
        self.assertEqual(stat.S_IMODE(self.lock.parent.stat().st_mode), 0o700)

    def test_existing_regular_lock_is_restricted_to_owner(self):
        self.lock.parent.mkdir(); self.lock.write_text(''); self.lock.chmod(0o666)
        with report_generation_slot(self.lock):
            self.assertEqual(stat.S_IMODE(self.lock.stat().st_mode), 0o600)

    def test_symlink_hardlink_and_fifo_cannot_be_used_as_lock_file(self):
        self.lock.parent.mkdir()
        target = self.root / 'other'; target.write_text('keep')
        for create in [lambda: self.lock.symlink_to(target), lambda: os.link(target, self.lock), lambda: os.mkfifo(self.lock)]:
            create()
            with self.assertRaises((OSError, ValueError)):
                with report_generation_slot(self.lock):
                    self.fail('Non-private file was accepted')
            self.lock.unlink()
        self.assertEqual(target.read_text(), 'keep')


class VoiceSlotTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        # The worker's text normalizer is irrelevant to scheduling. Avoid loading
        # its external voice environment or changing the real offline settings.
        with patch.dict(sys.modules, {'num2words': SimpleNamespace(num2words=lambda n, **kw: str(n))}), patch.dict(os.environ):
            spec = importlib.util.spec_from_file_location('numerom_voice_slot_tests', ROOT / 'scripts/generate-project-voices.py')
            self.worker = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.worker)
        # Synthetic samples cannot go through FFmpeg; the 1.2× tempo has its own tests.
        tempo = patch.dict(self.worker.voice_tempo.TEMPO, clear=True); tempo.start(); self.addCleanup(tempo.stop)
        self.helper = self.root / 'helper'; (self.helper / 'voice').mkdir(parents=True)
        for name in ('helper_male_ref', 'dmitrii_ref'):
            (self.helper / f'voice/{name}.wav').write_bytes(b'synthetic reference')
            (self.helper / f'voice/{name}.txt').write_text('Тестовая фраза.', encoding='utf-8')
        self.queue = self.root / 'backend/private/narration'
        (self.queue / 'jobs').mkdir(parents=True)
        self.whisper = SimpleNamespace(model=None, model_path=None)
        self.events, self.models = [], []

    def run_voice(self, count=1, failure=False, low_memory=False, reuse=False):
        for index in range(count):
            key = str(index + 1) * 64
            (self.queue / 'jobs' / (key + '.json')).write_text(json.dumps({
                'hash': key, 'id': 'full-report-summary-' + str(index), 'section': 'intro',
                'text': 'Тестовая фраза.'}), encoding='utf-8')
        class Samples:
            def __len__(self): return 10
            def astype(self, dtype): return self
        class Model:
            sample_rate = 10
            def generate(self, **kwargs): return [SimpleNamespace(audio=Samples())]
        def load_model(name):
            self.events.append('load')
            model = Model(); self.models.append(weakref.ref(model)); return model
        def transcribe(*args, **kwargs):
            self.whisper.model = object(); self.whisper.model_path = 'synthetic-whisper'
            if failure: raise RuntimeError('synthetic ASR failure')
            return {'text': 'Тестовая фраза.', 'segments': []}
        voice = SimpleNamespace(load_model=load_model,
            mx=SimpleNamespace(set_cache_limit=Mock(), random=SimpleNamespace(seed=Mock()),
                clear_cache=lambda: self.events.append('clear')),
            np=SimpleNamespace(concatenate=lambda arrays: Samples(), asarray=lambda array: array,
                float32='float32', zeros=lambda *args, **kwargs: Samples()),
            polish=lambda audio, sr: audio, to16k=lambda audio, sr: audio,
            highpass=lambda audio, sr: audio, gate=lambda audio, sr: audio,
            soft_edges=lambda audio, sr: audio, loudness=lambda audio: audio,
            words=lambda text: text.lower().split(), WHISPER='synthetic-whisper',
            mlx_whisper=SimpleNamespace(transcribe=transcribe),
            sf=SimpleNamespace(write=lambda path, *args: Path(path).write_bytes(b'synthetic PCM')))
        @contextmanager
        def slot():
            with report_generation_slot(self.root / 'runtime/generation.lock'):
                self.events.append('acquire')
                try:
                    yield
                finally:
                    self.assertIsNone(self.whisper.model)
                    self.assertIsNone(self.whisper.model_path)
                    self.assertTrue(all(ref() is None for ref in self.models), 'TTS model outlived its slot')
                    self.assertEqual(self.events[-1], 'clear')
                    self.events.append('release')
        def encode(command, **kwargs):
            self.assertEqual(command[0], '/usr/bin/afconvert')
            Path(command[-1]).write_bytes(b'synthetic AAC')
        handles, original_open = [], Path.open
        def tracked_open(path, *args, **kwargs):
            stream = original_open(path, *args, **kwargs)
            if path.name == 'worker.lock': handles.append(stream)
            return stream
        argv = ['generate-project-voices.py', '--limit', str(count)] + (['--low-memory'] if low_memory else [])
        if reuse:argv.append('--reuse-models')
        try:
            with patch.object(self.worker, 'ROOT', self.root), patch.object(self.worker, 'HELPER', self.helper), \
                    patch.object(sys, 'argv', argv), patch.object(Path, 'open', tracked_open), \
                    patch.object(self.worker, 'report_generation_slot', side_effect=slot), \
                    patch.object(self.worker, 'local_whisper_model', return_value=voice.WHISPER), \
                    patch.object(self.worker, 'model_memory_available', return_value=True), \
                    patch.object(self.worker, 'segments', return_value=['Тестовая фраза.']), \
                    patch.object(self.worker.importlib.util, 'spec_from_file_location', return_value=SimpleNamespace(loader=SimpleNamespace(exec_module=lambda module: None))), \
                    patch.object(self.worker.importlib.util, 'module_from_spec', return_value=voice), \
                    patch.object(self.worker.importlib, 'import_module', return_value=SimpleNamespace(ModelHolder=self.whisper)), \
                    patch.object(self.worker.subprocess, 'run', side_effect=encode), patch.object(builtins, 'print'):
                self.worker.main()
        finally:
            for stream in handles: stream.close()

    def test_each_chapter_releases_both_models_before_unlocking(self):
        self.run_voice(count=2)
        self.assertEqual([e for e in self.events if e in {'acquire', 'load', 'release'}],
                         ['acquire', 'load', 'release', 'acquire', 'load', 'release'])
        self.assertEqual(len(list((self.queue / 'clips').glob('*/ready.json'))), 2)

    def test_failed_recognition_also_releases_models_and_shared_slot(self):
        self.run_voice(failure=True, low_memory=True)
        self.assertEqual(self.events[-1], 'release')
        self.assertEqual(len(list((self.queue / 'clips').glob('*/failed.json'))), 1)
        self.assertEqual(list((self.queue / 'clips').glob('*/ready.json')), [])
        self.assertEqual(list((self.queue / 'clips').glob('*/working.json')), [])

    def test_reuse_mode_frees_both_models_before_each_shared_slot_release(self):
        self.run_voice(count=2,reuse=True)
        self.assertEqual(self.events.count('release'),2)
        self.assertEqual(len(list((self.queue/'clips').glob('*/ready.json'))),2)

    def test_reuse_mode_releases_models_on_recognition_failure(self):
        self.run_voice(failure=True,reuse=True)
        self.assertEqual(self.events[-1],'release')
        self.assertEqual(len(list((self.queue/'clips').glob('*/failed.json'))),1)

    def test_corrupt_ready_report_audio_is_regenerated(self):
        cache=self.queue/'clips'/('1'*64);cache.mkdir(parents=True)
        (cache/'ready.json').write_text('{corrupt',encoding='utf-8')
        self.run_voice()
        from domain.report_audio import ready_audio
        self.assertIsNotNone(ready_audio(cache,'1'*64))
        self.assertEqual(self.events.count('load'),1)

    def test_failed_held_report_audio_is_not_retried_implicitly(self):
        key='0'*64;cache=self.queue/'clips'/key;cache.mkdir(parents=True)
        marker={'error':'held rejected snapshot'}
        (cache/'failed.json').write_text(json.dumps(marker),encoding='utf-8')
        (self.queue/'jobs'/(key+'.json')).write_text(json.dumps({'hash':key,'id':'full-report-held',
            'section':'intro','text':'Запрещено повторять старый текст.'}),encoding='utf-8')
        self.run_voice()
        self.assertEqual(json.loads((cache/'failed.json').read_text()),marker)
        self.assertFalse((cache/'ready.json').exists())
        self.assertEqual(self.events.count('load'),1)


if __name__ == '__main__':
    unittest.main()
