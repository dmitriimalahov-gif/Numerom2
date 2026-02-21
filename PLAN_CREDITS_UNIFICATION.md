# План объединения систем баллов

## Текущая ситуация

### Система 1: Кредиты (credits_remaining)
- **Хранилище**: `users.credits_remaining`
- **Транзакции**: `credit_transactions` коллекция
- **Использование**: Оплата услуг (нумерология, ведическое время, консультации)
- **Функции**: 
  - `deduct_credits()` - списание баллов
  - `record_credit_transaction()` - запись транзакции
- **Отображение**: Компонент `CreditHistory.jsx` с категориями: numerology, vedic, learning, quiz, materials, purchase, refund

### Система 2: Баллы за обучение (points_earned)
- **Хранилище**: 
  - `quiz_attempts.points_earned` - баллы за тесты
  - `challenge_progress.points_earned` - баллы за челленджи
  - `exercise_responses.points_earned` - баллы за упражнения
- **Использование**: Только для статистики в `points_breakdown`
- **Проблема**: НЕ связаны с системой кредитов, не накапливаются, не используются

## Цель

Объединить обе системы в единую систему кредитов, где:
1. Все баллы за обучение начисляются как кредиты
2. Все транзакции записываются в `credit_transactions`
3. Все баллы отображаются в "Истории баллов"
4. Баллы можно накапливать и использовать для оплаты услуг

## Пошаговый план реализации

### Шаг 1: Создать функцию начисления кредитов за обучение

**Файл**: `backend/server.py` (после функции `deduct_credits`)

**Функция**: `award_credits_for_learning()`
```python
async def award_credits_for_learning(
    user_id: str, 
    amount: int, 
    description: str, 
    category: str,  # 'quiz', 'challenge', 'exercise', 'lesson'
    details: dict = None
):
    """Начислить кредиты за обучение и записать транзакцию"""
    if amount <= 0:
        return  # Не начисляем нулевые или отрицательные баллы
    
    user = await db.users.find_one({'id': user_id})
    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    # Начисляем кредиты
    await db.users.update_one({'id': user_id}, {'$inc': {'credits_remaining': amount}})
    
    # Записываем транзакцию
    await record_credit_transaction(user_id, amount, description, category, details)
```

### Шаг 2: Интегрировать начисление кредитов в эндпоинт упражнений

**Файл**: `backend/server.py`
**Эндпоинт**: `/api/student/exercise-response` (строка 6338)

**Изменения**:
- После сохранения ответа на упражнение (строка 6377 или 6363)
- Начислить кредиты:
  - 10 баллов за каждое упражнение (или использовать `points_earned` из `exercise_responses`)
  - Категория: `'exercise'`
  - Описание: `f"Выполнение упражнения урока {lesson_id}"`
  - Детали: `{'lesson_id': lesson_id, 'exercise_id': exercise_id}`

**Код**:
```python
# После сохранения exercise_response_data
if not existing_response:  # Только для новых ответов
    await award_credits_for_learning(
        user_id=user_id,
        amount=10,  # или points_earned из exercise_responses
        description=f"Выполнение упражнения урока {request_data['lesson_id']}",
        category='exercise',
        details={
            'lesson_id': request_data['lesson_id'],
            'exercise_id': request_data['exercise_id']
        }
    )
```

### Шаг 3: Интегрировать начисление кредитов в эндпоинт челленджей

**Файл**: `backend/server.py`
**Эндпоинт**: `/api/student/challenge-progress` (строка 6421)

**Изменения**:
- При завершении дня челленджа (строка 6479) - начислить баллы за день
- При завершении всего челленджа (строка 6489) - начислить бонусные баллы
- Использовать `points_earned` из расчета
- Категория: `'challenge'`
- Описание: `f"Завершение дня {day} челленджа урока {lesson_id}"` или `f"Завершение челленджа урока {lesson_id}"`

**Код**:
```python
# После расчета points_earned (строка 6488-6490)
if mark_completed and day not in completed_days:
    # Начисляем баллы за день
    await award_credits_for_learning(
        user_id=user_id,
        amount=points_per_day,
        description=f"Завершение дня {day} челленджа урока {lesson_id}",
        category='challenge',
        details={
            'lesson_id': lesson_id,
            'challenge_id': challenge_id,
            'day': day
        }
    )

# При завершении всего челленджа (строка 6489)
if is_completed and not existing_progress.get("completed_at"):
    # Начисляем бонусные баллы
    await award_credits_for_learning(
        user_id=user_id,
        amount=bonus_points,
        description=f"Завершение челленджа урока {lesson_id}",
        category='challenge',
        details={
            'lesson_id': lesson_id,
            'challenge_id': challenge_id,
            'total_days': total_days
        }
    )
```

### Шаг 4: Интегрировать начисление кредитов в эндпоинт тестов

**Файл**: `backend/server.py`
**Эндпоинт**: `/api/student/quiz-attempt` (строка 6652)

**Изменения**:
- После сохранения попытки теста (строка 6678)
- Начислить кредиты только если тест пройден (`passed = True`)
- Использовать `points_earned` из расчета (строка 6661-6664)
- Категория: `'quiz'`
- Описание: `f"Прохождение теста урока {lesson_id}"`

**Код**:
```python
# После сохранения attempt_data (строка 6678)
if passed and points_earned > 0:
    await award_credits_for_learning(
        user_id=user_id,
        amount=points_earned,
        description=f"Прохождение теста урока {lesson_id}",
        category='quiz',
        details={
            'lesson_id': lesson_id,
            'quiz_id': request_data.get("quiz_id", lesson_id),
            'score': request_data["score"],
            'passed': passed
        }
    )
```

### Шаг 5: Интегрировать начисление кредитов при завершении урока

**Файл**: `backend/server.py`
**Функция**: `update_lesson_progress()` (нужно найти)

**Изменения**:
- При достижении 100% завершения урока
- Начислить бонусные кредиты (например, 50 баллов)
- Категория: `'lesson'`
- Описание: `f"Завершение урока {lesson_id}"`

**Код**:
```python
# В функции update_lesson_progress, когда completion_percentage достигает 100%
if completion_percentage >= 100 and not progress.get("is_completed"):
    await award_credits_for_learning(
        user_id=user_id,
        amount=50,  # Бонус за завершение урока
        description=f"Завершение урока {lesson_id}",
        category='lesson',
        details={
            'lesson_id': lesson_id,
            'completion_percentage': completion_percentage
        }
    )
```

### Шаг 6: Обновить компонент CreditHistory.jsx

**Файл**: `frontend/src/components/CreditHistory.jsx`

**Изменения**:
- Убедиться, что категории `'quiz'`, `'challenge'`, `'exercise'`, `'lesson'` правильно отображаются
- Добавить иконки и цвета для новых категорий (если нужно)
- Категория `'learning'` уже есть (строка 44, 54)

**Проверка**:
- `categoryIcons` (строка 41-49) - добавить иконки для новых категорий
- `categoryColors` (строка 51-59) - добавить цвета для новых категорий

### Шаг 7: Тестирование

**Тестовые сценарии**:
1. Выполнить упражнение → проверить начисление 10 баллов в `credit_transactions`
2. Завершить день челленджа → проверить начисление баллов за день
3. Завершить весь челлендж → проверить начисление бонусных баллов
4. Пройти тест → проверить начисление баллов за тест
5. Завершить урок → проверить начисление бонусных баллов
6. Проверить отображение всех транзакций в "Истории баллов"
7. Проверить, что баланс `credits_remaining` увеличивается
8. Проверить, что начисленные баллы можно использовать для оплаты услуг

## Важные замечания

1. **Избежать двойного начисления**: Проверять, не начислялись ли уже баллы за это действие
2. **Обратная совместимость**: Старые записи с `points_earned` останутся в БД, но новые будут начисляться как кредиты
3. **Миграция данных**: Опционально - можно создать скрипт для миграции существующих `points_earned` в кредиты (но это не обязательно)
4. **Логирование**: Все начисления должны логироваться для отладки

## Ожидаемый результат

После реализации:
- Все баллы за обучение начисляются как кредиты
- Все транзакции видны в "Истории баллов"
- Студенты могут накапливать баллы и использовать их для оплаты услуг
- Единая система баллов для всего проекта



