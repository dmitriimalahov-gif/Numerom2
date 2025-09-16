#!/usr/bin/env python3
"""
REVIEW REQUEST TESTING: AdminPanel Delete Functions & Consultation User Selection
Testing new DELETE endpoints and consultation functionality as specified in review request.

NEW ENDPOINTS TO TEST:
1. DELETE /api/admin/lessons/{lesson_id} - delete lessons (new endpoint)
2. DELETE /api/admin/users/{user_id} - delete users (new endpoint)

ALSO TEST:
- Consultation endpoints with proper assigned_user_id field
- User selection functionality for consultations
"""

import requests
import json
import uuid
from datetime import datetime
import sys

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"

class DeleteFunctionsTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.super_admin_data = None
        self.test_results = []
        self.created_lesson_id = None
        self.created_user_id = None
        
    def log_test(self, test_name, status, details=""):
        """Log test results"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {details}")
        
    def authenticate_super_admin(self):
        """Authenticate super admin user"""
        print("\n🔐 STEP 1: SUPER ADMIN AUTHENTICATION")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": SUPER_ADMIN_EMAIL,
                "password": SUPER_ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data['access_token']
                self.super_admin_data = data['user']
                self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                
                # Verify super admin status
                if self.super_admin_data.get('is_super_admin'):
                    self.log_test("Super Admin Authentication", "PASS", 
                                f"Authenticated as {SUPER_ADMIN_EMAIL}, Credits: {self.super_admin_data.get('credits_remaining', 0)}")
                    return True
                else:
                    self.log_test("Super Admin Authentication", "FAIL", "User is not super admin")
                    return False
            else:
                self.log_test("Super Admin Authentication", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Super Admin Authentication", "FAIL", f"Exception: {str(e)}")
            return False
    
    def create_test_lesson(self):
        """Create a test lesson for deletion testing"""
        print("\n📚 STEP 2: CREATE TEST LESSON")
        
        try:
            lesson_data = {
                "id": str(uuid.uuid4()),
                "title": "Test Lesson for Deletion",
                "description": "This lesson will be deleted during testing",
                "video_url": "https://example.com/test-video.mp4",
                "duration_minutes": 30,
                "level": 1,
                "order": 999,
                "is_active": True,
                "points_for_lesson": 0
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/lessons", json=lesson_data)
            
            if response.status_code == 200:
                self.created_lesson_id = lesson_data["id"]
                self.log_test("Create Test Lesson", "PASS", f"Created lesson with ID: {self.created_lesson_id}")
                return True
            else:
                self.log_test("Create Test Lesson", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Create Test Lesson", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_delete_lesson_success(self):
        """Test successful lesson deletion"""
        print("\n🗑️ STEP 3: TEST DELETE LESSON (SUCCESS)")
        
        if not self.created_lesson_id:
            self.log_test("Delete Lesson Success", "SKIP", "No test lesson created")
            return False
            
        try:
            response = self.session.delete(f"{BACKEND_URL}/admin/lessons/{self.created_lesson_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Delete Lesson Success", "PASS", f"Lesson deleted successfully: {data.get('message', '')}")
                
                # Verify lesson is actually deleted by trying to fetch it
                verify_response = self.session.get(f"{BACKEND_URL}/admin/lessons")
                if verify_response.status_code == 200:
                    lessons = verify_response.json()
                    lesson_exists = any(lesson.get('id') == self.created_lesson_id for lesson in lessons)
                    if not lesson_exists:
                        self.log_test("Verify Lesson Deletion", "PASS", "Lesson successfully removed from database")
                    else:
                        self.log_test("Verify Lesson Deletion", "FAIL", "Lesson still exists in database")
                
                return True
            else:
                self.log_test("Delete Lesson Success", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Delete Lesson Success", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_delete_lesson_not_found(self):
        """Test lesson deletion with non-existent lesson ID"""
        print("\n🔍 STEP 4: TEST DELETE LESSON (404 ERROR)")
        
        try:
            fake_lesson_id = str(uuid.uuid4())
            response = self.session.delete(f"{BACKEND_URL}/admin/lessons/{fake_lesson_id}")
            
            if response.status_code == 404:
                self.log_test("Delete Lesson Not Found", "PASS", "Correctly returned 404 for non-existent lesson")
                return True
            else:
                self.log_test("Delete Lesson Not Found", "FAIL", f"Expected 404, got {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Delete Lesson Not Found", "FAIL", f"Exception: {str(e)}")
            return False
    
    def create_test_user(self):
        """Create a test user for deletion testing"""
        print("\n👤 STEP 5: CREATE TEST USER")
        
        try:
            # First, logout from super admin to register new user
            temp_session = requests.Session()
            
            user_data = {
                "email": f"testuser_{uuid.uuid4().hex[:8]}@example.com",
                "password": "testpassword123",
                "full_name": "Test User for Deletion",
                "birth_date": "15.03.1990",
                "city": "Москва"
            }
            
            response = temp_session.post(f"{BACKEND_URL}/auth/register", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                self.created_user_id = data['user']['id']
                self.log_test("Create Test User", "PASS", f"Created user with ID: {self.created_user_id}, Email: {user_data['email']}")
                return True
            else:
                self.log_test("Create Test User", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Create Test User", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_delete_user_success(self):
        """Test successful user deletion"""
        print("\n🗑️ STEP 6: TEST DELETE USER (SUCCESS)")
        
        if not self.created_user_id:
            self.log_test("Delete User Success", "SKIP", "No test user created")
            return False
            
        try:
            response = self.session.delete(f"{BACKEND_URL}/admin/users/{self.created_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Delete User Success", "PASS", f"User deleted successfully: {data.get('message', '')}")
                
                # Verify user is actually deleted by trying to fetch users list
                verify_response = self.session.get(f"{BACKEND_URL}/admin/users")
                if verify_response.status_code == 200:
                    users_data = verify_response.json()
                    users = users_data.get('users', [])
                    user_exists = any(user.get('id') == self.created_user_id for user in users)
                    if not user_exists:
                        self.log_test("Verify User Deletion", "PASS", "User successfully removed from database")
                    else:
                        self.log_test("Verify User Deletion", "FAIL", "User still exists in database")
                
                return True
            else:
                self.log_test("Delete User Success", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Delete User Success", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_delete_super_admin_protection(self):
        """Test that super admin cannot be deleted"""
        print("\n🛡️ STEP 7: TEST DELETE SUPER ADMIN (403 ERROR)")
        
        try:
            super_admin_id = self.super_admin_data.get('id')
            response = self.session.delete(f"{BACKEND_URL}/admin/users/{super_admin_id}")
            
            if response.status_code == 403:
                self.log_test("Delete Super Admin Protection", "PASS", "Correctly prevented super admin deletion with 403 error")
                return True
            else:
                self.log_test("Delete Super Admin Protection", "FAIL", f"Expected 403, got {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Delete Super Admin Protection", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_delete_user_not_found(self):
        """Test user deletion with non-existent user ID"""
        print("\n🔍 STEP 8: TEST DELETE USER (404 ERROR)")
        
        try:
            fake_user_id = str(uuid.uuid4())
            response = self.session.delete(f"{BACKEND_URL}/admin/users/{fake_user_id}")
            
            if response.status_code == 404:
                self.log_test("Delete User Not Found", "PASS", "Correctly returned 404 for non-existent user")
                return True
            else:
                self.log_test("Delete User Not Found", "FAIL", f"Expected 404, got {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Delete User Not Found", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_regular_user_delete_access(self):
        """Test that regular users cannot access delete endpoints"""
        print("\n🚫 STEP 9: TEST REGULAR USER DELETE ACCESS (403 ERROR)")
        
        try:
            # Create a regular user session
            temp_session = requests.Session()
            
            # Register a regular user
            user_data = {
                "email": f"regular_{uuid.uuid4().hex[:8]}@example.com",
                "password": "regularpassword123",
                "full_name": "Regular User",
                "birth_date": "20.05.1985",
                "city": "Москва"
            }
            
            register_response = temp_session.post(f"{BACKEND_URL}/auth/register", json=user_data)
            
            if register_response.status_code == 200:
                data = register_response.json()
                regular_token = data['access_token']
                temp_session.headers.update({'Authorization': f'Bearer {regular_token}'})
                
                # Try to delete a lesson (should fail)
                fake_lesson_id = str(uuid.uuid4())
                delete_response = temp_session.delete(f"{BACKEND_URL}/admin/lessons/{fake_lesson_id}")
                
                if delete_response.status_code == 403:
                    self.log_test("Regular User Delete Access", "PASS", "Regular user correctly denied access to delete endpoints")
                    return True
                else:
                    self.log_test("Regular User Delete Access", "FAIL", f"Expected 403, got {delete_response.status_code}")
                    return False
            else:
                self.log_test("Regular User Delete Access", "FAIL", f"Failed to create regular user: {register_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Regular User Delete Access", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_consultation_user_selection(self):
        """Test consultation endpoints with proper assigned_user_id field"""
        print("\n💬 STEP 10: TEST CONSULTATION USER SELECTION")
        
        try:
            # First, get all consultations to see current state
            consultations_response = self.session.get(f"{BACKEND_URL}/admin/consultations")
            
            if consultations_response.status_code == 200:
                consultations = consultations_response.json()
                self.log_test("Get Consultations", "PASS", f"Retrieved {len(consultations)} consultations")
                
                # Check if consultations have assigned_user_id field
                if consultations:
                    first_consultation = consultations[0]
                    if 'assigned_user_id' in first_consultation:
                        self.log_test("Consultation User Selection Field", "PASS", "assigned_user_id field present in consultations")
                    else:
                        self.log_test("Consultation User Selection Field", "FAIL", "assigned_user_id field missing from consultations")
                
                # Test user consultations endpoint
                user_consultations_response = self.session.get(f"{BACKEND_URL}/user/consultations")
                
                if user_consultations_response.status_code == 200:
                    user_consultations = user_consultations_response.json()
                    self.log_test("User Consultations", "PASS", f"User can access their consultations: {len(user_consultations)} found")
                    
                    # Check if user sees only their assigned consultations
                    super_admin_id = self.super_admin_data.get('id')
                    assigned_to_user = all(
                        consultation.get('assigned_user_id') == super_admin_id 
                        for consultation in user_consultations
                    )
                    
                    if assigned_to_user or len(user_consultations) == 0:
                        self.log_test("User Consultation Filtering", "PASS", "User sees only consultations assigned to them")
                    else:
                        self.log_test("User Consultation Filtering", "FAIL", "User sees consultations not assigned to them")
                    
                    return True
                else:
                    self.log_test("User Consultations", "FAIL", f"Status: {user_consultations_response.status_code}")
                    return False
                    
            else:
                self.log_test("Get Consultations", "FAIL", f"Status: {consultations_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Consultation User Selection", "FAIL", f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all delete function tests"""
        print("🧪 STARTING DELETE FUNCTIONS TESTING")
        print("=" * 60)
        
        # Step 1: Authenticate super admin
        if not self.authenticate_super_admin():
            print("❌ Cannot proceed without super admin authentication")
            return False
        
        # Step 2: Create test lesson
        self.create_test_lesson()
        
        # Step 3: Test lesson deletion (success)
        self.test_delete_lesson_success()
        
        # Step 4: Test lesson deletion (404 error)
        self.test_delete_lesson_not_found()
        
        # Step 5: Create test user
        self.create_test_user()
        
        # Step 6: Test user deletion (success)
        self.test_delete_user_success()
        
        # Step 7: Test super admin protection
        self.test_delete_super_admin_protection()
        
        # Step 8: Test user deletion (404 error)
        self.test_delete_user_not_found()
        
        # Step 9: Test regular user access
        self.test_regular_user_delete_access()
        
        # Step 10: Test consultation user selection
        self.test_consultation_user_selection()
        
        # Summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🎯 DELETE FUNCTIONS TESTING SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['status'] == 'PASS')
        failed = sum(1 for result in self.test_results if result['status'] == 'FAIL')
        skipped = sum(1 for result in self.test_results if result['status'] == 'SKIP')
        total = len(self.test_results)
        
        print(f"📊 RESULTS: {passed} PASSED, {failed} FAILED, {skipped} SKIPPED out of {total} tests")
        print(f"📈 SUCCESS RATE: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"   • {result['test']}: {result['details']}")
        
        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result['status'] == 'PASS':
                print(f"   • {result['test']}: {result['details']}")
        
        # Determine overall status
        critical_failures = [
            "Super Admin Authentication",
            "Delete Lesson Success", 
            "Delete User Success",
            "Delete Super Admin Protection"
        ]
        
        critical_failed = any(
            result['test'] in critical_failures and result['status'] == 'FAIL' 
            for result in self.test_results
        )
        
        if critical_failed:
            print("\n🚨 CRITICAL ISSUES FOUND - DELETE FUNCTIONS NOT WORKING PROPERLY")
            return False
        elif failed == 0:
            print("\n🎉 ALL TESTS PASSED - DELETE FUNCTIONS WORKING CORRECTLY")
            return True
        else:
            print("\n⚠️ MINOR ISSUES FOUND - DELETE FUNCTIONS MOSTLY WORKING")
            return True

if __name__ == "__main__":
    tester = DeleteFunctionsTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)