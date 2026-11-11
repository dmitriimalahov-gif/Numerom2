"""Small single-worker public pilot gateway. Start via uvicorn --factory.

Only explicitly reviewed methods/paths reach the loopback application. This does
not replace backend authorization or turn CORS into an authentication mechanism.
"""
import asyncio
import ipaddress
import json
import os
import re
import time
from datetime import datetime
from urllib.parse import parse_qs, urlsplit

import httpx
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.background import BackgroundTask
from starlette.routing import Route

MAX_BODY_BYTES = 16 * 1024
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_MEDIA_BYTES = 512 * 1024 * 1024
ID = r'[A-Za-z0-9_-]{1,128}'
FIXED_ROUTES = {
    ('POST','/api/auth/telegram/login'): 'login',
    ('POST','/api/auth/telegram/register'): 'register',
    ('POST','/api/auth/telegram/link'): 'login',
    ('POST','/api/telegram/menu'): 'write',
    ('GET','/api/telegram/payments/catalog'): 'read',
    ('POST','/api/telegram/payments/invoice'): 'checkout',
    ('GET','/api/telegram/full-reports/catalog'): 'read',
    ('POST','/api/telegram/full-reports/checkout'): 'checkout',
    ('GET','/api/geography/cities'): 'read',
    ('GET','/api/health'): 'health',
    ('GET','/api/admin/mobile/reports'): 'read',
    ('GET','/api/full-reports/catalog'): 'read',
    ('GET','/api/full-reports/history'): 'read',
    ('POST','/api/full-reports/checkout'): 'checkout',
    ('POST','/api/full-reports/preview'): 'read',
    ('POST','/api/report-pdf'): 'pdf',
    ('GET','/api/business'): 'read',
    ('GET','/api/business/template'): 'read',
    ('POST','/api/business/activate'): 'write',
    ('POST','/api/business/import/preview'): 'business_import',
    ('POST','/api/business/import'): 'business_import',
    ('POST','/api/business/groups'): 'write',
    ('POST','/api/numerology/vedic'): 'relationships',
    ('POST','/api/numerology/vedic/location'): 'location',
    ('GET','/api/numerology/vedic/catalog'): 'read',
    ('GET','/api/numerology/vedic/history'): 'read',
    ('POST','/api/numerology/assessment'): 'relationships',
    ('GET','/api/numerology/assessment/catalog'): 'read',
    ('GET','/api/numerology/assessment/history'): 'read',
    ('POST','/api/numerology/personal'): 'relationships',
    ('GET','/api/numerology/personal/catalog'): 'read',
    ('GET','/api/numerology/personal-numbers/history'): 'read',
    ('GET','/api/admin/manage/overview'): 'read',
    ('GET','/api/admin/manage/recovery-status'): 'read',
    ('GET','/api/admin/manage/users'): 'read',
    ('POST', '/api/auth/passkeys/options'): 'login',
    ('POST', '/api/auth/passkeys/verify'): 'login',
    ('GET', '/api/user/passkeys'): 'read',
    ('POST', '/api/user/passkeys/options'): 'write',
    ('POST', '/api/user/passkeys/verify'): 'write',
    ('POST', '/api/user/passkeys/remove'): 'write',
    ('POST', '/api/auth/login'): 'login',
    ('POST', '/api/auth/register'): 'register',
    ('POST', '/api/auth/forgot-password'): 'recovery',
    ('POST', '/api/auth/reset-password'): 'recovery',
    ('GET', '/api/user/profile-v2'): 'read',
    ('PATCH', '/api/user/profile-v2'): 'write',
    ('GET', '/api/numerology/costs'): 'read',
    ('GET', '/api/numerology/tools/catalog'): 'read',
    ('GET', '/api/numerology/tools/history'): 'read',
    ('POST', '/api/numerology/tools'): 'relationships',
    ('GET', '/api/numerology/relationships/catalog'): 'read',
    ('GET', '/api/numerology/relationships/history'): 'read',
    ('POST', '/api/numerology/relationships'): 'relationships',
    ('POST', '/api/numerology/personal-numbers'): 'personal',
    ('GET', '/api/numerology/personal-numbers/latest'): 'read',
    ('GET', '/api/learning-v2/lessons'): 'read',
    ('GET', '/api/user/credit-history'): 'read',
    ('GET', '/api/narration/project'): 'read',
    ('GET', '/api/public/narration/project'): 'public',
    ('POST', '/api/public/daily-email'): 'public',
    ('GET', '/api/payments/packages'): 'read',
    ('GET', '/api/payments/history'): 'read',
    ('GET', '/api/student/consultations'): 'read',
    ('POST', '/api/payments/checkout/session'): 'checkout',
    ('POST', '/api/webhook/stripe'): 'stripe_webhook',
    ('POST', '/api/student/exercise-response'): 'write',
    ('POST', '/api/student/quiz-attempt'): 'write',
}
RATE_LIMITS = {'health': (30, 60), 'login': (8, 60), 'register': (3, 3600), 'recovery': (3, 600),
               'location': (6, 60), 'business_import': (6, 60),
               'draft': (60, 60), 'attachment_upload': (12, 60),
               'relationships': (20, 60),
               'personal': (20, 60), 'write': (20, 60), 'read': (90, 60), 'media': (90, 60), 'public': (30, 60),
               'checkout': (8, 60), 'stripe_webhook': (120, 60), 'pdf': (6, 60)}
PROFILE_FIELDS = {'full_name', 'name', 'surname', 'phone_number', 'city',
                  'birth_city', 'birth_city_id',
                  'car_number', 'street', 'house_number', 'apartment_number',
                  'postal_code', 'birth_date'}


def _origin(value):
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.path not in ('', '/') or parsed.query or parsed.fragment or '*' in value):
        raise ValueError('Public gateway origins must be exact HTTPS origins without paths')
    if parsed.port not in (None, 443):
        raise ValueError('Public gateway origins must use HTTPS port 443')
    return f'https://{parsed.netloc}'.rstrip('/')


def _route(method, path):
    if method == 'GET' and re.fullmatch(r'/api/telegram/payments/orders/[a-f0-9]{64}', path):
        return 'read'
    if method=='POST' and re.fullmatch(r'/api/admin/mobile/reports/[a-f0-9]{64}/retry',path):return 'write'
    if method=='POST' and re.fullmatch(r'/api/full-reports/[a-f0-9]{64}/extend-profile',path):return 'write'
    if method=='GET' and re.fullmatch(r'/api/full-reports/[a-f0-9]{64}/revisions/[1-9][0-9]{0,5}',path):return 'read'
    if method in ('GET','POST') and re.fullmatch(r'/api/full-reports/[a-f0-9]{64}/video',path):return 'read' if method=='GET' else 'write'
    if method in ('GET','HEAD') and re.fullmatch(r'/api/student/report-video/[A-Za-z0-9_.-]{1,2048}',path):return 'media'
    if method in ('GET','HEAD') and re.fullmatch(r'/api/student/report-pdf/[A-Za-z0-9_.-]{1,2048}',path):return 'media'
    if method in ('GET','HEAD') and re.fullmatch(r'/api/student/report-pdf/[A-Za-z0-9_-][A-Za-z0-9_.-]{0,2047}/[A-Za-z0-9_-][A-Za-z0-9_.-]{0,118}\.pdf',path):return 'media'
    if method=='GET' and re.fullmatch(r'/api/full-reports/[a-f0-9]{64}(?:/narration)?',path):return 'read'
    if method=='POST' and re.fullmatch(r'/api/full-reports/[a-f0-9]{64}/cancel',path):return 'checkout'
    if method=='POST' and re.fullmatch(r'/api/full-reports/[a-f0-9]{64}/narration/' + ID + '/access',path):return 'write'
    if method=='PATCH' and re.fullmatch(r'/api/business/employees/' + ID,path):return 'write'
    if method=='POST' and re.fullmatch(r'/api/business/(?:employees|groups)/' + ID + '/remove',path):return 'write'
    if method=='GET' and re.fullmatch(r'/api/business/groups/' + ID + '/report',path):return 'read'
    if method in ('GET','POST') and re.fullmatch(r'/api/admin/mobile/consultations/' + ID + r'/materials',path):return 'read' if method=='GET' else 'attachment_upload'
    if method=='GET' and re.fullmatch(r'/api/admin/mobile/consultations/' + ID + '/materials/' + ID + '/access',path):return 'read'
    if method in ('GET','POST') and re.fullmatch(r'/api/admin/mobile/lessons/' + ID + r'/materials',path):return 'read' if method=='GET' else 'attachment_upload'
    if method=='POST' and re.fullmatch(r'/api/admin/mobile/lessons/' + ID + '/materials/' + ID,path):return 'write'
    if method=='GET' and re.fullmatch(r'/api/admin/mobile/lessons/' + ID + '/materials/' + ID + '/access',path):return 'read'
    if method=='GET' and re.fullmatch(r'/api/admin/manage/users/' + ID,path):return 'read'
    if method=='PATCH' and re.fullmatch(r'/api/admin/manage/users/' + ID + r'/(?:access|credits)',path):return 'write'
    if method=='POST' and path in ('/api/admin/mobile/lessons/import','/api/admin/mobile/lessons/import/preview'):return 'write'
    if method=='POST' and re.fullmatch(r'/api/admin/mobile/(?:lessons|consultations)/' + ID + '/archive',path):return 'write'
    if method=='GET' and re.fullmatch(r'/api/admin/mobile/(?:lessons|consultations|responses|analytics|challenge-notes|settings/(?:learning|costs|planetary-energy|monthly-route|telegram-stars))',path):return 'read'
    if method=='POST' and re.fullmatch(r'/api/admin/mobile/(?:(?:lessons|consultations|responses)/' + ID + r'|settings/(?:learning|costs|planetary-energy|monthly-route|telegram-stars)|users/' + ID + '/level)',path):return 'write'
    if method in ('GET','POST') and re.fullmatch(r'/api/student/exercise-attachments/' + ID + '/' + ID,path):return 'read' if method=='GET' else 'attachment_upload'
    if method=='POST' and re.fullmatch(r'/api/student/exercise-attachments/' + ID + '/' + ID + r'/[a-f0-9]{64}/remove',path):return 'write'
    if method=='GET' and re.fullmatch(r'/api/student/exercise-attachment-access/[a-f0-9]{64}',path):return 'read'
    if method in ('GET','HEAD') and re.fullmatch(r'/api/student/exercise-attachment-media/[A-Za-z0-9_.-]{1,2048}',path):return 'media'
    found = FIXED_ROUTES.get((method, path))
    if found:
        return found
    if method in ('GET','POST') and (re.fullmatch(r'/api/student/quiz-drafts/' + ID + '/' + ID,path) or
        re.fullmatch(r'/api/student/diary-drafts/' + ID + '/' + ID + r'/[a-fA-F0-9-]{36}/[1-9][0-9]?',path)):
        return 'read' if method=='GET' else 'draft'
    if method in ('GET','POST') and re.fullmatch(r'/api/student/exercise-drafts/' + ID + '/' + ID, path):
        return 'read' if method == 'GET' else 'draft'
    if method in ('GET','POST') and re.fullmatch(r'/api/student/diary/' + ID + '/' + ID, path):
        return 'read' if method == 'GET' else 'write'
    if method == 'POST' and re.fullmatch(r'/api/student/diary/' + ID + '/' + ID + '/restart', path):
        return 'write'
    if method == 'POST' and re.fullmatch(r'/api/student/consultations/' + ID + '/purchase',path):
        return 'write'
    if method == 'GET' and re.fullmatch(r'/api/student/consultations/' + ID + '/(?:video|pdf)/access',path):
        return 'read'
    if method in ('GET','HEAD') and re.fullmatch(r'/api/student/consultation-media/[A-Za-z0-9_.-]{1,2048}',path):
        return 'media'
    if method == 'GET' and re.fullmatch(r'/api/payments/checkout/status/cs_(?:test_|live_)?[A-Za-z0-9]{1,220}',path):
        return 'read'
    if method == 'POST' and re.fullmatch(r'/api/payments/checkout/cs_(?:test_|live_)?[A-Za-z0-9]{1,220}/cancel',path):
        return 'checkout'
    if method == 'GET' and re.fullmatch(r'/api/learning-v2/lessons/' + ID, path):
        return 'read'
    if method == 'GET' and re.fullmatch(r'/api/narration/lesson/' + ID, path):
        return 'read'
    if method == 'POST' and re.fullmatch(r'/api/narration/(?:project/' + ID + r'|lesson/' + ID + '/' + ID + r')/access', path):
        return 'write'
    if method in ('GET','HEAD') and re.fullmatch(r'/api/student/narration-media/[A-Za-z0-9_.-]{1,2048}',path):
        return 'media'
    if method == 'GET' and re.fullmatch(r'/api/student/(?:lesson-progress|exercise-responses|quiz-attempts|lesson-files)/' + ID, path):
        return 'read'
    if method == 'GET' and re.fullmatch(r'/api/student/lesson-files/' + ID + '/' + ID + '/access', path):
        return 'read'
    if method == 'GET' and re.fullmatch(r'/api/student/lesson-video/' + ID + '/access', path):
        return 'read'
    if method == 'POST' and re.fullmatch(r'/api/student/lesson-progress/' + ID + '/theory', path):
        return 'write'
    if method in ('GET', 'HEAD') and re.fullmatch(r'/api/student/media/[A-Za-z0-9_.-]{1,2048}', path):
        return 'media'
    return None


def _birth_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{2}\.\d{2}\.\d{4}', value):
        return False
    try:
        birth = datetime.strptime(value, '%d.%m.%Y')
        return 1900 <= birth.year and birth <= datetime.utcnow()
    except ValueError:
        return False


def _valid_body(path, body):
    if path == '/api/telegram/full-reports/checkout':
        from domain.full_report_purchase import FullReportCheckout
        try:
            FullReportCheckout.model_validate(body)
            return True
        except ValueError:
            return False
    if path in ('/api/auth/telegram/login','/api/auth/telegram/register','/api/auth/telegram/link','/api/telegram/menu','/api/telegram/payments/invoice'):
        from domain.telegram import TelegramLaunch, TelegramRegistration, TelegramLink, TelegramInvoice
        model = {'/api/auth/telegram/login': TelegramLaunch, '/api/auth/telegram/register': TelegramRegistration,
                 '/api/auth/telegram/link': TelegramLink, '/api/telegram/menu': TelegramLaunch,
                 '/api/telegram/payments/invoice': TelegramInvoice}[path]
        try:
            model.model_validate(body)
            return True
        except ValueError:
            return False
    if not isinstance(body, dict):
        return False
    if re.fullmatch(r'/api/admin/mobile/reports/[a-f0-9]{64}/retry',path):
        from services.admin_reports import ReportRetry
        try:ReportRetry.model_validate(body);return True
        except ValueError:return False
    if path.startswith('/api/full-reports/'):
        from domain.full_report_purchase import FullReportCheckout,FullReportPreview,FullReportProfileExtension
        from pydantic import ValidationError
        model={'/api/full-reports/checkout':FullReportCheckout,'/api/full-reports/preview':FullReportPreview}.get(path)
        if re.fullmatch(r'/api/full-reports/[a-f0-9]{64}/extend-profile',path):model=FullReportProfileExtension
        if model is None:return body=={}
        try:model.model_validate(body);return True
        except ValidationError:return False
    if path.startswith('/api/business/'):
        from services.business import ActivateRequest, PreviewRequest, ImportRequest, EmployeeWrite, GroupWrite, RevisionRequest
        from pydantic import ValidationError
        model={'/api/business/activate':ActivateRequest,'/api/business/import/preview':PreviewRequest,
               '/api/business/import':ImportRequest,'/api/business/groups':GroupWrite}.get(path)
        if re.fullmatch(r'/api/business/employees/' + ID,path):model=EmployeeWrite
        if re.fullmatch(r'/api/business/(?:employees|groups)/' + ID + '/remove',path):model=RevisionRequest
        if model is None:return False
        try:model.model_validate(body);return True
        except ValidationError:return False
    if path=='/api/public/daily-email':
        from services.daily_email import DailyEmailChoice
        from pydantic import ValidationError
        try:DailyEmailChoice.model_validate(body);return True
        except ValidationError:return False
    if path=='/api/report-pdf':
        from services.report_pdf import ReportPdfRequest
        from pydantic import ValidationError
        try:ReportPdfRequest.model_validate(body);return True
        except ValidationError:return False
    if path=='/api/numerology/vedic/location':
        from domain.vedic_location import LocationInput
        from pydantic import ValidationError
        try:LocationInput.model_validate(body);return True
        except ValidationError:return False
    if path=='/api/numerology/vedic':
        from domain.vedic_report import VedicRequest
        from pydantic import ValidationError
        try:VedicRequest.model_validate(body);return True
        except ValidationError:return False
    if path=='/api/numerology/assessment':
        from domain.assessment import AssessmentRequest
        from pydantic import ValidationError
        try:AssessmentRequest.model_validate(body);return True
        except ValidationError:return False
    if '/passkeys' in path:
        from routers.passkeys import Empty,RegisterBegin,Finish,RegisterFinish,Remove
        from pydantic import ValidationError
        model={'/api/auth/passkeys/options':Empty,'/api/auth/passkeys/verify':Finish,'/api/user/passkeys/options':RegisterBegin,
               '/api/user/passkeys/verify':RegisterFinish,'/api/user/passkeys/remove':Remove}.get(path)
        if model is None:return False
        try:model.model_validate(body);return True
        except ValidationError:return False
    if path=='/api/numerology/personal':
        from services.personal_calculations import PersonalRequest
        from pydantic import ValidationError
        try:PersonalRequest.model_validate(body);return True
        except ValidationError:return False
    if path.startswith('/api/student/exercise-attachments/'):
        if path.endswith('/remove'):return body=={}
        from services.exercise_attachments import AttachmentUpload
        from pydantic import ValidationError
        try:AttachmentUpload.model_validate(body);return True
        except ValidationError:return False
    if re.fullmatch(r'/api/admin/mobile/lessons/' + ID + r'/materials(?:/' + ID + ')?',path):
        from services.admin_materials import MaterialUpload,MaterialChange
        from pydantic import ValidationError
        try:(MaterialUpload if path.endswith('/materials') else MaterialChange).model_validate(body);return True
        except ValidationError:return False
    if re.fullmatch(r'/api/admin/mobile/consultations/' + ID + r'/materials',path):
        from services.admin_consultation_materials import ConsultationMaterialUpload
        from pydantic import ValidationError
        try:ConsultationMaterialUpload.model_validate(body);return True
        except ValidationError:return False
    if path.startswith('/api/admin/'):
        from services.mobile_admin import LessonChange,ConsultationChange,ReviewChange,SettingsChange,LevelChange,ImportPreview,LessonImport,ArchiveChange
        from routers.admin_management import AccessChange,CreditChange
        from pydantic import ValidationError
        model=(ImportPreview if path=='/api/admin/mobile/lessons/import/preview' else
               LessonImport if path=='/api/admin/mobile/lessons/import' else
               ArchiveChange if re.fullmatch(r'/api/admin/mobile/(?:lessons|consultations)/' + ID + '/archive',path) else
               AccessChange if path.endswith('/access') else CreditChange if path.endswith('/credits') else
               LessonChange if '/mobile/lessons/' in path else ConsultationChange if '/mobile/consultations/' in path else
               ReviewChange if '/mobile/responses/' in path else SettingsChange if '/mobile/settings/' in path else LevelChange if path.endswith('/level') else None)
        if model is None:return False
        try:
            validated = model.model_validate(body)
            if path == '/api/admin/mobile/settings/telegram-stars':
                from services.telegram_pricing import validate_prices
                validate_prices(validated.values)
            return True
        except (ValidationError, HTTPException):return False
    if path.startswith(('/api/student/quiz-drafts/','/api/student/diary-drafts/')):
        from services.learning_drafts import QuizDraftWrite,DiaryDraftWrite
        from pydantic import ValidationError
        try:
            (QuizDraftWrite if '/quiz-drafts/' in path else DiaryDraftWrite).model_validate(body)
            return True
        except ValidationError:return False
    if path.startswith('/api/student/exercise-drafts/'):
        from services.exercise_drafts import DraftWrite
        from pydantic import ValidationError
        try:
            DraftWrite.model_validate(body)
            return True
        except ValidationError:
            return False
    if path == '/api/numerology/tools':
        from domain.number_tools import ToolRequest
        from pydantic import ValidationError
        try:
            ToolRequest.model_validate(body)
            return True
        except ValidationError:
            return False
    if path == '/api/numerology/relationships':
        from domain.relationships import RelationshipRequest
        from pydantic import ValidationError
        try:
            RelationshipRequest.model_validate(body)
            return True
        except ValidationError:
            return False
    if path.startswith('/api/student/diary/'):
        from services.challenge_diary import DiaryWrite, DiaryRestart
        from pydantic import ValidationError
        try:
            (DiaryRestart if path.endswith('/restart') else DiaryWrite).model_validate(body)
            return True
        except ValidationError:
            return False
    if path.startswith('/api/student/consultations/') and path.endswith('/purchase'):
        from services.consultations import ConsultationPurchase
        from pydantic import ValidationError
        try:
            ConsultationPurchase.model_validate(body)
            return True
        except ValidationError:
            return False
    if path.startswith('/api/payments/checkout/') and path.endswith('/cancel'):
        return body == {}
    if path == '/api/payments/checkout/session':
        from domain.payments import CheckoutRequest
        from pydantic import ValidationError
        try:
            CheckoutRequest.model_validate(body)
            return True
        except ValidationError:
            return False
    if path.startswith('/api/narration/'):
        return body == {}
    if path.startswith('/api/student/'):
        from pydantic import ValidationError
        from services.student_learning import QuizSubmission, ExerciseSubmission, TheoryRead
        model = QuizSubmission if path.endswith('/quiz-attempt') else ExerciseSubmission if path.endswith('/exercise-response') else TheoryRead
        try:
            model.model_validate(body)
            return True
        except ValidationError:
            return False
    if path.endswith('/profile-v2'):
        return bool(body) and set(body) <= PROFILE_FIELDS and all(
            value is None or (isinstance(value, str) and len(value) <= 300
                              and (key != 'birth_date' or _birth_date(value)))
            for key, value in body.items())
    required = {
        '/api/auth/login': {'email', 'password'},
        '/api/auth/register': {'email', 'password', 'full_name', 'birth_date'},
        '/api/auth/forgot-password': {'email'},
        '/api/auth/reset-password': {'token', 'password'},
    }.get(path, set())
    allowed = required | ({'name', 'surname', 'city', 'phone_number'} if path.endswith('/register') else set())
    if not required <= set(body) or not set(body) <= allowed:
        return False
    if any(not isinstance(value, str) or len(value) > 300 for value in body.values()):
        return False
    if 'email' in body and (len(body['email']) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', body['email'])):
        return False
    if 'password' in body:
        minimum = 12 if path.endswith('/reset-password') else 8 if path.endswith('/register') else 1
        if len(body['password']) < minimum or len(body['password'].encode()) > 72:
            return False
    if 'birth_date' in body and not _birth_date(body['birth_date']):
        return False
    if 'full_name' in body and not body['full_name'].strip():
        return False
    if 'token' in body and not re.fullmatch(r'[A-Za-z0-9_-]{32,128}', body['token']):
        return False
    return True


class _Limiter:
    def __init__(self, clock):
        self.clock, self.windows = clock, {}

    def allow(self, key, maximum, seconds):
        now = self.clock()
        if len(self.windows) >= 4096:
            self.windows = {key: value for key, value in self.windows.items() if value[0] > now}
            if len(self.windows) >= 4096 and key not in self.windows:
                return False
        until, count = self.windows.get(key, (now + seconds, 0))
        if until <= now:
            until, count = now + seconds, 0
        if count >= maximum:
            return False
        self.windows[key] = (until, count + 1)
        return True


def create_public_gateway(allowed_origins, *, upstream_url='http://127.0.0.1:8000',
                          trust_cloudflare=False, transport=None, clock=time.monotonic,
                          max_response_bytes=MAX_RESPONSE_BYTES):
    origins = {_origin(value) for value in allowed_origins}
    if not origins:
        raise ValueError('At least one exact public HTTPS origin is required')
    upstream = urlsplit(upstream_url)
    if (upstream.scheme != 'http' or upstream.hostname != '127.0.0.1' or not upstream.port
            or upstream.username or upstream.password or upstream.path not in ('', '/')
            or upstream.query or upstream.fragment):
        raise ValueError('Upstream must be a fixed HTTP loopback URL')
    upstream_url = upstream_url.rstrip('/')
    limiter = _Limiter(clock)
    personal_lock = asyncio.Lock()
    in_flight = asyncio.Semaphore(8)

    async def gateway(request: Request):
        origin = request.headers.get('origin')
        response_headers = {'Cache-Control': 'no-store', 'Vary': 'Origin',
                            'Referrer-Policy': 'no-referrer', 'X-Content-Type-Options': 'nosniff'}
        def error(code, message):
            return JSONResponse({'detail': message}, status_code=code, headers=response_headers)
        if len(request.headers.getlist('origin')) > 1 or (origin and origin not in origins):
            return error(403, 'Источник запроса не разрешён')
        if origin:
            response_headers['Access-Control-Allow-Origin'] = origin
        method = request.headers.get('access-control-request-method', '') if request.method == 'OPTIONS' else request.method
        raw_path = request.scope.get('raw_path', b'').split(b'?', 1)[0]
        bucket = _route(method, request.url.path)
        if not bucket or b'%' in raw_path or b'\\' in raw_path:
            return error(404, 'Маршрут недоступен в публичном пилоте')
        if request.method == 'OPTIONS':
            requested_headers = {part.strip().lower() for part in request.headers.get('access-control-request-headers', '').split(',') if part.strip()}
            if not origin or not requested_headers <= {'authorization', 'content-type', 'range', 'if-range'}:
                return error(403, 'Параметры запроса не разрешены')
            return Response(status_code=204, headers={**response_headers,
                'Access-Control-Allow-Methods': method,
                'Access-Control-Allow-Headers': 'Authorization, Content-Type, Range, If-Range',
                'Access-Control-Max-Age': '300'})
        peer = request.client.host if request.client else 'unknown'
        ip = peer
        if trust_cloudflare and peer in ('127.0.0.1', '::1'):
            try:
                ip = str(ipaddress.ip_address(request.headers.get('cf-connecting-ip', '')))
            except ValueError:
                return error(400, 'Не удалось определить источник запроса')
        if (not limiter.allow(('global', 'requests'), 600, 60)
                or not limiter.allow((ip, bucket), *RATE_LIMITS[bucket])
                or (bucket == 'register' and not limiter.allow(('global', 'register'), 10, 3600))):
            response_headers['Retry-After'] = '60'
            return error(429, 'Слишком много запросов. Повторите позже.')
        protected = not request.url.path.startswith('/api/auth/') and bucket not in ('media','stripe_webhook','health','public')
        authorization = request.headers.get('authorization', '')
        if protected and (len(request.headers.getlist('authorization')) != 1 or
                          not re.fullmatch(r'Bearer [A-Za-z0-9._-]{1,4096}', authorization)):
            return error(401, 'Требуется вход в аккаунт')
        if request.headers.get('content-encoding', 'identity') != 'identity':
            return error(415, 'Сжатые тела запросов не поддерживаются')
        async def read_body():
            chunks, size = [], 0
            maximum = (8 * 1024 * 1024 if bucket in ('attachment_upload','business_import') else 4 * 1024 * 1024 if bucket == 'pdf' else 2 * 1024 * 1024 if '/admin/mobile/lessons/' in request.url.path else 128 * 1024 if request.url.path.startswith('/api/business/') or '/passkeys/' in request.url.path else 256 * 1024 if bucket == 'stripe_webhook' else 512 * 1024 if request.url.path == '/api/student/quiz-attempt' else
                       2 * 1024 * 1024 if request.url.path.startswith('/api/student/quiz-drafts/') else
                       128 * 1024 if request.url.path == '/api/student/exercise-response' or bucket == 'draft' or re.match(r'/api/admin/mobile/(?:responses|consultations)/',request.url.path) else MAX_BODY_BYTES)
            async for chunk in request.stream():
                size += len(chunk)
                if size > maximum:
                    raise OverflowError
                chunks.append(chunk)
            return b''.join(chunks)
        try:
            body = await asyncio.wait_for(read_body(), timeout=30 if bucket in ('attachment_upload','business_import','pdf') else 5)
        except OverflowError:
            return error(413, 'Запрос слишком большой')
        except asyncio.TimeoutError:
            return error(408, 'Время передачи запроса истекло')
        query = parse_qs(request.url.query, keep_blank_values=True)
        if bucket == 'personal':
            if set(query) != {'birth_date'} or len(query['birth_date']) != 1 or not _birth_date(query['birth_date'][0]) or body:
                return error(422, 'Введите существующую дату: ДД.ММ.ГГГГ')
        elif request.url.path == '/api/geography/cities':
            if set(query) != {'q'} or len(query['q']) != 1 or len(query['q'][0]) > 80 or body:
                return error(422, 'Укажите название города длиной до 80 символов.')
        elif request.url.path == '/api/user/credit-history':
            if not set(query) <= {'limit', 'offset'} or any(
                    len(values) != 1 or not re.fullmatch(r'\d{1,6}', values[0]) or
                    not (1 if key == 'limit' else 0) <= int(values[0]) <= (100 if key == 'limit' else 100000)
                    for key, values in query.items()):
                return error(422, 'Некорректные параметры истории')
        elif request.url.path=='/api/admin/manage/users':
            if not set(query)<={'q','page','page_size'} or any(len(v)!=1 for v in query.values()) or len(query.get('q',[''])[0])>200:
                return error(422,'Некорректные параметры поиска')
            for k,maximum in [('page',100000),('page_size',100)]:
                if k in query and (not re.fullmatch(r'\d{1,6}',query[k][0]) or not 1<=int(query[k][0])<=maximum):return error(422,'Некорректная страница')
        elif request.url.path in {
            '/api/admin/mobile/reports', '/api/admin/mobile/lessons',
            '/api/admin/mobile/consultations', '/api/admin/mobile/responses',
            '/api/admin/mobile/challenge-notes',
        }:
            kind = request.url.path.rsplit('/', 1)[-1]
            allowed = {'q', 'page', 'page_size'}
            enums = {}
            if kind == 'reports':
                enums['state'] = {'all', 'paid', 'pending', 'expired'}
            elif kind in {'lessons', 'consultations'}:
                enums['archived'] = {'all', 'active', 'archived'}
            else:
                allowed.update({'lesson_id', 'user_id'})
                if kind == 'responses':
                    enums['reviewed'] = {'all', 'pending', 'reviewed'}
            allowed.update(enums)
            if method != 'GET' or body or not set(query) <= allowed or any(len(v) != 1 for v in query.values()):
                return error(422, 'Некорректные параметры поиска')
            if len(query.get('q', [''])[0]) > (120 if kind == 'reports' else 100):
                return error(422, 'Слишком длинный поисковый запрос')
            for key, maximum in [('page', 10000), ('page_size', 20 if kind == 'reports' else 100)]:
                if key in query and (not re.fullmatch(r'[0-9]{1,5}', query[key][0]) or not 1 <= int(query[key][0]) <= maximum):
                    return error(422, 'Некорректная страница')
            for key, values in enums.items():
                if key in query and query[key][0] not in values:
                    return error(422, 'Некорректный фильтр')
            for key in ('lesson_id', 'user_id'):
                if key in query and query[key][0] and not re.fullmatch(ID, query[key][0]):
                    return error(422, 'Некорректный идентификатор')
        elif query:
            return error(422, 'Параметры запроса не поддерживаются')
        if bucket == 'stripe_webhook':
            signatures=request.headers.getlist('stripe-signature')
            if len(signatures)!=1 or len(signatures[0])>2048:
                return error(400,'Отсутствует подпись Stripe')
            # Preserve the signed bytes exactly. Never JSON-decode/re-encode here.
        elif method in ('POST', 'PATCH') and bucket != 'personal':
            if request.headers.get('content-type', '').split(';')[0].strip() != 'application/json':
                return error(415, 'Ожидаются данные JSON')
            try:
                parsed = json.loads(body)
            except (ValueError, UnicodeDecodeError):
                return error(422, 'Некорректные данные JSON')
            if not _valid_body(request.url.path, parsed):
                return error(422, 'Проверьте введённые данные')
            body = json.dumps(parsed, ensure_ascii=False, allow_nan=False).encode()
        elif method in ('GET', 'HEAD') and body:
            return error(422, 'Тело запроса не поддерживается')
        headers = {'Accept': 'application/json', 'Accept-Encoding': 'identity',
                   'X-Forwarded-For': ip, 'X-Forwarded-Proto': 'https'}
        if protected:
            headers['Authorization'] = authorization
        if bucket == 'stripe_webhook':
            headers['Stripe-Signature'] = signatures[0]
        if body:
            headers['Content-Type'] = 'application/json'
        if origin:
            headers['Origin'] = origin
            headers['Referer'] = origin + '/'

        async def forward_media():
            range_value = request.headers.get('range')
            if range_value is not None and (len(range_value) > 80 or not re.fullmatch(r'bytes=(?:\d+-\d*|-\d+)', range_value)):
                return error(422, 'Запрошен недопустимый диапазон материала')
            if range_value:
                headers['Range'] = range_value
            if_range = request.headers.get('if-range')
            if if_range:
                if len(if_range) > 128 or any(char in if_range for char in '\r\n'):
                    return error(422, 'Некорректный диапазон материала')
                headers['If-Range'] = if_range
            client = httpx.AsyncClient(transport=transport, timeout=httpx.Timeout(60, connect=5),
                                       follow_redirects=False, trust_env=False)
            await in_flight.acquire()
            remote, closed = None, False
            async def close():
                nonlocal closed
                if not closed:
                    closed = True
                    try:
                        if remote is not None:
                            await remote.aclose()
                        await client.aclose()
                    finally:
                        in_flight.release()
            try:
                remote = await client.send(client.build_request(method, upstream_url + request.url.path,
                                                               headers=headers), stream=True)
                if remote.status_code not in (200, 206):
                    code = remote.status_code if 400 <= remote.status_code < 500 else 502
                    await close()
                    return error(code, 'Материал недоступен. Откройте его из урока ещё раз.')
                length = remote.headers.get('content-length', '')
                if not length.isdigit() or int(length) > MAX_MEDIA_BYTES or remote.headers.get('content-encoding', 'identity') != 'identity':
                    await close()
                    return error(502, 'Некорректный размер материала')
                media_headers = {key: value for key, value in remote.headers.items() if key.lower() in {
                    'content-type', 'content-length', 'content-range', 'accept-ranges',
                    'content-disposition', 'etag', 'last-modified'}}
                media_headers.update(response_headers)
                media_headers['Content-Security-Policy'] = "sandbox; default-src 'none'; media-src 'self' blob:; img-src 'self' data: blob:; style-src 'unsafe-inline'"
                media_headers['Access-Control-Expose-Headers'] = 'Content-Length, Content-Range, Accept-Ranges, Content-Disposition, ETag, Last-Modified'
                async def chunks():
                    size = 0
                    try:
                        async for chunk in remote.aiter_bytes():
                            size += len(chunk)
                            if size > int(length) or size > MAX_MEDIA_BYTES:
                                raise RuntimeError('Media response exceeded declared size')
                            yield chunk
                    finally:
                        await close()
                return StreamingResponse(chunks(), status_code=remote.status_code, headers=media_headers,
                                         background=BackgroundTask(close))
            except (httpx.HTTPError, asyncio.TimeoutError):
                await close()
                return error(502, 'Материал временно недоступен')
        if bucket == 'media':
            return await forward_media()

        async def forward():
            url = upstream_url + request.url.path + ('?' + request.url.query if request.url.query else '')
            try:
                async with in_flight, httpx.AsyncClient(transport=transport, timeout=95 if bucket == 'pdf' else 30 if bucket in ('checkout','stripe_webhook','attachment_upload') or request.url.path=='/api/numerology/vedic' else 12, follow_redirects=False, trust_env=False) as client:
                    async with client.stream(method, url, headers=headers, content=body) as remote:
                        if bucket == 'health' and remote.status_code == 503:
                            # Public readiness stays unavailable without exposing database diagnostics.
                            return JSONResponse({'status': 'unavailable', 'service': 'numerom'},
                                                status_code=503, headers=response_headers)
                        if 300 <= remote.status_code < 400 or remote.status_code >= 500:
                            return error(502, 'Сервер временно недоступен')
                        if remote.status_code == 422:
                            return error(422, 'Проверьте введённые данные')
                        chunks, size = [], 0
                        async for chunk in remote.aiter_bytes():
                            size += len(chunk)
                            if size > (max(max_response_bytes, 8 * 1024 * 1024) if request.url.path.startswith('/api/business') else max_response_bytes):
                                return error(502, 'Ответ сервера превышает допустимый размер')
                            chunks.append(chunk)
                        try:
                            result = json.loads(b''.join(chunks))
                        except (ValueError, UnicodeDecodeError):
                            return error(502, 'Некорректный ответ сервера')
                        return JSONResponse(result, status_code=remote.status_code, headers=response_headers)
            except (httpx.HTTPError, asyncio.TimeoutError):
                return error(502, 'Сервер временно недоступен')
        if bucket == 'personal':
            async with personal_lock:
                return await forward()
        return await forward()

    return Starlette(debug=False, routes=[Route('/{path:path}', gateway,
        methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE', 'HEAD', 'OPTIONS'])])


def create_app():
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).with_name('.env'))
    return create_public_gateway(
        [value.strip() for value in os.environ.get('PUBLIC_GATEWAY_ORIGINS', '').split(',') if value.strip()],
        trust_cloudflare=os.environ.get('PUBLIC_GATEWAY_TRUST_CLOUDFLARE') == '1',
    )
