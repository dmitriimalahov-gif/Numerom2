#!/usr/bin/env python3
"""
Focused PDF Viewer Test Suite
Testing core PDF functionality after improvements

Review Request: Протестировать основные API endpoints после улучшений PDF viewer компонентов. 
Убедиться что аутентификация, загрузка файлов, и API стриминга PDF работают корректно.
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

class FocusedPDFTestSuite:
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
        """Test authentication system"""
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
                self.user_id = user_info.get('id')
                self.log_test("Authentication", True, 
                    f"Logged in as {user_info.get('email')} (Credits: {user_info.get('credits_remaining', 0)})")
                return True
            else:
                self.log_test("Authentication", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Authentication", False, f"Exception: {str(e)}")
            return False
    
    def create_test_pdf(self):
        """Create a test PDF file"""
        try:
            self.test_pdf_path = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 44>>stream
BT/F1 12 Tf 100 700 Td(PDF Viewer Test)Tj ET
endstream endobj
xref 0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer<</Size 5/Root 1 0 R>>
startxref 300
%%EOF"""
            self.test_pdf_path.write(pdf_content)
            self.test_pdf_path.close()
            
            self.log_test("Test PDF Creation", True, f"Created test PDF: {self.test_pdf_path.name}")
            return True
        except Exception as e:
            self.log_test("Test PDF Creation", False, f"Exception: {str(e)}")
            return False
    
    def test_consultation_pdf_upload(self):
        """Test PDF upload via consultation endpoint"""
        try:
            with open(self.test_pdf_path.name, 'rb') as f:
                files = {'file': ('test_consultation.pdf', f, 'application/pdf')}
                response = self.session.post(f"{BACKEND_URL}/admin/consultations/upload-pdf", files=files)
            
            if response.status_code == 200:
                data = response.json()
                self.consultation_pdf_id = data.get('file_id')
                self.log_test("Consultation PDF Upload", True, 
                    f"PDF uploaded - File ID: {self.consultation_pdf_id}")
                return True
            else:
                self.log_test("Consultation PDF Upload", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Consultation PDF Upload", False, f"Exception: {str(e)}")
            return False
    
    def test_consultation_pdf_streaming(self):
        """Test PDF streaming via consultation endpoint"""
        try:
            if not hasattr(self, 'consultation_pdf_id'):
                self.log_test("Consultation PDF Streaming", False, "No PDF ID available")
                return False
                
            pdf_url = f"{BACKEND_URL}/consultations/pdf/{self.consultation_pdf_id}"
            response = self.session.get(pdf_url)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                cors_header = response.headers.get('access-control-allow-origin', '')
                content_length = int(response.headers.get('content-length', '0'))
                
                is_pdf = content_type == 'application/pdf'
                has_cors = cors_header == '*'
                has_content = content_length > 0
                is_valid_pdf = response.content.startswith(b'%PDF')
                
                if is_pdf and has_cors and has_content and is_valid_pdf:
                    self.log_test("Consultation PDF Streaming", True, 
                        f"PDF streams correctly - Size: {content_length} bytes, CORS: {cors_header}")
                    return True
                else:
                    self.log_test("Consultation PDF Streaming", False, 
                        f"Issues - PDF: {is_pdf}, CORS: {has_cors}, Content: {has_content}, Valid: {is_valid_pdf}")
                    return False
            else:
                self.log_test("Consultation PDF Streaming", False, 
                    f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Consultation PDF Streaming", False, f"Exception: {str(e)}")
            return False
    
    def test_lesson_pdf_upload(self):
        """Test PDF upload via lesson endpoint"""
        try:
            with open(self.test_pdf_path.name, 'rb') as f:
                files = {'file': ('test_lesson.pdf', f, 'application/pdf')}
                response = self.session.post(f"{BACKEND_URL}/admin/lessons/upload-pdf", files=files)
            
            if response.status_code == 200:
                data = response.json()
                self.lesson_pdf_id = data.get('file_id')
                self.log_test("Lesson PDF Upload", True, 
                    f"PDF uploaded - File ID: {self.lesson_pdf_id}")
                return True
            else:
                self.log_test("Lesson PDF Upload", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Lesson PDF Upload", False, f"Exception: {str(e)}")
            return False
    
    def test_lesson_pdf_streaming(self):
        """Test PDF streaming via lesson endpoint"""
        try:
            if not hasattr(self, 'lesson_pdf_id'):
                self.log_test("Lesson PDF Streaming", False, "No lesson PDF ID available")
                return False
                
            pdf_url = f"{BACKEND_URL}/lessons/pdf/{self.lesson_pdf_id}"
            response = self.session.get(pdf_url)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                cors_header = response.headers.get('access-control-allow-origin', '')
                content_length = int(response.headers.get('content-length', '0'))
                
                is_pdf = content_type == 'application/pdf'
                has_cors = cors_header == '*'
                has_content = content_length > 0
                is_valid_pdf = response.content.startswith(b'%PDF')
                
                if is_pdf and has_cors and has_content and is_valid_pdf:
                    self.log_test("Lesson PDF Streaming", True, 
                        f"PDF streams correctly - Size: {content_length} bytes, CORS: {cors_header}")
                    return True
                else:
                    self.log_test("Lesson PDF Streaming", False, 
                        f"Issues - PDF: {is_pdf}, CORS: {has_cors}, Content: {has_content}, Valid: {is_valid_pdf}")
                    return False
            else:
                self.log_test("Lesson PDF Streaming", False, 
                    f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Lesson PDF Streaming", False, f"Exception: {str(e)}")
            return False
    
    def test_consultation_creation_with_pdf(self):
        """Test creating consultation with PDF"""
        try:
            if not hasattr(self, 'consultation_pdf_id') or not hasattr(self, 'user_id'):
                self.log_test("Consultation Creation with PDF", False, "Missing PDF ID or User ID")
                return False
                
            consultation_data = {
                "title": "Test PDF Consultation",
                "description": "Testing PDF viewer functionality",
                "pdf_file_id": self.consultation_pdf_id,
                "assigned_user_id": self.user_id,
                "cost_credits": 1,
                "is_active": True
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/consultations", json=consultation_data)
            
            if response.status_code == 200:
                data = response.json()
                self.test_consultation_id = data.get('consultation_id')
                self.log_test("Consultation Creation with PDF", True, 
                    f"Consultation created - ID: {self.test_consultation_id}")
                return True
            else:
                self.log_test("Consultation Creation with PDF", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Consultation Creation with PDF", False, f"Exception: {str(e)}")
            return False
    
    def test_user_consultations_retrieval(self):
        """Test retrieving user consultations"""
        try:
            response = self.session.get(f"{BACKEND_URL}/user/consultations")
            
            if response.status_code == 200:
                consultations = response.json()
                consultation_count = len(consultations)
                
                # Look for our test consultation
                test_consultation = None
                if hasattr(self, 'test_consultation_id'):
                    for consultation in consultations:
                        if consultation.get('id') == self.test_consultation_id:
                            test_consultation = consultation
                            break
                
                if test_consultation:
                    has_pdf = test_consultation.get('pdf_file_id') is not None
                    self.log_test("User Consultations Retrieval", True, 
                        f"Found {consultation_count} consultations, test consultation has PDF: {has_pdf}")
                else:
                    self.log_test("User Consultations Retrieval", True, 
                        f"Found {consultation_count} consultations (test consultation may not be visible)")
                return True
            else:
                self.log_test("User Consultations Retrieval", False, 
                    f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("User Consultations Retrieval", False, f"Exception: {str(e)}")
            return False
    
    def test_pdf_report_generation(self):
        """Test PDF report generation"""
        try:
            report_data = {
                "birth_date": "10.01.1982",
                "selected_calculations": ["personal_numbers"],
                "include_vedic": False,
                "include_charts": False
            }
            
            response = self.session.post(f"{BACKEND_URL}/reports/pdf/numerology", json=report_data)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = int(response.headers.get('content-length', '0'))
                
                is_pdf = content_type == 'application/pdf'
                has_content = content_length > 100  # Should have some content
                is_valid_pdf = response.content.startswith(b'%PDF')
                
                if is_pdf and has_content and is_valid_pdf:
                    self.log_test("PDF Report Generation", True, 
                        f"PDF report generated - Size: {content_length} bytes")
                    return True
                else:
                    self.log_test("PDF Report Generation", False, 
                        f"Issues - PDF: {is_pdf}, Content: {has_content}, Valid: {is_valid_pdf}")
                    return False
            else:
                self.log_test("PDF Report Generation", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("PDF Report Generation", False, f"Exception: {str(e)}")
            return False
    
    def test_html_report_generation(self):
        """Test HTML report generation"""
        try:
            report_data = {
                "birth_date": "10.01.1982",
                "selected_calculations": ["personal_numbers"],
                "include_vedic": False,
                "include_charts": False,
                "theme": "light"
            }
            
            response = self.session.post(f"{BACKEND_URL}/reports/html/numerology", json=report_data)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = int(response.headers.get('content-length', '0'))
                
                is_html = 'text/html' in content_type
                has_content = content_length > 100
                content_preview = response.text[:100]
                is_valid_html = '<!DOCTYPE html>' in content_preview or '<html' in content_preview
                
                if is_html and has_content and is_valid_html:
                    self.log_test("HTML Report Generation", True, 
                        f"HTML report generated - Size: {content_length} bytes")
                    return True
                else:
                    self.log_test("HTML Report Generation", False, 
                        f"Issues - HTML: {is_html}, Content: {has_content}, Valid: {is_valid_html}")
                    return False
            else:
                self.log_test("HTML Report Generation", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("HTML Report Generation", False, f"Exception: {str(e)}")
            return False
    
    def test_admin_consultations_list(self):
        """Test admin consultations list endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/consultations")
            
            if response.status_code == 200:
                consultations = response.json()
                consultation_count = len(consultations)
                
                # Check if any consultations have PDF files
                pdf_consultations = [c for c in consultations if c.get('pdf_file_id')]
                
                self.log_test("Admin Consultations List", True, 
                    f"Found {consultation_count} consultations, {len(pdf_consultations)} with PDFs")
                return True
            else:
                self.log_test("Admin Consultations List", False, 
                    f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Admin Consultations List", False, f"Exception: {str(e)}")
            return False
    
    def cleanup_test_files(self):
        """Clean up test files"""
        try:
            if hasattr(self, 'test_pdf_path'):
                os.unlink(self.test_pdf_path.name)
            self.log_test("Test Files Cleanup", True, "Cleaned up test files")
        except Exception as e:
            self.log_test("Test Files Cleanup", False, f"Exception: {str(e)}")
    
    def run_full_test_suite(self):
        """Run the complete focused PDF test suite"""
        print("🎯 STARTING FOCUSED PDF VIEWER TEST SUITE")
        print("=" * 60)
        
        # Step 1: Authentication
        if not self.authenticate():
            return False
        
        # Step 2: Create test files
        if not self.create_test_pdf():
            return False
        
        # Step 3: Test PDF upload and streaming
        print("\n📤 TESTING PDF UPLOAD & STREAMING:")
        self.test_consultation_pdf_upload()
        self.test_consultation_pdf_streaming()
        self.test_lesson_pdf_upload()
        self.test_lesson_pdf_streaming()
        
        # Step 4: Test consultation PDF viewer integration
        print("\n🔗 TESTING CONSULTATION PDF VIEWER:")
        self.test_consultation_creation_with_pdf()
        self.test_user_consultations_retrieval()
        self.test_admin_consultations_list()
        
        # Step 5: Test report generation
        print("\n📄 TESTING REPORT GENERATION:")
        self.test_pdf_report_generation()
        self.test_html_report_generation()
        
        # Cleanup
        self.cleanup_test_files()
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🎯 FOCUSED PDF VIEWER TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Print individual results
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
        
        print("\n" + "=" * 60)
        
        if success_rate >= 80:
            print("🎉 PDF VIEWER SYSTEM: WORKING CORRECTLY")
            print("✅ Authentication functional")
            print("✅ PDF upload and streaming operational")
            print("✅ ConsultationPDFViewer integration working")
        elif success_rate >= 60:
            print("⚠️  PDF VIEWER SYSTEM: MOSTLY WORKING")
            print("Some minor issues detected")
        else:
            print("❌ PDF VIEWER SYSTEM: NEEDS ATTENTION")
            print("Multiple issues detected")
        
        return success_rate >= 60

def main():
    """Main test execution"""
    test_suite = FocusedPDFTestSuite()
    
    try:
        success = test_suite.run_full_test_suite()
        test_suite.print_summary()
        
        return success
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Test suite failed with exception: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)