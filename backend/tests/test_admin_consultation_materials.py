import asyncio,base64,os,sys,tempfile,unittest,uuid
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from services.admin_consultation_materials import AdminConsultationMaterials,ConsultationMaterialUpload
from services.mobile_admin import MobileAdmin,ConsultationChange
from services.consultations import Consultations
PDF=b'%PDF-1.4\nsynthetic consultation\n%%EOF'
@unittest.skipUnless(os.getenv('NUMEROM_TEST_MONGO_URL'),'isolated Mongo only')
class AdminConsultationMaterialsTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  self.secret=patch.dict(os.environ,{'SECRET_KEY':'synthetic-consultation-key-'*3});self.secret.start()
  self.client=AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL']);self.db=self.client['numerom_test_consult_pdf_'+uuid.uuid4().hex];self.temp=tempfile.TemporaryDirectory();self.s=AdminConsultationMaterials(self.db,self.temp.name)
  self.media=Consultations(self.db,Path(self.temp.name)/'legacy','https://media.example.test',private_root=self.temp.name)
  await self.db.users.insert_many([{'id':'admin','is_admin':True},{'id':'student','credits_remaining':10},{'id':'other','credits_remaining':10}])
  await self.db.personal_consultations.insert_many([{'id':'c','title':'Разбор','assigned_user_id':'student','is_active':True,'cost_credits':5},{'id':'other','assigned_user_id':'other','is_active':True,'cost_credits':0}])
 async def asyncTearDown(self):await self.client.drop_database(self.db.name);self.client.close();self.temp.cleanup();self.secret.stop()
 def upload(self,**values):return ConsultationMaterialUpload(**{'request_id':uuid.uuid4(),'name':'Разбор.pdf','content_base64':base64.b64encode(PDF).decode(),'reason':'Готовый персональный разбор',**values})
 def edit(self,**values):return ConsultationChange(**{'request_id':uuid.uuid4(),'revision':0,'title':'Разбор','assigned_user_id':'student','cost_credits':5,'is_active':True,'reason':'Добавить PDF',**values})
 async def test_upload_is_idempotent_draft_and_publish_requires_same_consultation(self):
  request=self.upload();results=await asyncio.gather(*(self.s.upload('admin','c',request) for _ in range(3)));fid=results[0]['file']['id']
  self.assertEqual(len({r['file']['id'] for r in results}),1);self.assertEqual(await self.db.files.count_documents({}),1)
  self.assertNotIn('pdf_file_id',await self.db.personal_consultations.find_one({'id':'c'}))
  with self.assertRaises(HTTPException):await self.s.upload('student','c',self.upload())
  with self.assertRaises(HTTPException):await self.s.upload('admin','c',request.model_copy(update={'name':'Other.pdf'}))
  with self.assertRaises(HTTPException):await MobileAdmin(self.db).consultation('admin','other',self.edit(pdf_file_id=fid))
  await MobileAdmin(self.db).consultation('admin','c',self.edit(pdf_file_id=fid))
  with self.assertRaises(HTTPException):await self.media.access('student','c','pdf')
  await self.media.purchase('student','c',5)
  token=(await self.media.access('student','c','pdf'))['url'].rsplit('/',1)[1]
  self.assertEqual((await self.media.resolve(token))[0].read_bytes(),PDF)
  with self.assertRaises(HTTPException):await self.media.access('other','c','pdf')
  await MobileAdmin(self.db).consultation('admin','c',self.edit(revision=1,pdf_file_id=None))
  with self.assertRaises(HTTPException):await self.media.resolve(token)
  self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],5)
 async def test_admin_preview_requires_current_role_and_does_not_grant_student_access(self):
  fid=(await self.s.upload('admin','c',self.upload()))['file']['id']
  token=(await self.media.admin_access('admin','c',fid))['url'].rsplit('/',1)[1]
  self.assertEqual((await self.media.resolve(token))[0].read_bytes(),PDF)
  with self.assertRaises(HTTPException):await self.media.admin_access('student','c',fid)
  with self.assertRaises(HTTPException):await self.media.admin_access('admin','other',fid)
  with self.assertRaises(HTTPException):await self.media.access('student','c','pdf')
  await self.db.users.update_one({'id':'admin'},{'$set':{'is_admin':False}})
  with self.assertRaises(HTTPException):await self.media.resolve(token)
 async def test_pdf_only_and_atomic_failure_leave_no_metadata(self):
  with patch('services.admin_consultation_materials.validate_file',return_value=(b'png','image/png','image.png')):
   with self.assertRaises(HTTPException):await self.s.upload('admin','c',self.upload())
  with patch('services.admin_materials.os.link',side_effect=OSError('disk failed')):
   with self.assertRaises(OSError):await self.s.upload('admin','c',self.upload())
  self.assertEqual(await self.db.files.count_documents({}),0);self.assertEqual(list(Path(self.temp.name).iterdir()),[])
