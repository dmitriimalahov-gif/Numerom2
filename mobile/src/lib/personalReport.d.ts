import {PersonalSchemeView} from './personalScheme';
export interface NumberDetailView {
  key: string; shortTitle: string; title: string; value: number | null; meaning: string;
  interpretation: string; method: string; steps: string[]; note: string; detailed: boolean;
}
export interface PersonalReportView {
  birthDate: string; birthWeekday: string; profileName: string; profileParts?: {name:string;surname:string}|null; numbers: NumberDetailView[]; incomplete: boolean;
  scheme: PersonalSchemeView | null;
  planets: {formula: string; calculationNumber: number | null; birthWeekday: string; note: string;
    items: {name: string; value: number; meaning: string}[]} | null;
}
export interface PersonalResultView {report: PersonalReportView; createdAt: string; source: 'saved' | 'new'; id: string}
export interface PersonalCalculationState {
  result: PersonalResultView | null; latestLoading: boolean; latestError: string; latestLoaded: boolean;
  busy: boolean; calculationError: string; balanceLoading: boolean; balanceError: string;
}
export function personalReport(value: unknown, birthDate?: string): PersonalReportView;
export function savedPersonalResult(value: unknown): PersonalResultView | null;
export function calculationPrice(value: unknown): number;
export function calculationBlock(values: {date: string; price: number | null | undefined; balance: number | undefined; balanceError?: string; busy?: boolean}): string;
export function createPersonalCalculationController(options: {
  latest: () => Promise<unknown>; calculate: (date: string) => Promise<unknown>;
  refreshBalance: () => Promise<void>; isCurrent?: () => boolean;
}): {
  getSnapshot(): PersonalCalculationState; subscribe(listener: () => void): () => void;
  start(): Promise<void>; reloadLatest(): Promise<void>; refreshBalance(): Promise<void>;
  calculate(date: string, price: number | null | undefined, balance: number | undefined): Promise<void>;
};
