const test=require('node:test'),assert=require('node:assert/strict');
const {relationshipVoice}=require('../src/lib/relationshipVoice');
const entries=require('../../packages/project-knowledge/ru.json').items;
test('every score selects the contextual recording and all referenced texts exist',()=>{
 const expected=['contrast','contrast','contrast','contrast','contrast','different','different','close','close','same'];
 for(let score=1;score<=10;score++){
  const id=relationshipVoice(score);assert.equal(id,'relationship-'+expected[score-1]);
  const row=entries.find(entry=>entry.id===id);assert.ok(row?.text);assert.equal(row.section,'relationships');
 }
 for(const score of [0,11,NaN,1.5,'10'])assert.equal(relationshipVoice(score),null);
 assert.ok(entries.find(row=>row.id==='relationship-method')?.text);
});
