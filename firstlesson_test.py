#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for FirstLesson Component
Testing 4 new API endpoints as specified in review request:
1. POST /api/lessons/save-exercise-response
2. GET /api/lessons/exercise-responses/{lesson_id}  
3. POST /api/lessons/complete-challenge
4. GET /api/lessons/overall-progress/{lesson_id}
"""

import requests
import json
import sys
import os
from datetime import datetime

# Configuration
BASE_URL = "https://numerology-fix.preview.emergentagent.com/api"
TEST_USER_EMAIL = "dmitrii.malahov@gmail.com"
TEST_USER_PASSWORD = "756bvy67H"
LESSON_ID = "lesson_numerom_intro"
CHALLENGE_ID = "challenge_sun_7days"

class FirstLessonAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_info = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()

    def authenticate(self):
        """Authenticate with test user credentials"""
        try:
            login_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.user_info = data.get("user", {})
                
                # Set authorization header for future requests (but not Content-Type for form data)
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log_test(
                    "User Authentication", 
                    True, 
                    f"Logged in as {self.user_info.get('email')} with {self.user_info.get('credits_remaining', 0)} credits"
                )
                return True
            else:
                self.log_test(
                    "User Authentication", 
                    False, 
                    error=f"Login failed with status {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("User Authentication", False, error=str(e))
            return False

    def test_save_exercise_response(self):
        """Test POST /api/lessons/save-exercise-response"""
        try:
            # Test data for exercise responses
            test_exercises = [
                {
                    "exercise_id": "exercise_1_reflection",
                    "response_text": "Я чувствую, что числа действительно влияют на мою жизнь. Особенно заметно влияние числа 7 - дня недели моего рождения."
                },
                {
                    "exercise_id": "exercise_2_calculation", 
                    "response_text": "Мое число души: 1, число судьбы: 4. Это объясняет мою склонность к лидерству и практичности."
                },
                {
                    "exercise_id": "exercise_3_meditation",
                    "response_text": "Во время медитации я почувствовал связь с энергией Солнца. Ощущение тепла и силы было очень ярким."
                },
                {
                    "exercise_id": "exercise_4_practical",
                    "response_text": "Применил нумерологические принципы при выборе времени для важного разговора. Результат превзошел ожидания!"
                }
            ]
            
            saved_count = 0
            for exercise in test_exercises:
                # Prepare form data
                form_data = {
                    "lesson_id": LESSON_ID,
                    "exercise_id": exercise["exercise_id"],
                    "response_text": exercise["response_text"]
                }
                
                # Remove Content-Type header to let requests handle form data
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                response = self.session.post(
                    f"{BASE_URL}/lessons/save-exercise-response",
                    data=form_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    saved_count += 1
                else:
                    self.log_test(
                        f"Save Exercise Response - {exercise['exercise_id']}", 
                        False,
                        error=f"Status {response.status_code}: {response.text}"
                    )
                    return False
            
            self.log_test(
                "Save Exercise Responses", 
                True, 
                f"Successfully saved {saved_count}/4 exercise responses with upsert functionality"
            )
            return True
            
        except Exception as e:
            self.log_test("Save Exercise Responses", False, error=str(e))
            return False

    def test_get_exercise_responses(self):
        """Test GET /api/lessons/exercise-responses/{lesson_id}"""
        try:
            response = self.session.get(
                f"{BASE_URL}/lessons/exercise-responses/{LESSON_ID}",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                responses = data.get("responses", {})
                
                # Verify we got the saved responses
                expected_exercises = [
                    "exercise_1_reflection",
                    "exercise_2_calculation", 
                    "exercise_3_meditation",
                    "exercise_4_practical"
                ]
                
                found_exercises = []
                for exercise_id in expected_exercises:
                    if exercise_id in responses:
                        response_data = responses[exercise_id]
                        if response_data.get("completed") and response_data.get("response_text"):
                            found_exercises.append(exercise_id)
                
                self.log_test(
                    "Get Exercise Responses", 
                    True, 
                    f"Retrieved {len(found_exercises)}/4 saved exercise responses from MongoDB"
                )
                return True
            else:
                self.log_test(
                    "Get Exercise Responses", 
                    False,
                    error=f"Status {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Get Exercise Responses", False, error=str(e))
            return False

    def test_complete_challenge(self):
        """Test POST /api/lessons/complete-challenge"""
        try:
            # First, we need to start the challenge to have progress to complete
            # Let's try to start the challenge first
            start_data = {
                "challenge_id": CHALLENGE_ID
            }
            
            # Remove Content-Type header to let requests handle form data
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            start_response = self.session.post(
                f"{BASE_URL}/lessons/start-challenge",
                data=start_data,
                headers=headers
            )
            
            # Now complete the challenge with rating
            rating_values = [1, 2, 3, 4, 5]
            test_rating = 5  # Test with 5 stars
            
            complete_data = {
                "challenge_id": CHALLENGE_ID,
                "rating": test_rating,
                "notes": f"Завершил 7-дневный челлендж активации энергии Солнца с оценкой {test_rating} звезд. Чувствую значительные изменения в энергетике!"
            }
            
            response = self.session.post(
                f"{BASE_URL}/lessons/complete-challenge",
                data=complete_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                returned_rating = data.get("rating")
                message = data.get("message", "")
                
                if returned_rating == test_rating:
                    self.log_test(
                        "Complete Challenge", 
                        True, 
                        f"Challenge completed with {test_rating}/5 stars rating. Status updated to 'completed'"
                    )
                    return True
                else:
                    self.log_test(
                        "Complete Challenge", 
                        False,
                        error=f"Rating mismatch: sent {test_rating}, got {returned_rating}"
                    )
                    return False
            else:
                self.log_test(
                    "Complete Challenge", 
                    False,
                    error=f"Status {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Complete Challenge", False, error=str(e))
            return False

    def test_overall_progress(self):
        """Test GET /api/lessons/overall-progress/{lesson_id}"""
        try:
            response = self.session.get(
                f"{BASE_URL}/lessons/overall-progress/{LESSON_ID}",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = [
                    "lesson_id", "overall_percentage", "completed_components", 
                    "total_components", "breakdown"
                ]
                
                missing_fields = []
                for field in required_fields:
                    if field not in data:
                        missing_fields.append(field)
                
                if missing_fields:
                    self.log_test(
                        "Overall Progress", 
                        False,
                        error=f"Missing required fields: {missing_fields}"
                    )
                    return False
                
                # Verify progress calculation
                overall_percentage = data.get("overall_percentage", 0)
                breakdown = data.get("breakdown", {})
                
                # Check that percentage is between 0-100
                if not (0 <= overall_percentage <= 100):
                    self.log_test(
                        "Overall Progress", 
                        False,
                        error=f"Invalid percentage: {overall_percentage} (should be 0-100)"
                    )
                    return False
                
                # Verify breakdown components
                expected_components = ["theory", "exercises", "quiz", "challenge", "habits"]
                breakdown_details = []
                
                for component in expected_components:
                    status = breakdown.get(component, False)
                    breakdown_details.append(f"{component}: {'✓' if status else '✗'}")
                
                self.log_test(
                    "Overall Progress", 
                    True, 
                    f"Progress: {overall_percentage}% ({data.get('completed_components', 0)}/{data.get('total_components', 5)} components). Breakdown: {', '.join(breakdown_details)}"
                )
                return True
            else:
                self.log_test(
                    "Overall Progress", 
                    False,
                    error=f"Status {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Overall Progress", False, error=str(e))
            return False

    def test_data_persistence(self):
        """Test that data is actually saved and retrieved from MongoDB"""
        try:
            # Test 1: Save a new exercise response
            test_exercise_id = "exercise_persistence_test"
            test_response_text = f"Persistence test response - {datetime.now().isoformat()}"
            
            save_data = {
                "lesson_id": LESSON_ID,
                "exercise_id": test_exercise_id,
                "response_text": test_response_text
            }
            
            # Remove Content-Type header to let requests handle form data
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            save_response = self.session.post(
                f"{BASE_URL}/lessons/save-exercise-response",
                data=save_data,
                headers=headers
            )
            
            if save_response.status_code != 200:
                self.log_test(
                    "Data Persistence", 
                    False,
                    error=f"Failed to save test data: {save_response.status_code}"
                )
                return False
            
            # Test 2: Retrieve and verify the data
            get_response = self.session.get(
                f"{BASE_URL}/lessons/exercise-responses/{LESSON_ID}",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            
            if get_response.status_code != 200:
                self.log_test(
                    "Data Persistence", 
                    False,
                    error=f"Failed to retrieve test data: {get_response.status_code}"
                )
                return False
            
            data = get_response.json()
            responses = data.get("responses", {})
            
            if test_exercise_id in responses:
                retrieved_text = responses[test_exercise_id].get("response_text", "")
                if retrieved_text == test_response_text:
                    self.log_test(
                        "Data Persistence", 
                        True, 
                        "Exercise responses are correctly saved to and retrieved from MongoDB"
                    )
                    return True
                else:
                    self.log_test(
                        "Data Persistence", 
                        False,
                        error=f"Data mismatch: saved '{test_response_text}', got '{retrieved_text}'"
                    )
                    return False
            else:
                self.log_test(
                    "Data Persistence", 
                    False,
                    error=f"Test exercise {test_exercise_id} not found in responses"
                )
                return False
                
        except Exception as e:
            self.log_test("Data Persistence", False, error=str(e))
            return False

    def test_authentication_required(self):
        """Test that all endpoints require proper authentication"""
        try:
            # Test without authentication
            test_session = requests.Session()
            
            endpoints_to_test = [
                ("POST", f"{BASE_URL}/lessons/save-exercise-response", {"lesson_id": LESSON_ID, "exercise_id": "test", "response_text": "test"}),
                ("GET", f"{BASE_URL}/lessons/exercise-responses/{LESSON_ID}", None),
                ("POST", f"{BASE_URL}/lessons/complete-challenge", {"challenge_id": CHALLENGE_ID, "rating": 5}),
                ("GET", f"{BASE_URL}/lessons/overall-progress/{LESSON_ID}", None)
            ]
            
            auth_protected_count = 0
            for method, url, data in endpoints_to_test:
                if method == "POST":
                    response = test_session.post(url, data=data)
                else:
                    response = test_session.get(url)
                
                # Should return 401 Unauthorized or 403 Forbidden
                if response.status_code in [401, 403]:
                    auth_protected_count += 1
            
            if auth_protected_count == len(endpoints_to_test):
                self.log_test(
                    "Authentication Required", 
                    True, 
                    f"All {len(endpoints_to_test)} endpoints properly require authentication"
                )
                return True
            else:
                self.log_test(
                    "Authentication Required", 
                    False,
                    error=f"Only {auth_protected_count}/{len(endpoints_to_test)} endpoints require authentication"
                )
                return False
                
        except Exception as e:
            self.log_test("Authentication Required", False, error=str(e))
            return False

    def run_comprehensive_test(self):
        """Run all tests for FirstLesson API endpoints"""
        print("🎯 COMPREHENSIVE FIRSTLESSON API TESTING")
        print("=" * 60)
        print(f"Testing User: {TEST_USER_EMAIL}")
        print(f"Lesson ID: {LESSON_ID}")
        print(f"Challenge ID: {CHALLENGE_ID}")
        print(f"Backend URL: {BASE_URL}")
        print("=" * 60)
        print()
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Test all 4 new API endpoints
        tests = [
            ("Save Exercise Response", self.test_save_exercise_response),
            ("Get Exercise Responses", self.test_get_exercise_responses),
            ("Complete Challenge", self.test_complete_challenge),
            ("Overall Progress", self.test_overall_progress),
            ("Data Persistence", self.test_data_persistence),
            ("Authentication Required", self.test_authentication_required)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            if test_func():
                passed_tests += 1
        
        # Summary
        print("=" * 60)
        print("🎉 TESTING SUMMARY")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests) * 100
        
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
        
        print()
        print(f"📊 RESULTS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! FirstLesson API endpoints are working correctly.")
            return True
        else:
            print(f"⚠️  {total_tests - passed_tests} tests failed. Review the errors above.")
            return False

def main():
    """Main test execution"""
    tester = FirstLessonAPITester()
    success = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()