"""Compare two fresh local clone modes, without tempo or timbre effects.

The optional render handoff pauses one verified NumerOM video process tree,
retaining its shared lock and in-memory render state. A separate watchdog always
resumes it if this preview exits or exceeds its ten-minute budget.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import gc
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path.home() / 'Library/Application Support/NumerOM/runtime'
SLOT = RUNTIME / 'backend/private/runtime/report-generation.lock'
OUT = ROOT / 'artifacts/voice-human-clone-2026-11-07'
LAB = ROOT / 'backend/private/voice-lab-human-clone-2026-11-07'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'


def processes():
    lines = subprocess.check_output(['ps', '-axo', 'pid=,ppid=,state=,lstart=,command='], text=True).splitlines()
    rows = {}
    for line in lines:
        fields = line.split(None, 8)
        if len(fields) == 9:
            rows[int(fields[0])] = {'parent': int(fields[1]), 'state': fields[2],
                                   'identity': ' '.join(fields[3:8]), 'command': fields[8]}
    return rows


def resume(saved):
    current = processes()
    for pid, identity in reversed(list(saved.items())):
        if pid in current and current[pid]['identity'] == identity:
            try:
                os.kill(pid, signal.SIGCONT)
            except ProcessLookupError:
                pass


@contextmanager
def compute_slot(worker):
    from report_generation_slot import report_generation_slot
    if worker is None:
        with report_generation_slot(SLOT):
            yield
        return
    # Only a known render worker is eligible; never suspend the API or a model.
    rows = processes()
    expected = str(RUNTIME / 'scripts/generate-report-media.py') + ' --kind video --watch'
    if worker not in rows or expected not in rows[worker]['command']:
        raise RuntimeError('The selected process is not the expected video worker')
    children = [pid for pid, row in rows.items() if row['parent'] == worker]
    if len(children) != 1 or str(RUNTIME / 'video/render.mjs') not in rows[children[0]]['command']:
        raise RuntimeError('Expected exactly one active native report renderer')
    selected = {worker}
    for _ in range(15):
        selected.update(pid for pid, row in rows.items() if row['parent'] in selected)
    saved = {pid: rows[pid]['identity'] for pid in [worker, *sorted(selected - {worker})]}
    coordinator = os.open(LAB / 'preview.lock', os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(coordinator, fcntl.LOCK_EX | fcntl.LOCK_NB)
    pipe_read, pipe_write = os.pipe()
    parent = os.getpid()
    watchdog = os.fork()
    if watchdog == 0:
        os.close(pipe_write)
        try:
            readable, _, _ = select.select([pipe_read], [], [], 600)
            if not readable:
                os.kill(parent, signal.SIGTERM)
                time.sleep(5)
                try:
                    os.kill(parent, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            # EOF also resumes the renderer after unexpected parent termination.
            resume(saved)
        finally:
            os._exit(0)
    os.close(pipe_read)
    previous = signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    check_fd = None
    try:
        for pid in saved:
            os.kill(pid, signal.SIGSTOP)
        time.sleep(.3)
        current = processes()
        if any(pid not in current or 'T' not in current[pid]['state'] for pid in saved):
            raise RuntimeError('Could not verify that every renderer process is paused')
        if any(row['parent'] in saved and pid not in saved for pid, row in current.items()):
            raise RuntimeError('Renderer spawned another child before the pause')
        # The paused worker retains the global lock, so other model workers wait.
        check_fd = os.open(SLOT, os.O_RDWR)
        try:
            fcntl.flock(check_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            raise RuntimeError('Video worker no longer owns the active compute slot')
        print('PAUSED renderer tree; shared lock retained; watchdog active', flush=True)
        yield
    finally:
        if check_fd is not None:
            os.close(check_fd)
        resume(saved)
        os.close(pipe_write)
        os.waitpid(watchdog, 0)
        os.close(coordinator)
        signal.signal(signal.SIGTERM, previous)
        print('RESUMED renderer tree', flush=True)


def generate():
    sys.path.insert(0, '/Users/brandbox/Developer/helper-voice/local')
    import importlib.util
    import generate_local as voice
    from audio_clean import loudness
    spec = importlib.util.spec_from_file_location('voice_preview', ROOT / 'scripts/preview-natural-voice.py')
    preview = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preview)
    source = ROOT / 'backend/private/voice-lab-new-recording-2026-11-07/original.wav'
    original, ref_sr = voice.sf.read(source, dtype='float32')
    references = {}
    for name, start, end in [('reference-intonation', 56.44, 69.54), ('speaker-identity', 40.26, 69.54)]:
        reference = original[round((start-.15)*ref_sr):round((end+.25)*ref_sr)]
        reference = loudness(reference, rms_db=-20, peak_db=-2)
        path = LAB / f'{name}.wav'
        voice.sf.write(path, reference, ref_sr)
        path.chmod(0o600)
        references[name] = path
    short_ref, ref_sr = voice.sf.read(references['reference-intonation'], dtype='float32')
    transcript = preview.recognize(short_ref, ref_sr)
    expected = ('Давайте внимательнее посмотрим на эти привычки. В методике Нумером мы рассматриваем '
                'число души, число ума, число судьбы, имя и фамилию.')
    if preview.difference(expected, transcript) > .12:
        raise ValueError('Reference transcript needs correction')
    print('REFERENCE VERIFIED:', transcript, flush=True)
    manifest = {'text': preview.TEXT, 'source_recording_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'model': preview.MODEL, 'local_only': True, 'production_modified': False, 'samples': []}
    (OUT / 'text.txt').write_text(preview.TEXT)
    for index, name in enumerate(references):
        for attempt in range(2):
            print('SYNTH:', name, 'attempt', attempt+1, flush=True)
            started = time.monotonic()
            voice.mx.random.seed(20261109 + index*100 + attempt)
            model = voice.load_model(preview.MODEL)
            sr = model.sample_rate
            args = dict(text=preview.TEXT, ref_audio=str(references[name]), lang_code='russian',
                        temperature=.85, top_p=.95, top_k=50, max_tokens=520)
            if name == 'reference-intonation':
                args['ref_text'] = transcript
            parts = list(model.generate(**args))
            audio = voice.np.concatenate([voice.np.asarray(part.audio) for part in parts]).astype('float32')
            del model, parts
            gc.collect()
            voice.mx.clear_cache()
            # Only level matching; no EQ, gate, acceleration, or internal editing.
            audio = loudness(audio, rms_db=-19, peak_db=-1)
            heard = preview.recognize(audio, sr)
            error = preview.difference(preview.TEXT, heard)
            print('CHECK:', name, 'difference', round(error, 4), 'seconds', round(len(audio)/sr, 2),
                  'elapsed', round(time.monotonic()-started, 1), flush=True)
            if error <= .04:
                break
        if error > .08:
            raise ValueError(f'{name}: failed word check: {heard}')
        if not voice.np.isfinite(audio).all() or not 8 <= len(audio)/sr <= 35:
            raise ValueError('Invalid sample shape or duration')
        wav = OUT / f'{name}.wav'
        voice.sf.write(wav, audio, sr)
        encoded = OUT / f'{name}.m4a'
        encoded.unlink(missing_ok=True)
        subprocess.run(['/usr/bin/afconvert', '-f', 'm4af', '-d', 'aac', '-b', '64000',
                        str(wav), str(encoded)], check=True)
        manifest['samples'].append({'name': name, 'seconds': round(len(audio)/sr, 3), 'heard': heard,
            'word_difference': error, 'reference_sha256': hashlib.sha256(references[name].read_bytes()).hexdigest(),
            'sample_rate': sr, 'tempo': 1, 'effects': 'level matching only',
            'seed': 20261109+index*100+attempt, 'temperature': .85, 'top_p': .95,
            'listening_review': 'pending_user'})
        (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        print('READY:', name, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pause-render-worker', type=int)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    LAB.mkdir(parents=True, exist_ok=True, mode=0o700)
    with compute_slot(args.pause_render_worker):
        generate()


if __name__ == '__main__':
    main()
