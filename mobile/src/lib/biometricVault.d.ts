export interface VaultStore {get():Promise<string|null>;set(value:string):Promise<void>;remove():Promise<void>}
export interface BiometricVault extends VaultStore {get(unlock?:boolean):Promise<string|null>;enabled():Promise<boolean>;available():boolean;enable(token:string,isCurrent?:()=>boolean):Promise<void>;disable():Promise<void>}
export function createBiometricVault(options:{plain:VaultStore;protectedStore:VaultStore;flag:VaultStore;available:()=>boolean}):BiometricVault;
