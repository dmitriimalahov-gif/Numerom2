import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  Settings, FileText, Video, Upload, Save, Edit, Plus, Trash2,
  BookOpen, Brain, Target, Star, Zap, Eye, Download, Play, Copy
} from 'lucide-react';
import { useAuth } from './AuthContext';
import EnhancedVideoViewer from './EnhancedVideoViewer';
import ConsultationPDFViewer from './ConsultationPDFViewer';

const MultipleLessonAdmin = () => {
  const { user } = useAuth();
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
  
  // Основные состояния
  const [lessons, setLessons] = useState([]);
  const [selectedLesson, setSelectedLesson] = useState(null);
  const [editingLesson, setEditingLesson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('lessons-list');
  
  // Состояния для создания нового урока
  const [isCreatingNew, setIsCreatingNew] = useState(false);
  const [newLessonData, setNewLessonData] = useState({
    title: '',
    module: 'numerology',
    description: '',
    points_required: 0,
    is_active: true
  });
  
  // Состояния для редактирования контента
  const [lessonContent, setLessonContent] = useState({});
  const [activeSection, setActiveSection] = useState('theory');
  
  // Состояния для загрузки файлов (ТОЧНО КАК В КОНСУЛЬТАЦИЯХ)
  const [uploadingVideo, setUploadingVideo] = useState(false);
  const [videoUploadProgress, setVideoUploadProgress] = useState(0);
  
  // Состояния для модальных окон предпросмотра
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [selectedPDF, setSelectedPDF] = useState(null);

  // Состояния для редактирования упражнений
  const [editingExercise, setEditingExercise] = useState(null);
  const [addingExercise, setAddingExercise] = useState(false);
  const [exerciseForm, setExerciseForm] = useState({
    title: '',
    type: 'reflection',
    content: '',
    instructions: '',
    expected_outcome: ''
  });

  // Состояния для редактирования квиза
  const [editingQuestion, setEditingQuestion] = useState(null);
  const [addingQuestion, setAddingQuestion] = useState(false);
  const [questionForm, setQuestionForm] = useState({
    question: '',
    options: ['', '', '', ''],
    correct_answer: '',
    explanation: ''
  });

  // Состояния для редактирования челленджа
  const [editingDay, setEditingDay] = useState(null);
  const [addingDay, setAddingDay] = useState(false);
  const [dayForm, setDayForm] = useState({
    day: 1,
    title: '',
    tasks: ['', '', '']
  });

  useEffect(() => {
    loadLessons();
  }, []);

  // Синхронизация первого урока с общей системой
  const syncFirstLesson = async () => {
    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/api/admin/lessons/sync-first-lesson`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Синхронизация выполнена: ${data.message}`);
        loadLessons();
      } else {
        const errorData = await response.json();
        alert(`Ошибка синхронизации: ${errorData.detail || 'Неизвестная ошибка'}`);
      }
    } catch (err) {
      console.error('Ошибка синхронизации первого урока:', err);
      alert('Ошибка синхронизации первого урока');
    } finally {
      setSaving(false);
    }
  };

  // Загрузка списка всех уроков
  const loadLessons = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/api/admin/lessons`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setLessons(data.lessons || []);
      } else {
        console.error('Ошибка загрузки уроков:', response.status);
      }
    } catch (err) {
      console.error('Ошибка загрузки уроков:', err);
    } finally {
      setLoading(false);
    }
  };

  // Создание нового урока
  const createNewLesson = async () => {
    if (!newLessonData.title.trim()) {
      alert('Введите название урока');
      return;
    }

    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      
      const lessonData = {
        ...newLessonData,
        id: `lesson_${Date.now()}`,
        content: {
          theory: {
            what_is_topic: '',
            main_story: '',
            key_concepts: '',
            practical_applications: ''
          },
          exercises: [],
          quiz: {
            questions: [],
            answers: [],
            explanations: []
          },
          challenge: {
            title: '',
            description: '',
            daily_tasks: []
          }
        },
        created_at: new Date().toISOString()
      };
      
      const response = await fetch(`${backendUrl}/api/admin/lessons/create`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(lessonData)
      });

      if (response.ok) {
        alert('Урок успешно создан!');
        setIsCreatingNew(false);
        setNewLessonData({
          title: '',
          module: 'numerology',
          description: '',
          points_required: 0,
          is_active: true
        });
        loadLessons();
      } else {
        const errorData = await response.json();
        alert(`Ошибка создания урока: ${errorData.detail || 'Неизвестная ошибка'}`);
      }
    } catch (err) {
      console.error('Ошибка создания урока:', err);
      alert('Ошибка создания урока');
    } finally {
      setSaving(false);
    }
  };

  // Дублирование урока на основе первого занятия с новым содержанием
  const duplicateFromFirstLesson = async () => {
    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      
      const secondLessonData = {
        title: newLessonData.title || 'Урок 2: Цифры и Планеты в Нумерологии',
        module: newLessonData.module,
        description: newLessonData.description || 'Подробное изучение значений каждой цифры и соответствующих планет',
        points_required: newLessonData.points_required,
        is_active: newLessonData.is_active,
        id: `lesson_digits_planets_${Date.now()}`,
        content: {
          theory: {
            what_is_topic: `В этом уроке мы изучим детальные значения каждой цифры от 1 до 9 и их связь с планетарными энергиями.`,
            main_story: `Цифры и их планетарные соответствия:\n\n🌟 ЦИФРА 1 - СОЛНЦЕ (Сурья)\nКачества: лидерство, независимость, творчество\n\n🌙 ЦИФРА 2 - ЛУНА (Чандра)\nКачества: интуиция, сотрудничество, дипломатия`,
            key_concepts: `• ПЛАНЕТАРНЫЕ ЭНЕРГИИ\n• ЧИСЛЕННАЯ ВИБРАЦИЯ\n• КАРМИЧЕСКИЕ УРОКИ`,
            practical_applications: `1. АНАЛИЗ ЛИЧНОСТИ\n2. ВЫБОР ПРОФЕССИИ\n3. СОВМЕСТИМОСТЬ`
          },
          exercises: [
            {
              id: 'ex_digit_analysis',
              title: 'Анализ своих основных цифр',
              type: 'reflection',
              content: 'Определите свои основные числа и проанализируйте их характеристики',
              instructions: ['Рассчитайте свои три основных числа', 'Найдите описание каждого числа'],
              expected_outcome: 'Глубокое понимание своих численных энергий'
            }
          ],
          quiz: {
            id: 'quiz_digits_planets',
            title: 'Тест: Цифры и Планеты',
            questions: [
              {
                question: 'Какая планета соответствует цифре 1?',
                options: ['a) Луна', 'b) Солнце', 'c) Марс', 'd) Венера'],
                correct_answer: 'b',
                explanation: 'Цифре 1 соответствует Солнце (Сурья) - символ лидерства и независимости'
              }
            ]
          },
          challenge: {
            id: 'challenge_daily_numbers',
            title: 'Недельный вызов: Жизнь в гармонии с числами',
            description: '7-дневная практика осознанного взаимодействия со своими основными числами',
            daily_tasks: [
              {
                day: 1,
                title: 'День Число Души',
                tasks: ['Сосредоточьтесь на качествах своего Числа Души', 'Проявите позитивные качества']
              }
            ]
          }
        },
        created_at: new Date().toISOString()
      };
      
      const createResponse = await fetch(`${backendUrl}/api/admin/lessons/create`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(secondLessonData)
      });

      if (createResponse.ok) {
        alert('Урок "Цифры и Планеты" успешно создан!');
        setIsCreatingNew(false);
        setNewLessonData({
          title: '',
          module: 'numerology', 
          description: '',
          points_required: 0,
          is_active: true
        });
        loadLessons();
      } else {
        const errorData = await createResponse.json();
        alert(`Ошибка создания урока: ${errorData.detail || 'Неизвестная ошибка'}`);
      }
    } catch (err) {
      console.error('Ошибка создания урока:', err);
      alert('Ошибка создания урока');
    } finally {
      setSaving(false);
    }
  };

  // Загрузка конкретного урока для редактирования
  const loadLessonForEditing = async (lessonId) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/api/admin/lessons/${lessonId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setEditingLesson(data.lesson);
        setLessonContent(data.lesson.content || {});
        setActiveTab('lesson-editor');
      } else {
        alert('Ошибка загрузки урока');
      }
    } catch (err) {
      console.error('Ошибка загрузки урока:', err);
      alert('Ошибка загрузки урока');
    } finally {
      setLoading(false);
    }
  };

  // Сохранение изменений в контенте урока
  const saveContentSection = async (section, field, value) => {
    if (!editingLesson) return;

    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/api/admin/lessons/${editingLesson.id}/content`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          section,
          field,
          value
        })
      });

      if (response.ok) {
        setLessonContent(prev => ({
          ...prev,
          [section]: {
            ...prev[section],
            [field]: value
          }
        }));
      } else {
        alert('Ошибка сохранения');
      }
    } catch (err) {
      console.error('Ошибка сохранения:', err);
      alert('Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  // ЗАГРУЗКА ВИДЕО ДЛЯ УРОКА
  const handleLessonVideoUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingVideo(true);
    setVideoUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Используем XMLHttpRequest для отслеживания прогресса
      await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        // Отслеживание прогресса загрузки
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const percentComplete = Math.round((e.loaded / e.total) * 100);
            setVideoUploadProgress(percentComplete);
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status === 200) {
            const result = JSON.parse(xhr.responseText);
            setEditingLesson(prev => ({
              ...prev,
              video_file_id: result.file_id,
              video_filename: result.filename
            }));
            resolve();
          } else {
            alert('Ошибка загрузки видео');
            reject(new Error('Upload failed'));
          }
        });

        xhr.addEventListener('error', () => {
          reject(new Error('Network error'));
        });

        xhr.open('POST', `${backendUrl}/api/admin/lessons/upload-video`);
        xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('token')}`);
        xhr.send(formData);
      });
    } catch (error) {
      console.error('Ошибка загрузки видео урока:', error);
      alert('Ошибка загрузки видео');
    } finally {
      setUploadingVideo(false);
      setVideoUploadProgress(0);
    }
  };

  // ЗАГРУЗКА PDF ДЛЯ УРОКА - ТОЧНАЯ КОПИЯ ИЗ КОНСУЛЬТАЦИЙ
  const handleLessonPDFUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingVideo(true); // Используем тот же флаг для loading состояния

    try {
      const formData = new FormData();
      formData.append('file', file);

      // ИСПОЛЬЗУЕМ ТОТ ЖЕ ENDPOINT ЧТО И ДЛЯ КОНСУЛЬТАЦИЙ - РАБОТАЮЩИЙ!
      const response = await fetch(`${backendUrl}/api/admin/consultations/upload-pdf`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        setEditingLesson(prev => ({
          ...prev,
          pdf_file_id: result.file_id,
          pdf_filename: result.filename
        }));
        alert('PDF успешно загружен!');
      } else {
        alert('Ошибка загрузки PDF');
      }
    } catch (error) {
      console.error('Ошибка загрузки PDF урока:', error);
      alert('Ошибка загрузки PDF');
    } finally {
      setUploadingVideo(false);
    }
  };

  // ОБНОВЛЕНИЕ УРОКА - КАК КОНСУЛЬТАЦИИ
  const updateLesson = async () => {
    if (!editingLesson) return;

    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      
      // Сохраняем изменения урока (включая медиа file_id)
      const response = await fetch(`${backendUrl}/api/admin/lessons/${editingLesson.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: editingLesson.title,
          description: editingLesson.description,
          module: editingLesson.module,
          points_required: editingLesson.points_required,
          is_active: editingLesson.is_active,
          video_file_id: editingLesson.video_file_id,
          video_filename: editingLesson.video_filename,
          pdf_file_id: editingLesson.pdf_file_id,
          pdf_filename: editingLesson.pdf_filename,
          content: lessonContent
        })
      });

      if (response.ok) {
        alert('Урок успешно обновлен! Студенты увидят новые материалы.');
        loadLessons();
      } else {
        const errorData = await response.json();
        alert(`Ошибка обновления урока: ${errorData.detail || 'Неизвестная ошибка'}`);
      }
    } catch (err) {
      console.error('Ошибка обновления урока:', err);
      alert('Ошибка обновления урока');
    } finally {
      setSaving(false);
    }
  };

  // Добавить новое упражнение
  const addExercise = async () => {
    if (!editingLesson || !exerciseForm.title.trim()) {
      alert('Заполните название упражнения');
      return;
    }

    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();
      
      formData.append('lesson_id', editingLesson.id);
      formData.append('title', exerciseForm.title);
      formData.append('content', exerciseForm.content);
      formData.append('instructions', exerciseForm.instructions);
      formData.append('expected_outcome', exerciseForm.expected_outcome);
      formData.append('exercise_type', exerciseForm.type);
      
      const response = await fetch(`${backendUrl}/api/admin/add-exercise`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        alert('Упражнение добавлено успешно!');
        
        const newExercise = {
          id: data.exercise_id,
          title: exerciseForm.title,
          type: exerciseForm.type,
          content: exerciseForm.content,
          instructions: exerciseForm.instructions.split('\n').filter(i => i.trim()),
          expected_outcome: exerciseForm.expected_outcome
        };
        
        setLessonContent(prev => ({
          ...prev,
          exercises: [...(prev.exercises || []), newExercise]
        }));
        
        setExerciseForm({
          title: '',
          type: 'reflection',
          content: '',
          instructions: '',
          expected_outcome: ''
        });
        setAddingExercise(false);
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка добавления упражнения');
      }
    } catch (err) {
      console.error('Ошибка добавления упражнения:', err);
      alert('Ошибка добавления упражнения');
    } finally {
      setSaving(false);
    }
  };

  // Добавить новый вопрос квиза
  const addQuizQuestion = async () => {
    if (!editingLesson || !questionForm.question.trim()) {
      alert('Заполните вопрос');
      return;
    }

    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();
      
      formData.append('lesson_id', editingLesson.id);
      formData.append('question_text', questionForm.question);
      formData.append('options', questionForm.options.filter(opt => opt.trim()).join('\n'));
      formData.append('correct_answer', questionForm.correct_answer);
      formData.append('explanation', questionForm.explanation);
      
      const response = await fetch(`${backendUrl}/api/admin/add-quiz-question`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        alert('Вопрос добавлен успешно!');
        
        const newQuestion = {
          id: data.question_id,
          question: questionForm.question,
          options: questionForm.options.filter(opt => opt.trim()),
          correct_answer: questionForm.correct_answer,
          explanation: questionForm.explanation
        };
        
        setLessonContent(prev => ({
          ...prev,
          quiz: {
            ...prev.quiz,
            questions: [...(prev.quiz?.questions || []), newQuestion]
          }
        }));
        
        setQuestionForm({
          question: '',
          options: ['', '', '', ''],
          correct_answer: '',
          explanation: ''
        });
        setAddingQuestion(false);
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка добавления вопроса');
      }
    } catch (err) {
      console.error('Ошибка добавления вопроса:', err);
      alert('Ошибка добавления вопроса');
    } finally {
      setSaving(false);
    }
  };

  // Удаление урока
  const deleteLesson = async (lessonId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот урок? Это действие необратимо.')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${backendUrl}/api/admin/lessons/${lessonId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        alert('Урок успешно удален');
        loadLessons();
      } else {
        alert('Ошибка удаления урока');
      }
    } catch (err) {
      console.error('Ошибка удаления урока:', err);
      alert('Ошибка удаления урока');
    }
  };

  // Проверка прав доступа
  if (!user || (!user.is_admin && !user.is_super_admin)) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <Settings className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p className="text-gray-600">Доступ запрещен. Только для администраторов.</p>
        </CardContent>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p>Загрузка админ-панели уроков...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Заголовок */}
      <Card className="bg-gradient-to-r from-purple-600 to-blue-600">
        <CardHeader className="text-white">
          <CardTitle className="text-lg sm:text-2xl flex items-center">
            <BookOpen className="w-5 h-5 sm:w-6 sm:h-6 mr-2" />
            <span className="hidden sm:inline">Админ-панель: Редактор уроков NumerOM</span>
            <span className="sm:hidden">Редактор уроков</span>
          </CardTitle>
          <CardDescription className="text-white/90 text-sm">
            Создавайте и редактируйте уроки, управляйте контентом и материалами
          </CardDescription>
        </CardHeader>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-2 lg:grid-cols-3">
          <TabsTrigger value="lessons-list" className="flex items-center justify-center gap-1 sm:gap-2">
            <BookOpen className="w-4 h-4" />
            <span className="text-xs sm:text-sm">Список</span>
          </TabsTrigger>
          <TabsTrigger value="create-lesson" className="flex items-center justify-center gap-1 sm:gap-2">
            <Plus className="w-4 h-4" />
            <span className="text-xs sm:text-sm">Создать</span>
          </TabsTrigger>
          <TabsTrigger value="lesson-editor" className="flex items-center justify-center gap-1 sm:gap-2" disabled={!editingLesson}>
            <Edit className="w-4 h-4" />
            <span className="text-xs sm:text-sm">Редактор</span>
          </TabsTrigger>
        </TabsList>

        {/* СПИСОК УРОКОВ */}
        <TabsContent value="lessons-list" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <span>Все уроки</span>
                <div className="flex flex-col sm:flex-row gap-2">
                  <Button onClick={syncFirstLesson} variant="outline" size="sm" className="w-full sm:w-auto">
                    <BookOpen className="w-4 h-4 mr-2" />
                    <span className="hidden sm:inline">Синх. первого урока</span>
                    <span className="sm:hidden">Синхронизация</span>
                  </Button>
                  <Button onClick={() => setActiveTab('create-lesson')} className="w-full sm:w-auto">
                    <Plus className="w-4 h-4 mr-2" />
                    <span className="hidden sm:inline">Создать новый урок</span>
                    <span className="sm:hidden">Создать урок</span>
                  </Button>
                </div>
              </CardTitle>
              <CardDescription>
                Управление существующими уроками
              </CardDescription>
            </CardHeader>
            <CardContent>
              {lessons.length === 0 ? (
                <div className="text-center py-8">
                  <BookOpen className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                  <p className="text-gray-500 mb-4">Уроков пока нет</p>
                  <div className="flex flex-col sm:flex-row gap-3 justify-center">
                    <Button onClick={() => setActiveTab('create-lesson')}>
                      <Plus className="w-4 h-4 mr-2" />
                      Создать первый урок
                    </Button>
                    <Button onClick={syncFirstLesson} variant="outline">
                      <BookOpen className="w-4 h-4 mr-2" />
                      Добавить первое занятие
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="grid gap-4">
                  {lessons.map((lesson, index) => (
                    <Card 
                      key={lesson.id} 
                      className={`${
                        lesson.id === 'lesson_numerom_intro' 
                          ? 'border-l-4 border-l-blue-500 bg-blue-50/30' 
                          : 'border-l-4 border-l-gray-300'
                      }`}
                    >
                      <CardContent className="p-3 sm:p-4">
                        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                          <div className="flex-1">
                            <div className="flex flex-wrap items-center gap-2 mb-2">
                              <h4 className="font-semibold text-base sm:text-lg">{lesson.title}</h4>
                              {lesson.id === 'lesson_numerom_intro' && (
                                <Badge className="bg-blue-100 text-blue-800 text-xs">
                                  Первый урок
                                </Badge>
                              )}
                              {lesson.source && (
                                <Badge variant="outline" className="text-xs">
                                  {lesson.source === 'lesson_system' ? 'Системный' :
                                   lesson.source === 'custom_lessons' ? 'Пользовательский' :
                                   'Видео урок'}
                                </Badge>
                              )}
                            </div>

                            <p className="text-xs sm:text-sm text-gray-600 mb-3 line-clamp-2">
                              {lesson.description || 'Описание отсутствует'}
                            </p>

                            <div className="flex flex-wrap items-center gap-2 mb-3">
                              <Badge variant="outline" className="text-xs">Модуль: {lesson.module || 'Не указан'}</Badge>
                              <Badge variant="outline" className="text-xs">
                                Баллы: {lesson.points_required || 0}
                                {lesson.points_required === 0 && ' (Бесплатно)'}
                              </Badge>
                              <Badge variant={lesson.is_active ? "default" : "secondary"} className="text-xs">
                                {lesson.is_active ? "Активен" : "Неактивен"}
                              </Badge>
                            </div>

                            {/* ОТОБРАЖЕНИЕ МЕДИА КАК В КОНСУЛЬТАЦИЯХ */}
                            <div className="flex items-center gap-4 text-xs text-gray-500 mb-2">
                              {lesson.video_file_id && (
                                <div className="flex items-center bg-blue-50 px-2 py-1 rounded border border-blue-200">
                                  <Video className="w-3 h-3 mr-1 text-blue-600" />
                                  <span className="text-blue-700">Видео: {lesson.video_filename || 'загружено'}</span>
                                </div>
                              )}
                              {lesson.pdf_file_id && (
                                <div className="flex items-center bg-green-50 px-2 py-1 rounded border border-green-200">
                                  <FileText className="w-3 h-3 mr-1 text-green-600" />
                                  <span className="text-green-700">PDF: {lesson.pdf_filename || 'загружено'}</span>
                                </div>
                              )}
                            </div>

                            <div className="text-xs text-gray-500">
                              Создан: {new Date(lesson.created_at || Date.now()).toLocaleDateString()}
                              {lesson.source && (
                                <span className="ml-2">• Источник: {
                                  lesson.source === 'lesson_system' ? 'Система уроков' :
                                  lesson.source === 'custom_lessons' ? 'Пользовательские уроки' :
                                  'Видео уроки'
                                }</span>
                              )}
                            </div>
                          </div>

                          <div className="flex gap-2 sm:ml-4">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => loadLessonForEditing(lesson.id)}
                              disabled={lesson.source === 'lesson_system'}
                              title={lesson.source === 'lesson_system' ? 'Системный урок нельзя редактировать напрямую' : 'Редактировать урок'}
                              className="flex-shrink-0"
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => deleteLesson(lesson.id)}
                              className="text-red-600 hover:text-red-800 flex-shrink-0"
                              disabled={lesson.id === 'lesson_numerom_intro'}
                              title={lesson.id === 'lesson_numerom_intro' ? 'Нельзя удалить первый урок' : 'Удалить урок'}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* СОЗДАНИЕ НОВОГО УРОКА */}
        <TabsContent value="create-lesson" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Создание нового урока</CardTitle>
              <CardDescription>
                Заполните основную информацию о новом уроке
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Название урока</Label>
                <Input
                  placeholder="Введите название урока"
                  value={newLessonData.title}
                  onChange={(e) => setNewLessonData({...newLessonData, title: e.target.value})}
                />
              </div>

              <div>
                <Label>Модуль</Label>
                <select
                  className="w-full p-2 border rounded-md"
                  value={newLessonData.module}
                  onChange={(e) => setNewLessonData({...newLessonData, module: e.target.value})}
                >
                  <option value="numerology">Нумерология</option>
                  <option value="advanced">Продвинутый уровень</option>
                  <option value="practical">Практические занятия</option>
                </select>
              </div>

              <div>
                <Label>Описание</Label>
                <textarea
                  className="w-full p-2 border rounded-md"
                  rows="3"
                  placeholder="Краткое описание урока"
                  value={newLessonData.description}
                  onChange={(e) => setNewLessonData({...newLessonData, description: e.target.value})}
                />
              </div>

              <div>
                <Label>Требуемые баллы для доступа</Label>
                <Input
                  type="number"
                  min="0"
                  placeholder="0"
                  value={newLessonData.points_required}
                  onChange={(e) => setNewLessonData({...newLessonData, points_required: parseInt(e.target.value) || 0})}
                />
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={newLessonData.is_active}
                  onChange={(e) => setNewLessonData({...newLessonData, is_active: e.target.checked})}
                />
                <Label htmlFor="is_active">Урок активен</Label>
              </div>

              <div className="flex gap-3 pt-4">
                <Button 
                  onClick={createNewLesson}
                  disabled={saving || !newLessonData.title.trim()}
                  className="flex-1"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  {saving ? 'Создание...' : 'Создать пустой урок'}
                </Button>
                <Button 
                  onClick={duplicateFromFirstLesson}
                  disabled={saving || !newLessonData.title.trim()}
                  variant="outline"
                  className="flex-1"
                >
                  <Copy className="w-4 h-4 mr-2" />
                  {saving ? 'Создание...' : 'Создать "Цифры и Планеты"'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* РЕДАКТОР УРОКА */}
        <TabsContent value="lesson-editor" className="space-y-6">
          {editingLesson ? (
            <div className="space-y-6">
              {/* Заголовок редактируемого урока */}
              <Card>
                <CardHeader>
                  <CardTitle>Редактирование: {editingLesson.title}</CardTitle>
                  <CardDescription>
                    Модуль: {editingLesson.module} • Баллы: {editingLesson.points_required || 0}
                  </CardDescription>
                </CardHeader>
              </Card>

              {/* Вложенные табы для разделов урока */}
              <Tabs value={activeSection} onValueChange={setActiveSection} className="space-y-6">
                <TabsList className="grid w-full grid-cols-2 lg:grid-cols-4">
                  <TabsTrigger value="theory">
                    <BookOpen className="w-4 h-4 mr-2" />
                    Теория
                  </TabsTrigger>
                  <TabsTrigger value="exercises">
                    <Brain className="w-4 h-4 mr-2" />
                    Упражнения
                  </TabsTrigger>
                  <TabsTrigger value="quiz">
                    <Target className="w-4 h-4 mr-2" />
                    Тест
                  </TabsTrigger>
                  <TabsTrigger value="media">
                    <Upload className="w-4 h-4 mr-2" />
                    Медиа
                  </TabsTrigger>
                </TabsList>

                {/* РЕДАКТИРОВАНИЕ ТЕОРИИ */}
                <TabsContent value="theory" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Теоретическая часть</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <Label>Что изучаем в этом уроке?</Label>
                        <textarea
                          className="w-full p-3 border rounded-lg min-h-32"
                          value={lessonContent.theory?.what_is_topic || ''}
                          onChange={(e) => saveContentSection('theory', 'what_is_topic', e.target.value)}
                          placeholder="Введение в тему урока..."
                        />
                      </div>

                      <div>
                        <Label>Основная история/объяснение</Label>
                        <textarea
                          className="w-full p-3 border rounded-lg min-h-48"
                          value={lessonContent.theory?.main_story || ''}
                          onChange={(e) => saveContentSection('theory', 'main_story', e.target.value)}
                          placeholder="Основное содержание урока..."
                        />
                      </div>

                      <div>
                        <Label>Ключевые концепции</Label>
                        <textarea
                          className="w-full p-3 border rounded-lg min-h-32"
                          value={lessonContent.theory?.key_concepts || ''}
                          onChange={(e) => saveContentSection('theory', 'key_concepts', e.target.value)}
                          placeholder="Важные понятия и термины..."
                        />
                      </div>

                      <div>
                        <Label>Практическое применение</Label>
                        <textarea
                          className="w-full p-3 border rounded-lg min-h-32"
                          value={lessonContent.theory?.practical_applications || ''}
                          onChange={(e) => saveContentSection('theory', 'practical_applications', e.target.value)}
                          placeholder="Как применить знания на практике..."
                        />
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* РЕДАКТИРОВАНИЕ УПРАЖНЕНИЙ */}
                <TabsContent value="exercises" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between">
                        <span>Упражнения урока</span>
                        <Button onClick={() => setAddingExercise(true)} size="sm">
                          <Plus className="w-4 h-4 mr-2" />
                          Добавить упражнение
                        </Button>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* Список существующих упражнений */}
                      {lessonContent.exercises?.map((exercise, index) => (
                        <Card key={exercise.id || index} className="border border-gray-200">
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="font-semibold">{exercise.title}</h4>
                              <div className="flex gap-2">
                                <Badge variant="outline">{exercise.type}</Badge>
                                <Button size="sm" variant="outline" onClick={() => setEditingExercise(exercise)}>
                                  <Edit className="w-3 h-3" />
                                </Button>
                              </div>
                            </div>
                            <p className="text-sm text-gray-600 mb-2">{exercise.content}</p>
                            <p className="text-xs text-gray-500">Ожидаемый результат: {exercise.expected_outcome}</p>
                          </CardContent>
                        </Card>
                      ))}

                      {/* Форма добавления упражнения */}
                      {addingExercise && (
                        <Card className="border-green-200 bg-green-50">
                          <CardHeader>
                            <CardTitle className="flex items-center justify-between">
                              <span>Новое упражнение</span>
                              <Button size="sm" variant="outline" onClick={() => setAddingExercise(false)}>
                                Отмена
                              </Button>
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-4">
                            <div>
                              <Label>Название упражнения</Label>
                              <Input
                                value={exerciseForm.title}
                                onChange={(e) => setExerciseForm({...exerciseForm, title: e.target.value})}
                                placeholder="Название упражнения"
                              />
                            </div>
                            
                            <div>
                              <Label>Тип упражнения</Label>
                              <select
                                className="w-full p-2 border rounded-md"
                                value={exerciseForm.type}
                                onChange={(e) => setExerciseForm({...exerciseForm, type: e.target.value})}
                              >
                                <option value="reflection">Рефлексия</option>
                                <option value="calculation">Расчеты</option>
                                <option value="meditation">Медитация</option>
                                <option value="practical">Практическое</option>
                              </select>
                            </div>

                            <div>
                              <Label>Содержание упражнения</Label>
                              <textarea
                                className="w-full p-3 border rounded-lg min-h-32"
                                value={exerciseForm.content}
                                onChange={(e) => setExerciseForm({...exerciseForm, content: e.target.value})}
                                placeholder="Описание упражнения..."
                              />
                            </div>

                            <div>
                              <Label>Инструкции (по одной на строку)</Label>
                              <textarea
                                className="w-full p-3 border rounded-lg min-h-24"
                                value={exerciseForm.instructions}
                                onChange={(e) => setExerciseForm({...exerciseForm, instructions: e.target.value})}
                                placeholder="Шаг 1: ..."
                              />
                            </div>

                            <div>
                              <Label>Ожидаемый результат</Label>
                              <Input
                                value={exerciseForm.expected_outcome}
                                onChange={(e) => setExerciseForm({...exerciseForm, expected_outcome: e.target.value})}
                                placeholder="Что должен получить ученик"
                              />
                            </div>

                            <Button onClick={addExercise} disabled={saving} className="w-full">
                              <Save className="w-4 h-4 mr-2" />
                              {saving ? 'Сохранение...' : 'Добавить упражнение'}
                            </Button>
                          </CardContent>
                        </Card>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* РЕДАКТИРОВАНИЕ ТЕСТА */}
                <TabsContent value="quiz" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between">
                        <span>Тест по уроку</span>
                        <Button onClick={() => setAddingQuestion(true)} size="sm">
                          <Plus className="w-4 h-4 mr-2" />
                          Добавить вопрос
                        </Button>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* Список существующих вопросов */}
                      {lessonContent.quiz?.questions?.map((question, index) => (
                        <Card key={question.id || index} className="border border-gray-200">
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="font-semibold">Вопрос {index + 1}</h4>
                              <Button size="sm" variant="outline" onClick={() => setEditingQuestion(question)}>
                                <Edit className="w-3 h-3" />
                              </Button>
                            </div>
                            <p className="text-sm text-gray-700 mb-2">{question.question}</p>
                            <div className="text-xs text-gray-500">
                              <p>Правильный ответ: {question.correct_answer}</p>
                              <p>Объяснение: {question.explanation}</p>
                            </div>
                          </CardContent>
                        </Card>
                      ))}

                      {/* Форма добавления вопроса */}
                      {addingQuestion && (
                        <Card className="border-purple-200 bg-purple-50">
                          <CardHeader>
                            <CardTitle className="flex items-center justify-between">
                              <span>Новый вопрос</span>
                              <Button size="sm" variant="outline" onClick={() => setAddingQuestion(false)}>
                                Отмена
                              </Button>
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-4">
                            <div>
                              <Label>Текст вопроса</Label>
                              <Input
                                value={questionForm.question}
                                onChange={(e) => setQuestionForm({...questionForm, question: e.target.value})}
                                placeholder="Введите вопрос"
                              />
                            </div>
                            
                            <div>
                              <Label>Варианты ответов</Label>
                              {questionForm.options.map((option, idx) => (
                                <Input
                                  key={idx}
                                  className="mb-2"
                                  value={option}
                                  onChange={(e) => {
                                    const newOptions = [...questionForm.options];
                                    newOptions[idx] = e.target.value;
                                    setQuestionForm({...questionForm, options: newOptions});
                                  }}
                                  placeholder={`Вариант ${String.fromCharCode(97 + idx)}) ...`}
                                />
                              ))}
                            </div>

                            <div>
                              <Label>Правильный ответ</Label>
                              <select
                                className="w-full p-2 border rounded-md"
                                value={questionForm.correct_answer}
                                onChange={(e) => setQuestionForm({...questionForm, correct_answer: e.target.value})}
                              >
                                <option value="">Выберите правильный ответ</option>
                                <option value="a">a) {questionForm.options[0]}</option>
                                <option value="b">b) {questionForm.options[1]}</option>
                                <option value="c">c) {questionForm.options[2]}</option>
                                <option value="d">d) {questionForm.options[3]}</option>
                              </select>
                            </div>

                            <div>
                              <Label>Объяснение правильного ответа</Label>
                              <textarea
                                className="w-full p-3 border rounded-lg min-h-24"
                                value={questionForm.explanation}
                                onChange={(e) => setQuestionForm({...questionForm, explanation: e.target.value})}
                                placeholder="Объясните почему этот ответ правильный..."
                              />
                            </div>

                            <Button onClick={addQuizQuestion} disabled={saving} className="w-full">
                              <Save className="w-4 h-4 mr-2" />
                              {saving ? 'Сохранение...' : 'Добавить вопрос'}
                            </Button>
                          </CardContent>
                        </Card>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* ЗАГРУЗКА МЕДИА - ТОЧНО КАК В КОНСУЛЬТАЦИЯХ */}
                <TabsContent value="media" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Медиа материалы урока</CardTitle>
                      <CardDescription>
                        Управляйте видео и PDF материалами для урока
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      
                      {/* Video Upload - ТОЧНАЯ КОПИЯ ИЗ КОНСУЛЬТАЦИЙ */}
                      <div>
                        <Label>Видео урока</Label>
                        <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                          <input
                            type="file"
                            accept="video/*"
                            onChange={handleLessonVideoUpload}
                            className="w-full"
                            disabled={uploadingVideo}
                          />
                          {uploadingVideo && (
                            <div className="mt-2">
                              <div className="flex justify-between text-sm text-blue-600 mb-1">
                                <span>Загружается видео...</span>
                                <span>{videoUploadProgress}%</span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2.5">
                                <div
                                  className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                                  style={{ width: `${videoUploadProgress}%` }}
                                ></div>
                              </div>
                            </div>
                          )}
                          {editingLesson.video_filename && (
                            <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded flex justify-between items-center">
                              <p className="text-sm text-green-600">✓ Видео: {editingLesson.video_filename}</p>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  const videoUrl = editingLesson.video_file_id
                                    ? `${backendUrl}/api/lessons/video/${editingLesson.video_file_id}`
                                    : editingLesson.video_url;
                                  setSelectedVideo({
                                    url: videoUrl,
                                    title: `Предпросмотр: ${editingLesson.title || 'Урок'}`,
                                    lesson: editingLesson
                                  });
                                }}
                              >
                                <Eye className="w-3 h-3 mr-1" />
                                Просмотр
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* PDF Upload - ТОЧНАЯ КОПИЯ ИЗ КОНСУЛЬТАЦИЙ */}
                      <div>
                        <Label>PDF материалы урока</Label>
                        <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                          <input
                            type="file"
                            accept="application/pdf"
                            onChange={handleLessonPDFUpload}
                            className="w-full"
                            disabled={uploadingVideo}
                          />
                          {uploadingVideo && <p className="text-sm text-blue-600 mt-2">Загружается PDF...</p>}
                          {editingLesson.pdf_filename && (
                            <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded flex justify-between items-center">
                              <p className="text-sm text-green-600">✓ PDF: {editingLesson.pdf_filename}</p>
                              <Button 
                                size="sm" 
                                variant="outline"
                                onClick={() => {
                                  setSelectedPDF({
                                    url: `${backendUrl}/api/consultations/pdf/${editingLesson.pdf_file_id}`,
                                    title: `PDF: ${editingLesson.title || 'Урок'}`,
                                    lesson: editingLesson
                                  });
                                }}
                              >
                                <Eye className="w-3 h-3 mr-1" />
                                Просмотр
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Кнопка сохранения изменений урока */}
                      <div className="pt-4 border-t">
                        <Button 
                          onClick={updateLesson}
                          disabled={saving}
                          className="w-full"
                        >
                          <Save className="w-4 h-4 mr-2" />
                          {saving ? 'Сохранение...' : 'Сохранить изменения урока'}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <Edit className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500 mb-4">Выберите урок для редактирования</p>
                <Button onClick={() => setActiveTab('lessons-list')}>
                  <BookOpen className="w-4 h-4 mr-2" />
                  К списку уроков
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Модальные окна для предпросмотра - КАК В КОНСУЛЬТАЦИЯХ */}
      {selectedVideo && (
        <EnhancedVideoViewer
          videoUrl={selectedVideo.url}
          title={selectedVideo.title}
          description={selectedVideo.lesson?.description || 'Урок'}
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

export default MultipleLessonAdmin;