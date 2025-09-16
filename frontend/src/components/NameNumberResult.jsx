import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { numberDescriptions } from '../mock';
import { User, Sparkles } from 'lucide-react';

const NameNumberResult = ({ results }) => {
  const { name, nameNumber } = results;
  const description = numberDescriptions[nameNumber];

  return (
    <div className="space-y-6">
      <Card className="border-emerald-200 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-emerald-100 to-teal-100">
          <CardTitle className="text-emerald-800 flex items-center gap-2">
            <User className="w-5 h-5" />
            Результат расчета числа имени
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="text-center mb-6">
            <h3 className="text-xl text-emerald-700 mb-2">Имя: <strong>{name}</strong></h3>
            <div 
              className="text-6xl font-bold mb-4"
              style={{ color: description?.color || '#059669' }}
            >
              {nameNumber}
            </div>
            {description && (
              <Badge 
                variant="secondary" 
                className="text-lg px-4 py-2"
                style={{ backgroundColor: description.color + '20', color: description.color }}
              >
                {description.title}
              </Badge>
            )}
          </div>
          
          {description && (
            <div className="text-center">
              <p className="text-gray-700 text-lg">{description.description}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {description && (
        <Card 
          className="border-2 shadow-lg"
          style={{ 
            borderColor: description.color + '40',
            backgroundColor: description.color + '08'
          }}
        >
          <CardHeader>
            <CardTitle className="flex items-center gap-2" style={{ color: description.color }}>
              <Sparkles className="w-5 h-5" />
              Подробное описание числа {nameNumber}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2" style={{ color: description.color }}>Основные черты характера:</h4>
              <div className="flex flex-wrap gap-2 mb-4">
                {description.traits.map((trait, index) => (
                  <Badge 
                    key={index} 
                    variant="outline" 
                    style={{ borderColor: description.color + '60', color: description.color }}
                  >
                    {trait}
                  </Badge>
                ))}
              </div>
            </div>
            
            <div 
              className="p-4 rounded-lg"
              style={{ backgroundColor: description.color + '15' }}
            >
              <h4 className="font-semibold mb-2" style={{ color: description.color }}>Рекомендации для развития:</h4>
              <p style={{ color: description.color + 'CC' }}>{description.recommendations}</p>
            </div>
            
            <div 
              className="p-4 rounded-lg"
              style={{ backgroundColor: description.color + '10' }}
            >
              <h4 className="font-semibold mb-2" style={{ color: description.color }}>Значение числа имени:</h4>
              <p className="text-sm" style={{ color: description.color + 'CC' }}>
                Число имени влияет на то, как вас воспринимают окружающие и какую энергию вы излучаете в мир. 
                Оно может отличаться от числа жизненного пути, показывая разные аспекты вашей личности.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="border-emerald-200 bg-gradient-to-br from-emerald-50 to-teal-50">
        <CardHeader>
          <CardTitle className="text-emerald-800">Интерпретация числа имени</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm text-emerald-700">
            <p>
              Число имени <strong>{nameNumber}</strong> раскрывает, как вы проявляетесь во внешнем мире 
              и какое впечатление производите на людей.
            </p>
            <p>
              Если число имени отличается от числа жизненного пути, это может указывать на внутренний 
              конфликт или на необходимость гармонизации различных аспектов личности.
            </p>
            <p>
              Медитируйте на энергию этого числа и используйте его силу для достижения целей в 
              профессиональной и социальной сферах.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default NameNumberResult;