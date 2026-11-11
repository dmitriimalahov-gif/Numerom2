import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI, HTTPException, Request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.media_response import CHUNK_BYTES, MEDIA_CSP, media_file_response
from auth import create_access_token
from routers.student_media import create_student_media_router
from services.student_media import StudentMediaService


class MediaResponseTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'video.mp4'
        self.content = bytes(range(256)) * 1024
        self.path.write_bytes(self.content)
        self.app = FastAPI()

        @self.app.api_route('/media', methods=['GET', 'HEAD'])
        async def media(request: Request):
            return await media_file_response(request, self.path, 'Урок.mp4', 'video/mp4', 'inline')

    async def request(self, method='GET', headers=None):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url='https://test') as client:
            return await client.request(method, '/media', headers=headers)

    async def test_full_get_has_safe_headers_and_exact_content(self):
        response = await self.request()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.content)
        self.assertEqual(response.headers['content-length'], str(len(self.content)))
        self.assertEqual(response.headers['accept-ranges'], 'bytes')
        self.assertEqual(response.headers['cache-control'], 'private, no-store')
        self.assertEqual(response.headers['x-content-type-options'], 'nosniff')
        self.assertEqual(response.headers['referrer-policy'], 'no-referrer')
        self.assertEqual(response.headers['content-security-policy'], MEDIA_CSP)
        self.assertIn("filename*=UTF-8''", response.headers['content-disposition'])
        self.assertIn("media-src 'self' blob:", MEDIA_CSP)

    async def test_closed_open_suffix_and_clamped_ranges(self):
        for value, start, end in [('bytes=4-9', 4, 9), ('bytes=10-', 10, len(self.content)-1),
                                  ('bytes=-7', len(self.content)-7, len(self.content)-1),
                                  ('bytes=0-999999999', 0, len(self.content)-1)]:
            with self.subTest(value=value):
                response = await self.request(headers={'Range': value})
                self.assertEqual(response.status_code, 206)
                self.assertEqual(response.content, self.content[start:end+1])
                self.assertEqual(response.headers['content-range'], f'bytes {start}-{end}/{len(self.content)}')
                self.assertEqual(int(response.headers['content-length']), end-start+1)

    async def test_invalid_multiple_and_unsatisfiable_ranges_are_416(self):
        for value in ['bytes=', 'bytes=-', 'bytes=2-1', 'bytes=-0', 'bytes=999999-',
                      'bytes=0-1,2-3', 'items=0-1', 'bytes=0-a', 'bytes=+1-2', 'bytes='+'9'*5000+'-']:
            with self.subTest(value=value[:30]):
                response = await self.request(headers={'Range': value})
                self.assertEqual(response.status_code, 416)
                self.assertEqual(response.headers['content-range'], f'bytes */{len(self.content)}')
                self.assertEqual(response.content, b'')
        response = await self.request(headers=[('Range', 'bytes=0-1'), ('Range', 'bytes=2-3')])
        self.assertEqual(response.status_code, 416)

    async def test_head_has_full_metadata_no_body_and_ignores_range(self):
        response = await self.request('HEAD', {'Range': 'bytes=3-9'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.headers['content-length']), len(self.content))
        self.assertNotIn('content-range', response.headers)
        self.assertEqual(response.content, b'')

    async def test_if_range_requires_current_strong_validator(self):
        initial = await self.request('HEAD')
        for validator in [initial.headers['etag'], initial.headers['last-modified']]:
            response = await self.request(headers={'Range':'bytes=1-3', 'If-Range':validator})
            self.assertEqual(response.status_code, 206)
            self.assertEqual(response.content, self.content[1:4])
        for validator in ['"different"', 'W/' + initial.headers['etag'], 'Wed, 01 Jan 2020 00:00:00 GMT']:
            response = await self.request(headers={'Range':'bytes=1-3', 'If-Range':validator})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, self.content)

    async def test_empty_file_and_range(self):
        self.path.write_bytes(b'')
        self.assertEqual((await self.request()).content, b'')
        response = await self.request(headers={'Range':'bytes=0-'})
        self.assertEqual(response.status_code, 416)
        self.assertEqual(response.headers['content-range'], 'bytes */0')

    async def test_missing_symlink_and_oversized_files_are_rejected_before_body(self):
        self.path.unlink()
        self.assertEqual((await self.request()).status_code, 404)
        other = self.path.parent / 'other.mp4'
        other.write_bytes(b'other')
        self.path.symlink_to(other)
        self.assertEqual((await self.request()).status_code, 404)
        self.path.unlink()
        self.path.write_bytes(self.content)
        with patch('services.media_response.MAX_FILE_BYTES', 1):
            self.assertEqual((await self.request()).status_code, 413)

    async def test_stream_uses_bounded_chunks_and_closes_on_disconnect(self):
        request = Request({'type':'http', 'method':'GET', 'headers':[]})
        response = await media_file_response(request, self.path, 'x.mp4', 'video/mp4', 'inline')
        sizes = []
        async def send(message):
            if message['type'] == 'http.response.body':
                sizes.append(len(message['body']))
        async def receive():
            await asyncio.sleep(10)
        await response({'type':'http'}, receive, send)
        self.assertGreater(len(sizes), 2)
        self.assertLessEqual(max(sizes), CHUNK_BYTES)
        self.assertEqual(sum(sizes), len(self.content))
        self.assertTrue(response.file.closed)

        response = await media_file_response(request, self.path, 'x.mp4', 'video/mp4', 'inline')
        async def disconnected():
            return {'type':'http.disconnect'}
        await response({'type':'http'}, disconnected, send)
        self.assertTrue(response.file.closed)

    async def test_unsafe_mime_cannot_be_forced_inline(self):
        request = Request({'type':'http', 'method':'HEAD', 'headers':[]})
        response = await media_file_response(request, self.path, 'page.html', 'text/html', 'inline')
        self.assertEqual(response.headers['content-type'], 'application/octet-stream')
        self.assertTrue(response.headers['content-disposition'].startswith('attachment;'))

    async def test_response_keeps_opened_file_and_never_streams_past_original_length(self):
        request = Request({'type':'http', 'method':'GET', 'headers':[]})
        response = await media_file_response(request, self.path, 'x.mp4', 'video/mp4', 'inline')
        # An append cannot expand the already authorized response's byte budget.
        with self.path.open('ab') as file:
            file.write(b'new data')
        self.path.rename(self.path.with_suffix('.old'))
        self.path.write_bytes(b'replacement')
        chunks = []
        async def send(message):
            if message['type'] == 'http.response.body':
                chunks.append(message['body'])
        async def receive():
            await asyncio.sleep(10)
        await response({'type':'http'}, receive, send)
        self.assertEqual(b''.join(chunks), self.content)


class AuthorizedMediaResponseTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'video.mp4').write_bytes(b'0123456789')
        self.user = {'id':'user', 'auth_version':1}
        item = {'id':'file', 'lesson_id':'lesson', 'stored_name':'video.mp4', 'original_name':'Video.mp4'}
        self.db = SimpleNamespace(users=SimpleNamespace(find_one=AsyncMock(side_effect=lambda q:self.user if q=={'id':'user'} else None)),files=SimpleNamespace(find_one=AsyncMock(return_value=item)))
        env = patch.dict(os.environ, {'SECRET_KEY':'synthetic-media-test-key-'*3})
        env.start(); self.addCleanup(env.stop)
        authorized = patch('services.student_media.require_student_lesson', new=AsyncMock(return_value=(self.user, {'id':'lesson'})))
        self.authorized = authorized.start(); self.addCleanup(authorized.stop)
        self.service = StudentMediaService(self.db, self.root, 'https://media.example.org')
        self.app = FastAPI()
        self.app.include_router(create_student_media_router(self.db, self.root))

    async def request(self, token, method='GET'):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url='https://test') as client:
            return await client.request(method, '/api/student/media/'+token, headers={'Range':'bytes=2-4'})

    async def token(self):
        return (await self.service.access('user','lesson','file'))['url'].rsplit('/',1)[1]

    async def test_authorized_capability_supports_range_and_head(self):
        token = await self.token()
        response = await self.request(token)
        self.assertEqual(response.status_code, 206)
        self.assertEqual(response.content, b'234')
        head = await self.request(token, 'HEAD')
        self.assertEqual(head.status_code, 200)
        self.assertEqual(head.headers['content-length'], '10')
        self.assertEqual(head.content, b'')

    async def test_revoked_capability_and_account_token_cannot_read_partial_file(self):
        token = await self.token()
        self.user['auth_version'] = 2
        for method in ['GET','HEAD']:
            self.assertEqual((await self.request(token, method)).status_code, 401)
        account_token = create_access_token({'sub':'user', 'auth_version':2})
        self.assertEqual((await self.request(account_token)).status_code, 401)

    async def test_lesson_access_is_rechecked_for_partial_requests(self):
        token = await self.token()
        self.authorized.side_effect = HTTPException(403, 'No lesson access')
        response = await self.request(token)
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('content-range', response.headers)


if __name__ == '__main__':
    unittest.main()
