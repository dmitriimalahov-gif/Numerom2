import React, {useEffect,useRef,useState} from 'react';
import {Dialog,DialogContent,DialogDescription,DialogHeader,DialogTitle} from './ui/dialog';
import {Button} from './ui/button';
import {useAuth} from './AuthContext';
import {api} from '../services/api';
import {paymentCatalog,stripeCheckout} from '@numerom/api-client';
import {useNavigate} from 'react-router-dom';

export default function PaymentModal({isOpen,onClose}){
 const {user}=useAuth();const navigate=useNavigate();const [catalog,setCatalog]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const lock=useRef(false),generation=useRef(0);
 useEffect(()=>{const version=++generation.current;setCatalog(null);setError('');if(!isOpen||!user)return;
  const controller=new AbortController();api.request('/payments/packages',{signal:controller.signal}).then(v=>{if(version===generation.current)setCatalog(paymentCatalog(v));}).catch(e=>{if(!controller.signal.aborted&&version===generation.current)setError(e.message);});
  return()=>{generation.current++;controller.abort();};
 },[isOpen,user?.id]);
 async function start(package_type){
  if(lock.current)return;lock.current=true;setBusy(true);setError('');const version=generation.current;
  try{
   const key='numerom.web.payment.'+user.id;let attempt;try{attempt=JSON.parse(sessionStorage.getItem(key)||'null');}catch{}
   if(attempt&&attempt.package_type!==package_type)throw Error('Есть незавершённая попытка. Откройте её статус перед выбором другого пакета.');
   attempt=attempt||{package_type,request_id:crypto.randomUUID()};sessionStorage.setItem(key,JSON.stringify(attempt));
   const c=stripeCheckout(await api.request('/payments/checkout/session',{method:'POST',body:{...attempt,session_id:undefined,client:'web'}}));
   if(version!==generation.current)return;
   sessionStorage.setItem(key,JSON.stringify({...attempt,session_id:c.session_id}));
   if(c.state!=='pending'){navigate('/payment-success?session_id='+encodeURIComponent(c.session_id));return;}
   window.location.assign(c.url);
  }catch(e){if(version===generation.current)setError(e.message);}finally{lock.current=false;setBusy(false);}
 }
 return <Dialog open={isOpen} onOpenChange={value=>{if(!busy&&!value)onClose();}}><DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto"><DialogHeader><DialogTitle>Пополнить баллы</DialogTitle><DialogDescription>Разовая оплата через Stripe, без автоматического продления.</DialogDescription></DialogHeader>
 {error&&<p role="alert" className="text-red-700">{error}</p>}
 {!catalog&&!error&&<p role="status">Загружаем пакеты…</p>}
 {catalog?.mode==='test'&&<p className="rounded-lg bg-blue-50 p-4">Тестовая оплата: реальные деньги не списываются, рабочий баланс не меняется.</p>}
 {catalog&&!catalog.enabled&&<p role="status">{catalog.message}</p>}
 <div className="grid gap-4 sm:grid-cols-2">{catalog?.packages.map(p=><section key={p.id} className="rounded-xl border p-5 space-y-3"><h3 className="font-semibold">{p.title}</h3><p className="text-2xl">{p.credits} баллов</p><p>{new Intl.NumberFormat('ru-RU',{style:'currency',currency:'EUR'}).format(p.amount_total/100)}</p><p className="text-sm text-slate-600">{p.access_days?`Доступ на ${p.access_days} дней.`:''}{p.consultation?' Персональная консультация мастера.':''}</p><Button disabled={busy||!catalog.enabled||!catalog.clients.includes('web')} onClick={()=>start(p.id)}>{busy?'Открываем…':'Перейти к оплате'}</Button></section>)}</div>
 <a href="/payment-success" className="text-blue-800 underline">Проверить текущую оплату</a>
 </DialogContent></Dialog>;
}
