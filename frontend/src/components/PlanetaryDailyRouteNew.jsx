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
        `${apiBaseUrl}/vedic-time/planetary-route?date=${selectedDate}&city=${encodeURIComponent(user.city)}`
      );
      if (!response.ok) throw new Error('Ошибка загрузки данных');
      const data = await response.json();
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
    try {
      const response = await fetch(
        `${apiBaseUrl}/vedic-time/hourly-advice?planet=${hour.planet}&date=${selectedDate}&city=${encodeURIComponent(user.city)}`
      );
      if (!response.ok) throw new Error('Ошибка загрузки советов');
      return await response.json();
    } catch (err) {
      console.error('Ошибка загрузки советов:', err);
      return null;
    }
  };

  // Проверка, является ли час текущим
  const isCurrentHour = (hour) => {
    if (selectedDate !== new Date().toISOString().split('T')[0]) return false;
    const now = currentTime;
    const currentTimeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    const [startHour, startMin] = hour.start.split(':').map(Number);
    const [endHour, endMin] = hour.end.split(':').map(Number);
    const [currHour, currMin] = currentTimeStr.split(':').map(Number);
    
    const currentMinutes = currHour * 60 + currMin;
    const startMinutes = startHour * 60 + startMin;
    const endMinutes = endHour * 60 + endMin;
    
    return currentMinutes >= startMinutes && currentMinutes < endMinutes;
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

  if (!routeData) return null;

  const route = routeData.route || {};
  const dayAnalysis = route.day_analysis || {};

  return (
    <div className={`min-h-screen p-6 ${themeConfig.pageBackground}`}>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Заголовок */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className={`text-3xl font-bold ${themeConfig.text}`}>
              Планетарный маршрут на день
            </h1>
            <p className={`mt-2 ${themeConfig.mutedText}`}>
              Подробный анализ дня с рекомендациями
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className={themeConfig.surface}
            />
            <Button onClick={loadRouteData} variant="outline">
              <Calendar className="h-4 w-4 mr-2" />
              Обновить
            </Button>
          </div>
        </div>

        {/* Общая оценка дня */}
        <Card className={themeConfig.glass}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-indigo-500" />
              Персональный анализ дня
            </CardTitle>
            <CardDescription>
              {route.schedule?.weekday?.name_ru} • {route.schedule?.weekday?.ruling_planet}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-4xl font-bold" style={{ color: getPlanetColor(route.schedule?.weekday?.ruling_planet) }}>
                  {dayAnalysis.overall_score || 0} баллов
                </div>
                <div className="text-lg mt-1">{dayAnalysis.overall_rating}</div>
              </div>
              <div className={`px-4 py-2 rounded-lg ${
                dayAnalysis.color_class === 'green' ? 'bg-green-500/20 text-green-300' :
                dayAnalysis.color_class === 'blue' ? 'bg-blue-500/20 text-blue-300' :
                dayAnalysis.color_class === 'orange' ? 'bg-orange-500/20 text-orange-300' :
                'bg-gray-500/20 text-gray-300'
              }`}>
                {dayAnalysis.influence?.dynamic || 'Сбалансированное'}
              </div>
            </div>
            <p className={themeConfig.mutedText}>{dayAnalysis.overall_description}</p>
          </CardContent>
        </Card>

        {/* Ваши сильные стороны */}
        <Card className={themeConfig.glass}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Star className="h-6 w-6 text-yellow-500" />
              Ваши сильные стороны сегодня
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {dayAnalysis.positive_aspects?.slice(0, 6).map((aspect, idx) => (
                <div key={idx} className={`p-4 rounded-lg border ${themeConfig.surface}`}>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <p className={themeConfig.text}>{aspect}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Области для развития */}
        {dayAnalysis.challenges && dayAnalysis.challenges.length > 0 && (
          <Card className={themeConfig.glass}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-6 w-6 text-orange-500" />
                Области для развития
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {dayAnalysis.challenges.map((challenge, idx) => (
                  <div key={idx} className={`p-4 rounded-lg border ${themeConfig.surface}`}>
                    <div className="flex items-start gap-3">
                      <AlertTriangle className="h-5 w-5 text-orange-500 mt-0.5 flex-shrink-0" />
                      <p className={themeConfig.text}>{challenge}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Сила планет в вашей карте */}
        <Card className={themeConfig.glass}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-6 w-6 text-indigo-500" />
              Сила планет в вашей карте
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              {dayAnalysis.all_planet_counts && Object.entries(dayAnalysis.all_planet_counts).map(([planet, count]) => (
                <div key={planet} className={`p-4 rounded-lg border text-center ${themeConfig.surface}`}>
                  <div className="text-2xl mb-2" style={{ color: getPlanetColor(planet) }}>
                    {planet}
                  </div>
                  <div className="text-3xl font-bold">{count}</div>
                  <div className="text-sm mt-1 text-gray-500">
                    {'⭐'.repeat(Math.min(count, 5))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Почасовой план дня */}
        <Card className={themeConfig.glass}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-6 w-6 text-indigo-500" />
              Почасовой план дня (24 часа)
            </CardTitle>
            <CardDescription>
              Нажмите на час для подробных рекомендаций
            </CardDescription>
          </CardHeader>
          <CardContent>
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
                    className={`p-4 rounded-lg border cursor-pointer transition-all duration-300 hover:-translate-y-1 hover:shadow-lg ${
                      isCurrent 
                        ? 'ring-2 ring-indigo-500 bg-indigo-500/20' 
                        : themeConfig.surface
                    }`}
                    style={isCurrent ? { borderColor: planetColor } : {}}
                  >
                    <div className="text-center">
                      <div className="text-sm font-medium mb-2" style={{ color: planetColor }}>
                        {hour.planet}
                      </div>
                      <div className={`text-xs ${themeConfig.mutedText}`}>
                        {hour.start} - {hour.end}
                      </div>
                      {isCurrent && (
                        <div className="mt-2 text-xs font-bold text-indigo-400">
                          СЕЙЧАС
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Модальное окно с советами для планетарного часа */}
      <Dialog open={isHourDialogOpen} onOpenChange={setIsHourDialogOpen}>
        <DialogContent className={`max-w-2xl max-h-[80vh] overflow-y-auto ${themeConfig.card}`}>
          {selectedHour && (
            <HourAdviceContent 
              hour={selectedHour} 
              getAdvice={getPersonalizedAdvice} 
              themeConfig={themeConfig} 
            />
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

