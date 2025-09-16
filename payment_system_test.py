#!/usr/bin/env python3
"""
ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ СИСТЕМЫ БАЛЛОВ И НОВЫХ ПАКЕТОВ
Testing Payment System Fixes and New Packages

Согласно review request:
1. ДВОЙНОЕ НАЧИСЛЕНИЕ БАЛЛОВ - убедиться что баллы начисляются правильно (не в два раза больше)
2. НОВЫЕ ПАКЕТЫ - проверить правильные суммы и описания
3. УБРАНА ПРЕМИУМ ПОДПИСКА - убедиться что баллы ВСЕГДА списываются

НОВЫЕ ПАКЕТЫ:
- 'one_time': 0.99€ = 10 баллов + месяц доступа
- 'monthly': 9.99€ = 150 баллов + месяц доступа  
- 'annual': 66.6€ = 500 баллов + год доступа
- 'master_consultation': 666€ = 10000 баллов + персональная консультация
"""

import requests
import json
import time
from datetime import datetime
import sys

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

class PaymentSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        self.initial_credits = 0
        
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
        
    def create_test_user(self):
        """Создание тестового пользователя с известным количеством баллов"""
        print("\n👤 СОЗДАНИЕ ТЕСТОВОГО ПОЛЬЗОВАТЕЛЯ")
        
        # Generate unique test user
        timestamp = int(time.time())
        test_email = f"test_payment_{timestamp}@example.com"
        test_password = "TestPassword123!"
        
        try:
            # Register new user
            register_data = {
                "email": test_email,
                "password": test_password,
                "full_name": "Тестовый Пользователь Платежей",
                "birth_date": "15.03.1990",
                "city": "Москва"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=register_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.user_data = data.get('user')
                self.initial_credits = self.user_data.get('credits_remaining', 0)
                
                # Set authorization header
                self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                
                details = f"Email: {test_email}, Начальные баллы: {self.initial_credits}"
                self.log_test("Создание тестового пользователя", "PASS", details)
                return True
            else:
                self.log_test("Создание тестового пользователя", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Создание тестового пользователя", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def get_current_credits(self):
        """Получить текущий баланс баллов пользователя"""
        try:
            # Login to get fresh user data
            login_data = {
                "email": self.user_data['email'],
                "password": "TestPassword123!"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                return data.get('user', {}).get('credits_remaining', 0)
            return 0
        except:
            return 0
    
    def test_package_prices_and_credits(self):
        """Проверка правильности цен и начисления баллов для новых пакетов"""
        print("\n💰 ТЕСТ НОВЫХ ПАКЕТОВ И ЦЕН")
        
        # Expected package configuration
        expected_packages = {
            'one_time': {'price': 0.99, 'credits': 10, 'description': '10 баллов + месяц доступа'},
            'monthly': {'price': 9.99, 'credits': 150, 'description': '150 баллов + месяц доступа'},
            'annual': {'price': 66.6, 'credits': 500, 'description': '500 баллов + год доступа'},
            'master_consultation': {'price': 666.0, 'credits': 10000, 'description': '10000 баллов + персональная консультация'}
        }
        
        for package_type, expected in expected_packages.items():
            self.test_single_package_purchase(package_type, expected)
    
    def test_single_package_purchase(self, package_type, expected):
        """Тест покупки одного пакета"""
        print(f"\n🛒 ТЕСТ ПОКУПКИ ПАКЕТА: {package_type}")
        
        # Get credits before purchase
        credits_before = self.get_current_credits()
        
        try:
            # Step 1: Create checkout session
            checkout_data = {
                "package_type": package_type,
                "origin_url": "https://numerology-fix.preview.emergentagent.com"
            }
            
            response = self.session.post(f"{BACKEND_URL}/payments/checkout/session", json=checkout_data)
            
            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data.get('session_id')
                
                if session_id:
                    self.log_test(f"Создание сессии {package_type}", "PASS", f"Session ID: {session_id}")
                    
                    # Step 2: Check payment status (demo mode should auto-complete)
                    time.sleep(1)  # Brief delay for processing
                    
                    status_response = self.session.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        payment_status = status_data.get('payment_status')
                        
                        if payment_status == 'paid':
                            self.log_test(f"Статус оплаты {package_type}", "PASS", f"Статус: {payment_status}")
                            
                            # Step 3: Verify credit increase
                            time.sleep(1)  # Allow time for credit processing
                            credits_after = self.get_current_credits()
                            credits_added = credits_after - credits_before
                            
                            expected_credits = expected['credits']
                            
                            if credits_added == expected_credits:
                                self.log_test(f"Начисление баллов {package_type}", "PASS", 
                                            f"Добавлено РОВНО {credits_added} баллов (ожидалось {expected_credits})")
                                
                                # Check for double allocation bug
                                if credits_added == expected_credits * 2:
                                    self.log_test(f"КРИТИЧЕСКИЙ БАГ: Двойное начисление {package_type}", "FAIL", 
                                                f"Начислено {credits_added} вместо {expected_credits} - ДВОЙНОЕ НАЧИСЛЕНИЕ!")
                                
                            else:
                                self.log_test(f"Начисление баллов {package_type}", "FAIL", 
                                            f"Начислено {credits_added} баллов, ожидалось {expected_credits}")
                            
                            # Step 4: Check master consultation creation (if applicable)
                            if package_type == 'master_consultation':
                                self.verify_master_consultation_creation()
                                
                        else:
                            self.log_test(f"Статус оплаты {package_type}", "FAIL", f"Неожиданный статус: {payment_status}")
                    else:
                        self.log_test(f"Статус оплаты {package_type}", "FAIL", f"HTTP {status_response.status_code}")
                else:
                    self.log_test(f"Создание сессии {package_type}", "FAIL", "Отсутствует session_id")
            else:
                self.log_test(f"Создание сессии {package_type}", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test(f"Покупка пакета {package_type}", "FAIL", f"Ошибка: {str(e)}")
    
    def verify_master_consultation_creation(self):
        """Проверка создания персональной консультации для мастер пакета"""
        print("\n🎓 ПРОВЕРКА СОЗДАНИЯ МАСТЕР КОНСУЛЬТАЦИИ")
        
        try:
            # Check if consultation was created
            response = self.session.get(f"{BACKEND_URL}/user/consultations")
            
            if response.status_code == 200:
                consultations = response.json()
                
                if consultations and len(consultations) > 0:
                    # Look for master consultation
                    master_consultation = None
                    for consultation in consultations:
                        if 'мастер' in consultation.get('title', '').lower() or 'персональная' in consultation.get('title', '').lower():
                            master_consultation = consultation
                            break
                    
                    if master_consultation:
                        self.log_test("Создание мастер консультации", "PASS", 
                                    f"Консультация создана: {master_consultation.get('title')}")
                    else:
                        self.log_test("Создание мастер консультации", "FAIL", 
                                    "Мастер консультация не найдена среди пользовательских консультаций")
                else:
                    self.log_test("Создание мастер консультации", "FAIL", "Консультации не найдены")
            else:
                self.log_test("Создание мастер консультации", "FAIL", f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Создание мастер консультации", "FAIL", f"Ошибка: {str(e)}")
    
    def test_points_deduction_always_happens(self):
        """Тест что баллы ВСЕГДА списываются (убрана премиум подписка)"""
        print("\n🔥 ТЕСТ ОБЯЗАТЕЛЬНОГО СПИСАНИЯ БАЛЛОВ")
        
        # Get current credits
        credits_before = self.get_current_credits()
        
        if credits_before <= 0:
            self.log_test("Списание баллов - недостаточно баллов", "SKIP", 
                        f"У пользователя {credits_before} баллов, нужен хотя бы 1 балл для теста")
            return
        
        try:
            # Test personal numbers calculation (should always deduct 1 point)
            response = self.session.post(f"{BACKEND_URL}/numerology/personal-numbers")
            
            if response.status_code == 200:
                # Check credits after calculation
                credits_after = self.get_current_credits()
                credits_deducted = credits_before - credits_after
                
                if credits_deducted == 1:
                    self.log_test("Обязательное списание баллов", "PASS", 
                                f"Списан 1 балл как ожидалось ({credits_before} → {credits_after})")
                elif credits_deducted == 0:
                    self.log_test("КРИТИЧЕСКИЙ БАГ: Баллы не списались", "FAIL", 
                                "Баллы НЕ были списаны - возможно премиум статус все еще дает бесплатные расчеты!")
                else:
                    self.log_test("Неожиданное списание баллов", "WARN", 
                                f"Списано {credits_deducted} баллов вместо 1")
                    
            elif response.status_code == 402:
                # Payment required - this is expected if no credits
                self.log_test("Обязательное списание баллов", "PASS", 
                            "Получен код 402 - система правильно требует баллы")
            else:
                self.log_test("Тест списания баллов", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Тест списания баллов", "FAIL", f"Ошибка: {str(e)}")
    
    def run_payment_system_tests(self):
        """Запуск всех тестов системы платежей"""
        print("🎯 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ СИСТЕМЫ БАЛЛОВ И НОВЫХ ПАКЕТОВ")
        print("=" * 80)
        
        # Step 1: Create test user
        if not self.create_test_user():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось создать тестового пользователя")
            return False
        
        # Step 2: Test new packages and credit allocation
        self.test_package_prices_and_credits()
        
        # Step 3: Test that points are always deducted
        self.test_points_deduction_always_happens()
        
        # Summary
        self.print_test_summary()
        
        return True
    
    def print_test_summary(self):
        """Печать итогового отчёта"""
        print("\n" + "=" * 80)
        print("📋 ИТОГОВЫЙ ОТЧЁТ ТЕСТИРОВАНИЯ СИСТЕМЫ ПЛАТЕЖЕЙ")
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
        for result in self.test_results:
            if result['status'] == 'FAIL':
                if 'двойное начисление' in result['test'].lower():
                    critical_issues.append("🚨 ДВОЙНОЕ НАЧИСЛЕНИЕ БАЛЛОВ")
                elif 'баллы не списались' in result['test'].lower():
                    critical_issues.append("🚨 БАЛЛЫ НЕ СПИСЫВАЮТСЯ")
                elif 'начисление баллов' in result['test'].lower():
                    critical_issues.append("🚨 НЕПРАВИЛЬНОЕ НАЧИСЛЕНИЕ БАЛЛОВ")
        
        if critical_issues:
            print(f"\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ:")
            for issue in critical_issues:
                print(f"  • {issue}")
        else:
            print("\n🎉 КРИТИЧЕСКИЕ ПРОБЛЕМЫ НЕ ОБНАРУЖЕНЫ")
            print("Система платежей работает корректно!")
        
        if failed_tests > 0:
            print("\n❌ ПРОВАЛИВШИЕСЯ ТЕСТЫ:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  • {result['test']}: {result['details']}")

def main():
    """Главная функция запуска тестов"""
    tester = PaymentSystemTester()
    
    try:
        success = tester.run_payment_system_tests()
        if success:
            print("\n✅ Тестирование системы платежей завершено")
            return 0
        else:
            print("\n❌ Тестирование системы платежей завершено с ошибками")
            return 1
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        return 1
    except Exception as e:
        print(f"\n💥 Критическая ошибка тестирования: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())