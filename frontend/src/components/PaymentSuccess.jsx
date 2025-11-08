import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { CheckCircle, Loader, Crown, ArrowRight } from 'lucide-react';
import { useAuth } from './AuthContext';
import axios from 'axios';
import { getBackendUrl } from '../utils/backendUrl';

const PaymentSuccess = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { refreshProfile } = useAuth();
  const [status, setStatus] = useState('checking'); // checking, success, error
  const [paymentDetails, setPaymentDetails] = useState(null);

  const sessionId = searchParams.get('session_id');
  const backendUrl = getBackendUrl();

  useEffect(() => {
    if (sessionId) {
      checkPaymentStatus();
    } else {
      setStatus('error');
    }
  }, [sessionId]);

  const checkPaymentStatus = async () => {
    let attempts = 0;
    const maxAttempts = 5;
    const pollInterval = 2000; // 2 seconds

    const pollStatus = async () => {
      if (attempts >= maxAttempts) {
        setStatus('error');
        return;
      }

      try {
        const response = await axios.get(`${backendUrl}/api/payments/checkout/status/${sessionId}`);
        const data = response.data;

        if (data.payment_status === 'paid') {
          setPaymentDetails(data);
          setStatus('success');
          // Refresh user profile to get updated subscription/credits
          await refreshProfile();
          return;
        } else if (data.status === 'expired') {
          setStatus('error');
          return;
        }

        // Continue polling if payment is still pending
        attempts++;
        setTimeout(pollStatus, pollInterval);
      } catch (error) {
        console.error('Error checking payment status:', error);
        attempts++;
        if (attempts >= maxAttempts) {
          setStatus('error');
        } else {
          setTimeout(pollStatus, pollInterval);
        }
      }
    };

    pollStatus();
  };

  const handleContinue = () => {
    navigate('/');
  };

  if (status === 'checking') {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="p-8 text-center">
            <Loader className="w-12 h-12 animate-spin text-primary mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Обрабатываем ваш платёж</h2>
            <p className="text-muted-foreground">
              Пожалуйста, подождите, мы проверяем статус вашего платежа...
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="p-8 text-center">
            <div className="w-12 h-12 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-4">
              <span className="text-destructive text-xl">✕</span>
            </div>
            <h2 className="text-xl font-semibold mb-2">Ошибка платежа</h2>
            <p className="text-muted-foreground mb-6">
              Произошла ошибка при обработке вашего платежа. Если средства были списаны, 
              они будут возвращены в течение 5-7 рабочих дней.
            </p>
            <Button onClick={handleContinue} variant="outline" className="w-full">
              Вернуться на главную
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="max-w-md w-full">
        <CardHeader className="text-center">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-primary" />
          </div>
          <CardTitle className="text-2xl text-primary">Платёж успешен!</CardTitle>
          <CardDescription>
            Добро пожаловать в мир углублённого самопознания
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {paymentDetails && (
            <div className="bg-muted rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-muted-foreground">Сумма:</span>
                <span className="font-medium">
                  {paymentDetails.amount_total / 100} {paymentDetails.currency.toUpperCase()}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Статус:</span>
                <span className="text-primary font-medium">Оплачено</span>
              </div>
            </div>
          )}

          <div className="space-y-3">
            <div className="flex items-center space-x-3 p-3 bg-primary/5 rounded-lg">
              <Crown className="w-5 h-5 text-primary" />
              <span className="text-sm">Premium функции активированы</span>
            </div>
            
            <div className="flex items-center space-x-3 p-3 bg-primary/5 rounded-lg">
              <CheckCircle className="w-5 h-5 text-primary" />
              <span className="text-sm">Безлимитные расчёты доступны</span>
            </div>
            
            <div className="flex items-center space-x-3 p-3 bg-primary/5 rounded-lg">
              <CheckCircle className="w-5 h-5 text-primary" />
              <span className="text-sm">Персональные рекомендации включены</span>
            </div>
          </div>

          <Button onClick={handleContinue} className="w-full numerology-gradient">
            Продолжить изучение
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>

          <p className="text-xs text-muted-foreground text-center">
            Вы получите email-подтверждение вашей покупки в ближайшее время.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default PaymentSuccess;