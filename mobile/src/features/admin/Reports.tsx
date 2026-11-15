import {useEffect,useMemo,useState} from 'react';
import {ScrollView,Text,View} from 'react-native';
import {Button,Card,s} from '../../components/ui';
import {submissionId} from '../../lib/learning';
import {MutationState,PageInfo,Pagination,Reason,ResourceState,SearchBox,reasonText,useAdminData,useAdminMutation} from './common';

type Report={id:string;user:{id:string;name:string;email:string};birth_date:string;created_at:string;status:string;revision:number;mode:string;amount_total:number;currency:string;analysis:{status:string;message:string;percent?:number};audio:{ready:number;total:number;review:number;percent?:number;ready_seconds?:number;elapsed_seconds?:number};video:{status:string;message:string;progress?:number;percent?:number;seconds?:number;issue?:string;stalled?:boolean};media_job?:{state?:string;stage?:string;started_at?:number;stage_started_at?:number;updated_at?:number;elapsed_seconds?:number;idle_seconds?:number;stalled?:boolean;error_type?:string;chapter?:number;chapters_total?:number};overall_percent?:number;can_retry:boolean};
type QueueHealth={last_cycle_at?:number;idle_seconds?:number;elapsed_seconds?:number;state?:string;stage?:string;stale?:boolean;failures?:number;outcomes?:Record<string,number>};
const states=[['all','Все'],['paid','Оплаченные'],['pending','Ждут оплаты'],['expired','Завершённые попытки']] as const;
const statusLabels:Record<string,string>={paid:'Оплачен',pending:'Ожидает оплаты',creating:'Создаётся',processing:'Проверяем оплату',expired:'Оплата не завершена',failed:'Ошибка',ready:'Готово',preparing:'Готовится',review:'Нужна проверка',missing:'Ожидает подготовки',waiting_analysis:'Ждёт текста',waiting_audio:'Ждёт озвучки',queued:'В очереди',rendering:'Сборка видео',audio:'Озвучка',analysis:'Разбор',error:'Ошибка',needs_attention:'Нужно внимание'};
function duration(seconds?:number){if(!Number.isFinite(seconds)||seconds===undefined||seconds<0)return'—';const value=Math.floor(seconds),minutes=Math.floor(value/60);return minutes?`${minutes} мин ${value%60} сек`:`${value} сек`;}
function pct(value?:number){return Math.max(0,Math.min(100,Math.round(Number.isFinite(value)?value||0:0)));}
function Progress({value,color='#486da7'}:{value:number;color?:string}){const amount=pct(value);return <View accessibilityRole="progressbar" accessibilityLabel={`Готово ${amount}%`} accessibilityValue={{min:0,max:100,now:amount}} style={{height:7,borderRadius:8,backgroundColor:'#e6ebf2',overflow:'hidden'}}><View style={{height:7,width:`${amount}%`,borderRadius:8,backgroundColor:color}}/></View>;}
function eta(item:Report,now:number){
 if(item.video?.status==='ready')return'Готово';
 if(item.media_job?.state==='needs_attention'||item.video?.status==='failed')return'Остановлено';
 if(item.media_job?.state!=='running')return'Ожидает';
 if(item.media_job?.stalled||item.video?.stalled)return'Нет свежих данных';
 const progress=item.overall_percent;
 const started=item.media_job?.started_at;
 if(!Number.isFinite(progress)||!started||!progress||progress>=100)return'Пока не оценить';
 const remaining=Math.max(0,(now-started)*(100-progress)/progress);
 const finish=new Date((now+remaining)*1000).toLocaleTimeString('ru-RU',{hour:'2-digit',minute:'2-digit'});
 return`~${finish} · ${duration(remaining)}`;
}
function cellStyle(width:number){return{width,paddingHorizontal:9,paddingVertical:8,justifyContent:'center' as const,borderRightWidth:1,borderColor:'#e6ebf2'};}

export default function Reports(){
 const [q,setQ]=useState(''),[search,setSearch]=useState(''),[page,setPage]=useState(1),[state,setState]=useState('all'),[selected,setSelected]=useState<Report|null>(null);
 const list=useAdminData<PageInfo&{reports:Report[];media_queue?:QueueHealth}>(`/admin/mobile/reports?page=${page}&page_size=20&q=${encodeURIComponent(search)}&state=${state}`);
 const reports=list.data?.reports||[];
 useEffect(()=>{const timer=setInterval(()=>{if(state==='paid')void list.reload();},6000);return()=>clearInterval(timer);},[list.reload,state]);
 const stats=useMemo(()=>{const reports=list.data?.reports||[];const attention=(x:Report)=>x.video?.status==='failed'||!!x.audio?.review||!!x.media_job?.stalled||x.media_job?.state==='needs_attention';const ready=(x:Report)=>x.video?.status==='ready';const video=(x:Report)=>!attention(x)&&!ready(x)&&x.audio?.total>0&&x.audio.ready===x.audio.total&&(x.video?.status==='rendering'||x.media_job?.stage==='rendering');const audio=(x:Report)=>!attention(x)&&!ready(x)&&!video(x)&&x.analysis?.status==='ready'&&x.audio?.ready<x.audio?.total;const analysis=(x:Report)=>!attention(x)&&!ready(x)&&!video(x)&&!audio(x)&&x.analysis?.status!=='ready';return{audio:reports.reduce((n,x)=>n+(x.audio?.ready||0),0),audioTotal:reports.reduce((n,x)=>n+(x.audio?.total||0),0),videoReady:reports.filter(ready).length,rendering:reports.filter(video).length,attention:reports.filter(attention).length,stages:[['Текст',reports.filter(analysis).length,'#486da7'],['Озвучка',reports.filter(audio).length,'#348d82'],['Видео',reports.filter(video).length,'#7864a3'],['Готово',reports.filter(ready).length,'#46845c'],['Внимание',reports.filter(attention).length,'#b05d54']] as [string,number,string][]};},[list.data]);
 async function reload(){await list.reload();setSelected(null);}
 return <View style={{gap:18}}>
  <Text style={s.title}>Живая очередь озвучки и видео</Text><Text style={s.body}>Состояние оплаченных разборов обновляется каждые 6 секунд. График показывает текущую страницу списка.</Text>
  {state==='paid'&&<Card><Text style={s.label}>Озвучка на странице: {stats.audio}/{stats.audioTotal} · {stats.audioTotal?pct(stats.audio*100/stats.audioTotal):0}%</Text><Progress value={stats.audioTotal?stats.audio*100/stats.audioTotal:0} color="#348d82"/><Text style={s.label}>Распределение заказов по этапам · текущая страница</Text>{stats.stages.map(([label,count,color])=><View key={label} accessibilityLabel={`${label}: ${count}`} style={{gap:4}}><View style={{flexDirection:'row',justifyContent:'space-between'}}><Text style={s.small}>{label}</Text><Text style={s.small}>{count}</Text></View><View style={{height:6,borderRadius:8,backgroundColor:'#e6ebf2',overflow:'hidden'}}><View style={{height:6,width:`${pct(count*10)}%`,backgroundColor:color}}/></View></View>)}<Text style={s.label}>Видео готово: {stats.videoReady} · собирается: {stats.rendering} · требуют внимания: {stats.attention}</Text>{list.data?.media_queue&&<Text style={s.small}>{list.data.media_queue.state==='running'?`Mac: ${statusLabels[list.data.media_queue.stage||'']||'обработка очереди'} · этап ${duration(list.data.media_queue.elapsed_seconds)} · отметка ${duration(list.data.media_queue.idle_seconds)} назад`:`Последний цикл Mac: ${list.data.media_queue.last_cycle_at?duration(Math.max(0,Date.now()/1000-list.data.media_queue.last_cycle_at))+' назад':'нет отметки'}`} · ошибок: {list.data.media_queue.failures||0}{list.data.media_queue.stale?' · давно нет обновления':''}</Text>}</Card>}
  <SearchBox label="Найти разбор по ученику или номеру заказа" value={q} onChange={setQ} onSearch={()=>{setSearch(q.trim());setPage(1);setSelected(null);}}/>
  <View style={{flexDirection:'row',flexWrap:'wrap',gap:8}}>{states.map(([id,title])=><Button key={id} secondary title={`${state===id?'✓ ':''}${title}`} onPress={()=>{setState(id);setPage(1);setSelected(null);}}/>)}</View><ResourceState {...list}/>
  {list.data?.reports.length===0&&<Card><Text style={s.body}>По этому запросу разборов нет.</Text></Card>}
  {reports.length>0&&<ScrollView horizontal showsHorizontalScrollIndicator><View style={{minWidth:1210,borderWidth:1,borderColor:'#dce3eb',borderRadius:12,overflow:'hidden'}}>
   <View style={{flexDirection:'row',backgroundColor:'#edf2f7',borderBottomWidth:1,borderColor:'#dce3eb'}}>
    {(['Заказ / клиент','Этап','Текст','Озвучка / время','Видео / время','Завершение','Ошибка / обновление'] as const).map((label,i)=><Text key={label} style={[s.label,cellStyle([210,120,100,175,175,165,265][i]),{fontWeight:'700'}]}>{label}</Text>)}
   </View>
   {reports.map((item,index)=>{
    const voicePct=pct(item.audio.percent??(item.audio.total?item.audio.ready*100/item.audio.total:0));const videoPct=pct(item.video.percent??item.video.progress);const active=item.media_job?.stage;const now=Date.now()/1000;const elapsed=item.media_job?.stage_started_at?Math.max(0,now-item.media_job.stage_started_at):item.media_job?.elapsed_seconds;const stale=!!item.media_job?.stalled||!!item.video.stalled;const problem=item.video.issue||item.media_job?.error_type||(item.audio.review?`Проверить фрагменты: ${item.audio.review}`:item.analysis.status==='review'?item.analysis.message:stale?'Нет обновлений':'—');
    return <View key={item.id} accessibilityLabel={`Заказ ${item.id}, ${statusLabels[item.status]||item.status}, текст ${item.analysis.percent||0}%, озвучка ${voicePct}%, видео ${videoPct}%, завершение ${eta(item,now)}`} style={{flexDirection:'row',minHeight:68,backgroundColor:index%2?'#ffffff':'#fafbfd',borderBottomWidth:1,borderColor:'#e6ebf2'}}>
     <View style={cellStyle(210)}><Text numberOfLines={1} style={s.label}>{item.user.name||item.user.email||'Ученик'}</Text><Text numberOfLines={1} style={s.small}>{item.birth_date} · {new Date(item.created_at).toLocaleDateString('ru-RU')}</Text><Text numberOfLines={1} selectable style={s.small}>Заказ {item.id}</Text><Text style={s.small}>{item.mode==='test'?'ТЕСТ':'Оплачен'} · {(item.amount_total/100).toLocaleString('ru-RU',{style:'currency',currency:item.currency.toUpperCase()})} · v{item.revision}</Text></View>
     <View style={cellStyle(120)}><Text style={s.label}>{statusLabels[active||item.media_job?.state||item.status]||active||item.status}</Text><Text style={s.small}>{duration(elapsed)} на этапе</Text></View>
     <View style={cellStyle(100)}><Text style={s.label}>{statusLabels[item.analysis.status]||item.analysis.status}</Text><Text style={s.small}>{pct(item.analysis.percent)}%</Text></View>
     <View style={[cellStyle(175),{gap:5}]}><Text style={s.label}>{item.audio.ready}/{item.audio.total} · {voicePct}%</Text><Progress value={voicePct} color="#348d82"/><Text style={s.small}>{duration(item.audio.ready_seconds)} готово</Text></View>
     <View style={[cellStyle(175),{gap:5}]}><Text style={s.label}>{statusLabels[item.video.status]||item.video.status} · {videoPct}%</Text><Progress value={videoPct} color="#7864a3"/><Text style={s.small}>{item.video.status==='ready'?duration(item.video.seconds):duration(item.video.seconds||item.media_job?.elapsed_seconds)}{item.video.status==='rendering'?' · в работе':''}</Text></View>
     <View style={cellStyle(165)}><Text style={s.label}>{eta(item,now)}</Text><Text style={s.small}>{item.media_job?.state==='running'&&item.overall_percent?`общий прогресс ${pct(item.overall_percent)}% · оценка приблизительная`:'по текущему статусу'}</Text></View>
     <View style={cellStyle(265)}><Text numberOfLines={2} style={[s.small,(problem!=='—'?{color:'#a0443b'}:{})]}>{problem}</Text><Text style={s.small}>{item.media_job?.updated_at?`обновлено ${duration(Math.max(0,now-item.media_job.updated_at))} назад`:'нет отметки обработки'}</Text>{item.can_retry&&<Button secondary title="Повторить подготовку" onPress={()=>setSelected(item)}/>}{selected?.id===item.id&&<ReportRetry key={`${item.id}-${item.revision}`} item={item} reload={reload}/>}</View>
    </View>;
   })}
  </View></ScrollView>}
  <Pagination data={list.data} page={page} onPage={value=>{setPage(value);setSelected(null);}} loading={list.loading}/><Button secondary title="Обновить состояния" disabled={list.loading} onPress={()=>void reload()}/>
 </View>;
}

export function ReportRetry({item,reload}:{item:Report;reload:()=>Promise<void>}){
 const [reason,setReason]=useState('');const change=useAdminMutation(reload);
 function run(){try{const why=reasonText(reason);void change.run(`/admin/mobile/reports/${item.id}/retry`,{request_id:submissionId(),expected_revision:item.revision,reason:why});}catch(error){change.setError(error instanceof Error?error.message:'Укажите причину.');}}
 return <View style={{gap:12}}><Reason value={reason} onChange={setReason} disabled={change.locked}/><Button title="Подтвердить повтор подготовки" busy={change.busy} disabled={change.locked} onPress={run}/><MutationState state={change} onReload={()=>void reload()}/></View>;
}
