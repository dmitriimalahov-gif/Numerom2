import React, { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { X, Download, ExternalLink, FileText, AlertCircle, Loader2, ZoomIn, ZoomOut, RotateCw } from 'lucide-react';

const ConsultationPDFViewer = ({ pdfUrl, title, onClose }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [zoom, setZoom] = useState(100);
  const iframeRef = useRef(null);

  const handleLoad = () => {
    setLoading(false);
    // Автоматически подгоняем PDF под ширину плеера
    setTimeout(() => {
      calculateOptimalZoom();
    }, 500); // Небольшая задержка для полной загрузки iframe
  };

  // Вычисление оптимального масштаба для автоподгонки под ширину
  const calculateOptimalZoom = () => {
    if (iframeRef.current) {
      const iframe = iframeRef.current;
      const container = iframe.parentElement;
      
      if (container) {
        // Получаем ширину контейнера плеера
        const containerWidth = container.offsetWidth;
        
        // Стандартная ширина PDF A4 в пикселях при zoom=100%
        const standardPDFWidth = 595; 
        
        // Вычисляем zoom процент для заполнения ширины контейнера
        const calculatedZoom = Math.round((containerWidth / standardPDFWidth) * 100);
        
        // Ограничиваем диапазон для читаемости
        const optimalZoom = Math.max(50, Math.min(calculatedZoom, 200));
        
        console.log(`PDF Auto-fit: Container ${containerWidth}px, Calculated zoom: ${optimalZoom}%`);
        setZoom(optimalZoom);
      }
    }
  };

  const handleError = () => {
    setLoading(false);
    setError(true);
  };

  // Функции управления масштабом
  const handleZoomIn = () => {
    const newZoom = Math.min(zoom + 20, 150);
    setZoom(newZoom);
  };

  const handleZoomOut = () => {
    const newZoom = Math.max(zoom - 20, 50);
    setZoom(newZoom);
  };

  const handleFitToScreen = () => {
    // Пересчитываем оптимальный размер под текущую ширину контейнера
    calculateOptimalZoom();
  };

  // Применение масштаба к PDF файлу через URL параметры
  const applyZoom = () => {
    if (iframeRef.current) {
      // Вместо CSS transform используем zoom параметр PDF
      const zoomPercent = zoom;
      
      // Создаем новый URL с правильным zoom
      const newSrc = `${pdfUrl}#toolbar=0&navpanes=0&scrollbar=1&page=1&view=FitH&zoom=${zoomPercent}`;
      
      // Обновляем src iframe для применения нового масштаба PDF
      if (iframeRef.current.src !== newSrc) {
        iframeRef.current.src = newSrc;
      }
      
      console.log(`Applying PDF zoom: ${zoomPercent}%`);
    }
  };

  // Применяем zoom при его изменении
  useEffect(() => {
    if (!loading && !error) {
      applyZoom();
    }
  }, [zoom, loading, error]);

  // Автоматический пересчет масштаба при изменении размера окна
  useEffect(() => {
    const handleResize = () => {
      if (!loading && !error && iframeRef.current) {
        setTimeout(() => {
          calculateOptimalZoom();
        }, 100);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [loading, error]);

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = pdfUrl;
    link.download = `${title || 'consultation-document'}.pdf`;
    link.click();
  };

  const handleExternalOpen = () => {
    window.open(pdfUrl, '_blank');
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-2 sm:p-4">
      <Card className="w-full max-w-[100vw] sm:max-w-6xl max-h-[100vh] sm:max-h-[95vh] overflow-hidden">
        <CardHeader className="bg-gray-50 border-b p-2 sm:p-4">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center text-sm sm:text-lg truncate">
              <FileText className="w-4 h-4 sm:w-5 sm:h-5 mr-2 text-red-600 flex-shrink-0" />
              <span className="truncate">{title || 'PDF Консультация'}</span>
            </CardTitle>
            
            <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
              {/* Desktop контролы масштабирования */}
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
                  disabled={zoom >= 150}
                  className="p-1 h-6 w-6"
                >
                  <ZoomIn className="w-3 h-3" />
                </Button>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleFitToScreen}
                  className="text-xs px-2 py-1 h-6"
                  title="По размеру экрана"
                >
                  Авто
                </Button>
              </div>

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
          <div className="sm:hidden flex items-center justify-center gap-2 mt-3 pt-3 border-t">
            <Button
              variant="outline"
              size="sm"
              onClick={handleZoomOut}
              disabled={zoom <= 50}
              className="flex items-center px-3 py-2"
            >
              <ZoomOut className="w-4 h-4 mr-1" />
              Уменьшить
            </Button>
            
            <div className="px-3 py-2 bg-white border rounded text-sm font-medium min-w-[4rem] text-center">
              {zoom}%
            </div>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleZoomIn}
              disabled={zoom >= 150}
              className="flex items-center px-3 py-2"
            >
              <ZoomIn className="w-4 h-4 mr-1" />
              Увеличить
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleFitToScreen}
              className="flex items-center px-3 py-2"
              title="Подогнать под экран"
            >
              <RotateCw className="w-4 h-4 mr-1" />
              Авто
            </Button>
          </div>
        </CardHeader>
        
        <CardContent className="p-0 relative overflow-hidden">
          {/* Loading Indicator */}
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-100 z-10">
              <div className="text-center">
                <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2 text-gray-500" />
                <p className="text-sm text-gray-600 px-4">Загрузка PDF консультации...</p>
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
                height: '75vh',
                minHeight: '500px',
                maxWidth: '100%',
                display: 'block'
              }}
              onLoad={handleLoad}
              onError={handleError}
              title={title || 'PDF Consultation'}
              allowFullScreen
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ConsultationPDFViewer;