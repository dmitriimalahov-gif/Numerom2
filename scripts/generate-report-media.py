"""Single-process resumable local interpretation / Remotion queues."""
import argparse
import asyncio
from contextlib import nullcontext
import fcntl
import hashlib
import json
import math
import os
import platform
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time
from report_generation_slot import report_generation_slot

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from dotenv import load_dotenv
load_dotenv(ROOT / 'backend/.env')
from services.report_files import digest, read_json, write_json
from services.report_insights import ReportInsights, ROOT as INSIGHTS, VERSION as IVERSION, compose, transport_config
from services.report_video import ReportVideo, ROOT as MOVIES, VERSION as VVERSION, MAX_BYTES
from services.narration import NarrationService
from domain.report_video import build_manifest, FPS
from domain.media_retry import delay as retry_delay, scheduled

def node_path():
    configured = os.environ.get('NUMEROM_NODE_PATH')
    candidates = [configured, str(Path.home() / '.nvm/versions/node/v22.22.2/bin/node'), shutil.which('node')]
    return next((p for p in candidates if p and Path(p).is_file()), None)

def renderer_path():
    runtime = os.environ.get('NUMEROM_VIDEO_RUNTIME', 'native')
    if runtime not in ('native', 'docker'):
        raise RuntimeError('NUMEROM_VIDEO_RUNTIME must be native or docker')
    return ROOT / 'video' / ('render-docker.mjs' if runtime == 'docker' else 'render.mjs')

def probe_runtime():
    executable = shutil.which('ffprobe')
    if executable:
        return executable, None
    # Remotion ships the exact matching native FFmpeg utilities with its renderer.
    architecture = {'arm64': 'arm64', 'aarch64': 'arm64', 'x86_64': 'x64', 'AMD64': 'x64'}.get(platform.machine())
    if sys.platform == 'darwin' and architecture:
        directory = ROOT / 'video/node_modules/@remotion' / ('compositor-darwin-' + architecture)
        candidate = directory / 'ffprobe'
        if candidate.is_file() and os.access(candidate, os.X_OK):
            environment = dict(os.environ)
            environment['DYLD_LIBRARY_PATH'] = str(directory)
            return str(candidate), environment
    raise RuntimeError('A verified ffprobe executable is required before rendering')


def render(target, report):
    renderer = renderer_path()
    ffprobe, probe_environment = probe_runtime()
    manifest = build_manifest(report, NarrationService(None))
    write_json(target / 'manifest.json', manifest)
    executable = node_path()
    if not executable:
        raise RuntimeError('Node.js runtime is not configured')
    output = target / 'report.pending.mp4'
    output.unlink(missing_ok=True)
    command = [executable, str(renderer), '--input', str(target / 'manifest.json'), '--output', str(output)]
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
    started = time.time()
    def terminate_child(*_):
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
        raise SystemExit(0)
    previous = signal.signal(signal.SIGTERM, terminate_child)
    timed_out = threading.Event()
    def expire():
        timed_out.set()
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
    deadline = threading.Timer(6 * 3600, expire)
    deadline.daemon = True
    deadline.start()
    try:
        write_json(target / 'progress.json', {'progress': 0, 'updated_at': time.time()})
        for line in process.stdout:
            if time.time() - started > 6 * 3600:
                raise RuntimeError('Video render exceeded its time budget')
            try:
                event = json.loads(line)
                if isinstance(event, dict) and isinstance(event.get('progress'), (int, float)):
                    write_json(target / 'progress.json', {'progress': event['progress'], 'updated_at': time.time()})
            except (ValueError, TypeError):
                pass  # Browser diagnostics may include local file paths; keep them private.
        if process.wait() != 0 or timed_out.is_set() or not output.is_file() or output.is_symlink() or not 0 < output.stat().st_size <= MAX_BYTES:
            raise RuntimeError('Remotion did not produce a complete bounded MP4')
        probe = subprocess.run([ffprobe, '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(output)],
                               capture_output=True, text=True, check=True, timeout=30, env=probe_environment)
        metadata = json.loads(probe.stdout)
        streams = metadata.get('streams', [])
        if not any(s.get('codec_type') == 'video' and s.get('codec_name') == 'h264' and s.get('width') == 1280 and s.get('height') == 720 for s in streams):
            raise RuntimeError('Invalid MP4 video stream')
        if not any(s.get('codec_type') == 'audio' and s.get('codec_name') == 'aac' for s in streams):
            raise RuntimeError('Narration missing from MP4')
        expected = sum(c['durationInFrames'] for c in manifest['chapters']) / FPS
        actual = float(metadata['format']['duration'])
        if not math.isfinite(actual) or actual <= 0 or abs(actual - expected) > 1:
            raise RuntimeError('MP4 duration does not match the narrated report')
    finally:
        deadline.cancel()
        signal.signal(signal.SIGTERM, previous)
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
    chapters, offset = [], 0
    for chapter in manifest['chapters']:
        seconds = chapter['durationInFrames'] / FPS
        chapters.append({'id': chapter['id'], 'title': chapter['title'], 'start_seconds': offset, 'duration_seconds': seconds})
        offset += seconds
    output.replace(target / 'report.mp4')
    movie = target / 'report.mp4'
    write_json(target / 'ready.json', {'key': target.name, 'seconds': offset, 'bytes': movie.stat().st_size,
        'sha256': hashlib.sha256(movie.read_bytes()).hexdigest(), 'chapters': chapters, 'created_at': time.time()})
    (target / 'progress.json').unlink(missing_ok=True)

async def process_insight(target, report):
    result = read_json(target / 'ready.json')
    try:
        if not result or result.get('key') != target.name or result.get('provider') != 'ollama':
            raise ValueError('No committed interpretation')
        enriched = compose(report, result['result'], result['model'], transport_provider=result.get('transport_provider', 'ollama'))
    except (KeyError, TypeError, ValueError):
        result = await ReportInsights().generate(report)
        enriched = compose(report, result['result'], result['model'], transport_provider=result.get('transport_provider', 'ollama'))
    # Validate and construct BEFORE marking the interpretation ready.
    write_json(target / 'ready.json', result)
    voice = NarrationService(None)
    for item in enriched['narration']:
        voice.enqueue(item, 'full-report', 'paid-report')
    ReportVideo(None).enqueue(enriched)
    write_json(target / 'downstream.json', {'key': target.name, 'video_version': VVERSION, 'queued_at': time.time()})

def completed(kind, target, job):
    """A marker's existence is not completion; corrupt artifacts are repairable."""
    if kind == 'video':
        return ReportVideo(None).state(job['report'])['status'] == 'ready'
    saved = read_json(target / 'ready.json')
    if not saved or saved.get('key') != target.name or saved.get('provider') != 'ollama':
        return False
    try:
        compose(job['report'], saved['result'], saved['model'], transport_provider=saved.get('transport_provider', 'ollama'))
        downstream = read_json(target / 'downstream.json')
        return bool(downstream and downstream.get('key') == target.name
                    and downstream.get('video_version') == VVERSION)
    except (KeyError, TypeError, ValueError):
        return False

def insight_progress(target):
    """Count persisted work, not time spent or a freshly written rejection."""
    best=(0,0)
    for path in target.glob('checkpoint*.json'):
        saved=read_json(path) or {};parts=saved.get('parts')
        if not isinstance(parts,list):continue
        suffix=path.name[len('checkpoint'):-len('.json')]
        partial=read_json(target/('partial-positions'+suffix+'.json')) or {}
        positions=partial.get('positions')
        count=len(positions) if partial.get('part')==len(parts)+1 and isinstance(positions,list) else 0
        best=max(best,(len(parts),count))
    return best

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=['insights', 'video'], required=True)
    parser.add_argument('--watch', action='store_true')
    parser.add_argument('--limit', type=int, default=0)
    args = parser.parse_args()
    base, version = (INSIGHTS, IVERSION) if args.kind == 'insights' else (MOVIES, VVERSION)
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = (base / 'worker.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    done = 0
    while True:
        for path in sorted(base.glob('*/job.json'), key=lambda p: p.stat().st_mtime):
            target = path.parent
            failed = read_json(target / 'failed.json') or {}
            if failed and (type(failed.get('attempts')) is not int or failed['attempts'] < 0
                    or not scheduled(failed, 'retry_at') or time.time() < failed['retry_at']):
                continue
            job = read_json(path)
            if not job or job.get('version') != version or job.get('key') != target.name or digest(version, job.get('report')) != target.name:
                continue
            if completed(args.kind, target, job):
                continue
            report = job['report']
            before = insight_progress(target) if args.kind == 'insights' else (0,0)
            if args.kind == 'video':
                # A report composed with an older interpretation is superseded: its order shows the current one.
                if report.get('interpretation', {}).get('version') != IVERSION:
                    continue
                state = ReportVideo(None).state(report)
                if state['audio_ready'] != state['audio_total']:
                    continue
            try:
                # The configured remote bridge does not use the local GPU.
                # Keep local Ollama, TTS and Remotion mutually exclusive, while
                # remote text retries cannot stall the local speech queue.
                slot = (nullcontext() if args.kind == 'insights' and transport_config()[1] == 'strata'
                        else report_generation_slot())
                with slot:
                    print('START', args.kind, target.name, flush=True)
                    if args.kind == 'insights':
                        asyncio.run(process_insight(target, report))
                    else:
                        render(target, report)
                    (target / 'failed.json').unlink(missing_ok=True)
                    print('READY', args.kind, target.name, flush=True)
            except Exception as error:
                advanced = args.kind == 'insights' and insight_progress(target) > before
                attempts = 1 if advanced else failed.get('attempts', 0) + 1
                write_json(target / 'failed.json', {'attempts': attempts, 'retry_at': time.time() + (30 if advanced else retry_delay(attempts)),
                    'made_progress': advanced,
                    'error': type(error).__name__ + ': ' + str(error)[:500], 'at': time.time()})
                print('DEFERRED', args.kind, type(error).__name__, flush=True)
            done += 1
            if args.limit and done >= args.limit:
                return
        if not args.watch:
            return
        time.sleep(15)

if __name__ == '__main__':
    main()
