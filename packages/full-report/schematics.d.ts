import type {FullReport,ReportSection} from './index';
export type DiagramEntry={id:string;label:string;value:number|string|null;detail?:string;row?:number;column?:number;letter?:string};
export type Diagram={version:1;kind:'personal'|'square'|'lines'|'sequence'|'tasks'|'individual'|'series'|'period'|'bars'|'triangle'|'human';title:string;subtitle:string;width:640;height:number;entries:DiagramEntry[];cells?:{digit:number;count:number;digits:string;label:string}[];directions?:{id:string;label:string;digits:number[];value:number}[];years?:{age:number;year:number;value:number}[];periods?:{index:number;start:number;end:number}[];bounds?:{start:number;end:number};vedic?:boolean};
export function sectionDiagram(report:FullReport,section:ReportSection):Diagram|null;
/** Rejects malformed models. Only generated shapes and escaped text are emitted. */
export function diagramSvg(diagram:Diagram,options?:{activeIndex?:number;width?:number;height?:number}):string;
/** Optional magnified inset bounds; callers retain the full diagram alongside. */
export function diagramFocusBounds(diagram:Diagram,activeIndex:number):{x:number;y:number;width:number;height:number}|null;
