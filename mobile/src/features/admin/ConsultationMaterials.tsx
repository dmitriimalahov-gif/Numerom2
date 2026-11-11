import {useRef,useState} from 'react';
import {Linking,Text,View} from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import {Button,Notice,s} from '../../components/ui';
import {backendUrl,useSession} from '../../lib/session';
import {submissionId} from '../../lib/learning';
import {MutationState,Reason,ResourceState,reasonText,useAdminData,useAdminMutation} from './common';
import {readMaterialFile} from './Materials';
import {consultationUrl} from './mediaUrl';
type Pdf={id:string;name:string;mime:string;size:number};
export function ConsultationMaterials({id,selected,onSelect,disabled}:{id:string;selected:string|null;onSelect:(id:string|null)=>void;disabled:boolean}){
 const {api,user,session}=useSession(),owner=useRef(user?.id),pickLock=useRef(false),path=`/admin/mobile/consultations/${encodeURIComponent(id)}/materials`;
 const list=useAdminData<{files:Pdf[]}>(path),[reason,setReason]=useState(''),[picking,setPicking]=useState(false),[opening,setOpening]=useState(''),[openError,setOpenError]=useState('');
 const change=useAdminMutation(async()=>{setReason('');await list.reload();});
 async function pick(){if(disabled||change.locked||pickLock.current)return;pickLock.current=true;setPicking(true);
  try{const why=reasonText(reason),result=await DocumentPicker.getDocumentAsync({type:'application/pdf',multiple:false,copyToCacheDirectory:true,base64:false});
   if(result.canceled||owner.current!==session.getSnapshot().user?.id)return;
   const file=result.assets[0];if(!file)throw new Error('Выберите PDF.');const content_base64=await readMaterialFile(file);
   if(owner.current===session.getSnapshot().user?.id)await change.run(path,{request_id:submissionId(),name:file.name.slice(0,180),content_base64,reason:why},'POST',60000);
  }catch(e){change.setError(e instanceof Error?e.message:'Не удалось загрузить PDF.');}finally{setPicking(false);pickLock.current=false;}
 }
 async function open(file:Pdf){setOpening(file.id);setOpenError('');try{const result=await api.request<{url:string}>(`${path}/${file.id}/access`);if(owner.current===session.getSnapshot().user?.id)await Linking.openURL(consultationUrl(result.url,backendUrl));}catch(e){setOpenError(e instanceof Error?e.message:'Не удалось открыть PDF.');}finally{setOpening('');}}
 const locked=disabled||picking||change.locked;
 return <View style={{gap:14}}><Text style={s.title}>PDF для консультации</Text><Text style={s.small}>Загрузите PDF до 5 МБ, затем выберите его и сохраните консультацию. До сохранения новый файл виден только администратору.</Text><ResourceState {...list}/>
 {list.data?.files.map(file=><View key={file.id} style={{gap:8}}><Text style={s.label}>{file.name} · {(file.size/1024/1024).toLocaleString('ru-RU',{maximumFractionDigits:2})} МБ</Text><Button secondary title={`${selected===file.id?'Выбран PDF: ':'Выбрать PDF: '}${file.name}`} disabled={locked} onPress={()=>onSelect(file.id)}/><Button secondary title={`Проверить PDF: ${file.name}`} disabled={!!opening} busy={opening===file.id} onPress={()=>void open(file)}/></View>)}
 {!!selected&&<Button secondary title="Убрать PDF из консультации" disabled={locked} onPress={()=>onSelect(null)}/>}
 {!!openError&&<Notice message={openError}/>}<Reason value={reason} onChange={setReason} disabled={locked}/><Button title="Загрузить PDF консультации" busy={picking||change.busy} disabled={locked||list.loading||!list.data} onPress={()=>void pick()}/><MutationState state={change} onReload={()=>void list.reload()}/>
 </View>;
}
