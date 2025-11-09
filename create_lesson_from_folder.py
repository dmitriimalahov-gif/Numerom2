#!/usr/bin/env python3
"""
Скрипт для автоматического создания урока из папки с материалами.

Использование:
    python create_lesson_from_folder.py <номер_урока>
    
Например:
    python create_lesson_from_folder.py 1
    
Скрипт ищет папку: файлы для запуска/NumerOM запуск курса/{номер}/Для сайта {номер}
И создаёт урок на основе файлов:
    - Урок_{номер}_*_Теория.txt
    - Урок_{номер}_*_Упражнения.txt
    - Урок_{номер}_*_Тест.txt
    - Урок_{номер}_*_Челлендж.txt
    - файлы/* (PDF, DOCX файлы)
"""

import os
import sys
import json
import requests
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

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
    # Попробуем прочитать из файла, если есть
    token_file = BASE_DIR / ".admin_token"
    if token_file.exists():
        return token_file.read_text().strip()
    
    # Иначе запросим у пользователя
    print("\n🔐 Требуется токен администратора")
    print("Войдите в систему как администратор и скопируйте токен из localStorage")
    token = input("Введите токен: ").strip()
    
    # Сохраним для следующих запусков
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
    for line in lines:
        # Проверяем, является ли строка заголовком секции
        if line.strip().startswith('───') or (line.strip() and line.strip().isupper() and len(line.strip()) < 50):
            # Сохраняем предыдущую секцию
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # Начинаем новую секцию
            if not line.strip().startswith('───'):
                current_section = line.strip().lower().replace(' ', '_')
                current_content = []
        else:
            if line.strip():
                current_content.append(line)
    
    # Сохраняем последнюю секцию
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return {
        "introduction": sections.get("введение", ""),
        "myth": sections.get("миф_о_сурье", sections.get("миф", "")),
        "key_concepts": sections.get("ключевые_концепции", ""),
        "gunas": sections.get("проявления_в_гунах", ""),
        "body": sections.get("сурья_в_теле", sections.get("в_теле", "")),
        "karma": sections.get("кармическая_задача", ""),
        "upai": sections.get("упайи_(гармонизация_сурьи)", sections.get("упайи", "")),
        "pythagoras": sections.get("связь_с_квадратом_пифагора_и_числом_1", ""),
        "practical": sections.get("практическое_применение", ""),
        "full_text": content
    }


def parse_exercises(content: str) -> List[Dict[str, Any]]:
    """Парсинг упражнений"""
    exercises = []
    
    # Разбиваем на упражнения по заголовкам
    exercise_pattern = r'УПРАЖНЕНИЕ\s+(\d+)[:\s]+([^\n]+)'
    matches = list(re.finditer(exercise_pattern, content, re.IGNORECASE))
    
    for i, match in enumerate(matches):
        exercise_num = match.group(1)
        title = match.group(2).strip()
        
        # Извлекаем содержимое упражнения
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        exercise_content = content[start_pos:end_pos].strip()
        
        # Разбиваем на инструкции и ожидаемый результат
        instructions = []
        expected_outcome = ""
        
        lines = exercise_content.split('\n')
        current_section = "instructions"
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('───'):
                continue
            
            if "ожидаемый результат" in line.lower() or "результат:" in line.lower():
                current_section = "outcome"
                continue
            
            if current_section == "instructions":
                if line and not line.startswith('─'):
                    instructions.append(line)
            elif current_section == "outcome":
                if line and not line.startswith('─'):
                    expected_outcome += line + " "
        
        exercises.append({
            "title": title,
            "instructions": instructions,
            "expected_outcome": expected_outcome.strip()
        })
    
    return exercises


def parse_quiz(content: str) -> Dict[str, Any]:
    """Парсинг теста"""
    questions = []
    
    # Разбиваем на вопросы
    question_pattern = r'(\d+)\.\s+([^\n]+)\n((?:[a-dа-г]\).*\n?)+)'
    matches = re.finditer(question_pattern, content, re.MULTILINE)
    
    for match in matches:
        question_num = match.group(1)
        question_text = match.group(2).strip()
        options_text = match.group(3).strip()
        
        # Извлекаем варианты ответов
        options = []
        for line in options_text.split('\n'):
            line = line.strip()
            if line and (line[0].lower() in 'abcdабвгд' and line[1] in ')'):
                options.append(line)
        
        if question_text and len(options) >= 2:
            questions.append({
                "question": question_text,
                "options": options
            })
    
    return {
        "id": f"quiz_lesson_{len(questions)}",
        "title": "Тест по уроку",
        "questions": questions
    }


def parse_challenge(content: str) -> Dict[str, Any]:
    """Парсинг челленджа"""
    lines = content.split('\n')
    
    title = ""
    description = ""
    goals = []
    duration = "7 дней"
    
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('───'):
            continue
        
        # Определяем секции
        if "ЧЕЛЛЕНДЖ" in line.upper() and not title:
            title = line
        elif "ОПИСАНИЕ" in line.upper() or "ЦЕЛЬ" in line.upper():
            current_section = "description"
        elif "ЗАДАЧИ" in line.upper() or "ЗАДАНИЯ" in line.upper():
            current_section = "goals"
        elif "ДЛИТЕЛЬНОСТЬ" in line.upper():
            current_section = "duration"
        else:
            if current_section == "description":
                description += line + " "
            elif current_section == "goals":
                if line and (line[0].isdigit() or line.startswith('•') or line.startswith('-')):
                    goals.append(line.lstrip('0123456789.•- '))
            elif current_section == "duration":
                duration = line
    
    return {
        "title": title or "Недельный челлендж",
        "description": description.strip(),
        "goals": goals,
        "duration_days": 7
    }


def upload_file(filepath: Path, token: str) -> Optional[str]:
    """Загрузить файл на сервер"""
    try:
        with open(filepath, 'rb') as f:
            files = {'file': (filepath.name, f)}
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.post(
                f"{BACKEND_URL}/admin/upload-lesson-file",
                files=files,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Загружен: {filepath.name}")
                return data.get('file_id')
            else:
                print(f"  ❌ Ошибка загрузки {filepath.name}: {response.text}")
                return None
    except Exception as e:
        print(f"  ❌ Ошибка загрузки {filepath}: {e}")
        return None


def create_lesson(lesson_num: int, token: str):
    """Создать урок из папки"""
    
    # Определяем пути
    lesson_dir = LESSONS_BASE_DIR / str(lesson_num)
    content_dir = lesson_dir / f"Для сайта {lesson_num}"
    files_dir = lesson_dir / "файлы"
    
    if not content_dir.exists():
        print(f"❌ Папка не найдена: {content_dir}")
        return
    
    print(f"\n{'='*60}")
    print(f"📚 СОЗДАНИЕ УРОКА {lesson_num}")
    print(f"{'='*60}\n")
    
    # Получаем информацию о планете
    planet_info = LESSON_PLANETS.get(lesson_num, {
        "name": f"УРОК {lesson_num}",
        "planet": f"Планета {lesson_num}",
        "number": lesson_num
    })
    
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
    theory = parse_theory(theory_content)
    print("  ✅ Теория")
    
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
    
    # Загружаем файлы
    additional_files = []
    if files_dir.exists():
        print(f"\n📎 Загрузка файлов из {files_dir.name}...")
        for file_path in files_dir.glob("*"):
            if file_path.suffix.lower() in ['.pdf', '.docx', '.doc']:
                file_id = upload_file(file_path, token)
                if file_id:
                    additional_files.append({
                        "file_id": file_id,
                        "filename": file_path.name,
                        "title": file_path.stem
                    })
    
    # Формируем данные урока
    lesson_data = {
        "id": f"lesson_{lesson_num}_{planet_info['name'].lower()}",
        "title": f"Урок {lesson_num}: {planet_info['name']} - Число {planet_info['number']}",
        "module": f"Модуль {(lesson_num // 3) + 1}: Планеты и числа",
        "description": theory.get("introduction", "")[:200],
        "points_required": lesson_num * 100,
        "is_active": True,
        "content": {
            "theory": theory,
            "planet_info": planet_info
        },
        "exercises": exercises,
        "quiz": quiz,
        "challenges": [challenge] if challenge else [],
        "additional_pdfs": additional_files
    }
    
    # Отправляем на сервер
    print(f"\n🚀 Отправка урока на сервер...")
    
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{BACKEND_URL}/admin/lessons",
            json=lesson_data,
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"\n✅ УРОК {lesson_num} УСПЕШНО СОЗДАН!")
            print(f"{'='*60}\n")
        else:
            print(f"\n❌ Ошибка создания урока: {response.status_code}")
            print(f"Ответ: {response.text}")
    except Exception as e:
        print(f"\n❌ Ошибка отправки: {e}")


def main():
    if len(sys.argv) < 2:
        print("Использование: python create_lesson_from_folder.py <номер_урока>")
        print("Например: python create_lesson_from_folder.py 1")
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

