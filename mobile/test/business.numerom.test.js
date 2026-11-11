const test=require('node:test'),assert=require('node:assert/strict');
const {JSDOM}=require('jsdom');
const {employeeNumerom}=require('../src/lib/employeeNumerom');
const {numberKnowledge}=require('../src/lib/numberKnowledge');
const {numberReflection}=require('../src/lib/reflectionKnowledge');
const {businessEmployeeAnalysis,businessEmployeeAnalysisHtml,businessWorkspaceHtml}=require('../src/lib/business');
const member={id:'employee',name:'Анна',surname:'Иванова',birth_date:'10.01.1982',department:'',role:'',skills:[],experience:'',interests:[],hours_per_week:null};
const workspace={id:'workspace',company_name:'Пример',revision:0,employees:[member],groups:[],created_at:'2026-11-07T10:00:00Z',updated_at:'2026-11-07T10:00:00Z'};

test('identity alone yields four NumerOM indicators, linked strengths and original course practices',()=>{
 const analysis=businessEmployeeAnalysis(workspace,'employee'),result=analysis.numerom;
 assert.deepEqual(result.indicators.map(n=>n.key),['soul','mind','destiny','name']);
 assert.deepEqual(result.indicators.slice(0,3).map(n=>n.value),[1,1,4]);
 assert.match(result.indicators[3].formula,/А\(1\)/);
 for(const theme of result.themes){
  assert.equal(theme.strength,numberKnowledge(theme.digit).segments[1]);
  assert.equal(theme.practice,numberReflection(theme.digit).practice);
  assert.ok(theme.sources.length);assert.ok(theme.indicators.length);
 }
 assert.equal(result.themes.filter(t=>t.digit===1).length,1,'repeated numbers share a single interpretation');
 assert.deepEqual(analysis.skills,[]);assert.deepEqual(analysis.task_matches,[]);
});
test('date master numbers and name master numbers are retained, with explicit base interpretation',()=>{
 const result=employeeNumerom({...member,name:'K',surname:'I',birth_date:'22.11.2000'});
 assert.deepEqual(result.indicators.map(n=>n.value),[22,11,8,11]);
 assert.deepEqual(result.indicators.map(n=>n.base),[4,2,8,2]);
 assert.equal(result.themes.find(t=>t.digit===2).indicators.length,2);
 assert.match(result.indicators[3].formula,/K\(2\) \+ I\(9\) = 11/);
});
test('name table supports Ё, mixed Russian/Latin, separators and has no guessed alphabet conversion',()=>{
 const name=person=>employeeNumerom({...member,...person}).indicators.find(n=>n.key==='name');
 assert.equal(name({name:'Ё',surname:'A'}).value,8);
 assert.equal(name({name:'Е',surname:'A'}).value,7);
 assert.deepEqual(name({name:'Anna',surname:'Petrova'}),name({name:'Anna-',surname:"Petrova'"}));
 const unsupported=employeeNumerom({...member,name:'王',surname:'Öztürk'});
 assert.equal(unsupported.indicators.length,3);assert.match(unsupported.notes.join(' '),/недоступно/);
 const missing=employeeNumerom({...member,birth_date:null});
 assert.equal(missing.indicators.length,1);assert.equal(missing.indicators[0].key,'name');assert.match(missing.notes.join(' '),/дату рождения/);
});
test('edits recalculate numbers and exported strengths; work evidence never affects NumerOM',()=>{
 const first=employeeNumerom(member);
 assert.deepEqual(employeeNumerom({...member,skills:['Excel'],role:'Директор',experience:'Работа',hours_per_week:40}),first);
 const next=businessEmployeeAnalysis({...workspace,revision:1,employees:[{...member,name:'Мария',birth_date:'22.11.2000'}]},'employee');
 assert.notDeepEqual(next.numerom,first);assert.equal(next.workspace_revision,1);
 const personalHtml=businessEmployeeAnalysisHtml(workspace,'employee');
 assert.ok(personalHtml.indexOf('class="employee-numerom"')<personalHtml.indexOf('<h2>Рабочие сведения</h2>'),'personal report starts with the requested calculation');
 for(const html of [businessEmployeeAnalysisHtml(workspace,'employee'),businessWorkspaceHtml(workspace)]){
  const doc=new JSDOM(html).window.document,section=doc.querySelector('.employee-numerom');
  assert.equal(doc.querySelectorAll('.employee-numerom').length,1,'one portrait per employee, without duplicate interpretations');
  assert.ok(section);assert.equal(section.querySelectorAll('tbody tr').length,4);
  for(const n of first.indicators)assert.ok(section.textContent.includes(n.formula));
  for(const t of first.themes){assert.ok(section.textContent.includes(t.summary));assert.ok(section.textContent.includes(t.practice));}
 }
});
test('250-person export includes NumerOM for every employee within the server HTML limit',()=>{
 const employees=Array.from({length:250},(_,i)=>({...member,id:`e-${i}`,name:'Анна',surname:`Иванова`,birth_date:`${String(i%28+1).padStart(2,'0')}.02.1990`}));
 const html=businessWorkspaceHtml({...workspace,employees});
 assert.ok(html.length<1536*1024,`HTML length ${html.length}`);
 const doc=new JSDOM(html).window.document;
 assert.equal(doc.querySelectorAll('.employee-numerom').length,250);
 for(const card of doc.querySelectorAll('article'))assert.equal(card.querySelectorAll('.employee-numerom tbody tr').length,4);
});
