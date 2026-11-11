import {useCallback, useEffect, useRef, useState} from 'react';
import {setAudioModeAsync, useAudioPlayer, useAudioPlayerStatus} from 'expo-audio';
import {releaseAudioFocus, takeAudioFocus} from '../../lib/audioFocus';
import {holdScreen, releaseScreen} from '../../lib/wakeLock';
import {VoiceControls} from '../numbers/VoiceControls';
import {usePlaybackRate} from '../../lib/usePlaybackRate';

export function AudioTrack({source,seconds,label,digit}:{source:number|string;seconds:number;label?:string;digit?:number;trackId?:string}) {
  const player=useAudioPlayer((typeof source==='string'?{uri:source}:source),{updateInterval:250});
  const status=useAudioPlayerStatus(player);
  const [rate,setRate]=usePlaybackRate();
  useEffect(()=>{try{player.shouldCorrectPitch=true;player.setPlaybackRate(rate,'high');}catch{}},[player,rate]);
  const [error,setError]=useState(''),[pending,setPending]=useState(false);
  const request=useRef(0),intent=useRef(false),tag=useRef(`narration-${Math.random().toString(36).slice(2)}`);
  const stop=useCallback(()=>{request.current++;intent.current=false;setPending(false);try{player.pause();}catch{}releaseAudioFocus(stop);},[player]);
  // The recording goes on on other screens and with the phone locked; it stops only when this player closes.
  useEffect(()=>()=>{request.current++;intent.current=false;releaseAudioFocus(stop);releaseScreen(tag.current);},[stop]);
  useEffect(()=>{if(status.playing)holdScreen(tag.current);else releaseScreen(tag.current);},[status.playing]);
  useEffect(()=>{
    if(status.playing)setPending(false);
    if(status.didJustFinish){intent.current=false;setPending(false);releaseAudioFocus(stop);}
  },[status.didJustFinish,status.playing,stop]);
  useEffect(()=>{
    if(!pending)return;
    const id=request.current;
    const timer=setTimeout(()=>{if(id===request.current){stop();setError('Запись долго загружается. Попробуйте ещё раз.');}},15000);
    return ()=>clearTimeout(timer);
  },[pending,stop]);
  const play=async()=>{
    const id=++request.current;intent.current=true;setPending(true);setError('');
    try {
      await setAudioModeAsync({playsInSilentMode:true,allowsRecording:false,shouldPlayInBackground:true,interruptionMode:'doNotMix'});
      if(id!==request.current)return;
      if(status.didJustFinish||status.currentTime>=seconds-.15)await player.seekTo(0);
      if(id!==request.current)return;
      takeAudioFocus(stop);player.play();
    }catch{if(id===request.current){stop();setError('Не удалось включить запись. Попробуйте ещё раз.');}}
  };
  return <VoiceControls digit={digit} label={label} playing={status.playing} busy={pending||(intent.current&&status.isBuffering)} current={status.currentTime||0} duration={status.duration||seconds}
    error={error||(/error|failed/i.test(status.playbackState)?'Запись не загрузилась. Попробуйте ещё раз.':'')}
    onToggle={()=>{if(status.playing||intent.current)stop();else void play();}}
    onRestart={()=>{stop();setError('');void player.seekTo(0).catch(()=>setError('Не удалось вернуться к началу записи.'));}}
    rate={rate} onRate={setRate}/>;
}
