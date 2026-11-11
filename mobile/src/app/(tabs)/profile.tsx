import { useEffect, useRef, useState } from 'react';
import { Text } from 'react-native';
import {router} from 'expo-router';
import { Button, Card, Field, Heading, Notice, Screen, s } from '../../components/ui';
import { useSession } from '../../lib/session';
import { profileDraft, profileError, profilePatch, ProfileDraft } from '../../lib/accountForm';
import {PasskeySettings} from '../../components/PasskeySettings';
import {BiometricSettings} from '../../components/BiometricSettings';
import { colors } from '../../lib/theme';
import {LocationField} from '../../components/LocationField';
import {CityField} from '../../components/CityField';

export default function Profile() {
 const {api,user,session} = useSession();
 const [form,setForm]=useState(()=>{const values=profileDraft(user);return {draft:values,baseline:values};});
 const {draft,baseline}=form;
 const [busy,setBusy]=useState<'save' | 'logout' | null>(null);
 const [error,setError]=useState('');
 const [saved,setSaved]=useState(false);
 const lock=useRef(false),owner=useRef(user?.id);

 useEffect(()=>{
  const next=profileDraft(user);
  const sameOwner=owner.current===user?.id;owner.current=user?.id;
  setForm(current=>({draft:sameOwner?{...next,...profilePatch(current.draft,current.baseline)}:next,baseline:next}));
 },[user]);

 function change(field:keyof ProfileDraft,value:string) {
  setForm(current=>({...current,draft:{...current.draft,[field]:value}}));setSaved(false);setError('');
 }

 async function save() {
  if(lock.current) return;
  const validation=profileError(draft);
  if(validation){setError(validation);setSaved(false);return;}
  const changes=profilePatch(draft,baseline);
  if(!Object.keys(changes).length) return;
  lock.current=true;setBusy('save');setSaved(false);setError('');
  try {
   const savingOwner=user?.id;const updated=await api.updateProfile(changes);if(session.getSnapshot().user?.id!==savingOwner)return;
   const next=profileDraft(updated);setForm({draft:next,baseline:next});setSaved(true);
   try {await session.refresh();}
   catch {setError('Изменения сохранены. Не удалось обновить данные аккаунта. Они появятся после восстановления связи.');}
  }
  catch(e){setError(e instanceof Error?e.message:'Не удалось сохранить профиль');}
  finally{lock.current=false;setBusy(null);}
 }

 async function logout() {
  if(lock.current) return;
  lock.current=true;setBusy('logout');setError('');
  try{await session.signOut();}
  catch(e){setError(e instanceof Error?e.message:'Не удалось выйти');}
  finally{lock.current=false;setBusy(null);}
 }

 const hasChanges=Object.keys(profilePatch(draft,baseline)).length>0;
 return <Screen>
  <Heading eyebrow="Ваш аккаунт" title="Профиль" subtitle="Изменения будут доступны и на сайте NumerOM."/>
  <Card><Text style={s.title}>{user?.full_name || user?.name || 'Мой аккаунт'}</Text><Text style={s.body}>{user?.email}</Text><Text style={s.small}>Баланс: {user?.credits_remaining ?? '—'} баллов</Text></Card>
  <Field label="Полное имя в профиле" value={draft.full_name} onChangeText={v=>change('full_name',v)} autoComplete="name" editable={!busy}/>
  <Field label="Имя" value={draft.name} onChangeText={v=>change('name',v)} autoComplete="given-name" autoCorrect={false} editable={!busy}/>
  <Field label="Фамилия" value={draft.surname} onChangeText={v=>change('surname',v)} autoComplete="family-name" autoCorrect={false} editable={!busy}/>
  <Text style={s.small}>Для числа имени заполните имя и фамилию латинскими буквами A–Z. Допустимы пробелы, дефисы и апострофы. Полное имя в профиле можно оставить в привычном написании. Изменение имени и фамилии его не заменяет.</Text>
  <Field label="Дата рождения" value={draft.birth_date} onChangeText={v=>change('birth_date',v)} placeholder="ДД.ММ.ГГГГ" maxLength={10} keyboardType="numbers-and-punctuation" editable={!busy}/>
  <CityField key={`birth-${user?.id}`} value={draft.birth_city} disabled={!!busy} onChange={(value,id)=>{setForm(current=>({...current,draft:{...current.draft,birth_city:value,birth_city_id:id}}));setSaved(false);setError('');}}/>
  <Text style={s.title}>Текущее место</Text>
  <LocationField key={user?.id} value={draft.city} onChange={city=>change('city',city)} disabled={!!busy}/>
  <Text style={s.title}>Дополните личный разбор</Text>
  <Text style={s.body}>Эти поля необязательны. В полном разборе за 6,66 € появятся разделы телефона, дома и автомобиля — без доплаты. Для расчёта дома достаточно его номера; улицу можно не указывать.</Text>
  <Field label="Телефон с кодом страны" value={draft.phone_number} onChangeText={v=>change('phone_number',v)} maxLength={32} keyboardType="phone-pad" editable={!busy}/>
  <Field label="Номер дома" value={draft.house_number} onChangeText={v=>change('house_number',v)} maxLength={24} editable={!busy}/>
  <Field label="Номер квартиры" value={draft.apartment_number} onChangeText={v=>change('apartment_number',v)} maxLength={24} editable={!busy}/>
  <Field label="Почтовый индекс" value={draft.postal_code} onChangeText={v=>change('postal_code',v)} maxLength={24} editable={!busy}/>
  <Field label="Номер автомобиля" value={draft.car_number} onChangeText={v=>change('car_number',v)} maxLength={13} autoCapitalize="characters" editable={!busy}/>
  {!!error && <Notice message={error}/>}
  {saved && <Text accessibilityLiveRegion="polite" style={{color:colors.green}}>Профиль сохранён</Text>}
  <Button title="Сохранить изменения" busy={busy==='save'} disabled={!!busy || !hasChanges} onPress={()=>void save()}/>
  {(user?.is_admin||user?.is_super_admin)&&<Button title="Кабинет администратора" secondary onPress={()=>router.push('/admin')}/>}
  <BiometricSettings/><PasskeySettings/>
  <Button title="Выйти из аккаунта" secondary busy={busy==='logout'} disabled={!!busy} onPress={()=>void logout()}/>
 </Screen>;
}
