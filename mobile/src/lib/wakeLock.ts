import {activateKeepAwakeAsync,deactivateKeepAwake} from 'expo-keep-awake';

// Keeps the phone screen on while a recording or video plays.
export function holdScreen(tag:string){void activateKeepAwakeAsync(tag).catch(()=>{});}
export function releaseScreen(tag:string){try{void deactivateKeepAwake(tag);}catch{}}
