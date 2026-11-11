import asyncio
import base64
import io
import os
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import HTTPException
from PIL import Image
from motor.motor_asyncio import AsyncIOMotorClient
from services.exercise_attachments import AttachmentUpload, ExerciseAttachments, validate_file, MAX_BYTES
from services.student_learning import ExerciseSubmission, StudentLearningService
from routers.exercise_attachments import create_exercise_attachments_router


def upload(data=None, name='пример.png', request_id=None):
    if data is None:
        buffer = io.BytesIO(); Image.new('RGB', (2, 2), 'navy').save(buffer, 'PNG'); data = buffer.getvalue()
    return AttachmentUpload(request_id=request_id or uuid.uuid4(), name=name, content_base64=base64.b64encode(data).decode())


class FileValidationTests(unittest.TestCase):
    def test_real_image_and_pdf_but_not_mislabeled_script(self):
        self.assertEqual(validate_file(upload())[1], 'image/png')
        self.assertEqual(validate_file(upload(b'%PDF-1.7\n1 0 obj <<>> endobj\n%%EOF', 'notes.pdf'))[1], 'application/pdf')
        for body in (b'<script>alert(1)</script>', b'\x89PNG\r\n\x1a\nfake', b'%PDF-1.7 missing end'):
            with self.assertRaises(HTTPException): validate_file(upload(body))
    def test_base64_size_and_dimensions_are_bounded(self):
        with self.assertRaises(HTTPException): validate_file(upload(b'x' * (MAX_BYTES + 1)))
        with patch('services.exercise_attachments.Image.open') as open_image:
            image=open_image.return_value.__enter__.return_value
            image.format='PNG';image.width=20000;image.height=20000;image.size=(20000,20000)
            with self.assertRaises(HTTPException): validate_file(upload())
    def test_router_has_scoped_auth_and_passive_media(self):
        self.assertEqual(len(create_exercise_attachments_router(None).routes), 5)


@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'), 'isolated Mongo only')
class AttachmentTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mongo=AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL']);self.db=self.mongo['numerom_test_attachments_'+uuid.uuid4().hex]
        await self.db.users.insert_many([{'id':uid,'credits_remaining':10,'level':1,'auth_version':1,'is_admin':uid=='teacher'} for uid in ('owner','other','teacher')])
        await self.db.lessons_v2.insert_one({'id':'lesson','is_active':True,'level':1,'exercises':[{'id':'ex'},{'id':'second'}]})
        self.temp=tempfile.TemporaryDirectory();self.service=ExerciseAttachments(self.db,self.temp.name,public_url='https://files.example.invalid')
        self.learning=StudentLearningService(self.db)
        self.secret=patch.dict(os.environ,{'SECRET_KEY':'isolated-attachment-test-only-key'});self.secret.start()
    async def asyncTearDown(self):
        self.secret.stop();await self.mongo.drop_database(self.db.name);self.mongo.close();self.temp.cleanup()
    async def put(self, request=None): return (await self.service.upload('owner','lesson','ex',request or upload()))['file']['id']
    async def submit(self, ids): return await self.learning.submit_exercise('owner',ExerciseSubmission(lesson_id='lesson',exercise_id='ex',response_text='Моя работа',attachment_ids=ids))
    async def test_upload_is_private_and_does_not_award_or_complete(self):
        key=await self.put()
        self.assertEqual(len((await self.service.list('owner','lesson','ex'))['files']),1)
        self.assertEqual((await self.service.list('other','lesson','ex'))['files'],[])
        self.assertEqual((await self.learning.exercise_responses('owner','lesson'))['exercise_responses'],{})
        self.assertEqual((await self.db.users.find_one({'id':'owner'}))['credits_remaining'],10)
        for uid in ('other','teacher'):
            with self.assertRaises(HTTPException): await self.service.access(uid,key)
        self.assertEqual(await self.db.lesson_progress.count_documents({}),0)
    async def test_concurrent_quota_and_replay_are_atomic(self):
        request=upload();keys=await asyncio.gather(*(self.put(request) for _ in range(8)))
        self.assertEqual(len(set(keys)),1)
        results=await asyncio.gather(*(self.put() for _ in range(8)),return_exceptions=True)
        self.assertEqual(sum(isinstance(result,str) for result in results),2)
        self.assertEqual(len((await self.service.list('owner','lesson','ex'))['files']),3)
        with self.assertRaises(HTTPException): await self.put(upload(b'%PDF-1.7\n%%EOF','different.pdf',request.request_id))
    async def test_submission_owns_files_awards_once_and_teacher_can_read(self):
        key=await self.put();await self.submit([key]);await self.submit([key])
        self.assertEqual((await self.db.users.find_one({'id':'owner'}))['credits_remaining'],20)
        saved=(await self.learning.exercise_responses('owner','lesson'))['exercise_responses']['ex']
        self.assertEqual(saved['attachment_ids'],[key]);self.assertNotIn('attachment_files',saved)
        link=(await self.service.access('teacher',key))['url'];path,item=await self.service.resolve(link.rsplit('/',1)[1])
        self.assertTrue(path.is_file());self.assertEqual(item['id'],key)
        await self.db.users.update_one({'id':'owner'},{'$set':{'is_disabled':True}})
        self.assertTrue((await self.service.resolve(link.rsplit('/',1)[1]))[0].is_file())
        await self.db.users.update_one({'id':'owner'},{'$set':{'is_disabled':False}})
        with self.assertRaises(HTTPException): await self.service.remove('owner','lesson','ex',key)
        with self.assertRaises(HTTPException): await self.learning.submit_exercise('other',ExerciseSubmission(lesson_id='lesson',exercise_id='ex',response_text='copy',attachment_ids=[key]))
    async def test_legacy_text_edit_preserves_attachments_but_explicit_empty_clears(self):
        key=await self.put();await self.submit([key])
        await self.learning.submit_exercise('owner',ExerciseSubmission(lesson_id='lesson',exercise_id='ex',response_text='Уточнение с сайта'))
        self.assertEqual((await self.learning.exercise_responses('owner','lesson'))['exercise_responses']['ex']['attachment_ids'],[key])
        await self.submit([]);await self.service.remove('owner','lesson','ex',key)
        self.assertEqual((await self.service.list('owner','lesson','ex'))['files'],[])

    async def test_signed_http_download_is_attachment_range_and_not_cached(self):
        import httpx
        from fastapi import FastAPI
        from auth import get_current_user
        app=FastAPI();app.include_router(create_exercise_attachments_router(self.db,root=self.temp.name,public_url='https://files.example.invalid'))
        app.dependency_overrides[get_current_user]=lambda:{'user_id':'owner'}
        key=await self.put()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='https://files.example.invalid') as client:
            access=await client.get('/api/student/exercise-attachment-access/'+key);self.assertEqual(access.status_code,200)
            url=access.json()['url'];response=await client.get(url,headers={'Range':'bytes=0-7'})
            self.assertEqual(response.status_code,206);self.assertEqual(response.content,b'\x89PNG\r\n\x1a\n')
            self.assertTrue(response.headers['content-disposition'].startswith('attachment;'))
            self.assertIn('no-store',response.headers['cache-control']);self.assertEqual(response.headers['x-content-type-options'],'nosniff')
            head=await client.head(url);self.assertEqual(head.status_code,200);self.assertEqual(head.content,b'')
            await self.db.users.update_one({'id':'owner'},{'$inc':{'auth_version':1}})
            self.assertEqual((await client.get(url)).status_code,401)

    async def test_draft_remove_replay_and_session_revocation(self):
        request=upload();key=await self.put(request)
        token=(await self.service.access('owner',key))['url'].rsplit('/',1)[1]
        await self.db.users.update_one({'id':'owner'},{'$inc':{'auth_version':1}})
        with self.assertRaises(HTTPException): await self.service.resolve(token)
        await self.service.remove('owner','lesson','ex',key);await self.service.remove('owner','lesson','ex',key)
        self.assertEqual((await self.service.list('owner','lesson','ex'))['files'],[])
        with self.assertRaises(HTTPException): await self.put(request)
        with self.assertRaises(HTTPException): await self.submit([key])
    async def test_removal_racing_submission_never_loses_confirmed_file(self):
        for index in range(5):
            key=await self.put()
            results=await asyncio.gather(self.submit([key]), self.service.remove('owner','lesson','ex',key),return_exceptions=True)
            if not isinstance(results[0],Exception):
                token=(await self.service.access('owner',key))['url'].rsplit('/',1)[1]
                path,_=await self.service.resolve(token);self.assertTrue(path.is_file())
                await self.submit([]);await self.service.remove('owner','lesson','ex',key)
            else:
                self.assertIsInstance(results[0],HTTPException)
    async def test_closed_lesson_and_symlink_do_not_open(self):
        key=await self.put();token=(await self.service.access('owner',key))['url'].rsplit('/',1)[1]
        path,_=await self.service.resolve(token);path.unlink();path.symlink_to('/etc/hosts')
        with self.assertRaises(HTTPException): await self.service.resolve(token)
        await self.db.lessons_v2.update_one({'id':'lesson'},{'$set':{'is_active':False}})
        with self.assertRaises(HTTPException): await self.service.list('owner','lesson','ex')
