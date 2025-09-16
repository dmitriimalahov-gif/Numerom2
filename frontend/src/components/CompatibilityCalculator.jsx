import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Progress } from './ui/progress';
import { mockPersonalNumbers, mockCompatibility } from '../mock';

const CompatibilityCalculator = () => {
  const [partner1Name, setPartner1Name] = useState('');
  const [partner1Date, setPartner1Date] = useState('');
  const [partner2Name, setPartner2Name] = useState('');
  const [partner2Date, setPartner2Date] = useState('');
  const [result, setResult] = useState(null);

  const calculateCompatibility = () => {
    if (!partner1Name.trim() || !partner1Date.trim() || !partner2Name.trim() || !partner2Date.trim()) {
      alert('Заполните все поля');
      return;
    }

    if (!partner1Date.match(/^\d{2}\.\d{2}\.\d{4}$/) || !partner2Date.match(/^\d{2}\.\d{2}\.\d{4}$/)) {
      alert('Введите даты в формате ДД.ММ.ГГГГ');
      return;
    }

    const [day1, month1, year1] = partner1Date.split('.');
    const [day2, month2, year2] = partner2Date.split('.');
    
    const dateString1 = `${year1}-${month1}-${day1}`;
    const dateString2 = `${year2}-${month2}-${day2}`;
    
    const partner1Number = mockPersonalNumbers.getLifePathNumber(dateString1);
    const partner2Number = mockPersonalNumbers.getLifePathNumber(dateString2);
    
    const compatibility = mockCompatibility.calculateCompatibility(partner1Number, partner2Number);
    
    setResult({
      partner1: { name: partner1Name, number: partner1Number, date: partner1Date },
      partner2: { name: partner2Name, number: partner2Number, date: partner2Date },
      compatibility
    });
  };

  const getCompatibilityColor = (score) => {
    if (score >= 85) return '#10B981';
    if (score >= 70) return '#3B82F6';
    if (score >= 55) return '#F59E0B';
    return '#EF4444';
  };

  return (
    <div className="space-y-6">
      <Card className="border-emerald-200 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-emerald-100 to-teal-100">
          <CardTitle className="text-emerald-800">Расчет совместимости</CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h3 className="font-semibold text-emerald-800">Первый партнер</h3>
              <div>
                <Label htmlFor="partner1Name">Имя</Label>
                <Input
                  id="partner1Name"
                  value={partner1Name}
                  onChange={(e) => setPartner1Name(e.target.value)}
                  placeholder="Имя первого партнера"
                  className="mt-2"
                />
              </div>
              <div>
                <Label htmlFor="partner1Date">Дата рождения (ДД.ММ.ГГГГ)</Label>
                <Input
                  id="partner1Date"
                  value={partner1Date}
                  onChange={(e) => setPartner1Date(e.target.value)}
                  placeholder="10.01.1982"
                  className="mt-2"
                />
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="font-semibold text-emerald-800">Второй партнер</h3>
              <div>
                <Label htmlFor="partner2Name">Имя</Label>
                <Input
                  id="partner2Name"
                  value={partner2Name}
                  onChange={(e) => setPartner2Name(e.target.value)}
                  placeholder="Имя второго партнера"
                  className="mt-2"
                />
              </div>
              <div>
                <Label htmlFor="partner2Date">Дата рождения (ДД.ММ.ГГГГ)</Label>
                <Input
                  id="partner2Date"
                  value={partner2Date}
                  onChange={(e) => setPartner2Date(e.target.value)}
                  placeholder="15.05.1985"
                  className="mt-2"
                />
              </div>
            </div>
          </div>
          
          <Button 
            onClick={calculateCompatibility}
            disabled={!partner1Name.trim() || !partner1Date.trim() || !partner2Name.trim() || !partner2Date.trim()}
            className="w-full mt-6 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700"
          >
            Рассчитать совместимость
          </Button>
        </CardContent>
      </Card>

      {result && (
        <Card className="border-emerald-200 shadow-lg">
          <CardHeader className="bg-gradient-to-r from-emerald-100 to-teal-100">
            <CardTitle className="text-emerald-800">Результат совместимости</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid md:grid-cols-2 gap-4 mb-6">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <h3 className="font-semibold text-lg">{result.partner1.name}</h3>
                <div className="text-3xl font-bold text-blue-600 my-2">{result.partner1.number}</div>
                <p className="text-sm text-gray-600">{result.partner1.date}</p>
              </div>
              <div className="text-center p-4 bg-pink-50 rounded-lg">
                <h3 className="font-semibold text-lg">{result.partner2.name}</h3>
                <div className="text-3xl font-bold text-pink-600 my-2">{result.partner2.number}</div>
                <p className="text-sm text-gray-600">{result.partner2.date}</p>
              </div>
            </div>

            <div className="text-center">
              <div 
                className="text-4xl font-bold mb-2"
                style={{ color: getCompatibilityColor(result.compatibility.score) }}
              >
                {result.compatibility.score}%
              </div>
              <p className="text-lg font-semibold mb-4">{result.compatibility.level} совместимость</p>
              <Progress 
                value={result.compatibility.score} 
                className="w-full max-w-md mx-auto h-3"
              />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default CompatibilityCalculator;