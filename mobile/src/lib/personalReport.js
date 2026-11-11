const {validateBirthDate} = require('@numerom/api-client');
const {personalScheme} = require('./personalScheme');

const definitions = [
  ['soul', 'soul_number', 'Число души', 'Душа'],
  ['mind', 'mind_number', 'Число ума', 'Ум'],
  ['destiny', 'destiny_number', 'Число судьбы', 'Судьба'],
  ['helping_mind', 'helping_mind_number', 'Помогающее число ума', 'Помощь уму'],
  ['wisdom', 'wisdom_number', 'Число мудрости', 'Мудрость'],
  ['ruling', 'ruling_number', 'Правящее число', 'Правящее'],
  ['full_name', 'full_name_number', 'Число имени', 'Имя'],
];
const object = value => value && typeof value === 'object' && !Array.isArray(value);
const number = value => Number.isSafeInteger(value) && value >= 0;
const text = value => typeof value === 'string' ? value.trim() : '';
const nullableText = value => value === null || typeof value === 'string';

// This is a presentation boundary, never a second numerology calculator.
function personalReport(value, birthDate) {
  if (!object(value)) throw new Error('Сервер не вернул результат расчёта. Проверьте сохранённый результат.');
  const report = object(value.report) && value.report.version === 1 && validateBirthDate(value.report.birth_date)
    && (!birthDate || value.report.birth_date === birthDate) ? value.report : null;
  const entries = report && Array.isArray(report.numbers) ? report.numbers : [];
  let detailedCount = 0;
  const numbers = definitions.map(([key, field, title, shortTitle]) => {
    const matches = entries.filter(entry => object(entry) && entry.key === field);
    const entry = matches.length === 1 ? matches[0] : null;
    const complete = entry && (number(entry.value) || entry.value === null) && text(entry.title)
      && text(entry.meaning) && typeof entry.method === 'string' && nullableText(entry.interpretation)
      && nullableText(entry.note) && Array.isArray(entry.steps) && entry.steps.every(step => typeof step === 'string')
      && (value[field] === undefined || value[field] === entry.value);
    if (complete) detailedCount++;
    return {
      key, shortTitle, title: complete ? text(entry.title) : title,
      value: complete ? entry.value : number(value[field]) ? value[field] : null,
      meaning: complete ? text(entry.meaning) : '',
      interpretation: complete ? text(entry.interpretation) : '',
      method: complete ? text(entry.method) : '',
      steps: complete ? entry.steps.map(text).filter(Boolean) : [],
      note: complete ? text(entry.note) : '', detailed: !!complete,
    };
  });
  if (!numbers.some(entry => entry.value !== null) && !detailedCount) {
    throw new Error('В ответе нет доступных значений. Проверьте сохранённый результат перед повторным запуском.');
  }
  const source = report?.planets;
  const validPlanets = object(source) && typeof source.formula === 'string'
    && (number(source.calculation_number) || source.calculation_number === null)
    && typeof source.birth_weekday === 'string' && typeof source.note === 'string'
    && Array.isArray(source.items) && (source.items.length === 7 || source.items.length === 0)
    && source.items.every(item => object(item) && text(item.name) && number(item.value) && item.value <= 9 && typeof item.meaning === 'string')
    && new Set(source.items.map(item => item.name)).size === source.items.length;
  return {
    birthDate: report?.birth_date || birthDate || '',
    birthWeekday: text(report?.birth_weekday) || text(value.birth_weekday),
    profileName: text(report?.profile_name), profileParts: object(report?.profile_parts) && typeof report.profile_parts.name==='string' && typeof report.profile_parts.surname==='string' ? {name:report.profile_parts.name,surname:report.profile_parts.surname} : null, numbers,
    scheme: personalScheme(report?.scheme, report?.birth_date || birthDate || ''),
    planets: validPlanets ? {
      formula: text(source.formula), calculationNumber: source.calculation_number,
      birthWeekday: text(source.birth_weekday), note: text(source.note),
      items: source.items.map(item => ({name: text(item.name), value: item.value, meaning: text(item.meaning)})),
    } : null,
    incomplete: detailedCount !== definitions.length || !validPlanets,
  };
}

function savedPersonalResult(response) {
  if (!object(response) || !Object.hasOwn(response, 'calculation')) throw new Error('Не удалось прочитать сохранённый результат. Попробуйте загрузить его ещё раз.');
  const saved = response.calculation;
  if (saved === null) return null;
  if (!object(saved) || !text(saved.id) || !validateBirthDate(saved.birth_date) || typeof saved.created_at !== 'string') {
    throw new Error('Сохранённый результат получен не полностью. Попробуйте загрузить его ещё раз.');
  }
  return {report: personalReport(saved.results, saved.birth_date), createdAt: saved.created_at, source: 'saved', id: saved.id};
}

function calculationPrice(response) {
  const price = response?.personal_numbers;
  if (!Number.isSafeInteger(price) || price < 0) {
    throw new Error('Стоимость расчёта не получена. Загрузите её перед запуском.');
  }
  return price;
}

function calculationBlock({date, price, balance, balanceError = '', busy = false}) {
  if (busy) return 'Дождитесь завершения текущего запроса.';
  if (!Number.isSafeInteger(price) || price < 0) return 'Сначала загрузите стоимость расчёта.';
  if (balanceError || typeof balance !== 'number' || !Number.isFinite(balance)) return 'Обновите баланс перед новым расчётом.';
  if (balance < price) return 'Недостаточно баллов для нового расчёта.';
  if (!validateBirthDate(date)) return 'Укажите существующую дату: ДД.ММ.ГГГГ';
  return '';
}

function createPersonalCalculationController({latest, calculate, refreshBalance, isCurrent = () => true}) {
  let state = {result: null, latestLoading: true, latestError: '', latestLoaded: false,
    busy: false, calculationError: '', balanceLoading: false, balanceError: ''};
  const listeners = new Set();
  let started = false, latestPending = null, calculationPending = null, balancePending = null, version = 0;
  const publish = update => {
    if (!isCurrent()) return;
    state = {...state, ...update};
    listeners.forEach(listener => listener());
  };
  const errorText = (error, fallback) => error instanceof Error ? error.message : fallback;
  function loadLatest() {
    if (!isCurrent()) return Promise.resolve();
    if (latestPending) return latestPending;
    const requestedVersion = version;
    publish({latestLoading: true, latestError: ''});
    latestPending = Promise.resolve().then(() => isCurrent() ? latest() : undefined).then(response => {
      if (!isCurrent() || requestedVersion !== version) return;
      const result = savedPersonalResult(response);
      publish({latestLoaded: true, ...(result || !state.result ? {result} : {})});
    }).catch(error => {
      if (requestedVersion === version) publish({latestError: errorText(error, 'Не удалось загрузить сохранённый результат.')});
    }).finally(() => { latestPending = null; publish({latestLoading: false}); });
    return latestPending;
  }
  function reloadBalance() {
    if (!isCurrent()) return Promise.resolve();
    if (balancePending) return balancePending;
    publish({balanceLoading: true, balanceError: ''});
    balancePending = Promise.resolve().then(() => isCurrent() ? refreshBalance() : undefined).catch(error => {
      publish({balanceError: errorText(error, 'Не удалось обновить баланс.')});
    }).finally(() => { balancePending = null; publish({balanceLoading: false}); });
    return balancePending;
  }
  function runCalculation(date, price, balance) {
    if (!isCurrent()) return Promise.resolve();
    if (calculationPending) return calculationPending;
    const blocked = calculationBlock({date, price, balance, balanceError: state.balanceError, busy: state.balanceLoading});
    if (blocked) { publish({calculationError: blocked}); return Promise.resolve(); }
    publish({busy: true, calculationError: ''});
    calculationPending = Promise.resolve().then(() => isCurrent() ? calculate(date) : undefined).then(value => {
      if (!isCurrent()) return;
      const report = personalReport(value, date);
      version++;
      publish({result: {report, source: 'new', createdAt: '', id: ''}, latestError: ''});
    }).catch(error => {
      publish({calculationError: `${errorText(error, 'Не удалось подтвердить новый расчёт.')} Проверьте сохранённый результат перед повторным запуском. Проверка бесплатна, новый запуск оплачивается отдельно.`});
    }).finally(async () => {
      if (isCurrent()) await reloadBalance();
      calculationPending = null;
      publish({busy: false});
    });
    return calculationPending;
  }
  return {
    getSnapshot: () => state,
    subscribe: listener => { listeners.add(listener); return () => listeners.delete(listener); },
    start: () => { if (!started) { started = true; return loadLatest(); } return latestPending || Promise.resolve(); },
    reloadLatest: loadLatest, refreshBalance: reloadBalance, calculate: runCalculation,
  };
}

module.exports = {personalReport, savedPersonalResult, calculationPrice, calculationBlock, createPersonalCalculationController};
