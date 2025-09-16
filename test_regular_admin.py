#!/usr/bin/env python3
"""
Test Regular Admin Access to Consultation Endpoints
This test creates a regular admin user and tests the fixed consultation endpoints.

CRITICAL TEST: The fix changed require_super_admin=True to require_super_admin=False
This means regular admins should now be able to access consultation endpoints.
"""

import requests
import json
import tempfile
import os
import time

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"

# Test regular admin credentials
REGULAR_ADMIN_EMAIL = "test.admin@numerom.com"
REGULAR_ADMIN_PASSWORD = "testadmin123"

class RegularAdminTester:
    def __init__(self):
        self.session = requests.Session()
        self.super_admin_token = None
        self.regular_admin_token = None
        self.regular_admin_user_id = None
        
    def log(self, message):
        print(f"[TEST] {message}")
        
    def authenticate_super_admin(self):
        """Authenticate as super admin to create regular admin"""
        self.log("🔐 Authenticating as super admin...")
        
        login_data = {
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
        
        if response.status_code != 200:
            raise Exception(f"Super admin authentication failed: {response.status_code} - {response.text}")
            
        data = response.json()
        self.super_admin_token = data['access_token']
        
        self.log(f"✅ Super admin authenticated successfully")
        return True
        
    def create_regular_admin(self):
        """Create a regular admin user for testing"""
        self.log("👤 Creating regular admin user...")
        
        # First, try to register the user
        register_data = {
            "email": REGULAR_ADMIN_EMAIL,
            "password": REGULAR_ADMIN_PASSWORD,
            "full_name": "Test Regular Admin",
            "birth_date": "15.03.1990",
            "city": "Москва"
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/register", json=register_data)
        
        if response.status_code == 400 and "already exists" in response.text:
            self.log("ℹ️  Regular admin user already exists, proceeding with login...")
        elif response.status_code != 200:
            raise Exception(f"User registration failed: {response.status_code} - {response.text}")
        else:
            self.log("✅ Regular admin user registered successfully")
            
        # Login as the regular user
        login_data = {
            "email": REGULAR_ADMIN_EMAIL,
            "password": REGULAR_ADMIN_PASSWORD
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
        
        if response.status_code != 200:
            raise Exception(f"Regular user login failed: {response.status_code} - {response.text}")
            
        data = response.json()
        self.regular_admin_user_id = data['user']['id']
        
        # Now make this user an admin using super admin privileges
        headers = {'Authorization': f'Bearer {self.super_admin_token}'}
        response = requests.post(
            f"{BACKEND_URL}/admin/make-admin/{self.regular_admin_user_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to make user admin: {response.status_code} - {response.text}")
            
        self.log("✅ User granted admin rights successfully")
        
        # Login again to get updated token with admin rights
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
        
        if response.status_code != 200:
            raise Exception(f"Admin user login failed: {response.status_code} - {response.text}")
            
        data = response.json()
        self.regular_admin_token = data['access_token']
        
        self.log(f"✅ Regular admin authenticated")
        self.log(f"   User ID: {data['user']['id']}")
        self.log(f"   Is Admin: {data['user'].get('is_admin', False)}")
        self.log(f"   Is Super Admin: {data['user'].get('is_super_admin', False)}")
        
        # Verify this is a regular admin (not super admin)
        if data['user'].get('is_super_admin', False):
            raise Exception("User is super admin, not regular admin!")
            
        if not data['user'].get('is_admin', False):
            raise Exception("User is not admin!")
            
        return True
        
    def test_consultation_endpoints_as_regular_admin(self):
        """Test all consultation endpoints as regular admin"""
        self.log("🧪 Testing consultation endpoints as regular admin...")
        
        headers = {'Authorization': f'Bearer {self.regular_admin_token}'}
        test_results = []
        
        # Test 1: Upload video
        self.log("1️⃣ Testing video upload...")
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_file.write(b'DUMMY_VIDEO_DATA' * 1000)
            temp_file_path = temp_file.name
            
        try:
            with open(temp_file_path, 'rb') as video_file:
                files = {'file': ('test_video.mp4', video_file, 'video/mp4')}
                response = requests.post(f"{BACKEND_URL}/admin/consultations/upload-video", files=files, headers=headers)
                
            if response.status_code == 403:
                self.log("❌ Video upload: 403 Forbidden (BUG NOT FIXED)")
                test_results.append(("Video Upload", False))
            elif response.status_code == 200:
                self.log("✅ Video upload: Success")
                test_results.append(("Video Upload", True))
                video_result = response.json()
                video_file_id = video_result['file_id']
            else:
                self.log(f"❌ Video upload: {response.status_code} - {response.text}")
                test_results.append(("Video Upload", False))
                video_file_id = None
        finally:
            os.unlink(temp_file_path)
            
        # Test 2: Upload PDF
        self.log("2️⃣ Testing PDF upload...")
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer<</Size 4/Root 1 0 R>>
startxref
190
%%EOF"""
            temp_file.write(pdf_content)
            temp_file_path = temp_file.name
            
        try:
            with open(temp_file_path, 'rb') as pdf_file:
                files = {'file': ('test_document.pdf', pdf_file, 'application/pdf')}
                response = requests.post(f"{BACKEND_URL}/admin/consultations/upload-pdf", files=files, headers=headers)
                
            if response.status_code == 403:
                self.log("❌ PDF upload: 403 Forbidden (BUG NOT FIXED)")
                test_results.append(("PDF Upload", False))
            elif response.status_code == 200:
                self.log("✅ PDF upload: Success")
                test_results.append(("PDF Upload", True))
                pdf_result = response.json()
                pdf_file_id = pdf_result['file_id']
            else:
                self.log(f"❌ PDF upload: {response.status_code} - {response.text}")
                test_results.append(("PDF Upload", False))
                pdf_file_id = None
        finally:
            os.unlink(temp_file_path)
            
        # Test 3: Upload subtitles
        self.log("3️⃣ Testing subtitles upload...")
        with tempfile.NamedTemporaryFile(suffix='.vtt', delete=False) as temp_file:
            vtt_content = b"""WEBVTT

00:00:00.000 --> 00:00:05.000
Test subtitle
"""
            temp_file.write(vtt_content)
            temp_file_path = temp_file.name
            
        try:
            with open(temp_file_path, 'rb') as vtt_file:
                files = {'file': ('test_subtitles.vtt', vtt_file, 'text/vtt')}
                response = requests.post(f"{BACKEND_URL}/admin/consultations/upload-subtitles", files=files, headers=headers)
                
            if response.status_code == 403:
                self.log("❌ Subtitles upload: 403 Forbidden (BUG NOT FIXED)")
                test_results.append(("Subtitles Upload", False))
            elif response.status_code == 200:
                self.log("✅ Subtitles upload: Success")
                test_results.append(("Subtitles Upload", True))
            else:
                self.log(f"❌ Subtitles upload: {response.status_code} - {response.text}")
                test_results.append(("Subtitles Upload", False))
        finally:
            os.unlink(temp_file_path)
            
        # Test 4: Create consultation
        self.log("4️⃣ Testing consultation creation...")
        consultation_data = {
            "id": f"test_regular_admin_{int(time.time())}",
            "title": "Test Consultation by Regular Admin",
            "description": "Testing regular admin access",
            "assigned_user_id": self.regular_admin_user_id,
            "cost_credits": 1000,
            "is_active": True
        }
        
        response = requests.post(f"{BACKEND_URL}/admin/consultations", json=consultation_data, headers=headers)
        
        if response.status_code == 403:
            self.log("❌ Create consultation: 403 Forbidden (BUG NOT FIXED)")
            test_results.append(("Create Consultation", False))
            consultation_id = None
        elif response.status_code == 200:
            self.log("✅ Create consultation: Success")
            test_results.append(("Create Consultation", True))
            consultation_id = consultation_data["id"]
        else:
            self.log(f"❌ Create consultation: {response.status_code} - {response.text}")
            test_results.append(("Create Consultation", False))
            consultation_id = None
            
        # Test 5: Update consultation
        if consultation_id and video_file_id and pdf_file_id:
            self.log("5️⃣ Testing consultation update...")
            update_data = {
                "video_file_id": video_file_id,
                "pdf_file_id": pdf_file_id,
                "description": "Updated by regular admin"
            }
            
            response = requests.put(f"{BACKEND_URL}/admin/consultations/{consultation_id}", json=update_data, headers=headers)
            
            if response.status_code == 403:
                self.log("❌ Update consultation: 403 Forbidden (BUG NOT FIXED)")
                test_results.append(("Update Consultation", False))
            elif response.status_code == 200:
                self.log("✅ Update consultation: Success")
                test_results.append(("Update Consultation", True))
            else:
                self.log(f"❌ Update consultation: {response.status_code} - {response.text}")
                test_results.append(("Update Consultation", False))
        else:
            self.log("5️⃣ Skipping consultation update (missing prerequisites)")
            test_results.append(("Update Consultation", False))
            
        # Test 6: Get consultations
        self.log("6️⃣ Testing get consultations...")
        response = requests.get(f"{BACKEND_URL}/admin/consultations", headers=headers)
        
        if response.status_code == 403:
            self.log("❌ Get consultations: 403 Forbidden (BUG NOT FIXED)")
            test_results.append(("Get Consultations", False))
        elif response.status_code == 200:
            self.log("✅ Get consultations: Success")
            test_results.append(("Get Consultations", True))
            consultations = response.json()
            self.log(f"   Found {len(consultations)} consultations")
        else:
            self.log(f"❌ Get consultations: {response.status_code} - {response.text}")
            test_results.append(("Get Consultations", False))
            
        return test_results
        
    def run_all_tests(self):
        """Run the complete test scenario"""
        self.log("🚀 Starting Regular Admin Consultation Access Test")
        self.log("=" * 70)
        
        try:
            # Setup
            self.authenticate_super_admin()
            self.create_regular_admin()
            
            # Test consultation endpoints
            test_results = self.test_consultation_endpoints_as_regular_admin()
            
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
                self.log("✅ Regular admin can access all consultation endpoints")
                self.log("✅ FIX CONFIRMED: require_super_admin=False is working!")
                return True
            else:
                self.log("💥 SOME TESTS FAILED!")
                self.log("❌ Regular admin blocked from consultation endpoints")
                self.log("❌ BUG NOT FIXED: Still requires super admin rights")
                return False
                
        except Exception as e:
            self.log("=" * 70)
            self.log(f"❌ TEST SUITE FAILED: {str(e)}")
            return False

def main():
    """Main test execution"""
    tester = RegularAdminTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 CONCLUSION: Regular admin consultation access fix is working!")
        print("The change from require_super_admin=True to require_super_admin=False is successful.")
        exit(0)
    else:
        print("\n💥 CONCLUSION: Regular admin consultation access fix is NOT working!")
        exit(1)

if __name__ == "__main__":
    main()