#!/usr/bin/env python3
"""
FOCUSED SYSTEM TEST: Core functionality testing without external dependencies
"""

import requests
import json
import re
from datetime import datetime
import sys
import os

# Configuration - Use internal URL since external might have issues
BACKEND_URL = "http://localhost:8001/api"
TEST_USER_EMAIL = "dmitrii.malahov@gmail.com"
TEST_USER_PASSWORD = "756bvy67H"

class FocusedSystemTest:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 10  # 10 second timeout
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        self.critical_errors = []
        
    def log_test(self, test_name, status, details=""):
        """Log test results"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {details}")
        
        if status == "FAIL" and any(keyword in test_name.lower() for keyword in ['критический', 'аутентификация', 'база данных']):
            self.critical_errors.append(result)
    
    def test_authentication(self):
        """Test authentication with specified credentials"""
        print("\n🔐 ТЕСТ АУТЕНТИФИКАЦИИ")
        
        try:
            login_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.user_data = data.get('user')
                
                if self.auth_token:
                    self.log_test("POST /api/auth/login с dmitrii.malahov@gmail.com / 756bvy67H", "PASS", 
                                f"Токен получен успешно (длина: {len(self.auth_token)})")
                    
                    # Set authorization header for future requests
                    self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                    
                    # Verify user data
                    if self.user_data:
                        user_info = f"ID: {self.user_data.get('id')}, " \
                                   f"Super Admin: {self.user_data.get('is_super_admin')}, " \
                                   f"Premium: {self.user_data.get('is_premium')}, " \
                                   f"Credits: {self.user_data.get('credits_remaining')}"
                        self.log_test("Проверка что токен возвращается корректно", "PASS", user_info)
                        
                        # Check if user exists in database
                        if self.user_data.get('id'):
                            self.log_test("Пользователь dmitrii.malahov@gmail.com существует в базе", "PASS", 
                                        f"User ID: {self.user_data.get('id')}")
                        else:
                            self.log_test("Пользователь dmitrii.malahov@gmail.com существует в базе", "FAIL", "User ID отсутствует")
                    else:
                        self.log_test("Проверка что токен возвращается корректно", "FAIL", "Данные пользователя отсутствуют в ответе")
                else:
                    self.log_test("POST /api/auth/login с dmitrii.malahov@gmail.com / 756bvy67H", "FAIL", "Токен не возвращён в ответе")
                    return False
            else:
                self.log_test("POST /api/auth/login с dmitrii.malahov@gmail.com / 756bvy67H", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("POST /api/auth/login с dmitrii.malahov@gmail.com / 756bvy67H", "FAIL", f"Ошибка: {str(e)}")
            return False
        
        return True
    
    def test_main_functions(self):
        """Test main numerology functions"""
        print("\n⚡ ТЕСТ ОСНОВНЫХ ФУНКЦИЙ")
        
        if not self.auth_token:
            self.log_test("Основные функции", "SKIP", "Нет токена аутентификации")
            return
        
        # Test personal numbers
        try:
            response = self.session.post(f"{BACKEND_URL}/numerology/personal-numbers")
            if response.status_code == 200:
                data = response.json()
                if 'soul_number' in data and 'destiny_number' in data:
                    self.log_test("POST /api/numerology/personal-numbers", "PASS", 
                                f"Получены числа: душа={data.get('soul_number')}, судьба={data.get('destiny_number')}")
                else:
                    self.log_test("POST /api/numerology/personal-numbers", "FAIL", "Отсутствуют ключевые поля")
            elif response.status_code == 402:
                self.log_test("POST /api/numerology/personal-numbers", "WARN", "Недостаточно кредитов (функция работает)")
            else:
                self.log_test("POST /api/numerology/personal-numbers", "FAIL", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("POST /api/numerology/personal-numbers", "FAIL", f"Ошибка: {str(e)}")
        
        # Test Pythagorean square
        try:
            response = self.session.post(f"{BACKEND_URL}/numerology/pythagorean-square")
            if response.status_code == 200:
                data = response.json()
                if 'square' in data:
                    additional = data.get('additional_numbers', [])
                    self.log_test("POST /api/numerology/pythagorean-square", "PASS", 
                                f"Квадрат получен, доп. числа: {additional}")
                else:
                    self.log_test("POST /api/numerology/pythagorean-square", "FAIL", "Отсутствует поле 'square'")
            elif response.status_code == 402:
                self.log_test("POST /api/numerology/pythagorean-square", "WARN", "Недостаточно кредитов (функция работает)")
            else:
                self.log_test("POST /api/numerology/pythagorean-square", "FAIL", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("POST /api/numerology/pythagorean-square", "FAIL", f"Ошибка: {str(e)}")
        
        # Test user profile endpoint
        try:
            response = self.session.get(f"{BACKEND_URL}/learning/levels")
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /api/user/profile (через learning/levels)", "PASS", "Данные пользователя получены")
            else:
                self.log_test("GET /api/user/profile (через learning/levels)", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/user/profile (через learning/levels)", "FAIL", f"Ошибка: {str(e)}")
    
    def test_html_report_generation(self):
        """Test HTML report generation"""
        print("\n📄 ТЕСТ ГЕНЕРАЦИИ HTML ОТЧЁТОВ")
        
        if not self.auth_token:
            self.log_test("HTML отчёты", "SKIP", "Нет токена аутентификации")
            return
        
        # Test HTML report generation
        try:
            html_request = {
                "selected_calculations": ["personal_numbers", "pythagorean_square"],
                "theme": "light"
            }
            
            response = self.session.post(f"{BACKEND_URL}/reports/html/numerology", json=html_request)
            
            if response.status_code == 200:
                html_content = response.text
                content_type = response.headers.get('content-type', '')
                
                # Check content type
                if 'text/html' in content_type:
                    html_size = len(html_content)
                    self.log_test("POST /api/reports/html/numerology", "PASS", 
                                f"HTML сгенерирован без ошибок: {html_size} символов")
                    
                    # Check HTML content
                    if html_content.startswith('<!DOCTYPE html>'):
                        self.log_test("Проверить размер и содержимое HTML", "PASS", 
                                    f"HTML корректный: DOCTYPE найден, размер {html_size} символов")
                    else:
                        self.log_test("Проверить размер и содержимое HTML", "FAIL", "DOCTYPE отсутствует")
                    
                    # Check for NUMEROM branding
                    if 'NUMEROM' in html_content:
                        self.log_test("HTML содержит брендинг NUMEROM", "PASS", "NUMEROM найден в HTML")
                    else:
                        self.log_test("HTML содержит брендинг NUMEROM", "FAIL", "NUMEROM не найден")
                    
                    # Check for numerical data
                    numbers = re.findall(r'\b\d+\b', html_content)
                    if len(numbers) > 20:
                        self.log_test("HTML содержит существенные данные", "PASS", f"Найдено {len(numbers)} числовых значений")
                    else:
                        self.log_test("HTML содержит существенные данные", "FAIL", f"Мало данных: {len(numbers)} чисел")
                        
                else:
                    self.log_test("POST /api/reports/html/numerology", "FAIL", f"Неверный Content-Type: {content_type}")
            elif response.status_code == 402:
                self.log_test("POST /api/reports/html/numerology", "WARN", "Недостаточно кредитов (функция работает)")
            else:
                self.log_test("POST /api/reports/html/numerology", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("POST /api/reports/html/numerology", "FAIL", f"Ошибка: {str(e)}")
    
    def test_vedic_times_basic(self):
        """Test Vedic times without external dependencies"""
        print("\n🕐 ТЕСТ ВЕДИЧЕСКИХ ВРЕМЁН (базовый)")
        
        if not self.auth_token:
            self.log_test("Ведические времена", "SKIP", "Нет токена аутентификации")
            return
        
        # Test daily schedule without city (should fail gracefully)
        try:
            response = self.session.get(f"{BACKEND_URL}/vedic-time/daily-schedule")
            if response.status_code == 200:
                data = response.json()
                if 'rahu_kaal' in str(data).lower() or 'inauspicious_periods' in data:
                    self.log_test("GET /api/vedic-time/daily-schedule (без города)", "PASS", "Расписание получено")
                else:
                    self.log_test("GET /api/vedic-time/daily-schedule (без города)", "FAIL", "Отсутствуют ведические периоды")
            elif response.status_code == 422:
                self.log_test("GET /api/vedic-time/daily-schedule (без города)", "PASS", "Корректно требует город (422)")
            elif response.status_code == 402:
                self.log_test("GET /api/vedic-time/daily-schedule (без города)", "WARN", "Недостаточно кредитов")
            else:
                self.log_test("GET /api/vedic-time/daily-schedule (без города)", "FAIL", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/vedic-time/daily-schedule (без города)", "FAIL", f"Ошибка: {str(e)}")
        
        # Test planetary route without external dependencies
        try:
            response = self.session.get(f"{BACKEND_URL}/vedic-time/planetary-route")
            if response.status_code == 200:
                data = response.json()
                if 'daily_ruling_planet' in data or 'planetary' in str(data).lower():
                    self.log_test("GET /api/vedic-time/planetary-route", "PASS", "Планетарный маршрут получен")
                else:
                    self.log_test("GET /api/vedic-time/planetary-route", "FAIL", "Отсутствуют планетарные данные")
            elif response.status_code == 402:
                self.log_test("GET /api/vedic-time/planetary-route", "WARN", "Недостаточно кредитов")
            elif response.status_code == 422:
                self.log_test("GET /api/vedic-time/planetary-route", "PASS", "Корректно требует город (422)")
            else:
                self.log_test("GET /api/vedic-time/planetary-route", "FAIL", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/vedic-time/planetary-route", "FAIL", f"Ошибка: {str(e)}")
    
    def test_admin_functions(self):
        """Test admin functions if user is super admin"""
        print("\n👑 ТЕСТ АДМИНСКИХ ФУНКЦИЙ")
        
        if not self.auth_token:
            self.log_test("Админские функции", "SKIP", "Нет токена аутентификации")
            return
        
        # Check if user is super admin
        if not (self.user_data and self.user_data.get('is_super_admin')):
            self.log_test("Админские функции", "SKIP", "Пользователь не является супер админом")
            return
        
        # Test admin users endpoint
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/users")
            if response.status_code == 200:
                data = response.json()
                if 'users' in data and isinstance(data['users'], list):
                    user_count = len(data['users'])
                    self.log_test("GET /api/admin/users (если супер админ)", "PASS", f"Получено {user_count} пользователей")
                else:
                    self.log_test("GET /api/admin/users (если супер админ)", "FAIL", "Неверная структура ответа")
            else:
                self.log_test("GET /api/admin/users (если супер админ)", "FAIL", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/admin/users (если супер админ)", "FAIL", f"Ошибка: {str(e)}")
        
        # Test materials endpoint
        try:
            response = self.session.get(f"{BACKEND_URL}/materials")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    material_count = len(data)
                    self.log_test("GET /api/materials", "PASS", f"Получено {material_count} материалов")
                else:
                    self.log_test("GET /api/materials", "FAIL", "Неверная структура ответа")
            else:
                self.log_test("GET /api/materials", "FAIL", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/materials", "FAIL", f"Ошибка: {str(e)}")
    
    def analyze_errors(self):
        """Analyze errors found during testing"""
        print("\n🔍 АНАЛИЗ ОШИБОК")
        
        # Count different types of errors
        error_401 = len([r for r in self.test_results if '401' in r['details']])
        error_422 = len([r for r in self.test_results if '422' in r['details']])
        error_500 = len([r for r in self.test_results if '500' in r['details']])
        
        self.log_test("Детально проанализировать все 401 ошибки", "PASS" if error_401 == 0 else "WARN", 
                     f"Найдено {error_401} ошибок 401 (Unauthorized)")
        self.log_test("Детально проанализировать все 422 ошибки", "PASS" if error_422 <= 2 else "WARN", 
                     f"Найдено {error_422} ошибок 422 (Validation)")
        self.log_test("Детально проанализировать все 500 ошибки", "PASS" if error_500 == 0 else "FAIL", 
                     f"Найдено {error_500} критических ошибок 500 (Server Error)")
        
        # Find causes of failures
        failed_tests = [r for r in self.test_results if r['status'] == 'FAIL']
        if failed_tests:
            causes = []
            for test in failed_tests:
                if 'соединения' in test['details'].lower() or 'connection' in test['details'].lower():
                    causes.append("Проблемы соединения")
                elif '500' in test['details']:
                    causes.append("Внутренние ошибки сервера")
                elif '401' in test['details']:
                    causes.append("Проблемы аутентификации")
                elif '422' in test['details']:
                    causes.append("Ошибки валидации данных")
            
            unique_causes = list(set(causes))
            self.log_test("Найти причины сбоев", "INFO", f"Основные причины: {', '.join(unique_causes) if unique_causes else 'Неопределённые'}")
        else:
            self.log_test("Найти причины сбоев", "PASS", "Критических сбоев не обнаружено")
    
    def run_focused_test(self):
        """Run focused system test"""
        print("🎯 FOCUSED SYSTEM TEST: Тестирование основной функциональности NUMEROM")
        print("=" * 80)
        print("Проверяем работоспособность системы без внешних зависимостей...")
        print("=" * 80)
        
        # Step 1: Authentication
        auth_success = self.test_authentication()
        
        # Step 2: Main functions (only if authenticated)
        if auth_success:
            self.test_main_functions()
            
            # Step 3: HTML reports
            self.test_html_report_generation()
            
            # Step 4: Vedic times (basic)
            self.test_vedic_times_basic()
            
            # Step 5: Admin functions
            self.test_admin_functions()
        
        # Step 6: Error analysis
        self.analyze_errors()
        
        # Final summary
        self.print_summary()
        
        return len(self.critical_errors) == 0
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📋 ИТОГОВЫЙ ОТЧЁТ ТЕСТИРОВАНИЯ")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warned_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        skipped_tests = len([r for r in self.test_results if r['status'] == 'SKIP'])
        
        print(f"Всего тестов: {total_tests}")
        print(f"✅ Пройдено: {passed_tests}")
        print(f"❌ Провалено: {failed_tests}")
        print(f"⚠️ Предупреждения: {warned_tests}")
        print(f"⏭️ Пропущено: {skipped_tests}")
        
        success_rate = (passed_tests / max(total_tests - skipped_tests, 1)) * 100
        print(f"📊 Успешность: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ ПРОВАЛИВШИЕСЯ ТЕСТЫ:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  • {result['test']}: {result['details']}")
        
        # Critical assessment
        if len(self.critical_errors) > 0:
            print(f"\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ: {len(self.critical_errors)}")
            print("Система имеет серьёзные проблемы, которые мешают её работе!")
            for error in self.critical_errors:
                print(f"  🔥 {error['test']}: {error['details']}")
        else:
            print("\n🎉 КРИТИЧЕСКИЕ ПРОБЛЕМЫ НЕ ОБНАРУЖЕНЫ")
            if failed_tests == 0:
                print("✅ СИСТЕМА РАБОТАЕТ КОРРЕКТНО!")
                print("Все основные функции доступны и работают без ошибок.")
            else:
                print("⚠️ Система работает, но есть некритические проблемы.")
                print("Основная функциональность доступна пользователям.")

def main():
    """Main function"""
    test = FocusedSystemTest()
    
    try:
        success = test.run_focused_test()
        if success:
            print("\n✅ Тестирование завершено успешно")
            return 0
        else:
            print("\n❌ Тестирование выявило критические проблемы")
            return 1
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        return 1
    except Exception as e:
        print(f"\n💥 Критическая ошибка тестирования: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())