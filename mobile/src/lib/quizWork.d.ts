import type {LessonQuiz,QuizResult} from './learning';
import type {DraftState} from './exerciseDraft';
export interface QuizWork {submission_id:string;answers:Record<string,string>;index:number;stage:'editing'|'submitting'}
export interface QuizWorkState {draft:DraftState;work:QuizWork|null;result:QuizResult|null;busy:boolean;error:string;invalid:boolean}
export function parseWork(text:string,quiz:LessonQuiz):QuizWork|null;
export function createQuizWork(options:{read:()=>Promise<unknown>;write:(body:unknown)=>Promise<unknown>;submit:(body:unknown)=>Promise<unknown>;makeId:()=>string;lessonId:string;quiz:LessonQuiz;onSaved?:()=>Promise<void>;isCurrent?:()=>boolean;delay?:number}):{
 getSnapshot:()=>QuizWorkState;subscribe:(fn:()=>void)=>()=>void;load:()=>Promise<void>;flush:()=>Promise<boolean>;dispose:()=>void;answer:(id:string,value:string)=>void;go:(index:number)=>void;start:()=>Promise<void>;submit:()=>Promise<void>;keepMine:()=>Promise<boolean>;useServer:()=>Promise<void>;
};
