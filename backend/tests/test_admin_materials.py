import asyncio,base64,os,sys,tempfile,unittest,uuid
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from services.admin_materials import AdminMaterials,MaterialUpload,MaterialChange
from services.student_media import StudentMediaService
from services.student_learning import StudentLearningService
from services.mobile_admin import LessonChange,MobileAdmin
@unittest.skipUnless(os.getenv('NUMEROM_TEST_MONGO_URL'),'isolated Mongo only')
class AdminMaterialsTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  self.client=AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL']);self.db=self.client['numerom_test_admin_materials_'+uuid.uuid4().hex];self.directory=tempfile.TemporaryDirectory();self.s=AdminMaterials(self.db,self.directory.name)
  await self.db.users.insert_many([{'id':'admin','is_admin':True},{'id':'student','level':1},{'id':'higher','level':3}]);await self.db.lessons_v2.insert_one({'id':'l','title':'Урок','is_active':True,'level':1})
 async def asyncTearDown(self):await self.client.drop_database(self.db.name);self.client.close();self.directory.cleanup()
 def upload(self,**values):return MaterialUpload(**{'request_id':uuid.uuid4(),'name':'Материал.pdf','content_base64':base64.b64encode(b'%PDF-1.4\nexample\n%%EOF').decode(),'section':'theory','reason':'Учебный материал',**values})
 def change(self,**values):return MaterialChange(**{'request_id':uuid.uuid4(),'revision':0,'reason':'Опубликовать материал','name':'Практика','section':'exercises','is_active':True,**values})
 async def test_upload_replays_and_stays_private_until_published(self):
  request=self.upload();results=await asyncio.gather(*[self.s.upload('admin','l',request) for _ in range(3)]);self.assertEqual(len({r['file']['id'] for r in results}),1)
  row=await self.db.files.find_one({});self.assertTrue(row['private_material']);self.assertFalse(row['is_active']);self.assertNotIn('stored_name',results[0]['file'])
  files=await StudentLearningService(self.db).files('student','l');self.assertEqual(files['files'],[])
  media=StudentMediaService(self.db,Path(self.directory.name)/'legacy',private_root=self.directory.name)
  with self.assertRaises(HTTPException):await media.file('student','l',row['id'])
  self.assertTrue((await media.file('admin','l',row['id']))[2].is_file())
  await self.s.change('admin','l',row['id'],self.change());self.assertEqual(len((await StudentLearningService(self.db).files('student','l'))['files']),1)
  self.assertEqual((await media.file('student','l',row['id']))[2].read_bytes(),b'%PDF-1.4\nexample\n%%EOF')
  self.assertFalse(list(Path(self.directory.name).glob('.upload-*')))
  with self.assertRaises(HTTPException):await self.s.upload('admin','l',request.model_copy(update={'name':'other.pdf'}))
 async def test_student_and_wrong_lesson_cannot_manage_and_hide_revokes_access(self):
  with self.assertRaises(HTTPException):await self.s.upload('student','l',self.upload())
  value=(await self.s.upload('admin','l',self.upload()))['file'];identity=value['id'];await self.s.change('admin','l',identity,self.change())
  with self.assertRaises(HTTPException):await self.s.change('student','l',identity,self.change(revision=1))
  with self.assertRaises(HTTPException):await self.s.change('admin','missing',identity,self.change(revision=1))
  media=StudentMediaService(self.db,self.directory.name,'https://media.example.test',private_root=self.directory.name)
  with patch.dict(os.environ,{'SECRET_KEY':'synthetic-material-test-key-'*3}):
   token=(await media.access('student','l',identity))['url'].rsplit('/',1)[1]
   await self.s.change('admin','l',identity,self.change(revision=1,is_active=False))
   with self.assertRaises(HTTPException):await media.resolve(token)
  with self.assertRaises(HTTPException):await media.file('student','l',identity)
  await self.db.lessons_v2.update_one({'id':'l'},{'$set':{'is_active':False}})
  self.assertTrue((await media.file('admin','l',identity))[2].is_file())
  self.assertEqual(len(list(Path(self.directory.name).iterdir())),1)
 async def test_disk_failure_does_not_publish_metadata_and_cleans_tempfile(self):
  with patch('services.admin_materials.os.link',side_effect=OSError('simulated disk failure')):
   with self.assertRaises(OSError):await self.s.upload('admin','l',self.upload())
  self.assertEqual(await self.db.files.count_documents({}),0)
  self.assertEqual(list(Path(self.directory.name).iterdir()),[])
 async def test_video_url_is_exposed_without_private_answers(self):
  body=LessonChange(request_id=uuid.uuid4(),revision=0,reason='Добавить видео',title='Урок',level=1,order=0,is_active=True,video_url='https://video.example.test/lesson')
  await MobileAdmin(self.db).lesson('admin','l',body)
  from services.student_learning import _safe_lesson
  row=_safe_lesson(await self.db.lessons_v2.find_one({'id':'l'}));self.assertEqual(row['video_url'],'https://video.example.test/lesson');self.assertEqual(row['video_platform'],'external')
