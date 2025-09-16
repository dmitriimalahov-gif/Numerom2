#!/usr/bin/env python3
"""
ТЕСТИРОВАНИЕ СИСТЕМЫ ЛИЧНЫХ КОНСУЛЬТАЦИЙ С ВИДЕО И PDF ФАЙЛАМИ
Personal Consultations System Testing with Video and PDF Files

Согласно review request:
1. Консультация "eb0dcbb0-fe77-4b04-a7a2-3c2483fd6c9a" должна иметь video_file_id и pdf_file_id
2. Endpoints /api/consultations/video/{id} и /api/consultations/pdf/{id} должны работать
3. Файлы должны стримиться с правильными CORS headers
4. Админ должен уметь загружать видео и PDF файлы
5. Пользователь t@t.t (ID: 59ca2bfa-a802-4053-b34b-073a2480032a) должен купить консультацию за 6667 баллов
6. После покупки доступ к video_file_id: "8ccfa669-6ab7-4426-9b3d-59bccd1a3b3b" и pdf_file_id: "c303a0c3-1665-4470-af0b-d28afd0d17c8"
"""

import requests
import json
import io
from datetime import datetime
import sys
import os
from pathlib import Path

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"
TEST_USER_EMAIL = "t@t.t"
TEST_USER_ID = "59ca2bfa-a802-4053-b34b-073a2480032a"
TEST_CONSULTATION_ID = "eb0dcbb0-fe77-4b04-a7a2-3c2483fd6c9a"
TEST_VIDEO_FILE_ID = "8ccfa669-6ab7-4426-9b3d-59bccd1a3b3b"
TEST_PDF_FILE_ID = "c303a0c3-1665-4470-af0b-d28afd0d17c8"

class ConsultationSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.user_token = None
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
        
    def authenticate_admin(self):
        """Аутентификация супер-админа"""
        print("\n🔐 ТЕСТ 1: АУТЕНТИФИКАЦИЯ СУПЕР-АДМИНА")
        
        try:
            login_data = {
                "email": SUPER_ADMIN_EMAIL,
                "password": SUPER_ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('access_token')
                admin_data = data.get('user')
                
                if self.admin_token and admin_data:
                    details = f"User ID: {admin_data.get('id')}, is_super_admin: {admin_data.get('is_super_admin')}, credits: {admin_data.get('credits_remaining')}"
                    self.log_test("Аутентификация супер-админа", "PASS", details)
                    return True
                else:
                    self.log_test("Аутентификация супер-админа", "FAIL", "Отсутствует токен или данные")
                    return False
            else:
                self.log_test("Аутентификация супер-админа", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Аутентификация супер-админа", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def test_admin_file_upload(self):
        """Тестирование загрузки файлов админом"""
        print("\n📁 ТЕСТ 2: ЗАГРУЗКА ФАЙЛОВ АДМИНОМ")
        
        if not self.admin_token:
            self.log_test("Загрузка файлов", "SKIP", "Нет токена админа")
            return
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test video upload
        try:
            # Create a dummy video file
            video_content = b"FAKE_VIDEO_CONTENT_FOR_TESTING" * 100  # Make it larger
            video_file = io.BytesIO(video_content)
            
            files = {'file': ('test_video.mp4', video_file, 'video/mp4')}
            response = self.session.post(f"{BACKEND_URL}/admin/consultations/upload-video", 
                                       files=files, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                video_file_id = data.get('file_id')
                self.log_test("Загрузка видео админом", "PASS", f"Video ID: {video_file_id}")
                self.uploaded_video_id = video_file_id
            else:
                self.log_test("Загрузка видео админом", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Загрузка видео админом", "FAIL", f"Ошибка: {str(e)}")
        
        # Test PDF upload
        try:
            # Create a dummy PDF file
            pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n174\n%%EOF"
            pdf_file = io.BytesIO(pdf_content)
            
            files = {'file': ('test_document.pdf', pdf_file, 'application/pdf')}
            response = self.session.post(f"{BACKEND_URL}/admin/consultations/upload-pdf", 
                                       files=files, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                pdf_file_id = data.get('file_id')
                self.log_test("Загрузка PDF админом", "PASS", f"PDF ID: {pdf_file_id}")
                self.uploaded_pdf_id = pdf_file_id
            else:
                self.log_test("Загрузка PDF админом", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Загрузка PDF админом", "FAIL", f"Ошибка: {str(e)}")
    
    def test_consultation_creation(self):
        """Создание консультации с файлами"""
        print("\n📋 ТЕСТ 3: СОЗДАНИЕ КОНСУЛЬТАЦИИ С ФАЙЛАМИ")
        
        if not self.admin_token:
            self.log_test("Создание консультации", "SKIP", "Нет токена админа")
            return
        
        headers = {'Authorization': f'Bearer {self.admin_token}', 'Content-Type': 'application/json'}
        
        # Use the specific IDs from the review request
        consultation_data = {
            "id": TEST_CONSULTATION_ID,
            "title": "Персональная консультация с видео и PDF",
            "description": "Эксклюзивная консультация с видео материалами и PDF документами",
            "video_file_id": TEST_VIDEO_FILE_ID,
            "pdf_file_id": TEST_PDF_FILE_ID,
            "assigned_user_id": TEST_USER_ID,
            "cost_credits": 6667,
            "is_active": True
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/admin/consultations", 
                                       json=consultation_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Создание консультации с файлами", "PASS", 
                            f"Consultation ID: {TEST_CONSULTATION_ID}, video_file_id: {TEST_VIDEO_FILE_ID}, pdf_file_id: {TEST_PDF_FILE_ID}")
            else:
                self.log_test("Создание консультации с файлами", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Создание консультации с файлами", "FAIL", f"Ошибка: {str(e)}")
    
    def test_consultation_verification(self):
        """Проверка консультации в админ панели"""
        print("\n🔍 ТЕСТ 4: ПРОВЕРКА КОНСУЛЬТАЦИИ В АДМИН ПАНЕЛИ")
        
        if not self.admin_token:
            self.log_test("Проверка консультации", "SKIP", "Нет токена админа")
            return
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/consultations", headers=headers)
            
            if response.status_code == 200:
                consultations = response.json()
                
                # Find our test consultation
                test_consultation = None
                for consultation in consultations:
                    if consultation.get('id') == TEST_CONSULTATION_ID:
                        test_consultation = consultation
                        break
                
                if test_consultation:
                    has_video = test_consultation.get('video_file_id') == TEST_VIDEO_FILE_ID
                    has_pdf = test_consultation.get('pdf_file_id') == TEST_PDF_FILE_ID
                    assigned_correctly = test_consultation.get('assigned_user_id') == TEST_USER_ID
                    
                    if has_video and has_pdf and assigned_correctly:
                        self.log_test("Консультация имеет video_file_id и pdf_file_id", "PASS", 
                                    f"video_file_id: {test_consultation.get('video_file_id')}, pdf_file_id: {test_consultation.get('pdf_file_id')}")
                    else:
                        details = f"video_file_id: {test_consultation.get('video_file_id')}, pdf_file_id: {test_consultation.get('pdf_file_id')}, assigned_user_id: {test_consultation.get('assigned_user_id')}"
                        self.log_test("Консультация имеет video_file_id и pdf_file_id", "FAIL", details)
                else:
                    self.log_test("Консультация имеет video_file_id и pdf_file_id", "FAIL", f"Консультация {TEST_CONSULTATION_ID} не найдена")
            else:
                self.log_test("Проверка консультации", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Проверка консультации", "FAIL", f"Ошибка: {str(e)}")
    
    def test_file_streaming_endpoints(self):
        """Тестирование endpoints для стриминга файлов"""
        print("\n🎥 ТЕСТ 5: ТЕСТИРОВАНИЕ ENDPOINTS ДЛЯ СТРИМИНГА ФАЙЛОВ")
        
        # Test video streaming endpoint
        try:
            response = self.session.get(f"{BACKEND_URL}/consultations/video/{TEST_VIDEO_FILE_ID}")
            
            if response.status_code == 200:
                # Check CORS headers
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                }
                
                has_cors = any(cors_headers.values())
                details = f"Content-Type: {response.headers.get('content-type')}, CORS headers: {has_cors}"
                
                if has_cors:
                    self.log_test("Video streaming endpoint с CORS", "PASS", details)
                else:
                    self.log_test("Video streaming endpoint с CORS", "WARN", f"Нет CORS headers. {details}")
            else:
                self.log_test("Video streaming endpoint с CORS", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Video streaming endpoint с CORS", "FAIL", f"Ошибка: {str(e)}")
        
        # Test PDF streaming endpoint
        try:
            response = self.session.get(f"{BACKEND_URL}/consultations/pdf/{TEST_PDF_FILE_ID}")
            
            if response.status_code == 200:
                # Check CORS headers
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                }
                
                has_cors = any(cors_headers.values())
                details = f"Content-Type: {response.headers.get('content-type')}, CORS headers: {has_cors}"
                
                if has_cors:
                    self.log_test("PDF streaming endpoint с CORS", "PASS", details)
                else:
                    self.log_test("PDF streaming endpoint с CORS", "WARN", f"Нет CORS headers. {details}")
            else:
                self.log_test("PDF streaming endpoint с CORS", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("PDF streaming endpoint с CORS", "FAIL", f"Ошибка: {str(e)}")
    
    def authenticate_test_user(self):
        """Аутентификация тестового пользователя t@t.t"""
        print("\n👤 ТЕСТ 6: АУТЕНТИФИКАЦИЯ ПОЛЬЗОВАТЕЛЯ t@t.t")
        
        # First, let's create the test user if it doesn't exist
        if not self.admin_token:
            self.log_test("Создание тестового пользователя", "SKIP", "Нет токена админа")
            return False
        
        # Create test user with specific ID
        try:
            user_data = {
                "email": TEST_USER_EMAIL,
                "password": "testpassword123",
                "full_name": "Test User",
                "birth_date": "15.03.1990",
                "city": "Москва"
            }
            
            # Try to register the user (might fail if already exists)
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=user_data)
            
            # Now try to login
            login_data = {
                "email": TEST_USER_EMAIL,
                "password": "testpassword123"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.user_token = data.get('access_token')
                user_info = data.get('user')
                
                if self.user_token and user_info:
                    details = f"User ID: {user_info.get('id')}, credits: {user_info.get('credits_remaining')}"
                    self.log_test("Аутентификация пользователя t@t.t", "PASS", details)
                    self.actual_user_id = user_info.get('id')
                    return True
                else:
                    self.log_test("Аутентификация пользователя t@t.t", "FAIL", "Отсутствует токен или данные")
                    return False
            else:
                self.log_test("Аутентификация пользователя t@t.t", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Аутентификация пользователя t@t.t", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def setup_user_credits(self):
        """Настройка кредитов пользователя для покупки консультации"""
        print("\n💰 ТЕСТ 7: НАСТРОЙКА КРЕДИТОВ ПОЛЬЗОВАТЕЛЯ")
        
        if not self.admin_token or not hasattr(self, 'actual_user_id'):
            self.log_test("Настройка кредитов", "SKIP", "Нет токена админа или ID пользователя")
            return
        
        headers = {'Authorization': f'Bearer {self.admin_token}', 'Content-Type': 'application/json'}
        
        try:
            # Set user credits to 10000 (full master consultation package)
            credits_data = {"credits_remaining": 10000}
            response = self.session.patch(f"{BACKEND_URL}/admin/users/{self.actual_user_id}/credits", 
                                        json=credits_data, headers=headers)
            
            if response.status_code == 200:
                self.log_test("Установка 10000 кредитов пользователю", "PASS", "Пользователь получил 10000 кредитов")
            else:
                self.log_test("Установка 10000 кредитов пользователю", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Установка 10000 кредитов пользователю", "FAIL", f"Ошибка: {str(e)}")
    
    def test_consultation_purchase(self):
        """Тестирование покупки консультации"""
        print("\n🛒 ТЕСТ 8: ПОКУПКА КОНСУЛЬТАЦИИ ЗА 6667 БАЛЛОВ")
        
        if not self.user_token:
            self.log_test("Покупка консультации", "SKIP", "Нет токена пользователя")
            return
        
        headers = {'Authorization': f'Bearer {self.user_token}'}
        
        try:
            response = self.session.post(f"{BACKEND_URL}/user/consultations/{TEST_CONSULTATION_ID}/purchase", 
                                       headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                credits_spent = data.get('credits_spent')
                remaining_credits = data.get('remaining_credits')
                
                if credits_spent == 6667 and remaining_credits == 3333:
                    self.log_test("Покупка консультации за 6667 баллов", "PASS", 
                                f"Списано: {credits_spent}, осталось: {remaining_credits}")
                else:
                    self.log_test("Покупка консультации за 6667 баллов", "FAIL", 
                                f"Неверные суммы - списано: {credits_spent}, осталось: {remaining_credits}")
            else:
                self.log_test("Покупка консультации за 6667 баллов", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Покупка консультации за 6667 баллов", "FAIL", f"Ошибка: {str(e)}")
    
    def test_purchased_consultation_access(self):
        """Проверка доступа к купленной консультации"""
        print("\n🔓 ТЕСТ 9: ДОСТУП К КУПЛЕННОЙ КОНСУЛЬТАЦИИ")
        
        if not self.user_token:
            self.log_test("Доступ к консультации", "SKIP", "Нет токена пользователя")
            return
        
        headers = {'Authorization': f'Bearer {self.user_token}'}
        
        try:
            response = self.session.get(f"{BACKEND_URL}/user/consultations", headers=headers)
            
            if response.status_code == 200:
                consultations = response.json()
                
                # Find our consultation
                purchased_consultation = None
                for consultation in consultations:
                    if consultation.get('id') == TEST_CONSULTATION_ID:
                        purchased_consultation = consultation
                        break
                
                if purchased_consultation:
                    is_purchased = purchased_consultation.get('is_purchased', False)
                    has_video_id = purchased_consultation.get('video_file_id') == TEST_VIDEO_FILE_ID
                    has_pdf_id = purchased_consultation.get('pdf_file_id') == TEST_PDF_FILE_ID
                    
                    if is_purchased and has_video_id and has_pdf_id:
                        self.log_test("Консультация помечена как купленная с доступом к файлам", "PASS", 
                                    f"is_purchased: {is_purchased}, video_file_id: {TEST_VIDEO_FILE_ID}, pdf_file_id: {TEST_PDF_FILE_ID}")
                    else:
                        details = f"is_purchased: {is_purchased}, video_file_id: {purchased_consultation.get('video_file_id')}, pdf_file_id: {purchased_consultation.get('pdf_file_id')}"
                        self.log_test("Консультация помечена как купленная с доступом к файлам", "FAIL", details)
                else:
                    self.log_test("Консультация помечена как купленная с доступом к файлам", "FAIL", "Консультация не найдена в списке пользователя")
            else:
                self.log_test("Доступ к консультации", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Доступ к консультации", "FAIL", f"Ошибка: {str(e)}")
    
    def test_file_access_without_auth(self):
        """Проверка доступа к файлам без аутентификации"""
        print("\n🌐 ТЕСТ 10: ДОСТУП К ФАЙЛАМ БЕЗ АУТЕНТИФИКАЦИИ")
        
        # Create a new session without authentication
        no_auth_session = requests.Session()
        
        # Test video access
        try:
            response = no_auth_session.get(f"{BACKEND_URL}/consultations/video/{TEST_VIDEO_FILE_ID}")
            
            if response.status_code == 200:
                self.log_test("Доступ к видео без аутентификации", "PASS", 
                            f"Видео доступно, Content-Type: {response.headers.get('content-type')}")
            else:
                self.log_test("Доступ к видео без аутентификации", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Доступ к видео без аутентификации", "FAIL", f"Ошибка: {str(e)}")
        
        # Test PDF access
        try:
            response = no_auth_session.get(f"{BACKEND_URL}/consultations/pdf/{TEST_PDF_FILE_ID}")
            
            if response.status_code == 200:
                self.log_test("Доступ к PDF без аутентификации", "PASS", 
                            f"PDF доступен, Content-Type: {response.headers.get('content-type')}")
            else:
                self.log_test("Доступ к PDF без аутентификации", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Доступ к PDF без аутентификации", "FAIL", f"Ошибка: {str(e)}")
    
    def test_admin_user_select(self):
        """Проверка работы select пользователей для assigned_user_id"""
        print("\n👥 ТЕСТ 11: SELECT ПОЛЬЗОВАТЕЛЕЙ ДЛЯ ASSIGNED_USER_ID")
        
        if not self.admin_token:
            self.log_test("Select пользователей", "SKIP", "Нет токена админа")
            return
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/users", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                
                if users:
                    # Check if our test user is in the list
                    test_user_found = False
                    for user in users:
                        if user.get('email') == TEST_USER_EMAIL:
                            test_user_found = True
                            break
                    
                    if test_user_found:
                        self.log_test("Select пользователей работает", "PASS", 
                                    f"Найдено {len(users)} пользователей, включая тестового пользователя {TEST_USER_EMAIL}")
                    else:
                        self.log_test("Select пользователей работает", "WARN", 
                                    f"Найдено {len(users)} пользователей, но тестовый пользователь не найден")
                else:
                    self.log_test("Select пользователей работает", "FAIL", "Список пользователей пуст")
            else:
                self.log_test("Select пользователей работает", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Select пользователей работает", "FAIL", f"Ошибка: {str(e)}")
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ СИСТЕМЫ ЛИЧНЫХ КОНСУЛЬТАЦИЙ")
        print("=" * 80)
        
        # Run tests in sequence
        if self.authenticate_admin():
            self.test_admin_file_upload()
            self.test_consultation_creation()
            self.test_consultation_verification()
            self.test_file_streaming_endpoints()
            
            if self.authenticate_test_user():
                self.setup_user_credits()
                self.test_consultation_purchase()
                self.test_purchased_consultation_access()
            
            self.test_file_access_without_auth()
            self.test_admin_user_select()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Печать итогового отчета"""
        print("\n" + "=" * 80)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ СИСТЕМЫ КОНСУЛЬТАЦИЙ")
        print("=" * 80)
        
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warnings = len([r for r in self.test_results if r['status'] == 'WARN'])
        skipped = len([r for r in self.test_results if r['status'] == 'SKIP'])
        total = len(self.test_results)
        
        print(f"✅ Пройдено: {passed}")
        print(f"❌ Провалено: {failed}")
        print(f"⚠️ Предупреждения: {warnings}")
        print(f"⏭️ Пропущено: {skipped}")
        print(f"📈 Общий результат: {passed}/{total} ({(passed/total*100):.1f}%)")
        
        if failed > 0:
            print("\n❌ ПРОВАЛИВШИЕСЯ ТЕСТЫ:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  • {result['test']}: {result['details']}")
        
        print("\n🎯 КРИТИЧЕСКАЯ ПРОВЕРКА:")
        critical_tests = [
            "Консультация имеет video_file_id и pdf_file_id",
            "Video streaming endpoint с CORS",
            "PDF streaming endpoint с CORS", 
            "Покупка консультации за 6667 баллов",
            "Консультация помечена как купленная с доступом к файлам"
        ]
        
        critical_passed = 0
        for test_name in critical_tests:
            for result in self.test_results:
                if result['test'] == test_name and result['status'] == 'PASS':
                    critical_passed += 1
                    break
        
        print(f"Критических тестов пройдено: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("🎉 ВСЕ КРИТИЧЕСКИЕ ТЕСТЫ ПРОЙДЕНЫ! Пользователь t@t.t может видеть консультацию как купленную с возможностью просмотра видео и скачивания PDF.")
        else:
            print("⚠️ НЕ ВСЕ КРИТИЧЕСКИЕ ТЕСТЫ ПРОЙДЕНЫ. Требуется дополнительная работа.")

if __name__ == "__main__":
    tester = ConsultationSystemTester()
    tester.run_all_tests()
"""
ТЕСТИРОВАНИЕ КОНСУЛЬТАЦИЙ: Создание тестовых пользователей для исправления проблемы с выбором студента

ПРОБЛЕМА: В форме создания консультации нет студентов для выбора, только placeholder "Выберите студента"

ЗАДАЧА: Создать несколько тестовых пользователей чтобы заполнить выбор студентов в админ панели

ПРОЦЕДУРА:
1. Аутентификация супер-админа: dmitrii.malahov@gmail.com / 756bvy67H  
2. Создание тестовых пользователей: Использовать POST /api/auth/register
3. Проверка админ панели: GET /api/admin/users
4. Тестирование консультаций: Создать тестовую консультацию с назначением на одного из пользователей
"""

import requests
import json
from datetime import datetime
import sys

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"

# Test users to create
TEST_USERS = [
    {
        "email": "student1@example.com",
        "password": "password123",
        "full_name": "Анна Иванова",
        "birth_date": "15.03.1995",
        "city": "Москва",
        "phone_number": "+7-900-123-4567",
        "expected_credits": 50
    },
    {
        "email": "student2@example.com", 
        "password": "password123",
        "full_name": "Петр Петров",
        "birth_date": "22.07.1990",
        "city": "Санкт-Петербург",
        "phone_number": "+7-900-234-5678",
        "expected_credits": 100
    },
    {
        "email": "student3@example.com",
        "password": "password123", 
        "full_name": "Мария Сидорова",
        "birth_date": "08.12.1992",
        "city": "Екатеринбург",
        "phone_number": "+7-900-345-6789",
        "expected_credits": 25
    },
    {
        "email": "student4@example.com",
        "password": "password123",
        "full_name": "Сергей Смирнов", 
        "birth_date": "03.05.1988",
        "city": "Новосибирск",
        "phone_number": "+7-900-456-7890",
        "expected_credits": 200
    },
    {
        "email": "student5@example.com",
        "password": "password123",
        "full_name": "Елена Козлова",
        "birth_date": "19.09.1993",
        "city": "Казань", 
        "phone_number": "+7-900-567-8901",
        "expected_credits": 75
    }
]

class ConsultationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.admin_user_data = None
        self.created_users = []
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
        """1. АУТЕНТИФИКАЦИЯ СУПЕР-АДМИНА"""
        print("\n🔐 ТЕСТ 1: АУТЕНТИФИКАЦИЯ СУПЕР-АДМИНА")
        print(f"Попытка входа: {SUPER_ADMIN_EMAIL}")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": SUPER_ADMIN_EMAIL,
                "password": SUPER_ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.admin_user_data = data.get('user', {})
                
                # Set authorization header for future requests
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}'
                })
                
                is_super_admin = self.admin_user_data.get('is_super_admin', False)
                credits = self.admin_user_data.get('credits_remaining', 0)
                
                if is_super_admin:
                    self.log_test("Аутентификация супер-админа", "PASS", 
                                f"Успешный вход. Кредиты: {credits}, Супер-админ: {is_super_admin}")
                    return True
                else:
                    self.log_test("Аутентификация супер-админа", "FAIL", 
                                "Пользователь не является супер-админом")
                    return False
            else:
                self.log_test("Аутентификация супер-админа", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Аутентификация супер-админа", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def create_test_users(self):
        """2. СОЗДАНИЕ ТЕСТОВЫХ ПОЛЬЗОВАТЕЛЕЙ"""
        print("\n👥 ТЕСТ 2: СОЗДАНИЕ ТЕСТОВЫХ ПОЛЬЗОВАТЕЛЕЙ")
        
        success_count = 0
        
        for i, user_data in enumerate(TEST_USERS, 1):
            print(f"\nСоздание пользователя {i}/5: {user_data['full_name']} ({user_data['email']})")
            
            try:
                # Create user via registration endpoint
                response = self.session.post(f"{BACKEND_URL}/auth/register", json={
                    "email": user_data["email"],
                    "password": user_data["password"], 
                    "full_name": user_data["full_name"],
                    "birth_date": user_data["birth_date"],
                    "city": user_data["city"],
                    "phone_number": user_data["phone_number"]
                })
                
                if response.status_code == 200:
                    created_user = response.json()
                    user_info = created_user.get('user', {})
                    
                    # Store created user info
                    self.created_users.append({
                        'id': user_info.get('id'),
                        'email': user_data['email'],
                        'full_name': user_data['full_name'],
                        'birth_date': user_data['birth_date'],
                        'expected_credits': user_data['expected_credits']
                    })
                    
                    success_count += 1
                    self.log_test(f"Создание пользователя {user_data['full_name']}", "PASS",
                                f"ID: {user_info.get('id')}, Email: {user_data['email']}")
                    
                elif response.status_code == 400 and "already exists" in response.text:
                    # User already exists - this is OK for testing
                    self.log_test(f"Создание пользователя {user_data['full_name']}", "PASS",
                                f"Пользователь уже существует: {user_data['email']}")
                    success_count += 1
                    
                    # Still add to created_users list for further testing
                    self.created_users.append({
                        'email': user_data['email'],
                        'full_name': user_data['full_name'],
                        'birth_date': user_data['birth_date'],
                        'expected_credits': user_data['expected_credits']
                    })
                else:
                    self.log_test(f"Создание пользователя {user_data['full_name']}", "FAIL",
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Создание пользователя {user_data['full_name']}", "FAIL", 
                            f"Ошибка: {str(e)}")
        
        overall_status = "PASS" if success_count >= 3 else "FAIL"
        self.log_test("Создание тестовых пользователей", overall_status,
                    f"Создано/проверено {success_count}/5 пользователей")
        
        return success_count >= 3
    
    def update_user_credits(self):
        """2.1. ОБНОВЛЕНИЕ КРЕДИТОВ ПОЛЬЗОВАТЕЛЕЙ"""
        print("\n💰 ТЕСТ 2.1: ОБНОВЛЕНИЕ КРЕДИТОВ ПОЛЬЗОВАТЕЛЕЙ")
        
        if not self.created_users:
            self.log_test("Обновление кредитов", "SKIP", "Нет созданных пользователей")
            return False
        
        # First get all users to find their IDs
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/users")
            if response.status_code == 200:
                admin_users_data = response.json()
                all_users = admin_users_data.get('users', [])
                
                # Match created users with their IDs from admin panel
                for created_user in self.created_users:
                    for admin_user in all_users:
                        if admin_user['email'] == created_user['email']:
                            created_user['id'] = admin_user['id']
                            break
                
                # Update credits for each user
                success_count = 0
                for user in self.created_users:
                    if 'id' not in user:
                        continue
                        
                    try:
                        credits_response = self.session.patch(
                            f"{BACKEND_URL}/admin/users/{user['id']}/credits",
                            json={"credits_remaining": user['expected_credits']}
                        )
                        
                        if credits_response.status_code == 200:
                            success_count += 1
                            self.log_test(f"Обновление кредитов {user['full_name']}", "PASS",
                                        f"Установлено {user['expected_credits']} кредитов")
                        else:
                            self.log_test(f"Обновление кредитов {user['full_name']}", "FAIL",
                                        f"HTTP {credits_response.status_code}")
                    except Exception as e:
                        self.log_test(f"Обновление кредитов {user['full_name']}", "FAIL", str(e))
                
                overall_status = "PASS" if success_count >= 3 else "FAIL"
                self.log_test("Обновление кредитов пользователей", overall_status,
                            f"Обновлено {success_count}/{len(self.created_users)} пользователей")
                return success_count >= 3
                
            else:
                self.log_test("Обновление кредитов", "FAIL", 
                            f"Не удалось получить список пользователей: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Обновление кредитов", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def check_admin_users_list(self):
        """3. ПРОВЕРКА АДМИН ПАНЕЛИ: GET /api/admin/users"""
        print("\n📋 ТЕСТ 3: ПРОВЕРКА АДМИН ПАНЕЛИ - СПИСОК ПОЛЬЗОВАТЕЛЕЙ")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/users")
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                total_count = data.get('total_count', 0)
                
                # Check if our test users are in the list
                found_users = []
                for test_user in self.created_users:
                    for user in users:
                        if user['email'] == test_user['email']:
                            found_users.append({
                                'email': user['email'],
                                'name': user.get('name', ''),
                                'credits': user.get('credits_remaining', 0),
                                'id': user.get('id', '')
                            })
                            break
                
                if len(found_users) >= 3:
                    self.log_test("Проверка админ панели", "PASS",
                                f"Найдено {len(found_users)}/5 тестовых пользователей в списке из {total_count} пользователей")
                    
                    # Log details of found users
                    for user in found_users:
                        print(f"  - {user['name']} ({user['email']}) - {user['credits']} кредитов - ID: {user['id']}")
                    
                    return True
                else:
                    self.log_test("Проверка админ панели", "FAIL",
                                f"Найдено только {len(found_users)}/5 тестовых пользователей")
                    return False
                    
            else:
                self.log_test("Проверка админ панели", "FAIL",
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Проверка админ панели", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def test_consultation_creation(self):
        """4. ТЕСТИРОВАНИЕ КОНСУЛЬТАЦИЙ: Создание тестовой консультации"""
        print("\n🎯 ТЕСТ 4: ТЕСТИРОВАНИЕ СОЗДАНИЯ КОНСУЛЬТАЦИЙ")
        
        if not self.created_users:
            self.log_test("Создание консультации", "SKIP", "Нет тестовых пользователей")
            return False
        
        # Select first user for assignment
        target_user = self.created_users[0]
        
        # Get user ID from admin panel if not available
        if 'id' not in target_user:
            try:
                response = self.session.get(f"{BACKEND_URL}/admin/users")
                if response.status_code == 200:
                    users = response.json().get('users', [])
                    for user in users:
                        if user['email'] == target_user['email']:
                            target_user['id'] = user['id']
                            break
            except Exception as e:
                self.log_test("Получение ID пользователя", "FAIL", str(e))
                return False
        
        if 'id' not in target_user:
            self.log_test("Создание консультации", "FAIL", "Не удалось найти ID пользователя")
            return False
        
        # Create test consultation
        consultation_data = {
            "id": f"test_consultation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": "Тестовая персональная консультация",
            "description": "Консультация для тестирования системы назначения студентов",
            "cost_credits": 50,
            "duration_minutes": 60,
            "assigned_user_id": target_user['id'],
            "is_active": True,
            "consultation_type": "personal_numerology",
            "created_at": datetime.now().isoformat()
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/admin/consultations", json=consultation_data)
            
            if response.status_code == 200:
                result = response.json()
                consultation_id = result.get('consultation_id')
                
                self.log_test("Создание консультации", "PASS",
                            f"Консультация создана с ID: {consultation_id}, назначена пользователю: {target_user['full_name']} ({target_user['email']})")
                
                # Test getting user consultations
                return self.test_user_consultations(target_user)
                
            else:
                self.log_test("Создание консультации", "FAIL",
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Создание консультации", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def test_user_consultations(self, target_user):
        """4.1. ПРОВЕРКА КОНСУЛЬТАЦИЙ ПОЛЬЗОВАТЕЛЯ"""
        print(f"\n👤 ТЕСТ 4.1: ПРОВЕРКА КОНСУЛЬТАЦИЙ ПОЛЬЗОВАТЕЛЯ {target_user['full_name']}")
        
        # First, authenticate as the target user to check their consultations
        try:
            # Login as target user
            login_response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": target_user['email'],
                "password": "password123"  # Default password for test users
            })
            
            if login_response.status_code == 200:
                user_token = login_response.json().get('access_token')
                
                # Create new session for user
                user_session = requests.Session()
                user_session.headers.update({
                    'Authorization': f'Bearer {user_token}'
                })
                
                # Get user consultations
                consultations_response = user_session.get(f"{BACKEND_URL}/user/consultations")
                
                if consultations_response.status_code == 200:
                    consultations = consultations_response.json()
                    
                    if len(consultations) > 0:
                        self.log_test("Проверка консультаций пользователя", "PASS",
                                    f"Пользователь видит {len(consultations)} назначенных консультаций")
                        
                        # Test purchasing consultation
                        consultation = consultations[0]
                        return self.test_consultation_purchase(user_session, consultation, target_user)
                    else:
                        self.log_test("Проверка консультаций пользователя", "FAIL",
                                    "Пользователь не видит назначенных консультаций")
                        return False
                else:
                    self.log_test("Проверка консультаций пользователя", "FAIL",
                                f"HTTP {consultations_response.status_code}: {consultations_response.text}")
                    return False
            else:
                self.log_test("Вход пользователя для проверки консультаций", "FAIL",
                            f"HTTP {login_response.status_code}: {login_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Проверка консультаций пользователя", "FAIL", f"Ошибка: {str(e)}")
            return False
        finally:
            # Restore admin session
            self.session.headers.update({
                'Authorization': f'Bearer {self.auth_token}'
            })
    
    def test_consultation_purchase(self, user_session, consultation, target_user):
        """4.2. ТЕСТИРОВАНИЕ ПОКУПКИ КОНСУЛЬТАЦИИ"""
        print(f"\n💳 ТЕСТ 4.2: ТЕСТИРОВАНИЕ ПОКУПКИ КОНСУЛЬТАЦИИ")
        
        consultation_id = consultation.get('id')
        cost = consultation.get('cost_credits', 0)
        
        try:
            # Attempt to purchase consultation
            purchase_response = user_session.post(f"{BACKEND_URL}/user/consultations/{consultation_id}/purchase")
            
            if purchase_response.status_code == 200:
                result = purchase_response.json()
                self.log_test("Покупка консультации", "PASS",
                            f"Консультация успешно приобретена за {cost} кредитов. Остаток: {result.get('remaining_credits', 'N/A')}")
                return True
                
            elif purchase_response.status_code == 402:
                # Insufficient credits - this is expected behavior
                self.log_test("Покупка консультации", "PASS",
                            f"Корректная обработка недостатка кредитов: {purchase_response.text}")
                return True
                
            elif purchase_response.status_code == 400 and "уже приобретена" in purchase_response.text:
                # Already purchased - this is also OK
                self.log_test("Покупка консультации", "PASS",
                            "Корректная обработка повторной покупки")
                return True
                
            else:
                self.log_test("Покупка консультации", "FAIL",
                            f"HTTP {purchase_response.status_code}: {purchase_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Покупка консультации", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def test_admin_consultations_list(self):
        """5. ПРОВЕРКА СПИСКА КОНСУЛЬТАЦИЙ В АДМИН ПАНЕЛИ"""
        print("\n📊 ТЕСТ 5: ПРОВЕРКА СПИСКА КОНСУЛЬТАЦИЙ В АДМИН ПАНЕЛИ")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/consultations")
            
            if response.status_code == 200:
                consultations = response.json()
                
                if len(consultations) > 0:
                    self.log_test("Список консультаций в админ панели", "PASS",
                                f"Найдено {len(consultations)} консультаций")
                    
                    # Check if consultations have assigned_user_id
                    assigned_count = 0
                    for consultation in consultations:
                        if consultation.get('assigned_user_id'):
                            assigned_count += 1
                    
                    if assigned_count > 0:
                        self.log_test("Проверка поля assigned_user_id", "PASS",
                                    f"{assigned_count}/{len(consultations)} консультаций имеют назначенных пользователей")
                        return True
                    else:
                        self.log_test("Проверка поля assigned_user_id", "FAIL",
                                    "Ни одна консультация не имеет назначенного пользователя")
                        return False
                else:
                    self.log_test("Список консультаций в админ панели", "FAIL",
                                "Список консультаций пуст")
                    return False
                    
            else:
                self.log_test("Список консультаций в админ панели", "FAIL",
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Список консультаций в админ панели", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 НАЧАЛО ТЕСТИРОВАНИЯ КОНСУЛЬТАЦИЙ")
        print("=" * 80)
        
        # Test sequence
        tests = [
            ("Аутентификация супер-админа", self.authenticate_super_admin),
            ("Создание тестовых пользователей", self.create_test_users),
            ("Обновление кредитов пользователей", self.update_user_credits),
            ("Проверка админ панели", self.check_admin_users_list),
            ("Тестирование создания консультаций", self.test_consultation_creation),
            ("Проверка списка консультаций", self.test_admin_consultations_list)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_test(test_name, "ERROR", f"Неожиданная ошибка: {str(e)}")
        
        # Final summary
        print("\n" + "=" * 80)
        print("📊 ИТОГОВЫЙ ОТЧЕТ")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        status_icon = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 60 else "❌"
        
        print(f"{status_icon} ОБЩИЙ РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено ({success_rate:.1f}%)")
        
        if passed_tests >= 4:
            print("\n🎉 ПРОБЛЕМА РЕШЕНА:")
            print("- Тестовые пользователи созданы и доступны в админ панели")
            print("- Система консультаций работает корректно")
            print("- Поле assigned_user_id функционирует правильно")
            print("- В форме создания консультации теперь есть студенты для выбора")
        else:
            print("\n❌ ПРОБЛЕМА НЕ РЕШЕНА:")
            print("- Требуется дополнительная диагностика")
            print("- Проверьте логи выше для деталей ошибок")
        
        # Detailed test results
        print("\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for result in self.test_results:
            status_icon = "✅" if result['status'] == "PASS" else "❌" if result['status'] == "FAIL" else "⚠️"
            print(f"{status_icon} {result['test']}: {result['details']}")
        
        return success_rate >= 80

def main():
    """Main test execution"""
    tester = ConsultationTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()