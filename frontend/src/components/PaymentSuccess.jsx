import React,{useEffect,useRef,useState} from 'react';
import {useSearchParams,useNavigate} from 'react-router-dom';
import {Button} from './ui/button';
import {useAuth} from './AuthContext';
import {api} from '../services/api';
import {paymentReceipt,paymentMessage} from '@numerom/api-client';

export default function PaymentSuccess(){
 const [params]=useSearchParams();
 if(params.get('service')==='full-report')return <FullReportReturn orderId={params.get('order_id')}/>;
 return <CreditPaymentSuccess/>;
}

function FullReportReturn({orderId}){
 const navigate=useNavigate();
 useEffect(()=>{navigate('/dashboard/full-report'+(orderId?'?order_id='+encodeURIComponent(orderId):''),{replace:true});},[navigate,orderId]);
 return <p role="status">Открываем ваш разбор и проверяем подтверждение оплаты…</p>;
}

function CreditPaymentSuccess(){
 const [params]=useSearchParams();const navigate=useNavigate();const {user,refreshProfile}=useAuth();
 const [result,setResult]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[revision,setRevision]=useState(0);
 const generation=useRef(0);
 const refresh=useRef(refreshProfile);refresh.current=refreshProfile;
 const key=user?'numerom.web.payment.'+user.id:null;let saved=null;try{saved=JSON.parse(sessionStorage.getItem(key)||'null');}catch{}
 const sid=params.get('session_id')||saved?.session_id;
 const identity=(user?.id||'')+':'+(sid||'');
 const receipt=result?.identity===identity?result.receipt:null;
 useEffect(()=>{
  generation.current++;if(!user||!sid)return;let active=true,timer,attempts=0;const controller=new AbortController();
  async function poll(){setBusy(true);setError('');try{
   const r=paymentReceipt(await api.request('/payments/checkout/status/'+encodeURIComponent(sid),{signal:controller.signal}));
   if(!active)return;setResult({identity,receipt:r});
   if(['paid','expired','failed'].includes(r.status)){
    let current=null;try{current=JSON.parse(sessionStorage.getItem(key)||'null');}catch{}
    if(current?.session_id===sid)sessionStorage.removeItem(key);
    await refresh.current();
   }else if(++attempts<10)timer=setTimeout(poll,4000);
  }catch(e){if(active)setError(e.message);}finally{if(active)setBusy(false);}}
  void poll();return()=>{generation.current++;active=false;controller.abort();clearTimeout(timer);};
 },[user?.id,sid,key,revision,identity]);
 async function cancel(){const current=generation.current;setBusy(true);setError('');try{const r=paymentReceipt(await api.request('/payments/checkout/'+encodeURIComponent(sid)+'/cancel',{method:'POST',body:{}}));if(current!==generation.current)return;setResult({identity,receipt:r});setRevision(v=>v+1);}catch(e){if(current===generation.current)setError(e.message);}finally{if(current===generation.current)setBusy(false);}}
 return <main className="min-h-screen bg-slate-50 flex items-center justify-center p-5"><section className="w-full max-w-lg rounded-2xl bg-white border p-7 space-y-5"><h1 className="text-2xl font-semibold">Статус оплаты</h1>
 {!user?<p>Войдите в аккаунт NumerOM, чтобы проверить оплату. Подтверждение приходит на сервер автоматически.</p>:!sid?<p>Активная оплата не найдена. Баланс и история доступны в вашем кабинете.</p>:<>
 {receipt&&<><p role="status">{paymentMessage(receipt)}</p><p>{receipt.title} · {new Intl.NumberFormat('ru-RU',{style:'currency',currency:'EUR'}).format(receipt.amount_total/100)}</p></>}
 {!receipt&&busy&&<p role="status">Проверяем подтверждение Stripe…</p>}
 {error&&<p role="alert">{error}</p>}
 <Button disabled={busy} onClick={()=>setRevision(v=>v+1)}>Проверить ещё раз</Button>
 {receipt&&!['paid','expired','failed'].includes(receipt.status)&&<Button variant="outline" disabled={busy} onClick={cancel}>Отменить попытку оплаты</Button>}
 </>}
 <Button variant="outline" onClick={()=>navigate(user?'/dashboard/home':'/')}>Вернуться в NumerOM</Button>
 </section></main>;
}
