const {test}=require('node:test');
const assert=require('node:assert/strict');
const {personalScheme}=require('../src/lib/personalScheme');
const {schemeFixture}=require('./fixtures/personalScheme');
test('server square retains zero counts, canonical orientation and line sums without mutating input',()=>{
 const input=schemeFixture(),before=structuredClone(input);input.cells.reverse();
 const value=personalScheme(input,'10.01.1982');assert.deepEqual(value.cells.map(cell=>cell.digit),[1,4,7,2,5,8,3,6,9]);
 assert.equal(value.cells[2].count,0);assert.equal(value.lines[0].value,4);assert.equal(value.lines[7].value,0);
 assert.deepEqual(input.cells,before.cells.reverse());
});
test('missing, wrong-date, duplicate, incomplete and contradictory squares are unavailable, never reconstructed',()=>{
 assert.equal(personalScheme(undefined,'10.01.1982'),null);
 assert.equal(personalScheme(schemeFixture(),'02.03.1990'),null);
 for(const change of [s=>{s.version=2;},s=>{s.cells.pop();},s=>{s.cells[0]=s.cells[1];},s=>{s.cells[0].count=0;},s=>{s.lines[0].value=99;},s=>{s.lines[1]=s.lines[0];},s=>{s.lines[0].digits=[7,4,1];},s=>{s.additional_numbers.pop();}]){
  const input=schemeFixture();change(input);assert.equal(personalScheme(input,'10.01.1982'),null);
 }
});
