#!/usr/bin/env python3
"""
КРИТИЧЕСКАЯ ДИАГНОСТИКА: Проблема двойного начисления баллов
CRITICAL DIAGNOSIS: Double Credit Allocation Issue

Детальная диагностика проблемы двойного начисления баллов:
- Баллы всё еще начисляются в два раза больше чем указано в пакетах
- Найти ВСЕ места в коде где происходит начисление баллов и исправить дублирование

ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:
- Покупка 'one_time' должна давать РОВНО 10 баллов
- Покупка 'monthly' должна давать РОВНО 150 баллов  
- Покупка 'annual' должна давать РОВНО 500 баллов
- Покупка 'master_consultation' должна давать РОВНО 10000 баллов
"""

import requests
import json
import uuid
from datetime import datetime
import sys
import time

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

class DoubleCreditTester:
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
        
    def create_test_user(self):
        """Создать тестового пользователя с 0 баллов"""
        print("\n👤 СОЗДАНИЕ ТЕСТОВОГО ПОЛЬЗОВАТЕЛЯ")
        
        # Generate unique test user
        test_id = str(uuid.uuid4())[:8]
        test_email = f"test_credits_{test_id}@example.com"
        test_password = "TestPassword123!"
        
        user_data = {
            "email": test_email,
            "password": test_password,
            "full_name": f"Test User {test_id}",
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
                    # Set authorization header
                    self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                    
                    initial_credits = self.user_data.get('credits_remaining', 0)
                    user_id = self.user_data.get('id')
                    
                    self.log_test("Создание тестового пользователя", "PASS", 
                                f"Email: {test_email}, ID: {user_id}, Начальные баллы: {initial_credits}")
                    
                    self.test_email = test_email
                    self.test_password = test_password
                    return True
                else:
                    self.log_test("Создание тестового пользователя", "FAIL", "Отсутствует токен или данные")
                    return False
            else:
                self.log_test("Создание тестового пользователя", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Создание тестового пользователя", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def get_current_credits(self):
        """Получить текущий баланс баллов пользователя"""
        try:
            # Re-login to get fresh user data
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
    
    def test_payment_package(self, package_type, expected_credits):
        """Тестировать покупку конкретного пакета"""
        print(f"\n💳 ТЕСТ ПАКЕТА: {package_type.upper()}")
        
        # Step 1: Record initial balance
        initial_credits = self.get_current_credits()
        if initial_credits is None:
            self.log_test(f"Начальный баланс - {package_type}", "FAIL", "Не удалось получить баланс")
            return False
            
        print(f"📊 Начальный баланс: {initial_credits} баллов")
        
        # Step 2: Create checkout session
        try:
            payment_data = {
                "package_type": package_type,
                "origin_url": "https://numerology-fix.preview.emergentagent.com"
            }
            
            response = self.session.post(f"{BACKEND_URL}/payments/checkout/session", json=payment_data)
            
            if response.status_code == 200:
                checkout_data = response.json()
                session_id = checkout_data.get('session_id')
                
                if session_id:
                    self.log_test(f"Создание сессии - {package_type}", "PASS", f"Session ID: {session_id}")
                    
                    # Step 3: Check payment status (this should trigger credit allocation in demo mode)
                    time.sleep(1)  # Small delay to ensure processing
                    
                    status_response = self.session.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        payment_status = status_data.get('payment_status')
                        
                        self.log_test(f"Статус платежа - {package_type}", "PASS", f"Статус: {payment_status}")
                        
                        # Step 4: Check final balance
                        time.sleep(1)  # Allow time for credit processing
                        final_credits = self.get_current_credits()
                        
                        if final_credits is not None:
                            credits_added = final_credits - initial_credits
                            
                            print(f"📊 Финальный баланс: {final_credits} баллов")
                            print(f"📊 Добавлено баллов: {credits_added}")
                            print(f"📊 Ожидалось баллов: {expected_credits}")
                            
                            if credits_added == expected_credits:
                                self.log_test(f"Начисление баллов - {package_type}", "PASS", 
                                            f"Корректно начислено {credits_added} баллов (ожидалось {expected_credits})")
                                return True
                            else:
                                self.log_test(f"Начисление баллов - {package_type}", "FAIL", 
                                            f"ДВОЙНОЕ НАЧИСЛЕНИЕ! Начислено {credits_added} баллов, ожидалось {expected_credits}")
                                
                                # Detailed analysis
                                if credits_added == expected_credits * 2:
                                    print("🚨 ПОДТВЕРЖДЕНО: Баллы начисляются в ДВОЙНОМ размере!")
                                elif credits_added > expected_credits:
                                    print(f"🚨 ПРОБЛЕМА: Баллы начисляются больше ожидаемого (коэффициент: {credits_added/expected_credits:.2f})")
                                else:
                                    print(f"⚠️ НЕДОНАЧИСЛЕНИЕ: Баллы начисляются меньше ожидаемого")
                                
                                return False
                        else:
                            self.log_test(f"Проверка баланса - {package_type}", "FAIL", "Не удалось получить финальный баланс")
                            return False
                    else:
                        self.log_test(f"Статус платежа - {package_type}", "FAIL", f"HTTP {status_response.status_code}")
                        return False
                else:
                    self.log_test(f"Создание сессии - {package_type}", "FAIL", "Отсутствует session_id")
                    return False
            else:
                self.log_test(f"Создание сессии - {package_type}", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test(f"Тест пакета - {package_type}", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def test_all_payment_packages(self):
        """Тестировать все пакеты платежей"""
        print("\n🎯 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ВСЕХ ПАКЕТОВ")
        
        # Expected credits for each package
        packages = {
            'one_time': 10,
            'monthly': 150,
            'annual': 500,
            'master_consultation': 10000
        }
        
        results = {}
        
        for package_type, expected_credits in packages.items():
            print(f"\n{'='*60}")
            print(f"ТЕСТИРОВАНИЕ ПАКЕТА: {package_type.upper()}")
            print(f"ОЖИДАЕМЫЕ БАЛЛЫ: {expected_credits}")
            print(f"{'='*60}")
            
            success = self.test_payment_package(package_type, expected_credits)
            results[package_type] = success
            
            # Small delay between tests
            time.sleep(2)
        
        return results
    
    def analyze_credit_allocation_code(self):
        """Анализ мест в коде где происходит начисление баллов"""
        print("\n🔍 АНАЛИЗ КОДА: Поиск мест начисления баллов")
        
        # This is a conceptual analysis based on the server.py code we saw
        potential_duplication_points = [
            {
                "location": "server.py:214 (Demo mode)",
                "code": "await db.users.update_one({'id': user_id}, {'$inc': {'credits_remaining': credits_to_add}})",
                "description": "Начисление баллов в demo режиме при проверке статуса платежа"
            },
            {
                "location": "server.py:254 (Real Stripe mode)", 
                "code": "await db.users.update_one({'id': user_id}, {'$inc': {'credits_remaining': credits_to_add}})",
                "description": "Начисление баллов в реальном Stripe режиме при проверке статуса"
            },
            {
                "location": "Webhook endpoint",
                "code": "POST /api/webhook/stripe",
                "description": "Возможное дублирование через webhook при успешном платеже"
            }
        ]
        
        print("🚨 ПОТЕНЦИАЛЬНЫЕ МЕСТА ДУБЛИРОВАНИЯ:")
        for i, point in enumerate(potential_duplication_points, 1):
            print(f"{i}. {point['location']}")
            print(f"   Код: {point['code']}")
            print(f"   Описание: {point['description']}")
            print()
        
        print("💡 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
        print("1. Добавить проверку на уже начисленные баллы для данной транзакции")
        print("2. Использовать флаг 'credits_processed' в PaymentTransaction")
        print("3. Убедиться что webhook не дублирует начисление из status check")
        print("4. Добавить логирование всех операций начисления баллов")
    
    def run_comprehensive_diagnosis(self):
        """Запуск полной диагностики проблемы двойного начисления"""
        print("🚨 КРИТИЧЕСКАЯ ДИАГНОСТИКА: Проблема двойного начисления баллов")
        print("=" * 80)
        
        # Step 1: Create test user
        if not self.create_test_user():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось создать тестового пользователя")
            return False
        
        # Step 2: Test all payment packages
        results = self.test_all_payment_packages()
        
        # Step 3: Analyze code for duplication points
        self.analyze_credit_allocation_code()
        
        # Step 4: Summary and recommendations
        self.print_diagnosis_summary(results)
        
        return True
    
    def print_diagnosis_summary(self, results):
        """Печать итогового отчёта диагностики"""
        print("\n" + "=" * 80)
        print("📋 ИТОГОВЫЙ ОТЧЁТ ДИАГНОСТИКИ ДВОЙНОГО НАЧИСЛЕНИЯ")
        print("=" * 80)
        
        total_packages = len(results)
        failed_packages = len([r for r in results.values() if not r])
        
        print(f"Всего протестировано пакетов: {total_packages}")
        print(f"❌ Пакетов с проблемами: {failed_packages}")
        print(f"✅ Пакетов без проблем: {total_packages - failed_packages}")
        
        if failed_packages > 0:
            print(f"\n🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА ПОДТВЕРЖДЕНА!")
            print(f"Обнаружено двойное начисление баллов в {failed_packages} из {total_packages} пакетов")
            
            print("\n❌ ПРОБЛЕМНЫЕ ПАКЕТЫ:")
            for package, success in results.items():
                if not success:
                    print(f"  • {package}: ДВОЙНОЕ НАЧИСЛЕНИЕ")
            
            print("\n🔧 НЕОБХОДИМЫЕ ИСПРАВЛЕНИЯ:")
            print("1. Добавить проверку флага 'credits_processed' в PaymentTransaction")
            print("2. Предотвратить дублирование между status check и webhook")
            print("3. Добавить уникальный constraint на начисление баллов по session_id")
            print("4. Логировать все операции начисления для отладки")
            
        else:
            print(f"\n✅ ПРОБЛЕМА НЕ ПОДТВЕРЖДЕНА")
            print("Все пакеты начисляют корректное количество баллов")
        
        # Print detailed test results
        print(f"\n📊 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ ТЕСТОВ:")
        for result in self.test_results:
            status_icon = "✅" if result['status'] == "PASS" else "❌" if result['status'] == "FAIL" else "⚠️"
            print(f"{status_icon} {result['test']}: {result['details']}")

def main():
    """Главная функция запуска диагностики"""
    tester = DoubleCreditTester()
    
    try:
        success = tester.run_comprehensive_diagnosis()
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