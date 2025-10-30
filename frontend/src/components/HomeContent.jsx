import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { useAuth } from './AuthContext';
import PaymentModal from './PaymentModal';
import {
  User, Calendar, CreditCard, Calculator, Clock, Heart, BookOpen, TrendingUp
} from 'lucide-react';

const HomeContent = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [paymentOpen, setPaymentOpen] = useState(false);

  const handleSectionChange = (section) => {
    navigate(`/dashboard/${section}`);
  };

  return (
    <>
      <div className="space-y-6">
        {/* Приветствие и основная информация */}
        <Card className="numerology-gradient">
          <CardHeader className="text-white">
            <CardTitle className="text-2xl">Добро пожаловать в NUMEROM</CardTitle>
            <CardDescription className="text-white/90">
              Ваш персональный центр нумерологии и самопознания
            </CardDescription>
          </CardHeader>
        </Card>

        {/* Личные данные */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <User className="w-5 h-5 mr-2" />
              Ваши личные данные
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <User className="w-4 h-4 text-blue-600" />
                  <div>
                    <p className="text-xs text-muted-foreground">Имя</p>
                    <p className="font-medium">{user?.full_name || user?.name || 'Не указано'}</p>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-green-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Calendar className="w-4 h-4 text-green-600" />
                  <div>
                    <p className="text-xs text-muted-foreground">Дата рождения</p>
                    <p className="font-medium">{user?.birth_date || 'Не указана'}</p>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-orange-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <CreditCard className="w-4 h-4 text-orange-600" />
                  <div>
                    <p className="text-xs text-muted-foreground">Кредиты</p>
                    <p className="font-medium text-xl">{user?.credits_remaining || 0}</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Email: {user?.email}</p>
                  <p className="text-xs text-muted-foreground">
                    Статус: {user?.is_premium ? 'Premium подписка' : 'Базовый аккаунт'}
                    {user?.subscription_expires_at && (
                      <span className="ml-2">
                        до {new Date(user.subscription_expires_at).toLocaleDateString()}
                      </span>
                    )}
                  </p>
                </div>
                {!user?.is_premium && (
                  <Button
                    onClick={() => setPaymentOpen(true)}
                    className="bg-gradient-to-r from-purple-500 to-pink-500 text-white"
                  >
                    Получить Premium
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Пакеты кредитов */}
        {/* <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <CreditCard className="w-5 h-5 mr-2" />
              Пополнить кредиты
            </CardTitle>
            <CardDescription>
              Выберите подходящий пакет и экономьте при покупке больших пакетов
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              <div className="relative p-4 sm:p-6 border-2 rounded-lg hover:shadow-md transition-shadow w-full flex flex-col">
                <div className="text-center flex-1 flex flex-col">
                  <h3 className="text-base sm:text-lg font-bold mb-2">Стартовый</h3>
                  <div className="text-2xl sm:text-3xl font-bold text-blue-600 mb-2">10 кредитов</div>
                  <div className="text-xl sm:text-2xl font-bold mb-2">0.99€</div>
                  <div className="line-through text-gray-500 text-sm invisible">-</div>
                  <div className="text-sm text-gray-600 mb-3 sm:mb-4 flex-1">
                    <div>0.099€ за кредит</div>
                    <div className="text-xs">+ месяц доступа</div>
                  </div>
                  <Button
                    onClick={() => setPaymentOpen(true)}
                    className="w-full text-sm sm:text-base py-2 sm:py-3 mt-auto"
                    variant="outline"
                  >
                    Купить
                  </Button>
                </div>
              </div>

              <div className="relative p-4 sm:p-6 border-2 border-green-500 rounded-lg hover:shadow-md transition-shadow bg-green-50 w-full flex flex-col">
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <span className="bg-green-500 text-white px-3 sm:px-4 py-1 rounded-full text-xs sm:text-sm font-medium whitespace-nowrap">
                    Популярный
                  </span>
                </div>
                <div className="text-center flex-1 flex flex-col">
                  <h3 className="text-base sm:text-lg font-bold mb-2">Базовый</h3>
                  <div className="text-2xl sm:text-3xl font-bold text-green-600 mb-2">150 кредитов</div>
                  <div className="text-xl sm:text-2xl font-bold mb-2">9.99€</div>
                  <div className="line-through text-gray-500 text-sm">14.85€</div>
                  <div className="text-sm text-green-600 mb-3 sm:mb-4 flex-1">
                    <div>0.067€ за кредит</div>
                    <div className="text-xs font-medium">+ месяц доступа</div>
                  </div>
                  <Button
                    onClick={() => setPaymentOpen(true)}
                    className="w-full bg-green-600 hover:bg-green-700 text-sm sm:text-base py-2 sm:py-3 mt-auto"
                  >
                    Купить со скидкой
                  </Button>
                </div>
              </div>

              <div className="relative p-4 sm:p-6 border-2 border-purple-500 rounded-lg hover:shadow-md transition-shadow bg-purple-50 w-full flex flex-col">
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <span className="bg-purple-500 text-white px-2 sm:px-4 py-1 rounded-full text-xs sm:text-sm font-medium whitespace-nowrap">
                    Максимум выгоды
                  </span>
                </div>
                <div className="text-center flex-1 flex flex-col">
                  <h3 className="text-base sm:text-lg font-bold mb-2">Профессиональный</h3>
                  <div className="text-2xl sm:text-3xl font-bold text-purple-600 mb-2">1000 кредитов</div>
                  <div className="text-xl sm:text-2xl font-bold mb-2">66.6€</div>
                  <div className="line-through text-gray-500 text-sm">199.8€</div>
                  <div className="text-sm text-purple-600 mb-3 sm:mb-4 flex-1">
                    <div>0.067€ за кредит</div>
                    <div className="text-xs font-medium">+ год доступа</div>
                  </div>
                  <Button
                    onClick={() => setPaymentOpen(true)}
                    className="w-full bg-purple-600 hover:bg-purple-700 text-sm sm:text-base py-2 sm:py-3 mt-auto"
                  >
                    Максимальная выгода
                  </Button>
                </div>
              </div>
            </div>

            <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-start space-x-2">
                <TrendingUp className="w-5 h-5 text-yellow-600 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-yellow-800">Экономьте больше с крупными пакетами!</p>
                  <p className="text-yellow-700">
                    При покупке пакета "Оптимальный" вы экономите <strong>1.98€</strong>,
                    а с пакетом "Профессиональный" - целых <strong>3.95€</strong>!
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card> */}

        {/* Быстрые действия - улучшенные для мобильных */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          <Card className="p-3 sm:p-4 text-center hover:shadow-md transition-all cursor-pointer active:scale-95"
                onClick={() => handleSectionChange('numerology')}>
            <Calculator className="w-6 h-6 sm:w-8 sm:h-8 text-blue-600 mx-auto mb-2" />
            <h3 className="font-medium text-sm sm:text-base">Нумерология</h3>
            <p className="text-xs text-muted-foreground hidden sm:block">Расчеты чисел</p>
          </Card>

          <Card className="p-3 sm:p-4 text-center hover:shadow-md transition-all cursor-pointer active:scale-95"
                onClick={() => handleSectionChange('vedic-time')}>
            <Clock className="w-6 h-6 sm:w-8 sm:h-8 text-green-600 mx-auto mb-2" />
            <h3 className="font-medium text-sm sm:text-base">Ведические времена</h3>
            <p className="text-xs text-muted-foreground hidden sm:block">Планетарные часы</p>
          </Card>

          <Card className="p-3 sm:p-4 text-center hover:shadow-md transition-all cursor-pointer active:scale-95"
                onClick={() => handleSectionChange('compatibility')}>
            <Heart className="w-6 h-6 sm:w-8 sm:h-8 text-pink-600 mx-auto mb-2" />
            <h3 className="font-medium text-sm sm:text-base">Совместимость</h3>
            <p className="text-xs text-muted-foreground hidden sm:block">Анализ отношений</p>
          </Card>

          <Card className="p-3 sm:p-4 text-center hover:shadow-md transition-all cursor-pointer active:scale-95"
                onClick={() => handleSectionChange('learning')}>
            <BookOpen className="w-6 h-6 sm:w-8 sm:h-8 text-purple-600 mx-auto mb-2" />
            <h3 className="font-medium text-sm sm:text-base">Обучение</h3>
            <p className="text-xs text-muted-foreground hidden sm:block">Материалы и уроки</p>
          </Card>
        </div>
      </div>

      <PaymentModal isOpen={paymentOpen} onClose={() => setPaymentOpen(false)} />
    </>
  );
};

export default HomeContent;
