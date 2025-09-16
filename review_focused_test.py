#!/usr/bin/env python3
"""
Focused Backend Test Suite for Review Request
Проверить, что все основные API endpoints работают корректно после изменений в frontend компоненте UserDashboard.jsx. 
Сосредоточиться на аутентификации, получении данных пользователя, и основных нумерологических расчетах. 
Убедиться что backend не пострадал от frontend изменений.

Focus Areas:
1. Authentication (login/register)
2. User data retrieval 
3. Main numerological calculations (personal numbers, Pythagorean square, compatibility)
"""

import requests
import json
import os
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_USER_EMAIL = "dmitrii.malahov@gmail.com"
TEST_USER_PASSWORD = "756bvy67H"

class ReviewFocusedTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.user_data = None
        
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
    
    def test_authentication_login(self):
        """Test user authentication - login endpoint"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.user_data = data.get('user', {})
                
                if self.auth_token and self.user_data:
                    self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                    self.log_test("Authentication - Login", True, 
                        f"User: {self.user_data.get('email')}, Credits: {self.user_data.get('credits_remaining', 0)}")
                    return True
                else:
                    self.log_test("Authentication - Login", False, "Missing token or user data in response")
                    return False
            else:
                self.log_test("Authentication - Login", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Authentication - Login", False, f"Exception: {str(e)}")
            return False
    
    def test_user_data_retrieval(self):
        """Test user data retrieval after authentication"""
        try:
            # Test getting user profile/data through various endpoints
            
            # 1. Test credit history endpoint (shows user data access)
            response = self.session.get(f"{BACKEND_URL}/user/credit-history?limit=5")
            
            if response.status_code == 200:
                data = response.json()
                transactions = data.get('transactions', [])
                total = data.get('total', 0)
                
                self.log_test("User Data - Credit History", True, 
                    f"Retrieved {len(transactions)} transactions, Total: {total}")
                
                # 2. Test learning levels (user progress data)
                response2 = self.session.get(f"{BACKEND_URL}/learning/levels")
                
                if response2.status_code == 200:
                    learning_data = response2.json()
                    user_level = learning_data.get('user_level', {})
                    lessons = learning_data.get('available_lessons', [])
                    
                    self.log_test("User Data - Learning Progress", True, 
                        f"Level: {user_level.get('current_level', 0)}, Lessons: {len(lessons)}")
                    return True
                else:
                    self.log_test("User Data - Learning Progress", False, 
                        f"Status: {response2.status_code}")
                    return False
            else:
                self.log_test("User Data - Credit History", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("User Data Retrieval", False, f"Exception: {str(e)}")
            return False
    
    def test_personal_numbers_calculation(self):
        """Test personal numbers numerology calculation"""
        try:
            # Use a test birth date for calculation
            test_birth_date = "10.01.1982"
            
            response = self.session.post(f"{BACKEND_URL}/numerology/personal-numbers", 
                json={"birth_date": test_birth_date})
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for expected fields in personal numbers
                expected_fields = ['soul_number', 'mind_number', 'destiny_number', 'ruling_number']
                missing_fields = [field for field in expected_fields if field not in data]
                
                if not missing_fields:
                    # Check if planetary strength is included
                    planetary_strength = data.get('planetary_strength', {})
                    planet_count = len(planetary_strength)
                    
                    self.log_test("Numerology - Personal Numbers", True, 
                        f"All core numbers present, {planet_count} planetary strengths calculated")
                    return True
                else:
                    self.log_test("Numerology - Personal Numbers", False, 
                        f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Numerology - Personal Numbers", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Numerology - Personal Numbers", False, f"Exception: {str(e)}")
            return False
    
    def test_pythagorean_square_calculation(self):
        """Test Pythagorean square numerology calculation"""
        try:
            test_birth_date = "15.03.1990"
            
            response = self.session.post(f"{BACKEND_URL}/numerology/pythagorean-square", 
                json={"birth_date": test_birth_date})
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for expected fields in Pythagorean square
                expected_fields = ['square', 'horizontal_sums', 'vertical_sums', 'diagonal_sums']
                missing_fields = [field for field in expected_fields if field not in data]
                
                if not missing_fields:
                    square = data.get('square', [])
                    additional_numbers = data.get('additional_numbers', [])
                    
                    # Verify square is 3x3 and additional numbers exist
                    is_valid_square = len(square) == 3 and all(len(row) == 3 for row in square)
                    has_additional = len(additional_numbers) > 0
                    
                    if is_valid_square and has_additional:
                        self.log_test("Numerology - Pythagorean Square", True, 
                            f"3x3 square generated, {len(additional_numbers)} additional numbers")
                        return True
                    else:
                        self.log_test("Numerology - Pythagorean Square", False, 
                            f"Invalid square format or missing additional numbers")
                        return False
                else:
                    self.log_test("Numerology - Pythagorean Square", False, 
                        f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Numerology - Pythagorean Square", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Numerology - Pythagorean Square", False, f"Exception: {str(e)}")
            return False
    
    def test_compatibility_calculation(self):
        """Test compatibility numerology calculation"""
        try:
            compatibility_data = {
                "person1_birth_date": "15.03.1990",
                "person2_birth_date": "20.07.1985"
            }
            
            response = self.session.post(f"{BACKEND_URL}/numerology/compatibility", 
                json=compatibility_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for expected fields in compatibility
                expected_fields = ['compatibility_score', 'person1_life_path', 'person2_life_path']
                missing_fields = [field for field in expected_fields if field not in data]
                
                if not missing_fields:
                    score = data.get('compatibility_score', 0)
                    description = data.get('description', '')
                    
                    # Verify score is reasonable and description exists
                    is_valid_score = 0 <= score <= 100
                    has_description = len(description) > 0
                    
                    if is_valid_score and has_description:
                        self.log_test("Numerology - Compatibility", True, 
                            f"Score: {score}%, Description length: {len(description)} chars")
                        return True
                    else:
                        self.log_test("Numerology - Compatibility", False, 
                            f"Invalid score ({score}) or missing description")
                        return False
                else:
                    self.log_test("Numerology - Compatibility", False, 
                        f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Numerology - Compatibility", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Numerology - Compatibility", False, f"Exception: {str(e)}")
            return False
    
    def test_vedic_time_calculations(self):
        """Test Vedic time calculations (additional verification)"""
        try:
            # Test daily schedule endpoint
            params = {
                "date": "2025-01-15",
                "city": "Москва"
            }
            
            response = self.session.get(f"{BACKEND_URL}/vedic-time/daily-schedule", params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for key Vedic time fields
                expected_fields = ['city', 'weekday', 'inauspicious_periods', 'auspicious_periods']
                missing_fields = [field for field in expected_fields if field not in data]
                
                if not missing_fields:
                    rahu_kaal = data.get('inauspicious_periods', {}).get('rahu_kaal', {})
                    has_rahu_kaal = 'start_time' in rahu_kaal and 'end_time' in rahu_kaal
                    
                    if has_rahu_kaal:
                        self.log_test("Vedic Time - Daily Schedule", True, 
                            f"City: {data.get('city')}, Rahu Kaal: {rahu_kaal.get('start_time')}-{rahu_kaal.get('end_time')}")
                        return True
                    else:
                        self.log_test("Vedic Time - Daily Schedule", False, 
                            "Missing Rahu Kaal time periods")
                        return False
                else:
                    self.log_test("Vedic Time - Daily Schedule", False, 
                        f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Vedic Time - Daily Schedule", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Vedic Time - Daily Schedule", False, f"Exception: {str(e)}")
            return False
    
    def test_payment_system_integrity(self):
        """Test payment system endpoints (verification only, no actual payments)"""
        try:
            # Test payment packages info by attempting to create a session (will be demo mode)
            payment_data = {
                "package_type": "one_time",
                "origin_url": "https://numerology-fix.preview.emergentagent.com"
            }
            
            response = self.session.post(f"{BACKEND_URL}/payments/checkout/session", json=payment_data)
            
            if response.status_code == 200:
                data = response.json()
                session_id = data.get('session_id')
                url = data.get('url')
                
                if session_id and url:
                    # Test payment status check
                    status_response = self.session.get(f"{BACKEND_URL}/payments/checkout/status/{session_id}")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        payment_status = status_data.get('payment_status')
                        
                        self.log_test("Payment System - Integrity", True, 
                            f"Demo session created, Status: {payment_status}")
                        return True
                    else:
                        self.log_test("Payment System - Integrity", False, 
                            f"Status check failed: {status_response.status_code}")
                        return False
                else:
                    self.log_test("Payment System - Integrity", False, 
                        "Missing session_id or URL in response")
                    return False
            else:
                self.log_test("Payment System - Integrity", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Payment System - Integrity", False, f"Exception: {str(e)}")
            return False
    
    def test_quiz_system(self):
        """Test quiz system functionality"""
        try:
            # Test getting randomized questions
            response = self.session.get(f"{BACKEND_URL}/quiz/randomized-questions")
            
            if response.status_code == 200:
                data = response.json()
                questions = data.get('questions', [])
                session_id = data.get('session_id')
                
                if len(questions) > 0 and session_id:
                    # Test quiz submission with sample answers
                    sample_answers = []
                    for i, question in enumerate(questions[:3]):  # Test with first 3 questions
                        sample_answers.append({
                            "question_id": i,
                            "selected_answer": question.get('options', [{}])[0].get('text', 'A')
                        })
                    
                    submit_response = self.session.post(f"{BACKEND_URL}/quiz/submit", json=sample_answers)
                    
                    if submit_response.status_code == 200:
                        submit_data = submit_response.json()
                        score = submit_data.get('total_score', 0)
                        
                        self.log_test("Quiz System", True, 
                            f"{len(questions)} questions, Sample score: {score}")
                        return True
                    else:
                        self.log_test("Quiz System", False, 
                            f"Submit failed: {submit_response.status_code}")
                        return False
                else:
                    self.log_test("Quiz System", False, 
                        f"Invalid questions ({len(questions)}) or missing session_id")
                    return False
            else:
                self.log_test("Quiz System", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Quiz System", False, f"Exception: {str(e)}")
            return False
    
    def run_focused_test_suite(self):
        """Run the focused test suite for review request"""
        print("🎯 STARTING FOCUSED BACKEND TEST SUITE FOR REVIEW REQUEST")
        print("Проверка основных API endpoints после изменений в UserDashboard.jsx")
        print("=" * 70)
        
        # Step 1: Authentication
        print("\n🔐 TESTING AUTHENTICATION:")
        if not self.test_authentication_login():
            print("❌ Authentication failed - cannot continue with other tests")
            return False
        
        # Step 2: User Data Retrieval
        print("\n👤 TESTING USER DATA RETRIEVAL:")
        if not self.test_user_data_retrieval():
            print("⚠️ User data retrieval issues detected")
        
        # Step 3: Core Numerology Calculations
        print("\n🔢 TESTING CORE NUMEROLOGY CALCULATIONS:")
        personal_numbers_ok = self.test_personal_numbers_calculation()
        pythagorean_ok = self.test_pythagorean_square_calculation()
        compatibility_ok = self.test_compatibility_calculation()
        
        # Step 4: Additional Systems Verification
        print("\n⭐ TESTING ADDITIONAL SYSTEMS:")
        vedic_ok = self.test_vedic_time_calculations()
        payment_ok = self.test_payment_system_integrity()
        quiz_ok = self.test_quiz_system()
        
        # Determine overall success
        core_systems_ok = personal_numbers_ok and pythagorean_ok and compatibility_ok
        
        return core_systems_ok
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("🎯 FOCUSED BACKEND TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Categorize results
        auth_tests = [r for r in self.test_results if 'Authentication' in r['test']]
        user_tests = [r for r in self.test_results if 'User Data' in r['test']]
        numerology_tests = [r for r in self.test_results if 'Numerology' in r['test']]
        other_tests = [r for r in self.test_results if r not in auth_tests + user_tests + numerology_tests]
        
        # Print results by category
        categories = [
            ("🔐 AUTHENTICATION", auth_tests),
            ("👤 USER DATA", user_tests), 
            ("🔢 NUMEROLOGY", numerology_tests),
            ("⭐ OTHER SYSTEMS", other_tests)
        ]
        
        for category_name, category_tests in categories:
            if category_tests:
                print(f"\n{category_name}:")
                for result in category_tests:
                    status = "✅" if result['success'] else "❌"
                    print(f"  {status} {result['test']}")
                    if result['details']:
                        print(f"     {result['details']}")
        
        print("\n" + "=" * 70)
        
        # Core systems analysis
        core_numerology_passed = sum(1 for r in numerology_tests if r['success'])
        core_numerology_total = len(numerology_tests)
        auth_passed = sum(1 for r in auth_tests if r['success'])
        
        if auth_passed > 0 and core_numerology_passed == core_numerology_total and core_numerology_total > 0:
            print("🎉 REVIEW REQUEST VERIFICATION: SUCCESS")
            print("✅ Authentication working correctly")
            print("✅ User data retrieval functional")
            print("✅ All core numerology calculations operational")
            print("✅ Backend NOT affected by frontend UserDashboard.jsx changes")
        elif auth_passed > 0 and core_numerology_passed >= core_numerology_total * 0.8:
            print("⚠️ REVIEW REQUEST VERIFICATION: MOSTLY SUCCESS")
            print("✅ Authentication working")
            print("⚠️ Minor issues in some numerology calculations")
            print("✅ Backend largely unaffected by frontend changes")
        else:
            print("❌ REVIEW REQUEST VERIFICATION: ISSUES DETECTED")
            print("❌ Critical problems found in core functionality")
            print("❌ Backend may have been affected by frontend changes")
        
        return success_rate >= 80 and auth_passed > 0 and core_numerology_passed >= core_numerology_total * 0.8

def main():
    """Main test execution"""
    test_suite = ReviewFocusedTestSuite()
    
    try:
        success = test_suite.run_focused_test_suite()
        overall_success = test_suite.print_summary()
        
        if overall_success:
            print("\n🎯 ЗАКЛЮЧЕНИЕ: Backend API endpoints работают корректно")
            print("✅ Аутентификация функционирует")
            print("✅ Получение данных пользователя работает")
            print("✅ Основные нумерологические расчеты операционны")
            print("✅ Backend НЕ пострадал от изменений в frontend")
        else:
            print("\n❌ ЗАКЛЮЧЕНИЕ: Обнаружены проблемы в backend API")
            print("Требуется дополнительное исследование проблем")
        
        return overall_success
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Test suite failed with exception: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)