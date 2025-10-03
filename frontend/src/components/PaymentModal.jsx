import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { useAuth } from './AuthContext';

const PaymentModal = ({ isOpen, onClose }) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

  const startCheckout = async (packageType) => {
    setLoading(true);
    try {
      const res = await fetch(`${backendUrl}/api/payments/checkout/session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          package_type: packageType,
          origin_url: window.location.origin
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Ошибка оплаты');
      window.location.href = data.url;
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const plans = [
    { 
      id: 'one_time', 
      title: 'Стартовый пакет', 
      price: '0.99 €', 
      description: '10 баллов + месяц доступа' 
    },
    { 
      id: 'monthly', 
      title: 'Базовая подписка', 
      price: '9.99 €', 
      description: '150 баллов + месяц доступа' 
    },
    { 
      id: 'annual', 
      title: 'Годовая подписка', 
      price: '66.6 €', 
      description: '1000 баллов + год доступа' 
    },
    { 
      id: 'master_consultation', 
      title: 'Мастер консультация', 
      price: '666 €', 
      description: '10000 баллов + персональная консультация от мастера',
      special: true
    }
  ];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Выберите план</DialogTitle>
        </DialogHeader>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          {plans.map(p => (
            <div 
              key={p.id} 
              className={`border rounded-lg p-4 ${
                p.special 
                  ? 'border-2 border-yellow-400 bg-gradient-to-br from-yellow-50 to-amber-50 relative' 
                  : 'border-gray-200'
              }`}
            >
              {p.special && (
                <div className="absolute -top-2 -right-2 bg-yellow-400 text-black text-xs font-bold px-2 py-1 rounded-full">
                  ⭐ VIP
                </div>
              )}
              <div className={`text-lg font-medium mb-1 ${p.special ? 'text-amber-800' : ''}`}>
                {p.title}
              </div>
              <div className={`text-2xl font-bold mb-2 ${p.special ? 'text-amber-900' : ''}`}>
                {p.price}
              </div>
              <div className={`text-sm mb-4 ${p.special ? 'text-amber-700' : 'text-muted-foreground'}`}>
                {p.description}
              </div>
              <Button 
                onClick={() => startCheckout(p.id)} 
                disabled={loading} 
                className={`w-full ${
                  p.special 
                    ? 'bg-gradient-to-r from-yellow-400 to-amber-500 hover:from-yellow-500 hover:to-amber-600 text-black font-bold shadow-lg' 
                    : ''
                }`}
              >
                {loading ? 'Подождите…' : p.special ? 'Заказать VIP' : 'Оплатить'}
              </Button>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default PaymentModal;
