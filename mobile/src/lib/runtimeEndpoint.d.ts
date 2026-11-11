export interface EndpointConfig {v:number;api:string;iat:number;sig:string}
export function verifyEndpoint(value:unknown,publicKey:string,now?:number):boolean;
export function createEndpointResolver(options:{bundled:EndpointConfig;publicKey:string;configUrl:string;storage?:{get():Promise<string|null>;set(value:string):Promise<void>};fetchImpl?:typeof fetch;now?:()=>number;timeoutMs?:number;onChange?:(origin:string)=>void}):{ready():Promise<string>;refresh():Promise<string>;current():string;recover(previous:string):Promise<boolean>};
