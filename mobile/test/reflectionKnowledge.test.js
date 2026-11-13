const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {JSDOM}=require('jsdom');
const {numberReflection,comparisonReflection,reflectionHtml}=require('../src/lib/reflectionKnowledge');
const {symbolicPortraitHtml}=require('../src/lib/symbolicPortrait');
const {personalReportDocument}=require('../src/lib/reportExport');
const catalog=require('../../packages/reflection-knowledge/ru.json');
const pairs=require('../../packages/reflection-knowledge/comparisons.json');
const root=path.resolve(__dirname,'../..');

test('every reflection traces to unchanged local material and distinguishes editorial content',async t=>{
 assert.equal(catalog.scope,'planetary_reflection');
 assert.deepEqual(catalog.items.map(item=>item.digit),[1,2,3,4,5,6,7,8,9]);
 assert.equal(new Set(catalog.sources.map(s=>s.id)).size,catalog.sources.length);
 for(const source of catalog.sources){
  assert.ok(source.locator&&source.title);
  assert.ok(!path.isAbsolute(source.path));
  const absolute=path.resolve(root,source.path);assert.ok(absolute.startsWith(root+path.sep));
  assert.match(source.sha256,/^[a-f0-9]{64}$/);
  const privatePdf=source.kind==='course_pdf' && source.path.toLowerCase().endsWith('.pdf');
  await t.test('source integrity: '+source.id,{skip:process.env.CI==='1' && privatePdf && !fs.existsSync(absolute) ? 'Private lesson PDF remains in owner runtime' : false},()=>{
   assert.equal(crypto.createHash('sha256').update(fs.readFileSync(absolute)).digest('hex'),source.sha256);
  });
 }
 for(let digit=1;digit<=9;digit++){
  const entry=numberReflection(digit);assert.ok(entry.sourceSummary);
  assert.equal(entry.sources.length,entry.sourceIds.length);assert.ok(entry.sources.length);
  assert.equal(entry.reflection.length,2);assert.equal(new Set(entry.questions).size,2);
  assert.ok(entry.practice&&entry.comparisonFocus);
 }
 for(const digit of [3,4,5])assert.ok(numberReflection(digit).sources.every(source=>source.kind==='project_documentation'));
});

test('master numbers, counts, coercions and identity objects cannot select a substitute topic',()=>{
 for(const value of [0,-1,10,11,22,33,1.5,'1',null,undefined,NaN,Infinity,{name:'Anna',birth_date:'01.01.2000'}]){
  assert.equal(numberReflection(value),null);assert.equal(comparisonReflection(value,1),null);
  assert.equal(comparisonReflection(1,value),null);assert.equal(reflectionHtml(value),'');
 }
});

test('all 81 comparisons are covered, reversal preserves the exercise and repeated symbols stay distinct',()=>{
 assert.equal(pairs.items.length,36);
 assert.equal(new Set(pairs.items.map(p=>`${p.first}-${p.second}`)).size,36);
 for(const p of pairs.items)assert.ok(p.first>=1&&p.second<=9&&p.first<p.second);
 for(let a=1;a<=9;a++)for(let b=1;b<=9;b++){
  const result=comparisonReflection(a,b);assert.ok(result,`${a}/${b}`);
  assert.equal(result.practice,comparisonReflection(b,a).practice);
  assert.equal(result.questions.length,a===b?2:3);
  assert.deepEqual(result.themes.map(t=>t.digit),a===b?[a]:[a,b]);
  assert.ok(!('score' in result));assert.ok(!('compatibility' in result));
 }
 assert.match(comparisonReflection(8,8).title,/разных ситуациях/);
 assert.notEqual(comparisonReflection(1,2).practice,comparisonReflection(1,3).practice);
});

test('individual exports retain reflections, exact source locators and safe text',()=>{
 const entry=numberReflection(6),doc=new JSDOM(reflectionHtml(6)).window.document;
 assert.equal(doc.querySelectorAll('[data-reflection-digit="6"]').length,1);
 for(const question of entry.questions)assert.ok(doc.body.textContent.includes(question));
 for(const source of entry.sources)assert.ok(doc.body.textContent.includes(source.locator));
 const portrait=new JSDOM(symbolicPortraitHtml({name:'<img src=x onerror=alert(1)>',surname:'Demo',birth_date:'06.08.2000'})).window.document;
 assert.equal(portrait.querySelectorAll('.reflection').length,3);
 assert.equal(portrait.querySelectorAll('script,[onerror]').length,0);
 assert.ok(portrait.body.textContent.includes(entry.practice));
 const repeated=new JSDOM(symbolicPortraitHtml({name:'Anna',surname:'Demo',birth_date:'10.01.1982'})).window.document;
 assert.equal(repeated.querySelectorAll('[data-reflection-digit="1"]').length,1);
 const report={birthDate:'10.01.1982',numbers:[{title:'Число души',key:'soul',value:1,steps:[]},{title:'Число ума',key:'mind',value:1,steps:[]}],scheme:null,planets:null};
 const exported=new JSDOM(personalReportDocument({report}).html).window.document;
 assert.equal(exported.querySelectorAll('[data-reflection-digit="1"]').length,1);
});
