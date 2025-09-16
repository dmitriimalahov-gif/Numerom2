import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Calendar } from './ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';
import { CalendarIcon, Calculator, Heart, User, Clock } from 'lucide-react';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { mockPersonalNumbers, mockNameNumber, mockCompatibility, numberDescriptions } from '../mock';
import PersonalNumbersResult from './PersonalNumbersResult';
import NameNumberResult from './NameNumberResult';
import CompatibilityResult from './CompatibilityResult';
import VedicTimesCalculator from './VedicTimesCalculator';

const NumerologyCalculator = () => {
  const [selectedDate, setSelectedDate] = useState(null);
  const [name, setName] = useState('');
  const [partner1Name, setPartner1Name] = useState('');
  const [partner2Name, setPartner2Name] = useState('');
  const [partner1Date, setPartner1Date] = useState(null);
  const [partner2Date, setPartner2Date] = useState(null);
  
  const [personalResults, setPersonalResults] = useState(null);
  const [nameResults, setNameResults] = useState(null);
  const [compatibilityResults, setCompatibilityResults] = useState(null);

  const calculatePersonalNumbers = () => {
    if (!selectedDate) return;
    
    const dateString = format(selectedDate, 'yyyy-MM-dd');
    const lifePathNumber = mockPersonalNumbers.getLifePathNumber(dateString);
    const destinyNumber = mockPersonalNumbers.getDestinyNumber(dateString);
    const soulNumber = mockPersonalNumbers.getSoulNumber(dateString);
    
    setPersonalResults({
      lifePathNumber,
      destinyNumber,
      soulNumber,
      date: selectedDate
    });
  };

  const calculateNameNumber = () => {
    if (!name.trim()) return;
    
    const nameNumber = mockNameNumber.calculateNameNumber(name);
    setNameResults({
      name,
      nameNumber
    });
  };

  const calculateCompatibility = () => {
    if (!partner1Name.trim() || !partner2Name.trim() || !partner1Date || !partner2Date) return;
    
    const partner1LifePathNumber = mockPersonalNumbers.getLifePathNumber(format(partner1Date, 'yyyy-MM-dd'));
    const partner2LifePathNumber = mockPersonalNumbers.getLifePathNumber(format(partner2Date, 'yyyy-MM-dd'));
    
    const compatibility = mockCompatibility.calculateCompatibility(partner1LifePathNumber, partner2LifePathNumber);
    
    setCompatibilityResults({
      partner1: { name: partner1Name, number: partner1LifePathNumber, date: partner1Date },
      partner2: { name: partner2Name, number: partner2LifePathNumber, date: partner2Date },
      compatibility
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-emerald-50 to-teal-50">
      <div className="container mx-auto py-8 px-4">
        <div className="text-center mb-8">
          <div className="flex justify-center items-center gap-4 mb-4">
            <div className="relative">
              <div className="w-16 h-16 rounded-full border-4 border-emerald-400 flex items-center justify-center bg-white shadow-lg">
                <span className="text-2xl font-bold text-emerald-700">N</span>
              </div>
              <div className="absolute -top-1 -right-1 w-6 h-6 bg-emerald-500 rounded-full"></div>
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-700 to-teal-700 bg-clip-text text-transparent">
              NUMEROM
            </h1>
          </div>
          <p className="text-lg text-emerald-700 max-w-2xl mx-auto">
            Numbers Reveal - Откройте тайны своих чисел и узнайте больше о своей судьбе, характере и совместимости
          </p>
        </div>

        <Tabs defaultValue="personal" className="max-w-5xl mx-auto">
          <TabsList className="grid w-full grid-cols-4 mb-8">
            <TabsTrigger value="personal" className="flex items-center gap-2">
              <Calculator className="w-4 h-4" />
              Личные числа
            </TabsTrigger>
            <TabsTrigger value="name" className="flex items-center gap-2">
              <User className="w-4 h-4" />
              Число имени
            </TabsTrigger>
            <TabsTrigger value="compatibility" className="flex items-center gap-2">
              <Heart className="w-4 h-4" />
              Совместимость
            </TabsTrigger>
            <TabsTrigger value="vedic-times" className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Ведические времена
            </TabsTrigger>
          </TabsList>

          <TabsContent value="personal" className="space-y-6">
            <Card className="border-emerald-200 shadow-lg">
              <CardHeader className="bg-gradient-to-r from-emerald-100 to-teal-100">
                <CardTitle className="text-emerald-800">Расчет личных чисел</CardTitle>
                <CardDescription>
                  Введите дату рождения для расчета числа жизненного пути, судьбы и души
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6">
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="birthdate">Дата рождения</Label>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          className="w-full justify-start text-left font-normal mt-2"
                        >
                          <CalendarIcon className="mr-2 h-4 w-4" />
                          {selectedDate ? format(selectedDate, 'dd MMMM yyyy', { locale: ru }) : 'Выберите дату'}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <Calendar
                          mode="single"
                          selected={selectedDate}
                          onSelect={setSelectedDate}
                          initialFocus
                          locale={ru}
                        />
                      </PopoverContent>
                    </Popover>
                  </div>
                  <Button 
                    onClick={calculatePersonalNumbers}
                    disabled={!selectedDate}
                    className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700"
                  >
                    Рассчитать личные числа
                  </Button>
                </div>
              </CardContent>
            </Card>

            {personalResults && <PersonalNumbersResult results={personalResults} />}
          </TabsContent>

          <TabsContent value="name" className="space-y-6">
            <Card className="border-emerald-200 shadow-lg">
              <CardHeader className="bg-gradient-to-r from-emerald-100 to-teal-100">
                <CardTitle className="text-emerald-800">Расчет числа имени</CardTitle>
                <CardDescription>
                  Введите полное имя для расчета числа имени по ведической нумерологии
                </CardDescription>
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

            {nameResults && <NameNumberResult results={nameResults} />}
          </TabsContent>

          <TabsContent value="compatibility" className="space-y-6">
            <Card className="border-emerald-200 shadow-lg">
              <CardHeader className="bg-gradient-to-r from-emerald-100 to-teal-100">
                <CardTitle className="text-emerald-800">Расчет совместимости</CardTitle>
                <CardDescription>
                  Введите данные двух партнеров для расчета совместимости по числам жизненного пути
                </CardDescription>
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
                      <Label>Дата рождения</Label>
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button
                            variant="outline"
                            className="w-full justify-start text-left font-normal mt-2"
                          >
                            <CalendarIcon className="mr-2 h-4 w-4" />
                            {partner1Date ? format(partner1Date, 'dd MMMM yyyy', { locale: ru }) : 'Выберите дату'}
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0" align="start">
                          <Calendar
                            mode="single"
                            selected={partner1Date}
                            onSelect={setPartner1Date}
                            initialFocus
                            locale={ru}
                          />
                        </PopoverContent>
                      </Popover>
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
                      <Label>Дата рождения</Label>
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button
                            variant="outline"
                            className="w-full justify-start text-left font-normal mt-2"
                          >
                            <CalendarIcon className="mr-2 h-4 w-4" />
                            {partner2Date ? format(partner2Date, 'dd MMMM yyyy', { locale: ru }) : 'Выберите дату'}
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0" align="start">
                          <Calendar
                            mode="single"
                            selected={partner2Date}
                            onSelect={setPartner2Date}
                            initialFocus
                            locale={ru}
                          />
                        </PopoverContent>
                      </Popover>
                    </div>
                  </div>
                </div>
                <Button 
                  onClick={calculateCompatibility}
                  disabled={!partner1Name.trim() || !partner2Name.trim() || !partner1Date || !partner2Date}
                  className="w-full mt-6 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700"
                >
                  Рассчитать совместимость
                </Button>
              </CardContent>
            </Card>

            {compatibilityResults && <CompatibilityResult results={compatibilityResults} />}
          </TabsContent>

          <TabsContent value="vedic-times" className="space-y-6">
            <VedicTimesCalculator />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default NumerologyCalculator;