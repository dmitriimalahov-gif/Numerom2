import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  Upload, 
  FileText, 
  Users, 
  Settings, 
  Eye, 
  Edit3, 
  Save, 
  X, 
  Plus, 
  Minus,
  TrendingUp,
  Award,
  User,
  Calendar,
  CreditCard,
  Video,
  Trash2,
  BookOpen,
  Brain,
  Target,
  Star,
  Zap,
  PlayCircle,
  Lightbulb,
  Download
} from 'lucide-react';
import { useAuth } from './AuthContext';
import EnhancedVideoViewer from './EnhancedVideoViewer';
import ConsultationPDFViewer from './ConsultationPDFViewer';
import LessonAdmin from './LessonAdmin';
import MultipleLessonAdmin from './MultipleLessonAdmin';

const AdminPanel = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingCredits, setEditingCredits] = useState({});
  const [selectedUserProgress, setSelectedUserProgress] = useState(null);
  const [selectedUserDetails, setSelectedUserDetails] = useState(null);
  const [loadingUserDetails, setLoadingUserDetails] = useState(false);
  const [materials, setMaterials] = useState([]);
  const [loadingMaterials, setLoadingMaterials] = useState(false);
  const [editingMaterial, setEditingMaterial] = useState(null);
  const [uploadingVideo, setUploadingVideo] = useState(false);
  const [managingUserRoles, setManagingUserRoles] = useState(false);
  
  // State for lessons management
  const [lessons, setLessons] = useState([]);
  const [loadingLessons, setLoadingLessons] = useState(false);
  const [editingLesson, setEditingLesson] = useState(null);
  const [creatingLesson, setCreatingLesson] = useState(false);
  
  // State for lesson editor
  const [lessonContent, setLessonContent] = useState({});
  const [savingContent, setSavingContent] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState({
    video: null,
    pdf: null
  });
  
  // State for additional PDFs management
  const [additionalPdfs, setAdditionalPdfs] = useState([]);
  const [loadingAdditionalPdfs, setLoadingAdditionalPdfs] = useState(false);
  const [uploadingAdditionalPdf, setUploadingAdditionalPdf] = useState(false);
  
  // State for additional videos management
  const [additionalVideos, setAdditionalVideos] = useState([]);
  const [loadingAdditionalVideos, setLoadingAdditionalVideos] = useState(false);
  const [uploadingAdditionalVideo, setUploadingAdditionalVideo] = useState(false);
  
  // State for lesson editor navigation
  const [activeLessonTab, setActiveLessonTab] = useState('theory');
  
  // State for exercises editing
  const [customExercises, setCustomExercises] = useState([]);
  const [editingExercise, setEditingExercise] = useState(null);
  const [addingExercise, setAddingExercise] = useState(false);
  
  // State for quiz editing
  const [customQuizQuestions, setCustomQuizQuestions] = useState([]);
  const [editingQuestion, setEditingQuestion] = useState(null);
  const [addingQuestion, setAddingQuestion] = useState(false);
  
  // State for challenge editing
  const [customChallengeDays, setCustomChallengeDays] = useState([]);
  const [editingDay, setEditingDay] = useState(null);
  const [addingDay, setAddingDay] = useState(false);
  
  // State for theory sections management
  const [customTheorySections, setCustomTheorySections] = useState([]);
  const [editingTheorySection, setEditingTheorySection] = useState(null);
  const [addingTheorySection, setAddingTheorySection] = useState(false);
  const [selectedTheoryPreview, setSelectedTheoryPreview] = useState(null);
  
  // State for consultations management
  const [consultations, setConsultations] = useState([]);
  const [loadingConsultations, setLoadingConsultations] = useState(false);
  const [editingConsultation, setEditingConsultation] = useState(null);
  
  // State for modal viewers (как в PersonalConsultations)
  const [selectedLessonVideo, setSelectedLessonVideo] = useState(null);
  const [selectedLessonPDF, setSelectedLessonPDF] = useState(null);

  // Поиск пользователей
  const [userSearchTerm, setUserSearchTerm] = useState('');
  const [consultationUserSearchTerm, setConsultationUserSearchTerm] = useState('');

  // Фильтрация пользователей
  const filteredUsers = users.filter(user => 
    userSearchTerm === '' || 
    user.email?.toLowerCase().includes(userSearchTerm.toLowerCase()) ||
    user.full_name?.toLowerCase().includes(userSearchTerm.toLowerCase())
  );

  const filteredUsersForConsultation = users.filter(user => 
    consultationUserSearchTerm === '' || 
    user.email?.toLowerCase().includes(consultationUserSearchTerm.toLowerCase()) ||
    user.full_name?.toLowerCase().includes(consultationUserSearchTerm.toLowerCase())
  );

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  // Загрузка пользователей
  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${backendUrl}/api/admin/users`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUsers(data.users);
      }
    } catch (error) {
      console.error('Ошибка загрузки пользователей:', error);
    } finally {
      setLoading(false);
    }
  };

  // Обновление кредитов пользователя
  const updateUserCredits = async (userId, newCredits) => {
    try {
      const response = await fetch(`${backendUrl}/api/admin/users/${userId}/credits`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ credits_remaining: parseInt(newCredits) })
      });
      
      if (response.ok) {
        // Обновляем локальное состояние
        setUsers(users.map(u => 
          u.id === userId ? { ...u, credits_remaining: parseInt(newCredits) } : u
        ));
        setEditingCredits(prev => ({ ...prev, [userId]: false }));
      }
    } catch (error) {
      console.error('Ошибка обновления кредитов:', error);
    }
  };

  // Загрузка прогресса уроков пользователя
  const fetchUserProgress = async (userId) => {
    try {
      const response = await fetch(`${backendUrl}/api/admin/users/${userId}/lessons`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSelectedUserProgress(data);
      }
    } catch (error) {
      console.error('Ошибка загрузки прогресса:', error);
    }
  };

  // Загрузка материалов
  const fetchMaterials = async () => {
    setLoadingMaterials(true);
    try {
      const response = await fetch(`${backendUrl}/api/admin/materials`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setMaterials(data.materials);
      }
    } catch (error) {
      console.error('Ошибка загрузки материалов:', error);
    } finally {
      setLoadingMaterials(false);
    }
  };

  // Сохранение материала
  const saveMaterial = async () => {
    // Валидация
    if (!editingMaterial.title?.trim()) {
      alert('Пожалуйста, введите название урока');
      return;
    }

    try {
      const method = editingMaterial.isNew ? 'POST' : 'PUT';
      const url = editingMaterial.isNew 
        ? `${backendUrl}/api/admin/materials`
        : `${backendUrl}/api/admin/materials/${editingMaterial.id}`;

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: editingMaterial.title,
          description: editingMaterial.description,
          content: editingMaterial.content,
          video_url: editingMaterial.video_url,
          video_file: editingMaterial.video_file,
          quiz_questions: editingMaterial.quiz_questions || [],
          order: editingMaterial.order || 0,
          is_active: editingMaterial.is_active !== false
        })
      });

      if (response.ok) {
        setEditingMaterial(null);
        fetchMaterials();
        alert(`Материал успешно ${editingMaterial.isNew ? 'создан' : 'обновлен'}`);
      } else {
        const errorData = await response.json().catch(() => ({}));
        alert(`Ошибка сохранения: ${errorData.detail || 'Неизвестная ошибка'}`);
      }
    } catch (error) {
      console.error('Ошибка сохранения материала:', error);
      alert('Ошибка при сохранении материала');
    }
  };

  // Удаление материала
  const deleteMaterial = async (materialId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот материал?')) return;

    try {
      const response = await fetch(`${backendUrl}/api/admin/materials/${materialId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        fetchMaterials();
      }
    } catch (error) {
      console.error('Ошибка удаления материала:', error);
    }
  };

  // Загрузка видео
  const handleVideoUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingVideo(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // УНИФИКАЦИЯ: используем тот же endpoint что и для консультаций/уроков - РАБОТАЮЩИЙ!
      const response = await fetch(`${backendUrl}/api/admin/consultations/upload-video`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        
        if (editingMaterial) {
          // Для материалов - сохраняем file_id как в PersonalConsultations
          setEditingMaterial(prev => ({
            ...prev,
            video_file_id: result.file_id,  // Изменено с video_file на video_file_id
            video_filename: result.filename, // Добавляем filename для отображения
            video_url: '', // Очищаем video_url при загрузке файла
            file_url: ''   // Очищаем file_url
          }));
          alert('Видео успешно загружено!');
        } else if (editingLesson) {
          // Для уроков
          setEditingLesson(prev => ({
            ...prev,
            video_file_id: result.file_id,
            video_filename: result.filename
          }));
          alert('Видео успешно загружено!');
        }
      } else {
        alert('Ошибка загрузки видео');
      }
    } catch (error) {
      console.error('Ошибка загрузки видео:', error);
      alert('Ошибка загрузки видео');
    } finally {
      setUploadingVideo(false);
    }
  };

  // Загрузка видео для консультации
  const handleConsultationVideoUpload = async (event) => {
    const file = event.target.files[0];

    console.log('=== FRONTEND: НАЧАЛО ЗАГРУЗКИ ВИДЕО ===');
    console.log('Файл:', file);
    console.log('Имя файла:', file?.name);
    console.log('Тип файла:', file?.type);
    console.log('Размер файла:', file?.size, 'байт', file ? `(${(file.size / 1024 / 1024).toFixed(2)} MB)` : '');

    if (!file) {
      console.error('ОШИБКА: Файл не выбран!');
      return;
    }

    setUploadingVideo(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      console.log('FormData создан, файл добавлен');
      console.log('Отправляем запрос на:', `${backendUrl}/api/admin/consultations/upload-video`);

      const response = await fetch(`${backendUrl}/api/admin/consultations/upload-video`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      console.log('Ответ получен. Статус:', response.status, response.statusText);

      if (response.ok) {
        const result = await response.json();
        console.log('✅ УСПЕХ! Результат:', result);
        setEditingConsultation(prev => ({
          ...prev,
          video_file_id: result.file_id,
          video_filename: result.filename
        }));
        alert(`Видео успешно загружено: ${result.filename}`);
      } else {
        const errorText = await response.text();
        console.error('❌ ОШИБКА от сервера:', errorText);
        alert(`Ошибка загрузки видео: ${errorText}`);
      }
    } catch (error) {
      console.error('❌ КРИТИЧЕСКАЯ ОШИБКА при загрузке:', error);
      alert(`Ошибка загрузки видео: ${error.message}`);
    } finally {
      setUploadingVideo(false);
      console.log('=== FRONTEND: ЗАВЕРШЕНИЕ ЗАГРУЗКИ ===');
    }
  };

  // Загрузка PDF для консультации
  const handleConsultationPDFUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingVideo(true); // Используем тот же флаг для loading состояния

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${backendUrl}/api/admin/consultations/upload-pdf`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        setEditingConsultation(prev => ({
          ...prev,
          pdf_file_id: result.file_id,
          pdf_filename: result.filename
        }));
      } else {
        alert('Ошибка загрузки PDF');
      }
    } catch (error) {
      console.error('Ошибка загрузки PDF консультации:', error);
    } finally {
      setUploadingVideo(false);
    }
  };

  // Загрузка субтитров для консультации
  const handleConsultationSubtitlesUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingVideo(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${backendUrl}/api/admin/consultations/upload-subtitles`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        setEditingConsultation(prev => ({
          ...prev,
          subtitles_file_id: result.file_id,
          subtitles_filename: result.filename
        }));
      } else {
        alert('Ошибка загрузки субтитров');
      }
    } catch (error) {
      console.error('Ошибка загрузки субтитров консультации:', error);
    } finally {
      setUploadingVideo(false);
    }
  };

  // Загрузка видео файла для урока (ТОЧНАЯ КОПИЯ ИЗ КОНСУЛЬТАЦИЙ)
  const handleLessonVideoUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingVideo(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Используем тот же endpoint что и для консультаций - РАБОТАЮЩИЙ!
      const response = await fetch(`${backendUrl}/api/admin/consultations/upload-video`, {
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
          video_file_id: result.file_id,
          video_filename: result.filename
        }));
        alert('Видео успешно загружено!');
      } else {
        alert('Ошибка загрузки видео');
      }
    } catch (error) {
      console.error('Ошибка загрузки видео урока:', error);
      alert('Ошибка загрузки видео');
    } finally {
      setUploadingVideo(false);
    }
  };

  const handleLessonPDFUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingVideo(true); // Используем тот же флаг для loading состояния

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Используем тот же endpoint что и для консультаций - РАБОТАЮЩИЙ!
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

  // Загрузка субтитров для урока (копия из консультаций)
  const handleLessonSubtitlesUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingVideo(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${backendUrl}/api/admin/consultations/upload-subtitles`, {
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
          subtitles_file_id: result.file_id,
          subtitles_filename: result.filename
        }));
      } else {
        alert('Ошибка загрузки субтитров для урока');
      }
    } catch (error) {
      console.error('Ошибка загрузки субтитров урока:', error);
    } finally {
      setUploadingVideo(false);
    }
  };

  // ==================== ADDITIONAL PDFS FUNCTIONS ====================

  // Загрузка дополнительных PDF файлов урока
  const loadAdditionalPdfs = async () => {
    const lessonId = lessonContent?.id || 'lesson_numerom_intro'; // Используем fallback ID
    
    setLoadingAdditionalPdfs(true);
    try {
      const response = await fetch(`${backendUrl}/api/lessons/${lessonId}/additional-pdfs`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAdditionalPdfs(data.additional_pdfs || []);
      } else {
        console.error('Ошибка загрузки дополнительных PDF');
        setAdditionalPdfs([]);
      }
    } catch (error) {
      console.error('Ошибка загрузки дополнительных PDF:', error);
      setAdditionalPdfs([]);
    } finally {
      setLoadingAdditionalPdfs(false);
    }
  };

  // Загрузка дополнительного PDF файла
  const handleAdditionalPdfUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Запрос названия PDF у пользователя
    const pdfTitle = prompt('Введите название для PDF файла:', file.name.replace('.pdf', ''));
    if (!pdfTitle) return;

    setUploadingAdditionalPdf(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', pdfTitle);

      const response = await fetch(`${backendUrl}/api/admin/lessons/${lessonContent.id}/add-pdf`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        alert(`PDF "${pdfTitle}" успешно добавлен к уроку!`);
        
        // Обновляем список дополнительных PDF
        loadAdditionalPdfs();
        
        // Очищаем input
        event.target.value = '';
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка загрузки PDF');
      }
    } catch (error) {
      console.error('Ошибка загрузки дополнительного PDF:', error);
      alert('Ошибка загрузки PDF');
    } finally {
      setUploadingAdditionalPdf(false);
    }
  };

  // Удаление дополнительного PDF файла
  const handleDeleteAdditionalPdf = async (fileId, title) => {
    if (!window.confirm(`Вы уверены, что хотите удалить PDF "${title}"?`)) return;

    try {
      const response = await fetch(`${backendUrl}/api/admin/lessons/pdf/${fileId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        alert(`PDF "${title}" успешно удален!`);
        // Обновляем список дополнительных PDF
        loadAdditionalPdfs();
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка удаления PDF');
      }
    } catch (error) {
      console.error('Ошибка удаления дополнительного PDF:', error);
      alert('Ошибка удаления PDF');
    }
  };

  // Удаление всех дополнительных PDF файлов урока
  const handleDeleteAllAdditionalPdfs = async () => {
    if (additionalPdfs.length === 0) {
      alert('Нет PDF файлов для удаления');
      return;
    }

    const confirmed = window.confirm(
      `Вы уверены, что хотите удалить ВСЕ дополнительные PDF файлы (${additionalPdfs.length} шт.)? Это действие нельзя отменить!`
    );
    
    if (!confirmed) return;

    try {
      let successCount = 0;
      let errorCount = 0;
      
      // Удаляем все PDF файлы по одному
      for (const pdf of additionalPdfs) {
        try {
          const response = await fetch(`${backendUrl}/api/admin/lessons/pdf/${pdf.file_id}`, {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          });

          if (response.ok) {
            successCount++;
          } else {
            errorCount++;
            console.error(`Ошибка удаления PDF ${pdf.title}`);
          }
        } catch (error) {
          errorCount++;
          console.error(`Ошибка удаления PDF ${pdf.title}:`, error);
        }
      }
      
      // Показываем результат
      if (errorCount === 0) {
        alert(`Успешно удалено ${successCount} PDF файлов!`);
      } else {
        alert(`Удалено ${successCount} файлов, ошибок: ${errorCount}. Обновите список для актуального состояния.`);
      }
      
      // Обновляем список дополнительных PDF
      loadAdditionalPdfs();
      
    } catch (error) {
      console.error('Ошибка массового удаления PDF:', error);
      alert('Произошла ошибка при удалении PDF файлов');
    }
  };

  // ==================== ADDITIONAL VIDEOS FUNCTIONS ====================

  // Загрузка дополнительных видео файлов урока
  const loadAdditionalVideos = async () => {
    const lessonId = lessonContent?.id || 'lesson_numerom_intro'; // Используем fallback ID
    
    setLoadingAdditionalVideos(true);
    try {
      const response = await fetch(`${backendUrl}/api/lessons/${lessonId}/additional-videos`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAdditionalVideos(data.additional_videos || []);
      } else {
        console.error('Ошибка загрузки дополнительных видео');
        setAdditionalVideos([]);
      }
    } catch (error) {
      console.error('Ошибка загрузки дополнительных видео:', error);
      setAdditionalVideos([]);
    } finally {
      setLoadingAdditionalVideos(false);
    }
  };

  // Загрузка дополнительного видео файла
  const handleAdditionalVideoUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Запрос названия видео у пользователя
    const videoTitle = prompt('Введите название для видео файла:', file.name.replace(/\.[^/.]+$/, ''));
    if (!videoTitle) return;

    setUploadingAdditionalVideo(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', videoTitle);

      const response = await fetch(`${backendUrl}/api/admin/lessons/${lessonContent.id}/add-video`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Видео "${videoTitle}" успешно добавлено к уроку!`);
        
        // Обновляем список дополнительных видео
        loadAdditionalVideos();
        
        // Очищаем input
        event.target.value = '';
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка загрузки видео');
      }
    } catch (error) {
      console.error('Ошибка загрузки дополнительного видео:', error);
      alert('Ошибка загрузки видео');
    } finally {
      setUploadingAdditionalVideo(false);
    }
  };

  // Удаление дополнительного видео файла
  const handleDeleteAdditionalVideo = async (fileId, title) => {
    if (!window.confirm(`Вы уверены, что хотите удалить видео "${title}"?`)) return;

    try {
      const response = await fetch(`${backendUrl}/api/admin/lessons/video/${fileId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        alert(`Видео "${title}" успешно удалено!`);
        // Обновляем список дополнительных видео
        loadAdditionalVideos();
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка удаления видео');
      }
    } catch (error) {
      console.error('Ошибка удаления дополнительного видео:', error);
      alert('Ошибка удаления видео');
    }
  };

  // Удаление всех дополнительных видео файлов урока
  const handleDeleteAllAdditionalVideos = async () => {
    if (additionalVideos.length === 0) {
      alert('Нет видео файлов для удаления');
      return;
    }

    const confirmed = window.confirm(
      `Вы уверены, что хотите удалить ВСЕ дополнительные видео файлы (${additionalVideos.length} шт.)? Это действие нельзя отменить!`
    );
    
    if (!confirmed) return;

    try {
      let successCount = 0;
      let errorCount = 0;
      
      // Удаляем все видео файлы по одному
      for (const video of additionalVideos) {
        try {
          const response = await fetch(`${backendUrl}/api/admin/lessons/video/${video.file_id}`, {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          });

          if (response.ok) {
            successCount++;
          } else {
            errorCount++;
            console.error(`Ошибка удаления видео ${video.title}`);
          }
        } catch (error) {
          errorCount++;
          console.error(`Ошибка удаления видео ${video.title}:`, error);
        }
      }
      
      // Показываем результат
      if (errorCount === 0) {
        alert(`Успешно удалено ${successCount} видео файлов!`);
      } else {
        alert(`Удалено ${successCount} файлов, ошибок: ${errorCount}. Обновите список для актуального состояния.`);
      }
      
      // Обновляем список дополнительных видео
      loadAdditionalVideos();
      
    } catch (error) {
      console.error('Ошибка массового удаления видео:', error);
      alert('Произошла ошибка при удалении видео файлов');
    }
  };

  // ==================== LESSON EDITOR FUNCTIONS ====================

  // Загрузка содержимого урока для редактирования
  const loadLessonContent = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/admin/lesson-content/lesson_numerom_intro`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setLessonContent(data.lesson);
        setCustomExercises(data.custom_exercises || []);
        setCustomQuizQuestions(data.custom_quiz_questions || []);
        setCustomChallengeDays(data.custom_challenge_days || []);
        
        // Загружаем кастомные разделы теории
        loadCustomTheorySections();
        
        // Загружаем дополнительные PDF и видео файлы
        if (data.lesson && data.lesson.id) {
          setTimeout(() => {
            loadAdditionalPdfs();
            loadAdditionalVideos();
          }, 100); // Небольшая задержка для установки ID урока
        }
      }
    } catch (err) {
      console.error('Ошибка загрузки контента урока:', err);
    }
  };

  // Сохранение изменений контента урока
  const saveLessonContent = async (section, field, value) => {
    try {
      setSavingContent(true);
      
      const response = await fetch(`${backendUrl}/api/admin/update-lesson-content`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          lesson_id: 'lesson_numerom_intro',
          section,
          field,
          value
        })
      });

      if (response.ok) {
        // Обновить локальное состояние
        setLessonContent(prev => ({
          ...prev,
          [section]: {
            ...prev[section],
            [field]: value
          }
        }));
        alert('Контент успешно сохранен');
      } else {
        alert('Ошибка сохранения контента');
      }
    } catch (err) {
      console.error('Ошибка сохранения:', err);
      alert('Ошибка сохранения контента');
    } finally {
      setSavingContent(false);
    }
  };

  // Функции для работы с упражнениями
  const saveExercise = async (exerciseData, isNew = false) => {
    try {
      setSavingContent(true);
      const endpoint = isNew ? '/api/admin/add-exercise' : '/api/admin/update-exercise';
      
      const formData = new FormData();
      formData.append('lesson_id', 'lesson_numerom_intro');
      if (!isNew) formData.append('exercise_id', exerciseData.exercise_id);
      formData.append('title', exerciseData.title);
      formData.append('content', exerciseData.content);
      formData.append('instructions', exerciseData.instructions.join('\n'));
      formData.append('expected_outcome', exerciseData.expected_outcome);
      formData.append('exercise_type', exerciseData.type);

      const response = await fetch(`${backendUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (response.ok) {
        await loadLessonContent();
        setEditingExercise(null);
        setAddingExercise(false);
        alert('Упражнение успешно сохранено');
      } else {
        alert('Ошибка сохранения упражнения');
      }
    } catch (err) {
      console.error('Ошибка сохранения упражнения:', err);
      alert('Ошибка сохранения упражнения');
    } finally {
      setSavingContent(false);
    }
  };

  // Функции для работы с вопросами квиза
  const saveQuizQuestion = async (questionData, isNew = false) => {
    try {
      setSavingContent(true);
      const endpoint = isNew ? '/api/admin/add-quiz-question' : '/api/admin/update-quiz-question';
      
      const formData = new FormData();
      formData.append('lesson_id', 'lesson_numerom_intro');
      if (!isNew) formData.append('question_id', questionData.question_id);
      formData.append('question_text', questionData.question);
      formData.append('options', questionData.options.join('\n'));
      formData.append('correct_answer', questionData.correct_answer);
      formData.append('explanation', questionData.explanation);

      const response = await fetch(`${backendUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (response.ok) {
        await loadLessonContent();
        setEditingQuestion(null);
        setAddingQuestion(false);
        alert('Вопрос успешно сохранен');
      } else {
        alert('Ошибка сохранения вопроса');
      }
    } catch (err) {
      console.error('Ошибка сохранения вопроса:', err);
      alert('Ошибка сохранения вопроса');
    } finally {
      setSavingContent(false);
    }
  };

  // Функции для работы с днями челленджа
  const saveChallengeDay = async (dayData, isNew = false) => {
    try {
      setSavingContent(true);
      const endpoint = isNew ? '/api/admin/add-challenge-day' : '/api/admin/update-challenge-day';
      
      const formData = new FormData();
      formData.append('lesson_id', 'lesson_numerom_intro');
      formData.append('challenge_id', 'challenge_sun_7days');
      if (!isNew) formData.append('day', dayData.day);
      formData.append('title', dayData.title);
      formData.append('tasks', dayData.tasks.join('\n'));

      const response = await fetch(`${backendUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (response.ok) {
        await loadLessonContent();
        setEditingDay(null);
        setAddingDay(false);
        alert('День челленджа успешно сохранен');
      } else {
        alert('Ошибка сохранения дня челленджа');
      }
    } catch (err) {
      console.error('Ошибка сохранения дня челленджа:', err);
      alert('Ошибка сохранения дня челленджа');
    } finally {
      setSavingContent(false);
    }
  };

  // ==================== THEORY MANAGEMENT FUNCTIONS ====================
  
  // Сохранение раздела теории
  const saveTheorySection = async (sectionData, isNew = false) => {
    if (!sectionData.title || !sectionData.content) {
      alert('Заполните название и содержание раздела');
      return;
    }

    setSavingContent(true);
    try {
      if (sectionData.isBase) {
        // Сохранение базового раздела через существующий API
        await saveLessonContent('content.theory', sectionData.type, sectionData.content);
        alert('Базовый раздел теории сохранен!');
      } else {
        // Сохранение кастомного раздела
        const endpoint = isNew 
          ? `${backendUrl}/api/admin/add-theory-section`
          : `${backendUrl}/api/admin/update-theory-section`;
          
        const payload = isNew 
          ? { 
              title: sectionData.title,
              content: sectionData.content,
              lesson_id: lessonContent.id || 'lesson_numerom_intro'
            }
          : { 
              section_id: sectionData.id,
              title: sectionData.title,
              content: sectionData.content
            };

        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify(payload)
        });

        if (response.ok) {
          const result = await response.json();
          
          if (isNew) {
            // Добавляем новый раздел в список
            const newSection = {
              id: result.section_id,
              title: sectionData.title,
              content: sectionData.content,
              created_at: new Date().toISOString()
            };
            setCustomTheorySections(prev => [...prev, newSection]);
          } else {
            // Обновляем существующий раздел
            setCustomTheorySections(prev => 
              prev.map(section => 
                section.id === sectionData.id 
                  ? { ...section, title: sectionData.title, content: sectionData.content }
                  : section
              )
            );
          }
          
          alert(isNew ? 'Новый раздел теории создан!' : 'Раздел теории обновлен!');
        } else {
          const errorData = await response.json();
          alert(errorData.detail || 'Ошибка сохранения раздела');
        }
      }
      
      // Закрываем форму редактирования
      setEditingTheorySection(null);
      setAddingTheorySection(false);
      
    } catch (err) {
      console.error('Ошибка сохранения раздела теории:', err);
      alert('Ошибка сохранения раздела теории');
    } finally {
      setSavingContent(false);
    }
  };

  // Удаление кастомного раздела теории
  const deleteTheorySection = async (sectionId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот раздел теории?')) return;

    try {
      const response = await fetch(`${backendUrl}/api/admin/delete-theory-section/${sectionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        setCustomTheorySections(prev => prev.filter(section => section.id !== sectionId));
        alert('Раздел теории удален!');
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка удаления раздела');
      }
    } catch (error) {
      console.error('Ошибка удаления раздела теории:', error);
      alert('Ошибка удаления раздела');
    }
  };

  // Загрузка кастомных разделов теории
  const loadCustomTheorySections = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/admin/theory-sections`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setCustomTheorySections(data.theory_sections || []);
      } else {
        console.error('Ошибка загрузки разделов теории');
        setCustomTheorySections([]);
      }
    } catch (error) {
      console.error('Ошибка загрузки разделов теории:', error);
      setCustomTheorySections([]);
    }
  };

  // ==================== END THEORY MANAGEMENT ====================

  // ==================== EXERCISES MANAGEMENT ====================
  
  // Удаление кастомного упражнения
  const deleteExercise = async (exerciseId) => {
    if (!window.confirm('Вы уверены, что хотите удалить это упражнение?')) return;

    try {
      const response = await fetch(`${backendUrl}/api/admin/delete-exercise/${exerciseId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        setCustomExercises(prev => prev.filter(exercise => exercise.exercise_id !== exerciseId));
        alert('Упражнение удалено!');
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка удаления упражнения');
      }
    } catch (error) {
      console.error('Ошибка удаления упражнения:', error);
      alert('Ошибка удаления упражнения');
    }
  };

  // ==================== QUIZ MANAGEMENT ====================

  // Удаление кастомного вопроса теста
  const deleteQuizQuestion = async (questionId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот вопрос?')) return;

    try {
      const response = await fetch(`${backendUrl}/api/admin/delete-quiz-question/${questionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        setCustomQuizQuestions(prev => prev.filter(question => question.question_id !== questionId));
        alert('Вопрос теста удален!');
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка удаления вопроса');
      }
    } catch (error) {
      console.error('Ошибка удаления вопроса:', error);
      alert('Ошибка удаления вопроса');
    }
  };

  // ==================== CHALLENGE MANAGEMENT ====================

  // Удаление кастомного дня челленджа
  const deleteChallengeDay = async (dayNumber) => {
    if (!window.confirm(`Вы уверены, что хотите удалить День ${dayNumber} челленджа?`)) return;

    try {
      const response = await fetch(`${backendUrl}/api/admin/delete-challenge-day/${dayNumber}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        setCustomChallengeDays(prev => prev.filter(day => day.day !== dayNumber));
        alert(`День ${dayNumber} челленджа удален!`);
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка удаления дня челленджа');
      }
    } catch (error) {
      console.error('Ошибка удаления дня челленджа:', error);
      alert('Ошибка удаления дня челленджа');
    }
  };

  // ==================== END CONTENT MANAGEMENT ====================

  const handlePdfUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingVideo(true); // reuse the same loading state

    const formData = new FormData();
    formData.append('file', file);

    try {
      // УНИФИКАЦИЯ: используем тот же endpoint что и для консультаций - РАБОТАЮЩИЙ!
      const response = await fetch(`${backendUrl}/api/admin/consultations/upload-pdf`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        setEditingMaterial({
          ...editingMaterial,
          pdf_file_id: result.file_id,     // Изменено с file_url на pdf_file_id
          pdf_filename: result.filename,   // Добавляем filename для отображения
          video_url: '',     // clear video fields when uploading PDF
          video_file_id: '', // Изменено с video_file на video_file_id
          video_filename: ''
        });
        alert('PDF успешно загружен!');
      } else {
        alert('Ошибка загрузки PDF');
      }
    } catch (error) {
      console.error('Ошибка загрузки PDF:', error);
      alert('Ошибка загрузки PDF');
    } finally {
      setUploadingVideo(false);
    }
  };

  // Управление ролями пользователей (только для super admin)
  const grantAdminRights = async (userId) => {
    try {
      const response = await fetch(`${backendUrl}/api/admin/make-admin/${userId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`Права администратора предоставлены: ${result.user_email}`);
        fetchUsers(); // Refresh the users list
      } else {
        const errorData = await response.json().catch(() => ({}));
        alert(`Ошибка при предоставлении прав: ${errorData.detail || 'Неизвестная ошибка'}`);
      }
    } catch (error) {
      console.error('Ошибка предоставления прав:', error);
      alert('Ошибка при предоставлении прав администратора');
    }
  };

  const revokeAdminRights = async (userId) => {
    if (!window.confirm('Вы уверены, что хотите отозвать права администратора?')) return;

    try {
      const response = await fetch(`${backendUrl}/api/admin/revoke-admin/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`Права администратора отозваны: ${result.user_email}`);
        fetchUsers(); // Refresh the users list
      } else {
        const errorData = await response.json().catch(() => ({}));
        alert(`Ошибка при отзыве прав: ${errorData.detail || 'Неизвестная ошибка'}`);
      }
    } catch (error) {
      console.error('Ошибка отзыва прав:', error);
      alert('Ошибка при отзыве прав администратора');
    }
  };

  const deleteUser = async (userId) => {
    const userToDelete = users.find(u => u.id === userId);
    const userName = userToDelete ? `${userToDelete.name || userToDelete.email}` : 'пользователя';
    
    if (!window.confirm(`Вы уверены, что хотите ПОЛНОСТЬЮ УДАЛИТЬ ${userName}? Это действие нельзя отменить! Будут удалены все данные пользователя.`)) return;

    try {
      const response = await fetch(`${backendUrl}/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        alert(`Пользователь ${userName} успешно удален`);
        fetchUsers(); // Обновляем список пользователей
      } else {
        const errorData = await response.json().catch(() => ({}));
        alert(`Ошибка при удалении пользователя: ${errorData.detail || 'Неизвестная ошибка'}`);
      }
    } catch (error) {
      console.error('Ошибка удаления пользователя:', error);
      alert('Ошибка при удалении пользователя');
    }
  };

  // Функции для работы с вопросами теста
  const addQuizQuestion = () => {
    const newQuestion = {
      question: '',
      options: ['', '', '', ''],
      correct: 0
    };
    setEditingMaterial({
      ...editingMaterial,
      quiz_questions: [...(editingMaterial.quiz_questions || []), newQuestion]
    });
  };

  const removeQuizQuestion = (index) => {
    const questions = [...(editingMaterial.quiz_questions || [])];
    questions.splice(index, 1);
    setEditingMaterial({...editingMaterial, quiz_questions: questions});
  };

  const updateQuizQuestion = (index, field, value) => {
    const questions = [...(editingMaterial.quiz_questions || [])];
    questions[index] = {...questions[index], [field]: value};
    setEditingMaterial({...editingMaterial, quiz_questions: questions});
  };

  const updateQuizOption = (questionIndex, optionIndex, value) => {
    const questions = [...(editingMaterial.quiz_questions || [])];
    questions[questionIndex].options[optionIndex] = value;
    setEditingMaterial({...editingMaterial, quiz_questions: questions});
  };

  const addQuizOption = (questionIndex) => {
    const questions = [...(editingMaterial.quiz_questions || [])];
    questions[questionIndex].options.push('');
    setEditingMaterial({...editingMaterial, quiz_questions: questions});
  };

  useEffect(() => {
    if (activeTab === 'users') {
      fetchUsers();
    } else if (activeTab === 'consultations') {
      fetchConsultations();
      fetchUsers(); // Загружаем пользователей для выбора в консультациях
    }
  }, [activeTab]);

  // Functions for lessons management
  const fetchLessons = async () => {
    setLoadingLessons(true);
    try {
      const response = await fetch(`${backendUrl}/api/admin/lessons`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setLessons(data);
      }
    } catch (error) {
      console.error('Error fetching lessons:', error);
    } finally {
      setLoadingLessons(false);
    }
  };

  const createLesson = async (lessonData) => {
    try {
      const response = await fetch(`${backendUrl}/api/admin/lessons`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(lessonData)
      });
      
      if (response.ok) {
        const result = await response.json();
        const lessonId = result.lesson_id;
        
        // Автоматически генерируем Quiz для созданного урока
        try {
          const quizResponse = await fetch(`${backendUrl}/api/learning/generate-quiz`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              lesson_id: lessonId,
              video_url: lessonData.video_url,
              video_file_id: lessonData.video_file_id
            })
          });
          
          if (quizResponse.ok) {
            const quizData = await quizResponse.json();
            
            // Сохраняем сгенерированный Quiz в урок
            await fetch(`${backendUrl}/api/admin/lessons/${lessonId}`, {
              method: 'PUT',
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                ...lessonData,
                quiz_questions: quizData.questions
              })
            });
            
            console.log('Quiz автоматически сгенерирован для урока:', lessonId);
          }
        } catch (quizError) {
          console.error('Ошибка генерации Quiz:', quizError);
        }
        
        fetchLessons();
        setCreatingLesson(false);
        setEditingLesson(null);
        alert('Занятие успешно создано с автоматически сгенерированным тестом!');
      } else {
        alert('Ошибка при создании занятия');
      }
    } catch (error) {
      console.error('Error creating lesson:', error);
      alert('Ошибка при создании занятия');
    }
  };

  const updateLesson = async (lessonId, lessonData) => {
    try {
      const response = await fetch(`${backendUrl}/api/admin/lessons/${lessonId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(lessonData)
      });
      
      if (response.ok) {
        fetchLessons();
        setEditingLesson(null);
        alert('Занятие успешно обновлено!');
      } else {
        alert('Ошибка при обновлении занятия');
      }
    } catch (error) {
      console.error('Error updating lesson:', error);
      alert('Ошибка при обновлении занятия');
    }
  };

  const deleteLesson = async (lessonId) => {
    if (!confirm('Удалить это занятие?')) return;
    
    try {
      const response = await fetch(`${backendUrl}/api/admin/lessons/${lessonId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        fetchLessons();
        alert('Занятие удалено!');
      } else {
        alert('Ошибка при удалении занятия');
      }
    } catch (error) {
      console.error('Error deleting lesson:', error);
      alert('Ошибка при удалении занятия');
    }
  };

  // Functions for consultations management
  const fetchConsultations = async () => {
    setLoadingConsultations(true);
    try {
      const response = await fetch(`${backendUrl}/api/admin/consultations`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setConsultations(data);
      }
    } catch (error) {
      console.error('Error fetching consultations:', error);
    } finally {
      setLoadingConsultations(false);
    }
  };

  const createConsultation = async (consultationData) => {
    try {
      const response = await fetch(`${backendUrl}/api/admin/consultations`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(consultationData)
      });
      
      if (response.ok) {
        fetchConsultations();
        setEditingConsultation(null);
        alert('Консультация успешно создана!');
      } else {
        alert('Ошибка при создании консультации');
      }
    } catch (error) {
      console.error('Error creating consultation:', error);
      alert('Ошибка при создании консультации');
    }
  };

  // ДОБАВЛЯЮ функцию обновления консультации - КРИТИЧНО ДЛЯ ИСПРАВЛЕНИЯ БАГА!
  const updateConsultation = async (consultationId, consultationData) => {
    try {
      const response = await fetch(`${backendUrl}/api/admin/consultations/${consultationId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(consultationData)
      });
      
      if (response.ok) {
        fetchConsultations(); // Обновляем список консультаций
        setEditingConsultation(null);
        alert('Консультация успешно обновлена! Студент увидит новые материалы.');
      } else {
        const errorData = await response.json();
        alert(`Ошибка при обновлении консультации: ${errorData.detail || 'Неизвестная ошибка'}`);
      }
    } catch (error) {
      console.error('Error updating consultation:', error);
      alert('Ошибка при обновлении консультации');
    }
  };

  const deleteConsultation = async (consultationId) => {
    if (!confirm('Удалить эту консультацию?')) return;
    
    try {
      const response = await fetch(`${backendUrl}/api/admin/consultations/${consultationId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        fetchConsultations();
        alert('Консультация удалена!');
      } else {
        alert('Ошибка при удалении консультации');
      }
    } catch (error) {
      console.error('Error deleting consultation:', error);
      alert('Ошибка при удалении консультации');
    }
  };

  // Функция для получения детальных данных пользователя
  const fetchUserDetails = async (userId) => {
    if (!userId) {
      setSelectedUserDetails(null);
      return;
    }

    setLoadingUserDetails(true);
    try {
      const response = await fetch(`${backendUrl}/api/admin/users/${userId}/details`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const userDetails = await response.json();
        setSelectedUserDetails(userDetails);
      } else {
        console.error('Error fetching user details');
        setSelectedUserDetails(null);
      }
    } catch (error) {
      console.error('Error fetching user details:', error);
      setSelectedUserDetails(null);
    } finally {
      setLoadingUserDetails(false);
    }
  };

  // Function to render consultations tab
  const renderConsultationsTab = () => (
    <div className="space-y-6">
      {/* Header with Create Button */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <h3 className="text-base sm:text-lg font-semibold">Личные консультации</h3>
        <Button
          onClick={() => {
            setEditingConsultation({
              isNew: true,
              title: '',
              description: '',
              video_file: '',
              assigned_user_id: '',
              cost_credits: 10000,
              is_active: true,
              expires_at: ''
            });
          }}
          className="w-full sm:w-auto text-sm"
        >
          <Plus className="w-4 h-4 mr-2" />
          <span className="hidden sm:inline">Создать консультацию</span>
          <span className="sm:hidden">Создать</span>
        </Button>
      </div>

      {/* Форма редактирования консультации - ВВЕРХУ */}
      {editingConsultation && (
        <Card className="border-2 border-blue-500 shadow-lg">
          <CardHeader className="bg-blue-50">
            <CardTitle className="flex items-center justify-between text-blue-800">
              <span>{editingConsultation.isNew ? 'Создание консультации' : 'Редактирование консультации'}</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setEditingConsultation(null)}
              >
                ✕
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 p-6">
            {/* Поля формы */}
            <div>
              <Label>Название консультации</Label>
              <Input
                type="text"
                placeholder="Введите название консультации"
                value={editingConsultation.title || ''}
                onChange={(e) => setEditingConsultation({...editingConsultation, title: e.target.value})}
              />
            </div>

            <div>
              <Label>Стоимость (в кредитах)</Label>
              <Input
                type="number"
                placeholder="10000"
                value={editingConsultation.cost_credits || 10000}
                onChange={(e) => setEditingConsultation({...editingConsultation, cost_credits: parseInt(e.target.value)})}
              />
            </div>

            {/* Выбор ученика с поиском */}
            <div>
              <Label>Назначить ученику</Label>
              <div className="space-y-2">
                <Input
                  type="text"
                  placeholder="Поиск ученика по имени или email..."
                  value={consultationUserSearchTerm}
                  onChange={(e) => setConsultationUserSearchTerm(e.target.value)}
                  className="mb-2"
                />
                
                <select
                  className="w-full p-2 border rounded-md"
                  value={editingConsultation.assigned_user_id || ''}
                  onChange={(e) => {
                    const userId = e.target.value;
                    setEditingConsultation({...editingConsultation, assigned_user_id: userId});
                  }}
                >
                  <option value="">Выберите ученика</option>
                  {filteredUsersForConsultation.map(user => (
                    <option key={user.id} value={user.id}>
                      {user.full_name ? `${user.full_name} (${user.email})` : user.email}
                    </option>
                  ))}
                </select>

                {consultationUserSearchTerm && (
                  <p className="text-sm text-gray-600">
                    Найдено: {filteredUsersForConsultation.length} учеников
                  </p>
                )}
              </div>
            </div>

            <div>
              <Label>Описание консультации</Label>
              <textarea
                className="w-full p-2 border rounded-md"
                rows="4"
                placeholder="Описание консультации для студента"
                value={editingConsultation.description || ''}
                onChange={(e) => setEditingConsultation({...editingConsultation, description: e.target.value})}
              />
            </div>

            {/* Video Upload */}
            <div>
              <Label>Видео консультации</Label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                <input
                  type="file"
                  accept="video/*"
                  onChange={handleConsultationVideoUpload}
                  className="w-full"
                  disabled={uploadingVideo}
                />
                {uploadingVideo && <p className="text-sm text-blue-600 mt-2">Загружается видео...</p>}
                {editingConsultation.video_filename && (
                  <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded flex justify-between items-center">
                    <p className="text-sm text-green-600">✓ Видео: {editingConsultation.video_filename}</p>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => {
                        const videoUrl = editingConsultation.video_file_id 
                          ? `${backendUrl}/api/consultations/video/${editingConsultation.video_file_id}`
                          : editingConsultation.video_url;
                        setSelectedLessonVideo({
                          url: videoUrl,
                          title: `Предпросмотр: ${editingConsultation.title || 'Консультация'}`,
                          consultation: editingConsultation
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

            {/* PDF Upload */}
            <div>
              <Label>PDF материалы консультации</Label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={handleConsultationPDFUpload}
                  className="w-full"
                  disabled={uploadingVideo}
                />
                {uploadingVideo && <p className="text-sm text-blue-600 mt-2">Загружается PDF...</p>}
                {editingConsultation.pdf_filename && (
                  <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded flex justify-between items-center">
                    <p className="text-sm text-green-600">✓ PDF: {editingConsultation.pdf_filename}</p>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => {
                        setSelectedLessonPDF({
                          url: `${backendUrl}/api/consultations/pdf/${editingConsultation.pdf_file_id}`,
                          title: `PDF: ${editingConsultation.title || 'Консультация'}`,
                          consultation: editingConsultation
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

            {/* Кнопки действий */}
            <div className="flex justify-between">
              <Button 
                variant="outline"
                onClick={() => setEditingConsultation(null)}
              >
                Отмена
              </Button>
              <Button 
                onClick={() => {
                  const consultationData = {
                    title: editingConsultation.title,
                    description: editingConsultation.description,
                    assigned_user_id: editingConsultation.assigned_user_id,
                    cost_credits: editingConsultation.cost_credits,
                    video_file_id: editingConsultation.video_file_id,
                    video_filename: editingConsultation.video_filename,
                    pdf_file_id: editingConsultation.pdf_file_id,
                    pdf_filename: editingConsultation.pdf_filename,
                    subtitles_file_id: editingConsultation.subtitles_file_id,
                    subtitles_filename: editingConsultation.subtitles_filename,
                    is_active: editingConsultation.is_active !== false
                  };

                  if (editingConsultation.isNew) {
                    createConsultation(consultationData);
                  } else {
                    updateConsultation(editingConsultation.id, consultationData);
                  }
                }}
                disabled={!editingConsultation.title || !editingConsultation.assigned_user_id}
              >
                <Save className="w-4 h-4 mr-2" />
                {editingConsultation.isNew ? 'Создать консультацию' : 'Сохранить изменения'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Consultations List */}
      {loadingConsultations ? (
        <div className="text-center py-8">Загрузка консультаций...</div>
      ) : (
        <div className="grid gap-4">
          {consultations.map((consultation) => (
            <Card key={consultation.id}>
              <CardContent className="p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="font-semibold">{consultation.title}</h4>
                      <Badge variant={consultation.is_active ? "default" : "secondary"}>
                        {consultation.is_active ? "Активна" : "Неактивна"}
                      </Badge>
                      {consultation.is_purchased ? (
                        <Badge variant="default" className="bg-green-600">
                          💰 Куплена
                        </Badge>
                      ) : (
                        <Badge variant="outline">Не куплена</Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{consultation.description}</p>
                    
                    {/* Информация о покупателе */}
                    {consultation.is_purchased && consultation.buyer_details ? (
                      <div className="mt-3 p-3 bg-green-50 rounded-md border-l-4 border-green-400">
                        <h5 className="font-medium text-sm text-green-800 mb-2">🛒 Информация о покупателе:</h5>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-1 text-xs text-green-700">
                          <div><strong>Имя:</strong> {consultation.buyer_details.full_name}</div>
                          <div><strong>Email:</strong> {consultation.buyer_details.email}</div>
                          <div><strong>Дата рождения:</strong> {consultation.buyer_details.birth_date || 'Не указана'}</div>
                          <div><strong>Город:</strong> {consultation.buyer_details.city || 'Не указан'}</div>
                          <div><strong>Телефон:</strong> {consultation.buyer_details.phone || 'Не указан'}</div>
                          <div><strong>Адрес:</strong> {consultation.buyer_details.address || 'Не указан'}</div>
                          <div><strong>Потрачено баллов:</strong> {consultation.buyer_details.credits_spent}</div>
                          <div><strong>Дата покупки:</strong> {new Date(consultation.purchased_at).toLocaleString('ru-RU')}</div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs text-gray-500">
                        Назначена: {users.find(u => u.id === consultation.assigned_user_id)?.email || 'Пользователь не найден'} • 
                        Создана: {new Date(consultation.created_at).toLocaleDateString()}
                      </div>
                    )}

                    {/* Загруженные материалы - просмотр для админа */}
                    {(consultation.video_file_id || consultation.pdf_file_id) && (
                      <div className="mt-3 p-3 bg-blue-50 rounded-md border-l-4 border-blue-400">
                        <h5 className="font-medium text-sm text-blue-800 mb-2">📁 Загруженные материалы:</h5>
                        <div className="flex gap-2">
                          {consultation.video_file_id && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setSelectedLessonVideo({
                                  url: `${backendUrl}/api/consultations/video/${consultation.video_file_id}`,
                                  title: `Видео: ${consultation.title}`,
                                  consultation: consultation
                                });
                              }}
                              className="flex-1"
                            >
                              <PlayCircle className="w-4 h-4 mr-1" />
                              Смотреть видео
                            </Button>
                          )}
                          {consultation.pdf_file_id && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setSelectedLessonPDF({
                                  url: `${backendUrl}/api/consultations/pdf/${consultation.pdf_file_id}`,
                                  title: `PDF: ${consultation.title}`,
                                  consultation: consultation
                                });
                              }}
                              className="flex-1"
                            >
                              <FileText className="w-4 h-4 mr-1" />
                              Открыть PDF
                            </Button>
                          )}
                        </div>
                        {consultation.video_filename && (
                          <p className="text-xs text-blue-600 mt-1">Видео: {consultation.video_filename}</p>
                        )}
                        {consultation.pdf_filename && (
                          <p className="text-xs text-blue-600 mt-1">PDF: {consultation.pdf_filename}</p>
                        )}
                      </div>
                    )}

                    {/* Отсутствующие материалы */}
                    {!consultation.video_file_id && !consultation.pdf_file_id && (
                      <div className="mt-2 p-2 bg-yellow-50 rounded border-l-4 border-yellow-400">
                        <p className="text-xs text-yellow-700">⚠️ Материалы ещё не загружены. Нажмите "Редактировать" для загрузки.</p>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex flex-col gap-2">
                    {/* Кнопки управления */}
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setEditingConsultation({...consultation, isNew: false});
                        }}
                        title="Редактировать консультацию"
                      >
                        <Edit3 className="w-3 h-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => deleteConsultation(consultation.id)}
                        className="text-red-600 hover:text-red-800 hover:bg-red-50"
                        title="Удалить консультацию"
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>

                    {/* Индикатор стоимости */}
                    <div className="text-right">
                      <Badge variant="secondary" className="text-xs">
                        {consultation.cost_credits.toLocaleString()} баллов
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          
          {consultations.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <Video className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg">Консультаций пока нет</p>
              <p className="text-sm">Создайте персональную консультацию для студента</p>
            </div>
          )}
        </div>
      )}


    </div>
  );

  // Рендер редактора уроков
  const renderLessonEditor = () => {
    useEffect(() => {
      loadLessonContent();
    }, []);

    return (
      <div className="space-y-6">
        {/* Заголовок редактора */}
        <Card className="bg-gradient-to-r from-blue-600 to-purple-600">
          <CardHeader className="text-white">
            <CardTitle className="text-xl flex items-center">
              <BookOpen className="w-5 h-5 mr-2" />
              Редактор первого занятия NumerOM
            </CardTitle>
            <CardDescription className="text-white/90">
              Редактирование контента, загрузка материалов и управление уроком
            </CardDescription>
          </CardHeader>
        </Card>

        {/* Основные разделы редактора - УДОБНАЯ НАВИГАЦИЯ */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
          <Button
            variant={activeLessonTab === 'theory' ? 'default' : 'outline'}
            onClick={() => setActiveLessonTab('theory')}
            className="h-16 flex flex-col items-center justify-center gap-1"
          >
            <BookOpen className="w-5 h-5" />
            <span className="text-xs">Теория</span>
          </Button>
          
          <Button
            variant={activeLessonTab === 'exercises' ? 'default' : 'outline'}
            onClick={() => setActiveLessonTab('exercises')}
            className="h-16 flex flex-col items-center justify-center gap-1"
          >
            <Brain className="w-5 h-5" />
            <span className="text-xs">Упражнения</span>
          </Button>
          
          <Button
            variant={activeLessonTab === 'quiz' ? 'default' : 'outline'}
            onClick={() => setActiveLessonTab('quiz')}
            className="h-16 flex flex-col items-center justify-center gap-1"
          >
            <Target className="w-5 h-5" />
            <span className="text-xs">Тест</span>
          </Button>
          
          <Button
            variant={activeLessonTab === 'challenge' ? 'default' : 'outline'}
            onClick={() => setActiveLessonTab('challenge')}
            className="h-16 flex flex-col items-center justify-center gap-1"
          >
            <Zap className="w-5 h-5" />
            <span className="text-xs">Челлендж</span>
          </Button>
          
          <Button
            variant={activeLessonTab === 'additional-pdfs' ? 'default' : 'outline'}
            onClick={() => setActiveLessonTab('additional-pdfs')}
            className="h-16 flex flex-col items-center justify-center gap-1"
          >
            <FileText className="w-5 h-5" />
            <span className="text-xs">Доп. PDF</span>
          </Button>
          
          <Button
            variant={activeLessonTab === 'additional-videos' ? 'default' : 'outline'}
            onClick={() => setActiveLessonTab('additional-videos')}
            className="h-16 flex flex-col items-center justify-center gap-1"
          >
            <Video className="w-5 h-5" />
            <span className="text-xs">Доп. Видео</span>
          </Button>
        </div>

        {/* Контент разделов - УСЛОВНОЕ ОТОБРАЖЕНИЕ */}
        <Tabs value={activeLessonTab} onValueChange={setActiveLessonTab}>
        
        {/* УЛУЧШЕННЫЙ РАЗДЕЛ РЕДАКТИРОВАНИЯ ТЕОРИИ */}
        <TabsContent value="theory" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Edit3 className="w-5 h-5 mr-2" />
                    Управление теоретическим контентом
                  </div>
                  <Button 
                    onClick={() => setAddingTheorySection(true)}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Добавить раздел
                  </Button>
                </CardTitle>
                <CardDescription>
                  Управляйте разделами теории, которые студенты изучают в первом занятии
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                
                {/* Базовые разделы теории */}
                <div className="grid gap-4">
                  {/* Что такое нумерология */}
                  <div className="p-4 border rounded-lg bg-white">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center">
                        <BookOpen className="w-5 h-5 text-blue-600 mr-2" />
                        <h4 className="font-semibold">Что такое нумерология?</h4>
                        <Badge variant="outline" className="ml-2">Основной</Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => setEditingTheorySection({
                            type: 'what_is_numerology',
                            title: 'Что такое нумерология?',
                            content: lessonContent.content?.theory?.what_is_numerology || '',
                            isBase: true
                          })}
                        >
                          <Edit3 className="w-4 h-4 mr-1" />
                          Редактировать
                        </Button>
                        <Button
                          size="sm"
                          variant="outline" 
                          onClick={() => {
                            setSelectedTheoryPreview({
                              title: 'Что такое нумерология?',
                              content: lessonContent.content?.theory?.what_is_numerology || 'Контент не добавлен'
                            });
                          }}
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          Предпросмотр
                        </Button>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {lessonContent.content?.theory?.what_is_numerology || 'Описание нумерологии не добавлено...'}
                    </p>
                    <div className="flex items-center mt-2 text-xs text-gray-400">
                      <span>Символов: {(lessonContent.content?.theory?.what_is_numerology || '').length}</span>
                    </div>
                  </div>

                  {/* История космического корабля */}
                  <div className="p-4 border rounded-lg bg-white">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center">
                        <Zap className="w-5 h-5 text-purple-600 mr-2" />
                        <h4 className="font-semibold">История космического корабля</h4>
                        <Badge variant="outline" className="ml-2">Основной</Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => setEditingTheorySection({
                            type: 'cosmic_ship_story',
                            title: 'История космического корабля',
                            content: lessonContent.content?.theory?.cosmic_ship_story || '',
                            isBase: true
                          })}
                        >
                          <Edit3 className="w-4 h-4 mr-1" />
                          Редактировать
                        </Button>
                        <Button
                          size="sm"
                          variant="outline" 
                          onClick={() => {
                            setSelectedTheoryPreview({
                              title: 'История космического корабля',
                              content: lessonContent.content?.theory?.cosmic_ship_story || 'Контент не добавлен'
                            });
                          }}
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          Предпросмотр
                        </Button>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {lessonContent.content?.theory?.cosmic_ship_story || 'История о космическом корабле и планетах не добавлена...'}
                    </p>
                    <div className="flex items-center mt-2 text-xs text-gray-400">
                      <span>Символов: {(lessonContent.content?.theory?.cosmic_ship_story || '').length}</span>
                    </div>
                  </div>

                  {/* Планеты и числа */}
                  <div className="p-4 border rounded-lg bg-white">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center">
                        <Star className="w-5 h-5 text-yellow-600 mr-2" />
                        <h4 className="font-semibold">Соответствие планет и чисел</h4>
                        <Badge variant="outline" className="ml-2">Основной</Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => setEditingTheorySection({
                            type: 'planets_and_numbers',
                            title: 'Соответствие планет и чисел',
                            content: lessonContent.content?.theory?.planets_and_numbers || '',
                            isBase: true
                          })}
                        >
                          <Edit3 className="w-4 h-4 mr-1" />
                          Редактировать
                        </Button>
                        <Button
                          size="sm"
                          variant="outline" 
                          onClick={() => {
                            setSelectedTheoryPreview({
                              title: 'Соответствие планет и чисел',
                              content: lessonContent.content?.theory?.planets_and_numbers || 'Контент не добавлен'
                            });
                          }}
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          Предпросмотр
                        </Button>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {lessonContent.content?.theory?.planets_and_numbers || 'Описание соответствия планет и чисел не добавлено...'}
                    </p>
                    <div className="flex items-center mt-2 text-xs text-gray-400">
                      <span>Символов: {(lessonContent.content?.theory?.planets_and_numbers || '').length}</span>
                    </div>
                  </div>
                </div>

                {/* Кастомные разделы теории */}
                {customTheorySections.map((section, index) => (
                  <div key={section.id} className="p-4 border rounded-lg bg-green-50">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center">
                        <FileText className="w-5 h-5 text-green-600 mr-2" />
                        <h4 className="font-semibold">{section.title}</h4>
                        <Badge className="ml-2 bg-green-100 text-green-800">Кастомный</Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => setEditingTheorySection(section)}
                        >
                          <Edit3 className="w-4 h-4 mr-1" />
                          Редактировать
                        </Button>
                        <Button
                          size="sm"
                          variant="outline" 
                          onClick={() => {
                            setSelectedTheoryPreview({
                              title: section.title,
                              content: section.content || 'Контент не добавлен'
                            });
                          }}
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          Предпросмотр
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-red-600 hover:text-red-700"
                          onClick={() => deleteTheorySection(section.id)}
                        >
                          <Trash2 className="w-4 h-4 mr-1" />
                          Удалить
                        </Button>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {section.content || 'Контент раздела не добавлен...'}
                    </p>
                    <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
                      <span>Символов: {(section.content || '').length}</span>
                      <span>Создан: {new Date(section.created_at).toLocaleDateString('ru-RU')}</span>
                    </div>
                  </div>
                ))}

                {/* Информационная панель */}
                <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center">
                    <Lightbulb className="w-5 h-5 text-blue-600 mr-2" />
                    <div>
                      <h6 className="font-medium text-blue-900">Совет по управлению теорией</h6>
                      <p className="text-sm text-blue-700">
                        Базовые разделы нельзя удалить, но можно редактировать. Кастомные разделы можно полностью удалять. 
                        Используйте предпросмотр для проверки форматирования текста.
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Форма редактирования раздела теории */}
            {(editingTheorySection || addingTheorySection) && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Edit3 className="w-5 h-5 mr-2" />
                    {editingTheorySection ? 'Редактирование раздела теории' : 'Добавление раздела теории'}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {!editingTheorySection?.isBase && (
                    <div>
                      <Label className="font-medium">Название раздела</Label>
                      <Input
                        value={editingTheorySection?.title || ''}
                        onChange={(e) => setEditingTheorySection(prev => ({...prev, title: e.target.value}))}
                        placeholder="Название раздела теории"
                      />
                    </div>
                  )}

                  <div>
                    <Label className="font-medium">Содержание раздела</Label>
                    <textarea
                      value={editingTheorySection?.content || ''}
                      onChange={(e) => setEditingTheorySection(prev => ({...prev, content: e.target.value}))}
                      placeholder="Введите теоретический материал..."
                      className="w-full p-3 border rounded-lg min-h-48 text-sm"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Символов: {(editingTheorySection?.content || '').length}
                    </p>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      onClick={() => saveTheorySection(editingTheorySection, addingTheorySection)}
                      disabled={savingContent}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <Save className="w-4 h-4 mr-2" />
                      {savingContent ? 'Сохранение...' : 'Сохранить'}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setEditingTheorySection(null);
                        setAddingTheorySection(false);
                      }}
                    >
                      <X className="w-4 h-4 mr-2" />
                      Отмена
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Модальное окно предпросмотра теории */}
            {selectedTheoryPreview && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg p-6 max-w-2xl max-h-96 overflow-y-auto">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold">{selectedTheoryPreview.title}</h3>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setSelectedTheoryPreview(null)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                  <div className="prose prose-sm max-w-none">
                    <div className="whitespace-pre-wrap text-sm">
                      {selectedTheoryPreview.content}
                    </div>
                  </div>
                </div>
              </div>
            )}
        </TabsContent>

        {/* Остальные разделы для редактирования упражнений, квиза, челленджа */}
        <TabsContent value="exercises" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Brain className="w-5 h-5 mr-2" />
                    Редактирование упражнений
                  </div>
                  <Button 
                    onClick={() => setAddingExercise(true)}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Добавить упражнение
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Список базовых упражнений */}
                {lessonContent.exercises?.map((exercise, index) => (
                  <div key={exercise.id} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold">Упражнение {index + 1}: {exercise.title}</h4>
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => setEditingExercise(exercise)}
                      >
                        <Edit3 className="w-4 h-4 mr-1" />
                        Редактировать
                      </Button>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">Тип: {exercise.type}</p>
                    <p className="text-sm">{exercise.content?.slice(0, 100)}...</p>
                  </div>
                ))}

                {/* Список кастомных упражнений */}
                {customExercises.map((exercise, index) => (
                  <div key={exercise.exercise_id} className="p-4 border rounded-lg bg-blue-50">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold">
                        Кастом упражнение: {exercise.title}
                        <Badge className="ml-2 bg-blue-100 text-blue-800">Изменено</Badge>
                      </h4>
                      <div className="flex items-center gap-2">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => setEditingExercise(exercise)}
                        >
                          <Edit3 className="w-4 h-4 mr-1" />
                          Редактировать
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline"
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          onClick={() => deleteExercise(exercise.exercise_id)}
                        >
                          <Trash2 className="w-4 h-4 mr-1" />
                          Удалить
                        </Button>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">Тип: {exercise.type}</p>
                    <p className="text-sm">{exercise.content?.slice(0, 100)}...</p>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Форма редактирования упражнения */}
            {(editingExercise || addingExercise) && (
              <Card>
                <CardHeader>
                  <CardTitle>
                    {editingExercise ? 'Редактирование упражнения' : 'Добавление упражнения'}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label className="font-medium">Название упражнения</Label>
                    <Input
                      value={editingExercise?.title || ''}
                      onChange={(e) => setEditingExercise(prev => ({...prev, title: e.target.value}))}
                      placeholder="Введите название упражнения"
                    />
                  </div>

                  <div>
                    <Label className="font-medium">Тип упражнения</Label>
                    <select
                      value={editingExercise?.type || 'reflection'}
                      onChange={(e) => setEditingExercise(prev => ({...prev, type: e.target.value}))}
                      className="w-full p-2 border rounded-lg"
                    >
                      <option value="reflection">Рефлексия</option>
                      <option value="calculation">Расчеты</option>
                      <option value="meditation">Медитация</option>
                      <option value="practical">Практическое</option>
                    </select>
                  </div>

                  <div>
                    <Label className="font-medium">Содержание упражнения</Label>
                    <textarea
                      value={editingExercise?.content || ''}
                      onChange={(e) => setEditingExercise(prev => ({...prev, content: e.target.value}))}
                      placeholder="Описание упражнения"
                      className="w-full p-3 border rounded-lg min-h-32"
                    />
                  </div>

                  <div>
                    <Label className="font-medium">Инструкции (по одной на строку)</Label>
                    <textarea
                      value={editingExercise?.instructions?.join('\n') || ''}
                      onChange={(e) => setEditingExercise(prev => ({
                        ...prev, 
                        instructions: e.target.value.split('\n').filter(i => i.trim())
                      }))}
                      placeholder="Инструкция 1\nИнструкция 2\nИнструкция 3"
                      className="w-full p-3 border rounded-lg min-h-24"
                    />
                  </div>

                  <div>
                    <Label className="font-medium">Ожидаемый результат</Label>
                    <textarea
                      value={editingExercise?.expected_outcome || ''}
                      onChange={(e) => setEditingExercise(prev => ({...prev, expected_outcome: e.target.value}))}
                      placeholder="Что должно получиться в результате"
                      className="w-full p-3 border rounded-lg min-h-20"
                    />
                  </div>

                  <div className="flex gap-2">
                    <Button
                      onClick={() => saveExercise(editingExercise, addingExercise)}
                      disabled={savingContent}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <Save className="w-4 h-4 mr-2" />
                      {savingContent ? 'Сохранение...' : 'Сохранить'}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setEditingExercise(null);
                        setAddingExercise(false);
                      }}
                    >
                      <X className="w-4 h-4 mr-2" />
                      Отмена
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="quiz" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Target className="w-5 h-5 mr-2" />
                    Редактирование теста
                  </div>
                  <Button 
                    onClick={() => setAddingQuestion(true)}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Добавить вопрос
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Список базовых вопросов */}
                {lessonContent.quiz?.questions?.map((question, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold">Вопрос {index + 1}</h4>
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => setEditingQuestion({...question, question_id: `q${index + 1}`})}
                      >
                        <Edit3 className="w-4 h-4 mr-1" />
                        Редактировать
                      </Button>
                    </div>
                    <p className="text-sm">{question.question}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      Правильный ответ: {question.correct_answer}
                    </p>
                  </div>
                ))}

                {/* Список кастомных вопросов */}
                {customQuizQuestions.map((question, index) => (
                  <div key={question.question_id} className="p-4 border rounded-lg bg-blue-50">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold">
                        Кастом вопрос: {question.question_id}
                        <Badge className="ml-2 bg-blue-100 text-blue-800">Изменено</Badge>
                      </h4>
                      <div className="flex items-center gap-2">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => setEditingQuestion(question)}
                        >
                          <Edit3 className="w-4 h-4 mr-1" />
                          Редактировать
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline"
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          onClick={() => deleteQuizQuestion(question.question_id)}
                        >
                          <Trash2 className="w-4 h-4 mr-1" />
                          Удалить
                        </Button>
                      </div>
                    </div>
                    <p className="text-sm">{question.question}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      Правильный ответ: {question.correct_answer}
                    </p>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Форма редактирования вопроса */}
            {(editingQuestion || addingQuestion) && (
              <Card>
                <CardHeader>
                  <CardTitle>
                    {editingQuestion ? 'Редактирование вопроса' : 'Добавление вопроса'}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label className="font-medium">Текст вопроса</Label>
                    <textarea
                      value={editingQuestion?.question || ''}
                      onChange={(e) => setEditingQuestion(prev => ({...prev, question: e.target.value}))}
                      placeholder="Введите текст вопроса"
                      className="w-full p-3 border rounded-lg min-h-20"
                    />
                  </div>

                  <div>
                    <Label className="font-medium">Варианты ответов (по одному на строку)</Label>
                    <textarea
                      value={editingQuestion?.options?.join('\n') || ''}
                      onChange={(e) => setEditingQuestion(prev => ({
                        ...prev, 
                        options: e.target.value.split('\n').filter(o => o.trim())
                      }))}
                      placeholder="A) Первый вариант\nB) Второй вариант\nC) Третий вариант"
                      className="w-full p-3 border rounded-lg min-h-24"
                    />
                  </div>

                  <div>
                    <Label className="font-medium">Правильный ответ (буква)</Label>
                    <Input
                      value={editingQuestion?.correct_answer || ''}
                      onChange={(e) => setEditingQuestion(prev => ({...prev, correct_answer: e.target.value}))}
                      placeholder="A, B, C или D"
                      maxLength="1"
                    />
                  </div>

                  <div>
                    <Label className="font-medium">Объяснение</Label>
                    <textarea
                      value={editingQuestion?.explanation || ''}
                      onChange={(e) => setEditingQuestion(prev => ({...prev, explanation: e.target.value}))}
                      placeholder="Объяснение правильного ответа"
                      className="w-full p-3 border rounded-lg min-h-20"
                    />
                  </div>

                  <div className="flex gap-2">
                    <Button
                      onClick={() => saveQuizQuestion(editingQuestion, addingQuestion)}
                      disabled={savingContent}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <Save className="w-4 h-4 mr-2" />
                      {savingContent ? 'Сохранение...' : 'Сохранить'}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setEditingQuestion(null);
                        setAddingQuestion(false);
                      }}
                    >
                      <X className="w-4 h-4 mr-2" />
                      Отмена
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="challenge" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Zap className="w-5 h-5 mr-2" />
                    Редактирование челленджа
                  </div>
                  <Button 
                    onClick={() => setAddingDay(true)}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Добавить день
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Список базовых дней */}
                {lessonContent.challenges?.[0]?.daily_tasks?.map((day, index) => (
                  <div key={day.day} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold">День {day.day}: {day.title}</h4>
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => setEditingDay(day)}
                      >
                        <Edit3 className="w-4 h-4 mr-1" />
                        Редактировать
                      </Button>
                    </div>
                    <div className="text-sm">
                      <p className="text-gray-600">Задач: {day.tasks?.length || 0}</p>
                      <ul className="list-disc list-inside mt-1">
                        {day.tasks?.slice(0, 2).map((task, idx) => (
                          <li key={idx} className="text-xs text-gray-500">{task}</li>
                        ))}
                        {day.tasks?.length > 2 && (
                          <li className="text-xs text-gray-400">и еще {day.tasks.length - 2}...</li>
                        )}
                      </ul>
                    </div>
                  </div>
                ))}

                {/* Список кастомных дней */}
                {customChallengeDays.map((day, index) => (
                  <div key={day.day} className="p-4 border rounded-lg bg-blue-50">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold">
                        День {day.day}: {day.title}
                        <Badge className="ml-2 bg-blue-100 text-blue-800">Изменено</Badge>
                      </h4>
                      <div className="flex items-center gap-2">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => setEditingDay(day)}
                        >
                          <Edit3 className="w-4 h-4 mr-1" />
                          Редактировать
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline"
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          onClick={() => deleteChallengeDay(day.day)}
                        >
                          <Trash2 className="w-4 h-4 mr-1" />
                          Удалить
                        </Button>
                      </div>
                    </div>
                    <div className="text-sm">
                      <p className="text-gray-600">Задач: {day.tasks?.length || 0}</p>
                      <ul className="list-disc list-inside mt-1">
                        {day.tasks?.slice(0, 2).map((task, idx) => (
                          <li key={idx} className="text-xs text-gray-500">{task}</li>
                        ))}
                        {day.tasks?.length > 2 && (
                          <li className="text-xs text-gray-400">и еще {day.tasks.length - 2}...</li>
                        )}
                      </ul>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Форма редактирования дня челленджа */}
            {(editingDay || addingDay) && (
              <Card>
                <CardHeader>
                  <CardTitle>
                    {editingDay ? `Редактирование дня ${editingDay.day}` : 'Добавление дня'}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label className="font-medium">Название дня</Label>
                    <Input
                      value={editingDay?.title || ''}
                      onChange={(e) => setEditingDay(prev => ({...prev, title: e.target.value}))}
                      placeholder="Название дня челленджа"
                    />
                  </div>

                  <div>
                    <Label className="font-medium">Задачи дня (по одной на строку)</Label>
                    <textarea
                      value={editingDay?.tasks?.join('\n') || ''}
                      onChange={(e) => setEditingDay(prev => ({
                        ...prev, 
                        tasks: e.target.value.split('\n').filter(t => t.trim())
                      }))}
                      placeholder="Утренняя медитация\nВечерние аффирмации\nПрактика лидерства"
                      className="w-full p-3 border rounded-lg min-h-32"
                    />
                  </div>

                  <div className="flex gap-2">
                    <Button
                      onClick={() => saveChallengeDay(editingDay, addingDay)}
                      disabled={savingContent}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <Save className="w-4 h-4 mr-2" />
                      {savingContent ? 'Сохранение...' : 'Сохранить'}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setEditingDay(null);
                        setAddingDay(false);
                      }}
                    >
                      <X className="w-4 h-4 mr-2" />
                      Отмена
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* УЛУЧШЕННЫЙ РАЗДЕЛ ДОПОЛНИТЕЛЬНЫЕ PDF ФАЙЛЫ */}
          <TabsContent value="additional-pdfs" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center">
                    <FileText className="w-5 h-5 mr-2" />
                    Дополнительные PDF файлы к уроку
                    <Badge variant="secondary" className="ml-2">
                      {additionalPdfs.length} файлов
                    </Badge>
                  </div>
                  {additionalPdfs.length > 0 && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      onClick={() => handleDeleteAllAdditionalPdfs()}
                    >
                      <Trash2 className="w-4 h-4 mr-1" />
                      Удалить все
                    </Button>
                  )}
                </CardTitle>
                <CardDescription>
                  Управляйте дополнительными PDF файлами, которые студенты смогут просматривать во время урока
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                
                {/* Загрузка нового PDF */}
                <div className="border-2 border-dashed border-green-200 rounded-lg p-6 bg-green-50/30">
                  <div className="text-center">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
                      <Upload className="w-8 h-8 text-green-600" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Добавить PDF файл</h3>
                    <p className="text-sm text-gray-600 mb-4">
                      Поддерживаются файлы PDF (до 50MB)
                    </p>
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={handleAdditionalPdfUpload}
                      disabled={uploadingAdditionalPdf}
                      className="hidden"
                      id="additional-pdf-upload"
                    />
                    <label
                      htmlFor="additional-pdf-upload"
                      className={`inline-flex items-center px-6 py-3 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-700 cursor-pointer transition-colors ${
                        uploadingAdditionalPdf ? 'opacity-50 cursor-not-allowed' : ''
                      }`}
                    >
                      <FileText className="w-4 h-4 mr-2" />
                      {uploadingAdditionalPdf ? 'Загрузка...' : 'Выбрать PDF файл'}
                    </label>
                    {uploadingAdditionalPdf && (
                      <div className="mt-4">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div className="bg-green-600 h-2 rounded-full animate-pulse" style={{width: '60%'}}></div>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">Загружается PDF файл...</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Улучшенный список дополнительных PDF файлов */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-lg font-semibold text-gray-900">
                      Управление PDF файлами
                    </h4>
                    {additionalPdfs.length > 0 && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={loadAdditionalPdfs}
                        disabled={loadingAdditionalPdfs}
                      >
                        <Download className="w-4 h-4 mr-1" />
                        Обновить список
                      </Button>
                    )}
                  </div>
                  
                  {loadingAdditionalPdfs ? (
                    <div className="text-center py-12">
                      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">Загрузка PDF файлов</h3>
                      <p className="text-sm text-gray-500">Пожалуйста, подождите...</p>
                    </div>
                  ) : additionalPdfs.length > 0 ? (
                    <div className="grid gap-4">
                      {additionalPdfs.map((pdf, index) => (
                        <div key={pdf.file_id} className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
                          <div className="flex items-start justify-between">
                            <div className="flex items-start space-x-4 flex-1">
                              <div className="flex-shrink-0">
                                <div className="w-12 h-12 rounded-lg bg-green-100 flex items-center justify-center">
                                  <FileText className="w-6 h-6 text-green-600" />
                                </div>
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center space-x-2 mb-1">
                                  <h5 className="text-base font-semibold text-gray-900 truncate">{pdf.title}</h5>
                                  <Badge variant="outline" className="text-xs">
                                    #{index + 1}
                                  </Badge>
                                </div>
                                <p className="text-sm text-gray-600 mb-1">{pdf.filename}</p>
                                {pdf.uploaded_at && (
                                  <p className="text-xs text-gray-400">
                                    📅 Загружен: {new Date(pdf.uploaded_at).toLocaleDateString('ru-RU')} в {new Date(pdf.uploaded_at).toLocaleTimeString('ru-RU')}
                                  </p>
                                )}
                                <div className="flex items-center space-x-4 mt-2">
                                  <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full">
                                    ✅ Готов к просмотру
                                  </span>
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Button
                                size="sm"
                                variant="outline"
                                className="bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100"
                                onClick={() => {
                                  setSelectedLessonPDF({
                                    url: `${backendUrl}${pdf.pdf_url}`,
                                    title: pdf.title,
                                    description: `Предварительный просмотр дополнительного PDF "${pdf.title}"`
                                  });
                                }}
                              >
                                <Eye className="w-4 h-4 mr-1" />
                                Открыть
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                className="bg-purple-50 border-purple-200 text-purple-700 hover:bg-purple-100"
                                onClick={() => {
                                  const link = document.createElement('a');
                                  link.href = `${backendUrl}${pdf.pdf_url}`;
                                  link.download = pdf.filename;
                                  link.click();
                                }}
                              >
                                <Download className="w-4 h-4 mr-1" />
                                Скачать
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                className="bg-red-50 border-red-200 text-red-700 hover:bg-red-100"
                                onClick={() => handleDeleteAdditionalPdf(pdf.file_id, pdf.title)}
                              >
                                <Trash2 className="w-4 h-4 mr-1" />
                                Удалить
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                      
                      {/* Информационная панель */}
                      <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                        <div className="flex items-center">
                          <Lightbulb className="w-5 h-5 text-green-600 mr-2" />
                          <div>
                            <h6 className="font-medium text-green-900">Совет по управлению PDF</h6>
                            <p className="text-sm text-green-700">
                              PDF файлы автоматически становятся доступными студентам в FirstLesson. 
                              Используйте описательные названия для лучшей навигации.
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gray-100 mb-4">
                        <FileText className="w-10 h-10 text-gray-400" />
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">Нет PDF файлов</h3>
                      <p className="text-sm text-gray-500 mb-4">
                        Загрузите первый дополнительный PDF файл для этого урока
                      </p>
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 max-w-md mx-auto">
                        <div className="flex items-center">
                          <Star className="w-5 h-5 text-yellow-600 mr-2" />
                          <div className="text-left">
                            <h6 className="font-medium text-yellow-900">Рекомендация</h6>
                            <p className="text-sm text-yellow-700">
                              Добавьте справочные материалы, инструкции или дополнительную литературу
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* УЛУЧШЕННЫЙ РАЗДЕЛ ДОПОЛНИТЕЛЬНЫЕ ВИДЕО ФАЙЛЫ */}
          <TabsContent value="additional-videos" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Video className="w-5 h-5 mr-2" />
                    Дополнительные видео файлы к уроку
                    <Badge variant="secondary" className="ml-2">
                      {additionalVideos.length} файлов
                    </Badge>
                  </div>
                  {additionalVideos.length > 0 && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      onClick={() => handleDeleteAllAdditionalVideos()}
                    >
                      <Trash2 className="w-4 h-4 mr-1" />
                      Удалить все
                    </Button>
                  )}
                </CardTitle>
                <CardDescription>
                  Управляйте дополнительными видео файлами, которые студенты смогут просматривать во время урока
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                
                {/* Загрузка нового видео */}
                <div className="border-2 border-dashed border-purple-200 rounded-lg p-6 bg-purple-50/30">
                  <div className="text-center">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-purple-100 mb-4">
                      <Upload className="w-8 h-8 text-purple-600" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Добавить видео файл</h3>
                    <p className="text-sm text-gray-600 mb-4">
                      Поддерживаются форматы: MP4, AVI, MOV, WMV (до 100MB)
                    </p>
                    <input
                      type="file"
                      accept="video/*"
                      onChange={handleAdditionalVideoUpload}
                      disabled={uploadingAdditionalVideo}
                      className="hidden"
                      id="additional-video-upload"
                    />
                    <label
                      htmlFor="additional-video-upload"
                      className={`inline-flex items-center px-6 py-3 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-purple-600 hover:bg-purple-700 cursor-pointer transition-colors ${
                        uploadingAdditionalVideo ? 'opacity-50 cursor-not-allowed' : ''
                      }`}
                    >
                      <Video className="w-4 h-4 mr-2" />
                      {uploadingAdditionalVideo ? 'Загрузка...' : 'Выбрать видео файл'}
                    </label>
                    {uploadingAdditionalVideo && (
                      <div className="mt-4">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div className="bg-purple-600 h-2 rounded-full animate-pulse" style={{width: '60%'}}></div>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">Загружается видео файл...</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Улучшенный список дополнительных видео файлов */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-lg font-semibold text-gray-900">
                      Управление видео файлами
                    </h4>
                    {additionalVideos.length > 0 && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={loadAdditionalVideos}
                        disabled={loadingAdditionalVideos}
                      >
                        <Download className="w-4 h-4 mr-1" />
                        Обновить список
                      </Button>
                    )}
                  </div>
                  
                  {loadingAdditionalVideos ? (
                    <div className="text-center py-12">
                      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-purple-100 mb-4">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">Загрузка видео файлов</h3>
                      <p className="text-sm text-gray-500">Пожалуйста, подождите...</p>
                    </div>
                  ) : additionalVideos.length > 0 ? (
                    <div className="grid gap-4">
                      {additionalVideos.map((video, index) => (
                        <div key={video.file_id} className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
                          <div className="flex items-start justify-between">
                            <div className="flex items-start space-x-4 flex-1">
                              <div className="flex-shrink-0">
                                <div className="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center">
                                  <Video className="w-6 h-6 text-purple-600" />
                                </div>
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center space-x-2 mb-1">
                                  <h5 className="text-base font-semibold text-gray-900 truncate">{video.title}</h5>
                                  <Badge variant="outline" className="text-xs">
                                    #{index + 1}
                                  </Badge>
                                </div>
                                <p className="text-sm text-gray-600 mb-1">{video.filename}</p>
                                {video.uploaded_at && (
                                  <p className="text-xs text-gray-400">
                                    📅 Загружен: {new Date(video.uploaded_at).toLocaleDateString('ru-RU')} в {new Date(video.uploaded_at).toLocaleTimeString('ru-RU')}
                                  </p>
                                )}
                                <div className="flex items-center space-x-4 mt-2">
                                  <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full">
                                    ✅ Готов к просмотру
                                  </span>
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Button
                                size="sm"
                                variant="outline"
                                className="bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100"
                                onClick={() => {
                                  setSelectedLessonVideo({
                                    url: `${backendUrl}${video.video_url}`,
                                    title: video.title,
                                    description: `Предварительный просмотр дополнительного видео "${video.title}"`
                                  });
                                }}
                              >
                                <PlayCircle className="w-4 h-4 mr-1" />
                                Смотреть
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                className="bg-red-50 border-red-200 text-red-700 hover:bg-red-100"
                                onClick={() => handleDeleteAdditionalVideo(video.file_id, video.title)}
                              >
                                <Trash2 className="w-4 h-4 mr-1" />
                                Удалить
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                      
                      {/* Информационная панель */}
                      <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <div className="flex items-center">
                          <Lightbulb className="w-5 h-5 text-blue-600 mr-2" />
                          <div>
                            <h6 className="font-medium text-blue-900">Совет по управлению видео</h6>
                            <p className="text-sm text-blue-700">
                              Видео файлы автоматически становятся доступными студентам в FirstLesson. 
                              Используйте понятные названия для лучшей навигации.
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gray-100 mb-4">
                        <Video className="w-10 h-10 text-gray-400" />
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">Нет видео файлов</h3>
                      <p className="text-sm text-gray-500 mb-4">
                        Загрузите первый дополнительный видео файл для этого урока
                      </p>
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 max-w-md mx-auto">
                        <div className="flex items-center">
                          <Star className="w-5 h-5 text-yellow-600 mr-2" />
                          <div className="text-left">
                            <h6 className="font-medium text-yellow-900">Рекомендация</h6>
                            <p className="text-sm text-yellow-700">
                              Добавьте обучающие видео, которые дополнят основной материал урока
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    );
  };

  const renderUsersTab = () => (
    <div className="space-y-6">
      {/* Статистика */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
        <Card>
          <CardContent className="p-3 md:p-4">
            <div className="flex items-center space-x-2">
              <Users className="h-4 w-4 text-blue-600 flex-shrink-0" />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground truncate">Всего учеников</p>
                <p className="text-base md:text-lg font-bold">{users?.length || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-3 md:p-4">
            <div className="flex items-center space-x-2">
              <Award className="h-4 w-4 text-green-600 flex-shrink-0" />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground truncate">Premium</p>
                <p className="text-base md:text-lg font-bold">{users?.filter(u => u.is_premium)?.length || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-3 md:p-4">
            <div className="flex items-center space-x-2">
              <CreditCard className="h-4 w-4 text-orange-600 flex-shrink-0" />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground truncate">Кредитов</p>
                <p className="text-base md:text-lg font-bold">{users?.reduce((sum, u) => sum + (u.credits_remaining || 0), 0) || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-3 md:p-4">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-4 w-4 text-purple-600 flex-shrink-0" />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground truncate">Прогресс</p>
                <p className="text-base md:text-lg font-bold">
                  {users?.length ? Math.round(users.reduce((sum, u) => sum + (u.lessons_progress_percent || 0), 0) / users.length) : 0}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Таблица пользователей */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center text-base sm:text-lg">
            <Users className="w-4 h-4 sm:w-5 sm:h-5 mr-2" />
            База данных учеников
          </CardTitle>
          <CardDescription className="text-xs sm:text-sm">Управление пользователями и их кредитами</CardDescription>
        </CardHeader>
        <CardContent>
          {/* Поиск пользователей */}
          <div className="mb-4">
            <Label htmlFor="user-search" className="text-xs sm:text-sm">Поиск учеников</Label>
            <Input
              id="user-search"
              type="text"
              placeholder="Введите имя или email..."
              value={userSearchTerm}
              onChange={(e) => setUserSearchTerm(e.target.value)}
              className="max-w-md text-sm"
            />
            {userSearchTerm && (
              <p className="text-sm text-gray-600 mt-1">
                Найдено: {filteredUsers.length} из {users.length} учеников
              </p>
            )}
          </div>

          {loading ? (
            <div className="text-center py-4">Загрузка...</div>
          ) : (
            <>
              {/* Mobile View - Cards */}
              <div className="block md:hidden space-y-3">
                {(filteredUsers || []).map((u) => (
                  <Card key={u.id} className="p-4">
                    <div className="space-y-3">
                      {/* Header with name and status */}
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-semibold text-sm">{u.name || 'Без имени'}</div>
                          <div className="text-xs text-gray-500">{u.email}</div>
                        </div>
                        <div className="flex flex-col items-end gap-1">
                          {u.is_premium ? (
                            <Badge className="bg-green-600 text-xs">
                              {u.subscription_type || 'Premium'}
                            </Badge>
                          ) : (
                            <Badge variant="secondary" className="text-xs">Базовый</Badge>
                          )}
                          {u.is_super_admin && (
                            <Badge className="bg-red-600 text-xs">Super Admin</Badge>
                          )}
                          {u.is_admin && !u.is_super_admin && (
                            <Badge className="bg-blue-600 text-xs">Admin</Badge>
                          )}
                        </div>
                      </div>

                      {/* Credits */}
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-600">Кредиты:</span>
                        {editingCredits[u.id] ? (
                          <div className="flex items-center gap-1">
                            <Input
                              type="number"
                              min="0"
                              defaultValue={u.credits_remaining}
                              className="w-16 h-7 text-xs"
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  updateUserCredits(u.id, e.target.value);
                                }
                              }}
                              id={`credits-${u.id}`}
                            />
                            <Button
                              size="sm"
                              className="h-7 w-7 p-0"
                              onClick={() => {
                                const input = document.getElementById(`credits-${u.id}`);
                                updateUserCredits(u.id, input.value);
                              }}
                            >
                              <Save className="w-3 h-3" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-7 w-7 p-0"
                              onClick={() => setEditingCredits(prev => ({ ...prev, [u.id]: false }))}
                            >
                              <X className="w-3 h-3" />
                            </Button>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1">
                            <Badge variant={u.credits_remaining > 0 ? "default" : "secondary"}>
                              {u.credits_remaining || 0}
                            </Badge>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-7 w-7 p-0"
                              onClick={() => setEditingCredits(prev => ({ ...prev, [u.id]: true }))}
                            >
                              <Edit3 className="w-3 h-3" />
                            </Button>
                          </div>
                        )}
                      </div>

                      {/* Progress */}
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-600">Прогресс уроков:</span>
                          <span>{u.lessons_completed} из {u.lessons_total}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${u.lessons_progress_percent}%` }}
                            ></div>
                          </div>
                          <span className="text-xs">{u.lessons_progress_percent}%</span>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 w-7 p-0"
                            onClick={() => fetchUserProgress(u.id)}
                          >
                            <Eye className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex flex-wrap gap-1 pt-2 border-t">
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs"
                          onClick={() => {
                            const newCredits = (u.credits_remaining || 0) + 10;
                            updateUserCredits(u.id, newCredits);
                          }}
                          title="Добавить 10 кредитов"
                        >
                          <Plus className="w-3 h-3 mr-1" />
                          +10
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs"
                          onClick={() => {
                            const newCredits = Math.max(0, (u.credits_remaining || 0) - 10);
                            updateUserCredits(u.id, newCredits);
                          }}
                          title="Убрать 10 кредитов"
                        >
                          <Minus className="w-3 h-3 mr-1" />
                          -10
                        </Button>

                        {user?.is_super_admin && !u.is_super_admin && (
                          <>
                            {u.is_admin ? (
                              <Button
                                size="sm"
                                variant="destructive"
                                className="h-7 text-xs"
                                onClick={() => revokeAdminRights(u.id)}
                                title="Отозвать права администратора"
                              >
                                <User className="w-3 h-3 mr-1" />
                                Отозвать Admin
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                variant="default"
                                className="h-7 text-xs"
                                onClick={() => grantAdminRights(u.id)}
                                title="Предоставить права администратора"
                              >
                                <Settings className="w-3 h-3 mr-1" />
                                Сделать Admin
                              </Button>
                            )}
                          </>
                        )}

                        {user?.is_super_admin && u.id !== user.id && !u.is_super_admin && (
                          <Button
                            size="sm"
                            variant="destructive"
                            className="h-7 text-xs bg-red-600 hover:bg-red-700"
                            onClick={() => deleteUser(u.id)}
                            title="УДАЛИТЬ ПОЛЬЗОВАТЕЛЯ (необратимо!)"
                          >
                            <Trash2 className="w-3 h-3 mr-1" />
                            Удалить
                          </Button>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>

              {/* Desktop View - Table */}
              <div className="hidden md:block overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Ученик</th>
                      <th className="text-left p-2">Контакты</th>
                      <th className="text-left p-2">Кредиты</th>
                      <th className="text-left p-2">Статус</th>
                      <th className="text-left p-2">Прогресс уроков</th>
                      <th className="text-left p-2">Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(filteredUsers || []).map((u) => (
                    <tr key={u.id} className="border-b hover:bg-gray-50">
                      <td className="p-2">
                        <div>
                          <div className="font-medium">{u.name || 'Без имени'}</div>
                          <div className="text-xs text-gray-500">{u.id}</div>
                        </div>
                      </td>
                      <td className="p-2">
                        <div>
                          <div className="text-sm">{u.email}</div>
                          <div className="text-xs text-gray-500">
                            {u.birth_date && <span>🎂 {u.birth_date}</span>}
                            {u.city && <span className="ml-2">📍 {u.city}</span>}
                          </div>
                        </div>
                      </td>
                      <td className="p-2">
                        {editingCredits[u.id] ? (
                          <div className="flex items-center space-x-2">
                            <Input
                              type="number"
                              min="0"
                              defaultValue={u.credits_remaining}
                              className="w-20 h-8"
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  updateUserCredits(u.id, e.target.value);
                                }
                              }}
                              id={`credits-${u.id}`}
                            />
                            <Button
                              size="sm"
                              onClick={() => {
                                const input = document.getElementById(`credits-${u.id}`);
                                updateUserCredits(u.id, input.value);
                              }}
                            >
                              <Save className="w-3 h-3" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setEditingCredits(prev => ({ ...prev, [u.id]: false }))}
                            >
                              <X className="w-3 h-3" />
                            </Button>
                          </div>
                        ) : (
                          <div className="flex items-center space-x-2">
                            <Badge variant={u.credits_remaining > 0 ? "default" : "secondary"}>
                              {u.credits_remaining || 0}
                            </Badge>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => setEditingCredits(prev => ({ ...prev, [u.id]: true }))}
                            >
                              <Edit3 className="w-3 h-3" />
                            </Button>
                          </div>
                        )}
                      </td>
                      <td className="p-2">
                        <div className="space-y-1">
                          {/* Подписка */}
                          {u.is_premium ? (
                            <Badge className="bg-green-600">
                              {u.subscription_type || 'Premium'}
                            </Badge>
                          ) : (
                            <Badge variant="secondary">Базовый</Badge>
                          )}
                          {u.subscription_expires_at && (
                            <div className="text-xs text-gray-500">
                              до {new Date(u.subscription_expires_at).toLocaleDateString()}
                            </div>
                          )}
                          
                          {/* Роли администратора */}
                          <div className="flex flex-wrap gap-1">
                            {u.is_super_admin && (
                              <Badge className="bg-red-600 text-xs">Super Admin</Badge>
                            )}
                            {u.is_admin && !u.is_super_admin && (
                              <Badge className="bg-blue-600 text-xs">Admin</Badge>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="p-2">
                        <div className="flex items-center space-x-2">
                          <div className="w-16 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${u.lessons_progress_percent}%` }}
                            ></div>
                          </div>
                          <span className="text-xs">{u.lessons_progress_percent}%</span>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => fetchUserProgress(u.id)}
                          >
                            <Eye className="w-3 h-3" />
                          </Button>
                        </div>
                        <div className="text-xs text-gray-500">
                          {u.lessons_completed} из {u.lessons_total} уроков
                        </div>
                      </td>
                      <td className="p-2">
                        <div className="flex flex-wrap gap-1">
                          {/* Кредиты */}
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              const newCredits = (u.credits_remaining || 0) + 10;
                              updateUserCredits(u.id, newCredits);
                            }}
                            title="Добавить 10 кредитов"
                          >
                            <Plus className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              const newCredits = Math.max(0, (u.credits_remaining || 0) - 10);
                              updateUserCredits(u.id, newCredits);
                            }}
                            title="Убрать 10 кредитов"
                          >
                            <Minus className="w-3 h-3" />
                          </Button>
                          
                          {/* Управление ролями (только для Super Admin) */}
                          {user?.is_super_admin && !u.is_super_admin && (
                            <>
                              {u.is_admin ? (
                                <Button
                                  size="sm"
                                  variant="destructive"
                                  onClick={() => revokeAdminRights(u.id)}
                                  title="Отозвать права администратора"
                                >
                                  <User className="w-3 h-3" />
                                </Button>
                              ) : (
                                <Button
                                  size="sm"
                                  variant="default"
                                  onClick={() => grantAdminRights(u.id)}
                                  title="Предоставить права администратора"
                                >
                                  <Settings className="w-3 h-3" />
                                </Button>
                              )}
                            </>
                          )}

                          {/* Удаление пользователя (только для Super Admin, не для самого себя и супер-админов) */}
                          {user?.is_super_admin && u.id !== user.id && !u.is_super_admin && (
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => deleteUser(u.id)}
                              title="УДАЛИТЬ ПОЛЬЗОВАТЕЛЯ (необратимо!)"
                              className="ml-2 bg-red-600 hover:bg-red-700"
                            >
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Модальное окно прогресса уроков */}
      {selectedUserProgress && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Прогресс уроков - Пользователь ID: {selectedUserProgress.user_id}</span>
              <Button 
                variant="ghost"
                onClick={() => setSelectedUserProgress(null)}
              >
                <X className="w-4 h-4" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {selectedUserProgress.lessons.map((lesson, index) => (
                <div key={lesson.material_id} className="flex items-center justify-between p-3 border rounded">
                  <div className="flex-1">
                    <div className="font-medium">{lesson.title}</div>
                    {lesson.started_at && (
                      <div className="text-xs text-gray-500">
                        Начал: {new Date(lesson.started_at).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center space-x-3">
                    {lesson.quiz_score > 0 && (
                      <Badge variant="outline">
                        Тест: {lesson.quiz_score}%
                      </Badge>
                    )}
                    <Badge 
                      className={lesson.completed ? "bg-green-600" : "bg-gray-400"}
                    >
                      {lesson.completed ? 'Завершен' : 'В процессе'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  // Function to render materials tab
  const renderMaterialsTab = () => (
    <div className="p-6 text-center text-gray-500">
      <FileText className="mx-auto h-12 w-12 text-gray-300 mb-4" />
      <h3 className="text-lg font-medium">Раздел материалы удален</h3>
      <p>Этот раздел больше не используется</p>
    </div>
  );

  // Function to render materials editing (legacy code - now unused)
  const renderMaterialsEditingTab = () => (
    <div className="space-y-6">
      {/* Header with Add Button */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle className="flex items-center">
                <FileText className="w-5 h-5 mr-2" />
                Управление материалами и уроками
              </CardTitle>
              <CardDescription>Создание, редактирование и управление учебными материалами</CardDescription>
            </div>
            <Button onClick={() => setEditingMaterial({ isNew: true })}>
              <Plus className="w-4 h-4 mr-2" />
              Добавить материал
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Materials List */}
      <Card>
        <CardHeader>
          <CardTitle>Список материалов</CardTitle>
        </CardHeader>
        <CardContent>
          {loadingMaterials ? (
            <div className="text-center py-4">Загрузка материалов...</div>
          ) : materials?.length > 0 ? (
            <div className="space-y-4">
              {materials.map((material) => (
                <div key={material.id} className="p-4 border rounded-lg">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg">{material.title}</h3>
                      <p className="text-sm text-gray-600 mt-1">{material.description}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span>Порядок: {material.order}</span>
                        <span>Создан: {new Date(material.created_at).toLocaleDateString()}</span>
                        {material.video_url && <span>🔗 YouTube</span>}
                        {material.video_file_id && <span>📹 Видео файл</span>}
                        {material.pdf_file_id && <span>📄 PDF файл</span>}
                        <Badge className={material.is_active ? "bg-green-600" : "bg-gray-400"}>
                          {material.is_active ? 'Активен' : 'Неактивен'}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setEditingMaterial({ ...material, isNew: false })}
                      >
                        <Edit3 className="w-3 h-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => deleteMaterial(material.id)}
                      >
                        <X className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>Нет материалов</p>
              <p className="text-sm">Создайте первый материал, нажав кнопку выше</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Material Editor Modal */}
      {editingMaterial && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>{editingMaterial.isNew ? 'Создание нового материала' : 'Редактирование материала'}</span>
              <Button 
                variant="ghost"
                onClick={() => setEditingMaterial(null)}
              >
                <X className="w-4 h-4" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="title">Название урока</Label>
                  <Input
                    id="title"
                    value={editingMaterial.title || ''}
                    onChange={(e) => setEditingMaterial({...editingMaterial, title: e.target.value})}
                    placeholder="Введите название урока"
                  />
                </div>
                <div>
                  <Label htmlFor="order">Порядок отображения</Label>
                  <Input
                    id="order"
                    type="number"
                    value={editingMaterial.order || 0}
                    onChange={(e) => setEditingMaterial({...editingMaterial, order: parseInt(e.target.value)})}
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="description">Описание</Label>
                <Input
                  id="description"
                  value={editingMaterial.description || ''}
                  onChange={(e) => setEditingMaterial({...editingMaterial, description: e.target.value})}
                  placeholder="Краткое описание урока"
                />
              </div>

              {/* Lesson Assignment */}
              <div>
                <Label htmlFor="lesson_id">Прикрепить к уроку (необязательно)</Label>
                <select
                  id="lesson_id"
                  className="w-full p-2 border rounded-md"
                  value={editingMaterial.lesson_id || ''}
                  onChange={(e) => setEditingMaterial({...editingMaterial, lesson_id: e.target.value})}
                >
                  <option value="">Не прикреплять к конкретному уроку</option>
                  {lessons.map((lesson) => (
                    <option key={lesson.id} value={lesson.id}>
                      {lesson.title} (Уровень {lesson.level})
                    </option>
                  ))}
                </select>
                <div className="text-xs text-gray-500 mt-1">
                  Материал будет доступен студентам после изучения выбранного урока
                </div>
              </div>

              <div>
                <Label htmlFor="content">Содержание урока</Label>
                <textarea
                  id="content"
                  rows={6}
                  className="w-full p-3 border rounded-md"
                  value={editingMaterial.content || ''}
                  onChange={(e) => setEditingMaterial({...editingMaterial, content: e.target.value})}
                  placeholder="Введите содержание урока (поддерживается Markdown)"
                />
              </div>

              {/* Media Section */}
              <div className="space-y-3">
                <Label>Медиа материалы для урока</Label>
                <Tabs defaultValue="youtube">
                  <TabsList>
                    <TabsTrigger value="youtube">YouTube ссылка</TabsTrigger>
                    <TabsTrigger value="upload">Загрузить видео</TabsTrigger>
                    <TabsTrigger value="pdf">PDF документ</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="youtube" className="mt-3">
                    <Input
                      placeholder="https://www.youtube.com/watch?v=..."
                      value={editingMaterial.video_url || ''}
                      onChange={(e) => setEditingMaterial({...editingMaterial, video_url: e.target.value, video_file: '', file_url: ''})}
                    />
                  </TabsContent>
                  
                  <TabsContent value="upload" className="mt-3">
                    <div className="space-y-3">
                      <input
                        type="file"
                        accept="video/*"
                        onChange={handleVideoUpload}
                        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                      />
                      {uploadingVideo && (
                        <div className="text-sm text-blue-600">Загрузка видео...</div>
                      )}
                      {editingMaterial.video_file_id && editingMaterial.video_filename && (
                        <div className="p-3 bg-green-50 border border-green-200 rounded-md">
                          <div className="text-sm text-green-800 font-medium">✅ Видео загружено: {editingMaterial.video_filename}</div>
                          <div className="text-xs text-green-600 mt-1">ID: {editingMaterial.video_file_id}</div>
                          <div className="flex gap-2 mt-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                // Предварительный просмотр видео урока
                                window.open(`${backendUrl}/api/lessons/video/${editingMaterial.video_file_id}`, '_blank');
                              }}
                            >
                              <PlayCircle className="w-4 h-4 mr-1" />
                              Просмотр
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setEditingMaterial(prev => ({
                                  ...prev, 
                                  video_file_id: '', 
                                  video_filename: ''
                                }));
                              }}
                            >
                              <X className="w-4 h-4 mr-1" />
                              Удалить
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  </TabsContent>

                  <TabsContent value="pdf" className="mt-3">
                    <div className="space-y-3">
                      <input
                        type="file"
                        accept=".pdf"
                        onChange={handlePdfUpload}
                        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
                      />
                      {uploadingVideo && (
                        <div className="text-sm text-green-600">Загрузка PDF...</div>
                      )}
                      {editingMaterial.pdf_file_id && editingMaterial.pdf_filename && (
                        <div className="p-3 bg-green-50 border border-green-200 rounded-md">
                          <div className="text-sm text-green-800 font-medium">✅ PDF загружен: {editingMaterial.pdf_filename}</div>
                          <div className="text-xs text-green-600 mt-1">ID: {editingMaterial.pdf_file_id}</div>
                          <div className="flex gap-2 mt-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                // Предварительный просмотр как в PersonalConsultations
                                window.open(`${backendUrl}/api/consultations/pdf/${editingMaterial.pdf_file_id}`, '_blank');
                              }}
                            >
                              <Eye className="w-4 h-4 mr-1" />
                              Просмотр
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                // Скачивание
                                const link = document.createElement('a');
                                link.href = `${backendUrl}/api/consultations/pdf/${editingMaterial.pdf_file_id}`;
                                link.download = editingMaterial.pdf_filename;
                                link.click();
                              }}
                            >
                              <Download className="w-4 h-4 mr-1" />
                              Скачать
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setEditingMaterial(prev => ({
                                  ...prev, 
                                  pdf_file_id: '', 
                                  pdf_filename: ''
                                }));
                              }}
                            >
                              <X className="w-4 h-4 mr-1" />
                              Удалить
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  </TabsContent>
                </Tabs>
              </div>

              {/* Quiz Questions */}
              <div className="space-y-3">
                <Label>Вопросы для теста</Label>
                <div className="space-y-2">
                  {(editingMaterial.quiz_questions || []).map((question, index) => (
                    <div key={index} className="p-3 border rounded-md">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-medium">Вопрос {index + 1}</span>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => removeQuizQuestion(index)}
                        >
                          <X className="w-3 h-3" />
                        </Button>
                      </div>
                      <Input
                        placeholder="Текст вопроса"
                        value={question.question || ''}
                        onChange={(e) => updateQuizQuestion(index, 'question', e.target.value)}
                        className="mb-2"
                      />
                      <div className="space-y-1">
                        {question.options?.map((option, optionIndex) => (
                          <div key={optionIndex} className="flex items-center gap-2">
                            <Input
                              placeholder={`Вариант ${optionIndex + 1}`}
                              value={option}
                              onChange={(e) => updateQuizOption(index, optionIndex, e.target.value)}
                            />
                            <input
                              type="radio"
                              name={`correct-${index}`}
                              checked={question.correct === optionIndex}
                              onChange={() => updateQuizQuestion(index, 'correct', optionIndex)}
                            />
                          </div>
                        )) || []}
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => addQuizOption(index)}
                        >
                          Добавить вариант
                        </Button>
                      </div>
                    </div>
                  ))}
                  <Button
                    onClick={addQuizQuestion}
                    variant="outline"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Добавить вопрос
                  </Button>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={editingMaterial.is_active !== false}
                  onChange={(e) => setEditingMaterial({...editingMaterial, is_active: e.target.checked})}
                />
                <Label htmlFor="is_active">Материал активен</Label>
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setEditingMaterial(null)}>
                  Отмена
                </Button>
                <Button onClick={saveMaterial}>
                  {editingMaterial.isNew ? 'Создать' : 'Сохранить'}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  // Function to render lessons tab
  const renderLessonsTab = () => (
    <div className="space-y-6">
      {/* Header with Create Button */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Управление занятиями</h3>
        <Button 
          onClick={() => {
            setEditingLesson({
              isNew: true,
              title: '',
              description: '',
              content: '',
              level: 1,
              duration_minutes: 30,
              video_url: '',
              video_file: '',
              order: lessons.length + 1,
              is_active: true
            });
            setCreatingLesson(true);
          }}
        >
          <Plus className="w-4 h-4 mr-2" />
          Создать занятие
        </Button>
      </div>

      {/* Lessons List */}
      {loadingLessons ? (
        <div className="text-center py-8">Загрузка занятий...</div>
      ) : (
        <div className="grid gap-4">
          {lessons.map((lesson) => (
            <Card key={lesson.id}>
              <CardContent className="p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="font-semibold">{lesson.title}</h4>
                      <Badge variant={lesson.is_active ? "default" : "secondary"}>
                        {lesson.is_active ? "Активно" : "Неактивно"}
                      </Badge>
                      <Badge variant="outline">Уровень {lesson.level}</Badge>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{lesson.description}</p>
                    <div className="text-xs text-gray-500">
                      {lesson.duration_minutes} мин • Порядок: {lesson.order}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setEditingLesson({...lesson, isNew: false});
                      }}
                    >
                      <Edit3 className="w-3 h-3" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => deleteLesson(lesson.id)}
                    >
                      <X className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          
          {lessons.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <Upload className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg">Занятий пока нет</p>
              <p className="text-sm">Создайте первое занятие для учеников</p>
            </div>
          )}
        </div>
      )}

      {/* Lesson Editor Modal */}
      {editingLesson && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>{editingLesson.isNew ? 'Создание занятия' : 'Редактирование занятия'}</span>
              <Button 
                variant="ghost"
                onClick={() => {
                  setEditingLesson(null);
                  setCreatingLesson(false);
                }}
              >
                <X className="w-4 h-4" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="lesson_title">Название занятия</Label>
                  <Input
                    id="lesson_title"
                    value={editingLesson.title || ''}
                    onChange={(e) => setEditingLesson({...editingLesson, title: e.target.value})}
                    placeholder="Введите название занятия"
                  />
                </div>
                <div>
                  <Label htmlFor="lesson_level">Уровень</Label>
                  <Input
                    id="lesson_level"
                    type="number"
                    min="1"
                    max="10"
                    value={editingLesson.level || 1}
                    onChange={(e) => setEditingLesson({...editingLesson, level: parseInt(e.target.value)})}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="lesson_duration">Длительность (минуты)</Label>
                  <Input
                    id="lesson_duration"
                    type="number"
                    min="1"
                    value={editingLesson.duration_minutes || 30}
                    onChange={(e) => setEditingLesson({...editingLesson, duration_minutes: parseInt(e.target.value)})}
                  />
                </div>
                <div>
                  <Label htmlFor="lesson_order">Порядок отображения</Label>
                  <Input
                    id="lesson_order"
                    type="number"
                    value={editingLesson.order || 0}
                    onChange={(e) => setEditingLesson({...editingLesson, order: parseInt(e.target.value)})}
                  />
                </div>
                <div>
                  <Label htmlFor="lesson_credits_cost">Баллы за урок</Label>
                  <Input
                    id="lesson_credits_cost"
                    type="number"
                    min="0"
                    value={editingLesson.credits_cost || 10}
                    onChange={(e) => setEditingLesson({...editingLesson, credits_cost: parseInt(e.target.value)})}
                    placeholder="Баллы за просмотр"
                  />
                  <div className="text-xs text-gray-500 mt-1">
                    Списываются один раз за первый просмотр
                  </div>
                </div>
              </div>

              <div>
                <Label htmlFor="lesson_description">Описание</Label>
                <Input
                  id="lesson_description"
                  value={editingLesson.description || ''}
                  onChange={(e) => setEditingLesson({...editingLesson, description: e.target.value})}
                  placeholder="Краткое описание занятия"
                />
              </div>

              <div>
                <Label htmlFor="lesson_content">Содержание урока</Label>
                <textarea
                  id="lesson_content"
                  className="w-full p-2 border rounded-md min-h-[100px]"
                  value={editingLesson.content || ''}
                  onChange={(e) => setEditingLesson({...editingLesson, content: e.target.value})}
                  placeholder="Подробное содержание урока"
                />
              </div>

              {/* Video Upload (точная копия из консультаций) */}
              <div>
                <Label>Видео урока</Label>
                <div className="space-y-4">
                  {/* YouTube URL */}
                  <div>
                    <Label>YouTube/Vimeo ссылка (опционально)</Label>
                    <Input
                      value={editingLesson.video_url || ''}
                      onChange={(e) => setEditingLesson({...editingLesson, video_url: e.target.value})}
                      placeholder="https://www.youtube.com/embed/..."
                    />
                  </div>
                  
                  {/* Video File Upload */}
                  <div>
                    <Label>Загрузить видео файл</Label>
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                      <input
                        type="file"
                        accept="video/*"
                        onChange={handleLessonVideoUpload}
                        className="w-full"
                        disabled={uploadingVideo}
                      />
                      {uploadingVideo && <p className="text-sm text-blue-600 mt-2">Загружается видео...</p>}
                      {editingLesson.video_filename && (
                        <p className="text-sm text-green-600 mt-2">✓ Видео: {editingLesson.video_filename}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* PDF Upload (точная копия из консультаций) */}
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
                    <p className="text-sm text-green-600 mt-2">✓ PDF: {editingLesson.pdf_filename}</p>
                  )}
                </div>
              </div>

              {/* Subtitles Upload (точная копия из консультаций) */}
              <div>
                <Label>Субтитры для видео (опционально)</Label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                  <input
                    type="file"
                    accept=".vtt,.srt,text/vtt,application/x-subrip"
                    onChange={handleLessonSubtitlesUpload}
                    className="w-full"
                    disabled={uploadingVideo}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Поддерживаемые форматы: .vtt, .srt
                  </p>
                  {uploadingVideo && <p className="text-sm text-blue-600 mt-2">Загружаются субтитры...</p>}
                  {editingLesson.subtitles_filename && (
                    <p className="text-sm text-green-600 mt-2">✓ Субтитры: {editingLesson.subtitles_filename}</p>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="lesson_is_active"
                  checked={editingLesson.is_active !== false}
                  onChange={(e) => setEditingLesson({...editingLesson, is_active: e.target.checked})}
                />
                <Label htmlFor="lesson_is_active">Занятие активно</Label>
              </div>

              <div className="flex justify-end gap-2">
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setEditingLesson(null);
                    setCreatingLesson(false);
                  }}
                >
                  Отмена
                </Button>
                <Button onClick={() => {
                  if (editingLesson.isNew) {
                    const { isNew, ...lessonData } = editingLesson;
                    createLesson(lessonData);
                  } else {
                    const { isNew, ...lessonData } = editingLesson;
                    updateLesson(editingLesson.id, lessonData);
                  }
                }}>
                  {editingLesson.isNew ? 'Создать' : 'Сохранить'}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  // Check if user has admin rights (either super admin or regular admin)
  if (!user?.is_super_admin && !user?.is_admin) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardContent className="p-6">
          <Alert>
            <Settings className="h-4 w-4" />
            <AlertDescription>
              У вас нет прав администратора для доступа к этой панели
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg sm:text-2xl flex items-center">
            <Settings className="w-5 h-5 sm:w-6 sm:h-6 mr-2" />
            Панель Администратора
          </CardTitle>
          <CardDescription className="text-xs sm:text-sm">
            Управление пользователями, кредитами и учебными материалами
          </CardDescription>
        </CardHeader>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className={`grid w-full ${user?.is_super_admin ? 'grid-cols-7' : 'grid-cols-2'}`}>
          <TabsTrigger value="overview" className="flex items-center justify-center px-1 sm:px-3" title="Обзор">
            <TrendingUp className="w-4 h-4 sm:mr-2" />
            <span className="hidden sm:inline">Обзор</span>
          </TabsTrigger>
          <TabsTrigger value="users" className="flex items-center justify-center px-1 sm:px-3" title="Ученики">
            <Users className="w-4 h-4 sm:mr-2" />
            <span className="hidden sm:inline">Ученики</span>
          </TabsTrigger>
          <TabsTrigger value="consultations" className="flex items-center justify-center px-1 sm:px-3" title="Консультации">
            <Video className="w-4 h-4 sm:mr-2" />
            <span className="hidden sm:inline">Консультации</span>
          </TabsTrigger>
          <TabsTrigger value="lessons" className="flex items-center justify-center px-1 sm:px-3" title="Уроки">
            <BookOpen className="w-4 h-4 sm:mr-2" />
            <span className="hidden sm:inline">Уроки</span>
          </TabsTrigger>
          <TabsTrigger value="lessons-editor" className="flex items-center justify-center px-1 sm:px-3" title="Редактор уроков">
            <Edit3 className="w-4 h-4 sm:mr-2" />
            <span className="hidden sm:inline">Редактор</span>
          </TabsTrigger>
          <TabsTrigger value="first-lesson" className="flex items-center justify-center px-1 sm:px-3" title="Первый урок">
            <Star className="w-4 h-4 sm:mr-2" />
            <span className="hidden sm:inline">1 урок</span>
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center justify-center px-1 sm:px-3" title="Настройки">
            <Settings className="w-4 h-4 sm:mr-2" />
            <span className="hidden sm:inline">Настройки</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="users" className="space-y-6">
          {renderUsersTab()}
        </TabsContent>

        <TabsContent value="lessons" className="space-y-6">
          <MultipleLessonAdmin />
        </TabsContent>

        <TabsContent value="materials" className="space-y-6">
          {renderMaterialsTab()}
        </TabsContent>

        <TabsContent value="consultations" className="space-y-6">
          {renderConsultationsTab()}
        </TabsContent>

        {user?.is_super_admin && (
          <TabsContent value="lesson-editor" className="space-y-6">
            {renderLessonEditor()}
          </TabsContent>
        )}

        {user?.is_super_admin && (
          <TabsContent value="system" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Settings className="w-5 h-5 mr-2" />
                  Системное управление
                </CardTitle>
                <CardDescription>Функции доступные только суперадминистратору</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 border rounded-lg">
                    <h3 className="font-semibold text-lg mb-2">Управление администраторами</h3>
                    <p className="text-sm text-gray-600 mb-3">
                      Предоставление и отзыв прав администратора осуществляется в разделе "Ученики"
                    </p>
                    <div className="flex items-center gap-2 text-sm">
                      <Badge className="bg-red-600">Super Admin</Badge>
                      <span>- полные права, включая управление ролями</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm mt-1">
                      <Badge className="bg-blue-600">Admin</Badge>
                      <span>- управление пользователями и материалами</span>
                    </div>
                  </div>
                  
                  <div className="p-4 border rounded-lg">
                    <h3 className="font-semibold text-lg mb-2">Загрузка видео</h3>
                    <p className="text-sm text-gray-600">
                      Видео можно загружать как для материалов, так и напрямую для уроков через раздел "Материалы"
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>
      
      {/* Enhanced Video Player Modal - ТОЧНО КАК В PERSONALCONSULTATIONS */}
      {selectedLessonVideo && (
        <EnhancedVideoViewer
          videoUrl={selectedLessonVideo.url}
          title={selectedLessonVideo.title}
          description={selectedLessonVideo.description}
          onClose={() => setSelectedLessonVideo(null)}
        />
      )}

      {/* PDF Viewer Modal - ТОЧНО КАК В PERSONALCONSULTATIONS */}
      {selectedLessonPDF && (
        <ConsultationPDFViewer
          pdfUrl={selectedLessonPDF.url}
          title={selectedLessonPDF.title}
          onClose={() => setSelectedLessonPDF(null)}
        />
      )}

      {/* Модальные окна для предпросмотра материалов администратором */}
      {selectedLessonVideo && (
        <EnhancedVideoViewer
          videoUrl={selectedLessonVideo.url}
          title={selectedLessonVideo.title}
          description={`Предпросмотр администратора: ${selectedLessonVideo.consultation?.description || 'Консультация'}`}
          onClose={() => setSelectedLessonVideo(null)}
          backendUrl={backendUrl}
        />
      )}

      {selectedLessonPDF && (
        <ConsultationPDFViewer
          pdfUrl={selectedLessonPDF.url}
          title={selectedLessonPDF.title}
          onClose={() => setSelectedLessonPDF(null)}
        />
      )}
    </div>
  );
};

export default AdminPanel;