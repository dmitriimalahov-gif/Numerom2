import {useEffect,useRef,useState} from 'react';
import {Platform,Pressable,Text,View} from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import {File as LocalFile} from 'expo-file-system';
import type {ApiClient} from '@numerom/api-client';
import {Button,Loading,Notice,s} from '../ui';
import {backendUrl,useSession} from '../../lib/session';
import {submissionId} from '../../lib/learning';
import {useMaterialAccess} from '../../lib/useMaterialAccess';

const MAX=5*1024*1024;
type Attachment={id:string;name:string;mime:string;size:number;submitted:boolean};
type Upload={request_id:string;name:string;content_base64:string};
const message=(e:unknown)=>e instanceof Error?e.message:'Не удалось загрузить файл. Попробуйте ещё раз.';
function rows(value:unknown):Attachment[]{
 const files=(value as {files?:unknown})?.files;
 if(!Array.isArray(files)||files.length>3||files.some(f=>!f||! /^[a-f0-9]{64}$/.test(f.id)||typeof f.name!=='string'||!Number.isInteger(f.size)||f.size<1||f.size>MAX))throw new Error('Не удалось прочитать список вложений.');
 return files;
}
function fileData(asset:DocumentPicker.DocumentPickerAsset):Promise<string>{
 if(Platform.OS==='web'){
  if(!asset.file||asset.file.size<1||asset.file.size>MAX)throw new Error('Выберите файл размером до 5 МБ.');
  return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]||'');reader.onerror=()=>reject(new Error('Не удалось прочитать выбранный файл.'));reader.readAsDataURL(asset.file!);});
 }
 const file=new LocalFile(asset.uri);
 if(file.size<1||file.size>MAX)throw new Error('Выберите файл размером до 5 МБ.');
 return file.base64();
}
export function useExerciseAttachments(api:ApiClient,lesson:string,exercise:string){
 const {session,user}=useSession();const owner=useRef(user?.id).current;
 const media=useMaterialAccess();
 const active=useRef(true),busyRef=useRef(false),pending=useRef<Upload|null>(null),started=useRef(false);
 const [files,setFiles]=useState<Attachment[]>([]),[selected,setSelected]=useState<string[]>([]),[ready,setReady]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const path=`/student/exercise-attachments/${encodeURIComponent(lesson)}/${encodeURIComponent(exercise)}`;
 const current=()=>active.current&&session.getSnapshot().user?.id===owner;
 const load=async()=>{
  try{const value=rows(await api.request(path));if(!current())return;setFiles(value);setReady(true);setError('');if(!started.current){setSelected(value.map(f=>f.id));started.current=true;}}
  catch(e){if(current())setError(message(e));}
 };
 useEffect(()=>{active.current=true;void load();return()=>{active.current=false;pending.current=null;};},[api,path]);
 const run=async(action:()=>Promise<void>)=>{if(busyRef.current||media.isOpening())return;busyRef.current=true;setBusy(true);setError('');try{await action();}catch(e){if(current())setError(message(e));}finally{busyRef.current=false;if(current())setBusy(false);}};
 const send=async()=>{
  const body=pending.current;if(!body)return;
  let result:{file:{id:string}};
  try{result=await api.request<{file:{id:string}}>(path,{method:'POST',body,timeoutMs:60000});}
  catch(error){const status=(error as {status?:number})?.status;if([400,401,403,404,409,410,413,415,422].includes(status||0))pending.current=null;throw error;}
  if(!/^[a-f0-9]{64}$/.test(result?.file?.id))throw new Error('Сервер не подтвердил файл. Повторите загрузку.');
  if(!current())return;
  pending.current=null;setSelected(old=>[...new Set([...old,result.file.id])]);await load();
 };
 const pick=()=>run(async()=>{
  if(pending.current){await send();return;}
  const result=await DocumentPicker.getDocumentAsync({type:['application/pdf','image/png','image/jpeg'],multiple:false,copyToCacheDirectory:true,base64:false});
  if(result.canceled||!current())return;
  const asset=result.assets[0];if(!asset||asset.size!==undefined&&(asset.size<1||asset.size>MAX))throw new Error('Выберите файл размером до 5 МБ.');
  const content_base64=await fileData(asset);if(!current())return;
  pending.current={request_id:submissionId(),name:asset.name.slice(0,180),content_base64};await send();
 });
 const remove=(id:string)=>run(async()=>{await api.request(`${path}/${id}/remove`,{method:'POST',body:{}});if(current())setSelected(old=>old.filter(item=>item!==id));await load();});
 const open=(id:string)=>{
  if(busyRef.current)return Promise.resolve();setError('');
  return media.open(id,async signal=>{
  const result=await api.request<{url:string}>(`/student/exercise-attachment-access/${id}`,{signal});const url=new URL(result.url);
  if(url.protocol!=='https:'||url.origin!==new URL(backendUrl).origin||!url.pathname.startsWith('/api/student/exercise-attachment-media/'))throw new Error('Адрес вложения недоступен.');
  return url.toString();
 });};
 const toggle=(id:string)=>setSelected(old=>old.includes(id)?old.filter(item=>item!==id):[...old,id]);
 const saved=()=>{setFiles(old=>old.map(file=>({...file,submitted:selected.includes(file.id)})));};
 return {files,selected,ready,busy:busy||media.opening!==null,error:error||media.error,pending:!!pending.current,pick,remove,open,toggle,load,saved};
}
export function ExerciseAttachments({state,disabled=false}:{state:ReturnType<typeof useExerciseAttachments>;disabled?:boolean}){
 return <View style={{gap:12}}><Text style={s.label}>Вложения к ответу</Text><Text style={s.small}>До трёх файлов PDF, PNG или JPEG, каждый до 5 МБ. До отправки ответа файлы видны только вам.</Text>
 {!state.ready&&!state.error&&<Loading/>}
 {state.files.map(file=><View key={file.id} style={{gap:8}}>
  <Pressable accessibilityRole="checkbox" accessibilityLabel={`Отправить файл ${file.name}`} accessibilityState={{checked:state.selected.includes(file.id),disabled:disabled||state.busy}} disabled={disabled||state.busy} onPress={()=>state.toggle(file.id)} style={{padding:12,borderWidth:1,borderColor:state.selected.includes(file.id)?'#183B72':'#D5DDE8',borderRadius:12}}><Text style={s.body}>{state.selected.includes(file.id)?'✓ ':''}{file.name}</Text><Text style={s.small}>{(file.size/1024/1024).toLocaleString('ru-RU',{maximumFractionDigits:2})} МБ · {file.submitted?'Отправлен преподавателю':'Личный черновик'}</Text></Pressable>
  <Button secondary title={`Открыть ${file.name}`} onPress={()=>void state.open(file.id)} disabled={disabled||state.busy}/>
  {!file.submitted&&<Button secondary title={`Удалить ${file.name}`} onPress={()=>void state.remove(file.id)} disabled={disabled||state.busy}/>}
 </View>)}
 <Button secondary title={state.pending?'Повторить загрузку файла':'Добавить файл'} onPress={()=>void state.pick()} busy={state.busy} disabled={disabled||!state.ready||(!state.pending&&state.files.length>=3)}/>
 {state.files.some(file=>file.submitted&&!state.selected.includes(file.id))&&<Text style={s.small}>Сохраните изменения ответа, чтобы убрать выбранные вложения у преподавателя. После этого их можно удалить.</Text>}
 {!!state.error&&<Notice message={state.error} action="Обновить список" onAction={()=>void state.load()}/>}
 </View>;
}
