import {Text,View} from 'react-native';
import {Button,Card,s} from '../ui';
import {type EmployeeAnalysis as Analysis} from '../../lib/business';
import {colors} from '../../lib/theme';

export function EmployeeAnalysis({analysis,busy,onEdit,onExport,onClose}:{analysis:Analysis;busy:boolean;onEdit:()=>void;onExport:()=>void;onClose:()=>void}){
 const {employee,numerom}=analysis;
 return <View style={{gap:18}}>
  <Card tinted><Text style={s.eyebrow}>ПЕРСОНАЛЬНЫЙ РАЗБОР NUMEROM</Text><Text accessibilityRole="header" style={s.heading}>{employee.name} {employee.surname}</Text><Text style={s.body}>{employee.birth_date||'Дата рождения не указана'}</Text><Text style={s.body}>{employee.role||'Роль не указана'}{employee.department?` · ${employee.department}`:''}</Text>
   <Text style={s.body}>Показатели рассчитаны по сохранённым имени, фамилии и дате рождения. Расчёт, сильные стороны и практики войдут в отчёт.</Text>
   <Button secondary title="Дополнить карточку" disabled={busy} onPress={onEdit}/>
  </Card>
  <Card><Text accessibilityRole="header" style={s.title}>Ключевые показатели NumerOM</Text><Text style={s.small}>{numerom.note}</Text>
   <View style={{flexDirection:'row',flexWrap:'wrap',gap:12}}>{numerom.indicators.map(n=><View key={n.key} style={{flexGrow:1,flexBasis:240,minWidth:0,gap:6,padding:16,borderRadius:16,backgroundColor:colors.blue}}>
    <Text style={s.label}>{n.title}</Text><Text selectable style={[s.heading,{fontSize:36}]}>{n.value}</Text><Text style={s.body}>{n.context}</Text>
    {n.master&&<Text style={s.small}>Мастер-число сохраняется · базовая цифра {n.base}</Text>}
    <Text selectable style={s.small}>{n.formula}</Text>
   </View>)}</View>
   {numerom.indicators.some(n=>n.key==='name')&&<Text style={s.small}>{numerom.nameMethod}</Text>}
   {numerom.notes.map((note,i)=><Text key={i} style={s.body}>{note}</Text>)}
  </Card>
  <Card><Text accessibilityRole="header" style={s.title}>Сильные стороны в символике чисел</Text>
   {numerom.themes.map(theme=><View key={theme.digit} style={{gap:8,paddingVertical:12,borderTopWidth:1,borderColor:colors.line}}>
    <Text style={s.title}>{theme.digit} · {theme.planet} · {theme.title}</Text><Text style={s.small}>{theme.indicators.join(' · ')}</Text>
    <Text selectable style={s.label}>{theme.summary}</Text><Text selectable style={s.body}>{theme.strength}</Text>
    <Text style={s.label}>Вопрос к своему опыту</Text><Text selectable style={s.body}>{theme.question}</Text>
    <Text style={s.label}>Практика</Text><Text selectable style={s.body}>{theme.practice}</Text>
    <Text style={s.small}>Источник: {theme.sources.join('; ')}</Text>
   </View>)}
   {!numerom.themes.length&&<Text style={s.body}>Добавьте дату рождения или имя в поддерживаемом алфавите.</Text>}
  </Card>
  <Card><Text accessibilityRole="header" style={s.title}>Рабочие сведения</Text><Text style={s.label}>{analysis.status==='needs_evidence'?'Недостаточно рабочих данных':'Есть данные для обсуждения'}</Text><Text style={s.body}>Навыки и опыт из карточки помогают сопоставить требования задач с рабочими примерами сотрудника.</Text></Card>
  <Card><Text accessibilityRole="header" style={s.title}>Навыки для проверки</Text><Text style={s.small}>Указаны в карточке. Уровень владения ещё нужно подтвердить.</Text>
   {analysis.skills.length?<View style={{flexDirection:'row',flexWrap:'wrap',gap:8}}>{analysis.skills.map(skill=><View key={skill} style={{maxWidth:'100%',paddingHorizontal:12,paddingVertical:8,borderRadius:12,backgroundColor:colors.blue}}><Text selectable style={s.label}>{skill}</Text></View>)}</View>:<Text style={s.body}>Навыки пока не указаны.</Text>}
   <Text style={s.label}>Опыт и примеры работ</Text><Text selectable style={s.body}>{analysis.experience||'Примеры выполненных работ пока не добавлены.'}</Text>
   <Text style={s.label}>Профессиональные интересы</Text><Text selectable style={s.body}>{analysis.interests.join(' · ')||'Пока не указаны.'}</Text>
   <Text style={s.label}>Заявленная доступность</Text><Text style={s.body}>{analysis.hours_per_week==null?'Не указана.':`${analysis.hours_per_week} ч/нед.`}</Text><Text style={s.small}>Уточните фактическую загрузку и согласуйте участие в задаче с сотрудником.</Text>
  </Card>
  <Card><Text accessibilityRole="header" style={s.title}>Где есть совпадения с задачами</Text><Text style={s.small}>Сопоставлены названия навыков из карточки и требований сохранённых команд. Это темы для проверки опыта.</Text>
   {analysis.task_matches.length?analysis.task_matches.map(task=><View key={task.id} style={{gap:8,paddingVertical:12,borderTopWidth:1,borderColor:colors.line}}>
    <Text style={s.title}>{task.name}</Text><Text selectable style={s.body}>{task.task}</Text>
    <Text style={s.label}>Совпали в карточке</Text><Text selectable style={s.body}>{task.matched_skills.join(' · ')||'Нет совпадений.'}</Text>
    {!!task.unconfirmed_skills.length&&<><Text style={s.label}>Требования без сведений в карточке</Text><Text selectable style={s.body}>{task.unconfirmed_skills.join(' · ')}</Text></>}
    <Text style={s.small}>{task.is_member?'Сотрудник уже включён в эту команду.':'Сотрудник не включён в эту команду.'}</Text>
   </View>):<Text style={s.body}>Совпадений пока нет. Уточните навыки сотрудника и требования задач; отсутствие совпадений не означает отсутствия способности.</Text>}
  </Card>
  {!!analysis.missing_data.length&&<Card><Text accessibilityRole="header" style={s.title}>Что ещё нужно уточнить</Text>{analysis.missing_data.map((item,i)=><Text key={i} selectable style={s.body}>• {item}</Text>)}</Card>}
  <Card><Text accessibilityRole="header" style={s.title}>Как проверить на практике</Text>{analysis.next_steps.map((step,i)=><Text key={i} selectable style={s.body}>{i+1}. {step}</Text>)}<Text style={s.small}>{analysis.basis}</Text></Card>
  <Button title="Сохранить анализ / PDF" busy={busy} onPress={onExport}/><Button secondary title="К сотрудникам" onPress={onClose}/>
 </View>;
}
