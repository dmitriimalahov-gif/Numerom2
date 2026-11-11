"""Owner-bound MP4 access; rendering consumes only committed report snapshots."""
import hashlib
import hmac
import math
import os
import time
import stat
from functools import lru_cache
from urllib.parse import urlsplit

from fastapi import HTTPException
from jose import JWTError, jwt
from auth import signing_key
from services.narration import NarrationService
from services.report_files import PRIVATE, digest, enqueue, folder, read_json
from domain.media_retry import scheduled

# v3: motion graphics that follow the voice (numbers drop in as they are named), 24.10.2026.
VERSION = 'numerom-remotion-v3-motion'
ROOT = PRIVATE / 'report-video'
MAX_BYTES = 512 * 1024 * 1024

@lru_cache(maxsize=64)
def _file_hash(path, fingerprint):
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(descriptor, 'rb') as stream:
        info = os.fstat(stream.fileno())
        actual = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
        if not stat.S_ISREG(info.st_mode) or actual != fingerprint:
            return ''
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
        return digest.hexdigest()

def verified_movie(movie, meta):
    try:
        info = movie.stat()
        return _file_hash(str(movie), (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)) == meta.get('sha256')
    except OSError:
        return False

def video_key():
    return hmac.new(signing_key().encode(), b'numerom:report-video:v1', hashlib.sha256).hexdigest()

class ReportVideo:
    def __init__(self, db, root=ROOT, narration=None, reports=None, public_url=None):
        from services.full_reports import FullReports
        self.db, self.root = db, root
        self.voice = narration or NarrationService(db)
        self.reports = reports or FullReports(db)
        self.public_url = public_url

    def enqueue(self, report):
        key = digest(VERSION, report)
        enqueue(self.root, key, {'key': key, 'version': VERSION, 'report': report, 'created_at': time.time()})
        return key

    def state(self, report):
        key = digest(VERSION, report)
        target = folder(self.root, key)
        meta = read_json(target / 'ready.json')
        movie = target / 'report.mp4'
        audio_states = [self.voice.state(item)['status'] for item in report.get('narration', [])]
        counts = {'audio_total': len(audio_states), 'audio_ready': audio_states.count('ready')}
        if (meta and meta.get('key') == key and movie.is_file() and not movie.is_symlink()
                and 0 < movie.stat().st_size == meta.get('bytes', 0) <= MAX_BYTES
                and isinstance(meta.get('seconds'), (int, float)) and math.isfinite(meta['seconds']) and meta['seconds'] > 0
                and verified_movie(movie, meta)):
            return {'status': 'ready', 'message': 'Ваш видеоразбор готов.', **counts,
                    'seconds': meta['seconds'], 'bytes': meta['bytes'], 'chapters': meta.get('chapters', [])}
        failure = read_json(target / 'failed.json')
        if scheduled(failure, 'retry_at'):
            return {'status': 'queued', 'message': 'Подготовка продолжится автоматически. Готовые части сохранены.',
                    'automatic_retry': True, 'retry_at': failure['retry_at'], **counts}
        if (target / 'failed.json').exists() or (target / 'ready.json').exists():
            return {'status': 'failed', 'message': 'Не удалось завершить видео. Нажмите «Повторить», оплачивать снова не нужно.', **counts}
        if counts['audio_ready'] < counts['audio_total']:
            if 'review' in audio_states:
                return {'status': 'failed', 'stage': 'audio', 'message': 'Одна из аудиоглав не прошла подготовку. Нажмите «Повторить»: готовые главы сохранятся, новая оплата не нужна.', **counts}
            return {'status': 'waiting_audio', 'message': 'Готовим мужскую озвучку для всех глав. Затем автоматически соберём видео.', **counts}
        progress = read_json(target / 'progress.json')
        if progress and time.time() - progress.get('updated_at', 0) < 180:
            return {'status': 'rendering', 'message': 'Собираем схемы, графики и озвучку в видео.',
                    'progress': max(0, min(99, int(progress.get('progress', 0)))), **counts}
        return {'status': 'queued', 'message': 'Все записи готовы. Видео ожидает сборки.', **counts}

    async def owned(self, user_id, order_id):
        user, order = await self.reports.owned(user_id, order_id)
        if order['state'] != 'paid':
            raise HTTPException(403, 'Видео доступно после подтверждения оплаты полного разбора.')
        order = await self.reports.materialize(order)
        if not order.get('report'):
            raise HTTPException(503, 'Оплата подтверждена, сам отчёт ещё готовится.')
        return user, order

    async def status(self, user_id, order_id, retry=False):
        user, order = await self.owned(user_id, order_id)
        if order.get('analysis_status', 'ready') != 'ready':
            if retry:
                from services.report_insights import ReportInsights
                ReportInsights().retry(order['report'])
            review = order.get('analysis_status') == 'review' and not retry
            return {'status': 'failed' if review else 'waiting_analysis', 'stage': 'analysis', 'message': 'Смысловой разбор не прошёл проверку. Нажмите «Повторить», новая оплата не нужна.' if review else 'Готовим текст объяснений по сохранённым расчётам.',
                    'audio_ready': 0, 'audio_total': len(order['report'].get('narration', []))}
        report = order['report']
        key = self.enqueue(report)
        blocked_audio = 0
        if retry:
            from services.report_insights import VERSION as INSIGHT_VERSION
            interpretation = report.get('interpretation', {})
            if interpretation.get('provider') == 'ollama' and interpretation.get('version') == INSIGHT_VERSION:
                blocked_audio = self.voice.retry_report(report.get('narration', []), order_id)
            target = folder(self.root, key)
            if self.state(report)['status'] == 'failed':
                (target / 'failed.json').unlink(missing_ok=True)
                (target / 'ready.json').unlink(missing_ok=True)
                (target / 'progress.json').unlink(missing_ok=True)
        state = self.state(report)
        if blocked_audio and state['status'] == 'failed':
            state['message'] = 'Повтор озвучки временно ограничен: не чаще раза в минуту и до трёх раз в час. Попробуйте позже, оплачивать повторно не нужно.'
        if state['status'] == 'ready':
            public = (self.public_url or os.environ.get('PUBLIC_API_URL', '')).rstrip('/')
            parsed = urlsplit(public)
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
                raise HTTPException(503, 'Адрес видео ещё настраивается')
            lifetime = min(14400, max(3600, math.ceil(state['seconds']) + 1800))
            def link(download):
                token = jwt.encode({'sub': user_id, 'order': order_id, 'hash': key, 'download': download,
                    'auth_version': user.get('auth_version', 0), 'aud': 'numerom-report-video',
                    'exp': int(time.time()) + lifetime}, video_key(), algorithm='HS256')
                return public + '/api/student/report-video/' + token
            state.update(url=link(False), download_url=link(True), expires_in=lifetime)
        return state

    async def resolve(self, token):
        try:
            claims = jwt.decode(token, video_key(), algorithms=['HS256'], audience='numerom-report-video',
                                options={'require_exp': True, 'require_sub': True})
            if not all(isinstance(claims.get(k), str) for k in ('sub', 'order', 'hash')) or type(claims.get('download')) is not bool:
                raise ValueError()
        except (JWTError, ValueError):
            raise HTTPException(401, 'Ссылка на видео истекла. Откройте видео в своём отчёте ещё раз.')
        user, order = await self.owned(claims['sub'], claims['order'])
        if (user.get('auth_version', 0) != claims.get('auth_version') or order.get('analysis_status', 'ready') != 'ready'
                or digest(VERSION, order['report']) != claims['hash']):
            raise HTTPException(401, 'Ссылка отозвана. Откройте видео в своём отчёте ещё раз.')
        if self.state(order['report'])['status'] != 'ready':
            raise HTTPException(404, 'Видео пока недоступно')
        return folder(self.root, claims['hash']) / 'report.mp4', 'attachment' if claims['download'] else 'inline'
