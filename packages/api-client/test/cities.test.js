const test=require('node:test'),assert=require('node:assert/strict');
const {createCitySearch}=require('../cities');
const tick=()=>new Promise(resolve=>setTimeout(resolve,5));
const city=(id,label)=>({id,name:label,region:'Region',country:'Country',label});
test('superseded responses and disposed requests cannot populate suggestions',async()=>{
 const pending=[];const controller=createCitySearch({delay:0,request:(url,{signal})=>new Promise(resolve=>pending.push({url,signal,resolve}))});
 controller.search('Paris');await tick();controller.search('London');await tick();
 assert.equal(pending[0].signal.aborted,true);pending[0].resolve({items:[city('1','Paris')]});await tick();assert.deepEqual(controller.getSnapshot().items,[]);
 pending[1].resolve({items:[city('2','London')]});await tick();assert.equal(controller.getSnapshot().items[0].label,'London');
 controller.search('Tokyo');await tick();controller.dispose();pending[2].resolve({items:[city('3','Tokyo')]});await tick();assert.deepEqual(controller.getSnapshot().items,[]);
});
test('selection cancels searching and failure leaves manual entry possible',async()=>{
 let calls=0;const controller=createCitySearch({delay:0,request:async()=>{calls++;throw Error('offline');}});
 controller.search('x');await tick();assert.equal(calls,0);controller.search('Moscow');await tick();assert.match(controller.getSnapshot().error,/вручную/);
 controller.clear();assert.equal(controller.getSnapshot().error,'');assert.equal(controller.getSnapshot().busy,false);
});
