"""CPU-only delivery preview from the latest verified Dmitrii narration.

Keeps the source words and pitch, shortens only the centre of long quiet pauses,
and applies gentle EQ. Does not change the project's production voice.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy.signal import lfilter

ROOT = Path(__file__).resolve().parents[1]
HELPER = Path('/Users/brandbox/Developer/helper-voice')
sys.path.insert(0, str(HELPER / 'local'))
from audio_clean import loudness


def peak_eq(audio, sr, frequency, gain_db, q):
    gain = 10 ** (gain_db / 40)
    omega = 2 * np.pi * frequency / sr
    alpha = np.sin(omega) / (2 * q)
    cosine = np.cos(omega)
    b = [1 + alpha * gain, -2 * cosine, 1 - alpha * gain]
    a = [1 + alpha / gain, -2 * cosine, 1 - alpha / gain]
    return lfilter(b, a, audio)


def main():
    source = ROOT / 'artifacts/voice-new-recording-2026-11-07'
    out = ROOT / 'artifacts/voice-inspired-2026-11-07'
    out.mkdir(parents=True, exist_ok=True)
    audio, sr = sf.read(source / 'natural.wav', dtype='float32')
    source_seconds = len(audio) / sr
    hop = round(sr * .01)
    frames = audio[:len(audio) // hop * hop].reshape(-1, hop)
    rms = np.sqrt(np.mean(frames.astype(float) ** 2, axis=1))
    quiet = rms < 10 ** (-42 / 20)
    transitions = np.diff(np.r_[False, quiet, False].astype(int))
    cuts = []
    # Preserve at least 420 ms of each long pause and all its audible edges.
    for start, end in zip(np.where(transitions == 1)[0], np.where(transitions == -1)[0]):
        if (end - start) * .01 > .55 and start > 15 and end < len(quiet) - 20:
            middle = (start + end) * hop // 2
            remove = (end - start) * hop - round(.42 * sr)
            cuts.append((middle - remove // 2, middle + remove // 2))
    overlap = round(.008 * sr)
    for start, end in reversed(cuts):
        # Crossfade low-level samples instead of introducing a splice click.
        weight = np.linspace(0, 1, overlap)
        bridge = audio[start-overlap:start] * (1-weight) + audio[end:end+overlap] * weight
        audio = np.concatenate([audio[:start-overlap], bridge, audio[end+overlap:]])
    audio = peak_eq(audio, sr, 3800, -1.8, .85)
    audio = peak_eq(audio, sr, 220, .6, .8)
    intermediate = out / 'delivery-before-tempo.wav'
    sf.write(intermediate, audio, sr, subtype='FLOAT')
    ffdir = HELPER / 'projects/pharmaerp-video/node_modules/@remotion/compositor-darwin-arm64'
    if not (ffdir / 'ffmpeg').is_file():
        ffdir = Path.home() / 'Library/Application Support/NumerOM/runtime/video/node_modules/@remotion/compositor-darwin-arm64'
    wav = out / 'natural.wav'
    subprocess.run([str(ffdir / 'ffmpeg'), '-loglevel', 'error', '-y', '-i', str(intermediate),
                    '-filter:a', 'atempo=1.12', '-ar', str(sr), '-ac', '1', str(wav)],
                   env=dict(os.environ, DYLD_LIBRARY_PATH=str(ffdir)), check=True)
    rendered, output_sr = sf.read(wav, dtype='float32')
    rendered = loudness(rendered, rms_db=-19, peak_db=-1)
    assert np.isfinite(rendered).all() and output_sr == sr
    assert 10 < len(rendered) / sr < source_seconds
    assert np.max(np.abs(rendered)) < 1
    sf.write(wav, rendered, sr)
    encoded = out / 'natural.m4a'
    encoded.unlink(missing_ok=True)
    subprocess.run(['/usr/bin/afconvert', '-f', 'm4af', '-d', 'aac', '-b', '64000', str(wav), str(encoded)], check=True)
    intermediate.unlink()
    text = (source / 'text.txt').read_text()
    (out / 'text.txt').write_text(text)
    manifest = {
        'profile': 'numerom-dmitrii-v4-expressive-delivery-preview',
        'method': 'Post-processing of the verified v4 clone; no new synthesis',
        'source': str(source / 'natural.wav'),
        'source_sha256': hashlib.sha256((source / 'natural.wav').read_bytes()).hexdigest(),
        'text': text, 'local_only': True, 'production_modified': False,
        'source_seconds': source_seconds, 'seconds': round(len(rendered) / sr, 3),
        'tempo': 1.12, 'pitch_shift': False, 'noise_gate': False,
        'shortened_pauses': len(cuts), 'pause_floor_before_tempo_ms': 420,
        'eq': [{'hz': 3800, 'db': -1.8, 'q': .85}, {'hz': 220, 'db': .6, 'q': .8}],
        'sample_rate': sr, 'peak_dbfs': float(20 * np.log10(np.max(np.abs(rendered)))),
        'listening_review': 'pending_user',
        'new_reference_trial': 'Cancelled while queued behind active report render; not synthesized',
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
