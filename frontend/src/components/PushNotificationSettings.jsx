import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import { Bell, BellOff, Check, Clock, Smartphone, X } from 'lucide-react';
import axios from 'axios';
import { useAuth } from './AuthContext';
import * as serviceWorkerRegistration from '../serviceWorkerRegistration';

const PushNotificationSettings = ({ lessonId, onSubscribed }) => {
  const { user } = useAuth();
  const [notificationState, setNotificationState] = useState('checking'); // checking, unsupported, denied, default, granted
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [notificationTime, setNotificationTime] = useState('10:00');

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    checkNotificationSupport();
    checkExistingSubscription();
  }, []);

  const checkNotificationSupport = () => {
    if (!serviceWorkerRegistration.isPushNotificationSupported()) {
      setNotificationState('unsupported');
      return false;
    }

    const permission = serviceWorkerRegistration.getNotificationPermission();
    setNotificationState(permission);
    return true;
  };

  const checkExistingSubscription = async () => {
    try {
      const currentSubscription = await serviceWorkerRegistration.getCurrentPushSubscription();
      if (currentSubscription) {
        setSubscription(currentSubscription);
      }
    } catch (error) {
      console.error('Error checking subscription:', error);
    }
  };

  const handleSubscribe = async () => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // Получаем VAPID публичный ключ с бэкенда
      const vapidResponse = await axios.get(`${backendUrl}/api/push/vapid-public-key`);
      const vapidPublicKey = vapidResponse.data.publicKey;

      if (!vapidPublicKey) {
        throw new Error('VAPID ключ не настроен на сервере. Запустите generate_vapid_keys.py');
      }

      // Подписываемся на push уведомления
      const pushSubscription = await serviceWorkerRegistration.subscribeToPushNotifications(vapidPublicKey);

      // Отправляем подписку на бэкенд
      await axios.post(
        `${backendUrl}/api/push/subscribe`,
        {
          ...pushSubscription.toJSON(),
          notificationTime,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          lessonId: lessonId || null
        },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      setSubscription(pushSubscription);
      setNotificationState('granted');
      setSuccess('Уведомления успешно включены! 🎉');

      if (onSubscribed) {
        onSubscribed();
      }

      // Отправляем тестовое уведомление
      await axios.post(
        `${backendUrl}/api/push/send-test`,
        {},
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

    } catch (err) {
      console.error('Error subscribing to push notifications:', err);
      if (err.message && err.message.includes('Permission not granted')) {
        setError('Вы отклонили разрешение на уведомления. Разрешите в настройках браузера.');
        setNotificationState('denied');
      } else if (err.message && err.message.includes('VAPID')) {
        setError('Сервер не настроен. Обратитесь к администратору.');
      } else {
        setError('Ошибка при подписке на уведомления: ' + (err.response?.data?.detail || err.message));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUnsubscribe = async () => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const success = await serviceWorkerRegistration.unsubscribeFromPushNotifications();

      if (success && subscription) {
        // Удаляем подписку с бэкенда
        await axios.delete(
          `${backendUrl}/api/push/unsubscribe?endpoint=${encodeURIComponent(subscription.endpoint)}`,
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('token')}`
            }
          }
        );
      }

      setSubscription(null);
      setSuccess('Уведомления отключены');
    } catch (err) {
      console.error('Error unsubscribing:', err);
      setError('Ошибка при отписке: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateTime = async () => {
    if (!subscription) return;

    setLoading(true);
    setError('');

    try {
      await axios.post(
        `${backendUrl}/api/push/update-settings`,
        {
          endpoint: subscription.endpoint,
          notificationTime
        },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      setSuccess('Время уведомлений обновлено');
    } catch (err) {
      console.error('Error updating time:', err);
      setError('Ошибка при обновлении: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  if (notificationState === 'unsupported') {
    return (
      <Alert>
        <AlertDescription>
          Ваш браузер не поддерживает push-уведомления. Попробуйте Chrome, Firefox или Safari.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle className="flex items-center text-lg">
          <Bell className="w-5 h-5 mr-2 text-purple-600" />
          Напоминания о челлендже
        </CardTitle>
        <CardDescription>
          Получайте ежедневные push-уведомления на телефон или компьютер
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <X className="w-4 h-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert className="bg-green-50 border-green-200">
            <Check className="w-4 h-4 text-green-600" />
            <AlertDescription className="text-green-800">{success}</AlertDescription>
          </Alert>
        )}

        {!subscription ? (
          <div className="space-y-4">
            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
              <div className="flex items-start space-x-3">
                <Smartphone className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <h4 className="font-medium text-purple-900 mb-1">Как это работает?</h4>
                  <ul className="text-sm text-purple-800 space-y-1">
                    <li>• Уведомления приходят каждый день в выбранное время</li>
                    <li>• Работают даже когда сайт закрыт</li>
                    <li>• Можно отключить в любой момент</li>
                    <li>• Работает на телефоне и компьютере</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center">
                <Clock className="w-4 h-4 mr-2" />
                Время напоминаний
              </label>
              <input
                type="time"
                value={notificationTime}
                onChange={(e) => setNotificationTime(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <Button
              onClick={handleSubscribe}
              disabled={loading || notificationState === 'denied'}
              className="w-full numerology-gradient hover:brightness-90 text-white"
            >
              {loading ? (
                'Подключение...'
              ) : notificationState === 'denied' ? (
                <>
                  <BellOff className="w-4 h-4 mr-2" />
                  Уведомления заблокированы
                </>
              ) : (
                <>
                  <Bell className="w-4 h-4 mr-2" />
                  Включить напоминания
                </>
              )}
            </Button>

            {notificationState === 'denied' && (
              <p className="text-xs text-muted-foreground text-center">
                Разрешите уведомления в настройках браузера, затем обновите страницу
              </p>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center space-x-2 text-green-800">
                <Check className="w-5 h-5" />
                <span className="font-medium">Уведомления включены</span>
              </div>
              <p className="text-sm text-green-700 mt-1">
                Вы будете получать напоминания каждый день
              </p>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center">
                <Clock className="w-4 h-4 mr-2" />
                Время напоминаний
              </label>
              <div className="flex space-x-2">
                <input
                  type="time"
                  value={notificationTime}
                  onChange={(e) => setNotificationTime(e.target.value)}
                  className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <Button
                  onClick={handleUpdateTime}
                  disabled={loading}
                  variant="outline"
                  size="sm"
                >
                  Обновить
                </Button>
              </div>
            </div>

            <Button
              onClick={handleUnsubscribe}
              disabled={loading}
              variant="outline"
              className="w-full border-red-300 text-red-700 hover:bg-red-50"
            >
              <BellOff className="w-4 h-4 mr-2" />
              Отключить уведомления
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default PushNotificationSettings;
