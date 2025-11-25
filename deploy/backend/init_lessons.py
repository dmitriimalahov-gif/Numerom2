#!/usr/bin/env python3
"""
Скрипт инициализации уроков при запуске backend в Docker
Автоматически создает все уроки из файлов для запуска
"""
import os
import sys
import requests
import re
import time
from pathlib import Path
from datetime import datetime
import uuid

# URL backend внутри Docker сети (используем localhost, так как скрипт запускается в том же контейнере)
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
BASE_DIR = Path("/app/lesson_files/NumerOM запуск курса")  # Путь к файлам в контейнере

# Порядок создания занятий: вводное, 1-9, затем 0
LESSON_ORDER = [
    (" водное занятие", "lesson_intro_numbers", "Вводное занятие: Язык чисел", "Модуль 0: Введение", 0, 0),
    ("1", "lesson_1_surya", "Урок 1: СУРЬЯ (Солнце) - Число 1", "Модуль 1: Основы", 1, 1),
    ("2", "lesson_2_chandra", "Урок 2: ЧАНДРА (Луна) - Число 2", "Модуль 1: Основы", 1, 2),
    ("3", "lesson_3_guru", "Урок 3: ГУРУ (Юпитер) - Число 3", "Модуль 1: Основы", 1, 3),
    ("4", "lesson_4_rahu", "Урок 4: РАХУ - Число 4", "Модуль 2: Продвинутый", 2, 4),
    ("5", "lesson_5_buddhi", "Урок 5: БУДДХИ (Меркурий) - Число 5", "Модуль 2: Продвинутый", 2, 5),
    ("6", "lesson_6_shukra", "Урок 6: ШУКРА (Венера) - Число 6", "Модуль 2: Продвинутый", 2, 6),
    ("7", "lesson_7_ketu", "Урок 7: КЕТУ - Число 7", "Модуль 3: Продвинутый", 3, 7),
    ("8", "lesson_8_shani", "Урок 8: ШАНИ (Сатурн) - Число 8", "Модуль 3: Продвинутый", 3, 8),
    ("9", "lesson_9_mangal", "Урок 9: МАНГАЛ (Марс) - Число 9", "Модуль 3: Продвинутый", 3, 9),
    ("0", "lesson_0_problem", "Урок 0: Число проблемы", "Модуль 0: Введение", 0, 10),
]

SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"

def wait_for_backend(max_retries=30, retry_interval=2):
    """Ждет пока backend станет доступен"""
    for i in range(max_retries):
        try:
            response = requests.get(f"{BACKEND_URL}/docs", timeout=2)
            if response.status_code == 200:
                print(f"✅ Backend доступен на {BACKEND_URL}")
                return True
        except Exception as e:
            if i < max_retries - 1:
                print(f"⏳ Ожидание backend... ({i+1}/{max_retries})")
                time.sleep(retry_interval)
            else:
                print(f"❌ Backend недоступен: {e}")
                return False
    return False

def get_admin_token():
    """Получает токен администратора"""
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/auth/login",
                json={
                    "email": SUPER_ADMIN_EMAIL,
                    "password": SUPER_ADMIN_PASSWORD
                },
                timeout=10
            )
            if response.status_code == 200:
                token = response.json().get('access_token')
                if token:
                    print(f"✅ Получен токен администратора")
                    return token
        except Exception as e:
            if i < max_retries - 1:
                print(f"⏳ Повторная попытка получения токена... ({i+1}/{max_retries})")
                time.sleep(2)
            else:
                print(f"❌ Ошибка получения токена: {e}")
                return None
    return None

def check_lesson_exists(lesson_id, token):
    """Проверяет существует ли урок"""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(
            f"{BACKEND_URL}/api/admin/lessons/{lesson_id}",
            headers=headers,
            timeout=10
        )
        return response.status_code == 200
    except:
        return False

def find_lesson_folder(lesson_key):
    """Находит папку с материалами урока"""
    lesson_dir = BASE_DIR / lesson_key
    
    if not lesson_dir.exists():
        print(f"   ⚠️  Папка {lesson_key} не найдена в {BASE_DIR}")
        return None
    
    # Ищем подпапку "для сайта" с текстовыми файлами (рекурсивно)
    best_folder = None
    max_txt_count = 0
    
    for subdir in lesson_dir.rglob("*"):
        if subdir.is_dir() and ('сайт' in subdir.name.lower() or 'site' in subdir.name.lower()):
            txt_files = list(subdir.glob("*.txt"))
            if len(txt_files) > max_txt_count:
                max_txt_count = len(txt_files)
                best_folder = subdir
    
    if best_folder and max_txt_count > 0:
        return best_folder
    
    # Если не нашли подпапку, проверяем саму папку и все её подпапки
    txt_files = list(lesson_dir.rglob("*.txt"))
    if txt_files:
        folder_counts = {}
        for txt_file in txt_files:
            folder = txt_file.parent
            folder_counts[str(folder)] = folder_counts.get(str(folder), 0) + 1
        
        if folder_counts:
            best_folder_path = max(folder_counts.items(), key=lambda x: x[1])[0]
            return Path(best_folder_path)
    
    return lesson_dir

def find_lesson_files(lesson_folder):
    """Находит все файлы урока"""
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
        
        name_lower = file_path.name.lower()
        
        if 'теори' in name_lower and file_path.suffix == '.txt':
            files['theory'] = file_path
        elif 'упражн' in name_lower and file_path.suffix == '.txt':
            files['exercises'] = file_path
        elif 'тест' in name_lower and file_path.suffix == '.txt':
            files['test'] = file_path
        elif 'челлендж' in name_lower and file_path.suffix == '.txt':
            files['challenge'] = file_path
        elif file_path.suffix == '.pdf':
            files['pdfs'].append(file_path)
        elif file_path.suffix in ['.doc', '.docx']:
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
        print(f"      ⚠️  Ошибка чтения {file_path}: {e}")
        return None

# Импортируем функции парсинга из create_intro_lesson_improved.py
# Для упрощения, скопируем основные функции парсинга
def parse_theory(content):
    """Парсит теорию из файла"""
    if not content:
        return {}
    
    sections = {}
    current_section = None
    current_text = []
    prev_was_separator = False
    
    lines = content.split('\n')
    
    for line in lines:
        original_line = line
        line = line.strip()
        
        is_separator = line.startswith('──') or line.startswith('─')
        
        if is_separator:
            prev_was_separator = True
            continue
        
        if prev_was_separator and line.isupper() and len(line) > 5:
            if current_section and current_text:
                sections[current_section] = '\n'.join(current_text).strip()
            current_section = line
            current_text = []
            prev_was_separator = False
        elif line.isupper() and len(line) > 10 and not line.startswith('ФАЙЛЫ') and not current_section:
            if current_section and current_text:
                sections[current_section] = '\n'.join(current_text).strip()
            current_section = line
            current_text = []
        elif line and current_section:
            current_text.append(line)
            prev_was_separator = False
        elif line and not current_section:
            if 'introduction' not in sections:
                sections['introduction'] = []
            sections['introduction'].append(line)
            prev_was_separator = False
        else:
            prev_was_separator = False
    
    if current_section and current_text:
        sections[current_section] = '\n'.join(current_text).strip()
    
    if 'introduction' in sections and isinstance(sections['introduction'], list):
        sections['introduction'] = '\n'.join(sections['introduction']).strip()
    
    theory_structure = {
        'what_is_topic': sections.get('ВВЕДЕНИЕ', '').strip() if sections.get('ВВЕДЕНИЕ') else '',
        'main_story': '\n\n'.join(filter(None, [
            sections.get('СМЫСЛ НУМЕРОЛОГИИ', ''),
            sections.get('ПЛАНЕТАРНЫЙ КОД 1–9', ''),
            sections.get('ЗАЧЕМ ЭТО НУЖНО', '')
        ])).strip(),
        'key_concepts': sections.get('ПЛАНЕТАРНЫЙ КОД 1–9', '').strip() if sections.get('ПЛАНЕТАРНЫЙ КОД 1–9') else '',
        'practical_applications': '\n\n'.join(filter(None, [
            sections.get('ПРАКТИЧЕСКОЕ ПРИМЕНЕНИЕ', ''),
            sections.get('ПЕРВЫЙ ШАГ', ''),
            sections.get('ФИЛОСОФИЯ УЧЕНИЯ', '')
        ])).strip()
    }
    
    if not theory_structure['what_is_topic']:
        intro_text = sections.get('introduction', '')
        if intro_text:
            theory_structure['what_is_topic'] = intro_text[:500].strip()
        elif sections.get('ВВЕДЕНИЕ'):
            theory_structure['what_is_topic'] = sections.get('ВВЕДЕНИЕ', '').strip()
    
    theory_structure['full_text'] = content
    
    return theory_structure

def parse_exercises(content):
    """Парсит упражнения из файла"""
    if not content:
        return []
    
    exercises = []
    lines = content.split('\n')
    current_exercise = {}
    current_section = None
    current_text = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line or line.startswith('─') or line.startswith('РАЗДЕЛ') or line.startswith('УРОК') or line.startswith('ФАЙЛЫ'):
            if line.startswith('ФАЙЛЫ'):
                break
            i += 1
            continue
        
        match = re.match(r'^(\d+)\.\s*(.*)$', line)
        if match:
            if current_exercise and current_exercise.get('title'):
                if current_section == 'content':
                    current_exercise['content'] = '\n'.join(current_text).strip()
                elif current_section == 'instructions':
                    instructions_raw = [t.strip() for t in current_text if t.strip()]
                    instructions_clean = []
                    for inst in instructions_raw:
                        inst_clean = re.sub(r'^\d+[)\.]\s*', '', inst).strip()
                        if inst_clean:
                            instructions_clean.append(inst_clean)
                    current_exercise['instructions'] = instructions_clean
                elif current_section == 'outcome':
                    current_exercise['expected_outcome'] = '\n'.join(current_text).strip()
                
                exercises.append(current_exercise)
            
            rest = match.group(2).strip()
            if rest.startswith('Название:'):
                title = rest.replace('Название:', '').strip()
            else:
                title = rest if rest else f'Упражнение {match.group(1)}'
            
            current_exercise = {
                'id': f'exercise_{len(exercises) + 1}',
                'title': title,
                'type': 'practical',
                'content': '',
                'instructions': [],
                'expected_outcome': ''
            }
            current_section = None
            current_text = []
        
        elif 'Тип:' in line and current_exercise:
            exercise_type = line.replace('Тип:', '').strip()
            exercise_type_lower = exercise_type.lower()
            if 'медитатив' in exercise_type_lower:
                current_exercise['type'] = 'meditation'
            elif 'рефлекси' in exercise_type_lower:
                current_exercise['type'] = 'reflection'
            elif 'расчёт' in exercise_type_lower or 'расчет' in exercise_type_lower:
                current_exercise['type'] = 'calculation'
            elif 'практическ' in exercise_type_lower or 'практика' in exercise_type_lower:
                current_exercise['type'] = 'practice' if 'энергетическ' in exercise_type_lower else 'practical'
        
        elif 'Содержание:' in line and current_exercise:
            if current_section == 'instructions':
                instructions_raw = [t.strip() for t in current_text if t.strip()]
                instructions_clean = []
                for inst in instructions_raw:
                    inst_clean = re.sub(r'^\d+[)\.]\s*', '', inst).strip()
                    if inst_clean:
                        instructions_clean.append(inst_clean)
                current_exercise['instructions'] = instructions_clean
            elif current_section == 'outcome':
                current_exercise['expected_outcome'] = '\n'.join(current_text).strip()
            current_section = 'content'
            current_text = []
        
        elif ('Инструкция:' in line or 'Инструкции:' in line) and current_exercise:
            if current_section == 'content':
                current_exercise['content'] = '\n'.join(current_text).strip()
            elif current_section == 'outcome':
                current_exercise['expected_outcome'] = '\n'.join(current_text).strip()
            current_section = 'instructions'
            current_text = []
            i += 1
            continue
        
        elif 'Ожидаемый результат:' in line and current_exercise:
            if current_section == 'content':
                current_exercise['content'] = '\n'.join(current_text).strip()
            elif current_section == 'instructions':
                instructions_raw = [t.strip() for t in current_text if t.strip()]
                instructions_clean = []
                for inst in instructions_raw:
                    inst_clean = re.sub(r'^\d+[)\.]\s*', '', inst).strip()
                    if inst_clean:
                        instructions_clean.append(inst_clean)
                current_exercise['instructions'] = instructions_clean
            current_section = 'outcome'
            rest = line.split('Ожидаемый результат:')[1].strip()
            if rest:
                current_text = [rest]
            else:
                current_text = []
        
        elif line and current_exercise:
            current_text.append(line)
        
        i += 1
    
    if current_exercise and current_exercise.get('title'):
        if current_section == 'content':
            current_exercise['content'] = '\n'.join(current_text).strip()
        elif current_section == 'instructions':
            instructions_raw = [t.strip() for t in current_text if t.strip()]
            instructions_clean = []
            for inst in instructions_raw:
                inst_clean = re.sub(r'^\d+[)\.]\s*', '', inst).strip()
                if inst_clean:
                    instructions_clean.append(inst_clean)
            current_exercise['instructions'] = instructions_clean
        elif current_section == 'outcome':
            current_exercise['expected_outcome'] = '\n'.join(current_text).strip()
        
        exercises.append(current_exercise)
    
    return exercises

def parse_quiz(content):
    """Парсит тест из файла"""
    if not content:
        return None
    
    lines = content.split('\n')
    questions = []
    current_question = None
    current_options = []
    collecting_options = False
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # Начало вопроса (номер с точкой)
        match = re.match(r'^(\d+)\.\s*(.*)$', line)
        if match:
            if current_question:
                current_question['options'] = current_options
                questions.append(current_question)
            
            question_text = match.group(2).strip()
            current_question = {
                'id': f'question_{len(questions) + 1}',
                'question': question_text,
                'options': [],
                'correct_answer': None
            }
            current_options = []
            collecting_options = True
        elif collecting_options and line.startswith(('а)', 'б)', 'в)', 'г)', 'a)', 'b)', 'c)', 'd)')):
            option_text = re.sub(r'^[а-яa-z]\)\s*', '', line).strip()
            current_options.append(option_text)
            
            # Проверяем следующий элемент на правильный ответ
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if 'правил' in next_line.lower() or 'ответ' in next_line.lower():
                    current_question['correct_answer'] = len(current_options) - 1
                    i += 1
        elif collecting_options and line:
            # Если это не вариант ответа, возможно это продолжение вопроса
            if current_question:
                current_question['question'] += ' ' + line
        
        i += 1
    
    if current_question:
        current_question['options'] = current_options
        questions.append(current_question)
    
    if questions:
        return {
            'id': 'quiz_1',
            'title': 'Тест по уроку',
            'questions': questions,
            'passing_score': 70
        }
    
    return None

def parse_challenge(content):
    """Парсит челлендж из файла"""
    if not content:
        return None
    
    lines = content.split('\n')
    days = []
    current_day = None
    current_tasks = []
    collecting_tasks = False
    
    day_names = ['День 1', 'День 2', 'День 3', 'День 4', 'День 5', 'День 6', 'День 7']
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        day_found = False
        for day_name in day_names:
            if line.startswith(day_name):
                if current_day:
                    current_day['tasks'] = current_tasks
                    days.append(current_day)
                
                current_day = {
                    'day_number': len(days) + 1,
                    'title': line,
                    'tasks': []
                }
                current_tasks = []
                collecting_tasks = True
                day_found = True
                break
        
        if collecting_tasks and re.match(r'^\d+\.', line) and not day_found:
            task = line[2:].strip()
            current_tasks.append(task)
    
    if current_day:
        current_day['tasks'] = current_tasks
        days.append(current_day)
    
    if days:
        return {
            'id': 'challenge_1',
            'title': 'Челлендж на 7 дней',
            'description': 'Выполняйте задания каждый день в течение недели',
            'duration_days': len(days),
            'daily_tasks': days
        }
    
    return None

def upload_file(file_path, file_type, token):
    """Загружает файл через API"""
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
            files = {'file': (file_path.name, f, content_type)}
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.post(endpoint, files=files, headers=headers, timeout=60)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
    except Exception as e:
        return None

def create_lesson(lesson_data, token):
    """Создает урок через API"""
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    response = requests.post(
        f"{BACKEND_URL}/api/admin/lessons/create",
        json=lesson_data,
        headers=headers,
        timeout=30
    )
    return response.status_code in [200, 201]

def main():
    print("="*70)
    print("ИНИЦИАЛИЗАЦИЯ УРОКОВ ПРИ ЗАПУСКЕ BACKEND")
    print("="*70)
    
    # Проверяем наличие файлов
    if not BASE_DIR.exists():
        print(f"⚠️  Директория {BASE_DIR} не найдена")
        print("   Уроки не будут созданы автоматически")
        print("   Чтобы включить автоматическое создание, смонтируйте файлы в docker-compose.yml")
        return
    
    # Ждем пока backend станет доступен
    if not wait_for_backend():
        print("❌ Не удалось подключиться к backend")
        return
    
    # Получаем токен
    token = get_admin_token()
    if not token:
        print("❌ Не удалось получить токен администратора")
        return
    
    print(f"\n📚 Начинаем создание уроков...")
    print(f"   Базовая директория: {BASE_DIR}")
    
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    for lesson_key, lesson_id, title, module, level, order in LESSON_ORDER:
        print(f"\n📖 Обработка: {title}")
        
        # Проверяем существует ли урок
        if check_lesson_exists(lesson_id, token):
            print(f"   ⏭️  Урок уже существует, пропускаем")
            skipped_count += 1
            continue
        
        # Находим папку и файлы
        lesson_folder = find_lesson_folder(lesson_key)
        if not lesson_folder:
            print(f"   ⚠️  Материалы не найдены, пропускаем")
            skipped_count += 1
            continue
        
        files = find_lesson_files(lesson_folder)
        
        # Парсим контент
        theory_content = read_file_content(files['theory'])
        exercises_content = read_file_content(files['exercises'])
        quiz_content = read_file_content(files['test'])
        challenge_content = read_file_content(files['challenge'])
        
        # Создаем структуру урока
        lesson_data = {
            'id': lesson_id,
            'title': title,
            'module': module,
            'level': level,
            'order': order,
            'is_active': True,
            'content': {
                'theory': parse_theory(theory_content) if theory_content else {}
            },
            'exercises': parse_exercises(exercises_content) if exercises_content else [],
            'quiz': parse_quiz(quiz_content) if quiz_content else None,
            'challenges': [parse_challenge(challenge_content)] if challenge_content and parse_challenge(challenge_content) else []
        }
        
        # Загружаем медиафайлы
        if files['pdfs']:
            pdf_file = files['pdfs'][0]  # Берем первый PDF
            pdf_result = upload_file(pdf_file, 'pdf', token)
            if pdf_result:
                lesson_data['pdf_file_id'] = pdf_result.get('file_id')
                lesson_data['pdf_filename'] = pdf_result.get('filename')
                print(f"   ✅ PDF загружен: {pdf_file.name}")
        
        if files['word_files']:
            word_file = files['word_files'][0]  # Берем первый Word
            word_result = upload_file(word_file, 'word', token)
            if word_result:
                lesson_data['word_file_id'] = word_result.get('file_id')
                lesson_data['word_filename'] = word_result.get('filename')
                print(f"   ✅ Word загружен: {word_file.name}")
        
        # Создаем урок
        if create_lesson(lesson_data, token):
            print(f"   ✅ Урок создан: {title}")
            created_count += 1
        else:
            print(f"   ❌ Ошибка создания урока: {title}")
            error_count += 1
        
        # Небольшая задержка между уроками
        time.sleep(1)
    
    print("\n" + "="*70)
    print("РЕЗУЛЬТАТЫ ИНИЦИАЛИЗАЦИИ")
    print("="*70)
    print(f"✅ Создано: {created_count}")
    print(f"⏭️  Пропущено (уже существуют): {skipped_count}")
    print(f"❌ Ошибок: {error_count}")
    print("="*70)

if __name__ == "__main__":
    main()

