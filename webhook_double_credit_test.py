#!/usr/bin/env python3
"""
WEBHOOK DOUBLE CREDIT TEST: Проверка дублирования через webhook
Testing if webhook causes double credit allocation
"""

import requests
import json
import uuid
from datetime import datetime
import sys
import time

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

class WebhookDoubleCreditTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        
    def log_test(self, test_name, status, details=""):
        """Log test results"""
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {details}")
        
    def create_test_user(self):
        """Создать тестового пользователя"""
        test_id = str(uuid.uuid4())[:8]
        test_email = f"webhook_test_{test_id}@example.com"
        test_password = "TestPassword123!"
        
        user_data = {
            "email": test_email,
            "password": test_password,
            "full_name": f"Webhook Test User {test_id}",
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
    
    def test_multiple_status_checks(self, session_id, package_type, expected_credits):
        """Тестировать множественные проверки статуса (имитация дублирования)"""
        print(f"\n🔄 ТЕСТ МНОЖЕСТВЕННЫХ ПРОВЕРОК СТАТУСА")
        
        initial_credits = self.get_current_credits()
        print(f"📊 Начальный баланс: {initial_credits} баллов")
        
        # Make multiple status checks to see if credits are added multiple times
        for i in range(3):
            print(f"\n🔍 Проверка статуса #{i+1}")
            
            try:
                response = self.session.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
                
                if response.status_code == 200:
                    status_data = response.json()
                    payment_status = status_data.get('payment_status')
                    
                    current_credits = self.get_current_credits()
                    credits_added = current_credits - initial_credits
                    
                    print(f"   Статус: {payment_status}")
                    print(f"   Текущий баланс: {current_credits}")
                    print(f"   Добавлено баллов: {credits_added}")
                    
                    if credits_added > expected_credits:
                        self.log_test(f"Множественная проверка #{i+1}", "FAIL", 
                                    f"ДУБЛИРОВАНИЕ! Добавлено {credits_added} баллов, ожидалось {expected_credits}")
                        return False
                    
                    time.sleep(1)  # Small delay between checks
                else:
                    self.log_test(f"Множественная проверка #{i+1}", "FAIL", f"HTTP {response.status_code}")
                    return False
                    
            except Exception as e:
                self.log_test(f"Множественная проверка #{i+1}", "FAIL", f"Ошибка: {str(e)}")
                return False
        
        final_credits = self.get_current_credits()
        total_added = final_credits - initial_credits
        
        if total_added == expected_credits:
            self.log_test("Множественные проверки статуса", "PASS", 
                        f"Корректно добавлено {total_added} баллов после 3 проверок")
            return True
        else:
            self.log_test("Множественные проверки статуса", "FAIL", 
                        f"ДУБЛИРОВАНИЕ! Добавлено {total_added} баллов, ожидалось {expected_credits}")
            return False
    
    def test_webhook_simulation(self, session_id):
        """Имитация webhook вызова"""
        print(f"\n🎣 ИМИТАЦИЯ WEBHOOK")
        
        # This is a simplified webhook simulation
        # In real scenario, Stripe would send webhook data
        webhook_data = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": session_id,
                    "payment_status": "paid"
                }
            }
        }
        
        try:
            # Note: This might not work exactly like real Stripe webhook
            # but we can test if the endpoint exists and responds
            response = self.session.post(f"{BACKEND_URL}/webhook/stripe", 
                                       json=webhook_data,
                                       headers={'Stripe-Signature': 'test_signature'})
            
            if response.status_code in [200, 400]:  # 400 is expected for invalid signature
                self.log_test("Webhook endpoint", "PASS", f"Endpoint доступен (HTTP {response.status_code})")
                return True
            else:
                self.log_test("Webhook endpoint", "FAIL", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Webhook endpoint", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def test_webhook_duplication_scenario(self):
        """Полный тест сценария дублирования через webhook"""
        print("\n🎯 ТЕСТ СЦЕНАРИЯ ДУБЛИРОВАНИЯ ЧЕРЕЗ WEBHOOK")
        
        # Step 1: Create payment session
        payment_data = {
            "package_type": "one_time",
            "origin_url": "https://numerology-fix.preview.emergentagent.com"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/payments/checkout/session", json=payment_data)
            
            if response.status_code == 200:
                checkout_data = response.json()
                session_id = checkout_data.get('session_id')
                
                if session_id:
                    self.log_test("Создание платежной сессии", "PASS", f"Session ID: {session_id}")
                    
                    # Step 2: Test multiple status checks
                    success = self.test_multiple_status_checks(session_id, "one_time", 10)
                    
                    # Step 3: Test webhook simulation
                    self.test_webhook_simulation(session_id)
                    
                    return success
                else:
                    self.log_test("Создание платежной сессии", "FAIL", "Отсутствует session_id")
                    return False
            else:
                self.log_test("Создание платежной сессии", "FAIL", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Создание платежной сессии", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def run_webhook_test(self):
        """Запуск теста webhook дублирования"""
        print("🎣 ТЕСТ ДУБЛИРОВАНИЯ ЧЕРЕЗ WEBHOOK")
        print("=" * 60)
        
        # Step 1: Create test user
        if not self.create_test_user():
            print("❌ Не удалось создать тестового пользователя")
            return False
        
        # Step 2: Test webhook duplication scenario
        success = self.test_webhook_duplication_scenario()
        
        if success:
            print("\n✅ WEBHOOK ТЕСТ ПРОЙДЕН: Дублирование не обнаружено")
        else:
            print("\n❌ WEBHOOK ТЕСТ ПРОВАЛЕН: Обнаружено дублирование")
        
        return success

def main():
    """Главная функция"""
    tester = WebhookDoubleCreditTester()
    
    try:
        success = tester.run_webhook_test()
        return 0 if success else 1
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())