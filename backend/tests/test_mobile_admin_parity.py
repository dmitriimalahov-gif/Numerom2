import ast
import asyncio
import os
import sys
import unittest
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from fastapi import Depends, HTTPException, FastAPI
from routers.mobile_admin import create_mobile_admin_router
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from auth import get_current_user
from services.mobile_admin import (MobileAdmin, ReviewChange, SettingsChange, LessonChange,
    ConsultationChange, ImportPreview, LessonImport, ArchiveChange, LegacyReview)
from services.mobile_admin_settings import settings_spec, validate_settings
from services.mobile_admin_import import lesson_preview
from services.mobile_admin_learning import deliver_review_award
from services.credit_history import flush_pending_credit_transactions
from services.student_learning import require_student_lesson


class ValidationTests(unittest.TestCase):
    def test_all_four_specs_have_labels_and_valid_defaults(self):
        for kind in ('learning','costs','planetary-energy','monthly-route'):
            _,defaults,fields=settings_spec(kind)
            self.assertEqual(validate_settings(kind,defaults),defaults)
            self.assertEqual(set(defaults),set(fields))
            self.assertTrue(all(f['label'] and f['type'] in ('integer','number','boolean') for f in fields.values()))
            self.assertNotIn('is_active',defaults);self.assertNotIn('version',defaults)
    def test_strict_numeric_types_finiteness_and_interdependent_thresholds(self):
        for kind,patches in {
            'learning':[{'quiz_points_per_attempt':True},{'quiz_points_per_attempt':'2'},{'quiz_points_per_attempt':2.1},{'quiz_points_per_attempt':1001}],
            'costs':[{'personal_numbers':-1},{'personal_numbers':float('nan')}],
            'planetary-energy':[{'anti_cyclicity_enabled':1},{'friend_planet_bonus':True},{'friend_planet_bonus':float('inf')},{'normalization_min':90},{'normalization_min':1.0},{'energy_floor_multiplier':1,'energy_cap_multiplier':1}],
            'monthly-route':[{'challenging_day_threshold':70},{'completion_energy_min':60},{'transit_low_threshold':90},{'many_favorable_days_threshold':8},{'optimal_start_min_days':0},{'sphere_good_threshold':30}]
        }.items():
            defaults=settings_spec(kind)[1]
            for values in patches:
                with self.subTest(kind=kind,values=values),self.assertRaises(HTTPException):validate_settings(kind,{**defaults,**values})
        defaults=settings_spec('planetary-energy')[1]
        self.assertEqual(validate_settings('planetary-energy',{**defaults,'friend_planet_bonus':0})['friend_planet_bonus'],0)
    def test_review_points_are_explicit_strict_and_bounded(self):
        for value in (-1,101,True,'10',10.5):
            with self.assertRaises(ValidationError):LegacyReview(points_earned=value)
        self.assertEqual(LegacyReview(points_earned=0).points_earned,0)
    def test_txt_preserves_full_source_and_never_guesses_answer_keys(self):
        text='УРОК: ЦИФРА 4\n\nТЕСТ\n1. Вопрос\nA. Один\nB. Два\n'+('Абзац с объяснением.\n'*1200)
        first=lesson_preview(text);self.assertEqual(first,lesson_preview(text))
        self.assertEqual(''.join(block['content'] for block in first['lesson']['theory']),text)
        self.assertTrue(all(len(block['content'])<=10000 for block in first['lesson']['theory']))
        self.assertFalse(first['lesson']['is_active']);self.assertNotIn('quiz',first['lesson'])
        self.assertNotEqual(first['fingerprint'],lesson_preview(text+'!')['fingerprint'])
        for invalid in (' ','x\0y','x'*200001):
            with self.assertRaises(HTTPException):lesson_preview(invalid)


@unittest.skipUnless(os.getenv('NUMEROM_TEST_MONGO_URL'),'isolated Mongo only')
class ParityTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client=AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL'])
        self.db=self.client['numerom_test_mobile_parity_'+uuid.uuid4().hex]
        self.s=MobileAdmin(self.db)
        await self.db.users.insert_many([{'id':'admin','is_admin':True}, {'id':'u','full_name':'Анна Тест','email':'anna@example.test','level':1,'credits_remaining':10,'password_hash':'SECRET'}])
        await self.db.lessons_v2.insert_one({'id':'l','title':'Четвёрка','is_active':True,'level':1,'exercises':[{'id':'e','title':'Моя практика'}]})
        await self.db.exercise_responses.insert_one({'id':'r','user_id':'u','lesson_id':'l','exercise_id':'e','response_text':'Наблюдение','submitted_at':'one'})
    async def asyncTearDown(self):
        await self.client.drop_database(self.db.name);self.client.close()
    def meta(self,revision=0):return {'request_id':uuid.uuid4(),'revision':revision,'reason':'Проверка преподавателем'}
    async def review_body(self,points,**changes):
        row=next(r for r in (await self.s.responses('admin'))['responses'] if r['id']=='r')
        return ReviewChange(**{**self.meta(row['revision']),'expected_answer':row['expected_answer'],'admin_comment':'Спасибо за пример','points_earned':points,**changes})
    async def balance(self):return (await self.db.users.find_one({'id':'u'}))['credits_remaining']
    async def test_reward_high_water_duplicate_lower_raise_and_history(self):
        body=await self.review_body(30)
        first=await self.s.review('admin','r',body);again=await self.s.review('admin','r',body)
        self.assertEqual(first['points_awarded'],30);self.assertEqual(again['points_awarded'],0)
        self.assertEqual(await self.balance(),40)
        lower=await self.s.review('admin','r',await self.review_body(10))
        self.assertEqual(lower['points_awarded'],0);self.assertEqual(lower['award_total'],30)
        higher=await self.s.review('admin','r',await self.review_body(45))
        self.assertEqual(higher['points_awarded'],15);self.assertEqual(await self.balance(),55)
        transactions=await self.db.credit_transactions.find({}).to_list(10)
        self.assertEqual(sorted(t['amount'] for t in transactions),[15,30])
        self.assertEqual((await self.db.exercise_responses.find_one({'id':'r'}))['points_earned'],45)
    async def test_legacy_reward_is_initial_watermark_not_repeated(self):
        await self.db.exercise_responses.update_one({'id':'r'},{'$set':{'points_earned':20,'reviewed':True}})
        lower=await self.s.review('admin','r',await self.review_body(10))
        self.assertEqual(lower['points_awarded'],0)
        higher=await self.s.review('admin','r',await self.review_body(35))
        self.assertEqual(higher['points_awarded'],15);self.assertEqual(await self.balance(),25)
    async def test_concurrent_different_reviews_one_revision_winner(self):
        bodies=[await self.review_body(20),await self.review_body(70)]
        results=await asyncio.gather(*(self.s.review('admin','r',b) for b in bodies),return_exceptions=True)
        self.assertEqual(sum(isinstance(r,dict) for r in results),1)
        self.assertEqual(sum(isinstance(r,HTTPException) and r.status_code==409 for r in results),1)
        row=await self.db.exercise_responses.find_one({'id':'r'})
        self.assertEqual(await self.balance(),10+row['points_earned'])
        self.assertEqual(await self.db.credit_transactions.count_documents({}),1)
    async def test_reward_delivery_retry_and_deferred_history(self):
        body=await self.review_body(25)
        with patch('services.mobile_admin.deliver_review_award',AsyncMock(side_effect=RuntimeError('offline'))):
            saved=await self.s.review('admin','r',body)
        self.assertTrue(saved['award_pending']);self.assertEqual(await self.balance(),10)
        with patch('services.mobile_admin_learning.flush_pending_credit_transactions',AsyncMock(side_effect=RuntimeError('history offline'))):
            saved=await self.s.review('admin','r',body)
        self.assertFalse(saved['award_pending']);self.assertEqual(await self.balance(),35)
        user=await self.db.users.find_one({'id':'u'});self.assertEqual(len(user['pending_credit_transactions']),1)
        await flush_pending_credit_transactions(self.db,'u')
        await self.s.review('admin','r',body)
        self.assertEqual(await self.balance(),35);self.assertEqual(await self.db.credit_transactions.count_documents({}),1)
    async def test_newer_lower_review_preserves_undelivered_high_target(self):
        with patch('services.mobile_admin.deliver_review_award',AsyncMock(side_effect=RuntimeError('offline'))):
            await self.s.review('admin','r',await self.review_body(80))
        result=await self.s.review('admin','r',await self.review_body(20))
        self.assertEqual(result['points_awarded'],80);self.assertEqual(result['award_total'],80)
        self.assertEqual(await self.balance(),90)
    async def test_shared_legacy_http_handler_cannot_repeat_mobile_reward(self):
        # Execute the actual route body without importing server startup/services.
        tree=ast.parse((Path(__file__).parents[1]/'server.py').read_text())
        node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='review_exercise_response')
        node.decorator_list=[]
        scope={'db':self.db,'Depends':Depends,'get_current_user':get_current_user,'HTTPException':HTTPException}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'legacy-review-route','exec'),scope)
        await self.s.review('admin','r',await self.review_body(20))
        rid=str(uuid.uuid4());body={'points_earned':35,'admin_comment':'Проверено','request_id':rid}
        await scope[node.name]('r',body,{'user_id':'admin'})
        await scope[node.name]('r',body,{'user_id':'admin'})
        await scope[node.name]('r',{'points_earned':10},{'user_id':'admin'})
        await self.s.review('admin','r',await self.review_body(50))
        self.assertEqual(await self.balance(),60)
        self.assertEqual(sum(t['amount'] for t in await self.db.credit_transactions.find({}).to_list(10)),50)
        with self.assertRaises(HTTPException):await scope[node.name]('r',{'points_earned':True},{'user_id':'admin'})
    async def test_no_review_award_for_attachment_draft_or_stale_student_answer(self):
        body=await self.review_body(40)
        await self.db.exercise_responses.update_one({'id':'r'},{'$set':{'response_text':'Исправленный ответ'}})
        with self.assertRaises(HTTPException) as error:await self.s.review('admin','r',body)
        self.assertEqual(error.exception.status_code,409)
        await self.db.exercise_responses.update_one({'id':'r'},{'$set':{'attachment_draft_only':True}})
        with self.assertRaises(HTTPException) as error:await self.s.legacy_review('admin','r',LegacyReview(points_earned=50))
        self.assertEqual(error.exception.status_code,404);self.assertEqual(await self.balance(),10)
    async def test_response_pagination_search_filters_join_names_no_private_data(self):
        await self.db.exercise_responses.insert_many([{'id':'r2','user_id':'u','lesson_id':'l','exercise_id':'e','response_text':'Ещё один','reviewed':True}, {'id':'draft','user_id':'u','attachment_draft_only':True}])
        page=await self.s.responses('admin',page_size=1,q='Анна')
        self.assertEqual(page['total'],2);self.assertTrue(page['has_more'])
        row=page['responses'][0];self.assertEqual(row['student_name'],'Анна Тест');self.assertEqual(row['lesson_title'],'Четвёрка');self.assertEqual(row['exercise_title'],'Моя практика')
        self.assertNotIn('SECRET',str(page));self.assertNotIn('password_hash',str(page))
        pending=await self.s.responses('admin',reviewed='pending',lesson_id='l')
        self.assertEqual(pending['total'],1)
        self.assertEqual((await self.s.responses('admin',q='.*'))['total'],0)
    async def test_pending_challenge_notes_override_archive_and_feed_analytics(self):
        old={'id':'ch1','user_id':'u','lesson_id':'l','challenge_id':'c','revision':1,'attempt_number':1,'daily_notes':[{'day':1,'note':'Старое'}],'is_completed':False}
        new={**old,'revision':2,'daily_notes':[{'day':1,'note':'Сохранённая заметка'}],'completed_days':[1],'is_completed':True}
        await self.db.challenge_progress.insert_one(old)
        await self.db.users.update_one({'id':'u'},{'$set':{'pending_challenge_progress':[{'record':new}]}})
        notes=await self.s.challenge_notes('admin',q='Сохранённая',page_size=1)
        self.assertEqual(notes['total'],1);self.assertEqual(notes['notes'][0]['daily_notes'][0]['note'],'Сохранённая заметка')
        analytics=await self.s.analytics('admin')
        self.assertEqual(analytics['summary']['challenge_attempts'],1);self.assertEqual(analytics['summary']['completed_challenges'],1)
        self.assertEqual(analytics['summary']['pending_reviews'],1)
        self.assertEqual(analytics['lessons'][0]['challenge_attempts'],1)
    async def test_archive_keeps_history_blocks_student_and_future_edits(self):
        await self.db.lesson_progress.insert_one({'user_id':'u','lesson_id':'l','is_completed':True})
        body=ArchiveChange(**self.meta())
        await self.s.archive('admin','lessons','l',body);await self.s.archive('admin','lessons','l',body)
        self.assertEqual((await self.s.lessons('admin',archived='archived'))['total'],1)
        self.assertEqual((await self.s.lessons('admin',archived='active'))['total'],0)
        self.assertEqual(await self.db.lesson_progress.count_documents({}),1)
        self.assertEqual(await self.db.exercise_responses.count_documents({}),1)
        with self.assertRaises(HTTPException):await require_student_lesson(self.db,'u','l')
        with self.assertRaises(HTTPException):await self.s.lesson('admin','l',LessonChange(**self.meta(1),title='Вернуть',level=1,order=1,is_active=True))
        await self.db.personal_consultations.insert_one({'id':'c','title':'Разбор','assigned_user_id':'u','is_active':True,'pdf_file_id':'private'})
        await self.s.archive('admin','consultations','c',ArchiveChange(**self.meta()))
        self.assertEqual((await self.db.personal_consultations.find_one({'id':'c'}))['pdf_file_id'],'private')
    async def test_txt_preview_confirm_tamper_and_duplicate_create(self):
        text='Новый урок\nПодробная теория.'
        preview=await self.s.preview_import('admin',ImportPreview(text=text))
        self.assertEqual(await self.db.lessons_v2.count_documents({}),1)
        body=LessonImport(**self.meta(),text=text,fingerprint=preview['fingerprint'])
        first=await self.s.import_lesson('admin',body);second=await self.s.import_lesson('admin',body)
        self.assertEqual(first,second);self.assertEqual(await self.db.lessons_v2.count_documents({}),2)
        row=await self.db.lessons_v2.find_one({'id':first['id']});self.assertFalse(row['is_active'])
        with self.assertRaises(HTTPException):await self.s.import_lesson('admin',body.model_copy(update={'text':text+'!'}))
        with self.assertRaises(HTTPException):await self.s.preview_import('u',ImportPreview(text=text))
    async def test_settings_four_groups_revision_partial_bounds_and_no_coercion(self):
        for kind in ('learning','costs','planetary-energy','monthly-route'):
            state=await self.s.read_settings('admin',kind);self.assertEqual(state['revision'],0)
            body=SettingsChange(**self.meta(),values=state['values'])
            await self.s.write_settings('admin',kind,body);await self.s.write_settings('admin',kind,body)
            self.assertEqual((await self.s.read_settings('admin',kind))['revision'],1)
        for values in ({'normalization_min':95},{'anti_cyclicity_enabled':1},{'friend_planet_bonus':True}):
            with self.assertRaises(HTTPException):await self.s.write_settings('admin','planetary-energy',SettingsChange(**self.meta(1),values=values))
        await self.db.planetary_energy_modifiers_config.update_one({'is_active':True},{'$inc':{'mobile_revision':1},'$set':{'normalization_max':70}})
        with self.assertRaises(HTTPException):await self.s.write_settings('admin','planetary-energy',SettingsChange(**self.meta(1),values={'normalization_min':60}))
        with self.assertRaises(HTTPException):await self.s.write_settings('admin','planetary-energy',SettingsChange(**self.meta(2),values={'normalization_min':80}))
    async def test_every_new_admin_read_requires_live_role(self):
        for call in (lambda:self.s.challenge_notes('u'),lambda:self.s.analytics('u'),lambda:self.s.read_settings('u','monthly-route')):
            with self.assertRaises(HTTPException) as error:await call()
            self.assertEqual(error.exception.status_code,403)
        await self.db.users.update_one({'id':'admin'},{'$set':{'is_disabled':True}})
        with self.assertRaises(HTTPException):await self.s.analytics('admin')

    async def test_reward_delivery_concurrent_same_intent_credits_once(self):
        intent={'id':'r','user_id':'u','lesson_id':'l','review_legacy_watermark':0,'review_award_target':70}
        results=await asyncio.gather(*(deliver_review_award(self.db,intent) for _ in range(5)))
        self.assertEqual(sum(r['points_awarded'] for r in results),70)
        self.assertEqual(await self.balance(),80)
        self.assertEqual(await self.db.credit_transactions.count_documents({}),1)

    async def test_actual_router_auth_validation_and_reserved_import_paths(self):
        app=FastAPI();app.include_router(create_mobile_admin_router(self.db))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
            self.assertEqual((await client.get('/api/admin/mobile/analytics')).status_code,401)
            app.dependency_overrides[get_current_user]=lambda:{'user_id':'u'}
            self.assertEqual((await client.get('/api/admin/mobile/challenge-notes')).status_code,403)
            app.dependency_overrides[get_current_user]=lambda:{'user_id':'admin'}
            self.assertEqual((await client.get('/api/admin/mobile/responses?page_size=101')).status_code,422)
            self.assertEqual((await client.get('/api/admin/mobile/consultations?archived=wrong')).status_code,422)
            preview=await client.post('/api/admin/mobile/lessons/import/preview',json={'text':'Урок TXT\nТеория'})
            self.assertEqual(preview.status_code,200)
            meta={**self.meta(),'request_id':str(uuid.uuid4())}
            saved=await client.post('/api/admin/mobile/lessons/import',json={**meta,'text':'Урок TXT\nТеория','fingerprint':preview.json()['fingerprint']})
            self.assertEqual(saved.status_code,200)
            self.assertTrue(saved.json()['id'].startswith('import-'))
            for values in ({'anti_cyclicity_enabled':1},{'friend_planet_bonus':'0.3'}):
                invalid=await client.post('/api/admin/mobile/settings/planetary-energy',json={**meta,'values':values})
                self.assertEqual(invalid.status_code,422)
            self.assertEqual((await client.get('/api/admin/mobile/settings/monthly-route')).status_code,200)
