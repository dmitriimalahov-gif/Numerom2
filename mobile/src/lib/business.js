/** Business evidence contracts. Identity fields never determine roles or team suitability. */
const {employeeNumerom,employeeNumeromHtml}=require('./employeeNumerom');
const MAX_FILE = 5 * 1024 * 1024;
const fail = message => { throw new Error(message || 'Не удалось прочитать данные бизнеса. Обновите раздел.'); };
const record = value => value && typeof value === 'object' && !Array.isArray(value) ? value : fail();
const own = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
const controls = /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/;
function text(value, max, required = false, multiline = false) {
 if (typeof value !== 'string' || controls.test(value)) return fail();
 const canonical=value.normalize('NFC');
 const normalized = multiline ? canonical.trim() : canonical.trim().replace(/\s+/g, ' ');
 if (Array.from(normalized).length > max || required && !normalized) return fail();
 return normalized;
}
function identity(value) { return typeof value === 'string' && /^[A-Za-z0-9_-]{1,80}$/.test(value) ? value : fail(); }
function array(value, max) { return Array.isArray(value) && value.length <= max ? value : fail(); }
function unique(value) { return new Set(value).size === value.length ? value : fail(); }
// Unicode case folding matches the server's evidence labels, including ß/ss
// and final sigma, without incorrectly merging Turkish dotless i with i.
const caseFold = {"\u00b5":"\u03bc","\u00df":"ss","\u0149":"\u02bcn","\u017f":"s","\u01f0":"j\u030c","\u0345":"\u03b9","\u0390":"\u03b9\u0308\u0301","\u03b0":"\u03c5\u0308\u0301","\u03c2":"\u03c3","\u03d0":"\u03b2","\u03d1":"\u03b8","\u03d5":"\u03c6","\u03d6":"\u03c0","\u03f0":"\u03ba","\u03f1":"\u03c1","\u03f5":"\u03b5","\u0587":"\u0565\u0582","\u13a0":"\u13a0","\u13a1":"\u13a1","\u13a2":"\u13a2","\u13a3":"\u13a3","\u13a4":"\u13a4","\u13a5":"\u13a5","\u13a6":"\u13a6","\u13a7":"\u13a7","\u13a8":"\u13a8","\u13a9":"\u13a9","\u13aa":"\u13aa","\u13ab":"\u13ab","\u13ac":"\u13ac","\u13ad":"\u13ad","\u13ae":"\u13ae","\u13af":"\u13af","\u13b0":"\u13b0","\u13b1":"\u13b1","\u13b2":"\u13b2","\u13b3":"\u13b3","\u13b4":"\u13b4","\u13b5":"\u13b5","\u13b6":"\u13b6","\u13b7":"\u13b7","\u13b8":"\u13b8","\u13b9":"\u13b9","\u13ba":"\u13ba","\u13bb":"\u13bb","\u13bc":"\u13bc","\u13bd":"\u13bd","\u13be":"\u13be","\u13bf":"\u13bf","\u13c0":"\u13c0","\u13c1":"\u13c1","\u13c2":"\u13c2","\u13c3":"\u13c3","\u13c4":"\u13c4","\u13c5":"\u13c5","\u13c6":"\u13c6","\u13c7":"\u13c7","\u13c8":"\u13c8","\u13c9":"\u13c9","\u13ca":"\u13ca","\u13cb":"\u13cb","\u13cc":"\u13cc","\u13cd":"\u13cd","\u13ce":"\u13ce","\u13cf":"\u13cf","\u13d0":"\u13d0","\u13d1":"\u13d1","\u13d2":"\u13d2","\u13d3":"\u13d3","\u13d4":"\u13d4","\u13d5":"\u13d5","\u13d6":"\u13d6","\u13d7":"\u13d7","\u13d8":"\u13d8","\u13d9":"\u13d9","\u13da":"\u13da","\u13db":"\u13db","\u13dc":"\u13dc","\u13dd":"\u13dd","\u13de":"\u13de","\u13df":"\u13df","\u13e0":"\u13e0","\u13e1":"\u13e1","\u13e2":"\u13e2","\u13e3":"\u13e3","\u13e4":"\u13e4","\u13e5":"\u13e5","\u13e6":"\u13e6","\u13e7":"\u13e7","\u13e8":"\u13e8","\u13e9":"\u13e9","\u13ea":"\u13ea","\u13eb":"\u13eb","\u13ec":"\u13ec","\u13ed":"\u13ed","\u13ee":"\u13ee","\u13ef":"\u13ef","\u13f0":"\u13f0","\u13f1":"\u13f1","\u13f2":"\u13f2","\u13f3":"\u13f3","\u13f4":"\u13f4","\u13f5":"\u13f5","\u13f8":"\u13f0","\u13f9":"\u13f1","\u13fa":"\u13f2","\u13fb":"\u13f3","\u13fc":"\u13f4","\u13fd":"\u13f5","\u1c80":"\u0432","\u1c81":"\u0434","\u1c82":"\u043e","\u1c83":"\u0441","\u1c84":"\u0442","\u1c85":"\u0442","\u1c86":"\u044a","\u1c87":"\u0463","\u1c88":"\ua64b","\u1e96":"h\u0331","\u1e97":"t\u0308","\u1e98":"w\u030a","\u1e99":"y\u030a","\u1e9a":"a\u02be","\u1e9b":"\u1e61","\u1e9e":"ss","\u1f50":"\u03c5\u0313","\u1f52":"\u03c5\u0313\u0300","\u1f54":"\u03c5\u0313\u0301","\u1f56":"\u03c5\u0313\u0342","\u1f80":"\u1f00\u03b9","\u1f81":"\u1f01\u03b9","\u1f82":"\u1f02\u03b9","\u1f83":"\u1f03\u03b9","\u1f84":"\u1f04\u03b9","\u1f85":"\u1f05\u03b9","\u1f86":"\u1f06\u03b9","\u1f87":"\u1f07\u03b9","\u1f88":"\u1f00\u03b9","\u1f89":"\u1f01\u03b9","\u1f8a":"\u1f02\u03b9","\u1f8b":"\u1f03\u03b9","\u1f8c":"\u1f04\u03b9","\u1f8d":"\u1f05\u03b9","\u1f8e":"\u1f06\u03b9","\u1f8f":"\u1f07\u03b9","\u1f90":"\u1f20\u03b9","\u1f91":"\u1f21\u03b9","\u1f92":"\u1f22\u03b9","\u1f93":"\u1f23\u03b9","\u1f94":"\u1f24\u03b9","\u1f95":"\u1f25\u03b9","\u1f96":"\u1f26\u03b9","\u1f97":"\u1f27\u03b9","\u1f98":"\u1f20\u03b9","\u1f99":"\u1f21\u03b9","\u1f9a":"\u1f22\u03b9","\u1f9b":"\u1f23\u03b9","\u1f9c":"\u1f24\u03b9","\u1f9d":"\u1f25\u03b9","\u1f9e":"\u1f26\u03b9","\u1f9f":"\u1f27\u03b9","\u1fa0":"\u1f60\u03b9","\u1fa1":"\u1f61\u03b9","\u1fa2":"\u1f62\u03b9","\u1fa3":"\u1f63\u03b9","\u1fa4":"\u1f64\u03b9","\u1fa5":"\u1f65\u03b9","\u1fa6":"\u1f66\u03b9","\u1fa7":"\u1f67\u03b9","\u1fa8":"\u1f60\u03b9","\u1fa9":"\u1f61\u03b9","\u1faa":"\u1f62\u03b9","\u1fab":"\u1f63\u03b9","\u1fac":"\u1f64\u03b9","\u1fad":"\u1f65\u03b9","\u1fae":"\u1f66\u03b9","\u1faf":"\u1f67\u03b9","\u1fb2":"\u1f70\u03b9","\u1fb3":"\u03b1\u03b9","\u1fb4":"\u03ac\u03b9","\u1fb6":"\u03b1\u0342","\u1fb7":"\u03b1\u0342\u03b9","\u1fbc":"\u03b1\u03b9","\u1fbe":"\u03b9","\u1fc2":"\u1f74\u03b9","\u1fc3":"\u03b7\u03b9","\u1fc4":"\u03ae\u03b9","\u1fc6":"\u03b7\u0342","\u1fc7":"\u03b7\u0342\u03b9","\u1fcc":"\u03b7\u03b9","\u1fd2":"\u03b9\u0308\u0300","\u1fd3":"\u03b9\u0308\u0301","\u1fd6":"\u03b9\u0342","\u1fd7":"\u03b9\u0308\u0342","\u1fe2":"\u03c5\u0308\u0300","\u1fe3":"\u03c5\u0308\u0301","\u1fe4":"\u03c1\u0313","\u1fe6":"\u03c5\u0342","\u1fe7":"\u03c5\u0308\u0342","\u1ff2":"\u1f7c\u03b9","\u1ff3":"\u03c9\u03b9","\u1ff4":"\u03ce\u03b9","\u1ff6":"\u03c9\u0342","\u1ff7":"\u03c9\u0342\u03b9","\u1ffc":"\u03c9\u03b9","\uab70":"\u13a0","\uab71":"\u13a1","\uab72":"\u13a2","\uab73":"\u13a3","\uab74":"\u13a4","\uab75":"\u13a5","\uab76":"\u13a6","\uab77":"\u13a7","\uab78":"\u13a8","\uab79":"\u13a9","\uab7a":"\u13aa","\uab7b":"\u13ab","\uab7c":"\u13ac","\uab7d":"\u13ad","\uab7e":"\u13ae","\uab7f":"\u13af","\uab80":"\u13b0","\uab81":"\u13b1","\uab82":"\u13b2","\uab83":"\u13b3","\uab84":"\u13b4","\uab85":"\u13b5","\uab86":"\u13b6","\uab87":"\u13b7","\uab88":"\u13b8","\uab89":"\u13b9","\uab8a":"\u13ba","\uab8b":"\u13bb","\uab8c":"\u13bc","\uab8d":"\u13bd","\uab8e":"\u13be","\uab8f":"\u13bf","\uab90":"\u13c0","\uab91":"\u13c1","\uab92":"\u13c2","\uab93":"\u13c3","\uab94":"\u13c4","\uab95":"\u13c5","\uab96":"\u13c6","\uab97":"\u13c7","\uab98":"\u13c8","\uab99":"\u13c9","\uab9a":"\u13ca","\uab9b":"\u13cb","\uab9c":"\u13cc","\uab9d":"\u13cd","\uab9e":"\u13ce","\uab9f":"\u13cf","\uaba0":"\u13d0","\uaba1":"\u13d1","\uaba2":"\u13d2","\uaba3":"\u13d3","\uaba4":"\u13d4","\uaba5":"\u13d5","\uaba6":"\u13d6","\uaba7":"\u13d7","\uaba8":"\u13d8","\uaba9":"\u13d9","\uabaa":"\u13da","\uabab":"\u13db","\uabac":"\u13dc","\uabad":"\u13dd","\uabae":"\u13de","\uabaf":"\u13df","\uabb0":"\u13e0","\uabb1":"\u13e1","\uabb2":"\u13e2","\uabb3":"\u13e3","\uabb4":"\u13e4","\uabb5":"\u13e5","\uabb6":"\u13e6","\uabb7":"\u13e7","\uabb8":"\u13e8","\uabb9":"\u13e9","\uabba":"\u13ea","\uabbb":"\u13eb","\uabbc":"\u13ec","\uabbd":"\u13ed","\uabbe":"\u13ee","\uabbf":"\u13ef","\ufb00":"ff","\ufb01":"fi","\ufb02":"fl","\ufb03":"ffi","\ufb04":"ffl","\ufb05":"st","\ufb06":"st","\ufb13":"\u0574\u0576","\ufb14":"\u0574\u0565","\ufb15":"\u0574\u056b","\ufb16":"\u057e\u0576","\ufb17":"\u0574\u056d"};
const key = value => Array.from(value.normalize('NFKC'), char => caseFold[char] ?? char.toLowerCase()).join('').trim().replace(/\s+/g,' ');
function labels(value, max) { const result = array(value, max).map(item => text(item, 80, true)); unique(result.map(key)); return result; }
function hours(value, max) { return value === null || typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= max ? value : fail(); }
function birthDate(value) {
 if (value === null || value === '') return null;
 if (typeof value !== 'string') return fail('Дата рождения должна быть в формате ДД.ММ.ГГГГ.');
 const source = value.trim(), ru = /^(\d{2})\.(\d{2})\.(\d{4})$/.exec(source), iso = /^(\d{4})-(\d{2})-(\d{2})$/.exec(source);
 if (!ru && !iso) return fail('Дата рождения должна быть в формате ДД.ММ.ГГГГ.');
 const day = Number(ru ? ru[1] : iso[3]), month = Number(ru ? ru[2] : iso[2]), year = Number(ru ? ru[3] : iso[1]);
 const date = new Date(Date.UTC(year, month - 1, day)), today = new Date();
 if (year < 1900 || date.getUTCFullYear() !== year || date.getUTCMonth() !== month - 1 || date.getUTCDate() !== day || date.getTime() > Date.UTC(today.getFullYear(), today.getMonth(), today.getDate())) return fail('Проверьте дату рождения: от 1900 года до сегодняшнего дня.');
 return `${String(day).padStart(2, '0')}.${String(month).padStart(2, '0')}.${year}`;
}
function employee(value, withId = false) {
 const row = record(value);
 const result = { name:text(row.name,80,true), surname:text(row.surname,80,true), birth_date:birthDate(row.birth_date), department:text(row.department,120), role:text(row.role,120), skills:labels(row.skills,30), experience:text(row.experience,2000,false,true), interests:labels(row.interests,20), hours_per_week:hours(row.hours_per_week,168) };
 if (withId) result.id = identity(row.id);
 return result;
}
function group(value) {
 const row = record(value);
 return {id:identity(row.id),name:text(row.name,120,true),task:text(row.task,2000,true,true),required_skills:labels(row.required_skills,30),target_hours:hours(row.target_hours,3360),member_ids:unique(array(row.member_ids,20).map(identity))};
}
function timestamp(value) { const result = text(value,64,true); if (!/^\d{4}-\d{2}-\d{2}T/.test(result) || !Number.isFinite(Date.parse(result))) return fail(); return result; }
function businessWorkspace(value) {
 const outer = record(value), row = record(own(outer,'workspace') ? outer.workspace : outer);
 if (!Number.isSafeInteger(row.revision) || row.revision < 0) return fail();
 const employees = array(row.employees,250).map(item=>employee(item,true)), groups = array(row.groups,50).map(group);
 const employeeIds = new Set(unique(employees.map(item=>item.id))); unique(groups.map(item=>item.id));
 if (groups.some(item=>item.member_ids.some(id=>!employeeIds.has(id)))) return fail();
 return {id:identity(row.id),company_name:text(row.company_name,160,true),revision:row.revision,employees,groups,created_at:timestamp(row.created_at),updated_at:timestamp(row.updated_at)};
}
function businessEnvelope(value) {
 const row=record(value), pack=record(row.package);
 if (pack.id!=='business-250'||pack.max_employees!==250||pack.mode!=='pilot'||pack.price!==0||!own(row,'workspace')) return fail();
 return {package:{id:'business-250',title:text(pack.title,120,true),max_employees:250,mode:'pilot',price:0},workspace:row.workspace===null?null:businessWorkspace(row.workspace)};
}
function issue(value) {
 const row=record(value);
 if (!Number.isSafeInteger(row.row)||row.row<0||row.row>1000000) return fail();
 return {row:row.row,field:text(row.field,120),message:text(row.message,2000,true)};
}
function businessPreview(value) {
 const row=record(value);
 if (typeof row.valid!=='boolean'||!Number.isSafeInteger(row.row_count)||row.row_count<0||row.row_count>1000) return fail();
 const result={employees:array(row.employees,250).map(item=>employee(item)),issues:array(row.issues,3000).map(issue),warnings:array(row.warnings,3000).map(issue),row_count:row.row_count,valid:row.valid};
 if (result.employees.length>result.row_count||result.valid&&(result.issues.length>0||result.row_count!==result.employees.length||result.row_count<1||result.row_count>250)) return fail();
 return result;
}
function businessReport(value) {
 const outer=record(value),row=record(own(outer,'report')?outer.report:outer);
 const members=array(row.members,20).map(item=>employee(item,true)), ids=new Set(unique(members.map(item=>item.id)));
 if (!Number.isSafeInteger(row.member_count)||row.member_count!==members.length) return fail();
 const coverage=array(row.coverage,30).map(value=>{const item=record(value);return {skill:text(item.skill,80,true),employee_ids:unique(array(item.employee_ids,20).map(identity))};});
 unique(coverage.map(item=>key(item.skill)));
 if(coverage.some(item=>item.employee_ids.some(id=>!ids.has(id)))) return fail();
 const missing_skills=labels(row.missing_skills,30),missing_hours_data=unique(array(row.missing_hours_data,20).map(identity));
 const unknownHours=members.filter(member=>member.hours_per_week===null).map(member=>member.id);
 if(missing_hours_data.length!==unknownHours.length||missing_hours_data.some(id=>!unknownHours.includes(id))) return fail();
 if(missing_skills.length!==coverage.filter(item=>!item.employee_ids.length).length||missing_skills.some(skill=>!coverage.some(item=>key(item.skill)===key(skill)&&!item.employee_ids.length))) return fail();
 const available_hours=hours(row.available_hours,3360), expectedHours=members.reduce((sum,member)=>sum+(member.hours_per_week??0),0);
 if(unknownHours.length?available_hours!==null:available_hours===null||Math.abs(available_hours-expectedHours)>0.000001) return fail();
 return {name:text(row.name,120,true),task:text(row.task,2000,true,true),member_count:row.member_count,coverage,missing_skills,available_hours,target_hours:hours(row.target_hours,3360),missing_hours_data,next_steps:array(row.next_steps,8).map(item=>text(item,3000,true,true)),members};
}
function parseSkillList(value) {
 if (typeof value!=='string'||value.length>5000||controls.test(value)) return fail('Укажите навыки через точку с запятой.');
 const output=[],seen=new Set();
 for(const item of value.split(/[;\n]+/)){const cleaned=text(item,80);if(cleaned&&!seen.has(key(cleaned))){seen.add(key(cleaned));output.push(cleaned);}}
 if(output.length>30) return fail('Добавьте не более 30 навыков.');
 return output;
}
function employeeInput(value) {
 const row=record(value), hoursValue=row.hours_per_week;
 let parsedHours=hoursValue===undefined||hoursValue===null||typeof hoursValue==='string'&&!hoursValue.trim()?null:hoursValue;
 if(typeof parsedHours==='string'){
  if(!/^\d+(?:[.,]\d+)?$/.test(parsedHours.trim())) return fail('Доступность: число часов от 0 до 168 в неделю.');
  parsedHours=Number(parsedHours.trim().replace(',','.'));
 }
 const result=employee({...row,birth_date:row.birth_date??null,department:row.department??'',role:row.role??'',experience:row.experience??'',skills:typeof row.skills==='string'?parseSkillList(row.skills):row.skills??[],interests:typeof row.interests==='string'?parseSkillList(row.interests):row.interests??[],hours_per_week:parsedHours});
 return result;
}
/** Derive only from a normalized workspace; identity, titles and numerology are not evidence. */
function employeeAnalysis(workspace, member) {
 const declaredSkills=new Set(member.skills.map(key));
 const task_matches=[];
 for(const taskGroup of workspace.groups){
  const matched_skills=taskGroup.required_skills.filter(skill=>declaredSkills.has(key(skill)));
  if(!matched_skills.length)continue;
  task_matches.push({id:taskGroup.id,name:taskGroup.name,task:taskGroup.task,matched_skills,unconfirmed_skills:taskGroup.required_skills.filter(skill=>!declaredSkills.has(key(skill))),is_member:taskGroup.member_ids.includes(member.id)});
 }
 const missing_data=[];
 if(!member.skills.length)missing_data.push('Не указаны профессиональные навыки.');
 if(!member.experience)missing_data.push('Не описаны опыт и рабочие примеры.');
 if(!member.interests.length)missing_data.push('Не указаны профессиональные интересы.');
 if(member.hours_per_week===null)missing_data.push('Не указана доступность в часах в неделю.');
 const next_steps=member.skills.map(skill=>`Попросите показать пример работы, где использовался навык «${skill}», и уточните личный вклад, условия задачи и критерий результата.`);
 if(!member.skills.length)next_steps.push('Уточните у сотрудника, какие рабочие навыки он использует, и внесите их названия в карточку вместе с примерами.');
 next_steps.push(member.experience?'Обсудите указанный опыт: какую задачу решал сотрудник, что выполнил лично и какой результат можно проверить.':'Добавьте описание выполненной задачи: личный вклад, полученный результат и рабочий пример для обсуждения.');
 if(!member.interests.length)next_steps.push('Уточните, какие рабочие задачи интересны сотруднику, и сохраните его ответ.');
 else next_steps.push(`Обсудите заявленные интересы: ${member.interests.join('; ')}. Уточните, какие задачи сотрудник хотел бы попробовать; интерес сам по себе не подтверждает навык.`);
 next_steps.push(member.hours_per_week===null?'Уточните, сколько часов в неделю сотрудник может выделить на обсуждаемую задачу.':`Подтвердите заявленную доступность — ${member.hours_per_week} ч в неделю — с учётом других обязательств и сроков задачи.`);
 if(!workspace.groups.length)next_steps.push('Опишите задачу в сохранённой группе и укажите необходимые навыки, чтобы сопоставить требования с данными карточки.');
 else if(!task_matches.length)next_steps.push('Точных совпадений с требованиями сохранённых групп пока нет. Уточните названия навыков и требования задач вместе с сотрудником; отсутствие совпадений не означает отсутствие способности выполнить работу.');
 else if(task_matches.some(item=>item.unconfirmed_skills.length))next_steps.push('Обсудите требования, для которых в карточке нет сведений. Запросите рабочие примеры и обновите данные; отсутствие записи не означает отсутствие навыка.');
 return {
  employee:member,workspace_revision:workspace.revision,
  numerom:employeeNumerom(member),
  status:member.skills.length&&member.experience?'ready_for_discussion':'needs_evidence',
  skills:[...member.skills],experience:member.experience,interests:[...member.interests],hours_per_week:member.hours_per_week,
  task_matches,missing_data,next_steps,
  basis:'Основа рабочей части анализа — заявленные навыки, опыт, профессиональные интересы, доступность и требования сохранённых групп. Совпадение означает только одинаковое название навыка после нормализации записи; уровень владения не проверен. Готовность к обсуждению означает, что указаны навыки и опыт. Показатели по имени и дате рождения приведены в разделе NumerOM как символические трактовки для самопознания.',
 };
}
function businessEmployeeAnalysis(value, employeeId) {
 const workspace=businessWorkspace(value),member=workspace.employees.find(item=>item.id===employeeId);
 if(!member)return fail('Сотрудник не найден в этой рабочей области. Обновите список сотрудников.');
 return employeeAnalysis(workspace,member);
}
const escapeHtml = value => String(value).replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
function employeeAnalysisSectionHtml(analysis,{compact=false,includeNumerom=true}={}) {
 const e=escapeHtml,list=items=>`<ul>${items.map(item=>`<li>${e(item)}</li>`).join('')}</ul>`;
 const matches=analysis.task_matches.map(item=>`<section class="task-overlap"><h5>${e(item.name)}</h5><p>${e(item.task)}</p><p class="muted">${item.is_member?'Включён в группу владельцем рабочей области.':'Не включён в группу. Показано только совпадение указанных навыков с требованиями задачи.'}</p><p><strong>Совпадают названия навыков:</strong> ${e(item.matched_skills.join('; '))}.</p>${item.unconfirmed_skills.length?`<p><strong>Нет сведений по требованиям:</strong> ${e(item.unconfirmed_skills.join('; '))}. Отсутствие сведений не означает отсутствие навыка.</p>`:'<p>Все названия требуемых навыков есть в карточке. Уровень владения требует проверки рабочими примерами.</p>'}</section>`).join('');
 return `${includeNumerom?employeeNumeromHtml(analysis.numerom,{compact}):''}<section class="employee-analysis"><h4>Разбор заявленных сведений</h4><p><strong>${analysis.status==='ready_for_discussion'?'Есть навыки и опыт для обсуждения':'Нужно дополнить сведения о навыках и опыте'}</strong></p><h4>Совпадения с требованиями сохранённых задач</h4>${matches||'<p>Точных совпадений в сохранённых данных пока нет. Это не оценка способностей сотрудника.</p>'}<h4>Недостающие сведения</h4>${analysis.missing_data.length?list(analysis.missing_data):'<p>Навыки, опыт, интересы и доступность заполнены. Сведения заявлены и требуют подтверждения.</p>'}<h4>Вопросы и рабочие примеры для обсуждения</h4>${list(analysis.next_steps)}</section>`;
}
function businessEmployeeAnalysisHtml(value, employeeId) {
 const workspace=businessWorkspace(value),analysis=businessEmployeeAnalysis(workspace,employeeId),member=analysis.employee,e=escapeHtml;
 const field=(label,value)=>`<dt>${e(label)}</dt><dd>${e(value||'Не указано')}</dd>`;
 const list=items=>items.length?`<ul>${items.map(item=>`<li>${e(item)}</li>`).join('')}</ul>`:'<p class="muted">Не указано</p>';
 const memberships=workspace.groups.filter(item=>item.member_ids.includes(member.id)).map(item=>item.name);
 return `<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${e(member.name)} ${e(member.surname)} — NumerOM Business</title><style>@page{size:A4;margin:18mm}*{box-sizing:border-box}body{font-family:Arial,sans-serif;color:#162c49;line-height:1.5;max-width:1000px;margin:auto;padding:24px;font-size:14px;overflow-wrap:anywhere}h1{font-size:28px}h2{font-size:21px}h3,h4{font-size:17px;margin-top:24px}h5{font-size:15px;margin:14px 0 8px}h1,h2,h3,h4,h5{break-after:avoid}p,dd{white-space:pre-wrap}.muted{color:#56677d}.brand{font-weight:bold;color:#183b72;letter-spacing:.07em}dl{display:grid;grid-template-columns:150px 1fr;gap:8px}dt{font-weight:bold}dd{margin:0}.note{padding:14px;background:#f2f5fa;border-radius:12px}.task-overlap{border-left:3px solid #d7dfea;padding-left:14px}.employee-numerom th,.employee-numerom td{padding:9px;border:1px solid #d7dfea;text-align:left;vertical-align:top;overflow-wrap:anywhere}.employee-numerom th{background:#eef3fa}.numerom-theme{break-inside:avoid-page}footer{margin-top:28px;font-size:12px}@media print{body{padding:0}}</style></head><body><p class="brand">NUMEROM · BUSINESS 250</p><p>${e(workspace.company_name)}</p><h1>${e(member.name)} ${e(member.surname)}</h1><p>Дата рождения: ${e(member.birth_date||'Не указана')}. Версия рабочей области ${analysis.workspace_revision}.</p>${employeeNumeromHtml(analysis.numerom)}<h2>Рабочие сведения</h2><p class="note">${e(analysis.basis)}</p><h2>Данные карточки</h2><dl>${field('Дата рождения',member.birth_date||'Не указана')}${field('Подразделение',member.department)}${field('Текущая роль',member.role)}${field('Опыт',analysis.experience)}${field('Доступность',analysis.hours_per_week===null?'Не указана':`${analysis.hours_per_week} ч в неделю`)}</dl><h3>Заявленные навыки</h3>${list(analysis.skills)}<h3>Профессиональные интересы</h3>${list(analysis.interests)}<h3>Участие в сохранённых группах</h3>${memberships.length?list(memberships):'<p class="muted">Пока не включён в группы.</p>'}${employeeAnalysisSectionHtml(analysis,{includeNumerom:false})}<footer>Личный отчёт NumerOM Business. Перед передачей документа проверьте, кому доступны персональные сведения.</footer></body></html>`;
}
function businessReportHtml(value, companyName) {
 const report=businessReport(value),company=text(companyName,160,true),e=escapeHtml;
 const fullName=member=>`${member.name} ${member.surname}`, people=Object.fromEntries(report.members.map(member=>[member.id,fullName(member)]));
 const list=items=>items.length?`<ul>${items.map(item=>`<li>${e(item)}</li>`).join('')}</ul>`:'<p class="muted">Не указано</p>';
 const field=(label,value)=>`<dt>${e(label)}</dt><dd>${e(value||'Не указано')}</dd>`;
 const coverage=report.coverage.length?`<table><thead><tr><th>Требуемый навык</th><th>Участники с указанным навыком</th><th>Покрытие</th></tr></thead><tbody>${report.coverage.map(item=>`<tr><td>${e(item.skill)}</td><td>${e(item.employee_ids.map(id=>people[id]).join(', ')||'Нет сведений')}</td><td>${item.employee_ids.length?'Есть в данных':'Не подтверждено'}</td></tr>`).join('')}</tbody></table>`:'<p>Требуемые навыки ещё не заданы. Добавьте их для проверки покрытия задачи.</p>';
 return `<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${e(report.name)} — NumerOM Business</title><style>@page{size:A4;margin:18mm}*{box-sizing:border-box}body{font-family:Arial,sans-serif;color:#162c49;line-height:1.5;max-width:1000px;margin:auto;padding:24px;font-size:14px;overflow-wrap:anywhere}h1{font-size:28px}h2{font-size:21px;margin-top:28px}h3{font-size:17px}p,dd{white-space:pre-wrap}.muted{color:#56677d}.brand{font-weight:bold;color:#183b72;letter-spacing:.07em}table{border-collapse:collapse;width:100%;table-layout:fixed}th,td{padding:10px;border:1px solid #d7dfea;text-align:left;vertical-align:top}th{background:#eef3fa}article{break-inside:avoid;border-top:1px solid #d7dfea;margin-top:18px;padding-top:12px}dl{display:grid;grid-template-columns:145px 1fr;gap:8px}dt{font-weight:bold}dd{margin:0}.note{padding:14px;background:#f2f5fa;border-radius:12px}footer{margin-top:28px;font-size:12px}@media print{body{padding:0}thead{display:table-header-group}}</style></head><body><p class="brand">NUMEROM · BUSINESS 250</p><p>${e(company)}</p><h1>${e(report.name)}</h1><h2>Задача группы</h2><p>${e(report.task)}</p><p>Участников: ${report.member_count}. Состав выбран владельцем рабочей области.</p><p class="note">Введённые сведения — навыки, опыт, интересы и доступность. Расчётные сведения — покрытие указанных навыков и объём времени. Показатели NumerOM и символические трактовки по имени и дате рождения приложены к каждому участнику. Отчёт не содержит рейтинга сотрудников и не заменяет проверку квалификации.</p><h2>Покрытие задачи</h2>${coverage}<h3>Навыки, по которым не хватает сведений</h3>${report.missing_skills.length?list(report.missing_skills):'<p>По каждому указанному навыку есть хотя бы один участник. Уровень владения нужно подтвердить рабочим примером.</p>'}<h2>Планирование времени</h2><dl>${field('Нужно для задачи',report.target_hours===null?'Не указано':`${report.target_hours} ч в неделю`)}${field('Заявленная доступность',report.available_hours===null?'Недостаточно данных':`${report.available_hours} ч в неделю`)}</dl>${report.missing_hours_data.length?`<p>Не указана доступность: ${e(report.missing_hours_data.map(id=>people[id]).join(', '))}.</p>`:'<p>Доступность указана для всех участников.</p>'}<p class="muted">Время указано участниками или владельцем и требует подтверждения перед назначением задачи.</p><h2>Карточки всех участников</h2>${report.members.length?report.members.map(member=>`<article><h3>${e(fullName(member))}</h3><dl>${field('Дата рождения',member.birth_date||'Не указана')}${field('Подразделение',member.department)}${field('Текущая роль',member.role)}${field('Опыт',member.experience)}${field('Доступность',member.hours_per_week===null?'Не указана':`${member.hours_per_week} ч в неделю`)}</dl><h4>Заявленные навыки</h4>${list(member.skills)}<h4>Профессиональные интересы</h4>${list(member.interests)}${!member.skills.length||!member.experience||member.hours_per_week===null?`<p class="muted">Уточнить: ${e([!member.skills.length?'навыки':'',!member.experience?'опыт и рабочие примеры':'',member.hours_per_week===null?'доступность':''].filter(Boolean).join('; '))}.</p>`:''}</article>`).join(''):'<p>Участники ещё не выбраны.</p>'}<h2>Показатели NumerOM участников</h2>${report.members.map(member=>`<section><h3>${e(fullName(member))}</h3>${employeeNumeromHtml(employeeNumerom(member),{compact:true})}</section>`).join('')}<h2>Следующие действия</h2>${list(report.next_steps)}<footer>Личный отчёт рабочей области NumerOM Business. Перед передачей документа проверьте, кому доступны персональные сведения.</footer></body></html>`;
}
function businessWorkspaceHtml(value) {
 const workspace=businessWorkspace(value),e=escapeHtml,inventory=new Map(),memberships=new Map();
 for(const member of workspace.employees)for(const skill of member.skills){const id=key(skill),found=inventory.get(id);if(found)found.count++;else inventory.set(id,{name:skill,count:1});}
 for(const group of workspace.groups)for(const id of group.member_ids){if(!memberships.has(id))memberships.set(id,[]);memberships.get(id).push(group.name);}
 const missing={skills:workspace.employees.filter(member=>!member.skills.length).length,experience:workspace.employees.filter(member=>!member.experience).length,hours:workspace.employees.filter(member=>member.hours_per_week===null).length,interests:workspace.employees.filter(member=>!member.interests.length).length,role:workspace.employees.filter(member=>!member.role).length};
 const statedHours=workspace.employees.reduce((total,member)=>total+(member.hours_per_week??0),0);
 const field=(name,value)=>`<dt>${e(name)}</dt><dd>${e(value||'Не указано')}</dd>`;
 const list=items=>items.length?`<ul>${items.map(item=>`<li>${e(item)}</li>`).join('')}</ul>`:'<p class="muted">Не указано</p>';
 return `<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${e(workspace.company_name)} — сотрудники NumerOM Business</title><style>@page{size:A4;margin:18mm}*{box-sizing:border-box}body{font-family:Arial,sans-serif;color:#162c49;line-height:1.5;max-width:1000px;margin:auto;padding:24px;font-size:14px;overflow-wrap:anywhere}h1{font-size:28px}h2{font-size:21px;margin-top:28px}h3{font-size:17px}p,dd{white-space:pre-wrap}.muted{color:#56677d}.brand{font-weight:bold;color:#183b72;letter-spacing:.07em}table{border-collapse:collapse;width:100%;table-layout:fixed}th,td{padding:9px;border:1px solid #d7dfea;text-align:left;vertical-align:top}th{background:#eef3fa}h1,h2,h3,h4,h5{break-after:avoid}h5{font-size:15px;margin:14px 0 8px}.task-overlap{border-left:3px solid #d7dfea;padding-left:14px}article{border-top:1px solid #d7dfea;margin-top:18px;padding-top:12px}dl{display:grid;grid-template-columns:150px 1fr;gap:8px}dt{font-weight:bold}dd{margin:0}.note{padding:14px;background:#f2f5fa;border-radius:12px}footer{margin-top:28px;font-size:12px}@media print{body{padding:0}thead{display:table-header-group}}</style></head><body><p class="brand">NUMEROM · BUSINESS 250</p><h1>${e(workspace.company_name)}</h1><h2>Отчёт по сотрудникам</h2><p>Сотрудников: ${workspace.employees.length}. Сохранённых групп: ${workspace.groups.length}.</p><p class="note">В отчёте собраны введённые навыки, опыт, профессиональные интересы и доступность. Количество упоминаний навыка показывает полноту сведений, а не уровень квалификации. Расчёты по имени и дате рождения и трактовки базы знаний включены в раздел NumerOM каждого сотрудника. Профессиональный опыт и требования задач рассматриваются отдельно. Состав групп выбран владельцем. В разборе сотрудника показываются точные совпадения названий навыков с требованиями сохранённых задач, без оценки уровня владения. Готовность к обсуждению означает только наличие описания навыков и опыта.</p><h2>Каких данных не хватает</h2><table><thead><tr><th>Сведения</th><th>Сотрудников без сведений</th></tr></thead><tbody><tr><td>Навыки</td><td>${missing.skills}</td></tr><tr><td>Опыт и рабочие примеры</td><td>${missing.experience}</td></tr><tr><td>Доступность</td><td>${missing.hours}</td></tr><tr><td>Профессиональные интересы</td><td>${missing.interests}</td></tr><tr><td>Текущая роль</td><td>${missing.role}</td></tr></tbody></table><p>Заявленная доступность: ${e(statedHours)} ч в неделю у ${workspace.employees.length-missing.hours} из ${workspace.employees.length} сотрудников.${missing.hours?' Полная доступность компании неизвестна: часть сведений отсутствует.':' Время нужно подтвердить перед назначением задач.'}</p><h2>Перечень заявленных навыков</h2>${inventory.size?`<table><thead><tr><th>Навык</th><th>Сотрудников, у которых он указан</th></tr></thead><tbody>${Array.from(inventory.values()).sort((a,b)=>a.name.localeCompare(b.name,'ru')).map(item=>`<tr><td>${e(item.name)}</td><td>${item.count}</td></tr>`).join('')}</tbody></table>`:'<p>Навыки ещё не заполнены. Добавьте сведения и рабочие примеры.</p>'}<h2>Все сотрудники</h2>${workspace.employees.length?workspace.employees.map((member,index)=>`<article><h3>${index+1}. ${e(member.name)} ${e(member.surname)}</h3><dl>${field('Дата рождения',member.birth_date||'Не указана')}${field('Подразделение',member.department)}${field('Текущая роль',member.role)}${field('Опыт',member.experience)}${field('Доступность',member.hours_per_week===null?'Не указана':`${member.hours_per_week} ч в неделю`)}</dl><h4>Заявленные навыки</h4>${list(member.skills)}<h4>Профессиональные интересы</h4>${list(member.interests)}<h4>Участие в сохранённых группах</h4>${memberships.has(member.id)?list(memberships.get(member.id)):'<p class="muted">Пока не включён в группы.</p>'}${employeeAnalysisSectionHtml(employeeAnalysis(workspace,member),{compact:true})}</article>`).join(''):'<p>Сотрудники ещё не добавлены.</p>'}<h2>Сохранённые группы</h2>${workspace.groups.length?workspace.groups.map(group=>`<section><h3>${e(group.name)}</h3><p>${e(group.task)}</p><p>Участников: ${group.member_ids.length}. Плановая потребность: ${group.target_hours===null?'не указана':`${e(group.target_hours)} ч в неделю`}.</p><h4>Требуемые навыки</h4>${list(group.required_skills)}</section>`).join(''):'<p>Группы ещё не созданы.</p>'}<h2>Следующие действия</h2><ol><li>Уточните недостающие навыки, опыт и доступность вместе с сотрудниками.</li><li>Подтвердите заявленные навыки примерами выполненных работ.</li><li>Опишите конкретную задачу и необходимые навыки, затем выберите состав группы.</li><li>Сверьте покрытие задачи и доступное время в отдельном отчёте группы.</li><li>Согласуйте роли, сроки и критерии результата с участниками.</li></ol><footer>Личный отчёт NumerOM Business. Перед передачей документа проверьте, кому доступны персональные сведения.</footer></body></html>`;
}
function validateBusinessFile(filename,size) {
 if(typeof filename!=='string'||!filename||filename.length>255||/[\\/\u0000-\u001f\u007f]/.test(filename)) return fail('Проверьте название файла.');
 if(/\.xls$/i.test(filename)) return fail('Сохраните старый файл XLS как XLSX или CSV в Excel и загрузите снова.');
 if(!/\.(xlsx|csv)$/i.test(filename)) return fail('Выберите таблицу XLSX или CSV.');
 if(!Number.isSafeInteger(size)||size<1||size>MAX_FILE) return fail('Выберите непустой файл размером до 5 МБ.');
 return filename;
}
/** A CSV download is text-only: protect Excel from interpreting values as formulas. */
function businessTemplate(filename,content) {
 if(typeof filename!=='string'||!/^[A-Za-z0-9_-]{1,100}\.csv$/.test(filename)||typeof content!=='string'||content.length<1||content.length>262144||controls.test(content)) return fail('Не удалось подготовить шаблон.');
 const source=content.replace(/^\ufeff/,''),rows=[],row=[];let cell='',quoted=false,closed=false;
 const pushCell=()=>{row.push(cell);cell='';closed=false;};
 const pushRow=()=>{pushCell();rows.push(row.splice(0));};
 for(let i=0;i<source.length;i++){
  const char=source[i];
  if(quoted){if(char==='"'){if(source[i+1]==='"'){cell+='"';i++;}else{quoted=false;closed=true;}}else cell+=char;continue;}
  if(char==='"'){if(cell||closed) return fail('Не удалось прочитать CSV-шаблон.');quoted=true;}
  else if(char===';')pushCell();
  else if(char==='\r'||char==='\n'){if(char==='\r'&&source[i+1]==='\n')i++;pushRow();}
  else {if(closed)return fail('Не удалось прочитать CSV-шаблон.');cell+=char;}
 }
 if(quoted) return fail('Не удалось прочитать CSV-шаблон.');
 if(cell||row.length||closed)pushRow();
 if(!rows.length||rows.length>252||rows.some(item=>item.length>30)) return fail('Не удалось прочитать CSV-шаблон.');
 const safe=value=>`"${(/^[\s\u0000-\u001f]*[=+\-@]/u.test(value)?"'"+value:value).replace(/"/g,'""')}"`;
 return {filename,content:'\ufeff'+rows.map(item=>item.map(safe).join(';')).join('\r\n')+'\r\n'};
}
module.exports={businessEnvelope,businessWorkspace,businessPreview,businessReport,parseSkillList,employeeInput,businessReportHtml,businessWorkspaceHtml,businessEmployeeAnalysis,businessEmployeeAnalysisHtml,validateBusinessFile,businessTemplate};
