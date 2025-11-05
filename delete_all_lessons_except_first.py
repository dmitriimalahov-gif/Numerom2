#!/usr/bin/env python3
"""
Удаление всех занятий из базы данных, кроме первого (вводного)
"""
import sys
import requests

BACKEND_URL = "http://localhost:8000"

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

def get_all_lessons(token):
    """Получает все занятия"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{BACKEND_URL}/api/admin/lessons", headers=headers)
    if response.status_code == 200:
        return response.json().get('lessons', [])
    return []

def delete_lesson(lesson_id, token):
    """Удаляет занятие"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.delete(
        f"{BACKEND_URL}/api/admin/lessons/{lesson_id}",
        headers=headers
    )
    return response.status_code == 200

def main():
    print("="*70)
    print("УДАЛЕНИЕ ВСЕХ ЗАНЯТИЙ КРОМЕ ПЕРВОГО")
    print("="*70)
    
    # Получаем токен
    token = get_admin_token()
    if not token:
        print("❌ Не удалось получить токен администратора")
        return
    
    # Получаем все занятия
    print("\n📚 Получение списка занятий...")
    lessons = get_all_lessons(token)
    
    if not lessons:
        print("✅ В базе данных нет занятий для удаления")
        return
    
    print(f"   Найдено занятий: {len(lessons)}")
    
    # Находим первое занятие (вводное или с минимальным order/level)
    first_lesson = None
    
    # Сначала ищем вводное занятие
    for lesson in lessons:
        title = lesson.get('title', '').upper()
        lesson_id = lesson.get('id', '').upper()
        if 'ВВОДНОЕ' in title or 'INTRO' in lesson_id or 'ВВОД' in title:
            first_lesson = lesson
            break
    
    # Если не нашли вводное, ищем с минимальным order или level
    if not first_lesson:
        sorted_lessons = sorted(lessons, key=lambda x: (
            x.get('order', 999),
            x.get('level', 999),
            x.get('title', '')
        ))
        first_lesson = sorted_lessons[0]
    
    if first_lesson:
        print(f"\n✅ Первое занятие (будет сохранено):")
        print(f"   ID: {first_lesson.get('id')}")
        print(f"   Название: {first_lesson.get('title')}")
        print(f"   Модуль: {first_lesson.get('module', 'N/A')}")
        print(f"   Order: {first_lesson.get('order', 'N/A')}")
        print(f"   Level: {first_lesson.get('level', 'N/A')}")
    else:
        print("\n❌ Не удалось определить первое занятие")
        return
    
    # Подтверждение
    print(f"\n⚠️  Будет удалено занятий: {len(lessons) - 1}")
    print("   Вы уверены? (yes/no): ", end='')
    
    # Для автоматического выполнения вводим "yes"
    confirm = "yes"  # Можно изменить на input() для интерактивного режима
    
    if confirm.lower() != 'yes':
        print("❌ Операция отменена")
        return
    
    # Удаляем все занятия кроме первого
    first_lesson_id = first_lesson.get('id')
    deleted_count = 0
    failed_count = 0
    
    print("\n🗑️  Удаление занятий...")
    for lesson in lessons:
        lesson_id = lesson.get('id')
        if lesson_id == first_lesson_id:
            print(f"   ⏭️  Пропускаем (первое занятие): {lesson.get('title')}")
            continue
        
        lesson_title = lesson.get('title', 'N/A')
        if delete_lesson(lesson_id, token):
            deleted_count += 1
            print(f"   ✅ Удалено: {lesson_title} ({lesson_id})")
        else:
            failed_count += 1
            print(f"   ❌ Ошибка удаления: {lesson_title} ({lesson_id})")
    
    print("\n" + "="*70)
    print("РЕЗУЛЬТАТЫ")
    print("="*70)
    print(f"✅ Сохранено: 1 занятие ({first_lesson.get('title')})")
    print(f"🗑️  Удалено: {deleted_count}")
    if failed_count > 0:
        print(f"❌ Ошибок: {failed_count}")
    print("="*70)

if __name__ == "__main__":
    main()
