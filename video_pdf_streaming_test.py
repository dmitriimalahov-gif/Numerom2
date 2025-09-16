#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Полная диагностика проблемы с загрузкой и отображением видео/PDF файлов для студентов

ПРОБЛЕМА: Студенты не могут просматривать видео и PDF файлы в лекциях и дополнительных материалах

ЗАДАЧА: Найти и исправить все проблемы в цепочке загрузки → хранения → отображения файлов

ENDPOINTS ДЛЯ ДЕТАЛЬНОГО ТЕСТИРОВАНИЯ:
1. GET /api/video/{video_id} - стриминг видео файлов
2. GET /api/materials/{material_id}/stream - стриминг материалов (PDF)
3. GET /api/lessons - получение уроков с video_url
4. GET /api/materials - получение материалов
5. POST /api/learning/lesson/{id}/start - начало урока
6. Проверка путей к файлам и их существования
"""

import requests
import json
import re
from datetime import datetime
import sys
import os
from pathlib import Path

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
TEST_ADMIN_PASSWORD = "756bvy67H"

# Test student credentials (will create if needed)
TEST_STUDENT_EMAIL = "student.test@example.com"
TEST_STUDENT_PASSWORD = "testpass123"

class VideoStreamingTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.student_token = None
        self.admin_data = None
        self.student_data = None
        self.test_results = []
        self.available_videos = []
        self.available_materials = []
        self.available_lessons = []
        
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
        """1. АУТЕНТИФИКАЦИЯ АДМИНИСТРАТОРА"""
        print("\n🔐 ТЕСТ 1: АУТЕНТИФИКАЦИЯ АДМИНИСТРАТОРА")
        
        try:
            login_data = {
                "email": TEST_ADMIN_EMAIL,
                "password": TEST_ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('access_token')
                self.admin_data = data.get('user')
                
                if self.admin_token and self.admin_data:
                    details = f"Admin ID: {self.admin_data.get('id')}, Credits: {self.admin_data.get('credits_remaining')}"
                    self.log_test("Аутентификация администратора", "PASS", details)
                    return True
                else:
                    self.log_test("Аутентификация администратора", "FAIL", "Отсутствует токен или данные")
                    return False
            else:
                self.log_test("Аутентификация администратора", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Аутентификация администратора", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def create_test_student(self):
        """2. СОЗДАНИЕ ТЕСТОВОГО СТУДЕНТА"""
        print("\n👤 ТЕСТ 2: СОЗДАНИЕ ТЕСТОВОГО СТУДЕНТА")
        
        try:
            # Try to login first
            login_data = {
                "email": TEST_STUDENT_EMAIL,
                "password": TEST_STUDENT_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.student_token = data.get('access_token')
                self.student_data = data.get('user')
                self.log_test("Логин существующего студента", "PASS", f"Student ID: {self.student_data.get('id')}")
                return True
            
            # If login failed, try to register
            register_data = {
                "email": TEST_STUDENT_EMAIL,
                "password": TEST_STUDENT_PASSWORD,
                "full_name": "Test Student",
                "birth_date": "15.03.1990",
                "city": "Москва",
                "phone_number": "+7900123456"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=register_data)
            
            if response.status_code == 200:
                data = response.json()
                self.student_token = data.get('access_token')
                self.student_data = data.get('user')
                self.log_test("Регистрация нового студента", "PASS", f"Student ID: {self.student_data.get('id')}")
                return True
            else:
                self.log_test("Создание тестового студента", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Создание тестового студента", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def test_admin_lessons_endpoint(self):
        """3. ТЕСТИРОВАНИЕ ADMIN LESSONS ENDPOINT"""
        print("\n📚 ТЕСТ 3: ПОЛУЧЕНИЕ УРОКОВ ЧЕРЕЗ ADMIN API")
        
        try:
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            response = self.session.get(f"{BACKEND_URL}/admin/lessons", headers=headers)
            
            if response.status_code == 200:
                lessons = response.json()
                self.available_lessons = lessons
                
                if isinstance(lessons, list) and len(lessons) > 0:
                    # Check for video URLs in lessons
                    video_lessons = [lesson for lesson in lessons if lesson.get('video_url')]
                    
                    details = f"Найдено {len(lessons)} уроков, {len(video_lessons)} с видео"
                    self.log_test("Получение списка уроков", "PASS", details)
                    
                    # Log some lesson details
                    for i, lesson in enumerate(lessons[:3]):  # First 3 lessons
                        video_url = lesson.get('video_url', 'Нет видео')
                        title = lesson.get('title', 'Без названия')
                        lesson_id = lesson.get('id', 'Нет ID')
                        print(f"   Урок {i+1}: {title} (ID: {lesson_id}) - Видео: {video_url}")
                    
                    return True
                else:
                    self.log_test("Получение списка уроков", "FAIL", "Список уроков пуст")
                    return False
            else:
                self.log_test("Получение списка уроков", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Получение списка уроков", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def test_materials_endpoint(self):
        """4. ТЕСТИРОВАНИЕ MATERIALS ENDPOINT"""
        print("\n📄 ТЕСТ 4: ПОЛУЧЕНИЕ МАТЕРИАЛОВ")
        
        try:
            headers = {'Authorization': f'Bearer {self.student_token}'}
            response = self.session.get(f"{BACKEND_URL}/materials", headers=headers)
            
            if response.status_code == 200:
                materials = response.json()
                self.available_materials = materials
                
                if isinstance(materials, list):
                    pdf_materials = [mat for mat in materials if mat.get('material_type') == 'pdf']
                    
                    details = f"Найдено {len(materials)} материалов, {len(pdf_materials)} PDF"
                    self.log_test("Получение списка материалов", "PASS", details)
                    
                    # Log some material details
                    for i, material in enumerate(materials[:3]):  # First 3 materials
                        title = material.get('title', 'Без названия')
                        material_id = material.get('id', 'Нет ID')
                        material_type = material.get('material_type', 'Неизвестно')
                        file_url = material.get('file_url', 'Нет URL')
                        print(f"   Материал {i+1}: {title} (ID: {material_id}) - Тип: {material_type} - URL: {file_url}")
                    
                    return True
                else:
                    self.log_test("Получение списка материалов", "WARN", "Список материалов пуст")
                    return True  # Empty list is OK
            else:
                self.log_test("Получение списка материалов", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Получение списка материалов", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    def test_video_streaming_endpoints(self):
        """5. ТЕСТИРОВАНИЕ VIDEO STREAMING ENDPOINTS"""
        print("\n🎥 ТЕСТ 5: ТЕСТИРОВАНИЕ СТРИМИНГА ВИДЕО")
        
        # First, get uploaded videos from admin
        try:
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            
            # Check if there are any uploaded videos in the database
            # We'll try to find video IDs from lessons or try some test IDs
            video_ids_to_test = []
            
            # Extract video IDs from lessons
            for lesson in self.available_lessons:
                video_url = lesson.get('video_url', '')
                if '/api/video/' in video_url:
                    video_id = video_url.split('/api/video/')[-1]
                    video_ids_to_test.append(video_id)
            
            # If no video IDs found, try some common test patterns
            if not video_ids_to_test:
                # Try to create a test video first
                self.log_test("Поиск видео ID", "WARN", "Видео ID не найдены в уроках, попробуем создать тестовое видео")
                video_ids_to_test = ['test-video-id']  # Will likely fail, but we'll test the endpoint
            
            for video_id in video_ids_to_test[:3]:  # Test first 3 videos
                try:
                    # Test video streaming endpoint WITHOUT authentication first (as student would)
                    response = self.session.get(f"{BACKEND_URL}/video/{video_id}")
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '')
                        content_length = response.headers.get('content-length', '0')
                        
                        if 'video/' in content_type:
                            details = f"Video ID: {video_id}, Content-Type: {content_type}, Size: {content_length} bytes"
                            self.log_test(f"Стриминг видео {video_id}", "PASS", details)
                        else:
                            self.log_test(f"Стриминг видео {video_id}", "FAIL", f"Неверный Content-Type: {content_type}")
                    
                    elif response.status_code == 404:
                        self.log_test(f"Стриминг видео {video_id}", "FAIL", "Видео файл не найден (404)")
                    
                    elif response.status_code == 401:
                        # Try with student authentication
                        headers_student = {'Authorization': f'Bearer {self.student_token}'}
                        response = self.session.get(f"{BACKEND_URL}/video/{video_id}", headers=headers_student)
                        
                        if response.status_code == 200:
                            content_type = response.headers.get('content-type', '')
                            details = f"Video ID: {video_id}, Content-Type: {content_type} (требует аутентификации)"
                            self.log_test(f"Стриминг видео {video_id} (с аутентификацией)", "PASS", details)
                        else:
                            self.log_test(f"Стриминг видео {video_id}", "FAIL", f"HTTP {response.status_code} даже с аутентификацией")
                    
                    else:
                        self.log_test(f"Стриминг видео {video_id}", "FAIL", f"HTTP {response.status_code}: {response.text[:200]}")
                
                except Exception as e:
                    self.log_test(f"Стриминг видео {video_id}", "FAIL", f"Ошибка: {str(e)}")
            
            if not video_ids_to_test:
                self.log_test("Тестирование стриминга видео", "SKIP", "Нет доступных видео для тестирования")
                
        except Exception as e:
            self.log_test("Тестирование стриминга видео", "FAIL", f"Ошибка: {str(e)}")
    
    def test_pdf_streaming_endpoints(self):
        """6. ТЕСТИРОВАНИЕ PDF STREAMING ENDPOINTS"""
        print("\n📄 ТЕСТ 6: ТЕСТИРОВАНИЕ СТРИМИНГА PDF")
        
        try:
            if not self.available_materials:
                self.log_test("Тестирование стриминга PDF", "SKIP", "Нет доступных материалов для тестирования")
                return
            
            for material in self.available_materials[:3]:  # Test first 3 materials
                material_id = material.get('id')
                if not material_id:
                    continue
                
                try:
                    # Test PDF streaming as student
                    headers = {'Authorization': f'Bearer {self.student_token}'}
                    response = self.session.get(f"{BACKEND_URL}/materials/{material_id}/stream", headers=headers)
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '')
                        content_length = response.headers.get('content-length', '0')
                        
                        if 'application/pdf' in content_type:
                            details = f"Material ID: {material_id}, Content-Type: {content_type}, Size: {content_length} bytes"
                            self.log_test(f"Стриминг PDF {material_id}", "PASS", details)
                        else:
                            self.log_test(f"Стриминг PDF {material_id}", "FAIL", f"Неверный Content-Type: {content_type}")
                    
                    elif response.status_code == 404:
                        self.log_test(f"Стриминг PDF {material_id}", "FAIL", "PDF файл не найден (404)")
                    
                    elif response.status_code == 402:
                        self.log_test(f"Стриминг PDF {material_id}", "WARN", "Недостаточно кредитов для просмотра (402)")
                    
                    elif response.status_code == 401:
                        self.log_test(f"Стриминг PDF {material_id}", "FAIL", "Требуется аутентификация (401)")
                    
                    else:
                        self.log_test(f"Стриминг PDF {material_id}", "FAIL", f"HTTP {response.status_code}: {response.text[:200]}")
                
                except Exception as e:
                    self.log_test(f"Стриминг PDF {material_id}", "FAIL", f"Ошибка: {str(e)}")
                    
        except Exception as e:
            self.log_test("Тестирование стриминга PDF", "FAIL", f"Ошибка: {str(e)}")
    
    def test_lesson_start_endpoint(self):
        """7. ТЕСТИРОВАНИЕ НАЧАЛА УРОКА"""
        print("\n🎓 ТЕСТ 7: ТЕСТИРОВАНИЕ НАЧАЛА УРОКА")
        
        try:
            if not self.available_lessons:
                self.log_test("Тестирование начала урока", "SKIP", "Нет доступных уроков")
                return
            
            # Test starting a lesson as student
            lesson = self.available_lessons[0]  # Take first lesson
            lesson_id = lesson.get('id')
            
            if not lesson_id:
                self.log_test("Тестирование начала урока", "FAIL", "Урок без ID")
                return
            
            headers = {'Authorization': f'Bearer {self.student_token}'}
            response = self.session.post(f"{BACKEND_URL}/learning/lesson/{lesson_id}/start", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                points_deducted = data.get('points_deducted', 0)
                message = data.get('message', '')
                
                details = f"Lesson ID: {lesson_id}, Points deducted: {points_deducted}, Message: {message}"
                self.log_test("Начало урока", "PASS", details)
                
            elif response.status_code == 402:
                self.log_test("Начало урока", "WARN", "Недостаточно кредитов для начала урока (402)")
                
            elif response.status_code == 404:
                self.log_test("Начало урока", "FAIL", "Урок не найден (404)")
                
            else:
                self.log_test("Начало урока", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Тестирование начала урока", "FAIL", f"Ошибка: {str(e)}")
    
    def test_cors_headers(self):
        """8. ТЕСТИРОВАНИЕ CORS HEADERS"""
        print("\n🌐 ТЕСТ 8: ТЕСТИРОВАНИЕ CORS HEADERS")
        
        try:
            # Test CORS on video endpoint
            if self.available_lessons:
                lesson = self.available_lessons[0]
                video_url = lesson.get('video_url', '')
                if '/api/video/' in video_url:
                    video_id = video_url.split('/api/video/')[-1]
                    
                    # Make OPTIONS request to check CORS
                    response = self.session.options(f"{BACKEND_URL}/video/{video_id}")
                    
                    cors_headers = {
                        'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                        'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                        'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                    }
                    
                    if any(cors_headers.values()):
                        details = f"CORS headers найдены: {cors_headers}"
                        self.log_test("CORS headers для видео", "PASS", details)
                    else:
                        self.log_test("CORS headers для видео", "WARN", "CORS headers не найдены")
            
            # Test CORS on materials endpoint
            if self.available_materials:
                material = self.available_materials[0]
                material_id = material.get('id')
                
                if material_id:
                    response = self.session.options(f"{BACKEND_URL}/materials/{material_id}/stream")
                    
                    cors_headers = {
                        'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                        'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods')
                    }
                    
                    if any(cors_headers.values()):
                        details = f"CORS headers найдены: {cors_headers}"
                        self.log_test("CORS headers для материалов", "PASS", details)
                    else:
                        self.log_test("CORS headers для материалов", "WARN", "CORS headers не найдены")
                        
        except Exception as e:
            self.log_test("Тестирование CORS headers", "FAIL", f"Ошибка: {str(e)}")
    
    def test_mobile_compatibility(self):
        """9. ТЕСТИРОВАНИЕ МОБИЛЬНОЙ СОВМЕСТИМОСТИ"""
        print("\n📱 ТЕСТ 9: ТЕСТИРОВАНИЕ МОБИЛЬНОЙ СОВМЕСТИМОСТИ")
        
        try:
            # Set mobile user agent
            mobile_headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
                'Authorization': f'Bearer {self.student_token}'
            }
            
            # Test video endpoint with mobile user agent
            if self.available_lessons:
                lesson = self.available_lessons[0]
                video_url = lesson.get('video_url', '')
                if '/api/video/' in video_url:
                    video_id = video_url.split('/api/video/')[-1]
                    
                    response = self.session.get(f"{BACKEND_URL}/video/{video_id}", headers=mobile_headers)
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'video/' in content_type:
                            self.log_test("Мобильная совместимость видео", "PASS", f"Content-Type: {content_type}")
                        else:
                            self.log_test("Мобильная совместимость видео", "FAIL", f"Неверный Content-Type: {content_type}")
                    else:
                        self.log_test("Мобильная совместимость видео", "FAIL", f"HTTP {response.status_code}")
            
            # Test PDF endpoint with mobile user agent
            if self.available_materials:
                material = self.available_materials[0]
                material_id = material.get('id')
                
                if material_id:
                    response = self.session.get(f"{BACKEND_URL}/materials/{material_id}/stream", headers=mobile_headers)
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'application/pdf' in content_type:
                            self.log_test("Мобильная совместимость PDF", "PASS", f"Content-Type: {content_type}")
                        else:
                            self.log_test("Мобильная совместимость PDF", "FAIL", f"Неверный Content-Type: {content_type}")
                    elif response.status_code == 402:
                        self.log_test("Мобильная совместимость PDF", "WARN", "Недостаточно кредитов (402)")
                    else:
                        self.log_test("Мобильная совместимость PDF", "FAIL", f"HTTP {response.status_code}")
                        
        except Exception as e:
            self.log_test("Тестирование мобильной совместимости", "FAIL", f"Ошибка: {str(e)}")
    
    def check_file_paths_existence(self):
        """10. ПРОВЕРКА СУЩЕСТВОВАНИЯ ФАЙЛОВ НА ДИСКЕ"""
        print("\n💾 ТЕСТ 10: ПРОВЕРКА СУЩЕСТВОВАНИЯ ФАЙЛОВ НА ДИСКЕ")
        
        # Note: This test can't actually check file existence on the server disk
        # But we can check if the API returns proper file not found errors
        
        try:
            # Test with non-existent video ID
            response = self.session.get(f"{BACKEND_URL}/video/non-existent-video-id")
            
            if response.status_code == 404:
                self.log_test("Обработка несуществующего видео", "PASS", "Корректно возвращает 404 для несуществующего видео")
            else:
                self.log_test("Обработка несуществующего видео", "FAIL", f"Неожиданный статус: {response.status_code}")
            
            # Test with non-existent material ID
            headers = {'Authorization': f'Bearer {self.student_token}'}
            response = self.session.get(f"{BACKEND_URL}/materials/non-existent-material-id/stream", headers=headers)
            
            if response.status_code == 404:
                self.log_test("Обработка несуществующего материала", "PASS", "Корректно возвращает 404 для несуществующего материала")
            else:
                self.log_test("Обработка несуществующего материала", "FAIL", f"Неожиданный статус: {response.status_code}")
                
        except Exception as e:
            self.log_test("Проверка существования файлов", "FAIL", f"Ошибка: {str(e)}")
    
    def generate_summary_report(self):
        """11. ГЕНЕРАЦИЯ ИТОГОВОГО ОТЧЁТА"""
        print("\n📊 ИТОГОВЫЙ ОТЧЁТ ТЕСТИРОВАНИЯ")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['status'] == 'PASS'])
        failed_tests = len([t for t in self.test_results if t['status'] == 'FAIL'])
        warning_tests = len([t for t in self.test_results if t['status'] == 'WARN'])
        skipped_tests = len([t for t in self.test_results if t['status'] == 'SKIP'])
        
        print(f"Всего тестов: {total_tests}")
        print(f"✅ Пройдено: {passed_tests}")
        print(f"❌ Провалено: {failed_tests}")
        print(f"⚠️ Предупреждения: {warning_tests}")
        print(f"⏭️ Пропущено: {skipped_tests}")
        print(f"Успешность: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n🔍 ДЕТАЛЬНЫЙ АНАЛИЗ ПРОБЛЕМ:")
        
        critical_issues = []
        for test in self.test_results:
            if test['status'] == 'FAIL':
                critical_issues.append(f"❌ {test['test']}: {test['details']}")
        
        if critical_issues:
            print("КРИТИЧЕСКИЕ ПРОБЛЕМЫ:")
            for issue in critical_issues:
                print(f"  {issue}")
        else:
            print("✅ Критических проблем не обнаружено!")
        
        warnings = []
        for test in self.test_results:
            if test['status'] == 'WARN':
                warnings.append(f"⚠️ {test['test']}: {test['details']}")
        
        if warnings:
            print("\nПРЕДУПРЕЖДЕНИЯ:")
            for warning in warnings:
                print(f"  {warning}")
        
        print("\n" + "=" * 80)
        
        return {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'warnings': warning_tests,
            'skipped': skipped_tests,
            'success_rate': (passed_tests/total_tests)*100,
            'critical_issues': critical_issues,
            'warnings': warnings
        }
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 ЗАПУСК КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ ВИДЕО/PDF СТРИМИНГА")
        print("=" * 80)
        
        # Authentication tests
        if not self.authenticate_admin():
            print("❌ Не удалось аутентифицировать администратора. Прерывание тестов.")
            return False
        
        if not self.create_test_student():
            print("❌ Не удалось создать тестового студента. Прерывание тестов.")
            return False
        
        # Data gathering tests
        self.test_admin_lessons_endpoint()
        self.test_materials_endpoint()
        
        # Core streaming tests
        self.test_video_streaming_endpoints()
        self.test_pdf_streaming_endpoints()
        self.test_lesson_start_endpoint()
        
        # Technical tests
        self.test_cors_headers()
        self.test_mobile_compatibility()
        self.check_file_paths_existence()
        
        # Generate final report
        summary = self.generate_summary_report()
        
        return summary['success_rate'] > 70  # Consider successful if >70% tests pass

def main():
    """Main function"""
    tester = VideoStreamingTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
        sys.exit(0)
    else:
        print("\n💥 ТЕСТИРОВАНИЕ ВЫЯВИЛО КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
        sys.exit(1)

if __name__ == "__main__":
    main()