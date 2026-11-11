import {useRef,useState} from 'react';
import {Platform,Text,View} from 'react-native';
import {Button,Notice,s} from './ui';
import {deliverReport} from '../lib/reportPrint';
export function SavedReportExport({document,title,note}:{document:()=>string;title?:string;note?:string}){
 const lock=useRef(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function save(){if(lock.current)return;lock.current=true;setBusy(true);setError('');try{await deliverReport(document());}catch(e){setError(e instanceof Error?e.message:'Не удалось подготовить PDF.');}finally{lock.current=false;setBusy(false);}}
 return <View style={{gap:10}}><Button secondary title={title??(Platform.OS==='web'?'Скачать или напечатать PDF':'Сохранить отчёт PDF')} busy={busy} onPress={()=>void save()}/><Text style={s.small}>{note??'Все значения, графики и пояснения из сохранённого разбора.'} Баллы не списываются.{Platform.OS==='web'?' Когда PDF будет готов, внизу экрана появится кнопка «Открыть PDF»: сохраните, отправьте или распечатайте файл.':''}</Text>{!!error&&<Notice message={error}/>}</View>;
}
