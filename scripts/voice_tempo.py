"""Pitch-preserving tempo for finished narration: Dmitrii asked for his recordings at 1.2× (24.10.2026).

Uses the FFmpeg that Remotion already ships in video/node_modules, so the voice venv needs nothing new.
"""
import os
import math
import platform
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPO = {'dmitrii': 1.2, 'dmitrii-conversation-v1': 1.2}


def ffmpeg():
    arch = {'arm64': 'arm64', 'aarch64': 'arm64', 'x86_64': 'x64', 'AMD64': 'x64'}.get(platform.machine(), 'arm64')
    directory = ROOT/'video/node_modules/@remotion'/f'compositor-darwin-{arch}'
    return directory/'ffmpeg', dict(os.environ, DYLD_LIBRARY_PATH=str(directory))


def stretch(audio, sr, tempo, sf):
    """Mono float audio played `tempo` times faster at the same pitch."""
    if tempo == 1:
        return audio
    binary, environment = ffmpeg()
    with tempfile.TemporaryDirectory() as folder:
        source, target = Path(folder)/'in.wav', Path(folder)/'out.wav'
        sf.write(source, audio, sr)
        subprocess.run([str(binary), '-loglevel', 'error', '-y', '-i', str(source), '-filter:a', f'atempo={tempo}',
                        '-ar', str(sr), '-ac', '1', str(target)], check=True, env=environment)
        result, _ = sf.read(target, dtype='float32')
    return result


def faster(check, tempo, *, seconds=None):
    """Scale ASR cues; use measured output length when assembling audio.

    FFmpeg atempo can add or trim samples relative to duration / tempo. Those
    small differences accumulate between fragments, so their offsets must use
    actual output samples. The saved raw checks remain at the recorded pace.
    """
    if tempo == 1 and (seconds is None or seconds == check.get('seconds')):
        return check
    duration = check.get('seconds', 0) / tempo if seconds is None else seconds
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('Invalid measured narration duration')
    cues = [{**cue, 'start': cue['start'] / tempo, 'end': cue['end'] / tempo} for cue in check.get('cues', [])]
    if seconds is not None:
        cues = [{**cue, 'end': min(cue['end'], duration)} for cue in cues if cue['start'] < duration]
    return {**check, 'seconds': duration, 'cues': cues, 'tempo': tempo}
