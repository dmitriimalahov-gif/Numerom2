#!/usr/bin/env python3
"""
Автоматическое получение токена и запуск создания всех занятий
"""
import sys
import requests
import subprocess

BACKEND_URL = "http://localhost:8000"
SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"

def get_admin_token():
    """Получает токен администратора через API"""
    try:
        print("🔐 Получение токена администратора...")
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json={
                "email": SUPER_ADMIN_EMAIL,
                "password": SUPER_ADMIN_PASSWORD
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            if token:
                print(f"✅ Токен получен успешно!")
                return token
            else:
                print("❌ Токен не найден в ответе")
                return None
        else:
            print(f"❌ Ошибка входа: {response.status_code}")
            print(f"   Ответ: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Ошибка при получении токена: {str(e)}")
        return None

def main():
    print("="*70)
    print("АВТОМАТИЧЕСКОЕ СОЗДАНИЕ ВСЕХ ЗАНЯТИЙ")
    print("="*70)
    
    # Получаем токен
    token = get_admin_token()
    
    if not token:
        print("\n❌ Не удалось получить токен администратора")
        print("Проверьте, что:")
        print("1. Backend запущен на http://localhost:8000")
        print("2. Суперадминистратор создан в БД")
        sys.exit(1)
    
    # Запускаем скрипт создания занятий
    print("\n🚀 Запуск создания всех занятий...\n")
    try:
        result = subprocess.run(
            [sys.executable, "create_all_lessons.py", token],
            check=False,
            capture_output=False
        )
        sys.exit(result.returncode)
    except Exception as e:
        print(f"\n❌ Ошибка при запуске скрипта: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
