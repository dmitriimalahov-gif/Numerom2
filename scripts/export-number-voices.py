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
from domain.narration import clip
from domain.report_audio import ready_audio

# Identity of the personal non-commercial OmniVoice (VoiceStudio) batch.
# Matches noncommercial-voice/<batch>/config.json and MONITOR.md. The export
# accepts only clips published by that verified queue, so the manifest labels
# the actual local engine and profile rather than the retired Qwen3 voice.
OMNI_ENGINE = 'omnivoice'
OMNI_VOICE = 'dima golos'
OMNI_PROFILE = 'af750ff3'
OMNI_REFERENCE_SHA256 = '682c59cc1ea07f5323b15ce7bae34a35a8821598f8a1d127a2bc989eaac43849'
OMNI_MODEL_REVISION = 'c5fdb5ccb189668d56333f77ba2629f4cd7535f4'
OMNI_TEMPO = 1.0
OMNI_MAX_WORD_DIFFERENCE = 0.04


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
        segments = (meta.get('segments') or []) if meta else []
        if (not meta
                or meta.get('engine') != OMNI_ENGINE
                or meta.get('profile') != OMNI_PROFILE
                or meta.get('voice_reference_sha256') != OMNI_REFERENCE_SHA256
                or meta.get('model_revision') != OMNI_MODEL_REVISION
                or meta.get('automatic_checks_passed') is not True
                or meta.get('tempo') != OMNI_TEMPO
                or not segments
                or any(part.get('critical_ok') is not True
                       or not isinstance(part.get('difference'), (int, float))
                       or not (0 <= part['difference'] <= OMNI_MAX_WORD_DIFFERENCE)
                       for part in segments)):
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
    manifest = {'schema_version': 2, 'locale': 'ru-RU', 'voice': OMNI_VOICE, 'profile': OMNI_PROFILE,
        'provider': OMNI_ENGINE, 'tempo': OMNI_TEMPO,
        'voice_reference_sha256': OMNI_REFERENCE_SHA256, 'model_revision': OMNI_MODEL_REVISION, 'items': records}
    pending = package/'audio-manifest.pending.json'
    pending.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    pending.replace(package/'audio-manifest.json')
    print(json.dumps({'ready': len(records), 'voice': OMNI_VOICE, 'profile': OMNI_PROFILE,
                      'seconds': round(sum(r['seconds'] for r in records), 2)}))


if __name__ == '__main__': main()
