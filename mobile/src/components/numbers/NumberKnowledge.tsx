import {useState} from 'react';
import {Pressable, StyleSheet, Text, View} from 'react-native';
import {knowledgeNumbers, numberKnowledge} from '../../lib/numberKnowledge';
import {NumberStory} from './NumberStory';
import {ReflectionComparison} from './ReflectionComparison';

export function NumberKnowledge() {
  const [digit,setDigit]=useState(1);
  return <View style={styles.section}>
    <Text accessibilityRole="header" style={styles.title}>Девять чисел — девять историй</Text>
    <Text style={styles.intro}>Выберите число. Прочитайте его историю или послушайте спокойное объяснение.</Text>
    <View accessibilityRole="tablist" accessibilityLabel="Значения чисел от 1 до 9" style={styles.tabs}>
      {knowledgeNumbers.map(number=><Pressable key={number} accessibilityRole="tab" accessibilityLabel={`Число ${number}: ${numberKnowledge(number)?.planet}`} accessibilityState={{selected:digit===number}}
        onPress={()=>setDigit(number)} style={({pressed})=>[styles.tab,digit===number&&styles.active,pressed&&{opacity:.75}]}>
        <Text style={[styles.digit,digit===number&&styles.activeText]}>{number}</Text><Text style={[styles.name,digit===number&&styles.activeText]}>{numberKnowledge(number)?.planet}</Text>
      </Pressable>)}
    </View>
    <View style={styles.content}><NumberStory key={digit} digit={digit}/></View>
    <ReflectionComparison key={digit} digit={digit}/>
  </View>;
}
const styles=StyleSheet.create({
  section:{gap:16},title:{fontSize:24,lineHeight:31,fontWeight:'600',color:'#003447'},intro:{fontSize:15,lineHeight:23,color:'#536D63'},
  tabs:{flexDirection:'row',flexWrap:'wrap',gap:8},tab:{flexBasis:'30%',flexGrow:1,minHeight:58,padding:10,borderRadius:13,backgroundColor:'#E8F4EE',flexDirection:'row',gap:9,alignItems:'center',borderWidth:1,borderColor:'#D2E4DA'},
  active:{backgroundColor:'#003447',borderColor:'#003447'},digit:{fontSize:23,color:'#003447',fontWeight:'500'},name:{fontSize:12,color:'#365B52',flexShrink:1},activeText:{color:'#fff'},
  content:{padding:18,borderRadius:18,backgroundColor:'#fff',borderWidth:1,borderColor:'#DDE9E1'},note:{fontSize:12,lineHeight:19,color:'#536D63'},
});
