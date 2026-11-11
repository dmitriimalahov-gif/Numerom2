import React, { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';
import { Loader2, Moon, Sun } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend
} from 'chart.js';
import { getBackendUrl, getApiBaseUrl } from '../utils/backendUrl';
import NarrationPanel from '../features/learning/NarrationPanel';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

const pillGradient = 'bg-[#203653]';
const valueGradient = 'bg-[#385da5]';

// Match the supplied NumerOM square while keeping live values as text.
const CELL_COLORS = {
  1: { background: '#f47758', text: '#203653', border: '#f47758' },
  2: { background: '#ffffff', text: '#203653', border: '#bfdfd1' },
  3: { background: '#fa9418', text: '#203653', border: '#fa9418' },
  4: { background: '#ba9669', text: '#172c43', border: '#ba9669' },
  5: { background: '#bedfd0', text: '#203653', border: '#aed3c3' },
  6: { background: '#f8cbd3', text: '#203653', border: '#f8cbd3' },
  7: { background: '#bcbfc0', text: '#203653', border: '#bcbfc0' },
  8: { background: '#3867ad', text: '#ffffff', border: '#3867ad' },
  9: { background: '#f53f58', text: '#17283b', border: '#f53f58' }
};

const DOW_NUMBERS = [1, 2, 9, 5, 3, 6, 8]; // Sunday -> 1, Monday -> 2, ...

const digitalRoot = (value) => {
  if (value === null || value === undefined) return 0;
  let n = Math.abs(Math.trunc(value));
  while (n > 9) {
    n = n
      .toString()
      .split('')
      .reduce((sum, digit) => sum + Number(digit), 0);
  }
  return n;
};

const adjacencyScore = (a, b) => {
  if (!a || !b) return 0;
  const normA = ((a - 1 + 9) % 9) + 1;
  const normB = ((b - 1 + 9) % 9) + 1;
  const diff = Math.abs(normA - normB);
  return diff === 1 || diff === 8 ? 1 : 0;
};

const adjustColor = (hex, amount = 0.2) => {
  if (!hex) return hex;
  let normalized = hex.replace('#', '');
  if (normalized.length === 3) {
    normalized = normalized
      .split('')
      .map((c) => c + c)
      .join('');
  }
  if (normalized.length !== 6) return hex;
  const num = parseInt(normalized, 16);
  let r = (num >> 16) & 0xff;
  let g = (num >> 8) & 0xff;
  let b = num & 0xff;
  if (amount >= 0) {
    r = Math.round(r + (255 - r) * amount);
    g = Math.round(g + (255 - g) * amount);
    b = Math.round(b + (255 - b) * amount);
  } else {
    const factor = 1 + amount;
    r = Math.round(r * factor);
    g = Math.round(g * factor);
    b = Math.round(b * factor);
  }
  r = Math.min(255, Math.max(0, r));
  g = Math.min(255, Math.max(0, g));
  b = Math.min(255, Math.max(0, b));
  return `#${[r, g, b]
    .map((v) => v.toString(16).padStart(2, '0'))
    .join('')}`;
};

const formatDateInput = (date) => {
  if (!date) return '';
  return date.toISOString().split('T')[0];
};

const parseDateInput = (value) => {
  if (!value) return null;
  const [yearStr, monthStr, dayStr] = value.split('-');
  const year = Number(yearStr);
  const month = Number(monthStr);
  const day = Number(dayStr);
  if (Number.isNaN(year) || Number.isNaN(month) || Number.isNaN(day)) return null;
  const result = new Date(year, month - 1, day);
  if (Number.isNaN(result.getTime())) return null;
  return result;
};

const startOfWeekMonday = (date) => {
  if (!date) return null;
  const result = new Date(date);
  const day = result.getDay();
  const diff = (day + 6) % 7;
  result.setDate(result.getDate() - diff);
  result.setHours(0, 0, 0, 0);
  return result;
};

const formatMonthInput = (date) => {
  if (!date) return '';
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
};

const parseMonthInput = (value) => {
  if (!value) return null;
  const [yearStr, monthStr] = value.split('-');
  const year = Number(yearStr);
  const month = Number(monthStr);
  if (Number.isNaN(year) || Number.isNaN(month)) return null;
  return { year, month };
};

const getDaysInMonth = (year, month) => new Date(year, month, 0).getDate();

const getQuarterFromMonthIndex = (monthIndex) => Math.floor(monthIndex / 3) + 1;

const getQuarterStart = (year, quarter) => {
  const startMonthIndex = (quarter - 1) * 3;
  return new Date(year, startMonthIndex, 1);
};

const getQuarterDays = (year, quarter) => {
  const startMonthIndex = (quarter - 1) * 3;
  let days = 0;
  for (let i = 0; i < 3; i += 1) {
    days += new Date(year, startMonthIndex + i + 1, 0).getDate();
  }
  return days;
};

const formatRangeLabel = (start, end) => {
  if (!start || !end) return '';
  const startLabel = start.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
  const endLabel = end.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
  return `${startLabel} — ${endLabel}`;
};

const THEME_CONFIG = {
  dark: {
    pageBackground: 'bg-[#111516]',
    overlayGradient: 'radial-gradient(circle at top, rgba(126, 148, 139, 0.18), transparent 60%)',
    textPrimary: 'text-white',
    textSecondary: 'text-white/70',
    textMuted: 'text-white/60',
    textSubtle: 'text-white/40',
    border: 'border-white/10',
    subtleBorder: 'border-white/20',
    surfaceBackground: 'bg-[#1a1f1e]/60',
    surfaceShadow: 'shadow-[0_30px_60px_rgba(0,0,0,0.45)]',
    cardBackground: 'bg-[#121a1c]',
    secondaryCardBackground: 'bg-[#141b1c]',
    inlineCardBackground: 'bg-[#1f2628]',
    badgeBackground: 'bg-black/30',
    badgeText: 'text-white',
    toggleBackground: 'bg-white/10',
    toggleText: 'text-white',
    toggleBorder: 'border-white/20',
    dialogBackground: 'bg-[#111516]',
    dialogBorder: 'border-white/10',
    loaderText: 'text-white/70',
    chartShadow: 'shadow-[0_18px_32px_rgba(94,234,212,0.25)]'
  },
  light: {
    pageBackground: 'bg-[#f6f8fb]',
    overlayGradient: 'none',
    textPrimary: 'text-slate-900',
    textSecondary: 'text-slate-600',
    textMuted: 'text-slate-500',
    textSubtle: 'text-slate-400',
    border: 'border-slate-200',
    subtleBorder: 'border-slate-300',
    surfaceBackground: 'bg-white/80',
    surfaceShadow: 'shadow-sm',
    cardBackground: 'bg-white',
    secondaryCardBackground: 'bg-slate-100',
    inlineCardBackground: 'bg-slate-50',
    badgeBackground: 'bg-slate-200',
    badgeText: 'text-slate-800',
    toggleBackground: 'bg-slate-200',
    toggleText: 'text-slate-800',
    toggleBorder: 'border-slate-300',
    dialogBackground: 'bg-white',
    dialogBorder: 'border-slate-200',
    loaderText: 'text-slate-500',
    chartShadow: 'shadow-[0_18px_32px_rgba(148,163,184,0.22)]'
  }
};

const DETAIL_INITIAL_STATE = {
  open: false,
  title: '',
  text: '',
  advice: '',
  loading: false,
  energy: null
};

const SquareShell = ({
  children,
  className = '',
  style,
  onClick,
  interactive = false,
  borderClass = 'border-white/10',
  shadowClass = 'shadow-[inset_0_1px_0_rgba(255,255,255,0.12)]',
  ...rest
}) => (
  <div
    className={`aspect-square rounded-[26px] border ${borderClass} ${shadowClass} flex items-center justify-center text-center transition-all duration-200 ${
      interactive
        ? 'cursor-pointer hover:shadow-[0_12px_24px_rgba(0,0,0,0.35)] hover:brightness-110 hover:-translate-y-1'
        : ''
    } ${className}`}
    style={style}
    onClick={onClick}
    {...rest}
  >
    {children}
  </div>
);

const Placeholder = () => (
  <SquareShell className="opacity-0 border-transparent shadow-none" borderClass="border-transparent" />
);

const formatCount = (cell) => {
  if (!cell) return 0;
  if (typeof cell === 'number') return cell;
  if (Array.isArray(cell)) return cell.length;
  return String(cell).length;
};

const HIGHLIGHT_MAP = {
  horizontal: [
    [1, 4, 7],
    [2, 5, 8],
    [3, 6, 9]
  ],
  vertical: [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
  ],
  diagonal: [
    [1, 5, 9],
    [3, 5, 7]
  ]
};

const NUMBER_LAYOUT = [
  [1, 4, 7],
  [2, 5, 8],
  [3, 6, 9]
];

const INDEX_BY_NUMBER = {
  1: [0, 0],
  4: [0, 1],
  7: [0, 2],
  2: [1, 0],
  5: [1, 1],
  8: [1, 2],
  3: [2, 0],
  6: [2, 1],
  9: [2, 2]
};

const PLANET_SHORT = {
  1: '☉',
  2: '☽',
  3: '♃',
  4: '☊',
  5: '☿',
  6: '♀',
  7: '☋',
  8: '♄',
  9: '♂'
};

const PLANET_META = [
  { num: 1, name: 'Солнце', vedic: 'Surya', energyKey: 'surya' },
  { num: 2, name: 'Луна', vedic: 'Chandra', energyKey: 'chandra' },
  { num: 3, name: 'Юпитер', vedic: 'Guru', energyKey: 'guru' },
  { num: 4, name: 'Раху', vedic: 'Rahu', energyKey: 'rahu' },
  { num: 5, name: 'Меркурий', vedic: 'Budha', energyKey: 'budha' },
  { num: 6, name: 'Венера', vedic: 'Shukra', energyKey: 'shukra' },
  { num: 7, name: 'Кету', vedic: 'Ketu', energyKey: 'ketu' },
  { num: 8, name: 'Сатурн', vedic: 'Shani', energyKey: 'shani' },
  { num: 9, name: 'Марс', vedic: 'Mangala', energyKey: 'mangal' }
];

const PLANET_MAP = PLANET_META.reduce((acc, meta) => {
  acc[meta.num] = meta;
  return acc;
}, {});

const PLANET_INTERPRETATIONS = {
  1: `Surya — Солнце (1) ☉

Энергия лидерства, творчества и индивидуальности. Солнце — это ваша сущность, ваше «Я», способность быть в центре внимания и вести за собой других.

Качества энергии:
• Лидерство и инициативность
• Творческий потенциал и оригинальность
• Независимость и самостоятельность
• Организаторские способности
• Щедрость и великодушие

Как проявляется:
- В избытке: эгоцентризм, властность, нетерпимость к критике
- В балансе: харизматичность, вдохновляющее лидерство, творческая самореализация
- В недостатке: неуверенность в себе, зависимость от чужого мнения, отсутствие инициативы

Рекомендации для гармонизации:
• Развивайте творческие способности
• Учитесь брать ответственность на себя
• Практикуйте утренние солнечные медитации
• Носите золотые украшения или цвета солнца
• Укрепляйте физическое здоровье и осанку`,
  2: `Чандра — Луна (2) ☽

Энергия эмоций, интуиции и адаптации. Луна отвечает за внутренний мир, способность чувствовать и реагировать на изменения.

Качества энергии:
• Эмоциональность и чувствительность
• Интуиция и психические способности
• Адаптивность и гибкость
• Забота и материнские инстинкты
• Способность к сопереживанию

Как проявляется:
- В избытке: эмоциональная нестабильность, обидчивость, зависимость от настроения
- В балансе: эмоциональный интеллект, интуитивная мудрость, способность к глубоким отношениям
- В недостатке: эмоциональная заблокированность, трудности в выражении чувств

Рекомендации для гармонизации:
• Практикуйте медитации на воду и лунные ритуалы
• Развивайте эмоциональный интеллект
• Создавайте уютную домашнюю атмосферу
• Носите серебро и жемчуг
• Работайте с лунными циклами в планировании`,
  3: `Гуру — Юпитер (3) ♃

Энергия мудрости, обучения и расширения. Юпитер — ваш внутренний учитель, способность расти и передавать знания.

Качества энергии:
• Мудрость и философское мышление
• Способность к обучению и преподаванию
• Оптимизм и вера в лучшее
• Справедливость и этические принципы
• Стремление к развитию

Как проявляется:
- В избытке: самоуверенность, догматизм, склонность к назиданию
- В балансе: мудрое руководство, вдохновляющее обучение, справедливое суждение
- В недостатке: отсутствие веры в себя, трудности с принятием решений, пессимизм

Рекомендации для гармонизации:
• Изучайте философию и духовные практики
• Развивайте навыки наставничества
• Практикуйте благотворительность
• Носите жёлтые оттенки и золото
• Читайте вдохновляющие книги`,
  4: `Раху — Северный узел (4) ☊

Энергия трансформации, амбиций и кармических задач. Раху показывает направление вашего роста в этой жизни.

Качества энергии:
• Амбициозность и стремление к достижениям
• Способность к трансформации и изменениям
• Инновационное мышление
• Магнетизм и притягательность
• Кармические уроки и вызовы

Как проявляется:
- В избытке: одержимость целями, использование других, материализм
- В балансе: здоровые амбиции, способность к позитивным изменениям, харизма
- В недостатке: отсутствие целей, страх перемен, застой

Рекомендации для гармонизации:
• Работайте над кармическими уроками
• Развивайте здоровые амбиции
• Практикуйте техники трансформации сознания
• Изучайте астрологию и эзотерику
• Учитесь отпускать привязанности`,
  5: `Буддха — Меркурий (5) ☿

Энергия интеллекта, коммуникации и адаптации. Меркурий отвечает за ум, способности к обучению и обмен информацией.

Качества энергии:
• Интеллект и аналитика
• Коммуникативные навыки
• Любознательность и обучаемость
• Адаптивность и многозадачность
• Логическое мышление

Как проявляется:
- В избытке: поверхностность, суетливость, непостоянство
- В балансе: ясное мышление, эффективная коммуникация, быстрое обучение
- В недостатке: трудности в общении, проблемы с концентрацией, медлительность

Рекомендации для гармонизации:
• Развивайте навыки речи и письма
• Изучайте иностранные языки
• Практикуйте логические игры
• Носите зелёные оттенки и изумруды
• Занимайтесь дыхательными практиками`,
  6: `Шукра — Венера (6) ♀

Энергия любви, красоты и гармонии. Венера отвечает за отношения, творчество и умение наслаждаться жизнью.

Качества энергии:
• Любовь и чувственность
• Чувство эстетики
• Творческий потенциал
• Гармония в отношениях
• Способность к наслаждению

Как проявляется:
- В избытке: зависимость от удовольствий, лень, поверхностность
- В балансе: гармоничные отношения, вдохновение, чувство прекрасного
- В недостатке: трудности в любви, отсутствие творчества, грубость

Рекомендации для гармонизации:
• Занимайтесь творчеством
• Окружайте себя красотой
• Работайте над гармонией в отношениях
• Носите розовые оттенки и украшения
• Практикуйте любовь к себе`,
  7: `Кету — Южный узел (7) ☋

Энергия духовности, отрешенности и кармического опыта. Кету показывает таланты из прошлых воплощений и путь к свободе.

Качества энергии:
• Духовная мудрость и интуиция
• Способность к медитации и созерцанию
• Отрешённость от материального
• Психические способности
• Кармическая память

Как проявляется:
- В избытке: уход от ответственности, излишняя отрешённость, мистицизм
- В балансе: духовная зрелость, внутреннее спокойствие, свобода
- В недостатке: материалистичность, отсутствие духовных интересов

Рекомендации для гармонизации:
• Практикуйте медитацию и созерцание
• Изучайте духовные учения
• Работайте с прошлыми опытами
• Учитесь отпускать результаты
• Используйте интуицию в решениях`,
  8: `Шани — Сатурн (8) ♄

Энергия дисциплины, ответственности и структуры. Сатурн — строгий наставник, ведущий к зрелости.

Качества энергии:
• Дисциплина и самоконтроль
• Ответственность и надёжность
• Терпение и выносливость
• Структурное мышление
• Долгосрочное планирование

Как проявляется:
- В избытке: чрезмерная строгость, пессимизм, жесткость
- В балансе: мудрая дисциплина, стабильность, достижение целей
- В недостатке: безответственность, хаос, легкомыслие

Рекомендации для гармонизации:
• Развивайте самодисциплину постепенно
• Учитесь планированию и структурированию
• Практикуйте терпение и настойчивость
• Носите насыщенные тёмные оттенки и сапфиры
• Берите ответственность за проекты`,
  9: `Мангал — Марс (9) ♂

Энергия действия, силы и решимости. Марс даёт импульс к достижениям и защите важного.

Качества энергии:
• Виталитет и энергия
• Решительность и смелость
• Способность к активным действиям
• Защитные инстинкты
• Спортивные задатки

Как проявляется:
- В избытке: импульсивность, конфликтность, агрессия
- В балансе: здоровая активность, защита слабых, достижение целей
- В недостатке: пассивность, отсутствие энергии, замедленность

Рекомендации для гармонизации:
• Занимайтесь спортом и танцами
• Развивайте здоровую конкуренцию
• Учитесь направлять энергию конструктивно
• Носите красные оттенки и кораллы
• Практикуйте боевые искусства`
};

const buildPlanetDataSummary = (planetNumber, count = 0, digits = '') => {
  const meta = PLANET_MAP[planetNumber] || {};
  const russianName = meta.name || `Планета ${planetNumber}`;
  const numericLabel = `${russianName} (${planetNumber})`;
  const rawDigits = digits && String(digits).trim().length ? String(digits) : '';
  const digitsDisplay = rawDigits ? rawDigits : '—';
  const digitsSpaced = rawDigits ? rawDigits.split('').join(' ') : '—';

  let countInsight = '';
  if (count === 0) {
    countInsight = `⚠️ Энергия ${russianName.toLowerCase()} пока не проявлена в матрице. Это повод осознавать связанные качества и развивать их через практики и внимание к ежедневным действиям.`;
  } else if (count === 1) {
    countInsight = `🔹 Энергия ${russianName.toLowerCase()} присутствует в базовом виде. Важно заботиться о её реализации, чтобы не допустить дефицита и неравновесия.`;
  } else if (count <= 3) {
    countInsight = `✅ Энергия ${russianName.toLowerCase()} проявлена гармонично. У вас есть ресурсы на развитие качеств планеты и деликатную работу с ними.`;
  } else {
    countInsight = `⚡ Энергия ${russianName.toLowerCase()} выражена очень сильно. Важно направлять её осознанно, чтобы избегать перегибов и сохранять баланс.`;
  }

  return `Данные вашей матрицы:
• Количество (${numericLabel}): ${count}
• Цифровой ряд: ${digitsDisplay} ${digitsSpaced !== '—' ? `(${digitsSpaced})` : ''}

${countInsight}`.trim();
};

const PLANET_CHART_COLORS = {
  1: '#facc15', // Солнце – жёлтый
  2: '#f9fafb', // Луна – белый
  3: '#fb923c', // Юпитер – оранжевый
  4: '#8B4513', // Раху – Коричневый
  5: '#22c55e', // Меркурий – зелёный
  6: '#f472b6', // Венера – розовый
  7: '#808080', // Кету – Серый
  8: '#3b82f6', // Сатурн – синий
  9: '#ef4444'  // Марс – красный
};

const PLANET_COLUMNS = [
  [1, 2, 3],
  [4, 5, 6],
  [7, 8, 9]
];

const WEEK_PLANETS = [
  { dayIndex: 0, dayShort: 'Вс', dayLabel: 'Воскресенье', planet: 'Солнце / Surya', icon: '☉', color: '#facc15' },
  { dayIndex: 1, dayShort: 'Пн', dayLabel: 'Понедельник', planet: 'Луна / Chandra', icon: '☽', color: '#f9fafb' },
  { dayIndex: 2, dayShort: 'Вт', dayLabel: 'Вторник', planet: 'Марс / Mangala', icon: '♂', color: '#ef4444' },
  { dayIndex: 3, dayShort: 'Ср', dayLabel: 'Среда', planet: 'Меркурий / Budha', icon: '☿', color: '#22c55e' },
  { dayIndex: 4, dayShort: 'Чт', dayLabel: 'Четверг', planet: 'Юпитер / Guru', icon: '♃', color: '#fb923c' },
  { dayIndex: 5, dayShort: 'Пт', dayLabel: 'Пятница', planet: 'Венера / Shukra', icon: '♀', color: '#f472b6' },
  { dayIndex: 6, dayShort: 'Сб', dayLabel: 'Суббота', planet: 'Сатурн / Shani', icon: '♄', color: '#3b82f6' }
];

const RUSSIAN_NAME_VALUES = {
  а: 1, б: 2, в: 6, г: 3, д: 4, е: 5, ё: 5, ж: 2, з: 7, и: 1, й: 1,
  к: 2, л: 3, м: 4, н: 5, о: 7, п: 8, р: 2, с: 3, т: 4, у: 6, ф: 8,
  х: 5, ц: 3, ч: 7, ш: 2, щ: 9, ъ: 1, ы: 1, ь: 1, э: 6, ю: 7, я: 2
};

const calculateNameNumber = (name = '') => {
  if (!name) return 0;
  const total = Array.from(name.toLowerCase()).reduce((sum, char) => {
    if (RUSSIAN_NAME_VALUES[char] !== undefined) {
      return sum + RUSSIAN_NAME_VALUES[char];
    }
    return sum;
  }, 0);
  return digitalRoot(total);
};

const calculatePlanetaryEnergySeries = (birthDate, fullName, options = {}) => {
  const { startDate: rawStartDate = new Date(), days = 7 } = options;
  if (!birthDate || !days || days <= 0) {
    return {
      series: [],
      startDate: null,
      endDate: null
    };
  }
  const parts = birthDate.split('.');
  if (parts.length !== 3) {
    return {
      series: [],
      startDate: null,
      endDate: null
    };
  }
  const [dayStr, monthStr, yearStr] = parts;
  const birthDay = parseInt(dayStr, 10);
  const birthMonth = parseInt(monthStr, 10);
  const birthYear = parseInt(yearStr, 10);
  if (
    Number.isNaN(birthDay) ||
    Number.isNaN(birthMonth) ||
    Number.isNaN(birthYear) ||
    birthDay <= 0 ||
    birthMonth <= 0
  ) {
    return {
      series: [],
      startDate: null,
      endDate: null
    };
  }

  const destinyNumber = digitalRoot(birthDay + birthMonth + birthYear);
  const nameNumberRaw = calculateNameNumber(fullName);
  const nameNumber = nameNumberRaw || destinyNumber;

  const startDate = new Date(rawStartDate);
  startDate.setHours(0, 0, 0, 0);

  const series = [];

  for (let i = 0; i < days; i += 1) {
    const currentDate = new Date(startDate);
    currentDate.setDate(startDate.getDate() + i);

    const currentYear = currentDate.getFullYear();
    const personalYear = digitalRoot(birthDay + birthMonth + digitalRoot(currentYear));
    const personalDay = digitalRoot(personalYear + (currentDate.getMonth() + 1) + currentDate.getDate());
    const kDow = DOW_NUMBERS[currentDate.getDay()];

    const energiesByKey = {};
    const energiesByNumber = {};

    PLANET_META.forEach((meta) => {
      const planetNumber = meta.num;
      const affinity =
        Math.min(
          1,
          (planetNumber === destinyNumber ? 1 : 0) +
            0.7 * (planetNumber === nameNumber ? 1 : 0) +
            0.3 * adjacencyScore(planetNumber, destinyNumber) +
            0.2 * adjacencyScore(planetNumber, nameNumber)
        );

      const rhythm = Math.min(
        1,
        (planetNumber === personalDay ? 1 : 0) + 0.5 * adjacencyScore(planetNumber, personalDay)
      );

      const carrier = planetNumber === kDow ? 1 : 0;

      const score = Math.round(
        100 *
          (0.5 * affinity +
            0.3 * rhythm +
            0.2 * carrier)
      );

      energiesByKey[meta.energyKey] = score;
      energiesByNumber[planetNumber] = score;
    });

    const sortedPlanets = PLANET_META.map((meta) => ({
      ...meta,
      score: energiesByNumber[meta.num]
    })).sort((a, b) => b.score - a.score);

    series.push({
      date: currentDate.toISOString(),
      displayDate: currentDate.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' }),
      dayLabel: currentDate.toLocaleDateString('ru-RU', { weekday: 'long' }),
      dayShort: currentDate.toLocaleDateString('ru-RU', { weekday: 'short' }),
      personalYear,
      personalDay,
      kDow,
      energies: energiesByKey,
      energiesByNumber,
      topPlanets: sortedPlanets.slice(0, 2)
    });
  }

  const endDate = series.length
    ? new Date(series[series.length - 1].date)
    : null;

  return {
    series,
    startDate,
    endDate
  };
};

const personalEnergyPointPlugin = {
  id: 'personalEnergyPointPlugin',
  afterDatasetsDraw(chart) {
    const datasetMeta = chart.getDatasetMeta(0);
    const dataset = chart.config.data.datasets[0];
    const points = datasetMeta.data || [];
    if (!dataset?.dataMeta) return;
    const ctx = chart.ctx;
    points.forEach((point, index) => {
      const meta = dataset.dataMeta[index];
      if (!meta || !point) return;
      ctx.save();
      ctx.font = '18px "Inter", sans-serif';
      ctx.fillStyle = meta.color || '#ffffff';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.shadowColor = 'rgba(15,23,42,0.35)';
      ctx.shadowBlur = 6;
      ctx.fillText(meta.icon, point.x, point.y);
      ctx.restore();
    });
  }
};

const PythagoreanSquareNew = () => {
  const { user } = useAuth();
  const [squareData, setSquareData] = useState(null);
  const [personalData, setPersonalData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [detail, setDetail] = useState(DETAIL_INITIAL_STATE);
  const [hoveredNumbers, setHoveredNumbers] = useState([]);
  const [theme, setTheme] = useState(() => {
    if (typeof window === 'undefined') return 'light';
    return (localStorage.getItem('pythagorean-square-theme') || localStorage.getItem('theme')) === 'dark' ? 'dark' : 'light';
  });
  const now = useMemo(() => {
    const date = new Date();
    date.setHours(0, 0, 0, 0);
    return date;
  }, []);
  const [energyRangeMode, setEnergyRangeMode] = useState('week');
  const [selectedWeekDate, setSelectedWeekDate] = useState(() => formatDateInput(startOfWeekMonday(new Date())));
  const [selectedMonth, setSelectedMonth] = useState(() => formatMonthInput(new Date()));
  const [selectedQuarter, setSelectedQuarter] = useState(() => ({
    year: now.getFullYear(),
    quarter: getQuarterFromMonthIndex(now.getMonth())
  }));

  const themeConfig = useMemo(() => THEME_CONFIG[theme], [theme]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('pythagorean-square-theme', theme);
    }
  }, [theme]);

  const toggleTheme = () => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  const isDark = theme === 'dark';
  const textPrimaryClass = themeConfig.textPrimary;
  const textSecondaryClass = themeConfig.textSecondary;
  const textMutedClass = themeConfig.textMuted;
  const textSubtleClass = themeConfig.textSubtle;
  const borderClass = themeConfig.border;
  const surfaceBackgroundClass = themeConfig.surfaceBackground;
  const surfaceShadowClass = themeConfig.surfaceShadow;
  const cardBackgroundClass = themeConfig.cardBackground;
  const secondaryCardBackgroundClass = themeConfig.secondaryCardBackground;
  const inlineCardBackgroundClass = themeConfig.inlineCardBackground;
  const badgeBackgroundClass = themeConfig.badgeBackground;
  const badgeTextClass = themeConfig.badgeText;
  const toggleClassName = `inline-flex items-center gap-2 rounded-2xl px-4 py-2 border transition-all duration-200 ${themeConfig.toggleBackground} ${themeConfig.toggleText} ${themeConfig.toggleBorder}`;
  const dialogClassName = `${themeConfig.dialogBackground} ${themeConfig.dialogBorder}`;
  const loaderTextClass = themeConfig.loaderText;
  const chartShadowClass = themeConfig.chartShadow;
  const squareBorderClass = themeConfig.border;
  const sumBoxBackgroundClass = theme === 'dark' ? 'bg-[#0f1518]' : 'bg-white';
  const sumHoverClass = theme === 'dark' ? 'hover:bg-[#162022]' : 'hover:bg-slate-100';
  const cardShadowClass = theme === 'dark' ? 'shadow-[0_18px_32px_rgba(94,234,212,0.25)]' : 'shadow-[0_18px_32px_rgba(148,163,184,0.2)]';

  const backendUrl = useMemo(() => getBackendUrl(), []);
  const apiBaseUrl = useMemo(() => getApiBaseUrl(), []);

  useEffect(() => {
    if (!user?.birth_date) return;

    const fetchData = async () => {
      setLoading(true);
      setError('');
      try {
        const squareResponse = await axios.post('/numerology/pythagorean-square');
        const data = squareResponse.data;
        setSquareData(data);
        // Используем те же данные для personalData, так как бэкенд возвращает все поля
        setPersonalData(data);
      } catch (err) {
        console.error('Ошибка загрузки квадрата Пифагора (новый дизайн):', err);
        const detail = err?.response?.data?.detail;
        setError(
          detail ||
            'Не удалось получить данные квадрата Пифагора. Попробуйте обновить страницу или повторить позже.'
        );
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [apiBaseUrl, user?.birth_date]);

  const matrix = useMemo(() => {
    if (Array.isArray(squareData?.square) && squareData.square.length === 3) {
      return squareData.square;
    }
    // Фолбэк для теста без данных
    return [
      ['1', '3', '10'],
      ['5', '01', '6'],
      ['4', '', '11']
    ];
  }, [squareData]);

const topPersonal = [
  { key: 'soul_number', label: 'ч/д', accent: true, type: 'soul' },
  { key: 'mind_number', label: 'ч/у', type: 'mind' },
  { key: 'destiny_number', label: 'ч/с', type: 'destiny' }
];

const bottomPersonal = [
  { key: 'helping_mind_number', label: 'ч/у*', type: 'helping_mind' },
  { key: 'wisdom_number', label: 'ч/м', type: 'wisdom' },
  { key: 'ruling_number', label: 'п/ч', type: 'ruling' }
];

const personalCycles = [
  { key: 'personal_year', label: 'Л/Г', type: 'personalYear' },
  { key: 'personal_month', label: 'Л/М', type: 'personalMonth' },
  { key: 'personal_day', label: 'Л/Д', type: 'personalDay' },
  { key: 'personal_hour', label: 'Л/Ч', type: 'personalHour' },
  { key: 'challenge_number', label: 'Ч/П', type: 'challengeNumber' }
];

  const energyRangeConfig = useMemo(() => {
    if (energyRangeMode === 'month') {
      const parsed = parseMonthInput(selectedMonth) || {
        year: now.getFullYear(),
        month: now.getMonth() + 1
      };
      const year = Number.isNaN(parsed.year) ? now.getFullYear() : parsed.year;
      const month = Number.isNaN(parsed.month) ? now.getMonth() + 1 : parsed.month;
      const startDate = new Date(year, month - 1, 1);
      startDate.setHours(0, 0, 0, 0);
      const days = getDaysInMonth(year, month);
      const endDate = new Date(startDate);
      endDate.setDate(startDate.getDate() + days - 1);
      return {
        mode: 'month',
        startDate,
        days,
        month,
        year,
        label: startDate.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' }),
        rangeLabel: formatRangeLabel(startDate, endDate)
      };
    }

    if (energyRangeMode === 'quarter') {
      const year = Number(selectedQuarter?.year) || now.getFullYear();
      const normalizedQuarter = Math.min(4, Math.max(1, Number(selectedQuarter?.quarter) || getQuarterFromMonthIndex(now.getMonth())));
      const startDate = getQuarterStart(year, normalizedQuarter);
      startDate.setHours(0, 0, 0, 0);
      const days = getQuarterDays(year, normalizedQuarter);
      const endDate = new Date(startDate);
      endDate.setDate(startDate.getDate() + days - 1);
      return {
        mode: 'quarter',
        startDate,
        days,
        quarter: normalizedQuarter,
        year,
        label: `Квартал ${normalizedQuarter} · ${year}`,
        rangeLabel: formatRangeLabel(startDate, endDate)
      };
    }

    const baseDate = parseDateInput(selectedWeekDate) || now;
    const startDate = startOfWeekMonday(baseDate) || startOfWeekMonday(now) || now;
    const endDate = new Date(startDate);
    endDate.setDate(startDate.getDate() + 6);
    return {
      mode: 'week',
      startDate,
      days: 7,
      label: 'Неделя',
      rangeLabel: formatRangeLabel(startDate, endDate)
    };
  }, [energyRangeMode, selectedMonth, selectedQuarter, selectedWeekDate, now]);

  const handleShiftWeek = useCallback(
    (offset) => {
      const base = parseDateInput(selectedWeekDate) || now;
      const start = startOfWeekMonday(base) || startOfWeekMonday(now) || now;
      start.setDate(start.getDate() + offset * 7);
      setSelectedWeekDate(formatDateInput(start));
    },
    [selectedWeekDate, now]
  );

  const handleShiftMonth = useCallback(
    (offset) => {
      const parsed = parseMonthInput(selectedMonth);
      const baseYear = parsed?.year ?? now.getFullYear();
      const baseMonthIndex = (parsed?.month ?? now.getMonth() + 1) - 1;
      const target = new Date(baseYear, baseMonthIndex + offset, 1);
      setSelectedMonth(formatMonthInput(target));
    },
    [selectedMonth, now]
  );

  const handleShiftQuarter = useCallback(
    (offset) => {
      const currentYear = Number(selectedQuarter?.year) || now.getFullYear();
      const currentQuarter = Number(selectedQuarter?.quarter) || getQuarterFromMonthIndex(now.getMonth());
      const combined = currentQuarter - 1 + offset;
      const normalizedQuarter = ((combined % 4) + 4) % 4;
      const newQuarter = normalizedQuarter + 1;
      const yearDelta = Math.floor((currentQuarter - 1 + offset) / 4);
      const newYear = currentYear + yearDelta;
      setSelectedQuarter({ year: newYear, quarter: newQuarter });
    },
    [selectedQuarter, now]
  );

  const rangeInputClass = useMemo(
    () =>
      theme === 'dark'
        ? 'h-10 rounded-xl border border-white/15 bg-black/25 px-3 text-sm text-white placeholder-white/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400'
        : 'h-10 rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-900 placeholder-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400',
    [theme]
  );

  const rangeNavButtonClass = useMemo(
    () =>
      theme === 'dark'
        ? 'h-10 w-10 rounded-xl border border-white/15 text-white/70 hover:text-white hover:border-white/30 transition-colors'
        : 'h-10 w-10 rounded-xl border border-slate-200 text-slate-600 hover:text-slate-900 hover:border-slate-300 transition-colors',
    [theme]
  );

  const rangeButtonClass = useCallback(
    (mode) => {
      const isActive = energyRangeMode === mode;
      if (isActive) {
        return 'px-3 py-1.5 rounded-xl border border-transparent bg-emerald-500 text-white shadow-lg shadow-emerald-400/30 transition-all';
      }
      if (theme === 'dark') {
        return 'px-3 py-1.5 rounded-xl border border-white/10 text-white/70 hover:text-white hover:border-white/25 transition-all';
      }
      return 'px-3 py-1.5 rounded-xl border border-slate-200 text-slate-600 hover:text-slate-900 hover:border-slate-300 transition-all';
    },
    [energyRangeMode, theme]
  );

  // Загрузка данных динамики энергии планет из backend
  const [energyData, setEnergyData] = useState(null);
  const [energyLoading, setEnergyLoading] = useState(false);

  useEffect(() => {
    const loadEnergyData = async () => {
      if (!energyRangeConfig?.days || !user?.birth_date) {
        setEnergyData(null);
        return;
      }
      
      setEnergyLoading(true);
      try {
        const token = localStorage.getItem('token');
        const headers = { 'Authorization': `Bearer ${token}` };
        const url = getBackendUrl();
        const response = await fetch(`${url}/api/charts/planetary-energy/${energyRangeConfig.days}`, { headers });
        if (!response.ok) throw new Error('Ошибка загрузки данных');
        const data = await response.json();
        setEnergyData(data);
      } catch (error) {
        console.error('Ошибка загрузки динамики энергии:', error);
        setEnergyData(null);
      } finally {
        setEnergyLoading(false);
      }
    };

    loadEnergyData();
  }, [energyRangeConfig?.days, user?.birth_date]);

  const energyRangeResult = useMemo(() => {
    if (!energyData?.chart_data || energyData.chart_data.length === 0) {
      return { series: [], startDate: null, endDate: null };
    }
    
    // Преобразуем данные из backend в формат, ожидаемый компонентом
    const series = energyData.chart_data.map((day) => {
      const date = new Date(day.date);
      return {
        date: date.toISOString(),
        displayDate: date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' }),
        dayLabel: day.day_name || date.toLocaleDateString('ru-RU', { weekday: 'long' }),
        dayShort: date.toLocaleDateString('ru-RU', { weekday: 'short' }),
        energies: {
          surya: day.surya || 0,
          chandra: day.chandra || 0,
          mangal: day.mangal || 0,
          budha: day.budha || 0,
          guru: day.guru || 0,
          shukra: day.shukra || 0,
          shani: day.shani || 0,
          rahu: day.rahu || 0,
          ketu: day.ketu || 0
        }
      };
    });

    const startDate = series.length > 0 ? new Date(series[0].date) : null;
    const endDate = series.length > 0 ? new Date(series[series.length - 1].date) : null;

    return { series, startDate, endDate };
  }, [energyData]);

  const energySeries = energyRangeResult.series || [];
  const energyRangeStart = energyRangeResult.startDate;
  const energyRangeEnd = energyRangeResult.endDate;

  const planetCounts = useMemo(() => {
    const counts = {};
    NUMBER_LAYOUT.forEach((row, rowIndex) => {
      row.forEach((num, colIndex) => {
        const cell = matrix?.[rowIndex]?.[colIndex];
        counts[num] = formatCount(cell);
      });
    });
    return counts;
  }, [matrix]);

  const getDigitsForNumber = useCallback(
    (numberId) => {
      const coords = INDEX_BY_NUMBER[numberId];
      if (!coords) return '';
      const [row, col] = coords;
      const cellValue = matrix?.[row]?.[col];
      if (!cellValue) return '';
      if (typeof cellValue === 'string') return cellValue;
      if (Array.isArray(cellValue)) return cellValue.join('');
      return String(cellValue);
    },
    [matrix]
  );

  const horizontalSums = squareData?.horizontal_sums ?? [0, 0, 0];
  const verticalSums = squareData?.vertical_sums ?? [0, 0, 0];
  const diagonalSums = squareData?.diagonal_sums ?? [0, 0];
  const getPlanetEnergyValue = (energyKey) => {
    if (!energySeries.length) return null;
    const firstDay = energySeries[0];
    if (!firstDay) return null;
    const value = firstDay.energies?.[energyKey];
    return value === undefined || value === null ? null : value;
  };

  const energyChartData = useMemo(() => {
    if (!energySeries.length) return null;
    const labels = energySeries.map((day, index) => {
      if (day.displayDate) return day.displayDate;
      const raw = day.date ? new Date(day.date).toLocaleDateString('ru-RU') : null;
      return raw || `День ${index + 1}`;
    });

    const datasets = PLANET_META.map(({ num, name, vedic, energyKey }) => {
      const color = PLANET_CHART_COLORS[num] || '#38bdf8';
      const series = energySeries.map((day) => {
        const value = day.energies?.[energyKey];
        return value === undefined || value === null ? null : value;
      });
      if (!series.some((value) => value !== null)) return null;
      return {
        label: `${name} / ${vedic}`,
        data: series,
        borderColor: color,
        backgroundColor: adjustColor(color, 0.3),
        borderWidth: 2,
        pointRadius: 4,
        pointBackgroundColor: color,
        pointHoverRadius: 6,
        pointHoverBackgroundColor: adjustColor(color, 0.4),
        tension: 0.35,
        spanGaps: true
      };
    }).filter(Boolean);

    if (!datasets.length) return null;
    return { labels, datasets };
  }, [energySeries]);

  const energyChartOptions = useMemo(() => {
    const axisColor = theme === 'dark' ? 'rgba(226, 232, 240, 0.75)' : 'rgba(71, 85, 105, 0.85)';
    const gridColor = theme === 'dark' ? 'rgba(148,163,184,0.22)' : 'rgba(148,163,184,0.28)';
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: theme === 'dark' ? 'rgba(31, 41, 55, 0.95)' : 'rgba(255, 255, 255, 0.95)',
          titleColor: theme === 'dark' ? '#fff' : '#000',
          bodyColor: theme === 'dark' ? '#d1d5db' : '#4b5563',
          borderColor: theme === 'dark' ? 'rgba(75, 85, 99, 0.3)' : 'rgba(209, 213, 219, 0.8)',
          borderWidth: 1,
          padding: 12,
          displayColors: true,
          callbacks: {
            label: (context) => {
              const value = context.parsed.y;
              return `${context.dataset.label}: ${value ?? '—'}%`;
            }
          }
        }
      },
      scales: {
        x: {
          ticks: { color: axisColor, font: { size: 11 } },
          grid: { color: gridColor }
        },
        y: {
          ticks: {
            color: axisColor,
            font: { size: 11 },
            callback: (val) => `${val}%`
          },
          grid: { color: gridColor },
          suggestedMin: 0,
          suggestedMax: 100
        }
      },
      elements: {
        point: {
          hitRadius: 12,
          hoverRadius: 6
        }
      }
    };
  }, [theme]);

  const personalEnergy = useMemo(() => {
    if (!user?.birth_date) return null;
    try {
      const [dayStr, monthStr, yearStr] = user.birth_date.split('.');
      if (!dayStr || !monthStr || !yearStr) return null;

      const day = parseInt(dayStr, 10);
      const month = parseInt(monthStr, 10);
      const year = parseInt(yearStr, 10);
      if (Number.isNaN(day) || Number.isNaN(month) || Number.isNaN(year)) return null;

      const dayMonth = `${day.toString().padStart(2, '0')}${month.toString().padStart(2, '0')}`;
      const baseNumber = parseInt(dayMonth, 10) * year;
      let digits = String(baseNumber);
      if (digits.length < 7) {
        digits = digits.padEnd(7, '0');
      } else if (digits.length > 7) {
        digits = digits.slice(0, 7);
      }

      const birthDateObj = new Date(year, month - 1, day);
      const startIndex = birthDateObj.getDay(); // 0 (Sunday) - 6 (Saturday)
      const values = new Array(7).fill(0);
      for (let i = 0; i < 7; i += 1) {
        const targetIndex = (startIndex + i) % 7;
        values[targetIndex] = parseInt(digits[i], 10);
      }

      const series = WEEK_PLANETS.map((meta, idx) => {
        const color = meta.color || '#38bdf8';
        return {
          ...meta,
          value: values[idx] ?? 0,
          hoverColor: adjustColor(color, 0.35),
          borderColor: adjustColor(color, -0.25)
        };
      });

      const product = baseNumber;
      const formattedProduct = product.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');

      const chartData = {
        labels: series.map((meta) => meta.dayShort),
        datasets: [
          {
            label: 'Энергия дня',
            data: series.map((meta) => meta.value),
            borderColor: '#22d3ee',
            backgroundColor: 'rgba(34,211,238,0.18)',
            borderWidth: 3,
            pointBackgroundColor: series.map((meta) => meta.color),
            pointBorderColor: series.map((meta) => meta.borderColor || meta.color),
            pointBorderWidth: 4,
            pointHoverBackgroundColor: series.map((meta) => meta.hoverColor || meta.color),
            pointHoverBorderColor: series.map((meta) => meta.hoverColor || meta.color),
            pointRadius: 14,
            pointHoverRadius: 18,
            tension: 0.45,
            fill: {
              target: 'origin',
              above: 'rgba(34,211,238,0.12)'
            },
            dataMeta: series
          }
        ]
      };

      return {
        series,
        chartData,
        code: digits,
        calculation: {
          dayMonth,
          year,
          product,
          formattedProduct
        }
      };
    } catch {
      return null;
    }
  }, [user?.birth_date]);

  const personalEnergyChartOptions = useMemo(() => {
    const axisColor = theme === 'dark' ? 'rgba(226, 232, 240, 0.75)' : 'rgba(71, 85, 105, 0.85)';
    const gridColor = theme === 'dark' ? 'rgba(148,163,184,0.2)' : 'rgba(148,163,184,0.28)';
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (context) => {
              const value = context.parsed.y;
              const meta = context.dataset?.dataMeta?.[context.dataIndex] || WEEK_PLANETS[context.dataIndex];
              return `${meta?.dayLabel || ''} • ${meta?.planet || ''}: ${value ?? 0}`;
            },
            title: (context) => {
              const meta = context?.[0]?.dataset?.dataMeta?.[context[0].dataIndex] || WEEK_PLANETS[context[0].dataIndex];
              return `${meta?.dayShort || ''} · ${meta?.planet || ''}`;
            }
          }
        }
      },
      scales: {
        x: {
          ticks: { color: axisColor, font: { size: 11 } },
          grid: { color: gridColor }
        },
        y: {
          ticks: { color: axisColor, font: { size: 11 } },
          grid: { color: gridColor },
          suggestedMin: 0,
          suggestedMax: 9,
          stepSize: 1
        }
      },
      elements: {
        point: { hitRadius: 12, hoverRadius: 6 }
      }
    };
  }, [theme]);
  const openDetail = useCallback((title, text, options = {}) => {
    const names={'Число Души (ч/д)':'soul','Число Ума (ч/у)':'mind','Число Судьбы (ч/с)':'destiny','Число Ума* (ч/у*)':'helping_mind','Число Мудрости (ч/м)':'wisdom','Правящее Число (п/ч)':'ruling','Горизонталь 1-4-7':'row-0','Горизонталь 2-5-8':'row-1','Горизонталь 3-6-9':'row-2','Вертикаль 1-2-3':'col-0','Вертикаль 4-5-6':'col-1','Вертикаль 7-8-9':'col-2','Диагональ 1-5-9':'diag-0','Диагональ 3-5-7':'diag-1'};
    setDetail({
      open: true,
      title,
      text,
      narrationId:names[title],
      advice: options.advice ?? '',
      loading: options.loading ?? false,
      energy: options.energy ?? null
    });
  }, []);

  const closeDetail = useCallback(() => {
    setDetail(DETAIL_INITIAL_STATE);
  }, []);

  const PLANET_DETAILS = useMemo(
    () => ({
      1: {
        title: 'Солнце / Surya (1)',
        text: 'Символ лидерства, личности и творческой силы. Подсветка показывает сколько единиц в вашей матрице: чем их больше, тем ярче проявляется уверенность, инициатива и способность вести за собой.'
      },
      2: {
        title: 'Луна / Chandra (2)',
        text: 'Отвечает за эмоциональность, интуицию и гибкость. Баланс двоек показывает, насколько гармонично вы взаимодействуете с чувствами и окружением.'
      },
      3: {
        title: 'Юпитер / Guru (3)',
        text: 'Три — энергия знаний и общения. Связан с учительством, оптимизмом и способностью вдохновлять. Количество троек отражает ваш интеллектуальный потенциал и харизму.'
      },
      4: {
        title: 'Раху / Rahu (4)',
        text: 'Раху показывает фундамент, систему и выносливость. Раху даёт силу воли, практичность и способность организовывать процессы.'
      },
      5: {
        title: 'Меркурий / Budha (5)',
        text: 'Пятёрка — центр матрицы, отвечающий за коммуникацию, адаптивность и интеллект. Это нервная система квадрата, показатель гибкости и скорости мышления.'
      },
      6: {
        title: 'Венера / Shukra (6)',
        text: 'Шестёрки отражают гармонию, любовь и эстетическое восприятие. Венера даёт умение чувствовать красоту, заботиться и взаимодействовать с людьми мягко.'
      },
      7: {
        title: 'Кету / Ketu (7)',
        text: 'Семёрка связана с духовностью и внутренним компасом. Кету отвечает за интуитивные инсайты, связь с традицией и поиском истины.'
      },
      8: {
        title: 'Сатурн / Shani (8)',
        text: 'Восьмёрка — дисциплина, ответственность и структурирование. Сатурн показывает вашу устойчивость, терпение и отношение к труду.'
      },
      9: {
        title: 'Марс / Mangala (9)',
        text: 'Девятки — энергия действия, смелости и решительности. Марс отвечает за импульс к поступкам, защиту и жизненную силу.'
      }
    }),
    []
  );

  const fetchPlanetAdvice = useCallback(
    async (planetNumber, energyScore) => {
      if (!backendUrl) {
        setDetail((prev) => {
          if (!prev.open) return prev;
          return {
            ...prev,
            loading: false,
            advice: 'Нет подключения к серверу. Проверьте настройки BACKEND_URL.'
          };
        });
        return;
      }
      try {
        const token = localStorage.getItem('token');
        const headers = token ? { Authorization: `Bearer ${token}` } : undefined;
        const response = await axios.get(
          `/numerology/planetary-advice/${planetNumber}`,
          {
            params: { score: energyScore },
            headers
          }
        );
        const advice = response.data?.advice;
        setDetail((prev) => {
          if (!prev.open) return prev;
          return {
            ...prev,
            loading: false,
            advice: advice || 'Совет не найден. Попробуйте позже.'
          };
        });
      } catch (err) {
        console.error('Ошибка получения совета по планете:', err);
        setDetail((prev) => {
          if (!prev.open) return prev;
          return {
            ...prev,
            loading: false,
            advice: 'Не удалось получить рекомендации. Попробуйте позже.'
          };
        });
      }
    },
    [apiBaseUrl]
  );

  const handlePlanetCardClick = useCallback(
    (planetNumber, energyScore, extras = {}) => {
      const meta = PLANET_DETAILS[planetNumber];
      if (!meta) return;

      const normalizedEnergy =
        typeof energyScore === 'number' && !Number.isNaN(energyScore)
          ? Math.max(0, Math.min(100, Math.round(energyScore)))
          : null;

      const summaryText = meta.text;
      const interpretationText = PLANET_INTERPRETATIONS[planetNumber];
      const dataSummary = buildPlanetDataSummary(
        planetNumber,
        typeof extras.count === 'number' ? extras.count : 0,
        extras.digits ?? ''
      );

      const detailBody = [summaryText, interpretationText, dataSummary].filter(Boolean).join('\n\n');

      openDetail(meta.title, detailBody, {
        loading: normalizedEnergy !== null,
        energy: normalizedEnergy,
        advice: normalizedEnergy === null ? 'Нет данных по энергии для формирования рекомендаций.' : ''
      });

      if (normalizedEnergy !== null) {
        fetchPlanetAdvice(planetNumber, normalizedEnergy);
      }
    },
    [fetchPlanetAdvice, openDetail]
  );

  const PERSONAL_DETAILS = {
    soul: {
      title: 'Число Души (ч/д)',
      text: 'Проявление вашей сущности, того, что вдохновляет и наполняет энергией. Это то, кем вы себя чувствуете внутри. Число душевной мотивации раскрывает истинные желания и творческий потенциал.'
    },
    mind: {
      title: 'Число Ума (ч/у)',
      text: 'Отвечает за способ мышления, восприятие информации и стиль общения. Показывает, какие решения вы принимаете и как реагируете на происходящее.'
    },
    destiny: {
      title: 'Число Судьбы (ч/с)',
      text: 'Главный вектор развития, жизненная миссия и задачи, которые приходит решать человек. Показывает направление, в котором раскрывается ваш потенциал.'
    },
    helping_mind: {
      title: 'Число Ума* (ч/у*)',
      text: 'Дополнительная поддержка числа ума: помогает найти обходные пути, развивать новые навыки и flexibilность мышления.'
    },
    wisdom: {
      title: 'Число Мудрости (ч/м)',
      text: 'Интегральное число, показывающее, насколько глубоко вы осмысливаете опыт и умеете извлекать уроки. Связано с интуицией и «внутренним учителем».'
    },
    ruling: {
      title: 'Правящее Число (п/ч)',
      text: 'Сочетает влияние дня и месяца рождения, реагирует на обстоятельства и помогает использовать сильные стороны в каждом моменте. Часто проявляется в повседневных решениях.'
    },
    personalYear: {
      title: 'Личный Год',
      text: 'Показывает основную энергию и тему текущего года в вашей жизни. Каждый год имеет свой ритм и задачи.'
    },
    personalMonth: {
      title: 'Личный Месяц',
      text: 'Отражает энергию текущего месяца и помогает понять, на что сейчас стоит обратить внимание.'
    },
    personalDay: {
      title: 'Личный День',
      text: 'Энергия сегодняшнего дня. Помогает выбрать правильные действия и настроиться на нужную волну.'
    },
    personalHour: {
      title: 'Личный Час',
      text: 'Текущая энергия часа. Показывает, какие дела сейчас будут наиболее эффективны.'
    },
    challengeNumber: {
      title: 'Число Проблемы',
      text: 'Показывает внутренний конфликт между желаниями души и жизненным предназначением. Работа с этим числом помогает найти гармонию.'
    }
  };

  const HORIZONTAL_INFO = [
    {
      title: 'Горизонталь 1-4-7',
      text: 'Верхняя линия описывает сферу воли, целей и внутренних опор. Цифры 1, 4 и 7 формируют ваш запас силы, ответственность и устремленность. Чем больше значение, тем увереннее вы продумываете путь и удерживаете фокус.'
    },
    {
      title: 'Горизонталь 2-5-8',
      text: 'Средняя линия отражает эмоциональную и коммуникативную сферу: числа 2, 5 и 8 отвечают за гибкость, интеллект и взаимодействие с людьми. Высокая сумма показывает умение общаться, чувствовать и адаптироваться.'
    },
    {
      title: 'Горизонталь 3-6-9',
      text: 'Нижняя линия — это область реализации и результатов. Цифры 3, 6 и 9 показывают практичность, материальную устойчивость и способность доводить дела до конца.'
    }
  ];

  const VERTICAL_INFO = [
    {
      title: 'Вертикаль 1-2-3',
      text: 'Левая вертикаль описывает интеллект, любознательность и способность к обучению. Баланс единиц, двоек и троек показывает, насколько легко вам даются идеи, теория и анализ.'
    },
    {
      title: 'Вертикаль 4-5-6',
      text: 'Центральная вертикаль связана с деятельностью, коммуникацией и ответственностью. Числа 4, 5 и 6 отвечают за организацию процессов, работу с информацией и умение быть опорой.'
    },
    {
      title: 'Вертикаль 7-8-9',
      text: 'Правая вертикаль — линия опыта и действий. Она показывает, как вы реализуете идеи в мире, насколько решительны, настойчивы и готовы защищать свои решения.'
    }
  ];

  const DIAGONAL_INFO = [
    {
      title: 'Диагональ 1-5-9',
      text: 'Духовная диагональ. Показывает путь развития личности, стремление к смыслам и самореализации. Чем выше значение, тем сильнее тяга к осознанию миссии и внутреннему росту.'
    },
    {
      title: 'Диагональ 3-5-7',
      text: 'Материальная диагональ. Связана с практическим опытом, ремеслом и мастерством. Большой показатель говорит о способности действовать, создавать и заземлять идеи.'
    }
  ];

  return (
    <div
      className={`min-h-screen relative overflow-hidden transition-colors duration-500 ${themeConfig.pageBackground} ${textPrimaryClass}`}
    >
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: themeConfig.overlayGradient }}
      />
      <div className="relative z-10 mx-auto max-w-6xl px-2 py-4 md:py-6">
        <div className="mb-8 flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-semibold tracking-tight mb-2">
            Ваша карта чисел
          </h1>
            <p className={`${textSecondaryClass} text-sm md:text-base max-w-2xl`}>
            Персональные числа, квадрат Пифагора и планетарные энергии по вашей дате рождения.
          </p>
          </div>
          <button type="button" onClick={toggleTheme} className={toggleClassName}>
            {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            <span>{theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}</span>
          </button>
        </div>

        <div
          className={`rounded-3xl border ${borderClass} ${surfaceBackgroundClass} ${surfaceShadowClass} backdrop-blur-md p-6 md:p-10 overflow-x-auto`}
        >
          {loading ? (
            <div className={`flex flex-col items-center justify-center py-16 gap-3 ${loaderTextClass}`}>
              <Loader2 className={`w-8 h-8 animate-spin ${textMutedClass}`} />
              <span>Загружаем данные...</span>
            </div>
          ) : error ? (
            <div className="rounded-2xl border border-red-500/30 bg-red-500/10 px-6 py-5 text-sm text-red-700 dark:text-red-200">
              {error}
            </div>
          ) : (
            <div className="flex flex-col gap-12">
              <div
                className="inline-grid gap-4 md:gap-5"
                style={{ gridTemplateColumns: 'repeat(5, minmax(90px, 1fr))' }}
              >
              {topPersonal.map((item, rowIndex) => {
                const value = personalData?.[item.key] ?? '-';
                return (
                  <React.Fragment key={item.key}>
                    <SquareShell
                      borderClass={squareBorderClass}
                      className={`${valueGradient} ${
                        item.accent ? 'from-[#9cb4ab] via-[#88a099] to-[#5c6a65]' : ''
                      } ${textPrimaryClass} flex-col`}
                      interactive
                      onMouseEnter={() => setHoveredNumbers([])}
                      onMouseLeave={() => setHoveredNumbers([])}
                      onClick={() =>
                        openDetail(
                          PERSONAL_DETAILS[item.type].title,
                          PERSONAL_DETAILS[item.type].text
                        )
                      }
                    >
                      <span className={`text-sm uppercase tracking-[0.4em] ${textMutedClass}`}>{item.label}</span>
                      <span className="mt-1 text-3xl font-semibold">{value}</span>
                    </SquareShell>
                    {NUMBER_LAYOUT[rowIndex].map((numberId) => {
                      const [originRow, originCol] = INDEX_BY_NUMBER[numberId];
                      const cell = matrix[originRow]?.[originCol];
                      const colorConfig = CELL_COLORS[numberId] || CELL_COLORS[1];
                      const count = formatCount(cell);
                      const metaPlanet = PLANET_MAP[numberId];
                      const energyValue = metaPlanet ? getPlanetEnergyValue(metaPlanet.energyKey) : null;
                      const digitsString =
                        typeof cell === 'string'
                          ? cell
                          : Array.isArray(cell)
                          ? cell.join('')
                          : cell
                          ? String(cell)
                          : '';
                      const planetSymbol = PLANET_SHORT[numberId];
                      const baseShadow = 'inset 0 1px 0 rgba(255,255,255,0.22)';
                      const combinedShadow = colorConfig.glow
                        ? `${baseShadow}, ${colorConfig.glow}`
                        : baseShadow;
                      const highlighted = hoveredNumbers.includes(numberId);
                      const highlightedShadow = highlighted
                        ? `${combinedShadow}, 0 0 22px rgba(147, 197, 253, 0.55)`
                        : combinedShadow;
                      return (
                        <SquareShell
                          key={numberId}
                          borderClass={squareBorderClass}
                          className="flex-col"
                          style={{
                            background: colorConfig.background,
                            boxShadow: highlightedShadow,
                            borderColor: colorConfig.border,
                            filter: highlighted ? 'brightness(1.12)' : undefined,
                            transform: highlighted ? 'scale(1.02)' : undefined
                          }}
                          onClick={() =>
                            handlePlanetCardClick(numberId, energyValue, {
                              count,
                              digits: digitsString
                            })
                          }
                        interactive
                      >
                          <span
                            className="text-3xl font-semibold drop-shadow-sm"
                            style={{ color: colorConfig.text }}
                          >
                            {count}
                          </span>
                          <span
                            className="mt-1 text-xs uppercase tracking-[0.35em] flex items-center justify-center gap-1"
                            style={{ color: `${colorConfig.text}aa` }}
                          >
                            {planetSymbol && <span className="text-base leading-none">{planetSymbol}</span>}
                            {numberId}
                          </span>
                        </SquareShell>
                      );
                    })}
                    <SquareShell
                      borderClass={squareBorderClass}
                      className={`bg-gradient-to-br from-[#5f6b67] via-[#505855] to-[#2f3432] flex-col ${textPrimaryClass}`}
                      interactive
                      onMouseEnter={() => setHoveredNumbers(HIGHLIGHT_MAP.horizontal[rowIndex])}
                      onMouseLeave={() => setHoveredNumbers([])}
                      onClick={() => openDetail(HORIZONTAL_INFO[rowIndex].title, HORIZONTAL_INFO[rowIndex].text)}
                    >
                      <span className="text-3xl font-semibold">{horizontalSums[rowIndex] ?? '-'}</span>
                      <span className={`mt-1 text-[11px] uppercase tracking-[0.35em] ${textSubtleClass}`}>
                        <span className="md:hidden">гор. {rowIndex + 1}</span>
                        <span className="hidden md:inline">горизонталь {rowIndex + 1}</span>
                      </span>
                    </SquareShell>
                  </React.Fragment>
                );
              })}

              <SquareShell
                borderClass={squareBorderClass}
                className={`bg-gradient-to-br from-[#5f6b67] via-[#4f5854] to-[#2f3332] flex-col ${textPrimaryClass}`}
                interactive
                onMouseEnter={() => setHoveredNumbers(HIGHLIGHT_MAP.diagonal[1])}
                onMouseLeave={() => setHoveredNumbers([])}
                onClick={() => openDetail(DIAGONAL_INFO[1].title, DIAGONAL_INFO[1].text)}
              >
                <span className={`text-[11px] uppercase tracking-[0.35em] ${textMutedClass}`}>диаг.</span>
                <span className="mt-1 text-3xl font-semibold">{diagonalSums[1] ?? '-'}</span>
                <span className={`text-[11px] uppercase tracking-[0.35em] ${textSubtleClass} mt-1`}>3-5-7</span>
              </SquareShell>
              {verticalSums.map((value, idx) => (
                <SquareShell
                  key={`v-${idx}`}
                  borderClass={squareBorderClass}
                  className={`bg-gradient-to-br from-[#5f6b67] via-[#505855] to-[#2f3432] flex-col ${textPrimaryClass}`}
                  interactive
                  onMouseEnter={() => setHoveredNumbers(HIGHLIGHT_MAP.vertical[idx])}
                  onMouseLeave={() => setHoveredNumbers([])}
                  onClick={() => openDetail(VERTICAL_INFO[idx].title, VERTICAL_INFO[idx].text)}
                >
                  <span className="text-3xl font-semibold">{value}</span>
                  <span className={`mt-1 text-[11px] uppercase tracking-[0.35em] ${textSubtleClass}`}>
                    <span className="md:hidden">вер. {idx + 1}</span>
                    <span className="hidden md:inline">вертикаль {idx + 1}</span>
                  </span>
                </SquareShell>
              ))}
              <SquareShell
                borderClass={squareBorderClass}
                className={`bg-gradient-to-br from-[#5f6b67] via-[#4f5854] to-[#2f3332] flex-col ${textPrimaryClass}`}
                interactive
                onMouseEnter={() => setHoveredNumbers(HIGHLIGHT_MAP.diagonal[0])}
                onMouseLeave={() => setHoveredNumbers([])}
                onClick={() => openDetail(DIAGONAL_INFO[0].title, DIAGONAL_INFO[0].text)}
              >
                <span className={`text-[11px] uppercase tracking-[0.35em] ${textMutedClass}`}>диаг.</span>
                <span className="mt-1 text-3xl font-semibold">{diagonalSums[0] ?? '-'}</span>
                <span className={`text-[11px] uppercase tracking-[0.35em] ${textSubtleClass} mt-1`}>1-5-9</span>
              </SquareShell>

              {bottomPersonal.map((item) => (
                <SquareShell
                  key={item.key}
                  borderClass={squareBorderClass}
                  className={`bg-gradient-to-br from-[#6d7a76] via-[#5c6864] to-[#39413f] flex-col ${textPrimaryClass}`}
                  interactive
                  onMouseEnter={() => setHoveredNumbers([])}
                  onMouseLeave={() => setHoveredNumbers([])}
                  onClick={() =>
                    openDetail(
                      PERSONAL_DETAILS[item.type].title,
                      PERSONAL_DETAILS[item.type].text
                    )
                  }
                >
                  <span className={`text-sm uppercase tracking-[0.4em] ${textMutedClass}`}>{item.label}</span>
                  <span className="mt-1 text-3xl font-semibold">
                    {personalData?.[item.key] ?? '-'}
                  </span>
                </SquareShell>
              ))}
              <SquareShell
                borderClass={squareBorderClass}
                className="bg-gradient-to-br from-red-400 via-orange-400 to-red-500 flex-col text-white"
                interactive
                onMouseEnter={() => setHoveredNumbers([])}
                onMouseLeave={() => setHoveredNumbers([])}
                onClick={() =>
                  openDetail(
                    PERSONAL_DETAILS.challengeNumber.title,
                    PERSONAL_DETAILS.challengeNumber.text
                  )
                }
              >
                <span className="text-sm uppercase tracking-[0.4em] text-white/80">Ч/П</span>
                <span className="mt-1 text-3xl font-semibold">
                  {personalData?.challenge_number ?? '-'}
                </span>
              </SquareShell>
              <Placeholder />

              {personalCycles.filter(item => item.type !== 'challengeNumber').map((item) => (
                <SquareShell
                  key={item.key}
                  borderClass={squareBorderClass}
                  className={`bg-gradient-to-br ${
                    item.type === 'personalYear' ? 'from-yellow-400 via-orange-400 to-yellow-500' :
                    item.type === 'personalMonth' ? 'from-blue-400 via-indigo-400 to-blue-500' :
                    item.type === 'personalDay' ? 'from-green-400 via-emerald-400 to-green-500' :
                    item.type === 'personalHour' ? 'from-purple-400 via-pink-400 to-purple-500' :
                    'from-red-400 via-orange-400 to-red-500'
                  } flex-col text-white`}
                  interactive
                  onMouseEnter={() => setHoveredNumbers([])}
                  onMouseLeave={() => setHoveredNumbers([])}
                  onClick={() =>
                    openDetail(
                      PERSONAL_DETAILS[item.type].title,
                      PERSONAL_DETAILS[item.type].text
                    )
                  }
                >
                  <span className="text-sm uppercase tracking-[0.4em] text-white/80">{item.label}</span>
                  <span className="mt-1 text-3xl font-semibold">
                    {personalData?.[item.key] ?? '-'}
                  </span>
                </SquareShell>
              ))}
              <Placeholder />

              <Placeholder />
              <Placeholder />
              <Placeholder />
              <Placeholder />
              <Placeholder />
              </div>
              <div className={`border-t ${borderClass} pt-8`}>
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
                  <h2 className={`text-2xl font-semibold ${textPrimaryClass}`}>Сила планет</h2>
                  <p className={`text-sm max-w-2xl ${textMutedClass}`}>
                    Количество цифр и текущая энергетика каждой планеты. Наведите курсор на карточку, чтобы
                    подсветить соответствующую ячейку квадрата.
                  </p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {PLANET_COLUMNS.map((column, colIdx) => (
                    <div key={colIdx} className="space-y-4">
                      {column.map((num) => {
                        const { name, vedic, energyKey } = PLANET_MAP[num];
                        const count = planetCounts[num] ?? 0;
                        const energy = getPlanetEnergyValue(energyKey);
                        const colorConfig = CELL_COLORS[num] || CELL_COLORS[1];
                        const highlight = hoveredNumbers.includes(num);
                        const digits = getDigitsForNumber(num);
                        return (
                          <div
                            key={num}
                            className={`relative overflow-hidden rounded-2xl border ${borderClass} p-4 sm:p-5 transition-all duration-200 cursor-pointer ${secondaryCardBackgroundClass}`}
                            style={{
                              boxShadow: highlight
                                ? '0 12px 30px rgba(147,197,253,0.25)'
                                : '0 12px 30px rgba(15,23,42,0.18)'
                            }}
                            onMouseEnter={() => setHoveredNumbers([num])}
                            onMouseLeave={() => setHoveredNumbers([])}
                            onClick={() =>
                              handlePlanetCardClick(num, energy, {
                                count,
                                digits
                              })
                            }
                          >
                            <div
                              className="absolute inset-0 opacity-70"
                              style={{ background: colorConfig.background }}
                            />
                            <div className="relative z-10 flex flex-col gap-3">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                  <span className="text-3xl">{PLANET_SHORT[num]}</span>
                                  <div>
                                    <p className={`text-xs uppercase tracking-[0.35em] ${textSecondaryClass}`}>
                                      планета
                                    </p>
                                    <p className={`text-lg font-semibold ${textPrimaryClass}`}>
                                      {name} / {vedic}
                                    </p>
                                  </div>
                                </div>
                                <span
                                  className={`px-3 py-1 rounded-full text-xs font-semibold ${badgeBackgroundClass} ${badgeTextClass}`}
                                >
                                  № {num}
                                </span>
                              </div>
                              <div
                                className={`rounded-xl px-4 py-3 flex items-center justify-between ${
                                  isDark ? 'bg-black/25' : 'bg-white'
                                }`}
                              >
                                <span className={`text-sm ${textSecondaryClass}`}>Количество цифр</span>
                                <span className={`text-2xl font-bold ${textPrimaryClass}`}>{count}</span>
                              </div>
                              <div
                                className={`rounded-xl px-4 py-3 flex items-center justify-between ${
                                  isDark ? 'bg-black/15' : 'bg-white/80'
                                }`}
                              >
                                <span className={`text-sm ${textSecondaryClass}`}>Энергия дня</span>
                                <span className={`text-lg font-semibold ${textPrimaryClass}`}>
                                  {energy === null ? '—' : `${energy}%`}
                                </span>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ))}
                </div>
              </div>
              {energyChartData && (
                <div
                  className={`rounded-2xl border ${borderClass} ${secondaryCardBackgroundClass} p-6 md:p-8 ${chartShadowClass}`}
                >
                  <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between mb-6">
                    <div className="space-y-2">
                      <h3 className={`text-xl md:text-2xl font-semibold ${textPrimaryClass}`}>
                        Динамика энергий планет
                      </h3>
                      <p className={`text-sm max-w-2xl ${textMutedClass}`}>
                        Линия показывает изменение энергетики по дням. Выберите интересующий период, чтобы увидеть,
                        как меняются силы планет.
                      </p>
                      {energyRangeConfig?.rangeLabel && (
                        <p className={`text-xs ${textMutedClass}`}>
                          Период: <span className={textPrimaryClass}>{energyRangeConfig.rangeLabel}</span>
                        </p>
                      )}
                    </div>
                    <div className="flex flex-col gap-3 md:flex-row md:items-center">
                      <div
                        className={`flex flex-wrap items-center gap-2 rounded-2xl border ${borderClass} ${
                          isDark ? 'bg-black/20' : 'bg-white/80'
                        } px-2 py-1`}
                      >
                        <button type="button" onClick={() => setEnergyRangeMode('week')} className={rangeButtonClass('week')}>
                          Неделя
                        </button>
                        <button type="button" onClick={() => setEnergyRangeMode('month')} className={rangeButtonClass('month')}>
                          Месяц
                        </button>
                        <button type="button" onClick={() => setEnergyRangeMode('quarter')} className={rangeButtonClass('quarter')}>
                          Квартал
                        </button>
                      </div>
                      {energyRangeMode === 'week' && (
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            className={rangeNavButtonClass}
                            onClick={() => handleShiftWeek(-1)}
                            aria-label="Предыдущая неделя"
                          >
                            ‹
                          </button>
                          <input
                            type="date"
                            value={selectedWeekDate}
                            onChange={(event) => setSelectedWeekDate(event.target.value)}
                            className={rangeInputClass}
                          />
                          <button
                            type="button"
                            className={rangeNavButtonClass}
                            onClick={() => handleShiftWeek(1)}
                            aria-label="Следующая неделя"
                          >
                            ›
                          </button>
                        </div>
                      )}
                      {energyRangeMode === 'month' && (
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            className={rangeNavButtonClass}
                            onClick={() => handleShiftMonth(-1)}
                            aria-label="Предыдущий месяц"
                          >
                            ‹
                          </button>
                          <input
                            type="month"
                            value={selectedMonth}
                            onChange={(event) => setSelectedMonth(event.target.value)}
                            className={`${rangeInputClass} w-36`}
                          />
                          <button
                            type="button"
                            className={rangeNavButtonClass}
                            onClick={() => handleShiftMonth(1)}
                            aria-label="Следующий месяц"
                          >
                            ›
                          </button>
                        </div>
                      )}
                      {energyRangeMode === 'quarter' && (
                        <div className="flex flex-wrap items-center gap-2">
                          <button
                            type="button"
                            className={rangeNavButtonClass}
                            onClick={() => handleShiftQuarter(-1)}
                            aria-label="Предыдущий квартал"
                          >
                            ‹
                          </button>
                          <select
                            value={selectedQuarter.quarter}
                            onChange={(event) =>
                              setSelectedQuarter((prev) => ({
                                year: prev.year,
                                quarter: Math.min(4, Math.max(1, Number(event.target.value) || 1))
                              }))
                            }
                            className={`${rangeInputClass} w-28 pr-8`}
                          >
                            <option value={1}>I квартал</option>
                            <option value={2}>II квартал</option>
                            <option value={3}>III квартал</option>
                            <option value={4}>IV квартал</option>
                          </select>
                          <input
                            type="number"
                            inputMode="numeric"
                            min="1900"
                            max="2100"
                            value={selectedQuarter.year}
                            onChange={(event) => {
                              const yearValue = Number(event.target.value);
                              setSelectedQuarter((prev) => ({
                                quarter: prev.quarter,
                                year: Number.isNaN(yearValue) ? prev.year : yearValue
                              }));
                            }}
                            className={`${rangeInputClass} w-28`}
                          />
                          <button
                            type="button"
                            className={rangeNavButtonClass}
                            onClick={() => handleShiftQuarter(1)}
                            aria-label="Следующий квартал"
                          >
                            ›
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="h-80">
                    <Line data={energyChartData} options={energyChartOptions} />
                  </div>
                </div>
              )}
              {personalEnergy && (
                <div
                  className={`rounded-2xl border ${borderClass} ${cardBackgroundClass} p-6 md:p-8 ${chartShadowClass} space-y-6`}
                >
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div>
                      <h3 className={`text-xl md:text-2xl font-semibold ${textPrimaryClass}`}>
                        Личная энергия по дням недели
                      </h3>
                      <p className={`text-sm max-w-3xl mt-1 ${textMutedClass}`}>
                        Числовой код строится по формуле{' '}
                        <span className={textPrimaryClass}>DDMM × YYYY</span>. Первые семь цифр распределяются по дням
                        недели, начиная с дня рождения, — так мы видим, какие дни сильнее резонируют с вашей природной
                        энергией.
                      </p>
                      {personalEnergy.calculation && (
                        <div className="mt-3 space-y-2 text-sm">
                          <div
                            className={`inline-flex items-center gap-2 border ${borderClass} rounded-xl px-4 py-2 ${
                              isDark ? 'bg-white/5' : 'bg-white'
                            } ${textSecondaryClass}`}
                          >
                            <span className={`uppercase tracking-[0.3em] text-xs ${textMutedClass}`}>
                              Код
                            </span>
                            <span className={`font-semibold ${textPrimaryClass} text-lg tracking-[0.2em]`}>
                              {personalEnergy.code}
                            </span>
                          </div>
                          <div className={textMutedClass}>
                            {personalEnergy.calculation.dayMonth} × {personalEnergy.calculation.year} ={' '}
                            <span className={`${textPrimaryClass} font-semibold tracking-wide`}>
                              {personalEnergy.calculation.formattedProduct}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {personalEnergy.series.map((item) => (
                      <div
                        key={item.dayIndex}
                        className={`rounded-2xl border ${borderClass} ${inlineCardBackgroundClass} p-4 flex flex-col gap-2 transition-transform duration-200 hover:-translate-y-1 ${cardShadowClass}`}
                        style={{ boxShadow: `0 10px 22px ${item.color}26` }}
                      >
                        <div className="flex items-center justify-between">
                          <span className={`text-sm uppercase tracking-[0.3em] ${textMutedClass}`}>
                            {item.dayShort}
                          </span>
                          <span className="text-2xl" style={{ color: item.color }}>
                            {item.icon}
                          </span>
                        </div>
                        <div>
                          <p className={`text-lg font-semibold ${textPrimaryClass}`}>{item.dayLabel}</p>
                          <p className={`text-sm ${textMutedClass}`}>{item.planet}</p>
                        </div>
                        <div
                          className={`rounded-xl px-3 py-2 flex items-center justify-between ${
                            isDark ? 'bg-black/20' : 'bg-white'
                          }`}
                        >
                          <span className={`text-sm ${textMutedClass}`}>Энергия</span>
                          <span className={`text-2xl font-bold ${textPrimaryClass}`}>{item.value}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="h-72">
                    <Line
                      data={personalEnergy.chartData}
                      options={personalEnergyChartOptions}
                      plugins={[personalEnergyPointPlugin]}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <Dialog open={detail.open} onOpenChange={closeDetail}>
        <DialogContent className={`max-w-xl ${dialogClassName} ${textPrimaryClass} max-h-[80vh]`}>
          <DialogHeader>
            <DialogTitle className="text-2xl font-semibold">{detail.title}</DialogTitle>
            <DialogDescription className="sr-only">Подробная информация о нумерологическом значении</DialogDescription>
          </DialogHeader>
          <div
            className={`mt-4 space-y-4 overflow-y-auto pr-2 text-sm leading-relaxed ${textSecondaryClass}`}
            style={{ maxHeight: '60vh' }}
          >
            {detail.open&&detail.narrationId&&<NarrationPanel key={detail.narrationId} clipId={detail.narrationId}/>}
            <div className="whitespace-pre-line">{detail.text}</div>
            {detail.energy !== null && (
              <div>
                Текущий уровень энергии:{' '}
                <span className={`font-semibold ${textPrimaryClass}`}>{detail.energy}%</span>
              </div>
            )}
            {detail.loading ? (
              <div className={`flex items-center gap-2 ${textSecondaryClass}`}>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Подбираем рекомендации…</span>
              </div>
            ) : detail.advice ? (
              <div className={`whitespace-pre-line ${textPrimaryClass}`}>{detail.advice}</div>
            ) : null}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PythagoreanSquareNew;
