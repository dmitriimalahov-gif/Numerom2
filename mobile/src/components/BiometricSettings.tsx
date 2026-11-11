import {useEffect,useState} from 'react';
import {Platform,Text} from 'react-native';
import {Button,Card,Notice,s} from './ui';
import {useSession} from '../lib/session';
export function BiometricSettings(){
 const {biometrics,session,user}=useSession();const [enabled,setEnabled]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 useEffect(()=>{if(Platform.OS!=='web')void biometrics.enabled().then(setEnabled);},[biometrics]);
 if(Platform.OS==='web')return null;
 const available=biometrics.available();
 async function toggle(){if(busy)return;setBusy(true);setError('');const owner=user?.id;
  try{if(enabled)await biometrics.disable();else await biometrics.enable(session.getToken()||'',()=>session.getSnapshot().user?.id===owner);setEnabled(await biometrics.enabled());}
  catch(e){setError(e instanceof Error?e.message:'Не удалось изменить способ входа.');}finally{setBusy(false);}
 }
 return <Card><Text style={s.title}>Вход по биометрии</Text><Text style={s.body}>{enabled?'Face ID или отпечаток защищает вход после закрытия и сворачивания приложения.':'Разблокируйте сохранённый вход с помощью Face ID или отпечатка пальца.'}</Text><Text style={s.small}>Биометрические данные остаются на вашем устройстве. После истечения сессии потребуется снова войти.</Text>{!available&&!enabled?<Text style={s.small}>Доступно в установленном приложении на устройстве с настроенной биометрией.</Text>:<Button secondary title={enabled?'Отключить биометрический вход':'Включить Face ID / отпечаток'} busy={busy} onPress={()=>void toggle()}/>} {!!error&&<Notice message={error}/>}</Card>;
}
