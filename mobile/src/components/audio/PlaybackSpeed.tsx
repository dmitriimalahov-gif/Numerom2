import {Pressable, StyleSheet, Text, View} from 'react-native';
import {RATES, rateLabel} from '../../lib/playbackRate';

export function PlaybackSpeed({rate,onChange}:{rate:number;onChange:(value:number)=>void}) {
  return <View accessibilityRole="radiogroup" accessibilityLabel="Скорость воспроизведения" style={styles.row}>
    <Text style={styles.caption}>Скорость</Text>
    {RATES.map(value=>{
      const selected=value===rate;
      return <Pressable key={value} accessibilityRole="radio" accessibilityLabel={`Скорость ${rateLabel(value)}`}
        accessibilityState={{selected,checked:selected}} onPress={()=>onChange(value)}
        style={({pressed})=>[styles.chip,selected&&styles.selected,pressed&&{opacity:.75}]}>
        <Text style={[styles.text,selected&&styles.selectedText]}>{rateLabel(value)}</Text>
      </Pressable>;
    })}
  </View>;
}
const styles=StyleSheet.create({
  row:{flexDirection:'row',alignItems:'center',flexWrap:'wrap',gap:6},
  caption:{fontSize:12,color:'#365B52',marginRight:2},
  chip:{minHeight:36,minWidth:44,paddingHorizontal:8,justifyContent:'center',alignItems:'center',borderRadius:10,borderWidth:1,borderColor:'#9CC4B4',backgroundColor:'#fff'},
  selected:{backgroundColor:'#003447',borderColor:'#003447'},
  text:{fontSize:13,color:'#003447',fontVariant:['tabular-nums']},selectedText:{color:'#fff',fontWeight:'600'},
});
