import {useEffect,useRef,useState,useSyncExternalStore} from 'react';
import {ScrollView,Text,View} from 'react-native';
import {router} from 'expo-router';
import {Button,Card,Field,Heading,Loading,Notice,Screen,s} from '../../components/ui';
import {PersonalReport} from '../../components/numbers/PersonalReport';
import {useSession} from '../../lib/session';
import {createPersonalPaidController} from '../../lib/personalPaid';
import {pendingCalculationStorage} from '../../lib/pendingCalculationStorage';
import {submissionId} from '../../lib/learning';
import {serverDate} from '../../lib/serverDate';
export default function Numbers(){const {user}=useSession();return <NumbersBody key={user?.id}/>;}
function NumbersBody(){
 const {api,user,session,creditNotice}=useSession(),active=useRef(true),scroll=useRef<ScrollView|null>(null);
 const [controller]=useState(()=>createPersonalPaidController({catalog:()=>api.request('/numerology/personal/catalog'),history:()=>api.request('/numerology/personal-numbers/history'),calculate:body=>api.request('/numerology/personal',{method:'POST',body}),makeId:submissionId,refreshBalance:()=>session.refresh(),onInsufficientCredits:creditNotice.insufficient,isCurrent:()=>active.current,pendingStore:pendingCalculationStorage(user!.id,'personal')}));
 const state=useSyncExternalStore(controller.subscribe,controller.getSnapshot,controller.getSnapshot);
 const [date,setDate]=useState(user?.birth_date||''),[form,setForm]=useState(false),[history,setHistory]=useState(false);
 useEffect(()=>{active.current=true;void controller.load();return()=>{active.current=false;};},[controller]);
 useEffect(()=>{if(state.result){setForm(false);scroll.current?.scrollTo({y:0,animated:false});}},[state.result?.id]);
 const price=state.catalog?.personal,balance=user?.credits_remaining,locked=state.busy||!!state.pending;
 const canCalculate=typeof price==='number'&&typeof balance==='number'&&!state.balanceError;
 return <Screen scrollRef={scroll}><Heading title="Ваши числа" subtitle="Персональная схема, расшифровки и графики NumerOM."/>
  {state.loading&&!state.catalog&&<Loading/>}{!!state.error&&<Notice message={state.error}/>}
  {!!state.balanceError&&<Notice message={`Результат сохранён. ${state.balanceError}`} action="Обновить только баланс" onAction={()=>void controller.refreshBalance()}/>}
  {!!state.pending&&!state.busy&&<Notice message="Ответ ещё не подтверждён. Повтор проверит эту же попытку без второго списания, в том числе после перезагрузки." action="Проверить результат" onAction={()=>void controller.retry()}/>}
  {state.result&&<PersonalReport key={state.result.id} result={state.result.view} onProfile={()=>router.push('/profile')}/>}
  {state.result&&!form&&<Button secondary title="Новый расчёт" disabled={locked} onPress={()=>setForm(true)}/>}
  {(form||!state.result)&&<Card><Text style={s.title}>{state.result?'Новый расчёт':'Рассчитать свои числа'}</Text><Field label="Дата рождения для нового расчёта" placeholder="ДД.ММ.ГГГГ" value={date} onChangeText={setDate} keyboardType="numbers-and-punctuation" maxLength={10} editable={!locked}/>
   <Text style={s.body}>Стоимость: {typeof price==='number'?price:'—'} балл. · баланс: {typeof balance==='number'?balance:'—'}</Text>
   {typeof price==='number'&&typeof balance==='number'&&balance<price&&<Button secondary title="Пополнить баллы" onPress={()=>router.push('/top-up')}/>}
   <Button title={price===0?'Рассчитать бесплатно':`Рассчитать · ${price??'—'} балл.`} busy={state.busy} disabled={locked||!canCalculate} onPress={()=>void controller.calculate({kind:'personal',birth_date:date},balance)}/>
   <Text style={s.small}>Нажатие подтверждает стоимость. Просмотр сохранённых схем, расшифровок и озвучек бесплатный.</Text>
  </Card>}
  <Button secondary title={history?'Скрыть историю':`История личных расчётов (${state.history.length})`} onPress={()=>setHistory(!history)}/>
  {history&&<Card><Text style={s.title}>Последние 100 расчётов</Text>{!state.history.length&&<Text style={s.body}>Здесь появятся сохранённые персональные схемы.</Text>}{state.history.map(row=><Button key={row.id} secondary title={`${row.birth_date} · ${serverDate(row.created_at)?.toLocaleString('ru-RU')||'Дата не указана'}`} disabled={state.busy} onPress={()=>{controller.select(row);setHistory(false);}}/>)}</Card>}
  <Button secondary title="Обновить цены и историю" disabled={state.loading||state.busy} onPress={()=>void controller.load()}/>
 </Screen>;
}
