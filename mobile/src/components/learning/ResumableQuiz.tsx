import {useCallback,useEffect,useRef,useState,useSyncExternalStore} from 'react';
import {Text,View} from 'react-native';
import type {ApiClient} from '@numerom/api-client';
import {Button,Card,Field,Loading,Notice,s} from '../ui';
import {NarrationClip} from '../audio/Narration';
import {DraftStatus} from './DraftStatus';
import {Choices} from './LessonActivities';
import {useSession} from '../../lib/session';
import {useResource} from '../../lib/useResource';
import {serverDate} from '../../lib/serverDate';
import {LessonQuiz,quizAttempts,submissionId} from '../../lib/learning';
import {createQuizWork} from '../../lib/quizWork';

export function ResumableQuiz({api,lessonId,quiz,onSaved}:{api:ApiClient;lessonId:string;quiz:LessonQuiz;onSaved:()=>Promise<void>}){
 const {user,session}=useSession();const callback=useRef(onSaved);callback.current=onSaved;
 const history=useResource(useCallback(()=>api.request(`/student/quiz-attempts/${encodeURIComponent(lessonId)}`).then(quizAttempts),[api,lessonId]));
 const reload=useRef(history.reload);reload.current=history.reload;
 const [controller]=useState(()=>{const path=`/student/quiz-drafts/${encodeURIComponent(lessonId)}/${encodeURIComponent(quiz.id)}`,owner=user?.id;
  return createQuizWork({read:()=>api.request(path),write:body=>api.request(path,{method:'POST',body}),submit:body=>api.request('/student/quiz-attempt',{method:'POST',body}),makeId:submissionId,lessonId,quiz,
   isCurrent:()=>session.getSnapshot().user?.id===owner,onSaved:async()=>{await Promise.all([callback.current(),reload.current()]);}});
 });
 const state=useSyncExternalStore(controller.subscribe,controller.getSnapshot,controller.getSnapshot);
 useEffect(()=>{void controller.load();return()=>controller.dispose();},[controller]);
 const work=state.work,question=work&&quiz.questions[work.index],pending=work?.stage==='submitting',latest=state.result||history.data?.[0];
 const [confirm,setConfirm]=useState(false);
 return <Card><Text accessibilityRole="header" style={s.heading}>{quiz.title}</Text>{!!quiz.description&&<Text style={s.body}>{quiz.description}</Text>}
  {!state.draft.ready&&<Loading/>}
  {!!history.error&&<Notice message={history.error} action="Обновить результаты" onAction={()=>void history.reload()}/>}
  {!quiz.supported&&<Text style={s.body}>Преподаватель ещё готовит этот тест.</Text>}
  {latest&&!work&&<><Text style={s.heading}>{latest.score}%</Text><Text style={s.title}>{latest.passed?'Тест пройден':'Тест пока не пройден'}</Text><Text style={s.small}>Результат сохранён на сервере.</Text></>}
  {!work&&quiz.supported&&state.draft.ready&&<Button title={latest?'Пройти ещё раз':'Начать тест'} onPress={()=>void controller.start()}/>}
  {work&&question&&!state.invalid&&<>
   <Text style={s.small}>Вопрос {work.index+1} из {quiz.questions.length} · можно продолжить позже</Text><Text accessibilityRole="header" style={s.title}>{question.prompt}</Text>
   <NarrationClip key={question.id} id={`quiz-${question.id}`}/>
   {question.type==='text'?<Field label="Ваш ответ" value={work.answers[question.id]||''} onChangeText={value=>controller.answer(question.id,value)} onBlur={()=>void controller.flush()} multiline maxLength={4000} editable={!state.busy&&!pending} style={[s.input,{minHeight:100}]}/>:<Choices label={question.prompt} options={question.options} value={work.answers[question.id]||''} onChange={value=>controller.answer(question.id,value)} disabled={state.busy||pending}/>}
   <View style={s.row}>{work.index>0&&<View style={{flex:1}}><Button secondary title="Назад" onPress={()=>controller.go(work.index-1)} disabled={state.busy||pending}/></View>}{work.index<quiz.questions.length-1&&<View style={{flex:1}}><Button title="Далее" onPress={()=>controller.go(work.index+1)} disabled={!work.answers[question.id]?.trim()||state.busy||pending}/></View>}</View>
   {(work.index===quiz.questions.length-1||pending)&&<Button title={pending?'Проверить отправленную попытку':'Проверить ответы'} onPress={()=>void controller.submit()} busy={state.busy} disabled={!quiz.questions.every(q=>work.answers[q.id]?.trim())||state.draft.conflict}/>}
   {pending&&<Text style={s.small}>Ответы сохранены. Повтор проверяет эту же попытку, даже после перезагрузки.</Text>}
   {!pending&&!state.busy&&(!confirm?<Button secondary title="Начать тест заново" onPress={()=>setConfirm(true)}/>:<><Text style={s.small}>Очистить ответы текущего черновика?</Text><Button secondary title="Очистить ответы и начать заново" onPress={()=>{setConfirm(false);void controller.start();}}/><Button secondary title="Продолжить текущий тест" onPress={()=>setConfirm(false)}/></>)}
  </>}
  <DraftStatus state={state.draft} retry={()=>void (state.draft.ready?controller.flush():controller.load())} keepMine={()=>void controller.keepMine()} useServer={()=>void controller.useServer()}/>
  {!!state.error&&<Notice message={state.error}/>}
  {state.invalid&&<Button secondary title="Очистить несовместимый черновик и начать заново" onPress={()=>void controller.start()}/>}
  {!!history.data?.length&&<View style={{gap:8}}><Text style={s.label}>Сохранённые попытки</Text>{history.data.slice(0,5).map(r=><Text key={r.id} style={s.small}>{r.score}% · {r.passed?'Пройден':'Не пройден'}{serverDate(r.attemptedAt)?` · ${serverDate(r.attemptedAt)!.toLocaleDateString('ru-RU')}`:''}</Text>)}</View>}
 </Card>;
}
