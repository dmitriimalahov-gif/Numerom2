import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Loader, Sparkles, Star, Crown, Calculator, Gem, Zap, Grid3X3 } from 'lucide-react';
import { useAuth } from './AuthContext';
import axios from 'axios';
import { getBackendUrl } from '../utils/backendUrl';

const VedicNumerology = () => {
  const { user } = useAuth();
  const [name, setName] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('numbers');

  const backendUrl = getBackendUrl();

  const calculateVedicNumbers = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${backendUrl}/api/numerology/vedic/comprehensive`, null, {
        params: { name }
      });
      setResults(response.data);
    } catch (error) {
      console.error('Error calculating Vedic numerology:', error);
      setError(error.response?.data?.detail || 'Ошибка при расчете');
    } finally {
      setLoading(false);
    }
  };

  const getVedicColorForNumber = (number) => {
    const colors = {
      1: 'bg-orange-100 border-orange-300 text-orange-800', // Surya
      2: 'bg-gray-100 border-gray-300 text-gray-800',       // Chandra
      3: 'bg-yellow-100 border-yellow-300 text-yellow-800', // Guru
      4: 'bg-amber-100 border-amber-700 text-amber-800',    // Rahu
      5: 'bg-green-100 border-green-300 text-green-800',    // Budha
      6: 'bg-pink-100 border-pink-300 text-pink-800',       // Shukra
      7: 'bg-purple-100 border-purple-300 text-purple-800', // Ketu
      8: 'bg-slate-100 border-slate-400 text-slate-800',    // Shani
      9: 'bg-red-100 border-red-300 text-red-800'           // Mangal
    };
    return colors[number] || 'bg-gray-100 border-gray-300 text-gray-800';
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader className="w-6 h-6 animate-spin mr-2" />
          <span>Рассчитываем ведическую нумерологию...</span>
        </CardContent>
      </Card>
    );
  }

  const renderNumbersTab = () => (
    <>
      {/* Name Input */}
      <Card>
        <CardHeader>
          <CardTitle>Персональные Расчеты</CardTitle>
          <CardDescription>
            Для более точного анализа введите ваше полное имя (необязательно)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Полное имя (опционально)</Label>
            <Input
              id="name"
              type="text"
              placeholder="Ваше полное имя"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Button 
            onClick={calculateVedicNumbers} 
            className="w-full numerology-gradient"
            disabled={loading}
          >
            <Sparkles className="w-4 h-4 mr-2" />
            Рассчитать Ведическую Нумерологию
          </Button>
        </CardContent>
      </Card>

      {results && (
        <>
          {/* Core Vedic Numbers */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Star className="w-5 h-5 mr-2" />
                Основные Ведические Числа
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className={`p-4 rounded-lg border-2 ${getVedicColorForNumber(results.janma_ank)}`}>
                  <div className="text-center">
                    <div className="text-2xl font-bold mb-2">{results.janma_ank}</div>
                    <div className="font-semibold">जन्म अंक</div>
                    <div className="text-sm">Janma Ank</div>
                    <div className="text-xs mt-1">Число Рождения</div>
                  </div>
                </div>

                <div className={`p-4 rounded-lg border-2 ${getVedicColorForNumber(results.bhagya_ank)}`}>
                  <div className="text-center">
                    <div className="text-2xl font-bold mb-2">{results.bhagya_ank}</div>
                    <div className="font-semibold">भाग्य अंक</div>
                    <div className="text-sm">Bhagya Ank</div>
                    <div className="text-xs mt-1">Число Судьбы</div>
                  </div>
                </div>

                <div className={`p-4 rounded-lg border-2 ${getVedicColorForNumber(results.atma_ank)}`}>
                  <div className="text-center">
                    <div className="text-2xl font-bold mb-2">{results.atma_ank}</div>
                    <div className="font-semibold">आत्मा अंक</div>
                    <div className="text-sm">Atma Ank</div>
                    <div className="text-xs mt-1">Число Души</div>
                  </div>
                </div>

                {name && (
                  <div className={`p-4 rounded-lg border-2 ${getVedicColorForNumber(results.nama_ank)}`}>
                    <div className="text-center">
                      <div className="text-2xl font-bold mb-2">{results.nama_ank}</div>
                      <div className="font-semibold">नाम अंक</div>
                      <div className="text-sm">Nama Ank</div>
                      <div className="text-xs mt-1">Число Имени</div>
                    </div>
                  </div>
                )}

                <div className={`p-4 rounded-lg border-2 ${getVedicColorForNumber(results.shakti_ank)}`}>
                  <div className="text-center">
                    <div className="text-2xl font-bold mb-2">{results.shakti_ank}</div>
                    <div className="font-semibold">शक्ति अंक</div>
                    <div className="text-sm">Shakti Ank</div>
                    <div className="text-xs mt-1">Число Силы</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Graha Shakti */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Zap className="w-5 h-5 mr-2" />
                Грах Шакти (ग्रह शक्ति) - Планетарная Сила
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(results.graha_shakti).map(([graha, power], index) => (
                  <div key={graha} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <div>
                      <div className="font-medium">{graha}</div>
                      <div className="text-xs text-muted-foreground">
                        {graha.includes('Surya') && 'Лидерство'}
                        {graha.includes('Chandra') && 'Эмоции'}
                        {graha.includes('Guru') && 'Мудрость'}
                        {graha.includes('Rahu') && 'Амбиции'}
                        {graha.includes('Budha') && 'Интеллект'}
                        {graha.includes('Shukra') && 'Любовь'}
                        {graha.includes('Ketu') && 'Духовность'}
                        {graha.includes('Shani') && 'Дисциплина'}
                        {graha.includes('Mangal') && 'Энергия'}
                      </div>
                    </div>
                    <Badge 
                      variant={power > 0 ? "default" : "secondary"}
                      className={power > 2 ? "bg-green-600" : power > 0 ? "bg-yellow-600" : ""}
                    >
                      {power}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Planetary Periods */}
          <Card>
            <CardHeader>
              <CardTitle>Планетарные Периоды</CardTitle>
              <CardDescription>Текущие планетарные влияния</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-primary/10 rounded-lg">
                  <h4 className="font-semibold mb-2">महादशा (Mahadasha)</h4>
                  <div className="text-2xl font-bold text-primary">{results.mahadasha}</div>
                  <p className="text-sm text-muted-foreground mt-2">Основной планетарный период</p>
                </div>
                
                <div className="p-4 bg-secondary/10 rounded-lg">
                  <h4 className="font-semibold mb-2">अन्तर्दशा (Antardasha)</h4>
                  <div className="text-2xl font-bold text-secondary">{results.antardasha}</div>
                  <p className="text-sm text-muted-foreground mt-2">Второстепенный период</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </>
  );

  const renderYantraTab = () => (
    <>
      {results && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Grid3X3 className="w-5 h-5 mr-2" />
              Ведическая Янтра (यन्त्र)
            </CardTitle>
            <CardDescription>
              Магический квадрат с планетарными соответствиями
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="max-w-md mx-auto mb-6">
              <div className="grid grid-cols-3 gap-2">
                {results.yantra_matrix.map((row, rowIndex) =>
                  row.map((cell, colIndex) => {
                    const number = (rowIndex * 3) + colIndex + 1;
                    const grahaName = Object.values(results.graha_names)[number - 1];
                    
                    return (
                      <div
                        key={`${rowIndex}-${colIndex}`}
                        className={`
                          aspect-square border-2 rounded-lg p-2 text-center
                          ${getVedicColorForNumber(number)}
                          transition-all hover:shadow-md hover:scale-105 cursor-pointer
                        `}
                        onClick={() => setActiveTab('interpretations')}
                      >
                        <div className="text-xs mb-1">{number}</div>
                        <div className="text-lg font-bold">
                          {cell || '-'}
                        </div>
                        <div className="text-xs leading-tight" style={{fontSize: '0.6rem'}}>
                          {grahaName?.split('(')[1]?.replace(')', '') || ''}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Yantra Analysis */}
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Горизонтали</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-0">
                    {results.yantra_sums.horizontal.map((sum, index) => (
                      <div key={index} className="flex justify-between text-sm">
                        <span>Строка {index + 1}:</span>
                        <Badge variant="outline">{sum}</Badge>
                      </div>
                    ))}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Вертикали</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-0">
                    {results.yantra_sums.vertical.map((sum, index) => (
                      <div key={index} className="flex justify-between text-sm">
                        <span>Вертикаль {index + 1}:</span>
                        <Badge variant="outline">{sum}</Badge>
                      </div>
                    ))}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Диагонали</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="flex justify-between text-sm">
                      <span>Главная:</span>
                      <Badge variant="outline">{results.yantra_sums.diagonal[0]}</Badge>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Побочная:</span>
                      <Badge variant="outline">{results.yantra_sums.diagonal[1]}</Badge>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </>
  );

  const renderRemediesTab = () => (
    <>
      {results && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Upayas */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center">
                <Star className="w-4 h-4 mr-2" />
                उपाय (Upayas)
              </CardTitle>
              <CardDescription>Ведические средства</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {results.upayas.map((upaya, index) => (
                  <div key={index} className="p-3 bg-green-50 rounded-lg text-sm">
                    {upaya}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Mantras */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center">
                <Sparkles className="w-4 h-4 mr-2" />
                मन्त्र (Mantras)
              </CardTitle>
              <CardDescription>Священные звуки</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {results.mantras.map((mantra, index) => (
                  <div key={index} className="p-3 bg-blue-50 rounded-lg text-sm font-mono">
                    {mantra}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Gemstones */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center">
                <Gem className="w-4 h-4 mr-2" />
                रत्न (Ratnas)
              </CardTitle>
              <CardDescription>Драгоценные камни</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {results.gemstones.map((gemstone, index) => (
                  <div key={index} className="p-3 bg-purple-50 rounded-lg text-sm">
                    {gemstone}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </>
  );

  const renderInterpretationsTab = () => (
    <>
      {results ? (
        <Card>
          <CardHeader>
            <CardTitle>🔮 Интерпретации и Значения</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold mb-2">Ваше главное число: {results.janma_ank}</h4>
                <p className="text-sm text-blue-800">
                  {getNumberInterpretation(results.janma_ank)}
                </p>
              </div>
              
              <div className="p-4 bg-purple-50 rounded-lg">
                <h4 className="font-semibold mb-2">Число судьбы: {results.bhagya_ank}</h4>
                <p className="text-sm text-purple-800">
                  {getDestinyInterpretation(results.bhagya_ank)}
                </p>
              </div>

              <div className="p-4 bg-orange-50 rounded-lg">
                <h4 className="font-semibold mb-2">Планетарная совместимость</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <h5 className="text-sm font-medium mb-1">Благоприятные планеты:</h5>
                    <div className="text-xs space-y-1">
                      {getFavorablePlanets(results.janma_ank).map((planet, idx) => (
                        <div key={idx} className="flex items-center gap-2">
                          <span>{planet.symbol}</span>
                          <span>{planet.name}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h5 className="text-sm font-medium mb-1">Сложные планеты:</h5>
                    <div className="text-xs space-y-1">
                      {getChallengingPlanets(results.janma_ank).map((planet, idx) => (
                        <div key={idx} className="flex items-center gap-2">
                          <span>{planet.symbol}</span>
                          <span>{planet.name}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-6 text-center text-gray-600">
            Сначала рассчитайте ведическую нумерологию на вкладке "Числа"
          </CardContent>
        </Card>
      )}
    </>
  );

  const getNumberInterpretation = (number) => {
    const interpretations = {
      1: "Число Солнца. Вы прирожденный лидер с сильной волей и независимым характером. Стремитесь к успеху и признанию.",
      2: "Число Луны. Вы чувствительны, интуитивны и эмоциональны. Хорошо работаете в команде и цените гармонию.",
      3: "Число Юпитера. Вы оптимистичны, мудры и щедры. Обладаете даром учителя и стремитесь помогать другим.",
      4: "Число Раху. Вы практичны, надежны и методичны. Цените стабильность и умеете планировать на долгосрочную перспективу.",
      5: "Число Меркурия. Вы коммуникабельны, любознательны и адаптивны. Любите путешествия и новые знания.",
      6: "Число Венеры. Вы артистичны, красивы и любите гармонию. Цените красоту и комфорт в жизни.",
      7: "Число Кету. Вы духовны, мистичны и интуитивны. Склонны к философии и поиску глубокого смысла.",
      8: "Число Сатурна. Вы дисциплинированы, амбициозны и настойчивы. Достигаете успеха через упорный труд.",
      9: "Число Марса. Вы энергичны, храбры и решительны. Обладаете лидерскими качествами и боевым духом."
    };
    return interpretations[number] || "Особая энергия, требующая индивидуального анализа.";
  };

  const getDestinyInterpretation = (number) => {
    const interpretations = {
      1: "Ваша судьба - быть первопроходцем и лидером. Вам предназначено вести за собой других.",
      2: "Ваша судьба - создавать гармонию и сотрудничество. Вы призваны объединять людей.",
      3: "Ваша судьба - нести знания и мудрость. Вы учитель по природе.",
      4: "Ваша судьба - строить прочный фундамент. Вы создаете стабильность для других.",
      5: "Ваша судьба - быть мостом между мирами. Вы призваны общаться и объединять.",
      6: "Ваша судьба - создавать красоту и гармонию. Вы приносите эстетику в мир.",
      7: "Ваша судьба - духовный поиск и мистическое познание. Вы мудрец по природе.",
      8: "Ваша судьба - достижение материального успеха и власти. Вы призваны управлять.",
      9: "Ваша судьба - служение человечеству. Вы воин света и добра."
    };
    return interpretations[number] || "Особая миссия, требующая глубокого изучения.";
  };

  const getFavorablePlanets = (number) => {
    const favorable = {
      1: [{ name: "Солнце", symbol: "☀️" }, { name: "Марс", symbol: "♂" }],
      2: [{ name: "Луна", symbol: "🌙" }, { name: "Венера", symbol: "♀" }],
      3: [{ name: "Юпитер", symbol: "♃" }, { name: "Солнце", symbol: "☀️" }],
      4: [{ name: "Раху", symbol: "☊" }, { name: "Меркурий", symbol: "☿" }],
      5: [{ name: "Меркурий", symbol: "☿" }, { name: "Венера", symbol: "♀" }],
      6: [{ name: "Венера", symbol: "♀" }, { name: "Луна", symbol: "🌙" }],
      7: [{ name: "Кету", symbol: "☋" }, { name: "Юпитер", symbol: "♃" }],
      8: [{ name: "Сатурн", symbol: "♄" }, { name: "Раху", symbol: "☊" }],
      9: [{ name: "Марс", symbol: "♂" }, { name: "Солнце", symbol: "☀️" }]
    };
    return favorable[number] || [];
  };

  const getChallengingPlanets = (number) => {
    const challenging = {
      1: [{ name: "Сатурн", symbol: "♄" }, { name: "Кету", symbol: "☋" }],
      2: [{ name: "Марс", symbol: "♂" }, { name: "Сатурн", symbol: "♄" }],
      3: [{ name: "Раху", symbol: "☊" }, { name: "Кету", symbol: "☋" }],
      4: [{ name: "Луна", symbol: "🌙" }, { name: "Венера", symbol: "♀" }],
      5: [{ name: "Сатурн", symbol: "♄" }, { name: "Марс", symbol: "♂" }],
      6: [{ name: "Сатурн", symbol: "♄" }, { name: "Марс", symbol: "♂" }],
      7: [{ name: "Венера", symbol: "♀" }, { name: "Меркурий", symbol: "☿" }],
      8: [{ name: "Солнце", symbol: "☀️" }, { name: "Луна", symbol: "🌙" }],
      9: [{ name: "Сатурн", symbol: "♄" }, { name: "Венера", symbol: "♀" }]
    };
    return challenging[number] || [];
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="numerology-gradient">
        <CardHeader className="text-white">
          <CardTitle className="text-2xl flex items-center">
            <Sparkles className="w-6 h-6 mr-2" />
            Ведическая Нумерология (वैदिक ज्योतिष)
          </CardTitle>
          <CardDescription className="text-white/90">
            Древняя мудрость чисел для самопознания и духовного развития
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="numbers" className="flex items-center gap-2">
            <Star className="w-4 h-4" />
            Числа
          </TabsTrigger>
          <TabsTrigger value="yantra" className="flex items-center gap-2">
            <Grid3X3 className="w-4 h-4" />
            Янтра
          </TabsTrigger>
          <TabsTrigger value="remedies" className="flex items-center gap-2">
            <Gem className="w-4 h-4" />
            Средства
          </TabsTrigger>
          <TabsTrigger value="interpretations" className="flex items-center gap-2">
            <Calculator className="w-4 h-4" />
            Толкования
          </TabsTrigger>
        </TabsList>

        <TabsContent value="numbers" className="space-y-6">
          {renderNumbersTab()}
        </TabsContent>

        <TabsContent value="yantra" className="space-y-6">
          {renderYantraTab()}
        </TabsContent>

        <TabsContent value="remedies" className="space-y-6">
          {renderRemediesTab()}
        </TabsContent>

        <TabsContent value="interpretations" className="space-y-6">
          {renderInterpretationsTab()}
        </TabsContent>
      </Tabs>

      {/* Call to Action */}
      {!results && activeTab === 'numbers' && (
        <Card>
          <CardHeader>
            <CardTitle>Откройте Древнюю Мудрость</CardTitle>
            <CardDescription>
              Ведическая нумерология поможет вам понять:
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <div className="flex items-center">
                  <Crown className="w-4 h-4 mr-2 text-primary" />
                  <span>Ваше духовное предназначение</span>
                </div>
                <div className="flex items-center">
                  <Star className="w-4 h-4 mr-2 text-primary" />
                  <span>Планетарные влияния на жизнь</span>
                </div>
                <div className="flex items-center">
                  <Zap className="w-4 h-4 mr-2 text-primary" />
                  <span>Сильные и слабые стороны</span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center">
                  <Gem className="w-4 h-4 mr-2 text-primary" />
                  <span>Подходящие камни и мантры</span>
                </div>
                <div className="flex items-center">
                  <Sparkles className="w-4 h-4 mr-2 text-primary" />
                  <span>Ведические средства коррекции</span>
                </div>
                <div className="flex items-center">
                  <Calculator className="w-4 h-4 mr-2 text-primary" />
                  <span>Персональная янтра силы</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default VedicNumerology;