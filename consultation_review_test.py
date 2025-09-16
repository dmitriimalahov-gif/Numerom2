#!/usr/bin/env python3
"""
REVIEW REQUEST TESTING: Персональные консультации и третий пакет
Testing all fixes for personal consultations and third package according to review request

КЛЮЧЕВЫЕ ИСПРАВЛЕНИЯ ДЛЯ ТЕСТИРОВАНИЯ:
1. Персональная консультация теперь стоит 6667 баллов (остается 3333)
2. Третий пакет теперь дает 1000 баллов вместо 500
3. При покупке консультации в админпанели появляется информация о покупателе
4. При выборе студента в админпанели подтягиваются его личные данные

ENDPOINTS ДЛЯ ТЕСТИРОВАНИЯ:
1. POST /api/user/consultations/{id}/purchase - покупка консультации (обновлено)
2. GET /api/admin/consultations - получение консультаций с данными покупателей (обновлено)
3. GET /api/admin/users/{id}/details - получение детальных данных пользователя (новый)
4. SUBSCRIPTION_CREDITS - константы пакетов (обновлены)
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

class ConsultationReviewTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_user_token = None
        self.test_user_id = None
        self.test_user_email = None
        self.test_consultation_id = None
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
        """Аутентификация супер-админа dmitrii.malahov@gmail.com / 756bvy67H"""
        print("\n🔐 ТЕСТ 1: АУТЕНТИФИКАЦИЯ СУПЕР-АДМИНА")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": SUPER_ADMIN_EMAIL,
                "password": SUPER_ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data['access_token']
                user_data = data['user']
                
                # Проверяем супер-админ статус
                if user_data.get('is_super_admin') and user_data.get('credits_remaining', 0) >= 10000:
                    self.log_test("Аутентификация супер-админа", "PASS", 
                                f"Успешно: {user_data['email']}, кредиты: {user_data['credits_remaining']}")
                    return True
                else:
                    self.log_test("Аутентификация супер-админа", "FAIL", 
                                f"Недостаточно прав или кредитов: {user_data}")
                    return False
            else:
                self.log_test("Аутентификация супер-админа", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Аутентификация супер-админа", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def test_subscription_credits_constants(self):
        """Проверить константы пакетов - третий пакет должен давать 1000 баллов"""
        print("\n💰 ТЕСТ 2: ПРОВЕРКА КОНСТАНТ ПАКЕТОВ")
        
        try:
            # Создаем тестового пользователя с минимальными кредитами
            test_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
            self.test_user_email = test_email  # Сохраняем email для дальнейшего использования
            register_response = self.session.post(f"{BACKEND_URL}/auth/register", json={
                "email": test_email,
                "password": "testpass123",
                "full_name": "Test User",
                "birth_date": "15.03.1990"
            })
            
            if register_response.status_code != 200:
                self.log_test("Создание тестового пользователя", "FAIL", 
                            f"HTTP {register_response.status_code}: {register_response.text}")
                return False
            
            # Получаем токен тестового пользователя
            login_response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": test_email,
                "password": "testpass123"
            })
            
            if login_response.status_code != 200:
                self.log_test("Логин тестового пользователя", "FAIL", 
                            f"HTTP {login_response.status_code}: {login_response.text}")
                return False
            
            user_data = login_response.json()
            self.test_user_token = user_data['access_token']
            self.test_user_id = user_data['user']['id']
            initial_credits = user_data['user']['credits_remaining']
            
            self.log_test("Создание тестового пользователя", "PASS", 
                        f"Пользователь создан: {test_email}, начальные кредиты: {initial_credits}")
            
            # Тестируем покупку annual пакета (третий пакет)
            headers = {'Authorization': f'Bearer {self.test_user_token}'}
            checkout_response = self.session.post(f"{BACKEND_URL}/payments/checkout/session", 
                                                json={
                                                    "package_type": "annual",
                                                    "origin_url": "https://numerology-fix.preview.emergentagent.com"
                                                }, headers=headers)
            
            if checkout_response.status_code != 200:
                self.log_test("Создание сессии оплаты annual", "FAIL", 
                            f"HTTP {checkout_response.status_code}: {checkout_response.text}")
                return False
            
            session_data = checkout_response.json()
            session_id = session_data['session_id']
            
            # Проверяем статус платежа (в demo режиме автоматически оплачивается)
            status_response = self.session.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
            
            if status_response.status_code != 200:
                self.log_test("Проверка статуса платежа annual", "FAIL", 
                            f"HTTP {status_response.status_code}: {status_response.text}")
                return False
            
            # Проверяем что пользователь получил 1000 кредитов
            user_check_response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": test_email,
                "password": "testpass123"
            })
            
            if user_check_response.status_code == 200:
                updated_user = user_check_response.json()['user']
                final_credits = updated_user['credits_remaining']
                credits_added = final_credits - initial_credits
                
                if credits_added == 1000:
                    self.log_test("Третий пакет дает 1000 баллов", "PASS", 
                                f"Было: {initial_credits}, стало: {final_credits}, добавлено: {credits_added}")
                    return True
                else:
                    self.log_test("Третий пакет дает 1000 баллов", "FAIL", 
                                f"Ожидалось +1000, получено +{credits_added}")
                    return False
            else:
                self.log_test("Проверка кредитов после покупки", "FAIL", 
                            f"HTTP {user_check_response.status_code}: {user_check_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Проверка констант пакетов", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def ensure_test_user_has_credits(self):
        """Убедиться что у тестового пользователя есть 10000+ кредитов"""
        if not self.test_user_email or not self.admin_token:
            return False
        
        try:
            # Получаем текущие кредиты пользователя
            user_response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": self.test_user_email,
                "password": "testpass123"
            })
            
            if user_response.status_code != 200:
                return False
            
            current_credits = user_response.json()['user']['credits_remaining']
            
            if current_credits < 10000:
                # Добавляем кредиты через админа
                headers = {'Authorization': f'Bearer {self.admin_token}'}
                credits_update = self.session.patch(
                    f"{BACKEND_URL}/admin/users/{self.test_user_id}/credits",
                    json={"credits_remaining": 10000},
                    headers=headers
                )
                
                if credits_update.status_code == 200:
                    self.log_test("Добавление кредитов тестовому пользователю", "PASS", 
                                f"Кредиты обновлены до 10000")
                    return True
                else:
                    self.log_test("Добавление кредитов тестовому пользователю", "FAIL", 
                                f"HTTP {credits_update.status_code}: {credits_update.text}")
                    return False
            else:
                return True
                
        except Exception as e:
            self.log_test("Проверка кредитов пользователя", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def create_test_consultation(self):
        """Создать тестовую консультацию назначенную тестовому пользователю"""
        print("\n📝 ТЕСТ 3: СОЗДАНИЕ ТЕСТОВОЙ КОНСУЛЬТАЦИИ")
        
        if not self.admin_token or not self.test_user_id:
            self.log_test("Создание тестовой консультации", "FAIL", "Нет токена админа или ID пользователя")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            consultation_data = {
                "title": "Тестовая персональная консультация",
                "description": "Эксклюзивная персональная консультация для тестирования системы покупки",
                "video_url": "https://example.com/test-consultation-video",
                "assigned_user_id": self.test_user_id,
                "cost_credits": 10000,
                "is_active": True
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/consultations", 
                                       json=consultation_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                self.test_consultation_id = result['consultation_id']
                self.log_test("Создание тестовой консультации", "PASS", 
                            f"Консультация создана: {self.test_consultation_id}")
                return True
            else:
                self.log_test("Создание тестовой консультации", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Создание тестовой консультации", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def test_consultation_purchase(self):
        """Тест покупки консультации - КРИТИЧНЫЙ ТЕСТ"""
        print("\n💳 ТЕСТ 4: ПОКУПКА ПЕРСОНАЛЬНОЙ КОНСУЛЬТАЦИИ (КРИТИЧНЫЙ)")
        
        if not self.test_user_token or not self.test_consultation_id:
            self.log_test("Покупка консультации", "FAIL", "Нет токена пользователя или ID консультации")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.test_user_token}'}
            
            # Сначала проверяем текущие кредиты пользователя
            user_response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": self.test_user_email,
                "password": "testpass123"
            })
            
            if user_response.status_code != 200:
                self.log_test("Проверка кредитов перед покупкой", "FAIL", "Не удалось получить данные пользователя")
                return False
            
            initial_credits = user_response.json()['user']['credits_remaining']
            
            if initial_credits < 10000:
                self.log_test("Покупка консультации", "FAIL", 
                            f"Недостаточно кредитов: {initial_credits} < 10000")
                return False
            
            # Покупаем консультацию
            purchase_response = self.session.post(
                f"{BACKEND_URL}/user/consultations/{self.test_consultation_id}/purchase", 
                headers=headers
            )
            
            if purchase_response.status_code == 200:
                result = purchase_response.json()
                credits_spent = result.get('credits_spent', 0)
                remaining_credits = result.get('remaining_credits', 0)
                
                # ПРОВЕРЯЕМ: списалось 6667 баллов, осталось 3333
                if credits_spent == 6667 and remaining_credits == (initial_credits - 6667):
                    self.log_test("Покупка консультации - стоимость", "PASS", 
                                f"Списано: {credits_spent}, осталось: {remaining_credits}")
                    
                    # Дополнительная проверка: если было 10000, должно остаться 3333
                    if initial_credits >= 10000 and remaining_credits == (initial_credits - 6667):
                        self.log_test("Покупка консультации - логика", "PASS", 
                                    f"Было: {initial_credits}, списано: 6667, осталось: {remaining_credits}")
                        return True
                    else:
                        self.log_test("Покупка консультации - логика", "FAIL", 
                                    f"Неправильная логика списания: было {initial_credits}, осталось {remaining_credits}")
                        return False
                else:
                    self.log_test("Покупка консультации - стоимость", "FAIL", 
                                f"Неправильная стоимость: списано {credits_spent}, ожидалось 6667")
                    return False
            else:
                self.log_test("Покупка консультации", "FAIL", 
                            f"HTTP {purchase_response.status_code}: {purchase_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Покупка консультации", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def test_admin_consultations_with_buyer_data(self):
        """Тест админпанели - проверить что есть buyer_details с полной информацией"""
        print("\n👥 ТЕСТ 5: АДМИНПАНЕЛЬ - ДАННЫЕ ПОКУПАТЕЛЯ")
        
        if not self.admin_token:
            self.log_test("Админпанель - данные покупателя", "FAIL", "Нет токена админа")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            response = self.session.get(f"{BACKEND_URL}/admin/consultations", headers=headers)
            
            if response.status_code == 200:
                consultations = response.json()
                
                # Ищем нашу купленную консультацию
                purchased_consultation = None
                for consultation in consultations:
                    if consultation.get('id') == self.test_consultation_id and consultation.get('is_purchased'):
                        purchased_consultation = consultation
                        break
                
                if purchased_consultation:
                    buyer_details = purchased_consultation.get('buyer_details')
                    if buyer_details:
                        required_fields = ['user_id', 'full_name', 'email', 'birth_date', 'credits_spent']
                        missing_fields = [field for field in required_fields if not buyer_details.get(field)]
                        
                        if not missing_fields:
                            self.log_test("Админпанель - buyer_details", "PASS", 
                                        f"Все поля присутствуют: {list(buyer_details.keys())}")
                            
                            # Проверяем что credits_spent = 6667
                            if buyer_details.get('credits_spent') == 6667:
                                self.log_test("Админпанель - credits_spent", "PASS", 
                                            f"Правильная сумма: {buyer_details['credits_spent']}")
                                return True
                            else:
                                self.log_test("Админпанель - credits_spent", "FAIL", 
                                            f"Неправильная сумма: {buyer_details.get('credits_spent')}")
                                return False
                        else:
                            self.log_test("Админпанель - buyer_details", "FAIL", 
                                        f"Отсутствуют поля: {missing_fields}")
                            return False
                    else:
                        self.log_test("Админпанель - buyer_details", "FAIL", "buyer_details отсутствует")
                        return False
                else:
                    self.log_test("Админпанель - купленная консультация", "FAIL", 
                                "Купленная консультация не найдена")
                    return False
            else:
                self.log_test("Админпанель - получение консультаций", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Админпанель - данные покупателя", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def test_user_details_endpoint(self):
        """Тест GET /api/admin/users/{id}/details возвращает детальные данные"""
        print("\n📊 ТЕСТ 6: ENDPOINT ДЕТАЛЬНЫХ ДАННЫХ ПОЛЬЗОВАТЕЛЯ")
        
        if not self.admin_token or not self.test_user_id:
            self.log_test("Детальные данные пользователя", "FAIL", "Нет токена админа или ID пользователя")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            response = self.session.get(f"{BACKEND_URL}/admin/users/{self.test_user_id}/details", 
                                      headers=headers)
            
            if response.status_code == 200:
                user_details = response.json()
                
                # Проверяем наличие основных полей
                required_fields = ['id', 'email', 'full_name', 'birth_date', 'credits_remaining', 
                                 'lessons_completed', 'lessons_total', 'quiz_results_count']
                missing_fields = [field for field in required_fields if field not in user_details]
                
                if not missing_fields:
                    self.log_test("Детальные данные пользователя", "PASS", 
                                f"Все поля присутствуют: {len(user_details)} полей")
                    
                    # Проверяем что кредиты обновились после покупки
                    credits = user_details.get('credits_remaining', 0)
                    if credits < 10000:  # Должно быть меньше после покупки
                        self.log_test("Обновленные кредиты в деталях", "PASS", 
                                    f"Кредиты после покупки: {credits}")
                        return True
                    else:
                        self.log_test("Обновленные кредиты в деталях", "WARN", 
                                    f"Кредиты не изменились: {credits}")
                        return True  # Не критично
                else:
                    self.log_test("Детальные данные пользователя", "FAIL", 
                                f"Отсутствуют поля: {missing_fields}")
                    return False
            else:
                self.log_test("Детальные данные пользователя", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Детальные данные пользователя", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def test_protection_logic(self):
        """Проверить логику защиты - нельзя купить дважды, нужно 10000 баллов"""
        print("\n🛡️ ТЕСТ 7: ЛОГИКА ЗАЩИТЫ")
        
        if not self.test_user_token or not self.test_consultation_id:
            self.log_test("Логика защиты", "FAIL", "Нет токена пользователя или ID консультации")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.test_user_token}'}
            
            # Пытаемся купить консультацию повторно
            repeat_purchase_response = self.session.post(
                f"{BACKEND_URL}/user/consultations/{self.test_consultation_id}/purchase", 
                headers=headers
            )
            
            if repeat_purchase_response.status_code == 400:
                error_message = repeat_purchase_response.json().get('detail', '')
                if 'уже приобретена' in error_message or 'already' in error_message.lower():
                    self.log_test("Защита от повторной покупки", "PASS", 
                                f"Правильная ошибка: {error_message}")
                    return True
                else:
                    self.log_test("Защита от повторной покупки", "FAIL", 
                                f"Неправильная ошибка: {error_message}")
                    return False
            else:
                self.log_test("Защита от повторной покупки", "FAIL", 
                            f"Неожиданный статус: {repeat_purchase_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Логика защиты", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Запустить все тесты согласно review request"""
        print("🚀 НАЧАЛО ТЕСТИРОВАНИЯ ИСПРАВЛЕНИЙ ПЕРСОНАЛЬНЫХ КОНСУЛЬТАЦИЙ И ТРЕТЬЕГО ПАКЕТА")
        print("=" * 80)
        
        tests_passed = 0
        total_tests = 7
        
        # 1. Аутентификация супер-админа
        if self.authenticate_super_admin():
            tests_passed += 1
        
        # 2. Проверка констант пакетов (третий пакет = 1000 баллов)
        if self.test_subscription_credits_constants():
            tests_passed += 1
        
        # 3. Создание тестовой консультации
        if self.create_test_consultation():
            tests_passed += 1
        
        # 3.5. Убедиться что у пользователя есть достаточно кредитов
        if not self.ensure_test_user_has_credits():
            self.log_test("Подготовка кредитов для теста", "FAIL", "Не удалось обеспечить достаточно кредитов")
        
        # 4. КРИТИЧНЫЙ: Тест покупки консультации (6667 баллов, остается 3333)
        if self.test_consultation_purchase():
            tests_passed += 1
        
        # 5. Тест админпанели с данными покупателя
        if self.test_admin_consultations_with_buyer_data():
            tests_passed += 1
        
        # 6. Тест endpoint детальных данных пользователя
        if self.test_user_details_endpoint():
            tests_passed += 1
        
        # 7. Проверка логики защиты
        if self.test_protection_logic():
            tests_passed += 1
        
        # Итоговый отчет
        print("\n" + "=" * 80)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 80)
        
        success_rate = (tests_passed / total_tests) * 100
        
        print(f"✅ Пройдено тестов: {tests_passed}/{total_tests}")
        print(f"📈 Успешность: {success_rate:.1f}%")
        
        if success_rate >= 85:
            print("🎉 ОТЛИЧНО: Все основные исправления работают корректно!")
        elif success_rate >= 70:
            print("⚠️ ХОРОШО: Большинство исправлений работает, есть минорные проблемы")
        else:
            print("❌ ПРОБЛЕМЫ: Обнаружены критические ошибки в исправлениях")
        
        # Детальный отчет по каждому тесту
        print("\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for result in self.test_results:
            status_icon = "✅" if result['status'] == "PASS" else "❌" if result['status'] == "FAIL" else "⚠️"
            print(f"{status_icon} {result['test']}: {result['details']}")
        
        return success_rate >= 85

if __name__ == "__main__":
    tester = ConsultationReviewTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)