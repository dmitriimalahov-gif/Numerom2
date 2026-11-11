import {Platform} from 'react-native';
import * as SecureStore from 'expo-secure-store';
import {validBirthDate} from '../../../packages/full-report';
export type FullReportAttempt={request_id:string;birth_date:string;order_id?:string;use_profile?:boolean;profile_stale?:boolean;profile_fingerprint?:string|null};
const key=(id:string)=>'numerom.full-report.'+id.replace(/[^A-Za-z0-9._-]/g,'_');
export async function readReportAttempt(id:string):Promise<FullReportAttempt|null>{
 const raw=Platform.OS==='web'?window.sessionStorage.getItem(key(id)):await SecureStore.getItemAsync(key(id));
 try{const p=JSON.parse(raw||'null');return p&&/^[a-f0-9-]{36}$/i.test(p.request_id)&&validBirthDate(p.birth_date)&&(!p.order_id||/^[a-f0-9]{64}$/.test(p.order_id))?p:null;}catch{return null;}
}
export async function saveReportAttempt(id:string,value:FullReportAttempt|null){
 if(Platform.OS==='web'){if(value)window.sessionStorage.setItem(key(id),JSON.stringify(value));else window.sessionStorage.removeItem(key(id));}
 else if(value)await SecureStore.setItemAsync(key(id),JSON.stringify(value));else await SecureStore.deleteItemAsync(key(id));
}
