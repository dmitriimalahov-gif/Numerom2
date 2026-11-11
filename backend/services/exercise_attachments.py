"""Private bounded exercise files; metadata and submitted references share one CAS document."""
import base64
import binascii
import hashlib
import hmac
import io
import os
from pathlib import Path
import re
import time
from typing import Annotated
from urllib.parse import urlsplit
from uuid import UUID
import warnings

from fastapi import HTTPException
from jose import JWTError, jwt
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from auth import signing_key
from services.student_learning import _key, _student, require_student_lesson

MAX_BYTES = 5 * 1024 * 1024
MAX_ENCODED = 4 * ((MAX_BYTES + 2) // 3)
ROOT = Path(__file__).resolve().parents[1] / 'private/exercise-attachments'


class AttachmentUpload(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: UUID
    name: Annotated[StrictStr, Field(min_length=1, max_length=180)]
    content_base64: Annotated[StrictStr, Field(min_length=4, max_length=MAX_ENCODED)]

    @field_validator('request_id')
    @classmethod
    def v4(cls, value):
        if value.version != 4:
            raise ValueError('request_id must be UUIDv4')
        return value


def validate_file(request):
    try:
        data = base64.b64decode(request.content_base64, validate=True)
    except (ValueError, binascii.Error):
        raise HTTPException(422, 'Файл не удалось прочитать. Выберите его ещё раз.')
    if not 1 <= len(data) <= MAX_BYTES:
        raise HTTPException(413, 'Размер файла должен быть не больше 5 МБ.')
    if data.startswith(b'%PDF-') and b'%%EOF' in data[-1024:]:
        mime, extension = 'application/pdf', '.pdf'
    elif data.startswith((b'\x89PNG\r\n\x1a\n', b'\xff\xd8\xff')):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(data)) as image:
                    if image.format not in ('PNG', 'JPEG') or image.width * image.height > 20_000_000 or max(image.size) > 12000:
                        raise ValueError('dimensions')
                    extension = '.png' if image.format == 'PNG' else '.jpg'
                    mime = 'image/png' if image.format == 'PNG' else 'image/jpeg'
                    image.verify()
        except Exception:
            raise HTTPException(422, 'Изображение повреждено или слишком велико. Максимум 20 мегапикселей.')
    else:
        raise HTTPException(422, 'Поддерживаются только PDF, PNG и JPEG.')
    name = Path(request.name.replace('\\', '/')).name
    name = re.sub(r'[\x00-\x1f\x7f]', '', name).strip() or 'Вложение'
    name = Path(name).stem[:150] + extension
    return data, mime, name


def public(item):
    return {key: item[key] for key in ('id', 'name', 'mime', 'size')}


def attachment_key():
    return hmac.new(signing_key().encode(), b'numerom:exercise-attachment:v1', hashlib.sha256).hexdigest()


class ExerciseAttachments:
    def __init__(self, db, root=ROOT, public_url=None):
        self.db, self.root, self.public_url = db, Path(root).resolve(), public_url

    async def scope(self, uid, lesson, exercise):
        user, row = await require_student_lesson(self.db, uid, lesson)
        if exercise not in {item.get('id') for item in row.get('exercises', [])}:
            raise HTTPException(404, 'Упражнение не найдено')
        query = {'user_id': uid, 'lesson_id': lesson, 'exercise_id': exercise}
        return user, query

    async def list(self, uid, lesson, exercise):
        _, query = await self.scope(uid, lesson, exercise)
        row = await self.db.exercise_responses.find_one(query) or {}
        submitted = set(row.get('attachment_ids', []))
        return {'files': [{**public(item), 'submitted': item['id'] in submitted} for item in row.get('attachment_files', [])]}

    async def upload(self, uid, lesson, exercise, request):
        _, query = await self.scope(uid, lesson, exercise)
        data, mime, name = validate_file(request)
        identity = _key(uid, lesson, exercise, str(request.request_id))
        fingerprint = hashlib.sha256(data).hexdigest()
        collection = self.db.exercise_responses
        existing = await collection.find_one(query)
        identifier = existing['_id'] if existing else 'exercise-' + _key(uid, lesson, exercise)
        try:
            await collection.update_one({'_id': identifier}, {'$setOnInsert': {**query, 'id': str(identifier), 'attachment_draft_only': True}}, upsert=True)
        except DuplicateKeyError:
            pass
        row = await collection.find_one({'_id': identifier})
        if identity in row.get('attachment_removed_ids', []):
            raise HTTPException(410, 'Файл уже удалён. Выберите его заново.')
        if len(row.get('attachment_removed_ids', [])) >= 200:
            raise HTTPException(429, 'Лимит замен файлов в этом упражнении достигнут.')
        previous = next((item for item in row.get('attachment_files', []) if item['id'] == identity), None)
        if previous:
            if previous['sha256'] != fingerprint or previous['name'] != name:
                raise HTTPException(409, 'Этот запрос уже использован для другого файла.')
            return {'file': public(previous)}
        if len(row.get('attachment_files', [])) >= 3:
            raise HTTPException(409, 'К одному упражнению можно прикрепить не больше трёх файлов.')
        self.root.mkdir(parents=True, exist_ok=True)
        self.path(identity)
        # Same request can race; the name is content-bound and immutable.
        stored = self.root / (identity + '-' + fingerprint)
        try:
            with stored.open('xb') as file:
                file.write(data)
        except FileExistsError:
            pass
        item = {'id': identity, 'name': name, 'mime': mime, 'size': len(data), 'sha256': fingerprint, 'stored': stored.name}
        changed = await collection.find_one_and_update({'_id': identifier, 'attachment_files.id': {'$ne': identity}, 'attachment_removed_ids': {'$ne': identity},
            '$expr': {'$lt': [{'$size': {'$ifNull': ['$attachment_files', []]}}, 3]}},
            {'$push': {'attachment_files': item}}, return_document=ReturnDocument.AFTER)
        current = changed or await collection.find_one({'_id': identifier})
        saved = next((part for part in current.get('attachment_files', []) if part['id'] == identity), None)
        if not saved or saved['sha256'] != fingerprint or saved['name'] != name:
            # This unique content has no DB reference. Do not touch a winning upload.
            if not saved or saved.get('stored') != stored.name:
                stored.unlink(missing_ok=True)
            raise HTTPException(409, 'Лимит вложений достигнут или запрос уже занят другим файлом.')
        return {'file': public(saved)}

    def path(self, identity, fingerprint=None):
        if not re.fullmatch('[a-f0-9]{64}', identity) or (fingerprint is not None and not re.fullmatch('[a-f0-9]{64}', fingerprint)):
            raise HTTPException(404, 'Файл не найден')
        path = self.root / (identity + ('-' + fingerprint if fingerprint else ''))
        if path.is_symlink() or path.resolve().parent != self.root:
            raise HTTPException(404, 'Файл недоступен')
        return path

    async def remove(self, uid, lesson, exercise, identity):
        _, query = await self.scope(uid, lesson, exercise)
        self.path(identity)
        row = await self.db.exercise_responses.find_one_and_update({**query, 'attachment_ids': {'$ne': identity}, 'attachment_files.id': identity},
            {'$pull': {'attachment_files': {'id': identity}}, '$addToSet': {'attachment_removed_ids': identity}}, return_document=ReturnDocument.BEFORE)
        if row is None:
            existing = await self.db.exercise_responses.find_one(query) or {}
            if identity in existing.get('attachment_ids', []):
                raise HTTPException(409, 'Сначала отправьте ответ без этого вложения.')
            return {'removed': True}
        item = next((part for part in row.get('attachment_files', []) if part['id'] == identity), None)
        if item:
            self.path(identity, item['sha256']).unlink(missing_ok=True)
        return {'removed': True}

    async def authorized(self, uid, identity):
        self.path(identity)
        user = await _student(self.db, uid)
        row = await self.db.exercise_responses.find_one({'attachment_files.id': identity})
        if not row:
            raise HTTPException(404, 'Файл не найден')
        owner = row['user_id'] == uid
        reviewer = user.get('is_admin') or user.get('is_super_admin')
        if not owner and not (reviewer and identity in row.get('attachment_ids', []) and row.get('submitted_by_server')):
            raise HTTPException(404, 'Файл не найден')
        if owner:
            await require_student_lesson(self.db, uid, row['lesson_id'])
        elif not await self.db.lessons_v2.find_one({'id': row['lesson_id'], 'is_active': True}):
            raise HTTPException(404, 'Урок не найден')
        item = next(part for part in row['attachment_files'] if part['id'] == identity)
        return user, item

    async def access(self, uid, identity):
        user, item = await self.authorized(uid, identity)
        public_url = (self.public_url or os.environ.get('PUBLIC_API_URL', '')).rstrip('/')
        parsed = urlsplit(public_url)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
            raise HTTPException(503, 'Адрес файлов ещё настраивается')
        token = jwt.encode({'sub': uid, 'file': identity, 'auth_version': user.get('auth_version', 0),
            'aud': 'numerom-exercise-file', 'exp': int(time.time()) + 300}, attachment_key(), algorithm='HS256')
        return {'url': public_url + '/api/student/exercise-attachment-media/' + token, 'expires_in': 300}

    async def resolve(self, token):
        try:
            claims = jwt.decode(token, attachment_key(), algorithms=['HS256'], audience='numerom-exercise-file', options={'require_exp': True, 'require_sub': True})
            if not all(isinstance(claims.get(key), str) for key in ('sub', 'file')):
                raise ValueError()
        except (JWTError, ValueError):
            raise HTTPException(401, 'Ссылка истекла. Откройте вложение ещё раз.')
        user, item = await self.authorized(claims['sub'], claims['file'])
        if claims.get('auth_version') != user.get('auth_version', 0):
            raise HTTPException(401, 'Откройте вложение ещё раз.')
        return self.path(item['id'], item['sha256']), item
