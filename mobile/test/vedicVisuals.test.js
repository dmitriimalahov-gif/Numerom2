const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {execFileSync}=require('node:child_process');
const fixture=require('./fixtures/vedicReport.json');
const visuals=require('../src/lib/vedicVisuals');
const {VEDIC_PLANETS,localTimeLabel,planetSeriesModel,solarWheelModel,periodTimelineModel}=visuals;
const clone=value=>structuredClone(value);
const close=(a,b)=>assert.ok(Math.abs(a-b)<.00001,`${a} != ${b}`);
function routeDays(count){return Array.from({length:count},(_,i)=>({...clone(fixture.days[i%7]),date:new Date(Date.UTC(2026,9,18+i)).toISOString().slice(0,10)}));}
function solarDay({date='2026-10-18',before=null,after=null,transition=null}={}) {
  const day={...clone(fixture.days[0]),date,sunrise:'07:00',sunset:'19:00'};
  const next=new Date(Date.parse(date+'T00:00:00Z')+86400000).toISOString().slice(0,10);
  const suffix=value=>value===null?'Z':`+${String(value).padStart(2,'0')}:00`;
  const start=Date.parse(date+'T07:00:00'+suffix(before)),sunset=Date.parse(date+'T19:00:00'+suffix(before)),end=Date.parse(next+'T07:00:00'+suffix(after));
  const stamp=value=>{
    if(before===null)return new Date(value).toISOString().slice(0,19);
    const offset=transition&&value>=Date.parse(transition)?after:before;
    return new Date(value+offset*3600000).toISOString().slice(0,19)+suffix(offset);
  };
  const boundaries=Array.from({length:25},(_,i)=>i<=12?start+(sunset-start)*i/12:sunset+(end-sunset)*(i-12)/12);
  const order=['surya','chandra','mangal','budha','guru','shukra','shani'];
  day.hours=Array.from({length:24},(_,i)=>({hour:i+1,planet:order[i%7],title:VEDIC_PLANETS.find(p=>p.key===order[i%7]).title,start:stamp(boundaries[i]),end:stamp(boundaries[i+1]),period:i<12?'day':'night'}));
  return day;
}

test('all nine planet series retain the exact 1/7/30/90-day values with a genuine single-day point',()=>{
  for(const count of [1,7,30,90])for(const planet of VEDIC_PLANETS){
    const days=routeDays(count),model=planetSeriesModel(days,planet.key,{width:234});
    assert.equal(model.points.length,count);
    assert.deepEqual(model.points.map(p=>p.value),days.map(d=>d.energies.find(e=>e.key===planet.key).value));
    assert.ok(model.points.every(p=>p.x>=model.left&&p.x<=model.right&&p.y>=model.top&&p.y<=model.bottom));
    assert.ok(model.dateTicks.length<=3);
    assert.ok(model.dateTicks.slice(1).every((tick,i)=>tick.x-model.dateTicks[i].x>=40),'date labels must not overlap at320px');
    if(count===1){assert.equal(model.points[0].x,(model.left+model.right)/2);assert.equal(model.segments.length,0);assert.equal(model.dateTicks.length,1);}
  }
});
test('zero and hundred are exact boundaries; missing days break a line instead of becoming zero or averages',()=>{
  const days=routeDays(5);days.forEach(d=>{d.average=999;});
  days[0].energies[0].value=0;days[1].energies[0].value=100;days[2].energies[0].value=null;
  const model=planetSeriesModel(days,'surya');
  assert.equal(model.points[0].y,model.bottom);assert.equal(model.points[1].y,model.top);
  assert.equal(model.segments.length,2);assert.deepEqual(model.missingDates,[days[2].date]);
  assert.equal(model.points.some(p=>p.index===2),false);
  assert.equal(planetSeriesModel([{...days[0],energies:[]}],'surya'),null);
  assert.equal(planetSeriesModel([days[0],days[0]],'surya'),null);
  assert.equal(planetSeriesModel(days,'unknown'),null);
});
test('wheel follows 24 saved boundaries to the next sunrise and retains the original hour numbers',()=>{
  const day=solarDay(),model=solarWheelModel(day,{size:234});
  assert.equal(model.segments.length,24);assert.equal(model.timeBasis,'local-wall-clock');
  assert.deepEqual(model.segments.map(s=>s.hour),Array.from({length:24},(_,i)=>i+1));
  assert.equal(model.segments[0].startAngle,0);assert.equal(model.segments[23].endAngle,360);
  assert.equal(model.startLabel,'07:00');assert.equal(model.endLabel,'07:00');
  assert.equal(model.segments[23].endDate,'2026-10-19');assert.equal(model.segments[23].nextDate,true);
  assert.ok(model.segments.every(s=>s.path.startsWith('M ')&&!/NaN|undefined/.test(s.path)));
  assert.ok(model.markers.every(m=>Math.hypot(m.labelX-model.cx,m.labelY-model.cy)>model.innerRadius));
  assert.equal(solarWheelModel({...day,hours:day.hours.slice(1)}),null);
  const gap=clone(day);gap.hours[3].start=gap.hours[2].start;assert.equal(solarWheelModel(gap),null);
  const wrongBoundary=clone(day);wrongBoundary.sunset='20:00';assert.equal(solarWheelModel(wrongBoundary),null);
});
test('DST uses actual elapsed time with offsets while preserving city labels and repeated local hours',()=>{
  const spring=solarDay({date:'2026-03-28',before:2,after:3,transition:'2026-03-29T01:00:00Z'});
  const fall=solarDay({date:'2026-10-24',before:3,after:2,transition:'2026-10-25T01:00:00Z'});
  for(const [day,total] of [[spring,1380],[fall,1500]]){
    const model=solarWheelModel(day);assert.ok(model);assert.equal(model.timeBasis,'elapsed');
    assert.equal(model.segments[23].endMinute,total);assert.equal(model.startLabel,'07:00');assert.equal(model.endLabel,'07:00');
    for(const segment of model.segments){assert.ok(segment.endMinute>segment.startMinute);close(segment.endAngle-segment.startAngle,(segment.endMinute-segment.startMinute)/total*360);}
  }
  const repeated=solarWheelModel(fall).segments.find(s=>s.startLabel.startsWith('03:')&&s.endLabel.startsWith('03:'));
  assert.ok(repeated);close(repeated.endMinute-repeated.startMinute,65);
  const mixed=clone(fall);mixed.hours[0].start=mixed.hours[0].start.slice(0,19);assert.equal(solarWheelModel(mixed),null);
});
test('times and wheel geometry do not change with the device timezone',()=>{
  assert.equal(localTimeLabel('2026-10-25T03:45:00+02:00'),'03:45');assert.equal(localTimeLabel('07:26'),'07:26');assert.equal(localTimeLabel('25:00'),'—');
  const day=solarDay({date:'2026-10-24',before:3,after:2,transition:'2026-10-25T01:00:00Z'});
  const script="const m=require('./src/lib/vedicVisuals');process.stdout.write(JSON.stringify(m.solarWheelModel(JSON.parse(process.env.VEDIC_TEST_DAY))))";
  const outputs=['UTC','Pacific/Honolulu','Asia/Tokyo'].map(TZ=>execFileSync(process.execPath,['-e',script],{cwd:path.resolve(__dirname,'..'),env:{...process.env,TZ,VEDIC_TEST_DAY:JSON.stringify(day)},encoding:'utf8'}));
  assert.equal(outputs[0],outputs[1]);assert.equal(outputs[1],outputs[2]);
});
test('four period bars use actual saved times, preserve overlaps and identify missing intervals',()=>{
  const day=clone(fixture.days[0]),model=periodTimelineModel(day,{width:234});
  assert.equal(model.rows.length,4);assert.equal(model.startLabel,'07:26');assert.equal(model.endLabel,'18:11');
  const first=model.rows.find(r=>r.id==='gulika_kaal');assert.equal(first.x,model.left);
  const rahu=model.rows.find(r=>r.id==='rahu_kaal');close(rahu.width,(80/645)*(model.right-model.left));
  assert.ok(model.rows.every(r=>r.x>=0&&r.x+r.width<=model.width&&r.y+r.height<=model.height));
  const overlap=periodTimelineModel(fixture.days[4]);assert.equal(overlap.rows[0].x,overlap.rows[1].x);assert.notEqual(overlap.rows[0].y,overlap.rows[1].y);
  day.periods[0].start='bad';const partial=periodTimelineModel(day);assert.equal(partial.rows.length,3);assert.deepEqual(partial.missingIds,['rahu_kaal']);
  assert.equal(periodTimelineModel({...day,sunrise:''}),null);
});
test('all shared presentation models leave frozen receipt data untouched',()=>{
  const day=solarDay();function freeze(value){if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;}
  freeze(day);const before=JSON.stringify(day);planetSeriesModel([day],'surya');solarWheelModel(day);periodTimelineModel(day);assert.equal(JSON.stringify(day),before);
});

// Render the real TSX, including VedicResult, with native primitives mocked only.
function renderer(exportName,props,{feature=false}={}) {
  const React=require('react'),{renderToStaticMarkup}=require('react-dom/server'),ts=require('typescript');
  const state=[];let hook=0,buttons=[];
  const native=tag=>p=>{if(tag==='button')buttons.push(p);return React.createElement(tag,{role:p.accessibilityRole,'aria-label':p.accessibilityLabel,'aria-selected':p.accessibilityState?.selected,'data-testid':p.testID,disabled:p.disabled},p.children);};
  const svg=tag=>({children,accessible,accessibilityElementsHidden,...p})=>React.createElement(tag,p,children);
  const react={...React,useState:initial=>{const i=hook++;if(!(i in state))state[i]=typeof initial==='function'?initial():initial;return[state[i],value=>{state[i]=typeof value==='function'?value(state[i]):value;}];}};
  const primitives={View:native('div'),Text:native('span'),Pressable:native('button'),ScrollView:native('div'),StyleSheet:{create:s=>s,absoluteFill:{position:'absolute',inset:0}}};
  const Button=({title,onPress,disabled})=>React.createElement(primitives.Pressable,{accessibilityRole:'button',accessibilityLabel:title,onPress,disabled},title);
  const ui={Button,s:{},Card:primitives.View,Heading:({title})=>React.createElement('h2',null,title),Notice:({message})=>React.createElement('p',null,message),Screen:primitives.View,Loading:()=>null};
  const dependencies={react,'react/jsx-runtime':require('react/jsx-runtime'),'react-native':primitives,'react-native-svg':{__esModule:true,default:svg('svg'),Circle:svg('circle'),G:svg('g'),Line:svg('line'),Path:svg('path'),Polyline:svg('polyline'),Rect:svg('rect'),Text:svg('text')},
    '../ui':ui,'../components/ui':ui,'../../lib/vedicVisuals':visuals,'../lib/vedicVisuals':visuals,
    '../lib/vedicCalculations':require('../src/lib/vedicCalculations'),'expo-router':{router:{push(){},replace(){}}},'../lib/theme':{colors:{}},
    '../components/SavedReportExport':{SavedReportExport:()=>React.createElement('span',null,'Экспорт сохранённого результата')},'../lib/supplementalReportExport':{vedicDocument:()=>({})},
    '../components/audio/Narration':{NarrationClip:({id})=>React.createElement('span',{'data-narration':id})},
    '../components/numbers/InterpretationSheet':{InterpretationSheet:({detail})=>detail?React.createElement('span',{'data-knowledge':detail.knowledgeDigit},`${detail.title}: ${detail.value}`):null},
    '../lib/session':{},'../lib/pendingCalculationStorage':{},'../lib/learning':{},'../components/LocationField':{},
  };
  function load(relative){const module={exports:{}},filename=path.resolve(__dirname,relative);const output=ts.transpileModule(fs.readFileSync(filename,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText;
    vm.runInNewContext(output,{exports:module.exports,require:name=>{assert.ok(name in dependencies,`Unexpected dependency: ${name}`);return dependencies[name];}});return module.exports;}
  const charts=load('../src/components/vedic/VedicVisuals.tsx');dependencies['../components/vedic/VedicVisuals']=charts;
  const Component=feature?load('../src/features/VedicTime.tsx')[exportName]:charts[exportName];
  return {render(){hook=0;buttons=[];return renderToStaticMarkup(Component(props));},get buttons(){return buttons;}};
}
test('single-day component really renders one point and changing a planet retains interpretation callback',()=>{
  let picked=null;const day=solarDay();day.energies[0].value=0;
  const view=renderer('PlanetRouteChart',{days:[day],index:0,onDay(){},onInterpret:energy=>{picked=energy;}});
  const html=view.render();assert.match(html,/<svg /);assert.equal((html.match(/<circle /g)||[]).length,1);assert.doesNotMatch(html,/<polyline /);
  assert.match(html,/Солнце: 0/);
  const moon=view.buttons.find(b=>b.accessibilityLabel?.startsWith('Луна:'));moon.onPress();
  const next=view.render();assert.match(next,/Смысл и озвучка: Луна/);
  view.buttons.find(b=>b.accessibilityLabel==='Смысл и озвучка: Луна').onPress();assert.equal(picked.key,'chandra');assert.equal(picked.digit,2);
});
test('real chart handler accepts native and DOM clicks without turning a 90-day selection into NaN',()=>{
  const {JSDOM}=require('jsdom'),dom=new JSDOM('<div id="overlay"></div>'),overlay=dom.window.document.getElementById('overlay');
  const days=routeDays(90),model=planetSeriesModel(days,'surya',{width:234}),chosen=[];
  const props={days,index:0,onDay(value){chosen.push(value);props.index=value;},onInterpret(){}};
  const view=renderer('PlanetRouteChart',props);view.render();
  const handler=view.buttons.find(b=>b.testID==='vedic-series-touch').onPress;
  handler({nativeEvent:{locationX:model.points[42].x}});assert.equal(chosen.at(-1),42);
  overlay.getBoundingClientRect=()=>({left:40,top:15,width:468,height:368});
  overlay.addEventListener('click',event=>handler({nativeEvent:event,currentTarget:event.currentTarget,target:event.target}));
  overlay.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true,clientX:40+model.points[69].x*2,clientY:40}));
  assert.equal(chosen.at(-1),69);assert.match(view.render(),/70 из 90 дней/);assert.doesNotMatch(view.render(),/NaN/);
  const target={};handler({nativeEvent:{offsetX:model.points[18].x,target},currentTarget:target});assert.equal(chosen.at(-1),18);
  const count=chosen.length;
  for(const event of [{nativeEvent:{}},{nativeEvent:{locationX:NaN}},{nativeEvent:{locationX:Infinity}},{nativeEvent:{offsetX:200,target:{}},currentTarget:{}},{nativeEvent:{clientX:120},currentTarget:{getBoundingClientRect:()=>({left:0,width:0})}}])handler(event);
  assert.equal(chosen.length,count);assert.ok(chosen.every(Number.isInteger));
  dom.window.close();
});
test('real wheel handler selects a sector from DOM client coordinates and ignores missing coordinates',()=>{
  const day=solarDay(),model=solarWheelModel(day,{size:234}),view=renderer('SolarDayWheel',{day,timezone:'Europe/Chisinau'});view.render();
  const handler=view.buttons.find(b=>b.testID==='vedic-wheel-touch').onPress,target=model.segments[15];
  handler({nativeEvent:{clientX:50+target.labelX,clientY:80+target.labelY},currentTarget:{getBoundingClientRect:()=>({left:50,top:80,width:234,height:234})}});
  assert.match(view.render(),/Час 16/);
  handler({nativeEvent:{locationX:NaN,locationY:undefined}});assert.match(view.render(),/Час 16/);
});
test('period and wheel native buttons select visible explanations and all 24 hours remain accessible',()=>{
  const day=solarDay(),periods=renderer('DayPeriodTimeline',{day,timezone:'Europe/Chisinau'});periods.render();
  const button=periods.buttons.find(b=>b.accessibilityLabel?.startsWith('Абхиджит'));button.onPress();assert.match(periods.render(),/Самое благоприятное время/);
  const wheel=renderer('SolarDayWheel',{day,timezone:'Europe/Chisinau'});wheel.render();
  const hours=wheel.buttons.filter(b=>b.accessibilityLabel?.startsWith('Час '));assert.equal(hours.length,24);
  hours[23].onPress();assert.match(wheel.render(),/Час 24/);assert.match(wheel.render(),/19\.10\.2026/);
  for(const item of hours){const style=Object.assign({},...item.style.filter(Boolean));assert.ok(style.minHeight>=44);assert.ok(style.minWidth>=44);}
});
test('real VedicResult renders schedule without energies and daily data without losing cost, export or narration',()=>{
  for(const kind of ['schedule','daily']){
    const day=solarDay();if(kind==='schedule'){day.energies=[];day.average=null;}
    const results={...clone(fixture),kind,end_date:day.date,days:[day],narration_id:`vedic-${kind}`};
    const receipt={id:'a'.repeat(64),request_id:'cc225a20-0b98-4b21-8987-558da94c4b8f',created_at:'2026-10-18T11:00:00Z',cost:1,results};
    const html=renderer('VedicResult',{receipt},{feature:true}).render();
    assert.match(html,/Круг 24 планетарных часов/);assert.match(html,/Четыре периода дня/);
    assert.match(html,/Стоимость: 1 балл/);assert.match(html,/Экспорт сохранённого результата/);assert.match(html,new RegExp(`data-narration="vedic-${kind}"`));
    assert.equal(html.includes('Ритм девяти планет'),kind==='daily');
  }
  // The route states the wisdom number it used; receipts saved before 24.10.2026 have no note and show none.
  const note='Число мудрости 5 = судьба 4 + полное число имени 1; учтено в показателях планет.';
  const receipt={id:'a'.repeat(64),request_id:'cc225a20-0b98-4b21-8987-558da94c4b8f',created_at:'2026-10-18T11:00:00Z',cost:1,results:{...clone(fixture),days:[solarDay()],wisdom_note:note}};
  assert.ok(renderer('VedicResult',{receipt},{feature:true}).render().includes(note));
  assert.ok(!renderer('VedicResult',{receipt:{...receipt,results:{...receipt.results,wisdom_note:undefined}}},{feature:true}).render().includes('Число мудрости'));
});
