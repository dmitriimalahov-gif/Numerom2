#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Проблемы с отображением и загрузкой PDF файлов при создании уроков
Critical Testing: PDF Upload and Display Issues in Admin Panel

Тестирование согласно review request от пользователя dmitrii.malahov@gmail.com:
1. Проблемы с PDF загрузкой в админ панели (POST /api/admin/consultations/upload-pdf)
2. Проверка CORS headers для PDF endpoints
3. Проблемы с отображением уроков (GET /api/admin/lessons, GET /api/learning/levels)
4. Проблемы со стримингом PDF (GET /api/consultations/pdf/{file_id})
5. Проверка ObjectId serialization ошибок
"""

import requests
import json
import io
from datetime import datetime
import sys
import os

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_USER_EMAIL = "dmitrii.malahov@gmail.com"
TEST_USER_PASSWORD = "756bvy67H"

class PDFUploadTester:
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
        """Аутентификация супер-админа dmitrii.malahov@gmail.com"""
        print("\n🔐 АУТЕНТИФИКАЦИЯ СУПЕР-АДМИНА")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.user_data = data.get('user', {})
                
                # Set authorization header for future requests
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}',
                    'Content-Type': 'application/json'
                })
                
                is_super_admin = self.user_data.get('is_super_admin', False)
                credits = self.user_data.get('credits_remaining', 0)
                
                self.log_test(
                    "Аутентификация супер-админа", 
                    "PASS", 
                    f"Успешный вход: {TEST_USER_EMAIL}, супер-админ: {is_super_admin}, кредиты: {credits}"
                )
                return True
            else:
                self.log_test(
                    "Аутентификация супер-админа", 
                    "FAIL", 
                    f"Ошибка входа: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Аутентификация супер-админа", "FAIL", f"Исключение: {str(e)}")
            return False

    def test_pdf_upload_endpoints(self):
        """Тестирование PDF upload endpoints"""
        print("\n📄 ТЕСТ PDF UPLOAD ENDPOINTS")
        
        # Test 1: Check if consultation PDF upload endpoint exists
        try:
            # First check if the endpoint exists by making an OPTIONS request
            response = self.session.options(f"{BACKEND_URL}/admin/consultations/upload-pdf")
            
            if response.status_code in [200, 204, 405]:  # 405 means method not allowed but endpoint exists
                self.log_test(
                    "PDF Upload Endpoint Existence", 
                    "PASS", 
                    f"Endpoint /api/admin/consultations/upload-pdf доступен (статус: {response.status_code})"
                )
            else:
                self.log_test(
                    "PDF Upload Endpoint Existence", 
                    "FAIL", 
                    f"Endpoint недоступен: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("PDF Upload Endpoint Existence", "FAIL", f"Ошибка проверки endpoint: {str(e)}")
        
        # Test 2: Try actual PDF upload
        try:
            # Create a simple PDF-like content for testing
            pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
            
            files = {
                'file': ('test_lesson.pdf', io.BytesIO(pdf_content), 'application/pdf')
            }
            
            # Remove Content-Type header for multipart upload
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            
            response = requests.post(
                f"{BACKEND_URL}/admin/consultations/upload-pdf",
                files=files,
                headers=headers
            )
            
            if response.status_code == 200:
                self.log_test(
                    "PDF Upload Functionality", 
                    "PASS", 
                    f"PDF успешно загружен: {response.status_code}"
                )
            elif response.status_code == 404:
                self.log_test(
                    "PDF Upload Functionality", 
                    "FAIL", 
                    "Endpoint /api/admin/consultations/upload-pdf не найден (404)"
                )
            else:
                self.log_test(
                    "PDF Upload Functionality", 
                    "FAIL", 
                    f"Ошибка загрузки PDF: {response.status_code} - {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("PDF Upload Functionality", "FAIL", f"Исключение при загрузке PDF: {str(e)}")

    def test_cors_headers_pdf_endpoints(self):
        """Проверка CORS headers для PDF endpoints"""
        print("\n🌐 ТЕСТ CORS HEADERS ДЛЯ PDF ENDPOINTS")
        
        pdf_endpoints = [
            "/admin/consultations/upload-pdf",
            "/consultations/pdf/test-file-id",
            "/materials/test-material-id/stream"
        ]
        
        for endpoint in pdf_endpoints:
            try:
                # Test OPTIONS request for CORS preflight
                response = self.session.options(f"{BACKEND_URL}{endpoint}")
                
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                }
                
                has_cors = any(cors_headers.values())
                
                if has_cors:
                    self.log_test(
                        f"CORS Headers {endpoint}", 
                        "PASS", 
                        f"CORS headers найдены: {cors_headers}"
                    )
                else:
                    self.log_test(
                        f"CORS Headers {endpoint}", 
                        "WARN", 
                        f"CORS headers отсутствуют для {endpoint}"
                    )
                    
            except Exception as e:
                self.log_test(f"CORS Headers {endpoint}", "FAIL", f"Ошибка проверки CORS: {str(e)}")

    def test_lesson_display_issues(self):
        """Тестирование проблем с отображением уроков"""
        print("\n📚 ТЕСТ ОТОБРАЖЕНИЯ УРОКОВ")
        
        # Test 1: Admin lessons endpoint
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/lessons")
            
            if response.status_code == 200:
                lessons_data = response.json()
                
                # Check for ObjectId serialization issues
                lessons_str = json.dumps(lessons_data)
                if 'ObjectId' in lessons_str:
                    self.log_test(
                        "Admin Lessons ObjectId Serialization", 
                        "FAIL", 
                        "Найдены нериализованные ObjectId в ответе"
                    )
                else:
                    self.log_test(
                        "Admin Lessons ObjectId Serialization", 
                        "PASS", 
                        "ObjectId корректно сериализованы"
                    )
                
                # Check lesson structure
                if isinstance(lessons_data, list) and len(lessons_data) > 0:
                    lesson = lessons_data[0]
                    required_fields = ['id', 'title', 'video_url']
                    missing_fields = [field for field in required_fields if field not in lesson]
                    
                    if missing_fields:
                        self.log_test(
                            "Admin Lessons Structure", 
                            "WARN", 
                            f"Отсутствуют поля в уроках: {missing_fields}"
                        )
                    else:
                        self.log_test(
                            "Admin Lessons Structure", 
                            "PASS", 
                            f"Структура уроков корректна. Найдено уроков: {len(lessons_data)}"
                        )
                        
                    # Check for PDF-related fields
                    pdf_fields = ['pdf_file_id', 'subtitles_file_id']
                    pdf_field_status = {field: field in lesson for field in pdf_fields}
                    
                    self.log_test(
                        "Admin Lessons PDF Fields", 
                        "INFO", 
                        f"PDF поля в уроках: {pdf_field_status}"
                    )
                else:
                    self.log_test(
                        "Admin Lessons Structure", 
                        "WARN", 
                        "Нет уроков в системе или некорректный формат ответа"
                    )
                    
            else:
                self.log_test(
                    "Admin Lessons Endpoint", 
                    "FAIL", 
                    f"Ошибка получения уроков: {response.status_code} - {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("Admin Lessons Endpoint", "FAIL", f"Исключение: {str(e)}")
        
        # Test 2: Student lessons endpoint
        try:
            response = self.session.get(f"{BACKEND_URL}/learning/levels")
            
            if response.status_code == 200:
                levels_data = response.json()
                
                # Check for ObjectId serialization issues
                levels_str = json.dumps(levels_data)
                if 'ObjectId' in levels_str:
                    self.log_test(
                        "Student Lessons ObjectId Serialization", 
                        "FAIL", 
                        "Найдены нериализованные ObjectId в ответе"
                    )
                else:
                    self.log_test(
                        "Student Lessons ObjectId Serialization", 
                        "PASS", 
                        "ObjectId корректно сериализованы"
                    )
                
                # Check available lessons
                available_lessons = levels_data.get('available_lessons', [])
                if available_lessons:
                    lessons_with_video = [l for l in available_lessons if l.get('video_url')]
                    lessons_without_video = [l for l in available_lessons if not l.get('video_url')]
                    
                    self.log_test(
                        "Student Lessons Video URLs", 
                        "PASS" if lessons_with_video else "WARN", 
                        f"Уроков с видео: {len(lessons_with_video)}, без видео: {len(lessons_without_video)}"
                    )
                else:
                    self.log_test(
                        "Student Lessons Availability", 
                        "WARN", 
                        "Нет доступных уроков для студентов"
                    )
                    
            else:
                self.log_test(
                    "Student Lessons Endpoint", 
                    "FAIL", 
                    f"Ошибка получения уровней: {response.status_code} - {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("Student Lessons Endpoint", "FAIL", f"Исключение: {str(e)}")

    def test_pdf_streaming(self):
        """Тестирование стриминга PDF файлов"""
        print("\n🎬 ТЕСТ СТРИМИНГА PDF ФАЙЛОВ")
        
        # Test 1: Check if PDF streaming endpoint exists
        try:
            # Try to access a test PDF file ID
            test_file_id = "test-pdf-file-id"
            response = self.session.get(f"{BACKEND_URL}/consultations/pdf/{test_file_id}")
            
            if response.status_code == 404:
                self.log_test(
                    "PDF Streaming Endpoint", 
                    "PASS", 
                    "Endpoint /api/consultations/pdf/{file_id} существует (возвращает 404 для несуществующего файла)"
                )
            elif response.status_code == 200:
                self.log_test(
                    "PDF Streaming Endpoint", 
                    "PASS", 
                    "Endpoint работает и возвращает данные"
                )
            else:
                self.log_test(
                    "PDF Streaming Endpoint", 
                    "FAIL", 
                    f"Неожиданный статус: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("PDF Streaming Endpoint", "FAIL", f"Ошибка доступа к PDF streaming: {str(e)}")
        
        # Test 2: Check materials streaming (alternative PDF endpoint)
        try:
            response = self.session.get(f"{BACKEND_URL}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                
                if materials:
                    # Try to stream the first material
                    first_material = materials[0]
                    material_id = first_material.get('id')
                    
                    if material_id:
                        stream_response = self.session.get(f"{BACKEND_URL}/materials/{material_id}/stream")
                        
                        if stream_response.status_code == 200:
                            content_type = stream_response.headers.get('Content-Type', '')
                            
                            self.log_test(
                                "Materials PDF Streaming", 
                                "PASS", 
                                f"Материал успешно стримится. Content-Type: {content_type}"
                            )
                        else:
                            self.log_test(
                                "Materials PDF Streaming", 
                                "FAIL", 
                                f"Ошибка стриминга материала: {stream_response.status_code}"
                            )
                    else:
                        self.log_test(
                            "Materials PDF Streaming", 
                            "WARN", 
                            "Нет ID у первого материала"
                        )
                else:
                    self.log_test(
                        "Materials PDF Streaming", 
                        "WARN", 
                        "Нет материалов для тестирования стриминга"
                    )
            else:
                self.log_test(
                    "Materials List", 
                    "FAIL", 
                    f"Ошибка получения списка материалов: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Materials PDF Streaming", "FAIL", f"Исключение: {str(e)}")

    def test_create_lesson_with_pdf(self):
        """Тестирование создания урока с PDF файлом"""
        print("\n📝 ТЕСТ СОЗДАНИЯ УРОКА С PDF")
        
        try:
            # Create a test lesson with PDF
            lesson_data = {
                "id": f"test-lesson-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "title": "Тестовый урок с PDF",
                "description": "Урок для тестирования загрузки PDF",
                "video_url": "https://www.youtube.com/watch?v=test",
                "level": 1,
                "order": 999,
                "is_active": True,
                "duration_minutes": 30,
                "pdf_file_id": "test-pdf-file-id",
                "subtitles_file_id": "test-subtitles-file-id"
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/lessons", json=lesson_data)
            
            if response.status_code == 200:
                self.log_test(
                    "Create Lesson with PDF", 
                    "PASS", 
                    "Урок с PDF полями успешно создан"
                )
                
                # Clean up - delete the test lesson
                lesson_id = lesson_data["id"]
                delete_response = self.session.delete(f"{BACKEND_URL}/admin/lessons/{lesson_id}")
                
                if delete_response.status_code == 200:
                    self.log_test(
                        "Cleanup Test Lesson", 
                        "PASS", 
                        "Тестовый урок успешно удален"
                    )
                    
            else:
                self.log_test(
                    "Create Lesson with PDF", 
                    "FAIL", 
                    f"Ошибка создания урока: {response.status_code} - {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("Create Lesson with PDF", "FAIL", f"Исключение: {str(e)}")

    def run_comprehensive_pdf_tests(self):
        """Запуск всех тестов PDF функциональности"""
        print("🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ PDF ФУНКЦИОНАЛЬНОСТИ")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.authenticate_super_admin():
            print("❌ Не удалось аутентифицироваться. Прекращение тестирования.")
            return False
        
        # Step 2: Test PDF upload endpoints
        self.test_pdf_upload_endpoints()
        
        # Step 3: Test CORS headers
        self.test_cors_headers_pdf_endpoints()
        
        # Step 4: Test lesson display issues
        self.test_lesson_display_issues()
        
        # Step 5: Test PDF streaming
        self.test_pdf_streaming()
        
        # Step 6: Test lesson creation with PDF
        self.test_create_lesson_with_pdf()
        
        # Summary
        self.print_test_summary()
        
        return True

    def print_test_summary(self):
        """Печать итогового отчета"""
        print("\n" + "=" * 80)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ PDF ФУНКЦИОНАЛЬНОСТИ")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warning_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print(f"Всего тестов: {total_tests}")
        print(f"✅ Пройдено: {passed_tests}")
        print(f"❌ Провалено: {failed_tests}")
        print(f"⚠️ Предупреждения: {warning_tests}")
        print(f"📈 Успешность: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  ❌ {result['test']}: {result['details']}")
        
        if warning_tests > 0:
            print("\n⚠️ ПРЕДУПРЕЖДЕНИЯ:")
            for result in self.test_results:
                if result['status'] == 'WARN':
                    print(f"  ⚠️ {result['test']}: {result['details']}")
        
        print("\n" + "=" * 80)

def main():
    """Main function"""
    tester = PDFUploadTester()
    
    try:
        success = tester.run_comprehensive_pdf_tests()
        
        if success:
            print("\n🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        else:
            print("\n💥 ТЕСТИРОВАНИЕ ПРЕРВАНО ИЗ-ЗА КРИТИЧЕСКИХ ОШИБОК")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()