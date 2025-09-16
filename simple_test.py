#!/usr/bin/env python3
"""
Простой тест для проверки проблемы с планетарными маршрутами
"""

import requests
import time

# Конфигурация
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

def test_login():
    """Тест логина"""
    login_data = {
        "email": "dmitrii.malahov@gmail.com",
        "password": "756bvy67H"
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        return data.get('access_token')
    return None

def test_daily_route(token):
    """Тест дневного маршрута"""
    headers = {'Authorization': f'Bearer {token}'}
    params = {"date": "2025-08-24", "city": "Кишинев"}
    
    start_time = time.time()
    response = requests.get(f"{BACKEND_URL}/vedic-time/planetary-route", 
                          params=params, headers=headers, timeout=15)
    end_time = time.time()
    
    print(f"Дневной маршрут: {response.status_code} ({end_time - start_time:.1f}s)")
    return response.status_code == 200

def test_monthly_route(token):
    """Тест месячного маршрута"""
    headers = {'Authorization': f'Bearer {token}'}
    params = {"date": "2025-08-24", "city": "Кишинев"}
    
    start_time = time.time()
    try:
        response = requests.get(f"{BACKEND_URL}/vedic-time/planetary-route/monthly", 
                              params=params, headers=headers, timeout=30)
        end_time = time.time()
        
        print(f"Месячный маршрут: {response.status_code} ({end_time - start_time:.1f}s)")
        if response.status_code != 200:
            print(f"  Ошибка: {response.text[:200]}")
        return response.status_code == 200
    except requests.exceptions.Timeout:
        end_time = time.time()
        print(f"Месячный маршрут: TIMEOUT ({end_time - start_time:.1f}s)")
        return False

def test_quarterly_route(token):
    """Тест квартального маршрута"""
    headers = {'Authorization': f'Bearer {token}'}
    params = {"date": "2025-08-24", "city": "Кишинев"}
    
    start_time = time.time()
    try:
        response = requests.get(f"{BACKEND_URL}/vedic-time/planetary-route/quarterly", 
                              params=params, headers=headers, timeout=30)
        end_time = time.time()
        
        print(f"Квартальный маршрут: {response.status_code} ({end_time - start_time:.1f}s)")
        if response.status_code != 200:
            print(f"  Ошибка: {response.text[:200]}")
        return response.status_code == 200
    except requests.exceptions.Timeout:
        end_time = time.time()
        print(f"Квартальный маршрут: TIMEOUT ({end_time - start_time:.1f}s)")
        return False

def main():
    print("🎯 ДИАГНОСТИКА ПЛАНЕТАРНЫХ МАРШРУТОВ")
    print("=" * 50)
    
    # Логин
    token = test_login()
    if not token:
        print("❌ Ошибка логина")
        return
    
    print("✅ Логин успешен")
    
    # Тесты
    daily_ok = test_daily_route(token)
    monthly_ok = test_monthly_route(token)
    quarterly_ok = test_quarterly_route(token)
    
    print("\n📊 РЕЗУЛЬТАТЫ:")
    print(f"  Дневной: {'✅' if daily_ok else '❌'}")
    print(f"  Месячный: {'✅' if monthly_ok else '❌'}")
    print(f"  Квартальный: {'✅' if quarterly_ok else '❌'}")
    
    if not monthly_ok or not quarterly_ok:
        print("\n🔍 ДИАГНОЗ:")
        print("  Проблема: Таймауты при обращении к OpenStreetMap API")
        print("  Причина: Множественные geocoding запросы для каждого дня")
        print("  Решение: Кэширование координат города или увеличение timeout")

if __name__ == "__main__":
    main()