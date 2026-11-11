const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {orderedPlanetItems, planetChartGeometry} = require('../src/lib/planetChart');

const names = ['Солнце', 'Луна', 'Марс', 'Меркурий', 'Юпитер', 'Венера', 'Сатурн'];
const items = () => names.map((name, index) => ({name, value: [0, 9, 3, 6, 0, 4, 8][index], meaning: `Серверное пояснение: ${name}`}));
const planets = () => ({formula: 'Исходная формула', calculationNumber: 7, birthWeekday: 'Воскресенье', note: '', items: items()});

test('canonical days, colors and server values are paired by planet name without mutating input', () => {
  const input = Object.freeze(items().reverse().map(Object.freeze));
  const ordered = orderedPlanetItems(input);
  assert.deepEqual(ordered.map(item => item.name), names);
  assert.deepEqual(ordered.map(item => item.weekdayShort), ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']);
  assert.deepEqual(ordered.map(item => item.color), ['#f47758', '#ffffff', '#f53f58', '#bedfd0', '#fa9418', '#f8cbd3', '#3867ad']);
  for (const item of ordered) {
    const source = input.find(entry => entry.name === item.name);
    assert.equal(item.value, source.value);
    assert.equal(item.meaning, source.meaning);
  }
  assert.equal(input[0].name, 'Сатурн');
  ordered[0].color = 'changed';
  assert.equal(orderedPlanetItems(input)[0].color, '#f47758');
});

test('zero and nine land exactly on chart boundaries and all four axis values use the same scale', () => {
  const chart = planetChartGeometry(items(), 248);
  assert.equal(chart.points[0].y, chart.bottom);
  assert.equal(chart.points[0].barHeight, 0);
  assert.equal(chart.points[1].y, chart.top);
  assert.equal(chart.points[1].barHeight, chart.bottom - chart.top);
  assert.deepEqual(chart.ticks.map(tick => tick.value), [0, 3, 6, 9]);
  assert.equal(chart.points[2].y, chart.ticks[1].y);
  assert.equal(chart.points[3].y, chart.ticks[2].y);
});

test('320px and 390px screens fit the chart inside report margins and card padding', () => {
  for (const outerWidth of [276, 346]) {
    const chart = planetChartGeometry(items(), outerWidth - 28);
    assert.equal(chart.width, outerWidth - 28);
    for (const point of chart.points) {
      assert.ok(point.x - chart.step / 2 >= 0);
      assert.ok(point.x + chart.step / 2 <= chart.width);
      assert.ok(point.y - 22 >= 0);
      assert.ok(point.y + 22 <= chart.height);
      assert.ok(point.y >= chart.top && point.y <= chart.bottom);
    }
  }
});

test('missing, duplicate, unknown and malformed values show no fabricated chart data', () => {
  const malformed = [null, undefined, [], items().slice(1), [...items(), items()[0]],
    items().map((item, i) => i === 0 ? {...item, name: 'Земля'} : item),
    items().map((item, i) => i === 0 ? {...item, name: 'Луна'} : item),
    items().map((item, i) => i === 0 ? {...item, meaning: null} : item),
    ...[-1, 10, .5, NaN, Infinity, '0', null, undefined, false].map(value => items().map((item, i) => i === 0 ? {...item, value} : item))];
  for (const input of malformed) {
    assert.equal(orderedPlanetItems(input), null);
    assert.equal(planetChartGeometry(input, 248), null);
  }
  for (const width of [0, -1, NaN, Infinity]) assert.equal(planetChartGeometry(items(), width), null);
});

// Exercise the real component and its handlers without adding a native test runtime.
function renderer(input = planets(), width = 248) {
  const React = require('react'), {renderToStaticMarkup} = require('react-dom/server'), ts = require('typescript');
  const state = ['line', 'Солнце', width, null];
  let hook = 0, buttons = [], viewLayouts = [];
  const native = tag => props => {
    if (tag === 'button') buttons.push(props);
    if (props.onLayout) viewLayouts.push(props.onLayout);
    return React.createElement(tag, {role: props.accessibilityRole, 'aria-label': props.accessibilityLabel,
      'aria-selected': props.accessibilityState?.selected, 'data-testid': props.testID}, props.children);
  };
  const svg = tag => ({children, accessibilityElementsHidden, importantForAccessibility, accessible, ...props}) => React.createElement(tag, props, children);
  const filename = path.resolve(__dirname, '../src/components/numbers/PlanetCharts.tsx');
  const module = {exports: {}};
  const dependencies = {
    react: {...React, useState: initial => {const slot = hook++; if (state[slot] === undefined) state[slot] = initial; return [state[slot], value => {state[slot] = value;}];}},
    'react/jsx-runtime': require('react/jsx-runtime'),
    'react-native': {Text: native('span'), View: native('div'), Pressable: native('button'), StyleSheet: {create: styles => styles}},
    'react-native-svg': {__esModule: true, default: svg('svg'), Circle: svg('circle'), G: svg('g'), Line: svg('line'), Polyline: svg('polyline'), Rect: svg('rect'), Text: svg('text')},
    './NumberVoice': {NumberVoice: ({digit}) => React.createElement('div', null, `Озвучка планеты ${digit}`)},
    '../../lib/planetChart': require('../src/lib/planetChart'),
  };
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(filename, 'utf8'), {compilerOptions: {module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX}}).outputText,
    {exports: module.exports, require: name => {assert.ok(name in dependencies, `Unexpected dependency: ${name}`); return dependencies[name];}});
  const render = () => {hook = 0; buttons = []; viewLayouts = []; return renderToStaticMarkup(module.exports.PlanetCharts({planets: input}));};
  return {render, get buttons() {return buttons;}, layout: width => viewLayouts[0]({nativeEvent: {layout: {width}}}), setPlanets: value => {input = value;}};
}

test('real component renders exact zero, weekday labels and seven 48px accessible alternatives', () => {
  const view = renderer();
  const html = view.render();
  assert.match(html, /<polyline /);
  for (const day of ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']) assert.ok(html.includes(`>${day}</text>`));
  assert.match(html, /Серверное пояснение: Солнце/);
  assert.match(html, /aria-label="Солнце, воскресенье: 0 из 9" aria-selected="true"/);
  const alternatives = view.buttons.filter(button => button.accessibilityRole === 'button');
  assert.equal(alternatives.length, 7);
  for (const button of alternatives) {
    const style = Object.assign({}, ...button.style({pressed: false}).filter(Boolean));
    assert.ok(style.minHeight >= 44);
  }
});

test('point and button handlers select the actual server explanation; focus remains visible', () => {
  const view = renderer(); view.render();
  view.buttons.find(button => button.testID === 'planet-point-Луна').onPress();
  assert.match(view.render(), /Серверное пояснение: Луна/);
  const mars = view.buttons.find(button => button.accessibilityLabel?.startsWith('Марс,'));
  mars.onPress(); mars.onFocus();
  assert.match(view.render(), /Серверное пояснение: Марс/);
  const focusedMars = view.buttons.find(button => button.accessibilityLabel?.startsWith('Марс,'));
  const style = Object.assign({}, ...focusedMars.style({pressed: false}).filter(Boolean));
  assert.equal(style.borderWidth, 2);
  assert.equal(style.borderColor, '#003447');
});

test('switching to bars preserves data and selection, and zero produces no fake positive bar', () => {
  const view = renderer(); view.render();
  view.buttons.find(button => button.accessibilityLabel?.startsWith('Луна,')).onPress(); view.render();
  view.buttons.find(button => button.accessibilityLabel === 'Столбцы').onPress();
  const html = view.render();
  assert.doesNotMatch(html, /<polyline /);
  assert.equal((html.match(/<rect /g) || []).length, 5);
  assert.match(html, /Серверное пояснение: Луна/);
  assert.match(html, /aria-label="Луна, понедельник: 9 из 9" aria-selected="true"/);
  const moon = view.buttons.find(button => button.testID === 'planet-point-Луна');
  assert.ok(Object.assign({}, ...moon.style).height > 44);
});

test('measured width updates the chart and malformed or missing meanings remain honest', () => {
  const view = renderer(planets(), 0);
  assert.doesNotMatch(view.render(), /<svg /);
  view.layout(318);
  assert.match(view.render(), /<svg width="318"/);
  const emptyMeaning = planets(); emptyMeaning.items[0].meaning = '';
  view.setPlanets(emptyMeaning);
  assert.match(view.render(), /Пояснение для этой планеты в результате отсутствует/);
  const incomplete = planets(); incomplete.items.pop(); view.setPlanets(incomplete);
  const html = view.render();
  assert.match(html, /График пока недоступен/);
  assert.doesNotMatch(html, /<svg |<polyline |Серверное пояснение/);
});
