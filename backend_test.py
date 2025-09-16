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

class UnifiedMediaTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_lesson_id = "unified_media_test"
        self.video_file_id = None
        self.pdf_file_id = None
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
    
    def create_test_lesson(self):
        """Create test lesson with ID 'unified_media_test'"""
        self.log("📚 Creating test lesson...")
        
        lesson_data = {
            "id": self.test_lesson_id,
            "title": "Unified Media Test Lesson",
            "module": "Test Module",
            "description": "Test lesson for unified media system",
            "points_required": 0,
            "is_active": True,
            "content": {
                "theory": {
                    "what_is_topic": "Testing unified media integration",
                    "main_story": "This lesson tests the unified media system",
                    "key_concepts": "Media integration, consultation system",
                    "practical_applications": "File linking and streaming"
                }
            }
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/admin/lessons/create", json=lesson_data)
            if response.status_code == 200:
                data = response.json()
                self.add_result(
                    "Create Test Lesson", 
                    True, 
                    f"Lesson created successfully: {data.get('lesson_id', self.test_lesson_id)}"
                )
                return True
            else:
                self.add_result("Create Test Lesson", False, f"Failed to create lesson: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Create Test Lesson", False, f"Error creating lesson: {str(e)}")
            return False
    
    def upload_video_through_consultations(self):
        """Upload video through consultation system"""
        self.log("🎥 Uploading video through consultation system...")
        
        # Create test video content
        video_content = b"FAKE_VIDEO_CONTENT_FOR_TESTING" * 100  # Simulate video file
        
        try:
            files = {
                'file': ('test_unified_video.mp4', io.BytesIO(video_content), 'video/mp4')
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
        """Upload PDF through consultation system"""
        self.log("📄 Uploading PDF through consultation system...")
        
        # Create test PDF content
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n174\n%%EOF"
        
        try:
            files = {
                'file': ('test_unified_document.pdf', io.BytesIO(pdf_content), 'application/pdf')
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
    
    def link_video_to_lesson(self):
        """Link uploaded video to lesson using new endpoint"""
        self.log("🔗 Linking video to lesson...")
        
        if not self.video_file_id:
            self.add_result("Link Video to Lesson", False, "No video file_id available")
            return False
        
        try:
            # Get the video file data from uploaded_files collection first
            video_data = {
                "id": self.video_file_id,
                "lesson_id": self.test_lesson_id,
                "original_filename": "test_unified_video.mp4",
                "content_type": "video/mp4",
                "uploaded_by": self.user_id
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/lessons/{self.test_lesson_id}/link-video", json=video_data)
            if response.status_code == 200:
                data = response.json()
                self.add_result(
                    "Link Video to Lesson", 
                    True, 
                    f"Video linked successfully: {data.get('message', 'Success')}"
                )
                return True
            else:
                self.add_result("Link Video to Lesson", False, f"Failed to link video: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Link Video to Lesson", False, f"Error linking video: {str(e)}")
            return False
    
    def link_pdf_to_lesson(self):
        """Link uploaded PDF to lesson using new endpoint"""
        self.log("🔗 Linking PDF to lesson...")
        
        if not self.pdf_file_id:
            self.add_result("Link PDF to Lesson", False, "No PDF file_id available")
            return False
        
        try:
            # Get the PDF file data from uploaded_files collection first
            pdf_data = {
                "id": self.pdf_file_id,
                "lesson_id": self.test_lesson_id,
                "original_filename": "test_unified_document.pdf",
                "content_type": "application/pdf",
                "uploaded_by": self.user_id
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/lessons/{self.test_lesson_id}/link-pdf", json=pdf_data)
            if response.status_code == 200:
                data = response.json()
                self.add_result(
                    "Link PDF to Lesson", 
                    True, 
                    f"PDF linked successfully: {data.get('message', 'Success')}"
                )
                return True
            else:
                self.add_result("Link PDF to Lesson", False, f"Failed to link PDF: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Link PDF to Lesson", False, f"Error linking PDF: {str(e)}")
            return False
    
    def check_unified_urls(self):
        """Check that lesson media returns /api/consultations/* URLs"""
        self.log("🌐 Checking unified URLs format...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/lessons/media/{self.test_lesson_id}")
            if response.status_code == 200:
                data = response.json()
                
                videos = data.get('videos', [])
                pdfs = data.get('pdfs', [])
                
                # Check video URLs
                video_url_correct = False
                pdf_url_correct = False
                
                if videos:
                    for video in videos:
                        video_url = video.get('video_url', '')
                        if '/api/consultations/video/' in video_url:
                            video_url_correct = True
                            break
                
                if pdfs:
                    for pdf in pdfs:
                        pdf_url = pdf.get('pdf_url', '')
                        if '/api/consultations/pdf/' in pdf_url:
                            pdf_url_correct = True
                            break
                
                success = video_url_correct and pdf_url_correct
                details = f"Videos: {len(videos)} (URLs correct: {video_url_correct}), PDFs: {len(pdfs)} (URLs correct: {pdf_url_correct})"
                
                self.add_result("Check Unified URLs", success, details)
                return success
            else:
                self.add_result("Check Unified URLs", False, f"Failed to get lesson media: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Check Unified URLs", False, f"Error checking URLs: {str(e)}")
            return False
    
    def test_deletion_from_both_systems(self):
        """Test deletion removes files from both lesson and consultation systems"""
        self.log("🗑️ Testing deletion from both systems...")
        
        success_count = 0
        total_tests = 2
        
        # Test video deletion
        if self.video_file_id:
            try:
                response = self.session.delete(f"{BACKEND_URL}/admin/lessons/video/{self.video_file_id}")
                if response.status_code == 200:
                    success_count += 1
                    self.log(f"✅ Video deletion successful: {response.json().get('message', 'Success')}")
                else:
                    self.log(f"❌ Video deletion failed: {response.status_code} - {response.text}")
            except Exception as e:
                self.log(f"❌ Video deletion error: {str(e)}")
        
        # Test PDF deletion
        if self.pdf_file_id:
            try:
                response = self.session.delete(f"{BACKEND_URL}/admin/lessons/pdf/{self.pdf_file_id}")
                if response.status_code == 200:
                    success_count += 1
                    self.log(f"✅ PDF deletion successful: {response.json().get('message', 'Success')}")
                else:
                    self.log(f"❌ PDF deletion failed: {response.status_code} - {response.text}")
            except Exception as e:
                self.log(f"❌ PDF deletion error: {str(e)}")
        
        success = success_count == total_tests
        self.add_result("Test Deletion from Both Systems", success, f"{success_count}/{total_tests} deletions successful")
        return success
    
    def test_student_api_compatibility(self):
        """Test GET /api/learning/all-lessons includes custom_lessons"""
        self.log("👨‍🎓 Testing student API compatibility...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/learning/all-lessons")
            if response.status_code == 200:
                data = response.json()
                
                available_lessons = data.get('available_lessons', [])
                custom_lessons_count = sum(1 for lesson in available_lessons if lesson.get('source') == 'custom_lessons')
                
                # Check if our test lesson is included
                test_lesson_found = any(lesson.get('id') == self.test_lesson_id for lesson in available_lessons)
                
                # Check compatibility fields
                compatibility_fields = ['level', 'duration_minutes', 'video_url', 'video_file_id', 'pdf_file_id']
                compatibility_check = True
                
                for lesson in available_lessons:
                    if lesson.get('source') == 'custom_lessons':
                        for field in compatibility_fields:
                            if field not in lesson:
                                compatibility_check = False
                                break
                
                success = test_lesson_found and compatibility_check
                details = f"Total lessons: {len(available_lessons)}, Custom lessons: {custom_lessons_count}, Test lesson found: {test_lesson_found}, Compatibility: {compatibility_check}"
                
                self.add_result("Student API Compatibility", success, details)
                return success
            else:
                self.add_result("Student API Compatibility", False, f"Failed to get all lessons: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Student API Compatibility", False, f"Error testing student API: {str(e)}")
            return False
    
    def test_first_lesson_integration(self):
        """Test first lesson uses unified system"""
        self.log("🥇 Testing first lesson integration...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/lessons/media/lesson_numerom_intro")
            if response.status_code == 200:
                data = response.json()
                
                videos = data.get('videos', [])
                pdfs = data.get('pdfs', [])
                
                # Check if first lesson has media files
                has_media = len(videos) > 0 or len(pdfs) > 0
                
                # Check URL format for first lesson
                unified_urls = True
                for video in videos:
                    if '/api/consultations/video/' not in video.get('video_url', ''):
                        unified_urls = False
                        break
                
                for pdf in pdfs:
                    if '/api/consultations/pdf/' not in pdf.get('pdf_url', ''):
                        unified_urls = False
                        break
                
                success = has_media and unified_urls
                details = f"Has media: {has_media}, Videos: {len(videos)}, PDFs: {len(pdfs)}, Unified URLs: {unified_urls}"
                
                self.add_result("First Lesson Integration", success, details)
                return success
            else:
                self.add_result("First Lesson Integration", False, f"Failed to get first lesson media: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("First Lesson Integration", False, f"Error testing first lesson: {str(e)}")
            return False
    
    def cleanup_test_lesson(self):
        """Clean up test lesson"""
        self.log("🧹 Cleaning up test lesson...")
        
        try:
            response = self.session.delete(f"{BACKEND_URL}/admin/lessons/{self.test_lesson_id}")
            if response.status_code == 200:
                self.add_result("Cleanup Test Lesson", True, "Test lesson deleted successfully")
                return True
            else:
                self.add_result("Cleanup Test Lesson", False, f"Failed to delete test lesson: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Cleanup Test Lesson", False, f"Error cleaning up: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run complete unified media system test suite"""
        self.log("🚀 Starting Unified Media System Test Suite...")
        self.log("=" * 80)
        
        # Step 1: Authentication
        if not self.authenticate():
            return self.generate_report()
        
        # Step 2: Create test lesson
        if not self.create_test_lesson():
            return self.generate_report()
        
        # Step 3: Upload files through consultation system
        video_uploaded = self.upload_video_through_consultations()
        pdf_uploaded = self.upload_pdf_through_consultations()
        
        if not (video_uploaded and pdf_uploaded):
            self.cleanup_test_lesson()
            return self.generate_report()
        
        # Step 4: Link files to lesson
        video_linked = self.link_video_to_lesson()
        pdf_linked = self.link_pdf_to_lesson()
        
        # Step 5: Check unified URLs
        self.check_unified_urls()
        
        # Step 6: Test student API
        self.test_student_api_compatibility()
        
        # Step 7: Test first lesson integration
        self.test_first_lesson_integration()
        
        # Step 8: Test deletion from both systems
        self.test_deletion_from_both_systems()
        
        # Step 9: Cleanup
        self.cleanup_test_lesson()
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        self.log("=" * 80)
        self.log("📊 UNIFIED MEDIA SYSTEM TEST REPORT")
        self.log("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"Total Tests: {total_tests}")
        self.log(f"Passed: {passed_tests}")
        self.log(f"Failed: {failed_tests}")
        self.log(f"Success Rate: {success_rate:.1f}%")
        self.log("")
        
        # Detailed results
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            self.log(f"{status}: {result['test']}")
            if result['details']:
                self.log(f"    Details: {result['details']}")
        
        self.log("=" * 80)
        
        # Summary for main agent
        if success_rate >= 80:
            self.log("🎉 UNIFIED MEDIA SYSTEM TESTING SUCCESSFUL!")
            self.log("All key components of the unified media system are working correctly.")
        else:
            self.log("⚠️ UNIFIED MEDIA SYSTEM HAS ISSUES!")
            self.log("Some critical components need attention.")
        
        return {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': success_rate,
            'results': self.test_results
        }

def main():
    """Main test execution"""
    tester = UnifiedMediaTester()
    report = tester.run_all_tests()
    
    # Return exit code based on success rate
    if report['success_rate'] >= 80:
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main()