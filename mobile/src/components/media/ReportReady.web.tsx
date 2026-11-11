import {useState,useSyncExternalStore} from 'react';
import {Pressable,StyleSheet,Text,View} from 'react-native';
import {Ionicons} from '@expo/vector-icons';
import {useSafeAreaInsets} from 'react-native-safe-area-context';
import {useMiniPlayer} from './MediaDock.web';
import {readyReport} from '../../lib/readyReport';
import {openReport} from '../../lib/reportPrint.web';
import {colors as c} from '../../lib/theme';

// A prepared report PDF waits here for one tap: the tap itself is what lets a phone open it in a new tab.
export function ReportReady(){
 const file=useSyncExternalStore(readyReport.subscribe,readyReport.get,readyReport.get);
 const [expired,setExpired]=useState('');
 // The mini player below keeps the home-indicator gap when it shows; otherwise this bar does.
 const player=useMiniPlayer(),insets=useSafeAreaInsets(),bar=[styles.bar,{paddingBottom:10+(player?0:insets.bottom)}];
 if(!file)return expired?<View accessibilityRole="alert" style={bar}><Text style={[styles.name,{flex:1}]}>{expired}</Text>
  <Pressable accessibilityRole="button" accessibilityLabel="Закрыть сообщение" onPress={()=>setExpired('')} style={styles.close}><Ionicons name="close" size={22} color={c.navy}/></Pressable></View>:null;
 const open=()=>{
  readyReport.set(null);
  if(Date.now()>file.until){setExpired('Ссылка на PDF устарела. Нажмите кнопку сохранения отчёта ещё раз.');return;}
  setExpired('');openReport(file.url);
 };
 return <View accessibilityRole="alert" style={bar}>
  <Ionicons accessible={false} name="document-text-outline" size={26} color={c.navy}/>
  <View style={{flex:1}}><Text style={styles.ready}>PDF готов</Text><Text numberOfLines={2} style={styles.name}>{file.filename}</Text></View>
  <Pressable accessibilityRole="button" accessibilityLabel={`Открыть PDF: ${file.filename}`} onPress={open} style={({pressed})=>[styles.open,pressed&&{opacity:.8}]}><Text style={styles.openText}>Открыть PDF</Text></Pressable>
  <Pressable accessibilityRole="button" accessibilityLabel="Закрыть" onPress={()=>readyReport.set(null)} style={styles.close}><Ionicons name="close" size={22} color={c.navy}/></Pressable>
 </View>;
}
const styles=StyleSheet.create({
 bar:{flexDirection:'row',alignItems:'center',gap:10,paddingHorizontal:14,paddingVertical:10,backgroundColor:c.blue,borderTopWidth:1,borderTopColor:c.line},
 ready:{fontSize:14,fontWeight:'700',color:c.navy},name:{fontSize:12,lineHeight:17,color:c.ink},
 open:{minHeight:44,paddingHorizontal:14,borderRadius:12,justifyContent:'center',backgroundColor:'#003447'},openText:{color:'#fff',fontSize:14,fontWeight:'600'},
 close:{width:40,height:44,alignItems:'center',justifyContent:'center'},
});
