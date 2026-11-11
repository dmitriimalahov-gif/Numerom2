"""NumerOM launchd services. Helper's services and repositories are untouched."""
import argparse
import json
import os
import plistlib
import subprocess
import sys
import time
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]

def service_root(source=SOURCE_ROOT):
    pointer = source / 'backend/private/runtime/service-location.json'
    if not pointer.exists():
        return source
    info = pointer.stat()
    if pointer.is_symlink() or info.st_uid != os.getuid() or info.st_mode & 0o022:
        raise RuntimeError('Unsafe NumerOM service location')
    value = json.loads(pointer.read_text())
    root = Path(value['root'])
    if not root.is_absolute() or root.resolve() != root or not (root / '.data-initialized').is_file():
        raise RuntimeError('NumerOM service runtime is not initialized')
    if not (root / 'backend/server.py').is_file() or not (root / 'scripts/numerom_services.py').is_file():
        raise RuntimeError('NumerOM service runtime is incomplete')
    return root

ROOT = service_root()
SERVICE_PYTHON = ROOT / 'backend/.service-venv/bin/python'
PYTHON = SERVICE_PYTHON if SERVICE_PYTHON.is_file() else ROOT / 'backend/.venv/bin/python'
SERVICE_VOICE_PYTHON = ROOT / 'backend/.service-voice-venv/bin/python'
VOICE_PYTHON = (SERVICE_VOICE_PYTHON if SERVICE_VOICE_PYTHON.is_file()
                else Path.home()/'Developer/helper-voice/.venv-tts/bin/python')
RUNTIME = ROOT / 'backend/private/runtime'
PREFIX = 'md.numerom.app.'
DOMAIN = f'gui/{os.getuid()}'
AGENTS = Path.home() / 'Library/LaunchAgents'
PATH = f'{Path.home()}/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin'

def specifications():
    return {
        'api': [str(PYTHON), '-m', 'uvicorn', 'server:app', '--host', '127.0.0.1', '--port', '8000', '--no-access-log'],
        'gateway': [str(PYTHON), '-m', 'uvicorn', 'public_gateway:create_app', '--factory', '--host', '127.0.0.1', '--port', '8004', '--no-access-log'],
        'tunnel': [str(Path.home()/'.local/bin/cloudflared'), 'tunnel', '--url', 'http://127.0.0.1:8004', '--protocol', 'http2', '--no-autoupdate'],
        'watchdog': [str(PYTHON), str(ROOT/'scripts/numerom_watchdog.py')],
        'awake': ['/usr/bin/caffeinate','-i','-s'],
        'report-voice': [str(VOICE_PYTHON), '-B', '-u', str(ROOT/'scripts/generate-project-voices.py'), '--watch', '--reuse-models', '--auto-retry'],
        'report-analysis': [str(PYTHON), '-u', str(ROOT/'scripts/generate-report-media.py'), '--kind', 'insights', '--watch'],
        'report-video': [str(PYTHON), '-u', str(ROOT/'scripts/generate-report-media.py'), '--kind', 'video', '--watch'],
        'report-delivery': [str(PYTHON), '-u', str(ROOT/'scripts/deliver-full-reports.py')],
        'daily-email': [str(PYTHON), '-u', str(ROOT/'scripts/send-daily-emails.py')],
    }

def service_plist(name, args):
    data = {'Label': PREFIX+name, 'ProgramArguments': args, 'WorkingDirectory': str(ROOT/'backend'),
            'EnvironmentVariables': {'PATH': PATH, 'PYTHONUNBUFFERED': '1', 'LANG': 'en_US.UTF-8'},
            'RunAtLoad': True, 'StandardOutPath': str(RUNTIME/f'managed-{name}.log'),
            'StandardErrorPath': str(RUNTIME/f'managed-{name}.log')}
    if name == 'report-video':
        environment = data['EnvironmentVariables']
        # Native Chromium is verified outside macOS protected Desktop folders.
        desktop = Path.home() / 'Desktop'
        protected_checkout = sys.platform == 'darwin' and (ROOT == desktop or desktop in ROOT.parents)
        environment['NUMEROM_VIDEO_RUNTIME'] = 'docker' if protected_checkout else 'native'
        if protected_checkout:
            environment['PATH'] += ':/Applications/Docker.app/Contents/Resources/bin'
    if name == 'watchdog':
        data.update(StartInterval=60, ProcessType='Background')
    else:
        data.update(KeepAlive=True, ThrottleInterval=10)
    if name in ('report-voice', 'report-video'):
        # Without a ProcessType launchd throttles a job to background QoS: a full-report video rendered
        # 12× slower and never finished within its 6-hour budget (measured 24.10.2026). Nice keeps the
        # desktop responsive while speech and Chromium run at full speed.
        data.update(ProcessType='Interactive', Nice=5)
    return data

def launch(*args):
    return subprocess.run(['launchctl', *args], capture_output=True, text=True, timeout=20)

def loaded(name):
    return launch('print', f'{DOMAIN}/{PREFIX}{name}').returncode == 0

def restart(name):
    if name not in specifications():
        raise ValueError('Unknown NumerOM service')
    result = launch('kickstart', '-k', f'{DOMAIN}/{PREFIX}{name}')
    if result.returncode:
        raise RuntimeError(f'Cannot restart NumerOM {name}')

def install(names):
    AGENTS.mkdir(parents=True, exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True, mode=0o700)
    for name, args in specifications().items():
        if names and name not in names:
            continue
        path = AGENTS/(PREFIX+name+'.plist')
        content = plistlib.dumps(service_plist(name, args))
        changed = not path.exists() or path.read_bytes() != content
        if changed:
            path.write_bytes(content)
            path.chmod(0o600)
            if loaded(name):
                launch('bootout', f'{DOMAIN}/{PREFIX}{name}')
                # bootout returns before the job is gone; bootstrapping too early skipped the restart.
                for _ in range(50):
                    if not loaded(name):
                        break
                    time.sleep(0.2)
        if not loaded(name):
            result = launch('bootstrap', DOMAIN, str(path))
            if result.returncode:
                raise RuntimeError(f'Cannot install NumerOM {name}: launchctl code {result.returncode}')
        print(f'{name}: installed', flush=True)

def status():
    for name in specifications():
        result = launch('print', f'{DOMAIN}/{PREFIX}{name}')
        fields = [line.strip() for line in result.stdout.splitlines() if line.strip().startswith(('state =', 'pid =', 'last exit code ='))]
        print(name, ', '.join(fields) if result.returncode == 0 else 'not installed')
    path = RUNTIME/'watchdog-state.json'
    if path.exists():
        state = json.loads(path.read_text())
        print(json.dumps({k:state.get(k) for k in ('checked_at','api','public_ready','published','last_error')}, ensure_ascii=False))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install','status','restart'])
    parser.add_argument('services', nargs='*', choices=list(specifications()))
    args = parser.parse_args()
    if args.action == 'install': install(args.services)
    elif args.action == 'restart':
        for name in args.services: restart(name)
    else: status()
