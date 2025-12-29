import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Label } from './ui/label';
import { Alert, AlertDescription } from './ui/alert';
import { useAuth } from './AuthContext';
import { User, Phone, MapPin, Car, Home, Edit3, Calendar, Mail, CheckCircle2, Sparkles, Save, X } from 'lucide-react';
import { getBackendUrl } from '../utils/backendUrl';
import { useTheme } from '../hooks/useTheme';

const PersonalDataForm = () => {
  const { theme } = useOutletContext();
  const themeConfig = useTheme(theme);
  const { user, updateUser } = useAuth();
  const [formData, setFormData] = useState({
    full_name: '',
    name: '',
    surname: '',
    birth_date: '',
    phone_number: '',
    city: '',
    car_number: '',
    street: '',
    house_number: '',
    apartment_number: '',
    postal_code: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  const backendUrl = getBackendUrl();

  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || '',
        name: user.name || '',
        surname: user.surname || '',
        birth_date: user.birth_date || '',
        phone_number: user.phone_number || '',
        city: user.city || '',
        car_number: user.car_number || '',
        street: user.street || '',
        house_number: user.house_number || '',
        apartment_number: user.apartment_number || '',
        postal_code: user.postal_code || ''
      });
    }
  }, [user]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage('');

    const payload = { ...formData };

    if (typeof payload.birth_date === 'string') {
      const trimmedDate = payload.birth_date.trim();
      if (!trimmedDate) {
        delete payload.birth_date;
      } else {
        const dateRegex = /^\d{2}\.\d{2}\.\d{4}$/;
        if (!dateRegex.test(trimmedDate)) {
          setMessage('Введите дату рождения в формате ДД.ММ.ГГГГ');
          setIsLoading(false);
          return;
        }
        const [day, month, year] = trimmedDate.split('.').map(Number);
        const candidateDate = new Date(year, month - 1, day);
        const isValidDate =
          candidateDate.getFullYear() === year &&
          candidateDate.getMonth() === month - 1 &&
          candidateDate.getDate() === day;

        if (!isValidDate) {
          setMessage('Указанная дата рождения не существует');
          setIsLoading(false);
          return;
        }

        payload.birth_date = trimmedDate;
      }
    }

    Object.keys(payload).forEach((key) => {
      if (typeof payload[key] === 'string') {
        const trimmed = payload[key].trim();
        if (trimmed) {
          payload[key] = trimmed;
        } else {
          delete payload[key];
        }
      }
    });

    if (Object.keys(payload).length === 0) {
      setMessage('Заполните хотя бы одно поле для сохранения изменений');
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch(`${backendUrl}/api/user/profile-v2`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const updatedUser = await response.json();
        updateUser(updatedUser);
        setMessage('Данные успешно обновлены!');
        setIsEditing(false);
      } else {
        const errorData = await response.json();
        setMessage(`Ошибка: ${errorData.detail || 'Неизвестная ошибка'}`);
      }
    } catch (error) {
      setMessage('Ошибка при обновлении данных');
      console.error('Error updating profile:', error);
    }

    setIsLoading(false);
  };

  const InfoCard = ({ icon: Icon, label, value, color }) => (
    <div className={`group p-5 rounded-2xl border transition-all duration-300 hover:-translate-y-1 ${themeConfig.isDark ? 'bg-slate-800/40 border-slate-700/50 hover:bg-slate-800/60 hover:border-slate-600' : 'bg-white/80 border-slate-200 hover:bg-white hover:shadow-lg'}`}>
      <div className="flex items-start gap-4">
        <div className={`p-3 rounded-xl transition-all duration-300 group-hover:scale-110 ${themeConfig.isDark ? 'bg-gradient-to-br from-indigo-500/20 to-purple-500/20' : 'bg-gradient-to-br from-indigo-100 to-purple-100'}`}>
          <Icon className={`w-5 h-5 ${color || (themeConfig.isDark ? 'text-indigo-400' : 'text-indigo-600')}`} />
        </div>
        <div className="flex-1 min-w-0">
          <p className={`text-xs font-medium uppercase tracking-wider mb-1 ${themeConfig.isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            {label}
          </p>
          <p className={`text-base font-semibold truncate ${themeConfig.text}`}>
            {value || (
              <span className={themeConfig.isDark ? 'text-slate-500 italic' : 'text-slate-400 italic'}>
                Не указано
              </span>
            )}
          </p>
        </div>
      </div>
    </div>
  );

  if (!isEditing) {
    return (
      <div className={`min-h-screen ${themeConfig.bg} p-6`}>
        <div className="max-w-7xl mx-auto">
          {/* Заголовок с анимацией */}
          <div className="mb-8 space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <div className={`p-3 rounded-2xl ${themeConfig.isDark ? 'bg-gradient-to-br from-purple-500/20 to-pink-500/20' : 'bg-gradient-to-br from-purple-100 to-pink-100'}`}>
                    <Sparkles className={`w-8 h-8 ${themeConfig.isDark ? 'text-purple-400' : 'text-purple-600'}`} />
                  </div>
                  <div>
                    <h1 className={`text-4xl font-bold ${themeConfig.text}`}>
                      Личные данные
                    </h1>
                    <p className={`text-sm ${themeConfig.mutedText} mt-1`}>
                      Информация для нумерологических расчетов
                    </p>
                  </div>
                </div>
              </div>
              
              <Button 
                onClick={() => setIsEditing(true)}
                className={`${themeConfig.isDark ? 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500' : 'bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600'} text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-0.5`}
                size="lg"
              >
                <Edit3 className="w-5 h-5 mr-2" />
                Редактировать
              </Button>
            </div>
          </div>

          {/* Email пользователя */}
          <div className={`mb-6 p-6 rounded-2xl border ${themeConfig.isDark ? 'bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border-blue-500/20' : 'bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-200'}`}>
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-xl ${themeConfig.isDark ? 'bg-blue-500/20' : 'bg-blue-100'}`}>
                <Mail className={`w-6 h-6 ${themeConfig.isDark ? 'text-blue-400' : 'text-blue-600'}`} />
              </div>
              <div>
                <p className={`text-sm font-medium ${themeConfig.isDark ? 'text-blue-300' : 'text-blue-700'}`}>
                  Email (для входа)
                </p>
                <p className={`text-lg font-semibold ${themeConfig.text}`}>
                  {user?.email}
                </p>
              </div>
            </div>
          </div>

          {/* Основная информация */}
          <div className="space-y-8">
            {/* Персональные данные */}
            <div>
              <h2 className={`text-2xl font-bold ${themeConfig.text} mb-4 flex items-center gap-2`}>
                <User className={`w-6 h-6 ${themeConfig.isDark ? 'text-indigo-400' : 'text-indigo-600'}`} />
                Персональные данные
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <InfoCard icon={User} label="Полное имя" value={user?.full_name} />
                <InfoCard icon={User} label="Имя (латиницей)" value={user?.name} />
                <InfoCard icon={User} label="Фамилия (латиницей)" value={user?.surname} />
                <InfoCard icon={Calendar} label="Дата рождения" value={user?.birth_date} />
                <InfoCard icon={Phone} label="Телефон" value={user?.phone_number} />
                <InfoCard icon={MapPin} label="Город" value={user?.city} />
              </div>
            </div>

            {/* Дополнительная информация */}
            <div>
              <h2 className={`text-2xl font-bold ${themeConfig.text} mb-4 flex items-center gap-2`}>
                <Home className={`w-6 h-6 ${themeConfig.isDark ? 'text-purple-400' : 'text-purple-600'}`} />
                Дополнительная информация
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <InfoCard icon={Car} label="Номер автомобиля" value={user?.car_number} />
                
                {/* Адрес - расширенная карточка */}
                <div className={`group p-5 rounded-2xl border transition-all duration-300 hover:-translate-y-1 md:col-span-1 ${themeConfig.isDark ? 'bg-slate-800/40 border-slate-700/50 hover:bg-slate-800/60 hover:border-slate-600' : 'bg-white/80 border-slate-200 hover:bg-white hover:shadow-lg'}`}>
                  <div className="flex items-start gap-4">
                    <div className={`p-3 rounded-xl transition-all duration-300 group-hover:scale-110 ${themeConfig.isDark ? 'bg-gradient-to-br from-red-500/20 to-pink-500/20' : 'bg-gradient-to-br from-red-100 to-pink-100'}`}>
                      <Home className={`w-5 h-5 ${themeConfig.isDark ? 'text-red-400' : 'text-red-600'}`} />
                    </div>
                    <div className="flex-1">
                      <p className={`text-xs font-medium uppercase tracking-wider mb-2 ${themeConfig.isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                        Адрес
                      </p>
                      {(user?.street || user?.house_number || user?.apartment_number || user?.postal_code) ? (
                        <div className={`space-y-1 text-sm ${themeConfig.text}`}>
                          {user?.street && <p className="font-semibold">ул. {user.street}</p>}
                          <div className="flex gap-2 flex-wrap">
                            {user?.house_number && <span className={`px-2 py-0.5 rounded ${themeConfig.isDark ? 'bg-slate-700' : 'bg-slate-100'}`}>д. {user.house_number}</span>}
                            {user?.apartment_number && <span className={`px-2 py-0.5 rounded ${themeConfig.isDark ? 'bg-slate-700' : 'bg-slate-100'}`}>кв. {user.apartment_number}</span>}
                          </div>
                          {user?.postal_code && <p className={themeConfig.mutedText}>индекс: {user.postal_code}</p>}
                        </div>
                      ) : (
                        <p className={`text-base font-semibold ${themeConfig.isDark ? 'text-slate-500 italic' : 'text-slate-400 italic'}`}>
                          Не указан
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Статистика заполненности */}
          <div className={`mt-8 p-6 rounded-2xl border ${themeConfig.isDark ? 'bg-gradient-to-r from-emerald-500/10 to-teal-500/10 border-emerald-500/20' : 'bg-gradient-to-r from-emerald-50 to-teal-50 border-emerald-200'}`}>
            <div className="flex items-center gap-4">
              <CheckCircle2 className={`w-8 h-8 ${themeConfig.isDark ? 'text-emerald-400' : 'text-emerald-600'}`} />
              <div className="flex-1">
                <p className={`text-sm font-medium ${themeConfig.isDark ? 'text-emerald-300' : 'text-emerald-700'}`}>
                  Заполненность профиля
                </p>
                <div className="mt-2 flex items-center gap-4">
                  <div className="flex-1 h-2 bg-white/30 rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${themeConfig.isDark ? 'bg-emerald-400' : 'bg-emerald-600'} transition-all duration-500`}
                      style={{ width: `${Object.values(user || {}).filter(v => v && v !== '').length / 11 * 100}%` }}
                    />
                  </div>
                  <span className={`text-lg font-bold ${themeConfig.text}`}>
                    {Math.round(Object.values(user || {}).filter(v => v && v !== '').length / 11 * 100)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${themeConfig.bg} p-6`}>
      <div className="max-w-7xl mx-auto">
        {/* Заголовок */}
        <div className="mb-8 space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <div className={`p-3 rounded-2xl ${themeConfig.isDark ? 'bg-gradient-to-br from-indigo-500/20 to-purple-500/20' : 'bg-gradient-to-br from-indigo-100 to-purple-100'}`}>
                  <Edit3 className={`w-8 h-8 ${themeConfig.isDark ? 'text-indigo-400' : 'text-indigo-600'}`} />
                </div>
                <div>
                  <h1 className={`text-4xl font-bold ${themeConfig.text}`}>
                    Редактирование данных
                  </h1>
                  <p className={`text-sm ${themeConfig.mutedText} mt-1`}>
                    Все поля опциональны и используются для расчетов
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Сообщение об успехе/ошибке */}
          {message && (
            <Alert 
              variant={message.includes('успешно') ? 'default' : 'destructive'}
              className={`${message.includes('успешно') 
                ? (themeConfig.isDark ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' : 'bg-emerald-50 border-emerald-200 text-emerald-800')
                : (themeConfig.isDark ? 'bg-red-500/10 border-red-500/30 text-red-300' : 'bg-red-50 border-red-200 text-red-800')
              }`}
            >
              <AlertDescription className="flex items-center gap-2">
                {message.includes('успешно') ? (
                  <CheckCircle2 className="w-5 h-5" />
                ) : (
                  <X className="w-5 h-5" />
                )}
                {message}
              </AlertDescription>
            </Alert>
          )}

          {/* Персональные данные */}
          <div className={`p-8 rounded-3xl border ${themeConfig.isDark ? 'bg-slate-800/40 border-slate-700/50' : 'bg-white/80 border-slate-200'}`}>
            <h2 className={`text-2xl font-bold ${themeConfig.text} mb-6 flex items-center gap-3`}>
              <div className={`p-2 rounded-xl ${themeConfig.isDark ? 'bg-indigo-500/20' : 'bg-indigo-100'}`}>
                <User className={`w-6 h-6 ${themeConfig.isDark ? 'text-indigo-400' : 'text-indigo-600'}`} />
              </div>
              Персональные данные
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <Label htmlFor="full_name" className={`text-sm font-semibold ${themeConfig.text}`}>
                  Полное имя
                </Label>
                <Input
                  id="full_name"
                  name="full_name"
                  type="text"
                  value={formData.full_name}
                  onChange={handleChange}
                  placeholder="Ваше полное имя"
                  className={`h-12 ${themeConfig.input}`}
                />
              </div>

              <div className="space-y-3">
                <Label htmlFor="name" className={`text-sm font-semibold ${themeConfig.text}`}>
                  Имя (латиницей)
                </Label>
                <Input
                  id="name"
                  name="name"
                  type="text"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Например: DMITRI"
                  className={`h-12 ${themeConfig.input}`}
                />
                <p className={`text-xs ${themeConfig.mutedText}`}>
                  💡 Для нумерологических расчётов укажите имя латиницей
                </p>
              </div>

              <div className="space-y-3">
                <Label htmlFor="surname" className={`text-sm font-semibold ${themeConfig.text}`}>
                  Фамилия (латиницей)
                </Label>
                <Input
                  id="surname"
                  name="surname"
                  type="text"
                  value={formData.surname}
                  onChange={handleChange}
                  placeholder="Например: MALAHOV"
                  className={`h-12 ${themeConfig.input}`}
                />
                <p className={`text-xs ${themeConfig.mutedText}`}>
                  💡 Фамилию тоже вводите латиницей
                </p>
              </div>

              <div className="space-y-3">
                <Label htmlFor="birth_date" className={`text-sm font-semibold ${themeConfig.text}`}>
                  Дата рождения
                </Label>
                <Input
                  id="birth_date"
                  name="birth_date"
                  type="text"
                  value={formData.birth_date}
                  onChange={handleChange}
                  placeholder="ДД.ММ.ГГГГ"
                  className={`h-12 ${themeConfig.input}`}
                />
                <p className={`text-xs ${themeConfig.mutedText}`}>
                  ⭐ Используется во всех расчётах платформы
                </p>
              </div>

              <div className="space-y-3">
                <Label htmlFor="phone_number" className={`text-sm font-semibold ${themeConfig.text}`}>
                  Номер телефона
                </Label>
                <Input
                  id="phone_number"
                  name="phone_number"
                  type="text"
                  value={formData.phone_number}
                  onChange={handleChange}
                  placeholder="+37369183398"
                  className={`h-12 ${themeConfig.input}`}
                />
              </div>

              <div className="space-y-3">
                <Label htmlFor="city" className={`text-sm font-semibold ${themeConfig.text}`}>
                  Город
                </Label>
                <Input
                  id="city"
                  name="city"
                  type="text"
                  value={formData.city}
                  onChange={handleChange}
                  placeholder="Ваш город"
                  className={`h-12 ${themeConfig.input}`}
                />
              </div>
            </div>
          </div>

          {/* Дополнительная информация */}
          <div className={`p-8 rounded-3xl border ${themeConfig.isDark ? 'bg-slate-800/40 border-slate-700/50' : 'bg-white/80 border-slate-200'}`}>
            <h2 className={`text-2xl font-bold ${themeConfig.text} mb-6 flex items-center gap-3`}>
              <div className={`p-2 rounded-xl ${themeConfig.isDark ? 'bg-purple-500/20' : 'bg-purple-100'}`}>
                <Home className={`w-6 h-6 ${themeConfig.isDark ? 'text-purple-400' : 'text-purple-600'}`} />
              </div>
              Дополнительная информация
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <Label htmlFor="car_number" className={`text-sm font-semibold ${themeConfig.text}`}>
                  Номер автомобиля
                </Label>
                <Input
                  id="car_number"
                  name="car_number"
                  type="text"
                  value={formData.car_number}
                  onChange={handleChange}
                  placeholder="ABC123"
                  maxLength={13}
                  className={`h-12 ${themeConfig.input}`}
                />
                <p className={`text-xs ${themeConfig.mutedText}`}>
                  До 13 символов, любая раскладка
                </p>
              </div>

              <div className="space-y-3">
                <Label htmlFor="street" className={`text-sm font-semibold ${themeConfig.text}`}>
                  Улица
                </Label>
                <Input
                  id="street"
                  name="street"
                  type="text"
                  value={formData.street}
                  onChange={handleChange}
                  placeholder="Название улицы"
                  className={`h-12 ${themeConfig.input}`}
                />
              </div>

              <div className="space-y-3">
                <Label htmlFor="house_number" className={`text-sm font-semibold ${themeConfig.text}`}>
                  Номер дома
                </Label>
                <Input
                  id="house_number"
                  name="house_number"
                  type="text"
                  value={formData.house_number}
                  onChange={handleChange}
                  placeholder="123А"
                  className={`h-12 ${themeConfig.input}`}
                />
              </div>

              <div className="space-y-3">
                <Label htmlFor="apartment_number" className={`text-sm font-semibold ${themeConfig.text}`}>
                  Номер квартиры
                </Label>
                <Input
                  id="apartment_number"
                  name="apartment_number"
                  type="text"
                  value={formData.apartment_number}
                  onChange={handleChange}
                  placeholder="45"
                  className={`h-12 ${themeConfig.input}`}
                />
              </div>

              <div className="space-y-3 md:col-span-2">
                <Label htmlFor="postal_code" className={`text-sm font-semibold ${themeConfig.text}`}>
                  Почтовый индекс
                </Label>
                <Input
                  id="postal_code"
                  name="postal_code"
                  type="text"
                  value={formData.postal_code}
                  onChange={handleChange}
                  placeholder="123456"
                  className={`h-12 ${themeConfig.input}`}
                />
              </div>
            </div>
          </div>

          {/* Кнопки действий */}
          <div className="flex flex-wrap gap-4 pt-4">
            <Button 
              type="submit" 
              disabled={isLoading}
              className={`${themeConfig.isDark ? 'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500' : 'bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600'} text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-0.5 px-8 h-12`}
            >
              {isLoading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                  Сохранение...
                </>
              ) : (
                <>
                  <Save className="w-5 h-5 mr-2" />
                  Сохранить изменения
                </>
              )}
            </Button>
            <Button 
              type="button" 
              variant="outline"
              onClick={() => setIsEditing(false)}
              disabled={isLoading}
              className={`px-8 h-12 ${themeConfig.isDark ? 'border-slate-600 hover:bg-slate-800' : 'border-slate-300 hover:bg-slate-100'}`}
            >
              <X className="w-5 h-5 mr-2" />
              Отмена
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PersonalDataForm;