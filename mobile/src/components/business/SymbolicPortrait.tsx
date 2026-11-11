import {useCallback,useEffect,useRef,useState} from 'react';
import {AppState,Platform,Text,View} from 'react-native';
import {useFocusEffect} from 'expo-router';
import {Button,Card,Notice,s} from '../ui';
import {NameSchemes} from '../numbers/NameSchemes';
import {InterpretationSheet,type SchemeInterpretation} from '../numbers/InterpretationSheet';
import {NarrationProvider} from '../audio/Narration';
import {type Employee} from '../../lib/business';
import {symbolicPortrait,symbolicPortraitHtml} from '../../lib/symbolicPortrait';
import {deliverReport} from '../../lib/reportPrint';
import {useSession} from '../../lib/session';

export function SymbolicPortrait({employee,busy,onClose}:{employee:Employee;busy:boolean;onClose:()=>void}){
 const portrait=symbolicPortrait(employee),{session,user}=useSession();
 const [kind,setKind]=useState<'triangle'|'human'>('triangle'),[detail,setDetail]=useState<SchemeInterpretation|null>(null),[exporting,setExporting]=useState(false),[error,setError]=useState('');
 const alive=useRef(true),epoch=useRef(0),running=useRef(false),owner=useRef(user?.id).current,token=useRef(session.getToken()).current;
 const current=()=>alive.current&&session.getSnapshot().user?.id===owner&&session.getToken()===token;
 useFocusEffect(useCallback(()=>{alive.current=true;return()=>{alive.current=false;epoch.current++;};},[]));
 useEffect(()=>{
  const cancel=()=>{epoch.current++;};
  const native=AppState.addEventListener('change',state=>{if(state==='background')cancel();});
  const visibility=()=>{if(document.visibilityState==='hidden')cancel();};
  if(Platform.OS==='web')document.addEventListener('visibilitychange',visibility);
  return()=>{alive.current=false;epoch.current++;native.remove();if(Platform.OS==='web')document.removeEventListener('visibilitychange',visibility);};
 },[]);
 const exportPortrait=async()=>{
  if(busy||running.current||!current())return;
  const started=epoch.current;running.current=true;setExporting(true);setError('');
  const isCurrent=()=>current()&&started===epoch.current&&AppState.currentState!=='background'&&(Platform.OS!=='web'||document.visibilityState!=='hidden');
  try{await deliverReport(symbolicPortraitHtml(employee),{isCurrent});}
  catch(e){if(isCurrent())setError(e instanceof Error?e.message:'Не удалось открыть личный отчёт.');}
  finally{running.current=false;if(current())setExporting(false);}
 };
 return <NarrationProvider key={owner} path="/narration/project"><View style={{gap:18}}>
  <Card><Text accessibilityRole="header" style={s.heading}>Личный нумерологический портрет</Text><Text style={s.title}>{portrait.name} {portrait.surname}</Text><Text style={s.body}>{portrait.birthDate||'Дата рождения не указана'}</Text><Text style={s.small}>{portrait.note}</Text></Card>
  <Card><Text style={s.title}>Числа даты рождения</Text><Text style={s.small}>Нажмите число: откроются формула, трактовка из обучения и озвучка.</Text>
   {portrait.numbers.map(n=><View key={n.key} style={{gap:6}}><Button secondary title={`${n.title}: ${n.value}`} onPress={()=>setDetail({title:n.title,value:n.value,meaning:n.knowledge?.summary||'',calculationSummary:n.formula,knowledgeDigit:n.base,...(n.master?{knowledgeMaster:n.value,valueCaption:`Мастер-число ${n.value}. Общая трактовка ниже — для базовой цифры ${n.base}.`}:{})})}/><Text style={s.small}>{n.formula}</Text></View>)}
   {!!portrait.dateNote&&<Text style={s.body}>{portrait.dateNote}</Text>}
  </Card>
  <Card><Text style={s.title}>Схемы имени</Text><View style={{gap:8}}><Button secondary={kind!=='triangle'} title="Абракадабра имени" onPress={()=>setKind('triangle')}/><Button secondary={kind!=='human'} title="Человечек имени" onPress={()=>setKind('human')}/></View><NameSchemes data={portrait.nameSchemes} kind={kind} onSelect={setDetail}/></Card>
  {!!error&&<Notice message={error}/>}
  <Button title="Сохранить личный портрет / PDF" busy={exporting} disabled={busy} onPress={()=>void exportPortrait()}/><Button secondary title="К сотрудникам" disabled={busy||exporting} onPress={onClose}/>
  <InterpretationSheet detail={detail} onClose={()=>setDetail(null)} onProfile={()=>{}}/>
 </View></NarrationProvider>;
}
