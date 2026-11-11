import {useState} from 'react';
import {Pressable, StyleSheet, Text, View} from 'react-native';
import {numberReflection} from '../../lib/reflectionKnowledge';

export function NumberReflections({digit}:{digit:number}) {
  const [expanded,setExpanded]=useState(false);
  const entry=numberReflection(digit);
  if(!entry)return null;

  return <View style={styles.section}>
    <Text accessibilityRole="header" style={styles.title}>Для размышления</Text>
    <Text selectable style={styles.copy}>{entry.sourceSummary}</Text>
    <Text style={styles.caption}>Пересказ материала и вопросы редакции NumerOM</Text>
    <Pressable accessibilityRole="button" accessibilityState={{expanded}}
      accessibilityLabel={expanded?'Свернуть размышления':'Развернуть размышления'}
      onPress={()=>setExpanded(value=>!value)}
      style={({pressed})=>[styles.toggle,pressed&&styles.pressed]}>
      <Text style={styles.toggleText}>{expanded?'Свернуть размышления':'Развернуть размышления'}</Text>
      <Text accessible={false} style={styles.toggleIcon}>{expanded?'−':'+'}</Text>
    </Pressable>
    {expanded&&<View style={styles.details}>
      <Text accessibilityRole="header" style={styles.subtitle}>{entry.title}</Text>
      {entry.reflection.map((paragraph,index)=><Text key={index} selectable style={styles.copy}>{paragraph}</Text>)}
      <View style={styles.questions}>
        <Text accessibilityRole="header" style={styles.subtitle}>Вопросы к себе</Text>
        {entry.questions.map((question,index)=><View key={index} style={styles.question}>
          <Text style={styles.index}>{index+1}.</Text>
          <Text selectable style={[styles.copy,styles.questionText]}>{question}</Text>
        </View>)}
      </View>
      <View style={styles.practice}>
        <Text accessibilityRole="header" style={styles.subtitle}>Попробуйте на практике</Text>
        <Text selectable style={styles.copy}>{entry.practice}</Text>
      </View>
      <View style={styles.sources}>
        <Text accessibilityRole="header" style={styles.sourceTitle}>Материалы проекта</Text>
        {entry.sources.map(source=><Text key={source.id} selectable style={styles.caption}>{source.title} · {source.locator}</Text>)}
      </View>
    </View>}
  </View>;
}

const styles=StyleSheet.create({
  section:{gap:12,borderTopWidth:1,borderTopColor:'#DDE9E1',paddingTop:20},
  title:{fontSize:20,lineHeight:27,fontWeight:'600',color:'#003447'},
  subtitle:{fontSize:16,lineHeight:24,fontWeight:'600',color:'#003447'},
  copy:{fontSize:15,lineHeight:25,color:'#25444B'},
  caption:{fontSize:12,lineHeight:20,color:'#536D63'},
  toggle:{minHeight:48,paddingHorizontal:14,paddingVertical:12,flexDirection:'row',alignItems:'center',justifyContent:'space-between',gap:10,borderRadius:12,backgroundColor:'#E8F4EE'},
  toggleText:{fontSize:14,lineHeight:21,fontWeight:'600',color:'#003447',flexShrink:1},
  toggleIcon:{fontSize:22,lineHeight:24,color:'#28705E'},pressed:{opacity:.75},
  details:{gap:15},questions:{gap:10},question:{flexDirection:'row',gap:9,alignItems:'flex-start'},
  index:{fontSize:14,lineHeight:25,color:'#28705E'},questionText:{flex:1,minWidth:0},
  practice:{padding:14,gap:8,borderRadius:12,backgroundColor:'#F1F7F4'},
  sources:{gap:6,paddingTop:12,borderTopWidth:1,borderTopColor:'#E4EEE8'},
  sourceTitle:{fontSize:12,lineHeight:20,fontWeight:'600',color:'#365B52'},
});
