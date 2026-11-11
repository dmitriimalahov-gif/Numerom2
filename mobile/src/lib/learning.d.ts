import type {ApiClient,Lesson} from '@numerom/api-client';
export interface Exercise {id:string; title:string; description:string; instructions:string; type:string; options:string[]}
export interface Question {id:string; prompt:string; type:string; options:string[]}
export interface LessonQuiz {id:string; title:string; description:string; questions:Question[]; supported:boolean; passingScore:number|null}
export interface LessonFile {id:string; name:string; type:string; extension:string; section:string; size:number|null}
export interface ExerciseResponse {attachments?:string[];id:string; text:string; reviewed:boolean; comment:string; submittedAt:string}
export interface QuizResult {id:string; score:number; passed:boolean; attemptedAt:string; submissionId:string}
export interface LessonProgress {percentage:number; completed:boolean; theoryRead:boolean; exercisesCompleted:number|null; quizPassed:boolean; challengeCompleted:boolean}
export interface QuizPayload {lesson_id:string; quiz_id:string; answers:Record<string,string>; submission_id:string}
export function plainText(value:unknown):string;
export function lessonExercises(lesson:Lesson):Exercise[];
export function lessonQuiz(lesson:Lesson):LessonQuiz|null;
export function lessonFiles(value:unknown):LessonFile[];
export function exerciseResponses(value:unknown):Record<string,ExerciseResponse>;
export function quizResult(value:unknown):QuizResult;
export function quizAttempts(value:unknown):QuizResult[];
export function lessonProgress(value:unknown):LessonProgress;
export function quizPayload(lessonId:string,quiz:LessonQuiz,answers:Record<string,string>,submissionId:string):QuizPayload;
export function exercisePayload(lessonId:string,exercise:Exercise,answer:string):{lesson_id:string;exercise_id:string;response_text:string};
export function safeLearningUrl(value:string):string;
export function submissionId():string;
export function singleFlight():<T>(operation:()=>Promise<T>)=>Promise<T>;

export function quizSubmission():{hasPending:()=>boolean;reset:()=>void;submit:(api:ApiClient,lessonId:string,quiz:LessonQuiz,answers:Record<string,string>)=>Promise<QuizResult>};
