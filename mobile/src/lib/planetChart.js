const PLANETS = Object.freeze([
  {name: 'Солнце', weekday: 'Воскресенье', weekdayShort: 'Вс', color: '#f47758', border: '#f47758'},
  {name: 'Луна', weekday: 'Понедельник', weekdayShort: 'Пн', color: '#ffffff', border: '#bfdfd1'},
  {name: 'Марс', weekday: 'Вторник', weekdayShort: 'Вт', color: '#f53f58', border: '#f53f58'},
  {name: 'Меркурий', weekday: 'Среда', weekdayShort: 'Ср', color: '#bedfd0', border: '#9cbdaf'},
  {name: 'Юпитер', weekday: 'Четверг', weekdayShort: 'Чт', color: '#fa9418', border: '#fa9418'},
  {name: 'Венера', weekday: 'Пятница', weekdayShort: 'Пт', color: '#f8cbd3', border: '#dca8b2'},
  {name: 'Сатурн', weekday: 'Суббота', weekdayShort: 'Сб', color: '#3867ad', border: '#3867ad'},
].map(Object.freeze));

// Presentation only: keep the server's values and meanings; never calculate a forecast.
function orderedPlanetItems(items) {
  if (!Array.isArray(items) || items.length !== PLANETS.length) return null;
  const byName = new Map();
  for (const item of items) {
    if (!item || typeof item !== 'object' || byName.has(item.name)
      || !PLANETS.some(planet => planet.name === item.name)
      || !Number.isSafeInteger(item.value) || item.value < 0 || item.value > 9
      || typeof item.meaning !== 'string') return null;
    byName.set(item.name, item);
  }
  return PLANETS.map(planet => ({...planet, value: byName.get(planet.name).value, meaning: byName.get(planet.name).meaning}));
}

function planetChartGeometry(items, width, height = 228) {
  const ordered = orderedPlanetItems(items);
  if (!ordered || !Number.isFinite(width) || width < 100 || !Number.isFinite(height) || height < 100) return null;
  const left = 28, right = width - 14, top = 28, bottom = height - 42;
  const step = (right - left) / ordered.length;
  const y = value => bottom - value / 9 * (bottom - top);
  return {
    width, height, left, right, top, bottom, step,
    ticks: [0, 3, 6, 9].map(value => ({value, y: y(value)})),
    points: ordered.map((item, index) => ({...item, x: left + step * (index + .5), y: y(item.value), barHeight: bottom - y(item.value)})),
  };
}

module.exports = {orderedPlanetItems, planetChartGeometry};
