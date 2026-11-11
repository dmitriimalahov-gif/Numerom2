import {loadTelegram,telegramContext} from './telegram';
import React, { createContext, useContext, useEffect, useState, useSyncExternalStore } from 'react';
import { AppState, Platform } from 'react-native';
import Constants from 'expo-constants';
import {clientUrls} from './config';
import {createBiometricVault} from './biometricVault';
import {appSessionLifecycle} from './appSessionLifecycle';
import {createCreditNotice} from './creditNotice';
import {createEndpointResolver} from './runtimeEndpoint';
import {registerReportPdf} from './reportPdf';
import {readyReport} from './readyReport';
import endpointTrust from './endpointTrust.json';
import bundledEndpoint from '../../public/runtime-config.json';
import {Button,Brand,Heading,Loading,Notice,Screen} from '../components/ui';
import * as SecureStore from 'expo-secure-store';
import { createApiClient, createSessionController, SessionController } from '@numerom/api-client';

const configuredUrls = clientUrls(Constants.expoConfig?.extra, Platform.OS);
export let backendUrl = configuredUrls.backendUrl;
export const websiteUrl = configuredUrls.websiteUrl;
const endpointKey='numerom.endpoint.v1';
const endpoints=Constants.expoConfig?.extra?.production?createEndpointResolver({
 bundled:bundledEndpoint,...endpointTrust,onChange:origin=>{backendUrl=origin;},
 storage:Platform.OS==='web'?{get:async()=>window.localStorage.getItem(endpointKey),set:async value=>{window.localStorage.setItem(endpointKey,value);}}:
 {get:()=>SecureStore.getItemAsync(endpointKey),set:value=>SecureStore.setItemAsync(endpointKey,value)},
}):null;
const key = 'numerom.session.v1';
const nativeStore = (name:string, options:SecureStore.SecureStoreOptions={}) => ({
 get:()=>SecureStore.getItemAsync(name,options),set:(value:string)=>SecureStore.setItemAsync(name,value,options),remove:()=>SecureStore.deleteItemAsync(name,options),
});
const vault=createBiometricVault({plain:nativeStore(key),flag:nativeStore('numerom.biometric.enabled'),
 protectedStore:nativeStore('numerom.biometric.session',{requireAuthentication:true,authenticationPrompt:'Вход в NumerOM',keychainService:'numerom.biometric.v1',keychainAccessible:SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY}),
 available:()=>Platform.OS!=='web'&&Constants.appOwnership!=='expo'&&SecureStore.canUseBiometricAuthentication(),
});
const storage = Platform.OS==='web'?{
 get:async()=>window.sessionStorage.getItem(key),set:async(value:string)=>{window.sessionStorage.setItem(key,value);},remove:async()=>{window.sessionStorage.removeItem(key);},
}:vault;
function createRuntime() {
  let session: SessionController;
  const creditNotice = createCreditNotice();
  const api = createApiClient({ baseUrl: backendUrl, getBaseUrl:endpoints?async()=>{const url=await endpoints.ready();if(!url)throw Error('Не удалось получить адрес NumerOM. Повторите подключение.');return url;}:undefined,
    onConnectionFailure:endpoints?.recover, getToken: () => session?.getToken() || null, onUnauthorized: token => session.invalidate(token), onInsufficientCredits: creditNotice.serverRefused });
  session = createSessionController({api, storage});
  registerReportPdf(api.request);
  let owner:string|null=null;
  session.subscribe(()=>{
   const state=session.getSnapshot();
   creditNotice.sync(state.status==='signedIn'?session.getToken():null,state.user?.credits_remaining);
   // A prepared PDF belongs to the account that asked for it: signing out or in as someone else drops it.
   const account=state.status==='signedIn'?state.user?.id??null:null;
   if(account!==owner){owner=account;readyReport.set(null);}
  });
  return {api, session, creditNotice, biometrics:vault};
}
const Context = createContext<ReturnType<typeof createRuntime> | null>(null);
export function SessionProvider({children}: {children: React.ReactNode}) {
  const [runtime] = useState(createRuntime);
  const [telegramReady,setTelegramReady]=useState(false),[telegramError,setTelegramError]=useState('');
  useEffect(() => {let active=true;void(async()=>{
   try{if(telegramContext())await loadTelegram();if(active){setTelegramReady(true);await runtime.session.restore();}}
   catch{if(active)setTelegramError('Не удалось подключить Telegram. Закройте мини-приложение и откройте его из меню бота снова.');}
  })();return()=>{active=false;};}, [runtime]);
  const state=useSyncExternalStore(runtime.session.subscribe,runtime.session.getSnapshot,runtime.session.getSnapshot);
  useEffect(()=>{
   if(Platform.OS==='web')return;
   const listener=AppState.addEventListener('change',appSessionLifecycle(runtime.session));
   return()=>listener.remove();
  },[runtime]);
  useEffect(()=>{
   let active=true,busy=false;
   async function reconnect(){
    if(!active||busy||Platform.OS==='web'&&document.hidden)return;
    busy=true;
    try{
     await endpoints?.refresh();
     if(!active)return;
     if(runtime.session.getSnapshot().status==='unavailable')await runtime.session.restore();
    }finally{busy=false;}
   }
   const timer=setInterval(()=>void reconnect(),30000);
   const listener=AppState.addEventListener('change',next=>{if(next==='active')void reconnect();});
   if(Platform.OS==='web'){window.addEventListener('online',reconnect);document.addEventListener('visibilitychange',reconnect);}
   return()=>{active=false;clearInterval(timer);listener.remove();if(Platform.OS==='web'){window.removeEventListener('online',reconnect);document.removeEventListener('visibilitychange',reconnect);}};
  },[runtime]);
  return <Context.Provider value={runtime}>{!telegramReady?<Screen>{telegramError?<Notice message={telegramError}/>:<Loading/>}</Screen>:state.status==='locked'?<BiometricLock/>:children}</Context.Provider>;
}
export function useSession() {
  const runtime = useContext(Context);
  if (!runtime) throw new Error('SessionProvider is missing');
  const state = useSyncExternalStore(runtime.session.subscribe, runtime.session.getSnapshot, runtime.session.getSnapshot);
  return {...runtime, ...state};
}

function BiometricLock(){
 const {session,error}=useSession();const [busy,setBusy]=useState(false);const [message,setMessage]=useState('');
 const run=async(action:()=>Promise<void>)=>{if(busy)return;setBusy(true);setMessage('');try{await action();}catch(e){setMessage(e instanceof Error?e.message:'Попробуйте ещё раз.');}finally{setBusy(false);}};
 return <Screen><Brand/><Heading title="С возвращением" subtitle="Подтвердите вход с помощью Face ID или отпечатка пальца."/>{!!(message||error)&&<Notice message={message||error||''}/>}<Button title="Разблокировать NumerOM" busy={busy} onPress={()=>void run(()=>session.restore(true))}/><Button secondary title="Войти с паролем" disabled={busy} onPress={()=>void run(()=>session.signOut())}/></Screen>;
}
