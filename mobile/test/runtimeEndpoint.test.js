const {test}=require('node:test'),assert=require('node:assert/strict');
const {generateKeyPairSync,sign}=require('node:crypto');
const {createEndpointResolver,verifyEndpoint}=require('../src/lib/runtimeEndpoint');
const {privateKey,publicKey}=generateKeyPairSync('ec',{namedCurve:'prime256v1'});
const jwk=publicKey.export({format:'jwk'});
const pub='04'+Buffer.from(jwk.x,'base64url').toString('hex')+Buffer.from(jwk.y,'base64url').toString('hex');
const cfg=(api,iat)=>({v:1,api,iat,sig:sign('sha256',Buffer.from(`numerom-config:v1:${api}:${iat}`),{key:privateKey,dsaEncoding:'ieee-p1363'}).toString('hex')});
const old=cfg('https://old.example.org',100),next=cfg('https://new.example.org',200);
test('only valid NumerOM signatures and HTTPS origins are accepted',()=>{
 assert.equal(verifyEndpoint(next,pub,300),true);
 for(const bad of [{...next,api:'https://evil.example.org'},{...next,v:2},{...next,iat:3010},{...next,sig:'00'.repeat(64)},cfg('http://example.org',200),cfg('https://example.org/path',200)])assert.equal(verifyEndpoint(bad,pub,300),false);
});
test('the same installed app picks a new signed endpoint and refuses rollback and tampered cache',async()=>{
 let remote=next,stored=JSON.stringify({...old,api:'https://evil.example.org'}),calls=0,clock=300000;
 const resolver=createEndpointResolver({bundled:old,publicKey:pub,configUrl:'https://pages.example.org/runtime-config.json',now:()=>clock,
  storage:{get:async()=>stored,set:async v=>{stored=v;}},fetchImpl:async()=>{calls++;return {ok:true,text:async()=>JSON.stringify(remote)};}});
 assert.equal(await resolver.ready(),'https://new.example.org');assert.equal(JSON.parse(stored).api,next.api);
 remote=old;clock+=31000;await resolver.refresh();assert.equal(resolver.current(),next.api);
 remote={...next,iat:400,api:'https://evil.example.org'};clock+=31000;await resolver.refresh();assert.equal(resolver.current(),next.api);
 assert.equal(calls,3);
});
test('offline configuration retains verified address and concurrent refreshes coalesce',async()=>{
 let resolve,calls=0;
 const resolver=createEndpointResolver({bundled:old,publicKey:pub,configUrl:'https://pages.example.org/runtime-config.json',now:()=>300000,
  storage:{get:async()=>JSON.stringify(next),set:async()=>{}},fetchImpl:async()=>{calls++;return new Promise(r=>{resolve=r;});}});
 const a=resolver.ready(),b=resolver.ready();await new Promise(r=>setImmediate(r));assert.equal(calls,1);
 resolve({ok:false});assert.deepEqual(await Promise.all([a,b]),[next.api,next.api]);
});
