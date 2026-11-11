const {test}=require('node:test');
const assert=require('node:assert/strict');
const {createLocationSelection,distance}=require('../src/lib/locationSelection');
const deferred=()=>{let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return {promise,resolve,reject};};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const point=(latitude=47.01,longitude=28.86)=>({latitude,longitude,accuracy:80,timestamp:1000});
function fixture(overrides={}){
 let next,error,stops=0,time=100000,timers=[],selections=[],requests=[];
 const controller=createLocationSelection({locate:async()=>point(),watchLocation:async(onPosition,onError)=>{next=onPosition;error=onError;return()=>stops++;},resolve:async p=>{requests.push(p);return {...p,city:'Кишинёв, Молдова',timezone:'Europe/Chisinau'};},onSelect:v=>selections.push(v),now:()=>time,setTimer:(fn,ms)=>{const timer={fn,ms};timers.push(timer);return timer;},clearTimer:timer=>{timers=timers.filter(t=>t!==timer);},...overrides});
 return {controller,selections,requests,emit:p=>next(p),error:e=>error(e),get stops(){return stops;},get timers(){return timers;},advance:ms=>{time+=ms;const copy=timers;timers=[];copy.forEach(t=>t.fn());}};
}
test('one-time city lookup is explicit, sends only coordinates and proposes city',async()=>{
 const f=fixture();assert.equal(f.requests.length,0);await f.controller.locate();
 assert.deepEqual(f.requests,[{latitude:47.01,longitude:28.86}]);assert.equal(f.selections[0].city,'Кишинёв, Молдова');
 assert.equal(f.controller.getSnapshot().accuracy,80);assert.equal(f.controller.getSnapshot().live,false);
});
test('manual edit invalidates late reverse lookup and resets derived city',async()=>{
 const lookup=deferred(),f=fixture({resolve:()=>lookup.promise});const operation=f.controller.locate();await tick();f.controller.clear();
 lookup.resolve({...point(),city:'Старый город',timezone:'Europe/Chisinau'});await operation;
 assert.equal(f.selections.length,0);assert.equal(f.controller.getSnapshot().location,null);assert.equal(f.controller.getSnapshot().busy,false);
});
test('late permission reply after background does not request a city',async()=>{
 const permission=deferred(),f=fixture({locate:()=>permission.promise});const operation=f.controller.locate();f.controller.stop();permission.resolve(point());await operation;assert.equal(f.requests.length,0);
});
test('late live subscription is removed after screen closes',async()=>{
 let removed=0;const subscription=deferred(),f=fixture({watchLocation:()=>subscription.promise});const operation=f.controller.startLive();f.controller.stop();subscription.resolve(()=>removed++);await operation;
 assert.equal(removed,1);assert.equal(f.controller.getSnapshot().live,false);
});
test('live stop invalidates callbacks and cleanup runs exactly once',async()=>{
 const f=fixture();await f.controller.startLive();f.emit(point());await tick();f.controller.stop();f.controller.stop();f.emit(point(48));await tick();
 assert.equal(f.stops,1);assert.equal(f.requests.length,1);assert.equal(f.controller.getSnapshot().live,false);
});
test('GPS jitter updates coordinates without another reverse request',async()=>{
 const f=fixture();await f.controller.startLive();f.emit(point());await tick();f.emit(point(47.0105));await tick();
 assert.equal(f.requests.length,1);assert.equal(f.selections.at(-1).latitude,47.0105);
});
test('movement queues the latest position and rate-limits lookup to once per minute',async()=>{
 const f=fixture();await f.controller.startLive();f.emit(point());await tick();f.emit(point(48));f.emit(point(49));await tick();
 assert.equal(f.requests.length,1);assert.equal(f.timers.length,1);assert.equal(f.timers[0].ms,60000);
 f.advance(60000);await tick();assert.equal(f.requests.length,2);assert.equal(f.requests[1].latitude,49);assert.equal(f.selections.at(-1).latitude,49);
});
test('movement during lookup gets another lookup rather than being lost',async()=>{
 const lookup=deferred();let calls=0;const f=fixture({resolve:async p=>{calls++;if(calls===1)return lookup.promise;return {...p,city:'Другой город',timezone:'Europe/Paris'};}});
 await f.controller.startLive();f.emit(point());f.emit(point(48));lookup.resolve({...point(),city:'Кишинёв, Молдова',timezone:'Europe/Chisinau'});await tick();
 assert.equal(f.timers.length,1);f.advance(60000);await tick();assert.equal(calls,2);assert.equal(f.selections.at(-1).city,'Другой город');
});
test('manual editing cancels a queued movement lookup',async()=>{
 const f=fixture();await f.controller.startLive();f.emit(point());await tick();f.emit(point(48));assert.equal(f.timers.length,1);f.controller.clear();f.advance(60000);await tick();assert.equal(f.requests.length,1);assert.equal(f.stops,1);
});
test('denied or unavailable location leaves manual input untouched',async()=>{
 const f=fixture({locate:async()=>{throw Error('Доступ к геолокации запрещён.');}});await f.controller.locate();assert.equal(f.selections.length,0);assert.match(f.controller.getSnapshot().error,/запрещён/);assert.equal(f.controller.getSnapshot().busy,false);
});
test('live errors stop observation, account changes invalidate pending results',async()=>{
 const f=fixture();await f.controller.startLive();f.error(Error('Нет сигнала'));assert.equal(f.stops,1);assert.equal(f.controller.getSnapshot().live,false);
 let owner=true;const lookup=deferred(),g=fixture({isCurrent:()=>owner,resolve:()=>lookup.promise});const pending=g.controller.locate();await tick();owner=false;lookup.resolve({...point(),city:'Кишинёв',timezone:'Europe/Chisinau'});await pending;assert.equal(g.selections.length,0);g.controller.stop();
});
test('malformed device positions never leave the device; zero coordinates remain valid',async()=>{
 for(const p of [point(NaN),point(91),point(1,181),point('47')]){const f=fixture({locate:async()=>p});await f.controller.locate();assert.equal(f.requests.length,0);assert.ok(f.controller.getSnapshot().error);}
 const f=fixture({locate:async()=>point(0,0)});await f.controller.locate();assert.equal(f.requests.length,1);
 assert.equal(distance(point(),point()),0);
});
