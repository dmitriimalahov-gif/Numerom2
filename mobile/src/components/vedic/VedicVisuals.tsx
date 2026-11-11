import {useState} from 'react';
import {Pressable,ScrollView,StyleSheet,Text,View} from 'react-native';
import Svg,{Circle,G,Line,Path,Polyline,Rect,Text as SvgText} from 'react-native-svg';
import {Button,s} from '../ui';
import type {VedicDay} from '../../lib/vedicCalculations';
import {VEDIC_PLANETS,planetSeriesModel,solarWheelModel,periodTimelineModel} from '../../lib/vedicVisuals';

const ink='#003447';
const displayDate=(value:string)=>value.split('-').reverse().join('.');
const number=(value:number)=>value.toLocaleString('ru-RU',{maximumFractionDigits:2});
type Energy=VedicDay['energies'][number];
type CoordinateEvent={nativeEvent?:Record<string,unknown>;currentTarget?:{getBoundingClientRect?:()=>{left:number;top:number;width:number;height:number}};target?:unknown};
function pressCoordinate(event:unknown,axis:'x'|'y',extent:number):number|null {
  const source=event as CoordinateEvent,native=source?.nativeEvent;
  if(!native||!Number.isFinite(extent)||extent<=0)return null;
  const local=native[axis==='x'?'locationX':'locationY'];
  if(typeof local==='number'&&Number.isFinite(local))return local;
  // Web onPress carries a MouseEvent without React Native's locationX/Y.
  // Measure the current overlay, not a potentially different event target.
  const client=native[axis==='x'?'clientX':'clientY'],bounds=source.currentTarget?.getBoundingClientRect?.();
  const origin=bounds?.[axis==='x'?'left':'top'],size=bounds?.[axis==='x'?'width':'height'];
  if(typeof client==='number'&&Number.isFinite(client)&&typeof origin==='number'&&Number.isFinite(origin)&&typeof size==='number'&&Number.isFinite(size)&&size>0)
    return (client-origin)*extent/size;
  const offset=native[axis==='x'?'offsetX':'offsetY'];
  if(source.currentTarget&&(native.target===source.currentTarget||source.target===source.currentTarget)&&typeof offset==='number'&&Number.isFinite(offset))return offset;
  return null;
}

export function PlanetRouteChart({days,index,onDay,onInterpret}:{days:VedicDay[];index:number;onDay:(index:number)=>void;onInterpret:(energy:Energy)=>void}) {
  const [planetKey,setPlanetKey]=useState('surya');
  const [width,setWidth]=useState(234);
  const model=planetSeriesModel(days,planetKey,{width});
  const day=days[index]||days[0];
  const entry=day?.energies.find(item=>item.key===planetKey);
  const selected=model?.points.find(point=>point.index===index);
  return <View style={styles.section}>
    <Text accessibilityRole="header" style={styles.title}>Ритм девяти планет</Text>
    <Text style={s.small}>На графике одна выбранная планета. Индекс числовой модели: от 0 до 100.</Text>
    <View style={styles.legend}>
      {VEDIC_PLANETS.map(planet=>{
        const value=day?.energies.find(item=>item.key===planet.key)?.value;
        return <Pressable key={planet.key} accessibilityRole="button" accessibilityState={{selected:planet.key===planetKey}}
          accessibilityLabel={`${planet.title}: ${typeof value==='number'?number(value):'нет данных'}. Показать график`}
          onPress={()=>setPlanetKey(planet.key)} style={({pressed})=>[styles.planetButton,planet.key===planetKey&&styles.selected,pressed&&styles.pressed]}>
          <View style={[styles.dot,{backgroundColor:planet.color,borderColor:planet.stroke}]}/>
          <Text style={styles.planetTitle}>{planet.title}</Text><Text style={styles.legendValue}>{typeof value==='number'?number(value):'—'}</Text>
        </Pressable>;
      })}
    </View>
    {model?<>
      <View style={styles.chartHeading}><Text style={styles.title}>{model.planet.title}</Text><Text style={styles.currentValue}>{selected?number(selected.value):'—'}<Text style={styles.limit}> / 100</Text></Text></View>
      <View style={{height:model.height,width:'100%'}} onLayout={event=>setWidth(event.nativeEvent.layout.width)}>
        <Svg width="100%" height={model.height} viewBox={`0 0 ${model.width} ${model.height}`} accessible={false} accessibilityElementsHidden>
          {model.ticks.map(tick=><G key={tick.value}><Line x1={model.left} x2={model.right} y1={tick.y} y2={tick.y} stroke="#d5e2dc"/>
            <SvgText x={model.left-8} y={tick.y+4} fontSize={11} fill="#577267" textAnchor="end">{tick.value}</SvgText></G>)}
          {selected&&<Line x1={selected.x} x2={selected.x} y1={model.top} y2={model.bottom} stroke="#799689" strokeDasharray="3 4"/>}
          {model.segments.map((segment,i)=><Polyline key={i} points={segment.points} fill="none" stroke={model.planet.stroke} strokeWidth={2.5} strokeLinejoin="round"/>)}
          {model.points.map(point=><Circle key={point.index} cx={point.x} cy={point.y} r={point.index===index?6:days.length<=7?3.5:1.7} fill={model.planet.color} stroke={point.index===index?ink:model.planet.stroke} strokeWidth={point.index===index?2:1}/>)}
          {model.dateTicks.map(tick=><SvgText key={tick.index} x={tick.x} y={model.height-9} fontSize={10} fill="#577267" textAnchor={days.length===1?'middle':tick.index===0?'start':tick.index===days.length-1?'end':'middle'}>{tick.label}</SvgText>)}
        </Svg>
        {days.length>1&&<Pressable testID="vedic-series-touch" accessible={false} focusable={false} style={StyleSheet.absoluteFill}
          onPress={event=>{
            const x=pressCoordinate(event,'x',model.width);
            if(x===null)return;
            const next=Math.max(0,Math.min(days.length-1,Math.round((x-model.left)/(model.right-model.left)*(days.length-1))));
            if(Number.isInteger(next))onDay(next);
          }}/>}
      </View>
      {model.missingDates.length>0&&<Text style={s.small}>Для части дат показатель не получен. Линия в этих местах прерывается.</Text>}
    </>:<Text style={s.body}>Показатели этой планеты для периода не получены.</Text>}
    {days.length>1?<>
      <Text style={s.small}>Выберите день на графике или стрелками.</Text>
      <View style={styles.dayNavigation}>
        <Pressable accessibilityRole="button" accessibilityLabel="Предыдущий день" accessibilityState={{disabled:index===0}} disabled={index===0} onPress={()=>onDay(index-1)} style={[styles.arrow,index===0&&styles.disabled]}><Text style={styles.arrowText}>‹</Text></Pressable>
        <View style={styles.dayLabel}><Text style={styles.label}>{displayDate(day.date)}</Text><Text style={s.small}>{index+1} из {days.length} дней</Text></View>
        <Pressable accessibilityRole="button" accessibilityLabel="Следующий день" accessibilityState={{disabled:index===days.length-1}} disabled={index===days.length-1} onPress={()=>onDay(index+1)} style={[styles.arrow,index===days.length-1&&styles.disabled]}><Text style={styles.arrowText}>›</Text></Pressable>
      </View>
    </>:<Text style={styles.label}>{day?displayDate(day.date):'Дата не получена'}</Text>}
    {entry&&<Button secondary title={`Смысл и озвучка: ${entry.title}`} onPress={()=>onInterpret(entry)}/>}
  </View>;
}

export function DayPeriodTimeline({day,timezone}:{day:VedicDay;timezone:string}) {
  const [width,setWidth]=useState(234),[selectedId,setSelectedId]=useState('rahu_kaal');
  const model=periodTimelineModel(day,{width});
  const selected=model?.rows.find(row=>row.id===selectedId)||model?.rows[0];
  return <View style={styles.section}>
    <Text accessibilityRole="header" style={styles.title}>Четыре периода дня</Text>
    <Text style={s.small}>От восхода до заката · {timezone}. Нажмите на полосу, чтобы прочитать пояснение.</Text>
    {model&&selected?<>
      <View style={{height:model.height,width:'100%'}} onLayout={event=>setWidth(event.nativeEvent.layout.width)}>
        <Svg width="100%" height={model.height} viewBox={`0 0 ${model.width} ${model.height}`} accessible={false} accessibilityElementsHidden>
          {model.rows.map(row=><G key={row.id}>
            {row.id===selected.id&&<Rect x={0} y={row.y-27} width={model.width} height={51} rx={9} fill="#edf5f0"/>}
            <SvgText x={model.left} y={row.y-9} fontSize={12} fontWeight={row.id===selected.id?'600':'400'} fill={ink}>{row.title}</SvgText>
            <Rect x={model.left} y={row.y} width={model.right-model.left} height={row.height} rx={6} fill="#e3ece7"/>
            <Rect x={row.x} y={row.y} width={row.width} height={row.height} rx={Math.min(6,row.width/2)} fill={row.color}/>
          </G>)}
          {model.ticks.map((tick,i)=><SvgText key={i} x={tick.x} y={model.height-5} fontSize={11} fill="#577267" textAnchor={i===0?'start':'end'}>{tick.label}</SvgText>)}
        </Svg>
        {model.rows.map(row=><Pressable key={row.id} accessibilityRole="button" accessibilityLabel={`${row.title}, ${row.startLabel}–${row.endLabel}. Показать пояснение`}
          accessibilityState={{selected:row.id===selected.id}} onPress={()=>setSelectedId(row.id)}
          style={({pressed})=>[{position:'absolute',left:0,right:0,top:row.y-27,height:51,borderRadius:9,borderWidth:1,borderColor:row.id===selected.id?'#b9d3c5':'transparent'},pressed&&{backgroundColor:'rgba(0,52,71,.06)'}]}/>)}
      </View>
      <View accessibilityLiveRegion="polite" style={[styles.reading,{borderLeftColor:selected.color}]}><Text style={styles.label}>{selected.title} · {selected.startLabel}–{selected.endLabel}</Text><Text selectable style={styles.copy}>{selected.meaning||'Пояснение для этого периода не получено.'}</Text></View>
      {model.missingIds.length>0&&<Text style={s.small}>Часть периодов не получена. Показаны только сохранённые интервалы.</Text>}
    </>:<Text style={s.body}>Временные границы периодов не получены. Схема недоступна.</Text>}
  </View>;
}

export function SolarDayWheel({day,timezone}:{day:VedicDay;timezone:string}) {
  const [index,setIndex]=useState(0),[expanded,setExpanded]=useState(false),[size,setSize]=useState(234);
  const model=solarWheelModel(day,{size}),selected=model?.segments[index];
  return <View style={styles.section}>
    <Text accessibilityRole="header" style={styles.title}>Круг 24 планетарных часов</Text>
    <Text style={s.small}>От восхода до следующего восхода. {model?.timeBasis==='elapsed'?'Размер сектора показывает фактическую длительность часа.':'Размер сектора соответствует интервалу на сохранённых местных часах.'} Подписи времени: {timezone}.</Text>
    {model&&selected?<>
      <View style={{width:'100%',aspectRatio:1}} onLayout={event=>setSize(event.nativeEvent.layout.width)}>
        <Svg width="100%" height="100%" viewBox={`0 0 ${model.width} ${model.height}`} accessible={false} accessibilityElementsHidden>
          {model.bands.map(band=><Path key={band.period} d={band.path} fill={band.period==='day'?'#e7bd67':'#537699'}/>)}
          {model.segments.map(segment=><G key={segment.index}><Path d={segment.path} fill={segment.color} stroke={segment.index===index?ink:'#ffffff'} strokeWidth={segment.index===index?2.5:1}/>
            <SvgText x={segment.labelX} y={segment.labelY+3.5} fontSize={10} fontWeight={segment.index===index?'700':'400'} fill={segment.planet==='shani'?'#ffffff':ink} textAnchor="middle">{segment.hour}</SvgText></G>)}
          {model.markers.map(marker=><Circle key={marker.kind} cx={marker.x} cy={marker.y} r={3} fill={ink} stroke="#ffffff" strokeWidth={1}/>)}
          <SvgText x={model.cx} y={model.cy-23} fontSize={11} fill="#577267" textAnchor="middle">{selected.period==='day'?'Дневной':'Ночной'} час {selected.hour}</SvgText>
          <SvgText x={model.cx} y={model.cy} fontSize={16} fontWeight="600" fill={ink} textAnchor="middle">{selected.title}</SvgText>
          <SvgText x={model.cx} y={model.cy+23} fontSize={12} fill={ink} textAnchor="middle">{selected.startLabel}–{selected.endLabel}</SvgText>
        </Svg>
        <Pressable testID="vedic-wheel-touch" accessible={false} focusable={false} style={StyleSheet.absoluteFill} onPress={event=>{
          const x=pressCoordinate(event,'x',model.width),y=pressCoordinate(event,'y',model.height);
          if(x===null||y===null)return;
          const angle=(Math.atan2(x-model.cx,-(y-model.cy))*180/Math.PI+360)%360;
          const segment=model.segments.find(item=>angle>=item.startAngle&&angle<item.endAngle);
          if(segment)setIndex(segment.index);
        }}/>
      </View>
      <View style={styles.solarLegend}><View style={styles.legendItem}><View style={[styles.dot,{backgroundColor:'#e7bd67',borderColor:'#c09a4b'}]}/><Text style={s.small}>День {model.startLabel}–{model.sunsetLabel}</Text></View><View style={styles.legendItem}><View style={[styles.dot,{backgroundColor:'#537699',borderColor:'#537699'}]}/><Text style={s.small}>Ночь до {model.endLabel}</Text></View></View>
      <Text style={s.small}>Нажмите на сектор или выберите номер часа.</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator contentContainerStyle={{gap:7}} style={{maxWidth:'100%'}}>
        {model.segments.map(segment=><Pressable key={segment.index} accessibilityRole="button" accessibilityState={{selected:segment.index===index}}
          accessibilityLabel={`Час ${segment.hour}, ${segment.title}, ${segment.startLabel}–${segment.endLabel}${segment.nextDate?', с переходом на следующую дату':''}`}
          onPress={()=>setIndex(segment.index)} style={[styles.hourButton,segment.index===index&&styles.selected]}>
          <View style={[styles.dot,{backgroundColor:segment.color,borderColor:segment.stroke}]}/><Text style={styles.label}>{segment.hour}</Text>
        </Pressable>)}
      </ScrollView>
      <View accessibilityLiveRegion="polite" style={[styles.reading,{borderLeftColor:selected.stroke}]}>
        <Text style={styles.label}>Час {selected.hour} · {selected.title}</Text><Text style={styles.copy}>{displayDate(selected.startDate)} · {selected.startLabel}–{selected.endLabel}{selected.endDate!==selected.startDate?` (${displayDate(selected.endDate)})`:''}</Text>
      </View>
      <Button secondary title={expanded?'Скрыть расписание часов':'Все часы и время'} onPress={()=>setExpanded(!expanded)}/>
      {expanded&&<View style={{gap:9}}>{model.segments.map(segment=><Text key={segment.index} style={s.small}>{segment.hour}. {segment.title} · {segment.startLabel}–{segment.endLabel}{segment.startDate!==day.date?' · следующая дата':''}</Text>)}</View>}
    </>:<Text style={s.body}>Полные границы 24 часов не получены. Круг пока недоступен.</Text>}
  </View>;
}

const styles=StyleSheet.create({
  section:{gap:14,minWidth:0},title:{fontSize:20,lineHeight:27,fontWeight:'600',color:ink},label:{fontSize:13,lineHeight:20,fontWeight:'600',color:ink},copy:{fontSize:14,lineHeight:22,color:'#254e53'},
  legend:{flexDirection:'row',flexWrap:'wrap',gap:7},planetButton:{flexBasis:'46%',flexGrow:1,minWidth:0,minHeight:48,paddingHorizontal:9,paddingVertical:9,borderRadius:11,borderWidth:1,borderColor:'#d8e7de',backgroundColor:'#f4f9f6',flexDirection:'row',alignItems:'center',gap:6},
  selected:{borderColor:ink,backgroundColor:'#e1f0e7'},pressed:{opacity:.7},disabled:{opacity:.4},dot:{width:10,height:10,borderRadius:5,borderWidth:1,flexShrink:0},planetTitle:{fontSize:12,lineHeight:18,color:ink,flex:1},legendValue:{fontSize:12,lineHeight:18,fontWeight:'600',color:ink},
  chartHeading:{flexDirection:'row',justifyContent:'space-between',alignItems:'center',gap:8},currentValue:{fontSize:26,lineHeight:33,color:ink,fontWeight:'500'},limit:{fontSize:12,color:'#577267'},
  dayNavigation:{flexDirection:'row',alignItems:'center',gap:10},dayLabel:{flex:1,alignItems:'center',gap:2},arrow:{minWidth:48,minHeight:48,alignItems:'center',justifyContent:'center',borderRadius:12,backgroundColor:'#e8f4ee'},arrowText:{fontSize:28,color:ink},
  reading:{padding:13,gap:6,borderLeftWidth:3,borderRadius:10,backgroundColor:'#f1f7f3'},solarLegend:{flexDirection:'row',flexWrap:'wrap',gap:10},legendItem:{flexDirection:'row',gap:6,alignItems:'center'},
  hourButton:{minWidth:48,minHeight:48,flexDirection:'row',alignItems:'center',justifyContent:'center',gap:6,padding:9,borderRadius:10,borderWidth:1,borderColor:'#d8e7de',backgroundColor:'#f4f9f6'},
});
