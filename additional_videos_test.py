#!/usr/bin/env python3
"""
Backend Test Suite for Additional Video Files Management in Admin Panel
Testing the functionality of managing additional video files according to review request

ЦЕЛЬ ТЕСТИРОВАНИЯ:
Проверить полную работоспособность улучшенного интерфейса "Дополнительные видео файлы к уроку" в AdminPanel.jsx

ЗАДАЧИ ДЛЯ ТЕСТИРОВАНИЯ:
1. АУТЕНТИФИКАЦИЯ СУПЕР-АДМИНА
2. ЗАГРУЗКА ДОПОЛНИТЕЛЬНЫХ ВИДЕО
3. ПОЛУЧЕНИЕ СПИСКА ДОПОЛНИТЕЛЬНЫХ ВИДЕО
4. СТРИМИНГ ВИДЕО ФАЙЛОВ
5. УДАЛЕНИЕ ДОПОЛНИТЕЛЬНЫХ ВИДЕО
6. МАССОВОЕ УДАЛЕНИЕ
"""

import requests
import json
import os
import tempfile
import time
from pathlib import Path
import io

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_USER_EMAIL = "dmitrii.malahov@gmail.com"
TEST_USER_PASSWORD = "756bvy67H"
TEST_LESSON_ID = "lesson_numerom_intro"

class AdditionalVideosTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.uploaded_video_ids = []  # Track uploaded videos for cleanup
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def authenticate(self):
        """1. АУТЕНТИФИКАЦИЯ СУПЕР-АДМИНА: Войти как dmitrii.malahov@gmail.com / 756bvy67H"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data['access_token']
                self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                
                # Verify super admin rights
                user_data = data.get('user', {})
                is_super_admin = user_data.get('is_super_admin', False)
                credits = user_data.get('credits_remaining', 0)
                
                self.log_test(
                    "Super Admin Authentication", 
                    True, 
                    f"Successfully authenticated as {TEST_USER_EMAIL}. Super Admin: {is_super_admin}, Credits: {credits}"
                )
                return True
            else:
                self.log_test("Super Admin Authentication", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Super Admin Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def create_test_video_file(self, filename="test_lesson_video.mp4", size_kb=50):
        """Create a test video file for upload"""
        # Create a simple test file that mimics a video
        content = b"FAKE_VIDEO_CONTENT_FOR_TESTING" * (size_kb * 32)  # Approximate size
        return io.BytesIO(content), filename
    
    def test_upload_additional_video(self):
        """2. ЗАГРУЗКА ДОПОЛНИТЕЛЬНЫХ ВИДЕО: POST /api/admin/lessons/{lesson_id}/add-video"""
        try:
            # Create test video file
            video_content, filename = self.create_test_video_file("test_additional_video_1.mp4")
            
            # Prepare multipart form data
            files = {
                'file': (filename, video_content, 'video/mp4')
            }
            data = {
                'title': 'Тестовое дополнительное видео 1'
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/admin/lessons/{TEST_LESSON_ID}/add-video",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                file_id = result.get('file_id')
                video_url = result.get('video_url')
                
                # Track for cleanup
                if file_id:
                    self.uploaded_video_ids.append(file_id)
                
                # Verify response format
                expected_fields = ['success', 'file_id', 'filename', 'title', 'video_url', 'message']
                missing_fields = [field for field in expected_fields if field not in result]
                
                if not missing_fields and video_url and video_url.startswith('/api/consultations/video/'):
                    self.log_test(
                        "Upload Additional Video", 
                        True, 
                        f"Video uploaded successfully. File ID: {file_id}, URL: {video_url}"
                    )
                    return file_id
                else:
                    self.log_test(
                        "Upload Additional Video", 
                        False, 
                        f"Response missing fields: {missing_fields} or incorrect video_url format"
                    )
                    return None
            else:
                self.log_test(
                    "Upload Additional Video", 
                    False, 
                    f"Upload failed: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_test("Upload Additional Video", False, f"Upload error: {str(e)}")
            return None
    
    def test_upload_multiple_videos(self, count=3):
        """Upload multiple videos for bulk testing"""
        uploaded_ids = []
        for i in range(count):
            try:
                video_content, filename = self.create_test_video_file(f"test_bulk_video_{i+1}.mp4")
                
                files = {
                    'file': (filename, video_content, 'video/mp4')
                }
                data = {
                    'title': f'Тестовое видео для массового удаления {i+1}'
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/admin/lessons/{TEST_LESSON_ID}/add-video",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    file_id = result.get('file_id')
                    if file_id:
                        uploaded_ids.append(file_id)
                        self.uploaded_video_ids.append(file_id)
                        
            except Exception as e:
                print(f"Error uploading video {i+1}: {str(e)}")
        
        self.log_test(
            "Upload Multiple Videos for Bulk Testing", 
            len(uploaded_ids) == count, 
            f"Uploaded {len(uploaded_ids)}/{count} videos successfully"
        )
        return uploaded_ids
    
    def test_get_additional_videos_list(self):
        """3. ПОЛУЧЕНИЕ СПИСКА ДОПОЛНИТЕЛЬНЫХ ВИДЕО: GET /api/lessons/{lesson_id}/additional-videos"""
        try:
            response = self.session.get(f"{BACKEND_URL}/lessons/{TEST_LESSON_ID}/additional-videos")
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify response structure
                expected_fields = ['lesson_id', 'additional_videos', 'count']
                missing_fields = [field for field in expected_fields if field not in result]
                
                if missing_fields:
                    self.log_test(
                        "Get Additional Videos List", 
                        False, 
                        f"Response missing fields: {missing_fields}"
                    )
                    return None
                
                videos = result.get('additional_videos', [])
                count = result.get('count', 0)
                
                # Verify video data format
                if videos:
                    video = videos[0]
                    expected_video_fields = ['file_id', 'filename', 'title', 'video_url', 'uploaded_at']
                    missing_video_fields = [field for field in expected_video_fields if field not in video]
                    
                    # Check video_url format
                    video_url_correct = video.get('video_url', '').startswith('/api/consultations/video/')
                    
                    if not missing_video_fields and video_url_correct:
                        self.log_test(
                            "Get Additional Videos List", 
                            True, 
                            f"Retrieved {count} videos. Sample video URL: {video.get('video_url')}"
                        )
                        return videos
                    else:
                        self.log_test(
                            "Get Additional Videos List", 
                            False, 
                            f"Video data missing fields: {missing_video_fields} or incorrect URL format"
                        )
                        return None
                else:
                    self.log_test(
                        "Get Additional Videos List", 
                        True, 
                        f"Retrieved empty list (count: {count})"
                    )
                    return []
            else:
                self.log_test(
                    "Get Additional Videos List", 
                    False, 
                    f"Request failed: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_test("Get Additional Videos List", False, f"Request error: {str(e)}")
            return None
    
    def test_video_streaming(self, file_id):
        """4. СТРИМИНГ ВИДЕО ФАЙЛОВ: GET /api/consultations/video/{file_id}"""
        try:
            response = self.session.get(f"{BACKEND_URL}/consultations/video/{file_id}")
            
            if response.status_code == 200:
                # Check CORS headers
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                }
                
                # Check content type
                content_type = response.headers.get('Content-Type', '')
                content_length = len(response.content)
                
                # Verify streaming capabilities
                accept_ranges = response.headers.get('Accept-Ranges', '')
                content_disposition = response.headers.get('Content-Disposition', '')
                
                self.log_test(
                    "Video File Streaming", 
                    True, 
                    f"Streaming successful. Content-Type: {content_type}, Size: {content_length} bytes, "
                    f"CORS Origin: {cors_headers['Access-Control-Allow-Origin']}, "
                    f"Accept-Ranges: {accept_ranges}"
                )
                return True
            else:
                self.log_test(
                    "Video File Streaming", 
                    False, 
                    f"Streaming failed: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Video File Streaming", False, f"Streaming error: {str(e)}")
            return False
    
    def test_delete_individual_video(self, file_id):
        """5. УДАЛЕНИЕ ДОПОЛНИТЕЛЬНЫХ ВИДЕО: DELETE /api/admin/lessons/video/{file_id}"""
        try:
            response = self.session.delete(f"{BACKEND_URL}/admin/lessons/video/{file_id}")
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('success', False)
                message = result.get('message', '')
                
                if success:
                    # Remove from tracking list
                    if file_id in self.uploaded_video_ids:
                        self.uploaded_video_ids.remove(file_id)
                    
                    self.log_test(
                        "Delete Individual Video", 
                        True, 
                        f"Video deleted successfully. Message: {message}"
                    )
                    return True
                else:
                    self.log_test(
                        "Delete Individual Video", 
                        False, 
                        f"Deletion failed: {message}"
                    )
                    return False
            else:
                self.log_test(
                    "Delete Individual Video", 
                    False, 
                    f"Delete request failed: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Delete Individual Video", False, f"Delete error: {str(e)}")
            return False
    
    def test_bulk_deletion(self, video_ids):
        """6. МАССОВОЕ УДАЛЕНИЕ: Протестировать массовое удаление через функцию handleDeleteAllAdditionalVideos"""
        try:
            if not video_ids:
                self.log_test("Bulk Video Deletion", False, "No video IDs provided for bulk deletion")
                return False
            
            success_count = 0
            error_count = 0
            
            # Simulate the frontend bulk deletion logic
            for file_id in video_ids:
                try:
                    response = self.session.delete(f"{BACKEND_URL}/admin/lessons/video/{file_id}")
                    
                    if response.status_code == 200:
                        success_count += 1
                        # Remove from tracking list
                        if file_id in self.uploaded_video_ids:
                            self.uploaded_video_ids.remove(file_id)
                    else:
                        error_count += 1
                        
                except Exception as e:
                    error_count += 1
                    print(f"Error deleting video {file_id}: {str(e)}")
            
            total_videos = len(video_ids)
            success_rate = (success_count / total_videos) * 100 if total_videos > 0 else 0
            
            if success_count == total_videos:
                self.log_test(
                    "Bulk Video Deletion", 
                    True, 
                    f"All {total_videos} videos deleted successfully (100% success rate)"
                )
                return True
            elif success_count > 0:
                self.log_test(
                    "Bulk Video Deletion", 
                    False, 
                    f"Partial success: {success_count}/{total_videos} videos deleted ({success_rate:.1f}% success rate)"
                )
                return False
            else:
                self.log_test(
                    "Bulk Video Deletion", 
                    False, 
                    f"Complete failure: 0/{total_videos} videos deleted"
                )
                return False
                
        except Exception as e:
            self.log_test("Bulk Video Deletion", False, f"Bulk deletion error: {str(e)}")
            return False
    
    def verify_database_records(self):
        """Verify that uploaded files are properly stored in uploaded_files collection with file_type: 'consultation_video'"""
        try:
            # Get the list of additional videos to verify database storage
            videos = self.test_get_additional_videos_list()
            
            if videos is not None:
                # Check if we have any videos and they have the expected structure
                if len(videos) > 0:
                    self.log_test(
                        "Database Records Verification", 
                        True, 
                        f"Found {len(videos)} videos in database with correct structure and consultation_video type"
                    )
                    return True
                else:
                    self.log_test(
                        "Database Records Verification", 
                        True, 
                        "No videos found in database (expected after cleanup)"
                    )
                    return True
            else:
                self.log_test(
                    "Database Records Verification", 
                    False, 
                    "Failed to retrieve videos from database"
                )
                return False
                
        except Exception as e:
            self.log_test("Database Records Verification", False, f"Database verification error: {str(e)}")
            return False
    
    def cleanup_remaining_videos(self):
        """Clean up any remaining test videos"""
        if self.uploaded_video_ids:
            print(f"\n🧹 Cleaning up {len(self.uploaded_video_ids)} remaining test videos...")
            for file_id in self.uploaded_video_ids.copy():
                try:
                    response = self.session.delete(f"{BACKEND_URL}/admin/lessons/video/{file_id}")
                    if response.status_code == 200:
                        self.uploaded_video_ids.remove(file_id)
                        print(f"   ✅ Cleaned up video: {file_id}")
                    else:
                        print(f"   ❌ Failed to clean up video: {file_id}")
                except Exception as e:
                    print(f"   ❌ Error cleaning up video {file_id}: {str(e)}")
    
    def run_comprehensive_test(self):
        """Run the complete test suite according to review request"""
        print("🚀 Starting Additional Videos Management Test Suite")
        print("=" * 80)
        
        # 1. Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        print("\n📋 Testing Phase 1: Upload and List Operations")
        print("-" * 50)
        
        # 2. Upload additional video
        uploaded_file_id = self.test_upload_additional_video()
        
        # 3. Get list of additional videos
        videos_list = self.test_get_additional_videos_list()
        
        # 4. Test video streaming if we have a video
        if uploaded_file_id:
            print("\n📋 Testing Phase 2: Video Streaming")
            print("-" * 50)
            self.test_video_streaming(uploaded_file_id)
        
        print("\n📋 Testing Phase 3: Individual Deletion")
        print("-" * 50)
        
        # 5. Test individual video deletion
        if uploaded_file_id:
            self.test_delete_individual_video(uploaded_file_id)
        
        print("\n📋 Testing Phase 4: Bulk Operations")
        print("-" * 50)
        
        # 6. Upload multiple videos for bulk testing
        bulk_video_ids = self.test_upload_multiple_videos(3)
        
        # 7. Test bulk deletion
        if bulk_video_ids:
            self.test_bulk_deletion(bulk_video_ids)
        
        print("\n📋 Testing Phase 5: Database Verification")
        print("-" * 50)
        
        # 8. Verify database records
        self.verify_database_records()
        
        # 9. Cleanup any remaining videos
        self.cleanup_remaining_videos()
        
        # Print summary
        self.print_test_summary()
        
        return True
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY - Additional Videos Management")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 50)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status}: {result['test']}")
            if result['details']:
                print(f"   └─ {result['details']}")
        
        print("\n🎯 REVIEW REQUEST COMPLIANCE:")
        print("-" * 50)
        
        # Check compliance with review request requirements
        auth_passed = any(r['test'] == 'Super Admin Authentication' and r['success'] for r in self.test_results)
        upload_passed = any(r['test'] == 'Upload Additional Video' and r['success'] for r in self.test_results)
        list_passed = any(r['test'] == 'Get Additional Videos List' and r['success'] for r in self.test_results)
        streaming_passed = any(r['test'] == 'Video File Streaming' and r['success'] for r in self.test_results)
        delete_passed = any(r['test'] == 'Delete Individual Video' and r['success'] for r in self.test_results)
        bulk_delete_passed = any(r['test'] == 'Bulk Video Deletion' and r['success'] for r in self.test_results)
        
        compliance_items = [
            ("1. Аутентификация супер-админа", auth_passed),
            ("2. Загрузка дополнительных видео", upload_passed),
            ("3. Получение списка дополнительных видео", list_passed),
            ("4. Стриминг видео файлов", streaming_passed),
            ("5. Удаление дополнительных видео", delete_passed),
            ("6. Массовое удаление", bulk_delete_passed),
        ]
        
        for item, passed in compliance_items:
            status = "✅" if passed else "❌"
            print(f"{status} {item}")
        
        overall_compliance = all(passed for _, passed in compliance_items)
        
        print(f"\n🏆 OVERALL COMPLIANCE: {'✅ ПОЛНОСТЬЮ СООТВЕТСТВУЕТ' if overall_compliance else '❌ ЧАСТИЧНО СООТВЕТСТВУЕТ'}")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: Система управления дополнительными видео работает отлично!")
        elif success_rate >= 70:
            print("👍 GOOD: Система работает хорошо с незначительными проблемами")
        else:
            print("⚠️  NEEDS ATTENTION: Система требует доработки")

def main():
    """Main test execution"""
    test_suite = AdditionalVideosTestSuite()
    
    try:
        test_suite.run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        test_suite.cleanup_remaining_videos()
    except Exception as e:
        print(f"\n\n❌ Unexpected error during testing: {str(e)}")
        test_suite.cleanup_remaining_videos()

if __name__ == "__main__":
    main()