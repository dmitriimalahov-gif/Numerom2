"""Publish a verified VoiceStudio clip into existing authenticated NumerOM playback.

The application hash is a logical source slot, not a claim about the TTS engine.
Generation identity and the actual voice/model/audio hashes are retained separately.
No generation, database writes, public static exports, or notifications occur here.
"""
import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from numerom_services import service_root
ROOT = service_root()
sys.path.insert(0, str(ROOT / 'backend'))
from domain.narration import clip, lesson_clips
from domain.report_audio import ready_audio
from services.report_files import digest
from services.report_insights import VERSION, compose


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def atomic_json(path, value):
    temporary = path.with_name(path.name + f'.{os.getpid()}.pending')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def source_item(target, root=ROOT, db=None):
    scope, identifier = target['scope'], target['source_id']
    if scope == 'project':
        assert identifier == 'project-knowledge/ru.json'
        entries = read(root / 'packages/project-knowledge/ru.json')['items']
        items = [clip(e['id'], e.get('section', 'guide'), e['title'], e['text']) for e in entries]
    elif scope == 'lesson':
        lesson = db.lessons_v2.find_one({'id': identifier, 'is_active': True})
        if not lesson:
            raise ValueError('Lesson is no longer active')
        items = lesson_clips(lesson)
    elif scope == 'selected-report':
        if not re.fullmatch('[a-f0-9]{64}', identifier):
            raise ValueError('Invalid report snapshot')
        folder = root / 'backend/private/report-insights' / identifier
        job, ready = read(folder / 'job.json'), read(folder / 'ready.json')
        assert job['version'] == VERSION
        assert job['key'] == ready['key'] == identifier == digest(VERSION, job['report'])
        items = compose(job['report'], ready['result'], ready['model'],
                        transport_provider=ready.get('transport_provider', 'ollama'))['narration']
    else:
        raise ValueError('Unsupported source scope')
    item = next((i for i in items if i and i['id'] == target['item_id']), None)
    if not item or hashlib.sha256(item['text'].encode()).hexdigest() != target['source_sha256']:
        raise ValueError('Current source differs from the voiced snapshot')
    return item


def validate_generation(batch, key):
    config = read(batch / 'config.json')
    if not config.get('publish_to_project'):
        raise ValueError('Project publication has not been enabled')
    folder = batch / 'cache' / key
    meta = read(folder / 'ready.json')
    if (meta.get('key') != key or meta.get('engine') != 'omnivoice'
            or meta.get('voice_reference_sha256') != config['reference_sha256']
            or meta.get('model_revision') != config['model_revision']
            or not meta.get('automatic_checks_passed')):
        raise ValueError('Unverified generation identity')
    assert sha(batch / 'reference.wav') == config['reference_sha256']
    assert meta['segments'] and all(
        part.get('critical_ok') is True
        and isinstance(part.get('difference'), (float, int))
        and math.isfinite(part['difference']) and 0 <= part['difference'] <= config['max_word_difference']
        and 0 <= part.get('clipped_fraction', 1) < .01 for part in meta['segments'])
    for name, field in [('audio.m4a', 'sha256'), ('master.wav', 'wav_sha256')]:
        path = folder / name
        if path.is_symlink() or not path.is_file() or sha(path) != meta[field]:
            raise ValueError('Audio integrity check failed')
    assert meta['bytes'] == (folder / 'audio.m4a').stat().st_size
    assert 0 < meta['seconds'] < 24 * 3600 and math.isfinite(meta['seconds'])
    return config, meta


def install(batch, key, targets, *, root=ROOT, db=None):
    config, meta = validate_generation(batch, key)
    items = [(target, source_item(target, root, db)) for target in targets]
    if not items:
        raise ValueError('No playback placements')
    voice_root = root / 'backend/private/narration'
    voice_root.mkdir(parents=True, exist_ok=True)
    published = []
    with (voice_root / '.voicestudio-publication.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for target, item in items:
            assert re.fullmatch('[a-f0-9]{64}', item['hash'])
            destination = voice_root / 'clips' / item['hash']
            if destination.resolve() != destination:
                raise ValueError('Unsafe playback destination')
            destination.mkdir(parents=True, exist_ok=True)
            output = destination / 'audio.m4a'
            if not output.is_file() or output.is_symlink() or sha(output) != meta['sha256']:
                temporary = destination / f'audio.{os.getpid()}.pending.m4a'
                shutil.copyfile(batch / 'cache' / key / 'audio.m4a', temporary)
                assert sha(temporary) == meta['sha256']
                temporary.replace(output)
            # The ready marker is committed last; existing API checks it and the checksum.
            record = {**meta, 'hash': item['hash'], 'generation_cache_key': key,
                      'source_sha256': target['source_sha256'], 'source_scope': target['scope'],
                      'profile': config['profile_id'], 'published_at': time.time(),
                      'pronunciation_review': 'pending_human_listening'}
            atomic_json(destination / 'ready.json', record)
            if not ready_audio(destination, item['hash']):
                raise ValueError('Application rejected the published clip')
            published.append({'hash': item['hash'], 'scope': target['scope'], 'item_id': item['id'],
                              'audio_sha256': meta['sha256'], 'seconds': meta['seconds']})
    receipt = {'key': key, 'published_at': time.time(), 'placements': published,
               'voice_reference_sha256': config['reference_sha256']}
    atomic_json(batch / 'cache' / key / 'publication.json', receipt)
    return receipt


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--key', required=True)
    args = parser.parse_args()
    base = ROOT.parent / 'noncommercial-voice'
    assert args.batch.resolve().is_relative_to(base) and args.batch.resolve() == args.batch
    assert re.fullmatch('[a-f0-9]{64}', args.key)
    targets = read(args.batch / 'publication-map.json')[args.key]
    from dotenv import load_dotenv
    from pymongo import MongoClient
    load_dotenv(ROOT / 'backend/.env')
    with MongoClient(os.environ['MONGO_URL'], serverSelectionTimeoutMS=5000) as client:
        result = install(args.batch, args.key, targets, db=client[os.environ['MONGODB_DATABASE']])
    print(json.dumps({'published': len(result['placements']), 'key': args.key[:12]}))


if __name__ == '__main__':
    main()
