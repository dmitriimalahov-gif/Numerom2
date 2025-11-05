#!/usr/bin/env python3
"""
Скрипт для автоматического создания всех занятий (0-9) из папки "файлы для запуска"
Использование: python create_all_lessons.py <admin_token>
"""

import sys
import os
import requests
import json
from pathlib import Path
from datetime import datetime
import uuid
import re

BACKEND_URL = "http://localhost:8000"
BASE_DIR = Path("файлы для запуска/NumerOM запуск курса")

# Маппинг номеров занятий на названия и модули
LESSON_INFO = {
    " водное занятие": {
        "number": -1,
        "title": "Вводное занятие: Язык чисел",
        "module": "Модуль 0: Введение",
        "prefix": "intro"
    },
    "0": {
        "number": 0,
        "title": "Урок 0: Число проблемы",
        "module": "Модуль 0: Введение",
        "prefix": "problem"
    },
    "1": {
        "number": 1,
        "title": "Урок 1: СУРЬЯ (Солнце) - Число 1",
        "module": "Модуль 1: Основы",
        "prefix": "surya"
    },
    "2": {
        "number": 2,
        "title": "Урок 2: ЧАНДРА (Луна) - Число 2",
        "module": "Модуль 1: Основы",
        "prefix": "chandra"
    },
    "3": {
        "number": 3,
        "title": "Урок 3: ГУРУ (Юпитер) - Число 3",
        "module": "Модуль 1: Основы",
        "prefix": "guru"
    },
    "4": {
        "number": 4,
        "title": "Урок 4: РАХУ - Число 4",
        "module": "Модуль 2: Продвинутый",
        "prefix": "rahu"
    },
    "5": {
        "number": 5,
        "title": "Урок 5: БУДДХИ (Меркурий) - Число 5",
        "module": "Модуль 2: Продвинутый",
        "prefix": "buddhi"
    },
    "6": {
        "number": 6,
        "title": "Урок 6: ШУКРА (Венера) - Число 6",
        "module": "Модуль 2: Продвинутый",
        "prefix": "shukra"
    },
    "7": {
        "number": 7,
        "title": "Урок 7: КЕТУ - Число 7",
        "module": "Модуль 3: Углубленный",
        "prefix": "ketu"
    },
    "8": {
        "number": 8,
        "title": "Урок 8: ШАНИ (Сатурн) - Число 8",
        "module": "Модуль 3: Углубленный",
        "prefix": "shani"
    },
    "9": {
        "number": 9,
        "title": "Урок 9: МАНГАЛ (Марс) - Число 9",
        "module": "Модуль 3: Углубленный",
        "prefix": "mangal"
    }
}

def find_lesson_folder(lesson_dir):
    """Находит папку с файлами для сайта"""
    if not lesson_dir.exists():
        return None
    
    # Сначала проверяем, есть ли txt файлы (теория, тест и т.д.) прямо в папке
    has_txt_files = any(f.is_file() and f.suffix == '.txt' and ('теория' in f.name.lower() or 'тест' in f.name.lower() or 'упражнения' in f.name.lower() or 'челлендж' in f.name.lower()) for f in lesson_dir.iterdir() if f.is_file())
    
    # Если txt файлы есть прямо в папке, возвращаем её
    if has_txt_files:
        return lesson_dir
    
    # Если txt файлов нет, ищем папку "для сайта", "Для сайта", " для сайта" и т.д.
    for item in lesson_dir.iterdir():
        if item.is_dir():
            name_lower = item.name.lower()
            # Проверяем наличие ключевых слов
            if "сайт" in name_lower or "для" in name_lower or "вводное" in name_lower:
                # Проверяем, есть ли txt файлы в этой подпапке
                has_txt_files_sub = any(f.is_file() and f.suffix == '.txt' and ('теория' in f.name.lower() or 'тест' in f.name.lower() or 'упражнения' in f.name.lower() or 'челлендж' in f.name.lower()) for f in item.iterdir() if f.is_file())
                if has_txt_files_sub:
                    return item
                # Если в подпапке нет txt файлов, но есть другие подпапки, ищем дальше
                for sub_item in item.iterdir():
                    if sub_item.is_dir():
                        sub_name_lower = sub_item.name.lower()
                        if "сайт" in sub_name_lower or "для" in sub_name_lower or "вводное" in sub_name_lower:
                            has_txt_files_sub2 = any(f.is_file() and f.suffix == '.txt' and ('теория' in f.name.lower() or 'тест' in f.name.lower() or 'упражнения' in f.name.lower() or 'челлендж' in f.name.lower()) for f in sub_item.iterdir() if f.is_file())
                            if has_txt_files_sub2:
                                return sub_item
    
    # Если не нашли по ключевым словам, ищем любую подпапку с txt файлами
    for item in lesson_dir.iterdir():
        if item.is_dir():
            has_txt_files_sub = any(f.is_file() and f.suffix == '.txt' for f in item.iterdir() if f.is_file())
            if has_txt_files_sub:
                return item
    
    # Если ничего не найдено, возвращаем саму папку (на случай, если файлы там, но без ключевых слов)
    return lesson_dir

def find_lesson_files(lesson_folder):
    """Находит все файлы урока (теория, упражнения, тест, челлендж, PDF, Word)"""
    files = {
        'theory': None,
        'exercises': None,
        'test': None,
        'challenge': None,
        'pdfs': [],
        'word_files': []
    }
    
    if not lesson_folder or not lesson_folder.exists():
        return files
    
    for file_path in lesson_folder.iterdir():
        if not file_path.is_file():
            continue
        
        name = file_path.name.lower()
        
        # Теория
        if 'теория' in name or 'theory' in name:
            if file_path.suffix == '.txt':
                files['theory'] = file_path
        
        # Упражнения
        elif 'упражнен' in name or 'exercise' in name:
            if file_path.suffix == '.txt':
                files['exercises'] = file_path
        
        # Тест
        elif 'тест' in name or 'quiz' in name or 'test' in name:
            if file_path.suffix == '.txt':
                files['test'] = file_path
        
        # Челлендж
        elif 'челлендж' in name or 'challenge' in name:
            if file_path.suffix == '.txt':
                files['challenge'] = file_path
        
        # PDF файлы
        elif file_path.suffix == '.pdf':
            files['pdfs'].append(file_path)
        
        # Word файлы
        elif file_path.suffix in ['.docx', '.doc']:
            files['word_files'].append(file_path)
    
    return files

def read_file_content(file_path):
    """Читает содержимое файла"""
    if not file_path or not file_path.exists():
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"   ⚠️  Ошибка чтения {file_path.name}: {str(e)}")
        return None

def parse_test_content(content):
    """Парсит тест из текстового файла"""
    if not content:
        return None
    
    questions = []
    current_question = None
    current_options = []
    
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line or line.startswith('─') or line.startswith('РАЗДЕЛ') or line.startswith('УРОК'):
            continue
        
        # Начало нового вопроса
        if line and line[0].isdigit() and '.' in line:
            if current_question and current_options:
                questions.append({
                    'id': f'q{len(questions) + 1}',
                    'question': current_question,
                    'options': current_options,
                    'correct_answer': 1  # По умолчанию B
                })
            parts = line.split('.', 1)
            current_question = parts[1].strip() if len(parts) > 1 else line
            current_options = []
        # Варианты ответов
        elif line and len(line) >= 2 and line[0].isalpha() and line[1] == '.':
            option = line[2:].strip() if len(line) > 2 else line
            current_options.append(option)
    
    if current_question and current_options:
        questions.append({
            'id': f'q{len(questions) + 1}',
            'question': current_question,
            'options': current_options,
            'correct_answer': 1
        })
    
    if not questions:
        return None
    
    return {
        'id': f'quiz_{uuid.uuid4().hex[:8]}',
        'title': 'Тест урока',
        'questions': questions[:10] if len(questions) > 10 else questions
    }

def parse_exercises_content(content):
    """Парсит упражнения из текстового файла"""
    if not content:
        return []
    
    exercises = []
    current_exercise = None
    in_content = False
    in_instructions = False
    
    lines = content.split('\n')
    exercise_num = 0
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('─') or line.startswith('РАЗДЕЛ') or line.startswith('УРОК') or line.startswith('ФАЙЛЫ'):
            if line.startswith('ФАЙЛЫ'):
                break
            continue
        
        # Начало нового упражнения
        if line and line[0].isdigit() and '.' in line and len(line.split('.')[0]) <= 2:
            if current_exercise and current_exercise.get('title'):
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
                    current_exercise['content'] += '\n' + line if current_exercise['content'] else line
                elif in_instructions or (line and line[0].isdigit() and ')' in line):
                    current_exercise['instructions'].append(line)
                else:
                    current_exercise['content'] += '\n' + line if current_exercise['content'] else line
    
    if current_exercise and current_exercise.get('title'):
        exercises.append(current_exercise)
    
    return exercises[:6] if len(exercises) > 6 else exercises

def parse_challenge_content(content):
    """Парсит челлендж из текстового файла"""
    if not content:
        return None
    
    lines = content.split('\n')
    days = []
    current_day = None
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('─') or line.startswith('РАЗДЕЛ') or line.startswith('УРОК'):
            continue
        
        if 'ДЕНЬ' in line or 'ДЕНЬ' in line.upper():
            if current_day:
                days.append(current_day)
            # Извлекаем номер дня
            day_match = re.search(r'(\d+)', line)
            day_num = int(day_match.group(1)) if day_match else len(days) + 1
            day_name = line.split('—')[1].strip() if '—' in line else (line.split('-')[1].strip() if '-' in line else '')
            current_day = {
                'day': day_num,
                'title': day_name,
                'tasks': []
            }
        elif current_day and line:
            current_day['tasks'].append(line)
    
    if current_day:
        days.append(current_day)
    
    if not days:
        return None
    
    return {
        'id': f'challenge_{uuid.uuid4().hex[:8]}',
        'title': f'{len(days)}-дневный челлендж',
        'description': 'Ежедневные практики для закрепления материала',
        'duration_days': len(days),
        'daily_tasks': days[:14] if len(days) > 14 else days
    }

def upload_file(file_path, file_type, token):
    """Загружает файл через соответствующий endpoint"""
    endpoint_map = {
        'pdf': (f"{BACKEND_URL}/api/admin/consultations/upload-pdf", 'application/pdf'),
        'word': (f"{BACKEND_URL}/api/admin/lessons/upload-word", 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
        'video': (f"{BACKEND_URL}/api/admin/consultations/upload-video", 'video/mp4')
    }
    
    endpoint_info = endpoint_map.get(file_type)
    if not endpoint_info:
        return None
    
    endpoint, content_type = endpoint_info
    
    try:
        with open(file_path, 'rb') as f:
            # Указываем явно content-type для правильной обработки на сервере
            files = {'file': (file_path.name, f, content_type)}
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.post(endpoint, files=files, headers=headers, timeout=60)
            
            if response.status_code == 200:
                return response.json()
            else:
                error_text = response.text[:200] if response.text else "Нет ответа"
                print(f"      ❌ Ошибка загрузки: {response.status_code}")
                print(f"         Детали: {error_text}")
                return None
    except Exception as e:
        print(f"      ❌ Исключение: {str(e)}")
        return None

def create_lesson(lesson_data, token):
    """Создает урок через API"""
    endpoint = f"{BACKEND_URL}/api/admin/lessons/create"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(endpoint, json=lesson_data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"      ❌ Ошибка создания: {response.status_code}")
            print(f"      Ответ: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"      ❌ Исключение: {str(e)}")
        return None

def process_lesson(lesson_key, token):
    """Обрабатывает одно занятие"""
    info = LESSON_INFO[lesson_key]
    lesson_dir = BASE_DIR / lesson_key
    
    print(f"\n{'='*70}")
    print(f"📚 {info['title']}")
    print(f"{'='*70}")
    
    # Находим папку с файлами
    lesson_folder = find_lesson_folder(lesson_dir)
    if not lesson_folder:
        print(f"   ⚠️  Папка не найдена: {lesson_dir}")
        return False
    
    print(f"   📁 Папка: {lesson_folder.name}")
    
    # Находим файлы
    files = find_lesson_files(lesson_folder)
    
    # Читаем текстовые файлы
    theory_content = read_file_content(files['theory'])
    exercises_content = read_file_content(files['exercises'])
    test_content = read_file_content(files['test'])
    challenge_content = read_file_content(files['challenge'])
    
    print(f"   📄 Файлы: Теория={'✓' if theory_content else '✗'}, "
          f"Упражнения={'✓' if exercises_content else '✗'}, "
          f"Тест={'✓' if test_content else '✗'}, "
          f"Челлендж={'✓' if challenge_content else '✗'}")
    
    # Загружаем PDF файлы
    pdf_file_id = None
    pdf_filename = None
    if files['pdfs']:
        print(f"   📎 PDF файлов найдено: {len(files['pdfs'])}")
        # Берем первый PDF как основной
        pdf_result = upload_file(files['pdfs'][0], 'pdf', token)
        if pdf_result:
            pdf_file_id = pdf_result.get('file_id')
            pdf_filename = pdf_result.get('filename')
            print(f"      ✅ PDF загружен: {pdf_filename}")
    
    # Загружаем Word файлы
    word_file_id = None
    word_filename = None
    if files['word_files']:
        print(f"   📄 Word файлов найдено: {len(files['word_files'])}")
        # Берем первый Word как основной
        word_result = upload_file(files['word_files'][0], 'word', token)
        if word_result:
            word_file_id = word_result.get('file_id')
            word_filename = word_result.get('filename')
            print(f"      ✅ Word загружен: {word_filename}")
    
    # Парсим контент
    quiz = parse_test_content(test_content) if test_content else None
    exercises = parse_exercises_content(exercises_content) if exercises_content else []
    challenge = parse_challenge_content(challenge_content) if challenge_content else None
    
    # Формируем структуру content
    content_structure = {}
    if theory_content:
        content_structure['theory'] = {
            'introduction': theory_content.split('───────────────────────────────────────────────')[0] if '───────────────────────────────────────────────' in theory_content else theory_content[:1000],
            'full_text': theory_content
        }
    
    # Создаем ID урока
    lesson_id = f"lesson_{info['prefix']}_{uuid.uuid4().hex[:8]}"
    
    # Формируем данные урока
    lesson_data = {
        'id': lesson_id,
        'title': info['title'],
        'module': info['module'],
        'description': f"Урок {info['number'] if info['number'] >= 0 else 'вводный'} системы NumerOM",
        'content': content_structure,
        'exercises': exercises,
        'quiz': quiz,
        'challenges': [challenge] if challenge else [],
        'points_required': 0,
        'is_active': True,
        'level': max(1, info['number'] + 1) if info['number'] >= 0 else 0,
        'order': info['number'] if info['number'] >= 0 else -1
    }
    
    # Добавляем медиафайлы
    if pdf_file_id:
        lesson_data['pdf_file_id'] = pdf_file_id
        lesson_data['pdf_filename'] = pdf_filename
    
    if word_file_id:
        lesson_data['word_file_id'] = word_file_id
        lesson_data['word_filename'] = word_filename
    
    print(f"   📊 Контент: Упражнений={len(exercises)}, "
          f"Вопросов в тесте={len(quiz['questions']) if quiz else 0}, "
          f"Челлендж={'Да' if challenge else 'Нет'}")
    
    # Создаем урок
    result = create_lesson(lesson_data, token)
    
    if result:
        print(f"   ✅ Урок успешно создан! ID: {lesson_id}")
        return True
    else:
        print(f"   ❌ Не удалось создать урок")
        return False

def main():
    if len(sys.argv) < 2:
        print("Использование: python create_all_lessons.py <admin_token>")
        print("\nЧтобы получить токен:")
        print("1. Войдите в админ-панель на http://localhost:3000/admin")
        print("2. Откройте консоль браузера (F12)")
        print("3. Выполните: localStorage.getItem('token')")
        sys.exit(1)
    
    token = sys.argv[1]
    
    if not BASE_DIR.exists():
        print(f"❌ Базовая папка не найдена: {BASE_DIR}")
        print(f"   Текущая директория: {os.getcwd()}")
        sys.exit(1)
    
    print("="*70)
    print("АВТОМАТИЧЕСКОЕ СОЗДАНИЕ ВСЕХ ЗАНЯТИЙ")
    print("="*70)
    print(f"Будет обработано {len(LESSON_INFO)} занятий")
    
    # Обрабатываем все занятия в порядке номеров
    lesson_keys = [" водное занятие"] + [str(i) for i in range(10)]
    
    results = {'success': 0, 'failed': 0}
    
    for lesson_key in lesson_keys:
        if process_lesson(lesson_key, token):
            results['success'] += 1
        else:
            results['failed'] += 1
    
    print("\n" + "="*70)
    print("РЕЗУЛЬТАТЫ")
    print("="*70)
    print(f"✅ Успешно создано: {results['success']}")
    print(f"❌ Ошибок: {results['failed']}")
    print(f"\nВсе занятия доступны в админ-панели для редактирования")

if __name__ == "__main__":
    main()
