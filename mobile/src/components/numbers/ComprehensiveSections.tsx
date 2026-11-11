import {NameSchemes} from './NameSchemes';
import {useMemo,useState} from 'react';
import {Pressable,ScrollView,Text,View} from 'react-native';
import Svg,{Line,Polyline,Text as SvgText} from 'react-native-svg';
import {Button,Card,s} from '../ui';
import {NarrationClip} from '../audio/Narration';
import {PersonalResultView} from '../../lib/personalReport';
import {comprehensiveReport,Teaching} from '../../lib/comprehensiveReport';
import {InterpretationSheet,SchemeInterpretation} from './InterpretationSheet';
import {colors as c} from '../../lib/theme';
function Explanation({item}:{item:Teaching}){const [method,setMethod]=useState(false);return <><Text selectable style={s.body}>{item.meaning}</Text><NarrationClip id={item.id}/><Text selectable style={s.small}>{item.focus}</Text><Button secondary title={method?'Скрыть метод':'Как получены эти числа'} onPress={()=>setMethod(!method)}/>{method&&<Text selectable style={s.body}>{item.method}</Text>}</>;}
export function ComprehensiveSections({result,onProfile}:{result:PersonalResultView;onProfile:()=>void}){
 const data=useMemo(()=>comprehensiveReport(result),[result]),[open,setOpen]=useState(false),[section,setSection]=useState(0),[period,setPeriod]=useState(0),[detail,setDetail]=useState<SchemeInterpretation|null>(null);
 if(!data)return null;
 const {fractal,tasks,individual,cycles}=data,teaching=data.knowledge[section],selected=cycles.periods[period];
 const number=(title:string,value:number,formula:string)=><Pressable key={title} accessibilityRole="button" accessibilityLabel={`${title}: ${value}. Открыть расшифровку`} onPress={()=>setDetail({title,value,meaning:value===0?'Ноль получился из равных исходных чисел. Это арифметическое совпадение; оно не означает отсутствие задач.':teaching.meaning,knowledgeDigit:value>=1&&value<=9?value:undefined,knowledgeMaster:[11,22,33].includes(value)?value:undefined,calculationSummary:formula,narrationId:value===0?teaching.id:undefined})} style={{flexGrow:1,flexBasis:100,padding:14,borderWidth:1,borderColor:c.line,borderRadius:15,backgroundColor:c.surface,gap:6}}><Text style={s.label}>{title}</Text><Text style={[s.heading,{fontSize:30}]}>{value}</Text><Text style={s.small}>{formula}</Text></Pressable>;
 const [bd,bm,by]=data.birthDate.split('.').map(Number);
 // Author's table: peaks d+m, d+y, P1+P2, m+y; challenges the matching differences; shadow = peak + d, m, y, destiny.
 const {digit1:d,digit2:m,digit3:y}=fractal,peaks=cycles.periods.map(p=>p.peak),challenges=cycles.periods.map(p=>p.challenge);
 const taskValues=tasks?[tasks.problem1,tasks.problem2,tasks.problem3,tasks.problem4]:[];
 const taskFormulas=tasks?[`|${tasks.calculations.soulNumber} − ${tasks.calculations.mindNumber}|`,`|${tasks.calculations.soulNumber} − ${fractal.digit3}|`,`|${tasks.problem1} − ${tasks.problem2}|`,`|${tasks.calculations.mindNumber} − ${fractal.digit3}|`]:[];
 return <View style={{gap:16}}><Button secondary title={open?'Скрыть дополнительные расчёты':'Все схемы: имя, задачи и личные периоды'} onPress={()=>setOpen(!open)}/>{open&&<>
  <Text style={s.small}>Дополнение к сохранённому отчёту. Новое списание не требуется. Дата личных периодов: {data.targetDate.split('-').reverse().join('.')}.</Text>
  <View style={{flexDirection:'row',flexWrap:'wrap',gap:8}}>{data.knowledge.map((item,i)=><Pressable key={item.id} accessibilityRole="button" accessibilityState={{selected:section===i}} onPress={()=>setSection(i)} style={{padding:12,borderWidth:1,borderColor:section===i?c.navy:c.line,borderRadius:12,backgroundColor:section===i?c.blue:c.surface}}><Text style={s.label}>{item.title}</Text></Pressable>)}</View>
  <Card><Text style={s.title}>{teaching.title}</Text><Explanation key={teaching.id} item={teaching}/>
   {section===0&&<View style={{flexDirection:'row',flexWrap:'wrap',gap:10}}>{number('1 · День',fractal.digit1,`${bd} → ${fractal.digit1}`)}{number('2 · Месяц',fractal.digit2,`${bm} → ${fractal.digit2}`)}{number('3 · Год',fractal.digit3,`${by} → ${fractal.digit3}`)}{number('4 · Сумма',fractal.digit4,`${bd} + ${bm} + ${by} → ${fractal.digit4}`)}</View>}
   {section===1&&(tasks?<View style={{gap:14}}>{taskValues.map((value,i)=>{const bounds=[tasks.period1,tasks.period2,tasks.period3,tasks.period4][i];return <View key={i} style={{gap:5}}>{number(`Задача ${i+1}`,value,`${taskFormulas[i]} → ${value}`)}<Text style={s.small}>{i===2?'На протяжении жизни':bounds.end!==null?`От границы ${bounds.start} до границы ${bounds.end} лет`:`От границы ${bounds.start} лет`}</Text></View>;})}</View>:<Text style={s.body}>Для задач нужны сохранённые числа души, ума и судьбы. В этом результате часть значений не получена.</Text>)}
   {section===2&&<View style={{flexDirection:'row',flexWrap:'wrap',gap:10}}>{([['Год','chig'],['Месяц','chim'],['День','chid'],['Задача года','chpg'],['Задача месяца','chpm'],['Задача дня','chpd']] as const).map(([title,key])=>number(title,individual[key].value,individual[key].calculation))}</View>}
   {section===3&&<><Text style={s.label}>Числа личных годов от 1 до 100 лет</Text><Svg width="100%" height={156} viewBox="0 0 320 156" accessibilityLabel="Числа личных годов, возраст от одного до ста лет, шкала от одного до девяти">{[1,5,9].map(v=><Line key={v} x1={24} x2={310} y1={12+(9-v)*14} y2={12+(9-v)*14} stroke={c.line}/>)}{[1,5,9].map(v=><SvgText key={v} x={17} y={16+(9-v)*14} fill={c.muted} fontSize={10} textAnchor="end">{v}</SvgText>)}<Polyline points={cycles.years.map(y=>`${24+(y.age-1)*286/99},${12+(9-y.chlg)*14}`).join(' ')} stroke={c.accent} fill="none" strokeWidth={1.5}/><SvgText x={24} y={147} fontSize={11} fill={c.muted}>1 год</SvgText><SvgText x={310} y={147} textAnchor="end" fontSize={11} fill={c.muted}>100 лет</SvgText></Svg>
    <ScrollView horizontal contentContainerStyle={{gap:8}}>{cycles.periods.map((p,i)=><Pressable key={p.index} accessibilityRole="button" accessibilityState={{selected:period===i}} onPress={()=>setPeriod(i)} style={{padding:12,minHeight:44,borderWidth:1,borderColor:period===i?c.navy:c.line,backgroundColor:period===i?c.blue:c.surface,borderRadius:12}}><Text style={s.label}>{p.startAge}–{p.endAge} лет</Text></Pressable>)}</ScrollView>
    <Text style={s.title}>Период {selected.index} · {selected.startAge}–{selected.endAge} лет</Text><View style={{flexDirection:'row',flexWrap:'wrap',gap:10}}>{number('Тень',selected.shadow,`${selected.peak} + ${[d,m,y,fractal.digit4][period]} → ${selected.shadow}`)}{number('Вершина',selected.peak,`${[`${d} + ${m}`,`${d} + ${y}`,`${peaks[0]} + ${peaks[1]}`,`${m} + ${y}`][period]} → ${selected.peak}`)}{number('Вызов',selected.challenge,`${[`|${m} − ${d}|`,`|${d} − ${y}|`,`|${challenges[0]} − ${challenges[1]}|`,`|${m} − ${y}|`][period]} → ${selected.challenge}`)}{number('Переход',selected.transition,`${selected.shadow} + ${selected.peak} + ${selected.challenge} → ${selected.transition}`)}</View>
    {selected.years.map(y=><View key={y.age} style={s.row}><Text style={s.small}>{y.age} лет · {y.year} год</Text><Text style={s.label}>{y.chlg}</Text></View>)}
   </>}
   {section>=4&&<NameSchemes data={data.nameSchemes} kind={section===4?'triangle':'human'} onSelect={setDetail}/>}
  </Card>
 </>}<InterpretationSheet detail={detail} onClose={()=>setDetail(null)} onProfile={onProfile}/></View>;
}
