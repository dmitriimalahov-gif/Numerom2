export function createMaterialAccess(options:{openUrl:(url:string)=>Promise<unknown>;isCurrent?:()=>boolean;validateUrl?:(url:string)=>string}):{
 getSnapshot:()=>{opening:string|null;error:string};
 subscribe:(listener:()=>void)=>()=>void;
 isOpening:()=>boolean;
 cancel:()=>void;
 open:(key:string,resolve:(signal:AbortSignal)=>Promise<string>)=>Promise<void>;
};
