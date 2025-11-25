import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Label } from './ui/label';
import { Alert, AlertDescription } from './ui/alert';
import { useAuth } from './AuthContext';
import { User, Phone, MapPin, Car, Home, Edit3, Calendar } from 'lucide-react';
import { getBackendUrl } from '../utils/backendUrl';

const PersonalDataForm = () => {
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

  if (!isEditing) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center">
                <User className="w-5 h-5 mr-2" />
                Личные данные
              </CardTitle>
              <CardDescription>Ваша персональная информация для нумерологических расчетов</CardDescription>
            </div>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => setIsEditing(true)}
            >
              <Edit3 className="w-4 h-4 mr-2" />
              Редактировать
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <User className="w-4 h-4 text-blue-600" />
                <div>
                  <p className="text-sm text-muted-foreground">Полное имя</p>
                  <p className="font-medium">{user?.full_name || 'Не указано'}</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <User className="w-4 h-4 text-green-600" />
                <div>
                  <p className="text-sm text-muted-foreground">Имя</p>
                  <p className="font-medium">{user?.name || 'Не указано'}</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <User className="w-4 h-4 text-purple-600" />
                <div>
                  <p className="text-sm text-muted-foreground">Фамилия</p>
                  <p className="font-medium">{user?.surname || 'Не указана'}</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <Calendar className="w-4 h-4 text-indigo-600" />
                <div>
                  <p className="text-sm text-muted-foreground">Дата рождения</p>
                  <p className="font-medium">{user?.birth_date || 'Не указана'}</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <Phone className="w-4 h-4 text-green-600" />
                <div>
                  <p className="text-sm text-muted-foreground">Телефон</p>
                  <p className="font-medium">{user?.phone_number || 'Не указан'}</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <MapPin className="w-4 h-4 text-orange-600" />
                <div>
                  <p className="text-sm text-muted-foreground">Город</p>
                  <p className="font-medium">{user?.city || 'Не указан'}</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <Car className="w-4 h-4 text-purple-600" />
                <div>
                  <p className="text-sm text-muted-foreground">Номер автомобиля</p>
                  <p className="font-medium">{user?.car_number || 'Не указан'}</p>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <Home className="w-4 h-4 text-red-600" />
                <div>
                  <p className="text-sm text-muted-foreground">Адрес</p>
                  <div className="font-medium text-sm">
                    {user?.street && <p>ул. {user.street}</p>}
                    {user?.house_number && <p>д. {user.house_number}</p>}
                    {user?.apartment_number && <p>кв. {user.apartment_number}</p>}
                    {user?.postal_code && <p>индекс: {user.postal_code}</p>}
                    {!user?.street && !user?.house_number && !user?.apartment_number && !user?.postal_code && (
                      <p>Не указан</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Edit3 className="w-5 h-5 mr-2" />
          Редактирование личных данных
        </CardTitle>
        <CardDescription>
          Все поля опциональны и используются для нумерологических расчетов
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {message && (
            <Alert variant={message.includes('успешно') ? 'default' : 'destructive'}>
              <AlertDescription>{message}</AlertDescription>
            </Alert>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="full_name">Полное имя</Label>
              <Input
                id="full_name"
                name="full_name"
                type="text"
                value={formData.full_name}
                onChange={handleChange}
                placeholder="Ваше полное имя"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="name">Имя (латиницей)</Label>
              <Input
                id="name"
                name="name"
                type="text"
                value={formData.name}
                onChange={handleChange}
                placeholder="Например: DMITRI"
              />
              <p className="text-xs text-muted-foreground">
                Для нумерологических расчётов укажите имя латиницей (DMITRI, ANDREY и т.д.).
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="surname">Фамилия (латиницей)</Label>
              <Input
                id="surname"
                name="surname"
                type="text"
                value={formData.surname}
                onChange={handleChange}
                placeholder="Например: MALAHOV"
              />
              <p className="text-xs text-muted-foreground">
                Фамилию тоже вводите латиницей — алгоритмы имени работают только с латинскими буквами.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="birth_date">Дата рождения</Label>
              <Input
                id="birth_date"
                name="birth_date"
                type="text"
                value={formData.birth_date}
                onChange={handleChange}
                placeholder="ДД.ММ.ГГГГ"
              />
              <p className="text-xs text-muted-foreground">
                Используется во всех расчётах платформы
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone_number">Номер телефона</Label>
              <Input
                id="phone_number"
                name="phone_number"
                type="text"
                value={formData.phone_number}
                onChange={handleChange}
                placeholder="+37369183398"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="city">Город</Label>
              <Input
                id="city"
                name="city"
                type="text"
                value={formData.city}
                onChange={handleChange}
                placeholder="Ваш город"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="car_number">Номер автомобиля</Label>
              <Input
                id="car_number"
                name="car_number"
                type="text"
                value={formData.car_number}
                onChange={handleChange}
                placeholder="ABC123"
                maxLength={13}
              />
              <p className="text-xs text-muted-foreground">
                До 13 символов, любая раскладка
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="street">Улица</Label>
              <Input
                id="street"
                name="street"
                type="text"
                value={formData.street}
                onChange={handleChange}
                placeholder="Название улицы"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="house_number">Номер дома</Label>
              <Input
                id="house_number"
                name="house_number"
                type="text"
                value={formData.house_number}
                onChange={handleChange}
                placeholder="123А"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="apartment_number">Номер квартиры</Label>
              <Input
                id="apartment_number"
                name="apartment_number"
                type="text"
                value={formData.apartment_number}
                onChange={handleChange}
                placeholder="45"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="postal_code">Почтовый индекс</Label>
              <Input
                id="postal_code"
                name="postal_code"
                type="text"
                value={formData.postal_code}
                onChange={handleChange}
                placeholder="123456"
              />
            </div>
          </div>

          <div className="flex space-x-2 pt-4">
            <Button 
              type="submit" 
              disabled={isLoading}
              className="numerology-gradient"
            >
              {isLoading ? 'Сохранение...' : 'Сохранить'}
            </Button>
            <Button 
              type="button" 
              variant="outline"
              onClick={() => setIsEditing(false)}
            >
              Отмена
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default PersonalDataForm;