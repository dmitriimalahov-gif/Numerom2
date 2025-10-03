# Система аутентификации и авторизации

## Обзор

NUMEROM использует JWT (JSON Web Tokens) для аутентификации пользователей с системой ролей и прав доступа.

## Компоненты системы

### Backend (auth.py)

#### Конфигурация безопасности
```python
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 часа

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
```

#### Основные функции

##### 1. Хеширование паролей
```python
def get_password_hash(password: str) -> str:
    """Создает bcrypt хеш пароля"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль против хеша"""
    return pwd_context.verify(plain_password, hashed_password)
```

##### 2. JWT токены
```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Создает JWT токен с данными пользователя
    
    Args:
        data: Словарь с данными для включения в токен
        expires_delta: Время жизни токена (по умолчанию 24 часа)
    
    Returns:
        str: Закодированный JWT токен
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

##### 3. Проверка токенов
```python
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Извлекает текущего пользователя из JWT токена
    
    Returns:
        dict: Данные пользователя {"user_id": "xxx"}
    
    Raises:
        HTTPException: 401 если токен недействителен
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    return {"user_id": user_id}
```

## Система ролей

### Роли пользователей

#### 1. Обычный пользователь
```python
# Права доступа:
- Нумерологические расчеты
- Просмотр своих результатов
- Обучающие материалы (с ограничениями по кредитам)
- Управление своим профилем
```

#### 2. Администратор (is_admin = True)
```python
# Дополнительные права:
- Просмотр списка пользователей
- Управление кредитами пользователей
- Базовая аналитика
```

#### 3. Суперадминистратор (is_super_admin = True)
```python
# Полные права:
- Все права администратора
- Управление обучающим контентом
- Загрузка уроков и материалов
- Создание администраторов
- Системные настройки
```

### Проверка ролей

#### Создание суперадминистратора
```python
async def ensure_super_admin_exists(db):
    """
    Создает суперадминистратора при первом запуске
    Email: dmitrii.malahov@gmail.com
    Password: 756bvy67H
    """
    SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
    SUPER_ADMIN_PASSWORD = "756bvy67H"
    
    existing_admin = await db.users.find_one({"email": SUPER_ADMIN_EMAIL})
    
    if not existing_admin:
        super_admin = User(
            email=SUPER_ADMIN_EMAIL,
            password_hash=get_password_hash(SUPER_ADMIN_PASSWORD),
            full_name="Дмитрий Малахов (Суперадминистратор)",
            birth_date="01.01.1980",
            city="Москва",
            is_premium=True,
            is_super_admin=True,
            credits_remaining=1000000  # Безлимитные кредиты
        )
        
        await db.users.insert_one(super_admin.dict())
```

#### Проверка прав суперадмина
```python
def require_super_admin(current_user: dict, db):
    """Декоратор для проверки прав суперадминистратора"""
    async def check_super_admin():
        user_data = await db.users.find_one({"id": current_user["user_id"]})
        if not user_data or not user_data.get("is_super_admin", False):
            raise HTTPException(
                status_code=403, 
                detail="Доступ запрещен. Требуются права суперадминистратора."
            )
        return User(**user_data)
    return check_super_admin
```

## API Endpoints для аутентификации

### 1. Регистрация пользователя
```http
POST /api/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "Имя Фамилия",
  "birth_date": "15.08.1990",
  "city": "Москва"
}
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid4-string",
    "email": "user@example.com",
    "full_name": "Имя Фамилия",
    "birth_date": "15.08.1990",
    "city": "Москва",
    "is_premium": false,
    "credits_remaining": 0,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### 2. Вход в систему
```http
POST /api/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Ответ:** такой же как при регистрации

### 3. Получение профиля пользователя
```http
GET /api/profile
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Ответ:**
```json
{
  "id": "uuid4-string",
  "email": "user@example.com",
  "full_name": "Имя Фамилия",
  "birth_date": "15.08.1990",
  "city": "Москва",
  "phone_number": "+37369183398",
  "is_premium": false,
  "is_super_admin": false,
  "is_admin": false,
  "subscription_type": null,
  "credits_remaining": 50,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 4. Обновление профиля
```http
PUT /api/profile
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "full_name": "Новое Имя",
  "phone_number": "+37369183398",
  "city": "Кишинев",
  "car_number": "ABC123",
  "street": "ул. Пушкина",
  "house_number": "10",
  "apartment_number": "5",
  "postal_code": "2001"
}
```

## Frontend интеграция (AuthContext)

### AuthContext компонент
```jsx
import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);

  // Проверка токена при загрузке
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      // Проверяем валидность токена
      checkTokenValidity(token);
    } else {
      setLoading(false);
      setIsInitialized(true);
    }
  }, []);

  const checkTokenValidity = async (token) => {
    try {
      const response = await fetch('/api/profile', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        localStorage.removeItem('token');
      }
    } catch (error) {
      console.error('Token validation error:', error);
      localStorage.removeItem('token');
    } finally {
      setLoading(false);
      setIsInitialized(true);
    }
  };

  const login = async (email, password) => {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      setUser(data.user);
      return { success: true };
    } else {
      const error = await response.json();
      return { success: false, error: error.detail };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      login, 
      logout, 
      loading, 
      isInitialized 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

### Использование в компонентах
```jsx
import { useAuth } from './AuthContext';

const SomeComponent = () => {
  const { user, loading, isInitialized } = useAuth();

  if (loading || !isInitialized) {
    return <div>Загрузка...</div>;
  }

  if (!user) {
    return <div>Необходимо войти в систему</div>;
  }

  return (
    <div>
      <h1>Добро пожаловать, {user.full_name}!</h1>
      <p>Кредитов: {user.credits_remaining}</p>
    </div>
  );
};
```

## Middleware и защита маршрутов

### Backend middleware
```python
from fastapi import Depends

# Защищенный эндпоинт
@app.get("/api/protected-endpoint")
async def protected_endpoint(current_user: dict = Depends(get_current_user)):
    # current_user содержит {"user_id": "xxx"}
    return {"message": "Доступ разрешен", "user_id": current_user["user_id"]}

# Эндпоинт только для админов
@app.get("/api/admin/users")
async def get_all_users(current_user: dict = Depends(get_current_user)):
    # Дополнительная проверка роли админа
    user_data = await db.users.find_one({"id": current_user["user_id"]})
    if not user_data.get("is_super_admin", False):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    users = await db.users.find({}).to_list(length=None)
    return users
```

### Frontend защищенные маршруты
```jsx
import { Navigate } from 'react-router-dom';
import { useAuth } from './AuthContext';

const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { user, loading, isInitialized } = useAuth();

  if (loading || !isInitialized) {
    return <div>Загрузка...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (adminOnly && !user.is_super_admin) {
    return <div>Недостаточно прав доступа</div>;
  }

  return children;
};

// Использование:
<Route path="/admin" element={
  <ProtectedRoute adminOnly={true}>
    <AdminPanel />
  </ProtectedRoute>
} />
```

## Безопасность

### 1. Хранение паролей
- Используется **bcrypt** с автоматической солью
- Пароли никогда не хранятся в открытом виде
- Минимальная длина пароля не установлена (рекомендуется добавить)

### 2. JWT токены
- **Время жизни**: 24 часа
- **Алгоритм**: HS256
- **Секретный ключ**: задается через переменную окружения
- Токены содержат только `user_id` в поле `sub`

### 3. CORS
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Защита от атак
- **Rate limiting**: не реализован (рекомендуется добавить)
- **CSRF**: защищен через отсутствие cookies в пользу Bearer токенов
- **XSS**: защищен через правильную обработку данных
- **SQL Injection**: не применимо (используется MongoDB)

## Рекомендации по улучшению

### 1. Безопасность
- Добавить rate limiting для login/register
- Реализовать refresh токены
- Добавить двухфакторную аутентификацию
- Валидация сложности паролей

### 2. Пользовательский опыт
- Восстановление пароля через email
- Подтверждение email при регистрации
- "Запомнить меня" функциональность
- Уведомления о входе с новых устройств

### 3. Мониторинг
- Логирование попыток входа
- Отслеживание подозрительной активности
- Метрики аутентификации


