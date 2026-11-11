"""Real signatures and isolated Mongo: identity ownership, bonus and receipt replay."""
import asyncio
import hashlib
import hmac
import importlib.util
import json
import os
import sys
import time
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from domain.telegram import TelegramConfig, TelegramLaunch, TelegramRegistration, TelegramLink, TelegramInvoice, verify_init_data
from domain.full_report_purchase import FullReportCheckout
from services.telegram import TelegramAccounts
from services.telegram_payments import TelegramPayments
from auth import get_password_hash
from models import User
from public_gateway import _route, _valid_body

TOKEN = '123456789:' + 'isolated-test-bot-token-never-real'
CONFIG = TelegramConfig({'TELEGRAM_BOT_TOKEN': TOKEN, 'TELEGRAM_STARS_PRICES': '{"one_time":10,"full_report":40}'})


def launch(tid=42, **patch):
    values = {'auth_date': str(int(time.time())), 'user': json.dumps({'id': tid, 'first_name': 'Test'}), **patch}
    key = hmac.new(b'WebAppData', TOKEN.encode(), hashlib.sha256).digest()
    values['hash'] = hmac.new(key, '\n'.join(f'{k}={v}' for k, v in sorted(values.items())).encode(), hashlib.sha256).hexdigest()
    return urlencode(values)


class FakeBot:
    def __init__(self): self.calls = []
    async def call(self, method, **body):
        self.calls.append((method, body))
        if method == 'createInvoiceLink': return 'https://t.me/$invoice-for-test'
        return True


class Signatures(unittest.TestCase):
    def test_real_signature_and_no_unsigned_id(self):
        self.assertEqual(verify_init_data(launch(), CONFIG)['id'], 42)
        with self.assertRaises(HTTPException): verify_init_data(launch().replace('Test', 'Other'), CONFIG)
        with self.assertRaises(HTTPException): verify_init_data('user_id=42', CONFIG)

    def test_expiry_future_duplicate_bot_and_group(self):
        for raw in [launch(auth_date=str(int(time.time()) - 601)), launch(auth_date=str(int(time.time()) + 60)),
                    launch() + '&auth_date=1', launch(chat_type='group'), launch(tid=True),
                    launch(user=json.dumps({'id': 42, 'is_bot': True}))]:
            with self.subTest(raw_length=len(raw)), self.assertRaises(HTTPException): verify_init_data(raw, CONFIG)

    def test_signature_field_is_signed_for_bot_token_verification(self):
        self.assertEqual(verify_init_data(launch(signature='third-party-signature'), CONFIG)['id'], 42)

    def test_gateway_rejects_extra_identity_price_and_privileges(self):
        self.assertEqual(_route('POST', '/api/auth/telegram/login'), 'login')
        self.assertTrue(_valid_body('/api/auth/telegram/login', {'init_data': launch()}))
        for field in ['user_id', 'credits_remaining', 'is_admin', 'telegram_id']:
            self.assertFalse(_valid_body('/api/auth/telegram/register', {'init_data': launch(), 'full_name': 'Test', 'birth_date': '01.01.1980', field: 100}))
        self.assertFalse(_valid_body('/api/telegram/payments/invoice', {'package_type': 'one_time', 'request_id': str(uuid.uuid4()), 'amount': 1}))
        self.assertIsNone(_route('POST', '/api/telegram/updates'))


class Dispatch(unittest.IsolatedAsyncioTestCase):
    async def test_private_menu_group_guard_and_service_refund(self):
        saved = list(sys.path)
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
            spec = importlib.util.spec_from_file_location('telegram_worker_test', Path(__file__).resolve().parents[2] / 'scripts/run-telegram-bot.py')
            worker = importlib.util.module_from_spec(spec); spec.loader.exec_module(worker)
        finally: sys.path[:] = saved
        accounts = SimpleNamespace(menu=AsyncMock(), bot=FakeBot(), config=CONFIG)
        payments = SimpleNamespace(fulfill=AsyncMock(), record_refund=AsyncMock())
        await worker.handle(accounts, payments, {'message': {'chat': {'id': -7, 'type': 'group'}, 'from': {'id': 42}, 'text': '/balance'}})
        accounts.menu.assert_not_awaited()
        await worker.handle(accounts, payments, {'message': {'chat': {'id': 42, 'type': 'private'}, 'from': {'id': 42}, 'text': '/balance'}})
        accounts.menu.assert_awaited_once_with(42)
        receipt = {'invoice_payload': 'a' * 64}
        await worker.handle(accounts, payments, {'message': {'chat': {'id': 42, 'type': 'private'}, 'from': {'id': 1, 'is_bot': True}, 'refunded_payment': receipt}})
        payments.record_refund.assert_awaited_once_with(42, receipt)
        payments.fulfill.assert_not_awaited()


@unittest.skipUnless(os.getenv('NUMEROM_TEST_MONGO_URL'), 'isolated test database required')
class AccountsAndPayments(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client = AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL'], serverSelectionTimeoutMS=5000)
        self.db = self.client['numerom_test_telegram_' + uuid.uuid4().hex]
        self.previous = os.environ.get('SECRET_KEY'); os.environ['SECRET_KEY'] = 'isolated-telegram-test-signing-key-only'
        self.bot = FakeBot(); self.accounts = TelegramAccounts(self.db, CONFIG, self.bot)
        self.payments = TelegramPayments(self.db, self.accounts)

    async def asyncTearDown(self):
        await self.client.drop_database(self.db.name); self.client.close()
        if self.previous is None: os.environ.pop('SECRET_KEY', None)
        else: os.environ['SECRET_KEY'] = self.previous

    async def register(self, tid=42):
        return await self.accounts.register(TelegramRegistration(init_data=launch(tid), full_name='Test Person', birth_date='01.01.1980'))

    async def price_settings(self, values, revision=0):
        from services.mobile_admin import MobileAdmin, SettingsChange
        await self.db.users.update_one({'id': 'price-admin'}, {'$set': {'is_admin': True}}, upsert=True)
        body = SettingsChange(request_id=uuid.uuid4(), revision=revision, reason='Настройка цен Stars', values=values)
        return await MobileAdmin(self.db).write_settings('price-admin', 'telegram-stars', body)

    async def test_admin_stars_prices_apply_without_recreating_payment_service(self):
        user = (await self.register())['user']
        await self.price_settings({'one_time': 25, 'full_report': 90})
        catalog = await self.payments.catalog(user['id'])
        self.assertEqual(next(p['stars'] for p in catalog['packages'] if p['id'] == 'one_time'), 25)
        self.assertEqual((await self.payments.report_catalog(user['id']))['amount_total'], 90)
        order = await self.payments.create(user['id'], TelegramInvoice(package_type='one_time', request_id=str(uuid.uuid4())))
        self.assertEqual(order['amount'], 25)

    async def test_price_changes_and_disabling_keep_existing_invoice_snapshot(self):
        user = (await self.register())['user']
        request = TelegramInvoice(package_type='one_time', request_id=str(uuid.uuid4()))
        old = await self.payments.create(user['id'], request)
        await self.price_settings({'one_time': 25})
        new = await self.payments.create(user['id'], TelegramInvoice(package_type='one_time', request_id=str(uuid.uuid4())))
        self.assertEqual((old['amount'], new['amount']), (10, 25))
        await self.price_settings({'one_time': 0}, revision=1)
        self.assertEqual(await self.payments.create(user['id'], request), old)
        with self.assertRaises(HTTPException):
            await self.payments.create(user['id'], TelegramInvoice(package_type='one_time', request_id=str(uuid.uuid4())))
        payment = {'invoice_payload': old['order_id'], 'currency': 'XTR', 'total_amount': 10, 'telegram_payment_charge_id': 'before-price-change'}
        await self.payments.fulfill(42, payment)
        self.assertEqual((await self.db.users.find_one({'id': user['id']}))['credits_remaining'], 20)
        self.assertFalse(next(p['enabled'] for p in (await self.payments.catalog(user['id']))['packages'] if p['id'] == 'one_time'))

    async def test_report_invoice_price_is_frozen_when_admin_disables_new_sales(self):
        user = (await self.register())['user']
        request = FullReportCheckout(request_id=str(uuid.uuid4()), birth_date='01.01.1980', client='mobile')
        old = await self.payments.create_report(user['id'], request)
        await self.price_settings({'full_report': 0})
        self.assertEqual(await self.payments.create_report(user['id'], request), old)
        self.assertFalse((await self.payments.report_catalog(user['id']))['enabled'])
        with self.assertRaises(HTTPException):
            await self.payments.create_report(user['id'], request.model_copy(update={'request_id': uuid.uuid4()}))

    async def test_stars_settings_require_current_admin_and_strict_prices(self):
        from services.mobile_admin import MobileAdmin, SettingsChange
        from fastapi import FastAPI
        from routers.mobile_admin import create_mobile_admin_router
        from auth import get_current_user
        import httpx
        user = (await self.register())['user']; service = MobileAdmin(self.db)
        body = SettingsChange(request_id=uuid.uuid4(), revision=0, reason='Цена', values={'one_time': 20})
        app = FastAPI(); app.include_router(create_mobile_admin_router(self.db))
        app.dependency_overrides[get_current_user] = lambda: {'user_id': user['id'], 'is_admin': True}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            self.assertEqual((await client.get('/api/admin/mobile/settings/telegram-stars')).status_code, 403)
            self.assertEqual((await client.post('/api/admin/mobile/settings/telegram-stars', json=body.model_dump(mode='json'))).status_code, 403)
        await self.db.users.insert_one({'id': 'price-admin', 'is_admin': True})
        for value in [-1, 100001, True, 1.5]:
            with self.subTest(value=value), self.assertRaises(HTTPException):
                await service.write_settings('price-admin', 'telegram-stars', body.model_copy(update={'values': {'one_time': value}}))
        with self.assertRaises(HTTPException):
            await service.write_settings('price-admin', 'telegram-stars', body.model_copy(update={'values': {'bot_token': 1}}))
        await service.write_settings('price-admin', 'telegram-stars', body)
        await service.write_settings('price-admin', 'telegram-stars', body)
        saved = await service.read_settings('price-admin', 'telegram-stars')
        self.assertEqual(saved['revision'], 1); self.assertEqual(saved['values']['one_time'], 20)
        self.assertEqual(set(saved), {'revision', 'values', 'fields'})
        with self.assertRaises(HTTPException):
            await service.write_settings('price-admin', 'telegram-stars', body.model_copy(update={'request_id': uuid.uuid4()}))
        await self.db.users.update_one({'id': 'price-admin'}, {'$set': {'is_disabled': True}})
        with self.assertRaises(HTTPException): await service.read_settings('price-admin', 'telegram-stars')

    async def test_registration_retries_bonus_once_and_menu_immediately(self):
        results = await asyncio.gather(*(self.register() for _ in range(3)))
        self.assertEqual(len({x['user']['id'] for x in results}), 1)
        user = results[0]['user']; self.assertEqual(user['credits_remaining'], 10)
        self.assertEqual(await self.db.users.count_documents({}), 1)
        self.assertEqual(await self.db.credit_transactions.count_documents({}), 1)
        welcome = await self.db.credit_transactions.find_one({'user_id': user['id']})
        self.assertEqual(welcome['amount'], 10)
        await self.accounts.menu(42)
        text = [b['text'] for m, b in self.bot.calls if m == 'sendMessage'][-1]
        self.assertIn('10 баллов', text)
        self.assertNotIn('password_hash', user)
        await self.db.users.update_one({'id': user['id']}, {'$set': {'credits_remaining': 37}})
        self.assertEqual((await self.register())['user']['credits_remaining'], 37)
        await self.accounts.menu(42)
        self.assertIn('37 баллов', self.bot.calls[-1][1]['text'])

    async def test_existing_account_link_keeps_balance_and_cannot_be_taken(self):
        user = User(email='existing@example.invalid', password_hash=get_password_hash('existing-test-password'), full_name='Existing', birth_date='01.01.1980', credits_remaining=7)
        await self.db.users.insert_one(user.model_dump())
        body = TelegramLink(init_data=launch(), email=user.email, password='existing-test-password')
        linked = await self.accounts.link(body)
        self.assertEqual(linked['user']['id'], user.id); self.assertEqual(linked['user']['credits_remaining'], 7)
        self.assertEqual(await self.db.credit_transactions.count_documents({}), 0)
        with self.assertRaises(HTTPException):
            await self.accounts.link(TelegramLink(init_data=launch(43), email=user.email, password='existing-test-password'))
        await self.db.users.update_one({'id': user.id}, {'$inc': {'auth_version': 1}})
        with self.assertRaises(HTTPException): await self.accounts.login(TelegramLaunch(init_data=launch()))
        await self.accounts.link(body)
        self.assertEqual((await self.accounts.login(TelegramLaunch(init_data=launch())))['user']['id'], user.id)

    async def test_identity_collision_disabled_and_role_preservation(self):
        original = await self.register()
        user = User(email='second@example.invalid', password_hash=get_password_hash('existing-test-password'), full_name='Second', birth_date='01.01.1980')
        await self.db.users.insert_one(user.model_dump())
        with self.assertRaises(HTTPException): await self.accounts.link(TelegramLink(init_data=launch(), email=user.email, password='existing-test-password'))
        self.assertFalse(original['user']['is_admin'])
        await self.db.users.update_one({'id': original['user']['id']}, {'$set': {'is_disabled': True}})
        with self.assertRaises(HTTPException): await self.register()

    async def test_stars_checkout_and_duplicate_receipt_are_atomic(self):
        user = (await self.register())['user']; request = TelegramInvoice(package_type='one_time', request_id=str(uuid.uuid4()))
        order = await self.payments.create(user['id'], request)
        self.assertEqual(order, await self.payments.create(user['id'], request))
        self.assertEqual(sum(m == 'createInvoiceLink' for m, _ in self.bot.calls), 1)
        payment = {'invoice_payload': order['order_id'], 'currency': 'XTR', 'total_amount': 10, 'telegram_payment_charge_id': 'charge-1'}
        await self.payments.check(42, {**payment, 'id': 'pre-checkout-query'}, pre_checkout=True)
        await asyncio.gather(*(self.payments.fulfill(42, payment) for _ in range(3)))
        current = await self.db.users.find_one({'id': user['id']})
        self.assertEqual(current['credits_remaining'], 20)
        self.assertEqual(await self.db.credit_transactions.count_documents({}), 2)
        with self.assertRaises(HTTPException): await self.payments.check(42, {**payment, 'id': 'pre-checkout-query'}, pre_checkout=True)
        with self.assertRaises(HTTPException): await self.payments.fulfill(42, {**payment, 'telegram_payment_charge_id': 'another-charge'})

    async def test_forged_amount_owner_currency_and_read_are_rejected(self):
        user = (await self.register())['user']; other = (await self.register(43))['user']
        order = await self.payments.create(user['id'], TelegramInvoice(package_type='one_time', request_id=str(uuid.uuid4())))
        base = {'invoice_payload': order['order_id'], 'currency': 'XTR', 'total_amount': 10, 'telegram_payment_charge_id': 'charge-2'}
        for tid, patch in [(43, {}), (42, {'total_amount': 1}), (42, {'currency': 'EUR'}), (42, {'total_amount': True})]:
            with self.assertRaises(HTTPException): await self.payments.fulfill(tid, {**base, **patch})
        with self.assertRaises(HTTPException): await self.payments.status(other['id'], order['order_id'])
        self.assertEqual((await self.db.users.find_one({'id': user['id']}))['credits_remaining'], 10)

    async def test_refund_blocks_receipt_replay_and_retains_review(self):
        user = (await self.register())['user']
        order = await self.payments.create(user['id'], TelegramInvoice(package_type='one_time', request_id=str(uuid.uuid4())))
        payment = {'invoice_payload': order['order_id'], 'currency': 'XTR', 'total_amount': 10, 'telegram_payment_charge_id': 'refund-charge'}
        await self.payments.fulfill(42, payment)
        await self.payments.record_refund(42, payment)
        await self.payments.record_refund(42, payment)
        with self.assertRaises(HTTPException): await self.payments.fulfill(42, payment)
        self.assertEqual(await self.db.telegram_payment_review.count_documents({}), 1)
        self.assertEqual((await self.payments.status(user['id'], order['order_id']))['state'], 'refunded')

    async def test_parallel_precheckout_and_refund_before_receipt(self):
        user = (await self.register())['user']
        order = await self.payments.create(user['id'], TelegramInvoice(package_type='one_time', request_id=str(uuid.uuid4())))
        payment = {'invoice_payload': order['order_id'], 'currency': 'XTR', 'total_amount': 10, 'telegram_payment_charge_id': 'early-refund'}
        await self.payments.check(42, {**payment, 'id': 'query-one'}, pre_checkout=True)
        await self.payments.check(42, {**payment, 'id': 'query-one'}, pre_checkout=True)
        with self.assertRaises(HTTPException): await self.payments.check(42, {**payment, 'id': 'query-two'}, pre_checkout=True)
        await self.payments.record_refund(42, payment)
        with self.assertRaises(HTTPException): await self.payments.fulfill(42, payment)
        self.assertEqual((await self.db.users.find_one({'id': user['id']}))['credits_remaining'], 10)

    async def test_report_invoice_response_loss_is_recovered_and_wrong_profile_rejected(self):
        user = (await self.register())['user']
        request = FullReportCheckout(request_id=uuid.uuid4(), birth_date='01.01.1980')
        report = await self.payments.create_report(user['id'], request)
        await self.db.full_report_orders.update_one({'_id': report['order_id']}, {'$unset': {'checkout_url': ''}})
        repaired = await self.payments.create_report(user['id'], request)
        self.assertEqual(repaired['url'], 'https://t.me/$invoice-for-test')
        self.assertEqual(sum(m == 'createInvoiceLink' for m, _ in self.bot.calls), 1)
        with self.assertRaises(HTTPException):
            await self.payments.create_report(user['id'], FullReportCheckout(request_id=request.request_id, birth_date='02.01.1980'))

    async def test_report_purchase_entitlement_without_credit_debit(self):
        user = (await self.register())['user']; request = FullReportCheckout(request_id=uuid.uuid4(), birth_date='01.01.1980')
        report = await self.payments.create_report(user['id'], request)
        self.assertEqual(report['currency'], 'XTR'); self.assertEqual(report['amount_total'], 40)
        payment = {'invoice_payload': report['order_id'], 'currency': 'XTR', 'total_amount': 40, 'telegram_payment_charge_id': 'report-charge'}
        await self.payments.fulfill(42, payment); await self.payments.fulfill(42, payment)
        self.assertEqual((await self.db.full_report_orders.find_one({'_id': report['order_id']}))['state'], 'paid')
        self.assertEqual((await self.db.users.find_one({'id': user['id']}))['credits_remaining'], 10)
        from services.full_reports import FullReports
        from services.payments import PaymentConfig
        reports = FullReports(self.db, config=PaymentConfig({}))
        self.assertEqual((await reports.owned(user['id'], report['order_id']))[1]['state'], 'paid')
        self.assertEqual(len((await reports.history(user['id']))['orders']), 1)


if __name__ == '__main__': unittest.main()
