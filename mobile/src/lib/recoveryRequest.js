/** A resend never implies that the address belongs to an existing account. */
function createRecoveryRequest({request,now=Date.now,cooldownMs=60000}) {
 let state={busy:false,message:'',error:'',sentTo:'',retryAt:0},active=true;
 const listeners=new Set();
 const emit=patch=>{if(!active)return;state={...state,...patch};listeners.forEach(listener=>listener());};
 return {
  getSnapshot:()=>state,
  subscribe:listener=>{listeners.add(listener);return()=>listeners.delete(listener);},
  remainingSeconds:()=>Math.max(0,Math.ceil((state.retryAt-now())/1000)),
  changeAddress:()=>{if(!state.busy)emit({message:'',error:'',sentTo:''});},
  submit:async email=>{
   if(!active||state.busy||now()<state.retryAt)return;
   const address=email.trim();
   if(address.length>254||!/^\S+@\S+\.\S+$/.test(address)){emit({error:'Введите адрес электронной почты'});return;}
   emit({busy:true,error:''});
   try {
    const result=await request(address);
    if(typeof result?.message!=='string'||!result.message.trim())throw Error('Сервер не подтвердил запрос. Попробуйте ещё раз.');
    emit({message:result.message,sentTo:address,retryAt:now()+cooldownMs});
   }catch(error){
    // A lost response may still have sent a letter. Wait before requesting another.
    const uncertain=!error?.status||error.status===429;
    emit({error:error?.status===503?'Восстановление временно недоступно. Попробуйте позже или обратитесь в поддержку NumerOM.':error?.message||'Не удалось отправить запрос',...(uncertain?{retryAt:now()+cooldownMs}:{})});
   }finally{emit({busy:false});}
  },
  dispose:()=>{active=false;listeners.clear();},
 };
}
module.exports={createRecoveryRequest};
