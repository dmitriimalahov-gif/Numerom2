import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Progress } from './ui/progress';
import { 
  Brain, 
  BookOpen, 
  Settings, 
  LogOut, 
  Menu, 
  User, 
  Crown,
  Trophy,
  Target,
  Zap,
  TrendingUp,
  Award,
  Star,
  Flame,
  Calendar,
  CheckCircle2,
  Clock,
  Eye,
  Download,
  BarChart3,
  FileText,
  X,
  AlertCircle,
  Lightbulb,
  TrendingDown
} from 'lucide-react';
import { useAuth } from './AuthContext';
import { getBackendUrl } from '../utils/backendUrl';

const backendUrl = getBackendUrl();

const UserDashboardV2 = () => {
  const { user, logout, isAuthenticated, isInitialized } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [menuOpen, setMenuOpen] = useState(false);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  // Загрузка статистики студента
  useEffect(() => {
    // Ждем инициализации аутентификации
    if (!isInitialized) {
      return;
    }

    // Проверяем, что пользователь аутентифицирован
    if (!isAuthenticated) {
      console.log('User not authenticated, redirecting to login');
      navigate('/');
      return;
    }

    const token = localStorage.getItem('token');
    if (!token) {
      console.log('No token found, redirecting to login');
      navigate('/');
      return;
    }
    
    loadDashboardStats();
  }, [isInitialized, isAuthenticated, navigate]);

  const loadDashboardStats = async (showError = true) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No token available');
        if (showError) {
          navigate('/');
        }
        return;
      }

      const response = await fetch(`${backendUrl}/api/student/dashboard-stats`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });

      if (!response.ok) {
        if (response.status === 401) {
          console.error('Unauthorized - token may be invalid');
          // Очищаем токен и перенаправляем на логин только если это первичная загрузка
          localStorage.removeItem('token');
          if (showError) {
            navigate('/');
          }
          return;
        }
        console.error('Dashboard stats response not ok:', response.status, response.statusText);
        if (showError) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return;
      }

      const data = await response.json();
      console.log('Dashboard stats loaded:', data);
      setStats(data.stats);
    } catch (error) {
      console.error('Error loading dashboard stats:', error);
      // Если ошибка аутентификации, перенаправляем на логин только если это первичная загрузка
      if ((error.message.includes('401') || error.message.includes('Unauthorized')) && showError) {
        localStorage.removeItem('token');
        navigate('/');
      }
    } finally {
      setLoading(false);
    }
  };

  // Навигационные элементы
  const navigationItems = [
    {
      id: 'learning-v2',
      label: 'Обучение V2',
      icon: <Brain className="w-4 h-4" />,
      description: 'Интерактивная система обучения с 5 разделами'
    },
    {
      id: 'admin-v2',
      label: 'Админ-панель',
      icon: <Crown className="w-4 h-4" />,
      description: 'Управление уроками и контентом',
      adminOnly: true
    }
  ];

  const handleNavigation = (sectionId) => {
    if (sectionId === 'learning-v2') {
      navigate('/learning-v2-lesson/48fddd0b-4b00-4a99-9fed-21513f5b484b');
    } else if (sectionId === 'admin-v2') {
      navigate('/dashboard/admin-v2');
    }
    setMenuOpen(false);
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  // Проверяем, является ли пользователь администратором
  const isAdmin = user?.is_super_admin || user?.is_admin;
  const filteredNavigation = navigationItems.filter(item => !item.adminOnly || isAdmin);

  // Функция для получения цвета уровня
  const getLevelColor = (level) => {
    const colors = {
      1: 'from-gray-400 to-gray-600',
      2: 'from-green-400 to-green-600',
      3: 'from-blue-400 to-blue-600',
      4: 'from-purple-400 to-purple-600',
      5: 'from-yellow-400 to-yellow-600'
    };
    return colors[level] || colors[1];
  };

  // Функция для получения иконки уровня
  const getLevelIcon = (level) => {
    const icons = {
      1: '🌱',
      2: '📚',
      3: '🎓',
      4: '⭐',
      5: '👑'
    };
    return icons[level] || icons[1];
  };

  // Показываем загрузку, если еще не инициализирована аутентификация или загружаются данные
  if (!isInitialized || loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <Brain className="w-16 h-16 text-blue-600 mx-auto mb-4 animate-pulse" />
          <p className="text-lg text-gray-600">Загрузка вашего прогресса...</p>
        </div>
      </div>
    );
  }

  // Если пользователь не аутентифицирован, не показываем ничего (будет редирект)
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <Brain className="w-8 h-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-xl font-bold text-gray-900">NumerOM</h1>
                <p className="text-xs text-gray-500">Система обучения V2</p>
              </div>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex space-x-8">
              {filteredNavigation.map((item) => (
                <Button
                  key={item.id}
                  variant={location.pathname.startsWith(`/${item.id}`) ? "default" : "ghost"}
                  onClick={() => handleNavigation(item.id)}
                  className="flex items-center space-x-2"
                >
                  {item.icon}
                  <span>{item.label}</span>
                </Button>
              ))}
            </nav>

            {/* User Menu */}
            <div className="flex items-center space-x-4">
              {/* User Info */}
              <div className="hidden sm:flex items-center space-x-3">
                <Avatar className="w-8 h-8">
                  <AvatarFallback className="bg-blue-100 text-blue-600">
                    {user?.name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                  </AvatarFallback>
                </Avatar>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">
                    {user?.name || 'Пользователь'}
                  </p>
                  {isAdmin && (
                    <Badge variant="secondary" className="text-xs">
                      Администратор
                    </Badge>
                  )}
                </div>
              </div>

              {/* Logout Button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="text-gray-600 hover:text-gray-900"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:inline ml-2">Выйти</span>
              </Button>

              {/* Mobile Menu Button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setMenuOpen(!menuOpen)}
                className="md:hidden"
              >
                <Menu className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation */}
        {menuOpen && (
          <div className="md:hidden bg-white border-t border-gray-200">
            <div className="px-2 pt-2 pb-3 space-y-1">
              {filteredNavigation.map((item) => (
                <Button
                  key={item.id}
                  variant={location.pathname.startsWith(`/${item.id}`) ? "default" : "ghost"}
                  onClick={() => handleNavigation(item.id)}
                  className="w-full justify-start"
                >
                  {item.icon}
                  <span className="ml-2">{item.label}</span>
                </Button>
              ))}
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section - Level & Points */}
        <div className="mb-8">
          <Card className="border-0 shadow-2xl bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-600 text-white overflow-hidden relative">
            {/* Decorative Background */}
            <div className="absolute inset-0 opacity-10">
              <div className="absolute top-0 right-0 w-64 h-64 bg-white rounded-full -mr-32 -mt-32"></div>
              <div className="absolute bottom-0 left-0 w-96 h-96 bg-white rounded-full -ml-48 -mb-48"></div>
            </div>
            
            <CardContent className="pt-8 pb-8 relative z-10">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Level Info */}
                <div className="text-center md:text-left">
                  <div className="flex items-center justify-center md:justify-start mb-4">
                    <div className={`w-20 h-20 rounded-full bg-gradient-to-br ${getLevelColor(stats?.level || 1)} flex items-center justify-center text-4xl shadow-lg`}>
                      {getLevelIcon(stats?.level || 1)}
                    </div>
                  </div>
                  <h2 className="text-3xl font-bold mb-2">
                    Уровень {stats?.level || 1}
                  </h2>
                  <p className="text-xl text-blue-100 mb-4">
                    {stats?.level_name || 'Новичок'}
                  </p>
                  <div className="bg-white/20 rounded-lg p-3 backdrop-blur-sm">
                    <div className="flex justify-between text-sm mb-2">
                      <span>До следующего уровня</span>
                      <span className="font-bold">{stats?.progress_to_next_level || 0}%</span>
                    </div>
                    <Progress value={stats?.progress_to_next_level || 0} className="h-2 bg-white/30" />
                    <p className="text-xs text-blue-100 mt-2">
                      {stats?.total_points || 0} / {stats?.next_level_points || 100} баллов
                    </p>
                  </div>
                </div>

                {/* Total Points */}
                <div className="text-center">
                  <Trophy className="w-16 h-16 mx-auto mb-4 text-yellow-300" />
                  <h3 className="text-5xl font-bold mb-2">
                    {stats?.total_points || 0}
                  </h3>
                  <p className="text-xl text-blue-100">
                    Всего баллов
                  </p>
                  <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
                    <div className="bg-white/20 rounded-lg p-2 backdrop-blur-sm">
                      <Zap className="w-4 h-4 mx-auto mb-1" />
                      <p className="font-bold">{stats?.points_breakdown?.challenges || 0}</p>
                      <p className="text-xs text-blue-100">Челленджи</p>
                    </div>
                    <div className="bg-white/20 rounded-lg p-2 backdrop-blur-sm">
                      <Target className="w-4 h-4 mx-auto mb-1" />
                      <p className="font-bold">{stats?.points_breakdown?.quizzes || 0}</p>
                      <p className="text-xs text-blue-100">Тесты</p>
                    </div>
                    <div className="bg-white/20 rounded-lg p-2 backdrop-blur-sm">
                      <Brain className="w-4 h-4 mx-auto mb-1" />
                      <p className="font-bold">{stats?.points_breakdown?.exercises || stats?.points_breakdown?.exercise_review || 0}</p>
                      <p className="text-xs text-blue-100">Упражнения</p>
                    </div>
                    <div className="bg-white/20 rounded-lg p-2 backdrop-blur-sm">
                      <Clock className="w-4 h-4 mx-auto mb-1" />
                      <p className="font-bold">{stats?.points_breakdown?.time || 0}</p>
                      <p className="text-xs text-blue-100">Время</p>
                    </div>
                    <div className="bg-white/20 rounded-lg p-2 backdrop-blur-sm">
                      <Eye className="w-4 h-4 mx-auto mb-1" />
                      <p className="font-bold">{stats?.points_breakdown?.videos || 0}</p>
                      <p className="text-xs text-blue-100">Видео</p>
                    </div>
                    <div className="bg-white/20 rounded-lg p-2 backdrop-blur-sm">
                      <FileText className="w-4 h-4 mx-auto mb-1" />
                      <p className="font-bold">{stats?.points_breakdown?.files || 0}</p>
                      <p className="text-xs text-blue-100">Файлы</p>
                    </div>
                  </div>
                </div>

                {/* Achievements Preview */}
                <div className="text-center md:text-right">
                  <Award className="w-16 h-16 mx-auto md:ml-auto mb-4 text-yellow-300" />
                  <h3 className="text-3xl font-bold mb-2">
                    {stats?.total_achievements || 0}
                  </h3>
                  <p className="text-xl text-blue-100 mb-4">
                    Достижений
                  </p>
                  <Button
                    onClick={() => {
                      // Прокрутка к секции достижений
                      document.getElementById('achievements-section')?.scrollIntoView({ behavior: 'smooth' });
                    }}
                    className="bg-white/20 hover:bg-white/30 text-white border-white/30"
                    variant="outline"
                  >
                    <Star className="w-4 h-4 mr-2" />
                    Посмотреть все
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Lessons Progress */}
          <Card 
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              console.log('=== LESSONS CARD CLICKED ===');
              console.log('Current location:', window.location.pathname);
              console.log('Navigating to lesson page');
              navigate('/learning-v2-lesson/48fddd0b-4b00-4a99-9fed-21513f5b484b');
            }}
            className="cursor-pointer select-none hover:shadow-lg transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] h-full border-2 border-transparent hover:border-blue-200"
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                e.stopPropagation();
                console.log('Lessons card key pressed');
                navigate('/learning-v2-lesson/48fddd0b-4b00-4a99-9fed-21513f5b484b');
              }
            }}
            style={{ WebkitTapHighlightColor: 'transparent' }}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <BookOpen className="w-8 h-8 text-blue-600" />
                <Badge variant="secondary" className="text-lg font-bold">
                  {stats?.lessons?.completion_percentage || 0}%
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <h3 className="text-2xl font-bold mb-1">
                {stats?.lessons?.completed || 0} / {stats?.lessons?.total || 0}
              </h3>
              <p className="text-sm text-gray-600 mb-3">Уроков завершено</p>
              <Progress value={stats?.lessons?.completion_percentage || 0} className="h-2" />
              {stats?.lessons?.in_progress > 0 && (
                <p className="text-xs text-gray-500 mt-2">
                  {stats.lessons.in_progress} в процессе
                </p>
              )}
            </CardContent>
          </Card>

          {/* Challenges */}
          <Card 
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              console.log('=== CHALLENGES CARD CLICKED ===');
              console.log('Navigating to lesson page');
              navigate('/learning-v2-lesson/48fddd0b-4b00-4a99-9fed-21513f5b484b');
            }}
            className="cursor-pointer select-none hover:shadow-lg transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] h-full border-2 border-transparent hover:border-yellow-200"
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                e.stopPropagation();
                navigate('/learning-v2-lesson/48fddd0b-4b00-4a99-9fed-21513f5b484b');
              }
            }}
            style={{ WebkitTapHighlightColor: 'transparent' }}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <Zap className="w-8 h-8 text-yellow-600" />
                <Flame className="w-6 h-6 text-orange-500" />
              </div>
            </CardHeader>
            <CardContent>
              <h3 className="text-2xl font-bold mb-1">
                {stats?.total_challenge_attempts || stats?.activity?.total_challenges || 0}
              </h3>
              <p className="text-sm text-gray-600 mb-3">Челленджей пройдено</p>
              <p className="text-xs text-yellow-600 font-semibold mb-1">
                {stats?.points_breakdown?.challenges || 0} баллов
              </p>
              {stats?.activity?.recent_challenges > 0 && (
                <div className="flex items-center text-green-600 text-sm">
                  <TrendingUp className="w-4 h-4 mr-1" />
                  <span>+{stats.activity.recent_challenges} за месяц</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quizzes */}
          <Card 
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              console.log('=== QUIZZES CARD CLICKED ===');
              console.log('Navigating to lesson page');
              navigate('/learning-v2-lesson/48fddd0b-4b00-4a99-9fed-21513f5b484b');
            }}
            className="cursor-pointer select-none hover:shadow-lg transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] h-full border-2 border-transparent hover:border-green-200"
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                e.stopPropagation();
                navigate('/learning-v2-lesson/48fddd0b-4b00-4a99-9fed-21513f5b484b');
              }
            }}
            style={{ WebkitTapHighlightColor: 'transparent' }}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <Target className="w-8 h-8 text-green-600" />
                <CheckCircle2 className="w-6 h-6 text-green-500" />
              </div>
            </CardHeader>
            <CardContent>
              <h3 className="text-2xl font-bold mb-1">
                {stats?.total_quiz_attempts || stats?.activity?.total_quizzes || 0}
              </h3>
              <p className="text-sm text-gray-600 mb-3">Тестов пройдено</p>
              <p className="text-xs text-green-600 font-semibold mb-1">
                {stats?.points_breakdown?.quizzes || 0} баллов
              </p>
              {stats?.activity?.recent_quizzes > 0 && (
                <div className="flex items-center text-green-600 text-sm">
                  <TrendingUp className="w-4 h-4 mr-1" />
                  <span>+{stats.activity.recent_quizzes} за месяц</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Exercises */}
          <Card 
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              console.log('=== EXERCISES CARD CLICKED ===');
              console.log('Navigating to lesson page');
              navigate('/learning-v2-lesson/48fddd0b-4b00-4a99-9fed-21513f5b484b');
            }}
            className="cursor-pointer select-none hover:shadow-lg transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] h-full border-2 border-transparent hover:border-purple-200"
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                e.stopPropagation();
                navigate('/learning-v2-lesson/48fddd0b-4b00-4a99-9fed-21513f5b484b');
              }
            }}
            style={{ WebkitTapHighlightColor: 'transparent' }}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <Brain className="w-8 h-8 text-purple-600" />
                <BarChart3 className="w-6 h-6 text-purple-500" />
              </div>
            </CardHeader>
            <CardContent>
              <h3 className="text-2xl font-bold mb-1">
                {stats?.total_exercises_completed || stats?.activity?.total_exercises || 0}
              </h3>
              <p className="text-sm text-gray-600 mb-3">Упражнений выполнено</p>
              <p className="text-xs text-purple-600 font-semibold mb-1">
                {stats?.points_breakdown?.exercises || stats?.points_breakdown?.exercise_review || 0} баллов
              </p>
              {stats?.activity?.recent_exercises > 0 && (
                <div className="flex items-center text-green-600 text-sm">
                  <TrendingUp className="w-4 h-4 mr-1" />
                  <span>+{stats.activity.recent_exercises} за месяц</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Activity Chart & Recent Achievements */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Activity Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Calendar className="w-5 h-5 text-blue-600 mr-2" />
                Активность за неделю
              </CardTitle>
              <CardDescription>
                Ваша активность за последние 7 дней
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-end justify-between h-48 gap-2">
                {stats?.activity_chart?.map((day, index) => {
                  const maxActivity = Math.max(...(stats?.activity_chart?.map(d => d.activity) || [1]));
                  const height = maxActivity > 0 ? (day.activity / maxActivity) * 100 : 0;
                  
                  return (
                    <div key={index} className="flex-1 flex flex-col items-center">
                      <div className="relative w-full flex-1 flex items-end">
                        <div
                          className={`w-full rounded-t-lg transition-all ${
                            day.activity > 0 
                              ? 'bg-gradient-to-t from-blue-500 to-blue-400 hover:from-blue-600 hover:to-blue-500' 
                              : 'bg-gray-200'
                          }`}
                          style={{ height: `${Math.max(height, 5)}%` }}
                          title={`${day.day_name}: ${day.activity} активностей`}
                        >
                          {day.activity > 0 && (
                            <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs font-bold text-gray-700">
                              {day.activity}
                            </div>
                          )}
                        </div>
                      </div>
                      <p className="text-xs text-gray-600 mt-2 font-medium">{day.day_name}</p>
                      <p className="text-xs text-gray-400">{day.date}</p>
                    </div>
                  );
                })}
              </div>
              {stats?.activity_chart?.every(d => d.activity === 0) && (
                <p className="text-center text-gray-500 mt-4">
                  Начните обучение, чтобы увидеть вашу активность!
                </p>
              )}
            </CardContent>
          </Card>

          {/* Recent Achievements */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Star className="w-5 h-5 text-yellow-600 mr-2" />
                Последние достижения
              </CardTitle>
              <CardDescription>
                Ваши недавние успехи
              </CardDescription>
            </CardHeader>
            <CardContent>
              {stats?.recent_achievements && stats.recent_achievements.length > 0 ? (
                <div className="space-y-3">
                  {stats.recent_achievements.map((achievement, index) => (
                    <div key={index} className="flex items-start gap-3 p-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg hover:shadow-md transition-shadow">
                      <div className="text-2xl">{achievement.icon}</div>
                      <div className="flex-1">
                        <p className="font-medium text-sm text-gray-900">{achievement.title}</p>
                        <p className="text-xs text-gray-500">{achievement.date}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Trophy className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">Пока нет достижений</p>
                  <p className="text-sm text-gray-400 mt-2">Начните обучение, чтобы получить первые награды!</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Achievements Section */}
        <div id="achievements-section" className="mb-8">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-2xl">
                <Award className="w-6 h-6 text-yellow-600 mr-2" />
                Достижения
              </CardTitle>
              <CardDescription>
                Коллекция ваших наград и достижений
              </CardDescription>
            </CardHeader>
            <CardContent>
              {stats?.achievements && stats.achievements.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {stats.achievements.map((achievement) => (
                    <div
                      key={achievement.id}
                      className="relative group"
                    >
                      <div className={`p-6 rounded-xl border-2 text-center transition-all ${
                        achievement.earned
                          ? 'bg-gradient-to-br from-yellow-50 to-orange-50 border-yellow-300 hover:shadow-lg hover:scale-105'
                          : 'bg-gray-50 border-gray-200 opacity-50'
                      }`}>
                        <div className="text-4xl mb-3">{achievement.icon}</div>
                        <h4 className="font-bold text-sm mb-1">{achievement.title}</h4>
                        <p className="text-xs text-gray-600">{achievement.description}</p>
                        {achievement.earned && (
                          <Badge className="mt-3 bg-green-500">
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            Получено
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Award className="w-24 h-24 text-gray-300 mx-auto mb-4" />
                  <p className="text-lg text-gray-500 mb-2">Пока нет достижений</p>
                  <p className="text-sm text-gray-400 mb-6">
                    Завершайте уроки, проходите челленджи и тесты, чтобы получать награды!
                  </p>
                  <Button onClick={() => navigate('/learning-v2-lesson/48fddd0b-4b00-4a99-9fed-21513f5b484b')} className="bg-gradient-to-r from-blue-600 to-indigo-600">
                    <Brain className="w-4 h-4 mr-2" />
                    Начать обучение
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Детальная аналитика челленджей */}
        {stats?.challenge_analytics && stats.challenge_analytics.details && stats.challenge_analytics.details.length > 0 && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="flex items-center text-xl">
                <Zap className="w-6 h-6 text-yellow-600 mr-2" />
                Детальная аналитика челленджей
              </CardTitle>
              <CardDescription>
                Подробная статистика по всем вашим челленджам
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Общая статистика */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-gradient-to-br from-yellow-50 to-orange-50 p-4 rounded-lg border border-yellow-200">
                  <p className="text-sm text-gray-600 mb-1">Всего дней пройдено</p>
                  <p className="text-3xl font-bold text-yellow-600">{stats.challenge_analytics.total_days_completed}</p>
                </div>
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200">
                  <p className="text-sm text-gray-600 mb-1">Время на челленджи</p>
                  <p className="text-3xl font-bold text-blue-600">{stats.challenge_analytics.total_time_hours}ч</p>
                  <p className="text-xs text-gray-500 mt-1">{stats.challenge_analytics.total_time_minutes} минут</p>
                </div>
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-4 rounded-lg border border-green-200">
                  <p className="text-sm text-gray-600 mb-1">Завершено челленджей</p>
                  <p className="text-3xl font-bold text-green-600">
                    {stats.challenge_analytics.details.filter(c => c.is_completed).length}
                  </p>
                </div>
                <div className="bg-gradient-to-br from-red-50 to-pink-50 p-4 rounded-lg border border-red-200">
                  <p className="text-sm text-gray-600 mb-1">Дней с проблемами</p>
                  <p className="text-3xl font-bold text-red-600">{stats.challenge_analytics.problem_days?.length || 0}</p>
                </div>
              </div>

              {/* Детали по каждому челленджу */}
              <div className="space-y-4">
                {stats.challenge_analytics.details.map((challenge, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h4 className="font-semibold text-lg mb-1">{challenge.lesson_title}</h4>
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <span>День {challenge.current_day} из {challenge.total_days || '?'}</span>
                          <span className={challenge.is_completed ? "text-green-600 font-semibold" : "text-orange-600"}>
                            {challenge.is_completed ? "✓ Завершен" : "В процессе"}
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-yellow-600">{challenge.points_earned}</p>
                        <p className="text-xs text-gray-500">баллов</p>
                      </div>
                    </div>
                    
                    {/* Прогресс-бар */}
                    <div className="mb-3">
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600">Прогресс: {challenge.completed_days} / {challenge.total_days || '?'} дней</span>
                        <span className="font-semibold">{challenge.completion_percentage}%</span>
                      </div>
                      <Progress value={challenge.completion_percentage} className="h-3" />
                    </div>

                    {/* Дополнительная информация */}
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                      <div>
                        <p className="text-gray-500">Время осознания</p>
                        <p className="font-semibold">{challenge.time_minutes} мин</p>
                      </div>
                      {challenge.started_at && (
                        <div>
                          <p className="text-gray-500">Начало</p>
                          <p className="font-semibold">{new Date(challenge.started_at).toLocaleDateString('ru-RU')}</p>
                        </div>
                      )}
                      {challenge.completed_at && (
                        <div>
                          <p className="text-gray-500">Завершение</p>
                          <p className="font-semibold">{new Date(challenge.completed_at).toLocaleDateString('ru-RU')}</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Дни с проблемами */}
              {stats.challenge_analytics.problem_days && stats.challenge_analytics.problem_days.length > 0 && (
                <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <h5 className="font-semibold text-red-800 mb-3 flex items-center">
                    <Calendar className="w-4 h-4 mr-2" />
                    Дни с проблемами выполнения ({stats.challenge_analytics.problem_days.length})
                  </h5>
                  <div className="space-y-2">
                    {stats.challenge_analytics.problem_days.map((problem, idx) => (
                      <div key={idx} className="text-sm text-red-700">
                        <span className="font-semibold">{problem.lesson_title}</span> - День {problem.day}: {problem.reason}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Детальная аналитика тестов */}
        {stats?.quiz_analytics && stats.quiz_analytics.details && stats.quiz_analytics.details.length > 0 && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="flex items-center text-xl">
                <Target className="w-6 h-6 text-green-600 mr-2" />
                Детальная аналитика тестов
              </CardTitle>
              <CardDescription>
                Подробная статистика по всем вашим тестам
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Общая статистика */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-4 rounded-lg border border-green-200">
                  <p className="text-sm text-gray-600 mb-1">Всего попыток</p>
                  <p className="text-3xl font-bold text-green-600">{stats.quiz_analytics.total_attempts}</p>
                </div>
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200">
                  <p className="text-sm text-gray-600 mb-1">Максимальный балл</p>
                  <p className="text-3xl font-bold text-blue-600">{stats.quiz_analytics.max_score}%</p>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-4 rounded-lg border border-purple-200">
                  <p className="text-sm text-gray-600 mb-1">Средний балл</p>
                  <p className="text-3xl font-bold text-purple-600">{stats.quiz_analytics.avg_score}%</p>
                </div>
                <div className="bg-gradient-to-br from-yellow-50 to-orange-50 p-4 rounded-lg border border-yellow-200">
                  <p className="text-sm text-gray-600 mb-1">Всего баллов</p>
                  <p className="text-3xl font-bold text-yellow-600">{stats?.points_breakdown?.quizzes || 0}</p>
                </div>
              </div>

              {/* Детали по каждому тесту */}
              <div className="space-y-4">
                {stats.quiz_analytics.details.map((quiz, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h4 className="font-semibold text-lg mb-1">{quiz.lesson_title}</h4>
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <span>{quiz.total_attempts} попыт{quiz.total_attempts === 1 ? 'ка' : quiz.total_attempts < 5 ? 'ки' : 'ок'}</span>
                          <span className="text-green-600 font-semibold">
                            {quiz.passed_attempts} сдано ({quiz.pass_percentage}%)
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-green-600">{quiz.best_score}%</p>
                        <p className="text-xs text-gray-500">лучший результат</p>
                      </div>
                    </div>
                    
                    {/* Прогресс-бары */}
                    <div className="space-y-2 mb-3">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-gray-600">Лучший результат</span>
                          <span className="font-semibold">{quiz.best_score_percentage}% от максимума</span>
                        </div>
                        <Progress value={quiz.best_score_percentage} className="h-3" />
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-gray-600">Средний результат</span>
                          <span className="font-semibold">{quiz.avg_score_percentage}% от максимума</span>
                        </div>
                        <Progress value={quiz.avg_score_percentage} className="h-3 bg-gray-200" />
                      </div>
                    </div>

                    {/* Дополнительная информация */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                      <div>
                        <p className="text-gray-500">Средний балл</p>
                        <p className="font-semibold">{quiz.avg_score}%</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Максимум возможный</p>
                        <p className="font-semibold">{quiz.max_possible_score} баллов</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Всего баллов</p>
                        <p className="font-semibold">{quiz.total_points_earned}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Время осознания</p>
                        <p className="font-semibold">{quiz.total_time_minutes} мин</p>
                      </div>
                    </div>

                    {/* График попыток */}
                    {quiz.attempts && quiz.attempts.length > 1 && (
                      <div className="mt-4 pt-4 border-t border-gray-200">
                        <p className="text-sm font-semibold text-gray-700 mb-2">История попыток:</p>
                        <div className="flex items-end gap-2 h-24">
                          {quiz.attempts.map((attempt, idx) => {
                            const maxScore = Math.max(...quiz.attempts.map(a => a.score || 0), 100);
                            const height = ((attempt.score || 0) / maxScore) * 100;
                            return (
                              <div key={idx} className="flex-1 flex flex-col items-center">
                                <div className="relative w-full flex-1 flex items-end">
                                  <div
                                    className={`w-full rounded-t transition-all ${
                                      attempt.passed
                                        ? 'bg-gradient-to-t from-green-500 to-green-400'
                                        : 'bg-gradient-to-t from-orange-500 to-orange-400'
                                    }`}
                                    style={{ height: `${Math.max(height, 5)}%` }}
                                    title={`Попытка ${idx + 1}: ${attempt.score}% ${attempt.passed ? '✓' : '✗'}`}
                                  >
                                    {attempt.score > 0 && (
                                      <div className="absolute -top-5 left-1/2 transform -translate-x-1/2 text-xs font-bold text-gray-700 whitespace-nowrap">
                                        {attempt.score}%
                                      </div>
                                    )}
                                  </div>
                                </div>
                                <p className="text-xs text-gray-500 mt-1">#{idx + 1}</p>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Learning Section */}
          <Card className="hover:shadow-xl transition-shadow border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50">
            <CardHeader>
              <CardTitle className="flex items-center text-xl">
                <BookOpen className="w-6 h-6 text-blue-600 mr-2" />
                Продолжить обучение
              </CardTitle>
              <CardDescription>
                Интерактивные уроки по нумерологии
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Прогресс:</span>
                  <span className="font-bold text-blue-600">
                    {stats?.lessons?.completed || 0} / {stats?.lessons?.total || 0} уроков
                  </span>
                </div>
                <Progress value={stats?.lessons?.completion_percentage || 0} className="h-2" />
                <Button
                  onClick={() => navigate('/learning-v2-lesson/48fddd0b-4b00-4a99-9fed-21513f5b484b')}
                  className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                  size="lg"
                >
                  <Brain className="w-5 h-5 mr-2" />
                  Перейти к урокам
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Admin Section (only for admins) */}
          {isAdmin && (
            <Card className="hover:shadow-xl transition-shadow border-2 border-purple-200 bg-gradient-to-br from-purple-50 to-pink-50">
              <CardHeader>
                <CardTitle className="flex items-center text-xl">
                  <Crown className="w-6 h-6 text-purple-600 mr-2" />
                  Администрирование
                </CardTitle>
                <CardDescription>
                  Управление контентом и уроками
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  onClick={() => navigate('/admin-v2')}
                  variant="outline"
                  className="w-full border-purple-300 text-purple-700 hover:bg-purple-100"
                  size="lg"
                >
                  <Settings className="w-5 h-5 mr-2" />
                  Открыть админ-панель
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </main>

    </div>
  );
};

export default UserDashboardV2;

