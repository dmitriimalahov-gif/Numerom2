export type LoadingShape =
  | {kind:'rect';x:number;y:number;w:number;h:number;r:number;fill:string;stroke:string;opacity:number}
  | {kind:'text';x:number;y:number;text:string;size:number;weight:number;color:string;opacity:number;anchor?:'start'|'middle'}
  | {kind:'line';x1:number;y1:number;x2:number;y2:number;width:number;color:string;opacity:number};
export function loadingFrame(seconds:number,birthDate?:string|null,reduced?:boolean):{width:number;height:number;shapes:LoadingShape[];stage:number;caption:string};
export const LOADING_CYCLE:number;
export const LOADING_STAGES:string[];
