const test=require('node:test');
const assert=require('node:assert/strict');
const {createLocationSelection}=require('../src/lib/locationSelection');
const {createPaidCalculationController}=require('../../packages/api-client/paid-calculations');
const {createWebLocationAdapter}=require('../src/lib/deviceLocationCore');
const flush=()=>new Promise(resolve=>setImmediate(resolve));
const deferred=()=>{let resolve;const promise=new Promise(done=>{resolve=done;});return {promise,resolve};};
const A={latitude:47.01,longitude:28.86,accuracy:10,timestamp:1};
const B={latitude:48.01,longitude:29.86,accuracy:10,timestamp:2};
const city=(name,point)=>({city:name,timezone:'Europe/Chisinau',latitude:point.latitude,longitude:point.longitude});

test('late reverse result cannot replace a newer observed return to the previous city',async()=>{
 let emit,clock=0;const pending=deferred(),selected=[],timers=[];
 const controller=createLocationSelection({
  locate:async()=>A,watchLocation:async next=>{emit=next;return()=>{};},
  resolve:async point=>point.latitude===A.latitude?city('Город A',point):pending.promise,
  onSelect:value=>selected.push(value),now:()=>clock,
  setTimer:fn=>{timers.push(fn);return timers.length;},clearTimer:()=>{},
 });
 await controller.startLive();emit(A);await flush();
 clock=60000;emit(B);await flush();
 emit({...A,timestamp:3});await flush();
 assert.equal(selected.at(-1).city,'Город A');
 pending.resolve(city('Город B',B));await flush();
 assert.equal(selected.at(-1).city,'Город A','older B lookup must not overwrite newer A observation');
 controller.stop();
});

test('manual edit cancels both a pending lookup and late watch registration',async()=>{
 const registration=deferred(),lookup=deferred();let emit,removed=0;const selected=[];
 const controller=createLocationSelection({locate:async()=>A,watchLocation:next=>{emit=next;return registration.promise;},resolve:()=>lookup.promise,onSelect:value=>selected.push(value)});
 const start=controller.startLive();emit(A);await flush();controller.clear();
 registration.resolve(()=>{removed++;});lookup.resolve(city('Город A',A));await start;await flush();
 assert.equal(removed,1);assert.deepEqual(selected,[]);assert.equal(controller.getSnapshot().live,false);assert.equal(controller.getSnapshot().location,null);
});

test('live draft changes cannot change the coordinates of a pending paid retry',async()=>{
 let draft={kind:'schedule',city:'Город A',location:{latitude:A.latitude,longitude:A.longitude}},first=true;const sent=[];
 const paid=createPaidCalculationController({catalog:async()=>({schedule:1}),history:async()=>({calculations:[]}),calculate:async body=>{sent.push(structuredClone(body));if(first){first=false;throw Error('offline');}return {id:'receipt',request_id:body.request_id};},refreshBalance:async()=>{},makeId:()=> '11111111-1111-4111-8111-111111111111'}, {parseCatalog:value=>value,parseReceipt:value=>value,validateDraft:()=>'',historyLimit:5});
 await paid.load();await paid.calculate(draft,10);
 draft.location.latitude=B.latitude;draft.location.longitude=B.longitude;draft.city='Город B';
 await paid.retry();
 assert.equal(sent.length,2);assert.deepEqual(sent[1],sent[0]);assert.deepEqual(sent[1].location,{latitude:A.latitude,longitude:A.longitude});
});

test('leaving the screen cancels a one-shot device subscription before its first fix',async()=>{
 let failure,cleared=0;
 const adapter=createWebLocationAdapter(()=>({secureContext:true,geolocation:{watchPosition:(_next,error)=>{failure=error;return 17;},clearWatch:id=>{assert.equal(id,17);cleared++;}}}),{timeoutMs:60000});
 const controller=createLocationSelection({...adapter,resolve:async point=>city('Город A',point),onSelect:()=>{}});
 const pending=controller.locate();await flush();controller.stop();
 const clearedOnStop=cleared;
 // Release the test's provider callback so no timer remains even on failure.
 failure({code:3});await pending;
 assert.equal(clearedOnStop,1,'one-shot OS watch must stop on blur/background/manual cancel, not wait for a fix or timeout');
});
