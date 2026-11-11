const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const React=require('react'),{renderToStaticMarkup}=require('react-dom/server'),ts=require('typescript');
function preview(){
 let index=0,buttons=[],details=null;const states=[];
 const wrap=tag=>({children})=>React.createElement(tag,null,children);
 const person=(name,number)=>({name,number,birth_date:'01.01.2000',steps:['Серверный шаг']});
 const receipt={id:'report',request_id:'id',created_at:'2026-10-18T00:00:00Z',cost:5,results:{version:1,kind:'group',main:person('Анна',1),people:[person('Иван',9),person('Ольга',22)],average:6,method:'Единый метод',note:'Условная шкала',connections:[{name:'Иван',score:2,title:'Первое пояснение',interpretation:'Текст первой пары',focus:'Первый совет',formula:'Формула 1'},{name:'Ольга',score:10,title:'Второе пояснение',interpretation:'Текст второй пары',focus:'Второй совет',formula:'Формула 2'}]}};
 const deps={react:{...React,useState:initial=>{const i=index++;if(!(i in states))states[i]=initial;return [states[i],v=>states[i]=v];}},'react/jsx-runtime':require('react/jsx-runtime'),'react-native':{Text:wrap('span'),View:({children,accessibilityRole,...props})=>React.createElement('div',{role:accessibilityRole},children),Pressable:props=>{buttons.push(props);return React.createElement('button',null,props.children);},StyleSheet:{create:o=>o}},'expo-router':{router:{push(){}}},'@numerom/api-client':{},'../lib/relationshipVoice':require('../src/lib/relationshipVoice'),'../components/audio/Narration':{NarrationClip:({id})=>React.createElement('audio',{'data-narration':id})},'../lib/session':{},'../lib/learning':{},'../lib/theme':{colors:{}},'../components/ui':{Card:wrap('section'),Button:props=>{buttons.push({...props,accessibilityLabel:props.title});return React.createElement('button',null,props.title);},s:{}},'../components/numbers/InterpretationSheet':{InterpretationSheet:props=>{details=props.detail;return null;}}};
 deps['../components/SavedReportExport']={SavedReportExport:()=>React.createElement('button',null,'Сохранить PDF')};deps['../lib/savedReportExport']=require('../src/lib/savedReportExport');deps['../lib/pendingCalculationStorage']={};
 const mod={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname,'../src/features/Relationships.tsx'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{exports:mod.exports,require:name=>{assert.ok(name in deps,name);return deps[name];},Date});
 return {render(){index=0;buttons=[];return renderToStaticMarkup(React.createElement(mod.exports.RelationshipResult,{receipt}));},press(label){const target=buttons.find(p=>p.accessibilityLabel?.includes(label));assert.ok(target,label);target.onPress();},get detail(){return details;}};
}
test('group chart opens the selected pair and method appears only on request',()=>{
 const view=preview();let html=view.render();assert.equal((html.match(/role="progressbar"/g)||[]).length,2);assert.match(html,/Текст первой пары/);assert.doesNotMatch(html,/Единый метод/);assert.match(html,/data-narration="relationship-contrast"/);assert.doesNotMatch(html,/data-narration="relationship-method"/);
 view.press('Ольга: 10 из 10');html=view.render();assert.match(html,/Текст второй пары/);assert.doesNotMatch(html,/Текст первой пары/);assert.match(html,/data-narration="relationship-same"/);assert.doesNotMatch(html,/data-narration="relationship-contrast"/);
 view.press('Как рассчитана');html=view.render();assert.match(html,/Единый метод/);assert.match(html,/Серверный шаг/);assert.match(html,/Формула 2/);assert.match(html,/data-narration="relationship-method"/);
});
test('number selection uses the person number for narration, not the compatibility score',()=>{
 const view=preview();view.render();view.press('Иван: число 9');view.render();assert.equal(view.detail.knowledgeDigit,9);assert.equal(view.detail.value,9);
 view.press('Ольга: число 22');view.render();assert.equal(view.detail.narrationId,'master-22');assert.equal(view.detail.knowledgeDigit,undefined);
});
