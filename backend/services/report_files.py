"""Private, atomic report artifacts. Filenames are digests, never client paths."""
import hashlib
import fcntl
import json
import os
from pathlib import Path
import re
import tempfile
import stat

PRIVATE = Path(__file__).resolve().parents[1] / 'private'
MAX_JSON_BYTES = 4 * 1024 * 1024

def digest(version, value):
    return hashlib.sha256((version + '\0' + json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)).encode()).hexdigest()

def folder(root, key):
    root = Path(root).resolve()
    if not isinstance(key, str) or not re.fullmatch('[a-f0-9]{64}', key):
        raise ValueError('Invalid artifact key')
    result = root / key
    if result.resolve() != result:
        raise ValueError('Symlink artifact directory')
    return result

def read_json(path):
    path = Path(path)
    try:
        # Check the opened inode, not a separate stat that can race replacement.
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'rb') as stream:
            metadata = os.fstat(stream.fileno())
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_JSON_BYTES:
                return None
            raw = stream.read(MAX_JSON_BYTES + 1)
        if len(raw) > MAX_JSON_BYTES:
            return None
        def invalid_number(value):
            raise ValueError('Non-finite artifact value')
        result = json.loads(raw, parse_constant=invalid_number)
        return result if isinstance(result, dict) else None
    except (OSError, ValueError, UnicodeError):
        return None

def write_json(path, value):
    data = json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8')
    if len(data) > MAX_JSON_BYTES:
        raise ValueError('Report artifact is too large')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix='.writing-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

def enqueue(root, key, payload, limit=512):
    destination = folder(root, key)
    if not isinstance(payload, dict) or payload.get('key') != key or type(limit) is not int or limit < 1:
        raise ValueError('Invalid report queue entry')
    root = destination.parent
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(root / '.queue.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        existing = read_json(destination / 'job.json')
        if existing and existing.get('key') == key:
            return destination
        pending = sum(1 for p in root.glob('*/job.json') if p.parent != destination and read_json(p.parent / 'ready.json') is None)
        if pending >= limit:
            raise RuntimeError('Report generation queue is full')
        # The bound and write share one process-safe lock; corrupt jobs are repairable.
        write_json(destination / 'job.json', payload)
        return destination
