import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { mockNameNumber, numberDescriptions } from '../mock';

const NameNumberCalculator = () => {
  const [name, setName] = useState('');
  const [result, setResult] = useState(null);

  const calculateNameNumber = () => {
    if (!name.trim()) {
      alert('Введите имя');
      return;
    }
    
    const nameNumber = mockNameNumber.calculateNameNumber(name);
    setResult({
      name,
      nameNumber
    });
  };

  return (
    <div className="space-y-6">
      <Card className="border-emerald-200 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-emerald-100 to-teal-100">
          <CardTitle className="text-emerald-800">Расчет числа имени</CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Полное имя</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Введите ваше полное имя"
                className="mt-2"
              />
            </div>
            <Button 
              onClick={calculateNameNumber}
              disabled={!name.trim()}
              className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700"
            >
              Рассчитать число имени
            </Button>
          </div>
        </CardContent>
      </Card>

      {result && (
        <Card className="border-emerald-200 shadow-lg">
          <CardHeader className="bg-gradient-to-r from-emerald-100 to-teal-100">
            <CardTitle className="text-emerald-800">Результат</CardTitle>
          </CardHeader>
          <CardContent className="p-6 text-center">
            <h3 className="text-xl mb-4">Имя: <strong>{result.name}</strong></h3>
            <div 
              className="text-6xl font-bold mb-4"
              style={{ color: numberDescriptions[result.nameNumber]?.color || '#059669' }}
            >
              {result.nameNumber}
            </div>
            <Badge 
              className="text-lg px-4 py-2 mb-4"
              style={{ 
                backgroundColor: (numberDescriptions[result.nameNumber]?.color || '#059669') + '20',
                color: numberDescriptions[result.nameNumber]?.color || '#059669'
              }}
            >
              {numberDescriptions[result.nameNumber]?.title || 'Число ' + result.nameNumber}
            </Badge>
            <p className="text-gray-700 mt-4">
              {numberDescriptions[result.nameNumber]?.description || 'Описание числа'}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default NameNumberCalculator;