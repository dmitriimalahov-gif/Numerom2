#!/usr/bin/env python3
"""
Consultation Admin Rights Test - Review Request Specific
Testing the FIXED file upload functionality for personal consultations.

ISSUE WAS: 
- 403 Forbidden errors when uploading video/PDF files
- Required super admin rights instead of regular admin rights

FIXES:
- Changed all consultation endpoints from require_super_admin=True to require_super_admin=False
- Now regular admins can upload files

TEST SCENARIO:
1. Authenticate as dmitrii.malahov@gmail.com (check if regular admin or super admin)
2. Test POST /api/admin/consultations/upload-video - should work for regular admins
3. Test POST /api/admin/consultations/upload-pdf - should work for regular admins  
4. Test POST /api/admin/consultations/upload-subtitles - should work for regular admins
5. Test POST /api/admin/consultations - creating consultation
6. Test PUT /api/admin/consultations/{id} - updating consultation
7. Test GET /api/admin/consultations - getting consultation list

Using credentials: dmitrii.malahov@gmail.com / 756bvy67H
"""

import requests
import json
import os
import tempfile
from pathlib import Path
import time

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_EMAIL = "dmitrii.malahov@gmail.com"
TEST_PASSWORD = "756bvy67H"

class ConsultationAdminTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.is_super_admin = None
        self.is_admin = None
        self.consultation_id = None
        self.video_file_id = None
        self.pdf_file_id = None
        self.subtitles_file_id = None
        
    def log(self, message):
        print(f"[TEST] {message}")
        
    def authenticate(self):
        """Authenticate and check admin status"""
        self.log("🔐 Authenticating and checking admin status...")
        
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
        
        if response.status_code != 200:
            raise Exception(f"Authentication failed: {response.status_code} - {response.text}")
            
        data = response.json()
        self.auth_token = data['access_token']
        self.user_id = data['user']['id']
        self.is_super_admin = data['user'].get('is_super_admin', False)
        self.is_admin = data['user'].get('is_admin', False)
        
        # Set authorization header for future requests
        self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
        
        self.log(f"✅ Authenticated successfully as {TEST_EMAIL}")
        self.log(f"   User ID: {self.user_id}")
        self.log(f"   Credits: {data['user'].get('credits_remaining', 'N/A')}")
        self.log(f"   Is Admin: {self.is_admin}")
        self.log(f"   Is Super Admin: {self.is_super_admin}")
        
        # Determine admin status for testing
        if self.is_super_admin:
            self.log("⚠️  User is SUPER ADMIN - testing super admin access to consultation endpoints")
        elif self.is_admin:
            self.log("✅ User is REGULAR ADMIN - perfect for testing the fix!")
        else:
            self.log("❌ User is NOT ADMIN - this will test if endpoints properly reject non-admins")
        
        return True
        
    def test_upload_video(self):
        """Test POST /api/admin/consultations/upload-video"""
        self.log("🎥 Testing video upload for consultations...")
        
        # Create a dummy video file for testing
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            # Write some dummy video data
            temp_file.write(b'DUMMY_VIDEO_DATA_FOR_CONSULTATION_TESTING' * 1000)
            temp_file_path = temp_file.name
            
        try:
            with open(temp_file_path, 'rb') as video_file:
                files = {
                    'file': ('test_consultation_video.mp4', video_file, 'video/mp4')
                }
                
                response = self.session.post(f"{BACKEND_URL}/admin/consultations/upload-video", files=files)
                
            self.log(f"   Response Status: {response.status_code}")
            
            if response.status_code == 403:
                self.log("❌ 403 Forbidden - Admin rights insufficient (BUG NOT FIXED)")
                return False
            elif response.status_code != 200:
                self.log(f"❌ Upload failed: {response.status_code} - {response.text}")
                return False
                
            result = response.json()
            self.video_file_id = result['file_id']
            
            self.log(f"✅ Video uploaded successfully")
            self.log(f"   File ID: {self.video_file_id}")
            self.log(f"   Filename: {result['filename']}")
            self.log(f"   Video URL: {result['video_url']}")
            
        finally:
            # Clean up temp file
            os.unlink(temp_file_path)
            
        return True
        
    def test_upload_pdf(self):
        """Test POST /api/admin/consultations/upload-pdf"""
        self.log("📄 Testing PDF upload for consultations...")
        
        # Create a dummy PDF file for testing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            # Write minimal PDF content
            pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test PDF for consultation) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
299
%%EOF"""
            temp_file.write(pdf_content)
            temp_file_path = temp_file.name
            
        try:
            with open(temp_file_path, 'rb') as pdf_file:
                files = {
                    'file': ('test_consultation_document.pdf', pdf_file, 'application/pdf')
                }
                
                response = self.session.post(f"{BACKEND_URL}/admin/consultations/upload-pdf", files=files)
                
            self.log(f"   Response Status: {response.status_code}")
            
            if response.status_code == 403:
                self.log("❌ 403 Forbidden - Admin rights insufficient (BUG NOT FIXED)")
                return False
            elif response.status_code != 200:
                self.log(f"❌ Upload failed: {response.status_code} - {response.text}")
                return False
                
            result = response.json()
            self.pdf_file_id = result['file_id']
            
            self.log(f"✅ PDF uploaded successfully")
            self.log(f"   File ID: {self.pdf_file_id}")
            self.log(f"   Filename: {result['filename']}")
            self.log(f"   PDF URL: {result['pdf_url']}")
            
        finally:
            # Clean up temp file
            os.unlink(temp_file_path)
            
        return True
        
    def test_upload_subtitles(self):
        """Test POST /api/admin/consultations/upload-subtitles"""
        self.log("📝 Testing subtitles upload for consultations...")
        
        # Create a dummy subtitles file for testing
        with tempfile.NamedTemporaryFile(suffix='.vtt', delete=False) as temp_file:
            # Write VTT subtitle content
            vtt_content = b"""WEBVTT

00:00:00.000 --> 00:00:05.000
Welcome to the consultation

00:00:05.000 --> 00:00:10.000
This is a test subtitle file

00:00:10.000 --> 00:00:15.000
For testing consultation uploads
"""
            temp_file.write(vtt_content)
            temp_file_path = temp_file.name
            
        try:
            with open(temp_file_path, 'rb') as subtitles_file:
                files = {
                    'file': ('test_consultation_subtitles.vtt', subtitles_file, 'text/vtt')
                }
                
                response = self.session.post(f"{BACKEND_URL}/admin/consultations/upload-subtitles", files=files)
                
            self.log(f"   Response Status: {response.status_code}")
            
            if response.status_code == 403:
                self.log("❌ 403 Forbidden - Admin rights insufficient (BUG NOT FIXED)")
                return False
            elif response.status_code != 200:
                self.log(f"❌ Upload failed: {response.status_code} - {response.text}")
                return False
                
            result = response.json()
            self.subtitles_file_id = result['file_id']
            
            self.log(f"✅ Subtitles uploaded successfully")
            self.log(f"   File ID: {self.subtitles_file_id}")
            self.log(f"   Filename: {result['filename']}")
            
        finally:
            # Clean up temp file
            os.unlink(temp_file_path)
            
        return True
        
    def test_create_consultation(self):
        """Test POST /api/admin/consultations"""
        self.log("📝 Testing consultation creation...")
        
        consultation_data = {
            "id": f"test_admin_consultation_{int(time.time())}",
            "title": "Тестовая консультация для проверки прав админа",
            "description": "Консультация для тестирования исправленных прав доступа",
            "assigned_user_id": self.user_id,
            "cost_credits": 5000,
            "is_active": True
        }
        
        response = self.session.post(f"{BACKEND_URL}/admin/consultations", json=consultation_data)
        
        self.log(f"   Response Status: {response.status_code}")
        
        if response.status_code == 403:
            self.log("❌ 403 Forbidden - Admin rights insufficient (BUG NOT FIXED)")
            return False
        elif response.status_code != 200:
            self.log(f"❌ Creation failed: {response.status_code} - {response.text}")
            return False
            
        result = response.json()
        self.consultation_id = consultation_data["id"]
        
        self.log(f"✅ Consultation created successfully")
        self.log(f"   Consultation ID: {self.consultation_id}")
        self.log(f"   Title: {consultation_data['title']}")
        
        return True
        
    def test_update_consultation(self):
        """Test PUT /api/admin/consultations/{id}"""
        self.log("🔧 Testing consultation update...")
        
        if not self.consultation_id:
            self.log("❌ No consultation ID available for update test")
            return False
            
        update_data = {
            "video_file_id": self.video_file_id,
            "pdf_file_id": self.pdf_file_id,
            "subtitles_file_id": self.subtitles_file_id,
            "description": "Консультация обновлена с видео, PDF и субтитрами"
        }
        
        response = self.session.put(f"{BACKEND_URL}/admin/consultations/{self.consultation_id}", json=update_data)
        
        self.log(f"   Response Status: {response.status_code}")
        
        if response.status_code == 403:
            self.log("❌ 403 Forbidden - Admin rights insufficient (BUG NOT FIXED)")
            return False
        elif response.status_code != 200:
            self.log(f"❌ Update failed: {response.status_code} - {response.text}")
            return False
            
        result = response.json()
        
        self.log(f"✅ Consultation updated successfully")
        self.log(f"   Video File ID: {self.video_file_id}")
        self.log(f"   PDF File ID: {self.pdf_file_id}")
        self.log(f"   Subtitles File ID: {self.subtitles_file_id}")
        
        return True
        
    def test_get_consultations(self):
        """Test GET /api/admin/consultations"""
        self.log("📋 Testing consultation list retrieval...")
        
        response = self.session.get(f"{BACKEND_URL}/admin/consultations")
        
        self.log(f"   Response Status: {response.status_code}")
        
        if response.status_code == 403:
            self.log("❌ 403 Forbidden - Admin rights insufficient (BUG NOT FIXED)")
            return False
        elif response.status_code != 200:
            self.log(f"❌ Get consultations failed: {response.status_code} - {response.text}")
            return False
            
        consultations = response.json()
        
        self.log(f"✅ Consultations retrieved successfully")
        self.log(f"   Total consultations: {len(consultations)}")
        
        # Find our test consultation
        test_consultation = None
        for consultation in consultations:
            if consultation.get('id') == self.consultation_id:
                test_consultation = consultation
                break
                
        if test_consultation:
            self.log(f"✅ Test consultation found in list")
            self.log(f"   Has video_file_id: {bool(test_consultation.get('video_file_id'))}")
            self.log(f"   Has pdf_file_id: {bool(test_consultation.get('pdf_file_id'))}")
            self.log(f"   Has subtitles_file_id: {bool(test_consultation.get('subtitles_file_id'))}")
        else:
            self.log(f"⚠️  Test consultation not found in list")
        
        return True
        
    def test_file_access(self):
        """Test that uploaded files are accessible"""
        self.log("🔍 Testing file access...")
        
        success_count = 0
        total_tests = 0
        
        # Test video access
        if self.video_file_id:
            total_tests += 1
            response = self.session.get(f"{BACKEND_URL}/consultations/video/{self.video_file_id}")
            if response.status_code == 200:
                success_count += 1
                self.log(f"✅ Video file accessible (Content-Type: {response.headers.get('content-type', 'N/A')})")
            else:
                self.log(f"❌ Video file not accessible: {response.status_code}")
                
        # Test PDF access
        if self.pdf_file_id:
            total_tests += 1
            response = self.session.get(f"{BACKEND_URL}/consultations/pdf/{self.pdf_file_id}")
            if response.status_code == 200:
                success_count += 1
                self.log(f"✅ PDF file accessible (Content-Type: {response.headers.get('content-type', 'N/A')})")
            else:
                self.log(f"❌ PDF file not accessible: {response.status_code}")
                
        self.log(f"📊 File access results: {success_count}/{total_tests} files accessible")
        
        return success_count == total_tests
        
    def run_all_tests(self):
        """Run the complete test scenario"""
        self.log("🚀 Starting Consultation Admin Rights Test Suite")
        self.log("=" * 70)
        
        test_results = []
        
        try:
            # Authentication and admin status check
            self.authenticate()
            
            # Test all consultation endpoints
            test_results.append(("Video Upload", self.test_upload_video()))
            test_results.append(("PDF Upload", self.test_upload_pdf()))
            test_results.append(("Subtitles Upload", self.test_upload_subtitles()))
            test_results.append(("Create Consultation", self.test_create_consultation()))
            test_results.append(("Update Consultation", self.test_update_consultation()))
            test_results.append(("Get Consultations", self.test_get_consultations()))
            test_results.append(("File Access", self.test_file_access()))
            
            # Summary
            self.log("=" * 70)
            self.log("📊 TEST RESULTS SUMMARY:")
            
            passed_tests = 0
            total_tests = len(test_results)
            
            for test_name, result in test_results:
                status = "✅ PASS" if result else "❌ FAIL"
                self.log(f"   {test_name}: {status}")
                if result:
                    passed_tests += 1
            
            self.log(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
            
            if passed_tests == total_tests:
                self.log("🎉 ALL TESTS PASSED!")
                if self.is_super_admin:
                    self.log("✅ Super admin can access all consultation endpoints (expected)")
                elif self.is_admin:
                    self.log("✅ Regular admin can access all consultation endpoints (FIX CONFIRMED!)")
                else:
                    self.log("⚠️  Non-admin user can access consultation endpoints (unexpected)")
                return True
            else:
                self.log("💥 SOME TESTS FAILED!")
                if not self.is_admin and not self.is_super_admin:
                    self.log("✅ Non-admin user properly blocked from consultation endpoints (expected)")
                else:
                    self.log("❌ Admin user blocked from consultation endpoints (BUG NOT FIXED)")
                return False
                
        except Exception as e:
            self.log("=" * 70)
            self.log(f"❌ TEST SUITE FAILED: {str(e)}")
            return False

def main():
    """Main test execution"""
    tester = ConsultationAdminTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 CONCLUSION: Consultation admin rights fix is working correctly!")
        print("Regular admins can now upload files for personal consultations.")
        exit(0)
    else:
        print("\n💥 CONCLUSION: Issues found with consultation admin rights!")
        exit(1)

if __name__ == "__main__":
    main()