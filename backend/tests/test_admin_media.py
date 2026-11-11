import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import FastAPI
from fastapi.testclient import TestClient
from auth import get_current_user
from routers.admin_media import create_admin_media_router

class ConsultationMediaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        (root/'report.pdf').write_bytes(b'%PDF-1.7 test')
        self.actor = {'id':'admin','is_admin':True}
        self.item = {'id':'file','stored_name':'report.pdf','original_name':'Report.pdf'}
        self.db = SimpleNamespace(users=SimpleNamespace(find_one=AsyncMock(side_effect=lambda q,*args:self.actor)),
                                  files=SimpleNamespace(find_one=AsyncMock(side_effect=lambda q:self.item)))
        app = FastAPI(); app.include_router(create_admin_media_router(self.db, root))
        app.dependency_overrides[get_current_user] = lambda:{'user_id':'admin'}
        self.client = TestClient(app); self.addCleanup(self.client.close)
    def test_admin_can_preview_pdf_and_member_cannot_read_file_metadata(self):
        response=self.client.get('/api/admin/consultations/files/file')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.headers['cache-control'],'private, no-store')
        self.assertTrue(response.content.startswith(b'%PDF'))
        self.db.files.find_one.reset_mock(); self.actor['is_admin']=False
        self.assertEqual(self.client.get('/api/admin/consultations/files/file').status_code,403)
        self.db.files.find_one.assert_not_awaited()
    def test_lesson_files_and_traversal_are_not_consultation_previews(self):
        self.item['lesson_id']='lesson'
        self.assertEqual(self.client.get('/api/admin/consultations/files/file').status_code,404)
        self.item.pop('lesson_id'); self.item['stored_name']='../private.pdf'
        self.assertEqual(self.client.get('/api/admin/consultations/files/file').status_code,404)
