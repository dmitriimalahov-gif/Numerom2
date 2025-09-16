#!/usr/bin/env python3
"""
NUMEROM Report Selection System Testing Suite
Tests the new calculation selection system for reports as specified in the review request.
"""

import requests
import json
import os
from datetime import datetime
import time

# Get backend URL from environment
BACKEND_URL = "https://numerology-fix.preview.emergentagent.com/api"

class ReportSelectionTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.auth_token = None
        self.user_data = {
            "email": "report_test@numerom.com",
            "password": "SecurePass123!",
            "full_name": "Report Test User",
            "birth_date": "10.01.1982",
            "city": "Москва",
            "phone_number": "+7-999-123-4567"
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
    
    def make_request(self, method, endpoint, data=None, headers=None, params=None):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        default_headers = {"Content-Type": "application/json"}
        
        if headers:
            default_headers.update(headers)
            
        if self.auth_token:
            default_headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=default_headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=default_headers, timeout=30)
            elif method.upper() == "PATCH":
                response = requests.patch(url, json=data, headers=default_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.Timeout:
            return None
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def setup_test_user(self):
        """Register and login test user"""
        print("\n🔧 Setting up test user...")
        
        # Register user
        response = self.make_request("POST", "/auth/register", self.user_data)
        if response and response.status_code in [200, 400]:  # 400 if user already exists
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.log_result("User Registration", True, "New user registered successfully")
            else:
                # User exists, try login
                login_data = {"email": self.user_data["email"], "password": self.user_data["password"]}
                response = self.make_request("POST", "/auth/login", login_data)
                if response and response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get("access_token")
                    self.log_result("User Login", True, "Existing user logged in successfully")
                else:
                    self.log_result("User Setup", False, "Failed to login existing user")
                    return False
        else:
            self.log_result("User Setup", False, "Failed to register user")
            return False
            
        # Update user profile with additional data for testing availability logic
        profile_update = {
            "car_number": "А123БВ777",
            "street": "Тверская улица",
            "house_number": "10",
            "apartment_number": "25",
            "postal_code": "101000"
        }
        
        response = self.make_request("PATCH", "/user/profile", profile_update)
        if response and response.status_code == 200:
            self.log_result("Profile Update", True, "User profile updated with test data")
        else:
            self.log_result("Profile Update", False, "Failed to update user profile")
            
        return True
    
    def test_available_calculations_endpoint(self):
        """Test 1: GET /api/reports/available-calculations endpoint"""
        print("\n📋 Testing available calculations endpoint...")
        
        response = self.make_request("GET", "/reports/available-calculations")
        
        if not response:
            self.log_result("Available Calculations Endpoint", False, "Request timeout or connection error")
            return
            
        if response.status_code != 200:
            self.log_result("Available Calculations Endpoint", False, 
                          f"Expected 200, got {response.status_code}", response.text)
            return
            
        try:
            data = response.json()
            
            # Check main structure
            if "available_calculations" not in data:
                self.log_result("Available Calculations Structure", False, 
                              "Missing 'available_calculations' field")
                return
                
            calculations = data["available_calculations"]
            
            # Test each required calculation type
            required_calculations = [
                "personal_numbers", "name_numerology", "car_numerology", 
                "address_numerology", "vedic_numerology", "pythagorean_square",
                "planetary_route", "vedic_times"
            ]
            
            missing_calculations = []
            for calc_id in required_calculations:
                if calc_id not in calculations:
                    missing_calculations.append(calc_id)
                else:
                    calc = calculations[calc_id]
                    # Check required fields
                    required_fields = ["id", "name", "description", "available", "icon"]
                    missing_fields = [field for field in required_fields if field not in calc]
                    if missing_fields:
                        self.log_result(f"Calculation {calc_id} Fields", False, 
                                      f"Missing fields: {missing_fields}")
                    else:
                        self.log_result(f"Calculation {calc_id} Fields", True, 
                                      f"All required fields present")
            
            if missing_calculations:
                self.log_result("Required Calculations", False, 
                              f"Missing calculations: {missing_calculations}")
            else:
                self.log_result("Required Calculations", True, 
                              "All required calculations present")
            
            # Test availability logic
            self.test_availability_logic(calculations)
            
            self.log_result("Available Calculations Endpoint", True, 
                          f"Endpoint working correctly, returned {len(calculations)} calculations")
            
        except json.JSONDecodeError:
            self.log_result("Available Calculations Endpoint", False, 
                          "Invalid JSON response", response.text)
    
    def test_availability_logic(self, calculations):
        """Test the availability logic for different calculation types"""
        print("\n🔍 Testing calculation availability logic...")
        
        # Test cases based on review request requirements
        test_cases = [
            ("personal_numbers", True, "Should always be available"),
            ("name_numerology", True, "Should be available (user has full_name)"),
            ("car_numerology", True, "Should be available (user has car_number)"),
            ("address_numerology", True, "Should be available (user has address data)"),
            ("vedic_numerology", True, "Should always be available"),
            ("pythagorean_square", True, "Should always be available"),
            ("planetary_route", True, "Should always be available"),
            ("vedic_times", True, "Should be available (user has city)")
        ]
        
        for calc_id, expected_available, reason in test_cases:
            if calc_id in calculations:
                actual_available = calculations[calc_id]["available"]
                if actual_available == expected_available:
                    self.log_result(f"Availability Logic: {calc_id}", True, reason)
                else:
                    self.log_result(f"Availability Logic: {calc_id}", False, 
                                  f"Expected {expected_available}, got {actual_available}. {reason}")
            else:
                self.log_result(f"Availability Logic: {calc_id}", False, 
                              f"Calculation not found in response")
    
    def test_html_report_with_selected_calculations(self):
        """Test 2: POST /api/reports/html/numerology with selected_calculations"""
        print("\n📄 Testing HTML report with selected calculations...")
        
        # Test with specific selected calculations
        test_data = {
            "selected_calculations": ["personal_numbers", "pythagorean_square", "vedic_numerology"],
            "theme": "light"
        }
        
        response = self.make_request("POST", "/reports/html/numerology", test_data)
        
        if not response:
            self.log_result("HTML Report Selected Calculations", False, "Request timeout or connection error")
            return
            
        if response.status_code != 200:
            self.log_result("HTML Report Selected Calculations", False, 
                          f"Expected 200, got {response.status_code}", response.text)
            return
            
        # Check content type
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            self.log_result("HTML Report Content Type", False, 
                          f"Expected text/html, got {content_type}")
        else:
            self.log_result("HTML Report Content Type", True, "Correct content-type: text/html")
            
        # Check HTML content
        html_content = response.text
        if html_content.startswith("<!DOCTYPE html>"):
            self.log_result("HTML Report Format", True, "Valid HTML document structure")
        else:
            self.log_result("HTML Report Format", False, "Invalid HTML document structure")
            
        # Check for NUMEROM branding
        if "NUMEROM" in html_content:
            self.log_result("HTML Report Branding", True, "NUMEROM branding present")
        else:
            self.log_result("HTML Report Branding", False, "NUMEROM branding missing")
            
        self.log_result("HTML Report Selected Calculations", True, 
                      f"Generated HTML report with {len(html_content)} characters")
    
    def test_backward_compatibility(self):
        """Test 3: Backward compatibility with old parameters"""
        print("\n🔄 Testing backward compatibility...")
        
        # Test with old parameters (include_vedic, include_charts)
        old_format_data = {
            "include_vedic": True,
            "include_charts": True,
            "theme": "light"
        }
        
        response = self.make_request("POST", "/reports/html/numerology", old_format_data)
        
        if not response:
            self.log_result("Backward Compatibility", False, "Request timeout or connection error")
            return
            
        if response.status_code != 200:
            self.log_result("Backward Compatibility", False, 
                          f"Expected 200, got {response.status_code}", response.text)
            return
            
        html_content = response.text
        if html_content.startswith("<!DOCTYPE html>"):
            self.log_result("Backward Compatibility", True, 
                          "Old parameter format still works correctly")
        else:
            self.log_result("Backward Compatibility", False, 
                          "Old parameter format not working")
    
    def test_html_generator_sections(self):
        """Test 4: New HTML generator sections"""
        print("\n🏗️ Testing HTML generator sections...")
        
        # Test different combinations of calculations
        test_combinations = [
            {
                "name": "Name Numerology",
                "calculations": ["name_numerology"],
                "expected_content": ["имени", "фамилии"]
            },
            {
                "name": "Car Numerology", 
                "calculations": ["car_numerology"],
                "expected_content": ["автомобиль", "номер"]
            },
            {
                "name": "Address Numerology",
                "calculations": ["address_numerology"], 
                "expected_content": ["адрес", "дом"]
            },
            {
                "name": "All Sections",
                "calculations": ["personal_numbers", "pythagorean_square", "vedic_numerology", "vedic_times"],
                "expected_content": ["Персональные числа", "Квадрат Пифагора", "Ведическая"]
            }
        ]
        
        for test_case in test_combinations:
            test_data = {
                "selected_calculations": test_case["calculations"],
                "theme": "light"
            }
            
            response = self.make_request("POST", "/reports/html/numerology", test_data)
            
            if response and response.status_code == 200:
                html_content = response.text
                found_content = []
                for expected in test_case["expected_content"]:
                    if expected.lower() in html_content.lower():
                        found_content.append(expected)
                
                if len(found_content) >= len(test_case["expected_content"]) // 2:  # At least half should be found
                    self.log_result(f"HTML Section: {test_case['name']}", True, 
                                  f"Expected content found: {found_content}")
                else:
                    self.log_result(f"HTML Section: {test_case['name']}", False, 
                                  f"Expected content missing. Found: {found_content}")
            else:
                self.log_result(f"HTML Section: {test_case['name']}", False, 
                              f"Failed to generate report for {test_case['name']}")
    
    def test_compatibility_and_group_calculations(self):
        """Test 5: Compatibility and group compatibility availability"""
        print("\n👥 Testing compatibility calculations availability...")
        
        # First create some compatibility calculations to make them available
        compatibility_data = {
            "person1_birth_date": "10.01.1982",
            "person2_birth_date": "15.03.1990"
        }
        
        response = self.make_request("POST", "/numerology/compatibility", compatibility_data)
        if response and response.status_code == 200:
            self.log_result("Create Compatibility Calculation", True, "Compatibility calculation created")
            
            # Now check if compatibility appears in available calculations
            response = self.make_request("GET", "/reports/available-calculations")
            if response and response.status_code == 200:
                data = response.json()
                calculations = data.get("available_calculations", {})
                
                if "compatibility" in calculations and calculations["compatibility"]["available"]:
                    self.log_result("Compatibility Availability", True, 
                                  "Compatibility available after creating calculation")
                else:
                    self.log_result("Compatibility Availability", False, 
                                  "Compatibility not available despite having calculations")
            else:
                self.log_result("Compatibility Availability Check", False, 
                              "Failed to check availability after creating compatibility")
        else:
            self.log_result("Create Compatibility Calculation", False, 
                          "Failed to create compatibility calculation")
    
    def run_all_tests(self):
        """Run all report selection system tests"""
        print("🚀 Starting NUMEROM Report Selection System Tests")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user, aborting tests")
            return
            
        # Run tests
        self.test_available_calculations_endpoint()
        self.test_html_report_with_selected_calculations()
        self.test_backward_compatibility()
        self.test_html_generator_sections()
        self.test_compatibility_and_group_calculations()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = ReportSelectionTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)