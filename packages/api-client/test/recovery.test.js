const {test}=require('node:test'),assert=require('node:assert/strict');
const {createApiClient,createSessionController}=require('..');
const response=(status,data)=>({ok:status<400,status,json:async()=>data});
test('reads follow a verified new origin once; writes never replay after an ambiguous failure',async()=>{
 for(const method of ['GET','POST']){
  let origin='https://old.example.org',calls=[];
  const api=createApiClient({baseUrl:origin,getBaseUrl:async()=>origin,getToken:()=> 'token',
   onConnectionFailure:async old=>{assert.equal(old,origin);origin='https://new.example.org';return true;},
   fetchImpl:async(url,opts)=>{calls.push([url,opts]);if(url.includes('old.'))throw Error('offline');return response(200,{ok:true});}});
  if(method==='GET')assert.deepEqual(await api.request('/test'),{ok:true});
  else await assert.rejects(api.request('/test',{method,body:{request_id:'same'}}),e=>e.code==='network');
  assert.equal(calls.length,method==='GET'?2:1);
  assert.equal(calls[0][1].redirect,'error');
 }
});
test('a hung transport or body cannot leave login busy forever, even when abort is ignored',async()=>{
 for(const fetchImpl of [()=>new Promise(()=>{}),async()=>({ok:true,status:200,json:()=>new Promise(()=>{})})]){
  const api=createApiClient({baseUrl:'https://example.org',timeoutMs:10,fetchImpl});
  await assert.rejects(api.login('test@example.invalid','test-password'),e=>e.code==='timeout');
 }
});
test('offline restoration keeps the stored login and reconnects without another password',async()=>{
 let online=false,saved='saved-token',removed=0;
 const api=createApiClient({baseUrl:'https://example.org',getToken:()=>session.getToken(),fetchImpl:async()=>{if(!online)throw Error('offline');return response(200,{id:'student'});}});
 const session=createSessionController({api,storage:{get:async()=>saved,set:async v=>{saved=v;},remove:async()=>{removed++;saved=null;}}});
 await session.restore();assert.equal(session.getSnapshot().status,'unavailable');assert.equal(removed,0);
 online=true;await session.restore();assert.equal(session.getSnapshot().status,'signedIn');assert.equal(session.getToken(),'saved-token');
});
test('an account change during config refresh cannot replay an old authenticated read',async()=>{
 let token='first',calls=0;
 const api=createApiClient({baseUrl:'https://example.org',getToken:()=>token,fetchImpl:async()=>{calls++;throw Error('offline');},onConnectionFailure:async()=>{token='second';return true;}});
 await assert.rejects(api.request('/test'));assert.equal(calls,1);
});
