import {useState} from 'react';
import {Text,View} from 'react-native';
import {Button,Card,s} from '../ui';
import {type GroupReport} from '../../lib/business';
import {colors} from '../../lib/theme';
export function TeamReport({report,busy,onExport,onClose}:{report:GroupReport;busy:boolean;onExport:()=>void;onClose:()=>void}){
 const [expanded,setExpanded]=useState<string|null>(null);
 const names=(ids:string[])=>ids.map(id=>{const e=report.members.find(x=>x.id===id);return e?`${e.name} ${e.surname}`:'Участник';}).join(', ');
 const covered=report.coverage.filter(row=>row.employee_ids.length>0).length;
 return <View style={{gap:18}}><Card><Text style={s.eyebrow}>ОБЗОР КОМАНДЫ</Text><Text accessibilityRole="header" style={s.heading}>{report.name}</Text><Text selectable style={s.body}>{report.task}</Text><Text style={s.label}>Участников: {report.member_count}</Text>
 <Text style={s.title}>Покрытие задачи</Text><Text style={s.body}>{report.coverage.length?`${covered} из ${report.coverage.length} нужных навыков указаны у выбранных участников.`:'Добавьте необходимые навыки в настройках команды, чтобы увидеть покрытие задачи.'}</Text>
 {report.coverage.length>0&&<View accessibilityLabel={`Покрыто ${covered} из ${report.coverage.length} навыков`} style={{height:10,borderRadius:5,backgroundColor:colors.line,overflow:'hidden'}}><View style={{height:10,width:`${covered/report.coverage.length*100}%`,backgroundColor:colors.navy}}/></View>}
 {report.coverage.map(row=><View key={row.skill} style={{gap:4,paddingVertical:8,borderBottomWidth:1,borderColor:colors.line}}><Text style={s.label}>{row.employee_ids.length?'✓':'○'} {row.skill}</Text><Text selectable style={s.body}>{row.employee_ids.length?names(row.employee_ids):'Нет подтверждённых сведений в карточках команды'}</Text></View>)}
 <Text style={s.small}>Совпадение названия навыка — повод проверить опыт на задаче. Это не оценка качества сотрудника и не решение о найме.</Text>
 </Card><Card><Text style={s.title}>Нагрузка и согласование</Text><Text style={s.body}>Указанная доступность: {report.available_hours==null?'нет данных':`${report.available_hours} ч/нед.`}{report.missing_hours_data.length?' · данные неполные':''}</Text><Text style={s.body}>Задаче нужно: {report.target_hours==null?'не указано':`${report.target_hours} ч/нед.`}</Text>
 {!!report.missing_hours_data.length&&<Text style={s.body}>Уточните доступность: {names(report.missing_hours_data)}.</Text>}<Text style={s.small}>Доступность относится к выбранной задаче. Согласуйте фактическую загрузку с участниками; часы в разных командах могут пересекаться.</Text>
 {report.next_steps.map((step,i)=><Text key={i} selectable style={s.body}>{i+1}. {step}</Text>)}
 </Card><Card><Text style={s.title}>Каждый участник</Text>{report.members.map(e=><View key={e.id} style={{gap:10}}><Button secondary title={`${e.name} ${e.surname}${expanded===e.id?' · свернуть':''}`} onPress={()=>setExpanded(expanded===e.id?null:e.id)}/>{expanded===e.id&&<View style={{gap:8}}><Text style={s.body}>Роль: {e.role||'не указана'}. Отдел: {e.department||'не указан'}.</Text><Text selectable style={s.body}>Навыки: {e.skills.join(', ')||'пока нет данных'}</Text><Text selectable style={s.body}>Опыт: {e.experience||'пока нет данных'}</Text><Text selectable style={s.body}>Интересы: {e.interests.join(', ')||'пока нет данных'}</Text><Text style={s.body}>Доступность: {e.hours_per_week==null?'не указана':`${e.hours_per_week} ч/нед.`}</Text></View>}</View>)}
 {!report.members.length&&<Text style={s.body}>Выберите участников в настройках команды.</Text>}
 </Card><Button title="Сохранить отчёт / PDF" busy={busy} onPress={onExport}/><Button secondary title="К списку команд" disabled={busy} onPress={onClose}/></View>;
}
