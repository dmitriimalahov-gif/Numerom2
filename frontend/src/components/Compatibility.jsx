import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Loader, Heart, Users, Sparkles, Calculator, CheckCircle, AlertTriangle, Zap, Star, PieChart, Plus, Minus, Info, X } from 'lucide-react';
import { useAuth } from './AuthContext';
import { validateBirthDate } from '../lib/utils';
import axios from 'axios';
import GroupCompatibilityChart from './GroupCompatibilityChart';
import { getBackendUrl } from '../utils/backendUrl';

const Compatibility = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('pair');
  
  // Парная совместимость
  const [formData, setFormData] = useState({
    person1_birth_date: user?.birth_date || '',
    person2_birth_date: '',
    person1_name: user?.full_name || 'Вы',
    person2_name: ''
  });
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Групповая совместимость
  const [groupData, setGroupData] = useState({
    main_person_birth_date: user?.birth_date || '',
    main_person_name: user?.full_name || 'Вы',
    people: [
      { name: '', birth_date: '' }
    ]
  });
  const [groupResults, setGroupResults] = useState(null);
  const [groupLoading, setGroupLoading] = useState(false);
  const [groupError, setGroupError] = useState('');
  const [showFormula, setShowFormula] = useState(null);

  const backendUrl = getBackendUrl();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleGroupChange = (index, field, value) => {
    const newPeople = [...groupData.people];
    newPeople[index] = { ...newPeople[index], [field]: value };
    setGroupData({
      ...groupData,
      people: newPeople
    });
  };

  const addPerson = () => {
    if (groupData.people.length < 5) {
      setGroupData({
        ...groupData,
        people: [...groupData.people, { name: '', birth_date: '' }]
      });
    }
  };

  const removePerson = (index) => {
    if (groupData.people.length > 1) {
      const newPeople = groupData.people.filter((_, i) => i !== index);
      setGroupData({
        ...groupData,
        people: newPeople
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!validateBirthDate(formData.person1_birth_date)) {
      setError('Первая дата рождения должна быть в формате ДД.ММ.ГГГГ');
      return;
    }
    
    if (!validateBirthDate(formData.person2_birth_date)) {
      setError('Вторая дата рождения должна быть в формате ДД.ММ.ГГГГ');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${backendUrl}/api/numerology/compatibility`, formData);
      setResults(response.data);
    } catch (error) {
      console.error('Error calculating compatibility:', error);
      setError(error.response?.data?.detail || 'Ошибка при расчете совместимости');
    } finally {
      setLoading(false);
    }
  };

  const handleGroupSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!validateBirthDate(groupData.main_person_birth_date)) {
      setGroupError('Ваша дата рождения должна быть в формате ДД.ММ.ГГГГ');
      return;
    }

    const validPeople = groupData.people.filter(person => 
      person.name.trim() && validateBirthDate(person.birth_date)
    );

    if (validPeople.length === 0) {
      setGroupError('Добавьте минимум одного человека с корректными данными');
      return;
    }

    setGroupLoading(true);
    setGroupError('');

    try {
      const requestData = {
        main_person_birth_date: groupData.main_person_birth_date,
        main_person_name: groupData.main_person_name,
        people: validPeople
      };

      const response = await axios.post(`${backendUrl}/api/group-compatibility`, requestData, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      setGroupResults(response.data);
    } catch (err) {
      setGroupError(err.response?.data?.detail || 'Ошибка при расчете групповой совместимости');
      console.error('Group compatibility calculation error:', err);
    } finally {
      setGroupLoading(false);
    }
  };

  const getCompatibilityFormula = (person1_date, person2_date, person1_life_path, person2_life_path, compatibility_score) => {
    // Вычисляем числа судьбы из дат рождения
    const calculateLifePath = (birthDate) => {
      const cleanDate = birthDate.replace(/\D/g, '');
      let sum = 0;
      for (let digit of cleanDate) {
        sum += parseInt(digit);
      }
      while (sum > 9 && sum !== 11 && sum !== 22 && sum !== 33) {
        sum = Math.floor(sum / 10) + (sum % 10);
      }
      return sum;
    };

    const person1_calculation = person1_date.replace(/\D/g, '').split('').map(d => parseInt(d)).join(' + ');
    const person2_calculation = person2_date.replace(/\D/g, '').split('').map(d => parseInt(d)).join(' + ');
    
    return {
      person1_formula: `Человек 1: ${person1_date} → ${person1_calculation} = ${person1_life_path}`,
      person2_formula: `Человек 2: ${person2_date} → ${person2_calculation} = ${person2_life_path}`,
      compatibility_formula: `Совместимость = 10 - |${person1_life_path} - ${person2_life_path}| = 10 - ${Math.abs(person1_life_path - person2_life_path)} = ${compatibility_score}`,
      method_description: 'Метод расчёта совместимости основан на разности чисел судьбы партнёров. Чем меньше разность, тем выше совместимость.'
    };
  };

  const getCompatibilityColor = (score) => {
    if (score >= 8) return "border-green-500 text-green-700 bg-green-50";
    if (score >= 5) return "border-yellow-500 text-yellow-700 bg-yellow-50";
    return "border-red-500 text-red-700 bg-red-50";
  };

  const FormulaModal = ({ formula, onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b p-4 flex justify-between items-center">
          <h3 className="text-xl font-bold flex items-center">
            <Calculator className="w-6 h-6 mr-2 text-blue-500" />
            Формула вычисления совместимости
          </h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X className="w-6 h-6" />
          </button>
        </div>
        
        <div className="p-6 space-y-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-semibold text-blue-800 mb-2">📊 Расчёт чисел судьбы:</h4>
            <div className="font-mono text-sm space-y-1">
              <div>{formula.person1_formula}</div>
              <div>{formula.person2_formula}</div>
            </div>
          </div>
          
          <div className="bg-green-50 p-4 rounded-lg">
            <h4 className="font-semibold text-green-800 mb-2">💕 Формула совместимости:</h4>
            <div className="font-mono text-sm">
              {formula.compatibility_formula}
            </div>
          </div>
          
          <div className="bg-yellow-50 p-4 rounded-lg">
            <h4 className="font-semibold text-yellow-800 mb-2">ℹ️ Описание метода:</h4>
            <p className="text-sm">{formula.method_description}</p>
          </div>
          
          <div className="bg-purple-50 p-4 rounded-lg">
            <h4 className="font-semibold text-purple-800 mb-2">📋 Интерпретация результата:</h4>
            <div className="text-sm space-y-1">
              <div>• 8-10 баллов: Высокая совместимость</div>
              <div>• 5-7 баллов: Средняя совместимость</div>
              <div>• 1-4 балла: Низкая совместимость (требует работы)</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const getCompatibilityDescription = (score) => {
    if (score >= 9) return 'Идеальная совместимость';
    if (score >= 8) return 'Отличная совместимость';
    if (score >= 7) return 'Очень хорошая совместимость';
    if (score >= 6) return 'Хорошая совместимость';
    if (score >= 5) return 'Средняя совместимость';
    if (score >= 4) return 'Удовлетворительная совместимость';
    if (score >= 3) return 'Сложная совместимость';
    return 'Очень сложная совместимость';
  };

  const getAdvice = (score) => {
    if (score >= 8) {
      return "Вы прекрасно дополняете друг друга. Ваши числа судьбы создают гармоничное сочетание, способствующее взаимопониманию и поддержке.";
    }
    if (score >= 6) {
      return "У вас хорошие перспективы для отношений. Возможны некоторые различия в подходах к жизни, но они скорее дополняют, чем мешают.";
    }
    if (score >= 4) {
      return "Ваши отношения требуют работы и взаимных компромиссов. Понимание различий в характерах поможет найти общий язык.";
    }
    return "Ваши числа судьбы указывают на значительные различия в жизненных подходах. Потребуется много терпения и понимания для построения гармоничных отношений.";
  };

  const getLifePathDescription = (number) => {
    const descriptions = {
      1: "Лидер, независимый, инициативный",
      2: "Сотрудничество, дипломатия, чувствительность", 
      3: "Творчество, общительность, оптимизм",
      4: "Стабильность, практичность, надежность",
      5: "Свобода, адаптивность, любознательность",
      6: "Забота, ответственность, гармония",
      7: "Духовность, анализ, интуиция",
      8: "Материальный успех, амбиции, власть",
      9: "Гуманность, мудрость, служение"
    };
    return descriptions[number] || "Уникальная энергия";
  };

  const getHarmonyLevel = (score) => {
    if (score >= 8) return "Высокая";
    if (score >= 6) return "Хорошая";
    if (score >= 4) return "Средняя";
    return "Низкая";
  };

  const getHarmonyColor = (score) => {
    if (score >= 8) return "bg-green-200 text-green-800";
    if (score >= 6) return "bg-yellow-200 text-yellow-800";
    if (score >= 4) return "bg-orange-200 text-orange-800";
    return "bg-red-200 text-red-800";
  };

  const getCompatibilityAreas = (num1, num2) => {
    return [
      {
        name: "Эмоциональная связь",
        rating: Math.max(5, 10 - Math.abs(num1 - num2)),
        color: Math.abs(num1 - num2) <= 2 ? "bg-green-500" : Math.abs(num1 - num2) <= 4 ? "bg-yellow-500" : "bg-red-500"
      },
      {
        name: "Интеллектуальное понимание", 
        rating: num1 === num2 ? 10 : (num1 + num2) % 9 + 1,
        color: num1 === num2 ? "bg-green-500" : ((num1 + num2) % 9 + 1) >= 6 ? "bg-yellow-500" : "bg-red-500"
      },
      {
        name: "Жизненные цели",
        rating: 10 - Math.abs((num1 % 3) - (num2 % 3)) * 2,
        color: Math.abs((num1 % 3) - (num2 % 3)) === 0 ? "bg-green-500" : "bg-yellow-500"
      },
      {
        name: "Коммуникация",
        rating: Math.min(10, (num1 + num2)),
        color: (num1 + num2) >= 12 ? "bg-green-500" : (num1 + num2) >= 8 ? "bg-yellow-500" : "bg-red-500"
      }
    ];
  };

  const getStrengths = (score, num1, num2) => {
    const commonStrengths = [
      "Взаимное уважение к индивидуальности",
      "Способность к компромиссам",
      "Общие базовые ценности"
    ];

    if (score >= 7) {
      return [
        "Интуитивное понимание друг друга",
        "Естественная гармония в отношениях", 
        "Взаимодополняющие качества",
        ...commonStrengths
      ];
    } else if (score >= 5) {
      return [
        "Возможность роста через различия",
        "Обучение друг у друга",
        "Баланс противоположных качеств",
        ...commonStrengths
      ];
    } else {
      return [
        "Потенциал для глубоких изменений",
        "Развитие терпения и понимания",
        "Укрепление характера через вызовы",
        ...commonStrengths.slice(0, 1)
      ];
    }
  };

  const getChallenges = (score, num1, num2) => {
    const commonChallenges = [
      "Необходимость постоянной работы над отношениями",
      "Важность открытого общения"
    ];

    if (score >= 7) {
      return [
        "Избегание самодовольства в отношениях",
        "Поддержание индивидуальности партнеров",
        "Сохранение романтики и новизны",
        ...commonChallenges
      ];
    } else if (score >= 5) {
      return [
        "Различия в подходе к решению проблем",
        "Потребность в большем понимании",
        "Работа над принятием различий",
        ...commonChallenges
      ];
    } else {
      return [
        "Значительные различия в характерах",
        "Сложности в понимании друг друга",
        "Необходимость профессиональной помощи",
        "Развитие эмпатии и терпения",
        ...commonChallenges
      ];
    }
  };

  const getPracticalAdvice = (num1, num2) => {
    return {
      understanding: [
        "Изучите числовые характеристики друг друга",
        "Обсуждайте различия открыто и честно", 
        "Практикуйте активное слушание",
        "Находите общие точки соприкосновения"
      ],
      communication: [
        "Используйте 'я-высказывания' вместо обвинений",
        "Выбирайте подходящее время для серьезных разговоров",
        "Практикуйте эмпатию и понимание",
        "Создавайте традиции общения в паре"
      ]
    };
  };

  const getEnergeticCompatibility = (num1, num2) => {
    return [
      {
        name: "Ментальная энергия",
        icon: "🧠",
        level: Math.abs(num1 - num2) <= 2 ? "Высокая" : "Средняя",
        levelColor: Math.abs(num1 - num2) <= 2 ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800",
        description: "Совместимость мыслительных процессов"
      },
      {
        name: "Эмоциональная энергия", 
        icon: "❤️",
        level: (num1 + num2) % 2 === 0 ? "Гармоничная" : "Динамичная",
        levelColor: (num1 + num2) % 2 === 0 ? "bg-pink-100 text-pink-800" : "bg-purple-100 text-purple-800",
        description: "Эмоциональный резонанс между партнерами"
      },
      {
        name: "Физическая энергия",
        icon: "⚡",
        level: num1 === num2 ? "Синхронная" : "Комплементарная",
        levelColor: num1 === num2 ? "bg-blue-100 text-blue-800" : "bg-orange-100 text-orange-800", 
        description: "Совместимость биоритмов и активности"
      }
    ];
  };

  const getPlanetaryCompatibility = (num1, num2) => {
    const planetInfluences = [
      { number: 1, planet: "Солнце", symbol: "☀️" },
      { number: 2, planet: "Луна", symbol: "🌙" },
      { number: 3, planet: "Юпитер", symbol: "♃" },
      { number: 4, planet: "Раху", symbol: "☊" },
      { number: 5, planet: "Меркурий", symbol: "☿" },
      { number: 6, planet: "Венера", symbol: "♀" },
      { number: 7, planet: "Кету", symbol: "☋" },
      { number: 8, planet: "Сатурн", symbol: "♄" },
      { number: 9, planet: "Марс", symbol: "♂" }
    ];

    return planetInfluences.map(planet => {
      const influence1 = num1 === planet.number;
      const influence2 = num2 === planet.number;
      let rating = 5;
      let effect = "Нейтральное";

      if (influence1 && influence2) {
        rating = 10;
        effect = "Сильное взаимное влияние";
      } else if (influence1 || influence2) {
        rating = 8;
        effect = "Одностороннее влияние";
      } else {
        const compatibility = 10 - Math.min(Math.abs(num1 - planet.number), Math.abs(num2 - planet.number));
        rating = Math.max(3, compatibility);
        effect = rating >= 7 ? "Благоприятное" : rating >= 5 ? "Умеренное" : "Слабое";
      }

      return {
        name: planet.planet,
        symbol: planet.symbol,
        influence: `Влияние на числа ${num1} и ${num2}`,
        rating,
        ratingColor: rating >= 8 ? "text-green-600" : rating >= 6 ? "text-yellow-600" : "text-red-600",
        effect
      };
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="numerology-gradient">
        <CardHeader className="text-white">
          <CardTitle className="text-2xl flex items-center">
            <Heart className="w-6 h-6 mr-2" />
            Анализ Совместимости
          </CardTitle>
          <CardDescription className="text-white/90">
            Узнайте совместимость на основе чисел судьбы
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Tabs for different compatibility types */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="pair" className="flex items-center gap-2">
            <Heart className="w-4 h-4" />
            Парная совместимость
          </TabsTrigger>
          <TabsTrigger value="group" className="flex items-center gap-2">
            <PieChart className="w-4 h-4" />
            Групповой анализ
          </TabsTrigger>
        </TabsList>

        {/* Парная совместимость */}
        <TabsContent value="pair">
          <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Users className="w-5 h-5 mr-2" />
            Введите даты рождения
          </CardTitle>
          <CardDescription>
            Формат: ДД.ММ.ГГГГ (например, 15.03.1990)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="person1_name">Имя первого человека</Label>
                <Input
                  id="person1_name"
                  name="person1_name"
                  type="text"
                  placeholder="Ваше имя"
                  value={formData.person1_name}
                  onChange={handleChange}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="person2_name">Имя второго человека</Label>
                <Input
                  id="person2_name"
                  name="person2_name"
                  type="text"
                  placeholder="Имя партнера"
                  value={formData.person2_name}
                  onChange={handleChange}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="person1_birth_date">Первая дата рождения</Label>
                <Input
                  id="person1_birth_date"
                  name="person1_birth_date"
                  type="text"
                  placeholder="15.03.1990"
                  value={formData.person1_birth_date}
                  onChange={handleChange}
                  required
                />
                {user && (
                  <p className="text-xs text-muted-foreground">
                    По умолчанию используется ваша дата рождения
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="person2_birth_date">Вторая дата рождения</Label>
                <Input
                  id="person2_birth_date"
                  name="person2_birth_date"
                  type="text"
                  placeholder="20.07.1985"
                  value={formData.person2_birth_date}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <Button 
              type="submit" 
              className="w-full numerology-gradient"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader className="w-4 h-4 mr-2 animate-spin" />
                  Анализируем совместимость...
                </>
              ) : (
                <>
                  <Heart className="w-4 h-4 mr-2" />
                  Рассчитать совместимость
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      {results && (
        <>
          {/* Main Compatibility Score */}
          <Card>
            <CardHeader className="text-center">
              <CardTitle className="text-2xl">Результат Анализа</CardTitle>
              <CardDescription>Совместимость по числам судьбы</CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <div className="flex justify-center items-center space-x-8 mb-6">
                <div className="text-center">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-numerology-1 to-numerology-2 flex items-center justify-center mb-2">
                    <span className="text-2xl font-bold text-white">{results.person1_life_path}</span>
                  </div>
                  <p className="text-sm text-muted-foreground">Число судьбы 1</p>
                </div>

                <div className="flex flex-col items-center">
                  <Heart className="w-8 h-8 text-primary mb-2" />
                  <div className={`px-6 py-3 rounded-full border-2 ${getCompatibilityColor(results.compatibility_score)}`}>
                    <span className="text-2xl font-bold">{results.compatibility_score}/10</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowFormula(getCompatibilityFormula(
                      formData.person1_birth_date, 
                      formData.person2_birth_date, 
                      results.person1_life_path, 
                      results.person2_life_path, 
                      results.compatibility_score
                    ))}
                    className="mt-2 text-xs text-blue-600 hover:text-blue-800"
                  >
                    <Calculator className="w-3 h-3 mr-1" />
                    Показать формулу
                  </Button>
                </div>

                <div className="text-center">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-numerology-5 to-numerology-6 flex items-center justify-center mb-2">
                    <span className="text-2xl font-bold text-white">{results.person2_life_path}</span>
                  </div>
                  <p className="text-sm text-muted-foreground">Число судьбы 2</p>
                </div>
              </div>

              <Badge variant="secondary" className="text-lg px-4 py-2 mb-4">
                {getCompatibilityDescription(results.compatibility_score)}
              </Badge>

              <p className="text-muted-foreground max-w-2xl mx-auto">
                {results.description}
              </p>
            </CardContent>
          </Card>

          {/* Detailed Analysis */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Sparkles className="w-5 h-5 mr-2" />
                Детальный Анализ Совместимости
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Числовой анализ */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-semibold text-lg">Числовые характеристики:</h4>
                    <div className="space-y-3">
                      <div className="p-3 bg-blue-50 rounded-lg">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">Число судьбы 1:</span>
                          <Badge variant="outline">{results.person1_life_path}</Badge>
                        </div>
                        <p className="text-xs text-gray-600 mt-1">
                          {getLifePathDescription(results.person1_life_path)}
                        </p>
                      </div>
                      <div className="p-3 bg-purple-50 rounded-lg">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">Число судьбы 2:</span>
                          <Badge variant="outline">{results.person2_life_path}</Badge>
                        </div>
                        <p className="text-xs text-gray-600 mt-1">
                          {getLifePathDescription(results.person2_life_path)}
                        </p>
                      </div>
                      <div className="p-3 bg-green-50 rounded-lg">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">Гармония чисел:</span>
                          <Badge className={getHarmonyColor(results.compatibility_score)}>
                            {getHarmonyLevel(results.compatibility_score)}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="font-semibold text-lg">Совместимость по сферам:</h4>
                    <div className="space-y-2">
                      {getCompatibilityAreas(results.person1_life_path, results.person2_life_path).map((area, idx) => (
                        <div key={idx} className="p-3 bg-gray-50 rounded-lg">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium">{area.name}:</span>
                            <div className="flex items-center gap-2">
                              <div className={`w-3 h-3 rounded-full ${area.color}`}></div>
                              <span className="text-sm">{area.rating}/10</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Расширенные советы */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-primary/5 rounded-lg">
                    <h4 className="font-semibold mb-2 flex items-center">
                      <CheckCircle className="w-4 h-4 mr-1 text-green-600" />
                      Сильные стороны союза:
                    </h4>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      {getStrengths(results.compatibility_score, results.person1_life_path, results.person2_life_path).map((strength, idx) => (
                        <li key={idx}>• {strength}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="p-4 bg-orange-50 dark:bg-orange-950/10 rounded-lg">
                    <h4 className="font-semibold mb-2 flex items-center">
                      <AlertTriangle className="w-4 h-4 mr-1 text-orange-600" />
                      Потенциальные вызовы:
                    </h4>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      {getChallenges(results.compatibility_score, results.person1_life_path, results.person2_life_path).map((challenge, idx) => (
                        <li key={idx}>• {challenge}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Практические советы */}
                <div className="p-4 bg-muted rounded-lg">
                  <h4 className="font-semibold mb-3 flex items-center">
                    <Heart className="w-4 h-4 mr-1 text-red-500" />
                    Практические рекомендации для отношений:
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h5 className="font-medium text-sm mb-2">Для улучшения понимания:</h5>
                      <ul className="text-xs text-muted-foreground space-y-1">
                        {getPracticalAdvice(results.person1_life_path, results.person2_life_path).understanding.map((tip, idx) => (
                          <li key={idx}>• {tip}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <h5 className="font-medium text-sm mb-2">Для гармонии в общении:</h5>
                      <ul className="text-xs text-muted-foreground space-y-1">
                        {getPracticalAdvice(results.person1_life_path, results.person2_life_path).communication.map((tip, idx) => (
                          <li key={idx}>• {tip}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Энергетическая совместимость */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Zap className="w-5 h-5 mr-2" />
                Энергетическая совместимость
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {getEnergeticCompatibility(results.person1_life_path, results.person2_life_path).map((aspect, idx) => (
                  <div key={idx} className="text-center p-4 rounded-lg border">
                    <div className="text-2xl mb-2">{aspect.icon}</div>
                    <div className="font-medium text-sm mb-1">{aspect.name}</div>
                    <div className={`text-xs px-2 py-1 rounded ${aspect.levelColor}`}>
                      {aspect.level}
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">{aspect.description}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Планетарная совместимость */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Star className="w-5 h-5 mr-2" />
                Планетарная совместимость
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {getPlanetaryCompatibility(results.person1_life_path, results.person2_life_path).map((planet, idx) => (
                  <div key={idx} className="p-3 rounded-lg border flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="text-xl">{planet.symbol}</div>
                      <div>
                        <div className="font-medium text-sm">{planet.name}</div>
                        <div className="text-xs text-muted-foreground">{planet.influence}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-sm font-medium ${planet.ratingColor}`}>
                        {planet.rating}/10
                      </div>
                      <div className="text-xs text-muted-foreground">{planet.effect}</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Example Card */}
      {!results && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Calculator className="w-5 h-5 mr-2" />
              Как это работает?
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 text-sm text-muted-foreground">
              <p>
                Анализ совместимости основан на сравнении чисел судьбы двух людей. 
                Число судьбы рассчитывается из даты рождения и отражает основные 
                жизненные задачи и характеристики личности.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div className="p-3 bg-muted rounded-lg">
                  <h4 className="font-semibold text-foreground mb-2">Высокая совместимость (8-10):</h4>
                  <p>Числа дополняют друг друга, создавая гармоничный союз</p>
                </div>
                
                <div className="p-3 bg-muted rounded-lg">
                  <h4 className="font-semibold text-foreground mb-2">Средняя совместимость (5-7):</h4>
                  <p>Требуется работа над отношениями, но есть хороший потенциал</p>
                </div>
                
                <div className="p-3 bg-muted rounded-lg">
                  <h4 className="font-semibold text-foreground mb-2">Низкая совместимость (1-4):</h4>
                  <p>Значительные различия требуют терпения и понимания</p>
                </div>
                
                <div className="p-3 bg-muted rounded-lg">
                  <h4 className="font-semibold text-foreground mb-2">Пример расчёта:</h4>
                  <p>15.03.1990 → 1+5+0+3+1+9+9+0 = 28 → 2+8 = 10 → 1</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
        </TabsContent>

        {/* Групповая совместимость */}
        <TabsContent value="group">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Users className="w-5 h-5 mr-2" />
                Групповой анализ совместимости
              </CardTitle>
              <CardDescription>
                Анализ ваших отношений с группой людей (до 5 человек)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleGroupSubmit} className="space-y-4">
                {groupError && (
                  <Alert variant="destructive">
                    <AlertDescription>{groupError}</AlertDescription>
                  </Alert>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="main_person_name">Ваше имя</Label>
                    <Input
                      id="main_person_name"
                      value={groupData.main_person_name}
                      onChange={(e) => setGroupData({...groupData, main_person_name: e.target.value})}
                      placeholder="Ваше имя"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="main_person_birth_date">Ваша дата рождения</Label>
                    <Input
                      id="main_person_birth_date"
                      value={groupData.main_person_birth_date}
                      onChange={(e) => setGroupData({...groupData, main_person_birth_date: e.target.value})}
                      placeholder="15.03.1990"
                      required
                    />
                    {user && (
                      <p className="text-xs text-muted-foreground">
                        По умолчанию используется ваша дата рождения
                      </p>
                    )}
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label className="text-base font-semibold">Люди для анализа</Label>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={addPerson}
                      disabled={groupData.people.length >= 5}
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Добавить
                    </Button>
                  </div>

                  {groupData.people.map((person, index) => (
                    <div key={index} className="p-4 border rounded-lg space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium">Человек {index + 1}</h4>
                        {groupData.people.length > 1 && (
                          <Button
                            type="button"
                            variant="destructive"
                            size="sm"
                            onClick={() => removePerson(index)}
                          >
                            <Minus className="w-4 h-4" />
                          </Button>
                        )}
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div className="space-y-2">
                          <Label htmlFor={`person_name_${index}`}>Имя</Label>
                          <Input
                            id={`person_name_${index}`}
                            value={person.name}
                            onChange={(e) => handleGroupChange(index, 'name', e.target.value)}
                            placeholder="Имя человека"
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor={`person_birth_date_${index}`}>Дата рождения</Label>
                          <Input
                            id={`person_birth_date_${index}`}
                            value={person.birth_date}
                            onChange={(e) => handleGroupChange(index, 'birth_date', e.target.value)}
                            placeholder="15.03.1990"
                            required
                          />
                        </div>
                      </div>
                    </div>
                  ))}

                  <p className="text-sm text-muted-foreground">
                    Максимум 5 человек. Формат даты: ДД.ММ.ГГГГ
                  </p>
                </div>

                <Button 
                  type="submit" 
                  className="w-full numerology-gradient"
                  disabled={groupLoading}
                >
                  {groupLoading ? (
                    <>
                      <Loader className="w-4 h-4 mr-2 animate-spin" />
                      Анализируем группу...
                    </>
                  ) : (
                    <>
                      <PieChart className="w-4 h-4 mr-2" />
                      Рассчитать групповую совместимость
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Результаты групповой совместимости */}
          {groupResults && (
            <GroupCompatibilityChart groupResults={groupResults} />
          )}

          {/* Example Card для групповой совместимости */}
          {!groupResults && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <PieChart className="w-5 h-5 mr-2" />
                  Как работает групповой анализ?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 text-sm text-muted-foreground">
                  <p>
                    Групповой анализ показывает вашу совместимость с несколькими людьми одновременно. 
                    Вы получите интуитивно понятные круговые диаграммы, которые покажут:
                  </p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <h4 className="font-semibold text-foreground mb-2">🎯 Совместимость</h4>
                      <p>Процентное соотношение совместимости с каждым человеком</p>
                    </div>
                    
                    <div className="p-3 bg-green-50 rounded-lg">
                      <h4 className="font-semibold text-foreground mb-2">🤝 Типы отношений</h4>
                      <p>Категории отношений: зеркальные души, партнеры, кармические связи</p>
                    </div>
                    
                    <div className="p-3 bg-purple-50 rounded-lg">
                      <h4 className="font-semibold text-foreground mb-2">🌟 Жизненные пути</h4>
                      <p>Распределение чисел жизненного пути в вашей группе</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
      
      {/* Modal для отображения формул */}
      {showFormula && (
        <FormulaModal formula={showFormula} onClose={() => setShowFormula(null)} />
      )}
    </div>
  );
};

export default Compatibility;