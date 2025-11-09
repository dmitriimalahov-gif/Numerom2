#!/usr/bin/env python3
"""
Прямое обновление первого урока через MongoDB
"""

import sys
import re
from pathlib import Path
from typing import Dict, List
from datetime import datetime, UTC

# Конфигурация
BASE_DIR = Path("/Users/brandbox/Desktop/numerom/Numerom1")
LESSONS_BASE_DIR = BASE_DIR / "файлы для запуска" / "NumerOM запуск курса"

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

def generate_mongo_script(lesson_num: int):
    """Генерирует скрипт для MongoDB"""
    
    # Определяем пути
    lesson_dir = LESSONS_BASE_DIR / str(lesson_num)
    content_dir = lesson_dir / f"Для сайта {lesson_num}"
    
    if not content_dir.exists():
        print(f"❌ Папка не найдена: {content_dir}")
        return
    
    print(f"\n{'='*60}")
    print(f"📚 ГЕНЕРАЦИЯ СКРИПТА ДЛЯ ОБНОВЛЕНИЯ ПЕРВОГО УРОКА")
    print(f"{'='*60}\n")
    
    # Читаем теорию
    theory_file = list(content_dir.glob(f"Урок_{lesson_num}_*_Теория.txt"))
    if not theory_file:
        print(f"❌ Не найден файл с теорией")
        return
    
    theory_content = read_text_file(theory_file[0])
    theory_sections = parse_theory(theory_content)
    
    print(f"📖 Найдено разделов теории: {len(theory_sections)}")
    for key in theory_sections.keys():
        print(f"   - {key}")
    
    # Генерируем MongoDB скрипт
    mongo_script = f"""
// Скрипт для обновления первого урока данными из урока {lesson_num}
// Выполните в MongoDB Compass или mongo shell

use numerom;

// Удаляем старые данные первого урока
db.lesson_content.deleteMany({{"lesson_id": "lesson_numerom_intro"}});
db.lesson_exercises.deleteMany({{"lesson_id": "lesson_numerom_intro"}});

// Вставляем новые данные теории
"""
    
    for section_key, section_content in theory_sections.items():
        if section_content:
            # Экранируем кавычки
            escaped_content = section_content.replace('"', '\\"').replace('\n', '\\n')
            mongo_script += f'''
db.lesson_content.insertOne({{
    "lesson_id": "lesson_numerom_intro",
    "type": "content_update",
    "section": "theory",
    "field": "{section_key}",
    "value": "{escaped_content}",
    "updated_at": new Date()
}});
'''
    
    mongo_script += """
print("✅ Теория первого урока обновлена!");
"""
    
    # Сохраняем скрипт
    script_file = BASE_DIR / f"update_lesson_{lesson_num}_mongo.js"
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(mongo_script)
    
    print(f"\n✅ Скрипт MongoDB создан: {script_file.name}")
    print(f"\n🚀 Выполните команду:")
    print(f"   docker-compose exec -T backend mongo mongodb://numerom_mongodb:27017/numerom < {script_file.name}")

def main():
    if len(sys.argv) < 2:
        print("Использование: python update_first_lesson_direct.py <номер_урока>")
        print("Например: python update_first_lesson_direct.py 1")
        sys.exit(1)
    
    lesson_num = int(sys.argv[1])
    generate_mongo_script(lesson_num)

if __name__ == "__main__":
    main()
