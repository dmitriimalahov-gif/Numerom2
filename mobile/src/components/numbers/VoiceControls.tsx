import {Pressable, StyleSheet, Text, View} from 'react-native';
import {PlaybackSpeed} from '../audio/PlaybackSpeed';

const time = (value:number) => `${Math.floor(Math.max(0,value)/60)}:${String(Math.floor(Math.max(0,value)%60)).padStart(2,'0')}`;
export function VoiceControls({digit,label,playing,busy,current,duration,error,onToggle,onRestart,rate,onRate}: {
  digit?:number; label?:string; playing:boolean; busy:boolean; current:number; duration:number; error:string;
  onToggle:()=>void; onRestart:()=>void; rate?:number; onRate?:(value:number)=>void;
}) {
  const progress=duration>0?Math.min(100,Math.max(0,current/duration*100)):0;
  const name=label || `Число ${digit}`;
  return <View style={styles.player}>
    <View style={styles.row}>
      <Pressable accessibilityRole="button" accessibilityLabel={label?`${playing?'Пауза':busy?'Отменить загрузку':error?'Повторить':'Слушать'}: ${label}`:`${playing?'Пауза':busy?'Отменить загрузку числа':error?'Повторить аудио':'Слушать число'} ${digit}`}
        accessibilityState={{busy}} onPress={onToggle} style={({pressed})=>[styles.play,pressed&&{opacity:.75}]}>
        <Text style={styles.symbol}>{playing?'Ⅱ':busy?'×':'▶'}</Text><Text style={styles.label}>{playing?'Пауза':busy?'Отмена':error?'Повторить':'Слушать'}</Text>
      </Pressable>
      <Text style={styles.time}>{time(current)} / {time(duration)}</Text>
      <Pressable accessibilityRole="button" accessibilityLabel={`${name}: сначала`} onPress={onRestart} style={styles.restart}><Text style={styles.restartText}>↺</Text></Pressable>
    </View>
    <View accessibilityRole="progressbar" accessibilityLabel={`Прослушано, ${name}`} accessibilityValue={{min:0,max:100,now:Math.round(progress)}} style={styles.track}><View style={[styles.fill,{width:`${progress}%`}]}/></View>
    {onRate && <PlaybackSpeed rate={rate??1} onChange={onRate}/>}
    {!!error && <Text accessibilityRole="alert" style={styles.error}>{error}</Text>}
  </View>;
}
const styles=StyleSheet.create({
  player:{gap:12,padding:14,borderRadius:16,backgroundColor:'#E8F4EE'},row:{flexDirection:'row',alignItems:'center',gap:10},
  play:{minHeight:48,flex:1,flexDirection:'row',alignItems:'center',justifyContent:'center',gap:8,paddingHorizontal:10,borderRadius:12,backgroundColor:'#003447'},
  symbol:{color:'#fff',fontSize:15},label:{color:'#fff',fontSize:14,fontWeight:'600'},time:{fontSize:12,color:'#365B52',fontVariant:['tabular-nums']},
  restart:{minWidth:44,minHeight:48,justifyContent:'center',alignItems:'center'},restartText:{color:'#003447',fontSize:27},
  track:{height:4,borderRadius:2,overflow:'hidden',backgroundColor:'#C7DED3'},fill:{height:4,backgroundColor:'#28705E'},error:{color:'#9E3B35',fontSize:12,lineHeight:19},
});
