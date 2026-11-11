const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const {JSDOM}=require('jsdom'),React=require('react'),{createRoot}=require('react-dom/client'),ts=require('typescript');
const data=require('../src/lib/business');
const employee={name:'Тест',surname:'Сотрудник',birth_date:null,department:'',role:'',skills:['Excel'],experience:'',interests:[],hours_per_week:10};
const workspace={id:'company-id',company_name:'Тестовая компания',revision:0,employees:[],groups:[],created_at:'2026-10-18T12:00:00Z',updated_at:'2026-10-18T12:00:00Z'};
const envelope=()=>({package:{id:'business-250',title:'Business250',max_employees:250,mode:'pilot',price:0},workspace:structuredClone(workspace)});
const preview={employees:[employee],issues:[],warnings:[],row_count:1,valid:true};
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};};
async function setup(){
 const dom=new JSDOM('<div id="root"></div>',{url:'http://localhost',pretendToBeVisual:true});global.window=dom.window;global.document=dom.window.document;global.IS_REACT_ACT_ENVIRONMENT=true;
 let latest,focusCallback,focusCleanup,identity='owner',token='synthetic',sequence=0,handler=async()=>envelope(),picker=async()=>({filename:'test.csv',content_base64:'abc'}),deliver=async()=>{},calls=[];
 const session={getSnapshot:()=>({user:{id:identity}}),getToken:()=>token};
 const api={request:async(url,options={})=>{calls.push({url,options});return handler(url,options);}};
 const deps={react:React,'react-native':{Platform:{OS:'web'},AppState:{currentState:'active',addEventListener:()=>({remove(){}})}},'expo-router':{useFocusEffect:callback=>React.useEffect(()=>{focusCallback=callback;focusCleanup=callback();return()=>focusCleanup?.();},[callback])},'./session':{useSession:()=>({api,session,user:{id:'owner'}})},'./business':data,'./businessFile':{pickBusinessFile:()=>picker(),saveBusinessTemplate:async()=>{}},'./reportPrint':{deliverReport:(...args)=>deliver(...args)},'./learning':{submissionId:()=>`synthetic-request-${++sequence}`}};
 const module={exports:{}};
 vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname,'../src/lib/useBusiness.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports:module.exports,require:name=>{assert.ok(name in deps,name);return deps[name];},AbortController,Error,Set,document:dom.window.document});
 function Harness(){latest=module.exports.useBusiness();return React.createElement('div',null,latest.workspace?.company_name||'loading');}
 const root=createRoot(document.getElementById('root'));
 await React.act(async()=>{root.render(React.createElement(Harness));});
 return {get state(){return latest;},calls,setHandler(fn){handler=fn;},setPicker(fn){picker=fn;},setDeliver(fn){deliver=fn;},setOwner(value){identity=value;},async blur(){await React.act(async()=>focusCleanup());},async focus(){await React.act(async()=>{focusCleanup=focusCallback();});},async action(fn){let result;await React.act(async()=>{result=await fn(latest);});return result;},async flush(fn=()=>{}){await React.act(async()=>{fn();await Promise.resolve();});},async close(){await React.act(async()=>root.unmount());dom.window.close();delete global.window;delete global.document;delete global.IS_REACT_ACT_ENVIRONMENT;}};
}

test('business import double tap stays single-flight and uncertain retry retains request ID',async()=>{
 const f=await setup();try{
 f.setHandler(async url=>url.endsWith('/preview')?preview:envelope());await f.action(s=>s.pick());
 const pending=deferred();f.setHandler(()=>pending.promise);let first;
 await f.flush(()=>{first=f.state.commit();void f.state.commit();});
 assert.equal(f.calls.filter(c=>c.url==='/business/import').length,1);const sent=f.calls.at(-1).options.body;
 await f.flush(()=>pending.reject(new Error('network uncertain')));await first;assert.equal(f.state.hasPending,true);
 f.setHandler(async()=>({workspace:{...workspace,revision:1,employees:[{...employee,id:'employee-id'}]}}));await f.action(s=>s.commit());
 const imports=f.calls.filter(c=>c.url==='/business/import');assert.equal(imports.length,2);assert.equal(imports[1].options.body.request_id,sent.request_id);assert.equal(f.state.workspace.employees.length,1);assert.equal(f.state.hasPending,false);
 }finally{await f.close();}
});
test('file picker completing after route leave/reentry cannot upload old selection',async()=>{
 const f=await setup();try{const pending=deferred();f.setPicker(()=>pending.promise);let picking;await f.flush(()=>{picking=f.state.pick();});await f.blur();await f.focus();await f.flush(()=>pending.resolve({filename:'private.csv',content_base64:'abc'}));await picking;assert.equal(f.calls.filter(c=>c.url.endsWith('/preview')).length,0);assert.equal(f.state.preview,null);}finally{await f.close();}
});
test('responses from a previous account are ignored and abort on blur',async()=>{
 const f=await setup();try{const pending=deferred();f.setHandler(()=>pending.promise);let loading;await f.flush(()=>{loading=f.state.load();});const signal=f.calls.at(-1).options.signal;f.setOwner('different-owner');await f.blur();assert.equal(signal.aborted,true);await f.flush(()=>pending.resolve({...envelope(),workspace:{...workspace,company_name:'MUST NOT APPEAR'}}));await loading;assert.equal(f.state.workspace.company_name,'Тестовая компания');}finally{await f.close();}
});
test('stale revision clears pending import and preserves preview for explicit refresh',async()=>{
 const f=await setup();try{f.setHandler(async()=>preview);await f.action(s=>s.pick());f.setHandler(async()=>{throw Object.assign(new Error('Данные изменены'),{status:409});});await f.action(s=>s.commit());assert.equal(f.state.hasPending,false);assert.equal(f.state.preview.employees.length,1);assert.match(f.state.error,/Данные изменены/);}finally{await f.close();}
});
test('open editor uses its original revision even after workspace reload',async()=>{
 const f=await setup();try{f.setHandler(async()=>({...envelope(),workspace:{...workspace,revision:2}}));await f.action(s=>s.load());f.setHandler(async()=>{throw Object.assign(new Error('Conflict'),{status:409});});await f.action(s=>s.saveEmployee('employee-id',employee,0));const mutation=f.calls.findLast(c=>c.options.method==='PATCH');assert.equal(mutation.options.body.expected_revision,0);assert.match(f.state.error,/Conflict/);}finally{await f.close();}
});
test('reload closes a previously generated report before export',async()=>{
 const f=await setup();try{const report={name:'Task',task:'Report',member_count:0,coverage:[],missing_skills:[],available_hours:0,target_hours:null,missing_hours_data:[],next_steps:[],members:[]};f.setHandler(async()=>({report}));await f.action(s=>s.openReport('group-id'));assert.equal(f.state.report.name,'Task');f.setHandler(async()=>envelope());await f.action(s=>s.load());assert.equal(f.state.report,null);}finally{await f.close();}
});

const employeeEnvelope=(revision=1,changes={})=>({...envelope(),workspace:{...workspace,revision,employees:[{...employee,id:'employee-id',experience:'Собрал отчёт по продажам',...changes}]}});
test('employee analysis refreshes the owner workspace each time and derives the returned revision',async()=>{
 const f=await setup();try{
  f.setHandler(async()=>employeeEnvelope(2));await f.action(s=>s.openEmployeeAnalysis('employee-id'));
  assert.equal(f.calls.at(-1).url,'/business');assert.equal(f.state.analysisId,'employee-id');assert.equal(f.state.analysis.workspace_revision,2);assert.equal(f.state.analysis.status,'ready_for_discussion');
  f.setHandler(async()=>employeeEnvelope(3,{skills:[],experience:''}));await f.action(s=>s.openEmployeeAnalysis('employee-id'));
  assert.equal(f.state.analysis.workspace_revision,3);assert.equal(f.state.analysis.status,'needs_evidence');assert.deepEqual(f.state.analysis.skills,[]);
  f.setHandler(async()=>{throw Error('Refresh failed');});assert.equal(await f.action(s=>s.openEmployeeAnalysis('employee-id')),false);assert.equal(f.state.analysis,null);assert.equal(f.state.analysisId,null);
  let exports=0;f.setDeliver(async()=>{exports++;});await f.action(s=>s.exportEmployeeAnalysis());assert.equal(exports,0);
 }finally{await f.close();}
});
test('a removed employee is not analyzed from an older cached profile',async()=>{
 const f=await setup();try{
  f.setHandler(async()=>employeeEnvelope());await f.action(s=>s.openEmployeeAnalysis('employee-id'));
  f.setHandler(async()=>envelope());assert.equal(await f.action(s=>s.openEmployeeAnalysis('employee-id')),false);
  assert.equal(f.state.analysis,null);assert.equal(f.state.workspace.employees.length,0);assert.match(f.state.error,/Сотрудник не найден/);
 }finally{await f.close();}
});
test('closing or leaving during employee refresh cannot resurrect an analysis',async()=>{
 const f=await setup();try{
  const pending=deferred();f.setHandler(()=>pending.promise);let opening;await f.flush(()=>{opening=f.state.openEmployeeAnalysis('employee-id');});
  await f.action(s=>s.closeEmployeeAnalysis());await f.flush(()=>pending.resolve(employeeEnvelope()));assert.equal(await opening,false);assert.equal(f.state.analysis,null);assert.equal(f.state.error,'');
  const leaving=deferred();f.setHandler(()=>leaving.promise);await f.flush(()=>{opening=f.state.openEmployeeAnalysis('employee-id');});const signal=f.calls.at(-1).options.signal;
  await f.blur();assert.equal(signal.aborted,true);f.setHandler(async()=>employeeEnvelope(5,{experience:'Новые данные'}));await f.focus();
  await f.flush(()=>leaving.resolve(employeeEnvelope(1)));await opening;assert.equal(f.state.analysis,null);assert.equal(f.state.workspace.revision,5);
 }finally{await f.close();}
});
test('save and analyze sends edited values and original revision before refreshing the persisted result',async()=>{
 const f=await setup();try{
  const edited={...employee,skills:['SQL'],experience:'Создал запрос и сверил результат',hours_per_week:0};
  f.setHandler(async(url,options)=>options.method==='PATCH'?{workspace:employeeEnvelope(2,edited).workspace}:employeeEnvelope(2,edited));
  assert.equal(await f.action(s=>s.saveAndAnalyzeEmployee('employee-id',edited,0)),true);
  const last=f.calls.slice(-2);assert.equal(last[0].options.method,'PATCH');assert.equal(last[0].options.body.expected_revision,0);assert.deepEqual(last[0].options.body.employee,edited);assert.equal(last[1].url,'/business');
  assert.equal(f.state.analysis.workspace_revision,2);assert.deepEqual(f.state.analysis.skills,['SQL']);assert.equal(f.state.analysis.hours_per_week,0);
 }finally{await f.close();}
});
test('failed or cancelled save never calculates an unsaved profile or opens a later analysis',async()=>{
 const f=await setup();try{
  f.setHandler(async()=>{throw Object.assign(Error('Conflict'),{status:409});});const before=f.calls.length;
  assert.equal(await f.action(s=>s.saveAndAnalyzeEmployee('employee-id',employee,0)),false);assert.equal(f.calls.length,before+1);assert.equal(f.state.analysis,null);
  const pending=deferred();f.setHandler(()=>pending.promise);let saving;await f.flush(()=>{saving=f.state.saveAndAnalyzeEmployee('employee-id',employee,0);});const count=f.calls.length;
  await f.action(s=>s.closeEmployeeAnalysis());await f.flush(()=>pending.resolve({workspace:employeeEnvelope().workspace}));assert.equal(await saving,false);assert.equal(f.calls.length,count);assert.equal(f.state.analysis,null);
 }finally{await f.close();}
});
test('reload and mutations clear the current analysis before a request can fail',async()=>{
 const f=await setup();try{
  for(const action of [s=>s.load(),s=>s.saveEmployee('employee-id',employee,1)]){
   f.setHandler(async()=>employeeEnvelope());await f.action(s=>s.openEmployeeAnalysis('employee-id'));
   const pending=deferred();f.setHandler(()=>pending.promise);let running;await f.flush(()=>{running=action(f.state);});assert.equal(f.state.analysis,null);
   await f.flush(()=>pending.reject(Error('Request failed')));await running;assert.equal(f.state.analysisId,null);
  }
 }finally{await f.close();}
});
test('employee export uses the open snapshot and invalidates on close, account change and blur',async()=>{
 const f=await setup();try{
  f.setHandler(async()=>employeeEnvelope(4,{experience:'Текущий пример работы'}));await f.action(s=>s.openEmployeeAnalysis('employee-id'));
  let guard,html,count=0;const pending=deferred();f.setDeliver(async(value,options)=>{count++;html=value;guard=options.isCurrent;await pending.promise;});let exporting;
  await f.flush(()=>{exporting=f.state.exportEmployeeAnalysis();void f.state.exportEmployeeAnalysis();});assert.equal(count,1);assert.match(html,/Текущий пример работы/);assert.equal(guard(),true);
  f.setOwner('other');assert.equal(guard(),false);f.setOwner('owner');await f.action(s=>s.closeEmployeeAnalysis());assert.equal(guard(),false);
  await f.flush(()=>pending.resolve());await exporting;
  await f.action(s=>s.openEmployeeAnalysis('employee-id'));f.setDeliver(async(value,options)=>{guard=options.isCurrent;});await f.action(s=>s.exportEmployeeAnalysis());assert.equal(guard(),true);await f.blur();assert.equal(guard(),false);assert.equal(f.state.analysis,null);
 }finally{await f.close();}
});
