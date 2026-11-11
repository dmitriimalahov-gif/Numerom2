import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {appearances, formulaFor, extraNumbers, highlightCues, spokenWords, sharedSteps} from '../src/motion.mjs';

const report = JSON.parse(fs.readFileSync(new URL('../../docs/artifacts/full-report-fixture.json', import.meta.url))).report;
const section = (id) => report.sections.find((s) => s.id === id);
test('contextual consultation keeps saved math but does not repeat it in video overlays', () => {
 const source=section('personal'), narrated={...source,position_readings:[{value_index:0,insight:'Тема личного намерения'}]};
 assert.equal(formulaFor(narrated,0),'');assert.deepEqual(sharedSteps(narrated),[]);
 assert.ok(source.steps.length);assert.equal(formulaFor(source,0),'1 + 0 = 1');
});

test('a value enters when the voice names it; unnamed values enter one after another after the title', () => {
  const chapter = {durationInFrames: 2000, section: section('personal'), segments: [
    {fromFrame: 0, durationInFrames: 900, text: 'Вступление'},
    {fromFrame: 900, durationInFrames: 600, text: 'Число судьбы', focusCues: [{fromFrame: 950, durationInFrames: 100, focusIndex: 2}]},
    {fromFrame: 1500, durationInFrames: 500, text: 'Число души', focusIndex: 0}]};
  const enter = appearances(chapter, 4);
  assert.deepEqual(enter.map((e) => e.spoken), [true, false, true, false]);
  assert.equal(enter[2].frame, 950);
  assert.equal(enter[0].frame, 1500);
  assert.deepEqual([enter[1].frame, enter[3].frame], [26, 32]);
});

test('formulas are the saved arithmetic of each value, never a neighbour\'s and never recalculated', () => {
  assert.equal(formulaFor(section('personal'), 0), '1 + 0 = 1');
  assert.equal(formulaFor(section('personal'), 1), 'Месяц рождения: 1 → 1');
  assert.equal(formulaFor(section('personal'), 2), '10 + 1 + 1982 = 1993 · 1 + 9 + 9 + 3 = 22 · 2 + 2 = 4');
  assert.equal(formulaFor(section('tasks'), 0), '|1 − 1| = 0 → 0');
  assert.equal(formulaFor(section('lines'), 0), '3 + 1 + 0 = 4');
  assert.equal(formulaFor(section('cycle-period-1'), 0), 'вершина 2 + день 1 → 3');
  assert.equal(formulaFor(section('fractal'), 2), '1982 → 2');
  // «Солнце: 1; Луна: 9; …» lists every planet: Sun must not borrow the Moon's line.
  assert.deepEqual(section('planets').values.map((_, i) => formulaFor(section('planets'), i)), Array(7).fill(''));
  assert.equal(formulaFor(section('square'), 0), '');
  assert.deepEqual(extraNumbers(section('square')).map((e) => e.label + '=' + e.value), ['А1=22', 'А2=4', 'А3=20', 'А4=2']);
  assert.deepEqual(extraNumbers(section('vedic-yantra')), []);
});

test('potentials and points of attention follow the recognised speech, also inside a longer phrase', () => {
  const highlights = [
    {id: 'potentials', title: 'Ваши потенциалы', items: [{text: 'Сила собственного голоса помогает.', basis: ''}, {text: 'Масштабный замысел становится реальностью.', basis: ''}]},
    {id: 'attention', title: 'На что обратить внимание', items: [{text: 'В потоке ярких идей сохранять ясность.', basis: ''}]}];
  const chapter = {durationInFrames: 1000, segments: [
    {fromFrame: 0, durationInFrames: 200, text: 'Полный разбор. Обзор.'},
    {fromFrame: 200, durationInFrames: 200, text: 'Ваши потенциалы. Сила собственного голоса помогает.'},
    {fromFrame: 400, durationInFrames: 200, text: 'Масштабный замысел становится реальностью.'},
    {fromFrame: 600, durationInFrames: 100, text: 'На что обратить внимание?'},
    {fromFrame: 700, durationInFrames: 300, text: 'Потоки ярких идей сохранять ясность.'}]};
  const [potentials, attention] = highlightCues(chapter, highlights);
  assert.equal(potentials.fromFrame, 200);
  assert.ok(potentials.items[0].fromFrame > 200 && potentials.items[0].fromFrame < 400);
  assert.equal(potentials.items[1].fromFrame, 400);
  assert.equal(attention.fromFrame, 600);
  assert.equal(attention.items[0].fromFrame, 700);
  // Missing speech never runs backwards: the item waits for its group.
  const silent = highlightCues({durationInFrames: 100, segments: [{fromFrame: 0, durationInFrames: 100, text: 'Другое'}]}, highlights);
  assert.ok(silent.every((g) => g.items.every((i) => i.fromFrame >= g.fromFrame)));
});

test('spoken words grow with the caption and never exceed it', () => {
  const caption = {text: 'один два три четыре', fromFrame: 100, durationInFrames: 40};
  assert.deepEqual([90, 100, 111, 139, 200].map((f) => spokenWords(caption, f)), [0, 0, 2, 4, 4]);
  assert.equal(spokenWords({text: '', fromFrame: 0, durationInFrames: 0}, 10), 0);
});
