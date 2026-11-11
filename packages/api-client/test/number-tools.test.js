const {test}=require('node:test'),assert=require('node:assert/strict');
const {toolCatalog,toolReceipt,createToolController}=require('../number-tools');
const fixture={id:'saved',request_id:'uuid',cost:1,created_at:'2026-10-18T00:00:00Z',results:{version:1,kind:'name',title:'Имя',summary:'Анна',method:'Метод',inputs:{name:'Анна'},items:[{key:'name',label:'Имя',source:'Анна',number:5,total:14,tokens:[{symbol:'А',value:1},{symbol:'Н',value:6},{symbol:'Н',value:6},{symbol:'А',value:1}],steps:['1 + 6 + 6 + 1 = 14','1 + 4 = 5'],title:'Свобода',interpretation:'Значение имени',focus:'Подсказка',narration_id:'tool-name-5'}]}};
const draft={kind:'name',inputs:{name:'Анна'}};
const make=options=>createToolController({catalog:async()=>({name:1,address:1,car:1}),history:async()=>({calculations:[]}),calculate:async()=>fixture,refreshBalance:async()=>{},makeId:()=> 'uuid',...options});
test('tool contract verifies chart contributions and contextual audio identity',()=>{
 assert.equal(toolReceipt(fixture),fixture);assert.equal(toolCatalog({name:0,address:1,car:1}).name,0);
 for(const patch of [{total:15},{narration_id:'tool-car-5'},{number:0},{tokens:[]},{steps:[]}])assert.throws(()=>toolReceipt({...fixture,results:{...fixture.results,items:[{...fixture.results.items[0],...patch}]}}));
});
test('unsupported or empty data cannot spend',async()=>{
 let calls=0;const c=make({calculate:async()=>{calls++;return fixture;}});await c.load();
 for(const bad of [{kind:'name',inputs:{name:'123'}},{kind:'name',inputs:{name:'Ștefan'}},{kind:'address',inputs:{house_number:'A'}},{kind:'address',inputs:{house_number:'4',postal_code:'000'}},{kind:'car',inputs:{car_number:'²'}}])await c.calculate(bad,20);
 assert.equal(calls,0);await c.calculate(draft,0);assert.equal(calls,0);
});
test('ambiguous network failure retains exact payload and history can recover without spending',async()=>{
 let calls=0,committed=false;const bodies=[];const c=make({calculate:async body=>{calls++;bodies.push(body);committed=true;throw Error('Сеть');},history:async()=>({calculations:committed?[fixture]:[]})});await c.load();
 await c.calculate(draft,20);await c.calculate({kind:'car',inputs:{car_number:'ABC123'}},20);assert.equal(calls,1);
 await c.retry();assert.deepEqual(bodies[0],bodies[1]);await c.load();assert.equal(c.getSnapshot().pending,null);assert.equal(c.getSnapshot().result.id,'saved');assert.equal(calls,2);
});
test('double press and balance failure keep the committed result',async()=>{
 let calls=0,release;const wait=new Promise(resolve=>release=resolve);const c=make({calculate:async()=>{calls++;await wait;return fixture;},refreshBalance:async()=>{throw Error('Баланс');}});await c.load();
 const one=c.calculate(draft,20),two=c.calculate(draft,20);release();await Promise.all([one,two]);assert.equal(calls,1);assert.equal(c.getSnapshot().result.id,'saved');assert.ok(c.getSnapshot().balanceError);await c.refreshBalance();assert.equal(calls,1);
});
module.exports={fixture};
