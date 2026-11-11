import {useCallback,useEffect,useRef,useState,useSyncExternalStore} from 'react';
import {AppState,Linking,Platform} from 'react-native';
import {useFocusEffect} from 'expo-router';
import {useSession} from './session';
import {safeLearningUrl} from './learning';
import {createMaterialAccess} from './materialAccess';

export function useMaterialAccess(){
 const {session,user}=useSession();
 const focused=useRef(false);
 const [access]=useState(()=>{
  const owner=user?.id,token=session.getToken();
  return createMaterialAccess({openUrl:url=>Linking.openURL(url),validateUrl:safeLearningUrl,isCurrent:()=>focused.current&&session.getSnapshot().status==='signedIn'&&session.getSnapshot().user?.id===owner&&session.getToken()===token});
 });
 useFocusEffect(useCallback(()=>{focused.current=true;return()=>{focused.current=false;access.cancel();};},[access]));
 useEffect(()=>{
  if(Platform.OS==='web'){
   const hidden=()=>{if(document.hidden)access.cancel();};
   document.addEventListener('visibilitychange',hidden);
   return()=>document.removeEventListener('visibilitychange',hidden);
  }
  const listener=AppState.addEventListener('change',state=>{if(state==='background')access.cancel();});
  return()=>listener.remove();
 },[access]);
 const state=useSyncExternalStore(access.subscribe,access.getSnapshot,access.getSnapshot);
 return {...state,open:access.open,isOpening:access.isOpening};
}
