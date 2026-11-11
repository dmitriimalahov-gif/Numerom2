import {PortraitIdentity} from './symbolicPortrait';
export interface EmployeeNumerom {
 version:number;birthDate:string|null;note:string;nameMethod:string;notes:string[];
 indicators:{key:string;title:string;value:number;base:number;master:boolean;formula:string;context:string}[];
 themes:{digit:number;planet:string;title:string;summary:string;strength:string;practice:string;question:string;indicators:string[];sources:string[]}[];
}
export function employeeNumerom(value:PortraitIdentity):EmployeeNumerom;
export function employeeNumeromHtml(value:EmployeeNumerom,options?:{compact?:boolean}):string;
