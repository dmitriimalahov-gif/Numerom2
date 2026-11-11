"""Atomic paid reports: a durable receipt and debit share the user's commit.

Archives are idempotent outbox deliveries. A retry always resolves the original
request before checking a current price, so network loss cannot charge twice.
"""
import inspect
import hashlib
import json
import logging
from datetime import datetime, timezone
from fastapi import HTTPException
from models import CreditsDeductionConfig
from services.credit_debit import flush_pending_calculations
from services.credit_history import flush_pending_credit_transactions
from services.student_learning import _student

log = logging.getLogger(__name__)


class PaidCalculations:
    def __init__(self, db, *, namespace, report_key, prices, build, metadata, key_prefix=''):
        self.db, self.namespace, self.report_key = db, namespace, report_key
        self.prices, self.build, self.metadata, self.key_prefix = prices, build, metadata, key_prefix

    def receipt(self, record):
        date = record['created_at']
        if isinstance(date, datetime):
            date = date.replace(tzinfo=timezone.utc).isoformat()
        return {'id': record['id'], 'request_id': record['request_id'], 'created_at': date,
                'cost': record['cost'], 'results': record['results'][self.report_key]}

    async def catalog(self, uid):
        await _student(self.db, uid)
        config = await self.db.credits_deduction_config.find_one({'is_active': True})
        defaults = CreditsDeductionConfig().model_dump()
        prices = {kind: (config or {}).get(key, defaults[key]) for kind, key in self.prices.items()}
        return {kind: value if type(value) is int and 0 <= value <= 1000000 else None
                for kind, value in prices.items()}

    async def saved(self, uid, key, user):
        # Delivery writes the archive before removing the outbox; read outbox first.
        pending = next((item for item in user.get('pending_calculations', [])
                        if item.get('id') == key and item.get('user_id') == uid), None)
        return pending or await self.db.numerology_calculations.find_one({'_id': key, 'user_id': uid})

    async def deliver(self, uid):
        for operation in (flush_pending_calculations, flush_pending_credit_transactions):
            try:
                await operation(self.db, uid)
            except Exception:
                log.warning('Calculation archive delivery deferred; committed outbox retained')

    async def calculate(self, uid, data):
        user = await _student(self.db, uid)
        key = hashlib.sha256((self.key_prefix + uid + ':' + str(data.request_id)).encode()).hexdigest()
        body = data.model_dump(mode='json', exclude={'request_id'})
        fingerprint = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

        async def replay(current):
            marker = current.get(self.namespace, {}).get(key)
            if not marker:
                return None
            if marker != fingerprint:
                raise HTTPException(409, 'Эта попытка относится к другим данным. Начните новый расчёт.')
            record = await self.saved(uid, key, current)
            if not record:
                raise HTTPException(503, 'Результат сохраняется. Повторите проверку той же попытки.')
            await self.deliver(uid)
            return self.receipt(record)

        previous = await replay(user)
        if previous:
            return previous
        price = (await self.catalog(uid))[data.kind]
        if price is None:
            raise HTTPException(503, 'Стоимость расчёта временно недоступна')
        if price != data.expected_cost:
            raise HTTPException(409, 'Стоимость изменилась. Обновите цену перед расчётом.')
        result = self.build(data)
        if inspect.isawaitable(result):
            result = await result
        kind, description, birth_date = self.metadata(data)
        now = datetime.utcnow()
        now = now.replace(microsecond=(now.microsecond // 1000) * 1000)
        record = {'id': key, 'request_id': str(data.request_id), 'user_id': uid, 'created_at': now,
                  'calculation_type': kind, 'birth_date': birth_date, 'cost': price,
                  'results': {**result['legacy'], self.report_key: result}}
        transaction = {'id': self.namespace + '-' + key, 'user_id': uid, 'transaction_type': 'debit',
                       'amount': -price, 'category': 'numerology', 'created_at': now,
                       'description': description, 'details': {'calculation_type': kind, 'calculation_id': key}}
        pending = {'pending_calculations': record}
        if price:
            pending['pending_credit_transactions'] = transaction
        field = self.namespace + '.' + key
        updated = await self.db.users.update_one(
            {'id': uid, 'is_disabled': {'$ne': True}, field: {'$exists': False}, 'credits_remaining': {'$gte': price}},
            {'$inc': {'credits_remaining': -price}, '$set': {field: fingerprint}, '$push': pending})
        if not updated.matched_count:
            previous = await replay(await _student(self.db, uid))
            if previous:
                return previous
            raise HTTPException(402, 'Недостаточно баллов. Пополните баланс.')
        await self.deliver(uid)
        return self.receipt(record)

    async def history(self, uid):
        user = await _student(self.db, uid)
        pending = [record for record in user.get('pending_calculations', [])
                   if record.get('user_id') == uid and record.get('results', {}).get(self.report_key, {}).get('version') == 1]
        rows = await self.db.numerology_calculations.find(
            {'user_id': uid, f'results.{self.report_key}.version': 1}).sort('created_at', -1).limit(30).to_list(30)
        combined = {record['id']: record for record in rows + pending}
        records = sorted(combined.values(), key=lambda record: (record['created_at'], record['id']), reverse=True)[:30]
        return {'calculations': [self.receipt(record) for record in records]}
