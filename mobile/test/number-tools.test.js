const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const React=require('react'),{renderToStaticMarkup}=require('react-dom/server'),ts=require('typescript');
function preview(){
 let index=0,buttons=[],audio=[],details=null;const states=[];
 const wrap=tag=>({children})=>React.createElement(tag,null,children);
 const part=(key,label,number,source)=>({key,label,number,source,total:number,steps:[`Сумма ${number}`],tokens:[{symbol:String(number),value:number}],title:`Тема ${number}`,interpretation:`Смысл ${label}`,focus:`Совет ${number}`,narration_id:`tool-address-${number}`});
 const receipt={id:'report',request_id:'id',created_at:'2026-10-18T00:00:00Z',cost:1,results:{version:1,kind:'address',title:'Адрес',summary:'Дом 5, квартира 7',method:'Метод адреса',items:[part('house','Дом',5,'14'),part('apt','Квартира',7,'16')]}};
 const deps={react:{...React,useState:initial=>{const i=index++;if(!(i in states))states[i]=initial;return [states[i],v=>states[i]=v];}},'react/jsx-runtime':require('react/jsx-runtime'),'react-native':{Text:wrap('span'),View:({children,accessibilityRole})=>React.createElement('div',{role:accessibilityRole},children),Pressable:props=>{buttons.push(props);return React.createElement('button',null,props.children);},StyleSheet:{create:o=>o}},'expo-router':{router:{push(){}}},'@numerom/api-client':{},'../lib/session':{},'../lib/learning':{},'../lib/theme':{colors:{}},'../components/ui':{Card:wrap('section'),Button:props=>{buttons.push({...props,accessibilityLabel:props.title});return React.createElement('button',null,props.title);},s:{}},'../components/audio/Narration':{NarrationClip:props=>{audio.push(props.id);return null;}},'../components/numbers/InterpretationSheet':{InterpretationSheet:props=>{details=props.detail;return null;}}};
 deps['../components/SavedReportExport']={SavedReportExport:()=>React.createElement('button',null,'Сохранить PDF')};deps['../lib/savedReportExport']=require('../src/lib/savedReportExport');deps['../lib/pendingCalculationStorage']={};
 const mod={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname,'../src/features/NumberTools.tsx'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{exports:mod.exports,require:name=>{assert.ok(name in deps,name);return deps[name];},Date});
 return {render(){index=0;buttons=[];audio=[];return renderToStaticMarkup(React.createElement(mod.exports.ToolResult,{receipt}));},press(label){const target=buttons.find(p=>p.accessibilityLabel?.includes(label));assert.ok(target,label);target.onPress();},get audio(){return audio;},get detail(){return details;}};
}
test('selected address result changes its meaning, arithmetic and contextual audio',()=>{
 const view=preview();let html=view.render();assert.match(html,/Смысл Дом/);assert.deepEqual(view.audio,['tool-address-5']);assert.equal((html.match(/role="progressbar"/g)||[]).length,9);assert.doesNotMatch(html,/Метод адреса/);
 view.press('Квартира: 7');html=view.render();assert.match(html,/Смысл Квартира/);assert.doesNotMatch(html,/Смысл Дом/);assert.deepEqual(view.audio,['tool-address-7']);
 view.press('Метод расчёта');html=view.render();assert.match(html,/Метод адреса/);assert.deepEqual(view.audio,['tool-address-7','tool-method-address']);
});
test('frequency chart opens meaning of its digit rather than occurrence count',()=>{
 const view=preview();view.render();view.press('Значение 9: 0');view.render();assert.equal(view.detail.knowledgeDigit,9);assert.equal(view.detail.value,9);
});
