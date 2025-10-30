import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Label } from './ui/label';
import { Input } from './ui/input';
import {
  Settings, FileText, Video, Upload, Save, Edit, Plus, Copy,
  BookOpen, Brain, Target, Star, Zap, Trash2, Eye
} from 'lucide-react';
import { useAuth } from './AuthContext';

// Импорт подкомпонентов
import LessonTheoryEditor from './lesson-editor/LessonTheoryEditor';
import LessonExercisesEditor from './lesson-editor/LessonExercisesEditor';
import LessonQuizEditor from './lesson-editor/LessonQuizEditor';
import LessonChallengeEditor from './lesson-editor/LessonChallengeEditor';
import LessonMediaEditor from './lesson-editor/LessonMediaEditor';
import LessonHabitsEditor from './lesson-editor/LessonHabitsEditor';

/**
 * UNIFIED LESSON EDITOR
 * Универсальный редактор уроков для всех типов уроков, включая первый урок
 *
 * Props:
 * - showLessonsList: boolean - показывать ли список всех уроков (по умолчанию true)
 * - initialLessonId: string - ID урока для редактирования (опционально)
 */
const UnifiedLessonEditor = ({
  showLessonsList = true,
  initialLessonId = null
}) => {
  const { user } = useAuth();
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

  // ==================== СОСТОЯНИЯ ====================

  // Основные состояния
  const [lessons, setLessons] = useState([]);
  const [editingLesson, setEditingLesson] = useState(null);
  const [lessonContent, setLessonContent] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('lessons-list');
  const [activeSection, setActiveSection] = useState('theory');

  // Флаги режимов
  const [isCreatingNew, setIsCreatingNew] = useState(false);
  const [isFirstLesson, setIsFirstLesson] = useState(false);

  // Состояния для упражнений и тестов управляются внутри соответствующих компонентов

  // Состояния для медиа
  const [uploadingVideo, setUploadingVideo] = useState(false);
  const [uploadingPDF, setUploadingPDF] = useState(false);

  // ==================== ЖИЗНЕННЫЙ ЦИКЛ ====================

  useEffect(() => {
    if (showLessonsList) {
      loadLessons();
    } else if (initialLessonId) {
      loadLessonForEditing(initialLessonId);
    }
  }, []);

  // ==================== ЗАГРУЗКА ДАННЫХ ====================

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
        console.log('Загружено уроков:', data.lessons?.length, data.lessons);
        setLessons(data.lessons || []);
      } else {
        console.error('Ошибка загрузки уроков');
      }
    } catch (err) {
      console.error('Ошибка загрузки уроков:', err);
    } finally {
      setLoading(false);
    }
  };

  // Загрузка конкретного урока для редактирования
  const loadLessonForEditing = async (lessonId) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      // Определяем, это первый урок или нет
      const isFirst = lessonId === 'lesson_numerom_intro';
      setIsFirstLesson(isFirst);

      // Используем разные endpoints для первого урока и остальных
      const endpoint = isFirst
        ? `${backendUrl}/api/lessons/first-lesson`
        : `${backendUrl}/api/admin/lessons/${lessonId}`;

      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setIsCreatingNew(false);
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

  // Начать создание нового урока (копирует первый урок)
  const startCreatingNewLesson = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      // Загружаем структуру первого урока
      const firstLessonResponse = await fetch(`${backendUrl}/api/lessons/first-lesson`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!firstLessonResponse.ok) {
        alert('Не удалось загрузить структуру первого урока');
        return;
      }

      const firstLessonData = await firstLessonResponse.json();
      const firstLesson = firstLessonData.lesson;

      // Создаем шаблон нового урока на основе первого
      const newLessonId = `lesson_${Date.now()}`;
      const newLessonTemplate = {
        id: newLessonId,
        title: '',
        module: 'numerology',
        description: '',
        points_required: 0,
        is_active: true,
        content: JSON.parse(JSON.stringify(firstLesson.content)), // Deep copy
        video_path: null,
        pdf_path: null,
        additional_pdfs: [],
        video_file_id: null,
        video_filename: null,
        pdf_file_id: null,
        pdf_filename: null
      };

      // Генерируем уникальные ID для челленджа и других элементов
      if (newLessonTemplate.content.challenge) {
        newLessonTemplate.content.challenge.id = `challenge_${newLessonId}`;
      }
      if (newLessonTemplate.content.quiz) {
        newLessonTemplate.content.quiz.id = `quiz_${newLessonId}`;
      }

      setIsCreatingNew(true);
      setIsFirstLesson(false);
      setEditingLesson(newLessonTemplate);
      setLessonContent(newLessonTemplate.content || {});
      setActiveTab('lesson-editor');
    } catch (err) {
      console.error('Ошибка загрузки первого урока:', err);
      alert('Ошибка загрузки первого урока');
    } finally {
      setLoading(false);
    }
  };

  // Синхронизация первого урока с БД
  const syncFirstLesson = async () => {
    try {
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
        alert(data.message);
        loadLessons();
      } else {
        alert('Ошибка синхронизации');
      }
    } catch (err) {
      console.error('Ошибка синхронизации:', err);
      alert('Ошибка синхронизации');
    }
  };

  // ==================== СОХРАНЕНИЕ ДАННЫХ ====================

  // Сохранение секции контента (для первого урока - специальный endpoint)
  const saveContentSection = async (section, field, value) => {
    if (!editingLesson) return;

    try {
      setSaving(true);
      const token = localStorage.getItem('token');

      // Универсальный endpoint для ВСЕХ уроков
      const formData = new FormData();
      formData.append('lesson_id', editingLesson.id);
      formData.append('section', section);
      formData.append('field', field);
      formData.append('value', value);

      const response = await fetch(`${backendUrl}/api/admin/update-lesson-content`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        // Обновляем локальное состояние
        setLessonContent(prev => ({
          ...prev,
          [section]: {
            ...prev[section],
            [field]: value
          }
        }));
      } else {
        const errorData = await response.json();
        console.error('Ошибка сохранения:', errorData);

        // Обработка pydantic validation errors
        let errorMessage = 'Ошибка сохранения';
        if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail.map(err => `${err.loc?.join('.')}: ${err.msg}`).join('\n');
        } else if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail;
        } else {
          errorMessage = JSON.stringify(errorData.detail);
        }

        alert(errorMessage);
      }
    } catch (err) {
      console.error('Ошибка сохранения:', err);
      alert('Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  // Сохранение всего урока (создание или обновление)
  const saveLesson = async () => {
    if (!editingLesson) return;

    // Валидация для нового урока
    if (isCreatingNew) {
      if (!editingLesson.title || !editingLesson.title.trim()) {
        alert('Введите название урока');
        return;
      }
    }

    // Нельзя сохранить первый урок через этот метод
    if (isFirstLesson && !isCreatingNew) {
      alert('Первый урок редактируется через специальные endpoints');
      return;
    }

    try {
      setSaving(true);
      const token = localStorage.getItem('token');

      const lessonData = {
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
      };

      let response;

      if (isCreatingNew) {
        // СОЗДАНИЕ НОВОГО УРОКА
        // Используем ID который уже был создан и использован для challenge/quiz ID
        lessonData.id = editingLesson.id;
        lessonData.created_at = new Date().toISOString();

        response = await fetch(`${backendUrl}/api/admin/lessons/create`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(lessonData)
        });
      } else {
        // ОБНОВЛЕНИЕ СУЩЕСТВУЮЩЕГО УРОКА
        response = await fetch(`${backendUrl}/api/admin/lessons/${editingLesson.id}`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(lessonData)
        });
      }

      if (response.ok) {
        if (isCreatingNew) {
          alert('Урок успешно создан на основе первого урока!');
          setIsCreatingNew(false);
        } else {
          alert('Урок успешно обновлен!');
        }

        setActiveTab('lessons-list');
        setEditingLesson(null);
        loadLessons();
      } else {
        const errorData = await response.json();
        alert(`Ошибка сохранения урока: ${errorData.detail || 'Неизвестная ошибка'}`);
      }
    } catch (err) {
      console.error('Ошибка сохранения урока:', err);
      alert('Ошибка сохранения урока');
    } finally {
      setSaving(false);
    }
  };

  // Удаление урока
  const deleteLesson = async (lessonId) => {
    if (lessonId === 'lesson_numerom_intro') {
      alert('Первый урок нельзя удалить!');
      return;
    }

    if (!window.confirm('Вы уверены, что хотите удалить этот урок?')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${backendUrl}/api/admin/lessons/${lessonId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        alert('Урок успешно удален');
        loadLessons();
      } else {
        alert('Ошибка удаления урока');
      }
    } catch (err) {
      console.error('Ошибка удаления:', err);
      alert('Ошибка удаления урока');
    }
  };

  // ==================== УПРАВЛЕНИЕ УПРАЖНЕНИЯМИ ====================

  const addExercise = async (exerciseData) => {
    if (!editingLesson || !exerciseData.title.trim()) {
      alert('Заполните название упражнения');
      return;
    }

    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();

      formData.append('lesson_id', editingLesson.id);
      formData.append('title', exerciseData.title);
      formData.append('content', exerciseData.content);
      formData.append('instructions', exerciseData.instructions);
      formData.append('expected_outcome', exerciseData.expected_outcome);
      formData.append('exercise_type', exerciseData.type);

      const response = await fetch(`${backendUrl}/api/admin/add-exercise`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        alert('Упражнение добавлено успешно!');
        // Перезагружаем урок
        loadLessonForEditing(editingLesson.id);
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

  const updateExercise = async (exerciseData) => {
    if (!editingLesson || !exerciseData.title.trim() || !exerciseData.id) {
      alert('Заполните название упражнения');
      return;
    }

    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();

      // Debug: выводим данные которые отправляем
      console.log('Updating exercise:', {
        lesson_id: editingLesson.id,
        exercise_id: exerciseData.id,
        title: exerciseData.title,
        content: exerciseData.content,
        instructions: exerciseData.instructions,
        expected_outcome: exerciseData.expected_outcome,
        exercise_type: exerciseData.type
      });

      formData.append('lesson_id', editingLesson.id);
      formData.append('exercise_id', exerciseData.id);
      formData.append('title', exerciseData.title);
      formData.append('content', exerciseData.content || '');
      formData.append('instructions', exerciseData.instructions || '');
      formData.append('expected_outcome', exerciseData.expected_outcome || '');
      formData.append('exercise_type', exerciseData.type || 'reflection');

      const response = await fetch(`${backendUrl}/api/admin/update-exercise`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        alert('Упражнение обновлено успешно!');
        // Перезагружаем урок
        loadLessonForEditing(editingLesson.id);
      } else {
        const errorData = await response.json();
        console.error('Error updating exercise:', errorData);
        console.error('Error details:', JSON.stringify(errorData, null, 2));
        alert(JSON.stringify(errorData.detail || errorData, null, 2));
      }
    } catch (err) {
      console.error('Ошибка обновления упражнения:', err);
      alert('Ошибка обновления упражнения: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  // ==================== УПРАВЛЕНИЕ ТЕСТАМИ ====================

  const addQuizQuestion = async (questionData) => {
    if (!editingLesson || !questionData.question.trim()) {
      alert('Заполните вопрос');
      return;
    }

    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();

      formData.append('lesson_id', editingLesson.id);
      formData.append('question_text', questionData.question);
      formData.append('options', questionData.options.filter(opt => opt.trim()).join('\n'));
      formData.append('correct_answer', questionData.correct_answer);
      formData.append('explanation', questionData.explanation);

      const response = await fetch(`${backendUrl}/api/admin/add-quiz-question`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        alert('Вопрос добавлен успешно!');
        // Перезагружаем урок
        loadLessonForEditing(editingLesson.id);
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

  const updateQuizQuestion = async (questionData) => {
    if (!editingLesson || !questionData.question.trim() || !questionData.id) {
      alert('Заполните вопрос');
      return;
    }

    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();

      formData.append('lesson_id', editingLesson.id);
      formData.append('question_id', questionData.id);
      formData.append('question_text', questionData.question);
      formData.append('options', questionData.options.filter(opt => opt.trim()).join('\n'));
      formData.append('correct_answer', questionData.correct_answer);
      formData.append('explanation', questionData.explanation);

      const response = await fetch(`${backendUrl}/api/admin/update-quiz-question`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        alert('Вопрос обновлен успешно!');
        // Перезагружаем урок
        loadLessonForEditing(editingLesson.id);
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка обновления вопроса');
      }
    } catch (err) {
      console.error('Ошибка обновления вопроса:', err);
      alert('Ошибка обновления вопроса');
    } finally {
      setSaving(false);
    }
  };

  // ==================== УПРАВЛЕНИЕ ПРИВЫЧКАМИ ====================

  const addHabit = async (planet, habitData) => {
    if (!editingLesson || !habitData.habit.trim()) {
      alert('Заполните название привычки');
      return;
    }

    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();

      formData.append('lesson_id', editingLesson.id);
      formData.append('planet', planet);
      formData.append('habit', habitData.habit);
      formData.append('description', habitData.description);

      const response = await fetch(`${backendUrl}/api/admin/add-habit`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        alert('Привычка добавлена успешно!');
        // Перезагружаем урок
        loadLessonForEditing(editingLesson.id);
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка добавления привычки');
      }
    } catch (err) {
      console.error('Ошибка добавления привычки:', err);
      alert('Ошибка добавления привычки');
    } finally {
      setSaving(false);
    }
  };

  const updateHabit = async (planet, habitIndex, habitData) => {
    if (!editingLesson || !habitData.habit.trim()) {
      alert('Заполните название привычки');
      return;
    }

    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();

      formData.append('lesson_id', editingLesson.id);
      formData.append('planet', planet);
      formData.append('habit_index', habitIndex);
      formData.append('habit', habitData.habit);
      formData.append('description', habitData.description);

      const response = await fetch(`${backendUrl}/api/admin/update-habit-content`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        alert('Привычка обновлена успешно!');
        // Перезагружаем урок
        loadLessonForEditing(editingLesson.id);
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка обновления привычки');
      }
    } catch (err) {
      console.error('Ошибка обновления привычки:', err);
      alert('Ошибка обновления привычки');
    } finally {
      setSaving(false);
    }
  };

  const deleteHabit = async (planet, habitIndex) => {
    if (!editingLesson) return;

    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();

      formData.append('lesson_id', editingLesson.id);
      formData.append('planet', planet);
      formData.append('habit_index', habitIndex);

      const response = await fetch(`${backendUrl}/api/admin/delete-habit`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        alert('Привычка удалена успешно!');
        // Перезагружаем урок
        loadLessonForEditing(editingLesson.id);
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка удаления привычки');
      }
    } catch (err) {
      console.error('Ошибка удаления привычки:', err);
      alert('Ошибка удаления привычки');
    } finally {
      setSaving(false);
    }
  };

  // ==================== УПРАВЛЕНИЕ ДНЯМИ ЧЕЛЛЕНДЖА ====================

  const addChallengeDay = async (dayData) => {
    if (!editingLesson || !dayData.title.trim()) {
      alert('Заполните название дня');
      return;
    }

    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();

      const challengeId = lessonContent.challenge?.id || `challenge_${editingLesson.id}`;

      formData.append('lesson_id', editingLesson.id);
      formData.append('challenge_id', challengeId);
      formData.append('title', dayData.title);
      formData.append('tasks', Array.isArray(dayData.tasks) ? dayData.tasks.join('\n') : dayData.tasks);

      const response = await fetch(`${backendUrl}/api/admin/add-challenge-day`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        alert('День челленджа добавлен успешно!');
        // Перезагружаем урок
        loadLessonForEditing(editingLesson.id);
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка добавления дня');
      }
    } catch (err) {
      console.error('Ошибка добавления дня:', err);
      alert('Ошибка добавления дня');
    } finally {
      setSaving(false);
    }
  };

  const updateChallengeDay = async (dayData) => {
    if (!editingLesson || !dayData.title.trim() || !dayData.day) {
      alert('Заполните все поля дня');
      return;
    }

    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();

      const challengeId = lessonContent.challenge?.id || `challenge_${editingLesson.id}`;

      formData.append('lesson_id', editingLesson.id);
      formData.append('challenge_id', challengeId);
      formData.append('day', dayData.day);
      formData.append('title', dayData.title);
      formData.append('tasks', Array.isArray(dayData.tasks) ? dayData.tasks.join('\n') : dayData.tasks);

      const response = await fetch(`${backendUrl}/api/admin/update-challenge-day`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        alert('День челленджа обновлен успешно!');
        // Перезагружаем урок
        loadLessonForEditing(editingLesson.id);
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка обновления дня');
      }
    } catch (err) {
      console.error('Ошибка обновления дня:', err);
      alert('Ошибка обновления дня');
    } finally {
      setSaving(false);
    }
  };

  // ==================== ЗАГРУЗКА МЕДИА ====================

  const handleVideoUpload = async (event) => {
    const file = event.target.files[0];
    if (!file || !editingLesson) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploadingVideo(true);
      const token = localStorage.getItem('token');

      const endpoint = `${backendUrl}/api/admin/lessons/${editingLesson.id}/upload-video`;

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        setEditingLesson(prev => ({
          ...prev,
          video_file_id: data.file_id,
          video_filename: data.filename
        }));
        alert('Видео успешно загружено!');
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка загрузки видео');
      }
    } catch (err) {
      console.error('Ошибка загрузки видео:', err);
      alert('Ошибка загрузки видео');
    } finally {
      setUploadingVideo(false);
    }
  };

  const handlePDFUpload = async (event) => {
    const file = event.target.files[0];
    if (!file || !editingLesson) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploadingPDF(true);
      const token = localStorage.getItem('token');

      const endpoint = `${backendUrl}/api/admin/lessons/${editingLesson.id}/upload-pdf`;

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        setEditingLesson(prev => ({
          ...prev,
          pdf_file_id: data.file_id,
          pdf_filename: data.filename
        }));
        alert('PDF успешно загружен!');
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка загрузки PDF');
      }
    } catch (err) {
      console.error('Ошибка загрузки PDF:', err);
      alert('Ошибка загрузки PDF');
    } finally {
      setUploadingPDF(false);
    }
  };

  // ==================== РЕНДЕР ====================

  if (loading) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p>Загрузка...</p>
        </CardContent>
      </Card>
    );
  }

  // ==================== РЕНДЕР ====================

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <Card className="bg-gradient-to-r from-blue-600 to-purple-600">
        <CardHeader className="text-white">
          <CardTitle className="text-2xl flex items-center">
            <BookOpen className="w-6 h-6 mr-2" />
            Управление уроками NumerOM
          </CardTitle>
          <CardDescription className="text-white/90">
            Создание, редактирование и управление всеми уроками платформы
          </CardDescription>
        </CardHeader>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="lessons-list" className="flex items-center justify-center gap-1 sm:gap-2">
            <BookOpen className="w-4 h-4" />
            <span className="text-xs sm:text-sm">Список уроков</span>
          </TabsTrigger>
          <TabsTrigger value="lesson-editor" className="flex items-center justify-center gap-1 sm:gap-2" disabled={!editingLesson}>
            <Edit className="w-4 h-4" />
            <span className="text-xs sm:text-sm">{isCreatingNew ? 'Создание урока' : 'Редактирование'}</span>
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
                  <Button onClick={startCreatingNewLesson} className="w-full sm:w-auto">
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
                <p className="text-center text-gray-500 py-8">Нет доступных уроков</p>
              ) : (
                <div className="space-y-3">
                  {lessons.map((lesson) => (
                    <Card key={lesson.id} className="border border-gray-200">
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <h3 className="font-semibold">{lesson.title}</h3>
                              {lesson.id === 'lesson_numerom_intro' && (
                                <Badge className="bg-yellow-500">Первый урок</Badge>
                              )}
                              <Badge variant={lesson.is_active ? 'default' : 'secondary'}>
                                {lesson.is_active ? 'Активен' : 'Неактивен'}
                              </Badge>
                            </div>
                            <p className="text-sm text-gray-600">{lesson.description || 'Без описания'}</p>
                            <p className="text-xs text-gray-500 mt-1">
                              Модуль: {lesson.module} • Баллы: {lesson.points_required || 0}
                            </p>
                          </div>
                          <div className="flex gap-2 ml-4">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => loadLessonForEditing(lesson.id)}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            {lesson.id !== 'lesson_numerom_intro' && (
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={() => deleteLesson(lesson.id)}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            )}
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

        {/* РЕДАКТОР УРОКА - продолжение в следующем сообщении */}
        <TabsContent value="lesson-editor" className="space-y-6">
          {editingLesson ? (
            <div className="space-y-6">
              {/* Основная информация об уроке */}
              <Card>
                <CardHeader>
                  <CardTitle>
                    {isCreatingNew ? 'Создание нового урока на основе первого' :
                     isFirstLesson ? 'Редактирование первого урока' :
                     `Редактирование: ${editingLesson.title}`}
                  </CardTitle>
                  <CardDescription>
                    {isCreatingNew ? 'Заполните основную информацию и отредактируйте содержимое урока' :
                     isFirstLesson ? 'Первый урок - базовый шаблон для всех остальных уроков' :
                     `Модуль: ${editingLesson.module} • Баллы: ${editingLesson.points_required || 0}`}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>Название урока *</Label>
                      <Input
                        value={editingLesson.title || ''}
                        onChange={(e) => setEditingLesson({...editingLesson, title: e.target.value})}
                        placeholder="Введите название урока"
                        className={isCreatingNew && !editingLesson.title ? 'border-red-300' : ''}
                        disabled={isFirstLesson}
                      />
                    </div>

                    <div>
                      <Label>Модуль</Label>
                      <select
                        className="w-full p-2 border rounded-md"
                        value={editingLesson.module || 'numerology'}
                        onChange={(e) => setEditingLesson({...editingLesson, module: e.target.value})}
                        disabled={isFirstLesson}
                      >
                        <option value="numerology">Нумерология</option>
                        <option value="advanced">Продвинутый уровень</option>
                        <option value="practical">Практические занятия</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <Label>Описание</Label>
                    <textarea
                      className="w-full p-2 border rounded-md"
                      rows="2"
                      value={editingLesson.description || ''}
                      onChange={(e) => setEditingLesson({...editingLesson, description: e.target.value})}
                      placeholder="Краткое описание урока"
                      disabled={isFirstLesson}
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>Требуемые баллы для доступа</Label>
                      <Input
                        type="number"
                        min="0"
                        value={editingLesson.points_required || 0}
                        onChange={(e) => setEditingLesson({...editingLesson, points_required: parseInt(e.target.value) || 0})}
                        disabled={isFirstLesson}
                      />
                    </div>

                    <div className="flex items-center space-x-2 pt-6">
                      <input
                        type="checkbox"
                        id="is_active_edit"
                        checked={editingLesson.is_active !== false}
                        onChange={(e) => setEditingLesson({...editingLesson, is_active: e.target.checked})}
                        disabled={isFirstLesson}
                      />
                      <Label htmlFor="is_active_edit">Урок активен</Label>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Вложенные табы для редактирования контента */}
              <Tabs value={activeSection} onValueChange={setActiveSection} className="space-y-6">
                <TabsList className="grid w-full grid-cols-2 lg:grid-cols-5">
                  <TabsTrigger value="theory">Теория</TabsTrigger>
                  <TabsTrigger value="exercises">Упражнения</TabsTrigger>
                  <TabsTrigger value="quiz">Тест</TabsTrigger>
                  <TabsTrigger value="challenge">Челлендж</TabsTrigger>
                  <TabsTrigger value="habits">Привычки</TabsTrigger>
                </TabsList>

                {/* Теория */}
                <TabsContent value="theory">
                  <LessonTheoryEditor
                    lessonContent={lessonContent}
                    isFirstLesson={isFirstLesson}
                    onSave={saveContentSection}
                    lessonId={editingLesson.id}
                  />
                </TabsContent>

                {/* Упражнения */}
                <TabsContent value="exercises">
                  <LessonExercisesEditor
                    lessonContent={lessonContent}
                    onAddExercise={addExercise}
                    onUpdateExercise={updateExercise}
                    saving={saving}
                  />
                </TabsContent>

                {/* Тест */}
                <TabsContent value="quiz">
                  <LessonQuizEditor
                    lessonContent={lessonContent}
                    onAddQuestion={addQuizQuestion}
                    onUpdateQuestion={updateQuizQuestion}
                    saving={saving}
                  />
                </TabsContent>

                {/* Челлендж */}
                <TabsContent value="challenge">
                  <LessonChallengeEditor
                    lessonContent={lessonContent}
                    onSave={saveContentSection}
                    onAddDay={addChallengeDay}
                    onUpdateDay={updateChallengeDay}
                    lessonId={editingLesson.id}
                    saving={saving}
                  />
                </TabsContent>

                {/* Привычки */}
                <TabsContent value="habits">
                  <LessonHabitsEditor
                    habitTracker={editingLesson?.habit_tracker}
                    onAddHabit={addHabit}
                    onUpdateHabit={updateHabit}
                    onDeleteHabit={deleteHabit}
                    saving={saving}
                  />
                </TabsContent>
              </Tabs>

              {/* Медиа файлы - отдельно от вложенных табов */}
              <LessonMediaEditor
                editingLesson={editingLesson}
                onVideoUpload={handleVideoUpload}
                onPDFUpload={handlePDFUpload}
                uploadingVideo={uploadingVideo}
                uploadingPDF={uploadingPDF}
              />

              {/* Кнопки сохранения и отмены */}
              <div className="pt-4 border-t flex gap-3">
                <Button
                  onClick={saveLesson}
                  disabled={saving || (isCreatingNew && !editingLesson.title)}
                  className="flex-1"
                >
                  <Save className="w-4 h-4 mr-2" />
                  {saving ? 'Сохранение...' : (isCreatingNew ? 'Создать урок' : (isFirstLesson ? 'Изменения сохранены автоматически' : 'Сохранить изменения'))}
                </Button>
                <Button
                  onClick={() => {
                    setActiveTab('lessons-list');
                    setEditingLesson(null);
                    setIsCreatingNew(false);
                    setIsFirstLesson(false);
                  }}
                  disabled={saving}
                  variant="outline"
                >
                  {isFirstLesson ? 'Закрыть' : 'Отмена'}
                </Button>
              </div>

            </div>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <BookOpen className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-600">Выберите урок для редактирования</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default UnifiedLessonEditor;
