const test=require('node:test'),assert=require('node:assert/strict'),{randomUUID}=require('node:crypto');
const {createPaidCalculationController}=require('../paid-calculations');
function make(options){return createPaidCalculationController({catalog:async()=>({kind:1}),history:async()=>({calculations:[]}),makeId:randomUUID,refreshBalance:async()=>{},...options},{parseCatalog:x=>x,parseReceipt:x=>x,validateDraft:x=>x.kind==='kind'?'':'invalid'});}
function store(){let value=null;return {get:async()=>value,set:async x=>{value=x;}};}
test('lost reply persists original paid intent across reload',async()=>{
 const pendingStore=store(),requests=[];
 const one=make({pendingStore,calculate:async b=>{requests.push(b);throw Error('offline');}});await one.load();await one.calculate({kind:'kind',input:'date'},10);
 const two=make({pendingStore,calculate:async b=>{requests.push(b);return {id:'r',request_id:b.request_id,created_at:'2026-10-18T00:00:00Z'};}});
 await two.load();assert.equal(two.getSnapshot().pending.request_id,requests[0].request_id);await two.retry();assert.deepEqual(requests[0],requests[1]);assert.equal(await pendingStore.get(),null);
});
test('history recovery clears paid intent without submitting again',async()=>{
 const pendingStore=store(),body={kind:'kind',request_id:randomUUID(),expected_cost:1};await pendingStore.set(body);let calls=0;
 const c=make({pendingStore,history:async()=>({calculations:[{id:'r',request_id:body.request_id,created_at:'2026-10-18T00:00:00Z'}]}),calculate:async()=>calls++});await c.load();await c.retry();assert.equal(calls,0);assert.equal(await pendingStore.get(),null);assert.equal(c.getSnapshot().result.id,'r');
});
test('failed persistence prevents payment request and keeps the same pending UUID',async()=>{
 let calls=0;const c=make({pendingStore:{get:async()=>null,set:async()=>{throw Error('disk');}},calculate:async()=>calls++});await c.load();await c.calculate({kind:'kind'},10);const id=c.getSnapshot().pending.request_id;await c.retry();assert.equal(calls,0);assert.equal(c.getSnapshot().pending.request_id,id);
});
