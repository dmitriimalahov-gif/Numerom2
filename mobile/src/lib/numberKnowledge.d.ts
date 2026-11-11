export interface NumberKnowledge {
  digit: number; planet: string; title: string; summary: string; segments: string[];
  audio: {digit: number; path: string; seconds: number; bytes: number; sha256: string; text_sha256: string};
}
export function numberKnowledge(digit: unknown): NumberKnowledge | null;
export const knowledgeNumbers: number[];
export const knowledgeNote: string;
