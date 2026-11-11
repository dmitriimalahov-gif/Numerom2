const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const React=require('react'),{act}=React,{createRoot}=require('react-dom/client');
const {JSDOM}=require('jsdom');
const ts=require('typescript');
const payments=require('../../packages/api-client');
const catalog={enabled:true,mode:'test',clients:['mobile'],balance:7,test_balance:0,packages:[{id:'one_time',title:'Стартовый пакет',credits:10,amount_total:99,currency:'eur',recurring:false,access_days:30,consultation:false}]};
const sid='cs_test_123',order='a'.repeat(64),receipt={order_id:order,session_id:sid,status:'paid',payment_status:'paid',mode:'test',title:'Стартовый пакет',credits:10,amount_total:99,currency:'eur'};
async function screen({saved=null,status=receipt,returnId,checkoutError=false}={}){
 const dom=new JSDOM('<div id="root"></div>',{url:'https://example.org/'});
 global.window=dom.window;global.document=dom.window.document;global.IS_REACT_ACT_ENVIRONMENT=true;
 let pending=saved,refreshes=0,calls=[],opened=[],fail=checkoutError;
 const api={request:async(url,options)=>{
  calls.push({url,options});
  if(url==='/payments/packages')return catalog;
  if(url==='/payments/history')return {orders:[]};
  if(url.includes('/status/'))return status;
  if(url==='/payments/checkout/session'){
   if(fail){fail=false;throw Error('Потеря связи');}
   return {order_id:order,session_id:sid,url:'https://checkout.stripe.com/c/pay/'+sid,state:'pending',mode:'test'};
  }
  throw Error('Unexpected request '+url);
 }};
 const session={refresh:async()=>{refreshes++;}};
 const useSession=()=>({api,user:{id:'student',credits_remaining:7},session});
 const wrap=tag=>({children})=>React.createElement(tag,null,children);
 const deps={react:React,'react/jsx-runtime':require('react/jsx-runtime'),'react-native':{Text:wrap('span'),View:wrap('div'),Platform:{OS:'ios'},Linking:{openURL:async url=>opened.push(url)},AppState:{addEventListener:()=>({remove(){}})}},'expo-router':{router:{push(){}}},'@numerom/api-client':payments,'./ui':{Screen:wrap('main'),Card:wrap('section'),Heading:({title})=>React.createElement('h1',null,title),Loading:()=>null,Notice:({message})=>React.createElement('p',null,message),Button:({title,onPress,disabled,busy})=>React.createElement('button',{onClick:onPress,disabled:disabled||busy},title),s:{}},'../lib/session':{useSession},'../lib/learning':{submissionId:()=> '82c7a315-416c-4234-8146-022c41a7f43b'},'../lib/paymentStorage':{readPayment:async()=>pending,savePayment:async(uid,value)=>{assert.equal(uid,'student');pending=value;}}};
 const out={exports:{}};
 vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname,'../src/components/TopUp.tsx'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{exports:out.exports,require:name=>{assert.ok(name in deps,name);return deps[name];},setInterval:()=>0,clearInterval(){},Error,Intl,window:dom.window});
 const root=createRoot(document.getElementById('root'));
 await act(async()=>root.render(React.createElement(out.exports.TopUp,{sessionId:returnId})));
 return {get text(){return document.body.textContent;},get pending(){return pending;},calls,opened,get refreshes(){return refreshes;},async press(label){const b=[...document.querySelectorAll('button')].find(b=>b.textContent.includes(label));assert.ok(b,label);assert.equal(b.disabled,false);await act(async()=>b.click());},async close(){await act(async()=>root.unmount());dom.window.close();}};
}
test('lost checkout response reuses the same request before opening Stripe',async()=>{
 const view=await screen({checkoutError:true});try{
 await view.press('Выбрать');assert.match(view.text,/Потеря связи/);assert.equal(view.opened.length,0);
 const first=view.calls.find(c=>c.url==='/payments/checkout/session');
 await view.press('Продолжить в Stripe');
 const attempts=view.calls.filter(c=>c.url==='/payments/checkout/session');assert.equal(attempts.length,2);assert.deepEqual(attempts[1].options.body,first.options.body);assert.equal(view.opened.length,1);assert.equal(view.pending.session_id,sid);
 }finally{await view.close();}
});
test('verified test payment clears its pending attempt without spending real balance',async()=>{
 const view=await screen({saved:{package_type:'one_time',request_id:'saved',session_id:sid}});try{
 assert.match(view.text,/Рабочий баланс не изменён/);assert.equal(view.pending,null);assert.equal(view.refreshes,1);assert.equal(view.opened.length,0);assert.equal(view.calls.filter(c=>c.options?.method==='POST').length,0);
 }finally{await view.close();}
});
test('old return cannot erase a newer attempt without a session ID',async()=>{
 const newer={package_type:'one_time',request_id:'newer'};const view=await screen({saved:newer,returnId:sid});try{assert.deepEqual(view.pending,newer);assert.equal(view.opened.length,0);}finally{await view.close();}
});
