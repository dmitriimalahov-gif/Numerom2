# API Contracts for Vedic Numerology Calculator

## Описание системы
Калькулятор ведической нумерологии с тремя основными функциями:
1. Расчет личных чисел (жизненный путь, судьба, душа)
2. Расчет числа имени
3. Анализ совместимости партнеров

## Текущие Mock данные (для замены)
- `mockPersonalNumbers` - расчеты личных чисел
- `mockNameNumber` - расчет числа имени  
- `mockCompatibility` - анализ совместимости
- `numberDescriptions` - описания чисел 1-9

## API Endpoints для реализации

### 1. POST /api/personal-numbers
**Запрос:**
```json
{
  "birthDate": "2025-01-15"  // ISO date string
}
```

**Ответ:**
```json
{
  "lifePathNumber": 5,
  "destinyNumber": 6,
  "soulNumber": 6,
  "date": "2025-01-15",
  "descriptions": {
    "lifePathNumber": { "title": "Свободный дух", "description": "...", "traits": [...], "recommendations": "..." },
    "destinyNumber": { "title": "Заботливый", "description": "...", "traits": [...], "recommendations": "..." },
    "soulNumber": { "title": "Заботливый", "description": "...", "traits": [...], "recommendations": "..." }
  }
}
```

### 2. POST /api/name-number  
**Запрос:**
```json
{
  "name": "Елена Петрова"
}
```

**Ответ:**
```json
{
  "name": "Елена Петрова",
  "nameNumber": 8,
  "description": {
    "title": "Материалист",
    "description": "Число 8 представляет амбиции в материальной сфере...",
    "traits": ["Амбиции", "Материальный успех", "Власть", "Организация"],
    "recommendations": "Помните о важности духовных ценностей..."
  }
}
```

### 3. POST /api/compatibility
**Запрос:**
```json
{
  "partner1": {
    "name": "Алексей",
    "birthDate": "2025-01-10"
  },
  "partner2": {
    "name": "Мария", 
    "birthDate": "2025-01-20"
  }
}
```

**Ответ:**
```json
{
  "partner1": {
    "name": "Алексей",
    "number": 7,
    "date": "2025-01-10",
    "description": {...}
  },
  "partner2": {
    "name": "Мария",
    "number": 3,
    "date": "2025-01-20", 
    "description": {...}
  },
  "compatibility": {
    "score": 70,
    "level": "Хорошая"
  }
}
```

## Frontend Integration Changes

### Файлы для изменения:
1. `NumerologyCalculator.jsx` - заменить mock вызовы на API вызовы
2. `PersonalNumbersResult.jsx` - использовать данные из API
3. `NameNumberResult.jsx` - использовать данные из API  
4. `CompatibilityResult.jsx` - использовать данные из API
5. `mock.js` - можно удалить после интеграции

### Интеграция с backend:
```javascript
// Замена mock вызовов на API вызовы в NumerologyCalculator.jsx
const calculatePersonalNumbers = async () => {
  if (!selectedDate) return;
  
  try {
    const response = await axios.post(`${API}/personal-numbers`, {
      birthDate: format(selectedDate, 'yyyy-MM-dd')
    });
    setPersonalResults(response.data);
  } catch (error) {
    console.error('Error calculating personal numbers:', error);
  }
};
```

## Backend Implementation Requirements

### 1. Модели данных (MongoDB):
- `NumberDescription` - описания чисел 1-9
- `CalculationHistory` - история расчетов (опционально)

### 2. Алгоритмы ведической нумерологии:
- Расчет числа жизненного пути (сумма всех цифр даты рождения)
- Расчет числа судьбы (день рождения)  
- Расчет числа души (день месяца рождения)
- Расчет числа имени (сумма буквенных значений)
- Алгоритм совместимости чисел

### 3. Валидация:
- Проверка корректности дат
- Проверка имен (только буквы)
- Обработка ошибок

### 4. База данных:
- Коллекция с описаниями чисел 1-9
- Таблица соответствий букв и цифр для русского алфавита

## Следующие шаги:
1. Создать backend API endpoints
2. Реализовать алгоритмы ведической нумерологии
3. Заменить frontend mock данные на API вызовы
4. Протестировать интеграцию