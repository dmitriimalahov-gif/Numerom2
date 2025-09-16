import React, { useEffect, useRef, useState } from 'react';
import { X, ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from 'lucide-react';
import { Button } from './ui/button';
import * as pdfjsLib from 'pdfjs-dist';

// Use CDN worker to avoid bundler worker configuration issues
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.10.38/pdf.worker.min.js';

const PDFViewer = ({ url, token, onClose, title = 'Просмотр PDF' }) => {
  const canvasRef = useRef(null);
  const [pdfDoc, setPdfDoc] = useState(null);
  const [pageNum, setPageNum] = useState(1);
  const [numPages, setNumPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [zoom, setZoom] = useState(100);

  const loadPdf = async () => {
    setLoading(true);
    setError('');
    try {
      // Создаем headers только если токен предоставлен
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch(url, { headers });
      if (!res.ok) throw new Error('Не удалось загрузить PDF');
      const arrayBuffer = await res.arrayBuffer();
      const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });
      const doc = await loadingTask.promise;
      setPdfDoc(doc);
      setNumPages(doc.numPages);
      setPageNum(1);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const renderPage = async (num) => {
    if (!pdfDoc || !canvasRef.current) return;
    const page = await pdfDoc.getPage(num);
    
    // Получаем размеры контейнера
    const container = canvasRef.current.parentElement;
    const containerWidth = container.offsetWidth - 32; // учитываем padding
    const containerHeight = container.offsetHeight - 32;
    
    // Получаем исходные размеры страницы PDF
    const viewportScale1 = page.getViewport({ scale: 1 });
    
    // АВТОМАТИЧЕСКАЯ ПОДГОНКА ПОД ШИРИНУ ПЛЕЕРА:
    // Вычисляем scale для точного соответствия ширине контейнера
    const scaleToFitWidth = containerWidth / viewportScale1.width;
    
    // Проверяем не превышает ли высота при подгонке по ширине
    const heightAtWidthScale = viewportScale1.height * scaleToFitWidth;
    const scaleToFitHeight = containerHeight / viewportScale1.height;
    
    // Выбираем минимальный scale чтобы PDF полностью помещался
    let baseScale = Math.min(scaleToFitWidth, scaleToFitHeight);
    
    // Ограничиваем максимальный масштаб для качества
    baseScale = Math.min(baseScale, 3.0);
    
    // Применяем пользовательский zoom поверх автоматической подгонки
    const finalScale = baseScale * (zoom / 100);
    
    console.log(`PDF Auto-fit: Container ${containerWidth}x${containerHeight}, PDF ${viewportScale1.width}x${viewportScale1.height}, Scale: ${baseScale.toFixed(2)}, Final: ${finalScale.toFixed(2)}`);
    
    const viewport = page.getViewport({ scale: finalScale });
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    
    // Устанавливаем размеры canvas
    canvas.height = viewport.height;
    canvas.width = viewport.width;
    
    // Устанавливаем CSS размеры для адаптивности
    canvas.style.maxWidth = '100%';
    canvas.style.maxHeight = '100%';
    canvas.style.objectFit = 'contain';
    
    const renderContext = { canvasContext: context, viewport };
    await page.render(renderContext).promise;
  };

  // Функции управления zoom
  const handleZoomIn = () => {
    const newZoom = Math.min(zoom + 25, 200);
    setZoom(newZoom);
  };

  const handleZoomOut = () => {
    const newZoom = Math.max(zoom - 25, 50);
    setZoom(newZoom);
  };

  const handleFitToScreen = () => {
    // Сбрасываем zoom к 100% чтобы использовать только автоматическую подгонку
    setZoom(100);
  };

  useEffect(() => { loadPdf(); /* eslint-disable-next-line */ }, [url]);
  useEffect(() => { if (pdfDoc) renderPage(pageNum); /* eslint-disable-next-line */ }, [pdfDoc, pageNum, zoom]);
  
  // Обработчик изменения размера окна для адаптивности
  useEffect(() => {
    const handleResize = () => {
      if (pdfDoc && canvasRef.current) {
        // Перерисовываем страницу при изменении размера
        setTimeout(() => renderPage(pageNum), 100);
      }
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [pdfDoc, pageNum, zoom]);

  const prevPage = () => setPageNum((p) => Math.max(1, p - 1));
  const nextPage = () => setPageNum((p) => Math.min(numPages, p + 1));

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-2 sm:p-6">
      <div className="bg-white rounded-lg w-full max-w-[100vw] sm:max-w-5xl h-[95vh] sm:h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between p-3 border-b bg-white flex-shrink-0">
          <div className="font-semibold truncate pr-2 text-sm sm:text-base">{title}</div>
          
          <div className="flex items-center gap-1 sm:gap-2">
            {/* Desktop контролы zoom */}
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
            </div>
            
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-5 h-5" />
            </Button>
          </div>
        </div>
        
        {/* Мобильные контролы zoom */}
        <div className="sm:hidden flex items-center justify-center gap-2 p-2 border-b bg-gray-50">
          <Button
            variant="outline"
            size="sm"
            onClick={handleZoomOut}
            disabled={zoom <= 50}
            className="flex items-center px-3 py-1"
          >
            <ZoomOut className="w-4 h-4 mr-1" />
            Уменьшить
          </Button>
          
          <div className="px-3 py-1 bg-white border rounded text-sm font-medium min-w-[4rem] text-center">
            {zoom}%
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleZoomIn}
            disabled={zoom >= 200}
            className="flex items-center px-3 py-1"
          >
            <ZoomIn className="w-4 h-4 mr-1" />
            Увеличить
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleFitToScreen}
            className="flex items-center px-3 py-1"
          >
            Авто
          </Button>
        </div>
        
        <div className="flex-1 overflow-auto flex flex-col items-center justify-center bg-gray-50 p-2 sm:p-4">
          {loading && <div className="text-muted-foreground p-4 text-center">Загрузка…</div>}
          {error && <div className="text-red-600 p-4 text-center text-sm">{error}</div>}
          <canvas 
            ref={canvasRef} 
            className="shadow bg-white max-w-full h-auto" 
            style={{ maxWidth: '100%', height: 'auto' }}
          />
        </div>
        <div className="p-3 border-t flex items-center justify-between bg-white flex-shrink-0">
          <div className="text-xs sm:text-sm text-muted-foreground">Стр. {pageNum} из {numPages}</div>
          <div className="flex items-center gap-1 sm:gap-2">
            <Button variant="outline" size="sm" onClick={prevPage} disabled={pageNum <= 1}>
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={nextPage} disabled={pageNum >= numPages}>
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PDFViewer;