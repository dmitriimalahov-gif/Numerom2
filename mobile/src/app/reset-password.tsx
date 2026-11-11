import {useEffect, useRef, useState} from 'react';
import {Platform, Text} from 'react-native';
import * as Linking from 'expo-linking';
import {router} from 'expo-router';
import {Brand, Button, Card, Field, Heading, Notice, Screen, s} from '../components/ui';
import {useSession} from '../lib/session';
import {passwordError, recoveryToken} from '../lib/recovery';

export default function ResetPassword() {
 const {api, session} = useSession();
 const [token, setToken] = useState(() => Platform.OS === 'web' ? recoveryToken(window.location.href) : '');
 const [password, setPassword] = useState('');
 const [confirmation, setConfirmation] = useState('');
 const [busy, setBusy] = useState(false);
 const [message, setMessage] = useState('');
 const [error, setError] = useState('');
 const lock = useRef(false);
 useEffect(() => {
  if (Platform.OS === 'web') {
   if (window.location.hash) window.history.replaceState(window.history.state, '', window.location.pathname + window.location.search);
   return;
  }
  let active = true;
  void Linking.getInitialURL().then(url => {if (active) setToken(recoveryToken(url));});
  const listener = Linking.addEventListener('url', ({url}) => setToken(recoveryToken(url)));
  return () => {active = false; listener.remove();};
 }, []);
 async function submit() {
  if (lock.current || !token) return;
  const validation = passwordError(password, confirmation);
  if (validation) {setError(validation); return;}
  lock.current = true; setBusy(true); setError('');
  try {
   const result = await api.resetPassword(token, password);
   setMessage(result.message); setPassword(''); setConfirmation(''); setToken('');
   await session.signOut().catch(() => {});
  } catch (e) {setError(e instanceof Error ? e.message : 'Не удалось изменить пароль');}
  finally {lock.current = false; setBusy(false);}
 }
 return <Screen><Brand/><Heading title={message ? 'Пароль изменён' : 'Новый пароль'} subtitle="Один пароль для сайта и приложения NumerOM. Предыдущие сеансы будут завершены."/>
 {message ? <Card><Text style={s.body}>{message}</Text><Button title="Войти с новым паролем" onPress={() => router.replace('/')}/></Card> : !token ? <Card><Text style={s.body}>В ссылке отсутствует код восстановления. Откройте полную ссылку из письма или запросите новую.</Text><Button title="Получить новую ссылку" onPress={() => router.replace('/forgot-password')}/></Card> : <Card>
 <Field label="Новый пароль" value={password} onChangeText={setPassword} secureTextEntry autoComplete="new-password" maxLength={72}/><Text style={s.small}>Не менее 12 символов. Можно использовать пробелы.</Text>
 <Field label="Повторите пароль" value={confirmation} onChangeText={setConfirmation} secureTextEntry autoComplete="new-password" maxLength={72} onSubmitEditing={() => void submit()}/>
 {!!error && <Notice message={error}/>}<Button title="Сохранить новый пароль" busy={busy} onPress={() => void submit()}/>
 <Button title="Запросить новую ссылку" secondary disabled={busy} onPress={() => router.replace('/forgot-password')}/></Card>}
 <Button title="Вернуться ко входу" secondary disabled={busy} onPress={() => router.replace('/')}/></Screen>;
}
