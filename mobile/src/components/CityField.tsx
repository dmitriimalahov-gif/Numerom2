import {useCallback,useEffect,useState,useSyncExternalStore} from 'react';
import {Linking,Pressable,Text,View} from 'react-native';
import {useFocusEffect} from 'expo-router';
import {createCitySearch,CitySuggestion} from '@numerom/api-client/cities';
import {useSession} from '../lib/session';
import {Field,s} from './ui';
import {colors} from '../lib/theme';

export function CityField({value,onChange,disabled=false}:{value:string;onChange:(value:string,id:string)=>void;disabled?:boolean}){
 const {api}=useSession();const [controller]=useState(()=>createCitySearch({request:(...args)=>api.request(...args)}));
 const state=useSyncExternalStore(controller.subscribe,controller.getSnapshot,controller.getSnapshot),[searched,setSearched]=useState(false),[active,setActive]=useState(-1);
 useEffect(()=>()=>controller.dispose(),[controller]);
 useFocusEffect(useCallback(()=>()=>controller.clear(),[controller]));
 useEffect(()=>{if(disabled)controller.clear();},[disabled,controller]);
 function choose(item:CitySuggestion){controller.clear();setSearched(false);setActive(-1);onChange(item.label,item.id);}
 return <View style={{gap:10}}><Field label="Город рождения" value={value} editable={!disabled} maxLength={300} autoCorrect={false} placeholder="Начните вводить название города" onChangeText={text=>{onChange(text,'');setActive(-1);setSearched(text.trim().length>=2);controller.search(text);}} onKeyPress={event=>{const key=event.nativeEvent.key;if(key==='Escape'){controller.clear();setSearched(false);}else if(state.items.length&&['ArrowDown','ArrowUp'].includes(key))setActive(index=>(index+(key==='ArrowDown'?1:-1)+state.items.length)%state.items.length);}} onSubmitEditing={()=>{if(active>=0&&state.items[active])choose(state.items[active]);}}/>
  {state.busy&&<Text accessibilityLiveRegion="polite" style={s.small}>Ищем города…</Text>}
  {state.items.map((item,index)=><Pressable key={item.id} accessibilityRole="button" accessibilityLabel={`${item.name}, ${item.region}, ${item.country}`} onPress={()=>choose(item)} style={{padding:13,minHeight:52,borderWidth:1,borderColor:colors.line,borderRadius:12,backgroundColor:index===active?colors.blue:colors.surface,gap:4}}><Text style={s.label}>{item.name}</Text><Text style={s.small}>{[item.region,item.country].filter(Boolean).join(', ')}</Text></Pressable>)}
  {!!state.error&&<Text accessibilityLiveRegion="polite" style={s.small}>{state.error}</Text>}
  {searched&&!state.busy&&!state.error&&!state.items.length&&<Text accessibilityLiveRegion="polite" style={s.small}>Нет совпадений. Попробуйте другое написание или оставьте город, регион и страну вручную.</Text>}
  <Text style={s.small}>Город рождения не заменяет текущий город. Мелкого населённого пункта может не быть в справочнике.</Text><Text accessibilityRole="link" style={s.link} onPress={()=>void Linking.openURL('https://www.geonames.org/')}>Геоданные GeoNames · CC BY 4.0</Text>
 </View>;
}
