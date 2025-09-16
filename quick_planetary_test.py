#!/usr/bin/env python3
"""
Быстрое тестирование планетарных маршрутов
"""

import requests
import json

# Конфигурация
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"

def authenticate():
    """Аутентификация"""
    login_data = {
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        print(f"✅ Аутентификация успешна")
        return token
    else:
        print(f"❌ Ошибка аутентификации: {response.status_code}")
        return None

def test_endpoint(token, endpoint, params):
    """Тестирование конкретного endpoint"""
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        print(f"\n🔍 Тестирование: {endpoint}")
        print(f"   Параметры: {params}")
        
        response = requests.get(f"{BACKEND_URL}{endpoint}", params=params, headers=headers, timeout=10)
        
        print(f"   Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ УСПЕХ")
            
            # Показываем ключевые поля
            if 'period' in data:
                print(f"   📅 Период: {data.get('period')}")
            if 'city' in data:
                print(f"   🏙️ Город: {data.get('city')}")
            if 'total_days' in data:
                print(f"   📊 Дней: {data.get('total_days')}")
            if 'daily_schedule' in data:
                schedule = data.get('daily_schedule', [])
                print(f"   📋 Расписаний: {len(schedule)}")
                
            return True
        else:
            print(f"   ❌ ОШИБКА: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   📝 Детали: {error_data.get('detail', 'N/A')}")
            except:
                print(f"   📝 Ответ: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ⏱️ ТАЙМАУТ (>10 сек)")
        return False
    except Exception as e:
        print(f"   ❌ ИСКЛЮЧЕНИЕ: {e}")
        return False

def main():
    print("🎯 БЫСТРОЕ ТЕСТИРОВАНИЕ ПЛАНЕТАРНЫХ МАРШРУТОВ")
    print("=" * 60)
    
    # Аутентификация
    token = authenticate()
    if not token:
        return
    
    # Тестовые параметры из review request
    test_params = {"date": "2025-08-24", "city": "Кишинев"}
    
    # Тесты
    results = {}
    
    # 1. Дневной маршрут
    results['daily'] = test_endpoint(token, "/vedic-time/planetary-route", test_params)
    
    # 2. Месячный маршрут
    results['monthly'] = test_endpoint(token, "/vedic-time/planetary-route/monthly", test_params)
    
    # 3. Квартальный маршрут  
    results['quarterly'] = test_endpoint(token, "/vedic-time/planetary-route/quarterly", test_params)
    
    # Итоги
    print(f"\n" + "=" * 60)
    print(f"📊 РЕЗУЛЬТАТЫ:")
    print(f"   📅 Дневной: {'✅' if results['daily'] else '❌'}")
    print(f"   🗓️ Месячный: {'✅' if results['monthly'] else '❌'}")
    print(f"   📆 Квартальный: {'✅' if results['quarterly'] else '❌'}")
    
    # Проверяем критические проблемы
    critical_issues = []
    if not results['monthly']:
        critical_issues.append("Месячный планетарный маршрут")
    if not results['quarterly']:
        critical_issues.append("Квартальный планетарный маршрут")
    
    if critical_issues:
        print(f"\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ:")
        for issue in critical_issues:
            print(f"   ❌ {issue}")
    else:
        print(f"\n🎉 ВСЕ МАРШРУТЫ РАБОТАЮТ!")

if __name__ == "__main__":
    main()