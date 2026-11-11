"""Bounded passive-file streaming for the pinned Starlette without Range support."""
import hashlib
import os
import re
import stat
from email.utils import formatdate
from pathlib import Path
from urllib.parse import quote

import anyio
from fastapi import HTTPException, Request
from starlette.responses import Response, StreamingResponse

MAX_FILE_BYTES = 512 * 1024 * 1024
CHUNK_BYTES = 64 * 1024
MEDIA_CSP = "sandbox; default-src 'none'; media-src 'self' blob:; img-src 'self' data: blob:; style-src 'unsafe-inline'"


def _byte_range(value, size):
    """Accept exactly one byte range; cap parsing work before converting integers."""
    if len(value) > 128:
        raise ValueError('Range too long')
    match = re.fullmatch(r'bytes=([0-9]*)-([0-9]*)', value.strip())
    if not match or not any(match.groups()) or size == 0:
        raise ValueError('Invalid range')
    first, last = match.groups()
    if not first:
        suffix = int(last)
        if suffix <= 0:
            raise ValueError('Invalid suffix')
        return max(0, size - suffix), size - 1
    start = int(first)
    end = int(last) if last else size - 1
    if start >= size or end < start:
        raise ValueError('Unsatisfiable range')
    return start, min(end, size - 1)


class _OpenMediaResponse(StreamingResponse):
    def __init__(self, file, start, length, **kwargs):
        self.file = file

        async def chunks():
            await file.seek(start)
            remaining = length
            while remaining:
                chunk = await file.read(min(CHUNK_BYTES, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

        super().__init__(chunks(), **kwargs)

    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        finally:
            # Disconnect cancellation must not leave a file descriptor open.
            with anyio.CancelScope(shield=True):
                await self.file.aclose()


async def media_file_response(request: Request, path, name, kind, disposition):
    """Open before responding, then stream from this descriptor only, with no body buffer."""
    try:
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
        descriptor = await anyio.to_thread.run_sync(os.open, path, flags)
    except OSError:
        raise HTTPException(404, 'Файл материала пока недоступен')
    file = anyio.wrap_file(os.fdopen(descriptor, 'rb'))
    handed_off = False
    try:
        info = await anyio.to_thread.run_sync(os.fstat, descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise HTTPException(404, 'Файл материала пока недоступен')
        if info.st_size > MAX_FILE_BYTES:
            raise HTTPException(413, 'Материал слишком большой для просмотра')
        passive = kind == 'application/pdf' or kind.startswith(('video/', 'audio/')) or kind in (
            'image/png', 'image/jpeg', 'image/webp', 'image/gif')
        if not passive:
            kind, disposition = 'application/octet-stream', 'attachment'
        disposition = 'inline' if disposition == 'inline' else 'attachment'
        name = Path(str(name)).name.replace('\\', '_').replace('\r', '').replace('\n', '')
        fingerprint = f'{info.st_dev}-{info.st_ino}-{info.st_mtime_ns}-{info.st_size}'
        etag = '"' + hashlib.sha256(fingerprint.encode()).hexdigest() + '"'
        modified = formatdate(info.st_mtime, usegmt=True)
        headers = {
            'Content-Type': kind, 'Content-Length': str(info.st_size),
            'Content-Disposition': f"{disposition}; filename*=UTF-8''{quote(name, safe='')}",
            'Accept-Ranges': 'bytes', 'ETag': etag, 'Last-Modified': modified,
            'Cache-Control': 'private, no-store', 'Referrer-Policy': 'no-referrer',
            'X-Content-Type-Options': 'nosniff', 'Content-Security-Policy': MEDIA_CSP,
        }
        # Range is defined for GET, not HEAD. HEAD has the complete representation's metadata.
        if request.method == 'HEAD':
            return Response(headers=headers)
        start, end, status_code = 0, info.st_size - 1, 200
        ranges = request.headers.getlist('range')
        validator = request.headers.get('if-range')
        if ranges and (not validator or validator in (etag, modified)):
            try:
                if len(ranges) != 1:
                    raise ValueError('Multiple ranges')
                start, end = _byte_range(ranges[0], info.st_size)
            except ValueError:
                headers.update({'Content-Range': f'bytes */{info.st_size}', 'Content-Length': '0'})
                return Response(status_code=416, headers=headers)
            status_code = 206
            headers['Content-Range'] = f'bytes {start}-{end}/{info.st_size}'
            headers['Content-Length'] = str(end - start + 1)
        response = _OpenMediaResponse(file, start, end-start+1, status_code=status_code, headers=headers)
        handed_off = True
        return response
    finally:
        if not handed_off:
            with anyio.CancelScope(shield=True):
                await file.aclose()
