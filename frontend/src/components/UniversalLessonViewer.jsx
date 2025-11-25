/**
 * UNIVERSAL LESSON VIEWER
 * Универсальный просмотрщик уроков для всех типов уроков
 *
 * Этот компонент отображает урок с теорией, упражнениями, тестами,
 * челленджами и трекером привычек. Поддерживает как первый урок,
 * так и кастомные уроки из админ-панели.
 */

import React, { useState, useEffect, useMemo, Fragment } from 'react';

// UI компоненты для интерфейса
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Checkbox } from './ui/checkbox';

// Иконки для визуального оформления
import {
  BookOpen, PlayCircle, CheckCircle, Clock, Target, Zap,
  Star, Calendar, Award, ArrowRight, ArrowLeft,
  Sparkles, Sun, Moon, Loader, Trophy, Heart,
  Brain, Lightbulb, FileText, Timer, Rocket, Eye, Download, Video, Lock, File,
  Scroll, Info, Compass
} from 'lucide-react';

// Хуки и контекст
import { useAuth } from './AuthContext';

// Дополнительные компоненты для просмотра медиа
import EnhancedVideoViewer from './EnhancedVideoViewer';
import LessonDocumentViewer from './LessonDocumentViewer';
import PushNotificationSettings from './PushNotificationSettings';
import BunnyVideoPlayer from './BunnyVideoPlayer';

// Утилиты
import { getBackendUrl } from '../utils/backendUrl';

const UniversalLessonViewer = ({ lessonId, onBack }) => {
  console.log('🚀 UniversalLessonViewer запущен с lessonId:', lessonId);

  // Получаем данные пользователя из контекста аутентификации
  const { user } = useAuth();
  const backendUrl = getBackendUrl();

  // ==================== ОСНОВНЫЕ СОСТОЯНИЯ УРОКА ====================

  // Данные урока, загруженные с сервера
  const [lessonData, setLessonData] = useState(null);
  // Состояние загрузки данных урока
  const [loading, setLoading] = useState(true);
  // Сообщение об ошибке при загрузке
  const [error, setError] = useState('');

  // Активная вкладка (теория, упражнения, тест и т.д.)
  // Восстанавливается из localStorage для сохранения позиции пользователя
  const [activeSection, setActiveSection] = useState(() => {
    return localStorage.getItem(`lesson_${lessonId}_activeSection`) || 'theory';
  });

  // Множество завершенных секций урока
  const [completedSections, setCompletedSections] = useState(new Set());
  // Общий прогресс прохождения урока (в процентах)
  const [overallProgress, setOverallProgress] = useState(0);
  
  // ==================== СОСТОЯНИЯ ДЛЯ КВИЗА ====================

  // Ответы пользователя на вопросы теста (ключ - ID вопроса, значение - ответ)
  const [quizAnswers, setQuizAnswers] = useState({});
  // Результаты прохождения теста после отправки
  const [quizResults, setQuizResults] = useState(null);
  // Флаг отправки теста на сервер
  const [quizSubmitting, setQuizSubmitting] = useState(false);

  // ==================== СОСТОЯНИЯ ДЛЯ ЧЕЛЛЕНДЖА ====================

  // Прогресс выполнения челленджа (дни, задачи и т.д.)
  const [challengeProgress, setChallengeProgress] = useState(null);
  // Флаг, запущен ли челлендж пользователем
  const [challengeStarted, setChallengeStarted] = useState(false);
  // Выбранный день челленджа для просмотра/редактирования
  const [selectedChallengeDay, setSelectedChallengeDay] = useState(1);
  // Флаг завершения всего челленджа
  const [challengeCompleted, setChallengeCompleted] = useState(false);
  // Оценка пользователя челленджу (1-5 звезд)
  const [challengeRating, setChallengeRating] = useState(0);
  // Заметки пользователя о прошедшем дне челленджа
  const [challengeDayNotes, setChallengeDayNotes] = useState('');

  // ==================== СОСТОЯНИЯ ДЛЯ ТРЕКЕРА ПРИВЫЧЕК ====================

  // Конфигурация трекера привычек для урока
  const [habitTracker, setHabitTracker] = useState(null);
  // Состояние привычек на сегодня (выполнено/не выполнено)
  const [todayHabits, setTodayHabits] = useState({});
  // Прогресс выполнения привычек за день (в процентах)
  const [habitProgress, setHabitProgress] = useState(0);
  // Количество дней подряд без пропусков
  const [habitStreakDays, setHabitStreakDays] = useState(0);

  // ==================== СОСТОЯНИЯ ДЛЯ УПРАЖНЕНИЙ ====================

  // Ответы пользователя на упражнения (ключ - ID упражнения, значение - ответ)
  const [exerciseResponses, setExerciseResponses] = useState({});
  // Множество завершенных упражнений
  const [completedExercises, setCompletedExercises] = useState(new Set());
  // Множество упражнений, ответы на которые сохранены локально
  const [savedExercises, setSavedExercises] = useState(new Set());
  
  // ==================== СОСТОЯНИЯ ДЛЯ МЕДИАФАЙЛОВ ====================

  // Информация о загруженных файлах урока (видео, PDF, Word)
  const [uploadedLessonFiles, setUploadedLessonFiles] = useState({
    video: null,
    pdf: null,
    word: null
  });

  // ==================== СОСТОЯНИЯ ДЛЯ МОДАЛЬНЫХ ОКОН ====================

  // Выбранное видео для просмотра в модальном окне
  const [selectedVideo, setSelectedVideo] = useState(null);
  // Выбранный документ для просмотра в модальном окне
  const [selectedDocument, setSelectedDocument] = useState(null);

  // ==================== СОСТОЯНИЯ ДЛЯ ДОПОЛНИТЕЛЬНЫХ МАТЕРИАЛОВ ====================

  // Список дополнительных PDF файлов урока
  const [additionalPdfs, setAdditionalPdfs] = useState([]);
  // Список всех ресурсов урока (PDF, Word, Excel и др.)
  const [lessonResources, setLessonResources] = useState([]);
  // Список дополнительных видео файлов
  const [additionalVideos, setAdditionalVideos] = useState([]);

  // ==================== СОСТОЯНИЯ ДЛЯ НАВИГАЦИИ МАТЕРИАЛОВ ====================

  // Фильтр материалов: 'all' (все), 'videos' (видео), 'pdfs' (PDF)
  const [materialsFilter, setMaterialsFilter] = useState('all');
  // Поисковый запрос для фильтрации материалов
  const [materialsSearch, setMaterialsSearch] = useState('');
  // Сортировка материалов: 'recent' (по дате), 'name' (по имени), 'type' (по типу)
  const [materialsSortBy, setMaterialsSortBy] = useState('recent');

  // ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

  /**
   * Определяет формат документа по его метаданным
   * Используется для правильного отображения иконок и фильтрации
   */
  const determineDocumentFormat = (item) => {
    if (!item) return 'other';
    const contentType = (item.content_type || item.contentType || '').toLowerCase();
    const filename = (item.filename || item.title || '').toLowerCase();
    const extension = (item.file_extension || '').toLowerCase();

    const byExtension = (value) => {
      if (!value) return null;
      if (value.endsWith('.pdf')) return 'pdf';
      if (value.endsWith('.docx') || value.endsWith('.doc')) return 'word';
      if (value.endsWith('.xlsx') || value.endsWith('.xls')) return 'excel';
      if (value.endsWith('.pptx') || value.endsWith('.ppt')) return 'presentation';
      if (value.endsWith('.txt') || value.endsWith('.csv')) return 'text';
      return null;
    };

    const byContentType = () => {
      if (contentType.includes('pdf')) return 'pdf';
      if (contentType.includes('word')) return 'word';
      if (contentType.includes('excel') || contentType.includes('spreadsheet')) return 'excel';
      if (contentType.includes('presentation') || contentType.includes('powerpoint')) return 'presentation';
      if (contentType.includes('text') || contentType.includes('csv') || contentType.includes('plain')) return 'text';
      return null;
    };

    return (
      byExtension(extension) ||
      byExtension(filename) ||
      byContentType() ||
      'other'
    );
  };

  // ==================== ЭФФЕКТЫ ЗАГРУЗКИ ДАННЫХ ====================

  /**
   * Эффект для загрузки урока при изменении lessonId
   * Сбрасывает все состояния и загружает новые данные
   */
  useEffect(() => {
    // Сбросить все состояния при смене урока
    setLessonData(null);
    setLoading(true);
    setError('');
    setCompletedSections(new Set());
    setOverallProgress(0);
    setQuizAnswers({});
    setQuizResults(null);
    setChallengeProgress(null);
    setChallengeStarted(false);
    setSelectedChallengeDay(1);
    setChallengeCompleted(false);
    setChallengeRating(0);
    setChallengeDayNotes('');
    setHabitTracker(null);
    setTodayHabits({});
    setHabitProgress(0);
    setHabitStreakDays(0);
    setExerciseResponses({});
    setCompletedExercises(new Set());
    setSavedExercises(new Set());
    setAdditionalPdfs([]);
    setLessonResources([]);
    setAdditionalVideos([]);
    setSelectedVideo(null);
    setSelectedDocument(null);

    // Загрузить новый урок
    loadLesson();
  }, [lessonId]); // Перезагружать урок при изменении lessonId

  /**
   * Эффект для загрузки медиафайлов после успешной загрузки данных урока
   */
  useEffect(() => {
    if (lessonData) {
      loadUploadedLessonFiles();
      loadAdditionalPdfs();
      loadAdditionalVideos();
      loadLessonResources();
    }
  }, [lessonData]); // Перезагружать медиафайлы при изменении lessonData

  /**
   * Эффект для сохранения активной секции в localStorage
   * Позволяет пользователю вернуться к той же вкладке при следующем посещении урока
   */
  useEffect(() => {
    localStorage.setItem(`lesson_${lessonId}_activeSection`, activeSection);
  }, [activeSection]);

  // Автоматический пересчет прогресса при изменении completedSections
  useEffect(() => {
    calculateOverallProgress();
  }, [completedSections, completedExercises, challengeStarted, habitTracker]);

  // Автоматическое завершение упражнений когда все выполнены
  useEffect(() => {
    if (lessonData?.content?.exercises?.length > 0 &&
        completedExercises.size === lessonData.content.exercises.length &&
        !completedSections.has('exercises')) {
      setCompletedSections(prev => new Set([...prev, 'exercises']));
    }
  }, [completedExercises, lessonData]);

  // Пересчитывать прогресс привычек при изменении todayHabits или habitTracker
  useEffect(() => {
    calculateHabitProgress();
  }, [todayHabits, habitTracker]);

  // Функция расчета общего прогресса урока
  const calculateOverallProgress = () => {
    if (!lessonData?.content) return;

    // Определяем доступные секции первого урока
    const availableSections = [];

    // 1. Теория (проверяем и обычную theory, и custom_theory_blocks)
    if (lessonData.content.theory || lessonData.content.custom_theory_blocks?.blocks?.length > 0) {
      availableSections.push({
        name: 'theory',
        completed: completedSections.has('theory')
      });
    }

    // 2. Упражнения
    const exercises = lessonData.exercises || lessonData.content?.exercises || [];
    if (exercises.length > 0) {
      availableSections.push({
        name: 'exercises',
        completed: completedExercises.size === exercises.length
      });
    }

    // 3. Квиз
    // Проверяем квиз в content.quiz (для обычных уроков) или на верхнем уровне (для первого урока)
    const quizQuestions = lessonData.content?.quiz?.questions || lessonData.quiz?.questions || [];
    if (quizQuestions.length > 0) {
      availableSections.push({
        name: 'quiz',
        completed: completedSections.has('quiz')
      });
    }

    // 4. Челлендж (всегда учитываем если есть)
    // Проверяем челлендж в content.challenge или на верхнем уровне
    const challengeTasks = lessonData.content?.challenge?.daily_tasks || lessonData.challenges?.[0]?.daily_tasks || [];
    if (challengeTasks.length > 0) {
      availableSections.push({
        name: 'challenge',
        completed: challengeStarted
      });
    }

    // 5. Привычки (учитываем только если трекер создан)
    if (habitTracker) {
      availableSections.push({
        name: 'habits',
        completed: completedSections.has('habits')
      });
    }

    const totalSections = availableSections.length;
    const completedCount = availableSections.filter(s => s.completed).length;

    // Вычисляем процент
    const progress = totalSections > 0 ? Math.round((completedCount / totalSections) * 100) : 0;
    setOverallProgress(progress);
  };

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
const documentMaterials = filteredMaterials.filter(m => m.type === 'document');
const totalVideosCount = additionalVideos.length;
const totalDocumentsCount = additionalPdfs.length + lessonResources.length;

  // Загрузка загруженных файлов урока (дополнительные материалы)
  // ОСНОВНЫЕ МЕДИАФАЙЛЫ (video_file_id, pdf_file_id) ЗАГРУЖАЮТСЯ ПРЯМО В lessonData
  // Эта функция загружает только дополнительные материалы
  const loadUploadedLessonFiles = async () => {
    if (!lessonData) return;
    
    try {
      const token = localStorage.getItem('token');
      
      // Используем endpoint для получения дополнительных медиа-файлов урока
      const response = await fetch(`${backendUrl}/api/lessons/media/${lessonId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Получаем дополнительные видео и PDF файлы
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
          } : null,
          word: null // Word файлы загружаются только через lessonData
        });
      } else {
        console.log('Дополнительные медиа-файлы для урока не найдены');
        setUploadedLessonFiles({ 
          video: null, 
          pdf: null,
          word: null
        });
      }
    } catch (error) {
      console.error('Ошибка загрузки дополнительных медиа-файлов урока:', error);
      setUploadedLessonFiles({ 
        video: null, 
        pdf: null,
        word: null
      });
    }
  };

  // Загрузка дополнительных PDF файлов урока
  const loadAdditionalPdfs = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!lessonId) return;
      const response = await fetch(`${backendUrl}/api/lessons/${lessonId}/additional-pdfs`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        const pdfs = (data.additional_pdfs || []).map((pdf) => ({
          ...pdf,
          type: 'document',
          origin: 'pdf',
          format: 'pdf',
          resource_url: pdf.pdf_url,
          searchText: (pdf.title || pdf.filename || '').toLowerCase(),
          date: pdf.uploaded_at || new Date().toISOString()
        }));
        setAdditionalPdfs(pdfs);
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
      if (!lessonId) return;
      const response = await fetch(`${backendUrl}/api/lessons/${lessonId}/additional-videos`, {
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

  // ==================== ЗАГРУЗКА ДАННЫХ УРОКА ====================

  /**
   * Загружает данные урока с сервера
   * Поддерживает как первый урок (lesson_numerom_intro), так и кастомные уроки из админ-панели
   */
  const loadLesson = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      // Определяем endpoint в зависимости от типа урока
      // Первый урок имеет специальный endpoint для обратной совместимости
      const endpoint = lessonId === 'lesson_numerom_intro'
        ? `${backendUrl}/api/lessons/first-lesson`
        : `${backendUrl}/api/lessons/${lessonId}`;

      console.log(`📚 Загружаем урок: ${lessonId} с endpoint: ${endpoint}`);

      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('📚 Урок загружен:', data.lesson?.id);
      console.log('📖 Content:', data.lesson?.content ? 'есть' : 'нет');
      console.log('🔧 Source:', data.lesson?.source);
      console.log('📖 Theory:', data.lesson?.content?.theory ? 'есть' : 'нет');
      if (data.lesson?.content?.theory) {
        console.log('📖 Поля theory:', Object.keys(data.lesson.content.theory));
      }
      console.log('📖 Custom theory blocks:', data.lesson?.content?.custom_theory_blocks ? 'есть' : 'нет');
      if (data.lesson?.content?.custom_theory_blocks?.blocks) {
        console.log('📖 Блоков теории:', data.lesson.content.custom_theory_blocks.blocks.length);
      }
      console.log('💪 Exercises:', data.lesson?.exercises?.length || 0);
      console.log('❓ Quiz:', data.lesson?.content?.quiz ? 'есть' : 'нет');
      console.log('🏆 Challenge:', data.lesson?.content?.challenge ? 'есть' : 'нет');
      setLessonData(data.lesson);

      // Загрузить прогресс пользователя если есть (передаем lesson для получения challenge/quiz ID)
      await loadUserProgress(data.lesson);

    } catch (err) {
      console.error(`Ошибка загрузки урока ${lessonId}:`, err);
      setError('Не удалось загрузить урок. Попробуйте обновить страницу.');
    } finally {
      setLoading(false);
    }
  };

  // Загрузка прогресса пользователя
  const loadUserProgress = async (lesson) => {
    try {
      const token = localStorage.getItem('token');

      // Загрузить общий прогресс урока
      const overallResponse = await fetch(
        `${backendUrl}/api/lessons/overall-progress/${lessonId}`,
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
        `${backendUrl}/api/lessons/exercise-responses/${lessonId}`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );

      if (exerciseResponse.ok) {
        const exerciseData = await exerciseResponse.json();
        setExerciseResponses(exerciseData.responses || {});
        setSavedExercises(new Set(Object.keys(exerciseData.responses || {})));
      }

      // Загрузить прогресс челленджа (получаем challenge ID из данных урока)
      const challengeId = lesson?.content?.challenge?.id;
      if (challengeId) {
        const challengeResponse = await fetch(
          `${backendUrl}/api/lessons/challenge-progress/${challengeId}`,
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

      // Загрузить трекер привычек
      const habitTrackerResponse = await fetch(
        `${backendUrl}/api/lessons/habit-tracker/${lessonId}`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );

      if (habitTrackerResponse.ok) {
        const habitTrackerData = await habitTrackerResponse.json();
        if (habitTrackerData.tracker) {
          setHabitTracker(habitTrackerData.tracker);

          // Инициализировать сегодняшние привычки
          const today = new Date().toISOString().split('T')[0];
          const todayCompletions = habitTrackerData.tracker.daily_completions?.[today] || {};

          // Преобразовать в формат для UI
          const todayHabitsStatus = {};
          habitTrackerData.tracker.active_habits?.forEach(habit => {
            todayHabitsStatus[habit] = todayCompletions[habit]?.completed || false;
          });

          setTodayHabits(todayHabitsStatus);
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
      formData.append('lesson_id', lessonId);
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

      // Автоматически переключаемся на вкладку привычек
      setTimeout(() => {
        setActiveSection('habits');
      }, 1000);

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

      // Очистить поле впечатлений
      setChallengeDayNotes('');

      // Автоматически переключиться на следующий день (без задержки)
      if (day < 7) {
        setSelectedChallengeDay(day + 1);
      }

    } catch (err) {
      console.error('Ошибка завершения дня челленджа:', err);
      setError('Не удалось отметить день. Попробуйте еще раз.');
    }
  };

  // Начать челлендж заново
  const restartChallenge = () => {
    setChallengeProgress({
      challenge_id: 'challenge_sun_7days',
      start_date: new Date().toISOString(),
      current_day: 1,
      completed_days: [],
      status: 'active'
    });
    setSelectedChallengeDay(1);
    setChallengeDayNotes('');
    setChallengeCompleted(false);
  };

  // Добавить трекер привычек
  const addHabitTracker = async () => {
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('lesson_id', lessonId);

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
      formData.append('lesson_id', lessonId);
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
        // useEffect автоматически пересчитает прогресс при изменении todayHabits
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

  // Получить данные квиза и челленджа (работают с обоими форматами)
  const quizData = lessonData?.content?.quiz || lessonData?.quiz || {};
  const challengeData = lessonData?.content?.challenge || lessonData?.challenges?.[0] || {};

  // Отправить квиз
  const submitQuiz = async () => {
    const totalQuestions = quizData.questions?.length || 0;
    if (Object.keys(quizAnswers).length < totalQuestions) {
      setError('Пожалуйста, ответьте на все вопросы');
      return;
    }

    try {
      setQuizSubmitting(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();
      const quizId = quizData.id || 'quiz_intro_1';
      formData.append('quiz_id', quizId);
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

        // Автоматически переключаемся на следующую вкладку - челлендж
        setTimeout(() => {
          setActiveSection('challenge');
        }, 2000); // Даем время посмотреть результаты квиза
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
    // Автоматически переключаемся на следующую вкладку - упражнения
    setActiveSection('exercises');
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
          <Button onClick={() => {
            resetQuiz();
            setActiveSection('quiz');
          }} variant="outline">
            Попробовать снова
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!lessonData) {
    console.log('⚠️ lessonData отсутствует, показываем сообщение об ошибке');
    console.log('🔍 Состояние:', { loading, error, lessonId });
    return (
      <Card>
        <CardContent className="text-center py-8">
          <BookOpen className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
          <p>Урок не найден</p>
          <p className="text-sm text-gray-500 mt-2">ID: {lessonId}</p>
        </CardContent>
      </Card>
    );
  }

  console.log('✅ Рендерим урок:', lessonData.id);

  const sectionProgress = [
    { id: 'theory', title: 'Теория', icon: <BookOpen className="w-4 h-4" />, completed: completedSections.has('theory') },
    { id: 'exercises', title: 'Упражнения', icon: <Brain className="w-4 h-4" />, completed: completedSections.has('exercises') },
    { id: 'quiz', title: 'Тест', icon: <Target className="w-4 h-4" />, completed: completedSections.has('quiz') },
    { id: 'challenge', title: 'Челлендж', icon: <Zap className="w-4 h-4" />, completed: challengeStarted },
    { id: 'habits', title: 'Привычки', icon: <Star className="w-4 h-4" />, completed: habitTracker !== null }
  ];

  /**
   * Основная функция рендеринга компонента UniversalLessonViewer
   * Отображает урок с вкладками: теория, упражнения, тест, челлендж, привычки
   */
  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* ==================== ЗАГОЛОВОК УРОКА ==================== */}
      <div className="relative overflow-hidden">
        <Card className="border border-gray-200 bg-white shadow-sm">          
          <CardHeader className="p-6 border-b border-gray-100">
            {/* Медиафайлы урока - ПЕРЕМЕЩЕНЫ В САМЫЙ ВЕРХ */}
            {(lessonData?.video_file_id || lessonData?.pdf_file_id || lessonData?.word_file_id || lessonData?.video_url) && (
              <div className="mb-6 pb-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Video className="w-5 h-5 text-blue-600" />
                  Медиафайлы урока
                </h3>
                <div className="flex flex-wrap gap-3">
                  {/* Кнопка видео - УНИФИЦИРОВАННАЯ ЛОГИКА КАК В КОНСУЛЬТАЦИЯХ */}
                  {(lessonData?.video_file_id || lessonData?.video_url) && (
                    <Button
                      onClick={() => {
                        // Приоритет: video_file_id (загруженный файл через consultations endpoint)
                        const videoUrl = lessonData.video_file_id 
                          ? `${backendUrl}/api/consultations/video/${lessonData.video_file_id}`
                          : lessonData.video_url;
                        setSelectedVideo({
                          url: videoUrl,
                          title: lessonData.title,
                          description: lessonData.description || 'Видео урока'
                        });
                      }}
                      className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-medium px-6 py-3 rounded-lg shadow-md hover:shadow-lg transition-all"
                    >
                      <PlayCircle className="w-5 h-5 mr-2" />
                      Смотреть видео
                    </Button>
                  )}

                  {/* Кнопка PDF - ТОЧНО КАК В КОНСУЛЬТАЦИЯХ */}
                  {lessonData?.pdf_file_id && (
                    <div className="flex gap-2">
                      <Button
                        onClick={() => {
                          // Используем consultations endpoint для PDF (как в консультациях)
                          const pdfUrl = `${backendUrl}/api/consultations/pdf/${lessonData.pdf_file_id}`;
                          setSelectedDocument({
                            url: pdfUrl,
                            title: `${lessonData.title} - PDF материалы`
                          });
                        }}
                        variant="outline"
                        className="border-red-300 text-red-700 hover:bg-red-50 font-medium px-6 py-3 rounded-lg shadow-md hover:shadow-lg transition-all"
                      >
                        <Eye className="w-5 h-5 mr-2" />
                        Просмотреть
                      </Button>
                      <Button
                        onClick={() => {
                          const link = document.createElement('a');
                          link.href = `${backendUrl}/api/consultations/pdf/${lessonData.pdf_file_id}`;
                          link.download = `lesson-${lessonData.id}.pdf`;
                          link.click();
                        }}
                        variant="outline"
                        className="border-red-300 text-red-700 hover:bg-red-50 font-medium px-6 py-3 rounded-lg shadow-md hover:shadow-lg transition-all"
                      >
                        <Download className="w-5 h-5 mr-2" />
                        Скачать
                      </Button>
                    </div>
                  )}

                  {/* Кнопка Word */}
                  {lessonData?.word_file_id && (
                    <Button
                      onClick={() => {
                        const wordUrl = `${backendUrl}/api/lessons/word/${lessonData.word_file_id}`;
                        setSelectedDocument({
                          url: wordUrl,
                          title: `${lessonData.title} - Word материалы`
                        });
                      }}
                      variant="outline"
                      className="border-blue-300 text-blue-700 hover:bg-blue-50 font-medium px-6 py-3 rounded-lg shadow-md hover:shadow-lg transition-all"
                    >
                      <File className="w-5 h-5 mr-2" />
                      Открыть Word
                    </Button>
                  )}
                </div>
              </div>
            )}

            {/* Заголовок урока */}
            <div className="flex items-center gap-4 mb-6">
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

            {/* Бейджи и информация - по центру */}
            <div className="flex flex-col items-center gap-4">
              <div className="flex flex-wrap items-center justify-center gap-3">
                <Badge className="bg-green-50 text-green-700 border border-green-200 font-medium px-4 py-2 rounded-full">
                  🎁 Бесплатный урок
                </Badge>
                <Badge className="bg-gray-50 text-gray-700 border border-gray-200 px-3 py-1">
                  Модуль 1 • Базовый уровень
                </Badge>
              </div>
              <div className="flex items-center justify-center gap-4 text-sm text-gray-600">
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
              </TabsTrigger>
            ))}
          </TabsList>
        </div>

        {/* ==================== КОНТЕНТ ВКЛАДОК ==================== */}

        {/* ТЕОРИЯ - динамическое отображение с кастомными заголовками */}
        {/* Поддерживает как первый урок, так и кастомные блоки теории */}
        <TabsContent value="theory" className="space-y-6">
          {/* Определяем является ли это первым уроком */}
          {(() => {
            if (!lessonData || !lessonData.content) {
              return (
                <Card>
                  <CardContent className="text-center py-8 text-muted-foreground">
                    <Loader className="w-6 h-6 animate-spin mx-auto mb-2" />
                    <p>Загрузка контента урока...</p>
                  </CardContent>
                </Card>
              );
            }

            const isFirstLesson = lessonId === 'lesson_numerom_intro';

            // Получаем список скрытых полей
            let hiddenFields = new Set();
            const hiddenFieldsData = lessonData.content?.hidden_theory_fields?.fields;
            if (hiddenFieldsData) {
              try {
                const parsed = typeof hiddenFieldsData === 'string' ? JSON.parse(hiddenFieldsData) : hiddenFieldsData;
                hiddenFields = new Set(Array.isArray(parsed) ? parsed : []);
              } catch (e) {
                console.error('Error parsing hidden_theory_fields:', e);
              }
            }

            if (isFirstLesson) {
              // Блоки для первого урока
              console.log('🎯 Отображение ПЕРВОГО урока');
              return (
                <>
                  {!hiddenFields.has('what_is_numerology') && lessonData.content?.theory?.what_is_numerology && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <BookOpen className="w-5 h-5 mr-2" />
                          {lessonData.content.theory_labels?.what_is_numerology_label || 'Что такое нумерология?'}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="prose max-w-none">
                        <div className="text-gray-700 leading-relaxed text-base whitespace-pre-wrap">
                          {lessonData.content.theory.what_is_numerology}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {!hiddenFields.has('cosmic_ship_story') && lessonData.content?.theory?.cosmic_ship_story && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <Rocket className="w-5 h-5 mr-2" />
                          {lessonData.content.theory_labels?.cosmic_ship_story_label || 'История космического корабля'}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="prose max-w-none">
                        <div className="text-gray-700 leading-relaxed text-base whitespace-pre-wrap">
                          {lessonData.content.theory.cosmic_ship_story}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {!hiddenFields.has('planets_and_numbers') && lessonData.content?.theory?.planets_and_numbers && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <BookOpen className="w-5 h-5 mr-2" />
                          {lessonData.content.theory_labels?.planets_and_numbers_label || 'Соответствие планет и чисел'}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="prose max-w-none">
                        <div className="text-gray-700 leading-relaxed text-base whitespace-pre-wrap">
                          {lessonData.content.theory.planets_and_numbers}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </>
              );
            } else {
              // Блоки для других уроков
              // Отладочная информация
              console.log('🎯 Отображение ОБЫЧНОГО урока:', {
                lessonId,
                isFirstLesson,
                hasTheory: !!lessonData?.content?.theory,
                theoryKeys: lessonData?.content?.theory ? Object.keys(lessonData.content.theory) : [],
                lessonDataKeys: lessonData ? Object.keys(lessonData) : []
              });
              return (
                <>
                  {!hiddenFields.has('what_is_topic') && lessonData.content?.theory?.what_is_topic && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <BookOpen className="w-5 h-5 mr-2" />
                          {lessonData.content.theory_labels?.what_is_topic_label || 'Что изучаем в этом уроке?'}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="prose max-w-none">
                        <div className="text-gray-700 leading-relaxed text-base whitespace-pre-wrap">
                          {lessonData.content.theory.what_is_topic}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {!hiddenFields.has('main_story') && lessonData.content?.theory?.main_story && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <BookOpen className="w-5 h-5 mr-2" />
                          {lessonData.content.theory_labels?.main_story_label || 'Основная история/объяснение'}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="prose max-w-none">
                        <div className="text-gray-700 leading-relaxed text-base whitespace-pre-wrap">
                          {lessonData.content.theory.main_story}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {!hiddenFields.has('key_concepts') && lessonData.content?.theory?.key_concepts && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <Lightbulb className="w-5 h-5 mr-2" />
                          {lessonData.content.theory_labels?.key_concepts_label || 'Ключевые концепции'}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="prose max-w-none">
                        <div className="text-gray-700 leading-relaxed text-base whitespace-pre-wrap">
                          {lessonData.content.theory.key_concepts}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {!hiddenFields.has('practical_applications') && lessonData.content?.theory?.practical_applications && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <Sparkles className="w-5 h-5 mr-2" />
                          {lessonData.content.theory_labels?.practical_applications_label || 'Практическое применение'}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="prose max-w-none">
                        <div className="text-gray-700 leading-relaxed text-base whitespace-pre-wrap">
                          {lessonData.content.theory.practical_applications}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Динамическое отображение всех остальных блоков теории */}
                  {(() => {
                    const theoryKeys = Object.keys(lessonData.content?.theory || {}).filter(key =>
                      !['full_text', 'what_is_topic', 'main_story', 'key_concepts', 'practical_applications'].includes(key) &&
                      lessonData.content.theory[key] &&
                      typeof lessonData.content.theory[key] === 'string' &&
                      lessonData.content.theory[key].trim().length > 0
                    );

                    console.log('🎯 ДИНАМИЧЕСКИЕ БЛОКИ ТЕОРИИ:', {
                      allKeys: Object.keys(lessonData.content?.theory || {}),
                      filteredKeys: theoryKeys,
                      theoryData: lessonData.content?.theory
                    });

                    // ВРЕМЕННЫЙ КОД ДЛЯ ОТОБРАЖЕНИЯ ВСЕХ БЛОКОВ ТЕОРИИ
                    if (theoryKeys.length === 0) {
                      console.warn('⚠️ НЕТ ДИНАМИЧЕСКИХ БЛОКОВ ТЕОРИИ! Показываем все доступные блоки:');
                      const allTheoryKeys = Object.keys(lessonData.content?.theory || {}).filter(key => key !== 'full_text');
                      console.log('Все блоки теории:', allTheoryKeys);

                      return allTheoryKeys.map((key) => {
                        const displayName = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        return (
                          <Card key={key}>
                            <CardHeader>
                              <CardTitle className="flex items-center">
                                <BookOpen className="w-5 h-5 mr-2" />
                                {displayName} (ОТЛАДКА)
                              </CardTitle>
                            </CardHeader>
                            <CardContent className="prose max-w-none">
                              <div className="text-gray-700 leading-relaxed text-base whitespace-pre-wrap">
                                {lessonData.content.theory[key] || 'БЛОК ПУСТОЙ ИЛИ НЕ НАЙДЕН'}
                              </div>
                            </CardContent>
                          </Card>
                        );
                      });
                    }

                    return theoryKeys.map((key) => {
                      // Преобразуем ключ в читаемое название
                      const displayName = key
                        .replace(/_/g, ' ')
                        .replace(/\b\w/g, l => l.toUpperCase())
                        .replace(/O/g, 'о')
                        .replace(/A/g, 'а')
                        .replace(/И/g, 'и')
                        .replace(/В/g, 'в')
                        .replace(/С/g, 'с')
                        .replace(/У/g, 'у')
                        .replace(/П/g, 'п')
                        .replace(/К/g, 'к')
                        .replace(/Н/g, 'н')
                        .replace(/М/g, 'м')
                        .replace(/Д/g, 'д')
                        .replace(/Т/g, 'т')
                        .replace(/Р/g, 'р')
                        .replace(/Е/g, 'е')
                        .replace(/Й/g, 'й')
                        .replace(/Г/g, 'г')
                        .replace(/Ш/g, 'ш')
                        .replace(/Щ/g, 'щ')
                        .replace(/З/g, 'з')
                        .replace(/Х/g, 'х')
                        .replace(/Ъ/g, 'ъ')
                        .replace(/Ь/g, 'ь')
                        .replace(/Ю/g, 'ю')
                        .replace(/Я/g, 'я');

                      // Выбираем подходящую иконку в зависимости от типа блока
                      let IconComponent = BookOpen;
                      if (key.includes('ключев') || key.includes('концепц')) {
                        IconComponent = Lightbulb;
                      } else if (key.includes('практич') || key.includes('применен')) {
                        IconComponent = Target;
                      } else if (key.includes('миф') || key.includes('истор')) {
                        IconComponent = Scroll;
                      } else if (key.includes('введен')) {
                        IconComponent = Info;
                      } else if (key.includes('тел') || key.includes('тело')) {
                        IconComponent = Heart;
                      } else if (key.includes('карм') || key.includes('задач')) {
                        IconComponent = Compass;
                      } else if (key.includes('упай') || key.includes('гармониз')) {
                        IconComponent = Sun;
                      }

                      return (
                        <Card key={key}>
                          <CardHeader>
                            <CardTitle className="flex items-center">
                              <IconComponent className="w-5 h-5 mr-2" />
                              {displayName}
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="prose max-w-none">
                            <div className="text-gray-700 leading-relaxed text-base whitespace-pre-wrap">
                              {lessonData.content.theory[key]}
                            </div>
                          </CardContent>
                        </Card>
                      );
                    });
                  })()}
                </>
              );
            }
          })()}

          {/* Кастомные блоки теории */}
          {(() => {
            let customBlocks = lessonData.content?.custom_theory_blocks?.blocks;

            // Парсим JSON если это строка
            if (typeof customBlocks === 'string') {
              try {
                customBlocks = JSON.parse(customBlocks);
              } catch (e) {
                console.error('Error parsing custom_theory_blocks:', e);
                customBlocks = [];
              }
            }

            // Проверяем что это массив и он не пустой
            if (!Array.isArray(customBlocks) || customBlocks.length === 0) {
              return null;
            }

            return (
              <>
                {customBlocks.map((block) => (
                  <Card key={block.id}>
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        <BookOpen className="w-5 h-5 mr-2" />
                        {block.title}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="prose max-w-none">
                      <div className="text-gray-700 leading-relaxed text-base whitespace-pre-wrap">
                        {block.content}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </>
            );
          })()}

          {/* ДОПОЛНИТЕЛЬНЫЕ МАТЕРИАЛЫ */}
          {(additionalVideos.length > 0 || additionalPdfs.length > 0) && (
            <Card>
              <CardContent className="pt-6">
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
                              Все ({totalVideosCount + totalDocumentsCount})
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
                              Видео ({totalVideosCount})
                            </button>
                            <button
                              onClick={() => setMaterialsFilter('documents')}
                              className={`px-4 py-2 text-sm font-medium transition-all border-l border-purple-200/50 ${
                                materialsFilter === 'documents' 
                                  ? 'bg-purple-600 text-white' 
                                  : 'text-gray-600 hover:bg-purple-50'
                              }`}
                            >
                              <FileText className="w-4 h-4 inline mr-1" />
                              Документы ({totalDocumentsCount})
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
                              {materialsFilter === 'videos' ? 'Только видео' : 'Только документы'}
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
                      <Fragment>
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
                                {videoMaterials.length} из {totalVideosCount} видео
                                  </p>
                                </div>
                              </div>
                          {videoMaterials.length !== totalVideosCount && (
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

                    {/* Документы */}
                    {documentMaterials.length > 0 && (materialsFilter === 'all' || materialsFilter === 'documents') && (
                      <div className="p-6">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center">
                            <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-r from-green-600 to-emerald-600 rounded-lg mr-3">
                              <FileText className="w-5 h-5 text-white" />
                            </div>
                            <div>
                              <h4 className="text-lg font-semibold text-gray-900">Справочные материалы</h4>
                              <p className="text-sm text-gray-600">
                                {documentMaterials.length} из {totalDocumentsCount} документов
                              </p>
                            </div>
                          </div>
                          {documentMaterials.length !== totalDocumentsCount && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setMaterialsFilter('documents');
                                setMaterialsSearch('');
                              }}
                              className="text-green-600 border-green-600 hover:bg-green-50"
                            >
                              Показать все документы
                            </Button>
                          )}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {documentMaterials.map((doc, index) => {
                            const format = doc.format || determineDocumentFormat(doc);
                            const gradientClasses = {
                              pdf: 'from-green-600 to-emerald-600',
                              word: 'from-blue-600 to-indigo-600',
                              excel: 'from-teal-600 to-green-500',
                              presentation: 'from-amber-500 to-orange-500',
                              text: 'from-slate-600 to-gray-600',
                              other: 'from-purple-600 to-blue-600'
                            };
                            const gradient = gradientClasses[format] || gradientClasses.other;
                            const gradientClass = `flex items-center justify-center w-12 h-12 rounded-lg mr-3 flex-shrink-0 relative text-white bg-gradient-to-r ${gradient}`;
                            const labelMap = {
                              pdf: 'PDF',
                              word: 'Word',
                              excel: 'Excel',
                              presentation: 'Презентация',
                              text: 'Текст',
                              other: 'Документ'
                            };
                            const label = labelMap[format] || 'Документ';
                            const resourceUrl = doc.resource_url || doc.url || doc.pdf_url;
                            const sourceLabel = doc.origin === 'resource' ? 'Ресурсы' : 'PDF';

                            return (
                              <div key={doc.file_id} className="group bg-white rounded-xl border border-green-200/50 shadow-sm hover:shadow-md transition-all duration-200 p-4">
                                <div className="flex items-start mb-3">
                                  <div className={gradientClass}>
                                    <FileText className="w-6 h-6 text-white" />
                                    <div className="absolute -top-1 -right-1 bg-green-700 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold">
                                      {index + 1}
                                    </div>
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <h5 className="font-semibold text-gray-900 mb-1">{doc.title}</h5>
                                    <p className="text-sm text-gray-600">Дополнительный материал ({label})</p>
                                  </div>
                                </div>
                                <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
                                  <span>Файл: {doc.filename}</span>
                                  <span>Источник: {sourceLabel}</span>
                                </div>
                                <div className="flex gap-2">
                                  <Button
                                    onClick={() => {
                                      setSelectedDocument({
                                        ...doc,
                                        resource_url: resourceUrl,
                                        filename: doc.filename,
                                        title: doc.title,
                                        content_type: doc.content_type
                                      });
                                    }}
                                    className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white"
                                  >
                                    <Eye className="w-4 h-4 mr-2" />
                                    Открыть
                                  </Button>
                                  <Button
                                    variant="outline"
                                    onClick={() => {
                                      if (!resourceUrl) return;
                                      const baseHref = resourceUrl.startsWith('http') ? resourceUrl : `${backendUrl}${resourceUrl}`;
                                      const href = baseHref.includes('?') ? `${baseHref}&download=1` : `${baseHref}?download=1`;
                                      const link = document.createElement('a');
                                      link.href = href;
                                      link.target = '_blank';
                                      link.rel = 'noopener noreferrer';
                                      link.click();
                                    }}
                                    className="border-green-200 text-green-600 hover:bg-green-50"
                                  >
                                    <Download className="w-4 h-4 mr-2" />
                                    Скачать
                                  </Button>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Улучшенная информационная панель */}
                    <div className="bg-gradient-to-r from-purple-600/5 to-blue-600/5 border-t border-purple-200/30 p-4">
                      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                        <div className="flex items-center text-sm text-gray-600">
                          <Sparkles className="w-4 h-4 mr-2 text-purple-600" />
                          <span>
                            Показано {filteredMaterials.length} из {totalVideosCount + totalDocumentsCount} материалов
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-gray-500">
                          <div className="flex items-center">
                            <PlayCircle className="w-3 h-3 mr-1 text-purple-600" />
                            {videoMaterials.length} видео
                          </div>
                          <div className="flex items-center">
                            <FileText className="w-3 h-3 mr-1 text-green-600" />
                            {documentMaterials.length} документов
                          </div>
                          <div className="flex items-center">
                            <Timer className="w-3 h-3 mr-1 text-blue-600" />
                            Обновлено недавно
                          </div>
                        </div>
                      </div>
                    </div>
                  </Fragment>
              )}
                </div>
            </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* УПРАЖНЕНИЯ */}
        <TabsContent value="exercises" className="space-y-6">
          {(lessonData.exercises || lessonData.content?.exercises)?.map((exercise, index) => (
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
                {exercise.content && exercise.content.trim() && (
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="prose max-w-none text-sm">
                      <p className="whitespace-pre-line">{exercise.content}</p>
                    </div>
                  </div>
                )}

                <div>
                  <h4 className="font-semibold mb-2">Инструкции:</h4>
                  {exercise.instructions ? (
                    Array.isArray(exercise.instructions) ? (
                      <ul className="list-disc pl-5 space-y-1 text-sm">
                        {exercise.instructions.map((instruction, idx) => (
                          <li key={idx}>{instruction}</li>
                        ))}
                      </ul>
                    ) : (
                      <div className="text-sm whitespace-pre-line pl-5">
                        {exercise.instructions}
                      </div>
                    )
                  ) : (
                    <p className="text-sm text-gray-500 pl-5">Инструкции не указаны</p>
                  )}
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
                      disabled={!savedExercises.has(exercise.id)}
                      className={`flex-1 sm:flex-none transition-all duration-200 ${
                        completedExercises.has(exercise.id)
                          ? 'bg-green-500 hover:bg-green-600 text-white font-semibold'
                          : 'numerology-gradient hover:brightness-90'
                      }`}
                    >
                      {completedExercises.has(exercise.id) ? (
                        <>
                          <CheckCircle className="w-4 h-4 mr-1 sm:mr-2" />
                          <span className="hidden sm:inline">Упражнение выполнено</span>
                          <span className="sm:hidden">Выполнено</span>
                        </>
                      ) : (
                        <>
                          <Target className="w-4 h-4 mr-1 sm:mr-2" />
                          <span className="hidden sm:inline">Отметить как выполненное</span>
                          <span className="sm:hidden">Отметить</span>
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
                <Button onClick={() => setActiveSection('quiz')} className="numerology-gradient hover:brightness-90 transition-all duration-200">
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
                  {quizData.title}
                </CardTitle>
                <CardDescription>
                  Ответьте на все вопросы для проверки знаний. Для прохождения нужно набрать минимум 60%.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {quizData.questions?.map((question, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <h4 className="font-semibold mb-3">
                      Вопрос {index + 1}: {question.question}
                    </h4>
                    <div className="space-y-2">
                      {(question.options || []).map((option, optIndex) => (
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
                    className="numerology-gradient hover:brightness-90 disabled:brightness-90 disabled:cursor-not-allowed transition-all duration-200 px-8"
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
                {(quizResults.results || []).map((result, index) => (
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
                      <Button onClick={() => setActiveSection('challenge')} className="numerology-gradient hover:brightness-90 transition-all duration-200">
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
                  {challengeData.title}
                </CardTitle>
                <CardDescription>
                  {challengeData.description}
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
                  {(challengeData.daily_tasks || []).slice(0, 3).map((task, index) => (
                    <div key={index} className="p-3 border rounded-lg">
                      <div className="font-medium text-sm mb-2">День {task.day}: {task.title}</div>
                      <ul className="text-xs text-gray-600 space-y-1">
                        {(task.tasks || []).slice(0, 2).map((subtask, idx) => (
                          <li key={idx}>• {subtask}</li>
                        ))}
                        {task.tasks?.length > 2 && <li>• и еще {task.tasks.length - 2}...</li>}
                      </ul>
                    </div>
                  ))}
                </div>

                <PushNotificationSettings
                  lessonId={lessonData?.id}
                  onSubscribed={() => {
                    console.log('Push notifications subscribed successfully');
                  }}
                />

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

                {/* Кнопка "Пройти челлендж заново" */}
                <div className="flex flex-col items-center gap-3 pt-4 border-t">
                  <p className="text-sm text-gray-600 text-center">
                    Хотите усилить энергию Солнца еще больше?
                  </p>
                  <Button
                    onClick={restartChallenge}
                    className="numerology-gradient hover:brightness-90"
                  >
                    <Zap className="w-4 h-4 mr-2" />
                    Пройти челлендж заново
                  </Button>
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
                  <CardTitle>
                    День {selectedChallengeDay}: {challengeData.daily_tasks?.[selectedChallengeDay - 1]?.title}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <ul className="space-y-2">
                    {(challengeData.daily_tasks?.[selectedChallengeDay - 1]?.tasks || []).map((task, index) => (
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
                      const previousDayCompleted = day === 1 || challengeProgress?.completed_days?.includes(day - 1);
                      const isDisabled = !previousDayCompleted && !isCompleted;

                      return (
                        <Button
                          key={day}
                          variant={selectedChallengeDay === day ? "default" : "outline"}
                          size="sm"
                          onClick={() => setSelectedChallengeDay(day)}
                          disabled={isDisabled}
                          className={`${isCompleted ? 'border-green-500 bg-green-50 text-green-700' : ''} ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                          {isCompleted && <CheckCircle className="w-3 h-3 mr-1" />}
                          {isDisabled && <Lock className="w-3 h-3 mr-1" />}
                          День {day}
                        </Button>
                      );
                    })}
                  </div>
                  
                  {!challengeProgress?.completed_days?.includes(selectedChallengeDay) && (
                    <div className="space-y-3 pt-4 border-t">
                      <textarea
                        value={challengeDayNotes}
                        onChange={(e) => setChallengeDayNotes(e.target.value)}
                        placeholder="Поделитесь своими впечатлениями от выполнения задач дня (обязательно)..."
                        className="w-full p-3 border rounded-lg min-h-20 text-sm"
                      />
                      <Button
                        type="button"
                        onClick={(e) => {
                          e.preventDefault();
                          completeChallengeDay(selectedChallengeDay, challengeDayNotes);
                        }}
                        disabled={!challengeDayNotes.trim()}
                        className={`w-full sm:w-auto ${
                          challengeDayNotes.trim()
                            ? 'bg-green-600 hover:bg-green-700'
                            : 'bg-gray-400 cursor-not-allowed'
                        }`}
                      >
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Отправить впечатления и продолжить
                      </Button>
                      {!challengeDayNotes.trim() && (
                        <p className="text-sm text-orange-600">
                          ⚠️ Поделитесь впечатлениями, чтобы продолжить
                        </p>
                      )}
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
                  {(habitTracker.active_habits || []).map((habit, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center space-x-3 flex-1">
                        <Checkbox
                          checked={todayHabits[habit] || false}
                          onCheckedChange={(checked) => {
                            updateHabit(habit, checked);
                          }}
                        />
                        <label
                          className={`text-sm flex-1 cursor-pointer ${todayHabits[habit] ? 'line-through text-gray-500' : ''}`}
                          onClick={() => {
                            const newValue = !todayHabits[habit];
                            updateHabit(habit, newValue);
                          }}
                        >
                          {habit}
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        {todayHabits[habit] && (
                          <Badge className="bg-green-100 text-green-800 text-xs">
                            ✓ Выполнено
                          </Badge>
                        )}
                        <div className="text-xs text-gray-400">
                          {index + 1}/{habitTracker.active_habits.length}
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

      {/* Document Viewer Modal */}
      {selectedDocument && (
        <LessonDocumentViewer
          resource={selectedDocument}
          backendUrl={backendUrl}
          onClose={() => setSelectedDocument(null)}
        />
      )}
    </div>
  );
};

export default UniversalLessonViewer;

/**
 * КОНЕЦ КОМПОНЕНТА UniversalLessonViewer
 *
 * Этот компонент предоставляет полную функциональность для изучения уроков в системе NumerOM:
 * - Динамическая загрузка уроков с сервера
 * - Поддержка различных типов контента (теория, упражнения, тесты, челлендж, привычки)
 * - Интерактивный интерфейс с прогрессом и состоянием завершения
 * - Медиа поддержка (видео, PDF, документы)
 * - Адаптивный дизайн для различных устройств
 * - Сохранение прогресса пользователя
 */