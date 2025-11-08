import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { getBackendUrl, getApiBaseUrl } from '../utils/backendUrl';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);
  
  // Используем ref для отслеживания попыток загрузки профиля
  const profileFetchAttempts = useRef(0);
  const maxProfileFetchAttempts = 3;

  // Дополнительное логирование для отслеживания изменений состояния пользователя
  useEffect(() => {
    console.log('🔄 AuthContext: состояние изменилось:', {
      user: user ? `${user.email} (ID: ${user.id})` : 'null',
      hasToken: !!token,
      loading,
      isInitialized,
      timestamp: new Date().toISOString()
    });
  }, [user, token, loading, isInitialized]);

  const backendUrl = getBackendUrl();
  const apiBaseUrl = getApiBaseUrl();

  // Гарантируем единый baseURL для axios
  useEffect(() => {
    axios.defaults.baseURL = apiBaseUrl;
    console.log('[AuthContext] axios.defaults.baseURL установлено в:', axios.defaults.baseURL);
  }, [apiBaseUrl]);

  useEffect(() => {
    let mounted = true;
    
    const initializeAuth = async () => {
      console.log('AuthContext: инициализация аутентификации...');
      console.log('Токен в localStorage:', localStorage.getItem('token') ? 'найден' : 'отсутствует');
      
      try {
        if (token && mounted) {
          console.log('AuthContext: токен есть, устанавливаем заголовки и загружаем профиль');
          // Устанавливаем заголовок авторизации немедленно
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          
          // НЕ пытаемся загрузить профиль автоматически - это может сбрасывать пользователя
          // Вместо этого делаем простую проверку токена
          try {
            const response = await axios.get('/user/profile', {
              timeout: 5000,
              headers: {
                'Authorization': `Bearer ${token}`
              }
            });
            
            if (mounted && response.data) {
              console.log('AuthContext: профиль загружен успешно:', response.data.email);
              setUser(response.data);
            }
          } catch (profileError) {
            console.error('AuthContext: ошибка загрузки профиля:', profileError.message);
            // НЕ делаем logout при ошибке загрузки профиля
            // Пользователь может использовать приложение с сохраненным токеном
          }
        } else {
          console.log('AuthContext: токен отсутствует');
        }
      } catch (error) {
        console.error('AuthContext: ошибка инициализации:', error);
      } finally {
        if (mounted) {
          setLoading(false);
          setIsInitialized(true);
          console.log('AuthContext: инициализация завершена');
        }
      }
    };

    initializeAuth();
    
    return () => {
      mounted = false;
    };
  }, [token, apiBaseUrl]);

  const fetchUserProfileWithRetry = async () => {
    if (profileFetchAttempts.current >= maxProfileFetchAttempts) {
      console.warn('Превышено максимальное количество попыток загрузки профиля');
      setLoading(false);
      return;
    }

    profileFetchAttempts.current++;
    console.log(`Попытка загрузки профиля ${profileFetchAttempts.current}/${maxProfileFetchAttempts}`);

    try {
      const currentToken = localStorage.getItem('token');
      if (!currentToken) {
        console.warn('Токен отсутствует в localStorage');
        setLoading(false);
        return;
      }

      const response = await axios.get('/user/profile', {
        timeout: 10000,
        headers: {
          'Authorization': `Bearer ${currentToken}` // Явно указываем токен
        },
        validateStatus: (status) => status === 200
      });
      
      console.log('Профиль успешно загружен:', response.data.email);
      setUser(response.data);
      profileFetchAttempts.current = 0;
      setLoading(false);
    } catch (error) {
      console.error(`Ошибка загрузки профиля (попытка ${profileFetchAttempts.current}):`, error.message);
      
      // Логаут только при критических ошибках, НЕ при сетевых проблемах
      if (error.response?.status === 401 || error.response?.status === 403) {
        console.warn('Токен недействителен (401/403), выполняем logout');
        logout();
      } else if (profileFetchAttempts.current < maxProfileFetchAttempts) {
        console.log(`Повторная попытка через 2 секунды (сетевая ошибка)`);
        // Повторная попытка через 2 секунды только при сетевых ошибках
        setTimeout(() => {
          fetchUserProfileWithRetry();
        }, 2000);
      } else {
        console.error('Не удалось загрузить профиль после всех попыток');
        // НЕ делаем logout при сетевых ошибках
        setLoading(false);
      }
    }
  };

  const fetchUserProfile = async () => {
    profileFetchAttempts.current = 0; // Сброс счетчика для ручного вызова
    await fetchUserProfileWithRetry();
  };

  const login = async (email, password) => {
    console.log('=== НАЧАЛО ПРОЦЕССА ВХОДА ===');
    console.log('Email:', email);
    
    try {
      console.log('Отправляем запрос на сервер...');
      const response = await axios.post('/auth/login', {
        email,
        password
      }, {
        timeout: 15000
      });

      console.log('Получен ответ от сервера:', response.status);
      const { access_token, user: userData } = response.data;
      
      if (!access_token || !userData) {
        console.error('Некорректные данные с сервера');
        throw new Error('Получены некорректные данные с сервера');
      }

      console.log('Токен получен, длина:', access_token.length);
      console.log('Данные пользователя:', userData.email);
      
      // ПРИНУДИТЕЛЬНОЕ сохранение в localStorage
      try {
        console.log('Сохраняем в localStorage...');
        localStorage.setItem('token', access_token);
        localStorage.setItem('user_id', userData.id);
        localStorage.setItem('user_email', userData.email);
        localStorage.setItem('login_timestamp', Date.now().toString());
        
        // Проверяем что сохранилось
        const savedToken = localStorage.getItem('token');
        console.log('Проверка сохранения - токен в localStorage:', savedToken ? 'сохранен' : 'НЕ СОХРАНЕН');
        
        if (!savedToken) {
          throw new Error('Не удалось сохранить токен в localStorage');
        }
        
      } catch (storageError) {
        console.error('Ошибка сохранения в localStorage:', storageError);
        throw storageError;
      }
      
        // Обновляем state после успешного сохранения в localStorage
        console.log('✅ Обновляем React state...');
        
        // Устанавливаем заголовок авторизации сразу
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        
        // Обновляем state в правильном порядке
        console.log('Обновляем состояние: setLoading(false)...');
        setLoading(false);
        
        console.log('Обновляем состояние: setToken(access_token)...');
        setToken(access_token);
        
        console.log('Обновляем состояние: setUser(userData)...');
        setUser(userData);
        
        console.log('Обновляем состояние: setIsInitialized(true)...');
        setIsInitialized(true);
        
        console.log('=== ВХОД ЗАВЕРШЕН УСПЕШНО ===');
        console.log('React state обновлен, пользователь должен видеть UserDashboard');

      return { success: true };
    } catch (error) {
      console.error('ОШИБКА ВХОДА:', error);
      console.error('Текущий axios.defaults.baseURL:', axios.defaults.baseURL);
      if (error.config) {
        console.error('config.url:', error.config.url);
        console.error('config.baseURL:', error.config.baseURL);
      }
      return {
        success: false,
        error: error.message || 'Ошибка входа в систему'
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post('/auth/register', userData, {
        timeout: 15000
      });
      
      const { access_token, user: newUser } = response.data;
      
      setToken(access_token);
      setUser(newUser);
        
      // Сохраняем токен с дополнительными данными
      localStorage.setItem('token', access_token);
      localStorage.setItem('user_id', newUser.id);
      localStorage.setItem('user_email', newUser.email);
      localStorage.setItem('login_timestamp', Date.now().toString());
      
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      console.log('Успешная регистрация, пользователь:', newUser.email);

      return { success: true };
    } catch (error) {
      console.error('Registration error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed'
      };
    }
  };

  const updateUser = (updatedUserData) => {
    setUser(prevUser => ({
      ...prevUser,
      ...updatedUserData
    }));
    
    // Обновляем localStorage если изменился email
    if (updatedUserData.email) {
      localStorage.setItem('user_email', updatedUserData.email);
    }
  };

  const logout = () => {
    console.log('Выполняется logout...');
    
    setUser(null);
    setToken(null);
    setIsInitialized(false);
    
    // Очищаем все данные сессии
    localStorage.removeItem('token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_email'); 
    localStorage.removeItem('login_timestamp');
    
    // Удаляем заголовок авторизации
    delete axios.defaults.headers.common['Authorization'];
    
    profileFetchAttempts.current = 0; // Сброс счетчика
  };

  // Проверка действительности токена
  const isTokenValid = () => {
    if (!token) return false;
    
    const loginTimestamp = localStorage.getItem('login_timestamp');
    if (!loginTimestamp) return false;
    
    // Токен действителен 24 часа
    const tokenAge = Date.now() - parseInt(loginTimestamp);
    const maxAge = 24 * 60 * 60 * 1000; // 24 часа
    
    return tokenAge < maxAge;
  };

  // Периодическая проверка токена
  useEffect(() => {
    if (!isInitialized || !token) return;

    const checkTokenValidity = () => {
      if (!isTokenValid()) {
        console.warn('Токен истек, выполняем logout');
        logout();
      }
    };

    // Проверяем токен каждые 5 минут
    const interval = setInterval(checkTokenValidity, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, [token, isInitialized]);

  const value = {
    user,
    token,
    loading,
    isInitialized,
    login,
    register,
    updateUser,
    logout,
    refreshProfile: fetchUserProfile,
    isAuthenticated: !!(user && token && isTokenValid())
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};