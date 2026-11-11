// A video that keeps playing after its screen is left: it moves into a small floating window at the top
// of the app (and from there into the system picture-in-picture window) and goes back when the screen opens.
// The <video> element itself moves, so playback never restarts.
import {router,type Href} from 'expo-router';
import {holdScreen,releaseScreen} from './wakeLock';
import './nowPlaying.web';

type Docked={id:string;element:HTMLVideoElement;title:string;href:string};
let frame:HTMLDivElement|null=null,slot:HTMLDivElement|null=null,label:HTMLButtonElement|null=null,docked:Docked|null=null,count=0;

type WebKitVideo=HTMLVideoElement&{webkitSupportsPresentationMode?:(mode:string)=>boolean;webkitSetPresentationMode?:(mode:string)=>void};
/** The system «picture in picture» window: Chrome/Android use the standard API, Safari/iOS its own. */
export function canFloat(element:HTMLVideoElement){
 const video=element as WebKitVideo;
 return !!(document.pictureInPictureEnabled&&!element.disablePictureInPicture)||!!video.webkitSupportsPresentationMode?.('picture-in-picture');
}
export async function floatVideo(element:HTMLVideoElement){
 const video=element as WebKitVideo;
 if(element.paused)void element.play().catch(()=>{});
 if(document.pictureInPictureEnabled&&element.requestPictureInPicture){await element.requestPictureInPicture();return;}
 video.webkitSetPresentationMode?.('picture-in-picture');
}

export function createVideo(src:string,name:string){
 const element=document.createElement('video'),tag=`video-${++count}`;
 element.controls=true;element.playsInline=true;element.preload='metadata';element.src=src;
 element.setAttribute('playsinline','');element.setAttribute('webkit-playsinline','');
 // Chrome on Android and Safari move a playing video to the system window when the app is left.
 element.setAttribute('autopictureinpicture','');
 element.setAttribute('aria-label',name);
 Object.assign(element.style,{display:'block',width:'100%',height:'100%',background:'#132f43',objectFit:'contain'});
 element.addEventListener('playing',()=>{
  holdScreen(tag);
  const session=(navigator as Navigator&{mediaSession?:MediaSession}).mediaSession;
  // The video's own controls answer the lock screen; the narration's handlers would steer the wrong player.
  if(session&&typeof MediaMetadata!=='undefined'){
   session.metadata=new MediaMetadata({title:name,artist:'NumerOM'});
   for(const action of ['play','pause','seekbackward','seekforward','stop'] as MediaSessionAction[]){try{session.setActionHandler(action,null);}catch{}}
  }
 });
 element.addEventListener('pause',()=>releaseScreen(tag));
 element.addEventListener('ended',()=>{releaseScreen(tag);if(docked?.element===element)closeDock();});
 return element;
}

/** A new link for the same video (a refreshed signature) keeps the position and the play state. */
export function updateSource(element:HTMLVideoElement,src:string){
 if(element.getAttribute('src')===src)return;
 const at=element.currentTime,playing=!element.paused&&!element.ended;
 element.src=src;
 element.addEventListener('loadedmetadata',()=>{element.currentTime=Math.min(at,element.duration||at);if(playing)void element.play().catch(()=>{});},{once:true});
}

function button(text:string,name:string,onClick:()=>void){
 const node=document.createElement('button');
 node.type='button';node.textContent=text;node.setAttribute('aria-label',name);
 Object.assign(node.style,{minWidth:'40px',minHeight:'36px',padding:'0 10px',border:'0',borderRadius:'10px',background:'rgba(255,255,255,.14)',color:'#fff',font:'600 14px -apple-system, "Helvetica Neue", Helvetica, Arial, sans-serif',cursor:'pointer'});
 node.addEventListener('click',onClick);
 return node;
}
function ensureFrame(){
 if(frame&&slot&&label)return frame;
 frame=document.createElement('div');
 frame.setAttribute('role','region');frame.setAttribute('aria-label','Видео в отдельном окне');
 Object.assign(frame.style,{position:'fixed',top:'calc(env(safe-area-inset-top, 0px) + 74px)',right:'12px',width:'min(58vw, 300px)',zIndex:'1000',borderRadius:'14px',overflow:'hidden',background:'#132f43',boxShadow:'0 12px 32px rgba(16,36,58,.35)',display:'none'});
 slot=document.createElement('div');
 // A tall video is letterboxed so the window never covers half the screen.
 slot.style.aspectRatio='16 / 9';
 const bar=document.createElement('div');
 Object.assign(bar.style,{display:'flex',alignItems:'center',gap:'6px',padding:'6px'});
 // dismissTo goes back to the screen still open underneath, where the video has its place.
 label=button('','',()=>{if(docked)router.dismissTo(docked.href as Href);});
 Object.assign(label.style,{flex:'1',minWidth:'0',textAlign:'left',background:'transparent',overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',fontWeight:'500',fontSize:'13px'});
 bar.append(label);
 const float=button('⧉','Открыть поверх других приложений',()=>{if(docked)void floatVideo(docked.element).catch(()=>{});});
 float.dataset.role='float';
 bar.append(float,button('×','Закрыть видео',closeDock));
 frame.append(slot,bar);
 document.body.appendChild(frame);
 return frame;
}

// Another recording or video started: the floating window is not needed any more.
if(typeof document!=='undefined')document.addEventListener('play',event=>{if(docked&&event.target!==docked.element)closeDock();},true);

export function closeDock(){
 if(!docked)return;
 const {element}=docked;docked=null;
 element.pause();element.remove();
 if(frame)frame.style.display='none';
}

export const videoDock={
 /** The screen opens again: it takes its video back from the floating window. */
 take(id:string){
  if(docked?.id!==id)return null;
  const {element}=docked;docked=null;
  if(frame)frame.style.display='none';
  return element;
 },
 /** The screen is left: a playing video moves into the floating window, a paused one stays put. */
 leave(video:Docked){
  const {element}=video;
  if(element.paused||element.ended)return;
  if(docked&&docked.element!==element)closeDock();
  const node=ensureFrame();
  docked=video;
  slot?.replaceChildren(element);
  if(label){label.textContent=`↩ ${video.title}`;label.setAttribute('aria-label',`Вернуться к экрану: ${video.title}`);}
  const float=node.querySelector<HTMLButtonElement>('[data-role="float"]');
  if(float)float.style.display=canFloat(element)?'':'none';
  node.style.display='block';
 },
 docked:(id:string)=>docked?.id===id,
};
