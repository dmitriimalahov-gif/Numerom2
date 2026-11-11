"""Queue recovery and commit gates, without Ollama, Mongo, browsers or encoders."""
import asyncio
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(ROOT / 'scripts'))
# Loading the command must not read a developer's real environment in a test.
with patch('dotenv.load_dotenv', return_value=False):
    SPEC = importlib.util.spec_from_file_location('numerom_report_media_worker_tests', ROOT / 'scripts/generate-report-media.py')
    worker = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(worker)

from services.report_files import digest, folder, read_json, write_json
from services.report_video import ReportVideo
from report_generation_slot import report_generation_slot
import numerom_services


class FakeProcess:
    pid = 987654

    def __init__(self, code=0, lines=()):
        self.code, self.stdout = code, iter(lines)
        self.wait = Mock(return_value=code)
        self.poll = Mock(return_value=code)


class WorkerCase(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.report = {'title': 'Личный разбор', 'narration': [{'id': 'intro', 'hash': 'b' * 64}],
                       'interpretation': {'provider': 'ollama', 'version': worker.IVERSION}}

    def job(self, kind='video'):
        version = worker.VVERSION if kind == 'video' else worker.IVERSION
        key = digest(version, self.report)
        target = folder(self.root, key)
        job = {'key': key, 'version': version, 'report': self.report}
        write_json(target / 'job.json', job)
        return target, job

    def commit_video(self, target, content=b'verified synthetic MP4'):
        (target / 'report.mp4').write_bytes(content)
        write_json(target / 'ready.json', {'key': target.name, 'bytes': len(content), 'seconds': 5,
            'sha256': hashlib.sha256(content).hexdigest(), 'chapters': []})

    def service(self, ready=True):
        voice = SimpleNamespace(state=Mock(return_value={'status': 'ready' if ready else 'missing'}))
        return ReportVideo(None, root=self.root, narration=voice, reports=object())

    def main(self, kind, **patches):
        # The CLI normally holds this lock until process exit. Close it explicitly
        # because several CLI invocations share the test process.
        handles, original_open = [], Path.open
        def tracked_open(path, *args, **kwargs):
            stream = original_open(path, *args, **kwargs)
            if path.name == 'worker.lock':
                handles.append(stream)
            return stream
        with patch.object(worker, 'MOVIES' if kind == 'video' else 'INSIGHTS', self.root), \
                patch.object(sys, 'argv', ['generate-report-media.py', '--kind', kind, '--limit', '1']), \
                patch.object(worker, 'report_generation_slot', side_effect=lambda: report_generation_slot(self.root / 'runtime/generation.lock')), \
                patch.object(Path, 'open', tracked_open), \
                patch('builtins.print') as output:
            contexts = []
            try:
                for name, replacement in patches.items():
                    context = patch.object(worker, name, replacement)
                    context.start(); contexts.append(context)
                worker.main()
            finally:
                for context in reversed(contexts):
                    context.stop()
                for stream in handles:
                    stream.close()
        return output


class QueueRecoveryTests(WorkerCase):
    def test_corrupt_ready_movie_is_repaired_instead_of_skipped(self):
        target, job = self.job()
        self.commit_video(target)
        (target / 'report.mp4').write_bytes(b'changed synthetic MP4')
        service = self.service()
        with patch.object(worker, 'ReportVideo', return_value=service):
            self.assertFalse(worker.completed('video', target, job))
        write_json(target / 'failed.json', {'attempts': 1, 'retry_at': 0})
        renderer = Mock(side_effect=lambda target, report: self.commit_video(target))
        output = self.main('video', ReportVideo=Mock(return_value=service), render=renderer)
        renderer.assert_called_once_with(target, self.report)
        self.assertEqual(service.state(self.report)['status'], 'ready')
        self.assertFalse((target / 'failed.json').exists())
        self.assertIn(('READY', 'video', target.name), [call.args for call in output.call_args_list])

    def test_valid_ready_movie_never_renders_again(self):
        target, _ = self.job(); self.commit_video(target)
        renderer = Mock()
        self.main('video', ReportVideo=Mock(return_value=self.service()), render=renderer)
        renderer.assert_not_called()

    def test_renderer_failure_records_backoff_and_never_announces_ready(self):
        target, _ = self.job()
        renderer = Mock(side_effect=RuntimeError('synthetic encoder failure'))
        output = self.main('video', ReportVideo=Mock(return_value=self.service()), render=renderer)
        self.assertFalse((target / 'ready.json').exists())
        failure = read_json(target / 'failed.json')
        self.assertEqual(failure['attempts'], 1)
        self.assertAlmostEqual(failure['retry_at'] - failure['at'], 300, delta=1)
        self.assertTrue(failure['error'].startswith('RuntimeError:'))
        self.assertNotIn('READY', [call.args[0] for call in output.call_args_list])

    def test_incomplete_narration_is_not_sent_to_renderer(self):
        self.job(); renderer = Mock()
        self.main('video', ReportVideo=Mock(return_value=self.service(ready=False)), render=renderer)
        renderer.assert_not_called()
        self.assertFalse((self.root / 'runtime/generation.lock').exists())

    def test_insights_and_video_hold_shared_slot_only_during_job(self):
        for kind in ('insights', 'video'):
            with self.subTest(kind=kind):
                self.job(kind)
                def check(*args):
                    descriptor = os.open(self.root / 'runtime/generation.lock', os.O_RDWR)
                    try:
                        with self.assertRaises(BlockingIOError):
                            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    finally:
                        os.close(descriptor)
                action = AsyncMock(side_effect=check) if kind == 'insights' else Mock(side_effect=check)
                self.main(kind, ReportVideo=Mock(return_value=self.service()),
                          **{'process_insight' if kind == 'insights' else 'render': action})
                action.assert_called_once()
                descriptor = os.open(self.root / 'runtime/generation.lock', os.O_RDWR)
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                finally:
                    os.close(descriptor)

    def test_retry_delay_is_respected(self):
        target, _ = self.job()
        for failure in [{'attempts': 3, 'retry_at': 10**12}, {'attempts': 1, 'retry_at': 10**12}]:
            with self.subTest(failure=failure):
                write_json(target / 'failed.json', failure)
                renderer = Mock()
                self.main('video', ReportVideo=Mock(return_value=self.service()), render=renderer)
                renderer.assert_not_called()

    def test_remote_text_transport_does_not_block_local_voice_slot(self):
        self.job('insights')
        def check(*args):
            path=self.root/'runtime/generation.lock';path.parent.mkdir(exist_ok=True)
            descriptor=os.open(path,os.O_RDWR|os.O_CREAT,0o600)
            try:fcntl.flock(descriptor,fcntl.LOCK_EX|fcntl.LOCK_NB)
            finally:os.close(descriptor)
        action=AsyncMock(side_effect=check)
        self.main('insights',process_insight=action,
                  transport_config=Mock(return_value=('http://127.0.0.1:1234','strata')))
        action.assert_awaited_once()

    def test_exhausted_legacy_job_resumes_without_user_retry(self):
        target, _ = self.job()
        write_json(target / 'failed.json', {'attempts': 3, 'retry_at': 0})
        renderer = Mock(side_effect=lambda target, report: self.commit_video(target))
        self.main('video', ReportVideo=Mock(return_value=self.service()), render=renderer)
        renderer.assert_called_once()
        self.assertFalse((target / 'failed.json').exists())

    def test_new_verified_work_resets_backoff_without_claiming_completion(self):
        target,_=self.job('insights')
        write_json(target/'failed.json',{'attempts':8,'retry_at':0})
        async def advance(*args):
            write_json(target/'checkpoint.json',{'parts':[{'fragment':{}}]})
            raise ValueError('next part needs repair')
        self.main('insights',process_insight=AsyncMock(side_effect=advance))
        state=read_json(target/'failed.json')
        self.assertTrue(state['made_progress']);self.assertEqual(state['attempts'],1)
        self.assertAlmostEqual(state['retry_at']-state['at'],30,delta=1)
        self.assertFalse((target/'ready.json').exists())

    def test_foreign_digest_and_wrong_version_are_not_executed(self):
        target, job = self.job(); renderer = Mock()
        for mutation in [{'report': {'title': 'different'}}, {'version': 'old'}, {'key': 'c' * 64}]:
            with self.subTest(mutation=mutation):
                write_json(target / 'job.json', {**job, **mutation})
                self.main('video', ReportVideo=Mock(return_value=self.service()), render=renderer)
                renderer.assert_not_called()

    def test_corrupt_insight_marker_is_reprocessed(self):
        target, job = self.job('insights')
        (target / 'ready.json').write_text('{incomplete', encoding='utf-8')
        action = AsyncMock()
        self.assertFalse(worker.completed('insights', target, job))
        self.main('insights', process_insight=action)
        action.assert_awaited_once_with(target, self.report)

    def test_insight_completion_requires_provider_key_and_validated_result(self):
        target, job = self.job('insights')
        saved = {'key': target.name, 'provider': 'ollama', 'result': {}, 'model': 'synthetic-model'}
        for invalid in [{**saved, 'key': 'c' * 64}, {**saved, 'provider': 'other'}, {}]:
            write_json(target / 'ready.json', invalid)
            with patch.object(worker, 'compose') as compose:
                self.assertFalse(worker.completed('insights', target, job))
                compose.assert_not_called()
        write_json(target / 'ready.json', saved)
        for error in [KeyError('field'), TypeError('type'), ValueError('invalid meaning')]:
            with patch.object(worker, 'compose', side_effect=error):
                self.assertFalse(worker.completed('insights', target, job))
        with patch.object(worker, 'compose', return_value=self.report) as compose:
            self.assertFalse(worker.completed('insights', target, job))
            write_json(target / 'downstream.json', {'key': 'c' * 64})
            self.assertFalse(worker.completed('insights', target, job))
            write_json(target / 'downstream.json', {'key': target.name})
            self.assertFalse(worker.completed('insights', target, job), 'Legacy video receipt must requeue dynamic rendering')
            write_json(target / 'downstream.json', {'key': target.name, 'video_version': 'old-renderer'})
            self.assertFalse(worker.completed('insights', target, job))
            write_json(target / 'downstream.json', {'key': target.name, 'video_version': worker.VVERSION})
            self.assertTrue(worker.completed('insights', target, job))
            compose.assert_called_with(self.report, {}, 'synthetic-model', transport_provider='ollama')


class InsightOrderingTests(WorkerCase):
    def setUp(self):
        super().setUp()
        self.target, _ = self.job('insights')
        self.result = {'key': self.target.name, 'provider': 'ollama', 'model': 'synthetic-model', 'result': {}}
        self.enriched = {**self.report, 'narration': [{'id': 'first'}, {'id': 'second'}]}

    def test_superseded_interpretation_is_never_rendered(self):
        # Reports composed with an older interpretation stay queued but no longer hold the shared slot.
        self.report['interpretation']['version'] = 'numerom-insights-v2'
        self.job('video')
        render = Mock()
        self.main('video', ReportVideo=Mock(return_value=self.service()), render=render)
        render.assert_not_called()

    def test_validation_precedes_queues_and_audio_precedes_video(self):
        events = []
        async def generate(report):
            self.assertEqual(report, self.report); events.append('generate'); return self.result
        def compose(*args, transport_provider='ollama'):
            events.append('validate'); return self.enriched
        def audio(item, scope, variant):
            self.assertEqual((scope, variant), ('full-report', 'paid-report'))
            events.append('audio:' + item['id'])
        def video(report):
            self.assertIs(report, self.enriched); events.append('video')
        with patch.object(worker, 'ReportInsights', return_value=SimpleNamespace(generate=generate)), \
                patch.object(worker, 'compose', side_effect=compose), \
                patch.object(worker, 'NarrationService', return_value=SimpleNamespace(enqueue=audio)), \
                patch.object(worker, 'ReportVideo', return_value=SimpleNamespace(enqueue=video)):
            asyncio.run(worker.process_insight(self.target, self.report))
        self.assertEqual(events, ['generate', 'validate', 'audio:first', 'audio:second', 'video'])
        self.assertEqual(read_json(self.target / 'ready.json'), self.result)
        self.assertEqual(read_json(self.target / 'downstream.json')['key'], self.target.name)
        self.assertEqual(read_json(self.target / 'downstream.json')['video_version'], worker.VVERSION)

    def test_invalid_generated_text_never_commits_or_enqueues(self):
        with patch.object(worker, 'ReportInsights', return_value=SimpleNamespace(generate=AsyncMock(return_value=self.result))), \
                patch.object(worker, 'compose', side_effect=ValueError('unsupported interpretation')), \
                patch.object(worker, 'NarrationService') as audio, patch.object(worker, 'ReportVideo') as video:
            with self.assertRaises(ValueError):
                asyncio.run(worker.process_insight(self.target, self.report))
        self.assertFalse((self.target / 'ready.json').exists())
        audio.assert_not_called(); video.assert_not_called()

    def test_queue_failure_does_not_mark_entire_job_complete(self):
        with patch.object(worker, 'ReportInsights', return_value=SimpleNamespace(generate=AsyncMock(return_value=self.result))), \
                patch.object(worker, 'compose', return_value=self.enriched), \
                patch.object(worker, 'NarrationService', return_value=SimpleNamespace(enqueue=Mock(side_effect=RuntimeError('queue full')))), \
                patch.object(worker, 'ReportVideo') as video:
            with self.assertRaises(RuntimeError):
                asyncio.run(worker.process_insight(self.target, self.report))
            self.assertFalse(worker.completed('insights', self.target, {'report': self.report}),
                             'A failed audio enqueue must remain retryable by the worker')
        video.assert_not_called()

    def test_video_queue_retry_reuses_committed_interpretation_without_inference(self):
        generate = AsyncMock(return_value=self.result)
        audio = Mock()
        video = Mock(side_effect=[RuntimeError('video queue unavailable'), 'synthetic-key'])
        with patch.object(worker, 'ReportInsights', return_value=SimpleNamespace(generate=generate)), \
                patch.object(worker, 'compose', return_value=self.enriched), \
                patch.object(worker, 'NarrationService', return_value=SimpleNamespace(enqueue=audio)), \
                patch.object(worker, 'ReportVideo', return_value=SimpleNamespace(enqueue=video)):
            with self.assertRaises(RuntimeError):
                asyncio.run(worker.process_insight(self.target, self.report))
            self.assertEqual(read_json(self.target / 'ready.json'), self.result)
            self.assertFalse((self.target / 'downstream.json').exists())
            self.assertFalse(worker.completed('insights', self.target, {'report': self.report}))
            asyncio.run(worker.process_insight(self.target, self.report))
            self.assertTrue(worker.completed('insights', self.target, {'report': self.report}))
        generate.assert_awaited_once_with(self.report)
        self.assertEqual(video.call_count, 2)
        self.assertEqual(audio.call_count, 4)
        self.assertEqual(read_json(self.target / 'ready.json'), self.result)

    def test_inference_failure_leaves_no_completion_marker(self):
        with patch.object(worker, 'ReportInsights', return_value=SimpleNamespace(generate=AsyncMock(side_effect=RuntimeError('model unavailable')))), \
                patch.object(worker, 'NarrationService') as audio, patch.object(worker, 'ReportVideo') as video:
            with self.assertRaises(RuntimeError):
                asyncio.run(worker.process_insight(self.target, self.report))
        self.assertFalse((self.target / 'ready.json').exists())
        self.assertFalse((self.target / 'downstream.json').exists())
        audio.assert_not_called(); video.assert_not_called()


class RenderValidationTests(WorkerCase):
    def setUp(self):
        super().setUp()
        self.target, _ = self.job()
        self.manifest = {'chapters': [
            {'id': 'intro', 'title': 'Итог', 'durationInFrames': worker.FPS * 2},
            {'id': 'square', 'title': 'Квадрат', 'durationInFrames': worker.FPS * 3}]}
        self.metadata = {'streams': [
            {'codec_type': 'video', 'codec_name': 'h264', 'width': 1280, 'height': 720},
            {'codec_type': 'audio', 'codec_name': 'aac'}], 'format': {'duration': '5.0'}}
        self.payload = b'synthetic bounded MP4 output'
        environment = patch.dict(os.environ, {'NUMEROM_VIDEO_RUNTIME': 'native'})
        environment.start(); self.addCleanup(environment.stop)

    def render(self, *, metadata=None, output='file', exitcode=0, probe_error=None, timed_out=False, ignores_term=False):
        process = FakeProcess(exitcode, ['diagnostic text\n', json.dumps({'progress': 48}) + '\n'])
        if ignores_term:
            process.poll.side_effect = [None, 0]
            def wait(*args, **kwargs):
                if kwargs.get('timeout') == 15:
                    raise subprocess.TimeoutExpired(['renderer'], 15)
                return 0
            process.wait.side_effect = wait
        deadline = Mock()
        def spawn(*args, **kwargs):
            self.spawned = (args, kwargs)
            path = self.target / 'report.pending.mp4'
            if output == 'file':
                path.write_bytes(self.payload)
            elif output == 'empty':
                path.touch()
            elif output == 'symlink':
                external = self.root / 'unrelated.mp4'; external.write_bytes(self.payload)
                path.symlink_to(external)
            return process
        def timer(seconds, callback):
            self.assertEqual(seconds, 6 * 3600)
            if timed_out:
                deadline.start.side_effect = callback
            return deadline
        probe = Mock(side_effect=probe_error, return_value=SimpleNamespace(stdout=json.dumps(metadata or self.metadata)))
        with patch.object(worker, 'build_manifest', return_value=self.manifest), \
                patch.object(worker, 'NarrationService'), patch.object(worker, 'node_path', return_value='/synthetic/node'), \
                patch.object(worker, 'probe_runtime', return_value=('/synthetic/ffprobe', None)), \
                patch.object(worker.subprocess, 'Popen', side_effect=spawn), \
                patch.object(worker.subprocess, 'run', probe), \
                patch.object(worker.threading, 'Timer', side_effect=timer), \
                patch.object(worker.signal, 'signal', return_value=signal.SIG_DFL) as signals, \
                patch.object(worker.os, 'killpg') as kill:
            try:
                worker.render(self.target, self.report)
            finally:
                deadline.cancel.assert_called_once()
                self.assertEqual(signals.call_args.args, (signal.SIGTERM, signal.SIG_DFL))
                if ignores_term:
                    self.assertEqual([call.args for call in kill.call_args_list], [
                        (process.pid, signal.SIGTERM), (process.pid, signal.SIGKILL)])
        return probe

    def assert_uncommitted(self):
        self.assertFalse((self.target / 'ready.json').exists())
        self.assertFalse((self.target / 'report.mp4').exists())

    def test_verified_video_commits_real_metrics_digest_and_chapter_offsets(self):
        probe = self.render()
        self.assertEqual((self.target / 'report.mp4').read_bytes(), self.payload)
        self.assertFalse((self.target / 'report.pending.mp4').exists())
        self.assertFalse((self.target / 'progress.json').exists())
        ready = read_json(self.target / 'ready.json')
        self.assertEqual((ready['key'], ready['bytes'], ready['seconds']), (self.target.name, len(self.payload), 5))
        self.assertEqual(ready['sha256'], hashlib.sha256(self.payload).hexdigest())
        self.assertEqual([(c['start_seconds'], c['duration_seconds']) for c in ready['chapters']], [(0, 2), (2, 3)])
        self.assertEqual(probe.call_args.kwargs['timeout'], 30)
        self.assertTrue(probe.call_args.kwargs['check'])

    def test_native_and_docker_pass_the_same_private_absolute_inputs(self):
        for runtime, script in [('native', 'render.mjs'), ('docker', 'render-docker.mjs')]:
            with self.subTest(runtime=runtime), patch.dict(os.environ, {'NUMEROM_VIDEO_RUNTIME': runtime}):
                self.render()
                command = self.spawned[0][0]
                self.assertEqual(command, ['/synthetic/node', str(ROOT / 'video' / script),
                    '--input', str(self.target / 'manifest.json'), '--output', str(self.target / 'report.pending.mp4')])
                self.assertTrue(self.spawned[1]['start_new_session'])
                self.assertNotIn('shell', self.spawned[1])
                (self.target / 'report.mp4').unlink()
                (self.target / 'ready.json').unlink()

    def test_absent_runtime_defaults_to_native_and_unknown_fails_before_work(self):
        with patch.dict(os.environ):
            os.environ.pop('NUMEROM_VIDEO_RUNTIME', None)
            self.assertEqual(worker.renderer_path(), ROOT / 'video/render.mjs')
        for runtime in ['', 'Docker', 'native ', 'unknown', '../../outside.mjs']:
            with self.subTest(runtime=runtime), patch.dict(os.environ, {'NUMEROM_VIDEO_RUNTIME': runtime}), \
                    patch.object(worker, 'build_manifest') as manifest, patch.object(worker.subprocess, 'Popen') as process:
                with self.assertRaisesRegex(RuntimeError, 'must be native or docker'):
                    worker.render(self.target, self.report)
                manifest.assert_not_called(); process.assert_not_called()
                self.assert_uncommitted()

    def test_absent_empty_oversized_output_and_nonzero_exit_never_commit(self):
        for kwargs in [{'output': 'absent'}, {'output': 'empty'}, {'exitcode': 1}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(RuntimeError):
                self.render(**kwargs)
            self.assert_uncommitted()
        with patch.object(worker, 'MAX_BYTES', 3), self.assertRaises(RuntimeError):
            self.render()
        self.assert_uncommitted()

    def test_invalid_codec_dimensions_audio_and_duration_never_commit(self):
        variants = []
        invalid = copy.deepcopy(self.metadata); invalid['streams'][0]['codec_name'] = 'vp9'; variants.append(invalid)
        invalid = copy.deepcopy(self.metadata); invalid['streams'][0]['width'] = 640; variants.append(invalid)
        invalid = copy.deepcopy(self.metadata); invalid['streams'] = invalid['streams'][:1]; variants.append(invalid)
        invalid = copy.deepcopy(self.metadata); invalid['streams'][1]['codec_name'] = 'opus'; variants.append(invalid)
        invalid = copy.deepcopy(self.metadata); invalid['format']['duration'] = '100'; variants.append(invalid)
        for metadata in variants:
            with self.subTest(metadata=metadata), self.assertRaises(RuntimeError):
                self.render(metadata=metadata)
            self.assert_uncommitted()

    def test_nonfinite_duration_cannot_pass_video_validation(self):
        metadata = copy.deepcopy(self.metadata); metadata['format']['duration'] = 'NaN'
        with self.assertRaises((ValueError, RuntimeError)):
            self.render(metadata=metadata)
        self.assert_uncommitted()

    def test_symlink_output_is_never_committed(self):
        with self.assertRaises((ValueError, RuntimeError)):
            self.render(output='symlink')
        self.assert_uncommitted()

    def test_probe_failure_or_timeout_never_commit(self):
        for error in [subprocess.CalledProcessError(1, ['ffprobe']), subprocess.TimeoutExpired(['ffprobe'], 30)]:
            with self.subTest(error=type(error).__name__), self.assertRaises(type(error)):
                self.render(probe_error=error)
            self.assert_uncommitted()

    def test_deadline_prevents_a_successful_exit_from_becoming_ready(self):
        with self.assertRaises(RuntimeError):
            self.render(timed_out=True)
        self.assert_uncommitted()

    def test_deadline_kills_renderer_that_ignores_term_without_waiting_for_stdout(self):
        with self.assertRaises(RuntimeError):
            self.render(timed_out=True, ignores_term=True)
        self.assert_uncommitted()


class ProbeRuntimeTests(unittest.TestCase):
    def test_bundled_macos_probe_uses_only_matching_private_libraries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            binary=root/'video/node_modules/@remotion/compositor-darwin-arm64/ffprobe'
            binary.parent.mkdir(parents=True);binary.write_text('fixture');binary.chmod(0o700)
            with patch.object(worker,'ROOT',root), patch.object(worker.shutil,'which',return_value=None), patch.object(worker.sys,'platform','darwin'), patch.object(worker.platform,'machine',return_value='arm64'):
                command, environment=worker.probe_runtime()
                self.assertEqual(command,str(binary))
                self.assertEqual(environment['DYLD_LIBRARY_PATH'],str(binary.parent))
                binary.unlink()
                with self.assertRaisesRegex(RuntimeError,'verified ffprobe'):
                    worker.probe_runtime()

    def test_system_probe_retains_default_environment(self):
        with patch.object(worker.shutil,'which',return_value='/verified/ffprobe'):
            self.assertEqual(worker.probe_runtime(),('/verified/ffprobe',None))


class VideoServiceConfigurationTests(unittest.TestCase):
    def test_video_service_uses_native_outside_protected_desktop(self):
        cases = [('darwin', Path.home() / 'Desktop/Numerom', 'docker'),
                 ('darwin', Path.home() / 'Library/Application Support/NumerOM/runtime', 'native'),
                 ('linux', Path('/srv/numerom'), 'native')]
        for platform, root, runtime in cases:
            with self.subTest(platform=platform, root=root), patch.object(numerom_services.sys, 'platform', platform), patch.object(numerom_services, 'ROOT', root):
                command = numerom_services.specifications()['report-video']
                plist = numerom_services.service_plist('report-video', command)
                environment = plist['EnvironmentVariables']
                self.assertEqual(environment['NUMEROM_VIDEO_RUNTIME'], runtime)
                self.assertEqual(plist['ProgramArguments'], command)
                self.assertTrue(plist['KeepAlive'])
                docker_path = '/Applications/Docker.app/Contents/Resources/bin'
                self.assertEqual(docker_path in environment['PATH'].split(':'), runtime == 'docker')
                self.assertEqual(environment['PATH'].split(':')[:len(numerom_services.PATH.split(':'))],
                                 numerom_services.PATH.split(':'))

    def test_other_service_environments_are_unchanged_on_both_platforms(self):
        for platform in ('darwin', 'linux'):
            with self.subTest(platform=platform), patch.object(numerom_services.sys, 'platform', platform):
                for name, command in numerom_services.specifications().items():
                    if name == 'report-video': continue
                    plist = numerom_services.service_plist(name, command)
                    self.assertEqual(plist['EnvironmentVariables'], {
                        'PATH': numerom_services.PATH, 'PYTHONUNBUFFERED': '1', 'LANG': 'en_US.UTF-8'})


if __name__ == '__main__':
    unittest.main()
