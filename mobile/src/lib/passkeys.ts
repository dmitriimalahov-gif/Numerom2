import type {ApiClient,UserProfile} from '@numerom/api-client';
export const passkeysAvailable=()=>typeof window!=='undefined'&&window.isSecureContext&&typeof PublicKeyCredential!=='undefined';
const decode=(value:string)=>Uint8Array.from(atob(value.replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0));
const encode=(value:ArrayBuffer|null)=>value?btoa(String.fromCharCode(...new Uint8Array(value))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,''):null;
type Ceremony={challenge_id:string;options:any};
async function ceremony(api:ApiClient,password?:string,label?:string){
 if(!passkeysAvailable())throw Error('Этот браузер не поддерживает ключи доступа. Используйте вход с паролем.');
 const registration=password!==undefined,prefix=registration?'/user/passkeys':'/auth/passkeys';
 const data=await api.request<Ceremony>(`${prefix}/options`,{method:'POST',auth:registration,body:registration?{password}:{}});
 const options={...data.options,challenge:decode(data.options.challenge)};
 if(registration){options.user={...options.user,id:decode(options.user.id)};options.excludeCredentials=(options.excludeCredentials||[]).map((c:any)=>({...c,id:decode(c.id)}));}
 else options.allowCredentials=(options.allowCredentials||[]).map((c:any)=>({...c,id:decode(c.id)}));
 let credential:PublicKeyCredential|null;
 try{credential=await (registration?navigator.credentials.create({publicKey:options}):navigator.credentials.get({publicKey:options})) as PublicKeyCredential|null;}
 catch(e){if(e instanceof DOMException&&e.name==='NotAllowedError')throw Error('Подтверждение отменено или истекло. Можно повторить или войти с паролем.');throw Error('Не удалось использовать ключ доступа на этом устройстве.');}
 if(!credential)throw Error('Подтверждение отменено.');
 const response=credential.response as AuthenticatorAttestationResponse&AuthenticatorAssertionResponse;
 const proof={id:credential.id,rawId:encode(credential.rawId),type:credential.type,response:{clientDataJSON:encode(response.clientDataJSON),
  ...(registration?{attestationObject:encode(response.attestationObject),transports:response.getTransports?.()||[]}: {authenticatorData:encode(response.authenticatorData),signature:encode(response.signature),userHandle:encode(response.userHandle)})}};
 return api.request<any>(`${prefix}/verify`,{method:'POST',auth:registration,body:{challenge_id:data.challenge_id,credential:proof,...(registration?{label:label?.trim()||'Моё устройство'}:{})}});
}
export const signInWithPasskey=(api:ApiClient):Promise<{access_token:string;user:UserProfile}>=>ceremony(api);
export const registerPasskey=(api:ApiClient,password:string,label:string)=>ceremony(api,password,label);
