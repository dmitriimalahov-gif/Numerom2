const {createExerciseDraft}=require('./exerciseDraft');
const {quizPayload,quizResult}=require('./learning');
function parseWork(text,quiz){
 if(!text)return null;
 let w;try{w=JSON.parse(text);}catch{throw Error('Не удалось прочитать сохранённые ответы.');}
 const ids=new Set(quiz.questions.map(q=>q.id));
 if(!w||!/^[a-f\d]{8}-[a-f\d]{4}-4[a-f\d]{3}-[89ab][a-f\d]{3}-[a-f\d]{12}$/i.test(w.submission_id)||!['editing','submitting'].includes(w.stage)||
 !Number.isInteger(w.index)||w.index<0||w.index>=quiz.questions.length||!w.answers||typeof w.answers!=='object'||Array.isArray(w.answers)||
 Object.entries(w.answers).some(([id,value])=>!ids.has(id)||typeof value!=='string'||value.length>4000||
  value&&quiz.questions.find(q=>q.id===id).type!=='text'&&!quiz.questions.find(q=>q.id===id).options.includes(value)))throw Error('Тест изменился. Сохранённый черновик требует проверки.');
 return w;
}
function createQuizWork({read,write,submit,makeId,lessonId,quiz,onSaved=async()=>{},isCurrent=()=>true,delay}){
 const draft=createExerciseDraft({read,write,makeId,isCurrent,delay,maxLength:450000,resetOnClear:true});
 const listeners=new Set();let state={draft:draft.getSnapshot(),work:null,result:null,busy:false,error:'',invalid:false},locked=false;
 const emit=patch=>{state={...state,...patch};listeners.forEach(f=>f());};
 draft.subscribe(()=>{const d=draft.getSnapshot();try{emit({draft:d,work:parseWork(d.text,quiz),invalid:false});}catch(e){emit({draft:d,work:null,invalid:true,error:e.message});}});
 const update=work=>draft.edit(JSON.stringify(work));
 return {getSnapshot:()=>state,subscribe:f=>{listeners.add(f);return()=>listeners.delete(f);},load:()=>draft.load(),flush:()=>draft.flush(),dispose:()=>draft.dispose(),
  answer:(id,value)=>{if(locked||!state.work||state.work.stage!=='editing')return;update({...state.work,answers:{...state.work.answers,[id]:value}});},
  go:index=>{if(!locked&&state.work?.stage==='editing'&&index>=0&&index<quiz.questions.length)update({...state.work,index});},
  start:async()=>{if(locked||!state.draft.ready||state.work?.stage==='submitting')return;emit({error:'',result:null});update({submission_id:makeId(),answers:{},index:0,stage:'editing'});await draft.flush();},
  keepMine:()=>draft.keepMine(),useServer:()=>draft.useServer(),
  submit:async()=>{
   if(locked||!state.work||state.invalid||!isCurrent())return;locked=true;let sent=false;emit({busy:true,error:''});
   try{
    const work=state.work;const body=quizPayload(lessonId,quiz,work.answers,work.submission_id);
    if(work.stage!=='submitting')update({...work,stage:'submitting'});
    if(!await draft.flush())throw Error('Сначала нужно сохранить ответы. Проверьте сообщение черновика.');
    sent=true;const result=quizResult(await submit(body));if(!isCurrent())return;
    if(result.submissionId!==body.submission_id)throw Error('Сервер вернул результат другой попытки.');
    emit({result});await draft.clear();await onSaved();
   }catch(e){
    if(!isCurrent())return;
    if(sent&&[400,422].includes(e.status)&&state.work){update({...state.work,submission_id:makeId(),stage:'editing'});await draft.flush();}
    emit({error:e.message||'Не удалось подтвердить отправку теста.'});
   }
   finally{locked=false;emit({busy:false});}
  },
 };
}
module.exports={parseWork,createQuizWork};
