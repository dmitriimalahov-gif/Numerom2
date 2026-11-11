import {useEffect,useState} from 'react';
import {AccessibilityInfo,Platform,Text,View} from 'react-native';
import Svg,{Line,Rect,Text as SvgText} from 'react-native-svg';
import {loadingFrame} from '../../../../packages/full-report/loading-motion';
import {s} from '../ui';

// «Отчёт готовится»: the birth date's digits fly into the Pythagorean square, then its lines are traced.
// SVG text on the web otherwise falls back to a serif face; native uses the system font.
const FONT=Platform.OS==='web'?'-apple-system, "Helvetica Neue", Helvetica, Arial, sans-serif':undefined;
export function ReportPreparing({birthDate,message}:{birthDate?:string|null;message?:string}){
 const [seconds,setSeconds]=useState(0),[reduced,setReduced]=useState(false);
 useEffect(()=>{
  let live=true;
  AccessibilityInfo.isReduceMotionEnabled().then(value=>{if(live)setReduced(value);}).catch(()=>{});
  const subscription=AccessibilityInfo.addEventListener('reduceMotionChanged',setReduced);
  return()=>{live=false;subscription?.remove();};
 },[]);
 useEffect(()=>{
  if(reduced)return;
  // About 30 redraws a second are enough for this motion and keep the phone cool.
  let frame=0,last=0;const start=Date.now();
  const tick=(now:number)=>{if(now-last>=33){last=now;setSeconds((Date.now()-start)/1000);}frame=requestAnimationFrame(tick);};
  frame=requestAnimationFrame(tick);
  return()=>cancelAnimationFrame(frame);
 },[reduced]);
 const view=loadingFrame(seconds,birthDate,reduced);
 return <View accessible accessibilityRole="progressbar" accessibilityLabel={`Отчёт готовится. ${view.caption}`} style={{alignItems:'center',gap:10}}>
  <View style={{width:'100%',maxWidth:380,aspectRatio:view.width/view.height}}>
   <Svg width="100%" height="100%" viewBox={`0 0 ${view.width} ${view.height}`}>
    {view.shapes.map((shape,i)=>shape.kind==='rect'
     ?<Rect key={i} x={shape.x} y={shape.y} width={shape.w} height={shape.h} rx={shape.r} fill={shape.fill} stroke={shape.stroke} strokeWidth={1.2} opacity={shape.opacity}/>
     :shape.kind==='line'
     ?<Line key={i} x1={shape.x1} y1={shape.y1} x2={shape.x2} y2={shape.y2} stroke={shape.color} strokeWidth={shape.width} strokeLinecap="round" opacity={shape.opacity}/>
     :<SvgText key={i} x={shape.x} y={shape.y} fontFamily={FONT} fontSize={shape.size} fontWeight={String(shape.weight) as '400'|'700'} fill={shape.color} textAnchor={shape.anchor??'middle'} opacity={shape.opacity}>{shape.text}</SvgText>)}
   </Svg>
  </View>
  <Text accessibilityLiveRegion="polite" style={s.title}>{view.caption}…</Text>
  {!!message&&<Text style={[s.small,{textAlign:'center'}]}>{message}</Text>}
 </View>;
}
