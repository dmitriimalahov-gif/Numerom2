export interface SchemeCell {digit:number; count:number; digits:string; title:string; meaning:string}
export interface SchemeLine {key:string; digits:number[]; value:number; title:string; meaning:string}
export interface PersonalSchemeView {
  version:1; birthDate:string; method:string; note:string; additionalNumbers:number[];
  cells:SchemeCell[]; lines:SchemeLine[];
}
export function personalScheme(value:unknown,birthDate:string):PersonalSchemeView|null;
