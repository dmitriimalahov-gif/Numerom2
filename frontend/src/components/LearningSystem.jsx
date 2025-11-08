import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Alert, AlertDescription } from './ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import {
  Loader,
  PlayCircle,
  CheckCircle,
  Lock,
  Star,
  Trophy,
  BookOpen,
  Video,
  Clock,
  Target,
  Award,
  FileText,
  Brain,
  Zap,
  Calendar
} from 'lucide-react';
import { useAuth } from './AuthContext';
import axios from 'axios';
import EnhancedVideoViewer from './EnhancedVideoViewer';
import ConsultationPDFViewer from './ConsultationPDFViewer';
import WordViewer from './WordViewer';
import Quiz from './Quiz';
import UniversalLessonViewer from './UniversalLessonViewer';
import { getBackendUrl } from '../utils/backendUrl';

const LearningSystem = () => {
  const { user } = useAuth();
  const [learningData, setLearningData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedLesson, setSelectedLesson] = useState(null);
  const [selectedWord, setSelectedWord] = useState(null);
  const [showQuiz, setShowQuiz] = useState(false);
  const [quizData, setQuizData] = useState(null);
  const [generatingQuiz, setGeneratingQuiz] = useState(false);
  const [lessonCompleted, setLessonCompleted] = useState(false);
  
  // Убрано: showFirstLesson больше не используется, все уроки отображаются в одном списке

  const backendUrl = getBackendUrl();

  useEffect(() => {
    loadLearningData();
  }, []);

  // Сохранять selectedLesson в localStorage при изменении
  useEffect(() => {
    if (selectedLesson) {
      localStorage.setItem('learningSystem_selectedLessonId', selectedLesson.id || '');
      localStorage.setItem('learningSystem_selectedLessonData', JSON.stringify(selectedLesson));
    } else {
      localStorage.removeItem('learningSystem_selectedLessonId');
      localStorage.removeItem('learningSystem_selectedLessonData');
    }
  }, [selectedLesson]);

  // Восстановить selectedLesson при загрузке
  useEffect(() => {
    if (learningData?.available_lessons?.length > 0 && !selectedLesson) {
      const savedLessonId = localStorage.getItem('learningSystem_selectedLessonId');
      const savedLessonData = localStorage.getItem('learningSystem_selectedLessonData');

      if (savedLessonId && savedLessonData) {
        try {
          const lessonData = JSON.parse(savedLessonData);
          setSelectedLesson(lessonData);
        } catch (e) {
          console.error('Ошибка восстановления урока:', e);
        }
      }
    }
  }, [learningData]);

  const loadLearningData = async () => {
    setLoading(true);
    setError('');

    try {
      // ИСПОЛЬЗУЕМ НОВЫЙ ENDPOINT ДЛЯ ПОЛУЧЕНИЯ ВСЕХ УРОКОВ (включая custom_lessons)
      const response = await axios.get(`${backendUrl}/api/learning/all-lessons`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      setLearningData(response.data);
    } catch (error) {
      console.error('Error loading learning data:', error);
      setError(error.response?.data?.detail || 'Ошибка при загрузке данных обучения');
    } finally {
      setLoading(false);
    }
  };

  const completeLesson = async (lessonId, watchTime, quizScore) => {
    try {
      const response = await axios.post(`${backendUrl}/api/learning/complete-lesson/${lessonId}`, {
        watch_time: watchTime,
        quiz_score: quizScore
      });
      
      // Reload learning data to update progress
      await loadLearningData();
      
      return response.data;
    } catch (error) {
      console.error('Error completing lesson:', error);
      setError(error.response?.data?.detail || 'Ошибка при завершении урока');
    }
  };

  // Генерация Quiz на основе субтитров видео
  const generateQuizFromVideo = async (lesson) => {
    setGeneratingQuiz(true);
    try {
      const response = await axios.post(`${backendUrl}/api/learning/generate-quiz`, {
        lesson_id: lesson.id,
        video_url: lesson.video_url,
        video_file_id: lesson.video_file_id
      });
      
      setQuizData(response.data);
      return response.data;
    } catch (error) {
      console.error('Error generating quiz:', error);
      // Создаем базовый квиз если автоматическая генерация не удалась
      const fallbackQuiz = {
        questions: [
          {
            id: 1,
            question: "Вы просмотрели урок полностью?",
            options: ["Да, полностью", "Частично", "Только начало", "Не смотрел"],
            correct_answer: 0,
            explanation: "Для лучшего понимания материала рекомендуется просмотреть урок полностью."
          },
          {
            id: 2,
            question: "Что нового вы узнали из этого урока?",
            options: [
              "Новые концепции нумерологии",
              "Практические методы расчета",
              "Историческую информацию", 
              "Все вышеперечисленное"
            ],
            correct_answer: 3,
            explanation: "Каждый урок содержит комплексную информацию по нумерологии."
          }
        ],
        lesson_title: lesson.title,
        total_points: 10
      };
      setQuizData(fallbackQuiz);
      return fallbackQuiz;
    } finally {
      setGeneratingQuiz(false);
    }
  };

  // Обработка завершения просмотра видео
  const handleVideoComplete = async (lesson) => {
    setLessonCompleted(true);
    
    // Генерируем квиз автоматически
    await generateQuizFromVideo(lesson);
    
    // Показываем квиз после завершения видео
    setTimeout(() => {
      setShowQuiz(true);
    }, 1000);
  };

  // Обработка завершения квиза
  const handleQuizComplete = async (results) => {
    try {
      await axios.post(`${backendUrl}/api/learning/complete-lesson/${selectedLesson.id}`, {
        watch_time: 100, // Предполагаем полный просмотр
        quiz_score: results.score,
        quiz_answers: results.answers
      });
      
      // Обновляем данные обучения
      await loadLearningData();
      
      // Закрываем все модальные окна
      setShowQuiz(false);
      setSelectedLesson(null);
      setLessonCompleted(false);
      
    } catch (error) {
      console.error('Error completing lesson:', error);
    }
  };

  const getLevelName = (level) => {
    const levelNames = {
      1: "Новичок (प्रारंभिक)",
      2: "Ученик (छात्र)", 
      3: "Практикующий (अभ्यासी)",
      4: "Знающий (ज्ञानी)",
      5: "Опытный (अनुभवी)",
      6: "Мастер (गुरु)",
      7: "Эксперт (विशेषज्ञ)",
      8: "Мудрец (ऋषि)",
      9: "Учитель (आचार्य)",
      10: "Просветленный (जीवन्मुक्त)"
    };
    return levelNames[level] || `Уровень ${level}`;
  };

  const getLevelColor = (level) => {
    const colors = [
      '#E5E7EB', // Gray - Level 1
      '#FEF3C7', // Yellow - Level 2
      '#D1FAE5', // Green - Level 3
      '#DBEAFE', // Blue - Level 4
      '#E0E7FF', // Indigo - Level 5
      '#EDE9FE', // Purple - Level 6
      '#FCE7F3', // Pink - Level 7
      '#FED7AA', // Orange - Level 8
      '#FECACA', // Red - Level 9
      '#F3E8FF'  // Violet - Level 10
    ];
    return colors[level - 1] || colors[0];
  };

  const renderLevelProgress = () => {
    if (!learningData?.user_level) return null;

    const { current_level, experience_points, lessons_completed } = learningData.user_level;
    const nextLevelExp = current_level * 100; // Experience needed for next level
    const progressPercentage = (experience_points % 100);

    return (
      <Card className="mb-4 sm:mb-6" style={{ backgroundColor: getLevelColor(current_level) }}>
        <CardHeader className="p-4 sm:p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex-1">
              <CardTitle className="flex items-center text-lg sm:text-xl">
                <Trophy className="w-5 h-5 sm:w-6 sm:h-6 mr-2 text-yellow-600 flex-shrink-0" />
                <span>{getLevelName(current_level)}</span>
              </CardTitle>
              <CardDescription className="text-sm sm:text-base mt-1">
                Опыт: {experience_points} | Уроков: {lessons_completed}
              </CardDescription>
            </div>
            <div className="text-center sm:text-right">
              <div className="text-xl sm:text-2xl font-bold">{current_level}/10</div>
              <div className="text-xs sm:text-sm text-muted-foreground">Уровень</div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="px-4 pb-4 sm:px-6 sm:pb-6">
          <div className="space-y-2">
            <div className="flex justify-between text-xs sm:text-sm">
              <span>Прогресс до следующего уровня</span>
              <span>{progressPercentage}%</span>
            </div>
            <Progress value={progressPercentage} className="w-full h-2" />
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderLessonCard = (lesson) => {
    const isCompleted = lesson.completed;
    const isLocked = lesson.level > learningData?.user_level?.current_level;
    
    // Определяем тип урока и его медиа
    const hasVideo = lesson.video_url || lesson.video_file_id;
    const hasPDF = lesson.pdf_file_id;
    const hasQuizQuestions = lesson.quiz_questions && lesson.quiz_questions.length > 0;
    
    // Для custom_lessons проверяем наличие контента
    const hasCustomContent = lesson.source === 'custom_lessons' && lesson.content;
    const hasCustomExercises = hasCustomContent && lesson.content.exercises?.length > 0;
    const hasCustomQuiz = hasCustomContent && lesson.content.quiz?.questions?.length > 0;
    const hasCustomChallenge = hasCustomContent && lesson.content.challenge?.daily_tasks?.length > 0;

    return (
      <div key={lesson.id} className="mb-6">
        <Card className="border border-gray-200 bg-white shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden">
          
          <CardHeader className="pb-4">
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-2 mb-3">
                  {lesson.source === 'custom_lessons' ? (
                    <Badge className="bg-blue-50 text-blue-700 border border-blue-200 px-3 py-1">
                      Новый урок
                    </Badge>
                  ) : (
                    <Badge className="bg-purple-50 text-purple-700 border border-purple-200 px-3 py-1">
                      Видео урок
                    </Badge>
                  )}
                  {lesson.points_required === 0 ? (
                    <Badge className="bg-green-50 text-green-700 border border-green-200 px-3 py-1">
                      Бесплатно
                    </Badge>
                  ) : (
                    <Badge className="bg-orange-50 text-orange-700 border border-orange-200 px-3 py-1">
                      {lesson.points_required} баллов
                    </Badge>
                  )}
                  {isCompleted && (
                    <Badge className="bg-green-100 text-green-800 px-3 py-1">
                      ✓ Завершен
                    </Badge>
                  )}
                </div>
                
                <CardTitle className="text-xl sm:text-2xl font-semibold text-gray-900 mb-2">
                  {lesson.title}
                </CardTitle>
                
                <CardDescription className="text-gray-600 text-sm sm:text-base leading-relaxed">
                  {lesson.description || 'Интерактивный урок нумерологии с теорией, упражнениями и практическими заданиями'}
                </CardDescription>
              </div>
              
              <div className="flex sm:flex-col items-center sm:items-end gap-2">
                <div className="p-3 bg-purple-50 rounded-xl border border-purple-100">
                  {hasVideo ? (
                    <Video className="w-6 h-6 text-purple-600" />
                  ) : (
                    <BookOpen className="w-6 h-6 text-purple-600" />
                  )}
                </div>
              </div>
            </div>
          </CardHeader>
          
          <CardContent className="pt-0 space-y-4">
            {/* Основная информация */}
            <div className="flex flex-wrap gap-3">
              <div className="flex items-center bg-gray-50 rounded-lg px-3 py-2 border border-gray-100">
                <Clock className="w-4 h-4 mr-2 text-gray-600" />
                <span className="text-sm text-gray-700">{lesson.duration_minutes || 30} минут</span>
              </div>
              {hasCustomContent && (
                <div className="flex items-center bg-gray-50 rounded-lg px-3 py-2 border border-gray-100">
                  <Brain className="w-4 h-4 mr-2 text-gray-600" />
                  <span className="text-sm text-gray-700">Интерактивный</span>
                </div>
              )}
              <div className="flex items-center bg-gray-50 rounded-lg px-3 py-2 border border-gray-100">
                <Target className="w-4 h-4 mr-2 text-gray-600" />
                <span className="text-sm text-gray-700">Уровень {lesson.level || 1}</span>
              </div>
            </div>

            {/* Что включено - КАК В ПЕРВОМ УРОКЕ */}
            <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
              <h4 className="font-medium mb-3 text-gray-900 flex items-center">
                <BookOpen className="w-4 h-4 mr-2 text-blue-600" />
                Что включено в урок:
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {hasCustomContent && lesson.content.theory && (
                  <div className="flex items-center">
                    <BookOpen className="w-4 h-4 mr-2 text-blue-600 flex-shrink-0" />
                    <span className="text-sm text-gray-700">Теоретическая часть</span>
                  </div>
                )}
                {hasCustomExercises && (
                  <div className="flex items-center">
                    <Brain className="w-4 h-4 mr-2 text-blue-600 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{lesson.content.exercises.length} интерактивных упражнений</span>
                  </div>
                )}
                {hasCustomQuiz && (
                  <div className="flex items-center">
                    <Target className="w-4 h-4 mr-2 text-blue-600 flex-shrink-0" />
                    <span className="text-sm text-gray-700">Тест на знания ({lesson.content.quiz.questions.length} вопросов)</span>
                  </div>
                )}
                {hasCustomChallenge && (
                  <div className="flex items-center">
                    <Calendar className="w-4 h-4 mr-2 text-blue-600 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{lesson.content.challenge.daily_tasks.length}-дневный челлендж</span>
                  </div>
                )}
                {(hasVideo || lesson.video_file_id) && (
                  <div className="flex items-center">
                    <Video className="w-4 h-4 mr-2 text-blue-600 flex-shrink-0" />
                    <span className="text-sm text-gray-700">Видеоматериалы</span>
                  </div>
                )}
                {(hasPDF || lesson.pdf_file_id) && (
                  <div className="flex items-center">
                    <FileText className="w-4 h-4 mr-2 text-blue-600 flex-shrink-0" />
                    <span className="text-sm text-gray-700">PDF справочники</span>
                  </div>
                )}

                {/* Добавляем элементы если контента нет */}
                {!hasCustomExercises && !hasCustomQuiz && !hasVideo && !lesson.video_file_id && (
                  <>
                    <div className="flex items-center">
                      <BookOpen className="w-4 h-4 mr-2 text-blue-600 flex-shrink-0" />
                      <span className="text-sm text-gray-700">Теория и объяснения</span>
                    </div>
                    <div className="flex items-center">
                      <Star className="w-4 h-4 mr-2 text-blue-600 flex-shrink-0" />
                      <span className="text-sm text-gray-700">Практические советы</span>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Прогресс урока (если есть) */}
            {lesson.watch_time > 0 && (
              <div className="mb-3">
                <div className="flex justify-between text-xs text-muted-foreground mb-1">
                  <span>Просмотрено</span>
                  <span>{lesson.watch_time}/{lesson.duration_minutes} мин</span>
                </div>
                <Progress 
                  value={(lesson.watch_time / lesson.duration_minutes) * 100} 
                  className="h-2"
                />
              </div>
            )}

            {/* Кнопка действия - КАК В ПЕРВОМ УРОКЕ */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
              <div className="text-sm text-gray-500 flex items-center">
                <Award className="w-4 h-4 mr-1 text-blue-500 flex-shrink-0" />
                <span>
                  {hasCustomContent ? 'Получите опыт по завершении' : 'Получите сертификат по завершении'}
                </span>
              </div>
              
              <div className="flex gap-2">
                <Button
                  size="lg"
                  variant={isCompleted ? "outline" : "default"}
                  disabled={isLocked}
                  onClick={() => {
                    // Для custom_lessons открываем специальный просмотрщик
                    if (lesson.source === 'custom_lessons') {
                      setSelectedLesson({...lesson, isCustomLesson: true});
                    } else {
                      setSelectedLesson(lesson);
                    }
                    setLessonCompleted(false);
                    setShowQuiz(false);
                  }}
                  className={`${!isCompleted && !isLocked ? "bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-2.5 rounded-lg shadow-sm hover:shadow-md transition-all duration-200" : ""} w-full sm:w-auto`}
                >
                  <PlayCircle className="w-5 h-5 mr-2" />
                  {isCompleted ? "Повторить урок" : isLocked ? "Заблокирован" : "Начать урок"}
                </Button>
                
                {/* Кнопка PDF материалов (если есть) */}
                {(lesson.pdf_file_id || hasPDF) && !isLocked && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setSelectedLesson({
                        ...lesson,
                        showPDFOnly: true,
                        pdfUrl: lesson.pdf_file_id ? 
                          `${backendUrl}/api/consultations/pdf/${lesson.pdf_file_id}` : 
                          lesson.pdf_url
                      });
                    }}
                    className="border-red-300 text-red-700 hover:bg-red-50"
                  >
                    <FileText className="w-4 h-4 mr-1" />
                    PDF
                  </Button>
                )}
                
                {/* Кнопка Word материалов - УНИФИЦИРОВАННАЯ ЛОГИКА */}
                {lesson.word_file_id && !isLocked && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setSelectedWord({
                        wordUrl: `${backendUrl}/api/lessons/word/${lesson.word_file_id}`,
                        title: `${lesson.title} - Word материалы урока`
                      });
                    }}
                    className="border-blue-300 text-blue-700 hover:bg-blue-50"
                  >
                    <FileText className="w-4 h-4 mr-1" />
                    Word
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderVideoPlayer = (lesson) => {
    const isYouTube = lesson.video_url && (lesson.video_url.includes('youtube.com') || lesson.video_url.includes('youtu.be'));
    const isVimeo = lesson.video_url && lesson.video_url.includes('vimeo.com');
    
    // Создаем полный URL для backend видео (ТОЧНО КАК В PERSONALCONSULTATIONS)
    const backendUrl = getBackendUrl();
    let videoUrl = lesson.video_url || 
      (lesson.video_file_id ? `${backendUrl}/api/consultations/video/${lesson.video_file_id}` : null);
    
    // Если это относительный путь к API, добавляем базовый URL
    if (videoUrl && videoUrl.startsWith('/api/')) {
      videoUrl = `${backendUrl}${videoUrl}`;
    } else if (videoUrl && videoUrl.startsWith('/video/')) {
      videoUrl = `${backendUrl}/api${videoUrl}`;
    }

    // Функция для определения типа видео
    const getVideoType = () => {
      if (isYouTube) return 'YouTube';
      if (isVimeo) return 'Vimeo';
      if (videoUrl && (videoUrl.includes('.mp4') || videoUrl.includes('.webm') || videoUrl.includes('.ogg'))) return 'Видео файл';
      return 'Видео';
    };
    
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <Card className="w-full max-w-4xl max-h-[90vh] overflow-hidden">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center">
                <PlayCircle className="w-5 h-5 mr-2" />
                {lesson.title}
                <Badge variant="secondary" className="ml-2 text-xs">
                  {getVideoType()}
                </Badge>
              </CardTitle>
              <Button variant="outline" onClick={() => setSelectedLesson(null)}>
                Закрыть
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="bg-black aspect-video flex items-center justify-center">
              {videoUrl ? (
                <>
                  {isYouTube || isVimeo ? (
                    <iframe
                      src={videoUrl}
                      className="w-full h-full"
                      allowFullScreen
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      title={lesson.title}
                    />
                  ) : (
                    <video
                      src={videoUrl}
                      controls
                      controlsList="nodownload"
                      disablePictureInPicture
                      className="w-full h-full object-contain"
                      playsInline
                      webkit-playsinline="true"
                      onError={(e) => {
                        console.error('Video loading error:', e);
                        console.log('Failed video URL:', videoUrl);
                        // Fallback to iframe if video tag fails
                        e.target.style.display = 'none';
                        const iframe = document.createElement('iframe');
                        iframe.src = videoUrl;
                        iframe.className = 'w-full h-full';
                        iframe.allowFullscreen = true;
                        iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
                        e.target.parentNode.appendChild(iframe);
                      }}
                    >
                      <p className="text-white text-center p-4">
                        Ваш браузер не поддерживает воспроизведение видео.{' '}
                        <a href={videoUrl} target="_blank" rel="noopener noreferrer" className="text-blue-400 underline">
                          Открыть видео в новой вкладке
                        </a>
                      </p>
                    </video>
                  )}
                </>
              ) : (
                <div className="text-white text-center">
                  <Video className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p className="text-lg">Видео будет доступно в ближайшее время</p>
                  <p className="text-sm opacity-75 mt-2">
                    Администратор загружает контент для этого урока
                  </p>
                </div>
              )}
            </div>
            
            <div className="p-6">
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    {lesson.description}
                  </p>
                  <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                    <span>Продолжительность: {lesson.duration_minutes} мин</span>
                    <span>Уровень: {lesson.level}</span>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <Button
                    onClick={() => setSelectedLesson(null)}
                    variant="outline"
                  >
                    Закрыть
                  </Button>
                  <Button
                    onClick={() => {
                      // Go to quiz after watching video
                      setSelectedLesson({...lesson, showQuiz: true});
                    }}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Пройти тест
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader className="w-6 h-6 animate-spin mr-2" />
          <span>Загружаем систему обучения...</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6 px-2 sm:px-0">
      {/* Header */}
      <Card className="numerology-gradient overflow-hidden">
        <CardHeader className="text-white p-4 sm:p-6">
          <CardTitle className="text-xl sm:text-2xl flex items-center">
            <BookOpen className="w-5 h-5 sm:w-6 sm:h-6 mr-2 flex-shrink-0" />
            <span>Система Обучения</span>
          </CardTitle>
          <CardDescription className="text-white/90 text-sm sm:text-base">
            Пошаговое изучение ведической нумерологии и духовного развития
          </CardDescription>
        </CardHeader>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Tabs for Lessons */}
      <Tabs defaultValue="lessons" className="space-y-6">
        <TabsList className="grid w-full grid-cols-1">
          <TabsTrigger value="lessons" className="flex items-center gap-2">
            <Video className="w-4 h-4" />
            Уроки
          </TabsTrigger>
        </TabsList>

        {/* Lessons Tab */}
        <TabsContent value="lessons">
          {learningData && !selectedLesson && (
            <>
              {/* Level Progress */}
              {renderLevelProgress()}

              {/* Learning Path */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Target className="w-5 h-5 mr-2" />
                    Путь Обучения
                  </CardTitle>
                  <CardDescription>
                    Последовательное изучение от базовых понятий до мастерства
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Все уроки в последовательном порядке: вводное → 1-9 → 0 */}
                    {learningData.available_lessons
                      .filter((lesson) => 
                        !lesson.title.includes('Test Lesson') && 
                        !lesson.title.includes('for Editor') &&
                        !lesson.description.toLowerCase().includes('testing') &&
                        !lesson.title.includes('unified_media_test') && // Исключаем технические тесты
                        !lesson.title.includes('media_test_lesson')
                      )
                      .map((lesson) => renderLessonCard(lesson))
                    }
                  </div>

                  {learningData.available_lessons.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                      <BookOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p className="text-lg">Уроки будут добавлены в ближайшее время</p>
                      <p className="text-sm">
                        Администратор готовит контент для вашего уровня обучения
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Level Rewards */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Award className="w-5 h-5 mr-2" />
                    Система Достижений
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                    {Array.from({ length: 10 }, (_, i) => {
                      const level = i + 1;
                      const isUnlocked = level <= learningData.user_level.current_level;
                      
                      return (
                        <div 
                          key={level}
                          className={`p-4 rounded-lg border-2 text-center transition-all ${
                            isUnlocked 
                              ? 'border-primary bg-primary/10' 
                              : 'border-muted bg-muted/20 opacity-50'
                          }`}
                          style={{ backgroundColor: isUnlocked ? getLevelColor(level) : undefined }}
                        >
                          <div className="flex items-center justify-center mb-2">
                            {isUnlocked ? (
                              <Star className="w-8 h-8 text-yellow-600" />
                            ) : (
                              <Lock className="w-8 h-8 text-gray-400" />
                            )}
                          </div>
                          <div className="font-bold text-sm">{getLevelName(level)}</div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {isUnlocked ? 'Достигнут' : `${level * 3} уроков`}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>

              {/* Create Sample Lessons Button (for demo) */}
              {learningData.available_lessons.length === 0 && (
                <Card>
                  <CardContent className="text-center py-8">
                    <BookOpen className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
                    <h3 className="text-lg font-semibold mb-2">Готовим Контент</h3>
                    <p className="text-muted-foreground mb-4">
                      Администратор загружает видеоуроки для вашего обучения
                    </p>
                    <Button 
                      onClick={async () => {
                        alert('Функция администратора для создания уроков');
                      }}
                      variant="outline"
                    >
                      <Video className="w-4 h-4 mr-2" />
                      Демо: Создать Примеры Уроков
                    </Button>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>
      </Tabs>

      {/* ПРОСМОТРЩИК CUSTOM LESSONS (интерактивные уроки) - UniversalLessonViewer */}
      {selectedLesson && selectedLesson.isCustomLesson && !selectedLesson.showPDFOnly && !showQuiz && (
        <div className="space-y-4">
          <Card>
            <CardHeader className="bg-gradient-to-r from-purple-50 to-indigo-50">
              <div className="flex justify-between items-center">
                <CardTitle className="flex items-center text-purple-900">
                  <BookOpen className="w-5 h-5 mr-2" />
                  {selectedLesson.title}
                </CardTitle>
                <Button
                  variant="outline"
                  onClick={() => setSelectedLesson(null)}
                  className="border-purple-300 text-purple-700 hover:bg-purple-50"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Список уроков
                </Button>
              </div>
            </CardHeader>
          </Card>
          <UniversalLessonViewer
            lessonId={selectedLesson.id}
            onBack={() => setSelectedLesson(null)}
          />
        </div>
      )}

      {/* Enhanced Video Player Modal - УНИФИЦИРОВАННАЯ ЛОГИКА КАК В КОНСУЛЬТАЦИЯХ */}
      {selectedLesson && !selectedLesson.showPDFOnly && !selectedLesson.isCustomLesson && !showQuiz && (
        <EnhancedVideoViewer
          videoUrl={
            // Приоритет: video_file_id (загруженный файл через consultations endpoint)
            selectedLesson.video_file_id 
              ? `${backendUrl}/api/consultations/video/${selectedLesson.video_file_id}`
              : selectedLesson.video_url
          }
          title={selectedLesson.title}
          description={selectedLesson.description}
          cost_credits={selectedLesson.points_for_lesson || 0}
          consultation={{
            id: selectedLesson.id,
            created_at: selectedLesson.created_at || new Date().toISOString(),
            subtitles_file_id: selectedLesson.subtitles_file_id,
            pdf_file_id: selectedLesson.pdf_file_id
          }}
          backendUrl={backendUrl}
          onClose={() => {
            if (!lessonCompleted) {
              setLessonCompleted(true);
            } else {
              setSelectedLesson(null);
              setLessonCompleted(false);
            }
          }}
        />
      )}

      {/* PDF Viewer Modal - УНИФИЦИРОВАННАЯ ЛОГИКА КАК В КОНСУЛЬТАЦИЯХ */}
      {selectedLesson && selectedLesson.showPDFOnly && (
        <ConsultationPDFViewer
          pdfUrl={
            // Используем consultations endpoint для PDF
            selectedLesson.pdfUrl || 
            (selectedLesson.pdf_file_id ? `${backendUrl}/api/consultations/pdf/${selectedLesson.pdf_file_id}` : '')
          }
          title={`${selectedLesson.title} - PDF материалы урока`}
          onClose={() => setSelectedLesson(null)}
        />
      )}

      {/* Word Viewer Modal */}
      {selectedWord && (
        <WordViewer
          wordUrl={selectedWord.wordUrl}
          title={selectedWord.title}
          backendUrl={backendUrl}
          onClose={() => setSelectedWord(null)}
        />
      )}

      {/* Lesson Complete Modal */}
      {selectedLesson && lessonCompleted && !showQuiz && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader className="text-center">
              <CardTitle className="flex items-center justify-center text-green-600">
                <CheckCircle className="w-6 h-6 mr-2" />
                Урок просмотрен!
              </CardTitle>
            </CardHeader>
            <CardContent className="text-center space-y-4">
              <p>Отлично! Теперь пройдите тест для закрепления материала.</p>
              
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={() => {
                    setSelectedLesson(null);
                    setLessonCompleted(false);
                  }}
                  className="flex-1"
                >
                  Закрыть
                </Button>
                <Button
                  onClick={async () => {
                    await generateQuizFromVideo(selectedLesson);
                    setShowQuiz(true);
                  }}
                  disabled={generatingQuiz}
                  className="flex-1 numerology-gradient"
                >
                  {generatingQuiz ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin mr-2" />
                      Создаем тест...
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4 mr-2" />
                      Пройти тест
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Quiz Modal */}
      {showQuiz && quizData && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-4xl max-h-[90vh] overflow-auto">
            <Quiz
              questions={quizData.questions}
              title={`Тест: ${quizData.lesson_title}`}
              onComplete={handleQuizComplete}
              onClose={() => {
                setShowQuiz(false);
                setSelectedLesson(null);
                setLessonCompleted(false);
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default LearningSystem;