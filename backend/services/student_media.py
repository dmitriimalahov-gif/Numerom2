"""Short-lived, lesson-scoped media access without exposing an account bearer token."""
import hashlib
import hmac
import mimetypes
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit
from fastapi import HTTPException
from jose import JWTError, jwt
from auth import signing_key
from services.student_learning import require_student_lesson, _student

MAX_FILE_BYTES = 512 * 1024 * 1024

def media_key():
    # A media capability can never be accepted as an account login token.
    return hmac.new(signing_key().encode(), b'numerom:student-media:v1', hashlib.sha256).hexdigest()

class StudentMediaService:
    def __init__(self, db, root, public_url=None, private_root=None):
        self.db = db
        self.root = Path(root).resolve()
        self.public_url = public_url
        self.private_root = Path(private_root or Path(__file__).resolve().parents[1] / "private/lesson-materials").resolve()

    async def video(self, user_id, lesson_id):
        _, lesson = await require_student_lesson(self.db, user_id, lesson_id)
        video_id = lesson.get('bunny_video_id') or lesson.get('video_id')
        if lesson.get('video_platform') != 'bunny' or not isinstance(video_id, str) or not re.fullmatch(r'[a-fA-F0-9-]{36}', video_id):
            raise HTTPException(404, 'Видео пока не добавлено к уроку')
        library = os.environ.get('BUNNY_LIBRARY_ID', '')
        key = os.environ.get('BUNNY_EMBED_TOKEN_KEY', '')
        if not re.fullmatch(r'\d+', library) or not key:
            raise HTTPException(503, 'Просмотр видео временно недоступен. Обратитесь к преподавателю.')
        expires = int(time.time()) + 300
        signature = hashlib.sha256(f'{key}{video_id}{expires}'.encode()).hexdigest()
        return {'url': f'https://player.mediadelivery.net/embed/{library}/{video_id}?token={signature}&expires={expires}', 'expires_in':300}

    async def file(self, user_id, lesson_id, file_id):
        user = await _student(self.db, user_id)
        admin = bool(user.get('is_admin') or user.get('is_super_admin'))
        if admin:
            lesson = await self.db.lessons_v2.find_one({'id':lesson_id})
            if not lesson:raise HTTPException(404, 'Урок не найден')
        else:
            user, lesson = await require_student_lesson(self.db, user_id, lesson_id)
        item = await self.db.files.find_one({'id': file_id, 'lesson_id': lesson_id})
        if not item or (item.get('is_active') is False and not admin):
            raise HTTPException(404, 'Материал не найден')
        stored = item.get('stored_name', '')
        if not stored or Path(stored).name != stored or '\\' in stored or '\x00' in stored:
            raise HTTPException(404, 'Материал недоступен')
        if Path(lesson_id).name != lesson_id or '\\' in lesson_id:
            raise HTTPException(404, 'Материал недоступен')
        root = self.private_root if item.get("private_material") is True else self.root
        for candidate in (root / lesson_id / stored, root / stored):
            resolved = candidate.resolve()
            if not resolved.is_relative_to(root) or not resolved.is_file():
                continue
            if resolved.stat().st_size > MAX_FILE_BYTES:
                raise HTTPException(413, 'Материал слишком большой для просмотра')
            return user, item, resolved
        raise HTTPException(404, 'Файл материала пока недоступен')

    async def access(self, user_id, lesson_id, file_id):
        user, item, path = await self.file(user_id, lesson_id, file_id)
        public = (self.public_url or os.environ.get('PUBLIC_API_URL', '')).rstrip('/')
        parsed = urlsplit(public)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path:
            raise HTTPException(503, 'Публичный просмотр материалов ещё настраивается')
        token = jwt.encode({
            'sub': user_id, 'lesson': lesson_id, 'file': file_id,
            'auth_version': user.get('auth_version', 0), 'aud': 'numerom-student-media',
            'exp': datetime.now(timezone.utc) + timedelta(minutes=5),
        }, media_key(), algorithm='HS256')
        return {'url': public + '/api/student/media/' + token, 'expires_in': 300}

    async def resolve(self, token):
        try:
            claims = jwt.decode(token, media_key(), algorithms=['HS256'], audience='numerom-student-media', options={'require_exp': True, 'require_sub': True})
            if not all(isinstance(claims.get(k), str) and claims[k] for k in ('sub','lesson','file')):
                raise ValueError('Invalid media claims')
        except (JWTError, ValueError):
            raise HTTPException(401, 'Ссылка на материал истекла. Откройте его из урока ещё раз.')
        user, item, path = await self.file(claims['sub'], claims['lesson'], claims['file'])
        if claims.get('auth_version') != user.get('auth_version', 0):
            raise HTTPException(401, 'Ссылка на материал недействительна')
        name = Path(str(item.get('original_name') or item.get('original_filename') or path.name)).name.replace('\r','').replace('\n','')
        kind = mimetypes.guess_type(name)[0] or 'application/octet-stream'
        safe_inline = kind == 'application/pdf' or kind.startswith(('video/','audio/')) or kind in ('image/png','image/jpeg','image/webp','image/gif')
        return path, name, kind if safe_inline else 'application/octet-stream', 'inline' if safe_inline else 'attachment'
