import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

const WeeklyPlanetChart = () => {
  const [currentWeek, setCurrentWeek] = useState([]);

  const planets = {
    1: { name: 'Сурья', planet: 'Солнце', color: '#84CC16', day: 'Воскресенье' },
    2: { name: 'Чандра', planet: 'Луна', color: '#A3E635', day: 'Понедельник' },
    3: { name: 'Мангал', planet: 'Марс', color: '#BEF264', day: 'Вторник' },
    4: { name: 'Буддхи', planet: 'Меркурий', color: '#7FB069', day: 'Среда' },
    5: { name: 'Гуру', planet: 'Юпитер', color: '#84CC16', day: 'Четверг' },
    6: { name: 'Шукра', planet: 'Венера', color: '#BEF264', day: 'Пятница' },
    7: { name: 'Шани', planet: 'Сатурн', color: '#A3E635', day: 'Суббота' }
  };

  useEffect(() => {
    // Generate current week dates
    const today = new Date();
    const currentDay = today.getDay();
    const startOfWeek = new Date(today);
    startOfWeek.setDate(today.getDate() - currentDay);

    const week = [];
    for (let i = 0; i < 7; i++) {
      const date = new Date(startOfWeek);
      date.setDate(startOfWeek.getDate() + i);
      
      // Calculate favorable rating for each planet on each day
      const planetNumber = i === 6 ? 7 : (i + 1); // Sunday = 1, Saturday = 7
      const favorability = calculateFavorability(date, planetNumber);
      
      week.push({
        date: date,
        dayName: Object.values(planets)[i].day,
        planetNumber: planetNumber,
        planet: planets[planetNumber],
        favorability: favorability,
        activities: getFavorableActivities(planetNumber, favorability)
      });
    }
    
    setCurrentWeek(week);
  }, []);

  const calculateFavorability = (date, planetNumber) => {
    // Mock calculation based on date and planet
    const dayOfMonth = date.getDate();
    const month = date.getMonth() + 1;
    
    // Simple algorithm for demonstration
    const base = (dayOfMonth + month + planetNumber) % 10;
    return Math.max(3, Math.min(10, base + 3));
  };

  const getFavorableActivities = (planetNumber, favorability) => {
    const activities = {
      1: favorability > 7 ? ['Лидерство', 'Новые проекты', 'Публичные выступления'] : ['Отдых', 'Планирование'],
      2: favorability > 7 ? ['Семейные дела', 'Творчество', 'Интуитивные решения'] : ['Эмоциональный покой'],
      3: favorability > 7 ? ['Спорт', 'Активные действия', 'Решение конфликтов'] : ['Избегать споров'],
      4: favorability > 7 ? ['Обучение', 'Коммуникации', 'Торговля'] : ['Анализ', 'Размышления'],
      5: favorability > 7 ? ['Образование', 'Духовность', 'Мудрые решения'] : ['Самопознание'],
      6: favorability > 7 ? ['Искусство', 'Красота', 'Отношения'] : ['Наслаждение жизнью'],
      7: favorability > 7 ? ['Дисциплина', 'Трудная работа', 'Структура'] : ['Терпение', 'Осторожность']
    };
    
    return activities[planetNumber] || ['Обычные дела'];
  };

  const getFavorabilityColor = (rating) => {
    if (rating >= 8) return '#22C55E'; // Green
    if (rating >= 6) return '#84CC16'; // Lime
    if (rating >= 4) return '#EAB308'; // Yellow
    return '#EF4444'; // Red
  };

  const getFavorabilityText = (rating) => {
    if (rating >= 8) return 'Отлично';
    if (rating >= 6) return 'Хорошо';
    if (rating >= 4) return 'Средне';
    return 'Осторожно';
  };

  return (
    <Card className="border-lime-300 shadow-lg">
      <CardHeader style={{ background: 'linear-gradient(to right, #D9F99D, #BEF264)' }}>
        <CardTitle className="text-lime-800">Благоприятность планет на неделю</CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-7 gap-3">
          {currentWeek.map((day, index) => (
            <div 
              key={index}
              className="p-4 rounded-lg border-2 transition-all duration-300 hover:shadow-lg"
              style={{ 
                borderColor: day.planet.color,
                backgroundColor: day.planet.color + '10'
              }}
            >
              <div className="text-center">
                <div className="text-sm font-semibold text-gray-700">
                  {day.date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })}
                </div>
                <div className="text-xs text-gray-600">{day.dayName}</div>
                
                <div 
                  className="w-12 h-12 rounded-full mx-auto my-2 flex items-center justify-center text-white font-bold text-lg"
                  style={{ backgroundColor: day.planet.color }}
                >
                  {day.planetNumber}
                </div>
                
                <div className="text-sm font-semibold" style={{ color: day.planet.color }}>
                  {day.planet.name}
                </div>
                <div className="text-xs text-gray-600">{day.planet.planet}</div>
                
                <div className="mt-2">
                  <div 
                    className="text-lg font-bold"
                    style={{ color: getFavorabilityColor(day.favorability) }}
                  >
                    {day.favorability}/10
                  </div>
                  <div 
                    className="text-xs font-semibold"
                    style={{ color: getFavorabilityColor(day.favorability) }}
                  >
                    {getFavorabilityText(day.favorability)}
                  </div>
                </div>
                
                <div className="mt-3 space-y-1">
                  {day.activities.map((activity, actIndex) => (
                    <div 
                      key={actIndex}
                      className="text-xs px-2 py-1 rounded"
                      style={{ 
                        backgroundColor: day.planet.color + '20',
                        color: day.planet.color
                      }}
                    >
                      {activity}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-6 p-4 bg-lime-50 rounded-lg">
          <h4 className="font-semibold text-lime-800 mb-2">Рекомендации на неделю:</h4>
          <div className="text-sm text-lime-700 space-y-1">
            <p>• <strong>Зеленые дни (8-10):</strong> Максимально благоприятные для активных действий</p>
            <p>• <strong>Желто-зеленые дни (6-7):</strong> Хорошие для повседневных дел</p>  
            <p>• <strong>Желтые дни (4-5):</strong> Нейтральные, подходят для планирования</p>
            <p>• <strong>Красные дни (1-3):</strong> Будьте осторожны, избегайте важных решений</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default WeeklyPlanetChart;