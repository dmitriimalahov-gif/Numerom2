export type VideoChapter = {id:string;title:string;start_seconds:number;duration_seconds:number};
export type ReportVideoState = {status:'waiting_analysis'|'waiting_audio'|'queued'|'rendering'|'ready'|'failed';stage?:'analysis'|'audio'|'video';message:string;progress?:number;audio_ready:number;audio_total:number;seconds?:number;bytes?:number;url?:string;download_url?:string;expires_in?:number;chapters:VideoChapter[];link_until?:number};
export function mediaUrl(value:unknown,origin:string):string;
export function videoState(value:unknown,origin:string):ReportVideoState;
export function retainVideo(previous:ReportVideoState|null,next:ReportVideoState,now?:number):ReportVideoState;
export function videoPollDelay(value:ReportVideoState|null,now?:number):number|null;
