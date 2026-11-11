"""Finish current course jobs locally: introductions first, then all sections."""
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
state = ROOT / 'backend/private/narration/course-run.json'
command = [sys.executable, '-u', str(ROOT / 'scripts/generate-project-voices.py'),
           '--lesson-prefix', 'numerom-course-', '--low-memory']


def status(phase, **data):
    temporary = state.with_suffix('.tmp')
    temporary.write_text(json.dumps({'phase': phase, 'updated_at': datetime.now(timezone.utc).isoformat(), **data}, indent=2))
    temporary.replace(state)


if __name__ == '__main__':
    try:
        status('introductions')
        subprocess.run([*command, '--only-prefix', 'intro'], cwd=ROOT, check=True)
        status('all-sections')
        subprocess.run(command, cwd=ROOT, check=True)
        counts = {'ready': 0, 'review': 0, 'pending': 0}
        root = ROOT / 'backend/private/narration'
        for path in (root / 'jobs').glob('*.json'):
            job = json.loads(path.read_text())
            if not job.get('lesson_id', '').startswith('numerom-course-'):
                continue
            folder = root / 'clips' / path.stem
            key = 'ready' if (folder / 'ready.json').exists() else 'review' if (folder / 'failed.json').exists() else 'pending'
            counts[key] += 1
        status('needs-review' if counts['review'] or counts['pending'] else 'complete', **counts)
    except Exception as error:
        status('failed', error_type=type(error).__name__)
        raise
