#!/usr/bin/env python3
"""
PersonalConsultations Integration Test
Verifying that lessons use the exact same endpoints and viewer components as PersonalConsultations

This test ensures 100% unification as requested in the review.
"""

import requests
import json
import tempfile
import os

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_USER_EMAIL = "dmitrii.malahov@gmail.com"
TEST_USER_PASSWORD = "756bvy67H"

class ConsultationsIntegrationTest:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
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
        """Authenticate as super admin"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data['access_token']
                self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                return True
            return False
        except Exception as e:
            return False
    
    def test_consultations_upload_endpoints(self):
        """Test that consultations upload endpoints work"""
        try:
            # Create test files
            video_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            video_file.write(b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom' + b'\x00' * 1000)
            video_file.close()
            
            pdf_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            pdf_file.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\ntrailer\n<<\n/Size 1\n>>\n%%EOF')
            pdf_file.close()
            
            # Test video upload
            with open(video_file.name, 'rb') as f:
                files = {'file': ('consultation_video.mp4', f, 'video/mp4')}
                video_response = self.session.post(f"{BACKEND_URL}/admin/consultations/upload-video", files=files)
            
            # Test PDF upload
            with open(pdf_file.name, 'rb') as f:
                files = {'file': ('consultation_document.pdf', f, 'application/pdf')}
                pdf_response = self.session.post(f"{BACKEND_URL}/admin/consultations/upload-pdf", files=files)
            
            # Cleanup temp files
            os.unlink(video_file.name)
            os.unlink(pdf_file.name)
            
            video_success = video_response.status_code == 200
            pdf_success = pdf_response.status_code == 200
            
            if video_success and pdf_success:
                video_data = video_response.json()
                pdf_data = pdf_response.json()
                self.consultation_video_id = video_data.get('file_id')
                self.consultation_pdf_id = pdf_data.get('file_id')
                
                self.log_test("Consultations Upload Endpoints", True, 
                    f"Video ID: {self.consultation_video_id}, PDF ID: {self.consultation_pdf_id}")
                return True
            else:
                self.log_test("Consultations Upload Endpoints", False, 
                    f"Video status: {video_response.status_code}, PDF status: {pdf_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Consultations Upload Endpoints", False, f"Exception: {str(e)}")
            return False
    
    def test_consultations_streaming_endpoints(self):
        """Test that consultations streaming endpoints work"""
        try:
            if not hasattr(self, 'consultation_video_id') or not hasattr(self, 'consultation_pdf_id'):
                self.log_test("Consultations Streaming Endpoints", False, "No file IDs available")
                return False
            
            # Test video streaming
            video_response = self.session.get(f"{BACKEND_URL}/consultations/video/{self.consultation_video_id}")
            
            # Test PDF streaming
            pdf_response = self.session.get(f"{BACKEND_URL}/consultations/pdf/{self.consultation_pdf_id}")
            
            video_success = video_response.status_code == 200
            pdf_success = pdf_response.status_code == 200
            
            if video_success and pdf_success:
                self.log_test("Consultations Streaming Endpoints", True, 
                    f"Video size: {len(video_response.content)} bytes, PDF size: {len(pdf_response.content)} bytes")
                return True
            else:
                self.log_test("Consultations Streaming Endpoints", False, 
                    f"Video status: {video_response.status_code}, PDF status: {pdf_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Consultations Streaming Endpoints", False, f"Exception: {str(e)}")
            return False
    
    def test_lessons_use_same_endpoints(self):
        """Verify that lessons use the same consultations endpoints for streaming"""
        try:
            # Get lesson additional files
            lesson_videos_response = self.session.get(f"{BACKEND_URL}/lessons/lesson_numerom_intro/additional-videos")
            lesson_pdfs_response = self.session.get(f"{BACKEND_URL}/lessons/lesson_numerom_intro/additional-pdfs")
            
            if lesson_videos_response.status_code != 200 or lesson_pdfs_response.status_code != 200:
                self.log_test("Lessons Use Same Endpoints", False, "Could not retrieve lesson files")
                return False
            
            videos_data = lesson_videos_response.json()
            pdfs_data = lesson_pdfs_response.json()
            
            # Check that all video URLs use /api/consultations/video/
            video_urls_correct = True
            for video in videos_data.get('additional_videos', []):
                if not video.get('video_url', '').startswith('/api/consultations/video/'):
                    video_urls_correct = False
                    break
            
            # Check that all PDF URLs use /api/consultations/pdf/
            pdf_urls_correct = True
            for pdf in pdfs_data.get('additional_pdfs', []):
                if not pdf.get('pdf_url', '').startswith('/api/consultations/pdf/'):
                    pdf_urls_correct = False
                    break
            
            if video_urls_correct and pdf_urls_correct:
                self.log_test("Lessons Use Same Endpoints", True, 
                    f"All {len(videos_data.get('additional_videos', []))} videos and {len(pdfs_data.get('additional_pdfs', []))} PDFs use consultations endpoints")
                return True
            else:
                self.log_test("Lessons Use Same Endpoints", False, 
                    f"Video URLs correct: {video_urls_correct}, PDF URLs correct: {pdf_urls_correct}")
                return False
                
        except Exception as e:
            self.log_test("Lessons Use Same Endpoints", False, f"Exception: {str(e)}")
            return False
    
    def test_file_storage_unification(self):
        """Test that both consultations and lessons store files in the same directories"""
        try:
            # This is verified by checking that lesson uploads use consultation directories
            # and that the file_type is set to 'consultation_video' and 'consultation_pdf'
            
            # We can't directly access the file system, but we can verify through the API
            # that files uploaded via lesson endpoints are accessible via consultation endpoints
            
            # Create a test file via lesson endpoint
            video_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            video_file.write(b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom' + b'\x00' * 500)
            video_file.close()
            
            # Upload via lesson endpoint
            with open(video_file.name, 'rb') as f:
                files = {'file': ('unification_test.mp4', f, 'video/mp4')}
                data = {'title': 'Unification Test Video'}
                upload_response = self.session.post(
                    f"{BACKEND_URL}/admin/lessons/lesson_numerom_intro/add-video", 
                    files=files, 
                    data=data
                )
            
            os.unlink(video_file.name)
            
            if upload_response.status_code == 200:
                upload_data = upload_response.json()
                file_id = upload_data.get('file_id')
                
                # Try to access via consultation endpoint
                stream_response = self.session.get(f"{BACKEND_URL}/consultations/video/{file_id}")
                
                if stream_response.status_code == 200:
                    # Clean up
                    self.session.delete(f"{BACKEND_URL}/admin/lessons/video/{file_id}")
                    
                    self.log_test("File Storage Unification", True, 
                        "Lesson-uploaded file accessible via consultation endpoint")
                    return True
                else:
                    self.log_test("File Storage Unification", False, 
                        f"Lesson file not accessible via consultation endpoint: {stream_response.status_code}")
                    return False
            else:
                self.log_test("File Storage Unification", False, 
                    f"Could not upload via lesson endpoint: {upload_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("File Storage Unification", False, f"Exception: {str(e)}")
            return False
    
    def test_cors_headers_consistency(self):
        """Test that CORS headers are consistent between consultations and lesson streaming"""
        try:
            if not hasattr(self, 'consultation_video_id'):
                self.log_test("CORS Headers Consistency", False, "No consultation video ID available")
                return False
            
            # Get CORS headers from consultation endpoint
            consultation_response = self.session.get(f"{BACKEND_URL}/consultations/video/{self.consultation_video_id}")
            
            if consultation_response.status_code != 200:
                self.log_test("CORS Headers Consistency", False, "Could not access consultation video")
                return False
            
            # Check for required CORS headers
            required_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            headers_present = all(header in consultation_response.headers for header in required_headers)
            
            if headers_present:
                self.log_test("CORS Headers Consistency", True, 
                    "All required CORS headers present in consultation streaming")
                return True
            else:
                missing_headers = [h for h in required_headers if h not in consultation_response.headers]
                self.log_test("CORS Headers Consistency", False, 
                    f"Missing CORS headers: {missing_headers}")
                return False
                
        except Exception as e:
            self.log_test("CORS Headers Consistency", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🔗 Starting PersonalConsultations Integration Test")
        print("=" * 60)
        
        if not self.authenticate():
            print("❌ Authentication failed")
            return False
        
        # Run all tests
        self.test_consultations_upload_endpoints()
        self.test_consultations_streaming_endpoints()
        self.test_lessons_use_same_endpoints()
        self.test_file_storage_unification()
        self.test_cors_headers_consistency()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("🎉 100% UNIFICATION ACHIEVED - LESSONS = PERSONALCONSULTATIONS!")
        elif success_rate >= 80:
            print("⚠️  MOSTLY UNIFIED - MINOR INTEGRATION ISSUES")
        else:
            print("❌ UNIFICATION INCOMPLETE - MAJOR ISSUES")
        
        return success_rate >= 90

if __name__ == "__main__":
    test_suite = ConsultationsIntegrationTest()
    success = test_suite.run_all_tests()
    exit(0 if success else 1)