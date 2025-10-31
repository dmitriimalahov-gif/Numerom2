import React, { useState, useEffect } from 'react';
import { Alert, AlertDescription } from './ui/alert';
import { Card, CardContent } from './ui/card';
import { Loader, Play, AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './ui/button';

/**
 * BUNNY VIDEO PLAYER
 * Безопасный плеер для видео с Bunny.net Stream
 *
 * Особенности:
 * - Генерирует защищенный signed URL для каждого просмотра
 * - URL работает только 2 часа и привязан к IP пользователя
 * - Невозможно поделиться ссылкой
 * - Автоматическая проверка статуса обработки видео
 *
 * Props:
 * - lessonId: ID урока
 * - backendUrl: URL бэкенда (опционально)
 * - autoplay: Автоматический запуск (по умолчанию false)
 * - onError: Callback при ошибке
 * - onLoad: Callback при успешной загрузке
 */
const BunnyVideoPlayer = ({
  lessonId,
  backendUrl,
  autoplay = false,
  onError,
  onLoad
}) => {
  const [videoUrl, setVideoUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState(null);
  const [thumbnail, setThumbnail] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  const apiUrl = backendUrl || process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

  useEffect(() => {
    loadVideoUrl();
  }, [lessonId]);

  const loadVideoUrl = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Требуется авторизация для просмотра видео');
      }

      const response = await fetch(
        `${apiUrl}/api/lessons/${lessonId}/video-url`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Требуется авторизация');
        } else if (response.status === 403) {
          throw new Error('У вас нет доступа к этому уроку');
        } else if (response.status === 404) {
          throw new Error('Видео не найдено для этого урока');
        }
        throw new Error('Ошибка загрузки видео');
      }

      const data = await response.json();

      if (data.status === 'processing') {
        setStatus('processing');
        setThumbnail(data.thumbnail);
        setError('Видео еще обрабатывается на сервере. Это может занять несколько минут.');
      } else if (data.success && data.video_url) {
        setVideoUrl(data.video_url);
        setThumbnail(data.thumbnail);
        setStatus('ready');
        if (onLoad) {
          onLoad(data);
        }
      } else {
        throw new Error(data.message || 'Не удалось получить URL видео');
      }
    } catch (err) {
      console.error('Error loading video:', err);
      const errorMessage = err.message || 'Ошибка загрузки видео';
      setError(errorMessage);
      if (onError) {
        onError(err);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    setRetryCount(prev => prev + 1);
    loadVideoUrl();
  };

  // Состояние загрузки
  if (loading) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center h-96 bg-gradient-to-br from-gray-50 to-gray-100">
          <Loader className="w-12 h-12 animate-spin text-blue-600 mb-4" />
          <p className="text-gray-600">Загрузка видео...</p>
          <p className="text-sm text-gray-400 mt-2">Генерация защищенной ссылки</p>
        </CardContent>
      </Card>
    );
  }

  // Состояние обработки видео
  if (status === 'processing') {
    return (
      <Card className="border-yellow-200 bg-yellow-50">
        <CardContent className="py-8">
          <div className="flex flex-col items-center text-center">
            <AlertCircle className="w-16 h-16 text-yellow-600 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Видео обрабатывается
            </h3>
            <p className="text-gray-600 mb-4 max-w-md">
              Видео загружено на сервер и сейчас конвертируется для оптимального просмотра.
              Это обычно занимает 2-5 минут.
            </p>
            {thumbnail && (
              <img
                src={thumbnail}
                alt="Превью видео"
                className="w-full max-w-md rounded-lg mb-4"
                onError={(e) => e.target.style.display = 'none'}
              />
            )}
            <Button
              onClick={handleRetry}
              variant="outline"
              className="mt-4"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Проверить снова
            </Button>
            <p className="text-xs text-gray-500 mt-2">
              Попытка {retryCount + 1}
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Состояние ошибки
  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="py-8">
          <Alert variant="destructive" className="bg-transparent border-none">
            <AlertDescription className="text-center">
              <div className="flex flex-col items-center">
                <AlertCircle className="w-12 h-12 text-red-600 mb-3" />
                <p className="text-red-800 font-medium mb-2">Ошибка загрузки видео</p>
                <p className="text-red-700 text-sm mb-4">{error}</p>
                {status === 'processing' && (
                  <Button
                    onClick={handleRetry}
                    variant="outline"
                    className="border-red-300 text-red-700 hover:bg-red-100"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Попробовать снова
                  </Button>
                )}
              </div>
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  // Нет видео
  if (!videoUrl) {
    return (
      <Card className="border-gray-200 bg-gray-50">
        <CardContent className="py-8">
          <div className="flex flex-col items-center text-center">
            <Play className="w-16 h-16 text-gray-400 mb-4" />
            <p className="text-gray-600">Видео не загружено для этого урока</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Успешная загрузка - показываем iframe с видео
  return (
    <div className="relative w-full rounded-lg overflow-hidden shadow-lg bg-black">
      {/* Aspect ratio 16:9 */}
      <div className="relative" style={{ paddingBottom: '56.25%' }}>
        <iframe
          src={`${videoUrl}${autoplay ? '&autoplay=true' : ''}`}
          className="absolute top-0 left-0 w-full h-full"
          frameBorder="0"
          allow="accelerometer; gyroscope; autoplay; encrypted-media; picture-in-picture; fullscreen"
          allowFullScreen
          style={{
            border: 'none',
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%'
          }}
          title={`Видео урока ${lessonId}`}
        />
      </div>

      {/* Информация о защите */}
      <div className="bg-gray-900 text-gray-400 text-xs px-4 py-2 flex items-center justify-between">
        <span className="flex items-center">
          <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
          Защищенное соединение
        </span>
        <span>Ссылка действительна 2 часа</span>
      </div>
    </div>
  );
};

export default BunnyVideoPlayer;
