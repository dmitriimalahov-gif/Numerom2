export type SchemeEntry={id:string;title:string;summary:string;meaning:string;reading:{label:string;text:string}[];focus:string;narration:{id:string;text:string};sources:string[];kind?:'key'|'birth-days'|'line'|'personal'|'cell';digit?:number;count?:number};
export type SchemeCatalog={version:number|string;locale:string;method:{id:string;title:string;text:string;narration:{id:string;text:string};notes?:string[]};entries:SchemeEntry[]};
export function schemeCatalog(value:unknown,assetIds?:string[]):SchemeCatalog;
export function filterSchemes<T extends SchemeEntry & {group:string}>(entries:T[],group:string,query:string):T[];
export function adjacentScheme<T extends {id:string}>(entries:T[],id:string,offset:number):T|null;
