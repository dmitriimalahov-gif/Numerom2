import {SavedReportExport} from '../components/SavedReportExport';
import {toolReportDocument} from '../lib/savedReportExport';
import {useEffect,useRef,useState,useSyncExternalStore} from 'react';
import {Pressable,ScrollView,StyleSheet,Text,View} from 'react-native';
import {router} from 'expo-router';
import {createToolController,ToolKind,ToolReceipt} from '@numerom/api-client';
import {Button,Card,Field,Heading,Loading,Notice,Screen,s} from '../components/ui';
import {InterpretationSheet,SchemeInterpretation} from '../components/numbers/InterpretationSheet';
import {NarrationClip} from '../components/audio/Narration';
import {useSession} from '../lib/session';
import {pendingCalculationStorage} from '../lib/pendingCalculationStorage';
import {submissionId} from '../lib/learning';
import {colors as c} from '../lib/theme';

const titles:Record<ToolKind,string>={name:'Имя',address:'Адрес',car:'Автомобиль'};
const fields:Record<ToolKind,{key:string;label:string;max:number;placeholder?:string}[]>={
 name:[{key:'name',label:'Имя',max:120},{key:'surname',label:'Фамилия · необязательно',max:120}],
 address:[{key:'street',label:'Улица · для подписи результата',max:120},{key:'house_number',label:'Номер дома',max:24,placeholder:'Например, 14А'},{key:'apartment_number',label:'Квартира · необязательно',max:24},{key:'postal_code',label:'Индекс · необязательно',max:24}],
 car:[{key:'car_number',label:'Номер автомобиля',max:13,placeholder:'Например, ABC 123'}],
};
const points=(value:number)=>`${value} ${value%100>=11&&value%100<=14?'баллов':value%10===1?'балл':value%10>=2&&value%10<=4?'балла':'баллов'}`;
const dateLabel=(value:string)=>new Date(value).toLocaleString('ru-RU',{day:'numeric',month:'long',hour:'2-digit',minute:'2-digit'});

export function ToolResult({receipt}:{receipt:ToolReceipt}){
 const r=receipt.results;
 const [selected,setSelected]=useState(0),[method,setMethod]=useState(false),[detail,setDetail]=useState<SchemeInterpretation|null>(null);
 const item=r.items[selected];
 const counts=Array.from({length:9},(_,i)=>({digit:i+1,count:item.tokens.filter(t=>t.value===i+1).length}));
 const max=Math.max(1,...counts.map(v=>v.count));
 function explain(number:number){setDetail({title:`Число ${number}`,value:number,meaning:'',...(number<=9?{knowledgeDigit:number}:{narrationId:`master-${number}`})});}
 return <View style={{gap:20}}>
  <Card tinted><Text style={s.eyebrow}>Ваш сохранённый расчёт</Text><Text style={s.title}>{r.title}</Text><Text selectable style={s.body}>{r.summary}</Text><Text style={s.small}>{dateLabel(receipt.created_at)} · {points(receipt.cost)}</Text>
   <View style={styles.results}>{r.items.map((part,index)=><Pressable key={part.key} accessibilityRole="button" accessibilityState={{selected:selected===index}} accessibilityLabel={`${part.label}: ${part.number}. Показать смысл расчёта`} onPress={()=>setSelected(index)} style={[styles.result,selected===index&&styles.active]}>
    <Text style={styles.number}>{part.number}</Text><Text style={s.label}>{part.label}</Text><Text style={s.small}>{part.source}</Text>
   </Pressable>)}</View>
  </Card>
  <Card><Text style={s.eyebrow}>{item.label} · {item.number}</Text><Text style={s.title}>{item.title}</Text><Text selectable style={s.body}>{item.interpretation}</Text><Text style={s.label}>На что обратить внимание</Text><Text selectable style={s.body}>{item.focus}</Text>
   <NarrationClip key={item.narration_id} id={item.narration_id}/>
   <Button secondary title={`Трактовка числа ${item.number}${item.number<=9?' и его планеты':''}`}  onPress={()=>explain(item.number)}/>
  </Card>
  <Card><Text style={s.title}>Из чего складывается число</Text><Text style={s.small}>{r.kind==='address'?'Каждая цифра введённого значения.':'Каждый символ и его числовое значение.'}</Text>
   <View style={styles.tokens}>{item.tokens.map((token,index)=><View key={index} style={styles.token}><Text style={styles.symbol}>{token.symbol}</Text><Text style={s.small}>{token.value}</Text></View>)}</View>
   {item.steps.map((step,index)=><Text selectable key={index} style={styles.formula}>{step}</Text>)}
   {item.number>9&&<Text style={s.small}>Мастер-число {item.number} сохраняется в этом методе.</Text>}
  </Card>
  <Card><Text style={s.title}>Частота значений</Text><Text style={s.small}>График показывает, сколько раз значение встречается в исходных символах. Нажмите на строку, чтобы открыть трактовку.</Text>
   {counts.map(({digit,count})=><Pressable key={digit} accessibilityRole="button" accessibilityLabel={`Значение ${digit}: ${count}. Открыть трактовку`} onPress={()=>explain(digit)} style={styles.chartRow}>
    <Text style={s.label}>{digit}</Text><View accessibilityRole="progressbar" accessibilityLabel={`Частота ${digit}`} accessibilityValue={{min:0,max,now:count}} style={styles.track}><View style={[styles.fill,{width:`${count/max*100}%`}]}/></View><Text style={styles.count}>{count}</Text>
   </Pressable>)}
   {item.tokens.some(t=>t.value===0)&&<Text style={s.small}>Нули показаны в исходной записи и не увеличивают сумму.</Text>}
  </Card>
  <Button secondary title={method?'Скрыть метод':'Метод расчёта и его озвучка'} onPress={()=>setMethod(!method)}/>
  {method&&<Card><Text selectable style={s.body}>{r.method}</Text><NarrationClip id={`tool-method-${r.kind}`}/></Card>}
  <SavedReportExport document={()=>toolReportDocument(receipt)}/>
  <InterpretationSheet detail={detail} onClose={()=>setDetail(null)} onProfile={()=>router.push('/profile')}/>
 </View>;
}

export default function NumberTools(){
 const {api,user,session,creditNotice}=useSession();const active=useRef(true),scroll=useRef<ScrollView|null>(null);
 const [controller]=useState(()=>createToolController({catalog:()=>api.toolCatalog(),history:()=>api.toolHistory(),calculate:body=>api.calculateTool(body),refreshBalance:()=>session.refresh(),onInsufficientCredits:creditNotice.insufficient,makeId:submissionId,pendingStore:pendingCalculationStorage(user!.id,'tools'),isCurrent:()=>active.current}));
 const state=useSyncExternalStore(controller.subscribe,controller.getSnapshot,controller.getSnapshot);
 const [kind,setKind]=useState<ToolKind>('name'),[inputs,setInputs]=useState<Record<string,string>>({name:user?.name||user?.full_name?.split(' ')[0]||'',surname:user?.surname||''});
 const [form,setForm]=useState(false),[history,setHistory]=useState(false);
 useEffect(()=>{active.current=true;void controller.load();return()=>{active.current=false;};},[controller]);
 useEffect(()=>{if(state.result){setForm(false);scroll.current?.scrollTo({y:0,animated:true});}},[state.result?.id]);
 const price=state.catalog?.[kind],balance=user?.credits_remaining,locked=state.busy||!!state.pending;
 const canCalculate=typeof price==='number'&&typeof balance==='number'&&!state.balanceError;
 const draft=()=>({kind,inputs:Object.fromEntries(fields[kind].map(field=>[field.key,inputs[field.key]||'']))});
 return <Screen scrollRef={scroll}><Heading eyebrow="Ещё о ваших числах" title="Имя, адрес, автомобиль" subtitle="Выберите расчёт. Значения, формула и озвучка останутся в вашей истории."/>
  {state.loading&&!state.catalog&&<Loading/>}
  {!!state.error&&<Notice message={state.error}/>}
  {!!state.balanceError&&<Notice message={`Результат сохранён. ${state.balanceError}`} action="Обновить баланс" onAction={()=>void controller.refreshBalance()}/>}
  {state.pending&&!state.busy&&<Notice message="Ответ ещё не подтверждён. Повторная проверка использует ту же попытку и не списывает баллы второй раз." action="Проверить результат" onAction={()=>void controller.retry()}/>}
  {state.result&&<ToolResult key={state.result.id} receipt={state.result}/>}
  {state.result&&!form&&<Button title="Новый расчёт" secondary disabled={locked} onPress={()=>setForm(true)}/>}
  {(form||!state.result)&&<Card><Text style={s.title}>Что рассчитать</Text><View style={styles.modes}>{(Object.keys(titles) as ToolKind[]).map(value=><Pressable key={value} accessibilityRole="button" accessibilityLabel={titles[value]} accessibilityState={{selected:kind===value,disabled:locked}} disabled={locked} onPress={()=>setKind(value)} style={[styles.mode,kind===value&&{backgroundColor:c.navy}]}><Text style={[s.label,{color:kind===value?'#fff':c.navy,textAlign:'center'}]}>{titles[value]}</Text></Pressable>)}</View>
   {fields[kind].map(field=><Field key={field.key} label={field.label} value={inputs[field.key]||''} maxLength={field.max} placeholder={field.placeholder} editable={!locked} onChangeText={value=>setInputs(old=>({...old,[field.key]:value}))}/>)}
   {kind==='name'&&<Text style={s.small}>Русские или латинские буквы; дефисы и апострофы допустимы. Система 1–9 с отдельной буквой Ё.</Text>}
   {kind==='address'&&<Text style={s.small}>Улица сохраняется в подписи. В расчёте участвуют только цифры дома, квартиры и индекса.</Text>}
   <Text style={s.body}>Стоимость: {typeof price==='number'?points(price):'—'} · баланс: {typeof balance==='number'?points(balance):'—'}</Text>
   {typeof price==='number'&&typeof balance==='number'&&balance<price&&<Button secondary title="Пополнить баллы" onPress={()=>router.push('/top-up')}/>}
   <Button title={price===0?'Рассчитать бесплатно':`Рассчитать за ${typeof price==='number'?points(price):'—'}`} busy={state.busy} disabled={locked||!canCalculate} onPress={()=>void controller.calculate(draft(),balance)}/>
   <Text style={s.small}>Нажатие подтверждает стоимость. Просмотр сохранённого результата и озвучки бесплатный.</Text>
  </Card>}
  <Button secondary title={history?'Скрыть историю':`История расчётов (${state.history.length})`} onPress={()=>setHistory(!history)}/>
  {history&&<Card><Text style={s.title}>Последние 30 расчётов</Text>{!state.history.length&&<Text style={s.body}>Здесь появятся новые расчёты имени, адреса и автомобиля.</Text>}{state.history.map(row=><Button key={row.id} secondary title={`${titles[row.results.kind]} · ${row.results.summary} · ${dateLabel(row.created_at)}`} disabled={state.busy} onPress={()=>{controller.select(row);setHistory(false);}}/>)}</Card>}
  <Button secondary title="Обновить цены и историю" disabled={state.loading||state.busy} onPress={()=>void controller.load()}/><Button secondary title="На главную" onPress={()=>router.replace('/home')}/>
 </Screen>;
}
const styles=StyleSheet.create({
 results:{flexDirection:'row',flexWrap:'wrap',gap:10},result:{flexGrow:1,flexBasis:140,alignItems:'center',gap:8,padding:15,borderWidth:1,borderColor:c.line,borderRadius:16,backgroundColor:c.surface},active:{borderColor:c.accent},number:{fontSize:42,fontWeight:'600',color:c.navy},
 tokens:{flexDirection:'row',flexWrap:'wrap',gap:7},token:{alignItems:'center',minWidth:32,padding:6,borderRadius:8,backgroundColor:c.blue},symbol:{fontSize:18,fontWeight:'600',color:c.navy},formula:{fontSize:17,lineHeight:28,color:c.navy},
 chartRow:{flexDirection:'row',alignItems:'center',gap:14,minHeight:44},track:{flex:1,height:12,borderRadius:6,overflow:'hidden',backgroundColor:c.line},fill:{height:12,borderRadius:6,backgroundColor:c.accent},count:{minWidth:26,textAlign:'right',color:c.navy},
 modes:{flexDirection:'row',flexWrap:'wrap',gap:8},mode:{flexGrow:1,flexBasis:90,minHeight:48,padding:10,alignItems:'center',justifyContent:'center',borderRadius:12,backgroundColor:c.blue},
});
