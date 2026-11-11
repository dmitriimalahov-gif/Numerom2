export interface ReportPreview {birth_date:string;use_profile:boolean;profile_fingerprint:string|null;available:{id:string;title:string}[];excluded:{title:string;reason:string}[];message?:string;profile_snapshot?:{version:number;fields:Record<string,string>}}
export function profileRevision(user:unknown):string;
export function reportPreview(raw:unknown,birth:string,useProfile:boolean):ReportPreview;
