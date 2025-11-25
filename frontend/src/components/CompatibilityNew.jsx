import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  Loader, Heart, Users, Sparkles, Calculator, CheckCircle, AlertTriangle, 
  Zap, Star, PieChart, Plus, Minus, Info, X, TrendingUp, Shield, Target,
  Activity, Brain, Lightbulb, MessageCircle, Flame
} from 'lucide-react';
import { useAuth } from './AuthContext';
import { validateBirthDate } from '../lib/utils';
import axios from 'axios';
import GroupCompatibilityChart from './GroupCompatibilityChart';
import { getBackendUrl } from '../utils/backendUrl';
import { useOutletContext } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';

const CompatibilityNew = () => {
  const { user } = useAuth();
  const { theme } = useOutletContext();
  const themeConfig = useTheme(theme);
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
    } catch (err) {
      setError(err.response?.data?.detail || 'Произошла ошибка при расчете совместимости');
    } finally {
      setLoading(false);
    }
  };

  const handleGroupSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!validateBirthDate(groupData.main_person_birth_date)) {
      setGroupError('Дата рождения основного человека должна быть в формате ДД.ММ.ГГГГ');
      return;
    }

    for (let i = 0; i < groupData.people.length; i++) {
      if (!groupData.people[i].birth_date) {
        setGroupError(`Укажите дату рождения для человека ${i + 1}`);
        return;
      }
      if (!validateBirthDate(groupData.people[i].birth_date)) {
        setGroupError(`Дата рождения человека ${i + 1} должна быть в формате ДД.ММ.ГГГГ`);
        return;
      }
    }

    setGroupLoading(true);
    setGroupError('');

    try {
      const response = await axios.post(`${backendUrl}/api/numerology/group-compatibility`, groupData);
      console.log('📊 Group compatibility result:', response.data);
      setGroupResults(response.data);
    } catch (err) {
      setGroupError(err.response?.data?.detail || 'Произошла ошибка при расчете групповой совместимости');
    } finally {
      setGroupLoading(false);
    }
  };

  const getCompatibilityColor = (score) => {
    if (score >= 9) return 'border-green-500 bg-green-50 text-green-700';
    if (score >= 7) return 'border-emerald-500 bg-emerald-50 text-emerald-700';
    if (score >= 5) return 'border-yellow-500 bg-yellow-50 text-yellow-700';
    if (score >= 3) return 'border-orange-500 bg-orange-50 text-orange-700';
    return 'border-red-500 bg-red-50 text-red-700';
  };

  const getCompatibilityGradient = (score) => {
    if (score >= 9) return 'from-green-500 to-emerald-500';
    if (score >= 7) return 'from-emerald-500 to-teal-500';
    if (score >= 5) return 'from-yellow-500 to-amber-500';
    if (score >= 3) return 'from-orange-500 to-red-500';
    return 'from-red-500 to-pink-500';
  };

  const getCompatibilityIcon = (score) => {
    if (score >= 9) return <Heart className="w-6 h-6 text-green-500 fill-green-500" />;
    if (score >= 7) return <Sparkles className="w-6 h-6 text-emerald-500" />;
    if (score >= 5) return <Star className="w-6 h-6 text-yellow-500" />;
    if (score >= 3) return <Zap className="w-6 h-6 text-orange-500" />;
    return <AlertTriangle className="w-6 h-6 text-red-500" />;
  };

  const getCompatibilityDescription = (score) => {
    if (score >= 9) return { title: 'Идеальная совместимость', emoji: '💖' };
    if (score >= 8) return { title: 'Отличная совместимость', emoji: '💕' };
    if (score >= 7) return { title: 'Очень хорошая совместимость', emoji: '💗' };
    if (score >= 6) return { title: 'Хорошая совместимость', emoji: '💝' };
    if (score >= 5) return { title: 'Средняя совместимость', emoji: '💛' };
    if (score >= 4) return { title: 'Удовлетворительная совместимость', emoji: '🧡' };
    if (score >= 3) return { title: 'Сложная совместимость', emoji: '💔' };
    return { title: 'Очень сложная совместимость', emoji: '⚠️' };
  };

  const getLifePathDescription = (number) => {
    const descriptions = {
      1: { text: "Лидер, независимый, инициативный", planet: "Surya (Солнце)", color: "from-yellow-400 to-orange-500" },
      2: { text: "Сотрудничество, дипломатия, чувствительность", planet: "Chandra (Луна)", color: "from-blue-200 to-blue-400" }, 
      3: { text: "Творчество, общительность, оптимизм", planet: "Guru (Юпитер)", color: "from-purple-400 to-purple-600" },
      4: { text: "Стабильность, практичность, надежность", planet: "Rahu", color: "from-gray-400 to-gray-600" },
      5: { text: "Свобода, адаптивность, любознательность", planet: "Budh (Меркурий)", color: "from-green-400 to-green-600" },
      6: { text: "Забота, ответственность, гармония", planet: "Shukra (Венера)", color: "from-pink-400 to-pink-600" },
      7: { text: "Духовность, анализ, интуиция", planet: "Ketu", color: "from-indigo-400 to-indigo-600" },
      8: { text: "Материальный успех, амбиции, власть", planet: "Shani (Сатурн)", color: "from-blue-600 to-blue-800" },
      9: { text: "Гуманность, мудрость, служение", planet: "Mangal (Марс)", color: "from-red-500 to-red-700" }
    };
    return descriptions[number] || { text: "Уникальная энергия", planet: "Неизвестно", color: "from-gray-400 to-gray-600" };
  };

  const getCompatibilityAreas = (num1, num2) => {
    return [
      {
        name: "Эмоциональная связь",
        icon: <Heart className="w-5 h-5" />,
        rating: Math.max(5, 10 - Math.abs(num1 - num2)),
        description: "Глубина эмоционального понимания"
      },
      {
        name: "Интеллектуальное понимание", 
        icon: <Brain className="w-5 h-5" />,
        rating: num1 === num2 ? 10 : (num1 + num2) % 9 + 1,
        description: "Совпадение взглядов и мышления"
      },
      {
        name: "Жизненные цели",
        icon: <Target className="w-5 h-5" />,
        rating: 10 - Math.abs((num1 % 3) - (num2 % 3)) * 2,
        description: "Общность целей и стремлений"
      },
      {
        name: "Коммуникация",
        icon: <MessageCircle className="w-5 h-5" />,
        rating: Math.min(10, (num1 + num2)),
        description: "Лёгкость общения и взаимопонимания"
      },
      {
        name: "Энергетика",
        icon: <Zap className="w-5 h-5" />,
        rating: num1 === num2 ? 10 : Math.max(5, 10 - Math.abs(num1 - num2) * 1.5),
        description: "Совместимость энергетических полей"
      },
      {
        name: "Духовная связь",
        icon: <Sparkles className="w-5 h-5" />,
        rating: Math.abs((num1 + num2) % 10),
        description: "Глубина духовного резонанса"
      }
    ];
  };

  const getStrengths = (score, num1, num2) => {
    const commonStrengths = [
      { icon: <Shield className="w-4 h-4" />, text: "Взаимное уважение к индивидуальности" },
      { icon: <CheckCircle className="w-4 h-4" />, text: "Способность к компромиссам" },
      { icon: <Star className="w-4 h-4" />, text: "Общие базовые ценности" }
    ];

    if (score >= 7) {
      return [
        { icon: <Sparkles className="w-4 h-4" />, text: "Интуитивное понимание друг друга" },
        { icon: <Heart className="w-4 h-4" />, text: "Естественная гармония в отношениях" }, 
        { icon: <TrendingUp className="w-4 h-4" />, text: "Взаимодополняющие качества" },
        ...commonStrengths
      ];
    } else if (score >= 5) {
      return [
        { icon: <Lightbulb className="w-4 h-4" />, text: "Возможность роста через различия" },
        { icon: <Activity className="w-4 h-4" />, text: "Обучение друг у друга" },
        { icon: <Zap className="w-4 h-4" />, text: "Баланс противоположных качеств" },
        ...commonStrengths
      ];
    } else {
      return [
        { icon: <Target className="w-4 h-4" />, text: "Потенциал для глубоких изменений" },
        { icon: <Brain className="w-4 h-4" />, text: "Развитие терпения и понимания" },
        { icon: <Flame className="w-4 h-4" />, text: "Укрепление характера через вызовы" },
        ...commonStrengths.slice(0, 1)
      ];
    }
  };

  const getChallenges = (score, num1, num2) => {
    const commonChallenges = [
      { icon: <AlertTriangle className="w-4 h-4" />, text: "Необходимость постоянной работы над отношениями" },
      { icon: <MessageCircle className="w-4 h-4" />, text: "Важность открытого общения" }
    ];

    if (score >= 7) {
      return [
        { icon: <Info className="w-4 h-4" />, text: "Избегание самодовольства в отношениях" },
        { icon: <Users className="w-4 h-4" />, text: "Поддержание индивидуальности партнеров" },
        { icon: <Sparkles className="w-4 h-4" />, text: "Сохранение романтики и новизны" },
        ...commonChallenges
      ];
    } else if (score >= 5) {
      return [
        { icon: <AlertTriangle className="w-4 h-4" />, text: "Преодоление различий в подходах" },
        { icon: <Brain className="w-4 h-4" />, text: "Развитие терпения к особенностям партнера" },
        { icon: <Target className="w-4 h-4" />, text: "Поиск компромиссов в важных вопросах" },
        ...commonChallenges
      ];
    } else {
      return [
        { icon: <Flame className="w-4 h-4" />, text: "Значительные различия в характерах" },
        { icon: <Zap className="w-4 h-4" />, text: "Конфликты из-за разных жизненных ценностей" },
        { icon: <Shield className="w-4 h-4" />, text: "Необходимость глубокой работы над собой" },
        ...commonChallenges
      ];
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="bg-gradient-to-br from-purple-600 via-pink-600 to-red-600 dark:from-purple-900 dark:via-pink-900 dark:to-red-900">
        <CardHeader className="text-white">
          <CardTitle className="text-3xl flex items-center gap-3">
            <Heart className="w-8 h-8" />
            Анализ Совместимости
          </CardTitle>
          <CardDescription className="text-white/90 text-lg">
            Глубокий анализ совместимости на основе ведической нумерологии
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Tabs for different compatibility types */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="pair" className="flex items-center gap-2">
            <Heart className="w-4 h-4" />
            <span className="hidden sm:inline">Парная совместимость</span>
            <span className="sm:hidden">Пара</span>
          </TabsTrigger>
          <TabsTrigger value="group" className="flex items-center gap-2">
            <PieChart className="w-4 h-4" />
            <span className="hidden sm:inline">Групповой анализ</span>
            <span className="sm:hidden">Группа</span>
          </TabsTrigger>
        </TabsList>

        {/* Парная совместимость */}
        <TabsContent value="pair">
          <Card className={themeConfig.surface}>
            <CardHeader>
              <CardTitle className={`flex items-center gap-2 ${themeConfig.text}`}>
                <Users className="w-5 h-5" />
                Введите даты рождения
              </CardTitle>
              <CardDescription className={themeConfig.mutedText}>
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
                    <Label htmlFor="person1_name" className={themeConfig.text}>Имя первого человека</Label>
                    <Input
                      id="person1_name"
                      name="person1_name"
                      type="text"
                      placeholder="Ваше имя"
                      value={formData.person1_name}
                      onChange={handleChange}
                      className={themeConfig.input}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="person2_name" className={themeConfig.text}>Имя второго человека</Label>
                    <Input
                      id="person2_name"
                      name="person2_name"
                      type="text"
                      placeholder="Имя партнера"
                      value={formData.person2_name}
                      onChange={handleChange}
                      className={themeConfig.input}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="person1_birth_date" className={themeConfig.text}>Первая дата рождения</Label>
                    <Input
                      id="person1_birth_date"
                      name="person1_birth_date"
                      type="text"
                      placeholder="15.03.1990"
                      value={formData.person1_birth_date}
                      onChange={handleChange}
                      required
                      className={themeConfig.input}
                    />
                    {user && (
                      <p className={`text-xs ${themeConfig.mutedText}`}>
                        По умолчанию используется ваша дата рождения
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="person2_birth_date" className={themeConfig.text}>Вторая дата рождения</Label>
                    <Input
                      id="person2_birth_date"
                      name="person2_birth_date"
                      type="text"
                      placeholder="20.07.1985"
                      value={formData.person2_birth_date}
                      onChange={handleChange}
                      required
                      className={themeConfig.input}
                    />
                  </div>
                </div>

                <Button 
                  type="submit" 
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
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
              {/* Main Compatibility Score - НОВЫЙ ДИЗАЙН */}
              <Card className={themeConfig.surface}>
                <CardContent className="pt-8">
                  <div className="flex flex-col items-center space-y-6">
                    {/* Числа судьбы */}
                    <div className="flex items-center justify-center gap-8 w-full">
                      <div className="flex flex-col items-center">
                        <div className={`w-20 h-20 rounded-full bg-gradient-to-br ${getLifePathDescription(results.person1_life_path).color} flex items-center justify-center shadow-lg`}>
                          <span className="text-3xl font-bold text-white">{results.person1_life_path}</span>
                        </div>
                        <p className={`text-sm font-medium mt-2 ${themeConfig.text}`}>{formData.person1_name}</p>
                        <p className={`text-xs ${themeConfig.mutedText}`}>{getLifePathDescription(results.person1_life_path).planet}</p>
                      </div>

                      {/* Центральный блок с оценкой */}
                      <div className="flex flex-col items-center">
                        <div className={`relative w-32 h-32 rounded-full bg-gradient-to-br ${getCompatibilityGradient(results.compatibility_score)} flex items-center justify-center shadow-2xl`}>
                          <div className="absolute inset-2 bg-white dark:bg-gray-900 rounded-full flex flex-col items-center justify-center">
                            <span className={`text-4xl font-bold bg-gradient-to-br ${getCompatibilityGradient(results.compatibility_score)} bg-clip-text text-transparent`}>
                              {results.compatibility_score}
                            </span>
                            <span className={`text-xs ${themeConfig.mutedText}`}>из 10</span>
                          </div>
                        </div>
                        <div className="mt-4 flex items-center gap-2">
                          {getCompatibilityIcon(results.compatibility_score)}
                          <Badge variant="secondary" className="text-lg px-4 py-1">
                            {getCompatibilityDescription(results.compatibility_score).emoji} {getCompatibilityDescription(results.compatibility_score).title}
                          </Badge>
                        </div>
                      </div>

                      <div className="flex flex-col items-center">
                        <div className={`w-20 h-20 rounded-full bg-gradient-to-br ${getLifePathDescription(results.person2_life_path).color} flex items-center justify-center shadow-lg`}>
                          <span className="text-3xl font-bold text-white">{results.person2_life_path}</span>
                        </div>
                        <p className={`text-sm font-medium mt-2 ${themeConfig.text}`}>{formData.person2_name}</p>
                        <p className={`text-xs ${themeConfig.mutedText}`}>{getLifePathDescription(results.person2_life_path).planet}</p>
                      </div>
                    </div>

                    {/* Описание */}
                    <p className={`text-center max-w-2xl ${themeConfig.mutedText}`}>
                      {results.description}
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Совместимость по сферам - НОВЫЙ ДИЗАЙН */}
              <Card className={themeConfig.surface}>
                <CardHeader>
                  <CardTitle className={`flex items-center gap-2 ${themeConfig.text}`}>
                    <Sparkles className="w-5 h-5" />
                    Совместимость по сферам жизни
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {getCompatibilityAreas(results.person1_life_path, results.person2_life_path).map((area, idx) => (
                      <div key={idx} className={`p-4 rounded-xl border-2 ${themeConfig.border} ${themeConfig.hover} transition-all`}>
                        <div className="flex items-start gap-3">
                          <div className={`p-2 rounded-lg ${area.rating >= 7 ? 'bg-green-100 text-green-600' : area.rating >= 5 ? 'bg-yellow-100 text-yellow-600' : 'bg-red-100 text-red-600'}`}>
                            {area.icon}
                          </div>
                          <div className="flex-1">
                            <div className="flex justify-between items-start mb-2">
                              <h4 className={`font-semibold ${themeConfig.text}`}>{area.name}</h4>
                              <Badge className={area.rating >= 7 ? 'bg-green-500' : area.rating >= 5 ? 'bg-yellow-500' : 'bg-red-500'}>
                                {area.rating}/10
                              </Badge>
                            </div>
                            <p className={`text-xs ${themeConfig.mutedText}`}>{area.description}</p>
                            <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                              <div 
                                className={`h-2 rounded-full ${area.rating >= 7 ? 'bg-green-500' : area.rating >= 5 ? 'bg-yellow-500' : 'bg-red-500'}`}
                                style={{ width: `${area.rating * 10}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Сильные стороны и вызовы - НОВЫЙ ДИЗАЙН */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className={`${themeConfig.surface} border-2 border-green-200 dark:border-green-800`}>
                  <CardHeader>
                    <CardTitle className={`flex items-center gap-2 text-green-600 dark:text-green-400`}>
                      <CheckCircle className="w-5 h-5" />
                      Сильные стороны
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {getStrengths(results.compatibility_score, results.person1_life_path, results.person2_life_path).map((strength, idx) => (
                        <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-green-50 dark:bg-green-900/20">
                          <div className="text-green-600 dark:text-green-400 mt-0.5">
                            {strength.icon}
                          </div>
                          <p className={`text-sm ${themeConfig.text}`}>{strength.text}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card className={`${themeConfig.surface} border-2 border-orange-200 dark:border-orange-800`}>
                  <CardHeader>
                    <CardTitle className={`flex items-center gap-2 text-orange-600 dark:text-orange-400`}>
                      <AlertTriangle className="w-5 h-5" />
                      Области для внимания
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {getChallenges(results.compatibility_score, results.person1_life_path, results.person2_life_path).map((challenge, idx) => (
                        <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-orange-50 dark:bg-orange-900/20">
                          <div className="text-orange-600 dark:text-orange-400 mt-0.5">
                            {challenge.icon}
                          </div>
                          <p className={`text-sm ${themeConfig.text}`}>{challenge.text}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </>
          )}

          {/* Example Card */}
          {!results && (
            <Card className={themeConfig.surface}>
              <CardHeader>
                <CardTitle className={`flex items-center gap-2 ${themeConfig.text}`}>
                  <Info className="w-5 h-5" />
                  Как это работает?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <p className={themeConfig.mutedText}>
                    Наш анализ совместимости основан на ведической нумерологии и учитывает:
                  </p>
                  <ul className={`space-y-2 ${themeConfig.mutedText}`}>
                    <li className="flex items-start gap-2">
                      <Star className="w-4 h-4 mt-1 text-purple-500" />
                      <span>Числа судьбы обоих партнеров</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <Zap className="w-4 h-4 mt-1 text-yellow-500" />
                      <span>Планетарные влияния на отношения</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <Heart className="w-4 h-4 mt-1 text-pink-500" />
                      <span>Совместимость в разных сферах жизни</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <Sparkles className="w-4 h-4 mt-1 text-blue-500" />
                      <span>Сильные стороны и потенциальные вызовы</span>
                    </li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Групповая совместимость */}
        <TabsContent value="group">
          <Card className={themeConfig.surface}>
            <CardHeader>
              <CardTitle className={`flex items-center gap-2 ${themeConfig.text}`}>
                <PieChart className="w-5 h-5" />
                Групповой анализ совместимости
              </CardTitle>
              <CardDescription className={themeConfig.mutedText}>
                Анализ совместимости одного человека с группой (до 5 человек)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleGroupSubmit} className="space-y-4">
                {groupError && (
                  <Alert variant="destructive">
                    <AlertDescription>{groupError}</AlertDescription>
                  </Alert>
                )}

                {/* Основной человек */}
                <div className={`p-4 rounded-lg border-2 ${themeConfig.border} bg-purple-50 dark:bg-purple-900/20`}>
                  <h3 className={`font-semibold mb-3 ${themeConfig.text}`}>Основной человек</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="main_person_name" className={themeConfig.text}>Имя</Label>
                      <Input
                        id="main_person_name"
                        value={groupData.main_person_name}
                        onChange={(e) => setGroupData({...groupData, main_person_name: e.target.value})}
                        placeholder="Ваше имя"
                        className={themeConfig.isDark ? 'bg-gray-800 border-gray-700' : ''}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="main_person_birth_date" className={themeConfig.text}>Дата рождения</Label>
                      <Input
                        id="main_person_birth_date"
                        value={groupData.main_person_birth_date}
                        onChange={(e) => setGroupData({...groupData, main_person_birth_date: e.target.value})}
                        placeholder="15.03.1990"
                        required
                        className={themeConfig.isDark ? 'bg-gray-800 border-gray-700' : ''}
                      />
                    </div>
                  </div>
                </div>

                {/* Группа людей */}
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <h3 className={`font-semibold ${themeConfig.text}`}>Группа для анализа</h3>
                    <Button
                      type="button"
                      onClick={addPerson}
                      disabled={groupData.people.length >= 5}
                      variant="outline"
                      size="sm"
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      Добавить
                    </Button>
                  </div>

                  {groupData.people.map((person, index) => (
                    <div key={index} className={`p-4 rounded-lg border ${themeConfig.border}`}>
                      <div className="flex justify-between items-start mb-3">
                        <h4 className={`font-medium ${themeConfig.text}`}>Человек {index + 1}</h4>
                        {groupData.people.length > 1 && (
                          <Button
                            type="button"
                            onClick={() => removePerson(index)}
                            variant="ghost"
                            size="sm"
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label className={themeConfig.text}>Имя</Label>
                          <Input
                            value={person.name}
                            onChange={(e) => handleGroupChange(index, 'name', e.target.value)}
                            placeholder="Имя человека"
                            className={themeConfig.isDark ? 'bg-gray-800 border-gray-700' : ''}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label className={themeConfig.text}>Дата рождения</Label>
                          <Input
                            value={person.birth_date}
                            onChange={(e) => handleGroupChange(index, 'birth_date', e.target.value)}
                            placeholder="15.03.1990"
                            required
                            className={themeConfig.isDark ? 'bg-gray-800 border-gray-700' : ''}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <Button 
                  type="submit" 
                  className={`w-full ${themeConfig.gradient} text-white`}
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

          {/* Group Results */}
          {groupResults && (
            <GroupCompatibilityChart groupResults={groupResults} />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CompatibilityNew;

