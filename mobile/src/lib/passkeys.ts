import type {ApiClient,UserProfile} from '@numerom/api-client';
export const passkeysAvailable=()=>typeof window!=='undefined'&&window.isSecureContext&&typeof PublicKeyCredential!=='undefined';
const passkeyPreference='numerom.passkey.autologin.v1';
export const passkeyAutoEntryEnabled=()=>{try{return typeof window!=='undefined'&&window.localStorage.getItem(passkeyPreference)==='1';}catch{return false;}};
export const rememberPasskeyForAutoEntry=()=>{try{if(typeof window!=='undefined')window.localStorage.setItem(passkeyPreference,'1');}catch{}}
export const forgetPasskeyForAutoEntry=()=>{try{if(typeof window!=='undefined')window.localStorage.removeItem(passkeyPreference);}catch{}}
export const currentPasskeyRpId=()=>{if(typeof window==='undefined')return null;const host=window.location.hostname;if(host==='1.numer.om')return '1.numer.om';return null;};
const decode=(value:string)=>Uint8Array.from(atob(value.replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0));
const encode=(value:ArrayBuffer|null)=>value?btoa(String.fromCharCode(...new Uint8Array(value))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,''):null;
type Ceremony={challenge_id:string;options:any};
async function ceremony(api:ApiClient,password?:string,label?:string,signal?:AbortSignal,timeoutMs?:number){
 if(!passkeysAvailable())throw Error('Этот браузер не поддерживает ключи доступа. Используйте вход с паролем.');
 const registration=password!==undefined,prefix=registration?'/user/passkeys':'/auth/passkeys';
 const data=await api.request<Ceremony>(`${prefix}/options`,{method:'POST',auth:registration,body:registration?{password}:{},signal});
 const options={...data.options,challenge:decode(data.options.challenge)};
 if(registration){options.user={...options.user,id:decode(options.user.id)};options.excludeCredentials=(options.excludeCredentials||[]).map((c:any)=>({...c,id:decode(c.id)}));}
 else options.allowCredentials=(options.allowCredentials||[]).map((c:any)=>({...c,id:decode(c.id)}));
 let credential:PublicKeyCredential|null;
 try{credential=await (registration?navigator.credentials.create({publicKey:options}):navigator.credentials.get({publicKey:{...options,...(!registration&&timeoutMs?{timeout:timeoutMs}:{})},signal})) as PublicKeyCredential|null;}
 catch(e){if(e instanceof DOMException&&e.name==='NotAllowedError')throw Error('Подтверждение отменено или истекло. Можно повторить или войти с паролем.');throw Error('Не удалось использовать ключ доступа на этом устройстве.');}
 if(!credential)throw Error('Подтверждение отменено.');
 const response=credential.response as AuthenticatorAttestationResponse&AuthenticatorAssertionResponse;
 const proof={id:credential.id,rawId:encode(credential.rawId),type:credential.type,response:{clientDataJSON:encode(response.clientDataJSON),
  ...(registration?{attestationObject:encode(response.attestationObject),transports:response.getTransports?.()||[]}: {authenticatorData:encode(response.authenticatorData),signature:encode(response.signature),userHandle:encode(response.userHandle)})}};
 const result=await api.request<any>(`${prefix}/verify`,{method:'POST',auth:registration,body:{challenge_id:data.challenge_id,credential:proof,...(registration?{label:label?.trim()||'Моё устройство'}:{})}});
 rememberPasskeyForAutoEntry();
 return result;
}
export const signInWithPasskey=(api:ApiClient,options:{signal?:AbortSignal;timeoutMs?:number}={}):Promise<{access_token:string;user:UserProfile}>=>ceremony(api,undefined,undefined,options.signal,options.timeoutMs);
export const registerPasskey=(api:ApiClient,password:string,label:string)=>ceremony(api,password,label);
