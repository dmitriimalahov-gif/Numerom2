import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
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
import PaymentModal from './PaymentModal';

const UserDashboard = () => {
  const { user, logout, loading, isAuthenticated, isInitialized } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // State hooks - должны быть до любых условных возвратов
  const [paymentOpen, setPaymentOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  // Получить текущую секцию из URL
  const activeSection = location.pathname.split('/')[2] || 'home';

  // Effect hooks - должны быть до любых условных возвратов
  // Перенаправление если пользователь не аутентифицирован
  useEffect(() => {
    if (isInitialized && !isAuthenticated) {
      console.log('Пользователь не аутентифицирован, возвращаемся на главную');
      navigate('/');
    }
  }, [isInitialized, isAuthenticated, navigate]);

  // Перенаправить на /dashboard/home если находимся на /dashboard
  useEffect(() => {
    if (location.pathname === '/dashboard' || location.pathname === '/dashboard/') {
      navigate('/dashboard/home', { replace: true });
    }
  }, [location.pathname, navigate]);

  const handleSectionChange = (section) => {
    // Проверяем аутентификацию перед навигацией
    if (!isAuthenticated) {
      console.warn('Попытка навигации без аутентификации');
      return;
    }

    navigate(`/dashboard/${section}`);
    // Автоматически закрываем мобильное меню на маленьких экранах
    if (window.innerWidth < 768) {
      setMenuOpen(false);
    }
  };

  // Условные возвраты ПОСЛЕ всех хуков
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

  const baseItems = [
    { id: 'home', label: 'Главная', icon: <Sparkles className="w-4 h-4" /> },
    { id: 'personal-data', label: 'Личные данные', icon: <User className="w-4 h-4" /> },
    { id: 'credit-history', label: 'История баллов', icon: <BarChart3 className="w-4 h-4" /> },
    { id: 'numerology-design', label: 'Нумерология', icon: <Calculator className="w-4 h-4" /> },
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
  const adminItems = [];

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

  if (false) { // Fullscreen sections removed - routing handles all sections now
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
          <Outlet />
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

        <div className="flex-1 p-4 md:p-6"><Outlet /></div>
      </div>

      <PaymentModal isOpen={paymentOpen} onClose={() => setPaymentOpen(false)} />
    </div>
  );
};

export default UserDashboard;