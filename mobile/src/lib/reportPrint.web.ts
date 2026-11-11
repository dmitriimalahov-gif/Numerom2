import {reportPdfUrl} from './reportPdf';
import {reportName} from './reportName';
import {readyReport} from './readyReport';
/**
 * Prepares a server-made PDF of this report while the app stays on screen. A tab opened before the upload sent
 * the app to the background on iPhones, which then cut the upload off; the PDF now opens from a tap on «Открыть PDF».
 */
export async function deliverReport(html:string,options:{isCurrent?:()=>boolean;filename?:string}={}):Promise<void>{
 const isCurrent=()=>!options.isCurrent||options.isCurrent();
 if(!isCurrent())throw new Error('Экспорт отменён');
 readyReport.set(null);
 const file=await reportPdfUrl(html,options.filename??reportName(html));
 if(!isCurrent())throw new Error('Экспорт отменён');
 readyReport.set(file);
}
/** Called from the tap on «Открыть PDF»; a blocked tab falls back to opening the PDF in this one. */
export function openReport(url:string){
 const view=window.open(url,'_blank');
 if(view)view.opener=null;
 else window.location.assign(url);
}
