#!/usr/bin/env python3
"""
Backend Test Suite for Additional PDF Files to Lessons
Testing the complete chain: AdminPanel → backend → FirstLesson → ConsultationPDFViewer

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
TEST_LESSON_ID = "lesson_numerom_intro"  # Using the intro lesson from review request

class AdditionalPDFTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.uploaded_file_ids = []  # Track uploaded files for cleanup
        
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
                    f"Logged in as {user_info.get('email')} (Credits: {user_info.get('credits_remaining')}, Super Admin: {user_info.get('is_super_admin')})")
                return True
            else:
                self.log_test("Authentication", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Authentication", False, f"Exception: {str(e)}")
            return False
    
    def create_test_pdf(self, filename="test_additional_material.pdf", content="Test PDF content for additional materials"):
        """Create a test PDF file"""
        try:
            # Create a simple PDF-like file for testing
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
({content}) Tj
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
        except Exception as e:
            self.log_test("Create Test PDF", False, f"Exception: {str(e)}")
            return None
    
    def test_add_additional_pdf(self):
        """Test POST /api/admin/lessons/{lesson_id}/add-pdf"""
        try:
            # Create test PDF
            pdf_file = self.create_test_pdf()
            if not pdf_file:
                return False
            
            # Prepare form data
            files = {
                'file': ('test_additional_material.pdf', pdf_file, 'application/pdf')
            }
            data = {
                'title': 'Дополнительный материал по нумерологии'
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/admin/lessons/{TEST_LESSON_ID}/add-pdf",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('file_id'):
                    file_id = result['file_id']
                    self.uploaded_file_ids.append(file_id)  # Track for cleanup
                    self.log_test("Add Additional PDF", True, 
                        f"PDF uploaded successfully. File ID: {file_id}, Title: {result.get('title')}, URL: {result.get('pdf_url')}")
                    return file_id
                else:
                    self.log_test("Add Additional PDF", False, f"Invalid response structure: {result}")
                    return False
            else:
                self.log_test("Add Additional PDF", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Add Additional PDF", False, f"Exception: {str(e)}")
            return False
    
    def test_get_additional_pdfs(self):
        """Test GET /api/lessons/{lesson_id}/additional-pdfs"""
        try:
            response = self.session.get(f"{BACKEND_URL}/lessons/{TEST_LESSON_ID}/additional-pdfs")
            
            if response.status_code == 200:
                result = response.json()
                pdfs = result.get('additional_pdfs', [])
                count = result.get('count', 0)
                
                self.log_test("Get Additional PDFs", True, 
                    f"Found {count} additional PDFs for lesson {TEST_LESSON_ID}")
                
                # Check if our uploaded PDF is in the list
                if count > 0:
                    for pdf in pdfs:
                        print(f"   - PDF: {pdf.get('title')} (ID: {pdf.get('file_id')}, URL: {pdf.get('pdf_url')})")
                
                return pdfs
            else:
                self.log_test("Get Additional PDFs", False, f"Status: {response.status_code}, Response: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("Get Additional PDFs", False, f"Exception: {str(e)}")
            return []
    
    def test_pdf_streaming(self, file_id):
        """Test GET /api/consultations/pdf/{file_id} - PDF streaming endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/consultations/pdf/{file_id}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                # Check if it's a PDF
                if 'application/pdf' in content_type or response.content.startswith(b'%PDF'):
                    self.log_test("PDF Streaming", True, 
                        f"PDF streamed successfully. Content-Type: {content_type}, Size: {content_length} bytes")
                    return True
                else:
                    self.log_test("PDF Streaming", False, 
                        f"Invalid content type: {content_type}, Content preview: {response.content[:100]}")
                    return False
            else:
                self.log_test("PDF Streaming", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("PDF Streaming", False, f"Exception: {str(e)}")
            return False
    
    def test_delete_additional_pdf(self, file_id):
        """Test DELETE /api/admin/lessons/pdf/{file_id}"""
        try:
            response = self.session.delete(f"{BACKEND_URL}/admin/lessons/pdf/{file_id}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.log_test("Delete Additional PDF", True, 
                        f"PDF deleted successfully. Message: {result.get('message')}")
                    return True
                else:
                    self.log_test("Delete Additional PDF", False, f"Delete failed: {result}")
                    return False
            else:
                self.log_test("Delete Additional PDF", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Delete Additional PDF", False, f"Exception: {str(e)}")
            return False
    
    def test_unification_with_consultations(self):
        """Test that additional PDFs use the same consultations infrastructure"""
        try:
            # First add a PDF
            file_id = self.test_add_additional_pdf()
            if not file_id:
                return False
            
            # Test that the PDF is accessible via consultations endpoint
            pdf_streaming_success = self.test_pdf_streaming(file_id)
            
            # Get additional PDFs and verify URL format
            pdfs = self.test_get_additional_pdfs()
            
            unification_verified = False
            for pdf in pdfs:
                if pdf.get('file_id') == file_id:
                    pdf_url = pdf.get('pdf_url', '')
                    if '/api/consultations/pdf/' in pdf_url:
                        unification_verified = True
                        break
            
            if pdf_streaming_success and unification_verified:
                self.log_test("Unification with Consultations", True, 
                    "Additional PDFs correctly use consultations infrastructure")
                return True
            else:
                self.log_test("Unification with Consultations", False, 
                    f"Unification failed. Streaming: {pdf_streaming_success}, URL format: {unification_verified}")
                return False
                
        except Exception as e:
            self.log_test("Unification with Consultations", False, f"Exception: {str(e)}")
            return False
    
    def test_admin_panel_chain(self):
        """Test the complete admin panel chain: upload → list → view → delete"""
        try:
            print("\n🔧 TESTING ADMIN PANEL CHAIN:")
            
            # Step 1: Upload PDF with custom title
            print("Step 1: Uploading PDF with custom title...")
            file_id = self.test_add_additional_pdf()
            if not file_id:
                return False
            
            # Step 2: List additional PDFs
            print("Step 2: Listing additional PDFs...")
            pdfs = self.test_get_additional_pdfs()
            if not pdfs:
                return False
            
            # Step 3: Test PDF viewing/streaming
            print("Step 3: Testing PDF streaming...")
            streaming_success = self.test_pdf_streaming(file_id)
            if not streaming_success:
                return False
            
            # Step 4: Test PDF deletion
            print("Step 4: Testing PDF deletion...")
            delete_success = self.test_delete_additional_pdf(file_id)
            if delete_success:
                # Remove from tracking since it's deleted
                if file_id in self.uploaded_file_ids:
                    self.uploaded_file_ids.remove(file_id)
            
            self.log_test("Complete Admin Panel Chain", True, 
                "Full admin chain (upload → list → view → delete) working correctly")
            return True
            
        except Exception as e:
            self.log_test("Complete Admin Panel Chain", False, f"Exception: {str(e)}")
            return False
    
    def test_student_experience_chain(self):
        """Test the student experience: get additional PDFs → open PDF viewer"""
        try:
            print("\n👨‍🎓 TESTING STUDENT EXPERIENCE CHAIN:")
            
            # First upload a PDF as admin
            print("Setting up: Uploading test PDF...")
            file_id = self.test_add_additional_pdf()
            if not file_id:
                return False
            
            # Step 1: Student gets additional PDFs for lesson
            print("Step 1: Student getting additional PDFs...")
            pdfs = self.test_get_additional_pdfs()
            if not pdfs:
                return False
            
            # Step 2: Student opens PDF (via consultations viewer)
            print("Step 2: Student opening PDF...")
            streaming_success = self.test_pdf_streaming(file_id)
            
            if streaming_success:
                self.log_test("Student Experience Chain", True, 
                    "Student can successfully view additional materials")
                return True
            else:
                self.log_test("Student Experience Chain", False, 
                    "Student cannot access PDF materials")
                return False
            
        except Exception as e:
            self.log_test("Student Experience Chain", False, f"Exception: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up uploaded test files"""
        print("\n🧹 CLEANING UP TEST FILES:")
        for file_id in self.uploaded_file_ids:
            try:
                self.test_delete_additional_pdf(file_id)
            except:
                pass  # Ignore cleanup errors
    
    def run_all_tests(self):
        """Run all tests for additional PDF functionality"""
        print("🚀 STARTING ADDITIONAL PDF FILES TESTING")
        print("=" * 60)
        
        # Authentication
        if not self.authenticate():
            return False
        
        # Test individual endpoints
        print("\n📋 TESTING INDIVIDUAL ENDPOINTS:")
        self.test_add_additional_pdf()
        self.test_get_additional_pdfs()
        
        # Test unification
        print("\n🔗 TESTING UNIFICATION WITH CONSULTATIONS:")
        self.test_unification_with_consultations()
        
        # Test complete chains
        self.test_admin_panel_chain()
        self.test_student_experience_chain()
        
        # Cleanup
        self.cleanup()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY:")
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ Passed: {passed}/{total} ({success_rate:.1f}%)")
        
        if passed < total:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
        
        return success_rate >= 80  # 80% success rate threshold

if __name__ == "__main__":
    test_suite = AdditionalPDFTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 ADDITIONAL PDF FUNCTIONALITY: ALL TESTS PASSED!")
    else:
        print("\n⚠️  ADDITIONAL PDF FUNCTIONALITY: SOME TESTS FAILED!")
    
    exit(0 if success else 1)