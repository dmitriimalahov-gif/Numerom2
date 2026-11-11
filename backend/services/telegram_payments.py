"""Telegram Stars checkout. Only authenticated Bot API updates grant credits."""
import hashlib
import re
from datetime import datetime, timedelta
from urllib.parse import urlsplit

from fastapi import HTTPException
from domain.payments import PACKAGES
from services.telegram import TelegramAccounts
from services.credit_history import flush_pending_credit_transactions
from services.telegram_pricing import current_prices


class TelegramPayments:
    def __init__(self, db, accounts=None):
        self.db = db
        self.accounts = accounts or TelegramAccounts(db)
        self.config = self.accounts.config

    async def user(self, uid):
        user = await self.db.users.find_one({'id': uid, 'is_disabled': {'$ne': True}})
        identity = (user or {}).get('telegram_identity', '')
        if not identity.startswith(self.config.bot_id + ':') or not self.config.enabled:
            raise HTTPException(403, 'Сначала войдите через Telegram.')
        found = await self.accounts.find(int(identity.split(':')[1]))
        if not found or found['id'] != uid:
            raise HTTPException(403, 'Повторите вход через Telegram.')
        return user, int(identity.split(':')[1])

    async def catalog(self, uid):
        await self.user(uid)
        prices = await current_prices(self.db, self.config)
        return {'currency': 'XTR', 'packages': [dict(id=key, **value, stars=prices.get(key),
                    enabled=key in prices) for key, value in PACKAGES.items()],
                'message': 'Стоимость в Telegram Stars ещё настраивается.' if not any(key in prices for key in PACKAGES) else None}

    async def create(self, uid, request):
        user, telegram_id = await self.user(uid)
        product = PACKAGES[request.package_type]
        key = hashlib.sha256(f'telegram-stars:{self.config.bot_id}:{uid}:{request.request_id}'.encode()).hexdigest()
        now = datetime.utcnow()
        order = await self.db.telegram_orders.find_one({'_id': key})
        if not order:
            amount = (await current_prices(self.db, self.config)).get(request.package_type)
            if not amount:
                raise HTTPException(503, 'Стоимость этого пакета в Telegram Stars ещё не настроена.')
            order = {'_id': key, 'user_id': uid, 'telegram_id': telegram_id, 'bot_id': self.config.bot_id,
                     'package_type': request.package_type, 'amount': amount, 'currency': 'XTR',
                     **product, 'created_at': now, 'expires_at': now + timedelta(hours=24), 'state': 'pending'}
            await self.db.telegram_orders.update_one({'_id': key}, {'$setOnInsert': order}, upsert=True)
            order = await self.db.telegram_orders.find_one({'_id': key})
        if order['package_type'] != request.package_type or order['user_id'] != uid:
            raise HTTPException(409, 'Эта попытка относится к другому пакету.')
        if order['state'] != 'pending':
            return self.public(order)
        if order['expires_at'] < now:
            return self.public(order)
        if not order.get('invoice_url'):
            link = await self.accounts.bot.call('createInvoiceLink', title=order['title'],
                description=f'{order["credits"]} баллов NumerOM. Разовая покупка.', payload=key,
                provider_token='', currency='XTR', prices=[{'label': order['title'], 'amount': order['amount']}])
            parsed = urlsplit(link)
            if parsed.scheme != 'https' or parsed.hostname != 't.me' or parsed.port or parsed.username or parsed.password or not parsed.path.startswith('/$'):
                raise HTTPException(503, 'Telegram вернул неверную ссылку оплаты.')
            await self.db.telegram_orders.update_one({'_id': key, 'state': 'pending'}, {'$set': {'invoice_url': link}})
            order = await self.db.telegram_orders.find_one({'_id': key})
        return self.public(order)

    @staticmethod
    def public(order):
        value = {key: order.get(key) for key in ('state', 'amount', 'currency', 'credits', 'title', 'invoice_url')} | {'order_id': order['_id']}
        if order['state'] == 'pending' and order['expires_at'] < datetime.utcnow():
            value.update(state='expired', invoice_url=None)
        return value

    async def status(self, uid, key):
        await self.user(uid)
        order = await self.db.telegram_orders.find_one({'_id': key, 'user_id': uid})
        if not order:
            raise HTTPException(404, 'Платёж не найден.')
        return self.public(order)

    async def report_catalog(self, uid):
        await self.user(uid)
        from services.full_reports import FullReports
        catalog = await FullReports(self.db).catalog(uid)
        price = (await current_prices(self.db, self.config)).get('full_report')
        return {**catalog, 'payment_provider': 'telegram', 'currency': 'XTR', 'amount_total': price or 0,
                'mode': 'live', 'clients': ['telegram'], 'enabled': bool(price),
                'message': None if price else 'Стоимость разбора в Telegram Stars ещё настраивается.'}

    async def create_report(self, uid, request):
        _, telegram_id = await self.user(uid)
        from services.full_reports import FullReports, owner_reference
        from services.report_files import digest
        from domain.full_report_purchase import TITLE, DESCRIPTION
        reports = FullReports(self.db)
        key = hashlib.sha256(f'telegram-report:{self.config.bot_id}:{uid}:{request.request_id}'.encode()).hexdigest()
        existing = await self.db.full_report_orders.find_one({'_id': key})
        if existing and (existing['birth_date'] != request.birth_date or
                existing.get('checkout_use_profile') != request.use_profile or
                existing.get('checkout_profile_fingerprint') != request.profile_fingerprint):
            raise HTTPException(409, 'Эта попытка относится к другому составу разбора.')
        if not existing:
            price = (await current_prices(self.db, self.config)).get('full_report')
            if not price:
                raise HTTPException(503, 'Стоимость разбора в Telegram Stars ещё не настроена.')
            user, _ = await self.user(uid)
            snapshot = await reports.profile_snapshot(user, request.birth_date) if request.use_profile else None
            if request.use_profile and digest('full-report-profile-v1', snapshot) != request.profile_fingerprint:
                raise HTTPException(409, {'code': 'full_report_profile_changed', 'message': 'Профиль изменился. Проверьте состав отчёта.'})
            now = datetime.utcnow()
            existing = {'_id': key, 'user_id': uid, 'owner_ref': owner_reference(uid), 'birth_date': request.birth_date,
                'as_of_date': now.date().isoformat(), 'report_version': 1, 'revision': 1, 'title': TITLE,
                'description': DESCRIPTION, 'amount_total': price, 'currency': 'XTR', 'livemode': True,
                'payment_provider': 'telegram', 'state': 'pending', 'created_at': now, 'updated_at': now,
                'checkout_use_profile': request.use_profile, 'checkout_profile_fingerprint': request.profile_fingerprint,
                'profile_snapshot': snapshot, 'profile_fingerprint': request.profile_fingerprint}
            await self.db.full_report_orders.update_one({'_id': key}, {'$setOnInsert': existing}, upsert=True)
            existing = await self.db.full_report_orders.find_one({'_id': key})
        if (existing['birth_date'] != request.birth_date or existing.get('checkout_use_profile') != request.use_profile
                or existing.get('checkout_profile_fingerprint') != request.profile_fingerprint):
            raise HTTPException(409, 'Эта попытка относится к другому составу разбора.')
        order = {'_id': key, 'user_id': uid, 'telegram_id': telegram_id, 'bot_id': self.config.bot_id,
                 'package_type': 'full_report', 'amount': existing['amount_total'], 'currency': 'XTR',
                 'title': TITLE, 'credits': 0, 'state': existing['state'], 'created_at': existing['created_at'],
                 'expires_at': existing['created_at'] + timedelta(hours=24)}
        await self.db.telegram_orders.update_one({'_id': key}, {'$setOnInsert': order}, upsert=True)
        order = await self.db.telegram_orders.find_one({'_id': key})
        if order['state'] == 'pending' and order['expires_at'] < datetime.utcnow():
            raise HTTPException(409, 'Срок оплаты истёк. Отмените попытку и создайте новую.')
        if order['state'] == 'pending' and not order.get('invoice_url'):
            link = await self.accounts.bot.call('createInvoiceLink', title=TITLE, description=DESCRIPTION,
                payload=key, provider_token='', currency='XTR', prices=[{'label': TITLE, 'amount': order['amount']}])
            parsed = urlsplit(link)
            if parsed.scheme != 'https' or parsed.hostname != 't.me' or parsed.port or parsed.username or parsed.password or not parsed.path.startswith('/$'):
                raise HTTPException(503, 'Некорректная ссылка Telegram.')
            await self.db.telegram_orders.update_one({'_id': key, 'state': 'pending'}, {'$set': {'invoice_url': link}})
            order['invoice_url'] = link
        if order.get('invoice_url'):
            await self.db.full_report_orders.update_one({'_id': key, 'state': 'pending'}, {'$set': {'checkout_url': order['invoice_url']}})
        return reports.public(await self.db.full_report_orders.find_one({'_id': key}))

    async def check(self, telegram_id, payment, *, pre_checkout=False):
        key = payment.get('invoice_payload', '')
        if not isinstance(key, str) or not re.fullmatch('[a-f0-9]{64}', key):
            raise HTTPException(400, 'Платёж не относится к NumerOM.')
        order = await self.db.telegram_orders.find_one({'_id': key, 'bot_id': self.config.bot_id})
        user = await self.accounts.find(telegram_id)
        if (not order or not user or order['user_id'] != user['id'] or order['telegram_id'] != telegram_id
                or payment.get('currency') != 'XTR' or type(payment.get('total_amount')) is not int
                or payment['total_amount'] != order['amount']):
            raise HTTPException(400, 'Владелец или сумма платежа не совпадают с заказом.')
        if pre_checkout:
            query_id = payment.get('id')
            if not isinstance(query_id, str) or not 1 <= len(query_id) <= 256:
                raise HTTPException(400, 'Отсутствует идентификатор подтверждения.')
            claimed = await self.db.telegram_orders.update_one({'_id': key, 'state': 'pending',
                'expires_at': {'$gt': datetime.utcnow()},
                '$or': [{'pre_checkout_id': {'$exists': False}}, {'pre_checkout_id': query_id}]},
                {'$set': {'pre_checkout_id': query_id}})
            if not claimed.matched_count:
                raise HTTPException(409, 'Эта попытка уже подтверждается, завершена или истекла.')
        return order

    async def fulfill(self, telegram_id, payment):
        order = await self.check(telegram_id, payment)
        if order['state'] == 'refunded':
            raise HTTPException(409, 'Этот платёж возвращён. Требуется проверка поддержки.')
        charge = payment.get('telegram_payment_charge_id')
        if not isinstance(charge, str) or not 1 <= len(charge) <= 512:
            raise HTTPException(400, 'Отсутствует подтверждение платежа Telegram.')
        key = order['_id']; now = datetime.utcnow()
        # The unique charge record prevents a receipt being applied to another order.
        charge_key = hashlib.sha256(charge.encode()).hexdigest()
        await self.db.telegram_charges.update_one({'_id': charge_key}, {'$setOnInsert': {
            'order_id': key, 'charge_id': charge, 'user_id': order['user_id'], 'created_at': now}}, upsert=True)
        receipt = await self.db.telegram_charges.find_one({'_id': charge_key})
        if receipt['order_id'] != key or (order.get('charge_id') and order['charge_id'] != charge):
            raise HTTPException(409, 'Подтверждение относится к другому платежу.')
        claimed = await self.db.telegram_orders.update_one({'_id': key, 'state': {'$ne': 'refunded'},
            '$or': [{'charge_id': {'$exists': False}}, {'charge_id': charge}]}, {'$set': {'charge_id': charge}})
        if not claimed.matched_count:
            raise HTTPException(409, 'Заказ уже оплачен другим платежом. Требуется проверка возврата.')
        if order['package_type'] == 'full_report':
            result = await self.db.full_report_orders.update_one(
                {'_id': key, 'user_id': order['user_id'], 'payment_provider': 'telegram', 'refunded_at': {'$exists': False}},
                {'$set': {'state': 'paid', 'telegram_charge_id': charge, 'updated_at': now}})
            if not result.matched_count:
                if await self.db.full_report_orders.find_one({'_id': key, 'refunded_at': {'$exists': True}}):
                    raise HTTPException(409, 'Платёж возвращён.')
                raise HTTPException(503, 'Оплаченный разбор пока недоступен. Подтверждение будет повторено.')
            await self.db.telegram_orders.update_one({'_id': key, 'state': {'$ne': 'refunded'}}, {'$set': {'state': 'paid', 'charge_id': charge, 'paid_at': now}})
            return self.public(await self.db.telegram_orders.find_one({'_id': key}))
        marker = 'fulfilled_telegram_payments.' + key
        event = {'id': 'telegram-stars-' + key, 'user_id': order['user_id'], 'transaction_type': 'credit',
                 'amount': order['credits'], 'category': 'purchase', 'description': 'Telegram Stars · ' + order['title'],
                 'details': {'currency': 'XTR', 'stars': order['amount']}, 'created_at': now}
        values = {'credits_remaining': {'$add': [{'$ifNull': ['$credits_remaining', 0]}, order['credits']]},
                  marker: {'$literal': {'at': now, 'charge_id': charge}},
                  'pending_credit_transactions': {'$concatArrays': [{'$ifNull': ['$pending_credit_transactions', []]}, {'$literal': [event]}]}}
        if order.get('access_days'):
            current = {'$cond': [{'$eq': [{'$type': '$subscription_expires_at'}, 'date']}, '$subscription_expires_at', now]}
            values.update(is_premium=True, subscription_type='annual' if order['access_days'] == 365 else 'monthly',
                          subscription_expires_at={'$add': [{'$max': [now, current]}, order['access_days'] * 86400000]})
        await self.db.users.update_one({'id': order['user_id'], marker: {'$exists': False}}, [{'$set': values}])
        if not await self.db.users.find_one({'id': order['user_id'], marker: {'$exists': True}}):
            raise HTTPException(503, 'Зачисление будет повторно проверено.')
        if order.get('consultation'):
            await self.db.personal_consultations.update_one({'_id': 'telegram-' + key}, {'$setOnInsert': {
                'id': 'telegram-' + key, 'assigned_user_id': order['user_id'], 'title': 'Персональная консультация мастера',
                'description': 'Оплачено. Материалы появятся после подготовки мастером.', 'cost_credits': 0,
                'is_active': True, 'created_at': now, 'updated_at': now}}, upsert=True)
        await flush_pending_credit_transactions(self.db, order['user_id'])
        await self.db.telegram_orders.update_one({'_id': key, 'state': {'$ne': 'refunded'}}, {'$set': {'state': 'paid', 'charge_id': charge, 'paid_at': now}})
        return self.public(await self.db.telegram_orders.find_one({'_id': key}))

    async def record_refund(self, telegram_id, payment):
        """Keep refunds out of replay fulfillment and retain an operator review trail.

        Used credits/access need human review; never silently subtract a guessed balance.
        """
        key = payment.get('invoice_payload', '')
        charge = payment.get('telegram_payment_charge_id')
        order = await self.db.telegram_orders.find_one({'_id': key, 'bot_id': self.config.bot_id,
            'telegram_id': telegram_id}) if isinstance(key, str) and isinstance(charge, str) else None
        if not order or (order.get('charge_id') and order['charge_id'] != charge) or payment.get('currency') != 'XTR' or type(payment.get('total_amount')) is not int or payment['total_amount'] != order['amount']:
            raise HTTPException(400, 'Возврат требует проверки.')
        await self.db.telegram_orders.update_one({'_id': key}, {'$set': {'state': 'refunded', 'charge_id': charge, 'refunded_at': datetime.utcnow()}})
        if order['package_type'] == 'full_report':
            await self.db.full_report_orders.update_one({'_id': key}, {'$set': {'state': 'expired', 'refunded_at': datetime.utcnow()}})
        await self.db.telegram_payment_review.update_one({'_id': 'refund:' + key}, {'$setOnInsert': {
            'order_id': key, 'user_id': order['user_id'], 'reason': 'refund_entitlement_review',
            'status': 'needs_attention', 'created_at': datetime.utcnow()}}, upsert=True)
