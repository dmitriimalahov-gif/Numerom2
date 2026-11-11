const {test} = require('node:test');
const assert = require('node:assert/strict');
const {nameSchemes} = require('../../packages/numerology-core/name-schemes');
const {nameSchemeVisuals} = require('../src/lib/nameSchemeVisuals');

const input = (name='Dmitrii', surname='Malahov') => nameSchemes({name,surname}, '10.01.1982');

test('triangle preserves the original right-shifted columns and links every result to both source neighbours', () => {
  const data=input(), before=JSON.stringify(data), {triangle}=nameSchemeVisuals(data);
  assert.equal(triangle.nodes.length,45);
  assert.equal(triangle.edges.length,72);
  assert.deepEqual(triangle.nodes.map(node=>node.value),data.rows.flat());
  assert.deepEqual(triangle.letters.map(label=>label.text),data.firstNine);
  const nodeById=Object.fromEntries(triangle.nodes.map(node=>[node.id,node]));
  for(const node of triangle.nodes) {
    assert.equal(node.x,triangle.nodes[0].x+(node.row+node.column)*48);
    assert.equal(node.y,triangle.nodes[0].y+node.row*46);
    const incoming=triangle.edges.filter(edge=>edge.to===node.id);
    if(node.row===0) {assert.equal(incoming.length,0);continue;}
    assert.deepEqual(incoming.map(edge=>edge.from),[
      `triangle-${node.row-1}-${node.column}`,`triangle-${node.row-1}-${node.column+1}`]);
    assert.equal(node.x,nodeById[incoming[1].from].x);
    assert.ok(node.x>nodeById[incoming[0].from].x);
  }
  assert.equal(triangle.nodes.at(-1).x,triangle.nodes[8].x);
  assert.equal(JSON.stringify(data),before);
});

test('letter origins and neighbour sums remain inspectable without an independent number calculation', () => {
  const {triangle}=nameSchemeVisuals(input());
  assert.equal(triangle.nodes[0].value,4);
  assert.equal(triangle.nodes[0].formula,'D → 4');
  const firstResult=triangle.nodes.find(node=>node.id==='triangle-1-0');
  assert.equal(firstResult.value,8);
  assert.equal(firstResult.formula,'4 + 4 = 8');
  const reduced=triangle.nodes.find(node=>node.id==='triangle-1-2');
  assert.equal(reduced.formula,'9 + 2 = 11 → 2');
  for(const node of triangle.nodes) {
    assert.ok(node.title.includes(`ряд ${node.row+1}`));
    assert.ok(node.meaning);
  }
});

test('human retains the authored seven positions, saved number values and individual letter provenance', () => {
  const data=input(), {human}=nameSchemeVisuals(data);
  assert.deepEqual(human.nodes.map(node=>node.id),
    ['head','handLeft','soul','handRight','mindNumber','bottomDigit','destinyNumber']);
  assert.deepEqual(human.nodes.map(node=>[node.x,node.y]),
    [[150,42],[50,146],[150,146],[250,146],[50,260],[150,260],[250,260]]);
  for(const node of human.nodes) {
    assert.equal(node.value,data.human[node.id]);
    assert.ok(node.labelY>node.y+node.radius);
    assert.ok(node.labelLines.length);
  }
  assert.match(human.nodes.find(node=>node.id==='handLeft').formula,/3-я буква: I → 9/);
  assert.match(human.nodes.find(node=>node.id==='handRight').formula,/2-я буква: M → 4/);
  assert.match(human.nodes.find(node=>node.id==='bottomDigit').formula,/Последняя буква: I → 9/);
  assert.equal(human.edges.length,6);
});

test('charts describe only their declared source and preserve zero counts', () => {
  const data=input(), visuals=nameSchemeVisuals(data), otherSurname=nameSchemeVisuals(input('Dmitrii','Jackson'));
  assert.deepEqual(visuals.triangle.series.points.map(point=>point.value),data.rows[0]);
  assert.deepEqual(visuals.triangle.series.points.map(point=>point.label),data.firstNine);
  const distribution=visuals.human.series;
  assert.equal(distribution.kind,'distribution');
  assert.deepEqual(distribution.points.map(point=>point.value),[0,1,0,2,0,0,0,0,4]);
  assert.equal(distribution.points.reduce((sum,point)=>sum+point.value,0),data.nameLetters.length);
  assert.deepEqual(distribution,otherSurname.human.series);
  assert.equal(distribution.points[0].y,distribution.baseline);
  assert.equal(distribution.ticks.at(-1).value,4);
});

test('all diagram and chart geometry stays finite and inside a uniformly scaled 232px content area', () => {
  for(const data of [input(),input('Jean-Luc','O’Neil'),input('Anna','Ivanova')]) {
    const {triangle,human}=nameSchemeVisuals(data);
    for(const model of [triangle,human]) {
      const scale=232/model.width, ids=new Set(model.nodes.map(node=>node.id));
      for(const node of model.nodes) {
        assert.ok(node.x-node.radius>=0 && node.x+node.radius<=model.width);
        assert.ok(node.y-node.radius>=0 && node.y+node.radius<=model.height);
        assert.ok(Number.isFinite(node.x*scale) && Number.isFinite(node.y*scale));
        assert.ok((node.x+node.radius)*scale<=232);
        if(node.labelLines) assert.ok(node.labelY+(node.labelLines.length-1)*19<model.height);
      }
      for(const edge of model.edges) assert.ok(ids.has(edge.from)&&ids.has(edge.to));
      for(const point of model.series.points) {
        assert.ok(point.x>=0&&point.x<=model.series.width);
        assert.ok(point.y>=0&&point.y<=model.series.height);
      }
    }
  }
});

test('unavailable or incomplete schemes stay absent without profile guesses or fabricated zeros', () => {
  assert.deepEqual(nameSchemeVisuals(null),{triangle:null,human:null});
  assert.deepEqual(nameSchemeVisuals({available:false}),{triangle:null,human:null});
  assert.deepEqual(nameSchemeVisuals(input('Li','Wu')),{triangle:null,human:null});
  const short=input('Anna','Li');
  assert.equal(nameSchemeVisuals(short).triangle,null);
  assert.equal(nameSchemeVisuals(short).human.nodes.length,7);
  for(const mutate of [data=>{data.rows[2].pop();},data=>{data.firstNine[0]='?';},data=>{data.rows[0][0]=NaN;}]) {
    const data=input();mutate(data);assert.equal(nameSchemeVisuals(data).triangle,null);
  }
  for(const mutate of [data=>{data.nameLetters=[];},data=>{data.human.head=null;},data=>{data.nameLetters[0].digit=0;}]) {
    const data=input();mutate(data);assert.equal(nameSchemeVisuals(data).human,null);
  }
});
