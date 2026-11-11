import asyncio,json,os,sys,unittest,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from services.learning_drafts import LearningDrafts,QuizDraftWrite,DiaryDraftWrite
from services.challenge_diary import ChallengeDiary,DiaryWrite,DiaryRestart
from services.student_learning import StudentLearningService,QuizSubmission
from routers.learning_drafts import create_learning_drafts_router
from public_gateway import _route,_valid_body

class ContractTests(unittest.TestCase):
 def test_reviewed_routes_register_and_validate(self):
  self.assertEqual(len(create_learning_drafts_router(None).routes),4)
  for path in ['/api/student/quiz-drafts/lesson/q',f'/api/student/diary-drafts/lesson/c/{uuid.uuid4()}/1']:
   self.assertEqual(_route('GET',path),'read');self.assertEqual(_route('POST',path),'draft')
   self.assertTrue(_valid_body(path,{'request_id':str(uuid.uuid4()),'revision':0,'text':None}))
   self.assertFalse(_valid_body(path,{'request_id':str(uuid.uuid4()),'revision':0,'text':'x','user_id':'other'}))

@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'),'isolated Mongo only')
class LearningDraftTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  self.client=AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL']);self.db=self.client['numerom_test_learning_work_'+uuid.uuid4().hex]
  await self.db.users.insert_many([{'id':u,'level':1,'credits_remaining':10} for u in ('u','other')])
  await self.db.lessons_v2.insert_one({'id':'l','is_active':True,'level':1,'quiz':{'id':'q','questions':[{'id':'one','type':'multiple_choice','options':['A','B'],'correct_answer':'B'}]},'challenge':{'id':'c','duration_days':1,'daily_tasks':[{'day':1,'tasks':['Заметка']}]}})
  self.service=LearningDrafts(self.db)
 async def asyncTearDown(self):await self.client.drop_database(self.db.name);self.client.close()
 def quiz_body(self,**patch):
  work={'submission_id':str(uuid.uuid4()),'answers':{'one':'B'},'index':0,'stage':'editing',**patch}
  return QuizDraftWrite(request_id=uuid.uuid4(),revision=0,text=json.dumps(work))
 async def test_quiz_resume_is_private_and_does_not_grade(self):
  req=self.quiz_body();result=await self.service.quiz('u','l','q',req)
  self.assertEqual(result['text'],req.text);self.assertIsNone((await self.service.quiz('other','l','q'))['text'])
  self.assertEqual(await self.db.quiz_attempts.count_documents({}),0)
  self.assertEqual((await self.db.users.find_one({'id':'u'}))['credits_remaining'],10)
 async def test_pending_quiz_retries_same_final_submission_after_reload(self):
  req=self.quiz_body(stage='submitting');await self.service.quiz('u','l','q',req)
  restored=json.loads((await self.service.quiz('u','l','q'))['text'])
  final=QuizSubmission(lesson_id='l',quiz_id='q',submission_id=restored['submission_id'],answers=restored['answers'])
  service=StudentLearningService(self.db)
  await service.submit_quiz('u',final);await service.submit_quiz('u',final)
  self.assertEqual(await self.db.quiz_attempts.count_documents({}),1)
  self.assertEqual(await self.db.credit_transactions.count_documents({'category':'quiz'}),1)
 async def test_changed_questions_and_locked_lessons_reject_draft_write(self):
  for patch in ({'answers':{'hidden':'B'}},{'index':1},{'answers':{'one':'Z'}},{'stage':'submitting','answers':{}}):
   with self.assertRaises(HTTPException):await self.service.quiz('u','l','q',self.quiz_body(**patch))
  await self.db.lessons_v2.update_one({'id':'l'},{'$set':{'level':2}})
  with self.assertRaises(HTTPException) as e:await self.service.quiz('u','l','q')
  self.assertEqual(e.exception.status_code,403)
 async def test_diary_draft_bound_to_day_and_attempt_without_reward(self):
  diary=ChallengeDiary(self.db);p=(await diary.read('u','l','c'))['progress']
  request=DiaryDraftWrite(request_id=uuid.uuid4(),revision=0,text='Личное наблюдение')
  rows=await asyncio.gather(*(self.service.diary('u','l','c',p['attempt_id'],1,request) for _ in range(8)))
  self.assertEqual({r['revision'] for r in rows},{1});self.assertEqual((await diary.read('u','l','c'))['progress']['completed_days'],[])
  self.assertEqual(await self.db.credit_transactions.count_documents({}),0)
  with self.assertRaises(HTTPException):await self.service.diary('u','l','c',p['attempt_id'],2,request)
  saved=await diary.save('u','l','c',DiaryWrite(request_id=uuid.uuid4(),attempt_id=p['attempt_id'],revision=0,day=1,note=request.text,completed=True))
  p2=saved['progress'];await diary.save('u','l','c',DiaryRestart(request_id=uuid.uuid4(),attempt_id=p2['attempt_id'],revision=p2['revision']),restart=True)
  with self.assertRaises(HTTPException):await self.service.diary('u','l','c',p['attempt_id'],1,request)
