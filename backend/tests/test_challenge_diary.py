import asyncio
import os
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
import uuid
from unittest.mock import AsyncMock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from services.challenge_diary import ChallengeDiary,DiaryWrite,DiaryRestart,LegacyDiaryWrite,challenge_data,history_entry
from services.student_learning import StudentLearningService
from public_gateway import _route,_valid_body


def challenge():return {'id':'c','title':'Практика','description':'Наблюдения','duration_days':2,'daily_tasks':[{'day':n,'title':f'День {n}','description':'Внимание','tasks':['Запишите наблюдение']} for n in (1,2)]}

def write(progress,day=1,**kw):
    return DiaryWrite(request_id=uuid.uuid4(),attempt_id=progress['attempt_id'],revision=progress['revision'],day=day,note='Наблюдение',completed=True,**kw)


class ContractTests(unittest.TestCase):
    def test_history_normalizes_legacy_notes_without_exposing_internal_fields(self):
        row=history_entry({'id':'old','user_id':'private','requests':{'secret':'hash'},
                          'daily_notes':{'2':'Вторая запись','1':{'note':'Первая запись'},'invalid':'ignored'}})
        self.assertNotIn('user_id',row);self.assertNotIn('requests',row)
        self.assertEqual([(n['day'],n['note']) for n in row['daily_notes']],[(1,'Первая запись'),(2,'Вторая запись')])

    def test_models_and_gateway_only_accept_bounded_server_owned_input(self):
        valid={'request_id':str(uuid.uuid4()),'attempt_id':str(uuid.uuid4()),'revision':0,'day':1,'note':'Заметка','completed':True}
        self.assertTrue(_valid_body('/api/student/diary/lesson/c',valid))
        for patch in [{'points':500},{'completed':'yes'},{'day':True},{'note':'x'*4001},{'revision':-1}]:
            with self.assertRaises(ValidationError):DiaryWrite.model_validate({**valid,**patch})
        self.assertEqual(_route('GET','/api/student/diary/lesson/c'),'read')
        self.assertEqual(_route('POST','/api/student/diary/lesson/c/restart'),'write')
        self.assertFalse(_valid_body('/api/student/diary/lesson/c',{'note':'x'}))
        broken=challenge();broken['daily_tasks'][1]['day']=1
        with self.assertRaises(HTTPException):challenge_data({'challenge':broken},'c')


@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'),'isolated Mongo only')
class DiaryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mongo=AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL']);self.db=self.mongo['numerom_test_diary_'+uuid.uuid4().hex]
        await self.db.users.insert_many([{'id':'u','level':1,'credits_remaining':10},{'id':'other','level':1,'credits_remaining':10}])
        await self.db.lessons_v2.insert_one({'id':'lesson','title':'Урок','is_active':True,'level':1,'challenge':challenge()})
        self.service=ChallengeDiary(self.db)
    async def asyncTearDown(self):await self.mongo.drop_database(self.db.name);self.mongo.close()
    async def progress(self):return (await self.service.read('u','lesson','c'))['progress']
    async def balance(self):return (await self.db.users.find_one({'id':'u'}))['credits_remaining']

    async def test_read_is_free_and_note_is_not_completion(self):
        p=await self.progress();self.assertEqual(p['completed_days'],[])
        self.assertEqual(await self.db.challenge_progress.count_documents({}),0)
        req=write(p).model_copy(update={'completed':False})
        saved=await self.service.save('u','lesson','c',req)
        self.assertEqual(saved['progress']['completed_days'],[])
        self.assertEqual(saved['progress']['daily_notes'][0]['note'],'Наблюдение')
        self.assertEqual(await self.balance(),10)
        self.assertEqual((await self.service.read('other','lesson','c'))['progress']['daily_notes'],[])

    async def test_concurrent_retries_pay_once_then_complete_and_restart_once(self):
        first=write(await self.progress())
        replies=await asyncio.gather(*(self.service.save('u','lesson','c',first) for _ in range(12)))
        self.assertTrue(all(r['progress']['completed_days']==[1] for r in replies));self.assertEqual(await self.balance(),20)
        second=write(await self.progress(),day=2)
        await asyncio.gather(*(self.service.save('u','lesson','c',second) for _ in range(8)))
        p=await self.progress();self.assertTrue(p['is_completed']);self.assertEqual(p['points_earned'],70)
        self.assertEqual(await self.balance(),80)
        self.assertEqual(await self.db.credit_transactions.count_documents({'category':'challenge'}),2)
        restart=DiaryRestart(request_id=uuid.uuid4(),attempt_id=p['attempt_id'],revision=p['revision'])
        rows=await asyncio.gather(*(self.service.save('u','lesson','c',restart,restart=True) for _ in range(8)))
        self.assertEqual({r['progress']['attempt_number'] for r in rows},{2})
        self.assertEqual((await self.progress())['completed_days'],[]);self.assertEqual(await self.balance(),80)
        self.assertEqual(len(rows[0]['history']),1)
        with self.assertRaises(HTTPException):await self.service.save('u','lesson','c',second)

    async def test_outdated_device_and_changed_request_cannot_overwrite(self):
        p=await self.progress();one=write(p);await self.service.save('u','lesson','c',one)
        for request in [write(p,day=2),one.model_copy(update={'note':'Другой текст'})]:
            with self.assertRaises(HTTPException) as e:await self.service.save('u','lesson','c',request)
            self.assertEqual(e.exception.status_code,409)
        self.assertEqual((await self.progress())['daily_notes'][0]['note'],'Наблюдение');self.assertEqual(await self.balance(),20)
        edit=write(await self.progress()).model_copy(update={'completed':False,'note':'Дополнение'})
        p=(await self.service.save('u','lesson','c',edit))['progress'];self.assertEqual(p['completed_days'],[1]);self.assertEqual(await self.balance(),20)

    async def test_unknown_day_challenge_locked_lesson_and_empty_completion(self):
        p=await self.progress()
        for req in [write(p,day=3),write(p).model_copy(update={'note':'   '})]:
            with self.assertRaises(HTTPException) as e:await self.service.save('u','lesson','c',req)
            self.assertEqual(e.exception.status_code,422)
        with self.assertRaises(HTTPException):await self.service.read('u','lesson','wrong')
        await self.db.lessons_v2.update_one({'id':'lesson'},{'$set':{'level':2}})
        with self.assertRaises(HTTPException) as e:await self.service.read('u','lesson','c')
        self.assertEqual(e.exception.status_code,403);self.assertEqual(await self.balance(),10)

    async def test_archive_failure_keeps_note_credit_and_progress_then_retries(self):
        original=self.service.deliver;self.service.deliver=AsyncMock(side_effect=RuntimeError())
        request=write(await self.progress());result=await self.service.save('u','lesson','c',request)
        self.assertEqual(result['progress']['completed_days'],[1]);self.assertEqual(await self.balance(),20)
        self.assertEqual(await self.db.challenge_progress.count_documents({}),0)
        self.service.deliver=original;await self.service.save('u','lesson','c',request)
        self.assertEqual(await self.db.challenge_progress.count_documents({}),1)
        self.assertEqual(await self.db.credit_transactions.count_documents({}),1)
        self.assertEqual(await self.balance(),20)

    async def test_legacy_import_preserves_notes_without_repaying_completed_days(self):
        await self.db.challenge_progress.insert_one({'id':'old','user_id':'u','lesson_id':'lesson','challenge_id':'c','attempt_number':3,'completed_days':[1],
          'daily_notes':[{'day':1,'note':'Прежняя заметка'}],'points_earned':10,'is_completed':False})
        p=await self.progress();self.assertEqual(p['daily_notes'][0]['note'],'Прежняя заметка')
        await self.service.legacy_save('u',LegacyDiaryWrite(lesson_id='lesson',challenge_id='c',day=1,note='Новая запись',completed=True))
        self.assertEqual(await self.balance(),10);self.assertEqual(await self.db.challenge_progress.count_documents({}),1)
        self.assertEqual((await self.service.legacy_read('u','lesson','c'))['attempt_number'],3)
        self.assertEqual((await self.progress())['daily_notes'][0]['note'],'Новая запись')

    async def test_completion_participates_in_lesson_progress_and_lesson_reward_is_once(self):
        learning=StudentLearningService(self.db);await learning.mark_theory('u','lesson')
        self.assertEqual((await learning.progress('u','lesson'))['completion_percentage'],50)
        await self.service.save('u','lesson','c',write(await self.progress()))
        last=write(await self.progress(),day=2);await self.service.save('u','lesson','c',last)
        self.assertEqual((await learning.progress('u','lesson'))['completion_percentage'],100)

        self.assertEqual(await self.balance(),130)
        await self.service.save('u','lesson','c',last);self.assertEqual(await self.balance(),130)
        p=await self.progress();await self.service.save('u','lesson','c',DiaryRestart(request_id=uuid.uuid4(),attempt_id=p['attempt_id'],revision=p['revision']),restart=True)
        self.assertEqual((await learning.progress('u','lesson'))['completion_percentage'],100)

    async def test_same_request_uuid_in_different_lessons_has_separate_archives_and_rewards(self):
        await self.db.lessons_v2.insert_one({'id':'second','title':'Другой урок','is_active':True,'level':1,'challenge':challenge()})
        first=write(await self.progress())
        second_progress=(await self.service.read('u','second','c'))['progress']
        second=write(second_progress).model_copy(update={'request_id':first.request_id})
        await self.service.save('u','lesson','c',first)
        await self.service.save('u','second','c',second)
        self.assertEqual(await self.db.challenge_progress.count_documents({}),2)
        self.assertEqual(await self.db.credit_transactions.count_documents({}),2)
        self.assertEqual(await self.balance(),30)
