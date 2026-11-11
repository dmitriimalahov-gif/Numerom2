import type {Coordinates} from './deviceLocation';
export interface SelectedLocation {city:string;latitude:number;longitude:number;timezone:string}
export interface LocationState {busy:boolean;live:boolean;error:string;message:string;location:SelectedLocation|null;accuracy:number|null;updatedAt:number|null}
export function createLocationSelection(options:{locate:(signal?:AbortSignal)=>Promise<Coordinates>;watchLocation:(next:(point:Coordinates)=>void,error:(error:Error)=>void,signal?:AbortSignal)=>Promise<()=>void>;resolve:(point:{latitude:number;longitude:number})=>Promise<SelectedLocation>;onSelect:(location:SelectedLocation)=>void;isCurrent?:()=>boolean;now?:()=>number}):{
 getSnapshot:()=>LocationState;subscribe:(listener:()=>void)=>()=>void;locate:()=>Promise<void>;startLive:()=>Promise<void>;stop:(message?:string)=>void;clear:()=>void;
};
export function distance(a:{latitude:number;longitude:number},b:{latitude:number;longitude:number}):number;
export function validPoint(point:unknown):boolean;
