import {useCallback, useSyncExternalStore} from 'react';
import {useFocusEffect,usePathname} from 'expo-router';
import {Asset} from 'expo-asset';
import {nowPlaying} from '../../lib/nowPlaying.web';
import {VoiceControls} from '../numbers/VoiceControls';
import {usePlaybackRate} from '../../lib/usePlaybackRate';

// The recording plays in the app-wide player: it goes on after the listener leaves this screen
// (the mini player at the bottom takes over) and while the phone is locked.
export function AudioTrack({source,seconds,label,digit,trackId}:{source:number|string;seconds:number;label?:string;digit?:number;trackId?:string}) {
  const uri=typeof source==='string'?source:Asset.fromModule(source).uri;
  // A refreshed link signature is the same recording.
  const id=trackId||uri.split('?')[0];
  const track=useSyncExternalStore(nowPlaying.subscribe,nowPlaying.get,nowPlaying.get);
  const mine=track?.id===id?track:null;
  const [rate,setRate]=usePlaybackRate(),href=usePathname();
  useFocusEffect(useCallback(()=>nowPlaying.show(id),[id]));
  const playing=!!mine?.playing,busy=!!mine?.busy;
  return <VoiceControls digit={digit} label={label} playing={playing} busy={busy} current={mine?.current||0} duration={mine?.duration||seconds} error={mine?.error||''}
    onToggle={()=>{if(playing||busy)nowPlaying.pause();else void nowPlaying.play({id,source:uri,title:label||`Число ${digit}`,href,seconds});}}
    onRestart={()=>{if(mine){nowPlaying.pause();nowPlaying.seek(0);}}}
    rate={rate} onRate={setRate}/>;
}
