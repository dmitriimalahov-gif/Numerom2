import {useCallback,useState} from 'react';
import {Platform,Text,View} from 'react-native';
import {Button,Card,Field,Notice,s} from './ui';
import {useSession} from '../lib/session';
import {useResource} from '../lib/useResource';
import {currentPasskeyRpId,forgetPasskeyForAutoEntry,passkeysAvailable,registerPasskey} from '../lib/passkeys';
function Settings(){
 const {api}=useSession();const keys=useResource(useCallback(()=>api.request<{keys:{id:string;label:string;active:boolean}[]}>('/user/passkeys'),[api]));
 const [password,setPassword]=useState(''),[label,setLabel]=useState('Мой телефон'),[error,setError]=useState(''),[busy,setBusy]=useState(false),[adding,setAdding]=useState(false);
 async function run(action:()=>Promise<unknown>){if(busy)return;setBusy(true);setError('');try{await action();setPassword('');setAdding(false);await keys.reload();}catch(e){setError(e instanceof Error?e.message:'Не удалось сохранить ключ.');}finally{setBusy(false);}}
 return <Card><Text style={s.title}>Face ID, отпечаток или ключ доступа</Text><Text style={s.body}>Добавьте ключ для входа без пароля. Устройство подтверждает вашу личность биометрией или своим кодом блокировки.</Text>
  {keys.data?.keys.map(key=><View key={key.id} style={{gap:8}}><Text style={s.label}>{key.label}{key.active?'':' · требуется обновить'}</Text><Button secondary title={`Удалить ключ «${key.label}»`} disabled={busy} onPress={()=>void run(async()=>{await api.request('/user/passkeys/remove',{method:'POST',body:{id:key.id}});const current=await api.request<{keys:{active:boolean;rp_id?:string}[]}>('/user/passkeys');const rpId=currentPasskeyRpId();if(!rpId||!current.keys.some(item=>item.active&&(!item.rp_id||item.rp_id===rpId)))forgetPasskeyForAutoEntry();})}/></View>)}
  {!!keys.error&&<Notice message={keys.error} action="Обновить ключи" onAction={()=>void keys.reload()}/>}
  {adding?<><Field label="Название устройства" value={label} onChangeText={setLabel} maxLength={80} editable={!busy}/><Field label="Текущий пароль для подтверждения" secureTextEntry autoComplete="current-password" value={password} onChangeText={setPassword} editable={!busy}/><Button title="Создать ключ доступа" busy={busy} disabled={!password||!label.trim()} onPress={()=>void run(()=>registerPasskey(api,password,label))}/><Button secondary title="Отмена" disabled={busy} onPress={()=>{setAdding(false);setPassword('');}}/></>:<Button secondary title="Добавить ключ доступа" disabled={busy} onPress={()=>setAdding(true)}/>}
  {!!error&&<Notice message={error}/>}<Text style={s.small}>Пароль остаётся запасным способом входа. После сброса пароля зарегистрируйте ключ заново.</Text>
 </Card>;
}
export function PasskeySettings(){return Platform.OS==='web'&&passkeysAvailable()?<Settings/>:null;}
