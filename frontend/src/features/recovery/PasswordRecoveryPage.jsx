import React, {useEffect,useRef,useState} from 'react';
import {Link} from 'react-router-dom';
import {Brand} from '../../components/NumeromIdentity';
import {Button} from '../../components/ui/button';
import {Input} from '../../components/ui/input';
import {Label} from '../../components/ui/label';
import {api} from '../../services/api';
import './recovery.css';

export default function PasswordRecoveryPage({mode='request'}) {
 const reset=mode==='reset';
 const [token]=useState(()=>reset ? new URLSearchParams(window.location.hash.slice(1)).get('token') || '' : '');
 const [email,setEmail]=useState('');const [password,setPassword]=useState('');const [confirmation,setConfirmation]=useState('');
 const [busy,setBusy]=useState(false);const [error,setError]=useState('');const [message,setMessage]=useState('');const lock=useRef(false);
 useEffect(()=>{if(reset && window.location.hash)window.history.replaceState(window.history.state,'',window.location.pathname+window.location.search);},[reset]);
 async function submit(event){
  event.preventDefault();if(lock.current)return;setError('');
  if(reset && password!==confirmation){setError('Пароли не совпадают');return;}
  if(reset && (password.length<12 || new TextEncoder().encode(password).length>72)){setError('Используйте от 12 символов, не более 72 байт.');return;}
  lock.current=true;setBusy(true);
  try{const result=reset ? await api.resetPassword(token,password) : await api.requestPasswordReset(email);setMessage(result.message);setPassword('');setConfirmation('');}
  catch(e){setError(e.status===503?'Восстановление временно недоступно. Попробуйте позже или обратитесь в поддержку NumerOM.':e.message);}
  finally{lock.current=false;setBusy(false);}
 }
 return <main className="nm-recovery-page ph-no-capture"><section className="nm-recovery-card" aria-labelledby="recovery-title">
  <Link to="/" aria-label="NumerOM — главная"><Brand/></Link>
  <div><p className="nm-section-label">Доступ к вашему пространству</p><h1 id="recovery-title">{reset?'Новый пароль':'Восстановить пароль'}</h1><p>{reset?'Задайте новый пароль для сайта и приложения. Предыдущие сеансы будут завершены.':'Укажите почту вашего аккаунта. Мы отправим ссылку для восстановления доступа.'}</p></div>
  {reset&&!token ? <div role="status"><p>В ссылке отсутствует код восстановления.</p><Link className="nm-text-link" to="/forgot-password">Получить новую ссылку</Link></div> : message ? <div role="status" className="nm-recovery-success"><h2>{reset?'Пароль изменён':'Проверьте почту'}</h2><p>{message}</p>{!reset&&<p>Ссылка действует 30 минут. Повторный запрос можно отправить через минуту.</p>}<Link className="nm-text-link" to="/">Вернуться ко входу</Link></div> : <form onSubmit={submit} className="nm-recovery-form">
   {!reset ? <div><Label htmlFor="recovery-email">Электронная почта</Label><Input id="recovery-email" name="email" type="email" autoComplete="email" maxLength={254} value={email} onChange={e=>setEmail(e.target.value)} required/></div> : <><div><Label htmlFor="new-password">Новый пароль</Label><Input id="new-password" name="password" type="password" autoComplete="new-password" minLength={12} maxLength={72} value={password} onChange={e=>setPassword(e.target.value)} required/><small>Не менее 12 символов. Можно использовать пробелы.</small></div><div><Label htmlFor="confirm-password">Повторите пароль</Label><Input id="confirm-password" name="confirmation" type="password" autoComplete="new-password" value={confirmation} onChange={e=>setConfirmation(e.target.value)} required/></div></>}
   {error&&<div role="alert" className="nm-recovery-error">{error}{reset&&<Link to="/forgot-password">Запросить новую ссылку</Link>}</div>}
   <Button type="submit" disabled={busy}>{busy?'Подождите…':reset?'Сохранить новый пароль':'Получить ссылку'}</Button>
  </form>}
  <Link className="nm-recovery-back" to="/">← На главную</Link>
 </section></main>;
}
