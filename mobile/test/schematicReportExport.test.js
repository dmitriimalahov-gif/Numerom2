const {test}=require('node:test'),assert=require('node:assert/strict');
const {JSDOM}=require('jsdom');
const {nameSchemes}=require('../../packages/numerology-core/name-schemes');
const {nameSchemeVisuals}=require('../src/lib/nameSchemeVisuals');
const {planetSeriesModel,periodTimelineModel}=require('../src/lib/vedicVisuals');
const {nameSchematicHtml}=require('../src/lib/schematicReportExport');
const {comprehensiveHtml,vedicDocument}=require('../src/lib/supplementalReportExport');
const fixture=require('./fixtures/vedicReport.json');
const input={createdAt:'2026-10-18T00:00:00Z',report:{birthDate:'10.01.1982',profileParts:{name:'Anna',surname:'Petrova'},numbers:[{key:'soul',value:1},{key:'mind',value:1},{key:'destiny',value:4}]}};
test('personal export contains vector name schemes with every model node and original connection',()=>{
 const data=nameSchemes(input.report.profileParts,input.report.birthDate),models=nameSchemeVisuals(data);
 const dom=new JSDOM(comprehensiveHtml(input));
 for(const kind of ['triangle','human']){
  const model=models[kind],svg=dom.window.document.querySelector(`svg[data-scheme="${kind}"]`);
  assert.ok(svg,kind);assert.equal(svg.getAttribute('viewBox'),`0 0 ${model.width} ${model.height}`);
  assert.equal(svg.querySelectorAll('[data-node]').length,model.nodes.length);
  assert.equal(svg.querySelectorAll('line').length,model.edges.length);
  for(const node of model.nodes){const el=svg.querySelector(`[data-node="${node.id}"]`);assert.equal(Number(el.querySelector('circle').getAttribute('cx')),node.x);assert.equal(Number(el.querySelector('circle').getAttribute('cy')),node.y);assert.ok(el.textContent.includes(String(node.value)));assert.ok(el.getAttribute('aria-label').includes(node.formula));}
  assert.ok(dom.window.document.querySelector(`svg[data-scheme="${kind}-chart"]`));
 }
 assert.equal(models.triangle.nodes.length,45);assert.equal(models.human.nodes.length,7);dom.window.close();
});
test('every planetary graph exports exact saved daily values including zero and90days without selected UI filters',()=>{
 const r=structuredClone(fixture);r.days=Array.from({length:90},(_,i)=>{const d=structuredClone(fixture.days[i%7]);d.date=new Date(Date.UTC(2026,9,18+i)).toISOString().slice(0,10);return d;});r.days[0].energies[0].value=0;r.end_date=r.days.at(-1).date;
 const before=JSON.stringify(r),dom=new JSDOM(vedicDocument({results:r,created_at:input.createdAt}));
 assert.equal(dom.window.document.querySelectorAll('svg[data-scheme^="planet-"]').length,9);
 for(const energy of r.days[0].energies){const g=planetSeriesModel(r.days,energy.key,{width:580,height:190}),svg=dom.window.document.querySelector(`svg[data-scheme="planet-${energy.key}"]`);assert.equal(svg.querySelectorAll('[data-date]').length,90);for(const point of g.points){const el=svg.querySelector(`[data-date="${point.date}"]`);assert.equal(Number(el.getAttribute('data-value')),point.value);assert.equal(Number(el.getAttribute('cy')),point.y);}}
 assert.equal(dom.window.document.querySelectorAll('svg[data-scheme="day-periods"]').length,90);assert.equal(JSON.stringify(r),before);dom.window.close();
});
test('solar day export renders supplied intervals and schedule has no invented personal graphs',()=>{
 const r=structuredClone(fixture);r.kind='schedule';r.days=r.days.slice(0,1);const d=r.days[0];d.energies=[];d.average=null;d.sunrise='06:00';d.sunset='18:00';d.periods=[];
 d.hours=Array.from({length:24},(_,i)=>({hour:i+1,planet:'surya',title:'Солнце',period:i<12?'day':'night',start:new Date(Date.UTC(2026,9,18,6+i)).toISOString(),end:new Date(Date.UTC(2026,9,18,7+i)).toISOString()}));
 const dom=new JSDOM(vedicDocument({results:r,created_at:input.createdAt}));
 assert.equal(dom.window.document.querySelectorAll('svg[data-scheme="solar-hours"] [data-hour]').length,24);assert.equal(dom.window.document.querySelectorAll('svg[data-scheme^="planet-"]').length,0);dom.window.close();
});
test('time diagrams retain original timezone strings and exported contents cannot become markup',()=>{
 const r=structuredClone(fixture),attack='<img src="https://attacker.invalid" onerror="alert(1)">';r.city=attack;r.days[0].periods[0].title=attack;
 const dom=new JSDOM(vedicDocument({results:r,created_at:input.createdAt}));
 assert.equal(dom.window.document.querySelectorAll('img,script,iframe,a,foreignObject').length,0);assert.ok(dom.window.document.body.textContent.includes(attack));
 const g=periodTimelineModel(r.days[0],{width:580});assert.ok(dom.window.document.body.textContent.includes(g.startLabel));
 assert.equal(dom.window.document.querySelector('[data-period="rahu_kaal"]').getAttribute('x'),String(g.rows.find(v=>v.id==='rahu_kaal').x));
 assert.doesNotMatch(dom.serialize(),/NaN|undefined|Infinity/);dom.window.close();
 const missing=new JSDOM(nameSchematicHtml({available:false,note:attack},'triangle'));assert.equal(missing.window.document.querySelectorAll('img,svg').length,0);assert.equal(missing.window.document.body.textContent,attack);missing.window.close();
});

test('legacy UTC saved timestamps remain UTC in a differently zoned process',()=>{
 const {execFileSync}=require('node:child_process');
 const script=`const {document}=require(${JSON.stringify(require.resolve('../src/lib/savedReportExport'))});process.stdout.write(document('Test','2026-10-18T00:00:00',''));`;
 const html=execFileSync(process.execPath,['-e',script],{env:{...process.env,TZ:'Europe/Chisinau'}}).toString();
 assert.match(html,/18\.10\.2026, 00:00:00/);
});
