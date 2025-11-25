import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  BookOpen, 
  Brain, 
  Target, 
  Zap,
  ChevronLeft,
  Lightbulb
} from 'lucide-react';
import { useAuth } from './AuthContext';
import { getBackendUrl } from '../utils/backendUrl';

const backendUrl = getBackendUrl();

const AnalyticsDetailPage = () => {
  const { section } = useParams(); // 'lessons', 'challenges', 'quizzes', 'exercises'
  const navigate = useNavigate();
  const { isAuthenticated, isInitialized } = useAuth();
  
  const [stats, setStats] = useState(null);
  const [detailedAnalytics, setDetailedAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    console.log('=== AnalyticsDetailPage useEffect ===');
    console.log('Section:', section);
    console.log('isInitialized:', isInitialized);
    console.log('isAuthenticated:', isAuthenticated);
    
    if (!isInitialized) {
      console.log('Waiting for initialization...');
      return;
    }

    if (!isAuthenticated) {
      console.log('Not authenticated, redirecting...');
      navigate('/');
      return;
    }

    const token = localStorage.getItem('token');
    if (!token) {
      console.log('No token, redirecting...');
      navigate('/');
      return;
    }

    console.log('Loading dashboard stats and detailed analytics...');
    loadDashboardStats();
    loadDetailedAnalytics();
  }, [isInitialized, isAuthenticated, navigate, section]);

  const loadDashboardStats = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/');
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

      if (response.status === 401) {
        localStorage.removeItem('token');
        navigate('/');
        return;
      }

      if (!response.ok) {
        console.error('Dashboard stats response not ok:', response.status, response.statusText);
        return;
      }

      const data = await response.json();
      setStats(data.stats);
    } catch (error) {
      console.error('Error loading dashboard stats:', error);
    }
  };

  const loadDetailedAnalytics = async () => {
    try {
      console.log('=== LOADING DETAILED ANALYTICS ===');
      console.log('Section:', section);
      console.log('Backend URL:', backendUrl);
      setLoading(true);
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No token found');
        navigate('/');
        return;
      }

      const url = `${backendUrl}/api/student/analytics/${section}`;
      console.log('Fetching from URL:', url);

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });

      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);

      if (response.status === 401) {
        console.error('Unauthorized - removing token');
        localStorage.removeItem('token');
        navigate('/');
        return;
      }

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Detailed analytics response not ok:', response.status, response.statusText);
        console.error('Error response:', errorText);
        return;
      }

      const data = await response.json();
      console.log('Received data:', data);
      console.log('Analytics array:', data.analytics);
      console.log('Analytics length:', data.analytics?.length);
      
      setDetailedAnalytics(data.analytics);
      console.log('Detailed analytics set successfully');
    } catch (error) {
      console.error('Error loading detailed analytics:', error);
      console.error('Error stack:', error.stack);
    } finally {
      setLoading(false);
      console.log('Loading finished');
    }
  };

  const getTitle = () => {
    switch (section) {
      case 'lessons':
        return 'Детальная аналитика по урокам';
      case 'challenges':
        return 'Детальная аналитика по челленджам';
      case 'quizzes':
        return 'Детальная аналитика по тестам';
      case 'exercises':
        return 'Детальная аналитика по упражнениям';
      default:
        return 'Аналитика';
    }
  };

  const getIcon = () => {
    switch (section) {
      case 'lessons':
        return <BookOpen className="w-6 h-6 text-blue-600" />;
      case 'challenges':
        return <Zap className="w-6 h-6 text-yellow-600" />;
      case 'quizzes':
        return <Target className="w-6 h-6 text-green-600" />;
      case 'exercises':
        return <Brain className="w-6 h-6 text-purple-600" />;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка данных...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16 gap-4">
            <Button
              variant="ghost"
              onClick={() => navigate('/learning-v2-dashboard')}
              className="flex items-center gap-2"
            >
              <ChevronLeft className="w-4 h-4" />
              <span className="hidden sm:inline">Назад к дашборду</span>
              <span className="sm:hidden">Назад</span>
            </Button>
            <div className="flex items-center gap-3">
              {getIcon()}
              <h1 className="text-xl font-bold text-gray-900">{getTitle()}</h1>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!stats && (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Загрузка данных...</p>
              <p className="text-sm text-gray-500 mt-2">Пожалуйста, подождите</p>
            </div>
          </div>
        )}

        {stats && (
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">Обзор</TabsTrigger>
              <TabsTrigger value="statistics">Статистика</TabsTrigger>
              <TabsTrigger value="charts">Графики</TabsTrigger>
              <TabsTrigger value="recommendations">Рекомендации</TabsTrigger>
            </TabsList>
            
            {/* Debug info */}
            {process.env.NODE_ENV === 'development' && (
              <div className="mt-4 p-4 bg-gray-100 rounded text-xs">
                <p><strong>Debug Info:</strong></p>
                <p>Section: {section}</p>
                <p>Stats loaded: {stats ? 'Yes' : 'No'}</p>
                <p>Detailed analytics loaded: {detailedAnalytics ? 'Yes' : 'No'}</p>
                <p>Detailed analytics length: {detailedAnalytics?.length || 0}</p>
                <p>Loading: {loading ? 'Yes' : 'No'}</p>
                {detailedAnalytics && (
                  <pre className="mt-2 overflow-auto max-h-40">
                    {JSON.stringify(detailedAnalytics, null, 2)}
                  </pre>
                )}
              </div>
            )}

            {/* Аналитика по урокам */}
            {section === 'lessons' && (
              <>
                <TabsContent value="overview" className="space-y-4 mt-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Завершено уроков</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-blue-600">
                          {stats?.lessons?.completed || 0} / {stats?.lessons?.total || 0}
                        </div>
                        <Progress value={stats?.lessons?.completion_percentage || 0} className="mt-2" />
                        <p className="text-xs text-gray-500 mt-1">{stats?.lessons?.completion_percentage || 0}% завершено</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">В процессе</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-orange-600">
                          {stats?.lessons?.in_progress || 0}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">Активных уроков</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Среднее время</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-green-600">
                          {stats?.time_stats?.study_minutes ? Math.round(stats.time_stats.study_minutes / (stats?.lessons?.completed || 1)) : 0}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">минут на урок</p>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="statistics" className="space-y-4 mt-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Детальная статистика</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm text-gray-600">Всего времени изучения</p>
                          <p className="text-2xl font-bold">{stats?.time_stats?.study_minutes || 0} минут</p>
                          <p className="text-xs text-gray-500">{Math.round((stats?.time_stats?.study_minutes || 0) / 60)} часов</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Время просмотра видео</p>
                          <p className="text-2xl font-bold">{stats?.time_stats?.video_minutes || 0} минут</p>
                          <p className="text-xs text-gray-500">{Math.round((stats?.time_stats?.video_minutes || 0) / 60)} часов</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Просмотрено файлов</p>
                          <p className="text-2xl font-bold">{stats?.files?.views || 0}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Скачано файлов</p>
                          <p className="text-2xl font-bold">{stats?.files?.downloads || 0}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  
                  {/* Детали по каждому уроку */}
                  {detailedAnalytics && detailedAnalytics.length > 0 ? (
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">Детали по урокам ({detailedAnalytics.length})</h3>
                      {detailedAnalytics.map((lesson, index) => (
                        <Card key={index}>
                          <CardHeader>
                            <CardTitle>{lesson.lesson_title}</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                              <div>
                                <p className="text-sm text-gray-600">Прогресс</p>
                                <p className="text-xl font-bold">{lesson.completion_percentage}%</p>
                                <Progress value={lesson.completion_percentage} className="mt-2" />
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Время изучения</p>
                                <p className="text-xl font-bold">{lesson.time_minutes} мин</p>
                                <p className="text-xs text-gray-500">{Math.round(lesson.time_minutes / 60)} ч</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Видео время</p>
                                <p className="text-xl font-bold">{lesson.video_minutes} мин</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Файлы</p>
                                <p className="text-xl font-bold">{lesson.file_views} просмотров</p>
                                <p className="text-xs text-gray-500">{lesson.file_downloads} скачиваний</p>
                              </div>
                            </div>
                            {lesson.started_at && (
                              <div className="mt-4 pt-4 border-t">
                                <p className="text-sm text-gray-600">Начато: {new Date(lesson.started_at).toLocaleDateString('ru-RU')}</p>
                                {lesson.completed_at && (
                                  <p className="text-sm text-gray-600">Завершено: {new Date(lesson.completed_at).toLocaleDateString('ru-RU')}</p>
                                )}
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <Card>
                      <CardContent className="py-8 text-center text-gray-500">
                        {loading ? 'Загрузка данных...' : 'Нет данных об уроках'}
                        {!loading && detailedAnalytics && detailedAnalytics.length === 0 && (
                          <p className="text-xs mt-2">Попробуйте обновить страницу</p>
                        )}
                      </CardContent>
                    </Card>
                  )}
                </TabsContent>

                <TabsContent value="charts" className="space-y-4 mt-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>График активности по урокам</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {detailedAnalytics && detailedAnalytics.length > 0 ? (
                        <div className="space-y-4">
                          <div className="h-64 flex items-end justify-between gap-2">
                            {stats?.activity_chart?.map((day, index) => {
                              const maxActivity = Math.max(...(stats?.activity_chart?.map(d => d.activity) || [1]));
                              const height = maxActivity > 0 ? (day.activity / maxActivity) * 100 : 0;
                              return (
                                <div key={index} className="flex-1 flex flex-col items-center">
                                  <div className="relative w-full flex-1 flex items-end">
                                    <div
                                      className="w-full bg-gradient-to-t from-blue-500 to-blue-400 rounded-t transition-all hover:from-blue-600 hover:to-blue-500 cursor-pointer"
                                      style={{ height: `${Math.max(height, 5)}%` }}
                                      title={`${day.date}: ${day.activity} активностей`}
                                    />
                                  </div>
                                  <p className="text-xs text-gray-500 mt-2">{day.date}</p>
                                </div>
                              );
                            }) || <p className="text-gray-500">Нет данных</p>}
                          </div>
                          <div className="mt-6">
                            <h4 className="text-sm font-semibold mb-3">Прогресс по урокам:</h4>
                            <div className="space-y-2">
                              {detailedAnalytics.map((lesson, idx) => (
                                <div key={idx} className="flex items-center gap-3">
                                  <div className="flex-1">
                                    <div className="flex justify-between text-sm mb-1">
                                      <span className="font-medium">{lesson.lesson_title}</span>
                                      <span className="text-gray-600">{lesson.completion_percentage}%</span>
                                    </div>
                                    <Progress value={lesson.completion_percentage} className="h-2" />
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="h-64 flex items-center justify-center">
                          <p className="text-gray-500">Нет данных для отображения</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="recommendations" className="space-y-4 mt-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Lightbulb className="w-5 h-5 text-yellow-500" />
                        Рекомендации для улучшения
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {stats?.lessons?.completion_percentage < 50 && (
                        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                          <p className="font-semibold text-yellow-900 mb-2">⚠️ Низкий процент завершения</p>
                          <p className="text-sm text-yellow-800">Рекомендуем завершить начатые уроки перед переходом к новым. Это поможет лучше усвоить материал.</p>
                        </div>
                      )}
                      {stats?.time_stats?.study_minutes < 60 && (
                        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                          <p className="font-semibold text-blue-900 mb-2">💡 Увеличьте время изучения</p>
                          <p className="text-sm text-blue-800">Вы тратите мало времени на изучение. Рекомендуем уделять минимум 30 минут в день для лучшего усвоения материала.</p>
                        </div>
                      )}
                      {stats?.files?.views === 0 && (
                        <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
                          <p className="font-semibold text-purple-900 mb-2">📚 Изучите дополнительные материалы</p>
                          <p className="text-sm text-purple-800">Просмотрите файлы и видео, прикрепленные к урокам. Это поможет глубже понять материал.</p>
                        </div>
                      )}
                      {stats?.lessons?.completion_percentage >= 75 && (
                        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                          <p className="font-semibold text-green-900 mb-2">🎉 Отличный прогресс!</p>
                          <p className="text-sm text-green-800">Вы показываете отличные результаты! Продолжайте в том же духе и не забывайте про челленджи и тесты.</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
              </>
            )}

            {/* Аналитика по челленджам */}
            {section === 'challenges' && (
              <>
                <TabsContent value="overview" className="space-y-4 mt-6">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Дней пройдено</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-yellow-600">
                          {stats.challenge_analytics.total_days_completed || 0}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Время осознания</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-blue-600">
                          {stats.challenge_analytics.total_time_hours || 0}ч
                        </div>
                        <p className="text-xs text-gray-500">{stats.challenge_analytics.total_time_minutes || 0} мин</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Завершено</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-green-600">
                          {stats.challenge_analytics.details?.filter(c => c.is_completed).length || 0}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Баллов заработано</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-purple-600">
                          {stats?.points_breakdown?.challenges || 0}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="statistics" className="space-y-4 mt-6">
                  {detailedAnalytics && detailedAnalytics.length > 0 ? (
                    <div className="space-y-4">
                      {detailedAnalytics.map((challenge, index) => (
                        <Card key={index}>
                          <CardHeader>
                            <CardTitle>{challenge.lesson_title}</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                              <div>
                                <p className="text-sm text-gray-600">Прогресс</p>
                                <p className="text-xl font-bold">{challenge.completion_percentage}%</p>
                                <Progress value={challenge.completion_percentage} className="mt-2" />
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Дней завершено</p>
                                <p className="text-xl font-bold">{challenge.completed_days?.length || 0} / {challenge.total_days || '?'}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Время</p>
                                <p className="text-xl font-bold">{challenge.time_minutes} мин</p>
                                <p className="text-xs text-gray-500">{Math.round(challenge.time_minutes / 60)} ч</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Баллов</p>
                                <p className="text-xl font-bold">{challenge.points_earned}</p>
                              </div>
                            </div>
                            {challenge.started_at && (
                              <div className="mt-4 pt-4 border-t">
                                <p className="text-sm text-gray-600">Начато: {new Date(challenge.started_at).toLocaleDateString('ru-RU')}</p>
                                {challenge.completed_at && (
                                  <p className="text-sm text-gray-600">Завершено: {new Date(challenge.completed_at).toLocaleDateString('ru-RU')}</p>
                                )}
                                {challenge.daily_notes && challenge.daily_notes.length > 0 && (
                                  <div className="mt-2">
                                    <p className="text-sm font-semibold">Заметки по дням:</p>
                                    <ul className="text-sm text-gray-600 list-disc list-inside">
                                      {challenge.daily_notes.map((note, idx) => (
                                        <li key={idx}>День {note.day}: {note.note || 'Без заметки'}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <Card>
                      <CardContent className="py-8 text-center text-gray-500">
                        Нет данных о челленджах
                      </CardContent>
                    </Card>
                  )}
                </TabsContent>

                <TabsContent value="recommendations" className="space-y-4 mt-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Lightbulb className="w-5 h-5 text-yellow-500" />
                        Рекомендации
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {stats?.challenge_analytics?.problem_days && stats.challenge_analytics.problem_days.length > 0 && (
                        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                          <p className="font-semibold text-red-900 mb-2">⚠️ Дни с проблемами</p>
                          <ul className="list-disc list-inside text-sm text-red-800 space-y-1">
                            {stats.challenge_analytics.problem_days.map((problem, idx) => (
                              <li key={idx}>{problem.lesson_title} - День {problem.day}: {problem.reason}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {(() => {
                        const totalDays = stats?.challenge_analytics?.total_days_completed || detailedAnalytics?.reduce((sum, c) => sum + (c.completed_days?.length || 0), 0) || 0;
                        return totalDays < 10 && (
                          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                            <p className="font-semibold text-yellow-900 mb-2">💪 Увеличьте активность</p>
                            <p className="text-sm text-yellow-800">Попробуйте выполнять челленджи ежедневно. Регулярность - ключ к успеху!</p>
                          </div>
                        );
                      })()}
                      {detailedAnalytics && detailedAnalytics.length === 0 && (
                        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                          <p className="font-semibold text-blue-900 mb-2">📝 Начните челлендж</p>
                          <p className="text-sm text-blue-800">Вы еще не начали ни одного челленджа. Найдите урок с челленджем и начните свой путь к успеху!</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
              </>
            )}

            {/* Аналитика по тестам */}
            {section === 'quizzes' && (
              <>
                <TabsContent value="overview" className="space-y-4 mt-6">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Всего попыток</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-green-600">
                          {stats?.quiz_analytics?.total_attempts || detailedAnalytics?.reduce((sum, q) => sum + (q.total_attempts || 0), 0) || 0}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Максимальный балл</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-blue-600">
                          {stats?.quiz_analytics?.max_score || Math.max(...(detailedAnalytics?.map(q => q.best_score || 0) || [0]), 0)}%
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Средний балл</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-purple-600">
                          {stats?.quiz_analytics?.avg_score || (detailedAnalytics?.length > 0 ? Math.round(detailedAnalytics.reduce((sum, q) => sum + (q.avg_score || 0), 0) / detailedAnalytics.length) : 0)}%
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Баллов заработано</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-yellow-600">
                          {stats?.points_breakdown?.quizzes || detailedAnalytics?.reduce((sum, q) => sum + (q.total_points_earned || 0), 0) || 0}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="statistics" className="space-y-4 mt-6">
                  {detailedAnalytics && detailedAnalytics.length > 0 ? (
                    <div className="space-y-4">
                      {detailedAnalytics.map((quiz, index) => (
                        <Card key={index}>
                          <CardHeader>
                            <CardTitle>{quiz.lesson_title}</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                              <div>
                                <p className="text-sm text-gray-600">Попыток</p>
                                <p className="text-xl font-bold">{quiz.total_attempts}</p>
                                <p className="text-xs text-gray-500">{quiz.passed_attempts} успешных</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Лучший результат</p>
                                <p className="text-xl font-bold">{quiz.best_score}</p>
                                <p className="text-xs text-gray-500">из {quiz.max_possible_score}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Средний балл</p>
                                <p className="text-xl font-bold">{quiz.avg_score}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Баллов заработано</p>
                                <p className="text-xl font-bold">{quiz.total_points_earned}</p>
                                <p className="text-xs text-gray-500">{quiz.total_time_minutes} мин</p>
                              </div>
                            </div>
                            {quiz.attempts && quiz.attempts.length > 0 && (
                              <div className="mt-4">
                                <p className="text-sm font-semibold mb-2">История попыток:</p>
                                <div className="flex items-end gap-2 h-32">
                                  {quiz.attempts.map((attempt, idx) => {
                                    const maxScore = Math.max(...quiz.attempts.map(a => a.score || 0), quiz.max_possible_score);
                                    const height = maxScore > 0 ? ((attempt.score || 0) / maxScore) * 100 : 0;
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
                                            title={`Попытка ${idx + 1}: ${attempt.score} (${attempt.score_percentage}%)`}
                                          />
                                        </div>
                                        <p className="text-xs text-gray-500 mt-1">#{idx + 1}</p>
                                      </div>
                                    );
                                  })}
                                </div>
                                <div className="mt-4 space-y-2">
                                  {quiz.attempts.map((attempt, idx) => (
                                    <div key={idx} className="text-sm border-b pb-2">
                                      <div className="flex justify-between">
                                        <span>Попытка #{idx + 1}</span>
                                        <span className="font-semibold">{attempt.score} ({attempt.score_percentage}%)</span>
                                      </div>
                                      <div className="flex justify-between text-xs text-gray-500">
                                        <span>{attempt.passed ? '✅ Пройдено' : '❌ Не пройдено'}</span>
                                        <span>{attempt.points_earned} баллов • {attempt.time_spent_minutes} мин</span>
                                      </div>
                                      {attempt.attempted_at && (
                                        <p className="text-xs text-gray-400">{new Date(attempt.attempted_at).toLocaleString('ru-RU')}</p>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <Card>
                      <CardContent className="py-8 text-center text-gray-500">
                        Нет данных о тестах
                      </CardContent>
                    </Card>
                  )}
                </TabsContent>

                <TabsContent value="recommendations" className="space-y-4 mt-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Lightbulb className="w-5 h-5 text-yellow-500" />
                        Рекомендации
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {(() => {
                        const avgScore = stats?.quiz_analytics?.avg_score || (detailedAnalytics?.length > 0 ? detailedAnalytics.reduce((sum, q) => sum + (q.avg_score || 0), 0) / detailedAnalytics.length : 0);
                        const maxScore = stats?.quiz_analytics?.max_score || Math.max(...(detailedAnalytics?.map(q => q.best_score || 0) || [0]), 0);
                        
                        return (
                          <>
                            {avgScore < 70 && avgScore > 0 && (
                              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                                <p className="font-semibold text-red-900 mb-2">⚠️ Низкий средний балл</p>
                                <p className="text-sm text-red-800">Рекомендуем повторить материал перед повторной попыткой. Изучите теорию и упражнения более внимательно.</p>
                              </div>
                            )}
                            {maxScore >= 90 && (
                              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                                <p className="font-semibold text-green-900 mb-2">🎉 Отличные результаты!</p>
                                <p className="text-sm text-green-800">Вы показываете отличные знания! Продолжайте в том же духе.</p>
                              </div>
                            )}
                            {detailedAnalytics && detailedAnalytics.length === 0 && (
                              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                                <p className="font-semibold text-blue-900 mb-2">📝 Начните проходить тесты</p>
                                <p className="text-sm text-blue-800">Вы еще не прошли ни одного теста. Найдите урок с тестом и проверьте свои знания!</p>
                              </div>
                            )}
                          </>
                        );
                      })()}
                    </CardContent>
                  </Card>
                </TabsContent>
              </>
            )}

            {/* Аналитика по упражнениям */}
            {section === 'exercises' && (
              <>
                <TabsContent value="overview" className="space-y-4 mt-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Выполнено упражнений</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-purple-600">
                          {stats?.total_exercises_completed || 0}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Баллов заработано</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-green-600">
                          {stats?.points_breakdown?.exercises || stats?.points_breakdown?.exercise_review || 0}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Время на упражнения</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-blue-600">
                          {stats?.points_breakdown?.exercise_review_time_minutes || 0}
                        </div>
                        <p className="text-xs text-gray-500">минут</p>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="statistics" className="space-y-4 mt-6">
                  {detailedAnalytics && detailedAnalytics.length > 0 ? (
                    <div className="space-y-4">
                      {detailedAnalytics.map((lessonExercises, index) => (
                        <Card key={index}>
                          <CardHeader>
                            <CardTitle>{lessonExercises.lesson_title}</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                              <div>
                                <p className="text-sm text-gray-600">Всего упражнений</p>
                                <p className="text-xl font-bold">{lessonExercises.total_exercises}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Проверено</p>
                                <p className="text-xl font-bold">{lessonExercises.reviewed_exercises}</p>
                                <p className="text-xs text-gray-500">из {lessonExercises.total_exercises}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Баллов заработано</p>
                                <p className="text-xl font-bold">{lessonExercises.total_points_earned}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Время проверки</p>
                                <p className="text-xl font-bold">{lessonExercises.total_review_time_minutes} мин</p>
                              </div>
                            </div>
                            {lessonExercises.exercises && lessonExercises.exercises.length > 0 && (
                              <div className="mt-4 space-y-3">
                                <p className="text-sm font-semibold">Детали упражнений:</p>
                                {lessonExercises.exercises.map((exercise, idx) => (
                                  <div key={idx} className="border rounded-lg p-4">
                                    <div className="flex justify-between items-start mb-2">
                                      <span className="font-semibold">Упражнение #{idx + 1}</span>
                                      <span className={`px-2 py-1 rounded text-xs ${
                                        exercise.reviewed 
                                          ? exercise.points_earned > 0 
                                            ? 'bg-green-100 text-green-800' 
                                            : 'bg-red-100 text-red-800'
                                          : 'bg-yellow-100 text-yellow-800'
                                      }`}>
                                        {exercise.reviewed 
                                          ? exercise.points_earned > 0 
                                            ? '✅ Проверено' 
                                            : '❌ Не засчитано'
                                          : '⏳ Ожидает проверки'}
                                      </span>
                                    </div>
                                    <p className="text-sm text-gray-700 mb-2">{exercise.response_text}</p>
                                    {exercise.admin_comment && (
                                      <div className="mt-2 p-2 bg-blue-50 rounded">
                                        <p className="text-xs font-semibold text-blue-900">Комментарий преподавателя:</p>
                                        <p className="text-sm text-blue-800">{exercise.admin_comment}</p>
                                      </div>
                                    )}
                                    <div className="flex justify-between text-xs text-gray-500 mt-2">
                                      <span>Баллов: {exercise.points_earned}</span>
                                      {exercise.submitted_at && (
                                        <span>Отправлено: {new Date(exercise.submitted_at).toLocaleString('ru-RU')}</span>
                                      )}
                                      {exercise.reviewed_at && (
                                        <span>Проверено: {new Date(exercise.reviewed_at).toLocaleString('ru-RU')}</span>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <Card>
                      <CardContent className="py-8 text-center text-gray-500">
                        Нет данных об упражнениях
                      </CardContent>
                    </Card>
                  )}
                </TabsContent>

                <TabsContent value="recommendations" className="space-y-4 mt-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Lightbulb className="w-5 h-5 text-yellow-500" />
                        Рекомендации
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {stats?.total_exercises_completed < 5 && (
                        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                          <p className="font-semibold text-yellow-900 mb-2">💪 Увеличьте количество упражнений</p>
                          <p className="text-sm text-yellow-800">Выполняйте больше упражнений для лучшего закрепления материала. Практика - ключ к успеху!</p>
                        </div>
                      )}
                      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="font-semibold text-blue-900 mb-2">📝 Внимательно читайте комментарии</p>
                        <p className="text-sm text-blue-800">Обращайте внимание на комментарии преподавателя к вашим ответам. Это поможет улучшить результаты.</p>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </>
            )}
          </Tabs>
        )}
      </div>
    </div>
  );
};

export default AnalyticsDetailPage;

