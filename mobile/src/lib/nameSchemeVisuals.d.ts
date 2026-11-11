import {NameSchemes} from './comprehensiveReport';
export interface NameVisualNode {
  id:string;x:number;y:number;radius:number;value:number;title:string;formula:string;meaning:string;
  row?:number;column?:number;letter?:string;labelY?:number;labelLines?:string[];
}
export interface NameVisualSeries {
  kind:'sequence'|'distribution';title:string;width:number;height:number;baseline:number;note:string;
  points:{id:string;label:string;value:number;x:number;y:number}[];
  ticks:{value:number;y:number}[];
}
export interface NameDiagram {
  kind:'triangle'|'human';width:number;height:number;nodes:NameVisualNode[];
  edges:{from:string;to:string}[];letters:{id:string;text:string;x:number;y:number}[];
  series:NameVisualSeries|null;
}
export function nameSchemeVisuals(data:NameSchemes|null|undefined):{triangle:NameDiagram|null;human:NameDiagram|null};
