const {test}=require('node:test'),assert=require('node:assert/strict');
const {createPaidCalculationController}=require('../paid-calculations');
const A='00000000-0000-4000-8000-000000000001',B='00000000-0000-4000-8000-000000000002';
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {resolve,promise};};
const receipt=id=>({id,request_id:id,created_at:'2026-10-18T12:00:00Z'});
const schema={parseCatalog:v=>v,parseReceipt:v=>v,validateDraft:()=>''};
test('history recovery owns pending storage until completion, blocking retry/new charges and coalescing concurrent loads',async()=>{
 const clearStarted=deferred(),clearFinished=deferred();let stored={kind:'personal',request_id:A,expected_cost:1},clears=0,reads=0,calls=[];
 const c=createPaidCalculationController({catalog:async()=>({personal:1}),history:async()=>{reads++;return {calculations:[receipt(A)]};},calculate:async body=>{calls.push(body.request_id);throw Error('lost response');},refreshBalance:async()=>{},makeId:()=>B,
  pendingStore:{get:async()=>stored,set:async value=>{if(value===null){clears++;clearStarted.resolve();await clearFinished.promise;}stored=value;}}},schema);
 const first=c.load();await clearStarted.promise;const second=c.load();
 assert.equal(first,second);assert.equal(c.getSnapshot().loading,true);assert.equal(c.getSnapshot().pending.request_id,A);
 await c.retry();await c.calculate({kind:'personal'},10);
 assert.deepEqual(calls,[]);assert.equal(stored.request_id,A);assert.match(c.getSnapshot().error,/Дождитесь/);
 clearFinished.resolve();await Promise.all([first,second]);
 assert.equal(reads,1);assert.equal(clears,1);assert.equal(c.getSnapshot().error,'');assert.equal(c.getSnapshot().pending,null);assert.equal(stored,null);
 await c.calculate({kind:'personal'},10);assert.deepEqual(calls,[B]);assert.equal(c.getSnapshot().pending.request_id,B);assert.equal(stored.request_id,B);
});
test('a history refresh during sending cannot race or erase the request being committed',async()=>{
 const started=deferred(),reply=deferred();let historyCalls=0,stored=null;
 const c=createPaidCalculationController({catalog:async()=>({personal:1}),history:async()=>{historyCalls++;return {calculations:[]};},calculate:async()=>{started.resolve();await reply.promise;throw Error('lost response');},refreshBalance:async()=>{},makeId:()=>A,pendingStore:{get:async()=>stored,set:async v=>{stored=v;}}},schema);
 await c.load();const sending=c.calculate({kind:'personal'},10);await started.promise;
 await c.load();assert.equal(historyCalls,1);assert.equal(c.getSnapshot().busy,true);assert.equal(stored.request_id,A);
 reply.resolve();await sending;assert.equal(c.getSnapshot().pending.request_id,A);assert.equal(stored.request_id,A);
});
test('recovery storage failure releases the phase while retaining the original retry intent',async()=>{
 let fail=true,stored={kind:'personal',request_id:A,expected_cost:1};const calls=[];
 const c=createPaidCalculationController({catalog:async()=>({personal:1}),history:async()=>({calculations:[receipt(A)]}),calculate:async body=>{calls.push(body.request_id);return receipt(A);},refreshBalance:async()=>{},makeId:()=>B,pendingStore:{get:async()=>stored,set:async v=>{if(fail&&v===null)throw Error('disk');stored=v;}}},schema);
 await c.load();assert.equal(c.getSnapshot().loading,false);assert.equal(c.getSnapshot().pending.request_id,A);
 fail=false;await c.retry();assert.deepEqual(calls,[A]);assert.equal(c.getSnapshot().pending,null);assert.equal(stored,null);
});
