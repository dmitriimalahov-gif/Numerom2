import {useEffect,useRef,useState,useSyncExternalStore} from 'react';
import {Pressable,Text,View} from 'react-native';
import type {ApiClient} from '@numerom/api-client';
import {Button,Card,Loading,Notice,s} from '../ui';
import {NarrationClip} from '../audio/Narration';
import {createDiaryController} from '../../lib/diary';
import {submissionId} from '../../lib/learning';
import {colors as c} from '../../lib/theme';
import {DiaryNote} from './DiaryNote';

export function LessonDiary({api,lessonId,challengeId,onSaved}:{api:ApiClient;lessonId:string;challengeId:string;onSaved:()=>Promise<void>}){
 const active=useRef(true),savedCallback=useRef(onSaved);savedCallback.current=onSaved;
 const [controller]=useState(()=>{
  const path=`/student/diary/${encodeURIComponent(lessonId)}/${encodeURIComponent(challengeId)}`;
  return createDiaryController({read:()=>api.request(path),save:body=>api.request(path,{method:'POST',body}),restart:body=>api.request(path+'/restart',{method:'POST',body}),onSaved:()=>savedCallback.current(),makeId:submissionId,isCurrent:()=>active.current});
 });
 const state=useSyncExternalStore(controller.subscribe,controller.getSnapshot,controller.getSnapshot);
 const [day,setDay]=useState(1),[history,setHistory]=useState(false),[confirmRestart,setConfirmRestart]=useState(false);
 useEffect(()=>{active.current=true;void controller.load();return()=>{active.current=false;};},[controller]);
 const data=state.data,p=data?.progress,task=data?.challenge.days.find(d=>d.day===day);
 const note=state.drafts[day]??p?.daily_notes.find(n=>n.day===day)?.note??'';
 const completed=p?.completed_days.includes(day),locked=state.busy||!!state.pending;
 return <View style={{gap:18}}><Text accessibilityRole="header" style={s.heading}>Практика по дням</Text>
  {state.loading&&!data&&<Loading/>}
  {!!state.error&&<Notice message={state.error}/>}
  {state.remoteConflict&&<Button secondary title="Удалить мои несохранённые заметки и открыть новую попытку" onPress={()=>void controller.discardDrafts()}/>}
  {state.pending&&!state.busy&&<Notice message={data?.progress_sync_pending?'Заметка сохранена. Прогресс урока ещё синхронизируется.':'Сохранение ещё не подтверждено. Ваша заметка остаётся здесь.'} action="Проверить сохранение" onAction={()=>void controller.retry()}/>}
  {data&&p&&<>
   <Card tinted><Text style={s.title}>{data.challenge.title}</Text>{!!data.challenge.description&&<Text style={s.body}>{data.challenge.description}</Text>}
    <Text style={s.label}>Попытка {p.attempt_number} · выполнено {p.completed_days.length} из {data.challenge.duration_days} дней</Text>
    <Text style={s.body}>За эту попытку начислено {p.points_earned} баллов.</Text><Text style={s.small}>За день: {p.points_per_day}. За завершение: {p.bonus_points}. Повтор сохранения не начисляет награду снова.</Text>
    <NarrationClip id="challenge-intro"/>
   </Card>
   <View style={{flexDirection:'row',flexWrap:'wrap',gap:8}}>{data.challenge.days.map(item=><Pressable key={item.day} accessibilityRole="button" accessibilityLabel={`День ${item.day}${p.completed_days.includes(item.day)?', выполнен':''}`} accessibilityState={{selected:day===item.day}} onPress={()=>setDay(item.day)} style={{minWidth:48,minHeight:48,alignItems:'center',justifyContent:'center',borderRadius:13,backgroundColor:day===item.day?c.navy:c.blue}}><Text style={{color:day===item.day?'#fff':c.navy,fontWeight:'600'}}>{item.day}{p.completed_days.includes(item.day)?' ✓':''}</Text></Pressable>)}</View>
   {task&&<Card><Text style={s.eyebrow}>День {day} · {completed?'выполнен':'практика'}</Text><Text style={s.title}>{task.title}</Text>{!!task.description&&<Text selectable style={s.body}>{task.description}</Text>}
    <NarrationClip key={task.narration_id} id={task.narration_id}/>
    {task.tasks.map((text,index)=><Text selectable key={index} style={s.body}>{index+1}. {text}</Text>)}
    <DiaryNote key={`${p.attempt_id}:${day}`} api={api} path={`/student/diary-drafts/${encodeURIComponent(lessonId)}/${encodeURIComponent(challengeId)}/${p.attempt_id}/${day}`} initial={note} completed={!!completed} locked={locked}
     onEdit={value=>controller.edit(day,value)} onCommit={async(value,complete)=>{controller.edit(day,value);await controller.save(day,complete);const current=controller.getSnapshot();return !current.pending&&current.data?.progress.daily_notes.some(n=>n.day===day&&n.note===value.trim())===true&&(!complete||current.data.progress.completed_days.includes(day));}}/>

   </Card>}
   {p.is_completed&&<Card><Text style={s.title}>Практика завершена</Text><Text style={s.body}>Все дни этой попытки сохранены. Можно вернуться к своим наблюдениям или начать новую практику.</Text>
    {!confirmRestart?<Button secondary title="Повторить практику" disabled={locked} onPress={()=>setConfirmRestart(true)}/>:<><Text style={s.small}>Текущая попытка останется в истории. Новая начнётся с первого дня.</Text><Button title="Начать новую попытку" disabled={locked} onPress={()=>{void controller.restart();setConfirmRestart(false);setDay(1);}}/><Button secondary title="Остаться в этой попытке" onPress={()=>setConfirmRestart(false)}/></>}
   </Card>}
   <Button secondary title={history?'Скрыть прошлые попытки':`Прошлые попытки (${data.history.length})`} onPress={()=>setHistory(!history)}/>
   {history&&<Card>{!data.history.length&&<Text style={s.body}>Предыдущих попыток пока нет.</Text>}{data.history.map((entry,index)=><View key={entry.id||index} style={{gap:8}}><Text style={s.label}>Попытка {entry.attempt_number??'—'} · {entry.is_completed?'завершена':'сохранена'}</Text>{Array.isArray(entry.daily_notes)&&entry.daily_notes.map(row=><Text selectable key={row.day} style={s.body}>День {row.day}: {row.note}</Text>)}</View>)}</Card>}
  </>}
  <Button secondary title="Обновить сохранённый дневник" disabled={state.busy||state.loading} onPress={()=>void controller.load()}/>
 </View>;
}
