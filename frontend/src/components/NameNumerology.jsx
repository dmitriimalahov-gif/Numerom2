import React, { useEffect, useMemo, useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { 
  Calculator, 
  Sparkles, 
  Star, 
  Crown, 
  Heart,
  TrendingUp,
  Zap,
  Award,
  User,
  Moon,
  Sun,
  Grid3X3,
  Feather
} from 'lucide-react';
import { useAuth } from './AuthContext';

const LETTER_VALUES = {
  А: 1,
  Б: 2,
  В: 3,
  Г: 4,
  Д: 5,
  Е: 6,
  Ё: 6,
  Ж: 7,
  З: 8,
  И: 9,
  Й: 1,
  К: 2,
  Л: 3,
  М: 4,
  Н: 5,
  О: 6,
  П: 7,
  Р: 8,
  С: 9,
  Т: 1,
  У: 2,
  Ф: 3,
  Х: 4,
  Ц: 5,
  Ч: 6,
  Ш: 7,
  Щ: 8,
  Ъ: 9,
  Ы: 1,
  Ь: 2,
  Э: 3,
  Ю: 4,
  Я: 5,
  A: 1,
  B: 2,
  C: 3,
  D: 4,
  E: 5,
  F: 6,
  G: 7,
  H: 8,
  I: 9,
  J: 1,
  K: 2,
  L: 3,
  M: 4,
  N: 5,
  O: 6,
  P: 7,
  Q: 8,
  R: 9,
  S: 1,
  T: 2,
  U: 3,
  V: 4,
  W: 5,
  X: 6,
  Y: 7,
  Z: 8
};

const VOWELS = 'АЕЁИОУЫЭЮЯAEIOUY';
const MASTER_NUMBERS = new Set([11, 22]);

const NUMBER_MEANINGS = {
  1: {
    title: 'Лидерство',
    meaning: 'Независимость, инициатива, стремление к первенству. Лидерские качества и новаторство.',
    traits: ['Амбициозность', 'Самостоятельность', 'Творческий подход']
  },
  2: {
    title: 'Сотрудничество',
    meaning: 'Дипломатия, чувствительность, партнерство. Стремление к гармонии и поддержке.',
    traits: ['Тактичность', 'Чувствительность', 'Командная работа']
  },
  3: {
    title: 'Творчество',
    meaning: 'Артистизм, общительность, оптимизм. Творческое самовыражение и вдохновение.',
    traits: ['Креативность', 'Харизма', 'Позитивность']
  },
  4: {
    title: 'Стабильность',
    meaning: 'Практичность, организованность, трудолюбие. Системность и надежность.',
    traits: ['Организованность', 'Практичность', 'Упорство']
  },
  5: {
    title: 'Свобода',
    meaning: 'Любознательность, авантюризм, адаптивность. Любовь к переменам и путешествиям.',
    traits: ['Любознательность', 'Адаптивность', 'Активность']
  },
  6: {
    title: 'Гармония',
    meaning: 'Забота, ответственность, семейные ценности. Стремление к красоте и справедливости.',
    traits: ['Заботливость', 'Ответственность', 'Эстетизм']
  },
  7: {
    title: 'Мудрость',
    meaning: 'Духовность, анализ, интуиция. Поиск истины и глубокое понимание.',
    traits: ['Интуитивность', 'Аналитичность', 'Духовность']
  },
  8: {
    title: 'Власть',
    meaning: 'Амбиции, материальный успех, организаторские способности. Стремление к достижениям.',
    traits: ['Амбициозность', 'Управленческие навыки', 'Стратегичность']
  },
  9: {
    title: 'Служение',
    meaning: 'Гуманность, мудрость, великодушие. Служение людям и высшие идеалы.',
    traits: ['Альтруизм', 'Мудрость', 'Универсальность']
  },
  11: {
    title: 'Мастер-число вдохновения',
    meaning: 'Глубокая интуиция, духовное видение, способность вдохновлять других.',
    traits: ['Интуиция', 'Вдохновение', 'Высокая чувствительность']
  },
  22: {
    title: 'Мастер-строитель',
    meaning: 'Масштабное видение, практическая мудрость, воплощение идей в реальные проекты.',
    traits: ['Видение', 'Практичность', 'Масштабность']
  }
};

const THEME_CONFIG = {
  dark: {
    pageBackground: 'bg-slate-950 text-slate-100',
    overlayGradient: 'radial-gradient(1200px at 50% -10%, rgba(56,189,248,0.22), transparent 60%)',
    cardBackground: 'bg-slate-900/70',
    highlightBackground: 'bg-slate-950/60',
    cardBorder: 'border-slate-800/70',
    divider: 'border-slate-800',
    subtleText: 'text-slate-400',
    mutedText: 'text-slate-300',
    helperText: 'text-slate-400',
    chipBackground: 'bg-slate-800/80',
    chipText: 'text-slate-200',
    glass: 'bg-slate-900/60 backdrop-blur-xl border border-slate-800/80 shadow-[0_24px_64px_rgba(15,23,42,0.6)]'
  },
  light: {
    pageBackground: 'bg-slate-50 text-slate-900',
    overlayGradient: 'radial-gradient(1100px at 50% -5%, rgba(99,102,241,0.18), transparent 60%)',
    cardBackground: 'bg-white/85',
    highlightBackground: 'bg-white',
    cardBorder: 'border-slate-200',
    divider: 'border-slate-200',
    subtleText: 'text-slate-500',
    mutedText: 'text-slate-600',
    helperText: 'text-slate-500',
    chipBackground: 'bg-slate-100',
    chipText: 'text-slate-600',
    glass: 'bg-white/75 backdrop-blur-xl border border-white/80 shadow-[0_20px_50px_rgba(15,23,42,0.12)]'
  }
};

const SECTION_CONFIG = [
  {
    id: 'calculator',
    label: 'Расчёт',
    description: 'Основные вибрации имени',
    icon: Calculator
  },
  {
    id: 'analysis',
    label: 'Аналитика',
    description: 'Психологический профиль',
    icon: Sparkles
  },
  {
    id: 'compatibility',
    label: 'Совместимость',
    description: 'Партнёрские коды',
    icon: Heart
  }
];

const NUMBER_PALETTE = {
  default: {
    gradient: 'linear-gradient(135deg, rgba(15,23,42,0.85), rgba(15,23,42,0.4))',
    text: '#f8fafc',
    shadow: '0 18px 38px rgba(15,23,42,0.45)'
  },
  1: {
    gradient: 'linear-gradient(135deg, #fef3c7, #fde68a)',
    text: '#1f2937',
    shadow: '0 24px 42px rgba(253,230,138,0.35)'
  },
  2: {
    gradient: 'linear-gradient(135deg, #f8fafc, #e2e8f0)',
    text: '#1f2937',
    shadow: '0 24px 42px rgba(226,232,240,0.28)'
  },
  3: {
    gradient: 'linear-gradient(135deg, #fde68a, #fbbf24)',
    text: '#1f2937',
    shadow: '0 24px 42px rgba(251,191,36,0.32)'
  },
  4: {
    gradient: 'linear-gradient(135deg, #ead7b0, #d4b48c)',
    text: '#1f2937',
    shadow: '0 24px 42px rgba(212,180,140,0.32)'
  },
  5: {
    gradient: 'linear-gradient(135deg, #bbf7d0, #86efac)',
    text: '#14532d',
    shadow: '0 24px 42px rgba(134,239,172,0.35)'
  },
  6: {
    gradient: 'linear-gradient(135deg, #fce7f3, #fbcfe8)',
    text: '#831843',
    shadow: '0 24px 42px rgba(251,207,232,0.32)'
  },
  7: {
    gradient: 'linear-gradient(135deg, #e5e7eb, #d1d5db)',
    text: '#1f2937',
    shadow: '0 24px 42px rgba(209,213,219,0.28)'
  },
  8: {
    gradient: 'linear-gradient(135deg, #dbeafe, #bfdbfe)',
    text: '#1f2937',
    shadow: '0 24px 42px rgba(191,219,254,0.32)'
  },
  9: {
    gradient: 'linear-gradient(135deg, #fee2e2, #fecaca)',
    text: '#7f1d1d',
    shadow: '0 24px 42px rgba(254,202,202,0.34)'
  },
  11: {
    gradient: 'linear-gradient(135deg, #fef08a, #eab308)',
    text: '#422006',
    shadow: '0 24px 42px rgba(234,179,8,0.45)'
  },
  22: {
    gradient: 'linear-gradient(135deg, #bae6fd, #2563eb)',
    text: '#0f172a',
    shadow: '0 26px 44px rgba(37,99,235,0.45)'
  }
};

const NAME_COMPATIBILITY = {
  1: {
    partners: '2, 5, 7',
    tip: 'Ищите тех, кто поддержит ваш лидерский темперамент, но даст пространство для вдохновения.'
  },
  2: {
    partners: '1, 4, 8',
    tip: 'Важны надёжность и возможность делиться чувствами. Партнёр должен быть внимательным к деталям.'
  },
  3: {
    partners: '5, 6, 9',
    tip: 'Лучшие союзы рождаются там, где присутствует творчество и обмен идеями.'
  },
  4: {
    partners: '2, 6, 8',
    tip: 'Гармония приходит через устойчивость и общие задачи. Структура — ваш друг.'
  },
  5: {
    partners: '1, 3, 7',
    tip: 'Идеальны партнёры, которые разделяют вашу любовь к свободе и путешествиям.'
  },
  6: {
    partners: '2, 3, 9',
    tip: 'Отношения строятся на заботе и эстетике. Дом, созданный вместе, становится храмом.'
  },
  7: {
    partners: '5, 7, 9',
    tip: 'Взаимопонимание рождается в духовных беседах и совместных исследованиях.'
  },
  8: {
    partners: '2, 4, 6',
    tip: 'Нужны люди, ценящие вашу целеустремлённость и готовые разделить амбициозные цели.'
  },
  9: {
    partners: '3, 6, 9',
    tip: 'Вы сильнее там, где есть идея служения и общая миссия ради блага людей.'
  },
  11: {
    partners: '2, 6, 7',
    tip: 'Выберите партнёра, который поддержит вашу вдохновляющую миссию и разделит высокие идеалы.'
  },
  22: {
    partners: '4, 6, 8',
    tip: 'Вы создаёте большие структуры — ищите тех, кто поможет удерживать баланс и порядок.'
  }
};

const SOUL_COMPATIBILITY = {
  odd: {
    focus: 'Нечётные числа души тянутся к искренности, вдохновению и эмоциональной честности.',
    partners: 'Лучшие созвучия: 1, 3, 5, 7, 9.'
  },
  even: {
    focus: 'Чётные числа души ищут надёжность, заботу и устойчивую эмоциональную связь.',
    partners: 'Лучшие созвучия: 2, 4, 6, 8.'
  }
};

const PERSONALITY_COMPATIBILITY = {
  light: {
    focus: 'Вы привлекаете людей ясностью, оптимизмом и инициативой. Поддерживайте динамику общения.',
    partners: 'Яркий резонанс: 1, 3, 5, 7.'
  },
  deep: {
    focus: 'Ваше обаяние в глубине и надёжности. Люди ценят вашу собранность и логику.',
    partners: 'Гармония чаще с 2, 4, 6, 8.'
  }
};

const reduceToSingleDigit = (value) => {
  let num = Number(value) || 0;
  while (num > 9 && !MASTER_NUMBERS.has(num)) {
    num = String(num)
      .split('')
      .reduce((sum, digit) => sum + Number(digit), 0);
  }
  return num;
};

const calculateNameNumber = (name) => {
  if (!name) return 0;
  const chars = name.toUpperCase().split('');
  const total = chars.reduce((sum, char) => sum + (LETTER_VALUES[char] || 0), 0);
  return reduceToSingleDigit(total);
};

const extractVowels = (name) =>
  name
    .toUpperCase()
    .split('')
    .filter((char) => VOWELS.includes(char));

const extractConsonants = (name) =>
  name
    .toUpperCase()
    .split('')
    .filter((char) => LETTER_VALUES[char] && !VOWELS.includes(char));

const buildNumberPalette = (number) => NUMBER_PALETTE[number] || NUMBER_PALETTE.default;

const formatList = (items) => items.join(', ');

const NameNumerology = () => {
  const { user } = useAuth();
  const [firstName, setFirstName] = useState(user?.name?.split(' ')[0] || '');
  const [lastName, setLastName] = useState(user?.name?.split(' ')[1] || '');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeSection, setActiveSection] = useState('calculator');
  const [theme, setTheme] = useState(() => {
    if (typeof window === 'undefined') return 'dark';
    return localStorage.getItem('name-numerology-theme') === 'light' ? 'light' : 'dark';
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;
    localStorage.setItem('name-numerology-theme', theme);
  }, [theme]);

  const themeConfig = THEME_CONFIG[theme];
  const toggleTheme = () => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));

  const handleCalculate = () => {
    if (!firstName && !lastName) return;
    setLoading(true);

    const fullName = `${firstName} ${lastName}`.trim();
    const firstNameNumber = calculateNameNumber(firstName);
    const lastNameNumber = calculateNameNumber(lastName);
    const fullNameNumber = calculateNameNumber(fullName);
    
    const vowels = [...extractVowels(firstName), ...extractVowels(lastName)];
    const consonants = [...extractConsonants(firstName), ...extractConsonants(lastName)];

    const soulNumber = reduceToSingleDigit(
      vowels.reduce((sum, char) => sum + (LETTER_VALUES[char] || 0), 0)
    );

    const personalityNumber = reduceToSingleDigit(
      consonants.reduce((sum, char) => sum + (LETTER_VALUES[char] || 0), 0)
    );

    const birthSum = user?.birth_date
      ? user.birth_date
          .replace(/[.-]/g, '')
          .split('')
          .reduce((sum, digit) => sum + Number(digit), 0)
      : 0;

    const lifePathNumber = reduceToSingleDigit(birthSum);
    const maturityNumber = reduceToSingleDigit(fullNameNumber + lifePathNumber);

    const balanceNumber = reduceToSingleDigit(
      (LETTER_VALUES[firstName?.charAt(0)?.toUpperCase()] || 0) +
        (LETTER_VALUES[lastName?.charAt(0)?.toUpperCase()] || 0)
    );

    const letterBreakdown = {
      first: firstName.toUpperCase().split('').map((letter) => ({
        letter,
        value: LETTER_VALUES[letter] || 0
      })),
      last: lastName.toUpperCase().split('').map((letter) => ({
        letter,
        value: LETTER_VALUES[letter] || 0
      }))
    };

    setResults({
      firstName,
      lastName,
      fullName,
      firstNameNumber,
      lastNameNumber,
      fullNameNumber,
      soulNumber,
      personalityNumber,
      maturityNumber,
      lifePathNumber,
      balanceNumber,
      vowels,
      consonants,
      letterBreakdown
    });

    setLoading(false);
  };

  const coreNumbers = useMemo(() => {
    if (!results) return [];
    return [
      {
        key: 'first-name',
        label: 'Число имени',
        value: results.firstNameNumber,
        subtitle: results.firstName || '—',
        description: 'Личная инициатива и способ самопрезентации.'
      },
      {
        key: 'last-name',
        label: 'Число фамилии',
        value: results.lastNameNumber,
        subtitle: results.lastName || '—',
        description: 'Родовая опора и наследуемые качества.'
      },
      {
        key: 'full-name',
        label: 'Число полного имени',
        value: results.fullNameNumber,
        subtitle: results.fullName,
        description: 'Главная вибрация имени и имиджа.'
      }
    ];
  }, [results]);

  const deepNumbers = useMemo(() => {
    if (!results) return [];
    return [
      {
        key: 'soul',
        label: 'Число души',
        value: results.soulNumber,
        subtitle: 'Внутренние желания и истинные мотивы.'
      },
      {
        key: 'personality',
        label: 'Число личности',
        value: results.personalityNumber,
        subtitle: 'Внешний образ и первое впечатление.'
      },
      {
        key: 'maturity',
        label: 'Число зрелости',
        value: results.maturityNumber,
        subtitle: 'Раскрытие потенциала с опытом.'
      },
      {
        key: 'balance',
        label: 'Число баланса',
        value: results.balanceNumber,
        subtitle: 'Способ восстановить гармонию в сложных ситуациях.'
      },
      {
        key: 'life-path',
        label: 'Число жизненного пути',
        value: results.lifePathNumber,
        subtitle: 'Энергия даты рождения в связке с именем.'
      }
    ];
  }, [results]);

  const renderNumberCard = (item) => {
    const palette = buildNumberPalette(item.value);
    const meaning = NUMBER_MEANINGS[item.value];
    const displayValue = item.value || '—';

    return (
      <div
        key={item.key}
        className="group relative overflow-hidden rounded-2xl border transition-all duration-300 hover:-translate-y-1.5"
        style={{
          background: palette.gradient,
          color: palette.text,
          boxShadow: palette.shadow
        }}
      >
        <div className="absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
             style={{ background: 'linear-gradient(140deg, rgba(15,23,42,0.08), rgba(255,255,255,0.08))' }}
        />
        <div className="relative z-10 flex flex-col gap-3 p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-[0.35em] opacity-80">
              {item.label}
            </span>
            <Sparkles className="h-4 w-4 opacity-60" />
            </div>
          <div className="text-4xl font-semibold leading-none">{displayValue}</div>
          {item.subtitle && (
            <p className="text-sm font-medium opacity-80">{item.subtitle}</p>
          )}
          {item.description && (
            <p className="text-xs opacity-80 leading-relaxed">{item.description}</p>
          )}
          {meaning && (
            <div className="flex flex-wrap gap-2 pt-2 text-[11px] uppercase tracking-[0.2em] opacity-80">
              {meaning.traits.slice(0, 3).map((trait) => (
                <span
                  key={trait}
                  className="rounded-full bg-black/10 px-3 py-1 font-semibold"
                  style={{ color: palette.text }}
                >
                  {trait}
                </span>
              ))}
            </div>
          )}
          </div>
                </div>
    );
  };

  const renderOverviewSection = () => {
    if (!results) {
      return (
        <div className={`rounded-3xl ${themeConfig.glass} p-10 text-center`}>
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/15 text-emerald-300">
            <Grid3X3 className="h-7 w-7" />
                </div>
          <h3 className="mt-6 text-2xl font-semibold">Введите имя, чтобы раскрыть его вибрации</h3>
          <p className={`mt-3 text-sm ${themeConfig.helperText}`}>
            Имя — это ваш личный код. Заполните поля выше и нажмите «Рассчитать».
          </p>
        </div>
      );
    }

    const fullNameMeaning = NUMBER_MEANINGS[results.fullNameNumber];

    return (
      <div className="space-y-10">
        <div className={`relative overflow-hidden rounded-3xl ${themeConfig.glass} p-8 md:p-12`}>
          <div
            className="absolute inset-0 opacity-70"
            style={{
              background:
                'radial-gradient(circle at 10% 10%, rgba(96,165,250,0.3), transparent 55%), radial-gradient(circle at 90% 20%, rgba(244,114,182,0.35), transparent 60%)'
            }}
          />
          <div className="relative z-10 flex flex-col gap-8 md:flex-row md:items-start md:justify-between">
            <div className="space-y-6">
              <p className={`text-xs font-semibold uppercase tracking-[0.4em] ${themeConfig.subtleText}`}>
                Личная вибрация имени
              </p>
              <h2 className="text-3xl md:text-4xl font-semibold leading-tight">
                {results.fullName || '—'}
              </h2>
              <p className={`max-w-2xl text-sm md:text-base leading-relaxed ${themeConfig.mutedText}`}>
                {fullNameMeaning
                  ? `${fullNameMeaning.meaning} Это основная частота вашего имени. Совмещая её с датой рождения, вы выстраиваете уникальную траекторию роста.`
                  : 'Это основная частота вашего имени. Совмещая её с датой рождения, вы выстраиваете уникальную траекторию роста.'}
              </p>
              <div className="flex flex-wrap gap-3">
                {fullNameMeaning?.traits.map((trait) => (
                  <Badge key={trait} variant="secondary" className="text-xs uppercase tracking-[0.25em]">
                    {trait}
                  </Badge>
                ))}
                </div>
              </div>
            <div className="flex w-full max-w-sm flex-col gap-4">
              <div className="rounded-2xl bg-white/5 p-4 text-center shadow-inner shadow-black/20">
                <p className="text-xs uppercase tracking-[0.35em] opacity-70">Число полного имени</p>
                <p className="mt-3 text-5xl font-semibold">{results.fullNameNumber}</p>
                </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-xl bg-white/5 p-4 text-center">
                  <p className="text-xs uppercase tracking-[0.35em] opacity-70">Число души</p>
                  <p className="mt-2 text-2xl font-semibold">{results.soulNumber}</p>
                </div>
                <div className="rounded-xl bg-white/5 p-4 text-center">
                  <p className="text-xs uppercase tracking-[0.35em] opacity-70">Число личности</p>
                  <p className="mt-2 text-2xl font-semibold">{results.personalityNumber}</p>
                </div>
              </div>
              <div className="rounded-2xl bg-gradient-to-br from-emerald-400/15 to-sky-400/10 p-4 text-sm leading-relaxed">
                <p className="font-semibold uppercase tracking-[0.25em] text-emerald-200">Совет</p>
                <p className="mt-2 text-emerald-100">
                  Поддерживайте звучание имени, произносите его осознанно и соединяйте с дыхательными практиками — так вы усиливаете свою личную вибрацию.
                </p>
              </div>
            </div>
          </div>
                </div>

        <div className="space-y-5">
          <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
            <div>
              <h3 className="text-2xl font-semibold">Основные коды имени</h3>
              <p className={`text-sm ${themeConfig.helperText}`}>
                Каждый блок раскрывает конкретную грань вашей личной матрицы имени.
              </p>
                </div>
              </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">{coreNumbers.map(renderNumberCard)}</div>
    </div>

        <div className="space-y-5">
          <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
            <div>
              <h3 className="text-2xl font-semibold">Глубинные вибрации</h3>
              <p className={`text-sm ${themeConfig.helperText}`}>
                Эти числа показывают эмоциональную матрицу, зрелость и баланс имени.
                    </p>
                  </div>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {deepNumbers.map((item) => (
              <div
                key={item.key}
                className={`rounded-2xl ${themeConfig.glass} p-6 transition-all duration-300 hover:-translate-y-1.5`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className={`text-xs uppercase tracking-[0.4em] ${themeConfig.subtleText}`}>{item.label}</p>
                    <p className="mt-3 text-4xl font-semibold">{item.value || '—'}</p>
                  </div>
                  <Crown className="h-5 w-5 opacity-60" />
                </div>
                <p className={`mt-4 text-sm leading-relaxed ${themeConfig.mutedText}`}>{item.subtitle}</p>
                {NUMBER_MEANINGS[item.value] && (
                  <div className="mt-4 flex flex-wrap gap-2 text-xs">
                    {NUMBER_MEANINGS[item.value].traits.map((trait) => (
                      <span
                        key={trait}
                        className={`rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.3em] ${themeConfig.chipBackground} ${themeConfig.chipText}`}
                      >
                          {trait}
                      </span>
                      ))}
                    </div>
                )}
                  </div>
            ))}
                </div>
        </div>

        <div className={`rounded-3xl ${themeConfig.glass} p-8 md:p-10`}>
          <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-emerald-400/20 p-3 text-emerald-200">
                <Feather className="h-6 w-6" />
                  </div>
                  <div>
                <h3 className="text-xl font-semibold">Буквенная структура имени</h3>
                <p className={`text-sm ${themeConfig.helperText}`}>
                  Каждая буква добавляет собственную частоту. Следите за тем, какие звуки звучат чаще всего.
                </p>
                    </div>
                  </div>
          </div>

          <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2">
              <div className="space-y-4">
              <h4 className="text-base font-semibold">Имя: {results.firstName || '—'}</h4>
                  <div className="flex flex-wrap gap-2">
                {results.letterBreakdown.first.length ? (
                  results.letterBreakdown.first.map((item, index) => (
                    <div
                      key={`first-${item.letter}-${index}`}
                      className="min-w-[56px] rounded-xl bg-white/5 px-3 py-2 text-center shadow-inner shadow-black/20"
                    >
                      <div className="text-lg font-semibold">{item.letter}</div>
                      <div className="text-xs opacity-70">{item.value}</div>
                      </div>
                  ))
                ) : (
                  <span className={`text-sm ${themeConfig.helperText}`}>Добавьте имя для анализа букв.</span>
                )}
                {results.firstNameNumber ? (
                  <div className="min-w-[72px] rounded-xl bg-emerald-500/15 px-3 py-2 text-center">
                    <div className="text-lg font-semibold text-emerald-200">Σ</div>
                    <div className="text-xs font-semibold text-emerald-200">{results.firstNameNumber}</div>
                    </div>
                ) : null}
                  </div>
                </div>

            <div className="space-y-4">
              <h4 className="text-base font-semibold">Фамилия: {results.lastName || '—'}</h4>
                  <div className="flex flex-wrap gap-2">
                {results.letterBreakdown.last.length ? (
                  results.letterBreakdown.last.map((item, index) => (
                    <div
                      key={`last-${item.letter}-${index}`}
                      className="min-w-[56px] rounded-xl bg-white/5 px-3 py-2 text-center shadow-inner shadow-black/20"
                    >
                      <div className="text-lg font-semibold">{item.letter}</div>
                      <div className="text-xs opacity-70">{item.value}</div>
                      </div>
                  ))
                ) : (
                  <span className={`text-sm ${themeConfig.helperText}`}>Добавьте фамилию, чтобы увидеть полный код.</span>
                )}
                {results.lastNameNumber ? (
                  <div className="min-w-[72px] rounded-xl bg-sky-500/15 px-3 py-2 text-center">
                    <div className="text-lg font-semibold text-sky-200">Σ</div>
                    <div className="text-xs font-semibold text-sky-200">{results.lastNameNumber}</div>
                  </div>
                ) : null}
                    </div>
                  </div>
                </div>

          <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="rounded-2xl bg-gradient-to-br from-rose-500/10 to-pink-500/10 p-4 text-sm">
              <p className="font-semibold uppercase tracking-[0.35em] text-rose-100">Гласные</p>
              <p className="mt-2 text-rose-50">{results.vowels.length ? formatList(results.vowels) : '—'}</p>
              <Badge className="mt-4 w-fit bg-rose-500/20 text-rose-100">Число души: {results.soulNumber}</Badge>
            </div>
            <div className="rounded-2xl bg-gradient-to-br from-sky-500/10 to-indigo-500/10 p-4 text-sm">
              <p className="font-semibold uppercase tracking-[0.35em] text-sky-100">Согласные</p>
              <p className="mt-2 text-sky-50">{results.consonants.length ? formatList(results.consonants) : '—'}</p>
              <Badge className="mt-4 w-fit bg-sky-500/20 text-sky-100">Число личности: {results.personalityNumber}</Badge>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderAnalysisSection = () => {
    if (!results) {
      return (
        <div className={`rounded-3xl ${themeConfig.glass} p-10 text-center`}>
          <Sparkles className="mx-auto h-10 w-10 opacity-60" />
          <h3 className="mt-6 text-2xl font-semibold">Сначала рассчитайте имя</h3>
          <p className={`mt-3 text-sm ${themeConfig.helperText}`}>
            На вкладке «Расчёт» введите имя и фамилию — после этого откроется расширенный анализ.
          </p>
        </div>
      );
    }

    const analysisTargets = [
      {
        id: 'full-name-number',
        label: 'Число полного имени',
        value: results.fullNameNumber,
        icon: Crown,
        description:
          NUMBER_MEANINGS[results.fullNameNumber]?.meaning || 'Главная вибрация, описывающая общественный образ и предназначение имени.'
      },
      {
        id: 'soul-number',
        label: 'Число души',
        value: results.soulNumber,
        icon: Heart,
        description:
          NUMBER_MEANINGS[results.soulNumber]?.meaning || 'Уровень внутренней мотивации и эмоциональной природы.'
      },
      {
        id: 'personality-number',
        label: 'Число личности',
        value: results.personalityNumber,
        icon: Star,
        description:
          NUMBER_MEANINGS[results.personalityNumber]?.meaning || 'То, что видят окружающие: манеры, интонации, стиль общения.'
      },
      {
        id: 'maturity-number',
        label: 'Число зрелости',
        value: results.maturityNumber,
        icon: TrendingUp,
        description:
          NUMBER_MEANINGS[results.maturityNumber]?.meaning || 'Направление, в котором имя раскрывает вас во взрослой жизни.'
      },
      {
        id: 'balance-number',
        label: 'Число баланса',
        value: results.balanceNumber,
        icon: Zap,
        description:
          NUMBER_MEANINGS[results.balanceNumber]?.meaning || 'Подсказка, как быстрее возвращаться в ресурсное состояние.'
      },
      {
        id: 'life-path-number',
        label: 'Число жизненного пути',
        value: results.lifePathNumber,
        icon: Award,
        description:
          NUMBER_MEANINGS[results.lifePathNumber]?.meaning || 'Синергия имени и даты рождения: как вы проживаете свою миссию.'
      }
    ];

    return (
      <div className="space-y-10">
        <div className={`rounded-3xl ${themeConfig.glass} p-8 md:p-10`}>
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                    <div>
              <p className={`text-xs uppercase tracking-[0.4em] ${themeConfig.subtleText}`}>Психология имени</p>
              <h3 className="mt-2 text-3xl font-semibold">Глубинный профиль</h3>
              <p className={`mt-3 max-w-3xl text-sm leading-relaxed ${themeConfig.mutedText}`}>
                Ниже — разбор ключевых чисел. Изучайте сильные стороны, наблюдайте за тенями и интегрируйте подсказки в повседневность.
              </p>
                    </div>
                  </div>
          <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2">
            {analysisTargets.map((target) => {
              const palette = buildNumberPalette(target.value);
              const Icon = target.icon;
              const meaning = NUMBER_MEANINGS[target.value];

              return (
                <div
                  key={target.id}
                  className="relative overflow-hidden rounded-2xl border border-white/10 p-6 transition-all duration-300 hover:-translate-y-1.5"
                  style={{ background: palette.gradient, color: palette.text, boxShadow: palette.shadow }}
                >
                  <div className="absolute inset-0 opacity-0 transition-opacity duration-300 hover:opacity-20"
                       style={{ background: 'linear-gradient(160deg, rgba(255,255,255,0.2), transparent)' }}
                  />
                  <div className="relative z-10 flex flex-col gap-4">
                    <div className="flex items-center justify-between">
                    <div>
                        <p className="text-xs uppercase tracking-[0.4em] opacity-70">{target.label}</p>
                        <p className="mt-3 text-4xl font-semibold">{target.value || '—'}</p>
                    </div>
                      <div className="rounded-2xl bg-black/15 p-3">
                        <Icon className="h-5 w-5" />
                  </div>
                </div>
                    <p className="text-sm leading-relaxed opacity-90">{target.description}</p>
                    {meaning && (
                      <div className="flex flex-wrap gap-2 text-xs">
                        {meaning.traits.map((trait) => (
                          <span key={trait} className="rounded-full bg-black/20 px-3 py-1 uppercase tracking-[0.25em]">
                            {trait}
                          </span>
                        ))}
              </div>
                    )}
                  </div>
    </div>
  );
            })}
          </div>
        </div>
      </div>
    );
  };

  const renderCompatibilitySection = () => {
    if (!results) {
      return (
        <div className={`rounded-3xl ${themeConfig.glass} p-10 text-center`}>
          <Heart className="mx-auto h-10 w-10 opacity-60" />
          <h3 className="mt-6 text-2xl font-semibold">Рассчитайте имя, чтобы увидеть совместимость</h3>
          <p className={`mt-3 text-sm ${themeConfig.helperText}`}>
            После расчёта появятся подсказки по партнёрам, командам и людям, с которыми ваше имя резонирует сильнее всего.
          </p>
        </div>
      );
    }

    const nameData = NAME_COMPATIBILITY[results.fullNameNumber] || {
      partners: 'зависит от комбинации чисел',
      tip: 'Сформируйте базовую вибрацию имени и слушайте интуицию при выборе окружения.'
    };

    const soulKey = results.soulNumber % 2 === 0 ? 'even' : 'odd';
    const soulData = SOUL_COMPATIBILITY[soulKey];
    const personalityKey = [1, 3, 5, 7, 9].includes(results.personalityNumber) ? 'light' : 'deep';
    const personalityData = PERSONALITY_COMPATIBILITY[personalityKey];

    return (
      <div className="space-y-10">
        <div className={`rounded-3xl ${themeConfig.glass} p-8 md:p-10`}>
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p className={`text-xs uppercase tracking-[0.4em] ${themeConfig.subtleText}`}>Партнёрские резонансы</p>
              <h3 className="mt-2 text-3xl font-semibold">С кем имя звучит в унисон</h3>
              <p className={`mt-3 max-w-3xl text-sm leading-relaxed ${themeConfig.mutedText}`}>
                Используйте эти подсказки, когда выбираете наставников, партнёров или формируете команду. Это вибрационный ориентир, а не жёсткое правило.
              </p>
                  </div>
                </div>

          <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="rounded-2xl bg-gradient-to-br from-sky-500/15 to-indigo-500/10 p-6">
              <div className="flex items-center gap-3 text-sky-100">
                <div className="rounded-2xl bg-sky-500/25 p-3">
                  <Crown className="h-5 w-5" />
                  </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.4em] opacity-80">Число имени</p>
                  <p className="text-2xl font-semibold">{results.fullNameNumber}</p>
                </div>
              </div>
              <p className="mt-4 text-sm text-sky-50">
                Лучшие партнёры: {nameData.partners}.
              </p>
              <p className="mt-3 text-sm text-sky-100/80 leading-relaxed">{nameData.tip}</p>
                </div>

            <div className="rounded-2xl bg-gradient-to-br from-rose-500/15 to-pink-500/10 p-6">
              <div className="flex items-center gap-3 text-rose-100">
                <div className="rounded-2xl bg-rose-500/25 p-3">
                  <Heart className="h-5 w-5" />
                  </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.4em] opacity-80">Число души</p>
                  <p className="text-2xl font-semibold">{results.soulNumber}</p>
                </div>
              </div>
              <p className="mt-4 text-sm text-rose-50">{soulData.focus}</p>
              <p className="mt-3 text-sm text-rose-100/80 leading-relaxed">{soulData.partners}</p>
            </div>

            <div className="rounded-2xl bg-gradient-to-br from-emerald-500/15 to-teal-500/10 p-6">
              <div className="flex items-center gap-3 text-emerald-100">
                <div className="rounded-2xl bg-emerald-500/25 p-3">
                  <Star className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.4em] opacity-80">Число личности</p>
                  <p className="text-2xl font-semibold">{results.personalityNumber}</p>
                </div>
              </div>
              <p className="mt-4 text-sm text-emerald-50">{personalityData.focus}</p>
              <p className="mt-3 text-sm text-emerald-100/80 leading-relaxed">{personalityData.partners}</p>
            </div>
          </div>
        </div>

        <div className={`rounded-3xl ${themeConfig.glass} p-8 md:p-10`}>
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <h3 className="text-xl font-semibold">Практика для усиления имени</h3>
            <Badge className="bg-emerald-500/20 text-emerald-100">3–5 минут ежедневно</Badge>
          </div>
          <div className={`mt-6 grid grid-cols-1 gap-5 md:grid-cols-3 text-sm ${themeConfig.mutedText}`}>
            <div>
              <p className="font-semibold uppercase tracking-[0.35em]">1. Осознанное произнесение</p>
              <p className="mt-2 leading-relaxed">
                Произносите имя вслух на вдохе и выдохе. Слушайте, как меняется тембр. Это активирует вибрацию полного имени.
              </p>
            </div>
            <div>
              <p className="font-semibold uppercase tracking-[0.35em]">2. Резонанс с душой</p>
              <p className="mt-2 leading-relaxed">
                Шёпотом пропойте гласные — так вы подключаетесь к числу души. Следите за ощущениями в грудном центре.
              </p>
            </div>
            <div>
              <p className="font-semibold uppercase tracking-[0.35em]">3. Закрепление образа</p>
              <p className="mt-2 leading-relaxed">
                Напишите имя красивым шрифтом 9 раз. За каждым повтором благодарите себя. Это усиливает число личности и баланс.
              </p>
            </div>
          </div>
        </div>
    </div>
  );
  };

  const renderActiveSection = () => {
    switch (activeSection) {
      case 'calculator':
        return renderOverviewSection();
      case 'analysis':
        return renderAnalysisSection();
      case 'compatibility':
        return renderCompatibilitySection();
      default:
        return null;
    }
  };

  const SectionSwitcher = () => (
    <div className={`flex flex-col gap-3 rounded-3xl ${themeConfig.glass} p-3 md:flex-row`}>
      {SECTION_CONFIG.map(({ id, label, description, icon: Icon }) => {
        const isActive = activeSection === id;
  return (
          <button
            key={id}
            type="button"
            onClick={() => setActiveSection(id)}
            className={`flex flex-1 items-center justify-between gap-4 rounded-2xl border px-5 py-4 text-left transition-all duration-300 ${
              isActive
                ? 'border-emerald-400/60 bg-emerald-500/10 shadow-[0_12px_30px_rgba(16,185,129,0.25)]'
                : 'border-transparent hover:border-emerald-400/30 hover:bg-emerald-500/5'
            }`}
          >
            <div>
              <p className="text-sm font-semibold">{label}</p>
              <p className={`text-xs ${themeConfig.helperText}`}>{description}</p>
            </div>
            <div
              className={`rounded-xl p-2 ${
                isActive ? 'bg-emerald-500/20 text-emerald-200' : 'bg-slate-800/40 text-slate-300'
              }`}
            >
              <Icon className="h-4 w-4" />
            </div>
          </button>
        );
      })}
    </div>
  );

  return (
    <div className={`relative min-h-screen overflow-hidden ${themeConfig.pageBackground}`}>
      <div className="pointer-events-none absolute inset-0" style={{ background: themeConfig.overlayGradient }} />
      <div className="relative z-10 mx-auto flex min-h-screen max-w-6xl flex-col gap-8 px-4 py-12 md:py-16">
        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
          <div className="space-y-4">
            <p className={`text-xs uppercase tracking-[0.4em] ${themeConfig.subtleText}`}>Личный код</p>
            <h1 className="text-3xl md:text-4xl font-semibold leading-tight">
              Нумерология имени <span className="text-emerald-400">Numerom</span>
            </h1>
            <p className={`max-w-2xl text-sm md:text-base leading-relaxed ${themeConfig.mutedText}`}>
              Изучите скрытую архитектуру своего имени: от базовых чисел до энергетической совместимости. Все расчёты строятся на вашей персональной вибрации.
            </p>
                </div>
          <div className="flex items-center gap-4 self-start rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm shadow-lg shadow-black/20">
            <User className="h-4 w-4" />
            <span>{user?.name || 'Имя не указано'}</span>
            <span className={`text-xs ${themeConfig.helperText}`}>{user?.birth_date || 'Дата не указана'}</span>
                </div>
                </div>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className={`text-xs ${themeConfig.helperText}`}>
            Используйте полные имя и фамилию. Для иностранных имен сохраните оригинальное написание латиницей.
              </div>
          <button
            type="button"
            onClick={toggleTheme}
            className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm transition-all duration-200 hover:bg-white/10"
          >
            {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            <span>{theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}</span>
          </button>
                </div>

        <div className={`rounded-3xl ${themeConfig.glass} p-7 md:p-8`}>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div className="space-y-3">
              <Label htmlFor="firstName" className="text-sm font-semibold uppercase tracking-[0.35em]">
                Имя
              </Label>
              <Input
                id="firstName"
                type="text"
                placeholder="Введите ваше имя"
                value={firstName}
                onChange={(event) => setFirstName(event.target.value)}
                className="h-12 rounded-xl border border-white/10 bg-white/5 px-4 text-base backdrop-blur-sm focus-visible:ring-2 focus-visible:ring-emerald-400"
              />
                </div>
            <div className="space-y-3">
              <Label htmlFor="lastName" className="text-sm font-semibold uppercase tracking-[0.35em]">
                Фамилия
              </Label>
              <Input
                id="lastName"
                type="text"
                placeholder="Введите вашу фамилию"
                value={lastName}
                onChange={(event) => setLastName(event.target.value)}
                className="h-12 rounded-xl border border-white/10 bg-white/5 px-4 text-base backdrop-blur-sm focus-visible:ring-2 focus-visible:ring-emerald-400"
              />
                </div>
              </div>

          <Button
            onClick={handleCalculate}
            disabled={loading || (!firstName && !lastName)}
            className="mt-6 w-full rounded-2xl bg-gradient-to-r from-emerald-500 via-teal-400 to-sky-500 py-5 text-base font-semibold shadow-[0_18px_38px_rgba(16,185,129,0.35)] transition-all duration-200 hover:brightness-110"
          >
            <Calculator className="mr-2 h-4 w-4" />
            {loading ? 'Рассчитываем...' : 'Рассчитать нумерологию имени'}
          </Button>
            </div>

        <SectionSwitcher />

        <div className="pb-12">{renderActiveSection()}</div>
      </div>
    </div>
  );
};

export default NameNumerology;