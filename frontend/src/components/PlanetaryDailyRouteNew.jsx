import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Calendar, Clock, TrendingUp, AlertTriangle, CheckCircle, CheckCircle2, Sparkles, Activity, Target, Info, Loader2, Star, Zap, Shield, CalendarDays, CalendarRange } from 'lucide-react';
import { useAuth } from './AuthContext';
import { getApiBaseUrl } from '../utils/backendUrl';
import { useTheme } from '../hooks/useTheme';
import { getPlanetColor } from './constants/colors';
import { getTitleGlow, getTextGlow, getAccentGlow, getPlanetTitleGlow, getBrightColorForDark } from '../utils/textGlow';

// Получаем информацию о версии сборки
let buildVersion = 'dev';
let buildDate = new Date().toISOString();
try {
  const { getBuildVersion, getBuildDate } = require('../utils/buildInfo');
  buildVersion = getBuildVersion();
  buildDate = getBuildDate();
} catch (e) {
  console.warn('Build info not available, using dev version');
}
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

// Регистрируем компоненты Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const PlanetaryDailyRouteNew = () => {
  const { theme } = useOutletContext();
  const themeConfig = useTheme(theme);
  const [routeData, setRouteData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedMonthDate, setSelectedMonthDate] = useState(new Date().toISOString().split('T')[0]); // Для выбора месяца
  const [selectedQuarterDate, setSelectedQuarterDate] = useState(new Date().toISOString().split('T')[0]); // Для выбора квартала
  const [selectedHour, setSelectedHour] = useState(null);
  const [isHourDialogOpen, setIsHourDialogOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [activeTab, setActiveTab] = useState('day'); // day, week, month, quarter
  const [weeklyData, setWeeklyData] = useState(null);
  const [weeklyLoading, setWeeklyLoading] = useState(false);
  const [monthlyData, setMonthlyData] = useState(null);
  const [monthlyLoading, setMonthlyLoading] = useState(false);
  const [quarterlyData, setQuarterlyData] = useState(null);
  const [quarterlyLoading, setQuarterlyLoading] = useState(false);
  const [selectedDay, setSelectedDay] = useState(null);
  const [isDayDialogOpen, setIsDayDialogOpen] = useState(false);
  const { user } = useAuth();
  const apiBaseUrl = getApiBaseUrl();
  
  // Состояние для хранения стоимостей из API
  const [costs, setCosts] = useState({
    planetary_daily: 1,
    planetary_weekly: 2,
    planetary_monthly: 5,
    planetary_quarterly: 10
  });
  
  // Функция для форматирования даты: день месяц_прописью год
  const formatDateRu = (dateString) => {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return dateString;
      const months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 
                      'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
      return `${date.getDate()} ${months[date.getMonth()]} ${date.getFullYear()}`;
    } catch (e) {
      return dateString;
    }
  };
  
  // Логируем монтирование компонента после инициализации всех переменных
  useEffect(() => {
    console.log('🚀🚀🚀 КОМПОНЕНТ PlanetaryDailyRouteNew МОНТИРУЕТСЯ');
    console.log('🚀 Инициализация компонента:', {
      activeTab,
      hasUser: !!user,
      userEmail: user?.email,
      userCity: user?.city,
      selectedDate,
      routeData: !!routeData,
      weeklyData: !!weeklyData,
      monthlyData: !!monthlyData,
      quarterlyData: !!quarterlyData
    });
  }, []);
  
  // Логируем изменения activeTab для отладки
  useEffect(() => {
    console.log('📊📊📊 activeTab ИЗМЕНИЛСЯ НА:', activeTab);
    console.log('📊 Состояние данных:', {
      routeData: !!routeData,
      weeklyData: !!weeklyData,
      monthlyData: !!monthlyData,
      quarterlyData: !!quarterlyData,
      loading,
      weeklyLoading,
      monthlyLoading,
      quarterlyLoading
    });
  }, [activeTab, routeData, weeklyData, monthlyData, quarterlyData, loading, weeklyLoading, monthlyLoading, quarterlyLoading]);

  // Загружаем стоимости из API при монтировании
  useEffect(() => {
    const fetchCosts = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/credits/costs`);
        if (response.ok) {
          const data = await response.json();
          console.log('💰 Загружены стоимости из API:', data);
          setCosts({
            planetary_daily: data.planetary_daily || 1,
            planetary_weekly: data.planetary_weekly || 2,
            planetary_monthly: data.planetary_monthly || 5,
            planetary_quarterly: data.planetary_quarterly || 10
          });
        } else {
          console.warn('⚠️ Не удалось загрузить стоимости, используем дефолтные');
        }
      } catch (error) {
        console.error('❌ Ошибка загрузки стоимостей:', error);
      }
    };
    fetchCosts();
  }, [apiBaseUrl]);

  // Обновляем текущее время каждую минуту
  useEffect(() => {
    console.log('⏰ Установлен таймер обновления времени');
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000);
    return () => {
      console.log('⏰ Таймер обновления времени очищен');
      clearInterval(timer);
    };
  }, []);

  // УБРАНА автозагрузка - теперь все данные загружаются только по кнопке "Загрузить"

  const loadRouteData = async () => {
    if (!user?.city) {
      console.warn('⚠️ Не могу загрузить данные дня: нет города');
      return;
    }
    
    setLoading(true);
    setError('');
    setRouteData(null); // Сбрасываем старые данные перед загрузкой новых
    
    try {
      const url = `${apiBaseUrl}/vedic-time/planetary-route?date=${selectedDate}&city=${encodeURIComponent(user.city)}`;
      console.log('🔄 Загружаем данные дня:', url);
      
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Ошибка загрузки данных дня: ${response.status} ${errorText}`);
      }
      
      const data = await response.json();
      console.log('📅📅📅 ДАННЫЕ ДНЯ ПОЛУЧЕНЫ:', {
        hasData: !!data,
        hasDayAnalysis: !!data.day_analysis,
        date: data.date,
        city: data.city,
        keys: Object.keys(data || {}),
        fullData: data
      });
      
      console.log('📅 Устанавливаем routeData');
      setRouteData(data);
      console.log('📅 routeData установлен, состояние обновлено');
    } catch (err) {
      console.error('❌ Ошибка загрузки данных дня:', err);
      setError(err.message);
      setRouteData(null);
    } finally {
      setLoading(false);
    }
  };

  // Загрузка недельных данных
  const loadWeeklyData = async () => {
    if (!user?.city) {
      console.warn('⚠️ Не могу загрузить недельные данные: нет города');
      return;
    }
    
    setWeeklyLoading(true);
    setError('');
    setWeeklyData(null); // Сбрасываем старые данные перед загрузкой новых
    
    try {
      const url = `${apiBaseUrl}/vedic-time/planetary-route/weekly?date=${selectedDate}&city=${encodeURIComponent(user.city)}`;
      console.log('🔄 Загружаем недельные данные:', url);
      
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Ошибка загрузки недельных данных: ${response.status} ${errorText}`);
      }
      
      const data = await response.json();
      console.log('📅📅📅 НЕДЕЛЬНЫЕ ДАННЫЕ ПОЛУЧЕНЫ:', {
        hasData: !!data,
        dailyScheduleLength: data.daily_schedule?.length,
        period: data.period,
        startDate: data.start_date,
        endDate: data.end_date,
        keys: Object.keys(data || {}),
        fullData: data
      });
      
      console.log('📅 Устанавливаем weeklyData');
      setWeeklyData(data);
      console.log('📅 weeklyData установлен, состояние обновлено');
    } catch (err) {
      console.error('❌ Ошибка загрузки недельного маршрута:', err);
      setError(err.message);
      setWeeklyData(null);
    } finally {
      setWeeklyLoading(false);
    }
  };

  // Загрузка месячных данных
  const loadMonthlyData = async () => {
    if (!user?.city) {
      console.warn('⚠️ Не могу загрузить месячные данные: нет города');
      return;
    }
    
    setMonthlyLoading(true);
    setError('');
    setMonthlyData(null); // Сбрасываем старые данные перед загрузкой новых
    
    try {
      // Используем selectedMonthDate для загрузки данных выбранного месяца
      const url = `${apiBaseUrl}/vedic-time/planetary-route/monthly?date=${selectedMonthDate}&city=${encodeURIComponent(user.city)}`;
      console.log('🔄 Загружаем месячные данные:', url);
      
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Ошибка загрузки месячных данных: ${response.status} ${errorText}`);
      }
      
      const data = await response.json();
      console.log('📅📅📅 МЕСЯЧНЫЕ ДАННЫЕ ПОЛУЧЕНЫ:', {
        hasData: !!data,
        keys: Object.keys(data || {}),
        dailyScheduleLength: data.daily_schedule?.length,
        hasMonthlySummary: !!data.monthly_summary,
        hasWeeklyAnalysis: !!data.weekly_analysis,
        hasLifeSpheres: !!data.life_spheres,
        hasTrends: !!data.trends,
        hasLunarPhases: !!data.lunar_phases,
        hasPlanetaryTransits: !!data.planetary_transits,
        firstDay: data.daily_schedule?.[0],
        lastDay: data.daily_schedule?.[data.daily_schedule?.length - 1],
        fullData: data
      });
      
      // Проверяем, что данные валидны
      if (!data || !data.daily_schedule || data.daily_schedule.length === 0) {
        console.error('❌❌❌ Месячные данные не содержат daily_schedule или он пуст');
        setError('Данные не содержат расписание дней');
        setMonthlyData(null);
      } else {
        console.log('📅 Устанавливаем monthlyData');
        setMonthlyData(data);
        console.log('📅 monthlyData установлен, состояние обновлено');
        console.log('📅 Проверка после установки:', {
          monthlyData: !!monthlyData,
          newMonthlyData: !!data
        });
      }
    } catch (err) {
      console.error('❌ Ошибка загрузки месячного маршрута:', err);
      setError(err.message);
      setMonthlyData(null);
    } finally {
      setMonthlyLoading(false);
    }
  };

  // Загрузка квартальных данных
  const loadQuarterlyData = async () => {
    if (!user?.city) {
      console.warn('⚠️ Не могу загрузить квартальные данные: нет города');
      return;
    }

    setQuarterlyLoading(true);
    setError('');
    setQuarterlyData(null); // Сбрасываем старые данные перед загрузкой новых

    try {
      const url = `${apiBaseUrl}/vedic-time/planetary-route/quarterly?date=${selectedDate}&city=${encodeURIComponent(user.city)}`;
      console.log('🔄 Загружаем квартальные данные:', url);

      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Ошибка загрузки квартальных данных: ${response.status} ${errorText}`);
      }

      const data = await response.json();
      console.log('📅📅📅 КВАРТАЛЬНЫЕ ДАННЫЕ ПОЛУЧЕНЫ:', {
        hasData: !!data,
        keys: Object.keys(data || {}),
        period: data.period,
        startDate: data.start_date,
        endDate: data.end_date,
        totalWeeks: data.total_weeks,
        hasWeeklySchedule: Array.isArray(data.weekly_schedule),
        weeklyScheduleLength: data.weekly_schedule?.length,
        hasSummary: !!data.quarterly_summary,
        fullData: data
      });

      if (!data || !Array.isArray(data.weekly_schedule) || data.weekly_schedule.length === 0) {
        console.error('❌❌❌ Квартальные данные не содержат weekly_schedule или он пуст');
        setError('Данные не содержат расписание недель квартала');
        setQuarterlyData(null);
      } else {
        console.log('📅 Устанавливаем quarterlyData');
        setQuarterlyData(data);
        console.log('📅 quarterlyData установлен, состояние обновлено');
      }
    } catch (err) {
      console.error('❌ Ошибка загрузки квартального маршрута:', err);
      setError(err.message);
      setQuarterlyData(null);
    } finally {
      setQuarterlyLoading(false);
    }
  };

  // Обработчик переключения вкладок - загружаем данные только при клике
  const handleTabChange = (newTab) => {
    console.log('🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄');
    console.log('🔄 ПЕРЕКЛЮЧЕНИЕ НА ВКЛАДКУ:', newTab);
    console.log('🔄 Текущая вкладка:', activeTab);
    console.log('🔄 User:', user?.email);
    console.log('🔄 City:', user?.city);
    console.log('🔄 Selected Date:', selectedDate);
    console.log('🔄 Текущее состояние данных:', {
      routeData: !!routeData,
      weeklyData: !!weeklyData,
      monthlyData: !!monthlyData,
      quarterlyData: !!quarterlyData,
      loading,
      weeklyLoading,
      monthlyLoading,
      quarterlyLoading
    });
    console.log('🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄');
    
    // Сбрасываем ошибку при переключении вкладок, чтобы ошибки из других периодов не ломали отображение
    setError('');

    // Сначала меняем вкладку
    console.log('🔄 Устанавливаем activeTab на:', newTab);
    setActiveTab(newTab);
    
    // Данные загружаются ТОЛЬКО по кнопке "Загрузить", а не автоматически
    console.log('📋 Переключились на вкладку:', newTab);
  };

  // Функция для получения персонализированных советов для часа (клон из VedicTimeCalculations)
  const getPersonalizedAdvice = async (hour) => {
    if (!hour) return null;

    const planet = hour.planet;
    const planetSanskrit = hour.planet_sanskrit || planet;
    const isNight = hour.period === 'night';
    
    try {
      // Загружаем советы через API (тот же endpoint, что в Ведических временах)
      const response = await fetch(
        `${apiBaseUrl}/vedic-time/planetary-advice/${planet}?is_night=${isNight}`,
        {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        }
      );
      
      if (!response.ok) {
        throw new Error('Не удалось загрузить советы');
      }
      
      const advice = await response.json();
      
      // Добавляем информацию о времени
      const startTime = typeof hour.start === 'string' ? hour.start : hour.start_time?.slice(11, 16) || '';
      const endTime = typeof hour.end === 'string' ? hour.end : hour.end_time?.slice(11, 16) || '';
      advice.time = `${startTime} - ${endTime}`;
      advice.isFavorable = hour.is_favorable;
      
      return advice;
    } catch (error) {
      console.error('Ошибка загрузки советов:', error);
      
      // Fallback: возвращаем базовые советы
      const startTime = typeof hour.start === 'string' ? hour.start : hour.start_time?.slice(11, 16) || '';
      const endTime = typeof hour.end === 'string' ? hour.end : hour.end_time?.slice(11, 16) || '';
      
      return {
        planet,
        planetSanskrit,
        general_advice: `Время ${planetSanskrit} благоприятно для соответствующих планете действий.`,
        activities: ['Следуйте интуиции', 'Будьте внимательны к знакам'],
        avoid: ['Спешка', 'Необдуманные решения'],
        health: 'Заботьтесь о своем здоровье.',
        mantra: `Мантра планеты ${planetSanskrit}`,
        personalized_notes: [],
        time: `${startTime} - ${endTime}`,
        isFavorable: hour.is_favorable
      };
    }
  };

  // Проверка, является ли час текущим
  const isCurrentHour = (hour) => {
    if (!hour || !hour.start || !hour.end) return false;
    if (selectedDate !== new Date().toISOString().split('T')[0]) return false;
    
    try {
      const now = currentTime;
      const currentTimeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
      
      // Извлекаем время из строк формата "HH:MM" или из объектов времени
      const startTime = typeof hour.start === 'string' ? hour.start : hour.start_time?.slice(11, 16) || '';
      const endTime = typeof hour.end === 'string' ? hour.end : hour.end_time?.slice(11, 16) || '';
      
      if (!startTime || !endTime) return false;
      
      const [startHour, startMin] = startTime.split(':').map(Number);
      const [endHour, endMin] = endTime.split(':').map(Number);
      const [currHour, currMin] = currentTimeStr.split(':').map(Number);
      
      const currentMinutes = currHour * 60 + currMin;
      const startMinutes = startHour * 60 + startMin;
      const endMinutes = endHour * 60 + endMin;
      
      return currentMinutes >= startMinutes && currentMinutes < endMinutes;
    } catch (err) {
      console.error('Ошибка проверки текущего часа:', err, hour);
      return false;
    }
  };

  // Убрана глобальная проверка - теперь каждая вкладка управляет своим состоянием загрузки

  // Данные приходят напрямую, а не в route! (только для вкладки "День")
  // Используем routeData напрямую, чтобы избежать проблем с null
  const route = routeData; // Используем routeData для всех случаев, но проверяем внутри компонентов
  const dayAnalysis = routeData?.day_analysis || {};

  // ===============================
  // Квартальный маршрут: вычисления для UI (агрегации на фронте)
  // ===============================
  const quarterWeeks = Array.isArray(quarterlyData?.weekly_schedule) ? quarterlyData.weekly_schedule : [];
  const quarterAllDays = quarterWeeks.flatMap((w) => (Array.isArray(w?.days) ? w.days : []));
  const quarterSummary = quarterlyData?.quarterly_summary || {};

  const normalizeRulingPlanet = (planet) => {
    if (!planet) return '';
    return String(planet).split('(')[0].trim();
  };

  const monthKeyToRuLabel = (yyyyMm) => {
    if (!yyyyMm || typeof yyyyMm !== 'string' || yyyyMm.length < 7) return String(yyyyMm || '');
    const [yyyy, mm] = yyyyMm.split('-');
    const monthIndex = Number(mm) - 1;
    const monthNames = [
      'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
      'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
    ];
    const monthName = monthNames[monthIndex] || mm;
    return `${monthName} ${yyyy}`;
  };

  const buildQuarterMonthSummaries = (days) => {
    const groups = {};
    for (const d of days) {
      const date = d?.date;
      if (!date || typeof date !== 'string' || date.length < 10) continue;
      const key = date.slice(0, 7); // YYYY-MM
      if (!groups[key]) groups[key] = [];
      groups[key].push(d);
    }

    const keys = Object.keys(groups).sort();
    return keys.map((key) => {
      const monthDays = groups[key] || [];
      const sortedByDate = [...monthDays].sort((a, b) => String(a?.date || '').localeCompare(String(b?.date || '')));

      const favorableDays = monthDays.filter((d) => d?.day_type !== 'challenging');
      const challengingDays = monthDays.filter((d) => d?.day_type === 'challenging');
      const energies = monthDays
        .map((d) => (typeof d?.avg_energy_per_planet === 'number' ? d.avg_energy_per_planet : null))
        .filter((v) => typeof v === 'number');
      const avgEnergy = energies.length ? energies.reduce((a, b) => a + b, 0) / energies.length : 0;

      const planetCounts = {};
      for (const d of monthDays) {
        const p = normalizeRulingPlanet(d?.ruling_planet);
        if (!p) continue;
        planetCounts[p] = (planetCounts[p] || 0) + 1;
      }
      const dominantPlanet = Object.entries(planetCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || '';

      const bestDays = [...monthDays]
        .filter((d) => typeof d?.avg_energy_per_planet === 'number')
        .sort((a, b) => (b.avg_energy_per_planet || 0) - (a.avg_energy_per_planet || 0))
        .slice(0, 5);

      const hardDays = [...monthDays]
        .filter((d) => d?.day_type === 'challenging')
        .sort((a, b) => (Number(a?.avg_energy_per_planet || 0) - Number(b?.avg_energy_per_planet || 0)))
        .slice(0, 5);

      return {
        key,
        label: monthKeyToRuLabel(key),
        start_date: sortedByDate[0]?.date,
        end_date: sortedByDate[sortedByDate.length - 1]?.date,
        days_count: monthDays.length,
        favorable_days_count: favorableDays.length,
        challenging_days_count: challengingDays.length,
        avg_energy: Math.round(avgEnergy * 10) / 10,
        dominant_planet: dominantPlanet,
        planet_counts: planetCounts,
        best_days: bestDays,
        challenging_days: hardDays
      };
    });
  };

  const quarterMonthSummaries = buildQuarterMonthSummaries(quarterAllDays);

  const computeQuarterEnergyTrend = (weeks) => {
    if (!weeks?.length) return null;
    const weekAvg = weeks.map((w) => {
      const ds = Array.isArray(w?.days) ? w.days : [];
      const vals = ds
        .map((d) => (typeof d?.avg_energy_per_planet === 'number' ? d.avg_energy_per_planet : null))
        .filter((v) => typeof v === 'number');
      const avg = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
      return Math.round(avg * 10) / 10;
    });

    const n = weekAvg.length;
    const slice = Math.max(1, Math.floor(n / 3));
    const first = weekAvg.slice(0, slice);
    const last = weekAvg.slice(n - slice);
    const avgFirst = first.reduce((a, b) => a + b, 0) / first.length;
    const avgLast = last.reduce((a, b) => a + b, 0) / last.length;
    const diff = avgLast - avgFirst;

    const threshold = 1.5;
    const trend = diff > threshold ? 'рост' : diff < -threshold ? 'снижение' : 'стабильно';

    return {
      trend,
      avg_first: Math.round(avgFirst * 10) / 10,
      avg_last: Math.round(avgLast * 10) / 10,
      diff: Math.round(diff * 10) / 10,
      week_avg: weekAvg
    };
  };

  const quarterEnergyTrend = computeQuarterEnergyTrend(quarterWeeks);
  const quarterTopDays = [...quarterAllDays]
    .filter((d) => typeof d?.avg_energy_per_planet === 'number')
    .sort((a, b) => (b.avg_energy_per_planet || 0) - (a.avg_energy_per_planet || 0))
    .slice(0, 7);

  const quarterHardDays = [...quarterAllDays]
    .filter((d) => d?.day_type === 'challenging')
    .sort((a, b) => (Number(a?.avg_energy_per_planet || 0) - Number(b?.avg_energy_per_planet || 0)))
    .slice(0, 7);

  const quarterWeekMetrics = quarterWeeks.map((w) => {
    const days = Array.isArray(w?.days) ? w.days : [];
    const planetCounts = {};
    for (const d of days) {
      const p = normalizeRulingPlanet(d?.ruling_planet);
      if (!p) continue;
      planetCounts[p] = (planetCounts[p] || 0) + 1;
    }
    const dominantPlanet = Object.entries(planetCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || '';
    const vals = days
      .map((d) => (typeof d?.avg_energy_per_planet === 'number' ? d.avg_energy_per_planet : null))
      .filter((v) => typeof v === 'number');
    const avgEnergy = vals.length ? Math.round(((vals.reduce((a, b) => a + b, 0) / vals.length) * 10)) / 10 : 0;
    const challengingCount = days.filter((d) => d?.day_type === 'challenging').length;
    const favorableCount = days.filter((d) => d?.day_type !== 'challenging').length;
    return {
      ...w,
      dominant_planet: dominantPlanet,
      avg_energy: avgEnergy,
      favorable_days_count: favorableCount,
      challenging_days_count: challengingCount
    };
  });

  const quarterWeekByNumber = new Map(
    quarterWeekMetrics
      .filter((w) => typeof w?.week_number === 'number')
      .map((w) => [w.week_number, w])
  );

  return (
    <div className={`min-h-screen ${themeConfig.pageBackground} relative overflow-hidden`}>
      {/* Фоновый градиент */}
      <div 
        className="fixed inset-0 pointer-events-none"
        style={{ background: themeConfig.overlayGradient }}
      />
      
      <div className="relative z-10 max-w-7xl mx-auto p-6 space-y-6">
        {/* Заголовок */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className={`text-3xl font-bold ${themeConfig.text} drop-shadow-lg`}>
                Планетарный маршрут
              </h1>
              <Badge className={`${themeConfig.isDark ? 'bg-purple-500/20 text-purple-300 border-purple-500/40' : 'bg-purple-100 text-purple-700 border-purple-300'} text-xs font-mono`}>
                v{buildVersion}
              </Badge>
            </div>
            <p className={`mt-2 ${themeConfig.mutedText}`}>
              Детальный анализ с персональными рекомендациями
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className={`${themeConfig.surface} backdrop-blur-xl`}
            />
            <Button onClick={loadRouteData} className="backdrop-blur-xl">
              <Calendar className="h-4 w-4 mr-2" />
              Обновить
            </Button>
          </div>
        </div>

        {/* Табы для разных периодов */}
          <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
          <TabsList className={`grid w-full grid-cols-4 ${themeConfig.surface} backdrop-blur-xl p-1 rounded-2xl`}>
            <TabsTrigger 
              value="day" 
              className={`rounded-xl transition-all duration-300 ${
                activeTab === 'day' 
                  ? 'bg-gradient-to-r from-purple-500/20 to-blue-500/20 text-white shadow-lg' 
                  : themeConfig.mutedText
              }`}
            >
              <Calendar className="h-4 w-4 mr-2" />
              День
            </TabsTrigger>
            <TabsTrigger 
              value="week" 
              className={`rounded-xl transition-all duration-300 ${
                activeTab === 'week' 
                  ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 text-white shadow-lg' 
                  : themeConfig.mutedText
              }`}
            >
              <CalendarDays className="h-4 w-4 mr-2" />
              Неделя
            </TabsTrigger>
            <TabsTrigger 
              value="month" 
              className={`rounded-xl transition-all duration-300 ${
                activeTab === 'month' 
                  ? 'bg-gradient-to-r from-cyan-500/20 to-teal-500/20 text-white shadow-lg' 
                  : themeConfig.mutedText
              }`}
            >
              <CalendarRange className="h-4 w-4 mr-2" />
              Месяц
            </TabsTrigger>
            <TabsTrigger 
              value="quarter" 
              className={`rounded-xl transition-all duration-300 ${
                activeTab === 'quarter' 
                  ? 'bg-gradient-to-r from-teal-500/20 to-green-500/20 text-white shadow-lg' 
                  : themeConfig.mutedText
              }`}
            >
              <CalendarRange className="h-4 w-4 mr-2" />
              Квартал
            </TabsTrigger>
          </TabsList>

          {/* Число мудрости, с которым посчитан открытый маршрут: судьба + полное число имени из профиля */}
          {({ day: routeData, week: weeklyData, month: monthlyData, quarter: quarterlyData })[activeTab]?.wisdom_note && (
            <p className={`mt-4 text-sm ${themeConfig.mutedText}`}>
              {({ day: routeData, week: weeklyData, month: monthlyData, quarter: quarterlyData })[activeTab].wisdom_note}
            </p>
          )}

          {/* Контент для дня */}
          <TabsContent value="day" className="mt-6 space-y-6">
            {/* Селектор даты и кнопка загрузки */}
            <div className={`mb-6 rounded-2xl border p-6 ${themeConfig.glass}`}>
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div className="flex items-center gap-3">
                  <Calendar className="h-5 w-5 text-purple-500" />
                  <h3 className={`text-lg font-semibold ${themeConfig.text}`}>
                    Выберите день для просмотра
                  </h3>
                  {user && (
                    <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/40">
                      Баланс: {user.credits_remaining ?? 0} баллов
                    </Badge>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <Input
                    type="date"
                    value={selectedDate}
                    onChange={(e) => {
                      setSelectedDate(e.target.value);
                      console.log('📅 Выбрана новая дата дня:', e.target.value);
                    }}
                    className={`w-48 ${themeConfig.surface} backdrop-blur-xl`}
                  />
                  <Button 
                    onClick={loadRouteData}
                    disabled={loading || !user?.city}
                    className="bg-purple-500 hover:bg-purple-600"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Загрузка...
                      </>
                    ) : (
                      <>
                        <Calendar className="h-4 w-4 mr-2" />
                        Загрузить ({costs.planetary_daily} {costs.planetary_daily === 1 ? 'балл' : 'балла'})
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>

            {!user?.city ? (
              <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                <div className="text-center py-12">
                  <Info className={`h-16 w-16 mx-auto mb-4 ${themeConfig.mutedText}`} />
                  <h3 className={`text-2xl font-bold mb-2 ${themeConfig.text}`}>
                    Укажите город в профиле
                  </h3>
                  <p className={themeConfig.mutedText}>
                    Для расчета планетарного маршрута нужен город.
                  </p>
                </div>
              </div>
            ) : loading ? (
              <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                <div className={`flex items-center justify-center py-12 ${themeConfig.text}`}>
                  <Loader2 className="h-8 w-8 animate-spin text-purple-500 mr-3" />
                  <span>Загрузка планетарного маршрута на день...</span>
                </div>
              </div>
            ) : !routeData ? (
              <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                <div className="text-center py-12">
                  <Calendar className={`h-16 w-16 mx-auto mb-4 ${themeConfig.mutedText}`} />
                  <h3 className={`text-2xl font-bold mb-2 ${themeConfig.text}`}>
                    Планетарный маршрут на день
                  </h3>
                  <p className={`${themeConfig.mutedText} mb-4`}>
                    Детальный анализ планетарных часов и персональные рекомендации
                  </p>
                  
                  {/* Блок со стоимостью */}
                  <div className={`inline-block p-4 rounded-xl border-2 border-dashed mb-6 ${themeConfig.isDark ? 'border-purple-500/40 bg-purple-500/10' : 'border-purple-300 bg-purple-50'}`}>
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">💰</span>
                      <span className={`font-semibold ${themeConfig.text}`}>Стоимость:</span>
                      <span className={`text-2xl font-bold ${themeConfig.isDark ? 'text-purple-400' : 'text-purple-600'}`}>
                        {costs.planetary_daily} {costs.planetary_daily === 1 ? 'балл' : costs.planetary_daily >= 2 && costs.planetary_daily <= 4 ? 'балла' : 'баллов'}
                      </span>
                    </div>
                    {user && (
                      <p className={`text-sm mt-2 ${themeConfig.mutedText}`}>
                        Ваш баланс: <span className="font-bold">{user.credits_remaining ?? 0}</span> баллов
                      </p>
                    )}
                  </div>
                  
                  <div>
                    <Button 
                      onClick={loadRouteData} 
                      disabled={loading || !user?.city || (user?.credits_remaining ?? 0) < costs.planetary_daily}
                      className="bg-purple-500 hover:bg-purple-600 text-lg py-6 px-8"
                    >
                      <Calendar className="h-5 w-5 mr-2" />
                      Загрузить маршрут ({costs.planetary_daily} {costs.planetary_daily === 1 ? 'балл' : costs.planetary_daily >= 2 && costs.planetary_daily <= 4 ? 'балла' : 'баллов'})
                    </Button>
                    {(user?.credits_remaining ?? 0) < costs.planetary_daily && (
                      <p className="text-red-500 text-sm mt-2">⚠️ Недостаточно баллов</p>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <>
                {/* Общая оценка дня */}
        <div 
          className={`rounded-3xl border p-8 transition-all duration-500 hover:-translate-y-1 ${themeConfig.glass}`}
          style={{
            borderColor: getPlanetColor(routeData?.schedule?.weekday?.ruling_planet) + '40',
            boxShadow: `0 0 40px ${getPlanetColor(routeData?.schedule?.weekday?.ruling_planet)}20`
          }}
        >
          <div className="flex items-center gap-3 mb-6">
            <Sparkles 
              className="h-6 w-6 drop-shadow-[0_0_10px_rgba(255,255,255,0.45)]" 
              style={{ color: getPlanetColor(routeData?.schedule?.weekday?.ruling_planet) }}
            />
            <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
              Персональный анализ дня
            </h2>
          </div>
          
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="flex-1">
              <div className="flex items-baseline gap-3">
                <div 
                  className="text-6xl font-bold drop-shadow-lg"
                  style={{ 
                    color: getPlanetColor(routeData?.schedule?.weekday?.ruling_planet),
                    textShadow: `0 0 20px ${getPlanetColor(routeData?.schedule?.weekday?.ruling_planet)}80`
                  }}
                >
                  {dayAnalysis.overall_score || 0}
                </div>
                <div className={`text-2xl ${themeConfig.mutedText}`}>баллов</div>
              </div>
              <div className="mt-3 flex items-center gap-3">
                <div className={`text-xl font-semibold ${themeConfig.text}`}>
                  {dayAnalysis.overall_rating}
                </div>
                <div className="text-sm text-gray-500">•</div>
                <div className={`text-sm ${themeConfig.mutedText}`}>
                  {routeData?.schedule?.weekday?.name_ru}
                </div>
              </div>
            </div>
            
            <div className="flex flex-col gap-3">
              <div 
                className="px-6 py-3 rounded-2xl font-semibold text-center backdrop-blur-xl"
                style={{
                  backgroundColor: getPlanetColor(routeData?.schedule?.weekday?.ruling_planet) + '30',
                  color: themeConfig.isDark 
                    ? getBrightColorForDark(getPlanetColor(routeData?.schedule?.weekday?.ruling_planet))
                    : getPlanetColor(routeData?.schedule?.weekday?.ruling_planet),
                  boxShadow: `0 0 20px ${getPlanetColor(routeData?.schedule?.weekday?.ruling_planet)}40`,
                  textShadow: themeConfig.isDark 
                    ? `0 0 10px ${getBrightColorForDark(getPlanetColor(routeData?.schedule?.weekday?.ruling_planet))}60`
                    : undefined
                }}
              >
                {routeData?.schedule?.weekday?.ruling_planet}
              </div>
              <div className={`px-4 py-2 rounded-xl text-sm font-medium text-center ${
                dayAnalysis.color_class === 'green' ? 'bg-green-500/20 text-green-300 border border-green-500/40' :
                dayAnalysis.color_class === 'blue' ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40' :
                dayAnalysis.color_class === 'orange' ? 'bg-orange-500/20 text-orange-300 border border-orange-500/40' :
                'bg-gray-500/20 text-gray-300 border border-gray-500/40'
              }`}>
                {dayAnalysis.influence?.dynamic || 'Сбалансированное'}
              </div>
            </div>
          </div>
        </div>

        {/* Ваши сильные стороны */}
        <div className={`hidden rounded-3xl border p-8 ${themeConfig.glass}`}>
          <div className="flex items-center gap-3 mb-6">
            <Star className="h-6 w-6 text-yellow-500 drop-shadow-[0_0_10px_rgba(234,179,8,0.5)]" />
            <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
              Ваши сильные стороны сегодня
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {dayAnalysis.positive_aspects?.slice(0, 6).map((aspect, idx) => {
              // Проверяем, является ли аспект объектом с детальной информацией
              const isDetailedAspect = typeof aspect === 'object' && aspect.type;
              const displayText = isDetailedAspect ? aspect.short_text : aspect;
              const icon = isDetailedAspect ? aspect.icon : '';
              
              return (
                <div 
                  key={idx} 
                  className={`p-5 rounded-2xl border transition-all duration-300 hover:-translate-y-1 hover:shadow-lg ${themeConfig.surface}`}
                  style={{
                    borderColor: '#10b98140',
                    backgroundColor: themeConfig.isDark ? '#10b98110' : '#10b98108'
                  }}
                >
                  <div className="flex items-start gap-3">
                    {icon && <span className="text-2xl flex-shrink-0">{icon}</span>}
                    {!icon && <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0 drop-shadow-[0_0_8px_rgba(34,197,94,0.5)]" />}
                    <div className="flex-1">
                      <p className={`text-sm leading-relaxed ${themeConfig.text}`}>{displayText}</p>
                      {isDetailedAspect && (
                        <div className="mt-2 flex items-center gap-1 text-xs text-green-500">
                          <Info className="h-3 w-3" />
                          <span>Нажмите для подробностей</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Области для развития */}
        {dayAnalysis.challenges && dayAnalysis.challenges.length > 0 && (
          <div className={`hidden rounded-3xl border p-8 ${themeConfig.glass}`}>
            <div className="flex items-center gap-3 mb-6">
              <Target className="h-6 w-6 text-orange-500 drop-shadow-[0_0_10px_rgba(249,115,22,0.5)]" />
              <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
                Области для развития
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {dayAnalysis.challenges.map((challenge, idx) => {
                // Проверяем, является ли challenge объектом с детальной информацией
                const isDetailedChallenge = typeof challenge === 'object' && challenge.type;
                const displayText = isDetailedChallenge ? challenge.short_text : challenge;
                const icon = isDetailedChallenge ? challenge.icon : '';
                
                return (
                  <div 
                    key={idx}
                    className={`p-5 rounded-2xl border transition-all duration-300 hover:-translate-y-1 hover:shadow-lg ${themeConfig.surface}`}
                    style={{
                      borderColor: '#f9731640',
                      backgroundColor: themeConfig.isDark ? '#f9731610' : '#f9731608'
                    }}
                  >
                    <div className="flex items-start gap-3">
                      {icon && <span className="text-2xl flex-shrink-0">{icon}</span>}
                      {!icon && <AlertTriangle className="h-5 w-5 text-orange-500 mt-0.5 flex-shrink-0 drop-shadow-[0_0_8px_rgba(249,115,22,0.5)]" />}
                      <div className="flex-1">
                        <p className={`text-sm leading-relaxed ${themeConfig.text}`}>{displayText}</p>
                        {isDetailedChallenge && (
                          <div className="mt-2 flex items-center gap-1 text-xs text-orange-500">
                            <Info className="h-3 w-3" />
                            <span>Нажмите для решения</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Сила планет в вашей карте */}
        <div className={`hidden rounded-3xl border p-8 ${themeConfig.glass}`}>
          <div className="flex items-center gap-3 mb-6">
            <Shield className="h-6 w-6 text-indigo-500 drop-shadow-[0_0_10px_rgba(99,102,241,0.5)]" />
            <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
              Сила планет в вашей карте
            </h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {dayAnalysis.all_planet_counts && Object.entries(dayAnalysis.all_planet_counts).map(([planet, count]) => {
              const planetColor = getPlanetColor(planet);
              return (
                <div 
                  key={planet} 
                  className={`p-5 rounded-2xl border text-center transition-all duration-300 hover:-translate-y-1 hover:shadow-lg ${themeConfig.surface}`}
                  style={{
                    borderColor: planetColor + '40',
                    backgroundColor: themeConfig.isDark ? planetColor + '10' : planetColor + '08'
                  }}
                >
                  <div 
                    className="text-xl font-bold mb-2 drop-shadow-lg"
                    style={{ 
                      color: planetColor,
                      textShadow: `0 0 10px ${planetColor}60`
                    }}
                  >
                    {planet}
                  </div>
                  <div 
                    className="text-4xl font-bold mb-2"
                    style={{ color: planetColor }}
                  >
                    {count}
                  </div>
                  <div className="text-sm">
                    {[...Array(Math.min(count, 5))].map((_, i) => (
                      <span 
                        key={i} 
                        className="inline-block"
                        style={{ 
                          color: planetColor,
                          filter: `drop-shadow(0 0 4px ${planetColor}60)`
                        }}
                      >
                        ⭐
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* План действий на день */}
        {dayAnalysis.action_plan && (
          <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
            <div className="flex items-center gap-3 mb-6">
              <Activity className="h-6 w-6 text-purple-500 drop-shadow-[0_0_10px_rgba(168,85,247,0.5)]" />
              <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
                План действий на день
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Утро */}
              {dayAnalysis.action_plan.morning && dayAnalysis.action_plan.morning.length > 0 && (
                <div className={`p-5 rounded-2xl border ${themeConfig.surface}`} style={{
                  borderColor: '#fbbf2440',
                  backgroundColor: themeConfig.isDark ? '#fbbf2410' : '#fbbf2408'
                }}>
                  <h3 className="font-bold text-lg mb-3 flex items-center gap-2" style={{ color: '#fbbf24' }}>
                    🌅 Утро
                  </h3>
                  <ul className="space-y-2">
                    {dayAnalysis.action_plan.morning.map((item, idx) => (
                      <li key={idx} className={`text-sm flex items-start gap-2 ${themeConfig.text}`}>
                        <span className="text-yellow-500 mt-0.5">▸</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* День */}
              {dayAnalysis.action_plan.afternoon && dayAnalysis.action_plan.afternoon.length > 0 && (
                <div className={`p-5 rounded-2xl border ${themeConfig.surface}`} style={{
                  borderColor: '#f9731640',
                  backgroundColor: themeConfig.isDark ? '#f9731610' : '#f9731608'
                }}>
                  <h3 className="font-bold text-lg mb-3 flex items-center gap-2" style={{ color: '#f97316' }}>
                    ☀️ День
                  </h3>
                  <ul className="space-y-2">
                    {dayAnalysis.action_plan.afternoon.map((item, idx) => (
                      <li key={idx} className={`text-sm flex items-start gap-2 ${themeConfig.text}`}>
                        <span className="text-orange-500 mt-0.5">▸</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Вечер */}
              {dayAnalysis.action_plan.evening && dayAnalysis.action_plan.evening.length > 0 && (
                <div className={`p-5 rounded-2xl border ${themeConfig.surface}`} style={{
                  borderColor: '#8b5cf640',
                  backgroundColor: themeConfig.isDark ? '#8b5cf610' : '#8b5cf608'
                }}>
                  <h3 className="font-bold text-lg mb-3 flex items-center gap-2" style={{ color: '#8b5cf6' }}>
                    🌙 Вечер
                  </h3>
                  <ul className="space-y-2">
                    {dayAnalysis.action_plan.evening.map((item, idx) => (
                      <li key={idx} className={`text-sm flex items-start gap-2 ${themeConfig.text}`}>
                        <span className="text-purple-500 mt-0.5">▸</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Что избегать */}
              {dayAnalysis.action_plan.avoid && dayAnalysis.action_plan.avoid.length > 0 && (
                <div className={`p-5 rounded-2xl border ${themeConfig.surface}`} style={{
                  borderColor: '#ef444440',
                  backgroundColor: themeConfig.isDark ? '#ef444410' : '#ef444408'
                }}>
                  <h3 className="font-bold text-lg mb-3 flex items-center gap-2" style={{ color: '#ef4444' }}>
                    ⛔ Избегайте
                  </h3>
                  <ul className="space-y-2">
                    {dayAnalysis.action_plan.avoid.map((item, idx) => (
                      <li key={idx} className={`text-sm flex items-start gap-2 ${themeConfig.text}`}>
                        <span className="text-red-500 mt-0.5">✕</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Лучшие часы */}
              {dayAnalysis.action_plan.best_hours && dayAnalysis.action_plan.best_hours.length > 0 && (
                <div className={`p-5 rounded-2xl border ${themeConfig.surface}`} style={{
                  borderColor: '#10b98140',
                  backgroundColor: themeConfig.isDark ? '#10b98110' : '#10b98108'
                }}>
                  <h3 className="font-bold text-lg mb-3 flex items-center gap-2" style={{ color: '#10b981' }}>
                    ⏰ Лучшие часы
                  </h3>
                  <ul className="space-y-2">
                    {dayAnalysis.action_plan.best_hours.map((item, idx) => (
                      <li key={idx} className={`text-sm flex items-start gap-2 ${themeConfig.text}`}>
                        <span className="text-green-500 mt-0.5">⭐</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Защитные практики */}
              {dayAnalysis.action_plan.protective_practices && dayAnalysis.action_plan.protective_practices.length > 0 && (
                <div className={`p-5 rounded-2xl border ${themeConfig.surface}`} style={{
                  borderColor: '#6366f140',
                  backgroundColor: themeConfig.isDark ? '#6366f110' : '#6366f108'
                }}>
                  <h3 className="font-bold text-lg mb-3 flex items-center gap-2" style={{ color: '#6366f1' }}>
                    🛡️ Защитные практики
                  </h3>
                  <ul className="space-y-2">
                    {dayAnalysis.action_plan.protective_practices.map((item, idx) => (
                      <li key={idx} className={`text-sm flex items-start gap-2 ${themeConfig.text}`}>
                        <span className="text-indigo-500 mt-0.5">◆</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* График планетарных энергий */}
        {routeData?.planetary_energies && Object.keys(routeData.planetary_energies).length > 0 && (
          <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
            <div className="flex items-center gap-3 mb-6">
              <Activity className="h-6 w-6 text-purple-500 drop-shadow-[0_0_10px_rgba(168,85,247,0.5)]" />
              <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
                Энергия планет на день
              </h2>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(routeData.planetary_energies).map(([planetKey, energy]) => {
                  const planetNames = {
                    surya: 'Сурья (Солнце)',
                    chandra: 'Чандра (Луна)',
                    mangal: 'Мангал (Марс)',
                    budha: 'Будха (Меркурий)',
                    guru: 'Гуру (Юпитер)',
                    shukra: 'Шукра (Венера)',
                    shani: 'Шани (Сатурн)',
                    rahu: 'Раху',
                    ketu: 'Кету'
                  };
                  const planetColor = getPlanetColor(planetKey.charAt(0).toUpperCase() + planetKey.slice(1));
                  const energyPercent = Math.round(energy);
                  
                  return (
                    <div
                      key={planetKey}
                      className="rounded-xl border p-4"
                      style={{
                        borderColor: planetColor + '40',
                        backgroundColor: planetColor + '10'
                      }}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-semibold" style={{ color: planetColor }}>
                          {planetNames[planetKey] || planetKey}
                        </span>
                        <span className="text-lg font-bold" style={{ color: planetColor }}>
                          {energyPercent}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${energyPercent}%`,
                            backgroundColor: planetColor,
                            boxShadow: `0 0 10px ${planetColor}60`
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
              {routeData?.total_energy !== undefined && (
                <div className="mt-4 pt-4 border-t border-white/10">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-purple-200">
                      Общая энергия дня
                    </span>
                    <span className="text-xl font-bold text-purple-300">
                      {Math.round(routeData.total_energy / 9)}%
                    </span>
                  </div>
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500 bg-gradient-to-r from-purple-400 to-purple-600"
                      style={{
                        width: `${Math.min(100, Math.round(routeData.total_energy / 9))}%`,
                        boxShadow: '0 0 15px rgba(168, 85, 247, 0.6)'
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* График энергий планет на день (почасовой) */}
        {route?.hourly_guide_24h && route.hourly_guide_24h.length > 0 && (
          <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
            <div className="flex items-center gap-3 mb-6">
              <TrendingUp className="h-6 w-6 text-cyan-500 drop-shadow-[0_0_10px_rgba(6,182,212,0.5)]" />
              <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
                График энергий планет на день
              </h2>
            </div>
            
            <div className={`p-6 rounded-2xl ${themeConfig.surface}`}>
              <div className="space-y-6">
                {/* Легенда планет */}
                <div className="flex flex-wrap gap-3 justify-center mb-4">
                  {Array.from(new Set(routeData.hourly_guide_24h.map(h => h.planet))).map(planet => {
                    const planetColor = getPlanetColor(planet);
                    return (
                      <div key={planet} className="flex items-center gap-2">
                        <div 
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: planetColor }}
                        />
                        <span className={`text-sm font-semibold ${themeConfig.text}`}>
                          {planet}
                        </span>
                      </div>
                    );
                  })}
                </div>

                {/* График */}
                <div className="relative" style={{ height: '400px' }}>
                  {/* Временная шкала (ось X) */}
                  <div className="absolute bottom-0 left-0 right-0 flex justify-between border-t-2 pt-2" style={{
                    borderColor: themeConfig.isDark ? '#ffffff20' : '#00000020'
                  }}>
                    {[0, 3, 6, 9, 12, 15, 18, 21, 24].map(hour => (
                      <div key={hour} className={`text-xs ${themeConfig.mutedText}`}>
                        {hour}:00
                      </div>
                    ))}
                  </div>

                  {/* Блоки планет */}
                  <div className="absolute top-0 left-0 right-0 bottom-12 flex">
                    {routeData.hourly_guide_24h.map((hour, index) => {
                      const isActive = isCurrentHour(hour);
                      const planetColor = getPlanetColor(hour.planet);
                      const width = `${100 / routeData.hourly_guide_24h.length}%`;
                      
                      return (
                        <div
                          key={index}
                          className={`relative transition-all duration-300 cursor-pointer group ${
                            isActive ? 'z-10' : 'z-0'
                          }`}
                          style={{ 
                            width,
                            height: '100%'
                          }}
                          onClick={() => {
                            setSelectedHour(hour);
                            setIsHourDialogOpen(true);
                          }}
                        >
                          {/* Блок планеты */}
                          <div 
                            className={`h-full flex flex-col items-center justify-center transition-all duration-300 ${
                              isActive ? 'scale-110 shadow-2xl' : 'group-hover:scale-105'
                            }`}
                            style={{
                              backgroundColor: isActive 
                                ? (themeConfig.isDark ? planetColor + '60' : planetColor + '40')
                                : (themeConfig.isDark ? planetColor + '30' : planetColor + '20'),
                              borderLeft: index === 0 ? 'none' : `1px solid ${themeConfig.isDark ? '#ffffff10' : '#00000010'}`,
                              boxShadow: isActive ? `0 0 30px ${planetColor}80, inset 0 0 30px ${planetColor}40` : undefined
                            }}
                          >
                            {/* Текущее время маркер */}
                            {isActive && (
                              <div 
                                className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-xs font-bold text-white animate-pulse whitespace-nowrap"
                                style={{
                                  backgroundColor: planetColor,
                                  boxShadow: `0 0 20px ${planetColor}80`
                                }}
                              >
                                ⏰ СЕЙЧАС
                              </div>
                            )}

                            {/* Иконка планеты */}
                            <div 
                              className={`rounded-full flex items-center justify-center font-bold text-white transition-all ${
                                isActive ? 'w-16 h-16 text-xl' : 'w-12 h-12 text-sm group-hover:w-14 group-hover:h-14'
                              }`}
                              style={{
                                backgroundColor: planetColor,
                                boxShadow: `0 0 20px ${planetColor}80`
                              }}
                            >
                              {hour.planet_sanskrit?.slice(0, 2) || hour.planet.slice(0, 2)}
                            </div>

                            {/* Время (показывается при наведении или если активно) */}
                            {(isActive || index % 3 === 0) && (
                              <div className={`mt-2 text-xs font-bold ${themeConfig.text} text-center`}>
                                {typeof hour.start === 'string' ? hour.start : hour.start_time?.slice(11, 16) || ''}
                              </div>
                            )}
                          </div>

                          {/* Tooltip при наведении */}
                          <div 
                            className={`absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 rounded-lg text-xs font-semibold text-white whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none ${themeConfig.surface}`}
                            style={{
                              backgroundColor: planetColor,
                              boxShadow: `0 4px 12px ${planetColor}60`
                            }}
                          >
                            {hour.planet}
                            <br />
                            {typeof hour.start === 'string' ? hour.start : hour.start_time?.slice(11, 16) || ''} - {typeof hour.end === 'string' ? hour.end : hour.end_time?.slice(11, 16) || ''}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Подсказка */}
                <div className={`text-center text-sm ${themeConfig.mutedText} mt-4`}>
                  💡 Нажмите на блок планеты для получения детальных советов
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Планетарные часы дня с советами */}
        {route?.hourly_guide_24h && route.hourly_guide_24h.length > 0 && (
          <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
            <div className="flex items-center gap-3 mb-6">
              <Clock className="h-6 w-6 text-indigo-500 drop-shadow-[0_0_10px_rgba(99,102,241,0.5)]" />
              <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
                Планетарные часы дня
              </h2>
            </div>
            <p className={`text-sm ${themeConfig.mutedText} mb-6`}>
              Показано {routeData.hourly_guide_24h.length} планетарных часов. Нажмите на час для получения персональных советов.
            </p>
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {routeData.hourly_guide_24h?.map((hour, index) => {
              const isActive = isCurrentHour(hour);
              const planetColor = getPlanetColor(hour.planet);
              return (
                <div
                  key={index}
                  onClick={() => {
                    setSelectedHour(hour);
                    setIsHourDialogOpen(true);
                  }}
                  className={`rounded-2xl border p-5 transition-all duration-500 hover:-translate-y-1 relative cursor-pointer ${
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
                        color: isActive ? '#ffffff' : (themeConfig.isDark ? getBrightColorForDark(planetColor) : planetColor),
                        textShadow: isActive 
                          ? `0 0 10px ${planetColor}, 0 0 20px ${planetColor}80` 
                          : (themeConfig.isDark ? `0 0 8px ${getBrightColorForDark(planetColor)}60, 0 0 4px rgba(255,255,255,0.4)` : undefined)
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
                      Час {index + 1}
                    </span>
                  </div>
                  <div className={`mt-3 text-sm ${isActive ? 'font-bold text-white text-base' : themeConfig.mutedText}`}
                    style={{
                      textShadow: isActive ? `0 0 10px ${planetColor}80` : undefined
                    }}
                  >
                    {(typeof hour.start === 'string' ? hour.start : hour.start_time?.slice(11, 16)) || 'N/A'} —{' '}
                    {(typeof hour.end === 'string' ? hour.end : hour.end_time?.slice(11, 16)) || 'N/A'}
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
                      <Clock className="h-4 w-4" />
                      Сейчас активно
                    </div>
                  )}
                  {hour.is_favorable && !isActive && (
                    <div className="mt-3 inline-flex items-center gap-2 rounded-full bg-emerald-400/20 px-3 py-1 text-xs font-semibold text-emerald-600">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Благоприятно
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          </div>
        )}
              </>
            )}
          </TabsContent>

          {/* Контент для недели */}
          <TabsContent value="week" className="mt-6">
            {weeklyLoading ? (
              <div className={`flex items-center justify-center py-12 ${themeConfig.text}`}>
                <Loader2 className="h-8 w-8 animate-spin text-blue-500 mr-3" />
                <span>Загрузка недельного маршрута...</span>
              </div>
            ) : weeklyData ? (
              <div className="space-y-6">
                {/* Обзор недели */}
                <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                  <div className="flex items-center gap-3 mb-6">
                    <TrendingUp className="h-6 w-6 text-blue-500 drop-shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
                    <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
                      Обзор недели
                    </h2>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                    {/* Энергетика недели */}
                    <div className={`p-6 rounded-2xl border ${themeConfig.surface}`}>
                      <div className="text-center">
                        <div className="text-4xl font-bold mb-2" style={{
                          color: weeklyData.weekly_summary.week_energy === 'Высокая' ? '#10b981' :
                                 weeklyData.weekly_summary.week_energy === 'Средняя' ? '#3b82f6' : '#ef4444'
                        }}>
                          {weeklyData.weekly_summary.average_rating}/5
                        </div>
                        <div className={`text-sm ${themeConfig.mutedText}`}>
                          {weeklyData.weekly_summary.week_energy} энергия
                        </div>
                      </div>
                    </div>

                    {/* Благоприятные дни */}
                    <div className={`p-6 rounded-2xl border ${themeConfig.surface}`}>
                      <div className="text-center">
                        <div className="text-4xl font-bold text-emerald-500 mb-2">
                          {weeklyData.daily_schedule?.filter(d => d.day_type === 'favorable' || d.day_type === 'highly_favorable').length || weeklyData.weekly_summary?.favorable_days_count || 0}
                        </div>
                        <div className={`text-sm ${themeConfig.mutedText}`}>
                          Благоприятных дней
                        </div>
                      </div>
                    </div>

                    {/* Сложные дни */}
                    <div className={`p-6 rounded-2xl border ${themeConfig.surface}`}>
                      <div className="text-center">
                        <div className="text-4xl font-bold text-red-500 mb-2">
                          {weeklyData.daily_schedule?.filter(d => d.day_type === 'challenging').length || weeklyData.weekly_summary?.challenging_days_count || 0}
                        </div>
                        <div className={`text-sm ${themeConfig.mutedText}`}>
                          Сложных дней
                        </div>
                      </div>
                    </div>
                  </div>

                  <p className={`text-center text-lg ${themeConfig.mutedText}`}>
                    {weeklyData.weekly_summary.week_description}
                  </p>
                </div>

                {/* График планетарных энергий на неделю */}
                {weeklyData.daily_schedule && weeklyData.daily_schedule.some(d => d.planetary_energies) && (
                  <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                    <div className="flex items-center gap-3 mb-6">
                      <Activity className="h-6 w-6 text-cyan-500 drop-shadow-[0_0_10px_rgba(6,182,212,0.5)]" />
                      <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
                        Динамика энергии планет на неделю
                      </h2>
                    </div>
                    <div className="h-96">
                      <Line
                        data={{
                          labels: weeklyData.daily_schedule.map(d => {
                            const date = new Date(d.date);
                            return `${date.getDate()}.${date.getMonth() + 1}`;
                          }),
                          datasets: Object.keys(weeklyData.daily_schedule[0]?.planetary_energies || {}).map(planetKey => {
                            const planetNames = {
                              surya: 'Сурья',
                              chandra: 'Чандра',
                              mangal: 'Мангал',
                              budha: 'Будха',
                              guru: 'Гуру',
                              shukra: 'Шукра',
                              shani: 'Шани',
                              rahu: 'Раху',
                              ketu: 'Кету'
                            };
                            const planetColor = getPlanetColor(planetKey.charAt(0).toUpperCase() + planetKey.slice(1));
                            return {
                              label: planetNames[planetKey] || planetKey,
                              data: weeklyData.daily_schedule.map(d => d.planetary_energies?.[planetKey] || 0),
                              borderColor: planetColor,
                              backgroundColor: planetColor + '20',
                              fill: false,
                              tension: 0.4,
                              pointRadius: 4,
                              pointHoverRadius: 6
                            };
                          })
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: {
                              display: true,
                              position: 'top'
                            },
                            tooltip: {
                              mode: 'index',
                              intersect: false
                            }
                          },
                          scales: {
                            y: {
                              beginAtZero: true,
                              max: 100,
                              ticks: {
                                stepSize: 20
                              }
                            }
                          }
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* Календарь недели - 7 дней */}
                <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                  <div className="flex items-center gap-3 mb-6">
                    <CalendarDays className="h-6 w-6 text-purple-500 drop-shadow-[0_0_10px_rgba(168,85,247,0.5)]" />
                    <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
                      Календарь недели
                    </h2>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-7 gap-4">
                    {weeklyData.daily_schedule && weeklyData.daily_schedule.length > 0 ? (
                      weeklyData.daily_schedule.map((day, index) => {
                        const dayType = day.day_type || 'neutral';
                        const isFavorable = dayType === 'favorable' || dayType === 'highly_favorable';
                        const isChallenging = dayType === 'challenging';
                        const planetColor = getPlanetColor(day.ruling_planet);
                        const isToday = day.date === new Date().toISOString().split('T')[0];
                        
                        return (
                          <div
                            key={index}
                            className={`p-4 rounded-2xl border cursor-pointer transition-all duration-300 hover:scale-105 ${
                              isToday ? 'ring-2 ring-purple-500' : ''
                            }`}
                            style={{
                              borderColor: day.day_type === 'highly_favorable' ? '#10b98140' :
                                         day.day_type === 'favorable' ? '#3b82f640' :
                                         day.day_type === 'challenging' ? '#ef444440' : '#6b728040',
                              backgroundColor: themeConfig.isDark
                                ? (day.day_type === 'highly_favorable' ? '#10b98110' :
                                   day.day_type === 'favorable' ? '#3b82f610' :
                                   day.day_type === 'challenging' ? '#ef444410' : '#6b728010')
                                : (day.day_type === 'highly_favorable' ? '#10b98108' :
                                   day.day_type === 'favorable' ? '#3b82f608' :
                                   day.day_type === 'challenging' ? '#ef444408' : '#6b728008')
                            }}
                            onClick={() => {
                              setSelectedDay(day);
                              setIsDayDialogOpen(true);
                            }}
                          >
                            {/* День недели */}
                            <div className={`text-xs font-semibold mb-2 ${themeConfig.mutedText}`}>
                              {day.weekday_name}
                            </div>

                            {/* Дата */}
                            <div className={`text-lg font-bold mb-2 ${themeConfig.text}`}>
                              {new Date(day.date).getDate()}
                            </div>

                            {/* Планета */}
                            <div
                              className="w-12 h-12 mx-auto rounded-full flex items-center justify-center font-bold text-white text-sm mb-2"
                              style={{
                                backgroundColor: planetColor,
                                boxShadow: `0 0 15px ${planetColor}60`
                              }}
                            >
                              {day.planet_sanskrit?.slice(0, 2) || day.ruling_planet.slice(0, 2)}
                            </div>

                            {/* Оценка и тип дня */}
                            <div className="text-center">
                              {(day.compatibility_score !== undefined && day.compatibility_score !== null) ? (
                                <div className="text-xl font-bold mb-1" style={{
                                  color: day.day_type === 'highly_favorable' ? '#10b981' :
                                         day.day_type === 'favorable' ? '#3b82f6' :
                                         day.day_type === 'challenging' ? '#ef4444' : '#6b7280'
                                }}>
                                  {Math.round(day.compatibility_score)} балл
                                </div>
                              ) : (day.day_score !== undefined && day.day_score !== null) ? (
                                <div className="text-xl font-bold mb-1" style={{
                                  color: day.day_type === 'highly_favorable' ? '#10b981' :
                                         day.day_type === 'favorable' ? '#3b82f6' :
                                         day.day_type === 'challenging' ? '#ef4444' : '#6b7280'
                                }}>
                                  {Math.round(day.day_score)} балл
                                </div>
                              ) : null}
                              {day.avg_energy_per_planet !== undefined && day.avg_energy_per_planet !== null && (
                                <div className="text-sm font-semibold mb-1" style={{
                                  color: day.day_type === 'highly_favorable' ? '#10b981' :
                                         day.day_type === 'favorable' ? '#3b82f6' :
                                         day.day_type === 'challenging' ? '#ef4444' : '#6b7280'
                                }}>
                                  {Math.round(day.avg_energy_per_planet)}%
                                </div>
                              )}
                              <div className={`text-xs font-semibold mb-1 ${
                                day.day_type === 'highly_favorable' ? 'text-green-500' :
                                day.day_type === 'favorable' ? 'text-blue-500' :
                                day.day_type === 'challenging' ? 'text-red-500' : 'text-gray-500'
                              }`}>
                                {day.day_type_ru || 'Нейтральный'}
                              </div>
                            </div>

                            {/* Индикатор */}
                            {isToday && (
                              <div className="mt-2 text-center">
                                <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/40 text-xs">
                                  Сегодня
                                </Badge>
                              </div>
                            )}
                          </div>
                        );
                      })
                    ) : (
                      <div className="col-span-7 text-center py-8 text-gray-500">
                        Нет данных для отображения. Загрузите недельные данные.
                      </div>
                    )}
                  </div>
                </div>

                {/* График энергий недели */}
                <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                  <div className="flex items-center gap-3 mb-6">
                    <Activity className="h-6 w-6 text-cyan-500 drop-shadow-[0_0_10px_rgba(6,182,212,0.5)]" />
                    <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
                      График энергий недели
                    </h2>
                  </div>

                  <div className={`p-6 rounded-2xl ${themeConfig.surface}`}>
                    <div className="relative" style={{ height: '300px' }}>
                      {/* Ось Y - баллы */}
                      <div className="absolute left-0 top-0 bottom-0 w-12 flex flex-col justify-between text-xs" style={{
                        color: themeConfig.mutedText
                      }}>
                        <div>100</div>
                        <div>75</div>
                        <div>50</div>
                        <div>25</div>
                        <div>0</div>
                      </div>

                      {/* График */}
                      <div className="absolute left-14 right-0 top-0 bottom-12">
                        <svg width="100%" height="100%" viewBox="0 0 700 280" preserveAspectRatio="none">
                          {/* Сетка */}
                          <line x1="0" y1="0" x2="700" y2="0" stroke={themeConfig.isDark ? '#ffffff20' : '#00000020'} strokeWidth="1" />
                          <line x1="0" y1="70" x2="700" y2="70" stroke={themeConfig.isDark ? '#ffffff10' : '#00000010'} strokeWidth="1" />
                          <line x1="0" y1="140" x2="700" y2="140" stroke={themeConfig.isDark ? '#ffffff20' : '#00000020'} strokeWidth="1" />
                          <line x1="0" y1="210" x2="700" y2="210" stroke={themeConfig.isDark ? '#ffffff10' : '#00000010'} strokeWidth="1" />
                          <line x1="0" y1="280" x2="700" y2="280" stroke={themeConfig.isDark ? '#ffffff20' : '#00000020'} strokeWidth="1" />

                          {/* Линия графика */}
                          <polyline
                            fill="none"
                            stroke="#3b82f6"
                            strokeWidth="3"
                            points={weeklyData.daily_schedule.map((day, i) => {
                              const x = (i / 6) * 700;
                              const y = 280 - (day.compatibility_score / 100) * 280;
                              return `${x},${y}`;
                            }).join(' ')}
                          />

                          {/* Точки */}
                          {weeklyData.daily_schedule.map((day, i) => {
                            const x = (i / 6) * 700;
                            const y = 280 - (day.compatibility_score / 100) * 280;
                            const planetColor = getPlanetColor(day.ruling_planet);
                            
                            return (
                              <circle
                                key={i}
                                cx={x}
                                cy={y}
                                r="8"
                                fill={planetColor}
                                stroke="white"
                                strokeWidth="2"
                                style={{ cursor: 'pointer' }}
                                onClick={() => {
                                  setSelectedDay(day);
                                  setIsDayDialogOpen(true);
                                }}
                              />
                            );
                          })}
                        </svg>
                      </div>

                      {/* Ось X - дни недели */}
                      <div className="absolute left-14 right-0 bottom-0 flex justify-between text-xs" style={{
                        color: themeConfig.mutedText
                      }}>
                        {weeklyData.daily_schedule.map((day, i) => (
                          <div key={i} className="text-center">
                            {day.weekday_name.slice(0, 2)}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Ключевые рекомендации */}
                {weeklyData.weekly_summary.key_recommendations && weeklyData.weekly_summary.key_recommendations.length > 0 && (
                  <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                    <div className="flex items-center gap-3 mb-6">
                      <Target className="h-6 w-6 text-amber-500 drop-shadow-[0_0_10px_rgba(245,158,11,0.5)]" />
                      <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
                        Ключевые рекомендации
                      </h2>
                    </div>

                    <div className="space-y-4">
                      {weeklyData.weekly_summary.key_recommendations.map((rec, index) => (
                        <div
                          key={index}
                          className={`p-6 rounded-2xl border ${themeConfig.surface}`}
                          style={{
                            borderColor: rec.type === 'positive' ? '#10b98140' : '#ef444440',
                            backgroundColor: themeConfig.isDark
                              ? (rec.type === 'positive' ? '#10b98110' : '#ef444410')
                              : (rec.type === 'positive' ? '#10b98108' : '#ef444408')
                          }}
                        >
                          <h3 className={`font-bold text-lg mb-2 flex items-center gap-2 ${themeConfig.text}`}>
                            {rec.type === 'positive' ? (
                              <CheckCircle className="h-5 w-5 text-emerald-500" />
                            ) : (
                              <AlertTriangle className="h-5 w-5 text-amber-500" />
                            )}
                            {rec.title}
                          </h3>
                          <p className={`text-sm ${themeConfig.mutedText} mb-3`}>
                            {rec.advice}
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {rec.dates.map((date, i) => (
                              <Badge key={i} className={
                                rec.type === 'positive'
                                  ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
                                  : 'bg-amber-500/20 text-amber-400 border-amber-500/40'
                              }>
                                {new Date(date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                <div className="text-center py-12">
                  <CalendarDays className={`h-16 w-16 mx-auto mb-4 ${themeConfig.mutedText}`} />
                  <h3 className={`text-2xl font-bold mb-2 ${themeConfig.text}`}>
                    Планетарный маршрут на неделю
                  </h3>
                  <p className={`${themeConfig.mutedText} mb-6`}>
                    Нажмите кнопку для загрузки недельного маршрута
                  </p>
                    <Button 
                      onClick={loadWeeklyData}
                      disabled={weeklyLoading || !user?.city}
                      className="bg-blue-500 hover:bg-blue-600"
                    >
                      {weeklyLoading ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Загрузка...
                        </>
                      ) : (
                        <>
                          <CalendarDays className="h-4 w-4 mr-2" />
                          Загрузить ({costs.planetary_weekly} {costs.planetary_weekly === 1 ? 'балл' : 'балла'})
                        </>
                      )}
                    </Button>
                </div>
              </div>
            )}
          </TabsContent>

          {/* Контент для месяца */}
          <TabsContent value="month" className="mt-6">
            {(() => {
              console.log('🎨 РЕНДЕРИМ ВКЛАДКУ "МЕСЯЦ":', {
                monthlyLoading,
                hasMonthlyData: !!monthlyData,
                monthlyDataKeys: monthlyData ? Object.keys(monthlyData) : [],
                dailyScheduleLength: monthlyData?.daily_schedule?.length
              });
              return null;
            })()}
            {monthlyLoading ? (
              <div className={`flex items-center justify-center py-12 ${themeConfig.text}`}>
                <Loader2 className="h-8 w-8 animate-spin text-blue-500 mr-3" />
                <span>Загрузка месячного маршрута...</span>
                <div className="ml-4 text-xs text-gray-500">
                  (monthlyLoading: {String(monthlyLoading)})
                </div>
              </div>
            ) : monthlyData ? (
              <>
                {console.log('✅✅✅ РЕНДЕРИМ МЕСЯЧНЫЕ ДАННЫЕ:', {
                  hasData: !!monthlyData,
                  dailyScheduleLength: monthlyData.daily_schedule?.length,
                  hasMonthlySummary: !!monthlyData.monthly_summary,
                  hasWeeklyAnalysis: !!monthlyData.weekly_analysis,
                  hasLifeSpheres: !!monthlyData.life_spheres,
                  hasTrends: !!monthlyData.trends,
                  fullMonthlyData: monthlyData
                }) || null}
                
                {/* Селектор месяца */}
                <div className={`mb-6 rounded-2xl border p-6 ${themeConfig.glass}`}>
                  <div className="flex items-center justify-between flex-wrap gap-4">
                    <div className="flex items-center gap-3">
                      <CalendarRange className="h-5 w-5 text-blue-500" />
                      <h3 className={`text-lg font-semibold ${themeConfig.text}`}>
                        Выберите месяц для просмотра
                      </h3>
                      {user && (
                        <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/40">
                          Баланс: {user.credits_remaining ?? 0} баллов
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      <Input
                        type="month"
                        value={selectedMonthDate.substring(0, 7)} // Формат YYYY-MM для input type="month"
                        onChange={(e) => {
                          const newMonth = e.target.value + '-01'; // Добавляем день для полной даты
                          setSelectedMonthDate(newMonth);
                          console.log('📅 Выбран новый месяц:', newMonth);
                        }}
                        className={`w-48 ${themeConfig.surface} backdrop-blur-xl`}
                      />
                      <Button 
                        onClick={loadMonthlyData}
                        disabled={monthlyLoading || !user?.city}
                        className="bg-blue-500 hover:bg-blue-600"
                      >
                        {monthlyLoading ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Загрузка...
                          </>
                        ) : (
                          <>
                            <CalendarRange className="h-4 w-4 mr-2" />
                            Загрузить ({costs.planetary_monthly} {costs.planetary_monthly === 1 ? 'балл' : 'баллов'})
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                  <p className={`text-sm mt-2 ${themeConfig.mutedText}`}>
                    Текущий месяц: {new Date(selectedMonthDate).toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })}
                  </p>
                </div>

                <div className="space-y-6">
                {/* Обзор месяца */}
                <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                  <div className="flex items-center gap-3 mb-6">
                    <CalendarDays className="h-6 w-6 text-blue-500 drop-shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
                    <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
                      Планетарный обзор месяца
                    </h2>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div className={`text-center p-3 rounded-lg ${themeConfig.isDark ? 'bg-blue-500/20' : 'bg-blue-50'}`}>
                      <div className={`text-lg font-semibold ${themeConfig.isDark ? 'text-blue-300' : 'text-blue-700'}`}>
                        {monthlyData.total_days || 30}
                      </div>
                      <div className={`text-sm ${themeConfig.mutedText}`}>Дней в периоде</div>
                    </div>
                    <div className={`text-center p-3 rounded-lg ${themeConfig.isDark ? 'bg-green-500/20' : 'bg-green-50'}`}>
                      <div className={`text-lg font-semibold ${themeConfig.isDark ? 'text-green-300' : 'text-green-700'}`}>
                        {monthlyData.monthly_summary?.total_favorable_days || 0}
                      </div>
                      <div className={`text-sm ${themeConfig.mutedText}`}>Благоприятных дней</div>
                    </div>
                    <div className={`text-center p-3 rounded-lg ${themeConfig.isDark ? 'bg-red-500/20' : 'bg-red-50'}`}>
                      <div className={`text-lg font-semibold ${themeConfig.isDark ? 'text-red-300' : 'text-red-700'}`}>
                        {monthlyData.monthly_summary?.total_challenging_days || 0}
                      </div>
                      <div className={`text-sm ${themeConfig.mutedText}`}>Сложных дней</div>
                    </div>
                    <div className={`text-center p-3 rounded-lg ${themeConfig.isDark ? 'bg-purple-500/20' : 'bg-purple-50'}`}>
                      <div className={`text-lg font-semibold ${themeConfig.isDark ? 'text-purple-300' : 'text-purple-700'}`}>
                        {monthlyData.monthly_summary?.recommendations?.most_active_planet || 'Солнце'}
                      </div>
                      <div className={`text-sm ${themeConfig.mutedText}`}>Активная планета</div>
                    </div>
                  </div>
                </div>

                {/* Обзор месяца - Общая тематика и ключевые периоды */}
                <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                  <div className="flex items-center gap-3 mb-6">
                    <Target className="h-6 w-6 text-indigo-500 drop-shadow-[0_0_10px_rgba(99,102,241,0.5)]" />
                    <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
                      🌙 Обзор месяца
                    </h2>
                  </div>
                  <div className="space-y-4">
                    <div className={`p-4 rounded-lg border-2 ${themeConfig.isDark ? 'bg-blue-500/10 border-blue-400/30' : 'bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200'}`}>
                      <h3 className={`font-semibold text-lg mb-2 ${themeConfig.text}`}>Общая тематика месяца</h3>
                      <p className={themeConfig.mutedText}>
                        {monthlyData.weekly_analysis?.overall_theme || monthlyData.monthly_summary?.recommendations?.advice || 'Гармония и баланс'}
                      </p>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className={`p-4 rounded-lg ${themeConfig.isDark ? 'bg-green-500/10' : 'bg-green-50'}`}>
                        <h4 className={`font-semibold mb-2 ${themeConfig.isDark ? 'text-green-300' : 'text-green-800'}`}>Благоприятные недели</h4>
                        <div className="space-y-2">
                          {monthlyData.weekly_analysis?.favorable_weeks?.length > 0 ? (
                            monthlyData.weekly_analysis.favorable_weeks.map((week, idx) => (
                              <div key={idx} className={`text-sm ${themeConfig.mutedText}`}>
                                <span className="font-semibold">Неделя {week.week_number}:</span> {formatDateRu(week.start_date)} - {formatDateRu(week.end_date)}
                                <span className={`ml-2 ${themeConfig.isDark ? 'text-green-400' : 'text-green-600'}`}>({week.avg_energy}% энергии)</span>
                              </div>
                            ))
                          ) : (
                            <div className={`text-sm ${themeConfig.mutedText}`}>Нет благоприятных недель</div>
                          )}
                        </div>
                      </div>
                      
                      <div className={`p-4 rounded-lg ${themeConfig.isDark ? 'bg-red-500/10' : 'bg-red-50'}`}>
                        <h4 className={`font-semibold mb-2 ${themeConfig.isDark ? 'text-red-300' : 'text-red-800'}`}>Критические точки</h4>
                        <div className="space-y-3">
                          {monthlyData.weekly_analysis?.challenging_weeks?.length > 0 ? (
                            monthlyData.weekly_analysis.challenging_weeks.map((week, idx) => (
                              <div key={idx} className={`p-3 rounded-lg border-2 ${themeConfig.isDark ? 'bg-red-500/20 border-red-400/50' : 'bg-red-100 border-red-400'}`}>
                                <div className={`text-sm font-semibold mb-2 ${themeConfig.isDark ? 'text-red-300' : 'text-red-800'}`}>
                                  Неделя {week.week_number}: {formatDateRu(week.start_date)} - {formatDateRu(week.end_date)}
                                </div>
                                <div className={`text-xs mb-2 ${themeConfig.isDark ? 'text-red-400' : 'text-red-600'}`}>
                                  Средняя энергия: {week.avg_energy}%
                                </div>
                                {/* Показываем самые неблагоприятные дни недели */}
                                {monthlyData.daily_schedule && (
                                  <div className="mt-2 space-y-1">
                                    <div className={`text-xs font-semibold ${themeConfig.isDark ? 'text-red-300' : 'text-red-700'}`}>
                                      Самые неблагоприятные дни:
                                    </div>
                                    {monthlyData.daily_schedule
                                      .filter(day => {
                                        const dayDate = new Date(day.date);
                                        const weekStart = new Date(week.start_date);
                                        const weekEnd = new Date(week.end_date);
                                        return dayDate >= weekStart && dayDate <= weekEnd && day.day_type === 'challenging';
                                      })
                                      .sort((a, b) => (a.avg_energy_per_planet || 0) - (b.avg_energy_per_planet || 0))
                                      .slice(0, 3)
                                      .map((day, dayIdx) => (
                                        <div key={dayIdx} className={`text-xs ${themeConfig.isDark ? 'text-red-400' : 'text-red-700'}`}>
                                          • {formatDateRu(day.date)} - {day.avg_energy_per_planet?.toFixed(1) || 0}% энергии
                                        </div>
                                      ))}
                                  </div>
                                )}
                              </div>
                            ))
                          ) : (
                            <div className={`text-sm ${themeConfig.mutedText}`}>Нет критических недель</div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Календарь месяца с планетарными влияниями */}
                <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                  <div className="flex items-center gap-3 mb-6">
                    <CalendarDays className="h-6 w-6 text-purple-500 drop-shadow-[0_0_10px_rgba(168,85,247,0.5)]" />
                    <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
                      📅 Календарь планетарных влияний
                    </h2>
                  </div>
                  
                  <div className="grid grid-cols-7 gap-2 mb-4">
                    {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map(day => (
                      <div key={day} className={`text-center text-sm font-semibold p-2 ${themeConfig.mutedText}`}>
                        {day}
                      </div>
                    ))}
                  </div>
                  
                  <div className="grid grid-cols-7 gap-2">
                    {monthlyData.daily_schedule && monthlyData.daily_schedule.length > 0 ? (
                      monthlyData.daily_schedule.map((day, index) => {
                      const dayType = day.day_type || 'neutral';
                      const avgEnergy = (day.avg_energy_per_planet !== null && day.avg_energy_per_planet !== undefined) ? day.avg_energy_per_planet : 0;
                      // Используем compatibility_score если есть, иначе day_score
                      const dayScore = (day.compatibility_score !== null && day.compatibility_score !== undefined) 
                        ? day.compatibility_score 
                        : ((day.day_score !== null && day.day_score !== undefined) ? day.day_score : null);
                      const isFavorable = dayType === 'favorable' || dayType === 'highly_favorable';
                      const isChallenging = dayType === 'challenging';
                      const planetColor = getPlanetColor(day.ruling_planet);
                      const isToday = day.date === new Date().toISOString().split('T')[0];
                      
                      return (
                        <div 
                          key={index} 
                          className={`p-2 text-center border-2 rounded-lg hover:scale-105 min-h-[80px] flex flex-col justify-between cursor-pointer transition-all ${
                            isFavorable 
                              ? (themeConfig.isDark ? 'bg-green-500/20 border-green-400/50' : 'bg-green-50 border-green-400') 
                              : isChallenging 
                                ? (themeConfig.isDark ? 'bg-red-500/30 border-red-500/70' : 'bg-red-100 border-red-500')
                                : (themeConfig.isDark ? 'bg-gray-500/10 border-gray-400/30' : 'bg-gray-50 border-gray-300')
                          } ${isToday ? 'ring-2 ring-purple-500' : ''}`}
                          title={`${day.date} - ${day.day_type_ru || 'Нейтральный'}${dayScore !== null && dayScore !== undefined ? ` (${Math.round(dayScore)} баллов)` : ''}${avgEnergy ? ` - ${avgEnergy.toFixed(1)}% энергии` : ''}`}
                          onClick={() => {
                            setSelectedDay(day);
                            setIsDayDialogOpen(true);
                          }}
                        >
                          <div className={`text-sm font-semibold ${
                            isChallenging ? 'text-red-700' : 
                            isFavorable ? 'text-green-700' : 
                            themeConfig.text
                          }`}>
                            {new Date(day.date).getDate()}
                          </div>
                          <div 
                            className="text-[10px] font-semibold leading-tight break-words"
                            style={{
                              color: isChallenging 
                                ? (themeConfig.isDark ? '#ef4444' : '#dc2626')
                                : isFavorable
                                  ? (themeConfig.isDark ? '#10b981' : '#059669')
                                  : planetColor
                            }}
                          >
                            {day.ruling_planet?.split('(')[0]?.trim() || ''}
                          </div>
                          <div className="flex flex-col items-center gap-1 mt-1">
                            {dayScore !== null && dayScore !== undefined && (
                              <div 
                                className="text-lg font-bold mb-0.5"
                                style={{ 
                                  color: isFavorable 
                                    ? (themeConfig.isDark ? '#10b981' : '#059669') 
                                    : isChallenging 
                                      ? (themeConfig.isDark ? '#ef4444' : '#dc2626') 
                                      : themeConfig.isDark ? '#9ca3af' : '#6b7280'
                                }}
                              >
                                {Math.round(dayScore)}
                              </div>
                            )}
                            {avgEnergy && avgEnergy > 0 && (
                              <div className={`text-[10px] font-semibold ${
                                isFavorable 
                                  ? (themeConfig.isDark ? 'text-green-400' : 'text-green-600') 
                                  : isChallenging 
                                    ? (themeConfig.isDark ? 'text-red-400' : 'text-red-600') 
                                    : themeConfig.mutedText
                              }`}>
                                {avgEnergy.toFixed(0)}%
                              </div>
                            )}
                            {isToday && (
                              <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/40 text-[8px] px-1 py-0">
                                Сегодня
                              </Badge>
                            )}
                          </div>
                        </div>
                      );
                    })
                    ) : (
                      <div className="col-span-7 text-center py-8 text-gray-500">
                        Нет данных для отображения
                      </div>
                    )}
                  </div>
                </div>

                {/* Анализ по неделям */}
                {monthlyData.weekly_analysis?.weeks && monthlyData.weekly_analysis.weeks.length > 0 && (
                  <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                    <div className="flex items-center gap-3 mb-6">
                      <CalendarDays className="h-6 w-6 text-cyan-500 drop-shadow-[0_0_10px_rgba(6,182,212,0.5)]" />
                      <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
                        📆 Анализ по неделям
                      </h2>
                    </div>
                    <div className="space-y-6">
                      {monthlyData.weekly_analysis.weeks.map((week, idx) => (
                        <div key={idx} className={`p-4 border-2 rounded-lg ${themeConfig.isDark ? 'bg-gray-800/50 border-gray-700' : 'bg-gradient-to-r from-gray-50 to-blue-50 border-blue-200'}`}>
                          <div className="flex justify-between items-start mb-3">
                            <div>
                              <h3 className={`font-bold text-lg ${themeConfig.text}`}>Неделя {week.week_number}</h3>
                              <p className={`text-sm ${themeConfig.mutedText}`}>{formatDateRu(week.start_date)} - {formatDateRu(week.end_date)}</p>
                              <p className={`text-sm font-semibold mt-1 ${themeConfig.isDark ? 'text-blue-400' : 'text-blue-700'}`}>{week.theme}</p>
                            </div>
                            <div className="text-right">
                              <div className={`text-lg font-bold ${themeConfig.isDark ? 'text-purple-300' : 'text-purple-700'}`}>{week.avg_energy}%</div>
                              <div className={`text-xs ${themeConfig.mutedText}`}>Средняя энергия</div>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                            <div className={`text-sm ${themeConfig.mutedText}`}>
                              <span className="font-semibold">Доминирующая планета:</span> {week.dominant_planet}
                            </div>
                            <div className={`text-sm ${themeConfig.mutedText}`}>
                              <span className="font-semibold">Благоприятных дней:</span> {week.favorable_days_count}
                            </div>
                            <div className={`text-sm ${themeConfig.mutedText}`}>
                              <span className="font-semibold">Сложных дней:</span> {week.challenging_days_count}
                            </div>
                          </div>
                          
                          {week.recommendations && week.recommendations.length > 0 && (
                            <div>
                              <h4 className={`font-semibold text-sm mb-2 ${themeConfig.text}`}>Рекомендации:</h4>
                              <ul className={`list-disc list-inside text-sm space-y-1 ${themeConfig.mutedText}`}>
                                {week.recommendations.map((rec, rIdx) => (
                                  <li key={rIdx}>{rec}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Сферы жизни */}
                <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                  <div className="flex items-center gap-3 mb-6">
                    <Target className="h-6 w-6 text-amber-500 drop-shadow-[0_0_10px_rgba(245,158,11,0.5)]" />
                    <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
                      💼 Сферы жизни
                    </h2>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Карьера и финансы */}
                    <div className={`p-4 border-2 rounded-lg ${themeConfig.isDark ? 'bg-yellow-500/10 border-yellow-500/30' : 'bg-gradient-to-br from-yellow-50 to-orange-50 border-yellow-200'}`}>
                      <h3 className={`font-bold text-lg mb-3 flex items-center ${themeConfig.text}`}>
                        💼 Карьера и финансы
                        <span className={`ml-auto text-sm px-2 py-1 rounded ${
                          monthlyData.life_spheres?.career_finance?.rating === 'Отлично' ? 'bg-green-200 text-green-800' :
                          monthlyData.life_spheres?.career_finance?.rating === 'Хорошо' ? 'bg-blue-200 text-blue-800' :
                          monthlyData.life_spheres?.career_finance?.rating === 'Удовлетворительно' ? 'bg-yellow-200 text-yellow-800' :
                          'bg-red-200 text-red-800'
                        }`}>
                          {monthlyData.life_spheres?.career_finance?.rating || 'Нет данных'}
                        </span>
                      </h3>
                      <div className={`text-sm mb-3 ${themeConfig.mutedText}`}>
                        <span className="font-semibold">Средняя энергия:</span> {monthlyData.life_spheres?.career_finance?.avg_energy || 0}%
                      </div>
                      {monthlyData.life_spheres?.career_finance?.recommendations && monthlyData.life_spheres.career_finance.recommendations.length > 0 && (
                        <ul className={`list-disc list-inside text-sm space-y-1 ${themeConfig.mutedText}`}>
                          {monthlyData.life_spheres.career_finance.recommendations.map((rec, idx) => (
                            <li key={idx}>{rec}</li>
                          ))}
                        </ul>
                      )}
                    </div>

                    {/* Отношения и семья */}
                    <div className={`p-4 border-2 rounded-lg ${themeConfig.isDark ? 'bg-pink-500/10 border-pink-500/30' : 'bg-gradient-to-br from-pink-50 to-rose-50 border-pink-200'}`}>
                      <h3 className={`font-bold text-lg mb-3 flex items-center ${themeConfig.text}`}>
                        ❤️ Отношения и семья
                        <span className={`ml-auto text-sm px-2 py-1 rounded ${
                          monthlyData.life_spheres?.relationships_family?.rating === 'Отлично' ? 'bg-green-200 text-green-800' :
                          monthlyData.life_spheres?.relationships_family?.rating === 'Хорошо' ? 'bg-blue-200 text-blue-800' :
                          monthlyData.life_spheres?.relationships_family?.rating === 'Удовлетворительно' ? 'bg-yellow-200 text-yellow-800' :
                          'bg-red-200 text-red-800'
                        }`}>
                          {monthlyData.life_spheres?.relationships_family?.rating || 'Нет данных'}
                        </span>
                      </h3>
                      <div className={`text-sm mb-3 ${themeConfig.mutedText}`}>
                        <span className="font-semibold">Средняя энергия:</span> {monthlyData.life_spheres?.relationships_family?.avg_energy || 0}%
                      </div>
                      {monthlyData.life_spheres?.relationships_family?.recommendations && monthlyData.life_spheres.relationships_family.recommendations.length > 0 && (
                        <ul className={`list-disc list-inside text-sm space-y-1 ${themeConfig.mutedText}`}>
                          {monthlyData.life_spheres.relationships_family.recommendations.map((rec, idx) => (
                            <li key={idx}>{rec}</li>
                          ))}
                        </ul>
                      )}
                    </div>

                    {/* Здоровье и энергия */}
                    <div className={`p-4 border-2 rounded-lg ${themeConfig.isDark ? 'bg-green-500/10 border-green-500/30' : 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-200'}`}>
                      <h3 className={`font-bold text-lg mb-3 flex items-center ${themeConfig.text}`}>
                        💚 Здоровье и энергия
                        <span className={`ml-auto text-sm px-2 py-1 rounded ${
                          monthlyData.life_spheres?.health_energy?.rating === 'Отлично' ? 'bg-green-200 text-green-800' :
                          monthlyData.life_spheres?.health_energy?.rating === 'Хорошо' ? 'bg-blue-200 text-blue-800' :
                          monthlyData.life_spheres?.health_energy?.rating === 'Удовлетворительно' ? 'bg-yellow-200 text-yellow-800' :
                          'bg-red-200 text-red-800'
                        }`}>
                          {monthlyData.life_spheres?.health_energy?.rating || 'Нет данных'}
                        </span>
                      </h3>
                      <div className={`text-sm mb-3 ${themeConfig.mutedText}`}>
                        <span className="font-semibold">Средняя энергия:</span> {monthlyData.life_spheres?.health_energy?.avg_energy || 0}%
                      </div>
                      {monthlyData.life_spheres?.health_energy?.recommendations && monthlyData.life_spheres.health_energy.recommendations.length > 0 && (
                        <ul className={`list-disc list-inside text-sm space-y-1 ${themeConfig.mutedText}`}>
                          {monthlyData.life_spheres.health_energy.recommendations.map((rec, idx) => (
                            <li key={idx}>{rec}</li>
                          ))}
                        </ul>
                      )}
                    </div>

                    {/* Духовное развитие */}
                    <div className={`p-4 border-2 rounded-lg ${themeConfig.isDark ? 'bg-purple-500/10 border-purple-500/30' : 'bg-gradient-to-br from-purple-50 to-indigo-50 border-purple-200'}`}>
                      <h3 className={`font-bold text-lg mb-3 flex items-center ${themeConfig.text}`}>
                        🕉️ Духовное развитие
                        <span className={`ml-auto text-sm px-2 py-1 rounded ${
                          monthlyData.life_spheres?.spiritual_growth?.rating === 'Отлично' ? 'bg-green-200 text-green-800' :
                          monthlyData.life_spheres?.spiritual_growth?.rating === 'Хорошо' ? 'bg-blue-200 text-blue-800' :
                          monthlyData.life_spheres?.spiritual_growth?.rating === 'Удовлетворительно' ? 'bg-yellow-200 text-yellow-800' :
                          'bg-red-200 text-red-800'
                        }`}>
                          {monthlyData.life_spheres?.spiritual_growth?.rating || 'Нет данных'}
                        </span>
                      </h3>
                      <div className={`text-sm mb-3 ${themeConfig.mutedText}`}>
                        <span className="font-semibold">Средняя энергия:</span> {monthlyData.life_spheres?.spiritual_growth?.avg_energy || 0}%
                      </div>
                      {monthlyData.life_spheres?.spiritual_growth?.recommendations && monthlyData.life_spheres.spiritual_growth.recommendations.length > 0 && (
                        <ul className={`list-disc list-inside text-sm space-y-1 ${themeConfig.mutedText}`}>
                          {monthlyData.life_spheres.spiritual_growth.recommendations.map((rec, idx) => (
                            <li key={idx}>{rec}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                </div>

                {/* Тренды и прогнозы */}
                <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                  <div className="flex items-center gap-3 mb-6">
                    <TrendingUp className="h-6 w-6 text-emerald-500 drop-shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
                    <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
                      📈 Тренды и прогнозы
                    </h2>
                  </div>
                  <div className="space-y-6">
                    <div className={`p-4 rounded-lg border-2 ${themeConfig.isDark ? 'bg-blue-500/10 border-blue-400/30' : 'bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-200'}`}>
                      <h3 className={`font-bold text-lg mb-2 ${themeConfig.text}`}>Тренд энергии месяца</h3>
                      <p className={themeConfig.mutedText}>
                        {monthlyData.trends?.trend_description || 'Стабильный уровень энергии в течение месяца'}
                      </p>
                    </div>

                    {monthlyData.trends?.optimal_start_periods && monthlyData.trends.optimal_start_periods.length > 0 && (
                      <div>
                        <h3 className={`font-bold text-lg mb-3 ${themeConfig.isDark ? 'text-green-400' : 'text-green-700'}`}>Оптимальное время для начинаний</h3>
                        <div className="space-y-3">
                          {monthlyData.trends.optimal_start_periods.map((period, idx) => (
                            <div key={idx} className={`p-3 rounded-lg border-2 ${themeConfig.isDark ? 'bg-green-500/10 border-green-400/30' : 'bg-green-50 border-green-300'}`}>
                              <div className="flex justify-between items-center mb-2">
                                <span className={`font-semibold ${themeConfig.isDark ? 'text-green-300' : 'text-green-800'}`}>
                                  {formatDateRu(period.start_date)} - {formatDateRu(period.end_date)}
                                </span>
                                <span className={`text-sm ${themeConfig.isDark ? 'text-green-400' : 'text-green-600'}`}>
                                  {period.days_count} дней · {period.avg_energy}% энергии
                                </span>
                              </div>
                              <p className={`text-sm ${themeConfig.isDark ? 'text-green-300' : 'text-green-700'}`}>{period.description}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {monthlyData.trends?.completion_periods && monthlyData.trends.completion_periods.length > 0 && (
                      <div>
                        <h3 className={`font-bold text-lg mb-3 ${themeConfig.isDark ? 'text-blue-400' : 'text-blue-700'}`}>Периоды завершения проектов</h3>
                        <div className="space-y-3">
                          {monthlyData.trends.completion_periods.map((period, idx) => (
                            <div key={idx} className={`p-3 rounded-lg border-2 ${themeConfig.isDark ? 'bg-blue-500/10 border-blue-400/30' : 'bg-blue-50 border-blue-300'}`}>
                              <div className="flex justify-between items-center mb-2">
                                <span className={`font-semibold ${themeConfig.isDark ? 'text-blue-300' : 'text-blue-800'}`}>
                                  {formatDateRu(period.start_date)} - {formatDateRu(period.end_date)}
                                </span>
                                <span className={`text-sm ${themeConfig.isDark ? 'text-blue-400' : 'text-blue-600'}`}>
                                  {period.days_count} дней
                                </span>
                              </div>
                              <p className={`text-sm ${themeConfig.isDark ? 'text-blue-300' : 'text-blue-700'}`}>{period.description}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {monthlyData.trends?.planning_recommendations && monthlyData.trends.planning_recommendations.length > 0 && (
                      <div>
                        <h3 className={`font-bold text-lg mb-3 ${themeConfig.text}`}>Рекомендации по планированию</h3>
                        <ul className={`list-disc list-inside space-y-2 ${themeConfig.mutedText}`}>
                          {monthlyData.trends.planning_recommendations.map((rec, idx) => (
                            <li key={idx}>{rec}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>

                {/* Лунные фазы */}
                {monthlyData.lunar_phases && monthlyData.lunar_phases.length > 0 && (
                  <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                    <div className="flex items-center gap-3 mb-6">
                      <Star className="h-6 w-6 text-indigo-500 drop-shadow-[0_0_10px_rgba(99,102,241,0.5)]" />
                      <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
                        🌙 Лунные фазы и влияния
                      </h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      {monthlyData.lunar_phases.map((phase, idx) => (
                        <div key={idx} className={`p-4 rounded-lg border-2 ${themeConfig.isDark ? 'bg-indigo-500/10 border-indigo-400/30' : 'bg-gradient-to-br from-indigo-50 to-purple-50 border-indigo-200'}`}>
                          <div className="text-3xl mb-2">{phase.phase_emoji}</div>
                          <div className={`font-semibold mb-1 ${themeConfig.isDark ? 'text-indigo-300' : 'text-indigo-800'}`}>{phase.phase}</div>
                          <div className={`text-sm mb-2 ${themeConfig.mutedText}`}>{formatDateRu(phase.date)}</div>
                          <div className={`text-xs ${themeConfig.isDark ? 'text-indigo-300' : 'text-indigo-700'}`}>{phase.influence}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Планетарные транзиты */}
                {monthlyData.planetary_transits && monthlyData.planetary_transits.length > 0 && (
                  <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                    <div className="flex items-center gap-3 mb-6">
                      <Zap className="h-6 w-6 text-yellow-500 drop-shadow-[0_0_10px_rgba(234,179,8,0.5)]" />
                      <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
                        ⭐ Планетарные транзиты
                      </h2>
                    </div>
                    <div className="space-y-3">
                      {monthlyData.planetary_transits.map((transit, idx) => {
                        const planetColor = getPlanetColor(transit.planet);
                        const isPeak = transit.type === 'peak';
                        return (
                          <div 
                            key={idx} 
                            className={`p-3 rounded-lg border-2`}
                            style={{
                              backgroundColor: themeConfig.isDark 
                                ? `${planetColor}20` 
                                : `${planetColor}15`,
                              borderColor: themeConfig.isDark 
                                ? `${planetColor}50` 
                                : `${planetColor}40`
                            }}
                          >
                            <div className="flex justify-between items-center mb-1">
                              <span 
                                className="font-semibold"
                                style={{ color: planetColor }}
                              >
                                {formatDateRu(transit.date)} · {transit.planet}
                              </span>
                              <span 
                                className="text-sm font-semibold"
                                style={{ color: planetColor }}
                              >
                                {transit.energy}% энергии
                              </span>
                            </div>
                            <p 
                              className="text-sm"
                              style={{ 
                                color: themeConfig.isDark 
                                  ? `${planetColor}CC` 
                                  : `${planetColor}DD`
                              }}
                            >
                              {transit.description}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
                </div>
              </>
            ) : (
              <>
                {console.log('⚠️⚠️⚠️ НЕТ МЕСЯЧНЫХ ДАННЫХ, показываем заглушку:', {
                  monthlyLoading,
                  hasMonthlyData: !!monthlyData,
                  activeTab
                }) || null}
                <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                  <div className="text-center py-12">
                    <CalendarRange className={`h-16 w-16 mx-auto mb-4 ${themeConfig.mutedText}`} />
                    <h3 className={`text-2xl font-bold mb-2 ${themeConfig.text}`}>
                      Планетарный маршрут на месяц
                    </h3>
                    <p className={`${themeConfig.mutedText} mb-6`}>
                      Нажмите кнопку для загрузки месячного маршрута
                    </p>
                    <Button onClick={loadMonthlyData} disabled={!user?.city} className="bg-blue-500 hover:bg-blue-600">
                      Загрузить месячный маршрут ({costs.planetary_monthly} {costs.planetary_monthly === 1 ? 'балл' : 'баллов'})
                    </Button>
                  </div>
                </div>
              </>
            )}
          </TabsContent>

          {/* Контент для квартала */}
          <TabsContent value="quarter" className="mt-6 space-y-6">
            {/* Селектор квартала */}
            <div className={`mb-6 rounded-2xl border p-6 ${themeConfig.glass}`}>
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div className="flex items-center gap-3">
                  <CalendarRange className="h-5 w-5 text-teal-500" />
                  <h3 className={`text-lg font-semibold ${themeConfig.text}`}>
                    Выберите начало квартала
                  </h3>
                  {user && (
                    <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/40">
                      Баланс: {user.credits_remaining ?? 0} баллов
                    </Badge>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <Input
                    type="date"
                    value={selectedQuarterDate}
                    onChange={(e) => {
                      setSelectedQuarterDate(e.target.value);
                      console.log('📅 Выбрана новая дата квартала:', e.target.value);
                    }}
                    className={`w-48 ${themeConfig.surface} backdrop-blur-xl`}
                  />
                  <Button 
                    onClick={loadQuarterlyData}
                    disabled={quarterlyLoading || !user?.city}
                    className="bg-teal-500 hover:bg-teal-600"
                  >
                    {quarterlyLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Загрузка...
                      </>
                    ) : (
                      <>
                        <CalendarRange className="h-4 w-4 mr-2" />
                        Загрузить ({costs.planetary_quarterly} баллов)
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>

            {!user?.city ? (
              <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                <div className="text-center py-12">
                  <Info className={`h-16 w-16 mx-auto mb-4 ${themeConfig.mutedText}`} />
                  <h3 className={`text-2xl font-bold mb-2 ${themeConfig.text}`}>
                    Укажите город в профиле
                  </h3>
                  <p className={themeConfig.mutedText}>
                    Для квартального маршрута нужен город (для расчёта ведических периодов и расписания).
                  </p>
                </div>
              </div>
            ) : (
              <>
                {activeTab === 'quarter' && error && (
                  <div className={`rounded-3xl border p-6 ${themeConfig.glass}`}>
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="h-6 w-6 text-red-500" />
                      <div className={themeConfig.text}>
                        <span className="font-semibold">Ошибка:</span> {error}
                      </div>
                    </div>
                  </div>
                )}

                {quarterlyLoading ? (
                  <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                    <div className={`flex items-center justify-center py-12 ${themeConfig.text}`}>
                      <Loader2 className="h-8 w-8 animate-spin text-teal-500 mr-3" />
                      <span>Загрузка квартального маршрута...</span>
                    </div>
                  </div>
                ) : quarterlyData ? (
                  <>
                    <div
                      className={`rounded-3xl border p-8 transition-all duration-500 ${themeConfig.glass}`}
                      style={{
                        borderColor: '#14b8a640',
                        boxShadow: '0 0 40px rgba(20, 184, 166, 0.12)'
                      }}
                    >
                      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                        <div>
                          <div className="flex items-center gap-3">
                            <CalendarRange className="h-6 w-6 text-teal-500 drop-shadow-[0_0_10px_rgba(20,184,166,0.45)]" />
                            <h2 className={`text-2xl font-bold ${themeConfig.text}`}>Планетарный маршрут на квартал</h2>
                          </div>
                          <p className={`mt-2 ${themeConfig.mutedText}`}>
                            {formatDateRu(quarterlyData.start_date)} — {formatDateRu(quarterlyData.end_date)} · {quarterlyData.city}
                          </p>
                          <div className="mt-3 flex flex-wrap gap-2">
                            <Badge className="bg-teal-500/20 text-teal-400 border-teal-500/40">
                              {quarterlyData.total_weeks || quarterWeeks.length || 0} недель
                            </Badge>
                            <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/40">
                              {quarterSummary.total_best_days ?? 0} лучших дней
                            </Badge>
                            <Badge className="bg-red-500/20 text-red-400 border-red-500/40">
                              {quarterSummary.total_challenging_days ?? 0} сложных дней
                            </Badge>
                            {quarterEnergyTrend && (
                              <Badge className="bg-indigo-500/20 text-indigo-400 border-indigo-500/40">
                                тренд: {quarterEnergyTrend.trend}
                              </Badge>
                            )}
                          </div>
                        </div>

                        <div className="flex gap-3">
                          <Button
                            onClick={loadQuarterlyData}
                            className="bg-teal-500 hover:bg-teal-600"
                            disabled={quarterlyLoading}
                          >
                            Обновить квартал ({costs.planetary_quarterly} баллов)
                          </Button>
                        </div>
                      </div>
                    </div>

                    {/* 4 блока из бывшей заглушки — теперь с реальными данными */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* 🎯 Обзор квартала */}
                      <div className={`p-6 rounded-2xl border ${themeConfig.surface}`}>
                        <h4 className={`font-bold text-lg mb-3 ${themeConfig.text}`}>🎯 Обзор квартала</h4>
                        <div className={`space-y-3 text-sm ${themeConfig.mutedText}`}>
                          <div>
                            <div className={`font-semibold ${themeConfig.text}`}>Главные темы 3 месяцев</div>
                            <ul className="mt-2 space-y-1">
                              {(quarterMonthSummaries.length ? quarterMonthSummaries : []).slice(0, 3).map((m) => (
                                <li key={m.key}>
                                  • {m.label}: доминирующая планета — <span className={themeConfig.text}>{m.dominant_planet || 'нет данных'}</span>
                                </li>
                              ))}
                              {!quarterMonthSummaries.length && <li>• Нет данных для помесячной темы</li>}
                            </ul>
                          </div>

                          <div>
                            <div className={`font-semibold ${themeConfig.text}`}>Ключевые планетарные циклы (по неделям)</div>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {Object.entries(quarterSummary?.planet_weeks_distribution || {})
                                .sort((a, b) => (b?.[1] || 0) - (a?.[1] || 0))
                                .slice(0, 8)
                                .map(([planet, count]) => (
                                  <span
                                    key={planet}
                                    className="px-3 py-1 rounded-xl border text-xs"
                                    style={{
                                      borderColor: `${getPlanetColor(planet)}50`,
                                      backgroundColor: themeConfig.isDark ? `${getPlanetColor(planet)}18` : `${getPlanetColor(planet)}10`,
                                      color: themeConfig.isDark ? `${getPlanetColor(planet)}DD` : `${getPlanetColor(planet)}CC`
                                    }}
                                  >
                                    {planet}: {count} нед.
                                  </span>
                                ))}
                              {!Object.keys(quarterSummary?.planet_weeks_distribution || {}).length && (
                                <span className="text-xs">Нет распределения по планетам</span>
                              )}
                            </div>
                          </div>

                          <div>
                            <div className={`font-semibold ${themeConfig.text}`}>Благоприятные месяцы</div>
                            <ul className="mt-2 space-y-1">
                              {quarterMonthSummaries
                                .filter((m) => (m.avg_energy || 0) >= 60 && (m.challenging_days_count || 0) <= (m.days_count || 1) * 0.45)
                                .slice(0, 3)
                                .map((m) => (
                                  <li key={m.key}>
                                    • {m.label}: средняя энергия ~ <span className={themeConfig.text}>{m.avg_energy}%</span>
                                  </li>
                                ))}
                              {!quarterMonthSummaries.filter((m) => (m.avg_energy || 0) >= 60).length && (
                                <li>• По текущим данным явно выделенных благоприятных месяцев нет — ориентируйтесь по фокус-неделям ниже</li>
                              )}
                            </ul>
                          </div>

                          <div>
                            <div className={`font-semibold ${themeConfig.text}`}>Периоды трансформации (зоны риска)</div>
                            <ul className="mt-2 space-y-1">
                              {(quarterSummary?.quarterly_advice?.rest_weeks || []).length ? (
                                (quarterSummary.quarterly_advice.rest_weeks || []).map((num) => {
                                  const w = quarterWeekByNumber.get(num);
                                  return (
                                    <li key={num}>
                                      • Неделя {num}
                                      {w?.start_date ? ` (${formatDateRu(w.start_date)} — ${formatDateRu(w.end_date)})` : ''} — лучше снижать темп
                                    </li>
                                  );
                                })
                              ) : (
                                <li>• Нет ярко выраженных «недель отдыха» — контролируйте нагрузку по сложным дням</li>
                              )}
                            </ul>
                          </div>
                        </div>
                      </div>

                      {/* 📊 Помесячный анализ */}
                      <div className={`p-6 rounded-2xl border ${themeConfig.surface}`}>
                        <h4 className={`font-bold text-lg mb-3 ${themeConfig.text}`}>📊 Помесячный анализ</h4>
                        <div className={`space-y-4 text-sm ${themeConfig.mutedText}`}>
                          {(quarterMonthSummaries.length ? quarterMonthSummaries : []).slice(0, 3).map((m) => (
                            <div key={m.key} className={`p-4 rounded-xl border ${themeConfig.isDark ? 'border-white/10 bg-white/5' : 'border-gray-200 bg-white/60'}`}>
                              <div className={`font-semibold ${themeConfig.text}`}>
                                {m.label} · {formatDateRu(m.start_date)} — {formatDateRu(m.end_date)}
                              </div>
                              <div className="mt-2 grid grid-cols-1 sm:grid-cols-3 gap-2">
                                <div className={`p-2 rounded-lg ${themeConfig.isDark ? 'bg-emerald-500/10' : 'bg-emerald-50'}`}>
                                  <span className="font-semibold">Благоприятных:</span> {m.favorable_days_count}
                                </div>
                                <div className={`p-2 rounded-lg ${themeConfig.isDark ? 'bg-red-500/10' : 'bg-red-50'}`}>
                                  <span className="font-semibold">Сложных:</span> {m.challenging_days_count}
                                </div>
                                <div className={`p-2 rounded-lg ${themeConfig.isDark ? 'bg-indigo-500/10' : 'bg-indigo-50'}`}>
                                  <span className="font-semibold">Энергия:</span> ~{m.avg_energy}%
                                </div>
                              </div>

                              <div className="mt-3">
                                <div className={`font-semibold ${themeConfig.text}`}>Ключевые события (лучшие дни)</div>
                                <div className="mt-2 flex flex-wrap gap-2">
                                  {(m.best_days || []).slice(0, 5).map((d) => (
                                    <span
                                      key={d.date}
                                      className="px-3 py-1 rounded-xl border text-xs"
                                      style={{
                                        borderColor: '#10b98140',
                                        backgroundColor: themeConfig.isDark ? '#10b98118' : '#10b98110',
                                        color: themeConfig.isDark ? '#34d399' : '#047857'
                                      }}
                                    >
                                      {formatDateRu(d.date)} · {normalizeRulingPlanet(d.ruling_planet) || '—'} · {Math.round(d.avg_energy_per_planet || 0)}%
                                    </span>
                                  ))}
                                  {!m.best_days?.length && <span className="text-xs">Нет оценок энергии для выделения лучших дней</span>}
                                </div>
                              </div>

                              <div className="mt-3">
                                <div className={`font-semibold ${themeConfig.text}`}>Рекомендации по планированию</div>
                                <div className="mt-2">
                                  {(m.avg_energy || 0) >= 60
                                    ? 'Месяц подходит для запусков и расширения — планируйте ключевые шаги на фокус-недели.'
                                    : 'Месяц лучше использовать для подготовки, обучения и выравнивания процессов — избегайте перегруза в сложные дни.'}
                                </div>
                              </div>
                            </div>
                          ))}
                          {!quarterMonthSummaries.length && (
                            <div className="text-sm">Нет данных для помесячного анализа.</div>
                          )}
                        </div>
                      </div>

                      {/* 🌟 Долгосрочные цели */}
                      <div className={`p-6 rounded-2xl border ${themeConfig.surface}`}>
                        <h4 className={`font-bold text-lg mb-3 ${themeConfig.text}`}>🌟 Долгосрочные цели</h4>
                        <div className={`space-y-4 text-sm ${themeConfig.mutedText}`}>
                          <div>
                            <div className={`font-semibold ${themeConfig.text}`}>Оптимальное время для больших проектов</div>
                            <ul className="mt-2 space-y-1">
                              {(quarterSummary?.quarterly_advice?.focus_weeks || []).length ? (
                                (quarterSummary.quarterly_advice.focus_weeks || []).map((num) => {
                                  const w = quarterWeekByNumber.get(num);
                                  return (
                                    <li key={num}>
                                      • Неделя {num}
                                      {w?.start_date ? ` (${formatDateRu(w.start_date)} — ${formatDateRu(w.end_date)})` : ''} — высокий потенциал
                                    </li>
                                  );
                                })
                              ) : (
                                <li>• Нет выделенных «фокус-недель» — ориентируйтесь на лучшие дни и недели с высокой средней энергией</li>
                              )}
                            </ul>
                          </div>

                          <div>
                            <div className={`font-semibold ${themeConfig.text}`}>Периоды роста и развития</div>
                            <ul className="mt-2 space-y-1">
                              {(quarterSummary?.best_weeks || []).length ? (
                                (quarterSummary.best_weeks || []).slice(0, 5).map((w) => (
                                  <li key={w.week_number}>
                                    • Неделя {w.week_number} ({formatDateRu(w.start_date)} — {formatDateRu(w.end_date)}) — {w.best_days?.length || 0} сильных дней
                                  </li>
                                ))
                              ) : (
                                <li>• Нет ярко выраженных «лучших недель» — используйте точечно лучшие дни</li>
                              )}
                            </ul>
                          </div>

                          <div>
                            <div className={`font-semibold ${themeConfig.text}`}>Время для обучения</div>
                            <ul className="mt-2 space-y-1">
                              {quarterWeekMetrics
                                .filter((w) => ['Budh', 'Budha', 'Guru'].includes(String(w?.dominant_planet || '')))
                                .slice(0, 5)
                                .map((w) => (
                                  <li key={w.week_number}>
                                    • Неделя {w.week_number} ({formatDateRu(w.start_date)} — {formatDateRu(w.end_date)}) — {w.dominant_planet}
                                  </li>
                                ))}
                              {!quarterWeekMetrics.some((w) => ['Budh', 'Budha', 'Guru'].includes(String(w?.dominant_planet || ''))) && (
                                <li>• Выделенных «учебных недель» нет — планируйте обучение в дни Будхи/Гуру внутри недельного плана</li>
                              )}
                            </ul>
                          </div>

                          <div>
                            <div className={`font-semibold ${themeConfig.text}`}>Карьерные возможности</div>
                            <ul className="mt-2 space-y-1">
                              {quarterWeekMetrics
                                .filter((w) => ['Surya', 'Mangal', 'Shani'].includes(String(w?.dominant_planet || '')))
                                .slice(0, 5)
                                .map((w) => (
                                  <li key={w.week_number}>
                                    • Неделя {w.week_number} ({formatDateRu(w.start_date)} — {formatDateRu(w.end_date)}) — {w.dominant_planet}
                                  </li>
                                ))}
                              {!quarterWeekMetrics.some((w) => ['Surya', 'Mangal', 'Shani'].includes(String(w?.dominant_planet || ''))) && (
                                <li>• Нет явного карьерного доминирования — используйте фокус-недели и лучшие дни для ключевых решений</li>
                              )}
                            </ul>
                          </div>
                        </div>
                      </div>

                      {/* 🔮 Стратегический прогноз */}
                      <div className={`p-6 rounded-2xl border ${themeConfig.surface}`}>
                        <h4 className={`font-bold text-lg mb-3 ${themeConfig.text}`}>🔮 Стратегический прогноз</h4>
                        <div className={`space-y-4 text-sm ${themeConfig.mutedText}`}>
                          <div>
                            <div className={`font-semibold ${themeConfig.text}`}>Долгосрочные тренды</div>
                            <div className="mt-2">
                              {quarterEnergyTrend ? (
                                <>
                                  Тренд энергии: <span className={themeConfig.text}>{quarterEnergyTrend.trend}</span> (с {quarterEnergyTrend.avg_first}% до {quarterEnergyTrend.avg_last}%).
                                </>
                              ) : (
                                'Недостаточно данных для расчёта тренда.'
                              )}
                            </div>
                          </div>

                          <div>
                            <div className={`font-semibold ${themeConfig.text}`}>Важные решения и выборы</div>
                            <ul className="mt-2 space-y-1">
                              {quarterTopDays.length ? (
                                quarterTopDays.map((d) => (
                                  <li key={d.date}>
                                    • {formatDateRu(d.date)} — {normalizeRulingPlanet(d.ruling_planet) || '—'} · {Math.round(d.avg_energy_per_planet || 0)}%
                                  </li>
                                ))
                              ) : (
                                <li>• Нет данных по энергии для выделения лучших дней</li>
                              )}
                            </ul>
                          </div>

                          <div>
                            <div className={`font-semibold ${themeConfig.text}`}>Периоды отдыха и восстановления</div>
                            <ul className="mt-2 space-y-1">
                              {(quarterSummary?.quarterly_advice?.rest_weeks || []).length ? (
                                (quarterSummary.quarterly_advice.rest_weeks || []).map((num) => {
                                  const w = quarterWeekByNumber.get(num);
                                  return (
                                    <li key={num}>
                                      • Неделя {num}
                                      {w?.start_date ? ` (${formatDateRu(w.start_date)} — ${formatDateRu(w.end_date)})` : ''} — бережный режим
                                    </li>
                                  );
                                })
                              ) : quarterHardDays.length ? (
                                quarterHardDays.map((d) => (
                                  <li key={d.date}>
                                    • {formatDateRu(d.date)} — сложный день, {normalizeRulingPlanet(d.ruling_planet) || '—'}
                                  </li>
                                ))
                              ) : (
                                <li>• Нет выделенных периодов отдыха</li>
                              )}
                            </ul>
                          </div>

                          <div>
                            <div className={`font-semibold ${themeConfig.text}`}>Рекомендации по балансу жизни</div>
                            <div className="mt-2">
                              {quarterSummary?.quarterly_advice?.strategy || 'Держите баланс: активность в сильные недели, восстановление в сложные.'}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Недельный план квартала */}
                    <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                      <div className="flex items-center gap-3 mb-6">
                        <CalendarDays className="h-6 w-6 text-teal-500 drop-shadow-[0_0_10px_rgba(20,184,166,0.45)]" />
                        <h2 className={`text-2xl font-bold ${themeConfig.text}`}>🗓️ Недельный план квартала</h2>
                      </div>

                      <div className="space-y-3">
                        {quarterWeekMetrics.map((w) => (
                          <div key={w.week_number} className={`p-4 rounded-2xl border ${themeConfig.isDark ? 'border-white/10 bg-white/5' : 'border-gray-200 bg-white/60'}`}>
                            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                              <div>
                                <div className={`font-bold ${themeConfig.text}`}>
                                  Неделя {w.week_number}: {formatDateRu(w.start_date)} — {formatDateRu(w.end_date)}
                                </div>
                                <div className={`text-sm ${themeConfig.mutedText}`}>
                                  Доминирующая планета: <span className={themeConfig.text}>{w.dominant_planet || '—'}</span> ·
                                  средняя энергия ~ <span className={themeConfig.text}>{w.avg_energy}%</span> ·
                                  благоприятных {w.favorable_days_count} / сложных {w.challenging_days_count}
                                </div>
                              </div>
                              <div className="flex gap-2 flex-wrap">
                                {(w.best_days?.length || 0) > 0 && (
                                  <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/40">
                                    сильных дней: {w.best_days.length}
                                  </Badge>
                                )}
                                {(w.challenging_days?.length || 0) > 0 && (
                                  <Badge className="bg-red-500/20 text-red-400 border-red-500/40">
                                    сложных дней: {w.challenging_days.length}
                                  </Badge>
                                )}
                              </div>
                            </div>

                            {/* Дни недели */}
                            {Array.isArray(w.days) && w.days.length > 0 && (
                              <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
                                {w.days.map((d) => {
                                  const isHard = d?.day_type === 'challenging';
                                  const planet = normalizeRulingPlanet(d?.ruling_planet);
                                  const color = planet ? getPlanetColor(planet) : (isHard ? '#ef4444' : '#10b981');
                                  return (
                                    <div
                                      key={d.date}
                                      className="p-3 rounded-xl border transition-all duration-200"
                                      style={{
                                        borderColor: `${color}40`,
                                        backgroundColor: themeConfig.isDark ? `${color}14` : `${color}0D`
                                      }}
                                    >
                                      <div className={`text-xs ${themeConfig.mutedText}`}>{formatDateRu(d.date)}</div>
                                      <div className={`font-semibold text-sm ${themeConfig.text}`} style={{ color }}>
                                        {planet || '—'}
                                      </div>
                                      <div className={`text-xs ${themeConfig.mutedText}`}>
                                        {d.day_type_ru || (isHard ? 'Неблагоприятный' : 'Благоприятный')}
                                        {typeof d.avg_energy_per_planet === 'number' && (
                                          <span> · {Math.round(d.avg_energy_per_planet)}%</span>
                                        )}
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                ) : (
                  <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
                    <div className="text-center py-12">
                      <CalendarRange className={`h-16 w-16 mx-auto mb-4 ${themeConfig.mutedText}`} />
                      <h3 className={`text-2xl font-bold mb-2 ${themeConfig.text}`}>
                        Планетарный маршрут на квартал
                      </h3>
                      <p className={`${themeConfig.mutedText} mb-6`}>
                        Стратегический анализ на 3 месяца с долгосрочными прогнозами
                      </p>
                      <Button onClick={loadQuarterlyData} disabled={!user?.city} className="bg-teal-500 hover:bg-teal-600">
                        Загрузить квартальный маршрут ({costs.planetary_quarterly} баллов)
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Модальное окно с советами для планетарного часа */}
      <Dialog open={isHourDialogOpen} onOpenChange={setIsHourDialogOpen}>
        <DialogContent className={`max-w-2xl max-h-[80vh] overflow-y-auto ${themeConfig.card}`}>
          {selectedHour ? (
            <HourAdviceContent 
              hour={selectedHour} 
              getAdvice={getPersonalizedAdvice} 
              themeConfig={themeConfig} 
            />
          ) : (
            <>
              <DialogHeader>
                <DialogTitle>Планетарный час</DialogTitle>
                <DialogDescription>Выберите час для просмотра рекомендаций</DialogDescription>
              </DialogHeader>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Модальное окно с детальной информацией о дне недели */}
      <Dialog open={isDayDialogOpen} onOpenChange={setIsDayDialogOpen}>
        <DialogContent className={`max-w-3xl max-h-[80vh] overflow-y-auto ${themeConfig.card}`}>
          {selectedDay ? (
            <>
              <DialogHeader>
                <DialogTitle 
                  className="text-2xl font-bold flex items-center gap-3"
                  style={getPlanetTitleGlow(themeConfig.isDark, getPlanetColor(selectedDay.ruling_planet))}
                >
                  <span className="text-3xl">
                    {selectedDay.ruling_planet === 'Surya' && '☀️'}
                    {selectedDay.ruling_planet === 'Chandra' && '🌙'}
                    {selectedDay.ruling_planet === 'Mangal' && '🔴'}
                    {selectedDay.ruling_planet === 'Budh' && '💚'}
                    {selectedDay.ruling_planet === 'Guru' && '🟠'}
                    {selectedDay.ruling_planet === 'Shukra' && '💗'}
                    {selectedDay.ruling_planet === 'Shani' && '🔵'}
                    {selectedDay.ruling_planet === 'Rahu' && '🌑'}
                    {selectedDay.ruling_planet === 'Ketu' && '⚪'}
                  </span>
                  {selectedDay.weekday_name}, {new Date(selectedDay.date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' })}
                </DialogTitle>
                <DialogDescription 
                  className={themeConfig.mutedText}
                  style={getTextGlow(themeConfig.isDark)}
                >
                  {selectedDay.planet_sanskrit || selectedDay.ruling_planet ? (
                    <>
                      Планета дня: {selectedDay.planet_sanskrit || selectedDay.ruling_planet}
                      {((selectedDay.day_score !== undefined && selectedDay.day_score !== null) || 
                        (selectedDay.compatibility_score !== undefined && selectedDay.compatibility_score !== null)) && (
                        <span className="ml-3">
                          Оценка: <span style={{
                            color: ((selectedDay.day_score !== undefined && selectedDay.day_score !== null ? selectedDay.day_score : selectedDay.compatibility_score) >= 70) ? '#10b981' :
                                   ((selectedDay.day_score !== undefined && selectedDay.day_score !== null ? selectedDay.day_score : selectedDay.compatibility_score) >= 50) ? '#3b82f6' : '#ef4444',
                            ...getAccentGlow(themeConfig.isDark, ((selectedDay.day_score !== undefined && selectedDay.day_score !== null ? selectedDay.day_score : selectedDay.compatibility_score) >= 70) ? '#10b981' : ((selectedDay.day_score !== undefined && selectedDay.day_score !== null ? selectedDay.day_score : selectedDay.compatibility_score) >= 50) ? '#3b82f6' : '#ef4444')
                          }}>{(selectedDay.day_score !== undefined && selectedDay.day_score !== null) ? Math.round(selectedDay.day_score) : Math.round(selectedDay.compatibility_score)}/100</span>
                        </span>
                      )}
                    </>
                  ) : (
                    'Детальная информация о планетарном дне'
                  )}
                </DialogDescription>
              </DialogHeader>

              <div className="mt-6 space-y-6">
                {/* Краткий совет */}
                {selectedDay.key_advice && (
                  <div className={`p-4 rounded-lg ${themeConfig.surface}`}>
                    <p 
                      className={themeConfig.text}
                      style={getTextGlow(themeConfig.isDark)}
                    >
                      {selectedDay.key_advice}
                    </p>
                  </div>
                )}

                {/* Позитивные аспекты */}
                {selectedDay.positive_aspects && selectedDay.positive_aspects.length > 0 && (
                  <div>
                    <h3 
                      className={`font-bold text-lg mb-3 flex items-center gap-2 ${themeConfig.text}`}
                      style={getTitleGlow(themeConfig.isDark, '#10b981')}
                    >
                      <CheckCircle className="h-5 w-5 text-emerald-500" />
                      Ваши сильные стороны
                    </h3>
                    <div className="space-y-2">
                      {selectedDay.positive_aspects.map((aspect, idx) => (
                        <div 
                          key={idx}
                          className={`p-3 rounded-lg border ${themeConfig.surface}`}
                          style={{
                            borderColor: '#10b98140',
                            backgroundColor: themeConfig.isDark ? '#10b98110' : '#10b98108'
                          }}
                        >
                          <p 
                            className={`font-semibold text-sm ${themeConfig.text}`}
                            style={getTextGlow(themeConfig.isDark, '#10b981')}
                          >
                            {aspect.title}
                          </p>
                          <p 
                            className={`text-xs mt-1 ${themeConfig.mutedText}`}
                            style={getTextGlow(themeConfig.isDark)}
                          >
                            {aspect.short_text}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Вызовы */}
                {/* Личная энергия планеты дня */}
                {selectedDay.personal_planet_energy !== undefined && selectedDay.personal_planet_energy >= 0 && (
                  <div 
                    className={`p-4 rounded-lg border-2 ${themeConfig.text}`}
                    style={{
                      borderColor: selectedDay.personal_planet_energy === 0 ? '#ef4444' : 
                                   selectedDay.personal_planet_energy <= 3 ? '#f97316' :
                                   selectedDay.personal_planet_energy >= 7 ? '#10b981' : '#3b82f6',
                      backgroundColor: themeConfig.isDark 
                        ? (selectedDay.personal_planet_energy === 0 ? '#ef444420' : 
                           selectedDay.personal_planet_energy <= 3 ? '#f9731620' :
                           selectedDay.personal_planet_energy >= 7 ? '#10b98120' : '#3b82f620')
                        : (selectedDay.personal_planet_energy === 0 ? '#ef444410' : 
                           selectedDay.personal_planet_energy <= 3 ? '#f9731610' :
                           selectedDay.personal_planet_energy >= 7 ? '#10b98110' : '#3b82f610')
                    }}
                  >
                    <h3 className="font-bold text-lg mb-2 flex items-center gap-2">
                      {selectedDay.personal_planet_energy === 0 && <span className="text-2xl">🚨</span>}
                      {selectedDay.personal_planet_energy > 0 && selectedDay.personal_planet_energy <= 3 && <span className="text-2xl">⚡</span>}
                      {selectedDay.personal_planet_energy >= 7 && <span className="text-2xl">✨</span>}
                      {selectedDay.personal_planet_energy > 3 && selectedDay.personal_planet_energy < 7 && <span className="text-2xl">📊</span>}
                      <span style={{
                        color: selectedDay.personal_planet_energy === 0 ? '#ef4444' : 
                               selectedDay.personal_planet_energy <= 3 ? '#f97316' :
                               selectedDay.personal_planet_energy >= 7 ? '#10b981' : '#3b82f6'
                      }}>
                        Ваша личная энергия {selectedDay.planet_sanskrit || selectedDay.ruling_planet}
                      </span>
                    </h3>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className={`text-sm ${themeConfig.mutedText}`}>Энергия дня (DDMM × YYYY):</span>
                        <span className="text-2xl font-bold" style={{
                          color: selectedDay.personal_planet_energy === 0 ? '#ef4444' : 
                                 selectedDay.personal_planet_energy <= 3 ? '#f97316' :
                                 selectedDay.personal_planet_energy >= 7 ? '#10b981' : '#3b82f6'
                        }}>
                          {selectedDay.personal_planet_energy}/9
                        </span>
                      </div>
                      
                      {selectedDay.personal_planet_energy === 0 && (
                        <div className="mt-3">
                          <p className="text-sm font-bold text-red-500 mb-2">
                            ⚠️ КРИТИЧЕСКИЙ ДЕНЬ: НУЛЕВАЯ ЭНЕРГИЯ!
                          </p>
                          <p className={`text-xs ${themeConfig.mutedText}`}>
                            У вас полное отсутствие резонанса с энергией этого дня недели. 
                            Это один из самых сложных дней для вас. Избегайте важных начинаний, 
                            отдохните и восстановите силы.
                          </p>
                        </div>
                      )}
                      
                      {selectedDay.personal_planet_energy > 0 && selectedDay.personal_planet_energy <= 3 && (
                        <div className="mt-3">
                          <p className="text-sm font-bold text-orange-500 mb-2">
                            ⚡ Низкая энергия дня
                          </p>
                          <p className={`text-xs ${themeConfig.mutedText}`}>
                            Ваша личная энергия в этот день недели низкая. 
                            Планируйте меньше дел, делайте больше перерывов, 
                            избегайте энергозатратных задач.
                          </p>
                        </div>
                      )}
                      
                      {selectedDay.personal_planet_energy >= 7 && (
                        <div className="mt-3">
                          <p className="text-sm font-bold text-emerald-500 mb-2">
                            ✨ ВЫСОКАЯ ЭНЕРГИЯ ДНЯ!
                          </p>
                          <p className={`text-xs ${themeConfig.mutedText}`}>
                            Ваша личная энергия в этот день недели на пике! 
                            Планируйте самые важные дела, начинайте новые проекты, 
                            проводите важные встречи и переговоры.
                          </p>
                        </div>
                      )}
                      
                      {selectedDay.personal_planet_energy > 3 && selectedDay.personal_planet_energy < 7 && (
                        <div className="mt-3">
                          <p className="text-sm font-bold text-blue-500 mb-2">
                            📊 Средняя энергия дня
                          </p>
                          <p className={`text-xs ${themeConfig.mutedText}`}>
                            Ваша личная энергия в этот день недели на среднем уровне. 
                            Подходит для рутинных дел и текущих проектов.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {selectedDay.challenges && selectedDay.challenges.length > 0 && (
                  <div>
                    <h3 className={`font-bold text-lg mb-3 flex items-center gap-2 ${themeConfig.text}`}>
                      <AlertTriangle className="h-5 w-5 text-amber-500" />
                      Области для внимания
                    </h3>
                    <div className="space-y-2">
                      {selectedDay.challenges.map((challenge, idx) => (
                        <div 
                          key={idx}
                          className={`p-3 rounded-lg border ${themeConfig.surface}`}
                          style={{
                            borderColor: '#ef444440',
                            backgroundColor: themeConfig.isDark ? '#ef444410' : '#ef444408'
                          }}
                        >
                          <p className={`font-semibold text-sm ${themeConfig.text}`}>{challenge.title}</p>
                          <p className={`text-xs mt-1 ${themeConfig.mutedText}`}>{challenge.short_text}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Благоприятные действия */}
                {selectedDay.favorable_activities && selectedDay.favorable_activities.length > 0 && (
                  <div>
                    <h3 className={`font-bold text-lg mb-3 flex items-center gap-2 ${themeConfig.text}`}>
                      <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                      Благоприятные действия
                    </h3>
                    <ul className="space-y-2">
                      {selectedDay.favorable_activities.map((activity, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-emerald-500 mt-1">✓</span>
                          <span className={themeConfig.mutedText}>{activity}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Чего избегать */}
                {selectedDay.avoid_activities && selectedDay.avoid_activities.length > 0 && (
                  <div>
                    <h3 className={`font-bold text-lg mb-3 flex items-center gap-2 ${themeConfig.text}`}>
                      <AlertTriangle className="h-5 w-5 text-amber-500" />
                      Чего избегать
                    </h3>
                    <ul className="space-y-2">
                      {selectedDay.avoid_activities.map((item, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-amber-500 mt-1">⚠</span>
                          <span className={themeConfig.mutedText}>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Rahu Kaal предупреждение */}
                {selectedDay.rahu_kaal && selectedDay.rahu_kaal.start && (
                  <div 
                    className={`p-4 rounded-lg border-2 ${themeConfig.text}`}
                    style={{
                      borderColor: '#ef4444',
                      backgroundColor: themeConfig.isDark ? '#ef444410' : '#ef444408'
                    }}
                  >
                    <h3 className="font-bold text-sm mb-2 flex items-center gap-2 text-red-500">
                      ⚠️ Rahu Kaal
                    </h3>
                    <p className="text-sm">
                      С {selectedDay.rahu_kaal.start} до {selectedDay.rahu_kaal.end} - избегайте начинаний
                    </p>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <DialogHeader>
                <DialogTitle>День недели</DialogTitle>
                <DialogDescription>Выберите день для просмотра деталей</DialogDescription>
              </DialogHeader>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Футер с информацией о версии */}
      <div className={`relative z-10 max-w-7xl mx-auto px-6 pb-6`}>
        <div className={`mt-8 p-4 rounded-2xl border text-center ${themeConfig.isDark ? 'bg-slate-900/60 border-slate-700/50 backdrop-blur-xl' : 'bg-white/80 border-slate-200'}`}>
          <div className="flex flex-col md:flex-row items-center justify-center gap-2 md:gap-4 text-xs font-mono">
            <span className={themeConfig.mutedText}>
              📦 Build: <span className={`font-bold ${themeConfig.isDark ? 'text-purple-400' : 'text-purple-600'}`}>
                {buildVersion}
              </span>
            </span>
            <span className={`hidden md:inline ${themeConfig.mutedText}`}>·</span>
            <span className={themeConfig.mutedText}>
              🕐 {new Date(buildDate).toLocaleString('ru-RU', { 
                day: '2-digit', 
                month: '2-digit', 
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </span>
            <span className={`hidden md:inline ${themeConfig.mutedText}`}>·</span>
            <span className={`text-xs ${themeConfig.mutedText}`}>
              💰 Цены из БД загружены
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Компонент для отображения советов в модальном окне
const HourAdviceContent = ({ hour, getAdvice, themeConfig }) => {
  const [advice, setAdvice] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAdvice = async () => {
      setLoading(true);
      const data = await getAdvice(hour);
      setAdvice(data);
      setLoading(false);
    };
    
    loadAdvice();
  }, [hour, getAdvice]);

  if (loading) {
    return (
      <div className={`flex items-center justify-center py-12 ${themeConfig.text}`}>
        <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
        <span className="ml-3 text-lg">Загрузка советов...</span>
      </div>
    );
  }

  if (!advice) {
    return (
      <div className={`text-center py-12 ${themeConfig.text}`}>
        <AlertTriangle className="h-12 w-12 mx-auto text-amber-500 mb-4" />
        <p className="text-lg">Не удалось загрузить советы</p>
      </div>
    );
  }

  const planetColor = getPlanetColor(advice.planet);
  
  // Функция для получения правильного фона в зависимости от темы
  const getBackgroundStyle = (opacity = '20') => {
    if (themeConfig.isDark) {
      return { backgroundColor: planetColor + opacity };
    } else {
      // Для светлой темы используем более насыщенные цвета
      return { backgroundColor: planetColor + '30' };
    }
  };
  
  const getBorderStyle = (opacity = '60') => {
    if (themeConfig.isDark) {
      return { borderColor: planetColor + opacity };
    } else {
      // Для светлой темы используем более насыщенные границы
      return { borderColor: planetColor + '80' };
    }
  };

  return (
    <>
      <DialogHeader>
        <DialogTitle 
          className="text-2xl font-bold flex items-center gap-3"
          style={getPlanetTitleGlow(themeConfig.isDark, planetColor)}
        >
          <span className="text-3xl">
            {advice.planet === 'Surya' && '☀️'}
            {advice.planet === 'Chandra' && '🌙'}
            {advice.planet === 'Mangal' && '🔴'}
            {advice.planet === 'Budh' && '💚'}
            {advice.planet === 'Guru' && '🟠'}
            {advice.planet === 'Shukra' && '💗'}
            {advice.planet === 'Shani' && '🔵'}
            {advice.planet === 'Rahu' && '🌑'}
            {advice.planet === 'Ketu' && '⚪'}
          </span>
          {advice.planet_sanskrit || advice.planetSanskrit}
        </DialogTitle>
        <DialogDescription className={themeConfig.mutedText}>
          Планетарный час: {advice.time}
          {advice.isFavorable && (
            <span className="ml-3 inline-flex items-center gap-1 text-emerald-500">
              <CheckCircle2 className="h-4 w-4" />
              Благоприятное время
            </span>
          )}
        </DialogDescription>
      </DialogHeader>

      <div className="mt-6 space-y-6">
        {/* Персонализированные заметки */}
        {advice.personalized_notes && advice.personalized_notes.length > 0 && (
          <div className="space-y-3">
            {advice.personalized_notes.map((note, idx) => (
              <div 
                key={idx}
                className={`p-4 rounded-lg border-2 ${themeConfig.text}`}
                style={{
                  ...getBackgroundStyle('20'),
                  ...getBorderStyle('60')
                }}
              >
                <p className="font-bold text-sm mb-1">{note.title}</p>
                <p className="text-sm">{note.advice}</p>
              </div>
            ))}
          </div>
        )}

        {/* Общая характеристика */}
        <div>
          <h3 className={`font-bold text-lg mb-2 flex items-center gap-2 ${themeConfig.text}`}>
            <Sparkles className="h-5 w-5" style={{ color: planetColor }} />
            Общая характеристика
          </h3>
          <p className={themeConfig.mutedText}>{advice.general_advice || advice.general}</p>
        </div>

        {/* Благоприятные действия */}
        <div>
          <h3 className={`font-bold text-lg mb-3 flex items-center gap-2 ${themeConfig.text}`}>
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
            Благоприятные действия
          </h3>
          <ul className="space-y-2">
            {advice.activities.map((activity, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-emerald-500 mt-1">✓</span>
                <span className={themeConfig.mutedText}>{activity}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Чего избегать */}
        <div>
          <h3 className={`font-bold text-lg mb-3 flex items-center gap-2 ${themeConfig.text}`}>
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            Чего избегать
          </h3>
          <ul className="space-y-2">
            {advice.avoid.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-amber-500 mt-1">⚠</span>
                <span className={themeConfig.mutedText}>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Здоровье */}
        <div 
          className={`p-4 rounded-lg ${themeConfig.text}`}
          style={{
            ...getBackgroundStyle('15'),
            borderLeft: `4px solid ${planetColor}`
          }}
        >
          <h3 className="font-bold text-lg mb-2">💊 Здоровье</h3>
          <p className={themeConfig.mutedText}>{advice.health}</p>
        </div>

        {/* Мантра */}
        {advice.mantra && (
          <div 
            className={`p-4 rounded-lg text-center ${themeConfig.text}`}
            style={{
              ...getBackgroundStyle('20'),
              border: `2px solid ${planetColor}${themeConfig.isDark ? '60' : '80'}`
            }}
          >
            <h3 className="font-bold text-lg mb-2">🕉️ Мантра</h3>
            <p className="text-xl font-bold" style={{ color: planetColor }}>{advice.mantra}</p>
          </div>
        )}

        {/* Совет для времени суток */}
        {advice.time_advice && (
          <div className={`p-4 rounded-lg border ${themeConfig.text} ${themeConfig.isDark ? 'bg-blue-500/10 border-blue-500/30' : 'bg-blue-100 border-blue-300'}`}>
            <p className="text-sm italic">{advice.time_advice}</p>
          </div>
        )}
      </div>
    </>
  );
};

export default PlanetaryDailyRouteNew;
