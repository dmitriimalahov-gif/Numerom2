export interface CitySuggestion {id:string;name:string;country:string;country_code?:string;region:string;label:string;latitude?:number;longitude?:number;timezone?:string}
export interface CitySearchState {items:CitySuggestion[];busy:boolean;error:string}
export function createCitySearch(options:{request:(path:string,options:{signal:AbortSignal})=>Promise<unknown>;delay?:number}):{search:(value:string)=>void;clear:()=>void;dispose:()=>void;getSnapshot:()=>CitySearchState;subscribe:(fn:()=>void)=>()=>void};
