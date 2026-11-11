import {useMemo,useState} from 'react';
import {Text,View} from 'react-native';
import {SvgXml} from 'react-native-svg';
import {FullReport,ReportSection} from '../../../../packages/full-report';
import {sectionDiagram,diagramSvg} from '../../../../packages/full-report/schematics';
import {Button,s} from '../ui';
import {ReportChart} from './ReportChart';
export function ReportDiagram({report,section}:{report:FullReport;section:ReportSection}){
 const [width,setWidth]=useState(300),[activeIndex,setActiveIndex]=useState<number|undefined>();
 const diagram=useMemo(()=>sectionDiagram(report,section),[report,section]);
 const svg=useMemo(()=>diagram?diagramSvg(diagram,{activeIndex}):'',[diagram,activeIndex]);
 if(!diagram)return <ReportChart chart={section.chart}/>;
 return <View style={{gap:12}} onLayout={event=>{const next=event.nativeEvent.layout.width;if(next>0)setWidth(next);}}>
  <Text style={s.label}>{diagram.title}</Text><SvgXml xml={svg} width="100%" height={width*diagram.height/diagram.width} accessibilityLabel={diagram.title}/>
  {diagram.kind==='lines'&&!!diagram.directions?.length&&<View style={{gap:8}}><Button secondary title={activeIndex===undefined?'✓ Все восемь линий':'Все восемь линий'} onPress={()=>setActiveIndex(undefined)}/>{diagram.directions.map((line,index)=><Button key={line.id} secondary title={`${activeIndex===index?'✓ ':''}${line.label} · ${line.value}`} onPress={()=>setActiveIndex(index)}/>)}</View>}
 </View>;
}
