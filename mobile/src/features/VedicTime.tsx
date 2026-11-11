import {SavedReportExport} from '../components/SavedReportExport';
import {vedicDocument} from '../lib/supplementalReportExport';
import {useEffect,useRef,useState,useSyncExternalStore} from 'react';
import {Pressable,ScrollView,Text,View} from 'react-native';
import {router} from 'expo-router';
import {Button,Card,Field,Heading,Loading,Notice,Screen,s} from '../components/ui';
import {NarrationClip} from '../components/audio/Narration';
import {InterpretationSheet,SchemeInterpretation} from '../components/numbers/InterpretationSheet';
import {useSession} from '../lib/session';
import {pendingCalculationStorage} from '../lib/pendingCalculationStorage';
import {submissionId} from '../lib/learning';
import {createVedicController,kinds,titles,VedicDraft,VedicReceipt,VedicKind} from '../lib/vedicCalculations';
import {localTimeLabel} from '../lib/vedicVisuals';
import {PlanetRouteChart,DayPeriodTimeline,SolarDayWheel} from '../components/vedic/VedicVisuals';
import {colors as c} from '../lib/theme';
import {LocationField} from '../components/LocationField';
const date=(v:string)=>v.split('-').reverse().join('.');
// Solar boundaries already belong to the named city; never convert them into the device timezone.
const time=localTimeLabel;
const chip={padding:12,borderWidth:1,borderColor:c.line,borderRadius:13,backgroundColor:c.surface,minHeight:44} as const;
export function VedicResult({receipt}:{receipt:VedicReceipt}){
 const r=receipt.results;
 const [index,setIndex]=useState(0),[method,setMethod]=useState(false),[detail,setDetail]=useState<SchemeInterpretation|null>(null);
 const day=r.days[index]||r.days[0];
 if(!day)return <Notice message="Дни сохранённого маршрута не получены."/>;
 return <View style={{gap:20}}>
  <Card tinted><Text style={s.eyebrow}>СОХРАНЁННЫЙ РАСЧЁТ</Text><Text style={s.title}>{r.title}</Text><Text style={s.body}>{r.city} · {date(r.start_date)}{r.start_date!==r.end_date?` — ${date(r.end_date)}`:''}</Text><Text style={s.small}>Время города: {r.timezone}. {r.birth_date?`Дата рождения: ${r.birth_date}. `:''}Стоимость: {receipt.cost} балл.</Text>{!!r.wisdom_note&&<Text selectable style={s.small}>{r.wisdom_note}</Text>}<Text selectable style={s.body}>{r.meaning}</Text><NarrationClip id={r.narration_id}/></Card>
  {r.days.some(item=>item.energies.length>0)&&<Card><PlanetRouteChart days={r.days} index={index} onDay={setIndex}
    onInterpret={energy=>setDetail({title:energy.title,value:energy.value,valueCaption:'Индекс дня из 100',meaning:'',knowledgeDigit:energy.digit})}/></Card>}
  <Card><Text style={s.eyebrow}>{day.weekday} · {date(day.date)}</Text><Text style={s.title}>Планета дня — {day.ruler}</Text><Text style={s.body}>Восход {time(day.sunrise)} · закат {time(day.sunset)}</Text>
   {day.average!==null&&<Text style={s.small}>Средний индекс девяти планет: {day.average.toLocaleString('ru-RU',{maximumFractionDigits:2})} из 100.</Text>}
   <Text selectable style={s.body}>{r.focus}</Text>
  </Card>
  <Card><DayPeriodTimeline key={day.date} day={day} timezone={r.timezone}/></Card>
  {!!day.hours.length&&<Card><SolarDayWheel key={day.date} day={day} timezone={r.timezone}/></Card>}
  <Button secondary title={method?'Скрыть метод расчёта':'Как получен этот маршрут'} onPress={()=>setMethod(!method)}/>{method&&<Card><Text selectable style={s.body}>{r.method}</Text></Card>}
  <SavedReportExport document={()=>vedicDocument(receipt)}/>
  <InterpretationSheet detail={detail} onClose={()=>setDetail(null)} onProfile={()=>router.push('/profile')}/>
 </View>;
}
export default function VedicTime(){
 const {api,user,session,creditNotice}=useSession();const active=useRef(true),scroll=useRef<ScrollView|null>(null);
 const [locating,setLocating]=useState(false);
 const [controller]=useState(()=>{const owner=user!.id;return createVedicController({catalog:()=>api.request('/numerology/vedic/catalog'),history:()=>api.request('/numerology/vedic/history'),calculate:body=>api.request('/numerology/vedic',{method:'POST',body,timeoutMs:35000}),refreshBalance:()=>session.refresh(),onInsufficientCredits:creditNotice.insufficient,makeId:submissionId,isCurrent:()=>active.current&&session.getSnapshot().user?.id===owner,pendingStore:pendingCalculationStorage(owner,'vedic')});});
 const state=useSyncExternalStore(controller.subscribe,controller.getSnapshot,controller.getSnapshot);
 const [draft,setDraft]=useState<VedicDraft>({kind:'schedule',date:[new Date().getFullYear(),String(new Date().getMonth()+1).padStart(2,'0'),String(new Date().getDate()).padStart(2,'0')].join('-'),city:'',birth_date:user?.birth_date||''}),[form,setForm]=useState(false),[history,setHistory]=useState(false);
 useEffect(()=>{active.current=true;void controller.load();return()=>{active.current=false;};},[controller]);
 useEffect(()=>{if(state.result){setForm(false);scroll.current?.scrollTo({y:0,animated:true});}},[state.result?.id]);
 const cost=state.catalog?.[draft.kind],balance=user?.credits_remaining,locked=state.busy||!!state.pending;
 return <Screen scrollRef={scroll}><Heading eyebrow="ВРЕМЯ И РИТМЫ" title="Планетарный маршрут" subtitle="Выберите город и период. Сохранённый расчёт можно открыть повторно без списания баллов."/>
  {!!state.error&&<Notice message={state.error} action="Обновить цены и историю" onAction={()=>void controller.load()}/>}{!!state.balanceError&&<Notice message={state.balanceError} action="Обновить баланс" onAction={()=>void controller.refreshBalance()}/>}
  {state.pending&&<Card><Text style={s.body}>Подтверждение ещё не получено. Проверка повторяет ту же попытку, чтобы исключить повторное списание.</Text><Button title="Проверить предыдущую попытку" busy={state.busy} onPress={()=>void controller.retry()}/></Card>}
  {state.loading&&!state.catalog&&<Loading/>}
  {state.result&&<><VedicResult key={state.result.id} receipt={state.result}/><Button secondary disabled={locked} title={form?'Закрыть форму':'Новый маршрут'} onPress={()=>setForm(!form)}/></>}
  {(form||!state.result)&&<Card><Text style={s.title}>Параметры расчёта</Text><View style={{flexDirection:'row',flexWrap:'wrap',gap:8}}>{(Object.keys(kinds) as VedicKind[]).map(kind=><Pressable key={kind} disabled={locked} accessibilityRole="button" accessibilityState={{selected:draft.kind===kind,disabled:locked}} onPress={()=>setDraft(current=>({...current,kind}))} style={[chip,draft.kind===kind&&{backgroundColor:c.blue,borderColor:c.navy}]}><Text style={s.label}>{titles[kind]}</Text></Pressable>)}</View>
   <LocationField key={user?.id} value={draft.city} disabled={locked} allowLive onBusyChange={setLocating} onChange={(city,location)=>setDraft(current=>({...current,city,location}))}/><Field label="Дата начала · ГГГГ-ММ-ДД" value={draft.date} maxLength={10} editable={!locked} keyboardType="numbers-and-punctuation" onChangeText={date=>setDraft(current=>({...current,date}))}/>
   {draft.kind!=='schedule'&&<Field label="Дата рождения · ДД.ММ.ГГГГ" value={draft.birth_date} placeholder="ДД.ММ.ГГГГ" maxLength={10} editable={!locked} keyboardType="numbers-and-punctuation" onChangeText={birth_date=>setDraft(current=>({...current,birth_date}))}/>}
   <Text style={s.small}>{draft.kind==='schedule'?'24 планетарных часа и четыре традиционных периода дня.':draft.kind==='daily'?'Один календарный день с персональными индексами девяти планет.':`${kinds[draft.kind]} последовательных календарных дней с персональными индексами девяти планет.`} Баланс: {balance??'—'} балл.</Text>
   <Button title={`Рассчитать · ${cost??'—'} балл.`} busy={state.busy} disabled={locked||locating||typeof cost!=='number'||typeof balance!=='number'||!!state.balanceError} onPress={()=>void controller.calculate({...draft,city:draft.city.trim(),birth_date:draft.kind==='schedule'?'':draft.birth_date},balance)}/>
  </Card>}
  {!!state.history.length&&<><Button secondary title={history?'Скрыть историю':'Последние пять маршрутов'} onPress={()=>setHistory(!history)}/>{history&&<Card>{state.history.map(row=><Button key={row.id} secondary disabled={state.busy} title={`${row.results.title} · ${date(row.results.start_date)} · ${row.results.city}`} onPress={()=>controller.select(row)}/>)}</Card>}</>}
 <Button secondary title="На главную" onPress={()=>router.replace('/home')}/></Screen>;
}
