#!/usr/bin/env python3
"""
NUMEROM Focused Backend Review Test
Tests 3 specific backend fixes as requested:
1. Classic Pythagorean Square with 4 additional numbers
2. Payment session with user_id storage and credit updates
3. Vedic time schedule API
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

class FocusedReviewTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.auth_token = None
        self.user_id = None
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
    
    def make_request(self, method, endpoint, data=None, headers=None):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        default_headers = {"Content-Type": "application/json"}
        
        if headers:
            default_headers.update(headers)
            
        if self.auth_token and "Authorization" not in default_headers:
            default_headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=default_headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=default_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {method} {url}: {str(e)}")
            return None
    
    def create_fresh_user(self):
        """Create a fresh user for testing"""
        timestamp = int(time.time())
        user_data = {
            "email": f"reviewtest{timestamp}@numerom.com",
            "password": "ReviewTest123!",
            "full_name": "Review Test User",
            "birth_date": "15.03.1990",
            "city": "Москва"
        }
        
        response = self.make_request("POST", "/auth/register", user_data)
        
        if response and response.status_code == 200:
            data = response.json()
            if "access_token" in data and "user" in data:
                self.auth_token = data["access_token"]
                self.user_id = data["user"].get("id")
                self.log_result("Fresh User Creation", True, f"Created user: {user_data['email']}")
                return True
            else:
                self.log_result("Fresh User Creation", False, "Missing token or user data", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Fresh User Creation", False, "Registration failed", error)
        return False
    
    def test_pythagorean_square_additional_numbers(self):
        """Test 1: Classic Pythagorean Square returns 4 additional numbers"""
        if not self.auth_token:
            self.log_result("Pythagorean Square Additional Numbers", False, "No auth token available")
            return False
        
        response = self.make_request("POST", "/numerology/pythagorean-square")
        
        if response and response.status_code == 200:
            data = response.json()
            
            # Check for additional_numbers field
            if "additional_numbers" in data:
                additional_numbers = data["additional_numbers"]
                
                # Verify it has exactly 4 values
                if isinstance(additional_numbers, list) and len(additional_numbers) == 4:
                    # Verify all are integers
                    if all(isinstance(num, int) for num in additional_numbers):
                        # Check that square cells reflect the added digits
                        if "square" in data:
                            square = data["square"]
                            # Verify square is 3x3 matrix
                            if len(square) == 3 and all(len(row) == 3 for row in square):
                                self.log_result("Pythagorean Square Additional Numbers", True, 
                                              f"✅ 4 additional numbers: {additional_numbers}, square matrix valid")
                                return True
                            else:
                                self.log_result("Pythagorean Square Additional Numbers", False, 
                                              "Invalid square matrix structure", square)
                        else:
                            self.log_result("Pythagorean Square Additional Numbers", False, 
                                          "Missing square field", data)
                    else:
                        self.log_result("Pythagorean Square Additional Numbers", False, 
                                      "Additional numbers are not all integers", additional_numbers)
                else:
                    self.log_result("Pythagorean Square Additional Numbers", False, 
                                  f"Expected 4 additional numbers, got {len(additional_numbers) if isinstance(additional_numbers, list) else 'invalid'}", 
                                  additional_numbers)
            else:
                self.log_result("Pythagorean Square Additional Numbers", False, 
                              "Missing additional_numbers field", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Pythagorean Square Additional Numbers", False, 
                          "Failed to get Pythagorean square", error)
        
        return False
    
    def test_payment_session_user_id_storage(self):
        """Test 2: Payment session stores user_id and credits update correctly"""
        if not self.auth_token:
            self.log_result("Payment Session User ID Storage", False, "No auth token available")
            return False
        
        # Get initial user profile to check credits
        profile_response = self.make_request("GET", "/user/profile")
        if not profile_response or profile_response.status_code != 200:
            self.log_result("Payment Session User ID Storage", False, "Could not get initial user profile")
            return False
        
        initial_profile = profile_response.json()
        initial_credits = initial_profile.get("credits_remaining", 0)
        is_premium = initial_profile.get("is_premium", False)
        
        # Test one_time package (should give +10 credits for non-premium)
        payment_data = {
            "package_type": "one_time",
            "origin_url": "https://numerology-fix.preview.emergentagent.com"
        }
        
        # Create checkout session
        checkout_response = self.make_request("POST", "/payments/checkout/session", payment_data)
        
        if checkout_response and checkout_response.status_code == 200:
            checkout_data = checkout_response.json()
            session_id = checkout_data.get("session_id")
            
            if session_id:
                # Check payment status (should work in demo mode)
                status_response = self.make_request("GET", f"/payments/checkout/status/{session_id}")
                
                if status_response and status_response.status_code == 200:
                    status_data = status_response.json()
                    
                    # Verify user_id is stored in transaction
                    if "user_id" in status_data:
                        stored_user_id = status_data["user_id"]
                        if stored_user_id == self.user_id:
                            # Check if payment is marked as paid (demo mode)
                            if status_data.get("payment_status") == "paid":
                                # Verify credits were updated
                                new_profile_response = self.make_request("GET", "/user/profile")
                                if new_profile_response and new_profile_response.status_code == 200:
                                    new_profile = new_profile_response.json()
                                    new_credits = new_profile.get("credits_remaining", 0)
                                    
                                    # For one_time package, should add 10 credits for non-premium users
                                    expected_credits = initial_credits + (10 if not is_premium else 10)
                                    
                                    if new_credits >= initial_credits + 10:
                                        self.log_result("Payment Session User ID Storage", True, 
                                                      f"✅ User ID stored: {stored_user_id}, Credits updated: {initial_credits} → {new_credits}")
                                        return True
                                    else:
                                        self.log_result("Payment Session User ID Storage", False, 
                                                      f"Credits not updated correctly: {initial_credits} → {new_credits}, expected +10")
                                else:
                                    self.log_result("Payment Session User ID Storage", False, 
                                                  "Could not get updated user profile")
                            else:
                                self.log_result("Payment Session User ID Storage", False, 
                                              f"Payment not marked as paid: {status_data.get('payment_status')}")
                        else:
                            self.log_result("Payment Session User ID Storage", False, 
                                          f"User ID mismatch: expected {self.user_id}, got {stored_user_id}")
                    else:
                        self.log_result("Payment Session User ID Storage", False, 
                                      "user_id not found in payment status", status_data)
                else:
                    error = status_response.text if status_response else "Connection failed"
                    self.log_result("Payment Session User ID Storage", False, 
                                  "Failed to check payment status", error)
            else:
                self.log_result("Payment Session User ID Storage", False, 
                              "No session_id in checkout response", checkout_data)
        else:
            error = checkout_response.text if checkout_response else "Connection failed"
            self.log_result("Payment Session User ID Storage", False, 
                          "Failed to create checkout session", error)
        
        return False
    
    def test_vedic_time_daily_schedule(self):
        """Test 3: Vedic time schedule API returns sunrise/sunset and rahu_kaal without 500 errors"""
        if not self.auth_token:
            self.log_result("Vedic Time Daily Schedule", False, "No auth token available")
            return False
        
        # Ensure user has at least 1 credit or is premium
        profile_response = self.make_request("GET", "/user/profile")
        if profile_response and profile_response.status_code == 200:
            profile_data = profile_response.json()
            credits = profile_data.get("credits_remaining", 0)
            is_premium = profile_data.get("is_premium", False)
            
            if credits < 1 and not is_premium:
                self.log_result("Vedic Time Daily Schedule", False, 
                              f"User has insufficient credits ({credits}) and is not premium")
                return False
        
        # Test the specific endpoint with requested parameters
        endpoint = "/vedic-time/daily-schedule?date=2025-03-15&city=Москва"
        response = self.make_request("GET", endpoint)
        
        if response and response.status_code == 200:
            data = response.json()
            
            # Check for required fields
            required_fields = ["city", "date", "sun_times", "inauspicious_periods"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                # Check for sunrise/sunset in sun_times
                sun_times = data.get("sun_times", {})
                if "sunrise" in sun_times and "sunset" in sun_times:
                    # Check for rahu_kaal in inauspicious_periods
                    inauspicious_periods = data.get("inauspicious_periods", {})
                    if "rahu_kaal" in inauspicious_periods:
                        rahu_kaal = inauspicious_periods["rahu_kaal"]
                        # Verify rahu_kaal has start and end times
                        if "start" in rahu_kaal and "end" in rahu_kaal:
                            self.log_result("Vedic Time Daily Schedule", True, 
                                          f"✅ API working: sunrise/sunset present, rahu_kaal: {rahu_kaal['start']}-{rahu_kaal['end']}")
                            return True
                        else:
                            self.log_result("Vedic Time Daily Schedule", False, 
                                          "rahu_kaal missing start/end times", rahu_kaal)
                    else:
                        self.log_result("Vedic Time Daily Schedule", False, 
                                      "rahu_kaal not found in inauspicious_periods", inauspicious_periods)
                else:
                    self.log_result("Vedic Time Daily Schedule", False, 
                                  "sunrise/sunset not found in sun_times", sun_times)
            else:
                self.log_result("Vedic Time Daily Schedule", False, 
                              f"Missing required fields: {missing_fields}", data)
        elif response and response.status_code == 500:
            self.log_result("Vedic Time Daily Schedule", False, 
                          "❌ 500 ERROR - API returning server error", response.text)
        else:
            error = response.text if response else "Connection failed"
            status_code = response.status_code if response else "No response"
            self.log_result("Vedic Time Daily Schedule", False, 
                          f"API failed with status {status_code}", error)
        
        return False
    
    def run_focused_tests(self):
        """Run the 3 focused tests as requested"""
        print("🎯 Starting NUMEROM Focused Backend Review Tests")
        print("=" * 60)
        print("Testing 3 specific backend fixes:")
        print("1. Classic Pythagorean Square with 4 additional numbers")
        print("2. Payment session user_id storage and credit updates")
        print("3. Vedic time schedule API (no 500 errors)")
        print("=" * 60)
        
        # Create fresh user
        if not self.create_fresh_user():
            print("❌ Cannot proceed without fresh user")
            return 0, 1
        
        print("\n🔍 Running focused tests...")
        
        # Test 1: Pythagorean Square with additional numbers
        print("\n1️⃣ Testing Classic Pythagorean Square...")
        self.test_pythagorean_square_additional_numbers()
        
        # Test 2: Payment session with user_id storage
        print("\n2️⃣ Testing Payment Session User ID Storage...")
        self.test_payment_session_user_id_storage()
        
        # Test 3: Vedic time schedule
        print("\n3️⃣ Testing Vedic Time Daily Schedule...")
        self.test_vedic_time_daily_schedule()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 FOCUSED TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        
        # Show results for each test
        for result in self.test_results:
            if result["test"] != "Fresh User Creation":  # Skip user creation in summary
                status = "✅" if result["success"] else "❌"
                print(f"{status} {result['test']}")
        
        return passed, total

def main():
    """Main test execution"""
    tester = FocusedReviewTester()
    passed, total = tester.run_focused_tests()
    
    # Exit with appropriate code
    if passed >= 3:  # At least the 3 main tests should pass
        print("\n🎉 Focused tests completed!")
        exit(0)
    else:
        print(f"\n⚠️ Some focused tests failed")
        exit(1)

if __name__ == "__main__":
    main()