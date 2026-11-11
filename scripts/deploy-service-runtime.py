"""Copy a local NumerOM runtime out of Desktop without deleting source or data.

Run --seed-data only with NumerOM's writers stopped. Later deployments update
code only; the runtime database files, uploads, secrets and queue stay authoritative.
"""
import argparse
import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

SOURCE = Path(__file__).resolve().parents[1]
DEFAULT_DESTINATION = Path.home() / 'Library/Application Support/NumerOM/runtime'
IGNORE = shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store', '.git', '.cache')


def copy_tree(source, destination, exclude=()):
    source, destination = Path(source), Path(destination)
    def ignore(directory, names):
        ignored = set(IGNORE(directory, names)) | (set(exclude) & set(names))
        for name in set(names) - ignored:
            original = Path(directory) / name
            target = destination / original.relative_to(source)
            if original.is_symlink() and target.is_symlink():
                if os.readlink(original) == os.readlink(target):
                    ignored.add(name)
                else:
                    target.unlink()
        return ignored
    shutil.copytree(source, destination, dirs_exist_ok=True, symlinks=True, ignore=ignore)


def deploy(source, destination, seed_data=False, environments=True):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError('Service runtime must be separate from source checkout')
    if seed_data and (source / 'backend/private/runtime/service-location.json').exists():
        raise ValueError('Active runtime is authoritative; refusing to seed from stale checkout data')
    marker = destination / '.numerom-runtime.json'
    if destination.exists() and not marker.exists() and any(destination.iterdir()):
        raise ValueError('Refusing to overwrite an unrelated directory')
    if marker.exists() and json.loads(marker.read_text()).get('source') != str(source):
        raise ValueError('Runtime belongs to a different checkout')
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination.chmod(0o700)
    if seed_data and (destination / '.data-initialized').exists():
        raise ValueError('Runtime data already initialized; never overwrite it from checkout')
    marker.write_text(json.dumps({'source': str(source), 'phase': 'preparing', 'started_at': time.time()}, indent=2))
    marker.chmod(0o600)

    copy_tree(source / 'backend', destination / 'backend', (
        '.venv', 'venv', '.service-venv', '.service-voice-venv', 'private', 'uploads',
        'tests', '.env', '.env.backup-cors', '.env.vapid', '.env.example'))
    copy_tree(source / 'scripts', destination / 'scripts')
    copy_tree(source / 'packages', destination / 'packages')
    copy_tree(source / 'video', destination / 'video', ('node_modules', 'test'))
    lockfile = source / 'video/package-lock.json'
    dependency_tag = hashlib.sha256(lockfile.read_bytes()).hexdigest() if lockfile.is_file() else 'fixture'
    receipt = destination / 'video/.dependencies-copied'
    if not receipt.is_file() or receipt.read_text() != dependency_tag:
        copy_tree(source / 'video/node_modules', destination / 'video/node_modules')
        receipt.write_text(dependency_tag)
    for relative in ('mobile/public/runtime-config.json', 'mobile/src/lib/endpointTrust.json'):
        target = destination / relative
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / relative, target)
    if seed_data:
        for relative in ('backend/private', 'backend/uploads'):
            copy_tree(source / relative, destination / relative)
        shutil.copy2(source / 'backend/.env', destination / 'backend/.env')
        (destination / 'backend/.env').chmod(0o600)
        (destination / 'backend/private').chmod(0o700)
        (destination / '.data-initialized').write_text(str(time.time()))
    if environments:
        original = source / 'backend/.service-venv/bin/python'
        interpreter = original.resolve()
        for name in ('.service-venv', '.service-voice-venv'):
            target = destination / 'backend' / name
            if not (target / 'bin/python').exists():
                subprocess.run([str(interpreter), '-m', 'venv', '--without-pip', str(target)], check=True)
            version = f'python{sys.version_info.major}.{sys.version_info.minor}'
            copy_tree(source / 'backend' / name / 'lib' / version / 'site-packages',
                      target / 'lib' / version / 'site-packages')
    if environments:
        node = Path.home() / '.nvm/versions/node/v22.22.2/bin/node'
        if not node.is_file():
            raise ValueError('Verified Node 22 runtime is missing')
        subprocess.run([str(node), str(destination / 'video/prepare-browser.mjs')],
                       cwd=destination, check=True, timeout=180)
    marker.write_text(json.dumps({'source': str(source), 'phase': 'ready', 'deployed_at': time.time()}, indent=2))
    marker.chmod(0o600)
    return destination


def activate(source, destination):
    if not (destination / '.data-initialized').exists():
        raise ValueError('Initialize and verify runtime data before activation')
    marker = json.loads((destination / '.numerom-runtime.json').read_text())
    if marker.get('source') != str(source.resolve()):
        raise ValueError('Runtime belongs to a different checkout')
    if marker.get('phase') != 'ready':
        raise ValueError('Complete runtime deployment before activation')
    target = source / 'backend/private/runtime/service-location.json'
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = target.with_suffix('.pending')
    temporary.write_text(json.dumps({'root': str(destination.resolve())}))
    temporary.chmod(0o600)
    temporary.replace(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument('--seed-data', action='store_true')
    parser.add_argument('--activate', action='store_true')
    args = parser.parse_args()
    destination = deploy(SOURCE, args.destination, args.seed_data)
    if args.activate:
        activate(SOURCE, destination)
    print(json.dumps({'runtime': str(destination), 'data_initialized': (destination / '.data-initialized').exists(),
                      'activated': args.activate}))


if __name__ == '__main__':
    main()
