import * as DocumentPicker from 'expo-document-picker';
import {File,Paths} from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import {businessTemplate,validateBusinessFile} from './business';

export async function pickBusinessFile():Promise<{filename:string;content_base64:string}|null>{
 const result=await DocumentPicker.getDocumentAsync({type:['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','text/csv','text/comma-separated-values'],multiple:false,copyToCacheDirectory:true,base64:false});
 if(result.canceled)return null;
 const asset=result.assets[0];if(!asset)throw new Error('Не удалось открыть выбранный файл.');
 const file=new File(asset.uri);
 try{
  const filename=validateBusinessFile(asset.name,file.size);
  const content_base64=await file.base64();
  if(!content_base64||content_base64.length>Math.ceil(5*1024*1024/3)*4)throw new Error('Выберите непустой файл размером до 5 МБ.');
  return {filename,content_base64};
 }finally{if(file.uri.startsWith(Paths.cache.uri)){try{file.delete();}catch{/* Only remove the picker cache copy, never the user's source. */}}}
}
export async function saveBusinessTemplate(filename:string,content:string):Promise<void>{
 const template=businessTemplate(filename,content);
 if(!await Sharing.isAvailableAsync())throw new Error('На этом устройстве нельзя сохранить шаблон через меню «Поделиться». Откройте NumerOM в браузере.');
 const file=new File(Paths.cache,`business-${Date.now()}-${template.filename}`);
 try{file.write(template.content);await Sharing.shareAsync(file.uri,{mimeType:'text/csv',UTI:'public.comma-separated-values-text',dialogTitle:'Сохранить шаблон NumerOM Business'});}
 finally{try{file.delete();}catch{/* Share sheet creates its own destination copy. */}}
}
