import { useCallback, useMemo, useRef, useState } from 'react';
import { Text, View } from 'react-native';
import { Redirect, useLocalSearchParams } from 'expo-router';
import { Button, Card, Heading, Loading, Notice, Screen, s } from '../../components/ui';
import { LessonExercises, LessonMaterials } from '../../components/learning/LessonActivities';
import { useSession } from '../../lib/session';
import { useResource } from '../../lib/useResource';
import { lessonTextBlocks } from '../../lib/lessonContent';
import { lessonExercises, lessonProgress, lessonQuiz, singleFlight } from '../../lib/learning';
import type { ApiClient, Lesson } from '@numerom/api-client';
import {LessonDiary} from '../../components/learning/LessonDiary';
import {ResumableQuiz} from '../../components/learning/ResumableQuiz';
import {challengeId} from '../../lib/diary';
import {NarrationProvider,NarrationClip,NarrationLibrary} from '../../components/audio/Narration';

function LessonBody({api,lesson}: {api:ApiClient;lesson:Lesson}) {
 const {session}=useSession();
 const [balanceError,setBalanceError]=useState('');
 const refreshBalance=useCallback(async()=>{setBalanceError('');try{await session.refresh();}catch{setBalanceError('Изменения сохранены. Не удалось обновить баланс.');}},[session]);
 const progress=useResource(useCallback(()=>api.request(`/student/lesson-progress/${encodeURIComponent(lesson.id)}`).then(lessonProgress),[api,lesson.id]));
 const refreshLearning=useCallback(async()=>{await Promise.all([progress.reload(),refreshBalance()]);},[progress.reload,refreshBalance]);
 const [marking,setMarking]=useState(false),[markError,setMarkError]=useState('');
 const run=useRef(singleFlight()).current;
 const markTheory=()=>run(async()=>{setMarking(true);setMarkError('');try{const receipt=lessonProgress(await api.request(`/student/lesson-progress/${encodeURIComponent(lesson.id)}/theory`,{method:'POST',body:{}}));if(!receipt.theoryRead)throw new Error('Сервер не подтвердил отметку чтения. Попробуйте ещё раз.');await refreshLearning();}catch(error){setMarkError(error instanceof Error?error.message:'Не удалось сохранить отметку. Повторите попытку.');}finally{setMarking(false);}});
 const exercises=useMemo(()=>lessonExercises(lesson),[lesson]);
 const quiz=useMemo(()=>lessonQuiz(lesson),[lesson]);
 const theory=useMemo(()=>lessonTextBlocks(lesson),[lesson]);
 const challenge=challengeId(lesson);
 const studyAction=<View style={{gap:12}}>{progress.data?.theoryRead?<Text accessibilityLiveRegion="polite" style={s.label}>Материал отмечен как изученный.</Text>:<Button title={theory.length?'Теория прочитана':'Материалы изучены'} onPress={()=>void markTheory()} busy={marking} disabled={!progress.data || !!progress.error}/>}<Text style={s.small}>Отметка сохраняется в вашем учебном прогрессе.</Text>{!!markError && <Notice message={markError}/>}</View>;
 return <NarrationProvider path={`/narration/lesson/${encodeURIComponent(lesson.id)}`}>
  <Heading eyebrow={`Уровень ${lesson.level || 1}`} title={lesson.title} subtitle={lesson.description}/>
  <Card tinted><Text accessibilityRole="header" style={s.title}>Ваш прогресс</Text>{progress.loading && !progress.data && <Loading/>}{progress.error && <Notice message={progress.error} action="Обновить прогресс" onAction={()=>void progress.reload()}/>}
   {progress.data && <><Text accessibilityRole="progressbar" accessibilityValue={{min:0,max:100,now:progress.data.percentage,text:`${progress.data.percentage}%`}} style={s.heading}>{progress.data.percentage}%</Text><Text style={s.body}>{progress.data.completed?'Урок завершён':'Обучение продолжается'}</Text><Text style={s.small}>Сохранено на сервере{progress.data.exercisesCompleted!==null ? ` · Упражнений: ${progress.data.exercisesCompleted}` : ''}{progress.data.quizPassed?' · Тест пройден':''}</Text></>}
   {!!balanceError && <Notice message={balanceError} action="Обновить баланс" onAction={()=>void refreshBalance()}/>}
  </Card>
  {theory.length>0 ? <View style={{gap:18}}><Text accessibilityRole="header" style={s.heading}>Теория</Text>{theory.map((block,index)=><Card key={index}>{!!block.title && <Text accessibilityRole="header" style={s.title}>{block.title}</Text>}<NarrationClip id={`theory-${index}`}/><Text selectable style={s.body}>{block.text}</Text></Card>)}</View> : <Card><Text style={s.body}>Текстовая теория пока не добавлена. Проверьте материалы урока.</Text></Card>}
  {theory.length>0 && <Card>{studyAction}</Card>}
  <LessonMaterials api={api} lesson={lesson} studyAction={theory.length?undefined:studyAction}/>
  {exercises.length>0 && <LessonExercises api={api} lessonId={lesson.id} exercises={exercises} onSaved={refreshLearning}/>}
  {quiz && <ResumableQuiz key={quiz.id} api={api} lessonId={lesson.id} quiz={quiz} onSaved={refreshLearning}/>}
  {challenge && <LessonDiary key={challenge} api={api} lessonId={lesson.id} challengeId={challenge} onSaved={refreshLearning}/>}
  <Card><NarrationLibrary sections={['intro']}/></Card>
 </NarrationProvider>;
}
function AuthenticatedLesson({id,api}: {id:string;api:ApiClient}) {
 const lesson=useResource(useCallback(()=>api.lesson(id),[api,id]));
 return <Screen refreshing={lesson.loading} onRefresh={()=>void lesson.reload()}>{lesson.error && <Notice message={lesson.error} action="Повторить" onAction={()=>void lesson.reload()}/>}{lesson.loading && !lesson.data?<Loading/>:lesson.data?.lesson?<LessonBody api={api} lesson={lesson.data.lesson}/>:!lesson.error && <Card><Text style={s.body}>Материал пока недоступен.</Text></Card>}</Screen>;
}
export default function LessonDetail() {
 const {id}=useLocalSearchParams<{id:string}>();const {api,status,user}=useSession();
 if(status==='loading')return <Screen><Loading/></Screen>;
 if(status!=='signedIn')return <Redirect href="/"/>;
 if(typeof id!=='string' || !/^[A-Za-z0-9_-]{1,128}$/.test(id))return <Screen><Notice message="Не удалось определить урок. Откройте его из списка обучения."/></Screen>;
 return <AuthenticatedLesson key={`${user?.id}:${id}`} id={id} api={api}/>;
}
