import {SavedReportExport} from '../components/SavedReportExport';
import {relationshipReportDocument} from '../lib/savedReportExport';
import {useEffect, useRef, useState, useSyncExternalStore} from 'react';
import {Pressable, ScrollView, StyleSheet, Text, View} from 'react-native';
import {router} from 'expo-router';
import {createRelationshipController, RelationshipMember, RelationshipPerson, RelationshipReceipt} from '@numerom/api-client';
import {Button, Card, Field, Heading, Loading, Notice, Screen, s} from '../components/ui';
import {InterpretationSheet, SchemeInterpretation} from '../components/numbers/InterpretationSheet';
import {useSession} from '../lib/session';
import {pendingCalculationStorage} from '../lib/pendingCalculationStorage';
import {submissionId} from '../lib/learning';
import {colors as c} from '../lib/theme';
import {NarrationClip} from '../components/audio/Narration';
import {relationshipVoice} from '../lib/relationshipVoice';

const blank = ():RelationshipPerson => ({name:'',birth_date:''});
const points = (value:number) => `${value} ${value%100>=11&&value%100<=14?'баллов':value%10===1?'балл':value%10>=2&&value%10<=4?'балла':'баллов'}`;
const dateLabel = (value:string) => new Date(value).toLocaleString('ru-RU',{day:'numeric',month:'long',year:'numeric',hour:'2-digit',minute:'2-digit'});

export function RelationshipResult({receipt}:{receipt:RelationshipReceipt}) {
 const r=receipt.results;
 const [selected,setSelected]=useState(0),[method,setMethod]=useState(false),[detail,setDetail]=useState<SchemeInterpretation|null>(null);
 function explain(person:RelationshipMember) {
  setDetail({title:`${person.name} · число жизненного пути`,value:person.number,meaning:'',valueCaption:person.birth_date,
   ...(person.number<=9?{knowledgeDigit:person.number}:{narrationId:`master-${person.number}`})});
 }
 const connection=r.connections[selected];
 return <View style={{gap:20}}>
  <Card tinted><Text style={s.eyebrow}>Ваш сохранённый разбор</Text><Text style={s.title}>{r.kind==='pair'?'Два человека — два ритма':'Созвучие в группе'}</Text>
   <Text style={s.small}>{dateLabel(receipt.created_at)} · стоимость {points(receipt.cost)}</Text>
   <View style={styles.members}>{[r.main,...r.people].map((person,index)=><Pressable key={index} accessibilityRole="button" accessibilityLabel={`${person.name}: число ${person.number}. Открыть расшифровку и озвучку`} onPress={()=>explain(person)} style={styles.member}>
    <Text style={styles.number}>{person.number}</Text><Text style={styles.memberName}>{person.name}</Text><Text style={s.small}>{person.birth_date}</Text>{index===0&&<Text style={s.small}>Основной участник</Text>}
   </Pressable>)}</View>
   <Text style={s.small}>Нажмите на число, чтобы прочитать трактовку и послушать озвучку.</Text>
  </Card>
  <Card><Text style={s.title}>{r.kind==='pair'?'Индекс пары':'Индексы группы'}</Text>
   {r.connections.map((item,index)=><Pressable key={index} accessibilityRole="button" accessibilityState={{selected:selected===index}} accessibilityLabel={`${item.name}: ${item.score} из 10. Показать пояснение`} onPress={()=>setSelected(index)} style={[styles.graphRow,selected===index&&styles.selected]}>
    <View style={s.row}><Text style={[s.label,{flex:1}]}>{r.main.name} + {item.name}</Text><Text style={styles.score}>{item.score}<Text style={s.small}> / 10</Text></Text></View>
    <View accessibilityRole="progressbar" accessibilityLabel={`Индекс: ${item.name}`} accessibilityValue={{min:0,max:10,now:item.score}} style={styles.track}><View style={[styles.fill,{width:`${item.score*10}%`}]}/></View>
   </Pressable>)}
   {r.kind==='group'&&<Text style={s.body}>Средний индекс группы: {r.average.toLocaleString('ru-RU',{maximumFractionDigits:1})} / 10</Text>}
   <Text style={s.small}>{r.note}</Text>
  </Card>
  <Card><Text style={s.eyebrow}>{r.main.name} и {connection.name}</Text><Text style={s.title}>{connection.title}</Text>{relationshipVoice(connection.score)&&<NarrationClip key={selected} id={relationshipVoice(connection.score)!}/>}<Text selectable style={s.body}>{connection.interpretation}</Text><View style={s.separator}/><Text style={s.label}>На что обратить внимание</Text><Text selectable style={s.body}>{connection.focus}</Text></Card>
  <Button secondary title={method?'Скрыть формулы':'Как рассчитана совместимость'} onPress={()=>setMethod(!method)}/>
  {method&&<Card><NarrationClip id="relationship-method"/><Text selectable style={s.body}>{r.method}</Text>{[r.main,...r.people].map((person,index)=><View key={index} style={{gap:6}}><Text style={s.label}>{person.name} · {person.birth_date}</Text>{person.steps.map((step,i)=><Text selectable key={i} style={s.body}>{step}</Text>)}</View>)}{r.connections.map((item,index)=><Text selectable key={index} style={s.body}>{r.main.name} + {item.name}: {item.formula}</Text>)}</Card>}
  <SavedReportExport document={()=>relationshipReportDocument(receipt)}/>
  <InterpretationSheet detail={detail} onClose={()=>setDetail(null)} onProfile={()=>router.push('/profile')}/>
 </View>;
}

export default function Relationships() {
 const {api,user,session,creditNotice}=useSession();
 const active=useRef(true);
 const scroll=useRef<ScrollView|null>(null);
 const [controller]=useState(()=>createRelationshipController({catalog:()=>api.relationshipCatalog(),history:()=>api.relationshipHistory(),calculate:body=>api.calculateRelationships(body),refreshBalance:()=>session.refresh(),onInsufficientCredits:creditNotice.insufficient,makeId:submissionId,pendingStore:pendingCalculationStorage(user!.id,'relationships'),isCurrent:()=>active.current}));
 const state=useSyncExternalStore(controller.subscribe,controller.getSnapshot,controller.getSnapshot);
 const [kind,setKind]=useState<'pair'|'group'>('pair'),[main,setMain]=useState<RelationshipPerson>({name:user?.name || user?.full_name || '',birth_date:user?.birth_date || ''});
 const [people,setPeople]=useState<RelationshipPerson[]>([blank()]),[form,setForm]=useState(false),[history,setHistory]=useState(false);
 useEffect(()=>{active.current=true;void controller.load();return()=>{active.current=false;};},[controller]);
 useEffect(()=>{if(state.result){setForm(false);scroll.current?.scrollTo({y:0,animated:true});}},[state.result?.id]);
 const cost=state.catalog?.[kind], balance=user?.credits_remaining;
 const locked=state.busy || !!state.pending;
 const showForm=form || !state.result;
 const canCalculate=typeof cost==='number' && typeof balance==='number' && !state.balanceError;
 function edit(index:number,key:keyof RelationshipPerson,value:string){setPeople(old=>old.map((person,i)=>i===index?{...person,[key]:value}:person));}
 return <Screen scrollRef={scroll}><Heading eyebrow="Числа и отношения" title="Совместимость" subtitle="Рассмотрите индивидуальные акценты и найдите темы для разговора."/>
  {state.error&&<Notice message={state.error}/>}
  {state.balanceError&&<Notice message={`Расчёт сохранён. ${state.balanceError}`} action="Обновить только баланс" onAction={()=>void controller.refreshBalance()}/>}
  {state.pending&&<Card tinted><Text style={s.title}>Проверим предыдущую попытку</Text><Text style={s.body}>Ответ сервера не подтверждён. Повтор использует ту же попытку; уже оплаченный расчёт не спишет баллы снова.</Text><Button title="Повторить ту же попытку" busy={state.busy} onPress={()=>void controller.retry()}/><Button secondary title="Проверить сохранённые результаты" disabled={state.busy || state.loading} onPress={()=>void controller.load()}/></Card>}
  {state.loading&&!state.catalog&&<Loading/>}
  {state.result&&<><RelationshipResult key={state.result.id} receipt={state.result}/><Button title={form?'Закрыть форму':'Новый расчёт'} secondary disabled={locked} onPress={()=>setForm(!form)}/></>}
  {showForm&&<Card><Text style={s.title}>Кого сравним?</Text><View style={styles.modes}>{(['pair','group'] as const).map(value=><Pressable key={value} disabled={locked} accessibilityRole="button" accessibilityState={{selected:kind===value,disabled:locked}} onPress={()=>setKind(value)} style={[styles.mode,kind===value&&styles.modeActive]}><Text style={[s.label,kind===value&&{color:'#fff'}]}>{value==='pair'?'Пара':'Группа'}</Text></Pressable>)}</View>
   <Text style={s.label}>Основной участник</Text><Field label="Ваше имя" value={main.name} maxLength={80} editable={!locked} onChangeText={name=>setMain({...main,name})}/><Field label="Ваша дата рождения" placeholder="ДД.ММ.ГГГГ" value={main.birth_date} maxLength={10} keyboardType="numbers-and-punctuation" editable={!locked} onChangeText={birth_date=>setMain({...main,birth_date})}/>
   {(kind==='pair'?people.slice(0,1):people).map((person,index)=><View key={index} style={{gap:14,paddingTop:12,borderTopWidth:1,borderColor:c.line}}><Text style={s.title}>{kind==='pair'?'Второй участник':`Участник ${index+1}`}</Text><Field label={`Имя участника ${index+1}`} value={person.name} maxLength={80} editable={!locked} onChangeText={value=>edit(index,'name',value)}/><Field label={`Дата рождения участника ${index+1}`} placeholder="ДД.ММ.ГГГГ" value={person.birth_date} maxLength={10} keyboardType="numbers-and-punctuation" editable={!locked} onChangeText={value=>edit(index,'birth_date',value)}/>{kind==='group'&&people.length>1&&<Button title={`Убрать участника ${index+1}`} secondary disabled={locked} onPress={()=>setPeople(old=>old.filter((_,i)=>i!==index))}/>}</View>)}
   {kind==='group'&&people.length<5&&<Button title="Добавить участника" secondary disabled={locked} onPress={()=>setPeople(old=>[...old,blank()])}/>}
   {kind==='group'&&<Text style={s.small}>До пяти участников помимо основного. Сравнение каждого с основным, не всех возможных пар.</Text>}
   <View style={s.separator}/><Text style={s.body}>Стоимость: {typeof cost==='number'?points(cost):'—'} · баланс: {typeof balance==='number'?points(balance):'—'}</Text>
   {typeof cost==='number'&&typeof balance==='number'&&balance<cost&&<Button title="Пополнить баллы" secondary onPress={()=>router.push('/top-up')}/>}
   <Button title={cost===0?'Рассчитать бесплатно':`Рассчитать за ${typeof cost==='number'?points(cost):'—'}`} busy={state.busy} disabled={locked || !canCalculate} onPress={()=>void controller.calculate({kind,main,people:kind==='pair'?people.slice(0,1):people},balance)}/>
   <Text style={s.small}>Нажатие подтверждает указанную стоимость. Просмотр сохранённых результатов бесплатный.</Text>
  </Card>}
  <Button secondary title={history?'Скрыть историю':`Сохранённые расчёты (${state.history.length})`} onPress={()=>setHistory(!history)}/>
  {history&&<Card><Text style={s.title}>Последние 30 расчётов</Text>{!state.history.length&&<Text style={s.body}>Здесь появятся ваши новые расчёты пары и группы.</Text>}{state.history.map(item=><Button key={item.id} title={`${item.results.main.name} + ${item.results.people.map(p=>p.name).join(', ')} · ${dateLabel(item.created_at)}`} secondary disabled={state.busy} onPress={()=>{controller.select(item);setHistory(false);}}/>)}</Card>}
  <Button secondary title="Обновить цены и историю" disabled={state.loading || state.busy} onPress={()=>void controller.load()}/><Button secondary title="На главную" onPress={()=>router.replace('/home')}/>
 </Screen>;
}

const styles=StyleSheet.create({
 members:{flexDirection:'row',flexWrap:'wrap',gap:12},member:{flexGrow:1,flexBasis:140,alignItems:'center',gap:7,padding:16,borderRadius:18,backgroundColor:c.surface},number:{fontSize:42,fontWeight:'600',color:c.navy},memberName:{fontSize:16,fontWeight:'600',color:c.ink,textAlign:'center'},
 graphRow:{gap:12,padding:12,borderRadius:13,borderWidth:1,borderColor:c.line},selected:{borderColor:c.accent,backgroundColor:c.blue},score:{fontSize:23,fontWeight:'600',color:c.navy},track:{height:10,borderRadius:5,backgroundColor:c.line,overflow:'hidden'},fill:{height:10,borderRadius:5,backgroundColor:c.accent},modes:{flexDirection:'row',gap:10},mode:{flex:1,minHeight:48,justifyContent:'center',alignItems:'center',borderRadius:13,backgroundColor:c.blue},modeActive:{backgroundColor:c.navy},
});
