export interface ReflectionSource {
  id:string; title:string; path:string; sha256:string; locator:string;
  kind:'course_pdf'|'project_documentation';
}
export interface NumberReflection {
  digit:number; planet:string; title:string; theme:string; sourceIds:string[];
  sourceSummary:string; reflection:string[]; questions:string[]; practice:string;
  comparisonFocus:string; sources:ReflectionSource[];
}
export interface ComparisonReflection {
  first:number; second:number; title:string; intro:string;
  themes:Array<{digit:number;planet:string;theme:string}>;
  questions:string[]; practice:string; sourceNote:string;
}
export function numberReflection(digit:unknown):NumberReflection|null;
export function comparisonReflection(first:unknown,second:unknown):ComparisonReflection|null;
export function reflectionHtml(digit:unknown):string;
