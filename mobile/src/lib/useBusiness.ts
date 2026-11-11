import {useCallback,useEffect,useRef,useState} from 'react';
import {AppState,Platform} from 'react-native';
import {useFocusEffect} from 'expo-router';
import {useSession} from './session';
import {businessEnvelope,businessWorkspace,businessPreview,businessReport,businessReportHtml,businessWorkspaceHtml,businessEmployeeAnalysis,businessEmployeeAnalysisHtml,type BusinessEnvelope,type Workspace,type ImportPreview,type EmployeeInput,type GroupInput,type GroupReport} from './business';
import {pickBusinessFile,saveBusinessTemplate} from './businessFile';
import {deliverReport} from './reportPrint';
import {submissionId} from './learning';

export function useBusiness(){
 const {api,session,user}=useSession();
 const owner=useRef(user!.id).current,token=useRef(session.getToken()).current;
 const active=useRef(true),focused=useRef(true),running=useRef(false),epoch=useRef(0),requests=useRef(new Set<AbortController>()),reload=useRef<()=>unknown>(()=>{});
 const [envelope,setEnvelope]=useState<BusinessEnvelope|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState(''),[preview,setPreview]=useState<ImportPreview|null>(null),[filename,setFilename]=useState(''),[report,setReport]=useState<GroupReport|null>(null),[hasPending,setHasPending]=useState(false),[analysisId,setAnalysisId]=useState<string|null>(null);
 const selectedAnalysis=useRef<string|null>(null),analysisVersion=useRef(0);
 const workspace=envelope?.workspace||null,latest=useRef<Workspace|null>(workspace);latest.current=workspace;
 const pending=useRef<{request_id:string;expected_revision:number;employees:EmployeeInput[]}|null>(null);
 const current=()=>active.current&&focused.current&&session.getSnapshot().user?.id===owner&&session.getToken()===token;
 const closeEmployeeAnalysis=()=>{analysisVersion.current++;selectedAnalysis.current=null;setAnalysisId(null);};
 const analysis=workspace&&analysisId&&current()&&workspace.employees.some(e=>e.id===analysisId)?businessEmployeeAnalysis(workspace,analysisId):null;
 const cancel=()=>{epoch.current++;analysisVersion.current++;selectedAnalysis.current=null;requests.current.forEach(c=>c.abort());requests.current.clear();running.current=false;};
 useFocusEffect(useCallback(()=>{active.current=true;focused.current=true;setBusy(false);void reload.current();return()=>{focused.current=false;cancel();setAnalysisId(null);};},[]));
 useEffect(()=>{active.current=true;return()=>{active.current=false;cancel();pending.current=null;};},[]);
 useEffect(()=>{
  const leave=()=>{cancel();setAnalysisId(null);setBusy(false);};
  const native=AppState.addEventListener('change',next=>{if(next==='background')leave();});
  const visibility=()=>{if(document.visibilityState==='hidden')leave();};
  if(Platform.OS==='web')document.addEventListener('visibilitychange',visibility);
  return()=>{native.remove();if(Platform.OS==='web')document.removeEventListener('visibilitychange',visibility);};
 },[]);
 const exportGuard=()=>{const started=epoch.current;return()=>started===epoch.current&&current()&&AppState.currentState!=='background'&&(Platform.OS!=='web'||document.visibilityState!=='hidden');};
 const request=async(path:string,options:Record<string,unknown>={})=>{const controller=new AbortController(),started=epoch.current;requests.current.add(controller);try{const result=await api.request(path,{...options,signal:controller.signal,timeoutMs:60000});if(started!==epoch.current||!current())throw Error('Запрос отменён');return result;}finally{requests.current.delete(controller);}};
 const run=async(action:()=>Promise<void>)=>{
  if(running.current||!current())return false;running.current=true;const turn=epoch.current;setBusy(true);setError('');setNotice('');
  try{await action();return current()&&turn===epoch.current;}
  catch(e){if(current()&&turn===epoch.current&&(e as {name?:string})?.name!=='AbortError')setError(e instanceof Error?e.message:'Не удалось выполнить действие. Обновите данные и повторите.');return false;}
  finally{if(turn===epoch.current){running.current=false;if(current())setBusy(false);}}
 };
 const load=()=>run(async()=>{closeEmployeeAnalysis();setReport(null);const result=businessEnvelope(await request('/business'));if(current()){latest.current=result.workspace;setEnvelope(result);}});
 reload.current=load;
 const setWorkspace=(value:unknown)=>{const next=businessWorkspace(value);if(current()){closeEmployeeAnalysis();latest.current=next;setEnvelope(old=>old?{...old,workspace:next}:old);setReport(null);}};
 const activate=(company_name:string)=>run(async()=>{const result=businessEnvelope(await request('/business/activate',{method:'POST',body:{company_name}}));if(current())setEnvelope(result);});
 const template=()=>run(async()=>{const data=await request('/business/template') as {filename:string;content:string};if(current())await saveBusinessTemplate(data.filename,data.content);});
 const pick=()=>run(async()=>{if(pending.current)throw Error('Сначала проверьте результат предыдущего импорта.');const started=epoch.current;const file=await pickBusinessFile();if(!file||!current()||started!==epoch.current)return;const next=businessPreview(await request('/business/import/preview',{method:'POST',body:file}));if(current()){setPreview(next);setFilename(file.filename);}});
 const commit=()=>run(async()=>{
  if(!pending.current){if(!preview?.valid||!latest.current)throw Error('Сначала исправьте ошибки в файле.');pending.current={request_id:submissionId(),expected_revision:latest.current.revision,employees:preview.employees};setHasPending(true);}
  try{const result=await request('/business/import',{method:'POST',body:pending.current});if(!current())return;setWorkspace(result);pending.current=null;setHasPending(false);setPreview(null);setFilename('');setNotice('Сотрудники добавлены. Заполните рабочие навыки, чтобы планировать команды.');}
  catch(e){if([400,401,403,404,409,413,415,422].includes((e as {status?:number}).status||0)){pending.current=null;if(current())setHasPending(false);}throw e;}
 });
 const mutate=async(path:string,body:Record<string,unknown>,method='POST',expectedRevision?:number)=>{
  closeEmployeeAnalysis();if(!latest.current)throw Error('Откройте бизнес-пространство.');const result=await request(path,{method,body:{expected_revision:expectedRevision??latest.current.revision,...body}});if(current())setWorkspace(result);
 };
 const refreshEmployeeAnalysis=async(id:string)=>{
  closeEmployeeAnalysis();setReport(null);const version=analysisVersion.current;
  const result=businessEnvelope(await request('/business'));
  if(version!==analysisVersion.current)throw Object.assign(Error('Открытие анализа отменено.'),{name:'AbortError'});
  latest.current=result.workspace;setEnvelope(result);
  if(!result.workspace)throw Error('Сначала откройте бизнес-пространство.');
  businessEmployeeAnalysis(result.workspace,id);
  selectedAnalysis.current=id;setAnalysisId(id);
 };
 const openEmployeeAnalysis=(id:string)=>run(()=>refreshEmployeeAnalysis(id));
 const saveAndAnalyzeEmployee=(id:string,employee:EmployeeInput,revision:number)=>run(async()=>{
  closeEmployeeAnalysis();const version=analysisVersion.current;
  if(!latest.current)throw Error('Откройте бизнес-пространство.');
  const result=await request(`/business/employees/${encodeURIComponent(id)}`,{method:'PATCH',body:{expected_revision:revision,employee}});
  if(version!==analysisVersion.current)throw Object.assign(Error('Открытие анализа отменено.'),{name:'AbortError'});
  setWorkspace(result);
  await refreshEmployeeAnalysis(id);
 });
 const saveEmployee=(id:string|null,employee:EmployeeInput,revision:number)=>id?run(()=>mutate(`/business/employees/${encodeURIComponent(id)}`,{employee},'PATCH',revision)):run(async()=>{await mutate('/business/import',{request_id:submissionId(),employees:[employee]},'POST',revision);});
 const removeEmployee=(id:string,revision:number)=>run(()=>mutate(`/business/employees/${encodeURIComponent(id)}/remove`,{},'POST',revision));
 const saveGroup=(id:string|null,group:GroupInput,revision:number)=>run(()=>mutate('/business/groups',{...(id?{id}:{}),group},'POST',revision));
 const removeGroup=(id:string)=>run(()=>mutate(`/business/groups/${encodeURIComponent(id)}/remove`,{}));
 const openReport=(id:string)=>run(async()=>{closeEmployeeAnalysis();const next=businessReport(await request(`/business/groups/${encodeURIComponent(id)}/report`));if(current())setReport(next);});
 const exportWorkspace=()=>run(async()=>{if(!latest.current)throw Error('Сначала откройте сотрудников.');const html=businessWorkspaceHtml(latest.current);if(current())await deliverReport(html,{isCurrent:exportGuard()});});
 const exportReport=()=>run(async()=>{if(!report||!latest.current)throw Error('Сначала откройте отчёт.');const html=businessReportHtml(report,latest.current.company_name);if(current())await deliverReport(html,{isCurrent:exportGuard()});});
 const exportEmployeeAnalysis=()=>run(async()=>{
  const id=selectedAnalysis.current,snapshot=latest.current,version=analysisVersion.current;
  if(!id||!snapshot)throw Error('Сначала откройте анализ сотрудника.');
  const html=businessEmployeeAnalysisHtml(snapshot,id),guard=exportGuard();
  await deliverReport(html,{isCurrent:()=>guard()&&version===analysisVersion.current&&selectedAnalysis.current===id&&latest.current===snapshot});
 });
 return {envelope,workspace,busy,error,notice,preview,filename,report,hasPending,analysisId,analysis,load,activate,template,pick,commit,saveEmployee,saveAndAnalyzeEmployee,removeEmployee,saveGroup,removeGroup,openReport,openEmployeeAnalysis,closeEmployeeAnalysis,exportEmployeeAnalysis,exportReport,exportWorkspace,closeReport:()=>setReport(null),clearPreview:()=>{if(!pending.current){setPreview(null);setFilename('');}}};
}
