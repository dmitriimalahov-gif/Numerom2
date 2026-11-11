"""HTTP authorization contracts for Bunny routes; no server startup or external calls."""
import copy
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import FastAPI
from fastapi.testclient import TestClient
from auth import create_access_token
import bunny_endpoints
import bunny_manual_link


class SyntheticCollection:
    def __init__(self, documents=()):
        self.documents = copy.deepcopy(list(documents))
        self.reads = 0
        self.writes = 0

    async def find_one(self, query):
        self.reads += 1
        return copy.deepcopy(next((row for row in self.documents if all(row.get(key) == value for key, value in query.items())), None))

    async def update_one(self, query, update):
        self.writes += 1
        for row in self.documents:
            if all(row.get(key) == value for key, value in query.items()):
                row.update(copy.deepcopy(update.get('$set', {})))
                for key in update.get('$unset', {}):
                    row.pop(key, None)
                return SimpleNamespace(matched_count=1)
        return SimpleNamespace(matched_count=0)

    async def insert_one(self, document):
        self.writes += 1
        self.documents.append(copy.deepcopy(document))


ADMIN_ROUTES = (
    ('POST', '/api/admin/lessons/lesson-1/upload-video-bunny', {'files': {'file': ('lesson.mp4', b'synthetic video', 'video/mp4')}}),
    ('DELETE', '/api/admin/lessons/lesson-1/video-bunny', {}),
    ('GET', '/api/admin/lessons/lesson-1/video-info', {}),
    ('POST', '/api/admin/lessons/link-bunny-video', {'json': {'lesson_id': 'lesson-1', 'video_id': 'video-1'}}),
    ('GET', '/api/admin/lessons/lesson-1/bunny-video-id', {}),
)


class BunnyAuthorizationContracts(unittest.TestCase):
    def setUp(self):
        signing = patch.dict(os.environ, {'SECRET_KEY': 'synthetic-bunny-authorization-signing-key-only'})
        signing.start()
        self.addCleanup(signing.stop)
        self.db = SimpleNamespace(
            users=SyntheticCollection([
                {'id': 'member', 'is_admin': False, 'is_super_admin': False},
                {'id': 'admin', 'is_admin': True, 'is_super_admin': False},
                {'id': 'owner', 'is_admin': False, 'is_super_admin': True},
            ]),
            custom_lessons=SyntheticCollection([{
                'id': 'lesson-1', 'title': 'Synthetic lesson', 'video_platform': 'bunny',
                'video_id': 'video-1', 'video_library_id': 'library-test', 'video_status': 'ready',
            }]),
            lessons=SyntheticCollection(),
        )
        # The real handlers import only this synthetic db; production server is never loaded.
        server = patch.dict(sys.modules, {'server': SimpleNamespace(db=self.db)})
        server.start()
        self.addCleanup(server.stop)
        self.temp = tempfile.TemporaryDirectory(prefix='numerom-bunny-auth-')
        self.addCleanup(self.temp.cleanup)
        temp = patch.object(bunny_endpoints, 'TMP_DIR', Path(self.temp.name))
        temp.start()
        self.addCleanup(temp.stop)
        self.bunny = SimpleNamespace(
            library_id='library-test', cdn_hostname='media.example.invalid',
            upload_video=AsyncMock(return_value={
                'video_id': 'uploaded-1', 'library_id': 'library-test',
                'thumbnail_url': 'https://media.example.invalid/thumbnail.jpg',
                'iframe_url': 'https://media.example.invalid/embed',
            }),
            delete_video=AsyncMock(return_value=True),
            get_video_info=AsyncMock(return_value={'status': 4, 'title': 'Synthetic video'}),
            generate_signed_url=Mock(return_value='https://media.example.invalid/signed-video'),
        )
        self.factory_calls = 0
        def synthetic_bunny_service():
            self.factory_calls += 1
            return self.bunny
        self.app = FastAPI()
        self.app.state.auth_db = self.db
        self.app.include_router(bunny_endpoints.bunny_router)
        self.app.include_router(bunny_manual_link.manual_link_router)
        self.app.dependency_overrides[bunny_endpoints.get_bunny_service] = synthetic_bunny_service
        factory = patch('video_platforms.bunny_stream.get_bunny_service', synthetic_bunny_service)
        factory.start()
        self.addCleanup(factory.stop)
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)

    def headers(self, user_id, **claims):
        return {'Authorization': 'Bearer ' + create_access_token({'sub': user_id, **claims})}

    def assert_no_video_operations(self):
        self.bunny.upload_video.assert_not_called()
        self.bunny.delete_video.assert_not_called()
        self.bunny.get_video_info.assert_not_called()
        self.bunny.generate_signed_url.assert_not_called()
        self.assertEqual(self.factory_calls, 0)
        self.assertEqual(self.db.custom_lessons.reads + self.db.lessons.reads, 0)
        self.assertEqual(self.db.custom_lessons.writes + self.db.lessons.writes, 0)
        self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    def test_all_admin_routes_reject_anonymous_before_video_or_database_operations(self):
        for method, path, options in ADMIN_ROUTES:
            with self.subTest(path=path):
                result = self.client.request(method, path, **options)
                self.assertEqual(result.status_code, 401)
                self.assert_no_video_operations()

    def test_all_admin_routes_reject_members_even_with_admin_token_claim(self):
        for method, path, options in ADMIN_ROUTES:
            with self.subTest(path=path):
                result = self.client.request(method, path, headers=self.headers('member', role='admin', is_admin=True), **options)
                self.assertEqual(result.status_code, 403)
                self.assert_no_video_operations()

    def test_both_current_admin_flags_allow_every_admin_route(self):
        for actor in ('admin', 'owner'):
            for method, path, options in ADMIN_ROUTES:
                with self.subTest(actor=actor, path=path):
                    self.db.custom_lessons.documents[0].update(video_platform='bunny', video_id='video-1', video_status='ready')
                    result = self.client.request(method, path, headers=self.headers(actor, role='user'), **options)
                    self.assertEqual(result.status_code, 200, result.text)
                    self.assertTrue(result.json()['success'])
        self.bunny.upload_video.assert_awaited()
        self.bunny.delete_video.assert_awaited()
        self.bunny.get_video_info.assert_awaited()

    def test_demotion_and_disabled_account_are_checked_with_an_existing_token(self):
        token = self.headers('admin', role='admin')
        self.db.users.documents[1]['is_admin'] = False
        result = self.client.get('/api/admin/lessons/lesson-1/video-info', headers=token)
        self.assertEqual(result.status_code, 403)
        self.db.users.documents[1].update(is_admin=True, is_disabled=True)
        result = self.client.get('/api/admin/lessons/lesson-1/video-info', headers=token)
        self.assertEqual(result.status_code, 401)
        self.assert_no_video_operations()

    def test_user_video_route_requires_login_but_not_admin_rights(self):
        path = '/api/lessons/lesson-1/video-url'
        result = self.client.get(path)
        self.assertEqual(result.status_code, 401)
        self.assert_no_video_operations()
        result = self.client.get(path, headers=self.headers('member'))
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()['video_url'], 'https://media.example.invalid/signed-video')
        self.bunny.generate_signed_url.assert_called_once()
        self.bunny.upload_video.assert_not_called()
        self.bunny.delete_video.assert_not_called()


if __name__ == '__main__':
    unittest.main()
