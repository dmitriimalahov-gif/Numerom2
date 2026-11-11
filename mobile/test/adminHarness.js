const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const {JSDOM}=require('jsdom'),React=require('react'),{createRoot}=require('react-dom/client'),ts=require('typescript');
const apiContract=require('../../packages/api-client');
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};};
async function setup(entry,options={}){
 const dom=new JSDOM('<div id="root"></div>',{url:'https://example.test/admin',pretendToBeVisual:true}),previous=new Map();
 for(const [key,value]of Object.entries({window:dom.window,document:dom.window.document,IS_REACT_ACT_ENVIRONMENT:true})){previous.set(key,Object.getOwnPropertyDescriptor(global,key));Object.defineProperty(global,key,{value,writable:true,configurable:true});}
 let actor={id:'admin',is_admin:true,...options.actor},status=options.status||'signedIn',handler=options.handler||(()=>({})),picker=options.picker||(()=>({canceled:true})),props=options.props||{},sequence=0,mounted=true;
 const calls=[],navigation=[],links=[],session={getSnapshot:()=>({user:actor,status}),restore:async()=>{}},api={request:async(url,request={})=>{calls.push({url,request});return handler(url,request);}};
 const Box=({children})=>React.createElement('div',null,children),Button=({title,onPress,disabled,busy})=>React.createElement('button',{onClick:onPress,disabled:disabled||busy},title);
 const Field=({label,value,onChangeText,editable=true,multiline,onSubmitEditing})=>React.createElement(multiline?'textarea':'input',{'aria-label':label,value,disabled:!editable,onInput:e=>onChangeText(e.currentTarget.value),onKeyDown:e=>{if(e.key==='Enter'&&!multiline)onSubmitEditing?.();}});
 const ui={Button,Field,Card:Box,Screen:Box,Heading:({title,subtitle})=>React.createElement('header',null,title,subtitle),Loading:()=>React.createElement('span',null,'Загрузка'),Notice:({message,action,onAction})=>React.createElement('div',{role:'alert'},message,onAction&&React.createElement(Button,{title:action,onPress:onAction})),s:{}};
 const native={Text:Box,View:Box,ScrollView:Box,Pressable:({children,onPress,disabled,accessibilityLabel,accessibilityState})=>React.createElement('button',{onClick:onPress,disabled,'aria-label':accessibilityLabel,'aria-pressed':accessibilityState?.checked??accessibilityState?.selected},children),Platform:{OS:'ios'},Linking:{openURL:async url=>links.push(url)}};
 const modules=new Map();
 function load(filename){filename=path.resolve(filename);if(modules.has(filename))return modules.get(filename).exports;const mod={exports:{}};modules.set(filename,mod);
  const localRequire=name=>{if(name==='react')return React;if(name==='react/jsx-runtime')return require(name);if(name==='react-native')return native;if(name==='@numerom/api-client')return apiContract;if(name==='expo-router')return {router:{push:value=>navigation.push(value),replace:value=>navigation.push(value)}};if(name==='expo-document-picker')return {getDocumentAsync:async()=>picker()};if(name==='expo-file-system')return {File:class {get size(){return options.fileSize||12;}async text(){return options.fileText||'Урок\nСодержание';}}};
   if(/\/components\/ui$/.test(name))return ui;if(/\/lib\/session$/.test(name))return {useSession:()=>({user:actor,status,api,session}),backendUrl:'https://api.example.test'};if(/\/lib\/learning$/.test(name))return {submissionId:()=>`00000000-0000-4000-8000-${String(++sequence).padStart(12,'0')}`};
   if(name.startsWith('.')){const base=path.resolve(path.dirname(filename),name),target=['','.tsx','.ts','.js'].map(ext=>base+ext).find(file=>fs.existsSync(file)&&fs.statSync(file).isFile());assert.ok(target,'Local module '+name);return load(target);}throw Error('Unstubbed dependency '+name);
  };
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(filename,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}}).outputText,{exports:mod.exports,module:mod,require:localRequire,Error,URL,console,setTimeout,clearTimeout,window:dom.window,document:dom.window.document});return mod.exports;
 }
 const Component=load(path.resolve(__dirname,'../src',entry))[options.exportName||'default'],root=createRoot(document.getElementById('root'));
 const render=()=>root.render(React.createElement(Component,props));await React.act(async()=>render());
 return {calls,navigation,links,apiContract,dom,get text(){return document.body.textContent;},get writes(){return calls.filter(call=>call.request.method&&call.request.method!=='GET');},
 button(label){return [...document.querySelectorAll('button')].find(b=>typeof label==='string'?b.textContent===label:label.test(b.textContent));},
 field(label){return [...document.querySelectorAll('input,textarea')].find(b=>typeof label==='string'?b.getAttribute('aria-label')===label:label.test(b.getAttribute('aria-label')));},
 setHandler(next){handler=next;},setPicker(next){picker=next;},
 async click(label){const button=this.button(label);assert.ok(button,'Button '+label);await React.act(async()=>button.click());},
 async fill(label,value){const field=this.field(label);assert.ok(field,'Field '+label);assert.equal(field.disabled,false,'Editable '+label);await React.act(async()=>{field.value=value;field.dispatchEvent(new dom.window.Event('input',{bubbles:true}));});},
 async flush(fn=()=>{}){await React.act(async()=>{fn();await Promise.resolve();});},
 async update(next){props={...props,...next};await React.act(async()=>render());},
 async actor(next,{commit=true,state=status}={}){actor={...actor,...next};status=state;if(commit)await React.act(async()=>render());},
 async unmount(){if(mounted){mounted=false;await React.act(async()=>root.unmount());}},
 async close(){await this.unmount();dom.window.close();for(const[key,value]of previous){if(value)Object.defineProperty(global,key,value);else delete global[key];}},
 };
}
module.exports={setup,deferred,ApiError:apiContract.ApiError,plain:value=>JSON.parse(JSON.stringify(value))};
