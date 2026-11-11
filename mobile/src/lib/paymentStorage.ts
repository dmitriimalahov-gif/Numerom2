import {Platform} from 'react-native';
import * as SecureStore from 'expo-secure-store';
export type PendingPayment={request_id:string;package_type:string;session_id?:string};
const key=(userId:string)=>'numerom.payment.'+userId.replace(/[^A-Za-z0-9._-]/g,'_');
export async function readPayment(userId:string):Promise<PendingPayment|null>{
 const raw=Platform.OS==='web'?window.sessionStorage.getItem(key(userId)):await SecureStore.getItemAsync(key(userId));
 if(!raw)return null;
 try{const p=JSON.parse(raw);return typeof p.request_id==='string'&&typeof p.package_type==='string'?p:null;}catch{return null;}
}
export async function savePayment(userId:string,pending:PendingPayment|null){
 if(Platform.OS==='web'){if(pending)window.sessionStorage.setItem(key(userId),JSON.stringify(pending));else window.sessionStorage.removeItem(key(userId));}
 else if(pending)await SecureStore.setItemAsync(key(userId),JSON.stringify(pending));else await SecureStore.deleteItemAsync(key(userId));
}
