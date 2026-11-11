const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const core=require('../../packages/numerology-core/comprehensive');
const {comprehensiveReport}=require('../src/lib/comprehensiveReport');
const {comprehensiveHtml,vedicDocument,assessmentDocument}=require('../src/lib/supplementalReportExport');
const {JSDOM}=require('jsdom');
const fixture=require('./fixtures/vedicReport.json');
function original(){
 const source=fs.readFileSync(require.resolve('../../frontend/src/components/ComprehensiveReport.jsx'),'utf8');const ast=ts.createSourceFile('legacy.jsx',source,ts.ScriptTarget.Latest,true,ts.ScriptKind.JSX),found={};
 const names=Object.keys(core);
 function visit(node){if(ts.isVariableDeclaration(node)&&names.includes(node.name.getText(ast))&&!found[node.name.getText(ast)])found[node.name.getText(ast)]=node.initializer.getText(ast);ts.forEachChild(node,visit);}visit(ast);
 return vm.runInNewContext(names.map(n=>`const ${n}=${found[n]};`).join('\n')+'\n({'+names.join(',')+'})');
}
const result=()=>({createdAt:'2026-10-18T00:05:00Z',report:{birthDate:'10.01.1982',numbers:[{key:'soul',value:1},{key:'mind',value:1},{key:'destiny',value:4}]}});
test('extracted arithmetic matches all four original JSX functions for ordinary, zero-difference, master and leap dates',()=>{
 const old=original(),same=(a,b)=>assert.deepEqual(JSON.parse(JSON.stringify(a)),JSON.parse(JSON.stringify(b)));
 for(const birth of ['10.01.1982','29.02.2000','22.11.1999','11.11.2011','01.01.1900']){
  const f=core.calculateBehaviorFractal(birth);same(f,old.calculateBehaviorFractal(birth));
  same(core.calculateTaskNumbers(f.digit1,f.digit2,f.digit4,f.digit3),old.calculateTaskNumbers(f.digit1,f.digit2,f.digit4,f.digit3));
  same(core.calculateShadowsPeaksChallenges(birth),old.calculateShadowsPeaksChallenges(birth));
  same(core.calculateIndividualNumbers(birth,new Date(2026,9,18,12),f.digit4),old.calculateIndividualNumbers(birth,new Date(2026,9,18,12),f.digit4));
 }
});
test('saved snapshot fixes calendar date, preserves zero tasks, refuses invalid or missing data',()=>{
 const input=result(),before=JSON.stringify(input),r=comprehensiveReport(input);
 assert.equal(r.targetDate,'2026-10-18');assert.equal(r.fractal.fractal,'1124');assert.equal(r.tasks.problem1,0);assert.equal(r.individual.chig.value,3);assert.equal(r.individual.chim.value,4);assert.equal(r.individual.chid.value,4);assert.equal(JSON.stringify(input),before);
 input.report.numbers=[];assert.equal(comprehensiveReport(input).tasks,null);
 input.report.birthDate='31.02.2000';assert.equal(comprehensiveReport(input),null);
 input.report.birthDate='10.01.1982';input.createdAt='unknown';assert.equal(comprehensiveReport(input),null);
});
test('all supplemental reports export the same data and inert text with no external markup',()=>{
 const unsafe='<img src="https://attacker.invalid" onerror="alert(1)">';
 const route=structuredClone(fixture);route.city=unsafe;route.days[0].periods[0].meaning=unsafe;
 const document=vedicDocument({results:route,created_at:'2026-10-18T10:00:00Z'}),dom=new JSDOM(document);
 assert.equal(dom.window.document.querySelectorAll('img,script,iframe,a').length,0);assert.ok(dom.window.document.body.textContent.includes(unsafe));assert.match(dom.window.document.body.textContent,/Ритм периода/);dom.window.close();
 const a={results:{kind:'assessment',number:1,theme:unsafe,interpretation:unsafe,focus:'Смысл',frequencies:[{number:1,count:10}],answers:[{question:unsafe,answer:unsafe,number:1}],method:'Формула',total:10},created_at:'2026-10-18T00:00:00Z'};
 assert.doesNotMatch(assessmentDocument(a),/<img/);assert.match(assessmentDocument(a),/Формула/);
 const html=comprehensiveHtml(result());assert.match(html,/Задача 1: 0/);assert.match(html,/2026-10-18/);assert.match(html,/Тени, вершины/);
});
const {nameSchemes}=require('../../packages/numerology-core/name-schemes');
test('name triangle and human positions match the source algorithm without guessing full names',()=>{
 const source=fs.readFileSync(require.resolve('../../frontend/src/components/ComprehensiveReport.jsx'),'utf8');
 const start=source.indexOf("const name = (reportData.personal?.name || '').toUpperCase();");const end=source.indexOf('const surnameOnly =',start);
 const body=source.slice(start,end)+'return {rows,humanData};';
 const js=ts.transpileModule('(function(reportData){'+body+'})',{compilerOptions:{jsx:ts.JsxEmit.React,target:ts.ScriptTarget.ES2022}}).outputText;
 const run=vm.runInNewContext(js);
 for(const parts of [{name:'Dmitrii',surname:'Malahov'},{name:'Jean-Luc',surname:'O’Neil'},{name:'Anna',surname:'Ivanova'}]){
  const expected=run({personal:{...parts,birth_date:'10.01.1982'}}),actual=nameSchemes(parts,'10.01.1982');
  assert.deepEqual(actual.rows,JSON.parse(JSON.stringify(expected.rows)));assert.deepEqual(actual.human,JSON.parse(JSON.stringify(expected.humanData)));
  assert.equal(actual.rows.length,9);assert.equal(actual.rows.at(-1).length,1);
 }
 assert.equal(nameSchemes(null,'10.01.1982').available,false);
 assert.equal(nameSchemes({name:'Dmitrii Малахов',surname:''},'10.01.1982').available,false);
 assert.equal(nameSchemes({name:'Élodie',surname:'Malherbe'},'10.01.1982').available,false);
 const short=nameSchemes({name:'Li',surname:'Wu'},'10.01.1982');assert.deepEqual(short.rows,[]);assert.equal(short.human,null);
 const r=result();r.report.profileName='Dmitrii Malahov';assert.equal(comprehensiveReport(r).nameSchemes.available,false);
 r.report.profileParts={name:'Dmitrii',surname:'Malahov'};assert.equal(comprehensiveReport(r).nameSchemes.available,true);
});
