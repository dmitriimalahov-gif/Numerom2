"""Report PDFs made on the server.

Phones and Safari often ignore printing from a hidden frame, so the app sends the same self-contained HTML it used
to print. Chrome renders it with scripts off and the network blocked; the file is cached by content digest and
handed out through a short-lived link bound to the account.
"""
import asyncio
import hashlib
import hmac
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import HTTPException
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, Field

from auth import signing_key
from services.report_files import PRIVATE, folder

ROOT = PRIVATE / 'report-pdf'
APP = Path(__file__).resolve().parents[2]
MAX_HTML = 1536 * 1024
LIFETIME = 3600
KEEP_SECONDS = 3 * 86400
RENDER_SECONDS = 90  # the gateway waits 95 s, Cloudflare 100 s
# Added in front of the document's own policy: browsers enforce every policy, so nothing can widen it.
GUARD = ('<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; '
         'img-src data:; font-src data:; base-uri \'none\'; form-action \'none\'">')


class ReportPdfRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    html: str = Field(min_length=1, max_length=MAX_HTML)
    # «10.01.1982 Иван Петров — полный разбор»: the name the saved file gets on the phone.
    filename: str | None = Field(default=None, min_length=1, max_length=120)


DEFAULT_NAME = 'NumerOM-report'
CYRILLIC = dict(zip('абвгдеёжзийклмнопрстуфхцчшщъыьэюя',
                    ['a', 'b', 'v', 'g', 'd', 'e', 'e', 'zh', 'z', 'i', 'y', 'k', 'l', 'm', 'n', 'o', 'p', 'r', 's', 't', 'u',
                     'f', 'kh', 'ts', 'ch', 'sh', 'shch', '', 'y', '', 'e', 'yu', 'ya']))


def file_name(value):
    """The file's own name: no folders, quotes or control characters, at most 100 characters."""
    name = re.sub(r'[\x00-\x1f\x7f/\\:*?"<>|]+', ' ', str(value or ''))
    name = re.sub(r'\s+', ' ', name).strip(' .')[:100].strip(' .')
    return name or DEFAULT_NAME


def link_name(name):
    """The same name in Latin letters for the end of the link (the gateway takes only plain ASCII paths)."""
    latin = ''.join((CYRILLIC[c.lower()].capitalize() if c.isupper() else CYRILLIC[c]) if c.lower() in CYRILLIC else c for c in name)
    slug = re.sub(r'-{2,}', '-', re.sub(r'[^A-Za-z0-9.]+', '-', latin)).strip('-.')[:100].strip('-.')
    return (slug or DEFAULT_NAME) + '.pdf'


def pdf_key():
    return hmac.new(signing_key().encode(), b'numerom:report-pdf:v1', hashlib.sha256).hexdigest()


def node_path():
    configured = os.environ.get('NUMEROM_NODE_PATH')
    candidates = [configured, str(Path.home() / '.nvm/versions/node/v22.22.2/bin/node'), shutil.which('node')]
    return next((p for p in candidates if p and Path(p).is_file()), None)


def guarded(html):
    head = re.search(r'<head[^>]*>', html, re.IGNORECASE)
    return html[:head.end()] + GUARD + html[head.end():] if head else GUARD + html


def render(html, target):
    """Blocking: write target/report.pdf with video/render-report-pdf.mjs."""
    node = node_path()
    if not node:
        raise RuntimeError('Node.js runtime is not configured')
    target.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(prefix='numerom-pdf-') as temporary:
        page = Path(temporary) / 'report.html'
        page.write_text(guarded(html), encoding='utf-8')
        subprocess.run([node, str(APP / 'video/render-report-pdf.mjs'), '--html', str(page), '--output', str(target / 'report.pdf')],
                       cwd=APP, capture_output=True, timeout=RENDER_SECONDS, check=True, start_new_session=True)


class ReportPdf:
    def __init__(self, db, root=ROOT, public_url=None, renderer=render):
        self.db, self.root, self.public_url, self.renderer = db, Path(root), public_url, renderer
        self.lock = asyncio.Lock()

    def public(self):
        public = (self.public_url or os.environ.get('PUBLIC_API_URL', '')).rstrip('/')
        parsed = urlsplit(public)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
            raise HTTPException(503, 'Адрес PDF ещё настраивается')
        return public

    async def account(self, user_id):
        user = await self.db.users.find_one({'id': user_id}, {'auth_version': 1, 'is_disabled': 1})
        if not user or user.get('is_disabled'):
            raise HTTPException(401, 'Войдите в аккаунт ещё раз')
        return user

    def prune(self):
        cutoff = time.time() - KEEP_SECONDS
        for entry in self.root.glob('*/report.pdf'):
            try:
                if entry.stat().st_mtime < cutoff:
                    shutil.rmtree(folder(self.root, entry.parent.name), ignore_errors=True)
            except (OSError, ValueError):
                continue

    async def create(self, user_id, body):
        user = await self.account(user_id)
        public = self.public()
        key = hashlib.sha256(body.html.encode()).hexdigest()
        target = folder(self.root, key)
        if not (target / 'report.pdf').is_file():
            # One Chrome at a time: the same machine also renders report videos.
            async with self.lock:
                if not (target / 'report.pdf').is_file():
                    try:
                        await asyncio.to_thread(self.renderer, body.html, target)
                    except (subprocess.SubprocessError, OSError, RuntimeError):
                        raise HTTPException(503, 'Не удалось собрать PDF. Повторите через минуту.')
                    await asyncio.to_thread(self.prune)
        if not (target / 'report.pdf').is_file():
            raise HTTPException(503, 'Не удалось собрать PDF. Повторите через минуту.')
        name = file_name(body.filename)
        token = jwt.encode({'sub': user_id, 'pdf': key, 'name': name, 'auth_version': user.get('auth_version', 0), 'aud': 'numerom-report-pdf',
                            'exp': int(time.time()) + LIFETIME}, pdf_key(), algorithm='HS256')
        # The name also ends the link: some phone viewers save a PDF under the last part of its address.
        return {'url': public + '/api/student/report-pdf/' + token + '/' + link_name(name), 'filename': name + '.pdf', 'expires_in': LIFETIME}

    async def resolve(self, token):
        """The stored PDF and the file name it is handed out under."""
        try:
            claims = jwt.decode(token, pdf_key(), algorithms=['HS256'], audience='numerom-report-pdf',
                                options={'require_exp': True, 'require_sub': True})
            if not isinstance(claims.get('sub'), str) or not isinstance(claims.get('pdf'), str):
                raise ValueError()
            target = folder(self.root, claims['pdf'])
        except (JWTError, ValueError):
            raise HTTPException(401, 'Ссылка на PDF истекла. Нажмите «Сохранить PDF» ещё раз.')
        user = await self.db.users.find_one({'id': claims['sub']}, {'auth_version': 1, 'is_disabled': 1})
        if not user or user.get('is_disabled') or user.get('auth_version', 0) != claims.get('auth_version'):
            raise HTTPException(401, 'Ссылка отозвана. Нажмите «Сохранить PDF» ещё раз.')
        if not (target / 'report.pdf').is_file():
            raise HTTPException(404, 'PDF больше не хранится. Нажмите «Сохранить PDF» ещё раз.')
        return target / 'report.pdf', file_name(claims.get('name')) + '.pdf'
