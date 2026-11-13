import {telegramApp,openStarsInvoice} from '../lib/telegram';
import {useCallback,useEffect,useRef,useState} from 'react';
import {AppState,Linking,Platform,ScrollView,Text,View} from 'react-native';
import {FullReportCatalog,FullReportOrder,fullReportCatalog,fullReportOrder,fullReportStatus,validBirthDate,checkoutUrl,starsCheckoutUrl} from '../../../packages/full-report';
import {Button,Card,Field,Heading,Loading,Notice,Screen,s} from '../components/ui';
import {FullReportDocument} from '../components/full-report/FullReportDocument';
import {ReportPreparing} from '../components/full-report/ReportPreparing';
import {ReportProfilePreview} from '../components/full-report/ReportProfilePreview';
import {ReportPreview} from '../../../packages/full-report/profile-preview';
import {useSession} from '../lib/session';
import {submissionId} from '../lib/learning';
import {FullReportAttempt,readReportAttempt,saveReportAttempt} from '../lib/fullReportStorage';
export default function FullReport({orderId,cancelled=false}:{orderId?:string;cancelled?:boolean}){
 const {api,user,session}=useSession();const uid=user!.id;
 const [catalog,setCatalog]=useState<FullReportCatalog|null>(null),[history,setHistory]=useState<FullReportOrder[]>([]),[order,setOrder]=useState<FullReportOrder|null>(null);
 const [attempt,setAttempt]=useState<FullReportAttempt|null>(null),[birth,setBirth]=useState(user?.birth_date||''),[error,setError]=useState(''),[busy,setBusy]=useState(false),[loading,setLoading]=useState(true);
 const [deleting,setDeleting]=useState<string|null>(null);
 const [useProfile,setUseProfile]=useState(true),[preview,setPreview]=useState<ReportPreview|null>(null),[archive,setArchive]=useState<FullReportOrder|null>(null);
 const alive=useRef(true),lock=useRef(false),selection=useRef(0),scroll=useRef<ScrollView|null>(null);
 const isCurrent=useCallback(()=>alive.current&&session.getSnapshot().status==='signedIn'&&session.getSnapshot().user?.id===uid,[session,uid]);
 useEffect(()=>{alive.current=true;return()=>{alive.current=false;selection.current++;};},[]);
 const isTelegram=!!telegramApp(),catalogPath=isTelegram?'/telegram/full-reports/catalog':'/full-reports/catalog';
 const priceLabel=catalog?.currency==='XTR'?`${catalog.amount_total} Stars`:'6,66 €';
 const paymentUrl=(value:unknown)=>isTelegram?starsCheckoutUrl(value):checkoutUrl(value);
 async function openPayment(url:string){if(isTelegram){await openStarsInvoice(url);return;}if(Platform.OS==='web')window.location.assign(url);else await Linking.openURL(url);}
 const refreshHistory=useCallback(async()=>{const raw=await api.request('/full-reports/history') as {orders:unknown[]};if(!Array.isArray(raw.orders))throw new Error('История пока недоступна.');const orders=raw.orders.map(fullReportOrder);if(isCurrent())setHistory(orders);},[api,isCurrent]);
 async function deleteOrder(id:string){
  if(lock.current)return;
  lock.current=true;setBusy(true);setError('');
  try{
   const result=await api.request(`/full-reports/${id}`,{method:'DELETE'}) as {deleted?:boolean};
   if(!result.deleted)throw new Error('Удаление не подтверждено. Повторите попытку.');
   if(!isCurrent())return;
   selection.current++;if(order?.order_id===id){setOrder(null);setArchive(null);}
   if(attempt?.order_id===id){await saveReportAttempt(uid,null);setAttempt(null);}
   setHistory(items=>items.filter(item=>item.order_id!==id));setDeleting(null);
  }catch(e){if(isCurrent())setError(e instanceof Error?e.message:'Не удалось удалить разбор.');}
  finally{lock.current=false;if(isCurrent())setBusy(false);}
 }
 const showOrder=useCallback(async(id:string)=>{const seq=++selection.current;setArchive(null);const found=fullReportOrder(await api.request(`/full-reports/${id}`));if(!isCurrent()||seq!==selection.current)return;setOrder(found);if(['paid','failed','expired'].includes(found.status)){const stored=await readReportAttempt(uid);if(!isCurrent())return;if(stored?.order_id===found.order_id){await saveReportAttempt(uid,null);if(isCurrent())setAttempt(null);}}return found;},[api,uid,isCurrent]);
 useEffect(()=>{void(async()=>{try{const [raw,pending]=await Promise.all([api.request(catalogPath),readReportAttempt(uid)]);if(!isCurrent())return;setCatalog(fullReportCatalog(raw));setAttempt(pending);if(pending){setBirth(pending.birth_date);setUseProfile(!!pending.use_profile);}await refreshHistory();const id=orderId||pending?.order_id;if(id&&/^[a-f0-9]{64}$/.test(id))await showOrder(id);}catch(e){if(isCurrent())setError(e instanceof Error?e.message:'Не удалось загрузить услугу.');}finally{if(isCurrent())setLoading(false);}})();},[api,uid,orderId,refreshHistory,showOrder,isCurrent]);
 const retry=useCallback(async()=>{if(lock.current)return;lock.current=true;setBusy(true);setError('');try{if(order)await showOrder(order.order_id);if(!isCurrent())return;await refreshHistory();if(!isCurrent())return;const next=fullReportCatalog(await api.request(catalogPath));if(isCurrent())setCatalog(next);}catch(e){if(isCurrent())setError(e instanceof Error?e.message:'Не удалось обновить заказ.');}finally{lock.current=false;if(isCurrent())setBusy(false);}},[api,order,showOrder,refreshHistory,isCurrent]);
 useEffect(()=>{const sub=AppState.addEventListener('change',state=>{if(state==='active')void retry();});return()=>sub.remove();},[retry]);
 useEffect(()=>{if(!order||!['creating','pending','processing'].includes(order.status)&&order.report_status!=='preparing')return;const timer=setInterval(()=>void retry(),15000);return()=>clearInterval(timer);},[order,retry]);
 async function openCheckout(){
  if(lock.current||!isCurrent()||!catalog?.enabled)return;
  if(order?.status==='pending'&&paymentUrl(order.url)){
   const url=paymentUrl(order.url)!;
   try{await openPayment(url);}catch{setError('Не удалось открыть оплату. Попробуйте снова.');}
   return;
  }
  if(order&&(['creating','processing','paid'].includes(order.status)||order.status==='pending'))return;
  if(!validBirthDate(attempt?.birth_date||birth)){setError('Укажите существующую дату рождения в формате ДД.ММ.ГГГГ.');return;}
  lock.current=true;setBusy(true);setError('');
  try{if((attempt?.profile_stale&&(!preview||preview.birth_date!==birth))||(!attempt&&useProfile&&birth===user?.birth_date&&(!preview?.profile_fingerprint||preview.birth_date!==birth)))throw new Error('Дождитесь проверки состава разбора или отключите данные профиля.');const pending=(attempt?.profile_stale?{...attempt,profile_stale:false,use_profile:preview!.use_profile,profile_fingerprint:preview!.profile_fingerprint}:attempt)||{request_id:submissionId(),birth_date:birth.trim(),use_profile:useProfile&&birth===user?.birth_date,profile_fingerprint:useProfile&&birth===user?.birth_date?preview!.profile_fingerprint:null};await saveReportAttempt(uid,pending);if(!isCurrent())return;setAttempt(pending);
   const result=fullReportOrder(await api.request(isTelegram?'/telegram/full-reports/checkout':'/full-reports/checkout',{method:'POST',body:{request_id:pending.request_id,birth_date:pending.birth_date,client:'mobile',use_profile:!!pending.use_profile,profile_fingerprint:pending.profile_fingerprint||null}}));
   if(!isCurrent())return;setOrder(result);const saved={...pending,order_id:result.order_id};await saveReportAttempt(uid,saved);if(!isCurrent())return;setAttempt(saved);
   if(['paid','expired','failed'].includes(result.status)){await showOrder(result.order_id);if(isCurrent())await refreshHistory();return;}
   const url=paymentUrl(result.url);if(!url)throw new Error('Ссылка на оплату пока не получена. Проверьте заказ.');
   await openPayment(url);
  }catch(e){if(isCurrent()){
   setError(e instanceof Error?e.message:'Не удалось открыть оплату. Повторите эту же попытку.');
   const failure=e as {code?:string;orderId?:string};try { const saved=['full_report_profile_changed','full_report_attempt_frozen'].includes(failure.code||'')?await readReportAttempt(uid):null;if(!isCurrent())return;
   if(failure.code==='full_report_profile_changed'&&saved){const stale={...saved,profile_stale:true};await saveReportAttempt(uid,stale);if(isCurrent())setAttempt(stale);}
   if(failure.code==='full_report_attempt_frozen'&&failure.orderId&&saved){const frozen={...saved,order_id:failure.orderId,profile_stale:false};await saveReportAttempt(uid,frozen);if(isCurrent()){setAttempt(frozen);await showOrder(failure.orderId);}}
   }catch(recovery){if(isCurrent())setError(recovery instanceof Error?recovery.message:'Не удалось восстановить сохранённую попытку.');}
  }}finally{lock.current=false;if(isCurrent())setBusy(false);}
 }
 async function cancelOrder(){if(lock.current||!order)return;lock.current=true;setBusy(true);setError('');try{const result=fullReportOrder(await api.request(`/full-reports/${order.order_id}/cancel`,{method:'POST',body:{}}));if(!isCurrent())return;setOrder(result);if(['expired','failed','paid'].includes(result.status)){const stored=await readReportAttempt(uid);if(!isCurrent())return;if(stored?.order_id===result.order_id){await saveReportAttempt(uid,null);if(isCurrent())setAttempt(null);}}await refreshHistory();}catch(e){if(isCurrent())setError(e instanceof Error?e.message:'Не удалось проверить отмену.');}finally{lock.current=false;if(isCurrent())setBusy(false);}}
 async function extend(){if(lock.current||!order||!preview?.use_profile||preview.birth_date!==order.birth_date)return;lock.current=true;setBusy(true);setError('');const seq=selection.current;
  try{const next=fullReportOrder(await api.request(`/full-reports/${order.order_id}/extend-profile`,{method:'POST',body:{profile_fingerprint:preview.profile_fingerprint,expected_revision:order.revision||1}}));if(isCurrent()&&selection.current===seq){if(next.is_archived)setArchive(next);else{setOrder(next);setArchive(null);}await refreshHistory();}}
  catch(e){if(isCurrent())setError(e instanceof Error?e.message:'Не удалось дополнить отчёт.');}finally{lock.current=false;if(isCurrent())setBusy(false);}
 }
 async function openRevision(number:number){if(lock.current||!order)return;lock.current=true;setBusy(true);setError('');const seq=selection.current;
  try{const next=fullReportOrder(await api.request(`/full-reports/${order.order_id}/revisions/${number}`));if(isCurrent()&&selection.current===seq)setArchive(next);}
  catch(e){if(isCurrent())setError(e instanceof Error?e.message:'Не удалось открыть версию.');}finally{lock.current=false;if(isCurrent())setBusy(false);}
 }
 if(loading)return <Screen>{orderId?<ReportPreparing birthDate={user?.birth_date} message="Открываем ваш разбор."/>:<Loading/>}</Screen>;
 return <Screen scrollRef={scroll} refreshing={busy} onRefresh={()=>void retry()}>
  <Heading title="Полный разбор" subtitle="Расчёты вашей даты рождения и дополнительных данных профиля в одном отчёте — с объяснениями, авторскими схемами, мужской озвучкой и персональным видео."/>
  {!!error&&<Notice message={error} action="Повторить загрузку" onAction={()=>void retry()}/>}
  {cancelled&&<Text style={s.body}>Вы вернулись из оплаты. Если платёж не завершён, его можно продолжить или отменить ниже.</Text>}
  {!order?.report&&<Card><View style={s.row}><Text style={[s.title,{flex:1}]}>Один разбор</Text><Text style={s.heading}>{priceLabel}</Text></View><Text style={s.body}>Разовая оплата. Без подписки и списания баллов. Готовый отчёт, PDF, аудиоглавы и MP4 остаются в истории вашего аккаунта.</Text>
   {catalog?.includes.map((label,i)=><Text key={i} style={s.small}>• {label}</Text>)}
   <Field label="Дата рождения" value={birth} onChangeText={setBirth} placeholder="ДД.ММ.ГГГГ" maxLength={10} keyboardType="numbers-and-punctuation" editable={!attempt&&!busy}/>
   {!!attempt&&<Text style={s.small}>Сохранена попытка для {attempt.birth_date}. Повторное нажатие откроет тот же заказ.</Text>}
   {catalog?.mode==='test'&&<Text style={s.label}>Сейчас доступна тестовая оплата Stripe. Реальные деньги не списываются.</Text>}
   {catalog&&!catalog.enabled&&<Notice message={catalog.message||'Оплата пока недоступна.'}/>}
   {(!attempt||attempt.profile_stale)&&order?.status!=='paid'&&<ReportProfilePreview birth={birth} useProfile={useProfile} onUseProfile={setUseProfile} onPreview={setPreview} disabled={busy}/>}
   <Button title={attempt||order?.status==='pending'?`Продолжить оплату ${priceLabel}`:`Купить разбор за ${priceLabel}`}  disabled={!catalog?.enabled||!catalog.clients.includes(isTelegram?'telegram':'mobile')||!!order&&(['creating','processing','paid'].includes(order.status)||order.status==='pending'&&!paymentUrl(order.url))} busy={busy} onPress={()=>void openCheckout()}/>
   <Text style={s.small}>Дополнительные поля необязательны. Данные фиксируются при начале оплаты.</Text>
  </Card>}
  {!attempt&&order?.status==='paid'&&<Card><ReportProfilePreview birth={order.birth_date} useProfile={useProfile} onUseProfile={setUseProfile} onPreview={setPreview} disabled={busy}/></Card>}
  {order?.status==='paid'&&preview?.use_profile&&preview.profile_fingerprint!==order.profile_fingerprint&&<Card><Text style={s.body}>Дополните оплаченный разбор текущими данными профиля. Предыдущая версия сохранится; новый текст, озвучка и видео подготовятся заново.</Text><Button title="Дополнить разбор без доплаты" busy={busy} onPress={()=>void extend()}/></Card>}
  {order?.status==='paid'&&!order.report&&<Card tinted><ReportPreparing birthDate={order.birth_date} message={order.message||'Оплата подтверждена. Отчёт готовится; повторная оплата не нужна.'}/></Card>}
  {order&&<Card><Text style={s.title}>{fullReportStatus(order.status,order.report_status)}</Text>{!!order.person&&<Text style={s.body}>{order.person}</Text>}<Text style={s.body}>Дата рождения: {order.birth_date}</Text>{!!order.message&&<Text style={s.body}>{order.message}</Text>}
   {!order.report&&<Button secondary title="Проверить оплату и отчёт" busy={busy} onPress={()=>void retry()}/>}
   {['pending','creating'].includes(order.status)&&<Button secondary title="Отменить незавершённую оплату" busy={busy} onPress={()=>void cancelOrder()}/>}
   {['paid','failed','expired'].includes(order.status)&&<Button secondary title={attempt?'Вернуться к сохранённой попытке':'Разобрать другую дату'} onPress={()=>{selection.current++;setOrder(null);setArchive(null);setBirth(attempt?.birth_date||'');}}/>}
  </Card>}
  {!!order?.previous_revisions?.length&&<Card><Text style={s.title}>Версии разбора</Text><Button secondary title={`Текущая версия ${order.revision||1}`} onPress={()=>setArchive(null)}/>{order.previous_revisions.map(item=><Button key={item.revision} secondary title={`Версия ${item.revision}`} disabled={busy} onPress={()=>void openRevision(item.revision)}/>)}{archive&&<Text style={s.small}>Открыта сохранённая версия {archive.revision}. Аудио и видео доступны в текущей версии.</Text>}</Card>}
  {order?.report&&<FullReportDocument key={`${order.order_id}-${archive?.revision||order.revision||1}`} order={archive||order} archived={!!archive}/>}
  <View style={{gap:12}}><Text style={s.title}>Мои разборы</Text>{history.length===0?<Text style={s.body}>Здесь появятся ваши заказы и готовые отчёты.</Text>:history.map(item=><View key={item.order_id} style={{gap:8}}><Button secondary title={`${item.person?`${item.person} · `:''}${item.birth_date} · ${fullReportStatus(item.status,item.report_status)}`} disabled={busy} onPress={()=>{setError('');void showOrder(item.order_id).then(found=>{
   // The opened report starts at the top of the page, not down at the list it was picked from.
   if(found&&isCurrent())requestAnimationFrame(()=>scroll.current?.scrollTo({y:0,animated:true}));
  }).catch(e=>{if(isCurrent())setError(e instanceof Error?e.message:'Не удалось открыть отчёт.');});}}/>
   {deleting===item.order_id?<><Text style={s.body}>Удалить этот разбор из личного кабинета?</Text><Button title="Да, удалить разбор" busy={busy} onPress={()=>void deleteOrder(item.order_id)}/><Button secondary title="Отмена" disabled={busy} onPress={()=>setDeleting(null)}/></>:<Button secondary title="Удалить разбор" disabled={busy} onPress={()=>setDeleting(item.order_id)}/>}
  </View>)}</View>
 </Screen>;
}
