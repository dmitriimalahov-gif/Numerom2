import {useRef,useState,type ReactNode} from 'react';
import {Image,Modal,Pressable,ScrollView,StyleSheet,Text,View} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {Button,Card,Field,Heading,Screen,s} from '../components/ui';
import {colors} from '../lib/theme';
import {illustrations} from '../lib/illustrations';
import {NumberKnowledge} from '../components/numbers/NumberKnowledge';
import {NarrationProvider,NarrationClip,GUEST_GUIDE_PATH} from '../components/audio/Narration';
import {SchemeDetail} from '../components/schemes/SchemeDetail';
import {schemeCatalog,filterSchemes,adjacentScheme} from '../lib/schemeKnowledge';
import {useSession} from '../lib/session';
import material from '../../../packages/scheme-knowledge/ru.json';
const catalog=schemeCatalog(material,illustrations.map(item=>item.id));
const schemes=illustrations.map(asset=>({...asset,...catalog.entries.find(entry=>entry.id===asset.id)!}));
const groups=['','Квадрат и даты','Сочетания','Примеры расчётов'];

export default function Gallery(){
 const {status,user}=useSession();
 const [group,setGroup]=useState(''),[query,setQuery]=useState(''),[selected,setSelected]=useState(''),[method,setMethod]=useState(false),[numbers,setNumbers]=useState(false);
 const detailScroll=useRef<ScrollView>(null);
 const visible=filterSchemes(schemes,group,query),entry=schemes.find(item=>item.id===selected);
 const previous=adjacentScheme(visible,selected,-1),next=adjacentScheme(visible,selected,1),index=visible.findIndex(item=>item.id===selected);
 const select=(id:string)=>{setSelected(id);detailScroll.current?.scrollTo({y:0,animated:false});};
 // Guests hear the same shared guide narration as the account, from the public catalog.
 const narration=(children:ReactNode)=>status==='signedIn'
  ?<NarrationProvider key={user?.id} path="/narration/project">{children}</NarrationProvider>
  :<NarrationProvider key="guest" guest path={GUEST_GUIDE_PATH}>{children}</NarrationProvider>;
 const detail=entry?<SchemeDetail key={entry.id} entry={entry} source={entry.source}/>:null;
 return <Screen>
  <Heading title="Авторские схемы" subtitle="Рассмотрите рисунок, разберите его числа и послушайте объяснение из материалов NumerOM."/>
  <View style={{gap:12}}><Button secondary title={method?'Скрыть вводный разбор':'Как устроены авторские схемы'} onPress={()=>setMethod(!method)}/>{method&&<Card><Text style={s.title}>{catalog.method.title}</Text><Text selectable style={s.body}>{catalog.method.text}</Text>{!!catalog.method.notes?.length&&<View style={{gap:10}}><Text style={s.label}>Особенности учебного примера</Text>{catalog.method.notes.map((note,index)=><Text key={index} selectable style={s.small}>{note}</Text>)}</View>}{status!=='loading'&&narration(<NarrationClip id={catalog.method.narration.id}/>)}</Card>}</View>
  <View style={{gap:14}}><Field label="Найти схему" value={query} onChangeText={setQuery} placeholder="Число души, Венера, диагональ…" autoCorrect={false}/>
   <View accessibilityRole="tablist" accessibilityLabel="Группы авторских схем" style={styles.filters}>{groups.map(item=><Pressable key={item} accessibilityRole="tab" accessibilityState={{selected:item===group}} onPress={()=>setGroup(item)} style={[styles.filter,item===group&&{backgroundColor:colors.navy}]}><Text style={{color:item===group?'#fff':colors.navy,fontWeight:'500'}}>{item||'Все схемы'}</Text></Pressable>)}</View>
   <Text accessibilityLiveRegion="polite" style={s.small}>{visible.length} из {schemes.length} схем</Text>
  </View>
  {visible.length===0&&<Card><Text style={s.title}>По этому запросу схем нет</Text><Text style={s.body}>Попробуйте название числа, планеты или линии квадрата.</Text><Button secondary title="Показать все схемы" onPress={()=>{setQuery('');setGroup('');}}/></Card>}
  {visible.map(item=><Pressable key={item.id} accessibilityRole="button" accessibilityLabel={`Разобрать схему: ${item.title}`} accessibilityHint="Открывает рисунок, текст и озвучку" onPress={()=>select(item.id)} style={({pressed})=>[styles.card,pressed&&{opacity:.85}]}>
   <Image source={item.source} resizeMode="contain" accessibilityLabel={item.title} style={{width:'100%',height:item.group==='Квадрат и даты'&&item.id!=='KVADRAT'?90:210}}/>
   <Text style={s.title}>{item.title}</Text><Text style={s.body}>{item.summary}</Text><Text style={s.link}>Открыть разбор и озвучку</Text>
  </Pressable>)}
  <View style={{gap:18}}><Button secondary title={numbers?'Скрыть истории девяти чисел':'Девять чисел и их планеты'} onPress={()=>setNumbers(!numbers)}/>{numbers&&<NumberKnowledge/>}</View>
  <Modal visible={!!entry} animationType="none" onRequestClose={()=>setSelected('')}>
   <SafeAreaView style={{flex:1,backgroundColor:colors.background}}>
    <View style={styles.modalHeader}><Text accessibilityRole="header" style={s.title}>{entry?.title}</Text><Text style={s.small}>{index>=0?`Схема ${index+1} из ${visible.length}`:'Авторская схема'}</Text></View>
    <ScrollView ref={detailScroll} contentContainerStyle={styles.modalScroll}><View style={{width:'100%',maxWidth:640,alignSelf:'center'}}>{status==='loading'?detail:narration(detail)}</View></ScrollView>
    <View style={styles.modalFooter}><View style={styles.navigation}><View style={{flex:1}}><Button title="Назад" secondary disabled={!previous} onPress={()=>previous&&select(previous.id)}/></View><View style={{flex:1}}><Button title="Далее" secondary disabled={!next} onPress={()=>next&&select(next.id)}/></View></View><Button title="Закрыть схему" onPress={()=>setSelected('')}/></View>
   </SafeAreaView>
  </Modal>
 </Screen>;
}
const styles=StyleSheet.create({filters:{flexDirection:'row',flexWrap:'wrap',gap:8},filter:{backgroundColor:colors.surface,paddingHorizontal:14,paddingVertical:13,borderRadius:24,minHeight:46},card:{padding:20,borderRadius:23,backgroundColor:colors.surface,borderWidth:1,borderColor:colors.line,gap:13},modalHeader:{paddingHorizontal:20,paddingTop:16,paddingBottom:12,gap:5,width:'100%',maxWidth:680,alignSelf:'center'},modalScroll:{padding:20,paddingBottom:30},modalFooter:{width:'100%',maxWidth:680,alignSelf:'center',gap:8,paddingHorizontal:20,paddingTop:10,paddingBottom:12,borderTopWidth:1,borderColor:colors.line,backgroundColor:colors.surface},navigation:{flexDirection:'row',gap:10}});
