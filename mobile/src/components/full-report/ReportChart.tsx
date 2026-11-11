import {Text,View,StyleSheet} from 'react-native';
import Svg,{Line,Polyline,Text as SvgText} from 'react-native-svg';
import {chartValues,ReportChart as Chart} from '../../../../packages/full-report';
import {s} from '../ui';
import {colors as c} from '../../lib/theme';
export function ReportChart({chart}:{chart?:Chart}){
 const items=chartValues(chart);if(!items.length||!chart)return null;
 const max=Math.max(chart.type==='series'?9:1,...items.map(i=>i.value));
 if(chart.type==='matrix')return <View accessibilityLabel="Числовая схема" style={st.matrix}>{items.map((i,n)=><View key={n} style={st.cell}><Text style={s.small}>{i.label}</Text><Text style={st.value}>{i.value}</Text></View>)}</View>;
 if(chart.type==='series'){
  const x=(i:number)=>24+i*552/Math.max(1,items.length-1),y=(v:number)=>160-v/max*130;
  return <View style={{gap:8}}><Svg width="100%" height={190} viewBox="0 0 600 190" accessibilityLabel="График чисел по периодам">
   <Line x1={24} x2={576} y1={160} y2={160} stroke={c.line}/><Line x1={24} x2={24} y1={20} y2={160} stroke={c.line}/>
   <SvgText x={15} y={30} fontSize={12} fill={c.muted} textAnchor="end">{max}</SvgText><SvgText x={15} y={164} fontSize={12} fill={c.muted} textAnchor="end">0</SvgText>
   <Polyline points={items.map((i,n)=>`${x(n)},${y(i.value)}`).join(' ')} fill="none" stroke={c.accent} strokeWidth={2}/>
   {[0,Math.floor((items.length-1)/2),items.length-1].map(n=><SvgText key={n} x={x(n)} y={183} textAnchor={n===0?'start':n===items.length-1?'end':'middle'} fontSize={10} fill={c.muted}>{items[n].label}</SvgText>)}
  </Svg><Text style={s.small}>Все значения этого графика перечислены в результатах ниже и сохраняются в PDF.</Text></View>;
 }
 return <View style={{gap:10}}>{items.map((i,n)=><View key={n} style={{gap:5}}><View style={s.row}><Text style={[s.small,{flex:1}]}>{i.label}</Text><Text style={s.label}>{i.value}</Text></View><View style={st.track}><View style={[st.fill,{width:`${i.value/max*100}%`}]}/></View></View>)}</View>;
}
const st=StyleSheet.create({matrix:{flexDirection:'row',flexWrap:'wrap',gap:7},cell:{width:'31%',flexGrow:1,borderWidth:1,borderColor:c.line,padding:10,borderRadius:12,gap:4},value:{fontSize:27,fontWeight:'600',color:c.navy},track:{height:8,borderRadius:4,backgroundColor:c.blue},fill:{height:8,borderRadius:4,backgroundColor:c.accent}});
