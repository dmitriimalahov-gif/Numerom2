#!/usr/bin/env python3
"""
Скрипт для создания нового вводного занятия из файлов папки "вводное занятие"
Использование: python create_intro_lesson.py <admin_token>
"""

import sys
import os
import requests
import json
from pathlib import Path
from datetime import datetime
import uuid

BACKEND_URL = "http://localhost:8000"
LESSON_FILES_DIR = Path("файлы для запуска/NumerOM запуск курса/ водное занятие/для сайта вводное занятие")

def read_file_content(file_path):
    """Читает содержимое файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Ошибка чтения файла {file_path}: {str(e)}")
        return None

def parse_test_content(content):
    """Парсит тест из текстового файла"""
    questions = []
    current_question = None
    current_options = []
    
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line or line.startswith('─') or line.startswith('РАЗДЕЛ') or line.startswith('УРОК'):
            continue
        
        # Начало нового вопроса (номер вопроса)
        if line and line[0].isdigit() and '.' in line:
            if current_question and current_options:
                questions.append({
                    'id': f'q{len(questions) + 1}',
                    'question': current_question,
                    'options': current_options,
                    'correct_answer': 1  # B обычно правильный (индекс 1)
                })
            # Извлекаем текст вопроса
            parts = line.split('.', 1)
            current_question = parts[1].strip() if len(parts) > 1 else line
            current_options = []
        # Варианты ответов (A, B, C, D, E)
        elif line and len(line) >= 2 and line[0].isalpha() and line[1] == '.':
            option = line[2:].strip() if len(line) > 2 else line
            current_options.append(option)
    
    # Добавляем последний вопрос
    if current_question and current_options:
        questions.append({
            'id': f'q{len(questions) + 1}',
            'question': current_question,
            'options': current_options,
            'correct_answer': 1  # B обычно правильный
        })
    
    return {
        'id': f'quiz_intro_{uuid.uuid4().hex[:8]}',
        'title': 'Тест: Язык чисел',
        'questions': questions[:10] if len(questions) > 10 else questions
    }

def parse_exercises_content(content):
    """Парсит упражнения из текстового файла"""
    exercises = []
    current_exercise = None
    in_content = False
    in_instructions = False
    
    lines = content.split('\n')
    exercise_num = 0
    
    for line in lines:
        original_line = line
        line = line.strip()
        if not line or line.startswith('─') or line.startswith('РАЗДЕЛ') or line.startswith('УРОК') or line.startswith('ФАЙЛЫ'):
            if line.startswith('ФАЙЛЫ'):
                break
            continue
        
        # Начало нового упражнения (номер с точкой)
        if line and line[0].isdigit() and '.' in line and len(line.split('.')[0]) <= 2:
            if current_exercise and current_exercise['title']:
                exercises.append(current_exercise)
            exercise_num += 1
            current_exercise = {
                'id': f'ex{exercise_num}',
                'title': '',
                'type': 'practical',
                'content': '',
                'instructions': [],
                'expected_outcome': ''
            }
            in_content = False
            in_instructions = False
        elif current_exercise:
            if 'Название:' in line:
                current_exercise['title'] = line.split('Название:')[1].strip()
            elif 'Тип:' in line:
                type_str = line.split('Тип:')[1].strip().lower()
                if 'рефлексия' in type_str:
                    current_exercise['type'] = 'reflection'
                elif 'практическая' in type_str:
                    current_exercise['type'] = 'practical'
            elif 'Содержание:' in line:
                in_content = True
                in_instructions = False
            elif 'Инструкция:' in line or 'Инструкции:' in line:
                in_content = False
                in_instructions = True
            elif 'Ожидаемый результат:' in line:
                current_exercise['expected_outcome'] = line.split('Ожидаемый результат:')[1].strip()
                in_content = False
                in_instructions = False
            elif line:
                if in_content:
                    if current_exercise['content']:
                        current_exercise['content'] += '\n' + line
                    else:
                        current_exercise['content'] = line
                elif in_instructions or (line and (line[0].isdigit() and ')' in line)):
                    current_exercise['instructions'].append(line)
                else:
                    if not current_exercise['content']:
                        current_exercise['content'] = line
                    else:
                        current_exercise['content'] += '\n' + line
    
    if current_exercise and current_exercise['title']:
        exercises.append(current_exercise)
    
    return exercises[:6] if len(exercises) > 6 else exercises

def parse_challenge_content(content):
    """Парсит челлендж из текстового файла"""
    lines = content.split('\n')
    days = []
    current_day = None
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('─') or line.startswith('РАЗДЕЛ') or line.startswith('УРОК'):
            continue
        
        if 'ДЕНЬ' in line and line[0:4] == 'ДЕНЬ':
            if current_day:
                days.append(current_day)
            day_num = line.split('ДЕНЬ')[1].split('—')[0].strip()
            day_name = line.split('—')[1].strip() if '—' in line else ''
            current_day = {
                'day': int(day_num) if day_num.isdigit() else len(days) + 1,
                'title': day_name,
                'tasks': []
            }
        elif current_day and line:
            current_day['tasks'].append(line)
    
    if current_day:
        days.append(current_day)
    
    return {
        'id': f'challenge_intro_{uuid.uuid4().hex[:8]}',
        'title': '7-дневный челлендж: Начало пути',
        'description': 'Ежедневные практики для знакомства с нумерологией',
        'duration_days': 7,
        'daily_tasks': days[:7] if len(days) > 7 else days  # Максимум 7 дней
    }

def upload_pdf(file_path, token):
    """Загружает PDF файл"""
    if not os.path.exists(file_path):
        print(f"❌ PDF файл не найден: {file_path}")
        return None
    
    print(f"\n📤 Загрузка PDF: {file_path}...")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.post(
                f"{BACKEND_URL}/api/admin/consultations/upload-pdf",
                files=files,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ PDF загружен успешно!")
                print(f"   File ID: {result.get('file_id')}")
                return result
            else:
                print(f"❌ Ошибка загрузки PDF: {response.status_code}")
                print(f"   Ответ: {response.text}")
                return None
    except Exception as e:
        print(f"❌ Исключение при загрузке PDF: {str(e)}")
        return None

def create_lesson(lesson_data, token):
    """Создает новый урок через API"""
    print(f"\n💾 Создание урока: {lesson_data.get('title')}...")
    
    endpoint = f"{BACKEND_URL}/api/admin/lessons/create"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(endpoint, json=lesson_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Урок успешно создан!")
            return result
        else:
            print(f"❌ Ошибка создания урока: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Исключение при создании урока: {str(e)}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Использование: python create_intro_lesson.py <admin_token>")
        print("\nЧтобы получить токен:")
        print("1. Войдите в админ-панель")
        print("2. Откройте консоль браузера (F12)")
        print("3. Выполните: localStorage.getItem('token')")
        sys.exit(1)
    
    token = sys.argv[1]
    
    # Проверяем существование папки
    if not LESSON_FILES_DIR.exists():
        print(f"❌ Папка не найдена: {LESSON_FILES_DIR}")
        print(f"   Текущая директория: {os.getcwd()}")
        sys.exit(1)
    
    print("=" * 60)
    print("СОЗДАНИЕ НОВОГО ВВОДНОГО ЗАНЯТИЯ")
    print("=" * 60)
    
    # Читаем файлы
    print("\n📖 Чтение файлов...")
    
    theory_file = LESSON_FILES_DIR / "Урок_Введение_Теория.txt"
    exercises_file = LESSON_FILES_DIR / "Урок_Введение_Упражнения.txt"
    test_file = LESSON_FILES_DIR / "Урок_Введение_Тест.txt"
    challenge_file = LESSON_FILES_DIR / "Урок_Введение_Челлендж.txt"
    pdf_file = LESSON_FILES_DIR / "МЕТОДИЧКА1.pdf"
    
    theory_content = read_file_content(theory_file) if theory_file.exists() else None
    exercises_content = read_file_content(exercises_file) if exercises_file.exists() else None
    test_content = read_file_content(test_file) if test_file.exists() else None
    challenge_content = read_file_content(challenge_file) if challenge_file.exists() else None
    
    if not theory_content:
        print("❌ Не удалось прочитать файл теории")
        sys.exit(1)
    
    # Загружаем PDF
    pdf_result = None
    if pdf_file.exists():
        pdf_result = upload_pdf(pdf_file, token)
    
    # Парсим контент
    print("\n🔍 Парсинг контента...")
    
    quiz = parse_test_content(test_content) if test_content else None
    exercises = parse_exercises_content(exercises_content) if exercises_content else []
    challenge = parse_challenge_content(challenge_content) if challenge_content else None
    
    # Создаем структуру урока
    lesson_id = f"lesson_intro_numbers_{uuid.uuid4().hex[:8]}"
    
    # Формируем структуру content для API
    content_structure = {
        'theory': {
            'introduction': theory_content.split('───────────────────────────────────────────────')[0] if '───────────────────────────────────────────────' in theory_content else theory_content[:1000],
            'full_text': theory_content
        }
    }
    
    lesson_data = {
        'id': lesson_id,
        'title': 'Вводное занятие: Язык чисел',
        'module': 'Модуль 0: Введение',
        'description': 'Знакомство с нумерологией, языком энергии чисел и основными концепциями системы NumerOM',
        'content': content_structure,
        'exercises': exercises,
        'quiz': quiz,
        'challenges': [challenge] if challenge else [],
        'points_required': 0,
        'is_active': True,
        'level': 0,
        'order': 0
    }
    
    # Добавляем PDF если загружен
    if pdf_result:
        lesson_data['pdf_file_id'] = pdf_result.get('file_id')
        lesson_data['pdf_filename'] = pdf_result.get('filename')
        print(f"\n✅ PDF добавлен в урок: {pdf_result.get('filename')}")
    
    # Создаем урок
    print("\n" + "=" * 60)
    print("ДАННЫЕ УРОКА:")
    print("=" * 60)
    print(f"ID: {lesson_data['id']}")
    print(f"Название: {lesson_data['title']}")
    print(f"Модуль: {lesson_data['module']}")
    print(f"Упражнений: {len(exercises)}")
    print(f"Вопросов в тесте: {len(quiz['questions']) if quiz else 0}")
    print(f"Челлендж: {'Да' if challenge else 'Нет'}")
    print(f"PDF: {'Да' if pdf_result else 'Нет'}")
    
    result = create_lesson(lesson_data, token)
    
    if result:
        print("\n" + "=" * 60)
        print("✅ УРОК УСПЕШНО СОЗДАН!")
        print("=" * 60)
        print(f"ID урока: {lesson_id}")
        print(f"\nТеперь вы можете:")
        print("1. Открыть админ-панель")
        print("2. Найти урок в списке")
        print("3. Отредактировать его при необходимости")
        print("4. Проверить отображение во вкладке 'Обучение'")
    else:
        print("\n❌ Не удалось создать урок. Проверьте логи выше.")

if __name__ == "__main__":
    main()
