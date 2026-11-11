import { useRef, useState } from 'react';
import { Platform, Image, Pressable, Text, View } from 'react-native';
import { Redirect, router } from 'expo-router';
import { Brand, Button, Card, Field, Heading, Loading, Notice, Screen, s } from '../components/ui';
import { useSession } from '../lib/session';
import {passkeysAvailable,signInWithPasskey} from '../lib/passkeys';
import { registrationError } from '../lib/accountForm';
import { AuthorWord } from '../components/AuthorWord';

export default function Welcome() {
 const {api,session,status,error:sessionError,needsSignOutRetry} = useSession();
 const [register,setRegister] = useState(false);
 const [email,setEmail] = useState(''); const [password,setPassword] = useState('');
 const [confirmation,setConfirmation] = useState('');
 const [name,setName] = useState(''); const [date,setDate] = useState('');
 const [error,setError] = useState(''); const [busy,setBusy] = useState(false); const lock = useRef(false);
 async function submit() {
  if(lock.current) return;
  const validation=register ? registrationError({email,password,confirmation,full_name:name,birth_date:date}) : !/^\S+@\S+\.\S+$/.test(email.trim()) ? 'Введите адрес электронной почты' : !password ? 'Введите пароль' : '';
  if(validation){setError(validation);return;}
  lock.current=true;setBusy(true);setError('');
  try { if(register) await session.signUp({email:email.trim(),password,full_name:name.trim(),birth_date:date.trim()}); else await session.signIn(email,password); }
  catch(e) {setError(e instanceof Error ? e.message : 'Не удалось войти');}
  finally {lock.current=false;setBusy(false);}
 }
 async function passkey(){if(lock.current)return;lock.current=true;setBusy(true);setError('');try{await session.signInWith(()=>signInWithPasskey(api));}catch(e){setError(e instanceof Error?e.message:'Не удалось войти с ключом доступа.');}finally{lock.current=false;setBusy(false);}}
 async function logout() {
  if(lock.current) return;
  lock.current=true;setBusy(true);setError('');
  try {await session.signOut();}
  catch(e){setError(e instanceof Error ? e.message : 'Не удалось выйти из аккаунта');}
  finally{lock.current=false;setBusy(false);}
 }
 if(status === 'signedIn') return <Redirect href="/(tabs)/home"/>;
 if(status === 'loading') return <Screen><Brand/><Loading/></Screen>;
 if(status === 'unavailable') return <Screen><Brand/><Heading title="Продолжим, когда появится связь" subtitle="Ваш вход сохранён. Подключение восстановится автоматически, когда сервер снова будет доступен."/><Notice message={error || sessionError || 'Сервер недоступен'} action="Повторить" onAction={()=>{if(!lock.current) void session.restore().catch(e=>setError(e instanceof Error?e.message:'Не удалось восстановить вход'));}}/><Button title="Выйти из аккаунта" secondary busy={busy} onPress={()=>void logout()}/></Screen>;
 return <Screen><Brand/><Heading eyebrow="Пространство самопознания" title={'Ближе к себе.\nВ своём ритме.'} subtitle="Персональные числа, обучение и наглядные схемы — в одном месте."/>
 <AuthorWord/>
 <Card tinted><View style={s.row}><View style={{flex:1,gap:9}}><Text style={s.title}>У каждого числа своя история</Text><Text style={s.small}>Знакомьтесь с методом NumerOM шаг за шагом.</Text></View><Image accessibilityLabel="Учебный квадрат чисел NumerOM" source={require('../../assets/illustrations/KVADRATW.png')} style={{width:122,height:122}} resizeMode="contain"/></View><Button title="Посмотреть схемы" secondary onPress={()=>router.push('/guide')}/></Card>
 <View style={{gap:18}}><Heading title={register?'Ваше начало':'С возвращением'} subtitle={register?'Создайте общий аккаунт для сайта и приложения.':'Войдите с аккаунтом NumerOM.'}/>
 {register && <><Field label="Имя и фамилия" value={name} onChangeText={setName} autoComplete="name" editable={!busy}/><Text style={s.small}>Используйте привычное написание. Данные для числа имени можно дополнить в профиле.</Text><Field label="Дата рождения" placeholder="ДД.ММ.ГГГГ" value={date} onChangeText={setDate} keyboardType="numbers-and-punctuation" maxLength={10} editable={!busy}/></>}
 <Field label="Электронная почта" placeholder="you@example.com" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" autoCorrect={false} autoComplete="email" editable={!busy}/>
 <Field label="Пароль" value={password} onChangeText={setPassword} secureTextEntry autoComplete={register?'new-password':'current-password'} editable={!busy} onSubmitEditing={()=>{if(!register) void submit();}}/>
 {register && <><Text style={s.small}>Не менее 8 символов.</Text><Field label="Подтвердите пароль" value={confirmation} onChangeText={setConfirmation} secureTextEntry autoComplete="new-password" editable={!busy} onSubmitEditing={()=>void submit()}/></>}
 {!!(error || sessionError) && <Notice message={error || sessionError || ''}/>}
 {needsSignOutRetry && <Button title="Повторить выход" secondary busy={busy} onPress={()=>void logout()}/>}
 {!register&&<Pressable accessibilityRole="button" onPress={()=>router.push('/forgot-password')} style={{paddingVertical:10}}><Text style={s.link}>Забыли пароль?</Text></Pressable>}
 {!register&&Platform.OS==='web'&&passkeysAvailable()&&<Button secondary title="Войти с Face ID / ключом доступа" busy={busy} onPress={()=>void passkey()}/>}
 <Button title={register?'Создать аккаунт':'Войти'} busy={busy} onPress={()=>void submit()}/>
 <Pressable accessibilityRole="button" disabled={busy} onPress={()=>{setRegister(!register);setError('');setPassword('');setConfirmation('');}} style={{padding:12,alignItems:'center'}}><Text style={s.link}>{register?'Уже есть аккаунт? Войти':'Впервые здесь? Создать аккаунт'}</Text></Pressable>
 </View><Text style={[s.small,{textAlign:'center'}]}>Ваши расчёты и обучение остаются с вами на всех устройствах.</Text></Screen>;
}
