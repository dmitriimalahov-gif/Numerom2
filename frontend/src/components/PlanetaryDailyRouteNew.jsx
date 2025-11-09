import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Calendar, Clock, TrendingUp, AlertTriangle, CheckCircle, CheckCircle2, Sparkles, Activity, Target, Info, Loader2, Star, Zap, Shield } from 'lucide-react';
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
  const [selectedAspect, setSelectedAspect] = useState(null);
  const [isAspectDialogOpen, setIsAspectDialogOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
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
    if (!hour || !hour.planet) return null;
    
    try {
      const planet = hour.planet;
      const isNight = hour.period === 'night' || false;
      
      const response = await fetch(
        `${apiBaseUrl}/vedic-time/planetary-advice/${planet}?is_night=${isNight}`,
        {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        }
      );
      
      if (!response.ok) throw new Error('Ошибка загрузки советов');
      
      const advice = await response.json();
      
      // Добавляем информацию о времени
      const startTime = typeof hour.start === 'string' ? hour.start : hour.start_time?.slice(11, 16) || '';
      const endTime = typeof hour.end === 'string' ? hour.end : hour.end_time?.slice(11, 16) || '';
      advice.time = `${startTime} - ${endTime}`;
      advice.isFavorable = hour.is_favorable;
      
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
              Планетарный маршрут на день
            </h1>
            <p className={`mt-2 ${themeConfig.mutedText}`}>
              Подробный анализ дня с персональными рекомендациями
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
        <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
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
                  onClick={() => {
                    if (isDetailedAspect) {
                      setSelectedAspect(aspect);
                      setIsAspectDialogOpen(true);
                    }
                  }}
                  className={`p-5 rounded-2xl border transition-all duration-300 hover:-translate-y-1 hover:shadow-lg ${
                    isDetailedAspect ? 'cursor-pointer hover:border-green-500/60' : ''
                  } ${themeConfig.surface}`}
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
          <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
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
                    onClick={() => {
                      if (isDetailedChallenge) {
                        setSelectedAspect(challenge);
                        setIsAspectDialogOpen(true);
                      }
                    }}
                    className={`p-5 rounded-2xl border transition-all duration-300 hover:-translate-y-1 hover:shadow-lg ${
                      isDetailedChallenge ? 'cursor-pointer hover:border-orange-500/60' : ''
                    } ${themeConfig.surface}`}
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
        <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
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

        {/* График движения по планетам */}
        {route?.hourly_guide_24h && route.hourly_guide_24h.length > 0 && (
          <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
            <div className="flex items-center gap-3 mb-6">
              <TrendingUp className="h-6 w-6 text-cyan-500 drop-shadow-[0_0_10px_rgba(6,182,212,0.5)]" />
              <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
                График движения по планетам
              </h2>
            </div>
            
            <div className={`p-6 rounded-2xl ${themeConfig.surface}`} style={{
              borderLeft: `4px solid ${getPlanetColor(route.schedule?.weekday?.ruling_planet)}`,
              backgroundColor: themeConfig.isDark ? '#0f172a' : '#f8fafc'
            }}>
              <div className="space-y-4">
                {route.hourly_guide_24h.map((hour, index) => {
                  const isActive = isCurrentHour(hour);
                  const planetColor = getPlanetColor(hour.planet);
                  const nextHour = route.hourly_guide_24h[index + 1];
                  
                  return (
                    <div key={index}>
                      <div 
                        className={`flex items-center gap-4 p-4 rounded-xl transition-all duration-300 ${
                          isActive ? 'scale-105' : 'hover:scale-102'
                        }`}
                        style={{
                          backgroundColor: isActive 
                            ? (themeConfig.isDark ? planetColor + '30' : planetColor + '20')
                            : (themeConfig.isDark ? planetColor + '10' : planetColor + '08'),
                          borderLeft: `4px solid ${planetColor}`,
                          boxShadow: isActive ? `0 0 20px ${planetColor}40` : undefined
                        }}
                      >
                        {/* Время */}
                        <div className="flex-shrink-0 w-32">
                          <div className={`text-sm font-bold ${themeConfig.text}`}>
                            {typeof hour.start === 'string' ? hour.start : hour.start_time?.slice(11, 16) || ''}
                            {' - '}
                            {typeof hour.end === 'string' ? hour.end : hour.end_time?.slice(11, 16) || ''}
                          </div>
                          {isActive && (
                            <div className="text-xs font-bold text-cyan-500 mt-1">
                              ⏰ СЕЙЧАС
                            </div>
                          )}
                        </div>

                        {/* Планета */}
                        <div className="flex-shrink-0">
                          <div 
                            className="w-16 h-16 rounded-full flex items-center justify-center font-bold text-white shadow-lg"
                            style={{
                              backgroundColor: planetColor,
                              boxShadow: `0 0 20px ${planetColor}60`
                            }}
                          >
                            {hour.planet_sanskrit || hour.planet}
                          </div>
                        </div>

                        {/* Описание */}
                        <div className="flex-1">
                          <div className={`font-bold text-lg mb-1 ${themeConfig.text}`} style={{ color: planetColor }}>
                            {hour.planet}
                          </div>
                          <div className={`text-sm ${themeConfig.mutedText}`}>
                            {hour.description || `Час планеты ${hour.planet}`}
                          </div>
                        </div>

                        {/* Кнопка деталей */}
                        <button
                          onClick={() => {
                            setSelectedHour(hour);
                            setIsHourDialogOpen(true);
                          }}
                          className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
                            isActive ? 'animate-pulse' : ''
                          }`}
                          style={{
                            backgroundColor: planetColor + '20',
                            color: planetColor,
                            border: `2px solid ${planetColor}60`
                          }}
                        >
                          Подробнее
                        </button>
                      </div>

                      {/* Стрелка вниз между часами */}
                      {nextHour && (
                        <div className="flex justify-center py-2">
                          <div className={`text-2xl ${themeConfig.mutedText}`}>↓</div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Планетарные часы дня (старый вид - скрыт) */}
        <div className="hidden rounded-2xl border border-white/10 bg-white/5 p-5">
          <div className="flex items-center gap-3">
            <Clock className="h-5 w-5 text-indigo-300" />
            <h2 className="text-sm font-semibold uppercase tracking-[0.35em] text-indigo-200">
              Планетарные часы дня
            </h2>
          </div>
          <p className="mt-3 text-sm leading-relaxed text-indigo-100">
            Показано {route?.hourly_guide_24h?.length || 0} планетарных часов.
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
          <p className={themeConfig.mutedText}>{advice.general_advice || advice.general || advice.general_recommendation}</p>
        </div>

        {/* Благоприятные действия */}
        {(advice.activities || advice.best_activities) && (
          <div>
            <h3 className={`font-bold text-lg mb-3 flex items-center gap-2 ${themeConfig.text}`}>
              <CheckCircle2 className="h-5 w-5 text-emerald-500" />
              Благоприятные действия
            </h3>
            <ul className="space-y-2">
              {(advice.activities || advice.best_activities || []).map((activity, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-emerald-500 mt-1">✓</span>
                  <span className={themeConfig.mutedText}>{activity}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Чего избегать */}
        {(advice.avoid || advice.avoid_activities) && (
          <div>
            <h3 className={`font-bold text-lg mb-3 flex items-center gap-2 ${themeConfig.text}`}>
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              Чего избегать
            </h3>
            <ul className="space-y-2">
              {(advice.avoid || advice.avoid_activities || []).map((item, idx) => (
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

      {/* Модальное окно для детальной информации об аспекте */}
      <Dialog open={isAspectDialogOpen} onOpenChange={setIsAspectDialogOpen}>
        <DialogContent 
          className={`max-w-2xl max-h-[80vh] overflow-y-auto ${themeConfig.surface} ${themeConfig.text}`}
          style={{
            backgroundColor: themeConfig.isDark ? '#1a1a2e' : '#ffffff',
            borderColor: selectedAspect?.icon ? getPlanetColor(route?.schedule?.weekday?.ruling_planet) + '40' : undefined
          }}
        >
          {selectedAspect ? (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-3 text-2xl">
                  {selectedAspect.icon && <span className="text-3xl">{selectedAspect.icon}</span>}
                  <span style={{ color: getPlanetColor(route?.schedule?.weekday?.ruling_planet) }}>
                    {selectedAspect.title}
                  </span>
                </DialogTitle>
                <DialogDescription className={themeConfig.mutedText}>
                  Детальная информация о вашем преимуществе
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-6 mt-6">
                {/* Краткое описание */}
                <div 
                  className="p-4 rounded-lg border"
                  style={{
                    backgroundColor: themeConfig.isDark ? '#10b98115' : '#10b98108',
                    borderColor: '#10b98140'
                  }}
                >
                  <p className={`text-base leading-relaxed ${themeConfig.text}`}>
                    {selectedAspect.short_text}
                  </p>
                </div>

                {/* Детальная информация */}
                {selectedAspect.detailed_info && (
                  <div className="space-y-2">
                    <h3 className="font-bold text-lg flex items-center gap-2">
                      <Info className="h-5 w-5 text-blue-500" />
                      Подробнее
                    </h3>
                    <p className={`text-sm leading-relaxed ${themeConfig.mutedText}`}>
                      {selectedAspect.detailed_info}
                    </p>
                  </div>
                )}

                {/* Информация о планетах */}
                {selectedAspect.planet_info && (
                  <div 
                    className="p-4 rounded-lg"
                    style={{
                      backgroundColor: themeConfig.isDark 
                        ? `${getPlanetColor(route?.schedule?.weekday?.ruling_planet)}15`
                        : `${getPlanetColor(route?.schedule?.weekday?.ruling_planet)}08`,
                      borderLeft: `4px solid ${getPlanetColor(route?.schedule?.weekday?.ruling_planet)}`
                    }}
                  >
                    <h3 className="font-bold text-lg mb-2 flex items-center gap-2">
                      <Sparkles className="h-5 w-5" style={{ color: getPlanetColor(route?.schedule?.weekday?.ruling_planet) }} />
                      Планетарная информация
                    </h3>
                    <p className={themeConfig.text}>{selectedAspect.planet_info}</p>
                  </div>
                )}

                {/* Советы */}
                {selectedAspect.advice && selectedAspect.advice.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="font-bold text-lg flex items-center gap-2">
                      {selectedAspect.type?.includes('conflict') || selectedAspect.type?.includes('dissonance') || selectedAspect.type?.includes('absence') || selectedAspect.type?.includes('weakness') || selectedAspect.type?.includes('enemy') || selectedAspect.type?.includes('disharmony') || selectedAspect.type === 'rahu_kaal' ? (
                        <>
                          <AlertTriangle className="h-5 w-5 text-orange-500" />
                          Как справиться
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="h-5 w-5 text-green-500" />
                          Рекомендации
                        </>
                      )}
                    </h3>
                    <div className="space-y-2">
                      {selectedAspect.advice.map((tip, idx) => (
                        <div 
                          key={idx}
                          className={`p-3 rounded-lg border transition-all duration-300 hover:-translate-y-0.5 ${themeConfig.surface}`}
                          style={{
                            borderColor: selectedAspect.type?.includes('conflict') || selectedAspect.type?.includes('dissonance') || selectedAspect.type?.includes('absence') || selectedAspect.type?.includes('weakness') || selectedAspect.type?.includes('enemy') || selectedAspect.type?.includes('disharmony') || selectedAspect.type === 'rahu_kaal' ? '#f9731630' : '#10b98130',
                            backgroundColor: selectedAspect.type?.includes('conflict') || selectedAspect.type?.includes('dissonance') || selectedAspect.type?.includes('absence') || selectedAspect.type?.includes('weakness') || selectedAspect.type?.includes('enemy') || selectedAspect.type?.includes('disharmony') || selectedAspect.type === 'rahu_kaal' ? (themeConfig.isDark ? '#f9731608' : '#f9731605') : (themeConfig.isDark ? '#10b98108' : '#10b98105')
                          }}
                        >
                          <div className="flex items-start gap-2">
                            <span className={selectedAspect.type?.includes('conflict') || selectedAspect.type?.includes('dissonance') || selectedAspect.type?.includes('absence') || selectedAspect.type?.includes('weakness') || selectedAspect.type?.includes('enemy') || selectedAspect.type?.includes('disharmony') || selectedAspect.type === 'rahu_kaal' ? 'text-orange-500 mt-0.5' : 'text-green-500 mt-0.5'}>
                              {selectedAspect.type?.includes('conflict') || selectedAspect.type?.includes('dissonance') || selectedAspect.type?.includes('absence') || selectedAspect.type?.includes('weakness') || selectedAspect.type?.includes('enemy') || selectedAspect.type?.includes('disharmony') || selectedAspect.type === 'rahu_kaal' ? '!' : '✓'}
                            </span>
                            <p className={`text-sm ${themeConfig.text}`}>{tip}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Решение (для challenges) */}
                {selectedAspect.solution && (
                  <div 
                    className="p-4 rounded-lg border-2"
                    style={{
                      backgroundColor: themeConfig.isDark ? '#10b98120' : '#10b98115',
                      borderColor: '#10b981'
                    }}
                  >
                    <h3 className="font-bold text-lg mb-2 flex items-center gap-2 text-green-500">
                      <Zap className="h-5 w-5" />
                      Решение
                    </h3>
                    <p className={`text-sm font-semibold ${themeConfig.text}`}>{selectedAspect.solution}</p>
                  </div>
                )}
              </div>

              <div className="mt-6 flex justify-end">
                <Button 
                  onClick={() => setIsAspectDialogOpen(false)}
                  className="backdrop-blur-xl"
                  style={{
                    backgroundColor: getPlanetColor(route?.schedule?.weekday?.ruling_planet) + '20',
                    color: getPlanetColor(route?.schedule?.weekday?.ruling_planet),
                    borderColor: getPlanetColor(route?.schedule?.weekday?.ruling_planet) + '40'
                  }}
                >
                  Закрыть
                </Button>
              </div>
            </>
          ) : (
            <>
              <DialogHeader>
                <DialogTitle>Информация</DialogTitle>
                <DialogDescription>Загрузка...</DialogDescription>
              </DialogHeader>
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
};

export default PlanetaryDailyRouteNew;

