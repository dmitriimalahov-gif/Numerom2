// Shared geometry only: arithmetic stays in packages/numerology-core/name-schemes.js.
const isDigit = value => Number.isInteger(value) && value >= 1 && value <= 9;
const validLetters = letters => Array.isArray(letters) && letters.every(item =>
  item && /^[A-Z]$/.test(item.letter) && isDigit(item.digit));

function series(kind, title, values, note) {
  const width = 448, height = 172, baseline = 132;
  const maximum = kind === 'sequence' ? 9 : Math.max(1, ...values.map(item => item.value));
  const y = value => baseline - value / maximum * 96;
  return {kind, title, width, height, baseline, note,
    points: values.map((item, index) => ({...item, x:32 + index * 48, y:y(item.value)})),
    ticks:[...new Set([0, Math.ceil(maximum / 2), maximum])].map(value => ({value, y:y(value)}))};
}

function triangleVisual(data) {
  const {rows, firstNine} = data;
  if (!Array.isArray(rows) || rows.length !== 9 || !Array.isArray(firstNine) ||
      firstNine.length !== 9 || firstNine.some(letter => !/^[A-Z]$/.test(letter)) ||
      rows.some((row, index) => !Array.isArray(row) || row.length !== 9-index || !row.every(isDigit))) return null;
  const nodes = [], edges = [];
  rows.forEach((row, r) => row.forEach((value, column) => {
    const id = `triangle-${r}-${column}`;
    const a = rows[r-1]?.[column], b = rows[r-1]?.[column+1];
    const formula = r === 0 ? `${firstNine[column]} → ${value}` :
      `${a} + ${b} = ${a+b}${a+b > 9 ? ` → ${value}` : ''}`;
    nodes.push({id, x:32+(r+column)*48, y:64+r*46, radius:18, value, row:r, column,
      letter:r === 0 ? firstNine[column] : undefined,
      title:`Абракадабра · ряд ${r+1}, позиция ${column+1}`,
      formula, meaning:r === 0 ? 'Буква исходного имени и фамилии.' :
        'Результат сложения двух соседних ячеек предыдущего ряда со сведением к одной цифре.'});
    if (r > 0) edges.push({from:`triangle-${r-1}-${column}`, to:id},
      {from:`triangle-${r-1}-${column+1}`, to:id});
  }));
  return {kind:'triangle', width:448, height:460, nodes, edges,
    letters:firstNine.map((text, index) => ({id:`letter-${index}`, text, x:32+index*48, y:26})),
    series:series('sequence', 'Исходный числовой ряд', firstNine.map((letter, i) =>
      ({id:`triangle-0-${i}`, label:letter, value:rows[0][i]})),
    'Первые девять букв имени и фамилии слева направо. Линия соединяет их числовые значения; это не шкала времени.')};
}

function humanVisual(data) {
  const h = data.human, letters = data.nameLetters;
  if (!h || !validLetters(letters) || letters.length < 4 ||
      ['head','handLeft','handRight','soul','mindNumber','destinyNumber','bottomDigit'].some(key => !isDigit(h[key]))) return null;
  const positions = [
    ['head',150,42,'Голова',['Голова'],`1-я буква: ${letters[0].letter} → ${h.head}`,'Мысли, способ осмысления и отношение к значимым людям.'],
    ['handLeft',50,146,'Левая рука',['Левая рука'],`3-я буква: ${letters[2].letter} → ${h.handLeft}`,'Выражение чувств и общение.'],
    ['soul',150,146,'Центр',['Центр'],`4-я буква: ${letters[3].letter} → ${h.soul}`,'Внутреннее состояние и ощущение своего места.'],
    ['handRight',250,146,'Правая рука',['Правая рука'],`2-я буква: ${letters[1].letter} → ${h.handRight}`,'Реакция на напряжение и неудовлетворённость.'],
    ['mindNumber',50,260,'Число ума',['Число ума'],'Сокращённый месяц рождения','Привычный способ мыслить и выбирать действия.'],
    ['bottomDigit',150,260,'Точка опоры',['Точка','опоры'],`Последняя буква: ${letters.at(-1).letter} → ${h.bottomDigit}`,'Привычный способ действовать и проявлять намерение.'],
    ['destinyNumber',250,260,'Число судьбы',['Число','судьбы'],'Сокращённая сумма дня, месяца и года рождения','Общая тема пути и опоры на опыт.'],
  ];
  return {kind:'human', width:300, height:332,
    nodes:positions.map(([id,x,y,title,labelLines,formula,meaning]) =>
      ({id,x,y,radius:24,value:h[id],title,labelLines,labelY:y+43,formula,meaning})),
    edges:[['head','soul'],['handLeft','soul'],['soul','handRight'],
      ['soul','mindNumber'],['soul','bottomDigit'],['soul','destinyNumber']].map(([from,to]) => ({from,to})),
    letters:[],
    series:series('distribution', 'Цифры в буквах имени', Array.from({length:9}, (_,i) =>
      ({id:`digit-${i+1}`, label:String(i+1), value:letters.filter(item => item.digit === i+1).length})),
    'Высота столбца — количество букв имени с этой цифрой. Фамилия и числа даты рождения в распределение не входят.')};
}

function nameSchemeVisuals(data) {
  if (!data?.available) return {triangle:null, human:null};
  return {triangle:triangleVisual(data), human:humanVisual(data)};
}

module.exports = {nameSchemeVisuals};
