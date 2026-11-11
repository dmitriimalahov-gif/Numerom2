import asyncio
import os
import sys
import unittest
import uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from services.exercise_drafts import DraftWrite,ExerciseDrafts
from routers.exercise_drafts import create_exercise_drafts_router
from public_gateway import _route,_valid_body


class ContractTests(unittest.TestCase):
    def test_router_registers_read_and_write_paths(self):
        router=create_exercise_drafts_router(None)
        self.assertEqual([r.methods for r in router.routes],[{'GET'},{'POST'}])

    def test_gateway_bounds_and_null_clear(self):
        path='/api/student/exercise-drafts/lesson/exercise'
        self.assertEqual(_route('POST',path),'draft');self.assertEqual(_route('GET',path),'read')
        body={'request_id':str(uuid.uuid4()),'revision':0,'text':None}
        self.assertTrue(_valid_body(path,body))
        for patch in [{'text':'x'*10001},{'revision':False},{'user_id':'victim'},{'text':42}]:
            self.assertFalse(_valid_body(path,{**body,**patch}))


@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'),'isolated Mongo only')
class DraftTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mongo=AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL']);self.db=self.mongo['numerom_test_draft_'+uuid.uuid4().hex]
        await self.db.users.insert_many([{'id':u,'level':1,'credits_remaining':10} for u in ('u','other')])
        await self.db.lessons_v2.insert_one({'id':'lesson','is_active':True,'level':1,'exercises':[{'id':'ex'}]})
        self.service=ExerciseDrafts(self.db)
    async def asyncTearDown(self):await self.mongo.drop_database(self.db.name);self.mongo.close()
    def request(self,revision=0,text='Мой ответ'):return DraftWrite(request_id=uuid.uuid4(),revision=revision,text=text)
    async def save(self,request):return await self.service.save('u','lesson','ex',request)

    async def test_private_durable_draft_does_not_submit_or_award(self):
        self.assertIsNone((await self.service.read('u','lesson','ex'))['text'])
        await self.save(self.request())
        self.assertEqual((await ExerciseDrafts(self.db).read('u','lesson','ex'))['text'],'Мой ответ')
        self.assertIsNone((await self.service.read('other','lesson','ex'))['text'])
        self.assertEqual((await self.db.users.find_one({'id':'u'}))['credits_remaining'],10)
        for name in ('exercise_responses','lesson_progress','credit_transactions'):
            self.assertEqual(await self.db[name].count_documents({}),0)

    async def test_retry_and_concurrent_first_save_are_one_revision(self):
        req=self.request();rows=await asyncio.gather(*(self.save(req) for _ in range(12)))
        self.assertEqual({r['revision'] for r in rows},{1});self.assertEqual(await self.db.exercise_drafts.count_documents({}),1)
        with self.assertRaises(HTTPException) as e:await self.save(req.model_copy(update={'text':'Другой'}))
        self.assertEqual(e.exception.status_code,409)

    async def test_stale_edit_and_clear_cannot_erase_newer_draft(self):
        await self.save(self.request());await self.save(self.request(1,'Новая версия'))
        for request in (self.request(1,None),self.request(0,'Старая версия')):
            with self.assertRaises(HTTPException) as e:await self.save(request)
            self.assertEqual(e.exception.status_code,409)
        self.assertEqual((await self.service.read('u','lesson','ex'))['text'],'Новая версия')
        cleared=await self.save(self.request(2,None));self.assertIsNone(cleared['text']);self.assertEqual(cleared['revision'],3)

    async def test_access_to_lesson_and_exercise_is_rechecked(self):
        with self.assertRaises(HTTPException):await self.service.read('u','lesson','missing')
        await self.db.lessons_v2.update_one({'id':'lesson'},{'$set':{'level':2}})
        with self.assertRaises(HTTPException) as e:await self.save(self.request())
        self.assertEqual(e.exception.status_code,403)
        self.assertEqual(await self.db.exercise_drafts.count_documents({}),0)
