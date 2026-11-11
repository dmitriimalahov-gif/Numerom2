import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {validateManifest, browserProps} from '../manifest.mjs';
import {canonicalViews, svgViewport} from '../src/layout.mjs';
import {sceneModel} from '../src/timeline.mjs';
import {parseArguments} from '../render.mjs';

const report = JSON.parse(fs.readFileSync(new URL('../../docs/artifacts/full-report-fixture.json', import.meta.url))).report;
const manifest = () => ({version: 1, title: 'Полный разбор', birthDate: '10.01.1982', asOfDate: '2026-10-23', fps: 24, width: 1280, height: 720,
  report, chapters: [{id: 'full-report-square', title: 'Квадрат', durationInFrames: 240, audioPath: '/tmp/private/report.m4a',
    segments: [{fromFrame: 0, durationInFrames: 240, text: 'Ваш квадрат', focusIndex: 0}], section: report.sections.find((s) => s.id === 'square')}]});

test('saved report supplies the exact canonical diagram with original matrix order', () => {
  const result = validateManifest(manifest());
  assert.deepEqual(result.chapters[0].section.diagram.cells.map((c) => c.digit), [1, 4, 7, 2, 5, 8, 3, 6, 9]);
  assert.deepEqual(result.chapters[0].section.diagram.cells.map((c) => c.count), [3, 1, 0, 5, 0, 1, 0, 0, 1]);
  assert.equal(result.report, undefined);
});
test('all saved date-only sections derive canonical schemes without recomputation', () => {
  const input = manifest();
  input.chapters = report.sections.map((section, index) => ({...input.chapters[0], id: 'chapter-' + index, section}));
  const result = validateManifest(input);
  // Date-only report: eleven schemes plus the four life periods of the author's table.
  assert.equal(result.chapters.length, 15);
  assert.ok(result.chapters.every((chapter) => chapter.section.diagram));
  const years = result.chapters.find((c) => c.section.id === 'cycles').section.diagram.years;
  assert.equal(years.length, 100);
  assert.deepEqual(years.map((y) => y.value), report.raw.cycles.years.map((y) => y.chlg));
});
test('text-only synthesis preserves null and its meaning instead of drawing zero scores', () => {
  const input = manifest();
  input.chapters[0].section = {id: 'synthesis', title: 'Ваши темы', values: [{label: 'Сильная сторона', value: null, meaning: 'Ясное намерение.'}]};
  const result = validateManifest(input);
  assert.equal(result.chapters[0].section.values[0].value, null);
  assert.equal(result.chapters[0].section.values[0].meaning, 'Ясное намерение.');
  assert.equal(result.chapters[0].section.diagram, undefined);
});
test('browser props do not contain raw snapshots, private paths or unknown URL fields', () => {
  const input = manifest();
  input.secret = 'private'; input.chapters[0].imageUrl = 'https://example.com/a';
  const sanitized = validateManifest(input);
  sanitized.chapters[0].section.diagram.imageUrl = 'https://example.com/b';
  const sanitizedAgain = validateManifest(sanitized);
  const result = browserProps(sanitizedAgain, ['http://127.0.0.1:9876/token/audio/0.m4a']);
  assert.equal(JSON.stringify(result).includes('/tmp/private'), false);
  assert.equal(JSON.stringify(result).includes('example.com'), false);
  assert.equal(result.secret, undefined);
  assert.throws(() => browserProps(sanitized, ['https://remote.test/a.m4a']), /loopback/);
});
test('remote or relative audio, oversized and overlapping segments fail before browser startup', () => {
  for (const audioPath of ['https://remote.test/a.m4a', 'relative.m4a', '/tmp/file.mp3']) {
    const input = manifest(); input.chapters[0].audioPath = audioPath;
    assert.throws(() => validateManifest(input), /absolute local m4a/);
  }
  const input = manifest(); input.chapters[0].segments.push({fromFrame: 239, durationInFrames: 2, text: 'bad'});
  assert.throws(() => validateManifest(input), /ordered|inside/);
  input.chapters[0].segments = [{fromFrame: -1, durationInFrames: 2, text: 'bad'}];
  assert.throws(() => validateManifest(input), /segment start/);
});
test('manifest rejects ambiguous chapters, invalid matrices and nonfinite numbers', () => {
  let input = manifest(); input.chapters.push({...input.chapters[0]});
  assert.throws(() => validateManifest(input), /Duplicate/);
  input = structuredClone(manifest()); input.chapters[0].section.chart.items.pop();
  assert.throws(() => validateManifest(input), /nine/);
  input = structuredClone(manifest()); input.chapters[0].section.values[0].value = NaN;
  assert.throws(() => validateManifest(input), /value/);
  input = manifest(); input.width = 1920;
  assert.throws(() => validateManifest(input), /1280/);
});
test('focus view changes only viewport, preserving canonical paths and exact numbers', () => {
  const diagram = validateManifest(manifest()).chapters[0].section.diagram;
  const views = canonicalViews(diagram, 3);
  assert.ok(views.focus.includes('data-cell="2"'));
  assert.equal(views.focus.replace(/viewBox="[^"]*"/, ''), views.full.replace(/viewBox="[^"]*"/, ''));
  assert.throws(() => svgViewport(views.full, {x: 0, y: 0, width: 0, height: 2}), /viewport/);
});
test('all eight line focuses use genuine routes with complete square retained', () => {
  const input = manifest(); input.chapters[0].section = report.sections.find((s) => s.id === 'lines');
  const chapter = validateManifest(input).chapters[0];
  for (let index = 0; index < 8; index++) {
    chapter.segments[0].focusIndex = index;
    const model = sceneModel(chapter, 0), views = canonicalViews(chapter.section.diagram, model.focusIndex);
    assert.match(views.focus, new RegExp('data-direction="' + chapter.section.diagram.directions[index].id + '" data-active="true"'));
    assert.equal((views.focus.match(/data-cell=/g) || []).length, 9);
    assert.equal(model.value.value, chapter.section.diagram.directions[index].value);
  }
});
test('each personal focus stays inside original geometry including master numbers', () => {
  const input = manifest(); input.chapters[0].section = report.sections.find((s) => s.id === 'personal');
  const diagram = validateManifest(input).chapters[0].section.diagram;
  assert.ok(diagram.entries.some((e) => e.value === 22));
  for (let index = 0; index < diagram.entries.length; index++) {
    const {bounds} = canonicalViews(diagram, index);
    assert.ok(bounds.x >= 0 && bounds.y >= 0 && bounds.x + bounds.width <= diagram.width && bounds.y + bounds.height <= diagram.height);
  }
});
test('CLI rejects missing, repeated, remote and oversized preview arguments', () => {
  assert.throws(() => parseArguments([]), /absolute/);
  assert.throws(() => parseArguments(['--input', 'https://x/a.json', '--output', '/tmp/a.mp4']), /absolute/);
  assert.throws(() => parseArguments(['--input', '/tmp/a.json', '--input', '/tmp/b.json']), /Expected/);
  assert.throws(() => parseArguments(['--input', '/tmp/a.json', '--output', '/tmp/a.mp4', '--preview-seconds', '61']), /Preview/);
  assert.equal(parseArguments(['--input', '/tmp/a.json', '--output', '/tmp/a.mp4', '--preview-seconds', '8']).previewSeconds, 8);
});
