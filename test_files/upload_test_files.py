#!/usr/bin/env python3
"""
Скрипт для загрузки тестовых файлов в первое занятие
Использование: python upload_test_files.py <admin_token>
"""

import sys
import os
import requests
from pathlib import Path

BACKEND_URL = "http://localhost:8000"
LESSON_ID = "lesson_numerom_intro"

def upload_file(file_path, file_type, token):
    """Загрузить файл через consultations endpoint"""
    endpoint_map = {
        "video": f"{BACKEND_URL}/api/admin/consultations/upload-video",
        "pdf": f"{BACKEND_URL}/api/admin/consultations/upload-pdf",
        "word": f"{BACKEND_URL}/api/admin/lessons/upload-word"
    }
    
    endpoint = endpoint_map.get(file_type)
    if not endpoint:
        print(f"❌ Неизвестный тип файла: {file_type}")
        return None
    
    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        return None
    
    print(f"\n📤 Загрузка {file_type}: {file_path}...")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.post(endpoint, files=files, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {file_type.upper()} загружен успешно!")
                print(f"   File ID: {result.get('file_id')}")
                print(f"   Filename: {result.get('filename')}")
                return result
            else:
                print(f"❌ Ошибка загрузки {file_type}: {response.status_code}")
                print(f"   Ответ: {response.text}")
                return None
    except Exception as e:
        print(f"❌ Исключение при загрузке {file_type}: {str(e)}")
        return None

def update_lesson(lesson_id, updates, token):
    """Обновить урок с загруженными файлами"""
    print(f"\n💾 Сохранение изменений в урок {lesson_id}...")
    
    endpoint = f"{BACKEND_URL}/api/admin/lessons/{lesson_id}"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.put(endpoint, json=updates, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Урок успешно обновлен!")
            return result
        else:
            print(f"❌ Ошибка обновления урока: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Исключение при обновлении урока: {str(e)}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Использование: python upload_test_files.py <admin_token>")
        print("\nЧтобы получить токен:")
        print("1. Войдите в админ-панель")
        print("2. Откройте консоль браузера (F12)")
        print("3. Выполните: localStorage.getItem('token')")
        sys.exit(1)
    
    token = sys.argv[1]
    script_dir = Path(__file__).parent
    
    # Находим тестовые файлы
    video_file = script_dir / "test_video.mp4"
    pdf_file = script_dir / "test.pdf"
    word_file = script_dir / "test.docx"
    
    print("=" * 60)
    print("ЗАГРУЗКА ТЕСТОВЫХ ФАЙЛОВ В ПЕРВОЕ ЗАНЯТИЕ")
    print("=" * 60)
    
    results = {}
    
    # Загружаем видео
    if video_file.exists():
        video_result = upload_file(video_file, "video", token)
        if video_result:
            results['video_file_id'] = video_result.get('file_id')
            results['video_filename'] = video_result.get('filename')
    else:
        print(f"⚠️  Видео файл не найден: {video_file}")
    
    # Загружаем PDF
    if pdf_file.exists():
        pdf_result = upload_file(pdf_file, "pdf", token)
        if pdf_result:
            results['pdf_file_id'] = pdf_result.get('file_id')
            results['pdf_filename'] = pdf_result.get('filename')
    else:
        print(f"⚠️  PDF файл не найден: {pdf_file}")
    
    # Загружаем Word
    if word_file.exists():
        word_result = upload_file(word_file, "word", token)
        if word_result:
            results['word_file_id'] = word_result.get('file_id')
            results['word_filename'] = word_result.get('filename')
    else:
        print(f"⚠️  Word файл не найден: {word_file}")
    
    # Обновляем урок
    if results:
        print("\n" + "=" * 60)
        print("РЕЗУЛЬТАТЫ ЗАГРУЗКИ:")
        print("=" * 60)
        for key, value in results.items():
            print(f"  {key}: {value}")
        
        update_result = update_lesson(LESSON_ID, results, token)
        if update_result:
            print("\n✅ Все файлы успешно загружены и сохранены в уроке!")
            print(f"\nОткройте урок во вкладке обучения, чтобы проверить отображение файлов.")
        else:
            print("\n⚠️  Файлы загружены, но урок не обновлен.")
            print("   Обновите урок вручную в админ-панели.")
    else:
        print("\n❌ Не удалось загрузить ни одного файла.")
        sys.exit(1)

if __name__ == "__main__":
    main()
