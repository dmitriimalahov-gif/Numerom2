import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { 
  X, 
  ExternalLink, 
  AlertCircle, 
  Loader2, 
  Download, 
  Volume2, 
  Play, 
  Pause,
  Settings,
  Subtitles,
  CreditCard,
  FileText,
  Clock,
  Info
} from 'lucide-react';

const EnhancedVideoViewer = ({ 
  videoUrl, 
  title, 
  description, 
  cost_credits = 0, 
  onClose, 
  consultation = null,
  backendUrl = null
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [showSubtitles, setShowSubtitles] = useState(false);
  
  const videoRef = useRef(null);
  const [isMobile, setIsMobile] = useState(false);

  // Определяем тип видео
  const isYouTube = videoUrl && (videoUrl.includes('youtube.com') || videoUrl.includes('youtu.be') || videoUrl.includes('embed'));
  const isVimeo = videoUrl && videoUrl.includes('vimeo.com');

  useEffect(() => {
    const checkMobile = () => {
      return /android|avantgo|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino/i.test(navigator.userAgent);
    };
    
    setIsMobile(checkMobile());
    
    // Отладочная информация
    console.log('EnhancedVideoViewer props:', {
      videoUrl,
      title,
      description,
      cost_credits,
      consultation: consultation?.id,
      backendUrl,
      isYouTube,
      isVimeo
    });
  }, [videoUrl]);

  const handleVideoLoad = () => {
    setLoading(false);
    setError(false);
    if (videoRef.current) {
      setDuration(videoRef.current.duration || 0);
    }
  };

  const handleVideoError = (e) => {
    console.error('Video loading error for URL:', videoUrl);
    console.error('Video error details:', e);
    if (videoRef.current && videoRef.current.error) {
      console.error('Video element error code:', videoRef.current.error.code);
      console.error('Video element error message:', videoRef.current.error.message);
    }
    setLoading(false);
    setError(true);
  };

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleSeek = (e) => {
    if (videoRef.current && duration > 0) {
      const clickX = e.nativeEvent.offsetX;
      const width = e.currentTarget.offsetWidth;
      const newTime = (clickX / width) * duration;
      videoRef.current.currentTime = newTime;
      setCurrentTime(newTime);
    }
  };

  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    if (videoRef.current) {
      videoRef.current.volume = newVolume;
    }
  };

  const handlePlaybackRateChange = (rate) => {
    setPlaybackRate(rate);
    if (videoRef.current) {
      videoRef.current.playbackRate = rate;
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-1 sm:p-2">
      <Card className={`w-full ${isMobile ? 'max-w-full max-h-full' : 'max-w-6xl max-h-[95vh]'} overflow-hidden bg-gray-900 border-gray-700 ${isMobile ? 'rounded-none' : ''}`}>
        {/* Header с информацией */}
        <CardHeader className="bg-gray-800 border-b border-gray-700 pb-3">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <CardTitle className="text-white text-lg flex items-center mb-2">
                <Play className="w-5 h-5 mr-2 text-blue-400" />
                {title || 'Видео консультация'}
                {cost_credits > 0 && (
                  <Badge variant="secondary" className="ml-3 bg-green-600 text-white">
                    <CreditCard className="w-3 h-3 mr-1" />
                    {cost_credits} баллов
                  </Badge>
                )}
              </CardTitle>
              
              {description && (
                <div className="flex items-start mb-2">
                  <Info className="w-4 h-4 mr-2 text-gray-400 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-gray-300">
                    {description}
                  </p>
                </div>
              )}

              {consultation && (
                <div className="flex items-center gap-4 text-xs text-gray-400">
                  <span className="flex items-center">
                    <Clock className="w-3 h-3 mr-1" />
                    {new Date(consultation.created_at).toLocaleDateString('ru-RU')}
                  </span>
                  {consultation.pdf_file_id && (
                    <span className="flex items-center">
                      <FileText className="w-3 h-3 mr-1" />
                      PDF материалы доступны
                    </span>
                  )}
                </div>
              )}
            </div>
            
            <div className="flex items-center gap-1 sm:gap-2 ml-2 sm:ml-4">
              {!isMobile && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const link = document.createElement('a');
                      link.href = videoUrl;
                      link.download = title || 'consultation-video';
                      link.click();
                    }}
                    className="text-white border-gray-600 hover:bg-gray-700 text-xs"
                  >
                    <Download className="w-3 h-3 mr-1" />
                    Скачать
                  </Button>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open(videoUrl, '_blank')}
                    className="text-white border-gray-600 hover:bg-gray-700 text-xs"
                  >
                    <ExternalLink className="w-3 h-3 mr-1" />
                    Открыть отдельно
                  </Button>
                </>
              )}
              
              <Button
                variant="outline"
                size="sm"
                onClick={onClose}
                className="text-white border-gray-600 hover:bg-gray-700"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        
        {/* Video Content */}
        <CardContent className="p-0 relative bg-black" style={{ height: isMobile ? 'calc(100vh - 120px)' : '70vh' }}>
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black z-10">
              <div className="text-center text-white">
                <Loader2 className="w-8 h-8 mx-auto mb-4 animate-spin" />
                <p className="text-lg">Загрузка видео...</p>
                <p className="text-sm text-gray-400 mt-1">{title}</p>
              </div>
            </div>
          )}

          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-black">
              <div className="text-center text-white p-8">
                <AlertCircle className="w-16 h-16 mx-auto mb-4 text-red-500" />
                <h3 className="text-xl mb-4">Ошибка загрузки видео</h3>
                <p className="text-gray-300 mb-6">
                  URL: {videoUrl}
                </p>
                <div className="flex gap-4 justify-center">
                  <Button
                    onClick={() => window.open(videoUrl, '_blank')}
                    variant="outline"
                    className="text-white border-white hover:bg-white hover:text-black"
                  >
                    <ExternalLink className="w-4 h-4 mr-2" />
                    Открыть в новой вкладке
                  </Button>
                  <Button
                    onClick={() => {
                      setError(false);
                      setLoading(true);
                    }}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    Повторить
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Video или iframe */}
          {!error && (
            <>
              {isYouTube || isVimeo ? (
                <iframe
                  src={videoUrl}
                  className="w-full h-full"
                  allowFullScreen
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  title={title}
                  onLoad={handleVideoLoad}
                />
              ) : (
                <video
                  ref={videoRef}
                  src={videoUrl}
                  className="w-full h-full object-contain"
                  onLoadStart={() => setLoading(true)}
                  onCanPlay={handleVideoLoad}
                  onLoadedData={handleVideoLoad}
                  onTimeUpdate={handleTimeUpdate}
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                  onError={handleVideoError}
                  controls={isMobile}
                  playsInline
                >
                  {consultation?.subtitles_file_id && showSubtitles && (
                    <track
                      kind="subtitles"
                      src={`${backendUrl}/api/consultations/subtitles/${consultation.subtitles_file_id}`}
                      srcLang="ru"
                      label="Русские субтитры"
                      default
                    />
                  )}
                  <p className="text-center p-4 text-white">
                    Ваш браузер не поддерживает воспроизведение видео.
                  </p>
                </video>
              )}

              {/* Пользовательские элементы управления для desktop */}
              {!isMobile && !isYouTube && !isVimeo && (
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-black/80 to-transparent p-4">
                  {/* Progress Bar */}
                  <div className="mb-3">
                    <div 
                      className="w-full h-2 bg-gray-600 rounded cursor-pointer"
                      onClick={handleSeek}
                    >
                      <div 
                        className="h-full bg-blue-500 rounded"
                        style={{ width: duration > 0 ? `${(currentTime / duration) * 100}%` : '0%' }}
                      />
                    </div>
                  </div>
                  
                  {/* Controls */}
                  <div className="flex items-center gap-3 text-white">
                    <Button
                      onClick={togglePlay}
                      size="sm"
                      variant="ghost"
                      className="text-white hover:bg-white/20"
                    >
                      {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </Button>
                    
                    <span className="text-sm min-w-[80px]">
                      {formatTime(currentTime)} / {formatTime(duration)}
                    </span>
                    
                    <div className="flex items-center gap-2 ml-auto">
                      {consultation?.subtitles_file_id && (
                        <Button
                          onClick={() => setShowSubtitles(!showSubtitles)}
                          size="sm"
                          variant="ghost"
                          className={`text-white hover:bg-white/20 ${showSubtitles ? 'bg-white/20' : ''}`}
                          title="Субтитры"
                        >
                          <Subtitles className="w-4 h-4" />
                        </Button>
                      )}
                      
                      <select
                        value={playbackRate}
                        onChange={(e) => handlePlaybackRateChange(parseFloat(e.target.value))}
                        className="bg-black/50 text-white text-sm rounded px-2 py-1 border border-gray-600"
                        title="Скорость"
                      >
                        <option value={1}>1x</option>
                        <option value={1.5}>1.5x</option>
                        <option value={2}>2x</option>
                      </select>
                      
                      <div className="flex items-center gap-1">
                        <Volume2 className="w-4 h-4" />
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.1"
                          value={volume}
                          onChange={handleVolumeChange}
                          className="w-20"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default EnhancedVideoViewer;