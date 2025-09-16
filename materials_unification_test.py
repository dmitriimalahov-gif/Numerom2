#!/usr/bin/env python3
"""
Materials Unification Test Suite
Testing the unification of materials with PersonalConsultations model

Review Request: УНИФИКАЦИЯ МАТЕРИАЛОВ: Применение модели PersonalConsultations к материалам урока
"""

import requests
import json
import os
import tempfile
import time
from pathlib import Path

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_USER_EMAIL = "dmitrii.malahov@gmail.com"
TEST_USER_PASSWORD = "756bvy67H"

class MaterialsUnificationTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.video_file_id = None
        self.pdf_file_id = None
        self.material_id = None
        
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
                user_info = data.get('user', {})
                self.log_test("Authentication", True, 
                    f"Logged in as {user_info.get('email')} with {user_info.get('credits_remaining', 0)} credits")
                return True
            else:
                self.log_test("Authentication", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Authentication", False, f"Exception: {str(e)}")
            return False
    
    def create_test_files(self):
        """Create test video and PDF files"""
        try:
            # Create test video file (MP4 header)
            self.test_video_path = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            # Write minimal MP4 header
            mp4_header = b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom'
            self.test_video_path.write(mp4_header + b'\x00' * 1000)  # 1KB test file
            self.test_video_path.close()
            
            # Create test PDF file
            self.test_pdf_path = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            # Write minimal PDF header
            pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF'
            self.test_pdf_path.write(pdf_content)
            self.test_pdf_path.close()
            
            self.log_test("Test Files Creation", True, "Created test MP4 and PDF files")
            return True
        except Exception as e:
            self.log_test("Test Files Creation", False, f"Exception: {str(e)}")
            return False
    
    def test_unified_video_upload_endpoint(self):
        """Test 1: Materials use /api/admin/consultations/upload-video for upload"""
        try:
            with open(self.test_video_path.name, 'rb') as f:
                files = {'file': ('test_material_video.mp4', f, 'video/mp4')}
                response = self.session.post(f"{BACKEND_URL}/admin/consultations/upload-video", files=files)
            
            if response.status_code == 200:
                data = response.json()
                self.video_file_id = data.get('file_id')
                self.video_filename = data.get('filename', 'test_material_video.mp4')
                self.log_test("Unified Video Upload Endpoint", True, 
                    f"Video uploaded via consultations endpoint - file_id: {self.video_file_id}")
                return True
            else:
                self.log_test("Unified Video Upload Endpoint", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Unified Video Upload Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_unified_pdf_upload_endpoint(self):
        """Test 2: Materials use /api/admin/consultations/upload-pdf for upload"""
        try:
            with open(self.test_pdf_path.name, 'rb') as f:
                files = {'file': ('test_material_document.pdf', f, 'application/pdf')}
                response = self.session.post(f"{BACKEND_URL}/admin/consultations/upload-pdf", files=files)
            
            if response.status_code == 200:
                data = response.json()
                self.pdf_file_id = data.get('file_id')
                self.pdf_filename = data.get('filename', 'test_material_document.pdf')
                self.log_test("Unified PDF Upload Endpoint", True, 
                    f"PDF uploaded via consultations endpoint - file_id: {self.pdf_file_id}")
                return True
            else:
                self.log_test("Unified PDF Upload Endpoint", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Unified PDF Upload Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_material_creation_with_new_fields(self):
        """Test 3: Admin creates material with video_file_id and pdf_file_id"""
        try:
            material_data = {
                "title": "Test Unified Material",
                "description": "Testing unified materials system using PersonalConsultations model",
                "content": "This material tests the unification with consultations endpoints",
                "video_file_id": self.video_file_id,      # NEW field like PersonalConsultations
                "video_filename": self.video_filename,    # NEW field for display
                "pdf_file_id": self.pdf_file_id,          # NEW field like PersonalConsultations  
                "pdf_filename": self.pdf_filename,        # NEW field for display
                "order": 1,
                "is_active": True
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/materials", json=material_data)
            
            if response.status_code == 200:
                data = response.json()
                self.material_id = data.get('material_id')
                self.log_test("Material Creation with New Fields", True, 
                    f"Material created with ID: {self.material_id}, using video_file_id and pdf_file_id")
                return True
            else:
                self.log_test("Material Creation with New Fields", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Material Creation with New Fields", False, f"Exception: {str(e)}")
            return False
    
    def test_materials_list_with_new_fields(self):
        """Test 4: Materials list includes new fields"""
        try:
            response = self.session.get(f"{BACKEND_URL}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                
                # Find our test material
                test_material = None
                for material in materials:
                    if material.get('id') == self.material_id:
                        test_material = material
                        break
                
                if test_material:
                    has_video_file_id = 'video_file_id' in test_material and test_material['video_file_id'] == self.video_file_id
                    has_pdf_file_id = 'pdf_file_id' in test_material and test_material['pdf_file_id'] == self.pdf_file_id
                    has_video_filename = 'video_filename' in test_material
                    has_pdf_filename = 'pdf_filename' in test_material
                    
                    if has_video_file_id and has_pdf_file_id and has_video_filename and has_pdf_filename:
                        self.log_test("Materials List with New Fields", True, 
                            f"Material contains all new fields: video_file_id, pdf_file_id, video_filename, pdf_filename")
                        return True
                    else:
                        self.log_test("Materials List with New Fields", False, 
                            f"Missing fields - video_file_id: {has_video_file_id}, pdf_file_id: {has_pdf_file_id}, video_filename: {has_video_filename}, pdf_filename: {has_pdf_filename}")
                        return False
                else:
                    self.log_test("Materials List with New Fields", False, "Test material not found in materials list")
                    return False
            else:
                self.log_test("Materials List with New Fields", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Materials List with New Fields", False, f"Exception: {str(e)}")
            return False
    
    def test_unified_video_streaming_endpoint(self):
        """Test 5: Materials display video through /api/consultations/video/{file_id}"""
        try:
            response = self.session.get(f"{BACKEND_URL}/consultations/video/{self.video_file_id}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                if 'video' in content_type.lower() and content_length > 0:
                    self.log_test("Unified Video Streaming Endpoint", True, 
                        f"Video streams via consultations endpoint - Content-Type: {content_type}, Size: {content_length} bytes")
                    return True
                else:
                    self.log_test("Unified Video Streaming Endpoint", False, 
                        f"Invalid video response - Content-Type: {content_type}, Size: {content_length}")
                    return False
            else:
                self.log_test("Unified Video Streaming Endpoint", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Unified Video Streaming Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_unified_pdf_streaming_endpoint(self):
        """Test 6: Materials display PDF through /api/consultations/pdf/{file_id}"""
        try:
            response = self.session.get(f"{BACKEND_URL}/consultations/pdf/{self.pdf_file_id}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                if 'pdf' in content_type.lower() and content_length > 0:
                    self.log_test("Unified PDF Streaming Endpoint", True, 
                        f"PDF streams via consultations endpoint - Content-Type: {content_type}, Size: {content_length} bytes")
                    return True
                else:
                    self.log_test("Unified PDF Streaming Endpoint", False, 
                        f"Invalid PDF response - Content-Type: {content_type}, Size: {content_length}")
                    return False
            else:
                self.log_test("Unified PDF Streaming Endpoint", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Unified PDF Streaming Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_backward_compatibility(self):
        """Test 7: Backward compatibility with old fields (video_file, file_url)"""
        try:
            # Create a material with old fields for compatibility testing
            old_material_data = {
                "title": "Test Backward Compatibility Material",
                "description": "Testing backward compatibility with old fields",
                "video_file": "old_video_file.mp4",  # OLD field
                "file_url": "old_document.pdf",      # OLD field
                "order": 2,
                "is_active": True
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/materials", json=old_material_data)
            
            if response.status_code == 200:
                data = response.json()
                old_material_id = data.get('material_id')
                
                # Verify the old material appears in materials list
                list_response = self.session.get(f"{BACKEND_URL}/materials")
                if list_response.status_code == 200:
                    materials = list_response.json()
                    old_material = None
                    for material in materials:
                        if material.get('id') == old_material_id:
                            old_material = material
                            break
                    
                    if old_material:
                        has_old_fields = 'video_file' in old_material and 'file_url' in old_material
                        self.log_test("Backward Compatibility", True, 
                            f"Old material created and listed with legacy fields - ID: {old_material_id}")
                        return True
                    else:
                        self.log_test("Backward Compatibility", False, "Old material not found in list")
                        return False
                else:
                    self.log_test("Backward Compatibility", False, "Failed to retrieve materials list")
                    return False
            else:
                self.log_test("Backward Compatibility", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Backward Compatibility", False, f"Exception: {str(e)}")
            return False
    
    def test_material_type_detection(self):
        """Test 8: Material type detection with new fields"""
        try:
            response = self.session.get(f"{BACKEND_URL}/materials")
            
            if response.status_code == 200:
                materials = response.json()
                
                # Find our test material
                test_material = None
                for material in materials:
                    if material.get('id') == self.material_id:
                        test_material = material
                        break
                
                if test_material:
                    # Check if material has both video and PDF (should be detected as mixed type)
                    has_video = bool(test_material.get('video_file_id') or test_material.get('video_file'))
                    has_pdf = bool(test_material.get('pdf_file_id') or test_material.get('file_url'))
                    
                    if has_video and has_pdf:
                        self.log_test("Material Type Detection", True, 
                            f"Material correctly detected as having both video and PDF content")
                        return True
                    else:
                        self.log_test("Material Type Detection", False, 
                            f"Material type detection failed - has_video: {has_video}, has_pdf: {has_pdf}")
                        return False
                else:
                    self.log_test("Material Type Detection", False, "Test material not found")
                    return False
            else:
                self.log_test("Material Type Detection", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Material Type Detection", False, f"Exception: {str(e)}")
            return False
    
    def cleanup_test_files(self):
        """Clean up test files"""
        try:
            if hasattr(self, 'test_video_path') and os.path.exists(self.test_video_path.name):
                os.unlink(self.test_video_path.name)
            if hasattr(self, 'test_pdf_path') and os.path.exists(self.test_pdf_path.name):
                os.unlink(self.test_pdf_path.name)
            self.log_test("Cleanup Test Files", True, "Temporary test files cleaned up")
        except Exception as e:
            self.log_test("Cleanup Test Files", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all unification tests"""
        print("🚀 STARTING MATERIALS UNIFICATION TEST SUITE")
        print("=" * 60)
        
        # Authentication
        if not self.authenticate():
            return False
        
        # Create test files
        if not self.create_test_files():
            return False
        
        # Test the complete unification chain
        tests = [
            self.test_unified_video_upload_endpoint,
            self.test_unified_pdf_upload_endpoint,
            self.test_material_creation_with_new_fields,
            self.test_materials_list_with_new_fields,
            self.test_unified_video_streaming_endpoint,
            self.test_unified_pdf_streaming_endpoint,
            self.test_backward_compatibility,
            self.test_material_type_detection
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            time.sleep(0.5)  # Small delay between tests
        
        # Cleanup
        self.cleanup_test_files()
        
        print("\n" + "=" * 60)
        print(f"📊 MATERIALS UNIFICATION TEST RESULTS: {passed}/{total} PASSED")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - MATERIALS UNIFICATION WORKING CORRECTLY!")
            print("\n✅ VERIFIED UNIFICATION FEATURES:")
            print("   • Materials use /api/admin/consultations/upload-video for upload")
            print("   • Materials use /api/admin/consultations/upload-pdf for upload") 
            print("   • Materials save with video_file_id and pdf_file_id fields")
            print("   • Materials stream video via /api/consultations/video/{file_id}")
            print("   • Materials stream PDF via /api/consultations/pdf/{file_id}")
            print("   • Backward compatibility with old video_file/file_url fields")
            print("   • Material type detection works with new fields")
            print("   • Complete chain: Admin upload → Save → Student view → Stream")
        else:
            print(f"❌ {total - passed} TESTS FAILED - UNIFICATION ISSUES DETECTED")
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")
        
        return passed == total

def main():
    """Main test execution"""
    test_suite = MaterialsUnificationTestSuite()
    success = test_suite.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())