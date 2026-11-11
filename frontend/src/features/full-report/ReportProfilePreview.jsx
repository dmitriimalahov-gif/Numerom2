import React,{useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {profileRevision,reportPreview} from '../../../../packages/full-report/profile-preview';
import {validBirthDate} from '@numerom/full-report';
import {api} from '../../services/api';

export default function ReportProfilePreview({user,birth,useProfile,onUseProfile,onPreview,disabled=false}){
 const [preview,setPreview]=useState(null),[error,setError]=useState(''),[refresh,setRefresh]=useState(0);
 const revision=profileRevision(user),matches=birth===user.birth_date;
 useEffect(()=>{
  onPreview(null);setPreview(null);setError('');if(!validBirthDate(birth))return;
  const abort=new AbortController();let current=true;
  api.request('/full-reports/preview',{method:'POST',body:{birth_date:birth,use_profile:useProfile&&matches},signal:abort.signal}).then(raw=>{
   if(!current)return;const value=reportPreview(raw,birth,useProfile&&matches);setPreview(value);onPreview(value);
  }).catch(failure=>{if(current)setError(failure.message);});
  return()=>{current=false;abort.abort();};
 },[birth,useProfile,matches,revision,refresh,onPreview]);
 return <section className="fr-profile-preview" aria-label="Данные для полного разбора"><h3>Состав вашего разбора</h3>
  {matches?<label className="fr-profile-check"><input type="checkbox" checked={useProfile} disabled={disabled} onChange={event=>onUseProfile(event.target.checked)}/><span>Добавить данные моего профиля</span></label>:<p>Для другой даты используются только расчёты даты рождения. Личные данные вашего профиля к ней не добавляются.</p>}
  <p>Имя и фамилия открывают расчёт имени и числа мудрости; номер дома, телефон и автомобиль — свои разделы. Поля необязательны, стоимость остаётся 6,66 €.</p>
  {error?<p role="alert">{error} <button type="button" className="fr-text-button" onClick={()=>setRefresh(v=>v+1)}>Обновить состав</button></p>:!preview?<p role="status">Проверяем доступные разделы…</p>:<>
   <details><summary>Доступно разделов: {preview.available.length}</summary><ul>{preview.available.map(item=><li key={item.id}>{item.title}</li>)}</ul></details>
   {!!preview.excluded.length&&<details open={useProfile}><summary>Что можно добавить</summary><ul>{preview.excluded.map((item,index)=><li key={index}><strong>{item.title}</strong><span>{item.reason}</span></li>)}</ul></details>}
  </>}
  <Link to="/dashboard/personal-data">Заполнить профиль</Link><small>После изменения профиля вернитесь сюда: состав обновится. Уже начатая оплата сохраняет выбранные данные.</small>
 </section>;
}
