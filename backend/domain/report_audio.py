"""Shared lightweight validation for paid-report audio and its local worker."""
from functools import lru_cache
import hashlib
import math
import os
import stat
from services.report_files import read_json


@lru_cache(maxsize=128)
def _audio_hash(path, fingerprint):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns) != fingerprint:
            return None
        value = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
        return value.hexdigest()


def ready_audio(target, key):
    meta, audio = read_json(target / 'ready.json'), target / 'audio.m4a'
    try:
        if not meta or meta.get('hash') != key or audio.is_symlink():
            return None
        info = audio.stat()
        if (not stat.S_ISREG(info.st_mode) or not 0 < info.st_size == meta.get('bytes') <= 512 * 1024 * 1024
                or not isinstance(meta.get('seconds'), (int, float))
                or not math.isfinite(meta['seconds']) or meta['seconds'] <= 0):
            return None
        fingerprint = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
        return meta if _audio_hash(str(audio), fingerprint) == meta.get('sha256') else None
    except (OSError, ValueError, TypeError):
        return None
