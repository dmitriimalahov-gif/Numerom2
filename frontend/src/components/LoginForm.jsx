import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Label } from './ui/label';
import { Alert, AlertDescription } from './ui/alert';
import { useAuth } from './AuthContext';

const LoginForm = ({ onSwitchToRegister, onClose }) => {
  const { login, user } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);

  // Автоматически закрываем модал когда пользователь появляется в контексте
  useEffect(() => {
    if (user && isSuccess) {
      console.log('LoginForm: пользователь авторизован, закрываем модал');
      onClose();
    }
  }, [user, isSuccess, onClose]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    const result = await login(formData.email, formData.password);
    
    if (result.success) {
      // Show success message and wait for user state to update
      setError('');
      setIsSuccess(true);
      setIsLoading(false);
      
      console.log('LoginForm: логин успешен, ждем обновления состояния пользователя');
      // Модал закроется автоматически через useEffect когда user появится в контексте
    } else {
      setError(result.error);
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-bold bg-gradient-to-r from-[hsl(160,60%,50%)] via-[hsl(200,70%,55%)] to-[hsl(250,60%,55%)] bg-clip-text text-transparent">
          Добро пожаловать в NUMEROM
        </CardTitle>
        <CardDescription>
          Войдите в свой личный кабинет для самопознания
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="your@email.com"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Пароль</Label>
            <Input
              id="password"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder="Введите пароль..."
            />
          </div>

          <Button 
            type="submit" 
            className={`w-full ${isSuccess ? 'bg-green-500 hover:bg-green-600' : 'numerology-gradient'}`}
            disabled={isLoading || isSuccess}
          >
            {isSuccess ? '✅ Успешный вход!' : isLoading ? 'Вход...' : 'Войти'}
          </Button>

          <div className="text-center">
            <Button
              type="button"
              variant="link"
              onClick={onSwitchToRegister}
              className="text-muted-foreground"
            >
              Нет аккаунта? Зарегистрируйтесь
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default LoginForm;