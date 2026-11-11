import {useState} from 'react';
import {Text,View} from 'react-native';
import {Button,Card,Field,s} from '../../components/ui';
import {useSession} from '../../lib/session';
import {IntegerField,MutationState,Reason,ResourceState,integer,nameOf,reasonText,useAdminData,useAdminMutation} from './common';

type Account={id:string;email:string;name?:string;full_name?:string;is_admin:boolean;is_super_admin:boolean;is_disabled:boolean;credits_remaining:number;level:number};
type History={id:string;action:string;reason:string;created_at:string;before:Record<string,unknown>;after:Record<string,unknown>};
export default function Users(){
 const [query,setQuery]=useState(''),[search,setSearch]=useState(''),[page,setPage]=useState(1),[selected,setSelected]=useState<Account|null>(null),[epoch,setEpoch]=useState(0);
 const list=useAdminData<{users:Account[];total:number;page:number;page_size:number}>(`/admin/manage/users?q=${encodeURIComponent(search)}&page=${page}&page_size=20`);
 return <View style={{gap:18}}><Field label="Найти пользователя по имени или почте" value={query} onChangeText={setQuery} maxLength={200} autoCapitalize="none"/>
  <Button title="Найти" secondary onPress={()=>{setSearch(query.trim());setPage(1);setSelected(null);}}/>
  <ResourceState {...list}/>{list.data&&<Text style={s.small}>Найдено: {list.data.total} · страница {page}</Text>}
  {selected?<><Button title="К списку пользователей" secondary onPress={()=>setSelected(null)}/><AccountEditor key={`${selected.id}-${epoch}`} id={selected.id} onSaved={async()=>{await list.reload();setEpoch(v=>v+1);}}/></>:list.data?.users.map(u=><Card key={u.id}><Text style={s.title}>{nameOf(u)}</Text><Text selectable style={s.body}>{u.email}</Text><Text style={s.small}>{u.is_super_admin?'Владелец':u.is_admin?'Администратор':'Ученик'} · {u.is_disabled?'доступ закрыт':'доступ открыт'} · уровень {u.level} · {u.credits_remaining} балл.</Text><Button title={`Управление: ${nameOf(u)}`} secondary onPress={()=>setSelected(u)}/></Card>)}
  {!selected&&list.data&&<View style={s.row}><View style={{flex:1}}><Button title="Предыдущая" secondary disabled={page<=1||list.loading} onPress={()=>setPage(v=>v-1)}/></View><View style={{flex:1}}><Button title="Следующая" secondary disabled={page*list.data.page_size>=list.data.total||list.loading} onPress={()=>setPage(v=>v+1)}/></View></View>}
 </View>;
}
function AccountEditor({id,onSaved}:{id:string;onSaved:()=>Promise<void>}){
 const data=useAdminData<{user:Account;admin_history:History[]}>(`/admin/manage/users/${encodeURIComponent(id)}`);
 return <><ResourceState {...data}/>{data.data&&<AccountActions key={`${id}-${JSON.stringify(data.data.user)}`} account={data.data.user} history={data.data.admin_history} reload={data.reload} onSaved={onSaved}/>}</>;
}
function AccountActions({account:u,history,reload,onSaved}:{account:Account;history:History[];reload:()=>Promise<void>;onSaved:()=>Promise<void>}){
 const {user:actor}=useSession();const [reason,setReason]=useState(''),[amount,setAmount]=useState(''),[level,setLevel]=useState(String(u.level));
 const [confirm,setConfirm]=useState<{title:string;path:string;body:unknown;method:string}|null>(null);const change=useAdminMutation(onSaved);
 const mayEdit=!!actor?.is_super_admin||(!u.is_super_admin&&(!u.is_admin||actor?.id===u.id));
 const mayAccess=mayEdit&&!u.is_super_admin&&actor?.id!==u.id;
 function prepare(kind:'credits'|'level'|'access'|'role'){
  try{
   const why=reasonText(reason);let path=`/admin/manage/users/${encodeURIComponent(u.id)}`,body:Record<string,unknown>={reason:why},title='',method='PATCH';
   if(kind==='credits'){const delta=integer(amount,'Изменение баланса',-1000000,1000000);if(!delta)throw new Error('Изменение баланса не может быть нулевым.');if(u.credits_remaining+delta<0)throw new Error('Баланс не может стать отрицательным.');path+='/credits';body={...body,amount:delta,expected_balance:u.credits_remaining};title=`Баланс ${u.credits_remaining} → ${u.credits_remaining+delta} балл.`;}
   if(kind==='level'){const next=integer(level,'Уровень',1,100);if(next===u.level)throw new Error('Уровень уже установлен.');path=`/admin/mobile/users/${encodeURIComponent(u.id)}/level`;method='POST';body={...body,level:next,expected_level:u.level};title=`Уровень ${u.level} → ${next}`;}
   if(kind==='access'){path+='/access';body={...body,is_disabled:!u.is_disabled};title=u.is_disabled?'Открыть доступ к аккаунту':'Закрыть доступ к аккаунту';}
   if(kind==='role'){path+='/access';body={...body,is_admin:!u.is_admin};title=u.is_admin?'Снять роль администратора':'Назначить администратором';}
   setConfirm({path,body,title,method});change.setError('');
  }catch(e){change.setError(e instanceof Error?e.message:'Проверьте данные.');}
 }
 return <Card><Text style={s.title}>{nameOf(u)}</Text><Text selectable style={s.body}>{u.email}</Text><Text style={s.small}>Баланс {u.credits_remaining} балл. · уровень {u.level}</Text>
  {!mayEdit&&<Text style={s.body}>Для изменения этого аккаунта нужен владелец платформы.</Text>}
  {mayEdit&&<><Reason value={reason} onChange={setReason} disabled={change.locked||!!confirm}/><Field label="Изменить баланс · например 50 или −10" value={amount} onChangeText={setAmount} keyboardType="numbers-and-punctuation" editable={!change.locked&&!confirm}/><Button secondary title="Проверить изменение баланса" disabled={change.locked||!!confirm} onPress={()=>prepare('credits')}/>
   <IntegerField label="Уровень обучения" value={level} onChange={setLevel} min={1} max={100} disabled={change.locked||!!confirm}/><Button secondary title="Изменить уровень" disabled={change.locked||!!confirm} onPress={()=>prepare('level')}/>
   {mayAccess&&<Button secondary title={u.is_disabled?'Открыть доступ':'Закрыть доступ'} disabled={change.locked||!!confirm} onPress={()=>prepare('access')}/>}
   {mayAccess&&actor?.is_super_admin&&<Button secondary title={u.is_admin?'Снять роль администратора':'Назначить администратором'} disabled={change.locked||!!confirm} onPress={()=>prepare('role')}/>}
  </>}
  {confirm&&<Card tinted><Text style={s.title}>{confirm.title}</Text><Text style={s.body}>{u.email}</Text><Text style={s.small}>Причина: {reason}</Text><Button title="Подтвердить изменение" busy={change.busy} disabled={change.locked} onPress={()=>void change.run(confirm.path,confirm.body,confirm.method)}/><Button secondary title="Отменить правку" disabled={change.busy||!!change.pending} onPress={()=>setConfirm(null)}/></Card>}
  <MutationState state={change} onReload={()=>void onSaved()}/><Button title="Обновить пользователя" secondary disabled={change.busy||!!change.pending} onPress={()=>void reload()}/>
  <Text style={s.title}>История управления</Text>{history.length?history.slice().reverse().map(h=><View key={h.id} style={{gap:5}}><Text style={s.body}>{h.reason}</Text><Text style={s.small}>{new Date(h.created_at).toLocaleString('ru-RU')}</Text><Text selectable style={s.small}>{Object.keys(h.after).map(k=>`${({level:'Уровень',credits_remaining:'Баланс',is_admin:'Администратор',is_disabled:'Доступ закрыт'} as Record<string,string>)[k]||k}: ${String(h.before[k]??'—')} → ${String(h.after[k])}`).join(' · ')}</Text></View>):<Text style={s.small}>Изменений пока нет.</Text>}
 </Card>;
}
