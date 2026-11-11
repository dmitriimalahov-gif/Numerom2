import {useRef,useState} from 'react';
import {Platform,Text,View} from 'react-native';
import {Button,Notice,s} from '../ui';
import type {PersonalResultView} from '../../lib/personalReport';
import {personalReportDocument} from '../../lib/reportExport';
import {deliverReport} from '../../lib/reportPrint';
export function ExportReport({result}:{result:PersonalResultView}){
 const [busy,setBusy]=useState(false),[error,setError]=useState('');const lock=useRef(false);
 const exportReport=async()=>{
  if(lock.current)return;lock.current=true;setBusy(true);setError('');
  try{await deliverReport(personalReportDocument(result).html);}
  catch(e){setError(e instanceof Error?e.message:'Не удалось подготовить документ. Повторите экспорт.');}
  finally{lock.current=false;setBusy(false);}
 };
 return <View style={{gap:10}}><Button secondary title={Platform.OS==='web'?'Скачать или напечатать PDF':'Сохранить отчёт PDF'} busy={busy} onPress={()=>void exportReport()}/><Text style={s.small}>{Platform.OS==='web'?'Когда PDF будет готов, внизу экрана появится кнопка «Открыть PDF». ':''}В документ войдут схема, график и все доступные расшифровки. Баллы не списываются.</Text>{!!error&&<Notice message={error}/>}</View>;
}
