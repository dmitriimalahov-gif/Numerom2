"""One-time credential recovery; Mongo performs token consumption atomically."""
import hashlib
import logging
import re
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlsplit
from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool
from auth import get_password_hash

logger = logging.getLogger(__name__)
GENERIC_MESSAGE = 'Если аккаунт с этим адресом существует, вы получите письмо со ссылкой. Проверьте также папку «Спам».'
INVALID_LINK = 'Ссылка недействительна или срок её действия истёк. Запросите новую.'

def valid_reset_url(value):
    try:
        url = urlsplit(value)
        return bool(url.hostname and not url.username and not url.password and not url.query and not url.fragment and
                    (url.scheme == 'https' or (url.scheme == 'http' and url.hostname in ('localhost','127.0.0.1','::1'))))
    except ValueError: return False

class RecoveryService:
    def __init__(self, db, mailer, reset_url, clock=datetime.utcnow):
        self.db, self.mailer, self.reset_url, self.clock = db, mailer, reset_url, clock
    @property
    def configured(self): return bool(self.mailer.configured and valid_reset_url(self.reset_url))
    async def _reserve(self, scope, value, seconds):
        key = hashlib.sha256(f'{scope}:{value}'.encode()).hexdigest()
        now = self.clock()
        try:
            await self.db.recovery_limits.find_one_and_update(
                {'_id':key,'next_allowed_at':{'$lte':now}},
                {'$set':{'next_allowed_at':now+timedelta(seconds=seconds),'expires_at':now+timedelta(hours=1)}}, upsert=True)
            return True
        except DuplicateKeyError: return False
    async def reserve_request(self, email, ip):
        if not self.configured:
            raise HTTPException(503, 'Восстановление временно недоступно. Обратитесь в поддержку NumerOM.')
        ip_allowed = await self._reserve('request-ip', ip, 10)
        email_allowed = await self._reserve('request-email', email.casefold(), 60)
        return ip_allowed and email_allowed
    async def deliver(self, email):
        # Called after the uniform HTTP response; account existence is never returned.
        token_hash = None
        try:
            user = await self.db.users.find_one({'email':{'$regex':'^'+re.escape(email)+'$','$options':'i'},'is_disabled':{'$ne':True}})
            if not user: return
            token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            # A password change or access revocation also cancels in-flight deliveries.
            version = user.get('auth_version')
            saved = await self.db.users.update_one({'id':user['id'],'is_disabled':{'$ne':True},
                'auth_version':version if version is not None else {'$exists':False}}, {'$set':{
                'password_reset_hash':token_hash,'password_reset_expires_at':self.clock()+timedelta(minutes=30)}})
            if not saved.matched_count: return
            await self.mailer.send_reset(user['email'], self.reset_url+'#token='+token)
        except Exception:
            if token_hash:
                await self.db.users.update_one({'password_reset_hash':token_hash}, {'$unset':{'password_reset_hash':'','password_reset_expires_at':''}})
            logger.error('Password recovery delivery failed; verify mail service configuration')
    async def reset(self, token, password, ip):
        if not await self._reserve('reset-ip', ip, 1):
            raise HTTPException(429, 'Подождите немного и повторите попытку.')
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        query = {'password_reset_hash':token_hash,'password_reset_expires_at':{'$gt':self.clock()},'is_disabled':{'$ne':True}}
        # Avoid expensive password hashing for random tokens, without consuming valid ones yet.
        if not await self.db.users.find_one(query): raise HTTPException(400, INVALID_LINK)
        password_hash = await run_in_threadpool(get_password_hash, password)
        # Single-document compare-and-update gives one winner even across multiple workers.
        user = await self.db.users.find_one_and_update(query, {
            '$set':{'password_hash':password_hash,'password_changed_at':self.clock(),'updated_at':self.clock()},
            '$inc':{'auth_version':1}, '$unset':{'password_reset_hash':'','password_reset_expires_at':''}},
            return_document=ReturnDocument.BEFORE)
        if not user: raise HTTPException(400, INVALID_LINK)
        return user['email']
    async def notify_changed(self, email):
        try: await self.mailer.send_changed(email)
        except Exception: logger.error('Password change notification failed; verify mail service configuration')
