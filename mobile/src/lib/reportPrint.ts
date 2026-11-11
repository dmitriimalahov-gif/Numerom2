import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';
import {File,Paths} from 'expo-file-system';
import {Linking} from 'react-native';
import {reportName} from './reportName';
/** Native printing renders self-contained HTML locally; nothing is uploaded. */
export async function deliverReport(html:string,options:{isCurrent?:()=>boolean;filename?:string}={}):Promise<void>{
 const ensureCurrent=()=>{if(options.isCurrent&&!options.isCurrent())throw new Error('Экспорт отменён');};
 ensureCurrent();
 if(!await Sharing.isAvailableAsync()){
  ensureCurrent();await Print.printAsync({html});return;
 }
 ensureCurrent();
 const {uri}=await Print.printToFileAsync({html,width:595,height:842});
 // The share sheet saves the file under its own name: «10.01.1982 Иван Петров — полный разбор.pdf».
 let file=new File(uri);
 try{
  ensureCurrent();
  const named=new File(Paths.cache,`${options.filename??reportName(html)}.pdf`);
  try{if(named.exists)named.delete();await file.move(named);file=named;}catch{/* The printed file keeps its generated name. */}
  ensureCurrent();await Sharing.shareAsync(file.uri,{UTI:'com.adobe.pdf',mimeType:'application/pdf',dialogTitle:'Сохранить отчёт NumerOM'});
 }
 finally{try{file.delete();}catch{/* Sharing can retain its own copy; cleanup only our temporary PDF. */}}
}
export function openReport(url:string){void Linking.openURL(url);}
