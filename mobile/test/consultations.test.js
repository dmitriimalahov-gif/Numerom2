const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const React=require('react'),{renderToStaticMarkup}=require('react-dom/server'),ts=require('typescript');
const {createMaterialAccess}=require('../src/lib/materialAccess'),{safeLearningUrl}=require('../src/lib/learning');
function screen(){
 let index=0,refIndex=0,buttons=[],calls=[],opened=[];
 const item={id:'c1',title:'Личный разбор',description:'Ваши материалы',cost_credits:10,is_purchased:false,has_pdf:true,has_video:false};
 const states=[[item],true,'',false,null],refs=[];
 const api={request:async(url,options)=>{calls.push({url,options});if(url.endsWith('/purchase'))return {...item,is_purchased:true};if(url.endsWith('/access'))return {url:'https://example.org/api/student/consultation-media/signed'};throw Error(url);}};
 const media=createMaterialAccess({openUrl:async url=>opened.push(url),validateUrl:safeLearningUrl});
 const wrap=tag=>({children})=>React.createElement(tag,null,children);
 const deps={react:{...React,useCallback:f=>f,useEffect(){},useRef:initial=>refs[refIndex++]|| (refs[refIndex-1]={current:initial}),useState:initial=>{const i=index++;return [states[i]??initial,value=>{states[i]=typeof value==='function'?value(states[i]):value;}];}},'react/jsx-runtime':require('react/jsx-runtime'),'react-native':{Text:wrap('span'),View:wrap('div'),Linking:{openURL:async url=>opened.push(url)}},'expo-router':{router:{push(){},replace(){}}},'../components/ui':{Screen:wrap('main'),Card:wrap('section'),Heading:({title})=>React.createElement('h1',null,title),Loading:()=>null,Notice:({message})=>React.createElement('p',null,message),Button:props=>{buttons.push(props);return React.createElement('button',null,props.title);},s:{}},'../lib/session':{useSession:()=>({api,user:{id:'student',credits_remaining:20},status:'signedIn',session:{refresh:async()=>{}}})},'../lib/useMaterialAccess':{useMaterialAccess:()=>({...media.getSnapshot(),open:media.open,isOpening:media.isOpening})}};
 const out={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(require('node:path').join(__dirname,'../src/app/consultations.tsx'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{exports:out.exports,require:name=>{assert.ok(name in deps,name);return deps[name];},Error});
 return {calls,opened,render(){index=0;refIndex=0;buttons=[];return renderToStaticMarkup(React.createElement(out.exports.default));},press(title){const button=buttons.find(b=>b.title.startsWith(title));assert.ok(button,title);button.onPress();}};
}
test('consultation requires explicit price confirmation and rapid double tap sends one purchase',async()=>{
 const view=screen();view.render();assert.equal(view.calls.length,0);view.press('Открыть доступ за баллы');assert.equal(view.calls.length,0);
 assert.match(view.render(),/Подтвердите списание 10 баллов/);view.press('Подтвердить');view.press('Подтвердить');await new Promise(setImmediate);
 assert.equal(view.calls.length,1);assert.equal(view.calls[0].options.body.expected_cost,10);assert.match(view.render(),/Доступ открыт/);assert.equal(view.opened.length,0);
 view.press('Открыть PDF-разбор');view.press('Открыть PDF-разбор');await new Promise(setImmediate);assert.equal(view.calls[1].url,'/student/consultations/c1/pdf/access');assert.equal(view.calls.length,2);assert.equal(view.calls[1].options.signal.aborted,false);assert.equal(view.opened.length,1);assert.equal(view.calls.filter(c=>c.options?.method==='POST').length,1);
});
