#!/usr/bin/env python3
"""
КРИТИЧЕСКАЯ ДИАГНОСТИКА: Ошибки в админ панели NUMEROM

Пользователь сообщает о проблемах:
1. Админ панель выдает ошибку
2. Баллы не плюсуются после покупки

ПРОВЕРИТЬ:
1. **АДМИН ПАНЕЛЬ:**
   - Авторизоваться как супер админ (dmitrii.malahov@gmail.com / 756bvy67H)
   - Проверить доступ к админ панели
   - Протестировать все вкладки: Ученики, Занятия, Материалы, Консультации, Система
   - Найти конкретные ошибки в каждой вкладке

2. **СИСТЕМА БАЛЛОВ:**
   - Проверить endpoint покупки кредитов/баллов
   - Найти логику начисления баллов пользователю
   - Проверить что баллы корректно суммируются с текущим балансом

3. **ДЕТАЛЬНАЯ ПРОВЕРКА ENDPOINTS:**
   - GET /api/admin/users (для вкладки учеников)
   - GET /api/admin/lessons (для вкладки занятий) 
   - GET /api/admin/materials (для вкладки материалов)
   - GET /api/admin/consultations (для вкладки консультаций)
   - POST /api/admin/* (создание сущностей)

4. **ПРОВЕРКА БАЛЛОВ:**
   - GET /api/user/profile (текущий баланс)
   - POST endpoints для покупки баллов
   - Логика обновления credits_remaining
"""

import requests
import json
import uuid
from datetime import datetime
import sys
import os

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"

class AdminPanelTester:
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
        """1. АУТЕНТИФИКАЦИЯ СУПЕР АДМИНА"""
        print("\n🔐 ТЕСТ 1: АУТЕНТИФИКАЦИЯ СУПЕР АДМИНА")
        print(f"Email: {SUPER_ADMIN_EMAIL}")
        print(f"Password: {SUPER_ADMIN_PASSWORD}")
        
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
                    # Set authorization header for future requests
                    self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                    
                    user_details = f"User ID: {self.user_data.get('id')}, " \
                                 f"is_super_admin: {self.user_data.get('is_super_admin')}, " \
                                 f"is_premium: {self.user_data.get('is_premium')}, " \
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

    def test_admin_users_tab(self):
        """2. ТЕСТИРОВАНИЕ ВКЛАДКИ УЧЕНИКИ (USERS)"""
        print("\n👥 ТЕСТ 2: ВКЛАДКА УЧЕНИКИ - GET /api/admin/users")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/users")
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                total_count = data.get('total_count', 0)
                
                if users and len(users) > 0:
                    # Check first user structure
                    first_user = users[0]
                    required_fields = ['id', 'email', 'name', 'birth_date', 'city', 'credits_remaining', 
                                     'is_premium', 'subscription_type', 'lessons_completed', 'lessons_total', 
                                     'lessons_progress_percent']
                    
                    missing_fields = [field for field in required_fields if field not in first_user]
                    
                    if not missing_fields:
                        # Find super admin in users list
                        super_admin_user = next((u for u in users if u['email'] == SUPER_ADMIN_EMAIL), None)
                        if super_admin_user:
                            admin_details = f"Найден супер админ: {super_admin_user['credits_remaining']} кредитов"
                        else:
                            admin_details = "Супер админ не найден в списке"
                        
                        self.log_test("Админ панель - Ученики", "PASS", 
                                    f"Получено {total_count} пользователей, все поля присутствуют. {admin_details}")
                    else:
                        self.log_test("Админ панель - Ученики", "FAIL", 
                                    f"Отсутствуют поля: {', '.join(missing_fields)}")
                else:
                    self.log_test("Админ панель - Ученики", "FAIL", "Список пользователей пуст")
            else:
                self.log_test("Админ панель - Ученики", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Админ панель - Ученики", "FAIL", f"Ошибка: {str(e)}")

    def test_admin_lessons_tab(self):
        """3. ТЕСТИРОВАНИЕ ВКЛАДКИ ЗАНЯТИЯ (LESSONS)"""
        print("\n📚 ТЕСТ 3: ВКЛАДКА ЗАНЯТИЯ - GET /api/admin/lessons")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/lessons")
            
            if response.status_code == 200:
                lessons = response.json()
                
                if isinstance(lessons, list):
                    if len(lessons) > 0:
                        # Check first lesson structure
                        first_lesson = lessons[0]
                        required_fields = ['id', 'title', 'description', 'level', 'order']
                        
                        missing_fields = [field for field in required_fields if field not in first_lesson]
                        
                        if not missing_fields:
                            self.log_test("Админ панель - Занятия", "PASS", 
                                        f"Получено {len(lessons)} уроков, все поля присутствуют")
                        else:
                            self.log_test("Админ панель - Занятия", "FAIL", 
                                        f"Отсутствуют поля: {', '.join(missing_fields)}")
                    else:
                        self.log_test("Админ панель - Занятия", "PASS", "Список уроков пуст (это нормально)")
                else:
                    self.log_test("Админ панель - Занятия", "FAIL", "Неверный формат ответа")
            else:
                self.log_test("Админ панель - Занятия", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Админ панель - Занятия", "FAIL", f"Ошибка: {str(e)}")

    def test_admin_materials_tab(self):
        """4. ТЕСТИРОВАНИЕ ВКЛАДКИ МАТЕРИАЛЫ (MATERIALS)"""
        print("\n📄 ТЕСТ 4: ВКЛАДКА МАТЕРИАЛЫ - GET /api/admin/materials")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/materials")
            
            if response.status_code == 200:
                data = response.json()
                materials = data.get('materials', [])
                total_count = data.get('total_count', 0)
                
                if isinstance(materials, list):
                    self.log_test("Админ панель - Материалы", "PASS", 
                                f"Получено {total_count} материалов")
                else:
                    self.log_test("Админ панель - Материалы", "FAIL", "Неверный формат ответа")
            else:
                self.log_test("Админ панель - Материалы", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Админ панель - Материалы", "FAIL", f"Ошибка: {str(e)}")

    def test_admin_consultations_tab(self):
        """5. ТЕСТИРОВАНИЕ ВКЛАДКИ КОНСУЛЬТАЦИИ"""
        print("\n💬 ТЕСТ 5: ВКЛАДКА КОНСУЛЬТАЦИИ")
        
        # This endpoint might not exist, so we'll check if it returns 404 or works
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/consultations")
            
            if response.status_code == 200:
                self.log_test("Админ панель - Консультации", "PASS", "Эндпоинт работает")
            elif response.status_code == 404:
                self.log_test("Админ панель - Консультации", "WARN", "Эндпоинт не реализован (404)")
            else:
                self.log_test("Админ панель - Консультации", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Админ панель - Консультации", "FAIL", f"Ошибка: {str(e)}")

    def test_user_credits_management(self):
        """6. ТЕСТИРОВАНИЕ УПРАВЛЕНИЯ КРЕДИТАМИ ПОЛЬЗОВАТЕЛЕЙ"""
        print("\n💰 ТЕСТ 6: УПРАВЛЕНИЕ КРЕДИТАМИ ПОЛЬЗОВАТЕЛЕЙ")
        
        # First, get a regular user to test credit management
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/users")
            if response.status_code == 200:
                users = response.json().get('users', [])
                # Find a non-super-admin user
                test_user = None
                for user in users:
                    if user['email'] != SUPER_ADMIN_EMAIL and not user.get('is_super_admin', False):
                        test_user = user
                        break
                
                if test_user:
                    user_id = test_user['id']
                    original_credits = test_user['credits_remaining']
                    
                    # Test updating user credits
                    new_credits = original_credits + 50
                    update_data = {"credits_remaining": new_credits}
                    
                    response = self.session.patch(f"{BACKEND_URL}/admin/users/{user_id}/credits", 
                                                json=update_data)
                    
                    if response.status_code == 200:
                        # Verify the update by checking user profile
                        profile_response = self.session.get(f"{BACKEND_URL}/user/profile")
                        if profile_response.status_code == 200:
                            # This will show super admin profile, not the test user
                            # Let's check the user list again
                            users_response = self.session.get(f"{BACKEND_URL}/admin/users")
                            if users_response.status_code == 200:
                                updated_users = users_response.json().get('users', [])
                                updated_user = next((u for u in updated_users if u['id'] == user_id), None)
                                
                                if updated_user and updated_user['credits_remaining'] == new_credits:
                                    self.log_test("Управление кредитами", "PASS", 
                                                f"Кредиты обновлены с {original_credits} до {new_credits}")
                                else:
                                    self.log_test("Управление кредитами", "FAIL", 
                                                "Кредиты не обновились в базе данных")
                            else:
                                self.log_test("Управление кредитами", "FAIL", 
                                            "Не удалось проверить обновление кредитов")
                        else:
                            self.log_test("Управление кредитами", "WARN", 
                                        "Обновление выполнено, но проверка недоступна")
                    else:
                        self.log_test("Управление кредитами", "FAIL", 
                                    f"HTTP {response.status_code}: {response.text}")
                else:
                    self.log_test("Управление кредитами", "SKIP", "Нет подходящих пользователей для теста")
            else:
                self.log_test("Управление кредитами", "FAIL", "Не удалось получить список пользователей")
                
        except Exception as e:
            self.log_test("Управление кредитами", "FAIL", f"Ошибка: {str(e)}")

    def test_user_lesson_progress(self):
        """7. ТЕСТИРОВАНИЕ ПРОГРЕССА УРОКОВ ПОЛЬЗОВАТЕЛЕЙ"""
        print("\n📈 ТЕСТ 7: ПРОГРЕСС УРОКОВ ПОЛЬЗОВАТЕЛЕЙ")
        
        try:
            # Get users first
            response = self.session.get(f"{BACKEND_URL}/admin/users")
            if response.status_code == 200:
                users = response.json().get('users', [])
                if users:
                    # Test with first user
                    test_user = users[0]
                    user_id = test_user['id']
                    
                    # Get user lesson progress
                    response = self.session.get(f"{BACKEND_URL}/admin/users/{user_id}/lessons")
                    
                    if response.status_code == 200:
                        data = response.json()
                        lessons = data.get('lessons', [])
                        
                        self.log_test("Прогресс уроков пользователей", "PASS", 
                                    f"Получен прогресс для пользователя {user_id}: {len(lessons)} записей")
                    else:
                        self.log_test("Прогресс уроков пользователей", "FAIL", 
                                    f"HTTP {response.status_code}: {response.text}")
                else:
                    self.log_test("Прогресс уроков пользователей", "SKIP", "Нет пользователей для теста")
            else:
                self.log_test("Прогресс уроков пользователей", "FAIL", "Не удалось получить список пользователей")
                
        except Exception as e:
            self.log_test("Прогресс уроков пользователей", "FAIL", f"Ошибка: {str(e)}")

    def test_payment_system(self):
        """8. ТЕСТИРОВАНИЕ СИСТЕМЫ ПЛАТЕЖЕЙ И НАЧИСЛЕНИЯ БАЛЛОВ"""
        print("\n💳 ТЕСТ 8: СИСТЕМА ПЛАТЕЖЕЙ И НАЧИСЛЕНИЯ БАЛЛОВ")
        
        # Get current user credits before payment test
        try:
            profile_response = self.session.get(f"{BACKEND_URL}/user/profile")
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                current_credits = profile_data.get('credits_remaining', 0)
                self.log_test("Текущий баланс кредитов", "PASS", f"Текущие кредиты: {current_credits}")
            else:
                self.log_test("Текущий баланс кредитов", "FAIL", f"HTTP {profile_response.status_code}")
                current_credits = None
        except Exception as e:
            self.log_test("Текущий баланс кредитов", "FAIL", f"Ошибка: {str(e)}")
            current_credits = None

        # Test payment session creation
        payment_packages = ['one_time', 'monthly', 'annual']
        
        for package_type in payment_packages:
            try:
                payment_data = {
                    "package_type": package_type,
                    "origin_url": "https://numerology-fix.preview.emergentagent.com"
                }
                
                response = self.session.post(f"{BACKEND_URL}/payments/checkout/session", 
                                           json=payment_data)
                
                if response.status_code == 200:
                    data = response.json()
                    session_id = data.get('session_id')
                    url = data.get('url')
                    
                    if session_id and url:
                        self.log_test(f"Создание платежной сессии - {package_type}", "PASS", 
                                    f"Session ID: {session_id[:20]}...")
                        
                        # Test payment status check
                        status_response = self.session.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            payment_status = status_data.get('payment_status')
                            
                            self.log_test(f"Проверка статуса платежа - {package_type}", "PASS", 
                                        f"Статус: {payment_status}")
                            
                            # In demo mode, payment should be automatically marked as paid
                            if payment_status == 'paid':
                                # Check if credits were added
                                new_profile_response = self.session.get(f"{BACKEND_URL}/user/profile")
                                if new_profile_response.status_code == 200:
                                    new_profile_data = new_profile_response.json()
                                    new_credits = new_profile_data.get('credits_remaining', 0)
                                    
                                    if current_credits is not None:
                                        credit_increase = new_credits - current_credits
                                        if credit_increase > 0:
                                            self.log_test(f"Начисление кредитов - {package_type}", "PASS", 
                                                        f"Кредиты увеличились на {credit_increase} ({current_credits} → {new_credits})")
                                            current_credits = new_credits  # Update for next test
                                        else:
                                            self.log_test(f"Начисление кредитов - {package_type}", "FAIL", 
                                                        f"Кредиты не увеличились: {current_credits} → {new_credits}")
                                    else:
                                        self.log_test(f"Начисление кредитов - {package_type}", "WARN", 
                                                    f"Новый баланс: {new_credits} кредитов")
                                else:
                                    self.log_test(f"Начисление кредитов - {package_type}", "FAIL", 
                                                "Не удалось проверить новый баланс")
                        else:
                            self.log_test(f"Проверка статуса платежа - {package_type}", "FAIL", 
                                        f"HTTP {status_response.status_code}")
                    else:
                        self.log_test(f"Создание платежной сессии - {package_type}", "FAIL", 
                                    "Отсутствует session_id или url в ответе")
                else:
                    self.log_test(f"Создание платежной сессии - {package_type}", "FAIL", 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Платежная система - {package_type}", "FAIL", f"Ошибка: {str(e)}")

    def run_admin_panel_diagnostics(self):
        """Запуск полной диагностики админ панели"""
        print("🚨 КРИТИЧЕСКАЯ ДИАГНОСТИКА: Ошибки в админ панели NUMEROM")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.authenticate_super_admin():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось аутентифицировать супер админа")
            return False
        
        # Step 2: Test all admin panel tabs
        self.test_admin_users_tab()
        self.test_admin_lessons_tab()
        self.test_admin_materials_tab()
        self.test_admin_consultations_tab()
        
        # Step 3: Test user management features
        self.test_user_credits_management()
        self.test_user_lesson_progress()
        
        # Step 4: Test payment and credits system
        self.test_payment_system()
        
        # Summary
        self.print_diagnostic_summary()
        
        return True
    
    def print_diagnostic_summary(self):
        """Печать итогового диагностического отчёта"""
        print("\n" + "=" * 80)
        print("🔍 ДИАГНОСТИЧЕСКИЙ ОТЧЁТ: АДМИН ПАНЕЛЬ И СИСТЕМА БАЛЛОВ")
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
                if any(keyword in result['test'].lower() for keyword in ['админ панель', 'ученики', 'занятия', 'материалы', 'консультации']):
                    admin_panel_issues.append(result)
                elif any(keyword in result['test'].lower() for keyword in ['кредит', 'платеж', 'баланс', 'начисление']):
                    credits_system_issues.append(result)
        
        print("\n🎯 АНАЛИЗ ПРОБЛЕМ:")
        
        if admin_panel_issues:
            print(f"\n❌ ПРОБЛЕМЫ АДМИН ПАНЕЛИ ({len(admin_panel_issues)}):")
            for issue in admin_panel_issues:
                print(f"  • {issue['test']}: {issue['details']}")
        else:
            print("\n✅ АДМИН ПАНЕЛЬ: Критических проблем не обнаружено")
        
        if credits_system_issues:
            print(f"\n❌ ПРОБЛЕМЫ СИСТЕМЫ БАЛЛОВ ({len(credits_system_issues)}):")
            for issue in credits_system_issues:
                print(f"  • {issue['test']}: {issue['details']}")
        else:
            print("\n✅ СИСТЕМА БАЛЛОВ: Критических проблем не обнаружено")
        
        # Final assessment
        critical_issues = len(admin_panel_issues) + len(credits_system_issues)
        
        if critical_issues == 0:
            print(f"\n🎉 ЗАКЛЮЧЕНИЕ: Критические проблемы НЕ ПОДТВЕРЖДЕНЫ")
            print("Админ панель и система баллов работают корректно!")
        else:
            print(f"\n🚨 ЗАКЛЮЧЕНИЕ: Обнаружено {critical_issues} критических проблем")
            print("Требуется немедленное исправление!")

def main():
    """Главная функция запуска диагностики"""
    tester = AdminPanelTester()
    
    try:
        success = tester.run_admin_panel_diagnostics()
        if success:
            print("\n✅ Диагностика завершена успешно")
            return 0
        else:
            print("\n❌ Диагностика завершена с ошибками")
            return 1
    except KeyboardInterrupt:
        print("\n⏹️ Диагностика прервана пользователем")
        return 1
    except Exception as e:
        print(f"\n💥 Критическая ошибка диагностики: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())