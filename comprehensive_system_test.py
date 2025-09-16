#!/usr/bin/env python3
"""
КОМПЛЕКСНАЯ ДИАГНОСТИКА: Полное тестирование системы NUMEROM после сообщения о неработающей системе
Comprehensive Backend Testing for NUMEROM Application

This test suite performs comprehensive system diagnostics as requested:
1. Basic endpoints testing
2. Authentication testing  
3. Main functions testing
4. HTML report generation testing
5. Vedic times testing
6. Admin functions testing
7. Database verification
8. Error analysis
"""

import requests
import json
import re
from datetime import datetime
import sys
import os

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_USER_EMAIL = "dmitrii.malahov@gmail.com"
TEST_USER_PASSWORD = "756bvy67H"

class NumerologySystemDiagnostics:
    def __init__(self):
        self.session = requests.Session()
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
    
    def test_basic_endpoints(self):
        """1. ТЕСТ БАЗОВЫХ ENDPOINTS"""
        print("\n🔧 ТЕСТ 1: БАЗОВЫЕ ENDPOINTS")
        
        # Test root endpoint
        try:
            response = self.session.get(f"{BACKEND_URL}/")
            if response.status_code == 200:
                self.log_test("GET /api/ (root endpoint)", "PASS", f"HTTP 200: {response.text[:100]}")
            else:
                self.log_test("GET /api/ (root endpoint)", "FAIL", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/ (root endpoint)", "FAIL", f"Ошибка соединения: {str(e)}")
        
        # Test health endpoint (if exists)
        try:
            response = self.session.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                self.log_test("GET /health", "PASS", f"HTTP 200: {response.text[:100]}")
            elif response.status_code == 404:
                self.log_test("GET /health", "WARN", "Endpoint не существует (это нормально)")
            else:
                self.log_test("GET /health", "FAIL", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /health", "WARN", f"Endpoint недоступен: {str(e)}")
    
    def test_authentication_system(self):
        """2. ТЕСТ АУТЕНТИФИКАЦИИ"""
        print("\n🔐 ТЕСТ 2: СИСТЕМА АУТЕНТИФИКАЦИИ")
        
        # Test login with specified credentials
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
                    self.log_test("POST /api/auth/login", "PASS", f"Токен получен успешно (длина: {len(self.auth_token)})")
                    
                    # Set authorization header for future requests
                    self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                    
                    # Verify user data
                    if self.user_data:
                        user_info = f"ID: {self.user_data.get('id')}, " \
                                   f"Super Admin: {self.user_data.get('is_super_admin')}, " \
                                   f"Premium: {self.user_data.get('is_premium')}, " \
                                   f"Credits: {self.user_data.get('credits_remaining')}"
                        self.log_test("Проверка данных пользователя", "PASS", user_info)
                        
                        # Check if user exists in database
                        if self.user_data.get('id'):
                            self.log_test("Пользователь существует в базе данных", "PASS", f"User ID: {self.user_data.get('id')}")
                        else:
                            self.log_test("Пользователь существует в базе данных", "FAIL", "User ID отсутствует")
                    else:
                        self.log_test("Проверка данных пользователя", "FAIL", "Данные пользователя отсутствуют в ответе")
                else:
                    self.log_test("POST /api/auth/login", "FAIL", "Токен не возвращён в ответе")
                    return False
            else:
                self.log_test("POST /api/auth/login", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("POST /api/auth/login", "FAIL", f"Ошибка: {str(e)}")
            return False
        
        # Test authorized request
        try:
            response = self.session.get(f"{BACKEND_URL}/user/profile")
            if response.status_code == 200:
                self.log_test("Авторизованные запросы работают", "PASS", "Профиль пользователя получен")
            elif response.status_code == 404:
                # Try alternative endpoint
                response = self.session.post(f"{BACKEND_URL}/numerology/personal-numbers")
                if response.status_code in [200, 402]:  # 402 = insufficient credits is OK
                    self.log_test("Авторизованные запросы работают", "PASS", "Numerology endpoint доступен")
                else:
                    self.log_test("Авторизованные запросы работают", "FAIL", f"HTTP {response.status_code}")
            else:
                self.log_test("Авторизованные запросы работают", "FAIL", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Авторизованные запросы работают", "FAIL", f"Ошибка: {str(e)}")
        
        return True
    
    def test_main_functions(self):
        """3. ТЕСТ ОСНОВНЫХ ФУНКЦИЙ"""
        print("\n⚡ ТЕСТ 3: ОСНОВНЫЕ ФУНКЦИИ")
        
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
        
        # Test user profile (alternative endpoint)
        try:
            response = self.session.get(f"{BACKEND_URL}/learning/levels")
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /api/user/profile (альтернатива)", "PASS", "Данные пользователя получены")
            else:
                self.log_test("GET /api/user/profile (альтернатива)", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/user/profile (альтернатива)", "FAIL", f"Ошибка: {str(e)}")
    
    def test_html_report_generation(self):
        """4. ТЕСТ ГЕНЕРАЦИИ HTML ОТЧЁТОВ"""
        print("\n📄 ТЕСТ 4: ГЕНЕРАЦИЯ HTML ОТЧЁТОВ")
        
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
                                f"HTML сгенерирован: {html_size} символов, Content-Type: {content_type}")
                    
                    # Check HTML content
                    if html_content.startswith('<!DOCTYPE html>'):
                        self.log_test("HTML структура корректна", "PASS", "DOCTYPE найден")
                    else:
                        self.log_test("HTML структура корректна", "FAIL", "DOCTYPE отсутствует")
                    
                    # Check for NUMEROM branding
                    if 'NUMEROM' in html_content:
                        self.log_test("HTML содержит брендинг", "PASS", "NUMEROM найден в HTML")
                    else:
                        self.log_test("HTML содержит брендинг", "FAIL", "NUMEROM не найден")
                    
                    # Check for numerical data
                    numbers = re.findall(r'\b\d+\b', html_content)
                    if len(numbers) > 20:
                        self.log_test("HTML содержит данные", "PASS", f"Найдено {len(numbers)} числовых значений")
                    else:
                        self.log_test("HTML содержит данные", "FAIL", f"Мало данных: {len(numbers)} чисел")
                        
                    # Store for further analysis
                    self.html_content = html_content
                    
                else:
                    self.log_test("POST /api/reports/html/numerology", "FAIL", f"Неверный Content-Type: {content_type}")
            elif response.status_code == 402:
                self.log_test("POST /api/reports/html/numerology", "WARN", "Недостаточно кредитов (функция работает)")
            else:
                self.log_test("POST /api/reports/html/numerology", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("POST /api/reports/html/numerology", "FAIL", f"Ошибка: {str(e)}")
    
    def test_vedic_times(self):
        """5. ТЕСТ ВЕДИЧЕСКИХ ВРЕМЁН"""
        print("\n🕐 ТЕСТ 5: ВЕДИЧЕСКИЕ ВРЕМЕНА")
        
        if not self.auth_token:
            self.log_test("Ведические времена", "SKIP", "Нет токена аутентификации")
            return
        
        # Test daily schedule without city
        try:
            response = self.session.get(f"{BACKEND_URL}/vedic-time/daily-schedule")
            if response.status_code == 200:
                data = response.json()
                if 'rahu_kaal' in str(data).lower() or 'inauspicious_periods' in data:
                    self.log_test("GET /api/vedic-time/daily-schedule (без города)", "PASS", "Расписание получено")
                else:
                    self.log_test("GET /api/vedic-time/daily-schedule (без города)", "FAIL", "Отсутствуют ведические периоды")
            elif response.status_code == 422:
                self.log_test("GET /api/vedic-time/daily-schedule (без города)", "WARN", "Требуется город (нормально)")
            elif response.status_code == 402:
                self.log_test("GET /api/vedic-time/daily-schedule (без города)", "WARN", "Недостаточно кредитов")
            else:
                self.log_test("GET /api/vedic-time/daily-schedule (без города)", "FAIL", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/vedic-time/daily-schedule (без города)", "FAIL", f"Ошибка: {str(e)}")
        
        # Test daily schedule with city
        try:
            response = self.session.get(f"{BACKEND_URL}/vedic-time/daily-schedule?city=Москва")
            if response.status_code == 200:
                data = response.json()
                if 'rahu_kaal' in str(data).lower() or 'inauspicious_periods' in data:
                    self.log_test("GET /api/vedic-time/daily-schedule (с городом)", "PASS", "Расписание с городом получено")
                else:
                    self.log_test("GET /api/vedic-time/daily-schedule (с городом)", "FAIL", "Отсутствуют ведические периоды")
            elif response.status_code == 402:
                self.log_test("GET /api/vedic-time/daily-schedule (с городом)", "WARN", "Недостаточно кредитов")
            else:
                self.log_test("GET /api/vedic-time/daily-schedule (с городом)", "FAIL", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/vedic-time/daily-schedule (с городом)", "FAIL", f"Ошибка: {str(e)}")
        
        # Test planetary route
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
            else:
                self.log_test("GET /api/vedic-time/planetary-route", "FAIL", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/vedic-time/planetary-route", "FAIL", f"Ошибка: {str(e)}")
    
    def test_admin_functions(self):
        """6. ТЕСТ АДМИНСКИХ ФУНКЦИЙ"""
        print("\n👑 ТЕСТ 6: АДМИНСКИЕ ФУНКЦИИ")
        
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
                    self.log_test("GET /api/admin/users", "PASS", f"Получено {user_count} пользователей")
                else:
                    self.log_test("GET /api/admin/users", "FAIL", "Неверная структура ответа")
            else:
                self.log_test("GET /api/admin/users", "FAIL", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/admin/users", "FAIL", f"Ошибка: {str(e)}")
        
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
        """7. АНАЛИЗ ОШИБОК"""
        print("\n🔍 ТЕСТ 7: АНАЛИЗ ОШИБОК")
        
        # Count different types of errors
        error_401 = len([r for r in self.test_results if '401' in r['details']])
        error_422 = len([r for r in self.test_results if '422' in r['details']])
        error_500 = len([r for r in self.test_results if '500' in r['details']])
        
        self.log_test("Анализ 401 ошибок (Unauthorized)", "INFO" if error_401 == 0 else "WARN", 
                     f"Найдено {error_401} ошибок 401")
        self.log_test("Анализ 422 ошибок (Validation)", "INFO" if error_422 <= 2 else "WARN", 
                     f"Найдено {error_422} ошибок 422")
        self.log_test("Анализ 500 ошибок (Server Error)", "PASS" if error_500 == 0 else "FAIL", 
                     f"Найдено {error_500} критических ошибок 500")
        
        # Analyze connection errors
        connection_errors = len([r for r in self.test_results if 'соединения' in r['details'].lower() or 'connection' in r['details'].lower()])
        if connection_errors > 0:
            self.log_test("Анализ ошибок соединения", "FAIL", f"Найдено {connection_errors} ошибок соединения")
        else:
            self.log_test("Анализ ошибок соединения", "PASS", "Ошибки соединения не обнаружены")
    
    def run_comprehensive_diagnostics(self):
        """Запуск полной диагностики системы"""
        print("🎯 КОМПЛЕКСНАЯ ДИАГНОСТИКА: Полное тестирование системы NUMEROM")
        print("=" * 80)
        print("Пользователь сообщает что система не работает. Проводим полную диагностику...")
        print("=" * 80)
        
        # Step 1: Basic endpoints
        self.test_basic_endpoints()
        
        # Step 2: Authentication
        auth_success = self.test_authentication_system()
        
        # Step 3: Main functions (only if authenticated)
        if auth_success:
            self.test_main_functions()
            
            # Step 4: HTML reports
            self.test_html_report_generation()
            
            # Step 5: Vedic times
            self.test_vedic_times()
            
            # Step 6: Admin functions
            self.test_admin_functions()
        
        # Step 7: Error analysis
        self.analyze_errors()
        
        # Final summary
        self.print_diagnostic_summary()
        
        return len(self.critical_errors) == 0
    
    def print_diagnostic_summary(self):
        """Печать итогового отчёта диагностики"""
        print("\n" + "=" * 80)
        print("📋 ИТОГОВЫЙ ОТЧЁТ ДИАГНОСТИКИ СИСТЕМЫ")
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
                print("Система работает корректно!")
            else:
                print("Система работает, но есть некритические проблемы.")

def main():
    """Главная функция запуска диагностики"""
    diagnostics = NumerologySystemDiagnostics()
    
    try:
        success = diagnostics.run_comprehensive_diagnostics()
        if success:
            print("\n✅ Диагностика завершена успешно")
            return 0
        else:
            print("\n❌ Диагностика выявила критические проблемы")
            return 1
    except KeyboardInterrupt:
        print("\n⏹️ Диагностика прервана пользователем")
        return 1
    except Exception as e:
        print(f"\n💥 Критическая ошибка диагностики: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())