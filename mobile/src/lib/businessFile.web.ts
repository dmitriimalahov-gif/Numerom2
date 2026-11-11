import * as DocumentPicker from 'expo-document-picker';
import {businessTemplate,validateBusinessFile} from './business';

export async function pickBusinessFile():Promise<{filename:string;content_base64:string}|null>{
 const result=await DocumentPicker.getDocumentAsync({type:['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','text/csv','text/comma-separated-values'],multiple:false,copyToCacheDirectory:true,base64:false});
 if(result.canceled)return null;
 const asset=result.assets[0];if(!asset?.file)throw new Error('Не удалось открыть выбранный файл.');
 const filename=validateBusinessFile(asset.name,asset.file.size);
 const content_base64=await new Promise<string>((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>{const data=String(reader.result),comma=data.indexOf(',');if(comma<0)reject(new Error('Не удалось прочитать таблицу.'));else resolve(data.slice(comma+1));};reader.onerror=()=>reject(new Error('Не удалось прочитать таблицу.'));reader.onabort=()=>reject(new Error('Чтение таблицы отменено.'));reader.readAsDataURL(asset.file!);});
 return {filename,content_base64};
}
export async function saveBusinessTemplate(filename:string,content:string):Promise<void>{
 const template=businessTemplate(filename,content),url=URL.createObjectURL(new Blob([template.content],{type:'text/csv;charset=utf-8'})),anchor=document.createElement('a');
 anchor.href=url;anchor.download=template.filename;anchor.style.display='none';document.body.appendChild(anchor);
 try{anchor.click();}finally{anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);}
}
