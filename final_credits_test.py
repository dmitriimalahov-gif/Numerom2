#!/usr/bin/env python3
"""
ФИНАЛЬНЫЙ ТЕСТ: Точная диагностика проблемы с кредитами
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"

def final_credits_test():
    session = requests.Session()
    
    # Login
    login_data = {
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    }
    
    response = session.post(f"{BACKEND_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print("❌ Не удалось войти в систему")
        return
    
    data = response.json()
    auth_token = data.get('access_token')
    session.headers.update({'Authorization': f'Bearer {auth_token}'})
    
    print("🎯 ФИНАЛЬНЫЙ ТЕСТ: Точная диагностика проблемы с кредитами")
    print("=" * 70)
    
    # Check current profile
    profile_response = session.get(f"{BACKEND_URL}/user/profile")
    if profile_response.status_code == 200:
        profile_data = profile_response.json()
        current_credits = profile_data.get('credits_remaining')
        current_subscription = profile_data.get('subscription_type')
        print(f"📊 Текущее состояние:")
        print(f"   Кредиты: {current_credits}")
        print(f"   Подписка: {current_subscription}")
        print(f"   Премиум: {profile_data.get('is_premium')}")
    else:
        print("❌ Не удалось получить профиль пользователя")
        return
    
    # Test the issue: monthly subscription behavior
    print(f"\n💳 ТЕСТИРОВАНИЕ МЕСЯЧНОЙ ПОДПИСКИ:")
    print(f"   Ожидание: кредиты должны УВЕЛИЧИТЬСЯ на 100")
    print(f"   Проблема: кредиты УСТАНАВЛИВАЮТСЯ в 100")
    
    payment_data = {
        "package_type": "monthly",
        "origin_url": "https://numerology-fix.preview.emergentagent.com"
    }
    
    response = session.post(f"{BACKEND_URL}/payments/checkout/session", json=payment_data)
    if response.status_code == 200:
        data = response.json()
        session_id = data.get('session_id')
        print(f"   ✅ Платежная сессия создана: {session_id[:20]}...")
        
        # Check payment status
        status_response = session.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"   ✅ Статус платежа: {status_data.get('payment_status')}")
            
            # Check profile after payment
            new_profile_response = session.get(f"{BACKEND_URL}/user/profile")
            if new_profile_response.status_code == 200:
                new_profile_data = new_profile_response.json()
                new_credits = new_profile_data.get('credits_remaining')
                new_subscription = new_profile_data.get('subscription_type')
                
                print(f"\n📊 Результат после платежа:")
                print(f"   Кредиты: {current_credits} → {new_credits}")
                print(f"   Подписка: {current_subscription} → {new_subscription}")
                
                # Analysis
                print(f"\n🔍 АНАЛИЗ ПРОБЛЕМЫ:")
                if new_credits == 100:
                    print(f"   ❌ ПРОБЛЕМА ПОДТВЕРЖДЕНА:")
                    print(f"      Месячная подписка УСТАНАВЛИВАЕТ кредиты в 100")
                    print(f"      Вместо ДОБАВЛЕНИЯ 100 к существующим {current_credits}")
                    print(f"      Пользователь ПОТЕРЯЛ {current_credits - 100} кредитов!")
                    
                    print(f"\n💡 ТЕХНИЧЕСКАЯ ПРИЧИНА:")
                    print(f"   В коде server.py строки 212-217:")
                    print("   await db.users.update_one({'id': user_id}, {'$set': {")
                    print("       'is_premium': True,")
                    print("       'subscription_type': 'monthly',")
                    print("       'subscription_expires_at': datetime.utcnow() + timedelta(days=30),")
                    print("       'credits_remaining': SUBSCRIPTION_CREDITS['monthly']  # ← ПРОБЛЕМА")
                    print("   }})")
                    print("   ")
                    print("   ДОЛЖНО БЫТЬ:")
                    print("   '$inc': {'credits_remaining': SUBSCRIPTION_CREDITS['monthly']}")
                    
                elif new_credits == current_credits + 100:
                    print(f"   ✅ ПРОБЛЕМА ИСПРАВЛЕНА:")
                    print(f"      Кредиты корректно увеличились на 100")
                else:
                    print(f"   ⚠️ НЕОЖИДАННОЕ ПОВЕДЕНИЕ:")
                    print(f"      Кредиты изменились на {new_credits - current_credits}")
                    
            else:
                print("   ❌ Не удалось получить обновленный профиль")
        else:
            print(f"   ❌ Ошибка проверки статуса: {status_response.status_code}")
    else:
        print(f"   ❌ Ошибка создания сессии: {response.status_code}")
    
    print(f"\n🏁 ЗАКЛЮЧЕНИЕ:")
    print(f"   Проблема в server.py, функция get_payment_status")
    print(f"   Строки 212-217 и 239-244 используют '$set' вместо '$inc'")
    print(f"   Это ПЕРЕЗАПИСЫВАЕТ кредиты вместо их ДОБАВЛЕНИЯ")

if __name__ == "__main__":
    final_credits_test()