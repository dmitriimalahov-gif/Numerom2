export type VedicKind='schedule'|'daily'|'weekly'|'monthly'|'quarterly';
export interface VedicDraft {kind:VedicKind;date:string;city:string;birth_date:string;location?:{latitude:number;longitude:number}}
export interface VedicRequest extends VedicDraft {request_id:string;expected_cost:number}
export interface VedicDay {date:string;weekday:string;ruler:string;energies:{key:string;title:string;digit:number;value:number}[];average:number|null;sunrise:string;sunset:string;periods:{id:string;title:string;start:string;end:string;meaning:string}[];hours:{hour:number;planet:string;title:string;start:string;end:string;period:string}[];activities:string[];day_type_label:string}
export interface VedicReport {version:1;kind:VedicKind;title:string;city:string;timezone:string;start_date:string;end_date:string;birth_date:string;profile_name:string;wisdom?:{value:number;destiny:number;full_name_number:number;calculation:string}|null;wisdom_note?:string;days:VedicDay[];meaning:string;method:string;focus:string;narration_id:string}
export interface VedicReceipt {id:string;request_id:string;created_at:string;cost:number;results:VedicReport}
export const kinds:Record<VedicKind,number>;
export const titles:Record<VedicKind,string>;
export function vedicCatalog(value:unknown):Record<VedicKind,number|null>;
export function vedicReceipt(value:unknown):VedicReceipt;
export function validateDraft(value:unknown):string;
export function routeGeometry(days:VedicDay[]):{x:number;y:number;value:number;date:string}[];
export function createVedicController(options:{catalog:()=>Promise<unknown>;history:()=>Promise<unknown>;calculate:(body:VedicRequest)=>Promise<unknown>;refreshBalance:()=>Promise<void>;makeId:()=>string;isCurrent?:()=>boolean;onInsufficientCredits?:(details:{balance:number;cost:number})=>void;pendingStore?:{get():Promise<any>;set(value:any):Promise<void>}}):{getSnapshot:()=>{catalog:Record<VedicKind,number|null>|null;history:VedicReceipt[];result:VedicReceipt|null;loading:boolean;busy:boolean;error:string;balanceError:string;pending:VedicRequest|null};subscribe:(fn:()=>void)=>()=>void;load:()=>Promise<void>;select:(receipt:VedicReceipt)=>void;refreshBalance:()=>Promise<void>;retry:()=>Promise<void>;calculate:(draft:VedicDraft,balance:number|undefined)=>Promise<void>};
