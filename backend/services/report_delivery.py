"""Paid full reports finish without the owner opening them.

Each pass materializes paid orders (report, local interpretation, then every audio chapter and the video are
queued by the existing workers). Once the interpretation, all audio and the MP4 are ready for the order's
current revision, the owner gets one email and, where they subscribed on the site, a push notification.
"""
import asyncio
import logging
import os
from pathlib import Path
import time
from datetime import datetime, timedelta
from urllib.parse import urlsplit

from starlette.concurrency import run_in_threadpool

from services.full_reports import FullReports
from services.mail import SMTPMailer
from services.report_video import ReportVideo

log = logging.getLogger(__name__)
INTERVAL = 120
RETRY = timedelta(minutes=30)
RUNTIME_ROOT = Path(__file__).resolve().parents[2]


def code_revision(root=RUNTIME_ROOT):
    """Detect replaced dependencies before an old process reads new media caches."""
    paths = [root/'scripts/deliver-full-reports.py']
    for directory in ('backend/services', 'backend/domain'):
        paths.extend(sorted((root/directory).glob('*.py')))
    return tuple((str(path.relative_to(root)), path.stat().st_mtime_ns, path.stat().st_size)
                 for path in paths if path.is_file())



def app_url():
    """The public app address. PUBLIC_APP_URL, or the app the password-reset link already opens."""
    reset = os.environ.get('PASSWORD_RESET_URL', '')
    url = os.environ.get('PUBLIC_APP_URL', '') or (reset[:-len('reset-password/')] if reset.endswith('/reset-password/') else '')
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        return ''
    return url.rstrip('/')


class ReportDelivery:
    def __init__(self, db, reports=None, video=None, mailer=None, push=None, clock=datetime.utcnow):
        self.db = db
        self.reports = reports or FullReports(db)
        self.video = video or ReportVideo(db, reports=self.reports)
        self.mailer = mailer or SMTPMailer()
        self.push, self.clock = push, clock

    async def pending(self):
        now = self.clock()
        rows = await self.db.full_report_orders.find(
            {'state': 'paid', 'is_archived': {'$ne': True}, '$and': [
                {'$or': [{'livemode': self.reports.config.live}, {'payment_provider': 'telegram'}]},
                {'$or': [{'media_notify_retry_at': {'$exists': False}}, {'media_notify_retry_at': {'$lte': now}}]}]},
            {'revision': 1, 'media_notified_revision': 1}).sort('created_at', 1).to_list(200)
        return [row['_id'] for row in rows if row.get('media_notified_revision') != row.get('revision', 1)]

    async def tick(self):
        """One pass; returns how many owners were notified."""
        notified = 0
        pending = await self.pending()
        self.progress = {'pending': len(pending), 'ready': 0, 'preparing': 0, 'failed': 0}
        for order_id in pending:
            order = await self.db.full_report_orders.find_one({'_id': order_id})
            if not order:
                continue
            try:
                # Builds the report once, queues the interpretation, then all audio chapters and the video.
                order = await self.reports.materialize(order)
                if order.get('analysis_status') != 'ready' or not order.get('report'):
                    self.progress['preparing'] += 1
                    continue
                state = self.video.state(order['report'])
            except Exception:
                self.progress['failed'] += 1
                log.warning('Full-report background delivery deferred')
                continue
            if state['status'] == 'ready' and state['audio_ready'] == state['audio_total']:
                self.progress['ready'] += 1
                notified += await self.announce(order, state)
            else:
                self.progress['failed' if state['status'] == 'failed' else 'preparing'] += 1
        self.progress['notified'] = notified
        return notified

    async def announce(self, order, state):
        revision = order.get('revision', 1)
        claimed = await self.db.full_report_orders.update_one(
            {'_id': order['_id'], 'media_notified_revision': {'$ne': revision}, **self.reports.revision_filter(order)},
            {'$set': {'media_notified_revision': revision, 'media_notified_at': self.clock()}, '$unset': {'media_notify_retry_at': ''}})
        if not claimed.modified_count:
            return 0
        user = await self.db.users.find_one({'id': order['user_id']}, {'email': 1, 'telegram_only': 1, 'telegram_identity': 1})
        link = app_url() + '/full-report/?order_id=' + order['_id'] if app_url() else ''
        try:
            if not user or not user.get('email'):
                raise RuntimeError('Owner has no email address')
            if user.get('telegram_only'):
                from services.telegram import TelegramAccounts
                accounts = TelegramAccounts(self.db)
                identity = user.get('telegram_identity', '')
                if not identity.startswith(accounts.config.bot_id + ':'):
                    raise RuntimeError('Telegram owner needs relinking')
                recipient = int(identity.split(':')[1])
                linked = await accounts.find(recipient)
                if not linked or linked['id'] != order['user_id']:
                    raise RuntimeError('Telegram owner unavailable')
                await accounts.bot.call('sendMessage', chat_id=recipient,
                    text='Ваш полный разбор NumerOM готов: текст, озвучка глав и видео доступны в личном кабинете.',
                    reply_markup={'inline_keyboard': [[{'text': 'Мои разборы', 'web_app': {'url': accounts.app_link('full-report')}}]]})
            else:
                await self.mailer.send_report_ready(user['email'], link, round(state.get('seconds', 0) / 60), state['audio_total'])
        except Exception:
            # Release the claim: the next pass after RETRY sends again; no duplicate is possible while claimed.
            await self.db.full_report_orders.update_one(
                {'_id': order['_id'], 'media_notified_revision': revision},
                {'$unset': {'media_notified_revision': '', 'media_notified_at': ''}, '$set': {'media_notify_retry_at': self.clock() + RETRY}})
            log.warning('Full-report ready notification deferred')
            return 0
        log.info('Full-report ready notification sent for revision %s', revision)
        await self.notify_devices(order['user_id'], link)
        return 1

    async def notify_devices(self, user_id, link):
        """Site push subscriptions, best effort: the email is the delivery guarantee."""
        if self.push is None:
            return
        try:
            for subscription in await self.push.get_user_subscriptions(user_id):
                await run_in_threadpool(self.push.send_notification, subscription, 'Полный разбор NumerOM готов',
                                        'Текст, озвучка всех глав и видео уже в личном кабинете.', url=link or '/')
        except Exception:
            log.warning('Full-report push deferred')

    async def run(self):
        from services.report_files import write_json
        loaded_revision = code_revision()
        while True:
            # launchd KeepAlive starts a fresh interpreter with consistent module versions.
            # In-place deployment alone cannot update Python imports in a running process.
            if code_revision() != loaded_revision:
                log.info('Full-report delivery code changed; restarting to load current media versions')
                return
            progress = {'checked_at': time.time(), 'status': 'ok'}
            try:
                await self.tick()
                progress.update(self.progress)
            except Exception as error:
                progress.update(status='error', error_type=type(error).__name__)
                log.warning('Full-report delivery pass failed; retrying')
            write_json(RUNTIME_ROOT/'backend/private/runtime/report-delivery-state.json', progress)
            await asyncio.sleep(INTERVAL)
