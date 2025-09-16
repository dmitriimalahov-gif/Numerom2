import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { numberDescriptions } from '../mock';
import { Heart, Users, TrendingUp, AlertTriangle } from 'lucide-react';

const CompatibilityResult = ({ results }) => {
  const { partner1, partner2, compatibility } = results;

  const getCompatibilityColor = (score) => {
    if (score >= 85) return 'text-green-600';
    if (score >= 70) return 'text-blue-600';
    if (score >= 55) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getCompatibilityIcon = (score) => {
    if (score >= 85) return Heart;
    if (score >= 70) return Users;
    if (score >= 55) return TrendingUp;
    return AlertTriangle;
  };

  const CompatibilityIcon = getCompatibilityIcon(compatibility.score);

  const PartnerCard = ({ partner, title }) => {
    const description = numberDescriptions[partner.number];
    
    return (
      <Card className="border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50">
        <CardHeader>
          <CardTitle className="text-blue-800 text-lg">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center mb-4">
            <h3 className="text-xl font-semibold text-blue-700 mb-1">{partner.name}</h3>
            <div className="text-3xl font-bold text-blue-800 mb-2">{partner.number}</div>
            {description && (
              <Badge variant="secondary">{description.title}</Badge>
            )}
          </div>
          {description && (
            <p className="text-sm text-blue-700 text-center">{description.description}</p>
          )}
        </CardContent>
      </Card>
    );
  };

  const getCompatibilityAdvice = (score) => {
    if (score >= 85) {
      return {
        title: "Прекрасная совместимость!",
        advice: "У вас отличная энергетическая совместимость. Ваши числа гармонично дополняют друг друга, создавая крепкую основу для отношений.",
        tips: [
          "Поддерживайте открытое общение",
          "Развивайтесь вместе духовно",
          "Цените уникальность партнера"
        ]
      };
    } else if (score >= 70) {
      return {
        title: "Хорошая совместимость",
        advice: "Ваши числа хорошо сочетаются. При взаимном понимании и уважении у вас есть все шансы на гармоничные отношения.",
        tips: [
          "Работайте над пониманием различий",
          "Находите общие интересы",
          "Практикуйте терпение и компромиссы"
        ]
      };
    } else if (score >= 55) {
      return {
        title: "Умеренная совместимость",
        advice: "Ваши числа требуют дополнительных усилий для гармонии. Отношения возможны, но потребуют работы над собой.",
        tips: [
          "Изучайте особенности чисел партнера",
          "Развивайте эмпатию и понимание",
          "Фокусируйтесь на положительных качествах"
        ]
      };
    } else {
      return {
        title: "Сложная совместимость",
        advice: "Ваши числа создают определенные вызовы. Это не означает невозможность отношений, но требует особого внимания к различиям.",
        tips: [
          "Принимайте различия как возможность роста",
          "Работайте над личным развитием",
          "Ищите точки соприкосновения"
        ]
      };
    }
  };

  const advice = getCompatibilityAdvice(compatibility.score);

  return (
    <div className="space-y-6">
      <Card className="border-amber-200 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-amber-100 to-orange-100">
          <CardTitle className="text-amber-800 flex items-center gap-2">
            <Heart className="w-5 h-5" />
            Результат анализа совместимости
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid md:grid-cols-2 gap-6 mb-6">
            <PartnerCard partner={partner1} title="Первый партнер" />
            <PartnerCard partner={partner2} title="Второй партнер" />
          </div>
          
          <div className="text-center">
            <div className="flex justify-center items-center gap-3 mb-4">
              <CompatibilityIcon className={`w-8 h-8 ${getCompatibilityColor(compatibility.score)}`} />
              <div>
                <div className={`text-3xl font-bold ${getCompatibilityColor(compatibility.score)}`}>
                  {compatibility.score}%
                </div>
                <Badge variant="secondary" className="mt-1">
                  {compatibility.level} совместимость
                </Badge>
              </div>
            </div>
            
            <div className="max-w-md mx-auto mb-4">
              <Progress 
                value={compatibility.score} 
                className="h-3"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-pink-50">
        <CardHeader>
          <CardTitle className="text-purple-800 flex items-center gap-2">
            <Users className="w-5 h-5" />
            {advice.title}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-purple-700">{advice.advice}</p>
          
          <div>
            <h4 className="font-semibold text-purple-800 mb-2">Рекомендации для отношений:</h4>
            <ul className="space-y-2">
              {advice.tips.map((tip, index) => (
                <li key={index} className="flex items-start gap-2 text-purple-700">
                  <div className="w-2 h-2 bg-purple-400 rounded-full mt-2 flex-shrink-0"></div>
                  <span className="text-sm">{tip}</span>
                </li>
              ))}
            </ul>
          </div>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-4">
        <Card className="border-green-200 bg-gradient-to-br from-green-50 to-emerald-50">
          <CardHeader>
            <CardTitle className="text-green-800 text-lg">
              Сильные стороны союза
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm text-green-700">
              <p>• Взаимное дополнение энергий чисел {partner1.number} и {partner2.number}</p>
              <p>• Возможность обучения друг у друга</p>
              <p>• Баланс различных качеств личности</p>
              <p>• Потенциал для духовного роста</p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-orange-200 bg-gradient-to-br from-orange-50 to-red-50">
          <CardHeader>
            <CardTitle className="text-orange-800 text-lg">
              Области для работы
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm text-orange-700">
              <p>• Понимание различий в подходах к жизни</p>
              <p>• Гармонизация разных темпераментов</p>
              <p>• Развитие терпения и принятия</p>
              <p>• Поиск общих целей и ценностей</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-indigo-200 bg-gradient-to-br from-indigo-50 to-blue-50">
        <CardHeader>
          <CardTitle className="text-indigo-800">Заключение нумеролога</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-indigo-700 text-sm leading-relaxed">
            Помните, что нумерологическая совместимость - это лишь один из инструментов понимания отношений. 
            Настоящая гармония строится на взаимном уважении, любви, понимании и желании развиваться вместе. 
            Используйте эти знания как руководство, но не как окончательный вердикт. 
            Каждая пара уникальна и способна создать свой собственный путь к счастью.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default CompatibilityResult;