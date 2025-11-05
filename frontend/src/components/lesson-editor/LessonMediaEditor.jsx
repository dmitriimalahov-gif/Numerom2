import React, { useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Upload, Video, FileText, Loader, Cloud, CheckCircle2, File, Eye } from 'lucide-react';

/**
 * LESSON MEDIA EDITOR
 * Компонент для загрузки и управления медиа файлами урока
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

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Cloud className="w-5 h-5 text-blue-600" />
          Медиа файлы (Bunny.net CDN)
        </CardTitle>
        <p className="text-sm text-gray-500 mt-2">
          Файлы загружаются на Bunny.net CDN для быстрого и безопасного стриминга
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
              {editingLesson.video_file_id && (
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => {
                    const videoUrl = editingLesson.video_file_id 
                      ? `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/consultations/video/${editingLesson.video_file_id}`
                      : editingLesson.video_url;
                    window.open(videoUrl, '_blank');
                  }}
                >
                  <Eye className="w-3 h-3 mr-1" />
                  Просмотр
                </Button>
              )}
            </div>
          )}
          <p className="text-xs text-gray-500 mt-1">
            Форматы: MP4, AVI, MOV, WEBM. Максимум: 500MB. Загружается на Bunny.net CDN.
          </p>
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
              {editingLesson.pdf_file_id && (
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => {
                    window.open(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/consultations/pdf/${editingLesson.pdf_file_id}`, '_blank');
                  }}
                >
                  <Eye className="w-3 h-3 mr-1" />
                  Просмотр
                </Button>
              )}
            </div>
          )}
          <p className="text-xs text-gray-500 mt-1">
            Только PDF файлы. Максимум: 50MB
          </p>
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
              {editingLesson.word_file_id && (
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => {
                    window.open(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/lessons/word/${editingLesson.word_file_id}`, '_blank');
                  }}
                >
                  <Eye className="w-3 h-3 mr-1" />
                  Просмотр
                </Button>
              )}
            </div>
          )}
          <p className="text-xs text-gray-500 mt-1">
            Форматы: .doc, .docx. Максимум: 50MB
          </p>
        </div>

        {/* Информация о файлах */}
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
