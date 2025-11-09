#!/usr/bin/env python3
"""
Финальный скрипт для создания урока в custom_lessons с полной структурой
для редактирования через админ-панель и изучения студентами
"""

import os
import sys
import json
import requests
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime, UTC

# Конфигурация
BACKEND_URL = "http://192.168.110.178:8001/api"
BASE_DIR = Path("/Users/brandbox/Desktop/numerom/Numerom1")
LESSONS_BASE_DIR = BASE_DIR / "файлы для запуска" / "NumerOM запуск курса"

# Маппинг номеров уроков на планеты
LESSON_PLANETS = {
    0: {"name": "ЧИСЛО ПРОБЛЕМЫ", "planet": "Число Проблемы", "number": 0},
    1: {"name": "СУРЬЯ", "planet": "Surya (Солнце)", "number": 1},
    2: {"name": "ЧАНДРА", "planet": "Chandra (Луна)", "number": 2},
    3: {"name": "ГУРУ", "planet": "Guru (Юпитер)", "number": 3},
    4: {"name": "РАХУ", "planet": "Rahu", "number": 4},
    5: {"name": "БУДДХА", "planet": "Budh (Меркурий)", "number": 5},
    6: {"name": "ШУКРА", "planet": "Shukra (Венера)", "number": 6},
    7: {"name": "КЕТУ", "planet": "Ketu", "number": 7},
    8: {"name": "ШАНИ", "planet": "Shani (Сатурн)", "number": 8},
    9: {"name": "МАНГАЛ", "planet": "Mangal (Марс)", "number": 9},
}

def get_admin_token():
    """Получить токен администратора"""
    token_file = BASE_DIR / ".admin_token"
    if token_file.exists():
        return token_file.read_text().strip()
    
    print("\n🔐 Требуется токен администратора")
    token = input("Введите токен: ").strip()
    token_file.write_text(token)
    return token

def read_text_file(filepath: Path) -> str:
    """Прочитать текстовый файл"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"⚠️ Ошибка чтения файла {filepath}: {e}")
        return ""

def parse_theory(content: str) -> Dict[str, str]:
    """Парсинг теоретической части"""
    sections = {}
    current_section = None
    current_content = []
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('───'):
            # Сохраняем предыдущую секцию
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
                current_content = []
            
            # Следующая строка - заголовок секции
            if i + 1 < len(lines):
                i += 1
                header = lines[i].strip()
                if header and header.isupper():
                    current_section = header.lower()
                    if i + 1 < len(lines) and lines[i + 1].strip().startswith('───'):
                        i += 1
        else:
            if current_section and line:
                current_content.append(lines[i])
        
        i += 1
    
    # Сохраняем последнюю секцию
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return sections

def parse_exercises(content: str) -> List[Dict[str, Any]]:
    """Парсинг упражнений"""
    exercises = []
    
    # Разбиваем на блоки упражнений
    exercise_blocks = re.split(r'───+', content)
    
    for block in exercise_blocks:
        if not block.strip():
            continue
            
        # Ищем номер и название упражнения
        number_match = re.search(r'(\d+)\.\s*Название:\s*([^\n]+)', block, re.IGNORECASE)
        if not number_match:
            continue
            
        exercise_num = number_match.group(1)
        title = number_match.group(2).strip()
        
        # Извлекаем тип
        type_match = re.search(r'Тип:\s*([^\n]+)', block, re.IGNORECASE)
        exercise_type = type_match.group(1).strip() if type_match else "practical"
        
        # Извлекаем содержание
        content_match = re.search(r'Содержание:\s*\n(.*?)(?=Инструкция:|$)', block, re.DOTALL | re.IGNORECASE)
        exercise_content = content_match.group(1).strip() if content_match else ""
        
        # Извлекаем инструкции
        instructions = []
        instruction_match = re.search(r'Инструкция:\s*\n(.*?)(?=Ожидаемый результат:|$)', block, re.DOTALL | re.IGNORECASE)
        if instruction_match:
            instruction_text = instruction_match.group(1).strip()
            for line in instruction_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('•') or line.startswith('-')):
                    instructions.append(re.sub(r'^\d+\.\s*', '', line.lstrip('•- ')))
        
        # Извлекаем ожидаемый результат
        outcome_match = re.search(r'Ожидаемый результат:\s*\n?(.*?)(?=───|$)', block, re.DOTALL | re.IGNORECASE)
        expected_outcome = outcome_match.group(1).strip() if outcome_match else ""
        
        if title:
            exercises.append({
                "id": f"ex_{exercise_num}_{uuid.uuid4().hex[:8]}",
                "title": title,
                "type": exercise_type.lower(),
                "content": exercise_content,
                "instructions": instructions,
                "expected_outcome": expected_outcome
            })
    
    return exercises

def parse_quiz(content: str) -> Dict[str, Any]:
    """Парсинг теста"""
    questions = []
    correct_answers = []
    explanations = []
    
    # Разбиваем на вопросы
    question_pattern = r'(\d+)\.\s+([^\n]+)\n((?:[A-E]\.\s+[^\n]+\n?)+)'
    matches = re.finditer(question_pattern, content, re.MULTILINE)
    
    for match in matches:
        question_num = match.group(1)
        question_text = match.group(2).strip()
        options_text = match.group(3).strip()
        
        # Извлекаем варианты ответов
        options = []
        for line in options_text.split('\n'):
            line = line.strip()
            if line and re.match(r'^[A-E]\.', line):
                options.append(line)
        
        if question_text and len(options) >= 2:
            questions.append({
                "id": f"q_{question_num}_{uuid.uuid4().hex[:8]}",
                "question": question_text,
                "options": options,
                "correct_answer": "",  # Заполним из ответов
                "explanation": ""
            })
    
    # Извлекаем правильные ответы
    answers_match = re.search(r'ОТВЕТЫ:\s*\n([^\n]+)', content)
    if answers_match:
        answers_text = answers_match.group(1)
        answer_pairs = re.findall(r'(\d+)–([A-E])', answers_text)
        
        for i, (num, answer) in enumerate(answer_pairs):
            if i < len(questions):
                questions[i]["correct_answer"] = answer
                questions[i]["explanation"] = f"Правильный ответ: {answer}"
                correct_answers.append(answer)
                explanations.append(f"Правильный ответ на вопрос {num}: {answer}")
    
    return {
        "id": f"quiz_{uuid.uuid4().hex[:8]}",
        "title": "Тест по уроку",
        "questions": questions,
        "correct_answers": correct_answers,
        "explanations": explanations,
        "passing_score": 70
    }

def parse_challenge(content: str) -> Dict[str, Any]:
    """Парсинг челленджа"""
    lines = content.split('\n')
    
    title = ""
    description = ""
    daily_tasks = []
    
    current_day = None
    current_tasks = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('───'):
            continue
        
        # Заголовок челленджа
        if "ЧЕЛЛЕНДЖ" in line.upper() and not title:
            title = line
        elif "Описание:" in line:
            continue
        elif re.match(r'^[А-Я]+ — ', line):
            # Новый день
            if current_day and current_tasks:
                daily_tasks.append({
                    "day": len(daily_tasks) + 1,
                    "title": current_day,
                    "tasks": current_tasks
                })
            
            current_day = line
            current_tasks = []
        elif line and current_day:
            # Задачи дня
            if line[0].isdigit() or line.startswith('•') or line.startswith('-'):
                current_tasks.append(line.lstrip('0123456789.•- '))
            elif not any(keyword in line.lower() for keyword in ['результат:', 'описание:']):
                if not description and not current_day:
                    description += line + " "
    
    # Добавляем последний день
    if current_day and current_tasks:
        daily_tasks.append({
            "day": len(daily_tasks) + 1,
            "title": current_day,
            "tasks": current_tasks
        })
    
    return {
        "id": f"challenge_{uuid.uuid4().hex[:8]}",
        "title": title or "7-дневный челлендж",
        "description": description.strip(),
        "duration_days": 7,
        "daily_tasks": daily_tasks,
        "completion_tracking": {}
    }

def create_lesson(lesson_num: int, token: str):
    """Создать урок в custom_lessons"""
    
    # Определяем пути
    lesson_dir = LESSONS_BASE_DIR / str(lesson_num)
    content_dir = lesson_dir / f"Для сайта {lesson_num}"
    
    if not content_dir.exists():
        print(f"❌ Папка не найдена: {content_dir}")
        return
    
    print(f"\n{'='*60}")
    print(f"📚 СОЗДАНИЕ УРОКА {lesson_num} В CUSTOM_LESSONS")
    print(f"{'='*60}\n")
    
    # Получаем информацию о планете
    planet_info = LESSON_PLANETS.get(lesson_num)
    
    print(f"🪐 Планета: {planet_info['planet']}")
    print(f"🔢 Число: {planet_info['number']}")
    
    # Читаем файлы
    print(f"\n📖 Чтение файлов из {content_dir.name}...")
    
    theory_file = list(content_dir.glob(f"Урок_{lesson_num}_*_Теория.txt"))
    exercises_file = list(content_dir.glob(f"Урок_{lesson_num}_*_Упражнения.txt"))
    quiz_file = list(content_dir.glob(f"Урок_{lesson_num}_*_Тест.txt"))
    challenge_file = list(content_dir.glob(f"Урок_{lesson_num}_*_Челлендж.txt"))
    
    if not theory_file:
        print(f"❌ Не найден файл с теорией")
        return
    
    # Парсим содержимое
    print("\n🔍 Парсинг содержимого...")
    
    theory_content = read_text_file(theory_file[0])
    theory_sections = parse_theory(theory_content)
    print(f"  ✅ Теория ({len(theory_sections)} разделов)")
    
    exercises = []
    if exercises_file:
        exercises_content = read_text_file(exercises_file[0])
        exercises = parse_exercises(exercises_content)
        print(f"  ✅ Упражнения ({len(exercises)} шт.)")
    
    quiz = None
    if quiz_file:
        quiz_content = read_text_file(quiz_file[0])
        quiz = parse_quiz(quiz_content)
        print(f"  ✅ Тест ({len(quiz['questions'])} вопросов)")
    
    challenge = None
    if challenge_file:
        challenge_content = read_text_file(challenge_file[0])
        challenge = parse_challenge(challenge_content)
        print(f"  ✅ Челлендж ({len(challenge['daily_tasks'])} дней)")
    
    # Формируем полную структуру урока для custom_lessons
    lesson_id = f"lesson_{lesson_num}_{planet_info['name'].lower()}"
    
    lesson_data = {
        "id": lesson_id,
        "title": f"Урок {lesson_num}: {planet_info['name']} - Число {planet_info['number']}",
        "module": f"Модуль {(lesson_num // 3) + 1}: Планеты и числа",
        "description": theory_sections.get("введение", "")[:200] + "...",
        "level": 1,
        "order": lesson_num,
        "duration_minutes": 45,
        "points_required": lesson_num * 100,
        "is_active": True,
        
        # Медиа поля (как в консультациях)
        "video_url": "",
        "video_file_id": None,
        "video_filename": None,
        "pdf_file_id": None,
        "pdf_filename": None,
        "word_file_id": None,
        "word_filename": None,
        
        # Основной контент урока
        "content": {
            # Теория - структура как в первом уроке
            "theory": theory_sections,
            
            # Информация о планете
            "planet_info": planet_info,
            
            # Квиз
            "quiz": quiz,
            
            # Челлендж
            "challenge": challenge,
            
            # Дополнительная информация
            "practical_tips": {
                "basic_info": f"Изучение энергии {planet_info['planet']} и числа {planet_info['number']}",
                "how_to_use": "Практические советы по работе с этой энергией"
            }
        },
        
        # Упражнения (отдельно, как в первом уроке)
        "exercises": exercises,
        
        # Метаданные
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
        "source": "custom_lessons"
    }
    
    # Отправляем на сервер
    print(f"\n🚀 Создание урока в custom_lessons...")
    
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{BACKEND_URL}/admin/lessons/create",
            json=lesson_data,
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"\n✅ УРОК {lesson_num} СОЗДАН В CUSTOM_LESSONS!")
            print(f"   ID: {lesson_id}")
            print(f"   Название: {lesson_data['title']}")
            print(f"   Теория: {len(theory_sections)} разделов")
            print(f"   Упражнения: {len(exercises)} шт.")
            print(f"   Тест: {len(quiz['questions']) if quiz else 0} вопросов")
            print(f"   Челлендж: {len(challenge['daily_tasks']) if challenge else 0} дней")
            print(f"\n🎯 ГОТОВ К РЕДАКТИРОВАНИЮ И ИЗУЧЕНИЮ!")
            print(f"{'='*60}\n")
        else:
            print(f"\n❌ Ошибка создания урока: {response.status_code}")
            print(f"Ответ: {response.text}")
    except Exception as e:
        print(f"\n❌ Ошибка отправки: {e}")

def main():
    if len(sys.argv) < 2:
        print("Использование: python create_lesson_final.py <номер_урока>")
        print("Например: python create_lesson_final.py 1")
        sys.exit(1)
    
    lesson_num = int(sys.argv[1])
    
    if lesson_num not in range(0, 10):
        print(f"❌ Номер урока должен быть от 0 до 9")
        sys.exit(1)
    
    # Получаем токен
    token = get_admin_token()
    
    # Создаём урок
    create_lesson(lesson_num, token)

if __name__ == "__main__":
    main()
