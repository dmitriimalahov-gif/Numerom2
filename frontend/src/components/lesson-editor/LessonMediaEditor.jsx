import React, { useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Upload, Video, FileText, Loader, Cloud, CheckCircle2 } from 'lucide-react';

/**
 * LESSON MEDIA EDITOR
 * Компонент для загрузки и управления медиа файлами урока
 *
 * Props:
 * - editingLesson: объект урока
 * - onVideoUpload: (event) => Promise<void>
 * - onPDFUpload: (event) => Promise<void>
 * - uploadingVideo: boolean
 * - uploadingPDF: boolean
 */
const LessonMediaEditor = ({
  editingLesson,
  onVideoUpload,
  onPDFUpload,
  uploadingVideo = false,
  uploadingPDF = false
}) => {
  const videoInputRef = useRef(null);
  const pdfInputRef = useRef(null);

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
          {editingLesson?.video_filename && (
            <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-md">
              <div className="flex items-center gap-2 text-sm text-green-700">
                <CheckCircle2 className="w-4 h-4" />
                <span className="font-medium">{editingLesson.video_filename}</span>
              </div>
              {editingLesson?.video_status === 'processing' && (
                <div className="mt-2 flex items-center gap-2 text-xs text-yellow-600">
                  <Loader className="w-3 h-3 animate-spin" />
                  <span>Обрабатывается на Bunny.net...</span>
                </div>
              )}
              {editingLesson?.video_status === 'ready' && (
                <div className="mt-1 text-xs text-green-600 flex items-center gap-1">
                  <Cloud className="w-3 h-3" />
                  <span>Загружено на CDN</span>
                </div>
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
          {editingLesson?.pdf_filename && (
            <div className="mt-2 flex items-center gap-2 text-sm text-green-600">
              <FileText className="w-4 h-4" />
              <span>{editingLesson.pdf_filename}</span>
            </div>
          )}
          <p className="text-xs text-gray-500 mt-1">
            Только PDF файлы. Максимум: 50MB
          </p>
        </div>

        {/* Информация о файлах */}
        {(!editingLesson?.video_filename && !editingLesson?.pdf_filename) && (
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
