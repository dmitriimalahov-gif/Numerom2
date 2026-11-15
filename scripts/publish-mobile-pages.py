#!/usr/bin/env python3
"""Build the browser app locally. Production publication is only to 1.numer.om."""
import argparse
import os
from pathlib import Path
import subprocess
from runtime_config import sign_config, copy_public_config

ROOT = Path(__file__).resolve().parents[1]

def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api-url', default='https://1.numer.om', help='Official HTTPS API origin')
    parser.add_argument('--publish', action='store_true', help='Retired: GitHub Pages publication is disabled')
    args = parser.parse_args()
    if args.publish:
        parser.error('GitHub Pages is retired. Publish through the codex/numerom-production release workflow to 1.numer.om.')
    if args.api_url.rstrip('/') != 'https://1.numer.om':
        parser.error('NumerOM browser builds use only https://1.numer.om')
    env = {**os.environ, 'APP_VARIANT':'production', 'EXPO_PUBLIC_API_URL':'https://1.numer.om',
           'EXPO_PUBLIC_WEB_BASE_PATH':'', 'EXPO_PUBLIC_SITE_URL':'https://1.numer.om',
           'CI':'1', 'EXPO_NO_TELEMETRY':'1'}
    sign_config('https://1.numer.om')
    copy_public_config(ROOT)
    mobile = ROOT / 'mobile'
    run(['node','-e','if(Number(process.versions.node.split(".")[0])<22)process.exit(1)'], env=env)
    run(['npm','run','typecheck'], cwd=mobile, env=env)
    run(['npx','expo','export','--platform','web','--output-dir','dist-domain','--clear'], cwd=mobile, env=env)
    output = mobile / 'dist-domain'
    run(['node',str(ROOT/'scripts/prepare-mobile-pages.mjs'),str(output)], cwd=ROOT, env=env)
    print('Audited local build ready:', output)
    print('Production site: https://1.numer.om')

if __name__ == '__main__':
    main()
