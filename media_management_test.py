#!/usr/bin/env python3
"""
Media Management System Test Suite
Testing complete media file management system for lessons as requested in review.

NEW ENDPOINTS FOR TESTING:
1. DELETE /api/admin/lessons/video/{file_id} - удаление видео файла урока
2. DELETE /api/admin/lessons/pdf/{file_id} - удаление PDF файла урока  
3. GET /api/lessons/media/{lesson_id} - получение всех медиа файлов урока

AUTHENTICATION:
- Email: dmitrii.malahov@gmail.com
- Password: 756bvy67H

FULL TEST SCENARIO:
1. Create test lesson for media: POST /api/admin/lessons/create with lesson_id: "media_test_lesson"
2. Upload media files: POST /api/admin/lessons/media_test_lesson/upload-video and upload-pdf
3. Get media files list: GET /api/lessons/media/media_test_lesson
4. Delete media files: DELETE /api/admin/lessons/video/{video_id} and DELETE /api/admin/lessons/pdf/{pdf_id}
5. Check first lesson integration: GET /api/lessons/media/lesson_numerom_intro
6. Test error scenarios: 404 errors, access rights
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
TEST_LESSON_ID = "media_test_lesson"

class MediaManagementTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_lesson_id = TEST_LESSON_ID
        self.uploaded_video_id = None
        self.uploaded_pdf_id = None
        self.test_results = []
        
    def log(self, message):
        print(f"[MEDIA TEST] {message}")
        
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
                    f"Logged in as {user_info['email']}, Credits: {user_info.get('credits_remaining', 'N/A')}, Super Admin: {user_info.get('is_super_admin', False)}"
                )
                return True
            else:
                self.add_result("Authentication", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Authentication", False, f"Login error: {str(e)}")
            return False
    
    def create_test_lesson(self):
        """Create a test lesson for media uploads"""
        self.log("📚 Creating test lesson for media...")
        
        lesson_data = {
            "id": self.test_lesson_id,
            "title": "Test Lesson for Media Management",
            "module": "Test Module",
            "description": "Test lesson created for media file management testing",
            "points_required": 0,
            "is_active": True,
            "content": {
                "theory": {
                    "what_is_topic": "Test topic for media management",
                    "main_story": "This is a test lesson for media file management",
                    "key_concepts": "Media upload, file management, streaming",
                    "practical_applications": "Testing video and PDF uploads"
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
    
    def create_test_video_file(self):
        """Create a test video file for upload"""
        try:
            # Create a small test video file (actually just a text file with video extension)
            test_content = b"This is a test video file content for media management testing"
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_file.write(test_content)
            temp_file.close()
            return temp_file.name
        except Exception as e:
            self.log(f"Error creating test video file: {str(e)}")
            return None
    
    def create_test_pdf_file(self):
        """Create a test PDF file for upload"""
        try:
            # Create a simple PDF-like file (actually just text with PDF extension)
            test_content = b"%PDF-1.4\nThis is a test PDF file content for media management testing"
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.write(test_content)
            temp_file.close()
            return temp_file.name
        except Exception as e:
            self.log(f"Error creating test PDF file: {str(e)}")
            return None
    
    def upload_video_file(self):
        """Upload video file to test lesson"""
        self.log("🎥 Uploading test video file...")
        
        video_file_path = self.create_test_video_file()
        if not video_file_path:
            self.add_result("Upload Video File", False, "Failed to create test video file")
            return False
        
        try:
            with open(video_file_path, 'rb') as video_file:
                files = {'file': ('test_lesson_video.mp4', video_file, 'video/mp4')}
                response = self.session.post(
                    f"{BACKEND_URL}/admin/lessons/{self.test_lesson_id}/upload-video",
                    files=files
                )
            
            # Clean up temp file
            os.unlink(video_file_path)
            
            if response.status_code == 200:
                data = response.json()
                self.uploaded_video_id = data.get('file_id')
                self.add_result(
                    "Upload Video File", 
                    True, 
                    f"Video uploaded successfully: {data.get('filename')} (ID: {self.uploaded_video_id})"
                )
                return True
            else:
                self.add_result("Upload Video File", False, f"Upload failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Upload Video File", False, f"Upload error: {str(e)}")
            return False
    
    def upload_pdf_file(self):
        """Upload PDF file to test lesson"""
        self.log("📄 Uploading test PDF file...")
        
        pdf_file_path = self.create_test_pdf_file()
        if not pdf_file_path:
            self.add_result("Upload PDF File", False, "Failed to create test PDF file")
            return False
        
        try:
            with open(pdf_file_path, 'rb') as pdf_file:
                files = {'file': ('test_lesson_document.pdf', pdf_file, 'application/pdf')}
                response = self.session.post(
                    f"{BACKEND_URL}/admin/lessons/{self.test_lesson_id}/upload-pdf",
                    files=files
                )
            
            # Clean up temp file
            os.unlink(pdf_file_path)
            
            if response.status_code == 200:
                data = response.json()
                self.uploaded_pdf_id = data.get('file_id')
                self.add_result(
                    "Upload PDF File", 
                    True, 
                    f"PDF uploaded successfully: {data.get('filename')} (ID: {self.uploaded_pdf_id})"
                )
                return True
            else:
                self.add_result("Upload PDF File", False, f"Upload failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Upload PDF File", False, f"Upload error: {str(e)}")
            return False
    
    def get_lesson_media_files(self, lesson_id=None):
        """Get all media files for a lesson - NEW ENDPOINT TEST"""
        if lesson_id is None:
            lesson_id = self.test_lesson_id
            
        self.log(f"📋 Getting media files for lesson: {lesson_id}")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/lessons/media/{lesson_id}")
            
            if response.status_code == 200:
                data = response.json()
                videos = data.get('videos', [])
                pdfs = data.get('pdfs', [])
                
                self.add_result(
                    f"Get Media Files ({lesson_id})", 
                    True, 
                    f"Retrieved {len(videos)} videos and {len(pdfs)} PDFs"
                )
                
                # Verify structure
                for video in videos:
                    required_fields = ['id', 'filename', 'video_url', 'uploaded_at']
                    missing_fields = [field for field in required_fields if field not in video]
                    if missing_fields:
                        self.add_result(
                            "Video Structure Validation", 
                            False, 
                            f"Missing fields in video: {missing_fields}"
                        )
                    else:
                        self.add_result(
                            "Video Structure Validation", 
                            True, 
                            f"Video structure valid: {video['filename']}"
                        )
                
                for pdf in pdfs:
                    required_fields = ['id', 'filename', 'pdf_url', 'uploaded_at']
                    missing_fields = [field for field in required_fields if field not in pdf]
                    if missing_fields:
                        self.add_result(
                            "PDF Structure Validation", 
                            False, 
                            f"Missing fields in PDF: {missing_fields}"
                        )
                    else:
                        self.add_result(
                            "PDF Structure Validation", 
                            True, 
                            f"PDF structure valid: {pdf['filename']}"
                        )
                
                return data
            else:
                self.add_result(f"Get Media Files ({lesson_id})", False, f"Request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.add_result(f"Get Media Files ({lesson_id})", False, f"Request error: {str(e)}")
            return None
    
    def delete_video_file(self, file_id):
        """Delete video file - NEW ENDPOINT TEST"""
        self.log(f"🗑️ Deleting video file: {file_id}")
        
        try:
            response = self.session.delete(f"{BACKEND_URL}/admin/lessons/video/{file_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.add_result(
                    "Delete Video File", 
                    True, 
                    f"Video deleted successfully: {data.get('message', 'No message')}"
                )
                return True
            else:
                self.add_result("Delete Video File", False, f"Delete failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Delete Video File", False, f"Delete error: {str(e)}")
            return False
    
    def delete_pdf_file(self, file_id):
        """Delete PDF file - NEW ENDPOINT TEST"""
        self.log(f"🗑️ Deleting PDF file: {file_id}")
        
        try:
            response = self.session.delete(f"{BACKEND_URL}/admin/lessons/pdf/{file_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.add_result(
                    "Delete PDF File", 
                    True, 
                    f"PDF deleted successfully: {data.get('message', 'No message')}"
                )
                return True
            else:
                self.add_result("Delete PDF File", False, f"Delete failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.add_result("Delete PDF File", False, f"Delete error: {str(e)}")
            return False
    
    def test_first_lesson_integration(self):
        """Test integration with first lesson"""
        self.log("🎯 Testing first lesson media integration...")
        
        first_lesson_media = self.get_lesson_media_files("lesson_numerom_intro")
        if first_lesson_media:
            videos = first_lesson_media.get('videos', [])
            pdfs = first_lesson_media.get('pdfs', [])
            
            self.add_result(
                "First Lesson Integration", 
                True, 
                f"First lesson has {len(videos)} videos and {len(pdfs)} PDFs available"
            )
            
            # Log some details about available media
            if videos:
                self.log(f"📹 First lesson videos: {[v.get('filename', 'Unknown') for v in videos[:3]]}")
            if pdfs:
                self.log(f"📄 First lesson PDFs: {[p.get('filename', 'Unknown') for p in pdfs[:3]]}")
                
            return True
        else:
            self.add_result("First Lesson Integration", False, "Could not retrieve first lesson media")
            return False
    
    def test_error_scenarios(self):
        """Test error scenarios"""
        self.log("⚠️ Testing error scenarios...")
        
        # Test 1: Delete non-existent video file
        fake_video_id = str(uuid.uuid4())
        try:
            response = self.session.delete(f"{BACKEND_URL}/admin/lessons/video/{fake_video_id}")
            if response.status_code == 404:
                self.add_result(
                    "404 Error for Non-existent Video", 
                    True, 
                    "Correctly returned 404 for non-existent video file"
                )
            else:
                self.add_result(
                    "404 Error for Non-existent Video", 
                    False, 
                    f"Expected 404, got {response.status_code}"
                )
        except Exception as e:
            self.add_result("404 Error for Non-existent Video", False, f"Error: {str(e)}")
        
        # Test 2: Delete non-existent PDF file
        fake_pdf_id = str(uuid.uuid4())
        try:
            response = self.session.delete(f"{BACKEND_URL}/admin/lessons/pdf/{fake_pdf_id}")
            if response.status_code == 404:
                self.add_result(
                    "404 Error for Non-existent PDF", 
                    True, 
                    "Correctly returned 404 for non-existent PDF file"
                )
            else:
                self.add_result(
                    "404 Error for Non-existent PDF", 
                    False, 
                    f"Expected 404, got {response.status_code}"
                )
        except Exception as e:
            self.add_result("404 Error for Non-existent PDF", False, f"Error: {str(e)}")
        
        # Test 3: Get media for non-existent lesson
        fake_lesson_id = "non_existent_lesson_" + str(uuid.uuid4())[:8]
        try:
            response = self.session.get(f"{BACKEND_URL}/lessons/media/{fake_lesson_id}")
            # This might return empty arrays or 404, both are acceptable
            if response.status_code in [200, 404]:
                self.add_result(
                    "Non-existent Lesson Media", 
                    True, 
                    f"Handled non-existent lesson appropriately: {response.status_code}"
                )
            else:
                self.add_result(
                    "Non-existent Lesson Media", 
                    False, 
                    f"Unexpected response: {response.status_code}"
                )
        except Exception as e:
            self.add_result("Non-existent Lesson Media", False, f"Error: {str(e)}")
    
    def verify_file_deletion_from_database(self):
        """Verify that deleted files are removed from database"""
        self.log("🔍 Verifying file deletion from database...")
        
        # Get media files again to verify deletion
        media_data = self.get_lesson_media_files()
        if media_data:
            videos = media_data.get('videos', [])
            pdfs = media_data.get('pdfs', [])
            
            # Check if our uploaded files are still there (they shouldn't be)
            video_still_exists = any(v.get('id') == self.uploaded_video_id for v in videos) if self.uploaded_video_id else False
            pdf_still_exists = any(p.get('id') == self.uploaded_pdf_id for p in pdfs) if self.uploaded_pdf_id else False
            
            if not video_still_exists and not pdf_still_exists:
                self.add_result(
                    "Database Cleanup Verification", 
                    True, 
                    "Deleted files successfully removed from database"
                )
            else:
                self.add_result(
                    "Database Cleanup Verification", 
                    False, 
                    f"Files still in database - Video: {video_still_exists}, PDF: {pdf_still_exists}"
                )
        else:
            self.add_result("Database Cleanup Verification", False, "Could not verify database cleanup")
    
    def cleanup_test_lesson(self):
        """Clean up test lesson"""
        self.log("🧹 Cleaning up test lesson...")
        
        try:
            response = self.session.delete(f"{BACKEND_URL}/admin/lessons/{self.test_lesson_id}")
            if response.status_code == 200:
                self.add_result("Test Lesson Cleanup", True, "Test lesson deleted successfully")
            else:
                self.add_result("Test Lesson Cleanup", False, f"Cleanup failed: {response.status_code}")
        except Exception as e:
            self.add_result("Test Lesson Cleanup", False, f"Cleanup error: {str(e)}")
    
    def run_full_test_suite(self):
        """Run the complete media management test suite"""
        self.log("🚀 Starting Media Management System Test Suite")
        self.log("=" * 60)
        
        # Step 1: Authentication
        if not self.authenticate():
            self.log("❌ Authentication failed, stopping tests")
            return self.generate_report()
        
        # Step 2: Create test lesson
        if not self.create_test_lesson():
            self.log("❌ Test lesson creation failed, stopping tests")
            return self.generate_report()
        
        # Step 3: Upload media files
        video_uploaded = self.upload_video_file()
        pdf_uploaded = self.upload_pdf_file()
        
        if not (video_uploaded or pdf_uploaded):
            self.log("❌ No media files uploaded successfully")
            return self.generate_report()
        
        # Step 4: Get media files list
        self.get_lesson_media_files()
        
        # Step 5: Delete uploaded files
        if self.uploaded_video_id:
            self.delete_video_file(self.uploaded_video_id)
        
        if self.uploaded_pdf_id:
            self.delete_pdf_file(self.uploaded_pdf_id)
        
        # Step 6: Verify deletion from database
        self.verify_file_deletion_from_database()
        
        # Step 7: Test first lesson integration
        self.test_first_lesson_integration()
        
        # Step 8: Test error scenarios
        self.test_error_scenarios()
        
        # Step 9: Cleanup
        self.cleanup_test_lesson()
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate test report"""
        self.log("=" * 60)
        self.log("📊 MEDIA MANAGEMENT TEST REPORT")
        self.log("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"Total Tests: {total_tests}")
        self.log(f"Passed: {passed_tests}")
        self.log(f"Failed: {failed_tests}")
        self.log(f"Success Rate: {success_rate:.1f}%")
        self.log("")
        
        if failed_tests > 0:
            self.log("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    self.log(f"  - {result['test']}: {result['details']}")
            self.log("")
        
        self.log("✅ PASSED TESTS:")
        for result in self.test_results:
            if result['success']:
                self.log(f"  - {result['test']}: {result['details']}")
        
        self.log("=" * 60)
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'results': self.test_results
        }

def main():
    """Main test execution"""
    tester = MediaManagementTester()
    report = tester.run_full_test_suite()
    
    # Return appropriate exit code
    if report['failed_tests'] == 0:
        print("\n🎉 ALL TESTS PASSED!")
        exit(0)
    else:
        print(f"\n⚠️ {report['failed_tests']} TESTS FAILED!")
        exit(1)

if __name__ == "__main__":
    main()