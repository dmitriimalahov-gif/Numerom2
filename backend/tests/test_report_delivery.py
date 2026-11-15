"""Background delivery: paid reports progress without a visit, and the owner gets exactly one ready email."""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch
import uuid
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motor.motor_asyncio import AsyncIOMotorClient
from services.full_reports import FullReports
from services.mail import SMTPMailer
from services.report_delivery import ReportDelivery, app_url, code_revision

ORDER = 'a' * 64


class AppUrlTests(unittest.TestCase):
    def test_link_comes_from_the_app_the_reset_link_opens(self):
        with patch.dict(os.environ, {'PASSWORD_RESET_URL': 'https://1.numer.om/reset-password/'}, clear=True):
            self.assertEqual(app_url(), 'https://1.numer.om')
        with patch.dict(os.environ, {'PUBLIC_APP_URL': 'https://app.example.com/', 'PASSWORD_RESET_URL': 'https://x.example/reset-password/'}, clear=True):
            self.assertEqual(app_url(), 'https://app.example.com')
        for unsafe in ('http://example.com/', 'https://user:pass@example.com/', 'https://example.com/?next=evil'):
            with patch.dict(os.environ, {'PUBLIC_APP_URL': unsafe}, clear=True):
                self.assertEqual(app_url(), '')

    def test_dependency_update_changes_worker_revision_but_media_files_do_not(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);services=root/'backend/services';services.mkdir(parents=True)
            module=services/'report_video.py';module.write_text('VERSION = "v2"')
            before=code_revision(root)
            private=root/'backend/private';private.mkdir();(private/'ready.json').write_text('{}')
            self.assertEqual(code_revision(root),before)
            module.write_text('VERSION = "v3-motion"')
            self.assertNotEqual(code_revision(root),before)

    def test_running_delivery_exits_before_tick_when_dependencies_changed(self):
        import asyncio
        delivery=ReportDelivery.__new__(ReportDelivery);delivery.tick=AsyncMock()
        with patch('services.report_delivery.code_revision',side_effect=[('v2',),('v3',)]):
            asyncio.run(delivery.run())
        delivery.tick.assert_not_called()

    def test_email_names_text_audio_and_video_without_personal_data(self):
        mailer = SMTPMailer()
        with patch.object(mailer, '_send') as send:
            import asyncio
            asyncio.run(mailer.send_report_ready('owner@example.com', 'https://app.example.com/full-report/?order_id=' + ORDER, 62, 23))
        to, subject, body = send.call_args.args
        self.assertEqual((to, subject), ('owner@example.com', 'Ваш полный разбор NumerOM готов'))
        for part in ('потенциалы', 'озвучка всех глав (23)', 'около 62 мин', ORDER, 'Повторная оплата не нужна'):
            self.assertIn(part, body)


@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'), 'isolated Mongo required')
class ReportDeliveryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client = AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL'], serverSelectionTimeoutMS=3000)
        self.db = self.client['numerom_test_delivery_' + uuid.uuid4().hex]
        await self.db.users.insert_one({'id': 'owner', 'email': 'owner@example.com'})
        await self.db.full_report_orders.insert_many([
            {'_id': ORDER, 'user_id': 'owner', 'state': 'paid', 'livemode': False, 'created_at': datetime(2026, 10, 24)},
            {'_id': 'b' * 64, 'user_id': 'owner', 'state': 'pending', 'livemode': False, 'created_at': datetime(2026, 10, 24)},
            {'_id': 'c' * 64, 'user_id': 'owner', 'state': 'paid', 'livemode': True, 'created_at': datetime(2026, 10, 24)}])
        self.analysis = 'preparing'
        async def materialize(order):
            return {**order, 'report': {'version': 1}, 'analysis_status': self.analysis}
        self.reports = SimpleNamespace(config=SimpleNamespace(live=False), materialize=AsyncMock(side_effect=materialize),
                                       revision_filter=FullReports.revision_filter)
        self.video = SimpleNamespace(state=Mock(return_value={'status': 'rendering', 'audio_ready': 23, 'audio_total': 23}))
        self.mailer = SimpleNamespace(send_report_ready=AsyncMock())
        self.now = datetime(2026, 10, 24, 12)
        self.delivery = ReportDelivery(self.db, reports=self.reports, video=self.video, mailer=self.mailer, clock=lambda: self.now)

    async def asyncTearDown(self):
        await self.client.drop_database(self.db.name)
        self.client.close()

    def ready(self):
        self.analysis = 'ready'
        self.video.state.return_value = {'status': 'ready', 'audio_ready': 23, 'audio_total': 23, 'seconds': 3720}

    async def test_unopened_paid_report_is_driven_and_announced_once(self):
        with patch.dict(os.environ, {'PUBLIC_APP_URL': 'https://app.example.com'}):
            self.assertEqual(await self.delivery.tick(), 0)
            # Only this paid order of the current mode is materialized: no visit to the cabinet is needed.
            self.assertEqual([c.args[0]['_id'] for c in self.reports.materialize.call_args_list], [ORDER])
            self.analysis = 'ready'
            self.assertEqual(await self.delivery.tick(), 0)  # interpretation ready, video still rendering
            self.mailer.send_report_ready.assert_not_called()
            self.ready()
            self.assertEqual(await self.delivery.tick(), 1)
            self.assertEqual(await self.delivery.tick(), 0)
        self.mailer.send_report_ready.assert_awaited_once_with(
            'owner@example.com', 'https://app.example.com/full-report/?order_id=' + ORDER, 62, 23)
        saved = await self.db.full_report_orders.find_one({'_id': ORDER})
        self.assertEqual(saved['media_notified_revision'], 1)

    async def test_telegram_paid_report_is_delivered_in_telegram_and_respects_retry(self):
        await self.db.full_report_orders.update_one({'_id': ORDER}, {'$set': {'livemode': True, 'payment_provider': 'telegram'}})
        await self.db.users.update_one({'id': 'owner'}, {'$set': {'telegram_only': True, 'telegram_identity': '123:42'}})
        self.ready()
        fake = SimpleNamespace(config=SimpleNamespace(bot_id='123'), find=AsyncMock(return_value={'id': 'owner'}),
            app_link=Mock(return_value='https://example.org/telegram/?section=full-report'), bot=SimpleNamespace(call=AsyncMock()))
        with patch('services.telegram.TelegramAccounts', return_value=fake):
            self.assertEqual(await self.delivery.tick(), 1)
            self.assertEqual(await self.delivery.tick(), 0)
        fake.bot.call.assert_awaited_once()
        self.assertEqual(fake.bot.call.call_args.kwargs['chat_id'], 42)
        self.mailer.send_report_ready.assert_not_called()

    async def test_missing_audio_never_announces_a_ready_video(self):
        self.ready()
        self.video.state.return_value = {**self.video.state.return_value, 'audio_ready': 22}
        self.assertEqual(await self.delivery.tick(), 0)
        self.mailer.send_report_ready.assert_not_called()

    async def test_profile_extension_is_announced_again(self):
        self.ready()
        self.assertEqual(await self.delivery.tick(), 1)
        await self.db.full_report_orders.update_one({'_id': ORDER}, {'$set': {'revision': 2}})
        self.assertEqual(await self.delivery.tick(), 1)
        self.assertEqual(await self.delivery.tick(), 0)
        self.assertEqual(self.mailer.send_report_ready.await_count, 2)

    async def test_failed_email_is_retried_after_a_pause_without_duplicates(self):
        self.ready()
        self.mailer.send_report_ready.side_effect = [OSError('smtp down'), None]
        self.assertEqual(await self.delivery.tick(), 0)
        saved = await self.db.full_report_orders.find_one({'_id': ORDER})
        self.assertNotIn('media_notified_revision', saved)
        self.assertEqual(await self.delivery.tick(), 0)  # waits for the retry time
        self.now += timedelta(minutes=31)
        self.assertEqual(await self.delivery.tick(), 1)
        self.assertEqual(self.mailer.send_report_ready.await_count, 2)

    async def test_push_reaches_site_subscriptions_but_email_does_not_depend_on_it(self):
        self.ready()
        push = SimpleNamespace(get_user_subscriptions=AsyncMock(return_value=[{'endpoint': 'https://push.example/1', 'keys': {}}]),
                               send_notification=Mock(side_effect=RuntimeError('no VAPID keys')))
        self.delivery.push = push
        self.assertEqual(await self.delivery.tick(), 1)
        self.assertEqual(push.send_notification.call_args.args[1], 'Полный разбор NumerOM готов')


if __name__ == '__main__':
    unittest.main()
