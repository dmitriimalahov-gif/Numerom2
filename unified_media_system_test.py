#!/usr/bin/env python3
"""
Unified Media System Test Suite - Exact Copy of PersonalConsultations
Testing the unified media file system for lessons as requested in review.

REVIEW REQUEST: Протестируй полностью унифицированную систему медиа файлов (точная копия PersonalConsultations)

ENDPOINTS ДЛЯ ТЕСТИРОВАНИЯ:
1. POST /api/admin/consultations/upload-video - загрузка видео (как в консультациях)
2. POST /api/admin/consultations/upload-pdf - загрузка PDF (как в консультациях)  
3. PUT /api/admin/lessons/{lesson_id} (ОБНОВЛЕН) - сохранение video_file_id, pdf_file_id в уроке
4. GET /api/learning/all-lessons - получение уроков с медиа полями для студентов
5. GET /api/consultations/video/{file_id} - просмотр видео через консультационную систему
6. GET /api/consultations/pdf/{file_id} - просмотр PDF через консультационную систему

АУТЕНТИФИКАЦИЯ: dmitrii.malahov@gmail.com / 756bvy67H

ПОЛНЫЙ ТЕСТОВЫЙ СЦЕНАРИЙ (КАК В PERSONALCONSULTATIONS):
1. Создание урока с медиа полями
2. Загрузка файлов ЧЕРЕЗ КОНСУЛЬТАЦИОННУЮ СИСТЕМУ
3. Сохранение медиа в уроке (как в консультациях)
4. Проверка студенческого доступа
5. Тестирование просмотра файлов
6. Проверка синхронизации первого урока
"""

import requests
import json
import os
import tempfile
from pathlib import Path
import time
import io

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_EMAIL = "dmitrii.malahov@gmail.com"
TEST_PASSWORD = "756bvy67H"

class UnifiedMediaSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_lesson_id = "unified_media_test_lesson"
        self.video_file_id = None
        self.pdf_file_id = None
        self.video_filename = None
        self.pdf_filename = None
        self.test_results = []
        
    def log(self, message):
        print(f"[UNIFIED_MEDIA_TEST] {message}")
        
    def add_result(self, test_name, success, details=""):
        result = {
            'test': test_name,
            'success': success,
            'details': details
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
                self.auth_token = data['access_token']
                self.user_id = data['user']['id']
                self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                
                user_info = data['user']
                self.add_result(
                    "Authentication", 
                    True, 
                    f"Logged in as {user_info['email']} (ID: {self.user_id}, Super Admin: {user_info.get('is_super_admin', False)}, Credits: {user_info.get('credits_remaining', 0)})"
                )
                return True
            else:
                self.add_result("Authentication", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Authentication", False, f"Login error: {str(e)}")
            return False
    
    def create_lesson_with_media_fields(self):
        """1. Создание урока с медиа полями"""
        self.log("📚 Creating lesson with media fields...")
        
        lesson_data = {
            "id": self.test_lesson_id,
            "title": "Унифицированный медиа тест",
            "module": "Тестовый модуль",
            "description": "Урок для тестирования унифицированной медиа системы",
            "points_required": 0,
            "is_active": True,
            "video_file_id": "",  # Будет заполнено после загрузки
            "video_filename": "",
            "pdf_file_id": "",    # Будет заполнено после загрузки
            "pdf_filename": "",
            "content": {
                "theory": {
                    "what_is_topic": "Тестирование унифицированной медиа интеграции",
                    "main_story": "Этот урок тестирует унифицированную медиа систему",
                    "key_concepts": "Медиа интеграция, консультационная система",
                    "practical_applications": "Связывание файлов и стриминг"
                }
            }
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/admin/lessons/create", json=lesson_data)
            if response.status_code == 200:
                data = response.json()
                self.add_result(
                    "Create Lesson with Media Fields", 
                    True, 
                    f"Lesson created successfully: {data.get('lesson_id', self.test_lesson_id)}"
                )
                return True
            else:
                self.add_result("Create Lesson with Media Fields", False, f"Failed to create lesson: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Create Lesson with Media Fields", False, f"Error creating lesson: {str(e)}")
            return False
    
    def upload_video_through_consultations(self):
        """2. Загрузка видео ЧЕРЕЗ КОНСУЛЬТАЦИОННУЮ СИСТЕМУ"""
        self.log("🎥 Uploading video through consultation system...")
        
        # Create test video content
        video_content = b"FAKE_VIDEO_CONTENT_FOR_UNIFIED_TESTING" * 200  # Simulate video file
        self.video_filename = "unified_test_video.mp4"
        
        try:
            files = {
                'file': (self.video_filename, io.BytesIO(video_content), 'video/mp4')
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/consultations/upload-video", files=files)
            if response.status_code == 200:
                data = response.json()
                self.video_file_id = data.get('file_id')
                self.add_result(
                    "Upload Video via Consultations", 
                    True, 
                    f"Video uploaded successfully: file_id={self.video_file_id}, filename={data.get('filename')}"
                )
                return True
            else:
                self.add_result("Upload Video via Consultations", False, f"Failed to upload video: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Upload Video via Consultations", False, f"Error uploading video: {str(e)}")
            return False
    
    def upload_pdf_through_consultations(self):
        """2. Загрузка PDF ЧЕРЕЗ КОНСУЛЬТАЦИОННУЮ СИСТЕМУ"""
        self.log("📄 Uploading PDF through consultation system...")
        
        # Create test PDF content
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Unified Media Test) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000201 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n295\n%%EOF"
        self.pdf_filename = "unified_test_document.pdf"
        
        try:
            files = {
                'file': (self.pdf_filename, io.BytesIO(pdf_content), 'application/pdf')
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/consultations/upload-pdf", files=files)
            if response.status_code == 200:
                data = response.json()
                self.pdf_file_id = data.get('file_id')
                self.add_result(
                    "Upload PDF via Consultations", 
                    True, 
                    f"PDF uploaded successfully: file_id={self.pdf_file_id}, filename={data.get('filename')}"
                )
                return True
            else:
                self.add_result("Upload PDF via Consultations", False, f"Failed to upload PDF: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Upload PDF via Consultations", False, f"Error uploading PDF: {str(e)}")
            return False
    
    def save_media_in_lesson(self):
        """3. Сохранение медиа в уроке (как в консультациях)"""
        self.log("💾 Saving media in lesson (like consultations)...")
        
        if not self.video_file_id or not self.pdf_file_id:
            self.add_result("Save Media in Lesson", False, "Missing video_file_id or pdf_file_id")
            return False
        
        try:
            # Update lesson with media fields (exactly like consultations)
            update_data = {
                "video_file_id": self.video_file_id,
                "video_filename": self.video_filename,
                "pdf_file_id": self.pdf_file_id,
                "pdf_filename": self.pdf_filename
            }
            
            response = self.session.put(f"{BACKEND_URL}/admin/lessons/{self.test_lesson_id}", json=update_data)
            if response.status_code == 200:
                data = response.json()
                self.add_result(
                    "Save Media in Lesson", 
                    True, 
                    f"Media saved successfully: {data.get('message', 'Success')}"
                )
                return True
            else:
                self.add_result("Save Media in Lesson", False, f"Failed to save media: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Save Media in Lesson", False, f"Error saving media: {str(e)}")
            return False
    
    def check_student_access(self):
        """4. Проверка студенческого доступа"""
        self.log("👨‍🎓 Checking student access...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/learning/all-lessons")
            if response.status_code == 200:
                data = response.json()
                lessons = data.get('available_lessons', [])
                
                # Find our test lesson
                test_lesson = None
                for lesson in lessons:
                    if lesson.get('id') == self.test_lesson_id:
                        test_lesson = lesson
                        break
                
                if test_lesson:
                    has_video_file_id = 'video_file_id' in test_lesson and test_lesson['video_file_id']
                    has_pdf_file_id = 'pdf_file_id' in test_lesson and test_lesson['pdf_file_id']
                    
                    success = has_video_file_id and has_pdf_file_id
                    details = f"Lesson found with video_file_id: {has_video_file_id}, pdf_file_id: {has_pdf_file_id}"
                    
                    self.add_result("Check Student Access", success, details)
                    return success
                else:
                    self.add_result("Check Student Access", False, "Test lesson not found in student lessons")
                    return False
            else:
                self.add_result("Check Student Access", False, f"Failed to get student lessons: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Check Student Access", False, f"Error checking student access: {str(e)}")
            return False
    
    def test_file_viewing(self):
        """5. Тестирование просмотра файлов"""
        self.log("👀 Testing file viewing...")
        
        if not self.video_file_id or not self.pdf_file_id:
            self.add_result("Test File Viewing", False, "Missing file IDs")
            return False
        
        try:
            # Test video viewing through consultation system
            video_response = self.session.get(f"{BACKEND_URL}/consultations/video/{self.video_file_id}")
            video_success = video_response.status_code == 200
            
            # Test PDF viewing through consultation system
            pdf_response = self.session.get(f"{BACKEND_URL}/consultations/pdf/{self.pdf_file_id}")
            pdf_success = pdf_response.status_code == 200
            
            success = video_success and pdf_success
            details = f"Video viewing: {video_success} (status: {video_response.status_code}), PDF viewing: {pdf_success} (status: {pdf_response.status_code})"
            
            self.add_result("Test File Viewing", success, details)
            return success
                
        except Exception as e:
            self.add_result("Test File Viewing", False, f"Error testing file viewing: {str(e)}")
            return False
    
    def test_first_lesson_sync(self):
        """6. Проверка синхронизации первого урока"""
        self.log("🔄 Testing first lesson sync...")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/admin/lessons/sync-first-lesson")
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                action = data.get('action', 'unknown')
                
                self.add_result(
                    "Test First Lesson Sync", 
                    success, 
                    f"Sync result: {action} - {data.get('message', 'No message')}"
                )
                return success
            else:
                self.add_result("Test First Lesson Sync", False, f"Failed to sync first lesson: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Test First Lesson Sync", False, f"Error syncing first lesson: {str(e)}")
            return False
    
    def verify_unified_system_compatibility(self):
        """Проверка полной совместимости с PersonalConsultations"""
        self.log("🔍 Verifying unified system compatibility...")
        
        try:
            # Check that lessons use EXACTLY the same fields as consultations
            response = self.session.get(f"{BACKEND_URL}/admin/lessons")
            if response.status_code == 200:
                data = response.json()
                lessons = data.get('lessons', [])
                
                # Find our test lesson
                test_lesson = None
                for lesson in lessons:
                    if lesson.get('id') == self.test_lesson_id:
                        test_lesson = lesson
                        break
                
                if test_lesson:
                    # Check for consultation-style fields
                    has_video_file_id = 'video_file_id' in test_lesson
                    has_pdf_file_id = 'pdf_file_id' in test_lesson
                    has_video_filename = 'video_filename' in test_lesson
                    has_pdf_filename = 'pdf_filename' in test_lesson
                    
                    # Check field values
                    video_id_matches = test_lesson.get('video_file_id') == self.video_file_id
                    pdf_id_matches = test_lesson.get('pdf_file_id') == self.pdf_file_id
                    
                    success = all([has_video_file_id, has_pdf_file_id, has_video_filename, has_pdf_filename, video_id_matches, pdf_id_matches])
                    details = f"Fields present: video_file_id={has_video_file_id}, pdf_file_id={has_pdf_file_id}, video_filename={has_video_filename}, pdf_filename={has_pdf_filename}. Values match: video={video_id_matches}, pdf={pdf_id_matches}"
                    
                    self.add_result("Verify Unified System Compatibility", success, details)
                    return success
                else:
                    self.add_result("Verify Unified System Compatibility", False, "Test lesson not found in admin lessons")
                    return False
            else:
                self.add_result("Verify Unified System Compatibility", False, f"Failed to get admin lessons: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Verify Unified System Compatibility", False, f"Error verifying compatibility: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data"""
        self.log("🧹 Cleaning up test data...")
        
        try:
            # Delete test lesson
            response = self.session.delete(f"{BACKEND_URL}/admin/lessons/{self.test_lesson_id}")
            cleanup_success = response.status_code in [200, 404]  # 404 is OK if already deleted
            
            self.add_result("Cleanup Test Data", cleanup_success, f"Lesson deletion status: {response.status_code}")
            return cleanup_success
                
        except Exception as e:
            self.add_result("Cleanup Test Data", False, f"Error during cleanup: {str(e)}")
            return False
    
    def run_full_test_suite(self):
        """Run the complete unified media system test suite"""
        self.log("🚀 Starting Unified Media System Test Suite...")
        self.log("=" * 80)
        
        # Test sequence as specified in review request
        tests = [
            ("Authentication", self.authenticate),
            ("Create Lesson with Media Fields", self.create_lesson_with_media_fields),
            ("Upload Video via Consultations", self.upload_video_through_consultations),
            ("Upload PDF via Consultations", self.upload_pdf_through_consultations),
            ("Save Media in Lesson", self.save_media_in_lesson),
            ("Check Student Access", self.check_student_access),
            ("Test File Viewing", self.test_file_viewing),
            ("Test First Lesson Sync", self.test_first_lesson_sync),
            ("Verify Unified System Compatibility", self.verify_unified_system_compatibility),
            ("Cleanup Test Data", self.cleanup_test_data)
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                self.add_result(test_name, False, f"Unexpected error: {str(e)}")
            
            # Small delay between tests
            time.sleep(0.5)
        
        # Print summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        self.log("=" * 80)
        self.log("🎯 UNIFIED MEDIA SYSTEM TEST SUMMARY")
        self.log("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"📊 OVERALL RESULTS:")
        self.log(f"   Total Tests: {total_tests}")
        self.log(f"   ✅ Passed: {passed_tests}")
        self.log(f"   ❌ Failed: {failed_tests}")
        self.log(f"   📈 Success Rate: {success_rate:.1f}%")
        self.log("")
        
        # Key verification points from review request
        self.log("🔑 KEY VERIFICATION POINTS:")
        
        # Check if unified system works like PersonalConsultations
        upload_video_success = any(r['test'] == 'Upload Video via Consultations' and r['success'] for r in self.test_results)
        upload_pdf_success = any(r['test'] == 'Upload PDF via Consultations' and r['success'] for r in self.test_results)
        media_save_success = any(r['test'] == 'Save Media in Lesson' and r['success'] for r in self.test_results)
        student_access_success = any(r['test'] == 'Check Student Access' and r['success'] for r in self.test_results)
        file_viewing_success = any(r['test'] == 'Test File Viewing' and r['success'] for r in self.test_results)
        compatibility_success = any(r['test'] == 'Verify Unified System Compatibility' and r['success'] for r in self.test_results)
        
        self.log(f"   📤 Upload through consultation system: {'✅' if upload_video_success and upload_pdf_success else '❌'}")
        self.log(f"   💾 Media fields saved like consultations: {'✅' if media_save_success else '❌'}")
        self.log(f"   👨‍🎓 Student access with media fields: {'✅' if student_access_success else '❌'}")
        self.log(f"   👀 File viewing through consultation URLs: {'✅' if file_viewing_success else '❌'}")
        self.log(f"   🔄 System compatibility verified: {'✅' if compatibility_success else '❌'}")
        
        self.log("")
        self.log("📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            self.log(f"   {status}: {result['test']}")
            if result['details']:
                self.log(f"      Details: {result['details']}")
        
        self.log("=" * 80)
        
        # Final verdict
        critical_tests_passed = all([
            upload_video_success, upload_pdf_success, media_save_success, 
            student_access_success, file_viewing_success, compatibility_success
        ])
        
        if critical_tests_passed:
            self.log("🎉 VERDICT: Unified media system is FULLY COMPATIBLE with PersonalConsultations!")
            self.log("   ✅ All critical functionality working as expected")
            self.log("   ✅ System uses EXACT same endpoints and fields as consultations")
            self.log("   ✅ Students can access media through unified system")
        else:
            self.log("⚠️  VERDICT: Unified media system has COMPATIBILITY ISSUES")
            self.log("   ❌ Some critical functionality not working as expected")
            self.log("   ❌ System may not be fully compatible with PersonalConsultations")
        
        self.log("=" * 80)

if __name__ == "__main__":
    tester = UnifiedMediaSystemTester()
    tester.run_full_test_suite()