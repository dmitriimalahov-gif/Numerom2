/** Native credentials are released only by the OS-protected read. */
function createBiometricVault({plain,protectedStore,flag,available}) {
 let queue=Promise.resolve();
 const serial=fn=>{const next=queue.then(fn,fn);queue=next.catch(()=>{});return next;};
 const locked=()=>Object.assign(Error('Разблокируйте вход с помощью Face ID или отпечатка пальца.'),{code:'biometric_locked'});
 const enabled=async()=>await flag.get()==='enabled';
 return {
  enabled,available,
  get:(unlock=false)=>serial(async()=>{
   if(!await enabled())return plain.get();
   if(!unlock)throw locked();
   let token;try{token=await protectedStore.get();}catch{throw locked();}
   if(!token){await flag.remove();await plain.remove();await protectedStore.remove();return null;}
   return token;
  }),
  set:token=>serial(async()=>{
   if(await enabled()){await protectedStore.set(token);await plain.remove();}
   else await plain.set(token);
  }),
  remove:()=>serial(async()=>{await plain.remove();await protectedStore.remove();await flag.remove();}),
  enable:(token,isCurrent=()=>true)=>serial(async()=>{
   if(!token||!isCurrent())throw Error('Сначала войдите в аккаунт.');
   if(!available())throw Error('Настройте Face ID или отпечаток пальца в настройках устройства.');
   try{
    await protectedStore.set(token);
    if(await protectedStore.get()!==token||!isCurrent())throw Error('Подтверждение входа отменено.');
    // Remove the unprotected copy before publishing the enabled flag.
    await plain.remove();await flag.set('enabled');
   }catch(error){await protectedStore.remove();await flag.remove();throw error;}
  }),
  disable:()=>serial(async()=>{
   if(!await enabled())return;
   const token=await protectedStore.get();
   if(!token)throw Error('Войдите с паролем, чтобы изменить способ входа.');
   try{await plain.set(token);await flag.remove();}
   catch(error){await plain.remove();throw error;}
   await protectedStore.remove();
  }),
 };
}
module.exports={createBiometricVault};
