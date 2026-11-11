import {useEffect,useState,useSyncExternalStore} from 'react';
import {Text} from 'react-native';
import {router} from 'expo-router';
import {Brand,Button,Card,Field,Heading,Notice,Screen,s} from '../components/ui';
import {useSession} from '../lib/session';
import {createRecoveryRequest} from '../lib/recoveryRequest';
export default function ForgotPassword(){
 const {api}=useSession();const [email,setEmail]=useState('');
 const [request]=useState(()=>createRecoveryRequest({request:address=>api.requestPasswordReset(address)}));
 const {busy,message,error,sentTo,retryAt}=useSyncExternalStore(request.subscribe,request.getSnapshot,request.getSnapshot);
 const [,tick]=useState(0);
 useEffect(()=>{if(!retryAt)return;const timer=setInterval(()=>{tick(value=>value+1);if(!request.remainingSeconds())clearInterval(timer);},1000);return()=>clearInterval(timer);},[request,retryAt]);
 const remaining=request.remainingSeconds();
 const buttonTitle=remaining?`Повторить через ${remaining} с`:message?'Отправить ещё раз':'Получить ссылку';
 return <Screen><Brand/><Heading title="Восстановить пароль" subtitle="Укажите почту аккаунта NumerOM. Ссылка откроется на сайте, а новый пароль будет работать и в приложении."/>
 <Card>{message?<><Text style={s.title}>Проверьте почту</Text><Text selectable style={s.label}>{sentTo}</Text><Text style={s.body}>{message}</Text><Text style={s.small}>Ссылка действует 30 минут. Если запросите письмо повторно, используйте ссылку из самого нового письма.</Text></>:<Field label="Электронная почта" value={email} onChangeText={setEmail} editable={!busy} keyboardType="email-address" autoCapitalize="none" autoCorrect={false} autoComplete="email" maxLength={254} onSubmitEditing={()=>void request.submit(email)}/>}
 {!!error&&<Notice message={error}/>}
 <Button title={buttonTitle} busy={busy} disabled={remaining>0} onPress={()=>void request.submit(message?sentTo:email)}/>
 {!!message&&<Button title="Изменить адрес почты" secondary disabled={busy} onPress={()=>request.changeAddress()}/>}</Card>
 <Button title="Вернуться ко входу" secondary onPress={()=>router.replace('/')}/></Screen>;
}
