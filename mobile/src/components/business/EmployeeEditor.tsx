import {useState} from 'react';
import {Text,View} from 'react-native';
import {Button,Card,Field,Notice,s} from '../ui';
import {employeeInput,type EmployeeInput,type Employee} from '../../lib/business';

export function EmployeeEditor({employee,busy,onSave,onCalculate,onCancel,onRemove}:{employee:Employee|null;busy:boolean;onSave:(data:EmployeeInput)=>void;onCalculate?:(data:EmployeeInput)=>void;onCancel:()=>void;onRemove?:()=>void}){
 const [initial]=useState({name:employee?.name||'',surname:employee?.surname||'',birth_date:employee?.birth_date||'',department:employee?.department||'',role:employee?.role||'',skills:employee?.skills.join('; ')||'',experience:employee?.experience||'',interests:employee?.interests.join('; ')||'',hours_per_week:employee?.hours_per_week==null?'':String(employee.hours_per_week)});
 const [form,setForm]=useState(initial);
 const [error,setError]=useState(''),[remove,setRemove]=useState(false);
 const change=(key:keyof typeof form,value:string)=>setForm(old=>({...old,[key]:value}));
 const changed=(Object.keys(form) as (keyof typeof form)[]).some(key=>form[key]!==initial[key]);
 const submit=(action:(data:EmployeeInput)=>void)=>{try{const data=employeeInput(form);setError('');action(data);}catch(e){setError(e instanceof Error?e.message:'Проверьте поля карточки.');}};
 return <Card><Text accessibilityRole="header" style={s.title}>{employee?'Карточка сотрудника':'Новый сотрудник'}</Text>
 <Field label="Имя" value={form.name} maxLength={80} editable={!busy} onChangeText={v=>change('name',v)}/>
 <Field label="Фамилия" value={form.surname} maxLength={80} editable={!busy} onChangeText={v=>change('surname',v)}/>
 <Field label="Дата рождения · необязательно" placeholder="ДД.ММ.ГГГГ" value={form.birth_date} maxLength={10} editable={!busy} onChangeText={v=>change('birth_date',v)}/>
 <Text style={s.small}>Дата нужна для чисел души, ума и судьбы. Число имени рассчитывается по русскому или латинскому алфавиту. Все показатели включаются в отчёт NumerOM.</Text>
 <Field label="Подразделение" value={form.department} maxLength={120} editable={!busy} onChangeText={v=>change('department',v)}/>
 <Field label="Текущая роль" value={form.role} maxLength={120} editable={!busy} onChangeText={v=>change('role',v)}/>
 <Field label="Рабочие навыки · через точку с запятой" placeholder="Продажи; Excel; Закупки" value={form.skills} maxLength={2450} multiline editable={!busy} onChangeText={v=>change('skills',v)}/>
 <Field label="Опыт и примеры выполненных работ" placeholder="Какие задачи выполнял сотрудник, какие есть подтверждения" value={form.experience} maxLength={2000} multiline editable={!busy} onChangeText={v=>change('experience',v)}/>
 <Field label="Профессиональные интересы · через точку с запятой" placeholder="Что сотрудник хочет развивать" value={form.interests} maxLength={1630} multiline editable={!busy} onChangeText={v=>change('interests',v)}/>
 <Field label="Доступно для задачи · часов в неделю" placeholder="Неизвестно" value={form.hours_per_week} maxLength={6} keyboardType="decimal-pad" editable={!busy} onChangeText={v=>change('hours_per_week',v)}/>
 <Text style={s.small}>Записывайте сведения со слов сотрудника и из его рабочих результатов. Пустое поле означает, что данных пока нет.</Text>
 {!!error&&<Notice message={error}/>}
 {employee&&onCalculate&&<><Text style={s.small}>Анализ использует сохранённую карточку. Изменения будут сохранены перед расчётом.</Text><Button title={changed?'Сохранить и рассчитать\nанализ':'Рассчитать анализ'} busy={busy} onPress={()=>submit(onCalculate)}/></>}
 <Button secondary={!!onCalculate} title="Сохранить карточку" busy={busy} onPress={()=>submit(onSave)}/><Button secondary title="Отмена" disabled={busy} onPress={onCancel}/>
 {onRemove&&!remove&&<Button secondary title="Убрать сотрудника из списка" disabled={busy} onPress={()=>setRemove(true)}/>}
 {onRemove&&remove&&<View style={{gap:10}}><Text style={s.body}>Карточка и участие в сохранённых командах будут удалены из этого рабочего пространства.</Text><Button title="Подтвердить удаление" disabled={busy} onPress={onRemove}/><Button secondary title="Оставить сотрудника" disabled={busy} onPress={()=>setRemove(false)}/></View>}
 </Card>;
}
