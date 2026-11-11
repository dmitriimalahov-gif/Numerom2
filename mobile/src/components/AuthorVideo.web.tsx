import {Asset} from 'expo-asset';
import {useWindowDimensions,View} from 'react-native';
import {PlaybackSpeed} from './audio/PlaybackSpeed';
import {DockedVideo} from './video/DockedVideo.web';
import {usePlaybackRate} from '../lib/usePlaybackRate';

export function AuthorVideo({source,tall}:{source:number;tall:boolean}){
 const {height}=useWindowDimensions();
 const [rate,setRate]=usePlaybackRate();
 return <View style={{gap:12}}><DockedVideo autoPlay source={Asset.fromModule(source).uri} rate={rate} title="Слово автора" name="Видеообращение автора NumerOM"
   style={tall?{width:'100%',maxWidth:Math.round(height*.7*9/16),aspectRatio:'9/16',alignSelf:'center',borderRadius:12,overflow:'hidden',background:'#F4F7FB'}:{width:'100%',aspectRatio:'16/9',borderRadius:12,overflow:'hidden',background:'#F4F7FB'}}/>
  <PlaybackSpeed rate={rate} onChange={setRate}/></View>;
}
