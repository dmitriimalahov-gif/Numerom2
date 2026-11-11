import {useState} from 'react';
import {StyleSheet, Text, View} from 'react-native';
import {Button, s} from '../ui';
import {PersonalResultView, NumberDetailView} from '../../lib/personalReport';
import {SchemeCell, SchemeLine} from '../../lib/personalScheme';
import {serverDate} from '../../lib/serverDate';
import {PersonalScheme} from './PersonalScheme';
import {InterpretationSheet, SchemeInterpretation} from './InterpretationSheet';
import {PlanetCharts} from './PlanetCharts';
import {ExportReport} from './ExportReport';
import {ComprehensiveSections} from './ComprehensiveSections';
import {NarrationProvider,NarrationClip} from '../audio/Narration';

function savedDate(value:string) {
  const date=serverDate(value);
  return date ? date.toLocaleString('ru-RU',{day:'numeric',month:'long',year:'numeric',hour:'2-digit',minute:'2-digit'}) : 'дата сохранения не получена';
}

export function PersonalReport({result,onProfile}: {result:PersonalResultView;onProfile:()=>void}) {
  const {report}=result;
  const [selected,setSelected]=useState('soul');
  const [detail,setDetail]=useState<SchemeInterpretation|null>(null);
  const [showBasis,setShowBasis]=useState(false);
  const [showSchemeMethod,setShowSchemeMethod]=useState(false);
  const openNumber=(item:NumberDetailView) => {
    setSelected(item.key);
    setDetail({...item,
      narrationId:item.key,
      knowledgeDigit:item.value!==null && Number.isInteger(item.value) && item.value>=1 && item.value<=9 ? item.value : undefined,
      knowledgeMaster:item.value!==null && [11,22,33].includes(item.value) ? item.value : undefined,
      profileAction:item.value===null && ['full_name','wisdom'].includes(item.key)});
  };
  const openCell=(item:SchemeCell) => {
    setSelected(`cell-${item.digit}`);
    setDetail({title:`${item.title} · цифра ${item.digit}`,value:item.count,meaning:item.meaning,knowledgeDigit:item.digit,
      valueCaption:'Повторений в вашей схеме',
      calculationSummary:item.digits ? `В ячейке: ${item.digits}` : `Цифра ${item.digit} не встречается в расчёте.`});
  };
  const openLine=(item:SchemeLine) => {
    setSelected(`line-${item.key}`);
    const counts=item.digits.map(digit => report.scheme!.cells.find(cell => cell.digit===digit)!.count);
    setDetail({title:item.title,value:item.value,meaning:item.meaning,
      narrationId:item.key,
      method:'Складываем количество цифр в ячейках выбранной линии.',
      steps:[`Ячейки: ${item.digits.join(' · ')}`,`${counts.join(' + ')} = ${item.value}`]});
  };
  return <NarrationProvider path="/narration/project"><View style={styles.report}>
    <View style={styles.header}>
      <Text accessibilityRole="header" style={styles.title}>Ваша персональная схема</Text>
      <Text style={styles.date}>{report.birthDate}{report.birthWeekday ? ` · ${report.birthWeekday.toLowerCase()}` : ''}</Text>
      {!!report.profileName && <Text style={s.small}>Имя в расчёте: {report.profileName}</Text>}
      <Text style={s.small}>{result.source==='saved' ? `Сохранён: ${savedDate(result.createdAt)}` : 'Новый результат'}</Text>
      <Text style={styles.free}>Просмотр всех разделов бесплатный.</Text>
    </View>
    <PersonalScheme numbers={report.numbers} scheme={report.scheme} selected={selected} onNumber={openNumber} onCell={openCell} onLine={openLine}/>
    {report.scheme && <View style={{gap:12}}>
      <Button title={showSchemeMethod?'Скрыть расчёт схемы':'Расчёт схемы'} secondary onPress={()=>setShowSchemeMethod(!showSchemeMethod)}/>
      {showSchemeMethod && <View style={styles.basis}>
        <Text accessibilityRole="header" style={styles.basisTitle}>Квадрат Пифагора · метод Александрова</Text>
        <NarrationClip id="square"/>
        <Text style={styles.copy}>Дата: {report.birthDate}. Цифры даты и четырёх дополнительных чисел распределяются по ячейкам. Нули пропускаем.</Text>
        <Text selectable style={styles.copy}>А1: {report.birthDate.replace(/\D/g,'').split('').join(' + ')} = {report.scheme.additionalNumbers[0]}</Text>
        <Text selectable style={styles.copy}>А2: {String(report.scheme.additionalNumbers[0]).split('').join(' + ')} = {report.scheme.additionalNumbers[1]}</Text>
        <Text selectable style={styles.copy}>А3: |{report.scheme.additionalNumbers[0]} − 2 × {report.birthDate[0]}| = {report.scheme.additionalNumbers[2]}</Text>
        <Text selectable style={styles.copy}>А4: {String(report.scheme.additionalNumbers[2]).split('').join(' + ')} = {report.scheme.additionalNumbers[3]}</Text>
        <Text style={styles.copy}>В А3 используется первая цифра дня в записи ДД; для дней 01–09 это 0. Сумма линии — количество цифр в её трёх ячейках.</Text>
      </View>}
    </View>}
    {report.incomplete && <Text style={s.small}>Часть пояснений не получена. Показаны только доступные значения.</Text>}
    {report.planets && report.planets.items.length===7 ? <View style={{gap:12}}><Text accessibilityRole="header" style={styles.title}>Сила планет</Text><Text style={s.small}>Показатели вашей даты рождения по дням недели. Шкала от 0 до 9.</Text><PlanetCharts planets={report.planets}/></View> : <View style={styles.missing}><Text style={styles.title}>Планетарный график</Text><Text style={s.body}>{report.planets?.note || 'Показатели планет для этого результата не получены.'}</Text></View>}
    {report.planets && <View style={{gap:14}}>
      <Button title={showBasis ? 'Скрыть формулу графика' : 'Формула планетарного графика'} secondary onPress={() => setShowBasis(!showBasis)}/>
      {showBasis && <View style={styles.basis}>
        <Text accessibilityRole="header" style={styles.basisTitle}>Основа расчёта планет</Text>
        <NarrationClip id="planet-chart"/>
        {!!report.planets.birthWeekday && <Text style={styles.copy}>День рождения: {report.planets.birthWeekday.toLowerCase()}.</Text>}
        {report.planets.calculationNumber!==null && <Text style={styles.copy}>Расчётное число: {report.planets.calculationNumber}.</Text>}
        {!!report.planets.formula && <Text selectable style={styles.formula}>{report.planets.formula}</Text>}
        {!!report.planets.note && <Text selectable style={s.small}>{report.planets.note}</Text>}
      </View>}
    </View>}
    <ComprehensiveSections result={result} onProfile={onProfile}/>
    <ExportReport result={result}/>
    <InterpretationSheet detail={detail} onClose={() => setDetail(null)} onProfile={onProfile}/>
  </View></NarrationProvider>;
}
const styles=StyleSheet.create({
  report:{gap:23},header:{gap:6},title:{fontSize:22,lineHeight:29,fontWeight:'600',color:'#003447',letterSpacing:-.35},
  date:{fontSize:15,lineHeight:23,color:'#20364E'},free:{fontSize:12,lineHeight:19,color:'#28705E',marginTop:3},
  basis:{padding:18,borderRadius:16,backgroundColor:'#E8F4EE',gap:12},basisTitle:{fontSize:17,lineHeight:24,fontWeight:'600',color:'#003447'},
  copy:{fontSize:14,lineHeight:23,color:'#20364E'},formula:{fontSize:19,lineHeight:27,fontWeight:'500',color:'#003447'},missing:{gap:10},
});
