// Keeps the phone screen on while a recording or video plays (Screen Wake Lock API).
// The browser drops the lock whenever the page is hidden, so it is taken again when the page returns.
const holders=new Set<string>();
let sentinel:{release:()=>Promise<void>;addEventListener:(type:'release',fn:()=>void)=>void}|null=null,pending=false;

async function sync(){
 const lock=(navigator as Navigator&{wakeLock?:{request:(type:'screen')=>Promise<NonNullable<typeof sentinel>>}}).wakeLock;
 const wanted=holders.size>0&&document.visibilityState==='visible';
 if(wanted&&!sentinel&&!pending&&lock){
  pending=true;
  try{const taken=await lock.request('screen');sentinel=taken;taken.addEventListener('release',()=>{if(sentinel===taken)sentinel=null;});}catch{}
  finally{pending=false;}
  if(!holders.size)void sync();
 }else if(!wanted&&sentinel){const held=sentinel;sentinel=null;try{await held.release();}catch{}}
}
if(typeof document!=='undefined')document.addEventListener('visibilitychange',()=>void sync());

export function holdScreen(tag:string){holders.add(tag);void sync();}
export function releaseScreen(tag:string){holders.delete(tag);void sync();}
