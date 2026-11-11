import {useState} from 'react';
import {Pressable,Text,View} from 'react-native';
import {Button,Card,Field,Notice,s} from '../ui';
import {parseSkillList,type Employee,type Group,type GroupInput} from '../../lib/business';
import {colors} from '../../lib/theme';
export function TeamEditor({group,employees,busy,onSave,onCancel}:{group:Group|null;employees:Employee[];busy:boolean;onSave:(group:GroupInput)=>void;onCancel:()=>void}){
 const [name,setName]=useState(group?.name||''),[task,setTask]=useState(group?.task||''),[skills,setSkills]=useState(group?.required_skills.join('; ')||''),[hours,setHours]=useState(group?.target_hours==null?'':String(group.target_hours)),[members,setMembers]=useState<string[]>(group?.member_ids||[]),[query,setQuery]=useState(''),[page,setPage]=useState(0),[error,setError]=useState('');
 const filtered=employees.filter(e=>`${e.name} ${e.surname} ${e.department} ${e.role} ${e.skills.join(' ')}`.toLocaleLowerCase('ru').includes(query.trim().toLocaleLowerCase('ru')));
 const visible=filtered.slice(page*15,page*15+15);
 const toggle=(id:string)=>{if(members.includes(id))setMembers(members.filter(x=>x!==id));else if(members.length<20)setMembers([...members,id]);else setError('В одной команде может быть до 20 участников.');};
 const submit=()=>{try{if(!name.trim()||!task.trim())throw Error('Укажите название команды и конкретную задачу.');const target=hours.trim()===''?null:Number(hours.replace(',','.'));if(target!==null&&(!Number.isFinite(target)||target<0||target>3360))throw Error('Укажите нагрузку от 0 до 3360 часов в неделю.');const required_skills=parseSkillList(skills);if(required_skills.length>30)throw Error('Укажите не более 30 навыков.');setError('');onSave({name:name.trim(),task:task.trim(),required_skills,target_hours:target,member_ids:members});}catch(e){setError(e instanceof Error?e.message:'Проверьте параметры задачи.');}};
 return <Card><Text accessibilityRole="header" style={s.title}>{group?'Настроить команду':'Команда под задачу'}</Text>
 <Field label="Название команды" placeholder="Например, запуск нового продукта" value={name} onChangeText={setName} maxLength={120} editable={!busy}/>
 <Field label="Задача и ожидаемый результат" placeholder="Что нужно сделать и какой результат проверить" value={task} onChangeText={setTask} maxLength={2000} multiline editable={!busy}/>
 <Field label="Нужные навыки · через точку с запятой" placeholder="Продажи; Аналитика; Дизайн" value={skills} onChangeText={setSkills} maxLength={2450} multiline editable={!busy}/>
 <Text style={s.small}>Используйте такие же названия навыков, как в карточках: «Excel» и «Таблицы» считаются разными навыками. Отсутствие записи не означает отсутствие способности.</Text>
 <Field label="Плановая нагрузка команды · часов в неделю" placeholder="Не указана" value={hours} onChangeText={setHours} maxLength={8} keyboardType="decimal-pad" editable={!busy}/>
 <Text style={s.label}>Участники · {members.length} из 20</Text><Text style={s.small}>Выберите людей для совместной задачи. Отчёт покажет покрытие навыков и вопросы, которые стоит обсудить перед началом.</Text>
 <Field label="Найти участника" value={query} onChangeText={v=>{setQuery(v);setPage(0);}} placeholder="Имя, отдел или навык" maxLength={120}/>
 {visible.map(e=>{const checked=members.includes(e.id);return <Pressable key={e.id} accessibilityRole="checkbox" aria-checked={checked} accessibilityLabel={`${e.name} ${e.surname}`} accessibilityState={{checked,disabled:busy}} disabled={busy} onPress={()=>toggle(e.id)} style={{padding:13,borderRadius:13,borderWidth:1,borderColor:checked?colors.navy:colors.line,backgroundColor:checked?colors.blue:colors.surface,gap:5}}><Text style={s.label}>{checked?'✓ ':''}{e.name} {e.surname}</Text><Text style={s.small}>{e.role||'Роль не указана'}{e.department?` · ${e.department}`:''}</Text><Text style={s.body}>{e.skills.length?e.skills.join(' · '):'Навыки пока не заполнены'}</Text></Pressable>;})}
 {!filtered.length&&<Text style={s.body}>По этому запросу никого не найдено.</Text>}
 {filtered.length>15&&<View style={{gap:8}}><Text style={s.small}>{page*15+1}–{Math.min((page+1)*15,filtered.length)} из {filtered.length}</Text>{page>0&&<Button secondary title="Предыдущие участники" onPress={()=>setPage(page-1)}/>} {(page+1)*15<filtered.length&&<Button secondary title="Следующие участники" onPress={()=>setPage(page+1)}/>}</View>}
 {!!error&&<Notice message={error}/>}<Button title="Сохранить команду" busy={busy} onPress={submit}/><Button secondary title="Отмена" disabled={busy} onPress={onCancel}/>
 </Card>;
}
