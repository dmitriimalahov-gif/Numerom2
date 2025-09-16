#!/usr/bin/env python3
"""
КОМПЛЕКСНАЯ ПРОВЕРКА: Все админ панель endpoints согласно review request

ПРОВЕРИТЬ:
1. **АДМИН ПАНЕЛЬ:**
   - Авторизоваться как супер админ (dmitrii.malahov@gmail.com / 756bvy67H)
   - Проверить доступ к админ панели
   - Протестировать все вкладки: Ученики, Занятия, Материалы, Консультации, Система

2. **ДЕТАЛЬНАЯ ПРОВЕРКА ENDPOINTS:**
   - GET /api/admin/users (для вкладки учеников)
   - GET /api/admin/lessons (для вкладки занятий) 
   - GET /api/admin/materials (для вкладки материалов)
   - GET /api/admin/consultations (для вкладки консультаций)
   - POST /api/admin/* (создание сущностей)

3. **ПРОВЕРКА БАЛЛОВ:**
   - GET /api/user/profile (текущий баланс)
   - POST endpoints для покупки баллов
   - Логика обновления credits_remaining
"""

import requests
import json
import uuid
from datetime import datetime
import sys

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"

class ComprehensiveAdminTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        
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
        
    def authenticate_super_admin(self):
        """Аутентификация супер админа"""
        try:
            login_data = {
                "email": SUPER_ADMIN_EMAIL,
                "password": SUPER_ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.user_data = data.get('user')
                
                if self.auth_token and self.user_data:
                    self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                    
                    user_details = f"User ID: {self.user_data.get('id')}, " \
                                 f"is_super_admin: {self.user_data.get('is_super_admin')}, " \
                                 f"credits: {self.user_data.get('credits_remaining')}"
                    
                    self.log_test("Супер админ аутентификация", "PASS", user_details)
                    return True
                else:
                    self.log_test("Супер админ аутентификация", "FAIL", "Отсутствует токен или данные пользователя")
                    return False
            else:
                self.log_test("Супер админ аутентификация", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Супер админ аутентификация", "FAIL", f"Ошибка: {str(e)}")
            return False

    def test_user_profile_endpoint(self):
        """Тест GET /api/user/profile"""
        try:
            response = self.session.get(f"{BACKEND_URL}/user/profile")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['id', 'email', 'credits_remaining', 'is_premium', 'subscription_type']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    credits = data.get('credits_remaining')
                    is_premium = data.get('is_premium')
                    subscription = data.get('subscription_type')
                    self.log_test("GET /api/user/profile", "PASS", 
                                f"Кредиты: {credits}, Премиум: {is_premium}, Подписка: {subscription}")
                else:
                    self.log_test("GET /api/user/profile", "FAIL", 
                                f"Отсутствуют поля: {', '.join(missing_fields)}")
            else:
                self.log_test("GET /api/user/profile", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/user/profile", "FAIL", f"Ошибка: {str(e)}")

    def test_admin_users_endpoint(self):
        """Тест GET /api/admin/users (вкладка Ученики)"""
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/users")
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                total_count = data.get('total_count', 0)
                
                if users and len(users) > 0:
                    first_user = users[0]
                    required_fields = ['id', 'email', 'name', 'birth_date', 'city', 'credits_remaining', 
                                     'is_premium', 'subscription_type', 'lessons_completed', 'lessons_total', 
                                     'lessons_progress_percent']
                    
                    missing_fields = [field for field in required_fields if field not in first_user]
                    
                    if not missing_fields:
                        super_admin_user = next((u for u in users if u['email'] == SUPER_ADMIN_EMAIL), None)
                        admin_info = f"Супер админ найден: {super_admin_user['credits_remaining']} кредитов" if super_admin_user else "Супер админ не найден"
                        
                        self.log_test("GET /api/admin/users (Ученики)", "PASS", 
                                    f"Получено {total_count} пользователей. {admin_info}")
                    else:
                        self.log_test("GET /api/admin/users (Ученики)", "FAIL", 
                                    f"Отсутствуют поля: {', '.join(missing_fields)}")
                else:
                    self.log_test("GET /api/admin/users (Ученики)", "FAIL", "Список пользователей пуст")
            else:
                self.log_test("GET /api/admin/users (Ученики)", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/admin/users (Ученики)", "FAIL", f"Ошибка: {str(e)}")

    def test_admin_lessons_endpoint(self):
        """Тест GET /api/admin/lessons (вкладка Занятия)"""
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/lessons")
            
            if response.status_code == 200:
                lessons = response.json()
                
                if isinstance(lessons, list):
                    if len(lessons) > 0:
                        first_lesson = lessons[0]
                        required_fields = ['id', 'title', 'description', 'level', 'order']
                        missing_fields = [field for field in required_fields if field not in first_lesson]
                        
                        if not missing_fields:
                            self.log_test("GET /api/admin/lessons (Занятия)", "PASS", 
                                        f"Получено {len(lessons)} уроков, все поля присутствуют")
                        else:
                            self.log_test("GET /api/admin/lessons (Занятия)", "FAIL", 
                                        f"Отсутствуют поля: {', '.join(missing_fields)}")
                    else:
                        self.log_test("GET /api/admin/lessons (Занятия)", "PASS", "Список уроков пуст (нормально)")
                else:
                    self.log_test("GET /api/admin/lessons (Занятия)", "FAIL", "Неверный формат ответа")
            else:
                self.log_test("GET /api/admin/lessons (Занятия)", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/admin/lessons (Занятия)", "FAIL", f"Ошибка: {str(e)}")

    def test_admin_materials_endpoint(self):
        """Тест GET /api/admin/materials (вкладка Материалы)"""
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/materials")
            
            if response.status_code == 200:
                data = response.json()
                materials = data.get('materials', [])
                total_count = data.get('total_count', 0)
                
                self.log_test("GET /api/admin/materials (Материалы)", "PASS", 
                            f"Получено {total_count} материалов")
            else:
                self.log_test("GET /api/admin/materials (Материалы)", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/admin/materials (Материалы)", "FAIL", f"Ошибка: {str(e)}")

    def test_admin_consultations_endpoint(self):
        """Тест GET /api/admin/consultations (вкладка Консультации)"""
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/consultations")
            
            if response.status_code == 200:
                self.log_test("GET /api/admin/consultations (Консультации)", "PASS", "Эндпоинт работает")
            elif response.status_code == 404:
                self.log_test("GET /api/admin/consultations (Консультации)", "WARN", "Эндпоинт не реализован (404)")
            else:
                self.log_test("GET /api/admin/consultations (Консультации)", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/admin/consultations (Консультации)", "FAIL", f"Ошибка: {str(e)}")

    def test_admin_system_endpoints(self):
        """Тест системных админ эндпоинтов"""
        # Test user credit management
        try:
            # Get users first
            response = self.session.get(f"{BACKEND_URL}/admin/users")
            if response.status_code == 200:
                users = response.json().get('users', [])
                test_user = None
                for user in users:
                    if user['email'] != SUPER_ADMIN_EMAIL and not user.get('is_super_admin', False):
                        test_user = user
                        break
                
                if test_user:
                    user_id = test_user['id']
                    original_credits = test_user['credits_remaining']
                    new_credits = original_credits + 25
                    
                    # Test PATCH /api/admin/users/{user_id}/credits
                    update_data = {"credits_remaining": new_credits}
                    response = self.session.patch(f"{BACKEND_URL}/admin/users/{user_id}/credits", 
                                                json=update_data)
                    
                    if response.status_code == 200:
                        self.log_test("PATCH /api/admin/users/{user_id}/credits", "PASS", 
                                    f"Кредиты обновлены с {original_credits} до {new_credits}")
                    else:
                        self.log_test("PATCH /api/admin/users/{user_id}/credits", "FAIL", 
                                    f"HTTP {response.status_code}: {response.text}")
                else:
                    self.log_test("PATCH /api/admin/users/{user_id}/credits", "SKIP", "Нет подходящих пользователей")
            else:
                self.log_test("PATCH /api/admin/users/{user_id}/credits", "FAIL", "Не удалось получить пользователей")
                
        except Exception as e:
            self.log_test("PATCH /api/admin/users/{user_id}/credits", "FAIL", f"Ошибка: {str(e)}")

        # Test user lesson progress
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/users")
            if response.status_code == 200:
                users = response.json().get('users', [])
                if users:
                    test_user = users[0]
                    user_id = test_user['id']
                    
                    response = self.session.get(f"{BACKEND_URL}/admin/users/{user_id}/lessons")
                    
                    if response.status_code == 200:
                        data = response.json()
                        lessons = data.get('lessons', [])
                        self.log_test("GET /api/admin/users/{user_id}/lessons", "PASS", 
                                    f"Получен прогресс: {len(lessons)} записей")
                    else:
                        self.log_test("GET /api/admin/users/{user_id}/lessons", "FAIL", 
                                    f"HTTP {response.status_code}: {response.text}")
                else:
                    self.log_test("GET /api/admin/users/{user_id}/lessons", "SKIP", "Нет пользователей")
            else:
                self.log_test("GET /api/admin/users/{user_id}/lessons", "FAIL", "Не удалось получить пользователей")
                
        except Exception as e:
            self.log_test("GET /api/admin/users/{user_id}/lessons", "FAIL", f"Ошибка: {str(e)}")

    def test_credits_purchase_system(self):
        """Детальный тест системы покупки кредитов"""
        print("\n💳 ДЕТАЛЬНЫЙ ТЕСТ СИСТЕМЫ ПОКУПКИ КРЕДИТОВ")
        
        # Get initial credits
        try:
            profile_response = self.session.get(f"{BACKEND_URL}/user/profile")
            if profile_response.status_code == 200:
                initial_profile = profile_response.json()
                initial_credits = initial_profile.get('credits_remaining', 0)
                initial_subscription = initial_profile.get('subscription_type')
                
                self.log_test("Начальный баланс кредитов", "PASS", 
                            f"Кредиты: {initial_credits}, Подписка: {initial_subscription}")
                
                # Test one-time purchase (should ADD credits)
                payment_data = {
                    "package_type": "one_time",
                    "origin_url": "https://numerology-fix.preview.emergentagent.com"
                }
                
                response = self.session.post(f"{BACKEND_URL}/payments/checkout/session", json=payment_data)
                if response.status_code == 200:
                    data = response.json()
                    session_id = data.get('session_id')
                    
                    # Check payment status
                    status_response = self.session.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        if status_data.get('payment_status') == 'paid':
                            # Check new balance
                            new_profile_response = self.session.get(f"{BACKEND_URL}/user/profile")
                            if new_profile_response.status_code == 200:
                                new_profile = new_profile_response.json()
                                new_credits = new_profile.get('credits_remaining', 0)
                                credit_change = new_credits - initial_credits
                                
                                if credit_change == 10:  # Expected for one_time
                                    self.log_test("Покупка one_time кредитов", "PASS", 
                                                f"Кредиты увеличились на {credit_change} ({initial_credits} → {new_credits})")
                                else:
                                    self.log_test("Покупка one_time кредитов", "FAIL", 
                                                f"Неожиданное изменение кредитов: {credit_change} (ожидалось +10)")
                            else:
                                self.log_test("Покупка one_time кредитов", "FAIL", "Не удалось проверить новый баланс")
                        else:
                            self.log_test("Покупка one_time кредитов", "FAIL", "Платеж не прошел")
                    else:
                        self.log_test("Покупка one_time кредитов", "FAIL", "Ошибка проверки статуса")
                else:
                    self.log_test("Покупка one_time кредитов", "FAIL", f"HTTP {response.status_code}")
                    
                # Test monthly subscription issue
                print(f"\n🔍 ТЕСТИРОВАНИЕ ПРОБЛЕМЫ С МЕСЯЧНОЙ ПОДПИСКОЙ:")
                current_profile_response = self.session.get(f"{BACKEND_URL}/user/profile")
                if current_profile_response.status_code == 200:
                    current_profile = current_profile_response.json()
                    current_credits = current_profile.get('credits_remaining', 0)
                    
                    print(f"   Текущие кредиты перед месячной подпиской: {current_credits}")
                    
                    payment_data = {
                        "package_type": "monthly",
                        "origin_url": "https://numerology-fix.preview.emergentagent.com"
                    }
                    
                    response = self.session.post(f"{BACKEND_URL}/payments/checkout/session", json=payment_data)
                    if response.status_code == 200:
                        data = response.json()
                        session_id = data.get('session_id')
                        
                        status_response = self.session.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            if status_data.get('payment_status') == 'paid':
                                final_profile_response = self.session.get(f"{BACKEND_URL}/user/profile")
                                if final_profile_response.status_code == 200:
                                    final_profile = final_profile_response.json()
                                    final_credits = final_profile.get('credits_remaining', 0)
                                    
                                    print(f"   Кредиты после месячной подписки: {final_credits}")
                                    
                                    if final_credits == 100:
                                        self.log_test("Проблема месячной подписки", "FAIL", 
                                                    f"ПОДТВЕРЖДЕНО: Месячная подписка УСТАНАВЛИВАЕТ кредиты в 100, а не ДОБАВЛЯЕТ 100. "
                                                    f"Было: {current_credits}, стало: {final_credits}")
                                    else:
                                        self.log_test("Проблема месячной подписки", "PASS", 
                                                    f"Кредиты изменились корректно: {current_credits} → {final_credits}")
                                else:
                                    self.log_test("Проблема месячной подписки", "FAIL", "Не удалось проверить финальный баланс")
                            else:
                                self.log_test("Проблема месячной подписки", "FAIL", "Платеж не прошел")
                        else:
                            self.log_test("Проблема месячной подписки", "FAIL", "Ошибка проверки статуса")
                    else:
                        self.log_test("Проблема месячной подписки", "FAIL", f"HTTP {response.status_code}")
                        
            else:
                self.log_test("Начальный баланс кредитов", "FAIL", "Не удалось получить профиль")
                
        except Exception as e:
            self.log_test("Система покупки кредитов", "FAIL", f"Ошибка: {str(e)}")

    def run_comprehensive_test(self):
        """Запуск комплексного тестирования"""
        print("🎯 КРИТИЧЕСКАЯ ДИАГНОСТИКА: Ошибки в админ панели NUMEROM")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.authenticate_super_admin():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось аутентифицировать супер админа")
            return False
        
        # Step 2: Test user profile endpoint
        self.test_user_profile_endpoint()
        
        # Step 3: Test all admin panel tabs
        print(f"\n📋 ТЕСТИРОВАНИЕ ВСЕХ ВКЛАДОК АДМИН ПАНЕЛИ:")
        self.test_admin_users_endpoint()
        self.test_admin_lessons_endpoint()
        self.test_admin_materials_endpoint()
        self.test_admin_consultations_endpoint()
        
        # Step 4: Test system admin endpoints
        print(f"\n⚙️ ТЕСТИРОВАНИЕ СИСТЕМНЫХ АДМИН ФУНКЦИЙ:")
        self.test_admin_system_endpoints()
        
        # Step 5: Test credits purchase system
        self.test_credits_purchase_system()
        
        # Summary
        self.print_comprehensive_summary()
        
        return True
    
    def print_comprehensive_summary(self):
        """Печать итогового отчёта"""
        print("\n" + "=" * 80)
        print("🔍 ИТОГОВЫЙ ДИАГНОСТИЧЕСКИЙ ОТЧЁТ")
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
        
        # Categorize issues
        admin_panel_issues = []
        credits_system_issues = []
        
        for result in self.test_results:
            if result['status'] == 'FAIL':
                if any(keyword in result['test'].lower() for keyword in ['админ', 'ученики', 'занятия', 'материалы', 'консультации', 'admin']):
                    admin_panel_issues.append(result)
                elif any(keyword in result['test'].lower() for keyword in ['кредит', 'платеж', 'баланс', 'покупка', 'подписка']):
                    credits_system_issues.append(result)
        
        print("\n🎯 ДЕТАЛЬНЫЙ АНАЛИЗ ПРОБЛЕМ:")
        
        if admin_panel_issues:
            print(f"\n❌ ПРОБЛЕМЫ АДМИН ПАНЕЛИ ({len(admin_panel_issues)}):")
            for issue in admin_panel_issues:
                print(f"  • {issue['test']}: {issue['details']}")
        else:
            print("\n✅ АДМИН ПАНЕЛЬ: Все основные функции работают корректно")
        
        if credits_system_issues:
            print(f"\n❌ ПРОБЛЕМЫ СИСТЕМЫ БАЛЛОВ ({len(credits_system_issues)}):")
            for issue in credits_system_issues:
                print(f"  • {issue['test']}: {issue['details']}")
        else:
            print("\n✅ СИСТЕМА БАЛЛОВ: Критических проблем не обнаружено")
        
        # Final assessment
        critical_issues = len(admin_panel_issues) + len(credits_system_issues)
        
        print(f"\n🏁 ФИНАЛЬНОЕ ЗАКЛЮЧЕНИЕ:")
        if critical_issues == 0:
            print("🎉 Критические проблемы НЕ ПОДТВЕРЖДЕНЫ")
            print("Админ панель и система баллов работают в основном корректно!")
        else:
            print(f"🚨 Обнаружено {critical_issues} критических проблем")
            print("Требуется исправление системы начисления кредитов!")

def main():
    """Главная функция запуска тестирования"""
    tester = ComprehensiveAdminTester()
    
    try:
        success = tester.run_comprehensive_test()
        if success:
            print("\n✅ Комплексное тестирование завершено")
            return 0
        else:
            print("\n❌ Комплексное тестирование завершено с ошибками")
            return 1
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        return 1
    except Exception as e:
        print(f"\n💥 Критическая ошибка тестирования: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())