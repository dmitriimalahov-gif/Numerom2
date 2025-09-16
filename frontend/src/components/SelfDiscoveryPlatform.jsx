import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';
import { User, Mail, Lock, CreditCard, Calendar, BookOpen, Target, ArrowRight, CheckCircle, Star } from 'lucide-react';

const SelfDiscoveryPlatform = () => {
  const [currentStep, setCurrentStep] = useState('welcome');
  const [userData, setUserData] = useState({
    name: '',
    email: '',
    password: '',
    birthDate: '',
    subscriptionPlan: ''
  });

  // Exact colors from your KVADRATW image
  const numerologyColors = {
    1: '#8B4513', // Brown-red (Сурья)
    2: '#D3D3D3', // Light gray (Чандра) 
    3: '#A0522D', // Brown (Гуру)
    4: '#6B8E23', // Olive-brown (Раху)
    5: '#32CD32', // Green - main center color (Буддхи)
    6: '#FFB6C1', // Light pink (Шукра)
    7: '#708090', // Slate gray (Кету)
    8: '#4169E1', // Blue (Шани)
    9: '#DC143C'  // Red (Мангал)
  };

  const steps = [
    { id: 'welcome', title: 'Добро пожаловать', progress: 0 },
    { id: 'registration', title: 'Регистрация', progress: 20 },
    { id: 'subscription', title: 'Выбор плана', progress: 40 },
    { id: 'payment', title: 'Оплата', progress: 60 },
    { id: 'profile', title: 'Профиль', progress: 80 },
    { id: 'journey', title: 'Путешествие самопознания', progress: 100 }
  ];

  const subscriptionPlans = [
    {
      id: 'basic',
      name: 'Базовый',
      price: 990,
      duration: 'месяц',
      features: [
        'Расчет основных чисел',
        'Базовая интерпретация',
        '7 дней ведических периодов',
        'Email поддержка'
      ],
      color: numerologyColors[3],
      popular: false
    },
    {
      id: 'premium',
      name: 'Премиум',
      price: 2490,
      duration: '3 месяца',
      features: [
        'Все базовые функции',
        'Глубокий анализ совместимости',
        'Персональные рекомендации',
        'Еженедельные прогнозы',
        'Чат с экспертом'
      ],
      color: numerologyColors[5],
      popular: true
    },
    {
      id: 'master',
      name: 'Мастер',
      price: 4990,
      duration: '6 месяцев',
      features: [
        'Все премиум функции',
        'Индивидуальные консультации',
        'Карта жизненного пути',
        'Приоритетная поддержка',
        'Закрытые мастер-классы'
      ],
      color: numerologyColors[8],
      popular: false
    }
  ];

  const learningModules = [
    {
      id: 1,
      title: 'Основы ведической нумерологии',
      description: 'Узнайте историю и принципы древней науки чисел',
      duration: '2 недели',
      lessons: 12,
      color: numerologyColors[1],
      status: 'available'
    },
    {
      id: 2,
      title: 'Квадрат Пифагора по методу Александрова',
      description: 'Глубокое изучение системы расчетов и интерпретаций',
      duration: '3 недели',
      lessons: 18,
      color: numerologyColors[5],
      status: 'locked'
    },
    {
      id: 3,
      title: 'Планетные влияния и циклы',
      description: 'Изучение влияния планет на личность и судьбу',
      duration: '2 недели',
      lessons: 14,
      color: numerologyColors[7],
      status: 'locked'
    },
    {
      id: 4,
      title: 'Анализ совместимости',
      description: 'Искусство определения совместимости в отношениях',
      duration: '2 недели',
      lessons: 10,
      color: numerologyColors[6],
      status: 'locked'
    },
    {
      id: 5,
      title: 'Практическое применение',
      description: 'Как использовать знания в повседневной жизни',
      duration: '1 неделя',
      lessons: 8,
      color: numerologyColors[9],
      status: 'locked'
    }
  ];

  const getCurrentStepData = () => {
    return steps.find(step => step.id === currentStep);
  };

  const handleRegistration = (e) => {
    e.preventDefault();
    if (userData.name && userData.email && userData.password) {
      setCurrentStep('subscription');
    }
  };

  const handleSubscriptionSelect = (planId) => {
    setUserData({...userData, subscriptionPlan: planId});
    setCurrentStep('payment');
  };

  const handlePayment = () => {
    // Mock payment processing
    setTimeout(() => {
      setCurrentStep('profile');
    }, 2000);
  };

  const renderWelcome = () => (
    <div className="text-center space-y-6">
      <div className="relative">
        <div 
          className="w-24 h-24 rounded-full border-4 flex items-center justify-center bg-white shadow-2xl mx-auto mb-6"
          style={{ borderColor: numerologyColors[5] }}
        >
          <span className="text-3xl font-bold" style={{ color: numerologyColors[5] }}>N</span>
        </div>
      </div>
      
      <h1 className="text-4xl font-bold" style={{ color: numerologyColors[5] }}>
        NUMEROM ACADEMY
      </h1>
      
      <p className="text-lg text-gray-700 max-w-2xl mx-auto leading-relaxed">
        Добро пожаловать в интерактивную академию самопознания через ведическую нумерологию. 
        Откройте тайны своих чисел и трансформируйте свою жизнь с помощью древних знаний.
      </p>

      <div className="grid md:grid-cols-3 gap-6 mt-8">
        <Card className="border-2" style={{ borderColor: numerologyColors[1] + '40' }}>
          <CardContent className="p-6 text-center">
            <BookOpen className="w-12 h-12 mx-auto mb-4" style={{ color: numerologyColors[1] }} />
            <h3 className="font-semibold text-lg mb-2">Обучение</h3>
            <p className="text-sm text-gray-600">Пошаговые уроки от экспертов</p>
          </CardContent>
        </Card>

        <Card className="border-2" style={{ borderColor: numerologyColors[5] + '40' }}>
          <CardContent className="p-6 text-center">
            <Target className="w-12 h-12 mx-auto mb-4" style={{ color: numerologyColors[5] }} />
            <h3 className="font-semibold text-lg mb-2">Практика</h3>
            <p className="text-sm text-gray-600">Применение знаний на практике</p>
          </CardContent>
        </Card>

        <Card className="border-2" style={{ borderColor: numerologyColors[8] + '40' }}>
          <CardContent className="p-6 text-center">
            <Star className="w-12 h-12 mx-auto mb-4" style={{ color: numerologyColors[8] }} />
            <h3 className="font-semibold text-lg mb-2">Трансформация</h3>
            <p className="text-sm text-gray-600">Личностное развитие и рост</p>
          </CardContent>
        </Card>
      </div>

      <Button 
        onClick={() => setCurrentStep('registration')}
        className="text-white px-8 py-3 text-lg"
        style={{ backgroundColor: numerologyColors[5] }}
      >
        Начать путешествие <ArrowRight className="ml-2 w-5 h-5" />
      </Button>
    </div>
  );

  const renderRegistration = () => (
    <Card className="max-w-md mx-auto">
      <CardHeader style={{ backgroundColor: numerologyColors[5] + '20' }}>
        <CardTitle style={{ color: numerologyColors[5] }}>
          <User className="w-5 h-5 inline mr-2" />
          Создание аккаунта
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <form onSubmit={handleRegistration} className="space-y-4">
          <div>
            <Label htmlFor="name">Полное имя</Label>
            <Input
              id="name"
              value={userData.name}
              onChange={(e) => setUserData({...userData, name: e.target.value})}
              placeholder="Введите ваше полное имя"
              required
            />
          </div>
          
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={userData.email}
              onChange={(e) => setUserData({...userData, email: e.target.value})}
              placeholder="your@email.com"
              required
            />
          </div>
          
          <div>
            <Label htmlFor="password">Пароль</Label>
            <Input
              id="password"
              type="password"
              value={userData.password}
              onChange={(e) => setUserData({...userData, password: e.target.value})}
              placeholder="Создайте надежный пароль"
              required
            />
          </div>

          <Button 
            type="submit"
            className="w-full text-white"
            style={{ backgroundColor: numerologyColors[5] }}
          >
            Продолжить
          </Button>
        </form>
      </CardContent>
    </Card>
  );

  const renderSubscription = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-3xl font-bold mb-4" style={{ color: numerologyColors[5] }}>
          Выберите свой путь обучения
        </h2>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Каждый план открывает новые возможности для самопознания и духовного роста
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {subscriptionPlans.map((plan) => (
          <Card 
            key={plan.id}
            className={`border-2 relative transition-all duration-300 hover:shadow-lg ${
              plan.popular ? 'ring-2 ring-offset-2' : ''
            }`}
            style={{ 
              borderColor: plan.color + '60',
              ringColor: plan.popular ? plan.color : 'transparent'
            }}
          >
            {plan.popular && (
              <Badge 
                className="absolute -top-2 left-1/2 transform -translate-x-1/2 text-white"
                style={{ backgroundColor: plan.color }}
              >
                Популярный
              </Badge>
            )}
            
            <CardHeader style={{ backgroundColor: plan.color + '10' }}>
              <CardTitle style={{ color: plan.color }}>
                {plan.name}
              </CardTitle>
              <div className="text-center">
                <span className="text-3xl font-bold" style={{ color: plan.color }}>
                  {plan.price}₽
                </span>
                <span className="text-gray-600">/{plan.duration}</span>
              </div>
            </CardHeader>
            
            <CardContent className="p-6">
              <ul className="space-y-3 mb-6">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-center text-sm">
                    <CheckCircle className="w-4 h-4 mr-2" style={{ color: plan.color }} />
                    {feature}
                  </li>
                ))}
              </ul>
              
              <Button 
                onClick={() => handleSubscriptionSelect(plan.id)}
                className="w-full text-white"
                style={{ backgroundColor: plan.color }}
              >
                Выбрать план
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderPayment = () => {
    const selectedPlan = subscriptionPlans.find(p => p.id === userData.subscriptionPlan);
    
    return (
      <Card className="max-w-md mx-auto">
        <CardHeader style={{ backgroundColor: selectedPlan.color + '20' }}>
          <CardTitle style={{ color: selectedPlan.color }}>
            <CreditCard className="w-5 h-5 inline mr-2" />
            Оплата подписки
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="mb-6 p-4 rounded-lg" style={{ backgroundColor: selectedPlan.color + '10' }}>
            <h3 className="font-semibold" style={{ color: selectedPlan.color }}>
              {selectedPlan.name}
            </h3>
            <p className="text-2xl font-bold" style={{ color: selectedPlan.color }}>
              {selectedPlan.price}₽ / {selectedPlan.duration}
            </p>
          </div>

          <div className="space-y-4">
            <div>
              <Label htmlFor="cardNumber">Номер карты</Label>
              <Input
                id="cardNumber"
                placeholder="1234 5678 9012 3456"
                className="mt-2"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="expiry">Срок действия</Label>
                <Input
                  id="expiry"
                  placeholder="MM/YY"
                  className="mt-2"
                />
              </div>
              <div>
                <Label htmlFor="cvv">CVV</Label>
                <Input
                  id="cvv"
                  placeholder="123"
                  className="mt-2"
                />
              </div>
            </div>

            <Button 
              onClick={handlePayment}
              className="w-full text-white"
              style={{ backgroundColor: selectedPlan.color }}
            >
              Оплатить {selectedPlan.price}₽
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderProfile = () => (
    <Card className="max-w-md mx-auto">
      <CardHeader style={{ backgroundColor: numerologyColors[5] + '20' }}>
        <CardTitle style={{ color: numerologyColors[5] }}>
          <Calendar className="w-5 h-5 inline mr-2" />
          Завершение профиля
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div className="space-y-4">
          <div>
            <Label htmlFor="birthDate">Дата рождения (ДД.ММ.ГГГГ)</Label>
            <Input
              id="birthDate"
              value={userData.birthDate}
              onChange={(e) => setUserData({...userData, birthDate: e.target.value})}
              placeholder="10.01.1982"
            />
          </div>

          <Button 
            onClick={() => setCurrentStep('journey')}
            className="w-full text-white"
            style={{ backgroundColor: numerologyColors[5] }}
          >
            Завершить регистрацию
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  const renderJourney = () => (
    <div className="space-y-8">
      <div className="text-center">
        <CheckCircle className="w-16 h-16 mx-auto mb-4" style={{ color: numerologyColors[5] }} />
        <h2 className="text-3xl font-bold mb-4" style={{ color: numerologyColors[5] }}>
          Добро пожаловать в NUMEROM Academy!
        </h2>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Ваше путешествие самопознания начинается сейчас. Изучайте модули поэтапно для максимального результата.
        </p>
      </div>

      <div className="space-y-4">
        <h3 className="text-xl font-semibold mb-4">Программа обучения</h3>
        {learningModules.map((module, index) => (
          <Card 
            key={module.id}
            className={`border-2 transition-all duration-300 ${
              module.status === 'available' ? 'hover:shadow-lg cursor-pointer' : 'opacity-60'
            }`}
            style={{ borderColor: module.color + '40' }}
          >
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <div 
                      className="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm"
                      style={{ backgroundColor: module.color }}
                    >
                      {module.id}
                    </div>
                    <h4 className="text-lg font-semibold">{module.title}</h4>
                    {module.status === 'available' && (
                      <Badge variant="outline" style={{ borderColor: module.color, color: module.color }}>
                        Доступен
                      </Badge>
                    )}
                  </div>
                  <p className="text-gray-600 mb-3">{module.description}</p>
                  <div className="flex gap-4 text-sm text-gray-500">
                    <span>📚 {module.lessons} уроков</span>
                    <span>⏰ {module.duration}</span>
                  </div>
                </div>
                
                {module.status === 'available' ? (
                  <Button 
                    className="text-white"
                    style={{ backgroundColor: module.color }}
                  >
                    Начать
                  </Button>
                ) : (
                  <Button variant="outline" disabled>
                    <Lock className="w-4 h-4 mr-2" />
                    Заблокирован
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const currentStepData = getCurrentStepData();

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(to bottom right, #F0FFF0, #E0FFE0, #D0FFD0)' }}>
      <div className="container mx-auto py-8 px-4">
        {/* Progress Bar */}
        {currentStep !== 'welcome' && (
          <Card className="mb-8">
            <CardContent className="p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-semibold" style={{ color: numerologyColors[5] }}>
                  {currentStepData.title}
                </span>
                <span className="text-sm text-gray-600">
                  {currentStepData.progress}%
                </span>
              </div>
              <Progress 
                value={currentStepData.progress} 
                className="h-2"
              />
            </CardContent>
          </Card>
        )}

        {/* Step Content */}
        <div className="max-w-4xl mx-auto">
          {currentStep === 'welcome' && renderWelcome()}
          {currentStep === 'registration' && renderRegistration()}
          {currentStep === 'subscription' && renderSubscription()}
          {currentStep === 'payment' && renderPayment()}
          {currentStep === 'profile' && renderProfile()}
          {currentStep === 'journey' && renderJourney()}
        </div>
      </div>
    </div>
  );
};

export default SelfDiscoveryPlatform;