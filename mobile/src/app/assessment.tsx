import {SavedReportExport} from '../components/SavedReportExport';
import {assessmentDocument} from '../lib/supplementalReportExport';
import {useEffect,useRef,useState,useSyncExternalStore} from 'react';
import {Pressable,Text,View} from 'react-native';
import {router} from 'expo-router';
import {Button,Card,Heading,Loading,Notice,Screen,s} from '../components/ui';
import {NarrationProvider,NarrationClip} from '../components/audio/Narration';
import {useSession} from '../lib/session';
import {pendingCalculationStorage} from '../lib/pendingCalculationStorage';
import {createAssessmentController} from '../lib/assessment';
import {submissionId} from '../lib/learning';
import {colors} from '../lib/theme';

function Assessment(){
 const {api,user,session,creditNotice}=useSession();
 const [pendingStore]=useState(()=>pendingCalculationStorage(user!.id,'assessment'));
 const [controller]=useState(()=>{const owner=user!.id;return createAssessmentController({catalog:()=>api.request('/numerology/assessment/catalog'),history:()=>api.request('/numerology/assessment/history'),calculate:body=>api.request('/numerology/assessment',{method:'POST',body}),refreshBalance:()=>session.refresh(),onInsufficientCredits:creditNotice.insufficient,makeId:submissionId,isCurrent:()=>session.getSnapshot().user?.id===owner,pendingStore});});
 const state=useSyncExternalStore(controller.subscribe,controller.getSnapshot,controller.getSnapshot);
 const [draftStore]=useState(()=>pendingCalculationStorage(user!.id,'assessment-draft'));
 const [answers,setAnswers]=useState<Record<string,string>>({}),[index,setIndex]=useState(0),[draftReady,setDraftReady]=useState(false),[draftError,setDraftError]=useState(''),[expanded,setExpanded]=useState(false),[method,setMethod]=useState(false),[composing,setComposing]=useState(true);
 const chain=useRef(Promise.resolve());
 const complete=async()=>{const current=controller.getSnapshot();if(current.result&&!current.pending&&!current.error){setComposing(false);setAnswers({});setIndex(0);chain.current=chain.current.catch(()=>{}).then(()=>draftStore.set({answers:{},index:0,completed:true}));try{await chain.current;setDraftError('');}catch{setDraftError('Разбор сохранён в аккаунте. Не удалось сохранить состояние экрана на устройстве.');}}};
 useEffect(()=>{let active=true;void (async()=>{try{const [value,pending]=await Promise.all([draftStore.get(),pendingStore.get()]);if(!active)return;if(value){if(typeof value.answers!=='object'||Array.isArray(value.answers)||!Number.isInteger(value.index)||value.index<0||value.index>9)throw Error('Черновик опроса повреждён.');setAnswers(value.answers);setIndex(value.index);setComposing(!value.completed);}setDraftReady(true);await controller.load();if(active&&pending?.request_id===controller.getSnapshot().result?.request_id)await complete();}catch(e){if(active)setDraftError(e instanceof Error?e.message:'Не удалось восстановить ответы.');}})();return()=>{active=false;};},[controller,draftStore,pendingStore]);
 const save=(next:Record<string,string>,position:number)=>{setAnswers(next);setIndex(position);chain.current=chain.current.catch(()=>{}).then(()=>draftStore.set({answers:next,index:position}));void chain.current.then(()=>setDraftError('')).catch(()=>setDraftError('Не удалось сохранить ответы на устройстве. Оставьте страницу открытой и повторите.'));};
 const start=()=>{save({},0);setDraftReady(true);setComposing(true);setExpanded(false);setMethod(false);};
 const questions=state.catalog?.questions||[],q=questions[index],result=state.result?.results;
 const locked=state.busy||!!state.pending||!draftReady;
 const answered=questions.filter(question=>question.options.some(o=>o.id===answers[question.id])).length;
 const submit=async()=>{try{await chain.current;await controller.calculate({kind:'assessment',answers},user?.credits_remaining);await complete();}catch{setDraftError('Ответы пока не сохранены. Повторите сохранение.');}};
 return <Screen><Heading title="Самонаблюдение" subtitle="Десять вопросов о привычках и предпочтениях. Выберите то, что ближе вам сейчас."/>
 {state.loading&&!state.catalog&&<Loading/>}
 {!!state.error&&<Notice message={state.error} action="Обновить" onAction={()=>void controller.load()}/>}
 {!!state.balanceError&&<Notice message={state.balanceError} action="Обновить баланс" onAction={()=>void controller.refreshBalance()}/>}
 {!!draftError&&<Notice message={draftError} action={draftReady?'Сохранить ещё раз':'Начать новый опрос'} onAction={()=>draftReady?save(answers,index):start()}/>}
 {state.pending&&<Card><Text style={s.body}>Ответы отправлены, подтверждение ещё не получено. Повторная проверка использует ту же попытку.</Text><Button title="Проверить результат" busy={state.busy} onPress={()=>void controller.retry().then(complete)}/></Card>}
 {q&&composing&&<Card><Text style={s.eyebrow}>ВОПРОС {index+1} ИЗ 10</Text><Text style={s.title}>{q.question}</Text><Text style={s.small}>Отвечено: {answered} из 10. Ответы сохраняются на этом устройстве.</Text>
 <View accessibilityRole="radiogroup" accessibilityLabel={q.question} style={{gap:9}}>{q.options.map(option=><Pressable key={option.id} accessibilityRole="radio" accessibilityLabel={option.text} accessibilityState={{checked:answers[q.id]===option.id,disabled:locked}} disabled={locked} onPress={()=>save({...answers,[q.id]:option.id},index)} style={{padding:14,borderWidth:1,borderColor:answers[q.id]===option.id?colors.navy:colors.line,borderRadius:13,backgroundColor:answers[q.id]===option.id?colors.blue:colors.surface}}><Text style={s.body}>{answers[q.id]===option.id?'● ':'○ '}{option.text}</Text></Pressable>)}</View>
 <View style={{gap:10}}>{index>0&&<Button secondary title="Предыдущий вопрос" disabled={locked} onPress={()=>save(answers,index-1)}/>}{index<9?<Button title="Следующий вопрос" disabled={locked||!answers[q.id]} onPress={()=>save(answers,index+1)}/>:<Button title={`Получить разбор · ${state.catalog?.assessment??'—'} балл.`} disabled={locked||answered!==10||state.catalog?.assessment===null} busy={state.busy} onPress={()=>void submit()}/>}</View>
 <Text style={s.small}>Баллы списываются при получении нового разбора. Ранее сохранённые результаты открываются бесплатно.</Text>
 </Card>}
 {result&&!composing&&<Card><Text style={s.eyebrow}>ВАШ РАЗБОР</Text><Text style={s.heading}>{result.number} · {result.theme}</Text><Text selectable style={s.body}>{result.interpretation}</Text><Text selectable style={s.label}>{result.focus}</Text><NarrationClip key={result.narration_id} id={result.narration_id}/>
 <Text style={s.title}>Как распределились ответы</Text>{result.frequencies.map(row=><View key={row.number} style={{gap:5}}><Text style={s.small}>Число {row.number} · {row.count} из 10</Text><View accessibilityLabel={`Число ${row.number}: ${row.count} ответов`} style={{height:10,borderRadius:5,backgroundColor:colors.line,overflow:'hidden'}}><View style={{height:10,width:`${row.count*10}%`,backgroundColor:row.number===result.number?colors.navy:colors.accent}}/></View></View>)}
 {result.tie_note&&<Text style={s.small}>{result.tie_note} Числа с одинаковой частотой: {result.leaders.join(', ')}.</Text>}
 <Button secondary title={expanded?'Скрыть выбранные ответы':'Из каких ответов получен результат'} onPress={()=>setExpanded(!expanded)}/>{expanded&&result.answers.map(answer=><View key={answer.question_id} style={{gap:5}}><Text style={s.label}>{answer.question}</Text><Text selectable style={s.body}>{answer.answer} → {answer.number}</Text></View>)}
 <Button secondary title={method?'Скрыть метод':'Как рассчитан разбор'} onPress={()=>setMethod(!method)}/>{method&&<><Text selectable style={s.body}>{result.method}</Text><Text style={s.small}>Сумма выбранных значений: {result.total}.</Text><NarrationClip id="assessment-method"/></>}
 <SavedReportExport document={()=>assessmentDocument(state.result!)}/>
 <Button secondary title="Пройти заново" disabled={locked} onPress={start}/>
 </Card>}
 {!composing&&!result&&!state.loading&&<Button title="Начать опрос" onPress={start}/>}
 {state.history.length>0&&<Card><Text style={s.title}>Сохранённые разборы</Text>{state.history.map(row=><Button key={row.id} secondary title={`${new Date(row.created_at).toLocaleDateString('ru-RU')} · ${row.results.theme} · ${row.results.number}`} disabled={state.busy||!!state.pending} onPress={()=>{controller.select(row);setComposing(false);setExpanded(false);setMethod(false);}}/>)}</Card>}
 <Button secondary title="На главную" onPress={()=>router.replace('/home')}/>
 </Screen>;
}
export default function AssessmentRoute(){const {user,status}=useSession();if(status==='loading')return <Screen><Loading/></Screen>;if(status!=='signedIn')return <Screen><Heading title="Самонаблюдение" subtitle="Войдите, чтобы пройти опрос и сохранить свой разбор."/><Button title="Войти" onPress={()=>router.replace('/')}/></Screen>;return <NarrationProvider key={user!.id} path="/narration/project"><Assessment/></NarrationProvider>;}
