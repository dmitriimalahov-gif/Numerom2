#!/usr/bin/env python3
"""
Backend Testing Suite for NUMEROM Admin Materials Management
Testing new admin endpoints for materials CRUD operations and video upload
"""

import requests
import json
import io
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"

class AdminMaterialsTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_material_id = None
        self.test_video_id = None
        self.results = []
        
    def log_result(self, test_name, success, details="", response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data
        }
        self.results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()

    def authenticate_super_admin(self):
        """Authenticate as super admin"""
        print("🔐 Authenticating as Super Admin...")
        
        login_data = {
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                user_info = data.get('user', {})
                
                # Set authorization header for future requests
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}',
                    'Content-Type': 'application/json'
                })
                
                self.log_result(
                    "Super Admin Authentication",
                    True,
                    f"Logged in as {user_info.get('email')} with {user_info.get('credits_remaining')} credits, is_super_admin: {user_info.get('is_super_admin')}"
                )
                return True
            else:
                self.log_result(
                    "Super Admin Authentication",
                    False,
                    f"Login failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Super Admin Authentication",
                False,
                f"Authentication error: {str(e)}"
            )
            return False

    def test_get_all_materials(self):
        """Test GET /api/admin/materials - получение всех материалов"""
        print("📋 Testing GET /api/admin/materials...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/materials")
            
            if response.status_code == 200:
                data = response.json()
                materials = data.get('materials', [])
                total_count = data.get('total_count', 0)
                
                self.log_result(
                    "GET /api/admin/materials",
                    True,
                    f"Retrieved {total_count} materials successfully",
                    f"Sample: {materials[:2] if materials else 'No materials found'}"
                )
                return True
            else:
                self.log_result(
                    "GET /api/admin/materials",
                    False,
                    f"Failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result(
                "GET /api/admin/materials",
                False,
                f"Request error: {str(e)}"
            )
            return False

    def test_create_material(self):
        """Test POST /api/admin/materials - создание нового материала"""
        print("➕ Testing POST /api/admin/materials...")
        
        # Test material data as specified in review request
        material_data = {
            "title": "Тестовый урок",
            "description": "Описание тестового урока",
            "content": "Содержание урока",
            "video_url": "https://www.youtube.com/watch?v=test",
            "order": 1,
            "is_active": True
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/admin/materials", json=material_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.test_material_id = data.get('material_id')
                    self.log_result(
                        "POST /api/admin/materials",
                        True,
                        f"Material created successfully with ID: {self.test_material_id}",
                        data
                    )
                    return True
                else:
                    self.log_result(
                        "POST /api/admin/materials",
                        False,
                        "Response indicates failure",
                        data
                    )
                    return False
            else:
                self.log_result(
                    "POST /api/admin/materials",
                    False,
                    f"Failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result(
                "POST /api/admin/materials",
                False,
                f"Request error: {str(e)}"
            )
            return False

    def test_update_material(self):
        """Test PUT /api/admin/materials/{id} - обновление материала"""
        print("✏️ Testing PUT /api/admin/materials/{id}...")
        
        if not self.test_material_id:
            self.log_result(
                "PUT /api/admin/materials/{id}",
                False,
                "No test material ID available for update test"
            )
            return False
        
        # Updated material data
        updated_data = {
            "title": "Обновленный тестовый урок",
            "description": "Обновленное описание тестового урока",
            "content": "Обновленное содержание урока",
            "video_url": "https://www.youtube.com/watch?v=updated_test",
            "order": 2,
            "is_active": True
        }
        
        try:
            response = self.session.put(
                f"{BACKEND_URL}/admin/materials/{self.test_material_id}", 
                json=updated_data
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_result(
                        "PUT /api/admin/materials/{id}",
                        True,
                        f"Material {self.test_material_id} updated successfully",
                        data
                    )
                    return True
                else:
                    self.log_result(
                        "PUT /api/admin/materials/{id}",
                        False,
                        "Response indicates failure",
                        data
                    )
                    return False
            else:
                self.log_result(
                    "PUT /api/admin/materials/{id}",
                    False,
                    f"Failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result(
                "PUT /api/admin/materials/{id}",
                False,
                f"Request error: {str(e)}"
            )
            return False

    def test_upload_video(self):
        """Test POST /api/admin/upload-video - загрузка видео файла (с mock данными)"""
        print("🎥 Testing POST /api/admin/upload-video...")
        
        # Create mock video file data
        mock_video_content = b"MOCK_VIDEO_DATA_FOR_TESTING" * 100  # Small mock video data
        
        try:
            # Prepare multipart form data
            files = {
                'file': ('test_video.mp4', io.BytesIO(mock_video_content), 'video/mp4')
            }
            
            # Remove Content-Type header for multipart upload
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            
            response = requests.post(
                f"{BACKEND_URL}/admin/upload-video",
                files=files,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.test_video_id = data.get('video_id')
                    video_url = data.get('video_url')
                    self.log_result(
                        "POST /api/admin/upload-video",
                        True,
                        f"Video uploaded successfully. ID: {self.test_video_id}, URL: {video_url}",
                        data
                    )
                    return True
                else:
                    self.log_result(
                        "POST /api/admin/upload-video",
                        False,
                        "Response indicates failure",
                        data
                    )
                    return False
            else:
                self.log_result(
                    "POST /api/admin/upload-video",
                    False,
                    f"Failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result(
                "POST /api/admin/upload-video",
                False,
                f"Request error: {str(e)}"
            )
            return False

    def test_get_video(self):
        """Test GET /api/video/{id} - получение видео файла"""
        print("📹 Testing GET /api/video/{id}...")
        
        if not self.test_video_id:
            self.log_result(
                "GET /api/video/{id}",
                False,
                "No test video ID available for retrieval test"
            )
            return False
        
        try:
            response = requests.get(f"{BACKEND_URL}/video/{self.test_video_id}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                self.log_result(
                    "GET /api/video/{id}",
                    True,
                    f"Video retrieved successfully. Content-Type: {content_type}, Size: {content_length} bytes"
                )
                return True
            else:
                self.log_result(
                    "GET /api/video/{id}",
                    False,
                    f"Failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result(
                "GET /api/video/{id}",
                False,
                f"Request error: {str(e)}"
            )
            return False

    def test_delete_material(self):
        """Test DELETE /api/admin/materials/{id} - удаление материала"""
        print("🗑️ Testing DELETE /api/admin/materials/{id}...")
        
        if not self.test_material_id:
            self.log_result(
                "DELETE /api/admin/materials/{id}",
                False,
                "No test material ID available for deletion test"
            )
            return False
        
        try:
            response = self.session.delete(f"{BACKEND_URL}/admin/materials/{self.test_material_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_result(
                        "DELETE /api/admin/materials/{id}",
                        True,
                        f"Material {self.test_material_id} deleted successfully",
                        data
                    )
                    return True
                else:
                    self.log_result(
                        "DELETE /api/admin/materials/{id}",
                        False,
                        "Response indicates failure",
                        data
                    )
                    return False
            else:
                self.log_result(
                    "DELETE /api/admin/materials/{id}",
                    False,
                    f"Failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result(
                "DELETE /api/admin/materials/{id}",
                False,
                f"Request error: {str(e)}"
            )
            return False

    def test_access_rights(self):
        """Test access rights - verify non-admin users cannot access admin endpoints"""
        print("🔒 Testing Access Rights...")
        
        # Create a temporary session without admin token
        temp_session = requests.Session()
        
        try:
            # Test without authentication
            response = temp_session.get(f"{BACKEND_URL}/admin/materials")
            
            if response.status_code == 401 or response.status_code == 403:
                self.log_result(
                    "Access Rights - Unauthenticated",
                    True,
                    f"Correctly blocked unauthenticated access with status {response.status_code}"
                )
            else:
                self.log_result(
                    "Access Rights - Unauthenticated",
                    False,
                    f"Should have blocked access but got status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(
                "Access Rights - Unauthenticated",
                False,
                f"Request error: {str(e)}"
            )

    def run_all_tests(self):
        """Run all admin materials management tests"""
        print("🚀 Starting Admin Materials Management Test Suite")
        print("=" * 60)
        
        # Step 1: Authenticate
        if not self.authenticate_super_admin():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Test all CRUD operations
        self.test_get_all_materials()
        self.test_create_material()
        self.test_update_material()
        self.test_upload_video()
        self.test_get_video()
        self.test_delete_material()
        
        # Step 3: Test access rights
        self.test_access_rights()
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if "✅ PASS" in r['status'])
        failed = sum(1 for r in self.results if "❌ FAIL" in r['status'])
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        print("\nDetailed Results:")
        for result in self.results:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
        
        return failed == 0

def main():
    """Main test execution"""
    print("NUMEROM Admin Materials Management Testing")
    print("Testing new admin endpoints for materials CRUD operations")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Super Admin: {SUPER_ADMIN_EMAIL}")
    print()
    
    test_suite = AdminMaterialsTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed successfully!")
        return 0
    else:
        print("\n⚠️ Some tests failed. Check the details above.")
        return 1

if __name__ == "__main__":
    exit(main())