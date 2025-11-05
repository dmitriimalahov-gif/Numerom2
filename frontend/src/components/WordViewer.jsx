import React, { useState, useRef } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { X, Download, ExternalLink, File, AlertCircle, Loader2, ZoomIn, ZoomOut } from 'lucide-react';

const WordViewer = ({ wordUrl, title, onClose, backendUrl }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const iframeRef = useRef(null);

  // Используем Google Docs Viewer для просмотра Word файлов
  const getViewerUrl = () => {
    if (!wordUrl) return null;
    
    // Если URL относительный, добавляем backend URL
    const fullUrl = wordUrl.startsWith('http') ? wordUrl : `${backendUrl}${wordUrl}`;
    
    // Используем Google Docs Viewer для .doc и .docx файлов
    return `https://docs.google.com/viewer?url=${encodeURIComponent(fullUrl)}&embedded=true`;
  };

  const handleLoad = () => {
    setLoading(false);
  };

  const handleError = () => {
    setLoading(false);
    setError(true);
  };

  const handleDownload = () => {
    const fullUrl = wordUrl.startsWith('http') ? wordUrl : `${backendUrl}${wordUrl}`;
    window.open(fullUrl, '_blank');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-6xl h-[90vh] flex flex-col">
        <CardHeader className="flex-shrink-0 flex items-center justify-between border-b">
          <CardTitle className="flex items-center gap-2">
            <File className="w-5 h-5 text-blue-600" />
            {title || 'Просмотр Word документа'}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownload}
              className="flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Скачать
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="flex items-center gap-2"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-hidden p-0 relative">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
              <div className="text-center">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
                <p className="text-sm text-gray-600">Загрузка документа...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
              <div className="text-center p-6">
                <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Не удалось загрузить документ
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Попробуйте скачать файл и открыть его локально
                </p>
                <div className="flex gap-2 justify-center">
                  <Button onClick={handleDownload} variant="outline">
                    <Download className="w-4 h-4 mr-2" />
                    Скачать файл
                  </Button>
                  <Button onClick={onClose} variant="ghost">
                    Закрыть
                  </Button>
                </div>
              </div>
            </div>
          )}

          {!error && (
            <iframe
              ref={iframeRef}
              src={getViewerUrl()}
              className={`w-full h-full border-0 bg-white ${loading ? 'invisible' : 'visible'}`}
              style={{
                width: '100%',
                height: '100%',
                minHeight: '500px',
                display: 'block'
              }}
              onLoad={handleLoad}
              onError={handleError}
              title={title || 'Word Document'}
              allowFullScreen
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default WordViewer;
