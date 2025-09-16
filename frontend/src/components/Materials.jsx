import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { FileText, Eye, DownloadCloud, Loader2, Play, Video } from 'lucide-react';
import EnhancedVideoViewer from './EnhancedVideoViewer';
import ConsultationPDFViewer from './ConsultationPDFViewer';

const Materials = () => {
  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [selectedPDF, setSelectedPDF] = useState(null);

  // Обработка ESC для закрытия viewer'а
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && (selectedVideo || selectedPDF)) {
        setSelectedVideo(null);
        setSelectedPDF(null);
      }
    };

    if (selectedVideo || selectedPDF) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [selectedVideo, selectedPDF]);

  const loadMaterials = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${backendUrl}/api/materials`, { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } });
      if (!res.ok) throw new Error('Ошибка загрузки материалов');
      const data = await res.json();
      setMaterials(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadMaterials(); }, []);

  const openVideoMaterial = (material) => {
    // УНИФИКАЦИЯ: используем точно такую же логику как в PersonalConsultations
    let videoUrl = null;
    
    // Приоритет: video_file_id (загруженный файл через consultations endpoint)
    if (material.video_file_id) {
      videoUrl = `${backendUrl}/api/consultations/video/${material.video_file_id}`;
    }
    // Если нет video_file_id, проверяем старое поле video_file
    else if (material.video_file) {
      videoUrl = `${backendUrl}/api/video/${material.video_file}`;
    }
    // Если нет загруженного файла, используем внешний URL
    else if (material.video_url) {
      videoUrl = material.video_url;
    }
    
    if (videoUrl) {
      setSelectedVideo({
        url: videoUrl,
        title: material.title,
        description: material.description,
        material: material
      });
    }
  };

  const openPDFMaterial = (material) => {
    // УНИФИКАЦИЯ: используем точно такую же логику как в PersonalConsultations
    let pdfUrl = null;
    
    // Приоритет: pdf_file_id (загруженный файл через consultations endpoint)
    if (material.pdf_file_id) {
      pdfUrl = `${backendUrl}/api/consultations/pdf/${material.pdf_file_id}`;
    }
    // Если нет pdf_file_id, проверяем старое поле file_url
    else if (material.file_url) {
      if (material.file_url.startsWith('http')) {
        pdfUrl = material.file_url;
      } else {
        pdfUrl = `${backendUrl}${material.file_url.startsWith('/') ? '' : '/'}${material.file_url}`;
      }
    }
    
    if (pdfUrl) {
      setSelectedPDF({
        url: pdfUrl,
        title: material.title,
        material: material
      });
    }
  };

  // Определяет тип материала на основе данных (УНИФИЦИРОВАНО)
  const getMaterialType = (material) => {
    // Приоритет: новые поля video_file_id/pdf_file_id
    if (material.video_file_id || material.video_url || material.video_file) {
      return 'video';
    }
    if (material.pdf_file_id || (material.file_url && (material.file_url.includes('.pdf') || material.material_type === 'pdf'))) {
      return 'pdf';
    }
    return 'unknown';
  };

  // Получает URL для видео (УНИФИЦИРОВАНО С PERSONALCONSULTATIONS)
  const getVideoUrl = (material) => {
    console.log('Material data:', material); // Debug log
    
    // Приоритет 1: video_file_id - загруженный файл через consultations endpoint
    if (material.video_file_id) {
      console.log('Using video_file_id:', material.video_file_id);
      return `${backendUrl}/api/consultations/video/${material.video_file_id}`;
    }
    
    // Приоритет 2: video_file - старый способ загрузки (совместимость)
    if (material.video_file) {
      console.log('Using video_file:', material.video_file);
      return `${backendUrl}/api/video/${material.video_file}`;
    }
    
    // Приоритет 3: video_url - внешние ссылки (YouTube и т.д.)
    if (material.video_url) {
      console.log('Using video_url:', material.video_url);
      
      // YouTube ссылки конвертируем в embed формат
      if (material.video_url.includes('youtube.com') || material.video_url.includes('youtu.be')) {
        let videoId = '';
        if (material.video_url.includes('youtube.com/watch?v=')) {
          videoId = material.video_url.split('v=')[1].split('&')[0];
        } else if (material.video_url.includes('youtu.be/')) {
          videoId = material.video_url.split('youtu.be/')[1].split('?')[0];
        }
        if (videoId) {
          return `https://www.youtube.com/embed/${videoId}`;
        }
      }
      return material.video_url;
    }
    
    console.log('No video URL found in material:', material);
    return null;
  };

  // Получает правильный URL для PDF (УНИФИЦИРОВАНО С PERSONALCONSULTATIONS)
  const getPdfUrl = (material) => {
    // Приоритет 1: pdf_file_id - загруженный файл через consultations endpoint
    if (material.pdf_file_id) {
      return `${backendUrl}/api/consultations/pdf/${material.pdf_file_id}`;
    }
    
    // Приоритет 2: file_url - старый способ (совместимость)
    if (material.file_url) {
      // Если file_url уже содержит полный URL
      if (material.file_url.startsWith('http')) {
        return material.file_url;
      }
      
      // Если file_url является относительным путем
      return `${backendUrl}${material.file_url.startsWith('/') ? '' : '/'}${material.file_url}`;
    }
    
    return null;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        <Loader2 className="w-5 h-5 animate-spin mr-2" /> Загружаем материалы...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Методические материалы</CardTitle>
          <CardDescription>PDF-файлы, доступные для просмотра студентам</CardDescription>
        </CardHeader>
        <CardContent>
          {error && <div className="text-red-600 mb-4">{error}</div>}
          {materials.length === 0 ? (
            <div className="text-center text-muted-foreground py-10">Пока нет загруженных материалов</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {materials.map((m) => {
                const materialType = getMaterialType(m);
                return (
                  <Card key={m.id} className={materialType === 'video' ? "border-blue-100" : "border-green-100"}>
                    <CardContent className="p-4 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded flex items-center justify-center ${
                          materialType === 'video' ? 'bg-blue-50' : 'bg-green-50'
                        }`}>
                          {materialType === 'video' ? (
                            <Video className="w-5 h-5 text-blue-600" />
                          ) : (
                            <FileText className="w-5 h-5 text-green-600" />
                          )}
                        </div>
                        <div>
                          <div className="font-medium">{m.title}</div>
                          <div className="text-xs text-muted-foreground">
                            {m.description || (materialType === 'video' ? 'Видео материал' : 'PDF материал')}
                          </div>
                          {materialType === 'video' && (
                            <div className="text-xs text-blue-600 font-medium mt-1">
                              🎥 Видео урок
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button size="sm" variant="outline" onClick={() => materialType === 'video' ? openVideoMaterial(m) : openPDFMaterial(m)}>
                          {materialType === 'video' ? (
                            <>
                              <Play className="w-4 h-4 mr-1" /> Воспроизвести
                            </>
                          ) : (
                            <>
                              <Eye className="w-4 h-4 mr-1" /> Открыть
                            </>
                          )}
                        </Button>
                        {materialType === 'pdf' && m.file_url && (
                          <Button size="sm" className="hidden sm:inline-flex" variant="ghost" onClick={() => window.open(getPdfUrl(m), '_blank')}>
                            <DownloadCloud className="w-4 h-4 mr-1" />
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {selectedVideo && (
        <EnhancedVideoViewer
          videoUrl={selectedVideo.url}
          title={selectedVideo.title}
          description={selectedVideo.description}
          onClose={() => setSelectedVideo(null)}
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

export default Materials;