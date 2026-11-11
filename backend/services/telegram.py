"""Shared NumerOM accounts and private Telegram menus; no parallel balances."""
import asyncio
import hashlib
import json
import secrets
import urllib.request
import urllib.error
import uuid
from datetime import datetime

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from auth import create_access_token, get_password_hash
from domain.telegram import TelegramConfig, verify_init_data
from models import User, LoginRequest
from services.accounts import AccountService, public_profile
from services.credit_history import flush_pending_credit_transactions

SECTIONS = [
    ('Личные числа', 'numbers'), ('Полный разбор', 'full-report'),
    ('Совместимость', 'relationships'), ('Имя, адрес, телефон, автомобиль', 'number-tools'),
    ('Время и планетарный маршрут', 'vedic-time'), ('Самонаблюдение', 'assessment'),
    ('Обучение и практика', 'learning'), ('Библиотека схем', 'library'),
    ('Аудиогид', 'audio-guide'), ('Консультации', 'consultations'),
    ('Бизнес и команды', 'business'), ('Пополнить баллы', 'top-up'),
    ('История баллов', 'credits'), ('Профиль', 'profile'),
]


class BotAPI:
    def __init__(self, config):
        self.config = config

    async def call(self, method, **payload):
        self.config.require()
        def send():
            request = urllib.request.Request(
                f'https://api.telegram.org/bot{self.config.token}/{method}',
                data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(request, timeout=40) as response:
                    data = json.load(response)
            except urllib.error.HTTPError as error:
                # 400/403 (for example a blocked bot) must not poison the update queue.
                code = error.code if error.code in (400, 403) else 503
                raise HTTPException(code, 'Telegram отклонил операцию.') from None
            except (urllib.error.URLError, TimeoutError, ValueError):
                # Exceptions from HTTP libraries can contain the token-bearing URL.
                raise HTTPException(503, 'Telegram временно недоступен. Повторите позже.') from None
            if not data.get('ok'):
                raise HTTPException(503, 'Telegram не подтвердил операцию.')
            return data['result']
        return await asyncio.to_thread(send)


class TelegramAccounts:
    def __init__(self, db, config=None, bot=None):
        self.db = db
        self.config = config or TelegramConfig()
        self.bot = bot or BotAPI(self.config)

    async def indexes(self):
        await self.db.users.create_index('telegram_identity', unique=True, sparse=True)

    def identity(self, telegram_id):
        self.config.require()
        return self.config.bot_id + ':' + str(telegram_id)

    async def find(self, telegram_id):
        user = await self.db.users.find_one({'telegram_identity': self.identity(telegram_id)})
        if user and (user.get('is_disabled') or user.get('telegram_auth_version', 0) != user.get('auth_version', 0)):
            raise HTTPException(403, 'Вход через Telegram отключён. Войдите в существующий аккаунт заново.')
        return user

    def session(self, user):
        role = 'admin' if user.get('is_admin') or user.get('is_super_admin') else 'user'
        return {'access_token': create_access_token({'sub': user['id'], 'role': role,
                    'auth_version': user.get('auth_version', 0), 'login_provider': 'telegram'}),
                'token_type': 'bearer', 'user': public_profile(user)}

    async def login(self, data):
        identity = verify_init_data(data.init_data, self.config)
        user = await self.find(identity['id'])
        if not user:
            return {'registration_required': True}
        return self.session(user)

    async def register(self, data):
        telegram = verify_init_data(data.init_data, self.config)
        await self.indexes()
        identity = self.identity(telegram['id'])
        existing = await self.find(telegram['id'])
        if existing:
            return self.session(existing)
        uid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'numerom:telegram:' + identity))
        # An unguessable password cannot be used as an alternative Telegram login.
        password = await asyncio.to_thread(get_password_hash, secrets.token_urlsafe(32))
        user = User(id=uid, email=f'tg-{self.config.bot_id}-{telegram["id"]}@telegram.numerom.invalid',
                    password_hash=password, full_name=data.full_name,
                    name=data.full_name.split()[0], surname=' '.join(data.full_name.split()[1:]) or None,
                    birth_date=data.birth_date, city='', credits_remaining=10).model_dump()
        event = {'id': 'telegram-welcome-' + uid, 'user_id': uid, 'transaction_type': 'credit',
                 'amount': 10, 'category': 'purchase', 'description': 'Приветственный бонус при регистрации',
                 'details': {'reason': 'registration_bonus'}, 'created_at': datetime.utcnow()}
        user.update(_id='telegram:' + identity, telegram_identity=identity, telegram_only=True,
                    telegram_auth_version=0, pending_credit_transactions=[event])
        try:
            await self.db.users.update_one({'_id': user['_id']}, {'$setOnInsert': user}, upsert=True)
        except DuplicateKeyError:
            pass  # Concurrent registration/link: use the sole identity owner.
        current = await self.find(telegram['id'])
        if not current:
            raise HTTPException(503, 'Регистрация не завершена. Повторите вход.')
        await flush_pending_credit_transactions(self.db, current['id'])
        return self.session(current)

    async def link(self, data):
        telegram = verify_init_data(data.init_data, self.config)
        login = await AccountService(self.db).login(LoginRequest(email=data.email.strip(), password=data.password))
        uid = login.user.id
        await self.indexes()
        identity = self.identity(telegram['id'])
        current = await self.db.users.find_one({'id': uid})
        try:
            query = {'id': uid, 'is_disabled': {'$ne': True},
                     'auth_version': current.get('auth_version') if 'auth_version' in current else {'$exists': False},
                     '$or': [{'telegram_identity': identity}, {'telegram_identity': {'$exists': False}}]}
            result = await self.db.users.update_one(query, {'$set': {
                'telegram_identity': identity, 'telegram_auth_version': current.get('auth_version', 0)}})
            linked = await self.db.users.find_one({'id': uid, 'telegram_identity': identity})
            if not result.matched_count or not linked:
                raise HTTPException(409, 'Этот аккаунт уже связан с другим Telegram.')
        except DuplicateKeyError:
            raise HTTPException(409, 'Этот Telegram уже связан с другим аккаунтом NumerOM.') from None
        return self.session(linked)

    def app_link(self, section='home'):
        allowed = {path for _, path in SECTIONS} | {'home', 'admin'}
        if section not in allowed:
            section = 'home'
        return f'{self.config.app_url}/telegram/?section={section}'

    async def menu(self, telegram_id):
        user = await self.find(telegram_id)
        if not user:
            return await self.bot.call('sendMessage', chat_id=telegram_id,
                text='Добро пожаловать в NumerOM! Создайте аккаунт или войдите в существующий. После регистрации баланс сразу появится в меню.',
                reply_markup={'inline_keyboard': [[{'text': 'Войти / зарегистрироваться', 'web_app': {'url': self.app_link()}}]]})
        balance = user.get('credits_remaining', 0)
        buttons = [[{'text': f'Баланс: {balance} баллов · обновить', 'callback_data': 'balance'}],
                   [{'text': 'Открыть NumerOM', 'web_app': {'url': self.app_link()}}]]
        sections = SECTIONS + ([('Кабинет администратора', 'admin')] if user.get('is_admin') or user.get('is_super_admin') else [])
        buttons.extend([[{'text': label, 'web_app': {'url': self.app_link(path)}}] for label, path in sections])
        await self.bot.call('setChatMenuButton', chat_id=telegram_id,
            menu_button={'type': 'web_app', 'text': f'{balance} баллов · NumerOM', 'web_app': {'url': self.app_link()}})
        return await self.bot.call('sendMessage', chat_id=telegram_id,
            text=f'NumerOM\nВаш баланс: {balance} баллов\nВсе разделы открываются внутри Telegram.',
            reply_markup={'inline_keyboard': buttons})
