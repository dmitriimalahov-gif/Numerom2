export interface UserProfile {
  id: string; email: string; full_name?: string; name?: string | null; surname?: string | null;
  birth_date?: string; city?: string; phone_number?: string | null; credits_remaining?: number;
  birth_city?: string | null; birth_city_id?: string | null;
  car_number?: string | null; street?: string | null; house_number?: string | null; apartment_number?: string | null; postal_code?: string | null;
  level?: number; full_name_number?: number | null; is_admin?: boolean; is_super_admin?: boolean;
}
export interface Registration { email: string; password: string; full_name: string; birth_date: string; city?: string }
export interface Lesson { id: string; title: string; description?: string; level?: number; order?: number; content?: unknown; [key: string]: unknown }
export interface PersonalNumberDetail {
  key: string; title: string; value: number | null; meaning: string;
  interpretation: string | null; method: string; steps: string[]; note: string | null;
}
export interface PersonalReport {
  version: 1; birth_date: string; birth_weekday: string; profile_name: string | null; profile_parts?: {name:string;surname:string}|null;
  numbers: PersonalNumberDetail[];
  scheme?: {version:1; birth_date:string; method:string; note:string; additional_numbers:number[];
    cells:{digit:number; count:number; digits:string; title:string; meaning:string}[];
    lines:{key:string; digits:number[]; value:number; title:string; meaning:string}[]} | null;
  planets: {formula: string; calculation_number: number | null; birth_weekday: string;
    items: {name: string; value: number; meaning: string}[]; note: string};
}
export interface PersonalNumbers {
  soul_number: number; mind_number: number; destiny_number: number; helping_mind_number: number;
  wisdom_number: number | null; ruling_number: number; full_name_number?: number | null;
  birth_weekday?: string; planetary_strength?: Record<string, number>;
  calculation_details?: {calculation_number: number; start_planet_index: number}; report?: PersonalReport;
}
export interface SavedPersonalCalculation {id: string; birth_date: string; created_at: string; results: PersonalNumbers}
export class ApiError extends Error { constructor(message: string, status?: number, code?: string); status: number; code: string; orderId?: string }
export function resolveBackendUrl(configured?: string, location?: {protocol: string; hostname: string; port: string}): string;
export function validateBirthDate(value: string): boolean;
export interface ApiClient {
 request<T = unknown>(path: string, options?: {method?: string; body?: unknown; signal?: AbortSignal; auth?: boolean; timeoutMs?: number}): Promise<T>;
 login(email: string, password: string): Promise<{access_token: string; user: UserProfile}>;
 requestPasswordReset(email: string): Promise<{message: string}>;
 resetPassword(token: string, password: string): Promise<{message: string}>;
 register(data: Registration): Promise<{access_token: string; user: UserProfile}>;
 profile(): Promise<UserProfile>; updateProfile(data: Partial<UserProfile>): Promise<UserProfile>;
 lessons(): Promise<{lessons: Lesson[]; user_level: number}>;
 lesson(id: string): Promise<{lesson: Lesson; progress: Record<string, unknown>}>;
 calculationCosts(): Promise<{personal_numbers: number}>;
 toolCatalog():Promise<ToolCatalog>;
 toolHistory():Promise<{calculations:ToolReceipt[]}>;
 calculateTool(body:ToolRequest):Promise<ToolReceipt>;
 relationshipCatalog(): Promise<RelationshipCatalog>;
 relationshipHistory(): Promise<{calculations:RelationshipReceipt[]}>;
 calculateRelationships(body:RelationshipRequest): Promise<RelationshipReceipt>;
 personalNumbers(birthDate: string): Promise<PersonalNumbers>;
 latestPersonalNumbers(): Promise<{calculation: SavedPersonalCalculation | null}>;
}
export function createApiClient(options: {baseUrl: string; getBaseUrl?: () => string | Promise<string>; onConnectionFailure?: (origin:string) => boolean | Promise<boolean>; getToken?: () => string | null; fetchImpl?: typeof fetch; timeoutMs?: number; onUnauthorized?: (token: string) => unknown | Promise<unknown>; onInsufficientCredits?: (token: string) => unknown | Promise<unknown>}): ApiClient;
export interface SessionState { status: 'loading' | 'signedOut' | 'signedIn' | 'unavailable' | 'locked'; user: UserProfile | null; error: string | null; needsSignOutRetry?: boolean }
export interface SessionController {
 getToken(): string | null; getSnapshot(): SessionState; subscribe(listener: () => void): () => void;
 lock(): void; restore(unlock?: boolean): Promise<void>; signOut(): Promise<void>; signIn(email: string, password: string): Promise<void>;
 signInWith(loader:()=>Promise<{access_token:string;user:UserProfile}>):Promise<void>; signUp(data: Registration): Promise<void>; invalidate(token: string): Promise<void>; refresh(): Promise<void>;
}
export function createSessionController(options: {api: ApiClient; storage: {get(unlock?: boolean): Promise<string | null>; set(value: string): Promise<void>; remove(): Promise<void>}}): SessionController;
export interface CreditPackage {id:string;title:string;amount_total:number;credits:number;access_days:number;currency:'eur';recurring:false;consultation?:boolean}
export interface PaymentCatalog {packages:CreditPackage[];enabled:boolean;mode:'test'|'live';clients:string[];balance:number;test_balance:number;message:string|null}
export interface Checkout {url:string;session_id:string;order_id:string;mode:'test'|'live';state:string}
export interface PaymentReceipt {order_id:string;session_id:string|null;title:string;credits:number;amount_total:number;currency:'eur';mode:'test'|'live';status:'creating'|'pending'|'processing'|'paid'|'failed'|'expired';payment_status:'paid'|'unpaid';created_at:string}
export function paymentCatalog(value:unknown):PaymentCatalog;
export function stripeCheckout(value:unknown):Checkout;
export function paymentReceipt(value:unknown):PaymentReceipt;
export function paymentMessage(value:PaymentReceipt):string;
export interface RelationshipPerson {name:string;birth_date:string}
export interface RelationshipDraft {kind:'pair'|'group';main:RelationshipPerson;people:RelationshipPerson[]}
export interface RelationshipRequest extends RelationshipDraft {request_id:string;expected_cost:number}
export interface RelationshipMember extends RelationshipPerson {number:number;steps:string[]}
export interface RelationshipConnection {name:string;score:number;title:string;interpretation:string;focus:string;formula:string}
export interface RelationshipReceipt {id:string;request_id:string;created_at:string;cost:number;results:{version:1;kind:'pair'|'group';main:RelationshipMember;people:RelationshipMember[];connections:RelationshipConnection[];average:number;method:string;note:string}}
export interface RelationshipCatalog {pair:number|null;group:number|null}
export interface RelationshipState {catalog:RelationshipCatalog|null;history:RelationshipReceipt[];result:RelationshipReceipt|null;loading:boolean;busy:boolean;error:string;balanceError:string;pending:RelationshipRequest|null}
export function relationshipReceipt(value:unknown):RelationshipReceipt;
export function relationshipCatalog(value:unknown):RelationshipCatalog;
export function createRelationshipController(options:{catalog:()=>Promise<unknown>;history:()=>Promise<unknown>;calculate:(data:RelationshipRequest)=>Promise<unknown>;refreshBalance:()=>Promise<void>;makeId:()=>string;isCurrent?:()=>boolean;onInsufficientCredits?:(details:{balance:number;cost:number})=>void;pendingStore?:{get():Promise<any>;set(value:any):Promise<void>}}):{getSnapshot:()=>RelationshipState;subscribe:(fn:()=>void)=>()=>void;load:()=>Promise<void>;select:(value:RelationshipReceipt)=>void;refreshBalance:()=>Promise<void>;retry:()=>Promise<void>;calculate:(draft:RelationshipDraft,balance:number|undefined)=>Promise<void>};

export type ToolKind='name'|'address'|'car';
export interface ToolDraft {kind:ToolKind;inputs:Record<string,string>}
export interface ToolRequest extends ToolDraft {request_id:string;expected_cost:number}
export type ToolCatalog=Record<ToolKind,number|null>;
export interface ToolItem {key:string;label:string;source:string;number:number;total:number;tokens:{symbol:string;value:number}[];steps:string[];title:string;interpretation:string;focus:string;narration_id:string}
export interface ToolReceipt {id:string;request_id:string;created_at:string;cost:number;results:{version:1;kind:ToolKind;title:string;summary:string;inputs:Record<string,string>;items:ToolItem[];method:string}}
export interface ToolState {catalog:ToolCatalog|null;history:ToolReceipt[];result:ToolReceipt|null;loading:boolean;busy:boolean;error:string;balanceError:string;pending:ToolRequest|null}
export function toolCatalog(value:unknown):ToolCatalog;
export function toolReceipt(value:unknown):ToolReceipt;
export function createToolController(options:{catalog:()=>Promise<unknown>;history:()=>Promise<unknown>;calculate:(data:ToolRequest)=>Promise<unknown>;refreshBalance:()=>Promise<void>;makeId:()=>string;isCurrent?:()=>boolean;onInsufficientCredits?:(details:{balance:number;cost:number})=>void;pendingStore?:{get():Promise<any>;set(value:any):Promise<void>}}):{getSnapshot:()=>ToolState;subscribe:(fn:()=>void)=>()=>void;load:()=>Promise<void>;select:(value:ToolReceipt)=>void;refreshBalance:()=>Promise<void>;retry:()=>Promise<void>;calculate:(draft:ToolDraft,balance:number|undefined)=>Promise<void>};
