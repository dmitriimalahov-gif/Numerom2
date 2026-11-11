import {type CSSProperties,type MutableRefObject,useCallback,useEffect,useLayoutEffect,useRef,useState} from 'react';
import {useFocusEffect,usePathname} from 'expo-router';
import {Button} from '../ui';
import {canFloat,createVideo,floatVideo,updateSource,videoDock} from '../../lib/videoDock.web';

// A new link reloads the video, which resets playbackRate to defaultPlaybackRate.
function speed(node:HTMLVideoElement,rate?:number){if(rate){node.preservesPitch=true;node.defaultPlaybackRate=rate;node.playbackRate=rate;}}

// A video that goes on playing in a floating window when its screen is left, keeps the phone screen on
// while it plays and can open in the system «picture in picture» window over other apps.
export function DockedVideo({source,title,name,style,rate,autoPlay,video,onFailure}:{
 source:string;title:string;name:string;style:CSSProperties;rate?:number;autoPlay?:boolean;
 video?:MutableRefObject<HTMLVideoElement|null>;onFailure?:()=>void;
}){
 // A refreshed signature is the same video.
 const id=source.split('?')[0];
 const host=useRef<HTMLDivElement|null>(null),element=useRef<HTMLVideoElement|null>(null),pathname=usePathname();
 const failure=useRef(onFailure);failure.current=onFailure;
 const latest=useRef({source,title,pathname,rate,autoPlay});latest.current={source,title,pathname,rate,autoPlay};
 const [floating,setFloating]=useState(false);
 const attach=useCallback(()=>{
  const place=host.current;if(!place)return;
  let node=videoDock.take(id)??element.current;const fresh=!node;
  if(!node){node=createVideo(latest.current.source,name);node.addEventListener('error',()=>failure.current?.());}
  element.current=node;if(video)video.current=node;
  speed(node,latest.current.rate);
  if(node.parentElement!==place)place.replaceChildren(node);
  if(fresh&&latest.current.autoPlay)void node.play().catch(()=>{});
  setFloating(canFloat(node));
 },[id,name,video]);
 // Runs before React removes this screen's markup, while the video is still in the page.
 const detach=useCallback(()=>{
  const node=element.current;
  if(node&&host.current?.contains(node))videoDock.leave({id,element:node,title:latest.current.title,href:latest.current.pathname});
 },[id]);
 useLayoutEffect(()=>{attach();return detach;},[attach,detach]);
 useFocusEffect(useCallback(()=>{attach();return detach;},[attach,detach]));
 useEffect(()=>{if(element.current)updateSource(element.current,source);},[source]);
 useEffect(()=>{if(element.current)speed(element.current,rate);},[rate]);
 return <>
  <div ref={host} style={style}/>
  {floating&&<Button secondary title="Смотреть в отдельном окне" onPress={()=>{if(element.current)void floatVideo(element.current).catch(()=>{});}}/>}
 </>;
}
