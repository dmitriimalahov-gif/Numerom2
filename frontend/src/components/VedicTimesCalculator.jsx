import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Calendar } from './ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';
import { CalendarIcon, Clock, Sun, Moon } from 'lucide-react';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { mockVedicTimes, vedicTimeDescriptions } from '../mock';

const VedicTimesCalculator = () => {
  const [selectedDate, setSelectedDate] = useState(null);
  const [vedicTimes, setVedicTimes] = useState(null);

  const calculateVedicTimes = () => {
    if (!selectedDate) return;
    
    const result = mockVedicTimes.calculateVedicTimes(selectedDate);
    setVedicTimes(result);
  };

  const formatTime = (period) => {
    const startHour = Math.floor(period.start);
    const startMin = Math.round((period.start - startHour) * 60);
    const endHour = Math.floor(period.end);
    const endMin = Math.round((period.end - endHour) * 60);
    
    return `${String(startHour).padStart(2, '0')}:${String(startMin).padStart(2, '0')} - ${String(endHour).padStart(2, '0')}:${String(endMin).padStart(2, '0')}`;
  };

  const VedicTimeCard = ({ timeKey, period, description }) => (
    <Card 
      className="border-2 transition-all duration-300 hover:shadow-lg hover:scale-105" 
      style={{ borderColor: description.color + '40', backgroundColor: description.color + '10' }}
    >
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg" style={{ color: description.color }}>
          <Clock className="w-5 h-5" />
          {description.title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-center mb-4">
          <div 
            className="text-3xl font-bold mb-2"
            style={{ color: description.color }}
          >
            {formatTime(period)}
          </div>
        </div>
        <p className="text-sm text-gray-700 leading-relaxed">
          {description.description}
        </p>
      </CardContent>
    </Card>
  );

  const Astrological_Grid = () => (
    <div className="relative w-full max-w-md mx-auto mb-6">
      <svg viewBox="0 0 300 300" className="w-full h-full">
        {/* Grid lines */}
        {[0, 1, 2, 3].map(i => (
          <g key={i}>
            <line 
              x1="0" 
              y1={i * 75} 
              x2="300" 
              y2={i * 75} 
              stroke="#E0E0E0" 
              strokeWidth="2"
            />
            <line 
              x1={i * 75} 
              y1="0" 
              x2={i * 75} 
              y2="300" 
              stroke="#E0E0E0" 
              strokeWidth="2"
            />
          </g>
        ))}
        
        {/* Diagonal lines */}
        <line x1="0" y1="0" x2="300" y2="300" stroke="#7FB069" strokeWidth="3" />
        <line x1="300" y1="0" x2="0" y2="300" stroke="#7FB069" strokeWidth="3" />
        <line x1="150" y1="0" x2="150" y2="300" stroke="#7FB069" strokeWidth="3" />
        <line x1="0" y1="150" x2="300" y2="150" stroke="#7FB069" strokeWidth="3" />
        
        {/* Corner points */}
        <circle cx="37.5" cy="37.5" r="8" fill="#FFB6C1" stroke="#FFF" strokeWidth="2" />
        <circle cx="150" cy="37.5" r="8" fill="#A8A8A8" stroke="#FFF" strokeWidth="2" />
        <circle cx="262.5" cy="37.5" r="8" fill="#A0764A" stroke="#FFF" strokeWidth="2" />
        <circle cx="262.5" cy="150" r="8" fill="#2E4BC6" stroke="#FFF" strokeWidth="2" />
        <circle cx="262.5" cy="262.5" r="8" fill="#708090" stroke="#FFF" strokeWidth="2" />
        <circle cx="150" cy="262.5" r="8" fill="#FF8C00" stroke="#FFF" strokeWidth="2" />
        <circle cx="37.5" cy="262.5" r="8" fill="#E74C3C" stroke="#FFF" strokeWidth="2" />
        <circle cx="37.5" cy="150" r="8" fill="#7FB069" stroke="#FFF" strokeWidth="2" />
        <circle cx="150" cy="150" r="10" fill="#51C878" stroke="#FFF" strokeWidth="3" />
      </svg>
    </div>
  );

  const TimePeriodsGrid = () => {
    if (!vedicTimes) return null;

    const { periods } = vedicTimes;
    const dayNames = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'];

    return (
      <div className="grid grid-cols-5 gap-2 mb-6">
        <div className="text-center font-semibold text-gray-600">Ч/Д</div>
        {[1, 3, 1, 0, 4].map((num, idx) => (
          <div key={idx} className="text-center p-3 bg-gray-100 rounded-lg font-bold">
            {num}
          </div>
        ))}
        
        <div className="text-center font-semibold text-gray-600">Ч/У</div>
        {[1, 5, 0, 1, 6].map((num, idx) => (
          <div key={idx} className="text-center p-3 bg-gray-100 rounded-lg font-bold">
            {num}
          </div>
        ))}
        
        <div className="text-center font-semibold text-gray-600">Ч/С</div>
        {[4, 0, 0, 1, 1].map((num, idx) => (
          <div key={idx} className="text-center p-3 bg-gray-100 rounded-lg font-bold">
            {num}
          </div>
        ))}
        
        <div></div>
        {[0, 8, 1, 2, 4].map((num, idx) => (
          <div key={idx} className="text-center p-3 bg-gray-200 rounded-lg font-bold">
            {num}
          </div>
        ))}
        
        <div className="text-center font-semibold text-gray-600">Ч/У*</div>
        <div className="text-center p-3 bg-gray-300 rounded-lg font-bold">2</div>
        <div className="text-center font-semibold text-gray-600">Ч/М</div>
        <div className="text-center p-3 bg-gray-300 rounded-lg font-bold">4</div>
        <div className="text-center font-semibold text-gray-600">П/Ч</div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <Card className="border-emerald-200 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-emerald-100 to-teal-100">
          <CardTitle className="text-emerald-800 flex items-center gap-2">
            <Sun className="w-6 h-6" />
            Расчет ведических временных периодов
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="space-y-6">
            <Astrological_Grid />
            
            <div className="text-center">
              <h3 className="text-lg font-semibold text-emerald-800 mb-4">
                Выберите дату для расчета благоприятных и неблагоприятных периодов
              </h3>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className="w-full max-w-sm justify-start text-left font-normal"
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {selectedDate ? format(selectedDate, 'dd MMMM yyyy, EEEE', { locale: ru }) : 'Выберите дату'}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={selectedDate}
                    onSelect={setSelectedDate}
                    initialFocus
                    locale={ru}
                  />
                </PopoverContent>
              </Popover>
            </div>
            
            <Button 
              onClick={calculateVedicTimes}
              disabled={!selectedDate}
              className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700"
            >
              Рассчитать ведические периоды
            </Button>
          </div>
        </CardContent>
      </Card>

      {vedicTimes && (
        <>
          <Card className="border-emerald-200 shadow-lg">
            <CardHeader className="bg-gradient-to-r from-emerald-100 to-teal-100">
              <CardTitle className="text-emerald-800 flex items-center gap-2">
                <Moon className="w-5 h-5" />
                Ведические периоды на {vedicTimes.dayOfWeek}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <TimePeriodsGrid />
            </CardContent>
          </Card>

          <div className="grid md:grid-cols-2 gap-4">
            <VedicTimeCard 
              timeKey="rahuKala"
              period={vedicTimes.periods.rahuKala}
              description={vedicTimeDescriptions.rahuKala}
            />
            <VedicTimeCard 
              timeKey="abhijitMuhurta"
              period={vedicTimes.periods.abhijitMuhurta}
              description={vedicTimeDescriptions.abhijitMuhurta}
            />
            <VedicTimeCard 
              timeKey="gulikaKala"
              period={vedicTimes.periods.gulikaKala}
              description={vedicTimeDescriptions.gulikaKala}
            />
            <VedicTimeCard 
              timeKey="yamaghanda"
              period={vedicTimes.periods.yamaghanda}
              description={vedicTimeDescriptions.yamaghanda}
            />
          </div>

          <Card className="border-indigo-200 bg-gradient-to-br from-indigo-50 to-purple-50">
            <CardHeader>
              <CardTitle className="text-indigo-800">Рекомендации по времени</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm text-indigo-700">
                <p>
                  <strong>Абхиджит Мухурта</strong> - лучшее время для начала важных дел, подписания договоров, 
                  принятия решений и любых благоприятных начинаний.
                </p>
                <p>
                  <strong>Раху Кала и Ямаганда</strong> - избегайте начинания новых проектов, путешествий и 
                  важных встреч в эти периоды.
                </p>
                <p>
                  <strong>Гулика Кала</strong> - подходит для завершения старых дел, но не для новых начинаний.
                </p>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};

export default VedicTimesCalculator;