"""Administrative diagnostics and bounded repair of already-paid report jobs."""
import asyncio
import hashlib
import json
import re
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator

from services.admin_management import AdminManagementService
from services.full_reports import FullReports
from services.report_files import digest, folder, read_json
from services.report_insights import ReportInsights, VERSION as INSIGHT_VERSION, compose
from services.report_video import ReportVideo


class ReportRetry(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: UUID
    expected_revision: StrictInt = Field(ge=1, le=1000)
    reason: StrictStr = Field(min_length=1, max_length=500)

    @field_validator('request_id')
    @classmethod
    def uuid4(cls, value):
        if value.version != 4:
            raise ValueError('UUIDv4 required')
        return value

    @field_validator('reason')
    @classmethod
    def meaningful_reason(cls, value):
        if not value.strip():
            raise ValueError('Укажите причину повторной подготовки')
        return value.strip()


class AdminReports:
    def __init__(self, db, reports=None, insights=None, movies=None):
        self.db = db
        self.accounts = AdminManagementService(db)
        self.reports = reports or FullReports(db)
        self.insights = insights or ReportInsights()
        self.movies = movies or ReportVideo(db, reports=self.reports)

    def stages(self, order):
        # Reading this screen must never create jobs or signed customer links.
        empty = {'audio': {'ready': 0, 'total': 0, 'review': 0},
                 'video': {'status': 'not_started', 'message': 'Ожидает готового текста и озвучки.'}}
        if order['state'] != 'paid':
            return {**empty, 'analysis': {'status': 'unpaid', 'message': 'Подготовка начнётся после подтверждения оплаты.'}}
        report = order.get('report')
        if not report:
            return {**empty, 'analysis': {'status': 'not_started', 'message': 'Расчёт ещё не сохранён. Можно повторить подготовку без оплаты.'}}
        key = digest(INSIGHT_VERSION, report)
        target = folder(self.insights.root, key)
        saved = read_json(target / 'ready.json')
        if saved and saved.get('key') == key and saved.get('provider') == 'ollama':
            try:
                report = compose(report, saved['result'], saved['model'], transport_provider=saved.get('transport_provider', 'ollama'))
            except (ValueError, KeyError, TypeError):
                return {**empty, 'analysis': {'status': 'review', 'message': 'Текст требует повторной проверки.'}}
        else:
            failed = (target / 'failed.json').exists()
            return {**empty, 'analysis': {'status': 'review' if failed else 'preparing',
                'message': 'Текст требует повторной проверки.' if failed else 'Ожидает подготовки текста разбора.'}}
        statuses = [self.movies.voice.state(item)['status'] for item in report.get('narration', [])]
        video = self.movies.state(report)
        return {'analysis': {'status': 'ready', 'message': 'Текст прошёл проверку.'},
                'audio': {'ready': statuses.count('ready'), 'total': len(statuses), 'review': statuses.count('review')},
                'video': {key: video[key] for key in ('status', 'message', 'progress') if key in video}}

    async def list(self, actor_id, q='', state='all', page=1, page_size=10):
        await self.accounts.authorize(actor_id)
        if not 1 <= page <= 10000 or not 1 <= page_size <= 20 or state not in ('all', 'paid', 'pending', 'expired') or len(q) > 120:
            raise HTTPException(422, 'Неверные параметры списка')
        query = {}
        if state == 'pending':
            query['state'] = {'$in': ['pending', 'creating']}
        elif state != 'all':
            query['state'] = state
        if q.strip():
            expression = {'$regex': re.escape(q.strip()), '$options': 'i'}
            owners = await self.db.users.find({'$or': [{key: expression} for key in ('name', 'full_name', 'surname', 'email')]}, {'id': 1}).limit(500).to_list(500)
            query['$or'] = [{'_id': q.strip()}, {'user_id': {'$in': [u['id'] for u in owners]}}]
        total = await self.db.full_report_orders.count_documents(query)
        orders = await self.db.full_report_orders.find(query).sort([('created_at', -1), ('_id', 1)]).skip((page - 1) * page_size).limit(page_size).to_list(page_size)
        users = await self.db.users.find({'id': {'$in': [o['user_id'] for o in orders]}}, {'id': 1, 'name': 1, 'surname': 1, 'full_name': 1, 'email': 1, 'is_disabled': 1}).to_list(page_size)
        owners = {user['id']: user for user in users}
        rows = []
        for order in orders:
            owner = owners.get(order['user_id'], {})
            stages = await asyncio.to_thread(self.stages, order)
            rows.append({'id': order['_id'], 'user': {'id': order['user_id'],
                'name': owner.get('full_name') or ' '.join(filter(None, [owner.get('name'), owner.get('surname')])) or 'Пользователь',
                'email': owner.get('email', '')}, 'birth_date': order['birth_date'], 'created_at': order['created_at'],
                'status': order['state'], 'revision': order.get('revision', 1), 'mode': 'live' if order['livemode'] else 'test',
                'amount_total': order['amount_total'], 'currency': order['currency'], **stages,
                'can_retry': order['state'] == 'paid' and order['livemode'] == self.reports.config.live
                    and bool(owner) and not owner.get('is_disabled') and stages['video']['status'] != 'ready'})
        return {'reports': rows, 'total': total, 'page': page, 'page_size': page_size}

    async def retry(self, actor_id, order_id, body):
        await self.accounts.authorize(actor_id)
        order = await self.db.full_report_orders.find_one({'_id': order_id})
        if not order:
            raise HTTPException(404, 'Заказ не найден')
        if order['state'] != 'paid':
            raise HTTPException(409, 'Подготовку можно повторять только для оплаченного заказа.')
        if order['livemode'] != self.reports.config.live:
            raise HTTPException(409, 'Режим оплаты заказа отличается от текущего режима сервера.')
        if order.get('revision', 1) != body.expected_revision:
            raise HTTPException(409, 'Состав отчёта изменился. Обновите список.')
        request_id = str(body.request_id)
        fingerprint = hashlib.sha256(json.dumps(body.model_dump(mode='json'), sort_keys=True).encode()).hexdigest()
        receipt = order.get('admin_retry') or {}
        same = receipt.get('id') == request_id
        if same and receipt.get('fingerprint') != fingerprint:
            raise HTTPException(409, 'Этот запрос уже используется для другого действия.')
        if same and receipt.get('status') == 'done':
            return {'order_id': order_id, 'queued': True}
        now = datetime.utcnow()
        attempts = [entry for entry in order.get('admin_retry_times', []) if isinstance(entry, datetime) and now - timedelta(hours=1) < entry <= now]
        if not same and (len(attempts) >= 3 or attempts and now - max(attempts) < timedelta(seconds=60)):
            raise HTTPException(429, 'Повтор доступен раз в минуту, не более трёх раз в час. Готовые материалы сохраняются.')
        # A pending receipt can be resumed using the same UUID after an ambiguous
        # network response. CAS prevents concurrent admins from claiming new jobs.
        if not same:
            guard = {'admin_retry': order['admin_retry']} if 'admin_retry' in order else {'admin_retry': {'$exists': False}}
            changed = await self.db.full_report_orders.update_one({'_id': order_id, 'state': 'paid',
                **self.reports.revision_filter(order), **guard}, {'$set': {'admin_retry': {'id': request_id,
                    'fingerprint': fingerprint, 'status': 'pending', 'at': now}, 'admin_retry_times': [*attempts, now]},
                '$push': {'admin_audit': {'$each': [{'actor_id': actor_id, 'action': 'retry_generation', 'reason': body.reason,
                    'at': now, 'revision': body.expected_revision, 'request_id': request_id}], '$slice': -100}}})
            if not changed.matched_count:
                raise HTTPException(409, 'Заказ изменился. Обновите список перед повтором.')
        try:
            # The existing paid-owner pipeline verifies the current snapshot and
            # only requeues its clips; no payment or credit mutation is called.
            await self.movies.status(order['user_id'], order_id, retry=True)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(503, 'Повтор пока не завершён. Отправьте тот же запрос ещё раз; новая оплата не нужна.')
        await self.db.full_report_orders.update_one({'_id': order_id, 'admin_retry.id': request_id,
            **self.reports.revision_filter(order)}, {'$set': {'admin_retry.status': 'done'}})
        return {'order_id': order_id, 'queued': True}
