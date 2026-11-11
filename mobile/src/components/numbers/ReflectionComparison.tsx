import {useState} from 'react';
import {Pressable, StyleSheet, Text, View} from 'react-native';
import {comparisonReflection,numberReflection} from '../../lib/reflectionKnowledge';

const digits=[1,2,3,4,5,6,7,8,9];

export function ReflectionComparison({digit}:{digit:number}) {
  const [expanded,setExpanded]=useState(false);
  const [second,setSecond]=useState(digit===1?2:1);
  const first=numberReflection(digit);
  if(!first)return null;
  const comparison=comparisonReflection(digit,second);

  return <View style={styles.section}>
    <Pressable accessibilityRole="button" accessibilityState={{expanded}}
      accessibilityLabel={expanded?'Свернуть сопоставление двух тем':'Сопоставить две темы'}
      onPress={()=>setExpanded(value=>!value)}
      style={({pressed})=>[styles.toggle,pressed&&styles.pressed]}>
      <View style={styles.toggleCopy}>
        <Text style={styles.title}>Сопоставить две темы</Text>
        <Text style={styles.caption}>Символы чисел и вопросы для размышления</Text>
      </View>
      <Text accessible={false} style={styles.toggleIcon}>{expanded?'−':'+'}</Text>
    </Pressable>
    {expanded&&<View style={styles.details}>
      <Text style={styles.copy}>Первая тема: {digit} · {first.planet}. Выберите вторую тему.</Text>
      <View accessibilityRole="tablist" accessibilityLabel="Вторая тема для сопоставления" style={styles.tabs}>
        {digits.map(number=>{
          const entry=numberReflection(number);
          const selected=number===second;
          return <Pressable key={number} accessibilityRole="tab"
            accessibilityLabel={`Число ${number}: ${entry?.planet}`}
            accessibilityState={{selected}} onPress={()=>setSecond(number)}
            style={({pressed})=>[styles.tab,selected&&styles.active,pressed&&styles.pressed]}>
            <Text style={[styles.digit,selected&&styles.activeText]}>{number}</Text>
            <Text style={[styles.planet,selected&&styles.activeText]}>{entry?.planet}</Text>
          </Pressable>;
        })}
      </View>
      {comparison&&<View style={styles.result}>
        <Text accessibilityRole="header" style={styles.resultTitle}>{comparison.title}</Text>
        <Text selectable style={styles.copy}>{comparison.intro}</Text>
        <View style={styles.themes}>
          {comparison.themes.map(theme=><View key={theme.digit} style={styles.theme}>
            <Text style={styles.themeLabel}>{theme.digit} · {theme.planet}</Text>
            <Text selectable style={styles.copy}>{theme.theme}</Text>
          </View>)}
        </View>
        <Text accessibilityRole="header" style={styles.subtitle}>Вопросы для сопоставления</Text>
        {comparison.questions.map((question,index)=><View key={index} style={styles.question}>
          <Text style={styles.index}>{index+1}.</Text>
          <Text selectable style={[styles.copy,styles.questionText]}>{question}</Text>
        </View>)}
        <View style={styles.practice}>
          <Text accessibilityRole="header" style={styles.subtitle}>Попробуйте на практике</Text>
          <Text selectable style={styles.copy}>{comparison.practice}</Text>
        </View>
        <Text selectable style={styles.caption}>{comparison.sourceNote}</Text>
      </View>}
    </View>}
  </View>;
}

const styles=StyleSheet.create({
  section:{borderRadius:16,borderWidth:1,borderColor:'#DDE9E1',backgroundColor:'#FFFFFF',overflow:'hidden'},
  toggle:{minHeight:60,padding:16,flexDirection:'row',alignItems:'center',justifyContent:'space-between',gap:12},
  toggleCopy:{flex:1,minWidth:0,gap:4},title:{fontSize:17,lineHeight:24,fontWeight:'600',color:'#003447'},
  caption:{fontSize:12,lineHeight:20,color:'#536D63'},toggleIcon:{fontSize:24,lineHeight:28,color:'#28705E'},
  details:{paddingHorizontal:16,paddingBottom:18,gap:16},copy:{fontSize:15,lineHeight:25,color:'#25444B'},
  tabs:{flexDirection:'row',flexWrap:'wrap',gap:8},
  tab:{flexBasis:'29%',flexGrow:1,minHeight:58,padding:8,gap:3,alignItems:'center',justifyContent:'center',borderRadius:11,borderWidth:1,borderColor:'#D2E4DA',backgroundColor:'#E8F4EE'},
  digit:{fontSize:21,lineHeight:25,fontWeight:'600',color:'#003447'},planet:{fontSize:11,lineHeight:16,color:'#365B52',textAlign:'center'},
  active:{backgroundColor:'#003447',borderColor:'#003447'},activeText:{color:'#FFFFFF'},pressed:{opacity:.75},
  result:{gap:13},resultTitle:{fontSize:20,lineHeight:27,fontWeight:'600',color:'#003447'},
  subtitle:{fontSize:16,lineHeight:24,fontWeight:'600',color:'#003447'},
  themes:{gap:10},theme:{gap:6,padding:13,borderRadius:12,backgroundColor:'#F1F7F4'},
  themeLabel:{fontSize:13,lineHeight:20,fontWeight:'600',color:'#28705E'},
  question:{flexDirection:'row',gap:9,alignItems:'flex-start'},index:{fontSize:14,lineHeight:25,color:'#28705E'},questionText:{flex:1,minWidth:0},
  practice:{gap:8,paddingTop:13,borderTopWidth:1,borderTopColor:'#E4EEE8'},
});
