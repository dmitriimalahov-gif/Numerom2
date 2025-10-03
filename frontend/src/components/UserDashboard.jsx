import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Avatar, AvatarFallback } from './ui/avatar';
import {
  Sparkles, Calculator, Compass, Heart, HelpCircle, BarChart3,
  BookOpen, FileText, Settings, Grid3X3, Clock, MapPin,
  LogOut, CreditCard, Crown, Menu, User, Calendar, TrendingUp, Video
} from 'lucide-react';
import { useAuth } from './AuthContext';
import NumerologyDashboard from './NumerologyDashboard';
import NameNumerology from './NameNumerology';
import PythagoreanSquare from './PythagoreanSquare';
import Compatibility from './Compatibility';
import Quiz from './Quiz';
import PlanetaryDailyRoute from './PlanetaryDailyRoute';
import ReportExport from './ReportExport';
import VedicTimeCalculations from './VedicTimeCalculations';
import LearningSystem from './LearningSystem';
import AdminPanel from './AdminPanel';
import Materials from './Materials';
import PersonalDataForm from './PersonalDataForm';
import PersonalConsultations from './PersonalConsultations';
import PaymentModal from './PaymentModal';
import CreditHistory from './CreditHistory';
import LessonAdmin from './LessonAdmin';

const UserDashboard = () => {
  const { user, logout, loading, isAuthenticated, isInitialized } = useAuth();
  const [activeSection, setActiveSection] = useState('home');

  // Показываем загрузку пока инициализируется аутентификация
  if (loading || !isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-96">
          <CardContent className="text-center py-8">
            <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p>Загружаем ваш профиль...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Если пользователь не аутентифицирован после инициализации
  if (!isAuthenticated || !user) {
    return null; // MainDashboard покажет лендинг
  }

  // Проверка аутентификации
  useEffect(() => {
    // Если инициализация завершена и пользователь не аутентифицирован
    if (isInitialized && !isAuthenticated) {
      console.log('Пользователь не аутентифицирован, возвращаемся на главную');
      // Здесь можно добавить редирект или показать сообщение
    }
  }, [isInitialized, isAuthenticated]);

  const handleSectionChange = (section) => {
    // Проверяем аутентификацию перед сменой секции
    if (!isAuthenticated) {
      console.warn('Попытка навигации без аутентификации');
      return;
    }
    
    setActiveSection(section);
    // Автоматически закрываем мобильное меню на маленьких экранах
    if (window.innerWidth < 768) {
      setMenuOpen(false);
    }
  };
  const [paymentOpen, setPaymentOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const baseItems = [
    { id: 'home', label: 'Главная', icon: <Sparkles className="w-4 h-4" /> },
    { id: 'personal-data', label: 'Личные данные', icon: <User className="w-4 h-4" /> },
    { id: 'credit-history', label: 'История баллов', icon: <BarChart3 className="w-4 h-4" /> },
    { id: 'numerology', label: 'Нумерология', icon: <Calculator className="w-4 h-4" /> },
    { id: 'name-numerology', label: 'Нумерология имени', icon: <User className="w-4 h-4" /> },
    { id: 'vedic-time', label: 'Ведические времена', icon: <Clock className="w-4 h-4" /> },
    { id: 'planetary-route', label: 'Планетарный маршрут', icon: <MapPin className="w-4 h-4" /> },
    { id: 'compatibility', label: 'Совместимость', icon: <Heart className="w-4 h-4" /> },
    { id: 'quiz', label: 'Тест личности', icon: <HelpCircle className="w-4 h-4" /> },
    { id: 'learning', label: 'Обучение', icon: <BookOpen className="w-4 h-4" /> },
    { id: 'consultations', label: 'Личные консультации', icon: <Video className="w-4 h-4" /> },
    { id: 'report-export', label: 'Загрузка отчётов', icon: <FileText className="w-4 h-4" /> }
  ];

  // Добавить админские пункты меню для администраторов
  const adminItems = user?.role === 'admin' ? [
    { id: 'lesson-admin', label: 'Админ: Редактор уроков', icon: <Settings className="w-4 h-4" />, admin: true }
  ] : [];

  const navigationItems = (user?.is_super_admin || user?.is_admin)
    ? [...baseItems.slice(0, 12), { id: 'admin', label: 'Админ панель', icon: <Settings className="w-4 h-4" /> }, ...baseItems.slice(12), ...adminItems]
    : [...baseItems, ...adminItems];

  const switchTo = (id) => { 
    handleSectionChange(id); 
    // Автоматически закрываем мобильное меню при переходе
    setMenuOpen(false); 
  };

  const renderLeftMenu = () => (
    <div className="space-y-2">
      {/* Заголовок меню - всегда отображается */}
      <div className="mb-4">
        <h2 className="font-bold text-lg text-gray-800">
          NUMEROM
        </h2>
      </div>
      
      {/* Навигационные элементы - всегда в полном виде с текстом */}
      {navigationItems.map((item) => (
        <Button
          key={item.id}
          variant={activeSection === item.id ? 'default' : 'ghost'}
          className={`w-full flex items-center justify-start p-3 transition-colors ${
            activeSection === item.id 
              ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-md hover:from-purple-700 hover:to-indigo-700' 
              : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
          }`}
          onClick={() => switchTo(item.id)}
        >
          <div className="flex-shrink-0">
            {item.icon}
          </div>
          <span className="ml-3 text-sm font-medium whitespace-nowrap">
            {item.label}
          </span>
        </Button>
      ))}
    </div>
  );

  const fullscreenSections = [];

  const renderContent = () => {
    switch (activeSection) {
      case 'personal-data': return <PersonalDataForm />;
      case 'credit-history': return <CreditHistory onNavigate={handleSectionChange} />;
      case 'numerology': return <NumerologyDashboard onBack={() => setActiveSection('home')} />;
      case 'name-numerology': return <NameNumerology />;
      case 'square': return <PythagoreanSquare />;
      case 'vedic-time': return <VedicTimeCalculations />;
      case 'planetary-route': return <PlanetaryDailyRoute />;
      case 'compatibility': return <Compatibility />;
      case 'quiz': return <Quiz />;
      case 'learning': return <LearningSystem />;
      case 'consultations': return <PersonalConsultations />;
      case 'report-export': return <ReportExport />;
      case 'admin': return (user?.is_super_admin || user?.is_admin) ? <AdminPanel /> : <div>Доступ запрещен</div>;
      case 'lesson-admin': return user?.role === 'admin' ? <LessonAdmin /> : <div>Доступ запрещен</div>;
      case 'home':
      default:
        return (
          <div className="space-y-6">
            {/* Приветствие и основная информация */}
            <Card className="numerology-gradient">
              <CardHeader className="text-white">
                <CardTitle className="text-2xl">Добро пожаловать в NUMEROM</CardTitle>
                <CardDescription className="text-white/90">
                  Ваш персональный центр нумерологии и самопознания
                </CardDescription>
              </CardHeader>
            </Card>

            {/* Личные данные */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <User className="w-5 h-5 mr-2" />
                  Ваши личные данные
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <User className="w-4 h-4 text-blue-600" />
                      <div>
                        <p className="text-xs text-muted-foreground">Имя</p>
                        <p className="font-medium">{user?.full_name || user?.name || 'Не указано'}</p>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 bg-green-50 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <Calendar className="w-4 h-4 text-green-600" />
                      <div>
                        <p className="text-xs text-muted-foreground">Дата рождения</p>
                        <p className="font-medium">{user?.birth_date || 'Не указана'}</p>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 bg-orange-50 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <CreditCard className="w-4 h-4 text-orange-600" />
                      <div>
                        <p className="text-xs text-muted-foreground">Кредиты</p>
                        <p className="font-medium text-xl">{user?.credits_remaining || 0}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">Email: {user?.email}</p>
                      <p className="text-xs text-muted-foreground">
                        Статус: {user?.is_premium ? 'Premium подписка' : 'Базовый аккаунт'}
                        {user?.subscription_expires_at && (
                          <span className="ml-2">
                            до {new Date(user.subscription_expires_at).toLocaleDateString()}
                          </span>
                        )}
                      </p>
                    </div>
                    {!user?.is_premium && (
                      <Button
                        onClick={() => setPaymentOpen(true)}
                        className="bg-gradient-to-r from-purple-500 to-pink-500 text-white"
                      >
                        Получить Premium
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Пакеты кредитов */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <CreditCard className="w-5 h-5 mr-2" />
                  Пополнить кредиты
                </CardTitle>
                <CardDescription>
                  Выберите подходящий пакет и экономьте при покупке больших пакетов
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                  {/* Стартовый пакет */}
                  <div className="relative p-4 sm:p-6 border-2 rounded-lg hover:shadow-md transition-shadow w-full flex flex-col">
                    <div className="text-center flex-1 flex flex-col">
                      <h3 className="text-base sm:text-lg font-bold mb-2">Стартовый</h3>
                      <div className="text-2xl sm:text-3xl font-bold text-blue-600 mb-2">10 кредитов</div>
                      <div className="text-xl sm:text-2xl font-bold mb-2">0.99€</div>
                      <div className="line-through text-gray-500 text-sm invisible">-</div>
                      <div className="text-sm text-gray-600 mb-3 sm:mb-4 flex-1">
                        <div>0.099€ за кредит</div>
                        <div className="text-xs">+ месяц доступа</div>
                      </div>
                      <Button
                        onClick={() => setPaymentOpen(true)}
                        className="w-full text-sm sm:text-base py-2 sm:py-3 mt-auto"
                        variant="outline"
                      >
                        Купить
                      </Button>
                    </div>
                  </div>

                  {/* Популярный пакет */}
                  <div className="relative p-4 sm:p-6 border-2 border-green-500 rounded-lg hover:shadow-md transition-shadow bg-green-50 w-full flex flex-col">
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <span className="bg-green-500 text-white px-3 sm:px-4 py-1 rounded-full text-xs sm:text-sm font-medium whitespace-nowrap">
                        Популярный
                      </span>
                    </div>
                    <div className="text-center flex-1 flex flex-col">
                      <h3 className="text-base sm:text-lg font-bold mb-2">Базовый</h3>
                      <div className="text-2xl sm:text-3xl font-bold text-green-600 mb-2">150 кредитов</div>
                      <div className="text-xl sm:text-2xl font-bold mb-2">9.99€</div>
                      <div className="line-through text-gray-500 text-sm">14.85€</div>
                      <div className="text-sm text-green-600 mb-3 sm:mb-4 flex-1">
                        <div>0.067€ за кредит</div>
                        <div className="text-xs font-medium">+ месяц доступа</div>
                      </div>
                      <Button
                        onClick={() => setPaymentOpen(true)}
                        className="w-full bg-green-600 hover:bg-green-700 text-sm sm:text-base py-2 sm:py-3 mt-auto"
                      >
                        Купить со скидкой
                      </Button>
                    </div>
                  </div>

                  {/* Выгодный пакет */}
                  <div className="relative p-4 sm:p-6 border-2 border-purple-500 rounded-lg hover:shadow-md transition-shadow bg-purple-50 w-full flex flex-col">
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <span className="bg-purple-500 text-white px-2 sm:px-4 py-1 rounded-full text-xs sm:text-sm font-medium whitespace-nowrap">
                        Максимум выгоды
                      </span>
                    </div>
                    <div className="text-center flex-1 flex flex-col">
                      <h3 className="text-base sm:text-lg font-bold mb-2">Профессиональный</h3>
                      <div className="text-2xl sm:text-3xl font-bold text-purple-600 mb-2">1000 кредитов</div>
                      <div className="text-xl sm:text-2xl font-bold mb-2">66.6€</div>
                      <div className="line-through text-gray-500 text-sm">199.8€</div>
                      <div className="text-sm text-purple-600 mb-3 sm:mb-4 flex-1">
                        <div>0.067€ за кредит</div>
                        <div className="text-xs font-medium">+ год доступа</div>
                      </div>
                      <Button
                        onClick={() => setPaymentOpen(true)}
                        className="w-full bg-purple-600 hover:bg-purple-700 text-sm sm:text-base py-2 sm:py-3 mt-auto"
                      >
                        Максимальная выгода
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-start space-x-2">
                    <TrendingUp className="w-5 h-5 text-yellow-600 mt-0.5" />
                    <div className="text-sm">
                      <p className="font-medium text-yellow-800">Экономьте больше с крупными пакетами!</p>
                      <p className="text-yellow-700">
                        При покупке пакета "Оптимальный" вы экономите <strong>1.98€</strong>, 
                        а с пакетом "Профессиональный" - целых <strong>3.95€</strong>!
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Быстрые действия - улучшенные для мобильных */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
              <Card className="p-3 sm:p-4 text-center hover:shadow-md transition-all cursor-pointer active:scale-95" 
                    onClick={() => handleSectionChange('numerology')}>
                <Calculator className="w-6 h-6 sm:w-8 sm:h-8 text-blue-600 mx-auto mb-2" />
                <h3 className="font-medium text-sm sm:text-base">Нумерология</h3>
                <p className="text-xs text-muted-foreground hidden sm:block">Расчеты чисел</p>
              </Card>

              <Card className="p-3 sm:p-4 text-center hover:shadow-md transition-all cursor-pointer active:scale-95"
                    onClick={() => handleSectionChange('vedic-time')}>
                <Clock className="w-6 h-6 sm:w-8 sm:h-8 text-green-600 mx-auto mb-2" />
                <h3 className="font-medium text-sm sm:text-base">Ведические времена</h3>
                <p className="text-xs text-muted-foreground hidden sm:block">Планетарные часы</p>
              </Card>

              <Card className="p-3 sm:p-4 text-center hover:shadow-md transition-all cursor-pointer active:scale-95"
                    onClick={() => handleSectionChange('compatibility')}>
                <Heart className="w-6 h-6 sm:w-8 sm:h-8 text-pink-600 mx-auto mb-2" />
                <h3 className="font-medium text-sm sm:text-base">Совместимость</h3>
                <p className="text-xs text-muted-foreground hidden sm:block">Анализ отношений</p>
              </Card>

              <Card className="p-3 sm:p-4 text-center hover:shadow-md transition-all cursor-pointer active:scale-95"
                    onClick={() => handleSectionChange('learning')}>
                <BookOpen className="w-6 h-6 sm:w-8 sm:h-8 text-purple-600 mx-auto mb-2" />
                <h3 className="font-medium text-sm sm:text-base">Обучение</h3>
                <p className="text-xs text-muted-foreground hidden sm:block">Материалы и уроки</p>
              </Card>
            </div>
          </div>
        );
    }
  };

  if (fullscreenSections.includes(activeSection)) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-sage-50 via-lavender-50 to-numerology-50">
        {/* Mobile Menu Button - Fixed position for fullscreen sections */}
        <Button
          variant="ghost"
          onClick={() => setMenuOpen(true)}
          className="fixed top-3 left-3 z-50 bg-white/90 border rounded-full p-2 shadow md:hidden"
        >
          <Menu className="w-5 h-5" />
        </Button>
        
        {/* Credits display */}
        <div className="fixed top-3 right-3 z-50 inline-flex items-center gap-1 bg-sage-100 text-sage-800 rounded-full px-2 py-1 text-xs">
          <CreditCard className="w-3 h-3" /> {user?.credits_remaining || 0}
        </div>
        
        {/* Content */}
        <div className="fixed inset-0 pt-12 pb-6 px-3 overflow-auto">
          {renderContent()}
        </div>
        
        {/* Enhanced Mobile menu - унифицированное для всех секций */}
        {menuOpen && (
          <div className="fixed inset-0 top-0 z-50 md:hidden">
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setMenuOpen(false)}></div>
            <div className="fixed left-0 top-0 h-full w-80 max-w-[85vw] bg-white shadow-xl overflow-y-auto">
              {/* Mobile Menu Header */}
              <div className="p-4 border-b bg-white">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-r from-purple-600 to-indigo-600 flex items-center justify-center">
                      <Sparkles className="w-4 h-4 text-white" />
                    </div>
                    <h2 className="text-lg font-semibold text-gray-900">NUMEROM</h2>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setMenuOpen(false)}
                    className="p-2 hover:bg-gray-100"
                  >
                    ✕
                  </Button>
                </div>
                
                {/* User Info in Mobile Menu */}
                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Avatar className="w-8 h-8">
                      <AvatarFallback className="bg-gray-200 text-gray-800">
                        {user?.email?.charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {user?.full_name || user?.name || 'Пользователь'}
                      </p>
                      <p className="text-xs text-gray-500 truncate">{user?.email}</p>
                    </div>
                  </div>
                  <div className="mt-2 flex items-center justify-between">
                    <span className="inline-flex items-center gap-1 bg-gray-100 text-gray-800 rounded-full px-2 py-1 text-xs">
                      <CreditCard className="w-3 h-3" /> {user?.credits_remaining || 0} кредитов
                    </span>
                    {!user?.is_premium && (
                      <Button 
                        size="sm" 
                        className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-xs px-2 py-1 h-6 hover:from-purple-700 hover:to-indigo-700" 
                        onClick={() => {setPaymentOpen(true); () => setMenuOpen(false)();}}
                      >
                        Premium
                      </Button>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Mobile Menu Items */}
              <div className="p-4 bg-white">
                {renderLeftMenu()}
                
                {/* Mobile-specific actions */}
                <div className="mt-6 pt-4 border-t border-gray-200">
                  <Button
                    variant="ghost"
                    className="w-full justify-start p-3 h-auto text-left text-red-600 hover:bg-red-50"
                    onClick={() => {logout(); () => setMenuOpen(false)();}}
                  >
                    <LogOut className="w-4 h-4 mr-3" />
                    Выйти
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-sage-50 via-lavender-50 to-numerology-50">
      <header className="bg-white/80 backdrop-blur-sm border-b border-sage-200 sticky top-0 z-30">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {/* Mobile Menu Button - Always visible on mobile */}
            <Button
              variant="ghost"
              size="sm"
              className="md:hidden p-2"
              onClick={() => setMenuOpen(true)}
            >
              <Menu className="w-5 h-5" />
            </Button>
            <div className="w-8 h-8 rounded-full numerology-gradient flex items-center justify-center"><Sparkles className="w-5 h-5 text-white" /></div>
            <div><h1 className="text-xl font-bold text-gray-900">NUMEROM</h1><p className="text-xs text-gray-600 hidden sm:block">Панель управления</p></div>
          </div>
          <div className="flex items-center gap-2">
            {!user?.is_premium && (<Button size="sm" className="numerology-gradient hidden sm:flex" onClick={() => setPaymentOpen(true)}><Crown className="w-4 h-4 mr-1" /> Подписаться</Button>)}
            <span className="inline-flex items-center gap-1 bg-sage-100 text-sage-800 rounded-full px-2 py-1 text-xs"><CreditCard className="w-3 h-3" /> {user?.credits_remaining || 0}</span>
            <Avatar className="w-8 h-8 hidden sm:flex"><AvatarFallback className="bg-sage-200 text-sage-800">{user?.email?.charAt(0).toUpperCase()}</AvatarFallback></Avatar>
            <Button variant="ghost" size="sm" onClick={logout} className="text-gray-600 hover:text-gray-900 hidden sm:flex"><LogOut className="w-4 h-4" /></Button>
          </div>
        </div>
      </header>

      {/* Enhanced Mobile menu */}
      <div className={`fixed inset-0 top-0 z-50 md:hidden transition-opacity duration-300 ${menuOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}>
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setMenuOpen(false)}></div>
          <div className={`fixed left-0 top-0 h-full w-80 max-w-[85vw] bg-white shadow-xl overflow-y-auto transition-transform duration-300 ease-out ${menuOpen ? 'translate-x-0' : '-translate-x-full'}`}>
              {/* Mobile Menu Header */}
              <div className="p-4 border-b bg-white">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-r from-purple-600 to-indigo-600 flex items-center justify-center">
                      <Sparkles className="w-4 h-4 text-white" />
                    </div>
                    <h2 className="text-lg font-semibold text-gray-900">NUMEROM</h2>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setMenuOpen(false)}
                    className="p-2 hover:bg-gray-100"
                  >
                    ✕
                  </Button>
                </div>
                
                {/* User Info in Mobile Menu */}
                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Avatar className="w-8 h-8">
                      <AvatarFallback className="bg-gray-200 text-gray-800">
                        {user?.email?.charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {user?.full_name || user?.name || 'Пользователь'}
                      </p>
                      <p className="text-xs text-gray-500 truncate">{user?.email}</p>
                    </div>
                  </div>
                  <div className="mt-2 flex items-center justify-between">
                    <span className="inline-flex items-center gap-1 bg-gray-100 text-gray-800 rounded-full px-2 py-1 text-xs">
                      <CreditCard className="w-3 h-3" /> {user?.credits_remaining || 0} кредитов
                    </span>
                    {!user?.is_premium && (
                      <Button 
                        size="sm" 
                        className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-xs px-2 py-1 h-6 hover:from-purple-700 hover:to-indigo-700" 
                        onClick={() => {setPaymentOpen(true); () => setMenuOpen(false)();}}
                      >
                        Premium
                      </Button>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Mobile Menu Items */}
              <div className="p-4 bg-white">
                {renderLeftMenu()}
                
                {/* Mobile-specific actions */}
                <div className="mt-6 pt-4 border-t border-gray-200">
                  <Button
                    variant="ghost"
                    className="w-full justify-start p-3 h-auto text-left text-red-600 hover:bg-red-50"
                    onClick={() => {logout(); () => setMenuOpen(false)();}}
                  >
                    <LogOut className="w-4 h-4 mr-3" />
                    <span className="text-sm font-medium">Выйти</span>
                  </Button>
                </div>
              </div>
            </div>
      </div>

      <div className="mx-auto py-6 flex gap-4">
        {/* Desktop menu - всегда белый фон, фиксированная ширина */}
        <aside className="hidden md:block w-64 flex-shrink-0">
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm sticky top-20">
            <div className="p-4 overflow-y-auto max-h-[calc(100vh-6rem)]">
              {renderLeftMenu()}
            </div>
          </div>
        </aside>

        <div className="flex-1 p-4 md:p-6">{renderContent()}</div>
      </div>

      <PaymentModal isOpen={paymentOpen} onClose={() => setPaymentOpen(false)} />
    </div>
  );
};

export default UserDashboard;