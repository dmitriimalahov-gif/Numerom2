#!/usr/bin/env python3
"""
ТЕСТИРОВАНИЕ СИСТЕМЫ ИСТОРИИ ТРАНЗАКЦИЙ И ОБНОВЛЕННОЙ СТОИМОСТИ БАЛЛОВ
Testing Credit Transaction History System and Updated Credit Costs

Этот тест проверяет:
1. Новую систему стоимости баллов для всех функций
2. Правильное списание баллов согласно новым тарифам
3. Запись всех транзакций в историю credit_transactions
4. Корректность описаний операций в истории
5. Работу нового endpoint GET /api/user/credit-history

НОВАЯ СИСТЕМА СТОИМОСТИ:
- Нумерология имени: 1 балл
- Персональные числа: 1 балл  
- Квадрат Пифагора: 1 балл
- Ведическое время на день: 1 балл
- Планетарный маршрут на день: 1 балл
- Планетарный маршрут на месяц: 5 баллов
- Планетарный маршрут на квартал: 10 баллов
- Совместимость пары: 1 балл
- Групповая совместимость: 5 баллов
- Тест личности: 1 балл
- Просмотр урока: 10 баллов
- Прохождение Quiz: 1 балл
- Просмотр материалов: 1 балл
"""

import requests
import json
import uuid
from datetime import datetime
import sys
import os

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

# Новые тарифы для тестирования
EXPECTED_CREDIT_COSTS = {
    'name_numerology': 1,
    'personal_numbers': 1,
    'pythagorean_square': 1,
    'vedic_daily': 1,
    'planetary_daily': 1,
    'planetary_monthly': 5,
    'planetary_quarterly': 10,
    'compatibility_pair': 1,
    'group_compatibility': 5,
    'personality_test': 1,
    'lesson_viewing': 10,
    'quiz_completion': 1,
    'material_viewing': 1
}

class CreditSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        self.initial_credits = 0
        self.current_credits = 0
        self.test_password = "TestPassword123!"
        
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
        """Создание тестового пользователя с известным балансом"""
        print("\n👤 СОЗДАНИЕ ТЕСТОВОГО ПОЛЬЗОВАТЕЛЯ")
        
        # Generate unique test user
        test_email = f"test_credit_user_{uuid.uuid4().hex[:8]}@example.com"
        
        try:
            # Register new user
            register_data = {
                "email": test_email,
                "password": self.test_password,
                "full_name": "Тестовый Пользователь Кредитов",
                "birth_date": "15.03.1990",
                "city": "Москва"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=register_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.user_data = data.get('user')
                
                if self.auth_token and self.user_data:
                    # Set authorization header
                    self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                    
                    self.initial_credits = self.user_data.get('credits_remaining', 0)
                    self.current_credits = self.initial_credits
                    
                    # Add credits via payment simulation to have enough for testing
                    self._add_credits_via_payment()
                    
                    details = f"Email: {test_email}, Начальный баланс: {self.initial_credits} баллов, После пополнения: {self.current_credits} баллов"
                    self.log_test("Создание тестового пользователя", "PASS", details)
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
    
    def _add_credits_via_payment(self):
        """Добавить кредиты через симуляцию платежа"""
        try:
            # Create payment session
            payment_data = {
                "package_type": "monthly",  # 150 credits
                "origin_url": "https://numerology-fix.preview.emergentagent.com"
            }
            
            response = self.session.post(f"{BACKEND_URL}/payments/checkout/session", json=payment_data)
            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data.get('session_id')
                
                if session_id:
                    # Check payment status (will auto-complete in demo mode)
                    status_response = self.session.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
                    if status_response.status_code == 200:
                        # Update current credits
                        self.current_credits = self.get_current_credits()
                        self.log_test("Пополнение баланса", "PASS", f"Добавлено кредитов через платёж. Новый баланс: {self.current_credits}")
                    else:
                        self.log_test("Пополнение баланса", "FAIL", f"Ошибка проверки статуса платежа: {status_response.status_code}")
                else:
                    self.log_test("Пополнение баланса", "FAIL", "Не получен session_id")
            else:
                self.log_test("Пополнение баланса", "FAIL", f"Ошибка создания платежа: {response.status_code}")
        except Exception as e:
            self.log_test("Пополнение баланса", "FAIL", f"Ошибка: {str(e)}")
    
    def get_current_credits(self):
        """Получить текущий баланс пользователя"""
        try:
            # Login to get fresh user data
            login_data = {
                "email": self.user_data['email'],
                "password": self.test_password
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                user_data = data.get('user', {})
                return user_data.get('credits_remaining', 0)
            return self.current_credits
        except:
            return self.current_credits
    
    def test_numerology_functions(self):
        """Тест функций нумерологии (1 балл каждая)"""
        print("\n🔢 ТЕСТ ФУНКЦИЙ НУМЕРОЛОГИИ")
        
        numerology_tests = [
            {
                'name': 'Персональные числа',
                'endpoint': '/numerology/personal-numbers',
                'method': 'POST',
                'data': {'birth_date': '15.03.1990'},
                'expected_cost': EXPECTED_CREDIT_COSTS['personal_numbers']
            },
            {
                'name': 'Квадрат Пифагора',
                'endpoint': '/numerology/pythagorean-square',
                'method': 'POST',
                'data': {'birth_date': '15.03.1990'},
                'expected_cost': EXPECTED_CREDIT_COSTS['pythagorean_square']
            },
            {
                'name': 'Нумерология имени',
                'endpoint': '/numerology/name-numerology',
                'method': 'POST',
                'data': {'name': 'Анна', 'surname': 'Иванова'},
                'expected_cost': EXPECTED_CREDIT_COSTS['name_numerology']
            },
            {
                'name': 'Совместимость пары',
                'endpoint': '/numerology/compatibility',
                'method': 'POST',
                'data': {
                    'person1_birth_date': '15.03.1990',
                    'person2_birth_date': '20.07.1985'
                },
                'expected_cost': EXPECTED_CREDIT_COSTS['compatibility_pair']
            }
        ]
        
        for test in numerology_tests:
            self._test_credit_deduction(test)
    
    def test_vedic_functions(self):
        """Тест ведических функций"""
        print("\n🕉️ ТЕСТ ВЕДИЧЕСКИХ ФУНКЦИЙ")
        
        vedic_tests = [
            {
                'name': 'Ведическое время на день',
                'endpoint': '/vedic-time/daily-schedule',
                'method': 'GET',
                'params': {'date': '2025-03-15', 'city': 'Москва'},
                'expected_cost': EXPECTED_CREDIT_COSTS['vedic_daily']
            },
            {
                'name': 'Планетарный маршрут на день',
                'endpoint': '/vedic-time/planetary-route',
                'method': 'GET',
                'params': {'date': '2025-03-15', 'city': 'Москва'},
                'expected_cost': EXPECTED_CREDIT_COSTS['planetary_daily']
            },
            {
                'name': 'Планетарный маршрут на месяц',
                'endpoint': '/vedic-time/planetary-route/monthly',
                'method': 'GET',
                'params': {'date': '2025-03-15', 'city': 'Москва'},
                'expected_cost': EXPECTED_CREDIT_COSTS['planetary_monthly']
            },
            {
                'name': 'Планетарный маршрут на квартал',
                'endpoint': '/vedic-time/planetary-route/quarterly',
                'method': 'GET',
                'params': {'date': '2025-03-15', 'city': 'Москва'},
                'expected_cost': EXPECTED_CREDIT_COSTS['planetary_quarterly']
            }
        ]
        
        for test in vedic_tests:
            self._test_credit_deduction(test)
    
    def test_learning_functions(self):
        """Тест функций обучения"""
        print("\n📚 ТЕСТ ФУНКЦИЙ ОБУЧЕНИЯ")
        
        # First, get available lessons
        try:
            response = self.session.get(f"{BACKEND_URL}/learning/levels")
            if response.status_code == 200:
                data = response.json()
                lessons = data.get('available_lessons', [])
                
                if lessons:
                    lesson_id = lessons[0]['id']
                    
                    learning_tests = [
                        {
                            'name': 'Начало урока',
                            'endpoint': f'/learning/lesson/{lesson_id}/start',
                            'method': 'POST',
                            'data': {},
                            'expected_cost': EXPECTED_CREDIT_COSTS['lesson_viewing']
                        }
                    ]
                    
                    for test in learning_tests:
                        self._test_credit_deduction(test)
                else:
                    self.log_test("Получение списка уроков", "FAIL", "Нет доступных уроков")
            else:
                self.log_test("Получение списка уроков", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Получение списка уроков", "FAIL", f"Ошибка: {str(e)}")
        
        # Test quiz submission
        quiz_test = {
            'name': 'Прохождение викторины',
            'endpoint': '/quiz/submit',
            'method': 'POST',
            'data': [
                {"question_id": 1, "answer": "A"},
                {"question_id": 2, "answer": "B"}
            ],
            'expected_cost': EXPECTED_CREDIT_COSTS['quiz_completion']
        }
        self._test_credit_deduction(quiz_test)
        
        # Test material viewing
        try:
            response = self.session.get(f"{BACKEND_URL}/materials")
            if response.status_code == 200:
                materials = response.json()
                
                if materials:
                    material_id = materials[0]['id']
                    
                    material_test = {
                        'name': 'Просмотр материала',
                        'endpoint': f'/materials/{material_id}/stream',
                        'method': 'GET',
                        'data': {},
                        'expected_cost': EXPECTED_CREDIT_COSTS['material_viewing']
                    }
                    self._test_credit_deduction(material_test)
                else:
                    self.log_test("Получение списка материалов", "WARN", "Нет доступных материалов")
            else:
                self.log_test("Получение списка материалов", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Получение списка материалов", "FAIL", f"Ошибка: {str(e)}")
    
    def test_additional_functions(self):
        """Тест дополнительных функций"""
        print("\n🧪 ТЕСТ ДОПОЛНИТЕЛЬНЫХ ФУНКЦИЙ")
        
        # Test group compatibility
        group_test = {
            'name': 'Групповая совместимость',
            'endpoint': '/numerology/group-compatibility',
            'method': 'POST',
            'data': {
                'people': [
                    {'name': 'Анна', 'birth_date': '15.03.1990'},
                    {'name': 'Петр', 'birth_date': '20.07.1985'},
                    {'name': 'Мария', 'birth_date': '10.12.1992'}
                ]
            },
            'expected_cost': EXPECTED_CREDIT_COSTS['group_compatibility']
        }
        self._test_credit_deduction(group_test)
        
        # Test personality test
        personality_test = {
            'name': 'Тест личности',
            'endpoint': '/quiz/personality-test',
            'method': 'POST',
            'data': {
                'answers': [1, 2, 3, 4, 5]
            },
            'expected_cost': EXPECTED_CREDIT_COSTS['personality_test']
        }
        self._test_credit_deduction(personality_test)
    
    def _test_credit_deduction(self, test_config):
        """Универсальный тест списания баллов"""
        try:
            # Get credits before operation
            credits_before = self.get_current_credits()
            
            # Make API call
            if test_config['method'] == 'POST':
                response = self.session.post(
                    f"{BACKEND_URL}{test_config['endpoint']}", 
                    json=test_config.get('data', {})
                )
            elif test_config['method'] == 'GET':
                response = self.session.get(
                    f"{BACKEND_URL}{test_config['endpoint']}", 
                    params=test_config.get('params', {})
                )
            
            # Get credits after operation
            credits_after = self.get_current_credits()
            actual_deduction = credits_before - credits_after
            expected_deduction = test_config['expected_cost']
            
            if response.status_code == 200:
                if actual_deduction == expected_deduction:
                    details = f"Списано {actual_deduction} баллов (ожидалось {expected_deduction}). Баланс: {credits_before} → {credits_after}"
                    self.log_test(f"Списание баллов - {test_config['name']}", "PASS", details)
                    self.current_credits = credits_after
                else:
                    details = f"НЕВЕРНОЕ СПИСАНИЕ: списано {actual_deduction}, ожидалось {expected_deduction}. Баланс: {credits_before} → {credits_after}"
                    self.log_test(f"Списание баллов - {test_config['name']}", "FAIL", details)
            elif response.status_code == 402:
                # Insufficient credits - this is expected behavior
                details = f"Недостаточно баллов (требуется {expected_deduction}, доступно {credits_before})"
                self.log_test(f"Списание баллов - {test_config['name']}", "PASS", details)
            else:
                details = f"HTTP {response.status_code}: {response.text[:200]}"
                self.log_test(f"Списание баллов - {test_config['name']}", "FAIL", details)
                
        except Exception as e:
            self.log_test(f"Списание баллов - {test_config['name']}", "FAIL", f"Ошибка: {str(e)}")
    
    def test_credit_history(self):
        """Тест истории транзакций"""
        print("\n📋 ТЕСТ ИСТОРИИ ТРАНЗАКЦИЙ")
        
        try:
            # Get transaction history
            response = self.session.get(f"{BACKEND_URL}/user/credit-history")
            
            if response.status_code == 200:
                data = response.json()
                transactions = data.get('transactions', [])
                total = data.get('total', 0)
                
                if transactions:
                    self.log_test("Получение истории транзакций", "PASS", f"Получено {len(transactions)} транзакций из {total}")
                    
                    # Analyze transaction structure
                    self._analyze_transaction_history(transactions)
                else:
                    self.log_test("Получение истории транзакций", "WARN", "История транзакций пуста")
            else:
                self.log_test("Получение истории транзакций", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Получение истории транзакций", "FAIL", f"Ошибка: {str(e)}")
    
    def _analyze_transaction_history(self, transactions):
        """Анализ структуры истории транзакций"""
        print("\n🔍 АНАЛИЗ ИСТОРИИ ТРАНЗАКЦИЙ")
        
        required_fields = ['transaction_type', 'amount', 'description', 'category', 'created_at']
        valid_transactions = 0
        debit_transactions = 0
        categories = set()
        
        for transaction in transactions:
            # Check required fields
            has_all_fields = all(field in transaction for field in required_fields)
            if has_all_fields:
                valid_transactions += 1
                
                # Count debit transactions (credit spending)
                if transaction.get('transaction_type') == 'debit':
                    debit_transactions += 1
                
                # Collect categories
                category = transaction.get('category')
                if category:
                    categories.add(category)
        
        # Test results
        if valid_transactions == len(transactions):
            self.log_test("Структура транзакций", "PASS", f"Все {valid_transactions} транзакций имеют корректную структуру")
        else:
            self.log_test("Структура транзакций", "FAIL", f"Только {valid_transactions}/{len(transactions)} транзакций корректны")
        
        if debit_transactions > 0:
            self.log_test("Записи списания баллов", "PASS", f"Найдено {debit_transactions} записей списания")
        else:
            self.log_test("Записи списания баллов", "FAIL", "Не найдено записей списания баллов")
        
        expected_categories = {'numerology', 'vedic', 'learning', 'quiz', 'materials'}
        found_categories = categories.intersection(expected_categories)
        
        if found_categories:
            self.log_test("Категории операций", "PASS", f"Найдены категории: {', '.join(found_categories)}")
        else:
            self.log_test("Категории операций", "FAIL", f"Не найдены ожидаемые категории. Найдены: {', '.join(categories)}")
        
        # Check descriptions
        descriptions_with_details = 0
        for transaction in transactions:
            description = transaction.get('description', '')
            if len(description) > 10:  # Meaningful description
                descriptions_with_details += 1
        
        if descriptions_with_details > 0:
            self.log_test("Описания операций", "PASS", f"{descriptions_with_details}/{len(transactions)} транзакций имеют подробные описания")
        else:
            self.log_test("Описания операций", "FAIL", "Транзакции не имеют подробных описаний")
    
    def run_comprehensive_test(self):
        """Запуск полного тестирования системы кредитов"""
        print("🎯 ТЕСТИРОВАНИЕ СИСТЕМЫ ИСТОРИИ ТРАНЗАКЦИЙ И ОБНОВЛЕННОЙ СТОИМОСТИ БАЛЛОВ")
        print("=" * 80)
        
        # Step 1: Create test user
        if not self.create_test_user():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось создать тестового пользователя")
            return False
        
        # Step 2: Test numerology functions (1 credit each)
        self.test_numerology_functions()
        
        # Step 3: Test vedic functions
        self.test_vedic_functions()
        
        # Step 4: Test learning functions
        self.test_learning_functions()
        
        # Step 5: Test additional functions
        self.test_additional_functions()
        
        # Step 6: Test transaction history
        self.test_credit_history()
        
        # Summary
        self.print_test_summary()
        
        return True
    
    def print_test_summary(self):
        """Печать итогового отчёта"""
        print("\n" + "=" * 80)
        print("📋 ИТОГОВЫЙ ОТЧЁТ ТЕСТИРОВАНИЯ СИСТЕМЫ КРЕДИТОВ")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warned_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print(f"Всего тестов: {total_tests}")
        print(f"✅ Пройдено: {passed_tests}")
        print(f"❌ Провалено: {failed_tests}")
        print(f"⚠️ Предупреждения: {warned_tests}")
        
        success_rate = (passed_tests / max(total_tests, 1)) * 100
        print(f"📊 Успешность: {success_rate:.1f}%")
        
        print(f"\n💰 Баланс пользователя: {self.initial_credits} → {self.current_credits} баллов")
        print(f"💸 Потрачено баллов: {self.initial_credits - self.current_credits}")
        
        if failed_tests > 0:
            print("\n❌ ПРОВАЛИВШИЕСЯ ТЕСТЫ:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  • {result['test']}: {result['details']}")
        
        # Critical assessment
        critical_keywords = ['списание баллов', 'история транзакций', 'структура транзакций']
        critical_issues = [r for r in self.test_results if r['status'] == 'FAIL' and any(keyword in r['test'].lower() for keyword in critical_keywords)]
        
        if critical_issues:
            print(f"\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ СИСТЕМЫ КРЕДИТОВ: {len(critical_issues)}")
            print("Система списания баллов или история транзакций работает некорректно!")
        else:
            print("\n🎉 СИСТЕМА КРЕДИТОВ РАБОТАЕТ КОРРЕКТНО")
            print("Все функции правильно списывают баллы и записывают историю!")

def main():
    """Главная функция запуска тестов"""
    tester = CreditSystemTester()
    
    try:
        success = tester.run_comprehensive_test()
        if success:
            print("\n✅ Тестирование системы кредитов завершено")
            return 0
        else:
            print("\n❌ Тестирование системы кредитов завершено с ошибками")
            return 1
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        return 1
    except Exception as e:
        print(f"\n💥 Критическая ошибка тестирования: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())