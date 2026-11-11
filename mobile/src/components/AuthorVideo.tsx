import {useCallback,useEffect,useRef} from 'react';
import {useWindowDimensions,View} from 'react-native';
import {useFocusEffect} from 'expo-router';
import {useVideoPlayer,VideoView} from 'expo-video';
import {PlaybackSpeed} from './audio/PlaybackSpeed';
import {usePlaybackRate} from '../lib/usePlaybackRate';
import {takeAudioFocus,releaseAudioFocus} from '../lib/audioFocus';
import {holdScreen,releaseScreen} from '../lib/wakeLock';

// Plays with the screen kept on; leaving the screen or the app moves it to the picture-in-picture window.
export function AuthorVideo({source,tall}:{source:number;tall:boolean}){
 const {height}=useWindowDimensions();
 const view=useRef<VideoView|null>(null);
 const player=useVideoPlayer(source,instance=>{instance.loop=false;instance.staysActiveInBackground=true;instance.showNowPlayingNotification=true;instance.audioMixingMode='doNotMix';instance.play();});
 const [rate,setRate]=usePlaybackRate();
 const stop=useCallback(()=>{try{player.pause();}catch{}releaseAudioFocus(stop);},[player]);
 useFocusEffect(useCallback(()=>()=>{if(player.playing)void view.current?.startPictureInPicture().catch(()=>{});},[player]));
 useEffect(()=>{try{player.preservesPitch=true;player.playbackRate=rate;}catch{}},[player,rate]);
 useEffect(()=>{
  const playing=player.addListener('playingChange',event=>{
   if(event.isPlaying){takeAudioFocus(stop);holdScreen('author-video');}else{releaseAudioFocus(stop);releaseScreen('author-video');}
  });
  return()=>{playing.remove();stop();releaseScreen('author-video');};
 },[player,stop]);
 return <View style={{gap:12}}><VideoView ref={view} player={player} nativeControls contentFit="contain" fullscreenOptions={{enable:true}} allowsPictureInPicture startsPictureInPictureAutomatically
   style={tall?{width:'100%',maxWidth:Math.round(height*.7*9/16),aspectRatio:9/16,alignSelf:'center',borderRadius:12,backgroundColor:'#F4F7FB'}:{width:'100%',aspectRatio:16/9,borderRadius:12,backgroundColor:'#F4F7FB'}} accessibilityLabel="Видеообращение автора NumerOM"/>
  <PlaybackSpeed rate={rate} onChange={setRate}/></View>;
}
