const {test}=require('node:test'),assert=require('node:assert/strict');
const {createCreditNotice,creditNoticeText}=require('../src/lib/creditNotice');
const {createApiClient}=require('../../packages/api-client');
const {createPaidCalculationController}=require('../../packages/api-client/paid-calculations');
const schema={parseCatalog:v=>v,parseReceipt:v=>v,validateDraft:()=>''};
const id='00000000-0000-4000-8000-000000000001';

test('zero balance opens on spending the last credits, once; login and free viewing stay quiet',()=>{
 const c=createCreditNotice();c.sync('account',0);
 assert.equal(c.getSnapshot(),null);
 c.sync('account',5);c.sync('account',0);
 assert.equal(creditNoticeText(c.getSnapshot()).title,'У вас закончились баллы');
 c.dismiss();c.sync('account',0);assert.equal(c.getSnapshot(),null);
 c.insufficient({balance:0,cost:1});assert.equal(c.getSnapshot().balance,0);
 c.dismiss();c.insufficient({balance:0,cost:0});assert.equal(c.getSnapshot(),null);
});
test('positive but insufficient balance shows cost; top-up and account changes clear stale notices',()=>{
 const c=createCreditNotice();c.sync('first',2);c.insufficient({balance:2,cost:5});
 assert.equal(creditNoticeText(c.getSnapshot()).title,'Недостаточно баллов');
 assert.match(creditNoticeText(c.getSnapshot()).description,/2.*5/);
 const first=c.getSnapshot();c.insufficient({balance:0,cost:1});assert.equal(c.getSnapshot(),first);
 c.sync('first',6);assert.equal(c.getSnapshot(),null);
 c.serverRefused('first');assert.deepEqual(c.getSnapshot(),{});
 c.sync('second',3);assert.equal(c.getSnapshot(),null);
 c.serverRefused('first');assert.equal(c.getSnapshot(),null);
 c.sync(null,undefined);c.insufficient({balance:0,cost:5});assert.equal(c.getSnapshot(),null);
});
test('insufficient calculation opens notice without charge, pending intent, UUID or draft changes',async()=>{
 let calls=0,ids=0,writes=0;const c=createCreditNotice();c.sync('student',0);
 const controller=createPaidCalculationController({
  catalog:async()=>({personal:5}),history:async()=>({calculations:[]}),
  calculate:async()=>{calls++;},makeId:()=>{ids++;return id;},refreshBalance:async()=>{},
  onInsufficientCredits:c.insufficient,pendingStore:{get:async()=>null,set:async()=>{writes++;}},
 },schema);
 await controller.load();
 const draft={kind:'personal',birth_date:'12.04.1990'};
 await controller.calculate(draft,0);
 assert.equal(c.getSnapshot().balance,0);assert.deepEqual([calls,ids,writes],[0,0,0]);
 assert.equal(controller.getSnapshot().pending,null);assert.equal(draft.birth_date,'12.04.1990');
 c.dismiss();await controller.calculate(draft,undefined);assert.equal(c.getSnapshot(),null);
});
test('free calculations remain available at zero; an exact balance creates one result and then the notice',async()=>{
 for(const cost of [0,5]){
  const c=createCreditNotice();c.sync('student',cost);let calls=0;
  const controller=createPaidCalculationController({
   catalog:async()=>({personal:cost}),history:async()=>({calculations:[]}),
   calculate:async body=>{calls++;return {id,request_id:body.request_id,created_at:'2026-10-20'};},
   makeId:()=>id,refreshBalance:async()=>c.sync('student',0),onInsufficientCredits:c.insufficient,
  },schema);
  await controller.load();await controller.calculate({kind:'personal'},cost);
  assert.equal(calls,1);assert.equal(controller.getSnapshot().result.id,id);
  assert.equal(!!c.getSnapshot(),cost>0);
 }
});
test('server 402 with stale balance opens notice, clears pending intent and preserves original failure',async()=>{
 const c=createCreditNotice();c.sync('student',100);let stored=null,calls=0;
 const api=createApiClient({baseUrl:'https://example.org',getToken:()=> 'student',onInsufficientCredits:c.serverRefused,
  fetchImpl:async()=>{calls++;return {ok:false,status:402,json:async()=>({detail:'Недостаточно баллов'})};}});
 const controller=createPaidCalculationController({
  catalog:async()=>({personal:5}),history:async()=>({calculations:[]}),calculate:body=>api.request('/numerology/personal',{method:'POST',body}),
  makeId:()=>id,refreshBalance:async()=>{},pendingStore:{get:async()=>stored,set:async value=>{stored=value;}},
 },schema);
 await controller.load();await controller.calculate({kind:'personal'},100);
 assert.equal(calls,1);assert.deepEqual(c.getSnapshot(),{});assert.equal(stored,null);
 assert.equal(controller.getSnapshot().pending,null);assert.match(controller.getSnapshot().error,/Недостаточно/);
});
test('authentication, network and validation failures never open a top-up notice',async()=>{
 for(const status of [400,401,403,422,500]){
  let notified=0;
  const api=createApiClient({baseUrl:'https://example.org',getToken:()=> 'student',onInsufficientCredits:()=>notified++,
   fetchImpl:async()=>({ok:false,status,json:async()=>({detail:'Ошибка'})})});
  await assert.rejects(api.request('/test'),e=>e.status===status);assert.equal(notified,0);
 }
});
test('late 402 after sign-out/account switch and unauthenticated 402 do not notify',async()=>{
 let token='first',reply;let notifications=0;
 const api=createApiClient({baseUrl:'https://example.org',getToken:()=>token,onInsufficientCredits:()=>notifications++,
  fetchImpl:()=>new Promise(resolve=>{reply=resolve;})});
 const response={ok:false,status:402,json:async()=>({})};
 const pending=api.request('/test');token='second';reply(response);
 await assert.rejects(pending,e=>e.status===402);assert.equal(notifications,0);
 const publicRequest=api.request('/test',{auth:false});reply(response);
 await assert.rejects(publicRequest,e=>e.status===402);assert.equal(notifications,0);
});
