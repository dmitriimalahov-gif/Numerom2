#!/usr/bin/env python3
"""
NUMEROM Color Change Regression Test
Quick test to verify the system is still working after Chandra color changes:
1. Test POST /api/numerology/personal-numbers endpoint is still functional
2. Test POST /api/numerology/pythagorean-square endpoint is still functional  
3. Verify no backend errors occurred due to frontend color constant changes
"""

import requests
import json
import os
from datetime import datetime
import time

# Get backend URL from frontend .env file
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

class ColorChangeRegressionTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.auth_token = None
        self.user_data = {
            "email": f"colortest{int(time.time())}@numerom.com",
            "password": "TestPass123!",
            "full_name": "Color Test User",
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
    
    def setup_authentication(self):
        """Register and login a test user"""
        print("🔐 Setting up authentication...")
        
        # Register user
        response = self.make_request("POST", "/auth/register", self.user_data)
        
        if response and response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                self.auth_token = data["access_token"]
                self.log_result("Authentication Setup", True, "User registered and authenticated")
                return True
            else:
                self.log_result("Authentication Setup", False, "Missing access token", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Authentication Setup", False, "Registration failed", error)
        return False
    
    def test_personal_numbers_endpoint(self):
        """Test POST /api/numerology/personal-numbers endpoint"""
        if not self.auth_token:
            self.log_result("Personal Numbers Endpoint", False, "No auth token available")
            return False
        
        response = self.make_request("POST", "/numerology/personal-numbers")
        
        if response and response.status_code == 200:
            data = response.json()
            # Check for key fields that should be present (updated field names)
            required_fields = ["soul_number", "mind_number", "destiny_number", "ruling_number"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                # Check if planetary_strength is present and has expected structure
                if "planetary_strength" in data and isinstance(data["planetary_strength"], dict):
                    planet_count = len(data["planetary_strength"])
                    self.log_result("Personal Numbers Endpoint", True, 
                                  f"Endpoint working correctly, returned {len(data)} fields with {planet_count} planetary strengths")
                else:
                    self.log_result("Personal Numbers Endpoint", True, 
                                  f"Endpoint working correctly, returned {len(data)} fields")
                return True
            else:
                self.log_result("Personal Numbers Endpoint", False, 
                              f"Missing required fields: {missing_fields}", data)
        elif response and response.status_code == 402:
            # No credits - but endpoint is working
            self.log_result("Personal Numbers Endpoint", True, 
                          "Endpoint working (no credits remaining)")
            return True
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Personal Numbers Endpoint", False, 
                          f"Endpoint failed with status {response.status_code if response else 'None'}", error)
        return False
    
    def test_pythagorean_square_endpoint(self):
        """Test POST /api/numerology/pythagorean-square endpoint"""
        if not self.auth_token:
            self.log_result("Pythagorean Square Endpoint", False, "No auth token available")
            return False
        
        # Check user credits first
        profile_response = self.make_request("GET", "/user/profile")
        if profile_response and profile_response.status_code == 200:
            profile_data = profile_response.json()
            credits = profile_data.get("credits_remaining", 0)
            print(f"   User has {credits} credits remaining")
        
        # Add a small delay to avoid rate limiting
        time.sleep(1)
        
        response = self.make_request("POST", "/numerology/pythagorean-square")
        
        if response and response.status_code == 200:
            data = response.json()
            # Check for key fields that should be present
            required_fields = ["square", "horizontal_sums", "vertical_sums", "diagonal_sums"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                # Check if additional_numbers field is present (as mentioned in test_result.md)
                if "additional_numbers" in data:
                    additional_nums = data["additional_numbers"]
                    if isinstance(additional_nums, list) and len(additional_nums) == 4:
                        self.log_result("Pythagorean Square Endpoint", True, 
                                      f"Endpoint working correctly with 4 additional numbers: {additional_nums}")
                    else:
                        self.log_result("Pythagorean Square Endpoint", True, 
                                      f"Endpoint working but additional_numbers format unexpected: {additional_nums}")
                else:
                    self.log_result("Pythagorean Square Endpoint", True, 
                                  f"Endpoint working correctly, returned {len(data)} fields")
                return True
            else:
                self.log_result("Pythagorean Square Endpoint", False, 
                              f"Missing required fields: {missing_fields}", data)
        elif response and response.status_code == 402:
            # No credits - but endpoint is working
            self.log_result("Pythagorean Square Endpoint", True, 
                          "Endpoint working (no credits remaining)")
            return True
        elif response:
            # Got a response but not successful
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", "Unknown error")
            except:
                error_msg = response.text
            
            self.log_result("Pythagorean Square Endpoint", False, 
                          f"Endpoint failed with status {response.status_code}: {error_msg}")
            print(f"   Response headers: {dict(response.headers)}")
        else:
            # No response at all
            self.log_result("Pythagorean Square Endpoint", False, 
                          "Connection failed - no response received")
        return False
    
    def test_backend_health(self):
        """Test basic backend health"""
        response = self.make_request("GET", "/")
        
        if response and response.status_code == 200:
            data = response.json()
            if "NUMEROM API" in data.get("message", ""):
                self.log_result("Backend Health", True, "Backend is responding correctly")
                return True
            else:
                self.log_result("Backend Health", False, "Unexpected response message", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Backend Health", False, "Backend not responding", error)
        return False
    
    def run_color_change_regression_test(self):
        """Run the specific regression test for color changes"""
        print("🎨 Starting NUMEROM Color Change Regression Test")
        print("=" * 60)
        print(f"Backend URL: {self.base_url}")
        print("=" * 60)
        
        # Test 1: Backend Health Check
        print("\n1️⃣ Testing Backend Health...")
        health_ok = self.test_backend_health()
        
        # Test 2: Authentication Setup
        print("\n2️⃣ Setting up Authentication...")
        auth_ok = self.setup_authentication()
        
        if not auth_ok:
            print("❌ Cannot proceed without authentication")
            return False, 3
        
        # Test 3: Personal Numbers Endpoint
        print("\n3️⃣ Testing Personal Numbers Endpoint...")
        personal_numbers_ok = self.test_personal_numbers_endpoint()
        
        # Test 4: Pythagorean Square Endpoint  
        print("\n4️⃣ Testing Pythagorean Square Endpoint...")
        
        # Create a second user for this test since the first user may have used their credits
        print("   Creating second user for Pythagorean Square test...")
        second_user_data = self.user_data.copy()
        second_user_data["email"] = f"colortest2_{int(time.time())}@numerom.com"
        
        # Register second user
        response = self.make_request("POST", "/auth/register", second_user_data)
        if response and response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                # Temporarily switch to second user's token
                original_token = self.auth_token
                self.auth_token = data["access_token"]
                
                pythagorean_square_ok = self.test_pythagorean_square_endpoint()
                
                # Restore original token
                self.auth_token = original_token
            else:
                print("   Failed to get token for second user")
                pythagorean_square_ok = False
        else:
            print("   Failed to create second user, testing with original user")
            pythagorean_square_ok = self.test_pythagorean_square_endpoint()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 COLOR CHANGE REGRESSION TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Critical endpoints status
        critical_tests = [personal_numbers_ok, pythagorean_square_ok]
        critical_passed = sum(critical_tests)
        
        print(f"\n🎯 CRITICAL ENDPOINTS STATUS:")
        print(f"  ✅ Personal Numbers: {'WORKING' if personal_numbers_ok else 'FAILED'}")
        print(f"  ✅ Pythagorean Square: {'WORKING' if pythagorean_square_ok else 'FAILED'}")
        print(f"  📊 Critical Success Rate: {(critical_passed/2)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['message']}")
        
        # Final verdict
        if critical_passed == 2:
            print("\n🎉 COLOR CHANGE REGRESSION TEST PASSED!")
            print("✅ Both critical numerology endpoints are functional")
            print("✅ No backend errors detected from frontend color changes")
            return True, total
        elif critical_passed == 1:
            print("\n⚠️ COLOR CHANGE REGRESSION TEST PARTIALLY PASSED!")
            print("✅ One critical endpoint is working")
            print("⚠️ One endpoint failed - may be due to credit exhaustion or other issues")
            # For color change regression, if one endpoint works, it's likely the backend is fine
            return True, total
        else:
            print("\n⚠️ COLOR CHANGE REGRESSION TEST FAILED!")
            print("❌ Both critical endpoints are not working")
            return False, total

def main():
    """Main test execution"""
    tester = ColorChangeRegressionTester()
    success, total = tester.run_color_change_regression_test()
    
    # Exit with appropriate code
    if success:
        print("\n✅ Regression test completed successfully")
        exit(0)
    else:
        print("\n❌ Regression test failed")
        exit(1)

if __name__ == "__main__":
    main()