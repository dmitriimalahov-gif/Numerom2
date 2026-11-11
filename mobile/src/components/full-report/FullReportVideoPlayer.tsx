import {useCallback,useEffect,useRef} from 'react';
import {Text,View} from 'react-native';
import {useFocusEffect} from 'expo-router';
import {useVideoPlayer,VideoView} from 'expo-video';
import {Button,s} from '../ui';
import {takeAudioFocus,releaseAudioFocus} from '../../lib/audioFocus';
import type {VideoChapter} from './videoState';
import {PlaybackSpeed} from '../audio/PlaybackSpeed';
import {usePlaybackRate} from '../../lib/usePlaybackRate';
import {holdScreen,releaseScreen} from '../../lib/wakeLock';

export type ReportVideoPlayerProps={source:string;chapters:VideoChapter[];onFailure:()=>void};
// Plays with the screen kept on; leaving the screen or the app moves it to the picture-in-picture window.
export function FullReportVideoPlayer({source,chapters,onFailure}:ReportVideoPlayerProps){
 const position=useRef(0),failure=useRef(onFailure),view=useRef<VideoView|null>(null);failure.current=onFailure;
 const player=useVideoPlayer({uri:source,contentType:'progressive'},instance=>{instance.loop=false;instance.staysActiveInBackground=true;instance.showNowPlayingNotification=true;instance.audioMixingMode='doNotMix';instance.timeUpdateEventInterval=1;instance.currentTime=position.current;});
 const stop=useCallback(()=>{try{player.pause();}catch{}releaseAudioFocus(stop);},[player]);
 const [rate,setRate]=usePlaybackRate();
 useEffect(()=>{try{player.preservesPitch=true;player.playbackRate=rate;}catch{}},[player,rate]);
 useFocusEffect(useCallback(()=>()=>{if(player.playing)void view.current?.startPictureInPicture().catch(()=>{});},[player]));
 useEffect(()=>{
  const playing=player.addListener('playingChange',event=>{
   if(event.isPlaying){takeAudioFocus(stop);holdScreen('report-video');}else{releaseAudioFocus(stop);releaseScreen('report-video');}
  });
  const clock=player.addListener('timeUpdate',event=>{position.current=event.currentTime;});
  const status=player.addListener('statusChange',event=>{if(event.status==='error')failure.current();});
  return()=>{playing.remove();clock.remove();status.remove();stop();releaseScreen('report-video');};
 },[player,stop]);
 return <View style={{gap:12}}><VideoView ref={view} player={player} nativeControls contentFit="contain" fullscreenOptions={{enable:true}} allowsPictureInPicture startsPictureInPictureAutomatically style={{width:'100%',aspectRatio:16/9,borderRadius:12,backgroundColor:'#132f43'}} accessibilityLabel="Персональная видеоверсия полного разбора"/>
  <PlaybackSpeed rate={rate} onChange={setRate}/>
  {!!chapters.length&&<View style={{gap:8}}><Text style={s.label}>Главы видео</Text>{chapters.map(chapter=><Button key={chapter.id} secondary title={`${Math.floor(chapter.start_seconds/60)}:${String(Math.floor(chapter.start_seconds%60)).padStart(2,'0')} · ${chapter.title}`} onPress={()=>{try{player.currentTime=chapter.start_seconds;position.current=chapter.start_seconds;}catch{failure.current();}}}/>)}</View>}
 </View>;
}
