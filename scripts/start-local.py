#!/usr/bin/env python3
"""Start the existing local NumerOM installation without stopping other services."""
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from numerom_services import ROOT as SERVICE_ROOT, PYTHON

ROOT = Path(__file__).resolve().parents[1]
LOGS = SERVICE_ROOT / 'backend/private/runtime'


def occupied(port):
    with socket.socket() as connection:
        connection.settimeout(1)
        return connection.connect_ex(('127.0.0.1', port)) == 0


def ready(url, expected):
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return response.status == expected
    except urllib.error.HTTPError as error:
        return error.code == expected
    except (OSError, urllib.error.URLError):
        return False


def ensure_service(label, port, url, expected, command, cwd, env):
    if occupied(port):
        if not ready(url, expected):
            raise RuntimeError(f'Порт {port} занят, но {label} не отвечает. Чужой процесс не остановлен.')
        print(f'{label}: уже работает.', flush=True)
        return
    logfile = LOGS / f'{label}.log'
    with logfile.open('ab') as log:
        os.chmod(logfile, 0o600)
        process = subprocess.Popen(command, cwd=cwd, env=env,
                                   stdin=subprocess.DEVNULL, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f'{label} завершился. Журнал: {logfile}')
        if ready(url, expected):
            print(f'{label}: запущен (PID {process.pid}).', flush=True)
            return
        time.sleep(1)
    raise RuntimeError(f'{label} ещё не готов. Журнал: {logfile}')


def main():
    if not PYTHON.is_file():
        raise RuntimeError('Не найден backend/.venv. Сначала установите зависимости проекта.')
    if Path(sys.prefix).resolve() != PYTHON.parent.parent.resolve():
        os.execv(str(PYTHON), [str(PYTHON), str(Path(__file__).resolve())])
    from dotenv import dotenv_values
    from pymongo import MongoClient

    config = dotenv_values(SERVICE_ROOT / 'backend/.env')
    if not config.get('MONGO_URL'):
        raise RuntimeError('В backend/.env не настроен MONGO_URL.')
    with MongoClient(config['MONGO_URL'], serverSelectionTimeoutMS=4000) as client:
        client.admin.command('ping')
    print('База NumerOM: доступна.', flush=True)
    candidates = sorted((Path.home() / '.nvm/versions/node').glob('v*/bin/node'),
                        key=lambda path: tuple(int(n) for n in path.parent.parent.name[1:].split('.')),
                        reverse=True)
    node = next((path for path in candidates if int(path.parent.parent.name[1:].split('.')[0]) >= 22), None)
    if node is None:
        raise RuntimeError('Для этой установки требуется Node.js 22 или новее в ~/.nvm.')
    craco = ROOT / 'frontend/node_modules/@craco/craco/dist/bin/craco.js'
    if not craco.is_file():
        raise RuntimeError('Не установлены зависимости frontend.')
    LOGS.mkdir(parents=True, exist_ok=True, mode=0o700)
    env = {**os.environ, 'PATH': str(node.parent) + ':' + os.environ.get('PATH', ''),
           'BROWSER': 'none', 'HOST': '127.0.0.1', 'PORT': '5128',
           'GENERATE_SOURCEMAP': 'false'}
    ensure_service('api', 8000, 'http://127.0.0.1:8000/api/user/profile-v2', 401,
                   [str(PYTHON), '-m', 'uvicorn', 'server:app', '--host', '127.0.0.1',
                    '--port', '8000', '--no-access-log'], SERVICE_ROOT / 'backend', env)
    ensure_service('frontend', 5128, 'http://127.0.0.1:5128/', 200,
                   [str(node), str(craco), 'start'], ROOT / 'frontend', env)
    print('\nОткрыть NumerOM: http://127.0.0.1:5128/')
    print('Публичная мобильная версия отдельно требует работающего туннеля к API.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Database/transport exceptions can include connection credentials.
        print(str(error) if isinstance(error, RuntimeError) else
              f'Запуск не выполнен ({type(error).__name__}). Проверьте MongoDB и локальную конфигурацию.',
              file=sys.stderr)
        sys.exit(1)
