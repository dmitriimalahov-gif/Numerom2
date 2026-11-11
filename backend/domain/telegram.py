"""Telegram's signed Mini App identity; prices and secrets stay on the server."""
import hashlib
import hmac
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from dotenv import dotenv_values
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TelegramConfig:
    def __init__(self, env=None):
        if env is None:
            path = Path(__file__).resolve().parents[1] / 'private/runtime/telegram.env'
            env = {**(dotenv_values(path) if path.is_file() else {}), **os.environ}
        self.token = env.get('TELEGRAM_BOT_TOKEN', '')
        self.enabled = bool(re.fullmatch(r'[0-9]{5,20}:[A-Za-z0-9_-]{20,100}', self.token))
        self.bot_id = self.token.split(':', 1)[0] if self.enabled else ''
        self.app_url = env.get('TELEGRAM_APP_URL', 'https://dmitriimalahov-gif.github.io/numerom-app').rstrip('/')
        url = urlsplit(self.app_url)
        if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError('TELEGRAM_APP_URL must be an HTTPS application URL')
        # No implicit EUR/Stars conversion or unapproved prices.
        self.prices = json.loads(env.get('TELEGRAM_STARS_PRICES', '{}'))
        if not isinstance(self.prices, dict) or any(type(v) is not int or not 1 <= v <= 100000 for v in self.prices.values()):
            raise ValueError('Telegram Stars prices must be positive integers')
        self.support = env.get('TELEGRAM_SUPPORT_USERNAME', '').lstrip('@')
        if self.support and not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{4,31}', self.support):
            raise ValueError('Invalid Telegram support username')
        if set(self.prices) - {'one_time', 'monthly', 'annual', 'master_consultation', 'full_report'}:
            raise ValueError('Unknown Telegram Stars product')

    def require(self):
        if not self.enabled:
            raise HTTPException(503, 'Telegram-бот ещё не подключён.')


def verify_init_data(raw, config, *, now=None):
    config.require()
    if not isinstance(raw, str) or not 1 <= len(raw) <= 12000:
        raise HTTPException(401, 'Откройте NumerOM из меню Telegram-бота.')
    try:
        pairs = parse_qsl(raw, keep_blank_values=True, strict_parsing=True, max_num_fields=30)
        values = dict(pairs)
        if len(values) != len(pairs):
            raise ValueError('Duplicate fields')
        signature = values.pop('hash')
        if not re.fullmatch('[a-f0-9]{64}', signature):
            raise ValueError('Invalid signature')
        check = '\n'.join(f'{k}={v}' for k, v in sorted(values.items()))
        secret = hmac.new(b'WebAppData', config.token.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError('Bad signature')
        age = (time.time() if now is None else now) - int(values['auth_date'])
        if not -30 <= age <= 600:
            raise ValueError('Expired launch')
        user = json.loads(values['user'])
        if type(user.get('id')) is not int or not 0 < user['id'] < 2**52 or user.get('is_bot'):
            raise ValueError('Invalid user')
        if values.get('chat_type') not in (None, 'sender', 'private'):
            raise ValueError('Private chat required')
        return user
    except (ValueError, KeyError, TypeError, AttributeError):
        raise HTTPException(401, 'Данные Telegram недействительны или устарели. Откройте приложение заново.') from None


class TelegramLaunch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    init_data: str = Field(min_length=1, max_length=12000)


class TelegramRegistration(TelegramLaunch):
    full_name: str = Field(min_length=1, max_length=150)
    birth_date: str = Field(pattern=r'^\d{2}\.\d{2}\.\d{4}$')

    @field_validator('full_name')
    @classmethod
    def name(cls, value):
        if not value.strip():
            raise ValueError('Укажите имя')
        return value.strip()

    @field_validator('birth_date')
    @classmethod
    def birth(cls, value):
        date = datetime.strptime(value, '%d.%m.%Y')
        if date.year < 1900 or date > datetime.now():
            raise ValueError('Проверьте дату рождения')
        return value


class TelegramLink(TelegramLaunch):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class TelegramInvoice(BaseModel):
    model_config = ConfigDict(extra='forbid')
    package_type: str = Field(pattern=r'^(one_time|monthly|annual|master_consultation)$')
    request_id: str = Field(pattern=r'^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$')
