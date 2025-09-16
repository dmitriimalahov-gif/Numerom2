import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Checkbox } from './ui/checkbox';
import { 
  BookOpen, PlayCircle, CheckCircle, Clock, Target, Zap, 
  Star, Calendar, Award, ArrowRight, ArrowLeft, 
  Sparkles, Sun, Moon, Loader, Trophy, Heart,
  Brain, Lightbulb, FileText, Timer, Rocket, Eye, Download, Video
} from 'lucide-react';
import { useAuth } from './AuthContext';
import EnhancedVideoViewer from './EnhancedVideoViewer';
import ConsultationPDFViewer from './ConsultationPDFViewer';

const FirstLesson = () => {
  const { user } = useAuth();
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  
  // Состояния для управления уроком
  const [lessonData, setLessonData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeSection, setActiveSection] = useState('theory');
  const [completedSections, setCompletedSections] = useState(new Set());
  const [overallProgress, setOverallProgress] = useState(0);
  
  // Состояния для квиза
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizResults, setQuizResults] = useState(null);
  const [quizSubmitting, setQuizSubmitting] = useState(false);
  
  // Состояния для челленджа
  const [challengeProgress, setChallengeProgress] = useState(null);
  const [challengeStarted, setChallengeStarted] = useState(false);
  const [selectedChallengeDay, setSelectedChallengeDay] = useState(1);
  const [challengeCompleted, setChallengeCompleted] = useState(false);
  const [challengeRating, setChallengeRating] = useState(0);
  
  // Состояния для трекера привычек  
  const [habitTracker, setHabitTracker] = useState(null);
  const [todayHabits, setTodayHabits] = useState({});
  const [habitProgress, setHabitProgress] = useState(0);
  const [habitStreakDays, setHabitStreakDays] = useState(0);
  
  // Состояния для упражнений
  const [exerciseResponses, setExerciseResponses] = useState({});
  const [completedExercises, setCompletedExercises] = useState(new Set());
  const [savedExercises, setSavedExercises] = useState(new Set());
  
  // Состояния для загруженных файлов урока
  const [uploadedLessonFiles, setUploadedLessonFiles] = useState({
    video: null,
    pdf: null
  });
  
  // Состояния для модальных окон (как в PersonalConsultations)
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [selectedPDF, setSelectedPDF] = useState(null);
  
  // Состояние для дополнительных PDF файлов
  const [additionalPdfs, setAdditionalPdfs] = useState([]);
  
  // Состояние для дополнительных видео файлов
  const [additionalVideos, setAdditionalVideos] = useState([]);

  // Состояния для улучшенной навигации материалов
  const [materialsFilter, setMaterialsFilter] = useState('all'); // 'all', 'videos', 'pdfs'
  const [materialsSearch, setMaterialsSearch] = useState('');
  const [materialsSortBy, setMaterialsSortBy] = useState('recent'); // 'recent', 'name', 'type'

  useEffect(() => {
    loadFirstLesson();
    loadUploadedLessonFiles();
    loadAdditionalPdfs();
    loadAdditionalVideos();
  }, []);

  // Функции для навигации и фильтрации материалов
  const getFilteredAndSortedMaterials = () => {
    let allMaterials = [];
    
    // Добавляем видео с типом
    additionalVideos.forEach(video => {
      allMaterials.push({
        ...video,
        type: 'video',
        searchText: video.title.toLowerCase(),
        date: video.uploaded_at || new Date().toISOString()
      });
    });
    
    // Добавляем PDF с типом
    additionalPdfs.forEach(pdf => {
      allMaterials.push({
        ...pdf,
        type: 'pdf',
        searchText: pdf.title.toLowerCase(),
        date: pdf.uploaded_at || new Date().toISOString()
      });
    });

    // Применяем фильтр по типу
    if (materialsFilter !== 'all') {
      allMaterials = allMaterials.filter(material => {
        if (materialsFilter === 'videos') return material.type === 'video';
        if (materialsFilter === 'pdfs') return material.type === 'pdf';
        return true;
      });
    }

    // Применяем поиск
    if (materialsSearch.trim()) {
      const searchTerm = materialsSearch.toLowerCase().trim();
      allMaterials = allMaterials.filter(material => 
        material.searchText.includes(searchTerm)
      );
    }

    // Применяем сортировку
    allMaterials.sort((a, b) => {
      switch (materialsSortBy) {
        case 'name':
          return a.title.localeCompare(b.title);
        case 'type':
          return a.type.localeCompare(b.type);
        case 'recent':
        default:
          return new Date(b.date) - new Date(a.date);
      }
    });

    return allMaterials;
  };

  const filteredMaterials = getFilteredAndSortedMaterials();
  const videoMaterials = filteredMaterials.filter(m => m.type === 'video');
  const pdfMaterials = filteredMaterials.filter(m => m.type === 'pdf');

  // Загрузка загруженных файлов урока
  const loadUploadedLessonFiles = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Используем новый endpoint для получения медиа-файлов урока
      const response = await fetch(`${backendUrl}/api/lessons/media/lesson_numerom_intro`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Получаем первые доступные видео и PDF файлы
        const firstVideo = data.videos && data.videos.length > 0 ? data.videos[0] : null;
        const firstPDF = data.pdfs && data.pdfs.length > 0 ? data.pdfs[0] : null;
        
        setUploadedLessonFiles({
          video: firstVideo ? {
            url: `${backendUrl}${firstVideo.video_url}`,
            filename: firstVideo.filename,
            id: firstVideo.id
          } : null,
          pdf: firstPDF ? {
            url: `${backendUrl}${firstPDF.pdf_url}`,
            filename: firstPDF.filename,
            id: firstPDF.id
          } : null
        });
      } else {
        console.log('Медиа-файлы для урока не найдены или не загружены');
        setUploadedLessonFiles({ video: null, pdf: null });
      }
    } catch (error) {
      console.error('Ошибка загрузки медиа-файлов урока:', error);
      setUploadedLessonFiles({ video: null, pdf: null });
    }
  };

  // Загрузка дополнительных PDF файлов урока
  const loadAdditionalPdfs = async () => {
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/api/lessons/lesson_numerom_intro/additional-pdfs`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAdditionalPdfs(data.additional_pdfs || []);
      } else {
        console.log('Дополнительные PDF для урока не найдены');
        setAdditionalPdfs([]);
      }
    } catch (error) {
      console.error('Ошибка загрузки дополнительных PDF урока:', error);
      setAdditionalPdfs([]);
    }
  };

  // Загрузка дополнительных видео файлов урока
  const loadAdditionalVideos = async () => {
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/api/lessons/lesson_numerom_intro/additional-videos`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAdditionalVideos(data.additional_videos || []);
      } else {
        console.log('Дополнительные видео для урока не найдены');
        setAdditionalVideos([]);
      }
    } catch (error) {
      console.error('Ошибка загрузки дополнительных видео урока:', error);
      setAdditionalVideos([]);
    }
  };

  // Загрузка данных первого урока
  const loadFirstLesson = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/api/lessons/first-lesson`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setLessonData(data.lesson);
      
      // Загрузить прогресс пользователя если есть
      await loadUserProgress();
      
    } catch (err) {
      console.error('Ошибка загрузки первого урока:', err);
      setError('Не удалось загрузить урок. Попробуйте обновить страницу.');
    } finally {
      setLoading(false);
    }
  };

  // Загрузка прогресса пользователя
  const loadUserProgress = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Загрузить общий прогресс урока
      const overallResponse = await fetch(
        `${backendUrl}/api/lessons/overall-progress/lesson_numerom_intro`, 
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      
      if (overallResponse.ok) {
        const overallData = await overallResponse.json();
        setOverallProgress(overallData.overall_percentage);
        
        // Обновить завершенные секции на основе данных с сервера
        const newCompletedSections = new Set();
        if (overallData.breakdown.theory) newCompletedSections.add('theory');
        if (overallData.breakdown.exercises) newCompletedSections.add('exercises');
        if (overallData.breakdown.quiz) newCompletedSections.add('quiz');
        if (overallData.breakdown.challenge) newCompletedSections.add('challenge');
        if (overallData.breakdown.habits) newCompletedSections.add('habits');
        
        setCompletedSections(newCompletedSections);
      }
      
      // Загрузить ответы на упражнения
      const exerciseResponse = await fetch(
        `${backendUrl}/api/lessons/exercise-responses/lesson_numerom_intro`, 
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      
      if (exerciseResponse.ok) {
        const exerciseData = await exerciseResponse.json();
        setExerciseResponses(exerciseData.responses || {});
        setSavedExercises(new Set(Object.keys(exerciseData.responses || {})));
      }
      
      // Загрузить прогресс челленджа
      const challengeResponse = await fetch(
        `${backendUrl}/api/lessons/challenge-progress/challenge_sun_7days`, 
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
      
    } catch (err) {
      console.error('Ошибка загрузки прогресса:', err);
    }
  };

  // Сохранить ответ на упражнение
  const saveExerciseResponse = async (exerciseId, responseText) => {
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('lesson_id', 'lesson_numerom_intro');
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
        // Перезагрузить прогресс
        await loadUserProgress();
        return true;
      }
      return false;
    } catch (err) {
      console.error('Ошибка сохранения ответа:', err);
      return false;
    }
  };

  // Завершить челлендж с оценкой
  const completeChallenge = async (rating, notes = '') => {
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('challenge_id', 'challenge_sun_7days');
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
        const data = await response.json();
        setChallengeCompleted(true);
        setChallengeRating(rating);
        // Перезагрузить прогресс
        await loadUserProgress();
        return true;
      }
      return false;
    } catch (err) {
      console.error('Ошибка завершения челленджа:', err);
      return false;
    }
  };

  // Начать челлендж
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
      
      // Добавить трекер привычек
      await addHabitTracker();
      
    } catch (err) {
      console.error('Ошибка начала челленджа:', err);
      setError('Не удалось начать челлендж. Попробуйте еще раз.');
    }
  };

  // Отметить день челленджа как выполненный
  const completeChallengeDay = async (day, notes = '') => {
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('challenge_id', 'challenge_sun_7days');
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

      // Обновить прогресс
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

  // Добавить трекер привычек
  const addHabitTracker = async () => {
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('lesson_id', 'lesson_numerom_intro');

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

  // Обновить привычку
  const updateHabit = async (habitName, completed, notes = '') => {
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('lesson_id', 'lesson_numerom_intro');
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
        
        // Пересчитать прогресс привычек
        calculateHabitProgress();
        
        // Перезагрузить общий прогресс
        await loadUserProgress();
      }
    } catch (err) {
      console.error('Ошибка обновления привычки:', err);
    }
  };

  // Рассчитать прогресс привычек
  const calculateHabitProgress = () => {
    if (!habitTracker?.active_habits) return;
    
    const totalHabits = habitTracker.active_habits.length;
    const completedHabits = Object.values(todayHabits).filter(Boolean).length;
    const progressPercent = Math.round((completedHabits / totalHabits) * 100);
    
    setHabitProgress(progressPercent);
    
    // Если достигнут 100%, увеличить счетчик дней
    if (progressPercent === 100) {
      setHabitStreakDays(prev => prev + 1);
    }
  };

  // Сбросить трекер привычек для нового дня
  const resetHabitsForNewDay = () => {
    setTodayHabits({});
    setHabitProgress(0);
  };

  // Отправить квиз
  const submitQuiz = async () => {
    if (Object.keys(quizAnswers).length < 5) {
      setError('Пожалуйста, ответьте на все вопросы');
      return;
    }

    try {
      setQuizSubmitting(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('quiz_id', 'quiz_intro_1');
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
        // Перезагрузить прогресс
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

  // Сбросить квиз для повторной попытки
  const resetQuiz = () => {
    setQuizAnswers({});
    setQuizResults(null);
    setError('');
  };

  // Отметить упражнение как выполненное
  const completeExercise = (exerciseId) => {
    setCompletedExercises(prev => new Set([...prev, exerciseId]));
    setCompletedSections(prev => new Set([...prev, 'exercises']));
  };

  // Отметить теорию как прочитанную
  const completeTheory = () => {
    setCompletedSections(prev => new Set([...prev, 'theory']));
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader className="w-6 h-6 animate-spin mr-2" />
          <span>Загружаем первое занятие NumerOM...</span>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <div className="text-red-500 mb-4">{error}</div>
          <Button onClick={loadFirstLesson} variant="outline">
            Попробовать снова
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!lessonData) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <BookOpen className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
          <p>Урок не найден</p>
        </CardContent>
      </Card>
    );
  }

  const sectionProgress = [
    { id: 'theory', title: 'Теория', icon: <BookOpen className="w-4 h-4" />, completed: completedSections.has('theory') },
    { id: 'exercises', title: 'Упражнения', icon: <Brain className="w-4 h-4" />, completed: completedSections.has('exercises') },
    { id: 'quiz', title: 'Тест', icon: <Target className="w-4 h-4" />, completed: completedSections.has('quiz') },
    { id: 'challenge', title: 'Челлендж', icon: <Zap className="w-4 h-4" />, completed: challengeStarted },
    { id: 'habits', title: 'Привычки', icon: <Star className="w-4 h-4" />, completed: habitTracker !== null }
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* УЛУЧШЕННЫЙ ЗАГОЛОВОК УРОКА */}
      <div className="relative overflow-hidden">
        <Card className="border border-gray-200 bg-white shadow-sm">          
          <CardHeader className="p-6 border-b border-gray-100">
            <div className="flex items-start justify-between flex-wrap gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-4 mb-4">
                  <div className="p-3 bg-blue-50 rounded-xl border border-blue-100">
                    <Rocket className="w-8 h-8 text-blue-600" />
                  </div>
                  <div>
                    <CardTitle className="text-2xl sm:text-3xl font-semibold text-gray-900 mb-2">
                      {lessonData.title}
                    </CardTitle>
                    <CardDescription className="text-gray-600 text-base">
                      Введение в NumerOM: История космического корабля и основы нумерологии
                    </CardDescription>
                  </div>
                </div>
              </div>
              
              <div className="text-right">
                <div className="flex flex-col items-end gap-2 mb-4">
                  <Badge className="bg-green-50 text-green-700 border border-green-200 font-medium px-4 py-2 rounded-full">
                    🎁 Бесплатный урок
                  </Badge>
                  <Badge className="bg-gray-50 text-gray-700 border border-gray-200 px-3 py-1">
                    Модуль 1 • Базовый уровень
                  </Badge>
                </div>
                <div className="flex items-center gap-4 text-sm text-white/90">
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
            
            {/* Улучшенная шкала прогресса */}
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
            
            {/* Мини-индикаторы разделов */}
            <div className="mt-8 flex flex-wrap gap-2">
              {sectionProgress.map((section) => (
                <div
                  key={section.id}
                  className={`flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium transition-all ${
                    section.completed 
                      ? 'bg-green-500/20 text-green-100 border border-green-500/30' 
                      : 'bg-white/10 text-white/70 border border-white/20'
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

      {/* УЛУЧШЕННАЯ НАВИГАЦИЯ РАЗДЕЛОВ */}
      <Tabs value={activeSection} onValueChange={setActiveSection} className="space-y-8">
        <div className="sticky top-4 z-40 bg-white/95 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200/50 p-2">
          <TabsList className="grid w-full grid-cols-5 bg-transparent gap-1">
            {[
              { id: 'theory', label: 'Теория', icon: BookOpen, color: 'blue' },
              { id: 'exercises', label: 'Упражнения', icon: Brain, color: 'green' },
              { id: 'quiz', label: 'Тест', icon: Target, color: 'orange' },
              { id: 'challenge', label: 'Челлендж', icon: Zap, color: 'purple' },
              { id: 'habits', label: 'Привычки', icon: Star, color: 'pink' }
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

        {/* ТЕОРИЯ */}
        <TabsContent value="theory" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <BookOpen className="w-5 h-5 mr-2" />
                Что такое нумерология?
              </CardTitle>
            </CardHeader>
            <CardContent className="prose max-w-none">
              <p className="text-gray-700 leading-relaxed text-lg">
                {lessonData.content?.theory?.what_is_numerology}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Rocket className="w-5 h-5 mr-2" />
                История космического корабля
              </CardTitle>
              <CardDescription>
                Представьте космический корабль, где каждая планета выполняет свою роль
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Планеты в нумерологическом порядке с ведическими символами */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                {[
                  { 
                    number: 1, 
                    name: "СОЛНЦЕ", 
                    graha: "Surya (Сурья)",
                    icon: "☉", 
                    color: "from-yellow-300 to-yellow-400", 
                    textColor: "text-yellow-800", 
                    bgColor: "bg-yellow-50",
                    borderColor: "border-yellow-200",
                    description: "Создание идеи о корабле, лидерство, вдохновение команды"
                  },
                  { 
                    number: 2, 
                    name: "ЛУНА", 
                    graha: "Chandra (Чандра)",
                    icon: "☽", 
                    color: "from-white to-gray-100", 
                    textColor: "text-gray-800", 
                    bgColor: "bg-gray-50",
                    borderColor: "border-gray-300 shadow-md",
                    description: "Обустройство уюта, взаимоотношения в команде"
                  },
                  { 
                    number: 3, 
                    name: "ЮПИТЕР", 
                    graha: "Guru (Гуру)",
                    icon: "♃", 
                    color: "from-orange-400 to-orange-600", 
                    textColor: "text-orange-800", 
                    bgColor: "bg-orange-50",
                    borderColor: "border-orange-200",
                    description: "Технологии, образование, банковская система"
                  },
                  { 
                    number: 4, 
                    name: "РАХУ", 
                    graha: "Rahu (Раху)",
                    icon: "☊", 
                    color: "from-gray-400 to-gray-500", 
                    textColor: "text-gray-800", 
                    bgColor: "bg-gray-50",
                    borderColor: "border-gray-300",
                    description: "Современные тенденции, продвинутые технологии"
                  },
                  { 
                    number: 5, 
                    name: "МЕРКУРИЙ", 
                    graha: "Budha (Буддха)",
                    icon: "☿", 
                    color: "from-emerald-300 to-emerald-400", 
                    textColor: "text-emerald-800", 
                    bgColor: "bg-emerald-50",
                    borderColor: "border-emerald-200",
                    description: "Коммуникации, связь между отделами"
                  },
                  { 
                    number: 6, 
                    name: "ВЕНЕРА", 
                    graha: "Shukra (Шукра)",
                    icon: "♀", 
                    color: "from-pink-300 to-pink-400", 
                    textColor: "text-pink-800", 
                    bgColor: "bg-pink-50",
                    borderColor: "border-pink-200",
                    description: "Красота, дизайн корабля, эстетика"
                  },
                  { 
                    number: 7, 
                    name: "КЕТУ", 
                    graha: "Ketu (Кету)",
                    icon: "☋", 
                    color: "from-violet-400 to-violet-500", 
                    textColor: "text-violet-800", 
                    bgColor: "bg-violet-50",
                    borderColor: "border-violet-200",
                    description: "Духовность, философия путешествий"
                  },
                  { 
                    number: 8, 
                    name: "САТУРН", 
                    graha: "Shani (Шани)",
                    icon: "♄", 
                    color: "from-slate-500 to-slate-600", 
                    textColor: "text-slate-800", 
                    bgColor: "bg-slate-50",
                    borderColor: "border-slate-300",
                    description: "Порядок, контроль, регламенты, дисциплина"
                  },
                  { 
                    number: 9, 
                    name: "МАРС", 
                    graha: "Mangal (Мангал)",
                    icon: "♂", 
                    color: "from-red-400 to-red-500", 
                    textColor: "text-red-800", 
                    bgColor: "bg-red-50",
                    borderColor: "border-red-200",
                    description: "Энергия двигателей, движение, действие"
                  }
                ].map((planet) => (
                  <div 
                    key={planet.number} 
                    className={`p-4 rounded-lg border-2 hover:shadow-lg transition-all duration-300 transform hover:scale-105 ${planet.bgColor} ${planet.borderColor}`}
                  >
                    <div className="flex items-center mb-3">
                      <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${planet.color} flex items-center justify-center mr-3 shadow-lg`}>
                        <span className="text-2xl text-white font-bold filter drop-shadow-sm">{planet.icon}</span>
                      </div>
                      <div className="flex-1">
                        <h3 className={`font-bold text-base ${planet.textColor}`}>
                          {planet.name} ({planet.number})
                        </h3>
                        <div className={`text-xs ${planet.textColor} opacity-75 font-medium`}>
                          {planet.graha}
                        </div>
                      </div>
                    </div>
                    <p className={`text-sm leading-relaxed ${planet.textColor} opacity-90`}>
                      {planet.description}
                    </p>
                  </div>
                ))}
              </div>

              {/* УЛУЧШЕННЫЙ БЛОК ДОПОЛНИТЕЛЬНЫХ МАТЕРИАЛОВ С НАВИГАЦИЕЙ */}
              {(additionalVideos.length > 0 || additionalPdfs.length > 0) && (
                <div className="mb-8">
                  {/* Заголовок секции */}
                  <div className="text-center mb-6">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-purple-600 via-blue-600 to-indigo-600 rounded-full mb-4 shadow-lg">
                      <Video className="w-8 h-8 text-white" />
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">Учебные материалы</h3>
                    <p className="text-gray-600 max-w-md mx-auto">
                      Изучите видеоуроки и справочные материалы для глубокого понимания нумерологии
                    </p>
                  </div>

                  {/* Основной контейнер с навигацией */}
                  <div className="bg-gradient-to-br from-purple-50/50 via-blue-50/50 to-indigo-50/50 rounded-2xl border border-purple-200/50 shadow-xl backdrop-blur-sm overflow-hidden">
                    
                    {/* Панель управления и навигации */}
                    <div className="p-6 border-b border-purple-200/30 bg-white/30 backdrop-blur-sm">
                      <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
                        
                        {/* Левая часть - фильтры */}
                        <div className="flex flex-wrap items-center gap-3">
                          <span className="text-sm font-medium text-gray-700">Показать:</span>
                          <div className="flex items-center bg-white rounded-lg border border-purple-200/50 overflow-hidden">
                            <button
                              onClick={() => setMaterialsFilter('all')}
                              className={`px-4 py-2 text-sm font-medium transition-all ${
                                materialsFilter === 'all' 
                                  ? 'bg-purple-600 text-white' 
                                  : 'text-gray-600 hover:bg-purple-50'
                              }`}
                            >
                              Все ({additionalVideos.length + additionalPdfs.length})
                            </button>
                            <button
                              onClick={() => setMaterialsFilter('videos')}
                              className={`px-4 py-2 text-sm font-medium transition-all border-l border-purple-200/50 ${
                                materialsFilter === 'videos' 
                                  ? 'bg-purple-600 text-white' 
                                  : 'text-gray-600 hover:bg-purple-50'
                              }`}
                            >
                              <PlayCircle className="w-4 h-4 inline mr-1" />
                              Видео ({additionalVideos.length})
                            </button>
                            <button
                              onClick={() => setMaterialsFilter('pdfs')}
                              className={`px-4 py-2 text-sm font-medium transition-all border-l border-purple-200/50 ${
                                materialsFilter === 'pdfs' 
                                  ? 'bg-purple-600 text-white' 
                                  : 'text-gray-600 hover:bg-purple-50'
                              }`}
                            >
                              <FileText className="w-4 h-4 inline mr-1" />
                              PDF ({additionalPdfs.length})
                            </button>
                          </div>
                        </div>

                        {/* Правая часть - поиск и сортировка */}
                        <div className="flex flex-wrap items-center gap-3">
                          {/* Поиск */}
                          <div className="relative">
                            <input
                              type="text"
                              placeholder="Поиск материалов..."
                              value={materialsSearch}
                              onChange={(e) => setMaterialsSearch(e.target.value)}
                              className="pl-10 pr-4 py-2 w-64 border border-purple-200/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white/70 backdrop-blur-sm text-sm"
                            />
                            <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
                              <Lightbulb className="w-4 h-4 text-gray-400" />
                            </div>
                          </div>

                          {/* Сортировка */}
                          <select
                            value={materialsSortBy}
                            onChange={(e) => setMaterialsSortBy(e.target.value)}
                            className="px-3 py-2 border border-purple-200/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 bg-white/70 backdrop-blur-sm text-sm"
                          >
                            <option value="recent">По дате ↓</option>
                            <option value="name">По названию ↑</option>
                            <option value="type">По типу</option>
                          </select>
                        </div>
                      </div>

                      {/* Индикатор активного фильтра */}
                      {(materialsSearch.trim() || materialsFilter !== 'all') && (
                        <div className="mt-4 flex items-center gap-2">
                          <span className="text-sm text-gray-600">Активные фильтры:</span>
                          {materialsSearch.trim() && (
                            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                              🔍 "{materialsSearch}"
                              <button 
                                onClick={() => setMaterialsSearch('')}
                                className="ml-2 hover:text-blue-900"
                              >
                                ×
                              </button>
                            </span>
                          )}
                          {materialsFilter !== 'all' && (
                            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs bg-purple-100 text-purple-800">
                              {materialsFilter === 'videos' ? '🎬' : '📄'} 
                              {materialsFilter === 'videos' ? 'Только видео' : 'Только PDF'}
                              <button 
                                onClick={() => setMaterialsFilter('all')}
                                className="ml-2 hover:text-purple-900"
                              >
                                ×
                              </button>
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Результаты поиска и контент */}
                    {filteredMaterials.length === 0 ? (
                      <div className="p-12 text-center">
                        <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
                          <Lightbulb className="w-8 h-8 text-gray-400" />
                        </div>
                        <h4 className="text-lg font-semibold text-gray-900 mb-2">Материалы не найдены</h4>
                        <p className="text-gray-600 mb-4">
                          {materialsSearch.trim() 
                            ? `По запросу "${materialsSearch}" ничего не найдено`
                            : 'Выберите другой фильтр или измените критерии поиска'
                          }
                        </p>
                        <Button
                          onClick={() => {
                            setMaterialsSearch('');
                            setMaterialsFilter('all');
                          }}
                          variant="outline"
                          className="border-purple-600 text-purple-600 hover:bg-purple-50"
                        >
                          Сбросить фильтры
                        </Button>
                      </div>
                    ) : (
                      <>
                        {/* Видео материалы */}
                        {videoMaterials.length > 0 && (materialsFilter === 'all' || materialsFilter === 'videos') && (
                          <div className="p-6 border-b border-purple-200/30">
                            <div className="flex items-center justify-between mb-4">
                              <div className="flex items-center">
                                <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg mr-3">
                                  <PlayCircle className="w-5 h-5 text-white" />
                                </div>
                                <div>
                                  <h4 className="text-lg font-semibold text-gray-900">Видеоуроки</h4>
                                  <p className="text-sm text-gray-600">
                                    {videoMaterials.length} из {additionalVideos.length} видео
                                  </p>
                                </div>
                              </div>
                              {videoMaterials.length !== additionalVideos.length && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => {
                                    setMaterialsFilter('videos');
                                    setMaterialsSearch('');
                                  }}
                                  className="text-purple-600 border-purple-600 hover:bg-purple-50"
                                >
                                  Показать все видео
                                </Button>
                              )}
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {videoMaterials.map((video, index) => (
                                <div key={video.file_id} className="group bg-white rounded-xl border border-purple-200/50 shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden">
                                  <div className="aspect-video bg-gradient-to-br from-purple-100 to-blue-100 flex items-center justify-center relative">
                                    <div className="absolute inset-0 bg-gradient-to-br from-purple-600/20 to-blue-600/20"></div>
                                    <PlayCircle className="w-16 h-16 text-purple-600 drop-shadow-lg relative z-10" />
                                    <div className="absolute top-2 left-2 bg-purple-600 text-white text-xs font-medium px-2 py-1 rounded-full">
                                      Урок {index + 1}
                                    </div>
                                    <div className="absolute bottom-2 right-2 bg-black/50 text-white text-xs px-2 py-1 rounded">
                                      Видео
                                    </div>
                                  </div>
                                  <div className="p-4">
                                    <h5 className="font-semibold text-gray-900 mb-2">{video.title}</h5>
                                    <p className="text-sm text-gray-600 mb-3">Дополнительный материал для углубленного изучения</p>
                                    <Button 
                                      onClick={() => {
                                        setSelectedVideo({
                                          url: `${backendUrl}${video.video_url}`,
                                          title: video.title,
                                          description: `Дополнительный видеоматериал: ${video.title}`
                                        });
                                      }}
                                      className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-medium"
                                    >
                                      <PlayCircle className="w-4 h-4 mr-2" />
                                      Смотреть видео
                                    </Button>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* PDF материалы */}
                        {pdfMaterials.length > 0 && (materialsFilter === 'all' || materialsFilter === 'pdfs') && (
                          <div className="p-6">
                            <div className="flex items-center justify-between mb-4">
                              <div className="flex items-center">
                                <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-r from-green-600 to-emerald-600 rounded-lg mr-3">
                                  <FileText className="w-5 h-5 text-white" />
                                </div>
                                <div>
                                  <h4 className="text-lg font-semibold text-gray-900">Справочные материалы</h4>
                                  <p className="text-sm text-gray-600">
                                    {pdfMaterials.length} из {additionalPdfs.length} документов
                                  </p>
                                </div>
                              </div>
                              {pdfMaterials.length !== additionalPdfs.length && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => {
                                    setMaterialsFilter('pdfs');
                                    setMaterialsSearch('');
                                  }}
                                  className="text-green-600 border-green-600 hover:bg-green-50"
                                >
                                  Показать все PDF
                                </Button>
                              )}
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                              {pdfMaterials.map((pdf, index) => (
                                <div key={pdf.file_id} className="group bg-white rounded-xl border border-green-200/50 shadow-sm hover:shadow-md transition-all duration-200 p-4">
                                  <div className="flex items-start mb-3">
                                    <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-r from-green-600 to-emerald-600 rounded-lg mr-3 flex-shrink-0 relative">
                                      <FileText className="w-6 h-6 text-white" />
                                      <div className="absolute -top-1 -right-1 bg-green-700 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold">
                                        {index + 1}
                                      </div>
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <h5 className="font-semibold text-gray-900 mb-1">{pdf.title}</h5>
                                      <p className="text-sm text-gray-600">Дополнительный справочный материал</p>
                                    </div>
                                  </div>
                                  <div className="space-y-2">
                                    <Button 
                                      onClick={() => {
                                        setSelectedPDF({
                                          url: `${backendUrl}${pdf.pdf_url}`,
                                          title: pdf.title
                                        });
                                      }}
                                      className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-medium"
                                    >
                                      <Eye className="w-4 h-4 mr-2" />
                                      Открыть PDF
                                    </Button>
                                    <Button 
                                      onClick={() => {
                                        const link = document.createElement('a');
                                        link.href = `${backendUrl}${pdf.pdf_url}`;
                                        link.download = pdf.filename;
                                        link.click();
                                      }}
                                      variant="outline" 
                                      className="w-full border-green-600 text-green-600 hover:bg-green-50 font-medium"
                                    >
                                      <Download className="w-4 h-4 mr-2" />
                                      Скачать
                                    </Button>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    )}

                    {/* Улучшенная информационная панель */}
                    <div className="bg-gradient-to-r from-purple-600/5 to-blue-600/5 border-t border-purple-200/30 p-4">
                      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                        <div className="flex items-center text-sm text-gray-600">
                          <Sparkles className="w-4 h-4 mr-2 text-purple-600" />
                          <span>
                            Показано {filteredMaterials.length} из {additionalVideos.length + additionalPdfs.length} материалов
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-gray-500">
                          <div className="flex items-center">
                            <PlayCircle className="w-3 h-3 mr-1 text-purple-600" />
                            {videoMaterials.length} видео
                          </div>
                          <div className="flex items-center">
                            <FileText className="w-3 h-3 mr-1 text-green-600" />
                            {pdfMaterials.length} PDF
                          </div>
                          <div className="flex items-center">
                            <Timer className="w-3 h-3 mr-1 text-blue-600" />
                            Обновлено недавно
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold mb-2 flex items-center">
                  <Lightbulb className="w-4 h-4 mr-2 text-blue-600" />
                  Три состояния планет (Гуны)
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                  <div className="p-3 bg-red-50 rounded border-l-4 border-red-400">
                    <div className="font-medium text-red-700">🔴 РАДЖАС</div>
                    <div className="text-red-600">Активность, страсть, действие</div>
                  </div>
                  <div className="p-3 bg-blue-50 rounded border-l-4 border-blue-400">
                    <div className="font-medium text-blue-700">🔵 САТТВА</div>
                    <div className="text-blue-600">Гармония, мудрость, баланс</div>
                  </div>
                  <div className="p-3 bg-gray-50 rounded border-l-4 border-gray-400">
                    <div className="font-medium text-gray-700">⚫ ТАМАС</div>
                    <div className="text-gray-600">Инертность, лень, разрушение</div>
                  </div>
                </div>
              </div>
              
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
            </CardContent>
          </Card>
        </TabsContent>

        {/* УПРАЖНЕНИЯ */}
        <TabsContent value="exercises" className="space-y-6">
          {lessonData.exercises?.map((exercise, index) => (
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
          
          {completedExercises.size === lessonData.exercises?.length && lessonData.exercises?.length > 0 && (
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
        </TabsContent>

        {/* КВИЗ */}
        <TabsContent value="quiz" className="space-y-6">
          {!quizResults ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Target className="w-5 h-5 mr-2" />
                  {lessonData.quiz?.title}
                </CardTitle>
                <CardDescription>
                  Ответьте на все вопросы для проверки знаний. Для прохождения нужно набрать минимум 60%.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {lessonData.quiz?.questions?.map((question, index) => (
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
                
                <div className="pt-4 text-center">
                  <Button 
                    onClick={submitQuiz}
                    disabled={quizSubmitting || Object.keys(quizAnswers).length < 5}
                    className="numerology-gradient px-8"
                  >
                    {quizSubmitting ? (
                      <>
                        <Loader className="w-4 h-4 animate-spin mr-2" />
                        Проверяем ответы...
                      </>
                    ) : (
                      <>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Отправить ответы
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className={quizResults.passed && quizResults.percentage === 100 ? "border-green-200 bg-green-50" : "border-orange-200 bg-orange-50"}>
              <CardHeader>
                <CardTitle className={`flex items-center ${quizResults.passed && quizResults.percentage === 100 ? "text-green-800" : "text-orange-800"}`}>
                  {quizResults.passed && quizResults.percentage === 100 ? (
                    <>
                      <Trophy className="w-5 h-5 mr-2" />
                      Тест пройден на 100%!
                    </>
                  ) : (
                    <>
                      <Clock className="w-5 h-5 mr-2" />
                      Требуется 100% для прохождения
                    </>
                  )}
                </CardTitle>
                <CardDescription className={quizResults.passed && quizResults.percentage === 100 ? "text-green-700" : "text-orange-700"}>
                  Результат: {quizResults.score} из {quizResults.total_questions} ({quizResults.percentage.toFixed(1)}%)
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {quizResults.results?.map((result, index) => (
                  <div key={index} className={`p-3 rounded-lg border ${result.is_correct ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                    <div className="font-medium text-sm mb-1">{result.question}</div>
                    <div className="text-xs space-y-1">
                      <div>Ваш ответ: <span className={result.is_correct ? 'text-green-700' : 'text-red-700'}>{result.user_answer}</span></div>
                      {!result.is_correct && (
                        <div>Правильный ответ: <span className="text-green-700">{result.correct_answer}</span></div>
                      )}
                      <div className="text-gray-600 mt-2">{result.explanation}</div>
                    </div>
                  </div>
                ))}
                
                <div className="text-center pt-4 space-y-3">
                  {quizResults.passed && quizResults.percentage === 100 ? (
                    <>
                      <div className="p-3 bg-green-100 rounded-lg">
                        <div className="text-green-800 font-semibold">🎉 Поздравляем!</div>
                        <div className="text-green-700 text-sm">Тест успешно пройден и засчитан в отчёт</div>
                      </div>
                      <Button onClick={() => setActiveSection('challenge')} className="numerology-gradient">
                        Перейти к челленджу
                      </Button>
                    </>
                  ) : (
                    <>
                      <div className="p-3 bg-orange-100 rounded-lg">
                        <div className="text-orange-800 font-semibold">⚠️ Для прохождения нужно 100%</div>
                        <div className="text-orange-700 text-sm">Изучите правильные ответы и попробуйте снова</div>
                      </div>
                      <Button 
                        onClick={resetQuiz}
                        className="bg-orange-600 hover:bg-orange-700 text-white"
                      >
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Пройти тест заново
                      </Button>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ЧЕЛЛЕНДЖ */}
        <TabsContent value="challenge" className="space-y-6">
          {!challengeStarted ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Sun className="w-5 h-5 mr-2 text-yellow-600" />
                  {lessonData.challenges?.[0]?.title}
                </CardTitle>
                <CardDescription>
                  {lessonData.challenges?.[0]?.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-center mb-2">
                    <Calendar className="w-5 h-5 text-yellow-600 mr-2" />
                    <span className="font-semibold text-yellow-800">7-дневный челлендж</span>
                  </div>
                  <p className="text-yellow-700 text-sm">
                    Ежедневные практики для активации энергии Солнца (Сурьи) - 
                    лидерства, уверенности и силы воли.
                  </p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {lessonData.challenges?.[0]?.daily_tasks?.slice(0, 3).map((task, index) => (
                    <div key={index} className="p-3 border rounded-lg">
                      <div className="font-medium text-sm mb-2">День {task.day}: {task.title}</div>
                      <ul className="text-xs text-gray-600 space-y-1">
                        {task.tasks?.slice(0, 2).map((subtask, idx) => (
                          <li key={idx}>• {subtask}</li>
                        ))}
                        {task.tasks?.length > 2 && <li>• и еще {task.tasks.length - 2}...</li>}
                      </ul>
                    </div>
                  ))}
                </div>
                
                <div className="text-center pt-4">
                  <Button 
                    onClick={() => startChallenge('challenge_sun_7days')}
                    className="bg-yellow-600 hover:bg-yellow-700 text-white px-8"
                  >
                    <Sun className="w-4 h-4 mr-2" />
                    Начать 7-дневный челлендж
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : challengeCompleted ? (
            // Завершенный челлендж с оценкой
            <Card className="border-green-200 bg-green-50">
              <CardHeader>
                <CardTitle className="flex items-center text-green-800">
                  <Trophy className="w-5 h-5 mr-2" />
                  Челлендж завершен!
                </CardTitle>
                <CardDescription className="text-green-700">
                  Поздравляем с успешным прохождением 7-дневного челленджа энергии Солнца
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-7 gap-2 mb-4">
                  {Array.from({length: 7}, (_, i) => (
                    <div 
                      key={i + 1}
                      className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium bg-green-500 border-green-500 text-white"
                    >
                      <CheckCircle className="w-4 h-4" />
                    </div>
                  ))}
                </div>
                
                <div className="p-4 bg-green-100 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-green-800">Ваша оценка:</span>
                    <div className="flex items-center">
                      {Array.from({length: 5}, (_, i) => (
                        <Star 
                          key={i} 
                          className={`w-5 h-5 ${i < challengeRating ? 'text-yellow-400 fill-current' : 'text-gray-300'}`} 
                        />
                      ))}
                      <span className="ml-2 font-semibold text-green-800">{challengeRating}/5</span>
                    </div>
                  </div>
                  <div className="text-green-700 text-sm">
                    {challengeRating === 5 && "Превосходно! Вы полностью освоили энергию Солнца!"}
                    {challengeRating === 4 && "Отлично! Вы очень хорошо работали с энергией лидерства."}
                    {challengeRating === 3 && "Хорошо! Вы усвоили основы работы с солнечной энергией."}
                    {challengeRating === 2 && "Неплохо! Продолжайте практиковать для лучших результатов."}
                    {challengeRating === 1 && "Начало положено! Рекомендуем повторить челлендж."}
                  </div>
                </div>
                
                <div className="w-full bg-green-200 rounded-full h-3">
                  <div className="bg-green-600 h-3 rounded-full w-full"></div>
                </div>
                
                <div className="text-center text-sm text-green-700">
                  Завершено: 7 из 7 дней (100%)
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-6">
              {/* Прогресс челленджа */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Sun className="w-5 h-5 mr-2 text-yellow-600" />
                      Челлендж активен
                    </div>
                    <Badge className="bg-yellow-100 text-yellow-800">
                      День {challengeProgress?.current_day || 1} из 7
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-7 gap-2 mb-4">
                    {Array.from({length: 7}, (_, i) => {
                      const day = i + 1;
                      const isCompleted = challengeProgress?.completed_days?.includes(day);
                      const isCurrent = day === (challengeProgress?.current_day || 1);
                      
                      return (
                        <div 
                          key={day}
                          className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium border-2 
                            ${isCompleted 
                              ? 'bg-green-500 border-green-500 text-white' 
                              : isCurrent 
                                ? 'border-yellow-500 text-yellow-600 bg-yellow-50' 
                                : 'border-gray-300 text-gray-400'
                            }`}
                        >
                          {isCompleted ? <CheckCircle className="w-4 h-4" /> : day}
                        </div>
                      );
                    })}
                  </div>
                  
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-yellow-600 h-2 rounded-full transition-all duration-500"
                      style={{width: `${((challengeProgress?.completed_days?.length || 0) / 7) * 100}%`}}
                    ></div>
                  </div>
                  
                  <div className="text-center text-sm text-gray-600 mt-2">
                    Выполнено: {challengeProgress?.completed_days?.length || 0} из 7 дней
                  </div>
                  
                  {/* Показать кнопку завершения если все 7 дней выполнены */}
                  {(challengeProgress?.completed_days?.length || 0) >= 7 && !challengeCompleted && (
                    <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                      <h4 className="font-semibold text-green-800 mb-3">Поздравляем! Вы выполнили все 7 дней челленджа!</h4>
                      <p className="text-green-700 text-sm mb-4">
                        Оцените свой опыт прохождения челленджа от 1 до 5 звезд
                      </p>
                      
                      <div className="flex items-center justify-center space-x-1 mb-4">
                        {Array.from({length: 5}, (_, i) => (
                          <button
                            key={i}
                            onClick={() => setChallengeRating(i + 1)}
                            className="p-1 hover:scale-110 transition-transform"
                          >
                            <Star 
                              className={`w-8 h-8 ${i < challengeRating ? 'text-yellow-400 fill-current' : 'text-gray-300 hover:text-yellow-200'}`} 
                            />
                          </button>
                        ))}
                      </div>
                      
                      <Button 
                        onClick={() => {
                          if (challengeRating > 0) {
                            completeChallenge(challengeRating, 'Челлендж завершен успешно');
                          } else {
                            setError('Пожалуйста, поставьте оценку');
                          }
                        }}
                        disabled={challengeRating === 0}
                        className="w-full bg-green-600 hover:bg-green-700"
                      >
                        <Trophy className="w-4 h-4 mr-2" />
                        Завершить челлендж
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
              
              {/* Текущий день челленджа */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>
                      День {selectedChallengeDay}: {lessonData.challenges?.[0]?.daily_tasks?.[selectedChallengeDay - 1]?.title}
                    </span>
                    <Checkbox
                      checked={challengeProgress?.completed_days?.includes(selectedChallengeDay)}
                      onCheckedChange={(checked) => {
                        if (checked && !challengeProgress?.completed_days?.includes(selectedChallengeDay)) {
                          completeChallengeDay(selectedChallengeDay);
                        }
                      }}
                    />
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <ul className="space-y-2">
                    {lessonData.challenges?.[0]?.daily_tasks?.[selectedChallengeDay - 1]?.tasks?.map((task, index) => (
                      <li key={index} className="flex items-start space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <span className="text-sm">{task}</span>
                      </li>
                    ))}
                  </ul>
                  
                  <div className="flex gap-2 flex-wrap">
                    {Array.from({length: 7}, (_, i) => {
                      const day = i + 1;
                      const isCompleted = challengeProgress?.completed_days?.includes(day);
                      return (
                        <Button
                          key={day}
                          variant={selectedChallengeDay === day ? "default" : "outline"}
                          size="sm"
                          onClick={() => setSelectedChallengeDay(day)}
                          className={isCompleted ? 'border-green-500 bg-green-50 text-green-700' : ''}
                        >
                          {isCompleted && <CheckCircle className="w-3 h-3 mr-1" />}
                          День {day}
                        </Button>
                      );
                    })}
                  </div>
                  
                  {!challengeProgress?.completed_days?.includes(selectedChallengeDay) && (
                    <div className="space-y-3 pt-4 border-t">
                      <textarea 
                        placeholder="Поделитесь своими впечатлениями от выполнения задач дня..."
                        className="w-full p-3 border rounded-lg min-h-20 text-sm"
                      />
                      <Button 
                        onClick={() => completeChallengeDay(selectedChallengeDay)}
                        className="w-full sm:w-auto bg-green-600 hover:bg-green-700"
                      >
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Отметить день как выполненный
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* ТРЕКЕР ПРИВЫЧЕК */}
        <TabsContent value="habits" className="space-y-6">
          {!habitTracker ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Star className="w-5 h-5 mr-2" />
                  Трекер привычек энергии Солнца
                </CardTitle>
                <CardDescription>
                  Ежедневные практики для укрепления лидерских качеств и уверенности
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center py-8">
                <Star className="w-12 h-12 text-yellow-600 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">
                  Начните челлендж, чтобы активировать трекер привычек
                </p>
                <Button 
                  onClick={() => setActiveSection('challenge')}
                  variant="outline"
                >
                  Перейти к челленджу
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-6">
              {/* Статистика прогресса */}
              <Card className="border-yellow-200 bg-yellow-50">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Star className="w-5 h-5 mr-2 text-yellow-600" />
                      Прогресс привычек
                    </div>
                    <Badge className={`${habitProgress === 100 ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                      {habitProgress}%
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
                    <div className="text-center p-3 bg-white rounded-lg">
                      <div className="text-2xl font-bold text-yellow-600">{habitProgress}%</div>
                      <div className="text-xs text-gray-600">Сегодняшний прогресс</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg">
                      <div className="text-2xl font-bold text-green-600">{habitStreakDays}</div>
                      <div className="text-xs text-gray-600">Дней подряд 100%</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">{Object.values(todayHabits).filter(Boolean).length}</div>
                      <div className="text-xs text-gray-600">Привычек выполнено</div>
                    </div>
                  </div>
                  
                  <div className="w-full bg-yellow-200 rounded-full h-3 mb-2">
                    <div 
                      className={`h-3 rounded-full transition-all duration-500 ${habitProgress === 100 ? 'bg-green-600' : 'bg-yellow-600'}`}
                      style={{width: `${habitProgress}%`}}
                    ></div>
                  </div>
                  
                  {habitProgress === 100 && (
                    <div className="text-center mt-4">
                      <div className="p-3 bg-green-100 rounded-lg mb-3">
                        <div className="text-green-800 font-semibold">🎉 Отлично! Все привычки выполнены на сегодня!</div>
                        <div className="text-green-700 text-sm">Продолжайте завтра для поддержания серии</div>
                      </div>
                      <Button 
                        onClick={resetHabitsForNewDay}
                        className="bg-green-600 hover:bg-green-700 text-white"
                      >
                        <ArrowRight className="w-4 h-4 mr-2" />
                        Начать новый день привычек
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Основной трекер */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Heart className="w-5 h-5 mr-2 text-red-500" />
                    Ежедневные привычки - {new Date().toLocaleDateString('ru-RU')}
                  </CardTitle>
                  <CardDescription>
                    Отмечайте выполнение привычек каждый день для достижения 100%
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {habitTracker.active_habits?.map((habit, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                      <div className="flex items-center space-x-3 flex-1">
                        <Checkbox
                          checked={todayHabits[habit] || false}
                          onCheckedChange={(checked) => {
                            updateHabit(habit, checked);
                            // Немедленно обновить состояние для отзывчивости UI
                            setTimeout(calculateHabitProgress, 100);
                          }}
                        />
                        <span className={`text-sm flex-1 ${todayHabits[habit] ? 'line-through text-gray-500' : ''}`}>
                          {habit}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        {todayHabits[habit] && (
                          <Badge className="bg-green-100 text-green-800 text-xs">
                            ✓ Выполнено
                          </Badge>
                        )}
                        <div className="text-xs text-gray-400">
                          {index + 1}/5
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {habitProgress < 100 && (
                    <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="flex items-center mb-2">
                        <Lightbulb className="w-4 h-4 text-blue-600 mr-2" />
                        <span className="font-medium text-blue-800">Совет для достижения 100%</span>
                      </div>
                      <div className="text-blue-700 text-sm">
                        Выполните все {habitTracker.active_habits?.length || 0} привычек для полного прохождения дня. 
                        Трекер можно проходить каждый день для поддержания энергии Солнца.
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Enhanced Video Player Modal - как в PersonalConsultations */}
      {selectedVideo && (
        <EnhancedVideoViewer
          videoUrl={selectedVideo.url}
          title={selectedVideo.title}
          description={selectedVideo.description}
          onClose={() => setSelectedVideo(null)}
        />
      )}

      {/* PDF Viewer Modal - как в PersonalConsultations */}
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

export default FirstLesson;