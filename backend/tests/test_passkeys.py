"""Software authenticator tests: real P-256 signatures, no mocked verifier."""
import hashlib,json,os,secrets,sys,unittest,uuid
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cbor2
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from webauthn.helpers import bytes_to_base64url as b64
from auth import get_password_hash
from services.passkeys import Passkeys
from routers.passkeys import create_passkeys_router
from public_gateway import _route,_valid_body

RP='example.test';ORIGIN='https://example.test'
class Authenticator:
 def __init__(self):self.key=ec.generate_private_key(ec.SECP256R1());self.id=secrets.token_bytes(32)
 def proof(self,options,register=False,count=1,uv=True,origin=ORIGIN,uid='u'):
  client=json.dumps({'type':'webauthn.create' if register else 'webauthn.get','challenge':options['challenge'],'origin':origin,'crossOrigin':False}).encode()
  flags=1|(4 if uv else 0)|(64 if register else 0)
  auth=hashlib.sha256(RP.encode()).digest()+bytes([flags])+count.to_bytes(4,'big')
  if register:
   numbers=self.key.public_key().public_numbers()
   public=cbor2.dumps({1:2,3:-7,-1:1,-2:numbers.x.to_bytes(32,'big'),-3:numbers.y.to_bytes(32,'big')})
   auth+=bytes(16)+len(self.id).to_bytes(2,'big')+self.id+public
   response={'attestationObject':b64(cbor2.dumps({'fmt':'none','attStmt':{},'authData':auth}))}
  else:response={'authenticatorData':b64(auth),'signature':b64(self.key.sign(auth+hashlib.sha256(client).digest(),ec.ECDSA(hashes.SHA256()))),'userHandle':b64(uid.encode())}
  return {'id':b64(self.id),'rawId':b64(self.id),'type':'public-key','response':{**response,'clientDataJSON':b64(client)}}

class Contracts(unittest.TestCase):
 def test_router_and_gateway(self):
  self.assertEqual(len(create_passkeys_router(None).routes),6)
  self.assertEqual(_route('POST','/api/auth/passkeys/options'),'login')
  self.assertTrue(_valid_body('/api/auth/passkeys/options',{}))
  self.assertFalse(_valid_body('/api/auth/passkeys/options',{'user_id':'victim'}))
 def test_default_passkey_entry_is_only_the_official_domain(self):
  with patch.dict(os.environ,{},clear=True):
   service=Passkeys(None)
  self.assertEqual(service.origin('https://1.numer.om'),('https://1.numer.om','1.numer.om'))
  with self.assertRaises(HTTPException):
   service.origin('https://dmitriimalahov-gif.github.io')

@unittest.skipUnless(os.getenv('NUMEROM_TEST_MONGO_URL'),'isolated Mongo only')
class PasskeyTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  self.client=AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL']);self.db=self.client['numerom_test_passkeys_'+uuid.uuid4().hex]
  self.env=os.environ.get('SECRET_KEY');os.environ['SECRET_KEY']='isolated-webauthn-test-signing-key-only'
  await self.db.users.insert_one({'id':'u','email':'test@example.invalid','password_hash':get_password_hash('preview-only'),'auth_version':0})
  self.s=Passkeys(self.db,rp_id=RP,origins=[ORIGIN]);self.device=Authenticator()
 async def asyncTearDown(self):
  await self.client.drop_database(self.db.name);self.client.close()
  if self.env is None:os.environ.pop('SECRET_KEY',None)
  else:os.environ['SECRET_KEY']=self.env
 async def register(self):
  r=await self.s.begin(ORIGIN,'u','preview-only')
  return await self.s.finish(ORIGIN,r['challenge_id'],self.device.proof(r['options'],register=True),uid='u')
 async def attempt(self,**kwargs):
  r=await self.s.begin(ORIGIN)
  proof=self.device.proof(r['options'],**kwargs)
  return r,proof
 async def test_real_registration_and_discoverable_login(self):
  await self.register();r,proof=await self.attempt(count=2)
  result=await self.s.finish(ORIGIN,r['challenge_id'],proof)
  self.assertEqual(result['user']['id'],'u');self.assertTrue(result['access_token'])
  self.assertNotIn('public_key',(await self.s.list('u'))['keys'][0])
  with self.assertRaises(HTTPException):await self.s.finish(ORIGIN,r['challenge_id'],proof)
 async def test_password_and_exact_origin_are_required_to_add_key(self):
  for origin,pw in [(ORIGIN,'wrong'),('https://attacker.test','preview-only')]:
   with self.assertRaises(HTTPException):await self.s.begin(origin,'u',pw)
  self.assertEqual(await self.db.passkeys.count_documents({}),0)
 async def test_missing_user_verification_wrong_origin_and_userhandle_fail(self):
  await self.register()
  for patch in [{'uv':False},{'origin':'https://evil.test'},{'uid':'victim'}]:
   r,proof=await self.attempt(count=2,**patch)
   with self.assertRaises(HTTPException):await self.s.finish(ORIGIN,r['challenge_id'],proof)
 async def test_signature_tampering_and_counter_rollback_fail(self):
  await self.register();r,proof=await self.attempt(count=2);proof['response']['signature']=b64(bytes(70))
  with self.assertRaises(HTTPException):await self.s.finish(ORIGIN,r['challenge_id'],proof)
  r,proof=await self.attempt(count=1)
  with self.assertRaises(HTTPException):await self.s.finish(ORIGIN,r['challenge_id'],proof)
 async def test_expired_ceremony_deleted_key_and_disabled_user(self):
  key=await self.register();r,proof=await self.attempt(count=2)
  from datetime import datetime,timedelta
  await self.db.passkey_challenges.update_one({'_id':r['challenge_id']},{'$set':{'expires_at':datetime.utcnow()-timedelta(seconds=1)}})
  with self.assertRaises(HTTPException):await self.s.finish(ORIGIN,r['challenge_id'],proof)
  await self.s.remove('u',key['id']);r,proof=await self.attempt(count=2)
  with self.assertRaises(HTTPException):await self.s.finish(ORIGIN,r['challenge_id'],proof)
  await self.register();await self.db.users.update_one({'id':'u'},{'$set':{'is_disabled':True}});r,proof=await self.attempt(count=2)
  with self.assertRaises(HTTPException):await self.s.finish(ORIGIN,r['challenge_id'],proof)
 async def test_password_reset_revokes_preexisting_keys(self):
  await self.register();await self.db.users.update_one({'id':'u'},{'$inc':{'auth_version':1}})
  r,proof=await self.attempt(count=2)
  with self.assertRaises(HTTPException):await self.s.finish(ORIGIN,r['challenge_id'],proof)
  self.assertFalse((await self.s.list('u'))['keys'][0]['active'])
 async def test_removal_is_owner_scoped(self):
  key=await self.register();await self.db.users.insert_one({'id':'other'})
  await self.s.remove('other',key['id']);self.assertEqual(len((await self.s.list('u'))['keys']),1)
