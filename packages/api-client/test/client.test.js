const { test } = require('node:test');
const assert = require('node:assert/strict');
const { resolveBackendUrl, createApiClient, ApiError, validateBirthDate } = require('../index');
const json = (data, status = 200) => new Response(JSON.stringify(data), { status });

test('reopening a saved personal calculation only performs an authenticated read', async () => {
  const calls = [];
  const saved = {calculation:{id:'saved',birth_date:'10.01.1982',results:{soul_number:1}}};
  const api = createApiClient({baseUrl:'https://example.org',getToken:()=> 'current-user',fetchImpl:async(...args)=>{calls.push(args);return json(saved);}});
  assert.deepEqual(await api.latestPersonalNumbers(), saved);
  assert.equal(calls.length,1);
  assert.equal(calls[0][0],'https://example.org/api/numerology/personal-numbers/latest');
  assert.equal(calls[0][1].method,'GET');
  assert.equal(calls[0][1].headers.Authorization,'Bearer current-user');
  assert.equal(calls[0][1].body,undefined);
});

test('explicit API deployment is not replaced by the browser host', () => {
  assert.equal(resolveBackendUrl(' https://api.example.org/api/ ', { protocol: 'http:', hostname: 'localhost', port: '5128' }), 'https://api.example.org');
});
test('local development mappings and production same-origin are distinct', () => {
  assert.equal(resolveBackendUrl('', { protocol: 'http:', hostname: '192.168.1.8', port: '5128' }), 'http://192.168.1.8:8000');
  assert.equal(resolveBackendUrl('', { protocol: 'http:', hostname: 'localhost', port: '5129' }), 'http://localhost:8002');
  assert.equal(resolveBackendUrl('', { protocol: 'https:', hostname: 'numerom.example', port: '' }), 'https://numerom.example');
  assert.throws(() => resolveBackendUrl('javascript:alert(1)'), /HTTP/);
});
test('requests preserve query encoding and attach latest token', async () => {
  let token = 'first'; const calls = [];
  const api = createApiClient({ baseUrl: 'https://example.org/api/', getToken: () => token, fetchImpl: async (...args) => { calls.push(args); return json({ soul_number: 2 }); } });
  token = 'second';
  assert.equal((await api.personalNumbers('02.03.1990')).soul_number, 2);
  assert.equal(calls[0][0], 'https://example.org/api/numerology/personal-numbers?birth_date=02.03.1990');
  assert.equal(calls[0][1].headers.Authorization, 'Bearer second');
  assert.equal(calls[0][1].method, 'POST');
});
test('login does not carry an existing bearer token', async () => {
  let headers;
  await createApiClient({ baseUrl: 'https://example.org', getToken: () => 'old', fetchImpl: async (_, options) => { headers = options.headers; return json({access_token: 'new', user: {id: 'u'}}); } }).login('a@b.c', 'password');
  assert.equal(headers.Authorization, undefined);
});
test('failed mutations are never retried and report validation detail', async () => {
  let calls = 0;
  const api = createApiClient({ baseUrl: 'https://example.org', fetchImpl: async () => { calls++; return json({ detail: [{ msg: 'Invalid date' }] }, 422); } });
  await assert.rejects(api.updateProfile({ birth_date: 'bad' }), e => e instanceof ApiError && e.status === 422 && e.message.includes('Invalid date'));
  assert.equal(calls, 1);
});
test('401 invalidates only protected requests; 403 does not delete a session', async () => {
  const invalid = [];
  let status = 401;
  const api = createApiClient({ baseUrl: 'https://example.org', getToken: () => 'token-a', onUnauthorized: token => invalid.push(token), fetchImpl: async () => json({detail:'Denied'}, status) });
  await assert.rejects(api.profile());
  await assert.rejects(api.login('a@b.c', 'x'));
  status = 403;
  await assert.rejects(api.profile());
  assert.deepEqual(invalid, ['token-a']);
});
test('timeout and caller cancellation abort the transport without retry', async () => {
  const fetchImpl = (_, { signal }) => new Promise((_, reject) => signal.addEventListener('abort', () => reject(new Error('aborted')), { once: true }));
  const api = createApiClient({ baseUrl: 'https://example.org', timeoutMs: 10, fetchImpl });
  await assert.rejects(api.profile(), e => e.code === 'timeout');
  const controller = new AbortController();
  const request = api.request('/user/profile-v2', { signal: controller.signal }); controller.abort();
  await assert.rejects(request, e => e.code === 'cancelled');
});
test('birth date rejects impossible dates before a paid calculation', async () => {
  assert.equal(validateBirthDate('29.02.2000'), true);
  assert.equal(validateBirthDate('29.02.2001'), false);
  assert.equal(validateBirthDate('31.04.2000'), false);
  assert.equal(validateBirthDate('2000-01-02'), false);
  let called = false;
  const api = createApiClient({baseUrl: 'https://example.org', fetchImpl: async () => {called = true; return json({});}});
  await assert.rejects(api.personalNumbers('31.04.2000'));
  assert.equal(called, false);
});
test('a longer calculation timeout is scoped to that request', async () => {
  const fetchImpl=(_, {signal})=>new Promise((resolve,reject)=>{const timer=setTimeout(()=>resolve(json({ok:true})),25);signal.addEventListener('abort',()=>{clearTimeout(timer);reject(Error('aborted'));},{once:true});});
  const api=createApiClient({baseUrl:'https://example.org',timeoutMs:5,fetchImpl});
  assert.deepEqual(await api.request('/numerology/vedic',{timeoutMs:200}),{ok:true});
  await assert.rejects(api.profile(),e=>e.code==='timeout');
});

test('paid report profile errors preserve only supported recovery codes and owner order ids',async()=>{
 for(const detail of [{code:'full_report_profile_changed',message:'Review profile'},{code:'full_report_attempt_frozen',message:'Resume',order_id:'a'.repeat(64)},{code:'full_report_attempt_frozen',message:'Resume',order_id:'https://evil.example'},{code:'arbitrary',message:'Plain message'}]){
  const api=createApiClient({baseUrl:'https://example.org',getToken:()=> 'owner',fetchImpl:async()=>json({detail},409)});
  await assert.rejects(api.request('/full-reports/checkout',{method:'POST',body:{}}),error=>{assert.equal(error.message,detail.message);assert.equal(error.code,detail.code==='arbitrary'?'http':detail.code);assert.equal(error.orderId,detail.order_id==='a'.repeat(64)?detail.order_id:undefined);return true;});
 }
});
