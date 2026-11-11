const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {JSDOM}=require('jsdom'),React=require('react'),{createRoot}=require('react-dom/client'),ts=require('typescript');
async function screen(file,{registered=false,pending=null}={}){
 const dom=new JSDOM('<div id="root"></div>',{url:'https://example.org/telegram',pretendToBeVisual:true});
 const previous=new Map();for(const [key,value] of Object.entries({window:dom.window,document:dom.window.document,IS_REACT_ACT_ENVIRONMENT:true})){
  previous.set(key,Object.getOwnPropertyDescriptor(global,key));Object.defineProperty(global,key,{value,writable:true,configurable:true});}
 const calls=[],signIns=[],invoices=[],fields={},navigation=[];let refreshes=0,signOuts=0;
 const attempt={request_id:'00000000-0000-4000-8000-000000000123',package_type:'one_time'};
 if(pending)window.sessionStorage.setItem('numerom.telegram.payment.owner',JSON.stringify(attempt));
 const order={order_id:'a'.repeat(64),state:'pending',invoice_url:'https://t.me/$invoice',amount:10};
 const user={id:'owner',credits_remaining:registered?37:10};
 const api={request:async(url,request={})=>{
  calls.push({url,request});
  if(url==='/auth/telegram/login'&&registered==='revoked')throw Object.assign(Error('Повторите привязку'),{status:403});
  if(url==='/auth/telegram/link')return {access_token:'test-session',user};
  if(url==='/auth/telegram/login')return registered?{access_token:'test-session',user}:{registration_required:true};
  if(url==='/auth/telegram/register')return {access_token:'test-session',user};
  if(url==='/telegram/menu')return {ok:true};
  if(url==='/telegram/payments/catalog')return {packages:[{id:'one_time',title:'10 баллов',credits:10,stars:10,enabled:true}]};
  if(url==='/telegram/payments/invoice')return order;
  if(url.startsWith('/telegram/payments/orders/'))return order;
  throw Error('Unexpected request '+url);
 }};
 const session={signOut:async()=>signOuts++,signInWith:async loader=>{signIns.push(await loader());},refresh:async()=>refreshes++};
 const Box=({children})=>React.createElement('div',null,children);
 const ui={Brand:()=>null,Button:({title,onPress,disabled,busy})=>React.createElement('button',{onClick:onPress,disabled:disabled||busy},title),Card:Box,Heading:({title,subtitle})=>React.createElement('header',null,React.createElement('h1',null,title),subtitle),Loading:()=>React.createElement('span',null,'Loading'),Notice:({message})=>React.createElement('p',null,message),Screen:Box,s:{},Field:({label,onChangeText})=>{fields[label]=onChangeText;return React.createElement('input',{'aria-label':label});}};
 const deps={react:React,'react/jsx-runtime':require('react/jsx-runtime'),'react-native':{Text:Box,View:Box},'expo-router':{router:{push:p=>navigation.push(p),replace:p=>navigation.push(p)},useLocalSearchParams:()=>({section:'home'})},
 '../lib/session':{useSession:()=>({api,session,user,status:'signedOut'})},'../lib/telegram':{loadTelegram:async()=>({initData:'signed-launch',ready(){},expand(){}}),telegramSection:()=>'/home',openStarsInvoice:async url=>{invoices.push(url);return 'paid';}},'../lib/learning':{submissionId:()=>attempt.request_id},'../components/ui':ui,'./ui':ui};
 const mod={exports:{}};
 vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname,'../src',file),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{exports:mod.exports,require:n=>{assert.ok(n in deps,n);return deps[n];},window:dom.window,document:dom.window.document,setInterval:()=>1,clearInterval(){},Error,console});
 const root=createRoot(document.getElementById('root'));
 await React.act(async()=>root.render(React.createElement(React.StrictMode,null,React.createElement(mod.exports.default||mod.exports.TelegramTopUp))));
 return {calls,signIns,invoices,navigation,get text(){return document.body.textContent;},get refreshes(){return refreshes;},get signOuts(){return signOuts;},
  async fill(label,value){await React.act(async()=>fields[label](value));},
  async click(label){const b=[...document.querySelectorAll('button')].find(b=>b.textContent===label);assert.ok(b,label);await React.act(async()=>b.click());},
  async close(){await React.act(async()=>root.unmount());dom.window.close();for(const[k,v]of previous){if(v)Object.defineProperty(global,k,v);else delete global[k];}},
 };
}
test('Telegram registration shows 10 points and requests the private menu immediately, including StrictMode',async()=>{
 const f=await screen('app/telegram.tsx');try{
  assert.equal(f.signOuts,1);assert.equal(f.signIns.length,0);assert.match(f.text,/10 приветственных баллов/);
  await f.fill('Имя и фамилия','Example');await f.fill('Дата рождения','01.01.1980');await f.click('Зарегистрироваться');
  assert.match(f.text,/10 баллов/);assert.equal(f.signIns.length,1);
  const reg=f.calls.find(x=>x.url==='/auth/telegram/register');assert.equal(reg.request.body.init_data,'signed-launch');assert.equal(reg.request.body.full_name,'Example');
  assert.equal(f.calls.filter(x=>x.url==='/telegram/menu').length,1);
  await f.click('Открыть NumerOM');assert.deepEqual(f.navigation,['/home']);
 }finally{await f.close();}
});
test('existing Telegram account keeps actual balance without another registration',async()=>{
 const f=await screen('app/telegram.tsx',{registered:true});try{
  assert.match(f.text,/37 баллов/);assert.equal(f.calls.some(x=>x.url.endsWith('/register')),false);
  assert.equal(f.signIns.length,1);
 }finally{await f.close();}
});
test('Stars reload recovers the same attempt; an invoice callback alone never credits balance',async()=>{
 const f=await screen('components/TelegramTopUp.tsx',{pending:true});try{
  const attempts=f.calls.filter(x=>x.url==='/telegram/payments/invoice');assert.ok(attempts.length>=1);
  assert.equal(new Set(attempts.map(x=>x.request.body.request_id)).size,1);
  await f.click('Продолжить оплату');assert.deepEqual(f.invoices,['https://t.me/$invoice']);
  assert.equal(f.refreshes,0);assert.match(f.text,/Подтверждение оплаты ещё не получено/);
 }finally{await f.close();}
});

test('revoked Telegram binding offers password relinking rather than a retry loop',async()=>{
 const f=await screen('app/telegram.tsx',{registered:'revoked'});try{
  assert.match(f.text,/Связать мой аккаунт/);
  await f.fill('Электронная почта NumerOM','example@example.invalid');await f.fill('Пароль NumerOM','example-password');
  await f.click('Войти и связать Telegram');assert.match(f.text,/37 баллов/);
  assert.equal(f.calls.filter(x=>x.url==='/auth/telegram/link').length,1);
 }finally{await f.close();}
});
