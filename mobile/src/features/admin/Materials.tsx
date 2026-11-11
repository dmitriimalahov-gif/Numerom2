import {useRef,useState} from 'react';
import {Linking,Platform,Text,View} from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import {File as LocalFile} from 'expo-file-system';
import {Button,Card,Field,Notice,s} from '../../components/ui';
import {backendUrl,useSession} from '../../lib/session';
import {submissionId} from '../../lib/learning';
import {MutationState,Reason,ResourceState,Toggle,reasonText,useAdminData,useAdminMutation} from './common';
import {materialUrl} from './mediaUrl';

const MAX=5*1024*1024;
const sections=[['theory','Теория'],['exercises','Упражнения'],['quiz','Тест'],['challenge','Дневник'],['analytics','Аналитика']] as const;
type Section=typeof sections[number][0];
type Material={id:string;name:string;mime?:string;size?:number;section:Section;is_active:boolean;revision:number};
function SectionPicker({value,onChange,disabled}:{value:Section;onChange:(v:Section)=>void;disabled:boolean}){
 return <View style={{gap:8}}><Text style={s.label}>Раздел урока</Text><View style={{flexDirection:'row',gap:8,flexWrap:'wrap'}}>{sections.map(([id,title])=><Button key={id} secondary title={`${id===value?'✓ ':''}${title}`} disabled={disabled} onPress={()=>onChange(id)}/>)}</View></View>;
}
export async function readMaterialFile(asset:DocumentPicker.DocumentPickerAsset){
 if(asset.size!==undefined&&(asset.size<1||asset.size>MAX))throw new Error('Выберите файл размером до 5 МБ.');
 if(Platform.OS==='web'){
  if(!asset.file||asset.file.size<1||asset.file.size>MAX)throw new Error('Выберите файл размером до 5 МБ.');
  return new Promise<string>((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]||'');reader.onerror=()=>reject(new Error('Не удалось прочитать файл.'));reader.readAsDataURL(asset.file!);});
 }
 const file=new LocalFile(asset.uri);if(file.size<1||file.size>MAX)throw new Error('Выберите файл размером до 5 МБ.');return file.base64();
}
export function LessonMaterials({lessonId}:{lessonId:string}){
 const {api,user,session}=useSession(),owner=useRef(user?.id),pickLock=useRef(false);
 const path=`/admin/mobile/lessons/${encodeURIComponent(lessonId)}/materials`,list=useAdminData<{files:Material[]}>(path);
 const [section,setSection]=useState<Section>('theory'),[reason,setReason]=useState(''),[picking,setPicking]=useState(false),[opening,setOpening]=useState(''),[openError,setOpenError]=useState(''),[selected,setSelected]=useState<Material|null>(null),[epoch,setEpoch]=useState(0);
 async function reload(){await list.reload();setSelected(null);setEpoch(v=>v+1);}
 const change=useAdminMutation(async()=>{setReason('');await reload();});
 async function pick(){
  if(pickLock.current||change.locked)return;pickLock.current=true;setPicking(true);
  try{const why=reasonText(reason),result=await DocumentPicker.getDocumentAsync({type:['application/pdf','image/png','image/jpeg'],multiple:false,copyToCacheDirectory:true,base64:false});
   if(result.canceled||owner.current!==session.getSnapshot().user?.id)return;
   const asset=result.assets[0];if(!asset)throw new Error('Выберите файл.');const content_base64=await readMaterialFile(asset);
   if(owner.current!==session.getSnapshot().user?.id)return;
   await change.run(path,{request_id:submissionId(),name:asset.name.slice(0,180),content_base64,section,reason:why},'POST',60000);
  }catch(e){change.setError(e instanceof Error?e.message:'Не удалось загрузить файл.');}finally{pickLock.current=false;setPicking(false);}
 }
 async function open(file:Material){setOpening(file.id);setOpenError('');try{const result=await api.request<{url:string}>(`${path}/${encodeURIComponent(file.id)}/access`);if(owner.current===session.getSnapshot().user?.id)await Linking.openURL(materialUrl(result.url,backendUrl));}catch(e){setOpenError(e instanceof Error?e.message:'Не удалось открыть материал.');}finally{setOpening('');}}
 const locked=picking||change.locked;
 return <View style={{gap:16}}><Text style={s.title}>Материалы урока</Text><Text style={s.small}>PDF, PNG и JPEG до 5 МБ. Новый материал сначала сохраняется скрытым: откройте его, проверьте и включите доступ ученикам.</Text><ResourceState {...list}/>
 {list.data?.files.map(file=><Card key={file.id}><Text style={s.title}>{file.name}</Text><Text style={s.small}>{sections.find(([id])=>id===file.section)?.[1]||file.section} · {file.is_active?'Доступен ученикам':'Скрыт'}{file.size?` · ${(file.size/1024/1024).toLocaleString('ru-RU',{maximumFractionDigits:2})} МБ`:''}</Text><Button secondary title={`Открыть материал: ${file.name}`} busy={opening===file.id} disabled={!!opening} onPress={()=>void open(file)}/><Button secondary title={`Настроить материал: ${file.name}`} disabled={locked} onPress={()=>setSelected(file)}/></Card>)}
 {!!openError&&<Notice message={openError}/>}
 {selected&&<MaterialEditor key={`${selected.id}-${epoch}`} file={selected} path={path} onSaved={reload}/>}
 <Text style={s.title}>Добавить материал</Text><SectionPicker value={section} onChange={setSection} disabled={locked}/><Reason value={reason} onChange={setReason} disabled={locked}/><Button title="Выбрать и загрузить файл" busy={picking||change.busy} disabled={locked||list.loading||!list.data} onPress={()=>void pick()}/><MutationState state={change} onReload={()=>void reload()}/>
 </View>;
}
function MaterialEditor({file,path,onSaved}:{file:Material;path:string;onSaved:()=>Promise<void>}){
 const [name,setName]=useState(file.name),[section,setSection]=useState(file.section),[active,setActive]=useState(file.is_active),[reason,setReason]=useState('');
 const change=useAdminMutation(onSaved);
 return <Card><Text style={s.title}>Настройки материала</Text><Field label="Название материала" value={name} onChangeText={setName} maxLength={180} editable={!change.locked}/><SectionPicker value={section} onChange={setSection} disabled={change.locked}/><Toggle label="Материал доступен ученикам" value={active} onChange={setActive} disabled={change.locked}/><Text style={s.small}>Скрытый файл остаётся у администратора. Доступ ученика зависит также от уровня и публикации урока.</Text><Reason value={reason} onChange={setReason} disabled={change.locked}/><Button title="Сохранить материал" busy={change.busy} disabled={change.locked} onPress={()=>void change.versioned(`${path}/${encodeURIComponent(file.id)}`,file.revision,reason,{name,section,is_active:active})}/><MutationState state={change} onReload={()=>void onSaved()}/></Card>;
}
