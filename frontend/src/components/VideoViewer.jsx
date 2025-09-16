import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { X, ExternalLink, AlertCircle, Loader2, Download, Volume2 } from 'lucide-react';

const VideoViewer = ({ videoUrl, title, onClose, isYouTube = false }) => {
  const [videoError, setVideoError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [fileType, setFileType] = useState('video');
  const videoRef = useRef(null);
  const containerRef = useRef(null);
  const [isMobile, setIsMobile] = useState(false);

  // Определяем тип файла по URL
  const getFileType = (url) => {
    if (!url) return 'unknown';
    
    const extension = url.split('.').pop()?.toLowerCase();
    
    if (['mp4', 'webm', 'ogg', 'mov', 'avi'].includes(extension)) {
      return 'video';
    } else if (['mp3', 'wav', 'ogg', 'aac', 'm4a'].includes(extension)) {
      return 'audio';
    } else if (['pdf'].includes(extension)) {
      return 'pdf';
    } else if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(extension)) {
      return 'image';
    } else if (url.includes('youtube.com') || url.includes('youtu.be')) {
      return 'youtube';
    } else if (url.includes('vimeo.com')) {
      return 'vimeo';
    }
    
    return 'unknown';
  };

  useEffect(() => {
    // Определяем мобильное устройство
    const checkMobile = () => {
      const userAgent = navigator.userAgent || navigator.vendor || window.opera;
      return /android|avantgo|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino/i.test(userAgent);
    };
    
    setIsMobile(checkMobile());
    setFileType(getFileType(videoUrl));
    
    // Защита от скриншотов (только для desktop)
    if (!checkMobile()) {
      const preventScreenCapture = () => {
        const preventRightClick = (e) => {
          e.preventDefault();
          return false;
        };

        const preventKeyboardShortcuts = (e) => {
          if (
            e.key === 'F12' ||
            (e.ctrlKey && e.shiftKey && e.key === 'I') ||
            (e.ctrlKey && e.key === 'u') ||
            (e.ctrlKey && e.key === 's') ||
            e.key === 'PrintScreen'
          ) {
            e.preventDefault();
            return false;
          }
        };

        const handleVisibilityChange = () => {
          if (document.hidden && videoRef.current) {
            videoRef.current.pause();
          }
        };

        const preventSelection = (e) => {
          e.preventDefault();
          return false;
        };

        document.addEventListener('contextmenu', preventRightClick);
        document.addEventListener('keydown', preventKeyboardShortcuts);
        document.addEventListener('visibilitychange', handleVisibilityChange);
        document.addEventListener('selectstart', preventSelection);
        document.addEventListener('dragstart', preventSelection);

        if (containerRef.current) {
          containerRef.current.style.userSelect = 'none';
          containerRef.current.style.webkitUserSelect = 'none';
          containerRef.current.style.mozUserSelect = 'none';
          containerRef.current.style.msUserSelect = 'none';
        }

        return () => {
          document.removeEventListener('contextmenu', preventRightClick);
          document.removeEventListener('keydown', preventKeyboardShortcuts);
          document.removeEventListener('visibilitychange', handleVisibilityChange);
          document.removeEventListener('selectstart', preventSelection);
          document.removeEventListener('dragstart', preventSelection);
        };
      };

      const cleanup = preventScreenCapture();
      return cleanup;
    }
  }, [videoUrl]);

  const handleVideoError = (e) => {
    console.error('Media loading error:', e);
    setVideoError(true);
    setLoading(false);
  };

  const handleVideoLoad = () => {
    setLoading(false);
    setVideoError(false);
  };

  const renderMediaContent = () => {
    if (videoError) {
      return (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-100 select-none">
          <AlertCircle className="w-16 h-16 mb-4 text-red-500" />
          <p className="text-lg mb-4 text-center px-4">
            Не удалось загрузить медиафайл. 
          </p>
          <div className="flex flex-col sm:flex-row gap-2">
            <Button
              variant="outline"
              onClick={() => window.open(videoUrl, '_blank')}
              className="flex items-center"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              Открыть в браузере
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                const link = document.createElement('a');
                link.href = videoUrl;
                link.download = title || 'media-file';
                link.click();
              }}
              className="flex items-center"
            >
              <Download className="w-4 h-4 mr-2" />
              Скачать файл
            </Button>
          </div>
        </div>
      );
    }

    // Показываем loading индикатор
    if (loading) {
      return (
        <div className="absolute inset-0 flex items-center justify-center bg-black">
          <div className="text-center text-white">
            <Loader2 className="w-8 h-8 mx-auto mb-4 animate-spin" />
            <p>Загрузка медиафайла...</p>
          </div>
        </div>
      );
    }

    // Рендерим контент в зависимости от типа файла
    switch (fileType) {
      case 'video':
        return (
          <video
            ref={videoRef}
            src={videoUrl}
            controls
            controlsList={!isMobile ? "nodownload" : ""}
            disablePictureInPicture={!isMobile}
            className="absolute top-0 left-0 w-full h-full object-contain bg-black select-none"
            style={{ 
              userSelect: isMobile ? 'auto' : 'none',
              webkitUserSelect: isMobile ? 'auto' : 'none',
              mozUserSelect: isMobile ? 'auto' : 'none',
              msUserSelect: isMobile ? 'auto' : 'none',
              pointerEvents: 'auto'
            }}
            onError={handleVideoError}
            onLoadStart={() => setLoading(true)}
            onCanPlay={handleVideoLoad}
            onLoadedData={handleVideoLoad}
            onContextMenu={isMobile ? undefined : (e) => e.preventDefault()}
            draggable={false}
            playsInline // Важно для iOS
            webkit-playsinline="true" // Для старых версий iOS
          >
            <p className="text-center p-4 select-none text-white">
              Ваш браузер не поддерживает воспроизведение видео.{' '}
              <a href={videoUrl} target="_blank" rel="noopener noreferrer" className="text-blue-400 underline">
                Открыть видео в новой вкладке
              </a>
            </p>
          </video>
        );

      case 'audio':
        return (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
            <div className="text-center text-white p-8">
              <Volume2 className="w-16 h-16 mx-auto mb-6 text-blue-400" />
              <h3 className="text-xl mb-6">{title}</h3>
              <audio
                ref={videoRef}
                src={videoUrl}
                controls
                className="w-full max-w-md"
                onError={handleVideoError}
                onLoadStart={() => setLoading(true)}
                onCanPlay={handleVideoLoad}
                onLoadedData={handleVideoLoad}
                style={{ filter: 'invert(1)' }}
              >
                <p>
                  Ваш браузер не поддерживает воспроизведение аудио.{' '}
                  <a href={videoUrl} target="_blank" rel="noopener noreferrer" className="text-blue-400 underline">
                    Открыть аудио в новой вкладке
                  </a>
                </p>
              </audio>
            </div>
          </div>
        );

      case 'youtube':
      case 'vimeo':
        return (
          <iframe
            src={videoUrl}
            className="absolute top-0 left-0 w-full h-full"
            allowFullScreen
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            title={title}
            onLoad={handleVideoLoad}
          />
        );

      case 'pdf':
        return (
          <iframe
            src={videoUrl}
            className="absolute top-0 left-0 w-full h-full"
            title={title}
            onLoad={handleVideoLoad}
          />
        );

      case 'image':
        return (
          <img
            src={videoUrl}
            alt={title}
            className="absolute top-0 left-0 w-full h-full object-contain bg-black"
            onError={handleVideoError}
            onLoad={handleVideoLoad}
          />
        );

      default:
        // Для неизвестных типов файлов пытаемся использовать iframe
        return (
          <iframe
            src={videoUrl}
            className="absolute top-0 left-0 w-full h-full"
            title={title}
            onLoad={handleVideoLoad}
            onError={handleVideoError}
          />
        );
    }
  };

  return (
    <div 
      ref={containerRef}
      className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-2 sm:p-4"
      style={{ 
        userSelect: isMobile ? 'auto' : 'none', 
        webkitUserSelect: isMobile ? 'auto' : 'none',
        mozUserSelect: isMobile ? 'auto' : 'none',
        msUserSelect: isMobile ? 'auto' : 'none'
      }}
    >
      <div className="bg-white rounded-lg w-full max-w-5xl max-h-[95vh] overflow-hidden select-none">
        {/* Header */}
        <div className="flex items-center justify-between p-3 sm:p-4 border-b">
          <h3 className="text-base sm:text-lg font-semibold truncate pr-4 select-none flex items-center">
            {fileType === 'video' && <span className="mr-2">🎥</span>}
            {fileType === 'audio' && <span className="mr-2">🎵</span>}
            {fileType === 'pdf' && <span className="mr-2">📄</span>}
            {fileType === 'image' && <span className="mr-2">🖼️</span>}
            {title}
          </h3>
          <div className="flex items-center gap-2">
            {/* Mobile-friendly external link */}
            {isMobile && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => window.open(videoUrl, '_blank')}
                title="Открыть в браузере"
              >
                <ExternalLink className="w-4 h-4" />
              </Button>
            )}
            <Button
              size="sm"
              variant="outline"
              onClick={onClose}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Media Content */}
        <div className="relative select-none" style={{ 
          paddingBottom: fileType === 'audio' ? '0' : '56.25%', 
          height: fileType === 'audio' ? '400px' : '0',
          minHeight: isMobile ? '300px' : '400px'
        }}>
          {renderMediaContent()}
        </div>

        {/* Mobile controls footer */}
        {isMobile && !videoError && (
          <div className="p-3 bg-gray-50 border-t">
            <div className="flex justify-between items-center text-sm text-gray-600">
              <span>Тип: {fileType.toUpperCase()}</span>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => window.open(videoUrl, '_blank')}
                  className="text-xs"
                >
                  <ExternalLink className="w-3 h-3 mr-1" />
                  Браузер
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VideoViewer;