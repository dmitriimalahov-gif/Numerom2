const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const ts=require('typescript');
const {businessEnvelope,businessWorkspace,businessPreview,businessReport,employeeInput,parseSkillList,businessReportHtml,businessWorkspaceHtml,validateBusinessFile,businessTemplate}=require('../src/lib/business');

const employee=(overrides={})=>({id:'e-1',name:'Анна',surname:'Иванова',birth_date:'12.02.1990',department:'Проекты',role:'Менеджер',skills:['Планирование','Excel'],experience:'Два завершённых проекта',interests:['Обучение'],hours_per_week:20,...overrides});
const input=(overrides={})=>{const {id,...value}=employee(overrides);return value;};
const group=(overrides={})=>({id:'g-1',name:'Запуск проекта',task:'Подготовить смету и план',required_skills:['Планирование','Дизайн'],target_hours:30,member_ids:['e-1'],...overrides});
const workspace=(overrides={})=>({id:'business-1',company_name:'Учебная компания',revision:0,employees:[employee()],groups:[group()],created_at:'2026-10-18T08:00:00+00:00',updated_at:'2026-10-18T08:00:00+00:00',...overrides});
const pack={id:'business-250',title:'NumerOM Business 250',max_employees:250,mode:'pilot',price:0};
const report=(overrides={})=>({name:'Запуск проекта',task:'Подготовить смету и план',member_count:1,coverage:[{skill:'Планирование',employee_ids:['e-1']},{skill:'Дизайн',employee_ids:[]}],missing_skills:['Дизайн'],available_hours:20,target_hours:30,missing_hours_data:[],next_steps:['Уточнить опыт в дизайне'],members:[employee()],...overrides});

test('business activation envelope does not invent access, a price, or a workspace',()=>{
 assert.deepEqual(businessEnvelope({package:pack,workspace:null}),{package:pack,workspace:null});
 assert.equal(businessEnvelope({package:pack,workspace:workspace()}).workspace.employees.length,1);
 for(const value of [null,{},[],{package:pack},{package:{...pack,price:10},workspace:null},{package:{...pack,max_employees:500},workspace:null},{package:{...pack,mode:'paid'},workspace:null}])assert.throws(()=>businessEnvelope(value));
});

test('workspace keeps all 250 employees, rejects overflow, dangling references and duplicate identities',()=>{
 const all=Array.from({length:250},(_,i)=>employee({id:`e-${i}`,name:`Имя ${i}`}));
 assert.equal(businessWorkspace({workspace:workspace({employees:all})}).employees.length,250);
 for(const value of [workspace({employees:[...all,employee({id:'e-250'})]}),workspace({employees:[employee(),employee()]}),workspace({groups:[group({member_ids:['foreign']})]}),workspace({groups:[group(),group()]}),workspace({revision:0.5}),workspace({revision:Infinity}),workspace({revision:-1}),workspace({updated_at:'bad'})])assert.throws(()=>businessWorkspace(value));
 const loaded=businessWorkspace({...workspace(),private_token:'do-not-display'});
 assert.equal('private_token' in loaded,false);
});

test('server-valid supplementary Unicode uses codepoint limits and canonical label normalization',()=>{
 const unicode=workspace({company_name:'𐐀'.repeat(160),employees:[employee({name:'𐐀'.repeat(80),experience:'𐐀'.repeat(2000)})]});
 assert.equal(businessWorkspace(unicode).employees[0].name,'𐐀'.repeat(80));
 assert.equal(employeeInput({...input(),name:'A\u030A'}).name,'Å');
 assert.throws(()=>employeeInput({...input(),name:'𐐀'.repeat(81)}));
});

test('employee form normalizes explicit job evidence without deriving traits or rank from identity',()=>{
 const form={name:'  Анна  ',surname:'Иванова',birth_date:'1990-02-12',skills:'Excel; excel; Планирование\nКоординация',interests:'Проекты',hours_per_week:'20,5'};
 const saved=employeeInput(form);
 assert.deepEqual(saved,{name:'Анна',surname:'Иванова',birth_date:'12.02.1990',department:'',role:'',skills:['Excel','Планирование','Координация'],experience:'',interests:['Проекты'],hours_per_week:20.5});
 const other=employeeInput({...form,name:'Пётр',birth_date:'1981-08-23'});
 const {name,surname,birth_date,...evidence}=saved;
 const {name:otherName,surname:otherSurname,birth_date:otherDate,...otherEvidence}=other;
 assert.deepEqual(evidence,otherEvidence);
 assert.deepEqual(Object.keys(saved).sort(),['birth_date','department','experience','hours_per_week','interests','name','role','skills','surname']);
 assert.deepEqual(parseSkillList(' Ｅｘｃｅｌ ; Excel ; Управление   проектами'),['Ｅｘｃｅｌ','Управление проектами']);
 assert.deepEqual(parseSkillList('Straße; STRASSE; ς; σ; ı; i'),['Straße','ς','ı','i']);
 assert.equal(employeeInput({name:'Ольга',surname:'Петрова',hours_per_week:''}).hours_per_week,null);
 assert.equal(employeeInput({name:'Ольга',surname:'Петрова',hours_per_week:'0'}).hours_per_week,0);
});

test('invalid, oversized and ambiguous personal evidence cannot masquerade as valid form data',()=>{
 for(const patch of [{name:''},{name:'x'.repeat(81)},{birth_date:'31.02.1990'},{birth_date:'01.01.1899'},{birth_date:'01.01.2999'},{birth_date:'1/2/1990'},{hours_per_week:169},{hours_per_week:-1},{hours_per_week:true},{hours_per_week:'1e2'},{hours_per_week:'Infinity'},{hours_per_week:'20 ч'},{skills:Array(31).fill('Навык')},{interests:Array.from({length:21},(_,i)=>`Интерес${i}`)},{skills:['Excel','excel']},{experience:'bad\0data'},{role:'x'.repeat(121)}])assert.throws(()=>employeeInput({...input(),...patch}));
 assert.equal(employeeInput({...input(),birth_date:'29.02.2000'}).birth_date,'29.02.2000');
 assert.throws(()=>parseSkillList('x'.repeat(81)));
});

test('import preview exposes row errors and never reports partial or excessive import as valid',()=>{
 const preview={employees:[input()],issues:[],warnings:[{row:3,field:'name',message:'Проверьте однофамильцев'}],row_count:1,valid:true};
 assert.equal(businessPreview(preview).warnings[0].row,3);
 assert.equal(businessPreview({...preview,row_count:2,valid:false,issues:[{row:4,field:'birth_date',message:'Неверная дата'}]}).valid,false);
 assert.equal(businessPreview({employees:[],issues:[{row:0,field:'file',message:'Слишком много строк'}],warnings:[],row_count:251,valid:false}).row_count,251);
 assert.equal(businessPreview({employees:[],issues:[{row:0,field:'file',message:'Слишком много строк'}],warnings:[],row_count:1000,valid:false}).row_count,1000);
 assert.throws(()=>businessPreview({employees:[],issues:[],warnings:[],row_count:1001,valid:false}));
 for(const patch of [{valid:'true'},{row_count:2},{row_count:0},{issues:[{row:2,field:'name',message:'Ошибка'}]},{row_count:252},{warnings:[{row:-1,field:'name',message:'Ошибка'}]},{employees:[{...input(),skills:null}]}])assert.throws(()=>businessPreview({...preview,...patch}));
});

test('report rejects invented members, coverage and available hours including incomplete input',()=>{
 assert.equal(businessReport({report:report()}).available_hours,20);
 for(const patch of [{member_count:2},{coverage:[{skill:'Excel',employee_ids:['foreign']}],missing_skills:[]},{coverage:[{skill:'Excel',employee_ids:['e-1','e-1']}],missing_skills:[]},{missing_skills:[]},{missing_hours_data:['foreign']},{available_hours:21},{available_hours:null},{members:[employee({hours_per_week:null})]}])assert.throws(()=>businessReport(report(patch)));
 const incomplete=businessReport(report({members:[employee({hours_per_week:null})],available_hours:null,missing_hours_data:['e-1']}));
 assert.equal(incomplete.available_hours,null);
 assert.equal(businessReport(report({members:[],member_count:0,coverage:[],missing_skills:[],available_hours:0})).available_hours,0);
 assert.throws(()=>businessReport(report({next_steps:Array(9).fill('Действие')})));
});

test('printable report includes every member, gaps, task, evidence and missing data while escaping hostile markup',()=>{
 const members=[employee({name:'<img src=x onerror=alert(1)>',experience:'<script>alert(1)</script>',interests:['A & B']}),employee({id:'e-2',name:'Михаил',surname:'Сидоров',skills:[],experience:'',birth_date:null,hours_per_week:null})];
 const html=businessReportHtml(report({name:'Группа <b>А</b>',task:'Задача "1" & <2>',member_count:2,members,available_hours:null,missing_hours_data:['e-2']}),'Компания <script>');
 for(const text of ['Михаил Сидоров','Недостаточно данных','Дизайн','Уточнить опыт в дизайне','Профессиональные интересы','Текущая роль','&lt;img src=x onerror=alert(1)&gt;','&lt;script&gt;alert(1)&lt;/script&gt;','Задача &quot;1&quot; &amp; &lt;2&gt;','Показатели NumerOM и символические трактовки по имени и дате рождения приложены к каждому участнику'])assert.ok(html.includes(text),text);
 assert.equal(/<script|<img|\sonerror=/i.test(html.replace(/&lt;[^&]*&gt;/g,'')),false);
 assert.equal((html.match(/<article>/g)||[]).length,2);
 assert.equal((html.match(/class="employee-numerom"/g)||[]).length,2);
 assert.equal(html.includes('href='),false);
});

test('file guard accepts only bounded xlsx/csv and gives an explicit legacy XLS instruction',()=>{
 assert.equal(validateBusinessFile('Сотрудники.XLSX',5*1024*1024),'Сотрудники.XLSX');
 assert.equal(validateBusinessFile('Люди.csv',1),'Люди.csv');
 assert.throws(()=>validateBusinessFile('people.xls',1),/Сохраните старый файл XLS как XLSX/);
 for(const [name,size] of [['a.xlsm',10],['a.csv.exe',1],['a.csv',0],['a.xlsx',5*1024*1024+1],['../a.csv',1],['a\0.csv',1],['a.csv',Infinity],['a.csv','12']])assert.throws(()=>validateBusinessFile(name,size));
});

test('company report contains all 250 employee cards, aggregate skill evidence and membership without truncation',()=>{
 const employees=Array.from({length:250},(_,i)=>employee({id:`e-${i}`,name:`Сотрудник ${i+1}`,skills:i===249?[]:['Excel'],hours_per_week:i===249?null:1}));
 employees[249].surname='<script>Последний & участник</script>';
 const html=businessWorkspaceHtml(workspace({company_name:'Компания <img src=x>',employees,groups:[group({member_ids:['e-249']})]}));
 assert.equal((html.match(/<article>/g)||[]).length,250);
 for(const text of ['250. Сотрудник 250','&lt;script&gt;Последний &amp; участник&lt;/script&gt;','Участие в сохранённых группах','Запуск проекта','<td>Excel</td><td>249</td>','Полная доступность компании неизвестна','Компания &lt;img src=x&gt;'])assert.ok(html.includes(text),text);
 assert.equal(html.includes('<script>'),false);assert.equal(html.includes('<img '),false);
 assert.equal(businessWorkspaceHtml(workspace({employees:[],groups:[]})).includes('Сотрудники ещё не добавлены'),true);
});

test('CSV template preserves Unicode, quoted delimiters and newlines while neutralizing Excel formulas',()=>{
 const value=businessTemplate('numerom-business-template.csv','Имя;Опыт;Формула\r\n"Анна;Иванова";"Строка 1\nСтрока 2";"=HYPERLINK(""https://invalid"",""x"")"\r\nПётр;" +SUM(1)";"@NOW()"\nСергей;"\t-2";Обычный текст');
 assert.ok(value.content.startsWith('\ufeff'));
 for(const text of ['"Анна;Иванова"','"Строка 1\nСтрока 2"','"\'=HYPERLINK(""https://invalid"",""x"")"','"\' +SUM(1)"','"\'@NOW()"','"\'\t-2"','"Обычный текст"'])assert.ok(value.content.includes(text),text);
 assert.equal(businessTemplate('template.csv',value.content).content,value.content);
 for(const [filename,content] of [['../file.csv','a;b'],['file.html','a;b'],['file.csv','"unterminated'],['file.csv','"closed"extra'],['file.csv','a\0b'],['file.csv','x'.repeat(262145)]])assert.throws(()=>businessTemplate(filename,content));
});

function loadNativeFile({picker,read,size=10,sharing=true}){
 const files=[],source=fs.readFileSync(require.resolve('../src/lib/businessFile.ts'),'utf8'),module={exports:{}};
 class FakeFile{
  constructor(...args){this.uri=args.length===1?args[0]:`file:///cache/${args[1]}`;this.size=size;this.deleted=false;files.push(this);}
  async base64(){return read?read(): 'dGVzdA==';}
  write(content){this.content=content;}
  delete(){this.deleted=true;}
 }
 const shared=[];
 vm.runInNewContext(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports:module.exports,require:name=>name==='expo-document-picker'?{getDocumentAsync:picker}:name==='expo-file-system'?{File:FakeFile,Paths:{cache:{uri:'file:///cache/'}}}:name==='expo-sharing'?{isAvailableAsync:async()=>sharing,shareAsync:async(uri,options)=>shared.push({uri,options})}:name==='./business'?require('../src/lib/business'):assert.fail(name),Date});
 return {...module.exports,files,shared};
}

test('native picker reads one bounded file and deletes only its cached copy even when parsing fails',async()=>{
 let options;
 const reader=loadNativeFile({picker:async value=>{options=value;return {canceled:false,assets:[{name:'people.xlsx',uri:'file:///cache/document.xlsx'}]};}});
 assert.deepEqual(JSON.parse(JSON.stringify(await reader.pickBusinessFile())),{filename:'people.xlsx',content_base64:'dGVzdA=='});
 assert.equal(options.multiple,false);assert.equal(options.copyToCacheDirectory,true);
 assert.equal(reader.files[0].deleted,true);
 const broken=loadNativeFile({picker:async()=>({canceled:false,assets:[{name:'bad.xls',uri:'file:///cache/document.xls'}]})});
 await assert.rejects(broken.pickBusinessFile(),/XLSX/);assert.equal(broken.files[0].deleted,true);
 const source=loadNativeFile({picker:async()=>({canceled:false,assets:[{name:'people.csv',uri:'file:///documents/people.csv'}]}),read:()=>Promise.reject(new Error('read failure'))});
 await assert.rejects(source.pickBusinessFile(),/read failure/);assert.equal(source.files[0].deleted,false);
 assert.equal(await loadNativeFile({picker:async()=>({canceled:true,assets:null})}).pickBusinessFile(),null);
});

test('native template sharing uses sanitized CSV and removes the temporary file',async()=>{
 const fixture=loadNativeFile({picker:async()=>({canceled:true})});
 await fixture.saveBusinessTemplate('template.csv','Имя;Опыт\nАнна;=1+2');
 assert.ok(fixture.files[0].content.includes('"\'=1+2"'));
 assert.equal(fixture.files[0].deleted,true);
 assert.equal(fixture.shared.length,1);assert.equal(fixture.shared[0].options.mimeType,'text/csv');
 const noShare=loadNativeFile({picker:async()=>({canceled:true}),sharing:false});
 await assert.rejects(noShare.saveBusinessTemplate('template.csv','Имя;Опыт'),/браузере/);
 assert.equal(noShare.files.length,0);
});
