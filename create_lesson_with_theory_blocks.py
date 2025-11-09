#!/usr/bin/env python3
"""
Скрипт для создания урока с правильными блоками теории через API
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
import time

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

def parse_theory_blocks(content: str) -> List[Dict[str, str]]:
    """Парсинг теории на отдельные блоки с заголовками"""
    blocks = []
    current_title = None
    current_content = []
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Проверяем, является ли строка разделителем
        if line.startswith('───'):
            # Сохраняем предыдущий блок
            if current_title and current_content:
                blocks.append({
                    "title": current_title,
                    "content": '\n'.join(current_content).strip()
                })
                current_content = []
            
            # Следующая строка после разделителя - это заголовок
            if i + 1 < len(lines):
                i += 1
                header = lines[i].strip()
                if header and header.isupper():
                    current_title = header
                    # Пропускаем следующий разделитель если он есть
                    if i + 1 < len(lines) and lines[i + 1].strip().startswith('───'):
                        i += 1
        else:
            # Добавляем содержимое к текущему блоку
            if current_title and line:
                current_content.append(lines[i])
        
        i += 1
    
    # Сохраняем последний блок
    if current_title and current_content:
        blocks.append({
            "title": current_title,
            "content": '\n'.join(current_content).strip()
        })
    
    return blocks

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
                "title": title,
                "type": exercise_type.lower(),
                "content": exercise_content,
                "instructions": '\n'.join(instructions),  # Объединяем в строку для API
                "expected_outcome": expected_outcome
            })
    
    return exercises

def parse_quiz(content: str) -> List[Dict[str, Any]]:
    """Парсинг теста на отдельные вопросы"""
    questions = []
    
    # Разбиваем на вопросы
    question_pattern = r'(\d+)\.\s+([^\n]+)\n((?:[A-E]\.\s+[^\n]+\n?)+)'
    matches = re.finditer(question_pattern, content, re.MULTILINE)
    
    # Извлекаем правильные ответы
    answers_dict = {}
    answers_match = re.search(r'ОТВЕТЫ:\s*\n([^\n]+)', content)
    if answers_match:
        answers_text = answers_match.group(1)
        answer_pairs = re.findall(r'(\d+)–([A-E])', answers_text)
        for num, answer in answer_pairs:
            answers_dict[num] = answer
    
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
            correct_answer = answers_dict.get(question_num, "A")
            questions.append({
                "question": question_text,
                "options": options,
                "correct_answer": correct_answer,
                "explanation": f"Правильный ответ: {correct_answer}"
            })
    
    return questions

def parse_challenge_days(content: str) -> List[Dict[str, Any]]:
    """Парсинг челленджа на отдельные дни"""
    days = []
    lines = content.split('\n')
    
    current_day = None
    current_tasks = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('───'):
            continue
        
        if re.match(r'^[А-Я]+ — ', line):
            # Новый день
            if current_day and current_tasks:
                days.append({
                    "title": current_day,
                    "tasks": '\n'.join(current_tasks)
                })
            
            current_day = line
            current_tasks = []
        elif line and current_day:
            # Задачи дня
            if line[0].isdigit() or line.startswith('•') or line.startswith('-'):
                current_tasks.append(line.lstrip('0123456789.•- '))
    
    # Добавляем последний день
    if current_day and current_tasks:
        days.append({
            "title": current_day,
            "tasks": '\n'.join(current_tasks)
        })
    
    return days

def create_lesson_with_blocks(lesson_num: int, token: str):
    """Создать урок с блоками теории"""
    
    # Определяем пути
    lesson_dir = LESSONS_BASE_DIR / str(lesson_num)
    content_dir = lesson_dir / f"Для сайта {lesson_num}"
    
    if not content_dir.exists():
        print(f"❌ Папка не найдена: {content_dir}")
        return
    
    print(f"\n{'='*60}")
    print(f"📚 СОЗДАНИЕ УРОКА {lesson_num} С БЛОКАМИ ТЕОРИИ")
    print(f"{'='*60}\n")
    
    planet_info = LESSON_PLANETS.get(lesson_num)
    print(f"🪐 Планета: {planet_info['planet']}")
    print(f"🔢 Число: {planet_info['number']}")
    
    # Читаем файлы
    print(f"\n📖 Чтение файлов...")
    
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
    theory_blocks = parse_theory_blocks(theory_content)
    print(f"  ✅ Теория ({len(theory_blocks)} блоков)")
    
    exercises = []
    if exercises_file:
        exercises_content = read_text_file(exercises_file[0])
        exercises = parse_exercises(exercises_content)
        print(f"  ✅ Упражнения ({len(exercises)} шт.)")
    
    quiz_questions = []
    if quiz_file:
        quiz_content = read_text_file(quiz_file[0])
        quiz_questions = parse_quiz(quiz_content)
        print(f"  ✅ Тест ({len(quiz_questions)} вопросов)")
    
    challenge_days = []
    if challenge_file:
        challenge_content = read_text_file(challenge_file[0])
        challenge_days = parse_challenge_days(challenge_content)
        print(f"  ✅ Челлендж ({len(challenge_days)} дней)")
    
    # Шаг 1: Создаем базовый урок
    lesson_id = f"lesson_{lesson_num}_{planet_info['name'].lower()}"
    
    lesson_data = {
        "id": lesson_id,
        "title": f"Урок {lesson_num}: {planet_info['name']} - Число {planet_info['number']}",
        "module": f"Модуль {(lesson_num // 3) + 1}: Планеты и числа",
        "description": theory_blocks[0]["content"][:200] + "..." if theory_blocks else "",
        "level": 1,
        "order": lesson_num,
        "duration_minutes": 45,
        "points_required": lesson_num * 100,
        "is_active": True,
        "content": {
            # Сразу добавляем кастомные блоки теории в content
            "custom_theory_blocks": {
                "blocks": [
                    {
                        "id": f"custom_{int(time.time())}_{i}",
                        "title": block["title"],
                        "content": block["content"]
                    }
                    for i, block in enumerate(theory_blocks)
                ]
            },
            # Добавляем квиз если есть
            "quiz": {
                "id": f"quiz_{lesson_id}",
                "title": "Тест по уроку",
                "questions": quiz_questions
            } if quiz_questions else None,
            # Добавляем челлендж если есть
            "challenge": {
                "id": f"challenge_{lesson_id}",
                "title": "7-дневный челлендж",
                "description": "Практические задания на неделю",
                "duration_days": 7,
                "daily_tasks": [
                    {
                        "day": i + 1,
                        "title": day["title"],
                        "tasks": day["tasks"].split('\n') if isinstance(day["tasks"], str) else day["tasks"]
                    }
                    for i, day in enumerate(challenge_days)
                ]
            } if challenge_days else None
        },
        "exercises": exercises,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
        "source": "custom_lessons"
    }
    
    print(f"\n🚀 Шаг 1: Создание базового урока...")
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/admin/lessons/create",
            json=lesson_data,
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"  ✅ Базовый урок создан")
        else:
            print(f"  ❌ Ошибка создания базового урока: {response.text}")
            return
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return
    
    
    print(f"\n✅ УРОК {lesson_num} ПОЛНОСТЬЮ СОЗДАН!")
    print(f"   📖 Теория: {len(theory_blocks)} блоков")
    print(f"   📝 Упражнения: {len(exercises)} шт.")
    print(f"   ❓ Тест: {len(quiz_questions)} вопросов")
    print(f"   🏆 Челлендж: {len(challenge_days)} дней")
    print(f"\n🎯 ГОТОВ К РЕДАКТИРОВАНИЮ В АДМИН-ПАНЕЛИ!")
    print(f"🎓 ГОТОВ К ИЗУЧЕНИЮ СТУДЕНТАМИ!")
    print(f"{'='*60}\n")

def main():
    if len(sys.argv) < 2:
        print("Использование: python create_lesson_with_theory_blocks.py <номер_урока>")
        print("Например: python create_lesson_with_theory_blocks.py 1")
        sys.exit(1)
    
    lesson_num = int(sys.argv[1])
    
    if lesson_num not in range(0, 10):
        print(f"❌ Номер урока должен быть от 0 до 9")
        sys.exit(1)
    
    # Получаем токен
    token = get_admin_token()
    
    # Создаём урок с блоками
    create_lesson_with_blocks(lesson_num, token)

if __name__ == "__main__":
    main()
