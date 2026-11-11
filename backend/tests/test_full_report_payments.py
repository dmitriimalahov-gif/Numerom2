import asyncio
import copy
import hashlib
import hmac
import json
import os
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
import stripe
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from auth import get_current_user
from domain.full_report_purchase import FullReportCheckout, FullReportPreview, FullReportProfileExtension
from domain.narration import clip
from routers.full_reports import create_full_reports_router
from services.full_reports import FullReports
from services.narration import NarrationService
from services.payments import PaymentConfig, Payments


def config(live=True):
    return PaymentConfig({'STRIPE_SECRET_KEY': 'sk_' + ('live' if live else 'test') + '_fake',
        'STRIPE_WEBHOOK_SECRET': 'whsec_report_fixture', 'STRIPE_MODE': 'live' if live else 'test',
        'STRIPE_LIVE_ENABLED': '1' if live else '0',
        'STRIPE_MOBILE_RETURN_URL': 'https://example.org/app/payment-result/'})


class FakeStripe:
    def __init__(self, live=True):
        self.live = live
        self.sessions = {}
        self.keys = {}
        self.calls = []
        self.retrievals = 0

    async def create(self, params, key):
        self.calls.append((copy.deepcopy(params), key))
        if key not in self.keys:
            sid = 'cs_test_' + uuid.uuid4().hex
            self.keys[key] = sid
            self.sessions[sid] = {'id': sid, 'url': 'https://checkout.stripe.com/c/pay/' + sid,
                'payment_status': 'unpaid', 'status': 'open', 'livemode': self.live,
                **{key: params[key] for key in ['mode', 'metadata', 'client_reference_id']},
                'currency': 'eur', 'amount_total': params['line_items'][0]['price_data']['unit_amount']}
        return copy.deepcopy(self.sessions[self.keys[key]])

    async def retrieve(self, sid):
        self.retrievals += 1
        return copy.deepcopy(self.sessions[sid])

    async def expire(self, sid):
        if self.sessions[sid]['status'] != 'open':
            raise RuntimeError('Not open')
        self.sessions[sid]['status'] = 'expired'
        return copy.deepcopy(self.sessions[sid])

    def event(self, raw, signature):
        return stripe.Webhook.construct_event(raw, signature, 'whsec_report_fixture').to_dict()


def fixture_report(birth_date, as_of_date, profile_snapshot=None):
    return {'version': 1, 'birth_date': birth_date, 'as_of_date': as_of_date,
            **({'profile_snapshot': copy.deepcopy(profile_snapshot)} if profile_snapshot else {}),
            'title': 'Разбор', 'sections': [{'id': 'personal', 'title': 'Числа'}],
            'narration': [clip('full-report-personal', 'full-report', 'Числа', 'Ваш разбор чисел.')]}


class RequestContract(unittest.TestCase):
    def test_service_without_injected_builder_uses_project_arithmetic(self):
        # The running API constructs FullReports without a builder; profile
        # extension once called None here and answered 500.
        from domain.full_report import build_full_report
        service = FullReports(None, config())
        self.assertEqual(service.build('10.01.1982', '2026-10-23'), build_full_report('10.01.1982', '2026-10-23'))
        injected = Mock(side_effect=fixture_report)
        self.assertEqual(FullReports(None, config(), builder=injected).build('01.02.1990', '2026-10-23')['title'], 'Разбор')
        injected.assert_called_once_with('01.02.1990', '2026-10-23')

    def test_extra_prices_and_invalid_dates_are_rejected(self):
        data = {'birth_date': '01.02.1990', 'request_id': uuid.uuid4()}
        for extra in [{'amount_total': 1}, {'currency': 'usd'}, {'return_url': 'https://evil.test'},
                      {'birth_date': '31.02.2000'}, {'birth_date': '1.02.1990'},
                      {'birth_date': '01.01.3000'}, {'birth_date': '01.01.1899'},
                      {'request_id': uuid.uuid1()}]:
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                FullReportCheckout(**{**data, **extra})
        self.assertEqual(FullReportCheckout(**data).birth_date, data['birth_date'])


@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'), 'isolated Mongo required')
class FullReportPayments(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mongo = AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL'], serverSelectionTimeoutMS=3000)
        self.db = self.mongo['numerom_test_full_reports_' + uuid.uuid4().hex]
        await self.db.users.insert_many([{'id': 'student', 'credits_remaining': 17, 'auth_version': 2}, {'id': 'other'}])
        self.provider = FakeStripe()
        self.builder = Mock(side_effect=fixture_report)
        self.service = FullReports(self.db, config(), self.provider, self.builder)
        self.queue = patch('services.narration.NarrationService.enqueue').start()
        self.insights = patch('services.report_insights.ReportInsights.enrich', side_effect=lambda report: (report, 'ready')).start()
        self.video_queue = patch('services.report_video.ReportVideo.enqueue').start()
        self.addCleanup(patch.stopall)

    async def asyncTearDown(self):
        await self.mongo.drop_database(self.db.name)
        self.mongo.close()

    async def checkout(self, **kwargs):
        return await self.service.create('student', FullReportCheckout(
            birth_date=kwargs.get('birth_date', '01.02.1990'), request_id=kwargs.get('request_id', uuid.uuid4())))

    def paid(self, response):
        session = self.provider.sessions[response['session_id']]
        session.update(payment_status='paid', status='complete')
        return session

    async def webhook(self, session, kind='checkout.session.completed'):
        raw = json.dumps({'type': kind, 'data': {'object': session}}).encode()
        timestamp = int(time.time())
        signature = hmac.new(b'whsec_report_fixture', str(timestamp).encode() + b'.' + raw, hashlib.sha256).hexdigest()
        return await Payments(self.db, self.service.config, self.provider).webhook(raw, f't={timestamp},v1={signature}')

    async def test_catalog_price_is_separate_and_never_recurring(self):
        catalog = await self.service.catalog('student')
        self.assertEqual(catalog['amount_total'], 666)
        self.assertEqual(catalog['currency'], 'eur')
        self.assertIs(catalog['recurring'], False)
        self.assertEqual(catalog['mode'], 'live')

    async def test_pending_local_interpretation_preserves_paid_arithmetic_without_premature_audio(self):
        response = await self.checkout()
        self.insights.side_effect = lambda report: (report, 'preparing')
        await self.service.fulfill(self.paid(response))
        result = await self.service.status('student', response['order_id'])
        self.assertEqual((result['status'], result['report_status'], result['analysis_status']), ('paid', 'preparing', 'preparing'))
        self.assertEqual(result['report']['birth_date'], '01.02.1990')
        self.queue.assert_not_called()
        self.video_queue.assert_not_called()
        # Right after payment the voice is «preparing», not a server error: no records yet, no 503.
        _, items = await self.service.narration_source('student', response['order_id'])
        self.assertEqual(items, [])
        self.insights.side_effect = lambda report: (report, 'ready')
        result = await self.service.status('student', response['order_id'])
        self.assertEqual(result['report_status'], 'ready')
        self.queue.assert_called()
        self.video_queue.assert_called()
        self.assertEqual((await self.db.users.find_one({'id': 'student'}))['credits_remaining'], 17)

    async def test_concurrent_checkout_uses_one_session_no_pii_and_server_price(self):
        request = FullReportCheckout(birth_date='01.02.1990', request_id=uuid.uuid4())
        responses = await asyncio.gather(*(self.service.create('student', request) for _ in range(12)))
        self.assertEqual(len({r['session_id'] for r in responses}), 1)
        self.assertEqual(await self.db.full_report_orders.count_documents({}), 1)
        self.assertTrue(all(call == self.provider.calls[0] for call in self.provider.calls))
        params = self.provider.calls[0][0]
        self.assertEqual(params['mode'], 'payment')
        self.assertEqual(params['line_items'][0]['price_data']['unit_amount'], 666)
        self.assertEqual(set(params['metadata']), {'integration', 'order_id', 'owner_ref'})
        self.assertNotIn('student', json.dumps(params))
        self.assertNotIn('01.02.1990', json.dumps(params))
        self.assertIn('service=full-report', params['success_url'])
        self.assertNotIn('payment_method_types', params)
        self.assertEqual(self.builder.call_count, 0)
        self.assertEqual(self.queue.call_count, 0)

    async def test_same_attempt_cannot_change_birthdate_or_mode(self):
        request_id = uuid.uuid4()
        await self.checkout(request_id=request_id)
        with self.assertRaises(HTTPException):
            await self.checkout(request_id=request_id, birth_date='02.02.1990')
        self.service.config = config(False)
        with self.assertRaises(HTTPException):
            await self.checkout(request_id=request_id)

    async def test_unpaid_report_and_audio_are_not_available(self):
        response = await self.checkout()
        public = await self.service.status('student', response['order_id'])
        self.assertNotIn('report', public)
        with self.assertRaises(HTTPException) as caught:
            await self.service.narration_source('student', response['order_id'])
        self.assertEqual(caught.exception.status_code, 403)
        self.assertEqual(self.builder.call_count, 0)

    async def test_amount_currency_owner_mode_session_and_integration_are_verified(self):
        response = await self.checkout()
        paid = self.paid(response)
        for mutation in [{'amount_total': 665}, {'amount_total': True}, {'currency': 'usd'}, {'livemode': False},
                         {'id': 'cs_test_foreign'}, {'mode': 'subscription'}, {'status': 'open'},
                         {'client_reference_id': 'foreign'}, {'metadata': {**paid['metadata'], 'owner_ref': 'foreign'}}]:
            with self.subTest(mutation=mutation), self.assertRaises(HTTPException):
                await self.service.fulfill({**paid, **mutation})
        self.assertIsNone(await self.service.fulfill({**paid, 'metadata': {'integration': 'numerom-credits-v1'}}))
        self.assertEqual((await self.db.full_report_orders.find_one({}))['state'], 'pending')

    async def test_paid_snapshot_is_stable_and_never_spends_or_grants_credits(self):
        response = await self.checkout()
        self.paid(response)
        result = await self.service.status('student', response['order_id'])
        self.assertEqual(result['status'], 'paid')
        self.assertEqual(result['report_status'], 'ready')
        self.assertEqual(result['report']['birth_date'], '01.02.1990')
        self.builder.assert_called_once_with('01.02.1990', result['as_of_date'])
        self.builder.side_effect = RuntimeError('Future version must not replace snapshot')
        self.assertEqual((await self.service.status('student', response['order_id']))['report'], result['report'])
        self.assertEqual((await self.db.users.find_one({'id': 'student'}))['credits_remaining'], 17)
        self.assertEqual(await self.db.payment_orders.count_documents({}), 0)
        self.assertEqual(await self.db.credit_transactions.count_documents({}), 0)
        self.assertNotIn('is_premium', await self.db.users.find_one({'id': 'student'}))
        self.assertTrue(self.queue.called)

    async def test_concurrent_duplicate_fulfillment_creates_single_paid_snapshot(self):
        response = await self.checkout()
        paid = self.paid(response)
        await asyncio.gather(*(self.service.fulfill(paid) for _ in range(16)))
        results = await asyncio.gather(*(self.service.status('student', response['order_id']) for _ in range(8)))
        self.assertTrue(all(row['report'] == results[0]['report'] for row in results))
        self.assertEqual(await self.db.full_report_orders.count_documents({'state': 'paid', 'report': {'$exists': True}}), 1)

    async def test_generation_outage_keeps_paid_purchase_and_retries_without_repayment(self):
        response = await self.checkout()
        self.paid(response)
        self.builder.side_effect = RuntimeError('Temporary build outage')
        first = await self.service.status('student', response['order_id'])
        self.assertEqual((first['status'], first['report_status']), ('paid', 'preparing'))
        self.builder.side_effect = fixture_report
        second = await self.service.status('student', response['order_id'])
        self.assertEqual(second['report_status'], 'ready')
        self.assertEqual(len(self.provider.sessions), 1)
        self.assertEqual(self.provider.retrievals, 1)

    async def test_builder_cannot_save_another_person_or_date_snapshot(self):
        response = await self.checkout()
        self.paid(response)
        self.builder.side_effect = lambda birth, as_of: {**fixture_report(birth, as_of), 'birth_date': '02.02.1990'}
        self.assertEqual((await self.service.status('student', response['order_id']))['report_status'], 'preparing')
        self.builder.side_effect = lambda birth, as_of: {**fixture_report(birth, as_of), 'as_of_date': '2000-01-01'}
        self.assertEqual((await self.service.status('student', response['order_id']))['report_status'], 'preparing')
        self.assertNotIn('report', await self.db.full_report_orders.find_one({}))

    async def test_queue_failure_does_not_lose_paid_report_and_retries(self):
        response = await self.checkout()
        self.paid(response)
        self.queue.side_effect = OSError('Voice worker unavailable')
        first = await self.service.status('student', response['order_id'])
        self.assertEqual(first['report_status'], 'ready')
        self.queue.side_effect = None
        await self.service.status('student', response['order_id'])
        self.assertEqual(self.queue.call_count, 2)

    async def test_foreign_owner_cannot_read_cancel_or_narrate(self):
        response = await self.checkout()
        for method in [self.service.status, self.service.cancel, self.service.narration_source]:
            with self.assertRaises(HTTPException) as caught:
                await method('other', response['order_id'])
            self.assertEqual(caught.exception.status_code, 404)

    async def test_sandbox_purchase_is_labeled_and_inaccessible_in_live_mode(self):
        self.provider.live = False
        self.service.config = config(False)
        response = await self.checkout()
        self.paid(response)
        result = await self.service.status('student', response['order_id'])
        self.assertEqual(result['mode'], 'test')
        self.assertEqual(result['status'], 'paid')
        self.service.config = config(True)
        for method in [self.service.status, self.service.narration_source]:
            with self.assertRaises(HTTPException) as caught:
                await method('student', response['order_id'])
            self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual((await self.service.history('student'))['orders'], [])

    async def test_cancel_expires_open_but_cannot_undo_paid(self):
        response = await self.checkout()
        self.assertEqual((await self.service.cancel('student', response['order_id']))['status'], 'expired')
        second = await self.checkout()
        self.paid(second)
        self.assertEqual((await self.service.cancel('student', second['order_id']))['status'], 'paid')
        self.assertEqual((await self.service.cancel('student', second['order_id']))['status'], 'paid')

    async def test_cancel_unbound_creation_allows_new_attempt_and_retry_stays_expired(self):
        request_id = uuid.uuid4()
        create = self.provider.create
        self.provider.create = AsyncMock(side_effect=RuntimeError('Network response lost'))
        with self.assertRaises(HTTPException):
            await self.checkout(request_id=request_id)
        order = await self.db.full_report_orders.find_one({})
        self.assertEqual(order['state'], 'creating')
        self.assertEqual((await self.service.cancel('student', order['_id']))['status'], 'expired')
        self.provider.create = create
        self.assertEqual((await self.checkout(request_id=request_id))['status'], 'expired')
        self.assertEqual(len(self.provider.sessions), 0)
        self.assertEqual((await self.checkout())['status'], 'pending')

    async def test_cancel_during_creation_never_hides_a_later_verified_payment(self):
        create = self.provider.create

        async def cancel_during_create(params, key):
            session = await create(params, key)
            cancelled = await self.service.cancel('student', params['metadata']['order_id'])
            self.assertEqual(cancelled['status'], 'expired')
            return session

        self.provider.create = cancel_during_create
        response = await self.checkout()
        self.assertEqual(response['status'], 'expired')
        self.assertNotIn('url', response)
        self.paid(response)
        self.assertEqual((await self.service.status('student', response['order_id']))['status'], 'paid')

    async def test_signed_webhook_routes_once_and_stale_failure_does_not_revoke(self):
        response = await self.checkout()
        paid = self.paid(response)
        for kind in ['checkout.session.completed', 'checkout.session.async_payment_succeeded', 'checkout.session.async_payment_failed']:
            await self.webhook(paid, kind)
        self.assertEqual(self.provider.retrievals, 3)
        order = await self.db.full_report_orders.find_one({})
        self.assertEqual(order['state'], 'paid')
        self.assertEqual(order['report']['as_of_date'], order['as_of_date'])
        self.assertGreaterEqual(len(order['report']['sections']), 8)
        self.assertEqual((await self.db.users.find_one({'id': 'student'}))['credits_remaining'], 17)
        with self.assertRaises(HTTPException):
            await Payments(self.db, config(), self.provider).webhook(b'{}', 'invalid')

    async def test_webhook_before_checkout_response_cannot_reset_paid_state(self):
        create = self.provider.create

        async def early_payment(params, key):
            session = await create(params, key)
            session.update(payment_status='paid', status='complete')
            self.provider.sessions[session['id']] = copy.deepcopy(session)
            await self.service.fulfill(session)
            return session

        self.provider.create = early_payment
        response = await self.checkout()
        self.assertEqual(response['status'], 'paid')
        self.assertEqual(response['report_status'], 'ready')
        self.assertNotIn('url', response)

    async def test_delayed_failure_stays_failed_until_verified_paid(self):
        response = await self.checkout()
        session = self.provider.sessions[response['session_id']]
        session['status'] = 'complete'
        await self.webhook(session, 'checkout.session.async_payment_failed')
        await self.webhook(session)
        self.assertEqual((await self.service.status('student', response['order_id']))['status'], 'failed')
        self.paid(response)
        self.assertEqual((await self.service.status('student', response['order_id']))['status'], 'paid')

    async def test_paid_report_access_survives_payment_provider_unavailability(self):
        response = await self.checkout()
        self.paid(response)
        await self.service.status('student', response['order_id'])
        self.service.config._enabled = False
        self.assertEqual((await self.service.status('student', response['order_id']))['report_status'], 'ready')
        with self.assertRaises(HTTPException):
            await self.checkout()

    async def test_router_auth_price_injection_and_owned_read(self):
        app = FastAPI()
        app.include_router(create_full_reports_router(self.db, self.service))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            self.assertEqual((await client.get('/api/full-reports/history')).status_code, 401)
            app.dependency_overrides[get_current_user] = lambda: {'user_id': 'student'}
            self.assertEqual((await client.post('/api/full-reports/checkout', json={
                'birth_date': '01.02.1990', 'request_id': str(uuid.uuid4()), 'amount_total': 1})).status_code, 422)
            response = await client.post('/api/full-reports/checkout', json={
                'birth_date': '01.02.1990', 'request_id': str(uuid.uuid4())})
            self.assertEqual(response.status_code, 200)
            self.assertNotIn('report', response.json())

    async def test_narration_media_rechecks_owner_mode_and_auth_version(self):
        response = await self.checkout()
        self.paid(response)
        result = await self.service.status('student', response['order_id'])
        item = result['report']['narration'][0]
        with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ, {'SECRET_KEY': 'report-test-only-' * 4}), \
                patch('services.full_reports.PaymentConfig', return_value=self.service.config):
            voice = NarrationService(self.db, root=temporary, public_url='https://example.org')
            folder = voice.folder(item['hash'])
            folder.mkdir(parents=True)
            (folder / 'audio.m4a').write_bytes(b'test-audio')
            (folder / 'ready.json').write_text(json.dumps({'hash': item['hash'], 'seconds': 1, 'bytes': 10, 'sha256': hashlib.sha256(b'test-audio').hexdigest()}))
            access = await voice.access('student', 'full-report', response['order_id'], item['id'])
            token = access['url'].rsplit('/', 1)[1]
            self.assertEqual(await voice.resolve(token), folder / 'audio.m4a')
            with self.assertRaises(HTTPException):
                await voice.access('other', 'full-report', response['order_id'], item['id'])
            await self.db.users.update_one({'id': 'student'}, {'$inc': {'auth_version': 1}})
            with self.assertRaises(HTTPException):
                await voice.resolve(token)

    async def profile_preview(self, **changes):
        await self.db.users.update_one({'id': 'student'}, {'$set': {
            'birth_date': '01.02.1990', 'name': 'Alice', 'surname': 'Smith',
            'phone_number': '+37312345678', 'birth_city': 'Kyiv', **changes}})
        return await self.service.preview('student', FullReportPreview(birth_date='01.02.1990', use_profile=True))

    async def test_profile_preview_is_free_and_changed_profile_cannot_start_payment(self):
        preview = await self.profile_preview()
        request = FullReportCheckout(birth_date='01.02.1990', use_profile=True,
            profile_fingerprint=preview['profile_fingerprint'], request_id=uuid.uuid4())
        self.assertIn('profile-phone', [s['id'] for s in preview['available']])
        self.assertEqual(await self.db.full_report_orders.count_documents({}), 0)
        await self.db.users.update_one({'id': 'student'}, {'$set': {'name': 'Changed'}})
        with self.assertRaises(HTTPException) as raised:
            await self.service.create('student', request)
        self.assertEqual(raised.exception.detail['code'], 'full_report_profile_changed')
        self.assertEqual(len(self.provider.calls), 0)
        self.assertEqual(await self.db.full_report_orders.count_documents({}), 0)
        fresh = await self.service.preview('student', FullReportPreview(birth_date='01.02.1990', use_profile=True))
        result = await self.service.create('student', request.model_copy(update={'profile_fingerprint':fresh['profile_fingerprint']}))
        self.assertEqual(result['status'], 'pending')

    async def test_profile_snapshot_freezes_active_modifiers_without_editor_identity(self):
        from models import PlanetaryEnergyModifiersConfig
        from datetime import datetime
        await self.db.planetary_energy_modifiers_config.insert_one({'id': 'config', 'is_active': True, 'friend_planet_bonus': 0.11,
            'updated_by': 'editor@example.com', 'updated_at': datetime(2026, 10, 1), 'created_at': datetime(2026, 9, 1)})
        preview = await self.profile_preview()
        frozen = preview['profile_snapshot']['planetary_modifiers']
        self.assertEqual(frozen['friend_planet_bonus'], 0.11)
        self.assertEqual(frozen['enemy_planet_penalty'], PlanetaryEnergyModifiersConfig().enemy_planet_penalty)
        for key in ('_id', 'id', 'is_active', 'updated_by', 'updated_at', 'created_at'):
            self.assertNotIn(key, frozen)
        self.assertNotIn('editor@example.com', json.dumps(preview, ensure_ascii=False, default=str))
        request = FullReportCheckout(birth_date='01.02.1990', use_profile=True,
            profile_fingerprint=preview['profile_fingerprint'], request_id=uuid.uuid4())
        self.assertEqual((await self.service.create('student', request))['status'], 'pending')

    async def test_checkout_snapshots_profile_and_retry_never_recaptures_edited_profile(self):
        preview = await self.profile_preview()
        request = FullReportCheckout(birth_date='01.02.1990', use_profile=True,
            profile_fingerprint=preview['profile_fingerprint'], request_id=uuid.uuid4())
        first = await self.service.create('student', request)
        await self.db.users.update_one({'id': 'student'}, {'$set': {'name':'Later', 'phone_number':'+44111111111'}})
        repeated = await self.service.create('student', request)
        self.assertEqual(repeated['order_id'], first['order_id'])
        self.assertEqual(len(self.provider.calls), 1)
        self.paid(first)
        saved = await self.service.status('student', first['order_id'])
        self.assertEqual(saved['profile_snapshot'], preview['profile_snapshot'])
        self.assertEqual(saved['report']['profile_snapshot'], preview['profile_snapshot'])
        # The purchase list names whose report it is — from the frozen profile, not the edited one.
        self.assertEqual(saved['person'], 'Alice Smith')
        listed = (await self.service.history('student'))['orders']
        self.assertEqual([row.get('person') for row in listed], ['Alice Smith'])
        self.assertNotIn('+37312345678', json.dumps(listed, ensure_ascii=False, default=str))
        params = json.dumps(self.provider.calls[0][0])
        for private in ['Alice','Smith','Kyiv','37312345678','01.02.1990']: self.assertNotIn(private,params)
        self.assertEqual(saved['amount_total'],666)
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],17)

    async def test_paid_extension_is_free_idempotent_and_keeps_readable_original(self):
        purchase = await self.checkout();self.paid(purchase)
        original = await self.service.status('student',purchase['order_id'])
        preview = await self.profile_preview()
        request = FullReportProfileExtension(profile_fingerprint=preview['profile_fingerprint'],expected_revision=1)
        extended = await self.service.extend_profile('student',purchase['order_id'],request)
        self.assertEqual(extended['revision'],2)
        self.assertEqual(extended['report']['profile_snapshot'],preview['profile_snapshot'])
        again = await self.service.extend_profile('student',purchase['order_id'],request)
        self.assertEqual(again['revision'],2)
        stored = await self.db.full_report_orders.find_one({'_id':purchase['order_id']})
        self.assertEqual(len(stored['revisions']),1)
        self.assertEqual(stored['revisions'][0]['report'],original['report'])
        self.queue.reset_mock();self.video_queue.reset_mock()
        archived = await self.service.revision('student',purchase['order_id'],1)
        self.assertTrue(archived['is_archived'])
        self.assertFalse(archived['use_profile'])
        self.assertEqual(archived['report'],original['report'])
        self.queue.assert_not_called();self.video_queue.assert_not_called()
        self.assertEqual(len(self.provider.calls),1)
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],17)
        fresh = await self.profile_preview(name='New Name')
        third = await self.service.extend_profile('student',purchase['order_id'],FullReportProfileExtension(
            profile_fingerprint=fresh['profile_fingerprint'],expected_revision=2))
        self.assertEqual(third['revision'],3)
        self.assertEqual((await self.service.revision('student',purchase['order_id'],2))['report']['profile_snapshot'],preview['profile_snapshot'])

    async def test_extension_and_archive_enforce_paid_owner_mode_and_matching_profile_date(self):
        purchase=await self.checkout();preview=await self.profile_preview()
        request=FullReportProfileExtension(profile_fingerprint=preview['profile_fingerprint'],expected_revision=1)
        for action in (lambda:self.service.extend_profile('student',purchase['order_id'],request),
                       lambda:self.service.revision('student',purchase['order_id'],1)):
            with self.assertRaises(HTTPException) as error:await action()
            self.assertEqual(error.exception.status_code,403)
        self.paid(purchase);await self.service.status('student',purchase['order_id'])
        with self.assertRaises(HTTPException) as error:await self.service.extend_profile('other',purchase['order_id'],request)
        self.assertEqual(error.exception.status_code,404)
        with self.assertRaises(HTTPException):await FullReports(self.db,config(False),self.provider).revision('student',purchase['order_id'],1)
        await self.db.users.update_one({'id':'student'},{'$set':{'birth_date':'02.02.1990'}})
        with self.assertRaises(HTTPException) as error:await self.service.extend_profile('student',purchase['order_id'],request)
        self.assertEqual(error.exception.status_code,409)
        self.assertEqual((await self.db.full_report_orders.find_one({'_id':purchase['order_id']})).get('revision',1),1)

    async def test_concurrent_different_extensions_have_one_winner(self):
        from services.report_files import digest
        purchase=await self.checkout();self.paid(purchase);await self.service.status('student',purchase['order_id'])
        preview=await self.profile_preview();snapshots=[preview['profile_snapshot'],copy.deepcopy(preview['profile_snapshot'])]
        snapshots[1]['fields']['name']='Other spelling'
        waiting=asyncio.Event();counter=0
        async def captured(user,birth):
            nonlocal counter
            index=counter;counter+=1
            if counter==2:waiting.set()
            await waiting.wait()
            return snapshots[index]
        requests=[FullReportProfileExtension(profile_fingerprint=digest('full-report-profile-v1',s),expected_revision=1) for s in snapshots]
        with patch.object(self.service,'profile_snapshot',side_effect=captured):
            responses=await asyncio.gather(*(self.service.extend_profile('student',purchase['order_id'],r) for r in requests),return_exceptions=True)
        self.assertEqual(sum(isinstance(r,dict) for r in responses),1)
        self.assertEqual(sum(isinstance(r,HTTPException) and r.status_code==409 for r in responses),1)
        stored=await self.db.full_report_orders.find_one({'_id':purchase['order_id']})
        self.assertEqual((stored['revision'],len(stored['revisions'])),(2,1))
        self.assertEqual(len(self.provider.calls),1)

    async def test_old_builder_cannot_overwrite_extended_snapshot(self):
        purchase=await self.checkout();self.paid(purchase);await self.service.status('student',purchase['order_id'])
        old=await self.db.full_report_orders.find_one({'_id':purchase['order_id']});old.pop('report')
        preview=await self.profile_preview()
        await self.service.extend_profile('student',purchase['order_id'],FullReportProfileExtension(
            profile_fingerprint=preview['profile_fingerprint'],expected_revision=1))
        await self.service.materialize(old)
        saved=await self.db.full_report_orders.find_one({'_id':purchase['order_id']})
        self.assertEqual(saved['revision'],2)
        self.assertEqual(saved['report']['profile_snapshot'],preview['profile_snapshot'])

    async def test_legacy_order_without_revision_extends_and_reads_without_recharge(self):
        purchase=await self.checkout();self.paid(purchase);await self.service.status('student',purchase['order_id'])
        await self.db.full_report_orders.update_one({'_id':purchase['order_id']},{'$unset':{'revision':'','profile_snapshot':'','profile_fingerprint':'','checkout_use_profile':'','checkout_profile_fingerprint':''}})
        preview=await self.profile_preview()
        result=await self.service.extend_profile('student',purchase['order_id'],FullReportProfileExtension(
            profile_fingerprint=preview['profile_fingerprint'],expected_revision=1))
        self.assertEqual(result['revision'],2)
        self.assertTrue((await self.service.revision('student',purchase['order_id'],1))['is_archived'])
        self.assertEqual(len(self.provider.calls),1)

    async def test_profile_routes_auth_free_preview_and_frozen_checkout_contract(self):
        preview=await self.profile_preview()
        app=FastAPI();app.include_router(create_full_reports_router(self.db,self.service))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
            self.assertEqual((await client.post('/api/full-reports/preview',json={'birth_date':'01.02.1990','use_profile':True})).status_code,401)
            app.dependency_overrides[get_current_user]=lambda:{'user_id':'student'}
            self.assertEqual((await client.post('/api/full-reports/preview',json={'birth_date':'01.02.1990','use_profile':True})).status_code,200)
            body={'birth_date':'01.02.1990','use_profile':True,'profile_fingerprint':preview['profile_fingerprint'],'request_id':str(uuid.uuid4())}
            created=(await client.post('/api/full-reports/checkout',json=body)).json()
            body['profile_fingerprint']='a'*64
            response=await client.post('/api/full-reports/checkout',json=body)
            self.assertEqual(response.status_code,409)
            self.assertEqual(response.json()['detail']['code'],'full_report_attempt_frozen')
            self.assertEqual(response.json()['detail']['order_id'],created['order_id'])


    async def test_revision_limit_preserves_archive_and_does_not_create_jobs_or_charges(self):
        from services.full_reports import MAX_ARCHIVED_REVISIONS
        purchase=await self.checkout();self.paid(purchase);await self.service.status('student',purchase['order_id'])
        order=await self.db.full_report_orders.find_one({'_id':purchase['order_id']})
        revisions=[{'revision':i+1,'created_at':order['created_at'],'report':order['report']} for i in range(MAX_ARCHIVED_REVISIONS)]
        await self.db.full_report_orders.update_one({'_id':order['_id']},{'$set':{'revision':MAX_ARCHIVED_REVISIONS+1,'revisions':revisions}})
        preview=await self.profile_preview()
        self.builder.reset_mock();self.queue.reset_mock();self.video_queue.reset_mock()
        with self.assertRaises(HTTPException) as error:
            await self.service.extend_profile('student',order['_id'],FullReportProfileExtension(
                expected_revision=MAX_ARCHIVED_REVISIONS+1,profile_fingerprint=preview['profile_fingerprint']))
        self.assertEqual(error.exception.status_code,409)
        self.assertIn('предел',error.exception.detail)
        saved=await self.db.full_report_orders.find_one({'_id':order['_id']})
        self.assertEqual(saved['revisions'],revisions)
        self.assertEqual(saved['report'],order['report'])
        self.builder.assert_not_called();self.queue.assert_not_called();self.video_queue.assert_not_called()
        self.assertEqual(len(self.provider.calls),1)

    async def test_real_extended_builder_commit_preserves_exact_snapshot(self):
        from domain.full_report import build_full_report
        self.builder.side_effect=build_full_report
        preview=await self.profile_preview(house_number='12',apartment_number='4',car_number='AB123',postal_code='2044')
        purchase=await self.service.create('student',FullReportCheckout(birth_date='01.02.1990',request_id=uuid.uuid4(),
            use_profile=True,profile_fingerprint=preview['profile_fingerprint']))
        self.paid(purchase)
        result=await self.service.status('student',purchase['order_id'])
        self.assertEqual(result['report']['profile_snapshot'],preview['profile_snapshot'])
        self.assertIn('profile-phone',[s['id'] for s in result['report']['sections']])
        self.assertEqual(result['report_status'],'ready')
        self.assertEqual(len(self.provider.calls),1)

    async def test_legacy_ambiguous_checkout_keeps_original_stripe_product_parameters(self):
        request=FullReportCheckout(birth_date='01.02.1990',request_id=uuid.uuid4())
        self.provider.create=AsyncMock(side_effect=RuntimeError('outage'))
        with self.assertRaises(HTTPException):await self.service.create('student',request)
        order=await self.db.full_report_orders.find_one({})
        old_description='Все расчёты по дате, авторские схемы, смысловой разбор, практики, мужская озвучка и персональный MP4. Разовая оплата.'
        await self.db.full_report_orders.update_one({'_id':order['_id']},{'$set':{'title':'Полный разбор даты рождения'},'$unset':{'description':''}})
        self.provider.create=FakeStripe.create.__get__(self.provider,FakeStripe)
        await self.service.create('student',request)
        product=self.provider.calls[-1][0]['line_items'][0]['price_data']['product_data']
        self.assertEqual(product,{'name':'NumerOM · Полный разбор даты рождения','description':old_description})


    async def test_revision_bson_size_guard_preserves_paid_order_and_archives(self):
        purchase=await self.checkout();self.paid(purchase);await self.service.status('student',purchase['order_id'])
        original=await self.db.full_report_orders.find_one({'_id':purchase['order_id']})
        preview=await self.profile_preview()
        self.queue.reset_mock();self.video_queue.reset_mock()
        with patch('services.full_reports.MAX_REPORT_ORDER_BYTES',100), self.assertRaises(HTTPException) as error:
            await self.service.extend_profile('student',purchase['order_id'],FullReportProfileExtension(
                expected_revision=1,profile_fingerprint=preview['profile_fingerprint']))
        self.assertEqual(error.exception.status_code,409)
        self.assertIn('объём',error.exception.detail)
        saved=await self.db.full_report_orders.find_one({'_id':purchase['order_id']})
        self.assertEqual(saved,original)
        self.queue.assert_not_called();self.video_queue.assert_not_called()
        self.assertEqual(len(self.provider.calls),1)


if __name__ == '__main__':
    unittest.main()
