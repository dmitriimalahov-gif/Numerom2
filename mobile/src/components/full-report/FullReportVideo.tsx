import {useCallback,useEffect,useRef,useState} from 'react';
import {AppState,Linking,Platform,Text,View} from 'react-native';
import {useSession,backendUrl} from '../../lib/session';
import {Button,Card,Notice,s} from '../ui';
import {FullReportVideoPlayer} from './FullReportVideoPlayer';
import {ReportPreparing} from './ReportPreparing';
import {ReportVideoState,videoState,retainVideo,videoPollDelay,mediaUrl} from './videoState';

function VideoWorkspace({orderId,uid,birthDate}:{orderId:string;uid:string;birthDate?:string}){
 const {api,session}=useSession();
 const [state,setState]=useState<ReportVideoState|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const snapshot=useRef<ReportVideoState|null>(null),alive=useRef(false),sequence=useRef(0),inFlight=useRef(false),timer=useRef<ReturnType<typeof setTimeout>|null>(null),controller=useRef<AbortController|null>(null),reloadRef=useRef<(prepare?:boolean)=>Promise<void>>(async()=>{});
 const currentOwner=useCallback(()=>alive.current&&session.getSnapshot().status==='signedIn'&&session.getSnapshot().user?.id===uid,[session,uid]);
 const reload=useCallback(async(prepare=false)=>{
  if(inFlight.current||!currentOwner())return;
  if(timer.current)clearTimeout(timer.current);inFlight.current=true;
  const version=++sequence.current,token=session.getToken(),requestController=new AbortController();controller.current=requestController;
  const current=()=>currentOwner()&&version===sequence.current&&token===session.getToken();
  setBusy(true);setError('');
  try{
   const raw=await api.request(`/full-reports/${encodeURIComponent(orderId)}/video`,{...(prepare?{method:'POST',body:{}}:{}),signal:requestController.signal});
   if(!current())return;
   const next=retainVideo(snapshot.current,videoState(raw,backendUrl));snapshot.current=next;setState(next);
  }catch(e){if(current())setError(e instanceof Error?e.message:'Не удалось обновить видеоверсию.');}
  finally{if(version===sequence.current)inFlight.current=false;if(current()){setBusy(false);const delay=videoPollDelay(snapshot.current);if(delay!==null)timer.current=setTimeout(()=>{if(AppState.currentState==='active')void reloadRef.current(false);},delay);}}
 },[api,currentOwner,orderId,session]);
 reloadRef.current=reload;
 useEffect(()=>{
  alive.current=true;void reload();
  const listener=AppState.addEventListener('change',value=>{if(value==='active')void reloadRef.current(false);else if(timer.current)clearTimeout(timer.current);});
  return()=>{alive.current=false;sequence.current++;inFlight.current=false;controller.current?.abort();if(timer.current)clearTimeout(timer.current);listener.remove();};
 },[reload]);
 async function download(){
  const token=session.getToken();
  try{
   if(!currentOwner())return;
   if(!snapshot.current?.link_until||snapshot.current.link_until<=Date.now())await reload(true);
   if(!currentOwner()||token!==session.getToken())return;
   if(!snapshot.current?.link_until||snapshot.current.link_until<=Date.now())throw Error('Ссылка на видео обновляется. Нажмите «Скачать MP4» ещё раз.');
   const url=mediaUrl(snapshot.current.download_url,backendUrl);
   if(Platform.OS==='web'){const link=document.createElement('a');link.href=url;link.download='';link.rel='noreferrer';link.referrerPolicy='no-referrer';document.body.appendChild(link);link.click();link.remove();}
   else await Linking.openURL(url);
  }catch(e){if(currentOwner())setError(e instanceof Error?e.message:'Не удалось открыть скачивание видео.');}
 }
 return <Card tinted><Text accessibilityRole="header" style={s.title}>Ваш разбор в видео</Text><Text style={s.body}>Авторские схемы и персональная озвучка в одном MP4. Входит в покупку 6,66 €.</Text>
  {state?.status==='ready'&&state.url?<><FullReportVideoPlayer source={state.url} chapters={state.chapters} onFailure={()=>setError('Не удалось открыть видео. Обновите ссылку и повторите воспроизведение.')}/><Text style={s.small}>{state.seconds?`${Math.ceil(state.seconds/60)} мин`:'MP4'}{state.bytes?` · ${(state.bytes/1048576).toFixed(1)} МБ`:''}</Text><Button title="Скачать MP4" onPress={()=>void download()}/></>:<View style={{gap:10}}>{state&&!['failed','waiting_analysis'].includes(state.status)&&<ReportPreparing birthDate={birthDate}/>}<Text style={s.label}>{state?.status==='waiting_analysis'?'Готовим смысловой разбор':state?.status==='rendering'?'Собираем персональное видео':state?.status==='queued'?'Видео в очереди на подготовку':state?.status==='failed'?(state.stage==='analysis'?'Подготовку смыслового разбора нужно повторить':state.stage==='audio'?'Подготовку озвучки нужно повторить':'Подготовку видео нужно повторить'):'Подготавливаем аудиоглавы для видео'}</Text><Text accessibilityLiveRegion="polite" style={s.body}>{state?.message||(busy?'Проверяем состояние видеоверсии…':'Видео появится после подготовки всех персональных аудиоглав.')}</Text>{state&&state.status!=='waiting_analysis'&&state.stage!=='analysis'&&<Text style={s.small}>Готово аудиоглав: {state.audio_ready} из {state.audio_total}</Text>}{state?.progress!==undefined&&<View style={{gap:5}}><View accessibilityRole="progressbar" accessibilityValue={{min:0,max:100,now:state.progress}} style={{height:8,borderRadius:4,backgroundColor:'#DDE5EE',overflow:'hidden'}}><View style={{height:8,width:`${state.progress}%`,backgroundColor:'#356fa5'}}/></View><Text style={s.small}>{Math.round(state.progress)}%</Text></View>}</View>}
  {!!error&&<Notice message={error}/>}<Button secondary busy={busy} title={state?.status==='ready'?'Обновить ссылку на видео':state?.status==='failed'?(state.stage==='analysis'?'Повторить смысловой разбор':state.stage==='audio'?'Повторить подготовку озвучки':'Повторить подготовку видео'):'Подготовить / проверить видео'} onPress={()=>void reload(true)}/><Text style={s.small}>Дополнительная оплата и баллы не нужны. Можно закрыть страницу и вернуться позже.</Text>
 </Card>;
}
export function FullReportVideo({orderId,birthDate}:{orderId:string;birthDate?:string}){const {user}=useSession();return user?<VideoWorkspace key={`${user.id}:${orderId}`} uid={user.id} orderId={orderId} birthDate={birthDate}/>:null;}
