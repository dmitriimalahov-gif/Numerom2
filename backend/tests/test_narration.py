import json
import hashlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi import HTTPException
from jose import jwt
from domain.narration import lesson_clips
from services.narration import NarrationService,narration_key
from public_gateway import _route,_valid_body

class ContentTests(unittest.TestCase):
    def test_project_covers_each_personal_number_and_every_line(self):
        from domain.personal_report import NUMBER_INFO
        from domain.personal_scheme import LINE_INFO
        source=Path(__file__).resolve().parents[2]/'packages/project-knowledge/ru.json'
        entries=json.loads(source.read_text())['items'];ids=[e['id'] for e in entries]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertTrue(set(NUMBER_INFO)<=set(ids));self.assertTrue({e[0] for e in LINE_INFO}<=set(ids))
        for entry in entries:self.assertTrue(entry['text'].strip())
    def test_only_visible_fields_and_quiz_options_are_narrated(self):
        lesson={'id':'lesson','title':'Урок','content':{'theory':{'main_story':'Видно','secret':'СКРЫТАЯ ТЕОРИЯ'},'hidden_theory_fields':{'fields':['secret']},'custom_theory_blocks':{'blocks':[{'content':'ТАЙНА','hidden':True},{'title':'Дополнение','content':'Текст'}]}},
          'quiz':{'questions':[{'id':'q1','question':'Вопрос','options':['Один','Два'],'correct_answer':'СЕКРЕТ ОТВЕТА','explanation':'КЛЮЧ'}]},'student_response':'ЛИЧНЫЕ ДАННЫЕ'}
        clips=lesson_clips(lesson);text=json.dumps(clips,ensure_ascii=False)
        for secret in ['СКРЫТАЯ ТЕОРИЯ','ТАЙНА','СЕКРЕТ ОТВЕТА','КЛЮЧ','ЛИЧНЫЕ ДАННЫЕ']:self.assertNotIn(secret,text)
        self.assertIn('Вариант 1. Один',text);self.assertIn('theory-1',text)
    def test_edits_change_audio_identity_but_answers_do_not(self):
        lesson={'id':'lesson','theory':[{'title':'Тема','content':'Первый текст'}]}
        old=lesson_clips(lesson)[0]['hash'];lesson['theory'][0]['content']='Новый текст'
        self.assertNotEqual(old,lesson_clips(lesson)[0]['hash'])
    def test_gateway_exposes_only_narration_contracts(self):
        for path,method,bucket in [('/api/narration/project','GET','read'),('/api/narration/lesson/lesson','GET','read'),('/api/narration/lesson/lesson/theory-0/access','POST','write'),('/api/narration/project/soul/access','POST','write'),('/api/student/narration-media/signed.token','GET','media')]:
            self.assertEqual(_route(method,path),bucket)
        self.assertIsNone(_route('POST','/api/narration/generate'))
        # Guests read the shared guide catalog only; there is no guest access/queue route.
        self.assertEqual(_route('GET','/api/public/narration/project'),'public')
        self.assertIsNone(_route('POST','/api/public/narration/project/soul/access'))
        self.assertIsNone(_route('GET','/api/public/narration/lesson/lesson'))
        self.assertTrue(_valid_body('/api/narration/project/soul/access',{}))
        self.assertFalse(_valid_body('/api/narration/project/soul/access',{'text':'arbitrary'}))

class NarrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.user={'id':'user','auth_version':2};self.lesson={'id':'lesson','title':'Урок','theory':[{'title':'Тема','content':'Текст урока'}]}
        self.access=patch('services.narration.require_student_lesson',new=AsyncMock(return_value=(self.user,self.lesson))).start()
        self.addCleanup(patch.stopall)
        patch.dict(os.environ,{'SECRET_KEY':'narration-test-only-secret-'*3}).start()
        self.service=NarrationService(SimpleNamespace(),root=self.root,public_url='https://media.example.org')
        self.item=lesson_clips(self.lesson)[1]
    def ready(self):
        folder=self.service.folder(self.item['hash']);folder.mkdir(parents=True,exist_ok=True)
        (folder/'audio.m4a').write_bytes(b'fake-test-aac')
        (folder/'ready.json').write_text(json.dumps({'hash':self.item['hash'],'seconds':20,'bytes':13,
            'sha256':hashlib.sha256(b'fake-test-aac').hexdigest()}))
        return folder
    async def token(self):return (await self.service.access('user','lesson','lesson','theory-0'))['url'].rsplit('/',1)[1]
    async def test_queue_deduplicates_and_cannot_inject_text(self):
        for _ in range(2):self.assertEqual((await self.service.access('user','lesson','lesson','theory-0'))['status'],'preparing')
        self.assertEqual(len(list((self.root/'jobs').glob('*.json'))),1)
        with self.assertRaises(HTTPException):await self.service.access('user','lesson','lesson','unknown')
    async def test_scheduled_retry_never_requires_manual_restart(self):
        folder=self.service.folder(self.item['hash']);folder.mkdir(parents=True)
        (folder/'failed.json').write_text('{"error":"word mismatch"}')
        (folder/'automatic-retry.json').write_text('{"used":7,"after":9999999999}')
        state=self.service.state(self.item)
        self.assertEqual(state['status'],'preparing');self.assertTrue(state['automatic_retry'])
        self.assertEqual(state['retry_at'],9999999999)
        (folder/'automatic-retry.json').write_text('{"used":7,"after":"invalid"}')
        self.assertEqual(self.service.state(self.item)['status'],'review')
    async def test_ready_catalog_and_token_preserve_scope(self):
        folder=self.ready();token=await self.token()
        self.assertEqual(await self.service.resolve(token),folder/'audio.m4a')
        catalog=await self.service.catalog('user','lesson','lesson')
        self.assertEqual(catalog['items'][1]['status'],'ready');self.assertIn('/narration-media/',catalog['items'][1]['url'])
    async def test_pronunciation_refresh_keeps_previous_selected_voice_until_ready(self):
        current=self.item
        self.item=lesson_clips(self.lesson,previous_pronunciation=True)[1]
        old_folder=self.ready()
        catalog=await self.service.catalog('user','lesson','lesson')
        old=catalog['items'][1]
        self.assertEqual(old['hash'],self.item['hash']);self.assertTrue(old['replacement_pending'])
        token=old['url'].rsplit('/',1)[1]
        self.assertEqual(await self.service.resolve(token),old_folder/'audio.m4a')
        self.item=current;self.ready()
        catalog=await self.service.catalog('user','lesson','lesson')
        self.assertEqual(catalog['items'][1]['hash'],current['hash'])
        self.assertNotIn('replacement_pending',catalog['items'][1])
        with self.assertRaises(HTTPException):await self.service.resolve(token)
    async def test_revoked_level_and_account_version_block_old_link(self):
        self.ready();token=await self.token();self.user['auth_version']=3
        with self.assertRaises(HTTPException):await self.service.resolve(token)
        self.user['auth_version']=2;self.access.side_effect=HTTPException(403,'Locked')
        with self.assertRaises(HTTPException):await self.service.resolve(token)
    async def test_updated_text_invalidates_old_audio(self):
        self.ready();token=await self.token();self.lesson['theory'][0]['content']='Изменённый урок'
        with self.assertRaises(HTTPException):await self.service.resolve(token)
        self.assertEqual((await self.service.catalog('user','lesson','lesson'))['items'][1]['status'],'missing')
    async def test_session_jwt_and_bad_scope_cannot_play(self):
        self.ready()
        bad=jwt.encode({'sub':'user','aud':'numerom-narration','exp':9999999999},os.environ['SECRET_KEY'],algorithm='HS256')
        with self.assertRaises(HTTPException):await self.service.resolve(bad)
        with self.assertRaises(HTTPException):await self.service.access('user','admin','lesson','theory-0')
    async def test_symlink_audio_and_missing_files_are_not_ready(self):
        folder=self.ready();(folder/'audio.m4a').unlink();other=self.root/'other';other.write_bytes(b'fake-test-aac');(folder/'audio.m4a').symlink_to(other)
        self.assertNotEqual(self.service.state(self.item)['status'],'ready')
    async def test_unavailable_lesson_never_queues_any_content(self):
        self.access.side_effect=HTTPException(403,'Locked')
        with self.assertRaises(HTTPException):await self.service.access('user','lesson','lesson','theory-0')
        self.assertFalse((self.root/'jobs').exists())


class GuestNarrationTests(unittest.IsolatedAsyncioTestCase):
    """Guests hear the shared guide; a guest link never opens a lesson, report or queues synthesis."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        source=self.root/'project.json'
        source.write_text(json.dumps({'items':[{'id':'soul','section':'numbers','title':'Число души','text':'Число души — внутренний мотив.'},
            {'id':'method','section':'schemes','title':'Как читать схемы','text':'Схема читается слева направо.'}]},ensure_ascii=False))
        patch.dict(os.environ,{'SECRET_KEY':'narration-test-only-secret-'*3}).start();self.addCleanup(patch.stopall)
        # No account is named "guest": a forged lesson/report scope finds no owner.
        db=SimpleNamespace(users=SimpleNamespace(find_one=AsyncMock(return_value=None)))
        self.service=NarrationService(db,root=self.root/'narration',project_source=source,public_url='https://media.example.org')
        self.soul=self.service.project_items()[0]
        folder=self.service.folder(self.soul['hash']);folder.mkdir(parents=True)
        (folder/'audio.m4a').write_bytes(b'fake-test-aac')
        (folder/'ready.json').write_text(json.dumps({'hash':self.soul['hash'],'seconds':20,'bytes':13,
            'sha256':hashlib.sha256(b'fake-test-aac').hexdigest()}))
    def guest_token(self,**changes):
        claims={'sub':'guest','scope':'public-project','source':'project','clip':'soul','hash':self.soul['hash'],
            'aud':'numerom-narration','exp':9999999999,**changes}
        return jwt.encode(claims,narration_key(),algorithm='HS256')
    async def test_catalog_links_ready_guide_audio_and_never_queues(self):
        items={i['id']:i for i in self.service.public_catalog()['items']}
        self.assertEqual(items['soul']['status'],'ready')
        self.assertTrue(items['soul']['url'].startswith('https://media.example.org/api/student/narration-media/'))
        self.assertEqual(items['method']['status'],'missing');self.assertNotIn('url',items['method'])
        self.assertFalse((self.root/'narration/jobs').exists())
        token=items['soul']['url'].rsplit('/',1)[1]
        self.assertEqual(await self.service.resolve(token),self.service.folder(self.soul['hash'])/'audio.m4a')
    async def test_guest_link_opens_nothing_but_shared_guide(self):
        for token in (self.guest_token(sub='user'),self.guest_token(source='lesson'),self.guest_token(clip='unknown'),
                      self.guest_token(hash='0'*64),self.guest_token(scope='lesson'),self.guest_token(scope='full-report')):
            with self.subTest(token=token[-12:]),self.assertRaises(HTTPException):await self.service.resolve(token)
