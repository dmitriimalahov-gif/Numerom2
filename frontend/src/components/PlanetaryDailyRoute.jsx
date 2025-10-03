import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Calendar, CalendarDays, Clock, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';
import { useAuth } from './AuthContext';

const PlanetaryDailyRoute = () => {
  const [routeData, setRouteData] = useState({});
  const [loading, setLoading] = useState({});
  const [error, setError] = useState('');
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [activeTab, setActiveTab] = useState('daily');
  const [currentTime, setCurrentTime] = useState(new Date());
  const { user } = useAuth();

  const fetchRouteData = async (period = 'daily', date = selectedDate) => {
    if (!user) return;

    setLoading(prev => ({ ...prev, [period]: true }));
    setError('');

    try {
      const params = new URLSearchParams();
      if (date) params.append('date', date);
      if (user.city) params.append('city', user.city);

      let endpoint = `${process.env.REACT_APP_BACKEND_URL}/api/vedic-time/planetary-route`;
      if (period === 'monthly') {
        endpoint += '/monthly';
      } else if (period === 'quarterly') {
        endpoint += '/quarterly';
      }

      const response = await fetch(
        `${endpoint}?${params}`, 
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка получения планетарного маршрута');
      }

      const data = await response.json();
      setRouteData(prev => ({ ...prev, [period]: data }));
    } catch (err) {
      console.error(`Ошибка загрузки ${period}:`, err);
      setError(err.message);
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
    const route = routeData.daily;
    if (!route) return null;

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
              <div className="text-center p-3 bg-orange-50 rounded-lg">
                <div className="text-lg font-semibold text-orange-700">
                  {route.date}
                </div>
                <div className="text-sm text-gray-600">Дата</div>
              </div>
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-lg font-semibold text-blue-700">
                  {route.city}
                </div>
                <div className="text-sm text-gray-600">Город</div>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded-lg">
                <div className="text-lg font-semibold text-purple-700">
                  {route.daily_ruling_planet}
                </div>
                <div className="text-sm text-gray-600">Планета дня</div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-lg font-semibold text-green-700">
                  {route.personal_birth_date}
                </div>
                <div className="text-sm text-gray-600">Ваша дата рождения</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Лучшие часы для активности */}
        <Card>
          <CardHeader>
            <CardTitle className="text-green-700 flex items-center">
              <CheckCircle className="w-5 h-5 mr-2" />
              Лучшие часы для активности
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {route.best_activity_hours?.map((hour, index) => (
                <div key={index} className="bg-green-50 border-2 border-green-300 p-4 rounded-lg">
                  <div className="text-lg font-bold text-green-800 mb-1">
                    {hour}
                  </div>
                  <div className="text-sm text-green-700">
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
            <CardTitle className="text-red-700 flex items-center">
              <AlertTriangle className="w-5 h-5 mr-2" />
              Периоды, которых стоит избегать
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(route.avoid_periods || {}).map(([key, period]) => (
                <div key={key} className="bg-red-50 border-2 border-red-300 p-4 rounded-lg">
                  <h3 className="font-semibold text-red-800 mb-2">{period.name || key}</h3>
                  <div className="text-lg font-bold text-red-800 mb-2">
                    {period.start} - {period.end}
                  </div>
                  <div className="text-sm text-red-700">
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

        {/* Почасовой план дня */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Clock className="w-5 h-5 mr-2" />
              Почасовой план дня
            </CardTitle>
            <CardDescription>
              Первые 8 часов дня с планетарными влияниями
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {route.hourly_guide?.map((hour, index) => {
                const startTime = hour.start_time?.slice(11, 16);
                const endTime = hour.end_time?.slice(11, 16);
                const isCurrent = isCurrentHour(startTime, endTime);
                
                return (
                  <div
                    key={index}
                    className={`p-4 rounded-lg border-2 ${
                      isCurrent 
                        ? 'bg-blue-100 border-blue-400' 
                        : hour.is_favorable 
                          ? 'bg-green-50 border-green-300' 
                          : 'bg-gray-50 border-gray-300'
                    }`}
                  >
                    <div className="flex justify-between items-center mb-2">
                      <div className="flex items-center gap-3">
                        <span className="font-bold text-lg">Час {hour.hour}</span>
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
                      </div>
                      <div className="text-right">
                        <div className="font-semibold">{startTime} - {endTime}</div>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <div className="font-medium text-gray-800">
                        {hour.planet_sanskrit || hour.planet}
                      </div>
                      <div className="text-sm text-gray-600">
                        Планета: {hour.planet}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

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

  const renderMonthlyView = () => {
    const monthlyData = routeData.monthly;
    if (!monthlyData) return null;

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
                {monthlyData.monthly_summary.best_days.map((date, index) => (
                  <div key={index} className="text-center p-3 bg-green-50 border-2 border-green-300 rounded-lg">
                    <div className="font-semibold text-green-800">
                      {new Date(date).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })}
                    </div>
                    <div className="text-xs text-green-600">
                      {new Date(date).toLocaleDateString('ru-RU', { weekday: 'short' })}
                    </div>
                  </div>
                ))}
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
              {monthlyData.daily_schedule?.map((day, index) => (
                <div key={index} className="p-2 text-center border rounded-lg hover:bg-gray-50 min-h-[80px] flex flex-col justify-between">
                  <div className="text-sm font-semibold">
                    {new Date(day.date).getDate()}
                  </div>
                  <div className="text-[10px] text-gray-600 leading-tight break-words">
                    {day.ruling_planet?.split('(')[0]?.trim() || ''}
                  </div>
                  <div className="flex justify-center gap-1 mt-1">
                    {day.favorable_activities?.length >= 3 && (
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    )}
                    {day.avoid_activities?.length >= 3 && (
                      <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    )}
                  </div>
                </div>
              ))}
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
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="daily" className="flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            День
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
    </div>
  );
};

export default PlanetaryDailyRoute;