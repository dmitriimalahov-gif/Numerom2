const test=require('node:test'),assert=require('node:assert/strict');
const {createExerciseDraft}=require('../src/lib/exerciseDraft');
let counter=0;
function make(options={}){let row={text:null,revision:0,request_id:null};return createExerciseDraft({initial:'Отправленный ответ',read:async()=>({...row}),write:async body=>{row={...body,revision:body.revision+1};return row;},makeId:()=>`request-${++counter}`,delay:60000,...options});}
test('restores a private draft separately from the submitted answer',async()=>{
 const c=make({read:async()=>({revision:2,text:'Черновик',request_id:'old'})});await c.load();assert.equal(c.getSnapshot().text,'Черновик');assert.equal(c.getSnapshot().saved,true);c.dispose();
});
test('pending writes serialize edits and clearing keeps the visible submitted text',async()=>{
 let release;const bodies=[];const c=make({write:async body=>{bodies.push({...body});if(bodies.length===1)await new Promise(r=>release=r);return {...body,revision:body.revision+1};}});
 await c.load();c.edit('Первый');const writing=c.flush();c.edit('Второй');release();assert.equal(await writing,true);
 assert.deepEqual(bodies.map(b=>b.text),['Первый','Второй']);assert.equal(c.getSnapshot().saved,true);
 await c.clear();assert.equal(bodies[2].text,null);assert.equal(c.getSnapshot().text,'Второй');assert.equal(c.getSnapshot().dirty,false);c.dispose();
});
test('lost response retries the identical request before saving later typing',async()=>{
 let first=true;const bodies=[];const c=make({write:async body=>{bodies.push({...body});if(first){first=false;throw Error('Нет соединения');}return {...body,revision:body.revision+1};}});
 await c.load();c.edit('Исходный');assert.equal(await c.flush(),false);c.edit('Продолженный');await c.flush();assert.deepEqual(bodies[0],bodies[1]);assert.equal(bodies[2].text,'Продолженный');c.dispose();
});
test('version conflict preserves typing until explicit resolution',async()=>{
 let revision=0;const c=make({read:async()=>({revision,text:'На другом устройстве',request_id:null}),write:async body=>{if(body.revision!==2)throw Object.assign(Error('Conflict'),{status:409});return {...body,revision:3};}});
 await c.load();c.edit('Мой текст');await c.flush();assert.equal(c.getSnapshot().conflict,true);assert.equal(c.getSnapshot().text,'Мой текст');revision=2;await c.keepMine();assert.equal(c.getSnapshot().saved,true);assert.equal(c.getSnapshot().text,'Мой текст');c.dispose();
});
test('leaving a lesson flushes its edited text but changed account cannot write it',async()=>{
 let current=true,calls=0;const c=make({isCurrent:()=>current,write:async body=>{calls++;return {...body,revision:body.revision+1};}});
 await c.load();c.edit('Сохранить при выходе');c.dispose();await c.flush();assert.equal(calls,1);
 c.edit('Не передать другому аккаунту');current=false;c.dispose();await c.flush();assert.equal(calls,1);
});
test('late initial read cannot overwrite text already typed or saved',async()=>{
 let release,count=0;const c=make({read:async()=>{if(++count===2)await new Promise(r=>release=r);return {revision:0,text:null,request_id:null};}});
 await c.load();const oldRead=c.load();c.edit('Уже ввела текст');await c.flush();release();await oldRead;
 assert.equal(c.getSnapshot().text,'Уже ввела текст');assert.equal(c.getSnapshot().revision,1);c.dispose();
});
test('cleared remote draft restores the latest submitted answer, not an older baseline',async()=>{
 const c=make();await c.load();c.edit('Новый отправленный ответ');await c.flush();c.setInitial('Новый отправленный ответ');await c.clear();
 c.edit('Изменение, от которого отказываюсь');await c.useServer();assert.equal(c.getSnapshot().text,'Новый отправленный ответ');c.dispose();
});
