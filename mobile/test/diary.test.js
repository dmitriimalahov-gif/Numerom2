const {test}=require('node:test'),assert=require('node:assert/strict');
const {diary,challengeId,createDiaryController}=require('../src/lib/diary');
const start={challenge:{id:'c',title:'Практика',duration_days:2,days:[1,2].map(day=>({day,title:`День ${day}`,description:'Описание',tasks:['Наблюдение'],narration_id:`challenge-${day-1}`}))},progress:{id:'p',attempt_id:'attempt',attempt_number:1,revision:0,completed_days:[],daily_notes:[],is_completed:false,points_earned:0,points_per_day:10,bonus_points:50},history:[]};
const clone=v=>JSON.parse(JSON.stringify(v));
const saved=body=>({...clone(start),progress:{...start.progress,revision:body.revision+1,last_request_id:body.request_id,daily_notes:[{day:body.day,note:body.note}],completed_days:body.completed?[body.day]:[],points_earned:body.completed?10:0}});
const make=options=>createDiaryController({read:async()=>clone(start),save:async body=>saved(body),restart:async()=>{},makeId:()=> 'uuid',...options});
test('diary rejects invalid progress and only recognizes a valid lesson challenge',()=>{
 assert.equal(diary(start),start);assert.equal(challengeId({challenge:{id:'c'}}),'c');assert.equal(challengeId({challenge:{id:'../private'}}),null);
 assert.throws(()=>diary({...start,progress:{...start.progress,points_earned:-1}}));
 assert.throws(()=>diary({...start,challenge:{...start.challenge,days:[start.challenge.days[0],start.challenge.days[0]]}}));
});
test('opening and editing is free; blank completion does not submit',async()=>{
 let posts=0;const c=make({save:async body=>{posts++;return saved(body);}});await c.load();await c.save(1,true);assert.equal(posts,0);
 c.edit(1,'Первая заметка');await c.save(1,false);assert.equal(posts,1);assert.deepEqual(c.getSnapshot().data.progress.completed_days,[]);assert.equal(c.getSnapshot().dirty[1],undefined);
});
test('double press and lost response keep one immutable attempt',async()=>{
 let release,first=true,calls=[];const wait=new Promise(resolve=>release=resolve);
 const c=make({save:async body=>{calls.push(body);await wait;if(first){first=false;throw Error('Сеть');}return saved(body);}});await c.load();c.edit(1,'Наблюдение');const a=c.save(1,true),b=c.save(1,true);assert.equal(calls.length,1);release();await Promise.all([a,b]);
 c.edit(1,'Изменение');assert.equal(c.getSnapshot().drafts[1],'Наблюдение');await c.retry();assert.deepEqual(calls[0],calls[1]);assert.equal(c.getSnapshot().pending,null);
});
test('conflict leaves text editable and fresh revision is used after refresh',async()=>{
 let fresh=false,calls=[];const c=make({read:async()=>({...clone(start),progress:{...start.progress,revision:fresh?2:0}}),save:async body=>{calls.push(body);if(!fresh)throw Object.assign(Error('Конфликт'),{status:409});return saved(body);}});
 await c.load();c.edit(1,'Моя запись');await c.save(1,true);assert.equal(c.getSnapshot().pending,null);assert.equal(c.getSnapshot().drafts[1],'Моя запись');fresh=true;await c.load();await c.save(1,true);assert.equal(calls[1].revision,2);assert.equal(calls[1].note,'Моя запись');
});
test('refresh and another saved day never erase unsaved notes',async()=>{
 const c=make();await c.load();c.edit(1,'Первый');c.edit(2,'Второй');await c.save(1,true);assert.equal(c.getSnapshot().drafts[2],'Второй');assert.equal(c.getSnapshot().dirty[2],true);await c.load();assert.equal(c.getSnapshot().drafts[2],'Второй');
});
test('unconfirmed save remains retryable even if a GET sees the committed note',async()=>{
 let result=clone(start);const c=make({read:async()=>result,save:async body=>{result=saved(body);throw Error('Сеть');}});await c.load();c.edit(1,'Запись');await c.save(1,true);await c.load();assert.ok(c.getSnapshot().pending);assert.equal(c.getSnapshot().data.progress.completed_days[0],1);
});
test('remote restart never silently discards a local note',async()=>{
 let restarted=false;const c=make({read:async()=>({...clone(start),progress:{...start.progress,attempt_id:restarted?'new':'attempt'}})});await c.load();c.edit(1,'Не потерять');restarted=true;await c.load();assert.equal(c.getSnapshot().remoteConflict,true);assert.equal(c.getSnapshot().drafts[1],'Не потерять');await c.discardDrafts();assert.equal(c.getSnapshot().data.progress.attempt_id,'new');assert.deepEqual(c.getSnapshot().drafts,{});
});
