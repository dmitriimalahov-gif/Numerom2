import {useCallback,useEffect,useRef,useState} from 'react';
import {AppState,Linking,Platform,Text,View} from 'react-native';
import {router} from 'expo-router';
import {paymentCatalog,stripeCheckout,paymentReceipt,paymentMessage,PaymentCatalog,PaymentReceipt} from '@numerom/api-client';
import {Button,Card,Heading,Loading,Notice,Screen,s} from './ui';
import {useSession} from '../lib/session';
import {submissionId} from '../lib/learning';
import {readPayment,savePayment,PendingPayment} from '../lib/paymentStorage';

const money=(n:number)=>new Intl.NumberFormat('ru-RU',{style:'currency',currency:'EUR'}).format(n/100);
export function TopUp({sessionId,cancelled=false}:{sessionId?:string;cancelled?:boolean}){
 const {api,user,session}=useSession();
 const [catalog,setCatalog]=useState<PaymentCatalog|null>(null),[history,setHistory]=useState<PaymentReceipt[]>([]);
 const [pending,setPending]=useState<PendingPayment|null>(null),[receipt,setReceipt]=useState<PaymentReceipt|null>(null);
 const [error,setError]=useState(''),[busy,setBusy]=useState(false),[loaded,setLoaded]=useState(false);
 const lock=useRef(false),mounted=useRef(true),saved=useRef<PendingPayment|null>(null);
 const uid=user!.id;
 const load=useCallback(async()=>{
  const [c,h]=await Promise.all([api.request('/payments/packages'),api.request<{orders:unknown[]}>('/payments/history')]);
  const nextCatalog=paymentCatalog(c),nextHistory=h.orders.map(paymentReceipt);
  if(mounted.current){setCatalog(nextCatalog);setHistory(nextHistory);setError('');}
 },[api]);
 const apply=useCallback(async(r:PaymentReceipt)=>{
  if(!mounted.current)return;
  setReceipt(r);
  if(['paid','expired','failed'].includes(r.status)){
   // A return for an older order must not erase a newer pending purchase.
   if(saved.current?.session_id===r.session_id){await savePayment(uid,null);saved.current=null;if(mounted.current)setPending(null);}
   await session.refresh();await load();
  }
 },[uid,session,load]);
 const check=useCallback(async(id?:string)=>{
  const sid=id||saved.current?.session_id;if(!sid||lock.current)return;
  lock.current=true;if(mounted.current){setBusy(true);setError('');}
  try{await apply(paymentReceipt(await api.request('/payments/checkout/status/'+encodeURIComponent(sid))));}
  catch(e){if(mounted.current)setError(e instanceof Error?e.message:'Не удалось проверить платёж');}
  finally{lock.current=false;if(mounted.current)setBusy(false);}
 },[api,apply]);
 useEffect(()=>{
  mounted.current=true;
  void (async()=>{try{const p=await readPayment(uid);if(!mounted.current)return;saved.current=p;setPending(p);await load();await check(sessionId||p?.session_id);}catch(e){if(mounted.current)setError(e instanceof Error?e.message:'Не удалось загрузить оплату');}finally{if(mounted.current)setLoaded(true);}})();
  return()=>{mounted.current=false;};
 },[uid,load,check,sessionId]);
 useEffect(()=>{const sub=AppState.addEventListener('change',state=>{if(state==='active')void check(sessionId);});return()=>sub.remove();},[check,sessionId]);
 useEffect(()=>{
  const sid=receipt?.session_id||sessionId||pending?.session_id;
  if(!sid||receipt&&['paid','failed','expired'].includes(receipt.status))return;
  let tries=0;const timer=setInterval(()=>{if(++tries>=10)clearInterval(timer);void check(sid);},4000);
  return()=>clearInterval(timer);
 },[receipt?.status,receipt?.session_id,pending?.session_id,sessionId,check]);
 async function start(package_type:string){
  if(lock.current)return;lock.current=true;setBusy(true);setError('');
  try{
   const attempt=saved.current||{package_type,request_id:submissionId()};
   if(attempt.package_type!==package_type)throw Error('Сначала завершите или отмените текущую попытку.');
   await savePayment(uid,attempt);saved.current=attempt;setPending(attempt);
   const checkout=stripeCheckout(await api.request('/payments/checkout/session',{method:'POST',body:{package_type:attempt.package_type,request_id:attempt.request_id,client:'mobile'}}));
   if(!mounted.current)return;
   const next={...attempt,session_id:checkout.session_id};await savePayment(uid,next);saved.current=next;setPending(next);
   if(checkout.state!=='pending'){await apply(paymentReceipt(await api.request('/payments/checkout/status/'+checkout.session_id)));return;}
   if(Platform.OS==='web')window.location.assign(checkout.url);else await Linking.openURL(checkout.url);
  }catch(e){if(mounted.current)setError(e instanceof Error?e.message:'Не удалось открыть оплату');}
  finally{lock.current=false;if(mounted.current)setBusy(false);}
 }
 async function cancel(){
  const sid=saved.current?.session_id;if(!sid||lock.current)return;lock.current=true;setBusy(true);setError('');
  try{await apply(paymentReceipt(await api.request('/payments/checkout/'+sid+'/cancel',{method:'POST',body:{}})));}
  catch(e){if(mounted.current)setError(e instanceof Error?e.message:'Не удалось отменить попытку');}
  finally{lock.current=false;if(mounted.current)setBusy(false);}
 }
 return <Screen><Heading eyebrow="Баллы NumerOM" title="Пополнить баланс" subtitle="Выберите пакет. Стоимость фиксируется перед переходом в Stripe."/>
 <Card><Text style={s.small}>Ваш баланс</Text><Text style={s.heading}>{user?.credits_remaining??'—'}</Text><Text style={s.small}>баллов</Text></Card>
 {error&&<Notice message={error} action="Повторить проверку" onAction={()=>void (pending?.session_id?check():load().catch(e=>setError(e.message)))}/>}
 {!loaded&&<Loading/>}
 {catalog?.mode==='test'&&<Card tinted><Text style={s.title}>Тестовая оплата</Text><Text style={s.body}>Реальные деньги не списываются. Тестовые баллы хранятся отдельно от рабочего баланса.</Text><Text style={s.small}>Тестовый баланс: {catalog.test_balance} баллов</Text></Card>}
 {cancelled&&!receipt&&<Card><Text style={s.body}>Вы вернулись из Stripe. Проверяем статус — возврат сам по себе не подтверждает оплату или отмену.</Text></Card>}
 {receipt&&<Card tinted><Text accessibilityLiveRegion="polite" style={s.title}>{paymentMessage(receipt)}</Text><Text style={s.body}>{receipt.title} · {money(receipt.amount_total)}</Text></Card>}
 {pending&&<Card><Text style={s.title}>Текущая попытка оплаты</Text><Text style={s.body}>После оплаты вернитесь сюда. Если связь прервалась, продолжите ту же попытку.</Text><Button title="Продолжить в Stripe" busy={busy} onPress={()=>void start(pending.package_type)}/>{pending.session_id&&<><Button title="Проверить оплату" secondary disabled={busy} onPress={()=>void check()}/><Button title="Отменить эту попытку" secondary disabled={busy} onPress={()=>void cancel()}/></>}</Card>}
 {catalog&&!catalog.enabled&&<Notice message={catalog.message||'Оплата временно недоступна.'}/>}
 {catalog?.packages.map(p=><Card key={p.id}><View style={s.row}><Text style={[s.title,{flex:1}]}>{p.title}</Text><Text style={s.title}>{money(p.amount_total)}</Text></View><Text style={s.heading}>{p.credits} <Text style={s.body}>баллов</Text></Text><Text style={s.body}>{p.access_days?`Доступ на ${p.access_days} дней. `:''}{p.consultation?'Персональная консультация мастера. ':''}Разовая оплата, без автоматического продления.</Text><Button title={`Выбрать за ${money(p.amount_total)}`} disabled={!catalog.enabled||busy||!!pending||!catalog.clients.includes('mobile')} onPress={()=>void start(p.id)}/></Card>)}
 {!!history.length&&<><Text style={s.title}>Последние оплаты</Text>{history.slice(0,8).map(r=><Card key={r.order_id}><Text style={s.label}>{r.title} · {money(r.amount_total)}{r.mode==='test'?' · тест':''}</Text><Text style={s.body}>{paymentMessage(r)}</Text>{r.session_id&&!['paid','expired','failed'].includes(r.status)&&<Button title="Проверить этот платёж" secondary disabled={busy} onPress={()=>void check(r.session_id!)}/>}</Card>)}</>}
 <Button title="История баллов" secondary onPress={()=>router.push('/credits')}/>
 <Button title="На главную" secondary onPress={()=>router.replace('/home')}/>
 </Screen>;
}
