const {p256}=require('@noble/curves/nist.js');
const originPattern=/^https:\/\/[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$/;
const bytes=text=>Uint8Array.from(text,c=>c.charCodeAt(0));
function verifyEndpoint(value,publicKey,now=Math.floor(Date.now()/1000)){
 try{
  if(value?.v!==1||typeof value.api!=='string'||!originPattern.test(value.api)||
     !Number.isSafeInteger(value.iat)||value.iat<=0||value.iat>now+300||
     typeof value.sig!=='string'||!/^[a-f0-9]{128}$/.test(value.sig))return false;
  return p256.verify(value.sig,bytes(`numerom-config:v1:${value.api}:${value.iat}`),publicKey,{prehash:true,lowS:false});
 }catch{return false;}
}
function createEndpointResolver({bundled,publicKey,configUrl,storage,fetchImpl=(...args)=>fetch(...args),now=Date.now,timeoutMs=5000,onChange=()=>{}}){
 let best=null,initial=null,inFlight=null,lastFetch=-Infinity;
 function accept(value){
  if(!verifyEndpoint(value,publicKey,Math.floor(now()/1000))||best&&value.iat<=best.iat)return false;
  best={v:1,api:value.api,iat:value.iat,sig:value.sig};onChange(best.api);return true;
 }
 accept(bundled);
 function refresh(){
  if(inFlight)return inFlight;
  if(now()-lastFetch<30000)return Promise.resolve(best?.api||'');
  lastFetch=now();
  inFlight=(async()=>{
   const controller=new AbortController();let timer;
   // A separate deadline also covers platforms where fetch abort settles late.
   const deadline=new Promise((_,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('configuration timeout'));},timeoutMs);});
   try{
    const value=await Promise.race([(async()=>{
     const r=await fetchImpl(`${configUrl}?t=${now()}`,{cache:'no-store',redirect:'error',signal:controller.signal});
     if(!r.ok)return null;const text=await r.text();if(text.length>4096)return null;return JSON.parse(text);
    })(),deadline]);
    if(accept(value))try{await storage?.set(JSON.stringify(best));}catch{}
   }catch{}finally{clearTimeout(timer);}
   return best?.api||'';
  })().finally(()=>{inFlight=null;});
  return inFlight;
 }
 function ready(){
  if(!initial)initial=(async()=>{
   try{accept(JSON.parse(await storage?.get()||'null'));}catch{}
   await refresh();return best?.api||'';
  })();
  return initial.then(()=>best?.api||'');
 }
 return {ready,refresh,current:()=>best?.api||'',recover:async previous=>{await refresh();return !!best&&best.api!==previous;}};
}
module.exports={createEndpointResolver,verifyEndpoint};
