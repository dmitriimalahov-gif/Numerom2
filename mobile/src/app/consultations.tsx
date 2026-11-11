import {useCallback,useEffect,useRef,useState} from 'react';
import {Text,View} from 'react-native';
import {router} from 'expo-router';
import {Button,Card,Heading,Loading,Notice,Screen,s} from '../components/ui';
import {useSession} from '../lib/session';
import {useMaterialAccess} from '../lib/useMaterialAccess';
type Consultation={id:string;title:string;description:string;cost_credits:number|null;is_purchased:boolean;has_video:boolean;has_pdf:boolean};
export default function ConsultationRoute(){
 const {user,status}=useSession();
 if(status==='loading')return <Screen><Loading/></Screen>;
 if(status!=='signedIn')return <Screen><Heading title="Ваши консультации" subtitle="Войдите, чтобы открыть назначенные вам материалы."/><Button title="Войти" onPress={()=>router.replace('/')}/></Screen>;
 return <ConsultationList key={user!.id}/>;
}
function ConsultationList(){
 const {api,user,session,creditNotice}=useSession();const [items,setItems]=useState<Consultation[]>([]),[loaded,setLoaded]=useState(false),[error,setError]=useState(''),[buying,setBusy]=useState(false),[confirm,setConfirm]=useState<string|null>(null);
 const media=useMaterialAccess(),busy=buying||media.opening!==null;
 const active=useRef(true),lock=useRef(false);
 const load=useCallback(async()=>{
  try{const data=await api.request<{consultations:Consultation[]}>('/student/consultations');if(!active.current)return;setItems(data.consultations);setError('');setLoaded(true);}
  catch(e){if(active.current){setError(e instanceof Error?e.message:'Не удалось загрузить консультации');setLoaded(true);}}
 },[api]);
 useEffect(()=>{active.current=true;void load();return()=>{active.current=false;};},[load]);
 function hasCredits(item:Consultation){
  const balance=user?.credits_remaining,cost=item.cost_credits;
  if(typeof balance!=='number'||typeof cost!=='number')return false;
  if(balance<cost){creditNotice.insufficient({balance,cost});return false;}
  return true;
 }
 async function purchase(item:Consultation){
  if(!hasCredits(item))return;
  if(lock.current||media.isOpening())return;lock.current=true;setBusy(true);setError('');
  try{const result=await api.request<Consultation>('/student/consultations/'+encodeURIComponent(item.id)+'/purchase',{method:'POST',body:{expected_cost:item.cost_credits}});if(!active.current)return;if(!result.is_purchased)throw Error('Подтверждение доступа пока не получено');setItems(old=>old.map(c=>c.id===result.id?result:c));setConfirm(null);await session.refresh();}
  catch(e){if(active.current)setError(e instanceof Error?e.message:'Не удалось открыть доступ');}
  finally{lock.current=false;if(active.current)setBusy(false);}
 }
 async function open(item:Consultation,kind:'video'|'pdf'){
  if(lock.current)return;setError('');
  await media.open(`${item.id}:${kind}`,async signal=>(await api.request<{url:string}>('/student/consultations/'+encodeURIComponent(item.id)+'/'+kind+'/access',{signal})).url);
 }
 return <Screen><Heading eyebrow="Личная работа с мастером" title="Консультации" subtitle="Назначенные вам разборы, записи и материалы."/>
 <Card><Text style={s.small}>Ваш баланс</Text><Text style={s.heading}>{user?.credits_remaining??'—'} <Text style={s.body}>баллов</Text></Text></Card>
 {(error||media.error)&&<Notice message={error||media.error} action="Обновить список" onAction={()=>void load()}/>}
 {!loaded&&<Loading/>}
 {loaded&&!error&&!items.length&&<Card tinted><Text style={s.title}>Пока нет назначенных консультаций</Text><Text style={s.body}>После назначения мастером консультация появится здесь. Если материалы готовятся, её статус будет виден в этом разделе.</Text></Card>}
 {items.map(item=><Card key={item.id}><Text style={s.title}>{item.title}</Text>{!!item.description&&<Text style={s.body}>{item.description}</Text>}
 {item.is_purchased?<><Text style={s.label}>Доступ открыт</Text>{!item.has_video&&!item.has_pdf&&<Text style={s.body}>Материалы готовятся. Обновите список позже.</Text>}{item.has_video&&<Button title="Открыть видеоконсультацию" disabled={busy} onPress={()=>void open(item,'video')}/>} {item.has_pdf&&<Button title="Открыть PDF-разбор" secondary disabled={busy} onPress={()=>void open(item,'pdf')}/>}</>:<>
 <Text style={s.heading}>{item.cost_credits??'—'} <Text style={s.body}>баллов</Text></Text>
 {item.cost_credits===null?<Text style={s.body}>Стоимость уточняется.</Text>:confirm===item.id?<View style={{gap:12}}><Text style={s.body}>Подтвердите списание {item.cost_credits} баллов за эту консультацию. Повторный просмотр будет бесплатным.</Text><Button title={`Подтвердить · ${item.cost_credits} баллов`} busy={busy} onPress={()=>void purchase(item)}/><Button title="Вернуться к списку" secondary disabled={busy} onPress={()=>setConfirm(null)}/></View>:<Button title="Открыть доступ за баллы" disabled={busy||typeof user?.credits_remaining!=='number'} onPress={()=>{if(hasCredits(item))setConfirm(item.id);}}/>}
 {item.cost_credits!==null&&(user?.credits_remaining??0)<item.cost_credits&&<Text style={s.small}>На балансе недостаточно баллов.</Text>}
 </>}
 </Card>)}
 <Button title="Обновить консультации" secondary disabled={busy} onPress={()=>void load()}/><Button title="Пополнить баллы" onPress={()=>router.push('/top-up')}/><Button title="На главную" secondary onPress={()=>router.replace('/home')}/>
 </Screen>;
}
