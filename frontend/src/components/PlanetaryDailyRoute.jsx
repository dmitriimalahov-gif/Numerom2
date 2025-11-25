import React, { useState, useEffect, useRef } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Calendar, CalendarDays, Clock, TrendingUp, AlertTriangle, AlertCircle, CheckCircle, Sparkles, Activity, Target, Info, X } from 'lucide-react';
import { useAuth } from './AuthContext';
import { getApiBaseUrl } from '../utils/backendUrl';
import { useTheme } from '../hooks/useTheme';
import { getPlanetColor } from './constants/colors';
import { Line, getElementAtEvent } from 'react-chartjs-2';
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

const PlanetaryDailyRoute = () => {
  const { theme } = useOutletContext();
  const themeConfig = useTheme(theme);
  const [routeData, setRouteData] = useState({});
  const [loading, setLoading] = useState({});
  const [error, setError] = useState('');
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [activeTab, setActiveTab] = useState('daily');
  const [currentTime, setCurrentTime] = useState(new Date());
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [modalData, setModalData] = useState(null);
  const { user } = useAuth();
  const apiBaseUrl = getApiBaseUrl();
  
  // Состояния для управления графиком энергий планет
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
  const [hoveredPlanetsOnChart, setHoveredPlanetsOnChart] = useState([]);
  const chartRef = React.useRef(null);
  
  // Функции для работы с датами и цветами
  const formatDate = (dateString) => {
    if (!dateString) return '';
    try {
      if (dateString.includes('T')) {
        dateString = dateString.split('T')[0];
      }
      if (dateString.includes('.')) {
        const parts = dateString.split('.');
        if (parts.length === 3 && parseInt(parts[0]) < 32 && parseInt(parts[1]) < 13) {
          return dateString;
        }
      }
      if (dateString.includes('-')) {
        const parts = dateString.split('-');
        if (parts.length === 3) {
          return `${parts[2]}.${parts[1]}.${parts[0]}`;
        }
      }
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
  
  const getDayOfWeek = (dateString) => {
    if (!dateString) return '';
    try {
      let date;
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
  
  const getPlanetIndicatorColor = (num) => {
    const colors = {
      1: '#facc15', 2: '#cbd5e1', 3: '#fbbf24', 4: '#fb923c', 5: '#22c55e',
      6: '#f472b6', 7: '#94a3b8', 8: '#3b82f6', 9: '#ef4444'
    };
    return colors[num] || '#6b7280';
  };

  // Утилита для генерации классов с правильной контрастностью
  const getColorClasses = (color) => {
    const isDark = themeConfig.isDark;
    const colorMap = {
      green: {
        bg: isDark ? 'bg-green-500/20' : 'bg-green-50',
        text: isDark ? 'text-green-300' : 'text-green-700',
        border: isDark ? 'border-green-500/40' : 'border-green-300'
      },
      red: {
        bg: isDark ? 'bg-red-500/20' : 'bg-red-50',
        text: isDark ? 'text-red-300' : 'text-red-700',
        border: isDark ? 'border-red-500/40' : 'border-red-300'
      },
      blue: {
        bg: isDark ? 'bg-blue-500/20' : 'bg-blue-50',
        text: isDark ? 'text-blue-300' : 'text-blue-700',
        border: isDark ? 'border-blue-500/40' : 'border-blue-300'
      },
      orange: {
        bg: isDark ? 'bg-orange-500/20' : 'bg-orange-50',
        text: isDark ? 'text-orange-300' : 'text-orange-700',
        border: isDark ? 'border-orange-500/40' : 'border-orange-300'
      },
      purple: {
        bg: isDark ? 'bg-purple-500/20' : 'bg-purple-50',
        text: isDark ? 'text-purple-300' : 'text-purple-700',
        border: isDark ? 'border-purple-500/40' : 'border-purple-300'
      },
      amber: {
        bg: isDark ? 'bg-amber-500/20' : 'bg-amber-50',
        text: isDark ? 'text-amber-300' : 'text-amber-700',
        border: isDark ? 'border-amber-500/40' : 'border-amber-300'
      },
      yellow: {
        bg: isDark ? 'bg-yellow-500/20' : 'bg-yellow-50',
        text: isDark ? 'text-yellow-300' : 'text-yellow-700',
        border: isDark ? 'border-yellow-500/40' : 'border-yellow-300'
      },
      rose: {
        bg: isDark ? 'bg-rose-500/20' : 'bg-rose-50',
        text: isDark ? 'text-rose-300' : 'text-rose-700',
        border: isDark ? 'border-rose-500/40' : 'border-rose-300'
      },
      gray: {
        bg: isDark ? 'bg-gray-500/20' : 'bg-gray-50',
        text: isDark ? 'text-gray-300' : 'text-gray-700',
        border: isDark ? 'border-gray-500/40' : 'border-gray-300'
      }
    };
    return colorMap[color] || colorMap.gray;
  };

  const fetchRouteData = async (period = 'daily', date = selectedDate) => {
    if (!user) return;

    setLoading(prev => ({ ...prev, [period]: true }));
    setError('');

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Токен авторизации не найден. Пожалуйста, войдите в систему.');
      }

      const params = new URLSearchParams();
      if (date) params.append('date', date);
      if (user.city) params.append('city', user.city);

      let endpoint = `${apiBaseUrl}/vedic-time/planetary-route`;
      if (period === 'weekly') {
        endpoint += '/weekly';
      } else if (period === 'monthly') {
        endpoint += '/monthly';
      } else if (period === 'quarterly') {
        endpoint += '/quarterly';
      }

      const url = `${endpoint}?${params}`;
      console.log(`Загрузка планетарного маршрута: ${url}`);

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        credentials: 'include'
      });

      if (!response.ok) {
        let errorMessage = 'Ошибка получения планетарного маршрута';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (e) {
          // Если не удалось распарсить JSON, используем статус
          if (response.status === 401) {
            errorMessage = 'Ошибка авторизации. Пожалуйста, войдите в систему заново.';
          } else if (response.status === 402) {
            errorMessage = 'Недостаточно баллов для получения планетарного маршрута.';
          } else if (response.status === 404) {
            errorMessage = 'Пользователь не найден.';
          } else if (response.status === 422) {
            errorMessage = 'Не указан город или дата рождения. Пожалуйста, обновите профиль.';
          } else if (response.status >= 500) {
            errorMessage = 'Ошибка сервера. Пожалуйста, попробуйте позже.';
          }
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log(`[${period}] Данные получены:`, {
        hasData: !!data,
        keys: Object.keys(data || {}),
        monthlyKeys: period === 'monthly' ? {
          weekly_analysis: !!data?.weekly_analysis,
          life_spheres: !!data?.life_spheres,
          trends: !!data?.trends,
          lunar_phases: !!data?.lunar_phases,
          planetary_transits: !!data?.planetary_transits,
          monthly_summary: !!data?.monthly_summary,
          daily_schedule: !!data?.daily_schedule
        } : null
      });
      setRouteData(prev => {
        const newData = { ...prev, [period]: data };
        console.log(`[${period}] Обновляем routeData:`, {
          period,
          hasData: !!newData[period],
          allKeys: Object.keys(newData),
          dataKeys: newData[period] ? Object.keys(newData[period]) : []
        });
        return newData;
      });
      setError(''); // Очищаем ошибку при успешной загрузке
    } catch (err) {
      console.error(`Ошибка загрузки ${period}:`, err);
      let errorMessage = 'Ошибка загрузки маршрута. Проверьте подключение к интернету.';
      
      if (err instanceof TypeError && err.message === 'Failed to fetch') {
        errorMessage = 'Не удалось подключиться к серверу. Проверьте подключение к интернету и убедитесь, что сервер запущен.';
        console.error('Network error - возможно, сервер недоступен или проблема с CORS');
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(prev => ({ ...prev, [period]: false }));
    }
  };

  useEffect(() => {
    if (user) {
      // Загружаем данные для активной закладки
      fetchRouteData(activeTab);
    }
  }, [user, activeTab]);

  const handleDateChange = (e) => {
    const newDate = e.target.value;
    setSelectedDate(newDate);
    fetchRouteData(activeTab, newDate);
  };

  const handleTabChange = (newTab) => {
    setActiveTab(newTab);
    if (!routeData[newTab]) {
      fetchRouteData(newTab);
    }
  };

  const getCurrentTime = () => {
    return currentTime.toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  // Обновление времени каждую секунду
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const isCurrentHour = (startTime, endTime) => {
    const now = new Date();
    const currentHour = now.getHours();
    const currentMinute = now.getMinutes();
    const currentTime = currentHour * 60 + currentMinute;

    if (startTime && endTime) {
      const [startHour, startMinute] = startTime.split(':').map(Number);
      const [endHour, endMinute] = endTime.split(':').map(Number);
      const start = startHour * 60 + startMinute;
      const end = endHour * 60 + endMinute;

      return currentTime >= start && currentTime < end;
    }
    return false;
  };

  const renderDailyView = () => {
    console.log('renderDailyView вызван, routeData:', routeData);
    const route = routeData.daily;
    console.log('route из routeData.daily:', route);
    if (!route) {
      console.log('⚠️ routeData пустой!');
      return null;
    }

    return (
      <>
        {/* Основная информация */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Calendar className="w-5 h-5 mr-2" />
              Обзор дня
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className={`text-center p-3 rounded-lg ${themeConfig.isDark ? 'bg-orange-500/20' : 'bg-orange-50'}`}>
                <div className={`text-lg font-semibold ${themeConfig.isDark ? 'text-orange-300' : 'text-orange-700'}`}>
                  {route.date}
                </div>
                <div className={`text-sm ${themeConfig.mutedText}`}>Дата</div>
              </div>
              <div className={`text-center p-3 rounded-lg ${themeConfig.isDark ? 'bg-blue-500/20' : 'bg-blue-50'}`}>
                <div className={`text-lg font-semibold ${themeConfig.isDark ? 'text-blue-300' : 'text-blue-700'}`}>
                  {route.city}
                </div>
                <div className={`text-sm ${themeConfig.mutedText}`}>Город</div>
              </div>
              <div className={`text-center p-3 rounded-lg ${themeConfig.isDark ? 'bg-purple-500/20' : 'bg-purple-50'}`}>
                <div className={`text-lg font-semibold ${themeConfig.isDark ? 'text-purple-300' : 'text-purple-700'}`}>
                  {route.daily_ruling_planet}
                </div>
                <div className={`text-sm ${themeConfig.mutedText}`}>Планета дня</div>
              </div>
              <div className={`text-center p-3 rounded-lg ${themeConfig.isDark ? 'bg-green-500/20' : 'bg-green-50'}`}>
                <div className={`text-lg font-semibold ${themeConfig.isDark ? 'text-green-300' : 'text-green-700'}`}>
                  {route.personal_birth_date}
                </div>
                <div className={`text-sm ${themeConfig.mutedText}`}>Ваша дата рождения</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Анализ дня - Новая секция */}
        {route.day_analysis && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5" />
                Персональный анализ дня
              </CardTitle>
              <CardDescription>
                Совместимость дня с вашими личными числами
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Общая оценка */}
                <div className={`p-6 rounded-xl border-2 ${
                  route.day_analysis.overall_score >= 60 ? getColorClasses('green').bg + ' ' + getColorClasses('green').border :
                  route.day_analysis.overall_score >= 40 ? getColorClasses('blue').bg + ' ' + getColorClasses('blue').border :
                  route.day_analysis.overall_score >= 20 ? getColorClasses('amber').bg + ' ' + getColorClasses('amber').border :
                  getColorClasses('red').bg + ' ' + getColorClasses('red').border
                }`}>
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className={`text-2xl font-bold ${themeConfig.text}`}>
                        {route.day_analysis.overall_rating} день
                      </h3>
                      <p className={`text-sm ${themeConfig.mutedText} mt-1`}>
                        Оценка совместимости: {route.day_analysis.overall_score}/100
                      </p>
                    </div>
                    <div className={`text-5xl font-bold ${
                      route.day_analysis.overall_score >= 60 ? getColorClasses('green').text :
                      route.day_analysis.overall_score >= 40 ? getColorClasses('blue').text :
                      route.day_analysis.overall_score >= 20 ? getColorClasses('amber').text :
                      getColorClasses('red').text
                    }`}>
                      {route.day_analysis.overall_score}
                    </div>
                  </div>
                  <p className={`text-base ${themeConfig.text} mb-4`}>
                    {route.day_analysis.overall_description}
                  </p>
                  <Button
                    onClick={() => {
                      setModalData(route.day_analysis);
                      setShowDetailsModal(true);
                    }}
                    className="mt-2 w-full bg-indigo-500 hover:bg-indigo-600 text-white"
                  >
                    <Info className="w-4 h-4 mr-2" />
                    Подробная расшифровка
                  </Button>
                </div>

                {/* Детали анализа */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className={`p-4 rounded-lg ${themeConfig.isDark ? 'bg-purple-500/20' : 'bg-purple-50'}`}>
                    <div className={`text-sm ${themeConfig.mutedText} mb-1`}>Число дня</div>
                    <div className={`text-2xl font-bold ${themeConfig.isDark ? 'text-purple-300' : 'text-purple-700'}`}>
                      {route.day_analysis.day_number}
                    </div>
                  </div>
                  <div className={`p-4 rounded-lg ${themeConfig.isDark ? 'bg-indigo-500/20' : 'bg-indigo-50'}`}>
                    <div className={`text-sm ${themeConfig.mutedText} mb-1`}>Управляющая планета</div>
                    <div className={`text-2xl font-bold ${themeConfig.isDark ? 'text-indigo-300' : 'text-indigo-700'}`}>
                      {route.day_analysis.ruling_planet}
                    </div>
                  </div>
                  <div className={`p-4 rounded-lg ${themeConfig.isDark ? 'bg-cyan-500/20' : 'bg-cyan-50'}`}>
                    <div className={`text-sm ${themeConfig.mutedText} mb-1`}>Число планеты</div>
                    <div className={`text-2xl font-bold ${themeConfig.isDark ? 'text-cyan-300' : 'text-cyan-700'}`}>
                      {route.day_analysis.ruling_number}
                    </div>
                  </div>
                  <div className={`p-4 rounded-lg ${themeConfig.isDark ? 'bg-teal-500/20' : 'bg-teal-50'}`}>
                    <div className={`text-sm ${themeConfig.mutedText} mb-1`}>Сила планеты в вашей карте</div>
                    <div className={`text-2xl font-bold ${themeConfig.isDark ? 'text-teal-300' : 'text-teal-700'}`}>
                      {route.day_analysis.planet_strength}
                    </div>
                  </div>
                </div>

                {/* Заметки о совместимости */}
                {route.day_analysis.compatibility_notes && route.day_analysis.compatibility_notes.length > 0 && (
                  <div className="space-y-2">
                    <h4 className={`font-semibold ${themeConfig.text} mb-3`}>Ключевые факторы:</h4>
                    {route.day_analysis.compatibility_notes.map((note, idx) => (
                      <div key={idx} className={`flex items-start gap-3 p-3 rounded-lg ${themeConfig.isDark ? 'bg-white/5' : 'bg-gray-50'}`}>
                        <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                        <span className={themeConfig.text}>{note}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* График почасовой энергии - Новая секция */}
        {route.hourly_energy && route.hourly_energy.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Почасовая энергия планет
              </CardTitle>
              <CardDescription>
                Уровень энергии каждого планетарного часа с учётом вашей личной карты
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* График */}
                <div className="h-80">
                  <Line
                    data={{
                      labels: route.hourly_energy.map(h => h.time.split(' - ')[0]),
                      datasets: [{
                        label: 'Уровень энергии',
                        data: route.hourly_energy.map(h => h.energy_level),
                        borderColor: themeConfig.isDark ? 'rgba(99, 102, 241, 1)' : 'rgba(79, 70, 229, 1)',
                        backgroundColor: themeConfig.isDark ? 'rgba(99, 102, 241, 0.1)' : 'rgba(79, 70, 229, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 6,
                        pointHoverRadius: 8,
                        pointBackgroundColor: themeConfig.isDark ? 'rgba(99, 102, 241, 1)' : 'rgba(79, 70, 229, 1)',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                      }]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          display: false
                        },
                        tooltip: {
                          backgroundColor: themeConfig.isDark ? 'rgba(30, 41, 59, 0.95)' : 'rgba(255, 255, 255, 0.95)',
                          titleColor: themeConfig.isDark ? '#fff' : '#000',
                          bodyColor: themeConfig.isDark ? '#cbd5e1' : '#64748b',
                          borderColor: themeConfig.isDark ? 'rgba(148, 163, 184, 0.2)' : 'rgba(203, 213, 225, 0.8)',
                          borderWidth: 1,
                          padding: 12,
                          displayColors: false,
                          callbacks: {
                            title: (items) => {
                              const idx = items[0].dataIndex;
                              return route.hourly_energy[idx].time;
                            },
                            label: (item) => {
                              const idx = item.dataIndex;
                              const hour = route.hourly_energy[idx];
                              return [
                                `Планета: ${hour.planet}`,
                                `Энергия: ${hour.energy_level}/10`,
                                `Сила в карте: ${hour.personal_strength}`,
                                `${hour.activity_type}`
                              ];
                            }
                          }
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          max: 10,
                          ticks: {
                            color: themeConfig.isDark ? '#94a3b8' : '#64748b',
                            stepSize: 2
                          },
                          grid: {
                            color: themeConfig.isDark ? 'rgba(148, 163, 184, 0.1)' : 'rgba(203, 213, 225, 0.3)'
                          }
                        },
                        x: {
                          ticks: {
                            color: themeConfig.isDark ? '#94a3b8' : '#64748b',
                            maxRotation: 45,
                            minRotation: 45
                          },
                          grid: {
                            display: false
                          }
                        }
                      }
                    }}
                  />
                </div>

                {/* Легенда энергий */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className={`p-3 rounded-lg ${getColorClasses('green').bg}`}>
                    <div className={`text-sm font-semibold ${getColorClasses('green').text} mb-1`}>
                      Высокая энергия (7-10)
                    </div>
                    <div className={`text-xs ${themeConfig.mutedText}`}>
                      Отличное время для активности
                    </div>
                  </div>
                  <div className={`p-3 rounded-lg ${getColorClasses('blue').bg}`}>
                    <div className={`text-sm font-semibold ${getColorClasses('blue').text} mb-1`}>
                      Умеренная энергия (4-6)
                    </div>
                    <div className={`text-xs ${themeConfig.mutedText}`}>
                      Подходит для повседневных дел
                    </div>
                  </div>
                  <div className={`p-3 rounded-lg ${getColorClasses('red').bg}`}>
                    <div className={`text-sm font-semibold ${getColorClasses('red').text} mb-1`}>
                      Низкая энергия (1-3)
                    </div>
                    <div className={`text-xs ${themeConfig.mutedText}`}>
                      Время для отдыха
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Лучшие часы для активности */}
        <Card>
          <CardHeader>
            <CardTitle className={`flex items-center ${getColorClasses('green').text}`}>
              <CheckCircle className="w-5 h-5 mr-2" />
              Лучшие часы для активности
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {route.best_activity_hours?.map((hour, index) => (
                <div key={index} className={`border-2 p-4 rounded-lg ${getColorClasses('green').bg} ${getColorClasses('green').border}`}>
                  <div className={`text-lg font-bold mb-1 ${getColorClasses('green').text}`}>
                    {hour}
                  </div>
                  <div className={`text-sm ${themeConfig.mutedText}`}>
                    Оптимальное время для важных дел
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Периоды, которых стоит избегать */}
        <Card>
          <CardHeader>
            <CardTitle className={`flex items-center ${getColorClasses('red').text}`}>
              <AlertTriangle className="w-5 h-5 mr-2" />
              Периоды, которых стоит избегать
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(route.avoid_periods || {}).map(([key, period]) => (
                <div key={key} className={`border-2 p-4 rounded-lg ${getColorClasses('red').bg} ${getColorClasses('red').border}`}>
                  <h3 className={`font-semibold mb-2 ${getColorClasses('red').text}`}>{period.name || key}</h3>
                  <div className={`text-lg font-bold mb-2 ${getColorClasses('red').text}`}>
                    {period.start} - {period.end}
                  </div>
                  <div className={`text-sm ${themeConfig.mutedText}`}>
                    {period.description}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Благоприятный период */}
        {route.favorable_period && (
          <Card>
            <CardHeader>
              <CardTitle className="text-green-700">✨ Особо благоприятный период</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-green-50 border-2 border-green-400 p-6 rounded-lg">
                <h3 className="text-xl font-bold text-green-800 mb-2">
                  {route.favorable_period.name}
                </h3>
                <div className="text-2xl font-bold text-green-900 mb-3">
                  {route.favorable_period.start} - {route.favorable_period.end}
                </div>
                <p className="text-green-700 mb-2">
                  {route.favorable_period.description}
                </p>
                <div className="text-sm text-green-600">
                  Продолжительность: {route.favorable_period.duration_minutes} минут
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Почасовой план дня - 24 часа с детальными советами */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Clock className="w-5 h-5 mr-2" />
              Почасовой план дня (24 часа)
            </CardTitle>
            <CardDescription>
              Полный планетарный гид с персонализированными советами. Нажмите на час для подробностей.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {route.hourly_guide_24h?.map((hour, index) => {
                const startTime = hour.time?.split(' - ')[0];
                const endTime = hour.time?.split(' - ')[1];
                const isCurrent = isCurrentHour(startTime, endTime);
                
                return (
                  <div
                    key={index}
                    onClick={() => {
                      setModalData(hour);
                      setShowDetailsModal(true);
                    }}
                    className={`p-4 rounded-lg border-2 cursor-pointer transition-all hover:scale-[1.02] ${
                      isCurrent 
                        ? themeConfig.isDark 
                          ? 'bg-blue-500/30 border-blue-400' 
                          : 'bg-blue-100 border-blue-400'
                        : hour.is_favorable 
                          ? themeConfig.isDark
                            ? 'bg-green-500/20 border-green-500/40'
                            : 'bg-green-50 border-green-300'
                          : themeConfig.isDark
                            ? 'bg-white/5 border-white/10 hover:bg-white/10'
                            : 'bg-gray-50 border-gray-300 hover:bg-gray-100'
                    }`}
                  >
                    <div className="flex justify-between items-center mb-2">
                      <div className="flex items-center gap-3">
                        <span className={`font-bold text-lg ${themeConfig.text}`}>Час {hour.hour}</span>
                        {isCurrent && (
                          <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded">
                            СЕЙЧАС
                          </span>
                        )}
                        {hour.is_favorable && !isCurrent && (
                          <span className="bg-green-500 text-white text-xs px-2 py-1 rounded">
                            БЛАГОПРИЯТНО
                          </span>
                        )}
                        {hour.period === 'night' && (
                          <span className={`text-xs px-2 py-1 rounded ${themeConfig.isDark ? 'bg-indigo-500/30 text-indigo-200' : 'bg-indigo-100 text-indigo-700'}`}>
                            🌙 Ночь
                          </span>
                        )}
                      </div>
                      <div className="text-right">
                        <div className={`font-semibold ${themeConfig.text}`}>{hour.time}</div>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center mb-2">
                      <div className={`font-medium ${themeConfig.text}`}>
                        {hour.planet_sanskrit || hour.planet}
                      </div>
                      <div className={`text-sm ${themeConfig.mutedText}`}>
                        Энергия: {hour.energy_level}/10
                      </div>
                    </div>
                    
                    {/* Краткая информация */}
                    <div className={`text-sm ${themeConfig.mutedText} mt-2`}>
                      {hour.general_recommendation}
                    </div>
                    
                    {/* Индикатор кликабельности */}
                    <div className={`text-xs ${themeConfig.mutedText} mt-2 flex items-center gap-1`}>
                      <Info className="w-3 h-3" />
                      Нажмите для подробностей
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* График планетарных энергий */}
        {route.planetary_energies && Object.keys(route.planetary_energies).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Энергия планет на день
              </CardTitle>
              <CardDescription>
                Уровень энергии каждой планеты с учётом вашей личной карты
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {Object.entries(route.planetary_energies).map(([planetKey, energy]) => {
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
                {route.total_energy !== undefined && (
                  <div className="mt-4 pt-4 border-t border-white/10">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-purple-200">
                        Общая энергия дня
                      </span>
                      <span className="text-xl font-bold text-purple-300">
                        {Math.round(route.total_energy / 9)}%
                      </span>
                    </div>
                    <div className="mt-2 w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500 bg-gradient-to-r from-purple-400 to-purple-600"
                        style={{
                          width: `${Math.min(100, Math.round(route.total_energy / 9))}%`,
                          boxShadow: '0 0 15px rgba(168, 85, 247, 0.6)'
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Персональные рекомендации */}
        {route.daily_recommendations && (
          <Card>
            <CardHeader>
              <CardTitle>💡 Персональные рекомендации</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {route.daily_recommendations.activities && (
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-blue-800 mb-2">Рекомендуемые активности:</h3>
                    <ul className="text-sm text-blue-700 space-y-1">
                      {route.daily_recommendations.activities.map((activity, idx) => (
                        <li key={idx}>• {activity}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {route.daily_recommendations.avoid && (
                  <div className="bg-red-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-red-800 mb-2">Чего следует избегать:</h3>
                    <ul className="text-sm text-red-700 space-y-1">
                      {route.daily_recommendations.avoid.map((item, idx) => (
                        <li key={idx}>• {item}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {route.daily_recommendations.colors && (
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-purple-800 mb-2">Благоприятные цвета дня:</h3>
                    <div className="flex flex-wrap gap-2">
                      {route.daily_recommendations.colors.map((color, idx) => (
                        <span key={idx} className="text-sm bg-purple-200 text-purple-800 px-2 py-1 rounded">
                          {color}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {route.daily_recommendations.planet_mantra && (
                  <div className="bg-orange-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-orange-800 mb-2">Мантра дня:</h3>
                    <div className="text-lg font-mono text-orange-700 text-center p-2 bg-orange-100 rounded">
                      {route.daily_recommendations.planet_mantra}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </>
    );
  };

  const renderWeeklyView = () => {
    const weeklyData = routeData.weekly;
    if (!weeklyData) return null;

    return (
      <>
        {/* Обзор недели */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <CalendarDays className="w-5 h-5 mr-2" />
              Планетарный обзор недели
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-lg font-semibold text-blue-700">
                  {weeklyData.daily_schedule?.length || 0}
                </div>
                <div className="text-sm text-gray-600">Дней в неделе</div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-lg font-semibold text-green-700">
                  {weeklyData.daily_schedule?.filter(d => d.day_type === 'favorable' || d.day_type === 'highly_favorable').length || 0}
                </div>
                <div className="text-sm text-gray-600">Благоприятных дней</div>
              </div>
              <div className="text-center p-3 bg-red-50 rounded-lg">
                <div className="text-lg font-semibold text-red-700">
                  {weeklyData.daily_schedule?.filter(d => d.day_type === 'challenging').length || 0}
                </div>
                <div className="text-sm text-gray-600">Сложных дней</div>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded-lg">
                <div className="text-lg font-semibold text-purple-700">
                  {weeklyData.start_date} — {weeklyData.end_date}
                </div>
                <div className="text-sm text-gray-600">Период</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* График планетарных энергий на неделю */}
        {weeklyData.daily_schedule && weeklyData.daily_schedule.some(d => d.planetary_energies) && (
          <Card className={themeConfig.isDark ? 'bg-gray-800 border-gray-700' : 'bg-white'}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Динамика энергии планет на неделю
              </CardTitle>
              <CardDescription>
                Изменение энергии каждой планеты в течение недели
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Управление видимостью планет */}
              <div className="flex flex-wrap items-center gap-2 mb-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setVisiblePlanets({
                      surya: false, chandra: false, mangal: false, budha: false,
                      guru: false, shukra: false, shani: false, rahu: false, ketu: false
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
                      surya: true, chandra: true, mangal: true, budha: true,
                      guru: true, shukra: true, shani: true, rahu: true, ketu: true
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
                          setVisiblePlanets(prev => ({ ...prev, [key]: !prev[key] }));
                        }}
                        className={`transition-all duration-200 ${
                          isActive 
                            ? `border-2 shadow-md font-semibold bg-gradient-to-br ${colorConfig.bg} ${colorConfig.border}` 
                            : 'opacity-40 border-opacity-30'
                        } ${
                          isHovered ? 'ring-4 ring-amber-400 ring-offset-2 scale-105 z-10' : ''
                        }`}
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

              {/* График */}
              <div 
                className={`${themeConfig.isDark ? 'bg-gray-900' : 'bg-gray-50'} rounded-lg p-6 border ${themeConfig.isDark ? 'border-gray-700' : 'border-gray-200'}`}
                onMouseMove={(e) => {
                  if (chartRef.current) {
                    const chartInstance = chartRef.current.chartInstance || chartRef.current;
                    if (chartInstance) {
                      const elements = getElementAtEvent(chartInstance, e.nativeEvent || e);
                      if (elements && elements.length > 0) {
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
                    labels: weeklyData.daily_schedule.map(d => {
                      const formattedDate = formatDate(d.date);
                      const dayOfWeek = getDayOfWeek(d.date);
                      return dayOfWeek ? `${formattedDate}\n${dayOfWeek}` : formattedDate;
                    }),
                    datasets: [
                      visiblePlanets.surya && {
                        label: 'Surya (☉)',
                        data: weeklyData.daily_schedule.map(d => d.planetary_energies?.surya || 0),
                        borderColor: getPlanetIndicatorColor(1),
                        backgroundColor: getPlanetIndicatorColor(1) + '1A',
                        borderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: getPlanetIndicatorColor(1),
                        pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff',
                        pointBorderWidth: 2,
                        tension: 0.4,
                        fill: false
                      },
                      visiblePlanets.chandra && {
                        label: 'Chandra (☽)',
                        data: weeklyData.daily_schedule.map(d => d.planetary_energies?.chandra || 0),
                        borderColor: getPlanetIndicatorColor(2),
                        backgroundColor: getPlanetIndicatorColor(2) + '1A',
                        borderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: getPlanetIndicatorColor(2),
                        pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff',
                        pointBorderWidth: 2,
                        tension: 0.4,
                        fill: false
                      },
                      visiblePlanets.guru && {
                        label: 'Guru (♃)',
                        data: weeklyData.daily_schedule.map(d => d.planetary_energies?.guru || 0),
                        borderColor: getPlanetIndicatorColor(3),
                        backgroundColor: getPlanetIndicatorColor(3) + '1A',
                        borderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: getPlanetIndicatorColor(3),
                        pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff',
                        pointBorderWidth: 2,
                        tension: 0.4,
                        fill: false
                      },
                      visiblePlanets.rahu && {
                        label: 'Rahu (☊)',
                        data: weeklyData.daily_schedule.map(d => d.planetary_energies?.rahu || 0),
                        borderColor: getPlanetIndicatorColor(4),
                        backgroundColor: getPlanetIndicatorColor(4) + '1A',
                        borderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: getPlanetIndicatorColor(4),
                        pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff',
                        pointBorderWidth: 2,
                        tension: 0.4,
                        fill: false
                      },
                      visiblePlanets.budha && {
                        label: 'Budha (☿)',
                        data: weeklyData.daily_schedule.map(d => d.planetary_energies?.budha || 0),
                        borderColor: getPlanetIndicatorColor(5),
                        backgroundColor: getPlanetIndicatorColor(5) + '1A',
                        borderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: getPlanetIndicatorColor(5),
                        pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff',
                        pointBorderWidth: 2,
                        tension: 0.4,
                        fill: false
                      },
                      visiblePlanets.shukra && {
                        label: 'Shukra (♀)',
                        data: weeklyData.daily_schedule.map(d => d.planetary_energies?.shukra || 0),
                        borderColor: getPlanetIndicatorColor(6),
                        backgroundColor: getPlanetIndicatorColor(6) + '1A',
                        borderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: getPlanetIndicatorColor(6),
                        pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff',
                        pointBorderWidth: 2,
                        tension: 0.4,
                        fill: false
                      },
                      visiblePlanets.ketu && {
                        label: 'Ketu (☋)',
                        data: weeklyData.daily_schedule.map(d => d.planetary_energies?.ketu || 0),
                        borderColor: getPlanetIndicatorColor(7),
                        backgroundColor: getPlanetIndicatorColor(7) + '1A',
                        borderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: getPlanetIndicatorColor(7),
                        pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff',
                        pointBorderWidth: 2,
                        tension: 0.4,
                        fill: false
                      },
                      visiblePlanets.shani && {
                        label: 'Shani (♄)',
                        data: weeklyData.daily_schedule.map(d => d.planetary_energies?.shani || 0),
                        borderColor: getPlanetIndicatorColor(8),
                        backgroundColor: getPlanetIndicatorColor(8) + '1A',
                        borderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: getPlanetIndicatorColor(8),
                        pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff',
                        pointBorderWidth: 2,
                        tension: 0.4,
                        fill: false
                      },
                      visiblePlanets.mangal && {
                        label: 'Mangal (♂)',
                        data: weeklyData.daily_schedule.map(d => d.planetary_energies?.mangal || 0),
                        borderColor: getPlanetIndicatorColor(9),
                        backgroundColor: getPlanetIndicatorColor(9) + '1A',
                        borderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: getPlanetIndicatorColor(9),
                        pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff',
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
                    plugins: {
                      legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                          usePointStyle: true,
                          padding: 15,
                          font: { size: 11 },
                          color: themeConfig.isDark ? '#e5e7eb' : '#374151'
                        }
                      },
                      tooltip: {
                        backgroundColor: themeConfig.isDark ? 'rgba(31, 41, 55, 0.95)' : 'rgba(255, 255, 255, 0.95)',
                        titleColor: themeConfig.isDark ? '#fff' : '#000',
                        bodyColor: themeConfig.isDark ? '#d1d5db' : '#4b5563',
                        borderColor: themeConfig.isDark ? 'rgba(75, 85, 99, 0.3)' : 'rgba(209, 213, 219, 0.8)',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true,
                        callbacks: {
                          label: (context) => {
                            const value = context.parsed.y;
                            const planetName = context.dataset.label;
                            return `${planetName}: ${value}% энергии`;
                          },
                          title: (tooltipItems) => {
                            if (tooltipItems && tooltipItems.length > 0) {
                              const dataIndex = tooltipItems[0].dataIndex;
                              const date = weeklyData.daily_schedule[dataIndex]?.date;
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
                          color: themeConfig.isDark ? '#9ca3af' : '#6b7280',
                          font: { size: 11 }
                        },
                        grid: {
                          color: themeConfig.isDark ? 'rgba(156, 163, 175, 0.1)' : 'rgba(203, 213, 225, 0.3)',
                          lineWidth: 1
                        }
                      },
                      x: {
                        ticks: {
                          color: themeConfig.isDark ? '#9ca3af' : '#6b7280',
                          font: { size: 11 },
                          maxRotation: 45,
                          minRotation: 45
                        },
                        grid: {
                          color: themeConfig.isDark ? 'rgba(156, 163, 175, 0.1)' : 'rgba(203, 213, 225, 0.3)',
                          lineWidth: 1
                        }
                      }
                    }
                  }}
                  height={400}
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Дни недели с энергиями */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {weeklyData.daily_schedule?.map((day, index) => (
            <Card key={index}>
              <CardHeader>
                <CardTitle className="text-lg">
                  {new Date(day.date).toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' })}
                </CardTitle>
                <CardDescription>
                  {day.ruling_planet} · {day.day_type_ru}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {day.planetary_energies && (
                  <div className="space-y-2">
                    <div className="text-sm font-semibold mb-2">Энергии планет:</div>
                    <div className="grid grid-cols-3 gap-2">
                      {Object.entries(day.planetary_energies).slice(0, 6).map(([planetKey, energy]) => {
                        const planetColor = getPlanetColor(planetKey.charAt(0).toUpperCase() + planetKey.slice(1));
                        return (
                          <div key={planetKey} className="text-center">
                            <div className="text-xs font-semibold" style={{ color: planetColor }}>
                              {planetKey.charAt(0).toUpperCase()}
                            </div>
                            <div className="text-xs font-bold" style={{ color: planetColor }}>
                              {Math.round(energy)}%
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    {day.total_energy !== undefined && (
                      <div className="mt-2 pt-2 border-t">
                        <div className="text-xs text-gray-600">Общая энергия:</div>
                        <div className="text-sm font-bold text-purple-600">
                          {Math.round(day.total_energy / 9)}%
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </>
    );
  };

  const renderMonthlyView = () => {
    const monthlyData = routeData.monthly;
    
    // Если данных нет, показываем заглушки
    if (!monthlyData) {
      return (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-center text-2xl">
                <CalendarDays className="w-6 h-6 mr-2" />
                Планетарный маршрут на месяц
              </CardTitle>
              <CardDescription className="text-center">
                Полный анализ месяца с недельными и дневными прогнозами
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Обзор месяца */}
                <Card>
                  <CardHeader>
                    <CardTitle>🌙 Обзор месяца</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2 text-sm">
                      <li>• Общая тематика месяца</li>
                      <li>• Ключевые планетарные периоды</li>
                      <li>• Благоприятные недели</li>
                      <li>• Критические точки</li>
                    </ul>
                  </CardContent>
                </Card>

                {/* Календарь месяца */}
                <Card>
                  <CardHeader>
                    <CardTitle>📆 Календарь месяца</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2 text-sm">
                      <li>• 4-5 недель с анализом</li>
                      <li>• Важные даты и события</li>
                      <li>• Лунные фазы и влияния</li>
                      <li>• Планетарные транзиты</li>
                    </ul>
                  </CardContent>
                </Card>

                {/* Сферы жизни */}
                <Card>
                  <CardHeader>
                    <CardTitle>💼 Сферы жизни</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2 text-sm">
                      <li>• Карьера и финансы</li>
                      <li>• Отношения и семья</li>
                      <li>• Здоровье и энергия</li>
                      <li>• Духовное развитие</li>
                    </ul>
                  </CardContent>
                </Card>

                {/* Тренды и прогнозы */}
                <Card>
                  <CardHeader>
                    <CardTitle>📈 Тренды и прогнозы</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2 text-sm">
                      <li>• Графики энергий месяца</li>
                      <li>• Оптимальное время для начинаний</li>
                      <li>• Периоды завершения проектов</li>
                      <li>• Рекомендации по планированию</li>
                    </ul>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </>
      );
    }

    return (
      <>
        {/* Обзор месяца */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <CalendarDays className="w-5 h-5 mr-2" />
              Планетарный обзор месяца
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-lg font-semibold text-blue-700">
                  {monthlyData.total_days}
                </div>
                <div className="text-sm text-gray-600">Дней в периоде</div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-lg font-semibold text-green-700">
                  {monthlyData.monthly_summary?.total_favorable_days || 0}
                </div>
                <div className="text-sm text-gray-600">Благоприятных дней</div>
              </div>
              <div className="text-center p-3 bg-red-50 rounded-lg">
                <div className="text-lg font-semibold text-red-700">
                  {monthlyData.monthly_summary?.total_challenging_days || 0}
                </div>
                <div className="text-sm text-gray-600">Сложных дней</div>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded-lg">
                <div className="text-lg font-semibold text-purple-700">
                  {monthlyData.monthly_summary?.recommendations?.most_active_planet || 'Солнце'}
                </div>
                <div className="text-sm text-gray-600">Активная планета</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Лучшие дни месяца */}
        {monthlyData.monthly_summary?.best_days?.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-green-700 flex items-center">
                <CheckCircle className="w-5 h-5 mr-2" />
                Лучшие дни для важных дел
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {(monthlyData.monthly_summary.best_days_detailed || monthlyData.monthly_summary.best_days || []).map((dayData, index) => {
                  const date = typeof dayData === 'string' ? dayData : dayData.date;
                  const energy = typeof dayData === 'object' ? dayData.energy : null;
                  const planet = typeof dayData === 'object' ? dayData.ruling_planet : null;
                  return (
                    <div key={index} className="text-center p-3 bg-green-50 border-2 border-green-300 rounded-lg">
                      <div className="font-semibold text-green-800">
                        {new Date(date).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })}
                      </div>
                      <div className="text-xs text-green-600">
                        {new Date(date).toLocaleDateString('ru-RU', { weekday: 'short' })}
                      </div>
                      {energy !== null && (
                        <div className="text-xs font-semibold text-green-700 mt-1">
                          {energy}%
                        </div>
                      )}
                      {planet && (
                        <div className="text-[10px] text-green-500 mt-1">
                          {planet}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Сложные дни месяца */}
        {monthlyData.monthly_summary?.challenging_days?.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-red-700 flex items-center">
                <AlertCircle className="w-5 h-5 mr-2" />
                Дни, требующие осторожности
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {(monthlyData.monthly_summary.challenging_days_detailed || monthlyData.monthly_summary.challenging_days || []).map((dayData, index) => {
                  const date = typeof dayData === 'string' ? dayData : dayData.date;
                  const energy = typeof dayData === 'object' ? dayData.energy : null;
                  const planet = typeof dayData === 'object' ? dayData.ruling_planet : null;
                  return (
                    <div key={index} className="text-center p-3 bg-red-50 border-2 border-red-300 rounded-lg">
                      <div className="font-semibold text-red-800">
                        {new Date(date).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })}
                      </div>
                      <div className="text-xs text-red-600">
                        {new Date(date).toLocaleDateString('ru-RU', { weekday: 'short' })}
                      </div>
                      {energy !== null && (
                        <div className="text-xs font-semibold text-red-700 mt-1">
                          {energy}%
                        </div>
                      )}
                      {planet && (
                        <div className="text-[10px] text-red-500 mt-1">
                          {planet}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* График планетарных энергий на месяц */}
        {monthlyData.daily_schedule && monthlyData.daily_schedule.some(d => d.planetary_energies) && (
          <Card className={themeConfig.isDark ? 'bg-gray-800 border-gray-700' : 'bg-white'}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Динамика энергии планет на месяц
              </CardTitle>
              <CardDescription>
                Изменение энергии каждой планеты в течение месяца
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Управление видимостью планет */}
              <div className="flex flex-wrap items-center gap-2 mb-4">
                <Button variant="outline" size="sm" onClick={() => setVisiblePlanets({ surya: false, chandra: false, mangal: false, budha: false, guru: false, shukra: false, shani: false, rahu: false, ketu: false })}>
                  Выключить все
                </Button>
                <Button variant="outline" size="sm" onClick={() => setVisiblePlanets({ surya: true, chandra: true, mangal: true, budha: true, guru: true, shukra: true, shani: true, rahu: true, ketu: true })}>
                  Включить все
                </Button>
                <div className="flex flex-wrap gap-2">
                  {Object.entries({ surya: { label: 'Surya (☉)', num: 1 }, chandra: { label: 'Chandra (☽)', num: 2 }, guru: { label: 'Guru (♃)', num: 3 }, rahu: { label: 'Rahu (☊)', num: 4 }, budha: { label: 'Budha (☿)', num: 5 }, shukra: { label: 'Shukra (♀)', num: 6 }, ketu: { label: 'Ketu (☋)', num: 7 }, shani: { label: 'Shani (♄)', num: 8 }, mangal: { label: 'Mangal (♂)', num: 9 } }).map(([key, { label, num }]) => {
                    const isActive = visiblePlanets[key];
                    const colorConfig = CELL_COLORS[num];
                    return (
                      <Button key={key} variant="outline" size="sm" onClick={() => setVisiblePlanets(prev => ({ ...prev, [key]: !prev[key] }))} className={`transition-all ${isActive ? `border-2 shadow-md font-semibold bg-gradient-to-br ${colorConfig.bg} ${colorConfig.border}` : 'opacity-40'}`}>
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: getPlanetIndicatorColor(num), opacity: isActive ? 1 : 0.4 }} />
                          <span className={isActive ? colorConfig.text : ''}>{label}</span>
                        </div>
                      </Button>
                    );
                  })}
                </div>
              </div>

              {/* График */}
              <div className={`${themeConfig.isDark ? 'bg-gray-900' : 'bg-gray-50'} rounded-lg p-6 border ${themeConfig.isDark ? 'border-gray-700' : 'border-gray-200'}`}>
                <Line
                  data={{
                    labels: monthlyData.daily_schedule.map(d => {
                      const formattedDate = formatDate(d.date);
                      const dayOfWeek = getDayOfWeek(d.date);
                      return dayOfWeek ? `${formattedDate}\n${dayOfWeek}` : formattedDate;
                    }),
                    datasets: [
                      visiblePlanets.surya && { label: 'Surya (☉)', data: monthlyData.daily_schedule.map(d => d.planetary_energies?.surya || 0), borderColor: getPlanetIndicatorColor(1), backgroundColor: getPlanetIndicatorColor(1) + '1A', borderWidth: 2, pointRadius: 2, pointHoverRadius: 4, pointBackgroundColor: getPlanetIndicatorColor(1), pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff', pointBorderWidth: 2, tension: 0.4, fill: false },
                      visiblePlanets.chandra && { label: 'Chandra (☽)', data: monthlyData.daily_schedule.map(d => d.planetary_energies?.chandra || 0), borderColor: getPlanetIndicatorColor(2), backgroundColor: getPlanetIndicatorColor(2) + '1A', borderWidth: 2, pointRadius: 2, pointHoverRadius: 4, pointBackgroundColor: getPlanetIndicatorColor(2), pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff', pointBorderWidth: 2, tension: 0.4, fill: false },
                      visiblePlanets.guru && { label: 'Guru (♃)', data: monthlyData.daily_schedule.map(d => d.planetary_energies?.guru || 0), borderColor: getPlanetIndicatorColor(3), backgroundColor: getPlanetIndicatorColor(3) + '1A', borderWidth: 2, pointRadius: 2, pointHoverRadius: 4, pointBackgroundColor: getPlanetIndicatorColor(3), pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff', pointBorderWidth: 2, tension: 0.4, fill: false },
                      visiblePlanets.rahu && { label: 'Rahu (☊)', data: monthlyData.daily_schedule.map(d => d.planetary_energies?.rahu || 0), borderColor: getPlanetIndicatorColor(4), backgroundColor: getPlanetIndicatorColor(4) + '1A', borderWidth: 2, pointRadius: 2, pointHoverRadius: 4, pointBackgroundColor: getPlanetIndicatorColor(4), pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff', pointBorderWidth: 2, tension: 0.4, fill: false },
                      visiblePlanets.budha && { label: 'Budha (☿)', data: monthlyData.daily_schedule.map(d => d.planetary_energies?.budha || 0), borderColor: getPlanetIndicatorColor(5), backgroundColor: getPlanetIndicatorColor(5) + '1A', borderWidth: 2, pointRadius: 2, pointHoverRadius: 4, pointBackgroundColor: getPlanetIndicatorColor(5), pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff', pointBorderWidth: 2, tension: 0.4, fill: false },
                      visiblePlanets.shukra && { label: 'Shukra (♀)', data: monthlyData.daily_schedule.map(d => d.planetary_energies?.shukra || 0), borderColor: getPlanetIndicatorColor(6), backgroundColor: getPlanetIndicatorColor(6) + '1A', borderWidth: 2, pointRadius: 2, pointHoverRadius: 4, pointBackgroundColor: getPlanetIndicatorColor(6), pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff', pointBorderWidth: 2, tension: 0.4, fill: false },
                      visiblePlanets.ketu && { label: 'Ketu (☋)', data: monthlyData.daily_schedule.map(d => d.planetary_energies?.ketu || 0), borderColor: getPlanetIndicatorColor(7), backgroundColor: getPlanetIndicatorColor(7) + '1A', borderWidth: 2, pointRadius: 2, pointHoverRadius: 4, pointBackgroundColor: getPlanetIndicatorColor(7), pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff', pointBorderWidth: 2, tension: 0.4, fill: false },
                      visiblePlanets.shani && { label: 'Shani (♄)', data: monthlyData.daily_schedule.map(d => d.planetary_energies?.shani || 0), borderColor: getPlanetIndicatorColor(8), backgroundColor: getPlanetIndicatorColor(8) + '1A', borderWidth: 2, pointRadius: 2, pointHoverRadius: 4, pointBackgroundColor: getPlanetIndicatorColor(8), pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff', pointBorderWidth: 2, tension: 0.4, fill: false },
                      visiblePlanets.mangal && { label: 'Mangal (♂)', data: monthlyData.daily_schedule.map(d => d.planetary_energies?.mangal || 0), borderColor: getPlanetIndicatorColor(9), backgroundColor: getPlanetIndicatorColor(9) + '1A', borderWidth: 2, pointRadius: 2, pointHoverRadius: 4, pointBackgroundColor: getPlanetIndicatorColor(9), pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff', pointBorderWidth: 2, tension: 0.4, fill: false }
                    ].filter(Boolean)
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'nearest', intersect: false },
                    plugins: {
                      legend: { display: true, position: 'bottom', labels: { usePointStyle: true, padding: 15, font: { size: 11 }, color: themeConfig.isDark ? '#e5e7eb' : '#374151' } },
                      tooltip: {
                        backgroundColor: themeConfig.isDark ? 'rgba(31, 41, 55, 0.95)' : 'rgba(255, 255, 255, 0.95)',
                        titleColor: themeConfig.isDark ? '#fff' : '#000',
                        bodyColor: themeConfig.isDark ? '#d1d5db' : '#4b5563',
                        callbacks: {
                          label: (context) => `${context.dataset.label}: ${context.parsed.y}% энергии`,
                          title: (tooltipItems) => {
                            if (tooltipItems && tooltipItems.length > 0) {
                              const dataIndex = tooltipItems[0].dataIndex;
                              const date = monthlyData.daily_schedule[dataIndex]?.date;
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
                      y: { beginAtZero: true, max: 100, ticks: { stepSize: 10, callback: (value) => `${value}%`, color: themeConfig.isDark ? '#9ca3af' : '#6b7280', font: { size: 11 } }, grid: { color: themeConfig.isDark ? 'rgba(156, 163, 175, 0.1)' : 'rgba(203, 213, 225, 0.3)' } },
                      x: { ticks: { color: themeConfig.isDark ? '#9ca3af' : '#6b7280', font: { size: 10 }, maxRotation: 45, minRotation: 45 }, grid: { color: themeConfig.isDark ? 'rgba(156, 163, 175, 0.1)' : 'rgba(203, 213, 225, 0.3)' } }
                    }
                  }}
                  height={400}
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Календарь месяца с планетарными влияниями */}
        <Card>
          <CardHeader>
            <CardTitle>📅 Календарь планетарных влияний</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-7 gap-2 mb-4">
              {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map(day => (
                <div key={day} className="text-center text-sm font-semibold text-gray-600 p-2">
                  {day}
                </div>
              ))}
            </div>
            <div className="grid grid-cols-7 gap-2">
              {monthlyData.daily_schedule?.map((day, index) => {
                const dayType = day.day_type || 'neutral';
                const avgEnergy = (day.avg_energy_per_planet !== null && day.avg_energy_per_planet !== undefined) ? day.avg_energy_per_planet : 0;
                const isFavorable = dayType === 'favorable' || dayType === 'highly_favorable' || avgEnergy >= 60;
                const isChallenging = dayType === 'challenging' || (avgEnergy > 0 && avgEnergy < 40);
                
                return (
                  <div 
                    key={index} 
                    className={`p-2 text-center border rounded-lg hover:bg-gray-50 min-h-[80px] flex flex-col justify-between ${
                      isFavorable ? 'bg-green-50 border-green-300' : 
                      isChallenging ? 'bg-red-50 border-red-300' : 
                      'bg-gray-50 border-gray-300'
                    }`}
                    title={`${day.date} - ${day.day_type_ru || 'Нейтральный'}${avgEnergy ? ` (${avgEnergy.toFixed(1)}%)` : ''}`}
                  >
                    <div className="text-sm font-semibold">
                      {new Date(day.date).getDate()}
                    </div>
                    <div className="text-[10px] text-gray-600 leading-tight break-words">
                      {day.ruling_planet?.split('(')[0]?.trim() || ''}
                    </div>
                    <div className="flex flex-col items-center gap-1 mt-1">
                      {avgEnergy > 0 && (
                        <div className={`text-[9px] font-semibold ${
                          isFavorable ? 'text-green-700' : 
                          isChallenging ? 'text-red-700' : 
                          'text-gray-600'
                        }`}>
                          {avgEnergy.toFixed(0)}%
                        </div>
                      )}
                      <div className="flex justify-center gap-1">
                        {isFavorable && (
                          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        )}
                        {isChallenging && (
                          <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="flex justify-center items-center gap-4 mt-4 text-xs text-gray-600">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span>Благоприятный день</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                <span>Сложный день</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Обзор месяца - Общая тематика и ключевые периоды */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Target className="w-5 h-5 mr-2" />
              🌙 Обзор месяца
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border-2 border-blue-200">
                <h3 className="font-semibold text-lg mb-2">Общая тематика месяца</h3>
                <p className="text-gray-700">{monthlyData.weekly_analysis?.overall_theme || monthlyData.monthly_summary?.recommendations?.advice || 'Гармония и баланс'}</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-green-50 rounded-lg">
                  <h4 className="font-semibold text-green-800 mb-2">Благоприятные недели</h4>
                  <div className="space-y-2">
                    {monthlyData.weekly_analysis?.favorable_weeks?.length > 0 ? (
                      monthlyData.weekly_analysis.favorable_weeks.map((week, idx) => (
                        <div key={idx} className="text-sm">
                          <span className="font-semibold">Неделя {week.week_number}:</span> {week.start_date} - {week.end_date}
                          <span className="ml-2 text-green-600">({week.avg_energy}% энергии)</span>
                        </div>
                      ))
                    ) : (
                      <div className="text-sm text-gray-500">Нет благоприятных недель</div>
                    )}
                  </div>
                </div>
                
                <div className="p-4 bg-red-50 rounded-lg">
                  <h4 className="font-semibold text-red-800 mb-2">Критические точки</h4>
                  <div className="space-y-2">
                    {monthlyData.weekly_analysis?.challenging_weeks?.length > 0 ? (
                      monthlyData.weekly_analysis.challenging_weeks.map((week, idx) => (
                        <div key={idx} className="text-sm">
                          <span className="font-semibold">Неделя {week.week_number}:</span> {week.start_date} - {week.end_date}
                          <span className="ml-2 text-red-600">({week.avg_energy}% энергии)</span>
                        </div>
                      ))
                    ) : (
                      <div className="text-sm text-gray-500">Нет критических недель</div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Анализ по неделям */}
        {monthlyData.weekly_analysis?.weeks && monthlyData.weekly_analysis.weeks.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>📆 Календарь месяца - Анализ по неделям</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {monthlyData.weekly_analysis.weeks.map((week, idx) => (
                  <div key={idx} className="p-4 border-2 rounded-lg bg-gradient-to-r from-gray-50 to-blue-50">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-bold text-lg">Неделя {week.week_number}</h3>
                        <p className="text-sm text-gray-600">{week.start_date} - {week.end_date}</p>
                        <p className="text-sm font-semibold text-blue-700 mt-1">{week.theme}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-purple-700">{week.avg_energy}%</div>
                        <div className="text-xs text-gray-600">Средняя энергия</div>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                      <div className="text-sm">
                        <span className="font-semibold">Доминирующая планета:</span> {week.dominant_planet}
                      </div>
                      <div className="text-sm">
                        <span className="font-semibold">Благоприятных дней:</span> {week.favorable_days_count}
                      </div>
                      <div className="text-sm">
                        <span className="font-semibold">Сложных дней:</span> {week.challenging_days_count}
                      </div>
                    </div>
                    
                    {week.key_periods && week.key_periods.length > 0 && (
                      <div className="mb-3">
                        <h4 className="font-semibold text-sm mb-2">Ключевые периоды:</h4>
                        <div className="space-y-1">
                          {week.key_periods.map((period, pIdx) => (
                            <div key={pIdx} className={`text-xs p-2 rounded ${
                              period.type === 'peak' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                              <span className="font-semibold">{period.date}:</span> {period.description}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {week.recommendations && week.recommendations.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-sm mb-2">Рекомендации:</h4>
                        <ul className="list-disc list-inside text-sm space-y-1">
                          {week.recommendations.map((rec, rIdx) => (
                            <li key={rIdx}>{rec}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Сферы жизни */}
        <Card>
          <CardHeader>
            <CardTitle>💼 Сферы жизни</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Карьера и финансы */}
              <div className="p-4 border-2 rounded-lg bg-gradient-to-br from-yellow-50 to-orange-50">
                <h3 className="font-bold text-lg mb-3 flex items-center">
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
                <div className="text-sm mb-3">
                  <span className="font-semibold">Средняя энергия:</span> {monthlyData.life_spheres?.career_finance?.avg_energy || 0}%
                </div>
                {monthlyData.life_spheres?.career_finance?.recommendations && monthlyData.life_spheres.career_finance.recommendations.length > 0 && (
                  <ul className="list-disc list-inside text-sm space-y-1">
                    {monthlyData.life_spheres.career_finance.recommendations.map((rec, idx) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Отношения и семья */}
              <div className="p-4 border-2 rounded-lg bg-gradient-to-br from-pink-50 to-rose-50">
                <h3 className="font-bold text-lg mb-3 flex items-center">
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
                <div className="text-sm mb-3">
                  <span className="font-semibold">Средняя энергия:</span> {monthlyData.life_spheres?.relationships_family?.avg_energy || 0}%
                </div>
                {monthlyData.life_spheres?.relationships_family?.recommendations && monthlyData.life_spheres.relationships_family.recommendations.length > 0 && (
                  <ul className="list-disc list-inside text-sm space-y-1">
                    {monthlyData.life_spheres.relationships_family.recommendations.map((rec, idx) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Здоровье и энергия */}
              <div className="p-4 border-2 rounded-lg bg-gradient-to-br from-green-50 to-emerald-50">
                <h3 className="font-bold text-lg mb-3 flex items-center">
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
                <div className="text-sm mb-3">
                  <span className="font-semibold">Средняя энергия:</span> {monthlyData.life_spheres?.health_energy?.avg_energy || 0}%
                </div>
                {monthlyData.life_spheres?.health_energy?.recommendations && monthlyData.life_spheres.health_energy.recommendations.length > 0 && (
                  <ul className="list-disc list-inside text-sm space-y-1">
                    {monthlyData.life_spheres.health_energy.recommendations.map((rec, idx) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Духовное развитие */}
              <div className="p-4 border-2 rounded-lg bg-gradient-to-br from-purple-50 to-indigo-50">
                <h3 className="font-bold text-lg mb-3 flex items-center">
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
                <div className="text-sm mb-3">
                  <span className="font-semibold">Средняя энергия:</span> {monthlyData.life_spheres?.spiritual_growth?.avg_energy || 0}%
                </div>
                {monthlyData.life_spheres?.spiritual_growth?.recommendations && monthlyData.life_spheres.spiritual_growth.recommendations.length > 0 && (
                  <ul className="list-disc list-inside text-sm space-y-1">
                    {monthlyData.life_spheres.spiritual_growth.recommendations.map((rec, idx) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Тренды и прогнозы */}
        <Card>
          <CardHeader>
            <CardTitle>📈 Тренды и прогнозы</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Тренд энергии */}
              <div className="p-4 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg border-2 border-blue-200">
                <h3 className="font-bold text-lg mb-2">Тренд энергии месяца</h3>
                <p className="text-gray-700">{monthlyData.trends?.trend_description || 'Стабильный уровень энергии в течение месяца'}</p>
              </div>

                {/* Оптимальное время для начинаний */}
                {monthlyData.trends.optimal_start_periods && monthlyData.trends.optimal_start_periods.length > 0 && (
                  <div>
                    <h3 className="font-bold text-lg mb-3 text-green-700">Оптимальное время для начинаний</h3>
                    <div className="space-y-3">
                      {monthlyData.trends.optimal_start_periods.map((period, idx) => (
                        <div key={idx} className="p-3 bg-green-50 border-2 border-green-300 rounded-lg">
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-semibold text-green-800">
                              {period.start_date} - {period.end_date}
                            </span>
                            <span className="text-sm text-green-600">
                              {period.days_count} дней · {period.avg_energy}% энергии
                            </span>
                          </div>
                          <p className="text-sm text-green-700">{period.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              {/* Периоды завершения проектов */}
              {monthlyData.trends?.completion_periods && monthlyData.trends.completion_periods.length > 0 && (
                <div>
                  <h3 className="font-bold text-lg mb-3 text-blue-700">Периоды завершения проектов</h3>
                  <div className="space-y-3">
                    {monthlyData.trends.completion_periods.map((period, idx) => (
                      <div key={idx} className="p-3 bg-blue-50 border-2 border-blue-300 rounded-lg">
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-semibold text-blue-800">
                            {period.start_date} - {period.end_date}
                          </span>
                          <span className="text-sm text-blue-600">
                            {period.days_count} дней
                          </span>
                        </div>
                        <p className="text-sm text-blue-700">{period.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Рекомендации по планированию */}
              {monthlyData.trends?.planning_recommendations && monthlyData.trends.planning_recommendations.length > 0 && (
                <div>
                  <h3 className="font-bold text-lg mb-3">Рекомендации по планированию</h3>
                  <ul className="list-disc list-inside space-y-2">
                    {monthlyData.trends.planning_recommendations.map((rec, idx) => (
                      <li key={idx} className="text-gray-700">{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Лунные фазы */}
        {monthlyData.lunar_phases && monthlyData.lunar_phases.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>🌙 Лунные фазы и влияния</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {monthlyData.lunar_phases.map((phase, idx) => (
                  <div key={idx} className="p-4 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg border-2 border-indigo-200">
                    <div className="text-3xl mb-2">{phase.phase_emoji}</div>
                    <div className="font-semibold text-indigo-800 mb-1">{phase.phase}</div>
                    <div className="text-sm text-gray-600 mb-2">{phase.date}</div>
                    <div className="text-xs text-indigo-700">{phase.influence}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Планетарные транзиты */}
        {monthlyData.planetary_transits && monthlyData.planetary_transits.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>⭐ Планетарные транзиты</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {monthlyData.planetary_transits.map((transit, idx) => (
                  <div key={idx} className={`p-3 rounded-lg border-2 ${
                    transit.type === 'peak' ? 'bg-green-50 border-green-300' : 'bg-red-50 border-red-300'
                  }`}>
                    <div className="flex justify-between items-center mb-1">
                      <span className={`font-semibold ${
                        transit.type === 'peak' ? 'text-green-800' : 'text-red-800'
                      }`}>
                        {transit.date} · {transit.planet}
                      </span>
                      <span className={`text-sm ${
                        transit.type === 'peak' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {transit.energy}% энергии
                      </span>
                    </div>
                    <p className={`text-sm ${
                      transit.type === 'peak' ? 'text-green-700' : 'text-red-700'
                    }`}>
                      {transit.description}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Месячные рекомендации */}
        <Card>
          <CardHeader>
            <CardTitle>💡 Стратегия месяца</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-blue-800">
                {monthlyData.monthly_summary?.recommendations?.advice || 'Используйте планетарные ритмы для максимальной эффективности.'}
              </p>
            </div>
          </CardContent>
        </Card>
      </>
    );
  };

  const renderQuarterlyView = () => {
    const quarterlyData = routeData.quarterly;
    if (!quarterlyData) return null;

    return (
      <>
        {/* Обзор квартала */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="w-5 h-5 mr-2" />
              Планетарная стратегия квартала
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-lg font-semibold text-blue-700">
                  {quarterlyData.total_weeks}
                </div>
                <div className="text-sm text-gray-600">Недель</div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-lg font-semibold text-green-700">
                  {quarterlyData.quarterly_summary?.total_best_days || 0}
                </div>
                <div className="text-sm text-gray-600">Лучших дней</div>
              </div>
              <div className="text-center p-3 bg-red-50 rounded-lg">
                <div className="text-lg font-semibold text-red-700">
                  {quarterlyData.quarterly_summary?.total_challenging_days || 0}
                </div>
                <div className="text-sm text-gray-600">Сложных дней</div>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded-lg">
                <div className="text-lg font-semibold text-purple-700">90</div>
                <div className="text-sm text-gray-600">Дней периода</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Лучшие недели */}
        {quarterlyData.quarterly_summary?.best_weeks?.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-green-700 flex items-center">
                <CheckCircle className="w-5 h-5 mr-2" />
                Лучшие недели для больших проектов
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {quarterlyData.quarterly_summary.best_weeks.map((week, index) => (
                  <div key={index} className="p-4 bg-green-50 border-2 border-green-300 rounded-lg">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-semibold text-green-800">
                          Неделя {week.week_number}
                        </div>
                        <div className="text-sm text-green-700">
                          {week.start_date} — {week.end_date}
                        </div>
                      </div>
                      <Badge className="bg-green-200 text-green-800">
                        {week.best_days?.length || 0} отличных дней
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* График планетарных энергий на квартал */}
        {quarterlyData.daily_schedule && quarterlyData.daily_schedule.some(d => d.planetary_energies) && (
          <Card className={themeConfig.isDark ? 'bg-gray-800 border-gray-700' : 'bg-white'}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Динамика энергии планет на квартал
              </CardTitle>
              <CardDescription>
                Изменение энергии каждой планеты в течение квартала
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Управление видимостью планет */}
              <div className="flex flex-wrap items-center gap-2 mb-4">
                <Button variant="outline" size="sm" onClick={() => setVisiblePlanets({ surya: false, chandra: false, mangal: false, budha: false, guru: false, shukra: false, shani: false, rahu: false, ketu: false })}>
                  Выключить все
                </Button>
                <Button variant="outline" size="sm" onClick={() => setVisiblePlanets({ surya: true, chandra: true, mangal: true, budha: true, guru: true, shukra: true, shani: true, rahu: true, ketu: true })}>
                  Включить все
                </Button>
                <div className="flex flex-wrap gap-2">
                  {Object.entries({ surya: { label: 'Surya (☉)', num: 1 }, chandra: { label: 'Chandra (☽)', num: 2 }, guru: { label: 'Guru (♃)', num: 3 }, rahu: { label: 'Rahu (☊)', num: 4 }, budha: { label: 'Budha (☿)', num: 5 }, shukra: { label: 'Shukra (♀)', num: 6 }, ketu: { label: 'Ketu (☋)', num: 7 }, shani: { label: 'Shani (♄)', num: 8 }, mangal: { label: 'Mangal (♂)', num: 9 } }).map(([key, { label, num }]) => {
                    const isActive = visiblePlanets[key];
                    const colorConfig = CELL_COLORS[num];
                    return (
                      <Button key={key} variant="outline" size="sm" onClick={() => setVisiblePlanets(prev => ({ ...prev, [key]: !prev[key] }))} className={`transition-all ${isActive ? `border-2 shadow-md font-semibold bg-gradient-to-br ${colorConfig.bg} ${colorConfig.border}` : 'opacity-40'}`}>
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: getPlanetIndicatorColor(num), opacity: isActive ? 1 : 0.4 }} />
                          <span className={isActive ? colorConfig.text : ''}>{label}</span>
                        </div>
                      </Button>
                    );
                  })}
                </div>
              </div>

              {/* График */}
              <div className={`${themeConfig.isDark ? 'bg-gray-900' : 'bg-gray-50'} rounded-lg p-6 border ${themeConfig.isDark ? 'border-gray-700' : 'border-gray-200'}`}>
                <Line
                  data={{
                    labels: quarterlyData.daily_schedule.map(d => {
                      const formattedDate = formatDate(d.date);
                      const dayOfWeek = getDayOfWeek(d.date);
                      return dayOfWeek ? `${formattedDate}\n${dayOfWeek}` : formattedDate;
                    }),
                    datasets: [
                      visiblePlanets.surya && { label: 'Surya (☉)', data: quarterlyData.daily_schedule.map(d => d.planetary_energies?.surya || 0), borderColor: getPlanetIndicatorColor(1), backgroundColor: getPlanetIndicatorColor(1) + '1A', borderWidth: 2, pointRadius: 1, pointHoverRadius: 3, pointBackgroundColor: getPlanetIndicatorColor(1), pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff', pointBorderWidth: 2, tension: 0.4, fill: false },
                      visiblePlanets.chandra && { label: 'Chandra (☽)', data: quarterlyData.daily_schedule.map(d => d.planetary_energies?.chandra || 0), borderColor: getPlanetIndicatorColor(2), backgroundColor: getPlanetIndicatorColor(2) + '1A', borderWidth: 2, pointRadius: 1, pointHoverRadius: 3, pointBackgroundColor: getPlanetIndicatorColor(2), pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff', pointBorderWidth: 2, tension: 0.4, fill: false },
                      visiblePlanets.guru && { label: 'Guru (♃)', data: quarterlyData.daily_schedule.map(d => d.planetary_energies?.guru || 0), borderColor: getPlanetIndicatorColor(3), backgroundColor: getPlanetIndicatorColor(3) + '1A', borderWidth: 2, pointRadius: 1, pointHoverRadius: 3, pointBackgroundColor: getPlanetIndicatorColor(3), pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff', pointBorderWidth: 2, tension: 0.4, fill: false },
                      visiblePlanets.rahu && { label: 'Rahu (☊)', data: quarterlyData.daily_schedule.map(d => d.planetary_energies?.rahu || 0), borderColor: getPlanetIndicatorColor(4), backgroundColor: getPlanetIndicatorColor(4) + '1A', borderWidth: 2, pointRadius: 1, pointHoverRadius: 3, pointBackgroundColor: getPlanetIndicatorColor(4), pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff', pointBorderWidth: 2, tension: 0.4, fill: false },
                      visiblePlanets.budha && { label: 'Budha (☿)', data: quarterlyData.daily_schedule.map(d => d.planetary_energies?.budha || 0), borderColor: getPlanetIndicatorColor(5), backgroundColor: getPlanetIndicatorColor(5) + '1A', borderWidth: 2, pointRadius: 1, pointHoverRadius: 3, pointBackgroundColor: getPlanetIndicatorColor(5), pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff', pointBorderWidth: 2, tension: 0.4, fill: false },
                      visiblePlanets.shukra && { label: 'Shukra (♀)', data: quarterlyData.daily_schedule.map(d => d.planetary_energies?.shukra || 0), borderColor: getPlanetIndicatorColor(6), backgroundColor: getPlanetIndicatorColor(6) + '1A', borderWidth: 2, pointRadius: 1, pointHoverRadius: 3, pointBackgroundColor: getPlanetIndicatorColor(6), pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff', pointBorderWidth: 2, tension: 0.4, fill: false },
                      visiblePlanets.ketu && { label: 'Ketu (☋)', data: quarterlyData.daily_schedule.map(d => d.planetary_energies?.ketu || 0), borderColor: getPlanetIndicatorColor(7), backgroundColor: getPlanetIndicatorColor(7) + '1A', borderWidth: 2, pointRadius: 1, pointHoverRadius: 3, pointBackgroundColor: getPlanetIndicatorColor(7), pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff', pointBorderWidth: 2, tension: 0.4, fill: false },
                      visiblePlanets.shani && { label: 'Shani (♄)', data: quarterlyData.daily_schedule.map(d => d.planetary_energies?.shani || 0), borderColor: getPlanetIndicatorColor(8), backgroundColor: getPlanetIndicatorColor(8) + '1A', borderWidth: 2, pointRadius: 1, pointHoverRadius: 3, pointBackgroundColor: getPlanetIndicatorColor(8), pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff', pointBorderWidth: 2, tension: 0.4, fill: false },
                      visiblePlanets.mangal && { label: 'Mangal (♂)', data: quarterlyData.daily_schedule.map(d => d.planetary_energies?.mangal || 0), borderColor: getPlanetIndicatorColor(9), backgroundColor: getPlanetIndicatorColor(9) + '1A', borderWidth: 2, pointRadius: 1, pointHoverRadius: 3, pointBackgroundColor: getPlanetIndicatorColor(9), pointBorderColor: themeConfig.isDark ? '#1f2937' : '#fff', pointBorderWidth: 2, tension: 0.4, fill: false }
                    ].filter(Boolean)
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'nearest', intersect: false },
                    plugins: {
                      legend: { display: true, position: 'bottom', labels: { usePointStyle: true, padding: 15, font: { size: 11 }, color: themeConfig.isDark ? '#e5e7eb' : '#374151' } },
                      tooltip: {
                        backgroundColor: themeConfig.isDark ? 'rgba(31, 41, 55, 0.95)' : 'rgba(255, 255, 255, 0.95)',
                        titleColor: themeConfig.isDark ? '#fff' : '#000',
                        bodyColor: themeConfig.isDark ? '#d1d5db' : '#4b5563',
                        callbacks: {
                          label: (context) => `${context.dataset.label}: ${context.parsed.y}% энергии`,
                          title: (tooltipItems) => {
                            if (tooltipItems && tooltipItems.length > 0) {
                              const dataIndex = tooltipItems[0].dataIndex;
                              const date = quarterlyData.daily_schedule[dataIndex]?.date;
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
                      y: { beginAtZero: true, max: 100, ticks: { stepSize: 10, callback: (value) => `${value}%`, color: themeConfig.isDark ? '#9ca3af' : '#6b7280', font: { size: 11 } }, grid: { color: themeConfig.isDark ? 'rgba(156, 163, 175, 0.1)' : 'rgba(203, 213, 225, 0.3)' } },
                      x: { ticks: { color: themeConfig.isDark ? '#9ca3af' : '#6b7280', font: { size: 9 }, maxRotation: 45, minRotation: 45 }, grid: { color: themeConfig.isDark ? 'rgba(156, 163, 175, 0.1)' : 'rgba(203, 213, 225, 0.3)' } }
                    }
                  }}
                  height={400}
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Недельный обзор */}
        <Card>
          <CardHeader>
            <CardTitle>📊 Обзор по неделям</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {quarterlyData.weekly_schedule?.map((week, index) => (
                <div key={index} className="p-4 border rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <div>
                      <div className="font-semibold">Неделя {week.week_number}</div>
                      <div className="text-sm text-gray-600">
                        {week.start_date} — {week.end_date}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {week.best_days?.length > 0 && (
                        <Badge variant="success" className="bg-green-200 text-green-800">
                          {week.best_days.length} хороших
                        </Badge>
                      )}
                      {week.challenging_days?.length > 0 && (
                        <Badge variant="destructive" className="bg-red-200 text-red-800">
                          {week.challenging_days.length} сложных
                        </Badge>
                      )}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-7 gap-1">
                    {week.days?.map((day, dayIndex) => (
                      <div 
                        key={dayIndex} 
                        className={`p-2 text-center text-xs rounded ${
                          day.favorable_rating >= 3 ? 'bg-green-100 text-green-800' :
                          day.favorable_rating < 2 ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {new Date(day.date).getDate()}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Квартальная стратегия */}
        {quarterlyData.quarterly_summary?.quarterly_advice && (
          <Card>
            <CardHeader>
              <CardTitle>🎯 Стратегия квартала</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {quarterlyData.quarterly_summary.quarterly_advice.focus_weeks?.length > 0 && (
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <h3 className="font-semibold text-blue-800 mb-2">Недели для фокуса:</h3>
                    <p className="text-sm text-blue-700">
                      Недели {quarterlyData.quarterly_summary.quarterly_advice.focus_weeks.join(', ')} — 
                      идеальное время для запуска новых проектов и важных решений.
                    </p>
                  </div>
                )}
                
                {quarterlyData.quarterly_summary.quarterly_advice.rest_weeks?.length > 0 && (
                  <div className="p-4 bg-orange-50 rounded-lg">
                    <h3 className="font-semibold text-orange-800 mb-2">Недели для отдыха:</h3>
                    <p className="text-sm text-orange-700">
                      Недели {quarterlyData.quarterly_summary.quarterly_advice.rest_weeks.join(', ')} — 
                      время для восстановления, планирования и подготовки.
                    </p>
                  </div>
                )}

                <div className="p-4 bg-purple-50 rounded-lg">
                  <h3 className="font-semibold text-purple-800 mb-2">Общая стратегия:</h3>
                  <p className="text-sm text-purple-700">
                    {quarterlyData.quarterly_summary.quarterly_advice.strategy}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </>
    );
  };

  if (!user) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardContent className="p-6">
          <p className="text-center text-gray-600">
            Войдите в аккаунт для доступа к планетарному маршруту
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Заголовок */}
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl text-center">🗺️ Планетарный маршрут жизни</CardTitle>
          <CardDescription className="text-center">
            Персональное планирование активности по ведическим планетарным циклам
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4 items-center justify-center">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Дата:</label>
              <Input
                type="date"
                value={selectedDate}
                onChange={handleDateChange}
                className="w-auto"
              />
            </div>
            <div className="text-sm text-gray-600">
              Текущее время: {getCurrentTime()}
            </div>
            <Button onClick={() => fetchRouteData(activeTab)} disabled={loading[activeTab]}>
              Обновить данные
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Закладки */}
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="daily" className="flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            День
          </TabsTrigger>
          <TabsTrigger value="weekly" className="flex items-center gap-2">
            <CalendarDays className="w-4 h-4" />
            Неделя
          </TabsTrigger>
          <TabsTrigger value="monthly" className="flex items-center gap-2">
            <CalendarDays className="w-4 h-4" />
            Месяц
          </TabsTrigger>
          <TabsTrigger value="quarterly" className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Квартал
          </TabsTrigger>
        </TabsList>

        <TabsContent value="daily" className="space-y-6">
          {loading.daily && (
            <Card>
              <CardContent className="p-6">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Составляем дневной маршрут...</p>
                </div>
              </CardContent>
            </Card>
          )}
          {renderDailyView()}
        </TabsContent>

        <TabsContent value="weekly" className="space-y-6">
          {loading.weekly && (
            <Card>
              <CardContent className="p-6">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Составляем недельный маршрут...</p>
                </div>
              </CardContent>
            </Card>
          )}
          {renderWeeklyView()}
        </TabsContent>

        <TabsContent value="monthly" className="space-y-6">
          {loading.monthly && (
            <Card>
              <CardContent className="p-6">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Составляем месячный план...</p>
                </div>
              </CardContent>
            </Card>
          )}
          {renderMonthlyView()}
        </TabsContent>

        <TabsContent value="quarterly" className="space-y-6">
          {loading.quarterly && (
            <Card>
              <CardContent className="p-6">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Составляем квартальную стратегию...</p>
                </div>
              </CardContent>
            </Card>
          )}
          {renderQuarterlyView()}
        </TabsContent>
      </Tabs>

      {error && (
        <Card>
          <CardContent className="p-6">
            <div className="text-center text-red-600">
              <p>{error}</p>
              <Button onClick={() => fetchRouteData(activeTab)} className="mt-2">
                Попробовать снова
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Модальное окно с детальной расшифровкой */}
      <Dialog open={showDetailsModal} onOpenChange={setShowDetailsModal}>
        <DialogContent className={`max-w-4xl max-h-[90vh] overflow-y-auto ${themeConfig.card}`}>
          <DialogHeader>
            <DialogTitle className={`text-2xl font-bold ${themeConfig.text} flex items-center gap-2`}>
              <Sparkles className="w-6 h-6" />
              {modalData?.hour ? `Час ${modalData.hour}: ${modalData.planet_sanskrit || modalData.planet || 'Планета'}` : (modalData ? 'Детальная расшифровка планетарного анализа' : 'Информация')}
            </DialogTitle>
            <DialogDescription className={themeConfig.mutedText}>
              {modalData?.hour ? `${modalData.time || ''} - Персонализированные советы` : (modalData ? 'Полный анализ совместимости дня с вашей личной нумерологической картой' : '')}
            </DialogDescription>
          </DialogHeader>

          {modalData?.hour ? (
            // Модальное окно для часа
            <div className="space-y-6 mt-4">
              {/* Основная информация о часе */}
              <div className={`p-6 rounded-xl border-2 ${
                modalData.energy_level >= 7 ? getColorClasses('green').bg + ' ' + getColorClasses('green').border :
                modalData.energy_level >= 5 ? getColorClasses('blue').bg + ' ' + getColorClasses('blue').border :
                getColorClasses('gray').bg + ' ' + getColorClasses('gray').border
              }`}>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className={`text-3xl font-bold ${themeConfig.text}`}>
                      {modalData.planet_sanskrit || modalData.planet}
                    </h3>
                    <p className={`text-lg ${themeConfig.mutedText} mt-2`}>
                      {modalData.time}
                    </p>
                  </div>
                  <div className={`text-6xl font-bold ${
                    modalData.energy_level >= 7 ? getColorClasses('green').text :
                    modalData.energy_level >= 5 ? getColorClasses('blue').text :
                    getColorClasses('gray').text
                  }`}>
                    {modalData.energy_level}/10
                  </div>
                </div>
                <p className={`text-lg ${themeConfig.text}`}>
                  {modalData.general_recommendation}
                </p>
              </div>

              {/* Лучшие активности */}
              {modalData.best_activities && modalData.best_activities.length > 0 && (
                <div className={`p-6 rounded-lg ${getColorClasses('green').bg}`}>
                  <h4 className={`text-xl font-bold ${themeConfig.text} mb-4`}>✅ Рекомендуемые активности</h4>
                  <ul className={`space-y-2 ${themeConfig.text}`}>
                    {modalData.best_activities.map((activity, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span>•</span>
                        <span>{activity}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Чего избегать */}
              {modalData.avoid_activities && modalData.avoid_activities.length > 0 && (
                <div className={`p-6 rounded-lg ${getColorClasses('red').bg}`}>
                  <h4 className={`text-xl font-bold ${themeConfig.text} mb-4`}>❌ Чего следует избегать</h4>
                  <ul className={`space-y-2 ${themeConfig.text}`}>
                    {modalData.avoid_activities.map((activity, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span>•</span>
                        <span>{activity}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Персонализированные советы */}
              {modalData.personalized_advice && modalData.personalized_advice.length > 0 && (
                <div className={`p-6 rounded-lg ${themeConfig.surface}`}>
                  <h4 className={`text-xl font-bold ${themeConfig.text} mb-4 flex items-center gap-2`}>
                    <Sparkles className="w-5 h-5" />
                    Персональные советы для вас
                  </h4>
                  <div className={`space-y-3 ${themeConfig.text}`}>
                    {modalData.personalized_advice.map((advice, idx) => (
                      <div key={idx} className={`p-3 rounded-lg ${themeConfig.isDark ? 'bg-white/5' : 'bg-gray-50'}`}>
                        {advice}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Информация о силе планеты */}
              <div className={`p-6 rounded-lg ${themeConfig.surface}`}>
                <h4 className={`text-xl font-bold ${themeConfig.text} mb-4`}>💪 Ваша сила планеты</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className={`p-4 rounded-lg ${themeConfig.isDark ? 'bg-purple-500/20' : 'bg-purple-50'}`}>
                    <div className={`text-sm ${themeConfig.mutedText} mb-1`}>Сила в карте</div>
                    <div className={`text-3xl font-bold ${themeConfig.isDark ? 'text-purple-300' : 'text-purple-700'}`}>
                      {modalData.personal_strength}
                      {modalData.personal_strength >= 5 && ' 💪'}
                      {modalData.personal_strength === 0 && ' ⚠️'}
                    </div>
                  </div>
                  <div className={`p-4 rounded-lg ${themeConfig.isDark ? 'bg-indigo-500/20' : 'bg-indigo-50'}`}>
                    <div className={`text-sm ${themeConfig.mutedText} mb-1`}>Тип активности</div>
                    <div className={`text-lg font-bold ${themeConfig.isDark ? 'text-indigo-300' : 'text-indigo-700'}`}>
                      {modalData.activity_type}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : modalData ? (
            <div className="space-y-6 mt-4">
              {/* Общая оценка */}
              <div className={`p-6 rounded-xl border-2 ${
                modalData.overall_score >= 80 ? getColorClasses('green').bg + ' ' + getColorClasses('green').border :
                modalData.overall_score >= 65 ? getColorClasses('green').bg + ' ' + getColorClasses('green').border :
                modalData.overall_score >= 50 ? getColorClasses('blue').bg + ' ' + getColorClasses('blue').border :
                modalData.overall_score >= 35 ? getColorClasses('gray').bg + ' ' + getColorClasses('gray').border :
                getColorClasses('red').bg + ' ' + getColorClasses('red').border
              }`}>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className={`text-3xl font-bold ${themeConfig.text}`}>
                      {modalData.overall_rating} день
                    </h3>
                    <p className={`text-lg ${themeConfig.mutedText} mt-2`}>
                      Оценка совместимости: {modalData.overall_score}/100
                    </p>
                  </div>
                  <div className={`text-6xl font-bold ${
                    modalData.overall_score >= 65 ? getColorClasses('green').text :
                    modalData.overall_score >= 50 ? getColorClasses('blue').text :
                    modalData.overall_score >= 35 ? getColorClasses('gray').text :
                    getColorClasses('red').text
                  }`}>
                    {modalData.overall_score}
                  </div>
                </div>
                <p className={`text-lg ${themeConfig.text}`}>
                  {modalData.overall_description}
                </p>
              </div>

              {/* Ваши личные числа */}
              {modalData.user_planets && (
                <div className={`p-6 rounded-lg ${themeConfig.surface}`}>
                  <h4 className={`text-xl font-bold ${themeConfig.text} mb-4 flex items-center gap-2`}>
                    <Target className="w-5 h-5" />
                    Ваши личные числа
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className={`p-4 rounded-lg ${themeConfig.isDark ? 'bg-purple-500/20' : 'bg-purple-50'}`}>
                      <div className={`text-sm ${themeConfig.mutedText} mb-1`}>Число Души</div>
                      <div className={`text-2xl font-bold ${themeConfig.isDark ? 'text-purple-300' : 'text-purple-700'}`}>
                        {modalData.user_planets.soul.number}
                      </div>
                      {modalData.user_planets.soul.planet && (
                        <div className={`text-sm ${themeConfig.mutedText} mt-1`}>
                          Планета: {modalData.user_planets.soul.planet}
                        </div>
                      )}
                    </div>
                    <div className={`p-4 rounded-lg ${themeConfig.isDark ? 'bg-indigo-500/20' : 'bg-indigo-50'}`}>
                      <div className={`text-sm ${themeConfig.mutedText} mb-1`}>Число Судьбы</div>
                      <div className={`text-2xl font-bold ${themeConfig.isDark ? 'text-indigo-300' : 'text-indigo-700'}`}>
                        {modalData.user_planets.destiny.number}
                      </div>
                      {modalData.user_planets.destiny.planet && (
                        <div className={`text-sm ${themeConfig.mutedText} mt-1`}>
                          Планета: {modalData.user_planets.destiny.planet}
                        </div>
                      )}
                    </div>
                    <div className={`p-4 rounded-lg ${themeConfig.isDark ? 'bg-cyan-500/20' : 'bg-cyan-50'}`}>
                      <div className={`text-sm ${themeConfig.mutedText} mb-1`}>Число Ума</div>
                      <div className={`text-2xl font-bold ${themeConfig.isDark ? 'text-cyan-300' : 'text-cyan-700'}`}>
                        {modalData.user_planets.mind.number}
                      </div>
                      {modalData.user_planets.mind.planet && (
                        <div className={`text-sm ${themeConfig.mutedText} mt-1`}>
                          Планета: {modalData.user_planets.mind.planet}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Планета дня */}
              <div className={`p-6 rounded-lg ${themeConfig.surface}`}>
                <h4 className={`text-xl font-bold ${themeConfig.text} mb-4`}>
                  Планета дня
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className={`p-4 rounded-lg ${themeConfig.isDark ? 'bg-orange-500/20' : 'bg-orange-50'}`}>
                    <div className={`text-sm ${themeConfig.mutedText} mb-1`}>Управляющая планета</div>
                    <div className={`text-2xl font-bold ${themeConfig.isDark ? 'text-orange-300' : 'text-orange-700'}`}>
                      {modalData.ruling_planet}
                    </div>
                  </div>
                  <div className={`p-4 rounded-lg ${themeConfig.isDark ? 'bg-amber-500/20' : 'bg-amber-50'}`}>
                    <div className={`text-sm ${themeConfig.mutedText} mb-1`}>Число планеты</div>
                    <div className={`text-2xl font-bold ${themeConfig.isDark ? 'text-amber-300' : 'text-amber-700'}`}>
                      {modalData.ruling_number}
                    </div>
                  </div>
                  <div className={`p-4 rounded-lg ${themeConfig.isDark ? 'bg-teal-500/20' : 'bg-teal-50'}`}>
                    <div className={`text-sm ${themeConfig.mutedText} mb-1`}>Сила в вашей карте</div>
                    <div className={`text-2xl font-bold ${themeConfig.isDark ? 'text-teal-300' : 'text-teal-700'}`}>
                      {modalData.planet_strength}
                      {modalData.planet_strength >= 4 && ' 💪'}
                      {modalData.planet_strength === 0 && ' ⚠️'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Ваше окружение */}
              {modalData.user_environment && (
                <div className={`p-6 rounded-lg ${themeConfig.surface}`}>
                  <h4 className={`text-xl font-bold ${themeConfig.text} mb-4 flex items-center gap-2`}>
                    <Activity className="w-5 h-5" />
                    Влияние вашего окружения
                  </h4>
                  <div className="space-y-4">
                    {modalData.user_environment.name && modalData.user_environment.name.text && (
                      <div className={`p-4 rounded-lg ${themeConfig.isDark ? 'bg-pink-500/20' : 'bg-pink-50'} border-l-4 ${themeConfig.isDark ? 'border-pink-500' : 'border-pink-400'}`}>
                        <div className="flex justify-between items-center">
                          <div>
                            <div className={`text-sm ${themeConfig.mutedText} mb-1`}>📝 Ваше имя</div>
                            <div className={`font-semibold ${themeConfig.text}`}>{modalData.user_environment.name.text}</div>
                          </div>
                          <div className="text-right">
                            <div className={`text-2xl font-bold ${themeConfig.isDark ? 'text-pink-300' : 'text-pink-700'}`}>
                              {modalData.user_environment.name.number}
                            </div>
                            {modalData.user_environment.name.planet && (
                              <div className={`text-sm ${themeConfig.mutedText}`}>
                                {modalData.user_environment.name.planet}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {modalData.user_environment.address && modalData.user_environment.address.text && (
                      <div className={`p-4 rounded-lg ${themeConfig.isDark ? 'bg-emerald-500/20' : 'bg-emerald-50'} border-l-4 ${themeConfig.isDark ? 'border-emerald-500' : 'border-emerald-400'}`}>
                        <div className="flex justify-between items-center">
                          <div>
                            <div className={`text-sm ${themeConfig.mutedText} mb-1`}>🏠 Ваш адрес</div>
                            <div className={`font-semibold ${themeConfig.text}`}>{modalData.user_environment.address.text}</div>
                          </div>
                          <div className="text-right">
                            <div className={`text-2xl font-bold ${themeConfig.isDark ? 'text-emerald-300' : 'text-emerald-700'}`}>
                              {modalData.user_environment.address.number}
                            </div>
                            {modalData.user_environment.address.planet && (
                              <div className={`text-sm ${themeConfig.mutedText}`}>
                                {modalData.user_environment.address.planet}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {modalData.user_environment.car && modalData.user_environment.car.text && (
                      <div className={`p-4 rounded-lg ${themeConfig.isDark ? 'bg-sky-500/20' : 'bg-sky-50'} border-l-4 ${themeConfig.isDark ? 'border-sky-500' : 'border-sky-400'}`}>
                        <div className="flex justify-between items-center">
                          <div>
                            <div className={`text-sm ${themeConfig.mutedText} mb-1`}>🚗 Ваш автомобиль</div>
                            <div className={`font-semibold ${themeConfig.text}`}>{modalData.user_environment.car.text}</div>
                          </div>
                          <div className="text-right">
                            <div className={`text-2xl font-bold ${themeConfig.isDark ? 'text-sky-300' : 'text-sky-700'}`}>
                              {modalData.user_environment.car.number}
                            </div>
                            {modalData.user_environment.car.planet && (
                              <div className={`text-sm ${themeConfig.mutedText}`}>
                                {modalData.user_environment.car.planet}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                  <div className={`mt-4 p-3 rounded-lg ${themeConfig.isDark ? 'bg-white/5' : 'bg-gray-50'}`}>
                    <p className={`text-sm ${themeConfig.mutedText}`}>
                      💡 Эти элементы вашего окружения также влияют на совместимость дня и учитываются в общей оценке
                    </p>
                  </div>
                </div>
              )}

              {/* Детальный анализ совместимости */}
              {modalData.compatibility_notes && modalData.compatibility_notes.length > 0 && (
                <div className={`p-6 rounded-lg ${themeConfig.surface}`}>
                  <h4 className={`text-xl font-bold ${themeConfig.text} mb-4 flex items-center gap-2`}>
                    <CheckCircle className="w-5 h-5" />
                    Ключевые факторы совместимости
                  </h4>
                  <div className="space-y-3">
                    {modalData.compatibility_notes.map((note, idx) => (
                      <div 
                        key={idx} 
                        className={`p-4 rounded-lg border-l-4 ${
                          note.includes('ИДЕАЛЬНЫЙ') || note.includes('🌟') 
                            ? themeConfig.isDark 
                              ? 'bg-green-500/20 border-green-500' 
                              : 'bg-green-50 border-green-500'
                            : note.includes('дружественна') || note.includes('✨')
                              ? themeConfig.isDark
                                ? 'bg-blue-500/20 border-blue-500'
                                : 'bg-blue-50 border-blue-500'
                              : note.includes('враждебна') || note.includes('⚠️')
                                ? themeConfig.isDark
                                  ? 'bg-red-500/20 border-red-500'
                                  : 'bg-red-50 border-red-500'
                                : themeConfig.isDark
                                  ? 'bg-white/5 border-white/20'
                                  : 'bg-gray-50 border-gray-300'
                        }`}
                      >
                        <p className={`${themeConfig.text} text-base leading-relaxed`}>
                          {note}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Рекомендации */}
              <div className={`p-6 rounded-lg ${themeConfig.isDark ? 'bg-indigo-500/20' : 'bg-indigo-50'} border-2 ${themeConfig.isDark ? 'border-indigo-500/40' : 'border-indigo-200'}`}>
                <h4 className={`text-xl font-bold ${themeConfig.isDark ? 'text-indigo-300' : 'text-indigo-700'} mb-3`}>
                  💡 Рекомендации на день
                </h4>
                <div className={`space-y-2 ${themeConfig.text}`}>
                  {modalData.overall_score >= 65 && (
                    <>
                      <p>✓ Используйте этот день для важных начинаний и решений</p>
                      <p>✓ Ваша энергия находится на пике - действуйте уверенно</p>
                      <p>✓ Медитируйте на мантру планеты {modalData.ruling_planet} для усиления эффекта</p>
                    </>
                  )}
                  {modalData.overall_score >= 50 && modalData.overall_score < 65 && (
                    <>
                      <p>✓ Хороший день для повседневных дел и планирования</p>
                      <p>✓ Следуйте интуиции и будьте внимательны к деталям</p>
                      <p>✓ Избегайте рискованных решений</p>
                    </>
                  )}
                  {modalData.overall_score < 50 && modalData.overall_score >= 35 && (
                    <>
                      <p>⚠️ Сосредоточьтесь на рутинных задачах</p>
                      <p>⚠️ Отложите важные решения на более благоприятное время</p>
                      <p>⚠️ Уделите время отдыху и восстановлению сил</p>
                    </>
                  )}
                  {modalData.overall_score < 35 && (
                    <>
                      <p>⚠️ День для внутренней работы и саморазвития</p>
                      <p>⚠️ Работайте над развитием энергии {modalData.ruling_planet}</p>
                      <p>⚠️ Практикуйте мантры и медитации</p>
                      <p>⚠️ Избегайте конфликтов и стрессовых ситуаций</p>
                    </>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-6 text-center">
              <p className={themeConfig.text}>Нет данных для отображения</p>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PlanetaryDailyRoute;