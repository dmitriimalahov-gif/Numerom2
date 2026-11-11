import asyncio,os,sys,unittest,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException
from services.mobile_admin import MobileAdmin,LessonChange,ConsultationChange,SettingsChange,ReviewChange,LevelChange
from routers.mobile_admin import create_mobile_admin_router
from public_gateway import _route,_valid_body
class Contract(unittest.TestCase):
 def test_routes_are_bounded_and_register(self):
  paths={r.path for r in create_mobile_admin_router(__import__('types').SimpleNamespace(users=None)).routes}
  self.assertTrue({'/api/admin/mobile/responses','/api/admin/mobile/challenge-notes','/api/admin/mobile/lessons/import/preview','/api/admin/mobile/lessons/{identity}/archive'}<=paths)
  self.assertEqual(_route('GET','/api/admin/mobile/responses'),'read')
  self.assertIsNone(_route('DELETE','/api/admin/mobile/lessons/l'))
  self.assertFalse(_valid_body('/api/admin/mobile/settings/costs',{'values':{'personal_numbers':-1}}))
@unittest.skipUnless(os.getenv('NUMEROM_TEST_MONGO_URL'),'isolated Mongo only')
class MobileAdminTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  self.client=AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL']);self.db=self.client['numerom_test_mobile_admin_'+uuid.uuid4().hex]
  await self.db.users.insert_many([{'id':'admin','is_admin':True,'level':1},{'id':'root','is_super_admin':True,'level':1},{'id':'u','level':1,'credits_remaining':10}]);self.s=MobileAdmin(self.db)
 async def asyncTearDown(self):await self.client.drop_database(self.db.name);self.client.close()
 def meta(self,revision=0):return {'request_id':uuid.uuid4(),'revision':revision,'reason':'Проверка редактора'}
 def lesson(self,**values):return LessonChange(**{**self.meta(),'title':'Урок','description':'Описание','level':1,'order':1,'is_active':True,**values})
 async def test_student_cannot_read_or_edit_admin_content(self):
  for call in [lambda:self.s.lessons('u'),lambda:self.s.responses('u'),lambda:self.s.read_settings('u','costs'),lambda:self.s.lesson('u','x',self.lesson())]:
   with self.assertRaises(HTTPException) as e:await call()
   self.assertEqual(e.exception.status_code,403)
  self.assertEqual(await self.db.lessons_v2.count_documents({}),0)
 async def test_lesson_save_retry_archive_and_stale_edit(self):
  req=self.lesson(theory=[{'title':'Тема','content':'Пример'}]);await self.s.lesson('admin','l',req)
  await self.s.lesson('admin','l',req);self.assertEqual(await self.db.lessons_v2.count_documents({}),1)
  row=(await self.s.lessons('admin'))['lessons'][0];self.assertEqual(row['revision'],1)
  with self.assertRaises(HTTPException):await self.s.lesson('admin','l',self.lesson())
  await self.s.lesson('admin','l',self.lesson(revision=1,is_active=False))
  self.assertFalse((await self.db.lessons_v2.find_one({'id':'l'}))['is_active'])
 async def test_review_cannot_apply_to_newer_answer_or_draft_attachment(self):
  await self.db.exercise_responses.insert_many([{'id':'r','user_id':'u','response_text':'Первая версия','submitted_at':'one'}, {'id':'private','attachment_draft_only':True}])
  rows=(await self.s.responses('admin'))['responses'];self.assertEqual(len(rows),1)
  req=ReviewChange(**self.meta(),admin_comment='Поясните пример',expected_answer=rows[0]['expected_answer'])
  await self.db.exercise_responses.update_one({'id':'r'},{'$set':{'response_text':'Новая версия'}})
  with self.assertRaises(HTTPException):await self.s.review('admin','r',req)
  row=(await self.s.responses('admin'))['responses'][0]
  req=ReviewChange(**self.meta(),admin_comment='Принято',expected_answer=row['expected_answer']);await self.s.review('admin','r',req);await self.s.review('admin','r',req)
  self.assertEqual((await self.db.users.find_one({'id':'u'}))['credits_remaining'],10)
 async def test_settings_reject_unknown_and_excessive_rewards_and_retry(self):
  for kind,values in [('learning',{'quiz_points_per_attempt':1001}),('costs',{'unknown':2})]:
   with self.assertRaises(HTTPException):await self.s.write_settings('admin',kind,SettingsChange(**self.meta(),values=values))
  req=SettingsChange(**self.meta(),values={'personal_numbers':7});await self.s.write_settings('admin','costs',req);await self.s.write_settings('admin','costs',req)
  state=await self.s.read_settings('admin','costs');self.assertEqual(state['values']['personal_numbers'],7);self.assertEqual(state['revision'],1)
 async def test_consultation_requires_real_student_and_retains_private_media(self):
  body=ConsultationChange(**self.meta(),title='Консультация',assigned_user_id='u',cost_credits=2,is_active=True)
  await self.s.consultation('admin','c',body)
  await self.db.personal_consultations.update_one({'id':'c'},{'$set':{'pdf_file_id':'private-pdf'}})
  await self.s.consultation('admin','c',body.model_copy(update={**self.meta(1),'title':'Новое название'}))
  self.assertEqual((await self.db.personal_consultations.find_one({'id':'c'}))['pdf_file_id'],'private-pdf')
  with self.assertRaises(HTTPException):await self.s.consultation('admin','other',body.model_copy(update={'assigned_user_id':'missing'}))
 async def test_level_change_refuses_stale_and_protected_admin_account(self):
  req=LevelChange(level=2,expected_level=1,reason='Открыть следующий модуль');await self.s.level('admin','u',req)
  with self.assertRaises(HTTPException):await self.s.level('admin','u',req)
  with self.assertRaises(HTTPException):await self.s.level('admin','root',req)
 async def test_content_edit_retains_ids_and_legacy_fields_and_does_not_award(self):
  await self.db.lessons_v2.insert_one({'id':'l','title':'Old','theory':[{'id':'t','title':'T','content':'Old','legacy':'keep'}],
   'exercises':[{'id':'e','title':'E','legacy':'keep'}],
   'quiz':{'id':'q','time_limit_minutes':15,'questions':[{'id':'q1','hint':'keep'}]},
   'challenge':{'id':'c','daily_tasks':[{'day':1,'legacy':'keep'}]}})
  body=self.lesson(theory=[{'id':'t','title':'T','content':'New'}],exercises=[{'id':'e','title':'E','type':'reflection'}],
   quiz={'id':'q','title':'Q','questions':[{'id':'q1','question':'Выберите','options':['Да','Нет'],'correct_answer':'Да'}]},
   challenge={'id':'c','title':'C','duration_days':1,'daily_tasks':[{'day':1,'title':'D','tasks':['Наблюдать']}]})
  await self.s.lesson('admin','l',body);await self.s.lesson('admin','l',body)
  row=await self.db.lessons_v2.find_one({'id':'l'})
  self.assertEqual(row['theory'][0]['id'],'t');self.assertEqual(row['theory'][0]['legacy'],'keep')
  self.assertEqual(row['exercises'][0]['legacy'],'keep');self.assertEqual(row['quiz']['questions'][0]['hint'],'keep')
  self.assertEqual(row['quiz']['time_limit_minutes'],15);self.assertEqual(row['challenge']['daily_tasks'][0]['legacy'],'keep')
  self.assertEqual((await self.db.users.find_one({'id':'u'}))['credits_remaining'],10)
  self.assertEqual(await self.db.quiz_attempts.count_documents({}),0)

class ContentValidation(unittest.TestCase):
 def test_quiz_rejects_ungradable_questions_duplicate_ids_and_bad_weights(self):
  from pydantic import ValidationError
  from services.mobile_admin import QuizChange
  base={'id':'q','title':'Тест','questions':[{'id':'a','question':'Что?','options':['Да','Нет'],'correct_answer':'Да'}]}
  for patch in [{'correct_answer':'Иное'},{'options':['Да','Да']},{'points':0},{'points':101},{'type':'true_false','options':['Да','Нет','Может быть']},{'question':' '}]:
   with self.assertRaises(ValidationError):QuizChange(**{**base,'questions':[{**base['questions'][0],**patch}]})
  with self.assertRaises(ValidationError):QuizChange(**{**base,'questions':base['questions']*2})
  self.assertEqual(QuizChange(**base).questions[0].correct_answer,'Да')
 def test_challenge_requires_exact_days(self):
  from pydantic import ValidationError
  from services.mobile_admin import ChallengeChange
  base={'id':'c','title':'Дневник','duration_days':2,'daily_tasks':[{'day':1,'title':'Один'},{'day':2,'title':'Два'}]}
  self.assertEqual(len(ChallengeChange(**base).daily_tasks),2)
  for days in [[{'day':1,'title':'Один'}],[{'day':1,'title':'Один'},{'day':1,'title':'Два'}],[{'day':1,'title':'Один'},{'day':3,'title':'Три'}]]:
   with self.assertRaises(ValidationError):ChallengeChange(**{**base,'daily_tasks':days})
