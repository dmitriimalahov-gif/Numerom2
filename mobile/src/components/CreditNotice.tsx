import {ReactNode,useEffect,useRef,useSyncExternalStore} from 'react';
import {AccessibilityInfo,findNodeHandle,Modal,Platform,Pressable,ScrollView,StyleSheet,Text,View} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {router,usePathname} from 'expo-router';
import {Ionicons} from '@expo/vector-icons';
import {useSession} from '../lib/session';
import {creditNoticeText} from '../lib/creditNotice';
import {Button,s} from './ui';
import {colors as c} from '../lib/theme';

export function CreditNotice({children}:{children:ReactNode}){
 const {creditNotice,status}=useSession(),pathname=usePathname();
 const notice=useSyncExternalStore(creditNotice.subscribe,creditNotice.getSnapshot,creditNotice.getSnapshot);
 const closeButton=useRef<View|null>(null),previousFocus=useRef<HTMLElement|null>(null);
 const paymentPage=pathname==='/top-up'||pathname==='/payment-result';
 const visible=status==='signedIn'&&!!notice&&!paymentPage;
 useEffect(()=>{creditNotice.dismiss();},[pathname,creditNotice]);
 useEffect(()=>{
  if(!visible||Platform.OS!=='web')return;
  previousFocus.current=document.activeElement instanceof HTMLElement?document.activeElement:null;
  return()=>{if(previousFocus.current?.isConnected)previousFocus.current.focus();};
 },[visible]);
 function focusClose(){
  if(Platform.OS==='web')(closeButton.current as unknown as {focus?:()=>void})?.focus?.();
  else {const node=findNodeHandle(closeButton.current);if(node)AccessibilityInfo.setAccessibilityFocus(node);}
 }
 const copy=creditNoticeText(notice||{});
 return <View style={styles.shell}>
  <View style={styles.shell} aria-hidden={visible} accessibilityElementsHidden={visible} importantForAccessibility={visible?'no-hide-descendants':'auto'}>{children}</View>
  <Modal transparent visible={visible} animationType="none" onRequestClose={creditNotice.dismiss} onShow={focusClose} statusBarTranslucent>
   <SafeAreaView style={styles.overlay}>
    <Pressable accessible={false} focusable={false} tabIndex={-1} onFocus={focusClose} onPress={creditNotice.dismiss} style={StyleSheet.absoluteFill}/>
    <View accessibilityViewIsModal accessibilityLabel={copy.title} style={styles.sheet}>
     <Pressable ref={closeButton} accessibilityRole="button" accessibilityLabel="Закрыть окно пополнения" onPress={creditNotice.dismiss} style={styles.close}><Ionicons name="close-outline" size={25} color={c.muted}/></Pressable>
     <ScrollView contentContainerStyle={styles.content}>
      <View style={styles.icon}><Ionicons accessible={false} name="wallet-outline" size={32} color={c.navy}/></View>
      <Text accessibilityRole="header" style={styles.title}>{copy.title}</Text>
      <Text style={styles.description}>{copy.description}</Text>
      <Button title="Пополнить" onPress={()=>{creditNotice.dismiss();router.push('/top-up');}}/>
      <Button secondary title="Позже" onPress={creditNotice.dismiss}/>
      <Text style={[s.small,styles.footnote]}>Ваши сохранённые расчёты доступны без пополнения.</Text>
     </ScrollView>
    </View>
   </SafeAreaView>
  </Modal>
 </View>;
}
const styles=StyleSheet.create({
 shell:{flex:1},
 overlay:{flex:1,alignItems:'center',justifyContent:'center',padding:16,backgroundColor:'rgba(16,36,58,.42)'},
 sheet:{width:'100%',maxWidth:420,maxHeight:'95%',borderRadius:26,backgroundColor:c.surface,overflow:'hidden'},
 close:{alignSelf:'flex-end',width:48,height:48,alignItems:'center',justifyContent:'center'},
 content:{paddingHorizontal:24,paddingBottom:26,gap:16},
 icon:{alignSelf:'center',width:72,height:72,borderRadius:24,backgroundColor:c.blue,alignItems:'center',justifyContent:'center',marginBottom:4},
 title:{fontSize:26,lineHeight:33,fontWeight:'700',letterSpacing:-.5,color:c.navy,textAlign:'center'},
 description:{fontSize:15,lineHeight:23,color:c.muted,textAlign:'center',marginBottom:6},
 footnote:{textAlign:'center'},
});
