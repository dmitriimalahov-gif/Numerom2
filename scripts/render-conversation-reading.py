"""Render an authored NumerOM consultation using the owner-selected clone.

Read-only with respect to accounts, report orders and the production voice queue.
Each segment is checked locally, cached with its inputs, then joined losslessly.
"""
from __future__ import annotations

import argparse
import difflib
import gc
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, '/Users/brandbox/Developer/helper-voice/local')
from report_generation_slot import report_generation_slot
import voice_tempo
SLOT = Path.home() / 'Library/Application Support/NumerOM/runtime/backend/private/runtime/report-generation.lock'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    out = args.directory.resolve()
    script = json.loads((out / 'script.json').read_text())
    profile_path = ROOT / 'backend/private/voice-profiles' / script['voice_profile'] / 'profile.json'
    profile = json.loads(profile_path.read_text())
    reference = profile_path.parent / profile['reference']
    assert hashlib.sha256(reference.read_bytes()).hexdigest() == profile['reference_sha256']
    assert profile['selected_by_user'] and profile['mode'] == 'speaker_embedding'
    tempo = script.get('tempo', profile.get('tempo', 1))
    if not isinstance(tempo, (int, float)) or not .8 <= tempo <= 1.3:
        raise ValueError('Preview tempo must be between 0.8 and 1.3')
    output_name = script.get('output_name', 'Дмитрий-первый-разбор')
    if not isinstance(output_name, str) or not output_name or Path(output_name).name != output_name:
        raise ValueError('Output name must be a plain file name')
    print('WAIT: NumerOM compute slot', flush=True)
    with report_generation_slot(SLOT):
        import generate_local as voice
        from audio_clean import loudness
        spec = importlib.util.spec_from_file_location('preview', ROOT / 'scripts/preview-natural-voice.py')
        preview = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(preview)
        manifest = {'title': script['title'], 'birth_date': script['birth_date'],
                    'voice_profile': profile['id'], 'model': profile['model'],
                    'mode': profile['mode'], 'local_only': True, 'tempo': tempo,
                    'post_processing': 'level matching' + ('; pitch-preserving tempo' if tempo != 1 else ''), 'segments': []}
        pieces, offset = [], 0
        for index, segment in enumerate(script['segments']):
            text = segment['text']
            identity = hashlib.sha256(json.dumps([profile, text], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            wav = out / f'{index+1:02d}-{segment["id"]}.wav'
            meta = wav.with_suffix('.json')
            cached = json.loads(meta.read_text()) if wav.exists() and meta.exists() else {}
            if cached.get('identity') == identity and cached.get('word_difference', 1) <= .04:
                audio, sr = voice.sf.read(wav, dtype='float32')
                result = cached
                print('REUSE', index+1, segment['id'], flush=True)
            else:
                best = None
                for attempt in range(3):
                    seed = profile['seed'] + index * 37 + attempt * 101
                    voice.mx.random.seed(seed)
                    print('SYNTH', index+1, segment['id'], 'attempt', attempt+1, flush=True)
                    model = voice.load_model(profile['model'])
                    sr = model.sample_rate
                    # No reference transcript: exactly the second, selected clone mode.
                    parts = list(model.generate(text=text, ref_audio=str(reference), lang_code='russian',
                        temperature=profile['temperature'], top_p=profile['top_p'], top_k=profile['top_k'], max_tokens=650))
                    audio = voice.np.concatenate([voice.np.asarray(part.audio) for part in parts]).astype('float32')
                    del model, parts
                    gc.collect(); voice.mx.clear_cache()
                    audio = loudness(audio, rms_db=-19, peak_db=-1)
                    heard = preview.recognize(audio, sr)
                    difference = 1-difflib.SequenceMatcher(None, voice.words(text), voice.words(heard)).ratio()
                    print('CHECK', index+1, f'{difference:.1%}', round(len(audio)/sr, 2), 'seconds', flush=True)
                    candidate = {'identity': identity, 'text': text, 'heard': heard,
                                 'word_difference': difference, 'seed': seed}
                    if best is None or difference < best[0]['word_difference']:
                        best = (candidate, audio)
                    if difference <= .025:
                        break
                result, audio = best
                if result['word_difference'] > .04:
                    voice.sf.write(out / f'review-{index+1}.wav', audio, sr)
                    raise ValueError(f'Segment {index+1}: word check failed: {result["heard"]}')
                assert voice.np.isfinite(audio).all() and 4 < len(audio)/sr < 48
                voice.sf.write(wav, audio, sr)
                meta.write_text(json.dumps(result, ensure_ascii=False, indent=2))
            # Cached speech remains at its original pace. Only assembled output
            # and its actual timings use the requested playback tempo.
            source_seconds = len(audio)/sr
            audio = voice_tempo.stretch(audio, sr, tempo, voice.sf)
            if pieces:
                gap = voice.np.zeros(round(sr*.25/tempo), dtype='float32')
                pieces.append(gap); offset += len(gap)/sr
            pieces.append(audio)
            manifest['segments'].append({'id': segment['id'], 'start': round(offset,3),
                'seconds': round(len(audio)/sr,3), 'source_seconds': round(source_seconds,3), **result})
            offset += len(audio)/sr
            (out / 'audio-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        complete = voice.np.concatenate(pieces)
        if tempo != 1:
            final_heard = preview.recognize(complete, sr)
            final_difference = 1-difflib.SequenceMatcher(None,
                voice.words(' '.join(s['text'] for s in script['segments'])), voice.words(final_heard)).ratio()
            manifest['assembled_check'] = {'heard': final_heard, 'word_difference': final_difference}
            if final_difference > .04:
                voice.sf.write(out / 'review-assembled.wav', complete, sr)
                raise ValueError(f'Accelerated audio failed word check: {final_difference:.1%}')
            print('FINAL CHECK', f'{final_difference:.1%}', flush=True)
        master = out / (output_name + '.wav')
        voice.sf.write(master, complete, sr)
        encoded = out / (output_name + '.m4a')
        encoded.unlink(missing_ok=True)
        subprocess.run(['/usr/bin/afconvert', '-f','m4af','-d','aac','-b','64000',str(master),str(encoded)],check=True)
        preview_file = out / 'Начало-разбора.m4a'
        preview_file.unlink(missing_ok=True)
        preview_wav = out / 'Начало-разбора.wav'
        voice.sf.write(preview_wav, pieces[0], sr)
        subprocess.run(['/usr/bin/afconvert', '-f','m4af','-d','aac','-b','64000',
                        str(preview_wav),str(preview_file)],check=True)
        manifest.update(seconds=round(len(complete)/sr,3), sample_rate=sr,
                        audio_file=encoded.name,
                        sha256=hashlib.sha256(encoded.read_bytes()).hexdigest(),
                        listening_review='pending_user')
        (out / 'audio-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        print('READY', encoded, manifest['seconds'], 'seconds', flush=True)


if __name__ == '__main__':
    main()
