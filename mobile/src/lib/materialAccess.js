/** Only the screen and account that requested a material may launch it. */
function createMaterialAccess({openUrl,isCurrent=()=>true,validateUrl=value=>value}) {
 let state={opening:null,error:''},generation=0,pending=null;
 const listeners=new Set();
 const emit=patch=>{state={...state,...patch};listeners.forEach(listener=>listener());};
 return {
  getSnapshot:()=>state,
  subscribe:listener=>{listeners.add(listener);return()=>listeners.delete(listener);},
  isOpening:()=>pending!==null,
  cancel:()=>{++generation;pending?.abort();pending=null;emit({opening:null,error:''});},
  open:async(key,resolve)=>{
   if(pending||!isCurrent())return;
   const version=++generation,controller=new AbortController();pending=controller;
   const current=()=>version===generation&&!controller.signal.aborted&&isCurrent();
   emit({opening:key,error:''});
   try {
    const url=await resolve(controller.signal);
    if(!current())return;
    await openUrl(validateUrl(url));
   }catch(error){if(current())emit({error:error?.message||'Не удалось открыть материал. Попробуйте ещё раз.'});}
   finally{if(version===generation){pending=null;emit({opening:null});}}
  },
 };
}
module.exports={createMaterialAccess};
