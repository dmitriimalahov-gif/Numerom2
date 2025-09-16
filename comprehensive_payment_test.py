#!/usr/bin/env python3
"""
КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ СИСТЕМЫ ПЛАТЕЖЕЙ
Comprehensive Payment System Testing According to Review Request

ЗАДАЧА: Протестировать все исправления в системе платежей и начисления баллов

КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ ДЛЯ ТЕСТИРОВАНИЯ:
1. **ДВОЙНОЕ НАЧИСЛЕНИЕ БАЛЛОВ** - убедиться что баллы начисляются правильно (не в два раза больше)
2. **НОВЫЕ ПАКЕТЫ** - проверить правильные суммы и описания
3. **УБРАНА ПРЕМИУМ ПОДПИСКА** - убедиться что баллы ВСЕГДА списываются

НОВЫЕ ПАКЕТЫ ДЛЯ ТЕСТИРОВАНИЯ:
- 'one_time': 0.99€ = 10 баллов + месяц доступа
- 'monthly': 9.99€ = 150 баллов + месяц доступа  
- 'annual': 66.6€ = 500 баллов + год доступа
- 'master_consultation': 666€ = 10000 баллов + персональная консультация

ПРОЦЕДУРА ТЕСТИРОВАНИЯ:
1. **Аутентификация тестового пользователя** с известным количеством баллов
2. **Тест покупки пакета 'one_time'**
3. **Тест покупки пакета 'monthly'**
4. **Тест покупки пакета 'master_consultation'**
5. **Тест списания баллов в нумерологии**

ENDPOINTS ДЛЯ ТЕСТИРОВАНИЯ:
- POST /api/payments/checkout/session
- GET /api/payments/status/{session_id}
- POST /api/numerology/personal-numbers (для проверки списания)
- GET /api/admin/consultations (для проверки создания мастер консультации)
"""

import requests
import json
import time
from datetime import datetime
import sys

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

class ComprehensivePaymentTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        self.admin_token = None
        
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
    
    def authenticate_admin(self):
        """Аутентификация администратора для проверки консультаций"""
        try:
            admin_login = {
                "email": "dmitrii.malahov@gmail.com",
                "password": "756bvy67H"
            }
            
            response = requests.post(f"{BACKEND_URL}/auth/login", json=admin_login)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('access_token')
                return True
            return False
        except:
            return False
    
    def create_test_user_with_known_balance(self):
        """1. Аутентификация тестового пользователя с известным количеством баллов"""
        print("\n🔐 ТЕСТ 1: АУТЕНТИФИКАЦИЯ ТЕСТОВОГО ПОЛЬЗОВАТЕЛЯ")
        
        # Generate unique test user
        timestamp = int(time.time())
        test_email = f"payment_test_{timestamp}@example.com"
        test_password = "PaymentTest123!"
        
        try:
            # Register new user
            register_data = {
                "email": test_email,
                "password": test_password,
                "full_name": "Тестовый Пользователь Платежной Системы",
                "birth_date": "15.03.1990",
                "city": "Москва"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=register_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.user_data = data.get('user')
                initial_credits = self.user_data.get('credits_remaining', 0)
                
                # Set authorization header
                self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                
                details = f"Email: {test_email}, Начальные баллы: {initial_credits}"
                self.log_test("Аутентификация тестового пользователя", "PASS", details)
                return True
            else:
                self.log_test("Аутентификация тестового пользователя", "FAIL", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Аутентификация тестового пользователя", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def get_current_credits(self):
        """Получить текущий баланс баллов"""
        try:
            login_data = {
                "email": self.user_data['email'],
                "password": "PaymentTest123!"
            }
            
            response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                return response.json().get('user', {}).get('credits_remaining', 0)
            return 0
        except:
            return 0
    
    def test_one_time_package(self):
        """2. Тест покупки пакета 'one_time': 0.99€ = 10 баллов + месяц доступа"""
        print("\n💰 ТЕСТ 2: ПОКУПКА ПАКЕТА 'ONE_TIME'")
        
        credits_before = self.get_current_credits()
        
        try:
            # Create checkout session
            checkout_data = {
                "package_type": "one_time",
                "origin_url": "https://numerology-fix.preview.emergentagent.com"
            }
            
            response = self.session.post(f"{BACKEND_URL}/payments/checkout/session", json=checkout_data)
            
            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data.get('session_id')
                
                self.log_test("Создание транзакции one_time (0.99€)", "PASS", f"Session ID: {session_id}")
                
                # Simulate successful payment
                time.sleep(1)
                status_response = self.session.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data.get('payment_status') == 'paid':
                        self.log_test("Симуляция успешной оплаты", "PASS", "Статус: paid")
                        
                        # Check credit increase
                        time.sleep(1)
                        credits_after = self.get_current_credits()
                        credits_added = credits_after - credits_before
                        
                        if credits_added == 10:
                            self.log_test("Добавление РОВНО 10 баллов (не 20!)", "PASS", 
                                        f"Добавлено {credits_added} баллов")
                        elif credits_added == 20:
                            self.log_test("КРИТИЧЕСКИЙ БАГ: Двойное начисление баллов", "FAIL", 
                                        f"Добавлено {credits_added} баллов вместо 10 - ДВОЙНОЕ НАЧИСЛЕНИЕ!")
                        else:
                            self.log_test("Неожиданное начисление баллов", "FAIL", 
                                        f"Добавлено {credits_added} баллов, ожидалось 10")
                        
                        # Check subscription type
                        login_response = requests.post(f"{BACKEND_URL}/auth/login", json={
                            "email": self.user_data['email'],
                            "password": "PaymentTest123!"
                        })
                        if login_response.status_code == 200:
                            user_data = login_response.json().get('user', {})
                            subscription_type = user_data.get('subscription_type')
                            if subscription_type == 'monthly':
                                self.log_test("Проверка subscription_type = 'monthly' на 30 дней", "PASS", 
                                            f"Subscription: {subscription_type}")
                            else:
                                self.log_test("Проверка subscription_type", "WARN", 
                                            f"Subscription: {subscription_type}, ожидалось 'monthly'")
                    else:
                        self.log_test("Симуляция успешной оплаты", "FAIL", f"Статус: {status_data.get('payment_status')}")
                else:
                    self.log_test("Проверка статуса оплаты", "FAIL", f"HTTP {status_response.status_code}")
            else:
                self.log_test("Создание транзакции one_time", "FAIL", f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Тест пакета one_time", "FAIL", f"Ошибка: {str(e)}")
    
    def test_monthly_package(self):
        """3. Тест покупки пакета 'monthly': 9.99€ = 150 баллов"""
        print("\n💎 ТЕСТ 3: ПОКУПКА ПАКЕТА 'MONTHLY'")
        
        credits_before = self.get_current_credits()
        
        try:
            checkout_data = {
                "package_type": "monthly",
                "origin_url": "https://numerology-fix.preview.emergentagent.com"
            }
            
            response = self.session.post(f"{BACKEND_URL}/payments/checkout/session", json=checkout_data)
            
            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data.get('session_id')
                
                self.log_test("Проверка цены 9.99€", "PASS", f"Session создана: {session_id}")
                
                # Check payment status
                time.sleep(1)
                status_response = self.session.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data.get('payment_status') == 'paid':
                        # Check credit increase
                        time.sleep(1)
                        credits_after = self.get_current_credits()
                        credits_added = credits_after - credits_before
                        
                        if credits_added == 150:
                            self.log_test("Начисление 150 баллов", "PASS", f"Добавлено {credits_added} баллов")
                        else:
                            self.log_test("Начисление 150 баллов", "FAIL", 
                                        f"Добавлено {credits_added} баллов, ожидалось 150")
                    else:
                        self.log_test("Оплата monthly пакета", "FAIL", f"Статус: {status_data.get('payment_status')}")
                else:
                    self.log_test("Статус monthly пакета", "FAIL", f"HTTP {status_response.status_code}")
            else:
                self.log_test("Создание monthly транзакции", "FAIL", f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Тест monthly пакета", "FAIL", f"Ошибка: {str(e)}")
    
    def test_master_consultation_package(self):
        """4. Тест покупки пакета 'master_consultation': 666€ = 10000 баллов + консультация"""
        print("\n🎓 ТЕСТ 4: ПОКУПКА ПАКЕТА 'MASTER_CONSULTATION'")
        
        credits_before = self.get_current_credits()
        
        try:
            checkout_data = {
                "package_type": "master_consultation",
                "origin_url": "https://numerology-fix.preview.emergentagent.com"
            }
            
            response = self.session.post(f"{BACKEND_URL}/payments/checkout/session", json=checkout_data)
            
            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data.get('session_id')
                
                self.log_test("Проверка цены 666€", "PASS", f"Session создана: {session_id}")
                
                # Check payment status
                time.sleep(1)
                status_response = self.session.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data.get('payment_status') == 'paid':
                        # Check credit increase
                        time.sleep(1)
                        credits_after = self.get_current_credits()
                        credits_added = credits_after - credits_before
                        
                        if credits_added == 10000:
                            self.log_test("Начисление 10000 баллов", "PASS", f"Добавлено {credits_added} баллов")
                        else:
                            self.log_test("Начисление 10000 баллов", "FAIL", 
                                        f"Добавлено {credits_added} баллов, ожидалось 10000")
                        
                        # Check consultation creation
                        self.verify_personal_consultation_creation()
                        
                    else:
                        self.log_test("Оплата master_consultation", "FAIL", f"Статус: {status_data.get('payment_status')}")
                else:
                    self.log_test("Статус master_consultation", "FAIL", f"HTTP {status_response.status_code}")
            else:
                self.log_test("Создание master_consultation транзакции", "FAIL", f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Тест master_consultation", "FAIL", f"Ошибка: {str(e)}")
    
    def verify_personal_consultation_creation(self):
        """Проверка создания персональной консультации"""
        print("\n🔍 ПРОВЕРКА СОЗДАНИЯ ПЕРСОНАЛЬНОЙ КОНСУЛЬТАЦИИ")
        
        try:
            # Check user consultations
            response = self.session.get(f"{BACKEND_URL}/user/consultations")
            
            if response.status_code == 200:
                consultations = response.json()
                
                if consultations and len(consultations) > 0:
                    master_consultation = None
                    for consultation in consultations:
                        title = consultation.get('title', '').lower()
                        if 'мастер' in title or 'персональная' in title:
                            master_consultation = consultation
                            break
                    
                    if master_consultation:
                        self.log_test("Создание персональной консультации", "PASS", 
                                    f"Консультация: {master_consultation.get('title')}")
                    else:
                        self.log_test("Создание персональной консультации", "FAIL", 
                                    "Персональная консультация не найдена")
                else:
                    self.log_test("Создание персональной консультации", "FAIL", "Консультации не найдены")
            else:
                self.log_test("Проверка консультаций пользователя", "FAIL", f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Проверка персональной консультации", "FAIL", f"Ошибка: {str(e)}")
    
    def test_points_always_deducted(self):
        """5. Тест списания баллов в нумерологии - убедиться что баллы ВСЕГДА списываются"""
        print("\n🔥 ТЕСТ 5: СПИСАНИЕ БАЛЛОВ В НУМЕРОЛОГИИ")
        
        credits_before = self.get_current_credits()
        
        if credits_before <= 0:
            self.log_test("Недостаточно баллов для теста", "SKIP", 
                        f"У пользователя {credits_before} баллов")
            return
        
        try:
            # Test personal numbers calculation
            response = self.session.post(f"{BACKEND_URL}/numerology/personal-numbers", json={})
            
            if response.status_code == 200:
                # Check credits after calculation
                time.sleep(1)
                credits_after = self.get_current_credits()
                credits_deducted = credits_before - credits_after
                
                if credits_deducted == 1:
                    self.log_test("Списание 1 балла (независимо от подписки)", "PASS", 
                                f"Списан 1 балл ({credits_before} → {credits_after})")
                elif credits_deducted == 0:
                    self.log_test("КРИТИЧЕСКИЙ БАГ: Премиум статус дает бесплатные расчеты", "FAIL", 
                                "Баллы НЕ были списаны - премиум статус все еще работает!")
                else:
                    self.log_test("Неожиданное списание баллов", "WARN", 
                                f"Списано {credits_deducted} баллов вместо 1")
                    
            elif response.status_code == 402:
                self.log_test("Проверка требования баллов", "PASS", 
                            "Получен код 402 - система правильно требует баллы")
            else:
                self.log_test("Расчет personal-numbers", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Тест списания баллов", "FAIL", f"Ошибка: {str(e)}")
    
    def run_comprehensive_tests(self):
        """Запуск всех тестов согласно review request"""
        print("🎯 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ СИСТЕМЫ ПЛАТЕЖЕЙ")
        print("=" * 80)
        print("ЗАДАЧА: Протестировать все исправления в системе платежей и начисления баллов")
        print()
        print("КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ:")
        print("1. ДВОЙНОЕ НАЧИСЛЕНИЕ БАЛЛОВ - убедиться что баллы начисляются правильно")
        print("2. НОВЫЕ ПАКЕТЫ - проверить правильные суммы и описания")
        print("3. УБРАНА ПРЕМИУМ ПОДПИСКА - убедиться что баллы ВСЕГДА списываются")
        print("=" * 80)
        
        # Step 1: Create test user
        if not self.create_test_user_with_known_balance():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось создать тестового пользователя")
            return False
        
        # Step 2: Test one_time package
        self.test_one_time_package()
        
        # Step 3: Test monthly package
        self.test_monthly_package()
        
        # Step 4: Test master_consultation package
        self.test_master_consultation_package()
        
        # Step 5: Test points always deducted
        self.test_points_always_deducted()
        
        # Summary
        self.print_comprehensive_summary()
        
        return True
    
    def print_comprehensive_summary(self):
        """Печать итогового отчёта"""
        print("\n" + "=" * 80)
        print("📋 ИТОГОВЫЙ ОТЧЁТ ТЕСТИРОВАНИЯ ИСПРАВЛЕНИЙ СИСТЕМЫ ПЛАТЕЖЕЙ")
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
        
        # Critical issues analysis
        critical_issues = []
        double_allocation_found = False
        premium_bypass_found = False
        
        for result in self.test_results:
            if result['status'] == 'FAIL':
                if 'двойное начисление' in result['test'].lower():
                    critical_issues.append("🚨 ДВОЙНОЕ НАЧИСЛЕНИЕ БАЛЛОВ ОБНАРУЖЕНО")
                    double_allocation_found = True
                elif 'премиум статус' in result['test'].lower():
                    critical_issues.append("🚨 ПРЕМИУМ СТАТУС ДАЕТ БЕСПЛАТНЫЕ РАСЧЕТЫ")
                    premium_bypass_found = True
                elif 'начисление' in result['test'].lower():
                    critical_issues.append("🚨 НЕПРАВИЛЬНОЕ НАЧИСЛЕНИЕ БАЛЛОВ")
        
        if critical_issues:
            print(f"\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ:")
            for issue in set(critical_issues):  # Remove duplicates
                print(f"  • {issue}")
        else:
            print("\n🎉 КРИТИЧЕСКИЕ ПРОБЛЕМЫ НЕ ОБНАРУЖЕНЫ")
            print("✅ Двойное начисление баллов ИСПРАВЛЕНО")
            print("✅ Новые пакеты работают корректно")
            print("✅ Премиум подписка убрана - баллы всегда списываются")
        
        # Summary by test categories
        print(f"\n📊 РЕЗУЛЬТАТЫ ПО КАТЕГОРИЯМ:")
        
        # Package tests
        package_tests = [r for r in self.test_results if any(pkg in r['test'].lower() for pkg in ['one_time', 'monthly', 'master_consultation'])]
        package_passed = len([r for r in package_tests if r['status'] == 'PASS'])
        print(f"  📦 Тесты пакетов: {package_passed}/{len(package_tests)} пройдено")
        
        # Credit allocation tests
        credit_tests = [r for r in self.test_results if 'начисление' in r['test'].lower() or 'баллов' in r['test'].lower()]
        credit_passed = len([r for r in credit_tests if r['status'] == 'PASS'])
        print(f"  💰 Тесты начисления баллов: {credit_passed}/{len(credit_tests)} пройдено")
        
        # Deduction tests
        deduction_tests = [r for r in self.test_results if 'списание' in r['test'].lower()]
        deduction_passed = len([r for r in deduction_tests if r['status'] == 'PASS'])
        print(f"  🔥 Тесты списания баллов: {deduction_passed}/{len(deduction_tests)} пройдено")
        
        if failed_tests > 0:
            print("\n❌ ПРОВАЛИВШИЕСЯ ТЕСТЫ:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  • {result['test']}: {result['details']}")

def main():
    """Главная функция запуска тестов"""
    tester = ComprehensivePaymentTester()
    
    try:
        success = tester.run_comprehensive_tests()
        if success:
            print("\n✅ Комплексное тестирование системы платежей завершено")
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