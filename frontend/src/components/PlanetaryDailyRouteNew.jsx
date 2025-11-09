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

const PlanetaryDailyRouteNew = () => {
  const { theme } = useOutletContext();
  const themeConfig = useTheme(theme);
  const [routeData, setRouteData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedHour, setSelectedHour] = useState(null);
  const [isHourDialogOpen, setIsHourDialogOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [activeTab, setActiveTab] = useState('day'); // day, week, month, quarter
  const { user } = useAuth();
  const apiBaseUrl = getApiBaseUrl();

  // Обновляем текущее время каждую минуту
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000);
    return () => clearInterval(timer);
  }, []);

  // Загрузка данных маршрута
  useEffect(() => {
    if (user?.city) {
      loadRouteData();
    }
  }, [selectedDate, user]);

  const loadRouteData = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(
        `${apiBaseUrl}/vedic-time/planetary-route?date=${selectedDate}&city=${encodeURIComponent(user.city)}`,
        {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        }
      );
      if (!response.ok) throw new Error('Ошибка загрузки данных');
      const data = await response.json();
      console.log('📊 Полученные данные:', data);
      console.log('📊 route:', data.route);
      console.log('📊 day_analysis:', data.route?.day_analysis);
      setRouteData(data);
    } catch (err) {
      setError(err.message);
      console.error('Ошибка загрузки маршрута:', err);
    } finally {
      setLoading(false);
    }
  };

  // Функция для получения персонализированных советов для часа
  const getPersonalizedAdvice = async (hour) => {
    if (!hour || !hour.planet) {
      console.error('getPersonalizedAdvice: hour или hour.planet отсутствует', hour);
      return null;
    }
    
    try {
      const planet = hour.planet;
      const isNight = hour.period === 'night' || false;
      
      // Если у нас уже есть все данные в hour, используем их напрямую
      if (hour.best_activities || hour.personalized_advice) {
        const startTime = typeof hour.start === 'string' ? hour.start : hour.start_time?.slice(11, 16) || hour.time?.split(' - ')[0] || '';
        const endTime = typeof hour.end === 'string' ? hour.end : hour.end_time?.slice(11, 16) || hour.time?.split(' - ')[1] || '';
        
        return {
          planet: hour.planet,
          planet_sanskrit: hour.planet_sanskrit || hour.planet,
          planetSanskrit: hour.planet_sanskrit || hour.planet,
          time: `${startTime} - ${endTime}`,
          isFavorable: hour.is_favorable,
          personalStrength: hour.personal_strength || 0,
          energyLevel: hour.energy_level || 5,
          activityType: hour.activity_type || 'Умеренная энергия',
          generalRecommendation: hour.general_recommendation || '',
          bestActivities: hour.best_activities || [],
          avoidActivities: hour.avoid_activities || [],
          personalizedAdvice: hour.personalized_advice || []
        };
      }
      
      // Иначе делаем запрос к API
      const response = await fetch(
        `${apiBaseUrl}/vedic-time/planetary-advice/${planet}?is_night=${isNight}`,
        {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        }
      );
      
      if (!response.ok) throw new Error('Ошибка загрузки советов');
      
      const advice = await response.json();
      
      // Добавляем информацию о времени
      const startTime = typeof hour.start === 'string' ? hour.start : hour.start_time?.slice(11, 16) || hour.time?.split(' - ')[0] || '';
      const endTime = typeof hour.end === 'string' ? hour.end : hour.end_time?.slice(11, 16) || hour.time?.split(' - ')[1] || '';
      advice.time = `${startTime} - ${endTime}`;
      advice.isFavorable = hour.is_favorable;
      advice.personalStrength = hour.personal_strength || 0;
      advice.energyLevel = hour.energy_level || 5;
      
      return advice;
    } catch (err) {
      console.error('Ошибка загрузки советов:', err);
      
      // Fallback: возвращаем базовые советы
      const startTime = typeof hour.start === 'string' ? hour.start : hour.start_time?.slice(11, 16) || '';
      const endTime = typeof hour.end === 'string' ? hour.end : hour.end_time?.slice(11, 16) || '';
      
      return {
        planet: hour.planet,
        planet_sanskrit: hour.planet_sanskrit || hour.planet,
        general_recommendation: `Время ${hour.planet} благоприятно для соответствующих планете действий.`,
        best_activities: ['Следуйте интуиции', 'Будьте внимательны к знакам'],
        avoid_activities: ['Спешка', 'Необдуманные решения'],
        time: `${startTime} - ${endTime}`,
        isFavorable: hour.is_favorable,
        energy_level: 5
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

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
        <span className="ml-3 text-lg">Загрузка планетарного маршрута...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <AlertTriangle className="h-12 w-12 text-red-500" />
        <span className="ml-3 text-lg">Ошибка: {error}</span>
      </div>
    );
  }

  if (!routeData) {
    console.log('⚠️ routeData пустой!');
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Info className="h-12 w-12 text-blue-500" />
        <span className="ml-3 text-lg">Нет данных для отображения</span>
      </div>
    );
  }

  // Данные приходят напрямую, а не в route!
  const route = routeData;
  const dayAnalysis = routeData.day_analysis || {};
  
  console.log('✅ Рендерим с данными:', { route, dayAnalysis });

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
            <h1 className={`text-3xl font-bold ${themeConfig.text} drop-shadow-lg`}>
              Планетарный маршрут
            </h1>
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
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
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

          {/* Контент для дня */}
          <TabsContent value="day" className="mt-6 space-y-6">
        {/* Общая оценка дня */}
        <div 
          className={`rounded-3xl border p-8 transition-all duration-500 hover:-translate-y-1 ${themeConfig.glass}`}
          style={{
            borderColor: getPlanetColor(route.schedule?.weekday?.ruling_planet) + '40',
            boxShadow: `0 0 40px ${getPlanetColor(route.schedule?.weekday?.ruling_planet)}20`
          }}
        >
          <div className="flex items-center gap-3 mb-6">
            <Sparkles 
              className="h-6 w-6 drop-shadow-[0_0_10px_rgba(255,255,255,0.45)]" 
              style={{ color: getPlanetColor(route.schedule?.weekday?.ruling_planet) }}
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
                    color: getPlanetColor(route.schedule?.weekday?.ruling_planet),
                    textShadow: `0 0 20px ${getPlanetColor(route.schedule?.weekday?.ruling_planet)}80`
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
                  {route.schedule?.weekday?.name_ru}
                </div>
              </div>
            </div>
            
            <div className="flex flex-col gap-3">
              <div 
                className="px-6 py-3 rounded-2xl font-semibold text-center backdrop-blur-xl"
                style={{
                  backgroundColor: getPlanetColor(route.schedule?.weekday?.ruling_planet) + '30',
                  color: getPlanetColor(route.schedule?.weekday?.ruling_planet),
                  boxShadow: `0 0 20px ${getPlanetColor(route.schedule?.weekday?.ruling_planet)}40`
                }}
              >
                {route.schedule?.weekday?.ruling_planet}
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
          
          <p className={`mt-6 text-base leading-relaxed ${themeConfig.mutedText}`}>
            {dayAnalysis.overall_description}
          </p>
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

        {/* График энергий планет на день */}
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
                  {Array.from(new Set(route.hourly_guide_24h.map(h => h.planet))).map(planet => {
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
                    {route.hourly_guide_24h.map((hour, index) => {
                      const isActive = isCurrentHour(hour);
                      const planetColor = getPlanetColor(hour.planet);
                      const width = `${100 / route.hourly_guide_24h.length}%`;
                      
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
              Показано {route.hourly_guide_24h.length} планетарных часов. Нажмите на час для получения персональных советов.
            </p>
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {route.hourly_guide_24h?.map((hour, index) => {
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
          </TabsContent>

          {/* Контент для недели */}
          <TabsContent value="week" className="mt-6">
            <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
              <div className="text-center py-12">
                <CalendarDays className={`h-16 w-16 mx-auto mb-4 ${themeConfig.mutedText}`} />
                <h3 className={`text-2xl font-bold mb-2 ${themeConfig.text}`}>
                  Планетарный маршрут на неделю
                </h3>
                <p className={`${themeConfig.mutedText} mb-6`}>
                  Детальный анализ недели с рекомендациями на каждый день
                </p>
                
                {/* Предварительная структура */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8 text-left">
                  <div className={`p-6 rounded-2xl border ${themeConfig.surface}`}>
                    <h4 className={`font-bold text-lg mb-3 ${themeConfig.text}`}>📊 Обзор недели</h4>
                    <ul className={`space-y-2 text-sm ${themeConfig.mutedText}`}>
                      <li>• Общая энергетика недели</li>
                      <li>• Благоприятные и сложные дни</li>
                      <li>• Ключевые планетарные влияния</li>
                      <li>• Рекомендации по планированию</li>
                    </ul>
                  </div>
                  
                  <div className={`p-6 rounded-2xl border ${themeConfig.surface}`}>
                    <h4 className={`font-bold text-lg mb-3 ${themeConfig.text}`}>📅 Календарь недели</h4>
                    <ul className={`space-y-2 text-sm ${themeConfig.mutedText}`}>
                      <li>• 7 дней с детальным анализом</li>
                      <li>• Цветовая индикация дней</li>
                      <li>• Планетарные часы каждого дня</li>
                      <li>• Персональные советы</li>
                    </ul>
                  </div>
                  
                  <div className={`p-6 rounded-2xl border ${themeConfig.surface}`}>
                    <h4 className={`font-bold text-lg mb-3 ${themeConfig.text}`}>🎯 Цели недели</h4>
                    <ul className={`space-y-2 text-sm ${themeConfig.mutedText}`}>
                      <li>• Оптимальное время для важных дел</li>
                      <li>• Дни для отдыха и восстановления</li>
                      <li>• Периоды максимальной продуктивности</li>
                      <li>• Защита в сложные периоды</li>
                    </ul>
                  </div>
                  
                  <div className={`p-6 rounded-2xl border ${themeConfig.surface}`}>
                    <h4 className={`font-bold text-lg mb-3 ${themeConfig.text}`}>⚡ Энергетический график</h4>
                    <ul className={`space-y-2 text-sm ${themeConfig.mutedText}`}>
                      <li>• Визуализация энергий недели</li>
                      <li>• Пики и спады активности</li>
                      <li>• Планетарные транзиты</li>
                      <li>• Рекомендации по балансу</li>
                    </ul>
                  </div>
                </div>
                
                <Badge className="mt-6 bg-blue-500/20 text-blue-400 border-blue-500/40">
                  В разработке
                </Badge>
              </div>
            </div>
          </TabsContent>

          {/* Контент для месяца */}
          <TabsContent value="month" className="mt-6">
            <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
              <div className="text-center py-12">
                <CalendarRange className={`h-16 w-16 mx-auto mb-4 ${themeConfig.mutedText}`} />
                <h3 className={`text-2xl font-bold mb-2 ${themeConfig.text}`}>
                  Планетарный маршрут на месяц
                </h3>
                <p className={`${themeConfig.mutedText} mb-6`}>
                  Полный анализ месяца с недельными и дневными прогнозами
                </p>
                
                {/* Предварительная структура */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8 text-left">
                  <div className={`p-6 rounded-2xl border ${themeConfig.surface}`}>
                    <h4 className={`font-bold text-lg mb-3 ${themeConfig.text}`}>🌙 Обзор месяца</h4>
                    <ul className={`space-y-2 text-sm ${themeConfig.mutedText}`}>
                      <li>• Общая тематика месяца</li>
                      <li>• Ключевые планетарные периоды</li>
                      <li>• Благоприятные недели</li>
                      <li>• Критические точки</li>
                    </ul>
                  </div>
                  
                  <div className={`p-6 rounded-2xl border ${themeConfig.surface}`}>
                    <h4 className={`font-bold text-lg mb-3 ${themeConfig.text}`}>📆 Календарь месяца</h4>
                    <ul className={`space-y-2 text-sm ${themeConfig.mutedText}`}>
                      <li>• 4-5 недель с анализом</li>
                      <li>• Важные даты и события</li>
                      <li>• Лунные фазы и влияния</li>
                      <li>• Планетарные транзиты</li>
                    </ul>
                  </div>
                  
                  <div className={`p-6 rounded-2xl border ${themeConfig.surface}`}>
                    <h4 className={`font-bold text-lg mb-3 ${themeConfig.text}`}>💼 Сферы жизни</h4>
                    <ul className={`space-y-2 text-sm ${themeConfig.mutedText}`}>
                      <li>• Карьера и финансы</li>
                      <li>• Отношения и семья</li>
                      <li>• Здоровье и энергия</li>
                      <li>• Духовное развитие</li>
                    </ul>
                  </div>
                  
                  <div className={`p-6 rounded-2xl border ${themeConfig.surface}`}>
                    <h4 className={`font-bold text-lg mb-3 ${themeConfig.text}`}>📈 Тренды и прогнозы</h4>
                    <ul className={`space-y-2 text-sm ${themeConfig.mutedText}`}>
                      <li>• Графики энергий месяца</li>
                      <li>• Оптимальное время для начинаний</li>
                      <li>• Периоды завершения проектов</li>
                      <li>• Рекомендации по планированию</li>
                    </ul>
                  </div>
                </div>
                
                <Badge className="mt-6 bg-cyan-500/20 text-cyan-400 border-cyan-500/40">
                  В разработке
                </Badge>
              </div>
            </div>
          </TabsContent>

          {/* Контент для квартала */}
          <TabsContent value="quarter" className="mt-6">
            <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
              <div className="text-center py-12">
                <CalendarRange className={`h-16 w-16 mx-auto mb-4 ${themeConfig.mutedText}`} />
                <h3 className={`text-2xl font-bold mb-2 ${themeConfig.text}`}>
                  Планетарный маршрут на квартал
                </h3>
                <p className={`${themeConfig.mutedText} mb-6`}>
                  Стратегический анализ на 3 месяца с долгосрочными прогнозами
                </p>
                
                {/* Предварительная структура */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8 text-left">
                  <div className={`p-6 rounded-2xl border ${themeConfig.surface}`}>
                    <h4 className={`font-bold text-lg mb-3 ${themeConfig.text}`}>🎯 Обзор квартала</h4>
                    <ul className={`space-y-2 text-sm ${themeConfig.mutedText}`}>
                      <li>• Главные темы 3 месяцев</li>
                      <li>• Ключевые планетарные циклы</li>
                      <li>• Благоприятные месяцы</li>
                      <li>• Периоды трансформации</li>
                    </ul>
                  </div>
                  
                  <div className={`p-6 rounded-2xl border ${themeConfig.surface}`}>
                    <h4 className={`font-bold text-lg mb-3 ${themeConfig.text}`}>📊 Помесячный анализ</h4>
                    <ul className={`space-y-2 text-sm ${themeConfig.mutedText}`}>
                      <li>• 3 месяца с детальными прогнозами</li>
                      <li>• Ключевые события каждого месяца</li>
                      <li>• Планетарные влияния</li>
                      <li>• Рекомендации по планированию</li>
                    </ul>
                  </div>
                  
                  <div className={`p-6 rounded-2xl border ${themeConfig.surface}`}>
                    <h4 className={`font-bold text-lg mb-3 ${themeConfig.text}`}>🌟 Долгосрочные цели</h4>
                    <ul className={`space-y-2 text-sm ${themeConfig.mutedText}`}>
                      <li>• Оптимальное время для больших проектов</li>
                      <li>• Периоды роста и развития</li>
                      <li>• Время для обучения</li>
                      <li>• Карьерные возможности</li>
                    </ul>
                  </div>
                  
                  <div className={`p-6 rounded-2xl border ${themeConfig.surface}`}>
                    <h4 className={`font-bold text-lg mb-3 ${themeConfig.text}`}>🔮 Стратегический прогноз</h4>
                    <ul className={`space-y-2 text-sm ${themeConfig.mutedText}`}>
                      <li>• Долгосрочные тренды</li>
                      <li>• Важные решения и выборы</li>
                      <li>• Периоды отдыха и восстановления</li>
                      <li>• Рекомендации по балансу жизни</li>
                    </ul>
                  </div>
                </div>
                
                <Badge className="mt-6 bg-teal-500/20 text-teal-400 border-teal-500/40">
                  В разработке
                </Badge>
              </div>
            </div>
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
          style={{ color: planetColor }}
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
          {advice.planet_sanskrit || advice.planetSanskrit || advice.planet}
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
        {/* Информация о планете в карте */}
        {(advice.personalStrength !== undefined || advice.energyLevel !== undefined || advice.activityType) && (
          <div className="grid grid-cols-3 gap-3">
            {advice.personalStrength !== undefined && (
              <div 
                className={`p-3 rounded-lg text-center ${themeConfig.text}`}
                style={{
                  ...getBackgroundStyle('20'),
                  ...getBorderStyle('60')
                }}
              >
                <div className="text-2xl font-bold" style={{ color: planetColor }}>
                  {advice.personalStrength}
                </div>
                <div className="text-xs mt-1 opacity-70">Сила в карте</div>
              </div>
            )}
            {advice.energyLevel !== undefined && (
              <div 
                className={`p-3 rounded-lg text-center ${themeConfig.text}`}
                style={{
                  ...getBackgroundStyle('20'),
                  ...getBorderStyle('60')
                }}
              >
                <div className="text-2xl font-bold" style={{ color: planetColor }}>
                  {advice.energyLevel}/10
                </div>
                <div className="text-xs mt-1 opacity-70">Энергия часа</div>
              </div>
            )}
            {advice.activityType && (
              <div 
                className={`p-3 rounded-lg text-center ${themeConfig.text}`}
                style={{
                  ...getBackgroundStyle('20'),
                  ...getBorderStyle('60')
                }}
              >
                <div className="text-sm font-bold" style={{ color: planetColor }}>
                  {advice.activityType}
                </div>
              </div>
            )}
          </div>
        )}

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
        {(advice.general_advice || advice.general || advice.general_recommendation || advice.generalRecommendation) && (
          <div>
            <h3 className={`font-bold text-lg mb-2 flex items-center gap-2 ${themeConfig.text}`}>
              <Sparkles className="h-5 w-5" style={{ color: planetColor }} />
              Общая характеристика
            </h3>
            <p className={themeConfig.mutedText}>{advice.general_advice || advice.general || advice.general_recommendation || advice.generalRecommendation}</p>
          </div>
        )}

        {/* Благоприятные действия */}
        {(advice.activities || advice.best_activities || advice.bestActivities) && (advice.activities || advice.best_activities || advice.bestActivities).length > 0 && (
          <div>
            <h3 className={`font-bold text-lg mb-3 flex items-center gap-2 ${themeConfig.text}`}>
              <CheckCircle2 className="h-5 w-5 text-emerald-500" />
              Благоприятные действия
            </h3>
            <ul className="space-y-2">
              {(advice.activities || advice.best_activities || advice.bestActivities || []).map((activity, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-emerald-500 mt-1">✓</span>
                  <span className={themeConfig.mutedText}>{activity}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Чего избегать */}
        {(advice.avoid || advice.avoid_activities || advice.avoidActivities) && (advice.avoid || advice.avoid_activities || advice.avoidActivities).length > 0 && (
          <div>
            <h3 className={`font-bold text-lg mb-3 flex items-center gap-2 ${themeConfig.text}`}>
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              Чего избегать
            </h3>
            <ul className="space-y-2">
              {(advice.avoid || advice.avoid_activities || advice.avoidActivities || []).map((item, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-amber-500 mt-1">⚠</span>
                  <span className={themeConfig.mutedText}>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Здоровье */}
        {advice.health && (
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
        )}

        {/* Персонализированные советы */}
        {(advice.personalized_advice || advice.personalizedAdvice) && (advice.personalized_advice || advice.personalizedAdvice).length > 0 && (
          <div>
            <h3 className={`font-bold text-lg mb-3 flex items-center gap-2 ${themeConfig.text}`}>
              <Star className="h-5 w-5 text-yellow-500" />
              Персональные рекомендации
            </h3>
            <div className="space-y-2">
              {(advice.personalized_advice || advice.personalizedAdvice || []).map((item, idx) => (
                <div 
                  key={idx}
                  className={`p-3 rounded-lg border ${themeConfig.text}`}
                  style={{
                    ...getBackgroundStyle('15'),
                    ...getBorderStyle('40')
                  }}
                >
                  <p className="text-sm">{item}</p>
                </div>
              ))}
            </div>
          </div>
        )}

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
