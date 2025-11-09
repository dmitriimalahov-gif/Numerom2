#!/usr/bin/env python3
"""
Скрипт для обновления содержимого первого урока через коллекции lesson_content и lesson_exercises
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

def parse_theory(content: str) -> Dict[str, Any]:
    """Парсинг теоретической части"""
    sections = {}
    current_section = None
    current_content = []
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Проверяем, является ли строка разделителем
        if line.startswith('───'):
            # Сохраняем предыдущую секцию
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
                current_content = []
            
            # Следующая строка после разделителя - это заголовок секции
            if i + 1 < len(lines):
                i += 1
                header = lines[i].strip()
                if header and header.isupper():
                    current_section = header.lower()
                    # Пропускаем следующий разделитель если он есть
                    if i + 1 < len(lines) and lines[i + 1].strip().startswith('───'):
                        i += 1
        else:
            # Добавляем содержимое к текущей секции
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
    
    # Разбиваем на блоки упражнений по разделителям
    exercise_blocks = re.split(r'───+', content)
    
    for i, block in enumerate(exercise_blocks):
        if not block.strip():
            continue
            
        # Ищем номер упражнения
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
            # Разбиваем по пунктам
            for line in instruction_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('•') or line.startswith('-')):
                    instructions.append(re.sub(r'^\d+\.\s*', '', line.lstrip('•- ')))
        
        # Извлекаем ожидаемый результат
        outcome_match = re.search(r'Ожидаемый результат:\s*\n?(.*?)(?=───|$)', block, re.DOTALL | re.IGNORECASE)
        expected_outcome = outcome_match.group(1).strip() if outcome_match else ""
        
        if title:
            exercises.append({
                "id": f"ex_surya_{exercise_num}_{title.lower().replace(' ', '_')[:20]}",
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
                "question": question_text,
                "options": options
            })
    
    # Извлекаем правильные ответы из блока ОТВЕТЫ
    answers_match = re.search(r'ОТВЕТЫ:\s*\n([^\n]+)', content)
    if answers_match:
        answers_text = answers_match.group(1)
        # Парсим формат "1–C, 2–A, 3–C, ..."
        answer_pairs = re.findall(r'(\d+)–([A-E])', answers_text)
        for num, answer in answer_pairs:
            correct_answers.append(answer)
            explanations.append(f"Правильный ответ на вопрос {num}: {answer}")
    
    return {
        "id": f"quiz_surya_lesson",
        "title": "Тест по уроку Сурья",
        "questions": questions,
        "correct_answers": correct_answers,
        "explanations": explanations
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
        "id": f"challenge_surya_7days",
        "title": title or "7-дневный челлендж Сурьи",
        "description": description.strip(),
        "duration_days": 7,
        "daily_tasks": daily_tasks,
        "completion_tracking": {}
    }

def update_first_lesson_content(lesson_num: int, token: str):
    """Обновить содержимое первого урока через lesson_content и lesson_exercises"""
    
    # Определяем пути
    lesson_dir = LESSONS_BASE_DIR / str(lesson_num)
    content_dir = lesson_dir / f"Для сайта {lesson_num}"
    
    if not content_dir.exists():
        print(f"❌ Папка не найдена: {content_dir}")
        return
    
    print(f"\n{'='*60}")
    print(f"📚 ОБНОВЛЕНИЕ ПЕРВОГО УРОКА ДАННЫМИ ИЗ УРОКА {lesson_num}")
    print(f"{'='*60}\n")
    
    # Читаем файлы
    print(f"📖 Чтение файлов из {content_dir.name}...")
    
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
        print(f"  ✅ Челлендж")
    
    # Сохраняем данные в правильные коллекции через прямую вставку в MongoDB
    print(f"\n💾 Сохранение данных в базу...")
    
    try:
        # Подготавливаем данные для вставки
        content_updates = []
        
        # Сохраняем теорию в lesson_content
        for section_key, section_content in theory_sections.items():
            if section_content:
                content_updates.append({
                    "lesson_id": "lesson_numerom_intro",
                    "type": "content_update",
                    "section": "theory",
                    "field": section_key,
                    "value": section_content,
                    "updated_at": datetime.now(UTC).isoformat()
                })
        
        # Сохраняем упражнения в lesson_exercises
        exercise_updates = []
        for exercise in exercises:
            exercise_updates.append({
                "lesson_id": "lesson_numerom_intro",
                "content_type": "exercise_update",
                "exercise_id": exercise["id"],
                "title": exercise["title"],
                "type": exercise["type"],
                "content": exercise["content"],
                "instructions": exercise["instructions"],
                "expected_outcome": exercise["expected_outcome"],
                "updated_at": datetime.now(UTC).isoformat()
            })
        
        # Отправляем данные через API
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Сохраняем контент
        if content_updates:
            response = requests.post(
                f"{BACKEND_URL}/admin/lessons/lesson_numerom_intro/bulk-update-content",
                json={"updates": content_updates},
                headers=headers
            )
            
            if response.status_code == 200:
                print(f"  ✅ Теория сохранена ({len(content_updates)} разделов)")
            else:
                print(f"  ❌ Ошибка сохранения теории: {response.text}")
        
        # Сохраняем упражнения
        if exercise_updates:
            response = requests.post(
                f"{BACKEND_URL}/admin/lessons/lesson_numerom_intro/bulk-update-exercises",
                json={"exercises": exercise_updates},
                headers=headers
            )
            
            if response.status_code == 200:
                print(f"  ✅ Упражнения сохранены ({len(exercise_updates)} шт.)")
            else:
                print(f"  ❌ Ошибка сохранения упражнений: {response.text}")
        
        # Сохраняем тест и челлендж через обновление урока
        if quiz or challenge:
            update_data = {}
            if quiz:
                update_data["quiz"] = quiz
            if challenge:
                update_data["challenge"] = challenge
            
            response = requests.put(
                f"{BACKEND_URL}/admin/lessons/lesson_numerom_intro/content",
                json=update_data,
                headers=headers
            )
            
            if response.status_code == 200:
                print(f"  ✅ Тест и челлендж сохранены")
            else:
                print(f"  ❌ Ошибка сохранения теста/челленджа: {response.text}")
        
        print(f"\n✅ ПЕРВОЕ ЗАНЯТИЕ ОБНОВЛЕНО ДАННЫМИ ИЗ УРОКА {lesson_num}!")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n❌ Ошибка сохранения: {e}")

def main():
    if len(sys.argv) < 2:
        print("Использование: python create_lesson_content_update.py <номер_урока>")
        print("Например: python create_lesson_content_update.py 1")
        sys.exit(1)
    
    lesson_num = int(sys.argv[1])
    
    if lesson_num not in range(0, 10):
        print(f"❌ Номер урока должен быть от 0 до 9")
        sys.exit(1)
    
    # Получаем токен
    token = get_admin_token()
    
    # Обновляем первое занятие
    update_first_lesson_content(lesson_num, token)

if __name__ == "__main__":
    main()
