export const RATES: number[];
export function validRate(value: unknown): number;
export function getPlaybackRate(): number;
export function setPlaybackRate(value: unknown): number;
export function subscribePlaybackRate(listener: (rate: number) => void): () => void;
export function rateLabel(value: number): string;
export function reportPlaybackRate(encodedSpeed:number,selectedRate:number|null,sharedRate:number):number;
