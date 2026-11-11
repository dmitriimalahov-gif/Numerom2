import {createContext,useCallback,useContext,useEffect,useMemo,useRef,useState} from 'react';
import {Text,View} from 'react-native';
import {useSession,backendUrl} from '../../lib/session';
import {useResource} from '../../lib/useResource';
import {Button,Notice,s} from '../ui';
import {AudioTrack} from './AudioTrack';

type Clip={id:string;title:string;text:string;section:string;hash:string;status:string;seconds:number;url?:string;adapted?:boolean;replacement_pending?:boolean};
type State={items:Clip[];loading:boolean;error:string;dropped:boolean;refresh:()=>Promise<unknown>;path:string;guest:boolean};
const Context=createContext<State|null>(null);
/** A new recording replaces bundled audio only after the server verifies it. */
export function AvailableNarration({id,fallback}:{id:string;fallback:React.ReactNode}){
 const context=useContext(Context);
 const ready=context?.items.some(item=>item.id===id&&item.status==='ready'&&!!item.url);
 return ready?<NarrationClip id={id}/>:<>{fallback}</>;
}
function catalog(value:unknown):Clip[]{
 const items=(value as {items?:unknown})?.items;if(!Array.isArray(items))throw new Error('Не удалось загрузить озвучку.');
 return items.filter(item=>item&&typeof item.id==='string'&&typeof item.text==='string').map(item=>{
  if(item.url){const url=new URL(item.url);if(url.protocol!=='https:'||url.origin!==new URL(backendUrl).origin||!url.pathname.startsWith('/api/student/narration-media/'))throw new Error('Адрес записи недоступен.');}
  return item;
 });
}
/** Guests read the shared guide catalog without an account; they never ask the server to prepare audio. */
export const GUEST_GUIDE_PATH='/public/narration/project';
export function NarrationProvider({path,children,guest=false}:{path:string;children:React.ReactNode;guest?:boolean}){
 const {api}=useSession();
 const links=useMemo(()=>new Map<string,{url:string;until:number}>(),[api,path]);
 // A dropped connection or a busy server during polling is temporary; anything else (a foreign record address) is shown.
 const dropped=useRef(false);
 const resource=useResource(useCallback(()=>api.request(path,{auth:!guest}).catch(e=>{const f=e as {status?:number;code?:string};dropped.current=(f?.status??0)>=500||['network','timeout'].includes(f?.code??'');throw e;}).then(value=>{dropped.current=false;return value;}).then(value=>catalog(value).map(item=>{
  if(item.status!=='ready'||!item.url)return item;
  const previous=links.get(item.hash);
  if(previous&&previous.until>Date.now()&&new URL(previous.url).origin===new URL(item.url).origin)return {...item,url:previous.url};
  links.set(item.hash,{url:item.url,until:Date.now()+25*60*1000});return item;
 })),[api,path,links,guest]));
 const waiting=resource.data?.some(item=>item.replacement_pending||['preparing','review','missing'].includes(item.status))||(path.startsWith('/full-reports/')&&(!resource.data?.length||!!resource.error));
 useEffect(()=>{const timer=setInterval(()=>void resource.reload(),waiting?30000:25*60*1000);return ()=>clearInterval(timer);},[resource.reload,waiting]);
 return <Context.Provider value={{items:resource.data||[],loading:resource.loading,error:resource.error||'',dropped:!!resource.error&&dropped.current,refresh:resource.reload,path,guest}}>{children}</Context.Provider>;
}
export function NarrationClip({id,showText=false,fallbackText}:{id:string;showText?:boolean;fallbackText?:string}){
 const context=useContext(Context);const {api}=useSession();const [requestError,setRequestError]=useState(''),[busy,setBusy]=useState(false),[expanded,setExpanded]=useState(false);
 if(!context)return null;
 const item=context.items.find(item=>item.id===id);
 const report=context.path.startsWith('/full-reports/'),reportRetry=item?.status==='review'&&report;
 const refresh=async()=>{setBusy(true);setRequestError('');try{if(reportRetry)await api.request(context.path.replace(/\/narration$/,'/video'),{method:'POST',body:{}});else if(item && item.status!=='ready' && !context.guest)await api.request(`${context.path}/${encodeURIComponent(id)}/access`,{method:'POST',body:{}});await context.refresh();}catch(e){setRequestError(e instanceof Error?e.message:'Не удалось обновить запись.');}finally{setBusy(false);}};
 return <View style={{gap:12}}>
  {item?.status==='ready' && item.url ? <AudioTrack key={item.hash+item.url} trackId={item.hash} source={item.url} seconds={item.seconds} label={item.title}/>:
   <View style={{gap:8}}><Text style={s.small}>{context.loading?'Загружаем озвучку…':reportRetry?'Запись не прошла подготовку. Повтор доступен без новой оплаты.':item?.status==='review'?'Запись проходит проверку произношения.':report?'Озвучка готовится: голос записывает главы вашего разбора. Готовые главы появятся здесь сами. Страницу можно закрыть — когда будет готово всё, придёт письмо.':'Озвучка готовится.'}</Text><Button secondary title={reportRetry?'Повторить подготовку озвучки':'Проверить озвучку'} busy={busy||context.loading} onPress={()=>void refresh()}/></View>}
  {!!requestError && <Notice message={requestError}/>}
  {/* A paid report is polled every 30 s while its voice is recorded; one dropped mobile request is not a failure. */}
  {!!context.error && !requestError && (report&&context.dropped?<Text style={s.small}>Связь ненадолго прервалась — проверим озвучку снова автоматически.</Text>:<Notice message={context.error}/>)}
  {item && showText && <Text selectable style={s.body}>{item.text}</Text>}
  {!item && fallbackText && <Text selectable style={s.body}>{fallbackText}</Text>}
  {item && !showText && item.adapted && <><Button secondary title={expanded?'Скрыть текст озвучки':'Текст озвучки'} onPress={()=>setExpanded(!expanded)}/>{expanded&&<Text selectable style={s.body}>{item.text}</Text>}</>}
 </View>;
}
const sectionLabels:Record<string,string>={schemes:'Авторские схемы',assessment:'Самонаблюдение',vedic:'Периоды планет',comprehensive:'Полный разбор',relationships:'Совместимость пары и группы',tools:'Имя, адрес и автомобиль',intro:'Начало урока',theory:'Теория',exercise:'Практика',quiz:'Вопросы теста',challenge:'Задания по дням',numbers:'Личные числа',lines:'Линии квадрата',methods:'Расчёт схем',guide:'Помощь по разделам'};
export function NarrationLibrary({sections}:{sections?:string[]}){
 const context=useContext(Context);const [selected,setSelected]=useState('');
 if(!context)return null;
 const items=context.items.filter(item=>!sections||sections.includes(item.section));
 return <View style={{gap:14}}><Text accessibilityRole="header" style={s.title}>Аудиоверсия</Text>
  <Text style={s.small}>Выберите фрагмент. Прослушивание не изменяет учебный прогресс.</Text>
  {!!context.error && <Notice message={context.error} action="Повторить" onAction={()=>void context.refresh()}/>}
  {Object.keys(sectionLabels).filter(section=>items.some(item=>item.section===section)).map(section=><View key={section} style={{gap:10}}><Text style={s.label}>{sectionLabels[section]}</Text>{items.filter(item=>item.section===section).map(item=><View key={item.id} style={{gap:12}}><Button secondary title={`${selected===item.id?'−':'+'} ${item.title.length>110?item.title.slice(0,107)+'…':item.title}`} onPress={()=>setSelected(selected===item.id?'':item.id)}/>{selected===item.id&&<NarrationClip key={item.id} id={item.id} showText/>}</View>)}</View>)}
 </View>;
}
