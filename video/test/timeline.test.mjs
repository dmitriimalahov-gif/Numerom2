import test from 'node:test';
import assert from 'node:assert/strict';
import {buildTimeline, currentSegment, captionPages, captionAt, pageWindow, sceneModel} from '../src/timeline.mjs';

test('chapters join at exact audio boundaries with no silent filler frames', () => {
  const chapters = [2071, 325, 999].map((durationInFrames, id) => ({id, durationInFrames}));
  const result = buildTimeline(chapters);
  assert.deepEqual(result.chapters.map((c) => c.fromFrame), [0, 2071, 2396]);
  assert.equal(result.durationInFrames, 3395);
  assert.equal(result.chapters.at(-1).fromFrame + 999, result.durationInFrames);
});
test('segment switches on its first frame and holds caption through audio gaps', () => {
  const chapter = {segments: [{fromFrame: 2, durationInFrames: 5, text: 'Один'}, {fromFrame: 10, durationInFrames: 4, text: 'Два'}]};
  assert.equal(currentSegment(chapter, 1), null);
  assert.equal(currentSegment(chapter, 2).text, 'Один');
  assert.equal(currentSegment(chapter, 9).text, 'Один');
  assert.equal(currentSegment(chapter, 10).text, 'Два');
});
test('caption pagination keeps every word without truncating personal content', () => {
  const text = 'Первое предложение содержит числа 11 и 22. Второе объясняет взаимодействие и внимание к результатам. Третье даёт практический шаг.';
  const pages = captionPages(text, 48);
  assert.equal(pages.join(' '), text);
  assert.ok(pages.every((p) => p.length <= 48));
  const segment = {fromFrame: 50, durationInFrames: 240, text};
  assert.equal(captionAt(segment, 50, 48).text, pages[0]);
  assert.equal(captionAt(segment, 289, 48).text, pages.at(-1));
  assert.equal(captionAt(segment, 400, 48).text, pages.at(-1));
});
test('long individual words are preserved for CSS wrapping', () => {
  assert.deepEqual(captionPages('а'.repeat(200), 30), ['а'.repeat(200)]);
  assert.deepEqual(captionAt(null, 0), {text: '', index: 0, count: 0});
});
test('large value tables remain centered on narrated focus including final item', () => {
  assert.deepEqual(pageWindow(100, 50, 7), {start: 47, end: 54, activeIndex: 50});
  assert.deepEqual(pageWindow(100, 99, 7), {start: 93, end: 100, activeIndex: 99});
  assert.deepEqual(pageWindow(100, 0, 7), {start: 0, end: 7, activeIndex: 0});
});
test('unfocused tables advance deterministically and expose all data', () => {
  const shown = new Set();
  for (let frame = 0; frame < 300; frame++) {
    const {start, end} = pageWindow(100, null, 7, frame, 300);
    for (let index = start; index < end; index++) shown.add(index);
  }
  assert.equal(shown.size, 100);
  assert.deepEqual(pageWindow(0, null), {start: 0, end: 0, activeIndex: null});
});
test('invalid focus never highlights a different cell or invents a value', () => {
  const chapter = {durationInFrames: 20, segments: [{fromFrame: 0, durationInFrames: 20, text: 'Текст', focusIndex: 9}], section: {values: [{label: 'Ноль', value: 0}]}};
  assert.equal(sceneModel(chapter, 5).focusIndex, null);
  assert.equal(sceneModel(chapter, 5).value, null);
  chapter.segments[0].focusIndex = 0;
  assert.equal(sceneModel(chapter, 5).value.value, 0);
});
