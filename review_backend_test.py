#!/usr/bin/env python3
"""
NUMEROM Backend Review Test Suite
Tests specific scenarios from the review request after server.py restoration.
"""

import requests
import json
import os
from datetime import datetime
import time

# Get backend URL from environment
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

class ReviewTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.auth_token = None
        self.user_data = {
            "email": f"reviewuser{int(time.time())}@numerom.com",
            "password": "ReviewPass123!",
            "full_name": "Review Test User",
            "birth_date": "15.03.1990",
            "city": "Москва"
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
    
    def test_1_register_and_login(self):
        """Test 1: Register new user (email unique), login, check profile: credits=1, is_premium=false"""
        print("\n🔍 TEST 1: User Registration, Login, and Profile Check")
        
        # Register new user
        response = self.make_request("POST", "/auth/register", self.user_data)
        
        if not response or response.status_code != 200:
            error = response.text if response else "Connection failed"
            self.log_result("1. User Registration", False, "Registration failed", error)
            return False
        
        data = response.json()
        if "access_token" not in data or "user" not in data:
            self.log_result("1. User Registration", False, "Missing token or user data", data)
            return False
        
        self.auth_token = data["access_token"]
        self.log_result("1. User Registration", True, "User registered successfully")
        
        # Login with same credentials
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }
        
        response = self.make_request("POST", "/auth/login", login_data)
        
        if not response or response.status_code != 200:
            error = response.text if response else "Connection failed"
            self.log_result("1. User Login", False, "Login failed", error)
            return False
        
        data = response.json()
        if "access_token" not in data:
            self.log_result("1. User Login", False, "Missing access token", data)
            return False
        
        self.auth_token = data["access_token"]
        self.log_result("1. User Login", True, "Login successful")
        
        # Check profile: credits=1, is_premium=false
        response = self.make_request("GET", "/user/profile")
        
        if not response or response.status_code != 200:
            error = response.text if response else "Connection failed"
            self.log_result("1. Profile Check", False, "Failed to get profile", error)
            return False
        
        profile = response.json()
        credits = profile.get("credits_remaining")
        is_premium = profile.get("is_premium")
        
        if credits == 1 and is_premium == False:
            self.log_result("1. Profile Check", True, f"Profile correct: credits={credits}, is_premium={is_premium}")
            return True
        else:
            self.log_result("1. Profile Check", False, f"Profile incorrect: credits={credits}, is_premium={is_premium}", profile)
            return False
    
    def test_2_pythagorean_square(self):
        """Test 2: POST /api/numerology/pythagorean-square -> 200, response.additional_numbers has 4 ints; credits decrement to 0"""
        print("\n🔍 TEST 2: Pythagorean Square with Additional Numbers")
        
        if not self.auth_token:
            self.log_result("2. Pythagorean Square", False, "No auth token available")
            return False
        
        response = self.make_request("POST", "/numerology/pythagorean-square")
        
        if not response or response.status_code != 200:
            error = response.text if response else "Connection failed"
            self.log_result("2. Pythagorean Square", False, "API call failed", error)
            return False
        
        data = response.json()
        
        # Check for additional_numbers field with 4 integers
        additional_numbers = data.get("additional_numbers")
        if not additional_numbers:
            self.log_result("2. Pythagorean Square", False, "Missing additional_numbers field", data)
            return False
        
        if not isinstance(additional_numbers, list) or len(additional_numbers) != 4:
            self.log_result("2. Pythagorean Square", False, f"additional_numbers should be list of 4 ints, got: {additional_numbers}", data)
            return False
        
        # Check all are integers
        if not all(isinstance(num, int) for num in additional_numbers):
            self.log_result("2. Pythagorean Square", False, f"additional_numbers should contain integers, got: {additional_numbers}", data)
            return False
        
        self.log_result("2. Pythagorean Square", True, f"Response has additional_numbers with 4 ints: {additional_numbers}")
        
        # Check credits decremented to 0
        response = self.make_request("GET", "/user/profile")
        if response and response.status_code == 200:
            profile = response.json()
            credits = profile.get("credits_remaining")
            if credits == 0:
                self.log_result("2. Credits Decrement", True, f"Credits decremented to {credits}")
                return True
            else:
                self.log_result("2. Credits Decrement", False, f"Credits should be 0, got {credits}", profile)
                return False
        else:
            self.log_result("2. Credits Decrement", False, "Could not verify credit decrement")
            return False
    
    def test_3_payment_demo_flow(self):
        """Test 3: Payments demo: POST /api/payments/checkout/session (one_time) -> get session_id; GET /api/payments/checkout/status/{id} -> paid; profile credits increased by +10"""
        print("\n🔍 TEST 3: Payment Demo Flow")
        
        if not self.auth_token:
            self.log_result("3. Payment Demo", False, "No auth token available")
            return False
        
        # Create checkout session for one_time package
        payment_data = {
            "package_type": "one_time",
            "origin_url": "https://numerology-fix.preview.emergentagent.com"
        }
        
        response = self.make_request("POST", "/payments/checkout/session", payment_data)
        
        if not response or response.status_code != 200:
            error = response.text if response else "Connection failed"
            self.log_result("3. Checkout Session", False, "Failed to create checkout session", error)
            return False
        
        data = response.json()
        session_id = data.get("session_id")
        
        if not session_id:
            self.log_result("3. Checkout Session", False, "Missing session_id", data)
            return False
        
        self.log_result("3. Checkout Session", True, f"Checkout session created: {session_id}")
        
        # Check payment status
        response = self.make_request("GET", f"/payments/checkout/status/{session_id}")
        
        if not response or response.status_code != 200:
            error = response.text if response else "Connection failed"
            self.log_result("3. Payment Status", False, "Failed to check payment status", error)
            return False
        
        status_data = response.json()
        payment_status = status_data.get("payment_status")
        
        if payment_status != "paid":
            self.log_result("3. Payment Status", False, f"Payment status should be 'paid', got '{payment_status}'", status_data)
            return False
        
        self.log_result("3. Payment Status", True, f"Payment status: {payment_status}")
        
        # Check profile credits increased by +10
        response = self.make_request("GET", "/user/profile")
        if response and response.status_code == 200:
            profile = response.json()
            credits = profile.get("credits_remaining")
            if credits == 10:  # Should be 0 + 10 from one_time package
                self.log_result("3. Credits Increase", True, f"Credits increased to {credits}")
                return True
            else:
                self.log_result("3. Credits Increase", False, f"Credits should be 10, got {credits}", profile)
                return False
        else:
            self.log_result("3. Credits Increase", False, "Could not verify credit increase")
            return False
    
    def test_4_vedic_time_schedule(self):
        """Test 4: GET /api/vedic-time/daily-schedule?date=2025-03-15&city=Москва -> 200, contains inauspicious_periods.rahu_kaal"""
        print("\n🔍 TEST 4: Vedic Time Daily Schedule")
        
        if not self.auth_token:
            self.log_result("4. Vedic Time Schedule", False, "No auth token available")
            return False
        
        endpoint = "/vedic-time/daily-schedule?date=2025-03-15&city=Москва"
        response = self.make_request("GET", endpoint)
        
        if not response or response.status_code != 200:
            error = response.text if response else "Connection failed"
            self.log_result("4. Vedic Time Schedule", False, "API call failed", error)
            return False
        
        data = response.json()
        
        # Check for inauspicious_periods.rahu_kaal
        inauspicious_periods = data.get("inauspicious_periods")
        if not inauspicious_periods:
            self.log_result("4. Vedic Time Schedule", False, "Missing inauspicious_periods", data)
            return False
        
        rahu_kaal = inauspicious_periods.get("rahu_kaal")
        if not rahu_kaal:
            self.log_result("4. Vedic Time Schedule", False, "Missing rahu_kaal in inauspicious_periods", inauspicious_periods)
            return False
        
        self.log_result("4. Vedic Time Schedule", True, f"Response contains inauspicious_periods.rahu_kaal: {rahu_kaal}")
        return True
    
    def test_5_planetary_energy_chart(self):
        """Test 5: GET /api/charts/planetary-energy/7 -> 200, chart_data array with surya..ketu keys"""
        print("\n🔍 TEST 5: Planetary Energy Chart")
        
        if not self.auth_token:
            self.log_result("5. Planetary Energy Chart", False, "No auth token available")
            return False
        
        response = self.make_request("GET", "/charts/planetary-energy/7")
        
        if not response or response.status_code != 200:
            error = response.text if response else "Connection failed"
            self.log_result("5. Planetary Energy Chart", False, "API call failed", error)
            return False
        
        data = response.json()
        chart_data = data.get("chart_data")
        
        if not chart_data or not isinstance(chart_data, list):
            self.log_result("5. Planetary Energy Chart", False, "Missing or invalid chart_data array", data)
            return False
        
        # Check for planetary keys (surya, chandra, mangal, budha, guru, shukra, shani, rahu, ketu)
        expected_planets = ["surya", "chandra", "mangal", "budha", "guru", "shukra", "shani", "rahu", "ketu"]
        
        if len(chart_data) > 0:
            first_day = chart_data[0]
            found_planets = []
            for planet in expected_planets:
                if planet in first_day:
                    found_planets.append(planet)
            
            if len(found_planets) >= 7:  # Should have most planets
                self.log_result("5. Planetary Energy Chart", True, f"Chart data contains planetary keys: {found_planets}")
                return True
            else:
                self.log_result("5. Planetary Energy Chart", False, f"Missing planetary keys, found only: {found_planets}", first_day)
                return False
        else:
            self.log_result("5. Planetary Energy Chart", False, "Empty chart_data array", data)
            return False
    
    def test_6_html_report(self):
        """Test 6: HTML report: POST /api/reports/html/numerology -> 200 text/html and starts with <!DOCTYPE html>"""
        print("\n🔍 TEST 6: HTML Report Generation")
        
        if not self.auth_token:
            self.log_result("6. HTML Report", False, "No auth token available")
            return False
        
        html_request = {
            "include_vedic": True,
            "include_charts": True,
            "theme": "light"
        }
        
        response = self.make_request("POST", "/reports/html/numerology", html_request)
        
        if not response or response.status_code != 200:
            error = response.text if response else "Connection failed"
            self.log_result("6. HTML Report", False, "API call failed", error)
            return False
        
        # Check content type
        content_type = response.headers.get('content-type', '')
        if 'text/html' not in content_type:
            self.log_result("6. HTML Report", False, f"Wrong content type: {content_type}", response.text[:200])
            return False
        
        # Check content starts with <!DOCTYPE html>
        content = response.text
        if content.strip().startswith('<!DOCTYPE html>'):
            self.log_result("6. HTML Report", True, f"HTML report generated successfully (content-type: {content_type}, length: {len(content)})")
            return True
        else:
            self.log_result("6. HTML Report", False, f"Content doesn't start with <!DOCTYPE html>, starts with: {content[:50]}", content[:200])
            return False
    
    def test_7_pdf_report(self):
        """Test 7: PDF report: POST /api/reports/pdf/numerology -> 200 application/pdf with Content-Disposition attachment"""
        print("\n🔍 TEST 7: PDF Report Generation")
        
        if not self.auth_token:
            self.log_result("7. PDF Report", False, "No auth token available")
            return False
        
        pdf_request = {
            "include_vedic": True,
            "include_charts": True,
            "include_compatibility": False
        }
        
        response = self.make_request("POST", "/reports/pdf/numerology", pdf_request)
        
        if not response or response.status_code != 200:
            error = response.text if response else "Connection failed"
            self.log_result("7. PDF Report", False, "API call failed", error)
            return False
        
        # Check content type
        content_type = response.headers.get('content-type', '')
        if 'application/pdf' not in content_type:
            self.log_result("7. PDF Report", False, f"Wrong content type: {content_type}", response.text[:200])
            return False
        
        # Check Content-Disposition header
        content_disposition = response.headers.get('content-disposition', '')
        if 'attachment' not in content_disposition:
            self.log_result("7. PDF Report", False, f"Missing attachment in Content-Disposition: {content_disposition}")
            return False
        
        # Check content length
        content_length = len(response.content)
        if content_length < 1000:
            self.log_result("7. PDF Report", False, f"PDF too small: {content_length} bytes")
            return False
        
        self.log_result("7. PDF Report", True, f"PDF report generated successfully (content-type: {content_type}, size: {content_length} bytes)")
        return True
    
    def run_review_tests(self):
        """Run all review tests in sequence"""
        print("🚀 Starting NUMEROM Backend Review Tests")
        print("Testing specific scenarios after server.py restoration")
        print("=" * 60)
        
        # Run tests in order
        test_1_success = self.test_1_register_and_login()
        test_2_success = self.test_2_pythagorean_square()
        test_3_success = self.test_3_payment_demo_flow()
        test_4_success = self.test_4_vedic_time_schedule()
        test_5_success = self.test_5_planetary_energy_chart()
        test_6_success = self.test_6_html_report()
        test_7_success = self.test_7_pdf_report()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 REVIEW TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Show detailed results
        print("\n📋 DETAILED RESULTS:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test']}: {result['message']}")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print("\n❌ FAILED TESTS DETAILS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['message']}")
                if test['details']:
                    print(f"    Details: {test['details']}")
        
        return passed, total

def main():
    """Main test execution"""
    tester = ReviewTester()
    passed, total = tester.run_review_tests()
    
    # Exit with appropriate code
    if passed == total:
        print("\n🎉 All review tests passed!")
        exit(0)
    else:
        print(f"\n⚠️  {total - passed} review tests failed")
        exit(1)

if __name__ == "__main__":
    main()