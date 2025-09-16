import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { numberDescriptions } from '../mock';
import { Target, Heart, Crown } from 'lucide-react';

const PersonalNumbersResult = ({ results }) => {
  const { lifePathNumber, destinyNumber, soulNumber, date } = results;

  const NumberCard = ({ number, title, icon: Icon, description, colorScheme }) => {
    const desc = numberDescriptions[number];
    return (
      <Card 
        className={`border-2 transition-all duration-300 hover:shadow-lg hover:scale-105`}
        style={{ 
          borderColor: desc?.color || colorScheme.border,
          backgroundColor: (desc?.color || colorScheme.bg) + '10'
        }}
      >
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg" style={{ color: desc?.color || colorScheme.text }}>
            <Icon className="w-5 h-5" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center mb-4">
            <div 
              className="text-4xl font-bold mb-2"
              style={{ color: desc?.color || colorScheme.text }}
            >
              {number}
            </div>
            <Badge variant="secondary" className="mb-3">
              {desc?.title || 'Неизвестно'}
            </Badge>
          </div>
          <p className="text-sm text-gray-700 leading-relaxed">
            {description}
          </p>
        </CardContent>
      </Card>
    );
  };

  const DetailedDescription = ({ number }) => {
    const desc = numberDescriptions[number];
    if (!desc) return null;

    return (
      <Card 
        className="border-2 shadow-lg"
        style={{ 
          borderColor: desc.color + '40',
          backgroundColor: desc.color + '08'
        }}
      >
        <CardHeader>
          <CardTitle style={{ color: desc.color }}>
            Число {number}: {desc.title}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-gray-700">{desc.description}</p>
          
          <div>
            <h4 className="font-semibold mb-2" style={{ color: desc.color }}>Основные черты:</h4>
            <div className="flex flex-wrap gap-2">
              {desc.traits.map((trait, index) => (
                <Badge 
                  key={index} 
                  variant="outline" 
                  style={{ borderColor: desc.color + '60', color: desc.color }}
                >
                  {trait}
                </Badge>
              ))}
            </div>
          </div>
          
          <div 
            className="p-4 rounded-lg"
            style={{ backgroundColor: desc.color + '15' }}
          >
            <h4 className="font-semibold mb-2" style={{ color: desc.color }}>Рекомендации:</h4>
            <p className="text-sm" style={{ color: desc.color + 'CC' }}>{desc.recommendations}</p>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      <Card className="border-emerald-200 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-emerald-100 to-teal-100">
          <CardTitle className="text-emerald-800">Результат расчета личных чисел</CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid md:grid-cols-3 gap-4 mb-6">
            <NumberCard
              number={lifePathNumber}
              title="Число жизненного пути"
              icon={Target}
              description="Определяет вашу основную цель в жизни и путь развития"
              colorScheme={{ border: '#3B82F6', bg: '#DBEAFE', text: '#1E40AF' }}
            />
            <NumberCard
              number={destinyNumber}
              title="Число судьбы"
              icon={Crown}
              description="Показывает ваши таланты и предназначение"
              colorScheme={{ border: '#8B5CF6', bg: '#EDE9FE', text: '#5B21B6' }}
            />
            <NumberCard
              number={soulNumber}
              title="Число души"
              icon={Heart}
              description="Отражает ваши внутренние желания и мотивы"
              colorScheme={{ border: '#EC4899', bg: '#FCE7F3', text: '#BE185D' }}
            />
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <h3 className="text-xl font-semibold text-emerald-800">Подробные описания ваших чисел:</h3>
        
        <DetailedDescription number={lifePathNumber} />
        {destinyNumber !== lifePathNumber && <DetailedDescription number={destinyNumber} />}
        {soulNumber !== lifePathNumber && soulNumber !== destinyNumber && (
          <DetailedDescription number={soulNumber} />
        )}
      </div>

      <Card className="border-emerald-200 bg-gradient-to-br from-emerald-50 to-teal-50">
        <CardHeader>
          <CardTitle className="text-emerald-800 flex items-center gap-2">
            <Target className="w-5 h-5" />
            Общие рекомендации
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm text-emerald-700">
            <p>
              <strong>Число жизненного пути ({lifePathNumber}):</strong> Это ваша основная миссия в жизни. 
              Развивайте качества этого числа для достижения гармонии.
            </p>
            <p>
              <strong>Число судьбы ({destinyNumber}):</strong> Указывает на ваши природные таланты. 
              Используйте их для реализации жизненных целей.
            </p>
            <p>
              <strong>Число души ({soulNumber}):</strong> Ваш внутренний мотиватор. 
              Прислушивайтесь к внутреннему голосу для принятия важных решений.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PersonalNumbersResult;