import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { MapPin, Clock } from 'lucide-react';

const VedicTimesWidget = () => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [location, setLocation] = useState('Москва');
  const [vedicTimes, setVedicTimes] = useState(null);

  // Mock vedic times data for different cities
  const cityVedicTimes = {
    'Москва': {
      rahuKala: { start: '14:30', end: '16:00' },
      abhijitMuhurta: { start: '12:20', end: '13:10' },
      gulikaKala: { start: '10:45', end: '12:15' },
      yamaghanda: { start: '09:00', end: '10:30' }
    },
    'Санкт-Петербург': {
      rahuKala: { start: '14:45', end: '16:15' },
      abhijitMuhurta: { start: '12:35', end: '13:25' },
      gulikaKala: { start: '11:00', end: '12:30' },
      yamaghanda: { start: '09:15', end: '10:45' }
    }
  };

  const vedicTimeDescriptions = {
    rahuKala: { title: 'Раху Кала', color: '#FF6B6B', active: false },
    abhijitMuhurta: { title: 'Абхиджит', color: '#51C878', active: false },
    gulikaKala: { title: 'Гулика', color: '#D2691E', active: false },
    yamaghanda: { title: 'Ямаганда', color: '#9370DB', active: false }
  };

  useEffect(() => {
    // Update time every minute
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000);

    // Try to get user's location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          // In real app, convert coordinates to city name
          setLocation('Определяется...');
          setTimeout(() => setLocation('Москва'), 1000);
        },
        (error) => {
          setLocation('Москва'); // fallback
        }
      );
    }

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    // Calculate current vedic times for location
    const times = cityVedicTimes[location] || cityVedicTimes['Москва'];
    const now = currentTime.toTimeString().slice(0, 5);
    
    // Check which period is currently active
    const updatedTimes = { ...times };
    Object.keys(updatedTimes).forEach(period => {
      const start = updatedTimes[period].start;
      const end = updatedTimes[period].end;
      updatedTimes[period].active = (now >= start && now <= end);
    });

    setVedicTimes(updatedTimes);
  }, [currentTime, location]);

  const getCurrentPeriod = () => {
    if (!vedicTimes) return null;
    
    for (const [key, period] of Object.entries(vedicTimes)) {
      if (period.active) {
        return { key, period, description: vedicTimeDescriptions[key] };
      }
    }
    return null;
  };

  const currentPeriod = getCurrentPeriod();

  return (
    <Card className="border-emerald-200 shadow-lg">
      <CardHeader className="bg-gradient-to-r from-emerald-100 to-teal-100">
        <CardTitle className="text-emerald-800 flex items-center gap-2">
          <Clock className="w-5 h-5" />
          Ведические времена сегодня
        </CardTitle>
      </CardHeader>
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-4">
          <MapPin className="w-4 h-4 text-gray-600" />
          <span className="text-sm text-gray-600">{location}</span>
          <span className="ml-auto text-sm font-mono">
            {currentTime.toLocaleTimeString('ru-RU', { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </span>
        </div>

        {/* Current active period */}
        {currentPeriod && (
          <div 
            className="p-3 rounded-lg mb-4 text-white font-semibold text-center animate-pulse"
            style={{ backgroundColor: currentPeriod.description.color }}
          >
            Сейчас: {currentPeriod.description.title}
            <div className="text-sm opacity-90">
              {currentPeriod.period.start} - {currentPeriod.period.end}
            </div>
          </div>
        )}

        {/* All periods for today */}
        <div className="space-y-2">
          {vedicTimes && Object.entries(vedicTimes).map(([key, period]) => {
            const desc = vedicTimeDescriptions[key];
            return (
              <div 
                key={key}
                className={`flex justify-between items-center p-2 rounded text-sm ${
                  period.active ? 'ring-2 ring-offset-1' : ''
                }`}
                style={{ 
                  backgroundColor: desc.color + '20',
                  color: desc.color,
                  ringColor: period.active ? desc.color : 'transparent'
                }}
              >
                <span className="font-medium">{desc.title}</span>
                <span className="font-mono">
                  {period.start} - {period.end}
                </span>
              </div>
            );
          })}
        </div>

        {/* Quick recommendations */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <div className="text-xs text-gray-600">
            {currentPeriod ? (
              currentPeriod.key === 'abhijitMuhurta' ? (
                <span className="text-green-700 font-medium">
                  ✨ Благоприятное время для важных дел
                </span>
              ) : (
                <span className="text-orange-700 font-medium">
                  ⚠️ Избегайте новых начинаний
                </span>
              )
            ) : (
              <span className="text-gray-700">
                🟢 Нейтральное время для повседневных дел
              </span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default VedicTimesWidget;