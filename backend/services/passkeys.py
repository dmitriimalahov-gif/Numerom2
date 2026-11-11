"""Discoverable WebAuthn credentials; the server never receives biometrics."""
import json
import os
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlsplit
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from webauthn import generate_registration_options, generate_authentication_options, verify_registration_response, verify_authentication_response, options_to_json
from webauthn.helpers import bytes_to_base64url, base64url_to_bytes
from webauthn.helpers.structs import AuthenticatorSelectionCriteria, ResidentKeyRequirement, UserVerificationRequirement, PublicKeyCredentialDescriptor
from auth import verify_password, create_access_token
from services.accounts import public_profile


class Passkeys:
    def __init__(self,db,rp_id=None,origins=None):
        self.db=db
        self.rp_id=rp_id or os.getenv('PASSKEY_RP_ID','dmitriimalahov-gif.github.io')
        self.origins=origins or os.getenv('PASSKEY_ORIGINS','https://dmitriimalahov-gif.github.io').split(',')

    def origin(self,origin):
        if origin not in self.origins:raise HTTPException(403,'Этот адрес не настроен для ключей доступа')
        host=urlsplit(origin).hostname
        if host!=self.rp_id and not (host or '').endswith('.'+self.rp_id):raise HTTPException(503,'Проверьте домен ключей доступа')
        return origin

    async def user(self,uid):
        user=await self.db.users.find_one({'id':uid,'is_disabled':{'$ne':True}})
        if not user:raise HTTPException(401,'Войдите в действующий аккаунт')
        return user

    async def begin(self,origin,uid=None,password=None):
        self.origin(origin)
        user=await self.user(uid) if uid else None
        if user:
            if not password or len(password.encode())>72 or not verify_password(password,user['password_hash']):raise HTTPException(400,'Пароль не подтверждён')
            rows=await self.db.passkeys.find({'user_id':uid}).to_list(10)
            if len(rows)>=10:raise HTTPException(409,'Удалите один из старых ключей доступа')
            options=generate_registration_options(rp_id=self.rp_id,rp_name='NumerOM',user_id=uid.encode(),user_name=user['email'],
                exclude_credentials=[PublicKeyCredentialDescriptor(id=base64url_to_bytes(r['_id'])) for r in rows],
                authenticator_selection=AuthenticatorSelectionCriteria(resident_key=ResidentKeyRequirement.REQUIRED,user_verification=UserVerificationRequirement.REQUIRED))
        else:
            options=generate_authentication_options(rp_id=self.rp_id,user_verification=UserVerificationRequirement.REQUIRED)
        challenge_id=secrets.token_urlsafe(32)
        await self.db.passkey_challenges.create_index('expires_at',expireAfterSeconds=0)
        await self.db.passkey_challenges.insert_one({'_id':challenge_id,'user_id':uid,'origin':origin,'auth_version':(user or {}).get('auth_version',0),
            'challenge':bytes_to_base64url(options.challenge),'expires_at':datetime.utcnow()+timedelta(minutes=3)})
        return {'challenge_id':challenge_id,'options':json.loads(options_to_json(options))}

    async def finish(self,origin,challenge_id,credential,uid=None,label='Моё устройство'):
        self.origin(origin)
        ceremony=await self.db.passkey_challenges.find_one_and_delete({'_id':challenge_id,'origin':origin,'user_id':uid,'expires_at':{'$gt':datetime.utcnow()}})
        if not ceremony:raise HTTPException(400,'Запрос входа истёк. Начните ещё раз.')
        try:
            common={'credential':credential,'expected_challenge':base64url_to_bytes(ceremony['challenge']),'expected_rp_id':self.rp_id,'expected_origin':origin,'require_user_verification':True}
            if uid:
                user=await self.user(uid)
                if user.get('auth_version',0)!=ceremony['auth_version']:raise HTTPException(401,'Войдите снова')
                proof=verify_registration_response(**common)
                row={'_id':bytes_to_base64url(proof.credential_id),'user_id':uid,'public_key':bytes_to_base64url(proof.credential_public_key),
                     'sign_count':proof.sign_count,'auth_version':user.get('auth_version',0),'label':label,'created_at':datetime.utcnow()}
                await self.db.passkeys.insert_one(row)
                return {'id':row['_id'],'label':label}
            row=await self.db.passkeys.find_one({'_id':credential.get('id')})
            if not row:raise HTTPException(400,'Ключ не найден. Войдите с паролем.')
            user=await self.user(row['user_id'])
            if row['auth_version']!=user.get('auth_version',0):raise HTTPException(400,'После изменения доступа добавьте ключ заново.')
            handle=(credential.get('response') or {}).get('userHandle')
            if not handle or base64url_to_bytes(handle)!=user['id'].encode():raise HTTPException(400,'Ключ относится к другому аккаунту')
            proof=verify_authentication_response(**common,credential_public_key=base64url_to_bytes(row['public_key']),credential_current_sign_count=row['sign_count'])
            updated=await self.db.passkeys.update_one({'_id':row['_id'],'sign_count':row['sign_count']},{'$set':{'sign_count':proof.new_sign_count,'last_used_at':datetime.utcnow()}})
            if not updated.matched_count:raise HTTPException(409,'Повторите вход с ключом доступа')
            role='admin' if user.get('is_admin') or user.get('is_super_admin') else 'user'
            return {'access_token':create_access_token({'sub':user['id'],'role':role,'auth_version':user.get('auth_version',0)}),'user':public_profile(user)}
        except HTTPException:raise
        except DuplicateKeyError:raise HTTPException(409,'Этот ключ уже зарегистрирован')
        except (ValueError,TypeError,KeyError):raise HTTPException(400,'Не удалось проверить ключ доступа. Начните ещё раз.')
        except Exception as error:
            # Library proof errors must never become a successful login.
            if error.__class__.__module__.startswith('webauthn'):raise HTTPException(400,'Не удалось проверить ключ доступа. Начните ещё раз.')
            raise

    async def list(self,uid):
        user=await self.user(uid)
        rows=await self.db.passkeys.find({'user_id':uid}).to_list(100)
        return {'keys':[{'id':r['_id'],'label':r['label'],'created_at':r['created_at'],'last_used_at':r.get('last_used_at'),
                         'active':r['auth_version']==user.get('auth_version',0)} for r in rows]}

    async def remove(self,uid,key_id):
        await self.user(uid)
        await self.db.passkeys.delete_one({'_id':key_id,'user_id':uid})
        return {'deleted':True}
