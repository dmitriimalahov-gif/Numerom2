import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';

const AuthModal = ({ isOpen, onClose }) => {
  const [isLoginMode, setIsLoginMode] = useState(true);

  const switchToRegister = () => setIsLoginMode(false);
  const switchToLogin = () => setIsLoginMode(true);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="p-6 max-h-[95vh] overflow-y-auto">
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