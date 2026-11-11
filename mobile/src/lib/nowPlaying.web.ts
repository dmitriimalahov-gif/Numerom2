// One narration for the whole web app: it keeps playing while the listener moves to another screen,
// locks the phone or switches apps, shows on the lock screen and keeps the screen on while it plays.
import {getPlaybackRate,subscribePlaybackRate} from './playbackRate';
import {holdScreen,releaseScreen} from './wakeLock';

export type NowPlaying={id:string;title:string;href:string;playing:boolean;busy:boolean;ended:boolean;current:number;duration:number;error:string};
type Track={id:string;source:string;title:string;href:string;seconds:number};

let audio:HTMLAudioElement|null=null,state:NowPlaying|null=null,loading:ReturnType<typeof setTimeout>|null=null,request=0;
const listeners=new Set<()=>void>(),onScreen=new Map<string,number>();
const notify=()=>listeners.forEach(listener=>listener());
const emit=(patch:Partial<NowPlaying>)=>{if(state)state={...state,...patch};notify();};
const STALLED='Запись долго загружается. Проверьте соединение и нажмите «Повторить».';
const FAILED='Запись не загрузилась. Проверьте соединение и нажмите «Повторить».';

// Only one sound at a time across the app: any audio or video that starts pauses the others.
if(typeof document!=='undefined')document.addEventListener('play',event=>{
 for(const media of document.querySelectorAll('audio,video'))if(media!==event.target)(media as HTMLMediaElement).pause();
},true);

function settle(){if(loading){clearTimeout(loading);loading=null;}}
function element(){
 if(audio)return audio;
 const player=audio=document.createElement('audio');
 player.preload='none';player.hidden=true;player.setAttribute('playsinline','');
 document.body.appendChild(player);
 player.addEventListener('playing',()=>{settle();emit({playing:true,busy:false,ended:false,error:''});holdScreen('narration');});
 player.addEventListener('pause',()=>{settle();emit({playing:false,busy:false});releaseScreen('narration');});
 player.addEventListener('waiting',()=>{if(!player.paused)emit({busy:true});});
 player.addEventListener('timeupdate',()=>emit({current:player.currentTime||0}));
 player.addEventListener('durationchange',()=>{if(player.duration&&Number.isFinite(player.duration))emit({duration:player.duration});});
 player.addEventListener('ended',()=>{settle();emit({playing:false,busy:false,ended:true});releaseScreen('narration');});
 player.addEventListener('error',()=>{if(player.getAttribute('src')){settle();emit({playing:false,busy:false,error:FAILED});releaseScreen('narration');}});
 return player;
}

function lockScreenControls(title:string){
 const session=(navigator as Navigator&{mediaSession?:MediaSession}).mediaSession;
 if(!session||typeof MediaMetadata==='undefined')return;
 session.metadata=new MediaMetadata({title,artist:'NumerOM',album:'Озвучка разбора'});
 const actions:[MediaSessionAction,MediaSessionActionHandler][]=[
  ['play',()=>{if(state)void nowPlaying.resume();}],['pause',()=>nowPlaying.pause()],
  ['seekbackward',()=>{if(audio)nowPlaying.seek(Math.max(0,audio.currentTime-15));}],
  ['seekforward',()=>{if(audio)nowPlaying.seek(Math.min(audio.duration||Infinity,audio.currentTime+15));}],
  ['stop',()=>nowPlaying.close()]];
 for(const [action,handler] of actions){try{session.setActionHandler(action,handler);}catch{}}
}

subscribePlaybackRate(rate=>{if(audio){audio.preservesPitch=true;audio.playbackRate=rate;}});

export const nowPlaying={
 subscribe(listener:()=>void){listeners.add(listener);return()=>{listeners.delete(listener);};},
 get:()=>state,
 /** A screen that shows this recording's own controls; the mini player stays hidden meanwhile. */
 show(id:string){
  onScreen.set(id,(onScreen.get(id)||0)+1);notify();
  return()=>{const left=(onScreen.get(id)||1)-1;if(left)onScreen.set(id,left);else onScreen.delete(id);notify();};
 },
 visible:(id:string)=>onScreen.has(id),
 async play(track:Track){
  const player=element();
  if(!state||state.id!==track.id||state.error){
   player.src=track.source;
   state={id:track.id,title:track.title,href:track.href,playing:false,busy:true,ended:false,current:state?.id===track.id?state.current:0,duration:track.seconds,error:''};
   if(state.current)player.currentTime=state.current;
   notify();
  }else emit({busy:true,error:'',href:track.href});
  lockScreenControls(track.title);
  return start(player);
 },
 resume(){return audio&&state?start(audio):Promise.resolve();},
 pause(){request++;settle();audio?.pause();emit({playing:false,busy:false});},
 seek(seconds:number){if(audio){audio.currentTime=seconds;emit({current:seconds,ended:false});}},
 close(){
  request++;settle();
  if(audio){audio.pause();audio.removeAttribute('src');audio.load();}
  state=null;releaseScreen('narration');
  notify();
 },
};

async function start(player:HTMLAudioElement){
 const id=++request;
 if(player.ended)player.currentTime=0;
 player.preservesPitch=true;player.playbackRate=getPlaybackRate();
 settle();emit({busy:true,ended:false,error:''});
 loading=setTimeout(()=>{if(id===request&&state?.busy){request++;player.pause();emit({busy:false,error:STALLED});}},15000);
 try{await player.play();}catch{if(id===request){settle();emit({busy:false,playing:false,error:'Не удалось включить запись. Проверьте соединение и нажмите «Повторить».'});}}
}
