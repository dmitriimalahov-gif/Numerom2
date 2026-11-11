import {Modal, Pressable, ScrollView, StyleSheet, Text, View} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {Button} from '../ui';
import {NumberStory} from './NumberStory';
import {NarrationClip} from '../audio/Narration';
export interface SchemeInterpretation {
  title:string; value:number|null; meaning:string; interpretation?:string;
  method?:string; steps?:string[]; note?:string; profileAction?:boolean; knowledgeDigit?:number;
  valueCaption?:string; calculationSummary?:string;
  narrationId?:string;
  knowledgeMaster?:number;
}

export function InterpretationSheet({detail,onClose,onProfile}: {
  detail:SchemeInterpretation|null; onClose:()=>void; onProfile:()=>void;
}) {
  return <Modal visible={!!detail} transparent animationType="fade" onRequestClose={onClose}>
    <SafeAreaView style={styles.overlay}>
      <Pressable style={StyleSheet.absoluteFill} accessibilityRole="button" accessibilityLabel="Закрыть расшифровку" onPress={onClose}/>
      {detail && <View style={styles.sheet} accessibilityViewIsModal>
        <View style={styles.top}><Text style={styles.eyebrow}>Расшифровка NumerOM</Text><Pressable accessibilityRole="button" accessibilityLabel="Закрыть окно" onPress={onClose} style={styles.close}><Text style={styles.closeText}>×</Text></Pressable></View>
        <ScrollView contentContainerStyle={styles.body} keyboardShouldPersistTaps="handled">
          <View style={styles.heading}><Text style={styles.value}>{detail.value ?? '—'}</Text><Text accessibilityRole="header" style={styles.title}>{detail.title}</Text></View>
          {!!detail.valueCaption && <Text style={styles.caption}>{detail.valueCaption}</Text>}
          {!!detail.calculationSummary && <Text style={styles.copy}>{detail.calculationSummary}</Text>}
          {detail.value === null && <Text style={styles.copy}>Значение недоступно</Text>}
          {!!detail.narrationId && <NarrationClip key={detail.narrationId} id={detail.narrationId} showText fallbackText={detail.meaning}/>}
          {(!!detail.method || !!detail.steps?.length) && <View style={styles.method}>
            <Text accessibilityRole="header" style={styles.methodTitle}>Как рассчитано</Text>
            {!!detail.method && <Text selectable style={styles.copy}>{detail.method}</Text>}
            {detail.steps?.map((step,index) => <View key={index} style={styles.step}><Text style={styles.index}>{index+1}</Text><Text selectable style={[styles.copy,{flex:1}]}>{step}</Text></View>)}
          </View>}
          {detail.knowledgeDigit !== undefined ? <NumberStory key={detail.knowledgeDigit} digit={detail.knowledgeDigit}/> : (!detail.narrationId || !!detail.interpretation) &&
            <Text selectable style={styles.meaning}>{detail.interpretation || detail.meaning}</Text>}
          {detail.knowledgeMaster !== undefined && <NarrationClip key={`master-${detail.knowledgeMaster}`} id={`master-${detail.knowledgeMaster}`}/>}
          {!!detail.note && <View style={styles.note}><Text selectable style={styles.caption}>{detail.note}</Text></View>}
          {detail.profileAction && <Button title="Проверить имя в профиле" secondary onPress={() => {onClose();onProfile();}}/>}
        </ScrollView>
      </View>}
    </SafeAreaView>
  </Modal>;
}
const styles=StyleSheet.create({
  overlay:{flex:1,justifyContent:'flex-end',alignItems:'center',backgroundColor:'rgba(0,31,43,.42)',paddingHorizontal:14,paddingTop:36,paddingBottom:14},
  sheet:{width:'100%',maxWidth:560,maxHeight:'92%',backgroundColor:'#FFFFFF',borderRadius:25,overflow:'hidden'},
  top:{flexDirection:'row',alignItems:'center',justifyContent:'space-between',paddingLeft:22,paddingRight:10,borderBottomWidth:1,borderBottomColor:'#E4EEE8'},
  eyebrow:{fontSize:12,lineHeight:19,color:'#536D63'},close:{minWidth:48,minHeight:50,alignItems:'center',justifyContent:'center'},closeText:{fontSize:30,lineHeight:36,color:'#003447'},
  body:{padding:22,gap:18,paddingBottom:30},heading:{flexDirection:'row',alignItems:'center',gap:15},value:{fontSize:48,lineHeight:56,color:'#003447',fontWeight:'500'},title:{flex:1,fontSize:23,lineHeight:29,fontWeight:'600',color:'#003447'},
  meaning:{fontSize:16,lineHeight:25,fontWeight:'600',color:'#003447'},copy:{fontSize:15,lineHeight:24,color:'#20364E'},caption:{fontSize:12,lineHeight:20,color:'#536D63'},note:{padding:14,borderRadius:13,backgroundColor:'#E8F4EE'},
  method:{gap:12,borderTopWidth:1,borderTopColor:'#E4EEE8',paddingTop:18},methodTitle:{fontSize:17,lineHeight:24,fontWeight:'600',color:'#003447'},step:{flexDirection:'row',gap:12},index:{fontSize:12,lineHeight:24,color:'#28705E',minWidth:14},
});
