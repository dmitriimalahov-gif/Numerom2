import {useEffect,useRef,useState} from 'react';
import {Text,View} from 'react-native';
import {Href,router,useLocalSearchParams} from 'expo-router';
import {Brand,Button,Card,Field,Heading,Loading,Notice,Screen,s} from '../components/ui';
import {useSession} from '../lib/session';
import {loadTelegram,telegramSection} from '../lib/telegram';

export default function TelegramEntry(){
 const {api,session,status}=useSession();const params=useLocalSearchParams();
 const [init,setInit]=useState(''),[needsRegistration,setNeedsRegistration]=useState(false),[existing,setExisting]=useState(false);
 const [name,setName]=useState(''),[birth,setBirth]=useState(''),[email,setEmail]=useState(''),[password,setPassword]=useState('');
 const [busy,setBusy]=useState(true),[error,setError]=useState(''),[balance,setBalance]=useState<number|null>(null);
 const started=useRef(false),lock=useRef(false),active=useRef(true);
 useEffect(()=>{active.current=true;return()=>{active.current=false;};},[]);
 async function apply(result:any,raw:string){
  await session.signInWith(async()=>result);
  if(!active.current)return;
  setBalance(result.user.credits_remaining??0);setNeedsRegistration(false);
  // The server binds the recipient to both the signed launch and current account.
  try{await api.request('/telegram/menu',{method:'POST',body:{init_data:raw}});}catch{if(active.current)setError('Баланс в приложении обновлён. Меню чата можно обновить командой /menu.');}
 }
 async function launch(){
  if(lock.current)return;lock.current=true;setBusy(true);setError('');
  try{
   const app=await loadTelegram();app.ready();app.expand();app.setHeaderColor?.('#ffffff');app.setBackgroundColor?.('#F6F7F5');
   if(!active.current)return;
   // A browser's stored account must never override the current Telegram identity.
   await session.signOut();setInit(app.initData);
   const result=await api.request<any>('/auth/telegram/login',{method:'POST',body:{init_data:app.initData}});
   if(!active.current)return;
   if(result.registration_required)setNeedsRegistration(true);else await apply(result,app.initData);
  }catch(e){if(active.current){setError(e instanceof Error?e.message:'Не удалось войти.');if((e as {status?:number}).status===403){setNeedsRegistration(true);setExisting(true);}}}
  finally{lock.current=false;if(active.current)setBusy(false);}
 }
 useEffect(()=>{if(status==='loading'||started.current)return;started.current=true;void launch();},[status]);
 async function submit(){
  if(lock.current)return;lock.current=true;setBusy(true);setError('');
  try{
   const body=existing?{init_data:init,email:email.trim(),password}:{init_data:init,full_name:name.trim(),birth_date:birth.trim()};
   const result=await api.request<any>('/auth/telegram/'+(existing?'link':'register'),{method:'POST',body});
   if(active.current)await apply(result,init);
  }catch(e){if(active.current)setError(e instanceof Error?e.message:'Не удалось завершить регистрацию.');}
  finally{lock.current=false;if(active.current){setBusy(false);setPassword('');}}
 }
 return <Screen><Brand/><Heading title="NumerOM в Telegram" subtitle="Все ваши расчёты, обучение и материалы — в одном аккаунте."/>
 {!!error&&<Notice message={error}/>}{busy&&<Loading/>}
 {balance!==null?<Card tinted><Text style={s.small}>Ваш баланс</Text><Text accessibilityRole="header" style={s.heading}>{balance} баллов</Text><Text style={s.body}>Баланс и история доступны в меню на любом экране.</Text><Button title="Открыть NumerOM" disabled={busy} onPress={()=>router.replace(telegramSection(params.section) as Href)}/></Card>:
 needsRegistration?<View style={{gap:16}}><Heading title={existing?'Связать мой аккаунт':'Начать знакомство'} subtitle={existing?'Войдите в NumerOM. Баллы и покупки сохранятся.':'После регистрации в меню появятся 10 приветственных баллов.'}/>
 {existing?<><Field label="Электронная почта NumerOM" value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address" editable={!busy}/><Field label="Пароль NumerOM" value={password} onChangeText={setPassword} secureTextEntry editable={!busy}/></>:<><Field label="Имя и фамилия" value={name} onChangeText={setName} maxLength={150} editable={!busy}/><Field label="Дата рождения" value={birth} onChangeText={setBirth} placeholder="ДД.ММ.ГГГГ" maxLength={10} keyboardType="numbers-and-punctuation" editable={!busy}/></>}
 <Button title={existing?'Войти и связать Telegram':'Зарегистрироваться'} busy={busy} onPress={()=>void submit()}/><Button secondary title={existing?'Создать новый аккаунт':'У меня уже есть аккаунт NumerOM'} disabled={busy} onPress={()=>{setExisting(!existing);setError('');setPassword('');}}/></View>:
 !busy&&<Button title="Повторить подключение Telegram" onPress={()=>void launch()}/>}
 </Screen>;
}
