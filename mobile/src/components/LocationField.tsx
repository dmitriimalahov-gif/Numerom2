import {useCallback,useEffect,useRef,useState,useSyncExternalStore} from 'react';
import {AppState,Linking,Platform,Text,View} from 'react-native';
import {useFocusEffect} from 'expo-router';
import {Button,Field,Notice,s} from './ui';
import {locate,watchLocation} from '../lib/deviceLocation';
import {createLocationSelection,SelectedLocation} from '../lib/locationSelection';
import {useSession} from '../lib/session';
import {colors} from '../lib/theme';

export function LocationField({value,onChange,disabled=false,allowLive=false,onBusyChange}:{value:string;onChange:(city:string,point?:{latitude:number;longitude:number})=>void;disabled?:boolean;allowLive?:boolean;onBusyChange?:(busy:boolean)=>void}){
 const {api,user,session}=useSession();
 const owner=user?.id,props=useRef({onChange,disabled}),focused=useRef(false);
 props.current={onChange,disabled};
 const [controller]=useState(()=>createLocationSelection({locate,watchLocation,
  resolve:point=>api.request('/numerology/vedic/location',{method:'POST',body:point,timeoutMs:15000}) as Promise<SelectedLocation>,
  isCurrent:()=>focused.current&&!props.current.disabled&&session.getSnapshot().user?.id===owner,
  onSelect:place=>props.current.onChange(place.city,{latitude:place.latitude,longitude:place.longitude}),
 }));
 const state=useSyncExternalStore(controller.subscribe,controller.getSnapshot,controller.getSnapshot);
 useEffect(()=>{onBusyChange?.(state.busy);return()=>onBusyChange?.(false);},[state.busy,onBusyChange]);
 useFocusEffect(useCallback(()=>{focused.current=true;return()=>{focused.current=false;controller.stop();};},[controller]));
 useEffect(()=>{if(disabled)controller.stop();},[disabled,controller]);
 useEffect(()=>{
  const pause=()=>controller.stop('Определение геолокации остановлено.');
  // Permission sheets can briefly make iOS inactive; only leaving the app ends observation.
  const app=AppState.addEventListener('change',next=>{if(next==='background')pause();});
  const visibility=()=>{if(document.hidden)pause();};
  if(Platform.OS==='web')document.addEventListener('visibilitychange',visibility);
  return()=>{app.remove();if(Platform.OS==='web')document.removeEventListener('visibilitychange',visibility);controller.stop();};
 },[controller]);
 return <View style={{gap:10}}>
  <Field label="Город и страна" value={value} maxLength={120} placeholder="Например: Кишинёв, Молдова" editable={!disabled} onChangeText={city=>{controller.clear();onChange(city);}}/>
  <Button secondary title="Определить мой город" busy={state.busy&&!state.live} disabled={disabled||state.live} onPress={()=>void controller.locate()}/>
  {allowLive&&<Button secondary title={state.live?'Остановить трансляцию':'Транслировать геолокацию'} disabled={disabled||(!state.live&&state.busy)} onPress={()=>state.live?controller.stop('Трансляция остановлена.'):void controller.startLive()}/>}
  {(state.live||state.busy)&&<Text accessibilityLiveRegion="polite" style={[s.label,{color:colors.green}]}>{state.live?'● Трансляция включена':'Определяем местоположение…'}{state.busy&&state.live?' · определяем город…':''}</Text>}
  {state.location&&<Text style={s.small}>По геолокации: {state.location.city} · {state.location.timezone}{state.accuracy!==null?` · точность около ${state.accuracy<1000?`${Math.round(state.accuracy)} м`:`${(state.accuracy/1000).toFixed(1)} км`}`:''}</Text>}
  {!!state.message&&<Text accessibilityLiveRegion="polite" style={s.small}>{state.message}</Text>}
  {!!state.error&&<Notice message={state.error}/>}
  <Text style={s.small}>{allowLive?'Город обновляется, пока открыт этот экран. В отчёте сохраняется место на момент расчёта. ':'Город подставится в форму; сохраните изменения в профиле. '}Доступ запрашивается с вашего разрешения. Координаты передаются сервису определения города; непрерывная история перемещений не ведётся.</Text>
  {state.location&&<Text accessibilityRole="link" onPress={()=>void Linking.openURL('https://www.openstreetmap.org/copyright')} style={s.small}>Геоданные © OpenStreetMap</Text>}
 </View>;
}
