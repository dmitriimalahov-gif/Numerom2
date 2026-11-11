import {useCallback,useEffect,useRef,useState} from 'react';
import {Pressable,Text,View} from 'react-native';
import {ApiError} from '@numerom/api-client';
import {Button,Field,Loading,Notice,s} from '../../components/ui';
import {useSession} from '../../lib/session';
import {submissionId} from '../../lib/learning';
import {colors} from '../../lib/theme';

export type Revision={revision:number};
export function useAdminData<T>(path:string){
 const {api,session,user}=useSession();const uid=user?.id,sequence=useRef(0),alive=useRef(true);
 const [result,setResult]=useState<{path:string;owner:string|undefined;data:T|null;error:string|null;loading:boolean}>({path,owner:uid,data:null,error:null,loading:true});
 const valid=useCallback(()=>{const state=session.getSnapshot();return alive.current&&state.status==='signedIn'&&state.user?.id===uid&&!!(state.user?.is_admin||state.user?.is_super_admin);},[session,uid]);
 const reload=useCallback(async()=>{const version=++sequence.current;if(!valid())return;setResult(old=>({path,owner:uid,data:old.path===path&&old.owner===uid?old.data:null,error:null,loading:true}));
  try{const data=await api.request<T>(path);if(version===sequence.current&&valid())setResult({path,owner:uid,data,error:null,loading:false});}
  catch(error){if(version===sequence.current&&valid())setResult({path,owner:uid,data:null,error:error instanceof Error?error.message:'Не удалось загрузить данные.',loading:false});}
 },[api,path,uid,valid]);
 useEffect(()=>{alive.current=true;void reload();return()=>{alive.current=false;sequence.current++;};},[reload]);
 return {data:result.path===path&&result.owner===uid?result.data:null,error:result.path===path&&result.owner===uid?result.error:null,loading:result.path!==path||result.owner!==uid||result.loading,reload};
}
export function ResourceState({loading,error,reload}:{loading:boolean;error:string|null;reload:()=>Promise<void>}){
 return <>{loading&&<Loading/>}{!!error&&<Notice message={error} action="Обновить данные" onAction={()=>void reload()}/>}</>;
}
export function Toggle({label,value,onChange,disabled=false}:{label:string;value:boolean;onChange:(v:boolean)=>void;disabled?:boolean}){
 return <Pressable accessibilityRole="switch" accessibilityLabel={label} accessibilityState={{checked:value,disabled}} disabled={disabled} onPress={()=>onChange(!value)} style={{minHeight:50,padding:14,borderRadius:13,backgroundColor:value?colors.blue:colors.surface,borderWidth:1,borderColor:colors.line,flexDirection:'row',gap:14,alignItems:'center'}}><Text style={[s.body,{flex:1,color:colors.ink}]}>{label}</Text><Text style={s.link}>{value?'Да':'Нет'}</Text></Pressable>;
}
export function IntegerField({label,value,onChange,max=1000000,disabled=false,min=0}:{label:string;value:string;onChange:(v:string)=>void;max?:number;min?:number;disabled?:boolean}){
 return <Field label={`${label} · ${min}–${max}`} value={value} onChangeText={onChange} keyboardType={min<0?'numbers-and-punctuation':'number-pad'} editable={!disabled} maxLength={8}/>;
}
export function integer(value:string,label:string,min=0,max=1000000){
 if(!/^-?\d+$/.test(value.trim()))throw new Error(`${label}: укажите целое число.`);
 const n=Number(value);if(!Number.isSafeInteger(n)||n<min||n>max)throw new Error(`${label}: допустимо от ${min} до ${max}.`);return n;
}
export function reasonText(value:string){if(!value.trim())throw new Error('Укажите причину изменения.');if(value.trim().length>500)throw new Error('Причина должна быть не длиннее 500 символов.');return value.trim();}
export function useAdminMutation(onSaved:()=>Promise<void>|void){
 const {api,session,user}=useSession();const owner=useRef(user?.id);const mounted=useRef(true);const lock=useRef(false);
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[success,setSuccess]=useState(''),[conflict,setConflict]=useState(false);
 const [pending,setPending]=useState<{path:string;body:unknown;method:string;timeoutMs?:number}|null>(null);const retry=useRef<typeof pending>(null);
 const callback=useRef(onSaved);callback.current=onSaved;
 useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;};},[]);
 const current=()=>{const state=session.getSnapshot();return mounted.current&&state.status==='signedIn'&&owner.current===state.user?.id&&!!(state.user?.is_admin||state.user?.is_super_admin);};
 async function execute(item:NonNullable<typeof pending>){
  if(lock.current||!current())return;lock.current=true;setBusy(true);setError('');setSuccess('');setPending(item);retry.current=item;
  try{const result=await api.request<{award_pending?:boolean}>(item.path,{method:item.method,body:item.body,timeoutMs:item.timeoutMs});if(!current())return;if(result?.award_pending===true){setError('Проверка сохранена. Начисление баллов ожидает подтверждения; повторите этот запрос немного позже.');return;}retry.current=null;setPending(null);setSuccess('Изменения сохранены.');await callback.current();}
  catch(e){if(!current())return;const status=e instanceof ApiError?e.status:0;
   if(status>=400&&status<500&&status!==429){retry.current=null;setPending(null);}setConflict(status===409);
   setError(status===429?`${e instanceof Error?e.message:'Слишком частые запросы.'} Подождите перед повтором; исходный запрос сохранён.`:e instanceof Error?e.message:'Не удалось сохранить.');}
  finally{lock.current=false;if(current())setBusy(false);}
 }
 return {busy,error,success,conflict,pending,locked:busy||!!pending||conflict,setError,
  run:(path:string,body:unknown,method='POST',timeoutMs?:number)=>{if(!retry.current&&!conflict)return execute({path,body,method,timeoutMs});return Promise.resolve();},
  retry:()=>retry.current?execute(retry.current):Promise.resolve(),
  versioned:(path:string,revision:number,reason:string,values:Record<string,unknown>)=>{try{return !retry.current&&!conflict?execute({path,method:'POST',body:{...values,request_id:submissionId(),revision,reason:reasonText(reason)}}):Promise.resolve();}catch(e){setError(e instanceof Error?e.message:'Проверьте данные.');return Promise.resolve();}},
 };
}
export function MutationState({state,onReload}:{state:ReturnType<typeof useAdminMutation>;onReload?:()=>void}){
 return <>{!!state.error&&<Notice message={state.error}/>} {!!state.success&&<Text accessibilityLiveRegion="polite" style={{color:colors.green}}>{state.success}</Text>}
 {state.pending&&!state.busy&&<><Text style={s.small}>Подтверждение не получено. Повтор отправляет тот же запрос без изменения данных.</Text><Button title="Проверить сохранение" secondary onPress={()=>void state.retry()}/></>}
 {state.conflict&&onReload&&<><Text style={s.small}>Данные изменились. Загрузите новую версию, затем внесите правку повторно.</Text><Button secondary title="Отбросить правку и загрузить актуальное" onPress={onReload}/></>}</>;
}
export function Reason({value,onChange,disabled=false}:{value:string;onChange:(v:string)=>void;disabled?:boolean}){return <Field label="Причина изменения" value={value} onChangeText={onChange} editable={!disabled} maxLength={500} multiline/>;}
export function nameOf(user:{full_name?:string;name?:string;email?:string}){return user.full_name||user.name||user.email||'Пользователь';}

export type PageInfo={total:number;page:number;page_size:number};
export function Pagination({data,page,onPage,loading=false}:{data:PageInfo|null;page:number;onPage:(page:number)=>void;loading?:boolean}){
 if(!data)return null;return <View style={{gap:10}}><Text style={s.small}>Найдено: {data.total} · страница {page} из {Math.max(1,Math.ceil(data.total/data.page_size))}</Text><View style={s.row}><View style={{flex:1}}><Button secondary title="Предыдущая страница" disabled={loading||page<=1} onPress={()=>onPage(page-1)}/></View><View style={{flex:1}}><Button secondary title="Следующая страница" disabled={loading||page>=10000||page*data.page_size>=data.total} onPress={()=>onPage(page+1)}/></View></View></View>;
}
export function SearchBox({label,value,onChange,onSearch,disabled=false}:{label:string;value:string;onChange:(value:string)=>void;onSearch:()=>void;disabled?:boolean}){
 return <View style={{gap:10}}><Field label={label} value={value} onChangeText={onChange} editable={!disabled} maxLength={100} autoCapitalize="none" returnKeyType="search" onSubmitEditing={onSearch}/><Button secondary title="Найти" disabled={disabled} onPress={onSearch}/></View>;
}
