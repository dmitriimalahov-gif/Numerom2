/** Motion timing of the paid report video. Pure frame arithmetic over saved values: nothing is recalculated. */
import {focusTimeline} from './timeline.mjs';

const ENTER = 26;    // the chapter title owns the first second
const STAGGER = 6;

/** First frame the voice names each value; values it never names enter one after another after the title. */
export function appearances(chapter, count) {
  const first = new Array(count).fill(null);
  for (const event of focusTimeline(chapter)) {
    const index = event.focusIndex;
    if (Number.isInteger(index) && index >= 0 && index < count && first[index] === null) first[index] = event.fromFrame;
  }
  let fallback = 0;
  return first.map((frame) => ({frame: frame ?? ENTER + STAGGER * fallback++, spoken: frame !== null}));
}

const lower = (text) => String(text).toLowerCase().replace(/ё/g, 'е');

/** The saved arithmetic line of a value («Задача 1: |1 − 1| = 0 → 0» → «|1 − 1| = 0 → 0»), or ''. */
export function formulaFor(section, index) {
  if (section?.position_readings?.length) return '';
  const label = String(section?.values?.[index]?.label ?? '');
  for (const part of label.split(' · ').map((p) => p.trim()).filter(Boolean)) {
    const head = lower(part);
    const step = (section.steps ?? []).find((s) => lower(s).startsWith(head) && /^[:. ]/.test(s.slice(part.length)));
    if (!step) continue;
    const rest = step.slice(part.length).replace(/^[:.]?\s*/, '');
    // Keep only the arithmetic of narrative steps: «…; День рождения: 10; 1 + 0 = 1; Итог: 1» → «1 + 0 = 1».
    const pieces = rest.split(/;\s*|\.\s+/).map((p) => p.trim()).filter((p) => p && !/^итог/i.test(p));
    const arithmetic = pieces.filter((p) => /\d/.test(p) && /[=→+−×|]| - /.test(p)).map((p) => p.replace(/^[^:]*:\s*(?=[\d|(])/, ''));
    // A value taken as is in a narrative step («Число ума. …; Месяц рождения: 1») becomes «Месяц рождения: 1 → 1»;
    // a list step («Солнце: 1; Луна: 9; …») has no formula of its own.
    const source = step[part.length] === '.' && pieces.find((p) => /^[А-ЯЁа-яё ]+:\s*\d+$/.test(p));
    const value = section.values[index].value;
    const formula = arithmetic.length ? arithmetic.join(' · ') : source && value !== null ? `${source} → ${value}` : '';
    return formula.length > 96 ? formula.slice(0, 95) + '…' : formula;
  }
  return '';
}

/** Saved calculation lines that belong to no single value («1001 × 1982 = 1983982», «Первая граница: 27 − 4 = 23 лет»). */
export function sharedSteps(section) {
  if (section?.position_readings?.length) return [];
  const parts = (section?.values ?? []).flatMap((value) => String(value.label).split(' · ').map((p) => lower(p.trim())).filter(Boolean));
  return (section?.steps ?? []).filter((step) => {
    const text = lower(step);
    return !parts.some((part) => text.startsWith(part) && /^[:. ]/.test(step.slice(part.length)))
      && !/^а[1-4]:/.test(text) && /\d/.test(step) && /[=×−→]/.test(step) && step.length <= 90;
  });
}

/** The А1–А4 number the voice has named last on the current caption page, or null. */
export function spokenExtra(caption, frame) {
  const said = String(caption.text || '').split(/\s+/).filter(Boolean).slice(0, spokenWords(caption, frame));
  for (let i = said.length - 1; i >= 0; i--) {
    const match = said[i].match(/^[АAаa]([1-4])\b/);
    if (match) return 'А' + match[1];
  }
  return null;
}

/** Additional numbers of the Pythagorean square from its saved steps: «А1: … = 22» → [{label: 'А1', value: '22'}]. */
export function extraNumbers(section) {
  return (section?.steps ?? []).map((step) => step.match(/^(А[1-4]):.*=\s*(\d+)\s*$/)).filter(Boolean)
    .map((match) => ({label: match[1], value: match[2]}));
}

const words = (text) => lower(text).replace(/[^а-яa-z0-9]+/g, ' ').trim();
const tokens = (text) => words(text).split(' ').filter(Boolean);
// Recognised speech differs in endings and short words («Потоки ярких идей» for «В потоке ярких идей»).
const alike = (a, b) => a === b || (a.length > 4 && b.length > 4 && a.slice(0, 5) === b.slice(0, 5));

/** When each group title and item of «Главное в вашем разборе» is spoken: the first place, at or after the previous
 *  one, where at least three of its first four words follow each other — also inside a longer recognised phrase. */
export function highlightCues(chapter, highlights) {
  const segments = chapter.segments.map((segment) => ({...segment, tokens: tokens(segment.text)}));
  const locate = (text, after) => {
    const all = tokens(text);
    for (const skip of [0, 1]) {
      const head = all.slice(skip, skip + 4);
      if (head.length < 2) continue;
      const needed = Math.min(3, head.length);
      for (const segment of segments) {
        if (segment.fromFrame + segment.durationInFrames <= after) continue;
        for (let k = 0; k < segment.tokens.length; k++) {
          const hits = head.filter((word, j) => segment.tokens[k + j] !== undefined && alike(word, segment.tokens[k + j])).length;
          const frame = segment.fromFrame + Math.floor(k / segment.tokens.length * segment.durationInFrames);
          if (hits >= needed && frame >= after) return frame;
        }
      }
    }
    return null;
  };
  let cursor = 0;
  return highlights.map((group) => {
    const title = locate(group.title, cursor) ?? cursor;
    cursor = title;
    const items = group.items.map((item) => {
      const frame = locate(item.text, cursor);
      if (frame !== null) cursor = frame;
      return {...item, fromFrame: frame ?? cursor};
    });
    return {...group, fromFrame: title, items};
  });
}

/** How many words of the current caption page the voice has already said. */
export function spokenWords(caption, frame) {
  const total = String(caption.text || '').split(/\s+/).filter(Boolean).length;
  if (!total || !caption.durationInFrames) return total;
  return Math.max(0, Math.min(total, Math.ceil((frame - caption.fromFrame) / caption.durationInFrames * total)));
}
