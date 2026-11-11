"""Local A/B voice sample; never changes the production voice or existing clips.

Run with helper-voice/.venv-tts/bin/python. Uses the same shared GPU slot as
NumerOM reports, the owner's existing recording, Qwen3-TTS and local Whisper.
"""
from __future__ import annotations

import argparse
import difflib
import gc
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
ROOT = Path(__file__).resolve().parents[1]
HELPER = Path('/Users/brandbox/Developer/helper-voice')
LAB = ROOT / 'backend/private/voice-lab-2026-11-07'
OUT = ROOT / 'artifacts/voice-natural-2026-11-07'
SLOT = Path.home() / 'Library/Application Support/NumerOM/runtime/backend/private/runtime/report-generation.lock'
sys.path.insert(0, str(HELPER / 'local'))
from report_generation_slot import report_generation_slot
from audio_clean import highpass, gate, soft_edges, loudness
import generate_local as voice
from mlx_whisper import transcribe
from mlx_whisper.transcribe import ModelHolder

TEXT = ('Здравствуйте, я Дмитрий. Давайте спокойно посмотрим на ваш расчёт. '
        'Здесь важно заметить свои сильные стороны и понять, что хочется развивать. '
        'Не спешите. Выберите одну мысль, которая вам близка, и попробуйте применить её сегодня.')
MODEL = 'mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16'
WHISPER = 'mlx-community/whisper-large-v3-turbo'


def norm(value):
    return re.sub(r'[^а-я ]', '', value.lower().replace('ё', 'е')).split()


def difference(expected, heard):
    return 1 - difflib.SequenceMatcher(None, norm(expected), norm(heard)).ratio()


def recognize(audio, sr):
    result = transcribe(voice.to16k(audio, sr), path_or_hf_repo=WHISPER, language='ru')
    ModelHolder.model = None
    ModelHolder.model_path = None
    gc.collect()
    voice.mx.clear_cache()
    return result['text'].strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-dir', type=Path, default=LAB)
    parser.add_argument('--output-dir', type=Path, default=OUT)
    parser.add_argument('--natural-only', action='store_true')
    parser.add_argument('--natural-profile', default='numerom-dmitrii-v3-natural-preview')
    parser.add_argument('--temperature', type=float, default=.80)
    parser.add_argument('--top-p', type=float, default=.95)
    parser.add_argument('--tempo', type=float, default=1.0,
                        help='Pitch-preserving tempo after generation; 1.12 is 12%% faster.')
    args = parser.parse_args()
    if not .1 <= args.temperature <= 1.2:
        parser.error('--temperature must be between 0.1 and 1.2')
    if not .1 <= args.top_p <= 1:
        parser.error('--top-p must be between 0.1 and 1')
    if not .8 <= args.tempo <= 1.25:
        parser.error('--tempo must be between 0.8 and 1.25')
    lab, out = args.reference_dir.resolve(), args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / 'text.txt').write_text(TEXT)
    print('WAIT: shared NumerOM generation slot; existing reports keep running', flush=True)
    manifest = {'text': TEXT, 'model': MODEL, 'local_only': True, 'samples': []}
    with report_generation_slot(SLOT):
        print('START: voice comparison', flush=True)
        ref = lab / 'reference-natural.wav'
        ref_audio, ref_sr = voice.sf.read(ref, dtype='float32')
        expected = (lab / 'reference-natural.txt').read_text()
        heard_ref = recognize(ref_audio, ref_sr)
        ref_difference = difference(expected, heard_ref)
        print('REFERENCE:', heard_ref, 'difference', round(ref_difference, 3), flush=True)
        if ref_difference > .18:
            raise ValueError('Reference speech needs review before synthesis')
        # The reference transcript must describe the actual uninterrupted recording.
        (lab / 'reference-verified.txt').write_text(heard_ref)
        (lab / 'reference-verified.txt').chmod(0o600)
        variants = [('natural', True)] if args.natural_only else [('natural', True), ('current', False)]
        for name, natural in variants:
            wav = ref if natural else HELPER / 'voice/dmitrii_ref.wav'
            ref_text = heard_ref if natural else (HELPER / 'voice/dmitrii_ref.txt').read_text().strip()
            options = {'temperature': args.temperature if natural else .75,
                       'top_p': args.top_p if natural else .90}
            best = None
            for attempt in range(3):
                seed = 20261107 + attempt * 101
                voice.mx.random.seed(seed)
                print(f'SYNTH {name} attempt {attempt + 1}', flush=True)
                started = time.monotonic()
                model = voice.load_model(MODEL)
                sr = model.sample_rate
                generated = list(model.generate(text=TEXT, ref_audio=str(wav), ref_text=ref_text,
                                                lang_code='russian', max_tokens=520, **options))
                raw = voice.np.concatenate([voice.np.asarray(part.audio) for part in generated]).astype('float32')
                del model, generated
                gc.collect()
                voice.mx.clear_cache()
                if natural:
                    audio = soft_edges(highpass(raw, sr, hz=55), sr, head=.14, tail=.34,
                                       fade_in=.015, fade_out=.055, threshold=.002)
                    if args.tempo != 1:
                        audio = voice.stretch(audio, sr, args.tempo)
                else:
                    audio = soft_edges(gate(highpass(raw, sr), sr), sr)
                    audio = voice.stretch(audio, sr, 1.2)
                audio = loudness(audio, rms_db=-19, peak_db=-1)
                heard = recognize(audio, sr)
                error = difference(TEXT, heard)
                print(f'CHECK {name}: {error:.1%}; {len(audio) / sr:.1f}s; generated in {time.monotonic() - started:.1f}s', flush=True)
                if best is None or error < best['difference']:
                    best = {'audio': audio, 'difference': error, 'heard': heard, 'seed': seed}
                if error <= .04:
                    break
            audio = best.pop('audio')
            if best['difference'] > .08:
                voice.sf.write(out / f'{name}-review.wav', audio, sr)
                raise ValueError(f'{name}: transcription failed: {best}')
            target = out / f'{name}.wav'
            voice.sf.write(target, audio, sr)
            encoded = out / f'{name}.m4a'
            encoded.unlink(missing_ok=True)
            manifest['samples'].append({'name': name, **best, **options,
                'profile': args.natural_profile if natural else 'numerom-dmitrii-v2-clean',
                'seconds': round(len(audio) / sr, 3), 'sample_rate': sr,
                'tempo': args.tempo if natural else 1.2, 'noise_gate': not natural,
                'reference_sha256': hashlib.sha256(wav.read_bytes()).hexdigest(),
                'peak_dbfs': float(20 * voice.np.log10(max(abs(audio)))),
                'pronunciation_review': 'pending_human_listening'})
            (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
            # 64 kbit/s is supported by macOS AAC at the model's mono 24 kHz.
            # Equal encoding for both samples avoids a codec difference in the A/B.
            subprocess.run(['/usr/bin/afconvert', '-f', 'm4af', '-d', 'aac', '-b',
                            '64000', str(target), str(encoded)], check=True)
            print('READY', name, flush=True)
    print('DONE', out, flush=True)


if __name__ == '__main__':
    main()
