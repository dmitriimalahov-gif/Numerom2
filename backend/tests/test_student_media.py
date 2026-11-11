import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import HTTPException
from jose import jwt
from services.student_media import StudentMediaService, media_key

class StudentMediaTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / 'lesson').mkdir()
        (self.root / 'lesson' / 'stored.pdf').write_bytes(b'%PDF-1.7 synthetic')
        self.user = {'id': 'user', 'auth_version': 2}
        self.item = {'id': 'file', 'lesson_id': 'lesson', 'stored_name': 'stored.pdf', 'original_name': 'Lesson.pdf'}
        self.db = SimpleNamespace(users=SimpleNamespace(find_one=AsyncMock(side_effect=lambda q:self.user if q=={'id':'user'} else None)),files=SimpleNamespace(find_one=AsyncMock(side_effect=lambda q: self.item if q == {'id':'file','lesson_id':'lesson'} else None)))
        self.service = StudentMediaService(self.db, self.root, 'https://media.example.org')
        self.env = patch.dict(os.environ, {'SECRET_KEY':'synthetic-test-secret-' * 3})
        self.env.start(); self.addCleanup(self.env.stop)
        self.access = patch('services.student_media.require_student_lesson', new=AsyncMock(return_value=(self.user, {'id':'lesson'})))
        self.access_mock = self.access.start(); self.addCleanup(self.access.stop)
    async def token(self):
        return (await self.service.access('user','lesson','file'))['url'].rsplit('/',1)[1]
    async def test_valid_link_serves_only_file_from_matching_lesson(self):
        token = await self.token()
        path, name, kind, disposition = await self.service.resolve(token)
        self.assertEqual(path, self.root / 'lesson' / 'stored.pdf')
        self.assertEqual((name,kind,disposition), ('Lesson.pdf','application/pdf','inline'))
        with self.assertRaises(HTTPException):
            await self.service.access('user','different-lesson','file')
    async def test_expired_account_or_wrong_audience_token_cannot_download(self):
        token = await self.token()
        self.user['auth_version'] = 3
        with self.assertRaises(HTTPException): await self.service.resolve(token)
        for expiry, audience in ((-1,'numerom-student-media'), (300,'other')):
            bad = jwt.encode({'sub':'user','lesson':'lesson','file':'file','auth_version':3,
                              'aud':audience,'exp':datetime.now(timezone.utc)+timedelta(seconds=expiry)}, media_key(), algorithm='HS256')
            with self.assertRaises(HTTPException): await self.service.resolve(bad)
    async def test_normal_account_jwt_cannot_be_used_as_media_capability(self):
        token = jwt.encode({'sub':'user','lesson':'lesson','file':'file','aud':'numerom-student-media',
                           'exp':datetime.now(timezone.utc)+timedelta(minutes=5)}, os.environ['SECRET_KEY'], algorithm='HS256')
        with self.assertRaises(HTTPException): await self.service.resolve(token)
    async def test_path_traversal_and_symlink_outside_root_are_rejected(self):
        self.item['stored_name'] = '../../private.pdf'
        with self.assertRaises(HTTPException): await self.token()
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / 'secret.pdf'; target.write_text('private')
            (self.root / 'lesson' / 'link.pdf').symlink_to(target)
            self.item['stored_name'] = 'link.pdf'
            with self.assertRaises(HTTPException): await self.token()
    async def test_access_revocation_and_unsafe_mime_are_enforced(self):
        token = await self.token()
        self.access_mock.side_effect = HTTPException(403, 'Unavailable')
        with self.assertRaises(HTTPException): await self.service.resolve(token)
        self.access_mock.side_effect = None
        self.item['original_name'] = 'script.html'
        self.assertEqual((await self.service.resolve(token))[2:], ('application/octet-stream','attachment'))
