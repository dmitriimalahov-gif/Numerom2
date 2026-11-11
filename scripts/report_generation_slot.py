"""One heavy NumerOM job at a time across local worker processes."""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import stat


LOCK_PATH = Path(__file__).resolve().parents[1] / 'backend/private/runtime/report-generation.lock'


@contextmanager
def report_generation_slot(path=None):
    """Hold the slot only while computing; kernel close/exit releases the lock.

    The descriptor is private and never inherited by encoder subprocesses. An
    optional path lets isolated tests use their own temporary runtime directory.
    Keep the lock file in place: unlinking it would permit two different inodes
    to be locked concurrently.
    """
    path = Path(path) if path is not None else LOCK_PATH
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    flags = os.O_RDWR | os.O_CREAT | getattr(os, 'O_CLOEXEC', 0) | getattr(os, 'O_NOFOLLOW', 0) | os.O_NONBLOCK
    descriptor = os.open(path, flags, 0o600)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid():
            raise ValueError('The generation lock must be a private regular file')
        os.set_inheritable(descriptor, False)
        os.fchmod(descriptor, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        try:
            yield descriptor
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)
