import {useSyncExternalStore} from 'react';
import {Pressable,StyleSheet,Text,View} from 'react-native';
import {useSafeAreaInsets} from 'react-native-safe-area-context';
import {router,type Href} from 'expo-router';
import {Ionicons} from '@expo/vector-icons';
import {nowPlaying} from '../../lib/nowPlaying.web';
import {colors as c} from '../../lib/theme';

const time=(value:number)=>`${Math.floor(Math.max(0,value)/60)}:${String(Math.floor(Math.max(0,value)%60)).padStart(2,'0')}`;
const visibleOnScreen=()=>{const track=nowPlaying.get();return !!track&&nowPlaying.visible(track.id);};

/** The narration the mini player shows: one started on another screen and not finished yet. */
export function useMiniPlayer(){
 const track=useSyncExternalStore(nowPlaying.subscribe,nowPlaying.get,nowPlaying.get);
 const own=useSyncExternalStore(nowPlaying.subscribe,visibleOnScreen,visibleOnScreen);
 return !track||own||track.ended?null:track;
}

// The narration started on another screen goes on here, at the bottom of every screen.
export function MediaDock(){
 const track=useMiniPlayer();
 const insets=useSafeAreaInsets();
 if(!track)return null;
 const progress=track.duration>0?Math.min(100,track.current/track.duration*100):0;
 const active=track.playing||track.busy;
 return <View accessibilityRole="toolbar" accessibilityLabel="Озвучка" style={[styles.dock,{paddingBottom:10+insets.bottom}]}>
  <View style={styles.track}><View style={[styles.fill,{width:`${progress}%`}]}/></View>
  <View style={styles.row}>
   <Pressable accessibilityRole="button" accessibilityLabel={`${active?'Пауза':'Слушать'}: ${track.title}`} accessibilityState={{busy:track.busy}}
    onPress={()=>{if(active)nowPlaying.pause();else void nowPlaying.resume();}} style={({pressed})=>[styles.play,pressed&&styles.pressed]}>
    <Ionicons name={active?'pause':'play'} size={22} color="#fff"/>
   </Pressable>
   <Pressable accessibilityRole="button" accessibilityLabel={`Вернуться к экрану: ${track.title}`} onPress={()=>router.dismissTo(track.href as Href)} style={styles.text}>
    <Text numberOfLines={1} style={styles.title}>{track.title}</Text>
    <Text numberOfLines={1} style={[styles.time,!!track.error&&styles.error]}>{track.error||(track.busy?'Загружается…':`${time(track.current)} / ${time(track.duration)}`)}</Text>
   </Pressable>
   <Pressable accessibilityRole="button" accessibilityLabel="Закрыть озвучку" onPress={()=>nowPlaying.close()} style={({pressed})=>[styles.close,pressed&&styles.pressed]}>
    <Ionicons name="close" size={22} color={c.navy}/>
   </Pressable>
  </View>
 </View>;
}
const styles=StyleSheet.create({
 dock:{backgroundColor:c.surface,borderTopWidth:1,borderTopColor:c.line,paddingHorizontal:14,paddingTop:0,gap:8},
 track:{height:3,marginHorizontal:-14,backgroundColor:'#C7DED3'},fill:{height:3,backgroundColor:c.green},
 row:{flexDirection:'row',alignItems:'center',gap:12,paddingTop:2},
 play:{width:44,height:44,borderRadius:22,alignItems:'center',justifyContent:'center',backgroundColor:'#003447'},
 text:{flex:1,minHeight:44,justifyContent:'center'},title:{fontSize:14,fontWeight:'600',color:c.ink},
 time:{fontSize:12,color:c.muted,fontVariant:['tabular-nums']},error:{color:c.error},
 close:{width:44,height:44,borderRadius:13,alignItems:'center',justifyContent:'center'},pressed:{backgroundColor:c.blue},
});
