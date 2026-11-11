import React,{useCallback,useEffect,useRef,useState} from 'react';
import {getApiBaseUrl} from '../../utils/backendUrl';
import {useAuth} from '../../components/AuthContext';

const labels={intro:'Начало урока',theory:'Теория',exercise:'Практика',quiz:'Вопросы теста',challenge:'Задания по дням',numbers:'Личные числа',lines:'Линии квадрата',methods:'Расчёт схем',guide:'Помощь'};
export default function NarrationPanel({lessonId,clipId,section}){
 const {user}=useAuth();const [items,setItems]=useState([]),[error,setError]=useState(''),[busy,setBusy]=useState(false),[selected,setSelected]=useState('');
 const audio=useRef(null);const sequence=useRef(0);
 const path=lessonId?`/narration/lesson/${encodeURIComponent(lessonId)}`:'/narration/project';
 const reload=useCallback(async()=>{
  const request=++sequence.current;setBusy(true);setError('');
  try{
   const response=await fetch(getApiBaseUrl()+path,{headers:{Authorization:`Bearer ${localStorage.getItem('token')}`}});
   if(!response.ok)throw new Error('Не удалось загрузить озвучку. Проверьте доступ к материалу.');
   const data=await response.json();if(!Array.isArray(data.items))throw new Error('Записи пока недоступны.');
   for(const item of data.items)if(item.url){const url=new URL(item.url);if(url.protocol!=='https:'||url.username||url.password||url.search||url.hash||!url.pathname.startsWith('/api/student/narration-media/'))throw new Error('Адрес записи недоступен.');}
   if(request===sequence.current)setItems(data.items);
  }catch(e){if(request===sequence.current)setError(e.message);}finally{if(request===sequence.current)setBusy(false);}
 },[path]);
 useEffect(()=>{setItems([]);setSelected('');void reload();return()=>{sequence.current++;};},[reload,user?.id]);
 useEffect(()=>{const element=audio.current;return()=>element?.pause();},[items,selected,clipId,section]);
 useEffect(()=>{
  const hide=()=>{if(document.hidden)audio.current?.pause();};
  const focus=event=>{if(event.target!==audio.current)audio.current?.pause();};
  document.addEventListener('visibilitychange',hide);document.addEventListener('play',focus,true);
  return()=>{audio.current?.pause();document.removeEventListener('visibilitychange',hide);document.removeEventListener('play',focus,true);};
 },[]);
 const visible=items.filter(item=>(!clipId||item.id===clipId)&&(!section||item.section===section));
 const active=clipId?visible[0]:visible.find(item=>item.id===selected);
 const refreshAudio=async()=>{
  if(active && active.status==='missing'){
   setBusy(true);setError('');
   try{const response=await fetch(`${getApiBaseUrl()}${path}/${encodeURIComponent(active.id)}/access`,{method:'POST',headers:{Authorization:`Bearer ${localStorage.getItem('token')}`,'Content-Type':'application/json'},body:'{}'});if(!response.ok)throw new Error('Не удалось подготовить запись. Попробуйте снова.');}
   catch(e){setError(e.message);setBusy(false);return;}
  }
  await reload();
 };
 return <section className="rounded-2xl border border-emerald-100 bg-[#edf5f0] p-4 space-y-3" aria-label="Аудиоверсия">
  <h3 className="font-semibold text-[#003447]">{clipId?'Слушать объяснение':'Аудиоверсия урока'}</h3>
  {!clipId&&<label className="block text-sm text-slate-700">Фрагмент<select className="block mt-2 w-full rounded-xl border p-3 bg-white" value={selected} onChange={e=>{audio.current?.pause();setSelected(e.target.value);}}><option value="">Выберите материал</option>{visible.map(item=><option key={item.id} value={item.id}>{labels[item.section]||item.section} · {item.title}</option>)}</select></label>}
  {active?.status==='ready'&&active.url?<audio key={active.hash+active.url} ref={audio} controls preload="none" src={active.url} className="w-full" aria-label={active.title} onError={()=>setError('Не удалось загрузить запись. Обновите озвучку и попробуйте снова.')}/>:
   <p className="text-sm text-slate-600">{busy?'Загружаем список…':active?.status==='review'?'Запись проходит проверку произношения.':active?'Запись готовится.':'Выберите фрагмент для прослушивания.'}</p>}
  {active&&<details className="text-sm leading-relaxed text-slate-700"><summary className="cursor-pointer">Текст озвучки</summary><p className="mt-3 whitespace-pre-line">{active.text}</p></details>}
  {error&&<p role="alert" className="text-sm text-red-700">{error}</p>}
  <button type="button" onClick={()=>void refreshAudio()} disabled={busy} className="text-sm underline min-h-11 text-[#003447]">Обновить озвучку</button>
 </section>;
}
