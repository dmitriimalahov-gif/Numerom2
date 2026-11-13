import {useRef} from 'react';
import {Button,s} from '../ui';
import {Text,View} from 'react-native';
import {DockedVideo} from '../video/DockedVideo.web';
import {useReportPlaybackRate} from '../../lib/usePlaybackRate';
import {PlaybackSpeed} from '../audio/PlaybackSpeed';
import type {ReportVideoPlayerProps} from './FullReportVideoPlayer';
export function FullReportVideoPlayer({source,chapters,onFailure,encodedSpeed=1,aspectRatio=16/9}:ReportVideoPlayerProps){
 const [rate,setRate]=useReportPlaybackRate(encodedSpeed);
 const player=useRef<HTMLVideoElement|null>(null);
 return <View style={{gap:12}}><DockedVideo source={source} rate={rate/encodedSpeed} video={player} onFailure={onFailure} title="Видеоверсия разбора" name="Персональная видеоверсия полного разбора" style={{width:'100%',aspectRatio,borderRadius:12,overflow:'hidden',background:'#132f43'}}/>
 <PlaybackSpeed rate={rate} onChange={setRate}/>
 {!!chapters.length&&<View style={{gap:8}}><Text style={s.label}>Главы видео</Text>{chapters.map(chapter=><Button secondary key={chapter.id} title={`${Math.floor(chapter.start_seconds/60)}:${String(Math.floor(chapter.start_seconds%60)).padStart(2,'0')} · ${chapter.title}`} onPress={()=>{if(player.current)player.current.currentTime=chapter.start_seconds;}}/>)}</View>}
 </View>;
}
