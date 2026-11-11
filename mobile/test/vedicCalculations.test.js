const {test}=require('node:test'),assert=require('node:assert/strict');
const {kinds,validateDraft,vedicReceipt,createVedicController,routeGeometry}=require('../src/lib/vedicCalculations');
const {readFileSync}=require('node:fs');
const fixture=require('./fixtures/vedicReport.json');
const id='cc225a20-0b98-4b21-8987-558da94c4b8f';
const receipt=()=>({id:'a'.repeat(64),request_id:id,created_at:'2026-10-18T11:00:00Z',cost:1,results:structuredClone(fixture)});
const draft={kind:'weekly',date:'2026-10-18',birth_date:'10.01.1982',city:'Кишинёв'};
test('server route retains every ordered day, all nine measured model values and period times',()=>{
 const row=receipt();assert.equal(vedicReceipt(row),row);assert.equal(row.results.days.length,7);
 for(const patch of [r=>r.results.days.pop(),r=>r.results.days[0].energies.pop(),r=>r.results.days[0].energies[0].value=null,r=>r.results.days[0].average=999,r=>r.results.days[1].date=r.results.days[0].date,r=>r.results.narration_id='digit-1']){const invalid=receipt();patch(invalid);assert.throws(()=>vedicReceipt(invalid));}
});
test('validation rejects invalid dates, personal routes without a birthday and control characters',()=>{
 assert.equal(validateDraft(draft),'');assert.equal(validateDraft({...draft,kind:'schedule',birth_date:''}),'');
 for(const patch of [{date:'2026-02-30'},{date:'2099-12-29'},{birth_date:''},{birth_date:'31.02.2000'},{city:'12'},{city:'a\nb'}])assert.ok(validateDraft({...draft,...patch}));
 assert.equal(validateDraft({...draft,kind:'daily',date:'2099-12-31'}),'');
});
test('graph maps actual zero and hundred to scale bounds and does not invent fallback points',()=>{
 const points=routeGeometry([{date:'a',average:0},{date:'b',average:100}]);assert.equal(points[0].y,132);assert.equal(points[1].y,14);assert.equal(points[0].x,25);assert.equal(points[1].x,315);
});
test('geolocation is validated, optional for manual city, and immutable across a paid retry',async()=>{
 assert.equal(validateDraft({...draft,location:{latitude:47.01,longitude:28.86}}),'');
 for(const location of [null,{latitude:91,longitude:0},{latitude:0,longitude:Infinity},{latitude:'47',longitude:28}])assert.ok(validateDraft({...draft,location}));
 let attempts=[];
 const controller=createVedicController({catalog:async()=>Object.fromEntries(Object.keys(kinds).map(k=>[k,1])),history:async()=>({calculations:[]}),calculate:async body=>{attempts.push(body);throw Error('network');},refreshBalance:async()=>{},makeId:()=>id});
 await controller.load();const location={latitude:47.01,longitude:28.86};await controller.calculate({...draft,location},10);location.latitude=48;await controller.retry();
 assert.equal(attempts.length,2);assert.equal(attempts[1].location.latitude,47.01);assert.deepEqual(attempts[0],attempts[1]);
});
test('lost response keeps one durable request, retries once, and history selection never charges',async()=>{
 let saved=null,attempts=[],calls=0;
 const controller=createVedicController({catalog:async()=>Object.fromEntries(Object.keys(kinds).map(k=>[k,1])),history:async()=>({calculations:[]}),calculate:async body=>{attempts.push(body);if(calls++===0)throw Error('network');return receipt();},refreshBalance:async()=>{},makeId:()=>id,pendingStore:{get:async()=>saved,set:async v=>{saved=v;}}});
 await controller.load();await controller.calculate(draft,10);assert.equal(controller.getSnapshot().pending.request_id,id);assert.equal(saved.request_id,id);
 await controller.calculate({...draft,date:'2026-10-19'},10);assert.equal(attempts.length,1);
 await controller.retry();assert.deepEqual(attempts[0],attempts[1]);assert.equal(saved,null);assert.equal(controller.getSnapshot().result.id,'a'.repeat(64));
 controller.select(receipt());assert.equal(attempts.length,2);
});
