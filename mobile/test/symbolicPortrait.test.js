const test=require('node:test'),assert=require('node:assert/strict');
const {JSDOM}=require('jsdom');
const {symbolicPortrait,symbolicPortraitHtml}=require('../src/lib/symbolicPortrait');
const person={name:'Anna',surname:'Petrova',birth_date:'10.01.1982'};
test('portrait preserves project date rules, name geometry and knowledge source',()=>{
 const p=symbolicPortrait(person);assert.deepEqual(p.numbers.map(n=>n.value),[1,1,4]);assert.equal(p.nameSchemes.rows.flat().length,45);assert.equal(p.nameSchemes.human.destinyNumber,4);assert.equal(p.numbers[0].knowledge.planet,'Солнце');assert.match(p.numbers[2].formula,/10 \+ 1 \+ 1982 = 1993/);
 const master=symbolicPortrait({...person,birth_date:'22.11.2000'});assert.deepEqual(master.numbers.map(n=>n.value),[22,11,8]);assert.deepEqual(master.numbers.map(n=>n.base),[4,2,8]);
});
test('portrait ignores all job data and never modifies input',()=>{
 const p={...person,skills:['MUST_NOT_APPEAR'],experience:'PRIVATE_WORK',role:'Manager',hours_per_week:40};const before=JSON.stringify(p);
 assert.deepEqual(symbolicPortrait(p),symbolicPortrait(person));assert.equal(JSON.stringify(p),before);assert.doesNotMatch(symbolicPortraitHtml(p),/MUST_NOT_APPEAR|PRIVATE_WORK|Manager/);
});
test('missing dates and unsupported alphabet stay explicit without guessed transliteration',()=>{
 const p=symbolicPortrait({name:'Анна',surname:'Петрова'});assert.equal(p.numbers.length,0);assert.equal(p.birthDate,null);assert.equal(p.nameSchemes.available,false);assert.match(p.nameSchemes.note,/латинские/);assert.ok(p.dateNote);
 assert.throws(()=>symbolicPortrait({...person,birth_date:'31.02.2000'}));
});
test('separate portrait export includes vector schemes, knowledge and safe user text',()=>{
 const doc=new JSDOM(symbolicPortraitHtml(person)).window.document;assert.equal(doc.querySelectorAll('svg').length,4);assert.match(doc.body.textContent,/Инициатива и свой путь/);assert.match(doc.body.textContent,/не используются в рабочем анализе/);
 const html=symbolicPortraitHtml({...person,name:'<script>alert(1)</script>'});const hostile=new JSDOM(html).window.document;assert.equal(hostile.querySelectorAll('script').length,0);assert.match(hostile.querySelector('h1').textContent,/<script>/);assert.equal(hostile.querySelectorAll('[onerror]').length,0);
});
