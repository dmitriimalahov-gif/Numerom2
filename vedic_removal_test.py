#!/usr/bin/env python3
"""
ПРОВЕРКА ИЗМЕНЕНИЙ: Тестирование после удаления ведической матрицы из NUMEROM

Проверяем:
1. GET /api/reports/available-calculations - убедиться что vedic_numerology больше нет в списке
2. POST /api/reports/html/numerology - убедиться что отчёты генерируются без ошибок
3. Проверить что в систему не передаются старые цены в рублях
"""

import requests
import json
import sys
from datetime import datetime

# Получаем URL бэкенда из .env файла
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=')[1].strip()
    except:
        pass
    return "http://localhost:8001"

BASE_URL = get_backend_url()
API_URL = f"{BASE_URL}/api"

print(f"🎯 ПРОВЕРКА ИЗМЕНЕНИЙ: Удаление ведической матрицы из NUMEROM")
print(f"Backend URL: {BASE_URL}")
print(f"API URL: {API_URL}")
print("=" * 80)

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.issues = []
        
    def success(self, message):
        print(f"✅ {message}")
        self.passed += 1
        
    def failure(self, message):
        print(f"❌ {message}")
        self.failed += 1
        self.issues.append(message)
        
    def info(self, message):
        print(f"ℹ️  {message}")

results = TestResults()

# Данные супер админа для тестирования
SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"

def login_super_admin():
    """Вход супер админа"""
    try:
        login_data = {
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }
        
        response = requests.post(f"{API_URL}/auth/login", json=login_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            user_info = data.get('user', {})
            
            results.success(f"Супер админ вход успешен: {user_info.get('email')} (кредиты: {user_info.get('credits_remaining', 0)})")
            return token
        else:
            results.failure(f"Ошибка входа супер админа: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        results.failure(f"Исключение при входе супер админа: {str(e)}")
        return None

def test_available_calculations(token):
    """Тест 1: Проверка доступных расчётов - vedic_numerology должен отсутствовать"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_URL}/reports/available-calculations", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            available_calculations = data.get('available_calculations', {})
            
            # Проверяем что vedic_numerology отсутствует
            if 'vedic_numerology' in available_calculations:
                results.failure("vedic_numerology всё ещё присутствует в доступных расчётах!")
                return False
            else:
                results.success("vedic_numerology корректно удалён из доступных расчётов")
            
            # Проверяем что остальные расчёты присутствуют
            expected_calculations = [
                'personal_numbers', 'pythagorean_square', 'vedic_times', 
                'planetary_route', 'compatibility'
            ]
            
            missing_calculations = []
            for calc in expected_calculations:
                if calc not in available_calculations:
                    missing_calculations.append(calc)
            
            if missing_calculations:
                results.failure(f"Отсутствуют ожидаемые расчёты: {missing_calculations}")
                return False
            else:
                results.success(f"Все ожидаемые расчёты присутствуют: {expected_calculations}")
            
            results.info(f"Всего доступных расчётов: {len(available_calculations)}")
            for calc_id, calc_info in available_calculations.items():
                results.info(f"  - {calc_id}: {calc_info.get('name', 'Без названия')}")
            
            return True
            
        else:
            results.failure(f"Ошибка получения доступных расчётов: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        results.failure(f"Исключение при тестировании доступных расчётов: {str(e)}")
        return False

def test_html_report_generation(token):
    """Тест 2: Генерация HTML отчётов без ошибок после удаления vedic_numerology"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Тестируем различные комбинации расчётов
        test_cases = [
            {
                "name": "Базовые расчёты",
                "selected_calculations": ["personal_numbers", "pythagorean_square"]
            },
            {
                "name": "Ведические времена",
                "selected_calculations": ["personal_numbers", "vedic_times"]
            },
            {
                "name": "Планетарный маршрут",
                "selected_calculations": ["personal_numbers", "planetary_route"]
            },
            {
                "name": "Полный набор",
                "selected_calculations": ["personal_numbers", "pythagorean_square", "vedic_times", "planetary_route"]
            }
        ]
        
        all_passed = True
        
        for test_case in test_cases:
            try:
                report_data = {
                    "selected_calculations": test_case["selected_calculations"],
                    "theme": "light"
                }
                
                response = requests.post(f"{API_URL}/reports/html/numerology", 
                                       json=report_data, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    html_content = response.text
                    
                    # Проверяем что HTML не пустой
                    if len(html_content) < 1000:
                        results.failure(f"{test_case['name']}: HTML слишком короткий ({len(html_content)} символов)")
                        all_passed = False
                        continue
                    
                    # Проверяем что HTML содержит базовую структуру
                    if "<!DOCTYPE html>" not in html_content:
                        results.failure(f"{test_case['name']}: HTML не содержит DOCTYPE")
                        all_passed = False
                        continue
                    
                    if "NUMEROM" not in html_content:
                        results.failure(f"{test_case['name']}: HTML не содержит брендинг NUMEROM")
                        all_passed = False
                        continue
                    
                    # Проверяем что нет упоминаний vedic_numerology или ведической матрицы
                    if "vedic_numerology" in html_content.lower():
                        results.failure(f"{test_case['name']}: HTML содержит упоминания vedic_numerology")
                        all_passed = False
                        continue
                    
                    results.success(f"{test_case['name']}: HTML отчёт сгенерирован корректно ({len(html_content)} символов)")
                    
                else:
                    results.failure(f"{test_case['name']}: Ошибка генерации HTML: {response.status_code} - {response.text}")
                    all_passed = False
                    
            except Exception as e:
                results.failure(f"{test_case['name']}: Исключение при генерации HTML: {str(e)}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        results.failure(f"Исключение при тестировании генерации HTML: {str(e)}")
        return False

def test_pricing_in_euros(token):
    """Тест 3: Проверка что цены указаны в евро, а не в рублях"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Тестируем создание checkout сессии для каждого пакета
        packages = ['one_time', 'monthly', 'annual']
        expected_prices = {
            'one_time': 0.96,
            'monthly': 9.99, 
            'annual': 66.59
        }
        
        all_passed = True
        
        for package in packages:
            try:
                payment_data = {
                    "package_type": package,
                    "origin_url": BASE_URL
                }
                
                response = requests.post(f"{API_URL}/payments/checkout/session", 
                                       json=payment_data, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    session_id = data.get('session_id')
                    
                    if session_id:
                        # Проверяем статус платежа для получения информации о цене
                        status_response = requests.get(f"{API_URL}/payments/checkout/status/{session_id}", 
                                                     headers=headers, timeout=10)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            currency = status_data.get('currency', '').lower()
                            
                            if currency != 'eur':
                                results.failure(f"Пакет {package}: неправильная валюта '{currency}', ожидается 'eur'")
                                all_passed = False
                            else:
                                results.success(f"Пакет {package}: валюта корректна (EUR)")
                        else:
                            results.failure(f"Пакет {package}: ошибка получения статуса платежа")
                            all_passed = False
                    else:
                        results.failure(f"Пакет {package}: не получен session_id")
                        all_passed = False
                else:
                    results.failure(f"Пакет {package}: ошибка создания checkout сессии: {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                results.failure(f"Пакет {package}: исключение при тестировании цен: {str(e)}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        results.failure(f"Исключение при тестировании цен: {str(e)}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Начинаем тестирование изменений после удаления ведической матрицы...")
    print()
    
    # Шаг 1: Вход супер админа
    print("1️⃣ АУТЕНТИФИКАЦИЯ СУПЕР АДМИНА")
    print("-" * 40)
    token = login_super_admin()
    if not token:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось войти как супер админ")
        sys.exit(1)
    print()
    
    # Шаг 2: Тест доступных расчётов
    print("2️⃣ ТЕСТ ДОСТУПНЫХ РАСЧЁТОВ")
    print("-" * 40)
    test_available_calculations(token)
    print()
    
    # Шаг 3: Тест генерации HTML отчётов
    print("3️⃣ ТЕСТ ГЕНЕРАЦИИ HTML ОТЧЁТОВ")
    print("-" * 40)
    test_html_report_generation(token)
    print()
    
    # Шаг 4: Тест цен в евро
    print("4️⃣ ТЕСТ ЦЕН В ЕВРО")
    print("-" * 40)
    test_pricing_in_euros(token)
    print()
    
    # Итоговый отчёт
    print("=" * 80)
    print("📊 ИТОГОВЫЙ ОТЧЁТ")
    print(f"✅ Успешно: {results.passed}")
    print(f"❌ Провалено: {results.failed}")
    print(f"📈 Успешность: {results.passed/(results.passed + results.failed)*100:.1f}%")
    
    if results.issues:
        print("\n🚨 ОБНАРУЖЕННЫЕ ПРОБЛЕМЫ:")
        for i, issue in enumerate(results.issues, 1):
            print(f"{i}. {issue}")
    
    if results.failed == 0:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Удаление ведической матрицы выполнено корректно.")
        return True
    else:
        print(f"\n⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ: {results.failed} тестов провалено")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)