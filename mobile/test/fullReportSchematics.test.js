const test=require('node:test'),assert=require('node:assert/strict');
const {JSDOM}=require('jsdom');
const {sectionDiagram,diagramSvg,diagramFocusBounds}=require('../../packages/full-report/schematics');
const {fullReportHtml,fullReportSchemesHtml}=require('../../packages/full-report');
const fixture=require('../../docs/artifacts/full-report-fixture.json').report;
const section=id=>fixture.sections.find(s=>s.id===id);
const parse=svg=>new JSDOM(svg,{contentType:'image/svg+xml'}).window.document;
const copy=()=>structuredClone(fixture);

test('every current calculated section has a serializable diagram without changing its snapshot',()=>{
 const original=JSON.stringify(fixture);
 for(const s of fixture.sections){
  const d=sectionDiagram(fixture,s);assert.ok(d,s.id);assert.deepEqual(JSON.parse(JSON.stringify(d)),d);
  const svg=diagramSvg(d);assert.ok(parse(svg).documentElement);assert.equal(parse(svg).querySelector('parsererror'),null);
 }
 assert.equal(JSON.stringify(fixture),original);
});

test('author square retains the 147/258/369 positions, actual repeats and counts',()=>{
 const d=sectionDiagram(fixture,section('square')),doc=parse(diagramSvg(d));
 assert.deepEqual(d.cells.map(c=>c.digit),[1,4,7,2,5,8,3,6,9]);
 assert.deepEqual(d.cells.map(c=>c.digits),fixture.raw.scheme.cells.map(c=>c.digits));
 assert.deepEqual(d.cells.map(c=>c.count),fixture.raw.scheme.cells.map(c=>c.count));
 const two=doc.querySelector('[data-cell="2"]');assert.match(two.textContent,/22222/);assert.match(two.textContent,/кол-во 5/);
 assert.equal(doc.querySelectorAll('[data-cell]').length,9);
 assert.equal(doc.querySelector('[data-cell="7"]').textContent.includes('—'),true);
});

test('all eight directions expose saved totals simultaneously and highlight the selected route',()=>{
 const d=sectionDiagram(fixture,section('lines'));
 assert.deepEqual(d.directions.map(v=>v.value),fixture.raw.scheme.lines.map(v=>v.value));
 for(let activeIndex=0;activeIndex<8;activeIndex++){
  const doc=parse(diagramSvg(d,{activeIndex}));
  assert.equal(doc.querySelectorAll('[data-direction]').length,8);assert.equal(doc.querySelectorAll('[data-legend]').length,8);
  assert.equal(doc.querySelector('[data-direction][data-active="true"]').getAttribute('data-direction'),d.directions[activeIndex].id);
  assert.match(doc.querySelector(`[data-legend="${d.directions[activeIndex].id}"]`).textContent,new RegExp('= '+d.directions[activeIndex].value+'$'));
 }
 assert.deepEqual(d.directions[6].digits,[1,5,9]);assert.deepEqual(d.directions[7].digits,[3,5,7]);
});

test('vedic yantra uses its own date-only cells and counts planets per line rather than Pythagorean totals',()=>{
 const square=sectionDiagram(fixture,section('square')),yantra=sectionDiagram(fixture,section('vedic-yantra')),vedic=sectionDiagram(fixture,section('vedic-lines'));
 assert.equal(yantra.cells.find(c=>c.digit===2).count,1);assert.equal(square.cells.find(c=>c.digit===2).count,5);
 const sums=fixture.raw.vedic.yantra.yantra_sums;
 assert.deepEqual(vedic.directions.map(v=>v.value),[...sums.horizontal,...sums.vertical,...sums.diagonal]);
 assert.equal(vedic.directions[1].value,2);assert.notEqual(vedic.directions[1].value,fixture.raw.scheme.lines[1].value);
 const altered=copy();altered.raw.scheme.lines[1].value=77;
 assert.equal(sectionDiagram(altered,section('lines')).directions[1].value,77,'read the saved total without recomputing');
 assert.equal(sectionDiagram(altered,section('vedic-lines')).directions[1].value,2);
});

test('personal diagram follows author plate positions and never invents name-derived wisdom',()=>{
 const d=sectionDiagram(fixture,section('personal')),doc=parse(diagramSvg(d));
 for(const name of ['Ч/Д','Ч/У','Ч/С','Ч/У*','П/Ч','Ч/М'])assert.ok(doc.documentElement.textContent.includes(name),name);
 assert.match(doc.documentElement.textContent,/Нужно имя/);
 assert.equal(d.entries.find(e=>e.id==='helping_mind').value,11);
 assert.equal(d.entries.find(e=>e.id==='ruling').value,22);
 assert.equal(d.entries.some(e=>e.id==='wisdom'),false);
});

test('fractal, tasks, individual numbers and every period preserve the stored values and bounds',()=>{
 const f=sectionDiagram(fixture,section('fractal'));
 assert.deepEqual(f.entries.map(e=>e.value),[1,2,3,4].map(i=>fixture.raw.fractal['digit'+i]));
 const tasks=sectionDiagram(fixture,section('tasks'));assert.equal(tasks.entries[0].value,0);assert.match(tasks.entries[0].detail,/32–41/);assert.equal(tasks.entries[2].detail,'На протяжении жизни');
 const individual=sectionDiagram(fixture,section('individual'));assert.deepEqual(individual.entries.map(e=>e.value),['chig','chim','chid','chpg','chpm','chpd'].map(k=>fixture.raw.individual[k].value));
 for(const period of fixture.raw.cycles.periods){
  const d=sectionDiagram(fixture,section('cycle-period-'+period.index));
  assert.deepEqual(d.entries.map(e=>e.value),[period.shadow,period.peak,period.challenge,period.transition]);
  assert.deepEqual(d.years,period.years.map(y=>({age:y.age,year:y.year,value:y.chlg})));
  assert.deepEqual(d.bounds,{start:period.startAge,end:period.endAge});
 }
});

test('100-year series and seven planet strengths are retained as actual graph data',()=>{
 const years=sectionDiagram(fixture,section('cycles')),planets=sectionDiagram(fixture,section('planets'));
 assert.equal(years.years.length,100);assert.equal(parse(diagramSvg(years)).querySelector('[data-series]').getAttribute('data-series'),'100');
 assert.deepEqual(planets.entries.map(e=>[e.label,e.value]),section('planets').values.map(v=>[v.label,v.value]));
 assert.equal(planets.entries.length,7);
 assert.equal(parse(diagramSvg(years,{activeIndex:43})).querySelector('[data-active-year]').getAttribute('data-active-year'),'44');
});

test('optional video focus bounds remain inside the complete original diagram',()=>{
 for(const [id,count] of [['personal',7],['square',9],['lines',8],['tasks',4]]){
  const d=sectionDiagram(fixture,section(id));
  for(let index=0;index<count;index++){
   const bounds=diagramFocusBounds(d,index);assert.ok(bounds,id+':'+index);
   assert.ok(bounds.x>=0&&bounds.y>=0&&bounds.x+bounds.width<=d.width&&bounds.y+bounds.height<=d.height);
  }
  assert.equal(diagramFocusBounds(d,-1),null);assert.equal(diagramFocusBounds(d,99),null);
 }
});

test('legacy reports and narrative synthesis gracefully retain text and chart fallback',()=>{
 const legacy=copy();delete legacy.raw;assert.equal(sectionDiagram(legacy,section('square')),null);
 const synthesis={id:'synthesis',title:'Синтез',paragraphs:['Вывод из сохранённого разбора'],method:'',steps:[],values:[{label:'Практика',value:null,meaning:'Наблюдать конкретный пример'}]};
 assert.equal(sectionDiagram(fixture,synthesis),null);
 const report={...fixture,sections:[synthesis,...fixture.sections]},html=fullReportHtml({order_id:'a'.repeat(64),status:'paid',mode:'test',amount_total:666,currency:'eur',birth_date:report.birth_date,as_of_date:report.as_of_date,report});
 assert.match(html,/Наблюдать конкретный пример/);
});

test('SVG escapes every text value and forbids external resources or executable nodes',()=>{
 const d=sectionDiagram(fixture,section('fractal'));d.title='<script>alert(1)</script>';d.subtitle='<image href="https://bad.example"/>';d.entries[0].label='"><foreignObject onload="boom">';
 const svg=diagramSvg(d),doc=parse(svg);
 assert.equal(doc.querySelectorAll('script,foreignObject,image,a,style').length,0);
 assert.equal([...doc.querySelectorAll('*')].some(el=>[...el.attributes].some(a=>/^on/i.test(a.name)||/href$/i.test(a.name))),false);
 assert.ok(doc.documentElement.textContent.includes('<script>alert(1)</script>'));
 assert.throws(()=>diagramSvg({...d,kind:'html'}));assert.throws(()=>diagramSvg(d,{width:NaN}));assert.throws(()=>diagramSvg(d,{height:'100%'}));
});

test('viewBox preserves complete geometry at mobile and video sizes; PDF keeps every table result',()=>{
 for(const id of ['personal','lines','vedic-lines','fractal','cycle-period-4']){
  const d=sectionDiagram(fixture,section(id));
  for(const [width,height] of [[320,d.height/2],[1280,720]]){
   const svg=parse(diagramSvg(d,{width,height})).documentElement;
   assert.equal(svg.getAttribute('viewBox'),`0 0 ${d.width} ${d.height}`);assert.equal(svg.getAttribute('preserveAspectRatio'),'xMidYMid meet');
  }
 }
 const doc=new JSDOM(fullReportHtml({order_id:'a'.repeat(64),status:'paid',mode:'test',amount_total:666,currency:'eur',birth_date:fixture.birth_date,as_of_date:fixture.as_of_date,report:fixture})).window.document;
 assert.equal(doc.querySelectorAll('.report-schematic svg').length,fixture.sections.length);
 const expected=fixture.sections.reduce((n,s)=>n+s.values.length,0),tableRows=doc.querySelectorAll('section>table>tbody>tr').length;
 assert.equal(tableRows,expected);assert.ok(doc.body.textContent.includes('100 лет · 2082'));
});

test('PDF summary lists potentials and points of attention with their basis; malformed lists are refused',()=>{
 const report={...copy(),highlights:[{id:'potentials',title:'Ваши потенциалы',items:[{text:'Ясное намерение <b>растёт</b> в делах.',basis:'Личные числа — Число души: 1'}]},
  {id:'attention',title:'На что обратить внимание',items:[{text:'Замечайте лишнюю строгость к себе.',basis:'Квадрат — Цифра 1: 111'}]}]};
 const order={order_id:'a'.repeat(64),status:'paid',mode:'test',amount_total:666,currency:'eur',birth_date:fixture.birth_date,as_of_date:fixture.as_of_date,report};
 const summary=new JSDOM(fullReportHtml(order)).window.document.querySelector('section');
 assert.deepEqual([...summary.querySelectorAll('h3')].map(h=>h.textContent),['Ваши потенциалы','На что обратить внимание']);
 assert.match(summary.textContent,/Ясное намерение <b>растёт<\/b> в делах\.Основание в расчёте: Личные числа — Число души: 1/);
 assert.throws(()=>fullReportHtml({...order,report:{...report,highlights:[{title:'x',items:[{text:'y'}]}]}}),/Главное в разборе/);
 assert.ok(fullReportHtml({...order,report:copy()}).includes('Главное в вашем разборе'));
});

test('short report keeps every scheme and chart but no explanation, formula or interpretation',()=>{
 const report={...copy(),highlights:[{id:'potentials',title:'Ваши потенциалы',items:[{text:'Потенциал без места в кратком отчёте.',basis:'Личные числа'}]}]};
 const order={order_id:'a'.repeat(64),status:'paid',mode:'test',amount_total:666,currency:'eur',birth_date:fixture.birth_date,as_of_date:fixture.as_of_date,report};
 const html=fullReportSchemesHtml(order),doc=new JSDOM(html).window.document,text=doc.body.textContent;
 assert.equal(doc.querySelectorAll('.report-schematic svg').length,fixture.sections.filter(s=>sectionDiagram(fixture,s)).length);
 for(const s of fixture.sections){
  for(const p of s.paragraphs)assert.ok(!text.includes(p),p.slice(0,40));
  for(const step of s.steps)assert.ok(!text.includes(step),step.slice(0,40));
  for(const v of s.values)if(v.meaning.length>30)assert.ok(!text.includes(v.meaning.slice(0,30)),v.meaning.slice(0,30));
 }
 assert.ok(!text.includes('Потенциал без места')&&!text.includes('Главное в вашем разборе'));
 assert.ok(text.includes('Краткий отчёт: схемы и графики')&&text.includes(fixture.birth_date)&&text.includes('Тестовый отчёт'));
 // A 100-year chart without its 100-row table.
 assert.equal(doc.querySelectorAll('.series-table').length,0);
});

test('the plate shows Ч/М once the report holds the wisdom number from the entered name',()=>{
 const plain=diagramSvg(sectionDiagram(fixture,section('personal')));
 assert.ok(plain.includes('Нужно имя'));
 const named=copy();named.sections[0].values.push({label:'Число мудрости',value:5,meaning:'',key:'wisdom'},{label:'Полное число имени',value:1,meaning:'',key:'full_name'});
 const d=sectionDiagram(named,named.sections[0]),svg=diagramSvg(d);
 assert.ok(!svg.includes('Нужно имя'));assert.ok(svg.includes('data-node="wisdom"'));
 assert.deepEqual(diagramFocusBounds(d,7),{x:208,y:506,width:224,height:122});
});
