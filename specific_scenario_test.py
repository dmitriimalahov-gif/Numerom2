#!/usr/bin/env python3
"""
СПЕЦИФИЧЕСКИЙ ТЕСТ: Конкретный сценарий из review request
Пользователь покупает пакет за 0.99€ (должен получить 10 баллов)
"""

import requests
import json
import uuid
from datetime import datetime
import sys
import time

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

class SpecificScenarioTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        
    def log_test(self, test_name, status, details=""):
        """Log test results"""
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {details}")
        
    def create_test_user_with_zero_credits(self):
        """Создать тестового пользователя с 0 баллов"""
        print("\n👤 СОЗДАНИЕ ТЕСТОВОГО ПОЛЬЗОВАТЕЛЯ С 0 БАЛЛОВ")
        
        test_id = str(uuid.uuid4())[:8]
        test_email = f"zero_credits_{test_id}@example.com"
        test_password = "TestPassword123!"
        
        user_data = {
            "email": test_email,
            "password": test_password,
            "full_name": f"Zero Credits User {test_id}",
            "birth_date": "15.03.1990",
            "city": "Москва",
            "phone_number": "+7900123456"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.user_data = data.get('user')
                
                if self.auth_token and self.user_data:
                    self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                    self.test_email = test_email
                    self.test_password = test_password
                    
                    initial_credits = self.user_data.get('credits_remaining', 0)
                    user_id = self.user_data.get('id')
                    
                    # Manually set credits to 0 for this test
                    # (New users get 1 credit by default, but we want to test from 0)
                    
                    self.log_test("Создание тестового пользователя", "PASS", 
                                f"Email: {test_email}, ID: {user_id}, Начальные баллы: {initial_credits}")
                    return True
                    
            self.log_test("Создание тестового пользователя", "FAIL", f"HTTP {response.status_code}")
            return False
            
        except Exception as e:
            self.log_test("Создание тестового пользователя", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def get_current_credits(self):
        """Получить текущий баланс"""
        try:
            login_data = {
                "email": self.test_email,
                "password": self.test_password
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                user_data = data.get('user')
                if user_data:
                    return user_data.get('credits_remaining', 0)
            
            return None
            
        except Exception as e:
            print(f"Ошибка получения баланса: {str(e)}")
            return None
    
    def test_exact_scenario_from_review(self):
        """Тест точного сценария из review request"""
        print("\n🎯 ТЕСТ ТОЧНОГО СЦЕНАРИЯ ИЗ REVIEW REQUEST")
        print("Сценарий: Пользователь покупает пакет 'one_time' за 0.99€ (должен получить РОВНО 10 баллов)")
        
        # Step 1: Record initial balance
        initial_credits = self.get_current_credits()
        if initial_credits is None:
            self.log_test("Получение начального баланса", "FAIL", "Не удалось получить баланс")
            return False
            
        print(f"📊 Начальный баланс: {initial_credits} баллов")
        
        # Step 2: Create checkout session for 'one_time' package
        payment_data = {
            "package_type": "one_time",
            "origin_url": "https://numerology-fix.preview.emergentagent.com"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/payments/checkout/session", json=payment_data)
            
            if response.status_code == 200:
                checkout_data = response.json()
                session_id = checkout_data.get('session_id')
                checkout_url = checkout_data.get('url')
                
                self.log_test("Создание checkout сессии", "PASS", f"Session ID: {session_id}")
                print(f"💳 Checkout URL: {checkout_url}")
                
                # Step 3: Check payment status (this triggers credit allocation)
                time.sleep(1)
                
                status_response = self.session.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    payment_status = status_data.get('payment_status')
                    amount_total = status_data.get('amount_total')
                    currency = status_data.get('currency')
                    
                    self.log_test("Проверка статуса платежа", "PASS", 
                                f"Статус: {payment_status}, Сумма: {amount_total/100:.2f} {currency}")
                    
                    # Step 4: Verify final balance
                    time.sleep(1)
                    final_credits = self.get_current_credits()
                    
                    if final_credits is not None:
                        credits_added = final_credits - initial_credits
                        
                        print(f"📊 Финальный баланс: {final_credits} баллов")
                        print(f"📊 Добавлено баллов: {credits_added}")
                        print(f"📊 Ожидалось баллов: 10")
                        
                        # Step 5: Verify exact amount
                        if credits_added == 10:
                            self.log_test("КРИТИЧЕСКИЙ ТЕСТ: Точное начисление", "PASS", 
                                        f"✅ УСПЕХ! Начислено РОВНО 10 баллов (было {initial_credits}, стало {final_credits})")
                            
                            # Step 6: Test multiple status checks to ensure no duplication
                            print("\n🔄 ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: Множественные запросы статуса")
                            
                            for i in range(3):
                                time.sleep(0.5)
                                duplicate_response = self.session.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
                                if duplicate_response.status_code == 200:
                                    current_credits = self.get_current_credits()
                                    if current_credits != final_credits:
                                        self.log_test(f"Проверка дублирования #{i+1}", "FAIL", 
                                                    f"ДУБЛИРОВАНИЕ! Баллы изменились: {final_credits} → {current_credits}")
                                        return False
                                    else:
                                        self.log_test(f"Проверка дублирования #{i+1}", "PASS", 
                                                    f"Баллы не изменились: {current_credits}")
                            
                            return True
                            
                        elif credits_added == 20:
                            self.log_test("КРИТИЧЕСКИЙ ТЕСТ: Точное начисление", "FAIL", 
                                        f"❌ ДВОЙНОЕ НАЧИСЛЕНИЕ! Начислено {credits_added} баллов вместо 10")
                            return False
                            
                        else:
                            self.log_test("КРИТИЧЕСКИЙ ТЕСТ: Точное начисление", "FAIL", 
                                        f"❌ НЕВЕРНОЕ НАЧИСЛЕНИЕ! Начислено {credits_added} баллов вместо 10")
                            return False
                    else:
                        self.log_test("Получение финального баланса", "FAIL", "Не удалось получить финальный баланс")
                        return False
                else:
                    self.log_test("Проверка статуса платежа", "FAIL", f"HTTP {status_response.status_code}")
                    return False
            else:
                self.log_test("Создание checkout сессии", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Тест сценария", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def run_specific_scenario_test(self):
        """Запуск теста конкретного сценария"""
        print("🎯 ТЕСТ КОНКРЕТНОГО СЦЕНАРИЯ ИЗ REVIEW REQUEST")
        print("=" * 70)
        print("ЗАДАЧА: Пользователь покупает пакет за 0.99€ (должен получить РОВНО 10 баллов)")
        print("=" * 70)
        
        # Step 1: Create test user
        if not self.create_test_user_with_zero_credits():
            print("❌ Не удалось создать тестового пользователя")
            return False
        
        # Step 2: Test exact scenario
        success = self.test_exact_scenario_from_review()
        
        if success:
            print("\n🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
            print("✅ Пакет 'one_time' начисляет РОВНО 10 баллов")
            print("✅ Дублирование не обнаружено")
            print("✅ Проблема двойного начисления ИСПРАВЛЕНА")
        else:
            print("\n❌ ТЕСТ ПРОВАЛЕН!")
            print("🚨 Обнаружена проблема с начислением баллов")
        
        return success

def main():
    """Главная функция"""
    tester = SpecificScenarioTester()
    
    try:
        success = tester.run_specific_scenario_test()
        return 0 if success else 1
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())