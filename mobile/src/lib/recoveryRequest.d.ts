export function createRecoveryRequest(options:{request:(email:string)=>Promise<{message:string}>;now?:()=>number;cooldownMs?:number}):{
 getSnapshot:()=>{busy:boolean;message:string;error:string;sentTo:string;retryAt:number};
 subscribe:(listener:()=>void)=>()=>void;
 remainingSeconds:()=>number;
 changeAddress:()=>void;
 submit:(email:string)=>Promise<void>;
 dispose:()=>void;
};
