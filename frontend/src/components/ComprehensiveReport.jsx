import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { useAuth } from './AuthContext';
import { getBackendUrl } from '../utils/backendUrl';
import {
  User,
  Calendar,
  MapPin,
  Car,
  Star,
  Download,
  Palette,
  BarChart3,
  TrendingUp,
  Users,
  Moon,
  Sun,
  Eye,
  FileText,
  Clock,
  CheckCircle,
  AlertTriangle,
  Target,
  ChevronLeft,
  ChevronRight,
  Calculator
} from 'lucide-react';
import { Line, getElementAtEvent } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler);

const ComprehensiveReport = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [reportData, setReportData] = useState(null);
  const [theme, setTheme] = useState('light');
  const [activeTab, setActiveTab] = useState('overview');
  const [routePeriod, setRoutePeriod] = useState('daily'); // daily, weekly, monthly, quarterly
  const [routeData, setRouteData] = useState({
    daily: null,
    weekly: null,
    monthly: null,
    quarterly: null
  });
  // Якоря для секции «Персональные числа»
  const personalRefs = useMemo(() => ({
    soul: React.createRef(),
    mind: React.createRef(),
    destiny: React.createRef(),
    helping: React.createRef(),
    wisdom: React.createRef(),
    ruling: React.createRef()
  }), []);
  const scrollToPersonal = (key) => {
    const el = personalRefs[key]?.current;
    if (!el) return;
    const offset = 90; // компенсируем закреплённую панель
    const y = el.getBoundingClientRect().top + window.scrollY - offset;
    window.scrollTo({ top: y, behavior: 'smooth' });
  };
  const [energyPeriod, setEnergyPeriod] = useState('weekly'); // weekly, monthly, quarterly
  const [energyDate, setEnergyDate] = useState(new Date());
  const [energyData, setEnergyData] = useState(null);
  const [visiblePlanets, setVisiblePlanets] = useState({
    surya: true,
    chandra: true,
    mangal: true,
    budha: true,
    guru: true,
    shukra: true,
    shani: true,
    rahu: true,
    ketu: true
  });
  const [hoveredDigit, setHoveredDigit] = useState(null);
  const [hoveredSet, setHoveredSet] = useState(null);
  const [hoveredAbracadabraIndex, setHoveredAbracadabraIndex] = useState(null); // индекс в базовом ряду (0-8)
  const [hoveredHumanPart, setHoveredHumanPart] = useState(null); // 'head', 'handLeft', 'handRight', 'soul', 'mindNumber', 'destinyNumber', 'bottomDigit'
  const [hoveredPersonalNumber, setHoveredPersonalNumber] = useState(null); // 'soul', 'mind', 'destiny', 'helpingMind', 'wisdom', 'ruling'
  const [hoveredPlanetEnergy, setHoveredPlanetEnergy] = useState(null); // индекс планеты (0-6) для графика личной энергии
  const [hoveredPlanetsOnChart, setHoveredPlanetsOnChart] = useState([]); // массив планет, на которые наведён курсор на графике
  const [hoveredFractalDigit, setHoveredFractalDigit] = useState(null); // позиция цифры фрактала (1, 2, 3, 4) для подсветки
  const [hoveredTaskNumber, setHoveredTaskNumber] = useState(null); // позиция числа проблемы (1, 2, 3, 4) для подсветки
  const [hoveredIndividualNumber, setHoveredIndividualNumber] = useState(null); // 'chig', 'chim', 'chid' для подсветки
  const [selectedDayModal, setSelectedDayModal] = useState(null); // данные дня для модального окна
  const chartRef = useRef(null);
  const chartRefWeekly = useRef(null);

  const backendUrl = getBackendUrl();

  // Функция для форматирования даты без времени
  const formatDate = (dateString) => {
    if (!dateString) return '';
    try {
      // Если это ISO строка с временем, обрезаем до даты
      if (dateString.includes('T')) {
        dateString = dateString.split('T')[0];
      }
      
      // Если дата уже в формате DD.MM.YYYY, возвращаем как есть
      if (dateString.includes('.')) {
        const parts = dateString.split('.');
        if (parts.length === 3) {
          // Проверяем, что это действительно DD.MM.YYYY (первая часть меньше 32)
          if (parseInt(parts[0]) < 32 && parseInt(parts[1]) < 13) {
            return dateString;
          }
        }
      }
      
      // Если дата в формате YYYY-MM-DD, парсим и форматируем в DD.MM.YYYY
      if (dateString.includes('-')) {
        const parts = dateString.split('-');
        if (parts.length === 3) {
          const year = parts[0];
          const month = parts[1];
          const day = parts[2];
          return `${day}.${month}.${year}`;
        }
      }
      
      // Пробуем распарсить как Date и форматировать
      const date = new Date(dateString);
      if (!isNaN(date.getTime())) {
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        return `${day}.${month}.${year}`;
      }
      
      return dateString;
    } catch {
      return dateString;
    }
  };

  // Функция для получения дня недели из даты
  const getDayOfWeek = (dateString) => {
    if (!dateString) return '';
    try {
      let date;
      // Если дата в формате ДД.ММ.ГГГГ
      if (dateString.includes('.')) {
        const [day, month, year] = dateString.split('.');
        date = new Date(parseInt(year, 10), parseInt(month, 10) - 1, parseInt(day, 10));
      } else {
        date = new Date(dateString);
      }
      if (isNaN(date.getTime())) return '';
      const days = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'];
      return days[date.getDay()];
    } catch {
      return '';
    }
  };

  // Функция для приведения числа к одной цифре
  const reduceToSingleDigit = (num) => {
    if (num === 0) return 0;
    if (num === 11 || num === 22 || num === 33) return num; // Мастер-числа
    let result = num;
    while (result > 9) {
      result = String(result).split('').reduce((sum, digit) => sum + parseInt(digit, 10), 0);
      if (result === 11 || result === 22 || result === 33) break; // Мастер-числа
    }
    return result;
  };

  // Функция для приведения числа к одной цифре (без мастер-чисел, только для фрактала)
  const reduceToSingleDigitForFractal = (num) => {
    if (num === 0) return 0;
    let result = num;
    while (result > 9) {
      result = String(result).split('').reduce((sum, digit) => sum + parseInt(digit, 10), 0);
    }
    return result;
  };

  // Функция для расчёта фрактала поведения
  const calculateBehaviorFractal = (birthDate) => {
    if (!birthDate) return null;
    try {
      let day, month, year;
      
      // Если дата в формате ДД.ММ.ГГГГ
      if (birthDate.includes('.')) {
        const parts = birthDate.split('.');
        day = parseInt(parts[0], 10);
        month = parseInt(parts[1], 10);
        year = parseInt(parts[2], 10);
      } 
      // Если дата в формате YYYY-MM-DD
      else if (birthDate.includes('-')) {
        const parts = birthDate.split('-');
        year = parseInt(parts[0], 10);
        month = parseInt(parts[1], 10);
        day = parseInt(parts[2], 10);
      } else {
        return null;
      }

      if (isNaN(day) || isNaN(month) || isNaN(year)) return null;

      // Первая цифра: день рождения (приведённый к одной цифре, без мастер-чисел)
      const digit1 = reduceToSingleDigitForFractal(day);
      
      // Вторая цифра: месяц рождения (приведённый к одной цифре, без мастер-чисел)
      const digit2 = reduceToSingleDigitForFractal(month);
      
      // Третья цифра: год рождения, приведённый к одной цифре (без мастер-чисел)
      const digit3 = reduceToSingleDigitForFractal(year);
      
      // Четвёртая цифра: сумма всех чисел (день + месяц + год), приведённая к одной цифре (без мастер-чисел)
      const digit4 = reduceToSingleDigitForFractal(day + month + year);

      return {
        digit1,
        digit2,
        digit3,
        digit4,
        fractal: `${digit1}${digit2}${digit3}${digit4}`
      };
    } catch {
      return null;
    }
  };

  // Функция для расчёта чисел задач (проблем)
  // Использует уже приведённые к одной цифре числа: число души, число ума, число судьбы, число целого года
  const calculateTaskNumbers = (soulNumber, mindNumber, destinyNumber, yearNumber) => {
    if (soulNumber === null || soulNumber === undefined || 
        mindNumber === null || mindNumber === undefined || 
        destinyNumber === null || destinyNumber === undefined ||
        yearNumber === null || yearNumber === undefined) {
      return null;
    }
    try {
      // Первое число проблемы: число души минус число ума по модулю, приведённое к целому числу
      const problem1 = Math.abs(soulNumber - mindNumber);
      const problem1Reduced = reduceToSingleDigitForFractal(problem1);
      
      // Период первого числа: начинается с (36 - число судьбы), заканчивается полученная цифра + 9
      const period1Start = 36 - destinyNumber;
      const period1End = period1Start + 9;
      
      // Второе число проблемы: число души минус число целого года рождения (по модулю, приведённое к целому числу)
      const problem2 = Math.abs(soulNumber - yearNumber);
      const problem2Reduced = reduceToSingleDigitForFractal(problem2);
      
      // Период второго числа: начало - это окончание первого периода, длится 9 лет
      const period2Start = period1End;
      const period2End = period2Start + 9;
      
      // Третье число проблемы: первое число проблемы минус второе число проблемы по модулю
      const problem3 = Math.abs(problem1Reduced - problem2Reduced);
      const problem3Reduced = reduceToSingleDigitForFractal(problem3);
      
      // Период третьего числа: всю жизнь (от рождения)
      
      // Четвёртое число проблемы: месяц минус целое число года рождения (по модулю, приведённое к целому числу)
      // mindNumber - это число месяца (число ума вычисляется из месяца)
      const problem4 = Math.abs(mindNumber - yearNumber);
      const problem4Reduced = reduceToSingleDigitForFractal(problem4);
      
      // Период четвёртого числа: от окончания периода второго числа проблемы до конца жизни
      const period4Start = period2End;

      return {
        problem1: problem1Reduced,
        problem2: problem2Reduced,
        problem3: problem3Reduced,
        problem4: problem4Reduced,
        period1: { start: period1Start, end: period1End },
        period2: { start: period2Start, end: period2End },
        period3: { start: 0, end: null }, // Всю жизнь
        period4: { start: period4Start, end: null }, // До конца жизни
        calculations: {
          problem1Raw: problem1,
          problem2Raw: problem2,
          problem3Raw: problem3,
          problem4Raw: problem4,
          soulNumber,
          mindNumber,
          destinyNumber,
          yearNumber
        }
      };
    } catch {
      return null;
    }
  };

  // Функция для расчёта Теней, Вершин, Вызовов, Переходов
  const calculateShadowsPeaksChallenges = (birthDate) => {
    if (!birthDate) return null;
    try {
      let day, month, year;
      
      // Парсим дату рождения
      if (birthDate.includes('.')) {
        const parts = birthDate.split('.');
        day = parseInt(parts[0], 10);
        month = parseInt(parts[1], 10);
        year = parseInt(parts[2], 10);
      } else if (birthDate.includes('-')) {
        const parts = birthDate.split('-');
        year = parseInt(parts[0], 10);
        month = parseInt(parts[1], 10);
        day = parseInt(parts[2], 10);
      } else {
        return null;
      }

      if (isNaN(day) || isNaN(month) || isNaN(year)) return null;

      // Функция для приведения к одной цифре
      const reduceToSingleDigit = (num) => {
        let n = Math.abs(num);
        while (n > 9) {
          n = String(n).split('').reduce((sum, digit) => sum + parseInt(digit, 10), 0);
        }
        return n;
      };

      // Рассчитываем число судьбы (день + месяц + год, приведённое к одной цифре)
      const destinyNumber = reduceToSingleDigit(day + month + year);
      
      // Рассчитываем базовое число (день + месяц)
      const baseNumber = reduceToSingleDigit(day + month);
      
      // Рассчитываем ЧЛГ для каждого года жизни (от 1 до 100)
      // ЧЛГ = (день приведённый к одной цифре) + (месяц приведённый к одной цифре) + год жизни, приведённое к одной цифре
      const dayReduced = reduceToSingleDigit(day);
      const monthReduced = reduceToSingleDigit(month);
      const years = [];
      for (let age = 1; age <= 100; age++) {
        const currentYear = year + age;
        // Суммируем приведённые день + месяц + год, затем приводим к одной цифре
        const chlg = reduceToSingleDigit(dayReduced + monthReduced + currentYear);
        years.push({
          age,
          year: currentYear,
          chlg
        });
      }

      // Таблица автора «Тени · Вершины · Вызовы · Переходы»: четыре периода по 9 лет (23–32, 32–41, …).
      // Первый начинается с (27 - число судьбы).
      const firstPeriodStart = 27 - destinyNumber;
      const periodLength = 9;
      const yearReduced = reduceToSingleDigit(year);
      // Вершины: день + месяц; день + год; первая + вторая; месяц + год
      const firstPeak = reduceToSingleDigit(dayReduced + monthReduced);
      const secondPeak = reduceToSingleDigit(dayReduced + yearReduced);
      const peaks = [firstPeak, secondPeak, reduceToSingleDigit(firstPeak + secondPeak), reduceToSingleDigit(monthReduced + yearReduced)];
      // Вызовы: |месяц - день|; |день - год|; |первый - второй|; |месяц - год|
      const firstChallenge = Math.abs(monthReduced - dayReduced);
      const secondChallenge = Math.abs(dayReduced - yearReduced);
      const challenges = [firstChallenge, secondChallenge, Math.abs(firstChallenge - secondChallenge), Math.abs(monthReduced - yearReduced)];
      // Тень = вершина + день, месяц, год, число судьбы по порядку периодов
      const shadowBases = [dayReduced, monthReduced, yearReduced, destinyNumber];
      const periods = peaks.map((peak, i) => {
        const startAge = firstPeriodStart + i * periodLength;
        const endAge = startAge + periodLength;
        const shadow = reduceToSingleDigit(shadowBases[i] + peak);
        const challenge = challenges[i];
        // Переход = тень + вершина + вызов
        const transition = reduceToSingleDigit(shadow + peak + challenge);
        return {
          index: i + 1,
          startAge,
          endAge,
          years: years.filter(y => y.age >= startAge && y.age < endAge),
          shadow,      // Первая - Тень
          peak,        // Вторая - Вершина
          challenge,   // Третья - Вызов
          transition,  // Четвёртая - Переход
          periodNumbers: [shadow, peak, challenge, transition]
        };
      });

      return {
        baseNumber,
        destinyNumber,
        birthDate: { day, month, year },
        years,
        periods,
        sequence: years.map(y => y.chlg).join(' ')
      };
    } catch {
      return null;
    }
  };

  // Функция для расчёта ЧИГ, ЧИМ, ЧИД (Число индивидуального года, месяца, дня) и ЧПГ, ЧПМ, ЧПД
  const calculateIndividualNumbers = (birthDate, targetDate = null, destinyNumber = null) => {
    if (!birthDate) return null;
    try {
      let birthDay, birthMonth, birthYear;
      
      // Парсим дату рождения
      if (birthDate.includes('.')) {
        const parts = birthDate.split('.');
        birthDay = parseInt(parts[0], 10);
        birthMonth = parseInt(parts[1], 10);
        birthYear = parseInt(parts[2], 10);
      } else if (birthDate.includes('-')) {
        const parts = birthDate.split('-');
        birthYear = parseInt(parts[0], 10);
        birthMonth = parseInt(parts[1], 10);
        birthDay = parseInt(parts[2], 10);
      } else {
        return null;
      }

      if (isNaN(birthDay) || isNaN(birthMonth) || isNaN(birthYear)) return null;

      // Функция для приведения к одной цифре (по модулю, сводить к целому числу)
      const reduceToSingleDigit = (num) => {
        let n = Math.abs(num);
        while (n > 9) {
          n = String(n).split('').reduce((sum, digit) => sum + parseInt(digit, 10), 0);
        }
        return n;
      };

      // Если число судьбы не передано, вычисляем его
      if (destinyNumber === null || destinyNumber === undefined) {
        const destinySum = birthDay + birthMonth + birthYear;
        destinyNumber = reduceToSingleDigit(destinySum);
      }

      // Определяем текущую дату или используем переданную
      const now = targetDate ? new Date(targetDate) : new Date();
      const currentYear = now.getFullYear();
      const currentMonth = now.getMonth() + 1; // JavaScript месяцы 0-11
      const currentDay = now.getDate();

      // ЧИГ (Число индивидуального года) = день рождения + месяц рождения + текущий год
      const chig = reduceToSingleDigit(birthDay + birthMonth + currentYear);

      // ЧИМ (Число индивидуального месяца) = ЧИГ + текущий месяц
      const chim = reduceToSingleDigit(chig + currentMonth);

      // ЧИД (Число индивидуального дня) = ЧИМ + текущий день
      const chid = reduceToSingleDigit(chim + currentDay);

      // ЧПГ (Число проблемы года) = ЧИГ - число судьбы (по модулю)
      const chpgValue = reduceToSingleDigit(Math.abs(chig - destinyNumber));
      const chpg = {
        value: chpgValue,
        calculation: `|${chig} - ${destinyNumber}| = ${Math.abs(chig - destinyNumber)} → ${chpgValue}`
      };

      // ЧПМ (Число проблемы месяца) = месяц рождения - ЧИМ (по модулю)
      const chpmValue = reduceToSingleDigit(Math.abs(birthMonth - chim));
      const chpm = {
        value: chpmValue,
        calculation: `|${birthMonth} - ${chim}| = ${Math.abs(birthMonth - chim)} → ${chpmValue}`
      };

      // ЧПД (Число проблемы дня) = день рождения - ЧИД (по модулю)
      const chpdValue = reduceToSingleDigit(Math.abs(birthDay - chid));
      const chpd = {
        value: chpdValue,
        calculation: `|${birthDay} - ${chid}| = ${Math.abs(birthDay - chid)} → ${chpdValue}`
      };

      return {
        birthDate: { day: birthDay, month: birthMonth, year: birthYear },
        currentDate: { day: currentDay, month: currentMonth, year: currentYear },
        destinyNumber: destinyNumber,
        chig: {
          value: chig,
          calculation: `${birthDay} + ${birthMonth} + ${currentYear} = ${birthDay + birthMonth + currentYear} → ${chig}`
        },
        chim: {
          value: chim,
          calculation: `${chig} + ${currentMonth} = ${chig + currentMonth} → ${chim}`
        },
        chid: {
          value: chid,
          calculation: `${chim} + ${currentDay} = ${chim + currentDay} → ${chid}`
        },
        chpg: chpg,
        chpm: chpm,
        chpd: chpd
      };
    } catch {
      return null;
    }
  };

  // Интерпретации энергий для фрактала поведения
  const getBehaviorFractalInterpretation = (fractal) => {
    if (!fractal) return null;
    
    const digitMeanings = {
      1: { planet: 'Сурья (Солнце)', energy: 'Лидерство, инициатива, независимость, творчество' },
      2: { planet: 'Чандра (Луна)', energy: 'Партнёрство, чувствительность, интуиция, сотрудничество' },
      3: { planet: 'Гуру (Юпитер)', energy: 'Коммуникация, оптимизм, самовыражение, радость' },
      4: { planet: 'Раху (Северный узел)', energy: 'Стабильность, практичность, трудолюбие, структура' },
      5: { planet: 'Будха (Меркурий)', energy: 'Свобода, перемены, любопытство, приключения' },
      6: { planet: 'Шукра (Венера)', energy: 'Гармония, забота, ответственность, красота' },
      7: { planet: 'Кету (Южный узел)', energy: 'Анализ, духовность, мудрость, поиск истины' },
      8: { planet: 'Шани (Сатурн)', energy: 'Материальный успех, власть, организация, достижения' },
      9: { planet: 'Мангал (Марс)', energy: 'Гуманизм, завершение, служение, мудрость' },
      11: { planet: 'Мастер-число', energy: 'Интуиция, вдохновение, духовное просветление' },
      22: { planet: 'Мастер-число', energy: 'Практическая мудрость, строительство, служение человечеству' },
      33: { planet: 'Мастер-число', energy: 'Высшее служение, учительство, исцеление' }
    };

    const interpretations = {
      digit1: digitMeanings[fractal.digit1] || { planet: 'Неизвестно', energy: 'Энергия не определена' },
      digit2: digitMeanings[fractal.digit2] || { planet: 'Неизвестно', energy: 'Энергия не определена' },
      digit3: digitMeanings[fractal.digit3] || { planet: 'Неизвестно', energy: 'Энергия не определена' },
      digit4: digitMeanings[fractal.digit4] || { planet: 'Неизвестно', energy: 'Энергия не определена' }
    };

    // Общая интерпретация фрактала
    const generalInterpretation = `
      Ваш фрактал поведения ${fractal.fractal} раскрывает особенности вашего характера и поведения:
      • Первая цифра (${fractal.digit1}) - ${interpretations.digit1.planet}: определяет вашу основную жизненную позицию и способ самовыражения. ${interpretations.digit1.energy}.
      • Вторая цифра (${fractal.digit2}) - ${interpretations.digit2.planet}: показывает, как вы взаимодействуете с окружающими и строите отношения. ${interpretations.digit2.energy}.
      • Третья цифра (${fractal.digit3}) - ${interpretations.digit3.planet}: отражает ваши внутренние убеждения и духовные устремления. ${interpretations.digit3.energy}.
      • Четвёртая цифра (${fractal.digit4}) - ${interpretations.digit4.planet}: указывает на ваш жизненный путь и предназначение. ${interpretations.digit4.energy}.
      
      Взаимодействие этих энергий формирует уникальный паттерн вашего поведения, определяя, как вы реагируете на жизненные ситуации, принимаете решения и взаимодействуете с миром.
    `;

    return {
      interpretations,
      generalInterpretation
    };
  };

  // Функция для форматирования времени без миллисекунд
  const formatTime = (timeString) => {
    if (!timeString) return '';
    try {
      // Если это ISO строка с датой и временем
      if (timeString.includes('T')) {
        const timePart = timeString.split('T')[1];
        if (timePart) {
          // Убираем миллисекунды и часовой пояс, берем только HH:MM
          const cleanTime = timePart.split('.')[0].split('+')[0].split('Z')[0];
          return cleanTime.substring(0, 5); // HH:MM
        }
      }
      // Если это уже время в формате HH:MM:SS или HH:MM:SS.mmm
      if (timeString.includes(':')) {
        // Убираем миллисекунды, если есть
        const cleanTime = timeString.split('.')[0];
        // Берем только HH:MM (первые 5 символов)
        return cleanTime.substring(0, 5);
      }
      return timeString;
    } catch {
      return timeString;
    }
  };

  // Константы для визуализации
  const NUMBER_LAYOUT = [
    [1, 4, 7],  // Строка 0
    [2, 5, 8],  // Строка 1
    [3, 6, 9]   // Строка 2
  ];

  const INDEX_BY_NUMBER = {
    1: [0, 0], 4: [0, 1], 7: [0, 2],
    2: [1, 0], 5: [1, 1], 8: [1, 2],
    3: [2, 0], 6: [2, 1], 9: [2, 2]
  };

  const CELL_COLORS = {
    1: { bg: 'from-yellow-100 to-yellow-200', border: 'border-yellow-300', text: 'text-yellow-900' },
    2: { bg: 'from-slate-100 to-slate-200', border: 'border-slate-300', text: 'text-slate-900' },
    3: { bg: 'from-amber-100 to-amber-200', border: 'border-amber-300', text: 'text-amber-900' },
    4: { bg: 'from-orange-100 to-orange-200', border: 'border-orange-300', text: 'text-orange-900' },
    5: { bg: 'from-green-100 to-green-200', border: 'border-green-300', text: 'text-green-900' },
    6: { bg: 'from-pink-100 to-pink-200', border: 'border-pink-300', text: 'text-pink-900' },
    7: { bg: 'from-gray-100 to-gray-200', border: 'border-gray-300', text: 'text-gray-900' },
    8: { bg: 'from-blue-100 to-blue-200', border: 'border-blue-300', text: 'text-blue-900' },
    9: { bg: 'from-red-100 to-red-200', border: 'border-red-300', text: 'text-red-900' }
  };

  const PLANET_SYMBOLS = {
    1: '☉', 2: '☽', 3: '♃', 4: '☊', 5: '☿', 6: '♀', 7: '☋', 8: '♄', 9: '♂'
  };

  const PLANET_NAMES = {
    1: 'Солнце', 2: 'Луна', 3: 'Юпитер', 4: 'Раху', 5: 'Меркурий',
    6: 'Венера', 7: 'Кету', 8: 'Сатурн', 9: 'Марс'
  };

  // Функция для получения цвета индикатора планеты
  const getPlanetIndicatorColor = (num) => {
    const colors = {
      1: '#facc15', // yellow-400
      2: '#cbd5e1', // slate-300
      3: '#fbbf24', // amber-400
      4: '#fb923c', // orange-400
      5: '#22c55e', // green-500
      6: '#f472b6', // pink-400
      7: '#94a3b8', // slate-400
      8: '#3b82f6', // blue-500
      9: '#ef4444'  // red-500
    };
    return colors[num] || '#6b7280';
  };

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

  const WEEK_PLANETS = [
    { dayShort: 'Вс', dayLabel: 'Воскресенье', planet: 'Солнце / Surya', icon: '☉', color: '#facc15', num: 1 },
    { dayShort: 'Пн', dayLabel: 'Понедельник', planet: 'Луна / Chandra', icon: '☽', color: '#f9fafb', num: 2 },
    { dayShort: 'Вт', dayLabel: 'Вторник', planet: 'Марс / Mangala', icon: '♂', color: '#ef4444', num: 9 },
    { dayShort: 'Ср', dayLabel: 'Среда', planet: 'Меркурий / Budha', icon: '☿', color: '#22c55e', num: 5 },
    { dayShort: 'Чт', dayLabel: 'Четверг', planet: 'Юпитер / Guru', icon: '♃', color: '#fb923c', num: 3 },
    { dayShort: 'Пт', dayLabel: 'Пятница', planet: 'Венера / Shukra', icon: '♀', color: '#f472b6', num: 6 },
    { dayShort: 'Сб', dayLabel: 'Суббота', planet: 'Сатурн / Shani', icon: '♄', color: '#3b82f6', num: 8 }
  ];

  // Вычисление личной энергии по дням недели
  const personalEnergyData = useMemo(() => {
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

      const series = WEEK_PLANETS.map((meta, idx) => ({
        ...meta,
        value: values[idx] ?? 0
      }));

      // Линия реализации: все нули заменяются на 9
      const realizationSeries = series.map(day => ({
        ...day,
        value: day.value === 0 ? 9 : day.value
      }));

      const formattedProduct = baseNumber.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');

      return {
        series,
        realizationSeries,
        code: digits,
        calculation: {
          dayMonth,
          year,
          product: baseNumber,
          formattedProduct
        }
      };
    } catch {
      return null;
    }
  }, [user?.birth_date]);

  // Загрузка всех данных для отчета
  useEffect(() => {
    const fetchReportData = async () => {
      if (!user) {
        console.log('🔍 fetchReportData: user отсутствует');
        return;
      }

      try {
        console.log('🔍 fetchReportData: начинаем загрузку данных для пользователя:', user.email);
        setLoading(true);
        const token = localStorage.getItem('token');
        const headers = { 'Authorization': `Bearer ${token}` };

        // Получаем все необходимые данные параллельно
        const [
          personalData,
          pythagoreanSquare,
          planetaryEnergy,
          planetaryEnergyWeekly,
          planetaryRoute,
          savedCalculations
        ] = await Promise.all([
          // Личные данные (включая birth_date)
          fetch(`${backendUrl}/api/user/profile-v2`, { headers })
            .then(r => r.ok ? r.json() : null)
            .catch(() => null),

          // Квадрат Пифагора
          fetch(`${backendUrl}/api/numerology/pythagorean-square`, {
            method: 'POST',
            headers: { ...headers, 'Content-Type': 'application/json' }
          })
            .then(r => r.ok ? r.json() : null)
            .catch(() => null),

          // Планетарные энергии (сегодня)
          fetch(`${backendUrl}/api/charts/planetary-energy/7`, { headers })
            .then(r => r.ok ? r.json() : null)
            .catch(() => null),

          // Динамика энергий планет (неделя)
          fetch(`${backendUrl}/api/charts/planetary-energy/7`, { headers })
            .then(r => r.ok ? r.json() : null)
            .catch(() => null),

          // Планетарный маршрут (загружаем только дневной, остальные загружаются по требованию)
          fetch(`${backendUrl}/api/vedic-time/planetary-route?date=${new Date().toISOString().split('T')[0]}&city=${user.city || 'Москва'}`, { headers })
            .then(r => r.ok ? r.json() : null)
            .catch(() => null),

          // Сохранённые расчёты (совместимость, имя, адрес, автомобиль, планетарный маршрут)
          fetch(`${backendUrl}/api/numerology/saved-calculations`, { headers })
            .then(r => r.ok ? r.json() : null)
            .catch(() => null)
        ]);

        // Создаем персональные числа из birth_date (без списания баллов)
        let personalNumbers = {};
        console.log('🔍 fetchReportData: проверяем personalData:', {
          hasPersonalData: !!personalData,
          birthDate: personalData?.birth_date,
          birthDateType: typeof personalData?.birth_date,
          hasHyphen: personalData?.birth_date?.includes('-')
        });
        
        if (personalData && personalData.birth_date && typeof personalData.birth_date === 'string') {
          try {
            // Нормализуем формат даты (может быть YYYY-MM-DD или DD.MM.YYYY)
            let normalizedDate = personalData.birth_date;
            if (normalizedDate.includes('.')) {
              // Формат DD.MM.YYYY -> YYYY-MM-DD
              const [dd, mm, yyyy] = normalizedDate.split('.');
              normalizedDate = `${yyyy}-${mm.padStart(2, '0')}-${dd.padStart(2, '0')}`;
            }
            
            // Простой расчет персональных чисел (душа, ум, судьба)
            const [yyyy, mm, dd] = normalizedDate.split('-');
            if (yyyy && mm && dd) {
              const dayDigits = dd.split('').map(n=>parseInt(n,10));
              const monthDigits = mm.split('').map(n=>parseInt(n,10));
              const yearDigits = yyyy.split('').map(n=>parseInt(n,10));

              const sum = arr => arr.reduce((a,b)=>a+b,0);
              const reduce = n => { let x=n; while(x>9){ x = x.toString().split('').reduce((a,b)=>a+parseInt(b,10),0);} return x; };
              // Функция для числа судьбы - всегда сводит к одной цифре, без мастер-чисел
              const reduceDestiny = n => { let x=n; while(x>9){ x = x.toString().split('').reduce((a,b)=>a+parseInt(b,10),0);} return x; };

              const destinySum = sum([...dayDigits,...monthDigits,...yearDigits]);
              
              // Правящее число: сумма всех цифр даты рождения (день + месяц + год)
              const rulingSum = sum([...dayDigits, ...monthDigits, ...yearDigits]);
              const reduceForRuling = (n) => {
                if (n === 11 || n === 22) return n;
                let x = n;
                while (x > 9) {
                  x = String(x).split('').reduce((a, b) => a + parseInt(b, 10), 0);
                  if (x === 11 || x === 22) return x;
                }
                return x;
              };
              const rulingNumber = reduceForRuling(rulingSum);
              
              // Логируем для отладки
              console.log('🔢 Пересчёт Правящего числа на фронтенде:', {
                birth_date: personalData.birth_date,
                dayDigits,
                monthDigits,
                yearDigits,
                rulingSum,
                rulingNumber
              });

              personalNumbers = {
                birth_date: normalizedDate, // Сохраняем нормализованную дату
                soul_number: reduce(sum(dayDigits)),
                mind_number: reduce(sum(monthDigits)),
                destiny_number: reduceDestiny(destinySum), // Всегда сводится к одной цифре, без мастер-чисел
                helping_mind_number: reduce(sum([...dayDigits, ...monthDigits])),
                full_name_number: personalData.full_name ? reduce(personalData.full_name.replace(/\s+/g, '').split('').reduce((sum, char) => sum + (char.charCodeAt(0) - 96), 0)) : null,
                ruling_number: rulingNumber // Пересчитываем на фронтенде
              };
              
              console.log('✅ personalNumbers создан успешно:', personalNumbers);
            } else {
              console.warn('⚠️ fetchReportData: не удалось создать personalNumbers - неверный формат даты');
            }
          } catch (e) {
            console.error('❌ Error calculating personal numbers:', e);
          }
        } else {
          console.warn('⚠️ fetchReportData: personalNumbers не создан:', {
            hasPersonalData: !!personalData,
            hasBirthDate: !!personalData?.birth_date,
            birthDate: personalData?.birth_date
          });
        }

        // Извлекаем сохранённые данные
        const savedCompatibility = savedCalculations?.compatibility?.results || null;
        const savedNameNumerology = savedCalculations?.name_numerology?.results || null;
        const savedAddressNumerology = savedCalculations?.address_numerology?.results || null;
        const savedCarNumerology = savedCalculations?.car_numerology?.results || null;
        const savedPlanetaryRoute = savedCalculations?.planetary_route_daily?.results || planetaryRoute;

        // Убеждаемся, что pythagoreanSquare использует правильное ruling_number
        if (pythagoreanSquare && personalNumbers.ruling_number) {
          pythagoreanSquare.ruling_number = personalNumbers.ruling_number;
        }

        console.log('🔍 fetchReportData: данные загружены, сохраняем в reportData:', {
          hasPersonalData: !!personalData,
          personalDataBirthDate: personalData?.birth_date,
          hasPersonalNumbers: !!personalNumbers,
          personalNumbersKeys: personalNumbers ? Object.keys(personalNumbers) : [],
          personalNumbersRuling: personalNumbers?.ruling_number,
          personalNumbersBirthDate: personalNumbers?.birth_date,
          hasPythagoreanSquare: !!pythagoreanSquare,
          pythagoreanSquareKeys: pythagoreanSquare ? Object.keys(pythagoreanSquare) : [],
          pythagoreanSquareRuling: pythagoreanSquare?.ruling_number,
          hasSquare: !!pythagoreanSquare?.square
        });

        // Если personalNumbers пустой, но есть personalData с birth_date, попробуем создать его
        if (!personalNumbers || Object.keys(personalNumbers).length === 0) {
          if (personalData?.birth_date) {
            console.warn('⚠️ personalNumbers пустой, но есть birth_date, пытаемся создать заново...');
            // Попробуем создать personalNumbers из personalData.birth_date
            try {
              const bd = personalData.birth_date;
              // Поддерживаем оба формата
              let normalizedDate = bd;
              if (bd.includes('.')) {
                const [dd, mm, yyyy] = bd.split('.');
                normalizedDate = `${yyyy}-${mm.padStart(2, '0')}-${dd.padStart(2, '0')}`;
              }
              const [yyyy, mm, dd] = normalizedDate.split('-');
              if (yyyy && mm && dd) {
                const dayDigits = dd.split('').map(n=>parseInt(n,10));
                const monthDigits = mm.split('').map(n=>parseInt(n,10));
                const yearDigits = yyyy.split('').map(n=>parseInt(n,10));
                const sum = arr => arr.reduce((a,b)=>a+b,0);
                const reduce = n => { let x=n; while(x>9){ x = x.toString().split('').reduce((a,b)=>a+parseInt(b,10),0);} return x; };
                const reduceDestiny = n => { let x=n; while(x>9){ x = x.toString().split('').reduce((a,b)=>a+parseInt(b,10),0);} return x; };
                const destinySum = sum([...dayDigits,...monthDigits,...yearDigits]);
                const rulingSum = sum([...dayDigits, ...monthDigits, ...yearDigits]);
                const reduceForRuling = (n) => {
                  if (n === 11 || n === 22) return n;
                  let x = n;
                  while (x > 9) {
                    x = String(x).split('').reduce((a, b) => a + parseInt(b, 10), 0);
                    if (x === 11 || x === 22) return x;
                  }
                  return x;
                };
                const rulingNumber = reduceForRuling(rulingSum);
                personalNumbers = {
                  birth_date: normalizedDate,
                  soul_number: reduce(sum(dayDigits)),
                  mind_number: reduce(sum(monthDigits)),
                  destiny_number: reduceDestiny(destinySum),
                  helping_mind_number: reduce(sum([...dayDigits, ...monthDigits])),
                  full_name_number: personalData.full_name ? reduce(personalData.full_name.replace(/\s+/g, '').split('').reduce((sum, char) => sum + (char.charCodeAt(0) - 96), 0)) : null,
                  ruling_number: rulingNumber
                };
                console.log('✅ personalNumbers создан заново:', personalNumbers);
              }
            } catch (e) {
              console.error('❌ Ошибка при создании personalNumbers:', e);
            }
          }
        }

        setReportData({
          personal: personalData,
          numerology: { personal_numbers: personalNumbers },
          pythagoreanSquare: pythagoreanSquare,
          planetaryEnergy: planetaryEnergy,
          planetaryEnergyWeekly: planetaryEnergyWeekly,
          planetaryRoute: savedPlanetaryRoute || planetaryRoute,
          vedic: null,
          compatibility: savedCompatibility,
          nameNumerology: savedNameNumerology,
          addressNumerology: savedAddressNumerology,
          carNumerology: savedCarNumerology
        });

        // Сохраняем дневной маршрут
        if (planetaryRoute) {
          setRouteData(prev => ({ ...prev, daily: planetaryRoute }));
        }

      } catch (error) {
        console.error('Ошибка загрузки данных отчета:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchReportData();
  }, [user, backendUrl]);

  // Загрузка планетарного маршрута для разных периодов
  const loadRouteData = async (period) => {
    if (routeData[period]) return; // Уже загружено

    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };
      const today = new Date().toISOString().split('T')[0];
      const city = user?.city || 'Москва';

      let endpoint = `${backendUrl}/api/vedic-time/planetary-route`;
      if (period === 'weekly') {
        endpoint += '/weekly';
      } else if (period === 'monthly') {
        endpoint += '/monthly';
      } else if (period === 'quarterly') {
        endpoint += '/quarterly';
      }

      const response = await fetch(`${endpoint}?date=${today}&city=${city}`, { headers });
      if (response.ok) {
        const data = await response.json();
        setRouteData(prev => ({ ...prev, [period]: data }));
      }
    } catch (error) {
      console.error(`Ошибка загрузки маршрута на ${period}:`, error);
    }
  };

  // Загружаем данные при смене периода
  useEffect(() => {
    if (routePeriod && routePeriod !== 'daily') {
      loadRouteData(routePeriod);
    }
  }, [routePeriod, user]);

  // Загрузка данных динамики энергий планет
  const loadEnergyData = async (period, date) => {
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };
      
      let days = 7;
      if (period === 'monthly') days = 30;
      else if (period === 'quarterly') days = 90;

      const response = await fetch(`${backendUrl}/api/charts/planetary-energy/${days}`, { headers });
      if (response.ok) {
        const data = await response.json();
        setEnergyData(data);
      }
    } catch (error) {
      console.error('Ошибка загрузки данных энергий:', error);
    }
  };

  // Загружаем данные при смене периода или даты
  useEffect(() => {
    if (energyPeriod) {
      loadEnergyData(energyPeriod, energyDate);
    }
  }, [energyPeriod, energyDate, user]);

  // Переключение темы
  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  // Экспорт в PDF
  const exportToPDF = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/reports/pdf/numerology`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          selected_calculations: ['personal_numbers', 'pythagorean_square', 'name_numerology', 'address_numerology', 'car_numerology', 'vedic_times', 'planetary_route', 'compatibility'],
          include_vedic: true,
          include_charts: true,
          theme: theme
        })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `numerom_comprehensive_report_${user?.id || 'user'}_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      } else {
        console.error('Ошибка экспорта PDF');
      }
    } catch (error) {
      console.error('Ошибка экспорта:', error);
    }
  };

  // Экспорт в HTML
  const exportToHTML = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/reports/html/numerology`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          selected_calculations: ['personal_numbers', 'pythagorean_square', 'name_numerology', 'address_numerology', 'car_numerology', 'vedic_times', 'planetary_route', 'compatibility'],
          include_vedic: true,
          include_charts: true,
          theme: theme
        })
      });

      if (response.ok) {
        const htmlContent = await response.text();
        const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `numerom_comprehensive_report_${user?.id || 'user'}_${new Date().toISOString().split('T')[0]}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      } else {
        console.error('Ошибка экспорта HTML');
      }
    } catch (error) {
      console.error('Ошибка экспорта:', error);
    }
  };

  // Вспомогательная функция: пересчитать суммы по квадрату, если их нет в данных
  const computePythagoreanSums = (square) => {
    try {
      if (!square || !Array.isArray(square) || square.length !== 3) {
        return { h: [0, 0, 0], v: [0, 0, 0], d: [0, 0] };
      }
      const countLen = (cell) => {
        if (!cell) return 0;
        if (typeof cell === 'string') return cell.length;
        if (Array.isArray(cell)) return cell.length;
        return String(cell).length;
      };
      const h = [0, 0, 0];
      const v = [0, 0, 0];
      for (let r = 0; r < 3; r += 1) {
        for (let c = 0; c < 3; c += 1) {
          const len = countLen(square[r]?.[c]);
          h[r] += len;
          v[c] += len;
        }
      }
      const d = [countLen(square[0]?.[0]) + countLen(square[1]?.[1]) + countLen(square[2]?.[2]),
                 countLen(square[0]?.[2]) + countLen(square[1]?.[1]) + countLen(square[2]?.[0])];
      return { h, v, d };
    } catch {
      return { h: [0, 0, 0], v: [0, 0, 0], d: [0, 0] };
    }
  };

  // Подсветка цифр при наведении в методологии
  const chipStyleForDigit = (d) => {
    if (d === 0) {
      return {
        cls: `bg-gray-100 border-gray-300 text-gray-700 ${hoveredDigit===0?'ring-2 ring-gray-300':''}`,
        style: {}
      };
    }
    const colorCfg = CELL_COLORS[d] || { text: 'text-gray-800' };
    const activeRing = hoveredDigit === d ? ' ring-2 ring-amber-400' : '';
    // Простой однотонный фон для чипов
    const baseBg = d===1? 'bg-amber-100' : d===2? 'bg-gray-100' : d===3? 'bg-yellow-100' : d===4? 'bg-amber-200' : d===5? 'bg-emerald-100' : d===6? 'bg-pink-100' : d===7? 'bg-slate-100' : d===8? 'bg-blue-100' : 'bg-red-100';
    const baseBorder = d===1? 'border-amber-300' : d===2? 'border-gray-300' : d===3? 'border-yellow-300' : d===4? 'border-amber-300' : d===5? 'border-emerald-300' : d===6? 'border-pink-300' : d===7? 'border-slate-300' : d===8? 'border-blue-300' : 'border-red-300';
    const baseText = colorCfg.text || 'text-gray-800';
    return {
      cls: `${baseBg} ${baseText} border ${baseBorder}${activeRing}`,
      style: {}
    };
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">Формируем ваш персональный отчет...</p>
        </div>
      </div>
    );
  }

  if (!reportData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="p-6 text-center">
            <p className="text-red-600 mb-4">Не удалось загрузить данные отчета</p>
            <Button onClick={() => window.location.reload()}>
              Попробовать снова
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-gray-900 text-white' : 'bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50'}`}>
      {/* Шапка с контролами */}
      <div className="sticky top-0 z-50 bg-white/80 backdrop-blur-sm border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Персональный Отчет NUMEROM
              </h1>
              <p className="text-gray-600 mt-1">
                Полный анализ вашей нумерологической карты
              </p>
            </div>

            <div className="flex items-center gap-3">
              {/* Переключатель темы */}
              <Button
                variant="outline"
                size="sm"
                onClick={toggleTheme}
                className="flex items-center gap-2"
              >
                {theme === 'light' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
                {theme === 'light' ? 'Темная' : 'Светлая'}
              </Button>

              {/* Кнопки экспорта */}
              <Button
                variant="outline"
                size="sm"
                onClick={exportToHTML}
                className="flex items-center gap-2"
              >
                <FileText className="w-4 h-4" />
                HTML
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={exportToPDF}
                className="flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                PDF
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          {/* Навигация по разделам */}
          <TabsList className="grid w-full grid-cols-2 lg:grid-cols-4 xl:grid-cols-9 gap-2 p-1 bg-white/50 backdrop-blur-sm">
            <TabsTrigger value="overview" className="text-xs sm:text-sm">
              <User className="w-4 h-4 mr-1" />
              Обзор
            </TabsTrigger>
            <TabsTrigger value="charts" className="text-xs sm:text-sm">
              <BarChart3 className="w-4 h-4 mr-1" />
              Графики
            </TabsTrigger>
            <TabsTrigger value="calculations" className="text-xs sm:text-sm">
              <Calculator className="w-4 h-4 mr-1" />
              Расчёты
            </TabsTrigger>
            <TabsTrigger value="planetary" className="text-xs sm:text-sm">
              <TrendingUp className="w-4 h-4 mr-1" />
              Планеты
            </TabsTrigger>
            <TabsTrigger value="route" className="text-xs sm:text-sm">
              <MapPin className="w-4 h-4 mr-1" />
              Маршрут
            </TabsTrigger>
            <TabsTrigger value="compatibility" className="text-xs sm:text-sm">
              <Users className="w-4 h-4 mr-1" />
              Совместимость
            </TabsTrigger>
            <TabsTrigger value="name" className="text-xs sm:text-sm">
              <Star className="w-4 h-4 mr-1" />
              Имя
            </TabsTrigger>
            <TabsTrigger value="address" className="text-xs sm:text-sm">
              <MapPin className="w-4 h-4 mr-1" />
              Адрес
            </TabsTrigger>
            <TabsTrigger value="car" className="text-xs sm:text-sm">
              <Car className="w-4 h-4 mr-1" />
              Авто
            </TabsTrigger>
          </TabsList>

          {/* Вкладка: Обзор */}
          <TabsContent value="overview" className="space-y-6">
            <div className="space-y-6">
              {/* Личная информация */}
              <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="w-5 h-5 text-blue-600" />
                    Личная информация
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-600">Имя</label>
                      <p className="text-lg font-semibold">{reportData.personal?.name || user?.name || 'Не указано'}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Фамилия</label>
                      <p className="text-lg font-semibold">{reportData.personal?.surname || user?.surname || 'Не указано'}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Email</label>
                      <p className="text-base">{user?.email}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Дата рождения</label>
                      <p className="text-base flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        {reportData.personal?.birth_date ? formatDate(reportData.personal.birth_date) : 'Не указана'}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Ключевые числа */}
              <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Star className="w-5 h-5 text-purple-600" />
                    Ключевые числа
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {(() => {
                    const personalNumbers = reportData.numerology?.personal_numbers;
                    const birthDate = user?.birth_date || reportData.personal?.birth_date;
                    const fractal = birthDate ? calculateBehaviorFractal(birthDate) : null;
                    
                    if (!personalNumbers) return null;
                    
                    // Пересчитываем Правящее число на фронтенде
                    let calculatedRulingNumber = null;
                    if (birthDate) {
                      try {
                        const dateStr = birthDate.includes('-') ? birthDate : birthDate.split('.').reverse().join('-');
                        const [yyyy, mm, dd] = dateStr.split('-');
                        if (yyyy && mm && dd) {
                          const dayDigits = dd.split('').map(n => parseInt(n, 10));
                          const monthDigits = mm.split('').map(n => parseInt(n, 10));
                          const yearDigits = yyyy.split('').map(n => parseInt(n, 10));
                          const sum = arr => arr.reduce((a, b) => a + b, 0);
                          const rulingSum = sum([...dayDigits, ...monthDigits, ...yearDigits]);
                          const reduceForRuling = (n) => {
                            if (n === 11 || n === 22) return n;
                            let x = n;
                            while (x > 9) {
                              x = String(x).split('').reduce((a, b) => a + parseInt(b, 10), 0);
                              if (x === 11 || x === 22) return x;
                            }
                            return x;
                          };
                          calculatedRulingNumber = reduceForRuling(rulingSum);
                        }
                      } catch (e) {
                        console.error('Ошибка расчёта Правящего числа:', e);
                      }
                    }
                    
                    return (
                      <div className="space-y-6">
                        {/* Фрактал поведения */}
                        {fractal && (
                          <div>
                            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Фрактал поведения</h4>
                            <div className="flex items-center justify-center gap-3 flex-wrap">
                              {[
                                { digit: fractal.digit1, label: 'День', position: 1 },
                                { digit: fractal.digit2, label: 'Месяц', position: 2 },
                                { digit: fractal.digit3, label: 'Год', position: 3 },
                                { digit: fractal.digit4, label: 'Сумма', position: 4 }
                              ].map((item, idx) => {
                                const color = getPlanetIndicatorColor(item.digit);
                                return (
                                  <div key={idx} className="flex flex-col items-center">
                                    <div
                                      className="w-16 h-16 rounded-xl flex items-center justify-center text-3xl font-bold shadow-lg border-2 transition-all"
                                      style={{
                                        backgroundColor: color + '25',
                                        borderColor: color,
                                        color: color,
                                        boxShadow: `0 4px 6px -1px ${color}40, 0 2px 4px -1px ${color}20`
                                      }}
                                    >
                                      {item.digit}
                                    </div>
                                    <div className="text-xs font-medium mt-2 text-center max-w-[60px] px-2 py-1 rounded"
                                      style={{
                                        color: color,
                                        backgroundColor: color + '15'
                                      }}
                                    >
                                      {item.label}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                        
                        {/* Основные числа */}
                        <div>
                          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Персональные числа</h4>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                            {[
                              { key: 'soul_number', label: 'Число души (ЧД)', value: personalNumbers.soul_number },
                              { key: 'mind_number', label: 'Число ума (ЧУ)', value: personalNumbers.mind_number },
                              { key: 'destiny_number', label: 'Число судьбы (ЧС)', value: personalNumbers.destiny_number },
                              { key: 'wisdom_number', label: 'Число мудрости (ЧМ)', value: personalNumbers.wisdom_number },
                              { key: 'ruling_number', label: 'Правящее число (ПЧ)', value: calculatedRulingNumber !== null ? calculatedRulingNumber : personalNumbers.ruling_number }
                            ].filter(item => item.value !== null && item.value !== undefined).map((item) => {
                              const color = getPlanetIndicatorColor(item.value);
                              return (
                                <div key={item.key} className="text-center p-4 rounded-lg border-2 transition-all hover:shadow-lg"
                                  style={{
                                    borderColor: color,
                                    backgroundColor: color + '15'
                                  }}
                                >
                                  <div className="text-3xl font-bold mb-2" style={{ color: color }}>
                                    {item.value}
                                  </div>
                                  <div className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                    {item.label}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    );
                  })()}
                </CardContent>
              </Card>
            </div>

            {/* Краткий обзор всех разделов */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                <CardContent className="p-4 text-center">
                  <BarChart3 className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                  <h3 className="font-semibold">Графики</h3>
                  <p className="text-sm text-gray-600">Пифагорейский квадрат и планетарные энергии</p>
                </CardContent>
              </Card>

              <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                <CardContent className="p-4 text-center">
                  <TrendingUp className="w-8 h-8 text-green-600 mx-auto mb-2" />
                  <h3 className="font-semibold">Планетарный маршрут</h3>
                  <p className="text-sm text-gray-600">Ежедневные рекомендации</p>
                </CardContent>
              </Card>

              <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                <CardContent className="p-4 text-center">
                  <Users className="w-8 h-8 text-pink-600 mx-auto mb-2" />
                  <h3 className="font-semibold">Совместимость</h3>
                  <p className="text-sm text-gray-600">Личная и групповая</p>
                </CardContent>
              </Card>

              <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                <CardContent className="p-4 text-center">
                  <Star className="w-8 h-8 text-orange-600 mx-auto mb-2" />
                  <h3 className="font-semibold">Нумерология</h3>
                  <p className="text-sm text-gray-600">Имя, адрес, автомобиль</p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Вкладка: Графики */}
          <TabsContent value="charts" className="space-y-6">
            <div className="space-y-6">
              {/* Личная энергия по дням недели */}
              <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                <CardHeader>
                  <CardTitle>Личная энергия по дням недели</CardTitle>
                  <CardDescription>
                    Числовой код строится по формуле DDMM × YYYY. Первые семь цифр распределяются по дням недели, начиная с дня рождения
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {personalEnergyData ? (
                  <div className="space-y-6">
                    {/* Код и расчёт */}
                    <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg p-4 border border-indigo-200">
                      <div className="text-sm font-medium text-gray-700 mb-2">Код</div>
                      <div className="text-2xl font-bold text-indigo-600 mb-3">{personalEnergyData.code}</div>
                      <div className="text-xs text-gray-600 mb-3">
                        {personalEnergyData.calculation.dayMonth} × {personalEnergyData.calculation.year} = {personalEnergyData.calculation.formattedProduct}
                      </div>
                      <div className="mt-4 pt-4 border-t border-indigo-200">
                        <div className="text-sm font-semibold text-gray-800 mb-2">Алгоритм вычисления:</div>
                        <div className="text-xs text-gray-700 space-y-1.5">
                          <div>1. Берём день и месяц рождения: <span className="font-mono font-semibold">{personalEnergyData.calculation.dayMonth}</span></div>
                          <div>2. Умножаем на год рождения: <span className="font-mono font-semibold">{personalEnergyData.calculation.dayMonth} × {personalEnergyData.calculation.year}</span></div>
                          <div>3. Получаем произведение: <span className="font-mono font-semibold">{personalEnergyData.calculation.formattedProduct}</span></div>
                          <div>4. Берём первые 7 цифр результата: <span className="font-mono font-semibold">{personalEnergyData.code}</span></div>
                          <div>5. Распределяем эти цифры по дням недели, начиная с дня вашего рождения</div>
                          <div className="mt-2 pt-2 border-t border-indigo-100">
                            <span className="font-semibold text-amber-600">💡 Важно:</span> Если энергия дня равна <span className="font-mono font-semibold">0</span>, это означает потенциал для реализации до <span className="font-mono font-semibold">9</span>. Зелёная линия на графике показывает максимальный потенциал реализации.
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Карточки дней недели */}
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
                      {personalEnergyData.series.map((day, idx) => (
                        <div
                          key={idx}
                          className={`p-4 rounded-lg border-2 transition-all hover:shadow-lg ${
                            hoveredPlanetEnergy === idx ? 'ring-4 ring-amber-400 ring-offset-2 scale-105' : ''
                          }`}
                          style={{
                            borderColor: day.color,
                            backgroundColor: `${day.color}15`
                          }}
                        >
                          <div className="text-center">
                            <div className="text-xs font-medium text-gray-600 mb-1">{day.dayShort}</div>
                            <div className="text-xs text-gray-500 mb-2">{day.dayLabel}</div>
                            <div className="text-2xl mb-2" style={{ color: day.color }}>
                              {day.icon}
                            </div>
                            <div className="text-xs text-gray-600 mb-2">{day.planet}</div>
                            <div className="text-3xl font-bold" style={{ color: day.color }}>
                              {day.value}
                            </div>
                            <div className="text-xs text-gray-500 mt-1">
                              {day.value === 0 ? (
                                <span className="text-green-600 font-semibold">Потенциал: 9</span>
                              ) : (
                                'Энергия'
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* График */}
                    <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 border border-gray-300 dark:border-gray-600">
                      <Line
                        data={{
                          labels: personalEnergyData.series.map(d => d.dayShort),
                          datasets: [
                            {
                              label: 'Энергия дня',
                              data: personalEnergyData.series.map(d => d.value),
                              borderColor: '#22d3ee',
                              backgroundColor: 'rgba(34,211,238,0.18)',
                              borderWidth: 3,
                              pointBackgroundColor: personalEnergyData.series.map((d, idx) => 
                                hoveredPlanetEnergy === idx ? '#fbbf24' : d.color
                              ),
                              pointBorderColor: personalEnergyData.series.map((d, idx) => 
                                hoveredPlanetEnergy === idx ? '#fbbf24' : d.color
                              ),
                              pointBorderWidth: personalEnergyData.series.map((d, idx) => 
                                hoveredPlanetEnergy === idx ? 3 : 2
                              ),
                              pointRadius: personalEnergyData.series.map((d, idx) => 
                                hoveredPlanetEnergy === idx ? 12 : 8
                              ),
                              pointHoverRadius: 12,
                              tension: 0.45,
                              fill: {
                                target: 'origin',
                                above: 'rgba(34,211,238,0.12)'
                              }
                            },
                            {
                              label: 'Потенциал реализации',
                              data: personalEnergyData.realizationSeries.map(d => d.value),
                              borderColor: '#10b981',
                              backgroundColor: 'rgba(16,185,129,0.1)',
                              borderWidth: 2,
                              borderDash: [5, 5],
                              pointBackgroundColor: personalEnergyData.realizationSeries.map((d, idx) => 
                                hoveredPlanetEnergy === idx ? '#fbbf24' : '#10b981'
                              ),
                              pointBorderColor: personalEnergyData.realizationSeries.map((d, idx) => 
                                hoveredPlanetEnergy === idx ? '#fbbf24' : '#10b981'
                              ),
                              pointBorderWidth: personalEnergyData.realizationSeries.map((d, idx) => 
                                hoveredPlanetEnergy === idx ? 3 : 2
                              ),
                              pointRadius: personalEnergyData.realizationSeries.map((d, idx) => 
                                hoveredPlanetEnergy === idx ? 10 : 6
                              ),
                              pointHoverRadius: 10,
                              tension: 0.45,
                              fill: false
                            }
                          ]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          interaction: {
                            mode: 'index',
                            intersect: false
                          },
                          onHover: (event, activeElements) => {
                            if (activeElements.length > 0) {
                              const dataIndex = activeElements[0].index;
                              setHoveredPlanetEnergy(dataIndex);
                            } else {
                              setHoveredPlanetEnergy(null);
                            }
                          },
                          plugins: {
                            legend: { 
                              display: true,
                              position: 'top',
                              labels: {
                                usePointStyle: true,
                                padding: 15,
                                font: {
                                  size: 12
                                }
                              }
                            },
                            tooltip: {
                              callbacks: {
                                label: (context) => {
                                  const day = personalEnergyData.series[context.dataIndex];
                                  if (context.datasetIndex === 0) {
                                    return `${day.dayLabel} • ${day.planet}: ${context.parsed.y}${day.value === 0 ? ' (потенциал до 9)' : ''}`;
                                  } else {
                                    return `Потенциал реализации: ${context.parsed.y}`;
                                  }
                                }
                              }
                            }
                          },
                          scales: {
                            y: {
                              beginAtZero: true,
                              min: 0,
                              max: 10,
                              ticks: { 
                                stepSize: 1,
                                precision: 0,
                                callback: function(value) {
                                  // Показываем все целые значения от 0 до 10
                                  if (Number.isInteger(value) && value >= 0 && value <= 10) {
                                    return value;
                                  }
                                  return '';
                                }
                              },
                              afterBuildTicks: function(scale) {
                                // Явно устанавливаем все деления от 0 до 10 без пропусков
                                scale.ticks = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(v => ({ value: v }));
                              },
                              grid: { 
                                color: 'rgba(100,116,139,0.4)',
                                lineWidth: 1
                              }
                            },
                            x: {
                              grid: { 
                                color: 'rgba(100,116,139,0.4)',
                                lineWidth: 1
                              }
                            }
                          }
                        }}
                        height={200}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-64 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg">
                    <div className="text-center">
                      <Calendar className="w-12 h-12 text-indigo-600 mx-auto mb-2" />
                      <p className="text-gray-600">Загрузка данных...</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Динамика энергий планет */}
            <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
              <CardHeader>
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  <div>
                    <CardTitle className="text-2xl mb-2">Динамика энергий планет</CardTitle>
                    <CardDescription className="text-base">
                      Линия показывает изменение энергетики по дням. Выберите интересующий период, чтобы увидеть, как меняются силы планет.
                    </CardDescription>
                  </div>
                  {/* Кнопка показа алгоритма */}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const algorithmCard = document.getElementById('energy-algorithm');
                      if (algorithmCard) {
                        algorithmCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
                      }
                    }}
                  >
                    <BarChart3 className="w-4 h-4 mr-2" />
                    Показать алгоритм расчёта
                  </Button>
                  <div className="flex flex-col gap-3">
                    {/* Навигация по датам */}
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          const newDate = new Date(energyDate);
                          const days = energyPeriod === 'weekly' ? 7 : energyPeriod === 'monthly' ? 30 : 90;
                          newDate.setDate(newDate.getDate() - days);
                          setEnergyDate(newDate);
                        }}
                      >
                        <ChevronLeft className="w-4 h-4" />
                      </Button>
                      <div className="flex items-center gap-2 border rounded-md px-3 py-1.5">
                        <input
                          type="date"
                          value={energyDate.toISOString().split('T')[0]}
                          onChange={(e) => setEnergyDate(new Date(e.target.value))}
                          className="bg-transparent border-none outline-none text-sm"
                        />
                        <Calendar className="w-4 h-4 text-gray-500" />
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          const newDate = new Date(energyDate);
                          const days = energyPeriod === 'weekly' ? 7 : energyPeriod === 'monthly' ? 30 : 90;
                          newDate.setDate(newDate.getDate() + days);
                          setEnergyDate(newDate);
                        }}
                      >
                        <ChevronRight className="w-4 h-4" />
                      </Button>
                    </div>
                    {/* Выбор периода */}
                    <div className="flex flex-col gap-1">
                      <Button
                        variant={energyPeriod === 'weekly' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setEnergyPeriod('weekly')}
                        className="w-full"
                      >
                        Неделя
                      </Button>
                      <Button
                        variant={energyPeriod === 'monthly' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setEnergyPeriod('monthly')}
                        className="w-full"
                      >
                        Месяц
                      </Button>
                      <Button
                        variant={energyPeriod === 'quarterly' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setEnergyPeriod('quarterly')}
                        className="w-full"
                      >
                        Квартал
                      </Button>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {energyData?.chart_data ? (
                  <div className="space-y-4">
                    {/* Период */}
                    <div className="text-sm text-gray-600">
                      Период: {formatDate(energyData.chart_data[0]?.date)} — {formatDate(energyData.chart_data[energyData.chart_data.length - 1]?.date)}
                    </div>
                    
                    {/* Управление видимостью планет */}
                    <div className="flex flex-wrap items-center gap-2 mb-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setVisiblePlanets({
                            surya: false,
                            chandra: false,
                            mangal: false,
                            budha: false,
                            guru: false,
                            shukra: false,
                            shani: false,
                            rahu: false,
                            ketu: false
                          });
                        }}
                      >
                        Выключить все
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setVisiblePlanets({
                            surya: true,
                            chandra: true,
                            mangal: true,
                            budha: true,
                            guru: true,
                            shukra: true,
                            shani: true,
                            rahu: true,
                            ketu: true
                          });
                        }}
                      >
                        Включить все
                      </Button>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries({
                          surya: { label: 'Surya (☉)', num: 1 },
                          chandra: { label: 'Chandra (☽)', num: 2 },
                          guru: { label: 'Guru (♃)', num: 3 },
                          rahu: { label: 'Rahu (☊)', num: 4 },
                          budha: { label: 'Budha (☿)', num: 5 },
                          shukra: { label: 'Shukra (♀)', num: 6 },
                          ketu: { label: 'Ketu (☋)', num: 7 },
                          shani: { label: 'Shani (♄)', num: 8 },
                          mangal: { label: 'Mangal (♂)', num: 9 }
                        }).map(([key, { label, num }]) => {
                          const isActive = visiblePlanets[key];
                          const isHovered = hoveredPlanetsOnChart.includes(key);
                          const colorConfig = CELL_COLORS[num];
                          
                          return (
                            <Button
                              key={key}
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setVisiblePlanets(prev => ({
                                  ...prev,
                                  [key]: !prev[key]
                                }));
                              }}
                              className={`transition-all duration-200 ${
                                isActive 
                                  ? `border-2 shadow-md font-semibold bg-gradient-to-br ${colorConfig.bg} ${colorConfig.border}` 
                                  : 'opacity-40 border-opacity-30'
                              } ${
                                isHovered ? 'ring-4 ring-amber-400 ring-offset-2 scale-105 z-10' : ''
                              }`}
                              style={isActive ? {
                                ...(isHovered ? { opacity: 1 } : {})
                              } : {
                                backgroundColor: 'transparent',
                                ...(isHovered ? { opacity: 0.8 } : {})
                              }}
                            >
                              <div className="flex items-center gap-2">
                                <div
                                  className={`w-3 h-3 rounded-full transition-all duration-200 ${
                                    isActive ? 'ring-2 ring-offset-1' : ''
                                  }`}
                                  style={{ 
                                    backgroundColor: getPlanetIndicatorColor(num),
                                    ringColor: getPlanetIndicatorColor(num),
                                    opacity: isActive ? 1 : 0.4
                                  }}
                                />
                                <span className={isActive ? colorConfig.text : ''}>{label}</span>
                              </div>
                            </Button>
                          );
                        })}
                      </div>
                    </div>

                    {/* Дата рождения над графиком */}
                    {(user?.birth_date || reportData.personal?.birth_date) && (() => {
                      const birthDate = user?.birth_date || reportData.personal?.birth_date;
                      const dayOfWeek = getDayOfWeek(birthDate);
                      const formatBirthDate = (dateStr) => {
                        if (!dateStr) return '';
                        // Если дата в формате ДД.ММ.ГГГГ
                        if (dateStr.includes('.')) {
                          return dateStr;
                        }
                        // Если дата в формате YYYY-MM-DD
                        if (dateStr.includes('-')) {
                          const [year, month, day] = dateStr.split('-');
                          return `${day}.${month}.${year}`;
                        }
                        return dateStr;
                      };
                      const formattedDate = formatBirthDate(birthDate);
                      const digits = formattedDate.replace(/[^0-9]/g, '').split('');
                      
                      return (
                        <div className="mb-4 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                          <div className="flex items-center gap-3 flex-wrap">
                            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Дата рождения:</span>
                            <div className="flex items-center gap-1">
                              {formattedDate.split('').map((char, idx) => {
                                if (char === '.' || char === '-') {
                                  return <span key={idx} className="text-gray-700 dark:text-gray-300">{char}</span>;
                                }
                                const digit = parseInt(char, 10);
                                if (isNaN(digit)) return <span key={idx}>{char}</span>;
                                const color = CELL_COLORS[digit] || '#000';
                                return (
                                  <span
                                    key={idx}
                                    className="text-2xl font-bold px-1 rounded"
                                    style={{
                                      color: color,
                                      backgroundColor: color + '15'
                                    }}
                                  >
                                    {char}
                                  </span>
                                );
                              })}
                            </div>
                            {dayOfWeek && (
                              <>
                                <span className="text-gray-400 dark:text-gray-500">•</span>
                                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{dayOfWeek}</span>
                              </>
                            )}
                          </div>
                        </div>
                      );
                    })()}

                    {/* График */}
                    <div 
                      className={`${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'} rounded-lg p-6 border ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}
                      onMouseMove={(e) => {
                        if (chartRef.current) {
                          const chartInstance = chartRef.current.chartInstance || chartRef.current;
                          if (chartInstance) {
                            const elements = getElementAtEvent(chartInstance, e.nativeEvent || e);
                            if (elements && elements.length > 0) {
                              // Берём только ближайший элемент (первый в массиве) - конкретную планету под курсором
                              const element = elements[0];
                              const datasetIndex = element.datasetIndex;
                              const planetOrder = ['surya', 'chandra', 'guru', 'rahu', 'budha', 'shukra', 'ketu', 'shani', 'mangal'];
                              
                              let visibleIndex = 0;
                              for (let i = 0; i < planetOrder.length; i++) {
                                const planetKey = planetOrder[i];
                                if (visiblePlanets[planetKey]) {
                                  if (visibleIndex === datasetIndex) {
                                    setHoveredPlanetsOnChart([planetKey]);
                                    return;
                                  }
                                  visibleIndex++;
                                }
                              }
                              setHoveredPlanetsOnChart([]);
                            } else {
                              setHoveredPlanetsOnChart([]);
                            }
                          }
                        }
                      }}
                      onMouseLeave={() => {
                        setHoveredPlanetsOnChart([]);
                      }}
                    >
                      <Line
                        ref={chartRef}
                        data={{
                          labels: energyData.chart_data.map(d => {
                            const formattedDate = formatDate(d.date);
                            const dayOfWeek = getDayOfWeek(d.date);
                            return dayOfWeek ? `${formattedDate}\n${dayOfWeek}` : formattedDate;
                          }),
                          datasets: [
                            // Surya (Солнце) - 1
                            visiblePlanets.surya && {
                              label: 'Surya (☉)',
                              data: energyData.chart_data.map(d => d.surya || 0),
                              borderColor: getPlanetIndicatorColor(1),
                              backgroundColor: getPlanetIndicatorColor(1) + '1A',
                              borderWidth: 2,
                              pointRadius: 4,
                              pointHoverRadius: 6,
                              pointBackgroundColor: getPlanetIndicatorColor(1),
                              pointBorderColor: theme === 'dark' ? '#1f2937' : '#fff',
                              pointBorderWidth: 2,
                              tension: 0.4,
                              fill: false
                            },
                            // Chandra (Луна) - 2
                            visiblePlanets.chandra && {
                              label: 'Chandra (☽)',
                              data: energyData.chart_data.map(d => d.chandra || 0),
                              borderColor: getPlanetIndicatorColor(2),
                              backgroundColor: getPlanetIndicatorColor(2) + '1A',
                              borderWidth: 2,
                              pointRadius: 4,
                              pointHoverRadius: 6,
                              pointBackgroundColor: getPlanetIndicatorColor(2),
                              pointBorderColor: theme === 'dark' ? '#1f2937' : '#fff',
                              pointBorderWidth: 2,
                              tension: 0.4,
                              fill: false
                            },
                            // Guru (Юпитер) - 3
                            visiblePlanets.guru && {
                              label: 'Guru (♃)',
                              data: energyData.chart_data.map(d => d.guru || 0),
                              borderColor: getPlanetIndicatorColor(3),
                              backgroundColor: getPlanetIndicatorColor(3) + '1A',
                              borderWidth: 2,
                              pointRadius: 4,
                              pointHoverRadius: 6,
                              pointBackgroundColor: getPlanetIndicatorColor(3),
                              pointBorderColor: theme === 'dark' ? '#1f2937' : '#fff',
                              pointBorderWidth: 2,
                              tension: 0.4,
                              fill: false
                            },
                            // Rahu (Раху) - 4
                            visiblePlanets.rahu && {
                              label: 'Rahu (☊)',
                              data: energyData.chart_data.map(d => d.rahu || 0),
                              borderColor: getPlanetIndicatorColor(4),
                              backgroundColor: getPlanetIndicatorColor(4) + '1A',
                              borderWidth: 2,
                              pointRadius: 4,
                              pointHoverRadius: 6,
                              pointBackgroundColor: getPlanetIndicatorColor(4),
                              pointBorderColor: theme === 'dark' ? '#1f2937' : '#fff',
                              pointBorderWidth: 2,
                              tension: 0.4,
                              fill: false
                            },
                            // Budha (Меркурий) - 5
                            visiblePlanets.budha && {
                              label: 'Budha (☿)',
                              data: energyData.chart_data.map(d => d.budha || 0),
                              borderColor: getPlanetIndicatorColor(5),
                              backgroundColor: getPlanetIndicatorColor(5) + '1A',
                              borderWidth: 2,
                              pointRadius: 4,
                              pointHoverRadius: 6,
                              pointBackgroundColor: getPlanetIndicatorColor(5),
                              pointBorderColor: theme === 'dark' ? '#1f2937' : '#fff',
                              pointBorderWidth: 2,
                              tension: 0.4,
                              fill: false
                            },
                            // Shukra (Венера) - 6
                            visiblePlanets.shukra && {
                              label: 'Shukra (♀)',
                              data: energyData.chart_data.map(d => d.shukra || 0),
                              borderColor: getPlanetIndicatorColor(6),
                              backgroundColor: getPlanetIndicatorColor(6) + '1A',
                              borderWidth: 2,
                              pointRadius: 4,
                              pointHoverRadius: 6,
                              pointBackgroundColor: getPlanetIndicatorColor(6),
                              pointBorderColor: theme === 'dark' ? '#1f2937' : '#fff',
                              pointBorderWidth: 2,
                              tension: 0.4,
                              fill: false
                            },
                            // Ketu (Кету) - 7
                            visiblePlanets.ketu && {
                              label: 'Ketu (☋)',
                              data: energyData.chart_data.map(d => d.ketu || 0),
                              borderColor: getPlanetIndicatorColor(7),
                              backgroundColor: getPlanetIndicatorColor(7) + '1A',
                              borderWidth: 2,
                              pointRadius: 4,
                              pointHoverRadius: 6,
                              pointBackgroundColor: getPlanetIndicatorColor(7),
                              pointBorderColor: theme === 'dark' ? '#1f2937' : '#fff',
                              pointBorderWidth: 2,
                              tension: 0.4,
                              fill: false
                            },
                            // Shani (Сатурн) - 8
                            visiblePlanets.shani && {
                              label: 'Shani (♄)',
                              data: energyData.chart_data.map(d => d.shani || 0),
                              borderColor: getPlanetIndicatorColor(8),
                              backgroundColor: getPlanetIndicatorColor(8) + '1A',
                              borderWidth: 2,
                              pointRadius: 4,
                              pointHoverRadius: 6,
                              pointBackgroundColor: getPlanetIndicatorColor(8),
                              pointBorderColor: theme === 'dark' ? '#1f2937' : '#fff',
                              pointBorderWidth: 2,
                              tension: 0.4,
                              fill: false
                            },
                            // Mangal (Марс) - 9
                            visiblePlanets.mangal && {
                              label: 'Mangal (♂)',
                              data: energyData.chart_data.map(d => d.mangal || 0),
                              borderColor: getPlanetIndicatorColor(9),
                              backgroundColor: getPlanetIndicatorColor(9) + '1A',
                              borderWidth: 2,
                              pointRadius: 4,
                              pointHoverRadius: 6,
                              pointBackgroundColor: getPlanetIndicatorColor(9),
                              pointBorderColor: theme === 'dark' ? '#1f2937' : '#fff',
                              pointBorderWidth: 2,
                              tension: 0.4,
                              fill: false
                            }
                          ].filter(Boolean)
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          interaction: {
                            mode: 'nearest',
                            intersect: false
                          },
                          onHover: (event, activeElements) => {
                            try {
                              if (activeElements && activeElements.length > 0) {
                                // Берём только ближайший элемент (первый в массиве) - конкретную планету под курсором
                                const element = activeElements[0];
                                const datasetIndex = element.datasetIndex;
                                
                                // Порядок планет в datasets (только видимые)
                                const planetOrder = ['surya', 'chandra', 'guru', 'rahu', 'budha', 'shukra', 'ketu', 'shani', 'mangal'];
                                
                                // Находим индекс планеты в массиве видимых планет
                                let visibleIndex = 0;
                                for (let i = 0; i < planetOrder.length; i++) {
                                  const planetKey = planetOrder[i];
                                  if (visiblePlanets[planetKey]) {
                                    if (visibleIndex === datasetIndex) {
                                      setHoveredPlanetsOnChart([planetKey]);
                                      return;
                                    }
                                    visibleIndex++;
                                  }
                                }
                                setHoveredPlanetsOnChart([]);
                              } else {
                                setHoveredPlanetsOnChart([]);
                              }
                            } catch (error) {
                              console.error('Error in onHover:', error);
                              setHoveredPlanetsOnChart([]);
                            }
                          },
                          plugins: {
                            legend: {
                              display: true,
                              position: 'bottom',
                              labels: {
                                usePointStyle: true,
                                padding: 15,
                                font: {
                                  size: 11
                                },
                                color: theme === 'dark' ? '#e5e7eb' : '#374151'
                              }
                            },
                            tooltip: {
                              backgroundColor: theme === 'dark' ? 'rgba(31, 41, 55, 0.95)' : 'rgba(255, 255, 255, 0.95)',
                              titleColor: theme === 'dark' ? '#fff' : '#000',
                              bodyColor: theme === 'dark' ? '#d1d5db' : '#4b5563',
                              borderColor: theme === 'dark' ? 'rgba(75, 85, 99, 0.3)' : 'rgba(209, 213, 219, 0.8)',
                              borderWidth: 1,
                              padding: 12,
                              displayColors: true,
                              titleFont: {
                                size: 14,
                                weight: 'bold'
                              },
                              bodyFont: {
                                size: 13
                              },
                              callbacks: {
                                label: (context) => {
                                  const value = context.parsed.y;
                                  const planetName = context.dataset.label;
                                  return `${planetName}: ${value}% энергии`;
                                },
                                title: (tooltipItems) => {
                                  if (tooltipItems && tooltipItems.length > 0) {
                                    const dataIndex = tooltipItems[0].dataIndex;
                                    const date = energyData.chart_data[dataIndex]?.date;
                                    if (date) {
                                      const formattedDate = formatDate(date);
                                      const dayOfWeek = getDayOfWeek(date);
                                      return dayOfWeek ? [`Дата: ${formattedDate}`, dayOfWeek] : `Дата: ${formattedDate}`;
                                    }
                                  }
                                  return '';
                                }
                              }
                            }
                          },
                          scales: {
                            y: {
                              beginAtZero: true,
                              max: 100,
                              ticks: {
                                stepSize: 10,
                                callback: (value) => `${value}%`,
                                color: theme === 'dark' ? '#9ca3af' : '#6b7280',
                                font: {
                                  size: 11
                                }
                              },
                              grid: {
                                color: theme === 'dark' ? 'rgba(156, 163, 175, 0.1)' : 'rgba(203, 213, 225, 0.3)',
                                lineWidth: 1
                              }
                            },
                            x: {
                              ticks: {
                                color: theme === 'dark' ? '#9ca3af' : '#6b7280',
                                font: {
                                  size: 11
                                },
                                maxRotation: 45,
                                minRotation: 45
                              },
                              grid: {
                                color: theme === 'dark' ? 'rgba(156, 163, 175, 0.1)' : 'rgba(203, 213, 225, 0.3)',
                                lineWidth: 1
                              }
                            }
                          }
                        }}
                        height={400}
                      />
                    </div>
                  </div>
                ) : reportData.planetaryEnergyWeekly?.chart_data ? (
                  <div className="space-y-4">
                    {/* Период */}
                    <div className="text-sm text-gray-600">
                      Период: {formatDate(reportData.planetaryEnergyWeekly.chart_data[0]?.date)} — {formatDate(reportData.planetaryEnergyWeekly.chart_data[reportData.planetaryEnergyWeekly.chart_data.length - 1]?.date)}
                    </div>
                    
                    {/* Управление видимостью планет */}
                    <div className="flex flex-wrap items-center gap-2 mb-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setVisiblePlanets({
                            surya: false,
                            chandra: false,
                            mangal: false,
                            budha: false,
                            guru: false,
                            shukra: false,
                            shani: false,
                            rahu: false,
                            ketu: false
                          });
                        }}
                      >
                        Выключить все
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setVisiblePlanets({
                            surya: true,
                            chandra: true,
                            mangal: true,
                            budha: true,
                            guru: true,
                            shukra: true,
                            shani: true,
                            rahu: true,
                            ketu: true
                          });
                        }}
                      >
                        Включить все
                      </Button>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries({
                          surya: { label: 'Surya (☉)', num: 1 },
                          chandra: { label: 'Chandra (☽)', num: 2 },
                          guru: { label: 'Guru (♃)', num: 3 },
                          rahu: { label: 'Rahu (☊)', num: 4 },
                          budha: { label: 'Budha (☿)', num: 5 },
                          shukra: { label: 'Shukra (♀)', num: 6 },
                          ketu: { label: 'Ketu (☋)', num: 7 },
                          shani: { label: 'Shani (♄)', num: 8 },
                          mangal: { label: 'Mangal (♂)', num: 9 }
                        }).map(([key, { label, num }]) => {
                          const isActive = visiblePlanets[key];
                          const isHovered = hoveredPlanetsOnChart.includes(key);
                          const colorConfig = CELL_COLORS[num];
                          
                          return (
                            <Button
                              key={key}
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setVisiblePlanets(prev => ({
                                  ...prev,
                                  [key]: !prev[key]
                                }));
                              }}
                              className={`transition-all duration-200 ${
                                isActive 
                                  ? `border-2 shadow-md font-semibold bg-gradient-to-br ${colorConfig.bg} ${colorConfig.border}` 
                                  : 'opacity-40 border-opacity-30'
                              } ${
                                isHovered ? 'ring-4 ring-amber-400 ring-offset-2 scale-105 z-10' : ''
                              }`}
                              style={isActive ? {
                                ...(isHovered ? { opacity: 1 } : {})
                              } : {
                                backgroundColor: 'transparent',
                                ...(isHovered ? { opacity: 0.8 } : {})
                              }}
                            >
                              <div className="flex items-center gap-2">
                                <div
                                  className={`w-3 h-3 rounded-full transition-all duration-200 ${
                                    isActive ? 'ring-2 ring-offset-1' : ''
                                  }`}
                                  style={{ 
                                    backgroundColor: getPlanetIndicatorColor(num),
                                    ringColor: getPlanetIndicatorColor(num),
                                    opacity: isActive ? 1 : 0.4
                                  }}
                                />
                                <span className={isActive ? colorConfig.text : ''}>{label}</span>
                              </div>
                            </Button>
                          );
                        })}
                      </div>
                    </div>
                    
                    {/* График из начальных данных */}
                    <div 
                      className={`${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'} rounded-lg p-6 border ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}
                      onMouseMove={(e) => {
                        if (chartRefWeekly.current) {
                          const chartInstance = chartRefWeekly.current.chartInstance || chartRefWeekly.current;
                          if (chartInstance) {
                            const elements = getElementAtEvent(chartInstance, e.nativeEvent || e);
                            if (elements && elements.length > 0) {
                              // Берём только ближайший элемент (первый в массиве) - конкретную планету под курсором
                              const element = elements[0];
                              const datasetIndex = element.datasetIndex;
                              const planetOrder = ['surya', 'chandra', 'guru', 'rahu', 'budha', 'shukra', 'ketu', 'shani', 'mangal'];
                              
                              let visibleIndex = 0;
                              for (let i = 0; i < planetOrder.length; i++) {
                                const planetKey = planetOrder[i];
                                if (visiblePlanets[planetKey]) {
                                  if (visibleIndex === datasetIndex) {
                                    setHoveredPlanetsOnChart([planetKey]);
                                    return;
                                  }
                                  visibleIndex++;
                                }
                              }
                              setHoveredPlanetsOnChart([]);
                            } else {
                              setHoveredPlanetsOnChart([]);
                            }
                          }
                        }
                      }}
                      onMouseLeave={() => {
                        setHoveredPlanetsOnChart([]);
                      }}
                    >
                      <Line
                        ref={chartRefWeekly}
                        data={{
                          labels: reportData.planetaryEnergyWeekly.chart_data.map(d => {
                            const formattedDate = formatDate(d.date);
                            const dayOfWeek = getDayOfWeek(d.date);
                            return dayOfWeek ? `${formattedDate}\n${dayOfWeek}` : formattedDate;
                          }),
                          datasets: [
                            visiblePlanets.surya && {
                              label: 'Surya (☉)',
                              data: reportData.planetaryEnergyWeekly.chart_data.map(d => d.surya || 0),
                              borderColor: getPlanetIndicatorColor(1),
                              backgroundColor: getPlanetIndicatorColor(1) + '1A',
                              borderWidth: 2,
                              pointRadius: 4,
                              pointHoverRadius: 6,
                              pointBackgroundColor: getPlanetIndicatorColor(1),
                              pointBorderColor: theme === 'dark' ? '#1f2937' : '#fff',
                              pointBorderWidth: 2,
                              tension: 0.4,
                              fill: false
                            },
                            visiblePlanets.chandra && {
                              label: 'Chandra (☽)',
                              data: reportData.planetaryEnergyWeekly.chart_data.map(d => d.chandra || 0),
                              borderColor: getPlanetIndicatorColor(2),
                              backgroundColor: getPlanetIndicatorColor(2) + '1A',
                              borderWidth: 2,
                              pointRadius: 4,
                              pointHoverRadius: 6,
                              pointBackgroundColor: getPlanetIndicatorColor(2),
                              pointBorderColor: theme === 'dark' ? '#1f2937' : '#fff',
                              pointBorderWidth: 2,
                              tension: 0.4,
                              fill: false
                            },
                            visiblePlanets.guru && {
                              label: 'Guru (♃)',
                              data: reportData.planetaryEnergyWeekly.chart_data.map(d => d.guru || 0),
                              borderColor: getPlanetIndicatorColor(3),
                              backgroundColor: getPlanetIndicatorColor(3) + '1A',
                              borderWidth: 2,
                              pointRadius: 4,
                              pointHoverRadius: 6,
                              pointBackgroundColor: getPlanetIndicatorColor(3),
                              pointBorderColor: theme === 'dark' ? '#1f2937' : '#fff',
                              pointBorderWidth: 2,
                              tension: 0.4,
                              fill: false
                            },
                            visiblePlanets.rahu && {
                              label: 'Rahu (☊)',
                              data: reportData.planetaryEnergyWeekly.chart_data.map(d => d.rahu || 0),
                              borderColor: getPlanetIndicatorColor(4),
                              backgroundColor: getPlanetIndicatorColor(4) + '1A',
                              borderWidth: 2,
                              pointRadius: 4,
                              pointHoverRadius: 6,
                              pointBackgroundColor: getPlanetIndicatorColor(4),
                              pointBorderColor: theme === 'dark' ? '#1f2937' : '#fff',
                              pointBorderWidth: 2,
                              tension: 0.4,
                              fill: false
                            },
                            visiblePlanets.budha && {
                              label: 'Budha (☿)',
                              data: reportData.planetaryEnergyWeekly.chart_data.map(d => d.budha || 0),
                              borderColor: getPlanetIndicatorColor(5),
                              backgroundColor: getPlanetIndicatorColor(5) + '1A',
                              borderWidth: 2,
                              pointRadius: 4,
                              pointHoverRadius: 6,
                              pointBackgroundColor: getPlanetIndicatorColor(5),
                              pointBorderColor: theme === 'dark' ? '#1f2937' : '#fff',
                              pointBorderWidth: 2,
                              tension: 0.4,
                              fill: false
                            },
                            visiblePlanets.shukra && {
                              label: 'Shukra (♀)',
                              data: reportData.planetaryEnergyWeekly.chart_data.map(d => d.shukra || 0),
                              borderColor: getPlanetIndicatorColor(6),
                              backgroundColor: getPlanetIndicatorColor(6) + '1A',
                              borderWidth: 2,
                              pointRadius: 4,
                              pointHoverRadius: 6,
                              pointBackgroundColor: getPlanetIndicatorColor(6),
                              pointBorderColor: theme === 'dark' ? '#1f2937' : '#fff',
                              pointBorderWidth: 2,
                              tension: 0.4,
                              fill: false
                            },
                            visiblePlanets.ketu && {
                              label: 'Ketu (☋)',
                              data: reportData.planetaryEnergyWeekly.chart_data.map(d => d.ketu || 0),
                              borderColor: getPlanetIndicatorColor(7),
                              backgroundColor: getPlanetIndicatorColor(7) + '1A',
                              borderWidth: 2,
                              pointRadius: 4,
                              pointHoverRadius: 6,
                              pointBackgroundColor: getPlanetIndicatorColor(7),
                              pointBorderColor: theme === 'dark' ? '#1f2937' : '#fff',
                              pointBorderWidth: 2,
                              tension: 0.4,
                              fill: false
                            },
                            visiblePlanets.shani && {
                              label: 'Shani (♄)',
                              data: reportData.planetaryEnergyWeekly.chart_data.map(d => d.shani || 0),
                              borderColor: getPlanetIndicatorColor(8),
                              backgroundColor: getPlanetIndicatorColor(8) + '1A',
                              borderWidth: 2,
                              pointRadius: 4,
                              pointHoverRadius: 6,
                              pointBackgroundColor: getPlanetIndicatorColor(8),
                              pointBorderColor: theme === 'dark' ? '#1f2937' : '#fff',
                              pointBorderWidth: 2,
                              tension: 0.4,
                              fill: false
                            },
                            visiblePlanets.mangal && {
                              label: 'Mangal (♂)',
                              data: reportData.planetaryEnergyWeekly.chart_data.map(d => d.mangal || 0),
                              borderColor: getPlanetIndicatorColor(9),
                              backgroundColor: getPlanetIndicatorColor(9) + '1A',
                              borderWidth: 2,
                              pointRadius: 4,
                              pointHoverRadius: 6,
                              pointBackgroundColor: getPlanetIndicatorColor(9),
                              pointBorderColor: theme === 'dark' ? '#1f2937' : '#fff',
                              pointBorderWidth: 2,
                              tension: 0.4,
                              fill: false
                            }
                          ].filter(Boolean)
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          interaction: {
                            mode: 'nearest',
                            intersect: false
                          },
                          onHover: (event, activeElements) => {
                            try {
                              if (activeElements && activeElements.length > 0) {
                                // Берём только ближайший элемент (первый в массиве) - конкретную планету под курсором
                                const element = activeElements[0];
                                const datasetIndex = element.datasetIndex;
                                
                                // Порядок планет в datasets (только видимые)
                                const planetOrder = ['surya', 'chandra', 'guru', 'rahu', 'budha', 'shukra', 'ketu', 'shani', 'mangal'];
                                
                                // Находим индекс планеты в массиве видимых планет
                                let visibleIndex = 0;
                                for (let i = 0; i < planetOrder.length; i++) {
                                  const planetKey = planetOrder[i];
                                  if (visiblePlanets[planetKey]) {
                                    if (visibleIndex === datasetIndex) {
                                      setHoveredPlanetsOnChart([planetKey]);
                                      return;
                                    }
                                    visibleIndex++;
                                  }
                                }
                                setHoveredPlanetsOnChart([]);
                              } else {
                                setHoveredPlanetsOnChart([]);
                              }
                            } catch (error) {
                              console.error('Error in onHover:', error);
                              setHoveredPlanetsOnChart([]);
                            }
                          },
                          plugins: {
                            legend: {
                              display: true,
                              position: 'bottom',
                              onClick: (e, legendItem) => {
                                const planetMap = {
                                  'Surya (☉)': 'surya',
                                  'Chandra (☽)': 'chandra',
                                  'Mangal (♂)': 'mangal',
                                  'Budha (☿)': 'budha',
                                  'Guru (♃)': 'guru',
                                  'Shukra (♀)': 'shukra',
                                  'Shani (♄)': 'shani',
                                  'Rahu (☊)': 'rahu',
                                  'Ketu (☋)': 'ketu'
                                };
                                const planetKey = planetMap[legendItem.text];
                                if (planetKey) {
                                  setVisiblePlanets(prev => ({
                                    ...prev,
                                    [planetKey]: !prev[planetKey]
                                  }));
                                }
                              },
                              labels: {
                                usePointStyle: true,
                                padding: 15,
                                font: {
                                  size: 11
                                },
                                color: theme === 'dark' ? '#e5e7eb' : '#374151'
                              }
                            },
                            tooltip: {
                              backgroundColor: theme === 'dark' ? 'rgba(31, 41, 55, 0.95)' : 'rgba(255, 255, 255, 0.95)',
                              titleColor: theme === 'dark' ? '#fff' : '#000',
                              bodyColor: theme === 'dark' ? '#d1d5db' : '#4b5563',
                              borderColor: theme === 'dark' ? 'rgba(75, 85, 99, 0.3)' : 'rgba(209, 213, 219, 0.8)',
                              borderWidth: 1,
                              padding: 12,
                              displayColors: true,
                              titleFont: {
                                size: 14,
                                weight: 'bold'
                              },
                              bodyFont: {
                                size: 13
                              },
                              callbacks: {
                                label: (context) => {
                                  const value = context.parsed.y;
                                  const planetName = context.dataset.label;
                                  return `${planetName}: ${value}% энергии`;
                                },
                                title: (tooltipItems) => {
                                  if (tooltipItems && tooltipItems.length > 0) {
                                    const dataIndex = tooltipItems[0].dataIndex;
                                    const date = reportData.planetaryEnergyWeekly.chart_data[dataIndex]?.date;
                                    if (date) {
                                      const formattedDate = formatDate(date);
                                      const dayOfWeek = getDayOfWeek(date);
                                      return dayOfWeek ? [`Дата: ${formattedDate}`, dayOfWeek] : `Дата: ${formattedDate}`;
                                    }
                                  }
                                  return '';
                                }
                              }
                            }
                          },
                          scales: {
                            y: {
                              beginAtZero: true,
                              max: 100,
                              ticks: {
                                stepSize: 10,
                                callback: (value) => `${value}%`,
                                color: theme === 'dark' ? '#9ca3af' : '#6b7280',
                                font: {
                                  size: 11
                                }
                              },
                              grid: {
                                color: theme === 'dark' ? 'rgba(156, 163, 175, 0.1)' : 'rgba(203, 213, 225, 0.3)',
                                lineWidth: 1
                              }
                            },
                            x: {
                              ticks: {
                                color: theme === 'dark' ? '#9ca3af' : '#6b7280',
                                font: {
                                  size: 11
                                },
                                maxRotation: 45,
                                minRotation: 45
                              },
                              grid: {
                                color: theme === 'dark' ? 'rgba(156, 163, 175, 0.1)' : 'rgba(203, 213, 225, 0.3)',
                                lineWidth: 1
                              }
                            }
                          }
                        }}
                        height={400}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-64 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg">
                    <div className="text-center">
                      <Calendar className="w-12 h-12 text-purple-600 mx-auto mb-2" />
                      <p className="text-gray-600">Загрузка данных...</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Тени, Вершины, Вызовы, Переходы */}
            {(() => {
              const birthDate = user?.birth_date || reportData.personal?.birth_date;
              const shadowsPeaksData = birthDate ? calculateShadowsPeaksChallenges(birthDate) : null;
              
              if (!shadowsPeaksData) return null;
              
              return (
                <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                  <CardHeader>
                    <CardTitle>Тени · Вершины · Вызовы · Переходы</CardTitle>
                    <CardDescription>Циклы личных годов жизни на 100 лет</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      {/* Информация о базовых данных */}
                      <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <div className="text-gray-600 dark:text-gray-400">Дата рождения</div>
                            <div className="font-semibold">{birthDate}</div>
                          </div>
                          <div>
                            <div className="text-gray-600 dark:text-gray-400">Число судьбы</div>
                            <div className="font-semibold">{shadowsPeaksData.destinyNumber}</div>
                          </div>
                          <div>
                            <div className="text-gray-600 dark:text-gray-400">Первый период начинается</div>
                            <div className="font-semibold">{27 - shadowsPeaksData.destinyNumber} лет</div>
                          </div>
                          <div>
                            <div className="text-gray-600 dark:text-gray-400">Всего периодов</div>
                            <div className="font-semibold">{shadowsPeaksData.periods.length}</div>
                          </div>
                        </div>
                      </div>

                      {/* Алгоритм расчёта */}
                      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-700">
                        <div className="text-sm font-semibold mb-3">Алгоритм расчёта для каждого периода:</div>
                        <div className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                          <div>День, месяц и год рождения сначала приводятся к одной цифре. Четыре периода по 9 лет, первый начинается в 27 − число судьбы.</div>
                          <div className="mt-2"><strong>Вершина</strong> вычисляется по-разному для каждого периода:</div>
                          <div className="ml-4 space-y-1 text-xs">
                            <div>• <strong>Первый период:</strong> день + месяц</div>
                            <div>• <strong>Второй период:</strong> день + год</div>
                            <div>• <strong>Третий период:</strong> первая вершина + вторая вершина</div>
                            <div>• <strong>Четвёртый период:</strong> месяц + год</div>
                          </div>
                          <div className="mt-2"><strong>Вызов</strong> — разница тех же чисел по модулю: |месяц − день|, |день − год|, |первый вызов − второй вызов|, |месяц − год|</div>
                          <div><strong>Тень</strong> = вершина + день, месяц, год и число судьбы — по одному на каждый период</div>
                          <div><strong>Переход</strong> = тень + вершина + вызов</div>
                          <div className="mt-2 text-xs text-gray-600 dark:text-gray-400">
                            Все суммы приводятся к одной цифре.
                          </div>
                        </div>
                      </div>

                      {/* Периоды с цифрами */}
                      <div className="space-y-4">
                        {shadowsPeaksData.periods.map((period, periodIdx) => {
                          const periodColors = [
                            'bg-orange-50 dark:bg-orange-900/20 border-orange-300 dark:border-orange-700',
                            'bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-700',
                            'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700',
                            'bg-purple-50 dark:bg-purple-900/20 border-purple-300 dark:border-purple-700'
                          ];
                          const colorClass = periodColors[periodIdx % periodColors.length];
                          
                          return (
                            <div key={periodIdx} className={`rounded-lg p-4 border-2 ${colorClass}`}>
                              <div className="mb-3">
                                <div className="font-semibold text-lg mb-1">
                                  Период {period.index}: {period.startAge} - {period.endAge} лет
                                </div>
                                <div className="text-xs text-gray-600 dark:text-gray-400">
                                  {period.startAge === 27 - shadowsPeaksData.destinyNumber 
                                    ? `Начало: 27 - ${shadowsPeaksData.destinyNumber} = ${period.startAge}`
                                    : `Начало: окончание предыдущего периода`} | 
                                  Окончание: {period.startAge} + 9 = {period.endAge}
                                </div>
                              </div>
                              
                              {/* Верхний ряд: 4 цифры периода */}
                              <div className="grid grid-cols-4 gap-2 mb-2">
                                {[
                                  { label: 'Тень', value: period.shadow, showAge: false, age: null },        // Первая - Тень
                                  { label: 'Вершина', value: period.peak, showAge: false, age: null },  // Вторая - Вершина
                                  { label: 'Вызов', value: period.challenge, showAge: false, age: null },     // Третья - Вызов
                                  { label: 'Переход', value: period.transition, showAge: false, age: null } // Четвёртая - Переход
                                ].map((item, idx) => {
                                  const color = item.value ? getPlanetIndicatorColor(item.value) : '#999';
                                  return (
                                    <div key={idx} className="text-center">
                                      <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">{item.label}</div>
                                      <div 
                                        className="text-2xl font-bold rounded-lg p-2 border-2"
                                        style={{
                                          backgroundColor: color + '20',
                                          color: color,
                                          borderColor: color
                                        }}
                                      >
                                        {item.value || '-'}
                                      </div>
                                      {item.showAge && item.age && (
                                        <div className="text-xs text-gray-500 mt-1">ЧЛГ для {item.age} лет</div>
                                      )}
                                    </div>
                                  );
                                })}
                              </div>
                              
                              {/* Нижний ряд: диапазоны периодов */}
                              <div className="grid grid-cols-2 gap-2 mt-2">
                                <div className="text-center p-2 bg-white dark:bg-gray-800 rounded border border-gray-300 dark:border-gray-600">
                                  <div className="text-xs text-gray-600 dark:text-gray-400">Начало</div>
                                  <div className="font-bold">{period.startAge}</div>
                                </div>
                                <div className="text-center p-2 bg-white dark:bg-gray-800 rounded border border-gray-300 dark:border-gray-600">
                                  <div className="text-xs text-gray-600 dark:text-gray-400">Окончание</div>
                                  <div className="font-bold">{period.endAge}</div>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      {/* Полная таблица с годами */}
                      <div className="overflow-x-auto">
                        <div className="min-w-full">
                          <div className="text-sm font-semibold mb-2">Полная таблица всех лет</div>
                          <div className="grid grid-cols-5 gap-2 text-xs font-semibold mb-2 border-b pb-2">
                            <div className="text-center">Лет</div>
                            <div className="text-center">Год</div>
                            <div className="text-center">ЧЛГ</div>
                            <div className="text-center">Период</div>
                            <div className="text-center">Тип</div>
                          </div>
                          <div className="max-h-96 overflow-y-auto space-y-1">
                            {shadowsPeaksData.years.map((yearData, idx) => {
                              const period = shadowsPeaksData.periods.find(p => 
                                yearData.age >= p.startAge && yearData.age < p.endAge
                              );
                              
                              let cycleType = '';
                              if (period) {
                                // Числа периода не привязаны к отдельному году; отмечаем его начало
                                if (yearData.age === period.startAge) cycleType = 'Начало периода';
                              }
                              
                              const color = getPlanetIndicatorColor(yearData.chlg);
                              
                              return (
                                <div 
                                  key={idx}
                                  className="grid grid-cols-5 gap-2 text-xs py-1 hover:bg-gray-50 dark:hover:bg-gray-700 rounded transition-colors"
                                >
                                  <div className="text-center">{yearData.age}</div>
                                  <div className="text-center">{yearData.year}</div>
                                  <div 
                                    className="text-center font-bold rounded px-2 py-1"
                                    style={{
                                      backgroundColor: color + '20',
                                      color: color,
                                      border: `1px solid ${color}`
                                    }}
                                  >
                                    {yearData.chlg}
                                  </div>
                                  <div className="text-center text-gray-500">{period ? period.index : '-'}</div>
                                  <div className="text-center">
                                    {cycleType && (
                                      <span 
                                        className="px-2 py-1 rounded text-xs"
                                        style={{
                                          backgroundColor: color + '15',
                                          color: color
                                        }}
                                      >
                                        {cycleType}
                                      </span>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })()}

            {/* Алгоритм расчёта динамики энергий планет */}
            <Card id="energy-algorithm" className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
              <CardHeader>
                <CardTitle className="text-xl mb-2">Алгоритм расчёта динамики энергий планет</CardTitle>
                <CardDescription>
                  Подробное описание математической модели, используемой для вычисления планетарных энергий
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Шаг 1: Расчёт Janma Ank */}
                <div className="p-4 rounded-lg bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200">
                  <h3 className="text-lg font-bold text-blue-700 mb-3 flex items-center gap-2">
                    <span className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm">1</span>
                    Расчёт Janma Ank (Число рождения)
                  </h3>
                  <div className="space-y-2 text-sm text-gray-700">
                    <p><strong>Формула:</strong></p>
                    <div className="bg-white p-3 rounded border border-blue-200 font-mono">
                      <p>Janma Ank = reduce_to_single_digit(день + месяц + год)</p>
                      <p className="mt-2 text-xs text-gray-600">
                        Пример: {user?.birth_date ? (
                          <>
                            {user.birth_date.split('.').join(' + ')} = {(() => {
                              const [d, m, y] = user.birth_date.split('.').map(Number);
                              const sum = d + m + y;
                              let reduced = sum;
                              while (reduced > 9 && ![11, 22, 33].includes(reduced)) {
                                reduced = String(reduced).split('').reduce((acc, digit) => acc + parseInt(digit), 0);
                              }
                              return `${sum} → ${reduced}`;
                            })()}
                          </>
                        ) : '15.03.1990 = 15 + 3 + 1990 = 2008 → 10 → 1'}
                      </p>
                    </div>
                    <p className="text-xs text-gray-600 mt-2">
                      <strong>Примечание:</strong> Числа 11, 22, 33 не сводятся к одной цифре (мастер-числа)
                    </p>
                  </div>
                </div>

                {/* Шаг 2: Базовая энергия */}
                <div className="p-4 rounded-lg bg-gradient-to-br from-purple-50 to-pink-50 border-2 border-purple-200">
                  <h3 className="text-lg font-bold text-purple-700 mb-3 flex items-center gap-2">
                    <span className="bg-purple-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm">2</span>
                    Расчёт базовой энергии
                  </h3>
                  <div className="space-y-2 text-sm text-gray-700">
                    <p><strong>Формула:</strong></p>
                    <div className="bg-white p-3 rounded border border-purple-200 font-mono">
                      <p>base_energy = (Janma Ank × 10) mod 100</p>
                      <p className="mt-2 text-xs text-gray-600">
                        Пример: {user?.birth_date ? (() => {
                          const [d, m, y] = user.birth_date.split('.').map(Number);
                          const sum = d + m + y;
                          let reduced = sum;
                          while (reduced > 9 && ![11, 22, 33].includes(reduced)) {
                            reduced = String(reduced).split('').reduce((acc, digit) => acc + parseInt(digit), 0);
                          }
                          const baseEnergy = (reduced * 10) % 100;
                          return `(${reduced} × 10) mod 100 = ${baseEnergy}`;
                        })() : '(1 × 10) mod 100 = 10'}
                      </p>
                    </div>
                    <p className="text-xs text-gray-600 mt-2">
                      Базовая энергия определяет общий уровень планетарных влияний для человека
                    </p>
                  </div>
                </div>

                {/* Шаг 3: Расчёт энергий планет */}
                <div className="p-4 rounded-lg bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200">
                  <h3 className="text-lg font-bold text-green-700 mb-3 flex items-center gap-2">
                    <span className="bg-green-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm">3</span>
                    Расчёт базовой энергии для каждой планеты
                  </h3>
                  <div className="space-y-3 text-sm text-gray-700">
                    <p><strong>Для каждой даты вычисляется базовая энергия:</strong></p>
                    <ul className="space-y-2 bg-white p-3 rounded border border-green-200">
                      <li className="flex items-start gap-2">
                        <span className="text-orange-600 font-bold">☉ Surya (Солнце):</span>
                        <span className="font-mono">base_energy + (день % 20) - 10</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-blue-600 font-bold">☽ Chandra (Луна):</span>
                        <span className="font-mono">base_energy + (месяц % 20) - 10</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-red-600 font-bold">♂ Mangal (Марс):</span>
                        <span className="font-mono">base_energy + ((день + месяц) % 20) - 10</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-600 font-bold">☿ Budha (Меркурий):</span>
                        <span className="font-mono">base_energy + (год % 20) - 10</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-yellow-600 font-bold">♃ Guru (Юпитер):</span>
                        <span className="font-mono">base_energy + ((день × 2) % 20) - 10</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-pink-600 font-bold">♀ Shukra (Венера):</span>
                        <span className="font-mono">base_energy + ((месяц × 2) % 20) - 10</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-gray-600 font-bold">♄ Shani (Сатурн):</span>
                        <span className="font-mono">base_energy + ((год × 2) % 20) - 10</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-purple-600 font-bold">☊ Rahu (Раху):</span>
                        <span className="font-mono">base_energy + ((день + год) % 20) - 10</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-slate-600 font-bold">☋ Ketu (Кету):</span>
                        <span className="font-mono">base_energy + ((месяц + год) % 20) - 10</span>
                      </li>
                    </ul>
                  </div>
                </div>

                {/* Шаг 3.5: Планетарные часы */}
                <div className="p-4 rounded-lg bg-gradient-to-br from-indigo-50 to-blue-50 border-2 border-indigo-200">
                  <h3 className="text-lg font-bold text-indigo-700 mb-3 flex items-center gap-2">
                    <span className="bg-indigo-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm">3.5</span>
                    Учёт планетарных часов (время, принадлежащее каждой планете)
                  </h3>
                  <div className="space-y-3 text-sm text-gray-700">
                    <p><strong>Для каждой планеты подсчитывается количество планетарных часов в течение дня:</strong></p>
                    <ul className="space-y-2 bg-white p-3 rounded border border-indigo-200">
                      <li className="flex items-start gap-2">
                        <span className="text-blue-600 font-bold">⏰</span>
                        <span>День делится на 12 дневных и 12 ночных планетарных часов</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-600 font-bold">+</span>
                        <span><strong>Бонус за планетарные часы:</strong> Каждый час, принадлежащий планете, добавляет +2 к её энергии</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-gray-600 font-bold">ℹ️</span>
                        <span>Планетарные часы рассчитываются на основе времени восхода и заката солнца для города пользователя</span>
                      </li>
                    </ul>
                    <p className="text-xs text-gray-600 mt-2">
                      <strong>Пример:</strong> Если планете Surya принадлежит 3 часа в течение дня, её энергия увеличивается на +6 (3 × 2)
                    </p>
                  </div>
                </div>

                {/* Шаг 3.6: Модификаторы */}
                <div className="p-4 rounded-lg bg-gradient-to-br from-teal-50 to-cyan-50 border-2 border-teal-200">
                  <h3 className="text-lg font-bold text-teal-700 mb-3 flex items-center gap-2">
                    <span className="bg-teal-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm">3.6</span>
                    Применение модификаторов дружественности и враждебности
                  </h3>
                  <div className="space-y-3 text-sm text-gray-700">
                    <p><strong>К энергии добавляются модификаторы на основе отношений планет:</strong></p>
                    <ul className="space-y-2 bg-white p-3 rounded border border-teal-200">
                      <li className="flex items-start gap-2">
                        <span className="text-green-600 font-bold">+</span>
                        <span><strong>Личное число дня:</strong> +15 к планете, соответствующей личному числу дня</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-600 font-bold">+</span>
                        <span><strong>Личное число дня пользователя:</strong> +10 к планете, соответствующей личному числу дня пользователя</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-600 font-bold">+</span>
                        <span><strong>Максимальный бонус за дружественные планеты:</strong> +15 к планетам, дружественным правящей планете дня (лучший показатель дружественности)</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-red-600 font-bold">-</span>
                        <span><strong>Максимальный штраф за вражеские планеты:</strong> -15 к планетам, враждебным правящей планете дня (худший показатель враждебности)</span>
                      </li>
                    </ul>
                    <p className="text-xs text-gray-600 mt-2">
                      <strong>Правящая планета дня:</strong> Определяется по дню недели (Понедельник=Луна, Вторник=Марс, и т.д.)
                    </p>
                    <p className="text-xs text-gray-600 mt-1">
                      <strong>Поиск лучших/худших показателей:</strong> Система находит максимальный бонус за дружественность (+15) и максимальный штраф за враждебность (-15) среди всех планет
                    </p>
                  </div>
                </div>

                {/* Шаг 3.7: Нормализация */}
                <div className="p-4 rounded-lg bg-gradient-to-br from-purple-50 to-pink-50 border-2 border-purple-200">
                  <h3 className="text-lg font-bold text-purple-700 mb-3 flex items-center gap-2">
                    <span className="bg-purple-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm">3.7</span>
                    Нормализация значений в диапазон 0-100%
                  </h3>
                  <div className="space-y-3 text-sm text-gray-700">
                    <p><strong>Все значения нормализуются в диапазон 0-100%:</strong></p>
                    <div className="bg-white p-3 rounded border border-purple-200 font-mono text-xs">
                      <p>1. Находим минимальное и максимальное значение энергии среди всех планет</p>
                      <p className="mt-2">2. Масштабируем каждое значение по формуле:</p>
                      <p className="ml-4 mt-1">normalized = ((energy - min_energy) / (max_energy - min_energy)) × 100</p>
                      <p className="mt-2">3. Ограничиваем результат: min(100, max(0, normalized))</p>
                    </div>
                    <p className="text-xs text-gray-600 mt-2">
                      <strong>Результат:</strong> Каждая планета получает значение от 0% до 100%, где 100% - максимальная энергия среди всех планет в этот день
                    </p>
                  </div>
                </div>

                {/* Шаг 4: Пример расчёта */}
                <div className="p-4 rounded-lg bg-gradient-to-br from-orange-50 to-amber-50 border-2 border-orange-200">
                  <h3 className="text-lg font-bold text-orange-700 mb-3 flex items-center gap-2">
                    <span className="bg-orange-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm">4</span>
                    Пример расчёта для конкретной даты
                  </h3>
                  <div className="space-y-2 text-sm text-gray-700">
                    <p><strong>Дата расчёта:</strong> {new Date().toLocaleDateString('ru-RU')}</p>
                    <div className="bg-white p-3 rounded border border-orange-200 font-mono text-xs">
                      {user?.birth_date ? (() => {
                        const [d, m, y] = user.birth_date.split('.').map(Number);
                        const sum = d + m + y;
                        let janmaAnk = sum;
                        while (janmaAnk > 9 && ![11, 22, 33].includes(janmaAnk)) {
                          janmaAnk = String(janmaAnk).split('').reduce((acc, digit) => acc + parseInt(digit), 0);
                        }
                        const baseEnergy = (janmaAnk * 10) % 100;
                        const today = new Date();
                        const dayNum = today.getDate();
                        const monthNum = today.getMonth() + 1;
                        const yearNum = today.getFullYear() % 100;
                        const weekday = today.getDay(); // 0=Sunday, 6=Saturday
                        const dayPlanets = ['Surya', 'Chandra', 'Mangal', 'Budh', 'Guru', 'Shukra', 'Shani'];
                        const rulingPlanet = dayPlanets[weekday === 0 ? 6 : weekday - 1];
                        
                        // Calculate personal day
                        let personalDay = 0;
                        try {
                          const personalYear = (() => {
                            let py = d + m + yearNum;
                            while (py > 9 && ![11, 22, 33].includes(py)) {
                              py = String(py).split('').reduce((acc, digit) => acc + parseInt(digit), 0);
                            }
                            return py;
                          })();
                          const personalMonth = (() => {
                            let pm = personalYear + monthNum;
                            while (pm > 9 && ![11, 22, 33].includes(pm)) {
                              pm = String(pm).split('').reduce((acc, digit) => acc + parseInt(digit), 0);
                            }
                            return pm;
                          })();
                          personalDay = (() => {
                            let pd = personalMonth + dayNum;
                            while (pd > 9 && ![11, 22, 33].includes(pd)) {
                              pd = String(pd).split('').reduce((acc, digit) => acc + parseInt(digit), 0);
                            }
                            return pd;
                          })();
                        } catch {}
                        
                        const baseSurya = baseEnergy + (dayNum % 20) - 10;
                        const baseChandra = baseEnergy + (monthNum % 20) - 10;
                        
                        // Apply modifiers (simplified example)
                        let surya = baseSurya;
                        let chandra = baseChandra;
                        
                        // Personal day bonus
                        if (personalDay === 1) surya += 15;
                        if (personalDay === 2) chandra += 15;
                        
                        // Friend/enemy modifiers (simplified)
                        const planetRelationships = {
                          'Surya': {friends: ['Chandra', 'Mangal', 'Guru'], enemies: ['Shukra', 'Shani']},
                          'Chandra': {friends: ['Surya', 'Budh'], enemies: []}
                        };
                        const rulingData = planetRelationships[rulingPlanet] || {friends: [], enemies: []};
                        if (rulingData.friends.includes('Surya')) surya += 12;
                        if (rulingData.enemies.includes('Surya')) surya -= 12;
                        if (rulingData.friends.includes('Chandra')) chandra += 12;
                        if (rulingData.enemies.includes('Chandra')) chandra -= 12;
                        
                        surya = Math.min(100, Math.max(0, surya));
                        chandra = Math.min(100, Math.max(0, chandra));
                        
                        return (
                          <>
                            <p>Janma Ank = {janmaAnk}</p>
                            <p>base_energy = ({janmaAnk} × 10) mod 100 = {baseEnergy}</p>
                            <p className="mt-2">День: {dayNum}, Месяц: {monthNum}, Год: {yearNum}</p>
                            <p className="mt-2">Правящая планета дня: {rulingPlanet}</p>
                            <p>Личное число дня: {personalDay}</p>
                            <p className="mt-2"><strong>Расчёт Surya:</strong></p>
                            <p>Базовая: {baseEnergy} + ({dayNum} % 20) - 10 = {baseSurya}</p>
                            {personalDay === 1 && <p>+ Личное число дня: +15</p>}
                            {rulingData.friends.includes('Surya') && <p>+ Дружественная планета: +12</p>}
                            {rulingData.enemies.includes('Surya') && <p>- Вражеская планета: -12</p>}
                            <p><strong>Итого Surya: {surya}%</strong></p>
                            <p className="mt-2 text-gray-600">... аналогично для всех 9 планет</p>
                          </>
                        );
                      })() : (
                        <>
                          <p>Janma Ank = 1</p>
                          <p>base_energy = (1 × 10) mod 100 = 10</p>
                          <p className="mt-2">День: 15, Месяц: 3, Год: 25</p>
                          <p className="mt-2">Правящая планета дня: определяется по дню недели</p>
                          <p>Личное число дня: рассчитывается из даты рождения и текущей даты</p>
                          <p className="mt-2">Базовая Surya = 10 + (15 % 20) - 10 = 15</p>
                          <p>+ Модификаторы (личное число дня, дружественные/вражеские планеты)</p>
                          <p><strong>Итого: нормализованное значение 0-100%</strong></p>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* Шаг 5: Динамика во времени */}
                <div className="p-4 rounded-lg bg-gradient-to-br from-indigo-50 to-violet-50 border-2 border-indigo-200">
                  <h3 className="text-lg font-bold text-indigo-700 mb-3 flex items-center gap-2">
                    <span className="bg-indigo-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm">5</span>
                    Генерация динамики во времени
                  </h3>
                  <div className="space-y-2 text-sm text-gray-700">
                    <p><strong>Процесс:</strong></p>
                    <ol className="list-decimal list-inside space-y-1 bg-white p-3 rounded border border-indigo-200">
                      <li>Берётся базовая дата (сегодня)</li>
                      <li>Для каждого дня периода (неделя/месяц/квартал) вычисляется энергия всех планет</li>
                      <li>Результаты формируют временной ряд для построения графика</li>
                      <li>Каждая планета получает свою линию на графике</li>
                    </ol>
                    <p className="text-xs text-gray-600 mt-2">
                      <strong>Особенность:</strong> Алгоритм учитывает циклические изменения даты (день, месяц, год), что создаёт естественные колебания энергий планет во времени
                    </p>
                  </div>
                </div>

                {/* Математическая модель */}
                <div className="p-4 rounded-lg bg-gradient-to-br from-gray-50 to-slate-50 border-2 border-gray-300">
                  <h3 className="text-lg font-bold text-gray-700 mb-3">📐 Математическая модель</h3>
                  <div className="bg-white p-4 rounded border border-gray-300 font-mono text-xs space-y-2">
                    <p><strong>Общая формула для планеты P:</strong></p>
                    <p className="text-center text-base py-2 bg-gray-50 rounded">
                      E<sub>P</sub>(date) = clamp(0, 100, base_energy + f<sub>P</sub>(date) - 10)
                    </p>
                    <p className="mt-3"><strong>Где:</strong></p>
                    <ul className="list-disc list-inside space-y-1 ml-2">
                      <li>base_energy = (Janma Ank × 10) mod 100</li>
                      <li>f<sub>P</sub>(date) - функция модификации для планеты P</li>
                      <li>clamp(0, 100, x) = min(100, max(0, x))</li>
                    </ul>
                    <p className="mt-3"><strong>Функции модификации (базовая энергия):</strong></p>
                    <ul className="list-disc list-inside space-y-1 ml-2">
                      <li>f<sub>Surya</sub> = день % 20</li>
                      <li>f<sub>Chandra</sub> = месяц % 20</li>
                      <li>f<sub>Mangal</sub> = (день + месяц) % 20</li>
                      <li>f<sub>Budha</sub> = год % 20</li>
                      <li>f<sub>Guru</sub> = (день × 2) % 20</li>
                      <li>f<sub>Shukra</sub> = (месяц × 2) % 20</li>
                      <li>f<sub>Shani</sub> = (год × 2) % 20</li>
                      <li>f<sub>Rahu</sub> = (день + год) % 20</li>
                      <li>f<sub>Ketu</sub> = (месяц + год) % 20</li>
                    </ul>
                    <p className="mt-3"><strong>Дополнительные модификаторы:</strong></p>
                    <ul className="list-disc list-inside space-y-1 ml-2">
                      <li>+15 для планеты личного числа дня</li>
                      <li>+10 для планеты личного числа дня пользователя</li>
                      <li>+12 для планет, дружественных правящей планете дня</li>
                      <li>-12 для планет, враждебных правящей планете дня</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
            </div>
          </TabsContent>

          {/* Вкладка: Расчёты */}
          <TabsContent value="calculations" className="space-y-6">
            <div className="space-y-6">
              {/* Персональные числа и алгоритм */}
              <Card id="personal-numbers-card" className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                <CardHeader>
                  <CardTitle>Персональные числа и алгоритм</CardTitle>
                  <CardDescription>Душа · Ум · Судьба · Помогающее к Уму · Мудрость · Правящее</CardDescription>
                </CardHeader>
                <CardContent>
                  {(() => {
                    // Получаем данные напрямую из reportData
                    const personalNumbers = reportData?.numerology?.personal_numbers;
                    const square = reportData?.pythagoreanSquare?.square;
                    
                    // Проверяем наличие данных
                    if (!personalNumbers || !personalNumbers.birth_date) {
                      return (
                        <div className="text-sm text-gray-600 p-4 border border-yellow-300 rounded-lg bg-yellow-50">
                          <div className="font-medium mb-2">Для просмотра персональных чисел необходимо:</div>
                          <div>• Заполнить дату рождения в профиле</div>
                          <div>• Убедиться, что расчёт квадрата Пифагора выполнен</div>
                        </div>
                      );
                    }

                    // Нормализуем формат даты
                    let normalizedDate = personalNumbers.birth_date;
                    if (normalizedDate.includes('.')) {
                      const [dd, mm, yyyy] = normalizedDate.split('.');
                      normalizedDate = `${yyyy}-${mm.padStart(2, '0')}-${dd.padStart(2, '0')}`;
                    }
                    
                    const [yyyy, mm, dd] = normalizedDate.split('-');
                    if (!yyyy || !mm || !dd) {
                      return (
                        <div className="text-sm text-red-600 p-4 border border-red-300 rounded-lg bg-red-50">
                          <div className="font-medium mb-2">Ошибка: Неверный формат даты рождения</div>
                          <div>Дата: {personalNumbers.birth_date}</div>
                        </div>
                      );
                    }

                    // Вспомогательные функции
                    const dayDigits = dd.split('').map(n => parseInt(n, 10));
                    const monthDigits = mm.split('').map(n => parseInt(n, 10));
                    const yearDigits = yyyy.split('').map(n => parseInt(n, 10));
                    const sum = arr => arr.reduce((a, b) => a + b, 0);
                    const reduce = n => {
                      let x = n;
                      while (x > 9) {
                        x = x.toString().split('').reduce((a, b) => a + parseInt(b, 10), 0);
                      }
                      return x;
                    };
                    const reduceForRuling = (n) => {
                      if (n === 11 || n === 22) return n;
                      let x = n;
                      while (x > 9) {
                        x = String(x).split('').reduce((a, b) => a + parseInt(b, 10), 0);
                        if (x === 11 || x === 22) return x;
                      }
                      return x;
                    };

                    // Получаем числа из personalNumbers или пересчитываем
                    const soul = personalNumbers.soul_number ?? reduce(sum(dayDigits));
                    const mind = personalNumbers.mind_number ?? reduce(sum(monthDigits));
                    const destinySum = sum([...dayDigits, ...monthDigits, ...yearDigits]);
                    const destiny = personalNumbers.destiny_number ?? reduce(destinySum);
                    const helpingMind = personalNumbers.helping_mind_number ?? reduce(sum([...dayDigits, ...monthDigits]));
                    const nameNum = personalNumbers.full_name_number;
                    const wisdom = nameNum != null ? (personalNumbers.wisdom_number ?? reduce(destiny + parseInt(nameNum, 10))) : null;
                    const rulingSum = sum([...dayDigits, ...monthDigits, ...yearDigits]);
                    const ruling = personalNumbers.ruling_number ?? reduceForRuling(rulingSum);

                    const getCfg = (n) => CELL_COLORS[(n ?? 0)] || { bg: 'bg-white', border: 'border-gray-200', text: 'text-gray-800' };

                    return (
                      <>
                        {/* Карточки с числами */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                          <div 
                            className={`p-4 rounded-xl border-2 bg-gradient-to-br ${getCfg(soul).bg} ${getCfg(soul).border} shadow-md transition-all duration-200 cursor-pointer ${
                              hoveredPersonalNumber === 'soul' ? 'ring-4 ring-amber-400 ring-offset-2 scale-105 z-10' : ''
                            }`}
                            onMouseEnter={() => setHoveredPersonalNumber('soul')}
                            onMouseLeave={() => setHoveredPersonalNumber(null)}
                          >
                            <div className="text-xs text-gray-600 mb-1">Число Души (Ч/У)</div>
                            <div className={`text-3xl font-bold ${getCfg(soul).text} mb-2`}>{soul}</div>
                            <div className="text-xs text-gray-600 mt-1">
                              ДД = {dd} → {dayDigits.join(' + ')} = {sum(dayDigits)} → reduce = {soul}
                            </div>
                          </div>

                          <div 
                            className={`p-4 rounded-xl border-2 bg-gradient-to-br ${getCfg(mind).bg} ${getCfg(mind).border} shadow-md transition-all duration-200 cursor-pointer ${
                              hoveredPersonalNumber === 'mind' ? 'ring-4 ring-amber-400 ring-offset-2 scale-105 z-10' : ''
                            }`}
                            onMouseEnter={() => setHoveredPersonalNumber('mind')}
                            onMouseLeave={() => setHoveredPersonalNumber(null)}
                          >
                            <div className="text-xs text-gray-600 mb-1">Число Ума (Ч/Д)</div>
                            <div className={`text-3xl font-bold ${getCfg(mind).text} mb-2`}>{mind}</div>
                            <div className="text-xs text-gray-600 mt-1">
                              ММ = {mm} → {monthDigits.join(' + ')} = {sum(monthDigits)} → reduce = {mind}
                            </div>
                          </div>

                          <div 
                            className={`p-4 rounded-xl border-2 bg-gradient-to-br ${getCfg(destiny).bg} ${getCfg(destiny).border} shadow-md transition-all duration-200 cursor-pointer ${
                              hoveredPersonalNumber === 'destiny' ? 'ring-4 ring-amber-400 ring-offset-2 scale-105 z-10' : ''
                            }`}
                            onMouseEnter={() => setHoveredPersonalNumber('destiny')}
                            onMouseLeave={() => setHoveredPersonalNumber(null)}
                          >
                            <div className="text-xs text-gray-600 mb-1">Число Судьбы (Ч/С)</div>
                            <div className={`text-3xl font-bold ${getCfg(destiny).text} mb-2`}>{destiny}</div>
                            <div className="text-xs text-gray-600 mt-1">
                              ДД+ММ+ГГГГ = {[...dayDigits, ...monthDigits, ...yearDigits].join(' + ')} = {destinySum} → reduce = {destiny}
                            </div>
                          </div>

                          <div 
                            className={`p-4 rounded-xl border-2 bg-gradient-to-br ${getCfg(helpingMind).bg} ${getCfg(helpingMind).border} shadow-md transition-all duration-200 cursor-pointer ${
                              hoveredPersonalNumber === 'helpingMind' ? 'ring-4 ring-amber-400 ring-offset-2 scale-105 z-10' : ''
                            }`}
                            onMouseEnter={() => setHoveredPersonalNumber('helpingMind')}
                            onMouseLeave={() => setHoveredPersonalNumber(null)}
                          >
                            <div className="text-xs text-gray-600 mb-1">Помогающее к Уму (Ч/У*)</div>
                            <div className={`text-3xl font-bold ${getCfg(helpingMind).text} mb-2`}>{helpingMind}</div>
                            <div className="text-xs text-gray-600 mt-1">
                              ДД+ММ = {dayDigits.join(' + ')} + {monthDigits.join(' + ')} = {sum(dayDigits)} + {sum(monthDigits)} = {sum([...dayDigits, ...monthDigits])} → reduce = {helpingMind}
                            </div>
                          </div>

                          <div 
                            className={`p-4 rounded-xl border-2 ${wisdom != null ? `bg-gradient-to-br ${getCfg(wisdom).bg} ${getCfg(wisdom).border}` : 'bg-white border-gray-200'} shadow-md transition-all duration-200 cursor-pointer ${
                              hoveredPersonalNumber === 'wisdom' ? 'ring-4 ring-amber-400 ring-offset-2 scale-105 z-10' : ''
                            }`}
                            onMouseEnter={() => setHoveredPersonalNumber('wisdom')}
                            onMouseLeave={() => setHoveredPersonalNumber(null)}
                          >
                            <div className="text-xs text-gray-600 mb-1">Число Мудрости</div>
                            <div className={`text-3xl font-bold ${wisdom != null ? getCfg(wisdom).text : 'text-gray-400'} mb-2`}>{wisdom ?? '—'}</div>
                            <div className="text-xs text-gray-600 mt-1">
                              {nameNum != null
                                ? <>Ч/С + Ч/Имени = {destiny} + {nameNum} = {destiny + parseInt(nameNum, 10)} → reduce = {wisdom}</>
                                : 'Число полного имени отсутствует'}
                            </div>
                          </div>

                          <div 
                            className={`p-4 rounded-xl border-2 bg-gradient-to-br ${getCfg(ruling).bg} ${getCfg(ruling).border} shadow-md transition-all duration-200 cursor-pointer ${
                              hoveredPersonalNumber === 'ruling' ? 'ring-4 ring-amber-400 ring-offset-2 scale-105 z-10' : ''
                            }`}
                            onMouseEnter={() => setHoveredPersonalNumber('ruling')}
                            onMouseLeave={() => setHoveredPersonalNumber(null)}
                          >
                            <div className="text-xs text-gray-600 mb-1">Правящее число</div>
                            <div className={`text-3xl font-bold ${getCfg(ruling).text} mb-2`}>{ruling}</div>
                            <div className="text-xs text-gray-600 mt-1">
                              Правящее = День + Месяц + Год = {[...dayDigits, ...monthDigits, ...yearDigits].join(' + ')} = {rulingSum}
                              {(rulingSum === 11 || rulingSum === 22) ? ' (мастер-число, не сводится)' : ` → reduce = ${ruling}`}
                            </div>
                          </div>
                        </div>

                        {/* Алгоритмы расчёта */}
                        <div className="mt-6 pt-6 border-t">
                          <div className="text-sm font-semibold mb-4">Алгоритм расчёта персональных чисел</div>
                          <div className="space-y-3">
                            <div 
                              ref={personalRefs.soul} 
                              className={`p-3 border rounded-lg scroll-mt-24 transition-all duration-200 cursor-pointer ${
                                hoveredPersonalNumber === 'soul' ? 'ring-4 ring-amber-400 ring-offset-2 bg-amber-50 border-amber-300 scale-105' : 'hover:bg-gray-50'
                              }`}
                              onMouseEnter={() => setHoveredPersonalNumber('soul')}
                              onMouseLeave={() => setHoveredPersonalNumber(null)}
                            >
                              <div className="text-sm font-medium text-amber-700 mb-1">Число Души</div>
                              <div className="text-xs text-gray-700">
                                reduce(ДД) = {dayDigits.join(' + ')} = {sum(dayDigits)} → {soul}
                              </div>
                            </div>

                            <div 
                              ref={personalRefs.mind} 
                              className={`p-3 border rounded-lg scroll-mt-24 transition-all duration-200 cursor-pointer ${
                                hoveredPersonalNumber === 'mind' ? 'ring-4 ring-amber-400 ring-offset-2 bg-amber-50 border-amber-300 scale-105' : 'hover:bg-gray-50'
                              }`}
                              onMouseEnter={() => setHoveredPersonalNumber('mind')}
                              onMouseLeave={() => setHoveredPersonalNumber(null)}
                            >
                              <div className="text-sm font-medium text-emerald-700 mb-1">Число Ума</div>
                              <div className="text-xs text-gray-700">
                                reduce(ММ) = {monthDigits.join(' + ')} = {sum(monthDigits)} → {mind}
                              </div>
                            </div>

                            <div 
                              ref={personalRefs.destiny} 
                              className={`p-3 border rounded-lg scroll-mt-24 transition-all duration-200 cursor-pointer ${
                                hoveredPersonalNumber === 'destiny' ? 'ring-4 ring-amber-400 ring-offset-2 bg-amber-50 border-amber-300 scale-105' : 'hover:bg-gray-50'
                              }`}
                              onMouseEnter={() => setHoveredPersonalNumber('destiny')}
                              onMouseLeave={() => setHoveredPersonalNumber(null)}
                            >
                              <div className="text-sm font-medium text-sky-700 mb-1">Число Судьбы</div>
                              <div className="text-xs text-gray-700">
                                ДД+ММ+ГГГГ = {[...dayDigits, ...monthDigits, ...yearDigits].join(' + ')} = {destinySum} → reduce = {destiny}
                              </div>
                            </div>

                            <div 
                              ref={personalRefs.helping} 
                              className={`p-3 border rounded-lg scroll-mt-24 transition-all duration-200 cursor-pointer ${
                                hoveredPersonalNumber === 'helpingMind' ? 'ring-4 ring-amber-400 ring-offset-2 bg-amber-50 border-amber-300 scale-105' : 'hover:bg-gray-50'
                              }`}
                              onMouseEnter={() => setHoveredPersonalNumber('helpingMind')}
                              onMouseLeave={() => setHoveredPersonalNumber(null)}
                            >
                              <div className="text-sm font-medium text-indigo-700 mb-1">Помогающее число Ума</div>
                              <div className="text-xs text-gray-700">
                                reduce(ДД + ММ) = {dayDigits.join(' + ')} + {monthDigits.join(' + ')} = {sum(dayDigits)} + {sum(monthDigits)} = {sum([...dayDigits, ...monthDigits])} → {helpingMind}
                              </div>
                            </div>

                            {wisdom != null && (
                              <div 
                                ref={personalRefs.wisdom} 
                                className={`p-3 border rounded-lg scroll-mt-24 transition-all duration-200 cursor-pointer ${
                                  hoveredPersonalNumber === 'wisdom' ? 'ring-4 ring-amber-400 ring-offset-2 bg-amber-50 border-amber-300 scale-105' : 'hover:bg-gray-50'
                                }`}
                                onMouseEnter={() => setHoveredPersonalNumber('wisdom')}
                                onMouseLeave={() => setHoveredPersonalNumber(null)}
                              >
                                <div className="text-sm font-medium text-fuchsia-700 mb-1">Число Мудрости</div>
                                <div className="text-xs text-gray-700">
                                  reduce(Ч/С + Ч/Имени) = {destiny} + {nameNum} = {destiny + parseInt(nameNum, 10)} → {wisdom}
                                </div>
                              </div>
                            )}

                            <div 
                              ref={personalRefs.ruling} 
                              className={`p-3 border rounded-lg scroll-mt-24 transition-all duration-200 cursor-pointer ${
                                hoveredPersonalNumber === 'ruling' ? 'ring-4 ring-amber-400 ring-offset-2 bg-amber-50 border-amber-300 scale-105' : 'hover:bg-gray-50'
                              }`}
                              onMouseEnter={() => setHoveredPersonalNumber('ruling')}
                              onMouseLeave={() => setHoveredPersonalNumber(null)}
                            >
                              <div className="text-sm font-medium text-rose-700 mb-1">Правящее число</div>
                              <div className="text-xs text-gray-700">
                                Правящее = День + Месяц + Год = {[...dayDigits, ...monthDigits, ...yearDigits].join(' + ')} = {rulingSum}
                                {(rulingSum === 11 || rulingSum === 22) ? ' (мастер-число, не сводится)' : ` → reduce = ${ruling}`}
                              </div>
                            </div>
                          </div>
                        </div>
                      </>
                    );
                  })()}
                </CardContent>
              </Card>

              {/* Фрактал поведения */}
              {(() => {
                const birthDate = user?.birth_date || reportData.personal?.birth_date;
                const fractal = calculateBehaviorFractal(birthDate);
                const interpretation = fractal ? getBehaviorFractalInterpretation(fractal) : null;
                
                if (!fractal || !interpretation) return null;
                
                return (
                  <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                    <CardHeader>
                      <CardTitle>Фрактал поведения</CardTitle>
                      <CardDescription>Четырёхзначный код вашего характера и поведения</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-6">
                        {/* Отображение фрактала */}
                        <div className="flex items-center justify-center gap-4 flex-wrap">
                          <div className="text-center">
                            <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">Ваш фрактал</div>
                            <div className="flex gap-2">
                              {[
                                { digit: fractal.digit1, label: 'День', position: 1 },
                                { digit: fractal.digit2, label: 'Месяц', position: 2 },
                                { digit: fractal.digit3, label: 'Год', position: 3 },
                                { digit: fractal.digit4, label: 'Сумма', position: 4 }
                              ].map((item, idx) => {
                                const color = getPlanetIndicatorColor(item.digit);
                                const interp = interpretation.interpretations[`digit${item.position}`];
                                const isHovered = hoveredFractalDigit === item.position;
                                
                                return (
                                  <div 
                                    key={idx} 
                                    className="flex flex-col items-center"
                                    onMouseEnter={() => setHoveredFractalDigit(item.position)}
                                    onMouseLeave={() => setHoveredFractalDigit(null)}
                                  >
                                    <div
                                      className={`w-20 h-20 rounded-xl flex items-center justify-center text-4xl font-bold shadow-lg border-2 transition-all cursor-pointer ${isHovered ? 'ring-4 ring-amber-400 ring-offset-2 scale-110 shadow-xl' : 'hover:scale-110 hover:shadow-xl'}`}
                                      style={{
                                        backgroundColor: isHovered ? color + '35' : color + '25',
                                        borderColor: color,
                                        color: color,
                                        boxShadow: isHovered ? `0 8px 12px -2px ${color}60, 0 4px 6px -1px ${color}40` : `0 4px 6px -1px ${color}40, 0 2px 4px -1px ${color}20`
                                      }}
                                    >
                                      {item.digit}
                                    </div>
                                    <div 
                                      className={`text-xs font-medium mt-2 text-center max-w-[70px] px-2 py-1 rounded transition-all ${isHovered ? 'scale-105' : ''}`}
                                      style={{
                                        color: color,
                                        backgroundColor: isHovered ? color + '25' : color + '15'
                                      }}
                                    >
                                      {item.label}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        </div>

                        {/* Алгоритм расчёта */}
                        <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                          <h4 className="font-semibold mb-3 text-lg">Алгоритм расчёта</h4>
                          <div className="space-y-2 text-sm">
                            {birthDate && (() => {
                              let day, month, year;
                              if (birthDate.includes('.')) {
                                const parts = birthDate.split('.');
                                day = parseInt(parts[0], 10);
                                month = parseInt(parts[1], 10);
                                year = parseInt(parts[2], 10);
                              } else if (birthDate.includes('-')) {
                                const parts = birthDate.split('-');
                                year = parseInt(parts[0], 10);
                                month = parseInt(parts[1], 10);
                                day = parseInt(parts[2], 10);
                              }
                              
                              if (!day || !month || !year) return null;
                              
                              const dayReduced = reduceToSingleDigitForFractal(day);
                              const monthReduced = reduceToSingleDigitForFractal(month);
                              const yearReduced = reduceToSingleDigitForFractal(year);
                              const sumReduced = reduceToSingleDigitForFractal(day + month + year);
                              
                              const dayColor = getPlanetIndicatorColor(dayReduced);
                              const monthColor = getPlanetIndicatorColor(monthReduced);
                              const yearColor = getPlanetIndicatorColor(yearReduced);
                              const sumColor = getPlanetIndicatorColor(sumReduced);
                              
                              return (
                                <>
                                  <div 
                                    className={`flex items-center gap-2 flex-wrap p-2 rounded-lg transition-all cursor-pointer ${hoveredFractalDigit === 1 ? 'bg-amber-100 dark:bg-amber-900/30 ring-2 ring-amber-400' : ''}`}
                                    onMouseEnter={() => setHoveredFractalDigit(1)}
                                    onMouseLeave={() => setHoveredFractalDigit(null)}
                                  >
                                    <span className="font-medium">1-я цифра:</span>
                                    <span>День рождения {day} →</span>
                                    <span
                                      className={`px-2 py-1 rounded font-bold transition-all ${hoveredFractalDigit === 1 ? 'scale-110 shadow-lg' : ''}`}
                                      style={{
                                        color: dayColor,
                                        backgroundColor: dayColor + '20',
                                        border: `2px solid ${dayColor}`
                                      }}
                                    >
                                      {dayReduced}
                                    </span>
                                    <span className="text-gray-500">(основная жизненная позиция)</span>
                                  </div>
                                  <div 
                                    className={`flex items-center gap-2 flex-wrap p-2 rounded-lg transition-all cursor-pointer ${hoveredFractalDigit === 2 ? 'bg-amber-100 dark:bg-amber-900/30 ring-2 ring-amber-400' : ''}`}
                                    onMouseEnter={() => setHoveredFractalDigit(2)}
                                    onMouseLeave={() => setHoveredFractalDigit(null)}
                                  >
                                    <span className="font-medium">2-я цифра:</span>
                                    <span>Месяц рождения {month} →</span>
                                    <span
                                      className={`px-2 py-1 rounded font-bold transition-all ${hoveredFractalDigit === 2 ? 'scale-110 shadow-lg' : ''}`}
                                      style={{
                                        color: monthColor,
                                        backgroundColor: monthColor + '20',
                                        border: `2px solid ${monthColor}`
                                      }}
                                    >
                                      {monthReduced}
                                    </span>
                                    <span className="text-gray-500">(взаимодействие с окружающими)</span>
                                  </div>
                                  <div 
                                    className={`flex items-center gap-2 flex-wrap p-2 rounded-lg transition-all cursor-pointer ${hoveredFractalDigit === 3 ? 'bg-amber-100 dark:bg-amber-900/30 ring-2 ring-amber-400' : ''}`}
                                    onMouseEnter={() => setHoveredFractalDigit(3)}
                                    onMouseLeave={() => setHoveredFractalDigit(null)}
                                  >
                                    <span className="font-medium">3-я цифра:</span>
                                    <span>Год рождения {year} →</span>
                                    <span
                                      className={`px-2 py-1 rounded font-bold transition-all ${hoveredFractalDigit === 3 ? 'scale-110 shadow-lg' : ''}`}
                                      style={{
                                        color: yearColor,
                                        backgroundColor: yearColor + '20',
                                        border: `2px solid ${yearColor}`
                                      }}
                                    >
                                      {yearReduced}
                                    </span>
                                    <span className="text-gray-500">(внутренние убеждения)</span>
                                  </div>
                                  <div 
                                    className={`flex items-center gap-2 flex-wrap p-2 rounded-lg transition-all cursor-pointer ${hoveredFractalDigit === 4 ? 'bg-amber-100 dark:bg-amber-900/30 ring-2 ring-amber-400' : ''}`}
                                    onMouseEnter={() => setHoveredFractalDigit(4)}
                                    onMouseLeave={() => setHoveredFractalDigit(null)}
                                  >
                                    <span className="font-medium">4-я цифра:</span>
                                    <span>Сумма ({day} + {month} + {year} = {day + month + year}) →</span>
                                    <span
                                      className={`px-2 py-1 rounded font-bold transition-all ${hoveredFractalDigit === 4 ? 'scale-110 shadow-lg' : ''}`}
                                      style={{
                                        color: sumColor,
                                        backgroundColor: sumColor + '20',
                                        border: `2px solid ${sumColor}`
                                      }}
                                    >
                                      {sumReduced}
                                    </span>
                                    <span className="text-gray-500">(жизненный путь)</span>
                                  </div>
                                </>
                              );
                            })()}
                          </div>
                        </div>

                        {/* Интерпретация энергий */}
                        <div className="space-y-4">
                          <h4 className="font-semibold text-lg">Интерпретация энергий</h4>
                          
                          {/* Детальная интерпретация каждой цифры */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {[
                              { digit: fractal.digit1, label: 'Первая цифра', interp: interpretation.interpretations.digit1, desc: 'Основная жизненная позиция и способ самовыражения' },
                              { digit: fractal.digit2, label: 'Вторая цифра', interp: interpretation.interpretations.digit2, desc: 'Взаимодействие с окружающими и построение отношений' },
                              { digit: fractal.digit3, label: 'Третья цифра', interp: interpretation.interpretations.digit3, desc: 'Внутренние убеждения и духовные устремления' },
                              { digit: fractal.digit4, label: 'Четвёртая цифра', interp: interpretation.interpretations.digit4, desc: 'Жизненный путь и предназначение' }
                            ].map((item, idx) => {
                              const color = getPlanetIndicatorColor(item.digit);
                              const position = idx + 1; // 1, 2, 3, 4
                              const isHovered = hoveredFractalDigit === position;
                              
                              return (
                                <div
                                  key={idx}
                                  className={`p-4 rounded-xl border-2 transition-all cursor-pointer ${isHovered ? 'ring-4 ring-amber-400 ring-offset-2 scale-105 shadow-xl' : 'hover:shadow-lg hover:scale-105'}`}
                                  style={{
                                    borderColor: color,
                                    backgroundColor: isHovered ? color + '25' : color + '15',
                                    boxShadow: isHovered ? `0 8px 12px -2px ${color}50, 0 4px 6px -1px ${color}30` : `0 4px 6px -1px ${color}30`
                                  }}
                                  onMouseEnter={() => setHoveredFractalDigit(position)}
                                  onMouseLeave={() => setHoveredFractalDigit(null)}
                                >
                                  <div className="flex items-center gap-3 mb-2">
                                    <div
                                      className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl font-bold shadow-md transition-all ${isHovered ? 'scale-110' : ''}`}
                                      style={{
                                        backgroundColor: color + '30',
                                        color: color,
                                        border: `2px solid ${color}`
                                      }}
                                    >
                                      {item.digit}
                                    </div>
                                    <div>
                                      <div className="font-semibold">{item.label}</div>
                                      <div className="text-xs text-gray-500 dark:text-gray-400">{item.desc}</div>
                                    </div>
                                  </div>
                                  <div className="mt-2">
                                    <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                      {item.interp.planet}
                                    </div>
                                    <div className="text-sm text-gray-600 dark:text-gray-400">
                                      {item.interp.energy}
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>

                          {/* Общая интерпретация */}
                          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                            <h5 className="font-semibold mb-2 text-blue-900 dark:text-blue-100">Общая интерпретация</h5>
                            <p className="text-sm text-blue-800 dark:text-blue-200 whitespace-pre-line">
                              {interpretation.generalInterpretation.trim()}
                            </p>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })()}

              {/* Числа задач (проблем) */}
              {(() => {
                const birthDate = user?.birth_date || reportData.personal?.birth_date;
                // Получаем числа души, ума и судьбы из reportData или вычисляем локально
                let soulNumber = null;
                let mindNumber = null;
                let destinyNumber = null;
                let yearNumber = null;
                
                if (reportData?.numerology?.personal_numbers) {
                  soulNumber = reportData.numerology.personal_numbers.soul_number;
                  mindNumber = reportData.numerology.personal_numbers.mind_number;
                  destinyNumber = reportData.numerology.personal_numbers.destiny_number;
                }
                
                // Вычисляем число целого года рождения и другие числа, если нужно
                if (birthDate) {
                  try {
                    let day, month, year;
                    if (birthDate.includes('.')) {
                      const parts = birthDate.split('.');
                      day = parseInt(parts[0], 10);
                      month = parseInt(parts[1], 10);
                      year = parseInt(parts[2], 10);
                    } else if (birthDate.includes('-')) {
                      const parts = birthDate.split('-');
                      year = parseInt(parts[0], 10);
                      month = parseInt(parts[1], 10);
                      day = parseInt(parts[2], 10);
                    }
                    if (day && month && year) {
                      const toDigits = (s) => s.split('').map(n=>parseInt(n,10));
                      const sum = (arr) => arr.reduce((a,b)=>a+b,0);
                      const reduce = (n) => { let x = Math.abs(n); while (x > 9) x = String(x).split('').reduce((a,b)=>a+parseInt(b,10),0); return x; };
                      const dayDigits = toDigits(String(day).padStart(2, '0'));
                      const monthDigits = toDigits(String(month).padStart(2, '0'));
                      const yearDigits = toDigits(String(year));
                      
                      // Вычисляем число целого года рождения (сумма всех цифр года, приведённая к одной цифре)
                      yearNumber = reduce(sum(yearDigits));
                      
                      if (soulNumber === null || soulNumber === undefined) {
                        soulNumber = reduce(sum(dayDigits));
                      }
                      if (mindNumber === null || mindNumber === undefined) {
                        mindNumber = reduce(sum(monthDigits));
                      }
                      if (destinyNumber === null || destinyNumber === undefined) {
                        const destinySum = sum([...dayDigits, ...monthDigits, ...yearDigits]);
                        destinyNumber = reduce(destinySum);
                      }
                    }
                  } catch (e) {
                    console.error('Error calculating personal numbers:', e);
                  }
                }
                
                const taskNumbers = (soulNumber !== null && soulNumber !== undefined && 
                                    mindNumber !== null && mindNumber !== undefined && 
                                    destinyNumber !== null && destinyNumber !== undefined &&
                                    yearNumber !== null && yearNumber !== undefined) 
                                  ? calculateTaskNumbers(soulNumber, mindNumber, destinyNumber, yearNumber) 
                                  : null;
                
                if (!taskNumbers) return null;
                
                return (
                  <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                    <CardHeader>
                      <CardTitle>Числа задач (ЧП)</CardTitle>
                      <CardDescription>Четыре числа проблемы, определяющие жизненные задачи в разные периоды</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-6">
                        {/* Отображение чисел задач */}
                        <div className="flex items-center justify-center gap-4 flex-wrap">
                          <div className="text-center">
                            <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">Ваши числа задач</div>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                              {[
                                { number: taskNumbers.problem1, label: 'ЧП1', period: `${taskNumbers.period1.start}-${taskNumbers.period1.end} лет`, position: 1 },
                                { number: taskNumbers.problem2, label: 'ЧП2', period: `${taskNumbers.period2.start}-${taskNumbers.period2.end} лет`, position: 2 },
                                { number: taskNumbers.problem3, label: 'ЧП3', period: 'Всю жизнь', position: 3 },
                                { number: taskNumbers.problem4, label: 'ЧП4', period: `С ${taskNumbers.period4.start} лет`, position: 4 }
                              ].map((item, idx) => {
                                const color = getPlanetIndicatorColor(item.number);
                                const isHovered = hoveredTaskNumber === item.position;
                                
                                return (
                                  <div 
                                    key={idx} 
                                    className="flex flex-col items-center cursor-pointer"
                                    onMouseEnter={() => setHoveredTaskNumber(item.position)}
                                    onMouseLeave={() => setHoveredTaskNumber(null)}
                                  >
                                    <div
                                      className={`w-20 h-20 rounded-xl flex items-center justify-center text-4xl font-bold shadow-lg border-2 transition-all ${
                                        isHovered ? 'scale-110 shadow-xl ring-4 ring-amber-400 ring-offset-2 z-10' : 'hover:scale-110 hover:shadow-xl'
                                      }`}
                                      style={{
                                        backgroundColor: color + '25',
                                        borderColor: color,
                                        color: color,
                                        boxShadow: isHovered 
                                          ? `0 8px 12px -2px ${color}60, 0 4px 6px -1px ${color}40`
                                          : `0 4px 6px -1px ${color}40, 0 2px 4px -1px ${color}20`
                                      }}
                                    >
                                      {item.number}
                                    </div>
                                    <div className={`text-xs font-medium mt-2 text-center max-w-[80px] px-2 py-1 rounded transition-all ${
                                        isHovered ? 'scale-105' : ''
                                      }`}
                                      style={{
                                        color: color,
                                        backgroundColor: color + '15'
                                      }}
                                    >
                                      {item.label}
                                    </div>
                                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1 text-center">
                                      {item.period}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        </div>

                        {/* Алгоритм расчёта */}
                        <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                          <h4 className="font-semibold mb-3 text-lg">Алгоритм расчёта</h4>
                          <div className="space-y-3 text-sm">
                            {(() => {
                              const calc = taskNumbers.calculations;
                              const problem1Color = getPlanetIndicatorColor(taskNumbers.problem1);
                              const problem2Color = getPlanetIndicatorColor(taskNumbers.problem2);
                              const problem3Color = getPlanetIndicatorColor(taskNumbers.problem3);
                              const problem4Color = getPlanetIndicatorColor(taskNumbers.problem4);
                              const soulColor = getPlanetIndicatorColor(calc.soulNumber);
                              const mindColor = getPlanetIndicatorColor(calc.mindNumber);
                              const destinyColor = getPlanetIndicatorColor(calc.destinyNumber);
                              
                              return (
                                <>
                                  <div 
                                    className={`p-3 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 transition-all cursor-pointer ${
                                      hoveredTaskNumber === 1 ? 'bg-amber-50 dark:bg-amber-900/20 ring-2 ring-amber-400 scale-[1.02]' : ''
                                    }`}
                                    onMouseEnter={() => setHoveredTaskNumber(1)}
                                    onMouseLeave={() => setHoveredTaskNumber(null)}
                                  >
                                    <div className="flex items-center gap-2 flex-wrap mb-2">
                                      <span className="font-semibold">1-е число проблемы (ЧП1):</span>
                                      <span>Число Души</span>
                                      <span
                                        className="px-2 py-1 rounded font-bold"
                                        style={{
                                          color: soulColor,
                                          backgroundColor: soulColor + '20',
                                          border: `2px solid ${soulColor}`
                                        }}
                                      >
                                        {calc.soulNumber}
                                      </span>
                                      <span>- Число Ума</span>
                                      <span
                                        className="px-2 py-1 rounded font-bold"
                                        style={{
                                          color: mindColor,
                                          backgroundColor: mindColor + '20',
                                          border: `2px solid ${mindColor}`
                                        }}
                                      >
                                        {calc.mindNumber}
                                      </span>
                                      <span>= {calc.problem1Raw}</span>
                                      <span
                                        className="px-2 py-1 rounded font-bold"
                                        style={{
                                          color: problem1Color,
                                          backgroundColor: problem1Color + '20',
                                          border: `2px solid ${problem1Color}`
                                        }}
                                      >
                                        → {taskNumbers.problem1}
                                      </span>
                                    </div>
                                    <div className="text-xs text-gray-600 dark:text-gray-400">
                                      Период: с {taskNumbers.period1.start} до {taskNumbers.period1.end} лет (начинается с 36 - число судьбы {calc.destinyNumber} = {taskNumbers.period1.start}, заканчивается {taskNumbers.period1.start} + 9 = {taskNumbers.period1.end})
                                    </div>
                                  </div>
                                  
                                  <div 
                                    className={`p-3 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 transition-all cursor-pointer ${
                                      hoveredTaskNumber === 2 ? 'bg-amber-50 dark:bg-amber-900/20 ring-2 ring-amber-400 scale-[1.02]' : ''
                                    }`}
                                    onMouseEnter={() => setHoveredTaskNumber(2)}
                                    onMouseLeave={() => setHoveredTaskNumber(null)}
                                  >
                                    <div className="flex items-center gap-2 flex-wrap mb-2">
                                      <span className="font-semibold">2-е число проблемы (ЧП2):</span>
                                      <span>Число Души</span>
                                      <span
                                        className="px-2 py-1 rounded font-bold"
                                        style={{
                                          color: soulColor,
                                          backgroundColor: soulColor + '20',
                                          border: `2px solid ${soulColor}`
                                        }}
                                      >
                                        {calc.soulNumber}
                                      </span>
                                      <span>- Число целого года рождения</span>
                                      <span
                                        className="px-2 py-1 rounded font-bold"
                                        style={{
                                          color: getPlanetIndicatorColor(calc.yearNumber),
                                          backgroundColor: getPlanetIndicatorColor(calc.yearNumber) + '20',
                                          border: `2px solid ${getPlanetIndicatorColor(calc.yearNumber)}`
                                        }}
                                      >
                                        {calc.yearNumber}
                                      </span>
                                      <span>= {calc.problem2Raw}</span>
                                      <span
                                        className="px-2 py-1 rounded font-bold"
                                        style={{
                                          color: problem2Color,
                                          backgroundColor: problem2Color + '20',
                                          border: `2px solid ${problem2Color}`
                                        }}
                                      >
                                        → {taskNumbers.problem2}
                                      </span>
                                    </div>
                                    <div className="text-xs text-gray-600 dark:text-gray-400">
                                      Период: с {taskNumbers.period2.start} до {taskNumbers.period2.end} лет (начало - окончание первого периода {taskNumbers.period1.end}, длится 9 лет)
                                    </div>
                                  </div>
                                  
                                  <div 
                                    className={`p-3 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 transition-all cursor-pointer ${
                                      hoveredTaskNumber === 3 ? 'bg-amber-50 dark:bg-amber-900/20 ring-2 ring-amber-400 scale-[1.02]' : ''
                                    }`}
                                    onMouseEnter={() => setHoveredTaskNumber(3)}
                                    onMouseLeave={() => setHoveredTaskNumber(null)}
                                  >
                                    <div className="flex items-center gap-2 flex-wrap mb-2">
                                      <span className="font-semibold">3-е число проблемы (ЧП3):</span>
                                      <span>ЧП1</span>
                                      <span
                                        className="px-2 py-1 rounded font-bold"
                                        style={{
                                          color: problem1Color,
                                          backgroundColor: problem1Color + '20',
                                          border: `2px solid ${problem1Color}`
                                        }}
                                      >
                                        {taskNumbers.problem1}
                                      </span>
                                      <span>- ЧП2</span>
                                      <span
                                        className="px-2 py-1 rounded font-bold"
                                        style={{
                                          color: problem2Color,
                                          backgroundColor: problem2Color + '20',
                                          border: `2px solid ${problem2Color}`
                                        }}
                                      >
                                        {taskNumbers.problem2}
                                      </span>
                                      <span>= {calc.problem3Raw}</span>
                                      <span
                                        className="px-2 py-1 rounded font-bold"
                                        style={{
                                          color: problem3Color,
                                          backgroundColor: problem3Color + '20',
                                          border: `2px solid ${problem3Color}`
                                        }}
                                      >
                                        → {taskNumbers.problem3}
                                      </span>
                                    </div>
                                    <div className="text-xs text-gray-600 dark:text-gray-400">
                                      Период: всю жизнь (от рождения)
                                    </div>
                                  </div>
                                  
                                  <div 
                                    className={`p-3 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 transition-all cursor-pointer ${
                                      hoveredTaskNumber === 4 ? 'bg-amber-50 dark:bg-amber-900/20 ring-2 ring-amber-400 scale-[1.02]' : ''
                                    }`}
                                    onMouseEnter={() => setHoveredTaskNumber(4)}
                                    onMouseLeave={() => setHoveredTaskNumber(null)}
                                  >
                                    <div className="flex items-center gap-2 flex-wrap mb-2">
                                      <span className="font-semibold">4-е число проблемы (ЧП4):</span>
                                      <span>Месяц (Число Ума)</span>
                                      <span
                                        className="px-2 py-1 rounded font-bold"
                                        style={{
                                          color: mindColor,
                                          backgroundColor: mindColor + '20',
                                          border: `2px solid ${mindColor}`
                                        }}
                                      >
                                        {calc.mindNumber}
                                      </span>
                                      <span>- Число целого года рождения</span>
                                      <span
                                        className="px-2 py-1 rounded font-bold"
                                        style={{
                                          color: getPlanetIndicatorColor(calc.yearNumber),
                                          backgroundColor: getPlanetIndicatorColor(calc.yearNumber) + '20',
                                          border: `2px solid ${getPlanetIndicatorColor(calc.yearNumber)}`
                                        }}
                                      >
                                        {calc.yearNumber}
                                      </span>
                                      <span>= {calc.problem4Raw}</span>
                                      <span
                                        className="px-2 py-1 rounded font-bold"
                                        style={{
                                          color: problem4Color,
                                          backgroundColor: problem4Color + '20',
                                          border: `2px solid ${problem4Color}`
                                        }}
                                      >
                                        → {taskNumbers.problem4}
                                      </span>
                                    </div>
                                    <div className="text-xs text-gray-600 dark:text-gray-400">
                                      Период: с {taskNumbers.period4.start} лет до конца жизни (после окончания периода ЧП2)
                                    </div>
                                  </div>
                                </>
                              );
                            })()}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })()}

              {/* Пифагорейский квадрат */}
              <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                <CardHeader>
                  <CardTitle>Пифагорейский квадрат</CardTitle>
                  <CardDescription>Ваша числовая матрица рождения</CardDescription>
                </CardHeader>
                <CardContent>
                  {reportData.pythagoreanSquare ? (
                    <div className="space-y-6">
                      {/* Зона квадрата (без правой колонки алгоритма — вынесен в отдельную карточку ниже) */}
                      {(() => {
                         const square = reportData.pythagoreanSquare.square;
                         const fallback = computePythagoreanSums(square);
                         const hSums = reportData.pythagoreanSquare.horizontal_sums || fallback.h;
                         const vSums = reportData.pythagoreanSquare.vertical_sums || fallback.v;
                         const dSums = reportData.pythagoreanSquare.diagonal_sums || fallback.d;
                         // Функция для получения количества в ячейке
                         const countLen = (cell) => { if (!cell) return 0; if (typeof cell==='string') return cell.length; if (Array.isArray(cell)) return cell.length; return String(cell).length; };
                         const len = (n) => { const [r,c]=INDEX_BY_NUMBER[n]; return countLen(square?.[r]?.[c]); };
                         return (
                           <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mx-auto" style={{ maxWidth: 1100 }}>
                             {/* Квадрат */}
                             <div>
                               <div className="text-xs text-gray-500 mb-1">3×3 клетки (планеты и количества)</div>
                               <div className="grid grid-cols-3 grid-rows-3 gap-3">
                                 {/* 3x3 клетки */}
                                 {NUMBER_LAYOUT.flat().map((num) => {
                                   const [rowIdx, colIdx] = INDEX_BY_NUMBER[num];
                                   const cell = square?.[rowIdx]?.[colIdx] || '';
                                   const count = typeof cell === 'string' ? cell.length : Array.isArray(cell) ? cell.length : (cell ? String(cell).length : 0);
                                   const colorConfig = CELL_COLORS[num];
                                   const isActive = (hoveredDigit === num) || (Array.isArray(hoveredSet) && hoveredSet.includes(num));
                                   return (
                                     <div
                                       key={`cell-${num}`}
                                       className={`aspect-square flex flex-col items-center justify-center bg-gradient-to-br ${colorConfig.bg} border-2 ${colorConfig.border} rounded-xl font-bold shadow-md ${isActive ? 'ring-4 ring-amber-400' : ''}`}
                                       style={{ gridColumn: colIdx + 1, gridRow: rowIdx + 1 }}
                                     >
                                       <span className={`text-2xl ${colorConfig.text}`}>{count}</span>
                                       <span className={`text-xs ${colorConfig.text} opacity-70 mt-1 flex items-center gap-1`}>
                                         <span>{PLANET_SYMBOLS[num]}</span>
                                         <span>{num}</span>
                                       </span>
                                     </div>
                                   );
                                 })}
                               </div>
                             </div>
                             {/* Пояснение справа: Методологический разбор квадрата Пифагора */}
                             <div className="space-y-3">
                               <div className="p-4 rounded-lg border bg-white/80">
                                 <div className="text-base font-semibold mb-2 text-gray-800">Методологический разбор квадрата Пифагора</div>
                                 {(() => {
                                   try {
                                     const birth = (reportData?.personalNumbers?.birth_date || user?.birth_date || '').trim();
                                     if (!birth || !/^[0-9]{2}\.[0-9]{2}\.[0-9]{4}$/.test(birth)) {
                                       return (
                                         <div className="text-sm text-gray-700">
                                           Укажите корректную дату рождения в формате ДД.ММ.ГГГГ, чтобы увидеть пошаговый расчёт a,b,c,d.
                                         </div>
                                       );
                                     }
                                     const [dd, mm, yyyy] = birth.split('.');
                                     const digits = (dd + mm + yyyy).split('').map(d => parseInt(d, 10));
                                     const sumDigits = digits.reduce((s, d) => s + d, 0);
                                     const reduceToDigit = (n) => { let x = n; while (x > 9) x = String(x).split('').reduce((s, d) => s + parseInt(d, 10), 0); return x; };
                                     const a = sumDigits;
                                     const b = reduceToDigit(a);
                                     const dayFirst = dd[0] !== '0' ? parseInt(dd[0], 10) : parseInt(dd[1] || '0', 10);
                                     const cRaw = dayFirst * 2 - a;
                                     const c = Math.abs(cRaw);
                                     const d = reduceToDigit(c);
                                     return (
                                       <div className="space-y-2 text-sm text-gray-800">
                                         <div className="font-semibold">Дата: {birth}</div>
                                         <div>1) Вычисляем первые 4 числа: 1 = a; 2 = b; 3 = c; 4 = d.</div>
                                         <div className="bg-white rounded-md border p-3">
                                           <div><b>a</b> = сумма всех цифр = {digits.join(' + ')} = <b>{a}</b></div>
                                           <div><b>b</b> = a, приведённое к целому числу = {a} ⇒ <b>{b}</b></div>
                                           <div><b>c</b> = |(первая цифра дня × 2) − a| = |({dayFirst} × 2) − {a}| = <b>{c}</b></div>
                                           <div><b>d</b> = c, приведённое к целому числу = {c} ⇒ <b>{d}</b></div>
                                         </div>
                                         <div>2) Результат: 1 = {a}; 2 = {b}; 3 = {c}; 4 = {d}.</div>
                                         <div className="text-xs text-gray-500">* Если первая цифра дня равна 0 (например, 01 или 09), в расчёте используем вторую цифру дня рождения.</div>
                                       </div>
                                     );
                                   } catch { return null; }
                                 })()}
                               </div>
                               <div className="p-4 rounded-lg border bg-white/80">
                                 <div className="text-sm font-semibold mb-2 text-gray-800">Как заполняется квадрат и итоговый набор</div>
                                 {(() => {
                                   try {
                                     const birth = (reportData?.personalNumbers?.birth_date || user?.birth_date || '').trim();
                                     if (!birth || !/^[0-9]{2}\.[0-9]{2}\.[0-9]{4}$/.test(birth)) return null;
                                     const [dd, mm, yyyy] = birth.split('.');
                                     const digits = (dd + mm + yyyy).split('').map(d => parseInt(d, 10));
                                     const sumDigits = (arr)=>arr.reduce((s,d)=>s+d,0);
                                     const reduceToDigit = (n)=>{let x=n;while(x>9)x=String(x).split('').reduce((s,d)=>s+parseInt(d,10),0);return x;};
                                     const a = sumDigits(digits);
                                     const b = reduceToDigit(a);
                                     const dayFirst = dd[0] !== '0' ? parseInt(dd[0], 10) : parseInt(dd[1] || '0', 10);
                                     const c = Math.abs(dayFirst*2 - a);
                                     const d = reduceToDigit(c);
                                     const digitsA = String(a).split('').map(n=>parseInt(n,10));
                                     const digitsB = String(b).split('').map(n=>parseInt(n,10));
                                     const digitsC = String(c).split('').map(n=>parseInt(n,10));
                                     const digitsD = String(d).split('').map(n=>parseInt(n,10));
                                     const allDigits = [...digits, ...digitsA, ...digitsB, ...digitsC, ...digitsD];
                                     const planetNames = {1:'Солнце (Surya)',2:'Луна (Chandra)',3:'Юпитер (Guru)',4:'Раху (Rahu)',5:'Меркурий (Budha)',6:'Венера (Shukra)',7:'Кету (Ketu)',8:'Сатурн (Shani)',9:'Марс (Mangal)'};
                                     const bucket = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[]};
                                     allDigits.forEach(dg=>{ if(bucket[dg]) bucket[dg].push(dg); });
                                     return (
                                       <div>
                                         <div className="flex items-center gap-2 flex-wrap">
                                           <span className="font-semibold">Цифры из даты</span>:
                                           {digits.map((dg,i)=>{const cfg=chipStyleForDigit(dg);return(<span key={`date-${i}`} className={`px-1.5 py-0.5 rounded border text-xs ${cfg.cls}`} onMouseEnter={()=>setHoveredDigit(dg)} onMouseLeave={()=>setHoveredDigit(null)}>{dg}</span>)})}
                                         </div>
                                         <div className="flex items-center gap-2 flex-wrap mt-1">
                                           <span><b>a</b>:</span>
                                           {digitsA.map((dg,i)=>{const cfg=chipStyleForDigit(dg);return(<span key={`a-${i}`} className={`px-1.5 py-0.5 rounded border text-xs ${cfg.cls}`} onMouseEnter={()=>setHoveredDigit(dg)} onMouseLeave={()=>setHoveredDigit(null)}>{dg}</span>)})}
                                           <span className="ml-2"><b>b</b>:</span>
                                           {digitsB.map((dg,i)=>{const cfg=chipStyleForDigit(dg);return(<span key={`b-${i}`} className={`px-1.5 py-0.5 rounded border text-xs ${cfg.cls}`} onMouseEnter={()=>setHoveredDigit(dg)} onMouseLeave={()=>setHoveredDigit(null)}>{dg}</span>)})}
                                           <span className="ml-2"><b>c</b>:</span>
                                           {digitsC.map((dg,i)=>{const cfg=chipStyleForDigit(dg);return(<span key={`c-${i}`} className={`px-1.5 py-0.5 rounded border text-xs ${cfg.cls}`} onMouseEnter={()=>setHoveredDigit(dg)} onMouseLeave={()=>setHoveredDigit(null)}>{dg}</span>)})}
                                           <span className="ml-2"><b>d</b>:</span>
                                           {digitsD.map((dg,i)=>{const cfg=chipStyleForDigit(dg);return(<span key={`d-${i}`} className={`px-1.5 py-0.5 rounded border text-xs ${cfg.cls}`} onMouseEnter={()=>setHoveredDigit(dg)} onMouseLeave={()=>setHoveredDigit(null)}>{dg}</span>)})}
                                         </div>
                                         <div className="mt-2 text-xs text-gray-600">Итоговый набор (подсветка по наведению на цифры):</div>
                                         <div className="mt-2 grid grid-cols-3 gap-3 max-w-sm">
                                           {NUMBER_LAYOUT.flat().map((num)=>{
                                             const color = CELL_COLORS[num];
                                             const isActive = hoveredDigit === num;
                                             return (
                                               <div key={`final-${num}`} className={`min-h-[72px] rounded-xl border-2 shadow-sm p-2 bg-gradient-to-br ${color.bg} ${color.border} ${isActive ? 'ring-2 ring-amber-400' : ''}`} title={planetNames[num]}>
                                                 <div className={`text-[10px] mb-1 ${color.text}`}>{planetNames[num]}</div>
                                                 <div className="flex flex-wrap gap-1">
                                                   {bucket[num].length ? bucket[num].map((dg, idx)=> (
                                                     <span key={`chip-${num}-${idx}`} className={`px-1.5 py-0.5 rounded text-xs border ${hoveredDigit === dg ? 'bg-amber-100 border-amber-300 text-amber-800' : 'bg-white border-gray-200 text-gray-700'}`} onMouseEnter={()=>setHoveredDigit(dg)} onMouseLeave={()=>setHoveredDigit(null)}>{dg}</span>
                                                   )) : <span className="text-xs text-gray-400">—</span>}
                                                 </div>
                                               </div>
                                             );
                                           })}
                                         </div>
                                       </div>
                                     );
                                   } catch { return null; }
                                 })()}
                               </div>
                             </div>
                           </div>
                         );
                       })()}
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-64 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg">
                      <div className="text-center">
                        <BarChart3 className="w-12 h-12 text-blue-600 mx-auto mb-2" />
                        <p className="text-gray-600">Загрузка данных...</p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Горизонтали · Вертикали · Диагонали — отдельная карточка */}
              <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                <CardHeader>
                  <CardTitle>Горизонтали · Вертикали · Диагонали</CardTitle>
                  <CardDescription>Суммы по линиям и диагоналям + компактный квадрат</CardDescription>
                </CardHeader>
                <CardContent>
                  {(() => {
                    try {
                      const square = reportData?.pythagoreanSquare?.square;
                      if (!square) return null;
                      const fallback = computePythagoreanSums(square);
                      const hSums = reportData.pythagoreanSquare.horizontal_sums || fallback.h;
                      const vSums = reportData.pythagoreanSquare.vertical_sums || fallback.v;
                      const dSums = reportData.pythagoreanSquare.diagonal_sums || fallback.d;
                      const countLen = (cell) => { if (!cell) return 0; if (typeof cell==='string') return cell.length; if (Array.isArray(cell)) return cell.length; return String(cell).length; };
                      const len = (n) => { const [r,c]=INDEX_BY_NUMBER[n]; return countLen(square?.[r]?.[c]); };
                      return (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                          {/* Левая колонка: мини‑квадрат с суммами и диагоналями */}
                          <div>
                            <div className="grid grid-cols-4 grid-rows-4 gap-3">
                              {NUMBER_LAYOUT.flat().map((num) => {
                                const [rowIdx, colIdx] = INDEX_BY_NUMBER[num];
                                const cell = square?.[rowIdx]?.[colIdx] || '';
                                const count = typeof cell === 'string' ? cell.length : Array.isArray(cell) ? cell.length : (cell ? String(cell).length : 0);
                                const colorConfig = CELL_COLORS[num];
                                const isActive = (hoveredDigit === num) || (Array.isArray(hoveredSet) && hoveredSet.includes(num));
                                return (
                                  <div
                                    key={`mini-${num}`}
                                    className={`aspect-square flex flex-col items-center justify-center bg-gradient-to-br ${colorConfig.bg} border-2 ${colorConfig.border} rounded-xl font-bold shadow-md ${isActive ? 'ring-4 ring-amber-400' : ''}`}
                                    onMouseEnter={() => setHoveredDigit(num)}
                                    onMouseLeave={() => setHoveredDigit(null)}
                                    style={{ gridColumn: (colIdx+1), gridRow: (rowIdx+1) }}
                                  >
                                    <span className={`text-2xl ${colorConfig.text}`}>{count}</span>
                                    <span className={`text-xs ${colorConfig.text} opacity-70 mt-1 flex items-center gap-1`}>
                                      <span>{PLANET_SYMBOLS[num]}</span>
                                      <span>{num}</span>
                                    </span>
                                  </div>
                                );
                              })}
                              {hSums.map((sum, r) => (
                                (()=>{ const setForRow = r===0?[1,4,7]:r===1?[2,5,8]:[3,6,9]; const active = Array.isArray(hoveredSet) && hoveredSet.join(',')===setForRow.join(','); return (
                                  <div
                                    key={`mini-h-${r}`}
                                    className={`aspect-square flex items-center justify-center rounded-xl bg-blue-50 border-2 border-blue-200 shadow-md ${active ? 'ring-4 ring-amber-400' : ''}`}
                                    style={{ gridColumn: 4, gridRow: r + 1 }}
                                    onMouseEnter={()=>setHoveredSet(setForRow)}
                                    onMouseLeave={()=>setHoveredSet(null)}
                                  >
                                    <span className="text-lg font-bold text-blue-600">{sum}</span>
                                  </div>
                                );})()
                              ))}
                              {vSums.map((sum, c) => (
                                (()=>{ const setForCol = c===0?[1,2,3]:c===1?[4,5,6]:[7,8,9]; const active = Array.isArray(hoveredSet) && hoveredSet.join(',')===setForCol.join(','); return (
                                  <div
                                    key={`mini-v-${c}`}
                                    className={`h-12 flex items-center justify-center rounded-xl bg-purple-50 border-2 border-purple-200 shadow-md ${active ? 'ring-4 ring-amber-400' : ''}`}
                                    style={{ gridColumn: c + 1, gridRow: 4 }}
                                    onMouseEnter={()=>setHoveredSet(setForCol)}
                                    onMouseLeave={()=>setHoveredSet(null)}
                                  >
                                    <span className="text-lg font-bold text-purple-600">{sum}</span>
                                  </div>
                                );})()
                              ))}
                              <div className="h-12" style={{ gridColumn: 4, gridRow: 4 }} />
                            </div>
                            <div className="grid grid-cols-2 gap-3 mt-3">
                              {(()=>{ const active = Array.isArray(hoveredSet) && hoveredSet.join(',')===[3,5,7].join(','); return (
                                <div className={`p-3 rounded-xl bg-rose-50 border-2 border-rose-200 shadow-md text-center ${active?'ring-4 ring-amber-400':''}`}
                                     onMouseEnter={()=>setHoveredSet([3,5,7])}
                                     onMouseLeave={()=>setHoveredSet(null)}>
                                  <div className="text-sm font-semibold text-rose-700 mb-1">Диагональ (3-5-7)</div>
                                  <div className="text-lg font-bold text-rose-700">{dSums[1]}</div>
                                </div>
                              );})()}
                              {(()=>{ const active = Array.isArray(hoveredSet) && hoveredSet.join(',')===[1,5,9].join(','); return (
                                <div className={`p-3 rounded-xl bg-amber-50 border-2 border-amber-200 shadow-md text-center ${active?'ring-4 ring-amber-400':''}`}
                                     onMouseEnter={()=>setHoveredSet([1,5,9])}
                                     onMouseLeave={()=>setHoveredSet(null)}>
                                  <div className="text-sm font-semibold text-amber-700 mb-1">Диагональ (1-5-9)</div>
                                  <div className="text-lg font-bold text-amber-700">{dSums[0]}</div>
                                </div>
                              );})()}
                            </div>
                          </div>

                          {/* Правая колонка: объяснение с подсветкой */}
                          <div className="space-y-4 p-4 rounded-lg border bg-white/80">
                            <div className="text-base font-semibold text-gray-800">Объяснение горизонталей, вертикалей и диагоналей</div>
                            <p className="text-xs text-gray-600">
                              Наведите на карточку или на любое число — соответствующие цифры подсветятся в квадрате слева. Сумма считается как количество в ячейках (сколько раз встречается каждая цифра).
                            </p>
                            <div className="space-y-2 text-sm text-gray-800">
                              {/* Горизонтали */}
                              <div className="font-semibold text-gray-700">Горизонтали</div>
                              <div className="p-3 rounded-lg border hover:bg-amber-50"
                                   onMouseEnter={() => setHoveredSet([1,4,7])}
                                   onMouseLeave={() => setHoveredSet(null)}>
                                <div className="mb-1"><b>Горизонталь 1</b> (1‑4‑7):</div>
                                <div className="flex items-center gap-2 flex-wrap">
                                  {[1,4,7].map((d,i)=>{
                                    const cfg = chipStyleForDigit(d);
                                    return (
                                      <span key={`h1-${i}`} className={`px-1.5 py-0.5 rounded border text-xs ${cfg.cls}`}
                                            onMouseEnter={()=>setHoveredDigit(d)} onMouseLeave={()=>setHoveredDigit(null)}>{d}</span>
                                    );
                                  })}
                                  <span className="ml-auto text-gray-500">сумма:</span>
                                  <span className="font-bold">{hSums[0]}</span>
                                </div>
                              </div>
                              <div className="p-3 rounded-lg border hover:bg-amber-50"
                                   onMouseEnter={() => setHoveredSet([2,5,8])}
                                   onMouseLeave={() => setHoveredSet(null)}>
                                <div className="mb-1"><b>Горизонталь 2</b> (2‑5‑8):</div>
                                <div className="flex items-center gap-2 flex-wrap">
                                  {[2,5,8].map((d,i)=>{ const cfg=chipStyleForDigit(d); return (
                                    <span key={`h2-${i}`} className={`px-1.5 py-0.5 rounded border text-xs ${cfg.cls}`}
                                          onMouseEnter={()=>setHoveredDigit(d)} onMouseLeave={()=>setHoveredDigit(null)}>{d}</span>
                                  );})}
                                  <span className="ml-auto text-gray-500">сумма:</span>
                                  <span className="font-bold">{hSums[1]}</span>
                                </div>
                              </div>
                              <div className="p-3 rounded-lg border hover:bg-amber-50"
                                   onMouseEnter={() => setHoveredSet([3,6,9])}
                                   onMouseLeave={() => setHoveredSet(null)}>
                                <div className="mb-1"><b>Горизонталь 3</b> (3‑6‑9):</div>
                                <div className="flex items-center gap-2 flex-wrap">
                                  {[3,6,9].map((d,i)=>{ const cfg=chipStyleForDigit(d); return (
                                    <span key={`h3-${i}`} className={`px-1.5 py-0.5 rounded border text-xs ${cfg.cls}`}
                                          onMouseEnter={()=>setHoveredDigit(d)} onMouseLeave={()=>setHoveredDigit(null)}>{d}</span>
                                  );})}
                                  <span className="ml-auto text-gray-500">сумма:</span>
                                  <span className="font-bold">{hSums[2]}</span>
                                </div>
                              </div>

                              {/* Вертикали */}
                              <div className="font-semibold text-gray-700 mt-2">Вертикали</div>
                              <div className="p-3 rounded-lg border hover:bg-indigo-50"
                                   onMouseEnter={() => setHoveredSet([1,2,3])}
                                   onMouseLeave={() => setHoveredSet(null)}>
                                <div className="mb-1"><b>Вертикаль 1</b> (1‑2‑3):</div>
                                <div className="flex items-center gap-2 flex-wrap">
                                  {[1,2,3].map((d,i)=>{ const cfg=chipStyleForDigit(d); return (
                                    <span key={`v1-${i}`} className={`px-1.5 py-0.5 rounded border text-xs ${cfg.cls}`}
                                          onMouseEnter={()=>setHoveredDigit(d)} onMouseLeave={()=>setHoveredDigit(null)}>{d}</span>
                                  );})}
                                  <span className="ml-auto text-gray-500">сумма:</span>
                                  <span className="font-bold">{vSums[0]}</span>
                                </div>
                              </div>
                              <div className="p-3 rounded-lg border hover:bg-indigo-50"
                                   onMouseEnter={() => setHoveredSet([4,5,6])}
                                   onMouseLeave={() => setHoveredSet(null)}>
                                <div className="mb-1"><b>Вертикаль 2</b> (4‑5‑6):</div>
                                <div className="flex items-center gap-2 flex-wrap">
                                  {[4,5,6].map((d,i)=>{ const cfg=chipStyleForDigit(d); return (
                                    <span key={`v2-${i}`} className={`px-1.5 py-0.5 rounded border text-xs ${cfg.cls}`}
                                          onMouseEnter={()=>setHoveredDigit(d)} onMouseLeave={()=>setHoveredDigit(null)}>{d}</span>
                                  );})}
                                  <span className="ml-auto text-gray-500">сумма:</span>
                                  <span className="font-bold">{vSums[1]}</span>
                                </div>
                              </div>
                              <div className="p-3 rounded-lg border hover:bg-indigo-50"
                                   onMouseEnter={() => setHoveredSet([7,8,9])}
                                   onMouseLeave={() => setHoveredSet(null)}>
                                <div className="mb-1"><b>Вертикаль 3</b> (7‑8‑9):</div>
                                <div className="flex items-center gap-2 flex-wrap">
                                  {[7,8,9].map((d,i)=>{ const cfg=chipStyleForDigit(d); return (
                                    <span key={`v3-${i}`} className={`px-1.5 py-0.5 rounded border text-xs ${cfg.cls}`}
                                          onMouseEnter={()=>setHoveredDigit(d)} onMouseLeave={()=>setHoveredDigit(null)}>{d}</span>
                                  );})}
                                  <span className="ml-auto text-gray-500">сумма:</span>
                                  <span className="font-bold">{vSums[2]}</span>
                                </div>
                              </div>

                              {/* Диагонали */}
                              <div className="font-semibold text-gray-700 mt-2">Диагонали</div>
                              <div className="p-3 rounded-lg border hover:bg-rose-50"
                                   onMouseEnter={() => setHoveredSet([3,5,7])}
                                   onMouseLeave={() => setHoveredSet(null)}>
                                <div className="mb-1"><b>Диагональ 3‑5‑7</b>:</div>
                                <div className="flex items-center gap-2 flex-wrap">
                                  {[3,5,7].map((d,i)=>{ const cfg=chipStyleForDigit(d); return (
                                    <span key={`d1-${i}`} className={`px-1.5 py-0.5 rounded border text-xs ${cfg.cls}`}
                                          onMouseEnter={()=>setHoveredDigit(d)} onMouseLeave={()=>setHoveredDigit(null)}>{d}</span>
                                  );})}
                                  <span className="ml-auto text-gray-500">сумма:</span>
                                  <span className="font-bold">{dSums[1]}</span>
                                </div>
                              </div>
                              <div className="p-3 rounded-lg border hover:bg-amber-50"
                                   onMouseEnter={() => setHoveredSet([1,5,9])}
                                   onMouseLeave={() => setHoveredSet(null)}>
                                <div className="mb-1"><b>Диагональ 1‑5‑9</b>:</div>
                                <div className="flex items-center gap-2 flex-wrap">
                                  {[1,5,9].map((d,i)=>{ const cfg=chipStyleForDigit(d); return (
                                    <span key={`d2-${i}`} className={`px-1.5 py-0.5 rounded border text-xs ${cfg.cls}`}
                                          onMouseEnter={()=>setHoveredDigit(d)} onMouseLeave={()=>setHoveredDigit(null)}>{d}</span>
                                  );})}
                                  <span className="ml-auto text-gray-500">сумма:</span>
                                  <span className="font-bold">{dSums[0]}</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    } catch { return null; }
                  })()}
                </CardContent>
              </Card>

              {/* Абракадабра — анализ имени и фамилии (после диагоналей) */}
              <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                <CardHeader>
                  <CardTitle>Абракадабра</CardTitle>
                  <CardDescription>Разбор имени и фамилии по буквам и числам</CardDescription>
                </CardHeader>
                <CardContent>
                  {(() => {
                    try {
                      const name = (reportData.personal?.name || '').toUpperCase();
                      const surname = (reportData.personal?.surname || '').toUpperCase();
                      if (!name && !surname) {
                        return <div className="text-sm text-gray-600">Заполните имя и фамилию в профиле, чтобы увидеть расчёт.</div>;
                      }
                      // Используем только латинские буквы имени+фамилии
                      const combined = `${name}${surname}`.replace(/[^A-Z]/g, '');
                      const letters = combined.split('');
                      if (!letters.length) {
                        return <div className="text-sm text-gray-600">Не удалось выделить буквы из имени и фамилии.</div>;
                      }
                      const firstNine = letters.slice(0, 9);
                      if (firstNine.length < 9) {
                        return <div className="text-sm text-gray-600">Для алгоритма требуется минимум 9 латинских букв (имя+фамилия).</div>;
                      }

                      // Пифагорейское соответствие буква → число
                      const letterToDigit = (ch) => {
                        const groups = {
                          1: 'AJS',
                          2: 'BKT',
                          3: 'CLU',
                          4: 'DMV',
                          5: 'ENW',
                          6: 'FOX',
                          7: 'GPY',
                          8: 'HQZ',
                          9: 'IR'
                        };
                        const up = ch.toUpperCase();
                        for (const [num, lettersGroup] of Object.entries(groups)) {
                          if (lettersGroup.includes(up)) return parseInt(num, 10);
                        }
                        return 0;
                      };

                      const baseRow = firstNine.map(letterToDigit);
                      // Строим треугольник сумм: каждый следующий ряд — сумма соседних чисел, сведённая к одной цифре
                      const rows = [baseRow];
                      const reduceDigit = (n) => {
                        let x = Math.abs(n);
                        while (x > 9) x = String(x).split('').reduce((a, b) => a + parseInt(b, 10), 0);
                        return x;
                      };
                      for (let r = 1; r < 9; r++) {
                        const prev = rows[r - 1];
                        const next = [];
                        for (let i = 0; i < prev.length - 1; i++) {
                          next.push(reduceDigit(prev[i] + prev[i + 1]));
                        }
                        rows.push(next);
                      }

                      // Для визуализации имени: берём только имя (без фамилии) для карточек
                      const nameOnly = name.replace(/[^A-Z]/g, '');
                      const nameLetters = nameOnly.split('');
                      const nameDigits = nameLetters.map(letterToDigit);
                      
                      // Полное число имени для последней карточки
                      const fullNameNum = reportData?.personal?.full_name_number
                        ?? reportData?.numerology?.personal_numbers?.full_name_number
                        ?? null;
                      const fullNameDigit = fullNameNum != null ? (() => {
                        let x = Math.abs(parseInt(fullNameNum, 10));
                        while (x > 9) x = String(x).split('').reduce((a, b) => a + parseInt(b, 10), 0);
                        return x;
                      })() : null;

                      // Подготовка данных для человечка
                      const birthISO = reportData?.personal?.birth_date || reportData?.numerology?.personal_numbers?.birth_date;
                      const nameOnlyForHuman = name.replace(/[^A-Z]/g, '');
                      let humanData = null;
                      if (nameOnlyForHuman && birthISO) {
                        try {
                          const toDigits = (s) => s.split('').map(n => parseInt(n, 10));
                          const sum = (arr) => arr.reduce((a, b) => a + b, 0);
                          const reduce = (n) => { let x = Math.abs(n); while (x > 9) x = String(x).split('').reduce((a, b) => a + parseInt(b, 10), 0); return x; };
                          const [yyyy, mm, dd] = birthISO.includes('-') ? birthISO.split('-') : birthISO.split('.').reverse();
                          const dayDigits = toDigits(dd);
                          const monthDigits = toDigits(mm);
                          const yearDigits = toDigits(yyyy);
                          const mindNumber = reduce(sum(monthDigits));
                          const destinySum = sum([...dayDigits, ...monthDigits, ...yearDigits]);
                          const destinyNumber = reduce(destinySum);
                          const nameLetterDigits = nameOnlyForHuman.split('').map(letterToDigit);
                          if (nameLetterDigits.length >= 4) {
                            const head = nameLetterDigits[0];
                            const handLeft = nameLetterDigits[2]; // 3-я буква
                            const handRight = nameLetterDigits[1]; // 2-я буква
                            const soul = nameLetterDigits[3];
                            // Попа: число последней буквы имени
                            const bottomDigit = nameLetterDigits[nameLetterDigits.length - 1];
                            humanData = { head, handLeft, handRight, soul, mindNumber, destinyNumber, bottomDigit };
                          }
                        } catch {}
                      }

                      // Фамилия для визуализации
                      const surnameOnly = surname.replace(/[^A-Z]/g, '');
                      const surnameLetters = surnameOnly.split('');
                      const surnameDigits = surnameLetters.map(letterToDigit);

                      return (
                        <div className="space-y-4">
                          {/* Две колонки: слева треугольник, справа человечек */}
                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {/* Левая колонка: Абракадабра (треугольник) */}
                            <div className="space-y-4">
                              <div className="text-sm font-semibold">Абракадабра</div>
                              
                              {/* Фамилия в левой колонке */}
                              {surnameLetters.length > 0 && (
                                <div className="mb-4">
                                  <div className="text-sm font-semibold mb-2">Фамилия: {surname}</div>
                                  <div className="flex flex-wrap gap-2">
                                    {surnameLetters.map((letter, idx) => {
                                      const digit = surnameDigits[idx];
                                      const cfg = chipStyleForDigit(digit);
                                      return (
                                        <div
                                          key={`surname-card-${idx}`}
                                          className={`flex flex-col items-center justify-center w-16 h-20 rounded-lg border ${cfg.cls} transition-transform duration-150 ease-out hover:scale-110`}
                                        >
                                          <div className="text-2xl font-bold mb-1">{letter}</div>
                                          <div className="text-lg font-semibold">{digit}</div>
                                        </div>
                                      );
                                    })}
                                  </div>
                                </div>
                              )}

                              {/* Таблица: буквы, индексы и треугольник чисел в стиле цветных чипов */}
                              <div className="inline-block">
                                {/* Строка букв */}
                                <div className="grid grid-cols-9 text-center text-sm font-semibold font-mono mb-1">
                                  {firstNine.map((ch, idx) => (
                                    <div key={`ch-${idx}`} className="px-2 py-1">
                                      {ch}
                                    </div>
                                  ))}
                                </div>
                                {/* Строка индексов 1–9 (тоже в цветах планет) */}
                                <div className="grid grid-cols-9 text-center text-[11px] font-mono">
                                  {Array.from({ length: 9 }, (_, i) => i + 1).map((n) => {
                                    const cfg = chipStyleForDigit(n);
                                    return (
                                      <div
                                        key={`idx-${n}`}
                                        className={`flex items-center justify-center min-w-[24px] h-6 mx-[2px] text-[11px] rounded-md ${cfg.cls} transition-transform duration-150 ease-out hover:scale-110`}
                                      >
                                        {n}
                                      </div>
                                    );
                                  })}
                                </div>

                                {/* Числовой треугольник, выровненный по столбцам */}
                                <div className="mt-2">
                                  {/* Первый ряд: базовые числа */}
                                  <div className="grid grid-cols-9 text-center font-mono text-sm mb-1">
                                    {baseRow.map((num, idx) => {
                                      const cfg = chipStyleForDigit(num);
                                      const isHighlighted = hoveredAbracadabraIndex === idx || 
                                                           hoveredAbracadabraIndex === 'all' ||
                                                           (hoveredAbracadabraIndex === 'example' && (idx === 0 || idx === 2));
                                      return (
                                        <div
                                          key={`row0-${idx}`}
                                          className={`flex items-center justify-center min-w-[28px] h-7 mx-[2px] text-sm rounded-md ${cfg.cls} transition-all duration-150 ease-out hover:scale-110 ${isHighlighted ? 'ring-2 ring-amber-400 ring-offset-2 scale-110 z-10' : ''}`}
                                        >
                                          {num}
                                        </div>
                                      );
                                    })}
                                  </div>

                                  {/* Остальные ряды: сдвиг вправо на idx столбцов */}
                                  {rows.slice(1).map((row, idxRow) => (
                                    <div key={`row-${idxRow + 1}`} className="grid grid-cols-9 text-center font-mono text-sm mb-1">
                                      {Array.from({ length: 9 }, (_, col) => {
                                        const offset = idxRow + 1;
                                        const valueIndex = col - offset;
                                        if (valueIndex < 0 || valueIndex >= row.length) {
                                          return <div key={`empty-${idxRow}-${col}`} className="px-2 py-1" />;
                                        }
                                        const num = row[valueIndex];
                                        const cfg = chipStyleForDigit(num);
                                        return (
                                          <div
                                            key={`cell-${idxRow + 1}-${col}`}
                                            className={`flex items-center justify-center min-w-[28px] h-7 mx-[2px] text-sm rounded-md ${cfg.cls} transition-transform duration-150 ease-out hover:scale-110`}
                                          >
                                            {num}
                                          </div>
                                        );
                                      })}
                                    </div>
                                  ))}
                                </div>
                              </div>

                              {/* Алгоритм треугольника */}
                              <div className="p-3 rounded-lg border bg-white/80 text-xs text-gray-700 space-y-1">
                                <div><b>Шаг 1.</b> Из имени <b>{name || '—'}</b> и фамилии <b>{surname || '—'}</b> берём первые 9 латинских букв, например DMIRTIMAL.</div>
                                <div><b>Шаг 2.</b> Каждую букву переводим в число: A,J,S=1; B,K,T=2; C,L,U=3; D,M,V=4; E,N,W=5; F,O,X=6; G,P,Y=7; H,Q,Z=8; I,R=9.</div>
                                <div 
                                  onMouseEnter={() => {
                                    // Подсвечиваем все числа базового ряда
                                    setHoveredAbracadabraIndex('all');
                                  }}
                                  onMouseLeave={() => setHoveredAbracadabraIndex(null)}
                                  className="cursor-pointer hover:bg-amber-50 rounded px-1"
                                >
                                  <b>Шаг 3.</b> Получаем первую строку из 9 чисел — базовый ряд.
                                </div>
                                <div 
                                  onMouseEnter={() => {
                                    // Подсвечиваем пример: 4+9 (индексы 0 и 2 в базовом ряду для DMIRTIMAL)
                                    setHoveredAbracadabraIndex('example');
                                  }}
                                  onMouseLeave={() => setHoveredAbracadabraIndex(null)}
                                  className="cursor-pointer hover:bg-amber-50 rounded px-1"
                                >
                                  <b>Шаг 4.</b> Строим следующий ряд: складываем попарно соседние числа, результат сводим к одной цифре (например, 4+9=13 → 1+3=4).
                                </div>
                                <div><b>Шаг 5.</b> Повторяем шаг 4, пока не останется одно число на вершине треугольника.</div>
                              </div>
                            </div>

                            {/* Правая колонка: Человечек */}
                            <div className="space-y-4">
                              <div className="text-sm font-semibold">Человечек имени</div>
                              
                              {/* Имя в правой колонке */}
                              {nameLetters.length > 0 && (
                                <div className="mb-4">
                                  <div className="text-sm font-semibold mb-2">Имя: {name}</div>
                                  <div className="flex flex-wrap gap-2">
                                    {nameLetters.map((letter, idx) => {
                                      const digit = nameDigits[idx];
                                      const cfg = chipStyleForDigit(digit);
                                      return (
                                        <div
                                          key={`name-card-${idx}`}
                                          className={`flex flex-col items-center justify-center w-16 h-20 rounded-lg border ${cfg.cls} transition-transform duration-150 ease-out hover:scale-110`}
                                        >
                                          <div className="text-2xl font-bold mb-1">{letter}</div>
                                          <div className="text-lg font-semibold">{digit}</div>
                                        </div>
                                      );
                                    })}
                                    {fullNameDigit != null && (
                                      <div
                                        className={`flex flex-col items-center justify-center w-16 h-20 rounded-lg border ${chipStyleForDigit(fullNameDigit).cls} transition-transform duration-150 ease-out hover:scale-110 bg-teal-50 border-teal-300`}
                                      >
                                        <div className="text-2xl font-bold mb-1">Σ</div>
                                        <div className="text-lg font-semibold">{fullNameDigit}</div>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              )}
                              
                              {humanData ? (
                                <>
                                  <div className="flex flex-col items-center">
                                    <div className="grid grid-cols-3 gap-1 w-32">
                                      <div />
                                      {(() => {
                                        const cfg = chipStyleForDigit(humanData.head);
                                        const isHighlighted = hoveredHumanPart === 'head';
                                        return (
                                          <div className={`flex items-center justify-center aspect-square rounded-md ${cfg.cls} transition-all duration-150 ease-out hover:scale-110 ${isHighlighted ? 'ring-2 ring-amber-400 ring-offset-2 scale-110 z-10' : ''}`}>
                                            <span className="text-lg font-bold">{humanData.head}</span>
                                          </div>
                                        );
                                      })()}
                                      <div />

                                      {(() => {
                                        const cfg = chipStyleForDigit(humanData.handLeft);
                                        const isHighlighted = hoveredHumanPart === 'handLeft';
                                        return (
                                          <div className={`flex items-center justify-center aspect-square rounded-md ${cfg.cls} transition-all duration-150 ease-out hover:scale-110 ${isHighlighted ? 'ring-2 ring-amber-400 ring-offset-2 scale-110 z-10' : ''}`}>
                                            <span className="text-lg font-bold">{humanData.handLeft}</span>
                                          </div>
                                        );
                                      })()}
                                      {(() => {
                                        const cfg = chipStyleForDigit(humanData.soul);
                                        const isHighlighted = hoveredHumanPart === 'soul';
                                        return (
                                          <div className={`flex items-center justify-center aspect-square rounded-md ${cfg.cls} transition-all duration-150 ease-out hover:scale-110 ${isHighlighted ? 'ring-2 ring-amber-400 ring-offset-2 scale-110 z-10' : ''}`}>
                                            <span className="text-lg font-bold">{humanData.soul}</span>
                                          </div>
                                        );
                                      })()}
                                      {(() => {
                                        const cfg = chipStyleForDigit(humanData.handRight);
                                        const isHighlighted = hoveredHumanPart === 'handRight';
                                        return (
                                          <div className={`flex items-center justify-center aspect-square rounded-md ${cfg.cls} transition-all duration-150 ease-out hover:scale-110 ${isHighlighted ? 'ring-2 ring-amber-400 ring-offset-2 scale-110 z-10' : ''}`}>
                                            <span className="text-lg font-bold">{humanData.handRight}</span>
                                          </div>
                                        );
                                      })()}

                                      {(() => {
                                        const cfg = chipStyleForDigit(humanData.mindNumber);
                                        const isHighlighted = hoveredHumanPart === 'mindNumber';
                                        return (
                                          <div className={`flex items-center justify-center aspect-square rounded-md ${cfg.cls} transition-all duration-150 ease-out hover:scale-110 ${isHighlighted ? 'ring-2 ring-amber-400 ring-offset-2 scale-110 z-10' : ''}`}>
                                            <span className="text-lg font-bold">{humanData.mindNumber}</span>
                                          </div>
                                        );
                                      })()}
                                      {(() => {
                                        const cfg = chipStyleForDigit(humanData.bottomDigit);
                                        const isHighlighted = hoveredHumanPart === 'bottomDigit';
                                        return (
                                          <div className={`flex items-center justify-center aspect-square rounded-md ${cfg.cls} transition-all duration-150 ease-out hover:scale-110 ${isHighlighted ? 'ring-2 ring-amber-400 ring-offset-2 scale-110 z-10' : ''}`}>
                                            <span className="text-lg font-bold">{humanData.bottomDigit}</span>
                                          </div>
                                        );
                                      })()}
                                      {(() => {
                                        const cfg = chipStyleForDigit(humanData.destinyNumber);
                                        const isHighlighted = hoveredHumanPart === 'destinyNumber';
                                        return (
                                          <div className={`flex items-center justify-center aspect-square rounded-md ${cfg.cls} transition-all duration-150 ease-out hover:scale-110 ${isHighlighted ? 'ring-2 ring-amber-400 ring-offset-2 scale-110 z-10' : ''}`}>
                                            <span className="text-lg font-bold">{humanData.destinyNumber}</span>
                                          </div>
                                        );
                                      })()}
                                    </div>
                                  </div>

                                  {/* Алгоритм человечка */}
                                  <div className="p-3 rounded-lg border bg-white/80 text-xs text-gray-700 space-y-1">
                                    <div 
                                      onMouseEnter={() => setHoveredHumanPart('head')}
                                      onMouseLeave={() => setHoveredHumanPart(null)}
                                      className="cursor-pointer hover:bg-amber-50 rounded px-1"
                                    >
                                      <b>Голова (1‑я буква)</b> — {humanData.head}: мысли, отношение к родителям, то как мы думаем и где реализуемся в работе.
                                    </div>
                                    <div 
                                      onMouseEnter={() => setHoveredHumanPart('handLeft')}
                                      onMouseLeave={() => setHoveredHumanPart(null)}
                                      className="cursor-pointer hover:bg-amber-50 rounded px-1"
                                    >
                                      <b>Левая рука (3‑я буква)</b> — {humanData.handLeft}: чувства, самовыражение, отношения, в том числе в семье (имена партнёра и детей).
                                    </div>
                                    <div 
                                      onMouseEnter={() => setHoveredHumanPart('handRight')}
                                      onMouseLeave={() => setHoveredHumanPart(null)}
                                      className="cursor-pointer hover:bg-amber-50 rounded px-1"
                                    >
                                      <b>Правая рука (2‑я буква)</b> — {humanData.handRight}: злость, неудовлетворённость, реакция на стрессовые ситуации.
                                    </div>
                                    <div 
                                      onMouseEnter={() => setHoveredHumanPart('soul')}
                                      onMouseLeave={() => setHoveredHumanPart(null)}
                                      className="cursor-pointer hover:bg-amber-50 rounded px-1"
                                    >
                                      <b>Душа (4‑я буква)</b> — {humanData.soul}: внутреннее состояние, проживание себя, ощущение места в мире.
                                    </div>
                                    <div 
                                      onMouseEnter={() => setHoveredHumanPart('destinyNumber')}
                                      onMouseLeave={() => setHoveredHumanPart(null)}
                                      className="cursor-pointer hover:bg-amber-50 rounded px-1"
                                    >
                                      <b>Левая нога (число судьбы)</b> — {humanData.destinyNumber}: связь с родом и возможность брать ресурс, опора на судьбу.
                                    </div>
                                    <div 
                                      onMouseEnter={() => setHoveredHumanPart('mindNumber')}
                                      onMouseLeave={() => setHoveredHumanPart(null)}
                                      className="cursor-pointer hover:bg-amber-50 rounded px-1"
                                    >
                                      <b>Правая нога (число ума)</b> — {humanData.mindNumber}: программы рода, привычные сценарии мышления и действий.
                                    </div>
                                    <div 
                                      onMouseEnter={() => setHoveredHumanPart('bottomDigit')}
                                      onMouseLeave={() => setHoveredHumanPart(null)}
                                      className="cursor-pointer hover:bg-amber-50 rounded px-1"
                                    >
                                      <b>Точка опоры / «попа» (последняя буква имени)</b> — {humanData.bottomDigit}: то, как мы фактически действуем и проявляемся в мире.
                                    </div>
                                  </div>
                                </>
                              ) : (
                                <div className="text-xs text-gray-500">Заполните имя и дату рождения в профиле, чтобы увидеть расчёт.</div>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    } catch {
                      return null;
                    }
                  })()}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Вкладка: Планеты */}
          <TabsContent value="planetary" className="space-y-6">
            <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
              <CardHeader>
                <CardTitle>Интерпретация планет в вашей карте</CardTitle>
                <CardDescription>
                  Анализ планетарных энергий на основе квадрата Пифагора. Показаны все планеты с их состоянием и рекомендациями по развитию.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {reportData.pythagoreanSquare ? (
                  <div className="space-y-6">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((num) => {
                      const [rowIdx, colIdx] = INDEX_BY_NUMBER[num];
                      const cell = reportData.pythagoreanSquare.square?.[rowIdx]?.[colIdx] || '';
                      const count = typeof cell === 'string' ? cell.length : Array.isArray(cell) ? cell.length : (cell ? String(cell).length : 0);

                      const colorConfig = CELL_COLORS[num];
                      let interpretation = PLANET_INTERPRETATIONS[num];
                      const planetName = PLANET_NAMES[num];
                      const planetSymbol = PLANET_SYMBOLS[num];
                      
                      // Определяем состояние планеты
                      let strength = 'отсутствует';
                      let strengthColor = 'text-gray-500';
                      if (count >= 3) {
                        strength = 'сильная';
                        strengthColor = 'text-green-600';
                      } else if (count === 2) {
                        strength = 'средняя';
                        strengthColor = 'text-yellow-600';
                      } else if (count === 1) {
                        strength = 'слабая';
                        strengthColor = 'text-gray-600';
                      }

                      // Добавляем специальные рекомендации для отсутствующих планет
                      if (count === 0) {
                        const missingPlanetAdvice = {
                          1: `\n\n⚠️ Энергия Солнца не проявлена в вашей матрице.\n\nЭто означает, что вам нужно осознанно развивать качества лидерства, уверенности в себе и творческой самореализации. Рекомендуется:\n• Проявлять инициативу в повседневных делах\n• Развивать лидерские качества через практику\n• Укреплять самооценку и независимость\n• Заниматься творческими проектами\n• Практиковать утренние ритуалы и солнечные медитации`,
                          2: `\n\n⚠️ Энергия Луны не проявлена в вашей матрице.\n\nЭто означает, что вам нужно развивать эмоциональный интеллект и интуицию. Рекомендуется:\n• Работать с эмоциями и чувствами\n• Развивать эмпатию и способность к сопереживанию\n• Практиковать медитации и интуитивные практики\n• Создавать уютную домашнюю атмосферу\n• Работать с лунными циклами`,
                          3: `\n\n⚠️ Энергия Юпитера не проявлена в вашей матрице.\n\nЭто означает, что вам нужно развивать мудрость и способность к обучению. Рекомендуется:\n• Изучать философию и духовные практики\n• Развивать навыки наставничества и обучения\n• Практиковать благотворительность и помощь другим\n• Читать вдохновляющие книги\n• Развивать оптимизм и веру в лучшее`,
                          4: `\n\n⚠️ Энергия Раху не проявлена в вашей матрице.\n\nЭто означает, что вам нужно развивать амбиции и способность к трансформации. Рекомендуется:\n• Ставить цели и работать над их достижением\n• Развивать здоровые амбиции\n• Практиковать техники трансформации сознания\n• Изучать астрологию и эзотерику\n• Учиться отпускать привязанности`,
                          5: `\n\n⚠️ Энергия Меркурия не проявлена в вашей матрице.\n\nЭто означает, что вам нужно развивать интеллект и коммуникативные навыки. Рекомендуется:\n• Развивать навыки речи и письма\n• Изучать иностранные языки\n• Практиковать логические игры и головоломки\n• Улучшать коммуникацию с окружающими\n• Заниматься дыхательными практиками`,
                          6: `\n\n⚠️ Энергия Венеры не проявлена в вашей матрице.\n\nЭто означает, что вам нужно развивать любовь, красоту и гармонию. Рекомендуется:\n• Заниматься творчеством и искусством\n• Окружать себя красотой\n• Работать над гармонией в отношениях\n• Развивать чувство эстетики\n• Практиковать любовь к себе и другим`,
                          7: `\n\n⚠️ Энергия Кету не проявлена в вашей матрице.\n\nЭто означает, что вам нужно развивать духовность и внутреннюю мудрость. Рекомендуется:\n• Практиковать медитацию и созерцание\n• Изучать духовные учения\n• Работать с прошлыми опытами и кармой\n• Учиться отпускать результаты\n• Развивать интуицию и внутренний голос`,
                          8: `\n\n⚠️ Энергия Сатурна не проявлена в вашей матрице.\n\nЭто означает, что вам нужно развивать дисциплину и ответственность. Рекомендуется:\n• Развивать самодисциплину постепенно\n• Учиться планированию и структурированию\n• Практиковать терпение и настойчивость\n• Брать ответственность за свои действия\n• Создавать структуру в жизни`,
                          9: `\n\n⚠️ Энергия Марса не проявлена в вашей матрице.\n\nЭто означает, что вам нужно развивать активность и решительность. Рекомендуется:\n• Заниматься спортом и физической активностью\n• Развивать здоровую конкуренцию\n• Учиться направлять энергию конструктивно\n• Проявлять смелость в действиях\n• Практиковать боевые искусства или танцы`
                        };
                        interpretation += missingPlanetAdvice[num] || '';
                      }

                      return (
                        <div
                          key={num}
                          className={`rounded-xl border-2 ${colorConfig.border} p-6 bg-gradient-to-br ${colorConfig.bg} ${theme === 'dark' ? 'bg-opacity-20' : ''} ${count === 0 ? 'opacity-75' : ''}`}
                        >
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center gap-3">
                              <div className={`text-4xl ${colorConfig.text} ${count === 0 ? 'opacity-60' : ''}`}>
                                {planetSymbol}
                              </div>
                              <div>
                                <h3 className={`text-xl font-bold ${colorConfig.text} ${count === 0 ? 'opacity-70' : ''}`}>
                                  {planetName} / {num === 1 ? 'Surya' : num === 2 ? 'Chandra' : num === 3 ? 'Guru' : num === 4 ? 'Rahu' : num === 5 ? 'Budha' : num === 6 ? 'Shukra' : num === 7 ? 'Ketu' : num === 8 ? 'Shani' : 'Mangala'} ({num})
                                </h3>
                                <div className="flex items-center gap-3 mt-1">
                                  <span className={`text-sm font-medium ${colorConfig.text} ${count === 0 ? 'opacity-60' : 'opacity-80'}`}>
                                    Количество цифр: <span className="font-bold">{count}</span>
                                  </span>
                                  <span className={`text-sm font-medium ${strengthColor}`}>
                                    Состояние: <span className="font-bold capitalize">{strength}</span>
                                  </span>
                                </div>
                              </div>
                            </div>
                            <div className={`px-3 py-1 rounded-full ${colorConfig.border} bg-white/50 backdrop-blur-sm ${count === 0 ? 'opacity-60' : ''}`}>
                              <span className={`text-lg font-bold ${colorConfig.text}`}>{count}</span>
                            </div>
                          </div>
                          
                          <div className={`mt-4 p-4 rounded-lg ${theme === 'dark' ? 'bg-gray-900/50' : 'bg-white/80'} border ${colorConfig.border}`}>
                            <div className="prose prose-sm max-w-none">
                              <div className={`whitespace-pre-line ${theme === 'dark' ? 'text-gray-200' : 'text-gray-700'}`}>
                                {interpretation}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-64 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg">
                    <div className="text-center">
                      <TrendingUp className="w-12 h-12 text-indigo-600 mx-auto mb-2" />
                      <p className="text-gray-600">Загрузка данных...</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Вкладка: Планетарный маршрут */}
          <TabsContent value="route" className="space-y-6">
            {/* Выбор периода */}
            <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
              <CardContent className="pt-6">
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant={routePeriod === 'daily' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setRoutePeriod('daily')}
                  >
                    День
                  </Button>
                  <Button
                    variant={routePeriod === 'weekly' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setRoutePeriod('weekly')}
                  >
                    Неделя
                  </Button>
                  <Button
                    variant={routePeriod === 'monthly' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setRoutePeriod('monthly')}
                  >
                    Месяц
                  </Button>
                  <Button
                    variant={routePeriod === 'quarterly' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setRoutePeriod('quarterly')}
                  >
                    Квартал
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Отображение данных в зависимости от периода */}
            {routePeriod === 'daily' && reportData.planetaryRoute ? (
              <>
                {/* План действий на день */}
                {reportData.planetaryRoute.day_analysis?.action_plan && (
                  <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Target className="w-5 h-5" />
                        План действий на день
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {/* Утро */}
                        {reportData.planetaryRoute.day_analysis.action_plan.morning?.length > 0 && (
                          <div className="p-4 rounded-lg bg-gradient-to-br from-orange-50 to-yellow-50 border-2 border-orange-200">
                            <div className="flex items-center gap-2 mb-3">
                              <div className="w-8 h-8 rounded-full bg-orange-200 flex items-center justify-center">
                                <Sun className="w-5 h-5 text-orange-600" />
                              </div>
                              <h3 className="font-bold text-orange-700">Утро</h3>
                            </div>
                            <ul className="space-y-2">
                              {reportData.planetaryRoute.day_analysis.action_plan.morning.map((item, idx) => (
                                <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                                  <span className="text-orange-500 mt-1">•</span>
                                  <span>{item}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* День */}
                        {reportData.planetaryRoute.day_analysis.action_plan.afternoon?.length > 0 && (
                          <div className="p-4 rounded-lg bg-gradient-to-br from-yellow-50 to-amber-50 border-2 border-yellow-200">
                            <div className="flex items-center gap-2 mb-3">
                              <div className="w-8 h-8 rounded-full bg-yellow-200 flex items-center justify-center">
                                <Sun className="w-5 h-5 text-yellow-600" />
                              </div>
                              <h3 className="font-bold text-yellow-700">День</h3>
                            </div>
                            <ul className="space-y-2">
                              {reportData.planetaryRoute.day_analysis.action_plan.afternoon.map((item, idx) => (
                                <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                                  <span className="text-yellow-500 mt-1">•</span>
                                  <span>{item}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Вечер */}
                        {reportData.planetaryRoute.day_analysis.action_plan.evening?.length > 0 && (
                          <div className="p-4 rounded-lg bg-gradient-to-br from-purple-50 to-indigo-50 border-2 border-purple-200">
                            <div className="flex items-center gap-2 mb-3">
                              <div className="w-8 h-8 rounded-full bg-purple-200 flex items-center justify-center">
                                <Moon className="w-5 h-5 text-purple-600" />
                              </div>
                              <h3 className="font-bold text-purple-700">Вечер</h3>
                            </div>
                            <ul className="space-y-2">
                              {reportData.planetaryRoute.day_analysis.action_plan.evening.map((item, idx) => (
                                <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                                  <span className="text-purple-500 mt-1">•</span>
                                  <span>{item}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Избегайте */}
                        {reportData.planetaryRoute.day_analysis.action_plan.avoid?.length > 0 && (
                          <div className="p-4 rounded-lg bg-gradient-to-br from-red-50 to-rose-50 border-2 border-red-200">
                            <div className="flex items-center gap-2 mb-3">
                              <div className="w-8 h-8 rounded-full bg-red-200 flex items-center justify-center">
                                <AlertTriangle className="w-5 h-5 text-red-600" />
                              </div>
                              <h3 className="font-bold text-red-700">Избегайте</h3>
                            </div>
                            <ul className="space-y-2">
                              {reportData.planetaryRoute.day_analysis.action_plan.avoid.map((item, idx) => (
                                <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                                  <span className="text-red-500 mt-1">×</span>
                                  <span>{item}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Лучшие часы */}
                        {reportData.planetaryRoute.day_analysis.action_plan.best_hours?.length > 0 && (
                          <div className="p-4 rounded-lg bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200">
                            <div className="flex items-center gap-2 mb-3">
                              <div className="w-8 h-8 rounded-full bg-green-200 flex items-center justify-center">
                                <Clock className="w-5 h-5 text-green-600" />
                              </div>
                              <h3 className="font-bold text-green-700">Лучшие часы</h3>
                            </div>
                            <ul className="space-y-2">
                              {reportData.planetaryRoute.day_analysis.action_plan.best_hours.map((item, idx) => (
                                <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                                  <span className="text-green-500 mt-1">★</span>
                                  <span>{item}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Защитные практики */}
                        {reportData.planetaryRoute.day_analysis.action_plan.protective_practices?.length > 0 && (
                          <div className="p-4 rounded-lg bg-gradient-to-br from-indigo-50 to-purple-50 border-2 border-indigo-200">
                            <div className="flex items-center gap-2 mb-3">
                              <div className="w-8 h-8 rounded-full bg-indigo-200 flex items-center justify-center">
                                <CheckCircle className="w-5 h-5 text-indigo-600" />
                              </div>
                              <h3 className="font-bold text-indigo-700">Защитные практики</h3>
                            </div>
                            <ul className="space-y-2">
                              {reportData.planetaryRoute.day_analysis.action_plan.protective_practices.map((item, idx) => (
                                <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                                  <span className="text-indigo-500 mt-1">◆</span>
                                  <span>{item}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Основная информация */}
                <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Calendar className="w-5 h-5" />
                      Обзор дня
                    </CardTitle>
                    <CardDescription>Персональные рекомендации на текущий день</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      <div className="text-center p-4 rounded-lg bg-gradient-to-br from-orange-50 to-orange-100 border border-orange-200">
                        <div className="text-lg font-semibold text-orange-700">
                          {reportData.planetaryRoute.date ? formatDate(reportData.planetaryRoute.date) : 'Сегодня'}
                        </div>
                        <div className="text-sm text-orange-600 mt-1">Дата</div>
                      </div>
                      <div className="text-center p-4 rounded-lg bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200">
                        <div className="text-lg font-semibold text-blue-700">
                          {reportData.planetaryRoute.city || 'Не указан'}
                        </div>
                        <div className="text-sm text-blue-600 mt-1">Город</div>
                      </div>
                      <div className="text-center p-4 rounded-lg bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200">
                        <div className="text-lg font-semibold text-purple-700">
                          {reportData.planetaryRoute.daily_ruling_planet || '—'}
                        </div>
                        <div className="text-sm text-purple-600 mt-1">Планета дня</div>
                      </div>
                      <div className="text-center p-4 rounded-lg bg-gradient-to-br from-green-50 to-green-100 border border-green-200">
                        <div className="text-lg font-semibold text-green-700">
                          {reportData.planetaryRoute.personal_birth_date || '—'}
                        </div>
                        <div className="text-sm text-green-600 mt-1">Дата рождения</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Благоприятные и неблагоприятные периоды */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Благоприятный период */}
                  {reportData.planetaryRoute.favorable_period && (
                    <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg border-green-200`}>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-green-700">
                          <CheckCircle className="w-5 h-5" />
                          Благоприятный период
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          {reportData.planetaryRoute.favorable_period.start && (
                            <div className="p-4 rounded-lg bg-green-50 border border-green-200">
                              <div className="text-sm text-green-600 mb-1">Абхиджит мухурта</div>
                              <div className="text-xl font-bold text-green-700">
                                {formatTime(reportData.planetaryRoute.favorable_period.start)} - {formatTime(reportData.planetaryRoute.favorable_period.end)}
                              </div>
                              {reportData.planetaryRoute.favorable_period.duration && (
                                <div className="text-sm text-green-600 mt-1">
                                  Длительность: {reportData.planetaryRoute.favorable_period.duration}
                                </div>
                              )}
                            </div>
                          )}
                          {reportData.planetaryRoute.best_activity_hours && reportData.planetaryRoute.best_activity_hours.length > 0 && (
                            <div>
                              <div className="text-sm font-medium text-gray-700 mb-2">Лучшие часы для активности:</div>
                              <div className="space-y-2">
                                {reportData.planetaryRoute.best_activity_hours.map((hour, idx) => (
                                  <div key={idx} className="p-2 rounded bg-green-50 border border-green-200 text-sm text-green-700">
                                    {hour}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Периоды, которых следует избегать */}
                  {reportData.planetaryRoute.avoid_periods && (
                    <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg border-red-200`}>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-red-700">
                          <AlertTriangle className="w-5 h-5" />
                          Периоды, которых следует избегать
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          {reportData.planetaryRoute.avoid_periods.rahu_kaal && reportData.planetaryRoute.avoid_periods.rahu_kaal.start && (
                            <div className="p-3 rounded-lg bg-red-50 border border-red-200">
                              <div className="text-sm font-medium text-red-700 mb-1">Раху кала</div>
                              <div className="text-base font-semibold text-red-800">
                                {formatTime(reportData.planetaryRoute.avoid_periods.rahu_kaal.start)} - {formatTime(reportData.planetaryRoute.avoid_periods.rahu_kaal.end)}
                              </div>
                            </div>
                          )}
                          {reportData.planetaryRoute.avoid_periods.gulika_kaal && reportData.planetaryRoute.avoid_periods.gulika_kaal.start && (
                            <div className="p-3 rounded-lg bg-red-50 border border-red-200">
                              <div className="text-sm font-medium text-red-700 mb-1">Гулика кала</div>
                              <div className="text-base font-semibold text-red-800">
                                {formatTime(reportData.planetaryRoute.avoid_periods.gulika_kaal.start)} - {formatTime(reportData.planetaryRoute.avoid_periods.gulika_kaal.end)}
                              </div>
                            </div>
                          )}
                          {reportData.planetaryRoute.avoid_periods.yamaghanta && reportData.planetaryRoute.avoid_periods.yamaghanta.start && (
                            <div className="p-3 rounded-lg bg-red-50 border border-red-200">
                              <div className="text-sm font-medium text-red-700 mb-1">Ямагханта</div>
                              <div className="text-base font-semibold text-red-800">
                                {formatTime(reportData.planetaryRoute.avoid_periods.yamaghanta.start)} - {formatTime(reportData.planetaryRoute.avoid_periods.yamaghanta.end)}
                              </div>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>

                {/* Почасовой гид */}
                {reportData.planetaryRoute.hourly_guide && reportData.planetaryRoute.hourly_guide.length > 0 && (
                  <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Clock className="w-5 h-5" />
                        Почасовой гид
                      </CardTitle>
                      <CardDescription>Планетарные часы с рекомендациями</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                        {reportData.planetaryRoute.hourly_guide.map((hour, idx) => (
                          <div
                            key={idx}
                            className={`p-4 rounded-lg border-2 ${
                              hour.favorable
                                ? 'bg-green-50 border-green-200'
                                : 'bg-gray-50 border-gray-200'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <div className="text-sm font-medium text-gray-600">
                                {formatTime(hour.start_time)} - {formatTime(hour.end_time)}
                              </div>
                              {hour.favorable ? (
                                <CheckCircle className="w-4 h-4 text-green-600" />
                              ) : (
                                <AlertTriangle className="w-4 h-4 text-gray-400" />
                              )}
                            </div>
                            <div className="text-lg font-bold text-gray-800 mb-1">
                              {hour.planet_ru || hour.planet}
                            </div>
                            {hour.description && (
                              <div className="text-xs text-gray-600 mt-1">
                                {hour.description}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Ежедневные рекомендации */}
                {reportData.planetaryRoute.daily_recommendations && (
                  <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="w-5 h-5" />
                        Ежедневные рекомендации
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {reportData.planetaryRoute.daily_recommendations.favorable_activities && 
                         reportData.planetaryRoute.daily_recommendations.favorable_activities.length > 0 && (
                          <div>
                            <h4 className="font-semibold text-green-700 mb-2 flex items-center gap-2">
                              <CheckCircle className="w-4 h-4" />
                              Благоприятные активности
                            </h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                              {reportData.planetaryRoute.daily_recommendations.favorable_activities.map((activity, idx) => (
                                <div key={idx} className="p-2 rounded bg-green-50 border border-green-200 text-sm text-green-700">
                                  {activity}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        {reportData.planetaryRoute.daily_recommendations.avoid_activities && 
                         reportData.planetaryRoute.daily_recommendations.avoid_activities.length > 0 && (
                          <div>
                            <h4 className="font-semibold text-red-700 mb-2 flex items-center gap-2">
                              <AlertTriangle className="w-4 h-4" />
                              Активности, которых следует избегать
                            </h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                              {reportData.planetaryRoute.daily_recommendations.avoid_activities.map((activity, idx) => (
                                <div key={idx} className="p-2 rounded bg-red-50 border border-red-200 text-sm text-red-700">
                                  {activity}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </>
            ) : routePeriod === 'weekly' && routeData.weekly ? (
              <>
                <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                  <CardHeader>
                    <CardTitle>Планетарный маршрут на неделю</CardTitle>
                    <CardDescription>
                      Неблагоприятные дни (энергия &lt; 60%) выделены красным цветом
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {routeData.weekly.days?.map((day, idx) => {
                        const isChallenging = day.day_type === 'challenging' || (day.avg_energy_per_planet !== undefined && day.avg_energy_per_planet < 60);
                        const avgEnergy = day.avg_energy_per_planet !== undefined ? day.avg_energy_per_planet : null;
                        
                        return (
                          <div 
                            key={idx} 
                            className={`p-4 border-2 rounded-lg transition-all duration-200 cursor-pointer ${
                              isChallenging 
                                ? 'border-red-300 bg-red-50 hover:bg-red-100 hover:shadow-md' 
                                : 'border-green-300 bg-green-50 hover:bg-green-100 hover:shadow-md'
                            }`}
                            onMouseEnter={() => setSelectedDayModal(day)}
                            onMouseLeave={() => setSelectedDayModal(null)}
                            onClick={() => setSelectedDayModal(day)}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <h3 className="font-bold text-lg">
                                {formatDate(day.date)} - {day.weekday_name}
                              </h3>
                              <div className="flex items-center gap-2">
                                {avgEnergy !== null && (
                                  <Badge variant={isChallenging ? 'destructive' : 'default'} className="text-sm">
                                    {avgEnergy.toFixed(1)}%
                                  </Badge>
                                )}
                                {isChallenging ? (
                                  <AlertTriangle className="w-5 h-5 text-red-600" />
                                ) : (
                                  <CheckCircle className="w-5 h-5 text-green-600" />
                                )}
                              </div>
                            </div>
                            {day.day_type_ru && (
                              <div className={`text-sm font-semibold mb-2 ${isChallenging ? 'text-red-700' : 'text-green-700'}`}>
                                {day.day_type_ru}
                              </div>
                            )}
                            {day.day_analysis?.action_plan && (
                              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mt-3">
                                {day.day_analysis.action_plan.morning?.length > 0 && (
                                  <div className="text-sm">
                                    <strong className="text-orange-600">Утро:</strong>
                                    <ul className="list-disc list-inside ml-2">
                                      {day.day_analysis.action_plan.morning.map((item, i) => (
                                        <li key={i}>{item}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                                {day.day_analysis.action_plan.afternoon?.length > 0 && (
                                  <div className="text-sm">
                                    <strong className="text-yellow-600">День:</strong>
                                    <ul className="list-disc list-inside ml-2">
                                      {day.day_analysis.action_plan.afternoon.map((item, i) => (
                                        <li key={i}>{item}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                                {day.day_analysis.action_plan.evening?.length > 0 && (
                                  <div className="text-sm">
                                    <strong className="text-purple-600">Вечер:</strong>
                                    <ul className="list-disc list-inside ml-2">
                                      {day.day_analysis.action_plan.evening.map((item, i) => (
                                        <li key={i}>{item}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>

                {/* Модальное окно с подсказками */}
                <Dialog open={!!selectedDayModal} onOpenChange={(open) => !open && setSelectedDayModal(null)}>
                  <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                    <DialogHeader>
                      <DialogTitle>
                        {selectedDayModal && `${formatDate(selectedDayModal.date)} - ${selectedDayModal.weekday_name}`}
                      </DialogTitle>
                      <DialogDescription>
                        {selectedDayModal && selectedDayModal.day_type_ru && (
                          <span className={`font-semibold ${selectedDayModal.day_type === 'challenging' || (selectedDayModal.avg_energy_per_planet !== undefined && selectedDayModal.avg_energy_per_planet < 60) ? 'text-red-600' : 'text-green-600'}`}>
                            {selectedDayModal.day_type_ru}
                            {selectedDayModal.avg_energy_per_planet !== undefined && ` (${selectedDayModal.avg_energy_per_planet.toFixed(1)}% энергии)`}
                          </span>
                        )}
                      </DialogDescription>
                    </DialogHeader>
                    {selectedDayModal && (
                      <div className="space-y-4 mt-4">
                        {selectedDayModal.day_type === 'challenging' || (selectedDayModal.avg_energy_per_planet !== undefined && selectedDayModal.avg_energy_per_planet < 60) ? (
                          <div className="p-4 rounded-lg bg-red-50 border-2 border-red-200">
                            <h4 className="font-bold text-red-700 mb-2 flex items-center gap-2">
                              <AlertTriangle className="w-5 h-5" />
                              Что требуется сделать в этот день:
                            </h4>
                            <ul className="space-y-2 text-sm text-red-800">
                              <li className="flex items-start gap-2">
                                <span className="text-red-500 mt-1">•</span>
                                <span>Избегайте важных решений и подписания договоров</span>
                              </li>
                              <li className="flex items-start gap-2">
                                <span className="text-red-500 mt-1">•</span>
                                <span>Отложите начало новых проектов и важных дел</span>
                              </li>
                              <li className="flex items-start gap-2">
                                <span className="text-red-500 mt-1">•</span>
                                <span>Сосредоточьтесь на внутренней работе и планировании</span>
                              </li>
                              <li className="flex items-start gap-2">
                                <span className="text-red-500 mt-1">•</span>
                                <span>Практикуйте медитацию и восстановление энергии</span>
                              </li>
                              <li className="flex items-start gap-2">
                                <span className="text-red-500 mt-1">•</span>
                                <span>Избегайте конфликтов и стрессовых ситуаций</span>
                              </li>
                              <li className="flex items-start gap-2">
                                <span className="text-red-500 mt-1">•</span>
                                <span>Проведите время в спокойной обстановке</span>
                              </li>
                            </ul>
                          </div>
                        ) : (
                          <div className="p-4 rounded-lg bg-green-50 border-2 border-green-200">
                            <h4 className="font-bold text-green-700 mb-2 flex items-center gap-2">
                              <CheckCircle className="w-5 h-5" />
                              Что рекомендуется делать в этот день:
                            </h4>
                            <ul className="space-y-2 text-sm text-green-800">
                              <li className="flex items-start gap-2">
                                <span className="text-green-500 mt-1">•</span>
                                <span>Используйте этот день для важных начинаний и подписания договоров</span>
                              </li>
                              <li className="flex items-start gap-2">
                                <span className="text-green-500 mt-1">•</span>
                                <span>Принимайте важные решения и начинайте новые проекты</span>
                              </li>
                              <li className="flex items-start gap-2">
                                <span className="text-green-500 mt-1">•</span>
                                <span>Активно действуйте в профессиональной сфере</span>
                              </li>
                              <li className="flex items-start gap-2">
                                <span className="text-green-500 mt-1">•</span>
                                <span>Планируйте важные встречи и переговоры</span>
                              </li>
                            </ul>
                          </div>
                        )}
                        
                        {selectedDayModal.day_analysis?.action_plan && (
                          <div className="space-y-3">
                            {selectedDayModal.day_analysis.action_plan.morning?.length > 0 && (
                              <div className="p-3 rounded-lg bg-orange-50 border border-orange-200">
                                <strong className="text-orange-700 text-sm">Утро:</strong>
                                <ul className="list-disc list-inside ml-2 mt-1 text-sm text-gray-700">
                                  {selectedDayModal.day_analysis.action_plan.morning.map((item, i) => (
                                    <li key={i}>{item}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {selectedDayModal.day_analysis.action_plan.afternoon?.length > 0 && (
                              <div className="p-3 rounded-lg bg-yellow-50 border border-yellow-200">
                                <strong className="text-yellow-700 text-sm">День:</strong>
                                <ul className="list-disc list-inside ml-2 mt-1 text-sm text-gray-700">
                                  {selectedDayModal.day_analysis.action_plan.afternoon.map((item, i) => (
                                    <li key={i}>{item}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {selectedDayModal.day_analysis.action_plan.evening?.length > 0 && (
                              <div className="p-3 rounded-lg bg-purple-50 border border-purple-200">
                                <strong className="text-purple-700 text-sm">Вечер:</strong>
                                <ul className="list-disc list-inside ml-2 mt-1 text-sm text-gray-700">
                                  {selectedDayModal.day_analysis.action_plan.evening.map((item, i) => (
                                    <li key={i}>{item}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </DialogContent>
                </Dialog>
              </>
            ) : routePeriod === 'monthly' && routeData.monthly ? (
              <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                <CardHeader>
                  <CardTitle>Планетарный маршрут на месяц</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {routeData.monthly.days?.slice(0, 10).map((day, idx) => (
                      <div key={idx} className="p-4 border rounded-lg">
                        <h3 className="font-bold mb-2">{formatDate(day.date)} - {day.weekday_name}</h3>
                        {day.recommendations && (
                          <div className="text-sm text-gray-600">
                            <p><strong>Рекомендации:</strong> {day.recommendations.activities?.join(', ')}</p>
                            {day.recommendations.avoid && (
                              <p><strong>Избегать:</strong> {day.recommendations.avoid.join(', ')}</p>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                    {routeData.monthly.days?.length > 10 && (
                      <p className="text-sm text-gray-500 text-center">
                        И ещё {routeData.monthly.days.length - 10} дней...
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            ) : routePeriod === 'quarterly' && routeData.quarterly ? (
              <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                <CardHeader>
                  <CardTitle>Планетарный маршрут на квартал</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {routeData.quarterly.months?.map((month, idx) => (
                      <div key={idx} className="p-4 border rounded-lg">
                        <h3 className="font-bold mb-2">{month.month_name} {month.year}</h3>
                        <div className="text-sm text-gray-600">
                          <p>Дней в месяце: {month.days?.length || 0}</p>
                          {month.summary && (
                            <p className="mt-2">{month.summary}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                <CardHeader>
                  <CardTitle>
                    Планетарный маршрут {routePeriod === 'daily' ? 'на день' : routePeriod === 'weekly' ? 'на неделю' : routePeriod === 'monthly' ? 'на месяц' : 'на квартал'}
                  </CardTitle>
                  <CardDescription>
                    {routePeriod === 'daily' 
                      ? 'Персональные рекомендации на текущий день'
                      : `Загрузка данных для ${routePeriod === 'weekly' ? 'недели' : routePeriod === 'monthly' ? 'месяца' : 'квартала'}...`}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-center h-64 bg-gradient-to-br from-orange-50 to-yellow-50 rounded-lg">
                    <div className="text-center">
                      <MapPin className="w-12 h-12 text-orange-600 mx-auto mb-2" />
                      <p className="text-gray-600">
                        {routePeriod === 'daily' 
                          ? 'Данные не загружены'
                          : `Загрузка данных для ${routePeriod === 'weekly' ? 'недели' : routePeriod === 'monthly' ? 'месяца' : 'квартала'}...`}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Вкладка: Совместимость */}
          <TabsContent value="compatibility" className="space-y-6">
            {reportData.compatibility ? (
              <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                <CardHeader>
                  <CardTitle>Совместимость</CardTitle>
                  <CardDescription>Анализ совместимости с партнерами</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div className="flex justify-center items-center space-x-8">
                      <div className="text-center">
                        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center mb-2">
                          <span className="text-2xl font-bold text-white">{reportData.compatibility.person1_life_path || '?'}</span>
                        </div>
                        <p className="text-sm text-gray-600">Число судьбы 1</p>
                      </div>
                      <div className="text-center">
                        <div className={`px-6 py-3 rounded-full border-2 ${
                          (reportData.compatibility.compatibility_score || 0) >= 8 ? 'border-green-500 bg-green-50' :
                          (reportData.compatibility.compatibility_score || 0) >= 6 ? 'border-yellow-500 bg-yellow-50' :
                          'border-red-500 bg-red-50'
                        }`}>
                          <span className="text-2xl font-bold">{reportData.compatibility.compatibility_score || 0}/10</span>
                        </div>
                        <p className="text-sm text-gray-600 mt-2">Совместимость</p>
                      </div>
                      <div className="text-center">
                        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-pink-500 to-rose-500 flex items-center justify-center mb-2">
                          <span className="text-2xl font-bold text-white">{reportData.compatibility.person2_life_path || '?'}</span>
                        </div>
                        <p className="text-sm text-gray-600">Число судьбы 2</p>
                      </div>
                    </div>
                    <div className="text-center p-4 bg-gradient-to-br from-pink-50 to-rose-50 rounded-lg">
                      <p className="text-gray-700">{reportData.compatibility.description || 'Описание совместимости'}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                <CardHeader>
                  <CardTitle>Совместимость</CardTitle>
                  <CardDescription>Анализ совместимости с партнерами</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-center h-64 bg-gradient-to-br from-pink-50 to-rose-50 rounded-lg">
                    <div className="text-center">
                      <Users className="w-12 h-12 text-pink-600 mx-auto mb-2" />
                      <p className="text-gray-600">Совместимость не рассчитана</p>
                      <p className="text-sm text-gray-500">Перейдите в раздел "Совместимость" для расчёта</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Вкладка: Нумерология имени */}
          <TabsContent value="name" className="space-y-6">
            {reportData.nameNumerology ? (
              <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                <CardHeader>
                  <CardTitle>Нумерология имени</CardTitle>
                  <CardDescription>Числовой анализ вашего имени</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="text-center p-4 bg-gradient-to-br from-indigo-50 to-blue-50 rounded-lg">
                        <div className="text-3xl font-bold text-indigo-600 mb-2">{reportData.nameNumerology.first_name_number || '?'}</div>
                        <div className="text-sm font-medium text-gray-700">Число имени</div>
                        <div className="text-xs text-gray-500 mt-1">{reportData.nameNumerology.first_name || ''}</div>
                      </div>
                      {reportData.nameNumerology.last_name_number && (
                        <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg">
                          <div className="text-3xl font-bold text-purple-600 mb-2">{reportData.nameNumerology.last_name_number}</div>
                          <div className="text-sm font-medium text-gray-700">Число фамилии</div>
                          <div className="text-xs text-gray-500 mt-1">{reportData.nameNumerology.last_name || ''}</div>
                        </div>
                      )}
                      <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg">
                        <div className="text-3xl font-bold text-blue-600 mb-2">{reportData.nameNumerology.total_name_number || '?'}</div>
                        <div className="text-sm font-medium text-gray-700">Общее число имени</div>
                        <div className="text-xs text-gray-500 mt-1">{reportData.nameNumerology.full_name || ''}</div>
                      </div>
                    </div>
                    <div className="p-4 bg-gradient-to-br from-indigo-50 to-blue-50 rounded-lg">
                      <h4 className="font-semibold mb-2">Интерпретация</h4>
                      <p className="text-sm text-gray-700">{reportData.nameNumerology.total_interpretation || 'Интерпретация не доступна'}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
                <CardHeader>
                  <CardTitle>Нумерология имени</CardTitle>
                  <CardDescription>Числовой анализ вашего имени</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-center h-64 bg-gradient-to-br from-indigo-50 to-blue-50 rounded-lg">
                    <div className="text-center">
                      <Star className="w-12 h-12 text-indigo-600 mx-auto mb-2" />
                      <p className="text-gray-600">Нумерология имени не рассчитана</p>
                      <p className="text-sm text-gray-500">Перейдите в раздел "Нумерология" для расчёта</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Вкладка: Нумерология адреса */}
          <TabsContent value="address" className="space-y-6">
            <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
              <CardHeader>
                <CardTitle>Нумерология адреса</CardTitle>
                <CardDescription>Энергетика вашего места проживания</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-4 bg-gradient-to-br from-green-50 to-blue-50 rounded-lg">
                      <label className="text-sm font-medium text-gray-600">Улица</label>
                      <p className="text-lg font-semibold">{reportData.personal?.street || 'Не указана'}</p>
                    </div>
                    <div className="p-4 bg-gradient-to-br from-green-50 to-blue-50 rounded-lg">
                      <label className="text-sm font-medium text-gray-600">Номер дома</label>
                      <p className="text-lg font-semibold">{reportData.personal?.house_number || 'Не указан'}</p>
                    </div>
                  </div>
                  {reportData.addressNumerology ? (
                    <div className="space-y-4">
                      {reportData.addressNumerology.house_numerology && (
                        <div className="p-4 bg-gradient-to-br from-green-50 to-blue-50 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold">Номер дома</h4>
                            <div className="text-2xl font-bold text-green-600">{reportData.addressNumerology.house_numerology.value}</div>
                          </div>
                          <p className="text-sm text-gray-700">{reportData.addressNumerology.house_numerology.interpretation}</p>
                        </div>
                      )}
                      {reportData.addressNumerology.apartment_numerology && (
                        <div className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold">Номер квартиры</h4>
                            <div className="text-2xl font-bold text-purple-600">{reportData.addressNumerology.apartment_numerology.value}</div>
                          </div>
                          <p className="text-sm text-gray-700">{reportData.addressNumerology.apartment_numerology.interpretation}</p>
                        </div>
                      )}
                      {reportData.addressNumerology.postal_code_numerology && (
                        <div className="p-4 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold">Почтовый индекс</h4>
                            <div className="text-2xl font-bold text-blue-600">{reportData.addressNumerology.postal_code_numerology.value}</div>
                          </div>
                          <p className="text-sm text-gray-700">{reportData.addressNumerology.postal_code_numerology.interpretation}</p>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg">
                      <h4 className="font-semibold mb-2">Числовой анализ адреса</h4>
                      <p className="text-sm text-gray-600">
                        Расчеты нумерологии адреса не выполнены. Перейдите в раздел "Нумерология" для расчёта.
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Вкладка: Нумерология автомобиля */}
          <TabsContent value="car" className="space-y-6">
            <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white'} shadow-lg`}>
              <CardHeader>
                <CardTitle>Нумерология автомобиля</CardTitle>
                <CardDescription>Энергетика вашего транспортного средства</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 bg-gradient-to-br from-orange-50 to-red-50 rounded-lg">
                    <label className="text-sm font-medium text-gray-600">Номер автомобиля</label>
                    <p className="text-lg font-semibold">{reportData.personal?.car_number || reportData.carNumerology?.car_number || 'Не указан'}</p>
                  </div>
                  {reportData.carNumerology ? (
                    <div className="p-4 bg-gradient-to-br from-yellow-50 to-orange-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold">Числовой анализ автомобиля</h4>
                        <div className="text-3xl font-bold text-orange-600">{reportData.carNumerology.numerology_value || '?'}</div>
                      </div>
                      <p className="text-sm text-gray-700 mt-2">{reportData.carNumerology.interpretation || 'Интерпретация не доступна'}</p>
                    </div>
                  ) : (
                    <div className="p-4 bg-gradient-to-br from-yellow-50 to-orange-50 rounded-lg">
                      <h4 className="font-semibold mb-2">Числовой анализ автомобиля</h4>
                      <p className="text-sm text-gray-600">
                        Расчеты нумерологии автомобиля не выполнены. Перейдите в раздел "Нумерология" для расчёта.
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default ComprehensiveReport;
