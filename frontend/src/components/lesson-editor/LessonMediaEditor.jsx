import React, { useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Upload, Loader, Cloud, CheckCircle2, Eye } from 'lucide-react';
import { getApiBaseUrl } from '../../utils/backendUrl';

/**
 * LESSON MEDIA EDITOR
 * Компонент для управления медиа файлами урока
 *
 * Props:
 * - editingLesson: объект урока
 * - onVideoUpload: (event) => Promise<void>
 * - onPDFUpload: (event) => Promise<void>
 * - onWordUpload: (event) => Promise<void>
 * - uploadingVideo: boolean
 * - uploadingPDF: boolean
 * - uploadingWord: boolean
 */
const LessonMediaEditor = ({
  editingLesson,
  onVideoUpload,
  onPDFUpload,
  onWordUpload,
  uploadingVideo = false,
  uploadingPDF = false,
  uploadingWord = false
}) => {
  const videoInputRef = useRef(null);
  const pdfInputRef = useRef(null);
  const wordInputRef = useRef(null);
  const apiBaseUrl = getApiBaseUrl();

  const openInNewTab = (url) => {
    if (!url) return;
    window.open(url, '_blank');
  };

  const getConsultationAssetUrl = (type, id) => {
    if (!id) return null;
    return `${apiBaseUrl}/consultations/${type}/${id}`;
  };

  const getLessonWordUrl = (id) => {
    if (!id) return null;
    return `${apiBaseUrl}/lessons/word/${id}`;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Cloud className="w-5 h-5 text-blue-600" />
          Медиа файлы (Bunny.net CDN)
        </CardTitle>
        <p className="text-sm text-gray-500 mt-2">
          Файлы загружаются на CDN и становятся доступны студентам сразу после сохранения урока
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Загрузка видео */}
        <div>
          <Label>Видео урока</Label>
          <div className="flex items-center gap-3 mt-2">
            <input
              ref={videoInputRef}
              type="file"
              accept="video/*"
              className="hidden"
              onChange={onVideoUpload}
              disabled={uploadingVideo}
            />
            <Button
              onClick={() => videoInputRef.current?.click()}
              disabled={uploadingVideo}
              variant="outline"
              className="flex-1"
            >
              {uploadingVideo ? (
                <>
                  <Loader className="w-4 h-4 mr-2 animate-spin" />
                  Загрузка...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Загрузить видео
                </>
              )}
            </Button>
          </div>
          {(editingLesson?.video_filename || editingLesson?.video_file_id) && (
            <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded flex justify-between items-center">
              <div>
                <p className="text-sm text-green-600">✓ Видео: {editingLesson.video_filename || 'Видео файл загружен'}</p>
                {editingLesson?.video_status === 'processing' && (
                  <p className="text-xs text-yellow-600 mt-1">Обрабатывается...</p>
                )}
              </div>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => {
                    const videoUrl = editingLesson.video_file_id 
                    ? getConsultationAssetUrl('video', editingLesson.video_file_id)
                      : editingLesson.video_url;
                  openInNewTab(videoUrl);
                  }}
                >
                  <Eye className="w-3 h-3 mr-1" />
                  Просмотр
              </Button>
            </div>
          )}
          <p className="text-xs text-gray-500 mt-1">Поддерживаются любые видеофайлы до 500MB</p>
        </div>

        {/* Загрузка PDF */}
        <div>
          <Label>PDF материалы</Label>
          <div className="flex items-center gap-3 mt-2">
            <input
              ref={pdfInputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={onPDFUpload}
              disabled={uploadingPDF}
            />
            <Button
              onClick={() => pdfInputRef.current?.click()}
              disabled={uploadingPDF}
              variant="outline"
              className="flex-1"
            >
              {uploadingPDF ? (
                <>
                  <Loader className="w-4 h-4 mr-2 animate-spin" />
                  Загрузка...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Загрузить PDF
                </>
              )}
            </Button>
          </div>
          {(editingLesson?.pdf_filename || editingLesson?.pdf_file_id) && (
            <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded flex justify-between items-center">
              <p className="text-sm text-green-600">✓ PDF: {editingLesson.pdf_filename || 'PDF файл загружен'}</p>
                <Button 
                  size="sm" 
                  variant="outline"
                onClick={() => openInNewTab(getConsultationAssetUrl('pdf', editingLesson.pdf_file_id))}
                >
                  <Eye className="w-3 h-3 mr-1" />
                  Просмотр
                </Button>
            </div>
          )}
          <p className="text-xs text-gray-500 mt-1">Только PDF файлы. Максимум: 50MB</p>
        </div>

        {/* Загрузка Word */}
        <div>
          <Label>Word документы</Label>
          <div className="flex items-center gap-3 mt-2">
            <input
              ref={wordInputRef}
              type="file"
              accept=".doc,.docx,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              className="hidden"
              onChange={onWordUpload}
              disabled={uploadingWord}
            />
            <Button
              onClick={() => wordInputRef.current?.click()}
              disabled={uploadingWord}
              variant="outline"
              className="flex-1"
            >
              {uploadingWord ? (
                <>
                  <Loader className="w-4 h-4 mr-2 animate-spin" />
                  Загрузка...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Загрузить Word
                </>
              )}
            </Button>
          </div>
          {(editingLesson?.word_filename || editingLesson?.word_file_id) && (
            <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded flex justify-between items-center">
              <p className="text-sm text-green-600">✓ Word: {editingLesson.word_filename || 'Word файл загружен'}</p>
                <Button 
                  size="sm" 
                  variant="outline"
                onClick={() => openInNewTab(getLessonWordUrl(editingLesson.word_file_id))}
                >
                  <Eye className="w-3 h-3 mr-1" />
                  Просмотр
                </Button>
            </div>
          )}
          <p className="text-xs text-gray-500 mt-1">Форматы: .doc, .docx. Максимум: 50MB</p>
        </div>

        {/* Пустое состояние */}
        {(!editingLesson?.video_filename && !editingLesson?.video_file_id && 
          !editingLesson?.pdf_filename && !editingLesson?.pdf_file_id && 
          !editingLesson?.word_filename && !editingLesson?.word_file_id) && (
          <div className="text-center py-6 text-gray-400">
            <Upload className="w-12 h-12 mx-auto mb-2" />
            <p className="text-sm">Медиа файлы еще не загружены</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default LessonMediaEditor;
