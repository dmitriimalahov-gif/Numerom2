"""Bundle the exact current, verified project recordings for offline mobile playback."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

from numerom_services import service_root
SOURCE = Path(__file__).resolve().parents[1]
RUNTIME = service_root()
sys.path.insert(0, str(RUNTIME/'backend'))
from domain.consultation import VOICE, VOICE_IDENTITY
from domain.narration import clip
from domain.report_audio import ready_audio
from domain.pronunciation import VERSION as PRONUNCIATION


def main():
    package = SOURCE/'packages/number-knowledge'
    knowledge = json.loads((package/'ru.json').read_text())['items']
    guides = {e['id']: e for e in json.loads((RUNTIME/'packages/project-knowledge/ru.json').read_text())['items']}
    records, files = [], []
    for item in knowledge:
        e = guides[f'number-{item["digit"]}']
        current = clip(e['id'], e['section'], e['title'], e['text'])
        folder = RUNTIME/'backend/private/narration/clips'/current['hash']
        meta = ready_audio(folder, current['hash'])
        if (not meta or meta.get('profile') != VOICE_IDENTITY or meta.get('tempo') != 1.2 or meta.get('pronunciation')!=PRONUNCIATION
                or not meta.get('segments') or any(c['difference'] > .07 for c in meta['segments'])):
            raise ValueError(f'Current selected-voice audio is not verified: {e["id"]}')
        relative = f'audio/ru/number-{item["digit"]}.m4a'
        files.append((folder/'audio.m4a', package/relative))
        records.append({'digit': item['digit'], 'path': relative,
            **{k: meta[k] for k in ('seconds','bytes','sha256')}, 'hash': current['hash'],
            # Original educational text and the oral adaptation are separately identified.
            'text_sha256': hashlib.sha256('\n\n'.join(item['segments']).encode()).hexdigest(),
            'transcript': current['text'], 'speech_sha256': hashlib.sha256(current['text'].encode()).hexdigest()})
    if sorted(e['digit'] for e in records) != list(range(1, 10)):
        raise ValueError('Expected exactly nine number recordings')
    for src, dest in files:
        dest.parent.mkdir(parents=True, exist_ok=True)
        temporary = dest.with_suffix('.pending.m4a'); shutil.copy2(src, temporary); temporary.replace(dest)
    manifest = {'schema_version': 2, 'locale': 'ru-RU', 'voice': VOICE, 'profile': VOICE_IDENTITY,
        'provider': 'qwen3-tts-local', 'tempo': 1.2, 'pronunciation':PRONUNCIATION, 'items': records}
    pending = package/'audio-manifest.pending.json'
    pending.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    pending.replace(package/'audio-manifest.json')
    print(json.dumps({'ready': len(records), 'voice': VOICE, 'seconds': round(sum(r['seconds'] for r in records), 2)}))


if __name__ == '__main__': main()
