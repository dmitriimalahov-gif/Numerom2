"""Separate Stripe entitlement; no credits, subscriptions, or other purchases change."""
import asyncio
import hashlib
import logging
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from domain.full_report_purchase import AMOUNT_TOTAL, CURRENCY, DESCRIPTION, INTEGRATION, TITLE
from domain.full_report_profile import snapshot_profile
from services.report_files import digest
from services.payments import PaymentConfig, StripeProvider, unpaid_state
from services.student_learning import _student

log = logging.getLogger(__name__)
MAX_ARCHIVED_REVISIONS = 20
MAX_REPORT_ORDER_BYTES = 12 * 1024 * 1024


def owner_reference(user_id):
    return hashlib.sha256(('numerom-full-report-owner-v1:' + user_id).encode()).hexdigest()


class FullReports:
    def __init__(self, db, config=None, provider=None, builder=None):
        self.db = db
        self.config = config or PaymentConfig()
        self.provider = provider or StripeProvider(self.config)
        self.builder = builder

    def build(self, *args):
        """Paid purchase and profile extension use the same arithmetic builder."""
        builder = self.builder
        if builder is None:
            from domain.full_report import build_full_report
            builder = build_full_report
        return builder(*args)

    def available(self):
        if not self.config.enabled:
            raise HTTPException(503, 'Оплата отчёта временно недоступна. Деньги и баллы не списаны.')

    async def catalog(self, user_id):
        await _student(self.db, user_id)
        return {'title': TITLE, 'description': DESCRIPTION, 'amount_total': AMOUNT_TOTAL,
                'currency': CURRENCY, 'recurring': False, 'enabled': bool(self.config.enabled),
                'mode': self.config.mode, 'clients': list(self.config.returns),
                'message': None if self.config.enabled else 'Оплата временно недоступна. Подключение Stripe ещё настраивается.',
                'includes': ['Числа даты рождения и их значения', 'Квадрат Пифагора, линии и диагонали',
                             'Планетарные соответствия и авторские схемы', 'Жизненные циклы и личные периоды',
                             'Полный сохранённый отчёт с графиками', 'Озвучка разделов мужским голосом',
                             'Имя, фамилия, адрес, автомобиль и телефон из подтверждённого профиля',
                             'Планетарные часы и маршрут на 30 дней по городу профиля',
                             'Персональный видеоразбор MP4 со схемами', 'Смысловой разбор и практики по вашим расчётам']}

    async def profile_snapshot(self, user, birth_date):
        if user.get('birth_date') != birth_date:
            raise HTTPException(409, {'code': 'full_report_profile_changed', 'message': 'Дата отчёта отличается от даты владельца профиля. Выберите разбор только по дате или исправьте профиль.'})
        snapshot = snapshot_profile(user)
        def locations():
            from services.geography import city_index
            current = birth = None
            if snapshot['fields'].get('city'):
                current = city_index.resolve_unique(snapshot['fields']['city'])
            if snapshot['fields'].get('birth_city_id'):
                birth = city_index.lookup(snapshot['fields']['birth_city_id'])
            return current, birth
        try:
            current, birth = await asyncio.to_thread(locations)
        except Exception:
            current = birth = None
        snapshot['current_location'], snapshot['birth_location'] = current, birth
        # The routes in the report must match the app's route tools, so the author's active modifiers are frozen too.
        from services.vedic_calculations import active_modifiers, frozen_modifiers
        snapshot['planetary_modifiers'] = frozen_modifiers(await active_modifiers(self.db))
        return snapshot

    async def preview(self, user_id, request):
        user = await _student(self.db, user_id)
        snapshot = await self.profile_snapshot(user, request.birth_date) if request.use_profile else None
        from domain.full_report import build_full_report
        target = datetime.now(timezone.utc).date().isoformat()
        report = await asyncio.to_thread(build_full_report, request.birth_date, target, snapshot)
        return {'birth_date': request.birth_date, 'use_profile': request.use_profile,
                'profile_snapshot': snapshot, 'profile_fingerprint': digest('full-report-profile-v1', snapshot) if snapshot else None,
                'available': [{'id': s['id'], 'title': s['title']} for s in report['sections']],
                'excluded': report['excluded'],
                'message': 'В отчёт войдут подтверждённые данные. После оплаты их снимок сохраняется; дополнение оплаченного отчёта не требует новой оплаты.'}

    @staticmethod
    def person(order):
        """«Имя Фамилия» from the profile the report was made with, so a purchase list tells reports apart."""
        fields = (order.get('profile_snapshot') or {}).get('fields') or {}
        name = ' '.join(str(fields.get(key) or '').strip() for key in ('name', 'surname')).strip()
        return (name or str(fields.get('full_name') or '').strip())[:120] or None

    def public(self, order, include_report=False):
        result = {'order_id': order['_id'], 'status': order['state'],
                  'mode': 'live' if order['livemode'] else 'test', 'birth_date': order['birth_date'],
                  'as_of_date': order['as_of_date'], 'amount_total': order['amount_total'],
                  'currency': order['currency'], 'title': order['title'],
                  'revision': order.get('revision', 1), 'use_profile': bool(order.get('profile_fingerprint') or order.get('profile_snapshot')),
                  'profile_fingerprint': order.get('profile_fingerprint'),
                  'previous_revisions': [{'revision': r['revision'], 'created_at': r['created_at'].isoformat() + 'Z',
                      'profile_fingerprint': r.get('profile_fingerprint')} for r in order.get('revisions', [])],
                  'session_id': order.get('session_id'), 'created_at': order['created_at'].isoformat() + 'Z'}
        if order.get('payment_provider') == 'telegram':
            result['payment_provider'] = 'telegram'
        if self.person(order):
            result['person'] = self.person(order)
        if include_report and order.get('profile_snapshot'):
            result['profile_snapshot'] = order['profile_snapshot']
        if order.get('is_archived'):
            result['is_archived'] = True
        if order['state'] == 'pending' and order.get('checkout_url'):
            result['url'] = order['checkout_url']
        if order['state'] == 'paid':
            result['report_status'] = 'ready' if order.get('report') and order.get('analysis_status', 'ready') == 'ready' else 'preparing'
            result['analysis_status'] = order.get('analysis_status', 'preparing')
            if include_report and order.get('report'):
                result['report'] = order['report']
            elif not order.get('report'):
                result['message'] = 'Оплата подтверждена. Отчёт готовится; повторная оплата не нужна.'
        return result

    async def create(self, user_id, request):
        self.available()
        user = await _student(self.db, user_id)
        if request.client not in self.config.returns:
            raise HTTPException(503, 'Возврат после оплаты ещё настраивается.')
        order_id = hashlib.sha256((INTEGRATION + ':' + user_id + ':' + str(request.request_id)).encode()).hexdigest()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        existing = await self.db.full_report_orders.find_one({'_id': order_id, 'user_id': user_id})
        snapshot = None
        if existing is None and request.use_profile:
            snapshot = await self.profile_snapshot(user, request.birth_date)
            if digest('full-report-profile-v1', snapshot) != request.profile_fingerprint:
                raise HTTPException(409, {'code': 'full_report_profile_changed', 'message': 'Данные профиля изменились. Проверьте состав отчёта ещё раз, сохранив эту попытку оплаты.'})
        order = {'_id': order_id, 'user_id': user_id, 'owner_ref': owner_reference(user_id),
                 'birth_date': request.birth_date, 'as_of_date': now.date().isoformat(), 'report_version': 1,
                 'title': TITLE, 'description': DESCRIPTION, 'amount_total': AMOUNT_TOTAL, 'currency': CURRENCY, 'client': request.client,
                 'return_url': self.config.returns[request.client], 'livemode': self.config.live,
                 'state': 'creating', 'created_at': now, 'expires_at': int(time.time()) + 2700,
                 'revision': 1, 'checkout_use_profile': request.use_profile,
                 'checkout_profile_fingerprint': request.profile_fingerprint,
                 'profile_snapshot': snapshot, 'profile_fingerprint': request.profile_fingerprint}
        try:
            if existing is None:
                await self.db.full_report_orders.insert_one(order)
            else:
                order = existing
        except DuplicateKeyError:
            order = await self.db.full_report_orders.find_one({'_id': order_id})
        if any(order[key] != value for key, value in [('birth_date', request.birth_date),
                ('client', request.client), ('livemode', self.config.live)]):
            raise HTTPException(409, 'Эта попытка относится к другому отчёту. Начните новую оплату.')
        if (order.get('checkout_use_profile', False) != request.use_profile or
                order.get('checkout_profile_fingerprint') != request.profile_fingerprint):
            raise HTTPException(409, {'code': 'full_report_attempt_frozen', 'order_id': order['_id'], 'message': 'Состав этой попытки оплаты уже зафиксирован. Откройте сохранённый заказ в истории.'})
        if order['state'] == 'expired' and not order.get('session_id'):
            return self.public(order)
        if order.get('session_id'):
            return self.public(await self.materialize(await self.reconcile(order)), include_report=True)
        if time.time() >= order['expires_at']:
            await self.db.full_report_orders.update_one(
                {'_id': order_id, 'state': 'creating', 'session_id': {'$exists': False}},
                {'$set': {'state': 'expired'}})
            return self.public(await self.materialize(await self.reconcile(
                await self.db.full_report_orders.find_one({'_id': order_id}))), True)
        metadata = {'integration': INTEGRATION, 'order_id': order_id, 'owner_ref': order['owner_ref']}
        return_query = '?service=full-report&order_id=' + order_id
        params = {'mode': 'payment', 'client_reference_id': order_id, 'metadata': metadata,
                  'payment_intent_data': {'metadata': metadata},
                  'success_url': order['return_url'] + return_query + '&session_id={CHECKOUT_SESSION_ID}',
                  'cancel_url': order['return_url'] + return_query + '&cancelled=1',
                  'expires_at': order['expires_at'], 'integration_identifier': 'numerom_full_report_qvhjtxpr',
                  'line_items': [{'price_data': {'currency': CURRENCY, 'unit_amount': AMOUNT_TOTAL,
                                  'product_data': {'name': 'NumerOM · ' + order['title'],
                                                   'description': order.get('description', 'Все расчёты по дате, авторские схемы, смысловой разбор, практики, мужская озвучка и персональный MP4. Разовая оплата.')}}, 'quantity': 1}]}
        try:
            session = await self.provider.create(params, 'numerom-full-report-' + order_id)
        except Exception:
            log.warning('Full-report checkout unavailable; preserving idempotent order')
            raise HTTPException(502, 'Не удалось открыть Stripe. Повторите эту же попытку.')
        url = session.get('url', '')
        parsed = urlsplit(url)
        if (not re.fullmatch(r'cs_(?:test_|live_)?[A-Za-z0-9]+', session.get('id', '')) or
                parsed.scheme != 'https' or parsed.hostname != 'checkout.stripe.com' or parsed.username or parsed.password):
            raise HTTPException(502, 'Stripe вернул некорректную ссылку. Повторите позже.')
        # A webhook may beat the create response. Never roll back paid or bind another session.
        bound = await self.db.full_report_orders.update_one(
            {'_id': order_id, '$or': [{'session_id': {'$exists': False}}, {'session_id': session['id']}]},
            {'$set': {'session_id': session['id'], 'checkout_url': url}})
        if not bound.matched_count:
            raise HTTPException(409, 'Платёж уже связан с другой сессией Stripe.')
        await self.db.full_report_orders.update_one({'_id': order_id, 'state': 'creating'}, {'$set': {'state': 'pending'}})
        return self.public(await self.materialize(await self.db.full_report_orders.find_one({'_id': order_id})), True)

    async def fulfill(self, session):
        metadata = session.get('metadata') or {}
        if metadata.get('integration') != INTEGRATION:
            return None
        order_id = metadata.get('order_id', '')
        if not isinstance(order_id, str) or not re.fullmatch('[a-f0-9]{64}', order_id):
            raise HTTPException(400, 'Некорректный заказ отчёта')
        order = await self.db.full_report_orders.find_one({'_id': order_id})
        if not order:
            raise HTTPException(503, 'Заказ отчёта пока недоступен')
        session_id = session.get('id', '')
        if (not isinstance(session_id, str) or not re.fullmatch(r'cs_(?:test_|live_)?[A-Za-z0-9]+', session_id) or
                session.get('mode') != 'payment' or session.get('client_reference_id') != order_id or
                session.get('livemode') is not order['livemode'] or order['livemode'] != self.config.live or
                metadata.get('owner_ref') != order['owner_ref'] or order['owner_ref'] != owner_reference(order['user_id']) or
                type(session.get('amount_total')) is not int or session['amount_total'] != AMOUNT_TOTAL or
                order['amount_total'] != AMOUNT_TOTAL or session.get('currency') != CURRENCY or
                order['currency'] != CURRENCY or (order.get('session_id') and order['session_id'] != session_id)):
            raise HTTPException(400, 'Параметры платежа не совпали с заказом отчёта')
        if session.get('payment_status') != 'paid':
            return order
        if session.get('status') != 'complete':
            raise HTTPException(400, 'Stripe ещё не завершил оплату отчёта')
        result = await self.db.full_report_orders.update_one(
            {'_id': order_id, '$or': [{'session_id': {'$exists': False}}, {'session_id': session_id}]},
            {'$set': {'state': 'paid', 'session_id': session_id, 'updated_at': datetime.utcnow()}})
        if not result.matched_count:
            raise HTTPException(400, 'Сессия платежа изменилась')
        return await self.db.full_report_orders.find_one({'_id': order_id})

    async def reconcile(self, order, event_type=None):
        if order.get('payment_provider') == 'telegram':
            return order
        if order['livemode'] != self.config.live:
            raise HTTPException(409, 'Режим оплаты изменился. Этот заказ относится к другому режиму.')
        if not order.get('session_id') or order['state'] == 'paid':
            return order
        self.available()
        try:
            session = await self.provider.retrieve(order['session_id'])
        except Exception:
            raise HTTPException(502, 'Пока не удалось проверить Stripe. Проверьте снова позже.')
        return await self.accept_current(session, event_type)

    async def accept_current(self, session, event_type=None):
        order = await self.fulfill(session)
        if not order:
            raise HTTPException(400, 'Платёж не относится к отчёту NumerOM')
        if order['state'] != 'paid':
            state = unpaid_state(order, session, event_type)
            await self.db.full_report_orders.update_one({'_id': order['_id'], 'state': {'$ne': 'paid'},
                '$or': [{'session_id': {'$exists': False}}, {'session_id': session['id']}]},
                {'$set': {'state': state, 'session_id': session['id']}})
            order = await self.db.full_report_orders.find_one({'_id': order['_id']})
        return order

    async def materialize(self, order, *, archived=False):
        if order['state'] != 'paid' or (order.get('payment_provider') != 'telegram' and order['livemode'] != self.config.live):
            return order
        if not order.get('report'):
            try:
                args = (order['birth_date'], order['as_of_date'])
                if order.get('profile_snapshot') is not None:
                    args += (order['profile_snapshot'],)
                report = await asyncio.to_thread(self.build, *args)
                if (not isinstance(report, dict) or report.get('version') != order['report_version'] or
                        report.get('birth_date') != order['birth_date'] or report.get('as_of_date') != order['as_of_date'] or
                        report.get('profile_snapshot') != order.get('profile_snapshot')):
                    raise ValueError('Report builder snapshot mismatch')
                if archived:
                    order = {**order, 'report': report}
                else:
                    await self.db.full_report_orders.update_one(
                        {'_id': order['_id'], 'state': 'paid', 'report': {'$exists': False},
                         **self.revision_filter(order)},
                        {'$set': {'report': report, 'report_created_at': datetime.utcnow()}})
                    order = await self.db.full_report_orders.find_one({'_id': order['_id']})
            except Exception:
                log.warning('Paid full-report generation deferred; purchase remains paid')
                return order
        # Derived interpretation is saved once beside the immutable arithmetic.
        # Display, narration and video consume that same validated text.
        try:
            from services.report_insights import ReportInsights
            interpreted, state = ReportInsights().enrich(order['report'])
            order = {**order, 'report': interpreted, 'analysis_status': state}
        except Exception:
            log.warning('Paid report interpretation deferred; arithmetic remains readable')
            return {**order, 'analysis_status': 'preparing'}
        if state != 'ready' or archived:
            return order
        # Enqueue only the committed snapshot; failures never invalidate a paid report.
        try:
            from services.narration import NarrationService
            narration = NarrationService(self.db)
            for item in order['report'].get('narration', []):
                narration.enqueue(item, 'full-report', order['_id'])
            from services.report_video import ReportVideo
            ReportVideo(self.db).enqueue(order['report'])
        except Exception:
            log.warning('Full-report narration queue deferred; reading remains available')
        return order

    async def owned(self, user_id, order_id):
        user = await _student(self.db, user_id)
        if not isinstance(order_id, str) or not re.fullmatch('[a-f0-9]{64}', order_id):
            raise HTTPException(404, 'Отчёт не найден в вашем аккаунте')
        order = await self.db.full_report_orders.find_one({'_id': order_id, 'user_id': user_id})
        if not order:
            raise HTTPException(404, 'Отчёт не найден в вашем аккаунте')
        if order.get('payment_provider') != 'telegram' and order['livemode'] != self.config.live:
            raise HTTPException(409, 'Этот отчёт относится к другому режиму оплаты.')
        return user, order

    @staticmethod
    def revision_filter(order):
        return {'revision': order['revision']} if 'revision' in order else {'revision': {'$exists': False}}

    async def extend_profile(self, user_id, order_id, request):
        user, order = await self.owned(user_id, order_id)
        if order['state'] != 'paid':
            raise HTTPException(403, 'Дополнение доступно после подтверждения оплаты отчёта.')
        if user.get('birth_date') != order['birth_date']:
            raise HTTPException(409, 'Данные профиля можно добавить только к отчёту владельца с той же датой рождения.')
        # The fingerprint identifies the confirmed snapshot. An ambiguous retry
        # cannot capture subsequently edited data or create another revision.
        if order.get('profile_fingerprint') == request.profile_fingerprint:
            return self.public(await self.materialize(order), True)
        for revision in order.get('revisions', []):
            if revision.get('profile_fingerprint') == request.profile_fingerprint:
                return await self.revision(user_id, order_id, revision['revision'])
        if order.get('revision', 1) != request.expected_revision:
            raise HTTPException(409, 'Отчёт уже дополнен в другой вкладке. Обновите сохранённый отчёт.')
        if len(order.get('revisions', [])) >= MAX_ARCHIVED_REVISIONS:
            raise HTTPException(409, 'Достигнут предел сохранённых дополнений этого отчёта. Все прежние версии доступны в архиве; новые вычисления не запущены.')
        snapshot = await self.profile_snapshot(user, order['birth_date'])
        if digest('full-report-profile-v1', snapshot) != request.profile_fingerprint:
            raise HTTPException(409, 'Профиль изменился после проверки. Проверьте состав дополнения ещё раз.')
        if not order.get('report'):
            await self.materialize(order)
            _, order = await self.owned(user_id, order_id)
            if order.get('revision', 1) != request.expected_revision:
                if order.get('profile_fingerprint') == request.profile_fingerprint:
                    return self.public(await self.materialize(order), True)
                raise HTTPException(409, 'Отчёт уже дополнен в другой вкладке. Обновите сохранённый отчёт.')
            if not order.get('report'):
                raise HTTPException(503, 'Исходный оплаченный отчёт ещё создаётся. Повторите дополнение позже без оплаты.')
        # Keep each old frozen mathematical report, not just mutable profile IDs.
        previous = {key: order[key] for key in ('profile_snapshot', 'profile_fingerprint', 'report', 'report_created_at') if key in order}
        previous.update(revision=order.get('revision', 1), created_at=order.get('revision_created_at', order['created_at']))
        from bson import BSON
        next_report = await asyncio.to_thread(self.build, order['birth_date'], order['as_of_date'], snapshot)
        prospective = {**order, 'revisions': [*order.get('revisions', []), previous],
            'profile_snapshot': snapshot, 'profile_fingerprint': request.profile_fingerprint,
            'report': next_report, 'revision': order.get('revision', 1) + 1}
        if len(BSON.encode(prospective)) > MAX_REPORT_ORDER_BYTES:
            raise HTTPException(409, 'Архив отчёта достиг допустимого объёма. Все сохранённые версии доступны; новое дополнение не запущено.')
        changed = await self.db.full_report_orders.update_one(
            {'_id': order_id, 'user_id': user_id, 'state': 'paid', 'livemode': order['livemode'],
             **self.revision_filter(order), f'revisions.{MAX_ARCHIVED_REVISIONS - 1}': {'$exists': False}},
            {'$push': {'revisions': previous}, '$set': {'revision': order.get('revision', 1) + 1,
                'profile_snapshot': snapshot, 'profile_fingerprint': request.profile_fingerprint,
                'revision_created_at': datetime.utcnow()}, '$unset': {'report': '', 'report_created_at': ''}})
        if not changed.matched_count:
            _, latest = await self.owned(user_id, order_id)
            if latest.get('profile_fingerprint') == request.profile_fingerprint:
                return self.public(await self.materialize(latest), True)
            raise HTTPException(409, 'Отчёт уже дополнен в другой вкладке. Обновите сохранённый отчёт.')
        _, latest = await self.owned(user_id, order_id)
        return self.public(await self.materialize(latest), True)

    async def revision(self, user_id, order_id, revision):
        _, order = await self.owned(user_id, order_id)
        if order['state'] != 'paid':
            raise HTTPException(403, 'Архив доступен после подтверждения оплаты.')
        if order.get('revision', 1) == revision:
            return self.public(await self.materialize(order), True)
        previous = next((r for r in order.get('revisions', []) if r['revision'] == revision), None)
        if previous is None:
            raise HTTPException(404, 'Версия отчёта не найдена')
        archived = {key: value for key, value in order.items()
                    if key not in ('profile_snapshot', 'profile_fingerprint', 'report', 'report_created_at', 'analysis_status')}
        archived.update(previous)
        archived['is_archived'] = True
        return self.public(await self.materialize(archived, archived=True), True)

    async def status(self, user_id, order_id):
        _, order = await self.owned(user_id, order_id)
        return self.public(await self.materialize(await self.reconcile(order)), True)

    async def history(self, user_id):
        await _student(self.db, user_id)
        rows = await self.db.full_report_orders.find({'user_id': user_id, '$or': [{'livemode': self.config.live}, {'payment_provider': 'telegram'}]}, {'report.sections': 0, 'report.raw': 0, 'report.narration': 0, 'report.summary': 0, 'report.profile_snapshot': 0, 'profile_snapshot.issues': 0, 'profile_snapshot.current_location': 0, 'profile_snapshot.birth_location': 0, 'revisions.report': 0, 'revisions.profile_snapshot': 0}).sort('created_at', -1).limit(50).to_list(50)
        return {'orders': [self.public(order) for order in rows]}

    async def cancel(self, user_id, order_id):
        _, order = await self.owned(user_id, order_id)
        if order['state'] == 'paid':
            return self.public(await self.materialize(order), True)
        if order.get('payment_provider') == 'telegram':
            await self.db.telegram_orders.update_one({'_id': order_id, 'state': 'pending'}, {'$set': {'state': 'expired'}})
            await self.db.full_report_orders.update_one({'_id': order_id, 'state': 'pending'}, {'$set': {'state': 'expired'}})
            return self.public(await self.db.full_report_orders.find_one({'_id': order_id}))
        self.available()
        if not order.get('session_id'):
            # Cancelling a failed/ambiguous creation must not trap the user forever.
            # A concurrent verified payment still wins and may promote expired to paid.
            await self.db.full_report_orders.update_one(
                {'_id': order['_id'], 'state': 'creating', 'session_id': {'$exists': False}},
                {'$set': {'state': 'expired', 'updated_at': datetime.utcnow()}})
            order = await self.db.full_report_orders.find_one({'_id': order['_id']})
            if order['state'] == 'paid':
                return self.public(await self.materialize(order), True)
        if order.get('session_id'):
            try:
                await self.provider.expire(order['session_id'])
            except Exception:
                pass  # Paid sessions cannot expire; fetch authoritative state below.
            order = await self.reconcile(order)
        return self.public(await self.materialize(order), True)

    async def narration_source(self, user_id, order_id):
        user, order = await self.owned(user_id, order_id)
        if order['state'] != 'paid':
            raise HTTPException(403, 'Озвучка доступна после подтверждения оплаты отчёта.')
        order = await self.materialize(order)
        # Right after payment the chapters do not exist yet: that is a normal «preparing» state with no
        # records, not a server failure (a 503 reached the buyer as «Не удалось связаться с NumerOM»).
        if order.get('analysis_status', 'ready') != 'ready' or not order.get('report'):
            return user, []
        return user, order['report'].get('narration', [])
