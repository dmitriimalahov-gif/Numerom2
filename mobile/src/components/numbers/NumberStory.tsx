import {StyleSheet, Text, View} from 'react-native';
import {numberKnowledge} from '../../lib/numberKnowledge';
import {NumberVoice} from './NumberVoice';
import {NumberReflections} from './NumberReflections';

export function NumberStory({digit}:{digit:number}) {
  const entry=numberKnowledge(digit);
  if(!entry)return null;
  return <View style={styles.story}>
    <Text accessibilityRole="header" style={styles.title}>{entry.title}</Text>
    <View style={styles.voice}><Text style={styles.voiceLabel}>Озвучка основной истории</Text><NumberVoice key={digit} digit={digit}/></View>
    {entry.segments.map((paragraph,index)=><Text key={index} selectable style={styles.paragraph}>{paragraph}</Text>)}
    <NumberReflections key={digit} digit={digit}/>
  </View>;
}
const styles=StyleSheet.create({story:{gap:16},planet:{fontSize:13,lineHeight:20,color:'#28705E'},title:{fontSize:23,lineHeight:30,fontWeight:'600',color:'#003447'},paragraph:{fontSize:16,lineHeight:27,color:'#25444B'},voice:{gap:7},voiceLabel:{fontSize:12,lineHeight:19,color:'#536D63'}});
