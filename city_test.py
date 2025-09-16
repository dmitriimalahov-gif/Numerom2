#!/usr/bin/env python3
"""
Тест с разными городами
"""

import requests
import time

BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

def test_login():
    login_data = {"email": "dmitrii.malahov@gmail.com", "password": "756bvy67H"}
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json().get('access_token')
    return None

def test_monthly_with_city(token, city):
    headers = {'Authorization': f'Bearer {token}'}
    params = {"date": "2025-08-24", "city": city}
    
    start_time = time.time()
    try:
        response = requests.get(f"{BACKEND_URL}/vedic-time/planetary-route/monthly", 
                              params=params, headers=headers, timeout=20)
        end_time = time.time()
        
        print(f"{city}: {response.status_code} ({end_time - start_time:.1f}s)")
        return response.status_code == 200
    except requests.exceptions.Timeout:
        end_time = time.time()
        print(f"{city}: TIMEOUT ({end_time - start_time:.1f}s)")
        return False

def main():
    print("🌍 ТЕСТ С РАЗНЫМИ ГОРОДАМИ")
    print("=" * 40)
    
    token = test_login()
    if not token:
        print("❌ Ошибка логина")
        return
    
    cities = ["Кишинев", "Москва", "Киев", "Минск"]
    
    for city in cities:
        test_monthly_with_city(token, city)

if __name__ == "__main__":
    main()