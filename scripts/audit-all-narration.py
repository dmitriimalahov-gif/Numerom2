"""Audit current private lessons/project clips plus the nine bundled number clips."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from domain.narration import clip


def main():
    subprocess.run([sys.executable, str(ROOT / 'scripts/audit-project-narration.py'), '--require-ready'], check=True)
    private = json.loads((ROOT / 'artifacts/voice-project/coverage.json').read_text())
    package = ROOT / 'packages/number-knowledge'
    numbers = json.loads((package / 'ru.json').read_text())['items']
    manifest = json.loads((package / 'audio-manifest.json').read_text())
    from domain.consultation import VOICE, VOICE_IDENTITY
    assert manifest['voice'] == VOICE and manifest['profile'] == VOICE_IDENTITY
    assert sorted(row['digit'] for row in numbers) == list(range(1, 10))
    assert sorted(row['digit'] for row in manifest['items']) == list(range(1, 10))
    records = []
    for item in numbers:
        record = next(row for row in manifest['items'] if row['digit'] == item['digit'])
        path = package / record['path']
        assert path.resolve().is_relative_to(package.resolve()) and not path.is_symlink()
        data = path.read_bytes()
        assert b'ftyp' in data[:32] and len(data) == record['bytes']
        assert hashlib.sha256(data).hexdigest() == record['sha256']
        assert hashlib.sha256('\n\n'.join(item['segments']).encode()).hexdigest() == record['text_sha256']
        assert hashlib.sha256(record['transcript'].encode()).hexdigest() == record['speech_sha256']
        records.append(record)
    items = json.loads((ROOT / 'packages/project-knowledge/ru.json').read_text())['items']
    groups = {'scheme-': 30, 'assessment-': 10, 'vedic-': 5, 'comprehensive-': 6}
    current = []
    for prefix, expected in groups.items():
        rows = [row for row in items if row['id'].startswith(prefix)]
        assert len(rows) == expected and len({row['id'] for row in rows}) == expected
        for row in rows:
            item = clip(row['id'], row['section'], row['title'], row['text'])
            meta = json.loads((ROOT / 'backend/private/narration/clips' / item['hash'] / 'ready.json').read_text())
            assert meta['hash'] == item['hash']
            current.append({'id': row['id'], 'hash': item['hash'], 'seconds': meta['seconds'],
                'maximum_word_difference': max(part['difference'] for part in meta['segments'])})
    report = {
        'total': private['total'] + len(records), 'status': {'ready': private['total'] + len(records)},
        'private': {'total': private['total'], 'seconds': private['seconds'], 'bytes': private['bytes']},
        'public_numbers': {'total': len(records), 'seconds': round(sum(row['seconds'] for row in records), 2),
            'bytes': sum(row['bytes'] for row in records), 'records': records},
        'new_recordings': {'total': len(current), 'seconds': round(sum(row['seconds'] for row in current), 2),
            'groups': groups, 'records': current},
        'validation': 'Current source hashes, file integrity, private word-check threshold; public number source/file hashes.',
        'pronunciation_review': 'Automatic word checks do not establish complete manual review of Russian stresses.',
        'publication': 'Local source and audio verification; no claim about deployed client version.',
    }
    output = ROOT / 'artifacts/voice-schemes/complete-coverage.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'total': report['total'], 'ready': report['status']['ready'],
        'new_recordings': len(current), 'public_numbers': len(records)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
