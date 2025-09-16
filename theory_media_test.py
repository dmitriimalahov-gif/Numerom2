#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Theory Section Management and Media File Loading
Review Request Testing - Russian Language Admin Panel Functionality

ЦЕЛЬ ТЕСТИРОВАНИЯ:
Проверить что все критические проблемы, о которых сообщил пользователь, были исправлены.

ЗАДАЧИ ДЛЯ ТЕСТИРОВАНИЯ:
1. НОВЫЕ API ENDPOINTS ДЛЯ ТЕОРИИ
2. АУТЕНТИФИКАЦИЯ (dmitrii.malahov@gmail.com / 756bvy67H)
3. ТЕСТИРОВАНИЕ ТЕОРИИ (CRUD операции)
4. ТЕСТИРОВАНИЕ МЕДИА ФАЙЛОВ
5. ПРОВЕРКА БД
"""

import requests
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://numerology-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
TEST_EMAIL = "dmitrii.malahov@gmail.com"
TEST_PASSWORD = "756bvy67H"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_info = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error_msg=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'test': test_name,
            'status': status,
            'success': success,
            'details': details,
            'error': error_msg,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error_msg:
            print(f"   Error: {error_msg}")
        print()

    def authenticate(self):
        """Authenticate as super admin dmitrii.malahov@gmail.com"""
        print("🔐 АУТЕНТИФИКАЦИЯ СУПЕР-АДМИНА")
        print("=" * 50)
        
        try:
            login_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.user_info = data.get('user', {})
                
                # Set authorization header for future requests
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}',
                    'Content-Type': 'application/json'
                })
                
                is_super_admin = self.user_info.get('is_super_admin', False)
                credits = self.user_info.get('credits_remaining', 0)
                
                self.log_test(
                    "Аутентификация супер-админа",
                    True,
                    f"Email: {TEST_EMAIL}, Super Admin: {is_super_admin}, Credits: {credits}"
                )
                return True
            else:
                self.log_test(
                    "Аутентификация супер-админа", 
                    False, 
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Аутентификация супер-админа", False, "", str(e))
            return False

    def test_theory_sections_crud(self):
        """Test CRUD operations for theory sections"""
        print("📚 ТЕСТИРОВАНИЕ УПРАВЛЕНИЯ РАЗДЕЛАМИ ТЕОРИИ")
        print("=" * 50)
        
        # 1. GET /api/admin/theory-sections - получение списка
        try:
            response = self.session.get(f"{API_BASE}/admin/theory-sections")
            if response.status_code == 200:
                data = response.json()
                sections = data.get('theory_sections', [])
                count = data.get('count', 0)
                self.log_test(
                    "GET /api/admin/theory-sections",
                    True,
                    f"Получено {count} разделов теории"
                )
            else:
                self.log_test(
                    "GET /api/admin/theory-sections",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
        except Exception as e:
            self.log_test("GET /api/admin/theory-sections", False, "", str(e))
            return False

        # 2. POST /api/admin/add-theory-section - создание нового раздела
        test_section_data = {
            "title": "Тестовый раздел теории",
            "content": "Это тестовое содержание раздела теории для проверки функциональности CRUD операций.",
            "lesson_id": "lesson_numerom_intro"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/admin/add-theory-section", json=test_section_data)
            if response.status_code == 200:
                data = response.json()
                section_id = data.get('section_id')
                success = data.get('success', False)
                
                if success and section_id:
                    self.test_section_id = section_id  # Save for later tests
                    self.log_test(
                        "POST /api/admin/add-theory-section",
                        True,
                        f"Создан раздел с ID: {section_id}"
                    )
                else:
                    self.log_test(
                        "POST /api/admin/add-theory-section",
                        False,
                        "Не получен section_id или success=False",
                        str(data)
                    )
                    return False
            else:
                self.log_test(
                    "POST /api/admin/add-theory-section",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
        except Exception as e:
            self.log_test("POST /api/admin/add-theory-section", False, "", str(e))
            return False

        # 3. POST /api/admin/update-theory-section - обновление раздела
        update_data = {
            "section_id": self.test_section_id,
            "title": "Обновленный тестовый раздел теории",
            "content": "Это обновленное содержание раздела теории после редактирования."
        }
        
        try:
            response = self.session.post(f"{API_BASE}/admin/update-theory-section", json=update_data)
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                
                if success:
                    self.log_test(
                        "POST /api/admin/update-theory-section",
                        True,
                        f"Обновлен раздел с ID: {self.test_section_id}"
                    )
                else:
                    self.log_test(
                        "POST /api/admin/update-theory-section",
                        False,
                        "success=False в ответе",
                        str(data)
                    )
                    return False
            else:
                self.log_test(
                    "POST /api/admin/update-theory-section",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
        except Exception as e:
            self.log_test("POST /api/admin/update-theory-section", False, "", str(e))
            return False

        # 4. Проверяем что раздел сохранился в коллекции lesson_theory_sections
        try:
            response = self.session.get(f"{API_BASE}/admin/theory-sections")
            if response.status_code == 200:
                data = response.json()
                sections = data.get('theory_sections', [])
                
                # Ищем наш тестовый раздел
                found_section = None
                for section in sections:
                    if section.get('id') == self.test_section_id:
                        found_section = section
                        break
                
                if found_section:
                    self.log_test(
                        "Проверка сохранения в lesson_theory_sections",
                        True,
                        f"Раздел найден: '{found_section.get('title')}'"
                    )
                else:
                    self.log_test(
                        "Проверка сохранения в lesson_theory_sections",
                        False,
                        f"Раздел с ID {self.test_section_id} не найден",
                        f"Всего разделов: {len(sections)}"
                    )
                    return False
            else:
                self.log_test(
                    "Проверка сохранения в lesson_theory_sections",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
        except Exception as e:
            self.log_test("Проверка сохранения в lesson_theory_sections", False, "", str(e))
            return False

        # 5. DELETE /api/admin/delete-theory-section/{id} - удаление раздела
        try:
            response = self.session.delete(f"{API_BASE}/admin/delete-theory-section/{self.test_section_id}")
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                
                if success:
                    self.log_test(
                        "DELETE /api/admin/delete-theory-section",
                        True,
                        f"Удален раздел с ID: {self.test_section_id}"
                    )
                else:
                    self.log_test(
                        "DELETE /api/admin/delete-theory-section",
                        False,
                        "success=False в ответе",
                        str(data)
                    )
                    return False
            else:
                self.log_test(
                    "DELETE /api/admin/delete-theory-section",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
        except Exception as e:
            self.log_test("DELETE /api/admin/delete-theory-section", False, "", str(e))
            return False

        # 6. Проверяем что раздел удален из БД
        try:
            response = self.session.get(f"{API_BASE}/admin/theory-sections")
            if response.status_code == 200:
                data = response.json()
                sections = data.get('theory_sections', [])
                
                # Проверяем что наш раздел больше не существует
                found_section = None
                for section in sections:
                    if section.get('id') == self.test_section_id:
                        found_section = section
                        break
                
                if not found_section:
                    self.log_test(
                        "Проверка удаления из lesson_theory_sections",
                        True,
                        f"Раздел с ID {self.test_section_id} успешно удален из БД"
                    )
                else:
                    self.log_test(
                        "Проверка удаления из lesson_theory_sections",
                        False,
                        f"Раздел с ID {self.test_section_id} все еще существует",
                        f"Title: {found_section.get('title')}"
                    )
                    return False
            else:
                self.log_test(
                    "Проверка удаления из lesson_theory_sections",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
        except Exception as e:
            self.log_test("Проверка удаления из lesson_theory_sections", False, "", str(e))
            return False

        return True

    def test_media_files(self):
        """Test media file endpoints"""
        print("🎬 ТЕСТИРОВАНИЕ МЕДИА ФАЙЛОВ")
        print("=" * 50)
        
        # Test lesson IDs from review request
        lesson_ids = ["lesson_numerom_intro"]
        
        for lesson_id in lesson_ids:
            # 1. GET /api/lessons/{lesson_id}/additional-pdfs
            try:
                response = self.session.get(f"{API_BASE}/lessons/{lesson_id}/additional-pdfs")
                if response.status_code == 200:
                    data = response.json()
                    pdfs = data.get('additional_pdfs', [])
                    count = data.get('count', 0)
                    
                    self.log_test(
                        f"GET /api/lessons/{lesson_id}/additional-pdfs",
                        True,
                        f"Найдено {count} PDF файлов для урока {lesson_id}"
                    )
                    
                    # Показываем детали найденных PDF
                    if pdfs:
                        for i, pdf in enumerate(pdfs[:3]):  # Показываем первые 3
                            print(f"   PDF {i+1}: {pdf.get('filename')} - {pdf.get('title')}")
                    
                else:
                    self.log_test(
                        f"GET /api/lessons/{lesson_id}/additional-pdfs",
                        False,
                        f"Status: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_test(f"GET /api/lessons/{lesson_id}/additional-pdfs", False, "", str(e))

            # 2. GET /api/lessons/{lesson_id}/additional-videos
            try:
                response = self.session.get(f"{API_BASE}/lessons/{lesson_id}/additional-videos")
                if response.status_code == 200:
                    data = response.json()
                    videos = data.get('additional_videos', [])
                    count = data.get('count', 0)
                    
                    self.log_test(
                        f"GET /api/lessons/{lesson_id}/additional-videos",
                        True,
                        f"Найдено {count} видео файлов для урока {lesson_id}"
                    )
                    
                    # Показываем детали найденных видео
                    if videos:
                        for i, video in enumerate(videos[:3]):  # Показываем первые 3
                            print(f"   Video {i+1}: {video.get('filename')} - {video.get('title')}")
                    
                else:
                    self.log_test(
                        f"GET /api/lessons/{lesson_id}/additional-videos",
                        False,
                        f"Status: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_test(f"GET /api/lessons/{lesson_id}/additional-videos", False, "", str(e))

        # Test with fallback lesson_id if main doesn't work
        fallback_lesson_ids = ["lesson_basic", "default_lesson", "intro_lesson"]
        
        print("\n🔄 ТЕСТИРОВАНИЕ С FALLBACK LESSON IDS")
        for fallback_id in fallback_lesson_ids:
            try:
                response = self.session.get(f"{API_BASE}/lessons/{fallback_id}/additional-pdfs")
                if response.status_code == 200:
                    data = response.json()
                    count = data.get('count', 0)
                    if count > 0:
                        self.log_test(
                            f"Fallback test - {fallback_id} PDFs",
                            True,
                            f"Найдено {count} PDF файлов для fallback урока {fallback_id}"
                        )
                        break
            except Exception as e:
                continue

        return True

    def test_database_verification(self):
        """Verify database collections and operations"""
        print("🗄️ ПРОВЕРКА БАЗЫ ДАННЫХ")
        print("=" * 50)
        
        # Test that we can create and verify lesson_theory_sections collection
        test_section_data = {
            "title": "DB Verification Test Section",
            "content": "Test content for database verification",
            "lesson_id": "lesson_numerom_intro"
        }
        
        try:
            # Create a test section
            response = self.session.post(f"{API_BASE}/admin/add-theory-section", json=test_section_data)
            if response.status_code == 200:
                data = response.json()
                section_id = data.get('section_id')
                
                if section_id:
                    # Verify it exists
                    response = self.session.get(f"{API_BASE}/admin/theory-sections")
                    if response.status_code == 200:
                        data = response.json()
                        sections = data.get('theory_sections', [])
                        
                        found = any(s.get('id') == section_id for s in sections)
                        if found:
                            self.log_test(
                                "Проверка коллекции lesson_theory_sections",
                                True,
                                "Коллекция создается и CRUD операции работают с MongoDB"
                            )
                            
                            # Clean up - delete the test section
                            self.session.delete(f"{API_BASE}/admin/delete-theory-section/{section_id}")
                        else:
                            self.log_test(
                                "Проверка коллекции lesson_theory_sections",
                                False,
                                "Созданный раздел не найден в коллекции"
                            )
                    else:
                        self.log_test(
                            "Проверка коллекции lesson_theory_sections",
                            False,
                            f"Не удалось получить список разделов: {response.status_code}"
                        )
                else:
                    self.log_test(
                        "Проверка коллекции lesson_theory_sections",
                        False,
                        "Не получен section_id при создании"
                    )
            else:
                self.log_test(
                    "Проверка коллекции lesson_theory_sections",
                    False,
                    f"Не удалось создать тестовый раздел: {response.status_code}"
                )
        except Exception as e:
            self.log_test("Проверка коллекции lesson_theory_sections", False, "", str(e))

        # Check uploaded_files collection contains media files
        try:
            # We can't directly query the database, but we can check through the API
            response = self.session.get(f"{API_BASE}/lessons/lesson_numerom_intro/additional-pdfs")
            pdf_count = 0
            if response.status_code == 200:
                data = response.json()
                pdf_count = data.get('count', 0)
            
            response = self.session.get(f"{API_BASE}/lessons/lesson_numerom_intro/additional-videos")
            video_count = 0
            if response.status_code == 200:
                data = response.json()
                video_count = data.get('count', 0)
            
            total_media = pdf_count + video_count
            
            self.log_test(
                "Проверка uploaded_files содержит медиа файлы",
                total_media > 0,
                f"Найдено {pdf_count} PDF и {video_count} видео файлов в uploaded_files"
            )
            
        except Exception as e:
            self.log_test("Проверка uploaded_files содержит медиа файлы", False, "", str(e))

        return True

    def test_error_scenarios(self):
        """Test error handling scenarios"""
        print("⚠️ ТЕСТИРОВАНИЕ ОБРАБОТКИ ОШИБОК")
        print("=" * 50)
        
        # Test invalid section ID for update
        try:
            invalid_update = {
                "section_id": "invalid_id_123",
                "title": "Test",
                "content": "Test content"
            }
            response = self.session.post(f"{API_BASE}/admin/update-theory-section", json=invalid_update)
            
            if response.status_code == 400:
                self.log_test(
                    "Обработка неверного ID раздела при обновлении",
                    True,
                    "Корректно возвращается 400 Bad Request для неверного ID"
                )
            else:
                self.log_test(
                    "Обработка неверного ID раздела при обновлении",
                    False,
                    f"Ожидался статус 400, получен {response.status_code}"
                )
        except Exception as e:
            self.log_test("Обработка неверного ID раздела при обновлении", False, "", str(e))

        # Test delete non-existent section
        try:
            response = self.session.delete(f"{API_BASE}/admin/delete-theory-section/nonexistent123")
            
            if response.status_code in [400, 404]:
                self.log_test(
                    "Обработка удаления несуществующего раздела",
                    True,
                    f"Корректно возвращается статус {response.status_code} для несуществующего раздела"
                )
            else:
                self.log_test(
                    "Обработка удаления несуществующего раздела",
                    False,
                    f"Ожидался статус 400/404, получен {response.status_code}"
                )
        except Exception as e:
            self.log_test("Обработка удаления несуществующего раздела", False, "", str(e))

        # Test missing required fields
        try:
            incomplete_data = {
                "title": "",  # Empty title
                "content": "Some content"
            }
            response = self.session.post(f"{API_BASE}/admin/add-theory-section", json=incomplete_data)
            
            if response.status_code == 400:
                self.log_test(
                    "Обработка пустых обязательных полей",
                    True,
                    "Корректно возвращается 400 Bad Request для пустого title"
                )
            else:
                self.log_test(
                    "Обработка пустых обязательных полей",
                    False,
                    f"Ожидался статус 400, получен {response.status_code}"
                )
        except Exception as e:
            self.log_test("Обработка пустых обязательных полей", False, "", str(e))

        return True

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ BACKEND API")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 70)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось аутентифицироваться")
            return False
        
        # Step 2: Theory Sections CRUD Testing
        self.test_theory_sections_crud()
        
        # Step 3: Media Files Testing
        self.test_media_files()
        
        # Step 4: Database Verification
        self.test_database_verification()
        
        # Step 5: Error Scenarios
        self.test_error_scenarios()
        
        # Summary
        self.print_summary()
        
        return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Всего тестов: {total_tests}")
        print(f"Пройдено: {passed_tests} ✅")
        print(f"Провалено: {failed_tests} ❌")
        print(f"Успешность: {success_rate:.1f}%")
        print()
        
        # Show failed tests
        if failed_tests > 0:
            print("❌ ПРОВАЛИВШИЕСЯ ТЕСТЫ:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}")
                    if result['error']:
                        print(f"     Ошибка: {result['error']}")
            print()
        
        # Overall assessment
        if success_rate >= 90:
            print("🎉 ОТЛИЧНЫЙ РЕЗУЛЬТАТ: Все основные функции работают корректно!")
        elif success_rate >= 75:
            print("✅ ХОРОШИЙ РЕЗУЛЬТАТ: Большинство функций работает, есть минорные проблемы")
        elif success_rate >= 50:
            print("⚠️ СРЕДНИЙ РЕЗУЛЬТАТ: Основные функции работают, но есть серьезные проблемы")
        else:
            print("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ: Многие функции не работают корректно")
        
        print("=" * 70)

def main():
    """Main test execution"""
    tester = BackendTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()