#!/usr/bin/env python3
"""Build and publish only audited Expo browser artifacts, leaving the source checkout intact."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import fcntl
from urllib.parse import urlsplit
from runtime_config import sign_config, copy_public_config
from numerom_services import RUNTIME

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'dmitriimalahov-gif/numerom-app'

def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api-url', required=True, help='Public HTTPS gateway origin (no keys)')
    parser.add_argument('--publish', action='store_true', help='Push the audited build to the existing public Pages repository')
    args = parser.parse_args()
    url = urlsplit(args.api_url)
    if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment or url.path not in ('', '/'):
        parser.error('Use an HTTPS origin with no credentials, path, query or fragment')
    env = {**os.environ, 'APP_VARIANT':'production', 'EXPO_PUBLIC_API_URL':args.api_url.rstrip('/'),
           'EXPO_PUBLIC_WEB_BASE_PATH':'/numerom-app', 'EXPO_PUBLIC_SITE_URL':'',
           'CI':'1', 'EXPO_NO_TELEMETRY':'1'}
    sign_config(args.api_url.rstrip('/'))
    copy_public_config(ROOT)
    run(['node','-e','if(Number(process.versions.node.split(".")[0])<22)process.exit(1)'], env=env)
    mobile = ROOT / 'mobile'
    run([str(mobile/'node_modules/.bin/tsc'),'--noEmit'], cwd=mobile, env=env)
    run([str(mobile/'node_modules/.bin/expo'),'export','--platform','web','--output-dir','dist-pages','--clear'], cwd=mobile, env=env)
    output = mobile / 'dist-pages'
    run(['node',str(ROOT/'scripts/prepare-mobile-pages.mjs'),str(output)], cwd=ROOT, env=env)
    if not args.publish:
        print('Audited build ready:', output)
        return
    with tempfile.TemporaryDirectory(prefix='numerom-publication-') as temporary:
        checkout = Path(temporary)/'pages'
        run(['gh','repo','clone',REPOSITORY,str(checkout),'--','--depth','1'])
        origin = subprocess.check_output(['git','-C',str(checkout),'remote','get-url','origin'],text=True).strip()
        if origin not in (f'https://github.com/{REPOSITORY}.git', f'git@github.com:{REPOSITORY}.git'):
            raise RuntimeError('Unexpected publication remote')
        run(['git','-C',str(checkout),'rm','-r','--ignore-unmatch','.'],stdout=subprocess.DEVNULL)
        for item in output.iterdir():
            if item.is_dir(): shutil.copytree(item,checkout/item.name,dirs_exist_ok=True)
            else: shutil.copy2(item,checkout/item.name)
        run(['git','-C',str(checkout),'config','user.name','Dmitri Malahov'])
        run(['git','-C',str(checkout),'config','user.email','227223159+dmitriimalahov-gif@users.noreply.github.com'])
        run(['git','-C',str(checkout),'add','--all'])
        if subprocess.run(['git','-C',str(checkout),'diff','--cached','--quiet']).returncode == 0:
            print('Public artifacts are already up to date.'); return
        run(['git','-C',str(checkout),'commit','-m','Update NumerOM mobile browser application'],stdout=subprocess.DEVNULL)
        run(['git','-C',str(checkout),'push','origin','HEAD:main'])
    print('Published artifacts; verify Pages deployment before declaring the update live.')
    print('https://dmitriimalahov-gif.github.io/numerom-app/')

if __name__ == '__main__':
    lock_path = RUNTIME / 'publication.lock'
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        main()
