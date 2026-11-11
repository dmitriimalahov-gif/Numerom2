import test from 'node:test';
import assert from 'node:assert/strict';
import schematics from '../../packages/full-report/schematics.js';
import core from '../../packages/numerology-core/name-schemes.js';
import mobile from '../../mobile/src/lib/nameSchemeVisuals.js';
import {validateManifest} from '../manifest.mjs';
import {animateCanonicalSvg, directedViews} from '../src/directing.mjs';

const scheme = core.nameSchemes({name: 'Dmitrii', surname: 'Malahov'}, '10.01.1982');
const humanKeys = ['head', 'handLeft', 'handRight', 'soul', 'mindNumber', 'destinyNumber', 'bottomDigit'];
const triangle = {id: 'profile-abracadabra', title: 'Абракадабра имени', paragraphs: [], values: scheme.rows.flatMap((row, r) => row.map((value, column) =>
  ({label: `Ряд ${r + 1}, позиция ${column + 1}`, value, row: r, column})))};
const human = {id: 'profile-human', title: 'Человечек имени', paragraphs: [], values: humanKeys.map((key) => ({key, label: key, value: scheme.human[key]}))};
const report = {raw: {profile: {name_schemes: scheme}}, sections: [triangle, human]};
const points = (svg) => new Map([...svg.matchAll(/<g data-node="([^"]+)"[^>]*>(?:<title>[^<]*<\/title>)?<circle cx="([\d.]+)" cy="([\d.]+)"/g)].map((m) => [m[1], [+m[2], +m[3]]]));

test('all 45 triangle positions retain saved row order, letters and canonical mobile geometry', () => {
  const before = JSON.stringify(report), d = schematics.sectionDiagram(report, triangle), svg = schematics.diagramSvg(d);
  assert.equal(d.kind, 'triangle'); assert.equal(d.entries.length, 45);
  assert.deepEqual(d.entries.map((e) => e.value), scheme.rows.flat());
  assert.deepEqual(d.entries.filter((e) => e.row === 0).map((e) => e.letter), scheme.firstNine);
  const actual = points(svg), original = mobile.nameSchemeVisuals(scheme).triangle;
  for (const node of original.nodes) assert.deepEqual(actual.get(node.id), [20 + node.x * 1.3, 64 + node.y * 1.3]);
  assert.equal((svg.match(/data-link-target=/g) || []).length, original.edges.length);
  assert.equal(JSON.stringify(report), before);
});

test('human values follow report order while positions and connections match the author scheme', () => {
  const d = schematics.sectionDiagram(report, human), svg = schematics.diagramSvg(d), actual = points(svg);
  assert.equal(d.kind, 'human'); assert.deepEqual(d.entries.map((e) => e.id), humanKeys);
  assert.deepEqual(d.entries.map((e) => e.value), humanKeys.map((key) => scheme.human[key]));
  const original = mobile.nameSchemeVisuals(scheme).human;
  for (const node of original.nodes) assert.deepEqual(actual.get(node.id), [50 + node.x * 1.8, 90 + node.y * 1.8]);
  assert.ok(actual.get('mindNumber')[0] < actual.get('bottomDigit')[0]);
  assert.ok(actual.get('destinyNumber')[0] > actual.get('bottomDigit')[0]);
  assert.equal((svg.match(/data-link-target=/g) || []).length, original.edges.length);
});

test('new author schemes highlight each exact entry and keep focus bounds inside the original', () => {
  for (const section of [triangle, human]) {
    const d = schematics.sectionDiagram(report, section);
    for (let index = 0; index < d.entries.length; index++) {
      const bounds = schematics.diagramFocusBounds(d, index), p = points(schematics.diagramSvg(d)).get(d.entries[index].id);
      assert.ok(bounds.x >= 0 && bounds.y >= 0 && bounds.x + bounds.width <= d.width && bounds.y + bounds.height <= d.height);
      assert.ok(p[0] >= bounds.x && p[0] <= bounds.x + bounds.width && p[1] >= bounds.y && p[1] <= bounds.y + bounds.height);
      const state = {focusIndex: index, focusAge: 10, focusEvents: [{fromFrame: 0, focusIndex: index}]};
      const views = directedViews(d, state, 30);
      for (const key of ['x', 'y', 'width', 'height']) assert.ok(Math.abs(views.bounds[key] - bounds[key]) < .001);
      const svg = schematics.diagramSvg(d, {activeIndex: index});
      const texts = (s) => [...s.matchAll(/<text\b[^>]*>([^<]*)<\/text>/g)].map((m) => m[1]);
      assert.deepEqual(texts(animateCanonicalSvg(svg, d, state, 30)), texts(svg));
    }
    assert.equal(schematics.diagramFocusBounds(d, d.entries.length), null);
  }
});

test('missing or mismatched saved rows never get silently recalculated', () => {
  const altered = structuredClone(report); altered.raw.profile.name_schemes.rows[3][0] = 9;
  if (triangle.values.find((v) => v.row === 3 && v.column === 0).value === 9) altered.raw.profile.name_schemes.rows[3][0] = 8;
  assert.equal(schematics.sectionDiagram(altered, triangle), null);
  delete altered.raw.profile.name_schemes.human;
  assert.equal(schematics.sectionDiagram(altered, human), null);
  const d = schematics.sectionDiagram(report, triangle); d.entries[0].letter = '<script>';
  assert.throws(() => schematics.diagramSvg(d));
  const h = schematics.sectionDiagram(report, human); h.entries[0].value = 0;
  assert.throws(() => schematics.diagramSvg(h));
});

test('video manifest preserves semantic rows and letters but no caller-supplied markup', () => {
  const input = {version: 1, title: 'Отчёт', birthDate: '10.01.1982', asOfDate: '2026-10-23', fps: 24, width: 1280, height: 720, report,
    chapters: [triangle, human].map((section) => ({id: section.id, title: section.title, audioPath: '/tmp/test.m4a', durationInFrames: 240,
      segments: [{fromFrame: 0, durationInFrames: 240, text: 'Позиция схемы.', focusIndex: 0}], section}))};
  const prepared = validateManifest(input);
  assert.deepEqual(prepared.chapters.map((c) => c.section.diagram.kind), ['triangle', 'human']);
  assert.equal(prepared.chapters[0].section.diagram.entries[0].letter, scheme.firstNine[0]);
  assert.equal(prepared.chapters[0].section.diagram.entries[9].row, 1);
  input.chapters[0].section = {...triangle, diagram: {...prepared.chapters[0].section.diagram, arbitrarySvg: '<svg/>'}};
  assert.equal(validateManifest(input).chapters[0].section.diagram.arbitrarySvg, undefined);
});
