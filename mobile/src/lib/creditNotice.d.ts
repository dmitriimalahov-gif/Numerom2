export interface CreditNotice {balance?:number;cost?:number}
export function createCreditNotice():{
 getSnapshot():CreditNotice|null;
 subscribe(listener:()=>void):()=>void;
 dismiss():void;
 sync(owner:string|null,balance:number|undefined):void;
 insufficient(details:{balance:number;cost:number}):void;
 serverRefused(owner:string):void;
};
export function creditNoticeText(notice:CreditNotice):{title:string;description:string};
