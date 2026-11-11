import {useEffect,useState} from 'react';
import {Switch,Text,View} from 'react-native';
import {router} from 'expo-router';
import {profileRevision,reportPreview,ReportPreview} from '../../../../packages/full-report/profile-preview';
import {validBirthDate} from '../../../../packages/full-report';
import {useSession} from '../../lib/session';
import {Button,Notice,s} from '../ui';

export function ReportProfilePreview({birth,useProfile,onUseProfile,onPreview,disabled=false}:{birth:string;useProfile:boolean;onUseProfile:(value:boolean)=>void;onPreview:(value:ReportPreview|null)=>void;disabled?:boolean}){
 const {api,user,session}=useSession();const [preview,setPreview]=useState<ReportPreview|null>(null),[error,setError]=useState(''),[refresh,setRefresh]=useState(0),[expanded,setExpanded]=useState(false);
 const revision=profileRevision(user),matches=birth===user?.birth_date,uid=user?.id;
 useEffect(()=>{onPreview(null);setPreview(null);setError('');if(!validBirthDate(birth))return;
  const abort=new AbortController();let current=true;
  api.request('/full-reports/preview',{method:'POST',body:{birth_date:birth,use_profile:useProfile&&matches},signal:abort.signal}).then(raw=>{
   if(!current||session.getSnapshot().user?.id!==uid)return;const value=reportPreview(raw,birth,useProfile&&matches);setPreview(value);onPreview(value);
  }).catch(failure=>{if(current&&session.getSnapshot().user?.id===uid)setError(failure.message);});
  return()=>{current=false;abort.abort();};
 },[api,birth,useProfile,matches,revision,refresh,onPreview,session,uid]);
 return <View style={{gap:12}}><Text style={s.title}>Состав вашего разбора</Text>
  {matches?<View style={s.row}><Text style={[s.body,{flex:1}]}>Добавить данные моего профиля</Text><Switch accessibilityLabel="Добавить данные моего профиля" value={useProfile} disabled={disabled} onValueChange={onUseProfile}/></View>:<Text style={s.small}>Для другой даты используются только расчёты даты рождения. Данные вашего профиля к ней не добавляются.</Text>}
  <Text style={s.body}>Имя и фамилия добавят расчёт имени и числа мудрости, номер дома, телефон и автомобиль — свои разделы. Всё необязательно, стоимость остаётся 6,66 €.</Text>
  {!!error&&<Notice message={error} action="Обновить состав" onAction={()=>setRefresh(value=>value+1)}/>}
  {!preview&&!error&&<Text accessibilityLiveRegion="polite" style={s.small}>Проверяем доступные разделы…</Text>}
  {preview&&<><Button secondary title={`${expanded?'Скрыть':'Показать'} состав · ${preview.available.length} разделов`} onPress={()=>setExpanded(value=>!value)}/>{expanded&&preview.available.map(item=><Text key={item.id} style={s.small}>• {item.title}</Text>)}{useProfile&&preview.excluded.map((item,index)=><View key={index}><Text style={s.label}>{item.title}</Text><Text style={s.small}>{item.reason}</Text></View>)}</>}
  <Button secondary title="Заполнить профиль" onPress={()=>router.push('/profile')}/><Text style={s.small}>Вернитесь после сохранения профиля: состав обновится. Начатая оплата сохранит выбранные данные.</Text>
 </View>;
}
