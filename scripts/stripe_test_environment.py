"""Stripe TEST payments for NumerOM, run by the owner; keys are never echoed or logged.

Run «Подключить Stripe (тест).command». Pressing Enter repeats the 16.10.2026
setup: the Stripe CLI provisions a claimable 7-day sandbox without any key, the
payment webhook is registered and the API restarts. Claiming the sandbox by the
printed link makes it permanent; a sandbox that is still valid is reused, and
`--reuse-sandbox` configures it without questions. A pasted sk_test_… key
connects an existing permanent test environment instead. Re-running after the tunnel address changed
moves the same webhook to the new address. The watchdog also synchronizes this
address after tunnel recovery. The return page provides backup reconciliation.
"""
import json
import re
import shutil
import subprocess
import sys
import time
import tomllib
from datetime import date
from getpass import getpass
from pathlib import Path
from urllib.parse import urlsplit
import requests
from dotenv import dotenv_values, set_key, unset_key
from numerom_services import ROOT, restart

ENV = ROOT/'backend/.env'
STATE = ROOT/'backend/private/stripe/runtime.json'
SANDBOX = ROOT/'backend/private/stripe/sandbox-cli.toml'
API = 'https://api.stripe.com/v1'
# The events services/payments.py handles (docs/payments.md).
EVENTS = ['checkout.session.completed', 'checkout.session.async_payment_succeeded',
          'checkout.session.async_payment_failed', 'checkout.session.expired']


def stripe_call(method, path, key, data=None):
    response = requests.request(method, API+path, auth=(key, ''), data=data, timeout=20)
    try: body = response.json()
    except ValueError: body = {}
    if response.status_code != 200:
        raise RuntimeError((body.get('error') or {}).get('message') or f'Stripe HTTP {response.status_code}')
    return body


def save_state(value):
    STATE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = STATE.with_suffix('.pending')
    temporary.write_text(json.dumps(value, indent=2))
    temporary.chmod(0o600)
    temporary.replace(STATE)


def sync_test_webhook(origin):
    """Move only the configured TEST webhook; never create accounts or rotate keys.

    Persist the new URL only after Stripe confirms it, so a failed move is retried
    on the next watchdog tick. Return safe operational status without secrets.
    """
    parsed = urlsplit(origin)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.path not in ('', '/') or parsed.query or parsed.fragment):
        raise ValueError('Expected a public HTTPS origin')
    env = dotenv_values(ENV)
    if env.get('STRIPE_MODE', 'test') != 'test':
        return 'not_test'
    expiry = env.get('STRIPE_SANDBOX_EXPIRES_AT')
    if expiry:
        try: expired = date.fromisoformat(expiry) <= date.today()
        except ValueError: expired = True
        if expired: return 'sandbox_expired'
    key = env.get('STRIPE_SECRET_KEY') or ''
    if (not re.fullmatch(r'(?:[sr]k|rkcs)_test_[A-Za-z0-9]+', key)
            or not (env.get('STRIPE_WEBHOOK_SECRET') or '').startswith('whsec_')
            or not STATE.is_file()):
        return 'not_configured'
    state = json.loads(STATE.read_text())
    endpoint_id = state.get('webhook_id') or ''
    if state.get('mode') != 'test' or not re.fullmatch(r'we_[A-Za-z0-9]+', endpoint_id):
        return 'not_configured'
    url = origin.rstrip('/')+'/api/webhook/stripe'
    if state.get('url') == url:
        return 'ready'
    endpoint = stripe_call('POST', '/webhook_endpoints/'+endpoint_id, key, {'url': url})
    if (endpoint.get('id') != endpoint_id or endpoint.get('url') != url
            or endpoint.get('livemode') is not False or endpoint.get('status') != 'enabled'):
        raise RuntimeError('Stripe did not confirm the TEST webhook address')
    save_state({**state, 'url': url, 'webhook_synced_at': time.time()})
    return 'ready'


def sandbox_profile():
    """Key, expiry, claim link and account of the CLI sandbox while it is still valid; else None."""
    try: profile = tomllib.loads(SANDBOX.read_text())['numerom-credits']
    except (OSError, KeyError, tomllib.TOMLDecodeError): return None
    if not profile.get('test_mode_api_key') or str(profile.get('sandbox_expires_at', '')) <= date.today().isoformat():
        return None
    return profile['test_mode_api_key'], str(profile['sandbox_expires_at']), profile.get('sandbox_claim_url'), profile.get('account_id')


def create_sandbox(email):
    """`stripe sandbox create` into a private CLI profile, as on 16.10.2026; returns sandbox_profile()."""
    cli = shutil.which('stripe') or str(Path.home()/'.local/bin/stripe')
    SANDBOX.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if SANDBOX.exists():
        # A profile that still holds keys makes the CLI open a browser instead of provisioning.
        SANDBOX.rename(SANDBOX.with_name(f'sandbox-cli.replaced-{int(time.time())}.toml'))
    log = SANDBOX.with_name('sandbox-create.log')
    with log.open('w') as output:
        log.chmod(0o600)
        subprocess.run([cli, '--config', str(SANDBOX), '--project-name', 'numerom-credits', 'sandbox', 'create',
                        '--email', email, '--non-interactive'], stdout=output, stderr=subprocess.STDOUT, timeout=120, check=True)
    SANDBOX.chmod(0o600)
    created = sandbox_profile()
    if not created:
        raise KeyError('numerom-credits')
    return created


def connect(reuse=False):
    env = dotenv_values(ENV)
    origin = env.get('PUBLIC_API_URL') or ''
    if not origin.startswith('https://'):
        raise SystemExit('Сначала запустите NumerOM: нужен публичный HTTPS-адрес сервера. Ничего не изменено.')
    url = origin.rstrip('/')+'/api/webhook/stripe'
    expires = claim = account_id = None
    if reuse:
        found = sandbox_profile()
        if not found:
            raise SystemExit('Действующей песочницы Stripe нет: запустите настройку и нажмите Enter. Ничего не изменено.')
        key, expires, claim, account_id = found
    else:
        print('Тестовая оплата Stripe для NumerOM (реальные деньги не списываются).')
        print('• Просто нажмите Enter — будет создана новая тестовая песочница Stripe, как 16.10, ключ не нужен.')
        print('• Или вставьте постоянный тестовый ключ sk_test_… (символы не показываются).')
        key = ''.join(getpass('Ключ или Enter: ').split())
        if not key:
            found = sandbox_profile()
            if not found:
                email = env.get('SMTP_USER') or ''
                email = input(f'Почта владельца для песочницы [{email}]: ').strip() or email
                if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
                    raise SystemExit('Нужна почта владельца аккаунта. Ничего не изменено.')
                try: found = create_sandbox(email)
                except (OSError, subprocess.SubprocessError, KeyError, tomllib.TOMLDecodeError) as error:
                    raise SystemExit(f'Stripe CLI не создал песочницу ({type(error).__name__}). Подробности: {SANDBOX.with_name("sandbox-create.log")}. Настройки сервера не изменены.')
            key, expires, claim, account_id = found
        elif not re.fullmatch(r'sk_test_[A-Za-z0-9]{20,}', key):
            raise SystemExit('Нужен тестовый секретный ключ sk_test_…; боевые ключи здесь не принимаются. Ничего не сохранено.')
    state = json.loads(STATE.read_text()) if STATE.is_file() else {}
    try:
        if account_id is None:
            # A permanent key: confirm test mode and its account. A claimable sandbox key
            # cannot read these endpoints; the CLI profile already names its account.
            if stripe_call('GET', '/balance', key).get('livemode'):
                raise SystemExit('Stripe сообщил о боевом режиме. Ничего не сохранено.')
            account_id = stripe_call('GET', '/account', key)['id']
        same = (state.get('account_id') == account_id and state.get('webhook_id') and env.get('STRIPE_SECRET_KEY') == key
                and (env.get('STRIPE_WEBHOOK_SECRET') or '').startswith('whsec_'))
        if same:
            # Re-run after a tunnel change: keep the endpoint and its signing secret.
            endpoint = stripe_call('POST', '/webhook_endpoints/'+state['webhook_id'], key, {'url': url})
            secret = env['STRIPE_WEBHOOK_SECRET']
        else:
            endpoint = stripe_call('POST', '/webhook_endpoints', key, {
                'url': url, 'enabled_events[]': EVENTS, 'description': 'NumerOM test checkout'})
            secret = endpoint['secret']
    except (requests.RequestException, RuntimeError) as error:
        raise SystemExit(f'Stripe не принял запрос: {error}. Настройки сервера не изменены.')
    for name, value in (('STRIPE_SECRET_KEY', key), ('STRIPE_WEBHOOK_SECRET', secret), ('STRIPE_MODE', 'test')):
        set_key(ENV, name, value)
    # A sandbox stops working on its expiry date; checkout is switched off then instead of failing at Stripe.
    if expires:
        set_key(ENV, 'STRIPE_SANDBOX_EXPIRES_AT', expires)
    elif 'STRIPE_SANDBOX_EXPIRES_AT' in dotenv_values(ENV):
        unset_key(ENV, 'STRIPE_SANDBOX_EXPIRES_AT')
    ENV.chmod(0o600)
    save_state({'account_id': account_id, 'webhook_id': endpoint['id'], 'mode': 'test', 'url': url,
                'configured_at': time.time(), **({'expires_at': expires, 'claim_url': claim} if expires else {})})
    restart('api')
    print(f'Готово: тестовая оплата включена (аккаунт {account_id}), сервер перезапущен.')
    print('Тестовая карта Stripe: 4242 4242 4242 4242, любой будущий срок и CVC.')
    if expires:
        print(f'Песочница действует до {expires}. Чтобы она не истекла, откройте ссылку и закрепите её в своём аккаунте Stripe:')
        print(claim or 'ссылка сохранена в настройках Stripe CLI')


if __name__ == '__main__':
    try: connect(reuse='--reuse-sandbox' in sys.argv[1:])
    except (KeyboardInterrupt, EOFError): print('\nОтменено. Настройки не изменены.')
