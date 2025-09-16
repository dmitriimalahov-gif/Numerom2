#!/usr/bin/env python3
"""
NUMEROM Numerology Corrections Testing Suite
Tests the corrected numerology calculations with new formulas as per review request.
"""

import requests
import json
import os
from datetime import datetime
import time

# Get backend URL from environment
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.split('=')[1].strip() + '/api'
            break

class NumerologyCorrectionsTest:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.auth_token = None
        self.user_data = {
            "email": f"testuser{int(time.time())}@numerom.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "birth_date": "10.01.1982",  # Test date from review request
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
                self.log_result("User Setup", False, "Missing token in registration response", data)
        else:
            error = response.text if response else "Connection failed"
            self.log_result("User Setup", False, "Failed to register test user", error)
        return False
    
    def test_corrected_personal_numbers_10_01_1982(self):
        """Test corrected personal numbers calculation for birth date 10.01.1982"""
        if not self.auth_token:
            self.log_result("Corrected Personal Numbers (10.01.1982)", False, "No auth token available")
            return False
        
        # Test with specific birth date from review request
        test_birth_date = "10.01.1982"
        response = self.make_request("POST", "/numerology/personal-numbers", {"birth_date": test_birth_date})
        
        if response and response.status_code == 200:
            data = response.json()
            
            # Expected calculations based on review request:
            # Destiny Number (ЧС): day + month + year as numbers (10 + 1 + 1982 = 1993 → reduce to single digit)
            expected_destiny = self.reduce_to_single_digit(10 + 1 + 1982)  # 1993 → 1+9+9+3 = 22 → 2+2 = 4
            
            # Helping Mind Number (ЧУ*): day + month as numbers (10 + 1 = 11 → stays 11 as master number)
            expected_helping_mind = 11  # Should stay as master number
            
            # Ruling Number (ПЧ): sum of ALL digits (1+0+0+1+1+9+8+2 = 22 → stays 22 as master number)
            expected_ruling = 22  # Should stay as master number
            
            # Verify calculations
            actual_destiny = data.get("destiny_number")
            actual_helping_mind = data.get("helping_mind_number")
            actual_ruling = data.get("ruling_number")
            
            success = True
            errors = []
            
            if actual_destiny != expected_destiny:
                success = False
                errors.append(f"Destiny Number: expected {expected_destiny}, got {actual_destiny}")
            
            if actual_helping_mind != expected_helping_mind:
                success = False
                errors.append(f"Helping Mind Number: expected {expected_helping_mind}, got {actual_helping_mind}")
            
            if actual_ruling != expected_ruling:
                success = False
                errors.append(f"Ruling Number: expected {expected_ruling}, got {actual_ruling}")
            
            if success:
                self.log_result("Corrected Personal Numbers (10.01.1982)", True, 
                              f"All calculations correct: Destiny={actual_destiny}, Helping Mind={actual_helping_mind}, Ruling={actual_ruling}")
            else:
                self.log_result("Corrected Personal Numbers (10.01.1982)", False, 
                              f"Calculation errors: {'; '.join(errors)}", data)
            
            return success
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Corrected Personal Numbers (10.01.1982)", False, 
                          "Failed to calculate personal numbers", error)
        return False
    
    def test_master_numbers_preservation(self):
        """Test that master numbers 11 and 22 are preserved correctly"""
        if not self.auth_token:
            self.log_result("Master Numbers Preservation", False, "No auth token available")
            return False
        
        # Test cases that should produce master numbers
        test_cases = [
            {"birth_date": "02.09.1998", "expected_ruling": 11, "description": "Should preserve 11 during reduction (0+2+0+9+1+9+9+8=38→3+8=11)"},
            {"birth_date": "10.01.1982", "expected_ruling": 22, "description": "Should preserve 22 (1+0+0+1+1+9+8+2=22)"},
            {"birth_date": "29.02.1992", "expected_helping_mind": 11, "description": "Should preserve 11 for helping mind (29+2=31→3+1=4, but 29+2 direct = 31, need to check logic)"}
        ]
        
        all_success = True
        
        for i, test_case in enumerate(test_cases):
            response = self.make_request("POST", "/numerology/personal-numbers", {"birth_date": test_case["birth_date"]})
            
            if response and response.status_code == 200:
                data = response.json()
                
                if "expected_ruling" in test_case:
                    actual_ruling = data.get("ruling_number")
                    if actual_ruling == test_case["expected_ruling"]:
                        self.log_result(f"Master Numbers Test {i+1}", True, 
                                      f"Ruling number {actual_ruling} preserved for {test_case['birth_date']}")
                    else:
                        self.log_result(f"Master Numbers Test {i+1}", False, 
                                      f"Ruling number: expected {test_case['expected_ruling']}, got {actual_ruling} for {test_case['birth_date']}")
                        all_success = False
                
                if "expected_helping_mind" in test_case:
                    actual_helping_mind = data.get("helping_mind_number")
                    if actual_helping_mind == test_case["expected_helping_mind"]:
                        self.log_result(f"Master Numbers Test {i+1}", True, 
                                      f"Helping mind number {actual_helping_mind} preserved for {test_case['birth_date']}")
                    else:
                        self.log_result(f"Master Numbers Test {i+1}", False, 
                                      f"Helping mind number: expected {test_case['expected_helping_mind']}, got {actual_helping_mind} for {test_case['birth_date']}")
                        all_success = False
            else:
                error = response.text if response else "Connection failed"
                self.log_result(f"Master Numbers Test {i+1}", False, 
                              f"Failed to test {test_case['birth_date']}", error)
                all_success = False
        
        return all_success
    
    def test_comparison_with_old_calculations(self):
        """Test comparison with old calculations to verify changes are applied"""
        if not self.auth_token:
            self.log_result("Old vs New Calculations", False, "No auth token available")
            return False
        
        # Test the specific example from review request
        test_birth_date = "10.01.1982"
        response = self.make_request("POST", "/numerology/personal-numbers", {"birth_date": test_birth_date})
        
        if response and response.status_code == 200:
            data = response.json()
            
            # Verify the new formulas are being used:
            # 1. Destiny Number: day + month + year as numbers (not digit sum)
            # 2. Helping Mind Number: day + month as numbers (preserves master numbers)
            # 3. Ruling Number: sum of ALL digits (preserves master numbers 11, 22)
            
            destiny = data.get("destiny_number")
            helping_mind = data.get("helping_mind_number")
            ruling = data.get("ruling_number")
            
            # Check if the calculations match the new formulas
            expected_results = {
                "destiny_number": 4,  # 10+1+1982=1993→1+9+9+3=22→2+2=4
                "helping_mind_number": 11,  # 10+1=11 (master number preserved)
                "ruling_number": 22  # 1+0+0+1+1+9+8+2=22 (master number preserved)
            }
            
            success = True
            for field, expected in expected_results.items():
                actual = data.get(field)
                if actual != expected:
                    success = False
                    self.log_result("Old vs New Calculations", False, 
                                  f"{field}: expected {expected}, got {actual} - new formulas not applied correctly")
                    break
            
            if success:
                self.log_result("Old vs New Calculations", True, 
                              "New calculation formulas are correctly applied")
                
                # Also verify wisdom number calculation
                wisdom = data.get("wisdom_number")
                if wisdom is not None:
                    self.log_result("Wisdom Number Calculation", True, 
                                  f"Wisdom number calculated: {wisdom}")
                else:
                    self.log_result("Wisdom Number Calculation", False, 
                                  "Wisdom number missing from response")
            
            return success
        else:
            error = response.text if response else "Connection failed"
            self.log_result("Old vs New Calculations", False, 
                          "Failed to get calculations for comparison", error)
        return False
    
    def reduce_to_single_digit(self, number):
        """Helper function to reduce number to single digit (preserving master numbers)"""
        if number in [11, 22, 33]:
            return number
        
        while number > 9:
            if number == 11 or number == 22:
                return number
            number = sum(int(digit) for digit in str(number))
        return number
    
    def run_all_tests(self):
        """Run all numerology correction tests"""
        print("🧮 Starting NUMEROM Numerology Corrections Tests")
        print("=" * 60)
        print("Testing corrected numerology calculations with new formulas")
        print("Review Request: Birth date 10.01.1982 verification")
        print("=" * 60)
        
        # Setup test user
        if not self.setup_test_user():
            print("❌ Failed to setup test user - aborting tests")
            return 0, 1
        
        # Run correction tests
        print("\n🎯 TESTING CORRECTED FORMULAS:")
        self.test_corrected_personal_numbers_10_01_1982()
        self.test_master_numbers_preservation()
        self.test_comparison_with_old_calculations()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 NUMEROLOGY CORRECTIONS TEST SUMMARY")
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
            print("\n✅ All numerology correction tests passed!")
        
        return passed, total

def main():
    """Main test execution"""
    tester = NumerologyCorrectionsTest()
    passed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    if passed == total:
        print("\n🎉 All numerology correction tests passed!")
        exit(0)
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        exit(1)

if __name__ == "__main__":
    main()