import {useState} from 'react';
import {Pressable, ScrollView, StyleSheet, Text, View} from 'react-native';
import Svg, {Circle, Line, Polyline, Rect, Text as SvgText} from 'react-native-svg';
import {s} from '../ui';
import {NameSchemes as NameSchemesView} from '../../lib/comprehensiveReport';
import {NameDiagram, NameVisualNode, NameVisualSeries, nameSchemeVisuals} from '../../lib/nameSchemeVisuals';
import {SchemeInterpretation} from './InterpretationSheet';
import {colors as c} from '../../lib/theme';

function Diagram({model,onSelect}:{model:NameDiagram;onSelect:(node:NameVisualNode)=>void}) {
  const [width,setWidth] = useState(240);
  const [large,setLarge] = useState(false);
  const [selected,setSelected] = useState<string|null>(null);
  const renderedWidth = large ? Math.max(width,model.width) : width;
  const scale = renderedWidth/model.width;
  const byId = Object.fromEntries(model.nodes.map(node => [node.id,node]));
  return <View style={styles.diagram} onLayout={event => setWidth(Math.max(1,event.nativeEvent.layout.width))}>
    <View style={styles.toolbar}>
      <Text style={[s.small,{flex:1}]}>{model.kind === 'triangle' ? '9 рядов · 45 чисел' : '7 точек имени'}</Text>
      <Pressable accessibilityRole="button" accessibilityState={{expanded:large}}
        accessibilityLabel={large ? 'Показать схему целиком' : 'Увеличить числа схемы'}
        onPress={() => setLarge(!large)} style={styles.zoom}>
        <Text style={styles.zoomText}>{large ? 'Целиком' : 'Крупнее'}</Text>
      </Pressable>
    </View>
    {large && <Text style={s.small}>Сдвигайте схему по горизонтали. Нажмите «Целиком», чтобы вернуться к обзору.</Text>}
    <ScrollView horizontal scrollEnabled={large} showsHorizontalScrollIndicator={large}>
      <View style={{width:renderedWidth,height:model.height*scale}}>
        <Svg fontFamily="sans-serif" width={renderedWidth} height={model.height*scale} viewBox={`0 0 ${model.width} ${model.height}`}
          accessible={false} pointerEvents="none">
          {model.edges.map(edge => {
            const a=byId[edge.from],b=byId[edge.to],active=edge.to === selected || edge.from === selected;
            return <Line key={`${edge.from}-${edge.to}`} x1={a.x} y1={a.y} x2={b.x} y2={b.y}
              stroke={active ? c.accent : c.line} strokeWidth={active ? 2.5 : 1.5}/>;
          })}
          {model.letters.map(letter => <SvgText key={letter.id} x={letter.x} y={letter.y}
            textAnchor="middle" fontSize={21} fontWeight="600" fill={c.muted}>{letter.text}</SvgText>)}
          {model.nodes.map(node => <Circle key={node.id} cx={node.x} cy={node.y} r={node.radius}
            fill={node.id === selected ? c.navy : c.blue} stroke={node.id === selected ? c.navy : '#CCDCEB'} strokeWidth={1.5}/>)}
          {model.nodes.map(node => <SvgText key={`value-${node.id}`} x={node.x} y={node.y+8}
            textAnchor="middle" fontSize={model.kind === 'human' ? 26 : 25} fontWeight="600"
            fill={node.id === selected ? '#FFFFFF' : c.navy}>{node.value}</SvgText>)}
          {model.nodes.filter(node => node.labelLines?.length).map(node =>
            <Rect key={`label-bg-${node.id}`} x={node.x-47} y={node.labelY!-14} width={94}
              height={node.labelLines!.length*19+4} rx={5} fill={c.surface}/>)}
          {model.nodes.flatMap(node => (node.labelLines || []).map((label,index) =>
            <SvgText key={`label-${node.id}-${index}`} x={node.x} y={node.labelY!+index*19}
              textAnchor="middle" fontSize={15} fontWeight="500" fill={c.ink}>{label}</SvgText>))}
        </Svg>
        {model.nodes.map(node => {
          const target = model.kind === 'human' ? Math.min(76*scale,renderedWidth/3) : 44*scale;
          return <Pressable key={node.id} accessibilityRole="button"
            accessibilityLabel={`${node.title}: ${node.value}. ${node.formula}. Открыть трактовку`}
            accessibilityState={{selected:node.id === selected}}
            onPress={() => {setSelected(node.id);onSelect(node);}}
            style={{position:'absolute',left:node.x*scale-target/2,top:(node.y-node.radius-3)*scale,
              width:target,height:model.kind === 'human' ? 94*scale : 44*scale,borderRadius:12}}/>;
        })}
      </View>
    </ScrollView>
  </View>;
}

function SourceSeries({model}:{model:NameVisualSeries}) {
  const [width,setWidth] = useState(240);
  const summary = model.points.map(point => `${point.label}: ${point.value}`).join(', ');
  return <View style={styles.series} onLayout={event => setWidth(Math.max(1,event.nativeEvent.layout.width))}>
    <Text accessibilityRole="header" style={s.label}>{model.title}</Text>
    <View accessible accessibilityRole="image" accessibilityLabel={`${model.title}. ${summary}. ${model.note}`}>
      <Svg fontFamily="sans-serif" width={width} height={model.height*width/model.width} viewBox={`0 0 ${model.width} ${model.height}`} accessible={false}>
        {model.ticks.map(tick => <Line key={tick.value} x1={22} x2={432} y1={tick.y} y2={tick.y} stroke={c.line} strokeWidth={1}/>)}
        {model.kind === 'sequence' && <Polyline points={model.points.map(point => `${point.x},${point.y}`).join(' ')}
          fill="none" stroke={c.accent} strokeWidth={3} strokeLinejoin="round"/>}
        {model.points.map(point => model.kind === 'distribution' ?
          <Rect key={point.id} x={point.x-12} y={point.y} width={24} height={Math.max(1,model.baseline-point.y)} rx={4} fill={c.accent}/> :
          <Circle key={point.id} cx={point.x} cy={point.y} r={4} fill={c.accent}/>)}
        {model.points.map(point => <SvgText key={`number-${point.id}`} x={point.x} y={point.y-12}
          textAnchor="middle" fontSize={20} fontWeight="600" fill={c.navy}>{point.value}</SvgText>)}
        {model.points.map(point => <SvgText key={`label-${point.id}`} x={point.x} y={model.baseline+28}
          textAnchor="middle" fontSize={20} fill={c.muted}>{point.label}</SvgText>)}
      </Svg>
    </View>
    <Text style={s.small}>{model.note}</Text>
  </View>;
}

export function NameSchemes({data,kind,onSelect}:{data:NameSchemesView;kind:'triangle'|'human';onSelect:(detail:SchemeInterpretation)=>void}) {
  if (!data.available) return <Text style={s.body}>{data.note}</Text>;
  const model = nameSchemeVisuals(data)[kind];
  if (!model) return <Text style={s.body}>{(kind === 'triangle' ? data.triangleNote : data.humanNote) || 'Данных для этой схемы недостаточно.'}</Text>;
  const open = (node:NameVisualNode) => onSelect({title:node.title,value:node.value,meaning:node.meaning,
    interpretation:node.meaning,knowledgeDigit:node.value,calculationSummary:node.formula,note:node.meaning});
  return <View style={styles.content}>
    <Text style={[s.label,{fontSize:15,lineHeight:22}]}>{kind === 'triangle' ? `${data.name} ${data.surname}` : `Имя в расчёте: ${data.name}`}</Text>
    <Text style={s.small}>{kind === 'triangle' ?
      'Две соседние ячейки соединены с результатом их сложения в следующем ряду. Нажмите число для расчёта и трактовки.' :
      'Буквы имени и числа даты соединены в персональную схему. Нажмите на любую точку для её расчёта и трактовки.'}</Text>
    <Diagram key={`${kind}-${data.name}-${data.surname}`} model={model} onSelect={open}/>
    {model.series && <SourceSeries model={model.series}/>}
  </View>;
}

const styles = StyleSheet.create({
  content:{gap:12},diagram:{gap:8,width:'100%'},toolbar:{flexDirection:'row',alignItems:'center',gap:8},
  zoom:{minHeight:44,minWidth:88,paddingHorizontal:13,alignItems:'center',justifyContent:'center',borderRadius:12,backgroundColor:c.blue},
  zoomText:{fontSize:13,fontWeight:'600',color:c.navy},
  series:{gap:8,paddingTop:16,borderTopWidth:1,borderTopColor:c.line},
});
