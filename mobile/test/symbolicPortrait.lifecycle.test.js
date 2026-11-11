const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const {JSDOM}=require('jsdom'),React=require('react'),{createRoot}=require('react-dom/client'),ts=require('typescript');
async function setup(){
 const dom=new JSDOM('<div id="root"></div>',{url:'http://localhost',pretendToBeVisual:true});global.window=dom.window;global.document=dom.window.document;global.IS_REACT_ACT_ENVIRONMENT=true;
 let owner='owner',resolve,guard,calls=0;const waiting=new Promise(done=>{resolve=done;});
 const Box=({children})=>React.createElement('div',null,children);
 const deps={react:React,'react/jsx-runtime':require('react/jsx-runtime'),'react-native':{Text:Box,View:Box,Platform:{OS:'web'},AppState:{currentState:'active',addEventListener:()=>({remove(){}})}},'expo-router':{useFocusEffect:callback=>React.useEffect(callback,[callback])},'../ui':{s:{},Card:Box,Notice:()=>null,Button:({title,onPress,disabled})=>React.createElement('button',{onClick:onPress,disabled},title)},'../audio/Narration':{NarrationProvider:({path,children})=>{assert.equal(path,'/narration/project');return React.createElement(Box,null,children);}},'../numbers/NameSchemes':{NameSchemes:()=>null},'../numbers/InterpretationSheet':{InterpretationSheet:()=>null},'../../lib/symbolicPortrait':require('../src/lib/symbolicPortrait'),'../../lib/reportPrint':{deliverReport:async(html,options)=>{calls++;guard=options.isCurrent;assert.match(html,/Anna/);await waiting;}},'../../lib/session':{useSession:()=>({user:{id:'owner'},session:{getToken:()=> 'token',getSnapshot:()=>({user:{id:owner}})}})}};
 const module={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname,'../src/components/business/SymbolicPortrait.tsx'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{exports:module.exports,require:name=>{assert.ok(name in deps,name);return deps[name];},document:dom.window.document});
 const root=createRoot(document.getElementById('root'));let mounted=true;
 await React.act(async()=>root.render(React.createElement(module.exports.SymbolicPortrait,{employee:{id:'employee',name:'Anna',surname:'Petrova',birth_date:'10.01.1982'},busy:false,onClose(){}})));
 return {get calls(){return calls;},get guard(){return guard;},owner(value){owner=value;},async click(){await React.act(async()=>{Array.from(document.querySelectorAll('button')).find(b=>b.textContent==='Сохранить личный портрет / PDF').click();});},async unmount(){if(mounted){mounted=false;await React.act(async()=>root.unmount());}},async settle(){await React.act(async()=>resolve());},async close(){await this.unmount();await this.settle();dom.window.close();delete global.window;delete global.document;delete global.IS_REACT_ACT_ENVIRONMENT;}};
}
test('portrait export is single-flight and pending export guard rejects a changed account',async()=>{
 const f=await setup();try{await f.click();await f.click();assert.equal(f.calls,1);assert.equal(f.guard(),true);f.owner('other');assert.equal(f.guard(),false);await f.settle();}finally{await f.close();}
});
test('portrait export guard rejects an unmounted view and cannot start for another owner',async()=>{
 const f=await setup();try{await f.click();await f.unmount();assert.equal(f.guard(),false);await f.settle();}finally{await f.close();}
 const g=await setup();try{g.owner('other');await g.click();assert.equal(g.calls,0);}finally{await g.close();}
});
