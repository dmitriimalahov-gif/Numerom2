const test=require('node:test'),assert=require('node:assert/strict');
const {loadingFrame,LOADING_CYCLE}=require('../../packages/full-report/loading-motion');

const texts=(frame)=>frame.shapes.filter(s=>s.kind==='text').map(s=>s.text);
const finite=(frame)=>frame.shapes.every(s=>['x','y','w','h','x1','y1','x2','y2','opacity'].every(k=>s[k]===undefined||Number.isFinite(s[k])));

test('the date drops in, its digits land in their cells and every line is traced',()=>{
 const start=loadingFrame(.05,'10.01.1982'),landed=loadingFrame(4.8,'10.01.1982'),traced=loadingFrame(9.1,'10.01.1982');
 assert.equal(start.caption,'Читаем дату рождения');assert.equal(landed.caption,'Раскладываем цифры по квадрату');
 // 10.01.1982 has three ones and one each of 2, 8 and 9: the cells read exactly that.
 for(const cell of ['111','2','8','9'])assert.ok(texts(landed).includes(cell),cell);
 assert.equal(landed.shapes.filter(s=>s.kind==='line').length,0);
 assert.equal(traced.shapes.filter(s=>s.kind==='line').length,8);
 assert.ok([start,landed,traced].every(finite));
});

test('the motion loops, survives a missing date and stands still for reduced motion',()=>{
 assert.deepEqual(loadingFrame(3.3,'10.01.1982').shapes.filter(s=>s.opacity>.1),loadingFrame(3.3+LOADING_CYCLE,'10.01.1982').shapes.filter(s=>s.opacity>.1).map((s,i,a)=>a[i]));
 assert.ok(finite(loadingFrame(2,'not a date'))&&texts(loadingFrame(5,null)).includes('7'));
 const still=loadingFrame(0,'10.01.1982',true),later=loadingFrame(7,'10.01.1982',true);
 assert.deepEqual(still,later);
 assert.equal(still.shapes.filter(s=>s.kind==='line').length,8);
});
