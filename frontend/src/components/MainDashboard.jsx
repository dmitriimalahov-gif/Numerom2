import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Calculator, Compass, Heart, Star, Grid3X3, Clock, BarChart3, FileText, Sparkles, Users, TrendingUp, Shield } from 'lucide-react';
import { useAuth } from './AuthContext';
import AuthModal from './AuthModal';

const MainDashboard = () => {
  const { user, loading, isInitialized } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [, forceUpdate] = useState({});

  // Отладочное логирование и принудительное обновление
  useEffect(() => {
    console.log('MainDashboard render:', {
      user: user ? `${user.email} (ID: ${user.id})` : 'null',
      loading,
      isInitialized,
      hasToken: !!localStorage.getItem('token')
    });
    
    // Принудительное обновление при изменении пользователя
    if (user) {
      console.log('MainDashboard: форсируем обновление после логина');
      forceUpdate({});
      
      // Автоматически закрываем модал авторизации если пользователь авторизован
      if (showAuthModal) {
        console.log('MainDashboard: закрываем модал авторизации');
        setShowAuthModal(false);
      }
    }
  }, [user, loading, isInitialized, showAuthModal]);

  // Показываем загрузку только при первой инициализации
  if (loading && !isInitialized && !user) {
    console.log('MainDashboard: показываем загрузку, loading:', loading, 'isInitialized:', isInitialized);
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-sage-50 via-lavender-50 to-numerology-50">
        <Card className="w-96">
          <CardContent className="text-center py-8">
            <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p>Инициализируем систему...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // If user is logged in, redirect to dashboard
  if (user) {
    console.log('MainDashboard: пользователь найден, перенаправляем на /dashboard для:', user.email);
    return <Navigate to="/dashboard" replace />;
  }

  console.log('MainDashboard: пользователь не найден, показываем лендинг');
  console.log('Токен в localStorage:', localStorage.getItem('token') ? 'есть' : 'нет');

  const features = [
    { icon: <Calculator className="w-6 h-6 text-white" />, title: 'Персональные числа', description: 'Число судьбы, души, управляющее число и их влияние на вашу жизнь', gradient: 'bg-gradient-to-br from-blue-500 to-cyan-500' },
    { icon: <Compass className="w-6 h-6 text-white" />, title: 'Нумерология', description: 'Квадрат Пифагора + Персональные числа (Объединенный раздел)', gradient: 'bg-gradient-to-br from-teal-500 to-emerald-500' },
    { icon: <Clock className="w-6 h-6 text-white" />, title: 'Раху кала и мухурты', description: 'Ведическое расписание дня по городу и дате', gradient: 'bg-gradient-to-br from-orange-500 to-red-500' },
    { icon: <BarChart3 className="w-6 h-6 text-white" />, title: 'Графики энергий', description: 'Планетарные энергии и рекомендации на период', gradient: 'bg-gradient-to-br from-purple-500 to-indigo-600' },
    { icon: <FileText className="w-6 h-6 text-white" />, title: 'HTML отчёты', description: 'Скачивание брендированных HTML‑отчётов', gradient: 'bg-gradient-to-br from-emerald-500 to-teal-600' },
    { icon: <Users className="w-6 h-6 text-white" />, title: 'Пополнить баланс', description: 'Выберите пакет кредитов по удобной цене в евро', gradient: 'bg-gradient-to-br from-green-500 to-emerald-600' },
    { icon: <FileText className="w-6 h-6 text-white" />, title: 'Методические материалы', description: 'PDF‑материалы для обучения (для студентов)', gradient: 'bg-gradient-to-br from-rose-500 to-pink-600' },
    { icon: <Heart className="w-6 h-6 text-white" />, title: 'Совместимость', description: 'Анализ совместимости на основе дат рождения', gradient: 'bg-gradient-to-br from-yellow-500 to-orange-500' },
    { icon: <Star className="w-6 h-6 text-white" />, title: 'Тест самопознания', description: '10 вопросов для глубокого понимания вашей личности', gradient: 'bg-gradient-to-br from-violet-500 to-purple-500' }
  ];

  const pricingPlans = [
    {
      name: 'Стартовый',
      price: '0.99€',
      credits: '10 кредитов',
      features: ['Базовые расчеты', 'Квадрат Пифагора', 'Персональные числа', 'HTML отчёты', '+ месяц доступа'],
      gradient: 'bg-gradient-to-br from-sage-200 to-sage-300',
      popular: false
    },
    {
      name: 'Базовый',
      price: '9.99€',
      credits: '150 кредитов',
      features: ['Все функции', 'Ведические расчеты', 'Графики энергий', 'HTML отчеты', 'Совместимость', '+ месяц доступа'],
      gradient: 'bg-gradient-to-br from-lavender-200 to-lavender-300',
      popular: true
    },
    {
      name: 'Профессиональный',
      price: '66.6€',
      credits: '1000 кредитов',
      features: ['Все функции', 'Приоритетная поддержка', 'Эксклюзивные материалы', 'Групповая совместимость', '+ год доступа'],
      gradient: 'bg-gradient-to-br from-numerology-1 to-numerology-2',
      popular: false
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-sage-50 via-lavender-50 to-numerology-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-sage-200 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full numerology-gradient flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">NUMEROM</h1>
              <p className="text-sm text-gray-600">Инструмент самопознания</p>
            </div>
          </div>
          <Button
            onClick={() => setShowAuthModal(true)}
            className="numerology-gradient hover:shadow-xl hover:brightness-90 transition-all duration-200"
          >
            Войти
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto text-center max-w-4xl">
          <div className="mb-8">
            <Badge className="mb-4 bg-sage-100 text-sage-800 border-sage-200">
              Пошаговый инструмент самопознания
            </Badge>
            <h2 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
              Откройте свой
              <span className="block numerology-text-gradient">потенциал</span>
            </h2>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Персонализированные нумерологические расчеты, ведические временные циклы и глубокий анализ личности на основе вашей даты рождения
            </p>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Button
              size="lg"
              onClick={() => setShowAuthModal(true)}
              className="numerology-gradient hover:shadow-xl hover:brightness-90 transition-all duration-200 text-lg px-8 py-3"
            >
              Начать путешествие
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="relative border-2 border-[hsl(180,55%,45%)] text-[hsl(180,55%,45%)] hover:bg-[hsl(180,55%,45%)]/10 hover:shadow-lg transition-all text-lg px-8 py-3 font-semibold"
            >
              Узнать больше
            </Button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-2xl mx-auto">
            <div className="text-center">
              <div className="text-3xl font-bold text-gray-900 mb-2">10,000+</div>
              <div className="text-gray-600">Пользователей</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-gray-900 mb-2">50,000+</div>
              <div className="text-gray-600">Расчетов</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-gray-900 mb-2">99%</div>
              <div className="text-gray-600">Точность</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 bg-white/50">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h3 className="text-4xl font-bold text-gray-900 mb-4">
              Возможности платформы
            </h3>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Комплексный анализ личности через древние знания и современные технологии
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <Card key={index} className="group hover:shadow-lg transition-all duration-300 border-0 bg-white/80 backdrop-blur-sm">
                <CardHeader>
                  <div className={`w-12 h-12 rounded-lg ${feature.gradient} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                    {feature.icon}
                  </div>
                  <CardTitle className="text-xl text-gray-900">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-gray-600 text-base">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-20 px-4 sm:px-6 md:px-8">
        <div className="container mx-auto max-w-5xl px-0">
          <div className="text-center mb-16">
            <h3 className="text-4xl font-bold text-gray-900 mb-4">
              Выберите свой план
            </h3>
            <p className="text-xl text-gray-600">
              Гибкие тарифы для любых потребностей
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 md:gap-8">
            {pricingPlans.map((plan, index) => (
              <Card key={index} className={`relative w-full mt-6 flex flex-col ${plan.popular ? 'shadow-xl border-2 border-lavender-400' : ''} hover:shadow-lg transition-all duration-300 border-0 bg-white/80 backdrop-blur-sm`}>
                {plan.popular && (
                  <Badge className="absolute -top-4 left-1/2 transform -translate-x-1/2 text-white font-bold px-4 py-1.5 shadow-xl text-sm z-10" style={{ backgroundColor: 'hsl(180, 55%, 45%)' }}>
                    Популярный
                  </Badge>
                )}
                <CardHeader className="text-center p-4 sm:p-6">
                  <div className={`w-12 h-12 sm:w-16 sm:h-16 rounded-full ${plan.gradient} flex items-center justify-center mx-auto mb-3 sm:mb-4`}>
                    <Shield className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
                  </div>
                  <CardTitle className="text-lg sm:text-xl md:text-2xl text-gray-900">{plan.name}</CardTitle>
                  <div className="text-2xl sm:text-3xl font-bold text-gray-900 mt-2">{plan.price}</div>
                  <CardDescription className="text-base sm:text-lg text-gray-600">{plan.credits}</CardDescription>
                </CardHeader>
                <CardContent className="p-4 sm:p-6 flex flex-col flex-1">
                  <ul className="space-y-2 sm:space-y-3 mb-4 sm:mb-6 flex-1">
                    {plan.features.map((feature, featureIndex) => (
                      <li key={featureIndex} className="flex items-start text-gray-600 text-sm sm:text-base">
                        <div className="w-2 h-2 rounded-full bg-sage-400 mr-3 mt-2 flex-shrink-0"></div>
                        <span className="leading-relaxed">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Button
                    className="w-full numerology-gradient hover:shadow-xl hover:brightness-90 transition-all duration-200 text-sm sm:text-base py-2 sm:py-3 mt-auto"
                    onClick={() => setShowAuthModal(true)}
                  >
                    Выбрать план
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 bg-gradient-to-r from-sage-100 to-lavender-100">
        <div className="container mx-auto text-center max-w-3xl">
          <h3 className="text-4xl font-bold text-gray-900 mb-6">
            Готовы начать свое путешествие к самопознанию?
          </h3>
          <p className="text-xl text-gray-600 mb-8">
            Присоединяйтесь к тысячам людей, которые уже открыли свой потенциал с помощью NUMEROM
          </p>
          <Button
            size="lg"
            onClick={() => setShowAuthModal(true)}
            className="numerology-gradient hover:shadow-xl hover:brightness-90 transition-all duration-200 text-lg px-12 py-4"
          >
            Начать сейчас
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12 px-4">
        <div className="container mx-auto text-center">
          <div className="flex items-center justify-center space-x-3 mb-6">
            <div className="w-8 h-8 rounded-full numerology-gradient flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">NUMEROM</span>
          </div>
          <p className="text-gray-400 mb-4">
            Инструмент самопознания на основе древних знаний
          </p>
          <div className="text-sm text-gray-500">
            © 2024 NUMEROM. Все права защищены.
          </div>
        </div>
      </footer>

      {/* Auth Modal */}
      <AuthModal 
        isOpen={showAuthModal} 
        onClose={() => setShowAuthModal(false)} 
      />
    </div>
  );
};

export default MainDashboard;