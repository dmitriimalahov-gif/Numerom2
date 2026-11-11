import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, G, Line, Polyline, Rect, Text as SvgText } from 'react-native-svg';
import type { PersonalReportView } from '../../lib/personalReport';
import { orderedPlanetItems, planetChartGeometry } from '../../lib/planetChart';
import {NumberVoice} from './NumberVoice';

const ink = '#003447';
const chartHeight = 228;

export function PlanetCharts({planets}: {planets: NonNullable<PersonalReportView['planets']>}) {
  const [mode, setMode] = useState<'line' | 'bars'>('line');
  const [selectedName, setSelectedName] = useState('Солнце');
  const [width, setWidth] = useState(0);
  const [focused, setFocused] = useState<string | null>(null);
  const items = orderedPlanetItems(planets.items);
  const geometry = planetChartGeometry(planets.items, width, chartHeight);
  const selected = items?.find(item => item.name === selectedName) || items?.[0];

  if (!items || !selected) return <View style={styles.unavailable}>
    <Text style={styles.unavailableTitle}>График пока недоступен</Text>
    <Text style={styles.hint}>Для графика нужны значения всех семи планет от 0 до 9. В этом результате они получены не полностью.</Text>
    {planets.note ? <Text selectable style={styles.hint}>{planets.note}</Text> : null}
  </View>;

  return <View style={styles.card}>
    <View style={styles.toolbar}>
      <View style={styles.switch} accessibilityRole="tablist" accessibilityLabel="Вид графика планет">
        {([{key: 'line', title: 'Линия'}, {key: 'bars', title: 'Столбцы'}] as const).map(option =>
          <Pressable key={option.key} accessibilityRole="tab" accessibilityState={{selected: mode === option.key}}
            accessibilityLabel={option.title} onPress={() => setMode(option.key)}
            onFocus={() => setFocused(option.key)} onBlur={() => setFocused(null)}
            style={({pressed}) => [styles.modeButton, mode === option.key && styles.activeMode, focused === option.key && styles.focused, pressed && styles.pressed]}>
            <Text style={[styles.modeText, mode === option.key && styles.activeModeText]}>{option.title}</Text>
          </Pressable>)}
      </View>
      <Text style={styles.scale}>Шкала 0–9</Text>
    </View>
    <View style={styles.canvas} onLayout={event => setWidth(event.nativeEvent.layout.width)}>
      {geometry && <>
        <Svg width={geometry.width} height={geometry.height} accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
          {geometry.ticks.map(tick => <G key={tick.value}>
            <Line x1={geometry.left} x2={geometry.right} y1={tick.y} y2={tick.y} stroke="#cadbd2" strokeWidth={tick.value === 0 ? 1.2 : .8}/>
            <SvgText x={geometry.left - 10} y={tick.y + 4} fontSize={11} fill="#53716d" textAnchor="end">{tick.value}</SvgText>
          </G>)}
          {geometry.points.filter(point => point.name === selected.name).map(point =>
            <Line key={point.name} x1={point.x} x2={point.x} y1={geometry.top} y2={geometry.bottom}
              stroke="#809b91" strokeWidth={1} strokeDasharray="3 4"/>)}
          {mode === 'line' && <Polyline points={geometry.points.map(point => `${point.x},${point.y}`).join(' ')}
            fill="none" stroke={ink} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round"/>}
          {geometry.points.map(point => {
            const active = point.name === selected.name;
            const barWidth = Math.min(24, geometry.step * .6);
            return <G key={point.name}>
              {mode === 'bars' && point.value > 0 && <Rect x={point.x - barWidth / 2} y={point.y}
                width={barWidth} height={point.barHeight} fill={point.color} stroke={active ? ink : point.border} strokeWidth={active ? 1.5 : 1}/>}
              {(mode === 'line' || point.value === 0) && <>
                {active && <Circle cx={point.x} cy={point.y} r={10} fill="#ffffff" stroke={ink} strokeWidth={1.2}/>}
                <Circle cx={point.x} cy={point.y} r={active ? 6 : 5} fill={point.color} stroke={point.border} strokeWidth={1.5}/>
              </>}
              <SvgText x={point.x} y={point.y - 14} fontSize={12} fontWeight={active ? '700' : '500'} textAnchor="middle" fill={ink}>{point.value}</SvgText>
              <SvgText x={point.x} y={geometry.bottom + 25} fontSize={12} fontWeight={active ? '700' : '400'} textAnchor="middle" fill={ink}>{point.weekdayShort}</SvgText>
            </G>;
          })}
        </Svg>
        {/* Native hit areas avoid SVG event differences between iOS, Android and web.
            Full-size accessible alternatives below remain available on narrow screens. */}
        {geometry.points.map(point => <Pressable key={point.name} testID={`planet-point-${point.name}`}
          accessible={false} accessibilityElementsHidden importantForAccessibility="no" focusable={false}
          onPress={() => setSelectedName(point.name)}
          style={[styles.pointTarget, {left: point.x - geometry.step / 2, top: point.y - 22, width: geometry.step,
            height: mode === 'bars' ? geometry.bottom - point.y + 44 : 44}]}/>)}
      </>}
    </View>
    <Text style={styles.hint}>Нажмите на {mode === 'line' ? 'точку' : 'столбец'} или выберите планету ниже.</Text>
    <View style={styles.legend}>
      {items.map(item => <Pressable key={item.name} accessibilityRole="button"
        accessibilityLabel={`${item.name}, ${item.weekday.toLowerCase()}: ${item.value} из 9`}
        accessibilityHint="Показывает пояснение планетарной силы"
        accessibilityState={{selected: item.name === selected.name}}
        onPress={() => setSelectedName(item.name)} onFocus={() => setFocused(item.name)} onBlur={() => setFocused(null)}
        style={({pressed}) => [styles.legendButton, item.name === selected.name && styles.activeLegend, focused === item.name && styles.focused, pressed && styles.pressed]}>
        <View style={[styles.swatch, {backgroundColor: item.color, borderColor: item.border}]}/>
        <Text style={styles.legendName}>{item.name}</Text>
        <Text style={styles.legendValue}>{item.value}</Text>
      </Pressable>)}
    </View>
    <View style={[styles.explanation, {borderLeftColor: selected.border}]} accessibilityLiveRegion="polite">
      <View style={styles.explanationHeader}>
        <View style={styles.explanationHeading}>
          <Text accessibilityRole="header" style={styles.selectedTitle}>{selected.name}</Text>
          <Text style={styles.selectedDay}>{selected.weekday}</Text>
        </View>
        <Text style={styles.selectedValue}>{selected.value}<Text style={styles.valueLimit}> / 9</Text></Text>
      </View>
      <Text selectable style={styles.meaning}>{selected.meaning || 'Пояснение для этой планеты в результате отсутствует.'}</Text>
      <NumberVoice key={selected.name} digit={({Солнце:1,Луна:2,Марс:9,Меркурий:5,Юпитер:3,Венера:6,Сатурн:8} as Record<string,number>)[selected.name]}/>
    </View>
  </View>;
}

const styles = StyleSheet.create({
  card: {backgroundColor: '#e8f4ee', borderRadius: 20, padding: 14, gap: 14, minWidth: 0},
  toolbar: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8},
  switch: {flexDirection: 'row', padding: 3, borderRadius: 12, backgroundColor: '#dceae2', gap: 3},
  modeButton: {minHeight: 44, paddingHorizontal: 12, paddingVertical: 10, borderRadius: 9, borderWidth: 1, borderColor: 'transparent', justifyContent: 'center'},
  activeMode: {backgroundColor: '#ffffff', borderColor: '#d1e1d8'},
  modeText: {fontSize: 13, lineHeight: 18, color: '#53716d'}, activeModeText: {color: ink, fontWeight: '600'},
  focused: {borderColor: ink, borderWidth: 2}, pressed: {opacity: .7}, scale: {fontSize: 11, lineHeight: 17, color: '#53716d'},
  canvas: {height: chartHeight, width: '100%'}, pointTarget: {position: 'absolute'},
  hint: {fontSize: 12, lineHeight: 19, color: '#46645f'},
  legend: {flexDirection: 'row', flexWrap: 'wrap', gap: 7},
  legendButton: {flexBasis: '47%', flexGrow: 1, minWidth: 0, minHeight: 48, flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 9, paddingVertical: 9, borderRadius: 10, borderWidth: 1, borderColor: '#d4e4db', backgroundColor: '#f8fcfa'},
  activeLegend: {borderColor: ink, backgroundColor: '#ffffff'},
  swatch: {width: 10, height: 10, borderRadius: 5, borderWidth: 1, flexShrink: 0},
  legendName: {fontSize: 12, lineHeight: 18, color: ink, flex: 1, flexShrink: 1},
  legendValue: {fontSize: 15, lineHeight: 20, color: ink, fontWeight: '600'},
  explanation: {gap: 13, padding: 15, borderLeftWidth: 3, borderRadius: 12, backgroundColor: '#ffffff'},
  explanationHeader: {flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 12},
  explanationHeading: {gap: 3, flex: 1}, selectedTitle: {fontSize: 20, lineHeight: 26, fontWeight: '600', color: ink},
  selectedDay: {fontSize: 12, lineHeight: 18, color: '#53716d'}, selectedValue: {fontSize: 30, lineHeight: 38, fontWeight: '500', color: ink}, valueLimit: {fontSize: 13, fontWeight: '400', color: '#53716d'},
  meaning: {fontSize: 14, lineHeight: 23, color: '#254e53'},
  unavailable: {padding: 16, borderRadius: 14, backgroundColor: '#e8f4ee', gap: 7}, unavailableTitle: {fontSize: 16, lineHeight: 23, color: ink, fontWeight: '600'},
});
