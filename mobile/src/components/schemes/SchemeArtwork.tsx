import {useEffect,useRef,useState} from 'react';
import {AccessibilityInfo,Animated,AppState,Image,ImageSourcePropType,Modal,ScrollView,StyleSheet,Text,useWindowDimensions,View} from 'react-native';
import {Asset} from 'expo-asset';
import {SafeAreaView} from 'react-native-safe-area-context';
import {Button,s} from '../ui';
import {colors} from '../../lib/theme';

export function SchemeArtwork({source,title,id}:{source:ImageSourcePropType;title:string;id:string}){
 const [zoom,setZoom]=useState(0),[reducedMotion,setReducedMotion]=useState(true);
 const [artworkWidth,setArtworkWidth]=useState(280);
 const progress=useRef(new Animated.Value(1)).current;
 const {width,height}=useWindowDimensions();
 const asset=Asset.fromModule(source as number),ratio=(asset.width||1)/(asset.height||1);
 useEffect(()=>{
  let mounted=true,changed=false;
  const subscription=AccessibilityInfo.addEventListener('reduceMotionChanged',value=>{changed=true;if(mounted)setReducedMotion(value);});
  void AccessibilityInfo.isReduceMotionEnabled().then(value=>{if(mounted&&!changed)setReducedMotion(value);}).catch(()=>{});
  return()=>{mounted=false;subscription.remove();};
 },[]);
 useEffect(()=>{
  progress.stopAnimation();progress.setValue(1);
  if(reducedMotion)return;
  progress.setValue(0);
  const reveal=Animated.timing(progress,{toValue:1,duration:650,useNativeDriver:true,isInteraction:false});reveal.start();
  const subscription=AppState.addEventListener('change',state=>{if(state!=='active'){reveal.stop();progress.setValue(1);}});
  return()=>{reveal.stop();subscription.remove();progress.setValue(1);};
 },[id,reducedMotion,progress]);
 const imageWidth=Math.max(1,width-32)*zoom;
 return <View style={{gap:12}}>
  <Animated.View onLayout={event=>setArtworkWidth(event.nativeEvent.layout.width)} style={{opacity:progress.interpolate({inputRange:[0,1],outputRange:[.75,1]}),transform:[{scale:progress.interpolate({inputRange:[0,1],outputRange:[.985,1]})}]}}>
   <Image source={source} accessibilityLabel={title} resizeMode="contain" style={{width:'100%',height:artworkWidth/ratio}}/>
  </Animated.View>
  <Button title="Рассмотреть рисунок" secondary onPress={()=>setZoom(2)}/>
  <Modal visible={zoom>0} animationType="none" onRequestClose={()=>setZoom(0)}>
   <SafeAreaView style={{flex:1,backgroundColor:colors.surface,gap:12,padding:16}}>
    <Text accessibilityRole="header" style={s.title}>{title}</Text>
    <Text style={s.small}>Перемещайте рисунок по горизонтали и вертикали, чтобы рассмотреть детали.</Text>
    <View style={{flex:1,minHeight:150,borderWidth:1,borderColor:colors.line,borderRadius:12,overflow:'hidden'}}>
     <ScrollView horizontal nestedScrollEnabled contentContainerStyle={{minHeight:'100%'}}>
      <ScrollView nestedScrollEnabled style={{width:imageWidth,maxHeight:height}} contentContainerStyle={{flexGrow:1,justifyContent:'center'}}>
       <Image source={source} resizeMode="contain" accessibilityLabel={title} style={{width:imageWidth,height:imageWidth/ratio}}/>
      </ScrollView>
     </ScrollView>
    </View>
    <View style={styles.zoomActions}><View style={{flex:1}}><Button secondary title="Уменьшить" disabled={zoom<=1} onPress={()=>setZoom(value=>Math.max(1,value-.5))}/></View><Text accessibilityLiveRegion="polite" style={s.label}>{Math.round(zoom*100)}%</Text><View style={{flex:1}}><Button secondary title="Увеличить" disabled={zoom>=3} onPress={()=>setZoom(value=>Math.min(3,value+.5))}/></View></View>
    <Button title="Вернуться к разбору" onPress={()=>setZoom(0)}/>
   </SafeAreaView>
  </Modal>
 </View>;
}
const styles=StyleSheet.create({zoomActions:{flexDirection:'row',alignItems:'center',gap:8}});
