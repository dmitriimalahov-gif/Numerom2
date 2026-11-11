import {useState} from 'react';
import {Text,View} from 'react-native';
import {Button,s} from '../../components/ui';
import {MutationState,Reason,useAdminMutation} from './common';
export default function Archive({kind,id,revision,reload}:{kind:'lessons'|'consultations';id:string;revision:number;reload:()=>Promise<void>}){
 const [open,setOpen]=useState(false),[reason,setReason]=useState('');const change=useAdminMutation(reload);
 return <View style={{gap:12}}>{open?<><Text style={s.title}>Перенести в архив?</Text><Text style={s.small}>Материал будет скрыт. История учеников, ответы и результаты сохранятся. Архивная запись доступна только для просмотра.</Text><Reason value={reason} onChange={setReason} disabled={change.locked}/><Button title="Подтвердить архивирование" busy={change.busy} disabled={change.locked} onPress={()=>void change.versioned(`/admin/mobile/${kind}/${encodeURIComponent(id)}/archive`,revision,reason,{})}/><Button title="Отмена" secondary disabled={change.locked} onPress={()=>setOpen(false)}/><MutationState state={change} onReload={()=>void reload()}/></>:<Button secondary title="Перенести в архив" onPress={()=>setOpen(true)}/>}</View>;
}
