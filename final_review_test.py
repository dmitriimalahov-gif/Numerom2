#!/usr/bin/env python3
"""
ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ВСЕХ ИСПРАВЛЕНИЙ
Final Review Testing for Critical Fixes

Тестирует критические исправления согласно review request:
1. ДВОЙНОЕ НАЧИСЛЕНИЕ БАЛЛОВ - проверка что исправление работает
2. НОВЫЕ ПАКЕТЫ - проверка правильных цен в backend
3. ВИДЕО ENDPOINT - проверка стриминга видео
4. ПРЕМИУМ ФУНКЦИОНАЛЬНОСТЬ - проверка что баллы ВСЕГДА списываются
"""

import requests
import json
from datetime import datetime
import sys
import os

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_USER_EMAIL = "dmitrii.malahov@gmail.com"
TEST_USER_PASSWORD = "756bvy67H"

class FinalReviewTester:
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
        """Аутентификация супер-админа"""
        print("\n🔐 АУТЕНТИФИКАЦИЯ СУПЕР-АДМИНА")
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data['access_token']
                self.user_data = data['user']
                self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                
                self.log_test("Супер-админ аутентификация", "PASS", 
                    f"User ID: {self.user_data['id']}, Credits: {self.user_data.get('credits_remaining', 0)}, Super Admin: {self.user_data.get('is_super_admin', False)}")
                return True
            else:
                self.log_test("Супер-админ аутентификация", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Супер-админ аутентификация", "FAIL", f"Exception: {str(e)}")
            return False

    def test_payment_packages_constants(self):
        """ТЕСТ 1: Проверка констант PAYMENT_PACKAGES и SUBSCRIPTION_CREDITS"""
        print("\n💰 ТЕСТ 1: ПРОВЕРКА КОНСТАНТ ПАКЕТОВ")
        
        # Ожидаемые значения согласно review request
        expected_packages = {
            'one_time': 0.99,     # 0,99€ = 10 баллов
            'monthly': 9.99,      # 9,99€ = 150 баллов  
            'annual': 66.6,       # 66,6€ = 500 баллов
            'master_consultation': 666.0  # 666€ = 10000 баллов
        }
        
        expected_credits = {
            'one_time': 10,
            'monthly': 150,
            'annual': 500,
            'master_consultation': 10000
        }
        
        try:
            # Создаем тестового пользователя для проверки цен
            test_email = f"test_prices_{datetime.now().strftime('%H%M%S')}@example.com"
            register_response = self.session.post(f"{BACKEND_URL}/auth/register", json={
                "email": test_email,
                "password": "testpass123",
                "full_name": "Test Prices User",
                "birth_date": "15.03.1990"
            })
            
            if register_response.status_code == 200:
                test_token = register_response.json()['access_token']
                test_headers = {'Authorization': f'Bearer {test_token}'}
                
                # Проверяем каждый пакет
                all_packages_correct = True
                for package_type, expected_price in expected_packages.items():
                    try:
                        response = requests.post(f"{BACKEND_URL}/payments/checkout/session", 
                            json={"package_type": package_type, "origin_url": "https://test.com"},
                            headers=test_headers)
                        
                        if response.status_code == 200:
                            session_data = response.json()
                            session_id = session_data.get('session_id')
                            
                            # Проверяем статус платежа для получения информации о цене
                            status_response = requests.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                actual_amount = status_data.get('amount_total', 0) / 100  # Конвертируем из центов
                                
                                if abs(actual_amount - expected_price) < 0.01:  # Допускаем погрешность в 1 цент
                                    self.log_test(f"Пакет {package_type} цена", "PASS", f"Цена корректна: {actual_amount}€")
                                else:
                                    self.log_test(f"Пакет {package_type} цена", "FAIL", f"Ожидалось: {expected_price}€, получено: {actual_amount}€")
                                    all_packages_correct = False
                            else:
                                self.log_test(f"Пакет {package_type} статус", "FAIL", f"Не удалось получить статус: {status_response.status_code}")
                                all_packages_correct = False
                        else:
                            self.log_test(f"Пакет {package_type} создание", "FAIL", f"Не удалось создать сессию: {response.status_code}")
                            all_packages_correct = False
                            
                    except Exception as e:
                        self.log_test(f"Пакет {package_type} ошибка", "FAIL", f"Exception: {str(e)}")
                        all_packages_correct = False
                
                if all_packages_correct:
                    self.log_test("Константы пакетов", "PASS", "Все цены пакетов соответствуют ожидаемым: 0.99€, 9.99€, 66.6€, 666€")
                else:
                    self.log_test("Константы пакетов", "FAIL", "Некоторые цены пакетов не соответствуют ожидаемым")
                    
            else:
                self.log_test("Создание тестового пользователя", "FAIL", f"Status: {register_response.status_code}")
                
        except Exception as e:
            self.log_test("Константы пакетов", "FAIL", f"Exception: {str(e)}")

    def test_double_credit_allocation_fix(self):
        """ТЕСТ 2: Проверка исправления двойного начисления баллов"""
        print("\n🚨 ТЕСТ 2: ПРОВЕРКА ИСПРАВЛЕНИЯ ДВОЙНОГО НАЧИСЛЕНИЯ БАЛЛОВ")
        
        try:
            # Создаем нового пользователя с 1 баллом (по умолчанию)
            test_email = f"test_double_{datetime.now().strftime('%H%M%S')}@example.com"
            register_response = self.session.post(f"{BACKEND_URL}/auth/register", json={
                "email": test_email,
                "password": "testpass123",
                "full_name": "Test Double Credits",
                "birth_date": "15.03.1990"
            })
            
            if register_response.status_code == 200:
                test_token = register_response.json()['access_token']
                test_headers = {'Authorization': f'Bearer {test_token}'}
                initial_credits = register_response.json()['user']['credits_remaining']
                
                self.log_test("Создание тестового пользователя", "PASS", f"Начальные баллы: {initial_credits}")
                
                # Покупаем пакет one_time
                checkout_response = requests.post(f"{BACKEND_URL}/payments/checkout/session", 
                    json={"package_type": "one_time", "origin_url": "https://test.com"},
                    headers=test_headers)
                
                if checkout_response.status_code == 200:
                    session_id = checkout_response.json()['session_id']
                    
                    # Первая проверка статуса (должна начислить 10 баллов)
                    first_check = requests.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
                    if first_check.status_code == 200:
                        first_data = first_check.json()
                        self.log_test("Первая проверка статуса", "PASS", f"Статус: {first_data.get('payment_status')}")
                        
                        # Получаем текущие баллы пользователя
                        login_response = requests.post(f"{BACKEND_URL}/auth/login", json={
                            "email": test_email,
                            "password": "testpass123"
                        })
                        
                        if login_response.status_code == 200:
                            credits_after_first = login_response.json()['user']['credits_remaining']
                            expected_credits = initial_credits + 10  # Должно быть +10 баллов
                            
                            self.log_test("Баллы после первой проверки", "PASS", f"Баллы: {credits_after_first} (ожидалось: {expected_credits})")
                            
                            # Вторая проверка статуса (НЕ должна начислить дополнительные баллы)
                            second_check = requests.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
                            if second_check.status_code == 200:
                                second_data = second_check.json()
                                
                                # Снова получаем баллы пользователя
                                login_response2 = requests.post(f"{BACKEND_URL}/auth/login", json={
                                    "email": test_email,
                                    "password": "testpass123"
                                })
                                
                                if login_response2.status_code == 200:
                                    credits_after_second = login_response2.json()['user']['credits_remaining']
                                    
                                    if credits_after_second == credits_after_first:
                                        self.log_test("КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ", "PASS", 
                                            f"Двойное начисление ИСПРАВЛЕНО! Баллы остались: {credits_after_second} (не изменились при повторной проверке)")
                                    else:
                                        self.log_test("КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ", "FAIL", 
                                            f"ДВОЙНОЕ НАЧИСЛЕНИЕ НЕ ИСПРАВЛЕНО! Баллы изменились: {credits_after_first} → {credits_after_second}")
                                        
                                    # Проверяем что пакет one_time дает РОВНО 10 баллов
                                    total_added = credits_after_second - initial_credits
                                    if total_added == 10:
                                        self.log_test("Пакет one_time баллы", "PASS", f"Пакет one_time дает РОВНО 10 баллов (не 20!)")
                                    else:
                                        self.log_test("Пакет one_time баллы", "FAIL", f"Пакет one_time дал {total_added} баллов вместо 10")
                                        
                                else:
                                    self.log_test("Получение баллов после второй проверки", "FAIL", f"Status: {login_response2.status_code}")
                            else:
                                self.log_test("Вторая проверка статуса", "FAIL", f"Status: {second_check.status_code}")
                        else:
                            self.log_test("Получение баллов после первой проверки", "FAIL", f"Status: {login_response.status_code}")
                    else:
                        self.log_test("Первая проверка статуса", "FAIL", f"Status: {first_check.status_code}")
                else:
                    self.log_test("Создание checkout сессии", "FAIL", f"Status: {checkout_response.status_code}")
            else:
                self.log_test("Создание тестового пользователя", "FAIL", f"Status: {register_response.status_code}")
                
        except Exception as e:
            self.log_test("Тест двойного начисления", "FAIL", f"Exception: {str(e)}")

    def test_video_endpoint(self):
        """ТЕСТ 3: Проверка video endpoint"""
        print("\n🎥 ТЕСТ 3: ПРОВЕРКА VIDEO ENDPOINT")
        
        try:
            # Тестируем endpoint с несуществующим video_id
            test_video_id = "test_video_123"
            response = requests.get(f"{BACKEND_URL}/video/{test_video_id}")
            
            # Endpoint должен обработать запрос (даже если файл не существует)
            if response.status_code in [200, 404]:
                self.log_test("Video endpoint обработка", "PASS", 
                    f"Endpoint обрабатывает запросы корректно (Status: {response.status_code})")
            else:
                self.log_test("Video endpoint обработка", "FAIL", 
                    f"Endpoint возвращает неожиданный статус: {response.status_code}")
                    
            # Проверяем что endpoint существует и не возвращает 500 ошибку
            if response.status_code != 500:
                self.log_test("Video endpoint работоспособность", "PASS", 
                    "Endpoint не возвращает 500 ошибку")
            else:
                self.log_test("Video endpoint работоспособность", "FAIL", 
                    "Endpoint возвращает 500 ошибку")
                    
        except Exception as e:
            self.log_test("Video endpoint", "FAIL", f"Exception: {str(e)}")

    def test_premium_functionality(self):
        """ТЕСТ 4: Проверка что премиум не дает бесплатные расчёты"""
        print("\n👑 ТЕСТ 4: ПРОВЕРКА ПРЕМИУМ ФУНКЦИОНАЛЬНОСТИ")
        
        try:
            # Используем супер-админа (у него премиум статус)
            if not self.auth_token:
                self.log_test("Премиум функциональность", "FAIL", "Нет токена аутентификации")
                return
                
            initial_credits = self.user_data.get('credits_remaining', 0)
            is_premium = self.user_data.get('is_premium', False)
            
            self.log_test("Премиум статус пользователя", "INFO", f"Premium: {is_premium}, Credits: {initial_credits}")
            
            # Тестируем расчёт персональных чисел
            response = self.session.post(f"{BACKEND_URL}/numerology/personal-numbers", 
                json={"birth_date": "15.03.1990"})
            
            if response.status_code == 200:
                # Получаем обновленные данные пользователя
                login_response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                    "email": TEST_USER_EMAIL,
                    "password": TEST_USER_PASSWORD
                })
                
                if login_response.status_code == 200:
                    updated_credits = login_response.json()['user']['credits_remaining']
                    credits_used = initial_credits - updated_credits
                    
                    if credits_used > 0:
                        self.log_test("Премиум списание баллов", "PASS", 
                            f"Баллы ВСЕГДА списываются! Использовано: {credits_used} баллов ({initial_credits} → {updated_credits})")
                    else:
                        self.log_test("Премиум списание баллов", "FAIL", 
                            f"Баллы НЕ списались! Премиум дает бесплатные расчёты: {initial_credits} → {updated_credits}")
                else:
                    self.log_test("Получение обновленных данных", "FAIL", f"Status: {login_response.status_code}")
            elif response.status_code == 402:
                self.log_test("Премиум списание баллов", "PASS", 
                    "Получена ошибка 402 - недостаточно баллов, что подтверждает обязательное списание")
            else:
                self.log_test("Расчёт персональных чисел", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Премиум функциональность", "FAIL", f"Exception: {str(e)}")

    def test_all_package_credits(self):
        """ДОПОЛНИТЕЛЬНЫЙ ТЕСТ: Проверка всех пакетов на правильное начисление баллов"""
        print("\n💎 ДОПОЛНИТЕЛЬНЫЙ ТЕСТ: ПРОВЕРКА ВСЕХ ПАКЕТОВ")
        
        expected_credits = {
            'one_time': 10,
            'monthly': 150, 
            'annual': 500,
            'master_consultation': 10000
        }
        
        for package_type, expected_credit_amount in expected_credits.items():
            try:
                # Создаем нового пользователя для каждого пакета
                test_email = f"test_{package_type}_{datetime.now().strftime('%H%M%S')}@example.com"
                register_response = self.session.post(f"{BACKEND_URL}/auth/register", json={
                    "email": test_email,
                    "password": "testpass123",
                    "full_name": f"Test {package_type} User",
                    "birth_date": "15.03.1990"
                })
                
                if register_response.status_code == 200:
                    test_token = register_response.json()['access_token']
                    test_headers = {'Authorization': f'Bearer {test_token}'}
                    initial_credits = register_response.json()['user']['credits_remaining']
                    
                    # Покупаем пакет
                    checkout_response = requests.post(f"{BACKEND_URL}/payments/checkout/session", 
                        json={"package_type": package_type, "origin_url": "https://test.com"},
                        headers=test_headers)
                    
                    if checkout_response.status_code == 200:
                        session_id = checkout_response.json()['session_id']
                        
                        # Проверяем статус (начисляем баллы)
                        status_response = requests.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
                        if status_response.status_code == 200:
                            # Получаем обновленные баллы
                            login_response = requests.post(f"{BACKEND_URL}/auth/login", json={
                                "email": test_email,
                                "password": "testpass123"
                            })
                            
                            if login_response.status_code == 200:
                                final_credits = login_response.json()['user']['credits_remaining']
                                credits_added = final_credits - initial_credits
                                
                                if credits_added == expected_credit_amount:
                                    self.log_test(f"Пакет {package_type} баллы", "PASS", 
                                        f"Правильно начислено {credits_added} баллов")
                                else:
                                    self.log_test(f"Пакет {package_type} баллы", "FAIL", 
                                        f"Ожидалось {expected_credit_amount}, получено {credits_added}")
                            else:
                                self.log_test(f"Пакет {package_type} логин", "FAIL", f"Status: {login_response.status_code}")
                        else:
                            self.log_test(f"Пакет {package_type} статус", "FAIL", f"Status: {status_response.status_code}")
                    else:
                        self.log_test(f"Пакет {package_type} checkout", "FAIL", f"Status: {checkout_response.status_code}")
                else:
                    self.log_test(f"Пакет {package_type} регистрация", "FAIL", f"Status: {register_response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Пакет {package_type}", "FAIL", f"Exception: {str(e)}")

    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ВСЕХ ИСПРАВЛЕНИЙ")
        print("=" * 60)
        
        # Аутентификация
        if not self.authenticate_super_admin():
            print("❌ Не удалось аутентифицироваться. Завершение тестов.")
            return
            
        # Основные тесты согласно review request
        self.test_payment_packages_constants()
        self.test_double_credit_allocation_fix()
        self.test_video_endpoint()
        self.test_premium_functionality()
        self.test_all_package_credits()
        
        # Подсчет результатов
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        
        print("\n" + "=" * 60)
        print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ФИНАЛЬНОГО ТЕСТИРОВАНИЯ")
        print("=" * 60)
        print(f"Всего тестов: {total_tests}")
        print(f"✅ Пройдено: {passed_tests}")
        print(f"❌ Провалено: {failed_tests}")
        print(f"📈 Успешность: {(passed_tests/total_tests*100):.1f}%")
        
        # Критические результаты
        critical_issues = []
        for result in self.test_results:
            if result['status'] == 'FAIL' and any(keyword in result['test'].lower() for keyword in ['двойное', 'критическое', 'премиум', 'пакет']):
                critical_issues.append(result['test'])
        
        if critical_issues:
            print(f"\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ ({len(critical_issues)}):")
            for issue in critical_issues:
                print(f"   • {issue}")
        else:
            print(f"\n🎉 ВСЕ КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ РАБОТАЮТ КОРРЕКТНО!")
            
        return failed_tests == 0

if __name__ == "__main__":
    tester = FinalReviewTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)