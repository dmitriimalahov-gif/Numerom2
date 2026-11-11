import {useState} from 'react';
import {ImageSourcePropType,Pressable,StyleSheet,Text,View} from 'react-native';
import {Card,s} from '../ui';
import {NarrationClip} from '../audio/Narration';
import {SchemeEntry} from '../../lib/schemeKnowledge';
import {colors} from '../../lib/theme';
import {SchemeArtwork} from './SchemeArtwork';
import {NumberReflections} from '../numbers/NumberReflections';
const sections=[['meaning','Смысл'],['reading','Как читать'],['focus','Внимание']] as const;
export function SchemeDetail({entry,source}:{entry:SchemeEntry;source:ImageSourcePropType}){
 const [section,setSection]=useState<typeof sections[number][0]>('meaning');
 const reflectionDigit=(entry.kind==='cell'||entry.kind==='birth-days')&&typeof entry.digit==='number'&&Number.isInteger(entry.digit)&&entry.digit>=1&&entry.digit<=9?entry.digit:null;
 return <View style={{gap:20}}>
  <Text selectable style={s.body}>{entry.summary}</Text>
  <SchemeArtwork id={entry.id} source={source} title={entry.title}/>
  <Card tinted><Text style={s.title}>Послушать разбор</Text><NarrationClip id={entry.narration.id}/></Card>
  <View accessibilityRole="tablist" accessibilityLabel="Разделы объяснения схемы" style={styles.tabs}>{sections.map(([id,label])=><Pressable key={id} accessibilityRole="tab" accessibilityState={{selected:section===id}} onPress={()=>setSection(id)} style={[styles.tab,section===id&&styles.selected]}><Text style={[styles.tabText,section===id&&{color:'#fff'}]}>{label}</Text></Pressable>)}</View>
  <View style={{gap:17}}>
   {section==='meaning'&&<><Text accessibilityRole="header" style={s.title}>Что означает схема</Text><Text selectable style={s.body}>{entry.meaning}</Text></>}
   {section==='reading'&&<><Text accessibilityRole="header" style={s.title}>Разбор рисунка</Text>{entry.reading.map((step,index)=><View key={`${entry.id}-${index}`} style={styles.step}><Text selectable style={s.label}>{step.label}</Text><Text selectable style={s.body}>{step.text}</Text></View>)}</>}
   {section==='focus'&&<><Text accessibilityRole="header" style={s.title}>На что обратить внимание</Text><Text selectable style={s.body}>{entry.focus}</Text></>}
  </View>
  {reflectionDigit!==null&&<NumberReflections key={entry.id} digit={reflectionDigit}/>}
 </View>;
}
const styles=StyleSheet.create({tabs:{flexDirection:'row',flexWrap:'wrap',gap:7},tab:{flexGrow:1,minHeight:46,justifyContent:'center',alignItems:'center',backgroundColor:colors.blue,paddingHorizontal:11,paddingVertical:11,borderRadius:13},selected:{backgroundColor:colors.navy},tabText:{fontSize:13,fontWeight:'600',color:colors.navy},step:{gap:8,paddingLeft:14,borderLeftWidth:2,borderLeftColor:colors.line}});
