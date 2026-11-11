const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {personalReport, savedPersonalResult, calculationPrice, calculationBlock, createPersonalCalculationController} = require('../src/lib/personalReport');
const fields = ['soul_number','mind_number','destiny_number','helping_mind_number','wisdom_number','ruling_number','full_name_number'];
function fixture(date = '10.01.1982') {
  const values = [5,8,1,3,7,2,4];
  const result = Object.fromEntries(fields.map((key,index) => [key,values[index]]));
  result.report = {version:1,birth_date:date,birth_weekday:'Воскресенье',profile_name:'Test Person',
    numbers:fields.map((key,index) => ({key,title:index === 0 ? 'Число души' : key,value:values[index],meaning:`Смысл ${key}`,interpretation:`Расшифровка ${values[index]} для ${key}`,method:`Метод ${key}`,steps:['Первый серверный шаг','Второй серверный шаг'],note:null})),
    planets:{formula:'Серверное объяснение формулы',calculation_number:5,birth_weekday:'Воскресенье',note:'Серверное примечание',items:['Солнце','Луна','Марс','Меркурий','Юпитер','Венера','Сатурн'].map((name,index) => ({name,value:index,meaning:`Смысл ${name}`}))}};
  return result;
}
const saved = (date = '10.01.1982') => ({calculation:{id:'saved-1',birth_date:date,created_at:'2026-10-16T12:00:00Z',results:fixture(date)}});
const deferred = () => {let resolve,reject;const promise = new Promise((yes,no) => {resolve=yes;reject=no;});return {promise,resolve,reject};};
function controller(options = {}) {return createPersonalCalculationController({latest:async()=>saved(),calculate:async date=>fixture(date),refreshBalance:async()=>{},...options});}

test('report retains exact server values, meaning, interpretation and ordered steps', () => {
  const report = personalReport(fixture(),'10.01.1982');
  assert.equal(report.incomplete,false);assert.equal(report.numbers.length,7);
  assert.equal(report.numbers[0].interpretation,'Расшифровка 5 для soul_number');
  assert.deepEqual(report.numbers[0].steps,['Первый серверный шаг','Второй серверный шаг']);
  assert.equal(report.planets.items[0].value,0);assert.equal(report.planets.formula,'Серверное объяснение формулы');
});
test('legacy and malformed details retain only received numbers with honest missing metadata', () => {
  const old = fixture();delete old.report;old.wisdom_number=null;delete old.full_name_number;
  const report = personalReport(old,'10.01.1982');
  assert.equal(report.incomplete,true);assert.equal(report.planets,null);
  assert.equal(report.numbers[4].value,null);assert.equal(report.numbers[6].value,null);
  assert.ok(report.numbers.every(item=>!item.meaning && !item.interpretation && !item.method));
  const malformed=fixture();malformed.report.numbers[0].value=8;
  assert.equal(personalReport(malformed).numbers[0].value,5);
  assert.equal(personalReport(malformed).numbers[0].interpretation,'');
  malformed.report.numbers[0].value=5;malformed.report.numbers.push(malformed.report.numbers[0]);
  assert.equal(personalReport(malformed).numbers[0].detailed,false);
  assert.throws(()=>personalReport({}));
});
test('details for another date or version are not attached to a result', () => {
  const input=fixture();assert.equal(personalReport(input,'11.01.1982').numbers[0].detailed,false);
  input.report.version=2;assert.equal(personalReport(input).numbers[0].detailed,false);
});
test('planetary bars never clamp or manufacture invalid server values', () => {
  const input=fixture();input.report.planets.items[0].value=10;
  assert.equal(personalReport(input).planets,null);
  input.report.planets.items=[];input.report.planets.calculation_number=null;
  assert.equal(personalReport(input).planets.items.length,0);
  assert.equal(personalReport(input).planets.calculationNumber,null);
});
test('saved result uses its actual date and timestamp, not the profile or input draft', () => {
  const result=savedPersonalResult(saved());
  assert.equal(result.report.birthDate,'10.01.1982');assert.equal(result.createdAt,'2026-10-16T12:00:00Z');assert.equal(result.source,'saved');
  assert.equal(savedPersonalResult({calculation:null}),null);
  assert.throws(()=>savedPersonalResult({}));assert.throws(()=>savedPersonalResult({calculation:{}}));
});
test('unknown price, balance, invalid date and insufficient balance block charging', () => {
  for(const response of [{},{personal_numbers:'1'},{personal_numbers:-1},{personal_numbers:NaN},{personal_numbers:0.5}]) assert.throws(()=>calculationPrice(response));
  assert.equal(calculationPrice({personal_numbers:0}),0);
  const valid={date:'10.01.1982',price:1,balance:4};assert.equal(calculationBlock(valid),'');
  for(const delta of [{price:null},{price:0.5},{balance:undefined},{balance:0},{date:'31.02.1982'},{balanceError:'offline'},{busy:true}])assert.ok(calculationBlock({...valid,...delta}));
});
test('opening and re-opening the mounted tab loads latest once and never calculates', async () => {
  let reads=0,posts=0;const state=controller({latest:async()=>{reads++;return saved();},calculate:async()=>{posts++;return fixture();}});
  await Promise.all([state.start(),state.start()]);await state.start();assert.equal(reads,1);assert.equal(posts,0);
  assert.equal(state.getSnapshot().result.source,'saved');
  await state.reloadLatest();assert.equal(reads,2);assert.equal(posts,0);
});
test('a late latest response cannot overwrite a new successful calculation', async () => {
  const latest=deferred();const state=controller({latest:()=>latest.promise});
  const reading=state.start();await state.calculate('11.01.1982',1,5);latest.resolve(saved());await reading;
  assert.equal(state.getSnapshot().result.report.birthDate,'11.01.1982');assert.equal(state.getSnapshot().result.source,'new');
});
test('failed recalculation preserves the saved result and its date', async () => {
  const state=controller({calculate:async()=>{throw new Error('offline');}});await state.start();const before=state.getSnapshot().result;
  await state.calculate('11.01.1982',1,5);assert.equal(state.getSnapshot().result,before);assert.match(state.getSnapshot().calculationError,/Проверка бесплатна/);
});
test('rapid double tap shares exactly one paid operation', async () => {
  let calls=0;const paid=deferred();const state=controller({calculate:()=>{calls++;return paid.promise;}});
  const one=state.calculate('10.01.1982',1,5),two=state.calculate('11.01.1982',1,5);
  assert.equal(one,two);await Promise.resolve();assert.equal(calls,1);paid.resolve(fixture());await one;
  assert.equal(state.getSnapshot().result.report.birthDate,'10.01.1982');
});
test('balance refresh failure retains success; retry refreshes only balance', async () => {
  let posts=0,refreshes=0;const state=controller({calculate:async date=>{posts++;return fixture(date);},refreshBalance:async()=>{refreshes++;if(refreshes===1)throw new Error('balance offline');}});
  await state.calculate('10.01.1982',1,5);assert.ok(state.getSnapshot().result);assert.equal(state.getSnapshot().balanceError,'balance offline');
  await state.calculate('11.01.1982',1,5);assert.equal(posts,1);
  await state.refreshBalance();assert.equal(posts,1);assert.equal(refreshes,2);assert.equal(state.getSnapshot().balanceError,'');
});
test('latest failures retry independently and never become a paid calculation', async () => {
  let reads=0,posts=0;const state=controller({latest:async()=>{if(++reads===1)throw new Error('history offline');return saved();},calculate:async()=>{posts++;return fixture();}});
  await state.start();assert.match(state.getSnapshot().latestError,/offline/);await state.reloadLatest();assert.equal(state.getSnapshot().latestError,'');assert.equal(posts,0);
});
test('logout discards late replies and prevents queued work from using the next session', async () => {
  let current=true,refreshes=0;const pending=deferred();const state=controller({calculate:()=>pending.promise,isCurrent:()=>current,refreshBalance:async()=>{refreshes++;}});
  const operation=state.calculate('10.01.1982',1,5);await Promise.resolve();current=false;pending.resolve(fixture());await operation;
  assert.equal(state.getSnapshot().result,null);assert.equal(refreshes,0);
  let calls=0;current=true;const queued=controller({isCurrent:()=>current,latest:async()=>{calls++;return saved();}});
  const reading=queued.start();current=false;await reading;assert.equal(calls,0);
});

// Render the real screen and native scheme; drive the same press callbacks as the UI.
function renderedReport(result) {
  const React=require('react'),{renderToStaticMarkup}=require('react-dom/server'),ts=require('typescript');
  let hook=0,states=[],actions=new Map();
  const primitive=tag=>({children,accessibilityRole,accessibilityLabel,accessibilityState,onPress})=>{
    if(onPress && accessibilityLabel) actions.set(accessibilityLabel,onPress);
    return React.createElement(tag,{role:accessibilityRole,'aria-label':accessibilityLabel,'aria-selected':accessibilityState?.selected},children);
  };
  const deps={react:{...React,useState:initial=>{const index=hook++;if(!(index in states))states[index]=initial;return [states[index],value=>{states[index]=value;}];}},'react/jsx-runtime':require('react/jsx-runtime'),
    'react-native':{Text:primitive('span'),View:primitive('div'),Pressable:primitive('button'),ScrollView:primitive('div'),Modal:({visible,children})=>visible?React.createElement('section',{role:'dialog'},children):null,StyleSheet:{create:styles=>styles}},
    'react-native-safe-area-context':{SafeAreaView:primitive('div')},'../ui':{s:{},Button:({title,onPress})=>{actions.set(title,onPress);return React.createElement('button',null,title);}},
    '../../lib/serverDate':require('../src/lib/serverDate'),
    '../audio/Narration':{NarrationProvider:({children})=>children,NarrationClip:({id})=>React.createElement('div',null,`Объяснение раздела ${id}`)},
    './NumberStory':{NumberStory:({digit})=>React.createElement('div',{'aria-label':`История цифры ${digit}`},`Аудио цифры ${digit}`)},
    './ComprehensiveSections':{ComprehensiveSections:()=>null},'./ExportReport':{ExportReport:()=>React.createElement('button',null,'Экспорт отчёта')},
    './PlanetCharts':{PlanetCharts:({planets})=>React.createElement('div',{'aria-label':'График планет'},planets.items.map(item=>React.createElement('span',{key:item.name},`${item.name}: ${item.value}`)))}};
  function load(filename){
    const mod={exports:{}};
    vm.runInNewContext(ts.transpileModule(fs.readFileSync(filename,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{exports:mod.exports,require:name=>{
      if(name in deps)return deps[name];
      if(['./PersonalScheme','./InterpretationSheet'].includes(name))return load(path.resolve(path.dirname(filename),name+'.tsx'));
      throw new Error(`Unexpected dependency ${name}`);
    }});return mod.exports;
  }
  const component=load(path.resolve(__dirname,'../src/components/numbers/PersonalReport.tsx')).PersonalReport;
  const render=()=>{hook=0;actions.clear();return renderToStaticMarkup(React.createElement(component,{result,onProfile:()=>{}}));};
  return {render,press:label=>{assert.ok(actions.has(label),`No action: ${label}`);actions.get(label)();return render();}};
}
test('personal scheme opens exact server interpretation and formula through a free UI action', () => {
  const view=renderedReport(savedPersonalResult(saved()));const initial=view.render();
  assert.match(initial,/Ваша персональная схема/);assert.match(initial,/Сохранён:/);assert.match(initial,/График планет/);
  assert.doesNotMatch(initial,/role="dialog"/);
  const opened=view.press('Число души: 5. Открыть расшифровку');
  assert.match(opened,/role="dialog"/);assert.doesNotMatch(opened,/Смысл soul_number/);assert.match(opened,/Аудио цифры 5/);
  assert.doesNotMatch(opened,/Расшифровка 5 для soul_number/);
  assert.match(opened,/Объяснение раздела soul/);
  assert.match(opened,/Первый серверный шаг/);assert.match(opened,/Второй серверный шаг/);
  assert.ok(opened.indexOf('Первый серверный шаг')<opened.indexOf('Аудио цифры 5'));
  assert.doesNotMatch(view.press('Закрыть окно'),/role="dialog"/);
});
test('master number keeps its exact explanation without substituting a digit story',()=>{
  const response=saved();response.calculation.results.soul_number=22;
  Object.assign(response.calculation.results.report.numbers[0],{value:22,interpretation:'Расшифровка мастер-числа 22'});
  const view=renderedReport(savedPersonalResult(response));view.render();
  const html=view.press('Число души: 22. Открыть расшифровку');
  assert.match(html,/Расшифровка мастер-числа 22/);assert.match(html,/Объяснение раздела master-22/);assert.doesNotMatch(html,/Аудио цифры/);
});
test('unavailable name and wisdom show missing data and profile navigation only after selection', () => {
  const response=saved();for(const index of [4,6]){response.calculation.results[fields[index]]=null;Object.assign(response.calculation.results.report.numbers[index],{value:null,interpretation:null,note:'Проверьте имя латинскими буквами.'});}
  for(const index of [4,6]){
    const view=renderedReport(savedPersonalResult(response));view.render();
    const html=view.press(`${fields[index]}: нет значения. Открыть расшифровку`);
    assert.match(html,/Значение недоступно/);assert.match(html,/Проверьте имя латинскими буквами/);assert.match(html,/Проверить имя в профиле/);
  }
});
test('matrix zero and line totals open their own explanations instead of personal-number interpretation', () => {
  const response=saved();response.calculation.results.report.scheme=require('./fixtures/personalScheme').schemeFixture();
  const view=renderedReport(savedPersonalResult(response));const html=view.render();
  assert.match(html,/Персональная схема NumerOM/);
  assert.match(html,/Кету. Количество: 0/);
  const cell=view.press('Кету. Количество: 0. Открыть расшифровку');
  assert.match(cell,/Цифра 7 не встречается в расчёте/);assert.match(cell,/Повторений в вашей схеме/);
  assert.match(cell,/Аудио цифры 7/);assert.doesNotMatch(cell,/Аудио цифры 0/);
  assert.doesNotMatch(cell,/Классический квадрат|Символическая схема|Как рассчитано|А3:/);
  view.press('Закрыть окно');
  const line=view.press('Горизонталь 1-4-7: 4. Открыть расшифровку');
  assert.match(line,/3 \+ 1 \+ 0 = 4/);assert.match(line,/Ячейки: 1 · 4 · 7/);
  assert.match(line,/Объяснение раздела row-0/);
  assert.doesNotMatch(line,/Расшифровка 5 для soul_number/);
  assert.doesNotMatch(line,/Аудио цифры/);
});
test('the shared scheme method is shown once on explicit request, outside digit interpretations',()=>{
  const response=saved();response.calculation.results.report.scheme=require('./fixtures/personalScheme').schemeFixture();
  const view=renderedReport(savedPersonalResult(response));view.render();
  const expanded=view.press('Расчёт схемы');
  assert.match(expanded,/метод Александрова/);assert.match(expanded,/А3: \|.*22.*− 2 ×.*1.*\| =.*20/);
  assert.doesNotMatch(view.press('Скрыть расчёт схемы'),/метод Александрова/);
});
test('separate saved name fields are preserved without inferring from a display name',()=>{
 const value=fixture();value.report.profile_name='Jean Luc Delacroix';
 assert.equal(personalReport(value).profileParts,null);
 value.report.profile_parts={name:'Jean Luc',surname:'Delacroix'};
 assert.deepEqual(personalReport(value).profileParts,{name:'Jean Luc',surname:'Delacroix'});
 value.report.profile_parts={name:'Jean',surname:3};assert.equal(personalReport(value).profileParts,null);
});
