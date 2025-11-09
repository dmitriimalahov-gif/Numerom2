#!/usr/bin/env python3
"""
Автоматическая версия скрипта создания урока с авто-логином
"""

import sys
import requests
from pathlib import Path

# Импортируем функции из основного скрипта
sys.path.insert(0, str(Path(__file__).parent))
from create_lesson_from_folder import (
    create_lesson, BACKEND_URL, BASE_DIR, LESSON_PLANETS
)

def get_token_via_login(email="admin@numerom.com", password="admin123"):
    """Получить токен через логин"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"email": email, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            
            # Сохраняем токен
            token_file = BASE_DIR / ".admin_token"
            token_file.write_text(token)
            
            print(f"✅ Токен получен и сохранён")
            return token
        else:
            print(f"❌ Ошибка авторизации: {response.status_code}")
            print(f"Ответ: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Ошибка получения токена: {e}")
        return None


def main():
    if len(sys.argv) < 2:
        print("Использование: python create_lesson_auto.py <номер_урока> [email] [password]")
        print("Например: python create_lesson_auto.py 1")
        print("Или: python create_lesson_auto.py 1 admin@numerom.com admin123")
        sys.exit(1)
    
    lesson_num = int(sys.argv[1])
    
    if lesson_num not in range(0, 10):
        print(f"❌ Номер урока должен быть от 0 до 9")
        sys.exit(1)
    
    # Получаем email и password из аргументов или используем дефолтные
    email = sys.argv[2] if len(sys.argv) > 2 else "admin@numerom.com"
    password = sys.argv[3] if len(sys.argv) > 3 else "admin123"
    
    print(f"\n🔐 Авторизация как {email}...")
    
    # Получаем токен
    token = get_token_via_login(email, password)
    
    if not token:
        print("\n❌ Не удалось получить токен. Проверьте логин и пароль.")
        sys.exit(1)
    
    # Создаём урок
    create_lesson(lesson_num, token)


if __name__ == "__main__":
    main()

