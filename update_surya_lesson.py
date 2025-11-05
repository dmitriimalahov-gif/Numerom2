#!/usr/bin/env python3
"""
Обновление урока 1 (Сурья) с полным контентом из текстовых файлов
"""
import sys
import requests
import re
from pathlib import Path
from datetime import datetime
import uuid

BACKEND_URL = "http://localhost:8000"
LESSON_ID = "lesson_surya_775815a9"  # ID урока Сурья (нужно найти актуальный)

BASE_DIR = Path("файлы для запуска/NumerOM запуск курса/1/Для сайта 1")

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
    """Парсит теорию из файла"""
    if not content:
        return {}
    
    # Разделяем на секции по заголовкам
    sections = {}
    current_section = None
    current_text = []
    
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Проверяем, является ли строка заголовком секции
        if line.startswith('──') or line.startswith('─'):
            continue
        elif line.isupper() and len(line) > 10:
            # Сохраняем предыдущую секцию
            if current_section:
                sections[current_section] = '\n'.join(current_text).strip()
            # Новая секция
            current_section = line
            current_text = []
        else:
            current_text.append(line)
    
    # Сохраняем последнюю секцию
    if current_section:
        sections[current_section] = '\n'.join(current_text).strip()
    
    return {
        'introduction': sections.get('ВВЕДЕНИЕ', ''),
        'main_concepts': content  # Возвращаем весь контент как основное содержание
    }

def parse_exercises(content):
    """Парсит упражнения из файла"""
    if not content:
        return []
    
    exercises = []
    lines = content.split('\n')
    
    current_exercise = {}
    current_field = None
    current_text = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Проверяем начало нового упражнения
        if re.match(r'^\d+\.\s+Название:', line):
            # Сохраняем предыдущее упражнение
            if current_exercise and current_exercise.get('title'):
                exercises.append(current_exercise)
            
            # Начинаем новое упражнение
            title = line.replace('Название:', '').strip()
            current_exercise = {
                'id': f'exercise_{len(exercises) + 1}',
                'title': title,
                'type': 'calculation',  # По умолчанию
                'content': '',
                'instructions': [],
                'expected_outcome': ''
            }
            current_field = None
            current_text = []
        
        elif 'Тип:' in line and current_exercise:
            exercise_type = line.replace('Тип:', '').strip()
            type_map = {
                'Нумерологический расчёт': 'calculation',
                'Расчёт и интерпретация': 'calculation',
                'Аналитический расчёт': 'calculation',
                'Энергетическая практика': 'practice',
                'Психологическая практика': 'reflection',
                'Практическое упражнение': 'practical',
                'Духовная практика': 'practice'
            }
            current_exercise['type'] = type_map.get(exercise_type, 'reflection')
        
        elif 'Содержание:' in line and current_exercise:
            current_field = 'content'
            current_text = []
        
        elif 'Инструкция:' in line and current_exercise:
            # Сохраняем предыдущее поле
            if current_field == 'content':
                current_exercise['content'] = '\n'.join(current_text).strip()
            current_field = 'instructions'
            current_text = []
        
        elif 'Интерпретация:' in line and current_exercise:
            if current_field == 'content':
                current_exercise['content'] = '\n'.join(current_text).strip()
            current_field = 'content'  # Интерпретация тоже идет в content
            current_text = []
        
        elif 'Ожидаемый результат:' in line and current_exercise:
            # Сохраняем предыдущее поле
            if current_field == 'content':
                current_exercise['content'] = '\n'.join(current_text).strip()
            elif current_field == 'instructions':
                # Разделяем инструкции по номерам или переносам строк
                instructions_text = '\n'.join(current_text).strip()
                instructions_list = []
                for inst in re.split(r'\n\d+\.', instructions_text):
                    inst = inst.strip()
                    if inst:
                        instructions_list.append(inst)
                current_exercise['instructions'] = instructions_list
            
            current_field = 'expected_outcome'
            current_text = []
        
        elif line and current_exercise:
            if current_field:
                current_text.append(line)
    
    # Сохраняем последнее поле и упражнение
    if current_exercise:
        if current_field == 'content':
            current_exercise['content'] = '\n'.join(current_text).strip()
        elif current_field == 'instructions':
            instructions_text = '\n'.join(current_text).strip()
            instructions_list = []
            for inst in re.split(r'\n\d+\.', instructions_text):
                inst = inst.strip()
                if inst:
                    instructions_list.append(inst)
            current_exercise['instructions'] = instructions_list
        elif current_field == 'expected_outcome':
            current_exercise['expected_outcome'] = '\n'.join(current_text).strip()
        
        if current_exercise.get('title'):
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
        
        # Ищем блок с ответами
        if line.startswith('ОТВЕТЫ:'):
            answers_text = '\n'.join(lines[i:]).strip()
            break
        
        # Проверяем начало вопроса
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
        
        # Собираем варианты ответов
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
        answer_map = {q: a for q, a in answers}
        
        for q in questions:
            q_num = q['id'].split('_')[-1]
            if q_num in answer_map:
                q['correct_answer'] = answer_map[q_num].lower()
    
    return {
        'id': 'quiz_surya',
        'title': 'Тест по уроку 1: Сурья (Солнце)',
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
    
    day_names = ['ВОСКРЕСЕНЬЕ', 'ПОНЕДЕЛЬНИК', 'ВТОРНИК', 'СРЕДА', 'ЧЕТВЕРГ', 'ПЯТНИЦА', 'СУББОТА']
    
    for line in lines:
        line = line.strip()
        
        if not line or line.startswith('──'):
            continue
        
        # Проверяем начало нового дня
        day_found = False
        for day_name in day_names:
            if line.startswith(day_name):
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
    
    return {
        'id': 'challenge_surya_7days',
        'title': '7 дней света и осознанности',
        'description': 'Этот челлендж раскрывает энергию Сурьи — внутренний свет, лидерство, уверенность и ясность.',
        'duration_days': 7,
        'daily_tasks': days
    }

def update_lesson(token):
    """Обновляет урок с полным контентом"""
    
    # Читаем файлы
    theory_content = read_file_content(BASE_DIR / "Урок_1_СУРЬЯ_Теория.txt")
    exercises_content = read_file_content(BASE_DIR / "Урок_1_СУРЬЯ_Упражнения.txt")
    quiz_content = read_file_content(BASE_DIR / "Урок_1_СУРЬЯ_Тест.txt")
    challenge_content = read_file_content(BASE_DIR / "Урок_1_СУРЬЯ_Челлендж.txt")
    
    # Парсим контент
    theory = parse_theory(theory_content)
    exercises = parse_exercises(exercises_content)
    quiz = parse_quiz(quiz_content)
    challenge = parse_challenge(challenge_content)
    
    print(f"📚 Обновление урока Сурья...")
    print(f"   Теория: {'✓' if theory else '✗'}")
    print(f"   Упражнений: {len(exercises)}")
    print(f"   Вопросов в тесте: {len(quiz['questions']) if quiz else 0}")
    print(f"   Дней челленджа: {challenge['duration_days'] if challenge else 0}")
    
    # Формируем данные для обновления
    lesson_data = {
        'content': {
            'theory': theory
        },
        'exercises': exercises,
        'quiz': quiz,
        'challenges': [challenge] if challenge else []
    }
    
    # Обновляем урок
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    response = requests.put(
        f"{BACKEND_URL}/api/admin/lessons/{LESSON_ID}",
        json=lesson_data,
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"\n✅ Урок успешно обновлен!")
        return True
    else:
        print(f"\n❌ Ошибка обновления: {response.status_code}")
        print(f"   Ответ: {response.text[:500]}")
        return False

def main():
    # Сначала найдем актуальный ID урока
    token = get_admin_token()
    if not token:
        print("❌ Не удалось получить токен")
        return
    
    # Ищем урок Сурья
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{BACKEND_URL}/api/admin/lessons", headers=headers)
    if response.status_code == 200:
        lessons = response.json().get('lessons', [])
        surya_lesson = None
        for lesson in lessons:
            if 'СУРЬЯ' in lesson.get('title', '').upper() or 'СУРЬЯ' in lesson.get('id', '').upper():
                surya_lesson = lesson
                break
        
        if surya_lesson:
            global LESSON_ID
            LESSON_ID = surya_lesson['id']
            print(f"📖 Найден урок: {surya_lesson['title']} (ID: {LESSON_ID})")
        else:
            print("❌ Урок Сурья не найден в базе")
            print("   Доступные уроки:")
            for lesson in lessons[:5]:
                print(f"   - {lesson.get('title')} ({lesson.get('id')})")
            return
    
    # Обновляем урок
    update_lesson(token)

if __name__ == "__main__":
    main()
