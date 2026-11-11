import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import schematics from '../../packages/full-report/schematics.js';
import {cameraAt, animateCanonicalSvg, directedViews, entrance} from '../src/directing.mjs';
import {focusTimeline, sceneModel} from '../src/timeline.mjs';
import {validateManifest} from '../manifest.mjs';

const report = JSON.parse(fs.readFileSync(new URL('../../docs/artifacts/full-report-fixture.json', import.meta.url))).report;
const section = (id) => report.sections.find((s) => s.id === id);
const diagram = (id) => schematics.sectionDiagram(report, section(id));
const chapter = () => ({durationInFrames: 240, section: {...section('personal'), diagram: diagram('personal')}, segments: [
  {fromFrame: 0, durationInFrames: 180, text: 'Число души — один; число ума — один; число судьбы — четыре.', focusIndex: 2,
    focusCues: [{fromFrame: 12, durationInFrames: 48, focusIndex: 0}, {fromFrame: 60, durationInFrames: 60, focusIndex: 1}, {fromFrame: 120, durationInFrames: 60, focusIndex: 2}]},
  {fromFrame: 180, durationInFrames: 60, text: 'Общий взгляд на схему.'},
]});

test('a single caption directs several actual numbers at their supplied boundaries', () => {
  const c = chapter();
  assert.deepEqual([0, 11, 12, 59, 60, 119, 120, 179, 180].map((frame) => sceneModel(c, frame).focusIndex), [null, null, 0, 0, 1, 1, 2, 2, null]);
  assert.deepEqual([12, 60, 120].map((frame) => sceneModel(c, frame).value.value), [1, 1, 4]);
  assert.deepEqual(focusTimeline(c).map((e) => e.fromFrame), [0, 12, 60, 120, 180]);
});
test('legacy focus, explicit gaps and chart-only manifests remain usable', () => {
  const c = {durationInFrames: 50, section: {chart: {items: [{label: 'Ноль', value: 0}]}}, segments: [{fromFrame: 0, durationInFrames: 30, text: 'Ноль', focusIndex: 0}]};
  assert.equal(sceneModel(c, 40).focusIndex, 0);
  c.segments[0].focusCues = [{fromFrame: 5, durationInFrames: 5, focusIndex: 0}, {fromFrame: 20, durationInFrames: 10, focusIndex: 0}];
  assert.deepEqual([0, 5, 10, 19, 20].map((f) => sceneModel(c, f).focusIndex), [null, 0, null, null, 0]);
});
test('camera smoothly reaches exact canonical bounds and returns to overview', () => {
  const c = chapter(), d = c.section.diagram, events = focusTimeline(c);
  assert.deepEqual(cameraAt(d, events, 12), cameraAt(d, events, 11));
  assert.deepEqual(cameraAt(d, events, 30), schematics.diagramFocusBounds(d, 0));
  assert.deepEqual(cameraAt(d, events, 138), schematics.diagramFocusBounds(d, 2));
  assert.deepEqual(cameraAt(d, events, 198), {x: 0, y: 86, width: 640, height: 425});
  const between = cameraAt(d, events, 20);
  assert.ok(between.height > 124 && between.height < 425);
});
test('interrupted camera moves remain continuous and bounded', () => {
  const d = diagram('square'), events = [{fromFrame: 0, focusIndex: null}, {fromFrame: 10, focusIndex: 0}, {fromFrame: 14, focusIndex: 8}];
  const before = cameraAt(d, events, 13);
  assert.deepEqual(cameraAt(d, events, 14), before);
  for (let f = 0; f < 60; f++) {
    const b = cameraAt(d, events, f);
    assert.ok(b.x >= 0 && b.y >= 0 && b.x + b.width <= d.width + .001 && b.y + b.height <= d.height + .001);
  }
});
test('rapid enumeration highlights fields while retaining a stable overview', () => {
  const d = diagram('personal'), events = [{fromFrame: 0, focusIndex: null},
    {fromFrame: 12, focusIndex: 0}, {fromFrame: 30, focusIndex: 1}, {fromFrame: 45, focusIndex: 2}];
  for (const frame of [12, 25, 30, 40, 45]) assert.deepEqual(cameraAt(d, events, frame), {x: 0, y: 86, width: 640, height: 425});
  assert.deepEqual(cameraAt(d, events, 63), schematics.diagramFocusBounds(d, 2));
});
test('animated SVG preserves every canonical text, digit and route across frames', () => {
  const text = (svg) => [...svg.matchAll(/<text\b[^>]*>([^<]*)<\/text>/g)].map((m) => m[1]);
  for (const s of report.sections) {
    const d = schematics.sectionDiagram(report, s), original = schematics.diagramSvg(d, {activeIndex: 0});
    for (const f of [0, 5, 12, 50]) {
      const model = {focusIndex: 0, focusAge: f, focusEvents: [{fromFrame: 0, focusIndex: 0}]};
      const animated = animateCanonicalSvg(original, d, model, f);
      assert.deepEqual(text(animated), text(original), s.id);
      assert.equal((animated.match(/data-cell=/g) || []).length, (original.match(/data-cell=/g) || []).length);
      assert.equal((animated.match(/data-direction=/g) || []).length, (original.match(/data-direction=/g) || []).length);
    }
  }
});
test('digits drop in, active lines trace once, and the final SVG stays deterministic', () => {
  assert.equal(entrance(0).opacity, 0);
  assert.ok(entrance(8).y < 0);
  assert.deepEqual(entrance(18), {opacity: 1, y: 0, scale: 1});
  const d = diagram('lines'), original = schematics.diagramSvg(d, {activeIndex: 6});
  const state = {focusIndex: 6, focusAge: 5};
  const animated = animateCanonicalSvg(original, d, state, 50);
  assert.match(animated, /data-direction="diag-0" data-active="true"[^>]*><line pathLength="1"/);
  assert.equal(animated, animateCanonicalSvg(original, d, state, 50));
});
test('reduced motion removes reveal/pulse and jumps directly to the useful framing', () => {
  const d = diagram('personal'), model = sceneModel(chapter(), 12);
  const original = schematics.diagramSvg(d, {activeIndex: 0});
  assert.equal(animateCanonicalSvg(original, d, model, 12, true), original);
  assert.deepEqual(cameraAt(d, model.focusEvents, 12, true), schematics.diagramFocusBounds(d, 0));
  assert.deepEqual(entrance(0, 12, 18, true), {opacity: 1, y: 0, scale: 1});
});
test('sequence and 100-year camera use actual canonical coordinates', () => {
  for (const id of ['fractal', 'individual', 'cycles']) {
    const d = diagram(id), index = id === 'cycles' ? 99 : 0;
    const b = cameraAt(d, [{fromFrame: 0, focusIndex: index}], 30);
    assert.ok(b.width < d.width && b.height < d.height);
    assert.ok(b.x >= 0 && b.x + b.width <= d.width && b.y + b.height <= d.height);
  }
});
test('focus timing survives sanitization and cannot escape its narration segment', () => {
  const input = {version: 1, title: 'Разбор', birthDate: '01.01.2000', asOfDate: '2026-10-23', fps: 24, width: 1280, height: 720,
    motion: 'reduced', chapters: [{...chapter(), id: 'full-report-personal', title: 'Числа', audioPath: '/tmp/verified.m4a'}]};
  const result = validateManifest(input);
  assert.deepEqual(result.chapters[0].segments[0].focusCues, input.chapters[0].segments[0].focusCues);
  assert.equal(result.motion, 'reduced');
  input.chapters[0].segments[0].focusCues[0].durationInFrames = 200;
  assert.throws(() => validateManifest(input), /Focus cues|focus duration/);
  input.motion = 'random'; assert.throws(() => validateManifest(input));
});
