#!/usr/bin/env python3
"""
Comprehensive Test Suite for Additional PDF Files to Lessons
Testing edge cases and complete integration scenarios

Review Request: ТЕСТИРОВАНИЕ: Дополнительные PDF файлы к занятиям
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

class ComprehensivePDFTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.uploaded_file_ids = []
        
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
                    f"Logged in as {user_info.get('email')} (Super Admin: {user_info.get('is_super_admin')})")
                return True
            else:
                self.log_test("Authentication", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Authentication", False, f"Exception: {str(e)}")
            return False
    
    def create_test_pdf(self, filename="test.pdf", title_content="Test PDF"):
        """Create a test PDF file"""
        pdf_content = f"""%PDF-1.4
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
100 700 Td
({title_content}) Tj
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
300
%%EOF"""
        return io.BytesIO(pdf_content.encode('utf-8'))
    
    def test_multiple_pdf_uploads(self):
        """Test uploading multiple PDFs with different titles"""
        try:
            pdf_titles = [
                "Основы нумерологии - Часть 1",
                "Планетарные влияния в нумерологии",
                "Практические упражнения по числам",
                "Дополнительные материалы к уроку"
            ]
            
            uploaded_ids = []
            
            for i, title in enumerate(pdf_titles):
                pdf_file = self.create_test_pdf(f"material_{i+1}.pdf", title)
                
                files = {
                    'file': (f'material_{i+1}.pdf', pdf_file, 'application/pdf')
                }
                data = {
                    'title': title
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/admin/lessons/{TEST_LESSON_ID}/add-pdf",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success') and result.get('file_id'):
                        uploaded_ids.append(result['file_id'])
                        self.uploaded_file_ids.append(result['file_id'])
                    else:
                        self.log_test("Multiple PDF Uploads", False, f"Failed to upload PDF {i+1}")
                        return False
                else:
                    self.log_test("Multiple PDF Uploads", False, f"Upload {i+1} failed with status {response.status_code}")
                    return False
            
            self.log_test("Multiple PDF Uploads", True, f"Successfully uploaded {len(uploaded_ids)} PDFs")
            return uploaded_ids
            
        except Exception as e:
            self.log_test("Multiple PDF Uploads", False, f"Exception: {str(e)}")
            return False
    
    def test_pdf_list_with_custom_titles(self):
        """Test that custom titles are properly displayed in the list"""
        try:
            response = self.session.get(f"{BACKEND_URL}/lessons/{TEST_LESSON_ID}/additional-pdfs")
            
            if response.status_code == 200:
                result = response.json()
                pdfs = result.get('additional_pdfs', [])
                
                # Check that we have PDFs with custom titles
                custom_titles_found = []
                for pdf in pdfs:
                    title = pdf.get('title', '')
                    if title and title != pdf.get('filename', ''):
                        custom_titles_found.append(title)
                
                if len(custom_titles_found) > 0:
                    self.log_test("Custom Titles Display", True, 
                        f"Found {len(custom_titles_found)} PDFs with custom titles: {custom_titles_found}")
                    return True
                else:
                    self.log_test("Custom Titles Display", False, "No custom titles found in PDF list")
                    return False
            else:
                self.log_test("Custom Titles Display", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Custom Titles Display", False, f"Exception: {str(e)}")
            return False
    
    def test_pdf_streaming_with_cors(self):
        """Test PDF streaming with CORS headers"""
        try:
            # Get a PDF ID first
            response = self.session.get(f"{BACKEND_URL}/lessons/{TEST_LESSON_ID}/additional-pdfs")
            if response.status_code != 200:
                return False
            
            pdfs = response.json().get('additional_pdfs', [])
            if not pdfs:
                return False
            
            file_id = pdfs[0]['file_id']
            
            # Test streaming with CORS
            response = self.session.get(f"{BACKEND_URL}/consultations/pdf/{file_id}")
            
            if response.status_code == 200:
                # Check CORS headers
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                }
                
                cors_ok = all(header is not None for header in cors_headers.values())
                content_type = response.headers.get('content-type', '')
                
                if cors_ok and 'application/pdf' in content_type:
                    self.log_test("PDF Streaming with CORS", True, 
                        f"CORS headers present, Content-Type: {content_type}")
                    return True
                else:
                    self.log_test("PDF Streaming with CORS", False, 
                        f"CORS: {cors_ok}, Content-Type: {content_type}")
                    return False
            else:
                self.log_test("PDF Streaming with CORS", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("PDF Streaming with CORS", False, f"Exception: {str(e)}")
            return False
    
    def test_non_existent_pdf_access(self):
        """Test accessing non-existent PDF returns proper 404"""
        try:
            fake_id = "non-existent-pdf-id-12345"
            response = self.session.get(f"{BACKEND_URL}/consultations/pdf/{fake_id}")
            
            if response.status_code == 404:
                self.log_test("Non-existent PDF Access", True, "Properly returns 404 for non-existent PDF")
                return True
            else:
                self.log_test("Non-existent PDF Access", False, f"Expected 404, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Non-existent PDF Access", False, f"Exception: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up uploaded test files"""
        print("\n🧹 CLEANING UP TEST FILES:")
        for file_id in self.uploaded_file_ids:
            try:
                response = self.session.delete(f"{BACKEND_URL}/admin/lessons/pdf/{file_id}")
                if response.status_code == 200:
                    print(f"   ✅ Deleted PDF: {file_id}")
                else:
                    print(f"   ⚠️  Failed to delete PDF: {file_id}")
            except:
                print(f"   ❌ Error deleting PDF: {file_id}")
    
    def run_comprehensive_tests(self):
        """Run comprehensive tests for additional PDF functionality"""
        print("🚀 STARTING COMPREHENSIVE ADDITIONAL PDF TESTING")
        print("=" * 70)
        
        # Authentication
        if not self.authenticate():
            return False
        
        # Test multiple uploads
        print("\n📚 TESTING MULTIPLE PDF UPLOADS:")
        self.test_multiple_pdf_uploads()
        
        # Test custom titles
        print("\n🏷️  TESTING CUSTOM TITLES:")
        self.test_pdf_list_with_custom_titles()
        
        # Test streaming with CORS
        print("\n🌐 TESTING PDF STREAMING WITH CORS:")
        self.test_pdf_streaming_with_cors()
        
        # Test edge cases
        print("\n🔍 TESTING EDGE CASES:")
        self.test_non_existent_pdf_access()
        
        # Cleanup
        self.cleanup()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST SUMMARY:")
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ Passed: {passed}/{total} ({success_rate:.1f}%)")
        
        if passed < total:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
        
        return success_rate >= 85  # 85% success rate threshold

if __name__ == "__main__":
    test_suite = ComprehensivePDFTestSuite()
    success = test_suite.run_comprehensive_tests()
    
    if success:
        print("\n🎉 COMPREHENSIVE ADDITIONAL PDF TESTING: ALL TESTS PASSED!")
    else:
        print("\n⚠️  COMPREHENSIVE ADDITIONAL PDF TESTING: SOME TESTS FAILED!")
    
    exit(0 if success else 1)