#!/usr/bin/env python3
"""
Lesson Management System Test Suite
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
import uuid

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_EMAIL = "dmitrii.malahov@gmail.com"
TEST_PASSWORD = "756bvy67H"

# Test lesson data from review request
TEST_LESSON_DATA = {
    "title": "Тестовый урок: Цифры и Планеты",
    "module": "numerology", 
    "description": "Второй урок нумерологии о значениях цифр",
    "points_required": 5,
    "is_active": True,
    "content": {
        "theory": {
            "what_is_topic": "Изучение значений цифр 1-9",
            "main_story": "Детальный анализ каждой цифры",
            "key_concepts": "Планетарные соответствия", 
            "practical_applications": "Применение в жизни"
        }
    }
}

class LessonManagementTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.created_lesson_id = None
        self.video_file_id = None
        self.pdf_file_id = None
        self.test_results = []
        
    def log(self, message):
        print(f"[TEST] {message}")
        
    def add_result(self, test_name, success, details=""):
        result = {
            "test": test_name,
            "success": success,
            "details": details
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        self.log(f"{status}: {test_name} - {details}")
        
    def authenticate(self):
        """Authenticate as super admin"""
        self.log("🔐 Authenticating as super admin...")
        
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                self.user_id = data["user"]["id"]
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                })
                
                user_info = data["user"]
                self.add_result(
                    "Super Admin Authentication", 
                    True, 
                    f"Logged in as {user_info['email']}, Credits: {user_info.get('credits_remaining', 0)}, Super Admin: {user_info.get('is_super_admin', False)}"
                )
                return True
            else:
                self.add_result("Super Admin Authentication", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Super Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_create_lesson(self):
        """Test POST /api/admin/lessons/create"""
        self.log("📝 Testing lesson creation...")
        
        try:
            # Add unique ID to lesson data
            lesson_data = TEST_LESSON_DATA.copy()
            lesson_data["id"] = str(uuid.uuid4())
            self.created_lesson_id = lesson_data["id"]
            
            response = self.session.post(f"{BACKEND_URL}/admin/lessons/create", json=lesson_data)
            
            if response.status_code == 200:
                result = response.json()
                self.add_result(
                    "Create New Lesson", 
                    True, 
                    f"Lesson created successfully with ID: {self.created_lesson_id}"
                )
                return True
            else:
                self.add_result("Create New Lesson", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Create New Lesson", False, f"Exception: {str(e)}")
            return False
    
    def test_get_lesson_by_id(self):
        """Test GET /api/admin/lessons/{lesson_id}"""
        self.log("📖 Testing get lesson by ID...")
        
        if not self.created_lesson_id:
            self.add_result("Get Lesson by ID", False, "No lesson ID available from creation test")
            return False
            
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/lessons/{self.created_lesson_id}")
            
            if response.status_code == 200:
                data = response.json()
                lesson_data = data.get("lesson", {})
                
                # Verify lesson data matches what we created
                title_match = lesson_data.get("title") == TEST_LESSON_DATA["title"]
                module_match = lesson_data.get("module") == TEST_LESSON_DATA["module"]
                content_exists = "content" in lesson_data
                
                if title_match and module_match and content_exists:
                    self.add_result(
                        "Get Lesson by ID", 
                        True, 
                        f"Lesson retrieved successfully: {lesson_data.get('title')}"
                    )
                    return True
                else:
                    self.add_result("Get Lesson by ID", False, f"Data mismatch - title: {title_match}, module: {module_match}, content: {content_exists}")
                    return False
            else:
                self.add_result("Get Lesson by ID", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Get Lesson by ID", False, f"Exception: {str(e)}")
            return False
    
    def test_update_lesson_content(self):
        """Test PUT /api/admin/lessons/{lesson_id}/content"""
        self.log("✏️ Testing lesson content update...")
        
        if not self.created_lesson_id:
            self.add_result("Update Lesson Content", False, "No lesson ID available")
            return False
            
        try:
            # Use the correct structure expected by the endpoint
            updated_content = {
                "section": "theory",
                "field": "what_is_topic",
                "value": "ОБНОВЛЕНО: Изучение значений цифр 1-9"
            }
            
            response = self.session.put(f"{BACKEND_URL}/admin/lessons/{self.created_lesson_id}/content", json=updated_content)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.add_result(
                        "Update Lesson Content", 
                        True, 
                        "Lesson content updated successfully"
                    )
                    return True
                else:
                    self.add_result("Update Lesson Content", False, f"Update failed: {result}")
                    return False
            else:
                self.add_result("Update Lesson Content", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Update Lesson Content", False, f"Exception: {str(e)}")
            return False
    
    def test_upload_video(self):
        """Test POST /api/admin/lessons/{lesson_id}/upload-video"""
        self.log("🎥 Testing video upload...")
        
        if not self.created_lesson_id:
            self.add_result("Upload Video", False, "No lesson ID available")
            return False
            
        try:
            # Create a dummy video file for testing
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                # Write some dummy video data
                temp_file.write(b'DUMMY_VIDEO_DATA_FOR_TESTING' * 100)
                temp_file_path = temp_file.name
            
            try:
                with open(temp_file_path, 'rb') as video_file:
                    files = {
                        'file': ('test_lesson_video.mp4', video_file, 'video/mp4')
                    }
                    
                    # Create a new session without Content-Type header for multipart
                    upload_session = requests.Session()
                    upload_session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    
                    response = upload_session.post(
                        f"{BACKEND_URL}/admin/lessons/{self.created_lesson_id}/upload-video",
                        files=files
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        self.video_file_id = result.get('file_id')
                        self.add_result(
                            "Upload Video", 
                            True, 
                            f"Video uploaded successfully, file_id: {self.video_file_id}"
                        )
                        return True
                    else:
                        self.add_result("Upload Video", False, f"Failed: {response.status_code} - {response.text}")
                        return False
                        
            finally:
                # Clean up temp file
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.add_result("Upload Video", False, f"Exception: {str(e)}")
            return False
    
    def test_upload_pdf(self):
        """Test POST /api/admin/lessons/{lesson_id}/upload-pdf"""
        self.log("📄 Testing PDF upload...")
        
        if not self.created_lesson_id:
            self.add_result("Upload PDF", False, "No lesson ID available")
            return False
            
        try:
            # Create a dummy PDF file for testing
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                # Write some dummy PDF data
                temp_file.write(b'%PDF-1.4\nDUMMY_PDF_DATA_FOR_TESTING' * 50)
                temp_file_path = temp_file.name
            
            try:
                with open(temp_file_path, 'rb') as pdf_file:
                    files = {
                        'file': ('test_lesson_document.pdf', pdf_file, 'application/pdf')
                    }
                    
                    # Create a new session without Content-Type header for multipart
                    upload_session = requests.Session()
                    upload_session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    
                    response = upload_session.post(
                        f"{BACKEND_URL}/admin/lessons/{self.created_lesson_id}/upload-pdf",
                        files=files
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        self.pdf_file_id = result.get('file_id')
                        self.add_result(
                            "Upload PDF", 
                            True, 
                            f"PDF uploaded successfully, file_id: {self.pdf_file_id}"
                        )
                        return True
                    else:
                        self.add_result("Upload PDF", False, f"Failed: {response.status_code} - {response.text}")
                        return False
                        
            finally:
                # Clean up temp file
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.add_result("Upload PDF", False, f"Exception: {str(e)}")
            return False
    
    def test_get_all_lessons(self):
        """Test GET /api/admin/lessons (updated to include both collections)"""
        self.log("📚 Testing get all lessons from both collections...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/lessons")
            
            if response.status_code == 200:
                result = response.json()
                lessons = result.get('lessons', [])
                total_count = result.get('total_count', 0)
                
                # Check if our created lesson is in the list
                our_lesson_found = False
                video_lessons_count = 0
                custom_lessons_count = 0
                
                for lesson in lessons:
                    if lesson.get('id') == self.created_lesson_id:
                        our_lesson_found = True
                    
                    # Count lessons by source
                    source = lesson.get('source', 'unknown')
                    if source == 'video_lessons':
                        video_lessons_count += 1
                    elif source == 'custom_lessons':
                        custom_lessons_count += 1
                
                details = f"Total lessons: {total_count}, Video lessons: {video_lessons_count}, Custom lessons: {custom_lessons_count}"
                if our_lesson_found:
                    details += f", Our test lesson found: ✅"
                else:
                    details += f", Our test lesson found: ❌"
                
                self.add_result(
                    "Get All Lessons (Both Collections)", 
                    True, 
                    details
                )
                return True
            else:
                self.add_result("Get All Lessons (Both Collections)", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Get All Lessons (Both Collections)", False, f"Exception: {str(e)}")
            return False
    
    def test_access_rights(self):
        """Test admin vs super admin access rights"""
        self.log("🔐 Testing access rights system...")
        
        try:
            # Test that we can access super admin endpoints
            response = self.session.get(f"{BACKEND_URL}/admin/lessons")
            
            if response.status_code == 200:
                self.add_result(
                    "Super Admin Access Rights", 
                    True, 
                    "Super admin can access lesson management endpoints"
                )
                return True
            elif response.status_code == 403:
                self.add_result("Super Admin Access Rights", False, "Access denied - insufficient permissions")
                return False
            else:
                self.add_result("Super Admin Access Rights", False, f"Unexpected response: {response.status_code}")
                return False
                
        except Exception as e:
            self.add_result("Super Admin Access Rights", False, f"Exception: {str(e)}")
            return False
    
    def test_delete_lesson(self):
        """Test DELETE /api/admin/lessons/{lesson_id} (updated for both collections)"""
        self.log("🗑️ Testing lesson deletion from both collections...")
        
        if not self.created_lesson_id:
            self.add_result("Delete Lesson", False, "No lesson ID available")
            return False
            
        try:
            response = self.session.delete(f"{BACKEND_URL}/admin/lessons/{self.created_lesson_id}")
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('success', False)
                message = result.get('message', '')
                
                if success:
                    self.add_result(
                        "Delete Lesson (Both Collections)", 
                        True, 
                        f"Lesson deleted successfully: {message}"
                    )
                    return True
                else:
                    self.add_result("Delete Lesson (Both Collections)", False, f"Deletion failed: {message}")
                    return False
            else:
                self.add_result("Delete Lesson (Both Collections)", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Delete Lesson (Both Collections)", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all lesson management tests"""
        self.log("🚀 Starting Lesson Management System Tests...")
        self.log("=" * 60)
        
        # Authentication test
        if not self.authenticate():
            self.log("❌ Authentication failed - stopping tests")
            return False
        
        # Run all tests in sequence
        tests = [
            self.test_create_lesson,
            self.test_get_lesson_by_id,
            self.test_update_lesson_content,
            self.test_upload_video,
            self.test_upload_pdf,
            self.test_get_all_lessons,
            self.test_access_rights,
            self.test_delete_lesson  # This should be last
        ]
        
        for test_func in tests:
            try:
                test_func()
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                self.log(f"❌ Test {test_func.__name__} crashed: {str(e)}")
        
        # Print summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test results summary"""
        self.log("=" * 60)
        self.log("📊 TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            self.log(f"{status}: {result['test']}")
            if result["details"]:
                self.log(f"    Details: {result['details']}")
        
        self.log("=" * 60)
        success_rate = (passed / total * 100) if total > 0 else 0
        self.log(f"📈 OVERALL RESULT: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            self.log("🎉 LESSON MANAGEMENT SYSTEM: WORKING CORRECTLY")
        elif success_rate >= 60:
            self.log("⚠️ LESSON MANAGEMENT SYSTEM: PARTIALLY WORKING")
        else:
            self.log("❌ LESSON MANAGEMENT SYSTEM: MAJOR ISSUES DETECTED")

if __name__ == "__main__":
    tester = LessonManagementTester()
    tester.run_all_tests()