#!/usr/bin/env python3
"""Connect a BotFather bot locally. Token is entered without echo and never logged."""
import argparse
import asyncio
import getpass
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import urllib.request

from numerom_services import service_root
SOURCE = Path(__file__).resolve().parents[1]
ROOT = service_root()
# Setup code is shipped with the feature; the worker always uses deployed runtime.
sys.path.insert(0, str(SOURCE / 'backend'))
from dotenv import dotenv_values
from domain.telegram import TelegramConfig
from services.telegram import BotAPI

LABEL = 'md.numerom.telegram-bot'
PRODUCTS = {'one_time': '10 баллов', 'monthly': 'Месячный пакет', 'annual': 'Годовой пакет',
            'master_consultation': 'Консультация мастера', 'full_report': 'Полный разбор'}


def safe_config_file():
    folder = ROOT / 'backend/private/runtime'
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = folder / 'telegram.env'
    if path.exists() and (path.is_symlink() or path.stat().st_uid != os.getuid()):
        raise RuntimeError('Небезопасный файл настройки Telegram.')
    return path


def write_config(path, values):
    content = ''.join(f'{key}={json.dumps(str(value), ensure_ascii=False)}\n' for key, value in values.items())
    fd, temporary = tempfile.mkstemp(prefix='.telegram-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as output:
            os.fchmod(output.fileno(), 0o600)
            output.write(content)
            output.flush(); os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def deployed(config):
    required = ['backend/domain/telegram.py', 'backend/services/telegram.py',
                'backend/services/telegram_payments.py', 'backend/routers/telegram.py', 'scripts/run-telegram-bot.py']
    if any(not (ROOT / name).is_file() for name in required):
        raise RuntimeError('Серверная часть Telegram ещё не установлена в рабочую копию.')
    if 'create_telegram_router' not in (ROOT / 'backend/server.py').read_text():
        raise RuntimeError('Telegram ещё не подключён к рабочему серверу.')
    # Check public application before exposing its menu to users.
    with urllib.request.urlopen(config.app_url + '/telegram/?section=home', timeout=20) as response:
        html = response.read(2_000_000).decode('utf-8')
        if response.status != 200 or 'numerom-telegram' not in html:
            raise RuntimeError('Мини-приложение Telegram ещё не опубликовано.')


def install():
    domain = f'gui/{os.getuid()}'
    python = ROOT / 'backend/.service-venv/bin/python'
    folder = ROOT / 'backend/private/runtime'
    path = Path.home() / 'Library/LaunchAgents' / (LABEL + '.plist')
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {'Label': LABEL, 'ProgramArguments': [str(python), '-B', '-u', str(ROOT / 'scripts/run-telegram-bot.py'), '--configure'],
            'WorkingDirectory': str(ROOT / 'backend'), 'RunAtLoad': True, 'KeepAlive': True, 'ThrottleInterval': 15,
            'EnvironmentVariables': {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LANG': 'en_US.UTF-8', 'PYTHONUNBUFFERED': '1'},
            'StandardOutPath': str(folder / 'telegram-bot.log'), 'StandardErrorPath': str(folder / 'telegram-bot.log')}
    path.write_bytes(plistlib.dumps(data)); path.chmod(0o600)
    target = domain + '/' + LABEL
    loaded = subprocess.run(['launchctl', 'print', target], capture_output=True).returncode == 0
    if loaded:
        subprocess.run(['launchctl', 'bootout', target], check=True, capture_output=True)
    subprocess.run(['launchctl', 'bootstrap', domain, str(path)], check=True, capture_output=True)
    # Only API config needs reloading. Narration/video services are unrelated.
    subprocess.run(['launchctl', 'kickstart', '-k', domain + '/md.numerom.app.api'], check=True, capture_output=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', action='store_true', help='Start using the already saved token, without prompting')
    parser.add_argument('--prices', action='store_true', help='Configure Stars prices and support contact')
    parser.add_argument('--check', action='store_true', help='Check configuration without changing it')
    parser.add_argument('--configure-only', action='store_true', help='Save config, do not start worker')
    args = parser.parse_args()
    os.umask(0o077)
    path = safe_config_file()
    values = dict(dotenv_values(path)) if path.exists() else {}
    if args.check:
        config = TelegramConfig(values)
        print('Токен настроен:', 'да' if config.enabled else 'нет')
        print('Цен в Stars настроено:', len(config.prices))
        print('Файл настройки:', path)
        return
    if args.start:
        config = TelegramConfig(values); config.require(); deployed(config); install()
        print('Служба Telegram запущена с сохранёнными настройками.')
        return
    if not sys.stdin.isatty():
        raise RuntimeError('Откройте файл «Подключить Telegram бота.command» в Terminal для скрытого ввода токена.')
    print('Подключение NumerOM к боту, созданному в @BotFather. Токен не отправляется в чат.')
    token = getpass.getpass('Токен BotFather (ввод скрыт; Enter сохраняет прежний): ').strip()
    if token: values['TELEGRAM_BOT_TOKEN'] = token
    values.setdefault('TELEGRAM_APP_URL', 'https://1.numer.om')
    config = TelegramConfig(values); config.require()
    identity = asyncio.run(BotAPI(config).call('getMe'))
    if not identity.get('is_bot') or str(identity.get('id')) != config.bot_id:
        raise RuntimeError('Telegram не подтвердил бота.')
    if identity.get('username', '').lower() != 'numerom_bot':
        raise RuntimeError('Этот токен принадлежит другому боту. Нужен токен @numerom_bot.')
    values['TELEGRAM_BOT_USERNAME'] = identity['username']
    print('Подтверждён бот: @' + identity['username'])
    if args.prices:
        support = input('Username поддержки без @ (Enter сохраняет прежний): ').strip().lstrip('@')
        if support: values['TELEGRAM_SUPPORT_USERNAME'] = support
        prices = dict(config.prices)
        print('Цены задаются в целых Telegram Stars. Enter оставляет прежнюю цену; 0 отключает покупку.')
        print('Если цен ещё нет, все бесплатные функции и имеющиеся баллы доступны; покупка пакетов пока выключена.')
        for key, title in PRODUCTS.items():
            raw = input(f'{title} [{prices.get(key, "не задано")}]: ').strip()
            if not raw: continue
            if not raw.isdigit() or not 0 <= int(raw) <= 100000:
                raise RuntimeError('Стоимость должна быть целым числом от 1 до 100000, либо 0 для отключения.')
            if int(raw): prices[key] = int(raw)
            else: prices.pop(key, None)
        if prices and not values.get('TELEGRAM_SUPPORT_USERNAME'):
            raise RuntimeError('Для приёма оплаты укажите контакт поддержки. Настройка пока не сохранена.')
        values['TELEGRAM_STARS_PRICES'] = json.dumps(prices, separators=(',', ':'))
    config = TelegramConfig(values)
    write_config(path, values)
    if args.configure_only:
        print('Настройка сохранена с правами 600. Бот пока не запущен.')
    else:
        try: deployed(config)
        except Exception:
            print('Токен сохранён. Публикация мини-приложения ещё не подтверждена; запуск будет выполнен после неё.')
            return
        install()
        print('Служба подключена. Откройте https://t.me/' + identity['username'] + ' и нажмите /start.')
        print('Фактический вход и баланс проверьте в Telegram; создание службы ещё не подтверждает эту проверку.')


if __name__ == '__main__':
    try: main()
    except KeyboardInterrupt: print('\nПодключение отменено.'); sys.exit(130)
    except Exception as error:
        # Never print exception text from network libraries: it can contain a token URL.
        print('Подключение не завершено. Тип ошибки: ' + type(error).__name__)
        if isinstance(error, RuntimeError): print(str(error))
        sys.exit(1)
