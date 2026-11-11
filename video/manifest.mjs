import path from 'node:path';
import schematics from '../packages/full-report/schematics.js';

const text = (value, name, max = 20000) => {
  if (typeof value !== 'string' || value.length > max || value.includes('\0')) throw new Error(`Invalid ${name}`);
  return value;
};
const integer = (value, name, minimum, maximum) => {
  if (!Number.isSafeInteger(value) || value < minimum || value > maximum) throw new Error(`Invalid ${name}`);
  return value;
};
const list = (value, name, maximum) => {
  if (!Array.isArray(value) || value.length > maximum) throw new Error(`Invalid ${name}`);
  return value;
};
const numeric = (value, name) => {
  if (typeof value !== 'number' || !Number.isFinite(value) || Math.abs(value) > 1000000000) throw new Error(`Invalid ${name}`);
  return value;
};

function canonicalDiagram(input) {
  // Do not pass unknown caller fields (including paths and URLs) to Chromium.
  // The canonical renderer validates every semantic value in this allowlist.
  const diagram = Object.fromEntries(['version', 'kind', 'title', 'subtitle', 'width', 'height', 'vedic']
    .filter((key) => input[key] !== undefined).map((key) => [key, input[key]]));
  const select = (rows, keys) => rows.map((row) => Object.fromEntries(keys.filter((key) => row[key] !== undefined)
    .map((key) => [key, row[key]])));
  diagram.entries = select(input.entries ?? [], ['id', 'label', 'value', 'detail', 'row', 'column', 'letter']);
  if (input.cells) diagram.cells = select(input.cells, ['digit', 'count', 'digits', 'label']);
  if (input.directions) diagram.directions = select(input.directions, ['id', 'label', 'digits', 'value']);
  if (input.years) diagram.years = select(input.years, ['age', 'year', 'value']);
  if (input.periods) diagram.periods = select(input.periods, ['index', 'start', 'end']);
  if (input.bounds) diagram.bounds = {start: input.bounds.start, end: input.bounds.end};
  schematics.diagramSvg(diagram);
  return structuredClone(diagram);
}

function sectionOf(input, report) {
  if (input === undefined) return undefined;
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw new Error('Invalid section');
  const section = {
    id: text(input.id, 'section id', 100),
    title: text(input.title, 'section title', 240),
    paragraphs: list(input.paragraphs ?? [], 'paragraphs', 40).map((p) => text(p, 'paragraph')),
    // The saved arithmetic lines («Задача 1: |1 − 1| = 0») are shown beside the number the voice names.
    steps: list(input.steps ?? [], 'steps', 240).map((step) => text(step, 'step', 2000)),
    values: list(input.values ?? [], 'values', 120).map((v) => ({
      label: text(v.label, 'value label', 240),
      value: v.value === null ? null : typeof v.value === 'string' ? text(v.value, 'value', 160) : numeric(v.value, 'value'),
      meaning: text(v.meaning ?? '', 'meaning'),
    })),
  };
  if (input.chart !== undefined) {
    if (!['matrix', 'bars', 'series'].includes(input.chart?.type)) throw new Error('Invalid chart type');
    const items = list(input.chart.items, 'chart items', 120).map((item) => ({
      label: text(item.label, 'chart label', 240), value: numeric(item.value, 'chart value'),
    }));
    if (input.chart.type === 'matrix' && items.length !== 9) throw new Error('Matrix must contain nine ordered cells');
    section.chart = {type: input.chart.type, items};
  }
  const diagram = input.diagram ?? (report ? schematics.sectionDiagram(report, input) : null);
  if (diagram !== null && diagram !== undefined) {
    // The canonical shared renderer validates its exact semantic schema before
    // browser startup. No arbitrary SVG, CSS or URL can be supplied by a caller.
    if (!diagram || diagram.version !== 1 || typeof diagram.kind !== 'string'
      || JSON.stringify(diagram).length > 150000) throw new Error('Invalid canonical diagram');
    section.diagram = canonicalDiagram(diagram);
  }
  return section;
}

export function validateManifest(input) {
  if (!input || input.version !== 1 || input.fps !== 24 || input.width !== 1280 || input.height !== 720) {
    throw new Error('Expected manifest version 1, 1280×720 at 24 fps');
  }
  const chapters = list(input.chapters, 'chapters', 200).map((chapter) => {
    const durationInFrames = integer(chapter.durationInFrames, 'chapter duration', 1, 24 * 3600);
    const audioPath = text(chapter.audioPath, 'audio path', 4096);
    if (!path.isAbsolute(audioPath) || !audioPath.toLowerCase().endsWith('.m4a')) throw new Error('Audio must be an absolute local m4a path');
    let previousEnd = 0;
    const segments = list(chapter.segments, 'segments', 500).map((segment) => {
      const fromFrame = integer(segment.fromFrame, 'segment start', 0, durationInFrames - 1);
      const duration = integer(segment.durationInFrames, 'segment duration', 1, durationInFrames);
      if (fromFrame < previousEnd || fromFrame + duration > durationInFrames) throw new Error('Segments must be ordered, non-overlapping and inside their chapter');
      previousEnd = fromFrame + duration;
      const result = {fromFrame, durationInFrames: duration, text: text(segment.text, 'segment text')};
      if (segment.focusIndex !== undefined && segment.focusIndex !== null) result.focusIndex = integer(segment.focusIndex, 'focus index', 0, 1000000);
      if (segment.timingSource !== undefined) {
        if (!['asr', 'estimated'].includes(segment.timingSource)) throw new Error('Invalid timing source');
        result.timingSource = segment.timingSource;
      }
      if (segment.focusCues !== undefined) {
        let previousFocusEnd = fromFrame;
        result.focusCues = list(segment.focusCues, 'focus cues', 120).map((cue) => {
          const start = integer(cue.fromFrame, 'focus start', fromFrame, fromFrame + duration - 1);
          const length = integer(cue.durationInFrames, 'focus duration', 1, duration);
          if (start < previousFocusEnd || start + length > fromFrame + duration) throw new Error('Focus cues must be ordered and inside their segment');
          if (cue.timingSource !== undefined && !['estimated', 'asr-word'].includes(cue.timingSource)) throw new Error('Invalid focus timing source');
          previousFocusEnd = start + length;
          return {fromFrame: start, durationInFrames: length, focusIndex: integer(cue.focusIndex, 'focus index', 0, 1000000),
            ...(cue.timingSource ? {timingSource: cue.timingSource} : {})};
        });
      }
      return result;
    });
    return {id: text(chapter.id, 'chapter id', 120), title: text(chapter.title, 'chapter title', 240),
      audioPath, durationInFrames, segments, section: sectionOf(chapter.section, input.report)};
  });
  if (!chapters.length) throw new Error('Manifest needs at least one narrated chapter');
  if (new Set(chapters.map((c) => c.id)).size !== chapters.length) throw new Error('Duplicate chapter id');
  if (chapters.reduce((sum, c) => sum + c.durationInFrames, 0) > 24 * 3600 * 6) throw new Error('Report exceeds six hours');
  if (input.motion !== undefined && !['calm', 'reduced'].includes(input.motion)) throw new Error('Invalid motion setting');
  // «Главное в вашем разборе»: potentials and points of attention appear as the voice reads them.
  const highlights = list(input.report?.highlights ?? [], 'highlights', 4).map((group) => ({
    id: text(group?.id, 'highlight id', 40), title: text(group?.title, 'highlight title', 120),
    items: list(group?.items, 'highlight items', 12).map((item) => ({text: text(item?.text, 'highlight text', 1200), basis: text(item?.basis ?? '', 'highlight basis', 2000)}))}));
  return {version: 1, motion: input.motion ?? 'calm', title: text(input.title, 'title', 240), birthDate: text(input.birthDate, 'birth date', 40),
    asOfDate: text(input.asOfDate, 'report date', 40), fps: 24, width: 1280, height: 720, chapters, highlights};
}

export function browserProps(manifest, audioSources) {
  return {...manifest, chapters: manifest.chapters.map(({audioPath, ...chapter}, index) => {
    const audioSrc = audioSources[index];
    const url = new URL(audioSrc);
    if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1' || url.username || url.password) throw new Error('Only the private loopback audio origin is permitted');
    return {...chapter, audioSrc};
  })};
}
