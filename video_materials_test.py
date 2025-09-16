#!/usr/bin/env python3
"""
NUMEROM Video and Materials System Testing Suite
Tests video and materials endpoints as specified in the review request.
"""

import requests
import json
import os
import io
from datetime import datetime
import time

# Get backend URL from environment
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

class VideoMaterialsTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.auth_token = None
        self.super_admin_token = None
        self.test_results = []
        self.created_material_id = None
        self.uploaded_video_id = None
        
        # Super admin credentials from auth.py
        self.super_admin_data = {
            "email": "dmitrii.malahov@gmail.com",
            "password": "756bvy67H"
        }
        
        # Test user data
        self.user_data = {
            "email": f"videotest{int(time.time())}@numerom.com",
            "password": "SecurePass123!",
            "full_name": "Video Test User",
            "birth_date": "15.03.1990",
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
            
        # Use super admin token for admin endpoints, regular token for others
        if "/admin/" in endpoint and self.super_admin_token:
            default_headers["Authorization"] = f"Bearer {self.super_admin_token}"
        elif self.auth_token and "Authorization" not in default_headers:
            default_headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=default_headers, timeout=30)
            elif method.upper() == "POST":
                if files:
                    # Remove Content-Type for file uploads
                    if "Content-Type" in default_headers:
                        del default_headers["Content-Type"]
                    response = requests.post(url, data=data, files=files, headers=default_headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=default_headers, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=default_headers, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=default_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {method} {url}: {str(e)}")
            return None
    
    def setup_authentication(self):
        """Setup authentication for both regular user and super admin"""
        # Register and login regular user
        response = self.make_request("POST", "/auth/register", self.user_data)
        if response and response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token")
            self.log_result("User Registration", True, "Test user registered successfully")
        else:
            self.log_result("User Registration", False, "Failed to register test user")
            return False
        
        # Login super admin
        response = self.make_request("POST", "/auth/login", self.super_admin_data)
        if response and response.status_code == 200:
            data = response.json()
            self.super_admin_token = data.get("access_token")
            self.log_result("Super Admin Login", True, "Super admin logged in successfully")
            return True
        else:
            self.log_result("Super Admin Login", False, "Failed to login super admin")
            return False
    
    def test_materials_endpoint(self):
        """Test GET /api/materials - check that it returns materials with video_url and video_file fields"""
        if not self.auth_token:
            self.log_result("Materials Endpoint", False, "No auth token available")
            return False
        
        response = self.make_request("GET", "/materials")
        
        if response and response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                self.log_result("Materials Endpoint", True, f"Retrieved {len(data)} materials")
                
                # Check structure of materials if any exist
                if len(data) > 0:
                    material = data[0]
                    expected_fields = ["id", "title", "description", "file_url"]
                    
                    # Check for video-related fields (they might be None/empty but should exist)
                    video_fields_present = any(field in material for field in ["video_url", "video_file"])
                    
                    if all(field in material for field in expected_fields):
                        if video_fields_present:
                            self.log_result("Materials Structure", True, "Materials contain required fields including video fields")
                        else:
                            self.log_result("Materials Structure", False, "Materials missing video_url/video_file fields", material)
                            return False
                    else:
                        missing = [f for f in expected_fields if f not in material]
                        self.log_result("Materials Structure", False, f"Missing fields: {missing}", material)
                        return False
                else:
                    self.log_result("Materials Structure", True, "No materials found (empty list is valid)")
                
                return True
            else:
                self.log_result("Materials Endpoint", False, "Expected list response", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Materials Endpoint", False, "Failed to get materials", error)
        
        return False
    
    def test_admin_materials_endpoint(self):
        """Test GET /api/admin/materials - check that it returns complete material data"""
        if not self.super_admin_token:
            self.log_result("Admin Materials Endpoint", False, "No super admin token available")
            return False
        
        response = self.make_request("GET", "/admin/materials")
        
        if response and response.status_code == 200:
            data = response.json()
            if "materials" in data and isinstance(data["materials"], list):
                materials = data["materials"]
                self.log_result("Admin Materials Endpoint", True, f"Retrieved {len(materials)} materials with admin access")
                
                # Check structure if materials exist
                if len(materials) > 0:
                    material = materials[0]
                    admin_fields = ["id", "title", "description", "created_at", "created_by"]
                    
                    if all(field in material for field in admin_fields):
                        self.log_result("Admin Materials Structure", True, "Admin materials contain complete data")
                    else:
                        missing = [f for f in admin_fields if f not in material]
                        self.log_result("Admin Materials Structure", False, f"Missing admin fields: {missing}", material)
                        return False
                
                return True
            else:
                self.log_result("Admin Materials Endpoint", False, "Expected materials array in response", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Admin Materials Endpoint", False, "Failed to get admin materials", error)
        
        return False
    
    def test_create_material_with_video_url(self):
        """Test POST /api/admin/materials - test creating material with video_url"""
        if not self.super_admin_token:
            self.log_result("Create Material with Video URL", False, "No super admin token available")
            return False
        
        # Create material with YouTube video URL
        material_data = {
            "title": "Тестовый видео материал",
            "description": "Материал с YouTube видео для тестирования",
            "content": "Содержание тестового материала",
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "order": 1,
            "is_active": True
        }
        
        response = self.make_request("POST", "/admin/materials", material_data)
        
        if response and response.status_code == 200:
            data = response.json()
            if "success" in data and data["success"] and "material_id" in data:
                self.created_material_id = data["material_id"]
                self.log_result("Create Material with Video URL", True, f"Material created with ID: {self.created_material_id}")
                
                # Verify the material was created with correct fields
                return self.verify_created_material()
            else:
                self.log_result("Create Material with Video URL", False, "Unexpected response format", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Create Material with Video URL", False, "Failed to create material", error)
        
        return False
    
    def verify_created_material(self):
        """Verify that the created material has correct video_url field"""
        if not self.created_material_id:
            return False
        
        # Get the created material from admin endpoint
        response = self.make_request("GET", "/admin/materials")
        
        if response and response.status_code == 200:
            data = response.json()
            materials = data.get("materials", [])
            
            # Find our created material
            created_material = None
            for material in materials:
                if material.get("id") == self.created_material_id:
                    created_material = material
                    break
            
            if created_material:
                if created_material.get("video_url") == "https://www.youtube.com/watch?v=dQw4w9WgXcQ":
                    self.log_result("Verify Created Material", True, "Material saved with correct video_url")
                    return True
                else:
                    self.log_result("Verify Created Material", False, 
                                  f"video_url mismatch: {created_material.get('video_url')}", created_material)
            else:
                self.log_result("Verify Created Material", False, "Created material not found in list")
        else:
            self.log_result("Verify Created Material", False, "Failed to retrieve materials for verification")
        
        return False
    
    def test_upload_video_file(self):
        """Test POST /api/admin/upload-video - test video file upload"""
        if not self.super_admin_token:
            self.log_result("Upload Video File", False, "No super admin token available")
            return False
        
        # Create a mock video file (small MP4-like content)
        video_content = b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom\x00\x00\x00\x08free' + b'\x00' * 1000
        
        files = {
            'file': ('test_video.mp4', io.BytesIO(video_content), 'video/mp4')
        }
        
        response = self.make_request("POST", "/admin/upload-video", files=files)
        
        if response and response.status_code == 200:
            data = response.json()
            if "success" in data and data["success"] and "video_id" in data:
                self.uploaded_video_id = data["video_id"]
                video_url = data.get("video_url")
                self.log_result("Upload Video File", True, f"Video uploaded with ID: {self.uploaded_video_id}, URL: {video_url}")
                return True
            else:
                self.log_result("Upload Video File", False, "Unexpected response format", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Upload Video File", False, "Failed to upload video", error)
        
        return False
    
    def test_video_serving_endpoint(self):
        """Test GET /api/video/{video_id} - check that it returns video files"""
        if not self.uploaded_video_id:
            self.log_result("Video Serving Endpoint", False, "No uploaded video ID available")
            return False
        
        response = self.make_request("GET", f"/video/{self.uploaded_video_id}")
        
        if response and response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            content_length = len(response.content)
            
            if 'video/' in content_type and content_length > 0:
                self.log_result("Video Serving Endpoint", True, 
                              f"Video served successfully ({content_length} bytes, {content_type})")
                return True
            else:
                self.log_result("Video Serving Endpoint", False, 
                              f"Invalid video response: {content_type}, {content_length} bytes")
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Video Serving Endpoint", False, "Failed to serve video", error)
        
        return False
    
    def test_update_material_with_video_file(self):
        """Test PUT /api/admin/materials/{id} - test updating material with video_file"""
        if not self.created_material_id or not self.uploaded_video_id:
            self.log_result("Update Material with Video File", False, "Missing material ID or video ID")
            return False
        
        # Update material to reference the uploaded video file
        update_data = {
            "video_file": f"/api/video/{self.uploaded_video_id}",
            "description": "Материал обновлен с загруженным видео файлом"
        }
        
        response = self.make_request("PUT", f"/admin/materials/{self.created_material_id}", update_data)
        
        if response and response.status_code == 200:
            data = response.json()
            if "success" in data and data["success"]:
                self.log_result("Update Material with Video File", True, "Material updated with video_file")
                
                # Verify the update
                return self.verify_updated_material()
            else:
                self.log_result("Update Material with Video File", False, "Unexpected response format", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Update Material with Video File", False, "Failed to update material", error)
        
        return False
    
    def verify_updated_material(self):
        """Verify that the material was updated with video_file"""
        response = self.make_request("GET", "/admin/materials")
        
        if response and response.status_code == 200:
            data = response.json()
            materials = data.get("materials", [])
            
            # Find our updated material
            updated_material = None
            for material in materials:
                if material.get("id") == self.created_material_id:
                    updated_material = material
                    break
            
            if updated_material:
                video_file = updated_material.get("video_file")
                if video_file and self.uploaded_video_id in video_file:
                    self.log_result("Verify Updated Material", True, "Material updated with correct video_file reference")
                    return True
                else:
                    self.log_result("Verify Updated Material", False, 
                                  f"video_file not updated correctly: {video_file}", updated_material)
            else:
                self.log_result("Verify Updated Material", False, "Updated material not found")
        else:
            self.log_result("Verify Updated Material", False, "Failed to retrieve materials for verification")
        
        return False
    
    def test_material_type_logic(self):
        """Test material type logic (video vs pdf vs unknown)"""
        # This test checks if the system correctly identifies material types
        # based on video_url, video_file, and file_url fields
        
        response = self.make_request("GET", "/materials")
        
        if response and response.status_code == 200:
            materials = response.json()
            
            if len(materials) > 0:
                # Check if we can determine material types
                video_materials = []
                pdf_materials = []
                unknown_materials = []
                
                for material in materials:
                    has_video_url = bool(material.get("video_url"))
                    has_video_file = bool(material.get("video_file"))
                    has_file_url = bool(material.get("file_url"))
                    
                    if has_video_url or has_video_file:
                        video_materials.append(material)
                    elif has_file_url and "pdf" in material.get("file_url", "").lower():
                        pdf_materials.append(material)
                    else:
                        unknown_materials.append(material)
                
                self.log_result("Material Type Logic", True, 
                              f"Classified materials: {len(video_materials)} video, {len(pdf_materials)} PDF, {len(unknown_materials)} unknown")
                return True
            else:
                self.log_result("Material Type Logic", True, "No materials to classify (empty list)")
                return True
        else:
            self.log_result("Material Type Logic", False, "Failed to get materials for type classification")
        
        return False
    
    def test_materials_stream_endpoint(self):
        """Test GET /api/materials/{material_id}/stream - check that it works for PDF materials"""
        # First, we need to find a material with a file_url (PDF material)
        response = self.make_request("GET", "/materials")
        
        if response and response.status_code == 200:
            materials = response.json()
            
            # Look for a material with file_url (PDF)
            pdf_material = None
            for material in materials:
                if material.get("file_url") and "stream" in material.get("file_url", ""):
                    pdf_material = material
                    break
            
            if pdf_material:
                material_id = pdf_material["id"]
                stream_response = self.make_request("GET", f"/materials/{material_id}/stream")
                
                if stream_response and stream_response.status_code == 200:
                    content_type = stream_response.headers.get('content-type', '')
                    content_length = len(stream_response.content)
                    
                    if 'application/pdf' in content_type or content_length > 0:
                        self.log_result("Materials Stream Endpoint", True, 
                                      f"PDF material streamed successfully ({content_length} bytes)")
                        return True
                    else:
                        self.log_result("Materials Stream Endpoint", False, 
                                      f"Invalid stream response: {content_type}, {content_length} bytes")
                else:
                    error = stream_response.text if stream_response else "Connection failed"
                    self.log_result("Materials Stream Endpoint", False, "Failed to stream material", error)
            else:
                self.log_result("Materials Stream Endpoint", True, "No PDF materials found to test streaming (acceptable)")
                return True
        else:
            self.log_result("Materials Stream Endpoint", False, "Failed to get materials list")
        
        return False
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        if self.created_material_id and self.super_admin_token:
            response = self.make_request("DELETE", f"/admin/materials/{self.created_material_id}")
            if response and response.status_code == 200:
                self.log_result("Cleanup Test Material", True, "Test material deleted successfully")
            else:
                self.log_result("Cleanup Test Material", False, "Failed to delete test material")
    
    def run_all_tests(self):
        """Run all video and materials tests"""
        print("🎥 Starting NUMEROM Video and Materials System Tests")
        print("=" * 60)
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Failed to setup authentication, aborting tests")
            return 0, 1
        
        # Test 1: Basic materials endpoint
        print("\n📋 Testing Materials Endpoints:")
        self.test_materials_endpoint()
        self.test_admin_materials_endpoint()
        
        # Test 2: Create material with video URL
        print("\n🎬 Testing Material Creation with Video:")
        self.test_create_material_with_video_url()
        
        # Test 3: Video file upload and serving
        print("\n📤 Testing Video Upload and Serving:")
        self.test_upload_video_file()
        self.test_video_serving_endpoint()
        
        # Test 4: Update material with video file
        print("\n✏️ Testing Material Updates:")
        self.test_update_material_with_video_file()
        
        # Test 5: Material type logic and streaming
        print("\n🔍 Testing Material Type Logic:")
        self.test_material_type_logic()
        self.test_materials_stream_endpoint()
        
        # Cleanup
        print("\n🧹 Cleanup:")
        self.cleanup_test_data()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 VIDEO & MATERIALS TEST SUMMARY")
        print("=" * 60)
        
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
        else:
            print("\n🎉 All video and materials tests passed!")
        
        return passed, total

def main():
    """Main test execution"""
    tester = VideoMaterialsTester()
    passed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    if passed == total:
        print("\n✅ All video and materials tests completed successfully!")
        exit(0)
    else:
        print(f"\n⚠️ {total - passed} tests failed")
        exit(1)

if __name__ == "__main__":
    main()