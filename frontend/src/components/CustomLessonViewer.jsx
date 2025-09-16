import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Checkbox } from './ui/checkbox';
import { Progress } from './ui/progress';
import { 
  BookOpen, PlayCircle, CheckCircle, Clock, Target, Zap, 
  Star, Calendar, Award, ArrowRight, ArrowLeft, 
  Sparkles, Sun, Moon, Loader, Trophy, Heart,
  Brain, Lightbulb, FileText, Timer, Rocket, Eye, Download, Video,
  AlertCircle, Play
} from 'lucide-react';
import { useAuth } from './AuthContext';
import EnhancedVideoViewer from './EnhancedVideoViewer';
import ConsultationPDFViewer from './ConsultationPDFViewer';

const CustomLessonViewer = ({ lesson }) => {
  const { user } = useAuth();
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  
  // Состояния для управления уроком (ТОЧНО КАК В FIRSTLESSON)
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeSection, setActiveSection] = useState('theory');
  const [completedSections, setCompletedSections] = useState(new Set());
  const [overallProgress, setOverallProgress] = useState(0);
  
  // Состояния для квиза (ТОЧНО КАК В FIRSTLESSON)
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizResults, setQuizResults] = useState(null);
  const [quizSubmitting, setQuizSubmitting] = useState(false);
  
  // Состояния для челленджа (ТОЧНО КАК В FIRSTLESSON)
  const [challengeProgress, setChallengeProgress] = useState(null);
  const [challengeStarted, setChallengeStarted] = useState(false);
  const [selectedChallengeDay, setSelectedChallengeDay] = useState(1);
  const [challengeCompleted, setChallengeCompleted] = useState(false);
  const [challengeRating, setChallengeRating] = useState(0);
  
  // Состояния для трекера привычек (ТОЧНО КАК В FIRSTLESSON)
  const [habitTracker, setHabitTracker] = useState(null);
  const [todayHabits, setTodayHabits] = useState({});
  const [habitProgress, setHabitProgress] = useState(0);
  const [habitStreakDays, setHabitStreakDays] = useState(0);
  
  // Состояния для упражнений (ТОЧНО КАК В FIRSTLESSON)
  const [exerciseResponses, setExerciseResponses] = useState({});
  const [completedExercises, setCompletedExercises] = useState(new Set());
  const [savedExercises, setSavedExercises] = useState(new Set());
  
  // Состояния для медиа файлов
  const [lessonMedia, setLessonMedia] = useState({ videos: [], pdfs: [] });
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [selectedPDF, setSelectedPDF] = useState(null);
  
  useEffect(() => {
    if (lesson) {
      loadLessonMedia();
      loadUserProgress();
    }
  }, [lesson]);

  // Загрузка медиа файлов урока
  const loadLessonMedia = async () => {
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/api/lessons/media/${lesson.id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setLessonMedia({
          videos: data.videos || [],
          pdfs: data.pdfs || []
        });
      }
    } catch (err) {
      console.error('Ошибка загрузки медиа файлов:', err);
    }
  };

  // Загрузка прогресса пользователя (АДАПТИРОВАННАЯ ИЗ FIRSTLESSON)
  const loadUserProgress = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Загрузить общий прогресс урока
      const overallResponse = await fetch(
        `${backendUrl}/api/lessons/overall-progress/${lesson.id}`, 
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      
      if (overallResponse.ok) {
        const overallData = await overallResponse.json();
        setOverallProgress(overallData.overall_percentage || 0);
        
        // Обновить завершенные секции на основе данных с сервера
        const newCompletedSections = new Set();
        if (overallData.breakdown?.theory) newCompletedSections.add('theory');
        if (overallData.breakdown?.exercises) newCompletedSections.add('exercises');
        if (overallData.breakdown?.quiz) newCompletedSections.add('quiz');
        if (overallData.breakdown?.challenge) newCompletedSections.add('challenge');
        if (overallData.breakdown?.habits) newCompletedSections.add('habits');
        
        setCompletedSections(newCompletedSections);
      }
      
      // Загрузить ответы на упражнения
      const exerciseResponse = await fetch(
        `${backendUrl}/api/lessons/exercise-responses/${lesson.id}`, 
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      
      if (exerciseResponse.ok) {
        const exerciseData = await exerciseResponse.json();
        setExerciseResponses(exerciseData.responses || {});
        setSavedExercises(new Set(Object.keys(exerciseData.responses || {})));
      }
      
      // Загрузить прогресс челленджа (если есть)
      if (lesson.content?.challenge?.id) {
        const challengeResponse = await fetch(
          `${backendUrl}/api/lessons/challenge-progress/${lesson.content.challenge.id}`, 
          {
            headers: { 'Authorization': `Bearer ${token}` }
          }
        );
        
        if (challengeResponse.ok) {
          const challengeData = await challengeResponse.json();
          if (challengeData.progress) {
            setChallengeProgress(challengeData.progress);
            setChallengeStarted(true);
            setChallengeCompleted(challengeData.progress.status === 'completed');
          }
        }
      }
      
    } catch (err) {
      console.error('Ошибка загрузки прогресса:', err);
    }
  };

  // Сохранить ответ на упражнение (ТОЧНО КАК В FIRSTLESSON)
  const saveExerciseResponse = async (exerciseId, responseText) => {
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('lesson_id', lesson.id);
      formData.append('exercise_id', exerciseId);
      formData.append('response_text', responseText);

      const response = await fetch(`${backendUrl}/api/lessons/save-exercise-response`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        setSavedExercises(prev => new Set([...prev, exerciseId]));
        await loadUserProgress();
        return true;
      }
      return false;
    } catch (err) {
      console.error('Ошибка сохранения ответа:', err);
      return false;
    }
  };

  // Отправить квиз (АДАПТИРОВАННАЯ ИЗ FIRSTLESSON)
  const submitQuiz = async () => {
    const totalQuestions = lesson.content?.quiz?.questions?.length || 0;
    if (Object.keys(quizAnswers).length < totalQuestions) {
      setError('Пожалуйста, ответьте на все вопросы');
      return;
    }

    try {
      setQuizSubmitting(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('quiz_id', lesson.content.quiz.id);
      formData.append('answers', JSON.stringify(quizAnswers));

      const response = await fetch(`${backendUrl}/api/lessons/submit-quiz`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error('Не удалось отправить квиз');
      }

      const data = await response.json();
      setQuizResults(data);
      
      // Квиз засчитывается только при 100% правильных ответов
      if (data.passed && data.percentage === 100) {
        setCompletedSections(prev => new Set([...prev, 'quiz']));
        await loadUserProgress();
      } else {
        setError('Для прохождения теста необходимо ответить правильно на ВСЕ вопросы (100%)');
      }
      
    } catch (err) {
      console.error('Ошибка отправки квиза:', err);
      setError('Не удалось отправить квиз. Попробуйте еще раз.');
    } finally {
      setQuizSubmitting(false);
    }
  };

  // Начать челлендж (АДАПТИРОВАННАЯ ИЗ FIRSTLESSON)
  const startChallenge = async (challengeId) => {
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/api/lessons/start-challenge/${challengeId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Не удалось начать челлендж');
      }

      const data = await response.json();
      setChallengeStarted(true);
      setChallengeProgress({
        challenge_id: challengeId,
        start_date: data.start_date,
        current_day: 1,
        completed_days: [],
        status: 'active'
      });
      
      await addHabitTracker();
      
    } catch (err) {
      console.error('Ошибка начала челленджа:', err);
      setError('Не удалось начать челлендж. Попробуйте еще раз.');
    }
  };

  // Завершить день челленджа (АДАПТИРОВАННАЯ ИЗ FIRSTLESSON)
  const completeChallengeDay = async (day, notes = '') => {
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('challenge_id', lesson.content.challenge.id);
      formData.append('day', day.toString());
      formData.append('notes', notes);

      const response = await fetch(`${backendUrl}/api/lessons/complete-challenge-day`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error('Не удалось отметить день как выполненный');
      }

      const updatedCompleted = [...(challengeProgress?.completed_days || []), day];
      setChallengeProgress(prev => ({
        ...prev,
        completed_days: updatedCompleted,
        current_day: Math.min(day + 1, 7)
      }));
      
    } catch (err) {
      console.error('Ошибка завершения дня челленджа:', err);
      setError('Не удалось отметить день. Попробуйте еще раз.');
    }
  };

  // Добавить трекер привычек (АДАПТИРОВАННАЯ ИЗ FIRSTLESSON)
  const addHabitTracker = async () => {
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('lesson_id', lesson.id);

      const response = await fetch(`${backendUrl}/api/lessons/add-habit-tracker`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        setHabitTracker({
          active_habits: [
            "Утренняя аффирмация или медитация",
            "Осознание лидерских качеств", 
            "Проявление инициативы",
            "Контроль осанки и речи",
            "Вечернее подведение итогов"
          ]
        });
      }
    } catch (err) {
      console.error('Ошибка добавления трекера:', err);
    }
  };

  // Обновить привычку (АДАПТИРОВАННАЯ ИЗ FIRSTLESSON)
  const updateHabit = async (habitName, completed, notes = '') => {
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('lesson_id', lesson.id);
      formData.append('habit_name', habitName);
      formData.append('completed', completed.toString());
      formData.append('notes', notes);

      const response = await fetch(`${backendUrl}/api/lessons/update-habit`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        setTodayHabits(prev => ({
          ...prev,
          [habitName]: completed
        }));
        
        calculateHabitProgress();
        await loadUserProgress();
      }
    } catch (err) {
      console.error('Ошибка обновления привычки:', err);
    }
  };

  // Рассчитать прогресс привычек (ТОЧНО КАК В FIRSTLESSON)
  const calculateHabitProgress = () => {
    if (!habitTracker?.active_habits) return;
    
    const totalHabits = habitTracker.active_habits.length;
    const completedHabits = Object.values(todayHabits).filter(Boolean).length;
    const progressPercent = Math.round((completedHabits / totalHabits) * 100);
    
    setHabitProgress(progressPercent);
    
    if (progressPercent === 100) {
      setHabitStreakDays(prev => prev + 1);
    }
  };

  // Завершить челлендж с оценкой (АДАПТИРОВАННАЯ ИЗ FIRSTLESSON)
  const completeChallenge = async (rating, notes = '') => {
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('challenge_id', lesson.content.challenge.id);
      formData.append('rating', rating.toString());
      formData.append('notes', notes);

      const response = await fetch(`${backendUrl}/api/lessons/complete-challenge`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        setChallengeCompleted(true);
        setChallengeRating(rating);
        await loadUserProgress();
        return true;
      }
      return false;
    } catch (err) {
      console.error('Ошибка завершения челленджа:', err);
      return false;
    }
  };

  // Сбросить квиз для повторной попытки (ТОЧНО КАК В FIRSTLESSON)
  const resetQuiz = () => {
    setQuizAnswers({});
    setQuizResults(null);
    setError('');
  };

  // Отметить теорию как прочитанную
  const completeTheory = () => {
    setCompletedSections(prev => new Set([...prev, 'theory']));
  };

  // Сбросить трекер привычек для нового дня (ТОЧНО КАК В FIRSTLESSON)
  const resetHabitsForNewDay = () => {
    setTodayHabits({});
    setHabitProgress(0);
  };

  if (!lesson || !lesson.content) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <BookOpen className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
          <p>Урок не найден или не содержит контента</p>
        </CardContent>
      </Card>
    );
  }

  // Индикаторы прогресса секций (ТОЧНО КАК В FIRSTLESSON)
  const sectionProgress = [
    { id: 'theory', title: 'Теория', icon: <BookOpen className="w-4 h-4" />, completed: completedSections.has('theory') },
    { id: 'exercises', title: 'Упражнения', icon: <Brain className="w-4 h-4" />, completed: completedSections.has('exercises') },
    { id: 'quiz', title: 'Тест', icon: <Target className="w-4 h-4" />, completed: completedSections.has('quiz') },
    { id: 'challenge', title: 'Челлендж', icon: <Zap className="w-4 h-4" />, completed: challengeStarted },
    { id: 'habits', title: 'Привычки', icon: <Star className="w-4 h-4" />, completed: habitTracker !== null }
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* УЛУЧШЕННЫЙ ЗАГОЛОВОК УРОКА - ТОЧНО КАК В FIRSTLESSON */}
      <div className="relative overflow-hidden">
        <Card className="border border-gray-200 bg-white shadow-sm">          
          <CardHeader className="p-6 border-b border-gray-100">
            <div className="flex items-start justify-between flex-wrap gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-4 mb-4">
                  <div className="p-3 bg-purple-50 rounded-xl border border-purple-100">
                    <BookOpen className="w-8 h-8 text-purple-600" />
                  </div>
                  <div>
                    <CardTitle className="text-2xl sm:text-3xl font-semibold text-gray-900 mb-2">
                      {lesson.title}
                    </CardTitle>
                    <CardDescription className="text-gray-600 text-base">
                      {lesson.description}
                    </CardDescription>
                  </div>
                </div>
              </div>
              
              <div className="text-right">
                <div className="flex flex-col items-end gap-2 mb-4">
                  {lesson.points_required === 0 ? (
                    <Badge className="bg-green-50 text-green-700 border border-green-200 font-medium px-4 py-2 rounded-full">
                      🎁 Бесплатный урок
                    </Badge>
                  ) : (
                    <Badge className="bg-orange-50 text-orange-700 border border-orange-200 font-medium px-4 py-2 rounded-full">
                      💎 {lesson.points_required} баллов
                    </Badge>
                  )}
                  <Badge className="bg-gray-50 text-gray-700 border border-gray-200 px-3 py-1">
                    {lesson.module}
                  </Badge>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-600">
                  <div className="flex items-center">
                    <Clock className="w-4 h-4 mr-1" />
                    ~45 мин
                  </div>
                  <div className="flex items-center">
                    <Target className="w-4 h-4 mr-1" />
                    {completedSections.size}/5 разделов
                  </div>
                </div>
              </div>
            </div>
            
            {/* Улучшенная шкала прогресса - ТОЧНО КАК В FIRSTLESSON */}
            <div className="mt-6 space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-700 font-medium">Общий прогресс урока</span>
                <div className="flex items-center gap-2">
                  <span className="text-gray-900 font-semibold text-lg">{overallProgress}%</span>
                  {overallProgress === 100 && (
                    <div className="flex items-center bg-green-100 text-green-700 border border-green-200 px-3 py-1 rounded-full text-xs font-semibold">
                      <Trophy className="w-3 h-3 mr-1" />
                      Завершен
                    </div>
                  )}
                </div>
              </div>
              <div className="relative">
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className="bg-blue-500 h-3 rounded-full transition-all duration-1000 ease-out flex items-center justify-end pr-2"
                    style={{width: `${overallProgress}%`}}
                  >
                    {overallProgress > 10 && (
                      <Sparkles className="w-3 h-3 text-white" />
                    )}
                  </div>
                </div>
                <div className="absolute -bottom-6 left-0 right-0 flex justify-between text-xs text-gray-500">
                  <span>Начало</span>
                  <span className="hidden sm:inline">Середина</span>
                  <span>Завершение</span>
                </div>
              </div>
            </div>
            
            {/* Мини-индикаторы разделов - ТОЧНО КАК В FIRSTLESSON */}
            <div className="mt-8 flex flex-wrap gap-2">
              {sectionProgress.map((section) => (
                <div
                  key={section.id}
                  className={`flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium transition-all ${
                    section.completed 
                      ? 'bg-green-500/20 text-green-700 border border-green-500/30' 
                      : 'bg-gray-100 text-gray-600 border border-gray-200'
                  }`}
                >
                  {section.completed ? (
                    <CheckCircle className="w-3 h-3" />
                  ) : (
                    section.icon
                  )}
                  <span className="hidden sm:inline">{section.title}</span>
                </div>
              ))}
            </div>
          </CardHeader>
        </Card>
      </div>

      {/* УЛУЧШЕННАЯ НАВИГАЦИЯ РАЗДЕЛОВ - ТОЧНО КАК В FIRSTLESSON */}
      <Tabs value={activeSection} onValueChange={setActiveSection} className="space-y-8">
        <div className="sticky top-4 z-40 bg-white/95 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200/50 p-2">
          <TabsList className="grid w-full grid-cols-6 bg-transparent gap-1">
            {[
              { id: 'theory', label: 'Теория', icon: BookOpen, color: 'blue' },
              { id: 'exercises', label: 'Упражнения', icon: Brain, color: 'green' },
              { id: 'quiz', label: 'Тест', icon: Target, color: 'orange' },
              { id: 'challenge', label: 'Челлендж', icon: Zap, color: 'purple' },
              { id: 'habits', label: 'Привычки', icon: Star, color: 'yellow' },
              { id: 'media', label: 'Материалы', icon: FileText, color: 'pink' }
            ].map((tab) => (
              <TabsTrigger 
                key={tab.id}
                value={tab.id} 
                className={`flex flex-col items-center gap-1 p-3 rounded-xl transition-all duration-200 data-[state=active]:shadow-md ${
                  activeSection === tab.id
                    ? `bg-blue-50 text-blue-700 border border-blue-200`
                    : 'text-gray-600 hover:bg-gray-50 border border-transparent'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                <span className="text-xs font-medium hidden sm:block">{tab.label}</span>
                {completedSections.has(tab.id) && (
                  <CheckCircle className="w-3 h-3 absolute -top-1 -right-1 text-green-500 bg-white rounded-full border border-green-200" />
                )}
              </TabsTrigger>
            ))}
          </TabsList>
        </div>

        {/* ТЕОРИЯ - ТОЧНО КАК В FIRSTLESSON */}
        <TabsContent value="theory" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <BookOpen className="w-5 h-5 mr-2" />
                Что изучаем в этом уроке?
              </CardTitle>
            </CardHeader>
            <CardContent className="prose max-w-none">
              <p className="text-gray-700 leading-relaxed text-lg whitespace-pre-line">
                {lesson.content.theory?.what_is_topic}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Star className="w-5 h-5 mr-2" />
                Основное содержание
              </CardTitle>
            </CardHeader>
            <CardContent className="prose max-w-none">
              <div className="text-gray-700 leading-relaxed text-base whitespace-pre-line">
                {lesson.content.theory?.main_story}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Brain className="w-5 h-5 mr-2" />
                Ключевые концепции
              </CardTitle>
            </CardHeader>
            <CardContent className="prose max-w-none">
              <div className="text-gray-700 leading-relaxed text-base whitespace-pre-line">
                {lesson.content.theory?.key_concepts}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Lightbulb className="w-5 h-5 mr-2" />
                Практическое применение
              </CardTitle>
            </CardHeader>
            <CardContent className="prose max-w-none">
              <div className="text-gray-700 leading-relaxed text-base whitespace-pre-line">
                {lesson.content.theory?.practical_applications}
              </div>
            </CardContent>
          </Card>

          <div className="mt-6 text-center">
            <Button 
              onClick={completeTheory}
              className="numerology-gradient"
              disabled={completedSections.has('theory')}
            >
              {completedSections.has('theory') ? (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Теория изучена
                </>
              ) : (
                <>
                  <ArrowRight className="w-4 h-4 mr-2" />
                  Завершить изучение теории
                </>
              )}
            </Button>
          </div>
        </TabsContent>

        {/* УПРАЖНЕНИЯ - ТОЧНО КАК В FIRSTLESSON */}
        <TabsContent value="exercises" className="space-y-6">
          {lesson.content.exercises?.map((exercise, index) => (
            <Card key={exercise.id}>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Brain className="w-5 h-5 mr-2" />
                    Упражнение {index + 1}: {exercise.title}
                  </div>
                  <div className="flex items-center space-x-2">
                    {savedExercises.has(exercise.id) && (
                      <Badge className="bg-green-100 text-green-800">
                        Сохранено
                      </Badge>
                    )}
                    <Checkbox
                      checked={completedExercises.has(exercise.id)}
                      onCheckedChange={(checked) => {
                        if (checked) {
                          setCompletedExercises(prev => new Set([...prev, exercise.id]));
                        } else {
                          setCompletedExercises(prev => {
                            const newSet = new Set(prev);
                            newSet.delete(exercise.id);
                            return newSet;
                          });
                        }
                      }}
                    />
                  </div>
                </CardTitle>
                <CardDescription>
                  Тип: {exercise.type === 'reflection' ? 'Рефлексия' : 
                        exercise.type === 'calculation' ? 'Расчеты' : 
                        exercise.type === 'meditation' ? 'Медитация' : 'Практическое'}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="prose max-w-none text-sm">
                    <p className="whitespace-pre-line">{exercise.content}</p>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-semibold mb-2">Инструкции:</h4>
                  <ul className="list-disc pl-5 space-y-1 text-sm">
                    {exercise.instructions?.map((instruction, idx) => (
                      <li key={idx}>{instruction}</li>
                    ))}
                  </ul>
                </div>
                
                <div className="p-3 bg-blue-50 rounded-lg">
                  <div className="font-medium text-blue-800 text-sm mb-1">Ожидаемый результат:</div>
                  <div className="text-blue-700 text-sm">{exercise.expected_outcome}</div>
                </div>
                
                <div className="space-y-3">
                  <h4 className="font-semibold">Ваши заметки:</h4>
                  <textarea 
                    placeholder="Запишите свои мысли, инсайты и результаты упражнения..."
                    className="w-full p-3 border rounded-lg min-h-24 text-sm"
                    value={exerciseResponses[exercise.id]?.response_text || ''}
                    onChange={(e) => setExerciseResponses(prev => ({
                      ...prev,
                      [exercise.id]: {
                        ...prev[exercise.id],
                        response_text: e.target.value
                      }
                    }))}
                  />
                  <div className="flex gap-2 flex-wrap">
                    <Button 
                      onClick={async () => {
                        const responseText = exerciseResponses[exercise.id]?.response_text;
                        if (responseText?.trim()) {
                          const saved = await saveExerciseResponse(exercise.id, responseText);
                          if (saved) {
                            setError('');
                          } else {
                            setError('Не удалось сохранить ответ');
                          }
                        } else {
                          setError('Пожалуйста, напишите ответ перед сохранением');
                        }
                      }}
                      disabled={!exerciseResponses[exercise.id]?.response_text?.trim()}
                      variant="outline"
                      className="flex-1 sm:flex-none"
                    >
                      <FileText className="w-4 h-4 mr-2" />
                      Сохранить ответ
                    </Button>
                    
                    <Button 
                      onClick={() => {
                        if (savedExercises.has(exercise.id)) {
                          setCompletedExercises(prev => new Set([...prev, exercise.id]));
                        } else {
                          setError('Сначала сохраните ответ');
                        }
                      }}
                      disabled={completedExercises.has(exercise.id) || !savedExercises.has(exercise.id)}
                      className="flex-1 sm:flex-none"
                    >
                      {completedExercises.has(exercise.id) ? (
                        <>
                          <CheckCircle className="w-4 h-4 mr-2" />
                          Упражнение выполнено
                        </>
                      ) : (
                        <>
                          <Target className="w-4 h-4 mr-2" />
                          Отметить как выполненное
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          
          {completedExercises.size === lesson.content.exercises?.length && lesson.content.exercises?.length > 0 && (
            <Card className="border-green-200 bg-green-50">
              <CardContent className="text-center py-6">
                <Trophy className="w-12 h-12 text-green-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-green-800 mb-2">
                  Отлично! Все упражнения выполнены
                </h3>
                <p className="text-green-700 mb-4">
                  Теперь вы можете перейти к тестированию знаний
                </p>
                <Button onClick={() => setActiveSection('quiz')} className="numerology-gradient">
                  Пройти тест
                </Button>
              </CardContent>
            </Card>
          )}

          {(!lesson.content.exercises || lesson.content.exercises.length === 0) && (
            <Card>
              <CardContent className="text-center py-8">
                <Brain className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500">В этом уроке пока нет упражнений</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* КВИЗ - ТОЧНО КАК В FIRSTLESSON */}
        <TabsContent value="quiz" className="space-y-6">
          {!quizResults ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Target className="w-5 h-5 mr-2" />
                  {lesson.content.quiz?.title || 'Тест по уроку'}
                </CardTitle>
                <CardDescription>
                  Ответьте на все вопросы для проверки знаний. Для прохождения нужно набрать 100%.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {lesson.content.quiz?.questions?.map((question, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <h4 className="font-semibold mb-3">
                      Вопрос {index + 1}: {question.question}
                    </h4>
                    <div className="space-y-2">
                      {question.options?.map((option, optIndex) => (
                        <label key={optIndex} className="flex items-center space-x-2 cursor-pointer p-2 hover:bg-gray-50 rounded">
                          <input
                            type="radio"
                            name={`q${index + 1}`}
                            value={option.charAt(0)}
                            checked={quizAnswers[`q${index + 1}`] === option.charAt(0)}
                            onChange={(e) => setQuizAnswers(prev => ({
                              ...prev,
                              [`q${index + 1}`]: e.target.value
                            }))}
                            className="text-blue-600"
                          />
                          <span className="text-sm">{option}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
                
                <div className="text-center">
                  <Button 
                    onClick={submitQuiz}
                    disabled={quizSubmitting || Object.keys(quizAnswers).length < (lesson.content.quiz?.questions?.length || 0)}
                    className="numerology-gradient px-8 py-3"
                  >
                    {quizSubmitting ? (
                      <>
                        <Loader className="w-4 h-4 animate-spin mr-2" />
                        Проверяем ответы...
                      </>
                    ) : (
                      <>
                        <Target className="w-4 h-4 mr-2" />
                        Отправить тест
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className={quizResults.passed ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}>
              <CardHeader>
                <CardTitle className={`flex items-center ${quizResults.passed ? 'text-green-800' : 'text-red-800'}`}>
                  {quizResults.passed ? <Trophy className="w-5 h-5 mr-2" /> : <Target className="w-5 h-5 mr-2" />}
                  Результаты теста
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <div className={`text-4xl font-bold mb-2 ${quizResults.passed ? 'text-green-600' : 'text-red-600'}`}>
                    {quizResults.percentage}%
                  </div>
                  <p className={`text-sm ${quizResults.passed ? 'text-green-700' : 'text-red-700'}`}>
                    Правильных ответов: {quizResults.correct} из {quizResults.total}
                  </p>
                  
                  {quizResults.passed ? (
                    <div className="mt-4 p-4 bg-green-100 border border-green-200 rounded-lg">
                      <Trophy className="w-8 h-8 text-green-600 mx-auto mb-2" />
                      <h3 className="font-bold text-green-800">Поздравляем!</h3>
                      <p className="text-green-700 text-sm">Вы успешно прошли тест со 100% результатом!</p>
                    </div>
                  ) : (
                    <div className="mt-4 p-4 bg-red-100 border border-red-200 rounded-lg">
                      <h3 className="font-bold text-red-800">Нужно больше практики</h3>
                      <p className="text-red-700 text-sm">Для прохождения необходимо набрать 100%. Изучите материал еще раз.</p>
                    </div>
                  )}
                </div>
                
                {!quizResults.passed && (
                  <div className="text-center">
                    <Button 
                      onClick={resetQuiz}
                      variant="outline"
                      className="border-red-300 text-red-700 hover:bg-red-50"
                    >
                      <ArrowLeft className="w-4 h-4 mr-2" />
                      Попробовать еще раз
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
          
          {(!lesson.content.quiz?.questions || lesson.content.quiz.questions.length === 0) && (
            <Card>
              <CardContent className="text-center py-8">
                <Target className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500">В этом уроке пока нет теста</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ЧЕЛЛЕНДЖ - ТОЧНО КАК В FIRSTLESSON */}
        <TabsContent value="challenge" className="space-y-6">
          {lesson.content.challenge && lesson.content.challenge.daily_tasks?.length > 0 ? (
            <div className="space-y-6">
              <Card className="bg-gradient-to-r from-amber-50 to-orange-50 border-amber-200">
                <CardHeader>
                  <CardTitle className="flex items-center text-amber-900">
                    <Zap className="w-5 h-5 mr-2" />
                    {lesson.content.challenge.title}
                  </CardTitle>
                  <CardDescription className="text-amber-800">
                    {lesson.content.challenge.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {!challengeStarted ? (
                    <div className="text-center py-6">
                      <Calendar className="w-16 h-16 mx-auto mb-4 text-amber-600" />
                      <h3 className="text-lg font-semibold text-amber-900 mb-2">
                        Готовы к {lesson.content.challenge.daily_tasks.length}-дневному челленджу?
                      </h3>
                      <p className="text-amber-800 mb-6 max-w-md mx-auto">
                        Активируйте энергию через ежедневные практики и отслеживание привычек
                      </p>
                      <Button 
                        onClick={() => startChallenge(lesson.content.challenge.id)}
                        className="numerology-gradient px-8 py-3"
                      >
                        <Zap className="w-5 h-5 mr-2" />
                        Начать челлендж
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {/* Прогресс челленджа */}
                      <div className="bg-white rounded-lg p-4 border border-amber-200">
                        <div className="flex justify-between items-center mb-3">
                          <h4 className="font-semibold text-amber-900">Прогресс челленджа</h4>
                          <Badge className="bg-amber-100 text-amber-800">
                            День {challengeProgress?.current_day || 1} из {lesson.content.challenge.daily_tasks.length}
                          </Badge>
                        </div>
                        <div className="w-full bg-amber-100 rounded-full h-3">
                          <div 
                            className="bg-amber-500 h-3 rounded-full transition-all duration-500"
                            style={{width: `${((challengeProgress?.completed_days?.length || 0) / lesson.content.challenge.daily_tasks.length) * 100}%`}}
                          />
                        </div>
                        <div className="mt-2 text-sm text-amber-700">
                          Выполнено дней: {challengeProgress?.completed_days?.length || 0}
                        </div>
                      </div>

                      {/* Дни челленджа */}
                      <div className="grid gap-4">
                        {lesson.content.challenge.daily_tasks.map((day) => {
                          const isCompleted = challengeProgress?.completed_days?.includes(day.day);
                          const isCurrent = challengeProgress?.current_day === day.day;
                          const isAvailable = day.day <= (challengeProgress?.current_day || 1);

                          return (
                            <Card 
                              key={day.day}
                              className={`transition-all ${
                                isCompleted ? 'bg-green-50 border-green-300' : 
                                isCurrent ? 'bg-amber-50 border-amber-300 shadow-md' : 
                                isAvailable ? 'border-gray-200' : 'bg-gray-50 border-gray-200 opacity-50'
                              }`}
                            >
                              <CardContent className="p-4">
                                <div className="flex items-start justify-between mb-3">
                                  <div className="flex-1">
                                    <h4 className="font-semibold mb-1 flex items-center">
                                      {isCompleted && <CheckCircle className="w-4 h-4 mr-2 text-green-600" />}
                                      {isCurrent && <Clock className="w-4 h-4 mr-2 text-amber-600" />}
                                      День {day.day}: {day.title}
                                    </h4>
                                    
                                    <div className="space-y-2">
                                      {day.tasks?.map((task, taskIndex) => (
                                        <div key={taskIndex} className="flex items-start">
                                          <div className="w-1.5 h-1.5 bg-amber-400 rounded-full mr-3 mt-2 flex-shrink-0"></div>
                                          <span className="text-sm text-gray-700">{task}</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                  
                                  {isAvailable && !isCompleted && (
                                    <Button
                                      size="sm"
                                      onClick={() => completeChallengeDay(day.day)}
                                      className="ml-4"
                                    >
                                      <CheckCircle className="w-4 h-4 mr-1" />
                                      Выполнено
                                    </Button>
                                  )}
                                </div>
                              </CardContent>
                            </Card>
                          );
                        })}
                      </div>

                      {/* Завершение челленджа */}
                      {challengeProgress?.completed_days?.length === lesson.content.challenge.daily_tasks.length && !challengeCompleted && (
                        <Card className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-300">
                          <CardContent className="text-center py-8">
                            <Trophy className="w-16 h-16 text-green-600 mx-auto mb-4" />
                            <h3 className="text-xl font-bold text-green-800 mb-4">
                              Челлендж завершен!
                            </h3>
                            <p className="text-green-700 mb-6">
                              Оцените свой опыт прохождения челленджа:
                            </p>
                            
                            <div className="flex justify-center gap-2 mb-6">
                              {[1, 2, 3, 4, 5].map((star) => (
                                <button
                                  key={star}
                                  onClick={() => setChallengeRating(star)}
                                  className={`w-10 h-10 rounded-full transition-all ${
                                    star <= challengeRating 
                                      ? 'text-yellow-500 bg-yellow-100 border-2 border-yellow-300' 
                                      : 'text-gray-300 hover:text-yellow-400 border-2 border-gray-200'
                                  }`}
                                >
                                  <Star className="w-5 h-5 mx-auto" fill={star <= challengeRating ? 'currentColor' : 'none'} />
                                </button>
                              ))}
                            </div>
                            
                            <Button 
                              onClick={() => completeChallenge(challengeRating)}
                              disabled={challengeRating === 0}
                              className="numerology-gradient px-8 py-3"
                            >
                              <Trophy className="w-4 h-4 mr-2" />
                              Завершить челлендж
                            </Button>
                          </CardContent>
                        </Card>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <Zap className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500">В этом уроке нет челленджа</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ТРЕКЕР ПРИВЫЧЕК - ТОЧНО КАК В FIRSTLESSON */}
        <TabsContent value="habits" className="space-y-6">
          {habitTracker ? (
            <div className="space-y-6">
              <Card className="bg-gradient-to-r from-yellow-50 to-amber-50 border-yellow-200">
                <CardHeader>
                  <CardTitle className="flex items-center text-yellow-900">
                    <Star className="w-5 h-5 mr-2" />
                    Трекер привычек
                  </CardTitle>
                  <CardDescription className="text-yellow-800">
                    Отслеживайте выполнение ежедневных практик для укрепления энергии
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Прогресс дня */}
                    <div className="bg-white rounded-lg p-4 border border-yellow-200">
                      <div className="flex justify-between items-center mb-3">
                        <h4 className="font-semibold text-yellow-900">Прогресс дня</h4>
                        <div className="flex items-center gap-2">
                          <Badge className="bg-yellow-100 text-yellow-800">
                            {habitProgress}%
                          </Badge>
                          {habitProgress === 100 && (
                            <Badge className="bg-green-100 text-green-800">
                              🔥 {habitStreakDays} дней подряд
                            </Badge>
                          )}
                        </div>
                      </div>
                      <div className="w-full bg-yellow-100 rounded-full h-3">
                        <div 
                          className="bg-yellow-500 h-3 rounded-full transition-all duration-500"
                          style={{width: `${habitProgress}%`}}
                        />
                      </div>
                    </div>

                    {/* Список привычек */}
                    <div className="space-y-3">
                      {habitTracker.active_habits.map((habit, index) => (
                        <Card key={index} className="border border-yellow-200">
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center flex-1">
                                <Checkbox
                                  checked={todayHabits[habit] || false}
                                  onCheckedChange={(checked) => updateHabit(habit, checked)}
                                  className="mr-3"
                                />
                                <div>
                                  <h5 className="font-medium text-gray-900">{habit}</h5>
                                  <p className="text-sm text-gray-600">
                                    {habit.includes('аффирмация') ? 'Настрой на день и укрепление уверенности' :
                                     habit.includes('лидерских') ? 'Осознанное проявление лидерства' :
                                     habit.includes('инициативы') ? 'Активные действия и принятие решений' :
                                     habit.includes('осанки') ? 'Уверенная позиция тела и четкая речь' :
                                     'Анализ достижений и планирование'}
                                  </p>
                                </div>
                              </div>
                              
                              {todayHabits[habit] && (
                                <CheckCircle className="w-5 h-5 text-green-600" />
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>

                    {/* Кнопки управления */}
                    <div className="flex gap-3">
                      <Button 
                        onClick={resetHabitsForNewDay}
                        variant="outline"
                        className="flex-1"
                      >
                        <Calendar className="w-4 h-4 mr-2" />
                        Новый день
                      </Button>
                      
                      {habitProgress === 100 && (
                        <Button 
                          onClick={() => {
                            setCompletedSections(prev => new Set([...prev, 'habits']));
                            alert(`Отлично! Вы выполнили все привычки дня. Серия: ${habitStreakDays + 1} дней!`);
                          }}
                          className="flex-1 numerology-gradient"
                        >
                          <Trophy className="w-4 h-4 mr-2" />
                          Завершить день
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <Star className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Трекер привычек</h3>
                <p className="text-gray-500 mb-4">
                  Начните челлендж чтобы активировать трекер привычек
                </p>
                <Button onClick={() => setActiveSection('challenge')} variant="outline">
                  <Zap className="w-4 h-4 mr-2" />
                  Перейти к челленджу
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* МЕДИА МАТЕРИАЛЫ - УНИФИЦИРОВАННЫЕ С CONSULTATIONS */}
        <TabsContent value="media" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <FileText className="w-5 h-5 mr-2" />
                Учебные материалы
              </CardTitle>
              <CardDescription>
                Видеоуроки и справочные материалы для изучения
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              
              {/* Видео файлы - ТОЧНО КАК В CONSULTATIONS */}
              {lessonMedia.videos?.length > 0 && (
                <div className="space-y-4">
                  <h4 className="font-semibold text-blue-800 mb-3 flex items-center">
                    <Video className="w-4 h-4 mr-2" />
                    Видеоуроки ({lessonMedia.videos.length})
                  </h4>
                  <div className="grid gap-4">
                    {lessonMedia.videos.map((video) => (
                      <Card key={video.id} className="border border-blue-200 bg-blue-50">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <h5 className="font-medium text-blue-900 mb-1">
                                📹 {video.filename || video.original_filename}
                              </h5>
                              <p className="text-sm text-blue-700">
                                {video.file_size && `Размер: ${(video.file_size / 1024 / 1024).toFixed(1)} MB • `}
                                Загружено: {new Date(video.uploaded_at).toLocaleDateString()}
                              </p>
                            </div>
                            <Button
                              size="sm"
                              onClick={() => setSelectedVideo({
                                url: `${backendUrl}${video.video_url}`,
                                title: `${lesson.title} - Видеоурок`,
                                description: lesson.description,
                                lesson: lesson
                              })}
                              className="bg-blue-600 hover:bg-blue-700 text-white"
                            >
                              <Play className="w-4 h-4 mr-1" />
                              Смотреть
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {/* PDF файлы - ТОЧНО КАК В CONSULTATIONS */}
              {lessonMedia.pdfs?.length > 0 && (
                <div className="space-y-4">
                  <h4 className="font-semibold text-green-800 mb-3 flex items-center">
                    <FileText className="w-4 h-4 mr-2" />
                    PDF материалы ({lessonMedia.pdfs.length})
                  </h4>
                  <div className="grid gap-4">
                    {lessonMedia.pdfs.map((pdf) => (
                      <Card key={pdf.id} className="border border-green-200 bg-green-50">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <h5 className="font-medium text-green-900 mb-1">
                                📄 {pdf.filename || pdf.original_filename}
                              </h5>
                              <p className="text-sm text-green-700">
                                {pdf.file_size && `Размер: ${(pdf.file_size / 1024 / 1024).toFixed(1)} MB • `}
                                Загружено: {new Date(pdf.uploaded_at).toLocaleDateString()}
                              </p>
                            </div>
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                onClick={() => setSelectedPDF({
                                  url: `${backendUrl}${pdf.pdf_url}`,
                                  title: `${lesson.title} - PDF материалы`
                                })}
                                className="bg-green-600 hover:bg-green-700 text-white"
                              >
                                <Eye className="w-4 h-4 mr-1" />
                                Открыть
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  const link = document.createElement('a');
                                  link.href = `${backendUrl}${pdf.pdf_url}`;
                                  link.download = pdf.filename || pdf.original_filename;
                                  link.click();
                                }}
                                className="border-green-600 text-green-600 hover:bg-green-50"
                              >
                                <Download className="w-4 h-4 mr-1" />
                                Скачать
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {/* Если есть встроенные медиа поля в уроке (как в консультациях) */}
              {lesson.video_file_id && (
                <div className="space-y-4">
                  <h4 className="font-semibold text-purple-800 mb-3 flex items-center">
                    <Video className="w-4 h-4 mr-2" />
                    Основное видео урока
                  </h4>
                  <Card className="border border-purple-200 bg-purple-50">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h5 className="font-medium text-purple-900 mb-1">
                            📹 {lesson.video_filename || 'Видео урока'}
                          </h5>
                          <p className="text-sm text-purple-700">Основной видеоматериал урока</p>
                        </div>
                        <Button
                          onClick={() => setSelectedVideo({
                            url: `${backendUrl}/api/consultations/video/${lesson.video_file_id}`,
                            title: `${lesson.title} - Основное видео`,
                            description: lesson.description,
                            lesson: lesson
                          })}
                          className="bg-purple-600 hover:bg-purple-700 text-white"
                        >
                          <Play className="w-4 h-4 mr-1" />
                          Смотреть
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {lesson.pdf_file_id && (
                <div className="space-y-4">
                  <h4 className="font-semibold text-green-800 mb-3 flex items-center">
                    <FileText className="w-4 h-4 mr-2" />
                    Основные PDF материалы
                  </h4>
                  <Card className="border border-green-200 bg-green-50">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h5 className="font-medium text-green-900 mb-1">
                            📄 {lesson.pdf_filename || 'PDF материалы урока'}
                          </h5>
                          <p className="text-sm text-green-700">Основные справочные материалы</p>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => setSelectedPDF({
                              url: `${backendUrl}/api/consultations/pdf/${lesson.pdf_file_id}`,
                              title: `${lesson.title} - PDF материалы`
                            })}
                            className="bg-green-600 hover:bg-green-700 text-white"
                          >
                            <Eye className="w-4 h-4 mr-1" />
                            Открыть
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              const link = document.createElement('a');
                              link.href = `${backendUrl}/api/consultations/pdf/${lesson.pdf_file_id}`;
                              link.download = lesson.pdf_filename || 'lesson-materials.pdf';
                              link.click();
                            }}
                            className="border-green-600 text-green-600 hover:bg-green-50"
                          >
                            <Download className="w-4 h-4 mr-1" />
                            Скачать
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Если нет медиа файлов */}
              {(!lessonMedia.videos || lessonMedia.videos.length === 0) && 
               (!lessonMedia.pdfs || lessonMedia.pdfs.length === 0) &&
               !lesson.video_file_id && !lesson.pdf_file_id && (
                <Card>
                  <CardContent className="text-center py-8">
                    <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">Материалы готовятся</h3>
                    <p className="text-gray-500">Администратор добавит видео и PDF материалы для этого урока</p>
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Ошибки */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <p className="text-red-700 text-sm flex items-center">
              <AlertCircle className="w-4 h-4 mr-2" />
              {error}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Модальные окна для медиа - ТОЧНО КАК В CONSULTATIONS */}
      {selectedVideo && (
        <EnhancedVideoViewer
          videoUrl={selectedVideo.url}
          title={selectedVideo.title}
          description={selectedVideo.description}
          consultation={selectedVideo.lesson}
          onClose={() => setSelectedVideo(null)}
          backendUrl={backendUrl}
        />
      )}

      {selectedPDF && (
        <ConsultationPDFViewer
          pdfUrl={selectedPDF.url}
          title={selectedPDF.title}
          onClose={() => setSelectedPDF(null)}
        />
      )}
    </div>
  );
};

export default CustomLessonViewer;