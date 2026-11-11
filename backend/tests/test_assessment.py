import asyncio
import copy
import os
import sys
import unittest
import uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from domain.assessment import AssessmentRequest, public_questions, build_assessment, narration, THEMES
from services.assessment import Assessment
from quiz_data import NUMEROLOGY_QUIZ


def body(index=0, **changes):
    return {'kind':'assessment','request_id':str(uuid.uuid4()),'expected_cost':1,
        'answers':{q['id']:q['options'][index]['id'] for q in public_questions()},**changes}


class DomainTests(unittest.TestCase):
    def test_ten_visible_questions_have_no_scoring_values(self):
        before=copy.deepcopy(NUMEROLOGY_QUIZ)
        questions=public_questions();self.assertEqual(len(questions),10)
        self.assertTrue(all(len(q['options'])==9 and all(set(o)=={'id','text'} for o in q['options']) for q in questions))
        self.assertEqual(before,NUMEROLOGY_QUIZ)
    def test_all_nine_themes_match_visible_choices_and_narration(self):
        for index in range(9):
            result=build_assessment(AssessmentRequest(**body(index)))
            self.assertEqual(result['number'],index+1);self.assertEqual(result['total'],(index+1)*10)
            self.assertEqual(result['frequencies'][index]['count'],10)
            self.assertEqual(result['leaders'],[index+1]);self.assertIsNone(result['tie_note'])
            self.assertIn(result['interpretation'],narration(index+1));self.assertIn(result['focus'],narration(index+1))
            self.assertEqual(result['narration_id'],f'assessment-result-{index+1}')
    def test_tie_resolves_in_question_order_not_client_json_order(self):
        questions=public_questions()
        answers={q['id']:q['options'][0 if int(q['id'])<=5 else 1]['id'] for q in reversed(questions)}
        result=build_assessment(AssessmentRequest(**body(answers=answers)))
        self.assertEqual(result['number'],1);self.assertEqual(result['leaders'],[1,2]);self.assertTrue(result['tie_note'])
    def test_forged_incomplete_or_extra_choices_are_rejected(self):
        request=body()
        for answers in ({},dict(list(request['answers'].items())[:-1]),{**request['answers'],'1':'a'*20},{**request['answers'],'11':'b'*20}):
            with self.assertRaises(ValidationError):AssessmentRequest(**{**request,'answers':answers})
        with self.assertRaises(ValidationError):AssessmentRequest(**{**request,'score':100})


@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'),'isolated Mongo only')
class ServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mongo=AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL']);self.db=self.mongo['numerom_test_assessment_'+uuid.uuid4().hex]
        await self.db.users.insert_many([{'id':uid,'level':1,'credits_remaining':10} for uid in ('owner','other')])
        self.service=Assessment(self.db)
    async def asyncTearDown(self):await self.mongo.drop_database(self.db.name);self.mongo.close()
    async def test_concurrent_retries_create_one_receipt_and_one_charge(self):
        request=AssessmentRequest(**body());results=await asyncio.gather(*(self.service.calculate('owner',request) for _ in range(10)))
        self.assertEqual(len({r['id'] for r in results}),1);self.assertTrue(all(r['results']['number']==1 for r in results))
        self.assertEqual((await self.db.users.find_one({'id':'owner'}))['credits_remaining'],9)
        self.assertEqual(await self.db.numerology_calculations.count_documents({'user_id':'owner'}),1)
        self.assertEqual(await self.db.credit_transactions.count_documents({'user_id':'owner'}),1)
        self.assertEqual(len((await self.service.history('owner'))['calculations']),1)
        self.assertEqual((await self.service.history('other'))['calculations'],[])
    async def test_changed_request_or_price_cannot_charge(self):
        request=AssessmentRequest(**body());await self.service.calculate('owner',request)
        with self.assertRaises(HTTPException) as caught:await self.service.calculate('owner',AssessmentRequest(**body(1,request_id=request.request_id)))
        self.assertEqual(caught.exception.status_code,409)
        with self.assertRaises(HTTPException):await self.service.calculate('owner',AssessmentRequest(**body(expected_cost=2)))
        self.assertEqual((await self.db.users.find_one({'id':'owner'}))['credits_remaining'],9)
    async def test_saved_result_survives_price_change_and_disabled_user_is_denied(self):
        request=AssessmentRequest(**body());first=await self.service.calculate('owner',request)
        await self.db.credits_deduction_config.insert_one({'is_active':True,'quiz_completion':100})
        self.assertEqual(first,await self.service.calculate('owner',request))
        await self.db.users.update_one({'id':'owner'},{'$set':{'is_disabled':True}})
        with self.assertRaises(HTTPException):await self.service.history('owner')
