import type {PersonalResultView} from './personalReport';
export interface PersonalReceipt {id:string;birth_date:string;created_at:string;request_id:string|null;cost:number|null;view:PersonalResultView}
export function createPersonalPaidController(options:{catalog:()=>Promise<unknown>;history:()=>Promise<unknown>;calculate:(body:unknown)=>Promise<unknown>;makeId:()=>string;refreshBalance:()=>Promise<void>;isCurrent?:()=>boolean;onInsufficientCredits?:(details:{balance:number;cost:number})=>void;pendingStore:{get():Promise<unknown>;set(value:unknown):Promise<void>}}):{
 getSnapshot():{catalog:{personal:number}|null;history:PersonalReceipt[];result:PersonalReceipt|null;loading:boolean;busy:boolean;pending:unknown;error:string;balanceError:string};
 subscribe(fn:()=>void):()=>void;load():Promise<void>;retry():Promise<void>;refreshBalance():Promise<void>;select(row:PersonalReceipt):void;calculate(body:{kind:'personal';birth_date:string},balance:number|undefined):Promise<void>;
};
