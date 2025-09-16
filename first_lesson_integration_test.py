#!/usr/bin/env python3
"""
First Lesson Integration Test Suite
Testing the enhanced lesson management system with first lesson integration.

REVIEW REQUEST TESTING:
1. POST /api/admin/lessons/sync-first-lesson - синхронизация первого урока с системой
2. GET /api/admin/lessons (ОБНОВЛЕННЫЙ) - теперь автоматически включает первый урок из lesson_system

AUTHENTICATION:
- Email: dmitrii.malahov@gmail.com
- Password: 756bvy67H  
- Status: super admin

TEST SCENARIOS:
1. Проверка синхронизации первого урока
2. Проверка объединенного списка уроков
3. Проверка защиты от дублирования
4. Тестирование сортировки
5. Проверка редактирования первого урока
"""

import requests
import json
import os
import tempfile
from pathlib import Path
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_EMAIL = "dmitrii.malahov@gmail.com"
TEST_PASSWORD = "756bvy67H"

class FirstLessonIntegrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_lesson_id = None
        
    def log(self, message):
        print(f"[TEST] {message}")
        
    def authenticate(self):
        """Authenticate as super admin"""
        self.log("🔐 Authenticating as super admin...")
        
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data["access_token"]
            self.user_id = data["user"]["id"]
            self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            self.log(f"✅ Authentication successful! User ID: {self.user_id}")
            self.log(f"✅ User credits: {data['user'].get('credits_remaining', 'N/A')}")
            self.log(f"✅ Super admin status: {data['user'].get('is_super_admin', False)}")
            return True
        else:
            self.log(f"❌ Authentication failed: {response.status_code} - {response.text}")
            return False
    
    def test_sync_first_lesson(self):
        """Test 1: Проверка синхронизации первого урока"""
        self.log("\n🧪 TEST 1: Синхронизация первого урока")
        
        try:
            # Синхронизируем первый урок
            response = self.session.post(f"{BACKEND_URL}/admin/lessons/sync-first-lesson")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Sync response: {data}")
                
                # Проверяем что урок создался или уже существует
                if data.get('success') and data.get('action') in ['created', 'already_exists']:
                    self.log(f"✅ First lesson sync successful: {data.get('message')}")
                    
                    # Проверяем что урок имеет правильный ID
                    if data.get('action') == 'created':
                        self.log("✅ First lesson was created in custom_lessons collection")
                    else:
                        self.log("✅ First lesson already exists in system")
                    
                    return True
                else:
                    self.log(f"❌ Unexpected sync response: {data}")
                    return False
            else:
                self.log(f"❌ Sync failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Sync test error: {str(e)}")
            return False
    
    def test_combined_lessons_list(self):
        """Test 2: Проверка объединенного списка уроков"""
        self.log("\n🧪 TEST 2: Объединенный список уроков")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/lessons")
            
            if response.status_code == 200:
                data = response.json()
                lessons = data.get('lessons', [])
                total_count = data.get('total_count', 0)
                
                self.log(f"✅ Retrieved {total_count} lessons")
                
                # Проверяем что первый урок присутствует в списке
                first_lesson = None
                for lesson in lessons:
                    if lesson.get('id') == 'lesson_numerom_intro':
                        first_lesson = lesson
                        break
                
                if first_lesson:
                    self.log("✅ First lesson found in combined list")
                    self.log(f"✅ First lesson title: {first_lesson.get('title')}")
                    self.log(f"✅ First lesson source: {first_lesson.get('source')}")
                    
                    # Проверяем что первый урок действительно первый в списке
                    if lessons[0].get('id') == 'lesson_numerom_intro':
                        self.log("✅ First lesson is correctly positioned first in the list")
                    else:
                        self.log(f"⚠️  First lesson is not first in list. First lesson ID: {lessons[0].get('id')}")
                    
                    # Проверяем наличие поля source для всех уроков
                    all_have_source = all(lesson.get('source') for lesson in lessons)
                    if all_have_source:
                        self.log("✅ All lessons have 'source' field")
                    else:
                        self.log("⚠️  Some lessons missing 'source' field")
                    
                    return True
                else:
                    self.log("❌ First lesson not found in combined list")
                    return False
            else:
                self.log(f"❌ Failed to get lessons list: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Combined list test error: {str(e)}")
            return False
    
    def test_duplicate_protection(self):
        """Test 3: Проверка защиты от дублирования"""
        self.log("\n🧪 TEST 3: Защита от дублирования")
        
        try:
            # Повторно вызываем синхронизацию
            response = self.session.post(f"{BACKEND_URL}/admin/lessons/sync-first-lesson")
            
            if response.status_code == 200:
                data = response.json()
                
                # Должен вернуть 'already_exists'
                if data.get('action') == 'already_exists':
                    self.log("✅ Duplicate protection working - returned 'already_exists'")
                    self.log(f"✅ Message: {data.get('message')}")
                    return True
                else:
                    self.log(f"❌ Expected 'already_exists' but got: {data.get('action')}")
                    return False
            else:
                self.log(f"❌ Duplicate protection test failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Duplicate protection test error: {str(e)}")
            return False
    
    def test_sorting_with_new_lesson(self):
        """Test 4: Тестирование сортировки с новым уроком"""
        self.log("\n🧪 TEST 4: Тестирование сортировки")
        
        try:
            # Создаем тестовый урок
            test_lesson_data = {
                "id": f"test_lesson_{int(time.time())}",
                "title": "Тестовый урок для проверки сортировки",
                "module": "Тестовый модуль",
                "description": "Урок для проверки что первый урок остается первым",
                "points_required": 5,
                "is_active": True,
                "content": {
                    "theory": {
                        "what_is_topic": "Тестовая теория",
                        "main_story": "Тестовая история",
                        "key_concepts": "Тестовые концепции",
                        "practical_applications": "Тестовые применения"
                    },
                    "exercises": [],
                    "quiz": {
                        "id": "test_quiz",
                        "title": "Тестовый квиз",
                        "questions": [],
                        "correct_answers": [],
                        "explanations": []
                    }
                }
            }
            
            self.test_lesson_id = test_lesson_data["id"]
            
            # Создаем урок
            response = self.session.post(f"{BACKEND_URL}/admin/lessons/create", json=test_lesson_data)
            
            if response.status_code == 200:
                self.log("✅ Test lesson created successfully")
                
                # Получаем обновленный список уроков
                response = self.session.get(f"{BACKEND_URL}/admin/lessons")
                
                if response.status_code == 200:
                    data = response.json()
                    lessons = data.get('lessons', [])
                    
                    # Проверяем что первый урок все еще первый
                    if lessons and lessons[0].get('id') == 'lesson_numerom_intro':
                        self.log("✅ First lesson remains first after adding new lesson")
                        
                        # Проверяем что новый урок присутствует
                        test_lesson_found = any(lesson.get('id') == self.test_lesson_id for lesson in lessons)
                        if test_lesson_found:
                            self.log("✅ New test lesson found in list")
                            
                            # Проверяем source поля
                            first_lesson_source = lessons[0].get('source')
                            self.log(f"✅ First lesson source: {first_lesson_source}")
                            
                            return True
                        else:
                            self.log("❌ New test lesson not found in list")
                            return False
                    else:
                        self.log(f"❌ First lesson is not first. Current first: {lessons[0].get('id') if lessons else 'None'}")
                        return False
                else:
                    self.log(f"❌ Failed to get updated lessons list: {response.status_code}")
                    return False
            else:
                self.log(f"❌ Failed to create test lesson: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Sorting test error: {str(e)}")
            return False
    
    def test_first_lesson_editing(self):
        """Test 5: Проверка редактирования первого урока"""
        self.log("\n🧪 TEST 5: Редактирование первого урока")
        
        try:
            # Получаем первый урок для редактирования
            response = self.session.get(f"{BACKEND_URL}/admin/lessons/lesson_numerom_intro")
            
            if response.status_code == 200:
                data = response.json()
                lesson = data.get('lesson')
                
                if lesson:
                    self.log("✅ First lesson retrieved for editing")
                    self.log(f"✅ Lesson title: {lesson.get('title')}")
                    self.log(f"✅ Lesson source: {lesson.get('source')}")
                    
                    # Пробуем обновить контент урока
                    update_data = {
                        "section": "theory",
                        "field": "what_is_topic",
                        "value": f"Обновленная тема урока - {datetime.now().strftime('%H:%M:%S')}"
                    }
                    
                    response = self.session.put(f"{BACKEND_URL}/admin/lessons/lesson_numerom_intro/content", json=update_data)
                    
                    if response.status_code == 200:
                        update_result = response.json()
                        if update_result.get('success'):
                            self.log("✅ First lesson content updated successfully")
                            self.log(f"✅ Update message: {update_result.get('message')}")
                            return True
                        else:
                            self.log(f"❌ Content update failed: {update_result}")
                            return False
                    else:
                        self.log(f"❌ Content update request failed: {response.status_code} - {response.text}")
                        return False
                else:
                    self.log("❌ No lesson data in response")
                    return False
            else:
                self.log(f"❌ Failed to retrieve first lesson: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ First lesson editing test error: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test lesson if created"""
        if self.test_lesson_id:
            self.log(f"\n🧹 Cleaning up test lesson: {self.test_lesson_id}")
            try:
                response = self.session.delete(f"{BACKEND_URL}/admin/lessons/{self.test_lesson_id}")
                if response.status_code == 200:
                    self.log("✅ Test lesson cleaned up successfully")
                else:
                    self.log(f"⚠️  Test lesson cleanup failed: {response.status_code}")
            except Exception as e:
                self.log(f"⚠️  Test lesson cleanup error: {str(e)}")
    
    def run_all_tests(self):
        """Run all lesson management tests"""
        self.log("🚀 Starting First Lesson Integration Tests")
        self.log("=" * 60)
        
        if not self.authenticate():
            self.log("❌ Authentication failed - cannot proceed with tests")
            return False
        
        test_results = []
        
        # Test 1: Sync first lesson
        test_results.append(("Sync First Lesson", self.test_sync_first_lesson()))
        
        # Test 2: Combined lessons list
        test_results.append(("Combined Lessons List", self.test_combined_lessons_list()))
        
        # Test 3: Duplicate protection
        test_results.append(("Duplicate Protection", self.test_duplicate_protection()))
        
        # Test 4: Sorting with new lesson
        test_results.append(("Sorting Test", self.test_sorting_with_new_lesson()))
        
        # Test 5: First lesson editing
        test_results.append(("First Lesson Editing", self.test_first_lesson_editing()))
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("📊 TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{test_name}: {status}")
            if result:
                passed += 1
        
        self.log(f"\nOverall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED! First lesson integration working correctly.")
        else:
            self.log(f"⚠️  {total - passed} test(s) failed. Review the issues above.")
        
        return passed == total

if __name__ == "__main__":
    tester = FirstLessonIntegrationTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)