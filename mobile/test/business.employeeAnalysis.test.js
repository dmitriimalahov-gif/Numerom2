const {test}=require('node:test');
const assert=require('node:assert/strict');
const {JSDOM}=require('jsdom');
const {businessEmployeeAnalysis,businessEmployeeAnalysisHtml,businessWorkspaceHtml}=require('../src/lib/business');

const employee=(patch={})=>({id:'e-1',name:'Анна',surname:'Иванова',birth_date:'12.02.1990',department:'Проекты',role:'Координатор',skills:['Excel','Планирование'],experience:'Подготовила смету и план запуска.',interests:['Проекты'],hours_per_week:20,...patch});
const group=(patch={})=>({id:'g-1',name:'Смета',task:'Подготовить смету проекта',required_skills:['Excel','Бюджетирование'],target_hours:30,member_ids:['e-1'],...patch});
const workspace=(patch={})=>({id:'business-1',company_name:'Учебная компания',revision:7,employees:[employee()],groups:[group()],created_at:'2026-10-18T08:00:00+00:00',updated_at:'2026-10-18T08:00:00+00:00',...patch});
const evidence=analysis=>{const {employee,numerom,...result}=analysis;return result;};
const document=html=>new JSDOM(html).window.document;

test('employee analysis preserves task order and reports only exact declared-skill overlaps, including unassigned groups',()=>{
 const source=workspace({groups:[
  group({id:'g-first',name:'Чужая группа',member_ids:[],required_skills:['Планирование','Редактура']}),
  group({id:'g-no-match',required_skills:['Маркетинг']}),
  group({id:'g-empty',required_skills:[]}),
  group(),
 ]});
 const result=businessEmployeeAnalysis(source,'e-1');
 assert.equal(result.status,'ready_for_discussion');
 assert.equal(result.workspace_revision,7);
 assert.deepEqual(result.skills,['Excel','Планирование']);
 assert.equal(result.experience,'Подготовила смету и план запуска.');
 assert.deepEqual(result.interests,['Проекты']);
 assert.equal(result.hours_per_week,20);
 assert.deepEqual(result.task_matches,[
  {id:'g-first',name:'Чужая группа',task:'Подготовить смету проекта',matched_skills:['Планирование'],unconfirmed_skills:['Редактура'],is_member:false},
  {id:'g-1',name:'Смета',task:'Подготовить смету проекта',matched_skills:['Excel'],unconfirmed_skills:['Бюджетирование'],is_member:true},
 ]);
 assert.deepEqual(Object.keys(result).sort(),['basis','employee','experience','hours_per_week','interests','missing_data','next_steps','numerom','skills','status','task_matches','workspace_revision']);
 for(const skill of ['Excel','Планирование'])assert.ok(result.next_steps.some(step=>step.includes(`«${skill}»`)&&/пример работы/.test(step)&&/вклад/.test(step)&&/результат/.test(step)));
 assert.match(result.basis,/заявлен/);
});

test('names, surnames, birth dates and existing titles never change the computed employment analysis',()=>{
 const baseline=evidence(businessEmployeeAnalysis(workspace(),'e-1'));
 for(const identity of [
  {name:'Дмитрий',surname:'Малахов',birth_date:'01.01.1900'},
  {name:'Мария',surname:'Петрова',birth_date:'29.02.2000'},
  {name:'王',surname:'Öztürk',birth_date:null,role:'Генеральный директор',department:'Дирекция'},
 ])assert.deepEqual(evidence(businessEmployeeAnalysis(workspace({employees:[employee(identity)]}),'e-1')),baseline);
});

test('identity-only records need evidence and do not acquire task matches from titles, interests or group membership',()=>{
 const result=businessEmployeeAnalysis(workspace({employees:[employee({skills:[],experience:'',interests:[],hours_per_week:null,role:'Excel'})]}),'e-1');
 assert.equal(result.status,'needs_evidence');
 assert.deepEqual(result.task_matches,[]);
 assert.deepEqual(result.skills,[]);
 assert.equal(result.experience,'');
 assert.equal(result.hours_per_week,null);
 assert.equal(result.missing_data.length,4);
 assert.ok(result.missing_data.some(item=>/навык/i.test(item)));
 assert.ok(result.missing_data.some(item=>/опыт/i.test(item)));
 assert.ok(result.missing_data.some(item=>/интерес/i.test(item)));
 assert.ok(result.missing_data.some(item=>/доступност/i.test(item)));
 assert.ok(result.next_steps.length>0);
});

test('ready for discussion requires both skills and experience, never availability or claimed interests alone',()=>{
 for(const [skills,experience,status] of [
  [[], '', 'needs_evidence'],
  [['Excel'], '', 'needs_evidence'],
  [[], 'Описание работы', 'needs_evidence'],
  [['Excel'], 'Описание работы', 'ready_for_discussion'],
 ]){
  const result=businessEmployeeAnalysis(workspace({employees:[employee({skills,experience,interests:['Excel'],hours_per_week:0})]}),'e-1');
  assert.equal(result.status,status);
  assert.equal(result.hours_per_week,0);
  assert.equal(result.missing_data.some(item=>/доступност/i.test(item)),false);
 }
 const complete=businessEmployeeAnalysis(workspace(),'e-1');
 assert.deepEqual(complete.missing_data,[]);
 assert.ok(complete.task_matches[0].unconfirmed_skills.includes('Бюджетирование'));
});

test('skill intersections use exact Unicode casefold and whitespace normalization without substring or Turkish-dotless matches',()=>{
 const result=businessEmployeeAnalysis(workspace({
  employees:[employee({skills:['Ｅｘｃｅｌ','Straße','ς','A\u030A','Управление   проектами','ı','Excel VBA']})],
  groups:[group({required_skills:['excel','STRASSE','σ','Å','управление проектами','i','VBA','Excel для бизнеса']})],
 }),'e-1');
 assert.deepEqual(result.task_matches[0].matched_skills,['excel','STRASSE','σ','Å','управление проектами']);
 assert.deepEqual(result.task_matches[0].unconfirmed_skills,['i','VBA','Excel для бизнеса']);
});

test('analysis is recomputed from edited evidence and group requirements without modifying saved input',()=>{
 const source=workspace();
 const before=structuredClone(source);
 const first=businessEmployeeAnalysis(source,'e-1');
 assert.deepEqual(source,before);
 first.skills.push('НЕ СОХРАНЯТЬ');
 assert.deepEqual(source,before);
 source.revision=8;
 source.employees[0].skills=['Дизайн'];
 source.employees[0].experience='';
 const updated=businessEmployeeAnalysis(source,'e-1');
 assert.equal(updated.workspace_revision,8);
 assert.equal(updated.status,'needs_evidence');
 assert.deepEqual(updated.task_matches,[]);
 source.groups[0].required_skills=['Дизайн','Тестирование'];
 const changedTask=businessEmployeeAnalysis(source,'e-1');
 assert.deepEqual(changedTask.task_matches[0].matched_skills,['Дизайн']);
 assert.deepEqual(changedTask.task_matches[0].unconfirmed_skills,['Тестирование']);
 assert.ok(document(businessEmployeeAnalysisHtml(source,'e-1')).body.textContent.includes('Тестирование'));
});

test('all-staff printable report includes a current analysis for every one of 250 people and the last persons unassigned overlap',()=>{
 const employees=Array.from({length:250},(_,index)=>employee({id:`e-${index+1}`,name:`Сотрудник ${index+1}`,skills:[`Навык ${index+1}`],experience:`Рабочий пример ${index+1}`}));
 const source=workspace({employees,groups:[group({member_ids:[],required_skills:['Навык 250','Проверка результата']})]});
 const doc=document(businessWorkspaceHtml(source));
 const cards=[...doc.querySelectorAll('article')];
 assert.equal(cards.length,250);
 assert.equal(doc.querySelectorAll('.employee-analysis').length,250);
 for(let i=0;i<250;i++){
  const analysis=cards[i].querySelector('.employee-analysis');
  assert.ok(analysis,`Employee ${i+1} has an analysis`);
  assert.ok(analysis.textContent.includes(`«Навык ${i+1}»`));
 }
 const last=cards[249].textContent;
 for(const text of ['Сотрудник 250','Рабочий пример 250','Смета','Проверка результата','Не включён в группу'])assert.ok(last.includes(text),text);
 assert.equal(cards[0].querySelector('.employee-analysis').textContent.includes('Проверка результата'),false);
});

test('individual and all-staff HTML keep hostile fields as text and contain no executable markup or external links',()=>{
 const attack='<img src=x onerror="alert(1)"> & \'quoted\'';
 const source=workspace({company_name:attack,employees:[employee({name:attack,surname:'</title><script>x</script>',department:attack,role:attack,skills:[attack],experience:attack,interests:[attack]})],groups:[group({name:attack,task:attack,required_skills:[attack,'</li><svg onload="alert(1)">'],member_ids:[]})]});
 for(const html of [businessEmployeeAnalysisHtml(source,'e-1'),businessWorkspaceHtml(source)]){
  const doc=document(html);
  assert.equal(doc.querySelectorAll('script,img,svg,iframe,object,a,form,input').length,0);
  assert.ok(doc.body.textContent.includes(attack));
  assert.ok(doc.body.textContent.includes('</title><script>x</script>'));
  assert.ok(doc.body.textContent.includes('</li><svg onload="alert(1)">'));
  assert.ok(html.includes('&lt;img'));
  for(const element of doc.querySelectorAll('*'))assert.equal([...element.attributes].some(attr=>/^on/i.test(attr.name)),false);
 }
});

test('unknown employees and malformed workspaces fail instead of falling back to another persons analysis',()=>{
 assert.throws(()=>businessEmployeeAnalysis(workspace(),'missing'),/сотрудник/i);
 assert.throws(()=>businessEmployeeAnalysisHtml(workspace(),'missing'),/сотрудник/i);
 for(const invalid of [null,{},workspace({employees:[]}),workspace({revision:-1}),workspace({employees:[employee(),employee()]})])assert.throws(()=>businessEmployeeAnalysis(invalid,'e-1'));
 assert.deepEqual(businessEmployeeAnalysis({workspace:workspace()},'e-1'),businessEmployeeAnalysis(workspace(),'e-1'));
});

test('individual export keeps evidence and all matching tasks from the same model including unknown requirements',()=>{
 const source=workspace({employees:[employee({hours_per_week:null})],groups:[group(),group({id:'g-2',name:'Вторая задача',required_skills:['Планирование','Тестирование'],member_ids:[]})]});
 const result=businessEmployeeAnalysis(source,'e-1');
 const doc=document(businessEmployeeAnalysisHtml(source,'e-1'));
 const content=doc.body.textContent;
 for(const value of [result.employee.name,result.employee.surname,result.experience,...result.skills,...result.interests,...result.missing_data,...result.next_steps])assert.ok(content.includes(value),value);
 for(const match of result.task_matches)for(const value of [match.name,match.task,...match.matched_skills,...match.unconfirmed_skills])assert.ok(content.includes(value),value);
 assert.ok(content.includes('Не включён в группу'));
 assert.ok(content.includes('Недостаточно данных')||content.includes('Не указана'));
});
