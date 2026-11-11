import {useState} from 'react';
import {Text,View} from 'react-native';
import {FullReportOrder,fullReportHtml,fullReportSchemesHtml,positionParagraphs} from '../../../../packages/full-report';
import {Button,Card,s} from '../ui';
import {SavedReportExport} from '../SavedReportExport';
import {NarrationProvider,NarrationClip} from '../audio/Narration';
import {ReportDiagram} from './ReportDiagram';
import {FullReportVideo} from './FullReportVideo';
import {ReportPreparing} from './ReportPreparing';
export function FullReportDocument({order,archived=false}:{order:FullReportOrder;archived?:boolean}){
 const [opened,setOpened]=useState<string[]>([]),[methods,setMethods]=useState<string[]>([]);
 const report=order.report;if(!report)return null;
 const toggle=(id:string)=>setOpened(v=>v.includes(id)?v.filter(i=>i!==id):[...v,id]);
 const body=<View style={{gap:22}}>
  <View style={{gap:8}}><Text accessibilityRole="header" style={s.heading}>{report.title}</Text>{!!order.person&&<Text style={s.body}>{order.person}</Text>}<Text style={s.body}>Дата рождения: {report.birth_date}</Text><Text style={s.small}>Сохранённый расчёт на {report.as_of_date}. Чтение, аудио, PDF и персональное видео входят в покупку.</Text>{order.mode==='test'&&<Text style={s.label}>Тестовый отчёт · Stripe sandbox</Text>}</View>
  <Card tinted><Text style={s.title}>Главное в вашем разборе</Text>{report.summary.map((p,n)=><Text selectable key={n} style={s.body}>{p}</Text>)}{report.highlights?.map(group=><View key={group.id} style={{gap:8}}><Text style={s.label}>{group.title}</Text>{group.items.map((item,n)=><View key={n} style={{gap:2}}><Text selectable style={s.body}>• {item.text}</Text><Text selectable style={s.small}>Основание в расчёте: {item.basis}</Text></View>)}</View>)}{!archived&&report.narration?.some(i=>i.id==='full-report-summary')&&<NarrationClip id="full-report-summary"/>}</Card>
  {order.report_status==='preparing'&&(order.analysis_status==='review'?<Card tinted><Text accessibilityLiveRegion="polite" style={s.body}>Подготовка смыслового разбора остановилась. Повторите её кнопкой ниже; новая оплата не нужна.</Text></Card>:<Card tinted><ReportPreparing birthDate={report.birth_date} message="Смысловой разбор по вашим расчётам готовится в локальной нейросети. Числа уже доступны ниже."/></Card>)}
  {!archived&&<FullReportVideo orderId={order.order_id} birthDate={report.birth_date}/>}
  <SavedReportExport document={()=>fullReportHtml(order)}/>
  <SavedReportExport document={()=>fullReportSchemesHtml(order)} title="Краткий отчёт: схемы и графики" note="Только схемы, диаграммы и графики — без пояснений и расшифровок."/>
  <Text style={s.small}>Откройте раздел, чтобы увидеть результаты, схему и персональную аудиоглаву. Новые записи готовятся автоматически; готовые появляются здесь.</Text>
  <Button secondary title={opened.length===report.sections.length?'Свернуть все разделы':'Показать весь отчёт'} onPress={()=>setOpened(opened.length===report.sections.length?[]:report.sections.map(i=>i.id))}/>
  {report.sections.map(section=><Card key={section.id}>
   <Button secondary title={`${opened.includes(section.id)?'−':'+'} ${section.title}`} onPress={()=>toggle(section.id)}/>
   {opened.includes(section.id)&&<View style={{gap:15}}>
    {section.paragraphs.map((p,n)=><Text selectable key={n} style={s.body}>{p}</Text>)}
    <ReportDiagram report={report} section={section}/>
    {section.values.map((v,n)=><View key={n} style={{gap:5,paddingBottom:12,borderBottomWidth:1,borderColor:'#DDE5EE'}}><View style={s.row}><Text style={[s.label,{flex:1}]}>{v.label}</Text><Text style={s.title}>{v.value??'—'}</Text></View>{positionParagraphs(section,n).map((p,i)=><Text selectable key={i} style={s.body}>{p}</Text>)}</View>)}
    {!archived&&report.narration?.filter(i=>i.id===`full-report-${section.id}`||i.id.startsWith(`full-report-${section.id}-`)).map(i=><NarrationClip key={i.id} id={i.id}/>)}
    {(section.method||section.steps.length>0)&&<><Button secondary title={methods.includes(section.id)?'Скрыть расчёт':'Как рассчитано'} onPress={()=>setMethods(v=>v.includes(section.id)?v.filter(i=>i!==section.id):[...v,section.id])}/>{methods.includes(section.id)&&<View style={{gap:8}}><Text selectable style={s.small}>{section.method}</Text>{section.steps.map((v,n)=><Text selectable key={n} style={s.small}>{v}</Text>)}</View>}</>}
   </View>}
  </Card>)}
  {report.excluded?.length>0&&<View style={{gap:10}}><Text style={s.title}>Для чего нужны дополнительные данные</Text>{report.excluded.map((i,n)=><Text key={n} style={s.small}>{i.title}. {i.reason}</Text>)}</View>}
  {!!report.notice&&<Text style={s.small}>{report.notice}</Text>}
 </View>;
 return archived?body:<NarrationProvider path={`/full-reports/${order.order_id}/narration`}>{body}</NarrationProvider>;
}
