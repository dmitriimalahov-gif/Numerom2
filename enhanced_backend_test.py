#!/usr/bin/env python3
"""
Enhanced NUMEROM Backend API Testing Suite
Tests all enhanced backend functionality including Vedic numerology, randomized quiz, 
planetary energy charts, learning management system, and admin panel.
"""

import requests
import json
import os
from datetime import datetime
import time
import random

# Get backend URL from environment
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

class EnhancedNumeromAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.auth_token = None
        self.admin_token = None
        self.user_data = {
            "email": f"testuser{int(time.time())}@numerom.com",
            "password": "SecurePass123!",
            "full_name": "Enhanced Test User",
            "birth_date": "15.03.1990"
        }
        self.admin_data = {
            "email": f"admin{int(time.time())}@numerom.com", 
            "password": "AdminPass123!",
            "full_name": "Test Admin User",
            "birth_date": "22.07.1985"
        }
        self.test_results = []
        
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
    
    def make_request(self, method, endpoint, data=None, headers=None, use_admin_token=False):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        default_headers = {"Content-Type": "application/json"}
        
        if headers:
            default_headers.update(headers)
            
        # Use appropriate token
        token = self.admin_token if use_admin_token else self.auth_token
        if token and "Authorization" not in default_headers:
            default_headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=default_headers, timeout=30)
            elif method.upper() == "POST":
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
    
    def setup_test_users(self):
        """Setup regular user and admin user for testing"""
        # Register regular user
        response = self.make_request("POST", "/auth/register", self.user_data)
        if response and response.status_code == 200:
            data = response.json()
            self.auth_token = data["access_token"]
            self.log_result("User Setup", True, "Regular user registered successfully")
        else:
            self.log_result("User Setup", False, "Failed to register regular user")
            return False
        
        # Register admin user
        response = self.make_request("POST", "/auth/register", self.admin_data)
        if response and response.status_code == 200:
            data = response.json()
            self.admin_token = data["access_token"]
            admin_user_id = data["user"]["id"]
            
            # Make this user an admin
            admin_response = self.make_request("POST", f"/admin/make-admin/{admin_user_id}", {})
            if admin_response and admin_response.status_code == 200:
                self.log_result("Admin Setup", True, "Admin user created successfully")
                return True
            else:
                self.log_result("Admin Setup", False, "Failed to grant admin privileges")
        else:
            self.log_result("Admin Setup", False, "Failed to register admin user")
        
        return False
    
    def test_enhanced_vedic_numerology(self):
        """Test enhanced Vedic numerology comprehensive endpoint"""
        if not self.auth_token:
            self.log_result("Vedic Numerology", False, "No auth token available")
            return False
        
        # Test with name parameter
        test_data = {"name": "Vedic Test User"}
        response = self.make_request("POST", "/numerology/vedic/comprehensive", test_data)
        
        if response and response.status_code == 200:
            data = response.json()
            required_fields = [
                "janma_ank", "nama_ank", "bhagya_ank", "atma_ank", "shakti_ank",
                "graha_shakti", "mahadasha", "antardasha", "yantra_matrix", 
                "yantra_sums", "graha_names", "upayas", "mantras", "gemstones"
            ]
            
            missing_fields = [field for field in required_fields if field not in data]
            if not missing_fields:
                # Verify Sanskrit terminology
                graha_names = data.get("graha_names", {})
                if "सूर्य (Surya)" in graha_names.values():
                    # Verify yantra has proper planetary colors/positions
                    yantra_matrix = data.get("yantra_matrix", [])
                    if len(yantra_matrix) == 3 and len(yantra_matrix[0]) == 3:
                        # Verify remedies in Sanskrit
                        upayas = data.get("upayas", [])
                        if any("सूर्य" in upaya or "चन्द्र" in upaya for upaya in upayas):
                            self.log_result("Vedic Numerology", True, 
                                          "Enhanced Vedic numerology with Sanskrit terminology working")
                            return True
                        else:
                            self.log_result("Vedic Numerology", False, 
                                          "Sanskrit remedies not found", data)
                    else:
                        self.log_result("Vedic Numerology", False, 
                                      "Invalid yantra matrix structure", yantra_matrix)
                else:
                    self.log_result("Vedic Numerology", False, 
                                  "Sanskrit planetary names not found", graha_names)
            else:
                self.log_result("Vedic Numerology", False, 
                              f"Missing fields: {missing_fields}", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Vedic Numerology", False, "Failed to get Vedic analysis", error)
        
        return False
    
    def test_randomized_quiz_system(self):
        """Test randomized quiz system with multiple calls to verify randomization"""
        # Test getting randomized questions multiple times
        quiz_sets = []
        
        for i in range(3):  # Get 3 different quiz sets
            response = self.make_request("GET", "/quiz/randomized-questions")
            
            if response and response.status_code == 200:
                data = response.json()
                required_fields = ["session_id", "title", "description", "questions"]
                
                if all(field in data for field in required_fields):
                    questions = data.get("questions", [])
                    if len(questions) == 10:
                        # Check if questions have proper structure
                        first_q = questions[0]
                        if all(field in first_q for field in ["id", "question", "options", "category"]):
                            quiz_sets.append([q["id"] for q in questions])
                        else:
                            self.log_result("Randomized Quiz", False, 
                                          f"Invalid question structure in set {i+1}", first_q)
                            return False
                    else:
                        self.log_result("Randomized Quiz", False, 
                                      f"Expected 10 questions, got {len(questions)} in set {i+1}")
                        return False
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("Randomized Quiz", False, 
                                  f"Missing fields in set {i+1}: {missing}", data)
                    return False
            else:
                error = response.text if response else "Connection failed"
                self.log_result("Randomized Quiz", False, 
                              f"Failed to get quiz set {i+1}", error)
                return False
        
        # Verify randomization - at least some questions should be different
        if len(quiz_sets) == 3:
            set1, set2, set3 = quiz_sets
            if set1 != set2 or set2 != set3 or set1 != set3:
                self.log_result("Randomized Quiz", True, 
                              "Quiz randomization working - different questions each time")
                return True
            else:
                self.log_result("Randomized Quiz", False, 
                              "Quiz not randomized - same questions returned")
        
        return False
    
    def test_planetary_energy_charts(self):
        """Test planetary energy chart endpoints"""
        if not self.auth_token:
            self.log_result("Planetary Energy Charts", False, "No auth token available")
            return False
        
        # Test weekly chart (7 days)
        response = self.make_request("GET", "/charts/planetary-energy/7")
        
        if response and response.status_code == 200:
            data = response.json()
            required_fields = ["chart_data", "period", "user_birth_date"]
            
            if all(field in data for field in required_fields):
                chart_data = data.get("chart_data", [])
                if len(chart_data) == 7:
                    # Check first day structure
                    first_day = chart_data[0]
                    planetary_fields = ["surya", "chandra", "mangal", "budha", "guru", 
                                      "shukra", "shani", "rahu", "ketu"]
                    
                    if all(field in first_day for field in planetary_fields + ["date", "day_name"]):
                        # Test monthly chart (30 days)
                        monthly_response = self.make_request("GET", "/charts/planetary-energy/30")
                        
                        if monthly_response and monthly_response.status_code == 200:
                            monthly_data = monthly_response.json()
                            monthly_chart = monthly_data.get("chart_data", [])
                            
                            if len(monthly_chart) == 30:
                                self.log_result("Planetary Energy Charts", True, 
                                              "Weekly and monthly planetary energy charts working")
                                return True
                            else:
                                self.log_result("Planetary Energy Charts", False, 
                                              f"Monthly chart has {len(monthly_chart)} days, expected 30")
                        else:
                            self.log_result("Planetary Energy Charts", False, 
                                          "Monthly chart request failed")
                    else:
                        missing = [f for f in planetary_fields + ["date", "day_name"] if f not in first_day]
                        self.log_result("Planetary Energy Charts", False, 
                                      f"Missing planetary data: {missing}", first_day)
                else:
                    self.log_result("Planetary Energy Charts", False, 
                                  f"Weekly chart has {len(chart_data)} days, expected 7")
            else:
                missing = [f for f in required_fields if f not in data]
                self.log_result("Planetary Energy Charts", False, 
                              f"Missing fields: {missing}", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Planetary Energy Charts", False, 
                          "Failed to get planetary energy chart", error)
        
        return False
    
    def test_learning_management_system(self):
        """Test learning management system endpoints"""
        if not self.auth_token:
            self.log_result("Learning Management", False, "No auth token available")
            return False
        
        # Test get learning levels
        response = self.make_request("GET", "/learning/levels")
        
        if response and response.status_code == 200:
            data = response.json()
            required_fields = ["user_level", "available_lessons", "total_levels"]
            
            if all(field in data for field in required_fields):
                user_level = data.get("user_level", {})
                if "current_level" in user_level and "experience_points" in user_level:
                    # Create a test lesson first (as admin)
                    if self.admin_token:
                        lesson_data = {
                            "title": "Test Vedic Lesson",
                            "description": "Introduction to Vedic Numerology",
                            "video_url": "https://example.com/test-video.mp4",
                            "duration_minutes": 15,
                            "level": 1,
                            "order": 1,
                            "prerequisites": [],
                            "is_active": True
                        }
                        
                        create_response = self.make_request("POST", "/admin/lessons", 
                                                          lesson_data, use_admin_token=True)
                        
                        if create_response and create_response.status_code == 200:
                            lesson_id = create_response.json().get("lesson_id")
                            
                            # Test completing the lesson
                            complete_response = self.make_request("POST", 
                                                                f"/learning/complete-lesson/{lesson_id}?watch_time=15&quiz_score=85")
                            
                            if complete_response and complete_response.status_code == 200:
                                complete_data = complete_response.json()
                                expected_fields = ["lesson_completed", "experience_gained", 
                                                 "new_level", "total_completed"]
                                
                                if all(field in complete_data for field in expected_fields):
                                    if complete_data.get("lesson_completed") == True:
                                        self.log_result("Learning Management", True, 
                                                      "Learning system with level progression working")
                                        return True
                                    else:
                                        self.log_result("Learning Management", False, 
                                                      "Lesson not marked as completed")
                                else:
                                    missing = [f for f in expected_fields if f not in complete_data]
                                    self.log_result("Learning Management", False, 
                                                  f"Missing completion fields: {missing}")
                            else:
                                self.log_result("Learning Management", False, 
                                              "Failed to complete lesson")
                        else:
                            self.log_result("Learning Management", False, 
                                          "Failed to create test lesson")
                    else:
                        self.log_result("Learning Management", False, 
                                      "No admin token for lesson creation")
                else:
                    self.log_result("Learning Management", False, 
                                  "Invalid user level structure", user_level)
            else:
                missing = [f for f in required_fields if f not in data]
                self.log_result("Learning Management", False, 
                              f"Missing fields: {missing}", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Learning Management", False, 
                          "Failed to get learning levels", error)
        
        return False
    
    def test_admin_panel_functionality(self):
        """Test admin panel CRUD operations"""
        if not self.admin_token:
            self.log_result("Admin Panel", False, "No admin token available")
            return False
        
        # Test creating a lesson
        lesson_data = {
            "title": "Advanced Vedic Numerology",
            "description": "Deep dive into planetary influences",
            "video_url": "https://example.com/advanced-vedic.mp4",
            "duration_minutes": 25,
            "level": 2,
            "order": 1,
            "prerequisites": [],
            "is_active": True
        }
        
        create_response = self.make_request("POST", "/admin/lessons", 
                                          lesson_data, use_admin_token=True)
        
        if create_response and create_response.status_code == 200:
            create_data = create_response.json()
            lesson_id = create_data.get("lesson_id")
            
            if lesson_id:
                # Test getting all lessons
                get_response = self.make_request("GET", "/admin/lessons", 
                                               use_admin_token=True)
                
                if get_response and get_response.status_code == 200:
                    lessons = get_response.json()
                    
                    if isinstance(lessons, list) and len(lessons) > 0:
                        # Find our created lesson
                        created_lesson = next((l for l in lessons if l.get("id") == lesson_id), None)
                        
                        if created_lesson:
                            # Test updating the lesson
                            update_data = {
                                "title": "Updated Advanced Vedic Numerology",
                                "description": "Updated description"
                            }
                            
                            update_response = self.make_request("PUT", f"/admin/lessons/{lesson_id}",
                                                              update_data, use_admin_token=True)
                            
                            if update_response and update_response.status_code == 200:
                                self.log_result("Admin Panel", True, 
                                              "Admin CRUD operations working (create, read, update)")
                                return True
                            else:
                                self.log_result("Admin Panel", False, 
                                              "Failed to update lesson")
                        else:
                            self.log_result("Admin Panel", False, 
                                          "Created lesson not found in list")
                    else:
                        self.log_result("Admin Panel", False, 
                                      "No lessons returned or invalid format")
                else:
                    self.log_result("Admin Panel", False, 
                                  "Failed to get lessons list")
            else:
                self.log_result("Admin Panel", False, 
                              "No lesson ID returned from creation")
        else:
            error = create_response.text if create_response else "Connection failed"
            self.log_result("Admin Panel", False, 
                          "Failed to create lesson", error)
        
        return False
    
    def test_updated_payment_system(self):
        """Test all 3 pricing tiers in demo mode"""
        test_packages = {
            "one_time": 0.96,
            "monthly": 9.99, 
            "annual": 66.59  # Updated to match server
        }
        
        all_passed = True
        
        for package_type, expected_amount in test_packages.items():
            payment_data = {
                "package_type": package_type,
                "origin_url": "https://numerology-fix.preview.emergentagent.com"
            }
            
            response = self.make_request("POST", "/payments/checkout/session", payment_data)
            
            if response and response.status_code == 200:
                data = response.json()
                if "url" in data and "session_id" in data:
                    session_id = data["session_id"]
                    
                    # Test payment status
                    status_response = self.make_request("GET", f"/payments/checkout/status/{session_id}")
                    
                    if status_response and status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get("payment_status") == "paid":
                            # Verify amount (convert to cents for comparison)
                            amount_total = status_data.get("amount_total", 0)
                            expected_cents = int(expected_amount * 100)
                            
                            if amount_total == expected_cents:
                                self.log_result(f"Payment System ({package_type})", True, 
                                              f"Demo payment working - €{expected_amount}")
                            else:
                                self.log_result(f"Payment System ({package_type})", False, 
                                              f"Amount mismatch: expected {expected_cents}, got {amount_total}")
                                all_passed = False
                        else:
                            self.log_result(f"Payment System ({package_type})", False, 
                                          f"Payment not completed: {status_data.get('payment_status')}")
                            all_passed = False
                    else:
                        self.log_result(f"Payment System ({package_type})", False, 
                                      "Failed to check payment status")
                        all_passed = False
                else:
                    self.log_result(f"Payment System ({package_type})", False, 
                                  "Missing URL or session_id", data)
                    all_passed = False
            else:
                error = response.text if response else "Connection failed"
                self.log_result(f"Payment System ({package_type})", False, 
                              "Failed to create checkout session", error)
                all_passed = False
        
        return all_passed
    
    def test_integration_flow(self):
        """Test complete user flow: register → login → vedic calculation → complete lesson → level up"""
        # Create a fresh user for integration test
        integration_user = {
            "email": f"integration{int(time.time())}@numerom.com",
            "password": "IntegrationPass123!",
            "full_name": "Integration Test User",
            "birth_date": "25.12.1985"
        }
        
        # Register fresh user
        reg_response = self.make_request("POST", "/auth/register", integration_user)
        if not (reg_response and reg_response.status_code == 200):
            self.log_result("Integration Flow", False, "Failed to register integration user")
            return False
        
        integration_token = reg_response.json()["access_token"]
        integration_user_id = reg_response.json()["user"]["id"]
        
        # Step 2: Perform Vedic calculation with fresh user token
        vedic_response = self.make_request("POST", "/numerology/vedic/comprehensive", 
                                         {"name": "Integration Test"})
        # Temporarily use integration token
        temp_token = self.auth_token
        self.auth_token = integration_token
        
        vedic_response = self.make_request("POST", "/numerology/vedic/comprehensive", 
                                         {"name": "Integration Test"})
        
        # Restore original token
        self.auth_token = temp_token
        
        if not (vedic_response and vedic_response.status_code == 200):
            self.log_result("Integration Flow", False, "Vedic calculation failed")
            return False
        
        # Step 3: Get user profile to check credits (using integration token)
        self.auth_token = integration_token
        profile_response = self.make_request("GET", "/user/profile")
        self.auth_token = temp_token
        
        if not (profile_response and profile_response.status_code == 200):
            self.log_result("Integration Flow", False, "Failed to get user profile")
            return False
        
        profile_data = profile_response.json()
        credits_after_calc = profile_data.get("credits_remaining", 0)
        
        # Step 4: Create and complete a lesson (if admin token available)
        if self.admin_token:
            lesson_data = {
                "title": "Integration Test Lesson",
                "description": "Test lesson for integration flow",
                "video_url": "https://example.com/integration-test.mp4",
                "duration_minutes": 10,
                "level": 1,
                "order": 1,
                "is_active": True
            }
            
            create_response = self.make_request("POST", "/admin/lessons", 
                                              lesson_data, use_admin_token=True)
            
            if create_response and create_response.status_code == 200:
                lesson_id = create_response.json().get("lesson_id")
                
                # Complete the lesson with integration user
                self.auth_token = integration_token
                complete_response = self.make_request("POST", 
                                                    f"/learning/complete-lesson/{lesson_id}?watch_time=10&quiz_score=90")
                self.auth_token = temp_token
                
                if complete_response and complete_response.status_code == 200:
                    complete_data = complete_response.json()
                    
                    if complete_data.get("lesson_completed") and complete_data.get("experience_gained"):
                        self.log_result("Integration Flow", True, 
                                      "Complete integration flow working: register → vedic calc → lesson completion")
                        return True
                    else:
                        self.log_result("Integration Flow", False, 
                                      "Lesson completion data invalid")
                else:
                    self.log_result("Integration Flow", False, 
                                  "Failed to complete lesson")
            else:
                self.log_result("Integration Flow", False, 
                              "Failed to create test lesson")
        else:
            # Without admin, just verify the calculation worked
            self.log_result("Integration Flow", True, 
                          "Partial integration flow working: register → vedic calculation")
            return True
        
        return False
    
    def run_enhanced_tests(self):
        """Run all enhanced feature tests"""
        print("🚀 Starting Enhanced NUMEROM Backend API Tests")
        print("=" * 60)
        
        # Setup test users
        if not self.setup_test_users():
            print("❌ Failed to setup test users. Aborting tests.")
            return 0, 1
        
        # Enhanced feature tests
        self.test_enhanced_vedic_numerology()
        self.test_randomized_quiz_system()
        self.test_planetary_energy_charts()
        self.test_learning_management_system()
        self.test_admin_panel_functionality()
        self.test_updated_payment_system()
        self.test_integration_flow()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 ENHANCED FEATURES TEST SUMMARY")
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
            print("\n🎉 All enhanced features working perfectly!")
        
        return passed, total

def main():
    """Main test execution"""
    tester = EnhancedNumeromAPITester()
    passed, total = tester.run_enhanced_tests()
    
    # Exit with appropriate code
    if passed == total:
        print("\n🎉 All enhanced feature tests passed!")
        exit(0)
    else:
        print(f"\n⚠️  {total - passed} enhanced feature tests failed")
        exit(1)

if __name__ == "__main__":
    main()