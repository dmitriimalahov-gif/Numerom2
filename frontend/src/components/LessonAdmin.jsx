import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  Settings, FileText, Video, Upload, Save, Edit, 
  BookOpen, Brain, Target, Star, Zap
} from 'lucide-react';
import { useAuth } from './AuthContext';

const LessonAdmin = () => {
  const { user } = useAuth();
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  
  // Состояния для редактирования контента
  const [lessonContent, setLessonContent] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeSection, setActiveSection] = useState('theory');
  const [uploadedFiles, setUploadedFiles] = useState({
    video: null,
    pdf: null
  });

  useEffect(() => {
    loadLessonContent();
  }, []);

  // Загрузка содержимого урока для редактирования
  const loadLessonContent = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/api/lessons/first-lesson`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setLessonContent(data.lesson);
      }
    } catch (err) {
      console.error('Ошибка загрузки контента:', err);
    } finally {
      setLoading(false);
    }
  };

  // Сохранение изменений контента
  const saveContent = async (section, field, value) => {
    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      
      // TODO: Добавить API endpoint для обновления контента урока
      const response = await fetch(`${backendUrl}/api/admin/update-lesson-content`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
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
      }
    } catch (err) {
      console.error('Ошибка сохранения:', err);
    } finally {
      setSaving(false);
    }
  };

  // Загрузка видео файла (обновлено для новых endpoints)
  const handleVideoUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);  // Изменено с 'video' на 'file'

    try {
      const token = localStorage.getItem('token');
      // Используем новый упрощенный endpoint
      const response = await fetch(`${backendUrl}/api/admin/lessons/upload-video`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        setUploadedFiles(prev => ({
          ...prev,
          video: {
            url: `${backendUrl}${data.video_url}`,
            filename: data.filename,
            file_id: data.file_id
          }
        }));
        alert('Видео успешно загружено!');
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка загрузки видео');
      }
    } catch (err) {
      console.error('Ошибка загрузки видео:', err);
      alert('Ошибка загрузки видео');
    }
  };

  // Загрузка PDF файла (обновлено для новых endpoints)
  const handlePDFUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);  // Изменено с 'pdf' на 'file'

    try {
      const token = localStorage.getItem('token');
      // Используем новый упрощенный endpoint
      const response = await fetch(`${backendUrl}/api/admin/lessons/upload-pdf`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        setUploadedFiles(prev => ({
          ...prev,
          pdf: {
            url: `${backendUrl}${data.pdf_url}`,
            filename: data.filename,
            file_id: data.file_id
          }
        }));
        alert('PDF успешно загружен!');
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Ошибка загрузки PDF');
      }
    } catch (err) {
      console.error('Ошибка загрузки PDF:', err);
      alert('Ошибка загрузки PDF');
    }
  };

  // Проверка прав доступа (только для администраторов)
  if (!user || user.role !== 'admin') {
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
          <p>Загрузка админ-панели...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Заголовок админ-панели */}
      <Card className="bg-gradient-to-r from-blue-600 to-purple-600">
        <CardHeader className="text-white">
          <CardTitle className="text-2xl flex items-center">
            <Settings className="w-6 h-6 mr-2" />
            Админ-панель: Первое занятие NumerOM
          </CardTitle>
          <CardDescription className="text-white/90">
            Редактирование контента, загрузка материалов и управление уроком
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Основные разделы админки */}
      <Tabs value={activeSection} onValueChange={setActiveSection} className="space-y-6">
        <TabsList className="grid w-full grid-cols-2 lg:grid-cols-5">
          <TabsTrigger value="theory" className="flex items-center gap-2">
            <BookOpen className="w-4 h-4" />
            <span className="hidden sm:inline">Теория</span>
          </TabsTrigger>
          <TabsTrigger value="exercises" className="flex items-center gap-2">
            <Brain className="w-4 h-4" />
            <span className="hidden sm:inline">Упражнения</span>
          </TabsTrigger>
          <TabsTrigger value="quiz" className="flex items-center gap-2">
            <Target className="w-4 h-4" />
            <span className="hidden sm:inline">Тест</span>
          </TabsTrigger>
          <TabsTrigger value="challenge" className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            <span className="hidden sm:inline">Челлендж</span>
          </TabsTrigger>
          <TabsTrigger value="media" className="flex items-center gap-2">
            <Upload className="w-4 h-4" />
            <span className="hidden sm:inline">Медиа</span>
          </TabsTrigger>
        </TabsList>

        {/* РЕДАКТИРОВАНИЕ ТЕОРИИ */}
        <TabsContent value="theory" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Edit className="w-5 h-5 mr-2" />
                Редактирование теории
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Что такое нумерология */}
              <div>
                <h4 className="font-semibold mb-2">Что такое нумерология?</h4>
                <textarea
                  className="w-full p-3 border rounded-lg min-h-32 text-sm"
                  value={lessonContent.content?.theory?.what_is_numerology || ''}
                  onChange={(e) => saveContent('theory', 'what_is_numerology', e.target.value)}
                  placeholder="Описание нумерологии..."
                />
              </div>

              {/* История космического корабля */}
              <div>
                <h4 className="font-semibold mb-2">История космического корабля</h4>
                <textarea
                  className="w-full p-3 border rounded-lg min-h-48 text-sm"
                  value={lessonContent.content?.theory?.cosmic_ship_story || ''}
                  onChange={(e) => saveContent('theory', 'cosmic_ship_story', e.target.value)}
                  placeholder="История о космическом корабле и планетах..."
                />
              </div>

              {/* Планеты и числа */}
              <div>
                <h4 className="font-semibold mb-2">Соответствие планет и чисел</h4>
                <textarea
                  className="w-full p-3 border rounded-lg min-h-32 text-sm"
                  value={lessonContent.content?.theory?.planets_and_numbers || ''}
                  onChange={(e) => saveContent('theory', 'planets_and_numbers', e.target.value)}
                  placeholder="Описание соответствия планет и чисел..."
                />
              </div>

              <Button 
                onClick={() => loadLessonContent()}
                disabled={saving}
                className="w-full sm:w-auto"
              >
                <Save className="w-4 h-4 mr-2" />
                {saving ? 'Сохранение...' : 'Обновить контент'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ЗАГРУЗКА МЕДИА */}
        <TabsContent value="media" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Upload className="w-5 h-5 mr-2" />
                Загрузка видео и PDF материалов
              </CardTitle>
              <CardDescription>
                Загрузите дополнительные материалы для урока
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Загрузка видео */}
              <div className="p-4 border-2 border-dashed border-blue-300 rounded-lg">
                <div className="text-center">
                  <Video className="w-12 h-12 text-blue-500 mx-auto mb-4" />
                  <h4 className="font-semibold text-blue-800 mb-2">Видеоурок по планетам</h4>
                  <p className="text-sm text-gray-600 mb-4">
                    Загрузите видео для раздела теории (форматы: MP4, WebM, AVI)
                  </p>
                  <input
                    type="file"
                    accept="video/*"
                    onChange={handleVideoUpload}
                    className="hidden"
                    id="video-upload"
                  />
                  <label htmlFor="video-upload">
                    <Button variant="outline" className="cursor-pointer">
                      <Upload className="w-4 h-4 mr-2" />
                      Выбрать видео
                    </Button>
                  </label>
                  {uploadedFiles.video && (
                    <div className="mt-3">
                      <Badge className="bg-green-100 text-green-800">
                        ✓ Видео загружено
                      </Badge>
                    </div>
                  )}
                </div>
              </div>

              {/* Загрузка PDF */}
              <div className="p-4 border-2 border-dashed border-green-300 rounded-lg">
                <div className="text-center">
                  <FileText className="w-12 h-12 text-green-500 mx-auto mb-4" />
                  <h4 className="font-semibold text-green-800 mb-2">PDF справочник планет</h4>
                  <p className="text-sm text-gray-600 mb-4">
                    Загрузите PDF с подробной информацией о планетах
                  </p>
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handlePDFUpload}
                    className="hidden"
                    id="pdf-upload"
                  />
                  <label htmlFor="pdf-upload">
                    <Button variant="outline" className="cursor-pointer">
                      <Upload className="w-4 h-4 mr-2" />
                      Выбрать PDF
                    </Button>
                  </label>
                  {uploadedFiles.pdf && (
                    <div className="mt-3">
                      <Badge className="bg-green-100 text-green-800">
                        ✓ PDF загружен
                      </Badge>
                    </div>
                  )}
                </div>
              </div>

              {/* Статус загруженных файлов */}
              <Card className="bg-gray-50">
                <CardContent className="pt-4">
                  <h4 className="font-semibold mb-3">Загруженные материалы</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Видеоурок:</span>
                      <Badge variant={uploadedFiles.video ? "default" : "secondary"}>
                        {uploadedFiles.video ? "Загружен" : "Не загружен"}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">PDF справочник:</span>
                      <Badge variant={uploadedFiles.pdf ? "default" : "secondary"}>
                        {uploadedFiles.pdf ? "Загружен" : "Не загружен"}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Остальные разделы для редактирования упражнений, квиза, челленджа */}
        <TabsContent value="exercises">
          <Card>
            <CardHeader>
              <CardTitle>Редактирование упражнений</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">Функционал редактирования упражнений будет добавлен...</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="quiz">
          <Card>
            <CardHeader>
              <CardTitle>Редактирование теста</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">Функционал редактирования теста будет добавлен...</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="challenge">
          <Card>
            <CardHeader>
              <CardTitle>Редактирование челленджа</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">Функционал редактирования челленджа будет добавлен...</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ЗАГРУЗКА МЕДИА - по модели PersonalConsultations */}
        <TabsContent value="media" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Upload className="w-5 h-5 mr-2" />
                Загрузка медиа материалов
              </CardTitle>
              <CardDescription>
                Загрузите видео и PDF материалы для первого занятия
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              
              {/* Загрузка видео */}
              <div className="border rounded-lg p-6 bg-blue-50">
                <div className="flex items-start gap-4">
                  <Video className="w-8 h-8 text-blue-600 mt-1" />
                  <div className="flex-1">
                    <h4 className="font-semibold text-blue-800 mb-2">Видеоурок по планетам</h4>
                    <p className="text-sm text-gray-600 mb-4">
                      Загрузите обучающее видео о планетах и их значении в нумерологии
                    </p>
                    
                    <input
                      type="file"
                      accept="video/*"
                      onChange={handleVideoUpload}
                      className="hidden"
                      id="admin-video-upload"
                    />
                    <label htmlFor="admin-video-upload">
                      <Button variant="outline" className="cursor-pointer">
                        <Upload className="w-4 h-4 mr-2" />
                        Выбрать видео
                      </Button>
                    </label>
                    
                    {uploadedFiles.video && (
                      <div className="mt-4 p-4 bg-white rounded border">
                        <div className="flex items-center justify-between mb-3">
                          <Badge className="bg-green-100 text-green-800">
                            ✓ Видео загружено
                          </Badge>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setUploadedFiles(prev => ({...prev, video: null}))}
                          >
                            Удалить
                          </Button>
                        </div>
                        <div className="text-sm">
                          <div className="font-medium">{uploadedFiles.video.filename}</div>
                          <div className="text-gray-500">ID: {uploadedFiles.video.file_id}</div>
                        </div>
                        <Button
                          size="sm"
                          className="mt-2"
                          onClick={() => window.open(uploadedFiles.video.url, '_blank')}
                        >
                          <Video className="w-4 h-4 mr-1" />
                          Просмотреть
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Загрузка PDF */}
              <div className="border rounded-lg p-6 bg-green-50">
                <div className="flex items-start gap-4">
                  <FileText className="w-8 h-8 text-green-600 mt-1" />
                  <div className="flex-1">
                    <h4 className="font-semibold text-green-800 mb-2">PDF справочник планет</h4>
                    <p className="text-sm text-gray-600 mb-4">
                      Загрузите справочный материал в формате PDF
                    </p>
                    
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={handlePDFUpload}
                      className="hidden"
                      id="admin-pdf-upload"
                    />
                    <label htmlFor="admin-pdf-upload">
                      <Button variant="outline" className="cursor-pointer">
                        <Upload className="w-4 h-4 mr-2" />
                        Выбрать PDF
                      </Button>
                    </label>
                    
                    {uploadedFiles.pdf && (
                      <div className="mt-4 p-4 bg-white rounded border">
                        <div className="flex items-center justify-between mb-3">
                          <Badge className="bg-green-100 text-green-800">
                            ✓ PDF загружен
                          </Badge>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setUploadedFiles(prev => ({...prev, pdf: null}))}
                          >
                            Удалить
                          </Button>
                        </div>
                        <div className="text-sm">
                          <div className="font-medium">{uploadedFiles.pdf.filename}</div>
                          <div className="text-gray-500">ID: {uploadedFiles.pdf.file_id}</div>
                        </div>
                        <div className="flex gap-2 mt-2">
                          <Button
                            size="sm"
                            onClick={() => window.open(uploadedFiles.pdf.url, '_blank')}
                          >
                            <FileText className="w-4 h-4 mr-1" />
                            Просмотреть
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              const link = document.createElement('a');
                              link.href = uploadedFiles.pdf.url;
                              link.download = uploadedFiles.pdf.filename;
                              link.click();
                            }}
                          >
                            Скачать
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Статус загруженных файлов */}
              <Card className="bg-gray-50">
                <CardContent className="pt-4">
                  <h4 className="font-semibold mb-3">Статус медиа материалов</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div className="flex items-center justify-between">
                      <span>Видеоурок:</span>
                      <Badge variant={uploadedFiles.video ? "default" : "secondary"}>
                        {uploadedFiles.video ? "Загружен" : "Не загружен"}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>PDF справочник:</span>
                      <Badge variant={uploadedFiles.pdf ? "default" : "secondary"}>
                        {uploadedFiles.pdf ? "Загружен" : "Не загружен"}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default LessonAdmin;