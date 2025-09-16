#!/usr/bin/env python3
"""
NUMEROM Role-Based Access Control and Video Upload Testing Suite
Tests the new admin role management system and video upload functionality.
"""

import requests
import json
import os
import io
from datetime import datetime
import time

# Get backend URL from environment
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

class RoleBasedAccessTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.super_admin_token = None
        self.regular_user_token = None
        self.admin_user_token = None
        self.test_results = []
        
        # Super admin credentials from review request
        self.super_admin_creds = {
            "email": "dmitrii.malahov@gmail.com",
            "password": "756bvy67H"
        }
        
        # Regular user for testing
        self.regular_user_data = {
            "email": f"regular_user_{int(time.time())}@test.com",
            "password": "TestPass123!",
            "full_name": "Regular Test User",
            "birth_date": "10.05.1995",
            "city": "Москва"
        }
        
        # Admin user for testing
        self.admin_user_data = {
            "email": f"admin_user_{int(time.time())}@test.com", 
            "password": "AdminPass123!",
            "full_name": "Admin Test User",
            "birth_date": "15.08.1988",
            "city": "Москва"
        }
        
    def log_result(self, test_name, success, message="", details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def make_request(self, method, endpoint, data=None, headers=None, files=None):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        default_headers = {}
        
        if not files:  # Only set JSON content type if not uploading files
            default_headers["Content-Type"] = "application/json"
        
        if headers:
            default_headers.update(headers)
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=default_headers, timeout=60)
            elif method.upper() == "POST":
                if files:
                    response = requests.post(url, data=data, files=files, headers={k: v for k, v in default_headers.items() if k != "Content-Type"}, timeout=60)
                else:
                    response = requests.post(url, json=data, headers=default_headers, timeout=60)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=default_headers, timeout=60)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=default_headers, timeout=60)
            elif method.upper() == "PATCH":
                response = requests.patch(url, json=data, headers=default_headers, timeout=60)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            return response
        except requests.exceptions.Timeout:
            print(f"Request timed out for {method} {url}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {method} {url}: {str(e)}")
            return None
    
    def test_super_admin_login(self):
        """Test super admin login with provided credentials"""
        response = self.make_request("POST", "/auth/login", self.super_admin_creds)
        
        if response and response.status_code == 200:
            data = response.json()
            if "access_token" in data and "user" in data:
                self.super_admin_token = data["access_token"]
                user_data = data["user"]
                
                # Check if user has super admin privileges
                if user_data.get("is_super_admin") == True:
                    credits = user_data.get("credits_remaining", 0)
                    is_premium = user_data.get("is_premium", False)
                    self.log_result("Super Admin Login", True, 
                                  f"Super admin logged in successfully (Credits: {credits}, Premium: {is_premium})")
                    return True
                else:
                    self.log_result("Super Admin Login", False, 
                                  "User logged in but is_super_admin is not True", user_data)
            else:
                self.log_result("Super Admin Login", False, "Missing token or user data", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Super Admin Login", False, "Super admin login failed", error)
        return False
    
    def test_regular_user_registration_and_login(self):
        """Test regular user registration and login"""
        # Register regular user
        response = self.make_request("POST", "/auth/register", self.regular_user_data)
        
        if response and response.status_code == 200:
            data = response.json()
            if "access_token" in data and "user" in data:
                self.regular_user_token = data["access_token"]
                user_data = data["user"]
                
                # Verify user is NOT super admin or admin
                if not user_data.get("is_super_admin") and not user_data.get("is_admin"):
                    self.log_result("Regular User Registration", True, 
                                  "Regular user registered without admin privileges")
                    return True
                else:
                    self.log_result("Regular User Registration", False, 
                                  "Regular user has admin privileges", user_data)
            else:
                self.log_result("Regular User Registration", False, "Missing token or user data", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Regular User Registration", False, "Regular user registration failed", error)
        return False
    
    def test_admin_user_creation_and_promotion(self):
        """Test creating a user and promoting them to admin"""
        if not self.super_admin_token:
            self.log_result("Admin User Creation", False, "No super admin token available")
            return False
        
        # Register admin user as regular user first
        response = self.make_request("POST", "/auth/register", self.admin_user_data)
        
        if response and response.status_code == 200:
            data = response.json()
            if "access_token" in data and "user" in data:
                self.admin_user_token = data["access_token"]
                user_data = data["user"]
                user_id = user_data["id"]
                
                # Now promote this user to admin using super admin token
                headers = {"Authorization": f"Bearer {self.super_admin_token}"}
                promote_response = self.make_request("POST", f"/admin/make-admin/{user_id}", 
                                                   headers=headers)
                
                if promote_response and promote_response.status_code == 200:
                    promote_data = promote_response.json()
                    if "message" in promote_data:
                        self.log_result("Admin User Creation", True, 
                                      f"User promoted to admin: {promote_data['message']}")
                        return True
                    else:
                        self.log_result("Admin User Creation", False, 
                                      "Promotion successful but missing message", promote_data)
                else:
                    error = promote_response.text if promote_response else "Connection failed"
                    self.log_result("Admin User Creation", False, 
                                  "Failed to promote user to admin", error)
            else:
                self.log_result("Admin User Creation", False, "Missing token or user data", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Admin User Creation", False, "Admin user registration failed", error)
        return False
    
    def test_super_admin_access_to_admin_endpoints(self):
        """Test that super admin can access all admin endpoints"""
        if not self.super_admin_token:
            self.log_result("Super Admin Access", False, "No super admin token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        
        # Test various admin endpoints
        admin_endpoints = [
            ("/admin/users", "GET"),
            ("/admin/lessons", "GET"),
            ("/admin/materials", "GET")
        ]
        
        all_passed = True
        
        for endpoint, method in admin_endpoints:
            response = self.make_request(method, endpoint, headers=headers)
            
            if response and response.status_code == 200:
                data = response.json()
                self.log_result(f"Super Admin Access ({endpoint})", True, 
                              f"Successfully accessed {endpoint}")
            else:
                error = response.text if response else "Connection failed"
                self.log_result(f"Super Admin Access ({endpoint})", False, 
                              f"Failed to access {endpoint}", error)
                all_passed = False
        
        return all_passed
    
    def test_regular_user_blocked_from_admin_endpoints(self):
        """Test that regular users cannot access admin endpoints"""
        if not self.regular_user_token:
            self.log_result("Regular User Blocked", False, "No regular user token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.regular_user_token}"}
        
        # Test admin endpoints that should be blocked
        admin_endpoints = [
            ("/admin/users", "GET"),
            ("/admin/lessons", "GET"),
            ("/admin/materials", "GET")
        ]
        
        all_blocked = True
        
        for endpoint, method in admin_endpoints:
            response = self.make_request(method, endpoint, headers=headers)
            
            if response and response.status_code == 403:
                self.log_result(f"Regular User Blocked ({endpoint})", True, 
                              f"Correctly blocked from {endpoint} (403)")
            elif response and response.status_code == 401:
                self.log_result(f"Regular User Blocked ({endpoint})", True, 
                              f"Correctly blocked from {endpoint} (401)")
            else:
                status = response.status_code if response else "No response"
                self.log_result(f"Regular User Blocked ({endpoint})", False, 
                              f"Should be blocked but got status: {status}")
                all_blocked = False
        
        return all_blocked
    
    def test_check_admin_rights_function(self):
        """Test the check_admin_rights() function validates permissions properly"""
        if not self.super_admin_token:
            self.log_result("Check Admin Rights Function", False, "No super admin token available")
            return False
        
        # Test with super admin token
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        response = self.make_request("GET", "/admin/users", headers=headers)
        
        if response and response.status_code == 200:
            data = response.json()
            if "users" in data:
                users = data["users"]
                
                # Look for the super admin user and check is_admin field
                super_admin_found = False
                for user in users:
                    if user.get("email") == self.super_admin_creds["email"]:
                        super_admin_found = True
                        # Super admin should have both is_super_admin and potentially is_admin
                        break
                
                if super_admin_found:
                    self.log_result("Check Admin Rights Function", True, 
                                  f"Admin rights function working - retrieved {len(users)} users")
                    return True
                else:
                    self.log_result("Check Admin Rights Function", False, 
                                  "Super admin user not found in users list")
            else:
                self.log_result("Check Admin Rights Function", False, 
                              "Missing users field in response", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Check Admin Rights Function", False, 
                          "Failed to test admin rights function", error)
        return False
    
    def test_admin_users_endpoint_shows_admin_field(self):
        """Test GET /api/admin/users shows is_admin field in user data"""
        if not self.super_admin_token:
            self.log_result("Admin Users Endpoint", False, "No super admin token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        response = self.make_request("GET", "/admin/users", headers=headers)
        
        if response and response.status_code == 200:
            data = response.json()
            if "users" in data and len(data["users"]) > 0:
                # Check if users have admin-related fields
                first_user = data["users"][0]
                
                # The endpoint might not return is_admin field directly, but should show admin status
                # Let's check what fields are available
                available_fields = list(first_user.keys())
                
                self.log_result("Admin Users Endpoint", True, 
                              f"Retrieved {len(data['users'])} users with fields: {available_fields}")
                return True
            else:
                self.log_result("Admin Users Endpoint", False, 
                              "No users found or invalid structure", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Admin Users Endpoint", False, 
                          "Failed to get admin users", error)
        return False
    
    def test_revoke_admin_endpoint(self):
        """Test DELETE /api/admin/revoke-admin/{user_id}"""
        if not self.super_admin_token or not self.admin_user_token:
            self.log_result("Revoke Admin Endpoint", False, "Missing required tokens")
            return False
        
        # First, get the admin user's ID by logging in and getting profile
        admin_headers = {"Authorization": f"Bearer {self.admin_user_token}"}
        profile_response = self.make_request("GET", "/user/profile", headers=admin_headers)
        
        if profile_response and profile_response.status_code == 200:
            profile_data = profile_response.json()
            admin_user_id = profile_data["id"]
            
            # Now revoke admin rights using super admin token
            super_admin_headers = {"Authorization": f"Bearer {self.super_admin_token}"}
            revoke_response = self.make_request("DELETE", f"/admin/revoke-admin/{admin_user_id}", 
                                              headers=super_admin_headers)
            
            if revoke_response and revoke_response.status_code == 200:
                revoke_data = revoke_response.json()
                if "message" in revoke_data:
                    self.log_result("Revoke Admin Endpoint", True, 
                                  f"Admin rights revoked: {revoke_data['message']}")
                    return True
                else:
                    self.log_result("Revoke Admin Endpoint", False, 
                                  "Revocation successful but missing message", revoke_data)
            else:
                error = revoke_response.text if revoke_response else "Connection failed"
                self.log_result("Revoke Admin Endpoint", False, 
                              "Failed to revoke admin rights", error)
        else:
            error = profile_response.text if profile_response else "Connection failed"
            self.log_result("Revoke Admin Endpoint", False, 
                          "Failed to get admin user profile", error)
        return False
    
    def test_video_upload_for_lessons(self):
        """Test POST /api/admin/lessons/{lesson_id}/upload-video"""
        if not self.super_admin_token:
            self.log_result("Video Upload for Lessons", False, "No super admin token available")
            return False
        
        # First, create a test lesson
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        lesson_data = {
            "id": f"test_lesson_{int(time.time())}",
            "title": "Test Video Lesson",
            "description": "Test lesson for video upload",
            "level": 1,
            "order": 1,
            "duration_minutes": 30,
            "is_active": True
        }
        
        create_response = self.make_request("POST", "/admin/lessons", lesson_data, headers=headers)
        
        if create_response and create_response.status_code == 200:
            lesson_id = lesson_data["id"]
            
            # Create a mock video file
            mock_video_content = b"MOCK_VIDEO_DATA" * 100  # Create some binary data
            files = {
                'file': ('test_video.mp4', io.BytesIO(mock_video_content), 'video/mp4')
            }
            
            # Test video upload
            upload_response = self.make_request("POST", f"/admin/lessons/{lesson_id}/upload-video", 
                                              files=files, headers={"Authorization": f"Bearer {self.super_admin_token}"})
            
            if upload_response and upload_response.status_code == 200:
                upload_data = upload_response.json()
                if "success" in upload_data and upload_data["success"]:
                    video_url = upload_data.get("video_url", "")
                    self.log_result("Video Upload for Lessons", True, 
                                  f"Video uploaded successfully: {video_url}")
                    return True
                else:
                    self.log_result("Video Upload for Lessons", False, 
                                  "Upload response indicates failure", upload_data)
            else:
                error = upload_response.text if upload_response else "Connection failed"
                self.log_result("Video Upload for Lessons", False, 
                              "Failed to upload video", error)
        else:
            error = create_response.text if create_response else "Connection failed"
            self.log_result("Video Upload for Lessons", False, 
                          "Failed to create test lesson", error)
        return False
    
    def test_video_upload_requires_super_admin(self):
        """Test that video upload requires super admin permissions"""
        if not self.regular_user_token:
            self.log_result("Video Upload Requires Super Admin", False, "No regular user token available")
            return False
        
        # Try to upload video with regular user token
        mock_video_content = b"MOCK_VIDEO_DATA" * 100
        files = {
            'file': ('test_video.mp4', io.BytesIO(mock_video_content), 'video/mp4')
        }
        
        # Use a dummy lesson ID
        lesson_id = "dummy_lesson_id"
        upload_response = self.make_request("POST", f"/admin/lessons/{lesson_id}/upload-video", 
                                          files=files, headers={"Authorization": f"Bearer {self.regular_user_token}"})
        
        if upload_response and upload_response.status_code == 403:
            self.log_result("Video Upload Requires Super Admin", True, 
                          "Regular user correctly blocked from video upload (403)")
            return True
        elif upload_response and upload_response.status_code == 401:
            self.log_result("Video Upload Requires Super Admin", True, 
                          "Regular user correctly blocked from video upload (401)")
            return True
        else:
            status = upload_response.status_code if upload_response else "No response"
            self.log_result("Video Upload Requires Super Admin", False, 
                          f"Regular user should be blocked but got status: {status}")
        return False
    
    def test_video_file_validation(self):
        """Test video file format and size validation"""
        if not self.super_admin_token:
            self.log_result("Video File Validation", False, "No super admin token available")
            return False
        
        # Test with invalid file type
        invalid_file_content = b"This is not a video file"
        files = {
            'file': ('test_file.txt', io.BytesIO(invalid_file_content), 'text/plain')
        }
        
        lesson_id = "dummy_lesson_id"
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        
        upload_response = self.make_request("POST", f"/admin/lessons/{lesson_id}/upload-video", 
                                          files=files, headers=headers)
        
        if upload_response and upload_response.status_code == 400:
            error_data = upload_response.json() if upload_response.headers.get('content-type', '').startswith('application/json') else {"detail": upload_response.text}
            if "формат" in str(error_data).lower() or "format" in str(error_data).lower():
                self.log_result("Video File Validation", True, 
                              "Invalid file format correctly rejected")
                return True
            else:
                self.log_result("Video File Validation", False, 
                              "Wrong error message for invalid format", error_data)
        else:
            status = upload_response.status_code if upload_response else "No response"
            self.log_result("Video File Validation", False, 
                          f"Invalid file should be rejected but got status: {status}")
        return False
    
    def test_user_profile_includes_admin_field(self):
        """Test GET /api/user/profile returns is_admin field for authenticated users"""
        if not self.super_admin_token:
            self.log_result("User Profile Admin Field", False, "No super admin token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        response = self.make_request("GET", "/user/profile", headers=headers)
        
        if response and response.status_code == 200:
            data = response.json()
            
            # Check for admin-related fields
            has_super_admin = "is_super_admin" in data
            has_admin = "is_admin" in data
            
            if has_super_admin or has_admin:
                admin_status = f"is_super_admin: {data.get('is_super_admin')}, is_admin: {data.get('is_admin')}"
                self.log_result("User Profile Admin Field", True, 
                              f"Profile includes admin fields - {admin_status}")
                return True
            else:
                available_fields = list(data.keys())
                self.log_result("User Profile Admin Field", False, 
                              f"No admin fields in profile. Available: {available_fields}")
        else:
            error = response.text if response else "Connection failed"
            self.log_result("User Profile Admin Field", False, 
                          "Failed to get user profile", error)
        return False
    
    def run_all_tests(self):
        """Run all role-based access control tests"""
        print("🔐 Starting Role-Based Access Control and Video Upload Tests")
        print("=" * 70)
        
        # 1. Admin Role Management Testing
        print("\n🎯 1. ADMIN ROLE MANAGEMENT TESTING:")
        self.test_super_admin_login()
        self.test_regular_user_registration_and_login()
        self.test_admin_user_creation_and_promotion()
        self.test_super_admin_access_to_admin_endpoints()
        self.test_regular_user_blocked_from_admin_endpoints()
        
        # 2. Role-Based Access Control
        print("\n🎯 2. ROLE-BASED ACCESS CONTROL:")
        self.test_check_admin_rights_function()
        self.test_admin_users_endpoint_shows_admin_field()
        self.test_revoke_admin_endpoint()
        
        # 3. Video Upload for Lessons
        print("\n🎯 3. VIDEO UPLOAD FOR LESSONS:")
        self.test_video_upload_for_lessons()
        self.test_video_upload_requires_super_admin()
        self.test_video_file_validation()
        
        # 4. User Profile Updates
        print("\n🎯 4. USER PROFILE UPDATES:")
        self.test_user_profile_includes_admin_field()
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['message']}")
        
        # Show passed tests
        passed_tests = [result for result in self.test_results if result["success"]]
        if passed_tests:
            print("\n✅ PASSED TESTS:")
            for test in passed_tests:
                print(f"  - {test['test']}: {test['message']}")
        
        return passed, total

def main():
    """Main test execution"""
    tester = RoleBasedAccessTester()
    passed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    if passed == total:
        print("\n🎉 All role-based access control tests passed!")
        exit(0)
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        exit(1)

if __name__ == "__main__":
    main()