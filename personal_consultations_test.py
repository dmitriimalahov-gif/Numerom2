#!/usr/bin/env python3
"""
Backend API Testing for Personal Consultations
Testing all endpoints for personal consultations according to review request
"""

import requests
import json
import uuid
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://numerology-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Super admin credentials as specified in review request
SUPER_ADMIN_EMAIL = "dmitrii.malahov@gmail.com"
SUPER_ADMIN_PASSWORD = "756bvy67H"

class PersonalConsultationsAPITester:
    def __init__(self):
        self.super_admin_token = None
        self.regular_user_token = None
        self.regular_user_id = None
        self.test_consultation_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'details': details
        })
    
    def authenticate_super_admin(self):
        """Authenticate super admin user"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "email": SUPER_ADMIN_EMAIL,
                "password": SUPER_ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.super_admin_token = data['access_token']
                user_info = data['user']
                
                self.log_test(
                    "Super Admin Authentication",
                    True,
                    f"Successfully authenticated super admin with {user_info['credits_remaining']} credits",
                    f"User ID: {user_info['id']}, is_super_admin: {user_info['is_super_admin']}"
                )
                return True
            else:
                self.log_test(
                    "Super Admin Authentication",
                    False,
                    f"Failed to authenticate: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Super Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def create_regular_user(self):
        """Create and authenticate a regular user for testing"""
        try:
            # Create unique user
            test_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
            
            # Register user
            response = requests.post(f"{API_BASE}/auth/register", json={
                "email": test_email,
                "password": "testpassword123",
                "full_name": "Test User",
                "birth_date": "15.03.1990",
                "city": "Москва"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.regular_user_token = data['access_token']
                self.regular_user_id = data['user']['id']
                
                self.log_test(
                    "Regular User Creation",
                    True,
                    f"Created regular user with {data['user']['credits_remaining']} credits",
                    f"User ID: {self.regular_user_id}, Email: {test_email}"
                )
                return True
            else:
                self.log_test(
                    "Regular User Creation",
                    False,
                    f"Failed to create user: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Regular User Creation", False, f"Exception: {str(e)}")
            return False
    
    def test_admin_get_consultations(self):
        """Test GET /api/admin/consultations"""
        try:
            headers = {"Authorization": f"Bearer {self.super_admin_token}"}
            response = requests.get(f"{API_BASE}/admin/consultations", headers=headers)
            
            if response.status_code == 200:
                consultations = response.json()
                self.log_test(
                    "Admin Get All Consultations",
                    True,
                    f"Retrieved {len(consultations)} consultations",
                    f"Response type: {type(consultations)}"
                )
                return True
            else:
                self.log_test(
                    "Admin Get All Consultations",
                    False,
                    f"Failed: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Admin Get All Consultations", False, f"Exception: {str(e)}")
            return False
    
    def test_admin_create_consultation(self):
        """Test POST /api/admin/consultations"""
        try:
            headers = {"Authorization": f"Bearer {self.super_admin_token}"}
            
            # Create consultation data according to PersonalConsultation model
            consultation_data = {
                "title": "Test Personal Consultation",
                "description": "This is a test consultation for API testing",
                "video_url": "https://www.youtube.com/watch?v=test123",
                "video_file": None,
                "assigned_user_id": self.regular_user_id,
                "cost_credits": 10000,  # Default cost as per requirements
                "is_active": True
            }
            
            response = requests.post(f"{API_BASE}/admin/consultations", 
                                   json=consultation_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.test_consultation_id = data.get('consultation_id')
                
                self.log_test(
                    "Admin Create Consultation",
                    True,
                    f"Created consultation with ID: {self.test_consultation_id}",
                    f"Cost: {consultation_data['cost_credits']} credits"
                )
                return True
            else:
                self.log_test(
                    "Admin Create Consultation",
                    False,
                    f"Failed: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Admin Create Consultation", False, f"Exception: {str(e)}")
            return False
    
    def test_admin_update_consultation(self):
        """Test PUT /api/admin/consultations/{id}"""
        if not self.test_consultation_id:
            self.log_test("Admin Update Consultation", False, "No consultation ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.super_admin_token}"}
            
            update_data = {
                "title": "Updated Test Consultation",
                "description": "Updated description for testing",
                "cost_credits": 15000  # Changed cost
            }
            
            response = requests.put(f"{API_BASE}/admin/consultations/{self.test_consultation_id}",
                                  json=update_data, headers=headers)
            
            if response.status_code == 200:
                self.log_test(
                    "Admin Update Consultation",
                    True,
                    "Successfully updated consultation",
                    f"New cost: {update_data['cost_credits']} credits"
                )
                return True
            else:
                self.log_test(
                    "Admin Update Consultation",
                    False,
                    f"Failed: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Admin Update Consultation", False, f"Exception: {str(e)}")
            return False
    
    def test_user_get_consultations(self):
        """Test GET /api/user/consultations"""
        try:
            headers = {"Authorization": f"Bearer {self.regular_user_token}"}
            response = requests.get(f"{API_BASE}/user/consultations", headers=headers)
            
            if response.status_code == 200:
                consultations = response.json()
                assigned_consultations = [c for c in consultations if c.get('assigned_user_id') == self.regular_user_id]
                
                self.log_test(
                    "User Get Assigned Consultations",
                    True,
                    f"Retrieved {len(assigned_consultations)} assigned consultations out of {len(consultations)} total",
                    f"User sees only consultations assigned to them"
                )
                return True
            else:
                self.log_test(
                    "User Get Assigned Consultations",
                    False,
                    f"Failed: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("User Get Assigned Consultations", False, f"Exception: {str(e)}")
            return False
    
    def add_credits_to_user(self, credits_amount):
        """Add credits to regular user using admin endpoint"""
        try:
            headers = {"Authorization": f"Bearer {self.super_admin_token}"}
            response = requests.patch(f"{API_BASE}/admin/users/{self.regular_user_id}/credits",
                                    json={"credits_remaining": credits_amount}, headers=headers)
            
            if response.status_code == 200:
                self.log_test(
                    "Add Credits to User",
                    True,
                    f"Added {credits_amount} credits to user",
                    f"User ID: {self.regular_user_id}"
                )
                return True
            else:
                self.log_test(
                    "Add Credits to User",
                    False,
                    f"Failed: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Add Credits to User", False, f"Exception: {str(e)}")
            return False
    
    def test_user_purchase_consultation_success(self):
        """Test POST /api/user/consultations/{id}/purchase - successful purchase"""
        if not self.test_consultation_id:
            self.log_test("User Purchase Consultation (Success)", False, "No consultation ID available")
            return False
        
        # First, ensure user has enough credits
        if not self.add_credits_to_user(20000):  # More than enough for 15000 cost
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.regular_user_token}"}
            response = requests.post(f"{API_BASE}/user/consultations/{self.test_consultation_id}/purchase",
                                   headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                credits_spent = data.get('credits_spent', 0)
                
                self.log_test(
                    "User Purchase Consultation (Success)",
                    True,
                    f"Successfully purchased consultation for {credits_spent} credits",
                    data.get('message', '')
                )
                return True
            else:
                self.log_test(
                    "User Purchase Consultation (Success)",
                    False,
                    f"Failed: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("User Purchase Consultation (Success)", False, f"Exception: {str(e)}")
            return False
    
    def test_user_purchase_consultation_duplicate(self):
        """Test POST /api/user/consultations/{id}/purchase - prevent double purchase"""
        if not self.test_consultation_id:
            self.log_test("User Purchase Consultation (Duplicate)", False, "No consultation ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.regular_user_token}"}
            response = requests.post(f"{API_BASE}/user/consultations/{self.test_consultation_id}/purchase",
                                   headers=headers)
            
            if response.status_code == 400:
                self.log_test(
                    "User Purchase Consultation (Duplicate)",
                    True,
                    "Correctly prevented duplicate purchase",
                    response.json().get('detail', response.text)
                )
                return True
            else:
                self.log_test(
                    "User Purchase Consultation (Duplicate)",
                    False,
                    f"Should have returned 400, got: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("User Purchase Consultation (Duplicate)", False, f"Exception: {str(e)}")
            return False
    
    def test_user_purchase_insufficient_credits(self):
        """Test POST /api/user/consultations/{id}/purchase - insufficient credits"""
        # Create another consultation for this test
        try:
            headers = {"Authorization": f"Bearer {self.super_admin_token}"}
            
            # Create new user with minimal credits
            test_email = f"poor_user_{uuid.uuid4().hex[:8]}@example.com"
            
            # Register user
            response = requests.post(f"{API_BASE}/auth/register", json={
                "email": test_email,
                "password": "testpassword123",
                "full_name": "Poor Test User",
                "birth_date": "20.05.1985",
                "city": "Москва"
            })
            
            if response.status_code != 200:
                self.log_test("User Purchase Consultation (Insufficient Credits)", False, "Failed to create poor user")
                return False
            
            poor_user_data = response.json()
            poor_user_token = poor_user_data['access_token']
            poor_user_id = poor_user_data['user']['id']
            
            # Create consultation for poor user
            consultation_data = {
                "title": "Expensive Test Consultation",
                "description": "This consultation costs more than user has",
                "assigned_user_id": poor_user_id,
                "cost_credits": 10000,  # User only has 1 credit by default
                "is_active": True
            }
            
            response = requests.post(f"{API_BASE}/admin/consultations", 
                                   json=consultation_data, headers=headers)
            
            if response.status_code != 200:
                self.log_test("User Purchase Consultation (Insufficient Credits)", False, "Failed to create expensive consultation")
                return False
            
            expensive_consultation_id = response.json().get('consultation_id')
            
            # Try to purchase with insufficient credits
            poor_headers = {"Authorization": f"Bearer {poor_user_token}"}
            response = requests.post(f"{API_BASE}/user/consultations/{expensive_consultation_id}/purchase",
                                   headers=poor_headers)
            
            if response.status_code == 402:
                self.log_test(
                    "User Purchase Consultation (Insufficient Credits)",
                    True,
                    "Correctly returned 402 for insufficient credits",
                    response.json().get('detail', response.text)
                )
                return True
            else:
                self.log_test(
                    "User Purchase Consultation (Insufficient Credits)",
                    False,
                    f"Should have returned 402, got: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("User Purchase Consultation (Insufficient Credits)", False, f"Exception: {str(e)}")
            return False
    
    def test_admin_delete_consultation(self):
        """Test DELETE /api/admin/consultations/{id}"""
        if not self.test_consultation_id:
            self.log_test("Admin Delete Consultation", False, "No consultation ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.super_admin_token}"}
            response = requests.delete(f"{API_BASE}/admin/consultations/{self.test_consultation_id}",
                                     headers=headers)
            
            if response.status_code == 200:
                self.log_test(
                    "Admin Delete Consultation",
                    True,
                    "Successfully deleted consultation",
                    response.json().get('message', '')
                )
                return True
            else:
                self.log_test(
                    "Admin Delete Consultation",
                    False,
                    f"Failed: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Admin Delete Consultation", False, f"Exception: {str(e)}")
            return False
    
    def test_user_access_control(self):
        """Test that regular users cannot access admin endpoints"""
        try:
            headers = {"Authorization": f"Bearer {self.regular_user_token}"}
            
            # Try to access admin endpoint
            response = requests.get(f"{API_BASE}/admin/consultations", headers=headers)
            
            if response.status_code == 403:
                self.log_test(
                    "User Access Control",
                    True,
                    "Regular user correctly denied access to admin endpoints",
                    "403 Forbidden as expected"
                )
                return True
            else:
                self.log_test(
                    "User Access Control",
                    False,
                    f"Should have returned 403, got: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("User Access Control", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all personal consultations API tests"""
        print("🚀 Starting Personal Consultations Backend API Testing")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Authentication tests
        if not self.authenticate_super_admin():
            print("❌ Cannot proceed without super admin authentication")
            return False
        
        if not self.create_regular_user():
            print("❌ Cannot proceed without regular user")
            return False
        
        # Admin endpoint tests
        self.test_admin_get_consultations()
        self.test_admin_create_consultation()
        self.test_admin_update_consultation()
        
        # User endpoint tests
        self.test_user_get_consultations()
        self.test_user_purchase_consultation_success()
        self.test_user_purchase_consultation_duplicate()
        self.test_user_purchase_insufficient_credits()
        
        # Access control tests
        self.test_user_access_control()
        
        # Cleanup
        self.test_admin_delete_consultation()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Personal Consultations API is working correctly.")
            return True
        else:
            print(f"\n⚠️  {total - passed} tests failed. See details above.")
            return False

def main():
    """Main test execution"""
    tester = PersonalConsultationsAPITester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()