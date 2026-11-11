"""Video capabilities, real media route and measured scene timing; no live Mongo."""
import asyncio
import hashlib
import math
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import httpx
from fastapi import FastAPI, HTTPException
from jose import jwt
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from auth import create_access_token, get_current_user
from domain.report_video import FPS, GAP, build_manifest, cue_segments
from public_gateway import _route, _valid_body
from routers.full_reports import create_full_reports_router
from routers.narration import create_narration_router
from services.full_reports import FullReports
from services.narration import narration_key, NarrationService
from services.report_insights import VERSION as INSIGHT_VERSION
from services.report_files import digest, folder, write_json
from services.report_video import ReportVideo, VERSION, video_key

class FakeVoice:
    def __init__(self, root):
        self.root, self.statuses = Path(root), {}
        self.retry_report = Mock(return_value=0)
    def state(self, item):
        return {'status': self.statuses.get(item['id'], 'missing')}
    def folder(self, key):
        return folder(self.root, key)
    def ready(self, item, seconds=2.75, segments=None):
        target = self.folder(item['hash']); target.mkdir(parents=True)
        audio = b'verified synthetic AAC ' + item['id'].encode()
        (target / 'audio.m4a').write_bytes(audio)
        write_json(target / 'ready.json', {'hash': item['hash'], 'bytes': len(audio),
            'sha256': hashlib.sha256(audio).hexdigest(), 'seconds': seconds,
            'segments': segments or [{'seconds': seconds, 'text': item['title']}]})
        self.statuses[item['id']] = 'ready'
        return target

def report_fixture():
    return {'version': 1, 'title': 'Личный разбор', 'birth_date': '12.03.1990', 'as_of_date': '2026-10-23',
        'interpretation': {'provider': 'ollama', 'version': INSIGHT_VERSION},
        'sections': [{'id': 'personal', 'title': 'Числа', 'values': [{'label': 'Число души', 'value': 3}]},
            {'id': 'square', 'title': 'Квадрат', 'values': []},
            {'id': 'square-lines', 'title': 'Линии', 'values': [
                {'label': 'Горизонталь 1–4–7', 'value': 3}, {'label': 'Вертикаль 1–2–3', 'value': 4}]}],
        'narration': [{'id': 'full-report-summary', 'hash': '1' * 64, 'title': 'Итог', 'text': 'Личный итог.', 'seconds': 999},
            {'id': 'full-report-square-lines-1', 'hash': '2' * 64, 'title': 'Линии', 'text': 'Линии квадрата.', 'seconds': 999}]}

class VideoAccessTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        secret = patch.dict(os.environ, {'SECRET_KEY': 'synthetic-report-video-test-key-' * 3})
        secret.start(); self.addCleanup(secret.stop)
        self.user = {'id': 'owner', 'auth_version': 2}
        self.order = {'_id': 'a' * 64, 'user_id': 'owner', 'state': 'paid', 'livemode': False,
                      'report': report_fixture(), 'analysis_status': 'ready'}
        async def find_user(query):
            return self.user if query == {'id': 'owner'} else ({'id': 'other'} if query == {'id': 'other'} else None)
        async def find_order(query):
            return self.order if all(self.order.get(key) == value for key, value in query.items()) else None
        self.db = SimpleNamespace(users=SimpleNamespace(find_one=AsyncMock(side_effect=find_user)),
            full_report_orders=SimpleNamespace(find_one=AsyncMock(side_effect=find_order)))
        self.config = SimpleNamespace(live=False)
        self.reports = FullReports(self.db, config=self.config, provider=object())
        # Keep actual FullReports.owned; isolate the generation pipeline and all disk writes.
        self.reports.materialize = AsyncMock(side_effect=lambda order: order)
        self.voice = FakeVoice(self.root / 'voice')
        self.service = ReportVideo(self.db, root=self.root / 'video', narration=self.voice,
            reports=self.reports, public_url='https://media.example.invalid')
        self.content = b'0123456789-video-bytes'
    def ready(self, seconds=42.25):
        key = self.service.enqueue(self.order['report']); target = folder(self.service.root, key)
        (target / 'report.mp4').write_bytes(self.content)
        write_json(target / 'ready.json', {'key': key, 'bytes': len(self.content), 'seconds': seconds,
            'sha256': hashlib.sha256(self.content).hexdigest(),
            'chapters': [{'id': 'intro', 'title': 'Итог', 'start_seconds': 0, 'duration_seconds': seconds}]})
        return target
    async def state(self):
        return await self.service.status('owner', self.order['_id'])
    async def token(self, download=False):
        return (await self.state())['download_url' if download else 'url'].rsplit('/', 1)[1]
    async def denied(self, operation, code):
        with self.assertRaises(HTTPException) as failure:
            await operation
        self.assertEqual(failure.exception.status_code, code)
    async def media(self, token, method='GET', headers=None):
        app = FastAPI(); app.include_router(create_narration_router(self.db))
        with patch('services.report_video.ReportVideo', return_value=self.service):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='https://test.invalid') as client:
                return await client.request(method, '/api/student/report-video/' + token, headers=headers)
    async def test_foreign_unpaid_unknown_and_disabled_accounts_never_enqueue(self):
        await self.denied(self.service.status('other', self.order['_id']), 404)
        await self.denied(self.service.status('unknown', self.order['_id']), 401)
        self.order['state'] = 'pending'; await self.denied(self.state(), 403)
        self.order['state'] = 'paid'; self.user['is_disabled'] = True
        await self.denied(self.state(), 401)
        self.assertFalse(self.service.root.exists()); self.reports.materialize.assert_not_awaited()
    async def test_test_live_mode_boundary_rechecks_status_and_old_capability(self):
        self.ready(); token = await self.token(); self.config.live = True
        await self.denied(self.state(), 409); await self.denied(self.service.resolve(token), 409)
    async def test_auth_version_and_changed_snapshot_revoke_old_link(self):
        self.ready(); token = await self.token(); self.user['auth_version'] = 3
        await self.denied(self.service.resolve(token), 401)
        self.user['auth_version'] = 2; self.order['report'] = {**self.order['report'], 'title': 'Новое объяснение'}
        await self.denied(self.service.resolve(token), 401)
    async def test_pending_analysis_has_counts_but_no_video_link(self):
        self.ready(); token = await self.token(); self.order['analysis_status'] = 'preparing'
        result = await self.state()
        self.assertEqual((result['status'], result['audio_ready'], result['audio_total']), ('waiting_analysis', 0, 2))
        self.assertNotIn('url', result); await self.denied(self.service.resolve(token), 401)
    async def test_analysis_review_is_visible_and_owner_can_retry_without_purchase(self):
        self.order['analysis_status']='review'
        result=await self.state()
        self.assertEqual((result['status'],result['stage']),('failed','analysis'))
        with patch('services.report_insights.ReportInsights.retry') as retry:
            result=await self.service.status('owner',self.order['_id'],retry=True)
            retry.assert_called_once_with(self.order['report'])
        self.assertEqual(result['status'],'waiting_analysis');self.assertEqual(self.order['state'],'paid')
        self.voice.retry_report.assert_not_called()
    async def test_audio_retry_is_bound_to_paid_owner_and_current_validated_report(self):
        self.voice.statuses['full-report-summary']='review'
        self.assertEqual((await self.state())['stage'],'audio')
        await self.denied(self.service.status('other',self.order['_id'],retry=True),404)
        self.order['state']='pending';await self.denied(self.service.status('owner',self.order['_id'],retry=True),403)
        self.voice.retry_report.assert_not_called();self.order['state']='paid'
        await self.service.status('owner',self.order['_id'],retry=True)
        self.voice.retry_report.assert_called_once_with(self.order['report']['narration'],self.order['_id'])
        self.voice.retry_report.reset_mock();self.order['report']['interpretation']['version']='rejected-v1'
        await self.service.status('owner',self.order['_id'],retry=True)
        self.voice.retry_report.assert_not_called()
    async def test_distinct_inline_attachment_tokens_bind_owner_order_and_snapshot(self):
        target = self.ready(); result = await self.state()
        inline, download = (result[key].rsplit('/', 1)[1] for key in ['url', 'download_url'])
        self.assertNotEqual(inline, download)
        claims = jwt.decode(inline, video_key(), algorithms=['HS256'], audience='numerom-report-video')
        self.assertEqual((claims['sub'], claims['order'], claims['auth_version']), ('owner', self.order['_id'], 2))
        self.assertEqual(claims['hash'], digest(VERSION, self.order['report'])); self.assertNotIn('birth_date', claims)
        self.assertEqual(await self.service.resolve(inline), (target / 'report.mp4', 'inline'))
        self.assertEqual(await self.service.resolve(download), (target / 'report.mp4', 'attachment'))
        self.order['user_id'] = 'other'; await self.denied(self.service.resolve(inline), 404)
    async def test_expired_wrong_audience_account_and_narration_tokens_cannot_read_video(self):
        self.ready(); base = jwt.get_unverified_claims(await self.token())
        invalid = [create_access_token({'sub': 'owner', 'auth_version': 2}),
            jwt.encode(base, narration_key(), algorithm='HS256'),
            jwt.encode({**base, 'aud': 'numerom-narration'}, video_key(), algorithm='HS256'),
            jwt.encode({**base, 'exp': int(time.time()) - 5}, video_key(), algorithm='HS256'),
            jwt.encode({key: value for key, value in base.items() if key != 'exp'}, video_key(), algorithm='HS256'),
            jwt.encode({**base, 'download': 'attachment'}, video_key(), algorithm='HS256')]
        for token in invalid:
            await self.denied(self.service.resolve(token), 401)
    async def test_even_signed_unsafe_hash_claim_cannot_select_arbitrary_path(self):
        self.ready(); base = jwt.get_unverified_claims(await self.token())
        for value in ['../private', '/etc/passwd', 'b' * 64]:
            token = jwt.encode({**base, 'hash': value}, video_key(), algorithm='HS256')
            await self.denied(self.service.resolve(token), 401)
    async def test_only_https_public_origin_without_path_query_or_credentials_is_issued(self):
        self.ready()
        for origin in ['http://media.example.invalid', 'https://user@media.example.invalid',
                       'https://media.example.invalid/path', 'https://media.example.invalid?token=x']:
            self.service.public_url = origin; await self.denied(self.state(), 503)
    async def test_missing_shortened_symlink_and_invalid_metadata_are_not_ready(self):
        target = self.ready(); token = await self.token(); movie = target / 'report.mp4'
        movie.unlink(); await self.denied(self.service.resolve(token), 404)
        movie.write_bytes(b'short'); self.assertNotEqual(self.service.state(self.order['report'])['status'], 'ready')
        movie.unlink(); other = self.root / 'private.mp4'; other.write_bytes(self.content); movie.symlink_to(other)
        await self.denied(self.service.resolve(token), 404)
        movie.unlink(); movie.write_bytes(self.content); (target / 'ready.json').write_text('{invalid json')
        self.assertNotEqual(self.service.state(self.order['report'])['status'], 'ready')
    async def test_same_length_tampering_invalidates_cached_file_hash(self):
        target = self.ready(); token = await self.token(); movie = target / 'report.mp4'
        before = movie.stat(); movie.write_bytes(b'X' * len(self.content))
        # Retaining mtime and length must not fool the verification cache; ctime changes.
        os.utime(movie, ns=(before.st_atime_ns, before.st_mtime_ns))
        await self.denied(self.service.resolve(token), 404)
    async def test_corrupt_committed_file_can_be_requeued_without_paying_again(self):
        target = self.ready(); (target / 'report.mp4').write_bytes(b'X' * len(self.content))
        self.assertEqual((await self.state())['status'], 'failed')
        result = await self.service.status('owner', self.order['_id'], retry=True)
        self.assertEqual(result['status'], 'waiting_audio'); self.assertFalse((target / 'ready.json').exists())
        self.assertEqual(self.order['state'], 'paid')
    async def test_committed_media_metrics_and_single_materialization_per_access(self):
        self.ready(4500.5); result = await self.state()
        self.assertEqual((result['seconds'], result['bytes']), (4500.5, len(self.content)))
        self.assertEqual(result['expires_in'], math.ceil(4500.5) + 1800)
        self.assertEqual(result['chapters'][0]['duration_seconds'], 4500.5)
        self.assertEqual(self.reports.materialize.await_count, 1)
        await self.service.resolve(result['url'].rsplit('/', 1)[1]); self.assertEqual(self.reports.materialize.await_count, 2)
    async def test_real_materialization_only_enqueues_and_never_recurses_into_video_access(self):
        self.ready()
        self.reports.materialize = FullReports.materialize.__get__(self.reports, FullReports)
        key = digest(VERSION, self.order['report'])
        with patch('services.report_insights.ReportInsights.enrich', return_value=(self.order['report'], 'ready')) as insights, \
                patch('services.narration.NarrationService.enqueue') as audio_queue, \
                patch('services.report_video.ReportVideo.enqueue', return_value=key) as video_queue:
            result = await asyncio.wait_for(self.state(), timeout=2)
            self.assertEqual(result['status'], 'ready')
            self.assertEqual(insights.call_count, 1)
            self.assertEqual(audio_queue.call_count, len(self.order['report']['narration']))
            self.assertEqual(video_queue.call_count, 2)  # materialize and status deduplicate the same digest.
    async def test_waiting_audio_progress_failure_retry_and_queue_deduplication(self):
        result = await self.state(); self.assertEqual((result['status'], result['audio_ready'], result['audio_total']), ('waiting_audio', 0, 2))
        await self.state(); self.assertEqual(len(list(self.service.root.glob('*/job.json'))), 1)
        for item in self.order['report']['narration']: self.voice.statuses[item['id']] = 'ready'
        self.assertEqual((await self.state())['status'], 'queued')
        target = folder(self.service.root, digest(VERSION, self.order['report']))
        write_json(target / 'progress.json', {'updated_at': time.time(), 'progress': 44})
        self.assertEqual((await self.state())['progress'], 44)
        write_json(target / 'failed.json', {'error': 'Local worker failed'})
        self.assertEqual((await self.state())['status'], 'failed')
        result = await self.service.status('owner', self.order['_id'], retry=True)
        self.assertEqual(result['status'], 'queued'); self.assertFalse((target / 'failed.json').exists())
    async def test_actual_signed_media_route_supports_range_head_attachment_and_no_store(self):
        self.ready(); token = await self.token()
        response = await self.media(token, headers={'Range': 'bytes=2-6'})
        self.assertEqual((response.status_code, response.content), (206, self.content[2:7]))
        self.assertEqual(response.headers['content-range'], f'bytes 2-6/{len(self.content)}')
        self.assertEqual(response.headers['cache-control'], 'private, no-store')
        self.assertEqual(response.headers['referrer-policy'], 'no-referrer')
        head = await self.media(token, 'HEAD', {'Range': 'bytes=2-6'})
        self.assertEqual((head.status_code, head.content), (200, b'')); self.assertEqual(int(head.headers['content-length']), len(self.content))
        attachment = await self.media(await self.token(True), 'HEAD')
        self.assertTrue(attachment.headers['content-disposition'].startswith('attachment;'))
    async def test_revocation_blocks_head_range_before_streaming(self):
        self.ready(); token = await self.token(); self.user['auth_version'] += 1
        for method in ['GET', 'HEAD']:
            result = await self.media(token, method, {'Range': 'bytes=0-2'})
            self.assertEqual(result.status_code, 401); self.assertNotIn('content-range', result.headers)
            self.assertNotEqual(result.content, self.content[:3])
    async def test_api_routes_use_current_owner_and_require_empty_retry_body(self):
        app = FastAPI(); app.dependency_overrides[get_current_user] = lambda: {'user_id': 'owner'}
        movies = SimpleNamespace(status=AsyncMock(return_value={'status': 'waiting_audio'}))
        app.include_router(create_full_reports_router(self.db, service=self.reports, narration=self.voice, video=movies))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='https://test.invalid') as client:
            route = '/api/full-reports/' + self.order['_id'] + '/video'
            self.assertEqual((await client.get(route)).status_code, 200); movies.status.assert_awaited_with('owner', self.order['_id'])
            self.assertEqual((await client.post(route, json={})).status_code, 200); movies.status.assert_awaited_with('owner', self.order['_id'], retry=True)
            for body in [{'report': {}}, {'user_id': 'other'}, {'amount_total': 0}, {'path': '/etc/passwd'}]:
                before = movies.status.await_count
                self.assertEqual((await client.post(route, json=body)).status_code, 422); self.assertEqual(movies.status.await_count, before)

class VideoManifestTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.voice, self.report = FakeVoice(temporary.name), report_fixture()
    def test_measured_audio_length_not_estimate_and_longest_matching_section(self):
        for item in self.report['narration']: self.voice.ready(item, 2.75)
        manifest = build_manifest(self.report, self.voice)
        self.assertEqual((manifest['fps'], manifest['width'], manifest['height']), (24, 1280, 720))
        self.assertEqual([item['durationInFrames'] for item in manifest['chapters']], [66, 66])
        self.assertEqual([item['section']['id'] for item in manifest['chapters']], ['personal', 'square-lines'])
        self.assertEqual(manifest['report'], self.report)
    def test_chapter_without_report_section_has_no_section_object(self):
        # «Границы расчёта» has no section; the renderer rejects an empty one.
        self.report['narration'].append({'id': 'full-report-excluded', 'hash': '3' * 64, 'title': 'Границы расчёта',
                                         'text': 'Имя не указано.', 'seconds': 999})
        for item in self.report['narration']: self.voice.ready(item, 2.75)
        chapter = build_manifest(self.report, self.voice)['chapters'][-1]
        self.assertEqual(chapter['id'], 'full-report-excluded')
        self.assertNotIn('section', chapter)
        self.assertTrue(chapter['segments'])
    def test_sequential_cue_focus_and_exact_fragment_gap(self):
        meta = {'segments': [{'seconds': 3, 'text': 'Линии', 'cues': [
            {'start': 0, 'end': 1, 'text': 'Горизонталь 1–4–7 раскрывает задачу.'},
            {'start': 1, 'end': 2, 'text': 'Здесь продолжается объяснение.'},
            {'start': 2, 'end': 3, 'text': 'Вертикаль 1–2–3 показывает сочетание.'}]}, {'seconds': 2, 'text': 'Продолжение.'}]}
        cues = cue_segments(meta, self.report['sections'][2])
        self.assertEqual([item['focusIndex'] for item in cues], [0, 0, 1, 1])
        self.assertEqual(cues[-1]['fromFrame'], round((3 + GAP) * FPS)); self.assertEqual(cues[-1]['durationInFrames'], 2 * FPS)
    def test_summary_clears_focus_when_topic_changes_or_names_multiple_positions(self):
        section = {'values': [{'label': 'Число души'}, {'label': 'Число судьбы'}]}
        meta = {'segments': [{'seconds': 4, 'cues': [
            {'start': 0, 'end': 1, 'text': 'Число души — один.'},
            {'start': 1, 'end': 2, 'text': 'Фрактал показывает сочетание.'},
            {'start': 2, 'end': 3, 'text': 'Число души и число судьбы сопоставляются.'},
            {'start': 3, 'end': 4, 'text': 'Число судьбы — четыре.'}]}]}
        cues = cue_segments(meta, section, summary=True)
        self.assertEqual([item.get('focusIndex') for item in cues], [0, None, None, 1])
    def test_no_audio_missing_audio_and_nonready_chapter_cannot_render(self):
        with self.assertRaises(ValueError): build_manifest({**self.report, 'narration': []}, self.voice)
        with self.assertRaises(ValueError): build_manifest(self.report, self.voice)
        for item in self.report['narration']: self.voice.ready(item)
        (self.voice.folder(self.report['narration'][0]['hash']) / 'audio.m4a').unlink()
        with self.assertRaises((ValueError, OSError)): build_manifest(self.report, self.voice)
    def test_sped_up_cues_never_run_past_the_measured_chapter(self):
        # 1.2× recordings: the cue (scaled 1/1.2) ends 0.03 s after the measured audio; the video manifest
        # refused the chapter («Segments must be … inside their chapter») and the paid video never rendered.
        meta = {'segments': [{'seconds': 119.66, 'cues': [
            {'start': 100.0, 'end': 105.2, 'text': 'Сила двойки в умении слушать.'},
            {'start': 105.6, 'end': 119.69, 'text': 'Последняя фраза главы.', 'words': []}]}]}
        frames = math.ceil(119.66 * 24)
        segments = cue_segments(meta, {}, limit=frames)
        self.assertEqual(segments[-1]['fromFrame'] + segments[-1]['durationInFrames'], frames)
        self.assertLessEqual(max(s['fromFrame'] + s['durationInFrames'] for s in segments), frames)
        self.assertGreater(round(119.69 * 24), frames)

    def test_subtitle_frame_boundaries_do_not_overlap_after_rounding(self):
        # Real preview regression: independently rounded duration ended at 521,
        # while the adjacent subtitle started on frame 520.
        meta = {'segments': [{'seconds': 23, 'cues': [
            {'start': 17.68, 'end': 21.68, 'text': 'Начало объяснения.'},
            {'start': 21.68, 'end': 23, 'text': 'Продолжение объяснения.'}]}]}
        first, second = cue_segments(meta, {})
        self.assertEqual(first['fromFrame'] + first['durationInFrames'], second['fromFrame'])
    def test_tampered_audio_and_audio_symlink_are_rejected(self):
        for item in self.report['narration']: self.voice.ready(item)
        target = self.voice.folder(self.report['narration'][0]['hash']); audio = target / 'audio.m4a'
        audio.write_bytes(b'tampered')
        with self.assertRaises(ValueError): build_manifest(self.report, self.voice)
        audio.unlink(); audio.symlink_to(self.voice.folder(self.report['narration'][1]['hash']) / 'audio.m4a')
        with self.assertRaises(ValueError): build_manifest(self.report, self.voice)
    def test_invalid_fragment_durations_and_cue_bounds_fail_closed(self):
        for seconds in [0, -1, float('inf'), float('nan')]:
            with self.subTest(seconds=seconds), self.assertRaises(ValueError):
                cue_segments({'segments': [{'seconds': seconds, 'text': 'Текст'}]}, {})
        with self.assertRaises(ValueError):
            cue_segments({'segments': [{'seconds': 2, 'cues': [{'start': 0, 'end': 3, 'text': 'За концом'}]}]}, {})
    def test_fragment_total_cannot_exceed_actual_audio_length(self):
        for item in self.report['narration']: self.voice.ready(item, 2, [{'seconds': 8, 'text': 'Длиннее записи'}])
        with self.assertRaises(ValueError): build_manifest(self.report, self.voice)
    def test_explicit_clip_selection_cannot_invent_unknown_chapter(self):
        for item in self.report['narration']: self.voice.ready(item)
        wanted = self.report['narration'][1]['id']
        self.assertEqual([item['id'] for item in build_manifest(self.report, self.voice, clip_ids={wanted})['chapters']], [wanted])
        with self.assertRaises(ValueError): build_manifest(self.report, self.voice, clip_ids={'unknown'})

class VideoGatewayTests(unittest.TestCase):
    def test_only_exact_video_endpoints_and_empty_json_pass(self):
        route = '/api/full-reports/' + 'a' * 64 + '/video'
        self.assertEqual(_route('GET', route), 'read'); self.assertEqual(_route('POST', route), 'write')
        self.assertTrue(_valid_body(route, {}))
        for body in [{'text': 'arbitrary'}, {'report': {}}, {'path': '/etc/passwd'}, {'owner': 'other'}]: self.assertFalse(_valid_body(route, body))
        for method in ['GET', 'HEAD']: self.assertEqual(_route(method, '/api/student/report-video/signed.token'), 'media')
        for method, invalid in [('DELETE', route), ('PUT', route), ('POST', '/api/student/report-video/token'),
            ('GET', '/api/student/report-video/../file'), ('GET', route + '/raw')]: self.assertIsNone(_route(method, invalid))

if __name__ == '__main__': unittest.main()
