import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { mockPersonalNumbers, numberDescriptions } from '../mock';

const PersonalNumbersCalculator = () => {
  const [birthDate, setBirthDate] = useState('');
  const [results, setResults] = useState(null);

  const calculatePersonalNumbers = () => {
    if (!birthDate.match(/^\d{2}\.\d{2}\.\d{4}$/)) {
      alert('Введите дату в формате ДД.ММ.ГГГГ');
      return;
    }

    const [day, month, year] = birthDate.split('.');
    const dateString = `${year}-${month}-${day}`;
    
    const lifePathNumber = mockPersonalNumbers.getLifePathNumber(dateString);
    const destinyNumber = mockPersonalNumbers.getDestinyNumber(dateString);
    const soulNumber = mockPersonalNumbers.getSoulNumber(dateString);
    
    setResults({
      lifePathNumber,
      destinyNumber,
      soulNumber,
      date: birthDate
    });
  };

  const NumberCard = ({ number, title, description }) => {
    const desc = numberDescriptions[number];
    return (
      <Card 
        className="border-2 transition-all duration-300 hover:shadow-lg"
        style={{ 
          borderColor: desc?.color || '#059669',
          backgroundColor: (desc?.color || '#059669') + '10'
        }}
      >
        <CardHeader>
          <CardTitle style={{ color: desc?.color || '#059669' }}>
            {title}: {number}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-700">{description}</p>
          {desc && (
            <div className="mt-3">
              <h4 className="font-semibold text-sm mb-1" style={{ color: desc.color }}>
                {desc.title}
              </h4>
              <p className="text-xs text-gray-600">{desc.description}</p>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      <Card className="border-emerald-200 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-emerald-100 to-teal-100">
          <CardTitle className="text-emerald-800">Расчет личных чисел</CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="space-y-4">
            <div>
              <Label htmlFor="birthDate">Дата рождения (ДД.ММ.ГГГГ)</Label>
              <Input
                id="birthDate"
                value={birthDate}
                onChange={(e) => setBirthDate(e.target.value)}
                placeholder="10.01.1982"
                className="mt-2"
              />
            </div>
            <Button 
              onClick={calculatePersonalNumbers}
              disabled={!birthDate.trim()}
              className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700"
            >
              Рассчитать личные числа
            </Button>
          </div>
        </CardContent>
      </Card>

      {results && (
        <div className="grid md:grid-cols-3 gap-4">
          <NumberCard
            number={results.lifePathNumber}
            title="Число жизненного пути"
            description="Определяет вашу основную цель в жизни и путь развития"
          />
          <NumberCard
            number={results.destinyNumber}
            title="Число судьбы"
            description="Показывает ваши таланты и предназначение"
          />
          <NumberCard
            number={results.soulNumber}
            title="Число души"
            description="Отражает ваши внутренние желания и мотивы"
          />
        </div>
      )}
    </div>
  );
};

export default PersonalNumbersCalculator;