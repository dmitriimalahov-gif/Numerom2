import {useEffect,useRef,useState} from 'react';
import {Text,View} from 'react-native';
import {router} from 'expo-router';
import {Button,Card,Heading,Loading,Notice,Screen,s} from './ui';
import {useSession} from '../lib/session';
import {openStarsInvoice} from '../lib/telegram';
import {submissionId} from '../lib/learning';
type Product={id:string;title:string;credits:number;stars:number|null;enabled:boolean;access_days:number};
type Order={order_id:string;state:string;invoice_url?:string;amount:number};
type Attempt={request_id:string;package_type:string;order?:Order};
export function TelegramTopUp(){
 const {api,user,session}=useSession();
 const [products,setProducts]=useState<Product[]>([]),[message,setMessage]=useState(''),[error,setError]=useState('');
 const [busy,setBusy]=useState(false),[loading,setLoading]=useState(true),[pending,setPending]=useState<Order|null>(null);
 const attempt=useRef<Attempt|null>(null),lock=useRef(false),alive=useRef(true);
 const storageKey='numerom.telegram.payment.'+user!.id;
 function save(value:Attempt|null){
  // Persist BEFORE requesting an invoice: lost responses and reloads reuse the request.
  if(value)window.sessionStorage.setItem(storageKey,JSON.stringify(value));
  else window.sessionStorage.removeItem(storageKey);
  attempt.current=value;
 }
 async function check(order:Order){
  const result=await api.request<Order>('/telegram/payments/orders/'+order.order_id);
  if(!alive.current)return;
  if(result.state==='paid'){
   await session.refresh();
   if(alive.current){save(null);setPending(null);setMessage('Оплата подтверждена. Баллы зачислены.');}
  }else if(result.state==='expired'||result.state==='refunded'){
   save(null);setPending(null);setMessage(result.state==='refunded'?'Платёж возвращён. По баллам обратитесь в поддержку бота.':'Срок оплаты истёк. Можно создать новую попытку.');
  }else{
   if(attempt.current)save({...attempt.current,order:result});
   setPending(result);setMessage('Подтверждение оплаты ещё не получено. Можно продолжить эту же оплату.');
  }
 }
 useEffect(()=>{
  alive.current=true;
  void(async()=>{
   try{
    const r=await api.request<{packages:Product[];message?:string}>('/telegram/payments/catalog');
    if(!alive.current)return;
    setProducts(r.packages);setMessage(r.message||'');
    const raw=window.sessionStorage.getItem(storageKey);
    if(raw){
     const saved:Attempt=JSON.parse(raw);
     if(typeof saved.request_id!=='string'||!r.packages.some(p=>p.id===saved.package_type))throw Error('Не удалось восстановить оплату. Обратитесь в поддержку бота.');
     attempt.current=saved;
     const order=saved.order||await api.request<Order>('/telegram/payments/invoice',{method:'POST',body:{request_id:saved.request_id,package_type:saved.package_type}});
     if(alive.current)await check(order);
    }
   }catch(e){if(alive.current)setError(e instanceof Error?e.message:'Не удалось загрузить оплату.');}
   finally{if(alive.current)setLoading(false);}
  })();
  return()=>{alive.current=false;};
 },[api,storageKey]);
 useEffect(()=>{
  if(!pending)return;
  const timer=setInterval(()=>{if(!lock.current)void check(pending).catch(e=>{if(alive.current)setError(e.message);});},5000);
  return()=>clearInterval(timer);
 },[pending]);
 async function open(order:Order){
  if(!order.invoice_url)throw Error('Ссылка на оплату пока недоступна.');
  const state=await openStarsInvoice(order.invoice_url);
  if(!alive.current)return;
  if(state==='cancelled'||state==='failed'){
   setPending(null);setMessage('Оплата не завершена. При повторе будет использована та же попытка.');
  }else await check(order);
 }
 async function buy(id:string){
  if(lock.current)return;lock.current=true;setBusy(true);setError('');
  try{
   if(attempt.current&&attempt.current.package_type!==id)throw Error('Сначала завершите предыдущую оплату или дождитесь окончания её срока.');
   const saved=attempt.current||{request_id:submissionId(),package_type:id};save(saved);
   const order=await api.request<Order>('/telegram/payments/invoice',{method:'POST',body:{package_type:id,request_id:saved.request_id}});
   if(!alive.current)return;
   save({...saved,order});setPending(order);
   if(order.state!=='pending'){await check(order);return;}
   await open(order);
  }catch(e){if(alive.current)setError(e instanceof Error?e.message:'Не удалось открыть оплату.');}
  finally{lock.current=false;if(alive.current)setBusy(false);}
 }
 return <Screen><Heading title="Пополнить баллы" subtitle="Оплата внутри Telegram через Telegram Stars."/>
 <Card tinted><Text style={s.heading}>{user?.credits_remaining??'—'} баллов</Text></Card>
 {loading&&<Loading/>}{!!error&&<Notice message={error}/>} {!!message&&<Text style={s.body}>{message}</Text>}
 {products.map(p=><Card key={p.id}><Text style={s.title}>{p.title}</Text><Text style={s.heading}>{p.credits} баллов</Text>
 <Text style={s.body}>{p.access_days?`Доступ на ${p.access_days} дней. `:''}Разовая покупка.</Text>
 <Button title={p.stars?`Купить за ${p.stars} Stars`:'Стоимость настраивается'} disabled={!p.enabled||busy||loading||!!pending} onPress={()=>void buy(p.id)}/></Card>)}
 {pending&&<><Button title="Продолжить оплату" disabled={busy} onPress={()=>void buy(attempt.current!.package_type)}/>
 <Button secondary title="Проверить оплату" disabled={busy} onPress={()=>void check(pending).catch(e=>setError(e.message))}/></>}
 <View style={{gap:12}}><Button secondary title="История баллов" onPress={()=>router.push('/credits')}/><Button secondary title="На главную" onPress={()=>router.replace('/home')}/></View></Screen>;
}
