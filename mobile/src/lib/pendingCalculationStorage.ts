import {Platform} from 'react-native';
import * as SecureStore from 'expo-secure-store';
// Account and calculation kind never share pending payment intents.
export function pendingCalculationStorage(userId:string,kind:string){
 const key='numerom.calculation.'+encodeURIComponent(userId).replace(/%/g,'_')+'.'+kind;
 return {get:async()=>{const raw=Platform.OS==='web'?window.sessionStorage.getItem(key):await SecureStore.getItemAsync(key);return raw?JSON.parse(raw):null;},
 set:async(value:unknown)=>{const raw=value===null?null:JSON.stringify(value);
  if(Platform.OS==='web'){if(raw===null)window.sessionStorage.removeItem(key);else window.sessionStorage.setItem(key,raw);}
  else if(raw===null)await SecureStore.deleteItemAsync(key);else await SecureStore.setItemAsync(key,raw);
 }};
}
