#!/usr/bin/env python3
"""
Создание вводного занятия с правильным парсингом всех текстовых файлов
"""
import sys
import requests
import re
from pathlib import Path
from datetime import datetime
import uuid

BACKEND_URL = "http://localhost:8000"
BASE_DIR = Path("файлы для запуска/NumerOM запуск курса/ водное занятие/для сайта вводное занятие")
LESSON_ID = "lesson_intro_numbers"  # Фиксированный ID чтобы избежать дубликатов

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

def check_lesson_exists(lesson_id, token):
    """Проверяет, существует ли урок"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f"{BACKEND_URL}/api/admin/lessons/{lesson_id}",
        headers=headers
    )
    return response.status_code == 200

def read_file_content(file_path):
    """Читает содержимое файла"""
    if not file_path.exists():
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Ошибка чтения файла {file_path}: {e}")
        return None

def parse_theory(content):
    """Парсит теорию из файла и структурирует согласно проекту"""
    if not content:
        return {}
    
    # Разделяем на секции по заголовкам
    sections = {}
    current_section = None
    current_text = []
    
    lines = content.split('\n')
    prev_was_separator = False
    
    for line in lines:
        original_line = line
        line = line.strip()
        
        # Отслеживаем разделители
        is_separator = line.startswith('──') or line.startswith('─')
        
        # Если это разделитель, отмечаем и пропускаем
        if is_separator:
            prev_was_separator = True
            continue
        
        # Если после разделителя идет текст ВСЕМИ ЗАГЛАВНЫМИ - это заголовок секции
        if prev_was_separator and line.isupper() and len(line) > 5:
            # Сохраняем предыдущую секцию
            if current_section and current_text:
                sections[current_section] = '\n'.join(current_text).strip()
            # Новая секция
            current_section = line
            current_text = []
            prev_was_separator = False
        elif line.isupper() and len(line) > 10 and not line.startswith('ФАЙЛЫ') and not current_section:
            # Заголовок без разделителя перед ним
            if current_section and current_text:
                sections[current_section] = '\n'.join(current_text).strip()
            current_section = line
            current_text = []
        elif line and current_section:
            # Добавляем текст к текущей секции
            current_text.append(line)
            prev_was_separator = False
        elif line and not current_section:
            # Текст до первой секции - это введение/заголовок
            if 'introduction' not in sections:
                sections['introduction'] = []
            sections['introduction'].append(line)
            prev_was_separator = False
        else:
            prev_was_separator = False
    
    # Сохраняем последнюю секцию
    if current_section and current_text:
        sections[current_section] = '\n'.join(current_text).strip()
    
    # Обрабатываем introduction
    if 'introduction' in sections and isinstance(sections['introduction'], list):
        sections['introduction'] = '\n'.join(sections['introduction']).strip()
    
    # Маппинг секций на поля структуры для НЕ первого урока
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
    
    # Если what_is_topic пустое, пытаемся взять из introduction
    if not theory_structure['what_is_topic']:
        intro_text = sections.get('introduction', '')
        if intro_text:
            theory_structure['what_is_topic'] = intro_text[:500].strip()
        elif sections.get('ВВЕДЕНИЕ'):
            # Попробуем ещё раз получить ВВЕДЕНИЕ
            theory_structure['what_is_topic'] = sections.get('ВВЕДЕНИЕ', '').strip()
    
    # Отладочная информация
    if not theory_structure['what_is_topic']:
        print(f"   ⚠️  ВВЕДЕНИЕ не найдено. Доступные секции: {list(sections.keys())}")
    
    # Добавляем full_text для совместимости
    theory_structure['full_text'] = content
    
    return theory_structure

def parse_exercises(content):
    """Парсит упражнения из файла - улучшенная версия"""
    if not content:
        return []
    
    exercises = []
    lines = content.split('\n')
    
    current_exercise = {}
    current_section = None  # 'title', 'type', 'content', 'instructions', 'outcome'
    current_text = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Пропускаем пустые строки и разделители
        if not line or line.startswith('─') or line.startswith('РАЗДЕЛ') or line.startswith('УРОК') or line.startswith('ФАЙЛЫ'):
            if line.startswith('ФАЙЛЫ'):
                break
            i += 1
            continue
        
        # Начало нового упражнения (номер с точкой в начале строки)
        # Формат: "1. " или "1. Название: ..." или просто "1. Название"
        match = re.match(r'^(\d+)\.\s*(.*)$', line)
        if match:
            # Сохраняем предыдущее упражнение
            if current_exercise and current_exercise.get('title'):
                # Завершаем последнее поле
                if current_section == 'content':
                    current_exercise['content'] = '\n'.join(current_text).strip()
                elif current_section == 'instructions':
                    current_exercise['instructions'] = [t.strip() for t in current_text if t.strip()]
                elif current_section == 'outcome':
                    current_exercise['expected_outcome'] = '\n'.join(current_text).strip()
                
                exercises.append(current_exercise)
            
            # Начинаем новое упражнение
            rest = match.group(2).strip()
            if rest.startswith('Название:'):
                title = rest.replace('Название:', '').strip()
            else:
                title = rest if rest else f'Упражнение {match.group(1)}'
            
            current_exercise = {
                'id': f'exercise_{len(exercises) + 1}',
                'title': title,
                'type': 'practical',  # По умолчанию
                'content': '',
                'instructions': [],
                'expected_outcome': ''
            }
            current_section = None
            current_text = []
        
        # Определяем тип упражнения
        elif 'Тип:' in line and current_exercise:
            exercise_type = line.replace('Тип:', '').strip()
            type_map = {
                'Нумерологический расчёт': 'calculation',
                'Расчёт и интерпретация': 'calculation',
                'Аналитический расчёт': 'calculation',
                'Энергетическая практика': 'practice',
                'Психологическая практика': 'reflection',
                'Практическое упражнение': 'practical',
                'Практическая работа': 'practical',
                'Духовная практика': 'practice',
                'Рефлексия': 'reflection',
                'Медитативное упражнение': 'meditation',
                'Ежедневная практика': 'practice'
            }
            # Проверяем по ключевым словам
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
                current_exercise['type'] = type_map.get(exercise_type, 'practical')
        
        # Секция "Содержание:"
        elif 'Содержание:' in line and current_exercise:
            if current_section == 'instructions':
                current_exercise['instructions'] = [t.strip() for t in current_text if t.strip()]
            elif current_section == 'outcome':
                current_exercise['expected_outcome'] = '\n'.join(current_text).strip()
            current_section = 'content'
            current_text = []
        
        # Секция "Инструкция:" или "Инструкции:"
        elif ('Инструкция:' in line or 'Инструкции:' in line) and current_exercise:
            if current_section == 'content':
                current_exercise['content'] = '\n'.join(current_text).strip()
            elif current_section == 'outcome':
                current_exercise['expected_outcome'] = '\n'.join(current_text).strip()
            current_section = 'instructions'
            current_text = []
            # Пропускаем эту строку - следующая будет первой инструкцией
            i += 1
            continue
        
        # Секция "Ожидаемый результат:"
        elif 'Ожидаемый результат:' in line and current_exercise:
            if current_section == 'content':
                current_exercise['content'] = '\n'.join(current_text).strip()
            elif current_section == 'instructions':
                # Обрабатываем инструкции - убираем номера вида "1)", "2)", "1.", "2."
                instructions_raw = [t.strip() for t in current_text if t.strip()]
                instructions_clean = []
                for inst in instructions_raw:
                    # Убираем номера в начале строки: "1) ", "2) ", "1. ", "2. "
                    inst_clean = re.sub(r'^\d+[)\.]\s*', '', inst).strip()
                    if inst_clean:
                        instructions_clean.append(inst_clean)
                current_exercise['instructions'] = instructions_clean
            current_section = 'outcome'
            # Извлекаем текст после "Ожидаемый результат:"
            rest = line.split('Ожидаемый результат:')[1].strip()
            if rest:
                current_text = [rest]
            else:
                current_text = []
        
        # Обычный текст - добавляем в текущую секцию
        elif line and current_exercise:
            current_text.append(line)
        
        i += 1
    
    # Сохраняем последнее упражнение
    if current_exercise and current_exercise.get('title'):
        if current_section == 'content':
            current_exercise['content'] = '\n'.join(current_text).strip()
        elif current_section == 'instructions':
            # Обрабатываем инструкции - убираем номера вида "1)", "2)", "1.", "2."
            instructions_raw = [t.strip() for t in current_text if t.strip()]
            instructions_clean = []
            for inst in instructions_raw:
                # Убираем номера в начале строки: "1) ", "2) ", "1. ", "2. "
                inst_clean = re.sub(r'^\d+[)\.]\s*', '', inst).strip()
                if inst_clean:
                    instructions_clean.append(inst_clean)
            current_exercise['instructions'] = instructions_clean
        elif current_section == 'outcome':
            current_exercise['expected_outcome'] = '\n'.join(current_text).strip()
        
        exercises.append(current_exercise)
    
    return exercises

def parse_quiz(content):
    """Парсит тест из файла (используем улучшенную логику)"""
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
        
        # Ищем блок с ответами
        if line.startswith('ОТВЕТЫ:'):
            answers_text = '\n'.join(lines[i:]).strip()
            break
        
        # Проверяем начало вопроса (формат: "1. Текст вопроса")
        match = re.match(r'^(\d+)\.\s+(.+)$', line)
        if match:
            # Сохраняем предыдущий вопрос
            if current_question:
                current_question['options'] = current_options
                questions.append(current_question)
            
            # Начинаем новый вопрос
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
        
        # Собираем варианты ответов (формат: "A. Вариант")
        elif collecting_options and re.match(r'^[A-E]\.', line):
            option = line[2:].strip()  # Убираем "A. "
            current_options.append(option)
        
        # Проверяем, закончились ли варианты
        elif collecting_options and line and not re.match(r'^[A-E]\.', line):
            collecting_options = False
    
    # Сохраняем последний вопрос
    if current_question:
        current_question['options'] = current_options
        questions.append(current_question)
    
    # Парсим правильные ответы
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
        'id': 'quiz_intro',
        'title': 'Тест: Вводное занятие',
        'questions': questions,
        'passing_score': 70
    }

def parse_challenge(content):
    """Парсит челлендж на 7 дней"""
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
        
        # Проверяем начало нового дня
        day_found = False
        for day_name in day_names:
            if line.startswith(day_name) or f' {day_name}' in line:
                # Сохраняем предыдущий день
                if current_day:
                    current_day['tasks'] = current_tasks
                    days.append(current_day)
                
                # Начинаем новый день
                current_day = {
                    'day_number': len(days) + 1,
                    'title': line,
                    'tasks': []
                }
                current_tasks = []
                collecting_tasks = True
                day_found = True
                break
        
        # Собираем задачи дня
        if collecting_tasks and re.match(r'^\d+\.', line) and not day_found:
            task = line[2:].strip()  # Убираем "1. "
            current_tasks.append(task)
    
    # Сохраняем последний день
    if current_day:
        current_day['tasks'] = current_tasks
        days.append(current_day)
    
    if not days:
        return None
    
    return {
        'id': 'challenge_intro_7days',
        'title': '7-дневный челлендж',
        'description': 'Ежедневные практики для знакомства с нумерологией',
        'duration_days': len(days),
        'daily_tasks': days
    }

def upload_pdf(file_path, token):
    """Загружает PDF файл"""
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/pdf')}
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.post(
                f"{BACKEND_URL}/api/admin/consultations/upload-pdf",
                files=files,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"   ❌ Ошибка загрузки PDF: {response.status_code}")
                return None
    except Exception as e:
        print(f"   ❌ Исключение при загрузке PDF: {str(e)}")
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
        print(f"   ❌ Ошибка создания урока: {response.status_code}")
        print(f"   Ответ: {response.text[:300]}")
        return False

def update_lesson(lesson_id, lesson_data, token):
    """Обновляет существующий урок через API"""
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    response = requests.put(
        f"{BACKEND_URL}/api/admin/lessons/{lesson_id}",
        json=lesson_data,
        headers=headers
    )
    
    if response.status_code == 200:
        return True
    else:
        print(f"   ❌ Ошибка обновления урока: {response.status_code}")
        print(f"   Ответ: {response.text[:300]}")
        return False

def main():
    print("="*70)
    print("СОЗДАНИЕ ВВОДНОГО ЗАНЯТИЯ")
    print("="*70)
    
    # Получаем токен
    token = get_admin_token()
    if not token:
        print("❌ Не удалось получить токен администратора")
        return
    
    # Проверяем наличие папки
    if not BASE_DIR.exists():
        print(f"❌ Папка не найдена: {BASE_DIR}")
        return
    
    print(f"\n📁 Папка: {BASE_DIR.name}")
    
    # Проверяем, существует ли уже урок
    lesson_exists = check_lesson_exists(LESSON_ID, token)
    if lesson_exists:
        print(f"⚠️  Урок с ID '{LESSON_ID}' уже существует. Будет обновлен.")
    
    # Находим файлы
    theory_file = BASE_DIR / "Урок_Введение_Теория.txt"
    exercises_file = BASE_DIR / "Урок_Введение_Упражнения.txt"
    test_file = BASE_DIR / "Урок_Введение_Тест.txt"
    challenge_file = BASE_DIR / "Урок_Введение_Челлендж.txt"
    pdf_files = list(BASE_DIR.glob("*.pdf"))
    
    # Читаем файлы
    print("\n📖 Чтение файлов...")
    theory_content = read_file_content(theory_file)
    exercises_content = read_file_content(exercises_file)
    test_content = read_file_content(test_file)
    challenge_content = read_file_content(challenge_file)
    
    print(f"   Теория: {'✓' if theory_content else '✗'}")
    print(f"   Упражнения: {'✓' if exercises_content else '✗'}")
    print(f"   Тест: {'✓' if test_content else '✗'}")
    print(f"   Челлендж: {'✓' if challenge_content else '✗'}")
    
    # Парсим контент
    print("\n🔍 Парсинг контента...")
    theory = parse_theory(theory_content)
    exercises = parse_exercises(exercises_content)
    quiz = parse_quiz(test_content)
    challenge = parse_challenge(challenge_content)
    
    print(f"   Упражнений распознано: {len(exercises)}")
    for i, ex in enumerate(exercises[:3], 1):
        print(f"     {i}. {ex.get('title', 'N/A')} ({ex.get('type', 'N/A')})")
    print(f"   Вопросов в тесте: {len(quiz['questions']) if quiz else 0}")
    print(f"   Дней челленджа: {challenge['duration_days'] if challenge else 0}")
    
    # Загружаем PDF если есть
    pdf_file_id = None
    pdf_filename = None
    if pdf_files:
        print(f"\n📎 PDF файлов найдено: {len(pdf_files)}")
        pdf_result = upload_pdf(pdf_files[0], token)
        if pdf_result:
            pdf_file_id = pdf_result.get('file_id')
            pdf_filename = pdf_result.get('filename')
            print(f"   ✅ PDF загружен: {pdf_filename}")
    
    # Формируем данные урока
    lesson_data = {
        'id': LESSON_ID,
        'title': 'Вводное занятие: Язык чисел',
        'module': 'Модуль 0: Введение',
        'description': 'Знакомство с нумерологией, языком энергии чисел и основными концепциями системы NumerOM',
        'content': {
            'theory': theory
        },
        'exercises': exercises,
        'quiz': quiz,
        'challenges': [challenge] if challenge else [],
        'points_required': 0,
        'is_active': True,
        'level': 0,
        'order': 0
    }
    
    # Добавляем PDF если загружен
    if pdf_file_id:
        lesson_data['pdf_file_id'] = pdf_file_id
        lesson_data['pdf_filename'] = pdf_filename
    
    # Создаем или обновляем урок
    print(f"\n📚 {'Обновление' if lesson_exists else 'Создание'} урока...")
    if lesson_exists:
        success = update_lesson(LESSON_ID, lesson_data, token)
    else:
        success = create_lesson(lesson_data, token)
    
    if success:
        action = 'обновлен' if lesson_exists else 'создан'
        print(f"✅ Урок успешно {action}!")
        print(f"   ID: {LESSON_ID}")
        print(f"   Название: {lesson_data['title']}")
        print(f"   Упражнений: {len(exercises)}")
        print(f"   Вопросов в тесте: {len(quiz['questions']) if quiz else 0}")
        print(f"   Челленджей: {len(lesson_data['challenges'])}")
    else:
        print("❌ Не удалось создать/обновить урок")

if __name__ == "__main__":
    main()
