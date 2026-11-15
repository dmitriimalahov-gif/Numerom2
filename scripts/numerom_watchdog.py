"""Recover NumerOM and publish only its signed endpoint, never credentials or source."""
import fcntl
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
import requests
from dotenv import dotenv_values
from runtime_config import ROOT, CONFIG, atomic_write, sign_config, valid_origin
from numerom_services import RUNTIME, restart
from stripe_test_environment import sync_test_webhook

PUBLIC_CONFIG = 'https://1.numer.om/runtime-config.json'
ENV = ROOT/'backend/.env'
STATE = RUNTIME/'watchdog-state.json'
URL_RE = re.compile(r'https://[a-z0-9-]+\.trycloudflare\.com')

def probe(origin, local=False):
    try:
        headers = {'CF-Connecting-IP':'127.0.0.1'} if local else {}
        response = requests.get(origin+'/api/health', headers=headers, timeout=6, allow_redirects=False)
        payload = response.json()
        if response.status_code == 200 and payload == {'status':'ok','service':'numerom'}:
            return 'ready'
        if response.status_code == 503 and payload == {'status':'unavailable','service':'numerom'}:
            return 'database_unavailable'
    except (requests.RequestException, ValueError):
        pass
    return 'unreachable'


def healthy(origin, local=False):
    return probe(origin, local) == 'ready'

def tunnel_url():
    pinned=dotenv_values(ENV).get('NUMEROM_PUBLIC_ORIGIN')
    if pinned:
        if not valid_origin(pinned):raise ValueError('Invalid permanent public origin')
        return pinned
    path = RUNTIME/'managed-tunnel.log'
    if not path.exists(): return None
    with path.open('rb') as stream:
        stream.seek(max(0,path.stat().st_size-512*1024))
        matches = URL_RE.findall(stream.read().decode(errors='replace'))
    return matches[-1] if matches else None

def update_environment(url):
    if dotenv_values(ENV).get('PUBLIC_API_URL') == url: return False
    lines = ENV.read_text().splitlines()
    lines = [line for line in lines if not re.match(r'^\s*PUBLIC_API_URL\s*=', line)]
    atomic_write(ENV, '\n'.join(lines)+f"\nPUBLIC_API_URL='{url}'\n")
    return True

def publish_config():
    # The signed config is part of the reviewed 1.numer.om release. Never publish
    # a runtime endpoint to GitHub Pages or another public host.
    if not config_is_live():
        raise RuntimeError('Signed endpoint config is not live on 1.numer.om')

def config_is_live():
    try:
        response=requests.get(PUBLIC_CONFIG+f'?t={int(time.time())}', timeout=8)
        return response.status_code==200 and response.json()==json.loads(CONFIG.read_text())
    except (requests.RequestException, ValueError): return False

def check(state):
    failures=state.setdefault('failures',{})
    for name,origin in [('api','http://127.0.0.1:8000'),('gateway','http://127.0.0.1:8004')]:
        readiness = probe(origin, True)
        if readiness == 'database_unavailable':
            # The application is alive; restarting it cannot repair MongoDB.
            failures[name] = 0
            state.update(public_ready=False, waiting_for='database')
            return
        if readiness != 'ready':
            failures[name]=failures.get(name,0)+1
            if failures[name]>=3: restart(name);failures[name]=0
            state['public_ready']=False
            return
        failures[name]=0
    if state.pop('waiting_for', None) == 'database':
        # Startup setup may have failed while MongoDB was absent. Replay it once
        # after recovery, then verify the restarted application on the next check.
        restart('api')
        state['public_ready'] = False
        return
    url=tunnel_url()
    if not url or not healthy(url):
        failures['tunnel']=failures.get('tunnel',0)+1
        if failures['tunnel']>=3:
            if dotenv_values(ENV).get('NUMEROM_PUBLIC_ORIGIN'):
                subprocess.run(['launchctl','kickstart','-k',f'gui/{os.getuid()}/md.numerom.domain-bridge'],check=False,capture_output=True)
            else:restart('tunnel')
            failures['tunnel']=0
        state['public_ready']=False
        return
    failures['tunnel']=0
    state.update(api=url,public_ready=True)
    if update_environment(url): restart('api')
    try:
        state['stripe_webhook'] = sync_test_webhook(url)
    except Exception as error:
        # Stripe downtime must not stop recovery/publication of the application.
        # Error bodies can contain credentials: retain only the exception class.
        state['stripe_webhook'] = 'retry:'+type(error).__name__
    sign_config(url)
    if state.get('published')!=url or not state.get('deployment_verified'):
        publish_config()
        state['published']=url
        state['deployment_verified']=config_is_live()
    state.pop('last_error',None)

def main():
    RUNTIME.mkdir(exist_ok=True,parents=True)
    # The full release and watchdog share this lock, so an old build cannot
    # overwrite a newer endpoint during publication.
    with (RUNTIME/'publication.lock').open('a') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: return
        try: state=json.loads(STATE.read_text())
        except (OSError,ValueError): state={}
        try: check(state)
        except Exception as error: state['last_error']=type(error).__name__
        state['checked_at']=datetime.now(timezone.utc).isoformat()
        atomic_write(STATE,json.dumps(state,indent=2))
        print(json.dumps({k:state.get(k) for k in ('checked_at','public_ready','api','published','deployment_verified','stripe_webhook','last_error')}),flush=True)

if __name__ == '__main__': main()
