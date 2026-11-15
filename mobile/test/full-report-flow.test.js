const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {JSDOM}=require('jsdom'),React=require('react'),{createRoot}=require('react-dom/client'),ts=require('typescript');
const report=require('../../docs/artifacts/full-report-fixture.json').report;
const contract=require('../../packages/full-report');
const id='a'.repeat(64),otherId='b'.repeat(64);
const catalog={title:'Полный разбор',amount_total:666,currency:'eur',enabled:true,mode:'test',clients:['mobile'],includes:[]};
const order=(changes={})=>({order_id:id,status:'pending',mode:'test',amount_total:666,currency:'eur',birth_date:report.birth_date,as_of_date:report.as_of_date,session_id:'cs_test_example',url:'https://checkout.stripe.com/c/pay/cs_test_example',...changes});
const paid=(changes={})=>order({status:'paid',url:undefined,report_status:'ready',report,...changes});
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};};

async function setup(options={}){
 const dom=new JSDOM('<div id="root"></div>',{url:'https://example.org/full-report',pretendToBeVisual:true});
 const previous=new Map();
 for(const [key,value] of Object.entries({window:dom.window,document:dom.window.document,IS_REACT_ACT_ENVIRONMENT:true})){
  previous.set(key,Object.getOwnPropertyDescriptor(global,key));Object.defineProperty(global,key,{value,writable:true,configurable:true});
 }
 let identity='owner',sequence=0,mounted=true,handler=options.handler||defaultHandler,writer=null;
 const calls=[],navigation=[],saves=[],documents=[],storage=new Map(options.attempt?[['owner',options.attempt]]:[]);
 const session={getSnapshot:()=>({status:'signedIn',user:{id:identity}}),getToken:()=>identity+'-token'};
 function defaultHandler(url){if(url==='/full-reports/catalog')return catalog;if(url==='/full-reports/history')return {orders:options.history||[]};if(url===`/full-reports/${id}`)return options.order||order();throw Error('Unexpected request '+url);}
 const api={request:async(url,request={})=>{calls.push({url,request});return handler(url,request);}};
 const Box=({children})=>React.createElement('div',null,children);
 const Button=({title,onPress,disabled,busy})=>React.createElement('button',{onClick:onPress,disabled:disabled||busy},title);
 class AnimatedValue{constructor(value){this.value=value;}setValue(value){this.value=value;}stopAnimation(callback){callback?.(this.value);}}
 const Animated={Value:AnimatedValue,View:Box,spring:(value,options)=>({start:()=>value.setValue(options.toValue)})};
 const PanResponder={create:handlers=>({panHandlers:handlers})};
 const deps={react:React,'react/jsx-runtime':require('react/jsx-runtime'),
  'react-native':{Text:Box,View:Box,Pressable:({children,onPress})=>React.createElement('button',{onClick:onPress},children),Animated,PanResponder,Platform:{OS:'ios'},Linking:{openURL:async url=>navigation.push(url)},AppState:{currentState:'active',addEventListener:()=>({remove(){}})}},
  '../../../packages/full-report':contract,
  '../components/ui':{Button,Card:Box,Field:({label,value,onChangeText,editable=true})=>React.createElement('input',{'aria-label':label,value,disabled:!editable,onChange:e=>onChangeText(e.target.value)}),Heading:({title})=>React.createElement('h1',null,title),Loading:()=>React.createElement('span',null,'Loading'),Notice:({message,onAction,action})=>React.createElement('div',{role:'alert'},message,onAction&&React.createElement(Button,{title:action,onPress:onAction})),Screen:Box,s:{}},
  '../components/full-report/ReportProfilePreview':{ReportProfilePreview:({birth,useProfile,onPreview})=>{React.useEffect(()=>onPreview({birth_date:birth,use_profile:useProfile,profile_fingerprint:'c'.repeat(64),available:[],excluded:[]}),[birth,useProfile,onPreview]);return null;}},
  '../components/full-report/ReportPreparing':{ReportPreparing:({birthDate})=>React.createElement('div',{'data-preparing':birthDate||''})},
  '../components/full-report/FullReportDocument':{FullReportDocument:({order})=>{documents.push(order);return React.createElement('article',{'data-report':order.order_id},order.report.title);}},
  '../lib/telegram':{telegramApp:()=>options.telegram?{}:null,openStarsInvoice:async url=>{navigation.push(url);return 'paid';}},
  '../lib/session':{useSession:()=>({api,user:{id:identity,birth_date:report.birth_date},session})},
  '../lib/learning':{submissionId:()=>`00000000-0000-4000-8000-${String(++sequence).padStart(12,'0')}`},
  '../lib/fullReportStorage':{readReportAttempt:async uid=>storage.get(uid)||null,saveReportAttempt:async(uid,value)=>{saves.push({uid,value});if(writer)await writer(uid,value);if(value)storage.set(uid,structuredClone(value));else storage.delete(uid);}},
 };
 const mod={exports:{}};
 vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname,'../src/features/FullReport.tsx'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,
  {exports:mod.exports,require:name=>{assert.ok(name in deps,name);return deps[name];},window:dom.window,document:dom.window.document,setInterval:()=>1,clearInterval(){},AbortController,Error,console});
 const root=createRoot(document.getElementById('root'));
 const render=()=>root.render(React.createElement(mod.exports.default,{key:identity,orderId:options.orderId}));
 await React.act(async()=>render());
 return {calls,navigation,saves,documents,storage,defaultHandler,
  get text(){return document.body.textContent;},
  get checkoutCalls(){return calls.filter(c=>c.url==='/full-reports/checkout');},
  button(label){return [...document.querySelectorAll('button')].find(b=>typeof label==='string'?b.textContent===label:label.test(b.textContent));},
  setHandler(value){handler=value;},setWriter(value){writer=value;},
  async click(label){const button=this.button(label);assert.ok(button,'Button '+label);await React.act(async()=>{button.click();});},
  async flush(fn=()=>{}){await React.act(async()=>{fn();await Promise.resolve();});},
  async switchOwner(value,{render:commit=true}={}){identity=value;if(commit)await React.act(async()=>render());},
  async unmount(){if(mounted){mounted=false;await React.act(async()=>root.unmount());}},
  async close(){await this.unmount();dom.window.close();for(const [key,descriptor] of previous){if(descriptor)Object.defineProperty(global,key,descriptor);else delete global[key];}},
 };
}

test('ambiguous checkout retries the persisted UUID and double taps stay single-flight',async()=>{
 const f=await setup();try{
  const pending=deferred();f.setHandler((url)=>url==='/full-reports/checkout'?pending.promise:f.defaultHandler(url));
  await f.click(/Купить разбор/);await f.click(/Продолжить оплату/);assert.equal(f.checkoutCalls.length,1);
  const body=f.checkoutCalls[0].request.body;assert.equal(f.storage.get('owner').request_id,body.request_id);
  assert.equal(body.use_profile,true);assert.equal(body.profile_fingerprint,'c'.repeat(64));
  await f.flush(()=>pending.reject(Error('Network response lost')));assert.match(f.text,/Network response lost/);
  f.setHandler(url=>url==='/full-reports/checkout'?order():f.defaultHandler(url));await f.click(/Продолжить оплату/);
  assert.equal(f.checkoutCalls.length,2);assert.equal(f.checkoutCalls[1].request.body.request_id,body.request_id);
  assert.equal(f.checkoutCalls[1].request.body.birth_date,body.birth_date);assert.equal(f.navigation.length,1);
  assert.equal(f.checkoutCalls[1].request.body.profile_fingerprint,body.profile_fingerprint);
 }finally{await f.close();}
});

test('failed persistence blocks checkout before any payment can be created',async()=>{
 const f=await setup();try{
  f.setWriter(async()=>{throw Error('Storage unavailable');});await f.click(/Купить разбор/);
  assert.equal(f.checkoutCalls.length,0);assert.deepEqual(f.navigation,[]);assert.match(f.text,/Storage unavailable/);
 }finally{await f.close();}
});

test('unpaid API response cannot render or export an attached report',async()=>{
 const f=await setup({orderId:id,order:order({report})});try{
  assert.equal(f.documents.length,0);assert.equal(document.querySelector('article'),null);
  assert.match(f.text,/отчёт не подтверждён/);assert.equal(f.checkoutCalls.length,0);
 }finally{await f.close();}
});

test('history resumes an existing Stripe session without creating another purchase',async()=>{
 const existing=order(),f=await setup({history:[existing],order:existing});try{
  await f.click(new RegExp(`${report.birth_date} · Ожидает оплаты`));
  await f.click(/Купить разбор|Продолжить оплату/);
  assert.equal(f.checkoutCalls.length,0);assert.deepEqual(f.navigation,[existing.url]);
 }finally{await f.close();}
});

test('saved paid report opens from history without a checkout POST',async()=>{
 const saved=paid(),f=await setup({history:[{...saved,report:undefined}],order:saved});try{
  await f.click(new RegExp(`${report.birth_date} · Оплачено`));
  assert.equal(document.querySelector('article')?.getAttribute('data-report'),id);
  assert.equal(f.checkoutCalls.length,0);assert.deepEqual(f.navigation,[]);
  assert.equal(f.storage.has('owner'),false);
 }finally{await f.close();}
});

test('processing payment and paid report under preparation cannot start another purchase',async()=>{
 for(const current of [order({status:'processing',url:undefined}),paid({report:undefined,report_status:'preparing'})]){
  const f=await setup({orderId:id,order:current});try{
   assert.equal(f.button(/Купить разбор|Продолжить оплату/).disabled,true);
   await f.click(/Купить разбор|Продолжить оплату/);assert.equal(f.checkoutCalls.length,0);assert.deepEqual(f.navigation,[]);
   // A paid report still being prepared shows the square animation for its own birth date; an unpaid one does not.
   const animation=document.querySelector('[data-preparing]');
   assert.equal(animation?.getAttribute('data-preparing')??null,current.status==='paid'?current.birth_date:null);
  }finally{await f.close();}
 }
});

test('creating or pending without a confirmed checkout URL must not create a new purchase from history',async()=>{
 for(const status of ['creating','pending']){
  const current=order({status,url:undefined}),f=await setup({orderId:id,order:current});try{
   assert.equal(f.button(/Купить разбор|Продолжить оплату/).disabled,true,status);
   await f.click(/Купить разбор|Продолжить оплату/);assert.equal(f.checkoutCalls.length,0);
  }finally{await f.close();}
 }
});

test('checkout response after unmount cannot open Stripe',async()=>{
 const f=await setup();try{
  const pending=deferred();f.setHandler(url=>url==='/full-reports/checkout'?pending.promise:f.defaultHandler(url));
  await f.click(/Купить разбор/);await f.unmount();await f.flush(()=>pending.resolve(order()));
  assert.deepEqual(f.navigation,[]);assert.equal(f.storage.get('owner').order_id,undefined);
 }finally{await f.close();}
});

test('old account checkout response is ignored even before the route rerenders',async()=>{
 const f=await setup();try{
  const pending=deferred();f.setHandler(url=>url==='/full-reports/checkout'?pending.promise:f.defaultHandler(url));
  await f.click(/Купить разбор/);await f.switchOwner('different-owner',{render:false});
  await f.flush(()=>pending.resolve(order()));
  assert.deepEqual(f.navigation,[]);assert.equal(f.storage.get('owner').order_id,undefined);
 }finally{await f.close();}
});

test('account switch while saving returned order cannot navigate to previous account checkout',async()=>{
 const f=await setup();try{
  const save=deferred();f.setWriter(async(uid,value)=>{if(value?.order_id)await save.promise;});
  f.setHandler(url=>url==='/full-reports/checkout'?order():f.defaultHandler(url));
  await f.click(/Купить разбор/);await f.switchOwner('different-owner',{render:false});
  await f.flush(()=>save.resolve());assert.deepEqual(f.navigation,[]);
 }finally{await f.close();}
});

test('a late order lookup cannot replace a newer history selection',async()=>{
 const first=paid(),second=paid({order_id:otherId,birth_date:'02.02.1990',report:{...report,birth_date:'02.02.1990'}});
 const f=await setup({history:[{...first,report:undefined},{...second,report:undefined}]});try{
  const waiting=deferred();f.setHandler(url=>url===`/full-reports/${id}`?waiting.promise:url===`/full-reports/${otherId}`?second:f.defaultHandler(url));
  await f.click(new RegExp(`${report.birth_date} · Оплачено`));await f.click(/02.02.1990 · Оплачено/);
  await f.flush(()=>waiting.resolve(first));assert.equal(document.querySelector('article')?.getAttribute('data-report'),otherId);
  assert.equal(f.checkoutCalls.length,0);
 }finally{await f.close();}
});

test('cancelling a different history order preserves the unresolved checkout UUID',async()=>{
 const attempt={request_id:'00000000-0000-4000-8000-000000000042',birth_date:report.birth_date};
 const selected=order({order_id:otherId}),f=await setup({attempt,history:[selected]});try{
  f.setHandler((url)=>url===`/full-reports/${otherId}`?selected:url===`/full-reports/${otherId}/cancel`?{...selected,status:'expired',url:undefined}:f.defaultHandler(url));
  await f.click(new RegExp(`${report.birth_date} · Ожидает оплаты`));
  await f.click('Отменить незавершённую оплату');
  assert.equal(f.storage.get('owner')?.request_id,attempt.request_id);
  assert.equal(f.checkoutCalls.length,0);
 }finally{await f.close();}
});

test('leaving a saved report does not discard a different unresolved purchase attempt',async()=>{
 const attempt={request_id:'00000000-0000-4000-8000-000000000042',birth_date:report.birth_date};
 const selected=paid({order_id:otherId}),f=await setup({attempt,history:[{...selected,report:undefined}]});try{
  f.setHandler(url=>url===`/full-reports/${otherId}`?selected:url==='/full-reports/checkout'?order():f.defaultHandler(url));
  await f.click(new RegExp(`${report.birth_date} · Оплачено`));await f.click('Вернуться к сохранённой попытке');
  assert.equal(f.storage.get('owner')?.request_id,attempt.request_id);
  await f.click(/Продолжить оплату/);
  assert.equal(f.checkoutCalls[0].request.body.request_id,attempt.request_id);
 }finally{await f.close();}
});

test('paid profile extension uses the owned revision without another purchase',async()=>{
 const saved=paid({revision:1,profile_fingerprint:'a'.repeat(64)}),f=await setup({orderId:id,order:saved});try{
  f.setHandler((url)=>url===`/full-reports/${id}/extend-profile`?paid({revision:2,profile_fingerprint:'c'.repeat(64)}):f.defaultHandler(url));
  await f.click('Дополнить разбор без доплаты');
  const extension=f.calls.find(call=>call.url.endsWith('/extend-profile'));
  assert.deepEqual(JSON.parse(JSON.stringify(extension.request.body)),{profile_fingerprint:'c'.repeat(64),expected_revision:1});
  assert.equal(f.checkoutCalls.length,0);assert.equal(f.documents.at(-1).revision,2);
 }finally{await f.close();}
});

test('changed profile rechecks composition and preserves the same purchase UUID',async()=>{
 const f=await setup();try{
  f.setHandler(url=>url==='/full-reports/checkout'?Promise.reject(Object.assign(Error('Review profile'),{code:'full_report_profile_changed'})):f.defaultHandler(url));
  await f.click(/Купить разбор/);const first=f.checkoutCalls[0].request.body;assert.equal(f.storage.get('owner').profile_stale,true);
  f.setHandler(url=>url==='/full-reports/checkout'?order():f.defaultHandler(url));await f.click(/Продолжить оплату/);
  assert.equal(f.checkoutCalls[1].request.body.request_id,first.request_id);assert.equal(f.storage.get('owner').profile_stale,false);
 }finally{await f.close();}
});


test('Telegram report checkout uses Stars and never navigates to Stripe',async()=>{
 const starsCatalog={...catalog,payment_provider:'telegram',currency:'XTR',amount_total:40,mode:'live',clients:['telegram']};
 const starsOrder=order({payment_provider:'telegram',currency:'XTR',amount_total:40,mode:'live',url:'https://t.me/$test-invoice',session_id:undefined});
 const f=await setup({telegram:true,handler:(url)=>{
  if(url==='/telegram/full-reports/catalog')return starsCatalog;
  if(url==='/full-reports/history')return {orders:[]};
  if(url==='/telegram/full-reports/checkout')return starsOrder;
  throw Error('Unexpected request '+url);
 }});
 try{
  assert.match(f.text,/40 Stars/);await f.click(/Купить разбор/);
  assert.equal(f.calls.filter(c=>c.url==='/telegram/full-reports/checkout').length,1);
  assert.deepEqual(f.navigation,['https://t.me/$test-invoice']);
  assert.equal(f.checkoutCalls.length,0);
 }finally{await f.close();}
});
