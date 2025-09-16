import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { XCircle, ArrowLeft, CreditCard } from 'lucide-react';

const PaymentCancelled = () => {
  const navigate = useNavigate();

  const handleGoBack = () => {
    navigate('/');
  };

  const handleTryAgain = () => {
    navigate('/', { state: { openPaymentModal: true } });
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="max-w-md w-full">
        <CardHeader className="text-center">
          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
            <XCircle className="w-8 h-8 text-muted-foreground" />
          </div>
          <CardTitle className="text-2xl">Платёж отменён</CardTitle>
          <CardDescription>
            Вы отменили процесс оплаты. Никаких средств не было списано.
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-4">
          <div className="bg-muted/50 rounded-lg p-4">
            <h3 className="font-medium mb-2">Что произошло?</h3>
            <p className="text-sm text-muted-foreground">
              Платёж был отменён до завершения. Возможно, вы передумали или 
              произошла техническая ошибка в процессе оплаты.
            </p>
          </div>

          <div className="space-y-2">
            <Button onClick={handleTryAgain} className="w-full numerology-gradient">
              <CreditCard className="w-4 h-4 mr-2" />
              Попробовать снова
            </Button>
            
            <Button onClick={handleGoBack} variant="outline" className="w-full">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Вернуться на главную
            </Button>
          </div>

          <div className="text-center pt-4 border-t">
            <p className="text-xs text-muted-foreground">
              Нужна помощь? Свяжитесь с нашей поддержкой
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PaymentCancelled;