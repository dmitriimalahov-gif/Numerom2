// Device observation and city lookup share one lifetime. Stopping invalidates
// both pending permission prompts and late HTTP replies.
const validPoint=p=>p&&Number.isFinite(p.latitude)&&Math.abs(p.latitude)<=90&&Number.isFinite(p.longitude)&&Math.abs(p.longitude)<=180;
const coordinates=p=>({latitude:p.latitude,longitude:p.longitude});
function distance(a,b){
 const rad=n=>n*Math.PI/180,lat=rad(b.latitude-a.latitude),lng=rad(b.longitude-a.longitude);
 const h=Math.sin(lat/2)**2+Math.cos(rad(a.latitude))*Math.cos(rad(b.latitude))*Math.sin(lng/2)**2;
 return 6371000*2*Math.asin(Math.sqrt(Math.min(1,h)));
}
function createLocationSelection({locate,watchLocation,resolve,onSelect,isCurrent=()=>true,now=Date.now,setTimer=setTimeout,clearTimer=clearTimeout}){
 let state={busy:false,live:false,error:'',message:'',location:null,accuracy:null,updatedAt:null};
 let epoch=0,stopWatch=null,lastResolved=null,lastLookup=0,latest=null,resolving=false,timer=null,operation=null;
 const listeners=new Set();
 const publish=patch=>{state={...state,...patch};listeners.forEach(fn=>fn());};
 const current=id=>id===epoch&&isCurrent();
 function stop(message=''){
  epoch++;operation?.abort();operation=null;stopWatch?.();stopWatch=null;latest=null;resolving=false;
  if(timer!==null)clearTimer(timer);timer=null;
  publish({busy:false,live:false,message});
 }
 function clear(){stop();lastResolved=null;lastLookup=0;publish({location:null,accuracy:null,updatedAt:null,error:''});}
 function fail(error,id){if(!current(id))return;stop();publish({error:error?.message||'Не удалось определить город. Попробуйте ещё раз или введите его вручную.'});}
 function schedule(id){
  if(timer!==null||!state.live)return;
  timer=setTimer(()=>{timer=null;if(current(id)&&latest)void position(latest,id);},Math.max(1,60000-(now()-lastLookup)));
 }
 function select(result,point,id){
  if(!current(id))return;
  const value={...result,...coordinates(point)};
  publish({location:value,accuracy:Number.isFinite(point.accuracy)?point.accuracy:null,updatedAt:point.timestamp||now(),error:'',message:'',busy:false});
  onSelect(value);
 }
 async function position(point,id){
  if(!current(id))return;
  if(!validPoint(point)){fail(Error('Устройство передало некорректные координаты. Введите город вручную.'),id);return;}
  latest=point;
  // GPS jitter updates the position without repeatedly querying the geocoder.
  if(lastResolved&&distance(lastResolved.point,point)<1000){select(lastResolved.result,point,id);return;}
  if(resolving)return;
  if(lastResolved&&now()-lastLookup<60000){publish({message:'Уточняем город после перемещения…'});schedule(id);return;}
  resolving=true;lastLookup=now();publish({busy:true,error:''});
  try{
   const result=await resolve(coordinates(point));
   if(!current(id))return;
   if(!result||typeof result.city!=='string'||!result.city.trim()||typeof result.timezone!=='string'||!validPoint(result))throw Error('Не удалось определить название города. Введите его вручную.');
   lastResolved={point,result};
   // A fix from another city may have arrived while reverse geocoding was pending.
   if(latest&&distance(point,latest)>=1000){publish({message:'Уточняем город после перемещения…'});return;}
   select(result,latest||point,id);
  }catch(error){fail(error,id);}
  finally{if(current(id)){resolving=false;publish({busy:false});if(latest&&lastResolved&&distance(lastResolved.point,latest)>=1000)schedule(id);}}
 }
 async function start(live){
  stop();lastResolved=null;lastLookup=0;const id=epoch;operation=new AbortController();const signal=operation.signal;
  publish({busy:true,live,error:'',message:''});
  try{
   if(live){
    const remove=await watchLocation(p=>{void position(p,id);},error=>fail(error,id),signal);
    if(!current(id)){remove();return;}stopWatch=remove;
   }else{await position(await locate(signal),id);}
  }catch(error){fail(error,id);}
  finally{if(current(id)&&!live)publish({busy:false});}
 }
 return {getSnapshot:()=>state,subscribe:fn=>{listeners.add(fn);return()=>listeners.delete(fn);},locate:()=>start(false),startLive:()=>start(true),stop,clear};
}
module.exports={createLocationSelection,distance,validPoint};
