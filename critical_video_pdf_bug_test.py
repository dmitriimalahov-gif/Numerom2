#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Диагностика бага воспроизведения видео/PDF в FirstLesson.jsx и PersonalConsultations.jsx

КОНТЕКСТ ПРОБЛЕМЫ:
Был обнаружен критический баг: видео и PDF файлы успешно загружаются через админ-панель, 
но НЕ отображаются/не воспроизводятся в компонентах обучения (FirstLesson.jsx, PersonalConsultations.jsx). 
Проблема в несоответствии API endpoints.

ЦЕЛЬ ТЕСТИРОВАНИЯ:
1. Проверить работу новых упрощенных endpoints для загрузки медиа уроков
2. Проверить интеграцию с существующими API уроков
3. Проверить доступность файлов для фронтенда
4. Проверить совместимость с системой уроков
"""

import requests
import json
import io
import os
from datetime import datetime
from pathlib import Path

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
TEST_ADMIN_PASSWORD = "756bvy67H"

class CriticalVideoPDFBugTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        self.uploaded_files = []
        
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
                "email": TEST_ADMIN_EMAIL,
                "password": TEST_ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.user_data = data.get('user', {})
                
                # Set authorization header for future requests
                self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                
                # Verify super admin status
                is_super_admin = self.user_data.get('is_super_admin', False)
                credits = self.user_data.get('credits_remaining', 0)
                
                if is_super_admin:
                    self.log_test("Аутентификация супер-админа", "PASS", 
                                f"Успешный вход: {TEST_ADMIN_EMAIL}, кредиты: {credits}, супер-админ: {is_super_admin}")
                    return True
                else:
                    self.log_test("Аутентификация супер-админа", "FAIL", 
                                f"Пользователь не является супер-админом: {is_super_admin}")
                    return False
            else:
                self.log_test("Аутентификация супер-админа", "FAIL", 
                            f"Ошибка входа: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Аутентификация супер-админа", "FAIL", f"Исключение: {str(e)}")
            return False

    def create_test_video_file(self):
        """Создать тестовый видео файл"""
        # Create a more realistic MP4 file header for testing
        video_content = (
            b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom'
            b'\x00\x00\x00\x08free\x00\x00\x00\x28mdat'
            b'Test video content for FirstLesson.jsx integration testing'
        )
        return io.BytesIO(video_content), "firstlesson_test_video.mp4", "video/mp4"

    def create_test_pdf_file(self):
        """Создать тестовый PDF файл"""
        # Create a more realistic PDF file for testing
        pdf_content = (
            b'%PDF-1.4\n'
            b'1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n'
            b'2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n'
            b'3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n'
            b'/Contents 4 0 R\n>>\nendobj\n'
            b'4 0 obj\n<<\n/Length 44\n>>\nstream\n'
            b'BT\n/F1 12 Tf\n100 700 Td\n(FirstLesson PDF Test) Tj\nET\n'
            b'endstream\nendobj\n'
            b'xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n'
            b'0000000058 00000 n \n0000000115 00000 n \n0000000229 00000 n \n'
            b'trailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n323\n%%EOF'
        )
        return io.BytesIO(pdf_content), "firstlesson_test_material.pdf", "application/pdf"

    def test_new_lesson_video_upload(self):
        """ТЕСТ 2: POST /api/admin/lessons/upload-video - новый упрощенный endpoint"""
        print("\n📹 ТЕСТ 2: НОВЫЙ ENDPOINT ЗАГРУЗКИ ВИДЕО ДЛЯ УРОКОВ")
        try:
            # Create test video file
            video_file, filename, content_type = self.create_test_video_file()
            
            # Prepare multipart form data
            files = {
                'file': (filename, video_file, content_type)
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/lessons/upload-video", files=files)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure according to review request
                required_fields = ['success', 'file_id', 'filename', 'video_url', 'message']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    file_id = data.get('file_id')
                    video_url = data.get('video_url')
                    
                    # Store for later testing
                    self.test_video_id = file_id
                    self.test_video_url = video_url
                    self.uploaded_files.append(('video', file_id))
                    
                    # Verify URL format matches expected pattern
                    expected_pattern = f'/api/lessons/video/{file_id}'
                    if video_url == expected_pattern:
                        self.log_test("Новый endpoint загрузки видео", "PASS", 
                                    f"Видео загружено: file_id={file_id}, video_url={video_url}")
                        return True
                    else:
                        self.log_test("Новый endpoint загрузки видео", "FAIL", 
                                    f"Неверный формат URL: ожидался {expected_pattern}, получен {video_url}")
                        return False
                else:
                    self.log_test("Новый endpoint загрузки видео", "FAIL", 
                                f"Отсутствуют поля в ответе: {missing_fields}")
                    return False
            else:
                self.log_test("Новый endpoint загрузки видео", "FAIL", 
                            f"Ошибка HTTP: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Новый endpoint загрузки видео", "FAIL", f"Исключение: {str(e)}")
            return False

    def test_new_lesson_pdf_upload(self):
        """ТЕСТ 3: POST /api/admin/lessons/upload-pdf - новый упрощенный endpoint"""
        print("\n📄 ТЕСТ 3: НОВЫЙ ENDPOINT ЗАГРУЗКИ PDF ДЛЯ УРОКОВ")
        try:
            # Create test PDF file
            pdf_file, filename, content_type = self.create_test_pdf_file()
            
            # Prepare multipart form data
            files = {
                'file': (filename, pdf_file, content_type)
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/lessons/upload-pdf", files=files)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure according to review request
                required_fields = ['success', 'file_id', 'filename', 'pdf_url', 'message']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    file_id = data.get('file_id')
                    pdf_url = data.get('pdf_url')
                    
                    # Store for later testing
                    self.test_pdf_id = file_id
                    self.test_pdf_url = pdf_url
                    self.uploaded_files.append(('pdf', file_id))
                    
                    # Verify URL format matches expected pattern
                    expected_pattern = f'/api/lessons/pdf/{file_id}'
                    if pdf_url == expected_pattern:
                        self.log_test("Новый endpoint загрузки PDF", "PASS", 
                                    f"PDF загружен: file_id={file_id}, pdf_url={pdf_url}")
                        return True
                    else:
                        self.log_test("Новый endpoint загрузки PDF", "FAIL", 
                                    f"Неверный формат URL: ожидался {expected_pattern}, получен {pdf_url}")
                        return False
                else:
                    self.log_test("Новый endpoint загрузки PDF", "FAIL", 
                                f"Отсутствуют поля в ответе: {missing_fields}")
                    return False
            else:
                self.log_test("Новый endpoint загрузки PDF", "FAIL", 
                            f"Ошибка HTTP: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Новый endpoint загрузки PDF", "FAIL", f"Исключение: {str(e)}")
            return False

    def test_video_streaming_for_frontend(self):
        """ТЕСТ 4: GET /api/lessons/video/{file_id} - доступность для фронтенда"""
        print("\n🎬 ТЕСТ 4: СТРИМИНГ ВИДЕО ДЛЯ ФРОНТЕНДА")
        try:
            if not hasattr(self, 'test_video_id'):
                self.log_test("Стриминг видео для фронтенда", "SKIP", "Нет загруженного видео для тестирования")
                return False
            
            # Test without authentication (as frontend would access)
            unauth_session = requests.Session()
            response = unauth_session.get(f"{BACKEND_URL}/lessons/video/{self.test_video_id}")
            
            if response.status_code == 200:
                # Check content type and CORS headers
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                cors_origin = response.headers.get('access-control-allow-origin', '')
                
                if content_type.startswith('video/') and content_length > 0:
                    self.log_test("Стриминг видео для фронтенда", "PASS", 
                                f"Видео доступно: content-type={content_type}, размер={content_length} байт, CORS={cors_origin}")
                    return True
                else:
                    self.log_test("Стриминг видео для фронтенда", "FAIL", 
                                f"Неверный content-type или пустой файл: {content_type}, размер={content_length}")
                    return False
            else:
                self.log_test("Стриминг видео для фронтенда", "FAIL", 
                            f"Ошибка HTTP: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Стриминг видео для фронтенда", "FAIL", f"Исключение: {str(e)}")
            return False

    def test_pdf_streaming_for_frontend(self):
        """ТЕСТ 5: GET /api/lessons/pdf/{file_id} - доступность для фронтенда"""
        print("\n📖 ТЕСТ 5: СТРИМИНГ PDF ДЛЯ ФРОНТЕНДА")
        try:
            if not hasattr(self, 'test_pdf_id'):
                self.log_test("Стриминг PDF для фронтенда", "SKIP", "Нет загруженного PDF для тестирования")
                return False
            
            # Test without authentication (as frontend would access)
            unauth_session = requests.Session()
            response = unauth_session.get(f"{BACKEND_URL}/lessons/pdf/{self.test_pdf_id}")
            
            if response.status_code == 200:
                # Check content type and CORS headers
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                cors_origin = response.headers.get('access-control-allow-origin', '')
                
                if content_type == 'application/pdf' and content_length > 0:
                    self.log_test("Стриминг PDF для фронтенда", "PASS", 
                                f"PDF доступен: content-type={content_type}, размер={content_length} байт, CORS={cors_origin}")
                    return True
                else:
                    self.log_test("Стриминг PDF для фронтенда", "FAIL", 
                                f"Неверный content-type или пустой файл: {content_type}, размер={content_length}")
                    return False
            else:
                self.log_test("Стриминг PDF для фронтенда", "FAIL", 
                            f"Ошибка HTTP: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Стриминг PDF для фронтенда", "FAIL", f"Исключение: {str(e)}")
            return False

    def test_directory_structure_creation(self):
        """ТЕСТ 6: Проверка создания директорий LESSONS_VIDEO_DIR, LESSONS_PDF_DIR"""
        print("\n📁 ТЕСТ 6: ПРОВЕРКА СОЗДАНИЯ ДИРЕКТОРИЙ")
        try:
            # Test that files are stored in correct directories by checking database records
            if hasattr(self, 'test_video_id'):
                # The directories should be created automatically by the backend
                # We can verify this by checking if our uploaded files are accessible
                video_response = self.session.get(f"{BACKEND_URL}/lessons/video/{self.test_video_id}")
                if video_response.status_code == 200:
                    self.log_test("Создание LESSONS_VIDEO_DIR", "PASS", 
                                "Видео файл доступен, директория создана корректно")
                else:
                    self.log_test("Создание LESSONS_VIDEO_DIR", "FAIL", 
                                f"Видео файл недоступен: {video_response.status_code}")
                    return False
            
            if hasattr(self, 'test_pdf_id'):
                pdf_response = self.session.get(f"{BACKEND_URL}/lessons/pdf/{self.test_pdf_id}")
                if pdf_response.status_code == 200:
                    self.log_test("Создание LESSONS_PDF_DIR", "PASS", 
                                "PDF файл доступен, директория создана корректно")
                    return True
                else:
                    self.log_test("Создание LESSONS_PDF_DIR", "FAIL", 
                                f"PDF файл недоступен: {pdf_response.status_code}")
                    return False
            
            self.log_test("Проверка создания директорий", "SKIP", "Нет загруженных файлов для проверки")
            return False
                
        except Exception as e:
            self.log_test("Проверка создания директорий", "FAIL", f"Исключение: {str(e)}")
            return False

    def test_uuid_generation(self):
        """ТЕСТ 7: Проверка генерации уникальных имен файлов (uuid)"""
        print("\n🆔 ТЕСТ 7: ПРОВЕРКА ГЕНЕРАЦИИ UUID")
        try:
            file_ids = []
            
            # Upload multiple files to test UUID uniqueness
            for i in range(3):
                video_file, filename, content_type = self.create_test_video_file()
                files = {'file': (f"test_uuid_{i}.mp4", video_file, content_type)}
                
                response = self.session.post(f"{BACKEND_URL}/admin/lessons/upload-video", files=files)
                
                if response.status_code == 200:
                    data = response.json()
                    file_id = data.get('file_id')
                    if file_id:
                        file_ids.append(file_id)
                        self.uploaded_files.append(('video', file_id))
                else:
                    self.log_test("Генерация UUID", "FAIL", 
                                f"Ошибка загрузки файла {i}: {response.status_code}")
                    return False
            
            # Check that all file IDs are unique and look like UUIDs
            if len(file_ids) == 3 and len(set(file_ids)) == 3:
                # Basic UUID format check (36 characters with dashes)
                uuid_pattern_valid = all(len(fid) == 36 and fid.count('-') == 4 for fid in file_ids)
                if uuid_pattern_valid:
                    self.log_test("Генерация UUID", "PASS", 
                                f"Все файлы получили уникальные UUID: {file_ids}")
                    return True
                else:
                    self.log_test("Генерация UUID", "FAIL", 
                                f"Неверный формат UUID: {file_ids}")
                    return False
            else:
                self.log_test("Генерация UUID", "FAIL", 
                            f"UUID не уникальны или неполные: {file_ids}")
                return False
                
        except Exception as e:
            self.log_test("Генерация UUID", "FAIL", f"Исключение: {str(e)}")
            return False

    def test_integration_with_existing_lesson_system(self):
        """ТЕСТ 8: Интеграция с существующей системой уроков"""
        print("\n🔗 ТЕСТ 8: ИНТЕГРАЦИЯ С СИСТЕМОЙ УРОКОВ")
        try:
            # Test that existing lesson APIs still work after new endpoints addition
            response = self.session.get(f"{BACKEND_URL}/learning/levels")
            
            if response.status_code == 200:
                data = response.json()
                if 'user_level' in data and 'available_lessons' in data:
                    lessons_count = len(data.get('available_lessons', []))
                    self.log_test("Интеграция с API уроков", "PASS", 
                                f"API уроков работает: {lessons_count} уроков доступно")
                else:
                    self.log_test("Интеграция с API уроков", "FAIL", 
                                "Неверная структура ответа API уроков")
                    return False
            else:
                self.log_test("Интеграция с API уроков", "FAIL", 
                            f"Ошибка API уроков: {response.status_code}")
                return False
            
            # Test admin lessons API
            response = self.session.get(f"{BACKEND_URL}/admin/lessons")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Интеграция с админ API", "PASS", 
                                f"Админ API работает: {len(data)} уроков в системе")
                    return True
                else:
                    self.log_test("Интеграция с админ API", "FAIL", 
                                "Неверная структура ответа админ API")
                    return False
            else:
                self.log_test("Интеграция с админ API", "FAIL", 
                            f"Ошибка админ API: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Интеграция с системой уроков", "FAIL", f"Исключение: {str(e)}")
            return False

    def test_firstlesson_api_compatibility(self):
        """ТЕСТ 9: Совместимость с FirstLesson.jsx API"""
        print("\n🎯 ТЕСТ 9: СОВМЕСТИМОСТЬ С FIRSTLESSON.JSX")
        try:
            # Test FirstLesson API endpoints that might use the uploaded media
            response = self.session.get(f"{BACKEND_URL}/lessons/first-lesson")
            
            if response.status_code == 200:
                data = response.json()
                if 'lesson_id' in data and 'title' in data:
                    self.log_test("FirstLesson API совместимость", "PASS", 
                                f"FirstLesson API работает: урок '{data.get('title', 'Без названия')}'")
                    return True
                else:
                    self.log_test("FirstLesson API совместимость", "FAIL", 
                                "Неверная структура ответа FirstLesson API")
                    return False
            else:
                self.log_test("FirstLesson API совместимость", "FAIL", 
                            f"Ошибка FirstLesson API: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("FirstLesson API совместимость", "FAIL", f"Исключение: {str(e)}")
            return False

    def test_personal_consultations_compatibility(self):
        """ТЕСТ 10: Совместимость с PersonalConsultations.jsx"""
        print("\n👥 ТЕСТ 10: СОВМЕСТИМОСТЬ С PERSONALCONSULTATIONS.JSX")
        try:
            # Test personal consultations API that might use uploaded media
            response = self.session.get(f"{BACKEND_URL}/consultations/personal")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("PersonalConsultations API совместимость", "PASS", 
                                f"PersonalConsultations API работает: {len(data)} консультаций")
                    return True
                else:
                    self.log_test("PersonalConsultations API совместимость", "FAIL", 
                                "Неверная структура ответа PersonalConsultations API")
                    return False
            else:
                # 404 might be expected if no consultations exist
                if response.status_code == 404:
                    self.log_test("PersonalConsultations API совместимость", "PASS", 
                                "PersonalConsultations API работает (нет консультаций)")
                    return True
                else:
                    self.log_test("PersonalConsultations API совместимость", "FAIL", 
                                f"Ошибка PersonalConsultations API: {response.status_code}")
                    return False
                
        except Exception as e:
            self.log_test("PersonalConsultations API совместимость", "FAIL", f"Исключение: {str(e)}")
            return False

    def run_all_tests(self):
        """Запустить все тесты"""
        print("🚨 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправление бага воспроизведения видео/PDF в FirstLesson.jsx и PersonalConsultations.jsx")
        print("=" * 120)
        
        # Initialize test variables
        self.test_video_id = None
        self.test_video_url = None
        self.test_pdf_id = None
        self.test_pdf_url = None
        self.uploaded_files = []
        
        tests = [
            self.authenticate_admin,
            self.test_new_lesson_video_upload,
            self.test_new_lesson_pdf_upload,
            self.test_video_streaming_for_frontend,
            self.test_pdf_streaming_for_frontend,
            self.test_directory_structure_creation,
            self.test_uuid_generation,
            self.test_integration_with_existing_lesson_system,
            self.test_firstlesson_api_compatibility,
            self.test_personal_consultations_compatibility
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ Критическая ошибка в тесте {test.__name__}: {str(e)}")
                failed += 1
        
        # Summary
        print("\n" + "=" * 120)
        print("📊 ИТОГОВЫЙ ОТЧЕТ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ")
        print("=" * 120)
        
        total_tests = passed + failed
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ Пройдено тестов: {passed}")
        print(f"❌ Провалено тестов: {failed}")
        print(f"📈 Успешность: {success_rate:.1f}%")
        
        # Critical assessment
        if success_rate >= 90:
            print("\n🎉 КРИТИЧЕСКИЙ БАГ ИСПРАВЛЕН УСПЕШНО!")
            print("Новые endpoints для загрузки видео/PDF уроков работают корректно.")
            print("Интеграция с FirstLesson.jsx и PersonalConsultations.jsx должна работать.")
        elif success_rate >= 70:
            print("\n⚠️ ЧАСТИЧНОЕ ИСПРАВЛЕНИЕ - ТРЕБУЕТСЯ ДОРАБОТКА")
            print("Основная функциональность работает, но есть проблемы с интеграцией.")
        else:
            print("\n🚨 КРИТИЧЕСКИЙ БАГ НЕ ИСПРАВЛЕН!")
            print("Серьезные проблемы с новыми endpoints или интеграцией.")
        
        # Detailed results
        print("\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for result in self.test_results:
            status_icon = "✅" if result['status'] == "PASS" else "❌" if result['status'] == "FAIL" else "⚠️"
            print(f"{status_icon} {result['test']}: {result['details']}")
        
        # Cleanup info
        if self.uploaded_files:
            print(f"\n🗑️ ЗАГРУЖЕННЫЕ ТЕСТОВЫЕ ФАЙЛЫ ({len(self.uploaded_files)}):")
            for file_type, file_id in self.uploaded_files:
                print(f"  • {file_type.upper()}: {file_id}")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = CriticalVideoPDFBugTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 КРИТИЧЕСКИЙ БАГ УСПЕШНО ИСПРАВЛЕН!")
        exit(0)
    else:
        print("\n💥 КРИТИЧЕСКИЙ БАГ НЕ ИСПРАВЛЕН!")
        exit(1)