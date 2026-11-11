import React, { useCallback, useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import type { ApiClient, Lesson } from '@numerom/api-client';
import { Button, Card, Field, Loading, Notice, s } from '../ui';
import { colors } from '../../lib/theme';
import { useResource } from '../../lib/useResource';
import {NarrationClip} from '../audio/Narration';
import {ExerciseAttachments,useExerciseAttachments} from './ExerciseAttachments';
import {createExerciseDraft} from '../../lib/exerciseDraft';
import {useSession} from '../../lib/session';
import {useMaterialAccess} from '../../lib/useMaterialAccess';
import { Exercise, ExerciseResponse, exercisePayload, exerciseResponses, lessonFiles, singleFlight, submissionId } from '../../lib/learning';

const message = (error:unknown) => error instanceof Error ? error.message : 'Не удалось выполнить запрос. Попробуйте ещё раз.';
const pathId = encodeURIComponent;
export function Choices({label, options, value, onChange, disabled = false}: {label:string; options:string[]; value:string; onChange:(value:string)=>void; disabled?:boolean}) {
 return <View accessibilityRole="radiogroup" accessibilityLabel={label} style={{gap:10}}>{options.map((option,index) => <Pressable key={`${index}:${option}`} accessibilityRole="radio" accessibilityLabel={option} accessibilityState={{checked:value===option, disabled}} disabled={disabled} onPress={()=>onChange(option)} style={[styles.choice, value===option && styles.selected, disabled && {opacity:.65}]}>
  <View style={[styles.radio, value===option && {borderColor:colors.navy}]}>{value===option && <View style={styles.dot}/>}</View><Text style={[s.body,{flex:1,color:colors.ink}]}>{option}</Text>
 </Pressable>)}</View>;
}
function ExerciseEditor({api,lessonId,exercise,saved,onSaved}: {api:ApiClient;lessonId:string;exercise:Exercise;saved?:ExerciseResponse;onSaved:()=>Promise<void>}) {
 const {session,user}=useSession();
 const attachments=useExerciseAttachments(api,lessonId,exercise.id);
 const [draftController]=useState(()=>{
  const path=`/student/exercise-drafts/${pathId(lessonId)}/${pathId(exercise.id)}`,owner=user?.id;
  return createExerciseDraft({read:()=>api.request(path),write:body=>api.request(path,{method:'POST',body}),makeId:submissionId,initial:saved?.text||'',isCurrent:()=>session.getSnapshot().user?.id===owner});
 });
 const draftState=useSyncExternalStore(draftController.subscribe,draftController.getSnapshot,draftController.getSnapshot);
 const draft=draftState.text;
 const [confirmed,setConfirmed]=useState(saved);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState('');
 const run=useRef(singleFlight()).current;
 useEffect(()=>{setConfirmed(saved);draftController.setInitial(saved?.text||'');},[saved,draftController]);
 useEffect(()=>{void draftController.load();return()=>draftController.dispose();},[draftController]);
 const change=(value:string)=>{draftController.edit(value);setError('');};
 const save=()=>run(async()=>{
  setBusy(true);setError('');
  try {
   if(!await draftController.flush())throw new Error('Сначала сохраните черновик или разрешите конфликт версий.');
   if(!attachments.ready||attachments.busy)throw new Error('Дождитесь загрузки вложений.');
   const body={...exercisePayload(lessonId,exercise,draft),attachment_ids:attachments.selected};
   const result=await api.request<{response_id:string}>('/student/exercise-response',{method:'POST',body});
   if(!result?.response_id)throw new Error('Сервер не подтвердил сохранение ответа. Повторите отправку.');
   attachments.saved();
   setConfirmed({attachments:body.attachment_ids,id:result.response_id,text:body.response_text,reviewed:false,comment:'',submittedAt:''});
   draftController.setInitial(body.response_text);
   await draftController.clear();
   await onSaved();
  } catch(e){setError(message(e));} finally {setBusy(false);}
 });
 const changed=draft.trim()!==confirmed?.text || [...attachments.selected].sort().join(',')!==[...(confirmed?.attachments||[])].sort().join(',');
 return <Card><Text accessibilityRole="header" style={s.title}>{exercise.title}</Text>
  <NarrationClip id={`exercise-${exercise.id}`}/>
  {!!exercise.description && <Text selectable style={s.body}>{exercise.description}</Text>}
  {!!exercise.instructions && <Text selectable style={s.body}>{exercise.instructions}</Text>}
  {confirmed && <View accessibilityLiveRegion="polite" style={styles.receipt}><Text style={[s.label,{color:colors.green}]}>{confirmed.reviewed?'Проверено преподавателем':'Ответ сохранён. Ожидает проверки.'}</Text>{!!confirmed.comment && <Text selectable style={s.body}>{confirmed.comment}</Text>}</View>}
  {!draftState.ready&&<Loading/>}
  {exercise.type==='multiple_choice' && exercise.options.length ? <Choices label={`Ответ: ${exercise.title}`} options={exercise.options} value={draft} onChange={change} disabled={busy||!draftState.ready}/> : <Field label="Ваш ответ" value={draft} onChangeText={change} onBlur={()=>void draftController.flush()} multiline maxLength={10000} editable={!busy&&draftState.ready} textAlignVertical="top" style={[s.input,{minHeight:130}]}/>}
  <Text accessibilityLiveRegion="polite" style={s.small}>{draftState.saving?'Сохраняем черновик…':draftState.saved?'Черновик сохранён в вашем аккаунте. Преподавателю ещё не отправлен.':draftState.dirty?'Изменения пока не сохранены.':changed?'Черновик сохраняется автоматически.':'Отправленный ответ сохранён.'}</Text>
  {!!draftState.error&&<Notice message={draftState.error} action={draftState.ready?'Повторить сохранение':'Открыть черновик'} onAction={()=>void (draftState.ready?draftController.flush():draftController.load())}/>}
  {draftState.conflict&&<View style={{gap:10}}><Text style={s.small}>Сохраните свой текст или загрузите запись с другого устройства.</Text><Button secondary title="Сохранить мой текст вместо другой версии" onPress={()=>void draftController.keepMine()}/><Button secondary title="Заменить мой текст сохранённой версией" onPress={()=>void draftController.useServer()}/></View>}
  <ExerciseAttachments state={attachments} disabled={busy}/>
  {!!error && <Notice message={error}/>}
  <Button title={confirmed?'Сохранить изменения':'Отправить преподавателю'} onPress={()=>void save()} busy={busy} disabled={!draft.trim() || !changed || !draftState.ready || draftState.conflict || !attachments.ready || attachments.busy}/>
 </Card>;
}
export function LessonExercises({api,lessonId,exercises,onSaved}: {api:ApiClient;lessonId:string;exercises:Exercise[];onSaved:()=>Promise<void>}) {
 const responses=useResource(useCallback(()=>api.request(`/student/exercise-responses/${pathId(lessonId)}`).then(exerciseResponses),[api,lessonId]));
 const refresh=async()=>{await Promise.all([responses.reload(),onSaved()]);};
 return <View style={{gap:18}}><Text accessibilityRole="header" style={s.heading}>Практика</Text>
  {responses.loading && !responses.data && <Loading/>}
  {!!responses.error && <Notice message={responses.error} action="Обновить ответы" onAction={()=>void responses.reload()}/>}
  {responses.data && exercises.map(exercise=><ExerciseEditor key={exercise.id} api={api} lessonId={lessonId} exercise={exercise} saved={responses.data?.[exercise.id]} onSaved={refresh}/>)}
 </View>;
}
export function LessonMaterials({api,lesson,studyAction}: {api:ApiClient;lesson:Lesson;studyAction?:React.ReactNode}) {
 const files=useResource(useCallback(()=>api.request(`/student/lesson-files/${pathId(lesson.id)}`).then(lessonFiles),[api,lesson.id]));
 const {opening,error,open:openMaterial}=useMaterialAccess();
 const external=typeof lesson.video_url==='string' && lesson.video_url.trim() ? lesson.video_url : null;
 const bunny=lesson.video_platform==='bunny';
 const open=(fileId?:string)=>openMaterial(fileId || 'video',async signal=>{
   if(fileId){const response=await api.request<{url:string}>(`/student/lesson-files/${pathId(lesson.id)}/${pathId(fileId)}/access`,{signal});return response.url;}
   if(bunny){const response=await api.request<{url:string}>(`/student/lesson-video/${pathId(lesson.id)}/access`,{signal});return response.url;}
   return external || '';
 });
 return <Card><Text accessibilityRole="header" style={s.title}>Видео и материалы</Text>
  <Text style={s.small}>Материал откроется в браузере или подходящем приложении на устройстве.</Text>
  {(external || bunny) && <Button title="Открыть видео урока" onPress={()=>void open()} busy={opening==='video'} disabled={opening!==null}/>}
  {files.loading && !files.data && <Loading/>}
  {!!files.error && <Notice message={files.error} action="Обновить материалы" onAction={()=>void files.reload()}/>}
  {files.data?.map(file=><View key={file.id} style={{gap:10}}><Text style={s.label}>{file.name}</Text><Text style={s.small}>{file.extension || file.type || 'Файл'}{file.size!==null ? ` · ${(file.size/1024/1024).toLocaleString('ru-RU',{maximumFractionDigits:1})} МБ` : ''}</Text><Button title={file.type.startsWith('video/') || file.type==='video'?'Открыть видео':'Открыть материал'} onPress={()=>void open(file.id)} busy={opening===file.id} disabled={opening!==null} secondary/></View>)}
  {!files.loading && !files.error && files.data?.length===0 && !external && !bunny && <Text style={s.body}>К этому уроку пока не прикреплены файлы.</Text>}
  {((files.data?.length || 0)>0 || external || bunny) && studyAction}
  {!!error && <Notice message={error}/>}
 </Card>;
}
const styles=StyleSheet.create({
 choice:{minHeight:52,padding:14,borderRadius:14,borderWidth:1,borderColor:colors.line,flexDirection:'row',alignItems:'center',gap:12},selected:{backgroundColor:colors.blue,borderColor:colors.accent},
 radio:{width:21,height:21,borderRadius:11,borderWidth:1.5,borderColor:colors.muted,alignItems:'center',justifyContent:'center'},dot:{width:11,height:11,borderRadius:6,backgroundColor:colors.navy},receipt:{padding:16,gap:8,borderRadius:14,backgroundColor:'#EDF6F0'},
});
