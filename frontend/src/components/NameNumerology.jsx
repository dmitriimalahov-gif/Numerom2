import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  User, 
  Calculator, 
  Sparkles, 
  Star, 
  Crown, 
  Heart,
  TrendingUp,
  Eye,
  Zap,
  Award
} from 'lucide-react';
import { useAuth } from './AuthContext';

const NameNumerology = () => {
  const { user } = useAuth();
  const [firstName, setFirstName] = useState(user?.name?.split(' ')[0] || '');
  const [lastName, setLastName] = useState(user?.name?.split(' ')[1] || '');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('calculator');

  // Таблица соответствия букв и чисел (Пифагорейская)
  const letterValues = {
    'А': 1, 'Б': 2, 'В': 3, 'Г': 4, 'Д': 5, 'Е': 6, 'Ё': 6, 'Ж': 7, 'З': 8, 'И': 9,
    'Й': 1, 'К': 2, 'Л': 3, 'М': 4, 'Н': 5, 'О': 6, 'П': 7, 'Р': 8, 'С': 9, 'Т': 1,
    'У': 2, 'Ф': 3, 'Х': 4, 'Ц': 5, 'Ч': 6, 'Ш': 7, 'Щ': 8, 'Ъ': 9, 'Ы': 1, 'Ь': 2,
    'Э': 3, 'Ю': 4, 'Я': 5,
    'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9,
    'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'O': 6, 'P': 7, 'Q': 8, 'R': 9,
    'S': 1, 'T': 2, 'U': 3, 'V': 4, 'W': 5, 'X': 6, 'Y': 7, 'Z': 8
  };

  // Функция для расчета числа имени
  const calculateNameNumber = (name) => {
    if (!name) return 0;
    const upperName = name.toUpperCase();
    let sum = 0;
    for (let char of upperName) {
      if (letterValues[char]) {
        sum += letterValues[char];
      }
    }
    return reduceToSingleDigit(sum);
  };

  // Функция для сокращения числа до однозначного
  const reduceToSingleDigit = (num) => {
    while (num > 9 && num !== 11 && num !== 22) {
      num = String(num).split('').reduce((sum, digit) => sum + parseInt(digit), 0);
    }
    return num;
  };

  // Функция для получения гласных
  const getVowels = (name) => {
    const vowels = 'АЕЁИОУЫЭЮЯAEIOUY';
    return name.toUpperCase().split('').filter(char => vowels.includes(char));
  };

  // Функция для получения согласных
  const getConsonants = (name) => {
    const vowels = 'АЕЁИОУЫЭЮЯAEIOUY';
    return name.toUpperCase().split('').filter(char => 
      letterValues[char] && !vowels.includes(char)
    );
  };

  const calculateNameNumerology = () => {
    if (!firstName && !lastName) return;

    setLoading(true);

    const fullName = `${firstName} ${lastName}`.trim();
    
    // Основные расчеты
    const firstNameNumber = calculateNameNumber(firstName);
    const lastNameNumber = calculateNameNumber(lastName);
    const fullNameNumber = calculateNameNumber(fullName);
    
    // Число души (гласные)
    const vowelsFirst = getVowels(firstName);
    const vowelsLast = getVowels(lastName);
    const allVowels = [...vowelsFirst, ...vowelsLast];
    const soulNumber = reduceToSingleDigit(
      allVowels.reduce((sum, vowel) => sum + letterValues[vowel], 0)
    );

    // Число личности (согласные)
    const consonantsFirst = getConsonants(firstName);
    const consonantsLast = getConsonants(lastName);
    const allConsonants = [...consonantsFirst, ...consonantsLast];
    const personalityNumber = reduceToSingleDigit(
      allConsonants.reduce((sum, consonant) => sum + letterValues[consonant], 0)
    );

    // Число зрелости (имя + фамилия + дата рождения)
    const birthSum = user?.birth_date ?
      user.birth_date.replace(/[.-]/g, '').split('').reduce((sum, digit) => sum + parseInt(digit), 0) : 0;
    const maturityNumber = reduceToSingleDigit(fullNameNumber + reduceToSingleDigit(birthSum));

    // Число жизненного пути (только дата рождения)
    const lifePathNumber = user?.birth_date ?
      reduceToSingleDigit(birthSum) : 0;

    // Число баланса (первые буквы имени и фамилии)
    const balanceNumber = reduceToSingleDigit(
      letterValues[firstName?.charAt(0)?.toUpperCase()] + 
      letterValues[lastName?.charAt(0)?.toUpperCase()]
    );

    const calculatedResults = {
      firstName,
      lastName,
      fullName,
      firstNameNumber,
      lastNameNumber,
      fullNameNumber,
      soulNumber,
      personalityNumber,
      maturityNumber,
      lifePathNumber,
      balanceNumber,
      vowels: allVowels,
      consonants: allConsonants,
      letterBreakdown: {
        first: firstName.toUpperCase().split('').map(char => ({
          letter: char,
          value: letterValues[char] || 0
        })),
        last: lastName.toUpperCase().split('').map(char => ({
          letter: char,
          value: letterValues[char] || 0
        }))
      }
    };

    setResults(calculatedResults);
    setLoading(false);
  };

  const getNumberColor = (number) => {
    const colors = {
      1: 'bg-red-100 border-red-300 text-red-800',
      2: 'bg-orange-100 border-orange-300 text-orange-800',
      3: 'bg-yellow-100 border-yellow-300 text-yellow-800',
      4: 'bg-green-100 border-green-300 text-green-800',
      5: 'bg-blue-100 border-blue-300 text-blue-800',
      6: 'bg-indigo-100 border-indigo-300 text-indigo-800',
      7: 'bg-purple-100 border-purple-300 text-purple-800',
      8: 'bg-pink-100 border-pink-300 text-pink-800',
      9: 'bg-gray-100 border-gray-300 text-gray-800',
      11: 'bg-gold-100 border-gold-300 text-gold-800',
      22: 'bg-silver-100 border-silver-300 text-silver-800'
    };
    return colors[number] || 'bg-gray-100 border-gray-300 text-gray-800';
  };

  const getNumberMeaning = (number, type) => {
    const meanings = {
      1: { 
        title: "Лидерство", 
        meaning: "Независимость, инициатива, стремление к первенству. Лидерские качества и новаторство.",
        traits: ["Амбициозность", "Самостоятельность", "Творческий подход"] 
      },
      2: { 
        title: "Сотрудничество", 
        meaning: "Дипломатия, чувствительность, партнерство. Миротворчество и гармония.",
        traits: ["Тактичность", "Чувствительность", "Командная работа"] 
      },
      3: { 
        title: "Творчество", 
        meaning: "Артистизм, общительность, оптимизм. Творческое самовыражение и вдохновение.",
        traits: ["Креативность", "Харизма", "Позитивность"] 
      },
      4: { 
        title: "Стабильность", 
        meaning: "Практичность, организованность, трудолюбие. Системность и надежность.",
        traits: ["Организованность", "Практичность", "Упорство"] 
      },
      5: { 
        title: "Свобода", 
        meaning: "Любознательность, авантюризм, адаптивность. Любовь к переменам и путешествиям.",
        traits: ["Любознательность", "Адаптивность", "Активность"] 
      },
      6: { 
        title: "Гармония", 
        meaning: "Забота, ответственность, семейные ценности. Стремление к красоте и справедливости.",
        traits: ["Заботливость", "Ответственность", "Эстетизм"] 
      },
      7: { 
        title: "Мудрость", 
        meaning: "Духовность, анализ, интуиция. Поиск истины и глубокое понимание.",
        traits: ["Интуитивность", "Аналитичность", "Духовность"] 
      },
      8: { 
        title: "Власть", 
        meaning: "Амбиции, материальный успех, организаторские способности. Стремление к достижениям.",
        traits: ["Амбициозность", "Деловитость", "Управленческие навыки"] 
      },
      9: { 
        title: "Служение", 
        meaning: "Гуманность, мудрость, великодушие. Служение человечеству и высшие идеалы.",
        traits: ["Альтруизм", "Мудрость", "Универсальность"] 
      },
      11: { 
        title: "Мастер-число", 
        meaning: "Интуиция, вдохновение, духовное просветление. Высокая чувствительность и видение.",
        traits: ["Интуиция", "Вдохновение", "Духовность"] 
      },
      22: { 
        title: "Мастер-строитель", 
        meaning: "Масштабные проекты, практическая мудрость, глобальное видение. Способность воплотить мечты в реальность.",
        traits: ["Видение", "Практичность", "Масштабность"] 
      }
    };
    return meanings[number] || { title: "Особое число", meaning: "Уникальная энергия", traits: [] };
  };

  const renderCalculatorTab = () => (
    <div className="space-y-6">
      {/* Форма ввода */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <User className="w-5 h-5 mr-2" />
            Введите ваше имя и фамилию
          </CardTitle>
          <CardDescription>
            Для точного расчета используйте полное имя и фамилию
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="firstName">Имя</Label>
              <Input
                id="firstName"
                type="text"
                placeholder="Введите ваше имя"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="lastName">Фамилия</Label>
              <Input
                id="lastName"
                type="text"
                placeholder="Введите вашу фамилию"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
              />
            </div>
          </div>

          <Button
            onClick={calculateNameNumerology}
            className="w-full numerology-gradient hover:shadow-xl hover:brightness-90 transition-all duration-200"
            disabled={loading || (!firstName && !lastName)}
          >
            <Calculator className="w-4 h-4 mr-2" />
            {loading ? 'Рассчитываем...' : 'Рассчитать нумерологию имени'}
          </Button>
        </CardContent>
      </Card>

      {results && (
        <>
          {/* Основные числа имени */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Star className="w-5 h-5 mr-2" />
                Основные числа имени
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className={`p-4 rounded-lg border-2 text-center ${getNumberColor(results.firstNameNumber)}`}>
                  <div className="text-2xl font-bold mb-2">{results.firstNameNumber}</div>
                  <div className="font-semibold">Число имени</div>
                  <div className="text-sm">{results.firstName}</div>
                </div>

                <div className={`p-4 rounded-lg border-2 text-center ${getNumberColor(results.lastNameNumber)}`}>
                  <div className="text-2xl font-bold mb-2">{results.lastNameNumber}</div>
                  <div className="font-semibold">Число фамилии</div>
                  <div className="text-sm">{results.lastName}</div>
                </div>

                <div className={`p-4 rounded-lg border-2 text-center ${getNumberColor(results.fullNameNumber)}`}>
                  <div className="text-2xl font-bold mb-2">{results.fullNameNumber}</div>
                  <div className="font-semibold">Число полного имени</div>
                  <div className="text-sm">{results.fullName}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Глубокий анализ */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Sparkles className="w-5 h-5 mr-2" />
                Глубокий анализ личности
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className={`p-4 rounded-lg border-2 text-center ${getNumberColor(results.soulNumber)}`}>
                  <div className="text-xl font-bold mb-1">{results.soulNumber}</div>
                  <div className="font-medium text-sm">Число души</div>
                  <div className="text-xs mt-1">Внутренние желания</div>
                </div>

                <div className={`p-4 rounded-lg border-2 text-center ${getNumberColor(results.personalityNumber)}`}>
                  <div className="text-xl font-bold mb-1">{results.personalityNumber}</div>
                  <div className="font-medium text-sm">Число личности</div>
                  <div className="text-xs mt-1">Внешнее впечатление</div>
                </div>

                <div className={`p-4 rounded-lg border-2 text-center ${getNumberColor(results.maturityNumber)}`}>
                  <div className="text-xl font-bold mb-1">{results.maturityNumber}</div>
                  <div className="font-medium text-sm">Число зрелости</div>
                  <div className="text-xs mt-1">Жизненная миссия</div>
                </div>

                <div className={`p-4 rounded-lg border-2 text-center ${getNumberColor(results.balanceNumber)}`}>
                  <div className="text-xl font-bold mb-1">{results.balanceNumber}</div>
                  <div className="font-medium text-sm">Число баланса</div>
                  <div className="text-xs mt-1">Внутренняя гармония</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );

  const renderAnalysisTab = () => (
    <div className="space-y-6">
      {results ? (
        <>
          {/* Детальный анализ чисел */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center">
                  <Crown className="w-4 h-4 mr-2" />
                  Число полного имени ({results.fullNameNumber})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <h4 className="font-semibold text-blue-800">
                      {getNumberMeaning(results.fullNameNumber).title}
                    </h4>
                    <p className="text-sm text-blue-700 mt-1">
                      {getNumberMeaning(results.fullNameNumber).meaning}
                    </p>
                  </div>
                  <div>
                    <h5 className="font-medium text-sm mb-2">Ключевые качества:</h5>
                    <div className="flex flex-wrap gap-1">
                      {getNumberMeaning(results.fullNameNumber).traits.map((trait, idx) => (
                        <Badge key={idx} variant="secondary" className="text-xs">
                          {trait}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center">
                  <Heart className="w-4 h-4 mr-2" />
                  Число души ({results.soulNumber})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="p-3 bg-pink-50 rounded-lg">
                    <h4 className="font-semibold text-pink-800">
                      {getNumberMeaning(results.soulNumber).title}
                    </h4>
                    <p className="text-sm text-pink-700 mt-1">
                      {getNumberMeaning(results.soulNumber).meaning}
                    </p>
                  </div>
                  <div>
                    <h5 className="font-medium text-sm mb-2">Внутренние стремления:</h5>
                    <div className="flex flex-wrap gap-1">
                      {getNumberMeaning(results.soulNumber).traits.map((trait, idx) => (
                        <Badge key={idx} variant="secondary" className="text-xs">
                          {trait}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Буквенный анализ */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Calculator className="w-5 h-5 mr-2" />
                Буквенный анализ
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2">Имя: {results.firstName}</h4>
                  <div className="flex flex-wrap gap-2">
                    {results.letterBreakdown.first.map((item, idx) => (
                      <div key={idx} className="text-center p-2 bg-blue-50 rounded-lg min-w-[40px]">
                        <div className="font-bold">{item.letter}</div>
                        <div className="text-xs text-blue-600">{item.value}</div>
                      </div>
                    ))}
                    <div className="text-center p-2 bg-blue-200 rounded-lg min-w-[60px] ml-2">
                      <div className="font-bold text-blue-800">Σ</div>
                      <div className="text-xs font-bold text-blue-800">{results.firstNameNumber}</div>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">Фамилия: {results.lastName}</h4>
                  <div className="flex flex-wrap gap-2">
                    {results.letterBreakdown.last.map((item, idx) => (
                      <div key={idx} className="text-center p-2 bg-green-50 rounded-lg min-w-[40px]">
                        <div className="font-bold">{item.letter}</div>
                        <div className="text-xs text-green-600">{item.value}</div>
                      </div>
                    ))}
                    <div className="text-center p-2 bg-green-200 rounded-lg min-w-[60px] ml-2">
                      <div className="font-bold text-green-800">Σ</div>
                      <div className="text-xs font-bold text-green-800">{results.lastNameNumber}</div>
                    </div>
                  </div>
                </div>

                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-center">
                    <div>
                      <span className="font-semibold">Гласные буквы:</span>
                      <span className="ml-2">{results.vowels.join(', ')}</span>
                      <Badge className="ml-2">Число души: {results.soulNumber}</Badge>
                    </div>
                  </div>
                  <div className="flex justify-between items-center mt-2">
                    <div>
                      <span className="font-semibold">Согласные буквы:</span>
                      <span className="ml-2">{results.consonants.join(', ')}</span>
                      <Badge className="ml-2">Число личности: {results.personalityNumber}</Badge>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="p-6 text-center text-gray-600">
            Сначала выполните расчет имени на вкладке "Калькулятор"
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderCompatibilityTab = () => (
    <div className="space-y-6">
      {results ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Heart className="w-5 h-5 mr-2" />
              Совместимость по числам имени
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Alert>
                <TrendingUp className="h-4 w-4" />
                <AlertDescription>
                  Для полного анализа совместимости используйте раздел "Совместимость" 
                  с расчетом по датам рождения и именам
                </AlertDescription>
              </Alert>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-blue-50 rounded-lg text-center">
                  <div className="text-2xl font-bold text-blue-800 mb-2">{results.fullNameNumber}</div>
                  <div className="font-semibold">Ваше число имени</div>
                  <div className="text-sm text-blue-600 mt-2">
                    Совместимо с числами: {[1,5,7].includes(results.fullNameNumber % 9 + 1) ? '2,6,9' : '1,5,7'}
                  </div>
                </div>

                <div className="p-4 bg-pink-50 rounded-lg text-center">
                  <div className="text-2xl font-bold text-pink-800 mb-2">{results.soulNumber}</div>
                  <div className="font-semibold">Ваше число души</div>
                  <div className="text-sm text-pink-600 mt-2">
                    Душевная совместимость с: {[1,3,5,7,9].includes(results.soulNumber) ? 'нечетными' : 'четными'} числами
                  </div>
                </div>

                <div className="p-4 bg-green-50 rounded-lg text-center">
                  <div className="text-2xl font-bold text-green-800 mb-2">{results.personalityNumber}</div>
                  <div className="font-semibold">Число личности</div>
                  <div className="text-sm text-green-600 mt-2">
                    Внешняя привлекательность для чисел: {[2,4,6,8].includes(results.personalityNumber) ? '1,3,7' : '2,6,8'}
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-6 text-center text-gray-600">
            Сначала выполните расчет имени на вкладке "Калькулятор"
          </CardContent>
        </Card>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="numerology-gradient">
        <CardHeader className="text-white">
          <CardTitle className="text-2xl flex items-center">
            <User className="w-6 h-6 mr-2" />
            Нумерология Имени и Фамилии
          </CardTitle>
          <CardDescription className="text-white/90">
            Откройте тайны своего имени через числовые вибрации
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3 p-1">
          <TabsTrigger value="calculator" className="flex items-center gap-2 px-2 text-xs sm:text-sm">
            <Calculator className="w-4 h-4" />
            Калькулятор
          </TabsTrigger>
          <TabsTrigger value="analysis" className="flex items-center gap-2 px-2 text-xs sm:text-sm">
            <Eye className="w-4 h-4" />
            Анализ
          </TabsTrigger>
          <TabsTrigger value="compatibility" className="flex items-center gap-2 px-2 text-xs sm:text-sm">
            <Heart className="w-4 h-4" />
            Совместимость
          </TabsTrigger>
        </TabsList>

        <TabsContent value="calculator" className="space-y-6">
          {renderCalculatorTab()}
        </TabsContent>

        <TabsContent value="analysis" className="space-y-6">
          {renderAnalysisTab()}
        </TabsContent>

        <TabsContent value="compatibility" className="space-y-6">
          {renderCompatibilityTab()}
        </TabsContent>
      </Tabs>

      {/* Call to Action */}
      {!results && activeTab === 'calculator' && (
        <Card>
          <CardHeader>
            <CardTitle>Что может рассказать ваше имя?</CardTitle>
            <CardDescription>
              Нумерологический анализ имени поможет узнать:
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <div className="flex items-center">
                  <Crown className="w-4 h-4 mr-2 text-primary" />
                  <span>Ваши скрытые таланты и способности</span>
                </div>
                <div className="flex items-center">
                  <Star className="w-4 h-4 mr-2 text-primary" />
                  <span>Жизненное предназначение</span>
                </div>
                <div className="flex items-center">
                  <Zap className="w-4 h-4 mr-2 text-primary" />
                  <span>Внутренние мотивации и желания</span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center">
                  <Award className="w-4 h-4 mr-2 text-primary" />
                  <span>Впечатление, производимое на других</span>
                </div>
                <div className="flex items-center">
                  <Heart className="w-4 h-4 mr-2 text-primary" />
                  <span>Совместимость с партнерами</span>
                </div>
                <div className="flex items-center">
                  <TrendingUp className="w-4 h-4 mr-2 text-primary" />
                  <span>Пути достижения успеха</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default NameNumerology;