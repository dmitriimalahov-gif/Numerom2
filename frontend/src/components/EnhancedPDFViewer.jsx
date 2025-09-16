import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { X, Download, ExternalLink, FileText, AlertCircle, Loader2, ZoomIn, ZoomOut, RotateCw } from 'lucide-react';

const EnhancedPDFViewer = ({ pdfUrl, title, onClose }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [zoom, setZoom] = useState(100);
  const iframeRef = useRef(null);

  const handleLoad = () => {
    setLoading(false);
    // Применяем начальное масштабирование
    applyZoom();
  };

  const handleError = () => {
    setLoading(false);
    setError(true);
  };

  const handleZoomIn = () => {
    const newZoom = Math.min(zoom + 25, 200);
    setZoom(newZoom);
  };

  const handleZoomOut = () => {
    const newZoom = Math.max(zoom - 25, 50);
    setZoom(newZoom);
  };

  const handleFitToWidth = () => {
    // Автоматическая подгонка PDF файла под ширину контейнера
    if (iframeRef.current) {
      const iframe = iframeRef.current;
      const container = iframe.parentElement;
      
      if (container) {
        const containerWidth = container.offsetWidth;
        
        // Стандартная ширина PDF A4 при 100% zoom
        const standardPDFWidth = 595;
        
        // Вычисляем zoom для заполнения ширины
        let calculatedZoom = Math.round((containerWidth / standardPDFWidth) * 100);
        
        // Корректируем для мобильных устройств
        const isMobile = window.innerWidth < 768;
        if (isMobile) {
          calculatedZoom = Math.round(calculatedZoom * 0.95); // чуть меньше для мобильных
        }
        
        // Ограничиваем диапазон
        const optimalZoom = Math.max(50, Math.min(calculatedZoom, 200));
        
        console.log(`Enhanced PDF Auto-fit: Container ${containerWidth}px, Calculated zoom: ${optimalZoom}%`);
        setZoom(optimalZoom);
      }
    }
  };

  const applyZoom = () => {
    if (iframeRef.current) {
      // Применяем zoom к самому PDF файлу через URL параметры
      const zoomPercent = zoom;
      const newSrc = `${pdfUrl}#toolbar=0&navpanes=0&scrollbar=1&page=1&view=FitH&zoom=${zoomPercent}`;
      
      if (iframeRef.current.src !== newSrc) {
        iframeRef.current.src = newSrc;
      }
    }
  };

  // Применяем zoom при его изменении
  useEffect(() => {
    applyZoom();
  }, [zoom]);

  // Автоматическое подгонка под экран при загрузке
  useEffect(() => {
    if (!loading && !error) {
      setTimeout(handleFitToWidth, 500);
    }
  }, [loading, error]);

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = pdfUrl;
    link.download = `${title || 'document'}.pdf`;
    link.click();
  };

  const handleExternalOpen = () => {
    window.open(pdfUrl, '_blank');
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-2 sm:p-4">
      <Card className="w-full max-w-[100vw] sm:max-w-7xl max-h-[100vh] sm:max-h-[95vh] overflow-hidden flex flex-col">
        <CardHeader className="bg-gray-50 border-b p-2 sm:p-4 flex-shrink-0">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center text-sm sm:text-lg truncate">
              <FileText className="w-4 h-4 sm:w-5 sm:h-5 mr-2 text-red-600 flex-shrink-0" />
              <span className="truncate">{title || 'PDF Документ'}</span>
            </CardTitle>
            
            <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
              {/* Контролы масштабирования */}
              <div className="hidden sm:flex items-center gap-1 border rounded px-2 py-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleZoomOut}
                  disabled={zoom <= 50}
                  className="p-1 h-6 w-6"
                >
                  <ZoomOut className="w-3 h-3" />
                </Button>
                
                <span className="text-xs min-w-[3rem] text-center">{zoom}%</span>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleZoomIn}
                  disabled={zoom >= 200}
                  className="p-1 h-6 w-6"
                >
                  <ZoomIn className="w-3 h-3" />
                </Button>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleFitToWidth}
                  className="text-xs px-2 py-1 h-6"
                  title="Подогнать по ширине"
                >
                  По ширине
                </Button>
              </div>

              {/* Кнопки действий */}
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownload}
                className="text-xs hidden sm:flex"
              >
                <Download className="w-4 h-4 mr-1" />
                Скачать
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleExternalOpen}
                className="text-xs hidden sm:flex"
              >
                <ExternalLink className="w-4 h-4 mr-1" />
                Открыть отдельно
              </Button>
              
              {/* Мобильные кнопки */}
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownload}
                className="sm:hidden p-2"
                title="Скачать"
              >
                <Download className="w-4 h-4" />
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleExternalOpen}
                className="sm:hidden p-2"
                title="Открыть отдельно"
              >
                <ExternalLink className="w-4 h-4" />
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={onClose}
                className="p-2"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>
          
          {/* Мобильные контролы масштабирования */}
          <div className="sm:hidden flex items-center justify-center gap-2 mt-2 pt-2 border-t">
            <Button
              variant="outline"
              size="sm"
              onClick={handleZoomOut}
              disabled={zoom <= 50}
              className="flex-1"
            >
              <ZoomOut className="w-4 h-4 mr-1" />
              Уменьшить
            </Button>
            
            <div className="px-3 py-1 bg-gray-100 rounded text-sm min-w-[4rem] text-center">
              {zoom}%
            </div>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleZoomIn}
              disabled={zoom >= 200}
              className="flex-1"
            >
              <ZoomIn className="w-4 h-4 mr-1" />
              Увеличить
            </Button>
          </div>
        </CardHeader>
        
        <CardContent className="p-0 relative flex-1 overflow-auto">
          {/* Loading Indicator */}
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-100 z-10">
              <div className="text-center">
                <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2 text-gray-500" />
                <p className="text-sm text-gray-600 px-4">Загрузка PDF документа...</p>
              </div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="h-64 sm:h-96 flex items-center justify-center bg-gray-50 p-4">
              <div className="text-center">
                <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">Ошибка загрузки PDF</h3>
                <p className="text-gray-600 mb-4 text-sm">
                  PDF не удалось загрузить в браузере
                </p>
                <div className="flex flex-col sm:flex-row gap-2 justify-center">
                  <Button onClick={handleExternalOpen} variant="outline" size="sm">
                    <ExternalLink className="w-4 h-4 mr-2" />
                    Открыть в новой вкладке
                  </Button>
                  <Button onClick={handleDownload} size="sm">
                    <Download className="w-4 h-4 mr-2" />
                    Скачать файл
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* PDF Iframe - полная ширина от края до края */}
          <div className="w-full h-full overflow-auto bg-gray-100">
            <iframe
              ref={iframeRef}
              src={`${pdfUrl}#toolbar=0&navpanes=0&scrollbar=1&page=1&view=FitH&zoom=${zoom}`}
              className={`w-full border-0 bg-white ${loading ? 'invisible' : 'visible'}`}
              style={{
                width: '100%',
                height: '80vh',
                minHeight: '600px',
                maxWidth: '100%',
                display: 'block'
              }}
              onLoad={handleLoad}
              onError={handleError}
              title={title || 'PDF Document'}
              allowFullScreen
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default EnhancedPDFViewer;