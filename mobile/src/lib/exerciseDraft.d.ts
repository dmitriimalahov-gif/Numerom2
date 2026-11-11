export interface DraftState {text:string;revision:number;ready:boolean;dirty:boolean;saving:boolean;saved:boolean;error:string;conflict:boolean;pending:unknown|null}
export function createExerciseDraft(options:{read:()=>Promise<unknown>;write:(body:unknown)=>Promise<unknown>;makeId:()=>string;initial?:string;isCurrent?:()=>boolean;delay?:number;maxLength?:number;resetOnClear?:boolean}):{
 getSnapshot:()=>DraftState;subscribe:(listener:()=>void)=>()=>void;load:()=>Promise<void>;flush:()=>Promise<boolean>;setInitial:(text:string)=>void;edit:(text:string)=>void;clear:()=>Promise<boolean>;useServer:()=>Promise<void>;keepMine:()=>Promise<boolean>;dispose:()=>void;
};
