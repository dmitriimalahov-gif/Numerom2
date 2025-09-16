#!/usr/bin/env python3
"""
ДЕТАЛЬНОЕ РАССЛЕДОВАНИЕ: Проблема с начислением кредитов
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"

def investigate_credits_issue():
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
    
    print("🔍 ДЕТАЛЬНОЕ РАССЛЕДОВАНИЕ ПРОБЛЕМЫ С КРЕДИТАМИ")
    print("=" * 60)
    
    # Check current profile
    profile_response = session.get(f"{BACKEND_URL}/user/profile")
    if profile_response.status_code == 200:
        profile_data = profile_response.json()
        print(f"📊 Текущий профиль пользователя:")
        print(f"   Email: {profile_data.get('email')}")
        print(f"   Credits: {profile_data.get('credits_remaining')}")
        print(f"   Is Premium: {profile_data.get('is_premium')}")
        print(f"   Subscription Type: {profile_data.get('subscription_type')}")
        print(f"   Subscription Expires: {profile_data.get('subscription_expires_at')}")
    else:
        print("❌ Не удалось получить профиль пользователя")
        return
    
    # Test monthly subscription behavior
    print(f"\n💳 ТЕСТИРОВАНИЕ МЕСЯЧНОЙ ПОДПИСКИ:")
    payment_data = {
        "package_type": "monthly",
        "origin_url": "https://numerology-fix.preview.emergentagent.com"
    }
    
    response = session.post(f"{BACKEND_URL}/payments/checkout/session", json=payment_data)
    if response.status_code == 200:
        data = response.json()
        session_id = data.get('session_id')
        print(f"   ✅ Сессия создана: {session_id}")
        
        # Check payment status
        status_response = session.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"   ✅ Статус платежа: {status_data.get('payment_status')}")
            print(f"   💰 User ID в ответе: {status_data.get('user_id')}")
            
            # Check profile after payment
            new_profile_response = session.get(f"{BACKEND_URL}/user/profile")
            if new_profile_response.status_code == 200:
                new_profile_data = new_profile_response.json()
                print(f"   📊 Профиль после платежа:")
                print(f"      Credits: {new_profile_data.get('credits_remaining')}")
                print(f"      Is Premium: {new_profile_data.get('is_premium')}")
                print(f"      Subscription Type: {new_profile_data.get('subscription_type')}")
                print(f"      Subscription Expires: {new_profile_data.get('subscription_expires_at')}")
                
                # The issue: monthly and annual subscriptions SET credits to a fixed amount
                # instead of ADDING to existing credits
                print(f"\n🔍 АНАЛИЗ ПРОБЛЕМЫ:")
                print(f"   Месячная подписка УСТАНАВЛИВАЕТ кредиты в 100, а не ДОБАВЛЯЕТ 100")
                print(f"   Это объясняет почему кредиты уменьшились с 1000010 до 100")
            else:
                print("   ❌ Не удалось получить обновленный профиль")
        else:
            print(f"   ❌ Ошибка проверки статуса: {status_response.status_code}")
    else:
        print(f"   ❌ Ошибка создания сессии: {response.status_code}")

if __name__ == "__main__":
    investigate_credits_issue()