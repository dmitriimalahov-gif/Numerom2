const catalog = require('../../../packages/reflection-knowledge/ru.json');
const comparisons = require('../../../packages/reflection-knowledge/comparisons.json');

const validDigit = value => Number.isInteger(value) && value >= 1 && value <= 9;
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

// This layer describes symbols. It accepts no identity or employment data.
function numberReflection(digit) {
  if (!validDigit(digit)) return null;
  const item = catalog.items.find(entry => entry.digit === digit);
  if (!item) return null;
  const sources = item.sourceIds.map(id => catalog.sources.find(source => source.id === id)).filter(Boolean);
  return {...item, sources};
}

function comparisonReflection(first, second) {
  const a = numberReflection(first), b = numberReflection(second);
  if (!a || !b) return null;
  const repeated = first === second;
  const pair = comparisons.items.find(item => item.first === Math.min(first,second) && item.second === Math.max(first,second));
  if (!repeated && !pair) return null;
  return {
    first, second,
    title: repeated ? `Одна тема в разных ситуациях · ${first}` : `${first} и ${second} · две темы для размышления`,
    intro: repeated
      ? 'Повторение символа предлагает посмотреть на одну тему с двух сторон. Возьмите две конкретные ситуации из своего опыта.'
      : 'Рассмотрите, как эти две темы встречаются в одном вашем опыте. Вопросы ниже подготовлены редакцией по мотивам материалов NumerOM.',
    themes: (repeated ? [a] : [a,b]).map(item => ({digit:item.digit,planet:item.planet,theme:item.theme})),
    questions: repeated
      ? [a.comparisonFocus, 'Что в этих ситуациях было похоже, а что потребовало другого подхода?']
      : [pair.question, a.comparisonFocus, b.comparisonFocus],
    practice: repeated
      ? 'Запишите два примера: когда эта тема помогла вам и когда её оказалось слишком много или недостаточно. Отметьте одно действие, которое вы хотели бы попробовать иначе.'
      : pair.practice,
    sourceNote: 'Сопоставление относится к символическим темам. Источники каждой темы приведены в её разделе «Для размышления».',
  };
}

function reflectionHtml(digit) {
  const entry = numberReflection(digit);
  if (!entry) return '';
  const paragraphs = entry.reflection.map(text => `<p>${esc(text)}</p>`).join('');
  return `<section class="reflection" data-reflection-digit="${digit}"><h4>Для размышления · ${esc(entry.planet)}</h4><p>${esc(entry.sourceSummary)}</p>${paragraphs}<h4>Вопросы к своему опыту</h4><ul>${entry.questions.map(text => `<li>${esc(text)}</li>`).join('')}</ul><h4>Небольшая практика</h4><p>${esc(entry.practice)}</p><p class="source">Пересказ материала и вопросы редакции NumerOM. ${entry.sources.map(source => `${esc(source.title)} — ${esc(source.locator)}`).join('; ')}.</p></section>`;
}

module.exports = {numberReflection, comparisonReflection, reflectionHtml};
