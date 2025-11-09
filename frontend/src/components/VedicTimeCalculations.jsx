import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { useAuth } from './AuthContext';
import { getPlanetColor, tintHex, shadeHex, withAlpha } from './constants/colors';
import {
  Loader2,
  Sun,
  Moon,
  Calendar,
  MapPin,
  RefreshCcw,
  Clock3,
  Sparkles,
  AlertTriangle,
  CheckCircle2
} from 'lucide-react';
import { getApiBaseUrl } from '../utils/backendUrl';

const THEME_CONFIG = {
  dark: {
    pageBackground: 'bg-[#0f1214] text-slate-100',
    overlayGradient:
      'radial-gradient(1400px at 50% -5%, rgba(56,189,248,0.18), transparent 65%), radial-gradient(900px at 80% 0%, rgba(94,234,212,0.12), transparent 70%)',
    cardBorder: 'border-white/10',
    divider: 'border-white/10',
    mutedText: 'text-slate-300',
    subtleText: 'text-slate-400',
    chipBackground: 'bg-white/10 text-slate-100',
    highlightGreen: 'bg-emerald-400/15 text-emerald-100 border-emerald-500/40',
    highlightRed: 'bg-rose-400/15 text-rose-100 border-rose-500/40',
    highlightBlue: 'bg-sky-400/15 text-sky-100 border-sky-500/40',
    highlightBrown: 'bg-amber-400/20 text-amber-100 border-amber-500/40',
    highlightGray: 'bg-slate-400/20 text-slate-100 border-slate-500/40',
    glass: 'bg-white/5 backdrop-blur-xl border border-white/10 shadow-[0_20px_60px_rgba(15,23,42,0.45)]',
    surface: 'bg-white/4 border border-white/10'
  },
  light: {
    pageBackground: 'bg-[#f6f9fc] text-slate-900',
    overlayGradient:
      'radial-gradient(1200px at 50% -5%, rgba(129,140,248,0.18), transparent 70%), radial-gradient(900px at 85% 5%, rgba(45,212,191,0.14), transparent 75%)',
    cardBorder: 'border-white/70',
    divider: 'border-slate-200',
    mutedText: 'text-slate-600',
    subtleText: 'text-slate-500',
    chipBackground: 'bg-slate-100 text-slate-700',
    highlightGreen: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    highlightRed: 'bg-rose-100 text-rose-700 border-rose-200',
    highlightBlue: 'bg-sky-100 text-sky-700 border-sky-200',
    highlightBrown: 'bg-amber-100 text-amber-700 border-amber-200',
    highlightGray: 'bg-slate-100 text-slate-700 border-slate-200',
    glass: 'bg-white/70 backdrop-blur-xl border border-white/80 shadow-[0_20px_55px_rgba(148,163,184,0.25)]',
    surface: 'bg-white border border-slate-200'
  }
};

const WEEKDAY_MANTRAS = {
  воскресенье: {
    planet: 'Солнце',
    mantra: 'ॐ सूर्याय नमः',
    transliteration: 'Om Sūryāya Namaḥ',
    description: 'Укрепляет внутренний свет, уверенность и лидерские качества.'
  },
  sunday: {
    planet: 'Sun',
    mantra: 'ॐ सूर्याय नमः',
    transliteration: 'Om Sūryāya Namaḥ',
    description: 'Strengthens vitality, confidence, and leadership.'
  },
  понедельник: {
    planet: 'Луна',
    mantra: 'ॐ चंद्राय नमः',
    transliteration: 'Om Chandrāya Namaḥ',
    description: 'Гармонизирует эмоции, развивает интуицию и мягкость.'
  },
  monday: {
    planet: 'Moon',
    mantra: 'ॐ चंद्राय नमः',
    transliteration: 'Om Chandrāya Namaḥ',
    description: 'Harmonises emotions, nurtures intuition and empathy.'
  },
  вторник: {
    planet: 'Марс',
    mantra: 'ॐ मंगलाय नमः',
    transliteration: 'Om Maṅgalāya Namaḥ',
    description: 'Наполняет решительностью, смелостью и силой действий.'
  },
  tuesday: {
    planet: 'Mars',
    mantra: 'ॐ मंगलाय नमः',
    transliteration: 'Om Maṅgalāya Namaḥ',
    description: 'Infuses courage, determination, and drive.'
  },
  среда: {
    planet: 'Меркурий',
    mantra: 'ॐ बुधाय नमः',
    transliteration: 'Om Budhāya Namaḥ',
    description: 'Активирует интеллект, коммуникацию и гибкое мышление.'
  },
  wednesday: {
    planet: 'Mercury',
    mantra: 'ॐ बुधाय नमः',
    transliteration: 'Om Budhāya Namaḥ',
    description: 'Sharpens intellect, communication, and adaptability.'
  },
  четверг: {
    planet: 'Юпитер',
    mantra: 'ॐ बृहस्पतये नमः',
    transliteration: 'Om Bṛhaspataye Namaḥ',
    description: 'Раскрывает мудрость, духовность и наставнические качества.'
  },
  thursday: {
    planet: 'Jupiter',
    mantra: 'ॐ बृहस्पतये नमः',
    transliteration: 'Om Bṛhaspataye Namaḥ',
    description: 'Expands wisdom, spirituality, and guidance.'
  },
  пятница: {
    planet: 'Венера',
    mantra: 'ॐ शुक्राय नमः',
    transliteration: 'Om Śukrāya Namaḥ',
    description: 'Притягивает гармонию, любовь и творческое вдохновение.'
  },
  friday: {
    planet: 'Venus',
    mantra: 'ॐ शुक्राय नमः',
    transliteration: 'Om Śukrāya Namaḥ',
    description: 'Attracts harmony, love, and creative inspiration.'
  },
  суббота: {
    planet: 'Сатурн',
    mantra: 'ॐ शनैश्चराय नमः',
    transliteration: 'Om Śanaiścarāya Namaḥ',
    description: 'Укрепляет терпение, дисциплину и устойчивость.'
  },
  saturday: {
    planet: 'Saturn',
    mantra: 'ॐ शनैश्चराय नमः',
    transliteration: 'Om Śanaiścarāya Namaḥ',
    description: 'Builds patience, discipline, and resilience.'
  }
};

const PLANET_MANTRAS = {
  солнце: WEEKDAY_MANTRAS['воскресенье'],
  sun: WEEKDAY_MANTRAS['sunday'],
  surya: WEEKDAY_MANTRAS['sunday'],
  луна: WEEKDAY_MANTRAS['понедельник'],
  moon: WEEKDAY_MANTRAS['monday'],
  chandra: WEEKDAY_MANTRAS['monday'],
  марс: WEEKDAY_MANTRAS['вторник'],
  mars: WEEKDAY_MANTRAS['tuesday'],
  mangal: WEEKDAY_MANTRAS['tuesday'],
  меркурий: WEEKDAY_MANTRAS['среда'],
  mercury: WEEKDAY_MANTRAS['wednesday'],
  budha: WEEKDAY_MANTRAS['wednesday'],
  юпитер: WEEKDAY_MANTRAS['четверг'],
  jupiter: WEEKDAY_MANTRAS['thursday'],
  guru: WEEKDAY_MANTRAS['thursday'],
  венера: WEEKDAY_MANTRAS['пятница'],
  venus: WEEKDAY_MANTRAS['friday'],
  shukra: WEEKDAY_MANTRAS['friday'],
  сатурн: WEEKDAY_MANTRAS['суббота'],
  saturn: WEEKDAY_MANTRAS['saturday'],
  shani: WEEKDAY_MANTRAS['saturday']
};

const normaliseKey = (value) => {
  if (!value || typeof value !== 'string') return '';
  return value
    .toLowerCase()
    .split(/[\s,\/\-]+/)
    .filter(Boolean)
    .map((part) => part.normalize('NFD').replace(/[\u0300-\u036f]/g, ''))
    .join(' ')
    .trim();
};

const resolveMantraByPlanet = (planetRaw) => {
  if (!planetRaw) return null;
  const fragments = planetRaw
    .split(/[\/,()]+/)
    .map((part) => normaliseKey(part))
    .filter(Boolean);

  for (const fragment of fragments) {
    if (PLANET_MANTRAS[fragment]) {
      return PLANET_MANTRAS[fragment];
    }
  }
  return null;
};

const getLocalISODate = () => {
  const date = new Date();
  const tzOffset = date.getTimezoneOffset() * 60000;
  const local = new Date(date.getTime() - tzOffset);
  return local.toISOString().split('T')[0];
};

const VedicTimeCalculations = () => {
  const [schedule, setSchedule] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedDate, setSelectedDate] = useState(() => getLocalISODate());
  const [selectedCity, setSelectedCity] = useState('');
  const [theme, setTheme] = useState(() => {
    if (typeof window === 'undefined') return 'dark';
    return localStorage.getItem('vedic-time-theme') === 'light' ? 'light' : 'dark';
  });
  const { user } = useAuth();

  const apiBaseUrl = useMemo(() => getApiBaseUrl(), []);

  const parsePlanetaryTime = useCallback(
    (timeString) => {
      if (!timeString) return null;
      
      // Если приходит полный ISO-формат — используем напрямую
      const isoPattern = /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/;
      if (isoPattern.test(timeString)) {
        const date = new Date(timeString);
        console.log('📅 Парсинг ISO времени:', timeString, '→', date.toLocaleString('ru-RU'));
        return date;
      }

      if (!selectedDate) return null;

      // Если приходит только время (HH:MM), привязываем к выбранной дате (локальной)
      const normalized = timeString.slice(0, 5);
      const date = new Date(`${selectedDate}T${normalized}:00`);
      console.log('📅 Парсинг времени:', timeString, '→', date.toLocaleString('ru-RU'));
      return date;
    },
    [selectedDate]
  );

  useEffect(() => {
    if (typeof window === 'undefined') return;
    localStorage.setItem('vedic-time-theme', theme);
  }, [theme]);

  const themeConfig = THEME_CONFIG[theme];
  const toggleTheme = () => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));

  const mantraInfo = useMemo(() => {
    if (!schedule?.weekday) return null;

    const planetMantra = resolveMantraByPlanet(schedule.weekday.ruling_planet);
    if (planetMantra) {
      return planetMantra;
    }

    const dayKey = normaliseKey(schedule.weekday.name);
    if (dayKey && WEEKDAY_MANTRAS[dayKey]) {
      return WEEKDAY_MANTRAS[dayKey];
    }

    return null;
  }, [schedule]);

  const mantraPlanetSource = useMemo(() => {
    if (schedule?.weekday?.ruling_planet) {
      return schedule.weekday.ruling_planet;
    }
    return mantraInfo?.planet ?? '';
  }, [schedule?.weekday?.ruling_planet, mantraInfo?.planet]);

  const mantraPrimaryColor = useMemo(() => {
    const planetColor = getPlanetColor(mantraPlanetSource);
    return planetColor || '#1f2937';
  }, [mantraPlanetSource]);

  const mantraBackgroundStyle = useMemo(() => {
    const baseHex = tintHex(mantraPrimaryColor, 0); // нормализуем к hex
    const highlight = tintHex(baseHex, 0.55);
    const midtone = tintHex(baseHex, 0.15);
    const deep = shadeHex(baseHex, 0.25);
    return {
      background: `linear-gradient(135deg, ${highlight} 0%, ${midtone} 45%, ${baseHex} 75%, ${deep} 100%)`,
      borderColor: withAlpha(baseHex, 0.32),
      boxShadow: `0 28px 52px ${withAlpha(baseHex, 0.38)}`
    };
  }, [mantraPrimaryColor]);

  const fetchVedicSchedule = useCallback(
    async (date, city) => {
      if (!user || !apiBaseUrl) return;
      setLoading(true);
      setError('');
    try {
      const params = new URLSearchParams();
      if (date) params.append('date', date);
      if (city) params.append('city', city);
        const response = await fetch(
          `${apiBaseUrl}/vedic-time/daily-schedule?${params.toString()}`,
          {
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
          }
        );
        if (!response.ok) {
          throw new Error('Не удалось получить ведический календарь');
        }
      const data = await response.json();
      setSchedule(data);
      } catch (err) {
        setError(err.message || 'Произошла ошибка при загрузке расписания');
      } finally {
        setLoading(false);
      }
    },
    [apiBaseUrl, user]
  );

  const changeCity = useCallback(
    async (city) => {
      if (!user || !apiBaseUrl || !city) return;
      try {
        await fetch(`${apiBaseUrl}/user/change-city`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({ city })
        });
        await fetchVedicSchedule(selectedDate, city);
      } catch (err) {
        console.error('Ошибка смены города:', err);
      }
    },
    [apiBaseUrl, fetchVedicSchedule, selectedDate, user]
  );

  const currentPlanetaryHourIndex = useMemo(() => {
    if (!schedule?.planetary_hours?.length) return null;

    // Подсвечиваем текущий час только если выбранная дата — сегодня
    const todayISO = getLocalISODate();
    if (selectedDate !== todayISO) return null;

    const now = new Date();
    console.log('🕐 Текущее время:', now.toLocaleString('ru-RU'));

    // Проверяем дневные часы
    const dayHourIndex = schedule.planetary_hours.findIndex((hour, index) => {
      const start = parsePlanetaryTime(hour.start_time || hour.start);
      const end = parsePlanetaryTime(hour.end_time || hour.end);
      
      console.log(`☀️ Дневной час ${index + 1} (${hour.planet}):`, {
        start: start?.toLocaleString('ru-RU'),
        end: end?.toLocaleString('ru-RU'),
        now: now.toLocaleString('ru-RU'),
        isActive: start && end && now >= start && now < end
      });
      
      if (!start || !end) return false;
      return now >= start && now < end;
    });

    if (dayHourIndex !== -1) {
      console.log('✅ Активный дневной час:', dayHourIndex);
      return dayHourIndex;
    }

    // Проверяем ночные часы
    if (schedule.night_hours?.length) {
      const nightHourIndex = schedule.night_hours.findIndex((hour, index) => {
        const start = parsePlanetaryTime(hour.start_time || hour.start);
        const end = parsePlanetaryTime(hour.end_time || hour.end);
        
        console.log(`🌙 Ночной час ${index + 13} (${hour.planet}):`, {
          start: start?.toLocaleString('ru-RU'),
          end: end?.toLocaleString('ru-RU'),
          now: now.toLocaleString('ru-RU'),
          isActive: start && end && now >= start && now < end
        });
        
        if (!start || !end) return false;
        return now >= start && now < end;
      });

      if (nightHourIndex !== -1) {
        console.log('✅ Активный ночной час:', 12 + nightHourIndex);
        return 12 + nightHourIndex;
      }
    }

    console.log('❌ Активный час не найден');
    return null;
  }, [parsePlanetaryTime, schedule?.planetary_hours, schedule?.night_hours, selectedDate]);

  useEffect(() => {
    if (!user) return;
    const initialCity = user.city || 'Москва';
    setSelectedCity(initialCity);
    fetchVedicSchedule(selectedDate, initialCity);
  }, [user, fetchVedicSchedule, selectedDate]);

  // Автоматическое обновление активного часа каждую минуту
  const [, forceUpdate] = useState({});
  useEffect(() => {
    const interval = setInterval(() => {
      // Принудительно пересчитываем активный час
      forceUpdate({});
      console.log('🔄 Автоматическое обновление активного часа');
    }, 60000); // Каждую минуту

    return () => clearInterval(interval);
  }, []);

  const handleDateChange = useCallback(
    (event) => {
      const value = event.target.value;
      setSelectedDate(value);
      fetchVedicSchedule(value, selectedCity);
    },
    [fetchVedicSchedule, selectedCity]
  );

  const handleCityChange = useCallback(
    (event) => {
      const value = event.target.value;
      setSelectedCity(value);
      if (value.trim().length >= 2) {
        changeCity(value.trim());
      }
    },
    [changeCity]
  );

  if (!user) {
    return (
      <div className="mx-auto flex min-h-[60vh] max-w-3xl items-center justify-center text-center">
        <div className="rounded-3xl bg-slate-100/70 p-8 text-slate-600 shadow-lg">
          Для доступа к ведическим временным расчётам необходимо авторизоваться.
        </div>
      </div>
    );
  }

  const DailyStat = ({ title, value, helper, accentClass }) => (
    <div
      className={`rounded-2xl border ${themeConfig.cardBorder} bg-white/5 p-5 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-lg ${accentClass}`}
    >
      <p className={`text-xs uppercase tracking-[0.3em] ${themeConfig.subtleText}`}>{title}</p>
      <p className="mt-3 text-2xl font-semibold">{value ?? '—'}</p>
      {helper && <p className={`mt-2 text-xs ${themeConfig.mutedText}`}>{helper}</p>}
    </div>
  );

  const PeriodCard = ({ period, tone = 'red' }) => {
    if (!period) return null;
    const toneConfig =
      tone === 'green'
        ? themeConfig.highlightGreen
        : tone === 'brown'
        ? themeConfig.highlightBrown
        : tone === 'gray'
        ? themeConfig.highlightGray
        : tone === 'blue'
        ? themeConfig.highlightBlue
        : themeConfig.highlightRed;
    return (
      <div
        className={`rounded-2xl border p-5 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-lg ${toneConfig}`}
      >
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h3 className="text-lg font-semibold">{period.name}</h3>
          <div className="rounded-xl bg-black/10 px-4 py-1 text-sm font-semibold">
            {period.start} — {period.end}
          </div>
        </div>
        <p className="mt-3 text-sm leading-relaxed">{period.description}</p>
        <p className="mt-2 text-xs opacity-80">
          Продолжительность: {period.duration_minutes} минут
        </p>
      </div>
    );
  };

  // Определяем активный час для подсветки
  const activeHourIndex = currentPlanetaryHourIndex;

  return (
    <div className={`relative min-h-screen ${themeConfig.pageBackground}`}>
      <div className="pointer-events-none absolute inset-0" style={{ background: themeConfig.overlayGradient }} />
      <div className="relative z-10 mx-auto max-w-6xl px-4 py-12 md:py-16">
        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
          <div className="space-y-3">
            <p className={`text-xs uppercase tracking-[0.4em] ${themeConfig.subtleText}`}>
              Аюрведический распорядок
            </p>
            <h1 className="text-3xl md:text-4xl font-semibold leading-tight">
              Ведические времена и планетарные часы
            </h1>
            <p className={`max-w-2xl text-sm md:text-base leading-relaxed ${themeConfig.mutedText}`}>
              Отслеживайте Раху Кала, Абхиджит Мухурту и смену планетарных часов в мягком интерфейсе.
              Данные адаптируются к выбранной дате и вашему городу.
            </p>
          </div>
          <div className="flex items-center gap-3 self-start rounded-2xl border border-white/10 bg-white/5 px-4 py-2 shadow-lg shadow-black/25">
            <span className={`text-sm ${themeConfig.mutedText}`}>Тема</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleTheme}
              className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-1"
            >
              {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              {theme === 'dark' ? 'Светлая' : 'Тёмная'}
            </Button>
                </div>
                </div>

        <div className={`mt-10 rounded-3xl ${themeConfig.glass} p-6 md:p-8`}>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-[2fr,1.2fr]">
            <div className="space-y-4">
              <div className={`text-xs uppercase tracking-[0.35em] ${themeConfig.subtleText}`}>
                Параметры расчёта
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className={`rounded-2xl ${themeConfig.surface} p-4`}>
                  <label className={`flex items-center gap-2 text-xs uppercase tracking-[0.35em] ${themeConfig.subtleText}`}>
                    <Calendar className="h-4 w-4" /> дата
                  </label>
                  <Input
                    type="date"
                    value={selectedDate}
                    onChange={handleDateChange}
                    className="mt-2 h-11 rounded-xl border border-white/10 bg-white/60 px-3 text-sm text-slate-900 focus-visible:ring-2 focus-visible:ring-emerald-400"
                  />
                </div>
                <div className={`rounded-2xl ${themeConfig.surface} p-4`}>
                  <label className={`flex items-center gap-2 text-xs uppercase tracking-[0.35em] ${themeConfig.subtleText}`}>
                    <MapPin className="h-4 w-4" /> город
                  </label>
                  <Input
                    type="text"
                    value={selectedCity}
                    onChange={handleCityChange}
                    placeholder="Например, Москва"
                    className="mt-2 h-11 rounded-xl border border-white/10 bg-white/60 px-3 text-sm text-slate-900 focus-visible:ring-2 focus-visible:ring-emerald-400"
                  />
                </div>
              </div>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <Button
                  onClick={() => fetchVedicSchedule(selectedDate, selectedCity)}
                  disabled={loading}
                  className="flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-400 via-cyan-400 to-sky-400 px-6 py-3 text-sm font-semibold shadow-lg shadow-emerald-200/30 transition-all hover:brightness-110"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Обновляем данные...
                    </>
                  ) : (
                    <>
                      <RefreshCcw className="h-4 w-4" />
                      Обновить расчёт
                    </>
                  )}
                </Button>
                <p className={`text-xs ${themeConfig.subtleText}`}>
                  Расчёт учитывает широту, долготу и часовой пояс выбранного города.
                </p>
                      </div>
                    </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
              <div className="flex items-center gap-3">
                <Sparkles className="h-5 w-5 text-emerald-300" />
                <h2 className="text-sm font-semibold uppercase tracking-[0.35em] text-emerald-200">
                  Быстрый дайджест
                </h2>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-emerald-100">
                Ведические времена помогают выбирать гармоничные промежутки для действий и отдыха.
                Соблюдайте рекомендации для усиления планетарной поддержки.
              </p>
              <div className="mt-4 grid grid-cols-1 gap-3 text-xs text-emerald-100">
                <div>• Учитывайте Раху Кала — время, когда лучше избегать новых начинаний.</div>
                <div>• Абхиджит Мухурта — окно успеха, используйте для важных решений.</div>
                <div>• Планетарные часы раскрывают энергию текущего часа.</div>
                    </div>
                  </div>
                      </div>
                    </div>

        {error && (
          <div className="mt-6 rounded-3xl border border-rose-300 bg-rose-100/80 p-6 text-rose-800 shadow-lg">
            {error}
                  </div>
                )}

        {loading && !schedule && (
          <div className="mt-10 flex flex-col items-center justify-center gap-3 rounded-3xl border border-white/10 bg-white/5 p-12">
            <Loader2 className="h-8 w-8 animate-spin text-emerald-300" />
            <span className={`text-sm ${themeConfig.mutedText}`}>
              Рассчитываем ведический календарь...
            </span>
                  </div>
                )}

        {schedule && !loading && (
          <div className="mt-10 space-y-10">
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
              <DailyStat
                title="День недели"
                value={schedule.weekday?.name}
                helper={`Сегодня управляет планета ${schedule.weekday?.ruling_planet}`}
                accentClass="bg-gradient-to-br from-sky-400/10 to-sky-400/5"
              />
              <DailyStat
                title="Город и зона"
                value={`${schedule.city ?? '—'} · ${schedule.timezone ?? ''}`}
                helper="Расчёты учитывают локальный пояс"
                accentClass="bg-gradient-to-br from-emerald-400/10 to-emerald-300/5"
              />
            </div>

            <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
              <DailyStat
                title="Восход Солнца"
                value={schedule.sun_times?.sunrise}
                helper="Лучшее время для практик"
                accentClass="bg-gradient-to-br from-amber-300/15 to-amber-200/10"
              />
              <DailyStat
                title="Закат Солнца"
                value={schedule.sun_times?.sunset}
                helper="Период подведения итогов"
                accentClass="bg-gradient-to-br from-rose-300/15 to-rose-200/10"
              />
              <DailyStat
                title="Длительность дня"
                value={`${schedule.sun_times?.day_duration_hours ?? '-'} ч`}
                helper="Сумма солнечных часов"
                accentClass="bg-gradient-to-br from-indigo-300/10 to-indigo-200/10"
              />
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-rose-300" />
                <h2 className="text-xl font-semibold">Неблагоприятные промежутки</h2>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <PeriodCard period={schedule.inauspicious_periods?.rahu_kaal} tone="red" />
                <PeriodCard period={schedule.inauspicious_periods?.gulika_kaal} tone="brown" />
                <PeriodCard period={schedule.inauspicious_periods?.yamaghanta} tone="gray" />
                    </div>
                  </div>

            {schedule.auspicious_periods?.abhijit_muhurta && (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-300" />
                  <h2 className="text-xl font-semibold">Благоприятные окна</h2>
                </div>
                <PeriodCard period={schedule.auspicious_periods.abhijit_muhurta} tone="green" />
              </div>
          )}

          {schedule.recommendations && (
                <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-sky-300" />
                  <h2 className="text-xl font-semibold">Рекомендации дня</h2>
                </div>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  {schedule.recommendations.activities && (
                    <div className="rounded-2xl border border-white/10 bg-white/60 p-5">
                      <h3 className="text-sm font-semibold uppercase tracking-[0.3em] text-sky-700">
                        Рекомендуемые активности
                      </h3>
                      <ul className="mt-3 space-y-1 text-sm text-sky-600">
                        {schedule.recommendations.activities.map((activity, idx) => (
                          <li key={idx}>• {activity}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {schedule.recommendations.avoid && (
                    <div className="rounded-2xl border border-white/10 bg-white/60 p-5">
                      <h3 className="text-sm font-semibold uppercase tracking-[0.3em] text-rose-700">
                        Чего следует избегать
                      </h3>
                      <ul className="mt-3 space-y-1 text-sm text-rose-600">
                        {schedule.recommendations.avoid.map((item, idx) => (
                          <li key={idx}>• {item}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {schedule.recommendations.colors && (
                    <div className="rounded-2xl border border-white/10 bg-white/60 p-5">
                      <h3 className="text-sm font-semibold uppercase tracking-[0.3em] text-violet-700">
                        Благоприятные цвета
                      </h3>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {schedule.recommendations.colors.map((color, idx) => (
                          <span
                            key={idx}
                            className="rounded-full px-3 py-1 text-xs font-semibold capitalize"
                            style={{
                              backgroundColor: `${color.toLowerCase()}`,
                              color: ['white', 'белый', 'Ivory', 'Snow', 'Хлопок'].includes(color)
                                ? '#1f2937'
                                : '#f8fafc'
                            }}
                          >
                            {color}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                      </div>
                    </div>
                  )}

            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-white/90 drop-shadow-[0_0_10px_rgba(255,255,255,0.45)]" />
                <h2 className="text-xl font-semibold text-white">Мантра дня</h2>
                      </div>
              <div
                className="rounded-3xl border p-6 transition-all duration-300 hover:-translate-y-1"
                style={mantraBackgroundStyle}
              >
                {mantraInfo ? (
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-[0.35em] text-white/80">
                        {mantraInfo.planet}
                      </p>
                      <p className="mt-3 text-3xl font-semibold leading-tight text-white drop-shadow-[0_8px_22px_rgba(0,0,0,0.25)]">
                        {mantraInfo.mantra}
                      </p>
                      <p className="mt-1 text-xs uppercase tracking-[0.35em] text-white/70">
                        {mantraInfo.transliteration}
                      </p>
                    </div>
                    {mantraInfo.description && (
                      <p className="max-w-xl text-sm leading-relaxed text-white/85">
                        {mantraInfo.description}
                      </p>
                  )}
                </div>
                ) : (
                  <p className="text-sm text-white/85">
                    Для выбранного дня мантра не определена. Проверьте настройки города и даты.
                  </p>
                )}
              </div>
            </div>

          {/* Планетарные часы дня */}
            <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
              <div className="flex items-center gap-3">
                <Clock3 className="h-5 w-5 text-indigo-300" />
                <h2 className="text-sm font-semibold uppercase tracking-[0.35em] text-indigo-200">
                  Планетарные часы дня
                </h2>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-indigo-100">
                Показано {schedule.planetary_hours?.length || 0} планетарных часов.
              </p>
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {schedule.planetary_hours?.map((hour, index) => {
                  const isActive = activeHourIndex === index;
                  const planetColor = getPlanetColor(hour.planet);
                  return (
                    <div
                      key={index}
                      className={`rounded-2xl border p-5 transition-all duration-500 hover:-translate-y-1 relative ${
                        isActive ? 'shadow-2xl scale-110 ring-4 ring-offset-4 ring-offset-slate-900' : 'shadow-sm hover:shadow-lg'
                      }`}
                      style={{
                        borderColor: isActive ? planetColor : planetColor + '40',
                        backgroundColor: isActive ? planetColor + '40' : planetColor + '10',
                        boxShadow: isActive 
                          ? `0 0 60px ${planetColor}80, 0 0 120px ${planetColor}60, 0 20px 80px ${planetColor}40, inset 0 0 40px ${planetColor}20` 
                          : undefined,
                        ringColor: isActive ? planetColor : undefined,
                        borderWidth: isActive ? '3px' : '1px'
                      }}
                    >
                      {isActive && (
                        <div 
                          className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest whitespace-nowrap animate-pulse shadow-lg"
                          style={{
                            backgroundColor: planetColor,
                            color: '#ffffff',
                            boxShadow: `0 0 20px ${planetColor}80, 0 0 40px ${planetColor}60`
                          }}
                        >
                          ⏰ ТЕКУЩЕЕ ВРЕМЯ ⏰
                        </div>
                      )}
                      <div className="flex items-center justify-between">
                        <span
                          className={`font-bold ${isActive ? 'text-xl' : 'text-sm'}`}
                          style={{ 
                            color: isActive ? '#ffffff' : planetColor,
                            textShadow: isActive ? `0 0 10px ${planetColor}, 0 0 20px ${planetColor}80` : undefined
                          }}
                        >
                          {hour.planet_sanskrit || hour.planet}
                        </span>
                        <span 
                          className={`rounded-full px-3 py-1 text-xs font-bold ${isActive ? 'animate-pulse' : ''}`}
                          style={{
                            backgroundColor: isActive ? '#ffffff' : planetColor + '30',
                            color: isActive ? planetColor : planetColor,
                            boxShadow: isActive ? `0 0 15px ${planetColor}60` : undefined
                          }}
                        >
                          Час {hour.hour || index + 1}
                        </span>
                      </div>
                      <div className={`mt-3 text-sm ${isActive ? 'font-bold text-white text-base' : themeConfig.mutedText}`}
                        style={{
                          textShadow: isActive ? `0 0 10px ${planetColor}80` : undefined
                        }}
                      >
                        {hour.start_time?.slice(11, 16) || hour.start} —{' '}
                        {hour.end_time?.slice(11, 16) || hour.end}
                      </div>
                      {isActive && (
                        <div 
                          className="mt-3 inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-bold text-white animate-pulse"
                          style={{
                            backgroundColor: '#ffffff30',
                            backdropFilter: 'blur(10px)',
                            boxShadow: `0 0 20px ${planetColor}40`
                          }}
                        >
                          <Clock3 className="h-4 w-4" />
                          Сейчас активно
                        </div>
                      )}
                      {hour.is_favorable && !isActive && (
                        <div className="mt-3 inline-flex items-center gap-2 rounded-full bg-emerald-400/20 px-3 py-1 text-xs font-semibold text-emerald-600">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Благоприятно
                        </div>
                      )}
                      {hour.focus && (
                        <p className="mt-3 text-xs leading-relaxed text-emerald-200">{hour.focus}</p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

          {/* Планетарные часы ночи */}
          {schedule.night_hours && schedule.night_hours.length > 0 && (
            <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
              <div className="flex items-center gap-3">
                <Clock3 className="h-5 w-5 text-purple-300" />
                <h2 className="text-sm font-semibold uppercase tracking-[0.35em] text-purple-200">
                  Планетарные часы ночи
                </h2>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-purple-100">
                Показано {schedule.night_hours?.length || 0} планетарных часов.
              </p>
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {schedule.night_hours?.map((hour, index) => {
                  const isActive = activeHourIndex === (12 + index);
                  const planetColor = getPlanetColor(hour.planet);
                  return (
                    <div
                      key={index}
                      className={`rounded-2xl border p-5 transition-all duration-500 hover:-translate-y-1 relative ${
                        isActive ? 'shadow-2xl scale-110 ring-4 ring-offset-4 ring-offset-slate-900' : 'shadow-sm hover:shadow-lg'
                      }`}
                      style={{
                        borderColor: isActive ? planetColor : planetColor + '40',
                        backgroundColor: isActive ? planetColor + '40' : planetColor + '10',
                        boxShadow: isActive 
                          ? `0 0 60px ${planetColor}80, 0 0 120px ${planetColor}60, 0 20px 80px ${planetColor}40, inset 0 0 40px ${planetColor}20` 
                          : undefined,
                        ringColor: isActive ? planetColor : undefined,
                        borderWidth: isActive ? '3px' : '1px'
                      }}
                    >
                      {isActive && (
                        <div 
                          className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest whitespace-nowrap animate-pulse shadow-lg"
                          style={{
                            backgroundColor: planetColor,
                            color: '#ffffff',
                            boxShadow: `0 0 20px ${planetColor}80, 0 0 40px ${planetColor}60`
                          }}
                        >
                          ⏰ ТЕКУЩЕЕ ВРЕМЯ ⏰
                        </div>
                      )}
                      <div className="flex items-center justify-between">
                        <span
                          className={`font-bold ${isActive ? 'text-xl' : 'text-sm'}`}
                          style={{ 
                            color: isActive ? '#ffffff' : planetColor,
                            textShadow: isActive ? `0 0 10px ${planetColor}, 0 0 20px ${planetColor}80` : undefined
                          }}
                        >
                          {hour.planet_sanskrit || hour.planet}
                        </span>
                        <span 
                          className={`rounded-full px-3 py-1 text-xs font-bold ${isActive ? 'animate-pulse' : ''}`}
                          style={{
                            backgroundColor: isActive ? '#ffffff' : planetColor + '30',
                            color: isActive ? planetColor : planetColor,
                            boxShadow: isActive ? `0 0 15px ${planetColor}60` : undefined
                          }}
                        >
                          Час {hour.hour || (13 + index)}
                        </span>
                      </div>
                      <div className={`mt-3 text-sm ${isActive ? 'font-bold text-white text-base' : themeConfig.mutedText}`}
                        style={{
                          textShadow: isActive ? `0 0 10px ${planetColor}80` : undefined
                        }}
                      >
                        {hour.start_time?.slice(11, 16) || hour.start} —{' '}
                        {hour.end_time?.slice(11, 16) || hour.end}
                      </div>
                      {isActive && (
                        <div 
                          className="mt-3 inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-bold text-white animate-pulse"
                          style={{
                            backgroundColor: '#ffffff30',
                            backdropFilter: 'blur(10px)',
                            boxShadow: `0 0 20px ${planetColor}40`
                          }}
                        >
                          <Clock3 className="h-4 w-4" />
                          Сейчас активно
                        </div>
                      )}
                      {hour.is_favorable && !isActive && (
                        <div className="mt-3 inline-flex items-center gap-2 rounded-full bg-emerald-400/20 px-3 py-1 text-xs font-semibold text-emerald-600">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Благоприятно
                        </div>
                      )}
                      {hour.focus && (
                        <p className="mt-3 text-xs leading-relaxed text-emerald-200">{hour.focus}</p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          </div>
      )}
      </div>
    </div>
  );
};

export default VedicTimeCalculations;