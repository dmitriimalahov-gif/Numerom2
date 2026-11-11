#!/usr/bin/env python3
"""One durable Telegram long-polling worker. No public update/webhook endpoint."""
import argparse
import asyncio
import fcntl
import json
import os
import sys
from pathlib import Path

from numerom_services import service_root
ROOT = service_root()
sys.path.insert(0, str(ROOT / 'backend'))
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException
from domain.telegram import TelegramConfig
from services.telegram import TelegramAccounts
from services.telegram_payments import TelegramPayments


async def handle(accounts, payments, update):
    if query := update.get('pre_checkout_query'):
        try:
            await payments.check(query['from']['id'], query, pre_checkout=True)
            await accounts.bot.call('answerPreCheckoutQuery', pre_checkout_query_id=query['id'], ok=True)
        except HTTPException as error:
            if error.status_code >= 500:
                raise
            await accounts.bot.call('answerPreCheckoutQuery', pre_checkout_query_id=query['id'], ok=False,
                                    error_message='Не удалось подтвердить заказ. Откройте NumerOM и создайте новую попытку оплаты.')
        return
    callback = update.get('callback_query')
    message = (callback or {}).get('message') or update.get('message') or {}
    actor = (callback or {}).get('from') or message.get('from') or {}
    chat = message.get('chat') or {}
    if chat.get('type') != 'private' or type(chat.get('id')) is not int or chat['id'] <= 0:
        return
    # Payment service messages can have a service sender. Bind them to the private
    # chat and persisted order owner, never to callback/message text supplied by a user.
    if not callback and (refund := message.get('refunded_payment')):
        await payments.record_refund(chat['id'], refund)
        return
    if not callback and (payment := message.get('successful_payment')):
        await payments.fulfill(chat['id'], payment)
        await accounts.menu(chat['id'])
        return
    # Never reveal account/balance data through another actor's callback.
    if chat.get('id') != actor.get('id') or actor.get('is_bot'):
        return
    uid = actor['id']
    if callback:
        await accounts.bot.call('answerCallbackQuery', callback_query_id=callback['id'])
        if callback.get('data') == 'balance':
            await accounts.menu(uid)
        return
    command = (message.get('text') or '').split(' ', 1)[0].split('@', 1)[0]
    if command in ('/help', '/support', '/paysupport', '/terms'):
        support = '@' + accounts.config.support if accounts.config.support else 'Владелец NumerOM настраивает контакт поддержки.'
        await accounts.bot.call('sendMessage', chat_id=uid, text=(
            'Все функции доступны через кнопку NumerOM. /balance — обновить баланс, /menu — разделы.\n'
            'Покупки внутри Telegram оплачиваются Telegram Stars. Баллы начисляются только после подтверждения Telegram. '
            'По ошибкам оплаты и возвратам: ' + support))
    else:
        await accounts.menu(uid)


async def run(configure=False):
    load_dotenv(ROOT / 'backend/.env')
    config = TelegramConfig(); config.require()
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['MONGODB_DATABASE']]
    accounts = TelegramAccounts(db, config); payments = TelegramPayments(db, accounts)
    try:
        await accounts.indexes()
        identity = await accounts.bot.call('getMe')
        if not identity.get('is_bot') or str(identity['id']) != config.bot_id:
            raise RuntimeError('Unexpected Telegram bot identity')
        print(json.dumps({'bot': identity['username'], 'connected': True}), flush=True)
        if configure:
            await accounts.bot.call('setMyCommands', commands=[{'command': c, 'description': t} for c, t in [
                ('start', 'Вход и регистрация'), ('menu', 'Все разделы NumerOM'), ('balance', 'Мои баллы'),
                ('help', 'Помощь'), ('paysupport', 'Поддержка оплаты')]])
            await accounts.bot.call('setChatMenuButton', menu_button={'type': 'web_app', 'text': 'NumerOM',
                                    'web_app': {'url': accounts.app_link()}})
            await accounts.bot.call('setMyDescription', description='NumerOM: личные числа, обучение, разборы, аудио и видео. Баланс баллов сразу после регистрации.')
        hook = await accounts.bot.call('getWebhookInfo')
        if hook.get('url'):
            raise RuntimeError('Existing webhook detected; refusing to replace it')
        offset_key = 'telegram-offset:' + config.bot_id
        saved = await db.telegram_runtime.find_one({'_id': offset_key})
        offset = (saved or {}).get('offset', 0)
        while True:
            try:
                updates = await accounts.bot.call('getUpdates', offset=offset, timeout=25,
                    allowed_updates=['message', 'callback_query', 'pre_checkout_query'], limit=25)
                for update in updates:
                    try:
                        await handle(accounts, payments, update)
                    except HTTPException as error:
                        if error.status_code >= 500:
                            raise
                        # Keep a durable private record of rejected payments; never drop a receipt silently.
                        message = update.get('message') or {}
                        if message.get('successful_payment') or message.get('refunded_payment'):
                            await db.telegram_payment_review.update_one({'_id': str(update['update_id'])}, {'$setOnInsert': {
                                'payment': message.get('successful_payment') or message.get('refunded_payment'), 'telegram_id': (message.get('from') or {}).get('id'),
                                'status': 'needs_attention', 'http_status': error.status_code}}, upsert=True)
                        elif (message.get('chat') or {}).get('type') == 'private':
                            try:
                                await accounts.bot.call('sendMessage', chat_id=message['chat']['id'],
                                    text='Не удалось выполнить действие. Откройте NumerOM и повторите вход. /help — помощь.')
                            except HTTPException as delivery_error:
                                if delivery_error.status_code >= 500:
                                    raise
                    offset = update['update_id'] + 1
                    await db.telegram_runtime.update_one({'_id': offset_key}, {'$set': {'offset': offset}}, upsert=True)
            except (HTTPException, OSError):
                print(json.dumps({'state': 'retrying', 'reason': 'telegram_or_backend_unavailable'}), flush=True)
                await asyncio.sleep(5)
    finally:
        client.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--configure', action='store_true')
    args = parser.parse_args(); os.umask(0o077)
    folder = ROOT / 'backend/private/runtime'; folder.mkdir(parents=True, exist_ok=True)
    with (folder / 'telegram-bot.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            asyncio.run(run(args.configure))
        except KeyboardInterrupt:
            pass
        except Exception as error:
            print(json.dumps({'state': 'stopped', 'error_type': type(error).__name__}), flush=True)
            sys.exit(1)
