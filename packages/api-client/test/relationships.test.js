const {test}=require('node:test');
const assert=require('node:assert/strict');
const {relationshipReceipt,relationshipCatalog,createRelationshipController}=require('../relationships');
const request={kind:'pair',main:{name:'Анна',birth_date:'10.01.1982'},people:[{name:'Иван',birth_date:'22.11.1990'}]};
const member={name:'Анна',birth_date:'10.01.1982',number:4,steps:['10 + 1 + 1982 = 1993']};
const fixture={id:'result',request_id:'uuid',cost:1,created_at:'2026-10-18T00:00:00+00:00',results:{version:1,kind:'pair',main:member,people:[member],connections:[{name:'Иван',score:8,title:'Близкие акценты',interpretation:'Текст',focus:'Практика',formula:'10 − 2 = 8'}],average:8,method:'Метод',note:'Шкала'}};
const make=options=>createRelationshipController({catalog:async()=>({pair:1,group:5}),history:async()=>({calculations:[]}),calculate:async()=>fixture,refreshBalance:async()=>{},makeId:()=> 'uuid',...options});
const draft=()=>JSON.parse(JSON.stringify(request));
test('relationship contract rejects invented or invalid graph values',()=>{
 assert.equal(relationshipReceipt(fixture).results.average,8);
 for(const average of [NaN,11,-1,'8'])assert.throws(()=>relationshipReceipt({...fixture,results:{...fixture.results,average}}));
 assert.throws(()=>relationshipReceipt({...fixture,results:{...fixture.results,people:[]}}));
 assert.deepEqual(relationshipCatalog({pair:0,group:5}),{pair:0,group:5});
 assert.throws(()=>relationshipCatalog({pair:1.5,group:5}));
});
test('opening history is free and rapid double press submits once',async()=>{
 let calls=0,release;const response=new Promise(resolve=>release=resolve);
 const c=make({calculate:async()=>{calls++;await response;return fixture;}});await c.load();assert.equal(calls,0);
 const one=c.calculate(draft(),20),two=c.calculate(draft(),20);assert.equal(calls,1);release();await Promise.all([one,two]);
 assert.equal(c.getSnapshot().result.id,'result');assert.equal(c.getSnapshot().busy,false);
});
test('network retry reuses exact request and changed form cannot spend again',async()=>{
 const bodies=[];let first=true;const c=make({calculate:async body=>{bodies.push(body);if(first){first=false;throw Error('Сеть');}return fixture;}});await c.load();
 await c.calculate(draft(),20);const changed=draft();changed.people[0].name='Другая';await c.calculate(changed,20);assert.equal(bodies.length,1);
 await c.retry();assert.equal(bodies.length,2);assert.deepEqual(bodies[0],bodies[1]);assert.equal(c.getSnapshot().pending,null);
});
test('balance refresh failure keeps result and refresh never repeats POST',async()=>{
 let calls=0,fail=true;const c=make({calculate:async()=>{calls++;return fixture;},refreshBalance:async()=>{if(fail)throw Error('Баланс');}});await c.load();await c.calculate(draft(),20);
 assert.equal(c.getSnapshot().result.id,'result');assert.ok(c.getSnapshot().balanceError);await c.calculate(draft(),20);assert.equal(calls,1);
 fail=false;await c.refreshBalance();assert.equal(calls,1);assert.equal(c.getSnapshot().balanceError,'');
});
test('invalid date, unknown price and insufficient balance never submit',async()=>{
 let calls=0;const c=make({calculate:async()=>{calls++;return fixture;}});
 await c.calculate(draft(),20);await c.load();await c.calculate(draft(),0);
 const bad=draft();bad.main.birth_date='31.02.2000';await c.calculate(bad,20);assert.equal(calls,0);
});
test('late history cannot charge or replace a selected result, and departed accounts cannot publish',async()=>{
 let release,current=true;const delayed=new Promise(resolve=>release=resolve);let count=0,calls=0;
 const c=make({history:async()=>++count===1?{calculations:[]}:delayed,calculate:async()=>{calls++;return fixture;},isCurrent:()=>current});await c.load();const loading=c.load();await c.calculate(draft(),20);assert.equal(calls,0);
 c.select(fixture);release({calculations:[{...fixture,id:'old'}]});await loading;assert.equal(c.getSnapshot().result.id,'result');
 await c.calculate(draft(),20);assert.equal(calls,1);
 current=false;await c.load();assert.equal(c.getSnapshot().result.id,'result');assert.equal(count,2);
});
test('free history recovers a committed attempt after response was lost',async()=>{
 let committed=false;const c=make({calculate:async()=>{committed=true;throw Error('Сеть');},history:async()=>({calculations:committed?[fixture]:[]})});
 await c.load();await c.calculate(draft(),20);assert.ok(c.getSnapshot().pending);await c.load();assert.equal(c.getSnapshot().pending,null);assert.equal(c.getSnapshot().result.id,'result');
});
module.exports={fixture};
