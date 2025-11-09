import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Calendar, Clock, TrendingUp, AlertTriangle, CheckCircle, Sparkles, Activity, Target, Info, Loader2, Star, Zap, Shield } from 'lucide-react';
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
            {dayAnalysis.positive_aspects?.slice(0, 6).map((aspect, idx) => (
              <div 
                key={idx} 
                className={`p-5 rounded-2xl border transition-all duration-300 hover:-translate-y-1 hover:shadow-lg ${themeConfig.surface}`}
                style={{
                  borderColor: '#10b98140',
                  backgroundColor: themeConfig.isDark ? '#10b98110' : '#10b98108'
                }}
              >
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0 drop-shadow-[0_0_8px_rgba(34,197,94,0.5)]" />
                  <p className={`text-sm leading-relaxed ${themeConfig.text}`}>{aspect}</p>
                </div>
              </div>
            ))}
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
              {dayAnalysis.challenges.map((challenge, idx) => (
                <div 
                  key={idx} 
                  className={`p-5 rounded-2xl border transition-all duration-300 hover:-translate-y-1 hover:shadow-lg ${themeConfig.surface}`}
                  style={{
                    borderColor: '#f9731640',
                    backgroundColor: themeConfig.isDark ? '#f9731610' : '#f9731608'
                  }}
                >
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="h-5 w-5 text-orange-500 mt-0.5 flex-shrink-0 drop-shadow-[0_0_8px_rgba(249,115,22,0.5)]" />
                    <p className={`text-sm leading-relaxed ${themeConfig.text}`}>{challenge}</p>
                  </div>
                </div>
              ))}
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

        {/* Почасовой план дня */}
        <div className={`rounded-3xl border p-8 ${themeConfig.glass}`}>
          <div className="flex items-center gap-3 mb-4">
            <Clock className="h-6 w-6 text-indigo-500 drop-shadow-[0_0_10px_rgba(99,102,241,0.5)]" />
            <h2 className={`text-2xl font-bold ${themeConfig.text}`}>
              Почасовой план дня (24 часа)
            </h2>
          </div>
          <p className={`mb-6 text-sm ${themeConfig.mutedText}`}>
            Нажмите на час для подробных персональных рекомендаций
          </p>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
            {route.hourly_guide_24h?.map((hour, idx) => {
              const isCurrent = isCurrentHour(hour);
              const planetColor = getPlanetColor(hour.planet);
              
              return (
                <div
                  key={idx}
                  onClick={() => {
                    setSelectedHour(hour);
                    setIsHourDialogOpen(true);
                  }}
                  className={`rounded-2xl border p-4 transition-all duration-500 hover:-translate-y-1 relative cursor-pointer ${
                    isCurrent ? 'shadow-2xl scale-110 ring-4 ring-offset-4' : 'shadow-sm hover:shadow-lg'
                  }`}
                  style={{
                    borderColor: isCurrent ? planetColor : planetColor + '40',
                    backgroundColor: isCurrent ? planetColor + '40' : planetColor + '10',
                    boxShadow: isCurrent 
                      ? `0 0 60px ${planetColor}80, 0 0 120px ${planetColor}60, 0 20px 80px ${planetColor}40, inset 0 0 40px ${planetColor}20` 
                      : undefined,
                    ringColor: isCurrent ? planetColor : undefined,
                    borderWidth: isCurrent ? '3px' : '1px',
                    ringOffsetColor: themeConfig.isDark ? '#0f1214' : '#f6f9fc'
                  }}
                >
                  {isCurrent && (
                    <div 
                      className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-widest whitespace-nowrap animate-pulse shadow-lg"
                      style={{
                        backgroundColor: planetColor,
                        color: '#ffffff',
                        boxShadow: `0 0 20px ${planetColor}80, 0 0 40px ${planetColor}60`
                      }}
                    >
                      ⏰ СЕЙЧАС
                    </div>
                  )}
                  
                  <div className="text-center">
                    <div 
                      className={`font-bold mb-2 ${isCurrent ? 'text-lg' : 'text-sm'}`}
                      style={{ 
                        color: isCurrent ? '#ffffff' : planetColor,
                        textShadow: isCurrent ? `0 0 10px ${planetColor}, 0 0 20px ${planetColor}80` : undefined
                      }}
                    >
                      {hour.planet}
                    </div>
                    <div 
                      className={`text-xs ${isCurrent ? 'font-bold text-white' : themeConfig.mutedText}`}
                      style={{
                        textShadow: isCurrent ? `0 0 10px ${planetColor}80` : undefined
                      }}
                    >
                      {(typeof hour.start === 'string' ? hour.start : hour.start_time?.slice(11, 16)) || 'N/A'} — {(typeof hour.end === 'string' ? hour.end : hour.end_time?.slice(11, 16)) || 'N/A'}
                    </div>
                    {isCurrent && (
                      <div 
                        className="mt-2 inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-bold text-white animate-pulse"
                        style={{
                          backgroundColor: '#ffffff30',
                          backdropFilter: 'blur(10px)',
                          boxShadow: `0 0 20px ${planetColor}40`
                        }}
                      >
                        <Activity className="h-3 w-3" />
                        Активно
                      </div>
                    )}
                  </div>
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
          {advice.planet}
        </DialogTitle>
        <DialogDescription className={themeConfig.mutedText}>
          Планетарный час: {advice.time}
          {advice.energy_level && (
            <span className="ml-3">
              Энергия: {advice.energy_level}/10
            </span>
          )}
        </DialogDescription>
      </DialogHeader>

      <div className="mt-6 space-y-6">
        {/* Общая рекомендация */}
        {advice.general_recommendation && (
          <div className={`p-4 rounded-lg ${themeConfig.surface}`}>
            <h3 className={`font-semibold mb-2 ${themeConfig.text}`}>
              Общая рекомендация
            </h3>
            <p className={themeConfig.mutedText}>{advice.general_recommendation}</p>
          </div>
        )}

        {/* Лучшие активности */}
        {advice.best_activities && advice.best_activities.length > 0 && (
          <div className={`p-4 rounded-lg ${themeConfig.surface}`}>
            <h3 className={`font-semibold mb-3 flex items-center gap-2 ${themeConfig.text}`}>
              <CheckCircle className="h-5 w-5 text-green-500" />
              Рекомендуемые активности
            </h3>
            <ul className="space-y-2">
              {advice.best_activities.map((activity, idx) => (
                <li key={idx} className={`flex items-start gap-2 ${themeConfig.mutedText}`}>
                  <span className="text-green-500 mt-1">✓</span>
                  <span>{activity}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Чего избегать */}
        {advice.avoid_activities && advice.avoid_activities.length > 0 && (
          <div className={`p-4 rounded-lg ${themeConfig.surface}`}>
            <h3 className={`font-semibold mb-3 flex items-center gap-2 ${themeConfig.text}`}>
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              Чего избегать
            </h3>
            <ul className="space-y-2">
              {advice.avoid_activities.map((activity, idx) => (
                <li key={idx} className={`flex items-start gap-2 ${themeConfig.mutedText}`}>
                  <span className="text-orange-500 mt-1">✗</span>
                  <span>{activity}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Персонализированные советы */}
        {advice.personalized_advice && (
          <div className={`p-4 rounded-lg border-2 ${themeConfig.surface}`} style={{ borderColor: planetColor + '40' }}>
            <h3 className={`font-semibold mb-3 flex items-center gap-2 ${themeConfig.text}`}>
              <Sparkles className="h-5 w-5" style={{ color: planetColor }} />
              Персональные рекомендации
            </h3>
            <div className="space-y-3">
              {advice.personalized_advice.soul_advice && (
                <div>
                  <p className={`text-sm font-medium ${themeConfig.text}`}>
                    Для вашего числа души ({advice.personalized_advice.soul_number}):
                  </p>
                  <p className={`text-sm mt-1 ${themeConfig.mutedText}`}>
                    {advice.personalized_advice.soul_advice}
                  </p>
                </div>
              )}
              {advice.personalized_advice.destiny_advice && (
                <div>
                  <p className={`text-sm font-medium ${themeConfig.text}`}>
                    Для вашего числа судьбы ({advice.personalized_advice.destiny_number}):
                  </p>
                  <p className={`text-sm mt-1 ${themeConfig.mutedText}`}>
                    {advice.personalized_advice.destiny_advice}
                  </p>
                </div>
              )}
              {advice.personalized_advice.mind_advice && (
                <div>
                  <p className={`text-sm font-medium ${themeConfig.text}`}>
                    Для вашего числа ума ({advice.personalized_advice.mind_number}):
                  </p>
                  <p className={`text-sm mt-1 ${themeConfig.mutedText}`}>
                    {advice.personalized_advice.mind_advice}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Сила планеты в вашей карте */}
        {advice.planet_strength !== undefined && (
          <div className={`p-4 rounded-lg ${themeConfig.surface}`}>
            <h3 className={`font-semibold mb-2 ${themeConfig.text}`}>
              Сила планеты в вашей карте
            </h3>
            <div className="flex items-center gap-3">
              <div className="text-3xl font-bold" style={{ color: planetColor }}>
                {advice.planet_strength}
              </div>
              <div className="text-2xl">
                {'⭐'.repeat(Math.min(advice.planet_strength, 5))}
              </div>
            </div>
            <p className={`text-sm mt-2 ${themeConfig.mutedText}`}>
              {advice.planet_strength >= 4 ? 'Очень сильная планета в вашей карте!' :
               advice.planet_strength >= 2 ? 'Планета присутствует в вашей карте' :
               advice.planet_strength === 1 ? 'Слабая планета - возможность для развития' :
               'Планета отсутствует - время познакомиться с этой энергией'}
            </p>
          </div>
        )}
      </div>
    </>
  );
};

export default PlanetaryDailyRouteNew;

