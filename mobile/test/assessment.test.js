const {test}=require('node:test');const assert=require('node:assert/strict');
const fixture=require('./fixtures/assessment.json');const {assessmentCatalog,assessmentReceipt,createAssessmentController}=require('../src/lib/assessment');
test('catalog and receipt expose all ten real choices with the matching theme',()=>{
 assert.equal(assessmentCatalog(fixture.catalog).questions.length,10);assert.equal(assessmentReceipt(fixture.receipt).results.number,1);
 assert.throws(()=>assessmentCatalog({...fixture.catalog,questions:fixture.catalog.questions.slice(1)}));
 assert.throws(()=>assessmentReceipt({...fixture.receipt,results:{...fixture.receipt.results,narration_id:'unrelated'}}));
});
test('incomplete draft never submits or charges',async()=>{
 let calls=0;const controller=createAssessmentController({catalog:async()=>fixture.catalog,history:async()=>({calculations:[]}),calculate:async()=>{calls++;return fixture.receipt;},refreshBalance:async()=>{},makeId:()=>fixture.request.request_id});
 await controller.load();await controller.calculate({kind:'assessment',answers:{}},10);assert.equal(calls,0);assert.match(controller.getSnapshot().error,/десять/);
});
test('lost response reloads the same pending request and recovers without a second charge',async()=>{
 let pending=null,first=true,bodies=[];const store={get:async()=>pending,set:async v=>{pending=v;}};
 const options={catalog:async()=>fixture.catalog,history:async()=>({calculations:[]}),calculate:async body=>{bodies.push(body);if(first){first=false;throw Error('connection lost');}return fixture.receipt;},refreshBalance:async()=>{},makeId:()=>fixture.request.request_id,pendingStore:store};
 const original=createAssessmentController(options);await original.load();await original.calculate({kind:'assessment',answers:fixture.request.answers},10);assert.ok(pending);
 const resumed=createAssessmentController(options);await resumed.load();await resumed.retry();assert.deepEqual(bodies[0],bodies[1]);assert.equal(pending,null);assert.equal(resumed.getSnapshot().result.results.number,1);
});
