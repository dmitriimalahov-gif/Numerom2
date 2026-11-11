import {ReactNode,useEffect,useRef,useState} from 'react';
import {AccessibilityInfo,AppState,findNodeHandle,Modal,Platform,Pressable,ScrollView,StyleSheet,Text,useWindowDimensions,View} from 'react-native';
import {SafeAreaView,useSafeAreaInsets} from 'react-native-safe-area-context';
import {Href,router,usePathname} from 'expo-router';
import {Ionicons} from '@expo/vector-icons';
import {Brand} from './Brand';
import {NavigationChromeContext} from './NavigationChromeContext';
import {useSession} from '../lib/session';
import {activeSection,navigationSections,screenNavigation} from '../lib/mobileNavigation';
import {colors as c} from '../lib/theme';
import {telegramApp} from '../lib/telegram';

export function AppNavigation({children}:{children:ReactNode}){
 const {user,status}=useSession(),pathname=usePathname(),insets=useSafeAreaInsets(),{width}=useWindowDimensions();
 const signedIn=status==='signedIn',isAdmin=signedIn&&!!(user?.is_admin||user?.is_super_admin);
 const identity=`${status}:${user?.id||''}:${isAdmin}`,page=screenNavigation(pathname,signedIn);
 const [opened,setOpened]=useState<{identity:string;pathname:string}|null>(null);
 const visible=opened?.identity===identity&&opened.pathname===pathname;
 const [reduced,setReduced]=useState(true);
 const trigger=useRef<View|null>(null),closeButton=useRef<View|null>(null);
 const sections=navigationSections({signedIn,isAdmin}),active=activeSection(pathname,signedIn);
 const close=()=>setOpened(null);
 useEffect(()=>{setOpened(null);},[pathname,identity]);
 useEffect(()=>{const back=telegramApp()?.BackButton;if(!back)return;const handler=()=>router.canGoBack()?router.back():router.replace('/home');if(page.parent)back.show();else back.hide();back.onClick(handler);return()=>back.offClick(handler);},[pathname,page.parent]);
 useEffect(()=>{
  const subscription=AppState.addEventListener('change',next=>{if(next==='background')setOpened(null);});
  const hidden=()=>{if(document.hidden)setOpened(null);};
  if(Platform.OS==='web')document.addEventListener('visibilitychange',hidden);
  return()=>{subscription.remove();if(Platform.OS==='web')document.removeEventListener('visibilitychange',hidden);};
 },[]);
 useEffect(()=>{
  let alive=true,changed=false;
  const subscription=AccessibilityInfo.addEventListener('reduceMotionChanged',value=>{changed=true;setReduced(value);});
  AccessibilityInfo.isReduceMotionEnabled().then(value=>{if(alive&&!changed)setReduced(value);}).catch(()=>{});
  return()=>{alive=false;subscription.remove();};
 },[]);
 function focus(view:View|null){
  if(Platform.OS==='web')(view as unknown as {focus?:()=>void})?.focus?.();
  else{const node=findNodeHandle(view);if(node)AccessibilityInfo.setAccessibilityFocus(node);}
 }
 function navigate(path:string){close();if(pathname!==path)router.navigate(path as Href);}
 return <NavigationChromeContext.Provider value={true}><View style={styles.shell}>
  <SafeAreaView edges={['top','left','right']} style={styles.top} aria-hidden={visible} accessibilityElementsHidden={visible} importantForAccessibility={visible?'no-hide-descendants':'auto'}>
   <View style={styles.header}>
    <Pressable ref={trigger} accessibilityRole="button" accessibilityLabel="Открыть меню разделов" accessibilityHint="Все разделы NumerOM" accessibilityState={{expanded:visible}} aria-expanded={visible} onPress={()=>setOpened({identity,pathname})} style={({pressed})=>[styles.iconButton,pressed&&styles.pressed]}><Ionicons name="menu-outline" size={27} color={c.navy}/></Pressable>
    <View style={styles.headerTitle}><Text style={styles.wordmark}>NumerOM</Text><Text numberOfLines={1} style={styles.pageTitle}>{page.title}</Text></View>
    {signedIn&&<Pressable accessibilityRole="button" accessibilityLabel={`Баланс: ${user?.credits_remaining??0} баллов. История баллов`} onPress={()=>router.push('/credits')} style={{paddingVertical:10,paddingHorizontal:8,borderRadius:12,backgroundColor:c.blue}}><Text style={styles.balance}>{user?.credits_remaining??0} баллов</Text></Pressable>}
    {page.parent?<Pressable accessibilityRole="button" accessibilityLabel="Назад" onPress={()=>router.canGoBack()?router.back():router.replace(page.parent as Href)} style={({pressed})=>[styles.iconButton,pressed&&styles.pressed]}><Ionicons name="arrow-back-outline" size={22} color={c.navy}/></Pressable>:<View style={styles.headerSpace}/>}
   </View>
  </SafeAreaView>
  <View style={styles.content} aria-hidden={visible} accessibilityElementsHidden={visible} importantForAccessibility={visible?'no-hide-descendants':'auto'}>{children}</View>
  <Modal transparent visible={visible} animationType={reduced?'none':'fade'} statusBarTranslucent onRequestClose={close} onShow={()=>focus(closeButton.current)} onDismiss={()=>focus(trigger.current)}>
   <View style={styles.overlay}>
    <Pressable accessible={false} focusable={false} tabIndex={-1} onFocus={()=>focus(closeButton.current)} onPress={close} style={StyleSheet.absoluteFill}/>
    <View accessibilityViewIsModal accessibilityLabel="Разделы NumerOM" style={[styles.drawer,{width:Math.min(360,width-24),paddingTop:insets.top,paddingBottom:insets.bottom}]}>
     <View style={styles.drawerHeader}><Brand compact/><Pressable ref={closeButton} accessibilityRole="button" accessibilityLabel="Закрыть меню" onPress={close} style={({pressed})=>[styles.iconButton,pressed&&styles.pressed]}><Ionicons name="close-outline" size={27} color={c.navy}/></Pressable></View>
     <ScrollView contentContainerStyle={styles.menuContent} showsVerticalScrollIndicator>
      <View style={styles.intro}><Text accessibilityRole="header" style={styles.menuTitle}>Разделы</Text><Text style={styles.person}>{signedIn?(user?.full_name||user?.name||'Мой NumerOM'):'Начните знакомство с числами'}</Text>{signedIn&&<Text style={styles.balance}>Баланс: {user?.credits_remaining??'—'} баллов</Text>}</View>
      {sections.map(section=><View key={section.title} style={styles.group}><Text style={styles.groupTitle}>{section.title}</Text>{section.items.map(item=>{
       const selected=item.path===active;
       return <Pressable key={item.id} accessibilityRole="button" accessibilityLabel={item.label} accessibilityState={{selected}} aria-current={selected?'page':undefined} onPress={()=>navigate(item.path)} style={({pressed})=>[styles.item,selected&&styles.selected,pressed&&styles.pressed]}>
        <Ionicons accessible={false} name={item.icon as keyof typeof Ionicons.glyphMap} size={22} color={selected?c.navy:c.muted}/><Text style={[styles.itemLabel,selected&&styles.selectedLabel]}>{item.label}</Text>{selected&&<View style={styles.dot}/>}
       </Pressable>;
      })}</View>)}
     </ScrollView>
    </View>
   </View>
  </Modal>
 </View></NavigationChromeContext.Provider>;
}
const styles=StyleSheet.create({
 shell:{flex:1,backgroundColor:c.background},top:{backgroundColor:c.surface,borderBottomWidth:1,borderBottomColor:c.line},header:{minHeight:64,flexDirection:'row',alignItems:'center',gap:12,paddingHorizontal:14,paddingVertical:6},iconButton:{width:44,height:44,alignItems:'center',justifyContent:'center',borderRadius:13},headerTitle:{flex:1,gap:1},wordmark:{fontSize:21,fontWeight:'700',color:c.navy,letterSpacing:-.5},pageTitle:{fontSize:12,color:c.muted},headerSpace:{width:44},content:{flex:1},
 overlay:{flex:1,backgroundColor:'rgba(16,36,58,.38)'},drawer:{flex:1,backgroundColor:c.surface,alignSelf:'flex-start',borderTopRightRadius:24,borderBottomRightRadius:24,overflow:'hidden'},drawerHeader:{flexDirection:'row',alignItems:'center',justifyContent:'space-between',paddingHorizontal:22,paddingVertical:16,borderBottomWidth:1,borderBottomColor:c.line},menuContent:{paddingHorizontal:14,paddingBottom:28,gap:22},intro:{paddingHorizontal:12,paddingTop:20,gap:6},menuTitle:{fontSize:27,fontWeight:'700',color:c.navy,letterSpacing:-.6},person:{fontSize:14,lineHeight:21,color:c.muted},balance:{fontSize:13,color:c.accent,fontWeight:'600'},group:{gap:4},groupTitle:{paddingHorizontal:12,paddingBottom:5,fontSize:12,fontWeight:'600',color:c.muted},item:{flexDirection:'row',alignItems:'center',gap:12,minHeight:50,paddingHorizontal:12,paddingVertical:12,borderRadius:13},selected:{backgroundColor:c.blue},itemLabel:{flex:1,color:c.ink,fontSize:15,lineHeight:21},selectedLabel:{color:c.navy,fontWeight:'600'},dot:{width:6,height:6,borderRadius:3,backgroundColor:c.accent},pressed:{backgroundColor:c.blue},
});
