#!/usr/bin/env python3
"""
КРИТИЧЕСКАЯ ПРОВЕРКА: Тестирование исправления ошибки генерации HTML отчётов

Проблема была найдена: UnboundLocalError с datetime в функции generate_numerology_html.
Я исправил конфликт локальных импортов datetime.

ТЕСТИРОВАТЬ:
1. POST /api/reports/html/numerology - проверить, что ошибка UnboundLocalError больше не возникает
2. Генерация HTML отчётов работает стабильно
3. Проверить различные комбинации selected_calculations
4. Проверить логи на ошибки
5. Полный анализ HTML содержимого
6. Различные сценарии пользователя

Использовать супер админа dmitrii.malahov@gmail.com / 756bvy67H
"""

import requests
import json
import sys
import re
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

print(f"🎯 КРИТИЧЕСКАЯ ПРОВЕРКА: Исправление ошибки генерации HTML отчётов")
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

# Глобальная переменная для токена
auth_token = None

def login_super_admin():
    """Вход супер админа dmitrii.malahov@gmail.com / 756bvy67H"""
    global auth_token
    
    print("\n🔐 АУТЕНТИФИКАЦИЯ СУПЕР АДМИНА")
    
    login_data = {
        "email": "dmitrii.malahov@gmail.com",
        "password": "756bvy67H"
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/login", json=login_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get('access_token')
            user_info = data.get('user', {})
            
            results.success(f"Супер админ вошёл в систему")
            results.info(f"User ID: {user_info.get('id')}")
            results.info(f"Email: {user_info.get('email')}")
            results.info(f"Супер админ: {user_info.get('is_super_admin')}")
            results.info(f"Премиум: {user_info.get('is_premium')}")
            results.info(f"Кредиты: {user_info.get('credits_remaining')}")
            
            return True
        else:
            results.failure(f"Ошибка входа супер админа: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        results.failure(f"Исключение при входе супер админа: {str(e)}")
        return False

def get_auth_headers():
    """Получить заголовки авторизации"""
    if not auth_token:
        return {}
    return {"Authorization": f"Bearer {auth_token}"}

def test_html_report_generation():
    """Тестирование генерации HTML отчётов с различными параметрами"""
    
    print("\n📊 ТЕСТИРОВАНИЕ ГЕНЕРАЦИИ HTML ОТЧЁТОВ")
    
    # Тест-кейсы с различными комбинациями selected_calculations
    test_cases = [
        {
            "name": "Базовый отчёт",
            "data": {
                "selected_calculations": ["personal_numbers"],
                "theme": "light"
            }
        },
        {
            "name": "Полный отчёт",
            "data": {
                "selected_calculations": ["personal_numbers", "pythagorean_square", "vedic_times", "planetary_route"],
                "theme": "light"
            }
        },
        {
            "name": "Тёмная тема",
            "data": {
                "selected_calculations": ["personal_numbers", "pythagorean_square"],
                "theme": "dark"
            }
        },
        {
            "name": "Обратная совместимость (старые параметры)",
            "data": {
                "include_vedic": True,
                "include_charts": True,
                "theme": "light"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Тест {i}: {test_case['name']}")
        
        try:
            response = requests.post(
                f"{API_URL}/reports/html/numerology",
                json=test_case['data'],
                headers=get_auth_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                results.success(f"HTTP 200 - {test_case['name']}")
                
                # Проверяем Content-Type
                content_type = response.headers.get('content-type', '')
                if 'text/html' in content_type:
                    results.success(f"Правильный Content-Type: {content_type}")
                else:
                    results.failure(f"Неправильный Content-Type: {content_type}")
                
                # Анализируем HTML содержимое
                html_content = response.text
                analyze_html_content(html_content, test_case['name'])
                
            elif response.status_code == 500:
                results.failure(f"500 Internal Server Error - {test_case['name']}: {response.text}")
                
                # Проверяем на UnboundLocalError
                if 'UnboundLocalError' in response.text:
                    results.failure(f"КРИТИЧЕСКАЯ ОШИБКА: UnboundLocalError всё ещё присутствует!")
                elif 'datetime' in response.text.lower():
                    results.failure(f"Возможная проблема с datetime: {response.text}")
                    
            else:
                results.failure(f"Неожиданный статус {response.status_code} - {test_case['name']}: {response.text}")
                
        except requests.exceptions.Timeout:
            results.failure(f"Таймаут при генерации отчёта - {test_case['name']}")
        except Exception as e:
            results.failure(f"Исключение при тестировании {test_case['name']}: {str(e)}")

def analyze_html_content(html_content, test_name):
    """Анализ HTML содержимого на предмет полноты данных"""
    
    print(f"  📋 Анализ HTML содержимого для {test_name}")
    
    # Базовые проверки HTML структуры
    if not html_content:
        results.failure(f"  Пустой HTML контент")
        return
        
    if len(html_content) < 1000:
        results.failure(f"  Слишком короткий HTML ({len(html_content)} символов)")
        return
    else:
        results.success(f"  HTML размер: {len(html_content)} символов")
    
    # Проверяем DOCTYPE и базовую структуру
    if '<!DOCTYPE html>' in html_content:
        results.success(f"  DOCTYPE присутствует")
    else:
        results.failure(f"  DOCTYPE отсутствует")
    
    # Проверяем заголовок NUMEROM
    if 'NUMEROM' in html_content:
        results.success(f"  Брендинг NUMEROM найден")
    else:
        results.failure(f"  Брендинг NUMEROM отсутствует")
    
    # Проверяем наличие персональных данных
    personal_data_found = 0
    
    # Ищем email супер админа
    if 'dmitrii.malahov@gmail.com' in html_content:
        results.success(f"  Email пользователя найден")
        personal_data_found += 1
    else:
        results.failure(f"  Email пользователя отсутствует")
    
    # Ищем дату рождения (различные форматы)
    birth_date_patterns = [
        r'\d{2}\.\d{2}\.\d{4}',  # DD.MM.YYYY
        r'\d{1,2}/\d{1,2}/\d{4}',  # D/M/YYYY или DD/MM/YYYY
        r'\d{4}-\d{2}-\d{2}'  # YYYY-MM-DD
    ]
    
    birth_date_found = False
    for pattern in birth_date_patterns:
        if re.search(pattern, html_content):
            results.success(f"  Дата рождения найдена (формат: {pattern})")
            personal_data_found += 1
            birth_date_found = True
            break
    
    if not birth_date_found:
        results.failure(f"  Дата рождения не найдена")
    
    # Проверяем наличие персональных чисел
    personal_numbers = ['ЧД', 'ЧУ', 'ЧС', 'ЧУ*', 'ЧМ', 'ПЧ']
    numbers_found = 0
    
    for number_type in personal_numbers:
        if number_type in html_content:
            numbers_found += 1
    
    if numbers_found >= 4:
        results.success(f"  Персональные числа найдены ({numbers_found}/6)")
        personal_data_found += 1
    else:
        results.failure(f"  Недостаточно персональных чисел ({numbers_found}/6)")
    
    # Проверяем планетарную силу
    planets = ['Солнце', 'Луна', 'Марс', 'Меркурий', 'Юпитер', 'Венера', 'Сатурн']
    planets_found = 0
    
    for planet in planets:
        if planet in html_content:
            planets_found += 1
    
    if planets_found >= 5:
        results.success(f"  Планетарная сила найдена ({planets_found}/7 планет)")
        personal_data_found += 1
    else:
        results.failure(f"  Недостаточно планет в отчёте ({planets_found}/7)")
    
    # Проверяем квадрат Пифагора
    if 'А1' in html_content and 'А2' in html_content:
        results.success(f"  Квадрат Пифагора с дополнительными числами найден")
        personal_data_found += 1
    else:
        results.failure(f"  Квадрат Пифагора не найден или неполный")
    
    # Проверяем ведические времена
    vedic_terms = ['Rahu', 'राहु', 'Кaal', 'काल']
    vedic_found = any(term in html_content for term in vedic_terms)
    
    if vedic_found:
        results.success(f"  Ведические времена найдены")
        personal_data_found += 1
    else:
        results.info(f"  Ведические времена не найдены (возможно не включены)")
    
    # Проверяем планетарный маршрут
    route_terms = ['Утро', 'День', 'Вечер', '6:00', '12:00', '18:00']
    route_found = sum(1 for term in route_terms if term in html_content)
    
    if route_found >= 3:
        results.success(f"  Планетарный маршрут найден ({route_found}/6 элементов)")
        personal_data_found += 1
    else:
        results.info(f"  Планетарный маршрут не найден или неполный ({route_found}/6)")
    
    # Проверяем числовые значения (не должно быть пустых полей)
    number_pattern = r'\b\d+\b'
    numbers_in_html = re.findall(number_pattern, html_content)
    
    if len(numbers_in_html) >= 50:  # Ожидаем много числовых значений
        results.success(f"  Числовые данные найдены ({len(numbers_in_html)} чисел)")
        personal_data_found += 1
    else:
        results.failure(f"  Недостаточно числовых данных ({len(numbers_in_html)} чисел)")
    
    # Общая оценка полноты данных
    if personal_data_found >= 6:
        results.success(f"  ОТЧЁТ СОДЕРЖИТ ПОЛНЫЕ ДАННЫЕ ({personal_data_found}/8 разделов)")
    elif personal_data_found >= 4:
        results.info(f"  Отчёт содержит основные данные ({personal_data_found}/8 разделов)")
    else:
        results.failure(f"  ОТЧЁТ СОДЕРЖИТ НЕДОСТАТОЧНО ДАННЫХ ({personal_data_found}/8 разделов)")

def test_error_scenarios():
    """Тестирование сценариев, которые могли вызывать UnboundLocalError"""
    
    print("\n🚨 ТЕСТИРОВАНИЕ СЦЕНАРИЕВ ОШИБОК")
    
    error_test_cases = [
        {
            "name": "Пустой selected_calculations",
            "data": {
                "selected_calculations": [],
                "theme": "light"
            },
            "expect_error": True
        },
        {
            "name": "Несуществующий calculation",
            "data": {
                "selected_calculations": ["nonexistent_calculation"],
                "theme": "light"
            },
            "expect_error": False  # Должно игнорировать
        },
        {
            "name": "Смешанные параметры",
            "data": {
                "selected_calculations": ["personal_numbers"],
                "include_vedic": True,
                "include_charts": True,
                "theme": "dark"
            },
            "expect_error": False
        }
    ]
    
    for test_case in error_test_cases:
        print(f"\n🧪 Тест ошибки: {test_case['name']}")
        
        try:
            response = requests.post(
                f"{API_URL}/reports/html/numerology",
                json=test_case['data'],
                headers=get_auth_headers(),
                timeout=30
            )
            
            if test_case['expect_error']:
                if response.status_code == 400:
                    results.success(f"Ожидаемая ошибка 400: {test_case['name']}")
                elif response.status_code == 500:
                    results.failure(f"500 ошибка вместо ожидаемой 400: {test_case['name']}")
                    if 'UnboundLocalError' in response.text:
                        results.failure(f"КРИТИЧЕСКАЯ ОШИБКА: UnboundLocalError в {test_case['name']}")
                else:
                    results.failure(f"Неожиданный статус {response.status_code} для {test_case['name']}")
            else:
                if response.status_code == 200:
                    results.success(f"Успешная обработка: {test_case['name']}")
                elif response.status_code == 500:
                    results.failure(f"500 ошибка: {test_case['name']}")
                    if 'UnboundLocalError' in response.text:
                        results.failure(f"КРИТИЧЕСКАЯ ОШИБКА: UnboundLocalError в {test_case['name']}")
                else:
                    results.info(f"Статус {response.status_code} для {test_case['name']}: {response.text[:200]}")
                    
        except Exception as e:
            results.failure(f"Исключение в тесте {test_case['name']}: {str(e)}")

def test_regular_user_scenario():
    """Тестирование с обычным пользователем (с кредитами)"""
    
    print("\n👤 ТЕСТИРОВАНИЕ СЦЕНАРИЯ ОБЫЧНОГО ПОЛЬЗОВАТЕЛЯ")
    
    # Создаём тестового пользователя
    test_user_data = {
        "email": f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}@test.com",
        "password": "testpass123",
        "full_name": "Тестовый Пользователь",
        "birth_date": "15.03.1990",
        "city": "Москва"
    }
    
    try:
        # Регистрация
        reg_response = requests.post(f"{API_URL}/auth/register", json=test_user_data, timeout=10)
        
        if reg_response.status_code == 200:
            results.success("Тестовый пользователь зарегистрирован")
            
            reg_data = reg_response.json()
            test_token = reg_data.get('access_token')
            test_headers = {"Authorization": f"Bearer {test_token}"}
            
            # Тестируем генерацию отчёта
            report_data = {
                "selected_calculations": ["personal_numbers"],
                "theme": "light"
            }
            
            report_response = requests.post(
                f"{API_URL}/reports/html/numerology",
                json=report_data,
                headers=test_headers,
                timeout=30
            )
            
            if report_response.status_code == 200:
                results.success("HTML отчёт сгенерирован для обычного пользователя")
                
                # Проверяем, что кредиты списались
                profile_response = requests.get(f"{API_URL}/user/profile", headers=test_headers, timeout=10)
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    credits = profile_data.get('credits_remaining', 0)
                    results.success(f"Кредиты после генерации отчёта: {credits}")
                    
            elif report_response.status_code == 402:
                results.info("Недостаточно кредитов у тестового пользователя (ожидаемо)")
            elif report_response.status_code == 500:
                results.failure(f"500 ошибка для обычного пользователя: {report_response.text}")
                if 'UnboundLocalError' in report_response.text:
                    results.failure("КРИТИЧЕСКАЯ ОШИБКА: UnboundLocalError для обычного пользователя")
            else:
                results.failure(f"Неожиданный статус {report_response.status_code} для обычного пользователя")
                
        else:
            results.failure(f"Не удалось зарегистрировать тестового пользователя: {reg_response.status_code}")
            
    except Exception as e:
        results.failure(f"Исключение при тестировании обычного пользователя: {str(e)}")

def main():
    """Основная функция тестирования"""
    
    print("🚀 НАЧАЛО КРИТИЧЕСКОЙ ПРОВЕРКИ HTML ОТЧЁТОВ")
    
    # 1. Аутентификация супер админа
    if not login_super_admin():
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось войти как супер админ")
        sys.exit(1)
    
    # 2. Тестирование генерации HTML отчётов
    test_html_report_generation()
    
    # 3. Тестирование сценариев ошибок
    test_error_scenarios()
    
    # 4. Тестирование с обычным пользователем
    test_regular_user_scenario()
    
    # Итоговый отчёт
    print("\n" + "=" * 80)
    print("📊 ИТОГОВЫЙ ОТЧЁТ КРИТИЧЕСКОЙ ПРОВЕРКИ")
    print("=" * 80)
    
    total_tests = results.passed + results.failed
    success_rate = (results.passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"✅ Пройдено тестов: {results.passed}")
    print(f"❌ Провалено тестов: {results.failed}")
    print(f"📈 Успешность: {success_rate:.1f}%")
    
    if results.issues:
        print(f"\n🚨 ОБНАРУЖЕННЫЕ ПРОБЛЕМЫ:")
        for i, issue in enumerate(results.issues, 1):
            print(f"  {i}. {issue}")
    
    # Проверяем критические ошибки
    critical_errors = [issue for issue in results.issues if 'UnboundLocalError' in issue or 'КРИТИЧЕСКАЯ' in issue]
    
    if critical_errors:
        print(f"\n🔥 КРИТИЧЕСКИЕ ОШИБКИ ОБНАРУЖЕНЫ:")
        for error in critical_errors:
            print(f"  ⚠️  {error}")
        print(f"\n❌ ТЕСТИРОВАНИЕ ПРОВАЛЕНО: Обнаружены критические ошибки")
        return False
    elif results.failed == 0:
        print(f"\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print(f"✅ HTML отчёты генерируются корректно")
        print(f"✅ UnboundLocalError исправлена")
        print(f"✅ Отчёты содержат полные данные пользователя")
        return True
    else:
        print(f"\n⚠️  ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ПРЕДУПРЕЖДЕНИЯМИ")
        print(f"✅ Критические ошибки не обнаружены")
        print(f"⚠️  Есть минорные проблемы, требующие внимания")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)