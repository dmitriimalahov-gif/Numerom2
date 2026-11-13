import {useEffect, useState} from 'react';
import {Platform} from 'react-native';
import * as SecureStore from 'expo-secure-store';
import {getPlaybackRate, setPlaybackRate, subscribePlaybackRate, validRate,reportPlaybackRate} from './playbackRate';

const KEY = 'numerom.playback-rate';
let restored = false;

async function restore() {
  if (restored) return;
  restored = true;
  try {
    const raw = Platform.OS === 'web' ? window.localStorage.getItem(KEY) : await SecureStore.getItemAsync(KEY);
    if (raw) setPlaybackRate(validRate(Number(raw)));
  } catch {}
}

function persist(value: number) {
  try {
    if (Platform.OS === 'web') window.localStorage.setItem(KEY, String(value));
    else void SecureStore.setItemAsync(KEY, String(value)).catch(() => {});
  } catch {}
}

/** The shared listening speed and a setter that remembers it on this device. */
export function usePlaybackRate(): [number, (value: number) => void] {
  const [rate, setRate] = useState(getPlaybackRate());
  useEffect(() => {
    const unsubscribe = subscribePlaybackRate(setRate);
    void restore();
    setRate(getPlaybackRate());
    return unsubscribe;
  }, []);
  return [rate, value => persist(setPlaybackRate(value))];
}

/** Authored video tempo is the initial rate; explicit player controls override it. */
export function useReportPlaybackRate(encodedSpeed:number): [number,(value:number)=>void] {
  const [shared,setShared]=usePlaybackRate();
  const [selected,setSelected]=useState<number|null>(null);
  return [reportPlaybackRate(encodedSpeed,selected,shared),value=>{setSelected(value);setShared(value);}];
}
