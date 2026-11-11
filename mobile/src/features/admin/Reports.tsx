import {useState} from 'react';
import {Text,View} from 'react-native';
import {Button,Card,s} from '../../components/ui';
import {submissionId} from '../../lib/learning';
import {MutationState,PageInfo,Pagination,Reason,ResourceState,SearchBox,reasonText,useAdminData,useAdminMutation} from './common';
type Report={id:string;user:{id:string;name:string;email:string};birth_date:string;created_at:string;status:string;revision:number;mode:string;amount_total:number;currency:string;analysis:{status:string;message:string};audio:{ready:number;total:number;review:number};video:{status:string;message:string;progress?:number};can_retry:boolean};
const states=[['all','Все'],['paid','Оплаченные'],['pending','Ждут оплаты'],['expired','Завершённые попытки']] as const;
const statusLabels:Record<string,string>={paid:'Оплачен',pending:'Ожидает оплаты',creating:'Создаётся',processing:'Проверяем оплату',expired:'Оплата не завершена',failed:'Подготовка остановлена',ready:'Готово',preparing:'Готовится',review:'Нужна повторная подготовка',missing:'Ожидает подготовки',waiting_analysis:'Ожидает текст',waiting_audio:'Ожидает озвучку',queued:'В очереди',rendering:'Создаётся видео'};
export default function Reports(){
 const [q,setQ]=useState(''),[search,setSearch]=useState(''),[page,setPage]=useState(1),[state,setState]=useState('all'),[selected,setSelected]=useState<Report|null>(null);
 const list=useAdminData<PageInfo&{reports:Report[]}>(`/admin/mobile/reports?page=${page}&page_size=10&q=${encodeURIComponent(search)}&state=${state}`);
 async function reload(){await list.reload();setSelected(null);}
 return <View style={{gap:18}}><Text style={s.title}>Подготовка полных разборов</Text><Text style={s.body}>Состояние текста, озвучки и видео. Повтор подготовки не создаёт новую оплату.</Text><SearchBox label="Найти разбор по ученику или номеру заказа" value={q} onChange={setQ} onSearch={()=>{setSearch(q.trim());setPage(1);setSelected(null);}}/><View style={{flexDirection:'row',flexWrap:'wrap',gap:8}}>{states.map(([id,title])=><Button key={id} secondary title={`${state===id?'✓ ':''}${title}`} onPress={()=>{setState(id);setPage(1);setSelected(null);}}/>)}</View><ResourceState {...list}/>
  {list.data?.reports.length===0&&<Card><Text style={s.body}>По этому запросу разборов нет.</Text></Card>}
  {list.data?.reports.map(item=><Card key={item.id}><Text style={s.title}>{item.user.name||item.user.email||'Ученик'}</Text><Text selectable style={s.small}>{item.user.email}</Text><Text style={s.body}>{item.birth_date} · {statusLabels[item.status]||'Проверяем состояние'}</Text><Text style={s.small}>{(item.amount_total/100).toLocaleString('ru-RU',{style:'currency',currency:item.currency.toUpperCase()})} · {item.mode==='test'?'TEST · тестовая оплата':'LIVE · реальная оплата'} · версия {item.revision}</Text><Text style={s.label}>Текст: {statusLabels[item.analysis.status]||'Ожидает подготовки'}</Text>{!!item.analysis.message&&<Text style={s.small}>{item.analysis.message}</Text>}<Text style={s.label}>Озвучка: {item.audio.ready} из {item.audio.total}{item.audio.review?` · требуется проверка: ${item.audio.review}`:''}</Text><Text style={s.label}>Видео: {statusLabels[item.video.status]||'Ожидает подготовки'}{typeof item.video.progress==='number'?` · ${Math.round(Math.min(100,Math.max(0,item.video.progress)))}%`:''}</Text>{!!item.video.message&&<Text style={s.small}>{item.video.message}</Text>}
   {item.can_retry&&<Button secondary title="Повторить подготовку" onPress={()=>setSelected(item)}/>}<Text selectable style={s.small}>Заказ {item.id}</Text>
   {selected?.id===item.id&&<ReportRetry key={`${item.id}-${item.revision}`} item={item} reload={reload}/>}</Card>)}
  <Pagination data={list.data} page={page} onPage={value=>{setPage(value);setSelected(null);}} loading={list.loading}/><Button secondary title="Обновить состояния" disabled={list.loading} onPress={()=>void reload()}/>
 </View>;
}
export function ReportRetry({item,reload}:{item:Report;reload:()=>Promise<void>}){
 const [reason,setReason]=useState('');const change=useAdminMutation(reload);
 function run(){try{const why=reasonText(reason);void change.run(`/admin/mobile/reports/${item.id}/retry`,{request_id:submissionId(),expected_revision:item.revision,reason:why});}catch(error){change.setError(error instanceof Error?error.message:'Укажите причину.');}}
 return <View style={{gap:12}}><Reason value={reason} onChange={setReason} disabled={change.locked}/><Button title="Подтвердить повтор подготовки" busy={change.busy} disabled={change.locked} onPress={run}/><MutationState state={change} onReload={()=>void reload()}/></View>;
}
