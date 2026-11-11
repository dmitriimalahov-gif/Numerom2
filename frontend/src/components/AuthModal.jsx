import React, { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';

const AuthModal = ({ isOpen, onClose, initialMode = 'login' }) => {
  const [isLoginMode, setIsLoginMode] = useState(initialMode === 'login');

  useEffect(() => {
    if (isOpen) setIsLoginMode(initialMode === 'login');
  }, [isOpen, initialMode]);

  const switchToRegister = () => setIsLoginMode(false);
  const switchToLogin = () => setIsLoginMode(true);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="nm-auth-dialog">
        <DialogHeader className="sr-only">
          <DialogTitle>{isLoginMode ? 'Форма входа в систему' : 'Регистрация пользователя'}</DialogTitle>
          <DialogDescription>
            {isLoginMode
              ? 'Введите свои учетные данные, чтобы войти в систему.'
              : 'Заполните форму, чтобы создать новую учетную запись.'}
          </DialogDescription>
        </DialogHeader>
        {isLoginMode ? (
          <LoginForm 
            onSwitchToRegister={switchToRegister}
            onClose={onClose}
          />
        ) : (
          <RegisterForm 
            onSwitchToLogin={switchToLogin}
            onClose={onClose}
          />
        )}
      </DialogContent>
    </Dialog>
  );
};

export default AuthModal;