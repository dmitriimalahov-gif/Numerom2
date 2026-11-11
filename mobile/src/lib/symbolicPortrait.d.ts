import {NameSchemes} from './comprehensiveReport';
import {numberKnowledge} from './numberKnowledge';
export type PortraitIdentity={name:string;surname:string;birth_date?:string|null};
export type PortraitNumber={key:string;title:string;value:number;base:number;formula:string;master:boolean;knowledge:ReturnType<typeof numberKnowledge>};
export type SymbolicPortraitView={name:string;surname:string;birthDate:string|null;note:string;numbers:PortraitNumber[];nameSchemes:NameSchemes;dateNote:string};
export function symbolicPortrait(value:PortraitIdentity):SymbolicPortraitView;
export function symbolicPortraitHtml(value:PortraitIdentity):string;
