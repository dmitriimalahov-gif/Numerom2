#!/usr/bin/env python3
"""
Создание всех занятий в правильном порядке: вводное, 1-9, затем 0
Использует улучшенный парсинг из create_intro_lesson_improved.py
"""
import sys
import requests
import re
from pathlib import Path
from datetime import datetime
import uuid

BACKEND_URL = "http://localhost:8000"
BASE_DIR = Path("файлы для запуска/NumerOM запуск курса")

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

def get_admin_token():
    """Получает токен администратора"""
    response = requests.post(
        f"{BACKEND_URL}/api/auth/login",
        json={
            "email": "dmitrii.malahov@gmail.com",
            "password": "756bvy67H"
        },
        timeout=10
    )
    if response.status_code == 200:
        return response.json().get('access_token')
    return None

def find_lesson_folder(lesson_key):
    """Находит папку с материалами урока"""
    lesson_dir = BASE_DIR / lesson_key
    
    if not lesson_dir.exists():
        print(f"   ⚠️  Папка {lesson_key} не найдена")
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
    
    # Если нашли хорошую подпапку, возвращаем её
    if best_folder and max_txt_count > 0:
        return best_folder
    
    # Если не нашли подпапку, проверяем саму папку и все её подпапки
    txt_files = list(lesson_dir.rglob("*.txt"))
    if txt_files:
        # Возвращаем папку с наибольшим количеством .txt файлов
        folder_counts = {}
        for txt_file in txt_files:
            folder = txt_file.parent
            folder_counts[str(folder)] = folder_counts.get(str(folder), 0) + 1
        
        if folder_counts:
            best_folder_path = max(folder_counts.items(), key=lambda x: x[1])[0]
            return Path(best_folder_path)
    
    return lesson_dir  # Возвращаем даже если нет .txt, может быть только медиа

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
        print(f"      ⚠️  Ошибка чтения {file_path.name}: {e}")
        return None

def parse_theory(content):
    """Парсит теорию из файла"""
    if not content:
        return {}
    
    sections = {}
    current_section = None
    current_text = []
    lines = content.split('\n')
    prev_was_separator = False
    
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
            else:
                current_exercise['type'] = 'practical'
        
        elif 'Содержание:' in line and current_exercise:
            if current_section == 'instructions':
                current_exercise['instructions'] = [t.strip() for t in current_text if t.strip()]
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
    
    questions = []
    lines = content.split('\n')
    current_question = None
    current_options = []
    collecting_options = False
    answers_text = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if not line or line.startswith('──'):
            continue
        
        if line.startswith('ОТВЕТЫ:'):
            answers_text = '\n'.join(lines[i:]).strip()
            break
        
        match = re.match(r'^(\d+)\.\s+(.+)$', line)
        if match:
            if current_question:
                current_question['options'] = current_options
                questions.append(current_question)
            
            question_num = match.group(1)
            question_text = match.group(2)
            current_question = {
                'id': f'question_{question_num}',
                'question': question_text,
                'options': [],
                'correct_answer': '',
                'explanation': ''
            }
            current_options = []
            collecting_options = True
        
        elif collecting_options and re.match(r'^[A-E]\.', line):
            option = line[2:].strip()
            current_options.append(option)
        
        elif collecting_options and line and not re.match(r'^[A-E]\.', line):
            collecting_options = False
    
    if current_question:
        current_question['options'] = current_options
        questions.append(current_question)
    
    if answers_text:
        answer_pattern = r'(\d+)–([A-E])'
        answers = re.findall(answer_pattern, answers_text)
        answer_map = {q: a.lower() for q, a in answers}
        
        for q in questions:
            q_num = q['id'].split('_')[-1]
            if q_num in answer_map:
                q['correct_answer'] = answer_map[q_num]
    
    if not questions:
        return None
    
    return {
        'id': f'quiz_{uuid.uuid4().hex[:8]}',
        'title': 'Тест урока',
        'questions': questions,
        'passing_score': 70
    }

def parse_challenge(content):
    """Парсит челлендж"""
    if not content:
        return None
    
    days = []
    lines = content.split('\n')
    current_day = None
    current_tasks = []
    collecting_tasks = False
    
    day_names = ['ВОСКРЕСЕНЬЕ', 'ПОНЕДЕЛЬНИК', 'ВТОРНИК', 'СРЕДА', 'ЧЕТВЕРГ', 'ПЯТНИЦА', 'СУББОТА', 'ДЕНЬ 1', 'ДЕНЬ 2', 'ДЕНЬ 3', 'ДЕНЬ 4', 'ДЕНЬ 5', 'ДЕНЬ 6', 'ДЕНЬ 7']
    
    for line in lines:
        line = line.strip()
        
        if not line or line.startswith('──'):
            continue
        
        day_found = False
        for day_name in day_names:
            if line.startswith(day_name) or f' {day_name}' in line:
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
            files = {'file': (file_path.name, f, content_type)}
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.post(endpoint, files=files, headers=headers, timeout=60)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"      ❌ Ошибка загрузки: {response.status_code}")
                return None
    except Exception as e:
        print(f"      ❌ Исключение: {str(e)}")
        return None

def create_lesson(lesson_data, token):
    """Создает урок через API"""
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    response = requests.post(
        f"{BACKEND_URL}/api/admin/lessons/create",
        json=lesson_data,
        headers=headers
    )
    
    if response.status_code == 200:
        return True
    else:
        print(f"      ❌ Ошибка создания: {response.status_code}")
        print(f"      Ответ: {response.text[:200]}")
        return False

def process_lesson(lesson_key, lesson_id, title, module, level, order, token):
    """Обрабатывает одно занятие"""
    print(f"\n📚 Обработка: {title}")
    
    # Находим папку
    lesson_folder = find_lesson_folder(lesson_key)
    if not lesson_folder:
        print(f"   ⚠️  Пропущено (нет папки)")
        return False
    
    # Находим файлы
    files = find_lesson_files(lesson_folder)
    
    # Читаем текстовые файлы
    theory_content = read_file_content(files['theory'])
    exercises_content = read_file_content(files['exercises'])
    test_content = read_file_content(files['test'])
    challenge_content = read_file_content(files['challenge'])
    
    print(f"   📖 Теория: {'✓' if theory_content else '✗'}")
    print(f"   💪 Упражнения: {'✓' if exercises_content else '✗'}")
    print(f"   ❓ Тест: {'✓' if test_content else '✗'}")
    print(f"   🎯 Челлендж: {'✓' if challenge_content else '✗'}")
    
    # Парсим контент
    theory = parse_theory(theory_content)
    exercises = parse_exercises(exercises_content)
    quiz = parse_quiz(test_content)
    challenge = parse_challenge(challenge_content)
    
    print(f"   📝 Упражнений распознано: {len(exercises)}")
    print(f"   📝 Вопросов в тесте: {len(quiz['questions']) if quiz else 0}")
    print(f"   📝 Дней челленджа: {challenge['duration_days'] if challenge else 0}")
    
    # Загружаем медиафайлы
    pdf_file_id = None
    pdf_filename = None
    if files['pdfs']:
        print(f"   📎 PDF файлов: {len(files['pdfs'])}")
        pdf_result = upload_file(files['pdfs'][0], 'pdf', token)
        if pdf_result:
            pdf_file_id = pdf_result.get('file_id')
            pdf_filename = pdf_result.get('filename')
            print(f"      ✅ PDF загружен: {pdf_filename}")
    
    word_file_id = None
    word_filename = None
    if files['word_files']:
        print(f"   📄 Word файлов: {len(files['word_files'])}")
        word_result = upload_file(files['word_files'][0], 'word', token)
        if word_result:
            word_file_id = word_result.get('file_id')
            word_filename = word_result.get('filename')
            print(f"      ✅ Word загружен: {word_filename}")
    
    # Формируем данные урока
    lesson_data = {
        'id': lesson_id,
        'title': title,
        'module': module,
        'description': f'Урок {order}: {title}',
        'content': {
            'theory': theory
        },
        'exercises': exercises,
        'quiz': quiz,
        'challenges': [challenge] if challenge else [],
        'points_required': 0,
        'is_active': True,
        'level': level,
        'order': order
    }
    
    if pdf_file_id:
        lesson_data['pdf_file_id'] = pdf_file_id
        lesson_data['pdf_filename'] = pdf_filename
    
    if word_file_id:
        lesson_data['word_file_id'] = word_file_id
        lesson_data['word_filename'] = word_filename
    
    # Создаем урок
    if create_lesson(lesson_data, token):
        print(f"   ✅ Урок создан успешно!")
        return True
    else:
        print(f"   ❌ Ошибка создания урока")
        return False

def main():
    print("="*70)
    print("СОЗДАНИЕ ВСЕХ ЗАНЯТИЙ В ПРАВИЛЬНОМ ПОРЯДКЕ")
    print("="*70)
    
    token = get_admin_token()
    if not token:
        print("❌ Не удалось получить токен администратора")
        return
    
    success_count = 0
    failed_count = 0
    
    for lesson_key, lesson_id, title, module, level, order in LESSON_ORDER:
        if process_lesson(lesson_key, lesson_id, title, module, level, order, token):
            success_count += 1
        else:
            failed_count += 1
    
    print("\n" + "="*70)
    print("РЕЗУЛЬТАТЫ")
    print("="*70)
    print(f"✅ Создано успешно: {success_count}")
    print(f"❌ Ошибок: {failed_count}")
    print("="*70)

if __name__ == "__main__":
    main()
