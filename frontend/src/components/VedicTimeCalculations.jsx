import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { useAuth } from './AuthContext';
import { getPlanetColor } from './constants/colors';

const VedicTimeCalculations = () => {
  const [schedule, setSchedule] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedCity, setSelectedCity] = useState('');
  const { user } = useAuth();

  const fetchVedicSchedule = async (date = selectedDate, city = selectedCity) => {
    if (!user) return;
    setLoading(true); setError('');
    try {
      const params = new URLSearchParams();
      if (date) params.append('date', date);
      if (city) params.append('city', city);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/vedic-time/daily-schedule?${params}`, { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } });
      if (!response.ok) throw new Error('Ошибка получения ведического расписания');
      const data = await response.json();
      setSchedule(data);
    } catch (err) { setError(err.message); } finally { setLoading(false); }
  };

  const changeCity = async (newCity) => {
    if (!user || !newCity) return;
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/user/change-city`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` }, body: JSON.stringify({ city: newCity })
      });
      if (response.ok) await fetchVedicSchedule(selectedDate, newCity);
    } catch (err) { console.error('Ошибка смены города:', err); }
  };

  useEffect(() => { if (user) { setSelectedCity(user.city || 'Москва'); fetchVedicSchedule(); } }, [user]);

  const handleDateChange = (e) => { const newDate = e.target.value; setSelectedDate(newDate); fetchVedicSchedule(newDate, selectedCity); };
  const handleCityChange = (e) => { const newCity = e.target.value; setSelectedCity(newCity); changeCity(newCity); };

  if (!user) {
    return (
      <Card className="w-full max-w-4xl mx-auto"><CardContent className="p-6"><p className="text-center text-gray-600">Войдите в аккаунт для доступа к ведическим временным расчетам</p></CardContent></Card>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl text-center">⏰ Ведические временные расчеты</CardTitle>
          <CardDescription className="text-center">Раху Кала, Абхиджит Мухурта, планетарные часы</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4 items-center justify-center">
            <div className="flex items-center gap-2"><label className="text-sm font-medium">Дата:</label><Input type="date" value={selectedDate} onChange={handleDateChange} className="w-auto" /></div>
            <div className="flex items-center gap-2"><label className="text-sm font-medium">Город:</label><Input type="text" value={selectedCity} onChange={handleCityChange} placeholder="Введите название города" className="w-48" /></div>
            <Button onClick={() => fetchVedicSchedule()} disabled={loading}>Обновить</Button>
          </div>
        </CardContent>
      </Card>

      {loading && (<Card><CardContent className="p-6 text-center text-gray-600">Рассчитываем ведическое расписание...</CardContent></Card>)}
      {error && (<Card><CardContent className="p-6 text-center text-red-600">{error}</CardContent></Card>)}

      {schedule && (
        <>
          {/* Информация о дне */}
          <Card>
            <CardHeader><CardTitle>🌅 Информация о дне</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-3 bg-orange-50 rounded-lg">
                  <div className="text-lg font-semibold text-orange-700">{schedule.weekday?.name}</div>
                  <div className="text-sm text-gray-600">День недели</div>
                </div>
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-lg font-semibold" style={{ color: getPlanetColor(schedule.weekday?.ruling_planet) }}>{schedule.weekday?.ruling_planet}</div>
                  <div className="text-sm text-gray-600">Управляющая планета</div>
                </div>
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="text-lg font-semibold text-green-700">{schedule.city} ({schedule.timezone})</div>
                  <div className="text-sm text-gray-600">Город и часовой пояс</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Времена восхода и заката */}
          <Card>
            <CardHeader><CardTitle>☀️ Солнечные времена</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-3 bg-yellow-50 rounded-lg">
                  <div className="text-lg font-semibold text-yellow-700">{schedule.sun_times?.sunrise}</div>
                  <div className="text-sm text-gray-600">Восход</div>
                </div>
                <div className="text-center p-3 bg-orange-50 rounded-lg">
                  <div className="text-lg font-semibold text-orange-700">{schedule.sun_times?.sunset}</div>
                  <div className="text-sm text-gray-600">Закат</div>
                </div>
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-sm font-semibold text-blue-700">{schedule.sun_times?.day_duration_hours}</div>
                  <div className="text-sm text-gray-600">Длительность дня</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Неблагоприятные периоды */}
          <Card>
            <CardHeader><CardTitle className="text-red-700">⚠️ Неблагоприятные периоды</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-4">
                {schedule.inauspicious_periods?.rahu_kaal && (
                  <div className="p-4 bg-red-50 border-2 border-red-200 rounded-lg">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-2">
                      <h3 className="font-bold text-red-800 text-lg">{schedule.inauspicious_periods.rahu_kaal.name}</h3>
                      <div className="text-lg font-bold text-red-700">
                        {schedule.inauspicious_periods.rahu_kaal.start} - {schedule.inauspicious_periods.rahu_kaal.end}
                      </div>
                    </div>
                    <p className="text-sm text-red-700 mb-2">{schedule.inauspicious_periods.rahu_kaal.description}</p>
                    <div className="text-xs text-red-600">
                      Продолжительность: {schedule.inauspicious_periods.rahu_kaal.duration_minutes} минут
                    </div>
                  </div>
                )}

                {schedule.inauspicious_periods?.gulika_kaal && (
                  <div className="p-4 bg-red-50 border-2 border-red-200 rounded-lg">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-2">
                      <h3 className="font-bold text-red-800 text-lg">{schedule.inauspicious_periods.gulika_kaal.name}</h3>
                      <div className="text-lg font-bold text-red-700">
                        {schedule.inauspicious_periods.gulika_kaal.start} - {schedule.inauspicious_periods.gulika_kaal.end}
                      </div>
                    </div>
                    <p className="text-sm text-red-700 mb-2">{schedule.inauspicious_periods.gulika_kaal.description}</p>
                    <div className="text-xs text-red-600">
                      Продолжительность: {schedule.inauspicious_periods.gulika_kaal.duration_minutes} минут
                    </div>
                  </div>
                )}

                {schedule.inauspicious_periods?.yamaghanta && (
                  <div className="p-4 bg-red-50 border-2 border-red-200 rounded-lg">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-2">
                      <h3 className="font-bold text-red-800 text-lg">{schedule.inauspicious_periods.yamaghanta.name}</h3>
                      <div className="text-lg font-bold text-red-700">
                        {schedule.inauspicious_periods.yamaghanta.start} - {schedule.inauspicious_periods.yamaghanta.end}
                      </div>
                    </div>
                    <p className="text-sm text-red-700 mb-2">{schedule.inauspicious_periods.yamaghanta.description}</p>
                    <div className="text-xs text-red-600">
                      Продолжительность: {schedule.inauspicious_periods.yamaghanta.duration_minutes} минут
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Благоприятные периоды */}
          {schedule.auspicious_periods?.abhijit_muhurta && (
            <Card>
              <CardHeader><CardTitle className="text-green-700">✨ Благоприятные периоды</CardTitle></CardHeader>
              <CardContent>
                <div className="p-4 bg-green-50 border-2 border-green-300 rounded-lg">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-2">
                    <h3 className="font-bold text-green-800 text-lg">{schedule.auspicious_periods.abhijit_muhurta.name}</h3>
                    <div className="text-lg font-bold text-green-700">
                      {schedule.auspicious_periods.abhijit_muhurta.start} - {schedule.auspicious_periods.abhijit_muhurta.end}
                    </div>
                  </div>
                  <p className="text-sm text-green-700 mb-2">{schedule.auspicious_periods.abhijit_muhurta.description}</p>
                  <div className="text-xs text-green-600">
                    Продолжительность: {schedule.auspicious_periods.abhijit_muhurta.duration_minutes} минут
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Рекомендации дня */}
          {schedule.recommendations && (
            <Card>
              <CardHeader><CardTitle>💡 Рекомендации дня</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {schedule.recommendations.activities && (
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <h3 className="font-semibold text-blue-800 mb-2">Рекомендуемые активности:</h3>
                      <ul className="text-sm text-blue-700 space-y-1">
                        {schedule.recommendations.activities.map((activity, idx) => (
                          <li key={idx}>• {activity}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {schedule.recommendations.avoid && (
                    <div className="p-4 bg-red-50 rounded-lg">
                      <h3 className="font-semibold text-red-800 mb-2">Чего следует избегать:</h3>
                      <ul className="text-sm text-red-700 space-y-1">
                        {schedule.recommendations.avoid.map((item, idx) => (
                          <li key={idx}>• {item}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {schedule.recommendations.colors && (
                    <div className="p-4 bg-purple-50 rounded-lg">
                      <h3 className="font-semibold text-purple-800 mb-2">Благоприятные цвета:</h3>
                      <div className="flex flex-wrap gap-2">
                        {schedule.recommendations.colors.map((color, idx) => (
                          <span key={idx} className="text-sm bg-purple-200 text-purple-800 px-2 py-1 rounded">
                            {color}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {schedule.recommendations.planet_mantra && (
                    <div className="p-4 bg-orange-50 rounded-lg">
                      <h3 className="font-semibold text-orange-800 mb-2">Мантра дня:</h3>
                      <div className="text-lg font-mono text-orange-700 text-center p-3 bg-orange-100 rounded">
                        {schedule.recommendations.planet_mantra}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Планетарные часы */}
          <Card>
            <CardHeader>
              <CardTitle>🕐 Планетарные часы дня</CardTitle>
              <div className="text-sm text-gray-600">Показано {schedule.planetary_hours?.length || 0} планетарных часов</div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {schedule.planetary_hours?.map((hour, index) => (
                  <div key={index} className="p-3 rounded-lg border bg-white">
                    <div className="flex flex-col space-y-1">
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-medium" style={{ color: getPlanetColor(hour.planet) }}>
                          {hour.planet_sanskrit || hour.planet}
                        </div>
                        <div className="text-xs text-gray-500">Час {hour.hour || index + 1}</div>
                      </div>
                      <div className="text-xs text-gray-600">
                        {hour.start_time?.slice(11, 16) || hour.start} - {hour.end_time?.slice(11, 16) || hour.end}
                      </div>
                      {hour.is_favorable && (
                        <div className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                          Благоприятно
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};

export default VedicTimeCalculations;