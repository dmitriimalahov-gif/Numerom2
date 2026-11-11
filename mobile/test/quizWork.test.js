const test=require('node:test'),assert=require('node:assert/strict');
const {createQuizWork}=require('../src/lib/quizWork');
const crypto=require('node:crypto');
const quiz={id:'q',supported:true,questions:[{id:'one',type:'multiple_choice',options:['A','B']},{id:'two',type:'text',options:[]}]};
function storage(){let row={text:null,revision:0,request_id:null};return {read:async()=>({...row}),write:async body=>{row={...body,revision:body.revision+1};return row;}};}
function make(store,extra={}){return createQuizWork({...store,makeId:()=>crypto.randomUUID(),lessonId:'l',quiz,delay:60000,submit:async body=>({attempt_id:'a',score:100,passed:true,submission_id:body.submission_id}),...extra});}
test('restores answered questions and current position without submitting',async()=>{
 const store=storage();let submissions=0;const c=make(store,{submit:async()=>{submissions++;}});await c.load();await c.start();c.answer('one','B');c.go(1);c.answer('two','Мой ответ');await c.flush();c.dispose();
 const reopened=make(store);await reopened.load();assert.equal(reopened.getSnapshot().work.index,1);assert.deepEqual(reopened.getSnapshot().work.answers,{one:'B',two:'Мой ответ'});assert.equal(submissions,0);reopened.dispose();
});
test('lost final reply survives reload with identical immutable answers and UUID',async()=>{
 const store=storage(),bodies=[];const c=make(store,{submit:async body=>{bodies.push(body);throw Error('Lost reply');}});
 await c.load();await c.start();c.answer('one','B');c.go(1);c.answer('two','Текст');await c.submit();assert.equal(c.getSnapshot().work.stage,'submitting');c.answer('two','Нельзя изменить');assert.equal(c.getSnapshot().work.answers.two,'Текст');c.dispose();
 const next=make(store,{submit:async body=>{bodies.push(body);return {attempt_id:'a',score:100,passed:true,submission_id:body.submission_id};}});await next.load();await next.submit();assert.deepEqual(bodies[0],bodies[1]);assert.equal(next.getSnapshot().work,null);assert.equal(next.getSnapshot().result.score,100);next.dispose();
});
test('saving failure never sends an unpersisted final attempt',async()=>{
 let writes=0,submits=0;const store=storage();const c=make({...store,write:async body=>{if(++writes>1)throw Error('offline');return store.write(body);}},{submit:async()=>{submits++;}});
 await c.load();await c.start();c.answer('one','B');c.answer('two','text');await c.submit();assert.equal(submits,0);assert.ok(c.getSnapshot().error);c.dispose();
});
test('a definite validation rejection permits correction under a new attempt id',async()=>{
 const store=storage();let old;const c=make(store,{submit:async body=>{old=body.submission_id;throw Object.assign(Error('Вопрос изменился'),{status:422});}});
 await c.load();await c.start();c.answer('one','B');c.answer('two','Текст');await c.submit();
 assert.equal(c.getSnapshot().work.stage,'editing');assert.notEqual(c.getSnapshot().work.submission_id,old);c.answer('two','Исправленный ответ');assert.equal(c.getSnapshot().work.answers.two,'Исправленный ответ');c.dispose();
});
