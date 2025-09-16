#!/usr/bin/env python3
"""
Enhanced Pythagorean Square Testing Suite
Tests the enhanced Pythagorean Square functionality after adding detailed interpretations.
"""

import requests
import json
import os
from datetime import datetime
import time

# Get backend URL from environment
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

class EnhancedPythagoreanTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.auth_token = None
        self.user_data = {
            "email": f"pythagorean_test_{int(time.time())}@numerom.com",
            "password": "TestPass123!",
            "full_name": "Pythagorean Test User",
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
    
    def setup_test_user(self):
        """Register and login test user"""
        # Register user
        response = self.make_request("POST", "/auth/register", self.user_data)
        
        if response and response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                self.auth_token = data["access_token"]
                self.log_result("User Setup", True, "Test user registered and authenticated")
                return True
            else:
                self.log_result("User Setup", False, "Missing access token", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("User Setup", False, "Failed to register test user", error)
        return False
    
    def test_pythagorean_square_structure(self):
        """Test 1: Verify Pythagorean Square returns correct data structure"""
        if not self.auth_token:
            self.log_result("Pythagorean Square Structure", False, "No auth token available")
            return False
        
        response = self.make_request("POST", "/numerology/pythagorean-square")
        
        if response and response.status_code == 200:
            data = response.json()
            
            # Check required fields
            required_fields = ["square", "horizontal_sums", "vertical_sums", "diagonal_sums", "additional_numbers"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                # Verify square structure (3x3 matrix)
                square = data["square"]
                if isinstance(square, list) and len(square) == 3:
                    if all(isinstance(row, list) and len(row) == 3 for row in square):
                        # Verify additional numbers (should be 4 numbers)
                        additional_numbers = data["additional_numbers"]
                        if isinstance(additional_numbers, list) and len(additional_numbers) == 4:
                            # Verify sums are lists with correct lengths
                            h_sums = data["horizontal_sums"]
                            v_sums = data["vertical_sums"]
                            d_sums = data["diagonal_sums"]
                            
                            if (isinstance(h_sums, list) and len(h_sums) == 3 and
                                isinstance(v_sums, list) and len(v_sums) == 3 and
                                isinstance(d_sums, list) and len(d_sums) == 2):
                                
                                self.log_result("Pythagorean Square Structure", True, 
                                              f"Correct structure: 3x3 square, 4 additional numbers {additional_numbers}")
                                return True
                            else:
                                self.log_result("Pythagorean Square Structure", False, 
                                              "Invalid sums structure", {"h_sums": len(h_sums) if isinstance(h_sums, list) else type(h_sums),
                                                                        "v_sums": len(v_sums) if isinstance(v_sums, list) else type(v_sums),
                                                                        "d_sums": len(d_sums) if isinstance(d_sums, list) else type(d_sums)})
                        else:
                            self.log_result("Pythagorean Square Structure", False, 
                                          f"Invalid additional_numbers: expected 4, got {len(additional_numbers) if isinstance(additional_numbers, list) else type(additional_numbers)}")
                    else:
                        self.log_result("Pythagorean Square Structure", False, 
                                      "Square rows are not 3-element lists", square)
                else:
                    self.log_result("Pythagorean Square Structure", False, 
                                  f"Square is not 3x3 matrix: {type(square)}, length: {len(square) if isinstance(square, list) else 'N/A'}")
            else:
                self.log_result("Pythagorean Square Structure", False, 
                              f"Missing required fields: {missing_fields}", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Pythagorean Square Structure", False, 
                          f"API call failed with status {response.status_code if response else 'None'}", error)
        
        return False
    
    def test_pythagorean_square_json_response(self):
        """Test 2: Verify endpoint returns proper JSON response"""
        if not self.auth_token:
            self.log_result("Pythagorean Square JSON Response", False, "No auth token available")
            return False
        
        response = self.make_request("POST", "/numerology/pythagorean-square")
        
        if response and response.status_code == 200:
            # Check content type
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                try:
                    data = response.json()
                    # Verify it's valid JSON with expected structure
                    if isinstance(data, dict):
                        self.log_result("Pythagorean Square JSON Response", True, 
                                      f"Valid JSON response with content-type: {content_type}")
                        return True
                    else:
                        self.log_result("Pythagorean Square JSON Response", False, 
                                      f"JSON is not a dictionary: {type(data)}")
                except json.JSONDecodeError as e:
                    self.log_result("Pythagorean Square JSON Response", False, 
                                  f"Invalid JSON: {str(e)}")
            else:
                self.log_result("Pythagorean Square JSON Response", False, 
                              f"Wrong content type: {content_type}")
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Pythagorean Square JSON Response", False, 
                          f"API call failed with status {response.status_code if response else 'None'}", error)
        
        return False
    
    def test_credit_decrement_functionality(self):
        """Test 3: Test credit decrement functionality for non-premium users"""
        if not self.auth_token:
            self.log_result("Credit Decrement Functionality", False, "No auth token available")
            return False
        
        # Get initial user profile to check credits
        profile_response = self.make_request("GET", "/user/profile")
        if not profile_response or profile_response.status_code != 200:
            self.log_result("Credit Decrement Functionality", False, "Could not get user profile")
            return False
        
        profile_data = profile_response.json()
        initial_credits = profile_data.get("credits_remaining", 0)
        is_premium = profile_data.get("is_premium", False)
        
        # Make Pythagorean Square calculation
        calc_response = self.make_request("POST", "/numerology/pythagorean-square")
        
        if calc_response and calc_response.status_code == 200:
            # Check if credits were properly handled
            new_profile_response = self.make_request("GET", "/user/profile")
            if new_profile_response and new_profile_response.status_code == 200:
                new_profile_data = new_profile_response.json()
                new_credits = new_profile_data.get("credits_remaining", 0)
                
                if is_premium:
                    # Premium users should not lose credits
                    if new_credits == initial_credits:
                        self.log_result("Credit Decrement Functionality", True, 
                                      f"Premium user credits unchanged: {initial_credits}")
                        return True
                    else:
                        self.log_result("Credit Decrement Functionality", False, 
                                      f"Premium user credits changed: {initial_credits} -> {new_credits}")
                else:
                    # Non-premium users should lose 1 credit
                    if new_credits == initial_credits - 1:
                        self.log_result("Credit Decrement Functionality", True, 
                                      f"Non-premium user credits decremented: {initial_credits} -> {new_credits}")
                        return True
                    else:
                        self.log_result("Credit Decrement Functionality", False, 
                                      f"Incorrect credit decrement: {initial_credits} -> {new_credits} (expected -1)")
            else:
                self.log_result("Credit Decrement Functionality", False, "Could not verify credit changes")
        elif calc_response and calc_response.status_code == 402:
            # No credits remaining - this is also a valid test result
            self.log_result("Credit Decrement Functionality", True, 
                          "No credits remaining - payment required (credit system working)")
            return True
        else:
            error = calc_response.text if calc_response else "Connection failed"
            self.log_result("Credit Decrement Functionality", False, 
                          f"Calculation failed with status {calc_response.status_code if calc_response else 'None'}", error)
        
        return False
    
    def test_enhanced_frontend_compatibility(self):
        """Test 4: Confirm response format is compatible with enhanced frontend component"""
        if not self.auth_token:
            self.log_result("Enhanced Frontend Compatibility", False, "No auth token available")
            return False
        
        response = self.make_request("POST", "/numerology/pythagorean-square")
        
        if response and response.status_code == 200:
            data = response.json()
            
            # Check for fields that enhanced frontend expects
            compatibility_checks = []
            
            # 1. Square matrix for cell display
            if "square" in data and isinstance(data["square"], list):
                compatibility_checks.append("square_matrix")
            
            # 2. Horizontal/vertical/diagonal sums for interpretations
            if all(key in data for key in ["horizontal_sums", "vertical_sums", "diagonal_sums"]):
                compatibility_checks.append("sum_calculations")
            
            # 3. Additional numbers for detailed analysis
            if "additional_numbers" in data and isinstance(data["additional_numbers"], list):
                compatibility_checks.append("additional_numbers")
            
            # 4. Number positions for planetary interpretations (if available)
            if "number_positions" in data:
                compatibility_checks.append("number_positions")
            
            # 5. Check if square contains proper cell values (strings of repeated digits)
            square = data.get("square", [])
            valid_cells = True
            for row in square:
                for cell in row:
                    if cell and not isinstance(cell, str):
                        valid_cells = False
                        break
                if not valid_cells:
                    break
            
            if valid_cells:
                compatibility_checks.append("valid_cell_format")
            
            # Evaluate compatibility
            if len(compatibility_checks) >= 4:  # At least 4 out of 5 checks should pass
                self.log_result("Enhanced Frontend Compatibility", True, 
                              f"Compatible with enhanced frontend: {', '.join(compatibility_checks)}")
                return True
            else:
                self.log_result("Enhanced Frontend Compatibility", False, 
                              f"Missing compatibility features: {compatibility_checks}", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Enhanced Frontend Compatibility", False, 
                          f"API call failed with status {response.status_code if response else 'None'}", error)
        
        return False
    
    def test_specific_birth_date_calculation(self):
        """Test 5: Test with specific birth date to verify calculation accuracy"""
        if not self.auth_token:
            self.log_result("Specific Birth Date Calculation", False, "No auth token available")
            return False
        
        # Test with the birth date from user data (15.03.1990)
        response = self.make_request("POST", "/numerology/pythagorean-square", {"birth_date": "15.03.1990"})
        
        if response and response.status_code == 200:
            data = response.json()
            
            # Verify the calculation is consistent
            additional_numbers = data.get("additional_numbers", [])
            if len(additional_numbers) == 4:
                # For 15.03.1990, we can verify the calculation
                # Birth digits: 1,5,0,3,1,9,9,0 -> A1 = 28, A2 = 10, A3 = 28-2*1 = 26, A4 = 8
                expected_a1 = 28  # Sum of all digits
                expected_a2 = 10  # Sum of digits in A1 (2+8)
                expected_a3 = 26  # A1 - 2*first_digit_of_day (28 - 2*1)
                expected_a4 = 8   # Sum of digits in A3 (2+6)
                
                if (additional_numbers[0] == expected_a1 and 
                    additional_numbers[1] == expected_a2 and
                    additional_numbers[2] == expected_a3 and
                    additional_numbers[3] == expected_a4):
                    
                    self.log_result("Specific Birth Date Calculation", True, 
                                  f"Correct calculation for 15.03.1990: {additional_numbers}")
                    return True
                else:
                    self.log_result("Specific Birth Date Calculation", False, 
                                  f"Incorrect calculation: got {additional_numbers}, expected [{expected_a1}, {expected_a2}, {expected_a3}, {expected_a4}]")
            else:
                self.log_result("Specific Birth Date Calculation", False, 
                              f"Wrong number of additional numbers: {len(additional_numbers)}")
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Specific Birth Date Calculation", False, 
                          f"API call failed with status {response.status_code if response else 'None'}", error)
        
        return False
    
    def run_all_tests(self):
        """Run all enhanced Pythagorean Square tests"""
        print("🔥 Starting Enhanced Pythagorean Square Testing Suite")
        print("=" * 60)
        
        # Setup test user
        if not self.setup_test_user():
            print("❌ Failed to setup test user. Aborting tests.")
            return 0, 1
        
        # Run all tests
        tests = [
            self.test_pythagorean_square_structure,
            self.test_pythagorean_square_json_response,
            self.test_credit_decrement_functionality,
            self.test_enhanced_frontend_compatibility,
            self.test_specific_birth_date_calculation
        ]
        
        for test in tests:
            test()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 ENHANCED PYTHAGOREAN SQUARE TEST SUMMARY")
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
            print("\n🎉 All Enhanced Pythagorean Square tests passed!")
        
        return passed, total

def main():
    """Main test execution"""
    tester = EnhancedPythagoreanTester()
    passed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    if passed == total:
        print("\n✅ Enhanced Pythagorean Square functionality is working correctly!")
        exit(0)
    else:
        print(f"\n⚠️  {total - passed} tests failed - Enhanced Pythagorean Square needs attention")
        exit(1)

if __name__ == "__main__":
    main()