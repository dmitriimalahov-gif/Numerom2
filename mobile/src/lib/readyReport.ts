import type {ReportFile} from './reportPdf';
// A prepared PDF waiting for a tap: phones open a new tab only straight from a tap, never after a network wait.
let ready:ReportFile|null=null;
const listeners=new Set<()=>void>();
const notify=()=>listeners.forEach(listener=>listener());
export const readyReport={
 get:()=>ready,
 subscribe(listener:()=>void){listeners.add(listener);return()=>{listeners.delete(listener);};},
 set(next:ReportFile|null){ready=next;notify();},
};
