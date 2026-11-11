/** Autosaved private text; never submits an exercise or awards a learning point. */
function receipt(value,maxLength){
 if(!value||!Number.isInteger(value.revision)||value.revision<0||!(value.text===null||typeof value.text==='string')||
    value.text?.length>maxLength||!(value.request_id===null||typeof value.request_id==='string'))throw Error('Сервер не подтвердил черновик.');
 return value;
}
function createExerciseDraft({read,write,makeId,initial='',isCurrent=()=>true,delay=1800,maxLength=10000,resetOnClear=false}){
 let state={text:initial,revision:0,ready:false,dirty:false,saving:false,saved:false,error:'',conflict:false,pending:null};
 const listeners=new Set();let timer=null,running=null,generation=0,mode='draft';
 const emit=patch=>{state={...state,...patch};listeners.forEach(f=>f());};
 const cancel=()=>{if(timer!==null)clearTimeout(timer);timer=null;};
 async function load({keepMine=false}={}){
  if(running||!isCurrent())return;
  cancel();const requestedRevision=state.revision,startedGeneration=generation;emit({error:''});
  try{
   const row=receipt(await read(),maxLength);if(!isCurrent()||state.revision!==requestedRevision||running)return;
   emit({revision:row.revision,ready:true,pending:null,conflict:false,
    ...(keepMine||generation!==startedGeneration?{dirty:true,saved:false}:{text:row.text??initial,dirty:false,saved:row.text!==null})});
  }catch(e){emit({error:e.message||'Не удалось открыть черновик.'});}
 }
 function flush(){
  cancel();if(running)return running;
  if(!state.ready||state.conflict||!isCurrent())return Promise.resolve(false);
  running=(async()=>{
   while((state.dirty||state.pending)&&isCurrent()){
    const operation=state.pending||{body:{request_id:makeId(),revision:state.revision,text:mode==='clear'?null:state.text},generation,clear:mode==='clear'};
    emit({saving:true,pending:operation,error:''});
    try{
     const row=receipt(await write(operation.body),maxLength);if(!isCurrent())return false;
     if(row.request_id!==operation.body.request_id||row.revision!==operation.body.revision+1||row.text!==operation.body.text)throw Error('Сервер не подтвердил черновик.');
     emit({revision:row.revision,pending:null,dirty:generation!==operation.generation,saved:!operation.clear&&generation===operation.generation,...(operation.clear&&resetOnClear&&generation===operation.generation?{text:initial}:{})});
    }catch(e){
     const rejected=[400,403,404,409,422].includes(e.status);
     emit({error:e.message||'Черновик пока не сохранён.',conflict:e.status===409,...(rejected?{pending:null}:{})});return false;
    }
   }
   return !state.dirty&&!state.pending;
  })().finally(()=>{running=null;emit({saving:false});});
  return running;
 }
 return {getSnapshot:()=>state,subscribe:f=>{listeners.add(f);return()=>listeners.delete(f);},load,flush,
  setInitial:text=>{initial=text;},
  edit:text=>{if(!state.ready||text.length>maxLength)return;generation++;mode='draft';emit({text,dirty:true,saved:false});cancel();if(!state.conflict)timer=setTimeout(()=>void flush(),delay);},
  clear:async()=>{if(!await flush())return false;generation++;mode='clear';emit({dirty:true});return flush();},
  useServer:()=>load(),keepMine:async()=>{await load({keepMine:true});if(!state.conflict)return flush();return false;},
  dispose:()=>{cancel();void flush();},
 };
}
module.exports={createExerciseDraft};
