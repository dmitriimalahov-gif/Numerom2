import {useRef, useState} from 'react';
import {Text} from 'react-native';
import {useLocalSearchParams} from 'expo-router';
import {Brand, Button, Card, Heading, Notice, Screen, s} from '../components/ui';
import {useSession} from '../lib/session';

// Opened from a morning letter: turns the letters off (or back on) without signing in.
// The page asks for a tap first, so a mail scanner opening the link never unsubscribes anyone.
export default function DailyEmail() {
 const {api} = useSession();
 const {token} = useLocalSearchParams<{token?: string}>();
 const [state, setState] = useState<{subscribed: boolean; email: string} | null>(null);
 const [busy, setBusy] = useState(false), [error, setError] = useState('');
 const lock = useRef(false);
 const valid = typeof token === 'string' && /^[A-Za-z0-9_.-]{20,2048}$/.test(token);
 async function choose(subscribed: boolean) {
  if (lock.current || !valid) return;
  lock.current = true; setBusy(true); setError('');
  try {
   const result = await api.request('/public/daily-email', {method: 'POST', body: {token, subscribed}, auth: false}) as {subscribed?: unknown; email?: unknown};
   setState({subscribed: result?.subscribed === true, email: typeof result?.email === 'string' ? result.email : ''});
  } catch (e) {setError(e instanceof Error ? e.message : 'Не удалось сохранить выбор. Повторите попытку.');}
  finally {lock.current = false; setBusy(false);}
 }
 const address = state?.email ? ` для ${state.email}` : '';
 return <Screen><Brand/>
  <Heading title="Утренние письма" subtitle="Каждое утро в 8:00 — число вашего личного дня и короткое напутствие."/>
  <Card>
   {!valid ? <Text style={s.body}>Ссылка неполная. Откройте её из последнего письма NumerOM.</Text>
    : state ? <Text accessibilityLiveRegion="polite" style={s.body}>{state.subscribed ? `Утренние письма снова включены${address}.` : `Утренние письма отключены${address}. Больше они приходить не будут.`}</Text>
    : <Text style={s.body}>Отключить ежедневные письма с числом личного дня? Остальные письма NumerOM — о готовых отчётах и безопасности аккаунта — продолжат приходить.</Text>}
   {valid && (!state || state.subscribed) && <Button title="Отключить утренние письма" busy={busy} onPress={() => void choose(false)}/>}
   {valid && state && !state.subscribed && <Button secondary title="Включить снова" busy={busy} onPress={() => void choose(true)}/>}
  </Card>
  {!!error && <Notice message={error}/>}
 </Screen>;
}
