const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {createCreditNotice}=require('../src/lib/creditNotice');

async function screen(){
 const {JSDOM}=require('jsdom'),dom=new JSDOM('<div id="root"></div>',{url:'https://example.org/',pretendToBeVisual:true});
 const previous=new Map();
 const globals={window:dom.window,document:dom.window.document,HTMLElement:dom.window.HTMLElement,Element:dom.window.Element,
  Node:dom.window.Node,ShadowRoot:dom.window.ShadowRoot,navigator:dom.window.navigator,
  getComputedStyle:dom.window.getComputedStyle,requestAnimationFrame:dom.window.requestAnimationFrame.bind(dom.window),
  cancelAnimationFrame:dom.window.cancelAnimationFrame.bind(dom.window),IS_REACT_ACT_ENVIRONMENT:true};
 for(const [key,value] of Object.entries(globals)){
  previous.set(key,Object.getOwnPropertyDescriptor(global,key));Object.defineProperty(global,key,{value,writable:true,configurable:true});
 }
 const React=require('react'),{act}=React,{createRoot}=require('react-dom/client'),native=require('react-native-web');
 const creditNotice=createCreditNotice();creditNotice.sync('student',0);
 let pathname='/numbers',status='signedIn',mounts=0;const routes=[];
 const deps={react:React,'react/jsx-runtime':require('react/jsx-runtime'),'react-native':native,
  'react-native-safe-area-context':{SafeAreaView:native.View},'expo-router':{router:{push:route=>routes.push(route)},usePathname:()=>pathname},
  '@expo/vector-icons':{Ionicons:()=>null},'../lib/session':{useSession:()=>({creditNotice,status})},
  '../lib/creditNotice':require('../src/lib/creditNotice'),'../lib/theme':{colors:{navy:'#183B62',surface:'#fff'}},
  './NavigationChromeContext':{NavigationChromeContext:React.createContext(false)},'./Brand':{Brand:()=>null},
 };
 function load(file){
  const mod={exports:{}},ts=require('typescript');
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.resolve(__dirname,'../src/components',file),'utf8'),
   {compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,
   {exports:mod.exports,require:name=>{assert.ok(name in deps,name);return deps[name];},document:dom.window.document,HTMLElement:dom.window.HTMLElement});
  return mod.exports;
 }
 deps['./ui']=load('ui.tsx');
 const {CreditNotice}=load('CreditNotice.tsx'),root=createRoot(document.getElementById('root'));
 function Draft(){React.useEffect(()=>{mounts++;},[]);return React.createElement('input',{'aria-label':'Дата рождения',defaultValue:'12.04.1990'});}
 const render=()=>root.render(React.createElement(CreditNotice,null,React.createElement(Draft)));
 await act(async()=>render());
 return {routes,creditNotice,dom,act,
  get mounts(){return mounts;},
  get modal(){return document.querySelector('[aria-modal="true"]');},
  async show(){await act(async()=>creditNotice.insufficient({balance:0,cost:5}));},
  async press(text){const button=[...document.querySelectorAll('[role="button"]')].find(n=>n.textContent===text||n.getAttribute('aria-label')===text);assert.ok(button,text);await act(async()=>button.click());},
  async update(next){pathname=next.pathname??pathname;status=next.status??status;await act(async()=>render());},
  async close(){await act(async()=>root.unmount());dom.window.close();for(const [key,descriptor] of previous){if(descriptor)Object.defineProperty(global,key,descriptor);else delete global[key];}},
 };
}
test('real mobile web modal preserves form, traps focus, closes on Escape and opens top-up packages',async()=>{
 const ui=await screen();try{
  const input=document.querySelector('input');input.value='15.08.1988';input.focus();
  await ui.show();assert.ok(ui.modal);assert.match(ui.modal.textContent,/У вас закончились баллы/);
  assert.equal(document.activeElement.getAttribute('aria-label'),'Закрыть окно пополнения');
  assert.ok(input.closest('[aria-hidden="true"]'));
  await ui.act(async()=>input.focus());assert.notEqual(document.activeElement,input);
  await ui.act(async()=>document.dispatchEvent(new ui.dom.window.KeyboardEvent('keyup',{key:'Escape',bubbles:true})));
  assert.equal(ui.modal,null);assert.equal(input.value,'15.08.1988');assert.equal(ui.mounts,1);
  assert.equal(document.activeElement,input,'closing returns keyboard focus to the form');
  await ui.show();await ui.press('Позже');assert.equal(ui.modal,null);assert.deepEqual(ui.routes,[]);
  await ui.show();await ui.press('Пополнить');assert.equal(ui.modal,null);assert.deepEqual(ui.routes,['/top-up']);
  assert.equal(input.value,'15.08.1988');assert.equal(ui.mounts,1);
 }finally{await ui.close();}
});
test('top-up and payment return never have an obstructing modal; navigation and sign-out close it',async()=>{
 const ui=await screen();try{
  await ui.show();await ui.update({pathname:'/top-up'});assert.equal(ui.modal,null);
  await ui.show();assert.equal(ui.modal,null);
  await ui.update({pathname:'/payment-result'});await ui.show();assert.equal(ui.modal,null);
  await ui.update({pathname:'/numbers'});assert.equal(ui.modal,null);
  await ui.show();assert.ok(ui.modal);await ui.update({status:'signedOut'});assert.equal(ui.modal,null);
 }finally{await ui.close();}
});
