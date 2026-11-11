const fail=()=>{throw Error('Не удалось прочитать сохранённый дневник. Обновите данные.');};
const obj=v=>v&&typeof v==='object'&&!Array.isArray(v);
const text=v=>typeof v==='string';
function diary(value){
 const c=value?.challenge,p=value?.progress;
 if(!c||!p||!text(c.id)||!text(c.title)||!Array.isArray(c.days)||!Number.isInteger(c.duration_days)||c.duration_days<1||c.duration_days>90||c.days.length!==c.duration_days||
  !c.days.every(d=>d&&Number.isInteger(d.day)&&d.day>=1&&d.day<=c.duration_days&&text(d.title)&&text(d.description)&&text(d.narration_id)&&Array.isArray(d.tasks)&&d.tasks.every(text))||new Set(c.days.map(d=>d.day)).size!==c.duration_days||
  !text(p.attempt_id)||!Number.isInteger(p.revision)||p.revision<0||!Number.isInteger(p.attempt_number)||p.attempt_number<1||
  !Array.isArray(p.completed_days)||!p.completed_days.every(d=>Number.isInteger(d)&&d>=1&&d<=c.duration_days)||
  !Array.isArray(p.daily_notes)||!p.daily_notes.every(d=>d&&Number.isInteger(d.day)&&text(d.note))||
  !['points_earned','points_per_day','bonus_points'].every(k=>Number.isInteger(p[k])&&p[k]>=0)||typeof p.is_completed!=='boolean'||!Array.isArray(value.history))fail();
 return value;
}
function challengeId(lesson){const c=lesson.challenge || (obj(lesson.content)?lesson.content.challenge:null);return obj(c)&&typeof c.id==='string'&&/^[A-Za-z0-9_-]{1,128}$/.test(c.id)?c.id:null;}
function createDiaryController({read,save,restart,onSaved=async()=>{},makeId,isCurrent=()=>true}){
 let state={data:null,drafts:{},dirty:{},pending:null,busy:false,loading:false,error:'',remoteConflict:false};let locked=false,epoch=0;
 const listeners=new Set();const publish=patch=>{if(!isCurrent())return;state={...state,...patch};listeners.forEach(f=>f());};
 function accept(data,submitted){
  const reset=submitted?.restart || state.data&&state.data.progress.attempt_id!==data.progress.attempt_id;
  // Loading a remotely restarted attempt must not silently discard local notes.
  if(reset&&!submitted?.restart&&Object.values(state.dirty).some(Boolean)){
   publish({remoteConflict:true,error:'Начата другая попытка. Скопируйте несохранённые заметки перед обновлением дневника.'});return;
  }
  const drafts=reset?{}:{...state.drafts},dirty=reset?{}:{...state.dirty};
  for(const note of data.progress.daily_notes){if(!dirty[note.day]||submitted?.body.day===note.day){drafts[note.day]=note.note;delete dirty[note.day];}}
  if(submitted&&!submitted.restart)delete dirty[submitted.body.day];
  publish({data,drafts,dirty,remoteConflict:false,pending:submitted?(data.progress_sync_pending?submitted:null):state.pending});
 }
 async function load(){
  const current=++epoch;publish({loading:true,error:''});
  try{const data=diary(await read());if(current===epoch&&isCurrent())accept(data,null);}
  catch(e){if(current===epoch)publish({error:e.message||'Не удалось загрузить дневник.'});}
  finally{if(current===epoch)publish({loading:false});}
 }
 async function send(attempt){
  if(locked||!isCurrent())return;locked=true;epoch++;publish({busy:true,loading:false,error:'',pending:attempt});
  try{
   const data=diary(await (attempt.restart?restart:save)(attempt.body));
   const expected=attempt.restart?attempt.body.request_id:attempt.body.attempt_id;
   if(data.progress.attempt_id!==expected||data.progress.revision<=attempt.body.revision)fail();
   if(!isCurrent())return;
   accept(data,attempt);await onSaved();
  }catch(e){publish({error:e.message||'Не удалось подтвердить сохранение.',...([400,403,404,409,422].includes(e.status)?{pending:null}:{})});}
  finally{locked=false;publish({busy:false});}
 }
 return {getSnapshot:()=>state,subscribe:f=>{listeners.add(f);return()=>listeners.delete(f);},load,
  discardDrafts:async()=>{if(locked||state.pending)return;publish({dirty:{},drafts:{},remoteConflict:false});await load();},
  edit:(day,note)=>{if(!locked&&!state.pending)publish({drafts:{...state.drafts,[day]:note},dirty:{...state.dirty,[day]:true}});},
  retry:()=>state.pending?send(state.pending):Promise.resolve(),
  save:async(day,completed)=>{
   if(locked||state.pending||!state.data)return;
   if(!state.data.challenge.days.some(d=>d.day===day))return;
   const note=(state.drafts[day]??state.data.progress.daily_notes.find(n=>n.day===day)?.note??'').trim();
   if(note.length>4000||completed&&!note){publish({error:'Добавьте наблюдение о выполненном задании (до 4000 символов).'});return;}
   await send({restart:false,body:{request_id:makeId(),attempt_id:state.data.progress.attempt_id,revision:state.data.progress.revision,day,note,completed}});
  },
  restart:async()=>{
   if(locked||state.pending||!state.data?.progress.is_completed)return;
   if(Object.values(state.dirty).some(Boolean)){publish({error:'Сохраните заметки перед началом новой практики.'});return;}
   await send({restart:true,body:{request_id:makeId(),attempt_id:state.data.progress.attempt_id,revision:state.data.progress.revision}});
  },
 };
}
module.exports={diary,challengeId,createDiaryController};
