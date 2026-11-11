const { test } = require('node:test');
const assert = require('node:assert/strict');
const { createSessionController, ApiError } = require('../index');
const deferred = () => { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; };
function setup(api, saved = 'saved') {
  let value = saved;
  const storage = { get: async () => value, set: async v => { value = v; }, remove: async () => { value = null; } };
  return { session: createSessionController({ api, storage }), stored: () => value };
}
test('restoration uses the stored bearer and returns the server profile', async () => {
  const { session } = setup({ profile: async () => ({ id:'u', credits_remaining: 7 }) });
  await session.restore();
  assert.equal(session.getToken(), 'saved'); assert.equal(session.getSnapshot().user.credits_remaining, 7);
  assert.equal(session.getSnapshot().status, 'signedIn');
});
test('temporary network failure keeps token and permits restoration retry', async () => {
  let fail = true;
  const { session, stored } = setup({ profile: async () => { if (fail) throw new ApiError('No network', 0, 'network'); return {id:'u'}; } });
  await session.restore();
  assert.equal(stored(), 'saved'); assert.equal(session.getSnapshot().status, 'unavailable');
  fail = false; await session.restore(); assert.equal(session.getSnapshot().status, 'signedIn');
});
test('expired session clears secure storage', async () => {
  const { session, stored } = setup({ profile: async () => { throw new ApiError('Expired', 401); } });
  await session.restore(); assert.equal(stored(), null); assert.equal(session.getSnapshot().status, 'signedOut');
});
test('late restoration cannot resurrect a signed out session', async () => {
  const response = deferred(); const { session, stored } = setup({profile: () => response.promise});
  const restore = session.restore(); await Promise.resolve(); await session.signOut();
  response.resolve({id:'u'}); await restore;
  assert.equal(stored(), null); assert.equal(session.getSnapshot().status, 'signedOut');
});
test('late login response cannot store a token after logout', async () => {
  const response = deferred(); const { session, stored } = setup({login: () => response.promise}, null);
  const login = session.signIn('a@b.c', 'password'); await session.signOut();
  response.resolve({access_token:'late', user:{id:'u'}}); await login;
  assert.equal(stored(), null); assert.equal(session.getToken(), null);
});
test('storage failure does not publish a signed in account', async () => {
  const session = createSessionController({api:{login:async () => ({access_token:'secret',user:{id:'u'}})}, storage:{get:async()=>null,set:async()=>{throw new Error('locked');},remove:async()=>{}}});
  await assert.rejects(session.signIn('a@b.c', 'password'));
  assert.equal(session.getToken(), null); assert.equal(session.getSnapshot().status, 'signedOut');
});
test('late logout storage failure does not overwrite a newer session restoration error state', async () => {
  let rejectRemoval;
  const removal = new Promise((_, reject) => {rejectRemoval = reject;});
  const profile = deferred();
  const session = createSessionController({api:{profile:()=>profile.promise},storage:{get:async()=> 'saved',set:async()=>{},remove:()=> removal}});
  const exit = session.signOut();
  const failure = assert.rejects(exit);
  const restore = session.restore();
  rejectRemoval(new Error('synthetic storage failure'));
  await failure;
  assert.equal(session.getSnapshot().status,'loading');
  assert.equal(session.getSnapshot().error,null);
  profile.resolve({id:'current'}); await restore;
  assert.equal(session.getSnapshot().user.id,'current');
});
test('failed secure-storage logout offers a repeat without restoring the old user', async () => {
  let fail = true;
  const session = createSessionController({api:{},storage:{get:async()=>null,set:async()=>{},remove:async()=>{if(fail)throw new Error('locked');}}});
  await assert.rejects(session.signOut());
  assert.equal(session.getSnapshot().status,'signedOut');
  assert.equal(session.getSnapshot().needsSignOutRetry,true);
  assert.equal(session.getToken(),null);
  fail=false;await session.signOut();
  assert.equal(!!session.getSnapshot().needsSignOutRetry,false);
  assert.equal(session.getSnapshot().error,null);
});

test('biometric lock removes the bearer and late profile refresh cannot unlock it',async()=>{
 let resolve;const pending=new Promise(r=>resolve=r);let delayed=false;
 const {session}=setup({profile:async()=>delayed?pending:{id:'u'}});
 await session.restore();delayed=true;const refresh=session.refresh();session.lock();resolve({id:'u'});await refresh;
 assert.equal(session.getToken(),null);assert.equal(session.getSnapshot().status,'locked');
});
